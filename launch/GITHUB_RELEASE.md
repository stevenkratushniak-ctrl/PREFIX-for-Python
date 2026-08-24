# GitHub Release Prep

## Release Title

PREFIX for Python v0.1.0

## Release Summary

The first commercial wedge launch of PREFIX for Python: a deterministic Python prefix layer and VS Code workflow for bounded Python correctness.

## Highlights

- Deterministic Python prefix layer
- Explicit refusal model
- Local CLI
- Enter-triggered VS Code workflow
- Static landing page
- Product Hunt packet and launch assets

## Compatibility Lock

- Requires CPython `3.12.x`
- Validated on CPython `3.12.6`
- Keep release messaging at `>=3.12,<3.13`
- Do not claim Python `3.11`, `3.13`, or `3.14` support in rc2
- Python `3.13` and `3.14` require separate AST authority catalogs before support can be claimed

## Attachments

- `INSTALL_PREFIX_PYTHON.ps1`
- `DEMO_PREFIX_PYTHON.ps1`
- `RELEASE_NOTES_v0.1.0.md`
- `SHA256SUMS.txt`

## Release Checklist

- Verify `python -m unittest discover -s tests -q`
- Verify demo script output
- Package VS Code extension into a `.vsix`
- Update `SHA256SUMS.txt`
- Publish release notes
- Keep marketplace, landing, Product Hunt, install, troubleshooting, and release-note copy aligned to the CPython `3.12.x` boundary
