define([
    'jquery',
    'backbone',
    'underscore',
    'underscore.string',
    'moment',
    'utils/subscription_utils',
    'text!templates/subscription_list.html',
    'views/confirmation_dialog_view',
    'dataTablesBootstrap'
],
    function($,
              Backbone,
              _,
              _s,
              moment,
              SubscriptionUtils,
              subscriptionListViewTemplate,
              confirmationDialog) {
        'use strict';

        return Backbone.View.extend({
            className: 'subscription-list-view',

            template: _.template(subscriptionListViewTemplate),

            initialize: function() {
                this.confirm_dialog_view = new confirmationDialog();
                this.listenTo(this.collection, 'update', this.refreshTableData);
            },

            getRowData: function(subscription) {
                return {
                    id: subscription.get('id'),
                    title: subscription.get('title'),
                    subscription_type: SubscriptionUtils.formatSubscriptionType(subscription.get('subscription_type')),
                    subscription_actual_price: subscription.get('subscription_actual_price') + ' '+ currency,
                    subscription_price: subscription.get('subscription_price') + ' '+ currency,
                    subscription_status: subscription.get('subscription_status') ? 'Active': 'Inactive',
                    date_created: moment.utc(subscription.get('date_created')).format('MMMM DD, YYYY, h:mm A'),
                    course_payments: subscription.get('course_payments', true)
                };
            },

            renderSubscriptionTable: function() {
                var filterPlaceholder = gettext('Search...'),
                    $emptyLabel = '<label class="sr">' + filterPlaceholder + '</label>';

                if (!$.fn.dataTable.isDataTable('#subscriptionTable')) {
                    this.$el.find('#subscriptionTable').DataTable({
                        autoWidth: true,
                        info: true,
                        paging: true,
                        oLanguage: {
                            oPaginate: {
                                sNext: gettext('Next'),
                                sPrevious: gettext('Previous')
                            },

                            // Translators: _START_, _END_, and _TOTAL_ are placeholders. Do NOT translate them.
                            sInfo: gettext('Displaying _START_ to _END_ of _TOTAL_ subscriptions'),

                            // Translators: _MAX_ is a placeholder. Do NOT translate it.
                            sInfoFiltered: gettext('(filtered from _MAX_ total subscriptions)'),

                            // Translators: _MENU_ is a placeholder. Do NOT translate it.
                            sLengthMenu: gettext('Display _MENU_ subscriptions'),
                            sSearch: ''
                        },
                        order: [[0, 'asc']],
                        columns: [
                            {
                                title: gettext('Title'),
                                data: 'title',
                                fnCreatedCell: function(nTd, sData, oData) {
                                    $(nTd).html(_s.sprintf('<a href="/subscriptions/%s/" class="course-name">%s</a>', oData.id, oData.title));
                                }
                            },
                            {
                                title: gettext('Subscription Type'),
                                data: 'subscription_type',
                            },
                            {
                                title: gettext('Actual Price'),
                                data: 'subscription_actual_price',
                            },
                            {
                                title: gettext('Price'),
                                data: 'subscription_price',
                            },
                            {
                                title: gettext('Active Status'),
                                data: 'subscription_status',
                            },
                            {
                                title: gettext('Created'),
                                data: 'date_created'
                            },
                        ]
                    });

                    // NOTE: #subscriptionTable_filter is generated by dataTables
                    this.$el.find('#subscriptionTable_filter label').prepend($emptyLabel);

                    this.$el.find('#subscriptionTable_filter input')
                        .attr('placeholder', filterPlaceholder)
                        .addClass('field-input input-text')
                        .removeClass('form-control input-sm');
                }
            },

            render: function() {
                this.$el.html(this.template);
                this.$el.find('.pull-right').prepend(this.confirm_dialog_view.render().el)
                this.renderSubscriptionTable();
                this.refreshTableData();

                return this;
            },

            /**
             * Refresh the data table with the collection's current information.
             */
            refreshTableData: function() {
                var data = this.collection.map(this.getRowData, this),
                    $table = this.$el.find('#subscriptionTable').DataTable();
                SubscriptionUtils.setCoursePaymentsButtonText();

                $table.clear().rows.add(data).draw();
                return this;
            }
        });
    }
);