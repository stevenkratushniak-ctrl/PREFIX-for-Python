# PREFIX for Python 0.1.0

PREFIX for Python is a deterministic Python prefix layer for bounded structural correction. It applies only mapped `ALWAYS_SAFE` repairs, presents non-mutating advice when a singular repair is unavailable, and refuses unsupported or unsafe transitions.

## Release assets

- `prefix-python-0.1.0-windows-x64.zip` — per-user Windows x64 installer with bundled CPython 3.12.10, exact wheel, VSIX, payload manifest, demo inputs, and uninstall command
- `prefix-python-0.1.0-linux-amd64.tar.gz` — per-user Linux amd64 installer for a detected CPython 3.12 runtime, with exact wheel, VSIX, payload manifest, demo inputs, and uninstall command
- `prefix_python-0.1.0-py3-none-any.whl` — standalone Python package
- `prefix-python-0.1.0.vsix` — standalone VS Code extension
- `prefix-python-0.1.0-windows-linux.zip` — combined release bundle
- `RELEASE_MANIFEST.json`, `SHA256SUMS.txt`, and `VERIFY_RELEASE.py` — source identity, artifact hashes, parity evidence, and offline verification

## Normal installation

Extract the platform package. On Windows, run `Install-PREFIX-for-Python.cmd`. On Linux, run `./install-prefix-python.sh` and then `prefix-python-demo`.

Both installers verify their payload hashes, install the exact wheel without an unconditional network dependency step, install the shipped VSIX automatically, connect the extension to the installed engine, and run a real correction smoke check. Installation does not modify user source files.

## Product behavior

- Typed outcomes: `ACCEPT_VALID`, `ACCEPT_FIXED`, `REFUSE_UNMAPPED`, `REFUSE_AMBIGUOUS`, and `REFUSE_INVALID`
- Parse/reparse validation for every accepted mutation
- Advice and analysis without buffer mutation
- Receipt generation, inspection, deterministic replay, and rollback
- Symbolic-link write refusal
- VS Code document, selection, Enter, governance-surface, missing-engine, wrong-engine, and timeout behavior
- Automatic installed-runtime discovery on Windows and Linux

## Supported platforms

- Windows x64: packaged, fresh-installed, engine-qualified, and proven in two real VS Code extension-host launches
- Linux amd64: packaged, fresh-installed, engine-qualified, and proven in two real VS Code extension-host launches on a hosted Ubuntu 24.04 x86_64 runner
- Linux-on-WSL evidence is retained separately and is not described as native or genuine Linux proof
- CPython compatibility is intentionally limited to `>=3.12,<3.13`
- Windows arm64, Linux arm64, macOS, and Python 3.11, 3.13, and 3.14 are not qualified for this release

## Verification result

- Python unit suite: 56 tests passed; one Windows-only symlink-capability skip is allowed where the host cannot create a test link
- Portable engine qualification: 14 checks passed on Windows x64 and genuine Linux amd64
- Receipt apply, inspect, replay, rollback, determinism, refusal, and no-unintended-mutation checks passed
- VS Code extension compilation, behavior tests, deterministic packaging, and offline npm audit passed; audit result: 0 vulnerabilities
- Real VS Code host suite passed twice on Windows x64 and twice on genuine Linux amd64, including Enter, refusal, wrong/missing engine, five-second timeout, and restart
- Installer and uninstaller fresh-profile verification passed on both platforms
- Wheel and VSIX source-to-package parity passed

## Boundary

PREFIX for Python is not a semantic code generator, general debugger, cloud inference service, or promise that arbitrary invalid Python can be repaired. It changes source only under its declared deterministic structural rules and refuses beyond that surface.
