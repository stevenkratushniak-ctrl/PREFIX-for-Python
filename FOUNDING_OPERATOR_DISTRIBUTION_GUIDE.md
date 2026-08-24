# CONTROLLED OPERATOR DISTRIBUTION GUIDE

## Purpose

This guide defines the controlled distribution workflow for selected `PREFIX for Python` operators and engineering teams.

`PREFIX for Python` is a deterministic Python prefix layer for bounded correctness. It is distributed through a Controlled Operator Release with 30-day evaluation, proof-driven onboarding, and paid-license conversion after evaluation.

## Distribution Artifact

Selected operators receive exactly one canonical release package:

- `prefix-python-0.1.0-rc2.zip`

The extracted package contains:

- the canonical Python wheel
- the canonical VS Code extension package
- install and demo scripts
- bundled deterministic demo fixtures
- release notes
- operator-facing onboarding and support documents
- `SHA256SUMS.txt`
- `RELEASE_VERIFICATION_MANIFEST.json`

## Operator Verification Workflow

1. Extract the release zip into a local directory.
2. Verify bundle contents with `SHA256SUMS.txt`.
3. Run `INSTALL_PREFIX_PYTHON.ps1` from the extracted bundle directory.
4. Run `DEMO_PREFIX_PYTHON.ps1` from the same extracted bundle directory.
5. Review refusal behavior, deterministic correction output, and bundled notes before using the product in a real evaluation workspace.

## Install Surface

The bundle install flow is wheel-first and local-first:

- the installer locates the bundled `prefix_python-*.whl`
- creates a local `.venv`
- installs the wheel into that local environment
- does not require access to the broader source repository

## Demo Surface

The bundle demo uses only the bundled fixture files:

- `broken_missing_colon.txt`
- `broken_return_outside_function.txt`

This keeps the first-run workflow deterministic and independent of external source trees.

## Operator Expectations

Selected operators should expect:

- deterministic correction or refusal
- no guessing
- no hidden network behavior
- explicit refusal when correction legality is unproven
- local evidence generation through the operator console

## Support Boundary

Selected operators should use:

- `README.md`
- `PILOT_ONBOARDING_PACKET.md`
- `OPERATOR_SUPPORT_GUIDE.md`
- `30_DAY_EVALUATION_TERMS.md`

The release is intentionally bounded. Operators should not expect unsupported semantic repair, hidden fallback behavior, or probabilistic mutation.
