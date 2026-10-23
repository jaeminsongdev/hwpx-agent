//! Actual two-connection lock tests and the original coordinator's atomic-policy CAS, one fresh owned root only.
use super::*;
use revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::atomic_https::SIGNATURE;
use hwpx_agent_cli::form_product_request::stored_operations::https_targets::routing::atomic_sql::HttpsAtomicSqlJobRun;
const MIGRATION:&[u8]=include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"),"/../../migrations/postgres/0026_p09_https_policy_atomic_commit.up.sql"));
const LOCK:&str="SELECT hwpx_agent.require_https_policy_commit_v1($1,$2,$3,$4::character(64),$5,$6,$7,$8,$9::character(64),$10::character(64),$11::character(64),$12,$13,$14,$15::character(64))";
pub fn install(c:&mut Client,row:&mut Value)->Result<()>{
    c.batch_execute(&format!("SELECT set_config('hwpx_agent.migration_sha256','{}',false);\n{}",ContentDigest::of(MIGRATION).hex(),std::str::from_utf8(MIGRATION)?))?;
    c.batch_execute(&format!("GRANT EXECUTE ON FUNCTION {SIGNATURE} TO p09_revision_284"))?;
    row["state"]=json!("PASS_OWNED_EXACT_SCHEMA26_HTTPS_ATOMIC_POLICY");row["migrations"]=json!(26);Ok(())
}
fn app()->Result<Client>{let mut c=raw("p09_revision_284",&value("P09_SQL23_REVISION_PASSWORD")?)?;scoped(&mut c)?;Ok(c)}
fn guard(tx:&mut ::postgres::Transaction<'_>,v:&HttpsTargetPolicyVersion)->std::result::Result<(),::postgres::Error>{
    let b=&v.binding;let head=b.source_head_generation as i64;let generation=b.policy_generation as i64;
    tx.query_one(LOCK,&[&b.tenant.as_uuid(),&b.project.as_uuid(),&b.branch.as_uuid(),&b.creator_subject.hex(),&b.document.as_str(),&b.source_revision.as_uuid(),&head,
        &b.source_result_artifact.as_uuid(),&b.source_package_sha256.hex(),&b.source_provenance_sha256.hex(),&b.observed_graph_sha256.hex(),&b.policy_version,&generation,
        &v.artifact.as_uuid(),&v.digest.hex()])?;Ok(())
}
fn blocked<T>(value:std::result::Result<T,::postgres::Error>)->bool{matches!(value,Err(e)if e.code()==Some(&::postgres::error::SqlState::LOCK_NOT_AVAILABLE))}
pub fn revoked_denied(v:&HttpsTargetPolicyVersion)->Result<()>{let mut c=app()?;let mut tx=c.transaction()?;
    let denied=matches!(guard(&mut tx,v),Err(e)if e.code()==Some(&::postgres::error::SqlState::INSUFFICIENT_PRIVILEGE));tx.rollback()?;
    check(denied,"HTTPS_ATOMIC_CURRENT_REVOKED_POLICY_DENIED_BEFORE_CAS")
}
pub fn locks_and_binding(v:&HttpsTargetPolicyVersion)->Result<()>{
    let cfg=config()?;check(LocalPostgresStoredRevisionJobsRepository::connect_with_https_policy(&cfg,context()?,None).is_err(),"HTTPS_ATOMIC_OLD25_REVISION_DENIES26")?;
    let ac=LocalPostgresConfig::new(port()?,"postgres".into(),"p09_artifact_284".into(),value("P09_SQL23_ARTIFACT_PASSWORD")?)?;
    check(LocalPostgresMetadataRepository::connect_schema25(&ac,tenant()?).is_err(),"HTTPS_ATOMIC_OLD25_METADATA_DENIES26")?;
    let b=&v.binding;let mut first=app()?;let mut second=app()?;second.batch_execute("SET lock_timeout='100ms'")?;
    let mut owner=setup::admin()?;owner.batch_execute("SET lock_timeout='100ms'")?;
    let mut tx=first.transaction()?;guard(&mut tx,v)?;
    let generation=b.policy_generation as i64;
    check(blocked(second.query_one("SELECT hwpx_agent.revoke_source_https_target_policy_v1($1,$2,$3,$4::character(64),$5,$6,$7)",
        &[&id(1),&id(2),&id(3),&subject()?.hex(),&b.document.as_str(),&b.policy_version,&generation])),"HTTPS_ATOMIC_REVOKER_BLOCKS_UNTIL_SAME_TRANSACTION_END")?;
    let head=b.source_head_generation as i64;
    check(blocked(second.query_one("SELECT hwpx_agent.register_source_https_target_policy_v1($1,$2,$3,$4::character(64),$5,$6,$7,$8,$9,$10::character(64),$11::character(64),$12::character(64),$13,$14::character(64))",
        &[&id(1),&id(2),&id(3),&subject()?.hex(),&b.document.as_str(),&id(54222),&generation,&b.source_revision.as_uuid(),&head,
        &b.source_package_sha256.hex(),&b.source_provenance_sha256.hex(),&b.observed_graph_sha256.hex(),&v.artifact.as_uuid(),&v.digest.hex()])),"HTTPS_ATOMIC_NEW_POLICY_WRITER_BLOCKED")?;
    check(blocked(owner.execute("UPDATE hwpx_agent.project_acl SET role='reader' WHERE tenant_id=$1 AND project_id=$2 AND subject_sha256=$3::character(64)",
        &[&id(1),&id(2),&subject()?.hex()])) ,"HTTPS_ATOMIC_MEMBERSHIP_UPDATE_BLOCKED")?;
    for artifact in[b.source_result_artifact,v.artifact]{
        check(blocked(owner.execute("UPDATE hwpx_agent.artifact_acl SET can_read=false WHERE tenant_id=$1 AND artifact_id=$2 AND subject_sha256=$3::character(64)",
            &[&id(1),&artifact.as_uuid(),&subject()?.hex()])) ,"HTTPS_ATOMIC_SOURCE_AND_POLICY_ACL_UPDATES_BLOCKED")?;
    }
    tx.rollback()?;
    {let mut tx=second.transaction()?;guard(&mut tx,v)?;tx.rollback()?;}
    for mode in 0..4{let mut wrong=v.clone();match mode{0=>wrong.binding.policy_generation+=1,1=>wrong.binding.policy_version=id(54299),
        2=>wrong.digest=ContentDigest::of(b"other-policy"),_=>wrong.binding.source_provenance_sha256=ContentDigest::of(b"other-provenance")}
        let mut tx=first.transaction()?;let denied=matches!(guard(&mut tx,&wrong),Err(e)if e.code()==Some(&::postgres::error::SqlState::INSUFFICIENT_PRIVILEGE));
        tx.rollback()?;check(denied,"HTTPS_ATOMIC_VERSION_GENERATION_DIGEST_AND_SOURCE_BINDING_DENIED")?;
    }
    // An artifact role must not gain the policy locking API even though it can ingest ordinary Evidence.
    owner.batch_execute(&format!("GRANT EXECUTE ON FUNCTION {SIGNATURE} TO p09_artifact_284"))?;
    let denied=LocalPostgresMetadataRepository::connect_schema26(&ac,tenant()?).is_err();
    owner.batch_execute(&format!("REVOKE EXECUTE ON FUNCTION {SIGNATURE} FROM p09_artifact_284"))?;check(denied,"HTTPS_ATOMIC_ARTIFACT_ROLE_GUARD_DENIED")?;
    let definition:String=owner.query_one("SELECT pg_get_functiondef($1::text::regprocedure)",&[&SIGNATURE])?.try_get(0)?;
    check(definition.contains("BEGIN\n"),"HTTPS_ATOMIC_BODY_MUTATION_BOUNDARY")?;
    owner.batch_execute(&definition.replacen("BEGIN\n","BEGIN\n    -- owned atomic guard mutation\n",1))?;
    let denied=admitted_revision(&cfg,context()?).is_err();owner.batch_execute(&definition)?;check(denied,"HTTPS_ATOMIC_CHANGED_GUARD_BODY_DENIED")?;
    check(admitted_revision(&cfg,context()?).is_ok()&&admitted_artifact(&ac,tenant()?).is_ok(),"HTTPS_ATOMIC_SECURITY_RESTORED_BEFORE_PRODUCT")?;Ok(())
}
pub fn execute()->Result<Value>{
    let a=artifacts()?;let ctx=actor()?;let rc=context()?;let revisions=RevisionService::new(repository()?);
    let provider=StoredFormProvider::bind(&a,&revisions,&ctx,&rc,project()?,branch()?,DocumentId::parse("actual-form-document")?)?;
    let policy=Policy::new(repository()?);let wire=serde_json::to_vec(&load("https-public-request.json")?)?;
    let HttpsTargetRequestEntry::Prepared(product)=Product::prepare_https_targets_or_observe_json(&provider,&policy,&wire,limits()?,10)?else{return Err("HTTPS_ATOMIC_FRESH_REQUEST_REQUIRED".into())};
    let(c,r)=routes()?;let prepared=product.prepare_execution_manifest(&provider,&policy,&c,&r,domain_ir::TransactionId::parse("https-atomic-542")?,10)?;
    check(prepared.require_current_product_route(&provider,&policy,&c,&r,10).is_err(),"HTTPS_ATOMIC_PRODUCT_ROUTE_STAYS_DENIED")?;
    let checks=AtomicUsize::new(0);let workspace=owned_root()?.join("https-atomic-workspace");let s=state()?;let source=a.download(&ctx,read_id(&s,"source")?,10)?;
    let report=prepared.run_atomic_sql_job(&provider,&policy,HttpsAtomicSqlJobRun{policy:identity::StoredJobPolicy{max_delay_seconds:4,..Default::default()},
        commit:commit(5371)?,new_revision:revision(5372)?,limits:Default::default(),agent:id(130),execution:id(5423),lease_seconds:120,
        event:ContentDigest::of(b"https-atomic-542-event"),workspace:&workspace},
        ||{checks.fetch_add(1,Ordering::SeqCst);let(c,r)=routes().map_err(|_|())?;Ok((c,r,10))},
        |cap|{let mut c=raw("p09_revision_284",&value("P09_SQL23_REVISION_PASSWORD").map_err(|_|())?).map_err(|_|())?;scoped(&mut c).map_err(|_|())?;setup::register(&mut c,130,cap).map_err(|_|())},||10)?;
    check(report.stage==StoredJobRunStage::Completed&&report.repository_error.is_none()&&report.cas_error.is_none()&&report.binding_error.is_none()
        &&report.completion.is_some()&&checks.load(Ordering::SeqCst)==4,"HTTPS_ATOMIC_ORIGINAL_GUARDED_COORDINATOR_COMPLETED")?;
    let result=report.result.as_ref().ok_or("HTTPS_ATOMIC_RESULT")?;let registered=report.registered_intent.as_ref().ok_or("HTTPS_ATOMIC_REGISTERED")?;
    let claim=report.claim.as_ref().ok_or("HTTPS_ATOMIC_CLAIM")?;
    // The original report's lease carries the same unconsumed/then-consumed SQL identity used by registration and CAS.
    let lease=report.lease.ok_or("HTTPS_ATOMIC_LEASE")?;
    check(claim.job_id()==lease.identity().job_id&&report.registration_response.as_ref()==Some(registered),"HTTPS_ATOMIC_REAL_LEASE_REGISTERED_ROW_BOUND")?;
    check(revisions.repository().read_commit_intent(&rc,StoredCommitIntentLookup::new(project()?,lease.identity().idempotency_key,lease.identity().job_id,1)?)?.as_ref()==Some(registered),"HTTPS_ATOMIC_EXACT_REGISTERED_ROW")?;
    verify_output(&a.download(&ctx,result.artifact_id,11)?)?;check(a.download(&ctx,read_id(&s,"source")?,11)?==source,"HTTPS_ATOMIC_SOURCE_PRESERVED")?;
    check(revisions.head(&rc,project()?,branch()?)?==RevisionHead::new(Some(revision(5372)?),2)?,"HTTPS_ATOMIC_ONE_NEW_HEAD")?;
    save_value("https-completed.json",&json!({"result":result.artifact_id.public_id()}))?;
    Ok(json!({"state":"PASS_HTTPS_REAL_SQL26_ATOMIC_POLICY_AND_ORIGINAL_REGISTERED_CAS_COMPLETION_NOT_ADMISSION",
        "guard_attached_automatically":true,"policy_guard_inside_same_original_CAS_transaction":true,"actual_registered_row_and_AEAD_readback":true,"source_preserved":true,"route_unqualified":true}))
}
