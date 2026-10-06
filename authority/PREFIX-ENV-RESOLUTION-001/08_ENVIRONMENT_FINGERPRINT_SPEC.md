# Environment Fingerprint Specification
Canonical JSON, sorted keys, UTF-8, SHA-256. Schema PREFIX-ENV-FP-001.

Required identity inputs: implementation name; Python major.minor.micro; normalized executable identity/path; normalized sys.prefix and sys.base_prefix; venv boolean.

Resolution inputs: ordered sys.meta_path classifier identities; ordered sys.path values with empty-string retained semantically; ordered sys.path_hooks classifier identities; operation project root when explicitly supplied; package context and relevant package __path__ for submodule/relative requests; current working directory only when empty-string/equivalent relative search input makes CWD resolution-relevant.

Do not include: CPU/RAM, hostname, unrelated environment variables, arbitrary installed applications, unrelated filesystem timestamps, user documents, network state.

Module-specific evidence is NOT folded into the base environment fingerprint. Each resolution report separately hashes request + environment_fingerprint + relevant parent-package path snapshot + spec evidence. This prevents one module's existence from redefining environment identity while still detecting resolution changes.

Custom finder/hook objects are fingerprinted by stable classifier evidence (module + qualified class/type name and order), not memory addresses/repr. If stable classification cannot be produced, fingerprint state is AUTHORITY_INSUFFICIENT rather than inventing stability.