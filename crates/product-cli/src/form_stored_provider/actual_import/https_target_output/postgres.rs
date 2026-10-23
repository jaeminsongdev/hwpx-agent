//! Actual exact25 SQL selection/registration/revocation. Not an attested external issuer or policy execution lease.
use super::*;
use super::registration::{HttpsTargetPolicyRegistrationRepository,HttpsPolicyRegistration,HttpsPolicyRegistrationError};
use revision_service::{RevisionError,RevisionRequestContext,postgres::source_formula_policy::issuer_registry::stored_revision_jobs::{
    LocalPostgresStoredRevisionJobsRepository as Repository,https_policy::{HttpsPolicyReadRequest,HttpsPolicyRecord,HttpsPolicyRegistrationRequest,HttpsPolicySource}}};
pub struct PostgresHttpsTargetPolicyProvider{repository:Repository}
impl fmt::Debug for PostgresHttpsTargetPolicyProvider{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PostgresHttpsTargetPolicyProvider(<redacted>)")}}
impl PostgresHttpsTargetPolicyProvider{
    #[must_use]pub const fn new(repository:Repository)->Self{Self{repository}}
    /// # Errors
    /// Authenticated SQL editor, latest-version CAS and commit acknowledgement; no deletion or automatic retry.
    /// Binding is data only. SQL authorizes the fixed principal, tenant/project and requested latest version.
    pub fn revoke(&self,context:&RevisionRequestContext,binding:&SourcePolicyBinding)->Result<(),RevisionError>{
        if context.tenant_id()!=binding.tenant{return Err(RevisionError::InvalidRequest);}
        let s=HttpsPolicyReadRequest::new(binding.project,binding.branch,binding.document.as_str().into(),RevisionHead::new(Some(binding.source_revision),binding.source_head_generation)?)?;
        self.repository.revoke_https_policy(context,&s,binding.policy_version,binding.policy_generation)
    }
}
fn request(s:&HttpsTargetPolicyScope)->Result<HttpsPolicyReadRequest,RevisionError>{HttpsPolicyReadRequest::new(s.project(),s.branch(),s.document().as_str().into(),s.head())}
fn version(r:HttpsPolicyRecord,s:&HttpsTargetPolicyScope)->Result<HttpsTargetPolicyVersion,E>{
    if r.source_result!=s.source_artifact()||r.source_package!=s.source_sha256(){return Err(E::Binding);}
    Ok(HttpsTargetPolicyVersion{artifact:r.policy_artifact,digest:r.policy_digest,binding:SourcePolicyBinding{tenant:r.tenant,project:r.project,branch:r.branch,document:s.document().clone(),
        source_revision:r.source_head.revision_id().ok_or(E::Binding)?,source_head_generation:r.source_head.generation(),source_result_artifact:r.source_result,
        source_package_sha256:r.source_package,source_provenance_sha256:r.source_provenance,observed_graph_sha256:r.observed_graph,policy_version:r.version,
        policy_generation:r.generation,creator_subject:r.creator}})
}
impl HttpsTargetPolicyRepository for PostgresHttpsTargetPolicyProvider{
    fn read_current(&self,s:&HttpsTargetPolicyScope)->Result<HttpsTargetPolicyVersion,E>{
        let context=RevisionRequestContext::new(s.tenant(),s.subject());
        let r=self.repository.read_https_policy(&context,&request(s).map_err(|_|E::Repository)?).map_err(|_|E::Repository)?;version(r,s)
    }
}
impl HttpsTargetPolicyRegistrationRepository for PostgresHttpsTargetPolicyProvider{
    fn register(&self,s:&HttpsTargetPolicyScope,r:&HttpsPolicyRegistration)->Result<HttpsTargetPolicyVersion,HttpsPolicyRegistrationError>{
        use HttpsPolicyRegistrationError as F;let b=&r.version().binding;
        if b.tenant!=s.tenant()||b.project!=s.project()||b.branch!=s.branch()||&b.document!=s.document()||b.creator_subject!=s.subject()
            ||Some(b.source_revision)!=s.head().revision_id()||b.source_head_generation!=s.head().generation()||b.source_result_artifact!=s.source_artifact()
            ||b.source_package_sha256!=s.source_sha256()||b.policy_generation!=r.expected_generation()+1{return Err(F::Source);}
        let context=RevisionRequestContext::new(s.tenant(),s.subject());
        let req=HttpsPolicyRegistrationRequest::new(request(s).map_err(|_|F::Source)?,r.expected_generation(),b.policy_version,r.version().artifact,r.version().digest,
            HttpsPolicySource{result:b.source_result_artifact,package:b.source_package_sha256,provenance:b.source_provenance_sha256,graph:b.observed_graph_sha256}).map_err(|_|F::Source)?;
        let registered=self.repository.register_https_policy(&context,&req).map_err(|e|if e==RevisionError::CommitOutcomeUnknown{F::OutcomeUnknown}else{F::Repository})?;
        // Any post-commit reply mismatch is unknown, not a confirmed no-effect failure.
        version(registered,s).map_err(|_|F::OutcomeUnknown)
    }
}
