# PREFIX Continuation Graph Model

The continuation graph is a deterministic description of available next structural states.

## Graph Types

`APPLY` creates one applied successor when a single lawful continuation exists.

`ADVISE` creates one or more ranked candidate successors.

`ANALYZE` and `ROADMAP` create zero successors because no runtime continuation is admitted.

## Runtime Fields

The engine emits:

- `continuation_kind`
- `successor_count`
- `successors`
- `refusal_code`
- `graph_sha256`

The graph is intentionally small. It is not a speculative search tree.

## Bounded Branching

PREFIX does not explore arbitrary futures.

It only represents continuations already surfaced by deterministic Python rule authority.

