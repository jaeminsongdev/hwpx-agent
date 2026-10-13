//! Typed registration against owned SQL20 + actual AEAD + original source; initial seed is synthetic.
//! Synthetic scanner/worker policy authority; NOT native/full product route qualification.
#[path = "../../hwpx-package/examples/document_import_form_policies_support/mod.rs"]
mod fixture;
mod stored_source_policy_postgres_probe {
    pub mod worker;
}
use artifact_service::{
    Aes256GcmKeyring, ArtifactDescriptor, ArtifactError, ArtifactId, ArtifactKind,
    ArtifactPermission, ArtifactScanner, ArtifactService, ArtifactServiceConfig, AuthScope,
    ContentDigest, DownloadSigner, FileName, IngestRequest, KeyReference, LocalEncryptedBlobStore,
    LocalPostgresConfig, LocalPostgresMetadataRepository, MediaType, RequestContext, ScanEvidence,
    ScanRequest, ScanVerdict, ScannerReference, ScannerSignatureVersion, SubjectDigest, TenantId,
};
use domain_ir::DocumentId;
use hwpx_agent_cli::form_stored_provider::{
    StoredFormProvider,
    actual_import::source_policy::{
        SOURCE_POLICY_MEDIA_TYPE, SOURCE_POLICY_PAYLOAD_SCHEMA, SourcePolicyBinding,
        postgres::PostgresSourcePolicyProvider,
    },
};
use hwpx_package::document_import::{
    ImportedSourcePackage, SourceImportLimits,
    forms::{
        ImportedDocumentForms,
        policies::{FormPolicySourceBinding, PolicyBoundDocumentForms},
    },
};
use revision_service::{
    BranchId, CommitId, CommitOutcome, ProjectId, RevisionCommitRequest, RevisionHead, RevisionId,
    RevisionRequestContext, RevisionService, RevisionValidationState,
    postgres::{
        LocalPostgresRevisionConfig, LocalPostgresRevisionRepository, RevisionCommitLease,
        source_form_policy::LocalPostgresSourcePolicyRepository,
    },
};
use serde_json::json;
use std::{collections::BTreeSet, env, error::Error};
use uuid::Uuid;
type Result<T> = std::result::Result<T, Box<dyn Error>>;
type Artifacts =
    ArtifactService<LocalPostgresMetadataRepository, LocalEncryptedBlobStore, FixtureScanner>;
fn id(n: u128) -> Uuid {
    Uuid::from_u128(n)
}
fn tenant() -> Result<TenantId> {
    Ok(TenantId::new(id(1))?)
}
fn project() -> Result<ProjectId> {
    Ok(ProjectId::parse(&format!("prj_{}", id(2).simple()))?)
}
fn branch(i: usize) -> Result<BranchId> {
    Ok(BranchId::parse(&format!(
        "brn_{}",
        id(100 + i as u128).simple()
    ))?)
}
fn revision(i: usize) -> Result<RevisionId> {
    Ok(RevisionId::parse(&format!(
        "rev_{}",
        id(200 + i as u128).simple()
    ))?)
}
fn subject() -> Result<SubjectDigest> {
    Ok(SubjectDigest::parse(&"a".repeat(64))?)
}
fn context() -> Result<RevisionRequestContext> {
    Ok(RevisionRequestContext::new(tenant()?, subject()?))
}
fn port() -> Result<u16> {
    Ok(env::var("P84_DB_PORT")?.parse()?)
}
fn revision_config() -> Result<LocalPostgresRevisionConfig> {
    Ok(LocalPostgresRevisionConfig::new(
        port()?,
        "postgres".into(),
        "p84_revision_app".into(),
        env::var("P84_REVISION_PASSWORD")?,
    )?)
}
fn artifact_config() -> Result<LocalPostgresConfig> {
    Ok(LocalPostgresConfig::new(
        port()?,
        "postgres".into(),
        "p84_artifact_app".into(),
        env::var("P84_ARTIFACT_PASSWORD")?,
    )?)
}
fn check(ok: bool) -> Result<()> {
    if ok {
        Ok(())
    } else {
        Err("P84_CHECK_DENIED".into())
    }
}
#[derive(Debug)]
struct FixtureScanner;
impl ArtifactScanner for FixtureScanner {
    fn scan(&self, _: ScanRequest<'_>) -> std::result::Result<ScanEvidence, ArtifactError> {
        Ok(ScanEvidence {
            verdict: ScanVerdict::Clean,
            engine: ScannerReference::parse("fixture.p84-not-real")?,
            signature_version: ScannerSignatureVersion::parse("fixture-84")?,
        })
    }
}
fn artifacts() -> Result<Artifacts> {
    let r = KeyReference::parse("fixture.p84-aes")?;
    Ok(ArtifactService::new(
        LocalPostgresMetadataRepository::connect_source_form_policy_schema20(
            &artifact_config()?,
            tenant()?,
        )?,
        LocalEncryptedBlobStore::create(env::var("P84_BLOB_ROOT")?, 32 * 1024 * 1024 + 16)?,
        FixtureScanner,
        Aes256GcmKeyring::new(r.clone(), [(r, [84; 32])])?,
        DownloadSigner::new(
            "https://fixture.example.test/p84",
            KeyReference::parse("fixture.p84-hmac")?,
            &[85; 32],
            60,
        )?,
        ArtifactServiceConfig::new(32 * 1024 * 1024, 60)?,
    ))
}
fn actor() -> Result<RequestContext> {
    Ok(RequestContext::new(
        tenant()?,
        subject()?,
        [
            AuthScope::DocumentRead,
            AuthScope::DocumentWrite,
            AuthScope::SecurityModify,
            AuthScope::ArtifactShare,
        ],
    ))
}
fn ingest(
    a: &Artifacts,
    c: &RequestContext,
    bytes: Vec<u8>,
    kind: ArtifactKind,
    media: &str,
    name: &str,
) -> Result<ArtifactDescriptor> {
    Ok(a.ingest(
        c,
        IngestRequest {
            bytes,
            kind,
            media_type: MediaType::parse(media)?,
            file_name: FileName::parse(name)?,
        },
        10,
    )?)
}
fn main() {
    if run().is_err() {
        eprintln!("P84_PROBE_FAILED");
        std::process::exit(2);
    }
}
fn run() -> Result<()> {
    let mode = env::var("P84_MODE")?;
    if mode == "admission_denied" {
        check(
            LocalPostgresMetadataRepository::connect_source_form_policy_schema20(
                &artifact_config()?,
                tenant()?,
            )
            .is_err(),
        )?;
        check(
            LocalPostgresSourcePolicyRepository::connect(&revision_config()?, context()?, None)
                .is_err(),
        )?;
        println!("{}", json!({"state":"pass","mode":mode,"checks":2}));
        return Ok(());
    }
    if mode == "revision_admission_denied" {
        check(
            LocalPostgresSourcePolicyRepository::connect(&revision_config()?, context()?, None)
                .is_err(),
        )?;
        println!("{}", json!({"state":"pass","mode":mode,"checks":1}));
        return Ok(());
    }
    // Preserve and expose legacy prefix compatibility; it is NOT exact schema20 admission.
    check(LocalPostgresMetadataRepository::connect(&artifact_config()?, tenant()?).is_ok())?;
    check(
        LocalPostgresRevisionRepository::connect(&revision_config()?, context()?, None).is_err(),
    )?;
    let a = artifacts()?;
    let actor = actor()?;
    let ctx = context()?;
    let repo =
        LocalPostgresSourcePolicyRepository::connect(&revision_config()?, ctx.clone(), None)?;
    let revisions = RevisionService::new(repo.revision_repository());
    let policy_provider = PostgresSourcePolicyProvider::new(repo);
    let (_, manifest) = fixture::fixture_manifest()?;
    let mut checks = 0;
    let mut receipts = Vec::new();
    let mut i = 0;
    for row in manifest["cases"].as_array().ok_or("P84_CASES")? {
        for kind in ["source", "output"] {
            let raw = fixture::fixture_bytes(row["case"].as_str().ok_or("P84_CASE")?, kind)?;
            let direct = ImportedDocumentForms::import(ImportedSourcePackage::import(
                &raw,
                DocumentId::parse("p84-policy-document")?,
                *ContentDigest::of(&raw).as_bytes(),
                SourceImportLimits::default(),
            )?)?;
            if mode == "seed" {
                seed_case(&a, &actor, &direct, raw, i)?;
                checks += 3;
            }
            let (count, receipt) =
                verify_case(&a, &actor, &revisions, &policy_provider, &direct, i, &mode)?;
            checks += count;
            if let Some(receipt) = receipt {
                receipts.push(receipt);
            }
            i += 1;
        }
    }
    check(i == 10)?;
    println!(
        "{}",
        json!({"schema":"hwpx-agent.p09-84-stored-policy-probe/v1","state":"pass","mode":mode,
        "checks":checks,"cases":i,"receipt_sha256":receipts,"native_executed":false,
        "real_scanner_or_issuer_qualified":false,"p09_complete":false})
    );
    Ok(())
}
fn seed_case(
    a: &Artifacts,
    actor: &RequestContext,
    direct: &ImportedDocumentForms,
    raw: Vec<u8>,
    i: usize,
) -> Result<()> {
    let prior = ingest(
        a,
        actor,
        format!("P84 SYNTHETIC PRIOR {i}").into_bytes(),
        ArtifactKind::Source,
        "application/octet-stream",
        "fixture-prior.bin",
    )?;
    let result = ingest(
        a,
        actor,
        raw,
        ArtifactKind::Result,
        "application/vnd.hancom.hwpx+zip",
        "original.hwpx",
    )?;
    let req = RevisionCommitRequest::new(
        CommitId::parse(&format!("cmt_{}", id(300 + i as u128).simple()))?,
        project()?,
        branch(i)?,
        RevisionHead::empty(),
        revision(i)?,
        vec![],
        prior.artifact_id,
        result.artifact_id,
        None,
        ContentDigest::of(format!("P84 fixture plan {i}").as_bytes()),
        RevisionValidationState::Verified,
        ContentDigest::of(b"P84 fixture validation, not native"),
        ContentDigest::of(format!("P84 JOB RECEIPT {i}").as_bytes()),
    )?;
    let lease =
        stored_source_policy_postgres_probe::worker::receive(&req, i, prior.sha256, result.sha256)?;
    let ctx = context()?;
    let writer = LocalPostgresSourcePolicyRepository::connect(
        &revision_config()?,
        ctx.clone(),
        Some(RevisionCommitLease::bind(lease, &req)?),
    )?;
    check(matches!(
        RevisionService::new(writer.revision_repository()).commit(&ctx, &req)?,
        CommitOutcome::Committed(_)
    ))?;
    let receipt = ingest(
        a,
        actor,
        format!("P84 JOB RECEIPT {i}").into_bytes(),
        ArtifactKind::Receipt,
        "application/json",
        "fixture-receipt.json",
    )?;
    stored_source_policy_postgres_probe::worker::complete(&req, lease, receipt.artifact_id)?;
    let binding = SourcePolicyBinding {
        tenant: tenant()?,
        project: project()?,
        branch: branch(i)?,
        document: direct.graph().document_id().clone(),
        source_revision: revision(i)?,
        source_head_generation: 1,
        source_result_artifact: result.artifact_id,
        source_package_sha256: result.sha256,
        source_provenance_sha256: ContentDigest::parse(&hex::encode(
            direct.receipt().source_provenance_sha256,
        ))?,
        observed_graph_sha256: ContentDigest::parse(&hex::encode(direct.receipt().graph_sha256))?,
        policy_version: id(400 + i as u128),
        policy_generation: 1,
        creator_subject: subject()?,
    };
    let policy = ingest(
        a,
        actor,
        serde_json::to_vec(&json!({"schema_version":SOURCE_POLICY_PAYLOAD_SCHEMA,
        "binding":binding,"policies":fixture::explicit_test_policies(direct)}))?,
        ArtifactKind::Evidence,
        SOURCE_POLICY_MEDIA_TYPE,
        "fixture-policy.json",
    )?;
    stored_source_policy_postgres_probe::worker::register(
        &binding,
        policy.artifact_id,
        policy.sha256,
    )
}
fn verify_case(
    a: &Artifacts,
    actor: &RequestContext,
    revisions: &RevisionService<LocalPostgresRevisionRepository>,
    policies: &PostgresSourcePolicyProvider,
    direct: &ImportedDocumentForms,
    i: usize,
    mode: &str,
) -> Result<(usize, Option<String>)> {
    let ctx = context()?;
    let head = RevisionHead::new(Some(revision(i)?), 1)?;
    let provider = StoredFormProvider::bind(
        a,
        revisions,
        actor,
        &ctx,
        project()?,
        branch(i)?,
        direct.graph().document_id().clone(),
    )?;
    let source = provider.import_actual_forms(head, 20)?;
    if mode == "denied" {
        check(
            source
                .bind_stored_policies(&provider, policies, 21)
                .is_err(),
        )?;
        return Ok((1, None));
    }
    let bound = source.bind_stored_policies(&provider, policies, 21)?;
    let original = PolicyBoundDocumentForms::bind(
        direct,
        &FormPolicySourceBinding::for_imported(direct),
        &fixture::explicit_test_policies(direct),
    )?;
    check(bound.state() == original.state() && bound.graph() == original.graph())?;
    check(bound.receipt().policy == *original.receipt())?;
    check(bound.verify(&provider, policies, 22)? == *bound.receipt())?;
    check(revisions.head(&ctx, project()?, branch(i)?)? == head)?;
    let receipt = ContentDigest::of(&serde_json::to_vec(bound.receipt())?).hex();
    if mode == "prepared_product" {
        return prepared_product(&provider, &source, &bound, policies, direct, &ctx, head);
    }
    if mode == "register_generated" {
        return register_generated(&provider, &source, &bound, policies, direct, &ctx);
    }
    if mode == "safety" {
        let artifact = bound.receipt().policy_artifact;
        a.set_permissions(
            actor,
            artifact,
            subject()?,
            BTreeSet::from([ArtifactPermission::Manage]),
            23,
        )?;
        check(bound.verify(&provider, policies, 24).is_err())?;
        a.set_permissions(
            actor,
            artifact,
            subject()?,
            BTreeSet::from([ArtifactPermission::Read, ArtifactPermission::Manage]),
            25,
        )?;
        check(bound.verify(&provider, policies, 26)? == *bound.receipt())?;
        let repo =
            LocalPostgresSourcePolicyRepository::connect(&revision_config()?, ctx.clone(), None)?;
        stored_source_policy_postgres_probe::worker::revoke(
            &repo,
            &ctx,
            project()?,
            branch(i)?,
            head,
        )?;
        check(bound.verify(&provider, policies, 27).is_err())?;
        check(
            source
                .bind_stored_policies(&provider, policies, 27)
                .is_err(),
        )?;
        return Ok((8, Some(receipt)));
    }
    Ok((4, Some(receipt)))
}
fn register_generated(
    provider: &StoredFormProvider<
        '_,
        LocalPostgresMetadataRepository,
        LocalEncryptedBlobStore,
        FixtureScanner,
        LocalPostgresRevisionRepository,
    >,
    source: &hwpx_agent_cli::form_stored_provider::actual_import::StoredImportedDocumentForms,
    previous: &hwpx_agent_cli::form_stored_provider::actual_import::source_policy::StoredSourceFormPolicies<'_>,
    policies: &PostgresSourcePolicyProvider,
    direct: &ImportedDocumentForms,
    ctx: &RevisionRequestContext,
) -> Result<(usize, Option<String>)> {
    use hwpx_agent_cli::form_stored_provider::actual_import::source_policy::registration::{
        PolicyRegistrationError, postgres::PostgresSourcePolicyRegistrar,
    };
    let registrar = PostgresSourcePolicyRegistrar::new(
        LocalPostgresSourcePolicyRepository::connect(&revision_config()?, ctx.clone(), None)?,
    );
    let prepared = source.prepare_policy_registration(
        provider,
        &fixture::explicit_test_policies(direct),
        1,
        28,
    )?;
    let registered = prepared.register(provider, &registrar, 29)?;
    check(
        registered.version.policy_generation == 2
            && registered.version.policy_version != previous.receipt().policy_version,
    )?;
    check(previous.verify(provider, policies, 30).is_err())?;
    check(matches!(
        prepared.register(provider, &registrar, 31),
        Err(PolicyRegistrationError::Repository)
    ))?;
    let current = source.bind_stored_policies(provider, policies, 32)?;
    check(
        current.receipt().policy_generation == 2
            && current.receipt().policy_artifact == registered.artifact
            && current.receipt().policy_raw_sha256 == registered.digest,
    )?;
    check(
        current.graph() == previous.graph()
            && current.state() == previous.state()
            && current.receipt().policy == registered.policy,
    )?;
    check(current.verify(provider, policies, 33)? == *current.receipt())?;
    Ok((
        10,
        Some(ContentDigest::of(&serde_json::to_vec(current.receipt())?).hex()),
    ))
}

fn prepared_product(
    provider: &StoredFormProvider<
        '_,
        LocalPostgresMetadataRepository,
        LocalEncryptedBlobStore,
        FixtureScanner,
        LocalPostgresRevisionRepository,
    >,
    source: &hwpx_agent_cli::form_stored_provider::actual_import::StoredImportedDocumentForms,
    previous: &hwpx_agent_cli::form_stored_provider::actual_import::source_policy::StoredSourceFormPolicies<'_>,
    policies: &PostgresSourcePolicyProvider,
    direct: &ImportedDocumentForms,
    ctx: &RevisionRequestContext,
    head: RevisionHead,
) -> Result<(usize, Option<String>)> {
    use domain_ir::{
        FormControlLimitConfig, FormControlLimits, FormDocumentStateDraft, LogicalId,
        form_input::{
            FORM_INPUT_SCHEMA_VERSION, FormInputAccessPolicy, FormInputOperation,
            FormInputRequestDraft,
        },
    };
    use hwpx_agent_cli::form_product_request::{
        FORM_PRODUCT_REQUEST_SCHEMA,
        stored::{StoredProductFormBindings, StoredProductFormRequest},
    };
    use hwpx_package::{NativeFormPackageLimits, native_form_value_output::NativeFormValueReader};
    let explicit = PolicyBoundDocumentForms::bind(
        direct,
        &FormPolicySourceBinding::for_imported(direct),
        &fixture::explicit_test_policies(direct),
    )?;
    let native = explicit.native_binding();
    let limits = FormControlLimits::new(FormControlLimitConfig::default())?;
    let version = previous.receipt().policy.source.clone();
    // Read the original current source through the unchanged authenticated artifact service.
    let a = artifacts()?;
    let raw = a.download(&actor()?, previous.receipt().imported.source_artifact, 34)?;
    let observed = NativeFormValueReader::read(
        &raw,
        native.map(),
        native.policies(),
        limits,
        NativeFormPackageLimits::default(),
    )?;
    let draft: FormDocumentStateDraft =
        serde_json::from_slice(&observed.state().canonical_json(limits)?)?;
    let access = FormInputAccessPolicy {
        document_protection_sha256: draft.document_protection_sha256,
        input_allowed: true,
    };
    let input = FormInputRequestDraft {
        schema_version: FORM_INPUT_SCHEMA_VERSION.into(),
        request_id: LogicalId::parse("P86-component-reset")?,
        expected_source_state_sha256: observed.state().canonical_sha256(limits)?,
        expected_document_flow_sha256: observed.native_v1().document_flow_sha256().into(),
        access: access.clone(),
        operation: FormInputOperation::ResetDefaults {
            targets: native
                .policies()
                .iter()
                .map(|p| p.identity.clone())
                .collect(),
        },
    };
    let envelope = serde_json::to_vec(&json!({"schema_version": FORM_PRODUCT_REQUEST_SCHEMA,
        "idempotency_key":"P86-component-fixture-key", "project_id":project()?.public_id(),
        "document_id":version.document_id, "base_revision":head.revision_id().ok_or("P86_HEAD")?.public_id(),
        "expected_head_generation":head.generation(), "expected_source_package_sha256":hex::encode(version.source_package_sha256),
        "plan_id":"P86-stored-policy-reset", "form_input":input}))?;
    let prepared = previous.prepare_product_json(provider, policies, &envelope, &access, 35)?;
    let original = StoredProductFormRequest::prepare_json(
        provider,
        &envelope,
        &StoredProductFormBindings {
            map: native.map(),
            policies: native.policies(),
            access: &access,
        },
        35,
    )?;
    check(prepared.candidate_bytes() == original.candidate_bytes())?;
    check(prepared.receipt().product == *original.receipt())?;
    check(prepared.verify(provider, policies, &access, 36)? == *prepared.receipt())?;
    check(
        prepared
            .require_current_product_route(provider, policies, &access, 36)
            .is_err(),
    )?;
    let (registration_checks, _) =
        register_generated(provider, source, previous, policies, direct, ctx)?;
    check(prepared.verify(provider, policies, &access, 37).is_err())?;
    check(
        previous
            .prepare_product_json(provider, policies, &envelope, &access, 37)
            .is_err(),
    )?;
    let latest = source.bind_stored_policies(provider, policies, 38)?;
    let current = latest.prepare_product_json(provider, policies, &envelope, &access, 39)?;
    check(current.candidate_bytes() == prepared.candidate_bytes())?;
    check(current.verify(provider, policies, &access, 40)? == *current.receipt())?;
    check(
        current
            .require_current_product_route(provider, policies, &access, 40)
            .is_err(),
    )?;
    check(
        current.receipt().policy.policy_generation == 2
            && current.receipt().policy.policy_version != prepared.receipt().policy.policy_version,
    )?;
    Ok((
        registration_checks + 10,
        Some(ContentDigest::of(&serde_json::to_vec(current.receipt())?).hex()),
    ))
}
