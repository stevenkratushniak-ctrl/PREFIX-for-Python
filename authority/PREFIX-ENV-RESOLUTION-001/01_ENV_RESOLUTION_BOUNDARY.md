# Environment Resolution Boundary
Authority: PREFIX-ENV-RESOLUTION-001. Parent import authority: c4cb1f267e7a57ee7e1d1661f9a26f08891d49ab.

Inside is only observable state capable of changing resolution of the current Python import request: implementation/version/executable, sys.prefix/base_prefix, venv relation, ordered effective search inputs, operation project/package context, sys.meta_path and sys.path_hooks classification, relevant package __path__, built-in/frozen identity, ModuleSpec evidence, namespace portions, local/package/zip/distribution provenance when mechanically observable.

Outside: unrelated hardware/OS state, arbitrary filesystem inventory, network indexes, package acquisition/install/remove, dependency solving, environment mutation, executing candidate modules for proof, arbitrary custom-finder semantics, runtime side effects and source correction.

Relevance law: state is included only if changing it can alter the bounded resolution claim or the identity of the environment to which that claim applies.