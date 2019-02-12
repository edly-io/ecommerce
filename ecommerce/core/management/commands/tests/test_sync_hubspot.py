"""
Test the sync_hubspot management command
"""
from StringIO import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from factory.django import get_model
from mock import patch
from slumber.exceptions import HttpClientError

from ecommerce.core.management.commands.sync_hubspot import Command as sync_command
from ecommerce.extensions.test.factories import create_order
from ecommerce.tests.factories import SiteConfigurationFactory

SiteConfiguration = get_model('core', 'SiteConfiguration')


@patch.object(sync_command, '_hubspot_endpoint')
class TestSyncHubspotCommand(TestCase):
    """
    Test sync_hubspot management command.
    """

    def setUp(self):
        super(TestSyncHubspotCommand, self).setUp()
        self.hubspot_site_config = SiteConfigurationFactory.create(
            hubspot_secret_key='test_key',
        )
        self.product = None
        self.order_line = None
        self.order = self._create_order('1122', self.hubspot_site_config.site, set_up_call=True)

    def _create_order(self, order_number, site, set_up_call=False):
        """
        Creates the order with given order_number and site
        also update the order's product's title.
        """
        order = create_order(number="order-{order_number}".format(order_number=order_number), site=site)
        order_line = order.lines.first()
        product = order_line.product
        product.title = "product-title-{order_number}".format(order_number=order_number)
        product.save()
        if set_up_call:
            self.product = product
            self.order_line = order_line
        return order

    def _mocked_recent_modified_deal_endpoint(self):
        return {'results': [{'properties': {'ip__ecomm_bridge__order_number': {'value': self.order.number}}}]}

    def _mocked_sync_errors_messages_endpoint(self):
        return {'results': [
            {'objectType': 'DEAL', 'integratorObjectId': '1234', 'details': 'dummy-details-deal'},
            {'objectType': 'PRODUCT', 'integratorObjectId': '4321', 'details': 'dummy-details-product'},
        ]}

    def _get_command_output(self, is_stderr=False):
        """
        Returns the stdout output of command.
        """
        out = StringIO()
        if is_stderr:
            call_command('sync_hubspot', stderr=out)
        else:
            call_command('sync_hubspot', stdout=out)
        return out.getvalue()

    def test_with_no_hubspot_secret_keys(self, mocked_hubspot):
        """
        Test with SiteConfiguration having NOT any hubspot_secret_key
        """
        # removing keys
        SiteConfiguration.objects.update(hubspot_secret_key=None)

        # making sure there are still SiteConfigurations exists
        self.assertTrue(SiteConfiguration.objects.count() > 0)
        output = self._get_command_output()
        self.assertIn('No Hubspot enabled SiteConfiguration Found.', output)
        self.assertEqual(mocked_hubspot.call_count, 0)

    def test_first_sync_call(self, mocked_hubspot):
        """
        Test with SiteConfiguration having hubspot_secret_key and it is first hubspot sync call.
        1. Install Bridge
        2. Define settings
        3. Upsert(PRODUCT)
        4. Upsert(DEAL)
        5. Upsert(LINE ITEM)
        6. Sync-error
        """
        with patch.object(sync_command, '_get_last_synced_order', return_value=''):
            output = self._get_command_output()
            self.assertIn('It is first syncing call', output)
            self.assertEqual(mocked_hubspot.call_count, 6)

    def test_with_last_synced_order(self, mocked_hubspot):
        """
        Test with SiteConfiguration having hubspot_secret_key and there exists a last sync order.
        1. Install Bridge
        2. Define settings
        3. Upsert(PRODUCT)
        4. Upsert(DEAL)
        5. Upsert(LINE ITEM)
        6. Sync-error
        """
        with patch.object(sync_command, '_get_last_synced_order', return_value=self.order):
            self._create_order('11221', self.hubspot_site_config.site)
            output = self._get_command_output()
            self.assertIn('Pulled unsynced orders', output)
            self.assertEqual(mocked_hubspot.call_count, 6)

    def test_last_synced_order(self, mocked_hubspot):
        """
        Test when _get_last_synced_order function raises an exception.
        1. Recent Modified Deal.
        2. Sync Error.
        """
        with patch.object(sync_command, '_install_hubspot_ecommerce_bridge', return_value=True), \
                patch.object(sync_command, '_define_hubspot_ecommerce_settings', return_value=True):
            # mocked the Recent Modified Deal endpoint
            mocked_hubspot.return_value = self._mocked_recent_modified_deal_endpoint()
            output = self._get_command_output()
            self.assertIn('No data found to sync', output)
            self.assertEqual(mocked_hubspot.call_count, 2)

            with self.assertRaises(CommandError):
                # if Recent Modified Deal raises an exception
                mocked_hubspot.side_effect = HttpClientError
                output = self._get_command_output()
                # command will stop when _get_last_synced_order doesn't work properly
                self.assertEqual('', output)

    def test_install_hubspot_ecommerce_bridge(self, mocked_hubspot):
        """
        Test when _install_hubspot_ecommerce_bridge function.
        """
        with patch.object(sync_command, '_get_last_synced_order', return_value=self.order):
            output = self._get_command_output()
            self.assertIn('Successfully installed hubspot ecommerce bridge', output)
            # if _install_hubspot_ecommerce_bridge raises an exception
            mocked_hubspot.side_effect = HttpClientError
            output = self._get_command_output(is_stderr=True)
            self.assertIn('An error occurred while installing hubspot ecommerce bridge', output)

    def test_define_hubspot_ecommerce_settings(self, mocked_hubspot):
        """
        Test when _define_hubspot_ecommerce_settings function.
        """
        with patch.object(sync_command, '_install_hubspot_ecommerce_bridge', return_value=True), \
                patch.object(sync_command, '_get_last_synced_order', return_value=self.order):
            output = self._get_command_output()
            self.assertIn('Successfully defined the hubspot ecommerce settings', output)
            # if _define_hubspot_ecommerce_settings raises an exception
            mocked_hubspot.side_effect = HttpClientError
            output = self._get_command_output(is_stderr=True)
            self.assertIn('An error occurred while defining hubspot ecommerce settings', output)

    def test_sync_errors_messages_endpoint(self, mocked_hubspot):
        """
        Test when _call_sync_errors_messages_endpoint function.
        """
        with patch.object(sync_command, '_install_hubspot_ecommerce_bridge', return_value=True), \
                patch.object(sync_command, '_define_hubspot_ecommerce_settings', return_value=True), \
                patch.object(sync_command, '_sync_data'):
            mocked_response = self._mocked_sync_errors_messages_endpoint()
            mocked_hubspot.return_value = mocked_response
            output = self._get_command_output(is_stderr=True)
            self.assertIn(
                'sync-error endpoint: for {object_type} with id {id} for site {site}: {message}'.format(
                    object_type=mocked_response.get('results')[0].get('objectType'),
                    id=mocked_response.get('results')[0].get('integratorObjectId'),
                    site=self.hubspot_site_config.site.domain,
                    message=mocked_response.get('results')[0].get('details')
                ),
                output
            )

            # if _call_sync_errors_messages_endpoint raises an exception
            mocked_hubspot.side_effect = HttpClientError
            output = self._get_command_output(is_stderr=True)
            self.assertIn(
                'An error occurred while getting the error syncing message',
                output
            )
