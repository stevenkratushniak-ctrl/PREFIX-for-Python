# Next Authority Handoffs
ABSENT_IN_PINNED_ENVIRONMENT -> DEPENDENCY_DECLARATION_AUTHORITY: is this module required by declared project intent?
Declared dependency names present but module mapping unknown -> PACKAGE_DISTRIBUTION_MAPPING_AUTHORITY.
Known required distribution absent from intended environment -> INSTALLATION_AUTHORITY (separate; not granted here).
Environment identity/intended interpreter disputed -> PROJECT_RUNTIME_DECLARATION_AUTHORITY.
Custom finder semantics needed -> CUSTOM_IMPORT_PROVIDER_AUTHORITY.
Static source requests a relative module but package execution context missing -> PROJECT_PACKAGE_CONTEXT_AUTHORITY.

Directed expansion names the missing domain; it never substitutes “more context needed.”