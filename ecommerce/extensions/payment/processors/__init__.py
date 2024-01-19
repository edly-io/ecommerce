
import abc
from collections import namedtuple

import six
import waffle
from django.conf import settings
from django.utils.functional import cached_property
from oscar.core.loading import get_model

PaymentProcessorResponse = get_model('payment', 'PaymentProcessorResponse')

HandledProcessorResponse = namedtuple('HandledProcessorResponse',
                                      ['transaction_id', 'total', 'currency', 'card_number', 'card_type'])


class BasePaymentProcessor(metaclass=abc.ABCMeta):  # pragma: no cover
    """Base payment processor class."""

    # NOTE: Ensure that, if passed to a Django template, Django does not attempt to instantiate this class
    # or its children. Doing so without a Site object will cause issues.
    # See https://docs.djangoproject.com/en/1.8/ref/templates/api/#variables-and-lookups
    do_not_call_in_templates = True

    NAME = None

    def __init__(self, site):
        super(BasePaymentProcessor, self).__init__()
        self.site = site

    @abc.abstractmethod
    def get_transaction_parameters(self, basket, request=None, use_client_side_checkout=False, **kwargs):
        """
        Generate a dictionary of signed parameters required for this processor to complete a transaction.

        Arguments:
            use_client_side_checkout:
            basket (Basket): The basket of products being purchased.
            request (Request, optional): A Request object which can be used to construct an absolute URL in
                cases where one is required.
            use_client_side_checkout (bool, optional): Determines if client-side checkout should be used.
            **kwargs: Additional parameters.

        Returns:
            dict: Payment processor-specific parameters required to complete a transaction. At a minimum,
                this dict must include a `payment_page_url` indicating the location of the processor's
                hosted payment page.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def handle_processor_response(self, response, basket=None):
        """
        Handle a response from the payment processor.

        This method creates PaymentEvents and Sources for successful payments.

        Arguments:
            response (dict): Dictionary of parameters received from the payment processor

        Keyword Arguments:
            basket (Basket): Basket whose contents have been purchased via the payment processor

        Returns:
            HandledProcessorResponse
        """
        raise NotImplementedError

    @property
    def configuration(self):
        """
        Returns the configuration (set in Django settings) specific to this payment processor.

        Returns:
            dict: Payment processor configuration

        Raises:
            KeyError: If no settings found for this payment processor
        """
        partner_short_code = self.site.siteconfiguration.partner.short_code
        return settings.PAYMENT_PROCESSOR_CONFIG[partner_short_code.lower()][self.NAME.lower()]
        return {
            "mode": "SET-ME-PLEASE(sandbox,live)",
            # "client_id": "SET-ME-PLEASE",
            # "client_secret": "SET-ME-PLEASE",
            "base_url": "https://js.authorize.net/v1/Accept.js",
            "receipt_path": "/checkout/receipt/",
            "cancel_checkout_path": "/checkout/cancel-checkout/",
            "error_path": "/checkout/error/",
            'soap_api_url': "https://ics2wstest.ic3.com/commerce/1.x/transactionProcessor/CyberSourceTransaction_1.140.wsdl",
            'merchant_id': 'edly_103',
            'transaction_key': '9sm0632L7OQP/FwbZmUFgLDNuIJ5ORBX+z7387VqsyYLE8nmYB8qus0C3iFWVpdxI77kZgyM+PdlP8zPPWu8M4igdkYGo8aGkk6RyVsafx3HGV1WtxBUibktbPex6ManuO3IfIV4s9yxtE3VM0SDkMH9iBXNJS8rPLojmChVMoHED2tY06Xo6k9zHilEmVDa6hrqdpWtnw2vYf4PsaAE8voYu8DaMQ51g799tmqyJyJPFpMcLmRla1+sBXiO28j4HxBu1Pc7fiWj1RSY6OiwHWQp72g8RGVBRQcpFGuxY56UZP3VCidAdg9Lc1Xb8H9b6YJLU+VBxrgXcGWoT6eK/A==',
            'profile_id': '92905CB0-6DC4-42D8-ADBC-A45889552CB0',
            'access_key': 'd132d3b579123aaa804cf9f5cd452b37',
            'secret_key': 'b51db43b67d445149670b996f948855078c9262ebbf442908c2f9334522205625fc952514cf34edab8f5599eef465f51b097b9774bc24f8bbf2c1b9dbb8f113985d722fd3d0f475380ae86568be347abed18900c1d354cc29a7f06559a52ea0f2657968be1364bef8e791708981b708b46cff1d2fdbd4a7bba8439d920a5a827',
            'payment_page_url': "https://testsecureacceptance.cybersource.com/pay",
            'sop_profile_id': '92905CB0-6DC4-42D8-ADBC-A45889552CB0',
            'sop_access_key': 'd132d3b579123aaa804cf9f5cd452b37',
            'sop_secret_key': 'b51db43b67d445149670b996f948855078c9262ebbf442908c2f9334522205625fc952514cf34edab8f5599eef465f51b097b9774bc24f8bbf2c1b9dbb8f113985d722fd3d0f475380ae86568be347abed18900c1d354cc29a7f06559a52ea0f2657968be1364bef8e791708981b708b46cff1d2fdbd4a7bba8439d920a5a827',
            'sop_payment_page_url': "https://testsecureacceptance.cybersource.com/pay",
            "production_mode": True,
            "cancel_checkout_path": "/checkout/cancel-cgitheckout/",
            "merchant_auth_name": "37db9fz65LTY",
            "redirect_url": "https://accept.authorize.net/payment/payment",
            "transaction_key": "2esq7stAT9XE537f",
            "base_url": "https://js.authorize.net/v1/Accept.js",
            "client_key": "4zKB8FhmM622TA84FFKk4WsH8dW84GdN69L8NSNjGtaPk2fwS6458eeHb2A54axc",
            "transaction_key": "2esq7stAT9XE537f",
            "api_login_id": "37db9fz65LTY",
            "apple_pay_merchant_id_domain_association": "green.payments.multisitesdev.edly.io/.well-known/apple-developer-merchantid-domain-association",
            "publishable_key": "pk_test_3HZgA8H5SE89uUdV4cJtjpCd00q3Su2WH9",
            "secret_key": "sk_test_QT5fpPHU6uY8MMOqemf9oGFQ005wrdMotX",
            "country": "us"
        }
        # return {
        #     "country": "PK",
        #     "secret_key": "sk_test_51IQH5rLC7JMtLiZAoC4SfivDUCaeBQlbQQ9x9WtaTVjV8XPmgmRE2afVMocBJ2obDr05VHrONBTWveky67ZkEyti00VFfrQ3NX",
        #     "publishable_key": "pk_test_51IQH5rLC7JMtLiZA2W6apCTKZX1BB1jQWzPgm8f7D6LCk33ojwKtjgNj8ypaXztHD4vAbrJj7Wv7MsX0JvRcji8m00VHHqtUyl"
        #     }
       
       # authorizenet
        return {
            "production_mode": True,
            "cancel_checkout_path": "/checkout/cancel-cgitheckout/",
            "merchant_auth_name": "37db9fz65LTY",
            "redirect_url": "https://accept.authorize.net/payment/payment",
            "transaction_key": "2esq7stAT9XE537f",
            "base_url": "https://js.authorize.net/v1/Accept.js",
            "client_key": "4zKB8FhmM622TA84FFKk4WsH8dW84GdN69L8NSNjGtaPk2fwS6458eeHb2A54axc",
            "transaction_key": "2esq7stAT9XE537f",
            "api_login_id": "37db9fz65LTY"
        }
    

    @property
    def client_side_payment_url(self):
        """
        Returns the URL to which payment data, collected directly from the payment page, should be posted.

        If the payment processor does not support client-side payments, ``None`` will be returned.

        Returns:
            str
        """
        return None

    def record_processor_response(self, response, transaction_id=None, basket=None):
        """
        Save the processor's response to the database for auditing.

        Arguments:
            response (dict): Response received from the payment processor

        Keyword Arguments:
            transaction_id (string): Identifier for the transaction on the payment processor's servers
            basket (Basket): Basket associated with the payment event (e.g., being purchased)

        Return
            PaymentProcessorResponse
        """
        return PaymentProcessorResponse.objects.create(processor_name=self.NAME, transaction_id=transaction_id,
                                                       response=response, basket=basket)

    @abc.abstractmethod
    def issue_credit(self, order_number, basket, reference_number, amount, currency):
        """
        Issue a credit/refund for the specified transaction.

        Arguments:
            order_number (str): Order number of the order being refunded.
            basket (Basket): Basket associated with the order being refunded.
            reference_number (str): Reference number of the transaction being refunded.
            amount (Decimal): amount to be credited/refunded
            currency (string): currency of the amount to be credited

        Returns:
            str: Reference number of the *refund* transaction. Unless the payment processor groups related transactions,
             this will *NOT* be the same as the `reference_number` argument.
        """
        raise NotImplementedError

    @classmethod
    def is_enabled(cls):
        """
        Returns True if this payment processor is enabled, and False otherwise.
        """
        return waffle.switch_is_active(settings.PAYMENT_PROCESSOR_SWITCH_PREFIX + cls.NAME)


class BaseClientSidePaymentProcessor(BasePaymentProcessor, metaclass=abc.ABCMeta):  # pylint: disable=abstract-method
    """ Base class for client-side payment processors. """
    #abstract base class

    def get_template_name(self):
        """ Returns the path of the template to be loaded for this payment processor.

        Returns:
            str
        """
        print('callling template xc15 ', 'payment/{}.html'.format(self.NAME))
        return 'payment/{}.html'.format(self.NAME)


class ApplePayMixin:
    @cached_property
    def apple_pay_merchant_id_domain_association(self):
        """ Returns the Apple Pay merchant domain association contents that will be served at
        /.well-known/apple-developer-merchantid-domain-association.

        Returns:
            str
        """
        return (self.configuration.get('apple_pay_merchant_id_domain_association') or '').strip()
