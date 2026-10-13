# P09-29 complete native-form package binding report

Updated: 2026-10-02. State: `complete_package_binding_component_non_green`.

## Outcome and exact boundary

The production package reader/binder now independently derives real package
style/border/resource/reference/protection/opaque fingerprints and reconstructs
the complete multi-section typed form state. The old constant external metadata
hashes are not reused. Complete source/map/state/flow and domain-plan binding
rejects caller-forged metadata instead of accepting refreshed hashes.

Source: `crates/hwpx-package/src/native_form_package.rs`, compiled through
`tests/native_form_package_pending_export.rs` using unchanged current public
library dependencies. No mock production implementation is substituted. Current
P09-28 public lib and P09-27 form component remain byte exact; this new package
component itself is not exported yet. Package lowering/output, complete native
cases, routes, render/comparator and P09/product Gate remain unimplemented or
NOT_RUN. This advances package implementation, not a narrower completion goal.

The append-only source capsule is
`evidence/p09-29-native-form-package-binding.current-2020.v1.json`, SHA
`82a4112980c36bb901870d88d28810913bdbe64e7b3002f8b117b090bfcb9367`.
Publication and independent `--verify` reproduce exact bytes after final tests.
It binds 15 raw source/policy/test files and the exact preserved P09-28/r02
source predecessor, SHA
`cc9318ba2f75d16dad15f59ee5a6d704fcca14e6e772b4740d5b6d94a14026bc`.

## Actual independent source observation

The original P08-20 saved form capture remains unchanged: 14,556 bytes, SHA
`02e9b5acef95877b6934a6a3131069402138cc2190eff2e68db79aa7e9ac9ce7`.
Its 11 integrity-read package entries contain one actual form without native
IDs, in two physical paragraphs. The real OPF spine has the header as a
non-linear item followed by the paragraph section. Header is fully read and
bound as metadata, not miscounted as another form section. Every other spine
document needs its complete ordered section map; form-free sections also bind
all paragraphs, source bytes and document flow, without inventing a fake form.

`qualify_native_form_package_binding.py` independently reads the exact capture,
validates the finite entry inventory and fresh package SHA before decompression,
recomputes all seven exposed binding/flow fingerprints from actual XML/bytes,
then compares them with the compiled Rust probe. Only hashes/counts/fixed status
codes are public; no original field text, private path or policy values appear.
The lexical reference oracle is explicitly for this exact original capture,
not a general native target/comparator qualification.

## Implemented invariants

- Bounded ZIP integrity/CRC and closed `PackageGraph`, every actual part, complete
  ordered body spine, finite archive/entry/expanded/section bounds, no extraction.
- Complete globally unique logical paragraph/control maps and component
  reservations. All observed native form IDs/instances are checked globally;
  missing IDs remain missing. Root/character/payload/geometry/opaque observations
  come from the unchanged P09-27 native reader, never expected caller values.
- Actual complete header fingerprint, typed character catalog/reference checks,
  actual raw border catalog fingerprint, all declared resource paths including
  non-BinData assets, non-form reference inventory, bound metadata protection
  signals and conservative exact non-section-part/opaque fingerprints.
- Explicit complete caller default/validation policies are separate from native
  payload observations. Only non-observed policy fields are excluded from the
  native-value comparison; full policies and radio/validation/tab constraints
  are validated once in the complete global domain state. Required radio groups
  can span sections; no incorrect per-section required-group admission is used.
- Every global state field is independently reconstructed and compared. Source
  flow is derived from all non-form section bytes and part ordering, not a
  synthetic component constant. Full typed property/global-tab plans bind to
  this actual source flow; wrong flows, metadata, source or policy fail.
- Both source and planned character references require real catalog IDs.
  Nonzero native form border type semantics are unqualified: the inspected
  official model only establishes UINT storage, not a borderFill relationship.
  Do not silently equate those IDs. This profile refuses nonzero values pending
  evidence, retains their full product requirement and never claims all border
  types supported. Zero is the actual observed value, not an inferred general
  no-border/unlocked guarantee.
- Known metadata protection/signature/encryption/rights signals block plan
  binding, including case variants. Fingerprint/marker absence is not general
  document-protection qualification. Commands are preserved/hash-bound, never
  executed; no permission/trust setting is altered.

## Preserved legacy failures and implementation repairs

The original shape ID-index profile actually rejects the native capture with
`id_index_validation_failed`: exactly two unknown ID-like attributes,
`edit@borderTypeIDRef` and `formCharPr@charPrIDRef`. This caused the first package
prototype's ten dependent tests to fail. The new closed native-form overlay
accepts only exact reported unknown locations on fully observed native roots/
direct character children, whose identities/character references were separately
validated. Every other issue/code/namespace/location remains fatal. The real old
failure and overlay count two remain in the source capsule and a regression
test; the legacy index is never reported PASS or generically skipped.

The initial body-spine assumption also failed because the actual native OPF
includes the non-linear header. The corrected reader partitions the exact
validated header, not an arbitrary excluded file list. The new empty-form test
initially failed because the original section component requires a control;
the package layer now independently validates/binds genuinely form-free sections
without changing that frozen component or creating dummy IDs/controls. Initial
strict Clippy findings were corrected with split reader helpers, proper bounds/
extension handling and efficient formatting; no new lint allowances were added.
These development failures remain recorded here and in the session, not relabeled
as native/Gate success; no original or failed native receipt was deleted.

## Final tests and preservation

17/17 new Rust tests PASS, zero ignored/skipped:

- Exact actual capture and independently checked binding probe; original legacy
  failure and non-linear header; full state/real property plan binding.
- Seven forged metadata/non-form hashes; source metadata/preview drift; invalid
  form character/border references; forged/incomplete policy and wrong source flow.
- Derived complete two-section/global-tab case, required radio group spanning
  both sections, missing/reordered/extra/duplicate maps and native IDs.
- Empty-form section, extra unknown/dangling non-form refs, planned invalid
  references, both BinData and non-BinData binary resource drift.
- Observed protection rejection, finite bounds and debug/error redaction.

Derived radio/multi-section/resource packages are memory-only test fixtures,
not real native outputs. There is no package output-generation or save/reopen
claim hidden in these tests.

Six new Python tests PASS; full P09 Python 212/212 PASS. Workspace Rust all
targets/features, locked/offline: 1,818 PASS across 272 suites, zero failures,
three existing ignored native/external cases retained. Workspace strict Clippy,
format and diff whitespace checks PASS. P09-28/r02 reproduces unchanged; P09-25
compatibility-failure and P09-26 note-failure receipts also reproduce unchanged.
P09's authoritative counts remain 46 owned + 7 deferred, 35 unit/11 static
integration, zero oracle/green; none are promoted by this component checkpoint.

No new native/COM/UI session, access-permission action, registry/trust/network
change, original edit, deletion/move, staging, commit or push. Read-only Hwp
process check is zero. All P08/P09/P17 user-owned and private evidence survives.

## Next real product work

Current public-source successor is P09-31/v4, SHA
`22af68bce9aace86095c384f3c6d616145e3bce6a4b46ab0eca10c829e85b503`.
It exports this unchanged reader/binder and the unchanged P09-30 lowerer. Exact
old lib/test raw files are archived; original source capsule remains unchanged
and its obsolete full current verifier correctly fails. See
`P09-31_NATIVE_FORM_PACKAGE_PUBLIC_EXPORT_REPORT.md`; complete native cases and
saved/reopened oracle/routes remain next. This updates the pointer, not history.

Successor checkpoint: P09-30 implements actual complete global property/tab
package output, preservation and external output verification using this
unchanged production binder. Its separate source capsule is SHA
`ff7aeade25379f5b53f8f4e76da2fc08c902d4002897f6f11077572cf94bb099`;
see `P09-30_NATIVE_FORM_PACKAGE_OUTPUT_REPORT.md`. The initial P09-29 counts
and boundary below remain historical; this capsule and all 15 raw sources are
unchanged and actually reproduced by P09-30. Public exports/native cases/oracle
and routes remain the next dependencies, not claimed complete.

Preserve this source capsule. Implement actual complete package lowering and
output verification for full global property/tab operations without losing
cross-section/radio constraints, then connect through an explicit source/export
successor. Prepare complete disposable actual-source cases and the independent
saved/reopened package oracle, including unresolved border/protection and other
P09 families as their prerequisites become ready. Gather all ready cases into
one preflighted native batch; only the user handles sequential permission dialogs.
Do not run invalid/unchanged cases solely to enlarge the queue.

Note body-numbering/raw binding, CLICK_HERE style, caption visuals, remaining
form/field/comment/link families and mixed-document/differential/route acceptance
remain required. The full P09-P20 objective stays active; no P10 new implementation
before an authoritative P09 Gate.
