//! The actual policy is revoked AFTER the last app check read and BEFORE the original atomic SQL CAS.
//! Only the repository's read callback injects timing; output, validator, CAS and production source are unchanged.
use super::*;
use std::cell::Cell;
use hwpx_agent_cli::form_product_request::stored_operations::https_targets::routing::atomic_sql::HttpsAtomicSqlJobRun;
type SqlPolicy=postgres::PostgresHttpsTargetPolicyProvider;
struct LateRevoke{sql:SqlPolicy,phase:Cell<usize>,last_reads:Cell<usize>,revoked:Cell<bool>}
impl HttpsTargetPolicyRepository for LateRevoke{
    fn read_current(&self,scope:&HttpsTargetPolicyScope)->Result<HttpsTargetPolicyVersion,StoredHttpsTargetError>{
        let version=self.sql.read_current(scope)?;
        if self.phase.get()==4{
            let reads=self.last_reads.get()+1;self.last_reads.set(reads);
            if reads==3{
                // Fresh read has completed. The next operation after this final guard is the ORIGINAL revision service commit.
                if self.revoked.replace(true){return Err(StoredHttpsTargetError::Repository);}
                self.sql.revoke(&context().map_err(|_|StoredHttpsTargetError::Repository)?,&version.binding)
                    .map_err(|_|StoredHttpsTargetError::Repository)?;
            }
        }
        Ok(version)
    }
}
pub fn execute()->Result<Value>{
    let a=artifacts()?;let ctx=actor()?;let rc=context()?;let revisions=RevisionService::new(repository()?);
    let provider=StoredFormProvider::bind(&a,&revisions,&ctx,&rc,project()?,branch()?,DocumentId::parse("actual-form-document")?)?;
    let sql=SqlPolicy::new(repository()?);let policy=LateRevoke{sql,phase:Cell::new(0),last_reads:Cell::new(0),revoked:Cell::new(false)};
    let wire=serde_json::to_vec(&load("https-public-request.json")?)?;
    let HttpsTargetRequestEntry::Prepared(product)=Product::prepare_https_targets_or_observe_json(&provider,&policy,&wire,limits()?,10)?else{return Err("HTTPS_LATE_FRESH_REQUEST_REQUIRED".into())};
    let(c,r)=routes()?;let prepared=product.prepare_execution_manifest(&provider,&policy,&c,&r,domain_ir::TransactionId::parse("https-late-revoke544")?,10)?;
    check(prepared.require_current_product_route(&provider,&policy,&c,&r,10).is_err(),"HTTPS_LATE_ROUTE_STAYS_DENIED")?;
    let source=read_id(&state()?,"source")?;let original=a.download(&ctx,source,10)?;let workspace=owned_root()?.join("https-late-workspace");
    let report=prepared.run_atomic_sql_job(&provider,&policy,HttpsAtomicSqlJobRun{policy:identity::StoredJobPolicy{max_delay_seconds:4,..Default::default()},
        commit:commit(5441)?,new_revision:revision(5442)?,limits:Default::default(),agent:id(130),execution:id(5443),lease_seconds:120,
        event:ContentDigest::of(b"https-late-revoke544-event"),workspace:&workspace},
        ||{policy.phase.set(policy.phase.get()+1);let(c,r)=routes().map_err(|_|())?;Ok((c,r,10))},
        |cap|{let mut c=raw("p09_revision_284",&value("P09_SQL23_REVISION_PASSWORD").map_err(|_|())?).map_err(|_|())?;scoped(&mut c).map_err(|_|())?;
            setup::register(&mut c,130,cap).map_err(|_|())},||10)?;
    check(policy.phase.get()==4&&policy.last_reads.get()==3&&policy.revoked.get(),"HTTPS_LATE_EXACT_FINAL_READ_REVOCATION")?;
    check(report.stage==StoredJobRunStage::Transaction&&report.binding_error.is_none()&&report.repository_error.is_none()
        &&report.cas_error==Some(StoredCommitError::Revision)&&report.transaction.as_ref().is_some_and(|v|v.is_err())
        &&report.revision_receipt.is_none()&&report.completion.is_none()&&report.unknown.is_none(),"HTTPS_LATE_SQL_CAS_DENIED_NOT_APP_GUARD_OR_SUCCESS")?;
    let lease=report.lease.ok_or("HTTPS_LATE_ACTUAL_LEASE_REQUIRED")?;
    let registered=report.registered_intent.as_ref().ok_or("HTTPS_LATE_REGISTERED_INTENT_REQUIRED")?;
    check(report.registration_response.as_ref()==Some(registered)&&revisions.repository().read_commit_intent(&rc,
        StoredCommitIntentLookup::new(project()?,lease.identity().idempotency_key,lease.identity().job_id,1)?)?.as_ref()==Some(registered),"HTTPS_LATE_ACTUAL_REGISTERED_INTENT_RETAINED")?;
    let result=report.result.as_ref().ok_or("HTTPS_LATE_RESULT_REQUIRED")?;verify_output(&a.download(&ctx,result.artifact_id,11)?)?;
    for d in[report.intent.as_ref(),report.precommit.as_ref()]{let d=d.ok_or("HTTPS_LATE_EVIDENCE_REQUIRED")?;
        check(!a.download(&ctx,d.artifact_id,11)?.is_empty(),"HTTPS_LATE_AEAD_EVIDENCE_RETAINED")?;}
    check(revisions.head(&rc,project()?,branch()?)?==RevisionHead::new(Some(revision(20)?),1)?
        &&a.download(&ctx,source,11)?==original,"HTTPS_LATE_HEAD_SOURCE_UNCHANGED")?;
    let mut row=observe()?;row["state"]=json!("PASS_HTTPS_REAL_SQL26_LATE_REVOCATION_DENIES_ORIGINAL_CAS_RETAINS_EVIDENCE");
    row["last_app_guard_reads_completed"]=json!(true);row["original_SQL_CAS_denied"]=json!(true);row["result_intent_precommit_AEAD_retained"]=json!(true);Ok(row)
}
pub fn observe()->Result<Value>{
    let a=artifacts()?;let ctx=actor()?;let rc=context()?;let revisions=RevisionService::new(repository()?);
    let provider=StoredFormProvider::bind(&a,&revisions,&ctx,&rc,project()?,branch()?,DocumentId::parse("actual-form-document")?)?;
    let wire=serde_json::to_vec(&load("https-public-request.json")?)?;
    let HttpsTargetRequestEntry::Existing(job)=Product::prepare_https_targets_or_observe_json(&provider,&NoPolicyReads,&wire,limits()?,20)?else{return Err("HTTPS_LATE_EXISTING_NO_PREPARATION_REQUIRED".into())};
    check(job.state()==StoredJobState::InProgress&&job.attempt_no()==1&&job.result_revision_id().is_none()
        &&revisions.head(&rc,project()?,branch()?)?==RevisionHead::new(Some(revision(20)?),1)?,"HTTPS_LATE_DENIED_NOT_COMMITTED_OR_RETRIED")?;
    Ok(json!({"state":"PASS_HTTPS_LATE_REVOCATION_EXISTING_ATTEMPT_NO_REEXECUTION","job_in_progress_not_success":true,
        "head_generation":1,"attempt":1,"claim_lease_CAS_or_execution_retried":false}))
}
