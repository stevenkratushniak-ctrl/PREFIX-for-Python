# Python Rule Catalog By Lane

This catalog classifies the current Python authority surface into shipped product lanes.

## Authority Basis

Primary authority for this catalog was derived from the inspected finite Python taxonomy set:

- the 20-category Python taxonomy
- the extreme-pattern catalog
- the finite error-map schema
- the complete finite mapper notes

The catalog below describes the shipped Python product, not the entire theoretical authority surface.

This file is the standalone release-facing classification surface. It does not require external documentation roots at runtime.

## `APPLY`

Shipped and auto-applied only when one lawful continuation exists.

| Runtime Rule | Python Authority Category | Example Authority IDs | Why It Qualifies |
| --- | --- | --- | --- |
| `MISSING_COLON` | Syntax Errors | `PY-SYN-001` through `PY-SYN-011`, `SYN-001` through `SYN-016` | parser-bounded, line-local, idempotent |
| `AUTO_INDENT` | Indentation & Block Structure | `PY-IND-001`, `IND-011` | bounded indentation continuation only |
| `INSERT_PASS` | Indentation & Incomplete Constructs | `PY-IND-002` through `PY-IND-004`, `PY-INC-001` through `PY-INC-003` | keeps block parse-valid without semantic invention |
| `CLOSE_DELIMITER` | Syntax / Incomplete Constructs | `PY-SYN-012` through `PY-SYN-016`, `SYN-020` through `SYN-027` | singular closing sequence only |
| `REMOVE_EXTRA_DELIMITER` | Syntax Errors | local singular subset of delimiter authority | applied only when exactly one parse-valid removal exists |
| `NORMALIZE_TABS` | Indentation & Block Structure | `PY-IND-001`, `IND-001` | deterministic whitespace normalization |

Current Python-only extensions already promoted into `APPLY`:

- `async def` missing colon
- `async for` missing colon
- `async with` missing colon
- `except*` missing colon

## `ADVISE`

Shipped as ranked recommendations only. No automatic mutation.

| Runtime Rule | Python Authority Category | Example Authority IDs | Why It Stays Out Of `APPLY` |
| --- | --- | --- | --- |
| `ELIF_TO_IF_CANDIDATE` | Syntax / Incomplete Constructs | `PY-SYN-003`, `PY-INC-004` adjacent family | not singular enough for automatic mutation |
| `REMOVE_EXTRA_DELIMITER_CANDIDATE` | Syntax Errors | delimiter-repair family from syntax taxonomy | multiple lawful parse-valid outcomes exist |

Candidate ranking model used by the shipped runtime:

1. Python rule precedence
2. edit locality
3. canonical tie-break ordering

`ADVISE` never mutates code automatically.

## `ANALYZE`

Shipped as known bounded analysis surfaces. No automatic mutation.

| Refusal / Analysis Code | Python Authority Category | Example Authority IDs | Why It Is `ANALYZE` |
| --- | --- | --- | --- |
| `return_outside_function` | Control Flow | `PY-CTL-003` family | known invalid state, no safe auto-fix |
| `break_outside_loop` | Control Flow | `PY-CTL-003` family | known invalid state, no safe auto-fix |
| `continue_outside_loop` | Control Flow | `PY-CTL-003` family | known invalid state, no safe auto-fix |
| `undefined_name_unmapped` | Name Resolution | `CATEGORY_03_NAME_RESOLUTION`, `PY-CTX-001` | detection is bounded, correction would guess semantics |
| `assignment_rhs_unmapped` | Incomplete Constructs / Data Flow | incomplete-construct family | semantic completion required |
| `trailing_operator_unmapped` | Incomplete Constructs / Logic Intent | operator family | semantic operand completion required |
| `input_contains_nul` | Input Contract | runtime authority only | outside admissible source contract |
| `input_too_large` | Input Contract | runtime authority only | outside release boundary |
| `correction_loop_detected` | Runtime Safety | runtime authority only | safety refusal, not a user-visible correction |
| `correction_budget_exhausted` | Runtime Safety | runtime authority only | bounded engine termination |

## `ROADMAP`

Known Python authority surfaces deliberately not shipped into automatic mutation.

| Taxonomy Surface | Authority Basis | Current Reason |
| --- | --- | --- |
| Logic intent rewrites such as `=` to `==` in conditionals | `CATEGORY_14_LOGIC_INTENT`, `PY-LOG-001` | too semantic for current Enter-trigger product surface |
| Name typo normalization beyond exact bounded cases | `CATEGORY_03_NAME_RESOLUTION`, typo families | can drift into intent inference |
| Type misuse rewrites | `CATEGORY_04_TYPE_MISUSE` | not line-local enough for current trust contract |
| Import/module corrections | `CATEGORY_11_IMPORT`, `IMP-*` | import mutation changes program surface materially |
| API misuse rewrites | `CATEGORY_15_API_MISUSE`, `API-*` | often require contextual judgment |
| Security-sensitive rewrites | `CATEGORY_17_SECURITY`, `SEC-*` | must not auto-mutate security posture silently |
| Performance rewrites | `CATEGORY_18_PERFORMANCE`, `PRF-*` | optimization intent is not always the operator’s intent |
| Concurrency / async semantic rewrites beyond syntax | `CATEGORY_13_CONCURRENCY`, `PY-ASY-*` | can change execution semantics |
| Intent completion patterns | `python_complete_finite_mapper.py` Layer 4 | explicitly outside current Python product boundary |

## Promotion Law

A rule graduates from `ROADMAP`, `ANALYZE`, or `ADVISE` into `APPLY` only when:

- the authority category is finite and documented
- the exact runtime shape is singular
- the correction is line-local or bounded-local
- the correction is idempotent
- valid Python never changes
- parse/reparse validation proves the output
- tests prove no hidden mutation in non-apply lanes
- release qualification and reproducibility remain intact

Until then, the rule stays visible but non-mutating.
