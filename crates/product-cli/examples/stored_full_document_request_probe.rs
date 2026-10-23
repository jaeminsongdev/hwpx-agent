//! Actual disposable `PostgreSQL` + encrypted filesystem product-library preparation acceptance.
//! Fixture scanner/whole caller IR/seed authorization are NOT native import or signed execution.
use artifact_service::{
    Aes256GcmKeyring, ArtifactDescriptor, ArtifactError, ArtifactKind, ArtifactMetadataRepository,
    ArtifactPermission, ArtifactScanner, ArtifactService, ArtifactServiceConfig, AuthScope,
    ContentDigest, DownloadSigner, EncryptedBlobStore, FileName, IngestRequest, KeyReference,
    LocalEncryptedBlobStore, LocalPostgresConfig, LocalPostgresMetadataRepository, MediaType,
    RequestContext, ScanEvidence, ScanRequest, ScanVerdict, ScannerReference,
    ScannerSignatureVersion, SubjectDigest, TenantId,
};
use domain_ir::{
    DocumentGraph, DocumentGraphDraft, DocumentGraphLimits, DocumentId, DrawingNode, Flow, Inline,
    LogicalId, Node, NodeCommon, ParagraphNode, PlanId, Properties, PropertyValue, Section,
};
use hwpx_agent_cli::{
    form_product_request::{
        FORM_PRODUCT_REQUEST_SCHEMA,
        stored::StoredProductFormBindings,
        stored_full_document::{
            StoredFullDocumentProductFormError, StoredFullDocumentProductFormRequest,
        },
    },
    form_stored_provider::{StoredFormProvider, full_document::DOCUMENT_IR_MEDIA_TYPE},
    form_value_operation::{FormOperationContext, FormOperationIdentity, FormOperationPreparation},
};
use revision_service::{
    BranchId, CommitId, FullDocumentIrBinding, ProjectId, RevisionCommitRequest, RevisionError,
    RevisionHead, RevisionId, RevisionRequestContext, RevisionService, RevisionValidationState,
    postgres::{LocalPostgresRevisionConfig, LocalPostgresRevisionRepository},
};
use serde_json::Value;
use std::{
    collections::BTreeSet,
    path::PathBuf,
    time::{SystemTime, UNIX_EPOCH},
};
use thiserror::Error;
use uuid::Uuid;

#[path = "support/stored_actual_import.rs"]
mod actual_import;
#[path = "support/stored_full_request_fixture.rs"]
mod fixture;
#[path = "support/stored_full_request_safety.rs"]
mod safety;
#[path = "support/stored_full_request_worker.rs"]
mod worker;
const CASES: [&str; 4] = [
    "five-kinds",
    "empty-text",
    "reset-defaults",
    "clear-selections",
];
type Result<T> = std::result::Result<T, Failure>;
type Artifacts =
    ArtifactService<LocalPostgresMetadataRepository, LocalEncryptedBlobStore, FixtureScanner>;
type Revisions = RevisionService<LocalPostgresRevisionRepository>;
#[derive(Debug, Error)]
enum Failure {
    #[error("fixture_rejected")]
    Fixture,
    #[error("database_rejected")]
    Database,
    #[error("artifact_rejected")]
    Artifact(#[from] ArtifactError),
    #[error("revision_rejected")]
    Revision(#[from] RevisionError),
    #[error("product_rejected")]
    Product(#[from] StoredFullDocumentProductFormError),
    #[error("json_rejected")]
    Json(#[from] serde_json::Error),
}
fn env(name: &str) -> Result<String> {
    std::env::var(name).map_err(|_| Failure::Fixture)
}
fn id(n: u128) -> Uuid {
    Uuid::from_u128(n)
}
fn db<T>(r: std::result::Result<T, postgres::Error>) -> Result<T> {
    r.map_err(|e| {
        eprintln!(
            "P65_DB_ERROR code={}",
            e.code().map_or("UNKNOWN", postgres::error::SqlState::code)
        );
        if let Some(name) = e
            .as_db_error()
            .and_then(postgres::error::DbError::constraint)
            && name.len() <= 80
            && name
                .bytes()
                .all(|c| c.is_ascii_lowercase() || c.is_ascii_digit() || c == b'_')
        {
            eprintln!("P65_DB_CONSTRAINT name={name}");
        }
        Failure::Database
    })
}
fn phase<T>(name: &'static str, result: Result<T>) -> Result<T> {
    result.inspect_err(|_| eprintln!("P65_PHASE_FAILED phase={name}"))
}
fn config_port() -> Result<u16> {
    env("P65_DB_PORT")?.parse().map_err(|_| Failure::Fixture)
}
fn context() -> Result<RevisionRequestContext> {
    Ok(RevisionRequestContext::new(
        TenantId::new(id(1))?,
        SubjectDigest::parse(&"a".repeat(64))?,
    ))
}
fn revision_config() -> Result<LocalPostgresRevisionConfig> {
    Ok(LocalPostgresRevisionConfig::new(
        config_port()?,
        "postgres".into(),
        "p09_revision_app".into(),
        env("P65_REVISION_PASSWORD")?,
    )?)
}
fn now() -> Result<u64> {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .map_err(|_| Failure::Fixture)
}
fn graph(
    form: &fixture::Fixture,
    raw: &[u8],
    access: &domain_ir::form_input::FormInputAccessPolicy,
) -> Result<DocumentGraph> {
    let op = FormOperationPreparation::prepare_json(
        &FormOperationContext::bind(&form.source, &form.map, &form.policies)
            .map_err(|_| Failure::Fixture)?,
        FormOperationIdentity::new(
            DocumentId::parse("actual-form-document").map_err(|_| Failure::Fixture)?,
            domain_ir::RevisionId::parse("test-only-reference-revision")
                .map_err(|_| Failure::Fixture)?,
            PlanId::parse("test-only-reference-plan").map_err(|_| Failure::Fixture)?,
        )
        .map_err(|_| Failure::Fixture)?,
        raw,
        access,
    )
    .map_err(|_| Failure::Fixture)?;
    let mut draft = DocumentGraphDraft::new(
        DocumentId::parse("actual-form-document").map_err(|_| Failure::Fixture)?,
        vec![Section {
            section_id: LogicalId::parse("caller-full-section").map_err(|_| Failure::Fixture)?,
            properties: Properties::new(),
            master_pages: vec![],
            headers_footers: vec![],
            body: Flow {
                children: vec![
                    Node::Paragraph(ParagraphNode {
                        common: NodeCommon::new(
                            LogicalId::parse("keep-paragraph").map_err(|_| Failure::Fixture)?,
                        ),
                        inlines: vec![Inline::Text {
                            text: "test-only caller paragraph".into(),
                        }],
                        paragraph_properties: Properties::new(),
                    }),
                    Node::Drawing(DrawingNode {
                        common: NodeCommon::new(
                            LogicalId::parse("keep-drawing").map_err(|_| Failure::Fixture)?,
                        ),
                        resource_id: None,
                        children: Flow {
                            children: op.selection_projection().sections()[0]
                                .body
                                .children
                                .clone(),
                        },
                        properties: Properties::new(),
                    }),
                ],
            },
        }],
    );
    draft.source_profile = Some(
        LogicalId::parse("test-only-caller-graph-not-native-import")
            .map_err(|_| Failure::Fixture)?,
    );
    draft
        .metadata
        .insert("keep_metadata", PropertyValue::Integer(7));
    DocumentGraph::from_draft(draft, DocumentGraphLimits::default()).map_err(|_| Failure::Fixture)
}
#[derive(Debug)]
struct FixtureScanner {
    allowed: Vec<(ArtifactKind, ContentDigest)>,
}
impl ArtifactScanner for FixtureScanner {
    fn scan(&self, r: ScanRequest<'_>) -> std::result::Result<ScanEvidence, ArtifactError> {
        if !self.allowed.contains(&(r.kind, ContentDigest::of(r.bytes))) {
            return Err(ArtifactError::ScanNotClean);
        }
        Ok(ScanEvidence {
            engine: ScannerReference::parse("scanner.p65-fixture-only")?,
            signature_version: ScannerSignatureVersion::parse("not-native-v1")?,
            verdict: ScanVerdict::Clean,
        })
    }
}
struct Input {
    label: &'static str,
    form: fixture::Fixture,
    expected: Vec<u8>,
    raw: Vec<u8>,
    access: domain_ir::form_input::FormInputAccessPolicy,
    graph: DocumentGraph,
}
fn inputs() -> Result<Vec<Input>> {
    CASES
        .into_iter()
        .map(|label| {
            let (form, expected) = fixture::matrix(label).map_err(|_| Failure::Fixture)?;
            let (raw, access) =
                fixture::matrix_request(label, &form).map_err(|_| Failure::Fixture)?;
            let graph = graph(&form, &raw, &access)?;
            Ok(Input {
                label,
                form,
                expected,
                raw,
                access,
                graph,
            })
        })
        .collect()
}
fn prior(label: &str) -> Vec<u8> {
    format!("P65 synthetic prior source metadata {label}, NOT native input lineage").into_bytes()
}
fn receipt(label: &str) -> Vec<u8> {
    format!("P65 synthetic baseline receipt {label}, NOT signed form execution").into_bytes()
}
fn service(
    inputs: &[Input],
    key: u8,
) -> Result<(
    Artifacts,
    LocalPostgresMetadataRepository,
    LocalEncryptedBlobStore,
)> {
    let tenant = TenantId::new(id(1))?;
    let cfg = LocalPostgresConfig::new(
        config_port()?,
        "postgres".into(),
        "p65_artifact_app".into(),
        env("P65_ARTIFACT_PASSWORD")?,
    )?;
    let metadata =
        LocalPostgresMetadataRepository::connect_diagnosed(&cfg, tenant).map_err(|e| {
            eprintln!("P65_CONNECT_FAILED stage={}", e.stage().code());
            Failure::Artifact(e.into_error())
        })?;
    let root = PathBuf::from(env("P65_BLOB_ROOT")?);
    if !root.is_absolute() {
        return Err(Failure::Fixture);
    }
    let blobs = LocalEncryptedBlobStore::create(root, 32 * 1024 * 1024 + 16)?;
    let mut allowed = vec![];
    for input in inputs {
        for (kind, bytes) in [
            (ArtifactKind::Source, prior(input.label)),
            (ArtifactKind::Result, input.form.source.clone()),
            (
                ArtifactKind::DocumentIr,
                input.graph.canonical_json().map_err(|_| Failure::Fixture)?,
            ),
            (ArtifactKind::Receipt, receipt(input.label)),
        ] {
            allowed.push((kind, ContentDigest::of(&bytes)));
        }
    }
    let keyref = KeyReference::parse("kms.p65-synthetic")?;
    let artifacts = ArtifactService::new(
        metadata.clone(),
        blobs.clone(),
        FixtureScanner { allowed },
        Aes256GcmKeyring::new(keyref.clone(), [(keyref, [key; 32])])?,
        DownloadSigner::new(
            "https://artifact.invalid/v1/download",
            KeyReference::parse("hmac.p65-synthetic")?,
            &[65; 32],
            60,
        )?,
        ArtifactServiceConfig::new(32 * 1024 * 1024, 60)?,
    );
    Ok((artifacts, metadata, blobs))
}
fn read_service() -> Result<Revisions> {
    let ctx = context()?;
    let repo = LocalPostgresRevisionRepository::connect_diagnosed(&revision_config()?, ctx, None)
        .map_err(|e| {
        eprintln!("P65_CONNECT_FAILED stage={}", e.stage().code());
        Failure::Revision(e.into_error())
    })?;
    Ok(RevisionService::new(repo))
}
fn owner() -> Result<RequestContext> {
    Ok(RequestContext::new(
        TenantId::new(id(1))?,
        SubjectDigest::parse(&"b".repeat(64))?,
        [
            AuthScope::DocumentRead,
            AuthScope::DocumentWrite,
            AuthScope::ArtifactShare,
            AuthScope::SecurityModify,
        ],
    ))
}
fn reader() -> Result<RequestContext> {
    Ok(RequestContext::new(
        TenantId::new(id(1))?,
        SubjectDigest::parse(&"a".repeat(64))?,
        [AuthScope::DocumentRead],
    ))
}
fn project() -> Result<ProjectId> {
    Ok(ProjectId::parse(&format!("prj_{}", id(2).simple()))?)
}
fn branch(case: u8) -> Result<BranchId> {
    Ok(BranchId::parse(&format!(
        "brn_{}",
        id(100 + u128::from(case)).simple()
    ))?)
}
fn revision(case: u8) -> Result<RevisionId> {
    Ok(RevisionId::parse(&format!(
        "rev_{}",
        id(200 + u128::from(case)).simple()
    ))?)
}
fn request(input: &Input, case: u8) -> Result<Vec<u8>> {
    Ok(serde_json::to_vec(
        &serde_json::json!({"schema_version":FORM_PRODUCT_REQUEST_SCHEMA,
    "idempotency_key":format!("p65-synthetic-request-{}",input.label),"project_id":project()?.public_id(),"document_id":"actual-form-document",
    "base_revision":revision(case)?.public_id(),"expected_head_generation":1,"expected_source_package_sha256":ContentDigest::of(&input.form.source).hex(),
    "plan_id":"stored-full-document-plan","form_input":serde_json::from_slice::<Value>(&input.raw)?}),
    )?)
}
fn ingest(artifacts: &Artifacts, bytes: Vec<u8>, kind: ArtifactKind) -> Result<ArtifactDescriptor> {
    let media = if kind == ArtifactKind::DocumentIr {
        DOCUMENT_IR_MEDIA_TYPE
    } else {
        "application/octet-stream"
    };
    let value = artifacts.ingest(
        &owner()?,
        IngestRequest {
            bytes,
            kind,
            media_type: MediaType::parse(media)?,
            file_name: FileName::parse("p65-owned-fixture.bin")?,
        },
        now()?,
    )?;
    artifacts.set_permissions(
        &owner()?,
        value.artifact_id,
        reader()?.subject(),
        BTreeSet::from([ArtifactPermission::Read]),
        now()?,
    )?;
    Ok(value)
}
#[derive(Default)]
struct Probe {
    checks: Vec<(&'static str, &'static str)>,
    receipts: Vec<String>,
    candidates: Vec<String>,
}
impl Probe {
    fn check(&mut self, label: &'static str, name: &'static str, ok: bool) -> Result<()> {
        if !ok {
            eprintln!("P65_CHECK_FAILED check={name}");
            return Err(Failure::Fixture);
        }
        self.checks.push((label, name));
        Ok(())
    }
}
fn seed(p: &mut Probe, artifacts: &Artifacts, values: &[Input]) -> Result<()> {
    for (index, input) in values.iter().enumerate() {
        let case = u8::try_from(index).map_err(|_| Failure::Fixture)?;
        let source = ingest(artifacts, prior(input.label), ArtifactKind::Source)?;
        let result = ingest(artifacts, input.form.source.clone(), ArtifactKind::Result)?;
        let ir = ingest(
            artifacts,
            input.graph.canonical_json().map_err(|_| Failure::Fixture)?,
            ArtifactKind::DocumentIr,
        )?;
        let receipt = ingest(artifacts, receipt(input.label), ArtifactKind::Receipt)?;
        p.check(
            input.label,
            "baseline_artifacts_ingested",
            result.sha256 == ContentDigest::of(&input.form.source)
                && ir.sha256
                    == ContentDigest::of(
                        &input.graph.canonical_json().map_err(|_| Failure::Fixture)?,
                    ),
        )?;
        let req = RevisionCommitRequest::new(
            CommitId::generate(),
            project()?,
            branch(case)?,
            RevisionHead::empty(),
            revision(case)?,
            vec![],
            source.artifact_id,
            result.artifact_id,
            None,
            ContentDigest::of(b"p65 synthetic baseline operation"),
            RevisionValidationState::Verified,
            ContentDigest::of(b"p65 synthetic validation"),
            receipt.sha256,
        )?
        .with_full_document_ir(FullDocumentIrBinding {
            artifact_id: ir.artifact_id,
            artifact_sha256: ir.sha256,
            result_package_sha256: result.sha256,
            canonical_graph_sha256: ContentDigest::parse(&hex::encode(
                input
                    .graph
                    .canonical_sha256()
                    .map_err(|_| Failure::Fixture)?,
            ))?,
        })?;
        worker::commit(&req, case, &source.sha256.hex(), receipt.artifact_id)?;
        let node = read_service()?.node(&context()?, project()?, revision(case)?)?;
        p.check(
            input.label,
            "real_authorized_sealed_root",
            node.sealed() && node.full_document_ir() == req.full_document_ir(),
        )?;
    }
    Ok(())
}
fn verify(
    p: &mut Probe,
    artifacts: &Artifacts,
    metadata: &LocalPostgresMetadataRepository,
    blobs: &LocalEncryptedBlobStore,
    values: &[Input],
) -> Result<()> {
    let revisions = read_service()?;
    let ctx = context()?;
    let reader = reader()?;
    for (index, input) in values.iter().enumerate() {
        let case = u8::try_from(index).map_err(|_| Failure::Fixture)?;
        let provider = StoredFormProvider::bind(
            artifacts,
            &revisions,
            &reader,
            &ctx,
            project()?,
            branch(case)?,
            DocumentId::parse("actual-form-document").map_err(|_| Failure::Fixture)?,
        )
        .map_err(|_| Failure::Fixture)?;
        let bindings = StoredProductFormBindings {
            map: &input.form.map,
            policies: &input.form.policies,
            access: &input.access,
        };
        let before = metadata
            .audit_events()?
            .iter()
            .filter(|e| e.event == "artifact.ingested" || e.event == "artifact.ingest.deduplicated")
            .count();
        let prepared = StoredFullDocumentProductFormRequest::prepare_json(
            &provider,
            &request(input, case)?,
            &bindings,
            now()?,
        )?;
        p.check(
            input.label,
            "strict_request_whole_output",
            prepared.candidate_bytes() == input.expected,
        )?;
        p.check(
            input.label,
            "full_graph_digest_plan",
            prepared.compiled_plan().base_graph_sha256()
                == input
                    .graph
                    .canonical_sha256()
                    .map_err(|_| Failure::Fixture)?
                && prepared
                    .receipt()
                    .full_document
                    .full_document
                    .source_graph_sha256
                    == hex::encode(
                        input
                            .graph
                            .canonical_sha256()
                            .map_err(|_| Failure::Fixture)?,
                    ),
        )?;
        p.check(
            input.label,
            "fresh_verify_exact",
            prepared.verify(&provider, &bindings, now()?)? == *prepared.receipt(),
        )?;
        p.check(
            input.label,
            "whole_non_state_graph_fields_exact",
            only_states_changed(&input.graph, prepared.target_graph())?,
        )?;
        p.check(input.label,"route_denied_no_publication",matches!(prepared.require_current_product_route(&provider,&bindings,now()?),Err(StoredFullDocumentProductFormError::FullDocument(hwpx_agent_cli::form_stored_provider::full_document::StoredFullDocumentFormError::RouteUnqualified)))
            &&revisions.head(&ctx,project()?,branch(case)?)?==RevisionHead::new(Some(revision(case)?),1)?
            &&metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested"||e.event=="artifact.ingest.deduplicated").count()==before)?;
        let mut encrypted = true;
        for bytes in [
            &input.form.source,
            input
                .graph
                .canonical_json()
                .map_err(|_| Failure::Fixture)?
                .as_ref(),
        ] {
            let record = metadata
                .find_by_content(reader.tenant_id(), ContentDigest::of(bytes))?
                .ok_or(Failure::Fixture)?;
            let cipher = blobs.get(record.object_key())?.ok_or(Failure::Fixture)?;
            encrypted &= cipher.len() == bytes.len() + 16 && cipher != *bytes;
        }
        p.check(input.label, "encrypted_package_ir_not_plaintext", encrypted)?;
        p.receipts
            .push(ContentDigest::of(&serde_json::to_vec(prepared.receipt())?).hex());
        p.candidates
            .push(ContentDigest::of(prepared.candidate_bytes()).hex());
    }
    Ok(())
}
fn denied(p: &mut Probe, artifacts: &Artifacts, values: &[Input]) -> Result<()> {
    let revisions = read_service()?;
    let ctx = context()?;
    let reader = reader()?;
    for (index, input) in values.iter().enumerate() {
        let case = u8::try_from(index).map_err(|_| Failure::Fixture)?;
        let provider = StoredFormProvider::bind(
            artifacts,
            &revisions,
            &reader,
            &ctx,
            project()?,
            branch(case)?,
            DocumentId::parse("actual-form-document").map_err(|_| Failure::Fixture)?,
        )
        .map_err(|_| Failure::Fixture)?;
        p.check(
            input.label,
            "project_acl_denied",
            StoredFullDocumentProductFormRequest::prepare_json(
                &provider,
                &request(input, case)?,
                &StoredProductFormBindings {
                    map: &input.form.map,
                    policies: &input.form.policies,
                    access: &input.access,
                },
                now()?,
            )
            .is_err(),
        )?;
    }
    Ok(())
}
fn only_states_changed(source: &DocumentGraph, target: &DocumentGraph) -> Result<bool> {
    let original = source.clone().into_draft();
    let mut target = target.clone().into_draft();
    let Node::Drawing(source_controls) = &original.sections[0].body.children[1] else {
        return Err(Failure::Fixture);
    };
    let Node::Drawing(target_controls) = &mut target.sections[0].body.children[1] else {
        return Err(Failure::Fixture);
    };
    if source_controls.children.children.len() != target_controls.children.children.len() {
        return Ok(false);
    }
    for (source, target) in source_controls
        .children
        .children
        .iter()
        .zip(&mut target_controls.children.children)
    {
        let (Node::FormControl(source), Node::FormControl(target)) = (source, target) else {
            return Err(Failure::Fixture);
        };
        let state = source
            .properties
            .iter()
            .find(|(key, _)| *key == "complete_control_state_json")
            .ok_or(Failure::Fixture)?
            .1
            .clone();
        target
            .properties
            .insert("complete_control_state_json", state);
    }
    Ok(target == original)
}
fn main() {
    let run = || -> Result<Value> {
        let mode = env("P65_MODE")?;
        let values = inputs()?;
        let (artifacts, metadata, blobs) = service(&values, 65)?;
        let mut p = Probe::default();
        match mode.as_str() {
            "seed" => {
                seed(&mut p, &artifacts, &values)?;
                verify(&mut p, &artifacts, &metadata, &blobs, &values)?;
            }
            "verify" => verify(&mut p, &artifacts, &metadata, &blobs, &values)?,
            "denied" => denied(&mut p, &artifacts, &values)?,
            "safety" => safety::run(&mut p, &artifacts, &metadata, &values)?,
            "actual_import" => actual_import::run(&mut p, &artifacts, &metadata, &blobs, &values)?,
            "actual_import_denied" => actual_import::denied(&mut p, &artifacts, &values)?,
            "actual_import_safety" => {
                actual_import::safety(&mut p, &artifacts, &metadata, &values)?;
            }
            _ => return Err(Failure::Fixture),
        }
        Ok(
            serde_json::json!({"state":"pass","mode":mode,"actual_assertions":p.checks.len(),"checks":p.checks,"receipt_sha256":p.receipts,"candidate_sha256":p.candidates,
            "scanner_graph_and_baseline_authority":"synthetic_not_native_or_signed_execution","native_activated":false,"p09_complete":false}),
        )
    };
    match run() {
        Ok(value) => println!("{value}"),
        Err(error) => {
            eprintln!("P65_PROBE_FAILED code={error}");
            std::process::exit(2)
        }
    }
}
