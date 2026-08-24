# RELEASE READINESS REPORT

## Current State

`PREFIX for Python` is hardened enough to support a bounded public launch through the canonicalized release bundle at `release/prefix-python-0.1.0-rc2`.

## Evidence

- Python unit test suite: passed (`34/34`)
- Python source compile sweep: passed
- CLI smoke coverage: scan, apply, rollback, receipt inspection, and deterministic replay paths exercised successfully
- VS Code extension build: passed
- VS Code behavior helper test: passed
- VS Code package: passed
- secret-pattern scan: no matches
- broken-reference scan for root markdown links: no missing local targets detected in scanned launch docs and README

## Release Gate Decision

### Public launch decision

- Raw artifact bytes: `NOT READY` as authoritative verification surface
- Canonicalized release bundle: `READY`

## Why The Raw Artifacts Are Not The Authority Surface

Two repeated checks showed that:

- raw wheel hashes drift across rebuilds
- raw VSIX hashes drift across rebuilds

The underlying content normalizes to stable canonical archive hashes after timestamp-neutral repacking. Public release verification must therefore publish the canonicalized bundle hashes rather than the raw build-step hashes.

## Canonical Release Bundle

- bundle directory: `C:\PREFIX_PYTHON\release\prefix-python-0.1.0-rc2`
- bundle zip: `C:\PREFIX_PYTHON\release\prefix-python-0.1.0-rc2.zip`
- canonical wheel hash: `10d93e39a1dee2bf482fcae2385b11921e0698ab51ac5022645a76371dc1735e`
- canonical VSIX hash: `11320bb75a91e7c352150da507d8966af64021e93c37ee27dcd6187f939d30a4`
- authoritative full-bundle verification: `release/prefix-python-0.1.0-rc2/SHA256SUMS.txt`
- canonical bundle zip reproducibility check: two consecutive rebuilds produced the same zip hash

## Remaining Gaps

1. Full interactive VS Code extension-host GUI testing remains outside the automated evidence set.
2. Release readiness must be asserted from the canonicalized release bundle, not the raw build outputs.
