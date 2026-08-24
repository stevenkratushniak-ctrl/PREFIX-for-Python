# PREFIX for Python VS Code Extension

`PREFIX for Python` applies deterministic Python prefix correction inside VS Code on Windows x64 and Linux amd64.

It does not autocomplete. It does not infer intent from the cloud. It sends Python text to the local `prefix-python` engine, applies a mapped `ALWAYS_SAFE` correction when one lawful continuation exists, and refuses when the state is ambiguous or unsupported.

The extension now reflects the Python lane model directly:

- `APPLY` for singular lawful Python continuation
- `ADVISE` for ranked Python recommendations with zero mutation
- `ANALYZE` for bounded explanation without mutation
- `ROADMAP` for known but not-yet-shipped Python surfaces

## Commands

- `PREFIX: Govern Active Python Transition`
- `PREFIX: Govern Selected Python Structure`
- `PREFIX: Show Last Transition Governance Surface`

## Enter-Triggered Flow

When `prefixPython.enableOnEnter` is enabled, PREFIX evaluates Python structure after Enter inserts a newline.

The Enter-triggered surface is intentionally narrow and Python-only:

- one cursor only
- one newline insertion only
- no hidden selection expansion
- no multiline continuation guessing
- no triple-quoted-string mutation
- mapped missing-colon block headers only

Within that bounded surface:

- already lawful state: no mutation
- mapped `ALWAYS_SAFE` block-header state: correction applies immediately
- ranked continuation state: advice is surfaced locally and no mutation occurs
- ambiguous or unsupported state: refusal or analysis is surfaced locally and no mutation occurs

If PREFIX inserts `pass` to keep the document parse-valid on Enter, the inserted `pass` token is selected so the operator can replace it immediately with the intended block body.

## Requirements

- CPython 3.12.x
- `prefix-python` installed locally

Validated release runtimes include bundled CPython 3.12.10 on Windows and CPython 3.12.3 on hosted Ubuntu Linux.

The current release is intentionally pinned to the Python 3.12 AST authority surface. Python 3.11, 3.13, and 3.14 are not public compatibility targets for this release. Python 3.13 and 3.14 require separate AST authority catalogs before support can be claimed.

## Local Setup

The Windows and Linux PREFIX installers install this extension and connect it to the bundled engine automatically. No interpreter setting is required after a normal installation.

For source development only:

```text
cd editor/vscode
npm ci
npm run build
```

Run the extension against a PREFIX for Python 0.1.0 installation, or install the source into an isolated CPython 3.12 development environment:

```text
python3.12 -m pip install .
```

## Configuration

`prefixPython.pythonCommand`

- Default: blank (automatic PREFIX runtime discovery)
- Set an explicit CPython `3.12.x` path only to override the installed PREFIX engine

## Operational Behavior

- Valid text: no mutation
- Deterministically correctable text: document or selection is replaced in place under parse/reparse validation
- Advised text: the extension surfaces the recommendation packet and does not mutate the buffer
- Analyzed or unsupported text: the extension surfaces the bounded reason and does not mutate the buffer
- Selection correction requires one explicit Python selection and never widens silently to the full document
