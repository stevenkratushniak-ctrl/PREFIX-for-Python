# ITERATION_IN_CONNECTOR Boundary
Authority: ITERATION_IN_CONNECTOR_V2. Mutation primitive: insert exactly one literal token `in` plus required separating whitespace. Existing non-whitespace tokens remain byte-for-byte and in order.

Inside: for/async-for headers and for-clauses in list/set/dict comprehensions and generator expressions. Detection starts only after Python 3.12 rejects the proposal. Candidate gaps are confined to one governing clause and every candidate is reparsed through existing AST authority.

Outside: membership expressions, malformed targets/iterables, with/import/except syntax, lexical text. Comments, strings and f-string literal text are never insertion sites. A valid source is never changed.