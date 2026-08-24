# EVALUATION LIFECYCLE SYSTEM

## Lifecycle Stages

The founding-operator evaluation lifecycle is deterministic and explicit:

1. `invited`
2. `active`
3. `expired`
4. `conversion_ready` is a computed condition, not a free-form label

## Inputs

The lifecycle uses:

- explicit evaluation start date
- explicit activation date
- explicit duration
- explicit checkpoint records
- explicit issue records
- explicit `--as-of` date for reporting

## Hard Boundaries

- activation before the invited start date is refused
- activation after the evaluation end date is refused
- checkpoint records before activation are refused
- checkpoint records after the evaluation end date are refused
- issue records before activation are refused
- issue records after the evaluation end date are refused

## Conversion Readiness Rule

A team is `conversion_ready` only when all of the following are true:

- the evaluation has not expired
- onboarding complete
- install complete
- demo complete
- replay complete
- refusal review complete
- rollback validation complete
- trust level is `medium` or `high`
- open issue count derived from issue records is `0`

## Enterprise Follow-Up Rule

Enterprise follow-up is recommended when any of the following are true:

- the team is conversion-ready
- enterprise interest is `active`
- seat count is `10` or higher

## Lifecycle Outputs

Generated lifecycle outputs:

- cohort summaries
- reminders
- conversion summaries
- distribution manifests

These outputs are local JSON records under `reports/`.
