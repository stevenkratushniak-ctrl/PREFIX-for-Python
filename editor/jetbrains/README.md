# PREFIX for Python

This plugin connects local Python files in PyCharm to the existing PREFIX 0.1.0 engine. It applies mapped structural corrections, evaluates selected Python structure, and refuses unsupported or ambiguous input. Correction runs locally on CPython 3.12.

The commercial integration is a candidate for qualification. The current Lemon Squeezy delivery still advertises the older package without a license key or online activation. Do not install this candidate for a paying customer until the matching commercial runtime, provider key delivery, and final qualification are admitted together.

## Installation and activation

1. Install the matching PREFIX for Python commercial runtime for Windows x64 or Linux x64 with CPython 3.12. This plugin does not bundle Python or the correction engine.
2. In the supported PyCharm 2026.2 installation, open **Settings > Plugins**, choose the gear menu, then **Install Plugin from Disk** and select the final qualified PREFIX plugin ZIP.
3. Restart PyCharm when requested and open a local `.py` file.
4. Choose **Tools > PREFIX for Python > Activate License**. Paste the key supplied with the same PREFIX purchase used by the CLI and VS Code adapter. The field masks the key. Activation sends it to Lemon Squeezy through the engine, using standard input rather than command arguments.
5. Use **License Status** to confirm the shared installation entitlement. **Validate License** refreshes it. **Deactivate This Installation** releases the installation through the same engine.

The plugin first asks the shared engine for license status. It refuses correction when the entitlement is unavailable, expired, invalid, or absent. An older engine with the same 0.1.0 version but no commercial license command is insufficient.

## Correction commands

Use **Tools > PREFIX for Python > PREFIX: Govern Active Python Transition** to evaluate the active document. Select Python text and use **PREFIX: Govern Selected Python Structure** to evaluate only that structure. Mapped block corrections are also evaluated after normal Enter processing. The engine runs away from the UI thread, and a result can change the editor only while the document text, caret, modification stamp, editor identity, and writability still match the submitted state.

Supported work is restricted to local writable `.py` documents with one caret. Notebook cells, remote development, macOS, and ARM64 are outside this candidate's support boundary. Editor changes do not produce CLI `--apply` receipts. CLI receipt inspection, replay, and rollback remain separate engine workflows.

## Runtime discovery

The plugin uses the existing installed runtime path, then CPython 3.12. A `PREFIX_PYTHON_ENGINE` environment value can specify the matching interpreter explicitly. The optional JVM system property `prefixPython.pythonCommand` takes precedence. These values identify an executable; they never contain a license key.

The matching engine owns its standard entitlement directory, key storage, integrity checks, validation interval, and offline grace. The plugin creates no second commercial account, entitlement, key store, or pricing policy.

## Purchase and support

PREFIX for Python is one product at 29 USD once. Use the [existing Lemon Squeezy checkout](https://fastlaunch.lemonsqueezy.com/checkout/buy/37f6bf48-4f0d-4151-a076-8b60f030e985). Commercial support follows the order receipt; technical issues can be filed in the [PREFIX repository](https://github.com/stevenkratushniak-ctrl/PREFIX-for-Python/issues).

The [product page](https://fast-industries-prefix.steven-k-ratushniak.chatgpt.site/prefix/) and current [license](https://fast-industries-prefix.steven-k-ratushniak.chatgpt.site/legal/prefix/license/), [privacy](https://fast-industries-prefix.steven-k-ratushniak.chatgpt.site/legal/prefix/privacy/), and [refund](https://fast-industries-prefix.steven-k-ratushniak.chatgpt.site/legal/prefix/refund/) pages describe the existing offer. Candidate online activation requires matching terms and provider delivery before release.
