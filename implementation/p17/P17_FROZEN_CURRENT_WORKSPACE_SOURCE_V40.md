# P17 frozen current-workspace source v40 verification

Date: 2026-09-10

Decision: **PASS for immutable verification of the committed v40 source-qualification state only**

The replacement `frozen_current_source_v40.py` verifies the frozen v39 predecessor and then reads
historical v40 evidence only through bounded Git blob operations. Repository-selection environment
is removed, while replace refs, lazy fetch, interactive prompts and optional Git locks remain
disabled through the frozen Git reader.

The verifier confirms base commit
`131ce732e59f2360a713a14391bbff45d1dbde73` is an ancestor of qualification commit
`7167e0e1a14c6075f57608acd7ff89bd3d14a060`, and checks:

- v40 contract: 5,064 bytes, SHA-256
  `9b7cd7d3d2eda9cf3cd8bff2e9bc67f94a8a62f60a3701bfcdc53b0cd1f08c3d`;
- v40 current snapshot: 14,559 bytes, SHA-256
  `ec98c23d9a819752631dcb0e56fcd5bf45ff6e9586dce993d7dbaba3f92e847a`;
- exact v39 predecessor contract and frozen verification;
- nine implementation source blobs at the base commit;
- twenty-eight successor blobs at the base commit;
- the exact intentional `Cargo.lock` overlap between those two lists;
- three original guard blobs at the qualification commit; and
- all fifty-three exact source-only claims, including false integration and product claims.

The private frozen-v1 contract binds the verifier, its frozen-v39 dependency, compatibility test,
boundary/tamper tests, migration and this report. The original v40 generator remains a generation
record and is no longer the verification authority for later Gates.

The frozen-v40 CLI, private-contract CLI and fifteen focused compatibility, boundary and tamper
tests pass. The full P17 Python suite is rerun separately after this frozen layer is committed.

The ignored source-acceptance receipt is not promoted to a Git blob. Only the exact path, run ID and
digest embedded in the committed v40 documents are verified, so `receipt_blob_verified=false`.
This checkpoint does not claim authenticated dispatch, PostgreSQL sync orchestration, remote Git,
actual Hangul execution, P17-06 completion, production or full-product completion.
