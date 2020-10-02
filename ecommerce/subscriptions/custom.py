from oscar.core.loading import get_model

Benefit = get_model('offer', 'Benefit')
Condition = get_model('offer', 'Condition')
ConditionalOffer = get_model('offer', 'ConditionalOffer')


def class_path(klass):
    return '%s.%s' % (klass.__module__, klass.__name__)


def create_condition(condition_class, **kwargs):
    """
    Create a custom condition instance for subscription.
    """
    return Condition.objects.get_or_create(
        proxy_class=class_path(condition_class), **kwargs
    )

def create_conditional_offer(**kwargs):
    """
    Create a custom condition instance for subscription.
    """
    return ConditionalOffer.objects.get_or_create(
        status=ConditionalOffer.OPEN,
        offer_type=ConditionalOffer.SITE,
        **kwargs
    )

def create_benefit(benefit_class, **kwargs):
    """
    Create a custom benefit instance for subscription.
    """
    return Benefit.objects.get_or_create(
        proxy_class=class_path(benefit_class), **kwargs
    )
