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
                $elavonButton = $('#payment-button-elavon');
            this.postUrl = config.postUrl;
            $paymentForm.attr('action', config.postUrl);
            const params = (new URL(window.location)).searchParams;
            if (params.get('ssl_result_message') === 'APPROVAL') {
                window.location.href = config.receiptUrl;
            }

            window.onmessage = function (e) {
                console.log(e);
                if (e.data && e.data.message_source === 'cowpay') {
                    if (e.data.three_d_secured) {
                        $('body').append($('<div id="cowpay-otp-container"></div>'));
                        COWPAYOTPDIALOG.init();
                        COWPAYOTPDIALOG.load(e.data.cowpay_reference_id);
                    }
                    else if (e.data.payment_gateway_reference_id || (e.data.payment_status && e.data.payment_status == "PAID")) {
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
                }
            };
            $elavonButton.on('click', function() {
                window.location.href = config.receiptUrl;
            })
        }
    };
});
