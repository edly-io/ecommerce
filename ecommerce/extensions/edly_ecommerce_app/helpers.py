from django.conf import settings

import jwt
import json
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from ecommerce.extensions.edly_ecommerce_app.api.v1.constants import CLIENT_SITE_SETUP_FIELDS

from opaque_keys.edx.keys import CourseKey

DEFAULT_EDLY_COPYRIGHT_TEXT = _('Copy Rights. All rights reserved.')
DEFAULT_SERVICES_NOTIFICATIONS_COOKIE_EXPIRY = '900'  # value in seconds, 900 seconds = 15 minutes


def decode_edly_user_info_cookie(encoded_cookie_data):
    """
    Decode edly_user_info cookie data from JWT string.

    Arguments:
        encoded_cookie_data (dict): Edly user info cookie JWT encoded string.

    Returns:
        dict
    """
    return jwt.decode(encoded_cookie_data, settings.EDLY_COOKIE_SECRET_KEY, algorithms=[settings.EDLY_JWT_ALGORITHM])


def encode_edly_user_info_cookie(cookie_data):
    """
    Encode edly_user_info cookie data into JWT string.

    Arguments:
        cookie_data (dict): Edly user info cookie dict.

    Returns:
        string
    """
    return jwt.encode(cookie_data, settings.EDLY_COOKIE_SECRET_KEY, algorithm=settings.EDLY_JWT_ALGORITHM).decode('utf-8')


def get_edx_orgs_from_edly_cookie(encoded_cookie_data):
    """
    Returns "edx-orgs" value from the "edly-user-info" cookie.

    Arguments:
        encoded_cookie_data (dict): Edly user info cookie JWT encoded string.

    Returns:
        string
    """

    if not encoded_cookie_data:
        return ''

    decoded_cookie_data = decode_edly_user_info_cookie(encoded_cookie_data)
    return decoded_cookie_data.get('edx-orgs', None)


def is_valid_site_course(course_id, request):
    """
    Validate course ID with "edly-user-info" cookie and partner.

    Arguments:
        course_id (string): Course ID string.
        request (WSGI Request): Django Request object.

    Returns:
        boolean
    """
    course_key = CourseKey.from_string(course_id)
    edx_orgs_short_names = get_edx_orgs_from_edly_cookie(
        request.COOKIES.get(settings.EDLY_USER_INFO_COOKIE_NAME, None)
    )
    # We assume that the "short_code" value of ECOM site partner will always
    # be the same as "short_name" value of its related edx organization in LMS
    if edx_orgs_short_names and course_key.org in edx_orgs_short_names:
        return True

    return False


def user_has_edly_organization_access(request):
    """
    Check if the requested URL site is allowed for the user.

    This method checks if the partner "short_code" of requested URL site is
    same as "short_name" of edx organization. Since the partner "short_code"
    in ECOM will always be same as "short_name" of its related edx
    organization in LMS.

    Arguments:
        request: HTTP request object

    Returns:
        bool: Returns True if User has site access otherwise False.
    """
    partner_short_code = request.site.partner.short_code
    edly_user_info_cookie = request.COOKIES.get(settings.EDLY_USER_INFO_COOKIE_NAME, None)
    edx_orgs_short_names = get_edx_orgs_from_edly_cookie(edly_user_info_cookie)

    return partner_short_code in edx_orgs_short_names


def user_is_course_creator(request):
    """
    Check if the logged in user is a course creator.

    Arguments:
        request: HTTP request object

    Returns:
        bool: Returns True if User has site access otherwise False.
    """
    edly_user_info_cookie = request.COOKIES.get(settings.EDLY_USER_INFO_COOKIE_NAME, None)
    if not edly_user_info_cookie:
        return False

    decoded_cookie_data = decode_edly_user_info_cookie(edly_user_info_cookie)
    return decoded_cookie_data.get('is_course_creator', False)


def clean_django_settings_override(django_settings_override):
    """
    Enforce only allowed django settings to be overridden.
    """
    if not django_settings_override:
        return

    django_settings_override_keys = django_settings_override.keys()
    disallowed_override_keys = list(set(django_settings_override_keys) - set(settings.ALLOWED_DJANGO_SETTINGS_OVERRIDE))
    updated_override_keys = list(set(django_settings_override_keys) - set(disallowed_override_keys))
    missing_override_keys = list(set(settings.ALLOWED_DJANGO_SETTINGS_OVERRIDE) - set(updated_override_keys))

    validation_errors = []
    if disallowed_override_keys:
        disallowed_override_keys_string = ', '.join(disallowed_override_keys)
        validation_errors.append(
            ValidationError(
                _('Django settings override(s) "%(disallowed_override_keys)s" is/are not allowed to be overridden.'),
                params={'disallowed_override_keys': disallowed_override_keys_string},
            )
        )

    if missing_override_keys:
        missing_override_keys_string = ', '.join(missing_override_keys)
        validation_errors.append(
            ValidationError(
                _('Django settings override(s) "%(missing_override_keys)s" is/are missing.'),
                params={'missing_override_keys': missing_override_keys_string},
            )
        )

    if validation_errors:
        raise ValidationError(validation_errors)


def validate_site_configurations(request_data):
    """
    Identify missing required fields for client's site setup.

    Arguments:
        request_data (dict): Request data passed for site setup

    Returns:
        validation_messages (dict): Missing fields information
    """

    validation_messages = {}

    for field in CLIENT_SITE_SETUP_FIELDS:
        if not request_data.get(field, None):
            validation_messages[field] = '{0} is Missing'.format(field.replace('_', ' ').title())

    return validation_messages


def get_payments_site_configuration(request_data):
    """
    Prepare Payments Site Configurations for Client based on Request Data.

    Arguments:
        request_data (dict): Request data passed for site setup

    Returns:
        (dict): Payments Site Configuration
    """
    protocol = request_data.get('protocol', 'https')
    colors = json.loads(request_data.get('colors', "{}"))
    session_cookie_domain = request_data.get('session_cookie_domain', '')
    lms_site = request_data.get('lms_site', '')
    wordpress_site = request_data.get('wordpress_site', '')

    return {
        'SESSION_COOKIE_DOMAIN': session_cookie_domain,
        'PLATFORM_NAME': request_data.get('platform_name', ''),
        'GTM_ID': request_data.get('gtm_id', ''),
        'EDLY_COPYRIGHT_TEXT': DEFAULT_EDLY_COPYRIGHT_TEXT,
        'CONTACT_MAILING_ADDRESS': request_data.get('contact_mailing_address', ''),
        'DISABLE_PAID_COURSE_MODES': request_data.get('disable_course_modes', False),
        'PANEL_NOTIFICATIONS_BASE_URL': '{protocol}://{panel_base_domain}'.format(
            protocol=protocol,
            panel_base_domain=request_data.get('panel_notification_base_url', ''),
        ),
        'SERVICES_NOTIFICATIONS_COOKIE_EXPIRY': DEFAULT_SERVICES_NOTIFICATIONS_COOKIE_EXPIRY,
        'COLORS': colors,
        'FONTS': json.loads(request_data.get('fonts', "{}")),
        'BRANDING': json.loads(request_data.get('branding', "{}")),
        'DJANGO_SETTINGS_OVERRIDE': {
            'SESSION_COOKIE_DOMAIN': session_cookie_domain,
            'CSRF_TRUSTED_ORIGINS': request_data.get('csrf_trusted_origins', []),
            'CORS_ORIGIN_WHITELIST': request_data.get('csrf_origin_whitelist', []),
            'OSCAR_FROM_EMAIL': request_data.get('oscar_from_email', ''),
            'LANGUAGE_CODE': request_data.get('language_code', 'en'),
            'PAYMENT_PROCESSOR_CONFIG': json.loads(request_data.get('payment_processor_config', "{}")),
            'EDLY_WORDPRESS_URL': '{protocol}://{marketing_url_domain}'.format(
                protocol=protocol,
                marketing_url_domain=wordpress_site,
            ),
            'FRONTEND_LOGOUT_URL': '{protocol}://{lms_root_domain}/logout'.format(
                protocol=protocol,
                lms_root_domain=lms_site,
            ),
        }
    }


def get_payment_processors_names(request_data):
    """
    Returns comma-separated string of payment processor names provided in POST data.

    Arguments:
        request_data (dict): Request data passed for site setup

    Returns:
        (str): Payment Processors Comma-separated List
    """
    payment_processors = json.loads(request_data.get('payment_processor_config', "{}"))
    edly_slug = request_data.get('edly_slug', '')
    return ','.join(payment_processors.get(edly_slug, {}).keys())


def validate_django_settings_overrides(request_data):
    """
    Validates allowed django settings override for ecommerce.

    Arguments:
        request_data (dict): Request data passed for site config.

    Returns:
        validation_messages (list): Invalid fields information.
    """

    validation_messages = []

    for field in request_data.keys():
        if not field in getattr(settings, 'ALLOWED_DJANGO_SETTINGS_OVERRIDE', []):
            validation_messages.append(dict(field='{} is not allowed in lms django overrides'.format(field)))

    return validation_messages
