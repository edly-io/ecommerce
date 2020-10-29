"""
Subscription utility methods.
"""
from datetime import date
from factory.fuzzy import (
    FuzzyChoice,
    FuzzyDate,
    FuzzyInteger,
)

from ecommerce.subscriptions.api.v2.tests.constants import SUBSCRIPTION_TYPES


def mock_user_subscription():
    """
    Mock LMS response for user subscription.
    """
    return {
        'subscription_id': FuzzyInteger(1, 100).fuzz(),
        'subscription_type': FuzzyChoice(SUBSCRIPTION_TYPES).fuzz(),
        'expiration_date': FuzzyDate(start_date=date.today()).fuzz().strftime('%Y-%m-%d'),
        'course_enrollments': [],
        'max_allowed_courses': FuzzyInteger(1, 10).fuzz(),
        'user': FuzzyInteger(1, 10).fuzz()
    }
