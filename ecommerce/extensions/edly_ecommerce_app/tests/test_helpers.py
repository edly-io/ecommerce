from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import RequestFactory

from factory.fuzzy import FuzzyText
import jwt

from ecommerce.courses.tests.factories import CourseFactory
from ecommerce.extensions.edly_ecommerce_app.tests.factories import SiteFactory
from ecommerce.extensions.edly_ecommerce_app.helpers import (
    decode_edly_user_info_cookie,
    encode_edly_user_info_cookie,
    get_edx_org_from_edly_cookie,
    is_valid_site_course,
    user_is_course_creator,
)
from ecommerce.tests.factories import SiteConfigurationFactory
from ecommerce.tests.testcases import TestCase


class EdlyAppHelperMethodsTests(TestCase):
    """
    Unit tests for helper methods.
    """

    def setUp(self):
        super(EdlyAppHelperMethodsTests, self).setUp()
        self.request = RequestFactory().get('/')
        self.request.site = self.site
        self.course = CourseFactory(site=self.site, id=FuzzyText(prefix='course-v1:edx+course+'))
        self.test_edly_user_info_cookie_data = {
            'edly-org': 'edly',
            'edly-sub-org': 'cloud',
            'edx-org': 'edx',
            'is_course_creator': False,
        }

    def _set_edly_user_info_cookie(self):
        self.request.COOKIES[settings.EDLY_USER_INFO_COOKIE_NAME] = encode_edly_user_info_cookie(self.test_edly_user_info_cookie_data)

    def test_encode_edly_user_info_cookie(self):
        """
        Test that "encode_edly_user_info_cookie" method encodes data correctly.
        """
        actual_encoded_string = encode_edly_user_info_cookie(self.test_edly_user_info_cookie_data)
        expected_encoded_string = jwt.encode(
            self.test_edly_user_info_cookie_data, settings.EDLY_COOKIE_SECRET_KEY,
            algorithm=settings.EDLY_JWT_ALGORITHM
        )
        assert actual_encoded_string == expected_encoded_string

    def test_decode_edly_user_info_cookie(self):
        """
        Test that "decode_edly_user_info_cookie" method decodes data correctly.
        """
        encoded_data = jwt.encode(
            self.test_edly_user_info_cookie_data,
            settings.EDLY_COOKIE_SECRET_KEY,
            algorithm=settings.EDLY_JWT_ALGORITHM
        )
        decoded_edly_user_info_cookie_data = decode_edly_user_info_cookie(encoded_data)
        assert self.test_edly_user_info_cookie_data == decoded_edly_user_info_cookie_data

    def test_get_edly_sub_org_from_cookie(self):
        """
        Test that "get_edx_org_from_cookie" method returns edx-org short name correctly.
        """
        edx_org_short_name = self.test_edly_user_info_cookie_data.get('edx-org')
        edly_user_info_cookie_data = encode_edly_user_info_cookie(self.test_edly_user_info_cookie_data)
        assert edx_org_short_name == get_edx_org_from_edly_cookie(edly_user_info_cookie_data)

    def test_course_id_validates_false_if_edly_user_info_cookie_is_not_present(self):
        """
        Test that "is_valid_site_course" method validates false.

        Test that course ID validates as false if "edly-user-info" cookie is not present.
        """
        assert not is_valid_site_course(self.course.id, self.request)

    def test_course_id_validates_false_if_partner_short_code_mismatches_edx_org_short_name(self):
        """
        Test that "is_valid_site_course" method validates false.

        Test that course ID validates as false if partner short code doesn't match edx-org short name.
        """
        self._set_edly_user_info_cookie()
        self.request.site.partner.short_code = 'random'
        assert not is_valid_site_course(self.course.id, self.request)

    def test_course_id_validates_true(self):
        """
        Test that "is_valid_site_course" method validates true.

        Test that course ID validates as true if course ID matches with partner short code and edx-org
        short name.
        """
        self._set_edly_user_info_cookie()
        assert is_valid_site_course(self.course.id, self.request)

    def test_user_is_course_creator_works(self):
        """
        Test that "user_is_course_creator" method returns correct value.
        """
        self._set_edly_user_info_cookie()
        assert self.test_edly_user_info_cookie_data.get('is_course_creator') == user_is_course_creator(self.request)

    def test_clean_django_settings_override_for_disallowed_settings(self):
        """
        Test disallowed settings raise correct validation error.
        """
        default_settings = {
            key: getattr(settings, key, None) for key in settings.ALLOWED_DJANGO_SETTINGS_OVERRIDE
        }
        dissallowed_test_settings = dict(default_settings, HELLO='world')
        expected_error_message = 'Django settings override(s) "HELLO" is/are not allowed to be overridden.'

        with self.assertRaisesMessage(ValidationError, expected_error_message):
            site_configuration = SiteConfigurationFactory(
                site=SiteFactory(),
                edly_client_theme_branding_settings={
                    'DJANGO_SETTINGS_OVERRIDE': dissallowed_test_settings
                }
            )
            site_configuration.clean()

    def test_clean_django_settings_override_for_missing_settings(self):
        """
        Test missing settings raise correct validation error.
        """
        default_settings = {
            key: getattr(settings, key, None) for key in settings.ALLOWED_DJANGO_SETTINGS_OVERRIDE
        }
        missing_test_settings = default_settings.copy()
        missing_test_settings.pop('LANGUAGE_CODE')
        expected_error_message = 'Django settings override(s) "LANGUAGE_CODE" is/are missing.'

        with self.assertRaisesMessage(ValidationError, expected_error_message):
            site_configuration = SiteConfigurationFactory(
                site=SiteFactory(),
                edly_client_theme_branding_settings={
                    'DJANGO_SETTINGS_OVERRIDE': missing_test_settings
                }
            )
            site_configuration.clean()
