""" Cybersource Microform payment processor. """
from __future__ import absolute_import, unicode_literals

import crum
import logging
import datetime

from django.conf import settings
from oscar.core.loading import get_class, get_model
from oscar.apps.payment.exceptions import GatewayError, TransactionDeclined, UserCancelled
from ecommerce.extensions.payment.forms import CybersourceMicroformPaymentForm
from ecommerce.extensions.payment.processors import (
    BaseClientSidePaymentProcessor,
    HandledProcessorResponse,
)
from ecommerce.extensions.payment.utils import LxmlObjectJsonEncoder
from ecommerce.extensions.payment.utils import (
    clean_field_value,
    get_basket_program_uuid,
)
from ecommerce.extensions.payment.exceptions import (
    AuthorizationError,
    DuplicateReferenceNumber,
    ExcessivePaymentForOrderError,
    InvalidCybersourceDecision,
    InvalidSignatureError,
    PartialAuthorizationError,
    PCIViolation,
    ProcessorMisconfiguredError,
    RedundantPaymentNotificationError
)

import base64
import datetime
import json
import logging
import uuid
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Optional

import jwt
import jwt.exceptions
import waffle

from CyberSource import (
    AuthReversalRequest,
    CreatePaymentRequest,
    GeneratePublicKeyRequest,
    KeyGenerationApi,
    PaymentsApi,
    Ptsv2paymentsClientReferenceInformation,
    Ptsv2paymentsidreversalsClientReferenceInformation,
    Ptsv2paymentsidreversalsReversalInformation,
    Ptsv2paymentsidreversalsReversalInformationAmountDetails,
    Ptsv2paymentsMerchantDefinedInformation,
    Ptsv2paymentsOrderInformation,
    Ptsv2paymentsOrderInformationAmountDetails,
    Ptsv2paymentsOrderInformationBillTo,
    Ptsv2paymentsOrderInformationInvoiceDetails,
    Ptsv2paymentsOrderInformationLineItems,
    Ptsv2paymentsProcessingInformation,
    Ptsv2paymentsTokenInformation,
    ReversalApi,
)

# import CyberSource
from CyberSource.rest import ApiException
from django.conf import settings
from django.urls import reverse
from jwt.algorithms import RSAAlgorithm
from oscar.apps.payment.exceptions import (
    GatewayError,
    TransactionDeclined,
    UserCancelled,
)
from oscar.core.loading import get_class, get_model
from pytz import UTC
from zeep import Client
from zeep.helpers import serialize_object
from zeep.wsse import UsernameToken

logger = logging.getLogger(__name__)
Applicator = get_class("offer.applicator", "Applicator")
PaymentProcessorResponse = get_model("payment", "PaymentProcessorResponse")

AUTH_CAPTURE_TRANSACTION_TYPE = "authCaptureTransaction"

# class Decision(Enum):
#     accept = 'AUTHORIZED'
#     cancel = 'CANCEL'
#     decline = 'DECLINED'
#     error = 'ERROR'
#     review = 'REVIEW'
#     authorized_pending_review = 'AUTHORIZED_PENDING_REVIEW'

def del_none(d):  # pragma: no cover
    for key, value in list(d.items()):
        if value is None:
            del d[key]
        elif isinstance(value, dict):
            del_none(value)
    return d


class CybersourceMicroform(BaseClientSidePaymentProcessor):
    NAME = "cybersource_microform"
    template_name = "payment/cybersource_microform.html"

    def __init__(self, site):
        """
        Constructs a new instance of the Cybersource Microform processor.
        Raises:
            KeyError: If no settings configured for this payment processor.
        """
        super(CybersourceMicroform, self).__init__(site)
        # import pdb; pdb.set_trace()
        print("CybersourceMicroform processors xc14")
        self.request = crum.get_current_request()
        configuration = self.configuration
        self.base_url = configuration["base_url"]
        self.merchant_id = configuration["merchant_id"]
        self.transaction_key = configuration["transaction_key"]
        self.send_level_2_3_details = configuration.get("send_level_2_3_details", True)
        self.language_code = settings.LANGUAGE_CODE

        self.flex_run_environment = configuration.get(
            "flex_run_environment", "cybersource.environment.SANDBOX"
        )
        self.flex_shared_secret_key_id = configuration.get("flex_shared_secret_key_id")
        self.flex_shared_secret_key = configuration.get("flex_shared_secret_key")
        self.flex_target_origin = None

        self.connect_timeout = configuration.get("api_connect_timeout", 10.0)
        self.read_timeout = configuration.get("api_read_timeout", 10.0)

        # self.cybersource_api_config = {
        #     'authentication_type': 'http_signature',
        #     'run_environment': self.flex_run_environment,
        #     'merchantid': self.merchant_id,
        #     'merchant_keyid': self.flex_shared_secret_key_id,
        #     'merchant_secretkey': self.flex_shared_secret_key,
        #     'enable_log': False,
        # }

        self.cybersource_api_config = {
            "authentication_type": "http_signature",
            "run_environment": "apitest.cybersource.com",
            # 'run_environment': self.flex_run_environment,
            "merchantid": "edly400",
            "merchant_keyid": "6128d4be-b5b1-4fa4-8df5-ffc4c00e1114",
            "merchant_secretkey": "82W/a35zNTtYo5a5BOFwc3AQWsCJ73kNeI1Csyzw2sI=",
            "enable_log": False,
        }
        self.context_key = None
        # self.get_capture_context(self.request)

    @property
    def cybersource_form(self):
        print("here cybero")
        print("xc13 form")
        return CybersourceMicroformPaymentForm(
            user=self.request.user,
            request=self.request,
            initial={"basket": self.request.basket},
            label_suffix="",
        )

    @property
    def get_context(self):
        if not self.context_key:
            self.context_key = self.get_capture_context(self.request)
        return self.context_key

    @property
    def cancel_page_url(self):
        return "ho ho ho"

    def get_capture_context(self, request):  # pragma: no cover
        # To delete None values in Input Request Json body
        print("xc14 wa wa")
        session = request.session
        requestObj = GeneratePublicKeyRequest(
            encryption_type="RsaOaep256",
            target_origin="https://dev.payments.multisitesdev.edly.io",
        )
        print(requestObj)
        requestObj = del_none(requestObj.__dict__)
        requestObj = json.dumps(requestObj)

        api_instance = KeyGenerationApi(self.cybersource_api_config)
        return_data, _, _ = api_instance.generate_public_key(
            generate_public_key_request=requestObj,
            format="JWT",
            _request_timeout=(self.connect_timeout, self.read_timeout),
        )
        # if return_data:
        #     logger.info("Successfully-zx with site [%s] ", str(self.request.site))

        new_capture_context = {"key_id": return_data.key_id}
        return return_data.key_id

    # self.context_key = return_data.key_id
    # print('key ', return_data)
    # capture_contexts = [
    #     capture_context
    #     for (capture_context, _)
    #     in self._unexpired_capture_contexts(session)
    # ]
    # capture_contexts.insert(0, new_capture_context)
    # # Prevent session size explosion by limiting the number of recorded capture contexts
    # session['capture_contexts'] = capture_contexts[:20]
    # return new_capture_context

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
            for (capture_context, decoded_capture_context) in (
                (capture_context, jwt.decode(capture_context["key_id"], verify=False))
                for capture_context in session.get("capture_contexts", [])
            )
            if not datetime.datetime.fromtimestamp(
                decoded_capture_context["exp"], tz=UTC
            )
            < now
        ]

    def get_transaction_parameters(self, basket, form_data, request=None, **kwargs):
        print("xc13 get_transaction_parameters")
        # ttj = "\"eyJraWQiOiIwOE1zNXJ3aloySXZnekZWeDliZ2dQNGxhNXdFa2FQZSIsImFsZyI6IlJTMjU2In0.eyJkYXRhIjp7ImV4cGlyYXRpb25ZZWFyIjoiMjAyOSIsIm51bWJlciI6IjQwMTI…"
        #  Dummy example using your provided keys
        ttj = "eyJraWQiOiIwOFFybkxJQTFuQ1RUd2R6WkZkYmcwQVpoQUxyS3dYdiIsImFsZyI6IlJTMjU2In0.eyJkYXRhIjp7ImV4cGlyYXRpb25ZZWFyIjoiMjAyNCIsIm51bWJlciI6IjU1NTU1NVhYWFhYWDQ0NDQiLCJleHBpcmF0aW9uTW9udGgiOiIxMSIsInR5cGUiOiIwMDIifSwiaXNzIjoiRmxleC8wOCIsImV4cCI6MTcwNTU2Nzc1OCwidHlwZSI6Im1mLTAuMTEuMCIsImlhdCI6MTcwNTU2Njg1OCwianRpIjoiMUU0NEFDT01SM1RTNFVZOUc1NEVESEJPVjY2WVVLMjQyV1pSS1E1QTdTNDY0Q1pJQjlOSTY1QThFNjBFMkUwRSIsImNvbnRlbnQiOnsicGF5bWVudEluZm9ybWF0aW9uIjp7ImNhcmQiOnsiZXhwaXJhdGlvblllYXIiOnsidmFsdWUiOiIyMDI0In0sIm51bWJlciI6eyJtYXNrZWRWYWx1ZSI6IlhYWFhYWFhYWFhYWDQ0NDQiLCJiaW4iOiI1NTU1NTUifSwic2VjdXJpdHlDb2RlIjp7fSwiZXhwaXJhdGlvbk1vbnRoIjp7InZhbHVlIjoiMTEifSwidHlwZSI6eyJ2YWx1ZSI6IjAwMiJ9fX19fQ.iMPp2QaiLmx-"
        print('lmnop--1 ',form_data)
        # form_data = {
        #     "first_name": "John",
        #     "last_name": "Doe",
        #     "address_line1": "123 Main Street",
        #     "address_line2": "Apt 4B",
        #     "city": "Anytown",
        #     "state": "CA",
        #     "postal_code": "12345",
        #     # invalid value for `country`, length must be less than or equal to `2`
        #     "country": "US",
        # }

        # Create user_data dictionary
        user_data = {
            "first_name": form_data["first_name"],
            "last_name": form_data["last_name"],
            "address_line1": form_data["address_line1"],
            "address_line2": form_data["address_line2"],
            "city": form_data["city"],
            "state": form_data["state"],
            "postal_code": form_data["postal_code"],
            "country": form_data["country"],
        }

        transient_token_jwt = form_data["token"]
        try:
            payment_processor_response = self.payment_with_transient_token(basket,user_data, transient_token_jwt, request.user.email)
            # handle this in handle-processor
            # mn = LxmlObjectJsonEncoder().encode(payment_processor_response)
            # if mn.status != 'AUTHORIZED':
            # if payment_processor_response['status'] != 'AUTHORIZED':
            #     raise InvalidCybersourceDecision(payment_processor_response['status'])
            return payment_processor_response
        except ApiException as error:
            print('unique-- ', error)
            print('uni9 ,',error.body)
            self.record_processor_response(error.body, transaction_id=None, basket=basket)
            logger.exception('Payment failed for basket [%d].', basket,id)
            # This will display the generic error on the frontend
            # raise InvalidCybersourceDecision('DECLINED')
            raise GatewayError(error.reason)
        
        # if payment_processor_response['status'] != 'AUTHORIZED':
        #     raise InvalidCybersourceDecision(payment_processor_response['status'])


        # if response.decision != Decision.accept:
        #     if response.duplicate_payment:
        #         # This means user submitted payment request twice within 15 min.
        #         # We need to check if user first payment notification was handled successfuly and user has an order
        #         # if user has an order we can raise DuplicateReferenceNumber exception else we need to continue
        #         # the order creation process. to upgrade user in correct course mode.
        #         if Order.objects.filter(number=response.order_id).exists():
        #             raise DuplicateReferenceNumber

        #         # If we failed to capture a successful payment, and then the user submits payment again within a 15
        #         # minute window, then we get a duplicate payment message with no amount attached. We can't create an
        #         # order in that case.
        #         if response.total is None:
        #             raise DuplicateReferenceNumber

        #         logger.info(
        #             'Received duplicate CyberSource payment notification for basket [%d] which is not associated '
        #             'with any existing order. Continuing to validation and order creation processes.',
        #             basket.id,
        #         )
        #     else:
        #         if response.decision == Decision.authorized_pending_review:
        #             self.reverse_payment_api(response, "Automatic reversal of AUTHORIZED_PENDING_REVIEW", basket)

        #         raise {
        #             Decision.cancel: UserCancelled,
        #             Decision.decline: TransactionDeclined,
        #             Decision.error: GatewayError,
        #             Decision.review: AuthorizationError,
        #             Decision.authorized_pending_review: TransactionDeclined,
        #         }.get(response.decision, InvalidCybersourceDecision(response.decision))

        # transaction_id = response.transaction_id
        # if transaction_id and response.decision == Decision.accept:
        #     if Order.objects.filter(number=response.order_id).exists():
        #         if PaymentProcessorResponse.objects.filter(transaction_id=transaction_id).exists():
        #             raise RedundantPaymentNotificationError
        #         raise ExcessivePaymentForOrderError

        # if response.partial_authorization:
        #     # Raise an exception if the authorized amount differs from the requested amount.
        #     # Note (CCB): We should never reach this point in production since partial authorization is disabled
        #     # for our account, and should remain that way until we have a proper solution to allowing users to
        #     # complete authorization for the entire order
        #     raise PartialAuthorizationError

        return HandledProcessorResponse(
            transaction_id=response.transaction_id,
            total=response.total,
            currency=response.currency,
            card_number=response.card_number,
            card_type=response.card_type
        )
        

        response = []
        return response

    def payment_with_transient_token(
        self, basket, form_data, transient_token_jwt, user_email
    ):
        """
        app.post('/receipt', function (req, res) {

        var tokenResponse = JSON.parse(req.body.flexresponse)
        console.log('Transient token for payment is: ' + JSON.stringify(tokenResponse));

         try {

                var instance = new cybersourceRestApi.PaymentsApi(configObj);

                var clientReferenceInformation = new cybersourceRestApi.Ptsv2paymentsClientReferenceInformation();
                clientReferenceInformation.code = 'test_flex_payment';

                var processingInformation = new cybersourceRestApi.Ptsv2paymentsProcessingInformation();
                processingInformation.commerceIndicator = 'internet';

                var amountDetails = new cybersourceRestApi.Ptsv2paymentsOrderInformationAmountDetails();
                amountDetails.totalAmount = '102.21';
                amountDetails.currency = 'USD';

                var billTo = new cybersourceRestApi.Ptsv2paymentsOrderInformationBillTo();
                billTo.country = 'US';
                billTo.firstName = 'John';
                billTo.lastName = 'Deo';
                billTo.phoneNumber = '4158880000';
                billTo.address1 = 'test';
                billTo.postalCode = '94105';
                billTo.locality = 'San Francisco';
                billTo.administrativeArea = 'MI';
                billTo.email = 'test@cybs.com';
                billTo.address2 = 'Address 2';
                billTo.district = 'MI';
                billTo.buildingNumber = '123';

                var orderInformation = new cybersourceRestApi.Ptsv2paymentsOrderInformation();
                orderInformation.amountDetails = amountDetails;
                orderInformation.billTo = billTo;

                // EVERYTHING ABOVE IS JUST NORMAL PAYMENT INFORMATION
                // THIS IS WHERE YOU PLUG IN THE MICROFORM TRANSIENT TOKEN
                var tokenInformation = new cybersourceRestApi.Ptsv2paymentsTokenInformation();
                tokenInformation.transientTokenJwt = tokenResponse;

                var request = new cybersourceRestApi.CreatePaymentRequest();
                request.clientReferenceInformation = clientReferenceInformation;
                request.processingInformation = processingInformation;
                request.orderInformation = orderInformation;
                request.tokenInformation = tokenInformation;

                console.log('\n*************** Process Payment ********************* ');

                instance.createPayment(request, function (error, data, response) {
                    if (error) {
                        console.log('\nError in process a payment : ' + JSON.stringify(error));
                    }
                    else if (data) {
                        console.log('\nData of process a payment : ' + JSON.stringify(data));
                        res.render('receipt', { paymentResponse:  JSON.stringify(data)} );

                    }
                    console.log('\nResponse of process a payment : ' + JSON.stringify(response));
                    console.log('\nResponse Code of process a payment : ' + JSON.stringify(response['status']));
                    callback(error, data);
                });

            } catch (error) {
                console.log(error);
            }

          });
        """
        vc = self.test_response_handling()
        # vc['status'] = 'tinga minga'
        return vc
        clientReferenceInformation = Ptsv2paymentsClientReferenceInformation(
            code=basket.order_number,
        )

        """
        Indicates whether to also include a capture in the submitted authorization request or not.
         Possible values: - `true`: Include a capture with an authorization request.
         - `false`: (default) Do not include a capture with an authorization request. #### Used by Authorization and Capture Optional field.
        """
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

        self.record_processor_response(requestObj, transaction_id='[REQUEST]', basket=basket)

        api_instance = PaymentsApi(self.cybersource_api_config)

        payment_processor_response, _, _ = api_instance.create_payment(
            json.dumps(requestObj),
            _request_timeout=(self.connect_timeout, self.read_timeout),
        )
        print("zx zx 91- ", payment_processor_response)
        return payment_processor_response

    def test_response_handling(self):
        return {
            "client_reference_information": {
                "code": "EDLY-100012",
                "owner_merchant_id": None,
                "submit_local_date_time": None,
            },
            "consumer_authentication_information": {
                "acs_rendering_type": None,
                "acs_transaction_id": None,
                "acs_url": None,
                "authentication_path": None,
                "authentication_result": None,
                "authentication_status_msg": None,
                "authentication_transaction_id": None,
                "authorization_payload": None,
                "cardholder_message": None,
                "cavv": None,
                "cavv_algorithm": None,
                "challenge_cancel_code": None,
                "challenge_required": None,
                "decoupled_authentication_indicator": None,
                "directory_server_error_code": None,
                "directory_server_error_description": None,
                "directory_server_transaction_id": None,
                "eci": None,
                "eci_raw": None,
                "ecommerce_indicator": None,
                "effective_authentication_type": None,
                "indicator": None,
                "interaction_counter": None,
                "ivr": None,
                "network_score": None,
                "pareq": None,
                "pares_status": None,
                "proof_xml": None,
                "proxy_pan": None,
                "sdk_transaction_id": None,
                "signed_pares_status_reason": None,
                "specification_version": None,
                "step_up_url": None,
                "three_ds_server_transaction_id": None,
                "ucaf_authentication_data": None,
                "ucaf_collection_indicator": None,
                "veres_enrolled": None,
                "white_list_status": None,
                "white_list_status_source": None,
                "xid": None,
            },
            "error_information": 'yhaa haha',
            "id": "7055670670356906904953",
            "installment_information": None,
            "issuer_information": {
                "country": None,
                "country_specific_discretionary_data": None,
                "discretionary_data": None,
                "response_code": None,
            },
            "links": {
                "_self": {
                    "href": "/pts/v2/payments/7055670670356906904953",
                    "method": "GET",
                },
                "capture": None,
                "customer": None,
                "instrument_identifier": None,
                "payment_instrument": None,
                "reversal": None,
                "shipping_address": None,
            },
            "order_information": {
                "amount_details": {
                    "authorized_amount": "100.00",
                    "currency": "USD",
                    "total_amount": "100.00",
                },
                "invoice_details": None,
            },
            "payment_information": {
                "account_features": None,
                "bank": None,
                "card": {"suffix": None},
                "customer": None,
                "instrument_identifier": None,
                "payment_instrument": None,
                "shipping_address": None,
                "tokenized_card": {
                    "assurance_level": None,
                    "expiration_month": None,
                    "expiration_year": None,
                    "prefix": None,
                    "requestor_id": None,
                    "suffix": None,
                    "type": "002",
                },
            },
            "point_of_sale_information": {
                "amex_capn_data": None,
                "emv": None,
                "terminal_id": "00123456",
            },
            "processing_information": None,
            "processor_information": {
                "ach_verification": None,
                "amex_verbal_auth_reference_number": None,
                "approval_code": "831000",
                "auth_indicator": "1",
                "avs": {"code": "Y", "code_raw": "Y"},
                "card_verification": None,
                "consumer_authentication_response": None,
                "customer": None,
                "electronic_verification_results": None,
                "forwarded_acquirer_code": None,
                "master_card_authentication_type": None,
                "master_card_service_code": None,
                "master_card_service_reply_code": None,
                "merchant_advice": None,
                "merchant_number": "000000000123456",
                "name": None,
                "network_transaction_id": "0602MCC603474",
                "payment_account_reference_number": None,
                "provider_transaction_id": None,
                "response_category_code": None,
                "response_code": "00",
                "response_code_source": None,
                "response_details": None,
                "routing": None,
                "system_trace_audit_number": None,
                "transaction_id": "0602MCC603474",
                "transaction_integrity_code": None,
            },
            "reconciliation_id": "71731281",
            "risk_information": {
                "case_priority": None,
                "info_codes": {
                    "address": ["UNV-ADDR"],
                    "customer_list": None,
                    "global_velocity": None,
                    "identity_change": None,
                    "internet": None,
                    "phone": None,
                    "suspicious": ["RISK-TB"],
                    "velocity": None,
                },
                "ip_address": None,
                "local_time": "0:37:47",
                "profile": {
                    "desination_queue": None,
                    "name": "Standard mid-market profile",
                    "selector_rule": "Default Active Profile",
                },
                "providers": None,
                "rules": [{"decision": "IGNORE", "name": "Fraud Score - Monitor"}],
                "score": {
                    "factor_codes": ["B", "T"],
                    "model_used": "default",
                    "result": "25",
                },
                "travel": None,
                "velocity": None,
            },
            "status": "AUTHORIZED",
            "submit_time_utc": "2024-01-18T08:37:47Z",
            "token_information": None,
        }

    def handle_processor_response(self, response, basket=None):
        print("xc13 handle_processor_response")
        currency = basket.currency
        transaction_id = response['processor_information']['transaction_id']
        # transaction_id = (
        #     response.transactionResponse.transId
        #     if hasattr(response.transactionResponse, "transId")
        #     else None
        # )
        transaction_dict = LxmlObjectJsonEncoder().encode(response)

        self.record_processor_response(
            transaction_dict, transaction_id=transaction_id, basket=basket
        )
        if response['status'] == 'AUTHORIZED':
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
        if response['error_information']:
            raise InvalidCybersourceDecision(response['error_information'])
        raise InvalidCybersourceDecision(response['status'])


    def issue_credit(self, order_number, basket, reference_number, amount, currency):
        raise NotImplementedError(
            "Cybersource payment processor does not support refunds."
        )
