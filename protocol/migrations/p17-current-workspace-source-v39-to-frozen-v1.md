# P17 current-workspace source v39 to frozen verifier v1

## Problem

The historical v39 generator/validator imports v38 and ultimately rereads source files from the
current worktree. As those files legitimately evolve, `verify` now fails at
`implementation.bytes`. Re-executing that mutable chain is not an immutable audit of the 2026-09-08
qualification.

## Replacement

`tools/p17/frozen_current_source_v39.py verify` is the verification entrypoint for the historical
v39 qualification. It reads the exact v39 contract and current snapshot from qualification commit
`ebece5eaea645e2de0f2ba50227995969969e623`, checks the base/qualification ancestry, and validates
the predecessor, seven implementation sources, twenty-six successors and three guard sources from
their pinned Git commits. Reads are bounded and accept only full commit IDs and canonical relative
paths.

The v1-v39 generator files and qualification artifacts remain unchanged. They are historical
generation definitions, not current verification entrypoints.

## Evidence boundary

The ignored receipt is not a Git blob at either pinned commit. The frozen verifier therefore checks
only its exact path, run ID and SHA-256 references committed inside the v39 documents; it keeps
`receipt_blob_verified=false`. It does not assert actual Hangul, another PC/version, production,
P17 completion or product completion.
