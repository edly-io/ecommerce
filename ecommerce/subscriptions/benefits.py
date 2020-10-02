from django.utils.translation import ugettext_lazy as _
from oscar.apps.offer.benefits import PercentageDiscountBenefit
from oscar.core.loading import get_model

from ecommerce.extensions.offer.mixins import (
    BenefitWithoutRangeMixin,
    PercentageBenefitMixin,
)

Benefit = get_model('offer', 'Benefit')


class SubscriptionBenefit(BenefitWithoutRangeMixin, PercentageBenefitMixin,
                          PercentageDiscountBenefit):
    """
    "PercentageDiscountBenefit" without an attached range.

    The range is only used for the name and description. We would prefer not
    to deal with ranges since we rely on the condition to fully determine if
    a conditional offer is applicable to a basket.
    """

    class Meta(object):
        app_label = 'subscriptions'
        proxy = True

    @property
    def name(self):
        return _('%d%% subscription discount') % self.value
