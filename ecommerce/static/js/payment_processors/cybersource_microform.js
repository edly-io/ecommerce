/**
 * CyberSource microform payment processor specific actions.
 */
define([
    "jquery",
    "js-cookie",
    "underscore.string",
    "pages/basket_page",
], function ($, _s) {
    "use strict";

    return {
        init: function (config) {
            let $paymentForm = $("#paymentForm"),
                $paymentButton = $("#payment-button-cybersource-microform"),
                $month = $("#id_expiry_month"),
                $year = $("#id_expiry_year");
            $paymentForm.attr("action", config.postURL);

            var myStyles = {
                input: {
                    "font-size": "14px",
                    "font-family": "helvetica, tahoma, calibri, sans-serif",
                    color: "#555",
                },
                ":focus": { color: "blue" },
                ":disabled": { cursor: "not-allowed" },
                valid: { color: "#3c763d" },
                invalid: { color: "#a94442" },
            };

            require([
                "https://flex.cybersource.com/cybersource/assets/microform/0.11/flex-microform.min.js",
            ], function (cybersourceFlex) {
                var flex = new cybersourceFlex.Flex(config.context);
                var microform = flex.microform({ styles: myStyles });
                var number = microform.createField("number", {
                    placeholder: "Enter card number",
                });
                var securityCode = microform.createField("securityCode", {
                    placeholder: "•••",
                });

                number.load("#number-container");
                securityCode.load("#securityCode-container");

                $paymentButton.on("click", function (e) {
                    e.preventDefault();
                    $(".cybersource-microform-error").html("");

                    let isFormValid = $paymentForm.get(0).checkValidity();
                    if (!isFormValid) {
                        $paymentForm.get(0).reportValidity();
                        return;
                    }

                    if (isDateInvalid($year.val(), $month.val())) {
                        return;
                    }

                    var options = {
                        expirationMonth: $month.val(),
                        expirationYear: $year.val(),
                    };
                    microform.createToken(options, function (err, token) {
                        if (err) {
                            console.error(err);
                            $(".cybersource-microform-error")
                                .css("color", "red")
                                .append("<p>* " + err.message + "</p>");
                        } else {

                            $('<input>').attr({
                                type: 'hidden',
                                name: 'token',
                                value: token
                            }).appendTo($paymentForm);

                            $paymentForm.submit();
                        }
                    });
                });
            });

            function isDateInvalid(year, month) {
                if (!/^\d{4}$/.test(year)) {
                    $(".cybersource-microform-error")
                        .css("color", "red")
                        .append(
                            "<p>* " +
                            "Please enter a valid four-digit year (e.g., 2024)." +
                            "</p>"
                        );
                    return true;
                }

                if (!/^(0[1-9]|1[0-2])$/.test(month)) {
                    $(".cybersource-microform-error")
                        .css("color", "red")
                        .append(
                            "<p>* " +
                            "Please enter a valid two-digit month (e.g., 09)." +
                            "</p>"
                        );
                    return true;
                }

                return false;
            }
        },
    };
});
