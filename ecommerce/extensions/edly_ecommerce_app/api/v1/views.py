"""
Views for API v1.
"""

from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.http import Http404
from django.middleware import csrf
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
import waffle

from ecommerce.core.constants import ENABLE_SUBSCRIPTIONS_ON_RUNTIME_SWITCH
from ecommerce.core.models import SiteConfiguration
from ecommerce.extensions.edly_ecommerce_app.api.v1.constants import ERROR_MESSAGES
from ecommerce.extensions.edly_ecommerce_app.helpers import (
    user_is_course_creator,
    validate_site_configurations,
    get_payment_processors_names,
    get_payments_site_configuration,
)
from ecommerce.extensions.edly_ecommerce_app.permissions import CanAccessSiteCreation
from ecommerce.extensions.partner.models import Partner
from ecommerce.theming.models import SiteTheme


class SiteThemesActions(APIView):
    """
    Site Theme Configurations Retrieve/Update.
    """
    authentication_classes = (SessionAuthentication,)
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Return queryset on the basis of current site.
        """
        current_site = get_current_site(request)
        current_site_theme = SiteTheme.objects.select_related('site').filter(site=current_site).values(
            'theme_dir_name',
            'site__name'
        )
        return Response(current_site_theme)

    def post(self, request):
        theme_dir_name = request.data.get('theme_dir_name', None)

        if not theme_dir_name:
            return Response(
                {'error': ERROR_MESSAGES.get('SITE_THEME_DIRECTORY_MISSING')},
                status=status.HTTP_400_BAD_REQUEST
            )

        current_site = get_current_site(request)

        try:
            SiteTheme.objects.filter(site=current_site).update(theme_dir_name=theme_dir_name)
            return Response(
                {'success': ERROR_MESSAGES.get('SITE_THEME_UPDATE_SUCCESS')},
                status=status.HTTP_200_OK
            )
        except TypeError:
            return Response(
                {'error': ERROR_MESSAGES.get('SITE_THEME_UPDATE_FAILURE')},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserSessionInfo(APIView):
    """
    Get User Session Info
    """

    authentication_classes = (SessionAuthentication,)
    permission_classes = [IsAuthenticated]

    def get(self, request):
        csrf_token = csrf.get_token(request)
        data = {'csrf_token': csrf_token}
        return Response(data)


class StaffOrCourseCreatorOnlyMixin(object):
    """
    Makes sure only staff users and course creators can access the view.
    """

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not user_is_course_creator(request) and not request.user.is_staff:
            raise Http404

        return super(StaffOrCourseCreatorOnlyMixin, self).dispatch(request, *args, **kwargs)


class SubscriptionEnabledMixin(object):
    """
    Makes sure subscription app is visible only if subscriptions waffle switch is enabled.
    """

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not waffle.switch_is_active(ENABLE_SUBSCRIPTIONS_ON_RUNTIME_SWITCH):
            raise Http404

        return super(SubscriptionEnabledMixin, self).dispatch(request, *args, **kwargs)


class EdlySiteViewSet(APIView):
    """
    Create Default Payments Site and Site Configuration and Partner.
    """
    permission_classes = [IsAuthenticated, CanAccessSiteCreation]

    def post(self, request):
        """
        POST /api/edly_ecommerce_api/v1/edly_sites.
        """
        validations_messages = validate_site_configurations(request.data)
        if len(validations_messages) > 0:
            return Response(validations_messages, status=status.HTTP_400_BAD_REQUEST)

        try:
            self.process_client_sites_setup()
            return Response(
                {'success': ERROR_MESSAGES.get('CLIENT_SITES_SETUP_SUCCESS')},
                status=status.HTTP_200_OK
            )
        except TypeError:
            return Response(
                {'error': ERROR_MESSAGES.get('CLIENT_SITES_SETUP_FAILURE')},
                status=status.HTTP_400_BAD_REQUEST
            )

    def process_client_sites_setup(self):
        """
        Process client sites setup and update configurations.
        """
        edly_slug = self.request.data.get('edly_slug', '')
        payments_base = self.request.data.get('payments_site', '')
        theme_dir_name = self.request.data.get('theme_dir_name', 'st-lutherx-ecommerce')
        lms_url_root = '{protocol}://{lms_url_root}'.format(
            protocol=self.request.data.get('protocol', 'https'),
            lms_url_root=self.request.data.get('lms_site', '')
        )
        payments_site, __ = Site.objects.update_or_create(domain=payments_base, defaults=dict(name=payments_base))
        payments_partner, __ = Partner.objects.update_or_create(short_code=edly_slug, default_site=payments_site)
        payments_site_config, __ = SiteConfiguration.objects.update_or_create(
            site=payments_site,
            partner=payments_partner,
            defaults=dict(
                lms_url_root=lms_url_root,
                payment_processors=get_payment_processors_names(self.request.data),
                oauth_settings=self.get_oauth2_credentials(),
                edly_client_theme_branding_settings=get_payments_site_configuration(self.request.data)
            )
        )
        SiteTheme.objects.update_or_create(site=payments_site, defaults=dict(theme_dir_name=theme_dir_name))

    def get_oauth2_credentials(self):
        """
        Returns payments SSO and backend OAuth2 values.
        """
        oauth2_clients = self.request.data.get('oauth2_clients', {})
        payments_sso_values = oauth2_clients.get('payments-sso', {})
        payments_backend_values = oauth2_clients.get('payments-backend', {})
        oauth2_values = dict(
            SOCIAL_AUTH_EDX_OAUTH2_KEY=payments_sso_values.get('id', ''),
            SOCIAL_AUTH_EDX_OAUTH2_SECRET=payments_sso_values.get('secret', ''),
            BACKEND_SERVICE_EDX_OAUTH2_KEY=payments_backend_values.get('id', ''),
            BACKEND_SERVICE_EDX_OAUTH2_SECRET=payments_backend_values.get('secret', '')
        )
        return oauth2_values
