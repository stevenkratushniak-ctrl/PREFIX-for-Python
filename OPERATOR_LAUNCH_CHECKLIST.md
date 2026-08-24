# OPERATOR LAUNCH CHECKLIST

## Freeze

- [x] Canonical release bundle frozen at `release/prefix-python-0.1.0-rc2.zip`
- [x] Canonical zip sha256 verified as `7a92c318ce9be3f93ba97d319d2d1d1ebcba323205b4690c669e70485fb5d82d`

## Validation

- [x] `python -m unittest discover -s tests -q`
- [x] Python compile sweep
- [x] `npm run build`
- [x] `npm run test:behavior`
- [x] `npm run package`
- [x] `python qualification\run_release_qualification.py`
- [x] release ZIP checksum verification clean
- [x] release ZIP-only install validation clean
- [x] targeted secret scan clean
- [x] targeted purity scan clean
- [x] launch-doc link scan clean

## Release Surface

- [x] `FINAL_RELEASE_NOTES.md` prepared
- [x] `PRODUCT_HUNT_FINAL_COPY.md` prepared
- [x] `GITHUB_RELEASE_BODY.md` prepared
- [x] `demo/FINAL_RELEASE_DEMO.ps1` prepared

## Operator Reminders

- [ ] Publish only from the frozen canonical bundle, not raw build outputs
- [ ] Publish wheel, VSIX, manifest, and sums together
- [ ] Use the canonical zip hash in launch communications
- [ ] Keep the launch claim bounded to deterministic structural Python correctness
- [ ] Frame the release as Controlled Operator Release / Private Operator Release
- [ ] State selected engineering teams, 30-day evaluation, proof-driven onboarding, and paid-license conversion after evaluation
- [ ] Keep the runtime boundary at CPython `3.12.x` only
- [ ] Use only selected-operator, 30-day evaluation, proof-driven onboarding, and paid-license conversion language

## Known Caveat

- [ ] Note that full interactive VS Code extension-host GUI testing is outside the automated evidence set
