# P17 current workspace source qualification v24

Date: 2026-09-07

Scope: P06-04 table cell-style current-PC source-binding successor only

Decision: **qualified source boundary only; no P06 card, phase, runtime or product PASS**

The v1-v23 qualification contracts remain byte-for-byte unchanged. This v24 layer composes exact
v23 contract SHA-256 `62ed365ab62c367f4c25483a53333c185d34bfcbca09aa60d695da5780184aff`
and advances the P06-04 source view to clean implementation commit
`29e96cc54d03f96031cc059b7590846dc1a528ed`.

Current-host source acceptance run `402b0e3af3f34108b2ab670c70bcdf64` passed all 11 checks. Its
canonical receipt SHA-256 is
`00869670774e8ada8c052e8f30c7764c03b90016f33996c126dd4a0c9c45b4b2`. The twenty-five legacy
successors and locked/offline 25-member Cargo projection remain exact.

This layer additionally binds ten exact P06-04 implementation files: the preserving cell-style
reader/lowerer, exports, boundary and deterministic tests, bounded target package tool, private v1
contract and migration, policy, exact Hangul 2020 synthetic-source runner, contract validator and
negative tests. P06 validation remains separate from the immutable P15 CI source-lock chain.

P06-04 changes `crates/hwpx-package/src/lib.rs`, which v23 locked at the P06-03 revision. The v24
verifier therefore authenticates the immutable v23 contract by its exact digest and binds the new
`lib.rs` from commit history. It does not replay obsolete workspace bytes or rewrite predecessor
evidence.

This proves exact source bytes and composition only. The visible Hangul 2020 automation is still
waiting for user file-access approval. Source HWPX creation, product-generated target save/reopen,
strict semantic readback, PDF verification, visual review, current/independent FULL, security and
strict-review evidence remain separate requirements before P06-04 can close. It does not claim an
actual Hangul PASS, arbitrary-document compatibility, another PC/version, production, phase
completion or product completion.
