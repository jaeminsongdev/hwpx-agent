# P17 current workspace source qualification v39

Date: 2026-09-08

Scope: exact P06-06 target-oracle closure source successor only

Decision: **qualified source only; the exact runtime contract separately proves the current-PC
Hangul 2020 target, while this generic source qualification keeps runtime, P06-06/P06, production
and product claims false**

The v1-v38 qualification contracts remain byte-for-byte unchanged. This v39 layer composes exact
v38 contract SHA-256 `818e41c4e8ee46eea3b0f31b7d769eb56d19f9de46310ed73e37285cb237ebe0`
and binds clean implementation commit
`103bbf5b0448076e3f95db939b4d186100b6a4f4`.

Current-host source acceptance run `e159d3cf21df48b38bda3f9813d8a0d1` passed all 11 checks. Its
canonical receipt SHA-256 is
`b3d0349d0e0b84900f7200938d8687cbe3b636ffecd62d2670c7197da77815c3`. The twenty-six cumulative
successors, locked/offline 25-member Cargo projection, and generic runtime/production false claims
are preserved exactly.

The seven bound files add the exact saved-HWPX oracle, renderer-cache byte preservation checks,
immutable v2 target contract and migration, closure report, failed-attempt successor note,
independent validator and tamper tests. The contract source contains exact ignored-artifact hashes;
the ignored HWPX, PDF, trace and progress artifacts themselves remain outside Git.

This source-only qualification deliberately does not reclassify
`p06_06_structural_differential_verified`, `p06_06_product_target_oracle_verified`,
`p06_06_complete`, or generic `actual_hangul`. Those runtime decisions belong to the separately
validated v2 target contract. Another PC/version, arbitrary documents, P06 completion, production
and product completion are not claimed.
