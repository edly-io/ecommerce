p = {'client_reference_information': {'code': 'EDLY-100012',
                                   'owner_merchant_id': None,
                                   'submit_local_date_time': None},
  'consumer_authentication_information': {'acs_rendering_type': None,
                                          'acs_transaction_id': None,
                                          'acs_url': None,
                                          'authentication_path': None,
                                          'authentication_result': None,
                                          'authentication_status_msg': None,
                                          'authentication_transaction_id': None,
                                          'authorization_payload': None,
                                          'cardholder_message': None,
                                          'cavv': None,
                                          'cavv_algorithm': None,
                                          'challenge_cancel_code': None,
                                          'challenge_required': None,
                                          'decoupled_authentication_indicator': None,
                                          'directory_server_error_code': None,
                                          'directory_server_error_description': None,
                                          'directory_server_transaction_id': None,
                                          'eci': None,
                                          'eci_raw': None,
                                          'ecommerce_indicator': None,
                                          'effective_authentication_type': None,
                                          'indicator': None,
                                          'interaction_counter': None,
                                          'ivr': None,
                                          'network_score': None,
                                          'pareq': None,
                                          'pares_status': None,
                                          'proof_xml': None,
                                          'proxy_pan': None,
                                          'sdk_transaction_id': None,
                                          'signed_pares_status_reason': None,
                                          'specification_version': None,
                                          'step_up_url': None,
                                          'three_ds_server_transaction_id': None,
                                          'ucaf_authentication_data': None,
                                          'ucaf_collection_indicator': None,
                                          'veres_enrolled': None,
                                          'white_list_status': None,
                                          'white_list_status_source': None,
                                          'xid': None},
  'error_information': None,
  'id': '7055670670356906904953',
  'installment_information': None,
  'issuer_information': {'country': None,
                         'country_specific_discretionary_data': None,
                         'discretionary_data': None,
                         'response_code': None},
  'links': {'_self': {'href': '/pts/v2/payments/7055670670356906904953',
                      'method': 'GET'},
            'capture': None,
            'customer': None,
            'instrument_identifier': None,
            'payment_instrument': None,
            'reversal': None,
            'shipping_address': None},
  'order_information': {'amount_details': {'authorized_amount': '100.00',
                                           'currency': 'USD',
                                           'total_amount': '100.00'},
                        'invoice_details': None},
  'payment_information': {'account_features': None,
                          'bank': None,
                          'card': {'suffix': None},
                          'customer': None,
                          'instrument_identifier': None,
                          'payment_instrument': None,
                          'shipping_address': None,
                          'tokenized_card': {'assurance_level': None,
                                             'expiration_month': None,
                                             'expiration_year': None,
                                             'prefix': None,
                                             'requestor_id': None,
                                             'suffix': None,
                                             'type': '002'}},
  'point_of_sale_information': {'amex_capn_data': None,
                                'emv': None,
                                'terminal_id': '00123456'},
  'processing_information': None,
  'processor_information': {'ach_verification': None,
                            'amex_verbal_auth_reference_number': None,
                            'approval_code': '831000',
                            'auth_indicator': '1',
                            'avs': {'code': 'Y', 'code_raw': 'Y'},
                            'card_verification': None,
                            'consumer_authentication_response': None,
                            'customer': None,
                            'electronic_verification_results': None,
                            'forwarded_acquirer_code': None,
                            'master_card_authentication_type': None,
                            'master_card_service_code': None,
                            'master_card_service_reply_code': None,
                            'merchant_advice': None,
                            'merchant_number': '000000000123456',
                            'name': None,
                            'network_transaction_id': '0602MCC603474',
                            'payment_account_reference_number': None,
                            'provider_transaction_id': None,
                            'response_category_code': None,
                            'response_code': '00',
                            'response_code_source': None,
                            'response_details': None,
                            'routing': None,
                            'system_trace_audit_number': None,
                            'transaction_id': '0602MCC603474',
                            'transaction_integrity_code': None},
  'reconciliation_id': '71731281',
  'risk_information': {'case_priority': None,
                       'info_codes': {'address': ['UNV-ADDR'],
                                      'customer_list': None,
                                      'global_velocity': None,
                                      'identity_change': None,
                                      'internet': None,
                                      'phone': None,
                                      'suspicious': ['RISK-TB'],
                                      'velocity': None},
                       'ip_address': None,
                       'local_time': '0:37:47',
                       'profile': {'desination_queue': None,
                                   'name': 'Standard mid-market profile',
                                   'selector_rule': 'Default Active Profile'},
                       'providers': None,
                       'rules': [{'decision': 'IGNORE',
                                  'name': 'Fraud Score - Monitor'}],
                       'score': {'factor_codes': ['B', 'T'],
                                 'model_used': 'default',
                                 'result': '25'},
                       'travel': None,
                       'velocity': None},
  'status': 'AUTHORIZED',
  'submit_time_utc': '2024-01-18T08:37:47Z',
  'token_information': None}

print(p['status'])
print(p['processor_information']['transaction_id'])