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

`PREFIX for Python` classifies Python rules into four product lanes:

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
- Windows x64 and Linux amd64 installers that install the exact engine and VS Code extension together
- Release manifests, SHA-256 checksums, demos, qualification tooling, and source-to-package parity evidence

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

PREFIX for Python 0.1.0 is pinned to CPython `3.12.x`.

The Windows x64 package includes CPython `3.12.10`. The Linux amd64 package detects an installed CPython `3.12` runtime and blocks with a clear instruction if it is absent.

The package metadata requires `>=3.12,<3.13`, and the runtime intentionally refuses execution outside the Python 3.12 AST authority surface. Python `3.11`, `3.13`, and `3.14` are not public compatibility targets for this release. Python `3.13` and `3.14` require separate AST authority catalogs before support can be claimed.

## Install and Start

Download the package for your platform from the 0.1.0 release and extract it.

On Windows x64, double-click:

```text
Install-PREFIX-for-Python.cmd
```

The Windows installer verifies every payload hash, installs its bundled CPython 3.12 runtime and exact wheel per user, installs the shipped VSIX, connects the extension to that runtime automatically, and runs a correction smoke check. It does not require `python` or `pip` on `PATH`.

On Linux amd64, run from the extracted package directory:

```sh
./install-prefix-python.sh
prefix-python-demo
```

The Linux installer verifies every payload hash, uses a detected CPython 3.12 runtime, installs the exact wheel without a network dependency step, and installs the shipped VSIX automatically when the `code` command is present. If CPython 3.12 or VS Code is absent, it prints the exact missing prerequisite and leaves unrelated user files unchanged.

After installation, open a Python file in VS Code and run `PREFIX: Govern Active Python Transition`, or use `prefix-python` from a terminal. On Linux, ensure `~/.local/bin` is on `PATH` if your distribution does not add it automatically.

Uninstall with `Uninstall-PREFIX-for-Python.cmd` on Windows or `./uninstall-prefix-python.sh` on Linux.

## CLI Examples

Analyze a file:

```text
prefix-python broken_missing_colon.txt --json
```

Write the correction back to disk:

```text
prefix-python broken_missing_colon.txt --apply
```

Inspect a receipt:

```text
prefix-python --inspect-receipt .prefix-python-receipts\<receipt>.json --json
```

Replay a prior accepted correction without mutating any file:

```text
prefix-python --replay-receipt .prefix-python-receipts\<receipt>.json --json
```

Receipt-backed `--apply`, `--inspect-receipt`, `--replay-receipt`, and `--rollback` operations remain local and deterministic. PREFIX refuses symbolic-link writes and unsupported or ambiguous repairs instead of guessing.

For source verification, use CPython 3.12 and run `python -m unittest discover -s tests -q` from the repository root.

## VS Code Extension

The extension package lives in `editor/vscode/package.json`.

It provides:

- `PREFIX: Govern Active Python Transition`
- `PREFIX: Govern Selected Python Structure`
- `PREFIX: Show Last Transition Governance Surface`
- Enter-triggered correction for mapped `ALWAYS_SAFE` Python block-structure states
- local advised recommendations when ranked Python continuations exist

The intended primary experience is:

human types a mapped Python block header wrong  
presses Enter  
PREFIX either applies the singular lawful structural correction or refuses locally

The extension shells out only to the local Python engine. No cloud inference is required.

## Release 0.1.0

Release 0.1.0 provides separate Windows x64 and Linux amd64 packages, the standalone wheel and VSIX, a combined release bundle, SHA-256 checksums, release notes, and an offline release verifier. The supported claim is limited to the exact packages and qualification evidence published with that release.

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

## Release Artifacts

Final release assets are built into `release/prefix-python-0.1.0-final/`, with the combined Windows and Linux bundle at `release/prefix-python-0.1.0-windows-linux.zip`. `RELEASE_MANIFEST.json`, `SHA256SUMS.txt`, and `VERIFY_RELEASE.py` bind and verify the exact files.

## Operational Posture

- local-first
- deterministic by default
- finite rule surface
- refusal when unsupported
- no model dependency for the correction path
- no invalid state committed by the engine
- no hidden network behavior in the operator console
