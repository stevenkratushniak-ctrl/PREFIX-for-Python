# PREFIX ALWAYS_SAFE Rule Expansion

## Scope

This pass expanded only Python-only, deterministic, bounded, non-semantic corrections.

## New or Strengthened Coverage

### Async block headers

PREFIX now recognizes and deterministically repairs missing-colon block headers for:

- `async def`
- `async for`
- `async with`

These surfaces stay inside the existing structural contract:

- no symbol invention
- no import generation
- no semantic guessing
- parse/reparse validation remains mandatory

### Exception-group `except*` headers

PREFIX now recognizes `except*` as a block-introducing header for missing-colon repair inside lawful contexts.

## Safety Boundary

These expansions were accepted because they remain:

- deterministic
- idempotent
- grammar-local
- bounded to structural Python legality
- reversible through existing correction receipts

## Explicit Non-Expansions

This pass did not add:

- import generation
- variable renaming
- default value guessing
- operator completion
- semantic code synthesis
- multi-line intent inference

## Evidence

Positive tests added for:

- `async def` missing-colon correction
- `async with` missing-colon correction inside an async function
- `except*` missing-colon correction

Negative or boundary tests added for:

- valid async source preservation
- async signature continuation behavior
- post-fix idempotency on async correction surfaces
