# RELEASE REPRODUCIBILITY REPORT

## Scope

This report covers the canonical standalone founding-operator distribution state at:

- `C:\PREFIX_PYTHON`
- candidate: `prefix-python-0.1.0-rc2`

## Method

Two fresh canonical bundle builds were produced from the standalone root.

Each build cycle performed:

1. `python qualification\build_release_bundle.py`
2. capture of:
   - `release\prefix-python-0.1.0-rc2.zip`
   - `release\prefix-python-0.1.0-rc2\RELEASE_VERIFICATION_MANIFEST.json`
   - `release\prefix-python-0.1.0-rc2\SHA256SUMS.txt`

## Results

- build 1 bundle zip sha256: `7a92c318ce9be3f93ba97d319d2d1d1ebcba323205b4690c669e70485fb5d82d`
- build 2 bundle zip sha256: `7a92c318ce9be3f93ba97d319d2d1d1ebcba323205b4690c669e70485fb5d82d`
- build 1 manifest sha256: `0bc2aeee84d392d376fa52424b697887bad1bc1affd5b3cda5baaba80db961bb`
- build 2 manifest sha256: `0bc2aeee84d392d376fa52424b697887bad1bc1affd5b3cda5baaba80db961bb`
- build 1 `SHA256SUMS.txt` sha256: `20834482597a1b9af65b7cb082e9573d32cbb41c4a532d3d751a404ea676c220`
- build 2 `SHA256SUMS.txt` sha256: `20834482597a1b9af65b7cb082e9573d32cbb41c4a532d3d751a404ea676c220`

## Conclusion

Canonical distribution outputs were stable across two fresh rebuilds.

Stable surfaces confirmed:

- canonical release zip hash
- canonical bundle manifest hash
- canonical `SHA256SUMS.txt` hash
- release file structure

This is sufficient to treat `C:\PREFIX_PYTHON` as a reproducible standalone founding-operator distribution root.
