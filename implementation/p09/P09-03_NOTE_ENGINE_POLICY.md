# P09-03 note-engine policy

## Current source note file export

`ImportedDocumentStructure::export_note_file_candidate` creates an actual note-only body
HWPX candidate in `structure/note_export.rs`, `note_export/xml.rs` and `note_export/package.rs`.
The additive `hwpx-agent.source-note-file-hwpx/v1` profile accepts Footnotes, Endnotes or Both,
collects source body elements in XML insertion order and retains namespace-expanded names,
original local attributes, opaque subtrees, style definitions and resource bytes. It does not
overwrite source or reinterpret the older domain `DigestManifestV1`/`PrepareExport` as a writer.
The caller must deliberately consume verified HWPX bytes; the source-bound stored-service
candidate below is not an executable route. See `protocol/migrations/p09-note-file-export-profile-v1.md`.

Empty body sections are omitted, related OPF/RDF/ODF records are pruned, and native header
section count is updated. Source section properties are placed in the first output paragraph
without source main text. Standard previews are invalidated, not presented as new renders;
stale caret positions are removed. Other metadata and resources are retained and may contain
source information. This feature is NOT a redaction or metadata-sanitization tool.

The candidate uses the original bounded writer buffer and its existing package graph,
preservation and shape/v6 ID chain for source and output. Output also imports into the
actual document structure, has no remaining native note wrappers in its body, and matches
every expected expanded part hash. Exposing private buffer reuse and adding a crate-private
trust wrapper do not change existing writer behavior. Source drift, empty selections, hidden
note coverage, observed protection, active review/blocked/quarantined content, signed/encrypted
security, finite limits and invalid original IDs fail without an output candidate.

`evidence/p09-361-source-note-export-components026.v1.json` records six passes and two
source-admission fixture failures. `evidence/p09-361-source-note-export-recovery027.v1.json`
recovers only those two, retaining the previous six. The fixes move a namespaced extension
attribute from a strict native paragraph to its opaque element and a lock from attribute-free
ctrl to an admitted subtree. The unused import is the only production text change; complete
test inverse and source/input pins prove all other code and test bodies stayed the same.
The failed receipt is not relabelled.

The eight unique tests include temporary create-new HWPX files and actual disk reopen,
existing-file refusal, each selected family and combined insertion order, prefix shadowing
and default namespaces, opaque data, section/manifest/header updates, exact image resource
preservation, preview/caret invalidation, guards/limits and six exports plus three original
ID rejections across nine historical source packages. Original Native failures remain non-green.
The first run took 138.484 seconds (system CPU peak 67.83%, minimum available RAM 22.2125%,
Job private peak 1552.47 MiB); recovery took 143.422 seconds (442 fresh/final442, CPU peak
57.39%, RAM minimum 15.7814%, Job private peak 1551.87 MiB). Both owned jobs closed empty.
Existing CPU/private/RAM/commit/input protection remains, and no previous API/stored/249 suite
was replayed. Empty recovery diagnostics do not qualify workspace-wide strict lint.

The official help describes collecting selected note families in insertion order, but versions
differ on HWP versus HWPX output. It does not qualify exact Hancom 2020 native equivalence.
Section-property extraction now reads only the run envelope, inherited namespaces and secPr,
not a full parent-run copy. Packaging borrows collected section bytes rather than cloning them
into the metadata-change map, and source body-spine classification wins over metadata filenames.
The whole Form proof is reused only in the same operation; the original writer still validates
source package/shape-v6 ID/preservation and active/security policy before output construction.

`StoredImportedDocumentForms::prepare_note_file_candidate` joins fresh scope/head/ACL/quarantine/AEAD
and complete Form reconstruction to the actual HWPX candidate. Source SHA, selection, request SHA,
selected count and output receipt are bound. Each verify/consumer exposure reauthorizes the source
and checks output integrity; the last head check is inside the verified callback before consumption.
These reads are not atomic CAS. Retained receipts/proofs are not grants. Executable product routes
remain denied, with no output ingest, DB commit, issuer or publication authority.

`evidence/p09-361-stored-note-export-components030.v1.json` records 11 core and 8 stored tests,
all passed with 446 fresh/final446 inputs. New cases cover a large unselected parent run with identical
collected output, direct/proof equivalence and foreign/drift rejection, body/settings filename collision,
actual new file/reopen, all selected families, revoked/regranted ACL, quarantine/AEAD tamper, five foreign
scopes, head races at prepare/verify/final consumer and original guards/limits/ID rejections. The stored
run excludes 268 unrelated tests; it does not replay the source API or official queue. Total elapsed
time was 248.844 seconds; the two Cargo commands took 88.407 and 103.312 seconds, including tests
of 3.37 and 15.37 seconds. No timing speedup benchmark or PC-wide freeze-cause conclusion follows.
CPU peaked at 30.86%, available RAM bottomed at 19.2843%, Job private peaked at 1563.45 MiB/4.9071%.
Both jobs closed empty, diagnostics were empty, and the one-core/BelowNormal/6.25% CPU, 8% cap/7%
private stop and 95% RAM/commit safeguards remained unchanged.

The separate `form_product_request::stored_note_file::StoredNoteFileProductRequest::prepare_json`
now accepts `hwpx-agent.product-note-file-request/v1`. It requires a strict duplicate-free object,
an object operation with closed export/family enums, and at most 16 KiB. It rejects caller paths,
artifact IDs, source graphs, approvals and validator verdicts. Provider context document.write is
required at preparation and each output/verify exposure in addition to the unchanged source ACL.
The request binds project/document/base revision/head generation/source SHA/key/plan/family;
raw, canonical and provider-scoped digests are distinct. Scope includes tenant/subject/project/
branch/document. The source moves into the stored candidate without cloning it, and all existing
whole-source, writer and final-head checks remain. Keys are not claimed and receipts are not grants.
See `protocol/migrations/p09-note-file-product-request-v1.md` for the new API boundary.

`evidence/p09-361-note-file-request-components032.v1.json` records 8 new request and 8 affected
stored tests, all passed, 447 fresh/final447, with 268 unrelated tests excluded. Tests cover source
API JSON to actual temporary file/reopen without caller Form import, all families, raw/canonical/
key/plan/family binding, malformed/duplicate/nonobject input, exact 16 KiB bounds, write scope,
foreign bindings, revoked/regranted ACL, quarantine/AEAD, final-head races and original limits/ID
failures. The core 11, existing source API and official queue were not rerun. One missing Debug
warning for the empty entrypoint type was corrected by a derive only; debug-check033 proves the
full module inverse, unchanged other source/test/input pins (449 fresh/final449), and warning-free
library compilation without repeating tests. The first run took 75.360 seconds (tests 6.41 seconds,
CPU 55.44%, available RAM minimum 21.3877%, Job 899.48 MiB/2.8231%); compile-only took 91.625
seconds (CPU 31.35%, RAM minimum 19.9714%, Job 1483.74 MiB/4.6569%). Both jobs closed empty
under unchanged CPU/private/RAM/commit guards. No PC-wide performance cure or strict lint is claimed.

No CLI/server dispatcher, issuer, idempotency claim, ingest, revision commit, CAS or publication
route was added. The preparation verifies current access and still denies executable routes.
Detached note roots and the section-properties-only run now close xml:lang and xml:space as well
as namespaces. The nearest value wins, local overrides remain lexical source bytes, empty language
resets remain empty, and added attributes count against existing payload/section/output limits.
The source graph mapper uses a private SourceXmlContext profile for p/run language and valid space
attributes; it retains their original attributes/anchors, not a new typed TextFlow lowering promise.
Standalone typed reader/writer and existing SourcePreserving admission stay unchanged. Unknown
namespaced p/run attributes and invalid space values reject. A removed intermediate xml:base
rejects with InheritedContext until URI resolution is qualified; it is not silently discarded.

The pinned official ParaListType header/implementation hashes match the earlier source qualification.
Its native direction/wrap/alignment/dimensions/link/reference properties belong to the container,
not arbitrary paragraph attributes. Their source bytes remain in original anchors/selected-body
fingerprints, but no layout or numbering transfer to ordinary body flow is claimed.
See `protocol/migrations/p09-note-export-xml-context.md` for context rules and evidence.

components035/036 retain test-only private-access compile failures. components037 passes all 52
core/reader/mapper cases (6 new, 46 affected), then product test compilation fails on a new assertion
delimiter. recovery038 proves its full-file assertion-only inverse and unchanged production/core/
other input pins, runs only the two previously unexecuted product tests and passes both, excluding
284 others (459 fresh/final459, cleanup true). Original 52 passes are retained, not rerun; 54 unique
tests cover effective text/secPr context, empty/local overrides, fifty independent notes, inherited
byte limits, strict typed boundaries, base rejection and product output/ACL revocation. Original
failed receipts remain failed. No source API/official queue or Native suite was executed.

The 52-pass run took 252.625 seconds including the product compile failure (system CPU peak 71.13%,
RAM minimum 12.8784%, Job peak 1562.72 MiB/4.9048%). Recovery took 71.844 seconds (tests 0.04 seconds,
CPU peak 78.91%, RAM minimum 14.6709%, Job peak 902.80 MiB/2.8336%). All jobs closed empty under
unchanged safeguards; successful commands had no diagnostics. System CPU is not attributed wholly
to the verifier, and this is not a PC freeze-cause resolution or whole-workspace strict-lint claim.

Next is XML Base URI binding and native subList container semantics. Body-container layout, Native format/numbering/save/reopen/reference update/render,
full protection, issuer/DB/CAS/execution/publication and P09 acceptance remain open.
API v12 remains incomplete/4 unresolved/no report/exit3; official acceptance remains
158/249, 91 left, next case165; P09/A12/A13 are OPEN and P10 has not started.

## Source API note style integration and original verification

The reference-source API is now `hwpx-agent.product.reference-source-assessment/v12`.
`note_style_selections` contains only source style ID, subtree SHA256 and observed NoteKind;
it does not disclose style values, marker/user/prefix/suffix characters, note text or raw XML.
The API reuses existing token documents, validates all observed body-spine style declarations,
and preserves count/text/section/output limits. Absent styles stay absent; malformed or hidden
declarations reject with `REFERENCE_SOURCE_NOTE_STYLES_REJECTED`, not an empty array fallback.
See `protocol/migrations/p09-reference-source-assessment-v11-to-v12.md` for the client contract.

An actual locked historical Hancom package stores native `newNum="0"` in both note styles.
The pinned official [numbering.h](https://raw.githubusercontent.com/hancom-io/hwpx-owpml-model/1453388472c703a4b299a0834f425cdac16644b9/OWPML/Class/Para/numbering.h)
uses UINT for that property. Source observation now preserves this explicit unsigned value
without interpreting its effective meaning or replacing zero with one. Editing may preserve
zero only when the original has zero and its numbering restart mode is unchanged. Creating
new zero or changing that mode with zero rejects. The complete domain NoteStyle retains its
positive-start validation; Native number recalculation remains unqualified.

`evidence/p09-361-source-note-style-api-components023.v1.json` preserves the first 55 passing
API tests and two failures caused by conflating native source zero with a resolved positive
start. `evidence/p09-361-source-note-style-api-recovery024.v1.json` records 23 passing recovery
executions: 12 core tests, eight selected API tests and three stored tests. The 49 unaffected
positive API tests were retained through unchanged API/test/input pins, not replayed or counted
as new executions. Thus the API has 57 unique verified cases across the two preserved results.
The first failed result and historical Native failures remain unchanged.

Coverage includes actual read-only CLI v12/exit3, exact three-field selectors, privacy,
whole-package/document/part binding, XML order, absent/unsupported/malformed source, finite
count/text/section/output bounds, JSON-only selection plus explicit replacement values, stored
output API readback, stale/foreign/tampered selectors and revoked access. Core and stored tests
also preserve an existing zero byte-for-byte outside the explicit edit, deny new/reinterpreted
zero and retain complete-protection/native/execution denial. Existing API code/test text is
unchanged outside the explicit selector/schema/include additions and version expectations.

The recovery matched 435 fresh inputs again at closure. Three owned Cargo jobs ran serially
and closed with active process count zero. Total time was 296.078 seconds; test execution took
1.62, 0.90 and 1.10 seconds. System CPU peaked at 72.66%, available RAM reached a minimum of
14.5620%, and Job private memory peaked at 1555.57 MiB (4.8824%). Existing one-core BelowNormal,
CPU/private-memory/RAM/commit limits remain. The stored command filtered 265 unrelated tests;
this work did not run the official 249 queue, Hancom/COM/UI or Native011.

The API remains incomplete with four unresolved stages, no report and exit3. Next is actual
REF-025 note-file export rather than the old digest-only manifest. Full protection, Native
layout/numbering/save/reopen/reference update/render, DB/issuer/CAS/execution/publication and
P09 acceptance remain open. Official acceptance stays 158/249, 91 left, next case165;
P09/A12/A13 are OPEN, P10 has not started, and the fixed eight CROSSREF captures remain
NOT_RUN pending their authorized session qualification.

## Stored note style service integration and original verification

`StoredImportedDocumentForms::prepare_note_style_candidate` in
`crates/product-cli/src/form_stored_provider/actual_import/note_style_output.rs` connects actual
source style output to the existing authenticated stored-source service. It first performs the
original scope/head/ACL/quarantine/AEAD checks and whole Form reconstruction. The operation-local
`VerifiedFormReconstruction` then supplies the same source check to the shared non-generic
compiler, avoiding a second complete input import. Direct callers still perform their original
whole-source verification. The shared `note_style_request_sha256` preserves the original v1
source/order/ID/fingerprint and 16 length-framed values; a digest is not source or access authority.

Every candidate verification and byte exposure rechecks currently authorized source and output
binding. Preparation, verification and the writer callback each check the final revision head;
the consumer is not called after a failed check. Candidate internals cannot be replaced by a
receipt clone or deserialization. These reads do not hold a lock, implement atomic CAS, ingest
an output, commit a revision or grant issuer/execution/publication authority. Executable routes
remain rejected, and complete protection/native layout/numbering flags remain false.

`evidence/p09-361-stored-note-style-components021.v1.json` records 19 passing executions: eight new
stored-service tests, two new proof/digest tests and nine affected source-compiler regressions.
The stored target excludes 258 unrelated tests; the official 249-case queue is not replayed.
Coverage includes three regenerated packages, preserved note bodies, request order and sealed
receipts, ACL revoke/regrant, quarantine/AEAD tampering, all five foreign scopes, final head races
at prepare/verify/writer boundaries, original selection/value/protection/finite/writer failures,
and six edits plus three original paragraph-ID rejections across nine historical sources. Original
Native failures stay non-green. Direct and whole Form proof outputs match in bytes and receipt;
foreign originals and fresh-byte drift reject. Every one of the 16 values changes the digest.

All 443 inputs were freshly matched again at closure. Both owned Cargo jobs ran serially and
closed with active process count zero. Total elapsed time was 334.125 seconds, with test execution
of 1.29 and 7.82 seconds. System CPU peaked at 70.16%, available RAM reached a minimum of
16.3809%, and Job private memory peaked at 1552.70 MiB (4.8734%). One-core BelowNormal,
Job CPU cap 6.25%, private cap 8%/stop 7%, RAM/commit 95% and original input checks remain active.
Compiler diagnostics were empty for these targets, not a workspace-wide strict-lint qualification.

The original stored-component result predates the v12 API integration above. Actual external
note export, native save/reopen/reference update/render, complete
protection, DB/issuer/CAS/execution/publication and the P09 Gate remain open. The official count
remains 158/249, 91 left, next case165. No Hancom/COM/UI or Native011 runs occur here; the
conditionally authorized fixed eight CROSSREF captures remain NOT_RUN pending session qualification.

## Source note style implementation and original verification

`REF-023` now has actual-source style observation and an in-memory HWPX output candidate in
`crates/hwpx-package/src/document_import/structure/note_style.rs` and `note_style/output.rs`.
`import_note_styles` reuses existing body-spine section token documents; it does not reopen ZIP/XML.
Each admitted section has at most one main-body `secPr`, with at most one style per note family.
An existing style requires all five known children and 16 known attributes. Missing styles stay
absent, while missing properties, hidden/duplicate declarations, unsupported values and incompatible
families reject this profile. Unknown XML remains exact source, not inferred effective semantics.

`NoteStyleValues` contains observed values without a synthetic unlocked state or complete opaque
style authority. `lower_note_style_batch_candidate` binds whole fresh source, source style ID and
subtree fingerprint, validates family-specific values and lowers one package transaction. One output
import reads every admitted style back. Only changed known attribute value spans may differ;
unchanged lexical forms, opaque markup, note bodies and other package parts are preserved.
Each changed part shares ancestor and subtree protection maps instead of rescanning per style.
An observed lock rejects the batch, but absence of a lock never qualifies complete protection.

The source component has nine unique passing tests across two preserved runs. The original
`p09-361-source-note-style-components018.v1.json` records seven passes and two fixture-setup failures:
a missing required paragraph ID and a ZIP with `mimetype` not first. Only those two were rerun in
`p09-361-source-note-style-recovery019.v1.json`, with two passes and the prior seven filtered out.
Production and input pins were unchanged; inverting the two fixture fixes and a test-only unused
helper annotation reproduces the original complete test text. The original failure is not relabelled.

Coverage includes the 22/18/16 closed native catalogs, all 16 attributes, family-specific restart and
placement, two parts with identical local source information, whole-package source binding,
protection/finite limits, exact outside-edit preservation and nine historical generated/saved/reopened
note sources. Historical Native failures remain non-green. These are source component tests, not
the compiled 249-case queue or a Native result. Both owned jobs terminated and were closed;
one-core BelowNormal, Job CPU cap 6.25%, private cap 8%/stop 7%, and RAM/commit 95% remain active.

API selection integration, complete protection, real Hancom layout/numbering,
reference update, semantic save/reopen and render remain open for this style path. `REF-025` still
needs actual external note export; the old digest manifest is not that feature. P09/A12/A13 remain
OPEN, the official queue remains 158/249 with 91 left and next case165, and P10 has not started.

The serializer contract is pinned to Hancom OWPML commit
`1453388472c703a4b299a0834f425cdac16644b9`, including
[placement.cpp](https://raw.githubusercontent.com/hancom-io/hwpx-owpml-model/1453388472c703a4b299a0834f425cdac16644b9/OWPML/Class/Para/placement.cpp),
[numbering.cpp](https://raw.githubusercontent.com/hancom-io/hwpx-owpml-model/1453388472c703a4b299a0834f425cdac16644b9/OWPML/Class/Para/numbering.cpp),
[noteLine.cpp](https://raw.githubusercontent.com/hancom-io/hwpx-owpml-model/1453388472c703a4b299a0834f425cdac16644b9/OWPML/Class/Para/noteLine.cpp) and
[AutoNumFormatType.cpp](https://raw.githubusercontent.com/hancom-io/hwpx-owpml-model/1453388472c703a4b299a0834f425cdac16644b9/OWPML/Class/Para/AutoNumFormatType.cpp).
Its catalogs and source hashes are recorded in `evidence/p09-03-note-engine-source-qualification.v1.json`.

## Original typed model decision

P09-03 is `five_capability_typed_component_pass / official_model_qualified /
digest_manifest_export_only / direct_hwpx_not_run / target_not_run / task_incomplete`.
The original typed model covers `REF-021` through `REF-025`: footnote insertion, endnote insertion,
section-specific note style replacement, note-kind conversion, and deterministic digest-manifest
projection. It does not lower or mutate an HWPX package, invoke installed Hangul, write an external
note file, or claim semantic reopen, field/reference readback, render, automation, differential,
production, P09, or product completion.

## Qualified native surface

The official Hancom `hwpx-owpml-model` source is pinned at commit
`1453388472c703a4b299a0834f425cdac16644b9`. The run-control model admits exact `footNote` and
`endNote` children backed by `NoteType`. Each note binds native `flag`, 16-bit `number`,
`userChar`, `prefixChar`, `suffixChar`, `instId`, and `subList` state. Each section independently
owns `footNotePr` and `endNotePr` with `autoNumFormat`, `noteLine`, `noteSpacing`, family-specific
numbering and placement, `newNum`, `beneathText`, and opaque remainder state.

The typed catalogs preserve all 22 official number formats, all 18 `LineType2` values and all 16
official line widths. Footnotes admit continuous/per-section/per-page numbering and each/merged/
right-most-column placement. Endnotes admit continuous/per-section numbering and end-of-document/
end-of-section placement. Cross-family numbering or placement is rejected instead of coerced.

## Complete state, operations and protection

The ordered state contains every section and note. A note binds logical/native identity, exact
paragraph/run/inline anchor, semantic kind plus native tag, marker properties, body graph and
optional plain-text digests, marker/body style digests, opaque native-payload remainder, ordered
opaque properties, and its lock. Document state additionally binds all non-note content, style,
numbering, reference, resource, protection and opaque-document digests. Every section binds both
note styles, opaque state and protection.

Insert changes only the requested ordered note slot. Style replacement changes only the selected
section and family. Convert changes semantic kind and exact native tag while preserving identity,
anchor, marker, body, styles and opaque payload. Locked documents, sections, notes and styles reject
mutation. `PrepareExport` is read-only and emits only a bounded document-ordered manifest of
identity, kind and body/plain-text digests; it neither exposes raw body content nor creates a file.

## Determinism and failure policy

Requests and builds independently recheck exact source-state and document-flow SHA-256. Plans seal
operation, capability, request, source/result state, source/result flow and optional export-manifest
digest. Duplicate or unknown JSON fields, oversized input/output, empty section inventories, zero or
colliding IDs, duplicate anchors, mismatched native tags, invalid marker characters/digests/styles,
family-incompatible numbering/placement, missing or duplicate export selections, invalid insertion
indexes, protected/no-op mutations, drift, and plan tampering fail without a partial result. Debug
output redacts identities, anchors, marker characters, body/style/opaque digests and selections.

## Evidence boundary

Focused Rust tests passed 9/9: eight public happy/boundary/negative/preservation tests and one
private sealed-plan tamper test. Private contract tests passed 5/5. These tests prove typed component
state and pinned source metadata only.

`unit_model_implemented=true`, `five_capabilities_unit_passed=true`,
`official_model_source_qualified=true`, `complete_bound_state_preserved=true`,
`note_style_and_protection_fixtures=true`, `request_and_build_drift_rejected=true`, and
`digest_manifest_export=true`. `actual_note_export=false`, `direct_hwpx=false`,
`actual_hwpx=false`, `actual_hangul=false`, `semantic_reopen=false`, `field_readback=false`,
`reference_update=false`, `hancom_open=false`, `save_reopen=false`, `render=false`,
`automation=false`, `differential=false`, `p09_03_green=false`, `p09_complete=false`,
`production_ready=false`, and `product_complete=false`.

Reasoning level: `max`. Exact HWPX lowering/readback and real note export remain `max`.
