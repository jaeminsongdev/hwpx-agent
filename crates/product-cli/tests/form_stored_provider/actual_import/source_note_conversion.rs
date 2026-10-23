//! Real stored-provider code over in-memory service fixtures; no Native/issuer acceptance.
use super::*;
use super::field_ranges::fixture;
use super::field_ranges::fixture as base;
use hwpx_agent_cli::form_stored_provider::actual_import::{StoredImportedDocumentForms,
    note_conversion_output::StoredNoteKindConversionError as E};
use hwpx_package::{NoteHwpxLimitConfig, NoteHwpxLimits, WriterLimitConfig, WriterLimits,
    document_import::structure::note_conversion::{NoteKindConversion, NoteKindConversionError as OutputError, note_kind_conversion_request_sha256}};
use domain_ir::{LogicalId, NoteKind};
use sha2::{Digest as _, Sha256};
use std::{cell::Cell, fs, path::Path, sync::atomic::AtomicUsize};
use revision_service as rev;
#[allow(dead_code)] // Reuse the existing table fixture; other shared constructors are irrelevant here.
#[path = "../../../../hwpx-package/tests/support/document_import_bookmark_fixture.rs"]
mod table_fixture;
#[path = "../../../../hwpx-package/tests/support/document_import_note_fixture.rs"]
mod legacy_notes;

fn limits() -> Result<NoteHwpxLimits, hwpx_package::NoteHwpxError> { NoteHwpxLimits::new(NoteHwpxLimitConfig::default()) }
fn note(kind: &str, paragraph: u32) -> String {
    format!("<hp:ctrl><hp:{kind} instId='101' number='1'><hp:subList><hp:p id='{paragraph}'><hp:run><hp:t>PRIVATE-NOTE-BODY &amp; value</hp:t></hp:run></hp:p></hp:subList></hp:{kind}></hp:ctrl>")
}
fn synthetic() -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    fixture::package(&format!("<hp:p id='1'><hp:run>{}{}<hp:t>KEEP-MAIN</hp:t></hp:run></hp:p>", note("footNote", 11), note("endNote", 12)))
}
fn requests(source: &StoredImportedDocumentForms) -> Vec<NoteKindConversion<'_>> {
    source.notes().iter().map(|n| NoteKindConversion {
        note_id: &n.note_id, source_note_sha256: n.source_anchor.fingerprint_sha256,
        target_kind: if n.native_kind == "footNote" { NoteKind::Endnote } else { NoteKind::Footnote },
    }).collect()
}
fn checked(path: &Path, bytes: usize, sha: &str) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    for ancestor in path.ancestors() {
        let m = fs::symlink_metadata(ancestor)?;
        if m.file_type().is_symlink() { return Err("note fixture link rejected".into()); }
        #[cfg(windows)] {
            use std::os::windows::fs::MetadataExt as _;
            if m.file_attributes() & 0x400 != 0 { return Err("note fixture reparse rejected".into()); }
        }
    }
    let m = fs::symlink_metadata(path)?;
    if !m.is_file() || m.len() != bytes as u64 || bytes > 4 * 1024 * 1024 { return Err("note fixture length rejected".into()); }
    let raw = fs::read(path)?;
    if hex::encode(Sha256::digest(&raw)) != sha { return Err("note fixture digest rejected".into()); }
    Ok(raw)
}
fn generated() -> Result<Vec<Vec<u8>>, Box<dyn std::error::Error>> {
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../../fixtures/target-build/p09-note-id-allocation-20261019-r01/output");
    let manifest: serde_json::Value = serde_json::from_slice(&checked(&root.join("fixture-manifest.json"), 9946,
        "b6a203872545155952ef925a140d156ca4b37f99372751dde0747a4aed853f48")?)?;
    assert_eq!(manifest["actual_hangul"], false); assert_eq!(manifest["green_rows"], 0);
    let cases = manifest["cases"].as_array().ok_or("cases")?;
    assert_eq!(cases.len(), 3);
    let expected = ["p09-24-c01-footnote.hwpx", "p09-24-c02-endnote.hwpx", "p09-24-c03-footnote-endnote.hwpx"];
    cases.iter().zip(expected).map(|(case, file)| {
        if case["file"] != file { return Err("fixed note filename drift".into()); }
        checked(&root.join(file), usize::try_from(case["package_bytes"].as_u64().ok_or("size")?)?, case["package_sha256"].as_str().ok_or("digest")?)
    }).collect()
}
#[test]
fn stored_note_kind_three_generated_sources_convert_with_original_authorization_and_no_publication() -> TestResult {
    for bytes in generated()? {
        let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
        let provider = stored.provider()?;
        let source = provider.import_actual_forms(stored.head, 4)?;
        let request = requests(&source);
        let candidate = source.prepare_note_kind_candidate(&provider, &request, limits()?, WriterLimits::default(), 5)?;
        let receipt = candidate.verify(&provider, 6)?;
        assert_eq!(receipt, *candidate.receipt());
        assert_eq!(receipt.requested_batch_sha256, note_kind_conversion_request_sha256(*ContentDigest::of(&bytes).as_bytes(), &request, limits()?)?);
        assert_eq!(receipt.output.converted_notes, request.len());
        assert!(!receipt.issuer_execution_publication_authority && !receipt.output.execution_publication_authority
            && !receipt.output.native_number_recalculation_qualified && !receipt.output.complete_protection_qualified);
        let output = candidate.with_verified_bytes(&provider, 7, <[u8]>::to_vec)?;
        let after = fixture::forms(&output, "actual-form-document")?;
        assert_eq!(after.notes().len(), source.notes().len());
        for (before, next) in source.notes().iter().zip(after.notes()) {
            assert_eq!(before.native_attributes, next.native_attributes);
            assert_ne!(before.native_kind, next.native_kind);
        }
        assert!(matches!(candidate.require_current_product_route(&provider, 8), Err(E::RouteUnqualified)));
        assert_eq!(stored.revisions.head(&stored.revision_context, stored.project, stored.branch)?, stored.head);
        assert_eq!(stored.metadata.audit_events()?.iter().filter(|a| a.event == "artifact.ingested").count(), 2);
        assert_eq!(source.verify(&provider, 9)?, *source.receipt());
        assert!(!format!("{candidate:?}").contains("PRIVATE-NOTE"));
    }
    Ok(())
}
#[test]
fn stored_note_kind_digest_keeps_original_format_and_binds_order_source_fingerprint_kind_and_count() -> TestResult {
    let bytes = synthetic()?; let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?; let source = provider.import_actual_forms(stored.head, 4)?;
    let request = requests(&source); let digest = *ContentDigest::of(&bytes).as_bytes();
    let mut old = Sha256::new(); old.update(b"hwpx-agent.source-note-kind-conversion/v1\0"); old.update(digest); old.update((request.len() as u64).to_le_bytes());
    for r in &request { old.update(Sha256::digest(r.note_id.as_str().as_bytes())); old.update(r.source_note_sha256); old.update([u8::from(r.target_kind == NoteKind::Endnote)]); }
    let expected: [u8; 32] = old.finalize().into();
    assert_eq!(note_kind_conversion_request_sha256(digest, &request, limits()?)?, expected);
    let candidate = source.prepare_note_kind_candidate(&provider, &request, limits()?, WriterLimits::default(), 4)?;
    assert_eq!(candidate.receipt().requested_batch_sha256, expected);
    let r = &request[0]; let s = &request[1]; let foreign = LogicalId::parse("private-foreign-note")?;
    let original = || vec![NoteKindConversion { note_id: r.note_id, source_note_sha256: r.source_note_sha256, target_kind: r.target_kind },
        NoteKindConversion { note_id: s.note_id, source_note_sha256: s.source_note_sha256, target_kind: s.target_kind }];
    let mut reversed = original(); reversed.swap(0, 1);
    let mut other_id = original(); other_id[0].note_id = &foreign;
    let mut other_fingerprint = original(); other_fingerprint[0].source_note_sha256 = [0;32];
    let mut other_kind = original(); other_kind[0].target_kind = NoteKind::Footnote;
    for changed in [reversed, other_id, other_fingerprint, other_kind] {
        assert_ne!(note_kind_conversion_request_sha256(digest, &changed, limits()?)?, expected);
    }
    assert_ne!(note_kind_conversion_request_sha256([0;32], &request, limits()?)?, expected);
    assert_ne!(note_kind_conversion_request_sha256(digest, &request[..1], limits()?)?, expected);
    Ok(())
}
#[test]
fn stored_note_kind_acl_revoke_and_regrant_never_turn_retained_receipt_or_proof_into_access() -> TestResult {
    let bytes = synthetic()?; let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?; let source = provider.import_actual_forms(stored.head, 4)?;
    let request = requests(&source); let candidate = source.prepare_note_kind_candidate(&provider, &request, limits()?, WriterLimits::default(), 4)?;
    let _receipt = candidate.verify(&provider, 4)?; let _proof = source.imported().reconstruct_source_for_verification(&bytes)?;
    stored.artifacts.set_permissions(&stored.owner, stored.result, stored.reader.subject(), BTreeSet::new(), 5)?;
    let called = Cell::new(false);
    assert!(matches!(candidate.with_verified_bytes(&provider, 6, |_| called.set(true)), Err(E::Source(_)))); assert!(!called.get());
    assert!(matches!(candidate.verify(&provider, 6), Err(E::Source(_))));
    assert!(matches!(candidate.require_current_product_route(&provider, 6), Err(E::Source(_))));
    assert!(matches!(source.prepare_note_kind_candidate(&provider, &request, limits()?, WriterLimits::default(), 6), Err(E::Source(_))));
    stored.artifacts.set_permissions(&stored.owner, stored.result, stored.reader.subject(), BTreeSet::from([artifact_service::ArtifactPermission::Read]), 7)?;
    candidate.verify(&provider, 8)?;
    assert!(matches!(candidate.require_current_product_route(&provider, 8), Err(E::RouteUnqualified)));
    Ok(())
}
#[test]
fn stored_note_kind_quarantine_and_aead_tamper_deny_every_output_exposure_and_repreparation() -> TestResult {
    for quarantine in [false, true] {
        let stored = StoredFixture::new(&synthetic()?, ArtifactKind::Result, false)?;
        let provider = stored.provider()?; let source = provider.import_actual_forms(stored.head, 4)?;
        let request = requests(&source); let candidate = source.prepare_note_kind_candidate(&provider, &request, limits()?, WriterLimits::default(), 4)?;
        if quarantine { stored.artifacts.quarantine(&stored.owner, stored.result, artifact_service::QuarantineReason::parse("NOTE_KIND_FIXTURE_QUARANTINE")?, 5)?; }
        else { stored.blobs.tamper.store(true, Ordering::SeqCst); }
        let called = Cell::new(false);
        assert!(matches!(candidate.with_verified_bytes(&provider, 6, |_| called.set(true)), Err(E::Source(_)))); assert!(!called.get());
        assert!(candidate.verify(&provider, 6).is_err()); assert!(candidate.require_current_product_route(&provider, 6).is_err());
        assert!(source.prepare_note_kind_candidate(&provider, &request, limits()?, WriterLimits::default(), 6).is_err());
    }
    Ok(())
}
#[test]
fn stored_note_kind_each_foreign_scope_cannot_rebind_prepared_output_or_source() -> TestResult {
    let stored = StoredFixture::new(&synthetic()?, ArtifactKind::Result, false)?;
    let provider = stored.provider()?; let source = provider.import_actual_forms(stored.head, 4)?;
    let request = requests(&source); let candidate = source.prepare_note_kind_candidate(&provider, &request, limits()?, WriterLimits::default(), 4)?;
    for variant in 0..5 {
        let tenant = if variant == 4 { TenantId::new(uuid::Uuid::from_u128(702))? } else { stored.reader.tenant_id() };
        let subject = if variant == 3 { stored.owner.subject() } else { stored.reader.subject() };
        let actor = RequestContext::new(tenant, subject, [AuthScope::DocumentRead]); let context = rev::RevisionRequestContext::new(tenant, subject);
        let project = if variant == 2 { rev::ProjectId::parse("prj_70000000000000000000000000000002")? } else { stored.project };
        let branch = if variant == 1 { rev::BranchId::parse("brn_70000000000000000000000000000002")? } else { stored.branch };
        let document = DocumentId::parse(if variant == 0 { "different-note-document" } else { "actual-form-document" })?;
        let other = StoredFormProvider::bind(&stored.artifacts, &stored.revisions, &actor, &context, project, branch, document)?;
        let called = Cell::new(false);
        assert!(matches!(candidate.with_verified_bytes(&other, 5, |_| called.set(true)), Err(E::Source(StoredActualFormImportError::Binding)))); assert!(!called.get());
        assert!(candidate.verify(&other, 5).is_err()); assert!(candidate.require_current_product_route(&other, 5).is_err());
        assert!(source.prepare_note_kind_candidate(&other, &request, limits()?, WriterLimits::default(), 5).is_err());
    }
    Ok(())
}
struct BoundaryRepo { inner: rev::InMemoryRevisionRepository, calls: AtomicUsize, trigger: AtomicUsize,
    context: rev::RevisionRequestContext, advance: rev::RevisionCommitRequest }
impl rev::RevisionRepository for BoundaryRepo {
    fn compare_and_swap(&self, c: &rev::RevisionRequestContext, r: &rev::RevisionCommitRequest) -> Result<rev::CommitOutcome, rev::RevisionError> { self.inner.compare_and_swap(c, r) }
    fn head(&self, t: TenantId, p: rev::ProjectId, b: rev::BranchId) -> Result<rev::RevisionHead, rev::RevisionError> {
        let call = self.calls.fetch_add(1, Ordering::SeqCst) + 1;
        if call == self.trigger.load(Ordering::SeqCst) { assert!(matches!(self.inner.compare_and_swap(&self.context, &self.advance)?, rev::CommitOutcome::Committed(_))); }
        self.inner.head(t, p, b)
    }
    fn node(&self, t: TenantId, p: rev::ProjectId, r: rev::RevisionId) -> Result<rev::RevisionNode, rev::RevisionError> { self.inner.node(t, p, r) }
}
#[test]
fn stored_note_kind_final_writer_head_boundary_blocks_consumer_and_retained_candidate() -> TestResult {
    let stored = StoredFixture::new(&synthetic()?, ArtifactKind::Result, false)?;
    let provider = stored.provider()?; let source = provider.import_actual_forms(stored.head, 4)?;
    let request = requests(&source); let candidate = source.prepare_note_kind_candidate(&provider, &request, limits()?, WriterLimits::default(), 4)?;
    let advance = rev::RevisionCommitRequest::new(rev::CommitId::generate(), stored.project, stored.branch, stored.head, rev::RevisionId::generate(), stored.head.revision_id().into_iter().collect(), artifact_service::ArtifactId::generate(), stored.result, None,
        ContentDigest::of(b"note boundary fixture"), rev::RevisionValidationState::Verified, ContentDigest::of(b"note validation fixture"), ContentDigest::of(b"note transaction fixture"))?;
    let boundary = rev::RevisionService::new(BoundaryRepo { inner: stored.revisions.repository().clone(), calls: AtomicUsize::new(0), trigger: AtomicUsize::new(usize::MAX), context: stored.revision_context.clone(), advance });
    let bound = StoredFormProvider::bind(&stored.artifacts, &boundary, &stored.reader, &stored.revision_context, stored.project, stored.branch, DocumentId::parse("actual-form-document")?)?;
    boundary.repository().calls.store(0, Ordering::SeqCst);
    candidate.with_verified_bytes(&bound, 5, |_| ())?;
    let reads = boundary.repository().calls.load(Ordering::SeqCst); assert!(reads >= 4);
    boundary.repository().calls.store(0, Ordering::SeqCst); boundary.repository().trigger.store(reads, Ordering::SeqCst);
    let called = Cell::new(false);
    assert!(matches!(candidate.with_verified_bytes(&bound, 6, |_| called.set(true)), Err(E::Source(_)))); assert!(!called.get());
    assert_eq!(boundary.repository().calls.load(Ordering::SeqCst), reads);
    assert_ne!(stored.revisions.head(&stored.revision_context, stored.project, stored.branch)?, stored.head);
    assert!(candidate.verify(&provider, 6).is_err()); assert!(candidate.require_current_product_route(&provider, 6).is_err());
    assert!(source.prepare_note_kind_candidate(&provider, &request, limits()?, WriterLimits::default(), 6).is_err());
    Ok(())
}
#[test]
fn stored_note_kind_original_selection_protection_and_finite_limits_remain_fail_closed() -> TestResult {
    let stored = StoredFixture::new(&synthetic()?, ArtifactKind::Result, false)?;
    let provider = stored.provider()?; let source = provider.import_actual_forms(stored.head, 4)?; let request = requests(&source); let first = &request[0];
    let duplicate = [NoteKindConversion { note_id: first.note_id, source_note_sha256: first.source_note_sha256, target_kind: first.target_kind }, NoteKindConversion { note_id: first.note_id, source_note_sha256: first.source_note_sha256, target_kind: first.target_kind }];
    let foreign = LogicalId::parse("foreign-note")?;
    for bad in [Vec::new(), duplicate.into_iter().collect(), vec![NoteKindConversion { note_id: &foreign, source_note_sha256: first.source_note_sha256, target_kind: first.target_kind }], vec![NoteKindConversion { note_id: first.note_id, source_note_sha256: [0;32], target_kind: first.target_kind }]] {
        assert!(matches!(source.prepare_note_kind_candidate(&provider, &bad, limits()?, WriterLimits::default(), 4), Err(E::Output(OutputError::Selection))));
    }
    let noop = [NoteKindConversion { note_id: first.note_id, source_note_sha256: first.source_note_sha256, target_kind: NoteKind::Footnote }];
    assert!(matches!(source.prepare_note_kind_candidate(&provider, &noop, limits()?, WriterLimits::default(), 4), Err(E::Output(OutputError::NoChange))));
    let tight = NoteHwpxLimits::new(NoteHwpxLimitConfig { notes: 1, ..NoteHwpxLimitConfig::default() })?;
    assert!(matches!(source.prepare_note_kind_candidate(&provider, &request, tight, WriterLimits::default(), 4), Err(E::Output(OutputError::Limit))));
    assert!(matches!(source.prepare_note_kind_candidate(&provider, &request, limits()?, WriterLimits::new(WriterLimitConfig { max_output_bytes: 1 })?, 4), Err(E::Output(OutputError::Writer))));
    let locked = fixture::package(&table_fixture::paragraph(&table_fixture::table(&note("footNote", 11))).replace("lock=\"0\"", "lock=\"1\""))?;
    let protected = StoredFixture::new(&locked, ArtifactKind::Result, false)?; let access = protected.provider()?; let model = access.import_actual_forms(protected.head, 4)?; let selected = requests(&model);
    assert!(matches!(model.prepare_note_kind_candidate(&access, &selected, limits()?, WriterLimits::default(), 4), Err(E::Output(OutputError::Protection))));
    assert_eq!(stored.metadata.audit_events()?.iter().filter(|a| a.event == "artifact.ingested").count(), 2);
    Ok(())
}
#[test]
fn stored_note_kind_original_nine_sources_convert_six_and_reject_three_without_rewriting_history() -> TestResult {
    let (mut converted, mut rejected) = (0usize, 0usize);
    let mut lanes = [0usize; 3];
    for input in legacy_notes::actual_inputs()? {
        lanes[match input.lane { "generated" => 0, "saved" => 1, "reopened" => 2, _ => return Err("unknown locked note lane".into()) }] += 1;
        let stored = StoredFixture::new(&input.bytes, ArtifactKind::Result, false)?; let provider = stored.provider()?;
        let source = provider.import_actual_forms(stored.head, 4)?; let request = requests(&source);
        let output = source.prepare_note_kind_candidate(&provider, &request, limits()?, WriterLimits::default(), 4);
        if input.expected_notes == 2 { assert!(matches!(output, Err(E::Output(OutputError::Patch("id_index_duplicate_declaration"))))); rejected += 1; }
        else { let candidate = output?; candidate.with_verified_bytes(&provider, 5, |_| ())?; converted += 1; }
        assert_eq!(source.verify(&provider, 6)?, *source.receipt());
        assert_eq!(stored.revisions.head(&stored.revision_context, stored.project, stored.branch)?, stored.head);
    }
    assert_eq!((converted, rejected), (6, 3));
    assert_eq!(lanes, [3, 3, 3]);
    Ok(())
}

fn api_owned_selectors(value: &serde_json::Value) -> Result<Vec<(LogicalId, [u8; 32], NoteKind)>, Box<dyn std::error::Error>> {
    value["note_selections"].as_array().ok_or("API note selectors")?.iter().map(|entry| {
        Ok((LogicalId::parse(entry["note_id"].as_str().ok_or("API note ID")?)?,
            serde_json::from_value(entry["source_note_sha256"].clone())?, serde_json::from_value(entry["kind"].clone())?))
    }).collect()
}
fn api_requests(values: &[(LogicalId, [u8; 32], NoteKind)]) -> Vec<NoteKindConversion<'_>> {
    values.iter().map(|(id, fingerprint, kind)| NoteKindConversion { note_id: id, source_note_sha256: *fingerprint,
        target_kind: if *kind == NoteKind::Footnote { NoteKind::Endnote } else { NoteKind::Footnote } }).collect()
}
#[test]
fn stored_note_kind_reference_source_api_json_builds_requests_and_rejects_foreign_stale_or_revoked_access() -> TestResult {
    use hwpx_agent_cli::reference_validation_product::{ReferenceValidationProductOperation as Product,
        source::ReferenceSourceStatus};
    let bytes = synthetic()?; let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?; let source = provider.import_actual_forms(stored.head, 4)?;
    let reference_limits = domain_ir::ReferenceAuxiliaryLimits::new(Default::default())?;
    let assess = |data: &[u8], document: &str| Product::assess_package_source(data, DocumentId::parse(document).expect("fixed document"),
        Sha256::digest(data).into(), SourceImportLimits::default(), reference_limits);
    let report = assess(&bytes, "actual-form-document")?;
    let response: serde_json::Value = serde_json::from_slice(&report.canonical_json(reference_limits)?)?;
    assert_eq!(response["schema_version"], "hwpx-agent.product.reference-source-assessment/v13");
    let selected = api_owned_selectors(&response)?; let request = api_requests(&selected);
    // Selection comes from the product JSON alone: no caller-side Form/Note
    // import and no raw body, native attributes, guessed IDs or cached grant.
    let candidate = source.prepare_note_kind_candidate(&provider, &request, limits()?, WriterLimits::default(), 4)?;
    assert_eq!(candidate.receipt().requested_notes, 2);
    let output = candidate.with_verified_bytes(&provider, 5, <[u8]>::to_vec)?;
    let after = assess(&output, "actual-form-document")?;
    assert_eq!(after.note_selections().len(), selected.len());
    for ((old_id, _, old_kind), next) in selected.iter().zip(after.note_selections()) {
        assert_ne!(old_id, next.note_id()); assert_ne!(*old_kind, next.kind());
    }
    assert_eq!(after.status(), ReferenceSourceStatus::Incomplete); assert!(after.validation_report().is_none());
    let foreign = assess(&bytes, "foreign-note-api-document")?;
    let changed = fixture::package(&format!("<hp:p id='1'><hp:run>{}{}<hp:t>DIFFERENT-PRIVATE-MAIN</hp:t></hp:run></hp:p>", note("footNote", 11), note("endNote", 12)))?;
    let stale = assess(&changed, "actual-form-document")?;
    for other in [foreign, stale] {
        let json: serde_json::Value = serde_json::from_slice(&other.canonical_json(reference_limits)?)?;
        let selected = api_owned_selectors(&json)?; let wrong = api_requests(&selected);
        assert!(matches!(source.prepare_note_kind_candidate(&provider, &wrong, limits()?, WriterLimits::default(), 5), Err(E::Output(OutputError::Selection))));
    }
    let mut changed = selected.clone(); changed[0].1[0] ^= 1; let wrong = api_requests(&changed);
    assert!(matches!(source.prepare_note_kind_candidate(&provider, &wrong, limits()?, WriterLimits::default(), 5), Err(E::Output(OutputError::Selection))));
    assert!(matches!(candidate.require_current_product_route(&provider, 5), Err(E::RouteUnqualified)));
    assert_eq!(stored.revisions.head(&stored.revision_context, stored.project, stored.branch)?, stored.head);
    assert_eq!(stored.metadata.audit_events()?.iter().filter(|a| a.event == "artifact.ingested").count(), 2);
    stored.artifacts.set_permissions(&stored.owner, stored.result, stored.reader.subject(), BTreeSet::new(), 6)?;
    let called = Cell::new(false);
    assert!(matches!(candidate.with_verified_bytes(&provider, 7, |_| called.set(true)), Err(E::Source(_)))); assert!(!called.get());
    assert!(matches!(source.prepare_note_kind_candidate(&provider, &request, limits()?, WriterLimits::default(), 7), Err(E::Source(_))));
    Ok(())
}
