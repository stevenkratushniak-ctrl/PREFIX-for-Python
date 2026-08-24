# PREFIX Python RC2 Closure Report

## Final Status

`PREFIX_0_1_0_RC2_RELEASE_PROOF_BLOCKED`

The sealed artifacts remain byte-identical, historical Git authority is recovered, representative CPython patch qualification is complete, and signing readiness is prepared. Local release closure cannot be claimed because the real VS Code extension-host proof is blocked by an active updater and the Node build dependency audit contains unresolved high/moderate findings.

## 1. Source Authority

Verdict: `CANONICAL_GIT_AUTHORITY_FOUND`.

Historical authority is `C:\FastIndustries`, remote `https://github.com/stevenkratushniak-ctrl/FastIndustries.git`, observed at commit `037fd19738c327421182de791dee0134d610c624` and tree `29a721c25c77b38d7cb3800dac777a0850b8e6d8`.

The `ConstrainedPython` subtree was clean at tree `874acbdaddb691efa17488a74722f94b45e20546`. The standalone comparison covered all 95 tracked files: 32 identical, 63 different, 0 missing. The mechanically synchronized RC2 source is committed only on local branch `codex/prefix-rc2-close-002`; its exact commit/tree receipt is recorded in the final local evidence manifest after commit. No push or default-branch change is authorized.

## 2. VS Code Extension Host

Verdict: `VSCODE_EXTENSION_HOST_ACTIVATION_BLOCKED_BY_ACTIVE_UPDATER`.

Isolated VSIX installation, listing, settings, CPython 3.12.6 wheel execution outside the checkout, and normal-profile non-mutation are proven. Real-host activation, host command registration/invocation, visible result rendering, and invalid-config rendering are not proven because VS Code 1.119.0 terminated both isolated launches with its active-update guard.

## 3. CPython Patch Range

Verdict: `VALIDATED_ONLY_ON_EXACT_PATCH_SET`.

Proven exact patches: 3.12.0, 3.12.6, and 3.12.10. Their AST class/field surface and PREFIX transition output surface are equal. `ast.unparse()` is not patch-invariant, and source-only 3.12.11 through 3.12.14 were not executed. No complete 3.12.x qualification claim is made.

## 4. Registry Audits

Python: the package has no runtime dependencies. The controlled environment with pip 26.2 returned no known vulnerabilities; the initial bundled pip 24.2 had seven pip-only records. The private package itself is not vulnerability-matched by PyPI.

Node: npm returned 2 moderate and 7 high findings in the development/build graph. The shipped VSIX embeds no `node_modules`, but the build supply-chain finding is unresolved. The package lock was not changed.

## 5. Signing

`PREFIX_RC2_SIGNING_READINESS_PACKET.md` binds the exact standalone and ZIP-contained artifact identities to detached Sigstore, PEP 740/PyPI, and VSIX manifest/P7S options. Nothing was signed and no owner credential was touched.

## 6. Immutable Artifact Identities

- release ZIP: `7a92c318ce9be3f93ba97d319d2d1d1ebcba323205b4690c669e70485fb5d82d`
- standalone wheel: `feb085394d9a441d8202e546f2f9c55fd43c2aeaf735e5bb564c455636042b4a`
- standalone VSIX: `02a332530f55ff785e7f41d5e8004245c21033e7ea27e54dc2df586db757e4bf`
- top-level checksums: `b8ed9480ded428b4accc8536d991824c0feaa1c1e92281af462b4bba64fa936c`
- bundle checksums: `20834482597a1b9af65b7cb082e9573d32cbb41c4a532d3d751a404ea676c220`
- bundle manifest: `0bc2aeee84d392d376fa52424b697887bad1bc1affd5b3cda5baaba80db961bb`

## 7. Owner Decisions

1. Close normal VS Code and let the updater finish, then authorize the isolated real-host proof rerun.
2. Decide whether to remediate the Node development dependency findings and rebuild/re-hash, or explicitly accept them for RC2 based on the zero-embedded-dependency artifact evidence.
3. Decide whether public support language remains broad `3.12.x` metadata or is constrained to the exact qualified patch set pending source-only patch qualification.
4. Select the owner signing identity and channel mechanism only after the proof blockers are closed or accepted.

## 8. Scope Integrity

No runtime behavior, Python metadata, release artifact, checksum file, normal VS Code profile, default Git branch, remote, key, certificate, or publication service was changed.
