"""
Subscription product mixins.
"""
from oscar.test.factories import (
    AttributeOptionFactory,
    AttributeOptionGroupFactory,
    CategoryFactory,
    ProductAttributeFactory,
    ProductAttributeValueFactory,
    ProductCategoryFactory,
    ProductClassFactory,
    ProductFactory,
)
from oscar.core.loading import get_model

from ecommerce.core.constants import SUBSCRIPTION_CATEGORY_NAME, SUBSCRIPTION_PRODUCT_CLASS_NAME
from ecommerce.subscriptions.api.v2.tests.constants import SUBSCRIPTION_DURATION_UNIT_OPTIONS, SUBSCRIPTION_TYPES
from ecommerce.subscriptions.api.v2.tests.factories import SubscriptionFactory

Category = get_model('catalogue', 'Category')
ProductAttribute = get_model('catalogue', 'ProductAttribute')


class SubscriptionProductMixin(object):
    """
    Mixin to provide a method to create a subscription for tests.

    This mixin provides a method that creates a subscription product and sets up
    all required attributes and relevant class instances.
    """
    SUBSRIPTION_ATTRIBUTES = [
        {
            'name': 'Number of Courses',
            'code': 'subscription_number_of_courses',
            'type': ProductAttribute.INTEGER,
        },
        {
            'name': 'Subscription Actual Price',
            'code': 'subscription_actual_price',
            'type': ProductAttribute.FLOAT,
        },
        {
            'name': 'Subscription Display Order',
            'code': 'subscription_display_order',
            'type': ProductAttribute.INTEGER,
        },
        {
            'name': 'Subscription Duration unit',
            'code': 'subscription_duration_unit',
            'type': ProductAttribute.OPTION,
        },
        {
            'name': 'Subscription Duration value',
            'code': 'subscription_duration_value',
            'type': ProductAttribute.INTEGER,
        },
        {
            'name': 'Subscription Price',
            'code': 'subscription_price',
            'type': ProductAttribute.FLOAT,
        },
        {
            'name': 'Subscription Status',
            'code': 'subscription_status',
            'type': ProductAttribute.BOOLEAN,
        },
        {
            'name': 'Subscription Type',
            'code': 'subscription_type',
            'type': ProductAttribute.OPTION,
        },
    ]
    SUBSCRIPTION_DURATION_UNIT_GROUP_NAME = 'Subscription Duration Units'
    SUBSCRIPTION_TYPE_GROUP_NAME = 'Subscription Access Types'

    def _create_subscription_type_attribute_option_group(self):
        """
        Private method to create subscription type attribute group.
        """
        subscription_type_option_group = AttributeOptionGroupFactory(name=self.SUBSCRIPTION_TYPE_GROUP_NAME)
        for option in SUBSCRIPTION_TYPES:
            AttributeOptionFactory(option=option, group=subscription_type_option_group)

        return subscription_type_option_group

    def _create_subscription_duration_unit_attribute_option_group(self):
        """
        Private method to create subscription duration unit attribute group.
        """
        duration_unit_option_group = AttributeOptionGroupFactory(name=self.SUBSCRIPTION_DURATION_UNIT_GROUP_NAME)
        for option in SUBSCRIPTION_DURATION_UNIT_OPTIONS:
            AttributeOptionFactory(option=option, group=duration_unit_option_group)

        return duration_unit_option_group

    def _create_subscription_product_class(self):
        """
        Private method to set up subscription product class.

        Creates the subscription class, sets all of subscription attributes and attribute option groups.
        """
        subscription_product_class = ProductClassFactory(
            name=SUBSCRIPTION_PRODUCT_CLASS_NAME,
            requires_shipping=False,
            track_stock=False
        )
        for attribute in self.SUBSRIPTION_ATTRIBUTES:
            product_attribute = ProductAttributeFactory(
                name=attribute['name'],
                code=attribute['code'],
                type=attribute['type'],
                product_class=subscription_product_class,
            )

            if product_attribute.code == 'subscription_type':
                product_attribute.option_group = self._create_subscription_type_attribute_option_group()

            if product_attribute.code == 'subscription_duration_unit':
                product_attribute.option_group = self._create_subscription_duration_unit_attribute_option_group()

            product_attribute.save()

        return subscription_product_class

    def create_subscription(self, attributes=None, subscription_type=None, subscription_status=True, **kwargs):
        """
        Public method to create a dummy subscription.

        This method creates a subscription with the given parameters (type, status etc.) as well as the
        subscription category and subscription product category factory.

        Arguments:
            attributes (dict): Dict of subscription attributes to create a custom subscription
            subscription_type (str): Subscription type string to create a specific type of subscription
            subscription_status (bool): Subscription type to set for the subscription
            **kwargs: Additional kwargs e.g. stockrecord partner to set for the subscription

        Returns:
            Product: A dummy subscription product with all relevant product attributes set
        """
        Category.objects.all().delete()
        if subscription_type not in SUBSCRIPTION_TYPES:
            subscription_type = None

        subscription_product_class = self._create_subscription_product_class()
        subscription_category = CategoryFactory(
            name=SUBSCRIPTION_CATEGORY_NAME,
        )
        subscription = SubscriptionFactory(
            product_class=subscription_product_class,
            product_attributes=attributes,
            product_attributes__subscription_type=subscription_type,
            product_attributes__subscription_status=subscription_status,
            **kwargs
        )
        ProductCategoryFactory(
            product=subscription,
            category=subscription_category
        )

        return subscription
