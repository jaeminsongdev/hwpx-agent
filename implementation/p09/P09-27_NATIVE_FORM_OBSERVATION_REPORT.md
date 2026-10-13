# P09-27 observed-native form successor component report

Updated: 2026-10-02. State: `observed_native_identity_component_non_green`.

Current successor: P09-28 now connects this unchanged production module to
the public library through a preserved exact source/export successor. The old
pending-export qualifier correctly rejects the new live lib, while its original
capsule and exact old sources remain preserved. The following report describes
the historical P09-27 component checkpoint, not a renewed live pending-export
receipt. See `P09-28_NATIVE_FORM_PUBLIC_EXPORT_REPORT.md`; package/native/routing
and P09 Gate remain unqualified.

## Outcome

A separate production reader/builder/lowerer now reads the actual P08-20 saved
form lacking all native IDs and applies existing typed property/tab-order plans
without adding an invented ID to XML. It closes the reproduced missing-ID and
unchecked physical-anchor/geometry gaps at the section/component level. The
exact shared library exports and original P09-12 domain/HWPX implementation
remain untouched. This successor is compiled and executed by the pending-export
integration harness; it is not yet a public library/product route or a new
Hangul target qualification. No P09 Gate or product completion is claimed.

The real source capture remains 14,556 bytes with package SHA
`02e9b5acef95877b6934a6a3131069402138cc2190eff2e68db79aa7e9ac9ce7`
and section SHA
`89a263eff5d4536cc14223e48847a42e65c7e4f97d5b0c12b5cf73dc4bbba2ff`.
It contains two physical paragraphs, and the edit control is in paragraph
ordinal 1, run ordinal 0, inline ordinal 1. The first test draft supplied only
one paragraph and correctly failed incomplete-map admission; the corrected
complete-map test uses both real paragraphs, not a weakened map check.
Neither original bytes nor historical P08/P09 receipts were altered.

## Implementation

- `crates/hwpx-package/src/native_form_hwpx.rs`: explicit observed optional-ID
  identity enum, complete logical paragraph/component-reservation map, physical
  ancestry/direct-child path and run/inline anchor, independent native common/
  character/payload observations for edit/check/radio/combo/list, actual protect
  flag, length-framed geometry and opaque attributes/children/inter-child gaps.
- No native-ID injection or identity-normalized XML admission. Native missing
  identity stays `Missing`; observed optional `id`, `instid` or `instId` stays
  exact. Duplicate/ambiguous/native namespaced identities and incomplete or
  duplicate logical maps fail. Domain `native_object_id` is explicitly only a
  component reservation in this bridge, not an observed saved native ID.
- The reader independently derives source, raw-control and non-form hashes.
  Full sealed readback comparison prevents source/map/path/identity drift;
  domain-state verification rejects caller-forged anchors, geometry/opaque and
  non-form hashes instead of trusting refreshed values.
- Builder/lowerer use the real existing `FormControlBuilder` and immutable domain
  plan for common/character properties and complete tab order. Plans bind the
  complete source observation, logical map, actual domain plan and profile.
  Lowering edits only admitted attribute values (or missing groupName insertion),
  rereads all controls, checks actual target domain projection and proves every
  outside-edit byte unchanged. Native identity, payload, geometry, opaque command
  and non-selected controls are preserved. Protected controls and unsupported
  insertion/date/payload/command transitions reject before output.
- Unknown opaque character contents and inter-child comments are independently
  bound, not accidentally omitted from preservation fingerprints. Opaque commands
  are hashed/preserved, never interpreted or executed. Debug/error output redacts
  values, maps and private identities.
- Native XML does not establish caller default/validation policy. Other package
  part style/border/resource/reference/protection bindings remain explicit caller
  inputs and are not falsely claimed as independently read by this section-only
  component. Complete package/target/route validation remains necessary.

## Tests and source capsule

`crates/hwpx-package/tests/native_form_hwpx_pending_export.rs` compiles the exact
successor production file through the unchanged public preserving-XML types.
It does not duplicate a mock implementation or change shared exports merely to
make a test pass. 18/18 tests PASS, no skips/ignored new cases:

- Actual hash-pinned missing-ID capture, unchanged source reread, real typed
  property lowering and independent geometry/payload/opaque/identity preservation.
- Forged anchor/shape/opaque/non-form state rejection; full five-kind property
  and tab-order transformations, unaffected-control equality, optional native-ID
  variants, duplicates/aliases, map errors, stale source/payload/geometry/flow.
- Missing groupName insertion, unknown opaque attributes/children/commands,
  wrong namespace/rich text/duplicate geometry, physical protection, unsupported
  payload/command transition, debug redaction, finite limits/output growth,
  opaque character/gap bindings and real nested paragraph paths.

`tools/p09/qualify_native_form_observation_component.py` independently binds the
original capture, predecessor/source-export authority, unchanged shared lib and
new raw sources; executes the exact locked/offline test target; requires all 18
named tests actually pass with zero failures/skips; rereads sources after execution.
Six new Python tests reject forged/missing/failed/ignored/extra test outputs,
source drift, corpus absence, private-text exposure and false product claims.

The exclusive public capsule is
`implementation/p09/evidence/p09-27-native-form-observation-component.current-2020.v1.json`,
SHA `bf23f8ba6c30f7578284274111f5060070a5edf3b413a8ad557d3ae422cb8c82`.
Independent `--verify` reproduces exact bytes. Shared exports, complete target
packages, new native execution, production routing, render/differential, green
rows and P09/product completion remain false/NOT_RUN. This is an implementation
checkpoint, not substitution of component success for the full goal.

## Verification and preserved authority

- Locked/offline Rust workspace, all targets/features: 1,783 PASS across 270
  test targets/suites; three existing explicitly ignored native/external tests
  remain ignored and are not qualified by this command.
- Full P09 Python suite: 199/199 PASS, no skips.
- Workspace Clippy, all targets/features, locked/offline, `-D warnings`: PASS.
- `cargo fmt --all -- --check` and `git diff --check`: PASS.
- Original P09-12 validator genuinely passes all four raw implementation and
  four source locks; its actual/native/render/differential claims remain NOT_RUN.
- P09-23 export/source v2, P09-25 original compatibility failure and P09-26 note
  failure receipts reproduce their unchanged hashes. The body-numbering/raw
  namespace-binding gaps and CLICK_HERE formatting mismatch remain visible.
- Shared lib remains SHA
  `1eae8f6896cb5bb70762ac41e00d0fa017af794cb6dfaec8463879eb1f366d09`.
  No new native/COM session, UI permission request or input, trust/registry/system
  change, network, original edit, deletion/move, staging, commit or push occurred.
  Read-only process check finds zero Hwp processes.

## Required next product work

Preserve this pending-export capsule and raw shared-lib predecessor before an
explicit new source/export successor. Connect the new public types only under
that qualification, retain prior live-verifier failures honestly, then generate
complete production-path property/tab-order cases from actual native source with
real package-part bindings. Build the independent target oracle and gather all
dependency-ready native cases into one preflighted batch, as the user requires.

Finish note body-numbering/native binding, field formatting and the other P09
families; require actual lifecycle/readback/render, routing/fallback, differential
and combined-document evidence before authoritative P09 Gate. Do not start P10
new implementation or mark P09/P09-P20 complete from this component checkpoint.
