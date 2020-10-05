define([
	'backbone',
	'js-cookie',
    'underscore'
], function(
    Backbone,
    Cookies,
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

        setCoursePaymentsButtonText: function() {
			Backbone.ajax({
				type: 'GET',
				headers: {
					'X-CSRFToken': Cookies.get('ecommerce_csrftoken'),
				},
				url:
					window.location.origin +
					'/api/v2/subscriptions/course_payments_status/',
				success: function(data) {
                    var coursePaymentsButton = $('[name=course-payments]');
                    if (data.course_payments)
                        coursePaymentsButton.text(gettext('Disable Course Payments'));
                    else coursePaymentsButton.text(gettext('Enable Course Payments'));
                },
			});
        }
    }
})
