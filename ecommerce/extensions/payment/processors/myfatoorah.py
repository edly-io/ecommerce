""" MyFatoorah payment processor.

MyFatoorah is a MENA payment gateway (KNET, mada, Visa/Mastercard, Benefit,
Apple Pay) used across KW, SA, AE, QA, BH, JO, OM and EG.

PCI DSS scope
-------------
This processor never touches cardholder data. The learner is redirected to
MyFatoorah's own hosted invoice page, where every card field lives, and comes
back to us with nothing but an opaque ``paymentId``. That is what keeps Edly
eligible for SAQ A rather than SAQ A-EP or SAQ D.

Four properties have to survive any future edit to this file:

* Subclass ``BasePaymentProcessor``, never ``BaseClientSidePaymentProcessor``.
  The latter introduces a ``payment/myfatoorah.html`` template, which is exactly
  where a card input would eventually be added.
* Never call MyFatoorah's ``DirectPayment`` endpoint. Their own documentation
  gates it on the caller already being PCI certified.
* Never trust the browser about whether a payment succeeded. ``get_payment_status``
  re-asks MyFatoorah server-to-server, and that answer is the only one used.
* Never persist or log a PAN, CVV or expiry beyond the masked values MyFatoorah
  returns. ``_scrub`` enforces the allow-list of fields we are willing to store.
"""


import base64
import hashlib
import hmac
import logging
from decimal import Decimal

import requests
from django.urls import reverse
from oscar.apps.payment.exceptions import GatewayError
from six.moves.urllib.parse import urljoin

from ecommerce.core.url_utils import get_ecommerce_url
from ecommerce.extensions.payment.exceptions import MissingTransactionDetailError
from ecommerce.extensions.payment.processors import BasePaymentProcessor, HandledProcessorResponse

logger = logging.getLogger(__name__)

SEND_PAYMENT_ENDPOINT = '/v2/SendPayment'
GET_PAYMENT_STATUS_ENDPOINT = '/v2/GetPaymentStatus'

# Invoice-level state. MyFatoorah returns exactly one of Pending/Paid/Canceled.
INVOICE_STATUS_PAID = 'Paid'

# Transaction-level state. 'Succss' is MyFatoorah's own spelling in their API
# contract, not a typo here -- see their GetPaymentStatus reference.
TRANSACTION_STATUS_SUCCESS = 'Succss'

# Webhook V2 event codes.
EVENT_PAYMENT_STATUS_CHANGED = 1

DEFAULT_TIMEOUT = 15

# Fields we are willing to write to PaymentProcessorResponse. Everything else in
# a MyFatoorah payload is dropped before it is persisted. Both spellings of the
# transaction-value field are listed because MyFatoorah ships the misspelled one.
_DATA_FIELDS = (
    'InvoiceId',
    'InvoiceStatus',
    'InvoiceReference',
    'CustomerReference',
    'InvoiceValue',
    'InvoiceDisplayValue',
    'CreatedDate',
    'ExpiryDate',
)
_TRANSACTION_FIELDS = (
    'TransactionDate',
    'TransactionStatus',
    'PaymentId',
    'PaymentGateway',
    'AuthorizationId',
    'ReferenceId',
    'TrackId',
    'TransactionValue',
    'TransationValue',
    'PaidCurrency',
    'PaidCurrencyValue',
    'Error',
    'ErrorCode',
)
# Masked PAN and brand only. No cardholder name, no expiry, and there is never a
# CVV to begin with.
_CARD_FIELDS = (
    'Number',
    'Brand',
)


def _scrub(payload):
    """
    Reduce a MyFatoorah payload to the fields we are willing to store.

    ``record_processor_response`` persists whatever it is handed, forever. A
    GetPaymentStatus response carries a ``Card`` object including the cardholder
    name and expiry, so this filters down to an allow-list rather than trusting
    the gateway not to widen its payload later.

    Arguments:
        payload (dict): Raw response body from MyFatoorah.

    Returns:
        dict: A copy safe to persist.
    """
    if not isinstance(payload, dict):
        return {}

    data = payload.get('Data')
    scrubbed_data = None
    if isinstance(data, dict):
        scrubbed_data = {key: data[key] for key in _DATA_FIELDS if key in data}

        transactions = []
        for transaction in data.get('InvoiceTransactions') or []:
            if not isinstance(transaction, dict):
                continue
            scrubbed_transaction = {
                key: transaction[key] for key in _TRANSACTION_FIELDS if key in transaction
            }
            card = transaction.get('Card')
            if isinstance(card, dict):
                scrubbed_transaction['Card'] = {key: card[key] for key in _CARD_FIELDS if key in card}
            # Older MyFatoorah payloads put the masked PAN directly on the transaction.
            if 'CardNumber' in transaction:
                scrubbed_transaction['CardNumber'] = transaction['CardNumber']
            transactions.append(scrubbed_transaction)
        if transactions:
            scrubbed_data['InvoiceTransactions'] = transactions

        if 'InvoiceURL' in data:
            scrubbed_data['InvoiceURL'] = data['InvoiceURL']

    scrubbed = {key: payload[key] for key in ('IsSuccess', 'Message') if key in payload}
    if payload.get('ValidationErrors'):
        scrubbed['ValidationErrors'] = payload['ValidationErrors']
    if scrubbed_data is not None:
        scrubbed['Data'] = scrubbed_data
    return scrubbed


class MyFatoorah(BasePaymentProcessor):
    """
    MyFatoorah hosted-redirect payment processor.

    Deliberately declares no ``template_name`` and leaves ``client_side_payment_url``
    at its inherited ``None``. That absence is a PCI control, not an oversight.
    """

    NAME = 'myfatoorah'

    def __init__(self, site):
        """
        Constructs a new instance of the MyFatoorah processor.

        Raises:
            KeyError: If a required setting is not configured for this payment processor.
        """
        super(MyFatoorah, self).__init__(site)
        configuration = self.configuration
        self.api_token = configuration['api_token']
        self.base_url = configuration['base_url']
        # Optional, but signature verification fails closed without it.
        self.webhook_secret = configuration.get('webhook_secret')
        self.timeout = configuration.get('timeout', DEFAULT_TIMEOUT)

    @property
    def cancel_url(self):
        return get_ecommerce_url(self.configuration['cancel_checkout_path'])

    @property
    def error_url(self):
        return get_ecommerce_url(self.configuration['error_path'])

    @property
    def callback_url(self):
        """ The URL MyFatoorah returns the learner to once they leave the hosted page. """
        return get_ecommerce_url(reverse('myfatoorah:callback'))

    @property
    def _headers(self):
        return {
            'Authorization': 'Bearer {token}'.format(token=self.api_token),
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def _request(self, endpoint, payload, basket=None):
        """
        POST to MyFatoorah and return the parsed body.

        Failures are recorded for audit and re-raised as ``GatewayError``. Note that
        neither the request headers nor the raw response body are logged: the former
        carries the API token and the latter can carry masked card data.

        Arguments:
            endpoint (str): Path on the MyFatoorah API, e.g. ``/v2/SendPayment``.
            payload (dict): JSON request body.

        Keyword Arguments:
            basket (Basket): Basket to associate with any recorded response.

        Returns:
            dict: Parsed response body.

        Raises:
            GatewayError: On transport failure, unparseable body, or ``IsSuccess: false``.
        """
        url = urljoin(self.base_url, endpoint)

        try:
            response = requests.post(url, json=payload, headers=self._headers, timeout=self.timeout)
        except requests.RequestException as exc:
            logger.error(
                'MyFatoorah request to [%s] failed with [%s].', endpoint, type(exc).__name__
            )
            raise GatewayError('MyFatoorah request to {} failed.'.format(endpoint))

        try:
            body = response.json()
        except ValueError:
            logger.error(
                'MyFatoorah returned a non-JSON response from [%s] with status [%d].',
                endpoint,
                response.status_code,
            )
            raise GatewayError('MyFatoorah returned an unparseable response from {}.'.format(endpoint))

        if not body.get('IsSuccess'):
            self.record_processor_response(_scrub(body), basket=basket)
            logger.error(
                'MyFatoorah rejected the request to [%s] with status [%d]: %s',
                endpoint,
                response.status_code,
                body.get('Message'),
            )
            raise GatewayError('MyFatoorah rejected the request to {}.'.format(endpoint))

        return body

    def get_transaction_parameters(self, basket, request=None, use_client_side_checkout=False, **kwargs):
        """
        Create a MyFatoorah invoice and hand back its hosted payment page.

        The learner is sent to MyFatoorah's own page, which renders both the
        payment-method picker and the card form, so no card data ever reaches us.

        Arguments:
            basket (Basket): The basket of products being purchased.

        Keyword Arguments:
            request (Request): Unused; accepted to satisfy the base class contract.
            use_client_side_checkout (bool): Unused; this processor is redirect-only.

        Returns:
            dict: Contains ``payment_page_url``, the MyFatoorah hosted invoice URL.

        Raises:
            GatewayError: If MyFatoorah declines to create the invoice.
        """
        owner = basket.owner
        payload = {
            'InvoiceValue': float(basket.total_incl_tax),
            'DisplayCurrencyIso': basket.currency,
            'CustomerName': owner.get_full_name() or owner.username,
            'CustomerEmail': owner.email,
            # Our end of the correlation. MyFatoorah echoes this back on status
            # lookups and webhooks, letting us tie a payment to a basket.
            'CustomerReference': basket.order_number,
            # 'LNK' asks MyFatoorah for an invoice link instead of emailing or
            # texting the learner -- we redirect them to it ourselves.
            'NotificationOption': 'LNK',
            'CallBackUrl': self.callback_url,
            'ErrorUrl': self.callback_url,
        }

        body = self._request(SEND_PAYMENT_ENDPOINT, payload, basket=basket)
        data = body.get('Data') or {}
        invoice_id = data.get('InvoiceId')
        invoice_url = data.get('InvoiceURL')

        if not invoice_id or not invoice_url:
            self.record_processor_response(_scrub(body), basket=basket)
            logger.error(
                'MyFatoorah accepted the invoice for basket [%d] but returned no InvoiceId/InvoiceURL.',
                basket.id,
            )
            raise GatewayError('MyFatoorah did not return a payment URL.')

        # This row is how the callback and webhook find their way back to the
        # basket, so it has to be written before the learner leaves.
        self.record_processor_response(_scrub(body), transaction_id=invoice_id, basket=basket)
        logger.info(
            'Created MyFatoorah invoice [%s] for basket [%d].', invoice_id, basket.id
        )

        return {'payment_page_url': invoice_url}

    def get_payment_status(self, key, key_type='PaymentId', basket=None):
        """
        Ask MyFatoorah, server-to-server, what actually happened to a payment.

        This is the only authority on payment state. The query string MyFatoorah
        redirects the learner back with, and the body it posts to our webhook, are
        both treated as untrusted lookup keys that lead here.

        Arguments:
            key (str): The ``paymentId`` or ``InvoiceId`` to look up.

        Keyword Arguments:
            key_type (str): Which identifier ``key`` is -- ``PaymentId`` (MyFatoorah's
                recommendation) or ``InvoiceId``.
            basket (Basket): Basket to associate with any recorded response.

        Returns:
            dict: The parsed GetPaymentStatus response body.

        Raises:
            MissingTransactionDetailError: If MyFatoorah returns no invoice data.
            GatewayError: On transport or gateway failure.
        """
        body = self._request(
            GET_PAYMENT_STATUS_ENDPOINT,
            {'Key': str(key), 'KeyType': key_type},
            basket=basket,
        )

        if not (body.get('Data') or {}).get('InvoiceId'):
            logger.error('MyFatoorah returned no invoice detail for %s [%s].', key_type, key)
            raise MissingTransactionDetailError(
                'MyFatoorah returned no invoice detail for {} {}.'.format(key_type, key)
            )

        return body

    def record_status_response(self, status_response, basket=None):
        """
        Persist a scrubbed status response for audit without treating it as a payment.

        Used when we look up a payment and decide *not* to act on it, so the decision
        is still traceable afterwards.

        Arguments:
            status_response (dict): A GetPaymentStatus response body.

        Keyword Arguments:
            basket (Basket): Basket to associate with the recorded response.

        Returns:
            PaymentProcessorResponse
        """
        data = status_response.get('Data') or {}
        return self.record_processor_response(
            _scrub(status_response), transaction_id=data.get('InvoiceId'), basket=basket
        )

    @staticmethod
    def is_paid(status_response):
        """
        Return True only if MyFatoorah considers this invoice settled.

        Both the invoice and at least one of its transactions must agree, so a
        pending or failed attempt against a paid-looking invoice cannot slip past.

        Arguments:
            status_response (dict): A GetPaymentStatus response body.

        Returns:
            bool
        """
        data = status_response.get('Data') or {}
        if data.get('InvoiceStatus') != INVOICE_STATUS_PAID:
            return False

        transactions = data.get('InvoiceTransactions') or []
        return any(
            transaction.get('TransactionStatus') == TRANSACTION_STATUS_SUCCESS
            for transaction in transactions
            if isinstance(transaction, dict)
        )

    @staticmethod
    def get_successful_transaction(status_response):
        """ Return the first settled transaction of an invoice, or an empty dict. """
        data = status_response.get('Data') or {}
        for transaction in data.get('InvoiceTransactions') or []:
            if isinstance(transaction, dict) and transaction.get('TransactionStatus') == TRANSACTION_STATUS_SUCCESS:
                return transaction
        return {}

    @staticmethod
    def get_invoice_value(status_response):
        """
        Return the amount MyFatoorah says it charged, as a Decimal.

        Callers compare this against the basket total. Taking the amount from the
        gateway rather than the basket is what makes that comparison meaningful.

        Arguments:
            status_response (dict): A GetPaymentStatus response body.

        Returns:
            Decimal or None: The invoice value, or None if it is absent/unparseable.
        """
        value = (status_response.get('Data') or {}).get('InvoiceValue')
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except (TypeError, ValueError, ArithmeticError):
            logger.error('MyFatoorah returned an unparseable InvoiceValue [%r].', value)
            return None

    def verify_webhook_signature(self, raw_body, signature_header):
        """
        Verify a webhook's ``myfatoorah-signature`` header.

        MyFatoorah signs the flattened ``Data`` object: its properties joined as
        ``key=value,key2=value2``, UTF-8 encoded, HMAC SHA-256 with the account's
        secret key, then base64.

        Field order matters and MyFatoorah documents a specific order per event
        type. This implementation uses the order the fields arrive in, which holds
        for their current payloads but has NOT yet been confirmed against a real
        delivery -- verify against a live webhook in staging before go-live. If
        their order ever diverges from payload order, sign an explicit field list
        per event type here rather than iterating the payload.

        Fails closed: if no ``webhook_secret`` is configured, nothing verifies.

        Arguments:
            raw_body (dict): The parsed webhook body.
            signature_header (str): Value of the ``myfatoorah-signature`` header.

        Returns:
            bool: True only if the signature matches.
        """
        if not self.webhook_secret:
            logger.error(
                'Rejecting MyFatoorah webhook: no webhook_secret is configured for this site.'
            )
            return False

        if not signature_header:
            logger.warning('Rejecting MyFatoorah webhook: no signature header present.')
            return False

        data = raw_body.get('Data')
        if not isinstance(data, dict):
            logger.warning('Rejecting MyFatoorah webhook: no Data object to verify.')
            return False

        message = ','.join(
            '{key}={value}'.format(key=key, value='' if value is None else value)
            for key, value in data.items()
        )
        expected = base64.b64encode(
            hmac.new(
                self.webhook_secret.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256,
            ).digest()
        ).decode('utf-8')

        if not hmac.compare_digest(expected, signature_header):
            logger.warning('Rejecting MyFatoorah webhook: signature mismatch.')
            return False

        return True

    def handle_processor_response(self, response, basket=None):
        """
        Record a verified MyFatoorah payment.

        Arguments:
            response (dict): A GetPaymentStatus response body. Never the redirect
                query string and never a raw webhook body -- callers must resolve
                those to a verified status response first.

        Keyword Arguments:
            basket (Basket): Basket whose contents were purchased.

        Returns:
            HandledProcessorResponse
        """
        data = response.get('Data') or {}
        transaction = self.get_successful_transaction(response)

        invoice_id = data.get('InvoiceId')
        # PaymentId identifies the individual transaction, which is what a future
        # refund would reference; fall back to the invoice if it is missing.
        transaction_id = transaction.get('PaymentId') or invoice_id

        card = transaction.get('Card') or {}
        # Already masked by MyFatoorah -- we never see a full PAN.
        card_number = card.get('Number') or transaction.get('CardNumber')
        card_type = card.get('Brand') or transaction.get('PaymentGateway')

        self.record_processor_response(_scrub(response), transaction_id=transaction_id, basket=basket)
        logger.info(
            'Recorded MyFatoorah payment [%s] on invoice [%s] for basket [%d].',
            transaction_id,
            invoice_id,
            basket.id,
        )

        # Amount and currency come from the gateway, not the basket. Callers verify
        # they agree with the basket before reaching this point.
        total = self.get_invoice_value(response)
        currency = transaction.get('PaidCurrency') or basket.currency

        return HandledProcessorResponse(
            transaction_id=transaction_id,
            total=total,
            currency=currency,
            card_number=card_number,
            card_type=card_type,
        )

    def issue_credit(self, order_number, basket, reference_number, amount, currency):
        raise NotImplementedError('The MyFatoorah payment processor does not support refunds.')
