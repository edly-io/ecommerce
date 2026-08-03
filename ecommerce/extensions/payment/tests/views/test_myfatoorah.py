# -*- coding: utf-8 -*-
""" Tests of the MyFatoorah payment views.

The tests that matter most here are the ones asserting an order is *not* placed:
they encode the trust boundary between us and the gateway.
"""


import json

import responses
from django.urls import reverse
from oscar.core.loading import get_model

from ecommerce.core.constants import SEAT_PRODUCT_CLASS_NAME
from ecommerce.extensions.checkout.utils import get_receipt_page_url
from ecommerce.extensions.payment.processors.myfatoorah import MyFatoorah
from ecommerce.extensions.payment.tests.mixins import MyFatoorahMixin, PaymentEventsMixin
from ecommerce.extensions.test.factories import create_basket
from ecommerce.tests.testcases import TestCase

JSON = 'application/json'

Order = get_model('order', 'Order')
PaymentProcessorResponse = get_model('payment', 'PaymentProcessorResponse')
ProductClass = get_model('catalogue', 'ProductClass')
SourceType = get_model('payment', 'SourceType')


class MyFatoorahViewTestMixin(MyFatoorahMixin, PaymentEventsMixin):
    """ Shared setup: a frozen basket with a MyFatoorah invoice already recorded against it. """

    def setUp(self):
        super(MyFatoorahViewTestMixin, self).setUp()
        self.price = '100.0'
        self.user = self.create_user()
        self.seat_product_class, __ = ProductClass.objects.get_or_create(name=SEAT_PRODUCT_CLASS_NAME)
        self.basket = create_basket(
            owner=self.user, site=self.site, price=self.price, product_class=self.seat_product_class
        )
        self.basket.freeze()

        self.processor = MyFatoorah(self.site)
        self.processor_name = self.processor.NAME

        # Stands in for the row get_transaction_parameters writes before the learner
        # leaves for MyFatoorah; it is how the views find this basket again.
        self.processor.record_processor_response(
            {'IsSuccess': True}, transaction_id=self.INVOICE_ID, basket=self.basket
        )

    def assert_no_order_placed(self):
        self.assertFalse(Order.objects.filter(number=self.basket.order_number).exists())

    def assert_myfatoorah_source_exists(self):
        """ Verify the order carries a MyFatoorah payment source labelled with the masked PAN. """
        self.assert_payment_source_exists(
            self.basket,
            SourceType.objects.get(name=self.processor_name),
            self.PAYMENT_ID,
            self.MASKED_CARD_NUMBER,
        )

    def get_status_request_body(self):
        """ Return the body of the GetPaymentStatus call.

        Order fulfillment makes its own outbound requests, so the status lookup is
        not reliably the last recorded call.
        """
        for call in responses.calls:
            if call.request.url.endswith('/v2/GetPaymentStatus'):
                return json.loads(call.request.body)
        return None


class MyFatoorahCallbackViewTests(MyFatoorahViewTestMixin, TestCase):
    """ Tests of the learner-facing return URL. """

    path = reverse('myfatoorah:callback')

    def _get(self, payment_id=None):
        params = {'paymentId': payment_id or self.PAYMENT_ID}
        return self.client.get(self.path, params)

    @responses.activate
    def test_successful_payment_places_order(self):
        """ Verify a settled payment produces an order, a payment source, and a receipt redirect. """
        self.mock_payment_status(basket=self.basket)

        response = self._get()

        self.assertRedirects(
            response,
            get_receipt_page_url(
                order_number=self.basket.order_number,
                site_configuration=self.basket.site.siteconfiguration,
                disable_back_button=True,
            ),
            fetch_redirect_response=False,
        )

        self.assertTrue(Order.objects.filter(number=self.basket.order_number).exists())
        self.assert_myfatoorah_source_exists()

    @responses.activate
    def test_payment_status_is_verified_server_side(self):
        """ Verify the view asks MyFatoorah rather than trusting the query string. """
        self.mock_payment_status(basket=self.basket)

        self._get()

        self.assertEqual(
            self.get_status_request_body(), {'Key': self.PAYMENT_ID, 'KeyType': 'PaymentId'}
        )

    def test_missing_payment_id(self):
        """ Verify a callback with no payment reference is refused without any gateway call. """
        response = self.client.get(self.path)

        self.assertRedirects(response, reverse('checkout:error'), fetch_redirect_response=False)
        self.assert_no_order_placed()

    @responses.activate
    def test_unpaid_invoice_places_no_order(self):
        """ Verify a pending invoice does not become an order.

        This is the case a learner can trigger by hand-crafting a return URL.
        """
        self.mock_payment_status(basket=self.basket, invoice_status='Pending')

        response = self._get()

        self.assertRedirects(response, reverse('checkout:error'), fetch_redirect_response=False)
        self.assert_no_order_placed()

    @responses.activate
    def test_failed_transaction_places_no_order(self):
        """ Verify a failed transaction on a paid-looking invoice places no order. """
        self.mock_payment_status(basket=self.basket, transaction_status='Failed')

        response = self._get()

        self.assertRedirects(response, reverse('checkout:error'), fetch_redirect_response=False)
        self.assert_no_order_placed()

    @responses.activate
    def test_underpayment_places_no_order(self):
        """ Verify a charge smaller than the basket total places no order. """
        self.mock_payment_status(basket=self.basket, invoice_value=1.0)

        response = self._get()

        self.assertRedirects(response, reverse('checkout:error'), fetch_redirect_response=False)
        self.assert_no_order_placed()

    @responses.activate
    def test_currency_mismatch_places_no_order(self):
        """ Verify a payment settled in another currency places no order.

        Without this check, 100 of a weaker currency would buy a 100 USD seat.
        """
        self.mock_payment_status(basket=self.basket, paid_currency='KWD')

        response = self._get()

        self.assertRedirects(response, reverse('checkout:error'), fetch_redirect_response=False)
        self.assert_no_order_placed()

    @responses.activate
    def test_customer_reference_mismatch_places_no_order(self):
        """ Verify a mismatch between the gateway's reference and the basket places no order. """
        self.mock_payment_status(basket=self.basket, customer_reference='EDX-SOMEONE-ELSE')

        response = self._get()

        self.assertRedirects(response, reverse('checkout:error'), fetch_redirect_response=False)
        self.assert_no_order_placed()

    @responses.activate
    def test_unknown_invoice_places_no_order(self):
        """ Verify a payment we have no record of places no order. """
        body = self.payment_status_response(basket=self.basket)
        body['Data']['InvoiceId'] = 9999999
        self.mock_payment_status(body=body)

        response = self._get()

        self.assertRedirects(response, reverse('checkout:error'), fetch_redirect_response=False)
        self.assert_no_order_placed()

    @responses.activate
    def test_gateway_failure_places_no_order(self):
        """ Verify a gateway outage places no order. """
        self.mock_payment_status(body={'IsSuccess': False, 'Message': 'Server error'}, status=500)

        response = self._get()

        self.assertRedirects(response, reverse('checkout:error'), fetch_redirect_response=False)
        self.assert_no_order_placed()

    @responses.activate
    def test_repeated_callback_places_one_order(self):
        """ Verify a learner refreshing the return URL does not buy the seat twice. """
        self.mock_payment_status(basket=self.basket)
        self.mock_payment_status(basket=self.basket)

        self._get()
        second_response = self._get()

        self.assertEqual(Order.objects.filter(number=self.basket.order_number).count(), 1)
        self.assertEqual(second_response.status_code, 302)


class MyFatoorahWebhookViewTests(MyFatoorahViewTestMixin, TestCase):
    """ Tests of the server-to-server notification endpoint. """

    path = reverse('myfatoorah:webhook')

    def _post(self, body=None, signature=None):
        body = body if body is not None else self.webhook_body()
        if signature is None:
            signature = self.signature_for(body)
        return self.client.post(
            self.path,
            json.dumps(body),
            content_type=JSON,
            HTTP_MYFATOORAH_SIGNATURE=signature,
        )

    @responses.activate
    def test_signed_webhook_places_order(self):
        """ Verify a correctly signed notification for a settled payment places an order. """
        self.mock_payment_status(basket=self.basket)

        response = self._post()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Order.objects.filter(number=self.basket.order_number).exists())
        self.assert_myfatoorah_source_exists()

    def test_unsigned_webhook_rejected(self):
        """ Verify a notification with no signature header is refused. """
        response = self._post(signature='')

        self.assertEqual(response.status_code, 400)
        self.assert_no_order_placed()

    def test_bad_signature_rejected(self):
        """ Verify a forged notification is refused before any gateway call is made. """
        response = self._post(signature='YmFkLXNpZ25hdHVyZQ==')

        self.assertEqual(response.status_code, 400)
        self.assert_no_order_placed()

    def test_tampered_body_rejected(self):
        """ Verify a body altered after signing is refused. """
        body = self.webhook_body()
        signature = self.signature_for(body)
        body['Data']['InvoiceId'] = 9999999

        response = self._post(body=body, signature=signature)

        self.assertEqual(response.status_code, 400)
        self.assert_no_order_placed()

    def test_unrelated_event_ignored(self):
        """ Verify a non-payment event is acknowledged but ignored. """
        body = self.webhook_body(event_code=2)

        response = self._post(body=body)

        self.assertEqual(response.status_code, 204)
        self.assert_no_order_placed()

    def test_webhook_without_payment_reference_rejected(self):
        """ Verify a payment event carrying no identifiers is refused. """
        body = self.webhook_body()
        del body['Data']['PaymentId']
        del body['Data']['InvoiceId']

        response = self._post(body=body)

        self.assertEqual(response.status_code, 400)
        self.assert_no_order_placed()

    @responses.activate
    def test_unpaid_webhook_places_no_order(self):
        """ Verify a signed notification about an unpaid invoice places no order.

        A valid signature proves the message came from MyFatoorah, not that the
        payment succeeded -- the status lookup is still what decides.
        """
        self.mock_payment_status(basket=self.basket, invoice_status='Pending')

        response = self._post()

        self.assertEqual(response.status_code, 200)
        self.assert_no_order_placed()

    @responses.activate
    def test_webhook_after_callback_places_one_order(self):
        """ Verify the callback and the webhook together produce exactly one order.

        Both fire for a normal purchase, so idempotency here is the difference
        between one enrolment and a duplicate order.
        """
        self.mock_payment_status(basket=self.basket)
        self.mock_payment_status(basket=self.basket)

        self.client.get(reverse('myfatoorah:callback'), {'paymentId': self.PAYMENT_ID})
        response = self._post()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.filter(number=self.basket.order_number).count(), 1)

    @responses.activate
    def test_gateway_failure_is_acknowledged(self):
        """ Verify a gateway outage still returns 200 so MyFatoorah stops retrying. """
        self.mock_payment_status(body={'IsSuccess': False, 'Message': 'Server error'}, status=500)

        response = self._post()

        self.assertEqual(response.status_code, 200)
        self.assert_no_order_placed()
