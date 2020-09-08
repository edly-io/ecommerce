"""
Unit tests for subscription module.
"""
import ddt
import httpretty
import json
import mock
from oscar.core.loading import get_model
from oscar.test.factories import (
    BasketFactory,
    UserFactory,
)
from requests.exceptions import ConnectionError, Timeout
from testfixtures import LogCapture

from django.test import override_settings

from ecommerce.extensions.fulfillment.status import LINE
from ecommerce.extensions.fulfillment.tests.mixins import FulfillmentTestMixin
from ecommerce.extensions.test.factories import create_order
from ecommerce.subscriptions.api.v2.tests.mixins import SubscriptionProductMixin
from ecommerce.subscriptions.modules import SubscriptionFulfillmentModule
from ecommerce.subscriptions.utils import get_lms_user_subscription_api_url, get_subscription_expiration_date
from ecommerce.tests.factories import ProductFactory
from ecommerce.tests.testcases import TestCase

LOGGER_NAME = 'ecommerce.extensions.analytics.utils'
JSON = 'application/json'


@ddt.ddt
@override_settings(EDX_API_KEY='foo')
class SubscriptionFulfillmentModuleTests(FulfillmentTestMixin, SubscriptionProductMixin, TestCase):
    """
    Unit tests for "SubscriptionModule".
    """

    def setUp(self):
        """
        Setup initial test data.
        """
        super(SubscriptionFulfillmentModuleTests, self).setUp()

        self.user = UserFactory()
        self.user.tracking_context = {
            'ga_client_id': 'test-client-id', 'lms_user_id': 'test-user-id', 'lms_ip': '127.0.0.1'
        }
        self.user.save()
        self.subscription = self.create_subscription()
        self.basket = BasketFactory(owner=self.user, site=self.site)
        self.basket.add_product(self.subscription, 1)
        self.order = create_order(number=1, basket=self.basket, user=self.user)

        subscription_type = self.subscription.attr.subscription_type.option
        subscription_expiration = get_subscription_expiration_date(self.subscription)
        number_of_courses = self.subscription.attribute_values.filter(attribute__code='number_of_courses').first()
        self.user_subscription_api_payload = {
            'user': self.order.user.username,
            'subscription_id': self.subscription.id,
            'expiration_date': str(subscription_expiration) if subscription_expiration else subscription_expiration,
            'subscription_type': subscription_type,
            'max_allowed_courses': number_of_courses.value if number_of_courses else None,
        }

    def test_get_supported_lines(self):
        """
        Verify that "SubscriptionFullfillmentModule" gets lines containing subscription product.
        """
        basket = BasketFactory(owner=self.user, site=self.site)
        basket.add_product(
            ProductFactory(stockrecords__partner=self.partner),
            1
        )
        basket.add_product(self.subscription, 1)
        order = create_order(number=2, basket=basket, user=self.user)
        supported_lines = SubscriptionFulfillmentModule().get_supported_lines(list(order.lines.all()))
        self.assertEqual(1, len(supported_lines))

    @httpretty.activate
    def test_subscription_fulfillment_module_fulfills_successfully(self):
        """
        Verify that "SubscriptionFullfillmentModule" fulfills the subscription product line successfully
        """
        httpretty.register_uri(httpretty.PUT, get_lms_user_subscription_api_url(self.subscription.id), status=201, body='{}', content_type=JSON)
        with LogCapture(LOGGER_NAME) as logs:
            SubscriptionFulfillmentModule().fulfill_product(self.order, list(self.order.lines.all()))

            line = self.order.lines.get()
            logs.check(
                (
                    LOGGER_NAME,
                    'INFO',
                    'line_fulfilled: order_line_id="{}", order_number="{}", product_class="{}", user_id="{}"'.format(
                        line.id,
                        line.order.number,
                        line.product.get_product_class().name,
                        line.order.user.id,
                    )
                )
            )

        self.assertEqual(LINE.COMPLETE, line.status)

        last_request = httpretty.last_request()
        actual_body = json.loads(last_request.body)
        actual_headers = last_request.headers

        expected_headers = {
            'X-Edx-Ga-Client-Id': self.user.tracking_context['ga_client_id'],
            'X-Forwarded-For': self.user.tracking_context['lms_ip'],
        }

        self.assertDictContainsSubset(expected_headers, actual_headers)
        self.assertEqual(self.user_subscription_api_payload, actual_body)

    @override_settings(EDX_API_KEY=None)
    def test_subscription_fulfillment_module_not_configured(self):
        """
        Verify that subscription fulfillment fails if valid configuration is not present.
        """
        SubscriptionFulfillmentModule().fulfill_product(self.order, list(self.order.lines.all()))
        self.assertEqual(LINE.FULFILLMENT_CONFIGURATION_ERROR, self.order.lines.all()[0].status)

    @mock.patch('requests.put', mock.Mock(side_effect=ConnectionError))
    def test_subscription_fulfillment_module_network_error(self):
        """
        Verify that subscription fulfillment fails if there is a ConnectionError.
        """
        SubscriptionFulfillmentModule().fulfill_product(self.order, list(self.order.lines.all()))
        self.assertEqual(LINE.FULFILLMENT_NETWORK_ERROR, self.order.lines.all()[0].status)

    @mock.patch('requests.put', mock.Mock(side_effect=Timeout))
    def test_subscription_fulfillment_module_request_timeout(self):
        """
        Verify that subscription fulfillment fails if there is a Timeout error.
        """
        SubscriptionFulfillmentModule().fulfill_product(self.order, list(self.order.lines.all()))
        self.assertEqual(LINE.FULFILLMENT_TIMEOUT_ERROR, self.order.lines.all()[0].status)

    @httpretty.activate
    @ddt.data(None, '{"message": "Error occurred!"}')
    def test_subscription_fulfillment_module_server_error(self, body):
        """
        Verify that subscription fulfillment fails if there is an internal server error.
        """
        httpretty.register_uri(httpretty.PUT, get_lms_user_subscription_api_url(self.subscription.id), status=500, body=body, content_type=JSON)
        SubscriptionFulfillmentModule().fulfill_product(self.order, list(self.order.lines.all()))
        self.assertEqual(LINE.FULFILLMENT_SERVER_ERROR, self.order.lines.all()[0].status)

    def test_revoke_subscription(self):
        """
        Verify that subscription product line revokation logs correctly.
        """
        line = self.order.lines.first()

        with LogCapture(LOGGER_NAME) as logs:
            self.assertTrue(SubscriptionFulfillmentModule().revoke_line(line))

            logs.check(
                (
                    LOGGER_NAME,
                    'INFO',
                    'line_revoked: order_line_id="{}", order_number="{}", product_class="{}", user_id="{}"'.format(
                        line.id,
                        line.order.number,
                        line.product.get_product_class().name,
                        line.order.user.id
                    )
                )
            )

    def test_subscription_fulfillment_request_headers(self):
        """
        Verify that subscription fulfillment request contains analytics headers.
        """
        # Now call the subscription api to send PUT request to LMS and verify
        # that the header of the request being sent contains the analytics
        # header 'x-edx-ga-client-id'.
        # This will raise the exception 'ConnectionError' because the LMS is
        # not available for ecommerce tests.
        try:
            # pylint: disable=protected-access
            SubscriptionFulfillmentModule()._post_to_user_subscription_api(data=self.user_subscription_api_payload, user=self.user)
        except ConnectionError as exp:
            # Check that the enrollment request object has the analytics header
            # 'x-edx-ga-client-id' and 'x-forwarded-for'.
            self.assertEqual(exp.request.headers.get('x-edx-ga-client-id'), self.user.tracking_context['ga_client_id'])
            self.assertEqual(exp.request.headers.get('x-forwarded-for'), self.user.tracking_context['lms_ip'])
