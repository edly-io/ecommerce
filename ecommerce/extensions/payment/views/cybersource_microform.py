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
from enum import Enum

logger = logging.getLogger(__name__)

# 

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
        form_kwargs = self.get_form_kwargs()
       
        print('pop2 ', form_kwargs)
        form = self.form_class(**form_kwargs)
        # print('uiop--34 ', form)


        # self.form_valid(form)

        
        if form.is_valid():
            print('898989')
            return self.form_valid(form)
        
        print('09099 ', form.errors.items(), form.errors)
        for field, errors in form.errors.items():
            print(f"Field: {field}, Errors: {', '.join(errors)}")
        return self.form_invalid(form)
        # print('hola-a ', self.payment_processor.payment_with_transient_token())
        

        # try:
        #     if form.is_valid():
        #         return self.form_valid(form)
        # except (TransactionDeclined) as exp:
        #     messages.add_message(request, messages.ERROR, 'Payment error: {}'.format(str(exp)))
        #     basket_url = reverse('basket:summary')
        #     return HttpResponseRedirect(basket_url)

        # return self.form_invalid(form)
        return JsonResponse({}, status=200)


    def form_valid(self, form):
        print('holla--12')
        form_data = form.cleaned_data
        # print('091- ', form)
        print('091- ', form_data)
        print('092- ', self.request.user.email)
        basket = form_data['basket']
        order_number = basket.order_number
        # data_descriptor = form_data['data_descriptor']
        # data_value = form_data['data_value']

        # will enable this later
        basket_add_organization_attribute(basket, self.request.POST)

        response = self.payment_processor.get_transaction_parameters(
            basket=basket, request=self.request, form_data=form_data
        )

        # return JsonResponse({}, status=200)

        try:
            self.handle_payment(response, basket)
        except Exception as e:  # pylint: disable=broad-except
            print('this- ',e)
            logger.exception('An error occurred while processing the Authorizent payment for basket [%d].', basket.id)
            return JsonResponse({'error': str(e)}, status=400)

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
