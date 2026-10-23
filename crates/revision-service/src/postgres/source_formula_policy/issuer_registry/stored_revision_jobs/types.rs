use super::*;
use artifact_service::{ArtifactDescriptor, ArtifactKind, StorageState, ValidationState};

/// Syntactically checked server-received lease. Only the SQL authority check can qualify it.
#[derive(Clone, Copy)]
pub struct StoredJobLease(RevisionLeaseIdentity);
impl StoredJobLease {
    /// # Errors
    /// Rejects nil identities, attempts outside1..10 and mismatched fencing; mints no authority.
    pub fn new(identity: RevisionLeaseIdentity) -> Result<Self, RevisionError> {
        if [identity.idempotency_key,identity.job_id,identity.agent_instance_id,identity.execution_id,identity.authorization_id]
            .iter().any(Uuid::is_nil) || !(1..=10).contains(&identity.attempt_no)
            || identity.fencing_token != i64::from(identity.attempt_no) { return Err(RevisionError::InvalidRequest); }
        Ok(Self(identity))
    }
    #[must_use]
    pub const fn identity(self) -> RevisionLeaseIdentity { self.0 }
}
impl PartialEq for StoredJobLease {
    fn eq(&self, other: &Self) -> bool {
        let (a,b)=(self.0,other.0);
        (a.idempotency_key,a.job_id,a.agent_instance_id,a.execution_id,a.attempt_no,a.fencing_token,a.authorization_id)
            ==(b.idempotency_key,b.job_id,b.agent_instance_id,b.execution_id,b.attempt_no,b.fencing_token,b.authorization_id)
    }
}
impl Eq for StoredJobLease {}
impl fmt::Debug for StoredJobLease { fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("StoredJobLease(<redacted>)")} }

#[derive(Clone)]
pub struct StoredCommitRegistration {
    pub(super) lease: StoredJobLease,
    pub(super) request: RevisionCommitRequest,
    pub(super) intent: ArtifactId,
    pub(super) intent_sha: ContentDigest,
    pub(super) precommit: ArtifactId,
}
impl StoredCommitRegistration {
    /// Server-owned descriptors must already have passed full service readback.
    /// # Errors
    /// Rejects wrong kinds/state/media/size, aliases or a precommit hash different from the request.
    pub fn new(lease: StoredJobLease, request: RevisionCommitRequest, result: &ArtifactDescriptor,
        intent: &ArtifactDescriptor, precommit: &ArtifactDescriptor) -> Result<Self, RevisionError> {
        RevisionCommitLease::bind(lease.identity(),&request)?;
        let available=|d:&ArtifactDescriptor|d.storage_state==StorageState::Available
            &&d.validation_state==ValidationState::Verified&&d.quarantine_reason.is_none();
        let receipt=|d:&ArtifactDescriptor|available(d)&&d.kind==ArtifactKind::Receipt&&d.media_type.as_str()=="application/json"
            &&(1..=65536).contains(&d.size_bytes);
        if !receipt(intent)||!receipt(precommit)||!available(result)||result.kind!=ArtifactKind::Result
            ||result.media_type.as_str()!="application/vnd.hancom.hwpx+zip"||!(1..=33554432).contains(&result.size_bytes)
            ||result.artifact_id!=request.result_artifact_id()||precommit.sha256!=request.transaction_receipt_sha256()
            ||[request.source_artifact_id(),result.artifact_id].iter().any(|id|*id==intent.artifact_id||*id==precommit.artifact_id)
            ||intent.artifact_id==precommit.artifact_id||intent.sha256==precommit.sha256 { return Err(RevisionError::InvalidRequest); }
        Ok(Self{lease,request,intent:intent.artifact_id,intent_sha:intent.sha256,precommit:precommit.artifact_id})
    }
    #[must_use]
    pub const fn request(&self)->&RevisionCommitRequest {&self.request}
    #[must_use]
    pub const fn lease(&self)->StoredJobLease {self.lease}
}
impl fmt::Debug for StoredCommitRegistration {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("StoredCommitRegistration(<redacted>)")} }

#[derive(Clone, Eq, PartialEq)]
pub struct StoredCommitIntentRecord {
    pub(super) tenant:TenantId,pub(super) subject:SubjectDigest,pub(super) project:ProjectId,
    pub(super) lease:StoredJobLease,pub(super) commit:CommitId,pub(super) revision:RevisionId,
    pub(super) result:ArtifactId,pub(super) summary:ContentDigest,pub(super) request_sha:ContentDigest,
    pub(super) intent:ArtifactId,pub(super) intent_sha:ContentDigest,pub(super) precommit:ArtifactId,
}
impl StoredCommitIntentRecord {
    /// Expected model for a trusted repository implementation, not a DB/authorization attestation.
    /// # Errors
    /// Propagates canonical serialization failure; SQL adapters compare this to the actual row.
    pub fn expected(context:&RevisionRequestContext,registration:&StoredCommitRegistration)->Result<Self,RevisionError>{
        let request=&registration.request;
        Ok(Self{tenant:context.tenant_id(),subject:context.subject(),project:request.project_id(),lease:registration.lease,
            commit:request.commit_id(),revision:request.new_revision_id(),result:request.result_artifact_id(),
            summary:request.validation_summary_sha256(),request_sha:request.canonical_sha256()?,intent:registration.intent,
            intent_sha:registration.intent_sha,precommit:registration.precommit})
    }
    /// # Errors
    /// Rejects any different context, job/lease, request or artifact identity.
    pub fn validate_for(&self,context:&RevisionRequestContext,registration:&StoredCommitRegistration)->Result<(),RevisionError>{
        if self!=&Self::expected(context,registration)? {return Err(RevisionError::RepositoryFailure);}Ok(())
    }
    /// Checks a saved encrypted request against a freshly read registered row and exact locator.
    /// This does not expose/renew a lease, inspect current result availability, or authorize CAS.
    /// # Errors
    /// Rejects foreign context, locator, canonical request or bound commit/result identities.
    pub fn validate_recovered_request(&self,context:&RevisionRequestContext,lookup:StoredCommitIntentLookup,request:&RevisionCommitRequest)->Result<(),RevisionError>{
        let lease=self.lease.identity();
        if self.tenant!=context.tenant_id()||self.subject!=context.subject()||self.project!=lookup.project
            ||lease.idempotency_key!=lookup.key||lease.job_id!=lookup.job||lease.attempt_no!=lookup.attempt
            ||request.project_id()!=self.project||request.commit_id()!=self.commit||request.new_revision_id()!=self.revision
            ||request.result_artifact_id()!=self.result||request.validation_summary_sha256()!=self.summary||request.canonical_sha256()!=Ok(self.request_sha)
            ||[self.result,self.intent,self.precommit].iter().collect::<std::collections::BTreeSet<_>>().len()!=3{
            return Err(RevisionError::InvalidRequest);
        }Ok(())
    }
    #[must_use] pub const fn intent_artifact_id(&self)->ArtifactId{self.intent}
    #[must_use] pub const fn intent_sha256(&self)->ContentDigest{self.intent_sha}
    #[must_use] pub const fn precommit_artifact_id(&self)->ArtifactId{self.precommit}
    #[must_use] pub const fn request_sha256(&self)->ContentDigest{self.request_sha}
}
impl fmt::Debug for StoredCommitIntentRecord {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("StoredCommitIntentRecord(<redacted>)")} }

#[derive(Clone,Copy)]
pub struct StoredCommitIntentLookup{pub(super) project:ProjectId,pub(super) key:Uuid,pub(super) job:Uuid,pub(super) attempt:i32}
impl StoredCommitIntentLookup{
    /// # Errors
    /// Rejects nil job/key and invalid attempts. Missing rows never authorize retry.
    pub fn new(project:ProjectId,key:Uuid,job:Uuid,attempt:i32)->Result<Self,RevisionError>{
        if key.is_nil()||job.is_nil()||!(1..=10).contains(&attempt){return Err(RevisionError::InvalidRequest);}Ok(Self{project,key,job,attempt})
    }
    #[must_use]pub const fn project_id(self)->ProjectId{self.project}
    #[must_use]pub const fn idempotency_key(self)->Uuid{self.key}
    #[must_use]pub const fn job_id(self)->Uuid{self.job}
    #[must_use]pub const fn attempt_no(self)->i32{self.attempt}
}
impl fmt::Debug for StoredCommitIntentLookup {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("StoredCommitIntentLookup(<redacted>)")} }

/// Trusted server repository boundary. Neither an arbitrary artifact nor a fake row grants routing.
pub trait StoredRevisionJobRepository:RevisionRepository{
    /// # Errors
    /// Requires real validating lease/authority and immutable exact registration. Ack loss is Unknown.
    fn register_commit_intent(&self,context:&RevisionRequestContext,registration:&StoredCommitRegistration)->Result<StoredCommitIntentRecord,RevisionError>;
    /// # Errors
    /// Enforces current scope/intent access; None is no observation, not a no-effect assertion.
    fn read_commit_intent(&self,context:&RevisionRequestContext,lookup:StoredCommitIntentLookup)->Result<Option<StoredCommitIntentRecord>,RevisionError>;
}
