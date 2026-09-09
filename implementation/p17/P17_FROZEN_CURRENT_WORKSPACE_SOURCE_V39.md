# P17 frozen current-workspace source v39 verification

Date: 2026-09-10

Decision: **PASS for immutable verification of the committed v39 source-qualification state only**

The original `current_workspace_source_qualification_v39.py verify` now fails with
`implementation.bytes` because it imports the mutable v38-to-v1 chain and rereads source files from
the current worktree. That failure is preserved; the original v1-v39 generators, qualification
documents and guards are not rewritten.

The replacement `frozen_current_source_v39.py` reads historical bytes only through bounded Git
blob operations with repository-selection environment removed and replace refs, lazy fetch,
interactive prompts and optional Git locks disabled. It verifies full commit IDs, confirms base commit
`103bbf5b0448076e3f95db939b4d186100b6a4f4` is an ancestor of qualification commit
`ebece5eaea645e2de0f2ba50227995969969e623`, and checks:

- v39 contract: 4,493 bytes, SHA-256
  `544c68cdea536e234139bd492f7e2812fe1b7ab02826af580f307284835f287c`;
- v39 current snapshot: 13,245 bytes, SHA-256
  `cb0b4acdc16433d858047026587752bb563a763bcd4f8eec48437f74f8941927`;
- exact v38 predecessor contract digest;
- seven implementation source blobs at the base commit;
- twenty-six successor blobs at the base commit, including their canonical accepted/composition
  predecessor sets;
- three original guard blobs at the qualification commit; and
- all forty-five exact source-only claims, including the false runtime/product claims.

The private frozen-v1 contract binds the new verifier, compatibility test, boundary/tamper tests,
migration and this report. Historical mutable validators remain available as generation records but
are no longer verification authority for future Gates.

The frozen-v39 CLI, private-contract CLI and sixteen focused tests pass. The broader P17 Python
suite currently runs 178 tests and still reports 31 pre-existing mutable-source errors across legacy
current-workspace, local-host and successor-admission qualifications. Those failures are not skipped
or relabeled; R-0008 remains open until they receive equivalent immutable-history verification.

The ignored receipt bytes were not committed at either pinned commit. Only the exact receipt path,
run ID and digest embedded in the committed v39 documents are verified. This checkpoint does not
claim a receipt-blob audit, actual Hangul execution, another PC/version, P17 completion, production
or full-product completion.
