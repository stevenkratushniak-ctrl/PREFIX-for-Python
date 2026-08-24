# PREFIX Refusal Correctness Model

## Law

PREFIX corrects only when one lawful Python continuation exists inside the mapped deterministic surface.

Otherwise it refuses.

Refusal is a success state.

## Runtime Refusal Guarantees

- unsupported structural states are refused
- ambiguous candidate states are refused
- semantic completion is refused
- multi-cursor Enter mutation is refused
- empty selection correction is refused
- selection correction never widens silently to the full document

## Enter-Path Refusal Boundaries

The VS Code Enter path now refuses when:

- more than one cursor is active
- the operator has an explicit selection
- the edit was not a simple single Enter insertion
- the prior line is not a mapped missing-colon Python header
- the prior line appears to be inside a triple-quoted string
- the prior line appears to be part of a continuation state
- the engine returns an event set outside the bounded Enter surface

## Engine Refusal Boundaries

Document and CLI refusals remain explicit for:

- assignment without right-hand side
- trailing operator completion
- orphaned `else`
- `return` outside a function
- `continue` outside a loop
- `break` outside a loop
- unresolved module-level names
- oversized input
- NUL-byte input
- non-UTF-8 file decode failure

## Why This Matters

PREFIX trust depends on a strict asymmetry:

- if PREFIX corrected the structure, the correction was singular and lawful
- if PREFIX refused, the operator can trust that the system did not silently guess

This is the differentiator from autocomplete or reactive AI tooling.
