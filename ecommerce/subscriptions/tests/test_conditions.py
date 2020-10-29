"""
Unit tests for subscription condition.
"""
import mock
from oscar.core.loading import get_model
from oscar.test.factories import BasketFactory

from ecommerce.extensions.catalogue.tests.mixins import DiscoveryTestMixin
from ecommerce.subscriptions.api.v2.tests.factories import (
    SubscriptionConditionFactory,
    SubscriptionOfferFactory
)
from ecommerce.subscriptions.api.v2.tests.mixins import SubscriptionProductMixin
from ecommerce.subscriptions.api.v2.tests.utils import mock_user_subscription
from ecommerce.tests.factories import ProductFactory
from ecommerce.tests.testcases import TestCase

BasketAttribute = get_model('basket', 'BasketAttribute')
Product = get_model('catalogue', 'Product')
ProductClass = get_model('catalogue', 'ProductClass')

LOGGER_NAME = 'ecommerce.subscriptions.conditions'


@mock.patch('ecommerce.subscriptions.conditions.get_valid_user_subscription')
class SubscriptionConditionTests(DiscoveryTestMixin, SubscriptionProductMixin, TestCase):
    """
    Unit tests for "SubscriptionCondition".
    """

    def setUp(self):
        """
        Setup initial test data.
        """
        super(SubscriptionConditionTests, self).setUp()
        self.condition = SubscriptionConditionFactory()
        self.offer = SubscriptionOfferFactory(partner=self.partner, condition=self.condition)
        self.basket = BasketFactory(site=self.site, owner=self.create_user())
        ___, seat = self.create_course_and_seat(partner=self.partner)
        self.basket.add_product(
            seat,
            1
        )

    def test_name(self, mocked_user_subscriptions_api_response):
        """
        Verify that subscription condition is set correctly.
        """
        mocked_user_subscriptions_api_response.return_value = None
        expected = 'Basket includes a subscription'
        self.assertEqual(self.condition.name, expected)

    def test_is_satisfied_with_empty_basket(self, mocked_user_subscriptions_api_response):
        """
        Verify that subscription offer is not applied on an empty basket.
        """
        mocked_user_subscriptions_api_response.return_value = None
        self.basket.flush()
        self.assertTrue(self.basket.is_empty)
        self.assertFalse(self.condition.is_satisfied(self.offer, self.basket))

    def test_is_satisfied_without_owner(self, mocked_user_subscriptions_api_response):
        """
        Verify that subscription offer is not applied on a basket without owner.
        """
        mocked_user_subscriptions_api_response.return_value = None
        self.basket.owner = None
        self.assertFalse(self.condition.is_satisfied(self.offer, self.basket))

    def test_is_satisfied_with_different_basket_and_offer_partner(self, mocked_user_subscriptions_api_response):
        """
        Verify that subscription offer is not applied if basket and offer have different partners.
        """
        mocked_user_subscriptions_api_response.return_value = None
        self.basket.site.partner = None
        self.assertFalse(self.condition.is_satisfied(self.offer, self.basket))

    def test_is_satisfied_with_no_valid_subscription(self, mocked_user_subscriptions_api_response):
        """
        Verify that subscription offer is not applied if not valid user subscription exists for the user.
        """
        mocked_user_subscriptions_api_response.return_value = None
        self.assertFalse(self.condition.is_satisfied(self.offer, self.basket))

    def test_is_satisfied_with_valid_conditions(self, mocked_user_subscriptions_api_response):
        """
        Verify that subscription offer is applied if all the conditions are met.
        """
        mocked_user_subscriptions_api_response.return_value = mock_user_subscription()
        self.assertTrue(self.condition.is_satisfied(self.offer, self.basket))

    def test_get_applicable_lines_with_empty_basket(self, mocked_user_subscriptions_api_response):
        """
        Verify that subscription offer is not applied if basket is empty.
        """
        mocked_user_subscriptions_api_response.return_value = None
        self.basket.flush()
        self.assertEqual(self.condition.get_applicable_lines(self.offer, self.basket), [])

    def test_get_applicable_lines_without_seat_product(self, mocked_user_subscriptions_api_response):
        """
        Verify that subscription offer is not applied if basket does not contain a seat product.
        """
        mocked_user_subscriptions_api_response.return_value = None
        self.basket.flush()
        self.basket.add_product(
            ProductFactory(stockrecords__partner=self.partner),
            1
        )
        self.assertEqual(self.condition.get_applicable_lines(self.offer, self.basket), [])

    def test_get_applicable_lines_with_seat_product_without_basket_attribute(self, mocked_user_subscriptions_api_response):
        """
        Verify that subscription offer is not applied if subscription basket attribute is not set.
        """
        mocked_user_subscriptions_api_response.return_value = None
        self.assertEqual(self.condition.get_applicable_lines(self.offer, self.basket), [])

    def test_get_applicable_lines_with_seat_product_with_basket_attribute(self, mocked_user_subscriptions_api_response):
        """
        Verify that subscription offer is applied if basket contains a seat product and subscription attribute is set.
        """
        mocked_user_subscriptions_api_response.return_value = None
        with mock.patch.object(BasketAttribute.objects, 'get') as basket_attribute:
            basket_attribute.return_value = {}
            applicable_lines = [
                (line.product.stockrecords.first().price_excl_tax, line) for line in self.basket.all_lines()
            ]
            self.assertEqual(self.condition.get_applicable_lines(self.offer, self.basket), applicable_lines)
