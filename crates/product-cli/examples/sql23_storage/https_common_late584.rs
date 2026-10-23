//! Common public request -> original SQL CAS: revoke after the last app policy read.
//! Timing is injected only in the fixture policy reader, never in production CAS.
use super::*;
use std::sync::atomic::AtomicBool;
use hwpx_agent_cli::form_product_request::stored_operations::https_targets::{
    dispatch::{PolicyBoundOperationLimits,recovery::PolicyBoundRequestEntry},
    routing::atomic_sql::HttpsAtomicSqlJobRun,
};

struct LatePolicy {
    sql:postgres::PostgresHttpsTargetPolicyProvider,
    callbacks:AtomicUsize,last_reads:AtomicUsize,revoked:AtomicBool,
}
impl HttpsTargetPolicyRepository for LatePolicy {
    fn read_current(&self,scope:&HttpsTargetPolicyScope)->Result<HttpsTargetPolicyVersion,StoredHttpsTargetError>{
        let version=self.sql.read_current(scope)?;
        // The common bridge has one manifest callback before the original four guards.
        if self.callbacks.load(Ordering::SeqCst)==5&&self.last_reads.fetch_add(1,Ordering::SeqCst)+1==3 {
            if self.revoked.swap(true,Ordering::SeqCst){return Err(StoredHttpsTargetError::Repository);}
            self.sql.revoke(&context().map_err(|_|StoredHttpsTargetError::Repository)?,&version.binding)
                .map_err(|_|StoredHttpsTargetError::Repository)?;
        }
        Ok(version)
    }
}

pub fn execute()->Result<Value>{
    let a=artifacts()?;let ctx=actor()?;let rc=context()?;let revisions=RevisionService::new(repository()?);
    let provider=StoredFormProvider::bind(&a,&revisions,&ctx,&rc,project()?,branch()?,DocumentId::parse("actual-form-document")?)?;
    let policy=LatePolicy {sql:postgres::PostgresHttpsTargetPolicyProvider::new(repository()?),
        callbacks:AtomicUsize::new(0),last_reads:AtomicUsize::new(0),revoked:AtomicBool::new(false)};
    let wire=serde_json::to_vec(&load("https-public-request.json")?)?;
    let PolicyBoundRequestEntry::Prepared(product)=Product::prepare_json_or_observe_with_https_policy(&provider,&policy,&wire,None,PolicyBoundOperationLimits::standard()?,10)?
        else{return Err("COMMON_LATE584_FRESH_COMMON_REQUEST_REQUIRED_NO_REPLAY".into())};
    let product=*product;
    check(product.require_current_product_route_with_https_policy(&provider,&policy,None,10).is_err(),"COMMON_LATE584_PRODUCT_ROUTE_STAYS_DENIED")?;
    let s=state()?;let source=read_id(&s,"source")?;let original=a.download(&ctx,source,10)?;
    let workspace=owned_root()?.join("common-late584-workspace");
    let report=product.run_atomic_https_sql_job(&provider,&policy,domain_ir::TransactionId::parse("common-late584")?,
        HttpsAtomicSqlJobRun {policy:identity::StoredJobPolicy{max_delay_seconds:4,..Default::default()},
            commit:commit(5841)?,new_revision:revision(5842)?,limits:Default::default(),agent:id(130),execution:id(5843),lease_seconds:120,
            event:ContentDigest::of(b"common-late584-event"),workspace:&workspace},
        ||{policy.callbacks.fetch_add(1,Ordering::SeqCst);let(c,r)=routes().map_err(|_|())?;Ok((c,r,10))},
        |cap|{let mut c=raw("p09_revision_284",&value("P09_SQL23_REVISION_PASSWORD").map_err(|_|())?).map_err(|_|())?;scoped(&mut c).map_err(|_|())?;
            setup::register(&mut c,130,cap).map_err(|_|())},||10)?;
    check(policy.callbacks.load(Ordering::SeqCst)==5&&policy.last_reads.load(Ordering::SeqCst)==3&&policy.revoked.load(Ordering::SeqCst),
        "COMMON_LATE584_EXACT_FINAL_APP_READ_REVOCATION_REQUIRED")?;
    check(report.stage==StoredJobRunStage::Transaction&&report.binding_error.is_none()&&report.repository_error.is_none()
        &&report.cas_error==Some(StoredCommitError::Revision)&&report.transaction.as_ref().is_some_and(|v|v.is_err())
        &&report.revision_receipt.is_none()&&report.completion.is_none()&&report.unknown.is_none(),
        "COMMON_LATE584_ORIGINAL_SQL_CAS_DENIED_NOT_APP_GUARD_SUCCESS_OR_RETRY")?;
    let lease=report.lease.ok_or("COMMON_LATE584_REAL_LEASE_REQUIRED")?;
    let registered=report.registered_intent.as_ref().ok_or("COMMON_LATE584_REGISTERED_INTENT_REQUIRED")?;
    check(report.registration_response.as_ref()==Some(registered)&&revisions.repository().read_commit_intent(&rc,
        StoredCommitIntentLookup::new(project()?,lease.identity().idempotency_key,lease.identity().job_id,1)?)?.as_ref()==Some(registered),
        "COMMON_LATE584_EXACT_ORIGINAL_REGISTERED_INTENT_RETAINED")?;
    verify_output(&a.download(&ctx,report.result.as_ref().ok_or("COMMON_LATE584_RESULT_REQUIRED")?.artifact_id,11)?)?;
    for item in[report.intent.as_ref(),report.precommit.as_ref()] {
        check(!a.download(&ctx,item.ok_or("COMMON_LATE584_EVIDENCE_REQUIRED")?.artifact_id,11)?.is_empty(),"COMMON_LATE584_AEAD_EVIDENCE_RETAINED")?;
    }
    check(a.download(&ctx,source,11)?==original&&revisions.head(&rc,project()?,branch()?)?==RevisionHead::new(Some(revision(20)?),1)?,
        "COMMON_LATE584_ORIGINAL_SOURCE_HEAD_UNCHANGED")?;
    let observed=observe()?;
    Ok(json!({"state":"PASS_COMMON_LATE584_ORIGINAL_SQL_CAS_DENIAL_AND_EVIDENCE_NOT_ADMISSION",
        "common_policy_bound_dispatch":true,"last_app_guard_reads_completed":true,"original_SQL_CAS_denied":true,
        "result_intent_precommit_AEAD_retained":true,"source_and_head_preserved":true,"current_route_callbacks":5,
        "route_unqualified":true,"read_only_observation":observed}))
}

pub fn observe()->Result<Value>{
    let a=artifacts()?;let ctx=actor()?;let rc=context()?;let revisions=RevisionService::new(repository()?);
    let provider=StoredFormProvider::bind(&a,&revisions,&ctx,&rc,project()?,branch()?,DocumentId::parse("actual-form-document")?)?;
    let wire=serde_json::to_vec(&load("https-public-request.json")?)?;
    let PolicyBoundRequestEntry::ExistingHttps(job)=Product::prepare_json_or_observe_with_https_policy(&provider,&NoPolicyReads,&wire,None,PolicyBoundOperationLimits::standard()?,20)?
        else{return Err("COMMON_LATE584_EXISTING_ONLY_NO_POLICY_PREPARATION_OR_EXECUTION".into())};
    check(job.state()==StoredJobState::InProgress&&job.attempt_no()==1&&job.fencing_token()==1&&job.result_revision_id().is_none()
        &&revisions.head(&rc,project()?,branch()?)?==RevisionHead::new(Some(revision(20)?),1)?,"COMMON_LATE584_DENIED_NOT_COMMITTED_OR_RETRIED")?;
    let lookup=Product::prepare_https_targets_lookup_json(&provider,&wire,limits()?)?;
    let StoredRequestRecoveryObservation::Existing {job:recovered,effect:ArchivedRegisteredStoredCommitRecoveryOutcome::Registered(StoredCommitRecoveryOutcome::NotObserved)}=
        lookup.recover_registered(&provider,||20)? else{return Err("COMMON_LATE584_REGISTERED_NOT_OBSERVED_IS_NOT_NO_EFFECT_OR_RETRY_PERMISSION".into())};
    check(recovered==job,"COMMON_LATE584_SAME_CURRENT_JOB_ATTEMPT_OBSERVATION")?;
    Ok(json!({"state":"PASS_COMMON_LATE584_REGISTERED_UNCOMMITTED_OBSERVATION_NO_REEXECUTION",
        "common_existing_without_policy_or_compilation":true,"registered_effect_not_observed_not_no_effect_proof":true,
        "job_in_progress_not_success":true,"head_generation":1,"attempt":1,"fencing_token":1,
        "claim_lease_CAS_or_execution_retried":false}))
}
