"""
Unit tests for subscription API views.
"""
import json
import mock
from oscar.test.factories import OrderLineFactory
import pytest

from django.urls import reverse

from ecommerce.core.models import SiteConfiguration
from ecommerce.subscriptions.api.v2.tests.constants import LIMITED_ACCESS, FULL_ACCESS_COURSES
from ecommerce.subscriptions.api.v2.tests.mixins import SubscriptionProductMixin
from ecommerce.subscriptions.api.v2.tests.utils import mock_user_subscription
from ecommerce.tests.testcases import TestCase


class SubscriptionViewSetTests(SubscriptionProductMixin, TestCase):
    """
    Unit tests for "SubscriptionViewSet".
    """
    def _login_as_user(self, username=None, is_staff=False):
        """
        Log in with a particular username or as staff user.
        """
        user = self.create_user(
            username=username,
            is_staff=is_staff
        )

        self.client.logout()
        self.client.login(username=user.username, password='test')
        return user

    def _build_renew_subscription_url(self, subscription_id):
        """
        build renew subscription url for a given subscription.
        """
        return '{root_url}?subscription_id={subscription_id}'.format(
            root_url=reverse('api:v2:subscriptions-renew-subscription-list'),
            subscription_id=subscription_id
        )

    def test_list(self):
        """
        Verify that subscriptions list API returns results correctly.
        """
        self.create_subscription(stockrecords__partner=self.site.partner)
        expected_keys = [
            'id', 'title', 'date_created', 'subscription_type', 'subscription_actual_price', 'subscription_price',
            'subscription_status', 'display_order', 'partner_sku', 'is_course_payments_enabled'
        ]
        request_url = reverse('api:v2:subscriptions-list')
        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(response.data.get('count'), 0)
        self.assertEqual(response.data.get('results')[0].keys(), expected_keys)

    def test_list_active(self):
        """
        Verify that subscriptions list API returns results correctly with active filter.
        """
        request_url = reverse('api:v2:subscriptions-list') + '?filter_active=true'
        self.create_subscription(stockrecords__partner=self.site.partner)
        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(response.data.get('count'), 0)
        self.create_subscription(stockrecords__partner=self.site.partner, subscription_status=False)
        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('count'), 1)

    def test_retrieve(self):
        """
        Verify that subscriptions API returns results correctly.
        """
        subscription = self.create_subscription(stockrecords__partner=self.site.partner)
        request_url = reverse('api:v2:subscriptions-detail', args=[subscription.id])
        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data)

    def test_create(self):
        """
        Verify that subscriptions API correctly creates a new subscription.
        """
        subscription_data = {
            'title': 'Test subscription',
            'description': 'Test subscription description',
            'subscription_type': LIMITED_ACCESS,
            'subscription_actual_price': 100.00,
            'subscription_price': 50.00,
            'subscription_active_status': 'true',
            'subscription_number_of_courses': 4,
            'subscription_duration_value': 4,
            'subscription_duration_unit': 'months',
            'subscription_display_order': 1
        }
        request_url = reverse('api:v2:subscriptions-list')
        response = self.client.get(request_url)
        self.assertEqual(response.data.get('count'), 0)
        response = self.client.post(request_url, data=subscription_data)
        self.assertEqual(response.status_code, 201)
        response = self.client.get(request_url)
        self.assertGreater(response.data.get('count'), 0)

    def test_update(self):
        """
        Verify that subscriptions API correctly updates a new subscription.
        """
        subscription = self.create_subscription(stockrecords__partner=self.site.partner)
        subscription_data = {
            'title': 'Test subscription',
            'description': 'Test subscription description',
            'subscription_type': LIMITED_ACCESS,
            'subscription_actual_price': 100.00,
            'subscription_price': 50.00,
            'subscription_active_status': 'inactive',
            'subscription_number_of_courses': 4,
            'subscription_duration_value': 4,
            'subscription_duration_unit': 'months',
            'subscription_display_order': 1
        }
        request_url = reverse('api:v2:subscriptions-detail', args=[subscription.id])
        response = self.client.put(request_url, data=json.dumps(subscription_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('title'), subscription_data.get('title'))
        self.assertEqual(response.data.get('description'), subscription_data.get('description'))
        self.assertFalse(response.data.get('subscription_status'))

    def test_toggle_course_payments_without_authentication(self):
        """
        Verify that subscriptions API does not toggle course payments flag without authentication.
        """
        request_url = reverse('api:v2:subscriptions-toggle-course-payments-list')
        response = self.client.post(request_url)
        self.assertEqual(response.status_code, 401)

    def test_toggle_course_payments_with_authentication(self):
        """
        Verify that subscriptions API correctly toggles course payments flag with authentication.
        """
        self._login_as_user(is_staff=True)
        request_url = reverse('api:v2:subscriptions-toggle-course-payments-list')
        expected_data = {
            'course_payments': not self.site.siteconfiguration.enable_course_payments
        }
        response = self.client.post(request_url)
        self.assertEqual(response.data, expected_data)
        self.assertEqual(response.status_code, 200)

    def test_course_payments_status(self):
        """
        Verify that subscriptions API correctly returns course payments flag status.
        """
        request_url = reverse('api:v2:subscriptions-course-payments-status-list')
        expected_data = {
            'course_payments': self.site.siteconfiguration.enable_course_payments
        }
        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, expected_data)

    @mock.patch.object(SiteConfiguration, 'access_token', mock.Mock(return_value='foo'))
    def test_renew_subscription_without_subscription_id_query_parameter(self):
        """
        Verify that subscriptions API returns correct response on missing subscription id.
        """
        self._login_as_user(is_staff=True)
        request_url = reverse('api:v2:subscriptions-renew-subscription-list')

        expected_data = dict(error='Subscription ID not provided.')
        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 406)
        self.assertDictEqual(response.data, expected_data)

    @mock.patch.object(SiteConfiguration, 'access_token', mock.Mock(return_value='foo'))
    def test_renew_subscription_without_subscription(self):
        """
        Verify that subscriptions API returns correct response if subscription is inactive/non-existant.
        """
        self._login_as_user(is_staff=True)
        request_url = self._build_renew_subscription_url(1)
        expected_data = dict(error='Subscription is inactive or does not exist.')
        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 406)
        self.assertDictEqual(response.data, expected_data)

    @mock.patch.object(SiteConfiguration, 'access_token', mock.Mock(return_value='foo'))
    def test_renew_subscription_with_incorrect_subscription_type(self):
        """
        Verify that subscriptions API correct response if requested subscription is of unsupported.
        """
        self._login_as_user(is_staff=True)
        limited_access_subscription = self.create_subscription(
            subscription_type=LIMITED_ACCESS, stockrecords__partner=self.site.partner
        )
        request_url = self._build_renew_subscription_url(str(limited_access_subscription.id))
        expected_data = dict(
            error='Subscription of type {no_expiry_type} can\'t be renewed.'.format(
                no_expiry_type=limited_access_subscription.attr.subscription_type.option
            )
        )
        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 406)
        self.assertDictEqual(response.data, expected_data)

    @mock.patch.object(SiteConfiguration, 'access_token', mock.Mock(return_value='foo'))
    @mock.patch('ecommerce.subscriptions.utils.get_lms_resource_for_user')
    def test_renew_subscription_with_existing_valid_subscription(self, lms_resource_for_user):
        """
        Verify that subscriptions API correct response if user already has a valid subscription.
        """
        self._login_as_user(is_staff=True)
        full_access_courses_subscription = self.create_subscription(
            subscription_type=FULL_ACCESS_COURSES,
            subscription_status=True,
            stockrecords__partner=self.site.partner
        )
        request_url = self._build_renew_subscription_url(str(full_access_courses_subscription.id))
        lms_resource_for_user.return_value = [mock_user_subscription()]
        expected_data = dict(error='User already has a valid subscription.')
        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 406)
        self.assertDictEqual(response.data, expected_data)

    @mock.patch.object(SiteConfiguration, 'access_token', mock.Mock(return_value='foo'))
    @mock.patch('ecommerce.subscriptions.utils.get_lms_resource_for_user')
    def test_renew_subscription_without_existing_purchase_of_subscription(self, lms_resource_for_user):
        """
        Verify that subscriptions API correct response if user has not purchased requested subscription previously.
        """
        self._login_as_user(is_staff=True)
        full_access_courses_subscription = self.create_subscription(
            subscription_type=FULL_ACCESS_COURSES,
            subscription_status=True,
            stockrecords__partner=self.site.partner
        )
        request_url = self._build_renew_subscription_url(str(full_access_courses_subscription.id))
        lms_resource_for_user.return_value = []
        expected_data = dict(error='The user has not purchased the requested subscription previously.')
        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 406)
        self.assertDictEqual(response.data, expected_data)

    @mock.patch.object(SiteConfiguration, 'access_token', mock.Mock(return_value='foo'))
    def test_renew_subscription_with_all_checks_passed(self):
        """
        Verify that subscriptions API correctly redirects to basket page if all checks have passed.
        """
        user = self._login_as_user(is_staff=True)
        full_access_courses_subscription = self.create_subscription(
            subscription_type=FULL_ACCESS_COURSES,
            subscription_status=True,
            stockrecords__partner=self.site.partner
        )
        request_url = self._build_renew_subscription_url(str(full_access_courses_subscription.id))
        OrderLineFactory(product=full_access_courses_subscription, order__user=user)
        response = self.client.get(request_url)
        expected_url = '{base_url}?sku={sku}'.format(
            base_url=reverse('basket:basket-add'),
            sku=full_access_courses_subscription.stockrecords.first().partner_sku,
        )
        self.assertRedirects(response, expected_url, fetch_redirect_response=False)
