from logging import getLogger
from django.conf import settings
from django.contrib.auth import logout
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin

from ecommerce.core.models import SiteConfiguration
from ecommerce.extensions.edly_ecommerce_app.constants import DEACTIVATED, TRIAL_EXPIRED
from ecommerce.extensions.edly_ecommerce_app.helpers import user_has_edly_organization_access

logger = getLogger(__name__)


class SettingsOverrideMiddleware(MiddlewareMixin):
    """
    Django middleware to override django settings from site configuration.
    """

    def process_request(self, request):
        """
        Override django settings from django site configuration.
        """
        current_site = get_current_site(request)
        try:
            current_site_configuration = current_site.siteconfiguration
        except SiteConfiguration.DoesNotExist:
            logger.warning('Site (%s) has no related site configuration.', current_site)
            return None

        if current_site_configuration:
            django_settings_override_values = current_site_configuration.get_edly_configuration_value('DJANGO_SETTINGS_OVERRIDE', None)
            if django_settings_override_values:
                for config_key, config_value in django_settings_override_values.items():
                    current_value = getattr(settings, config_key, None)
                    if _should_extend_config(current_value, config_value):
                        current_value.extend(config_value)
                        setattr(settings, config_key, current_value)
                    else:
                        setattr(settings, config_key, config_value)
            else:
                logger.warning('Site configuration for site (%s) has no django settings overrides.', current_site)


class EdlyOrganizationAccessMiddleware(MiddlewareMixin):
    """
    Django middleware to validate edly user organization access based on request.
    """

    def process_request(self, request):
        """
        Validate logged in user's access based on request site and its linked edx organization.
        """
        if request.user.is_superuser or request.user.is_staff:
            return

        current_site = get_current_site(request)
        try:
            current_site_configuration = current_site.siteconfiguration
        except SiteConfiguration.DoesNotExist:
            current_site_configuration = None

        if current_site_configuration:
            django_override_settings = current_site_configuration.get_edly_configuration_value('DJANGO_SETTINGS_OVERRIDE', {})
            if django_override_settings.get('CURRENT_PLAN') == DEACTIVATED and \
                    not _is_logged_in_path(request.path) and request.user.is_authenticated:
                redirect_url = current_site_configuration.edly_client_theme_branding_settings.get('PANEL_NOTIFICATIONS_BASE_URL')
                if not redirect_url.endswith('/'):
                    redirect_url += '/'

                return HttpResponseRedirect(redirect_url)

        if django_override_settings.get('CURRENT_PLAN') == TRIAL_EXPIRED and not _is_logged_in_path(request.path):
                redirect_url = getattr(settings, 'EXPIRE_REDIRECT_URL')
                return HttpResponseRedirect(redirect_url)

        if request.user.is_authenticated and not user_has_edly_organization_access(request):
            logger.exception('Edly user %s has no access for site %s.' % (request.user.email, request.site))
            if 'logout' not in request.path:
                return HttpResponseRedirect(reverse('logout'))


def _should_extend_config(current_value, new_value):
    """
    Check if middleware should extend config value or update it.
    """
    return isinstance(current_value, (list, tuple)) and isinstance(new_value, (list, tuple))


def _is_logged_in_path(path):
    return '/login' in path
