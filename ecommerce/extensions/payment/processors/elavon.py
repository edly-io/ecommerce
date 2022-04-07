import urllib.parse
import crum
from datetime import datetime
import json
import logging
import requests
from six.moves.urllib.parse import urljoin

from oscar.apps.payment.exceptions import GatewayError

from ecommerce.extensions.checkout.utils import get_receipt_page_url
from ecommerce.extensions.payment.models import ElavonPaymentRecord
from ecommerce.extensions.payment.forms import ElavonPaymentForm
from ecommerce.extensions.payment.processors import BaseClientSidePaymentProcessor, HandledProcessorResponse

logger = logging.getLogger(__name__)


class Elavon(BaseClientSidePaymentProcessor):
    NAME = 'elavon'
    template_name = 'payment/elavon.html'

    def __init__(self, site):
        """
        Constructs a new instance of the LumsxPay processor.

        Raises:
            KeyError: If no settings configured for this payment processor.
        """
        super(Elavon, self).__init__(site)
        self.request = crum.get_current_request()
        configuration = self.configuration
        self.merchant_id = configuration['merchant_id']
        self.merchant_user_id = configuration['merchant_user_id']
        self.merchant_pin = configuration['merchant_pin']
        self.base_url = configuration['base_url']

    def _get_request_payload(self, basket):
        """
        Get Cowpay request payload.
        """
        merchant_reference_id = '{order_number}{current_timestamp}'.format(
            order_number=basket.order_number, current_timestamp=int(datetime.now().timestamp())
        )
        logging.info('basket %s %s', basket.order_number, basket.total_incl_tax)
        return {
            'ssl_merchant_id': self.merchant_id,
            'ssl_user_id': self.merchant_user_id,
            'ssl_pin': self.merchant_pin,
            'ssl_transaction_type': 'ccsale',
            'ssl_amount': str(basket.total_incl_tax),
            'ssl_merchant_txn_id': merchant_reference_id,
            'description': 'Edly Elavon transaction for order number: {order_number}.'.format(
                order_number=basket.order_number
            )
        }

    @property
    def elavon_token(self):
        elavon_url = self.base_url
        basket = self.request.basket
        payload = self._get_request_payload(basket)
        response = requests.post(elavon_url, params=payload)
        return urllib.parse.quote(response.text.encode('utf-8'))

    @property
    def receipt_page_url(self):
        site = self.request.site
        basket = self.request.user.baskets.filter(site=site, lines__isnull=False).last()
        return get_receipt_page_url(site.siteconfiguration, order_number=basket.order_number)

    @property
    def elavon_form(self):
        return ElavonPaymentForm(
            user=self.request.user,
            request=self.request,
            initial={'basket': self.request.basket},
            label_suffix=''
        )

    def get_transaction_parameters(self, basket, request=None, **kwargs):
        elavon_url = self.base_url
        basket = self.request.basket
        payload = self._get_request_payload(basket)
        response = requests.post(elavon_url, params=payload)
        if response.status_code == 200:
            logger.info('elavon token %s', urllib.parse.quote(response.text.encode('utf-8')))
            return urllib.parse.quote(response.text.encode('utf-8'))
        else:
            raise GatewayError('Elavon API call failed due to %s', response.text)

    def handle_processor_response(self, response, basket=None):
        currency = basket.currency
        merchant_id = response['cowpay_reference_id']
        gateway_id = response['payment_gateway_reference_id']

        ElavonPaymentRecord.objects.get_or_create(
            payment_gateway_reference_id=gateway_id,
            defaults=dict(
                basket=basket,
                merchant_reference_id=merchant_id,
                payment_gateway_reference_id=gateway_id,
                site=self.site,
                user_id=response['user'],
            )
        )

        self.record_processor_response(response, transaction_id=merchant_id, basket=basket)
        logger.info('Successfully created Elavon charge [%s] for basket [%d].', merchant_id, basket.id)

        total = basket.total_incl_tax
        card_type = self.NAME

        return HandledProcessorResponse(
            transaction_id=merchant_id,
            total=total,
            currency=currency,
            card_number=gateway_id,
            card_type=card_type
        )

    def issue_credit(self, order_number, basket, reference_number, amount, currency):
        raise NotImplementedError('The Cowpay payment processor does not support refunds.')
