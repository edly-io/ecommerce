"""
Unit tests for edly_app context_processor
"""

from django.test import RequestFactory
from ecommerce.extensions.edly_ecommerce_app.context_processor import edly_app_context
from ecommerce.tests.testcases import TestCase


class EdlyAppContextProcessorTests(TestCase):
    """
    Unit tests for Edly Context processor.
    """

    def setUp(self):
        super(EdlyAppContextProcessorTests, self).setUp()
        self.request = RequestFactory().get('/')
        self.request.site = self.site

    def test_default_edly_app_context(self):
        self.assertDictEqual(
            edly_app_context(self.request),
            {
                'session_cookie_domain': self.site_configuration.base_cookie_domain,
                'services_notifications_url': '',
                'services_notifications_cookie_expiry': 180,
                'gtm_id': None
            }
        )

    def test_custom_edly_app_context(self):
        test_config_values = {
            'PANEL_NOTIFICATIONS_BASE_URL': 'http://panel.backend.dev.edly.com:9998',
            'SERVICES_NOTIFICATIONS_COOKIE_EXPIRY': 360,
            'GTM_ID': 'GTM-XXXXXX',
        }

        site_configuration = self.request.site.siteconfiguration
        site_configuration.edly_client_theme_branding_settings = test_config_values
        site_configuration.save()

        test_panel_services_notifications_url = '{base_url}/api/v1/all_services_notifications/'.format(
            base_url=test_config_values['PANEL_NOTIFICATIONS_BASE_URL']
        )

        self.assertDictEqual(
            edly_app_context(self.request),
            {
                'session_cookie_domain': site_configuration.base_cookie_domain,
                'services_notifications_url': test_panel_services_notifications_url,
                'services_notifications_cookie_expiry': test_config_values['SERVICES_NOTIFICATIONS_COOKIE_EXPIRY'],
                'gtm_id': test_config_values['GTM_ID'],
            }
        )
