/* istanbul ignore next */
require([
    'jquery',
    'payment_processors/cowpay'
], function($, Cowpay) {
    'use strict';

    $(document).ready(function() {
        Cowpay.init(window.CowpayConfig);
    });
});
