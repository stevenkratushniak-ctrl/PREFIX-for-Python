# ADVERSARIAL TEST MATRIX

| Case | Surface | Expected Result | Evidence |
| --- | --- | --- | --- |
| Missing colon | Engine | `ACCEPT_FIXED` | `tests.test_prefix_python.PrefixPythonEngineTests.test_missing_colon_and_indent_are_corrected` |
| Missing block indentation | Engine | `ACCEPT_FIXED` | `tests.test_prefix_python.PrefixPythonEngineTests.test_missing_colon_and_indent_are_corrected` |
| Empty function body | Engine | `ACCEPT_FIXED` | `tests.test_prefix_python.PrefixPythonEngineTests.test_empty_function_gets_pass` |
| Unmatched opening delimiter | Engine | `ACCEPT_FIXED` | `tests.test_prefix_python.PrefixPythonEngineTests.test_unmatched_delimiter_is_closed` |
| Singular extra closing delimiter | Engine | `ACCEPT_FIXED` | `tests.test_prefix_python.PrefixPythonEngineTests.test_extra_closing_delimiter_is_removed` |
| Mixed tabs/spaces | Engine | `ACCEPT_FIXED` | `tests.test_prefix_python.PrefixPythonEngineTests.test_tabs_are_normalized_with_evidence` |
| Windows newline preservation | Engine | `ACCEPT_FIXED` | `tests.test_prefix_python.PrefixPythonEngineTests.test_windows_newlines_are_preserved` |
| Orphaned `else` | Engine | `REFUSE_INVALID` | `tests.test_prefix_python.PrefixPythonEngineTests.test_orphaned_else_is_refused` |
| `return` outside function | Engine | `REFUSE_INVALID` | `tests.test_prefix_python.PrefixPythonEngineTests.test_return_outside_function_is_refused` |
| Orphaned `elif` | Engine | `REFUSE_UNMAPPED` with candidates | `tests.test_prefix_python.PrefixPythonEngineTests.test_orphaned_elif_is_candidate_only` |
| Assignment without RHS | Engine | `REFUSE_UNMAPPED` | `tests.test_prefix_python.PrefixPythonEngineTests.test_assignment_rhs_is_refused_not_guessed` |
| Trailing operator | Engine | `REFUSE_UNMAPPED` | `tests.test_prefix_python.PrefixPythonEngineTests.test_trailing_operator_is_refused_not_guessed` |
| Undefined name | Engine | `REFUSE_UNMAPPED` | `tests.test_prefix_python.PrefixPythonEngineTests.test_undefined_name_is_refused` |
| NUL byte input | Engine | `REFUSE_INVALID` | `tests.test_prefix_python.PrefixPythonEngineTests.test_nul_bytes_are_refused` |
| Oversized input | Engine | `REFUSE_INVALID` | `tests.test_prefix_python.PrefixPythonEngineTests.test_oversized_input_is_refused` |
| Deterministic repeatability | Engine | identical payloads | `tests.test_prefix_python.PrefixPythonEngineTests.test_repeatability_is_deterministic` |
| Idempotency after fix | Engine | second pass `ACCEPT_VALID` | `tests.test_prefix_python.PrefixPythonEngineTests.test_idempotency_holds_after_fix` |
| No invalid AST committed | Engine | accepted output parses | `tests.test_prefix_python.PrefixPythonEngineTests.test_no_invalid_ast_is_committed_on_accept` |
| Unicode identifier input | Engine | `ACCEPT_VALID` | `tests.test_prefix_python.PrefixPythonEngineTests.test_unicode_identifier_is_accepted` |
| Invalid UTF-8 file | CLI | refusal | `tests.test_cli_prefix_python.PrefixPythonCliTests.test_invalid_utf8_file_is_refused` |
| Missing path | CLI | refusal | `tests.test_cli_prefix_python.PrefixPythonCliTests.test_missing_path_is_refused` |
| Scan path JSON | CLI | `ACCEPT_FIXED`, no write | `tests.test_cli_prefix_python.PrefixPythonCliTests.test_scan_file_json` |
| Stdin scan | CLI | `ACCEPT_FIXED` | `tests.test_cli_prefix_python.PrefixPythonCliTests.test_stdin_scan` |
| Apply + receipt + rollback | CLI | all succeed | `tests.test_cli_prefix_python.PrefixPythonCliTests.test_apply_and_rollback_valid_preimage` |
| Receipt replay determinism | CLI | `ACCEPT_VALID`, replay verified | `tests.test_cli_prefix_python.PrefixPythonCliTests.test_replay_receipt_verifies_deterministic_apply` |
| Receipt inspection | CLI | `ACCEPT_VALID`, chain depth surfaced | `tests.test_cli_prefix_python.PrefixPythonCliTests.test_inspect_receipt_reports_chain_depth` |
| Rollback invalid preimage | CLI | refusal | `tests.test_cli_prefix_python.PrefixPythonCliTests.test_rollback_refuses_invalid_preimage` |
| Parse authority | AST bridge | valid AST authority | `tests.test_ast_bridge.PrefixPythonAstBridgeTests.test_validate_source_text_accepts_parseable_source` |
| Parse rejection | AST bridge | refusal | `tests.test_ast_bridge.PrefixPythonAstBridgeTests.test_validate_source_text_rejects_unparseable_source` |
| Python 3.12 type alias admission | AST bridge | valid AST authority | `tests.test_ast_bridge.PrefixPythonAstBridgeTests.test_validate_source_text_accepts_python_3_12_type_alias` |
| Empty function AST illegality | AST bridge | violation detected | `tests.test_ast_bridge.PrefixPythonAstBridgeTests.test_validate_ast_legality_rejects_empty_function_body` |
| Compare arity corruption | AST bridge | violation detected | `tests.test_ast_bridge.PrefixPythonAstBridgeTests.test_validate_ast_legality_rejects_compare_arity_mismatch` |
| VS Code typed outcome behavior | Extension | behavior helper passes | `editor/vscode/response.test.js` via `npm run test:behavior` |
