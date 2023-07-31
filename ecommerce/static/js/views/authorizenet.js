/* istanbul ignore next */
require([
    'jquery',
    'payment_processors/authorizenet'
], function($, AuthorizenetClient) {
    'use strict';

    $(document).ready(function() {
        AuthorizenetClient.init(window.AuthorizenetConfig);
    });
});
