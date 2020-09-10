define([
	'jquery',
	'backbone',
	'underscore',
	'underscore.string',
	'text!templates/individual_payments_action_modal.html',
], function ($, Backbone, _, _s, ConfirmationDialogButtons) {
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
            this.toggleIndividualCoursePaymentsData()
		},

		toggleIndividualCoursePaymentsData: function () {
			Backbone.ajax({
				context: this,
				type: 'GET',
				url: window.location.origin +
					'/api/v2/subscriptions/toggle_course_individual_payments/',
				success: this.onSuccess,
			});
		},

		onSuccess: function (data) {
            var course_individual_payments_button = $('[name=course-individual-payments]');
			if(data.course_individual_payments) course_individual_payments_button.text(gettext('Disable Course Individual Payments'));
			else course_individual_payments_button.text(gettext('Enable Course Individual Payments'));
			$('#individualPaymentsActionModal').modal('hide');
        },

		render: function () {
			this.$el.html(this.template);
			return this;
		},
	});
});
