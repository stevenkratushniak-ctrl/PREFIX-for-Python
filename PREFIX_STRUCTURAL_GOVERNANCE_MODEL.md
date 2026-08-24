# PREFIX Structural Governance Model

`PREFIX for Python` governs transition requests. It does not describe itself as a code fixer.

Every runtime outcome is classified by structural law:

- `APPLY`: one lawful continuation exists and mutation is admissible.
- `ADVISE`: bounded continuations exist, but mutation is not admissible.
- `ANALYZE`: the surface is known, but no lawful continuation is proven.
- `ROADMAP`: the surface is outside the shipped runtime.

## Runtime Evidence

The engine now emits a `structural_context` object for every outcome.

This context records:

- `surface_class`
- `governing_law`
- `locality`
- `event_count`
- `refusal_code`
- `source_line_count`
- `witness_sha256`

## Governance Classes

`already_lawful` means the submitted Python state is accepted without mutation.

`single_lawful_continuation` means a bounded local transition was proven and applied.

`multiple_lawful_continuations` means candidates exist, but no mutation occurs.

`unsafe_or_unproven_continuation` means the state is understood but mutation would require guessing.

`unmapped_surface` means the current runtime has no shipped authority for the transition.

## Product Law

Mutation is never justified by convenience. Mutation is justified only by structural admissibility.

