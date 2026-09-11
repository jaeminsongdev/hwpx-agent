# P07-09 equation editor smoke policy

## Decision

P07-09 is `implementation_ready / target_not_run`. The exact one-token edit planner, private-plan
loader, combined manual/automation evidence verifier, native HWPX oracle and bounded interactive
target harness are implemented. No editor session has been run for this card, so P07-09 and P07
remain in progress.

## Planned edit boundary

The request binds the complete immutable input artifact, package graph, document flow, anchor,
native object ID/count, semantic SHA and script SHA plus exact harness and oracle identities. Both
request admission and private-plan loading compare the complete observed source state.

Before and after `MathAst` values must each compile and reparse without semantic drift. The
canonical EqEdit token sequence must have equal cardinality and exactly one differing token
fingerprint. No-op, whitespace-only, insertion/deletion and multi-token edits fail closed. The plan
binds the changed index and old/new token digests without exposing them in Debug output.

The private plan loader checks its trusted file SHA and then recomputes source-state, canonical
scripts, semantic/script digests, token difference and plan SHA. A JSON plan cannot promote itself
by editing a receipt field.

## Combined target evidence

A passing evidence document requires both sides:

- Manual: the user double-clicked the only native equation, observed the equation editor, committed
  the planned one-token change, closed the editor and performed all clicks/typing. Four distinct
  screenshot digests and the complete operator-attestation digest are mandatory. Computer Use is
  screenshot-only; any Computer Use click or typing flag fails.
- Automated: exact target preflight, immutable input, initial/saved/reopened native readback,
  save, close and reopen must all be `passed`, with distinct trace and oracle-receipt digests.

Before evidence must equal the plan source. Saved and reopened snapshots must keep the same native
object ID/count, carry the planned new semantic/script hashes, change artifact/graph/flow from the
input, and match each other exactly. Silent, text and image fallback and object replacement counts
must all be zero. Failed-before-effect and effect-unknown never pass.

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
receipts carry only hashes, counts and states. Debug redacts revisions, object IDs, scripts,
semantics, artifacts and evidence digests.

No P07-09 editor run, target receipt, save/reopen PASS, render, P07 differential, P07 completion,
other Hangul version, production or product completion is claimed. These remain `false` /
`not_run` until the combined P06/P07 target campaign.

Reasoning level: `max`. The combined target campaign also remains `max` because manual UI,
immutable artifacts, structural readback, render and differential evidence must agree.
