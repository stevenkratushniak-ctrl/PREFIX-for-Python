# PRODUCT HUNT LAUNCH CHECKLIST

## Positioning

- [x] Product is described as a deterministic Python prefix layer for bounded correctness.
- [x] Product is not described as autocomplete, copilot, or generic AI fixing.
- [x] Copy says refusal is part of the product contract, not a fallback.

## Accuracy

- [x] README bounded correction surface matches shipped engine behavior.
- [x] Product Hunt packet removes assignment-RHS and trailing-operator placeholder claims.
- [x] Public docs no longer expose `AutoFix` as the public product name.

## Demo

- [x] Scan demo path exists via `examples/broken_missing_colon.txt`
- [x] Refusal demo path exists via `examples/broken_return_outside_function.txt`
- [x] CLI apply/rollback smoke path was executed successfully on a parse-valid preimage

## Artifacts

- [x] Wheel builds successfully
- [x] VS Code extension builds successfully
- [x] VS Code package command succeeds
- [x] SHA-256 verification will be bundled with release artifacts

## Trust

- [x] No secret-pattern hits found in shipped product surfaces
- [x] No network code in shipped Python engine or CLI
- [x] Candidate-only repairs are surfaced without silent mutation

## Remaining Disclosure

- [ ] Full interactive VS Code extension-host GUI validation is still a documented limitation
- [x] Canonicalized release bundle exists and publishes stable artifact hashes
