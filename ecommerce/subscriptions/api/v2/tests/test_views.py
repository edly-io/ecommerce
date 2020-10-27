"""
Unit tests for subscription API views.
"""
import json
import pytest

from django.urls import reverse

from ecommerce.subscriptions.api.v2.tests.constants import LIMITED_ACCESS
from ecommerce.subscriptions.api.v2.tests.mixins import SubscriptionProductMixin
from ecommerce.tests.testcases import TestCase


class SubscriptionViewSetTests(SubscriptionProductMixin, TestCase):
    """
    Unit tests for "SubscriptionViewSet".
    """

    def test_list(self):
        """
        Verify that subscriptions list API returns results correctly.
        """
        self.create_subscription(stockrecords__partner=self.site.partner)
        expected_keys = [
            'title', 'subscription_type', 'subscription_actual_price', 'subscription_price', 'subscription_status',
            'display_order', 'partner_sku', 'is_course_payments_enabled'
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
            'subscription_type': LIMITED_ACCESS,
            'subscription_actual_price': 100.00,
            'subscription_price': 50.00,
            'subscription_active_status': 'true',
            'number_of_courses': 4,
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
            'subscription_type': LIMITED_ACCESS,
            'subscription_actual_price': 100.00,
            'subscription_price': 50.00,
            'subscription_active_status': 'inactive',
            'number_of_courses': 4,
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
        self.assertFalse(response.data.get('subscription_status'))

    def test_toggle_course_payments(self):
        """
        Verify that subscriptions API correctly toggles course payments flag.
        """
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
