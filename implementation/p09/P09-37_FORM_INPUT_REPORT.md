# P09-37 atomic form input and default restoration

2026-10-03, current worktree, offline only. User's no-native/access-dialog hold
remains in force; active P09-P20 goal is not paused or complete. No new P10.

## Implemented result

`crates/domain-ir/src/form_input.rs` implements a separate actual production
module for value-only atomic input and default restoration. It supports text,
checkbox, radio, combo, list and semantic date values. It is compiled through
two explicit pending-export integration targets, not yet a shared public export,
HWPX output, native candidate or production route. Frozen form-control/v1 and
domain/hwpx shared library bytes are unchanged; old APIs/results are preserved.

`SetValues` updates only requested current values/selections. `ResetDefaults`
updates current values from existing caller-declared defaults, never changes
the defaults themselves or validation. A complete radio selection switch is
one atomic transition over the full inventory, independent of assignment order:
partial required-group updates fail and no invalid intermediate/partial state
is returned. Defaults/validation/items/captions/flags/common state, anchors,
native identities/bindings, shape/unknown data, catalogs, resource/reference/
protection/opaque hashes and document flow remain exact. Semantic dates retain
UnverifiedDateControl; no native date implementation is inferred.

All requested targets enforce shape lock, enabled/editable and text read_only.
Explicit caller access must bind the complete source protection digest. Build
requires a fresh matching caller access policy; revocation rejects even when
the source state has not changed. This is caller policy only, not a native
security/permission observation. Actual unchanged domain validators enforce
text/length/numeric/multiline, checkbox/tri-state, required radio/selection,
item membership and Gregorian dates/ranges. Referenced external validators
reject ExternalValidationUnqualified; no digest is counted as execution.

Requests are bounded, strict JSON with recursive duplicate-key rejection,
unknown/coerced/trailing content rejection and identical typed-caller bounds.
Private plans have no deserializer, seal all source/target/flow/request/access/
operation/count fields, and build independently replays the entire plan.
New bounded JSON writer checks growth before allocation; no silent clamping.
Debug/errors are redacted and public receipts contain only hashes/counts and
one explicit caller-only/native-protection/external-validation/output-
unqualified qualification enum. No manufactured combinations of success flags.

## Actual capture binding and remaining output gap

The unchanged real P08-20 complete capture (14,556 bytes, raw SHA
`02e9b5acef95877b6934a6a3131069402138cc2190eff2e68db79aa7e9ac9ce7`)
is read through the actual stable public complete-package reader and explicit
full policies. The new input plan changes one current value while independently
asserting every other complete typed field exact and observed native identity
still Missing. Capture identity is rechecked after the test. Independent Python
rederives the complete package bindings and flow, not a mock reader result.

Compiled probe fingerprints:

- Source state: `7841acc0e27ca1a96ace5c21375f46e3a3936ac9efa3a03efc9aecb699a708e1`.
- Target state: `e201df8bf80c6df99ce98e30fb8b89900d74c3ead494e3f4432d2efe2be57026`.
- Flow: `1c1df01dadb3475fe7f1d6ca0c5692770f54a1d403dd8eedcbc39d9634f4a22b`.
- Input plan: `c8abe430e6bc9d55e8e4606958ce8638a97cb3a6368910e0fcadaa00b7660651`.

Actual legacy complete HWPX lowerer invocation still returns NonRepresentable
for the value change. That rejection is asserted and preserved, not bypassed.
Code inspection also shows the v1 opaque control fingerprint includes hp:text
bytes and payload attributes, so changing native input without a properly
versioned value-aware opaque profile would invalidate full-state preservation.
No original fingerprint/plan is silently rebound and no native ID is injected.
The typed target above is NOT saved/reopened/native HWPX output evidence.

## Qualification and regression

- Exact production module compiled domain suite: 17 PASS, zero ignored/failed.
- Actual-capture/public-reader integration suite: 3 PASS, zero ignored/failed
  (includes the same two private invariant cases in the second compile target).
- Independent source/probe/inventory/privacy qualifier Python: 6 PASS.
- Full Rust workspace all targets/features, locked/offline: 1,928 PASS,
  three existing ignored, 281 suites, zero failures; actual command result.
- Full P09 Python: 312 PASS, zero skips/errors/failures.
- Full strict workspace Clippy `-D warnings`, fmt and whitespace: PASS.
- Original P09-02 validator genuinely PASS, original three domain source pins
  unchanged; date/native/HWPX/render/automation/differential flags remain open.
- P09-34/r02, P09-35 and P09-36 raw capsules/sources and 22 historical native
  trace/artifact hashes are checked unchanged before/after qualification.

Preserved initial findings: first integration fixtures rejected 13/15 cases
because their opaque namespace used a colon-containing token invalid under
the unchanged v1 domain contract. Fixtures were corrected to the existing hp
token and made internally valid before the negative mutations; validators were
not relaxed. Initial strict Clippy identified excessive receipt booleans,
semicolon/hex formatting and an oversized integration function; these were
refactored without lint suppression. First Python privacy run had one false
positive because the word before occurs in a public test name; the check now
forbids the quoted plaintext fixture value and redacts failure diagnostics.
All corrected tests and full regressions pass; no initial failure is called PASS.

Component capsule:
`implementation/p09/evidence/p09-37-atomic-form-input-component.current-2020.v1.json`,
7,177 bytes, raw SHA
`3075b4bc0c12e383a48d1c3dc0c6fb548612ac6054ab6afda3a3ec20383c21a0`.
Exclusive publication and fresh full --verify reproduce every byte exactly.
Six new production/test/policy/verifier sources are frozen by this receipt;
reports/PLANS remain mutable pointers. Source changes require a qualified
successor, never refreshing the original locks or overwriting failed evidence.

## Next boundary

Continue offline work: explicitly qualify a public domain input API successor
while preserving the original complete-domain library and validators, then
implement complete native value output with independently derived value-aware
opaque/source/target bindings and all original package-preservation oracles.
Default/validation native persistence and external execution, date native shape,
protection, insertion/all types, routing, field/note semantics, render and full
product differential remain required. This input stage does not replace them.

The prepared15-case native diagnostic matrix / 30 stages remains NOT_RUN.
Typed-only/unimplemented input cases are NOT appended to a permission batch.
No new Hancom/COM/UI, native session/dialog, security/trust/registry/network,
staging/commit/push, original rewrite/deletion/move or unrelated user changes.
All prior native failures and zero green remain. After explicit user resume,
dispatch only the entire genuinely changed dependency-ready matrix in one
sequential batch; the human alone handles permissions. P09 Gate remains open.
