# P17 current workspace source qualification v21

Date: 2026-09-07

Scope: P06-01 TableGrid current-PC source-binding successor only

Decision: **qualified source boundary only; no P06 card, phase, runtime or product PASS**

The v1-v20 qualification contracts remain byte-for-byte unchanged. This v21 layer composes exact v20
contract SHA-256 `adca1fbccedad8b4c6dfb7dbd223f86b02a7ba5f9357c21220340b3796969d22`
and advances the P06-01 source view to clean implementation commit
`6e49b0f6d3937d1026f3a0395e1a58bf405a148c`.

Current-host source acceptance run `70de52be98564f43b030557435682606` passed all 11 checks. Its
canonical receipt SHA-256 is
`c44885ee42ef8e245fb6120b542474a32998ce4afe4d33d9326946dfb2b01d9d`. The twenty-five legacy
successors and locked/offline 25-member Cargo projection remain exact.

This layer additionally binds eight exact P06 implementation files: the `domain-ir` TableGrid module,
exports and tests; the private v1 contract and explicit migration; the P06-01 policy; the contract
validator and negative tests. P06 validation is executed as separately recorded evidence so the
immutable P15 CI source-lock chain is not rewritten. The qualification guard, tests and this report
are also digest-bound in the v21 contract.

This proves only exact source bytes and composition. P06-01 requires separate Windows/offline Linux,
current/independent FULL, security and strict-review evidence before it can be marked complete. It does
not claim HWPX table lifting/lowering, Hangul execution, rendering, another PC/version, production,
phase completion or product completion.
