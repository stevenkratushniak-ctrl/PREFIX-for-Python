# Custom Finder Boundary
Standard CPython 3.12 meta surface is classified around BuiltinImporter, FrozenImporter and PathFinder. Additional, replaced or reordered finders are first-class evidence.

A custom finder may override path processing and can even precede built-in/frozen handling. A custom path hook can reinterpret a path entry. Therefore standard absence is not claimed when an unmodeled relevant custom finder/hook is active.

If a custom finder returns a spec, report RESOLVED_BY_CUSTOM_FINDER with its stable classifier and spec fields; do not claim standard provenance or loader success. If invoking it safely/deterministically itself is outside the proof contract, refuse discovery and report the exact custom-finder authority required.