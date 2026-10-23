//! Separate exact-schema23 server connector. No migrations/grants, retry, Native or route issuance.
use super::*;
use crate::{CommitId,CommitOutcome,RevisionCommitRequest,RevisionId,RevisionNode};
use crate::postgres::RevisionLeaseIdentity;
mod admission;
mod types;
pub mod lifecycle;
pub mod request_lookup;
pub use types::{StoredJobLease,StoredCommitRegistration,StoredCommitIntentRecord,StoredCommitIntentLookup,StoredRevisionJobRepository};

const MIGRATION23:&[u8]=include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"),"/../../migrations/postgres/0023_p09_stored_revision_jobs.up.sql"));
const REGISTER:&str="SELECT hwpx_agent.register_stored_revision_commit_intent_v1(
    $1,$2,$3::character(64),$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14::character(64),
    $15::character(64),$16,$17::character(64),$18) AS intent";
const READ:&str="SELECT tenant_id,project_id,idempotency_key,job_id,attempt_no,fencing_token,
    subject_sha256::text,agent_instance_id,execution_id,authorization_id,commit_id,new_revision_id,
    result_artifact_id,validation_summary_sha256::text,commit_request_sha256::text,
    intent_artifact_id,intent_sha256::text,precommit_artifact_id
    FROM hwpx_agent.read_stored_revision_commit_intent_v1($1,$2,$3::character(64),$4,$5,$6)";

#[derive(Clone)]
pub struct LocalPostgresStoredRevisionJobsRepository{inner:LocalPostgresRevisionRepository,lease:Option<StoredJobLease>,request_lookup_qualified:bool}
impl fmt::Debug for LocalPostgresStoredRevisionJobsRepository{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("LocalPostgresStoredRevisionJobsRepository(<redacted>)")}}
impl LocalPostgresStoredRevisionJobsRepository{
    /// Checks exact schema1..23, existing policy guards and new table/function/trigger boundaries.
    /// # Errors
    /// Rejects unsafe privileges, altered bodies/metadata or transport failure; never installs SQL.
    pub fn connect(config:&LocalPostgresRevisionConfig,context:RevisionRequestContext,lease:Option<StoredJobLease>)->Result<Self,RevisionError>{
        Self::connect_mode(config,context,lease,false)
    }
    /// Explicit schema24 path. Does not migrate/grant; every schema23 guard remains mandatory.
    /// # Errors
    /// Requires exact schema1..24 and an admitted read-only lookup function/privilege boundary.
    pub fn connect_with_request_lookup(config:&LocalPostgresRevisionConfig,context:RevisionRequestContext,lease:Option<StoredJobLease>)->Result<Self,RevisionError>{
        Self::connect_mode(config,context,lease,true)
    }
    fn connect_mode(config:&LocalPostgresRevisionConfig,context:RevisionRequestContext,lease:Option<StoredJobLease>,lookup:bool)->Result<Self,RevisionError>{
        let mut client=Config::new().host("127.0.0.1").port(config.port).dbname(&config.database).user(&config.user)
            .password(config.password.as_bytes()).connect_timeout(Duration::from_secs(3))
            .application_name("hwpx-agent-local-stored-revision-schema23")
            .options("-c statement_timeout=5000 -c lock_timeout=1000 -c idle_in_transaction_session_timeout=5000 -c transaction_timeout=10000 -c search_path=pg_catalog")
            .connect(NoTls).map_err(db_error)?;
        if lookup{admission::admit_with_lookup(&mut client)?;}else{admission::admit(&mut client)?;}
        admit_read_policies(&mut client)?;admit_guarded_writes(&mut client)?;
        admit_form_policy_security(&mut client)?;admit_policy_security(&mut client)?;admit_registry_security(&mut client)?;
        lifecycle::admit_controls(&mut client)?;
        Ok(Self{inner:LocalPostgresRevisionRepository{context,lease:None,client:Arc::new(Mutex::new(client))},lease,request_lookup_qualified:lookup})
    }
    /// Same admitted connection/context with syntactically checked received identity; SQL still
    /// checks the real unconsumed capability on registration and commit.
    #[must_use] pub fn with_received_lease(&self,lease:StoredJobLease)->Self{Self{inner:self.inner.clone(),lease:Some(lease),request_lookup_qualified:self.request_lookup_qualified}}
}
impl RevisionRepository for LocalPostgresStoredRevisionJobsRepository{
    fn authorize_context(&self,context:&RevisionRequestContext)->Result<(),RevisionError>{self.inner.authorize_context(context)}
    fn compare_and_swap(&self,context:&RevisionRequestContext,request:&RevisionCommitRequest)->Result<CommitOutcome,RevisionError>{
        self.authorize_context(context)?;
        let lease=self.lease.ok_or(RevisionError::InvalidRequest)?;
        let bound=RevisionCommitLease::bind(lease.identity(),request)?;
        let repository=LocalPostgresRevisionRepository{context:self.inner.context.clone(),lease:Some(bound),client:Arc::clone(&self.inner.client)};
        repository.compare_and_swap(context,request)
    }
    fn head(&self,tenant:TenantId,project:ProjectId,branch:BranchId)->Result<RevisionHead,RevisionError>{self.inner.head(tenant,project,branch)}
    fn node(&self,tenant:TenantId,project:ProjectId,revision:RevisionId)->Result<RevisionNode,RevisionError>{self.inner.node(tenant,project,revision)}
}
impl StoredRevisionJobRepository for LocalPostgresStoredRevisionJobsRepository{
    fn register_commit_intent(&self,context:&RevisionRequestContext,registration:&StoredCommitRegistration)->Result<StoredCommitIntentRecord,RevisionError>{
        self.authorize_context(context)?;
        if self.lease!=Some(registration.lease){return Err(RevisionError::InvalidRequest);}
        let identity=registration.lease.identity();let request=&registration.request;
        let expected=StoredCommitIntentRecord::expected(context,registration)?;
        self.inner.scoped(context.tenant_id(),IsolationLevel::ReadCommitted,|tx|{
            let result=tx.query_one(REGISTER,&[&context.tenant_id().as_uuid(),&request.project_id().as_uuid(),&context.subject().hex(),
                &identity.idempotency_key,&identity.job_id,&identity.agent_instance_id,&identity.execution_id,&identity.attempt_no,
                &identity.fencing_token,&identity.authorization_id,&request.commit_id().as_uuid(),&request.new_revision_id().as_uuid(),
                &request.result_artifact_id().as_uuid(),&request.validation_summary_sha256().hex(),&request.canonical_sha256()?.hex(),
                &registration.intent.as_uuid(),&registration.intent_sha.hex(),&registration.precommit.as_uuid()]).map_err(db_error)?;
            if value::<Uuid>(&result,"intent")?!=registration.intent.as_uuid(){return Err(RevisionError::RepositoryFailure);}
            let lookup=StoredCommitIntentLookup::new(request.project_id(),identity.idempotency_key,identity.job_id,identity.attempt_no)?;
            let row=read(tx,context,lookup)?.ok_or(RevisionError::RepositoryFailure)?;
            if row!=expected{return Err(RevisionError::RepositoryFailure);}Ok(row)
        })
    }
    fn read_commit_intent(&self,context:&RevisionRequestContext,lookup:StoredCommitIntentLookup)->Result<Option<StoredCommitIntentRecord>,RevisionError>{
        self.authorize_context(context)?;
        self.inner.scoped(context.tenant_id(),IsolationLevel::RepeatableRead,|tx|read(tx,context,lookup))
    }
}
fn read(tx:&mut ::postgres::Transaction<'_>,context:&RevisionRequestContext,lookup:StoredCommitIntentLookup)->Result<Option<StoredCommitIntentRecord>,RevisionError>{
    let Some(row)=tx.query_opt(READ,&[&context.tenant_id().as_uuid(),&lookup.project.as_uuid(),&context.subject().hex(),
        &lookup.key,&lookup.job,&lookup.attempt]).map_err(db_error)? else{return Ok(None)};
    let identity=RevisionLeaseIdentity{idempotency_key:value(&row,"idempotency_key")?,job_id:value(&row,"job_id")?,
        agent_instance_id:value(&row,"agent_instance_id")?,execution_id:value(&row,"execution_id")?,attempt_no:value(&row,"attempt_no")?,
        fencing_token:value(&row,"fencing_token")?,authorization_id:value(&row,"authorization_id")?};
    let lease=StoredJobLease::new(identity)?;
    let record=StoredCommitIntentRecord{tenant:TenantId::new(value(&row,"tenant_id")?).map_err(|_|RevisionError::RepositoryFailure)?,
        subject:SubjectDigest::parse(&value::<String>(&row,"subject_sha256")?).map_err(|_|RevisionError::RepositoryFailure)?,
        project:ProjectId::parse(&format!("prj_{}",value::<Uuid>(&row,"project_id")?.simple()))?,lease,
        commit:CommitId::parse(&format!("cmt_{}",value::<Uuid>(&row,"commit_id")?.simple()))?,
        revision:RevisionId::parse(&format!("rev_{}",value::<Uuid>(&row,"new_revision_id")?.simple()))?,
        result:artifact_id(value(&row,"result_artifact_id")?)?,summary:row_digest(&row,"validation_summary_sha256")?,
        request_sha:row_digest(&row,"commit_request_sha256")?,intent:artifact_id(value(&row,"intent_artifact_id")?)?,
        intent_sha:row_digest(&row,"intent_sha256")?,precommit:artifact_id(value(&row,"precommit_artifact_id")?)?};
    if record.tenant!=context.tenant_id()||record.subject!=context.subject()||record.project!=lookup.project
        ||identity.idempotency_key!=lookup.key||identity.job_id!=lookup.job||identity.attempt_no!=lookup.attempt
        ||[record.result,record.intent,record.precommit].iter().collect::<std::collections::BTreeSet<_>>().len()!=3{
        return Err(RevisionError::RepositoryFailure);
    }
    Ok(Some(record))
}
