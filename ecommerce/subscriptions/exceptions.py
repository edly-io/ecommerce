"""
Exceptions used by the Subscription app.
"""


class SubscriptionNotBuyableException(Exception):
    """
    Exception for learners if they cannot purchase the subscription.

    This exception is raised when the learners already have an active
    subscription or the subscription they want to buy is inactive.
    """
    pass
