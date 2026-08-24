# COHORT MANAGEMENT SYSTEM

## Cohort Model

The cohort model is deterministic and file-backed.

Each cohort is represented by:

- a cohort record
- invite records
- activation records
- checkpoint records
- issue records
- generated reports

## Key Identifiers

- `cohort_id`
- `team_id`
- `invite_id`
- `evaluation_license_id`

All identifiers are content-derived and deterministic.

## Management Actions

The system supports:

- create cohort context through `invite`
- enroll teams through `activate`
- monitor progress through `checkpoint`
- track friction through `issue`
- view state through generated reports

## Operational Questions Answered

The cohort system answers:

- who has been invited
- who is active
- who is nearing expiry
- who is conversion-ready
- which teams need reminders
- which teams warrant enterprise follow-up
- which release bundle each team received
