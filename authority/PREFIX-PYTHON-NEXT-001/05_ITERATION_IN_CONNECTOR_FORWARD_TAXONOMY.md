# ITERATION_IN_CONNECTOR Forward Taxonomy
F0 VALID: connector already lawful -> ADMISSIBLE.
F1 MISSING_UNIQUE: absent; exactly one bounded insertion reparses and satisfies the expected ast.For/ast.AsyncFor/comprehension node with preserved target and iterable token subsequences -> INADMISSIBLE with one successor.
F2 MISSING_MULTI: 2+ legal insertion successors -> AMBIGUOUS.
F3 MISSING_ZERO: no insertion legalizes -> OUTSIDE AUTHORITY.
F4 OTHER_SYNTAX: another malformed token/state governs -> OUTSIDE AUTHORITY.
F5 LEXICAL_SHADOW: apparent construct occurs in comment/string/f-string literal text -> non-target.
F6 VALID_OTHER_MEANING: source already parses -> ADMISSIBLE, unchanged.