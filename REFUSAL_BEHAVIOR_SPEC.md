# REFUSAL BEHAVIOR SPEC

## Typed Outcomes

`PREFIX for Python` emits exactly one of these public outcomes:

- `ACCEPT_VALID`
- `ACCEPT_FIXED`
- `REFUSE_UNMAPPED`
- `REFUSE_AMBIGUOUS`
- `REFUSE_INVALID`

## Contract

- `ACCEPT_VALID`
  - parse-valid and reparse-valid
  - no mutation required
- `ACCEPT_FIXED`
  - exactly one deterministic structural repair path exists
  - repaired text is parse-valid and reparse-valid
  - file mutation occurs only when the caller explicitly invokes `--apply` or the VS Code command applies the returned text
- `REFUSE_UNMAPPED`
  - no mapped deterministic repair exists
  - no mutation occurs
- `REFUSE_AMBIGUOUS`
  - multiple lawful repairs exist, or the product has candidate-only repairs that are intentionally not auto-authoritative
  - no mutation occurs
- `REFUSE_INVALID`
  - input is outside the admissible surface or violates a hard enforcement rule
  - no mutation occurs

## Refusal Classes Proven In This Release

- `input_contains_nul`
- `input_too_large`
- `input_decode_error`
- `return_outside_function`
- `continue_outside_loop`
- `break_outside_loop`
- `orphaned_else`
- `undefined_name_unmapped`
- `rollback_preimage_invalid`
- `rollback_postimage_mismatch`
- `rollback_commit_failed`
- `apply_commit_failed`
- `replay_diverged`
- `replay_postimage_mismatch`
- `replay_requires_apply_receipt`
- `write_symlink_refused`
- `unsupported_syntax_state`

## Candidate Behavior

Candidate surfaces are never auto-applied.

Current candidate-only rule:

- `ELIF_TO_IF_CANDIDATE`

Current ambiguous/multi-repair surface:

- extra closing delimiter removal when more than one parse-valid removal path exists

## CLI Exit Behavior

- exit `0`
  - `ACCEPT_VALID`
  - `ACCEPT_FIXED`
- exit `2`
  - any refusal outcome

## Mutation Rules

- scan path: never writes
- stdin path: never writes
- `--apply`: writes only for `ACCEPT_FIXED`
- rollback: writes only when the receipt target matches, the receipt is intact, and the receipt preimage is parse-valid under Python 3.12 authority
- receipt replay: never writes, reruns the engine on stored preimage text, and refuses if replay diverges from the stored accepted evidence
- receipt inspection: never writes, surfaces lineage and chain data only

## User-Facing Error Discipline

- no generic exceptions are exposed as intended user behavior
- refusal payloads are machine-readable JSON under `--json`
- refusal payloads preserve `refusal_code`, `refusal_reason`, and any surfaced candidates
- receipt write failures and rollback write failures are converted into refusal payloads instead of raw process crashes
