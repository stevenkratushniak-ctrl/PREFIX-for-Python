# Import ↔ Environment Interface
Python authority can report: source structure, requested target, relative level, alias/binding and pinned resolver evidence.

Environment/dependency authority owns intended interpreter/environment, declared dependencies, installed artifacts, environment construction, acquisition, lock solving and install/remove actions.

Handoff fields: state_id, source location, requested_module, relative_level, package_context, interpreter_identity, sys_path_fingerprint, finder classification/fingerprint, spec status/origin/search locations, requested_symbol, static-symbol evidence, dynamic-risk flags and missing_authority.

Stable handoffs: ENV-MODULE-ABSENT_IN_PINNED_ENV; ENV-MODULE-PRESENT_OTHER_PINNED_ENV; ENV-CUSTOM_FINDER_ACTIVE; ENV-PACKAGE_CONTEXT_MISSING. No handoff authorizes installation.