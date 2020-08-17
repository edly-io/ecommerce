"""
HTTP endpoints for interacting with courses.
"""

import logging

from oscar.core.loading import get_model
from rest_framework import filters, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ecommerce.core.constants import SUBSCRIPTION_PRODUCT_CLASS_NAME
from ecommerce.extensions.api.filters import ProductFilter
from ecommerce.extensions.api.v2.views import NonDestroyableModelViewSet
from ecommerce.extensions.checkout.mixins import EdxOrderPlacementMixin
from ecommerce.extensions.edly_ecommerce_app.permissions import IsAdminOrCourseCreator
from ecommerce.extensions.partner.shortcuts import get_partner_for_site
from ecommerce.subscriptions.api.v2.serializers import (
    SubscriptionListSerializer,
    SubscriptionSerializer,
)

Product = get_model('catalogue', 'Product')

logger = logging.getLogger(__name__)


class SubscriptionViewSet(EdxOrderPlacementMixin, NonDestroyableModelViewSet):
    """
    Subscription viewset.
    """
    permission_classes = (IsAuthenticated, IsAdminOrCourseCreator)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = ProductFilter

    def get_queryset(self):
        site_configuration = self.request.site.siteconfiguration
        return Product.objects.filter(
            product_class__name=SUBSCRIPTION_PRODUCT_CLASS_NAME,
            stockrecords__partner=site_configuration.partner
        )

    def get_serializer_class(self):
        if self.action == 'list':
            return SubscriptionListSerializer

        return SubscriptionSerializer

    def get_serializer_context(self):
        context = super(SubscriptionViewSet, self).get_serializer_context()
        context['partner'] = get_partner_for_site(self.request)
        return context
