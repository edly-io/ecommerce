"""
Unit tests for subscription benefit.
"""
from ecommerce.extensions.test import mixins
from ecommerce.subscriptions.api.v2.tests.factories import SubscriptionBenefitFactory
from ecommerce.tests.testcases import TestCase


class SubscriptionBenefitTests(mixins.BenefitTestMixin, TestCase):
    """
    Unit tests for "SubscriptionBenefit".
    """
    factory_class = SubscriptionBenefitFactory
    name_format = '{value}% subscription discount'
