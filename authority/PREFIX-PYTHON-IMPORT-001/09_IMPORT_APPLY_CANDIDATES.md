# Import APPLY Candidates
## INSERT_FROM_IMPORT_CONNECTOR_V1 — map-level survivor
For a malformed from-import proposal lacking mandatory literal import, enumerate only token-boundary insertions of literal import within the governing statement. Potential APPLY requires exactly one successor that parses in Python 3.12, passes PREFIX AST authority, yields ast.ImportFrom, preserves all existing non-whitespace tokens in order and is idempotent.

Example evidence only: from pkg name -> from pkg import name when and only when cardinality is exactly one.

Not APPLY: missing alias as; module/symbol near-name substitution; relative-level rewriting; alias collision repair; environment absence. Existing V1 delimiter authority may independently repair singular import-parenthesis failures.