# PREFIX Rule Lane Model

`PREFIX for Python` is not a flat fixer. It is a deterministic Python prefix layer with explicit rule lanes.

## Authority Sources

This lane model is derived from the inspected finite Python taxonomy authority that informed this sealed product release:

- the 20-category Python taxonomy
- the extreme-pattern catalog
- the finite error-map schema
- the complete finite mapper notes

That authority establishes the bounded Python category surface. `PREFIX for Python` does not enable those rules wholesale. It classifies them before shipping them.

The standalone product does not depend on any external taxonomy root at runtime. The release-contained lane model and rule catalog are the operator-facing authority surfaces for this build.

## Product Lanes

### `APPLY`

`APPLY` is the only mutation lane.

A rule enters `APPLY` only when all of the following are true:

- Python-only
- deterministic
- line-local or bounded-local
- idempotent
- non-semantic
- parse/reparse validated
- no intent inference
- no import generation
- no type guessing
- no architecture rewrite
- no security/performance “optimization” guess

Current `APPLY` examples:

- missing block colons
- empty-block stabilization with `pass`
- required indentation normalization
- singular unmatched delimiter completion
- singular extra closing delimiter removal
- tab-to-space normalization

### `ADVISE`

`ADVISE` is the ranked recommendation lane.

Rules in `ADVISE` are:

- real
- bounded
- deterministic to detect
- not safe to auto-apply
- surfaced as ranked candidates
- never applied automatically

`ADVISE` is for situations where PREFIX can see lawful continuations but cannot claim singular `ALWAYS_SAFE` authority.

Current `ADVISE` examples:

- orphaned `elif` promotion candidate
- ambiguous delimiter-removal candidate sets

### `ANALYZE`

`ANALYZE` is the bounded explanation lane.

Rules in `ANALYZE` are:

- known to the Python finite authority
- detectable without guessing
- not eligible for auto-apply
- often not candidate-generating
- returned as calm, truthful non-mutation surfaces

Current `ANALYZE` examples:

- `return` outside function
- `break` outside loop
- `continue` outside loop
- unresolved module-level name
- assignment without right-hand side
- trailing operator requiring semantic completion
- NUL-byte input
- oversized input beyond release contract

### `ROADMAP`

`ROADMAP` contains known Python authority surfaces not yet promoted into the shipped runtime.

Rules may live in taxonomy authority but remain outside the current product until they satisfy promotion criteria and validation.

Examples:

- broader typo families
- compatibility rewrites not yet proven line-local in this runtime
- logic, context, and performance classes that are real but not yet safe enough for product promotion

## Runtime State Model

The operator-facing runtime states remain simple:

- `APPLIED`
- `ADVISED`
- `REFUSED`

State mapping:

- `APPLY` lane → `APPLIED`
- `ADVISE` lane → `ADVISED`
- `ANALYZE` lane → `REFUSED`
- `ROADMAP` lane → `REFUSED`

## Promotion Criteria Into `APPLY`

A Python rule may move into `APPLY` only when all of the following are proven on disk:

1. finite authority source exists
2. exact rule shape is documented
3. singular lawful continuation exists
4. correction is idempotent
5. correction is line-local or bounded-local
6. valid Python is preserved
7. parse/reparse validation passes
8. negative tests prove non-application on ambiguous states
9. CLI and VS Code tests prove no hidden mutation outside the allowed surface
10. qualification and reproducibility outputs remain stable

If any of the above fails, the rule remains in `ADVISE`, `ANALYZE`, or `ROADMAP`.

## Non-Negotiable Law

`ADVISE` and `ANALYZE` make PREFIX feel broader and smarter.

They do not weaken trust.

Only `APPLY` mutates code.
