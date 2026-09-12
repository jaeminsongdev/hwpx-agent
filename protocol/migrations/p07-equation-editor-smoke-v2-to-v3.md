# P07 equation editor smoke v2 to v3 migration

V2 required four screenshot hashes in addition to an operator attestation. That requirement did
not establish a machine visual oracle: the images were private, their contents were not evaluated
by the product verifier, and UI actions were performed by the user. V3 removes photo collection
from this card and replaces it with a bounded, plan-bound manual checklist.

Every manual UI item is represented as `user_attested`, never `passed`, `verified`, or
`screenshot_verified`. The checklist covers the planned before equation, double-click, native
editor visibility, the exact one-token change, editor close/commit, the planned post-commit
equation, Save As to `after.hwpx`, user ownership of every click and keystroke, and whether an
anomaly was reported. `anomaly_reported=true`, a missing item, Computer Use click/typing, an
unknown field, or a checklist digest mismatch fails closed. Photos are not required and cannot be
substituted for the checklist or any automated proof.

The automatic boundary is unchanged: exact Hangul 2020 identity, immutable input, before/saved/
reopened native HWPX readback, stable output, close/reopen, native object identity, semantic and
raw saved-script bindings, package graph and document-flow mutation, and zero fallback all remain
mandatory. A passing receipt may claim actual Hangul and save/reopen, but it does not claim a
visual oracle or render verification.

V2 plans and evidence do not migrate or relabel. V3 changes the request, evidence, receipt and
harness identities, and a PASS requires a fresh hash-pinned v3 run. Predecessor attempts and their
failure/discovery artifacts remain preserved. Adding or removing screenshot fields from a v2
document cannot produce valid v3 evidence.
