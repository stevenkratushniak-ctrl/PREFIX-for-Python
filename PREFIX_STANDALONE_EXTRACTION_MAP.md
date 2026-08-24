# PREFIX STANDALONE EXTRACTION MAP

## Authority

- source root label: `parent_source_root`
- backup label: `ConstrainedPython_20260512_162244`
- standalone root: `C:\PREFIX_PYTHON`

## Extraction Method

The complete product root was copied from the parent source root into `C:\PREFIX_PYTHON`, then hardened in place until it no longer required the parent repository for product execution, release verification, or founding-operator operations.

## Top-Level Directories Copied

- `ast`
- `build`
- `core`
- `demo`
- `dist`
- `docs`
- `editor`
- `examples`
- `launch`
- `prefix_python`
- `prefix_python.egg-info`
- `qualification`
- `release`
- `rules`
- `site`
- `tests`

## Top-Level Product Files Copied

- package metadata: `pyproject.toml`, `LICENSE.txt`, `.gitignore`
- product docs: `README.md`, `KNOWN_LIMITATIONS.md`, `HARDENING_REPORT.md`, `RELEASE_READINESS_REPORT.md`
- release evidence: `ADVERSARIAL_REPORT.json`, `DETERMINISM_REPORT.json`, `REFUSAL_REPORT.json`, `STRESS_REPORT.json`, `RELEASE_VERIFICATION_MANIFEST.json`, `RELEASE_CANDIDATE_REPORT.md`
- commercial and launch docs: `PRICING_AND_PACKAGING.md`, `CATEGORY_POSITIONING.md`, `VALUE_BASED_PRICING_RATIONALE.md`, `ENTERPRISE_VALUE_PROPOSITION.md`, `CUSTOMER_ONE_PAGER.md`, `WEBSITE_COPY.md`, `PRODUCT_HUNT_FINAL_COPY.md`, `GITHUB_RELEASE_BODY.md`
- founding-operator program docs: `FOUNDING_OPERATOR_PROGRAM.md`, `FOUNDING_OPERATOR_OPERATIONS.md`, `CONTROLLED_RELEASE_AUTOMATION.md`, `CONTROLLED_RELEASE_STRATEGY.md`, `EVALUATION_LIFECYCLE_SYSTEM.md`, `PILOT_ONBOARDING_PACKET.md`, `PILOT_FEEDBACK_WORKFLOW.md`, `OPERATOR_SUPPORT_GUIDE.md`, `EVALUATION_SUCCESS_CRITERIA.md`, `CONVERSION_AND_RENEWAL_PLAN.md`, `PREFIX_OPERATOR_CONSOLE_PLAN.md`, `PREFIX_OPERATIONAL_AUTOMATION_REPORT.md`, `PREFIX_FOUNDING_OPERATOR_RELEASE_HARDENING_REPORT.md`, `PREFIX_FOUNDING_OPERATOR_RELEASE_CHECKLIST.md`

## Standalone Rewrite Surfaces

The following surfaces were rewritten or regenerated to remove parent-root assumptions:

- `qualification/run_release_qualification.py`
- `HARDENING_REPORT.md`
- `RELEASE_READINESS_REPORT.md`
- `PREFIX_FOUNDING_OPERATOR_RELEASE_HARDENING_REPORT.md`
- `release/prefix-python-0.1.0-rc2/HARDENING_REPORT.md`
- `release/prefix-python-0.1.0-rc2/RELEASE_READINESS_REPORT.md`
- regenerated root evidence outputs:
  - `ADVERSARIAL_REPORT.json`
  - `DETERMINISM_REPORT.json`
  - `REFUSAL_REPORT.json`
  - `STRESS_REPORT.json`
  - `RELEASE_VERIFICATION_MANIFEST.json`
  - `RELEASE_CANDIDATE_REPORT.md`

## Standalone Cleanup Applied

- removed stale `__pycache__` directories
- removed the inherited historical `release/prefix-python-0.1.0-rc1` directory before regenerating standalone qualification outputs
- verified no remaining literal references to:
  - legacy parent repo roots
  - legacy user-profile paths
  - legacy external AutoFix document roots

## Standalone Command Root

All required release, test, packaging, and founding-operator commands were executed from:

- `C:\PREFIX_PYTHON`
- `C:\PREFIX_PYTHON\editor\vscode`

## Result

`C:\PREFIX_PYTHON` is the standalone product authority root for `PREFIX for Python`.
