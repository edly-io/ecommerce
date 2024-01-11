/**
 * CyberSource payment processor specific actions.
 */
define([
    'jquery',
    'js-cookie',
    'underscore.string',
    'pages/basket_page'
], function($, Cookies, _s, BasketPage) {
    'use strict';

    return {
        init: function(config) {
            var $paymentForm = $('#paymentForm'),
                $pciFields = $('.pci-field', $paymentForm),
                cardMap = {
                    visa: '001',
                    mastercard: '002',
                    amex: '003',
                    discover: '004'
                };
            let $paymentButton = $('#payment-button-cybersource-microform'),
                $card = $('#id_card_number'),
                $month = $('#id_expiry_month'),
                $year = $('#id_expiry_year'),
                $code = $('#id_card_code')

            // var flex;

            var myStyles = {  
                'input': {    
                  'font-size': '14px',    
                  'font-family': 'helvetica, tahoma, calibri, sans-serif',    
                  'color': '#555'  
                },  
                ':focus': { 'color': 'blue' },  
                ':disabled': { 'cursor': 'not-allowed' },  
                'valid': { 'color': '#3c763d' },  
                'invalid': { 'color': '#a94442' }
              };
  
    
                // setup
                // var flex = new Flex(captureContext);
                // var microform = flex.microform({ styles: myStyles });
            
            // should work on form initilize
            require(['https://testflex.cybersource.com/microform/bundle/v2/flex-microform.min.js'], function (cybersourceFlex) {
                var flex  = new cybersourceFlex.Flex(config.context);
                console.log('kkkkk22 -- ', flex);
                var microform = flex.microform({ styles: myStyles });
                var number = microform.createField('number', { placeholder: 'Enter card number' });
                var securityCode = microform.createField('securityCode', { placeholder: '•••' });

                number.load('#number-container');
                securityCode.load('#securityCode-container');

                $paymentButton.on('click', function(e) {
                    e.preventDefault();
                    // console.log('hola----here here------hola ', $card.val(), cybersourceFlex);
                    // console.log('year', $year.val(), $month.val());
                    // console.log('code ', $code.val());
                    // console.log('cc ', config.context)

                    var options = {    
                        expirationMonth: $month.val(),  
                        expirationYear: $year.val()
                      };   
                      microform.createToken(options, function (err, token) {
                        if (err) {
                          // handle error
                          console.error(err);
                          errorsOutput.textContent = err.message;
                        } else {
                          // At this point you may pass the token back to your server as you wish.
                          // In this example we append a hidden input to the form and submit it.      
                          console.log(JSON.stringify(token));
                          flexResponse.value = JSON.stringify(token);
                          form.submit();
                        }
                      });
                      
    
                    });
            });

            this.signingUrl = config.signingUrl;

            // The payment form should post to CyberSource
            $paymentForm.attr('action', config.postUrl);

            // $paymentButton.on('click', function(e) {
            //     e.preventDefault();
            //     console.log('hola----------hola ', $card.val());
            //     console.log('year', $year.val(), $month.val());
            //     console.log('code ', $code.val());



            //     // var options = {    
            //     //     expirationMonth: $month.val(),  
            //     //     expirationYear: $year.val()
            //     //   };        
                  
            //     //   microform.createToken(options, function (err, token) {
            //     //     if (err) {
            //     //       // handle error
            //     //       console.error(err);
            //     //       errorsOutput.textContent = err.message;
            //     //     } else {
            //     //       // At this point you may pass the token back to your server as you wish.
            //     //       // In this example we append a hidden input to the form and submit it.      
            //     //       console.log(JSON.stringify(token));
            //     //       flexResponse.value = JSON.stringify(token);
            //     //       form.submit();
            //     //     }
            //     //   });
                  

            //     });
                

            // // Add name attributes to the PCI fields
            // $pciFields.each(function() {
            //     var $this = $(this);
            //     $this.attr('name', $this.data('name'));
            // });

            // $paymentForm.submit($.proxy(this.onSubmit, this));

            // // Add CyberSource-specific fields
            // $paymentForm.append($('<input type="hidden" name="card_expiry_date" class="pci-field">'));
            // $paymentForm.append($('<input type="hidden" name="card_type" class="pci-field">'));

            // Add an event listener to populate the CyberSource card type field
            // $paymentForm.on('cardType:detected', function(event, data) {
            //     $('input[name=card_type]', $paymentForm).val(cardMap[data.type]);
            // });

        },
        

        /**
         * Payment form submit handler.
         *
         * Before posting to CyberSource, this handler retrieves signed data fields from the server. PCI fields
         * (e.g. credit card number, expiration) should NEVER be posted to the server, only to CyberSource.
         *
         * @param event
         */
        // onSubmit: function(event) {
        //     var $form = $(event.target),
        //         $signedFields = $('input,select', $form).not('.pci-field'),
        //         expMonth = $('#card-expiry-month', $form).val(),
        //         expYear = $('#card-expiry-year', $form).val();

        //     // Restore name attributes so the data can be posted to CyberSource
        //     $('#card-number', $form).attr('name', 'card_number');
        //     $('#card-cvn', $form).attr('name', 'card_cvn');

        //     // Post synchronously since we need the returned data.
        //     $.ajax({
        //         type: 'POST',
        //         url: this.signingUrl,
        //         data: $signedFields.serialize(),
        //         async: false,
        //         success: function(data) {
        //             var formData = data.form_fields,
        //                 key;

        //             // Format the date for CyberSource (MM-YYYY)
        //             $('input[name=card_expiry_date]', $form).val(expMonth + '-' + expYear);

        //             // Disable the fields on the form so they are not posted since their names are not what is
        //             // expected by CyberSource. Instead post add the parameters from the server to the form,
        //             // and post them.
        //             $signedFields.attr('disabled', 'disabled');

        //             // eslint-disable-next-line no-restricted-syntax
        //             for (key in formData) {
        //                 if (Object.prototype.hasOwnProperty.call(formData, key)) {
        //                     $form.append(
        //                         '<input type="hidden" name="' + key + '" value="' + formData[key] + '" />'
        //                     );
        //                 }
        //             }
        //         },

        //         error: function(jqXHR, textStatus) {
        //             var $field,
        //                 cardHolderFields,
        //                 error,
        //                 k;

        //             // Don't allow the form to submit.
        //             event.preventDefault();
        //             event.stopPropagation();

        //             cardHolderFields = [
        //                 'first_name', 'last_name', 'address_line1', 'address_line2', 'state', 'city', 'country',
        //                 'postal_code'
        //             ];

        //             if (textStatus === 'error') {
        //                 error = JSON.parse(jqXHR.responseText);

        //                 if (error.field_errors) {
        //                     // eslint-disable-next-line no-restricted-syntax
        //                     for (k in error.field_errors) {
        //                         if (cardHolderFields.indexOf(k) !== -1) {
        //                             $field = $('input[name=' + k + ']');
        //                             // TODO Use custom events to remove this dependency.
        //                             BasketPage.appendCardHolderValidationErrorMsg($field, error.field_errors[k]);
        //                             $field.focus();
        //                         }
        //                     }
        //                 } else {
        //                     // Unhandled errors should redirect to the general payment error page.
        //                     window.location.href = window.paymentErrorPath;
        //                 }
        //             }
        //         }
        //     });
        // },

        // displayErrorMessage: function(message) {
        //     $('#messages').html(_s.sprintf('<div class="alert alert-error">%s<i class="icon-warning-sign"></i></div>',
        //         message));
        // },


        /* istanbul ignore next */
        // redirectToReceipt: function(orderNumber) {
        //     /* istanbul ignore next */
        //     window.location.href = this.applePayConfig.receiptUrl + '?order_number=' + orderNumber;
        // }

    };
});



// require(['https://testflex.cybersource.com/microform/bundle/v2/flex-microform.min.js'], function(cybersourceFlex){
//     console.log('jjjj - ', cybersourceFlex.Flex)
//     var form = document.querySelector('#my-sample-form');
// var payButton = document.querySelector('#pay-button');
// var flexResponse = document.querySelector('#flexresponse');
// var expMonth = document.querySelector('#expMonth');
// var expYear = document.querySelector('#expYear');
// var errorsOutput = document.querySelector('#errors-output');

// // the capture context that was requested server-side for this transaction



// // custom styles that will be applied to each field we create using Microform
// var myStyles = {  
//   'input': {    
//     'font-size': '14px',    
//     'font-family': 'helvetica, tahoma, calibri, sans-serif',    
//     'color': '#555'  
//   },  
//   ':focus': { 'color': 'blue' },  
//   ':disabled': { 'cursor': 'not-allowed' },  
//   'valid': { 'color': '#3c763d' },  
//   'invalid': { 'color': '#a94442' }
// };

// // setup
// var flex = new cybersourceFlex.Flex(captureContext);
// var microform = flex.microform({ styles: myStyles });
// var number = microform.createField('number', { placeholder: 'Enter card number' });
// var securityCode = microform.createField('securityCode', { placeholder: '•••' });

// number.load('#number-container');
// securityCode.load('#securityCode-container');


// payButton.addEventListener('click', function() {  
  
//   var options = {    
//     expirationMonth: document.querySelector('#expMonth').value,  
//     expirationYear: document.querySelector('#expYear').value 
//   };              
  
//   microform.createToken(options, function (err, token) {
//     if (err) {
//       // handle error
//       console.error(err);
//       errorsOutput.textContent = err.message;
//     } else {
//       // At this point you may pass the token back to your server as you wish.
//       // In this example we append a hidden input to the form and submit it.      
//       console.log(JSON.stringify(token));
//       flexResponse.value = JSON.stringify(token);
//       form.submit();
//     }
//   });
// });
// });


// require(['flexMicroformScript'], function (flexMicroformScript) {
//     console.log('kkkkk -- ', flexMicroformScript)
// });