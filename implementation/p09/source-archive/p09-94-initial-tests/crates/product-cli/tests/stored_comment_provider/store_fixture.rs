//! Actual artifact/revision service APIs with an IN-MEMORY backend and synthetic scanner/actors.
//! Fixture commits bind storage bytes, never native comment import or product execution proof.
use artifact_service::*;
use domain_ir::{DocumentGraph, DocumentId};
use hwpx_agent_cli::form_stored_provider::{StoredFormError, StoredFormProvider};
use revision_service::*;
use std::{
    collections::BTreeSet,
    error::Error,
    sync::{
        Arc,
        atomic::{AtomicBool, Ordering},
    },
};
use uuid::Uuid;

pub(super) const SOURCE: &[u8] =
    b"P94 synthetic STORAGE ONLY source bytes, NOT HWPX/native comment evidence";
#[derive(Debug)]
pub(super) struct Scanner(bool);
impl ArtifactScanner for Scanner {
    fn scan(&self, _: ScanRequest<'_>) -> Result<ScanEvidence, ArtifactError> {
        Ok(ScanEvidence {
            engine: ScannerReference::parse("scanner.fixture-only")?,
            signature_version: ScannerSignatureVersion::parse("not-native-v1")?,
            verdict: if self.0 {
                ScanVerdict::Unverified(QuarantineReason::parse("P94_FIXTURE_UNVERIFIED")?)
            } else {
                ScanVerdict::Clean
            },
        })
    }
}
#[derive(Clone, Debug, Default)]
pub(super) struct Blob {
    inner: InMemoryBlobStore,
    pub(super) result_tamper: Arc<AtomicBool>,
    pub(super) ir_tamper: Arc<AtomicBool>,
}
impl EncryptedBlobStore for Blob {
    fn put_if_absent(&self, key: &ObjectKey, bytes: &[u8]) -> Result<(), ArtifactError> {
        self.inner.put_if_absent(key, bytes)
    }
    fn get(&self, key: &ObjectKey) -> Result<Option<Vec<u8>>, ArtifactError> {
        let mut bytes = self.inner.get(key)?;
        let kind = key.as_str().split('/').nth(3);
        if ((kind == Some("result") && self.result_tamper.load(Ordering::SeqCst))
            || (kind == Some("document_ir") && self.ir_tamper.load(Ordering::SeqCst)))
            && let Some(bytes) = &mut bytes
            && let Some(first) = bytes.first_mut()
        {
            *first ^= 1;
        }
        Ok(bytes)
    }
    fn relocate_if_absent(
        &self,
        source: &ObjectKey,
        target: &ObjectKey,
    ) -> Result<(), ArtifactError> {
        self.inner.relocate_if_absent(source, target)
    }
}
type Artifacts = ArtifactService<InMemoryMetadataRepository, Blob, Scanner>;
pub(super) type Provider<'a> =
    StoredFormProvider<'a, InMemoryMetadataRepository, Blob, Scanner, InMemoryRevisionRepository>;
fn artifacts(
    metadata: InMemoryMetadataRepository,
    blob: Blob,
    unverified: bool,
) -> Result<Artifacts, Box<dyn Error>> {
    // Synthetic fixture keys only; no operational keyring, DB, endpoint or issuer is used.
    let reference = KeyReference::parse("fixture.p94-aes")?;
    Ok(ArtifactService::new(
        metadata,
        blob,
        Scanner(unverified),
        Aes256GcmKeyring::new(reference.clone(), [(reference, [94; 32])])?,
        DownloadSigner::new(
            "https://fixture.example.test/download",
            KeyReference::parse("fixture.p94-hmac")?,
            &[95; 32],
            60,
        )?,
        ArtifactServiceConfig::new(32 * 1024 * 1024, 60)?,
    ))
}
pub(super) struct Stored {
    pub(super) artifacts: Artifacts,
    pub(super) metadata: InMemoryMetadataRepository,
    pub(super) blob: Blob,
    pub(super) revisions: RevisionService<InMemoryRevisionRepository>,
    pub(super) owner: RequestContext,
    pub(super) reader: RequestContext,
    pub(super) revision_context: RevisionRequestContext,
    pub(super) project: ProjectId,
    pub(super) branch: BranchId,
    pub(super) result: ArtifactId,
    pub(super) head: RevisionHead,
}
impl Stored {
    pub(super) fn new(kind: ArtifactKind, unverified: bool) -> Result<Self, Box<dyn Error>> {
        let tenant = TenantId::new(Uuid::from_u128(9401))?;
        let owner_subject = SubjectDigest::from_authenticated_subject("P94 synthetic owner")?;
        let reader_subject = SubjectDigest::from_authenticated_subject("P94 synthetic reader")?;
        let owner = RequestContext::new(
            tenant,
            owner_subject,
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
        let blob = Blob::default();
        let artifacts = artifacts(metadata.clone(), blob.clone(), unverified)?;
        let prior = artifacts.ingest(
            &owner,
            IngestRequest {
                bytes: b"P94 synthetic prior storage bytes".to_vec(),
                media_type: MediaType::parse("application/octet-stream")?,
                file_name: FileName::parse("fixture-prior.bin")?,
                kind: ArtifactKind::Source,
            },
            1,
        )?;
        let result = artifacts.ingest(
            &owner,
            IngestRequest {
                bytes: SOURCE.to_vec(),
                media_type: MediaType::parse("application/octet-stream")?,
                file_name: FileName::parse("fixture-result.bin")?,
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
        let project = ProjectId::parse("prj_94000000000000000000000000000001")?;
        let branch = BranchId::parse("brn_94000000000000000000000000000001")?;
        let repository = InMemoryRevisionRepository::default();
        repository.provision_stream(tenant, project, branch)?;
        let revisions = RevisionService::new(repository);
        let commit = RevisionCommitRequest::new(
            CommitId::generate(),
            project,
            branch,
            RevisionHead::empty(),
            RevisionId::generate(),
            vec![],
            prior.artifact_id,
            result.artifact_id,
            None,
            ContentDigest::of(b"synthetic operation"),
            RevisionValidationState::Verified,
            ContentDigest::of(b"synthetic validation"),
            ContentDigest::of(b"synthetic transaction"),
        )?;
        assert!(matches!(
            revisions.commit(&revision_context, &commit)?,
            CommitOutcome::Committed(_)
        ));
        let head = revisions.head(&revision_context, project, branch)?;
        Ok(Self {
            artifacts,
            metadata,
            blob,
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
    pub(super) fn provider(&self) -> Result<Provider<'_>, StoredFormError> {
        self.provider_document("comment-document")
    }
    pub(super) fn provider_document(
        &self,
        document: &str,
    ) -> Result<Provider<'_>, StoredFormError> {
        StoredFormProvider::bind(
            &self.artifacts,
            &self.revisions,
            &self.reader,
            &self.revision_context,
            self.project,
            self.branch,
            DocumentId::parse(document).map_err(|_| StoredFormError::Scope)?,
        )
    }
    pub(super) fn attach(
        &mut self,
        graph: &DocumentGraph,
        raw: Vec<u8>,
        kind: ArtifactKind,
        media: &str,
        fault: usize,
    ) -> Result<FullDocumentIrBinding, Box<dyn Error>> {
        let service = artifacts(self.metadata.clone(), self.blob.clone(), fault == 4)?;
        let ir = service.ingest(
            &self.owner,
            IngestRequest {
                bytes: raw,
                kind,
                media_type: MediaType::parse(media)?,
                file_name: FileName::parse("fixture-complete-ir.json")?,
            },
            4,
        )?;
        self.artifacts.set_permissions(
            &self.owner,
            ir.artifact_id,
            self.reader.subject(),
            BTreeSet::from([ArtifactPermission::Read]),
            5,
        )?;
        let mut binding = FullDocumentIrBinding {
            artifact_id: ir.artifact_id,
            artifact_sha256: ir.sha256,
            result_package_sha256: ContentDigest::of(SOURCE),
            canonical_graph_sha256: ContentDigest::parse(&hex::encode(graph.canonical_sha256()?))?,
        };
        match fault {
            1 => binding.artifact_sha256 = ContentDigest::of(b"wrong artifact"),
            2 => binding.result_package_sha256 = ContentDigest::of(b"wrong source"),
            3 => binding.canonical_graph_sha256 = ContentDigest::of(b"wrong graph"),
            _ => {}
        }
        let request = self.commit()?.with_full_document_ir(binding)?;
        assert!(matches!(
            self.revisions.commit(&self.revision_context, &request)?,
            CommitOutcome::Committed(_)
        ));
        self.head = self
            .revisions
            .head(&self.revision_context, self.project, self.branch)?;
        Ok(binding)
    }
    fn commit(&self) -> Result<RevisionCommitRequest, revision_service::RevisionError> {
        RevisionCommitRequest::new(
            CommitId::generate(),
            self.project,
            self.branch,
            self.head,
            RevisionId::generate(),
            self.head.revision_id().into_iter().collect(),
            ArtifactId::generate(),
            self.result,
            None,
            ContentDigest::of(b"synthetic operation"),
            RevisionValidationState::Verified,
            ContentDigest::of(b"synthetic validation"),
            ContentDigest::of(b"synthetic transaction"),
        )
    }
    pub(super) fn advance(&self) -> Result<(), Box<dyn Error>> {
        assert!(matches!(
            self.revisions
                .commit(&self.revision_context, &self.commit()?)?,
            CommitOutcome::Committed(_)
        ));
        Ok(())
    }
}
