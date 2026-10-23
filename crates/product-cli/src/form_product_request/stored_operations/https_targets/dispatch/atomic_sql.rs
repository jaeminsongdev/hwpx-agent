//! Consuming server bridge to the original SQL26 policy-bound coordinator, never a transport/registry grant.
use super::*;
use super::super::routing::{HttpsTargetManifestError,atomic_sql::HttpsAtomicSqlJobRun};
use crate::stored_revision_commit::job::StoredJobRunReport;
use domain_ir::{RouteContext,CapabilityRouteCatalog,TransactionId};
use revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::LocalPostgresStoredRevisionJobsRepository as SqlRepository;

#[derive(Debug,Error)]
pub enum CommonHttpsSqlError{
    #[error("COMMON_HTTPS_SQL_OPERATION_KIND_DENIED")]OperationKind,
    #[error("COMMON_HTTPS_SQL_CURRENT_ROUTE_UNAVAILABLE")]CurrentRoute,
    #[error("COMMON_HTTPS_SQL_ORIGINAL_MANIFEST_OR_COORDINATOR_DENIED")]Manifest(#[from]HttpsTargetManifestError),
}
impl PreparedStoredProductOperation{
    /// Trusted authenticated server entry only; request/manifest/lookup data are not execution authority.
    /// # Errors
    /// Rejects other operation kinds before reading routes or creating SQL/job/workspace effects.
    /// Uses one current route snapshot for the original manifest, then moves the same callback
    /// into the unchanged automatic guards and SQL policy-in-CAS coordinator. No output/source,
    /// validator, revision service, CAS callback or fallback/retry is supplied by the caller.
    #[allow(clippy::too_many_arguments)]
    pub fn run_atomic_https_sql_job<R,B,S,P,F,A,Q>(self,provider:&StoredFormProvider<'_,R,B,S,SqlRepository>,repository:&P,
        transaction:TransactionId,run:HttpsAtomicSqlJobRun<'_>,mut current:F,before_claim:A,clock:Q)->Result<StoredJobRunReport,CommonHttpsSqlError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,P:HttpsTargetPolicyRepository,
        F:FnMut()->Result<(RouteContext,CapabilityRouteCatalog,u64),()>,A:FnOnce(ContentDigest)->Result<(),()>,Q:FnMut()->u64{
        let Self::HttpsTargets(product)=self else{return Err(CommonHttpsSqlError::OperationKind)};
        let(context,catalog,now)=current().map_err(|_|CommonHttpsSqlError::CurrentRoute)?;
        let manifest=(*product).prepare_execution_manifest(provider,repository,&context,&catalog,transaction,now)?;
        Ok(manifest.run_atomic_sql_job(provider,repository,run,current,before_claim,clock)?)
    }
}
