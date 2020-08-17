/* eslint no-underscore-dangle: ["error", { "allow": ["_initAttributes", "_super"] }] */

define([
    'jquery',
    'backbone',
    'backbone.super',
    'backbone.validation',
    'backbone.stickit',
    'ecommerce',
    'underscore',
    'underscore.string',
    'utils/utils',
    'text!templates/_alert_div.html',
    'text!templates/subscription_form.html',
    'models/subscription_model',
    'collections/subscription_collection',
    'views/form_view',
],
    function($,
              Backbone,
              BackboneSuper,
              BackboneValidation,
              BackboneStickit,
              ecommerce,
              _,
              _s,
              Utils,
              AlertDivTemplate,
              SubscriptionFormTemplate,
              Subscription,
              Subscriptions,
              FormView) {
        'use strict';

        return FormView.extend({
            tagName: 'form',

            className: 'subscription-form-view',

            updateWithPatch: false,

            template: _.template(SubscriptionFormTemplate),

            subscriptionDurationUnits: [
                {
                    value: 'days',
                    label: gettext('Days')
                },
                {
                    value: 'months',
                    label: gettext('Months')
                },
                {
                    value: 'years',
                    label: gettext('Years')
                },
            ],

            baseCouponBindings: {
                'input[name=title]': {
                    observe: 'title'
                },
                'input[name=subscription_type]': {
                    observe: 'subscription_type'
                },
                'input[name=duration_value]': {
                    observe: 'subscription_duration_value'
                },
                'select[name=duration_unit]': {
                    observe: 'subscription_duration_unit',
                    selectOptions: {
                        collection: function() {
                            return this.subscriptionDurationUnits;
                        }
                    }
                },
                'input[name=actual_price]': {
                    observe: 'subscription_actual_price'
                },
                'input[name=number_of_courses]': {
                    observe: 'number_of_courses'
                },
                'input[name=price]': {
                    observe: 'subscription_price'
                },
                'input[name=subscription_active_status]': {
                    observe: 'subscription_active_status'
                },
            },

            bindings: function() {
                return _.extend({}, this.baseCouponBindings);
            },

            events: {
                'click .external-link': 'routeToLink',
                'click #cancel-button': 'cancelButtonClicked'
            },

            getEditableAttributes: function() {
                return [
                    'title',
                    'subscription_active_status',
                ];
            },

            setupToggleListeners: function() {
                this.listenTo(this.model, 'change:subscription_type', this.toggleSubscriptionTypeFields);
            },

            initialize: function(options) {
                this.alertViews = [];
                this.editing = options.editing || false;
                this.hiddenClass = 'hidden';
                if (this.editing) {
                    this.editableAttributes = this.getEditableAttributes();
                    // Store initial model attribute values in order to revert to them when cancel button is clicked.
                    this._initAttributes = $.extend(true, {}, this.model.attributes);
                }

                this.setupToggleListeners();
                this._super();
            },

            cancelButtonClicked: function() {
                this.model.set(this._initAttributes);
            },

            setLimitToElement: function(element, maxValue, minValue) {
                element.attr({max: maxValue, min: minValue});
            },

            formGroup: function(el) {
                return this.$(el).closest('.form-group');
            },

            toggleSubscriptionTypeFields: function() {
                var subscriptionType = this.$('[name=subscription_type]:checked').val(),
                    limitedAccessFields = [
                        '[name=number_of_courses]',
                    ],
                    fullAccessFields = [
                        '[name=duration_value]',
                        '[name=duration_unit]',
                    ];

                if (subscriptionType === 'full-access-courses') {
                    _.each(fullAccessFields, function(field) {
                        this.formGroup(field).removeClass(this.hiddenClass);
                        this.$(field).attr('disabled', false);
                    }, this);
                    _.each(limitedAccessFields, function(field) {
                        this.hideField(field);
                    }, this);
                } else if (subscriptionType === 'full-access-time-period') {
                    _.each(limitedAccessFields, function(field) {
                        this.formGroup(field).removeClass(this.hiddenClass);
                        this.$(field).attr('disabled', false);
                    }, this);
                    _.each(fullAccessFields, function(field) {
                        this.hideField(field);
                    }, this);
                } else if (subscriptionType === 'limited-access') {
                    _.each(limitedAccessFields, function(field) {
                        this.formGroup(field).removeClass(this.hiddenClass);
                        this.$(field).attr('disabled', false);
                    }, this);
                    _.each(fullAccessFields, function(field) {
                        this.formGroup(field).removeClass(this.hiddenClass);
                        this.$(field).attr('disabled', false);
                    }, this);
                } else if (subscriptionType === 'lifetime-access') {
                    _.each(limitedAccessFields, function(field) {
                        this.hideField(field);
                    }, this);
                    _.each(fullAccessFields, function(field) {
                        this.hideField(field);
                    }, this);
                }
            },

            hideField: function(fieldName) {
                var field = this.$(fieldName);
                this.formGroup(fieldName).addClass(this.hiddenClass);
                field.attr('disabled', true);
                field.trigger('change');
            },

            disableNonEditableFields: function() {
                this.$('.non-editable').attr('disabled', true);
            },

            setRadioValues: function(name, value) {
                this.$('input:radio[name=' + name + '][value=' + value + ']').attr('checked', true);
            },

            /**
             * Open external links in a new tab.
             * Works only for anchor elements that contain 'external-link' class.
             */
            routeToLink: function(e) {
                e.preventDefault();
                e.stopPropagation();
                window.open(e.currentTarget.href);
            },

            render: function() {
                this.$el.html(this.template(this.model.attributes));
                this.stickit();

                this.$('.row:first').before(AlertDivTemplate);

                this.toggleSubscriptionTypeFields();
                if (this.editing) {
                    this.setRadioValues('subscription_type', this.model.attributes.subscription_type);
                    var subscription_active_status = this.model.attributes.subscription_status ? 'active' : 'inactive'
                    this.setRadioValues('subscription_active_status', subscription_active_status);
                    this.disableNonEditableFields();
                    this.$('button[type=submit]').html(gettext('Save Changes'));

                } else {
                    this.model.set({
                        subscription_type: 'limited-access',
                        subscription_active_status: 'active',
                    });
                    this.$('button[type=submit]').html(gettext('Create Subscription'));
                }

                this._super();
                return this;
            },

            saveSuccess: function(model, response) {
                this.goTo(response.id.toString());
            }

        });
    }
);
