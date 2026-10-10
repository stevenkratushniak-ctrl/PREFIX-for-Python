# PREFIX-EDITOR-002 — Boundary Correction / Implementation Stop

## Status

Implementation stopped before adapter source creation because the completed authority map contained a build-line contradiction.

## Pinned source authority

- base commit: `33b61e9059c06d295aff9eb62bf4b4feb1dc3d56`
- base tree: `d1d7a9df87073924375c785ac52cab33d85aca61`
- proof branch: `prefix-editor-002-jetbrains-proof`

No files under `prefix_python/` or `editor/vscode/` were modified.

## Contradiction

The prior map stated that PyCharm 2026.2 should be qualified as JetBrains platform build family `262`, while one current JetBrains SDK build-number table labels “2026.2” as branch `261`.

That SDK table is inconsistent with JetBrains' actual PyCharm 2026.2 release metadata.

Authoritative PyCharm release records show:

- PyCharm 2026.2 = `262.8665.309`
- PyCharm 2026.2.0.1 = `262.8665.369`
- PyCharm 2026.2.1 = `262.9437.214`
- PyCharm 2026.2.2 = `262.10315.174`

JetBrains Marketplace compatibility records likewise identify PyCharm 2026.2 artifacts on the `262` line.

## Repaired boundary

For PREFIX-EDITOR-002, the first qualification boundary is:

- product: PyCharm unified product
- release line: 2026.2.x
- actual platform branch: `262`
- initial minimum stable build: `262.8665.309` (PyCharm 2026.2 GA)
- descriptor `since-build`: `262.8665.309`
- descriptor `until-build`: `262.*`
- operating systems: Windows x64 and Linux x64
- files: ordinary local writable `.py` files only

The adapter must be compiled and verified against an actual 2026.2.x PyCharm distribution, not against the erroneous row in the generic SDK table.

## Toolchain correction

The prior map also tied Java 25 to “2026.2”. JetBrains' SDK pages currently state Java 25 for 2026.2+, but because the branch-label table itself is contradictory, the proof build must derive its toolchain from the actual selected PyCharm 2026.2 platform artifact and Gradle platform metadata. The implementation must not hard-code a Java/toolchain claim until that artifact resolves successfully.

## Stop decision

Per the campaign instruction, no adapter implementation was improvised across this contradiction. No Kotlin source, plugin descriptor, Gradle build, tests, or packaged plugin were created in this stopped pass.

The next implementation pass starts from this repaired boundary and must first resolve/download the actual PyCharm 2026.2 platform artifact. Only then may it create the isolated Kotlin adapter and run Plugin Verifier.

## Follow-up capability explicitly not claimed

Editor-originated receipt generation remains outside this adapter proof. The existing qualified engine/CLI receipt contract is unchanged.
