//! Archived intent v2: old intent stays nested verbatim, canonical manifest bytes are data only.
//! No executable manifest reconstruction, engine, claim/lease, ingest, CAS or job-state changes in recovery.
use super::*;
use operation_engine::ArchivedExecutionManifest;
const SCHEMA_V2:&str="hwpx-agent.stored-revision-commit-intent/v2";

#[derive(Serialize)]struct Write<'a>{schema_version:&'static str,commit_intent:&'a CommitIntent,manifest_canonical_json:&'a[u8]}
#[derive(Deserialize)]#[serde(deny_unknown_fields)]
struct Read{schema_version:String,commit_intent:CommitIntent,manifest_canonical_json:Vec<u8>}
#[derive(Deserialize)]struct Header{schema_version:String}
enum Decoded{Legacy(CommitIntent),Archived(CommitIntent,ArchivedExecutionManifest)}

pub(super) fn encode(intent:&CommitIntent,archive:&ArchivedExecutionManifest)->Result<Vec<u8>,StoredCommitError>{
    if intent.manifest_sha256.as_bytes()!=&archive.canonical_sha256(){return Err(StoredCommitError::Binding);}
    serde_json::to_vec(&Write{schema_version:SCHEMA_V2,commit_intent:intent,manifest_canonical_json:archive.canonical_json()}).map_err(|_|StoredCommitError::Binding)
}
fn decode(bytes:&[u8])->Result<Decoded,StoredCommitError>{
    if bytes.is_empty()||bytes.len()as u64>MAX_INTENT_BYTES{return Err(StoredCommitError::Binding);}
    // Header is a discriminator only. The ORIGINAL bytes are then fully parsed by one exact closed type.
    let header:Header=serde_json::from_slice(bytes).map_err(|_|StoredCommitError::Binding)?;
    match header.schema_version.as_str(){
        SCHEMA=>Ok(Decoded::Legacy(serde_json::from_slice(bytes).map_err(|_|StoredCommitError::Binding)?)),
        SCHEMA_V2=>{
            let record:Read=serde_json::from_slice(bytes).map_err(|_|StoredCommitError::Binding)?;
            if record.schema_version!=SCHEMA_V2||record.commit_intent.schema_version!=SCHEMA{return Err(StoredCommitError::Binding);}
            let archived=ArchivedExecutionManifest::from_canonical_json(&record.manifest_canonical_json,*record.commit_intent.manifest_sha256.as_bytes()).map_err(|_|StoredCommitError::Binding)?;
            Ok(Decoded::Archived(record.commit_intent,archived))
        },_=>Err(StoredCommitError::Binding),
    }
}
pub(super) fn decode_with_original(bytes:&[u8],manifest:&ExecutionManifest)->Result<CommitIntent,StoredCommitError>{
    match decode(bytes)?{
        Decoded::Legacy(intent)=>Ok(intent),
        Decoded::Archived(intent,archive)=>{
            if archive.canonical_json()!=manifest.canonical_json().map_err(|_|StoredCommitError::Binding)?{return Err(StoredCommitError::Binding);}
            Ok(intent)
        }
    }
}

/// Missing registration, legacy data needing an original manifest, and committed observation remain distinct.
/// No variant is a no-effect, execution, retry or current-route permit.
#[derive(Clone,Debug,Eq,PartialEq)]
pub enum ArchivedRegisteredStoredCommitRecoveryOutcome{
    RegistrationNotObserved,LegacyManifestRequired,Registered(StoredCommitRecoveryOutcome),
}

/// # Errors
/// Recovers read-only from the exact registered locator and authenticated encrypted v2 intent/precommit.
/// Neither an original manifest nor separately saved ServiceRequest is accepted/required.
/// Current artifact ACL/AEAD and original registered-request/sealed-node/result checks remain mandatory.
#[allow(clippy::too_many_arguments)]
pub fn reconcile_archived_registered_stored_commit<R,B,S,V,F>(artifacts:&ArtifactService<R,B,S>,revisions:&RevisionService<V>,
    context:&RequestContext,revision_context:&RevisionRequestContext,
    lookup:revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::StoredCommitIntentLookup,mut clock:F)
    ->Result<ArchivedRegisteredStoredCommitRecoveryOutcome,StoredCommitError>
where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:StoredRevisionJobRepository,F:FnMut()->u64,
{
    type O=ArchivedRegisteredStoredCommitRecoveryOutcome;
    if context.tenant_id()!=revision_context.tenant_id()||context.subject()!=revision_context.subject()||!context.has_scope(AuthScope::DocumentRead){return Err(StoredCommitError::Scope);}
    let Some(row)=revisions.repository().read_commit_intent(revision_context,lookup)
        .map_err(|e|if e==RevisionError::CommitOutcomeUnknown{StoredCommitError::Unknown}else{StoredCommitError::Revision})?
        else{return Ok(O::RegistrationNotObserved)};
    let descriptor=artifacts.get_descriptor(context,row.intent_artifact_id(),clock()).map_err(|_|StoredCommitError::Artifact)?;
    if !readable_intent(&descriptor)||descriptor.artifact_id!=row.intent_artifact_id()||descriptor.sha256!=row.intent_sha256(){return Err(StoredCommitError::Artifact);}
    let bytes=artifacts.download(context,row.intent_artifact_id(),clock()).map_err(|_|StoredCommitError::Artifact)?;
    if bytes.len()as u64!=descriptor.size_bytes||bytes.len()as u64>MAX_INTENT_BYTES||ContentDigest::of(&bytes)!=row.intent_sha256(){return Err(StoredCommitError::Artifact);}
    let (intent,archive)=match decode(&bytes)?{Decoded::Legacy(intent)=>(intent,None),Decoded::Archived(intent,archive)=>(intent,Some(archive))};
    if intent.schema_version!=SCHEMA||intent.tenant!=context.tenant_id()||intent.subject!=context.subject()
        ||intent.result_size==0||intent.result_size>MAX_BYTES||intent.source_size==0||intent.source_size>MAX_BYTES{return Err(StoredCommitError::Binding);}
    row.validate_recovered_request(revision_context,lookup,&intent.request).map_err(|_|StoredCommitError::Binding)?;
    let precommit=artifacts.get_descriptor(context,row.precommit_artifact_id(),clock()).map_err(|_|StoredCommitError::Artifact)?;
    if !readable_intent(&precommit)||precommit.artifact_id!=row.precommit_artifact_id()||precommit.sha256!=intent.request.transaction_receipt_sha256(){return Err(StoredCommitError::Artifact);}
    let precommit_bytes=artifacts.download(context,precommit.artifact_id,clock()).map_err(|_|StoredCommitError::Artifact)?;
    if precommit_bytes.len()as u64!=precommit.size_bytes||precommit_bytes.len()as u64>MAX_INTENT_BYTES||ContentDigest::of(&precommit_bytes)!=precommit.sha256{return Err(StoredCommitError::Artifact);}
    let Some(archive)=archive else{return Ok(O::LegacyManifestRequired)};
    if archive.expected_source_sha256()!=*intent.source_sha256.as_bytes()||archive.expected_source_size()!=intent.source_size
        ||intent.request.source_artifact_id().public_id()!=archive.source_artifact_id().as_str()
        ||intent.request.expected_head().revision_id().map(|r|r.public_id()).as_deref()!=Some(archive.base_revision().as_str())
        ||intent.request.operation_plan_sha256().as_bytes()!=&archive.compiled_plan_sha256(){return Err(StoredCommitError::Binding);}
    archive.verify_precommit(&precommit_bytes,*intent.result_sha256.as_bytes(),intent.result_size).map_err(|_|StoredCommitError::Binding)?;
    observe_authenticated_intent(artifacts,revisions,context,revision_context,&intent,&mut clock).map(O::Registered)
}
