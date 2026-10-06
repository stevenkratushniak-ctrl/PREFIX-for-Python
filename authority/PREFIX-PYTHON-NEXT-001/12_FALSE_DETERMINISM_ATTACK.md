# False Determinism Attack
Attack standard: valid neighbors, malformed neighbors, nesting, whitespace/comments/strings/f-strings, decorators, comprehensions, lambdas, async, classes/closures/imports/shadowing, *args/**kwargs, positional/keyword-only, matching, repeat correction, V1 interaction, competing repairs, runtime knowledge.

## ITERATION_IN_CONNECTOR
Survives only with construct-scoped gap enumeration and token preservation. Test simple/nested for; async for; tuple/starred targets; list/set/dict/generator comprehensions; multiple for clauses; filters; lambdas as iterable expressions; comments/newlines; strings/f-strings containing “for”; existing legal `in`; malformed target; missing iterable; missing colon plus missing in; unmatched delimiters plus missing in. If more than one `in` insertion legalizes, demote to ADVISE.

## EXCEPT_ALIAS_AS_CONNECTOR
Survives only for a legal alias-name token and AST handler-alias proof. Test except and except*; qualified exception expressions; tuples; nested try; comments/spacing; strings/f-strings; already-valid alias; bare except; malformed type; missing colon plus missing as; multiple handlers; match/with/import “as” neighbors. Any alternate legal insertion gap destroys APPLY.

## Candidates killed
Missing comma: `f(a b)`-shaped failures can represent omitted operator/comma or other edits. Unterminated strings: close/escape/triple-string intent competes. With/import missing-as: comma can create another lawful construct. Conditional `=`: `==` and `:=` differ semantically. Call/signature binding repairs require reorder/delete/name/default intent. Dedent repair can change block ownership. No killed family may enter APPLY through generic syntax-message matching.