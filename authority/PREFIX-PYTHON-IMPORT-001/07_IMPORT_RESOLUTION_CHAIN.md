# Import Resolution Chain
SOURCE -> Python 3.12 grammar -> Import/ImportFrom AST -> absolute/relative target derivation -> pinned import context -> module spec/search evidence -> optional symbol evidence -> local binding -> classification.

Statically strong: grammar, AST shape, aliases, dot count, syntactic binding, declarations in inspectable project source.

Snapshot-dependent: interpreter, sys.path, cwd, parent __path__, sys.modules and finder configuration.

General-case dynamic boundary: custom meta/path finders, loader execution, module side effects, module __getattr__, runtime re-exports, mutable __path__, generated/network modules and monkey-patched __import__.

FOUND_SPEC is not LOAD_PROVEN: loader execution can still fail. Import-001 does not execute candidate imports to manufacture proof.