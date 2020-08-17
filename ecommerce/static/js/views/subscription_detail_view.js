define([
    'jquery',
    'backbone',
    'ecommerce',
    'underscore',
    'underscore.string',
    'moment',
    'text!templates/_alert_div.html',
    'text!templates/subscription_detail.html',
    'utils/alert_utils',
    'utils/subscription_utils',
],
    function($,
              Backbone,
              ecommerce,
              _,
              _s,
              moment,
              AlertDivTemplate,
              SubscriptionDetailTemplate,
              AlertUtils,
              SubscriptionUtils) {
        'use strict';

        return Backbone.View.extend({
            className: 'coupon-detail-view',


            template: _.template(SubscriptionDetailTemplate),

            initialize: function() {
                this.alertViews = [];
            },

            formatDateTime: function(dateTime) {
                return moment.utc(dateTime).format('MM/DD/YYYY h:mm A');
            },

            render: function() {
                var html,
                templateData,
                id = this.model.get('id'),
                title = this.model.get('title'),
                subscriptionType = SubscriptionUtils.formatSubscriptionType(this.model.get('subscription_type')),
                subscriptionStatus = this.model.get('subscription_status'),
                dateCreated = this.model.get('date_created'),
                dateEdited = this.model.get('date_updated'),
                numberOfCourses = this.model.get('number_of_courses'),
                subscriptionActualPrice = this.model.get('subscription_actual_price'),
                subscriptionPrice = this.model.get('subscription_price'),
                subscriptionDurationValue = this.model.get('subscription_duration_value'),
                subscriptionDurationUnit = this.model.get('subscription_duration_unit');

                templateData = {
                    id,
                    title,
                    subscription_type: subscriptionType,
                    subscription_status: subscriptionStatus,
                    subscription_actual_price: subscriptionActualPrice,
                    subscription_price: subscriptionPrice,
                    number_of_courses: numberOfCourses,
                    subscription_duration_value: subscriptionDurationValue,
                    subscription_duration_unit: subscriptionDurationUnit,
                    dateEdited: dateEdited ? this.formatDateTime(dateEdited) : '',
                    dateCreated: dateCreated ? this.formatDateTime(dateCreated) : '',
                };

                html = this.template(templateData);

                this.$el.html(html);
                this.delegateEvents();

                this.$alerts = this.$el.find('.alerts');

                return this;
            },

        });
    }
);
