# PREFIX Python RC2 Signing Readiness Packet

## Status

Prepared and unsigned. No owner key, certificate, identity token, or publishing credential was generated, imported, selected, or used.

Signing must occur only after the remaining release-proof blockers in `PREFIX_RC2_CLOSE_002_REPORT.md` are resolved or explicitly accepted by the owner.

## Exact Unsigned Inputs

| Input | SHA-256 |
| --- | --- |
| `release/prefix-python-0.1.0-rc2.zip` | `7a92c318ce9be3f93ba97d319d2d1d1ebcba323205b4690c669e70485fb5d82d` |
| `release/prefix_python-0.1.0-py3-none-any.whl` | `feb085394d9a441d8202e546f2f9c55fd43c2aeaf735e5bb564c455636042b4a` |
| `release/prefix-python-0.1.0.vsix` | `02a332530f55ff785e7f41d5e8004245c21033e7ea27e54dc2df586db757e4bf` |
| `release/SHA256SUMS.txt` | `b8ed9480ded428b4accc8536d991824c0feaa1c1e92281af462b4bba64fa936c` |
| `release/prefix-python-0.1.0-rc2/SHA256SUMS.txt` | `20834482597a1b9af65b7cb082e9573d32cbb41c4a532d3d751a404ea676c220` |
| `release/prefix-python-0.1.0-rc2/RELEASE_VERIFICATION_MANIFEST.json` | `0bc2aeee84d392d376fa52424b697887bad1bc1affd5b3cda5baaba80db961bb` |

The ZIP contains canonicalized distribution copies. They are intentionally distinct from the top-level standalone artifacts and are already disclosed in the release notes:

| Embedded input | SHA-256 |
| --- | --- |
| ZIP-contained wheel | `ade524310084b6b8c6532ff48efa0524f0c7456293b6ecc6233606ab8d2d697e` |
| ZIP-contained VSIX | `e76ab64f9ffc60ca356a57065fa95079cb1aa7a1defe9e6f40efa7ee93a1edd2` |

A signing operator must identify whether the standalone file, the ZIP as a whole, or both are being signed. The two artifact classes are not interchangeable.

## Recommended Mechanisms

### Private blob distribution

Use detached Sigstore bundles for the ZIP, standalone wheel, standalone VSIX, and checksum files. `cosign sign-blob FILE --bundle FILE.sigstore.json` leaves the signed input bytes unchanged and creates a separate verification bundle containing the signature, certificate, and transparency-log proof.

Verification requires the owner-approved certificate identity and OIDC issuer:

```powershell
cosign verify-blob .\release\prefix-python-0.1.0-rc2.zip --bundle .\release\prefix-python-0.1.0-rc2.zip.sigstore.json --certificate-identity $CertificateIdentity --certificate-oidc-issuer $CertificateOidcIssuer
```

The owner must set `$CertificateIdentity` and `$CertificateOidcIssuer` from the approved signing identity. PREFIX must not infer them.

### Python package publication

If the wheel is later published to PyPI, use PyPI Trusted Publishing with PEP 740 digital attestations. PyPI binds each attestation to the distribution digest and Trusted Publisher identity. The attestation is detached; the wheel bytes and SHA-256 remain unchanged. Do not use legacy embedded wheel signatures or PGP uploads as the primary plan.

### VS Code Marketplace publication

For Marketplace publication, use the current `@vscode/vsce` manifest/signature workflow with an owner-approved signing tool, or Marketplace trusted publishing if the owner authorizes publication. The supported verification path is:

```powershell
npx @vscode/vsce generate-manifest -i .\release\prefix-python-0.1.0.vsix -o .\release\prefix-python-0.1.0.vsix.manifest
& $VsixSignTool '.\release\prefix-python-0.1.0.vsix.manifest' '.\release\prefix-python-0.1.0.vsix.signature.p7s'
npx @vscode/vsce verify-signature -i .\release\prefix-python-0.1.0.vsix -m .\release\prefix-python-0.1.0.vsix.manifest -s .\release\prefix-python-0.1.0.vsix.signature.p7s
```

The owner must provide `$VsixSignTool` and its certificate context. No tool or certificate has been selected in this pass.

## Timestamp and Transparency Requirements

- Sigstore: retain the generated bundle and its transparency-log inclusion proof.
- PEP 740/PyPI: retain the index provenance object and Trusted Publisher identity.
- P7S/VSIX: require the owner signing policy to specify certificate chain validation and a trusted timestamp when the selected signing tool and certificate profile support it.
- Record signing time as metadata only; it must not alter the deterministic release payload.

## Files That Change

Detached signing does not change the ZIP, wheel, VSIX, or existing checksum files. It adds only detached outputs such as:

- `*.sigstore.json`
- `*.manifest`
- `*.signature.p7s`
- a signing-result manifest containing their hashes and verification results

If an owner instead chooses an in-place or bundle-embedded signature, the modified artifact receives a new SHA-256. Every dependent manifest, checksum file, release seal, and distribution instruction must then be regenerated and reverified.

## Regeneration Order

1. Resolve or explicitly accept all release-proof blockers.
2. Freeze the exact unsigned payloads.
3. Reverify the hashes in this packet.
4. Generate detached signature or attestation outputs.
5. Verify each signature against the exact input file.
6. Hash the detached outputs.
7. Create a separate signing-result manifest.
8. If detached outputs are added to a distribution package, rebuild that package and regenerate its outer checksum and authority seal.
9. Never rewrite the original evidence to imply that an unsigned hash was signed.

## Smallest Owner Action

The owner selects one approved identity/mechanism for each distribution channel, authorizes access to that identity only during the signing operation, and returns the detached outputs for local verification. No source, runtime, or release payload change is required for detached signing.

## Primary Specifications

- VS Code extension publishing: <https://code.visualstudio.com/api/working-with-extensions/publishing-extension>
- `@vscode/vsce` signing commands: <https://github.com/microsoft/vscode-vsce>
- PyPI digital attestations: <https://docs.pypi.org/attestations/>
- PEP 740: <https://peps.python.org/pep-0740/>
- Sigstore blob signing: <https://docs.sigstore.dev/cosign/signing/signing_with_blobs/>
- Sigstore blob verification: <https://docs.sigstore.dev/cosign/verifying/verify/>
