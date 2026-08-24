# PREFIX Constrained Transition Engine

The constrained transition engine is the runtime path that converts an edit request into `APPLY`, `ADVISE`, `ANALYZE`, or `ROADMAP`.

## Execution Order

1. Normalize bounded input surfaces.
2. Validate current Python structure.
3. Apply singular deterministic transitions when admitted.
4. Surface ranked candidates when mutation is not singular.
5. Analyze known unsafe or semantic surfaces without mutation.
6. Refuse unmapped surfaces.

## Mutation Boundary

Only `APPLY` mutates.

`ADVISE`, `ANALYZE`, and `ROADMAP` are non-mutating.

## Replay Boundary

Receipts continue to store engine output. Because transition governance and continuation graphs are part of the engine result, replay also verifies the structural evidence surface.

