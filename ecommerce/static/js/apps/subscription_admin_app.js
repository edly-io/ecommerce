require([
    'backbone',
    'routers/subscription_router',
    'utils/navigate'
],
    function(Backbone,
              SubscriptionRouter,
              navigate) {
        'use strict';

        $(function() {
            var $app = $('#app'),
                subscriptionApp = new SubscriptionRouter({$el: $app});

            subscriptionApp.start();

            // Handle navbar clicks.
            $('a.navbar-brand').on('click', navigate);

            // Handle internal clicks
            $app.on('click', 'a', navigate);
        });
    }
);
