# P17 current workspace source qualification v23

Date: 2026-09-07

Scope: P06-03 table merge/split current-PC source-binding successor only

Decision: **qualified source boundary only; no P06 card, phase, runtime or product PASS**

The v1-v22 qualification contracts remain byte-for-byte unchanged. This v23 layer composes exact
v22 contract SHA-256 `2d52898b8d232ea819f4f875a3760ba676dc7d67899f78687987014cead3e176`
and advances the P06-03 source view to clean implementation commit
`0bd152dd85fa42632f8f7213e96e445af44524be`.

Current-host source acceptance run `d39fd169945141d5ae2f968cb0b10b08` passed all 11 checks. Its
canonical receipt SHA-256 is
`e6ba2648c19874056a22646db9fde8948d89864227d260546ecd40768fb043bf`. The twenty-five legacy
successors and locked/offline 25-member Cargo projection remain exact.

This layer additionally binds eight exact P06-03 implementation files: the `domain-ir` merge/split
module, updated exports and property/conflict tests; the private v1 contract and explicit migration;
the P06-03 policy; the contract validator and its negative tests. P06 validation remains separate
from the immutable P15 CI source-lock chain.

P06-03 intentionally changes `crates/domain-ir/src/lib.rs`, which v22 locked at the P06-02 revision.
The v23 verifier therefore authenticates the immutable v22 contract by its exact digest and binds the
new `lib.rs` from commit history. It does not replay the obsolete v22 workspace-byte comparison or
rewrite the predecessor contract.

This proves only exact source bytes and composition. P06-03 still requires separate Windows/offline
Linux, current/independent FULL, security and strict-review evidence before it can be marked complete.
It does not claim actual Flow-byte semantics, HWPX table lifting/lowering, Hangul execution,
rendering, another PC/version, production, phase completion or product completion.
