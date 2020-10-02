define([
	'jquery',
	'js-cookie',
	'backbone',
	'underscore',
	'underscore.string',
	'text!templates/course_payments_action_modal.html',
], function ($, Cookies, Backbone, _, _s, ConfirmationDialogButtons) {
	'use strict';

	return Backbone.View.extend({
		template: _.template(ConfirmationDialogButtons),

		events: {
			'click [name=confirm-toggle]': 'confirmToggle',
		},

		initialize: function (options) {
			this._super(); // eslint-disable-line no-underscore-dangle
		},

		confirmToggle: function (event) {
			event.preventDefault();
			this.toggleCoursePaymentsData();
		},

		toggleCoursePaymentsData: function () {
			Backbone.ajax({
				context: this,
				type: 'POST',
				headers: {
					'X-CSRFToken': Cookies.get('ecommerce_csrftoken'),
				},
				url:
					window.location.origin +
					'/api/v2/subscriptions/toggle_course_payments/',
				success: this.onSuccess,
			});
		},

		onSuccess: function (data) {
			var coursePaymentsButton = $('[name=course-payments]');
			if (data.course_payments)
				coursePaymentsButton.text(gettext('Disable Course Payments'));
			else coursePaymentsButton.text(gettext('Enable Course Payments'));
			$('#coursePaymentsActionModal').modal('hide');
		},

		render: function () {
			this.$el.html(this.template);
			return this;
		},
	});
});
