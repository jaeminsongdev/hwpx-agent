use super::*;
use artifact_service::{ArtifactId, SubjectDigest, TenantId};
use revision_service::CommitObservation;
use serde::{Deserialize, Serialize};

const SCHEMA: &str = "hwpx-agent.stored-revision-commit-intent/v1";
const MAX_INTENT_BYTES: u64 = 64 * 1024;

#[derive(Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct CommitIntent {
    schema_version: String,
    tenant: TenantId,
    subject: SubjectDigest,
    manifest_sha256: ContentDigest,
    source_sha256: ContentDigest,
    source_size: u64,
    result_sha256: ContentDigest,
    result_size: u64,
    request: ServiceRequest,
}

fn digest(bytes: [u8; 32]) -> Result<ContentDigest, StoredCommitError> {
    ContentDigest::parse(&hex::encode(bytes)).map_err(|_| StoredCommitError::Binding)
}

impl<R, B, S, V, F> StoredResultRevisionCas<'_, R, B, S, V, F>
where R: ArtifactMetadataRepository, B: EncryptedBlobStore, S: ArtifactScanner,
    V: RevisionRepository, F: FnMut() -> u64,
{
    pub(super) fn persist_precommit(&mut self, request: &RevisionCommitRequest) -> Result<(), StoredCommitError> {
        let bytes = request.canonical_json().map_err(|_| StoredCommitError::Binding)?;
        if bytes.is_empty() || bytes.len() as u64 > MAX_INTENT_BYTES { return Err(StoredCommitError::Binding); }
        let sha = ContentDigest::of(&bytes);
        if sha != digest(request.canonical_sha256().map_err(|_| StoredCommitError::Binding)?)? {
            return Err(StoredCommitError::Binding);
        }
        let stored = self.artifacts.ingest(self.context, IngestRequest { bytes,
            media_type: MediaType::parse("application/json").map_err(|_| StoredCommitError::Binding)?,
            file_name: FileName::parse("workspace-precommit.json").map_err(|_| StoredCommitError::Binding)?, kind: ArtifactKind::Receipt,
        }, (self.clock)()).map_err(|_| StoredCommitError::Artifact)?;
        self.retained_precommit = Some(stored.clone());
        if !readable_intent(&stored) || stored.sha256 != sha { return Err(StoredCommitError::Artifact); }
        let readback = self.artifacts.download(self.context, stored.artifact_id, (self.clock)())
            .map_err(|_| StoredCommitError::Artifact)?;
        if readback.len() as u64 != stored.size_bytes || ContentDigest::of(&readback) != sha {
            return Err(StoredCommitError::Artifact);
        }
        Ok(())
    }

    pub(super) fn persist_intent(&mut self, request: &ServiceRequest) -> Result<(), StoredCommitError> {
        let intent = CommitIntent {
            schema_version: SCHEMA.into(), tenant: self.context.tenant_id(), subject: self.context.subject(),
            manifest_sha256: digest(self.manifest_sha256)?, source_sha256: digest(self.binding.manifest.expected_source_sha256())?,
            source_size: self.binding.manifest.expected_source_size(), result_sha256: self.output_sha256,
            result_size: self.binding.output.len() as u64, request: request.clone(),
        };
        let bytes = serde_json::to_vec(&intent).map_err(|_| StoredCommitError::Binding)?;
        if bytes.len() as u64 > MAX_INTENT_BYTES { return Err(StoredCommitError::Binding); }
        let sha = ContentDigest::of(&bytes);
        self.intent_sha256 = Some(sha);
        let stored = self.artifacts.ingest(self.context, IngestRequest { bytes,
            media_type: MediaType::parse("application/json").map_err(|_| StoredCommitError::Binding)?,
            file_name: FileName::parse("revision-intent.json").map_err(|_| StoredCommitError::Binding)?, kind: ArtifactKind::Receipt,
        }, (self.clock)()).map_err(|_| StoredCommitError::Artifact)?;
        self.retained_intent = Some(stored.clone());
        if !readable_intent(&stored) || stored.sha256 != sha { return Err(StoredCommitError::Artifact); }
        let readback = self.artifacts.download(self.context, stored.artifact_id, (self.clock)())
            .map_err(|_| StoredCommitError::Artifact)?;
        if readback.len() as u64 != stored.size_bytes || ContentDigest::of(&readback) != sha {
            return Err(StoredCommitError::Artifact);
        }
        Ok(())
    }
}

/// Expected identity comes from the authenticated server's retained job, not arbitrary receipt JSON.
/// The job must persist this handle/digest before it can promise restart-safe reconciliation.
pub struct StoredCommitRecoveryBinding<'a> {
    pub intent: ArtifactId,
    pub intent_sha256: ContentDigest,
    pub manifest: &'a ExecutionManifest,
    pub request: &'a ServiceRequest,
    pub result_sha256: ContentDigest,
    pub result_size: u64,
}
impl fmt::Debug for StoredCommitRecoveryBinding<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("StoredCommitRecoveryBinding").field("result_size", &self.result_size).finish_non_exhaustive()
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum RecoveredResult {
    VerifiedAvailable(ArtifactDescriptor),
    /// The commit remains observed, but its result cannot currently be served as verified.
    Unavailable,
}
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum StoredCommitRecoveryOutcome {
    Committed { receipt: RevisionReceipt, result: RecoveredResult },
    /// Not visible now, NOT proof of no effect, no retry or job-transition authorization.
    NotObserved,
}

/// Observes a saved intent through current artifact access/AEAD and the sealed-node repository.
/// A later head does not erase historical commit evidence. Result availability is independent.
/// # Errors
/// Rejects missing access, foreign/drifted/oversized/duplicate/unknown intent fields and bindings.
/// Never commits, ingests, updates a field/job or starts Native; missing visibility is unresolved.
#[allow(clippy::too_many_arguments)]
pub fn reconcile_stored_commit<R, B, S, V, F>(
    artifacts: &ArtifactService<R, B, S>, revisions: &RevisionService<V>,
    context: &RequestContext, revision_context: &RevisionRequestContext,
    binding: &StoredCommitRecoveryBinding<'_>, mut clock: F,
) -> Result<StoredCommitRecoveryOutcome, StoredCommitError>
where R: ArtifactMetadataRepository, B: EncryptedBlobStore, S: ArtifactScanner,
    V: RevisionRepository, F: FnMut() -> u64,
{
    if context.tenant_id() != revision_context.tenant_id() || context.subject() != revision_context.subject()
        || !context.has_scope(AuthScope::DocumentRead)
    { return Err(StoredCommitError::Scope); }
    if binding.result_size == 0 || binding.result_size > MAX_BYTES { return Err(StoredCommitError::Binding); }
    let descriptor = artifacts.get_descriptor(context, binding.intent, clock()).map_err(|_| StoredCommitError::Artifact)?;
    if !readable_intent(&descriptor) || descriptor.artifact_id != binding.intent || descriptor.sha256 != binding.intent_sha256 {
        return Err(StoredCommitError::Artifact);
    }
    let bytes = artifacts.download(context, binding.intent, clock()).map_err(|_| StoredCommitError::Artifact)?;
    if bytes.len() as u64 != descriptor.size_bytes || bytes.len() as u64 > MAX_INTENT_BYTES
        || ContentDigest::of(&bytes) != binding.intent_sha256
    { return Err(StoredCommitError::Artifact); }
    let intent: CommitIntent = serde_json::from_slice(&bytes).map_err(|_| StoredCommitError::Binding)?;
    observe_bound_intent(artifacts,revisions,context,revision_context,binding,&mut clock,&intent)
}

#[allow(clippy::too_many_arguments)]
fn observe_bound_intent<R,B,S,V,F>(artifacts:&ArtifactService<R,B,S>,revisions:&RevisionService<V>,context:&RequestContext,
    revision_context:&RevisionRequestContext,binding:&StoredCommitRecoveryBinding<'_>,clock:&mut F,intent:&CommitIntent)
    ->Result<StoredCommitRecoveryOutcome,StoredCommitError>
where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository,F:FnMut()->u64,
{
    if intent.schema_version != SCHEMA || intent.tenant != context.tenant_id() || intent.subject != context.subject()
        || intent.manifest_sha256 != digest(binding.manifest.canonical_sha256().map_err(|_| StoredCommitError::Binding)?)?
        || intent.source_sha256 != digest(binding.manifest.expected_source_sha256())?
        || intent.source_size != binding.manifest.expected_source_size() || intent.request != *binding.request
        || intent.result_sha256 != binding.result_sha256 || intent.result_size != binding.result_size
        || binding.request.source_artifact_id().public_id() != binding.manifest.source_artifact_id().as_str()
        || binding.request.expected_head().revision_id().map(|r| r.public_id()).as_deref() != Some(binding.manifest.base_revision().as_str())
        || binding.request.operation_plan_sha256() != digest(binding.manifest.compiled_plan_sha256())?
    { return Err(StoredCommitError::Binding); }
    let observation = revisions.observe_commit(revision_context, &intent.request)
        .map_err(|error| if error == RevisionError::CommitOutcomeUnknown { StoredCommitError::Unknown } else { StoredCommitError::Revision })?;
    match observation {
        CommitObservation::NotObserved => Ok(StoredCommitRecoveryOutcome::NotObserved),
        CommitObservation::Committed(receipt) => {
            let mut verify = || -> Result<ArtifactDescriptor, StoredCommitError> {
                let result = artifacts.get_descriptor(context, intent.request.result_artifact_id(), clock())
                    .map_err(|_| StoredCommitError::Artifact)?;
                if !available(&result) || result.sha256 != intent.result_sha256 || result.size_bytes != intent.result_size {
                    return Err(StoredCommitError::Artifact);
                }
                let data = artifacts.download(context, result.artifact_id, clock()).map_err(|_| StoredCommitError::Artifact)?;
                if data.len() as u64 != result.size_bytes || ContentDigest::of(&data) != result.sha256 { return Err(StoredCommitError::Artifact); }
                Ok(result)
            };
            let result = verify().map_or(RecoveredResult::Unavailable, RecoveredResult::VerifiedAvailable);
            Ok(StoredCommitRecoveryOutcome::Committed { receipt, result })
        }
    }
}

/// Registration and commit visibility are distinct. Neither missing state permits execution.
#[derive(Clone,Debug,Eq,PartialEq)]
pub enum RegisteredStoredCommitRecoveryOutcome{
    RegistrationNotObserved,
    Registered(StoredCommitRecoveryOutcome),
}

/// Recovers from an exact DB locator, authenticated encrypted receipts and a trusted manifest.
/// No separately saved ServiceRequest is needed. Result availability remains independent of
/// committed observation. This is not a route/lease or no-effect/retry authorization.
/// # Errors
/// Rechecks context/read scope, DB row/request identity, receipt access/AEAD and manifest binding.
/// Never ingests, registers, commits, leases, changes job/attempt state or invokes the engine.
#[allow(clippy::too_many_arguments)]
pub fn reconcile_registered_stored_commit<R,B,S,V,F>(artifacts:&ArtifactService<R,B,S>,revisions:&RevisionService<V>,
    context:&RequestContext,revision_context:&RevisionRequestContext,
    lookup:revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::StoredCommitIntentLookup,
    manifest:&ExecutionManifest,mut clock:F)->Result<RegisteredStoredCommitRecoveryOutcome,StoredCommitError>
where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:StoredRevisionJobRepository,F:FnMut()->u64,
{
    if context.tenant_id()!=revision_context.tenant_id()||context.subject()!=revision_context.subject()||!context.has_scope(AuthScope::DocumentRead){return Err(StoredCommitError::Scope);}
    let Some(row)=revisions.repository().read_commit_intent(revision_context,lookup)
        .map_err(|e|if e==RevisionError::CommitOutcomeUnknown{StoredCommitError::Unknown}else{StoredCommitError::Revision})?
        else{return Ok(RegisteredStoredCommitRecoveryOutcome::RegistrationNotObserved)};
    let descriptor=artifacts.get_descriptor(context,row.intent_artifact_id(),clock()).map_err(|_|StoredCommitError::Artifact)?;
    if !readable_intent(&descriptor)||descriptor.artifact_id!=row.intent_artifact_id()||descriptor.sha256!=row.intent_sha256(){return Err(StoredCommitError::Artifact);}
    let bytes=artifacts.download(context,row.intent_artifact_id(),clock()).map_err(|_|StoredCommitError::Artifact)?;
    if bytes.len()as u64!=descriptor.size_bytes||bytes.len()as u64>MAX_INTENT_BYTES||ContentDigest::of(&bytes)!=row.intent_sha256(){return Err(StoredCommitError::Artifact);}
    let intent:CommitIntent=serde_json::from_slice(&bytes).map_err(|_|StoredCommitError::Binding)?;
    row.validate_recovered_request(revision_context,lookup,&intent.request).map_err(|_|StoredCommitError::Binding)?;
    if intent.result_size==0||intent.result_size>MAX_BYTES{return Err(StoredCommitError::Binding);}
    let precommit=artifacts.get_descriptor(context,row.precommit_artifact_id(),clock()).map_err(|_|StoredCommitError::Artifact)?;
    if !readable_intent(&precommit)||precommit.artifact_id!=row.precommit_artifact_id()||precommit.sha256!=intent.request.transaction_receipt_sha256(){return Err(StoredCommitError::Artifact);}
    let precommit_bytes=artifacts.download(context,precommit.artifact_id,clock()).map_err(|_|StoredCommitError::Artifact)?;
    if precommit_bytes.len()as u64!=precommit.size_bytes||precommit_bytes.len()as u64>MAX_INTENT_BYTES||ContentDigest::of(&precommit_bytes)!=precommit.sha256{return Err(StoredCommitError::Artifact);}
    let binding=StoredCommitRecoveryBinding{intent:row.intent_artifact_id(),intent_sha256:row.intent_sha256(),manifest,request:&intent.request,
        result_sha256:intent.result_sha256,result_size:intent.result_size};
    // Share the original manifest/sealed-node/result checks. Each encrypted receipt is read once.
    observe_bound_intent(artifacts,revisions,context,revision_context,&binding,&mut clock,&intent).map(RegisteredStoredCommitRecoveryOutcome::Registered)
}

fn readable_intent(d: &ArtifactDescriptor) -> bool {
    d.kind == ArtifactKind::Receipt && d.storage_state == StorageState::Available
        && d.validation_state == ValidationState::Verified && d.quarantine_reason.is_none()
        && d.media_type.as_str() == "application/json" && d.size_bytes > 0 && d.size_bytes <= MAX_INTENT_BYTES
}
