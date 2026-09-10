# P17 current-workspace source v40 to frozen verifier v1

## Problem

The v40 generator validates current worktree bytes and an ignored acceptance receipt. That is
correct while producing the qualification, but it is not a durable historical audit after those
sources legitimately change.

## Replacement

`tools/p17/frozen_current_source_v40.py verify` is the verification entrypoint for the committed
v40 qualification. It first verifies the immutable v39 predecessor, then reads the exact v40
contract and current snapshot from qualification commit
`7167e0e1a14c6075f57608acd7ff89bd3d14a060`. It checks base commit
`131ce732e59f2360a713a14391bbff45d1dbde73`, ancestry, the exact v39 predecessor contract, nine
implementation sources, twenty-eight successors, three qualification guards and all claims from
bounded Git blobs.

The v40 implementation list and successor list both contain `Cargo.lock`. The frozen verifier
accepts exactly that one overlap and rejects every other overlap. This is an explicit redundant
binding of the same base-commit blob, not an extra test or product claim.

The v1-v40 generators and qualification artifacts remain unchanged as historical generation
records. The frozen v39 verifier is the only runtime dependency and is itself source-locked by the
private v40 contract.

## Evidence boundary

The ignored acceptance receipt remains outside Git, so only its exact committed path, run ID and
SHA-256 references are verified. `receipt_blob_verified` stays false. No authenticated dispatcher,
PostgreSQL sync state machine, remote network execution, actual Hangul run, production state,
P17-06 completion or product completion is claimed.
