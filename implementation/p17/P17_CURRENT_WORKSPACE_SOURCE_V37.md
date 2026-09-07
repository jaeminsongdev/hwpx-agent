# P17 current workspace source qualification v37

Date: 2026-09-07

Scope: exact P06-06 current-PC Hangul 2020 formula adapter source successor only

Decision: **qualified source only; the P06-06 contract separately attests actual source capture and
adapter-component evidence, while this generic qualification keeps runtime, P06-06/P06,
production and product claims false**

The v1-v36 qualification contracts remain byte-for-byte unchanged. This v37 layer composes exact
v36 contract SHA-256 `9758f4510a17459e28667aacbe729ee43336729218dea9343dc57dd11c5138ab`
and binds clean implementation commit
`9814876d3848a173c00035ead14b78c718201720`.

Current-host source acceptance run `35e5459c8f3f492e81837945fed09247` passed all 11 checks. Its
canonical receipt SHA-256 is
`2d230b29f891f851fc3256b01f027cc5b5ddecdffb5250c167bd5003d17dff4b`. The twenty-six cumulative
successors, locked/offline 25-member Cargo projection, and generic runtime/production false claims
are preserved exactly.

The nine bound files add the package export, exact native-shape lift/lower adapter, Rust integration
tests, read-only actual-source checker, additive migration, component report, exact contract,
ignored-evidence validator and negative tests. The source binds the named current-PC evidence hashes
without copying private artifacts into Git or exposing native commands through the public API.

This source-only qualification deliberately does not reclassify its own generic `actual_hangul`,
`p06_06_actual_source_capture_verified`, `p06_06_actual_source_adapter_readback_verified`,
`p06_06_product_target_oracle_verified`, or `p06_06_complete` claims. Actual decisions belong to
the P06-06 HWPX contract and remain fail-closed if ignored evidence is absent or changed. Structural
differential, altered product target, another PC/version, arbitrary documents, P06 completion,
production and product completion are not claimed.
