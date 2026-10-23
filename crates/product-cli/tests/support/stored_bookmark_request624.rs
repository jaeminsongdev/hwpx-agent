//! Strict public data -> owned source candidate. Memory repository/keys are fixtures.
use super::*;
use hwpx_agent_cli::form_product_request::stored_operations::{
    StoredProductOperationError as OE, StoredProductRequest as Entry,
    bookmark_commands::{
        BOOKMARK_COMMAND_PRODUCT_REQUEST_SCHEMA as SCHEMA, BookmarkCommandProductError as PE,
        BookmarkCommandProductLimits as Limits, BookmarkCommandRequestEntry,
    },
};
use revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::{
    lifecycle::{StoredJobObservation, StoredJobOutcome, StoredJobState},
    request_lookup::{
        StoredRequestLookup, StoredRequestLookupError, StoredRequestLookupRepository,
        StoredRequestObservation,
    },
};
fn budget() -> Result<Limits, Box<dyn Error>> {
    Ok(Limits::standard()?)
}
fn raw_request(
    f: &StoredFixture,
    source: &StoredImportedDocumentForms,
    new_target: bool,
) -> Result<Value, Box<dyn Error>> {
    let s = selection(source, new_target)?;
    Ok(
        json!({"schema_version":SCHEMA,"idempotency_key":"bookmark-request624-key","project_id":f.project.public_id(),
        "document_id":"actual-form-document","base_revision":f.head.revision_id().ok_or("head")?.public_id(),
        "expected_head_generation":f.head.generation(),"expected_source_package_sha256":hex::encode(source.receipt().imported.source_package_sha256),
        "plan_id":"bookmark-request624-plan","operation":{"kind":"change_bookmark_crossref_commands","changes":[{
            "reference_id":s.id,"expected_source_field_sha256":hex::encode(s.field),"expected_meaning_sha256":hex::encode(s.meaning),
            "target_id":s.target,"display":"page","hyperlink":true}]}}),
    )
}
fn wire(v: &Value) -> Result<Vec<u8>, Box<dyn Error>> {
    Ok(serde_json::to_vec(v)?)
}
fn original(f: &StoredFixture, bytes: &[u8]) -> TestResult {
    require(f.revisions.head(&f.revision_context, f.project, f.branch)? == f.head)?;
    require(f.artifacts.download(&f.owner, f.result, 20)? == bytes)?;
    require(
        f.metadata
            .audit_events()?
            .iter()
            .filter(|v| v.event == "artifact.ingested")
            .count()
            == 2,
    )
}
pub(crate) fn observation() -> Result<Value, Box<dyn Error>> {
    require(
        hex::encode(Sha256::digest(CORPUS.as_bytes()))
            == "9e033d551a968c46d982a3a46f5faf6cf96fc99f29b6c9ac6393bff88e9f4e3f",
    )?;
    let corpus: Value = serde_json::from_str(CORPUS)?;
    let pin = &corpus["cases"][2]["artifacts"]["saved"];
    let bytes = read_pin(pin)?;
    let f = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let ctx = write_context(&f);
    let p = provider(&f, &ctx)?;
    let raw = {
        let source = p.import_actual_forms(f.head, 4)?;
        wire(&raw_request(&f, &source, false)?)?
    };
    // Discovery source is dropped before preparation; the product owns its source/output.
    let operation = Entry::prepare_json(&p, &raw, None, 5)?;
    let product = operation.as_bookmark_commands().ok_or("bookmark variant")?;
    let output = operation.with_verified_bytes(&p, None, 6, |v| v.to_vec())?;
    let bound = Product::read_source_bookmark_crossrefs(
        &output,
        DocumentId::parse("actual-form-document")?,
        Sha256::digest(&output).into(),
        SourceImportLimits::default(),
        limits()?,
    )?;
    require(bound.bindings().len() == 1 && bound.bindings()[0].hyperlink)?;
    require(
        product.verify(&p, 7)? == product.receipt() && product.compiled().operations().len() == 1,
    )?;
    require(
        operation
            .require_current_product_route(&p, None, 8)
            .is_err(),
    )?;
    let lookup = Entry::prepare_bookmark_commands_lookup_json(&p, &raw, budget()?)?;
    require(
        hex::encode(lookup.canonical_request_sha256())
            == product.receipt().canonical_request_sha256
            && hex::encode(lookup.scoped_request_sha256())
                == product.receipt().scoped_request_sha256,
    )?;
    original(&f, &bytes)?;
    require(read_pin(pin)? == bytes)?;
    Ok(
        json!({"state":"bookmark_request624_actual_owned_common_dispatch_not_native_CAS_or_route","source_sha256":pin["sha256"],
        "receipt":product.receipt(),"actual_native_started":false,"head_changed":false,"result_ingested":false,
        "source_overwritten":false,"route_qualified":false,"idempotency_claimed":false,"P09_complete":false}),
    )
}
#[test]
fn actual_captured_common_request_owns_source_and_delivers_compiled_candidate_without_publish()
-> TestResult {
    observation()?;
    Ok(())
}
#[test]
fn standalone_and_common_dispatch_match_original_compiler_bytes_receipts_and_hash_only_diagnostics()
-> TestResult {
    let bytes = sample()?;
    let f = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let ctx = write_context(&f);
    let p = provider(&f, &ctx)?;
    let raw = {
        let source = p.import_actual_forms(f.head, 4)?;
        wire(&raw_request(&f, &source, true)?)?
    };
    let standalone = Entry::prepare_bookmark_commands_json(&p, &raw, budget()?, 5)?;
    let common = Entry::prepare_json(&p, &raw, None, 6)?;
    let product = common.as_bookmark_commands().ok_or("variant")?;
    assert_eq!(standalone.compiled(), product.compiled());
    assert_eq!(standalone.receipt(), product.receipt());
    assert_eq!(
        standalone.receipt().raw_request_sha256,
        hex::encode(Sha256::digest(&raw))
    );
    assert_eq!(
        standalone.with_verified_bytes(&p, 7, |v| v.to_vec())?,
        common.with_verified_bytes(&p, None, 8, |v| v.to_vec())?
    );
    assert!(
        !product.receipt().idempotency_key_claimed
            && !product.receipt().execution_or_publication_authority
    );
    for value in [
        serde_json::to_string(product.receipt())?,
        String::from_utf8(product.compiled().canonical_json()?)?,
        format!("{common:?}"),
    ] {
        for secret in [
            "private-old",
            "private-new",
            "private-cache",
            "原文",
            "?private",
        ] {
            assert!(!value.contains(secret));
        }
    }
    assert!(
        common
            .with_verified_preview_json(&p, None, 9, |_| ())
            .is_err()
    );
    assert!(common.require_current_product_route(&p, None, 10).is_err());
    original(&f, &bytes)
}
#[test]
fn strict_shapes_unknown_duplicate_hash_boolean_display_and_size_errors_reject_before_source_reads()
-> TestResult {
    let bytes = sample()?;
    let f = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let ctx = write_context(&f);
    let revisions = RevisionService::new(HeadFault {
        inner: f.revisions.repository().clone(),
        reads: AtomicUsize::new(0),
        at: AtomicUsize::new(0),
        fail: false,
        hook: None,
    });
    let p = StoredFormProvider::bind(
        &f.artifacts,
        &revisions,
        &ctx,
        &f.revision_context,
        f.project,
        f.branch,
        DocumentId::parse("actual-form-document")?,
    )?;
    let source = p.import_actual_forms(f.head, 4)?;
    let value = raw_request(&f, &source, true)?;
    revisions.repository().arm(0);
    let audits = f.metadata.audit_events()?.len();
    for variant in 0..24 {
        let mut v = value.clone();
        match variant {
            0 => v["unknown"] = true.into(),
            1 => v["approved"] = true.into(),
            2 => v["operation"]["Command"] = "RAW_FORBIDDEN".into(),
            3 => v["operation"]["kind"] = "crossref_insert".into(),
            4 => v["operation"]["changes"][0]["target_name"] = "RAW_FORBIDDEN".into(),
            5 => v["operation"]["changes"][0]["display"] = "unknown".into(),
            6 => v["operation"]["changes"][0]["hyperlink"] = 1.into(),
            7 => v["operation"]["changes"][0]["expected_meaning_sha256"] = "A".repeat(64).into(),
            8 => v["expected_source_package_sha256"] = "bad".into(),
            9 => v["expected_head_generation"] = 0.into(),
            10 => v["expected_head_generation"] = u64::MAX.into(),
            11 => v["operation"]["changes"] = json!([]),
            12 => {
                let duplicate = v["operation"]["changes"][0].clone();
                v["operation"]["changes"]
                    .as_array_mut()
                    .ok_or("changes")?
                    .push(duplicate);
            }
            13 => {
                v.as_object_mut().ok_or("object")?.remove("idempotency_key");
            }
            14 => v["base_revision"] = "not-service-revision".into(),
            15 => v = json!([]),
            16 => {
                v["operation"] = json!([
                    "change_bookmark_crossref_commands",
                    v["operation"]["changes"].clone()
                ])
            }
            17 => v["operation"]["changes"] = json!({}),
            18 => v["operation"]["changes"][0] = json!([]),
            19 => v["operation"]["changes"][0]["target_id"] = json!({"name":"RAW_FORBIDDEN"}),
            20 => v["operation"]["changes"][0]["display"] = json!(null),
            21 => {
                v["operation"]["changes"][0]
                    .as_object_mut()
                    .ok_or("change")?
                    .remove("hyperlink");
            }
            22 => v["schema_version"] = "future-schema".into(),
            _ => {
                v["operation"]["changes"][0]["expected_source_field_sha256"] = "0".repeat(63).into()
            }
        }
        let raw = wire(&v)?;
        assert!(
            Entry::prepare_bookmark_commands_json(&p, &raw, budget()?, 5).is_err(),
            "strict variant {variant}"
        );
        assert!(
            Entry::prepare_bookmark_commands_lookup_json(&p, &raw, budget()?).is_err(),
            "lookup variant {variant}"
        );
        assert!(
            Entry::prepare_json(&p, &raw, None, 5).is_err(),
            "common variant {variant}"
        );
    }
    let valid = String::from_utf8(wire(&value)?)?;
    for raw in [
        format!(
            "{{\"schema_version\":\"{SCHEMA}\",{}",
            valid.trim_start_matches('{')
        )
        .into_bytes(),
        valid
            .replace(
                "\"hyperlink\":true",
                "\"hyperlink\":true,\"hyperlink\":false",
            )
            .into_bytes(),
        format!("{valid} null").into_bytes(),
        vec![b' '; 2 * 1024 * 1024 + 1],
    ] {
        assert!(Entry::prepare_bookmark_commands_json(&p, &raw, budget()?, 5).is_err());
        assert!(Entry::prepare_json(&p, &raw, None, 5).is_err());
    }
    assert_eq!(revisions.repository().reads.load(Ordering::SeqCst), 0);
    assert_eq!(f.metadata.audit_events()?.len(), audits);
    Ok(())
}
#[test]
fn stale_scope_head_source_field_meaning_or_target_cannot_prepare_owned_output() -> TestResult {
    let bytes = sample()?;
    let f = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let ctx = write_context(&f);
    let p = provider(&f, &ctx)?;
    let source = p.import_actual_forms(f.head, 4)?;
    let value = raw_request(&f, &source, true)?;
    let read = f.provider()?;
    for variant in 0..8 {
        let mut v = value.clone();
        match variant {
            0 => v["project_id"] = revision_service::ProjectId::generate().public_id().into(),
            1 => v["document_id"] = "foreign-document".into(),
            2 => v["base_revision"] = revision_service::RevisionId::generate().public_id().into(),
            3 => v["expected_head_generation"] = 2.into(),
            4 => v["expected_source_package_sha256"] = "0".repeat(64).into(),
            5 => {
                v["operation"]["changes"][0]["expected_source_field_sha256"] = "0".repeat(64).into()
            }
            6 => v["operation"]["changes"][0]["expected_meaning_sha256"] = "0".repeat(64).into(),
            _ => v["operation"]["changes"][0]["target_id"] = "missing-bookmark-target".into(),
        }
        assert!(
            Entry::prepare_bookmark_commands_json(&p, &wire(&v)?, budget()?, 5).is_err(),
            "binding {variant}"
        );
    }
    assert!(Entry::prepare_json(&read, &wire(&value)?, None, 5).is_err());
    original(&f, &bytes)
}
#[test]
fn canonical_lookup_ignores_json_format_but_binds_every_semantic_option_and_provider_scope()
-> TestResult {
    let bytes = sample()?;
    let f = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let ctx = write_context(&f);
    let p = provider(&f, &ctx)?;
    let source = p.import_actual_forms(f.head, 4)?;
    let value = raw_request(&f, &source, true)?;
    let a = Entry::prepare_bookmark_commands_lookup_json(&p, &wire(&value)?, budget()?)?;
    let b = Entry::prepare_bookmark_commands_lookup_json(
        &p,
        &serde_json::to_vec_pretty(&value)?,
        budget()?,
    )?;
    assert_eq!(a.canonical_request_sha256(), b.canonical_request_sha256());
    assert_eq!(a.scoped_request_sha256(), b.scoped_request_sha256());
    for variant in 0..4 {
        let mut v = value.clone();
        match variant {
            0 => v["operation"]["changes"][0]["hyperlink"] = false.into(),
            1 => v["operation"]["changes"][0]["display"] = "content".into(),
            2 => v["plan_id"] = "different-plan".into(),
            _ => v["idempotency_key"] = "different-key".into(),
        }
        let q = Entry::prepare_bookmark_commands_lookup_json(&p, &wire(&v)?, budget()?)?;
        assert_ne!(a.canonical_request_sha256(), q.canonical_request_sha256());
        assert_ne!(a.scoped_request_sha256(), q.scoped_request_sha256());
    }
    let foreign = StoredFormProvider::bind(
        &f.artifacts,
        &f.revisions,
        &ctx,
        &f.revision_context,
        f.project,
        BranchId::generate(),
        DocumentId::parse("actual-form-document")?,
    )?;
    let q = Entry::prepare_bookmark_commands_lookup_json(&foreign, &wire(&value)?, budget()?)?;
    assert_eq!(a.canonical_request_sha256(), q.canonical_request_sha256());
    assert_ne!(a.scoped_request_sha256(), q.scoped_request_sha256());
    Ok(())
}
struct LookupModel {
    inner: InMemoryRevisionRepository,
    mode: u8,
    reads: AtomicUsize,
    lookups: AtomicUsize,
    commits: AtomicUsize,
}
impl RevisionRepository for LookupModel {
    fn authorize_context(&self, c: &RevisionRequestContext) -> Result<(), RevisionError> {
        self.inner.authorize_context(c)
    }
    fn head(
        &self,
        t: TenantId,
        p: revision_service::ProjectId,
        b: BranchId,
    ) -> Result<RevisionHead, RevisionError> {
        self.reads.fetch_add(1, Ordering::SeqCst);
        if self.mode == 0 {
            self.inner.head(t, p, b)
        } else {
            Err(RevisionError::RepositoryFailure)
        }
    }
    fn node(
        &self,
        t: TenantId,
        p: revision_service::ProjectId,
        r: revision_service::RevisionId,
    ) -> Result<RevisionNode, RevisionError> {
        self.reads.fetch_add(1, Ordering::SeqCst);
        if self.mode == 0 {
            self.inner.node(t, p, r)
        } else {
            Err(RevisionError::RepositoryFailure)
        }
    }
    fn compare_and_swap(
        &self,
        _: &RevisionRequestContext,
        _: &RevisionCommitRequest,
    ) -> Result<CommitOutcome, RevisionError> {
        self.commits.fetch_add(1, Ordering::SeqCst);
        Err(RevisionError::InvalidRequest)
    }
}
impl StoredRequestLookupRepository for LookupModel {
    fn observe_request(
        &self,
        c: &RevisionRequestContext,
        q: &StoredRequestLookup,
    ) -> Result<StoredRequestObservation, StoredRequestLookupError> {
        self.authorize_context(c)?;
        self.lookups.fetch_add(1, Ordering::SeqCst);
        match self.mode {
            0 => Ok(StoredRequestObservation::NotObserved),
            1 => Ok(StoredRequestObservation::Existing(
                StoredJobObservation::observed(
                    StoredJobOutcome::Replay,
                    q.job_id(),
                    StoredJobState::InProgress,
                    1,
                    1,
                    None,
                    None,
                    None,
                    None,
                )?,
            )),
            2 => Err(StoredRequestLookupError::KeyConflict),
            3 => Err(RevisionError::CommitOutcomeUnknown.into()),
            _ => Err(RevisionError::RepositoryFailure.into()),
        }
    }
}
#[test]
fn existing_or_uncertain_lookup_never_reads_source_compiles_or_claims() -> TestResult {
    let bytes = sample()?;
    let f = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let ctx = write_context(&f);
    let p = provider(&f, &ctx)?;
    let source = p.import_actual_forms(f.head, 4)?;
    let raw = wire(&raw_request(&f, &source, true)?)?;
    for mode in 1..5 {
        let revisions = RevisionService::new(LookupModel {
            inner: f.revisions.repository().clone(),
            mode,
            reads: AtomicUsize::new(0),
            lookups: AtomicUsize::new(0),
            commits: AtomicUsize::new(0),
        });
        let provider = StoredFormProvider::bind(
            &f.artifacts,
            &revisions,
            &ctx,
            &f.revision_context,
            f.project,
            f.branch,
            DocumentId::parse("actual-form-document")?,
        )?;
        let audits = f.metadata.audit_events()?.len();
        let entry = Entry::prepare_bookmark_commands_or_observe_json(&provider, &raw, budget()?, 5);
        if mode == 1 {
            assert!(matches!(
                entry,
                Ok(BookmarkCommandRequestEntry::Existing(_))
            ));
        } else {
            assert!(entry.is_err());
        }
        assert_eq!(revisions.repository().lookups.load(Ordering::SeqCst), 1);
        assert_eq!(revisions.repository().reads.load(Ordering::SeqCst), 0);
        assert_eq!(revisions.repository().commits.load(Ordering::SeqCst), 0);
        assert_eq!(f.metadata.audit_events()?.len(), audits);
    }
    Ok(())
}
#[test]
fn not_observed_prepares_owned_candidate_without_turning_observation_into_claim() -> TestResult {
    let bytes = sample()?;
    let f = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let ctx = write_context(&f);
    let p = provider(&f, &ctx)?;
    let source = p.import_actual_forms(f.head, 4)?;
    let raw = wire(&raw_request(&f, &source, true)?)?;
    let revisions = RevisionService::new(LookupModel {
        inner: f.revisions.repository().clone(),
        mode: 0,
        reads: AtomicUsize::new(0),
        lookups: AtomicUsize::new(0),
        commits: AtomicUsize::new(0),
    });
    let provider = StoredFormProvider::bind(
        &f.artifacts,
        &revisions,
        &ctx,
        &f.revision_context,
        f.project,
        f.branch,
        DocumentId::parse("actual-form-document")?,
    )?;
    let BookmarkCommandRequestEntry::Prepared(product) =
        Entry::prepare_bookmark_commands_or_observe_json(&provider, &raw, budget()?, 5)?
    else {
        return Err("prepared variant".into());
    };
    product.verify(&provider, 6)?;
    assert!(!product.receipt().idempotency_key_claimed);
    assert_eq!(revisions.repository().lookups.load(Ordering::SeqCst), 1);
    assert_eq!(revisions.repository().commits.load(Ordering::SeqCst), 0);
    original(&f, &bytes)
}
#[test]
fn owned_common_delivery_rechecks_acl_and_cannot_revive_after_regrant() -> TestResult {
    let bytes = sample()?;
    let f = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let ctx = write_context(&f);
    let p = provider(&f, &ctx)?;
    let raw = {
        let source = p.import_actual_forms(f.head, 4)?;
        wire(&raw_request(&f, &source, true)?)?
    };
    let operation = Entry::prepare_json(&p, &raw, None, 5)?;
    f.artifacts
        .set_permissions(&f.owner, f.result, f.reader.subject(), BTreeSet::new(), 6)?;
    let hit = AtomicBool::new(false);
    assert!(
        operation
            .with_verified_bytes(&p, None, 7, |_| hit.store(true, Ordering::SeqCst))
            .is_err()
    );
    assert!(!hit.load(Ordering::SeqCst));
    f.artifacts.set_permissions(
        &f.owner,
        f.result,
        f.reader.subject(),
        BTreeSet::from([ArtifactPermission::Read]),
        8,
    )?;
    assert!(
        operation
            .with_verified_bytes(&p, None, 9, |_| hit.store(true, Ordering::SeqCst))
            .is_err()
    );
    assert!(!hit.load(Ordering::SeqCst));
    original(&f, &bytes)
}
#[test]
fn old_https_no_repository_denial_and_unknown_schema_still_precede_head_access() -> TestResult {
    let bytes = sample()?;
    let f = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let ctx = write_context(&f);
    let revisions = RevisionService::new(HeadFault {
        inner: f.revisions.repository().clone(),
        reads: AtomicUsize::new(0),
        at: AtomicUsize::new(0),
        fail: false,
        hook: None,
    });
    let p = StoredFormProvider::bind(
        &f.artifacts,
        &revisions,
        &ctx,
        &f.revision_context,
        f.project,
        f.branch,
        DocumentId::parse("actual-form-document")?,
    )?;
    let source = p.import_actual_forms(f.head, 4)?;
    let mut v = raw_request(&f, &source, true)?;
    revisions.repository().arm(0);
    let audits = f.metadata.audit_events()?.len();
    v["schema_version"] = "hwpx-agent.product-https-target-request/v1".into();
    v["operation"]["kind"] = "change_https_targets".into();
    let change = v["operation"]["changes"][0]
        .as_object_mut()
        .ok_or("change")?;
    for key in ["target_id", "display", "hyperlink"] {
        change.remove(key);
    }
    change.insert(
        "target".into(),
        json!({"kind":"https","uri":"https://example.org/closed"}),
    );
    assert!(matches!(
        Entry::prepare_json(&p, &wire(&v)?, None, 5),
        Err(OE::PolicyRepositoryRequired)
    ));
    v["schema_version"] = "unknown-schema".into();
    assert!(Entry::prepare_json(&p, &wire(&v)?, None, 5).is_err());
    assert_eq!(revisions.repository().reads.load(Ordering::SeqCst), 0);
    assert_eq!(f.metadata.audit_events()?.len(), audits);
    Ok(())
}
#[test]
fn server_item_budget_is_checked_before_any_source_or_lookup_read() -> TestResult {
    let bytes = sample()?;
    let f = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let ctx = write_context(&f);
    let p = provider(&f, &ctx)?;
    let source = p.import_actual_forms(f.head, 4)?;
    let mut v = raw_request(&f, &source, true)?;
    let duplicate = v["operation"]["changes"][0].clone();
    v["operation"]["changes"]
        .as_array_mut()
        .ok_or("changes")?
        .push(duplicate);
    let mut limit = budget()?;
    let mut config = limit.auxiliary.config();
    config.items_per_kind = 1;
    limit.auxiliary = ReferenceAuxiliaryLimits::new(config)?;
    let audits = f.metadata.audit_events()?.len();
    assert!(matches!(
        Entry::prepare_bookmark_commands_json(&p, &wire(&v)?, limit, 5),
        Err(PE::Limit)
    ));
    assert!(matches!(
        Entry::prepare_bookmark_commands_lookup_json(&p, &wire(&v)?, limit),
        Err(PE::Limit)
    ));
    assert_eq!(f.metadata.audit_events()?.len(), audits);
    Ok(())
}
