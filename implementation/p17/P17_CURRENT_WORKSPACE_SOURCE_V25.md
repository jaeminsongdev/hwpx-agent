# P17 current workspace source qualification v25

Date: 2026-09-07

Scope: P06-04 bounded Hangul readback source-binding successor only

Decision: **qualified source boundary only; no P06 card, phase, runtime or product PASS**

The v1-v24 qualification contracts remain byte-for-byte unchanged. This v25 layer composes exact
v24 contract SHA-256 `02e12717738bf70bf76ea69da516a583ed06901ed294700c3853e9b0f84e3d19`
and advances the P06-04 runtime-readback source view to clean commit
`6d7bf929644cfb8c2ae326c351431df73711a95e`.

Current-host source acceptance run `3af6a98241e649f4b3f08e943bb2a61f` passed all 11 checks. Its
canonical receipt SHA-256 is
`c55d51b40764ecccbfba839f35555d6edd8850a6134994f4d77037b61280c043`. The twenty-five legacy
successors and locked/offline 25-member Cargo projection remain exact.

This layer binds six exact changed files: the P06-04 runtime policy and private contract, the thin
cell-style readback wrapper, its fifteen-case static/preflight suite, and the updated contract
validator plus negative tests. The wrapper delegates to the previously qualified x86 STA watchdog
with an exact P06 schema and error namespace; it does not duplicate or weaken that engine.

This proves source bytes and composition only. The current source-fixture automation remains
waiting for visible user file-access approval. No source or target HWPX runtime result, PDF visual
review, current/independent FULL PASS, arbitrary document, another PC/version, production, phase
completion or product completion is claimed.
