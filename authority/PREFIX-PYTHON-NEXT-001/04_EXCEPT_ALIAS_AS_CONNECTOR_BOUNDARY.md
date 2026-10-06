# EXCEPT_ALIAS_AS_CONNECTOR Boundary
Authority: EXCEPT_ALIAS_AS_CONNECTOR_V2. Mutation primitive: insert exactly one literal token `as` plus required separating whitespace. Existing non-whitespace tokens remain byte-for-byte and in order.

Inside: except and except* headers with an exception expression followed by a legal alias-name token but lacking as. Detection starts only after Python 3.12 rejects the proposal. Candidate gaps are confined to one governing clause and every candidate is reparsed through existing AST authority.

Outside: with/import/pattern as, malformed exception expressions, alias renaming, bare except. Comments, strings and f-string literal text are never insertion sites. A valid source is never changed.