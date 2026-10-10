# PREFIX for Python 0.1.0

## Private customer-qualification repair candidate

This local candidate preserves version 0.1.0 and its existing license. It has a new source commit and new artifact hashes; it is **not** the unchanged public `v0.1.0` download. No new public release or live-sale approval is implied. Read the accompanying qualification record for results tied to these exact bytes.

Repairs: indentation normalization no longer changes literal tab data; unchanged valid inputs retain their newline bytes; CLI writes keep UTF-8/line-ending bytes; recovery receipts are saved and reread before a target edit; malformed or changed receipts refuse; PREFIX writers are serialized; delayed editor results cannot replace newer typing. Editor responses must bind to the exact input and output hashes. Receipt inspection distinguishes verified content from a matching current target.

PREFIX for Python is a local tool for bounded structural correction. It applies mapped deterministic repairs, presents non-mutating advice in supported ambiguous cases, and refuses unsupported cases. Its internal `ALWAYS_SAFE` classification is not a guarantee of intended program behavior. Review changes and retain your own version-control history.

## Release assets

- `prefix-python-0.1.0-windows-x64.zip` — per-user Windows x64 installer with bundled CPython 3.12.10, exact wheel, VSIX, payload manifest, demo inputs, and uninstall command
- `prefix-python-0.1.0-linux-amd64.tar.gz` — per-user Linux amd64 installer for a detected CPython 3.12 runtime, with exact wheel, VSIX, payload manifest, demo inputs, and uninstall command
- `prefix_python-0.1.0-py3-none-any.whl` — standalone Python package
- `prefix-python-0.1.0.vsix` — standalone VS Code extension
- `prefix-python-0.1.0-windows-linux.zip` — combined release bundle
- `RELEASE_MANIFEST.json`, `SHA256SUMS.txt`, and `VERIFY_RELEASE.py` — source identity, artifact hashes, parity evidence, and offline verification

## Normal installation

Extract the platform package. On Windows, run `Install-PREFIX-for-Python.cmd`. On Linux, run `./install-prefix-python.sh` and then `prefix-python-demo`.

Both installers verify their payload hashes, install the exact wheel without an unconditional network dependency step, and run a correction smoke check. Windows requires an existing VS Code installation; Linux installs the extension when VS Code is detected, otherwise it installs the CLI and explains how to add the extension later. Installation does not modify user source files.

## Product behavior

- Typed outcomes: `ACCEPT_VALID`, `ACCEPT_FIXED`, `REFUSE_UNMAPPED`, `REFUSE_AMBIGUOUS`, and `REFUSE_INVALID`
- Parse/reparse validation for every accepted mutation
- Advice and analysis without buffer mutation
- Receipt generation, inspection, deterministic replay, and rollback to a parse-valid preimage. Rollback refuses invalid original Python or a target changed since the recorded transition.
- Symbolic-link write refusal
- VS Code document, selection, Enter, governance-surface, missing-engine, wrong-engine, and timeout behavior
- Automatic installed-runtime discovery on Windows and Linux

## Platform boundaries

- Windows x64 and Linux amd64 packages are included. Fresh execution results for this repair must be read from its accompanying qualification record; earlier results do not qualify changed bytes.
- Linux-on-WSL evidence is retained separately and is not described as native or genuine Linux proof
- CPython compatibility is intentionally limited to `>=3.12,<3.13`
- Windows arm64, Linux arm64, macOS, and Python 3.11, 3.13, and 3.14 are not qualified for this release

## Retained original-release evidence, not new candidate results

- Python unit suite: 56 tests passed; one Windows-only symlink-capability skip is allowed where the host cannot create a test link
- Portable engine qualification: 14 checks passed on Windows x64 and genuine Linux amd64
- Receipt apply, inspect, replay, rollback, determinism, refusal, and no-unintended-mutation checks passed
- VS Code extension compilation, behavior tests and deterministic packaging passed. An offline npm audit is not a current vulnerability scan and does not establish a security certification.
- Real VS Code host suite passed twice on Windows x64 and twice on genuine Linux amd64, including Enter, refusal, wrong/missing engine, five-second timeout, and restart
- Installer and uninstaller fresh-profile verification passed on both platforms
- Wheel and VSIX source-to-package parity passed

## Boundary

PREFIX for Python is not a semantic code generator, general debugger, cloud inference service, or promise that arbitrary invalid Python can be repaired. It changes source only under its declared deterministic structural rules and refuses beyond that surface.

Receipts contain source text and absolute local target paths. Keep the receipt directory private and copy it together if you need its chain. Receipt SHA-256 values detect changed content; they are not signatures and cannot authenticate a maliciously rewritten receipt. A receipt saved before an interrupted edit is a prepared transition, not proof that the edit happened; inspection checks the current file's exact postimage. PREFIX does not promise to coordinate edits made by unrelated applications: stop editing the target while using CLI apply/rollback. VS Code edits remain unsaved until you save normally; CLI receipts are generated by CLI apply, not by the editor commands.
