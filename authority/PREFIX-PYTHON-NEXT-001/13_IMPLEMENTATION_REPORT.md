# Implementation Report
Status: NOT IMPLEMENTED in this campaign branch.

Reason: repository mutation access is available, but this execution environment cannot clone/run the repository or its Python 3.12 qualification suite (network is unavailable to the container, and the GitHub connector is repository-object access rather than an executable workspace). The assignment explicitly permits an implementation-ready work order when safe isolated implementation/qualification is unavailable. Shipping unexecuted engine changes would violate the APPLY standard.

Mechanical work order:
1. Branch from the pinned authority-map commit; do not touch release/ artifacts or editor/vscode authority.
2. Add engine helpers that tokenize source, identify only the two V2 governing constructs, enumerate connector insertion gaps deterministically, and re-run validate_source_text for every candidate.
3. Promote only candidate_count==1 plus surface-specific AST invariant to a CorrectionEvent; candidate_count>1 must be non-mutating ADVISE; zero stays ROADMAP.
4. Add stable rule IDs INSERT_ITERATION_IN_V2 and INSERT_EXCEPT_ALIAS_AS_V2 and an authority_version field or equivalent versioned proof metadata without changing V1 event meaning.
5. Preserve the editor-neutral engine contract. VS Code and JetBrains adapters consume outcomes; no adapter owns these rules.
6. Add tests before promotion; do not alter packages/installers/version/public release.