# PREFIX STANDALONE VALIDATION REPORT

## Validation Root

All validation in this report was executed from `C:\PREFIX_PYTHON` or its standalone extension subdirectory.

## Commands Run

```powershell
python -m unittest discover -s tests -q
npm run build
npm run test:behavior
npm run package
python -m pip wheel . --no-deps -w dist
python -m prefix_python.operator_console --help
python qualification\run_release_qualification.py
python qualification\build_release_bundle.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\PREFIX_PYTHON\demo\FINAL_RELEASE_DEMO.ps1
python markdown link scan across all repo markdown
rg search for old-root references
rg search for external-machine references
release ZIP checksum verification
release ZIP-only install validation
```

## Results

- `python -m unittest discover -s tests -q`
  - `55` passed
  - `0` failed
- `npm run build`
  - passed
- `npm run test:behavior`
  - passed
- `npm run package`
  - passed
- `python -m pip wheel . --no-deps -w dist`
  - passed
- `python -m prefix_python.operator_console --help`
  - passed
- deterministic final release demo generation
  - passed
- standalone qualification regeneration
  - passed
- release ZIP checksum verification
  - `21` entries verified
  - `0` failures
- release ZIP-only install validation
  - passed
- markdown link scan
  - `LINK_SCAN_CLEAN`
- old-root reference scan
  - no matches
- external-machine reference scan
  - no matches

## Canonical Bundle

- release bundle sha256: `7a92c318ce9be3f93ba97d319d2d1d1ebcba323205b4690c669e70485fb5d82d`
- bundle manifest sha256: `0bc2aeee84d392d376fa52424b697887bad1bc1affd5b3cda5baaba80db961bb`
- bundle `SHA256SUMS.txt` sha256: `20834482597a1b9af65b7cb082e9573d32cbb41c4a532d3d751a404ea676c220`

## Validation Conclusion

The standalone root validates as an independent product root for `PREFIX for Python`.
