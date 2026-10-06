# Import Forward Taxonomy
|ID|Family|State|Evidence|Class|Runtime/env?|
|---|---|---|---|---|---|
|IMP-LEX-001|lexical|grammar-valid import|tokenize+parse+AST|ADMISSIBLE|no|
|IMP-LEX-002|lexical|missing mandatory import after from-target|bounded insertion enumeration+reparse|INADMISSIBLE if unique|no|
|IMP-LEX-003|lexical|missing as in alias-looking sequence|tokens/reparse|AMBIGUOUS|no|
|IMP-LEX-004|lexical|malformed comma/target list|tokens/reparse|AMBIGUOUS/OUTSIDE|no|
|IMP-LEX-005|lexical|unbalanced import parentheses|existing delimiter authority|V1-governed if singular|no|
|IMP-MOD-001|module|target found by pinned resolver snapshot|spec/provenance|ADMISSIBLE-EVIDENCE|yes|
|IMP-MOD-002|module|target unresolved in pinned environment|resolver snapshot|ENVIRONMENT-INCOMPLETE/UNKNOWN|yes|
|IMP-MOD-003|module|same-name alternatives|roots/spec provenance|AMBIGUOUS|yes|
|IMP-MOD-004|module|custom/dynamic finder may govern|finder evidence|AUTHORITY-INSUFFICIENT|yes|
|IMP-SYM-001|symbol|requested name statically declared|source AST|ADMISSIBLE-EVIDENCE|project|
|IMP-SYM-002|symbol|requested name absent statically|AST+dynamic-risk screen|ANALYZE only|possibly|
|IMP-SYM-003|symbol|re-export/__getattr__/runtime mutation|source/runtime evidence|AUTHORITY-INSUFFICIENT|yes|
|IMP-BIND-001|binding|normal import binding|AST|ADMISSIBLE|no|
|IMP-BIND-002|binding|legal explicit alias|AST|ADMISSIBLE|no|
|IMP-BIND-003|binding|collision/shadowing|scope AST|ANALYZE|no for detection|
|IMP-REL-001|relative|relative grammar valid|AST level/module|ADMISSIBLE-STRUCTURE|no|
|IMP-REL-002|relative|package context unestablished|execution context|CONTEXT-DEPENDENT|yes|
|IMP-REL-003|relative|beyond top package in pinned context|package context|CONTRADICTION in snapshot|yes|
|IMP-ENV-001|environment|valid structure, module absent|pinned resolver|ENVIRONMENT-INCOMPLETE|yes|
|IMP-ENV-002|environment|present only in another known env|multiple snapshots|ADVISE/ANALYZE|yes|
|IMP-ENV-003|environment|environment not pinned|missing snapshot|AUTHORITY-INSUFFICIENT|yes|