""" Views for interacting with the MyFatoorah payment processor.

There are two ways MyFatoorah tells us a payment happened, and both land here:

* ``MyFatoorahCallbackView`` -- the learner's browser is redirected back to us
  after they finish on MyFatoorah's hosted page.
* ``MyFatoorahWebhookView`` -- MyFatoorah's servers POST us a signed notification.

The webhook is not redundant. If the learner pays and then closes the tab before
the redirect completes, the callback never fires and the payment would otherwise
never become an enrolment.

Neither entry point is trusted about payment state. Both treat their input as an
opaque lookup key, re-ask MyFatoorah server-to-server via ``get_payment_status``,
and only then place an order -- see ``MyFatoorahPaymentMixin.place_order_for_payment``,
which both share so their trust checks cannot drift apart.
"""


import logging

from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from oscar.apps.partner import strategy
from oscar.apps.payment.exceptions import PaymentError
from oscar.core.loading import get_class, get_model
from rest_framework.views import APIView

from ecommerce.extensions.basket.utils import basket_add_organization_attribute
from ecommerce.extensions.checkout.mixins import EdxOrderPlacementMixin
from ecommerce.extensions.checkout.utils import get_receipt_page_url
from ecommerce.extensions.payment.exceptions import AuthorizationError, InvalidBasketError, PartialAuthorizationError
from ecommerce.extensions.payment.processors.myfatoorah import EVENT_PAYMENT_STATUS_CHANGED, MyFatoorah

logger = logging.getLogger(__name__)

Applicator = get_class('offer.applicator', 'Applicator')
Order = get_model('order', 'Order')
PaymentProcessorResponse = get_model('payment', 'PaymentProcessorResponse')

SIGNATURE_HEADER = 'HTTP_MYFATOORAH_SIGNATURE'


class MyFatoorahPaymentMixin(EdxOrderPlacementMixin):
    """ Shared verify-then-place-order logic for the callback and the webhook. """

    @property
    def payment_processor(self):
        return MyFatoorah(self.request.site)

    def get_basket(self, invoice_id):
        """
        Retrieve the basket an invoice was created for.

        The link is the ``PaymentProcessorResponse`` row written by
        ``get_transaction_parameters`` before the learner left for MyFatoorah.

        Arguments:
            invoice_id: ``InvoiceId`` reported by MyFatoorah.

        Returns:
            Basket or None.
        """
        if not invoice_id:
            return None

        try:
            basket = PaymentProcessorResponse.objects.get(
                processor_name=self.payment_processor.NAME,
                transaction_id=invoice_id,
            ).basket
        except MultipleObjectsReturned:
            logger.warning('Duplicate MyFatoorah invoice ID [%s] received.', invoice_id)
            return None
        except (ObjectDoesNotExist, ValueError):
            logger.warning('No basket found for MyFatoorah invoice ID [%s].', invoice_id)
            return None

        if basket is None:
            return None

        basket.strategy = strategy.Default()
        Applicator().apply(basket, basket.owner, self.request)
        return basket

    def place_order_for_payment(self, request, key, key_type='PaymentId'):
        """
        Verify a payment with MyFatoorah and place the order if it is genuinely paid.

        Arguments:
            request: The incoming request.
            key: The ``paymentId``/``InvoiceId`` supplied by MyFatoorah. Untrusted.

        Keyword Arguments:
            key_type (str): Which identifier ``key`` is.

        Returns:
            tuple: ``(basket, order)``. ``order`` is the pre-existing order when this
                payment was already processed, so callers get idempotency for free.

        Raises:
            InvalidBasketError: No basket could be tied to the payment.
            AuthorizationError: MyFatoorah does not consider the invoice paid.
            PartialAuthorizationError: The charged amount or currency disagrees with the basket.
            PaymentError: Recording the payment failed.
        """
        processor = self.payment_processor
        status_response = processor.get_payment_status(key, key_type=key_type)
        data = status_response.get('Data') or {}
        invoice_id = data.get('InvoiceId')

        basket = self.get_basket(invoice_id)
        if not basket:
            raise InvalidBasketError(
                'No basket found for MyFatoorah invoice {}.'.format(invoice_id)
            )

        # MyFatoorah echoes back the order number we sent as CustomerReference.
        # If it disagrees with the basket we resolved, something is wrong enough
        # that we should not create an order.
        customer_reference = data.get('CustomerReference')
        if customer_reference and customer_reference != basket.order_number:
            raise InvalidBasketError(
                'MyFatoorah invoice {invoice} reports CustomerReference [{reference}] but its basket '
                '[{basket_id}] has order number [{order_number}].'.format(
                    invoice=invoice_id,
                    reference=customer_reference,
                    basket_id=basket.id,
                    order_number=basket.order_number,
                )
            )

        if not processor.is_paid(status_response):
            processor.record_status_response(status_response, basket=basket)
            raise AuthorizationError(
                'MyFatoorah invoice {invoice} is not paid (status [{status}]).'.format(
                    invoice=invoice_id, status=data.get('InvoiceStatus')
                )
            )

        # Compare against what the gateway says it charged, not what we asked for.
        invoice_value = processor.get_invoice_value(status_response)
        if invoice_value is None or invoice_value != basket.total_incl_tax:
            raise PartialAuthorizationError(
                'MyFatoorah invoice {invoice} charged [{charged}] but basket [{basket_id}] '
                'totals [{expected}].'.format(
                    invoice=invoice_id,
                    charged=invoice_value,
                    basket_id=basket.id,
                    expected=basket.total_incl_tax,
                )
            )

        paid_currency = (processor.get_successful_transaction(status_response) or {}).get('PaidCurrency')
        if paid_currency and paid_currency != basket.currency:
            raise PartialAuthorizationError(
                'MyFatoorah invoice {invoice} was paid in [{paid}] but basket [{basket_id}] '
                'is priced in [{expected}].'.format(
                    invoice=invoice_id,
                    paid=paid_currency,
                    basket_id=basket.id,
                    expected=basket.currency,
                )
            )

        # The callback and the webhook can both fire for the same payment, in either
        # order. Whoever loses the race must not place a second order.
        existing_order = Order.objects.filter(number=basket.order_number).first()
        if existing_order:
            logger.info(
                'Order [%s] already exists for MyFatoorah invoice [%s]; skipping order placement.',
                basket.order_number,
                invoice_id,
            )
            return basket, existing_order

        with transaction.atomic():
            self.handle_payment(status_response, basket)

        order = self.create_order(request, basket)

        try:
            self.handle_post_order(order)
        except Exception:  # pylint: disable=broad-except
            self.log_order_placement_exception(basket.order_number, basket.id)

        return basket, order


class MyFatoorahCallbackView(MyFatoorahPaymentMixin, View):
    """ Handle a learner returning from MyFatoorah's hosted payment page. """

    # Disable atomicity for the view. Otherwise, we'd be unable to commit to the database
    # until the request had concluded; Django will refuse to commit when an atomic() block
    # is active, since that would break atomicity. Without an order present in the database
    # at the time fulfillment is attempted, asynchronous order fulfillment tasks will fail.
    @method_decorator(transaction.non_atomic_requests)
    def dispatch(self, request, *args, **kwargs):
        return super(MyFatoorahCallbackView, self).dispatch(request, *args, **kwargs)

    def get_basket(self, invoice_id):
        """ Attach any organization attribute carried on the return URL before the order is placed. """
        basket = super(MyFatoorahCallbackView, self).get_basket(invoice_id)
        if basket:
            basket_add_organization_attribute(basket, self.request.GET)
        return basket

    def get(self, request):
        """
        Verify the payment behind a returning learner and show them their receipt.

        Note this is a GET return URL rather than a webhook, so it is not CSRF
        exempt and it carries no authority of its own -- ``paymentId`` is only a
        lookup key.
        """
        payment_id = request.GET.get('paymentId') or request.GET.get('Id')

        if not payment_id:
            logger.warning('MyFatoorah callback received without a paymentId.')
            return redirect(reverse('checkout:error'))

        try:
            basket, __ = self.place_order_for_payment(request, payment_id)
        except (AuthorizationError, PartialAuthorizationError) as exc:
            logger.warning('Declining MyFatoorah payment [%s]: %s', payment_id, exc)
            return redirect(reverse('checkout:error'))
        except InvalidBasketError as exc:
            logger.error('Cannot process MyFatoorah payment [%s]: %s', payment_id, exc)
            return redirect(reverse('checkout:error'))
        except PaymentError:
            logger.exception('Failed to record MyFatoorah payment [%s].', payment_id)
            return redirect(reverse('checkout:error'))
        except Exception:  # pylint: disable=broad-except
            # The payment may well have gone through even though we failed to place the
            # order. The learner sees an error, but the webhook is the backstop that
            # will place the order if MyFatoorah confirms the payment.
            logger.exception('Unexpected error handling MyFatoorah payment [%s].', payment_id)
            return redirect(reverse('checkout:error'))

        return redirect(
            get_receipt_page_url(
                order_number=basket.order_number,
                site_configuration=basket.site.siteconfiguration,
                disable_back_button=True,
            )
        )


class MyFatoorahWebhookView(MyFatoorahPaymentMixin, APIView):
    """
    Handle MyFatoorah's server-to-server payment notification.

    Returns 200 for anything it has finished with -- including payments it decided
    not to act on -- so MyFatoorah stops retrying. Only an unverifiable signature
    or a malformed body gets a 4xx.
    """

    authentication_classes = ()
    permission_classes = ()

    @method_decorator(transaction.non_atomic_requests)
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super(MyFatoorahWebhookView, self).dispatch(request, *args, **kwargs)

    def post(self, request):
        body = request.data
        if not isinstance(body, dict):
            logger.warning('Rejecting MyFatoorah webhook: body is not an object.')
            return HttpResponse(status=400)

        if not self.payment_processor.verify_webhook_signature(body, request.META.get(SIGNATURE_HEADER)):
            # verify_webhook_signature has already logged the specific reason.
            return HttpResponse(status=400)

        event_code = (body.get('Event') or {}).get('Code')
        if event_code != EVENT_PAYMENT_STATUS_CHANGED:
            logger.info('Ignoring MyFatoorah webhook event code [%s].', event_code)
            return HttpResponse(status=204)

        data = body.get('Data') or {}
        # Prefer PaymentId, which MyFatoorah recommends for status lookups, but
        # fall back to the invoice if this event only carries that.
        key = data.get('PaymentId')
        key_type = 'PaymentId'
        if not key:
            key = data.get('InvoiceId')
            key_type = 'InvoiceId'

        if not key:
            logger.warning('Rejecting MyFatoorah webhook: no PaymentId or InvoiceId in Data.')
            return HttpResponse(status=400)

        try:
            self.place_order_for_payment(request, key, key_type=key_type)
        except (AuthorizationError, PartialAuthorizationError) as exc:
            logger.warning('Declining MyFatoorah webhook payment [%s]: %s', key, exc)
        except InvalidBasketError as exc:
            logger.error('Cannot process MyFatoorah webhook payment [%s]: %s', key, exc)
        except Exception:  # pylint: disable=broad-except
            logger.exception('Unexpected error handling MyFatoorah webhook payment [%s].', key)

        return HttpResponse(status=200)
