""" View for interacting with the payment processor. """
from __future__ import unicode_literals
import logging

from django.http import HttpResponseRedirect, JsonResponse

from ecommerce.extensions.basket.utils import basket_add_organization_attribute
from ecommerce.extensions.checkout.mixins import EdxOrderPlacementMixin
from ecommerce.extensions.checkout.utils import get_receipt_page_url
from ecommerce.extensions.payment.processors.cybersource_microform import CybersourceMicroform
from ecommerce.extensions.payment.forms import CybersourceMicroformPaymentForm
from ecommerce.extensions.payment.views import BasePaymentSubmitView

logger = logging.getLogger(__name__)


class CybersourceMicroformSubmitView(EdxOrderPlacementMixin, BasePaymentSubmitView):


    form_class = CybersourceMicroformPaymentForm
    def __init__(self):
        print('CybersourceMicroform view xc12')
        super(CybersourceMicroformSubmitView, self).__init__()


    @property
    def payment_processor(self):
        print('CybersourceMicroform payment_processor xc12')
        return CybersourceMicroform(self.request.site)

    def post(self, request):  # pylint: disable=unused-argument
        print('hello-09')
        # form_kwargs = self.get_form_kwargs()

        form = self.form_class(**request.POST)
        print('uiop--34 ', form)

        if form.is_valid():
            return self.form_valid(form)
        

        # try:
        #     if form.is_valid():
        #         return self.form_valid(form)
        # except (TransactionDeclined) as exp:
        #     messages.add_message(request, messages.ERROR, 'Payment error: {}'.format(str(exp)))
        #     basket_url = reverse('basket:summary')
        #     return HttpResponseRedirect(basket_url)

        return self.form_invalid(form)
        return JsonResponse({}, status=200)


    def form_valid(self, form):
        print('holla--12')
        form_data = form.cleaned_data
        basket = form_data['basket']
        order_number = basket.order_number
        data_descriptor = form_data['data_descriptor']
        data_value = form_data['data_value']

        basket_add_organization_attribute(basket, self.request.POST)

        response = self.payment_processor.get_transaction_parameters(
            basket, data_descriptor=data_descriptor, data_value=data_value
        )
        try:
            self.handle_payment(response, basket)
        except Exception:  # pylint: disable=broad-except
            logger.exception('An error occurred while processing the Authorizent payment for basket [%d].', basket.id)
            return JsonResponse({}, status=400)

        try:
            order = self.create_order(self.request, basket)
        except Exception:  # pylint: disable=broad-except
            logger.exception('An error occurred while processing the Authorizenet payment for basket [%d].', basket.id)
            return JsonResponse({}, status=400)

        self.handle_post_order(order)

        receipt_url = get_receipt_page_url(
            site_configuration=self.request.site.siteconfiguration,
            order_number=order_number,
            disable_back_button=True,
        )

        return HttpResponseRedirect(receipt_url)
