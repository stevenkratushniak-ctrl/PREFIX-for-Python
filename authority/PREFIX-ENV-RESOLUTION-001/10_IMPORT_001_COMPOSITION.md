# Import-001 Composition
Import authority remains independent. It emits a structurally valid request and one of its environment handoffs.

ENV-MODULE-ABSENT_IN_PINNED_ENV -> Environment authority verifies fingerprint/snapshot and may return ABSENT_IN_PINNED_ENVIRONMENT.
ENV-MODULE-PRESENT_OTHER_PINNED_ENV -> compare independently fingerprinted reports; no environment switch.
ENV-CUSTOM_FINDER_ACTIVE -> classify custom component; return narrowed/custom result or OUTSIDE.
ENV-PACKAGE_CONTEXT_MISSING -> request exact parent package identity/__path__ evidence; do not rewrite relative source.

Composition record links import_authority_version, import_request hash, environment_fingerprint and resolution_report hash. Neither map inherits mutation authority from the other.