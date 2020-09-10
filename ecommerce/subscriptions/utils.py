from datetime import date
from dateutil.relativedelta import relativedelta

from ecommerce.core.url_utils import get_lms_url

NO_EXPIRY_TYPES = ['lifetime-access', 'full-access-time-period']


def get_lms_user_subscription_api_url(subscription_id=None):
    """
    Get LMS url to post user subscription data.
    """
    return get_lms_url('/api/subscriptions/v1/{}/'.format(subscription_id))

def get_subscription_expiration_date(subscription):
    """
    Calculate subscription expiry date for a given subscription.
    """
    if subscription.attr.subscription_type.option in NO_EXPIRY_TYPES:
        return None

    current_date = date.today()
    subscription_duration_unit = subscription.attr.subscription_duration_unit.option
    subscription_duration_value = subscription.attr.subscription_duration_value
    duration_to_add = {subscription_duration_unit: subscription_duration_value}
    expiry_date = current_date + relativedelta(**duration_to_add)
    return expiry_date
