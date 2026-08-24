# PREFIX Operator Demo Guide

## Purpose

This demo proves PREFIX as a deterministic Python structural-governance runtime for the Controlled Operator Release.

The demo should be run from the standalone root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\PREFIX_PYTHON\demo\PREFIX_GOVERNANCE_SHOWCASE.ps1
```

## What The Demo Shows

### APPLY

The operator provides a mapped invalid Python structure. PREFIX admits exactly one lawful continuation, applies a bounded governed mutation, validates parse/reparse, and writes a receipt.

Evidence:
- `state=APPLIED`
- `lane=APPLY`
- `governing_law=single_lawful_continuation`
- `mutation_performed=true`
- `parse_reparse_validated=true`
- transition witness root present

### ADVISE

The operator provides a structure with a deterministic candidate continuation, but no automatic mutation authority. PREFIX ranks the continuation and withholds mutation.

Evidence:
- `state=ADVISED`
- `lane=ADVISE`
- recommendation packet hash present
- `mutation_performed=false`

### ANALYZE

The operator provides a structure that would require semantic invention to complete. PREFIX identifies the unsafe region and withholds mutation.

Evidence:
- `lane=ANALYZE`
- `governing_law=unsafe_or_unproven_continuation`
- `mutation_performed=false`

### REFUSE

The operator provides an unsupported topology. PREFIX refuses deterministically at the admissibility boundary.

Evidence:
- refusal code present
- `mutation_performed=false`
- transition witness root present

### REPLAY

The receipt is replayed from the stored pre-image and must reproduce the same deterministic engine result.

Evidence:
- `replay_verified=true`
- stored transition hash present
- output hash matches the APPLY output hash

### ROLLBACK

The demo also applies a parse-valid tab-normalization transition and rolls it back through receipt evidence. This proves undo authority without pretending every invalid pre-image is rollback-ready.

Evidence:
- rollback readiness is inspected from the apply receipt
- rollback emits a new receipt
- restored hash is reported
- no network or hidden state is involved

## Operator Reading

The important claim is not "PREFIX fixes everything."

The claim is stricter:

If PREFIX mutates, the mutation is lawful, bounded, replayable, and evidence-bearing.
