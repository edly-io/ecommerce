
from django.conf.urls import include, url

from ecommerce.extensions.payment.views import PaymentFailedView, SDNFailure, authorizenet, cybersource, cybersource_microform, paypal, stripe, cowpay

CYBERSOURCE_APPLE_PAY_URLS = [
    url(r'^authorize/$', cybersource.CybersourceApplePayAuthorizationView.as_view(), name='authorize'),
    url(r'^start-session/$', cybersource.ApplePayStartSessionView.as_view(), name='start_session'),
]
CYBERSOURCE_URLS = [
    url(r'^apple-pay/', include((CYBERSOURCE_APPLE_PAY_URLS, 'apple_pay'))),
    url(r'^redirect/$', cybersource.CybersourceInterstitialView.as_view(), name='redirect'),
    url(r'^submit/$', cybersource.CybersourceSubmitView.as_view(), name='submit'),
    url(r'^api-submit/$', cybersource.CybersourceSubmitAPIView.as_view(), name='api_submit'),
    url(r'^authorize/$', cybersource.CybersourceAuthorizeAPIView.as_view(), name='authorize'),
    url(r'^microform/submit/$', cybersource_microform.CybersourceMicroformSubmitView.as_view(), name='microform_submit'),
]

PAYPAL_URLS = [
    url(r'^execute/$', paypal.PaypalPaymentExecutionView.as_view(), name='execute'),
    url(r'^profiles/$', paypal.PaypalProfileAdminView.as_view(), name='profiles'),
]

SDN_URLS = [
    url(r'^failure/$', SDNFailure.as_view(), name='failure'),
]

STRIPE_URLS = [
    url(r'^submit/$', stripe.StripeSubmitView.as_view(), name='submit'),
]

AUTHORIZENET_URLS = [
    url(r'^notification/$', authorizenet.AuthorizeNetNotificationView.as_view(), name='authorizenet_notifications'),
    url(r'^redirect/$', authorizenet.handle_redirection, name='redirect'),
    url(r'^submit/$', authorizenet.AuthorizenetClientView.as_view(), name='submit'),
]

COWPAY_URLS = [
    url(r'^submit/$', cowpay.CowpayFawrySubmitView.as_view(), name='submit'),
    url(r'^receipt/$', cowpay.CowpayFawryReceiptView.as_view(), name='receipt'),
    url(r'^execute/$', cowpay.CowpayExecutionView.as_view(), name='execute'),
]

urlpatterns = [
    url(r'^cybersource/', include((CYBERSOURCE_URLS, 'cybersource'))),
    url(r'^error/$', PaymentFailedView.as_view(), name='payment_error'),
    url(r'^paypal/', include((PAYPAL_URLS, 'paypal'))),
    url(r'^sdn/', include((SDN_URLS, 'sdn'))),
    url(r'^stripe/', include((STRIPE_URLS, 'stripe'))),
    url(r'^authorizenet/', include((AUTHORIZENET_URLS, 'authorizenet'))),
    url(r'^cowpay/', include((COWPAY_URLS, 'cowpay'))),
]
