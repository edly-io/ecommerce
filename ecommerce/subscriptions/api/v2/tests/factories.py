"""
Subscription related factories.
"""
from datetime import date
from factory import post_generation, RelatedFactory, SubFactory
from factory.django import DjangoModelFactory
from factory.fuzzy import (
    FuzzyChoice,
    FuzzyDate,
    FuzzyFloat,
    FuzzyInteger,
    FuzzyText,
)
from oscar.core.loading import get_model
from oscar.test.factories import (
    BenefitFactory,
    ConditionFactory,
    ConditionalOfferFactory,
    ProductAttributeValueFactory,
    ProductClassFactory,
)
from random import choice

from ecommerce.subscriptions.benefits import SubscriptionBenefit
from ecommerce.subscriptions.conditions import SubscriptionCondition
from ecommerce.subscriptions.custom import class_path

Basket = get_model('basket', 'Basket')
BasketAttribute = get_model('basket', 'BasketAttribute')
BasketAttributeType = get_model('basket', 'BasketAttributeType')
ConditionalOffer = get_model('offer', 'ConditionalOffer')
Product = get_model('catalogue', 'Product')

SUBSCRIPTION_ATTRIBUTES_VALUES = lambda subscription: {
    'limited-access': {
        'subscription_number_of_courses': FuzzyInteger(1, 10).fuzz(),
        'subscription_duration_value': FuzzyInteger(1, 10).fuzz(),
        'subscription_duration_unit': choice(subscription.attr.get_attribute_by_code('subscription_duration_unit').option_group.options.all()),
        'subscription_actual_price': FuzzyFloat(100.0, 500.0).fuzz(),
        'subscription_price': FuzzyFloat(10.0, 99.0).fuzz(),
        'subscription_display_order': FuzzyInteger(1, 5).fuzz(),
        'subscription_status': FuzzyChoice((True, False)).fuzz()
    },
    'full-access-courses': {
        'subscription_duration_value': FuzzyInteger(1, 10).fuzz(),
        'subscription_duration_unit': choice(subscription.attr.get_attribute_by_code('subscription_duration_unit').option_group.options.all()),
        'subscription_actual_price': FuzzyFloat(100.0, 500.0).fuzz(),
        'subscription_price': FuzzyFloat(10.0, 99.0).fuzz(),
        'subscription_display_order': FuzzyInteger(1, 5).fuzz(),
        'subscription_status': FuzzyChoice((True, False)).fuzz()
    },
    'full-access-time-period': {
        'subscription_number_of_courses': FuzzyInteger(1, 10).fuzz(),
        'subscription_actual_price': FuzzyFloat(100.0, 500.0).fuzz(),
        'subscription_price': FuzzyFloat(10.0, 99.0).fuzz(),
        'subscription_display_order': FuzzyInteger(1, 5).fuzz(),
        'subscription_status': FuzzyChoice((True, False)).fuzz()
    },
    'lifetime-access': {
        'subscription_actual_price': FuzzyFloat(100.0, 500.0).fuzz(),
        'subscription_price': FuzzyFloat(10.0, 99.0).fuzz(),
        'subscription_display_order': FuzzyInteger(1, 5).fuzz(),
        'subscription_status': FuzzyChoice((True, False)).fuzz()
    }
}


class SubscriptionFactory(DjangoModelFactory):
    """
    Factory class for Subscription product.
    """
    class Meta(object):
        model = Product

    title = FuzzyText()
    description = FuzzyText()
    product_class = SubFactory(ProductClassFactory)
    stockrecords = RelatedFactory('oscar.test.factories.StockRecordFactory', 'product')

    @post_generation
    def product_attributes(subscription, create, extracted, **kwargs):
        """
        Post generation product to set required subscription product attributes.
        """
        if not create:
            return

        subscription_type = kwargs.get('subscription_type')
        if subscription_type and not extracted:
            subscription_type_attribute = subscription.attr.get_attribute_by_code('subscription_type')
            subscription_type_option = subscription_type_attribute.option_group.options.get(option=subscription_type)
            setattr(subscription.attr, 'subscription_type', subscription_type_option)
            for attribute_key, attribute_value in SUBSCRIPTION_ATTRIBUTES_VALUES(subscription)[subscription_type].items():
                setattr(subscription.attr, attribute_key, attribute_value)

        elif extracted:
            subscription_type = extracted.get('subscription_type')
            if subscription_type:
                subscription_type_attribute = subscription.attr.get_attribute_by_code('subscription_type')
                subscription_type_option = subscription_type_attribute.option_group.options.get(option=subscription_type)
                setattr(subscription.attr, 'subscription_type', subscription_type_option)
                for attribute_key in SUBSCRIPTION_ATTRIBUTES_VALUES(subscription)[subscription_type].keys():
                    if attribute_key == 'subscription_duration_unit':
                        duration_unit_attribute = subscription.attr.get_attribute_by_code('subscription_duration_unit')
                        duration_unit_option = duration_unit_attribute.option_group.options.get(option=extracted.get(attribute_key))
                        setattr(subscription.attr, attribute_key, duration_unit_option)
                    else:
                        setattr(subscription.attr, attribute_key, extracted.get(attribute_key))

        else:
            subscription_type = choice(subscription.attr.get_attribute_by_code('subscription_type').option_group.options.all())
            setattr(subscription.attr, 'subscription_type', subscription_type)
            for attribute_key, attribute_value in SUBSCRIPTION_ATTRIBUTES_VALUES(subscription)[subscription_type.option].items():
                setattr(subscription.attr, attribute_key, attribute_value)

        setattr(subscription.attr, 'subscription_status', kwargs.get('subscription_status', subscription.attr.subscription_status))
        subscription.attr.save()


class SubscriptionConditionFactory(ConditionFactory):
    """
    Factory class for "SubscriptionCondition".
    """
    class Meta(object):
        model = SubscriptionCondition

    range = None
    type = ''
    value = None
    proxy_class = class_path(SubscriptionCondition)


class SubscriptionBenefitFactory(BenefitFactory):
    """
    Factory class for "SubscriptionBenefit".
    """
    range = None
    type = ''
    value = 100
    proxy_class = class_path(SubscriptionBenefit)


class SubscriptionOfferFactory(ConditionalOfferFactory):
    """
    Factory class for Subscription Conditional offer.
    """
    benefit = SubFactory(SubscriptionBenefitFactory)
    condition = SubFactory(SubscriptionConditionFactory)
    offer_type = ConditionalOffer.SITE
    status = ConditionalOffer.OPEN


class BasketAttributeFactory(DjangoModelFactory):
    """
    Factory class for "BasketAttribute".
    """
    class Meta(object):
        model = BasketAttribute

    basket = SubFactory(Basket)
    attribute_type = SubFactory(BasketAttributeType)
    value_text = FuzzyText()
