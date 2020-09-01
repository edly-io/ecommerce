from __future__ import unicode_literals

import logging
from rest_framework import serializers
from oscar.core.loading import get_model
import waffle

from django.conf import settings
from django.db import transaction, IntegrityError
from django.utils.translation import ugettext_lazy as _

from ecommerce.core.constants import (
    ENABLE_SUBSCRIPTIONS_ON_RUNTIME_SWITCH,
    SUBSCRIPTION_CATEGORY_NAME,
    SUBSCRIPTION_PRODUCT_CLASS_NAME,
)
from ecommerce.extensions.catalogue.utils import generate_sku

logger = logging.getLogger(__name__)

Category = get_model('catalogue', 'Category')
Product = get_model('catalogue', 'Product')
ProductClass = get_model('catalogue', 'ProductClass')
ProductCategory = get_model('catalogue', 'ProductCategory')
StockRecord = get_model('partner', 'StockRecord')

SUBSCRIPTION_TYPE_ATTRIBUTES = {
    'limited-access': ['number_of_courses', 'subscription_duration_value', 'subscription_duration_unit', ],
    'full-access-courses': ['subscription_duration_value', 'subscription_duration_unit', ],
    'full-access-time-period': ['number_of_courses', ],
    'lifetime-access': [],
}
SUBSCRIPTION_GENERAL_ATTRIBUTES = ['subscription_type', 'subscription_actual_price', 'subscription_price', 'subscription_status', 'subscription_display_order']


class SubscriptionListSerializer(serializers.ModelSerializer):
    subscription_type = serializers.SerializerMethodField()
    subscription_actual_price = serializers.SerializerMethodField()
    subscription_price = serializers.SerializerMethodField()
    subscription_status = serializers.SerializerMethodField()
    display_order = serializers.SerializerMethodField()

    def get_subscription_type(self, product):
        """
        Get selected subscription type for a subscription.
        """
        return product.attr.subscription_type.option

    def get_subscription_actual_price(self, product):
        """
        Get subscription actual price for a subscription.
        """
        return product.attr.subscription_actual_price

    def get_subscription_price(self, product):
        """
        Get subscription price for a subscription.
        """
        return product.attr.subscription_price

    def get_subscription_status(self, product):
        """
        Get subscription status for a subscription.
        """
        return product.attr.subscription_status

    def get_display_order(self, product):
        """
        Get subscription's display order.
        """
        return product.attr.subscription_display_order

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'date_created', 'subscription_type', 'subscription_actual_price', 'subscription_price',
            'subscription_status', 'display_order',
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    subscription_type = serializers.SerializerMethodField()
    subscription_actual_price = serializers.SerializerMethodField()
    subscription_price = serializers.SerializerMethodField()
    subscription_status = serializers.SerializerMethodField()
    number_of_courses = serializers.SerializerMethodField()
    subscription_duration_value = serializers.SerializerMethodField()
    subscription_duration_unit = serializers.SerializerMethodField()

    def get_subscription_type(self, product):
        """
        Get subscription type.
        """
        return product.attribute_values.get(attribute__code='subscription_type').value.option

    def get_subscription_actual_price(self, product):
        """
        Get subscription actual price.
        """
        return product.attr.subscription_actual_price

    def get_subscription_price(self, product):
        """
        Get subscription price.
        """
        return product.attr.subscription_price

    def get_subscription_status(self, product):
        """
        Get subscription "Active/Inactive" status.
        """
        return product.attr.subscription_status

    def get_number_of_courses(self, product):
        """
        Get number of courses depending on the subscription type.
        """
        subscription_type = product.attribute_values.get(attribute__code='subscription_type').value.option
        if subscription_type == 'limited-access' or subscription_type == 'full-access-time-period':
            return product.attr.number_of_courses
        return None

    def get_subscription_duration_value(self, product):
        """
        Get subscription duration unit depending on the subscription type.
        """
        subscription_type = product.attribute_values.get(attribute__code='subscription_type').value.option
        if subscription_type == 'limited-access' or subscription_type == 'full-access-courses':
            return product.attr.subscription_duration_value

        return None

    def get_subscription_duration_unit(self, product):
        """
        Get subscription duration unit depending on the subscription type.
        """
        subscription_type = product.attribute_values.get(attribute__code='subscription_type').value.option
        if subscription_type == 'limited-access' or subscription_type == 'full-access-courses':
            return product.attribute_values.get(attribute__code='subscription_duration_unit').value.option

        return None

    def to_internal_value(self, obj):
        """
        Add subscription attributes to serializer's initial data.
        """
        internal_value = super(SubscriptionSerializer, self).to_internal_value(obj)
        subscription_status = True if obj.get('subscription_active_status', 'active') == 'active' else False
        internal_value.update({
            'id': obj.get('id', None),
            'subscription_type': obj.get('subscription_type', ''),
            'subscription_actual_price': obj.get('subscription_actual_price', 0.0),
            'subscription_price': obj.get('subscription_price', 0.0),
            'subscription_status': subscription_status,
            'number_of_courses': obj.get('number_of_courses', 0),
            'subscription_duration_value': obj.get('subscription_duration_value', 0),
            'subscription_duration_unit': obj.get('subscription_duration_unit', 'days'),
            'subscription_display_order': obj.get('subscription_display_order', 1),
        })

        return internal_value

    def validate(self, subscription):
        """
        Validate subscription attributes corresponding to selected subscription_type.
        """
        subscription_type = subscription.get('subscription_type')
        if not subscription_type:
            raise serializers.ValidationError(_(u'Subscription must have a subscription type.'))

        if not all(attribute in subscription for attribute in SUBSCRIPTION_TYPE_ATTRIBUTES[subscription_type]):
            raise serializers.ValidationError(_(u'Invalid attributes provided for the selected subscription type.'))

        if subscription.get('subscription_price') is None:
            raise serializers.ValidationError(_(u'Products must have a price.'))

        return subscription

    def create(self, validated_data):
        """
        Create a new subscription product and corresponding stock records.
        """
        if not waffle.switch_is_active(ENABLE_SUBSCRIPTIONS_ON_RUNTIME_SWITCH):
            message = _(
                u'Subscription was not published to LMS '
                u'because the switch [enable_subscriptions] is disabled. '
            )
            raise Exception(message)

        title = validated_data['title']
        subscription_attributes = self._get_subscription_attributes(validated_data)
        partner = self.context['partner']
        try:
            with transaction.atomic():
                product_class = ProductClass.objects.get(name=SUBSCRIPTION_PRODUCT_CLASS_NAME)
                subscription = Product.objects.create(
                    title=title,
                    course=None,
                    is_discountable=True,
                    structure=Product.STANDALONE,
                    product_class=product_class,
                )
                category = Category.objects.get(name=SUBSCRIPTION_CATEGORY_NAME)
                ProductCategory.objects.create(category=category, product=subscription)
                self._save_subscription_attributes(subscription, subscription_attributes)
                self._create_update_stockrecord(subscription, partner)
                return subscription

        except Exception as exception:
            logger.exception(exception, exception.message)
            raise

    def update(self, subscription, validated_data):
        """
        Update a subscription product.
        """
        subscription.title = validated_data['title']
        attribute_values = self._get_subscription_attributes(validated_data)
        self._save_subscription_attributes(subscription, attribute_values)
        subscription.save()
        self._create_update_stockrecord(subscription, self.context['partner'])
        return subscription

    def _get_subscription_attributes(self, subscription_data):
        """
        Get subscription attributes from subscription data from request.
        """
        subscription_type = subscription_data['subscription_type']
        subscription_attributes = {
            attribute: subscription_data[attribute]
            for attribute in SUBSCRIPTION_GENERAL_ATTRIBUTES
        }
        subscription_attributes.update({
            attribute: subscription_data[attribute]
            for attribute in SUBSCRIPTION_TYPE_ATTRIBUTES[subscription_type]
        })

        return subscription_attributes

    def _save_subscription_attributes(self, subscription, subscription_attributes):
        """
        Save subscription attributes.
        """
        for attribute_key, attribute_value in subscription_attributes.items():
            setattr(subscription.attr, attribute_key, attribute_value)
            subscription.attr.save()

    def _create_update_stockrecord(self, subscription, partner):
        """
        Create a stock record for the subscription if it doesn't already exist.
        """
        try:
            partner_sku = generate_sku(subscription, partner)
            stock_record, created = StockRecord.objects.update_or_create(
                product=subscription,
                partner=partner,
                defaults={
                    'partner_sku': partner_sku,
                    'price_excl_tax': subscription.attr.subscription_price,
                    'price_currency': settings.OSCAR_DEFAULT_CURRENCY
                }
            )
            if created:
                logger.info(
                    'Subscription product stock record with title [%s] created. ',
                    subscription.title,
                )
            else:
                logger.info(
                    'Subscription product stock record with title [%s] updated. ',
                    subscription.title,
                )

        except IntegrityError:
            raise serializers.ValidationError(
                _(u'Subscription with the title "{subscription_title}" of type "{subscription_type}" already exists.').format(
                    subscription_title=subscription.title,
                    subscription_type=subscription.attr.subscription_type
                )
            )

    class Meta:
        model = Product
        fields = (
            'id', 'title', 'date_created', 'date_updated', 'subscription_type', 'subscription_actual_price', 'subscription_price', 'subscription_status',
            'number_of_courses', 'subscription_duration_value', 'subscription_duration_unit'
        )
