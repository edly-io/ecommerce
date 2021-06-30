from ecommerce.extensions.payment.processors import BaseClientSidePaymentProcessor


class Lumsxpay(BaseClientSidePaymentProcessor):
    NAME = 'lumsxpay'
    template_name = 'payment/lumsxpay.html'

    def __init__(self, site):
        """
        Constructs a new instance of the LumsxPay processor.

        Raises:
            KeyError: If no settings configured for this payment processor.
        """
        super(Lumsxpay, self).__init__(site)
        configuration = self.configuration
        self.url_for_online_payment = 'https://dev-payments-lumsx.lums.edu.pk'
        self.url_for_download_voucher = 'https://dev-payments-lumsx.lums.edu.pk'
        self.support_email = 'support@lums.edu.pk'
        self.lms_dashboard_url = self.site.siteconfiguration.lms_url_root
        self.CRON_DELAY_TIME = 10

    def get_transaction_parameters(self, basket, request=None, use_client_side_checkout=True, **kwargs):
        raise NotImplementedError('The LumsxPay payment processor does not support transaction parameters.')

    def handle_processor_response(self, response, basket=None):
        pass

    def issue_credit(self, order_number, basket, reference_number, amount, currency):
        raise NotImplementedError('The Lumsxpay payment processor does not support refunds.')
