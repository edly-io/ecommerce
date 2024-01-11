/* istanbul ignore next */
// require.config({
//     flexMicroformScript: 'https://testflex.cybersource.com/microform/bundle/v2/flex-microform.min.js'
// });

require([
    'jquery',
    'payment_processors/cybersource_microform'
], function($, CyberSourceClient) {
    'use strict';

    $(document).ready(function() {
        CyberSourceClient.init(window.CyberSourceConfig);
    });
});

// require(['flexMicroformScript'], function (flexMicroformScript) {
//     console.log('kkkkk -- ', flexMicroformScript)
// });

// define('flexMicroform', [], function() {
//     // Load the script
//     var script = document.createElement('script');
//     script.src = 'https://flex.cybersource.com/cybersource/assets/microform/0.11/flex-microform.min.js';
//     document.head.appendChild(script);
//     FlexMicroform = {};
//     // Return any functionality you might want to expose
//     // For instance, if the script defines a global object 'FlexMicroform',
//     // you might return that for use within your application
//     return FlexMicroform; // Adjust this according to how the script defines its functionality
// });

// require(['flexMicroform'], function(FlexMicroform) {
//     // Use FlexMicroform functionality here
// });