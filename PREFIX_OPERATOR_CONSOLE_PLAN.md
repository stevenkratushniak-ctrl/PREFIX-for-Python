# PREFIX OPERATOR CONSOLE PLAN

## Purpose

`PREFIX for Python` includes a deterministic operator console for the Founding Operator Cohort.

This is not a CRM and not a general admin dashboard.

It is a file-backed operational command layer for:

- pilot invitations
- cohort enrollment
- evaluation activation
- checkpoint tracking
- issue logging
- expiration monitoring
- conversion readiness
- release distribution manifests

## Design Law

The console must feel like infrastructure, not SaaS clutter.

That means:

- command-first
- canonical JSON outputs
- deterministic IDs
- explicit dates
- explicit bundle hash verification
- no hidden background jobs
- no opaque scoring
- no random invitation tokens

## Entrypoints

Installed script:

```powershell
prefix-python-ops --help
```

Module form:

```powershell
python -m prefix_python.operator_console --help
```

## Commands

- `init`
- `invite`
- `activate`
- `checkpoint`
- `issue`
- `cohort-summary`
- `reminders`
- `conversion-summary`
- `distribution-manifest`

## Workspace Layout

Each operator workspace is deterministic and local-first:

```text
pilot_ops/
├── program.json
├── cohorts/
├── invites/
├── enrollments/
├── checkpoints/
├── issues/
├── events/
└── reports/
```

## Hardening Rules

- `init` verifies the release bundle exists and matches the supplied hash when one is provided.
- `invite` refuses empty team data, invalid operator emails, invalid seat counts, invalid durations, and duplicate team creation.
- `activate` refuses activation outside the invited evaluation window.
- `checkpoint` and `issue` refuse records outside the evaluation term.
- report generation refuses to succeed if the pinned release bundle is missing or hash-mismatched.
- generated reports include a deterministic `workspace_fingerprint`.

## Evidence Model

- `program.json` pins the release bundle and evaluation defaults.
- `invites/` stores deterministic invitation and evaluation-license records.
- `enrollments/` stores activated teams.
- `checkpoints/` stores evaluation progress.
- `issues/` stores operator-reported issues.
- `events/` stores deterministic event summaries derived from canonical payloads.
- `reports/` stores generated cohort, reminder, conversion, and distribution outputs.

## Why No Web Dashboard

A web dashboard would add session state, UI complexity, and unnecessary drift.

The operator console keeps the release program:

- local-first
- inspectable
- scriptable
- deterministic
- compatible with internal ops review

## Validation Surface

The console is covered by `tests/test_operator_console.py` and exercised in the evidence workspace under `qualification/_hardening_artifacts/operator_console_demo`.
