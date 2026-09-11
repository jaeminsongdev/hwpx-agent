# P07-06 equation automation policy

## Decision

P07-06 is admitted as exact-current-PC `pass / oracle_verified`. The typed component binds native
insert, edit and readback to a complete source state and opaque binding-set digest. A separate
source-derived disposable probe passed all three operations, save/reopen and strict native HWPX
semantic readback on licensed Hangul 2020 `11.0.0.9136` x86 ko-KR.

Other Hangul versions require independent qualification. This is not P10 production execution and
does not silently promote the frozen P02 binding registry.

## Typed boundary

- Each request binds schema/profile, revision, complete package-graph SHA, document-flow SHA,
  insertion-anchor fingerprint and the opaque installed binding-set SHA.
- Insert requires no selected equation. Edit/readback require the exact selected object ID and
  expected semantic SHA. Admission and plan build both compare the full observed source state.
- Insert/edit own a normalized `MathAst`. It is compiled through the bounded EqEdit engine and
  reparsed for semantic equality before a plan is returned. Readback is nonmutating.
- Insert, edit and readback use distinct capability IDs. Plans never expose raw action,
  ParameterSet or item identifiers.

## Receipts and mutation semantics

Receipts bind plan, binding-set and source-state SHA values plus native object identity, semantic
SHA, resulting package graph, document flow and native-object count. Failed-before-effect and
effect-unknown are failures. Insert/edit must change graph and flow; readback must preserve both.
Edit/readback must return the selected object and every successful receipt must return the expected
semantic state.

## Source-derived target probe

The private builder pins the exact P02 automation-record file, selects three action rows and eight
typed parameter rows by opaque record identity, checks source lock, source kind, ParameterSet
coherence, locator and declared type, then hashes the complete private binding set. Raw values and
scripts are written only below the ignored P07 private-evidence boundary. The public receipt carries
only identities, hashes, counts and privacy flags.

The x86 STA target harness rechecks Registry32 COM identity, exact build/executable SHA, request and
harness SHA values. It uses a finite runtime ParameterSet alias policy, records the resolution
strategy, forbids fallback after a possible effect, bounds execution to 180 seconds and cleans only
the target process it started. It opens no user document and changes no registry or system setting.

## Exact target evidence and normalization

Attempt 03 passed COM creation/version, blank-document creation, insert default/execute, exact
source-derived reverse control selection, nonexecuting edit-default script readback, first save,
edit default/execute, second exact readback, second save, close/reopen and quit. Both immutable saved
files pass the automation-native product reader. Their semantic/script SHAs are exact and distinct;
the native object ID remains stable through the edit.

The reader uses a separate strict automation-current-2020 profile for the exact normalization seen
in these files: paragraph-relative positioning, zero vertical and 56-unit horizontal margins,
renderer-authored shape comment and a blank-document metadata run. The direct-lowerer profile stays
strict and distinct. The initial oracle failure remains diagnostic evidence; the same immutable
files were reused after correcting the profile.

Attempts 01 and 02 remain failed evidence. No failed or partial artifact was promoted.

## Limits, privacy and non-claims

JSON rejects malformed, duplicate, unknown and oversized input. Revision, request, AST, EqEdit and
serialized outputs have finite ceilings. Debug output redacts revisions, object IDs, scripts,
digests and semantic state. Public P07-06 artifacts contain no private paths or raw automation
identifiers.

P07-07 layout estimator/visual evidence, P07-09 editor double-click smoke, direct/automation
differential, P10-05 security registration, P10-06 production execution, other versions, P07
completion, production readiness and product completion remain `false` / `not_run`.

Reasoning level: `max`. P07-07 remains `max` because its baseline/ink-box visual Gate is target
render dependent.
