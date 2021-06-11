from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import RequestFactory

from factory.fuzzy import FuzzyText
import jwt

from ecommerce.courses.tests.factories import CourseFactory
from ecommerce.extensions.edly_ecommerce_app.api.v1.constants import CLIENT_SITE_SETUP_FIELDS
from ecommerce.extensions.edly_ecommerce_app.tests.factories import SiteFactory
from ecommerce.extensions.edly_ecommerce_app.helpers import (
    decode_edly_user_info_cookie,
    DEFAULT_EDLY_COPYRIGHT_TEXT,
    DEFAULT_SERVICES_NOTIFICATIONS_COOKIE_EXPIRY,
    encode_edly_user_info_cookie,
    get_edx_org_from_edly_cookie,
    get_payment_processors_names,
    get_payments_site_configuration,
    is_valid_site_course,
    user_is_course_creator,
    validate_site_configurations,
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
        self.request_data = dict(
            lms_site='edx.devstack.lms:18000',
            wordpress_site='edx.devstack.lms',
            payments_site='edx.devstack.lms:18130',
            edly_slug='edx',
            session_cookie_domain='.devstack.lms',
            branding=dict(logo='http://edx.devstack.lms:18000/media/logo.png'),
            fonts=dict(base_font='Open Sans'),
            colors=dict(primary='#00000'),
            platform_name='Edly',
            theme_dir_name='st-lutherx-ecommerce',
            oauth2_clients={
                'payments-sso': {
                    'id': 'payments-sso-id',
                    'secret': 'payments-sso-secret',
                },
                'payments-backend': {
                    'id': 'payments-backend-id',
                    'secret': 'payments-backend-secret',
                },
            },
            oscar_from_email='edly@example.com',
            panel_notification_base_url='panel.backend.edly.devstack.lms:9090',
            contact_mailing_address='edly@example.com',
        )

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
        ).decode('utf-8')
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

    def test_validate_site_configurations(self):
        """
        Test that required site creation data is present in request data.
        """
        contact_mailing_address = self.request_data.pop('contact_mailing_address')
        validation_messages = validate_site_configurations(self.request_data)
        self.assertDictEqual(
            validation_messages, {'contact_mailing_address': '{0} is Missing'.format('contact_mailing_address'.replace('_', ' ').title())}
        )

        self.request_data['contact_mailing_address'] = contact_mailing_address
        validation_messages = validate_site_configurations(self.request_data)
        self.assertEqual(len(validation_messages), 0)

    def test_get_payments_site_configuration(self):
        """
        Test that correct payments site configuration data is returned using the request data.
        """
        expected_site_configuration = {
            'SESSION_COOKIE_DOMAIN': self.request_data.get('session_cookie_domain'),
            'PLATFORM_NAME': self.request_data.get('platform_name'),
            'GTM_ID': '',
            'EDLY_COPYRIGHT_TEXT': DEFAULT_EDLY_COPYRIGHT_TEXT,
            'CONTACT_MAILING_ADDRESS': self.request_data.get('contact_mailing_address', ''),
            'DISABLE_PAID_COURSE_MODES': self.request_data.get('disable_course_modes', False),
            'PANEL_NOTIFICATIONS_BASE_URL': self.request_data.get('panel_notification_base_url', ''),
            'SERVICES_NOTIFICATIONS_COOKIE_EXPIRY': DEFAULT_SERVICES_NOTIFICATIONS_COOKIE_EXPIRY,
            'COLORS': self.request_data.get('colors'),
            'FONTS': self.request_data.get('fonts'),
            'BRANDING': self.request_data.get('branding'),
            'DJANGO_SETTINGS_OVERRIDE': {
                'SESSION_COOKIE_DOMAIN': self.request_data.get('session_cookie_domain'),
                'OSCAR_FROM_EMAIL': self.request_data.get('oscar_from_email', ''),
                'LANGUAGE_CODE': 'en',
                'PAYMENT_PROCESSOR_CONFIG': {},
                'EDLY_WORDPRESS_URL': 'https://{0}'.format(self.request_data.get('wordpress_site')),
                'FRONTEND_LOGOUT_URL': 'https://{0}/logout'.format(self.request_data.get('lms_site')),
            }
        }
        payments_site_configuration = get_payments_site_configuration(self.request_data)
        self.assertDictEqual(payments_site_configuration, expected_site_configuration)

    def test_get_payment_processors_names(self):
        """
        Test that correct payment processors names are extracted from the payment processor configuration.
        """
        self.request_data['payment_processor_config'] = {}
        payment_processors_names = get_payment_processors_names(self.request_data)
        self.assertEqual(payment_processors_names, '')

        payment_processors_config = dict(
            edx=dict(
                stripe=dict(
                    mode='SET-ME-PLEASE(sandbox,live)',
                    client_id='SET-ME-PLEASE',
                    client_secret='SET-ME-PLEASE'
                )
            )
        )
        self.request_data['payment_processor_config'] = payment_processors_config
        payment_processors_names = get_payment_processors_names(self.request_data)
        self.assertEqual(payment_processors_names, 'stripe')
