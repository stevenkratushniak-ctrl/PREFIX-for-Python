# ADVISE / ANALYZE / REFUSE Map
For either V2 surface: 2+ valid bounded insertion successors -> ADVISE only, never mutate. Zero successors -> ROADMAP/REFUSE. Malformed surrounding grammar, lexical uncertainty, failed AST invariant, or runtime-dependent interpretation -> ROADMAP/REFUSE.

High-value non-APPLY inventory: unexpected/dedent states -> ANALYZE where detection is reliable; positional-after-keyword, duplicate keyword, and default-order signature failures -> ANALYZE; missing comma, unterminated strings, with/import alias ambiguity, conditional assignment/comparison, leading-zero literals -> ROADMAP unless a future narrower boundary proves singularity.

Existing V1 lanes and refusal codes remain authoritative and unchanged.