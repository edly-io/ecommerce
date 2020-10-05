import json
import logging
import requests
from requests.exceptions import ConnectionError, Timeout
from rest_framework import status

from django.conf import settings

from ecommerce.extensions.analytics.utils import audit_log, parse_tracking_context
from ecommerce.extensions.fulfillment.modules import BaseFulfillmentModule
from ecommerce.extensions.fulfillment.status import LINE
from ecommerce.subscriptions.utils import get_lms_user_subscription_api_url, get_subscription_expiration_date

logger = logging.getLogger(__name__)


class SubscriptionFulfillmentModule(BaseFulfillmentModule):
    """
    Fulfillment Module for creating a user subscription record after a subscription purchase.
    """

    def _post_to_user_subscription_api(self, data, user):
        """
        Makes a PUT request with the required data to create a user subscription.
        """
        user_subscription_api_url = get_lms_user_subscription_api_url(data['subscription_id'])
        timeout = settings.USER_SUBSCRIPTION_FULFILLMENT_TIMEOUT
        headers = {
            'Content-Type': 'application/json',
            'X-Edx-Api-Key': settings.EDX_API_KEY
        }

        __, client_id, ip = parse_tracking_context(user)

        if client_id:
            headers['X-Edx-Ga-Client-Id'] = client_id

        if ip:
            headers['X-Forwarded-For'] = ip

        return requests.put(user_subscription_api_url, data=json.dumps(data), headers=headers, timeout=timeout)

    def supports_line(self, line):
        return line.product.is_subscription_product

    def get_supported_lines(self, lines):
        """
        Return a list of lines that can be fulfilled through subscription.

        Checks each line to determine if it is a "Subscription". Subscription are fulfilled by creating a
        user subscription record in the LMS, which is the sole functionality of this module. Any Subscription product
        will be returned as a supported line.

        Arguments:
            lines (List of Lines): Order Lines, associated with purchased products in an Order.

        Returns:
            A supported list of unmodified lines associated with "Susbcription" products.
        """
        return [line for line in lines if self.supports_line(line)]

    def fulfill_product(self, order, lines, email_opt_in=False):
        """
        Fulfills the purchase of a "Subscription" by creating a user subscription record in the LMS.

        Uses the order and the lines to create relevant user subscription records on the LMS side.
        May result in an error if the User Subscription API cannot be reached, or if there is
        additional business logic errors when trying to create the user subscription record.

        Arguments:
            order (Order): The Order associated with the lines to be fulfilled. The user associated with the order
            is presumed to be the student buying the subscription.
            lines (List of Lines): Order Lines, associated with purchased products in an Order. These should only
                be "Subscription" products.
            email_opt_in (bool): Whether the user should be opted in to emails
                as part of the fulfillment. Defaults to False.

        Returns:
            The original set of lines, with new statuses set based on the success or failure of fulfillment.

        """
        logger.info("Attempting to fulfill 'Subscription' product types for order [%s]", order.number)
        api_key = getattr(settings, 'EDX_API_KEY', None)
        if not api_key:
            logger.error(
                'EDX_API_KEY must be set to use the SubscriptionFulfillmentModule'
            )
            for line in lines:
                line.set_status(LINE.FULFILLMENT_CONFIGURATION_ERROR)

            return order, lines

        for line in lines:
            subscription = line.product
            subscription_type = subscription.attr.subscription_type.option
            subscription_expiration = get_subscription_expiration_date(subscription)
            number_of_courses = subscription.attribute_values.filter(attribute__code='number_of_courses').first()
            data = {
                'user': order.user.id,
                'subscription_id': subscription.id,
                'expiration_date': str(subscription_expiration) if subscription_expiration else subscription_expiration,
                'subscription_type': subscription_type,
                'number_of_courses': number_of_courses.value if number_of_courses else None,
            }
            try:
                response = self._post_to_user_subscription_api(data, user=order.user)
                if response.status_code == status.HTTP_201_CREATED:
                    line.set_status(LINE.COMPLETE)

                    audit_log(
                        'line_fulfilled',
                        order_line_id=line.id,
                        order_number=order.number,
                        product_class=line.product.get_product_class().name,
                        user_id=order.user.id,
                    )
                else:
                    try:
                        data = response.json()
                        reason = data.get('message')
                    except Exception:  # pylint: disable=broad-except
                        reason = '(No detail provided.)'

                    logger.error(
                        'Fulfillment of line [%d] on order [%s] failed with status code [%d]: %s',
                        line.id, order.number, response.status_code, reason
                    )
                    order.notes.create(message=reason, note_type='Error')
                    line.set_status(LINE.FULFILLMENT_SERVER_ERROR)
            except ConnectionError:
                logger.error(
                    'Unable to fulfill line [%d] of order [%s] due to a network problem', line.id, order.number
                )
                order.notes.create(message='Fulfillment of order failed due to a network problem.', note_type='Error')
                line.set_status(LINE.FULFILLMENT_NETWORK_ERROR)
            except Timeout:
                logger.error(
                    'Unable to fulfill line [%d] of order [%s] due to a request time out', line.id, order.number
                )
                order.notes.create(message='Fulfillment of order failed due to a request time out.', note_type='Error')
                line.set_status(LINE.FULFILLMENT_TIMEOUT_ERROR)

        logger.info('Finished fulfilling "Subscription" product types for order [%s]', order.number)
        return order, lines

    def revoke_line(self, line):
        try:
            logger.info('Attempting to revoke fulfillment of Line [%d]...', line.id)
            audit_log(
                'line_revoked',
                order_line_id=line.id,
                order_number=line.order.number,
                product_class=line.product.get_product_class().name,
                user_id=line.order.user.id
            )

            return True
        except Exception:  # pylint: disable=broad-except
            logger.exception('Failed to revoke fulfillment of Line [%d].', line.id)

        return False

