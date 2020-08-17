define([
    'backbone',
    'backbone.super',
    'backbone.validation',
    'jquery',
    'js-cookie',
    'underscore',
    'underscore.string',
    'utils/utils',
    'moment',
    'backbone.relational'
],
    function(Backbone,
              BackboneSuper,
              BackboneValidation,
              $,
              Cookies,
              _,
              _s,
              Utils,
              moment) {
        'use strict';

        /* eslint-env es6: true */
        var SUBSCRIPTION_TYPES = {
            limited_access: gettext('Limited Access'),
            full_access_courses: gettext('Full Access (Courses)'),
            full_access_time: gettext('Full Access (Time Period)'),
            lifetime_access: gettext('Lifetime Access')
        };

        var SUBSCRIPTION_DURATION_UNITS = {
            days: 'Days',
            months: 'Months',
            years: 'Years',
        }

        _.extend(Backbone.Validation.messages, {
            required: gettext('This field is required.'),
            number: gettext('This value must be a number.'),
            date: gettext('This value must be a date.'),
            duration_units: gettext('At least one duration unit must be selected.')
        });
        _.extend(Backbone.Model.prototype, Backbone.Validation.mixin);

        return Backbone.RelationalModel.extend({
            urlRoot: '/api/v2/subscriptions/',

            defaults: {
                id: null,
                title: null,
                subscription_type: SUBSCRIPTION_TYPES.limited_access,
                subscription_duration_value: 0,
                subscription_duration_unit: SUBSCRIPTION_DURATION_UNITS.days,
                number_of_courses: 0,
                subscription_actual_price: 0,
                subscription_price: 0,
                subscription_display_order: 1,
                subscription_status: true
            },

            subscriptionTypes: SUBSCRIPTION_TYPES,

            baseSubscriptionValidation: {
                subscription_status: {
                    required: true
                },
                subscription_duration_value: {
                    pattern: 'number',
                    required: function() {
                        var subscription_type = this.get('subscription_type');
                        return subscription_type === SUBSCRIPTION_TYPES.limited_access || subscription_type === SUBSCRIPTION_TYPES.full_access_courses;
                    }
                },
                subscription_duration_unit: {
                    required: function() {
                        var subscription_type = this.get('subscription_type');
                        return subscription_type === SUBSCRIPTION_TYPES.limited_access || subscription_type === SUBSCRIPTION_TYPES.full_access_courses;
                    }
                },
                number_of_courses: {
                    pattern: 'number',
                    required: function() {
                        var subscription_type = this.get('subscription_type');
                        return subscription_type === SUBSCRIPTION_TYPES.limited_access || subscription_type === SUBSCRIPTION_TYPES.full_access_time;
                    }
                },
                subscription_actual_price: {
                    required: true
                },
                subscription_price: {
                    required: true
                },
            },

            validation: function() {
                return _.extend({}, this.baseSubscriptionValidation);
            },

            url: function() {
                var url = this._super();

                // Ensure the URL always ends with a trailing slash
                url += _s.endsWith(url, '/') ? '' : '/';

                return url;
            },

            save: function(attributes, options) {
                /* eslint no-param-reassign: 2 */

                // Remove all saved models from store, which prevents Duplicate id errors
                Backbone.Relational.store.reset();

                _.defaults(options || (options = {}), {
                    // The API requires a CSRF token for all POST requests using session authentication.
                    headers: {'X-CSRFToken': Cookies.get('ecommerce_csrftoken')},
                    contentType: 'application/json'
                });

                if (!options.patch) {
                    options.data = JSON.stringify(this.toJSON());
                }

                return this._super(attributes, options);
                /* eslint no-param-reassign: 0 */
            }
        });
    }
);
