# Import False-Determinism Attack
INSERT_FROM_IMPORT_CONNECTOR_V1: attack absolute/relative forms, dotted modules, one/many targets, aliases, parenthesized lists, trailing comma, star, comments/newlines, semicolons, strings/f-strings, malformed dotted names, missing targets, multiple defects and V1 delimiter interaction. A second parse-valid insertion gap destroys APPLY.

Resolver rewrites fail APPLY under same-name local modules, stdlib/third-party shadowing, packages/subpackages, namespace portions, relative context, sys.modules, custom sys.meta_path/path_hooks, mutable sys.path/__path__, conditional and TYPE_CHECKING imports, try/except fallbacks, circular initialization, generated modules and environment differences.

Symbol rewrites fail under re-exports, __all__, module __getattr__, conditional definitions, extension modules, loader-created attributes, monkey-patching and multiple valid names. Alias collision repair fails because shadowing may be intentional. Relative-level repair fails because execution context changes meaning.

Conclusion: dynamic behavior shrinks source APPLY to the mandatory from/import connector, and only under explicit cardinality proof.