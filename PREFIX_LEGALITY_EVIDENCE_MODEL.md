# PREFIX Legality Evidence Model

PREFIX exposes why an outcome was lawful, advised, analyzed, or refused.

## Evidence Surfaces

Accepted transitions carry:

- AST hash
- token hash
- legality report
- construction signature
- transition witness root
- parse/reparse validation flag

All outcomes carry:

- lane
- state
- structural context
- legality score
- continuation graph
- transition governance

## Legality Score

The score is not probabilistic confidence.

It is a deterministic product signal derived from:

- lane
- status
- event count
- candidate count
- parse/reparse validation
- governing law
- surface class

`APPLY` outcomes score highest because mutation is structurally admitted.

`ADVISE` outcomes score lower because the system sees continuations but refuses mutation.

`ANALYZE` and `ROADMAP` outcomes score lower because mutation is not admitted.

## Operator Meaning

The score explains admissibility strength. It never authorizes mutation by itself.

