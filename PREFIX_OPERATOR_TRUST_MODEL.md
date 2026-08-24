# PREFIX Operator Trust Model

## Product Trust Boundary

`PREFIX for Python` is trustworthy only if the operator can see that:

- correction scope is bounded
- correction authority is structural, not semantic
- refusal is truthful
- mutation is inspectable
- replay is deterministic
- rollback remains available when writes occur

## Trust Surfaces in This Release

- typed outcomes:
  - `ACCEPT_VALID`
  - `ACCEPT_FIXED`
  - `REFUSE_UNMAPPED`
  - `REFUSE_AMBIGUOUS`
  - `REFUSE_INVALID`
- parse/reparse validation on accepted mutations
- AST and token hashes in engine responses
- legality report counts in engine responses
- receipt inspection and replay verification in the CLI
- status-bar trust signaling in VS Code:
  - ready
  - working
  - fixed
  - refused

## Trust Improvements in This Hardening Pass

- Enter-trigger mutation is no longer “any newline plus engine.”
- Selection correction can no longer widen silently to the full document.
- Inserted `pass` is selected immediately on Enter so the operator can replace it without hunting for the mutation.
- Qualification evidence now correctly reports engine status families and idempotency, reducing proof drift between runtime truth and release reporting.

## Operator Promise

The operator should be able to trust:

- lawful Python was preserved if PREFIX did nothing
- lawful Python was restored if PREFIX corrected
- ambiguity or unsupported structure existed if PREFIX refused

That is the core trust contract for a deterministic Python prefix layer.
