# P09-38 actual public atomic form input API

Date: 2026-10-03. Offline source qualification only; P09 Gate remains open.
The user is asleep. No Hancom/COM/UI session or access-allow dialog was started.

## Implemented change and preservation

- Add only `pub mod form_input;` to `crates/domain-ir/src/lib.rs`, exposing the
  unchanged production implementation at `domain_ir::form_input`.
- Entire pre-export library is preserved at
  `source-archive/p09-38-pre-form-input-export/domain-ir-lib.rs` within this
  directory. Original SHA256 is
  `b4726732a47175205a7e35f3aa8e018e66b2a0fbada144bebeac3f395540c058`;
  current SHA256 is
  `6f44e4baca13f0665abc6c2599bc4ab0ff559af11b02f37d7747a9334c5ccb85`.
  Removing the unique declared export recovers the full original bytes.
- Add actual public domain and actual-capture integration targets. All scenario
  bodies are byte-exact copies of their frozen predecessors; only the import
  headers change. No public target source-includes the implementation.
- No changes to original form-control or form-input bodies, pending-export
  tests, dependency manifests, legacy validators/tests, previous capsules,
  native harness, fixtures or private evidence. No staging/commit/push.

## Actual current verification

- Production `cargo check -p domain-ir --lib --locked --offline`: PASS.
- Public domain15 + public actual-capture1 + actual library private2:18 PASS.
  Library-private filtering explicitly excludes unrelated unit tests only.
- New Python public-export qualification:8 PASS. Original archive/delta,
  public header/body/source-inclusion, probe substitution, duplicate/conflicting
  CLI results and legacy current-failure preservation are checked.
- Full Rust workspace/all-targets:1,946 PASS,0 failed,3 existing ignored,
  283 suites. All pending-export predecessor Rust targets remain runnable.
- Full workspace/all-targets strict Clippy `-D warnings`, cargo fmt check,
  compileall and git diff check: PASS.
- Source guard rechecks older12 capsules/194 source pins, immediate P09-37
  six sources, P09-34/r02/P09-35/P09-36 sources and22 historical artifacts.
  Full original P09-36 offline preflight is freshly reproduced byte-exact;
  its P09-35 preparation and original native readbacks remain unchanged.
- Actual original capture public reader/value plan reproduces the original
  state/flow/target/plan hashes and all other complete state. Missing native IDs
  stay Missing. Existing complete HWPX lowerer still returns NonRepresentable.
- New append-only capsule publication and fresh full byte-exact reproduction:
  PASS. Path:
  `evidence/p09-38-atomic-form-input-public-export.current-2020.v1.json` within
  this directory;21,080 bytes,7 source pins, SHA256
  `2be9751323aa0d01d9dfcc57a461156df8b80eb201ed2d6e24b6c99fbe9764b0`.
  All35 actual original validator results are included:12 PASS/23 FAIL, without
  lock refresh. Final complete Python rerun executes314 tests with10 failures
  and4 errors (one class-setup error and three individual test errors). All8 new
  public-export tests pass in that rerun. No tests are skipped or rewritten;
  this new source qualification is not current full Python regression PASS.

## Preserved failures; no legacy regression PASS

The additive export legitimately changes the old full-file domain library hash.
All ten original P09 typed-contract validators therefore fail: seven report
`implementation_digest`, while citation/mail-merge/reference-auxiliary report
`digest:crates/domain-ir/src/lib.rs`. Sources and old expectations are unchanged.
Actually invoked predecessor P09-37 authority fails
`public_export_source_identity_changed`, and P09-34/r02 full current verifier
fails `bridge_source_identity_changed`. Neither old capsule is rewritten.

The initial complete Python run executes306 tests and reports10 failures and
5 errors: ten original contract-positive tests, P09-37/new P09-38 class setup,
and three full-current shared-source bridge tests. The new class setup failure
is corrected and all its8 tests now pass; the other old-current failures remain
genuine. Final current rerun executes314 tests in370.927 seconds and reports
10 failures/4 errors: ten contract-positive tests, one P09-37 class-setup error
and three full-current bridge test errors. The corrected new P09-38 class
executes all8 cases successfully. Preserve both runs; never convert failed
old-current tests into archived/current PASS. Legacy negative tests retain their
original code, but their old positive source baseline is now invalid; therefore
their current execution is not a qualified substitute for independently restored
archived-scope negative-case parity. That successor is the next offline boundary.

Initial new verifier failures are retained here: it first parsed a frozen CLI's
JSON result plus trailing public PASS banner as one JSON document; it then
expected one shared domain-digest error code, although three pinned validators
use the path-qualified code. The successor now strictly accepts exactly one
duplicate-free result and at most one known public PASS banner, rejects unknown
or conflicting/duplicate results, and preserves each actual error code. This
corrects the new collector; original validators/locks are not changed.

## Remaining product and next offline boundary

This qualifies the public typed API, not native input/default output, native
protection/date shape, executed external validation, production routing, render
or differential. Zero green rows; no P10 work. The future complete15-case native
diagnostic batch/30 stages remains NOT_RUN, without typed-only fillers.

First create an explicit legacy-regression source successor preserving every
original test/negative case and actually invoked current failure. Do not simply
refresh locks or pretend the current legacy aggregate is green. Then implement
complete native value output with independently qualified value-aware opaque
and source/target bindings. Keep all originals/drift/failures; no silent opaque
hash rebinding. After explicit user resume only, dispatch all genuinely changed,
dependency-ready cases together as one sequential batch. Permissions remain
human-owned; no automatic clicks or trust/security/registry changes.
