from django.conf import settings

import jwt
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from opaque_keys.edx.keys import CourseKey


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


def get_edx_org_from_edly_cookie(encoded_cookie_data):
    """
    Returns "edx-org" value from the "edly-user-info" cookie.

    Arguments:
        encoded_cookie_data (dict): Edly user info cookie JWT encoded string.

    Returns:
        string
    """

    if not encoded_cookie_data:
        return ''

    decoded_cookie_data = decode_edly_user_info_cookie(encoded_cookie_data)
    return decoded_cookie_data.get('edx-org', None)


def is_valid_site_course(course_id, request):
    """
    Validate course ID with "edly-user-info" cookie and partner.

    Arguments:
        course_id (string): Course ID string.
        request (WSGI Request): Django Request object.

    Returns:
        boolean
    """
    partner_short_code = request.site.partner.short_code
    course_key = CourseKey.from_string(course_id)
    edx_org_short_name = get_edx_org_from_edly_cookie(
        request.COOKIES.get(settings.EDLY_USER_INFO_COOKIE_NAME, None)
    )
    # We assume that the "short_code" value of ECOM site partner will always
    # be the same as "short_name" value of its related edx organization in LMS
    if edx_org_short_name and course_key.org == edx_org_short_name and course_key.org == partner_short_code:
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
    edx_org_short_name = get_edx_org_from_edly_cookie(edly_user_info_cookie)

    return partner_short_code == edx_org_short_name

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
