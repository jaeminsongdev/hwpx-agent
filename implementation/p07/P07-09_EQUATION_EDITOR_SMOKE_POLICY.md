# P07-09 equation editor smoke policy

## Decision

P07-09 is `implementation_ready_v2 / target_incomplete`. Licensed-target attempts demonstrated
that the native editor may retain the stored compiler spelling when first opened and canonicalize
it while the operator edits. V2 therefore models planned semantic token change and saved native
serialization as independent boundaries. Predecessor attempts remain failed or discovery
evidence, so P07-09 and P07 remain in progress until a fresh complete v2 run passes.

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
difference and plan SHA. V1 plans do not migrate or relabel. A JSON plan cannot promote itself by
editing a receipt field.

## Combined target evidence

A passing evidence document requires both sides:

- Manual: the user double-clicked the only native equation, observed the equation editor, committed
  the planned one-token change, closed the editor and performed all clicks/typing. Four distinct
  screenshot digests and the complete operator-attestation digest are mandatory. Computer Use is
  screenshot-only; any Computer Use click or typing flag fails.
- Automated: exact target preflight, immutable input, initial/saved/reopened native readback,
  save, close and reopen must all be `passed`, with distinct trace and oracle-receipt digests.

Before evidence must equal the plan source. Saved and reopened snapshots must keep the same native
object ID/count, carry the planned new semantic hash and exact saved-native script hash, change
artifact/graph/flow from the input, and match each other exactly. Silent, text and image fallback
and object replacement counts must all be zero. Failed-before-effect and effect-unknown never pass.

## Target harness boundary

The harness accepts only a hash-pinned private plan and fixed `before.hwpx`/`after.hwpx` files below
the ignored P07 private-evidence boundary. It rejects reparse-point traversal, preexisting HWP
processes, wrong Registry32 COM identity/build/executable, changed scripts and reused screenshots.
It starts x86 STA Hangul visibly, but never clicks or types. On timeout before a stable manual save,
it leaves the visible process for the user instead of force-closing possible unsaved work.

After the user supplies the exact attestation and save, the harness closes/reopens the same saved
file and invokes a hash-pinned Rust oracle. The oracle uses the strict automation-native HWPX reader,
ID index and complete package-state/equation-flow hashes. A separate Rust evidence oracle reloads
the plan and verifies the final evidence.

## Privacy and non-claims

Raw plans, scripts, screenshots and target outputs remain under ignored private evidence. Public
receipts carry only hashes, counts and states. Debug redacts revisions, object IDs, all script
states, semantics, artifacts and evidence digests.

Attempts 06 through 09 prove failure/discovery facts only. Attempt 06 overwrote its disposable
input; 07 preserved input and exposed saved native canonicalization; 08 showed the editor-open raw
spelling is not deterministic; 09 used the corrected plan and produced a conforming saved HWPX but
captured none of the four mandatory screenshots, so automated close/reopen was not admitted.
User permission does not replace missing evidence. A fresh v2 target receipt, render, P07
differential, P07 completion, other-version, production and product claims remain absent until
their respective Gates complete.

Reasoning level: `max`. The combined target campaign also remains `max` because manual UI,
immutable artifacts, structural readback, render and differential evidence must agree.
