/* istanbul ignore next */
require([
    'jquery',
    'payment_processors/elavon'
], function($, Elavon) {
    'use strict';

    $(document).ready(function() {
        Elavon.init(window.ElavonConfig);
    });
});
