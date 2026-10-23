use artifact_service::{
    ArtifactId, ArtifactKind, ContentDigest, ObjectKey, StorageState, SubjectDigest, TenantId,
};
use revision_service::{
    BranchId, CommitId, CommitOutcome, FullDocumentIrBinding, InMemoryRevisionRepository,
    ProjectId, RevisionCommitRequest, RevisionError, RevisionHead, RevisionId,
    RevisionRequestContext, RevisionService, RevisionValidationState,
};
use std::error::Error;
use uuid::Uuid;
type TestResult = Result<(), Box<dyn Error>>;

fn request() -> Result<RevisionCommitRequest, RevisionError> {
    RevisionCommitRequest::new(
        CommitId::generate(),
        ProjectId::generate(),
        BranchId::generate(),
        RevisionHead::empty(),
        RevisionId::generate(),
        vec![],
        ArtifactId::generate(),
        ArtifactId::generate(),
        Some(ArtifactId::generate()),
        ContentDigest::of(b"test-only-op"),
        RevisionValidationState::Verified,
        ContentDigest::of(b"test-only-validation"),
        ContentDigest::of(b"test-only-transaction"),
    )
}
fn binding() -> FullDocumentIrBinding {
    FullDocumentIrBinding {
        artifact_id: ArtifactId::generate(),
        artifact_sha256: ContentDigest::of(b"test-only-ir"),
        result_package_sha256: ContentDigest::of(b"test-only-package"),
        canonical_graph_sha256: ContentDigest::of(b"test-only-graph"),
    }
}

#[test]
fn old_wire_requests_have_no_new_field_and_keep_the_same_canonical_digest() -> TestResult {
    let old = request()?;
    let raw = serde_json::to_vec(&old)?;
    let value: serde_json::Value = serde_json::from_slice(&raw)?;
    assert!(value.get("full_document_ir").is_none());
    let restored: RevisionCommitRequest = serde_json::from_slice(&raw)?;
    assert!(old == restored);
    assert_eq!(restored.canonical_sha256()?, ContentDigest::of(&raw));
    assert_eq!(restored.full_document_ir(), None);
    Ok(())
}

#[test]
fn new_ir_link_is_canonical_strict_redacted_and_covered_by_cas_request_digest() -> TestResult {
    let old = request()?;
    let linked = old.clone().with_full_document_ir(binding())?;
    let raw = serde_json::to_vec(&linked)?;
    let restored: RevisionCommitRequest = serde_json::from_slice(&raw)?;
    assert!(linked == restored);
    assert_ne!(linked.canonical_sha256()?, old.canonical_sha256()?);
    assert_eq!(linked.full_document_ir(), restored.full_document_ir());
    let public = format!("{:?}", linked.full_document_ir());
    assert!(!public.contains("art_"));
    for path in ["extra", "artifact_sha256"] {
        let mut invalid: serde_json::Value = serde_json::from_slice(&raw)?;
        invalid["full_document_ir"][path] = serde_json::json!("INVALID");
        assert!(serde_json::from_value::<RevisionCommitRequest>(invalid).is_err());
    }
    Ok(())
}

#[test]
fn ir_artifact_must_not_alias_source_result_diff_or_an_existing_attachment() -> TestResult {
    let original = request()?;
    for alias in [
        original.source_artifact_id(),
        original.result_artifact_id(),
        original.semantic_diff_artifact_id().ok_or("diff")?,
    ] {
        let mut bind = binding();
        bind.artifact_id = alias;
        assert!(matches!(
            original.clone().with_full_document_ir(bind),
            Err(RevisionError::InvalidRequest)
        ));
        let mut raw = serde_json::to_value(&original)?;
        raw["full_document_ir"] = serde_json::to_value(bind)?;
        assert!(serde_json::from_value::<RevisionCommitRequest>(raw).is_err());
    }
    assert!(matches!(
        original
            .with_full_document_ir(binding())?
            .with_full_document_ir(binding()),
        Err(RevisionError::InvalidRequest)
    ));
    Ok(())
}

#[test]
fn real_cas_seals_ir_link_in_same_node_and_rejects_stale_metadata_commit() -> TestResult {
    let tenant = TenantId::new(Uuid::from_u128(6001))?;
    let context = RevisionRequestContext::new(
        tenant,
        SubjectDigest::from_authenticated_subject("test-only-ir-context")?,
    );
    let original = request()?;
    let bind = binding();
    let linked = original.clone().with_full_document_ir(bind)?;
    let repo = InMemoryRevisionRepository::default();
    repo.provision_stream(tenant, original.project_id(), original.branch_id())?;
    let service = RevisionService::new(repo);
    assert!(matches!(
        service.commit(&context, &linked)?,
        CommitOutcome::Committed(_)
    ));
    let node = service.node(&context, original.project_id(), original.new_revision_id())?;
    assert_eq!(node.full_document_ir(), Some(bind));
    assert!(node.sealed());
    assert!(matches!(
        service.commit(&context, &original)?,
        CommitOutcome::Conflict(_)
    ));
    assert_eq!(
        service
            .node(&context, original.project_id(), original.new_revision_id())?
            .full_document_ir(),
        Some(bind)
    );
    Ok(())
}

#[test]
fn document_ir_has_its_own_encrypted_object_namespace_and_preserves_old_kind_tags() -> TestResult {
    let tenant = TenantId::new(Uuid::from_u128(6002))?;
    let digest = ContentDigest::of(b"same-content");
    let ir = ObjectKey::for_artifact(
        tenant,
        ArtifactKind::DocumentIr,
        StorageState::Available,
        digest,
    )?;
    let result = ObjectKey::for_artifact(
        tenant,
        ArtifactKind::Result,
        StorageState::Available,
        digest,
    )?;
    assert_ne!(ir, result);
    assert_eq!(ir.as_str().split('/').nth(3), Some("document_ir"));
    assert_eq!(
        serde_json::to_string(&ArtifactKind::DocumentIr)?,
        "\"document_ir\""
    );
    assert_eq!(serde_json::to_string(&ArtifactKind::Source)?, "\"source\"");
    assert_eq!(serde_json::to_string(&ArtifactKind::Result)?, "\"result\"");
    assert_eq!(ObjectKey::parse(ir.as_str())?, ir);
    Ok(())
}
