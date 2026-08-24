# Product Hunt Packet

## Name

PREFIX for Python

## Tagline

Deterministic Python prefix correction before execution.

## Short Description

PREFIX for Python enforces a bounded Python correctness surface locally, applies singular deterministic repairs, and refuses the rest.

Requires CPython `3.12.x`. Validated on CPython `3.12.6`.

Available through a Controlled Operator Release for selected engineering teams.

## Full Description

PREFIX for Python is a local-first Python prefix layer and VS Code workflow for Python teams that want lawful structure before execution instead of debugging after failure.

It accepts a finite admissible error surface, applies bounded deterministic corrections when a single lawful repair exists, and refuses ambiguous states instead of guessing.

This is not autocomplete. It is not copilot behavior. It is a deterministic Python prefix layer.

Current bounded correction classes include missing block colons, missing indentation, empty bodies, simple unmatched opening delimiters, singular extra closing delimiters, and deterministic tab normalization.

Unsupported or candidate-only states are refused explicitly.

Runtime support in rc2 is intentionally pinned. Python `3.11`, `3.13`, and `3.14` are not claimed in this release. Python `3.13` and `3.14` require separate AST authority catalogs.

Selected teams receive a 30-day evaluation with proof-driven onboarding. Commercial use after evaluation requires a paid license.

## Launch Topics

- Developer Tools
- Python
- VS Code
- Productivity

## Maker Comment

We built PREFIX for teams that are tired of treating invalid intermediate Python states as normal. The product boundary is intentionally narrow: finite Python error classes, deterministic correction, refusal when unsupported, and local-first operation.

The runtime boundary is intentionally narrow too: CPython `3.12.x` only for rc2, validated on `3.12.6`.

## CTA

Apply for Private Operator Release access.
