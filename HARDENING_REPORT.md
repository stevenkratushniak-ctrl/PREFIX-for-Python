# HARDENING REPORT

## Scope

This report covers only `PREFIX for Python` in `C:\PREFIX_PYTHON`.

## Hardening Changes Completed

1. Engine outcome taxonomy was hardened from generic `valid/corrected/refused` into:
   - `ACCEPT_VALID`
   - `ACCEPT_FIXED`
   - `REFUSE_UNMAPPED`
   - `REFUSE_AMBIGUOUS`
   - `REFUSE_INVALID`
2. The AST bridge was replaced with a real Python 3.12 authority layer:
   - `prefix_python.ast_bridge.parse_to_ast`
   - `prefix_python.ast_bridge.validate_source_text`
   - `prefix_python.ast_bridge.validate_ast_legality`
   - parse + compile validation
   - parent/child legality checks
   - block-body non-emptiness checks
   - token-stream hashing
   - source-position continuity checks
   - parse/reparse validation via `ast.unparse()` roundtrip
   - node-type allowlist pinned to Python `3.12`, including `TypeAlias`, `TryStar`, and `match_case`
3. Auto-apply repair surface was narrowed to deterministic structural rules only:
   - `MISSING_COLON`
   - `AUTO_INDENT`
   - `INSERT_PASS`
   - `CLOSE_DELIMITER`
   - `REMOVE_EXTRA_DELIMITER` when singular
   - `NORMALIZE_TABS`
4. Risky semantic placeholder repairs were removed from auto-apply:
   - assignment RHS completion now refuses
   - trailing operator completion now refuses
   - orphaned `elif` is candidate-only, never auto-applied
5. CLI behavior was hardened:
   - `--apply` added as the authoritative mutation path
   - receipt-backed apply path added
   - receipt-backed rollback path added
   - receipt inspection path added
   - deterministic replay path added
   - receipt lineage and chain hashes added
   - before/after AST authority snapshots added to receipts
   - rollback refuses invalid preimages rather than silently re-committing invalid syntax
   - symlink writes remain refused
6. VS Code extension behavior was hardened:
   - typed outcome handling
   - candidate-aware refusal messaging
   - pure behavior helpers added and tested separately
7. Broken example fixtures were converted from invalid `.py` files to `.txt` fixtures so compile validation can honestly cover the shipped Python source tree.

## Contradictions Removed

- The shipped rule catalog no longer says `DEFER TO AI RANKING`.
- Public README and launch materials no longer expose `AutoFix` naming as the public product identity.
- The product no longer claims assignment-RHS or trailing-operator placeholder insertion as release behavior.
- The AST bridge is no longer a stub.

## Validation Evidence

- `python -m unittest discover -s tests -q`
  - result: `34` tests passed, `0` failed
- `py_compile` sweep over shipped Python source tree
  - result: passed after broken example fixtures were converted to `.txt`
- `npm run build`
  - result: passed
- `npm run test:behavior`
  - result: passed
- `npm run package`
  - result: passed

## Release Engineering Note

Raw wheel and raw VS Code package bytes are not reproducible across rebuilds because archive timestamps vary. Canonicalized archive bytes are stable across repeated rebuilds and the authoritative bundle now exists at `release/prefix-python-0.1.0-rc2`.
