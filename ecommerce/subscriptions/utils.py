import logging
from datetime import date

from dateutil.relativedelta import relativedelta
from django.conf import settings
from edx_django_utils.cache import TieredCache
from oscar.core.loading import get_model
from requests.exceptions import ConnectionError, Timeout
from slumber.exceptions import SlumberBaseException

from ecommerce.core.url_utils import get_lms_url
from ecommerce.core.utils import get_cache_key

logger = logging.getLogger(__name__)

SUBSCRIPTION_RESOURCE_NAME = 'subscriptions'
SUBSCRIPTION_ATTRIBUTE_TYPE = 'subscription'

BasketAttribute = get_model('basket', 'BasketAttribute')
BasketAttributeType = get_model('basket', 'BasketAttributeType')


def get_lms_resource_for_user(user, site, endpoint, resource_name=None, query_dict=dict()):
    """
    Get data for a user from an LMS endpoint.
    """
    cache_key = get_cache_key(
        site_domain=site.domain,
        resource=resource_name,
        username=user.username,
    )
    data_list_cached_response = TieredCache.get_cached_response(cache_key)
    if data_list_cached_response.is_found:
        return data_list_cached_response.value

    try:
        data_list = endpoint.get(**query_dict) or []
        data_list = data_list.get('results')
        TieredCache.set_all_tiers(cache_key, data_list, settings.LMS_API_CACHE_TIMEOUT)
    except (ConnectionError, SlumberBaseException, Timeout) as exc:
        logger.error('Failed to retrieve %s : %s', resource_name, str(exc))
        data_list = []

    return data_list

def get_active_user_subscription(user, site):
    """
    Get valid user subscription for a user from LMS.
    """
    site_configuration = site.siteconfiguration
    user_subscriptions_endpoint = site_configuration.subscriptions_api_client.user_subscriptions
    query_dict = {
        'valid': 'true',
        'user': user.id,
    }
    user_subscriptions_data = get_lms_resource_for_user(
        user, site, user_subscriptions_endpoint, resource_name=SUBSCRIPTION_RESOURCE_NAME, query_dict=query_dict
    )

    return user_subscriptions_data

def subscription_is_buyable(subscription, user, site):
    """
    Check if a user already owns a valid subscription.
    """
    if not subscription.attr.subscription_status:
        return False

    active_user_subscription = get_active_user_subscription(user, site)
    return len(active_user_subscription) < 1


def basket_add_subscription_attribute(basket, request_data):
    """
    Add subscription attribute on basket, if subscription value is provided
    in the query parameter.

    Arguments:
        basket(Basket): order basket
        request_data (dict): HttpRequest data

    """
    apply_subscription = True if request_data.get(SUBSCRIPTION_ATTRIBUTE_TYPE) == 'true' else False

    subscription_attribute, __ = BasketAttributeType.objects.get_or_create(name=SUBSCRIPTION_ATTRIBUTE_TYPE)
    if apply_subscription:
        BasketAttribute.objects.get_or_create(
            basket=basket,
            attribute_type=subscription_attribute,
            value_text=apply_subscription
        )
    else:
        BasketAttribute.objects.filter(basket=basket, attribute_type=subscription_attribute).delete()

def get_subscription_from_order(order):
    """
    Get subscription from a given order if exists.
    """
    for discount in order.discounts.all():
        subscription = discount.offer.condition.subscription
        if subscription:
            return subscription.id

    return None