# P17 current workspace source qualification v21

Date: 2026-09-07

Scope: P06-01 TableGrid current-PC source-binding successor only

Decision: **qualified source boundary only; no P06 card, phase, runtime or product PASS**

The v1-v20 qualification contracts remain byte-for-byte unchanged. This v21 layer composes exact v20
contract SHA-256 `adca1fbccedad8b4c6dfb7dbd223f86b02a7ba5f9357c21220340b3796969d22`
and advances the P06-01 source view to clean implementation commit
`0b8db6e695f60cae8b9e59bd988922fb7e90b9f1`.

Current-host source acceptance run `ad8c1afa1c6b42d0a34469dbbd4471ca` passed all 11 checks. Its
canonical receipt SHA-256 is
`2ec4bd69fbe3f20003ce2b0774dc6e62fb5b039b0d3798e68502321d1e22d94f`. The twenty-five legacy
successors and locked/offline 25-member Cargo projection remain exact.

This layer additionally binds nine exact P06 implementation files: the `domain-ir` TableGrid module,
exports and tests; the private v1 contract and explicit migration; the P06-01 policy; the contract
validator and negative tests; and CI registration. The qualification guard, tests and this report are
also digest-bound in the v21 contract.

This proves only exact source bytes and composition. P06-01 requires separate Windows/offline Linux,
current/independent FULL, security and strict-review evidence before it can be marked complete. It does
not claim HWPX table lifting/lowering, Hangul execution, rendering, another PC/version, production,
phase completion or product completion.
