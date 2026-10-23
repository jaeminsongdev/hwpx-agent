# Source note file export HWPX profile v1

`hwpx-agent.source-note-file-hwpx/v1` provides a new actual HWPX artifact candidate for
`ref.note_export`. It is additive to the old domain `NoteExportFormat::DigestManifestV1`;
that existing format and `PrepareExport` remain read-only digest projections. No database,
stored-document or old receipt migration occurs. The new stored-service candidate is additive too;
it does not convert old digest receipts into file output or authority.

## Operation

Call `ImportedDocumentStructure::export_note_file_candidate` with fresh source bytes,
`NoteFileSelection::Footnotes`, `Endnotes` or `Both`, finite NoteHwpxLimits and WriterLimits.
The result exposes a receipt and `with_verified_bytes`, not mutable internal bytes or an
execution/publication grant. The callback rechecks immutable SHA and the original writer's
package/ID/preservation chain. The caller chooses a new isolated output destination; the
component does not overwrite or publish the original.

Selected note body XML becomes ordinary body content in source insertion order. Every moved
element is namespace-closed and checked against original expanded names and local attributes.
Inherited xml:lang/xml:space are materialized without changing existing local overrides. The
original section-properties-only run is inserted at the first body element; empty sections,
manifest/spine/RDF/ODF links and header section count are reconciled. Known previews and caret
positions are invalidated. Other metadata, style definitions and resources are retained,
including unused source data. This is not a privacy-redaction tool.

Source and output keep the original bounded graph, preservation and shape/v6 ID validation.
No invalid paragraph IDs are repaired. Hidden notes, protection, active review/blocked/
quarantined content, signed/encrypted security, empty selections, drift and finite-limit failures
reject. Output is reparsed and every expected expanded part is matched before sealing it.

## Official behavior and target boundary

The [Hancom 120 help](https://help.hancom.com/hoffice120/ko-KR/Hwp/insert/annotations/annotations%28save%29.htm)
describes selecting all footnotes, all endnotes or both and collecting their contents in insertion
order into HWPX. The [multi-version help](https://help.hancom.com/hoffice/multi/ko_kr/hwp/insert/annotations/annotations%28save%29.htm)
describes the same selection/order but names HWP output. The attempted Hancom 110 help URL was
unavailable. These sources establish a common selection/order behavior, not exact behavior of
the installed Hancom 2020 command. This profile explicitly produces HWPX; it is not binary HWP
support or an automatic desktop fallback.

Note subList/container layout, effective numbering, field/reference updates, native save/reopen
and rendering still require target qualification. Copying original body XML and passing package
checks does not close those validators or the P09 Gate. Retained metadata/resources are not
guaranteed free of source information. Full protection and issuer/execution/publication remain
unqualified; a receipt is not source access permission or atomic CAS.

## Stored source integration

`StoredImportedDocumentForms::prepare_note_file_candidate` accepts the same family selection and
limits through the existing bound StoredFormProvider. It performs fresh scope/head/ACL/quarantine/AEAD
checks and complete Form reconstruction. The call-local VerifiedFormReconstruction may construct
the candidate only for its original instance and identical fresh bytes. It avoids a second full source
reconstruction, not the original writer's source package/ID/preservation or active/security validation.
The exported request digest keeps the exact v1 domain/source SHA/family-byte formula.

Each candidate verify or with_verified_bytes call reauthorizes the original source and checks the
sealed output; the writer callback checks the head immediately before invoking its consumer. A
receipt/proof is not retained access authority. The checks do not lock the head or implement atomic
CAS, and require_current_product_route always denies executable routes. No stored output ingest,
revision commit, issuer or publication route is introduced.

Section properties are assembled from the original run envelope, namespace environment and secPr
without materializing the unselected parent run. Packaging borrows selected section buffers, and
body-spine role takes precedence over coincidental settings.xml/metadata filenames.

## Verification and next integration

The first component run preserves six passes and two invalid fixture constructions. Only those
two were corrected and rerun, both passed, and the old six were excluded. Evidence is in
`implementation/p09/evidence/p09-361-source-note-export-components026.v1.json` and
`implementation/p09/evidence/p09-361-source-note-export-recovery027.v1.json`.
Tests cover actual temporary HWPX file creation/reopen, family/order, source preservation,
namespace/opaque/resource preservation, section/metadata/preview/caret reconciliation, guards,
limits and the historical six-export/three-ID-rejection policy. They are not Native equivalence.

The optimized core and stored join passed 11 core and 8 stored tests in
`implementation/p09/evidence/p09-361-stored-note-export-components030.v1.json`.
The 446 current inputs passed final fresh hashing; both owned jobs closed empty. The large-run test
compares identical collected output without making a wall-clock speedup claim. Stored cases cover
file creation/reopen, family/source/request binding, revoked/regranted access, quarantine/AEAD,
five foreign scopes, final-head races and the original finite/protection/ID failures. No API or 249-case
queue replay occurred. System CPU peaked at 30.86%, minimum available RAM was 19.2843%, and Job
private peaked at 1563.45 MiB/4.9071% under the existing resource guards.

The separate [product request v1](p09-note-file-product-request-v1.md) now prepares this candidate
through strict JSON and fresh provider write scope without caller-side Form import. Its owned
source handoff reuses these exact stored/compiler checks; it does not add an executable route.

The [XML context preservation rules](p09-note-export-xml-context.md) now cover inherited language
and valid space handling in both direct and stored-product candidates. Intermediate xml:base on
removed ancestors still rejects explicitly; URI interpretation and container geometry are not inferred.

Next is XML Base URI binding and note body-container/subList layout. Target Native layout/numbering/save/reopen/reference update/
render, complete protection and issuer/DB/CAS/execution/publication remain unqualified.
