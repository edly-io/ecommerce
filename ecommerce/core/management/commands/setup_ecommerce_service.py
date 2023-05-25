""" Management command to set up ecommerce service locally"""
import csv

from django.db import connection
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from ecommerce.theming.models import SiteTheme
from ecommerce.core.models import SiteConfiguration
from oscar.core.loading import get_model
from waffle.models import Switch


class Command(BaseCommand):
    help = 'Set up ecommerce service locally'
    domain_name = 'edx.devstack.lms:18130'

    @staticmethod
    def create_temp_username_userid():
        """create and import data to table temp_username_userid."""
        create_table_query = """
        CREATE TABLE temp_username_userid
        (
        username VARCHAR(150),
        lms_user_id INT(11),
        PRIMARY KEY(lms_user_id)
        );
        """
        csv_file_path = '/edx/app/ecommerce/ecommerce/users_data.csv'
        with open(csv_file_path, "r") as csv_file:
            csv_data = list(csv.reader(csv_file))

        with connection.cursor() as cursor:
            cursor.execute(create_table_query)
            for data in csv_data:
                cursor.execute("INSERT INTO temp_username_userid (username, lms_user_id) VALUES (%s, %s)", data)

    def setup_ecommerce_service(self):
        site, _ = Site.objects.get_or_create(name=self.domain_name, domain=self.domain_name)
        SiteTheme.objects.get_or_create(site=site, theme_dir_name='st-lutherx-ecommerce')
        partner_model = get_model('partner', 'Partner')
        partner, _ = partner_model.objects.get_or_create(name='Edly', default_site_id=site.id, short_code='Edly')
        SiteConfiguration.objects.get_or_create(
            site=site, partner=partner, lms_url_root='http://edx.devstack.lms:18000',
            payment_processors='stripe,paypal', client_side_payment_processor='stripe',
            oauth_settings={
                "SOCIAL_AUTH_EDX_OAUTH2_ISSUERS": [
                    "http://edx.devstack.lms:18000"
                ],
                "SOCIAL_AUTH_EDX_OAUTH2_KEY": "ecommerce-sso-key",
                "BACKEND_SERVICE_EDX_OAUTH2_SECRET": "ecommerce-backend-service-secret",
                "SOCIAL_AUTH_EDX_OAUTH2_SECRET": "ecommerce-sso-secret",
                "SOCIAL_AUTH_EDX_OAUTH2_PUBLIC_URL_ROOT": "http://edx.devstack.lms:18000",
                "SOCIAL_AUTH_EDX_OAUTH2_LOGOUT_URL": "http://edx.devstack.lms:18000/logout",
                "BACKEND_SERVICE_EDX_OAUTH2_KEY": "ecommerce-backend-service-key",
                "SOCIAL_AUTH_EDX_OAUTH2_URL_ROOT": "http://edx.devstack.lms:18000"
            },
            discovery_api_url='http://edx.devstack.lms:18381/api/v1/',
            edly_client_theme_branding_settings={
                "BRANDING": {
                    "logo": "https://edly-cloud-static-assets.s3.amazonaws.com/red-theme/logo.png",
                    "logo-white": "https://edly-cloud-static-assets.s3.amazonaws.com/red-theme/logo-white.png",
                    "favicon": "https://edly-cloud-static-assets.s3.amazonaws.com/red-theme/favicon.png"
                },
                "FONTS": {
                    "heading-font": "Open Sans, sans-serif",
                    "font-path": "https://fonts.googleapis.com/css?family=Open+Sans&display=swap",
                    "base-font": "Open Sans, sans-serif"
                },
                "SESSION_COOKIE_DOMAIN": ".edx.devstack.lms",
                "DJANGO_SETTINGS_OVERRIDE": {
                    "CURRENT_PLAN": "ESSENTIALS",
                    "CSRF_TRUSTED_ORIGINS": [
                        ".edx.devstack.lms",
                        "panel.edx.devstack.lms:3030"
                    ],
                    "OSCAR_DEFAULT_CURRENCY": "USD",
                    "OSCAR_DEFAULT_CURRENCY_SYMBOL": "$",
                    "CORS_ORIGIN_WHITELIST": ["https://apps.edx.devstack.lms:3030"],
                    "OSCAR_FROM_EMAIL": "<from email address>",
                    "SESSION_COOKIE_DOMAIN": ".edx.devstack.lms",
                    "LANGUAGE_CODE": "en",
                    "EDLY_WORDPRESS_URL": "http://wordpress.edx.devstack.lms/",
                    "FRONTEND_LOGOUT_URL": "http://edx.devstack.lms:18000/logout",
                    "PAYMENT_PROCESSOR_CONFIG": {
                        "red": {
                            "paypal": {
                                "mode": "SET-ME-PLEASE(sandbox,live)",
                                "client_id": "SET-ME-PLEASE",
                                "client_secret": "SET-ME-PLEASE",
                                "receipt_path": "/checkout/receipt/",
                                "cancel_checkout_path": "/checkout/cancel-checkout/",
                                "error_path": "/checkout/error/"
                            },
                            "authorizenet": {
                                "mode": "SET-ME-PLEASE(sandbox,live)",
                                "redirect_url": "SET-ME-PLEASE",
                                "cancel_checkout_path": "/checkout/cancel-checkout/",
                                "merchant_auth_name": "SET-ME-PLEASE",
                                "transaction_key": "SET-ME-PLEASE"
                            }
                        }
                    }
                },
                "PLATFORM_NAME": "http://wordpress.edx.devstack.lms/",
                "COLORS": {
                    "primary": "#dd1f25",
                    "secondary": "#dd1f25"
                },
                "EDLY_COPYRIGHT_TEXT": "Edly Copy Rights. All rights reserved for red site.",
                "PANEL_NOTIFICATIONS_BASE_URL": "http://panel.edx.devstack.lms:9999/",
                "CONTACT_MAILING_ADDRESS": "Edly 25 Mohlanwal Road, Westwood Colony Lahore, Punjab 54000",
                "SERVICES_NOTIFICATIONS_COOKIE_EXPIRY": "900",
                "GTM_ID": "GTM-M69F9BL",
                "DISABLE_PAID_COURSE_MODES": False
            }
        )

        Switch.objects.get_or_create(name='enable_non_edly_cloud_options_switch', active=True)
        Switch.objects.get_or_create(name='payment_processor_active_authorizenet', active=True)
        Switch.objects.get_or_create(name='ENABLE_NOTIFICATIONS', active=True)
        Switch.objects.get_or_create(name='verify_student_disable_account_activation_requirement', active=True)

    def handle(self, *args, **options):
        """Set up ecommerce service locally"""
        self.create_temp_username_userid()
        self.setup_ecommerce_service()
