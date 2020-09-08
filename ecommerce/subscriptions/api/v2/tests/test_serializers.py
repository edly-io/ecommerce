"""
Unit tests for subscription API serializers.
"""
import ddt

from ecommerce.subscriptions.api.v2.serializers import (
    SubscriptionListSerializer,
    SubscriptionSerializer,
)
from ecommerce.subscriptions.api.v2.tests.mixins import SubscriptionProductMixin
from ecommerce.tests.testcases import TestCase


class SubscriptionListSerializerTests(SubscriptionProductMixin, TestCase):
    """
    Unit tests for "SubscriptionListSerializer".
    """

    def test_list_serializer(self):
        """
        Verify that subscriptions list serializer correctly serializes subscriptions.
        """
        context = {
            'request': self.request,
            'partner': self.partner
        }
        subscription = self.create_subscription()
        expected_data = {
            'title': subscription.title,
            'subscription_type': subscription.attr.subscription_type.option,
            'subscription_actual_price': subscription.attr.subscription_actual_price,
            'subscription_price': subscription.attr.subscription_price,
            'subscription_status': subscription.attr.subscription_status,
            'display_order': subscription.attr.subscription_display_order,
            'partner_sku': subscription.stockrecords.first().partner_sku,
            'is_course_payments_enabled': self.request.site.siteconfiguration.enable_course_payments
        }
        subscription_serializer = SubscriptionListSerializer(subscription, context=context)
        self.assertEqual(subscription_serializer.data, expected_data)


@ddt.ddt
class SubscriptionSerializerTests(SubscriptionProductMixin, TestCase):
    """
    Unit tests for "SubscriptionSerializer".
    """
    @ddt.data(
        'limited-access',
        'full-access-courses',
        'full-access-time-period',
        'lifetime-access'
    )
    def test_subscription_serializer(self, subscription_type):
        """
        Verify that subscription serializer correctly serializes subscription detail.
        """
        context = {
            'request': self.request,
            'partner': self.partner
        }
        subscription = self.create_subscription(subscription_type=subscription_type)
        conditional_attribute_values = {
            'limited-access': lambda subscription: {
                'number_of_courses': subscription.attr.number_of_courses,
                'subscription_duration_unit': subscription.attr.subscription_duration_unit.option,
                'subscription_duration_value': subscription.attr.subscription_duration_value
            },
            'full-access-courses': lambda subscription: {
                'number_of_courses': None,
                'subscription_duration_unit': subscription.attr.subscription_duration_unit.option,
                'subscription_duration_value': subscription.attr.subscription_duration_value
            },
            'full-access-time-period': lambda subscription: {
                'number_of_courses': subscription.attr.number_of_courses,
                'subscription_duration_unit': None,
                'subscription_duration_value': None
            },
            'lifetime-access': lambda subscription: {
                'number_of_courses': None,
                'subscription_duration_unit': None,
                'subscription_duration_value': None
            },
        }
        expected_data = {
            'title': subscription.title,
            'subscription_type': subscription_type,
            'subscription_actual_price': subscription.attr.subscription_actual_price,
            'subscription_price': subscription.attr.subscription_price,
            'subscription_status': subscription.attr.subscription_status,
        }
        expected_data.update(conditional_attribute_values[subscription_type](subscription))

        subscription_serializer = SubscriptionSerializer(subscription, context=context)
        self.assertEqual(subscription_serializer.data, expected_data)
