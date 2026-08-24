# PREFIX for Python VS Code Extension

`PREFIX for Python` applies deterministic Python prefix correction inside VS Code.

It does not autocomplete. It does not infer intent from the cloud. It sends Python text to the local `prefix-python` engine, applies a mapped `ALWAYS_SAFE` correction when one lawful continuation exists, and refuses when the state is ambiguous or unsupported.

The extension now reflects the Python lane model directly:

- `APPLY` for singular lawful Python continuation
- `ADVISE` for ranked Python recommendations with zero mutation
- `ANALYZE` for bounded explanation without mutation
- `ROADMAP` for known but not-yet-shipped Python surfaces

## Commands

- `PREFIX: Correct Active Python Document`
- `PREFIX: Correct Selected Python Text`

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

Validated runtime: CPython 3.12.6.

The current release is intentionally pinned to the Python 3.12 AST authority surface. Python 3.11, 3.13, and 3.14 are not public compatibility targets for this release. Python 3.13 and 3.14 require separate AST authority catalogs before support can be claimed.

## Local Setup

```powershell
cd editor\vscode
npm install
npm run build
```

From the product root, make sure the engine is installed:

```powershell
python -m pip install .
```

## Configuration

`prefixPython.pythonCommand`

- Default: `python`
- Set this to a CPython `3.12.x` interpreter path when your default `python` is not CPython `3.12.x`

## Operational Behavior

- Valid text: no mutation
- Deterministically correctable text: document or selection is replaced in place under parse/reparse validation
- Advised text: the extension surfaces the recommendation packet and does not mutate the buffer
- Analyzed or unsupported text: the extension surfaces the bounded reason and does not mutate the buffer
- Selection correction requires one explicit Python selection and never widens silently to the full document
