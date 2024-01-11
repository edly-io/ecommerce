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
    ReversalApi
)
from CyberSource.rest import ApiException

url = 'https://apitest.cybersource.com/microform/v2/sessions'
requestObj = GeneratePublicKeyRequest(
    encryption_type='RsaOaep256',
    target_origin='https://www.example.com',
)
# requestObj = del_none(requestObj.__dict__)
# requestObj = json.dumps(requestObj)

api_instance = KeyGenerationApi(self.cybersource_api_config)
return_data, _, _ = api_instance.generate_public_key(
    generate_public_key_request=requestObj,
    format='JWT',
)

new_capture_context = {'key_id': return_data.key_id}

# capture_contexts = [
#     capture_context
#     for (capture_context, _)
#     in self._unexpired_capture_contexts(session)
# ]
# capture_contexts.insert(0, new_capture_context)
# # Prevent session size explosion by limiting the number of recorded capture contexts
# session['capture_contexts'] = capture_contexts[:20]
