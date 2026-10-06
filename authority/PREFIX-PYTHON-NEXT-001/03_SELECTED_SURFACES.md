# Selected Surfaces
## ITERATION_IN_CONNECTOR_V2
Missing mandatory `in` in for/async-for statement headers and comprehension/generator iteration clauses. Insertion-only, token-preserving, construct-scoped candidate enumeration. APPLY only at successor cardinality exactly 1.

## EXCEPT_ALIAS_AS_CONNECTOR_V2
Missing mandatory `as` between exception expression and alias target in except/except* headers. Same insertion-only/cardinality rule plus AST proof of handler alias binding.

This is not generalized “missing keyword repair.” With-items, imports, calls, parameters, arbitrary expressions and semantic typo repair remain outside authority.