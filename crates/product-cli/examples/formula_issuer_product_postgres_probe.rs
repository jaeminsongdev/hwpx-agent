//! Original source -> leased SQL22 revision -> generated policy -> real signature -> original consumer.
#[path = "formula_issuer_product_postgres_probe/source.rs"]
mod source;
#[path = "formula_issuer_product_postgres_probe/worker.rs"]
mod worker;
#[path = "formula_issuer_product_postgres_probe/durable.rs"]
mod durable;
use durable::ProbeBlobStore;
// P151 negative-controls module: private synthetic fixture only.
#[path = "formula_issuer_product_postgres_probe/durable_negative.rs"]
mod durable_negative;
// End P151 negative-controls module.
use artifact_service::{
    Aes256GcmKeyring, ArtifactError, ArtifactMetadataRepository, ArtifactScanner, ArtifactService,
    ArtifactServiceConfig, AuthScope, ContentDigest, DownloadSigner, EncryptedBlobStore,
    InMemoryBlobStore, KeyReference, LocalPostgresConfig, LocalPostgresMetadataRepository,
    RequestContext, ScanEvidence, ScanRequest, ScanVerdict, ScannerReference,
    ScannerSignatureVersion, SubjectDigest, TenantId,
};
use hwpx_agent_cli::form_stored_provider::actual_import::source_policy::formulas::{
    issuer::{
        FormulaIssuerKey, FormulaIssuerTrustDraft, SystemFormulaIssuerClock,
        registry::{
            FORMULA_ISSUER_TRUST_SCHEMA,
            provision::{PostgresFormulaIssuerWriteGateway, RegistryFormulaProvisioner},
        },
    },
    postgres::PostgresFormulaPolicyProvider,
};
use revision_service::{
    ProjectId, RevisionRequestContext,
    postgres::{
        LocalPostgresRevisionConfig,
        source_formula_policy::issuer_registry::{
            FormulaIssuerRegistryRepository, LocalPostgresFormulaIssuerRegistryRepository,
            management::{
                LocalPostgresFormulaRegistryManagementRepository, RegistryManagementCapability,
            },
        },
    },
};
use ring::{
    rand::{SecureRandom, SystemRandom},
    signature::{Ed25519KeyPair, KeyPair},
};
use std::time::{SystemTime, UNIX_EPOCH};
use uuid::Uuid;

type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>;
#[derive(Debug)]
struct ProbeRootScanner {
    source_digest: ContentDigest,
    graph_digest: ContentDigest,
}
impl ArtifactScanner for ProbeRootScanner {
    fn scan(&self, request: ScanRequest<'_>) -> std::result::Result<ScanEvidence, ArtifactError> {
        if [
            self.source_digest,
            self.graph_digest,
            ContentDigest::of(source::PRIOR),
            ContentDigest::of(source::RECEIPT),
        ]
        .contains(&ContentDigest::of(request.bytes))
        {
            return scan_evidence();
        }
        let value: serde_json::Value =
            serde_json::from_slice(request.bytes).map_err(|_| ArtifactError::ScanNotClean)?;
        if !(value["schema_version"] == FORMULA_ISSUER_TRUST_SCHEMA
            && value["issuer"] == "p143-test"
            || value["schema_version"] == "hwpx-agent.source-table-formula-policy/v1"
            || value["schema_version"] == "hwpx-agent.source-formula-approval/v1")
        {
            return Err(ArtifactError::ScanNotClean);
        }
        scan_evidence()
    }
}
fn scan_evidence() -> std::result::Result<ScanEvidence, ArtifactError> {
    Ok(ScanEvidence {
        engine: ScannerReference::parse("scanner.synthetic-root")?,
        signature_version: ScannerSignatureVersion::parse("p142-v1")?,
        verdict: ScanVerdict::Clean,
    })
}
#[derive(Default)]
struct Probe {
    stage: &'static str,
    checks: Vec<&'static str>,
    formula_outcome: Option<&'static str>,
    source_index: Option<usize>,
    source_sha256: Option<String>,
    original_source_sha256: Option<String>,
    input_mode: Option<&'static str>,
    only_one_numeric_leaf_changed: bool,
}
impl Probe {
    fn check(&mut self, stage: &'static str, ok: bool) -> Result<()> {
        self.stage = stage;
        if !ok {
            return Err("closed_probe_check_failed".into());
        }
        self.checks.push(stage);
        Ok(())
    }
}
fn env(name: &str) -> Result<String> {
    Ok(std::env::var(name)?)
}
fn config(user: &str) -> Result<LocalPostgresRevisionConfig> {
    Ok(LocalPostgresRevisionConfig::new(
        env("P143_DB_PORT")?.parse()?,
        "postgres".into(),
        user.into(),
        env("P143_DB_PASSWORD")?,
    )?)
}
fn run(p: &mut Probe) -> Result<()> {
    let tenant = TenantId::new(Uuid::parse_str("60000000-0000-0000-0000-000000000001")?)?;
    let owner = SubjectDigest::parse(&"a".repeat(64))?;
    let context = RequestContext::new(
        tenant,
        owner,
        [AuthScope::DocumentRead, AuthScope::DocumentWrite],
    );
    let revision = RevisionRequestContext::new(tenant, owner);
    let project = ProjectId::parse("prj_62000000000000000000000000000001")?;
    p.stage = "original_artifact_schema22_admission";
    let metadata = LocalPostgresMetadataRepository::connect_formula_issuer_registry_schema22(
        &LocalPostgresConfig::new(
            env("P143_DB_PORT")?.parse()?,
            "postgres".into(),
            "p142_artifact".into(),
            env("P143_DB_PASSWORD")?,
        )?,
        tenant,
    )?;
    p.check("original_artifact_schema22_admission", true)?;
    p.stage = "registry_exact_admissions";
    let reader = LocalPostgresFormulaIssuerRegistryRepository::connect(
        &config("p141_reader")?,
        revision.clone(),
        None,
    )?;
    let roots = LocalPostgresFormulaRegistryManagementRepository::connect(
        &config("p141_root")?,
        revision.clone(),
        RegistryManagementCapability::Trust,
    )?;
    let approvals = LocalPostgresFormulaRegistryManagementRepository::connect(
        &config("p141_approval")?,
        revision.clone(),
        RegistryManagementCapability::Approval,
    )?;
    let writer = PostgresFormulaIssuerWriteGateway::new(&roots, &approvals);
    let policies = PostgresFormulaPolicyProvider::new(reader.policy_repository());
    p.check("registry_exact_admissions", true)?;
    root_workflow(p, &metadata, &reader, &writer, &policies, &context, project)
}
type Service =
    ArtifactService<LocalPostgresMetadataRepository, ProbeBlobStore, ProbeRootScanner>;
fn artifact_service(
    metadata: &LocalPostgresMetadataRepository,
    input: &source::Input,
) -> Result<(Service, ProbeBlobStore)> {
    let random = SystemRandom::new();
    let mut key = [0; 32];
    random
        .fill(&mut key)
        .map_err(|_| "random_key_unavailable")?;
    let reference = KeyReference::parse("kms.p143-ephemeral")?;
    let keyring_result = Aes256GcmKeyring::new(reference.clone(), [(reference, key)]);
    key.fill(0);
    let keyring = keyring_result?;
    let mut hmac = [0; 32];
    random
        .fill(&mut hmac)
        .map_err(|_| "random_key_unavailable")?;
    let signer_result = DownloadSigner::new(
        "https://artifact.invalid/v1/download",
        KeyReference::parse("hmac.p143-ephemeral")?,
        &hmac,
        60,
    );
    hmac.fill(0);
    let blobs = ProbeBlobStore::from_driver_env()?;
    let artifacts = ArtifactService::new(
        metadata.clone(),
        blobs.clone(),
        ProbeRootScanner {
            source_digest: ContentDigest::of(&input.raw),
            graph_digest: ContentDigest::of(&input.graph_bytes),
        },
        keyring,
        signer_result?,
        ArtifactServiceConfig::new(32 * 1024 * 1024, 60)?,
    );
    Ok((artifacts, blobs))
}
fn trust_draft(
    context: &RequestContext,
    project: ProjectId,
) -> Result<(FormulaIssuerTrustDraft, Ed25519KeyPair, u64)> {
    let random = SystemRandom::new();
    let private =
        Ed25519KeyPair::generate_pkcs8(&random).map_err(|_| "ephemeral_custody_unavailable")?;
    let pair = Ed25519KeyPair::from_pkcs8(private.as_ref())
        .map_err(|_| "ephemeral_custody_unavailable")?;
    let public: [u8; 32] = pair.public_key().as_ref().try_into()?;
    let now = SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs();
    let draft = FormulaIssuerTrustDraft {
        tenant: context.tenant_id(),
        project,
        issuer: "p143-test".into(),
        generation: 4,
        valid_from: now.saturating_sub(1),
        valid_until: now.checked_add(3600).ok_or("clock_range")?,
        max_approval_lifetime: 600,
        active_keys: vec![FormulaIssuerKey::new("p143-ephemeral".into(), public)?],
    };
    Ok((draft, pair, now))
}
fn root_workflow(
    p: &mut Probe,
    metadata: &LocalPostgresMetadataRepository,
    reader: &LocalPostgresFormulaIssuerRegistryRepository,
    writer: &PostgresFormulaIssuerWriteGateway<'_>,
    policies: &PostgresFormulaPolicyProvider,
    context: &RequestContext,
    project: ProjectId,
) -> Result<()> {
    let input = source::read()?;
    p.source_index = Some(input.index);
    p.source_sha256 = Some(ContentDigest::of(&input.raw).hex());
    p.original_source_sha256 = Some(input.original_sha.hex());
    p.input_mode = Some(input.mode);
    p.only_one_numeric_leaf_changed = input.only_one_numeric_leaf_changed;
    let (artifacts, blobs) = artifact_service(metadata, &input)?;
    let (draft, pair, now) = trust_draft(context, project)?;
    let clock = SystemFormulaIssuerClock;
    let provisioner =
        RegistryFormulaProvisioner::new(reader, writer, policies, &artifacts, context, &clock);
    p.stage = "original_root_workflow_AEAD_SQL_commit_readback";
    let receipt = provisioner.install_trust(draft, 3)?;
    p.check("original_root_workflow_AEAD_SQL_commit_readback", true)?;
    let row = reader.read_trust(
        &RevisionRequestContext::new(context.tenant_id(), context.subject()),
        project,
    )?;
    p.check(
        "root_named_metadata_exact",
        row.tenant == context.tenant_id()
            && row.project == project
            && row.generation == 4
            && row.artifact == receipt.artifact()
            && row.digest == receipt.digest()
            && row.issuer == "p143-test"
            && row.creator == context.subject(),
    )?;
    let record = metadata
        .find(context.tenant_id(), row.artifact)?
        .ok_or("artifact_missing")?;
    let raw = artifacts.download(context, row.artifact, now)?;
    p.check(
        "real_plaintext_digest_exact",
        ContentDigest::of(&raw) == row.digest && record.content_sha256() == row.digest,
    )?;
    let ciphertext = blobs.get(record.object_key())?.ok_or("blob_missing")?;
    p.check(
        "real_ciphertext_hash_exact",
        ContentDigest::of(&ciphertext) == record.encryption().ciphertext_sha256,
    )?;
    p.check(
        "ciphertext_not_plaintext",
        !ciphertext.windows(raw.len()).any(|bytes| bytes == raw),
    )?;
    // P150 owned-local extension: original RAM mode and assertions are unchanged.
    if blobs.is_durable() {
        p.check("durable_root_disk_ciphertext_tag_and_digest_exact",
            ciphertext.len() == raw.len().checked_add(16).ok_or("ciphertext_length")?
                && ContentDigest::of(&ciphertext) == record.encryption().ciphertext_sha256)?;
        blobs.reopen()?;
        p.check("durable_root_fresh_handle_original_service_whole_read",
            blobs.get(record.object_key())? == Some(ciphertext.clone())
                && artifacts.download(context,row.artifact,now)? == raw)?;
    }
    // End P150 owned-local extension.
    let decoded: serde_json::Value = serde_json::from_slice(&raw)?;
    p.check(
        "generated_public_key_roundtrip",
        decoded["keys"][0]["public_key_hex"] == hex::encode(pair.public_key().as_ref()),
    )?;
    p.check(
        "real_DB_audit_ingested",
        metadata
            .audit_events()?
            .iter()
            .any(|event| event.event == "artifact.ingested" && event.artifact_id == row.artifact),
    )?;
    source::run(
        p,
        &source::Pipeline {
            metadata,
            registry: reader,
            writes: writer,
            policies,
            artifacts: &artifacts,
            blobs: &blobs,
            context,
            pair: &pair,
            project,
        },
        &input,
    )
}
fn main() {
    let mut probe = Probe::default();
    let result = run(&mut probe);
    println!(
        "{}",
        serde_json::json!({"state":if result.is_ok(){"PASS_ORIGINAL_SIGNATURE_CONSUMER_SQL22_COMPONENT_NOT_NATIVE_OR_GATE"}else{"FAIL_CLOSED"},
        "checks":probe.checks,"failed_stage":if result.is_ok(){None}else{Some(probe.stage)},"formula_outcome":probe.formula_outcome,
        "source_index":probe.source_index,"source_sha256":probe.source_sha256,
        "original_source_sha256":probe.original_source_sha256,"input_mode":probe.input_mode,
        "only_one_numeric_leaf_changed":probe.only_one_numeric_leaf_changed,
        "real_approval_signature_and_original_consumer_executed":result.is_ok(),"durable_blob_store_qualified":false,
        "production_key_custody_qualified":false,"P09_gate":"OPEN","product_complete":false})
    );
    if result.is_err() {
        std::process::exit(1);
    }
}
