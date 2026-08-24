# PREFIX Validation Results

## Scope

This report captures the Python-only runtime hardening validation pass for the sealed standalone product root at `C:\PREFIX_PYTHON`.

## Commands Executed

```powershell
python -m unittest discover -s tests -q
npm run build
npm run test:behavior
npm run package
python -m pip wheel . --no-deps -w dist
python qualification\run_release_qualification.py
python qualification\build_release_bundle.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\PREFIX_PYTHON\demo\FINAL_RELEASE_DEMO.ps1
release ZIP checksum verification
release ZIP-only install validation
repo markdown link scan
old-root leakage scan
external-machine leakage scan
```

## Results

- Python unit tests: `55 passed, 0 failed`
- VS Code TypeScript build: passed
- VS Code behavior tests: passed
- VS Code packaging: passed
- wheel build: passed
- release qualification: passed
- deterministic receipt demo: passed
- release ZIP checksum verification: `21` entries, `0` failures
- release ZIP-only install validation: passed
- markdown link scan: `LINK_SCAN_CLEAN`
- old-root leakage scan: no matches
- external-machine leakage scan: no matches

## Determinism Evidence

- engine determinism summary: `all_cases_identical = true`
- engine idempotency summary: `idempotency_ok = true`
- adversarial summary: `all_cases_matched = true`
- refusal summary: `all_engine_cases_refused = true`, `all_cli_cases_refused = true`
- bundle reproducibility: stable across two fresh rebuilds

## Canonical Bundle

- zip sha256: `7a92c318ce9be3f93ba97d319d2d1d1ebcba323205b4690c669e70485fb5d82d`
- manifest sha256: `0bc2aeee84d392d376fa52424b697887bad1bc1affd5b3cda5baaba80db961bb`
- `SHA256SUMS.txt` sha256: `20834482597a1b9af65b7cb082e9573d32cbb41c4a532d3d751a404ea676c220`
