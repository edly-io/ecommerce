# -*- coding: utf-8 -*-
"""
Unit tests for middlewares.
"""
from testfixtures import LogCapture
from django.conf import settings
from django.contrib import auth
from django.urls import reverse

from ecommerce.core.models import SiteConfiguration
from ecommerce.extensions.edly_ecommerce_app.helpers import encode_edly_user_info_cookie
from ecommerce.extensions.edly_ecommerce_app.middleware import logger
from ecommerce.tests.factories import SiteConfigurationFactory
from ecommerce.tests.testcases import TestCase

class SettingsOverrideMiddlewareTests(TestCase):
    """
    Tests settings override middleware for sites.
    """
    def setUp(self):
        """
        Create environment for settings override middleware tests.
        """
        super(SettingsOverrideMiddlewareTests, self).setUp()
        self.dashboard_url = reverse('dashboard:index')
        self.user = self.create_user(is_superuser=True)
        self.client.login(username=self.user.username, password='test')
        self.default_settings = {
            key: getattr(settings, key, None) for key in [
                'ALLOWED_HOSTS',
                'CSRF_TRUSTED_ORIGINS',
                'EDLY_WORDPRESS_URL',
                'OSCAR_FROM_EMAIL',
                'PLATFORM_NAME',
            ]
        }

    def _assert_settings_values(self, expected_settings_values):
        """
        Checks if current settings values match expected settings values.
        """
        for config_key, expected_config_value in expected_settings_values.items():
            assert expected_config_value == getattr(settings, config_key, None)

    def test_settings_override_middleware_logs_warning_for_empty_override(self):
        """
        Tests "SettingsOverrideMiddleware" logs warning if site configuration has no django settings override values.
        """
        with LogCapture(logger.name) as logs:
            self.client.get(self.dashboard_url)
            logs.check(
                (
                    logger.name,
                    'WARNING',
                    'Site configuration for site ({site}) has no django settings overrides.'.format(site=self.request.site)
                )
            )
            self._assert_settings_values(self.default_settings)

    def test_settings_override_middleware_overrides_settings_correctly(self):
        """
        Tests "SettingsOverrideMiddleware" correctly overrides django settings.
        """
        django_override_settings = {
            'ALLOWED_HOSTS': [],
            'EDLY_WORDPRESS_URL': 'http://red.wordpress.edx.devstack.lms',
            'CSRF_TRUSTED_ORIGINS': [],
            'OSCAR_FROM_EMAIL': 'test@example.com',
            'PLATFORM_NAME': 'Test Platform',
        }
        SiteConfiguration.objects.all().delete()
        SiteConfigurationFactory(
            site=self.site,
            edly_client_theme_branding_settings={
                'DJANGO_SETTINGS_OVERRIDE': django_override_settings
            }
        )
        self._assert_settings_values(self.default_settings)
        self.client.get(self.dashboard_url)
        self._assert_settings_values(django_override_settings)


class EdlyOrganizationAccessMiddlewareTests(TestCase):
    """
    Tests Edly organization access middleware for sites.
    """
    def setUp(self):
        """
        Create environment for Edly organization access middleware tests.
        """
        super(EdlyOrganizationAccessMiddlewareTests, self).setUp()
        self.basket_url = reverse('basket:summary')
        self.user = self.create_user()
        self.client.login(username=self.user.username, password='test')
        self.test_edly_user_info_cookie_data = {
            'edly-org': 'edly',
            'edly-sub-org': 'cloud',
            'edx-org': 'edx',
        }

    def _set_edly_user_info_cookie(self):
        """
        Sets edly user info cookie on client.
        """
        self.client.cookies.load(
            {
                settings.EDLY_USER_INFO_COOKIE_NAME: encode_edly_user_info_cookie(self.test_edly_user_info_cookie_data)
            }
        )

    def test_user_with_edly_organization_access(self):
        """
        Test logged in user access based on user's linked edly sub organization.
        """
        self._set_edly_user_info_cookie()

        response = self.client.get(self.basket_url)
        assert response.status_code == 200

    def test_user_without_edly_organization_access(self):
        """
        Verify that logged in user gets redirected to logout page and valid log message response if user has no access.

        Test that logged in user gets redirected to logout page and valid log message if user has no access for
        request site's edly sub organization.
        """

        with LogCapture(logger.name) as logs:
            response = self.client.get(self.basket_url)
            self.assertRedirects(response, settings.FRONTEND_LOGOUT_URL, target_status_code=302)
            user = auth.get_user(self.client)
            assert not user.is_authenticated()

            logs.check(
                (
                    logger.name,
                    'WARNING',
                    'Site configuration for site ({site}) has no django settings overrides.'.format(site=self.site)
                ),
                (
                    logger.name,
                    'ERROR',
                    'Edly user %s has no access for site %s.' % (self.user.email, self.site)
                ),
                (
                    logger.name,
                    'WARNING',
                    'Site configuration for site ({site}) has no django settings overrides.'.format(site=self.site)
                ),
            )

    def test_super_user_has_all_sites_access(self):
        """
        Test logged in super user has access to all sites.
        """
        edly_user = self.create_user(is_superuser=True)
        self.client.logout()
        self.client.login(username=edly_user.username, password='test')

        response = self.client.get(self.basket_url)
        assert response.status_code == 200
