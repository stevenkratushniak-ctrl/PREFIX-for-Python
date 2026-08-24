# Python Version Compatibility Report

## Decision

Keep the current minimum and maximum runtime boundary:

`CPython >=3.12,<3.13`

Do not raise or lower the minimum version for rc2.

Do not claim Python 3.11, 3.13, or 3.14 compatibility for this release.

## Compatibility Matrix

| Runtime | Installed locally | Result | Public claim |
| --- | --- | --- | --- |
| CPython 3.11.9 | Yes | Install refused by package metadata; source execution fails closed through AST authority pin. | Not supported |
| CPython 3.12.6 | Yes | Full unit suite passed; warning-enabled suite passed; wheel build passed; CLI smoke passed. | Supported |
| CPython 3.13.7 | Yes | Install refused by package metadata; source execution fails closed through AST authority pin. | Not supported |
| CPython 3.14 | No | No local interpreter available. | Not validated |

## Compatibility Authority

PREFIX Python rc2 is not merely "Python 3 compatible."

It is pinned to the Python 3.12 AST authority surface:
- node registry
- transition constraints
- parse/reparse behavior
- token authority
- proof and replay semantics

The runtime guard in `prefix_python/ast_bridge.py` refuses non-3.12 runtimes intentionally.

## Packaging Metadata

Current metadata:

```toml
requires-python = ">=3.12,<3.13"
classifiers = [
  "Programming Language :: Python :: 3",
  "Programming Language :: Python :: 3 :: Only",
  "Programming Language :: Python :: 3.12"
]
```

This is accurate for rc2 and should remain unchanged.

## VS Code Extension Assumption

The VS Code extension shells out to the configured local Python command.

For rc2, that command must resolve to CPython 3.12.x with `prefix-python` installed.

The extension is not independently compatible with Python 3.11, 3.13, or 3.14 unless the configured engine is.

## Targeted Checks Performed

- `py -0p`
- `py -3.12 -m unittest discover -s tests -q`
- `py -3.12 -Wd -m unittest discover -s tests -q`
- `py -3.12 -m pip wheel . --no-deps -w qualification\_hardening_artifacts\python_version_compat\py312_wheel`
- `py -3.12 -m prefix_python --version`
- CPython 3.12 stdin CLI smoke
- `py -3.13 -m pip install --dry-run --no-deps release\prefix_python-0.1.0-py3-none-any.whl`
- CPython 3.13 source execution fail-closed check
- `py -3.11 -m pip install --dry-run --no-deps release\prefix_python-0.1.0-py3-none-any.whl`
- CPython 3.11 source execution fail-closed check
- `py -3.14 --version`
- `npm run test:behavior`
- wheel metadata inspection

## Results

CPython 3.12:
- `55/55` tests passed.
- Warning-enabled test suite passed.
- Wheel build passed.
- CLI version command passed.
- CLI governed-transition smoke passed.

CPython 3.13:
- Wheel installation refused because `3.13.7` is outside `<3.13,>=3.12`.
- Source execution refused through AST authority guard.

CPython 3.11:
- Wheel installation refused because `3.11.9` is outside `<3.13,>=3.12`.
- Source execution refused through AST authority guard.

CPython 3.14:
- No local interpreter was available.
- No compatibility claim was made.

## Dependency Audit

Runtime dependency posture:
- no third-party runtime dependencies
- standard-library-only engine path
- packaging uses `setuptools>=68`
- VS Code extension invokes local engine through configured Python command

Observed compatibility constraints:
- AST node registry is Python 3.12-specific.
- `ast.TypeAlias`, `ast.TypeVar`, `ast.TypeVarTuple`, `ast.ParamSpec`, and `ast.TryStar` are included in the pinned registry.
- Non-3.12 runtime execution is intentionally refused.

## Metadata Changes

No `pyproject.toml` change was required.

The existing `requires-python = ">=3.12,<3.13"` boundary is accurate.

Public docs were corrected where they previously implied Python `>=3.11` support.

## Remaining Risks

- Python 3.13 and 3.14 require separate AST authority catalogs before support can be claimed.
- Python 3.14 could not be locally tested because no interpreter was installed.
- VS Code users must configure `prefixPython.pythonCommand` to a CPython 3.12 interpreter.

## Recommendation

Keep the current minimum version.

Do not raise above Python 3.12, because that would narrow the already validated rc2 audience without benefit.

Do not lower to Python 3.11, because the AST authority and package metadata do not support it.

Do not claim Python 3.13 or 3.14 until separate finite AST registries, transition maps, and proof validation suites are created for those versions.
