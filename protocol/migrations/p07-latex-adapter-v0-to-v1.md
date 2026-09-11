# P07 LaTeX adapter v0 to v1 migration

`hwpx-agent.latex-adapter/v1` and `hwpx-agent.latex-parser/tier-a-v1` replace the design-only LaTeX
source placeholder with a private, finite and fail-closed adapter into `hwpx-agent.math-ast/v1`.

There is no stored v0 adapter result to rewrite. Existing documents, public capability schemas,
MathAst v1 and equation source strings remain unchanged. A caller opts into v1 by providing exactly
one source string plus zero or more bounded macro definitions. Macro bodies are expanded only in the
adapter sandbox and are not retained as independent result fields.

Previously unspecified adjacency, multi-letter identifiers, ordinary function application and
unary-minus power precedence now return explicit candidates. Migration MUST NOT select the preferred candidate automatically.
Unsupported commands and constructs fail with a content-free code; text or image fallback is never
introduced.

The v1 result binds the parser/model/normalization versions, source SHA-256, exact byte/token/macro
counts, every retained ambiguity site and the complete admitted MathAst. MathML, EqEdit, HWPX,
native Hangul execution, save/reopen, rendering and automation remain separate P07 Gates and are not
promoted by this migration.
