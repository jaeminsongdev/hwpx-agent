//! Authenticated server registration of strictly validated HTTPS policy data. No public transport or execution grant.
use super::*;
use artifact_service::{FileName,IngestRequest,MediaType};
use domain_ir::ExternalTargetKind;
pub struct HttpsPolicyRegistration{version:HttpsTargetPolicyVersion,expected:u64}
impl HttpsPolicyRegistration{
    #[must_use]pub const fn version(&self)->&HttpsTargetPolicyVersion{&self.version}
    #[must_use]pub const fn expected_generation(&self)->u64{self.expected}
}
impl fmt::Debug for HttpsPolicyRegistration{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("HttpsPolicyRegistration(<redacted>; data_not_authority)")}}
pub trait HttpsTargetPolicyRegistrationRepository:HttpsTargetPolicyRepository{
    /// # Errors
    /// Atomically authorize editor/actual artifact management/head/generation CAS and exact row readback.
    /// A lost commit acknowledgement must remain OutcomeUnknown, with no retry.
    fn register(&self,scope:&HttpsTargetPolicyScope,request:&HttpsPolicyRegistration)->Result<HttpsTargetPolicyVersion,HttpsPolicyRegistrationError>;
}
pub struct PreparedHttpsPolicyRegistration<'a>{source:&'a StoredImportedDocumentForms,binding:SourcePolicyBinding,bytes:Vec<u8>,expected:u64}
impl fmt::Debug for PreparedHttpsPolicyRegistration<'_>{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedHttpsPolicyRegistration(<redacted>; no_execution_authority)")}}
#[derive(Debug,Error,Eq,PartialEq)]
pub enum HttpsPolicyRegistrationError{
    #[error("HTTPS_POLICY_REGISTRATION_SOURCE_DENIED")]Source,
    #[error("HTTPS_POLICY_REGISTRATION_PAYLOAD_DENIED")]Payload,
    #[error("HTTPS_POLICY_REGISTRATION_ARTIFACT_DENIED")]Artifact,
    #[error("HTTPS_POLICY_REGISTRATION_REPOSITORY_DENIED")]Repository,
    #[error("HTTPS_POLICY_REGISTRATION_OUTCOME_UNKNOWN_NO_RETRY")]OutcomeUnknown,
}
/// Retained encrypted Evidence is never deleted, even on CAS/acknowledgement failure.
#[derive(Debug,Error)]
#[error("{error}; encrypted_policy_retained_if_ingested")]
pub struct HttpsPolicyPublicationFailure{pub error:HttpsPolicyRegistrationError,pub retained_policy_artifact:Option<ArtifactId>}
fn failure(error:HttpsPolicyRegistrationError,retained:Option<ArtifactId>)->HttpsPolicyPublicationFailure{
    HttpsPolicyPublicationFailure{error,retained_policy_artifact:retained}
}
impl StoredImportedDocumentForms{
    /// # Errors
    /// Trusted server policy input only: authenticated write scope, exact fresh source, finite HTTPS-only approvals and bounded generated payload.
    /// Public change requests cannot select this policy or call a transport to issue one.
    pub fn prepare_https_policy_registration<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,selected:&ExternalLinkPolicy,
        expected_generation:u64,limits:LinkReferenceLimits,now:u64)->Result<PreparedHttpsPolicyRegistration<'_>,HttpsPolicyRegistrationError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        use HttpsPolicyRegistrationError as F;
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite)||expected_generation>=i64::MAX as u64{return Err(F::Source);}
        self.fresh_source(provider,now).map_err(|_|F::Source)?;
        if !selected.allow_https||selected.allow_mailto||selected.allow_managed_documents
            ||selected.approvals.is_empty()||selected.approvals.iter().any(|v|v.kind!=ExternalTargetKind::Https){return Err(F::Payload);}
        selected.validated_external_targets(limits).map_err(|_|F::Payload)?;
        let s=&self.source;let r=&self.receipt.imported;
        let binding=SourcePolicyBinding{tenant:s.scope.tenant,project:s.scope.project,branch:s.scope.branch,document:s.scope.document.clone(),
            source_revision:s.head.revision_id().ok_or(F::Source)?,source_head_generation:s.head.generation(),source_result_artifact:s.artifact,source_package_sha256:s.digest,
            source_provenance_sha256:ContentDigest::parse(&hex::encode(r.source_provenance_sha256)).map_err(|_|F::Source)?,
            observed_graph_sha256:ContentDigest::parse(&hex::encode(r.graph_sha256)).map_err(|_|F::Source)?,policy_version:uuid::Uuid::new_v4(),policy_generation:expected_generation+1,
            creator_subject:s.scope.subject};
        revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::https_policy::HttpsPolicyReadRequest::new(
            binding.project,binding.branch,binding.document.as_str().into(),s.head).map_err(|_|F::Source)?;
        let bytes=serde_json::to_vec(&serde_json::json!({"schema_version":HTTPS_TARGET_POLICY_SCHEMA,"binding":binding,"policy":selected})).map_err(|_|F::Payload)?;
        if bytes.is_empty()||bytes.len()>MAX_POLICY_BYTES{return Err(F::Payload);}
        let decoded:Envelope=serde_json::from_slice(&bytes).map_err(|_|F::Payload)?;
        if decoded.schema_version!=HTTPS_TARGET_POLICY_SCHEMA||decoded.binding!=binding||decoded.policy!=*selected{return Err(F::Payload);}
        self.fresh_source(provider,now).map_err(|_|F::Source)?;
        Ok(PreparedHttpsPolicyRegistration{source:self,binding,bytes,expected:expected_generation})
    }
}
impl PreparedHttpsPolicyRegistration<'_>{
    /// # Errors
    /// One-shot actual Evidence ingest/AEAD readback and SQL generation CAS. Retains every ingested policy on failure.
    /// Repository acknowledgement loss/readback mismatch is unknown, never a no-effect statement or retry permit.
    pub fn register<R,B,S,V,P>(self,provider:&StoredFormProvider<'_,R,B,S,V>,repository:&P,now:u64)
        ->Result<HttpsTargetPolicyVersion,HttpsPolicyPublicationFailure>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository,P:HttpsTargetPolicyRegistrationRepository{
        use HttpsPolicyRegistrationError as F;
        let Self{source,binding,bytes,expected}=self;
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(failure(F::Source,None));}
        source.fresh_source(provider,now).map_err(|_|failure(F::Source,None))?;
        let digest=ContentDigest::of(&bytes);
        let descriptor=provider.artifacts.ingest(provider.artifact_context,IngestRequest{bytes,kind:ArtifactKind::Evidence,
            media_type:MediaType::parse(HTTPS_TARGET_POLICY_MEDIA_TYPE).map_err(|_|failure(F::Artifact,None))?,
            file_name:FileName::parse("source-https-target-policy.json").map_err(|_|failure(F::Artifact,None))?},now).map_err(|_|failure(F::Artifact,None))?;
        let retained=Some(descriptor.artifact_id);let version=HttpsTargetPolicyVersion{binding,artifact:descriptor.artifact_id,digest};
        if descriptor.sha256!=digest{return Err(failure(F::Artifact,retained));}
        policy(source,provider,&version,now).map_err(|_|failure(F::Artifact,retained))?;
        source.fresh_source(provider,now).map_err(|_|failure(F::Source,retained))?;
        let registered=repository.register(&scope(source),&HttpsPolicyRegistration{version:version.clone(),expected}).map_err(|error|failure(error,retained))?;
        if registered!=version{return Err(failure(F::OutcomeUnknown,retained));}Ok(version)
    }
}
