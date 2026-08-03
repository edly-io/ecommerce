# -*- coding: utf-8 -*-
""" Tests of the MyFatoorah payment processor. """


import json
from decimal import Decimal

import responses
from oscar.apps.payment.exceptions import GatewayError

from ecommerce.extensions.payment.exceptions import MissingTransactionDetailError
from ecommerce.extensions.payment.processors.myfatoorah import MyFatoorah, _scrub
from ecommerce.extensions.payment.tests.mixins import MyFatoorahMixin
from ecommerce.extensions.payment.tests.processors.mixins import PaymentProcessorTestCaseMixin
from ecommerce.tests.testcases import TestCase


class MyFatoorahTests(MyFatoorahMixin, PaymentProcessorTestCaseMixin, TestCase):
    """ Tests of the MyFatoorah processor. """

    processor_class = MyFatoorah
    processor_name = 'myfatoorah'

    @responses.activate
    def test_get_transaction_parameters(self):
        """ Verify the processor creates an invoice and returns its hosted payment page. """
        self.mock_send_payment()

        response = self.processor.get_transaction_parameters(self.basket)

        self.assertEqual(response, {'payment_page_url': self.INVOICE_URL})

        request_body = json.loads(responses.calls[-1].request.body)
        self.assertEqual(request_body['InvoiceValue'], float(self.basket.total_incl_tax))
        self.assertEqual(request_body['DisplayCurrencyIso'], self.basket.currency)
        self.assertEqual(request_body['CustomerReference'], self.basket.order_number)
        self.assertEqual(request_body['NotificationOption'], 'LNK')
        self.assertIn('/payment/myfatoorah/callback/', request_body['CallBackUrl'])

        # The audit row is what lets the callback find this basket again.
        self.assert_processor_response_recorded(
            self.processor.NAME,
            self.INVOICE_ID,
            _scrub(self.send_payment_response()),
            basket=self.basket,
        )

    @responses.activate
    def test_get_transaction_parameters_sends_bearer_token(self):
        """ Verify the API token is sent as a bearer token. """
        self.mock_send_payment()

        self.processor.get_transaction_parameters(self.basket)

        self.assertEqual(
            responses.calls[-1].request.headers['Authorization'],
            'Bearer fake-myfatoorah-api-token',
        )

    @responses.activate
    def test_get_transaction_parameters_gateway_error(self):
        """ Verify a rejected invoice raises GatewayError and is recorded. """
        self.mock_send_payment(is_success=False)

        with self.assertRaises(GatewayError):
            self.processor.get_transaction_parameters(self.basket)

    @responses.activate
    def test_get_transaction_parameters_without_payment_url(self):
        """ Verify a success response missing InvoiceURL is still treated as a failure. """
        body = self.send_payment_response()
        del body['Data']['InvoiceURL']
        self.mock_send_payment(body=body)

        with self.assertRaises(GatewayError):
            self.processor.get_transaction_parameters(self.basket)

    @responses.activate
    def test_get_transaction_parameters_unparseable_response(self):
        """ Verify a non-JSON response raises GatewayError rather than propagating ValueError. """
        responses.add(
            responses.POST,
            self.myfatoorah_url('/v2/SendPayment'),
            body='<html>gateway down</html>',
            status=502,
        )

        with self.assertRaises(GatewayError):
            self.processor.get_transaction_parameters(self.basket)

    @responses.activate
    def test_get_payment_status(self):
        """ Verify payment status is looked up by PaymentId, as MyFatoorah recommends. """
        self.mock_payment_status(basket=self.basket)

        response = self.processor.get_payment_status(self.PAYMENT_ID)

        self.assertTrue(self.processor.is_paid(response))
        request_body = json.loads(responses.calls[-1].request.body)
        self.assertEqual(request_body, {'Key': self.PAYMENT_ID, 'KeyType': 'PaymentId'})

    @responses.activate
    def test_get_payment_status_by_invoice_id(self):
        """ Verify the lookup can fall back to an invoice ID. """
        self.mock_payment_status(basket=self.basket)

        self.processor.get_payment_status(self.INVOICE_ID, key_type='InvoiceId')

        request_body = json.loads(responses.calls[-1].request.body)
        self.assertEqual(request_body, {'Key': str(self.INVOICE_ID), 'KeyType': 'InvoiceId'})

    @responses.activate
    def test_get_payment_status_without_invoice(self):
        """ Verify a response carrying no invoice detail raises. """
        body = self.payment_status_response(basket=self.basket)
        body['Data'] = None
        self.mock_payment_status(body=body)

        with self.assertRaises(MissingTransactionDetailError):
            self.processor.get_payment_status(self.PAYMENT_ID)

    def test_is_paid_requires_both_invoice_and_transaction(self):
        """ Verify a paid invoice with no settled transaction is not treated as paid.

        Guards against a pending or failed attempt on an otherwise paid-looking
        invoice being accepted.
        """
        self.assertTrue(self.processor.is_paid(self.payment_status_response(basket=self.basket)))
        self.assertFalse(
            self.processor.is_paid(self.payment_status_response(basket=self.basket, invoice_status='Pending'))
        )
        self.assertFalse(
            self.processor.is_paid(
                self.payment_status_response(basket=self.basket, transaction_status='Failed')
            )
        )

    def test_get_invoice_value(self):
        """ Verify the charged amount is read from the gateway response as a Decimal. """
        response = self.payment_status_response(basket=self.basket, invoice_value=20.0)
        self.assertEqual(self.processor.get_invoice_value(response), Decimal('20.0'))

        response['Data']['InvoiceValue'] = 'not-a-number'
        self.assertIsNone(self.processor.get_invoice_value(response))

        del response['Data']['InvoiceValue']
        self.assertIsNone(self.processor.get_invoice_value(response))

    def test_handle_processor_response(self):
        """ Verify the processor records the payment and reports the gateway's own amount. """
        response = self.payment_status_response(basket=self.basket)

        handled = self.processor.handle_processor_response(response, basket=self.basket)

        self.assertEqual(handled.transaction_id, self.PAYMENT_ID)
        self.assertEqual(handled.total, self.basket.total_incl_tax)
        self.assertEqual(handled.currency, self.basket.currency)
        self.assertEqual(handled.card_number, self.MASKED_CARD_NUMBER)
        self.assertEqual(handled.card_type, self.CARD_BRAND)

        self.assert_processor_response_recorded(
            self.processor.NAME,
            self.PAYMENT_ID,
            _scrub(response),
            basket=self.basket,
        )

    def test_handle_processor_response_without_card_detail(self):
        """ Verify a payment method that reports no card (e.g. KNET) still records. """
        response = self.payment_status_response(basket=self.basket, include_card=False)

        handled = self.processor.handle_processor_response(response, basket=self.basket)

        self.assertIsNone(handled.card_number)
        self.assertEqual(handled.card_type, 'VISA/MASTER')

    def test_issue_credit(self):
        """ Verify refunds are not supported. """
        with self.assertRaises(NotImplementedError):
            self.processor.issue_credit(
                self.basket.order_number, self.basket, self.PAYMENT_ID, Decimal('20.00'), 'USD'
            )

    def test_issue_credit_error(self):
        """ Refunds are unsupported, so there is no gateway error path to exercise. """
        with self.assertRaises(NotImplementedError):
            self.processor.issue_credit(
                self.basket.order_number, self.basket, self.PAYMENT_ID, Decimal('20.00'), 'USD'
            )

    def test_verify_webhook_signature(self):
        """ Verify a correctly signed webhook body is accepted. """
        body = self.webhook_body()
        self.assertTrue(self.processor.verify_webhook_signature(body, self.signature_for(body)))

    def test_verify_webhook_signature_rejects_bad_signature(self):
        """ Verify a wrong signature, a missing header, and a wrong secret are all rejected. """
        body = self.webhook_body()

        self.assertFalse(self.processor.verify_webhook_signature(body, 'not-the-signature'))
        self.assertFalse(self.processor.verify_webhook_signature(body, None))
        self.assertFalse(
            self.processor.verify_webhook_signature(body, self.signature_for(body, secret='wrong-secret'))
        )

    def test_verify_webhook_signature_fails_closed_without_secret(self):
        """ Verify verification fails when no webhook secret is configured.

        A missing secret must not be read as "no verification required".
        """
        body = self.webhook_body()
        signature = self.signature_for(body)
        self.processor.webhook_secret = None

        self.assertFalse(self.processor.verify_webhook_signature(body, signature))

    def test_verify_webhook_signature_without_data(self):
        """ Verify a body with no Data object is rejected rather than crashing. """
        self.assertFalse(self.processor.verify_webhook_signature({'Event': {'Code': 1}}, 'signature'))


class ScrubTests(MyFatoorahMixin, TestCase):
    """ Tests of the payload allow-list applied before anything is persisted.

    These encode a PCI guarantee: what MyFatoorah sends us is not what we store.
    """

    def test_scrub_drops_cardholder_name_and_expiry(self):
        """ Verify only the masked PAN and brand survive from the Card object. """
        scrubbed = _scrub(self.payment_status_response())

        card = scrubbed['Data']['InvoiceTransactions'][0]['Card']
        self.assertEqual(card, {'Number': self.MASKED_CARD_NUMBER, 'Brand': self.CARD_BRAND})
        self.assertNotIn('NameOnCard', card)
        self.assertNotIn('ExpiryMonth', card)
        self.assertNotIn('ExpiryYear', card)

    def test_scrub_drops_customer_contact_detail(self):
        """ Verify learner contact details are not duplicated into the audit row. """
        scrubbed = _scrub(self.payment_status_response())

        self.assertNotIn('CustomerEmail', scrubbed['Data'])
        self.assertNotIn('CustomerName', scrubbed['Data'])

    def test_scrub_keeps_the_fields_we_reconcile_on(self):
        """ Verify scrubbing does not discard what we need for audit and reconciliation. """
        scrubbed = _scrub(self.payment_status_response(customer_reference='EDX-100001'))

        data = scrubbed['Data']
        self.assertEqual(data['InvoiceId'], self.INVOICE_ID)
        self.assertEqual(data['InvoiceStatus'], 'Paid')
        self.assertEqual(data['CustomerReference'], 'EDX-100001')
        self.assertIn('InvoiceValue', data)

        transaction = data['InvoiceTransactions'][0]
        self.assertEqual(transaction['PaymentId'], self.PAYMENT_ID)
        self.assertEqual(transaction['TransactionStatus'], 'Succss')

    def test_scrub_drops_unknown_fields(self):
        """ Verify a field MyFatoorah adds later is not persisted just because it is new. """
        response = self.payment_status_response()
        response['Data']['SomeNewSensitiveField'] = 'nope'
        response['Data']['InvoiceTransactions'][0]['AnotherNewField'] = 'also nope'

        scrubbed = _scrub(response)

        self.assertNotIn('SomeNewSensitiveField', scrubbed['Data'])
        self.assertNotIn('AnotherNewField', scrubbed['Data']['InvoiceTransactions'][0])

    def test_scrub_handles_malformed_payloads(self):
        """ Verify scrubbing never raises on unexpected shapes. """
        self.assertEqual(_scrub(None), {})
        self.assertEqual(_scrub('a string'), {})
        self.assertEqual(_scrub({}), {})
        self.assertEqual(_scrub({'IsSuccess': True, 'Data': None}), {'IsSuccess': True})
