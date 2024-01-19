/**
 * Authorizenet payment processor specific actions.
 */
define([
    'jquery',
    'utils/credit_card'
], function($, CreditCardUtils) {
    'use strict';

    return {
        init: function(config) {
            let $paymentForm = $('#paymentForm'), 
                $paymentButton = $('#payment-button-authorizenet'),
                $cardNumber = $('#id_card_number'),
                $expiryMonth = $('#id_expiry_month'),
                $expiryYear = $('#id_expiry_year'),
                $cardCode = $('#id_card_code'),
                $fullName = $('#id_full_name');

            this.postURL = config.postURL;
            console.log('kl--- ', config.postURL);
            $paymentForm.attr('action', config.postURL);

            $fullName.attr('required', true);
            $cardNumber.attr('required', true);
            $cardCode.attr('required', true);
            $expiryMonth.attr('required', true);
            $expiryYear.attr('required', true);
            $expiryMonth.attr('maxLength', 2);
            $expiryYear.attr('maxLength', 2);

            $cardNumber.keyup(function () {
                $('.help-block-card').html('');
                if ($cardNumber.val() !== '' && !CreditCardUtils.isValidCardNumber($cardNumber.val())) {
                    $('.help-block-card').css('color', 'red').html('*olp olp');
                }
            });
            console('yah ', $paymentButton)

            $paymentButton.on('click', function(e) {
                e.preventDefault();
                $('.authorizenet-error').html('');

                let isFormValid = $paymentForm.get(0).checkValidity();
                if (!isFormValid) {
                    $paymentForm.get(0).reportValidity();
                    return;
                }

                var authData = {};
                authData.clientKey = config.clientKey;
                authData.apiLoginID = config.apiLoginID;

                var cardData = {};
                cardData.cardNumber = $cardNumber.val();
                cardData.month = $expiryMonth.val();
                cardData.year = $expiryYear.val();
                cardData.fullName = $fullName.val();
                cardData.cardCode = $cardCode.val();

                var secureData = {};
                secureData.authData = authData;
                secureData.cardData = cardData;
                
                Accept.dispatchData(secureData, responseHandler);

                function responseHandler(response) {
                    // if (response.messages.resultCode === 'Error') {
                    //     var i = 0;
                    //     while (i < response.messages.message.length) {
                    //         $('.authorizenet-error').css('color', 'green').append("<p>*" + response.messages.message[i].text + "</p>");
                    //         i = i + 1;
                    //     }
                    // } else {
                    //     paymentFormUpdate(response.opaqueData);
                    // }
                    paymentFormUpdate(response.opaqueData);
                }

                function paymentFormUpdate(opaqueData) {
                    $('#id_data_descriptor').val(opaqueData.dataDescriptor);
                    $('#id_data_value').val(opaqueData.dataValue);

                    $cardNumber.val('');
                    $cardCode.val('');
                    $expiryYear.val('');
                    $expiryMonth.val('');

                    $paymentForm.submit();
                }
            });
        }
    };
});
