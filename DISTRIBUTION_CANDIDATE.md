# PREFIX for Python 0.1.0 distribution candidate

This candidate integrates existing commercial entitlement and secure input with
the qualified source at `77d742f0d764064f8ffac8a9ae2101823a4bb2c8`. The engine,
AST bridge, operator console and version module retain their qualified bytes.
The CLI dispatch wrapper, operator entry point, installers and existing editor
adapters use the same entitlement policy. Correction rules were not redesigned.

The existing product is $29 USD once through the existing Lemon Squeezy checkout:
https://fastlaunch.lemonsqueezy.com/checkout/buy/37f6bf48-4f0d-4151-a076-8b60f030e985

The currently published checkout promises the qualified keyless package. This
candidate requires activation before correction. It must not replace that
promised download until the owner confirms license-key delivery and authorizes
the matching customer promise and artifacts. No production activation, purchase,
receipt delivery, publisher agreement or marketplace publication is established
by the candidate's technical tests.

## Candidate installation and activation

Windows x64 includes its private CPython 3.12.10 runtime and requires VS Code.
Linux x64 requires an installed CPython 3.12; its VS Code installation is optional
for CLI use. Payload hashes are checked before installation. An unactivated
installer smoke check records `REFUSE_INVALID` with `entitlement_required` and
does not mistake that expected refusal for a broken installation.

Use `prefix-python license activate` after installing. The prompt hides the key;
do not place a key in command arguments. Editor activation uses password input
and sends it to the same CLI through standard input. `license status --json`,
`license validate`, and `license deactivate` use the same local state. Activation
and validation contact Lemon Squeezy. Corrections operate locally; the retained
cache policy allows seven days without validation and a thirty-day grace period.

For a wheel, use a CPython 3.12 environment and install the exact wheel supplied
with `DISTRIBUTION_MANIFEST.json`. `prefix-python` and `prefix-python-ops` both
enforce the gate. A successful installation or synthetic fixture test is not a
live customer entitlement.

Run `python tools/run_distribution_tests.py` to verify source regressions with a
temporary synthetic entitlement. Hosted qualification uses standard runners in
the existing public repository, without caches, signing or publication. Results
are limited to the exact recorded source commit and artifact hashes. Actual
extension-host checks and PyCharm SDK editor fixtures are recorded separately;
rendered PyCharm GUI interaction and production key delivery require their own
evidence.

Public installation instructions for the currently offered keyless package:
https://fast-industries-prefix.steven-k-ratushniak.chatgpt.site/prefix/install/
Technical issues: https://github.com/stevenkratushniak-ctrl/PREFIX-for-Python/issues
Keep license keys, receipts and private source code out of public issues. Use the
seller contact on the actual purchase receipt for private order matters.
