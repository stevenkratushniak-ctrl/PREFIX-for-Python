# Import Domain Boundary
Authority ID: PREFIX-PY312-IMPORT-001. Parent: PREFIX-PYTHON-NEXT-001. Python: CPython 3.12.x.

Inside: ordinary source import/from-import statements; dotted module names; aliases; comma/parenthesized targets; star form; explicit relative levels; AST Import/ImportFrom/alias binding shape; mechanically supplied project roots and interpreter/environment snapshots used only as resolution evidence.

Layers remain separate: L1 grammar; L2 AST structure; L3 module resolution evidence; L4 requested-symbol evidence; L5 local binding; L6 environment availability.

Outside: package installation/removal; network/index lookup; dependency solving; lockfile/build-backend rewriting; arbitrary packaging; executing candidate modules merely to discover exports; unmodeled import hooks/loaders; generated/remote modules; monkey-patched import state; semantic package preference; cross-environment claims without a pinned snapshot.

Filesystem existence is evidence, not universal runtime-import proof. Python permits extensible finders/hooks, namespace packages, mutable package paths and replacement import behavior.