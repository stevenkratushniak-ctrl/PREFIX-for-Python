# PYTHON 3.12 AST RULE CATALOG

## Authority Inputs

- node registry: `ast/python_ast_nodes.txt`
- parent/child constraints: `ast/python_ast_constraints.txt`
- transition rules: `rules/python_invalid_to_valid_transitions.txt`
- canonical authority implementation: `prefix_python/ast_bridge.py`
- enforcement engine: `prefix_python/engine.py`

## Version Pin

- Python runtime pin: `3.12`
- AST node registry pin: Python `3.12` standard-library `ast`
- explicit authority additions validated in code: `TypeAlias`, `TryStar`, `match_case`, `TypeVar`, `ParamSpec`, `TypeVarTuple`

## Legality Contract

The authority layer enforces more than parse success. Accepted states also require:

- parent/child legality for the pinned node surface
- non-empty required block bodies
- identifier legality for names, args, aliases, and attributes
- comparison arity equality
- context legality for `Name`, `Attribute`, `Subscript`, `Tuple`, `List`, and `Starred`
- source-position continuity
- token-stream capture and hashing
- roundtrip AST continuity after `ast.unparse()`

## Deterministic Auto-Apply Rules

| Rule ID | Class | Behavior |
| --- | --- | --- |
| `MISSING_COLON` | Block introduction | Append a singular required colon to a block-introducing line. |
| `AUTO_INDENT` | Block indentation | Indent the first block statement to the required depth. |
| `INSERT_PASS` | Empty block | Insert `pass` into an empty required block. |
| `CLOSE_DELIMITER` | Delimiter closure | Close unmatched opening delimiters at line end. |
| `REMOVE_EXTRA_DELIMITER` | Extra delimiter | Remove a singular extra closing delimiter when exactly one parse-valid repair exists. |
| `NORMALIZE_TABS` | Indentation normalization | Expand tabs deterministically to four spaces. |

## Candidate-Only Rules

| Rule ID | Class | Behavior |
| --- | --- | --- |
| `ELIF_TO_IF_CANDIDATE` | Keyword structure | Surface orphaned `elif` to `if` as a candidate-only repair. Never auto-apply. |

## Refusal-Only Rules

These states do not auto-apply and do not receive a hidden semantic placeholder:

- assignment without right-hand side
- trailing operator without operand
- orphaned `else`
- `return` outside function
- `continue` outside loop
- `break` outside loop
- unresolved module-level names
- NUL-byte inputs
- oversized inputs
- invalid UTF-8 file input

## Research / Future Rules

These are explicitly outside the current deterministic release surface:

- deterministic same-scope declaration insertion for unresolved names
- keyword-structure recovery beyond candidate-only `elif` handling
- multi-line delimiter relocation
- semantic placeholder completion
- multi-file or cross-module enforcement

## Deterministic Proof Outputs

For accepted states the engine now emits:

- `ast_sha256`
- `token_sha256`
- legality report
- proof trace with event hash, node count, token count, and roundtrip AST hash
