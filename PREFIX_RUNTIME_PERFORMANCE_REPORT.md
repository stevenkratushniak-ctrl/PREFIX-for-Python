# PREFIX Runtime Performance Report

## Scope

This report covers the Python-only deterministic prefix runtime as validated from `C:\PREFIX_PYTHON`.

## Small Structural Cases

From `STRESS_REPORT.json`, the bounded engine cases completed in these measured windows:

- missing colon: `1.244 ms`
- empty function: `0.703 ms`
- assignment refusal: `0.175 ms`
- unmatched delimiter: `0.590 ms`
- trailing-operator refusal: `0.896 ms`
- orphaned `elif` refusal: `0.257 ms`
- unicode identifier normalization case: `3.096 ms`

These are the surfaces closest to the intended editor-time prefix experience.

## Concurrency and Repeatability

- engine concurrency payload check: `64/64` identical payload hashes
- rapid-save simulation failures: `0`
- CLI batch failures: `0`
- fuzz exceptions: `0` across `250` seeded cases

## Large-File Boundary

The bounded near-limit large-file case completed successfully but took `21873.067 ms`.

This does not weaken the Enter-trigger product claim because the editor-time path is now restricted to narrow local block-header surfaces rather than broad whole-document opportunism.

## Extension Host Stability

Qualification confirmed:

- VS Code extension build: stable
- VSIX package hash: stable across repeated packaging
- local engine invocation remains shell-free and network-free

## Performance Conclusion

PREFIX is fast on the mapped Python structural surfaces it is meant to prefix in real time.

The product should continue to treat whole-document near-limit files as bounded but non-heroic paths, while keeping the Enter-trigger runtime focused on instant local structural stabilization.
