# PREFIX for Python v0.1.0-rc2

Deterministic Python prefix layer for bounded correctness.

## Release Posture

This is a Controlled Operator Release for selected engineering teams.

Recommended public frame:

- Controlled Operator Release
- Private Operator Release
- 30-Day Evaluation
- Apply for access

## What This Release Is

- local-first
- refusal-capable
- requires CPython `3.12.x`
- validated on CPython `3.12.6`
- Python `3.12` AST-authoritative
- bounded to deterministic structural correction
- Enter-triggered inside VS Code for mapped `ALWAYS_SAFE` Python block-structure states
- receipt-backed for rollback, inspection, and replay
- suitable for selected engineering-team evaluation
- proof-driven onboarding included for the 30-day evaluation period
- commercial use after evaluation requires a paid license

## Compatibility Lock

- Supported runtime boundary: `>=3.12,<3.13`
- Python `3.11`, `3.13`, and `3.14` are outside rc2 support
- Python `3.13` and `3.14` require separate AST authority catalogs before support can be claimed

## What It Is Not

- AI autocomplete
- copilot software
- probabilistic repair
- best-effort fixing
- hidden mutation

## Included Artifacts

- `release/prefix-python-0.1.0-rc2/prefix_python-0.1.0-py3-none-any.whl`
- `release/prefix-python-0.1.0-rc2/prefix-python-0.1.0.vsix`
- `release/prefix-python-0.1.0-rc2/RELEASE_VERIFICATION_MANIFEST.json`
- `release/prefix-python-0.1.0-rc2/SHA256SUMS.txt`
- `release/prefix-python-0.1.0-rc2.zip`

## Canonical Verification

- zip sha256: `7a92c318ce9be3f93ba97d319d2d1d1ebcba323205b4690c669e70485fb5d82d`
- bundle manifest sha256: `0bc2aeee84d392d376fa52424b697887bad1bc1affd5b3cda5baaba80db961bb`
- bundle SHA256SUMS sha256: `20834482597a1b9af65b7cb082e9573d32cbb41c4a532d3d751a404ea676c220`
- standalone wheel sha256: `feb085394d9a441d8202e546f2f9c55fd43c2aeaf735e5bb564c455636042b4a`
- standalone VSIX sha256: `02a332530f55ff785e7f41d5e8004245c21033e7ea27e54dc2df586db757e4bf`
- canonicalized bundle wheel sha256: `ade524310084b6b8c6532ff48efa0524f0c7456293b6ecc6233606ab8d2d697e`
- canonicalized bundle VSIX sha256: `e76ab64f9ffc60ca356a57065fa95079cb1aa7a1defe9e6f40efa7ee93a1edd2`

## Validation Summary

- Python unit tests: `55/55` passed
- Python compile sweep: passed
- VS Code extension build: passed
- VS Code behavior test: passed
- VS Code package build: passed
- release qualification: passed
- release ZIP checksum verification: passed
- release ZIP-only install validation: passed
- targeted secret scan: clean
- targeted purity scan: clean
- launch-doc link scan: clean

## Core Product Guarantees

- invalid AST states must not commit
- one deterministic correction or refusal
- ambiguity => refusal
- parse/reparse validation mandatory
- receipts mandatory for applied mutations
- deterministic replay supported from receipts

## Caveat

Full interactive VS Code extension-host GUI testing remains outside the automated evidence set.
