define([
    'models/subscription_model',
    'pages/page',
    'views/subscription_detail_view'
],
    function(Subscription,
              Page,
              SubscriptionDetailView) {
        'use strict';

        return Page.extend({
            title: function() {
                return this.model.get('title') + ' - ' + gettext('View Subscription');
            },

            initialize: function(options) {
                this.model = Subscription.findOrCreate({id: options.id});
                this.view = new SubscriptionDetailView({model: this.model});
                this.listenTo(this.model, 'sync', this.refresh);
                this.model.fetch();
            }
        });
    }
);
