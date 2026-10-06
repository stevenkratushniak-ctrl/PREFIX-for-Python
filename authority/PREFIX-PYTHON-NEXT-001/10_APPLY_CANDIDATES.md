# APPLY Candidates
Two V2 rules qualify at the map level, subject to implementation tests.

1. INSERT_ITERATION_IN_V2: construct-scoped enumeration must find exactly one insertion of `in` that produces Python-3.12 parse-valid and PREFIX-authority-valid source while preserving existing non-whitespace tokens in order.
2. INSERT_EXCEPT_ALIAS_AS_V2: same for `as`, additionally requiring AST proof of exception-handler alias binding.

Neither rule triggers merely from a friendly parser message. Candidate cardinality is evidence. Valid input is unchanged. Second execution must be ACCEPT_VALID. Existing proof, receipt, replay and rollback machinery must govern new event IDs.