"""
Unit tests for subscription utility methods.
"""
import httpretty
import json
import mock
from oscar.test.factories import BasketFactory
from testfixtures import LogCapture

from ecommerce.core.models import SiteConfiguration
from ecommerce.subscriptions.api.v2.tests.factories import BasketAttributeFactory, MockUserSubscriptionFactory
from ecommerce.subscriptions.api.v2.tests.mixins import SubscriptionProductMixin
from ecommerce.subscriptions.utils import *
from ecommerce.tests.testcases import TestCase

Product = get_model('catalogue', 'Product')


class SubscriptionUtilsTests(SubscriptionProductMixin, TestCase):
    """
    Unit tests for subscription utility methods.
    """

    def setUp(self):
        """
        Setup initial test data.
        """
        super(SubscriptionUtilsTests, self).setUp()
        self.subscription = self.create_subscription(stockrecords__partner=self.site.partner, subscription_status=True)
        self.user = self.create_user()
        self.basket = BasketFactory(site=self.site, owner=self.user)

    def get_duration_to_add(self, subscription):
        """
        Tests utility method to get subscription duration to add to the current date.
        """
        subscription_duration_unit = subscription.attr.subscription_duration_unit.option
        subscription_duration_value = subscription.attr.subscription_duration_value
        return {subscription_duration_unit: subscription_duration_value}

    def test_is_subscription_buyable_with_inactive_subscription(self):
        """
        Verify that is_subscription_buyable returns False for an inactive subscription.
        """
        Product.objects.all().delete()
        subscription = self.create_subscription(stockrecords__partner=self.site.partner, subscription_status=False)
        self.assertFalse(is_subscription_buyable(subscription, self.user, self.site))

    @mock.patch('ecommerce.subscriptions.utils.get_valid_user_subscription')
    def test_is_subscription_buyable_with_no_valid_subscription(self, valid_user_subscription):
        """
        Verify that is_subscription_buyable returns True for empty subscription result from LMS.

        If there is an empty response for valid user subscriptions from LMS for a user, it means that
        the given user has no purchased valid subscription and hence can buy a new subscription.
        """
        valid_user_subscription.return_value = []
        self.assertTrue(is_subscription_buyable(self.subscription, self.user, self.site))

    @mock.patch('ecommerce.subscriptions.utils.get_valid_user_subscription')
    def test_is_subscription_buyable_with_valid_subscription(self, valid_user_subscription):
        """
        Verify that is_subscription_buyable returns False for subscription result from LMS.

        If there is a non-empty response for valid user subscriptions from LMS for a user, it means that
        the given user already owns a valid subscription and hence can not buy a new subscription.
        """
        valid_user_subscription.return_value = [MockUserSubscriptionFactory()]
        self.assertFalse(is_subscription_buyable(self.subscription, self.user, self.site))

    def test_basket_add_subscription_attribute(self):
        """
        Verify that basket attribute for subscription application is set successfully.
        """
        request_data = {
            SUBSCRIPTION_ATTRIBUTE_TYPE: 'false'
        }
        basket_attribute_type = BasketAttributeType.objects.get(name=SUBSCRIPTION_ATTRIBUTE_TYPE)
        basket_add_subscription_attribute(self.basket, request_data)
        self.assertFalse(BasketAttribute.objects.filter(basket=self.basket, attribute_type=basket_attribute_type).exists())

        request_data[SUBSCRIPTION_ATTRIBUTE_TYPE] = 'true'
        basket_add_subscription_attribute(self.basket, request_data)
        self.assertTrue(BasketAttribute.objects.filter(basket=self.basket, attribute_type=basket_attribute_type).exists())

    def test_get_subscription_from_basket_attribute(self):
        """
        Verify that get_subscription_from_basket_attribute correctly retrieves subscription ID from basket attribute.
        """
        self.assertIsNone(get_subscription_from_basket_attribute(self.basket))
        subscription_id_attribute_type, __ = BasketAttributeType.objects.get_or_create(name=SUBSCRIPTION_ID_ATTRIBUTE_TYPE)
        BasketAttributeFactory(
            basket=self.basket,
            attribute_type=subscription_id_attribute_type,
            value_text=str(self.subscription.id)
        )
        self.assertTrue(get_subscription_from_basket_attribute(self.basket))

    def get_subscription_expiration_date(self):
        """
        Verify that get_subscription_expiry_date method calculates the expiration date correctly.
        """
        limited_subscription = self.create_subscription(product_attributes__subscription_type='limited-access')
        limited_subscription_duration_to_add = self.get_duration_to_add(limited_subscription)
        limited_subscription_expiration_date = date.today() + relativedelta(**limited_subscription_duration_to_add)

        full_access_courses_subscription = self.create_subscription(product_attributes__subscription_type='full-access-courses')
        full_access_courses_subscription_duration_to_add = self.get_duration_to_add(full_access_courses_subscription)
        full_access_courses_subscription_expiration_date = date.today() + relativedelta(**full_access_courses_subscription_duration_to_add)

        full_access_time_period_subscription = self.create_subscription(product_attributes__subscription_type='full-access-time-period')
        lifetime_subscription = self.create_subscription(product_attributes__subscription_type='lifetime-access')

        self.assertEqual(get_subscription_expiration_date(limited_subscription), limited_subscription_expiration_date)
        self.assertEqual(get_subscription_expiration_date(full_access_courses_subscription), full_access_courses_subscription_expiration_date)
        self.assertIsNone(get_subscription_expiration_date(full_access_time_period_subscription))
        self.assertIsNone(get_subscription_expiration_date(lifetime_subscription))

    @mock.patch.object(SiteConfiguration, 'access_token', mock.Mock(return_value='foo'))
    @mock.patch('ecommerce.subscriptions.utils.get_lms_resource_for_user')
    def test_get_valid_user_subscription(self, lms_resource_for_user):
        """
        Verify that get_valid_user_subscription method fetches a valid user subscription successfully.
        """
        lms_resource_for_user.return_value = []
        valid_user_subscription = get_valid_user_subscription(self.user, self.site)
        self.assertEqual(valid_user_subscription, [])

        lms_response = MockUserSubscriptionFactory()
        lms_resource_for_user.return_value = lms_response
        valid_user_subscription = get_valid_user_subscription(self.user, self.site)
        self.assertEqual(valid_user_subscription, lms_response)

    @httpretty.activate
    @mock.patch.object(SiteConfiguration, 'access_token', mock.Mock(return_value='foo'))
    def test_get_lms_resource_for_user_with_connection_error(self):
        """
        Verify that get_lms_resource_for_user catches ConnectionError correctly.
        """
        def request_callback(_method, _uri, _headers):
            raise ConnectionError

        endpoint = self.site_configuration.subscriptions_api_client.user_subscriptions
        httpretty.register_uri(httpretty.GET, endpoint.url(), body=request_callback)
        query_dict = dict(valid=True, user=self.user.username)
        with LogCapture(logger.name) as logs:
            response = get_lms_resource_for_user(
                self.user, self.site, endpoint, resource_name=SUBSCRIPTION_RESOURCE_NAME, query_dict=query_dict
            )
            self.assertEqual(response, [])
            logs.check(
                (
                    logger.name,
                    'ERROR',
                    'Failed to retrieve {} : {}'.format(
                        SUBSCRIPTION_RESOURCE_NAME,
                        '(\'Connection aborted.\', BadStatusLine("\'\'",))'
                    )
                )
            )

    @httpretty.activate
    @mock.patch.object(SiteConfiguration, 'access_token', mock.Mock(return_value='foo'))
    def test_get_lms_resource_for_user_with_slumber_exception(self):
        """
        Verify that get_lms_resource_for_user catches SlumberBaseException correctly.
        """
        def request_callback(_method, _uri, _headers):
            raise SlumberBaseException

        endpoint = self.site_configuration.subscriptions_api_client.user_subscriptions
        httpretty.register_uri(httpretty.GET, endpoint.url(), body=request_callback)
        query_dict = dict(valid=True, user=self.user.username)
        with LogCapture(logger.name) as logs:
            response = get_lms_resource_for_user(
                self.user, self.site, endpoint, resource_name=SUBSCRIPTION_RESOURCE_NAME, query_dict=query_dict
            )
            self.assertEqual(response, [])
            logs.check(
                (
                    logger.name,
                    'ERROR',
                    'Failed to retrieve {} : {}'.format(
                        SUBSCRIPTION_RESOURCE_NAME,
                        '(\'Connection aborted.\', BadStatusLine("\'\'",))'
                    )
                )
            )

    @httpretty.activate
    @mock.patch.object(SiteConfiguration, 'access_token', mock.Mock(return_value='foo'))
    def test_get_lms_resource_for_user_with_timeout_error(self):
        """
        Verify that get_lms_resource_for_user catches TimeoutError correctly.
        """
        def request_callback(_method, _uri, _headers):
            raise Timeout

        endpoint = self.site_configuration.subscriptions_api_client.user_subscriptions
        httpretty.register_uri(httpretty.GET, endpoint.url(), body=request_callback)
        query_dict = dict(valid=True, user=self.user.username)
        with LogCapture(logger.name) as logs:
            response = get_lms_resource_for_user(
                self.user, self.site, endpoint, resource_name=SUBSCRIPTION_RESOURCE_NAME, query_dict=query_dict
            )
            self.assertEqual(response, [])
            logs.check(
                (
                    logger.name,
                    'ERROR',
                    'Failed to retrieve {} : {}'.format(
                        SUBSCRIPTION_RESOURCE_NAME,
                        '(\'Connection aborted.\', BadStatusLine("\'\'",))'
                    )
                )
            )

    @httpretty.activate
    @mock.patch.object(SiteConfiguration, 'access_token', mock.Mock(return_value='foo'))
    def test_get_lms_resource_for_user(self):
        """
        Verify that get_lms_resource_for_user returns results correctly if no exceptions are raised.
        """
        lms_user_subscription_response = MockUserSubscriptionFactory()
        endpoint = self.site_configuration.subscriptions_api_client.user_subscriptions
        httpretty.register_uri(httpretty.GET, endpoint.url(), body='[{}]'.format(json.dumps(lms_user_subscription_response)), content_type="application/json")
        query_dict = dict(valid=True, user=self.user.username)
        response = get_lms_resource_for_user(
            self.user, self.site, endpoint, resource_name=SUBSCRIPTION_RESOURCE_NAME, query_dict=query_dict
        )
        self.assertEqual(response, lms_user_subscription_response)
