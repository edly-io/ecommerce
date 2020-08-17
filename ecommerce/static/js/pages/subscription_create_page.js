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
            title: gettext('Create New Subscription'),

            initialize: function() {
                this.model = new Subscription();
                this.view = new SubscriptionCreateEditView({model: this.model});
                this.render();
            }
        });
    }
);
