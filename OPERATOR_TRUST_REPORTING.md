# OPERATOR TRUST REPORTING

## Trust Signals Collected

The operator console records structured trust-adjacent signals without violating local-first posture:

- replay count
- refusal count
- rollback count
- milestone completion
- operator trust level
- enterprise interest level
- open issue count
- issue severity and category

## Privacy Posture

The system does not require:

- telemetry streaming
- cloud collection
- background monitoring
- editor surveillance

It relies on explicit checkpoint and issue records created by the operating team.

## Trust Reports

Trust posture appears in:

- `cohort-summary`
- `conversion-summary`
- `reminders`

## Why This Matters

Enterprise buyers care about whether the pilot produced:

- deterministic replay usage
- successful refusal handling
- rollback confidence
- low unresolved friction
- consistent operator trust

The reporting layer is designed to make those signals visible without turning PREFIX into instrumentation-heavy software.
