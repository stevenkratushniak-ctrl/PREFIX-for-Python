# Known Limitations

- PREFIX for Python is intentionally limited to a bounded correction surface: structural syntax repair, not semantic bug fixing.
- Unsupported states are refused rather than guessed. Proven refusal classes in this release include orphaned `else`, `return` outside a function, oversized inputs, NUL-byte inputs, and non-UTF-8 files.
- The CLI includes a symbolic-link write refusal path, but this qualification run could not execute that case on Windows because local symlink creation required privileges not available to the current session.
- The CLI accepts exactly one file path or stdin per invocation. Directory traversal, recursive batch mode, rollback orchestration, and backup session management are out of scope for `0.1.0`.
- `--write` is atomic and same-path only, but it does not yet emit automatic sidecar backups.
- Input decoding is UTF-8 only. Files that require alternate encodings are refused.
- The release qualification validates VS Code extension build and package stability, but not a full interactive extension-host test matrix inside real GUI sessions.
- Python runtime support is pinned to CPython `3.12.x` in this release candidate and validated on CPython `3.12.6`. Python `3.11`, `3.13`, and `3.14` are not claimed compatible in rc2. Python `3.13` and `3.14` require separate AST authority catalogs before support can be claimed.
