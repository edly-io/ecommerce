from __future__ import unicode_literals

import logging
import operator

from django.db import models
from oscar.apps.offer import utils as oscar_utils
from oscar.core.loading import get_model

from ecommerce.core.constants import ENABLE_SUBSCRIPTIONS_ON_RUNTIME_SWITCH
from ecommerce.extensions.offer.decorators import check_condition_applicability
from ecommerce.extensions.offer.mixins import ConditionWithoutRangeMixin, SingleItemConsumptionConditionMixin
from ecommerce.subscriptions.utils import SUBSCRIPTION_ATTRIBUTE_TYPE, get_active_user_subscription, SUBSCRIPTION_ID_ATTRIBUTE_TYPE

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
        return 'Basket includes a subscription'

    @check_condition_applicability([ENABLE_SUBSCRIPTIONS_ON_RUNTIME_SWITCH])
    def is_satisfied(self, offer, basket):  # pylint: disable=unused-argument
        """
        Checks if a user has a valid purchased subscription.

        Arguments:
            basket (Basket): Basket object with all the relevant information of owner and cart lines.

        Returns:
            bool: Boolean value of whether a subscription can be applied.
        """
        if not basket.owner:
            return False

        if basket.site.partner != offer.partner:
            return False

        active_user_subscription = get_active_user_subscription(basket.owner, basket.site)
        if not active_user_subscription:
            return False

        subscription_id_attribute, __ = BasketAttributeType.objects.get_or_create(name=SUBSCRIPTION_ID_ATTRIBUTE_TYPE)
        BasketAttribute.objects.get_or_create(
            basket=basket,
            attribute_type=subscription_id_attribute,
            value_text=active_user_subscription.get(SUBSCRIPTION_ID_ATTRIBUTE_TYPE)
        )
        return True

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
        applicable_lines = []
        try:
            BasketAttribute.objects.get(
                basket=basket,
                attribute_type=BasketAttributeType.objects.get(name=SUBSCRIPTION_ATTRIBUTE_TYPE),
            )
        except BasketAttribute.DoesNotExist:
            return applicable_lines

        for line in basket.all_lines():
            if not self.can_apply_condition(line, basket):
                continue

            price = oscar_utils.unit_price(offer, line)
            if not price:
                continue

            applicable_lines.append((price, line))

        return sorted(applicable_lines, reverse=most_expensive_first, key=operator.itemgetter(0))
