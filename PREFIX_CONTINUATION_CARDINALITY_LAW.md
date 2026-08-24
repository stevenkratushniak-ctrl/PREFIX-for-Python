# PREFIX Continuation Cardinality Law

Continuation cardinality governs mutation.

## Cardinality Rules

`0` continuations means mutation is refused.

`1` lawful continuation may enter `APPLY` only if the transition also satisfies locality, idempotency, and parse/reparse validation.

`2+` lawful continuations enter `ADVISE`. They are ranked deterministically and never auto-applied.

## Why Cardinality Matters

Cardinality prevents false authority.

When more than one continuation is possible, automatic mutation would encode intent. PREFIX refuses that role.

## Operator Contract

If PREFIX mutates, the continuation was singular.

If PREFIX advises, continuation exists but intent is not singular.

If PREFIX analyzes or refuses, no admitted continuation exists in the shipped runtime.

