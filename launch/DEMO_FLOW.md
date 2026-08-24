# Demo Flow

## 1. Open With the Thesis

Say:

`PREFIX for Python corrects bounded invalid states before execution and refuses the rest.`

Use CPython `3.12.x` for all command-line demo steps. This release was validated on CPython `3.12.6`.

## 2. Show a Correctable Failure

Run:

```powershell
py -3.12 -m prefix_python examples\broken_missing_colon.txt --json
```

Talk track:

- missing colon detected
- indentation inserted
- output re-parsed and verified
- legality report and proof trace emitted

## 3. Show Refusal

Run:

```powershell
py -3.12 -m prefix_python examples\broken_return_outside_function.txt --json
```

Talk track:

- unsupported state
- no guesswork
- explicit refusal reason

## 4. Show Receipt Replay

Run:

```powershell
py -3.12 -m prefix_python examples\broken_missing_colon.txt --apply --json
py -3.12 -m prefix_python --replay-receipt <receipt>.json --json
```

Talk track:

- accepted mutations produce receipts
- replay proves the same preimage yields the same accepted output
- rollback and replay are operator trust surfaces, not opaque behavior

## 5. Show VS Code

- Open a Python file with the broken example
- Execute `PREFIX: Correct Active Python Document`
- Show the in-place correction and the output channel proof lines

## 6. Close

The product does not promise universal repair. It promises a bounded deterministic surface and truthful refusal outside that surface.
