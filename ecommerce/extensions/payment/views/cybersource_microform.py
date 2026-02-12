""" View for interacting with the payment processor. """
from __future__ import unicode_literals

import logging
from enum import Enum

from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from oscar.apps.payment.exceptions import TransactionDeclined

from ecommerce.extensions.basket.utils import basket_add_organization_attribute
from ecommerce.extensions.checkout.mixins import EdxOrderPlacementMixin
from ecommerce.extensions.checkout.utils import get_receipt_page_url
from ecommerce.extensions.payment.forms import CybersourceMicroformPaymentForm
from ecommerce.extensions.payment.processors.cybersource_microform import CybersourceMicroform
from ecommerce.extensions.payment.views import BasePaymentSubmitView

logger = logging.getLogger(__name__)


class CybersourceMicroformSubmitView(EdxOrderPlacementMixin, BasePaymentSubmitView):
    form_class = CybersourceMicroformPaymentForm

    def __init__(self):
        super(CybersourceMicroformSubmitView, self).__init__()

    @property
    def payment_processor(self):
        return CybersourceMicroform(self.request.site)

    def post(self, request):  # pylint: disable=unused-argument
        form_kwargs = self.get_form_kwargs()
        form = self.form_class(**form_kwargs)

        try:
            if form.is_valid():
                return self.form_valid(form)
        except TransactionDeclined as exp:
            messages.add_message(
                request, messages.ERROR, "Payment error: {}".format(str(exp))
            )
            basket_url = reverse("basket:summary")
            return HttpResponseRedirect(basket_url)

        return self.form_invalid(form)

    def form_valid(self, form):
        form_data = form.cleaned_data
        basket = form_data["basket"]
        order_number = basket.order_number

        basket_add_organization_attribute(basket, self.request.POST)

        response = self.payment_processor.get_transaction_parameters(
            basket=basket, request=self.request, form_data=form_data
        )

        try:
            self.handle_payment(response, basket)
        except Exception as e:
            logger.exception(
                "An error occurred while processing the Cybersource Microform payment for basket [%d].",
                basket.id,
            )
            return JsonResponse({"error": str(e)}, status=400)

        try:
            order = self.create_order(self.request, basket)
        except Exception:  # pylint: disable=broad-except
            logger.exception(
                "An error occurred while processing the Cybersource Microform payment for basket [%d].",
                basket.id,
            )
            return JsonResponse({}, status=400)

        self.handle_post_order(order)

        receipt_url = get_receipt_page_url(
            site_configuration=self.request.site.siteconfiguration,
            order_number=order_number,
            disable_back_button=True,
        )

        return HttpResponseRedirect(receipt_url)
