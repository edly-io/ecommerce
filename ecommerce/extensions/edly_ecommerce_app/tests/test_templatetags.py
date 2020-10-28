# -*- coding: utf-8 -*-

from django.template import Context, Template

from ecommerce.tests.testcases import TestCase


class EdlyExtrasTests(TestCase):

    def setUp(self):
        super(EdlyExtrasTests, self).setUp()

    def test_site_configuration_value(self):
        """
        Verify site configuration template tag returns correct value.
        """
        expected_configuration_value = 'FAKE_VALUE'
        self.site.siteconfiguration.edly_client_theme_branding_settings['FAKE_KEY'] = expected_configuration_value
        self.site.siteconfiguration.save()

        template = Template(
            "{% load edly_extras %}"
            "{% site_configuration_value \"FAKE_KEY\" %}"
        )
        context = Context({'request': self.request})
        assert template.render(context) == expected_configuration_value
