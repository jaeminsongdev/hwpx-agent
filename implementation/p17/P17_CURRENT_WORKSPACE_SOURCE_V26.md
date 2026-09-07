# P17 current workspace source qualification v26

Date: 2026-09-07

Scope: P06-04 canonical source-fixture text evidence successor only

Decision: **qualified source boundary only; no P06 card, phase, runtime or product PASS**

The v1-v25 qualification contracts remain byte-for-byte unchanged. This v26 layer composes exact
v25 contract SHA-256 `408c8531ed2775f45cb13f20f65edf1eead6ac4363cf5201c9e0589aba671393`
and advances the P06-04 source-fixture evidence view to clean commit
`2d18ae2ca704797819be7f749e21b1dc1bfd53ac`.

Current-host source acceptance run `3abc86939089473f972cb09a5e1bce57` passed all 11 checks. Its
canonical receipt SHA-256 is
`05b1f716356fbd358a6ab353c43beb0f977ab8e273f1da44eedd7a3c65d7b33c`. The twenty-five legacy
successors and locked/offline 25-member Cargo projection remain exact.

This layer binds the source-fixture generator and its contract validator and negative tests. The
generator now applies the same NUL removal, LF newline normalization, Unicode NFC normalization and
trailing-LF removal as the bounded Hangul readback engine before hashing visible text. This makes the
generated trace an exact predeclared text binding for the later save/reopen check.

This proves source bytes and composition only. The already-running source-fixture process loaded the
pre-fix script and remains waiting for visible user file-access approval, so it cannot establish this
new runtime claim. No source or target HWPX result, PDF visual review, current/independent FULL PASS,
arbitrary document, another PC/version, production, phase completion or product completion is claimed.
