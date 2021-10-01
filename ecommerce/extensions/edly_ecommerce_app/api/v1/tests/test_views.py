"""
Unit tests for API v1 views.
"""
import json

import pytest
from django.contrib.sites.models import Site
from django.test.client import Client
from django.urls import reverse
from rest_framework import status

from ecommerce.extensions.edly_ecommerce_app.api.v1.constants import (
    CLIENT_SITE_SETUP_FIELDS,
    EDLY_PANEL_WORKER_USER,
    ERROR_MESSAGES,
)
from ecommerce.extensions.edly_ecommerce_app.tests.factories import SiteThemeFactory
from ecommerce.extensions.partner.models import Partner
from ecommerce.tests.testcases import TestCase

pytestmark = pytest.mark.django_db


class SiteThemesActionsView(TestCase):
    """
    Unit tests for site themes configurations.
    """

    def setUp(self):
        """
        Prepare environment for tests.
        """
        super(SiteThemesActionsView, self).setUp()
        user = self.create_user()
        self.site_theme = SiteThemeFactory()
        self.client = Client()
        self.client.login(username=user.username, password=self.password)
        self.site_themes_url = reverse('edly_ecommerce_api:site_themes')

    def test_without_authentication(self):
        """
        Verify authentication is required when accessing the endpoint.
        """
        self.client.logout()
        response = self.client.get(self.site_themes_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_current_site_theme_info(self):
        """
        Verify response on list view.
        """
        response = self.client.get(self.site_themes_url, SERVER_NAME=self.site_theme.site.domain, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.json()[0]['site__name'] == self.site_theme.site.domain

    def test_update_current_site_theme(self):
        """
        Test that ecommerce users can update site theme.
        """
        edly_theme_data = {
            'theme_dir_name': "new-theme-ecommerce"
        }
        response = self.client.post(
            self.site_themes_url,
            SERVER_NAME=self.site_theme.site.domain,
            data=json.dumps(edly_theme_data),
            content_type='application/json'
        )
        assert response.status_code == status.HTTP_200_OK

        response = self.client.get(self.site_themes_url, SERVER_NAME=self.site_theme.site.domain, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.json()[0]['theme_dir_name'] == edly_theme_data['theme_dir_name']


class CSRFTokenInfoView(TestCase):
    """
    Unit test for user csrf token.
    """

    def setUp(self):
        """
        Prepare environment for tests.
        """
        super(CSRFTokenInfoView, self).setUp()
        user = self.create_user()
        self.site_theme = SiteThemeFactory()
        self.client = Client()
        self.client.login(username=user.username, password=self.password)
        self.session_url = reverse('edly_ecommerce_api:get_csrf_token')

    def test_without_authentication(self):
        """
        Verify authentication is required when accessing the endpoint.
        """
        self.client.logout()
        response = self.client.get(self.session_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_csrf_token(self):
        """
        Verify response on list view.
        """
        response = self.client.get(self.session_url, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert 'csrf_token' in response.json()


class EdlySiteViewSet(TestCase):
    """
    Unit tests for EdlySiteViewSet viewset.
    """

    def setUp(self):
        """
        Prepare environment for tests.
        """
        super(EdlySiteViewSet, self).setUp()
        self.admin_user = self.create_user(is_staff=True, username=EDLY_PANEL_WORKER_USER)
        self.edly_sites_url = reverse('edly_ecommerce_api:edly_sites')
        self.client = Client()
        self.client.login(username=self.admin_user.username, password=self.password)
        self.request_data = dict(
            lms_site='edx.devstack.lms:18000',
            wordpress_site='edx.devstack.lms',
            payments_site='edx.devstack.lms:18130',
            discovery_site='edx.devstack.lms:18381',
            edly_slug='edly',
            session_cookie_domain='.devstack.lms',
            branding=json.dumps(dict(logo='http://edx.devstack.lms:18000/media/logo.png')),
            fonts=json.dumps(dict(base_font='Open Sans')),
            colors=json.dumps(dict(primary='#00000')),
            platform_name='Edly',
            theme_dir_name='st-lutherx-ecommerce',
            oauth2_clients=json.dumps({
                'payments-sso': {
                    'id': 'payments-sso-id',
                    'secret': 'payments-sso-secret',
                },
                'payments-backend': {
                    'id': 'payments-backend-id',
                    'secret': 'payments-backend-secret',
                },
            }),
            oscar_from_email='edly@example.com',
            panel_notification_base_url='panel.backend.edly.devstack.lms:9090',
            contact_mailing_address='edly@example.com',
            csrf_trusted_origins=['.edx.devstack.lms:18000'],
            csrf_origin_whitelist=['.edx.devstack.lms:18000'],
        )

    def test_without_authentication(self):
        """
        Verify authentication is required when accessing the endpoint.
        """
        self.client.logout()
        response = self.client.post(self.edly_sites_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_without_permission(self):
        """
        Verify panel permission is required when accessing the endpoint.
        """
        user = self.create_user()
        self.client.logout()
        self.client.login(username=user.username, password=self.password)
        response = self.client.post(self.edly_sites_url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_request_data_validation(self):
        """
        Verify validation messages in response for missing required data.
        """
        response = self.client.post(self.edly_sites_url, data={})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert set(response.json().keys()) == set(CLIENT_SITE_SETUP_FIELDS)

    def test_client_setup(self):
        """
        Verify successful client setup with correct data.
        """
        response = self.client.post(self.edly_sites_url, data=self.request_data)

        assert response.status_code == status.HTTP_200_OK
        payments_site = Site.objects.get(domain=self.request_data.get('payments_site', ''))
        assert payments_site.siteconfiguration
        assert payments_site.siteconfiguration.oauth_settings

    def test_client_setup_idempotent(self):
        """
        Test that the values are only update not created on multiple API calls.
        """
        response = self.client.post(self.edly_sites_url, data=self.request_data, format='json')

        assert response.status_code == status.HTTP_200_OK
        payments_site = Site.objects.get(domain=self.request_data.get('payments_site', ''))
        assert payments_site.siteconfiguration

        sites_count = Site.objects.all().count()
        partners_count = Partner.objects.all().count()
        old_domain = self.request_data.get('payments_site')
        self.request_data['payments_site'] = 'new.edx.devstack.lms:18130'
        self.request_data['old_domain_values'] = dict(payments_site=old_domain)
        response = self.client.post(
            self.edly_sites_url,
            data=json.dumps(self.request_data),
            content_type='application/json',
        )

        assert response.status_code == status.HTTP_200_OK
        assert Site.objects.all().count() == sites_count
        assert Partner.objects.all().count() == partners_count
