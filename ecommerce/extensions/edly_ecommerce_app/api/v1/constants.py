"""
Constants for Edly Ecommerce API.
"""
from django.utils.translation import ugettext as _

ERROR_MESSAGES = {
    'SITE_THEME_DIRECTORY_MISSING': _('Site theme directory not provided.'),
    'SITE_THEME_UPDATE_SUCCESS': _('Site theme update completed.'),
    'SITE_THEME_UPDATE_FAILURE': _('Site theme update failed.'),
    'CLIENT_SITES_SETUP_SUCCESS': _('Client sites setup successful.'),
    'CLIENT_SITES_SETUP_FAILURE': _('Client sites setup failed.'),
    'DJANGO_SETTINGS_UPDATE_SUCCESS': _('Django settings updated successfully.'),
    'DJANGO_SETTINGS_UPDATE_FAILURE': _('Django settings update failed.'),
    'SITE_CONFIGURATIONS_UPDATE_SUCCESS': _('Site Configurations updated successfully.'),
    'SITE_CONFIGURATIONS_UPDATE_FAILURE': _('Site Configurations update failed.'),
}

CLIENT_SITE_SETUP_FIELDS = [
    'lms_site',
    'wordpress_site',
    'payments_site',
    'discovery_site',
    'edly_slug',
    'session_cookie_domain',
    'branding',
    'fonts',
    'colors',
    'platform_name',
    'oscar_from_email',
    'panel_notification_base_url',
    'contact_mailing_address',
    'theme_dir_name',
    'oauth2_clients',
    'csrf_trusted_origins',
    'csrf_origin_whitelist',
    'current_plan',
]

EDLY_PANEL_WORKER_USER = 'edly_panel_worker'
