# PREFIX AST Governance Runtime

`PREFIX for Python` moves toward AST-governed construction while preserving line-local performance.

## Current Runtime

The runtime accepts text as the operator projection, then admits only structures that survive:

- Python 3.12 parse
- compile validation
- token hashing
- AST node registry validation
- parent/child legality checks
- node contract checks
- AST roundtrip equivalence

## Construction Signature

The AST bridge now emits a construction signature with counts for:

- block nodes
- async nodes
- delimiter-sensitive nodes
- scope boundary nodes
- pattern nodes

This signature helps explain structural shape without requiring a full AST dump in operator surfaces.

## Boundary

PREFIX does not rebuild the whole editor model on every keystroke.

Enter-trigger handling stays bounded and invokes the engine only after a narrow structural precheck.

