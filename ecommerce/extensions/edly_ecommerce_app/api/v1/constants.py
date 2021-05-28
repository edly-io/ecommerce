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
}

CLIENT_SITE_SETUP_FIELDS = [
    'lms_site',
    'wordpress_site',
    'payments_site',
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
    'oauth2_clients'
]

EDLY_PANEL_WORKER_USER = 'edly_panel_worker'
