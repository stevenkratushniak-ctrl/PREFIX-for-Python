# PREFIX AST Distance Scoring

AST distance scoring is a deterministic support model for future candidate ordering.

The current shipped runtime uses rule priority, edit locality, and canonical tie-break ordering. It does not yet use a full AST edit-distance engine.

## Current Runtime Scoring

Candidate score is deterministic and based on:

- rule priority
- first changed column
- text delta size
- canonical rule and text ordering

## Future AST Distance Criteria

A future rule may incorporate AST distance only if it remains:

- deterministic
- bounded
- explainable
- reproducible
- non-semantic

## Promotion Boundary

AST distance may rank candidates.

AST distance alone may not authorize mutation.

