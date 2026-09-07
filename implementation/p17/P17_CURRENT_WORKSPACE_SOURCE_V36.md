# P17 current workspace source qualification v36

Date: 2026-09-07

Scope: exact P06-05 calibrated target and oracle-contract source successor only

Decision: **qualified source only; the actual P06-05 runtime Gate is separately attested by its v2
contract, while this qualification keeps generic runtime, P06 phase, production and product claims
false**

The v1-v35 qualification contracts remain byte-for-byte unchanged. This v36 layer composes exact
v35 contract SHA-256 `37a2b79a528cb90b59482286ab7835674e34e2f08dddfed0c71a99dcecec72a1`
and binds clean implementation commit
`97741561c748e575eaf4c06c47acb4c15a9ab266`.

Current-host source acceptance run `3d1319eb167744489cc5b282f4b41a72` passed all 11 checks. Its
canonical receipt SHA-256 is
`932e64ef14546a04186c454b4bbffdc1afd14072d7f0e11ac08e9770fcd0df08`. The twenty-six cumulative
successors, locked/offline 25-member Cargo projection, and generic runtime/production false claims
are preserved exactly.

The six bound files add the calibrated target builder, immutable v1-to-v2 migration, exact v2
contract, P06-05 target readback report, ignored-artifact validator and negative tests. The source
binds the zero-guard and four-micrometer failed semantic calibrations, 350-micrometer calibrated
publication, exact Hangul 2020 trace, regenerated line-cache semantics and PDF evidence hashes.

This source-only qualification deliberately does not reclassify its own generic `actual_hangul`,
`p06_05_actual_target_hancom_readback_verified`, `p06_05_target_pdf_verified`, or `p06_05_complete`
claims. Those actual decisions belong to the exact v2 runtime contract and remain fail-closed if its
ignored artifacts are absent or changed. Another PC/version, arbitrary documents, P06 completion,
production and product completion are not claimed.
