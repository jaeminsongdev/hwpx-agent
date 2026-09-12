# P07-09 equation editor smoke policy

## Decision

P07-09 is `target_pass_v3 / p07_in_progress` for the exact current Hangul 2020 target. V3 keeps
the semantic edit and saved native serialization as independent boundaries, replaces unverified
photo collection with a plan-bound `user_attested` checklist, and preserves all automatic native
save/reopen and structural readback Gates. P07-09 is closed; P07 remains in progress because its
layout/corpus/render/differential Gates are separate.

## Planned edit boundary

The request binds the complete immutable input artifact, package graph, document flow, anchor,
native object ID/count, semantic SHA and script SHA plus exact harness and oracle identities. Both
request admission and private-plan loading compare the complete observed source state.

Before and after `MathAst` values must each compile and reparse without semantic drift. Their
canonical compiler scripts must have equal token cardinality and exactly one differing
fingerprint. The exact saved raw native script is bound separately and must parse to the planned
after semantic state; it need not equal the compiler-canonical spelling. No-op, formatting-only
substitution, insertion/deletion, saved-script semantic mismatch and multi-token edits fail closed.
The plan binds canonical before/after and saved-after digests plus the changed index and old/new
token digests without exposing them in Debug.

The private plan loader checks its trusted file SHA and then recomputes source-state, both
canonical compiler programs, saved-script parsing, semantic/raw-script digests, canonical token
difference and plan SHA. V1/V2 plans do not migrate or relabel. A JSON plan cannot promote itself
by editing a receipt field.

## Combined target evidence

A passing evidence document requires both sides:

- Manual: the user attests the planned before equation, double-click, native editor visibility,
  planned one-token change, editor close/commit, planned post-commit equation, Save As, and user
  ownership of all clicks/typing. Every item is `user_attested`; no UI item is called verified.
  Any reported anomaly or Computer Use click/typing fails. Photos are not required and do not form
  a visual oracle.
- Automated: exact target preflight, immutable input, initial/saved/reopened native readback,
  save, close and reopen must all be `passed`, with distinct trace and oracle-receipt digests.

Before evidence must equal the plan source. Saved and reopened snapshots must keep the same native
object ID/count, carry the planned new semantic hash and exact saved-native script hash, change
artifact/graph/flow from the input, and match each other exactly. Silent, text and image fallback
and object replacement counts must all be zero. Failed-before-effect and effect-unknown never pass.

## Target harness boundary

The harness accepts only a hash-pinned private plan and fixed `before.hwpx`/`after.hwpx` files below
the ignored P07 private-evidence boundary. It rejects reparse-point traversal, preexisting HWP
processes, wrong Registry32 COM identity/build/executable, changed scripts, missing checklist
items and reported anomalies. It starts x86 STA Hangul visibly, but never clicks or types. On
timeout before a stable manual save, it leaves the visible process for the user instead of
force-closing possible unsaved work.

After the user supplies the exact checklist and save, the interactive child confirms a stable
output, immutable input and actual HWP process exit. If Hangul 2020 invalidates the interactive
COM reference during UI Save As, a source-pinned finalizer binds that failed trace and performs two
fresh x86 STA open/close cycles. Hash checks occur only before open and after close because Hangul
holds an exclusive file lock while open. The hash-pinned Rust oracle then checks the strict native
HWPX reader, ID index and complete package-state/equation-flow hashes, and a separate Rust evidence
oracle reloads the plan and verifies the combined evidence.

## Privacy and non-claims

Raw plans, scripts, predecessor traces and target outputs remain under ignored private evidence.
Public receipts carry only hashes, counts and states. Debug redacts revisions, object IDs, all
script states, semantics, artifacts and evidence digests. Existing private photos remain preserved
but are neither required nor used by v3.

Attempts 06 through 13 and the failed child/finalizer traces in 14 remain failure/discovery facts.
They are not rewritten or promoted. Attempt 14's separately hash-bound v4 finalizer passed two
fresh reopen/close cycles, while the Rust target and evidence oracles proved the requested `x+2`
semantics, preserved native object identity, changed package graph/document flow and zero fallback.
This closes only the exact-current-target editor-smoke and save/reopen Gate. Visual oracle, render,
P07 differential, P07 completion, other-version, production and product claims remain absent.

Reasoning level: `max`. The combined target campaign also remains `max` because manual UI,
immutable artifacts, structural readback, render and differential evidence must agree.
