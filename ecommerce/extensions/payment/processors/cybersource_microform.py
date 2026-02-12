""" Cybersource Microform payment processor. """
from __future__ import absolute_import, unicode_literals

import json
import logging
from urllib.parse import urlsplit

import crum
from CyberSource import (
    CreatePaymentRequest,
    GeneratePublicKeyRequest,
    KeyGenerationApi,
    PaymentsApi,
    Ptsv2paymentsClientReferenceInformation,
    Ptsv2paymentsMerchantDefinedInformation,
    Ptsv2paymentsOrderInformation,
    Ptsv2paymentsOrderInformationAmountDetails,
    Ptsv2paymentsOrderInformationBillTo,
    Ptsv2paymentsOrderInformationInvoiceDetails,
    Ptsv2paymentsOrderInformationLineItems,
    Ptsv2paymentsProcessingInformation,
    Ptsv2paymentsTokenInformation,
)
from CyberSource.rest import ApiException
from django.conf import settings
from oscar.apps.payment.exceptions import GatewayError, TransactionDeclined

from ecommerce.extensions.payment.exceptions import InvalidCybersourceDecision
from ecommerce.extensions.payment.forms import CybersourceMicroformPaymentForm
from ecommerce.extensions.payment.processors import (
    BaseClientSidePaymentProcessor,
    HandledProcessorResponse,
)
from ecommerce.extensions.payment.utils import (
    LxmlObjectJsonEncoder,
    clean_field_value,
    get_basket_program_uuid,
)

logger = logging.getLogger(__name__)
PRODUCTION_HOST_NAME = "api.cybersource.com"
SANDBOX_HOST_NAME = "apitest.cybersource.com"

def del_none(d):  # pragma: no cover
    """Delete None values in dict."""
    for key, value in list(d.items()):
        if value is None:
            del d[key]
        elif isinstance(value, dict):
            del_none(value)
    return d


class CybersourceMicroform(BaseClientSidePaymentProcessor):
    NAME = "cybersource_microform"

    def __init__(self, site):
        """
        Constructs a new instance of the Cybersource Microform processor.
        Raises:
            KeyError: If no settings configured for this payment processor.
        """
        super(CybersourceMicroform, self).__init__(site)
        self.request = crum.get_current_request()
        configuration = self.configuration
        self.target_origin = configuration.get("target_origin", None)
        self.language_code = settings.LANGUAGE_CODE
        self.connect_timeout = configuration.get("api_connect_timeout", 5.0)
        self.read_timeout = configuration.get("api_read_timeout", 5.0)

        self.cybersource_api_config = {
            "authentication_type": "http_signature",
            "run_environment": PRODUCTION_HOST_NAME
            if configuration["production_mode"]
            else SANDBOX_HOST_NAME,
            "merchantid": configuration["merchant_id"],
            "merchant_keyid": configuration["merchant_key_id"],
            "merchant_secretkey": configuration["merchant_secret_key"],
            "enable_log": False,
        }
        self.context_key = None

    @property
    def cybersource_form(self):
        return CybersourceMicroformPaymentForm(
            user=self.request.user,
            request=self.request,
            initial={"basket": self.request.basket},
            label_suffix="",
        )

    @property
    def get_context(self):
        """Initialize and store context on page load."""
        if not self.context_key:
            try:
                self.context_key = self.get_capture_context()
            except ApiException as error:
                if error.body:
                    raise GatewayError(error.body)
        return self.context_key

    def get_target_origin(self):
        """Target origin for flex form"""
        if self.target_origin:
            return self.target_origin

        parts = urlsplit(str(self.request.site))

        if parts.netloc:
            return "https://" + parts.netloc
        return "https://" + parts.path

    def get_capture_context(self):  # pragma: no cover
        """Capture context for initializing and processing payment fields on the form page."""
        requestObj = GeneratePublicKeyRequest(
            encryption_type="RsaOaep256", target_origin=self.get_target_origin()
        )

        requestObj = del_none(requestObj.__dict__)
        requestObj = json.dumps(requestObj)

        api_instance = KeyGenerationApi(self.cybersource_api_config)
        return_data, _, _ = api_instance.generate_public_key(
            generate_public_key_request=requestObj,
            format="JWT",
            _request_timeout=(self.connect_timeout, self.read_timeout),
        )
        return return_data.key_id

    def get_transaction_parameters(self, basket, form_data, request=None, **kwargs):
        """Get the transaction parameters and Process a payment using the transient token."""
        transient_token_jwt = form_data["token"]
        try:
            payment_processor_response = self.payment_with_transient_token(
                basket, form_data, transient_token_jwt, request.user.email
            )
            return payment_processor_response
        except ApiException as error:
            self.record_processor_response(
                error.body, transaction_id=None, basket=basket
            )
            logger.exception("Payment failed for basket [%d].", basket.id)
            raise GatewayError(error.reason)

    def payment_with_transient_token(self, basket, form_data, transient_token_jwt, user_email):
        """Process a payment using the transient token and using user data."""
        clientReferenceInformation = Ptsv2paymentsClientReferenceInformation(
            code=basket.order_number,
        )

        processingInformation = Ptsv2paymentsProcessingInformation(
            capture=True,
            purchase_level="3",
        )

        orderInformationAmountDetails = Ptsv2paymentsOrderInformationAmountDetails(
            total_amount=str(basket.total_incl_tax),
            currency=basket.currency,
        )

        orderInformationBillTo = Ptsv2paymentsOrderInformationBillTo(
            first_name=form_data["first_name"],
            last_name=form_data["last_name"],
            address1=form_data["address_line1"],
            address2=form_data["address_line2"],
            locality=form_data["city"],
            administrative_area=form_data["state"],
            postal_code=form_data["postal_code"],
            country=form_data["country"],
            email=user_email,
        )
        orderInformationInvoiceDetails = Ptsv2paymentsOrderInformationInvoiceDetails(
            purchase_order_number="BLANK"
        )

        merchantDefinedInformation = []
        program_uuid = get_basket_program_uuid(basket)
        if program_uuid:
            programInfo = Ptsv2paymentsMerchantDefinedInformation(
                key="1",
                value="program,{program_uuid}".format(program_uuid=program_uuid),
            )
            merchantDefinedInformation.append(programInfo.__dict__)

        merchantDataIndex = 2
        orderInformationLineItems = []
        for line in basket.all_lines():
            orderInformationLineItem = Ptsv2paymentsOrderInformationLineItems(
                product_name=clean_field_value(line.product.title),
                product_code=line.product.get_product_class().slug,
                product_sku=line.stockrecord.partner_sku,
                quantity=line.quantity,
                unit_price=str(line.unit_price_incl_tax),
                total_amount=str(line.line_price_incl_tax_incl_discounts),
                unit_of_measure="ITM",
                discount_amount=str(line.discount_value),
                discount_applied=True,
                amount_includes_tax=True,
                tax_amount=str(line.line_tax),
                tax_rate="0",
            )
            orderInformationLineItems.append(orderInformationLineItem.__dict__)
            line_course = line.product.course
            if line_course:
                courseInfo = Ptsv2paymentsMerchantDefinedInformation(
                    key=str(merchantDataIndex),
                    value="course,{course_id},{course_type}".format(
                        course_id=line_course.id if line_course else None,
                        course_type=line_course.type if line_course else None,
                    ),
                )
                merchantDefinedInformation.append(courseInfo.__dict__)
                merchantDataIndex += 1

        orderInformation = Ptsv2paymentsOrderInformation(
            amount_details=orderInformationAmountDetails.__dict__,
            bill_to=orderInformationBillTo.__dict__,
            line_items=orderInformationLineItems,
            invoice_details=orderInformationInvoiceDetails.__dict__,
        )

        tokenInformation = Ptsv2paymentsTokenInformation(
            transient_token_jwt=transient_token_jwt,
        )

        requestObj = CreatePaymentRequest(
            client_reference_information=clientReferenceInformation.__dict__,
            processing_information=processingInformation.__dict__,
            token_information=tokenInformation.__dict__,
            order_information=orderInformation.__dict__,
            merchant_defined_information=merchantDefinedInformation,
        )

        requestObj = del_none(requestObj.__dict__)

        self.record_processor_response(
            requestObj, transaction_id="[REQUEST]", basket=basket
        )

        api_instance = PaymentsApi(self.cybersource_api_config)

        payment_processor_response, _, _ = api_instance.create_payment(
            json.dumps(requestObj),
            _request_timeout=(self.connect_timeout, self.read_timeout),
        )
        return payment_processor_response

    def handle_processor_response(self, response, basket=None):
        """
        Handle a response from CyberSource and Proceed only if the payment is authorized; otherwise,
        raise an exception.
        """
        currency = basket.currency

        transaction_dict = LxmlObjectJsonEncoder().encode(response)

        transaction_id = response.processor_information.transaction_id

        self.record_processor_response(
            transaction_dict, transaction_id=transaction_id, basket=basket
        )

        if response.status == "AUTHORIZED":
            logger.info(
                "Successfully created Cybersource Microform charge [%s] for basket [%d].",
                "merchant_id",
                basket.id,
            )

            total = basket.total_incl_tax
            card_type = self.NAME

            return HandledProcessorResponse(
                transaction_id=transaction_id,
                total=total,
                currency=currency,
                card_number="XXXX",
                card_type=card_type,
            )

        elif response.status == "DECLINED":
            if response.error_information:
                raise TransactionDeclined(response.error_information)
            raise TransactionDeclined(response.status)

        else:
            if response.error_information:
                raise InvalidCybersourceDecision(response.error_information)
            raise InvalidCybersourceDecision(response.status)

    def issue_credit(self, order_number, basket, reference_number, amount, currency):
        raise NotImplementedError(
            "Cybersource payment processor does not support refunds."
        )
