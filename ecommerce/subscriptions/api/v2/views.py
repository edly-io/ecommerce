"""
HTTP endpoints for interacting with courses.
"""

import logging

from django.http import HttpResponseRedirect
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from oscar.core.loading import get_model
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from ecommerce.core.constants import SUBSCRIPTION_PRODUCT_CLASS_NAME
from ecommerce.extensions.api.filters import ProductFilter
from ecommerce.extensions.api.v2.views import NonDestroyableModelViewSet
from ecommerce.extensions.edly_ecommerce_app.permissions import IsAdminOrCourseCreator
from ecommerce.extensions.partner.shortcuts import get_partner_for_site
from ecommerce.subscriptions.api.v2.serializers import SubscriptionListSerializer, SubscriptionSerializer
from ecommerce.subscriptions.api.v2.tests.constants import FULL_ACCESS_COURSES
from ecommerce.subscriptions.utils import get_valid_user_subscription

OrderLine = get_model('order', 'Line')
Product = get_model('catalogue', 'Product')

logger = logging.getLogger(__name__)


class SubscriptionViewSet(NonDestroyableModelViewSet):
    """
    Subscription viewset.
    """
    permission_classes = (AllowAny, )
    filter_backends = (DjangoFilterBackend,)
    filter_class = ProductFilter

    def get_queryset(self):
        site_configuration = self.request.site.siteconfiguration
        filter_active_param = self.request.query_params.get('filter_active', 'false')
        filter_active = True if filter_active_param == 'true' else False
        products = Product.objects.prefetch_related('stockrecords').filter(
            product_class__name=SUBSCRIPTION_PRODUCT_CLASS_NAME,
            stockrecords__partner=site_configuration.partner,
        )
        if filter_active:
            products = products.filter(attribute_values__value_boolean=filter_active)

        return products

    def get_serializer_class(self):
        if self.action == 'list':
            return SubscriptionListSerializer

        return SubscriptionSerializer

    def get_serializer_context(self):
        context = super(SubscriptionViewSet, self).get_serializer_context()
        context['partner'] = get_partner_for_site(self.request)
        return context

    @action(
        detail=False,
        permission_classes=[IsAuthenticated, IsAdminOrCourseCreator],
        methods=['post']
    )
    def toggle_course_payments(self, request, **kwargs):
        """
        View to toggle course payments.
        """
        site_configuration = request.site.siteconfiguration
        site_configuration.enable_course_payments = not site_configuration.enable_course_payments
        site_configuration.save()
        return Response(status=status.HTTP_200_OK, data={'course_payments': site_configuration.enable_course_payments})

    @action(detail=False, methods=['get'])
    def course_payments_status(self, request, **kwargs):
        """
        View to get course payments status.
        """
        site_configuration = request.site.siteconfiguration
        return Response(status=status.HTTP_200_OK, data={'course_payments': site_configuration.enable_course_payments})

    def _get_unacceptable_response_object(self, message):
        """
        Get response object for unacceptable request with status code and message.
        """
        return Response(
            status=status.HTTP_406_NOT_ACCEPTABLE,
            data={
                'error': message
            }
        )

    @action(
        detail=False,
        permission_classes=[IsAuthenticated],
        methods=['get']
    )
    def renew_subscription(self, request, **kwargs):
        """
        View to renew a subscription.
        """
        subscription_id = request.query_params.get('subscription_id')
        if not subscription_id:
            return self._get_unacceptable_response_object('Subscription ID not provided.')

        subscription = self.get_queryset().filter(id=subscription_id).first()
        if not subscription:
            return self._get_unacceptable_response_object('Subscription is inactive or does not exist.')

        requested_subscription_type = subscription.attr.subscription_type.option
        if requested_subscription_type != FULL_ACCESS_COURSES:
            return self._get_unacceptable_response_object(
                'Subscription of type {no_expiry_type} can\'t be renewed.'.format(
                    no_expiry_type=requested_subscription_type
                )
            )
        current_valid_subscription = get_valid_user_subscription(request.user, request.site)
        if current_valid_subscription:
            return self._get_unacceptable_response_object('User already has a valid subscription.')

        orders_lines = OrderLine.objects.filter(product=subscription, order__user=request.user)
        if not orders_lines:
            return self._get_unacceptable_response_object(
                'The user has not purchased the requested subscription previously.'
            )

        add_to_basket_url = '{base_url}?sku={sku}'.format(
            base_url=reverse('basket:basket-add'),
            sku=subscription.stockrecords.first().partner_sku,
        )
        return HttpResponseRedirect(add_to_basket_url)
