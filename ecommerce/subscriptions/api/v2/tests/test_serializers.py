"""
Unit tests for subscription API serializers.
"""
import ddt

from ecommerce.subscriptions.api.v2.serializers import (
    SubscriptionListSerializer,
    SubscriptionSerializer,
)
from ecommerce.subscriptions.api.v2.tests.constants import (
    FULL_ACCESS_COURSES,
    FULL_ACCESS_TIME_PERIOD,
    LIFETIME_ACCESS,
    LIMITED_ACCESS,
    SUBSCRIPTION_TYPES,
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
        date_created = str(subscription.date_created).replace(' ', 'T').replace('+00:00', 'Z')
        expected_data = {
            'id': subscription.id,
            'title': subscription.title,
            'description': subscription.description,
            'date_created': date_created,
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
        LIMITED_ACCESS,
        FULL_ACCESS_COURSES,
        FULL_ACCESS_TIME_PERIOD,
        LIFETIME_ACCESS
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
            LIMITED_ACCESS: lambda subscription: {
                'subscription_number_of_courses': subscription.attr.subscription_number_of_courses,
                'subscription_duration_unit': subscription.attr.subscription_duration_unit.option,
                'subscription_duration_value': subscription.attr.subscription_duration_value
            },
            FULL_ACCESS_COURSES: lambda subscription: {
                'subscription_number_of_courses': None,
                'subscription_duration_unit': subscription.attr.subscription_duration_unit.option,
                'subscription_duration_value': subscription.attr.subscription_duration_value
            },
            FULL_ACCESS_TIME_PERIOD: lambda subscription: {
                'subscription_number_of_courses': subscription.attr.subscription_number_of_courses,
                'subscription_duration_unit': None,
                'subscription_duration_value': None
            },
            LIFETIME_ACCESS: lambda subscription: {
                'subscription_number_of_courses': None,
                'subscription_duration_unit': None,
                'subscription_duration_value': None
            },
        }
        date_created = str(subscription.date_created).replace(' ', 'T').replace('+00:00', 'Z')
        date_updated = str(subscription.date_updated).replace(' ', 'T').replace('+00:00', 'Z')
        expected_data = {
            'id': subscription.id,
            'title': subscription.title,
            'description': subscription.description,
            'date_created': date_created,
            'date_updated': date_updated,
            'subscription_type': subscription_type,
            'subscription_actual_price': subscription.attr.subscription_actual_price,
            'subscription_price': subscription.attr.subscription_price,
            'subscription_status': subscription.attr.subscription_status,
        }
        expected_data.update(conditional_attribute_values[subscription_type](subscription))

        subscription_serializer = SubscriptionSerializer(subscription, context=context)
        self.assertEqual(subscription_serializer.data, expected_data)
