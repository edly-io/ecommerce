""" Cybersource Microform payment processor. """
from __future__ import absolute_import, unicode_literals

import crum
import logging

from django.conf import settings
from oscar.core.loading import get_class, get_model

from ecommerce.extensions.payment.forms import CybersourceMicroformPaymentForm
from ecommerce.extensions.payment.processors import BaseClientSidePaymentProcessor, HandledProcessorResponse
from ecommerce.extensions.payment.utils import LxmlObjectJsonEncoder

logger = logging.getLogger(__name__)
Applicator = get_class('offer.applicator', 'Applicator')
PaymentProcessorResponse = get_model('payment', 'PaymentProcessorResponse')

AUTH_CAPTURE_TRANSACTION_TYPE = "authCaptureTransaction"


class CybersourceMicroform(BaseClientSidePaymentProcessor):
    NAME = 'cybersource_microform'
    template_name = 'payment/cybersource_microform.html'

    def __init__(self, site):
        """
        Constructs a new instance of the Cybersource Microform processor.
        Raises:
            KeyError: If no settings configured for this payment processor.
        """
        super(CybersourceMicroform, self).__init__(site)
        self.request = crum.get_current_request()
        configuration = self.configuration
        self.base_url = configuration['base_url']
        self.merchant_id = configuration['merchant_id']
        self.transaction_key = configuration['transaction_key']
        self.send_level_2_3_details = configuration.get('send_level_2_3_details', True)
        self.language_code = settings.LANGUAGE_CODE

        self.flex_run_environment = configuration.get('flex_run_environment', 'cybersource.environment.SANDBOX')
        self.flex_shared_secret_key_id = configuration.get('flex_shared_secret_key_id')
        self.flex_shared_secret_key = configuration.get('flex_shared_secret_key')
        self.flex_target_origin = None

        self.connect_timeout = configuration.get('api_connect_timeout', 0.5)
        self.read_timeout = configuration.get('api_read_timeout', 5.0)

        self.cybersource_api_config = {
            'authentication_type': 'http_signature',
            'run_environment': self.flex_run_environment,
            'merchantid': self.merchant_id,
            'merchant_keyid': self.flex_shared_secret_key_id,
            'merchant_secretkey': self.flex_shared_secret_key,
            'enable_log': False,
        }

    @property
    def cybersource_form(self):
        return CybersourceMicroformPaymentForm(
            user=self.request.user,
            request=self.request,
            initial={'basket': self.request.basket},
            label_suffix=''
        )

    def get_capture_context(self, request):  # pragma: no cover
        # To delete None values in Input Request Json body
        session = request.session

        requestObj = GeneratePublicKeyRequest(
            encryption_type='RsaOaep256',
            target_origin=self.flex_target_origin,
        )
        requestObj = del_none(requestObj.__dict__)
        requestObj = json.dumps(requestObj)

        api_instance = KeyGenerationApi(self.cybersource_api_config)
        return_data, _, _ = api_instance.generate_public_key(
            generate_public_key_request=requestObj,
            format='JWT',
            _request_timeout=(self.connect_timeout, self.read_timeout),
        )

        new_capture_context = {'key_id': return_data.key_id}

        capture_contexts = [
            capture_context
            for (capture_context, _)
            in self._unexpired_capture_contexts(session)
        ]
        capture_contexts.insert(0, new_capture_context)
        # Prevent session size explosion by limiting the number of recorded capture contexts
        session['capture_contexts'] = capture_contexts[:20]
        return new_capture_context

    def _unexpired_capture_contexts(self, session):
        """
        Return all unexpired capture contexts in the supplied session.

        Arguments:
            session (Session): the current user session

        Returns: [(capture_context, decoded_capture_context)]
            The list of all still-valid capture contexts, both encoded and decoded
        """
        now = datetime.datetime.now(UTC)
        return [
            (capture_context, decoded_capture_context)
            for (capture_context, decoded_capture_context)
            in (
                (capture_context, jwt.decode(capture_context['key_id'], verify=False))
                for capture_context
                in session.get('capture_contexts', [])
            )
            if not datetime.datetime.fromtimestamp(decoded_capture_context['exp'], tz=UTC) < now
        ]

    def get_transaction_parameters(self, basket, request=None, **kwargs):
        response = []
        return response

    def handle_processor_response(self, response, basket=None):
        currency = basket.currency
        transaction_id = response.transactionResponse.transId if hasattr(response.transactionResponse, 'transId') else None
        transaction_dict = LxmlObjectJsonEncoder().encode(response)

        self.record_processor_response(transaction_dict, transaction_id=transaction_id, basket=basket)
        logger.info('Successfully created Cybersource Microform charge [%s] for basket [%d].', 'merchant_id', basket.id)

        total = basket.total_incl_tax
        card_type = self.NAME

        return HandledProcessorResponse(
            transaction_id=transaction_id,
            total=total,
            currency=currency,
            card_number='XXXX',
            card_type=card_type
        )

    def issue_credit(self, order_number, basket, reference_number, amount, currency):
        raise NotImplementedError('Authorizenet payment processor does not support refunds.')
