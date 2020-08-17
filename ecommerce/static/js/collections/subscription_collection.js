define([
    'collections/paginated_collection',
    'models/subscription_model'
],
    function(PaginatedCollection,
              Subscription) {
        'use strict';

        return PaginatedCollection.extend({
            model: Subscription,
            url: '/api/v2/subscriptions/'
        });
    }
);
