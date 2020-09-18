from __future__ import unicode_literals

import logging
import operator

from oscar.apps.offer import utils as oscar_utils
from oscar.core.loading import get_model

from django.db import models

from ecommerce.core.constants import ENABLE_SUBSCRIPTIONS_ON_RUNTIME_SWITCH
from ecommerce.extensions.offer.decorators import check_condition_applicability
from ecommerce.extensions.offer.mixins import ConditionWithoutRangeMixin, SingleItemConsumptionConditionMixin
from ecommerce.subscriptions.utils import get_active_user_subscription, SUBSCRIPTION_ATTRIBUTE_TYPE

logger = logging.getLogger(__name__)

BasketAttribute = get_model('basket', 'BasketAttribute')
BasketAttributeType = get_model('basket', 'BasketAttributeType')
Condition = get_model('offer', 'Condition')


class SubscriptionCondition(ConditionWithoutRangeMixin, SingleItemConsumptionConditionMixin, Condition):

    class Meta(object):
        app_label = 'subscriptions'
        proxy = True

    @property
    def name(self):
        return 'Basket includes a subscription {}'.format(self.subscription.title)

    @check_condition_applicability([ENABLE_SUBSCRIPTIONS_ON_RUNTIME_SWITCH])
    def is_satisfied(self, offer, basket):  # pylint: disable=unused-argument
        """
        Checks if a user has a valid purchased subscription.
        Args:
            basket : contains information on line items for order, associated siteconfiguration
                        for retrieving program details, and associated user for retrieving enrollments
        Returns:
            bool
        """
        if not basket.owner:
            return False

        active_user_subscriptions = get_active_user_subscription(basket.owner, basket.site)
        return len(active_user_subscriptions) > 0

    def can_apply_condition(self, line, basket):
        """
        Determines whether the condition can be applied to a given basket line.
        """
        product = line.product
        if not product.is_seat_product or not product.get_is_discountable():
            return False

        return True

    def get_applicable_lines(self, offer, basket, most_expensive_first=True):
        """
        Return line data for the lines that can be consumed by this condition.
        """
        line_tuples = []
        try:
            BasketAttribute.objects.get(
                basket=basket,
                attribute_type=BasketAttributeType.objects.get(name=SUBSCRIPTION_ATTRIBUTE_TYPE),
            )
        except BasketAttribute.DoesNotExist:
            return line_tuples
        for line in basket.all_lines():
            if not self.can_apply_condition(line, basket):
                continue

            price = oscar_utils.unit_price(offer, line)
            if not price:
                continue
            line_tuples.append((price, line))

        return sorted(line_tuples, reverse=most_expensive_first, key=operator.itemgetter(0))
