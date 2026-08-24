# FOUNDING OPERATOR OPERATIONS

## Operating Model

The Founding Operator program is run through deterministic local commands, not manual spreadsheets.

The lifecycle is:

1. initialize operator workspace
2. generate invite and evaluation license
3. activate the invited team
4. record checkpoints
5. log issues
6. generate cohort and reminder reports
7. generate conversion and enterprise follow-up reports
8. generate release distribution manifest

## Initialize the Program Workspace

```powershell
prefix-python-ops init --root .\pilot_ops --release-bundle .\release\prefix-python-0.1.0-rc2.zip
```

If a release hash is supplied, it must match the bundle on disk or initialization is refused.

## Invite a Team

```powershell
prefix-python-ops invite --root .\pilot_ops --cohort-name "Founding Operator Cohort" --team-name "Northwind" --operator-name "Avery Lane" --operator-email "avery@northwind.dev" --seat-count 12 --start-date 2026-05-01
```

Outputs:

- deterministic `invite_id`
- deterministic `team_id`
- deterministic `evaluation_license_id`

The console refuses duplicate team creation, empty operator fields, invalid emails, and invalid seat-count or duration values.

## Activate the Evaluation

```powershell
prefix-python-ops activate --root .\pilot_ops --invite-id <invite_id> --activation-date 2026-05-01
```

Activation is refused if the requested activation date falls outside the invited evaluation window.

## Record a Checkpoint

```powershell
prefix-python-ops checkpoint --root .\pilot_ops --team-id <team_id> --checkpoint-date 2026-05-21 --onboarding complete --install complete --demo complete --replay complete --refusal complete --rollback complete --trust-level high --enterprise-interest active --replay-count 8 --refusal-count 3 --rollback-count 2 --open-issues 0
```

Checkpoint records are refused if they predate activation or land outside the evaluation term.

## Record an Issue

```powershell
prefix-python-ops issue --root .\pilot_ops --team-id <team_id> --issue-date 2026-05-18 --severity medium --category install --summary "Initial VSIX trust prompt required acknowledgement." --status resolved
```

Issue records are refused if they predate activation or land outside the evaluation term.

## Generate Reports

```powershell
prefix-python-ops cohort-summary --root .\pilot_ops --as-of 2026-05-21
prefix-python-ops reminders --root .\pilot_ops --as-of 2026-05-21
prefix-python-ops conversion-summary --root .\pilot_ops --as-of 2026-05-21
prefix-python-ops distribution-manifest --root .\pilot_ops --as-of 2026-05-21
```

Generated reports include:

- `bundle_hash_verified`
- deterministic `workspace_fingerprint`
- output derived only from local workspace state

Report generation is refused if the pinned release bundle has disappeared or no longer matches its stored hash.

## Operator Outcome

The operating team gets:

- explicit invite and license records
- explicit activation records
- explicit checkpoint history
- deterministic reminders
- conversion-readiness signal
- release distribution manifest tied to the canonical bundle hash
