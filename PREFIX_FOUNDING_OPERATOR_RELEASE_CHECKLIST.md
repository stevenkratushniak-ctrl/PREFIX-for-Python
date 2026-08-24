# PREFIX FOUNDING OPERATOR RELEASE CHECKLIST

## Bundle Integrity

- [x] Canonical release bundle exists at `release/prefix-python-0.1.0-rc2.zip`
- [x] Canonical bundle hash remains `7a92c318ce9be3f93ba97d319d2d1d1ebcba323205b4690c669e70485fb5d82d`
- [x] Operator console verifies pinned bundle existence and hash
- [x] Distribution manifests are tied to the canonical bundle path and hash

## Operator Console

- [x] `init` verifies bundle presence and supplied hash correctness
- [x] `invite` rejects duplicate-team creation
- [x] `invite` rejects invalid seat counts, invalid durations, and invalid operator emails
- [x] `activate` rejects activation outside the invited evaluation window
- [x] `checkpoint` rejects records outside the evaluation term
- [x] `issue` rejects records outside the evaluation term
- [x] reports include deterministic `workspace_fingerprint`
- [x] reports refuse success when the pinned bundle drifts

## Validation

- [x] `python -m unittest discover -s tests -q`
- [x] `npm run test:behavior`
- [x] `python -m pip wheel . --no-deps -w dist`
- [x] `python -m prefix_python.operator_console --help`
- [x] installed `prefix-python-ops --help` validated after local package install
- [x] deterministic operator demo generation completed
- [x] repo-wide markdown link scan completed

## Demo Evidence

- [x] `demo/FOUNDING_OPERATOR_RELEASE_DEMO.ps1` generates the operator evidence workspace
- [x] `qualification/_hardening_artifacts/operator_console_demo` contains deterministic local records
- [x] cohort summary generated
- [x] reminders generated
- [x] conversion summary generated
- [x] distribution manifest generated

## Operator Handoff Clarity

- [x] README documents both installed and module-based operator entrypoints
- [x] operator docs reflect lifecycle refusal behavior
- [x] install path is clear even when user Scripts is not on `PATH`

## Release Decision

- [x] Suitable for selected founding operators
- [x] No hidden network behavior in the operator console
- [x] No unproven enterprise claims introduced in this pass
