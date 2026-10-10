# PREFIX-EDITOR-002 JetBrains Proof Notes

## Authority
Base: 33b61e9059c06d295aff9eb62bf4b4feb1dc3d56 / d1d7a9df87073924375c785ac52cab33d85aca61.
Boundary repair: 9b1167cccf0c24bf7142ac6501151380627d0c08 / f81920ff553f96d24984adce894d03b6111b06a9.

## Repaired implementation detail
EnterHandlerDelegate executes synchronously in the Enter write path. PREFIX is an external process, so blocking preprocessEnter on engine execution would violate the mapped responsiveness/threading requirement. The proof uses postProcessEnter as the Enter admission trigger: the normal Enter produces the proposed state, that exact state is evaluated off-EDT, and mutation is admitted only if the document modification stamp, text, caret, editor identity and writability still match when the result returns.

## Receipt boundary
Editor-originated mutations do NOT claim CLI --apply receipts. Editor receipt generation is a separate future bounded capability.

## Deliberately absent
No licensing changes, Marketplace publication, notebook/remote support, macOS/ARM64 support, cloud correction, PSI correction authority, or changes to prefix_python/ or editor/vscode/.
