"""
Exceptions used by the Subscription app.
"""


class SubscriptionNotBuyableException(Exception):
    """
    Exception for user if he already has an active subscription or the subscription is inactive.
    """
    pass
