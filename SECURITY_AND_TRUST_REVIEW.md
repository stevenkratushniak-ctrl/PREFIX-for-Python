# SECURITY AND TRUST REVIEW

## Scope

This review covers the shipped `PREFIX for Python` product root only.

## Trust Surface Summary

- local-first engine
- no network dependency in the Python package
- no telemetry code in the Python package
- no cloud or model call path in the correction engine
- explicit subprocess boundary only in the VS Code extension, which shells out to the configured local Python interpreter

## Filesystem Behavior

- scan mode reads input only
- `--apply` writes only to the declared target file
- writes are atomic via temp-file replace in the target directory
- apply writes emit receipts in a sibling `.prefix-python-receipts` directory unless the user configures another receipt directory
- apply receipts include deterministic lineage ids, chain hashes, before/after authority snapshots, and replay contracts
- rollback requires a receipt and target match
- rollback refuses invalid preimages rather than silently re-committing invalid syntax
- replay refuses divergence rather than trusting stale or mutated receipt payloads
- symlink writes are refused

## Process Behavior

- Python engine: no subprocess execution
- CLI: no subprocess execution
- VS Code extension: one bounded subprocess call to `python -m prefix_python --stdin --json`

## Network Behavior

Targeted source scan results:

- no `requests`
- no `urllib`
- no `socket`
- no `fetch`
- no `XMLHttpRequest`
- no `openai`
- no telemetry or analytics imports in shipped source surfaces

## Secret Review

Targeted secret-pattern scan over the product root found no matches for:

- API keys
- PEM private key headers
- `OPENAI_API_KEY`
- `password =`
- `secret =`
- `token =`

## Determinism Review

- accepted outputs are parse/reparse validated under Python `3.12`
- accepted outputs include AST legality reports and deterministic proof traces
- refused paths do not mutate the target
- wheel and VS Code package raw archive bytes drift across rebuilds because of zip timestamp variance
- canonicalized archive bytes are stable across repeated rebuilds and must be used as the authoritative release verification surface

## Remaining Risk Notes

- The extension trusts the user-configured Python interpreter path. That is a deployment trust decision, not an engine-side heuristic.
- Full interactive VS Code host testing is not covered by the current automated evidence set.
