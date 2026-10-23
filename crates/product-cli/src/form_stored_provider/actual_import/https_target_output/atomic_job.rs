//! Provider-internal execution bridge. Raw service/context fields remain private.
use super::*;
use crate::form_product_request::stored_operations::https_targets::routing::{PreparedHttpsTargetExecutionManifest,HttpsTargetManifestError};
use crate::form_product_request::stored_operations::https_targets::routing::atomic_sql::HttpsAtomicSqlJobRun;
use crate::stored_revision_commit::job::StoredJobRunReport;
use domain_ir::{RouteContext,CapabilityRouteCatalog};
use revision_service::{RevisionService,postgres::source_formula_policy::issuer_registry::stored_revision_jobs::{LocalPostgresStoredRevisionJobsRepository as SqlRepository,https_policy::HttpsPolicyRecord}};
type M=HttpsTargetManifestError;
impl PreparedHttpsTargetExecutionManifest{
    /// # Errors
    /// Current source/policy/route guards AND the exact26 policy guard inside the original SQL CAS transaction.
    /// The caller cannot substitute an unbound revision service, output, validator or CAS callback here.
    pub fn run_atomic_sql_job<R,B,S,P,F,A,Q>(&self,provider:&StoredFormProvider<'_,R,B,S,SqlRepository>,repository:&P,
        run:HttpsAtomicSqlJobRun<'_>,current:F,before_claim:A,clock:Q)->Result<StoredJobRunReport,HttpsTargetManifestError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,P:HttpsTargetPolicyRepository,
        F:FnMut()->Result<(RouteContext,CapabilityRouteCatalog,u64),()>,A:FnOnce(ContentDigest)->Result<(),()>,Q:FnMut()->u64{
        let(version,plan)=self.atomic_policy_data();let b=&version.binding;
        let bound=provider.revisions.repository().with_atomic_https_policy(HttpsPolicyRecord{tenant:b.tenant,project:b.project,branch:b.branch,document:b.document.as_str().into(),
            version:b.policy_version,generation:b.policy_generation,source_head:revision_service::RevisionHead::new(Some(b.source_revision),b.source_head_generation).map_err(|_|M::AtomicPolicy)?,
            source_result:b.source_result_artifact,source_package:b.source_package_sha256,source_provenance:b.source_provenance_sha256,observed_graph:b.observed_graph_sha256,
            policy_artifact:version.artifact,policy_digest:version.digest,creator:b.creator_subject},
            ContentDigest::parse(&hex::encode(plan)).map_err(|_|M::AtomicPolicy)?).map_err(|_|M::AtomicPolicy)?;
        let revisions=RevisionService::new(bound);
        self.with_verified_guarded_job_preparation(provider,repository,run.policy,run.commit,run.new_revision,run.limits,current,|job,source,mut validator|{
            // Callback exposes only registration DATA. SQL still requires a genuine live registered worker/lease.
            before_claim(job.claim().input().capability_sha).map_err(|_|M::AtomicPolicy)?;
            Ok::<_,M>(job.run_once(provider.artifacts,&revisions,provider.artifact_context,provider.revision_context,run.agent,run.execution,run.lease_seconds,
                run.event,run.workspace,source,&mut validator,clock))
        })?
    }
}
