define([
    'collections/subscription_collection',
    'pages/page',
    'views/subscription_list_view'
],
    function(SubscriptionCollection,
              Page,
              SubscriptionListView) {
        'use strict';

        return Page.extend({
            title: gettext('Subscriptions'),

            initialize: function() {
                this.collection = new SubscriptionCollection();
                this.view = new SubscriptionListView({collection: this.collection});
                this.render();
                this.collection.fetch({remove: false, data: {page_size: 50}});
            }
        });
    }
);
