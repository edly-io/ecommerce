"""Devstack settings"""

from corsheaders.defaults import default_headers as corsheaders_default_headers

from ecommerce.settings.production import *

# noinspection PyUnresolvedReferences
from ecommerce.settings._debug_toolbar import *  # isort:skip

DEBUG = True
INTERNAL_IPS = ['127.0.0.1']
ENABLE_AUTO_AUTH = True

# The django server cannot handle https calls
PROTOCOL = 'http'

# Docker does not support the syslog socket at /dev/log. Rely on the console.
LOGGING['handlers']['local'] = {
    'class': 'logging.NullHandler',
}

SOCIAL_AUTH_REDIRECT_IS_HTTPS = False
SESSION_COOKIE_SECURE = False

# Allow live changes to JS and CSS
COMPRESS_OFFLINE = False
COMPRESS_ENABLED = False

JWT_AUTH.update({
    'JWT_ISSUER': 'http://localhost:18000/oauth2',
    'JWT_ISSUERS': [{
        'AUDIENCE': 'lms-key',
        'ISSUER': 'http://localhost:18000/oauth2',
        'SECRET_KEY': 'lms-secret',
    }],
    # Must match public signing key used in LMS.
    'JWT_PUBLIC_SIGNING_JWK_SET': (
        '{"keys": [{"kid": "devstack_key", "e": "AQAB", "kty": "RSA", "n": "smKFSYowG6nNUAdeqH1jQQnH1PmIHphzBmwJ5vRf1vu'
        '48BUI5VcVtUWIPqzRK_LDSlZYh9D0YFL0ZTxIrlb6Tn3Xz7pYvpIAeYuQv3_H5p8tbz7Fb8r63c1828wXPITVTv8f7oxx5W3lFFgpFAyYMmROC'
        '4Ee9qG5T38LFe8_oAuFCEntimWxN9F3P-FJQy43TL7wG54WodgiM0EgzkeLr5K6cDnyckWjTuZbWI-4ffcTgTZsL_Kq1owa_J2ngEfxMCObnzG'
        'y5ZLcTUomo4rZLjghVpq6KZxfS6I1Vz79ZsMVUWEdXOYePCKKsrQG20ogQEkmTf9FT_SouC6jPcHLXw"}]}'
    ),
})

CORS_ORIGIN_WHITELIST = (
    'http://localhost:1991',
    'http://localhost:1996',
    'http://localhost:1998',
    'http://localhost:8734',
)
CORS_ALLOW_HEADERS = corsheaders_default_headers + (
    'use-jwt-cookie',
)
CORS_ALLOW_CREDENTIALS = True

# List of enterprise customer uuids to exclude from transition to use of enterprise-catalog
ENTERPRISE_CUSTOMERS_EXCLUDED_FROM_CATALOG = ()
ENTERPRISE_CATALOG_API_URL = urljoin(ENTERPRISE_CATALOG_SERVICE_URL, 'api/v1/')

# PAYMENT PROCESSING
PAYMENT_PROCESSOR_CONFIG = {
    'edx': {
        'cybersource': {
            'merchant_id': 'edx_org',
            'transaction_key': '2iJRV1OoAiMxSsFRQfkmdeqYKzwV76R5AY7vs/zKCQf2Dy0gYsno6sEizavo9rz29kcq/s2F+nGP0DrNNwDXyAxI3FW77HY+0jAssnXwd8cW1Pt5aEBcQvnOQ4i9nbN2mr1XJ+MthRbNodz1FgLFuTiZenpjFq1DFmQwFi2u7V1ItQrmG19kvnpk1++mZ8Dx7s4GdN8jxdvesNGoKo7E05X6LZTHdUCP3rfq/1Nn4RDoPvxtv9UMe77yxtUF8LVJ8clAl4VyW+6uhmgfIWninfQiESR0HQ++cNJS1EXHjwNyuDEdEALKxAwgUu4DQpFbTD1bcRRm4VrnDr6MsA8NaA==',
            'soap_api_url': 'https://ics2wstest.ic3.com/commerce/1.x/transactionProcessor/CyberSourceTransaction_1.166.wsdl',
            'cancel_checkout_path': PAYMENT_PROCESSOR_CANCEL_PATH,
            'send_level_2_3_details': True,
            'sop_profile_id': '00D31C4B-4E8F-4E9F-A6B9-1DB8C7C86223',
            'sop_access_key': '014cb974072f3edd9d5d04eb46c35fe6',
            'sop_secret_key': '38d0c4ca3c0a49a186dbded91f523a9435ef86ddf0e8434196e5974a4ae997c40e35f6963bae468b9e34652bdc0b289fe180512fffa841ccb4ec357a1daf8cd048dec47262a64401b1c1f38e80c1cf65bf719dfd579b40bd8f7322550a270bf3c33c8aebd64f48089101cab36234426e60d0879ab7284b0dae90780bf2c4d2d9',
            'sop_payment_page_url': 'https://testsecureacceptance.cybersource.com/silent/pay',
            'flex_shared_secret_key_id': 'd2df1f49-dffa-4814-8da2-2751a62b79a6',
            'flex_shared_secret_key': 'c9QEORcKDT7u27zLtuy2S0T/HfKo8gl+JnCy6OHtm9Q=',
        },
        'cybersource-rest': {
            'merchant_id': 'edx_org',
            'transaction_key': '2iJRV1OoAiMxSsFRQfkmdeqYKzwV76R5AY7vs/zKCQf2Dy0gYsno6sEizavo9rz29kcq/s2F+nGP0DrNNwDXyAxI3FW77HY+0jAssnXwd8cW1Pt5aEBcQvnOQ4i9nbN2mr1XJ+MthRbNodz1FgLFuTiZenpjFq1DFmQwFi2u7V1ItQrmG19kvnpk1++mZ8Dx7s4GdN8jxdvesNGoKo7E05X6LZTHdUCP3rfq/1Nn4RDoPvxtv9UMe77yxtUF8LVJ8clAl4VyW+6uhmgfIWninfQiESR0HQ++cNJS1EXHjwNyuDEdEALKxAwgUu4DQpFbTD1bcRRm4VrnDr6MsA8NaA==',
            'soap_api_url': 'https://ics2wstest.ic3.com/commerce/1.x/transactionProcessor/CyberSourceTransaction_1.166.wsdl',
            'cancel_checkout_path': PAYMENT_PROCESSOR_CANCEL_PATH,
            'send_level_2_3_details': True,
            'sop_profile_id': '00D31C4B-4E8F-4E9F-A6B9-1DB8C7C86223',
            'sop_access_key': '014cb974072f3edd9d5d04eb46c35fe6',
            'sop_secret_key': '38d0c4ca3c0a49a186dbded91f523a9435ef86ddf0e8434196e5974a4ae997c40e35f6963bae468b9e34652bdc0b289fe180512fffa841ccb4ec357a1daf8cd048dec47262a64401b1c1f38e80c1cf65bf719dfd579b40bd8f7322550a270bf3c33c8aebd64f48089101cab36234426e60d0879ab7284b0dae90780bf2c4d2d9',
            'sop_payment_page_url': 'https://testsecureacceptance.cybersource.com/silent/pay',
            'flex_shared_secret_key_id': 'd2df1f49-dffa-4814-8da2-2751a62b79a6',
            'flex_shared_secret_key': 'c9QEORcKDT7u27zLtuy2S0T/HfKo8gl+JnCy6OHtm9Q=',
        },
        'paypal': {
            'mode': 'sandbox',
            'client_id': 'AVcS4ZWEk7IPqaJibex3bCR0_lykVQ2BHdGz6JWVik0PKWGTOQzWMBOHRppPwFXMCPUqRsoBUDSE-ro5',
            'client_secret': 'EHNgP4mXL5mI54DQI1-EgXo6y0BDUzj5x1_8gQD0dNWSWS6pcLqlmGq8f5En6oos0z2L37a_EJ27mJ_a',
            'cancel_checkout_path': PAYMENT_PROCESSOR_CANCEL_PATH,
            'error_path': PAYMENT_PROCESSOR_ERROR_PATH,
        },
        'stripe': {
            'api_version': '2022-08-01; server_side_confirmation_beta=v1',
            'enable_telemetry': None,
            'log_level': 'debug',
            'max_network_retries': 0,
            'proxy': None,
            'publishable_key': 'SET-ME-PLEASE',
            'secret_key': 'SET-ME-PLEASE',
            'error_path': PAYMENT_PROCESSOR_ERROR_PATH,
            'cancel_checkout_path': PAYMENT_PROCESSOR_CANCEL_PATH,
            'receipt_url': PAYMENT_PROCESSOR_RECEIPT_PATH,
        },
        'authorizenet': {
            'mode': 'sandbox',
            'redirect_url': config_from_yaml.get('AUTHORIZENET_REDIRECT_URL'),
            'cancel_checkout_path': PAYMENT_PROCESSOR_CANCEL_PATH,
            'merchant_auth_name': config_from_yaml.get('AUTHORIZENET_MERCHANT_AUTH_NAME'),
            'transaction_key': config_from_yaml.get('AUTHORIZENET_TRANSACTION_KEY'),
        },
        'myfatoorah': {
            'api_token': config_from_yaml.get('MYFATOORAH_API_TOKEN'),
            # Sandbox. Live is region-specific -- see _oscar.py.
            'base_url': config_from_yaml.get('MYFATOORAH_BASE_URL', 'https://apitest.myfatoorah.com'),
            'webhook_secret': config_from_yaml.get('MYFATOORAH_WEBHOOK_SECRET'),
            'cancel_checkout_path': PAYMENT_PROCESSOR_CANCEL_PATH,
            'error_path': PAYMENT_PROCESSOR_ERROR_PATH,
        }
    },
}
# END PAYMENT PROCESSING

# Language cookie
LANGUAGE_COOKIE_NAME = 'openedx-language-preference'

# Email configurations
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'SUPPORT_EMAIL'
EMAIL_HOST_PASSWORD = 'PASSWORD'

#SAILTHRU settings
SAILTHRU_KEY = 'abc123'
SAILTHRU_SECRET = 'top_secret'

REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] + ('rest_framework.renderers.BrowsableAPIRenderer',)

#####################################################################
# Lastly, see if the developer has any local overrides.
if os.path.isfile(join(dirname(abspath(__file__)), 'private.py')):
    # noinspection PyUnresolvedReferences
    from .private import *  # pylint: disable=import-error
