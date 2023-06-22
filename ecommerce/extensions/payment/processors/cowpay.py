import crum
from datetime import datetime
import hashlib
import json
import logging
import requests
from six.moves.urllib.parse import urljoin

from oscar.apps.payment.exceptions import GatewayError

from ecommerce.extensions.checkout.utils import get_receipt_page_url
from ecommerce.extensions.payment.forms import CowpayFawryPaymentForm
from ecommerce.extensions.payment.models import CowpayPaymentRecord
from ecommerce.extensions.payment.processors import BaseClientSidePaymentProcessor, HandledProcessorResponse

logger = logging.getLogger(__name__)


class Cowpay(BaseClientSidePaymentProcessor):
    NAME = 'cowpay'
    template_name = 'payment/cowpay.html'

    def __init__(self, site):
        """
        Constructs a new instance of the LumsxPay processor.

        Raises:
            KeyError: If no settings configured for this payment processor.
        """
        super(Cowpay, self).__init__(site)
        self.request = crum.get_current_request()
        configuration = self.configuration
        self.token = configuration['token']
        self.base_url = configuration['base_url']
        self.merchant_code = configuration['merchant_code']
        self.merchant_hash_key = configuration['merchant_hash_key']
        self.mobile_number_for_iframe_token = configuration['mobile_number_for_iframe_token']

    def _get_request_header(self):
        """
        Get Cowpay request header.
        """
        return {
            'Authorization': 'Bearer {token}'.format(token=self.token),
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    def _get_request_payload(self, basket, customer_name, customer_mobile, customer_email):
        """
        Get Cowpay request payload.
        """
        merchant_reference_id = '{order_number}{current_timestamp}'.format(
            order_number=basket.order_number, current_timestamp=int(datetime.now().timestamp())
        )
        return json.dumps({
            'merchant_reference_id': merchant_reference_id,
            'customer_merchant_profile_id': self.request.user.id,
            'customer_name': customer_name,
            'customer_mobile': customer_mobile,
            'customer_email': customer_email,
            'amount': str(basket.total_incl_tax),
            'currency_code': basket.currency,
            'signature': hashlib.sha256('{merchant_code}{merchant_reference_id}{customer_merchant_profile_id}{amount}{hash_key}'.format(
                merchant_code=self.merchant_code,
                merchant_reference_id=merchant_reference_id,
                customer_merchant_profile_id=self.request.user.id,
                amount=basket.total_incl_tax,
                hash_key=self.merchant_hash_key
            ).encode()).hexdigest(),
            'description': 'Edly iframe transaction for order number: {order_number}.'.format(
                order_number=basket.order_number
            )
        })

    @property
    def fawry_form(self):
        return CowpayFawryPaymentForm(
            user=self.request.user,
            request=self.request,
            initial={'basket': self.request.basket},
            label_suffix=''
        )

    @property
    def iframe_token(self):
        cowpay_url = urljoin(self.base_url, '/api/v2/charge/card/init')
        headers = self._get_request_header()
        basket = self.request.basket
        payload = self._get_request_payload(
            basket, basket.owner.get_full_name(), self.mobile_number_for_iframe_token, self.request.user.email
        )
        response = requests.request('POST', cowpay_url, headers=headers, data=payload)
        response = response.json()
        if not response.get('success'):
            logger.exception('Unable to retrieve cowpay iframe token because %s', response.get('errors'))

        return response.get('token')

    @property
    def receipt_page_url(self):
        site = self.request.site
        basket = self.request.user.baskets.filter(site=site, lines__isnull=False).last()
        return get_receipt_page_url(site.siteconfiguration, order_number=basket.order_number)

    def get_transaction_parameters(self, basket, request=None, **kwargs):
        cowpay_url = urljoin(self.base_url, '/api/v2/charge/fawry')
        headers = self._get_request_header()
        data = kwargs.get('form_data')
        if data:
            payload = self._get_request_payload(
                basket, data['customer_name'], data['customer_mobile'], data['customer_email']
            )
            response = requests.request('POST', cowpay_url, headers=headers, data=payload)
            response = response.json()
            if response.get('success'):
                return response
            else:
                raise GatewayError('Cowpay API call failed due to %s', response.get('errors'))

        else:
            raise GatewayError('Form data not available',)

    def handle_processor_response(self, response, basket=None):
        currency = basket.currency
        merchant_id = response['cowpay_reference_id']
        gateway_id = response['payment_gateway_reference_id']

        CowpayPaymentRecord.objects.get_or_create(
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
        logger.info('Successfully created Cowpay charge [%s] for basket [%d].', merchant_id, basket.id)

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
