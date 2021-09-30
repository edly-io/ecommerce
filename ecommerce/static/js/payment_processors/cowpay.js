/**
 * Cowpay payment processor specific actions.
 */
define([
    'jquery'
], function($) {
    'use strict';

    return {
        init: function(config) {
            let $paymentForm = $('#paymentForm'),
                $cowpayButton = $('#payment-button-cowpay');
            this.postUrl = config.postUrl;
            $paymentForm.attr('action', config.postUrl);

            window.onmessage = function (e) {
                console.log(e);
                if (e.data && e.data.message_source === 'cowpay') {
                    var formData = new FormData();

                    for (const key in e.data) {
                        formData.append(key, e.data[key]);
                    }

                    fetch(config.cowpayExecutionUrl, {
                        credentials: 'include',
                        method: 'POST',
                        body: formData
                    })
                    .then(response => response.json())
                    .then(json => {
                        window.location.href = json.url;
                    });
                }
            };
            $cowpayButton.on('click', function() {
                $('body').append($('<div id="cowpay-iframe-container"></div>'));
                COWPAYIFRAMEDIALOG.init();
                COWPAYIFRAMEDIALOG.load(config.cowpayIframeToken);
            })
        }
    };
});
