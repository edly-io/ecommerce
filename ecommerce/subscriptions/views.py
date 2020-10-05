from django.views.generic import TemplateView

from ecommerce.extensions.edly_ecommerce_app.api.v1.views import (
    StaffOrCourseCreatorOnlyMixin,
    SubscriptionEnabledMixin
)


class SubscriptionAppView(StaffOrCourseCreatorOnlyMixin, SubscriptionEnabledMixin, TemplateView):
    template_name = 'subscriptions/subscriptions_app.html'

    def get_context_data(self, **kwargs):
        context = super(SubscriptionAppView, self).get_context_data(**kwargs)
        context['admin'] = 'subscription'
        return context
