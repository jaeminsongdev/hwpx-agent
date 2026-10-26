//! Real ArtifactService ACL/AEAD and RevisionService with memory repositories;
//! fixture scanner/keys/commits are NOT production issuer/SQL/Native evidence.
#![allow(dead_code)] // Shared fixture includes metadata/provider helpers for other hosts.
use domain_ir::{DocumentId, LogicalId, ReferenceAuxiliaryLimits, SourceAnchorHandle};
use hwpx_agent_cli::form_stored_provider::actual_import::{
    StoredImportedDocumentForms,
    bookmark_insertion_output::{
        PreparedStoredBookmarkInsertionCandidate as Candidate, StoredBookmarkInsertionError as E,
    },
};
use hwpx_package::{
    WriterLimits,
    cross_reference_sdk::SdkCrossReferenceDisplay as Display,
    document_import::fields::{
        ImportedDocumentFields, bookmark_insertion::SourceBookmarkInsertion as Request,
    },
};
use serde_json::{Value, json};
use sha2::{Digest as _, Sha256};
use std::{error::Error, fs::OpenOptions, io::Write, path::Path};
include!("support/stored_source_fixture.rs");
#[cfg(test)]
#[path = "support/bookmark_display_admission639.rs"]
mod admission639;
#[path="support/block_bookmark_authoring679.rs"]
mod block679;
pub fn fixed_block_output_batch681() -> Result<Value> { block679::fixed_block_output_batch681() }
#[path="support/bookmark_insertion_compiler708.rs"]
mod compiler708;
pub fn fixed_insertion_compiler708() -> Result<Value> { compiler708::observation() }
#[path="support/bookmark_insertion_request711.rs"]
mod request711;
pub fn fixed_insertion_request711() -> Result<Value> { request711::observation() }
#[path = "../../hwpx-package/tests/support/document_import_field_fixture.rs"]
#[allow(dead_code)]
mod base;
#[path = "../../hwpx-package/tests/support/document_import_bookmark_fixture.rs"]
#[allow(dead_code)]
mod fixture;
pub type Result<T = (), E = Box<dyn Error>> = std::result::Result<T, E>;
const DOC: &str = "p09-source-bookmark-first-insertion627";
const EXPECTED: &str = include_str!(
    "../../../implementation/p09/evidence/p09-361-bookmark-creation627-output-digests.v1.json"
);
pub fn require(ok: bool) -> Result {
    if ok {
        Ok(())
    } else {
        Err("P628_CURRENT_STORED_INSERTION_REJECTED_NO_RAW_VALUES".into())
    }
}
fn limits() -> Result<ReferenceAuxiliaryLimits> {
    Ok(ReferenceAuxiliaryLimits::new(Default::default())?)
}
fn sample() -> Result<Vec<u8>> {
    base::package(&format!(
        "<hp:p id='1'><hp:run>{}</hp:run></hp:p><hp:p id='2'><hp:run><hp:t>private-display&amp;原文</hp:t></hp:run></hp:p>",
        fixture::marker("private-target")
    ))
}
fn write_context(s: &StoredFixture) -> RequestContext {
    RequestContext::new(
        s.reader.tenant_id(),
        s.reader.subject(),
        [AuthScope::DocumentRead, AuthScope::DocumentWrite],
    )
}
fn provider<'a>(
    s: &'a StoredFixture,
    ctx: &'a RequestContext,
) -> std::result::Result<Provider<'a>, StoredFormError> {
    StoredFormProvider::bind(
        &s.artifacts,
        &s.revisions,
        ctx,
        &s.revision_context,
        s.project,
        s.branch,
        DocumentId::parse(DOC).map_err(|_| StoredFormError::Scope)?,
    )
}
fn selection(source: &StoredImportedDocumentForms) -> Result<(SourceAnchorHandle, LogicalId)> {
    let forms = source.imported();
    let raw = forms.source();
    let fields = ImportedDocumentFields::import(forms)?;
    for part in raw.parts() {
        if let Some(xml) = part.xml() {
            let mut intervals = Vec::new();
            for f in fields.fields() {
                let a = raw.resolve_anchor(&f.begin_anchor)?;
                let b = raw.resolve_anchor(&f.end_anchor)?;
                if a.part().path() == part.path() {
                    intervals.push((
                        a.element()
                            .ok_or("begin")?
                            .outer_span()
                            .ok_or("begin span")?
                            .start(),
                        b.element()
                            .ok_or("end")?
                            .outer_span()
                            .ok_or("end span")?
                            .end(),
                    ));
                }
            }
            for (i, n) in xml.elements().iter().enumerate() {
                if n.name().local_name() != "run"
                    || !n.first_child().is_some_and(|j| {
                        xml.elements()[j].name().local_name() == "t"
                            && xml.elements()[j].first_child().is_none()
                            && xml.elements()[j].next_sibling().is_none()
                    })
                {
                    continue;
                }
                let span = n.outer_span().ok_or("run span")?;
                if intervals
                    .iter()
                    .any(|(a, b)| *a < span.end() && span.start() < *b)
                {
                    continue;
                }
                return Ok((
                    part.element_anchor(i).ok_or("run anchor")?.clone(),
                    source
                        .bookmarks()
                        .first()
                        .ok_or("target")?
                        .reference_id
                        .clone(),
                ));
            }
        }
    }
    Err("P628_PLAIN_OUTSIDE_RUN_MISSING".into())
}
fn prepare(
    source: StoredImportedDocumentForms,
    p: &Provider<'_>,
    display: Display,
    hyperlink: bool,
) -> Result<Candidate> {
    let (run, target) = selection(&source)?;
    Ok(source.into_bookmark_insertion_candidate(
        p,
        Request {
            run: &run,
            target_id: &target,
            display,
            hyperlink,
        },
        limits()?,
        WriterLimits::default(),
        5,
    )?)
}
fn advance(s: &StoredFixture) -> Result {
    let request = RevisionCommitRequest::new(
        CommitId::generate(),
        s.project,
        s.branch,
        s.head,
        revision_service::RevisionId::generate(),
        s.head.revision_id().into_iter().collect(),
        artifact_service::ArtifactId::generate(),
        s.result,
        None,
        ContentDigest::of(b"P628 fixture advance"),
        RevisionValidationState::Verified,
        ContentDigest::of(b"fixture validation only"),
        ContentDigest::of(b"fixture transaction only"),
    )?;
    require(matches!(
        s.revisions.commit(&s.revision_context, &request)?,
        CommitOutcome::Committed(_)
    ))
}
#[test]
fn current_service_source_becomes_owned_new_field_without_commit() -> Result {
    let bytes = sample()?;
    let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let ctx = write_context(&s);
    let p = provider(&s, &ctx)?;
    let original_metadata = s
        .metadata
        .find(s.owner.tenant_id(), s.result)?
        .ok_or("source metadata")?;
    let source = p.import_actual_forms(s.head, 4)?;
    let c = prepare(source, &p, Display::BookmarkName, false)?;
    let out = c.with_verified_bytes(&p, 6, |v| v.to_vec())?;
    let forms = base::forms(&out, DOC)?;
    require(ImportedDocumentFields::import(&forms)?.fields().len() == 1)?;
    require(
        c.receipt().output.original_fields == 0
            && c.receipt().output.inserted_fields == 1
            && !c.receipt().output.requires_existing_crossref_envelope
            && !c.receipt().execution_or_publication_authority
            && !c
                .receipt()
                .output
                .native_currentness_execution_or_publication_qualified
            && s.revisions.head(&s.revision_context, s.project, s.branch)? == s.head,
    )?;
    require(
        !serde_json::to_string(c.receipt())?.contains("private-")
            && !format!("{c:?}").contains("private-"),
    )?;
    require(s.metadata.find(s.owner.tenant_id(), s.result)? == Some(original_metadata))
}
#[test]
fn write_scope_is_required_before_preparation() -> Result {
    let bytes = sample()?;
    let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let p = provider(&s, &s.reader)?;
    let source = p.import_actual_forms(s.head, 4)?;
    let (run, target) = selection(&source)?;
    require(matches!(
        source.into_bookmark_insertion_candidate(
            &p,
            Request {
                run: &run,
                target_id: &target,
                display: Display::Page,
                hyperlink: false
            },
            limits()?,
            WriterLimits::default(),
            5
        ),
        Err(E::Permission)
    ))
}
#[test]
fn acl_revoke_regrant_never_revives_denied_candidate() -> Result {
    let bytes = sample()?;
    let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let ctx = write_context(&s);
    let p = provider(&s, &ctx)?;
    let c = prepare(p.import_actual_forms(s.head, 4)?, &p, Display::Page, false)?;
    s.artifacts
        .set_permissions(&s.owner, s.result, s.reader.subject(), BTreeSet::new(), 6)?;
    let mut called = false;
    require(c.with_verified_bytes(&p, 7, |_| called = true).is_err() && !called)?;
    s.artifacts.set_permissions(
        &s.owner,
        s.result,
        s.reader.subject(),
        BTreeSet::from([ArtifactPermission::Read]),
        8,
    )?;
    require(
        matches!(
            c.with_verified_bytes(&p, 9, |_| called = true),
            Err(E::PreviouslyDenied)
        ) && !called,
    )?;
    let fresh = prepare(p.import_actual_forms(s.head, 9)?, &p, Display::Page, false)?;
    let _ = fresh.verify(&p, 10)?;
    Ok(())
}
#[test]
fn aead_failure_and_restoration_never_revive_denied_candidate() -> Result {
    let bytes = sample()?;
    let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let ctx = write_context(&s);
    let p = provider(&s, &ctx)?;
    let c = prepare(
        p.import_actual_forms(s.head, 4)?,
        &p,
        Display::BookmarkName,
        true,
    )?;
    s.blobs.tamper.store(true, Ordering::SeqCst);
    let mut called = false;
    require(c.with_verified_bytes(&p, 6, |_| called = true).is_err() && !called)?;
    s.blobs.tamper.store(false, Ordering::SeqCst);
    require(
        matches!(
            c.with_verified_bytes(&p, 7, |_| called = true),
            Err(E::PreviouslyDenied)
        ) && !called,
    )
}
#[test]
fn changed_head_denies_before_consumer_and_poison_is_sticky() -> Result {
    let bytes = sample()?;
    let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let ctx = write_context(&s);
    let p = provider(&s, &ctx)?;
    let c = prepare(
        p.import_actual_forms(s.head, 4)?,
        &p,
        Display::RelativePosition,
        false,
    )?;
    advance(&s)?;
    let mut called = false;
    require(c.with_verified_bytes(&p, 6, |_| called = true).is_err() && !called)?;
    require(
        matches!(
            c.with_verified_bytes(&p, 7, |_| called = true),
            Err(E::PreviouslyDenied)
        ) && !called,
    )
}
#[test]
fn foreign_provider_document_cannot_deliver_owned_output() -> Result {
    let bytes = sample()?;
    let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let ctx = write_context(&s);
    let p = provider(&s, &ctx)?;
    let c = prepare(
        p.import_actual_forms(s.head, 4)?,
        &p,
        Display::BookmarkName,
        true,
    )?;
    let other = StoredFormProvider::bind(
        &s.artifacts,
        &s.revisions,
        &ctx,
        &s.revision_context,
        s.project,
        s.branch,
        DocumentId::parse("foreign-document")?,
    )?;
    let mut called = false;
    require(c.with_verified_bytes(&other, 6, |_| called = true).is_err() && !called)?;
    require(
        matches!(
            c.with_verified_bytes(&p, 7, |_| called = true),
            Err(E::PreviouslyDenied)
        ) && !called,
    )
}
#[test]
fn quarantined_and_wrong_kind_sources_cannot_enter_preparation() -> Result {
    let bytes = sample()?;
    for (kind, unverified) in [(ArtifactKind::Result, true), (ArtifactKind::Source, false)] {
        let s = StoredFixture::new(&bytes, kind, unverified)?;
        let ctx = write_context(&s);
        let p = provider(&s, &ctx)?;
        require(p.import_actual_forms(s.head, 4).is_err())?;
    }
    Ok(())
}
#[test]
fn unqualified_route_is_not_a_write_grant_or_source_mutation() -> Result {
    let bytes = sample()?;
    let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let ctx = write_context(&s);
    let p = provider(&s, &ctx)?;
    let c = prepare(p.import_actual_forms(s.head, 4)?, &p, Display::Page, true)?;
    require(matches!(
        c.require_current_product_route(&p, 6),
        Err(E::RouteUnqualified)
    ))?;
    let _ = c.verify(&p, 7)?;
    require(s.revisions.head(&s.revision_context, s.project, s.branch)? == s.head)
}
fn read_pin(pin: &Value) -> Result<Vec<u8>> {
    let name = pin["path"].as_str().ok_or("path")?;
    require(
        name.starts_with("implementation/p09/evidence/private/")
            && !name.contains('\\')
            && !name.split('/').any(|s| s == ".." || s.is_empty()),
    )?;
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
    let path = root.join(name);
    regular_ancestors(&path)?;
    let m = path.metadata()?;
    require(m.is_file() && m.len() <= 4194304 && Some(m.len()) == pin["bytes"].as_u64())?;
    let bytes = std::fs::read(path)?;
    require(Some(hex::encode(Sha256::digest(&bytes)).as_str()) == pin["sha256"].as_str())?;
    Ok(bytes)
}
fn regular_ancestors(path: &Path) -> Result {
    for p in path.ancestors() {
        let m = p.symlink_metadata()?;
        require(!m.file_type().is_symlink())?;
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt as _;
            require(m.file_attributes() & 0x400 == 0)?;
        }
    }
    Ok(())
}
/// Only fixed private evidence copies; not result ingestion or a user revision.
pub fn fixed_output_batch(generation: u16) -> Result<Value> {
    require((1..=999).contains(&generation))?;
    let expected: Value = serde_json::from_str(EXPECTED)?;
    if expected["cases"]
        .as_array()
        .is_some_and(|cases| cases.iter().any(|c| c["display"] == "content"))
    {
        return Err("P628_CONSUMED_POINT_CONTENT_DISCOVERY_BATCH_RETIRED".into());
    }
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
    let relative = format!(
        "implementation/p09/evidence/private/p09-361-bookmark-insertion628-prepared-{generation:03}"
    );
    let directory = root.join(&relative);
    regular_ancestors(directory.parent().ok_or("parent")?)?;
    require(!directory.exists())?;
    std::fs::create_dir(&directory)?;
    regular_ancestors(&directory)?;
    let bytes = read_pin(&expected["source"])?;
    let mut rows = Vec::new();
    let cases = expected["cases"].as_array().ok_or("cases")?;
    require(cases.len() == 8)?;
    for (i, case) in cases.iter().enumerate() {
        require(case["case_index"].as_u64() == Some((i + 1) as u64))?;
        let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
        let ctx = write_context(&s);
        let p = provider(&s, &ctx)?;
        let display = match case["display"].as_str() {
            Some("page") => Display::Page,
            Some("bookmark_name") => Display::BookmarkName,
            Some("content") => Display::Content,
            Some("relative_position") => Display::RelativePosition,
            _ => return Err("P628_DISPLAY_REJECTED".into()),
        };
        let c = prepare(
            p.import_actual_forms(s.head, 4)?,
            &p,
            display,
            case["hyperlink"].as_bool().ok_or("hyperlink")?,
        )?;
        let filename = format!("case-{:02}.hwpx", i + 1);
        let path = directory.join(&filename);
        let pin = c.with_verified_bytes(&p, 6, |output| -> Result<Value> {
            let sha = hex::encode(Sha256::digest(output));
            require(Some(sha.as_str()) == case["output_sha256"].as_str())?;
            let mut f = OpenOptions::new()
                .write(true)
                .create_new(true)
                .open(&path)?;
            f.write_all(output)?;
            f.sync_all()?;
            Ok(json!({"path":format!("{relative}/{filename}"),"bytes":output.len(),"sha256":sha}))
        })??;
        require(s.revisions.head(&s.revision_context, s.project, s.branch)? == s.head)?;
        rows.push(json!({"case_index":i+1,"output":pin,"receipt":c.receipt(),"exact627_candidate_bytes":true}));
    }
    require(
        read_pin(&expected["source"])? == bytes && std::fs::read_dir(&directory)?.count() == 8,
    )?;
    Ok(
        json!({"state":"stored_bookmark_insertion628_prepared_eight_private_copies_not_CAS_or_native","observations":rows,
        "generation":generation,"actual_native_started":false,"head_changed":false,"result_ingested":false,"source_overwritten":false,
        "product_route_qualified":false,"P09_complete":false,"memory_repositories_scanner_and_keys_are_fixtures":true}),
    )
}
