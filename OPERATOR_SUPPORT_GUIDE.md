# OPERATOR SUPPORT GUIDE

## Support Philosophy

Support for `PREFIX for Python` should feel like operator support for infrastructure, not like community support for a casual utility.

The tone should be:

- direct
- calm
- precise
- respectful

## Support Priorities

### Priority 1

- install blockers
- rollback concerns
- replay concerns
- refusal confusion tied to trust or safety

### Priority 2

- workflow fit questions
- editor embodiment clarity
- packaging and policy questions

### Priority 3

- commercial packaging and rollout planning

## Release Access

Support should describe rc2 as a Controlled Operator Release.

- Access is for selected operators and engineering teams.
- Evaluation runs for 30 days.
- Onboarding is proof-driven: install, demo, refusal review, receipt inspection, replay, and rollback-readiness.
- Runtime support is CPython `3.12.x` only.
- Commercial use after evaluation requires conversion to a paid license.

## Operator Questions To Expect

- Why did PREFIX refuse?
- Can I trust the replay?
- Is rollback safe?
- What is actually in scope today?
- How should we evaluate rollout for a team?

## Support Answer Pattern

Each response should reinforce:

- boundedness
- determinism
- explicit refusal
- auditability
- local-first trust

## Escalation

Escalate quickly if an operator reports:

- unexpected mutation
- unclear replay result
- unclear receipt lineage
- refusal that appears inconsistent

Those are trust-critical issues, not routine support noise.

## Runtime Compatibility Troubleshooting

When install or launch fails because the wrong interpreter is active, answer with the pinned boundary directly:

- rc2 requires CPython `3.12.x`
- validated on CPython `3.12.6`
- Python `3.11`, `3.13`, and `3.14` are not supported in this release
- Python `3.13` and `3.14` require separate AST authority catalogs before support can be claimed

For VS Code support, direct operators to set `prefixPython.pythonCommand` to an explicit CPython `3.12.x` interpreter path.
