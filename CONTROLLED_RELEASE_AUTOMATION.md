# CONTROLLED RELEASE AUTOMATION

## Objective

Automate the controlled founding-operator release without turning PREFIX into a generic sales system.

## Automated Surfaces

The operator console automates:

- invite generation
- evaluation-license generation
- cohort activation
- checkpoint recording
- issue collection
- expiration tracking
- reminder generation
- conversion reporting
- release distribution manifests

## Release Distribution Rule

Every enrolled team receives a distribution record pinned to the canonical bundle:

- bundle path
- bundle sha256
- evaluation license id
- team id

This ensures distribution stays tied to the exact release that was approved.

If the pinned bundle is missing or hash-mismatched, report generation is refused.

## Reminder Logic

The system generates reminders for:

- onboarding checkpoint due by day 3
- demo walkthrough due by day 7
- replay validation due by day 14
- rollback validation due by day 14
- conversion review window within nine days of expiry
- expired evaluations requiring closure or conversion

## Expiration Tracking

Expiration is deterministic:

- evaluation start date is explicit
- duration is explicit
- end date is computed
- reports use explicit `--as-of` dates
- checkpoints and issue records outside the evaluation term are refused

No hidden clocks are used in the decision model.

## Operational Evidence

The demo evidence workspace is stored at:

- `qualification/_hardening_artifacts/operator_console_demo`

Generated reports include:

- `qualification/_hardening_artifacts/operator_console_demo/reports/cohort-summary-2026-05-21.json`
- `qualification/_hardening_artifacts/operator_console_demo/reports/conversion-summary-2026-05-21.json`
- `qualification/_hardening_artifacts/operator_console_demo/reports/distribution-manifest-2026-05-21.json`

Each report is tied to a deterministic `workspace_fingerprint`.
