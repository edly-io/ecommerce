/* istanbul ignore next */
require([
    'jquery',
    'payment_processors/cybersource_microform'
], function($, CyberSourceClient) {
    'use strict';

    $(document).ready(function() {
        CyberSourceClient.init(window.CyberSourceConfig);
    });
});
