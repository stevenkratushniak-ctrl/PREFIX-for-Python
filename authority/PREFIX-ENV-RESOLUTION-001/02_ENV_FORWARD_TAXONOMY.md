# Environment Forward Taxonomy
ENV-INT-001 supported CPython 3.12 identity -> PINNED_SUPPORTED.
ENV-INT-002 non-3.12/non-CPython where CPython-specific claim required -> UNSUPPORTED_ENVIRONMENT.
ENV-INT-003 interpreter identity unavailable -> AUTHORITY_INSUFFICIENT.
ENV-ID-001 sys.prefix == sys.base_prefix -> BASE_ENVIRONMENT.
ENV-ID-002 prefixes differ -> VIRTUAL_ENVIRONMENT.
ENV-PATH-001 ordered effective search inputs captured -> PINNED_PATH.
ENV-PATH-002 duplicate/overlapping entries -> PINNED_WITH_OVERLAP; resolution order retained.
ENV-PATH-003 active empty-string path -> CWD_SENSITIVE.
ENV-PATH-004 path/finder inputs observed changing during claim -> UNSTABLE_SNAPSHOT.
ENV-FIND-001 default BuiltinImporter/FrozenImporter/PathFinder surface -> STANDARD_FINDERS.
ENV-FIND-002 additional/replaced meta finder -> CUSTOM_FINDER_ACTIVE.
ENV-HOOK-001 default path hooks/classified zip/filesystem -> STANDARD_OR_CLASSIFIED_PATH_HOOKS.
ENV-HOOK-002 unmodeled path hook -> CUSTOM_PATH_HOOK_ACTIVE.
ENV-MOD-001 spec identifies built-in -> RESOLVED_BUILTIN.
ENV-MOD-002 spec identifies frozen -> RESOLVED_FROZEN.
ENV-MOD-003 file-backed source/bytecode/extension -> RESOLVED_LOCATION.
ENV-MOD-004 package spec with search locations -> RESOLVED_REGULAR_PACKAGE unless namespace evidence.
ENV-MOD-005 origin None + package search portions -> RESOLVED_NAMESPACE_PACKAGE.
ENV-MOD-006 spec supplied by unmodeled custom finder -> RESOLVED_BY_CUSTOM_FINDER, not standard-proof.
ENV-MOD-007 no spec under stable standard pinned surface -> ABSENT_IN_PINNED_ENVIRONMENT.
ENV-MOD-008 parent package context/path unavailable -> PACKAGE_CONTEXT_REQUIRED.
ENV-MOD-009 spec exists but loader execution untested -> RESOLUTION_FOUND_LOAD_UNPROVEN.
ENV-DIST-001 distribution metadata maps/provides evidence for resolved location -> DISTRIBUTION_EVIDENCE_ONLY.
ENV-DIST-002 module-to-distribution mapping absent/plural -> NO_INSTALL_INFERENCE.