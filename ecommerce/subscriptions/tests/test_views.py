"""
Unit tests for subscription Template views.
"""
from waffle.testutils import override_switch

from django.conf import settings
from django.urls import reverse

from ecommerce.core.constants import ENABLE_SUBSCRIPTIONS_ON_RUNTIME_SWITCH
from ecommerce.tests.testcases import TestCase


class SubscriptionAppViewTests(TestCase):
    """
    Unit tests for "SubscriptionAppView".
    """
    path = reverse('subscriptions:app', args=[''])

    def _create_and_login_staff_user(self):
        """
        Setup staff user with an OAuth2 access token and log the user in.
        """
        user = self.create_user(is_staff=True)
        self.create_access_token(user)
        self.assertIsNotNone(user.access_token)
        self.client.login(username=user.username, password=self.password)

    def test_login_required(self):
        """
        Verify that users are required to login before accessing the view.
        """
        self.client.logout()
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 302)
        self.assertIn(settings.LOGIN_URL, response.url)

    def test_staff_user_required(self):
        """
        Verify the view is only accessible to staff users.
        """
        user = self.create_user(is_staff=False)
        self.client.login(username=user.username, password=self.password)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 302)

        self._create_and_login_staff_user()
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)

    @override_switch(ENABLE_SUBSCRIPTIONS_ON_RUNTIME_SWITCH, active=False)
    def test_subscriptions_switch_turned_off(self):
        """
        Verify that the view is not accessible with "ENABLE_SUBSCRIPTIONS_ON_RUNTIME_SWITCH" inactive.
        """
        self._create_and_login_staff_user()
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 404)

    @override_switch(ENABLE_SUBSCRIPTIONS_ON_RUNTIME_SWITCH, active=True)
    def test_subscriptions_switch_turned_on(self):
        """
        Verify that the view is accessible with "ENABLE_SUBSCRIPTIONS_ON_RUNTIME_SWITCH" active.
        """
        self._create_and_login_staff_user()
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)

    @override_switch(ENABLE_SUBSCRIPTIONS_ON_RUNTIME_SWITCH, active=True)
    def test_context(self):
        """
        Verify that additional context values are present.
        """
        self._create_and_login_staff_user()
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['admin'], 'subscription')
