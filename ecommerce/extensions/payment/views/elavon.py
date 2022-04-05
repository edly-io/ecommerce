"""
Views for interacting with the elavon payment processor.
"""
from __future__ import absolute_import, unicode_literals
from datetime import date
import logging
import json
from urllib.parse import urlencode

from oscar.apps.checkout.views import *  # pylint: disable=wildcard-import, unused-wildcard-import
from oscar.apps.payment.exceptions import PaymentError, GatewayError
from oscar.core.loading import get_class, get_model

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404, JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.urls import reverse

from ecommerce.core.models import User
from ecommerce.extensions.basket.utils import basket_add_organization_attribute
from ecommerce.extensions.checkout.mixins import EdxOrderPlacementMixin
from ecommerce.extensions.checkout.utils import get_receipt_page_url
from ecommerce.extensions.payment.forms import ElavonPaymentForm
from ecommerce.extensions.payment.models import ElavonPaymentRecord
from ecommerce.extensions.payment.processors.elavon import Elavon
from ecommerce.extensions.payment.views import BasePaymentSubmitView

logger = logging.getLogger(__name__)

Applicator = get_class('offer.applicator', 'Applicator')
Basket = get_model('basket', 'Basket')


class ElavonSubmitView(BasePaymentSubmitView):
    """
    Starts Elavon payment process.

    The view expects POST data containing a `Basket` ID. The specified basket is frozen, and the user is redirected
    to the elavon receipt page after successful elavon transaction.
    """
    form_class = ElavonPaymentForm

    @property
    def payment_processor(self):
        return Elavon(self.request.site)

    def get_receipt_url(self, basket, gateway_reference_id):
        """
        Construct Elavon receipt URL.
        """
        params = {
            'order_number': basket.order_number,
            'disable_back_button': 'true',
            'elavon_payment_id': gateway_reference_id
        }
        receipt_url = '{}?{}'.format(reverse('elavon:receipt'), urlencode(params))
        return receipt_url

    def form_valid(self, form):
        """
        Redirects to Elavon receipt if Elavon transaction successful else redirects to the checkout error page.
        """
        data = form.cleaned_data
        basket = data['basket']
        request = self.request

        try:
            response = self.payment_processor.get_transaction_parameters(basket, request, form_data=data)
            ElavonPaymentRecord.objects.create(
                basket=basket,
                merchant_reference_id=response['merchant_reference_id'],
                payment_gateway_reference_id=response['payment_gateway_reference_id'],
                site=request.site,
                user=request.user
            )
            redirect_url = self.get_receipt_url(basket, response['payment_gateway_reference_id'])
        except GatewayError as error:
            logger.exception(error)
            redirect_url = reverse('checkout:error')

        basket_add_organization_attribute(basket, request.POST)
        basket.freeze()

        return HttpResponseRedirect(redirect_url, status=303)


class ElavonReceiptView(ThankYouView):
    """
    Renders the Cowpay Fawry receipt page.
    """
    template_name = 'edx/checkout/cowpay_receipt.html'

    @method_decorator(csrf_exempt)
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):  # pylint: disable=arguments-differ
        return super(ElavonReceiptView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        try:
            response = super(ElavonReceiptView, self).get(request, *args, **kwargs)
        except Http404:
            self.template_name = 'edx/checkout/receipt_not_found.html'
            context = {
                'order_history_url': request.site.siteconfiguration.build_lms_url('account/settings'),
            }
            return self.render_to_response(context=context, status=404)

        return response

    def get_context_data(self, **kwargs):  # pylint: disable=arguments-differ
        """
        Get context data for Elavon receipt page.
        """
        context = super(ElavonReceiptView, self).get_context_data(**kwargs)
        request = self.request
        request_data = request.GET
        basket = self.object.basket

        basket.strategy = request.strategy
        Applicator().apply(basket, request.user, request)

        context.update({
            'order_date': date.today(),
            'order_number': basket.order_number,
            'fawry_payment_id': request_data.get('elavon_payment_id'),
            'currency': basket.currency,
            'amount': basket.total_incl_tax,
            'subtotal': basket.total_incl_tax_excl_discounts,
            'lines': basket.lines,
            'user': request.user,
            'disable_back_button': request_data.get('disable_back_button', 0),
            'payment_method': 'Elavon'
        })
        return context

    def get_object(self):
        """
        Get Elavon payment record.
        """
        kwargs = {
            'payment_gateway_reference_id': self.request.GET['elavon_payment_id'],
            'site': self.request.site,
            'user': self.request.user
        }

        return get_object_or_404(ElavonPaymentRecord, **kwargs)


class ElavonExecutionView(EdxOrderPlacementMixin, View):
    """
    Execute an approved Cowpay payment and place an order for paid products as appropriate.
    """
    @property
    def payment_processor(self):
        return Elavon(self.request.site)

    @method_decorator(transaction.non_atomic_requests)
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super(ElavonExecutionView, self).dispatch(request, *args, **kwargs)

    def post(self, request):
        """
        This view will be called by Cowpay to handle order placement and fulfillment.
        """
        data = request.POST.dict()
        if not data:
            data = json.loads(request.body.decode('utf8').replace("'", '"'))

        if not data['payment_gateway_reference_id']:
            logger.warning('No execution step can be carried out until payment is successful')
            return JsonResponse({'message': 'Payment has not been completed yet.'}, status=200)

        user = request.user if request.user.is_authenticated else User.objects.get(id=data['customer_merchant_profile_id'])
        data['user'] = user.id
        logger.info('Data received: %s', data)
        try:
            payment_record = ElavonPaymentRecord.objects.get(payment_gateway_reference_id=data['payment_gateway_reference_id'])
            basket = payment_record.basket
        except ElavonPaymentRecord.DoesNotExist:
            basket = user.baskets.filter(site=request.site, lines__isnull=False).last()

        basket.strategy = request.strategy
        Applicator().apply(basket, request.user, request)
        logger.info('Basket to be used:%s with amount:%s and number of lines:%d', basket.id, basket.total_incl_tax, basket.num_lines)

        try:
            self.handle_payment(data, basket)
            logger.info('Successfully handled elavon payment for basket [%d]', basket.id)
        except (PaymentError, Exception) as ex:
            logger.exception('An error occurred while processing the Elavon payment for basket [%d]. The exception was %s', basket.id, ex)
            return JsonResponse({}, status=400)

        try:
            order = self.create_order(request, basket)
            logger.info('Successfully handled elavon order placement for basket [%d]', basket.id)
        except Exception as ex:                     # pylint: disable=broad-except
            logger.exception('An error occurred while processing the Elavon order creation for basket [%d]. The exception was %s', basket.id, ex)
            return JsonResponse({}, status=400)

        self.handle_post_order(order)

        receipt_url = get_receipt_page_url(
            site_configuration=self.request.site.siteconfiguration,
            order_number=basket.order_number,
            disable_back_button=True,
        )
        return JsonResponse({'url': receipt_url}, status=201)
