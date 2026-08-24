# PREFIX Transition Admissibility Model

`PREFIX for Python` treats each edit as a transition request from one Python structure to another.

## Admissibility Requirements

A transition is admissible for mutation only when all of the following are true:

- the source is within the bounded Python input contract
- the transition has a pinned deterministic rule
- the transition is line-local or bounded-local
- the result parses under Python 3.12
- the AST legality report has zero violations
- parse/reparse validation succeeds
- the transition is idempotent
- no semantic value, name, import, type, or intent is invented

## Runtime Witness

The engine emits `transition_governance` with:

- `governing_law`
- `local_mutation_boundary`
- `structural_witness_sha256`
- `continuation_graph_sha256`
- `transition_witness_root_sha256`

The witness root ties the structural context to the continuation graph. If either changes, the witness changes.

## Refusal Is Admissible

Refusal is not failure. It is the correct outcome when admissibility cannot be proven.

