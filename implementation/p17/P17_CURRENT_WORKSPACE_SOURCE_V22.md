# P17 current workspace source qualification v22

Date: 2026-09-07

Scope: P06-02 table operations current-PC source-binding successor only

Decision: **qualified source boundary only; no P06 card, phase, runtime or product PASS**

The v1-v21 qualification contracts remain byte-for-byte unchanged. This v22 layer composes exact
v21 contract SHA-256 `27d25fb3c6b1ac5f0c2761b054f9c80172534c2450cb619cafdc7ee01dc4fec9`
and advances the P06-02 source view to clean implementation commit
`f0f5c1e162d46993593b1f4a45fc8afd2c620a34`.

Current-host source acceptance run `b3105583c99c49878eeeda58e5841567` passed all 11 checks. Its
canonical receipt SHA-256 is
`f527e309bc07c6217a63d07cdfa0576b38106e451a0e113e1574ec695d19ea5b`. The twenty-five legacy
successors and locked/offline 25-member Cargo projection remain exact.

This layer additionally binds eight exact P06-02 implementation files: the `domain-ir` table
operations module, updated exports and boundary/index tests; the private v1 contract and explicit
migration; the P06-02 policy; the contract validator and its negative tests. P06 validation remains
separate from the immutable P15 CI source-lock chain.

P06-02 intentionally changes `crates/domain-ir/src/lib.rs`, which v21 locked at the P06-01 revision.
The v22 verifier therefore authenticates the immutable v21 contract by its exact digest and binds the
new `lib.rs` from commit history. It does not replay the obsolete v21 workspace-byte comparison or
rewrite the predecessor contract.

This proves only exact source bytes and composition. P06-02 requires separate Windows/offline Linux,
current/independent FULL, security and strict-review evidence before it can be marked complete. It
does not claim HWPX table lifting/lowering, Hangul execution, rendering, another PC/version,
production, phase completion or product completion.
