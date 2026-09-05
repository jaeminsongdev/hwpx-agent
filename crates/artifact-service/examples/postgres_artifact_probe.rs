//! Disposable local DB acceptance probe; never accepts a user document or public artifact path.
use std::collections::BTreeSet;
use std::path::Path;

use artifact_service::{
    Aes256GcmKeyring, ArtifactError, ArtifactKind, ArtifactMetadataRepository, ArtifactPermission,
    ArtifactScanner, ArtifactService, ArtifactServiceConfig, AuthScope, ContentDigest,
    DownloadSigner, EncryptedBlobStore, FileName, IngestRequest, KeyReference,
    LocalEncryptedBlobStore, LocalPostgresConfig, LocalPostgresMetadataRepository, MediaType,
    ObjectKey, PostgresConnectStage, QuarantineReason, RequestContext, ScanEvidence, ScanRequest,
    ScanVerdict, ScannerReference, ScannerSignatureVersion, StorageState, SubjectDigest, TenantId,
    ValidationState,
};
use uuid::Uuid;

const PAYLOAD: &[u8] = b"synthetic-P16-private-artifact-persistence-proof";
const NOW: u64 = 1_000;

#[derive(Debug)]
struct SyntheticOnlyScanner;
impl ArtifactScanner for SyntheticOnlyScanner {
    fn scan(&self, request: ScanRequest<'_>) -> Result<ScanEvidence, ArtifactError> {
        if request.bytes != PAYLOAD {
            return Err(ArtifactError::ScanNotClean);
        }
        Ok(ScanEvidence {
            engine: ScannerReference::parse("scanner.synthetic")?,
            signature_version: ScannerSignatureVersion::parse("probe-v1")?,
            verdict: ScanVerdict::Clean,
        })
    }
}

type Service =
    ArtifactService<LocalPostgresMetadataRepository, LocalEncryptedBlobStore, SyntheticOnlyScanner>;

fn service(
    repository: LocalPostgresMetadataRepository,
    root: &Path,
    key: u8,
) -> Result<Service, ArtifactError> {
    let reference = KeyReference::parse("kms.local-probe")?;
    Ok(ArtifactService::new(
        repository,
        LocalEncryptedBlobStore::create(root, 4096)?,
        SyntheticOnlyScanner,
        Aes256GcmKeyring::new(reference.clone(), [(reference, [key; 32])])?,
        DownloadSigner::new(
            "https://artifact.invalid/v1/download",
            KeyReference::parse("hmac.local-probe")?,
            &[83; 32],
            300,
        )?,
        ArtifactServiceConfig::new(1024, 60)?,
    ))
}
fn check(value: bool) -> Result<(), ArtifactError> {
    if value {
        Ok(())
    } else {
        Err(ArtifactError::IntegrityMismatch)
    }
}
fn env(name: &str) -> Result<String, ArtifactError> {
    std::env::var(name).map_err(|_| ArtifactError::InvalidState)
}
fn request() -> Result<IngestRequest, ArtifactError> {
    Ok(IngestRequest {
        bytes: PAYLOAD.to_vec(),
        media_type: MediaType::parse("application/octet-stream")?,
        file_name: FileName::parse("synthetic-plan-evidence.bin")?,
        kind: ArtifactKind::Evidence,
    })
}

fn connect(
    config: &LocalPostgresConfig,
    tenant: TenantId,
) -> Result<LocalPostgresMetadataRepository, ArtifactError> {
    LocalPostgresMetadataRepository::connect_diagnosed(config, tenant).map_err(|failure| {
        eprintln!(
            "P16_POSTGRES_ARTIFACT_CONNECT_FAILED stage={}",
            failure.stage().code()
        );
        failure.into_error()
    })
}

fn main() {
    if let Err(error) = run() {
        eprintln!("P16_POSTGRES_ARTIFACT_PROBE_FAILED code={}", error.code());
        std::process::exit(1);
    }
}

fn run() -> Result<(), ArtifactError> {
    eprintln!("P16_POSTGRES_ARTIFACT_PROBE_STAGE stage=CONFIG");
    let mode = env("HWPX_P16_PROBE_MODE")?;
    let config = LocalPostgresConfig::new(
        env("HWPX_P16_PG_PORT")?
            .parse()
            .map_err(|_| ArtifactError::InvalidState)?,
        "postgres".to_owned(),
        env("HWPX_P16_PG_USER")?,
        env("HWPX_P16_PG_PASSWORD")?,
    )?;
    let tenant = TenantId::new(Uuid::from_u128(1))?;
    if matches!(
        mode.as_str(),
        "reject-role" | "reject-policies" | "reject-privileges"
    ) {
        let expected = match mode.as_str() {
            "reject-role" => PostgresConnectStage::Role,
            "reject-policies" => PostgresConnectStage::Policies,
            _ => PostgresConnectStage::Privileges,
        };
        let rejected = LocalPostgresMetadataRepository::connect_diagnosed(&config, tenant);
        check(
            matches!(rejected, Err(ref failure) if failure.stage() == expected
            && failure.error() == &ArtifactError::AccessDenied),
        )?;
        println!("P16_POSTGRES_ARTIFACT_PROBE_PASS mode={mode}");
        return Ok(());
    }
    eprintln!("P16_POSTGRES_ARTIFACT_PROBE_STAGE stage=CONNECT");
    let repository = connect(&config, tenant)?;
    let root_string = env("HWPX_P16_BLOB_ROOT")?;
    let root = Path::new(&root_string);
    let service = service(repository.clone(), root, 71)?;
    let owner_id = SubjectDigest::from_authenticated_subject("synthetic-owner")?;
    let owner = RequestContext::new(
        tenant,
        owner_id,
        [
            AuthScope::DocumentRead,
            AuthScope::DocumentWrite,
            AuthScope::ArtifactShare,
            AuthScope::SecurityModify,
            AuthScope::SecurityInspect,
        ],
    );
    if mode == "seed" {
        eprintln!("P16_POSTGRES_ARTIFACT_PROBE_STAGE stage=SEED_LOOKUP");
        check(
            repository
                .find_by_content(tenant, ContentDigest::of(PAYLOAD))?
                .is_none(),
        )?;
        eprintln!("P16_POSTGRES_ARTIFACT_PROBE_STAGE stage=SEED_INGEST");
        let descriptor = service.ingest(&owner, request()?, NOW)?;
        eprintln!("P16_POSTGRES_ARTIFACT_PROBE_STAGE stage=SEED_DOWNLOAD");
        check(service.download(&owner, descriptor.artifact_id, NOW)? == PAYLOAD)?;
        println!("P16_POSTGRES_ARTIFACT_PROBE_PASS mode=seed");
        return Ok(());
    }
    let record = repository
        .find_by_content(tenant, ContentDigest::of(PAYLOAD))?
        .ok_or(ArtifactError::NotFound)?;
    if mode == "verify" {
        check(service.download(&owner, record.artifact_id(), NOW)? == PAYLOAD)?;
        let blob = LocalEncryptedBlobStore::create(root, 4096)?
            .get(record.object_key())?
            .ok_or(ArtifactError::NotFound)?;
        check(!blob.windows(PAYLOAD.len()).any(|window| window == PAYLOAD))?;
        check(service.ingest(&owner, request()?, NOW)?.artifact_id == record.artifact_id())?;
        check(repository.insert(record.clone()) == Err(ArtifactError::Conflict))?;
        check(!format!("{config:?}{repository:?}").contains("synthetic-owner"))?;
        println!("P16_POSTGRES_ARTIFACT_PROBE_PASS mode=verify");
        return Ok(());
    }
    if mode == "acl-quarantine" {
        exercise_security(&config, &repository, &service, &owner, &record, root)?;
        println!("P16_POSTGRES_ARTIFACT_PROBE_PASS mode=acl-quarantine");
        return Ok(());
    }
    if mode == "verify-quarantine" {
        check(record.storage_state() == StorageState::Quarantined && record.acl_version() == 4)?;
        check(service.download(&owner, record.artifact_id(), NOW)? == PAYLOAD)?;
        check(!repository.audit_events()?.is_empty())?;
        println!("P16_POSTGRES_ARTIFACT_PROBE_PASS mode=verify-quarantine");
        return Ok(());
    }
    Err(ArtifactError::InvalidState)
}

fn exercise_security(
    config: &LocalPostgresConfig,
    repository: &LocalPostgresMetadataRepository,
    service: &Service,
    owner: &RequestContext,
    record: &artifact_service::ArtifactRecord,
    root: &Path,
) -> Result<(), ArtifactError> {
    let tenant = owner.tenant_id();
    let artifact = record.artifact_id();
    let foreign = TenantId::new(Uuid::from_u128(2))?;
    check(repository.find(foreign, artifact) == Err(ArtifactError::NotFound))?;
    let foreign_repository = connect(config, foreign)?;
    check(foreign_repository.find(foreign, artifact)?.is_none())?;
    check(foreign_repository.audit_events()?.is_empty())?;
    let reader_id = SubjectDigest::from_authenticated_subject("synthetic-reader")?;
    let reader = RequestContext::new(tenant, reader_id, [AuthScope::DocumentRead]);
    check(service.download(&reader, artifact, NOW) == Err(ArtifactError::AccessDenied))?;
    check(
        service.set_permissions(
            owner,
            artifact,
            reader_id,
            BTreeSet::from([ArtifactPermission::Read]),
            NOW,
        )? == 2,
    )?;
    let url = service.issue_download_url(&reader, artifact, NOW)?;
    check(service.set_permissions(owner, artifact, reader_id, BTreeSet::new(), NOW)? == 3)?;
    check(service.redeem_download_url(&reader, &url, NOW).is_err())?;
    check(
        repository.set_permissions(
            tenant,
            artifact,
            2,
            reader_id,
            BTreeSet::from([ArtifactPermission::Read]),
        ) == Err(ArtifactError::Conflict),
    )?;
    check(
        repository.set_permissions(tenant, artifact, 3, owner.subject(), BTreeSet::new())
            == Err(ArtifactError::InvalidState),
    )?;
    let target = ObjectKey::for_artifact(
        tenant,
        record.kind(),
        StorageState::Quarantined,
        record.content_sha256(),
    )?;
    check(
        repository.transition_state(
            tenant,
            artifact,
            1,
            StorageState::Available,
            StorageState::Quarantined,
            ValidationState::Quarantined,
            Some(QuarantineReason::parse("MANUAL_REVIEW")?),
            target,
        ) == Err(ArtifactError::Conflict),
    )?;
    let wrong_key = self::service(repository.clone(), root, 99)?;
    check(wrong_key.download(owner, artifact, NOW) == Err(ArtifactError::CryptoFailure))?;
    check(
        service
            .quarantine(
                owner,
                artifact,
                QuarantineReason::parse("MANUAL_REVIEW")?,
                NOW,
            )?
            .storage_state
            == StorageState::Quarantined,
    )?;
    let ordinary_owner = RequestContext::new(tenant, owner.subject(), [AuthScope::DocumentRead]);
    check(service.download(&ordinary_owner, artifact, NOW) == Err(ArtifactError::Quarantined))?;
    check(
        repository
            .audit_events()?
            .iter()
            .all(|event| event.tenant_id == tenant),
    )?;
    Ok(())
}
