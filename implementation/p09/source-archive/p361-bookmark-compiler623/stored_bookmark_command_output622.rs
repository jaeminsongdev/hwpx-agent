//! Focused authenticated stored updates; memory repositories/keys/scanner are fixtures only.
use domain_ir::{DocumentId, LogicalId, ReferenceAuxiliaryLimits};
use hwpx_agent_cli::{
    form_stored_provider::actual_import::{
        StoredImportedDocumentForms,
        bookmark_command_output::{
            PreparedStoredBookmarkCommandCandidate, StoredBookmarkCommandError as E,
        },
    },
    reference_validation_product::ReferenceValidationProductOperation as Product,
};
use hwpx_package::{
    WriterLimits,
    cross_reference_sdk::SdkCrossReferenceDisplay as Display,
    document_import::{
        SourceImportLimits,
        fields::{
            ImportedDocumentFields,
            bookmark_crossref::SourceBookmarkResolution,
            semantics::{
                ImportedFieldMeaning,
                source_index::{
                    SourceFieldMeaningIndex,
                    bookmark_updates::SourceBookmarkCommandChange as Change,
                },
            },
        },
    },
};
use revision_service::{RevisionError, RevisionNode, RevisionRepository};
use serde_json::{Value, json};
use sha2::{Digest as _, Sha256};
use std::{
    error::Error,
    fs::OpenOptions,
    io::Read,
    path::Path,
    sync::atomic::AtomicUsize,
    time::{Duration, Instant},
};
include!("support/stored_source_fixture.rs");
#[path = "../../hwpx-package/tests/support/document_import_field_fixture.rs"]
#[allow(dead_code)]
mod base;
#[path = "../../hwpx-package/tests/support/document_import_bookmark_fixture.rs"]
#[allow(dead_code)]
mod fixture;
type TestResult = Result<(), Box<dyn Error>>;
fn limits() -> Result<ReferenceAuxiliaryLimits, Box<dyn Error>> {
    Ok(ReferenceAuxiliaryLimits::new(Default::default())?)
}
fn require(ok: bool) -> TestResult {
    if ok {
        Ok(())
    } else {
        Err("P622_STORED_OBSERVATION_REJECTED".into())
    }
}
fn sample() -> Result<Vec<u8>, Box<dyn Error>> {
    base::package(&fixture::paragraph(&format!(
        "{}{}<hp:ctrl><hp:fieldBegin id='7' type='CROSSREF'><hp:parameters cnt='1'><hp:stringParam name='Command'>?private-old;6;1;0;0</hp:stringParam></hp:parameters></hp:fieldBegin></hp:ctrl><hp:t>private-cache&amp;原文</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='7'/></hp:ctrl>",
        fixture::marker("private-old"),
        fixture::marker("private-new")
    )))
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
) -> Result<Provider<'a>, StoredFormError> {
    StoredFormProvider::bind(
        &s.artifacts,
        &s.revisions,
        ctx,
        &s.revision_context,
        s.project,
        s.branch,
        DocumentId::parse("actual-form-document").map_err(|_| StoredFormError::Scope)?,
    )
}
struct Selection {
    id: LogicalId,
    field: [u8; 32],
    meaning: [u8; 32],
    target: LogicalId,
}
impl Selection {
    fn request(&self) -> Change<'_> {
        Change {
            reference_id: &self.id,
            expected_source_field_sha256: self.field,
            expected_meaning_sha256: self.meaning,
            target_id: &self.target,
            display: Display::Page,
            hyperlink: true,
        }
    }
}
fn selection(
    source: &StoredImportedDocumentForms,
    new_target: bool,
) -> Result<Selection, Box<dyn Error>> {
    let fields = ImportedDocumentFields::import(source.imported())?;
    let index = SourceFieldMeaningIndex::import(&fields, limits()?)?;
    let (i, f) = fields
        .fields()
        .iter()
        .enumerate()
        .find(|(_, f)| f.native_kind == "CROSSREF")
        .ok_or("field")?;
    let target = if new_target {
        source
            .bookmarks()
            .get(1)
            .ok_or("new target")?
            .reference_id
            .clone()
    } else {
        let ImportedFieldMeaning::BookmarkCrossReference { command } =
            &index.observations()[i].meaning
        else {
            return Err("meaning".into());
        };
        let SourceBookmarkResolution::Bound {
            logical_target_id, ..
        } = &command.target
        else {
            return Err("bound".into());
        };
        logical_target_id.clone()
    };
    Ok(Selection {
        id: f.reference_id.clone(),
        field: f.begin_anchor.fingerprint_sha256,
        meaning: index.meaning_sha256(i)?,
        target,
    })
}
fn prepare<'a>(
    source: &'a StoredImportedDocumentForms,
    p: &Provider<'_>,
    s: &Selection,
) -> Result<PreparedStoredBookmarkCommandCandidate<'a>, E> {
    source.prepare_bookmark_command_candidate(
        p,
        &[s.request()],
        limits().map_err(|_| E::Binding)?,
        WriterLimits::default(),
        5,
    )
}
fn advance(s: &StoredFixture) -> TestResult {
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
        ContentDigest::of(b"advance-fixture"),
        RevisionValidationState::Verified,
        ContentDigest::of(b"validation-fixture"),
        ContentDigest::of(b"transaction-fixture"),
    )?;
    assert!(matches!(
        s.revisions.commit(&s.revision_context, &request)?,
        CommitOutcome::Committed(_)
    ));
    Ok(())
}
#[test]
fn actual_acl_aead_source_and_direct_lowerer_produce_equal_owned_bytes_without_publish()
-> TestResult {
    let bytes = sample()?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let ctx = write_context(&stored);
    let p = provider(&stored, &ctx)?;
    let source = p.import_actual_forms(stored.head, 4)?;
    let s = selection(&source, true)?;
    let candidate = prepare(&source, &p, &s)?;
    let direct = Product::prepare_source_bookmark_command_changes(
        &bytes,
        DocumentId::parse("actual-form-document")?,
        Sha256::digest(&bytes).into(),
        SourceImportLimits::default(),
        limits()?,
        &[s.request()],
        WriterLimits::default(),
    )?;
    assert_eq!(&candidate.receipt().output, direct.receipt());
    let actual = candidate.with_verified_bytes(&p, 6, |v| v.to_vec())?;
    assert_eq!(actual, direct.with_verified_bytes(|v| v.to_vec())?);
    assert_eq!(candidate.verify(&p, 7)?, candidate.receipt());
    assert!(!candidate.receipt().execution_or_publication_authority);
    assert!(matches!(
        candidate.require_current_product_route(&p, 8),
        Err(E::RouteUnqualified)
    ));
    assert_eq!(
        stored
            .revisions
            .head(&stored.revision_context, stored.project, stored.branch)?,
        stored.head
    );
    assert_eq!(
        stored
            .metadata
            .audit_events()?
            .iter()
            .filter(|v| v.event == "artifact.ingested")
            .count(),
        2
    );
    assert_eq!(
        stored.artifacts.download(&stored.owner, stored.result, 9)?,
        bytes
    );
    assert!(!format!("{candidate:?}").contains("private-cache"));
    Ok(())
}
#[test]
fn read_scope_alone_never_prepares_a_mutation_candidate() -> TestResult {
    let stored = StoredFixture::new(&sample()?, ArtifactKind::Result, false)?;
    let p = stored.provider()?;
    let source = p.import_actual_forms(stored.head, 4)?;
    let s = selection(&source, true)?;
    assert!(matches!(prepare(&source, &p, &s), Err(E::Permission)));
    Ok(())
}
#[test]
fn acl_revoke_prevents_delivery_and_regrant_cannot_revive_denied_candidate() -> TestResult {
    let stored = StoredFixture::new(&sample()?, ArtifactKind::Result, false)?;
    let ctx = write_context(&stored);
    let p = provider(&stored, &ctx)?;
    let source = p.import_actual_forms(stored.head, 4)?;
    let s = selection(&source, true)?;
    let c = prepare(&source, &p, &s)?;
    stored.artifacts.set_permissions(
        &stored.owner,
        stored.result,
        stored.reader.subject(),
        BTreeSet::new(),
        6,
    )?;
    let hit = AtomicBool::new(false);
    assert!(
        c.with_verified_bytes(&p, 7, |_| hit.store(true, Ordering::SeqCst))
            .is_err()
    );
    assert!(!hit.load(Ordering::SeqCst));
    stored.artifacts.set_permissions(
        &stored.owner,
        stored.result,
        stored.reader.subject(),
        BTreeSet::from([ArtifactPermission::Read]),
        8,
    )?;
    assert!(matches!(c.verify(&p, 9), Err(E::PreviouslyDenied)));
    Ok(())
}
#[test]
fn quarantine_and_aead_tamper_deny_retained_and_new_preparation() -> TestResult {
    for quarantine in [false, true] {
        let stored = StoredFixture::new(&sample()?, ArtifactKind::Result, false)?;
        let ctx = write_context(&stored);
        let p = provider(&stored, &ctx)?;
        let source = p.import_actual_forms(stored.head, 4)?;
        let s = selection(&source, true)?;
        let c = prepare(&source, &p, &s)?;
        if quarantine {
            stored.artifacts.quarantine(
                &stored.owner,
                stored.result,
                QuarantineReason::parse("BOOKMARK_FIXTURE_QUARANTINE")?,
                6,
            )?;
        } else {
            stored.blobs.tamper.store(true, Ordering::SeqCst);
        }
        let hit = AtomicBool::new(false);
        assert!(
            c.with_verified_bytes(&p, 7, |_| hit.store(true, Ordering::SeqCst))
                .is_err()
        );
        assert!(!hit.load(Ordering::SeqCst));
        assert!(prepare(&source, &p, &s).is_err());
    }
    Ok(())
}
#[test]
fn restoring_ciphertext_cannot_revive_a_candidate_after_observed_integrity_denial() -> TestResult {
    let stored = StoredFixture::new(&sample()?, ArtifactKind::Result, false)?;
    let ctx = write_context(&stored);
    let p = provider(&stored, &ctx)?;
    let source = p.import_actual_forms(stored.head, 4)?;
    let s = selection(&source, true)?;
    let c = prepare(&source, &p, &s)?;
    stored.blobs.tamper.store(true, Ordering::SeqCst);
    assert!(c.verify(&p, 6).is_err());
    stored.blobs.tamper.store(false, Ordering::SeqCst);
    assert!(matches!(c.verify(&p, 7), Err(E::PreviouslyDenied)));
    Ok(())
}
#[test]
fn unverified_scan_or_wrong_artifact_kind_never_imports() -> TestResult {
    for (kind, scan) in [
        (ArtifactKind::Result, true),
        (ArtifactKind::Evidence, false),
        (ArtifactKind::Source, false),
    ] {
        let stored = StoredFixture::new(&sample()?, kind, scan)?;
        let ctx = write_context(&stored);
        let p = provider(&stored, &ctx)?;
        assert!(p.import_actual_forms(stored.head, 4).is_err());
    }
    Ok(())
}
#[test]
fn all_five_foreign_scopes_deny_source_candidate_and_callback() -> TestResult {
    let stored = StoredFixture::new(&sample()?, ArtifactKind::Result, false)?;
    let ctx = write_context(&stored);
    let p = provider(&stored, &ctx)?;
    let source = p.import_actual_forms(stored.head, 4)?;
    let s = selection(&source, true)?;
    for variant in 0..5 {
        let c = prepare(&source, &p, &s)?;
        let tenant = if variant == 4 {
            TenantId::new(Uuid::from_u128(622))?
        } else {
            ctx.tenant_id()
        };
        let subject = if variant == 3 {
            stored.owner.subject()
        } else {
            ctx.subject()
        };
        let ac = RequestContext::new(
            tenant,
            subject,
            [AuthScope::DocumentRead, AuthScope::DocumentWrite],
        );
        let rc = RevisionRequestContext::new(tenant, subject);
        let other = StoredFormProvider::bind(
            &stored.artifacts,
            &stored.revisions,
            &ac,
            &rc,
            if variant == 0 {
                revision_service::ProjectId::generate()
            } else {
                stored.project
            },
            if variant == 1 {
                BranchId::generate()
            } else {
                stored.branch
            },
            DocumentId::parse(if variant == 2 {
                "foreign-document"
            } else {
                "actual-form-document"
            })?,
        )?;
        let hit = AtomicBool::new(false);
        assert!(
            c.with_verified_bytes(&other, 6, |_| hit.store(true, Ordering::SeqCst))
                .is_err()
        );
        assert!(!hit.load(Ordering::SeqCst));
        assert!(prepare(&source, &other, &s).is_err());
    }
    Ok(())
}
#[test]
fn real_head_advance_blocks_delivery_and_retained_receipt_is_not_authority() -> TestResult {
    let stored = StoredFixture::new(&sample()?, ArtifactKind::Result, false)?;
    let ctx = write_context(&stored);
    let p = provider(&stored, &ctx)?;
    let source = p.import_actual_forms(stored.head, 4)?;
    let s = selection(&source, true)?;
    let c = prepare(&source, &p, &s)?;
    advance(&stored)?;
    let hit = AtomicBool::new(false);
    assert!(
        c.with_verified_bytes(&p, 6, |_| hit.store(true, Ordering::SeqCst))
            .is_err()
    );
    assert!(!hit.load(Ordering::SeqCst));
    assert!(prepare(&source, &p, &s).is_err());
    Ok(())
}
struct HeadFault<'a> {
    inner: InMemoryRevisionRepository,
    reads: AtomicUsize,
    at: AtomicUsize,
    fail: bool,
    hook: Option<Box<dyn Fn() + Send + Sync + 'a>>,
}
impl HeadFault<'_> {
    fn arm(&self, at: usize) {
        self.reads.store(0, Ordering::SeqCst);
        self.at.store(at, Ordering::SeqCst);
    }
}
impl RevisionRepository for HeadFault<'_> {
    fn authorize_context(&self, c: &RevisionRequestContext) -> Result<(), RevisionError> {
        self.inner.authorize_context(c)
    }
    fn compare_and_swap(
        &self,
        c: &RevisionRequestContext,
        r: &RevisionCommitRequest,
    ) -> Result<CommitOutcome, RevisionError> {
        self.inner.compare_and_swap(c, r)
    }
    fn head(
        &self,
        t: TenantId,
        p: revision_service::ProjectId,
        b: BranchId,
    ) -> Result<RevisionHead, RevisionError> {
        let n = self.reads.fetch_add(1, Ordering::SeqCst) + 1;
        if n == self.at.load(Ordering::SeqCst) {
            if let Some(h) = &self.hook {
                h();
            }
            if self.fail {
                return Ok(RevisionHead::empty());
            }
        }
        self.inner.head(t, p, b)
    }
    fn node(
        &self,
        t: TenantId,
        p: revision_service::ProjectId,
        r: revision_service::RevisionId,
    ) -> Result<RevisionNode, RevisionError> {
        self.inner.node(t, p, r)
    }
}
#[test]
fn final_head_check_inside_writer_callback_denies_consumer_after_successful_full_read() -> TestResult
{
    let stored = StoredFixture::new(&sample()?, ArtifactKind::Result, false)?;
    let ctx = write_context(&stored);
    let revisions = RevisionService::new(HeadFault {
        inner: stored.revisions.repository().clone(),
        reads: AtomicUsize::new(0),
        at: AtomicUsize::new(0),
        fail: true,
        hook: None,
    });
    let p = StoredFormProvider::bind(
        &stored.artifacts,
        &revisions,
        &ctx,
        &stored.revision_context,
        stored.project,
        stored.branch,
        DocumentId::parse("actual-form-document")?,
    )?;
    let source = p.import_actual_forms(stored.head, 4)?;
    let s = selection(&source, true)?;
    let c = source.prepare_bookmark_command_candidate(
        &p,
        &[s.request()],
        limits()?,
        WriterLimits::default(),
        5,
    )?;
    revisions.repository().arm(6);
    let hit = AtomicBool::new(false);
    assert!(
        c.with_verified_bytes(&p, 6, |_| hit.store(true, Ordering::SeqCst))
            .is_err()
    );
    assert!(!hit.load(Ordering::SeqCst));
    assert_eq!(revisions.repository().reads.load(Ordering::SeqCst), 6);
    Ok(())
}
#[test]
fn final_acl_recheck_blocks_revocation_after_the_first_whole_source_reconstruction() -> TestResult {
    let stored = StoredFixture::new(&sample()?, ArtifactKind::Result, false)?;
    let ctx = write_context(&stored);
    let revoke = || {
        stored
            .artifacts
            .set_permissions(
                &stored.owner,
                stored.result,
                stored.reader.subject(),
                BTreeSet::new(),
                6,
            )
            .expect("fixture ACL revocation");
    };
    let revisions = RevisionService::new(HeadFault {
        inner: stored.revisions.repository().clone(),
        reads: AtomicUsize::new(0),
        at: AtomicUsize::new(0),
        fail: false,
        hook: Some(Box::new(revoke)),
    });
    let p = StoredFormProvider::bind(
        &stored.artifacts,
        &revisions,
        &ctx,
        &stored.revision_context,
        stored.project,
        stored.branch,
        DocumentId::parse("actual-form-document")?,
    )?;
    let source = p.import_actual_forms(stored.head, 4)?;
    let s = selection(&source, true)?;
    let c = source.prepare_bookmark_command_candidate(
        &p,
        &[s.request()],
        limits()?,
        WriterLimits::default(),
        5,
    )?;
    revisions.repository().arm(4);
    let hit = AtomicBool::new(false);
    assert!(
        c.with_verified_bytes(&p, 7, |_| hit.store(true, Ordering::SeqCst))
            .is_err()
    );
    assert!(!hit.load(Ordering::SeqCst));
    assert_eq!(revisions.repository().reads.load(Ordering::SeqCst), 4);
    Ok(())
}
#[test]
fn source_bound_fingerprints_cannot_be_forged_even_with_write_scope() -> TestResult {
    let stored = StoredFixture::new(&sample()?, ArtifactKind::Result, false)?;
    let ctx = write_context(&stored);
    let p = provider(&stored, &ctx)?;
    let source = p.import_actual_forms(stored.head, 4)?;
    let mut s = selection(&source, true)?;
    s.field = [0; 32];
    assert!(matches!(prepare(&source, &p, &s), Err(E::Output(_))));
    Ok(())
}
const CORPUS: &str = include_str!(
    "../../../implementation/p09/evidence/p09-361-capture010-bookmark-binding-corpus613.v1.json"
);
fn read_pin(pin: &Value) -> Result<Vec<u8>, Box<dyn Error>> {
    let name = pin["path"].as_str().ok_or("pin")?;
    require(
        name.starts_with("implementation/p09/evidence/private/")
            && !name.contains('\\')
            && !name.split('/').any(|v| v == ".." || v.is_empty()),
    )?;
    let root = Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .ok_or("root")?;
    let path = root.join(name);
    for ancestor in path.ancestors() {
        let m = ancestor.symlink_metadata()?;
        require(!m.file_type().is_symlink())?;
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt as _;
            require(m.file_attributes() & 0x400 == 0)?;
        }
    }
    let size = pin["bytes"].as_u64().ok_or("size")?;
    require(size > 0 && size <= 4194304 && path.is_file() && path.metadata()?.len() == size)?;
    std::thread::sleep(Duration::from_millis(50));
    let mut options = OpenOptions::new();
    options.read(true);
    #[cfg(windows)]
    {
        use std::os::windows::fs::OpenOptionsExt as _;
        options.share_mode(1);
    }
    let mut file = options.open(path)?;
    let mut bytes = Vec::new();
    let mut buffer = [0; 65536];
    let watch = Instant::now();
    loop {
        let n = file.read(&mut buffer)?;
        if n == 0 {
            break;
        }
        require(bytes.len() + n <= 4194304)?;
        bytes.try_reserve(n)?;
        bytes.extend_from_slice(&buffer[..n]);
        if let Some(delay) =
            Duration::from_secs_f64(bytes.len() as f64 / 2097152.).checked_sub(watch.elapsed())
        {
            std::thread::sleep(delay);
        }
    }
    require(
        bytes.len() as u64 == size
            && hex::encode(Sha256::digest(&bytes)) == pin["sha256"].as_str().ok_or("sha")?,
    )?;
    Ok(bytes)
}

pub(crate) fn captured_fixture_observation() -> Result<Value, Box<dyn Error>> {
    require(
        hex::encode(Sha256::digest(CORPUS.as_bytes()))
            == "9e033d551a968c46d982a3a46f5faf6cf96fc99f29b6c9ac6393bff88e9f4e3f",
    )?;
    let corpus: Value = serde_json::from_str(CORPUS)?;
    let pin = &corpus["cases"][2]["artifacts"]["saved"];
    let bytes = read_pin(pin)?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let ctx = write_context(&stored);
    let p = provider(&stored, &ctx)?;
    let source = p.import_actual_forms(stored.head, 4)?;
    let s = selection(&source, false)?;
    let c = prepare(&source, &p, &s)?;
    let output = c.with_verified_bytes(&p, 6, |v| v.to_vec())?;
    let bound = Product::read_source_bookmark_crossrefs(
        &output,
        DocumentId::parse("actual-form-document")?,
        Sha256::digest(&output).into(),
        SourceImportLimits::default(),
        limits()?,
    )?;
    require(
        bound.bindings().len() == 1
            && bound.bindings()[0].hyperlink
            && c.receipt().output.cached_values_preserved_not_refreshed
            && !c.receipt().execution_or_publication_authority,
    )?;
    require(
        read_pin(pin)? == bytes
            && stored.artifacts.download(&stored.owner, stored.result, 7)? == bytes,
    )?;
    require(
        stored
            .revisions
            .head(&stored.revision_context, stored.project, stored.branch)?
            == stored.head
            && stored
                .metadata
                .audit_events()?
                .iter()
                .filter(|v| v.event == "artifact.ingested")
                .count()
                == 2,
    )?;
    Ok(
        json!({"state":"stored_bookmark622_actual_source_fixture_not_native_CAS_or_route","source_sha256":pin["sha256"],"receipt":c.receipt(),"actual_native_started":false,"head_changed":false,"result_ingested":false,"source_overwritten":false,"route_qualified":false,"P09_complete":false}),
    )
}
#[test]
fn actual_captured_source_passes_real_acl_aead_candidate_delivery_without_head_or_result_write()
-> TestResult {
    captured_fixture_observation()?;
    Ok(())
}
