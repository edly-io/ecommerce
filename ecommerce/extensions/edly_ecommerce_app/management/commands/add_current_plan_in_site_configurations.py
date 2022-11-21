"""
Command for updating "current_plan" in all site configurations.
"""
import logging

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand

from ecommerce.core.models import SiteConfiguration
from ecommerce.extensions.edly_ecommerce_app.constants import ESSENTIALS

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Update all site configurations to have default value for current_plan.
    """

    def add_arguments(self, parser):
        """
        Add arguments for values of current_plan
        """
        parser.add_argument(
            '--current_plan',
            default=ESSENTIALS,
            help='Current plan type',
        )

    def handle(self, *args, **options):
        """
        Update site configuration for current_plan.
        """
        current_plan_value = options['current_plan']
        site_configurations = SiteConfiguration.objects.all()
        for site_configuration in site_configurations:
            django_settings_override  = site_configuration.edly_client_theme_branding_settings.get(
                'DJANGO_SETTINGS_OVERRIDE', {}
            )

            django_settings_override['CURRENT_PLAN'] = current_plan_value
            site_configuration.edly_client_theme_branding_settings['DJANGO_SETTINGS_OVERRIDE'] = django_settings_override
            try:
                site_configuration.save()
            except ValidationError as exp:
                LOGGER.info('Failed to update site configuration {} due to {}', site_configuration, exp)
