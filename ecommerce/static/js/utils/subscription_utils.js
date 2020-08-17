define([
    'underscore'
], function(
    _
) {
    'use strict';

    return {
        /**
         * Returns a subscription type text corresponding to the subscription type slug.
         *
         * @param {String} subscriptionType
         * @returns {String}
         */
        formatSubscriptionType: function(subscriptionType) {
            if (subscriptionType === 'limited-access')
                return gettext('Limited Access');
            else if (subscriptionType === 'full-access-courses')
                return gettext('Full Access (Courses)');
            else if (subscriptionType === 'full-access-time-period')
                return gettext('Full Access (Time Period)');
            else if (subscriptionType === 'lifetime-access')
                return gettext('Lifetime Access');
            return '';
        },
    }
})
