"""
Unit tests for edly_app context_processor
"""

from django.conf import settings
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
                'services_notifications_url': "",
                'session_cookie_domain': settings.SESSION_COOKIE_DOMAIN,
                'services_notifications_cookie_expiry': 180
            }
        )

    def test_custom_edly_app_context(self):
        test_config_values = {
            "PANEL_NOTIFICATIONS_BASE_URL": "http://panel.backend.dev.edly.com:9999",
            "SESSION_COOKIE_DOMAIN": ".test.com",
            "SERVICES_NOTIFICATIONS_COOKIE_EXPIRY": "360"
        }

        self.request.site.siteconfiguration.configuration_values = test_config_values
        test_panel_services_notifications_url = '{base_url}/api/v1/all_services_notifications/'.format(
            base_url=test_config_values['PANEL_NOTIFICATIONS_BASE_URL']
        )

        self.assertDictEqual(
            edly_app_context(self.request),
            {
                'services_notifications_url': test_panel_services_notifications_url,
                'session_cookie_domain': test_config_values['SESSION_COOKIE_DOMAIN'],
                'services_notifications_cookie_expiry': test_config_values['SERVICES_NOTIFICATIONS_COOKIE_EXPIRY']
            }
        )
