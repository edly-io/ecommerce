define([
    'models/subscription_model',
    'pages/page',
    'views/subscription_create_edit_view'
],
    function(Subscription,
              Page,
              SubscriptionCreateEditView) {
        'use strict';

        return Page.extend({
            title: function() {
                return this.model.get('title') + ' - ' + gettext('Edit Subscription');
            },

            initialize: function(options) {
                this.model = Subscription.findOrCreate({id: options.id});
                this.view = new SubscriptionCreateEditView({
                    editing: true,
                    model: this.model
                });

                this.listenTo(this.model, 'sync', this.render);
                this.model.fetch();
            }
        });
    }
);
