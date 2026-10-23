use artifact_service::{
    Aes256GcmKeyring, ArtifactKind, ArtifactMetadataRepository, ArtifactPermission,
    ArtifactScanner, ArtifactService, ArtifactServiceConfig, AuthScope, ContentDigest,
    DownloadSigner, EncryptedBlobStore, FileName, InMemoryBlobStore, InMemoryMetadataRepository,
    IngestRequest, KeyReference, MediaType, ObjectKey, QuarantineReason, RequestContext,
    ScanEvidence, ScanRequest, ScanVerdict, ScannerReference, ScannerSignatureVersion,
    SubjectDigest, TenantId,
};
use hwpx_agent_cli::form_stored_provider::*;
use revision_service::{
    BranchId, CommitId, CommitOutcome, InMemoryRevisionRepository, RevisionCommitRequest,
    RevisionHead, RevisionRequestContext, RevisionService, RevisionValidationState,
};
use std::{
    collections::BTreeSet,
    sync::{
        Arc,
        atomic::{AtomicBool, Ordering},
    },
};
use uuid::Uuid;

// TEST ONLY: local scanner fixture and synthetic crypto keys, NOT a real scanner,
// external issuer/native approval or product signed form route.
#[derive(Debug)]
struct FixtureScanner {
    unavailable: bool,
}
impl ArtifactScanner for FixtureScanner {
    fn scan(&self, _: ScanRequest<'_>) -> Result<ScanEvidence, artifact_service::ArtifactError> {
        Ok(ScanEvidence {
            engine: ScannerReference::parse("scanner.fixture-only")?,
            signature_version: ScannerSignatureVersion::parse("not-native-v1")?,
            verdict: if self.unavailable {
                ScanVerdict::Unverified(QuarantineReason::parse("FIXTURE_UNVERIFIED")?)
            } else {
                ScanVerdict::Clean
            },
        })
    }
}
#[derive(Clone, Debug, Default)]
struct FaultBlob {
    inner: InMemoryBlobStore,
    tamper: Arc<AtomicBool>,
    tamper_ir: Arc<AtomicBool>,
}
impl EncryptedBlobStore for FaultBlob {
    fn put_if_absent(
        &self,
        key: &ObjectKey,
        bytes: &[u8],
    ) -> Result<(), artifact_service::ArtifactError> {
        self.inner.put_if_absent(key, bytes)
    }
    fn get(&self, key: &ObjectKey) -> Result<Option<Vec<u8>>, artifact_service::ArtifactError> {
        let mut value = self.inner.get(key)?;
        if (self.tamper.load(Ordering::SeqCst)
            || (self.tamper_ir.load(Ordering::SeqCst)
                && key.as_str().split('/').nth(3) == Some("document_ir")))
            && let Some(bytes) = &mut value
            && let Some(first) = bytes.first_mut()
        {
            *first ^= 1;
        }
        Ok(value)
    }
    fn relocate_if_absent(
        &self,
        source: &ObjectKey,
        target: &ObjectKey,
    ) -> Result<(), artifact_service::ArtifactError> {
        self.inner.relocate_if_absent(source, target)
    }
}
type Artifacts = ArtifactService<InMemoryMetadataRepository, FaultBlob, FixtureScanner>;
type Provider<'a> = StoredFormProvider<
    'a,
    InMemoryMetadataRepository,
    FaultBlob,
    FixtureScanner,
    InMemoryRevisionRepository,
>;
fn fixture_artifacts(
    metadata: InMemoryMetadataRepository,
    blobs: FaultBlob,
    unverified: bool,
) -> Result<Artifacts, Box<dyn Error>> {
    let reference = KeyReference::parse("fixture.p45-aes")?;
    let keyring = Aes256GcmKeyring::new(reference.clone(), [(reference, [45; 32])])?;
    let signer = DownloadSigner::new(
        "https://fixture.example.test/download",
        KeyReference::parse("fixture.p45-hmac")?,
        &[46; 32],
        60,
    )?;
    Ok(ArtifactService::new(
        metadata,
        blobs,
        FixtureScanner {
            unavailable: unverified,
        },
        keyring,
        signer,
        ArtifactServiceConfig::new(32 * 1024 * 1024, 60)?,
    ))
}
struct StoredFixture {
    artifacts: Artifacts,
    metadata: InMemoryMetadataRepository,
    blobs: FaultBlob,
    revisions: RevisionService<InMemoryRevisionRepository>,
    owner: RequestContext,
    reader: RequestContext,
    revision_context: RevisionRequestContext,
    project: revision_service::ProjectId,
    branch: BranchId,
    result: artifact_service::ArtifactId,
    head: RevisionHead,
}
impl StoredFixture {
    fn new(source: &[u8], kind: ArtifactKind, unverified: bool) -> Result<Self, Box<dyn Error>> {
        let tenant = TenantId::new(Uuid::from_u128(451))?;
        let subject = SubjectDigest::from_authenticated_subject("P45 fixture owner private")?;
        let reader_subject =
            SubjectDigest::from_authenticated_subject("P45 fixture reader private")?;
        let owner = RequestContext::new(
            tenant,
            subject,
            [
                AuthScope::DocumentRead,
                AuthScope::DocumentWrite,
                AuthScope::ArtifactShare,
                AuthScope::SecurityModify,
            ],
        );
        let reader = RequestContext::new(tenant, reader_subject, [AuthScope::DocumentRead]);
        let revision_context = RevisionRequestContext::new(tenant, reader_subject);
        let metadata = InMemoryMetadataRepository::default();
        let blobs = FaultBlob::default();
        let artifacts = fixture_artifacts(metadata.clone(), blobs.clone(), unverified)?;
        let prior = artifacts.ingest(
            &owner,
            IngestRequest {
                bytes: b"P45 prior source METADATA FIXTURE ONLY".to_vec(),
                media_type: MediaType::parse("application/octet-stream")?,
                file_name: FileName::parse("prior.bin")?,
                kind: ArtifactKind::Source,
            },
            1,
        )?;
        let result = artifacts.ingest(
            &owner,
            IngestRequest {
                bytes: source.to_vec(),
                media_type: MediaType::parse("application/vnd.hancom.hwpx+zip")?,
                file_name: FileName::parse("private-original.hwpx")?,
                kind,
            },
            2,
        )?;
        artifacts.set_permissions(
            &owner,
            result.artifact_id,
            reader_subject,
            BTreeSet::from([ArtifactPermission::Read]),
            3,
        )?;
        let project = revision_service::ProjectId::parse("prj_45000000000000000000000000000001")?;
        let branch = BranchId::parse("brn_45000000000000000000000000000001")?;
        let repository = InMemoryRevisionRepository::default();
        repository.provision_stream(tenant, project, branch)?;
        let revisions = RevisionService::new(repository);
        // Actual sealed repository-node fixture. These opaque metadata digests and
        // Verified tag are NOT a form/native execution manifest or product commit.
        let request = RevisionCommitRequest::new(
            CommitId::generate(),
            project,
            branch,
            RevisionHead::empty(),
            revision_service::RevisionId::generate(),
            vec![],
            prior.artifact_id,
            result.artifact_id,
            None,
            ContentDigest::of(b"fixture operation only"),
            RevisionValidationState::Verified,
            ContentDigest::of(b"fixture validation only"),
            ContentDigest::of(b"fixture transaction only"),
        )?;
        assert!(matches!(
            revisions.commit(&revision_context, &request)?,
            CommitOutcome::Committed(_)
        ));
        let head = revisions.head(&revision_context, project, branch)?;
        Ok(Self {
            artifacts,
            metadata,
            blobs,
            revisions,
            owner,
            reader,
            revision_context,
            project,
            branch,
            result: result.artifact_id,
            head,
        })
    }
    fn provider(&self) -> Result<Provider<'_>, StoredFormError> {
        StoredFormProvider::bind(
            &self.artifacts,
            &self.revisions,
            &self.reader,
            &self.revision_context,
            self.project,
            self.branch,
            DocumentId::parse("actual-form-document").map_err(|_| StoredFormError::Scope)?,
        )
    }
}
