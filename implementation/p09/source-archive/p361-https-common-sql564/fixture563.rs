//! New common-dispatch integration; original coordinator owns claims/leases/registration/CAS/output.
use super::*;
use hwpx_agent_cli::form_product_request::stored_operations::https_targets::{dispatch::{PolicyBoundOperationLimits,atomic_sql::CommonHttpsSqlError},routing::atomic_sql::HttpsAtomicSqlJobRun};

fn run<'a>(workspace:&'a std::path::Path)->Result<HttpsAtomicSqlJobRun<'a>>{Ok(HttpsAtomicSqlJobRun{
    policy:identity::StoredJobPolicy{max_delay_seconds:4,..Default::default()},commit:commit(5371)?,new_revision:revision(5372)?,limits:Default::default(),
    agent:id(130),execution:id(5633),lease_seconds:120,event:ContentDigest::of(b"https-common-563-event"),workspace})}

pub fn execute()->Result<Value>{
    let a=artifacts()?;let ctx=actor()?;let rc=context()?;let revisions=RevisionService::new(repository()?);
    let provider=StoredFormProvider::bind(&a,&revisions,&ctx,&rc,project()?,branch()?,DocumentId::parse("actual-form-document")?)?;
    let policy=Policy::new(repository()?);let wire=serde_json::to_vec(&load("https-public-request.json")?)?;
    let prepare=||Product::prepare_json_with_https_policy(&provider,&policy,&wire,None,PolicyBoundOperationLimits::standard()?,10);
    let denied=prepare()?;let denied_workspace=owned_root()?.join("https-common-route-denied");let callbacks=AtomicUsize::new(0);
    let result=denied.run_atomic_https_sql_job(&provider,&policy,domain_ir::TransactionId::parse("https-common-route-denied")?,run(&denied_workspace)?,
        ||Err(()),|_|{callbacks.fetch_add(1,Ordering::SeqCst);Err(())},||10);
    check(matches!(result,Err(CommonHttpsSqlError::CurrentRoute))&&callbacks.load(Ordering::SeqCst)==0&&!denied_workspace.exists(),"HTTPS_COMMON_NO_ROUTE_NO_CLAIM_OR_WORKSPACE")?;
    let mut db=raw("p09_revision_284",&value("P09_SQL23_REVISION_PASSWORD")?)?;scoped(&mut db)?;
    let jobs:i64=db.query_one("SELECT count(*) FROM hwpx_agent.jobs",&[])?.get(0);drop(db);
    check(jobs==1&&revisions.head(&rc,project()?,branch()?)?==RevisionHead::new(Some(revision(20)?),1)?,"HTTPS_COMMON_PREFLIGHT_NO_DURABLE_EFFECT")?;
    let product=prepare()?;check(product.require_current_product_route_with_https_policy(&provider,&policy,None,10).is_err(),"HTTPS_COMMON_ORIGINAL_ROUTE_STAYS_DENIED")?;
    let checks=AtomicUsize::new(0);let workspace=owned_root()?.join("https-common-workspace");let s=state()?;let source=a.download(&ctx,read_id(&s,"source")?,10)?;
    let report=product.run_atomic_https_sql_job(&provider,&policy,domain_ir::TransactionId::parse("https-common-563")?,run(&workspace)?,
        ||{checks.fetch_add(1,Ordering::SeqCst);let(c,r)=routes().map_err(|_|())?;Ok((c,r,10))},
        |cap|{let mut c=raw("p09_revision_284",&value("P09_SQL23_REVISION_PASSWORD").map_err(|_|())?).map_err(|_|())?;scoped(&mut c).map_err(|_|())?;setup::register(&mut c,130,cap).map_err(|_|())},||10)?;
    check(report.stage==StoredJobRunStage::Completed&&report.repository_error.is_none()&&report.cas_error.is_none()&&report.binding_error.is_none()
        &&report.completion.is_some()&&checks.load(Ordering::SeqCst)==5,"HTTPS_COMMON_ORIGINAL_GUARDED_COORDINATOR_COMPLETED")?;
    let result=report.result.as_ref().ok_or("HTTPS_COMMON_RESULT")?;let registered=report.registered_intent.as_ref().ok_or("HTTPS_COMMON_REGISTERED")?;
    let claim=report.claim.as_ref().ok_or("HTTPS_COMMON_CLAIM")?;let lease=report.lease.ok_or("HTTPS_COMMON_LEASE")?;
    check(claim.job_id()==lease.identity().job_id&&report.registration_response.as_ref()==Some(registered),"HTTPS_COMMON_REAL_LEASE_REGISTERED_ROW_BOUND")?;
    check(revisions.repository().read_commit_intent(&rc,StoredCommitIntentLookup::new(project()?,lease.identity().idempotency_key,lease.identity().job_id,1)?)?.as_ref()==Some(registered),"HTTPS_COMMON_EXACT_REGISTERED_ROW")?;
    verify_output(&a.download(&ctx,result.artifact_id,11)?)?;check(a.download(&ctx,read_id(&s,"source")?,11)?==source,"HTTPS_COMMON_SOURCE_PRESERVED")?;
    check(revisions.head(&rc,project()?,branch()?)?==RevisionHead::new(Some(revision(5372)?),2)?,"HTTPS_COMMON_ONE_NEW_HEAD")?;
    save_value("https-completed.json",&json!({"result":result.artifact_id.public_id()}))?;
    Ok(json!({"state":"PASS_HTTPS_COMMON_SQL26_ORIGINAL_ATOMIC_CAS_COMPLETION_NOT_ADMISSION","common_policy_bound_dispatch":true,
        "unavailable_route_before_claim_callback_and_workspace_denied":true,"guard_attached_automatically":true,"policy_guard_inside_same_original_CAS_transaction":true,
        "actual_registered_row_and_AEAD_readback":true,"source_preserved":true,"route_unqualified":true,"current_route_callbacks":5}))
}
