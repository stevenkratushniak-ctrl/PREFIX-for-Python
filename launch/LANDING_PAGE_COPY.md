# Landing Page Copy

## Hero

### Headline

Correct Python before it breaks.

### Subheadline

PREFIX for Python is a deterministic Python prefix layer. It intercepts bounded invalid Python structure locally, applies mapped `ALWAYS_SAFE` corrections, and refuses ambiguous states before broken structure propagates.

### Primary CTA

Apply for access

### Secondary CTA

Review the proof model

## Proof Bar

- Local-first
- Deterministic
- `ALWAYS_SAFE` only
- Refusal over guessing

## Compatibility Callout

- Requires CPython `3.12.x`
- Validated on CPython `3.12.6`
- Python `3.11`, `3.13`, and `3.14` are not claimed in rc2
- Python `3.13` and `3.14` support requires separate AST authority catalogs and is not claimed in rc2

## Release Posture

- Controlled Operator Release
- Selected engineering teams
- 30-Day Evaluation
- Proof-driven onboarding
- Paid-license conversion after evaluation

## Problem Section

Traditional editor flows allow invalid Python states to exist and push the cost downstream into debugging, reruns, and review cycles.

PREFIX moves the boundary earlier. If the state is mapped and the continuation is singular, it corrects it. If not, it refuses.

## How It Works

1. Intercept Python structure as the operator types.
2. Identify whether the state belongs to a finite mapped class.
3. Apply the singular lawful correction.
4. Re-parse and verify.
5. Refuse if the state is unsupported or ambiguous.

## Supported Classes

- Missing block colon
- Missing indentation
- Empty required block
- Simple unmatched delimiter
- Singular extra closing delimiter
- Tab normalization to four spaces

## Refusal Section

PREFIX refuses unsupported states explicitly. That includes orphaned `else`, `return` outside a function, and syntax failures that admit multiple plausible repairs.

## Closing

Apply for Private Operator Release access.
