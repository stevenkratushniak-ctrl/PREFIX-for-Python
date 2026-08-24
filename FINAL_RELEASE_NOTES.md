# FINAL RELEASE NOTES

## Product

`PREFIX for Python`

Deterministic Python prefix layer for bounded correctness.

## Release Surface

This release is authorized from the frozen canonical bundle only:

- `release/prefix-python-0.1.0-rc2.zip`

Identity rule:

- Python package and CLI version: `0.1.0`
- Release bundle revision: `0.1.0-rc2`
- `rc2` identifies the controlled release bundle revision, not a different Python package version.

Authoritative verification files:

- `release/prefix-python-0.1.0-rc2/RELEASE_VERIFICATION_MANIFEST.json`
- `release/prefix-python-0.1.0-rc2/SHA256SUMS.txt`

## Release Outcome

- Typed outcomes:
  - `ACCEPT_VALID`
  - `ACCEPT_FIXED`
  - `REFUSE_UNMAPPED`
  - `REFUSE_AMBIGUOUS`
  - `REFUSE_INVALID`
- Parse/reparse validation is mandatory for accepted states.
- Invalid AST states are not committed.
- Ambiguity is refused.
- Receipts support rollback, inspection, and deterministic replay.
- The VS Code extension supports Enter-triggered prefix correction for mapped `ALWAYS_SAFE` Python block-structure states.

## Validation Snapshot

- Python unit suite: `55/55` passed
- Python compile sweep: passed
- VS Code extension build: passed
- VS Code behavior test: passed
- VS Code package build: passed
- release qualification: passed
- release ZIP checksum verification: passed
- release ZIP-only install validation: passed
- targeted secret scan: clean
- targeted purity scan: clean
- link scan: clean

## Compatibility Lock

- Requires CPython `3.12.x`
- Validated on CPython `3.12.6`
- Package metadata remains `>=3.12,<3.13`
- Python `3.13` and `3.14` require separate AST authority catalogs and are not claimed in rc2
- Python `3.11`, `3.13`, and `3.14` remain outside the supported release boundary

## Canonical Bundle Hash

- zip sha256: `7a92c318ce9be3f93ba97d319d2d1d1ebcba323205b4690c669e70485fb5d82d`
- bundle manifest sha256: `0bc2aeee84d392d376fa52424b697887bad1bc1affd5b3cda5baaba80db961bb`
- bundle SHA256SUMS sha256: `20834482597a1b9af65b7cb082e9573d32cbb41c4a532d3d751a404ea676c220`
- standalone wheel sha256: `feb085394d9a441d8202e546f2f9c55fd43c2aeaf735e5bb564c455636042b4a`
- standalone VSIX sha256: `02a332530f55ff785e7f41d5e8004245c21033e7ea27e54dc2df586db757e4bf`
- canonicalized bundle wheel sha256: `ade524310084b6b8c6532ff48efa0524f0c7456293b6ecc6233606ab8d2d697e`
- canonicalized bundle VSIX sha256: `e76ab64f9ffc60ca356a57065fa95079cb1aa7a1defe9e6f40efa7ee93a1edd2`

## Final Launch Decision

Bounded public launch approved from the frozen canonical bundle.

## Remaining Caveat

Full interactive VS Code extension-host GUI testing is still outside the automated evidence set.
