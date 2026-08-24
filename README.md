# PREFIX for Python

`PREFIX for Python` is a deterministic Python prefix layer for bounded correctness.

It operates before failure, before invalidity, and before execution. The engine intercepts a bounded set of invalid Python structural states, applies mapped `ALWAYS_SAFE` corrections when one lawful continuation exists, advises ranked candidates when no singular auto-apply path exists, and refuses the transition when the state is unsupported or unsafe.

This repository is the sealed standalone product root for the Python release only. It does not depend on remote inference, cloud routing, or probabilistic repair.

## Product Boundary

`PREFIX for Python` describes the actual operating boundary:

- before syntax failure
- before invalid state manifestation
- before execution
- before debugging burden accrues
- inside Python only for the current sealed release

This release preserves deterministic correction, finite grammar theory, refusal semantics, anti-hallucination posture, local-first execution, and operational certainty.

## Python Lane Model

`PREFIX for Python` now classifies Python rules into four product lanes:

- `APPLY`: singular lawful Python continuations that are `ALWAYS_SAFE`, line-local, idempotent, and parse/reparse validated
- `ADVISE`: ranked Python continuations that are real and bounded, but never auto-applied
- `ANALYZE`: known Python categories that can be detected and explained without mutation
- `ROADMAP`: Python authority surfaces that exist in the finite taxonomy but are not shipped into the runtime yet

Runtime states stay operator-simple:

- `APPLIED`
- `ADVISED`
- `REFUSED`

## Product Positioning

`PREFIX for Python` is not an AI coding assistant.

It is a deterministic Python prefix layer:

- finite admissible error spaces
- mapped `ALWAYS_SAFE` correction
- ranked advice without hidden mutation
- bounded analysis without semantic invention
- refusal over hallucination
- lawful structure before propagation
- local-first operation
- deterministic output from identical input

## What Ships

- A local Python engine that accepts valid Python, applies bounded deterministic repairs, advises ranked continuations, analyzes bounded non-apply cases, or refuses the transition
- A CLI for file, stdin, receipt inspection, rollback, and deterministic replay workflows
- A VS Code extension that can prefix-correct mapped Python block-structure states on Enter and through explicit commands while exposing legality and proof data locally
- Controlled Operator Release support materials for 30-day evaluation, conversion readiness, and release distribution reporting
- Launch assets for GitHub, Product Hunt, release packaging, pricing, screenshots, and landing-page deployment

## Supported Deterministic Corrections

`PREFIX for Python` currently handles a bounded set of high-frequency structural failures:

- missing block colons
- missing indented block bodies
- empty function or class bodies
- simple unmatched opening delimiters
- singular extra closing delimiters
- tabs normalized to four spaces

Advice and analysis stay separate from apply. Example:

- `orphaned elif` is `ADVISED` with ranked non-mutating candidates
- `return` outside a function is `ANALYZE`, not auto-fixed
- assignment right-hand sides or trailing operators are `ANALYZE`, not guessed
- unsupported syntax failures remain `REFUSED` in the `ROADMAP` lane until explicitly promoted

## Python Compatibility

PREFIX Python rc2 is pinned to CPython `3.12.x`.

Validated runtime: CPython `3.12.6`.

The package metadata requires `>=3.12,<3.13`, and the runtime intentionally refuses execution outside the Python 3.12 AST authority surface. Python `3.11`, `3.13`, and `3.14` are not public compatibility targets for this release. Python `3.13` and `3.14` require separate AST authority catalogs before support can be claimed.

## Quick Start

From the product root:

Use a CPython `3.12.x` interpreter for every install and launch command below.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install .
```

Analyze a file:

```powershell
prefix-python examples\broken_missing_colon.txt --json
```

Write the correction back to disk:

```powershell
prefix-python examples\broken_missing_colon.txt --apply
```

Inspect a receipt:

```powershell
prefix-python --inspect-receipt .prefix-python-receipts\<receipt>.json --json
```

Replay a prior accepted correction without mutating any file:

```powershell
prefix-python --replay-receipt .prefix-python-receipts\<receipt>.json --json
```

Correct from stdin:

```powershell
Get-Content examples\broken_missing_colon.txt -Raw | prefix-python --stdin --json
```

Run the demo:

```powershell
python demo\demo_script.py
```

Run tests:

```powershell
python -m unittest discover -s tests -q
```

## VS Code Extension

The extension package lives in `editor/vscode/package.json`.

It provides:

- `PREFIX: Correct Active Python Document`
- `PREFIX: Correct Selected Python Text`
- Enter-triggered correction for mapped `ALWAYS_SAFE` Python block-structure states
- local advised recommendations when ranked Python continuations exist

The intended primary experience is:

human types a mapped Python block header wrong  
presses Enter  
PREFIX either applies the singular lawful structural correction or refuses locally

The extension shells out only to the local Python engine. No cloud inference is required.

## Controlled Operator Release

`PREFIX for Python` rc2 is available through a Controlled Operator Release for selected engineering teams.

Release access is structured as:

- selected operators and engineering teams
- 30-day evaluation
- proof-driven onboarding
- CPython `3.12.x` only
- conversion to a paid license after evaluation

This release is positioned as controlled infrastructure evaluation for selected engineering teams.

Apply for Private Operator Release access.

## Example

Input:

```python
if ready
print("launch")
```

Output:

```python
if ready:
    print("launch")
```

If the input cannot be corrected with a single deterministic path, `PREFIX for Python` refuses the transition and returns the refusal reason instead of guessing.

Typed outcomes:

- `ACCEPT_VALID`
- `ACCEPT_FIXED`
- `REFUSE_UNMAPPED`
- `REFUSE_AMBIGUOUS`
- `REFUSE_INVALID`

Lane outcomes:

- `APPLY` → state `APPLIED`
- `ADVISE` → state `ADVISED`
- `ANALYZE` or `ROADMAP` → state `REFUSED`

## Trust Surface

Every accepted correction carries:

- parse/reparse validation
- Python `3.12` AST hash
- token-stream hash
- legality report with node, edge, and token counts
- deterministic proof trace for applied repair events
- receipt-backed rollback and receipt-backed deterministic replay

Every operator evaluation report carries:

- explicit `as_of` date
- bundle-hash verification
- deterministic `workspace_fingerprint`
- report state derived only from local records

## Repository Layout

```text
PREFIX_PYTHON/
├── prefix_python/          # Canonical engine, CLI, and operator console
├── core/                   # Compatibility wrappers to the canonical engine
├── editor/vscode/          # VS Code extension package
├── examples/               # Demo inputs for screenshots and launch flows
├── tests/                  # Deterministic engine and operator tests
├── launch/                 # Product Hunt, landing-page, pricing, and launch copy
├── release/                # Release scripts, notes, and checksums
├── site/                   # Static landing page
└── docs/                   # Theory and supporting documents
```

## Commercial Package

Launch materials are ready in:

- `launch/PRODUCT_HUNT.md`
- `launch/LAUNCH_COPY.md`
- `launch/LANDING_PAGE_COPY.md`
- `launch/PRICING.md`
- `launch/SCREENSHOTS.md`
- `launch/GITHUB_RELEASE.md`
- `launch/DEMO_FLOW.md`
- `launch/DEPLOYMENT.md`

Release assets are prepared in `release/`.

Controlled release materials cover selected-team evaluation, proof-driven onboarding, conversion readiness, and paid-license transition after the 30-day evaluation.

## Operational Posture

- local-first
- deterministic by default
- finite rule surface
- refusal when unsupported
- no model dependency for the correction path
- no invalid state committed by the engine
- no hidden network behavior in the operator console
