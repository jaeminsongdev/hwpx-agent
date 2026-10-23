//! New owned schema25 only. Negative SQL mutations are restored before product execution.
use super::*;
use hwpx_agent_cli::form_stored_provider::actual_import::StoredImportedDocumentForms;
use hwpx_agent_cli::form_stored_provider::actual_import::https_target_output::postgres::PostgresHttpsTargetPolicyProvider as Policy;
use revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::https_policy::{HttpsPolicyReadRequest,HttpsPolicyRegistrationRequest,HttpsPolicySource};
use hwpx_package::document_import::fields::semantics::source_index::https_targets::SourceHttpsTargetChange;
type Provider<'a>=StoredFormProvider<'a,LocalPostgresMetadataRepository,LocalEncryptedBlobStore,SyntheticScanner,LocalPostgresStoredRevisionJobsRepository>;
const MIGRATION:&[u8]=include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"),"/../../migrations/postgres/0025_p09_source_https_target_policy.up.sql"));
pub fn install()->Result<Value>{let mut row=lookup24::run("--fixture")?;let mut c=setup::admin()?;let sql=std::str::from_utf8(MIGRATION)?;
    c.batch_execute(&format!("SELECT set_config('hwpx_agent.migration_sha256','{}',false);\n{sql}",ContentDigest::of(MIGRATION).hex()))?;
    c.batch_execute("GRANT EXECUTE ON FUNCTION hwpx_agent.register_source_https_target_policy_v1(uuid,uuid,uuid,character,text,uuid,bigint,uuid,bigint,character,character,character,uuid,character),
        hwpx_agent.read_source_https_target_policy_v1(uuid,uuid,uuid,character,text,uuid,bigint),
        hwpx_agent.revoke_source_https_target_policy_v1(uuid,uuid,uuid,character,text,uuid,bigint) TO p09_revision_284")?;
    row["state"]=json!("PASS_OWNED_EXACT_SCHEMA25_HTTPS_POLICY_ROLES_NO_SEEDED_ARTIFACTS");row["migrations"]=json!(25);Ok(row)
}
fn config()->Result<LocalPostgresRevisionConfig>{Ok(LocalPostgresRevisionConfig::new(port()?,"postgres".into(),"p09_revision_284".into(),value("P09_SQL23_REVISION_PASSWORD")?)?)}
fn scope()->Result<HttpsPolicyReadRequest>{Ok(HttpsPolicyReadRequest::new(project()?,branch()?,"actual-form-document".into(),RevisionHead::new(Some(revision(20)?),1)?)?)}
fn current(repo:&LocalPostgresStoredRevisionJobsRepository)->Result<revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::https_policy::HttpsPolicyRecord>{
    Ok(repo.read_https_policy(&context()?,&scope()?)?)
}
pub fn publish_and_check(a:&Artifacts,revisions:&RevisionService<LocalPostgresStoredRevisionJobsRepository>,p:&Provider<'_>,source:&StoredImportedDocumentForms,selected:&ExternalLinkPolicy)->Result<HttpsTargetPolicyVersion>{
    let repo=revisions.repository();let rc=context()?;let publisher=Policy::new(repo.clone());let mut admin=setup::admin()?;let cfg=config()?;
    check(LocalPostgresStoredRevisionJobsRepository::connect(&cfg,rc.clone(),None).is_err()
        &&LocalPostgresStoredRevisionJobsRepository::connect_with_request_lookup(&cfg,rc.clone(),None).is_err(),"HTTPS_POLICY_OLD_JOB_CONNECTORS_DENY25")?;
    let artcfg=LocalPostgresConfig::new(port()?,"postgres".into(),"p09_artifact_284".into(),value("P09_SQL23_ARTIFACT_PASSWORD")?)?;
    check(LocalPostgresMetadataRepository::connect_schema24(&artcfg,tenant()?).is_err(),"HTTPS_POLICY_OLD_ARTIFACT24_DENIES25")?;
    check(current(repo).is_err(),"HTTPS_POLICY_NO_POLICY_DENIED")?;
    for mode in 0..5{let mut bad=selected.clone();match mode{0=>bad.approvals.clear(),1=>bad.allow_mailto=true,2=>bad.allow_managed_documents=true,
        3=>bad.approvals[0].kind=domain_ir::ExternalTargetKind::Mailto,_=>bad.policy_revision_sha256="invalid".into()}
        check(source.prepare_https_policy_registration(p,&bad,0,limits()?.targets,10).is_err(),"HTTPS_POLICY_INVALID_SERVER_INPUT_DENIED")?;}
    check(source.prepare_https_policy_registration(p,selected,i64::MAX as u64,limits()?.targets,10).is_err(),"HTTPS_POLICY_EXHAUSTED_GENERATION_DENIED")?;
    let first=source.prepare_https_policy_registration(p,selected,0,limits()?.targets,10)?.register(p,&publisher,10)?;
    let actual=current(repo)?;check(actual.version==first.binding.policy_version&&actual.generation==1&&actual.policy_artifact==first.artifact
        &&a.download(&actor()?,first.artifact,10)?.len()>0,"HTTPS_POLICY_REAL_SQL_REGISTER_AND_AEAD")?;
    let version=first.binding.policy_version;
    let stale=HttpsPolicyRegistrationRequest::new(scope()?,0,version,first.artifact,first.digest,HttpsPolicySource{result:first.binding.source_result_artifact,
        package:first.binding.source_package_sha256,provenance:first.binding.source_provenance_sha256,graph:first.binding.observed_graph_sha256})?;
    check(repo.register_https_policy(&rc,&stale).is_err()&&current(repo)?.generation==1,"HTTPS_POLICY_STALE_GENERATION_NO_WRITE")?;
    let rejected=match source.prepare_https_policy_registration(p,selected,0,limits()?.targets,10)?.register(p,&publisher,10){
        Ok(_)=>return Err("HTTPS_POLICY_STALE_PUBLICATION_MUST_FAIL".into()),Err(error)=>error};
    let orphan=rejected.retained_policy_artifact.ok_or("HTTPS_POLICY_REJECTED_EVIDENCE_NOT_RETAINED")?;
    check(rejected.error==registration::HttpsPolicyRegistrationError::Repository&&current(repo)?.generation==1
        &&a.get_descriptor(&actor()?,orphan,10)?.kind==ArtifactKind::Evidence&&!a.download(&actor()?,orphan,10)?.is_empty(),"HTTPS_POLICY_FAILED_CAS_PRESERVES_ACTUAL_ENCRYPTED_EVIDENCE")?;
    let managing=HttpsPolicyRegistrationRequest::new(scope()?,1,id(53833),first.artifact,first.digest,HttpsPolicySource{result:first.binding.source_result_artifact,
        package:first.binding.source_package_sha256,provenance:first.binding.source_provenance_sha256,graph:first.binding.observed_graph_sha256})?;
    let manage_before:bool=admin.query_one("SELECT can_manage FROM hwpx_agent.artifact_acl WHERE tenant_id=$1 AND artifact_id=$2 AND subject_sha256=$3::character(64)",&[&id(1),&first.artifact.as_uuid(),&subject()?.hex()])?.try_get(0)?;
    check(manage_before,"HTTPS_POLICY_FIXTURE_MANAGE_REQUIRED")?;
    admin.execute("UPDATE hwpx_agent.artifact_acl SET can_manage=false WHERE tenant_id=$1 AND artifact_id=$2 AND subject_sha256=$3::character(64)",&[&id(1),&first.artifact.as_uuid(),&subject()?.hex()])?;
    let denied=repo.register_https_policy(&rc,&managing).is_err();
    admin.execute("UPDATE hwpx_agent.artifact_acl SET can_manage=$4 WHERE tenant_id=$1 AND artifact_id=$2 AND subject_sha256=$3::character(64)",&[&id(1),&first.artifact.as_uuid(),&subject()?.hex(),&manage_before])?;
    check(denied&&current(repo)?.generation==1,"HTTPS_POLICY_READ_WITHOUT_MANAGE_CANNOT_REGISTER")?;
    let foreign=RevisionRequestContext::new(tenant()?,SubjectDigest::parse(&"b".repeat(64))?);
    check(repo.read_https_policy(&foreign,&scope()?).is_err(),"HTTPS_POLICY_FIXED_SUBJECT_DENIED")?;
    let stale_head=HttpsPolicyReadRequest::new(project()?,branch()?,"actual-form-document".into(),RevisionHead::new(Some(revision(20)?),2)?)?;
    check(repo.read_https_policy(&rc,&stale_head).is_err(),"HTTPS_POLICY_STALE_SOURCE_HEAD_DENIED")?;
    let old_role:String=admin.query_one("SELECT role FROM hwpx_agent.project_acl WHERE tenant_id=$1 AND project_id=$2 AND subject_sha256=$3::character(64)",&[&id(1),&id(2),&subject()?.hex()])?.try_get(0)?;
    check(admin.execute("UPDATE hwpx_agent.project_acl SET role='reader' WHERE tenant_id=$1 AND project_id=$2 AND subject_sha256=$3::character(64)",&[&id(1),&id(2),&subject()?.hex()])?==1,"HTTPS_POLICY_ONE_OWNED_MEMBERSHIP")?;
    let denied=current(repo).is_err();admin.execute("UPDATE hwpx_agent.project_acl SET role=$4 WHERE tenant_id=$1 AND project_id=$2 AND subject_sha256=$3::character(64)",&[&id(1),&id(2),&subject()?.hex(),&old_role])?;
    check(denied,"HTTPS_POLICY_READER_CANNOT_READ_EDIT_POLICY")?;
    for artifact in[first.binding.source_result_artifact,first.artifact]{
        let before:bool=admin.query_one("SELECT can_read FROM hwpx_agent.artifact_acl WHERE tenant_id=$1 AND artifact_id=$2 AND subject_sha256=$3::character(64)",&[&id(1),&artifact.as_uuid(),&subject()?.hex()])?.try_get(0)?;
        check(before,"HTTPS_POLICY_FIXTURE_READ_ACL_REQUIRED")?;
        admin.execute("UPDATE hwpx_agent.artifact_acl SET can_read=false WHERE tenant_id=$1 AND artifact_id=$2 AND subject_sha256=$3::character(64)",&[&id(1),&artifact.as_uuid(),&subject()?.hex()])?;
        let denied=current(repo).is_err();admin.execute("UPDATE hwpx_agent.artifact_acl SET can_read=$4 WHERE tenant_id=$1 AND artifact_id=$2 AND subject_sha256=$3::character(64)",&[&id(1),&artifact.as_uuid(),&subject()?.hex(),&before])?;
        check(denied,"HTTPS_POLICY_CURRENT_SOURCE_AND_POLICY_ACL_DENIED")?;
    }
    admin.batch_execute("GRANT SELECT ON hwpx_agent.source_https_target_policy_versions TO p09_artifact_284")?;
    let denied=LocalPostgresMetadataRepository::connect_schema25(&artcfg,tenant()?).is_err();
    admin.batch_execute("REVOKE SELECT ON hwpx_agent.source_https_target_policy_versions FROM p09_artifact_284")?;
    check(denied,"HTTPS_POLICY_ARTIFACT_ROLE_SEPARATION")?;
    admin.batch_execute("GRANT EXECUTE ON FUNCTION hwpx_agent.require_source_https_target_policy_role_v1(uuid,uuid,character,boolean) TO p09_revision_284")?;
    let denied=LocalPostgresStoredRevisionJobsRepository::connect_with_https_policy(&cfg,rc.clone(),None).is_err();
    admin.batch_execute("REVOKE EXECUTE ON FUNCTION hwpx_agent.require_source_https_target_policy_role_v1(uuid,uuid,character,boolean) FROM p09_revision_284")?;
    check(denied,"HTTPS_POLICY_HELPER_EXECUTION_PRIVILEGE_DENIED")?;
    admin.batch_execute("ALTER TABLE hwpx_agent.source_https_target_policy_versions NO FORCE ROW LEVEL SECURITY")?;
    let denied=LocalPostgresStoredRevisionJobsRepository::connect_with_https_policy(&cfg,rc.clone(),None).is_err();
    admin.batch_execute("ALTER TABLE hwpx_agent.source_https_target_policy_versions FORCE ROW LEVEL SECURITY")?;
    check(denied,"HTTPS_POLICY_UNFORCED_RLS_DENIED")?;
    let definition:String=admin.query_one("SELECT pg_get_functiondef('hwpx_agent.require_source_https_target_policy_role_v1(uuid,uuid,character,boolean)'::regprocedure)",&[])?.try_get(0)?;
    check(definition.contains("BEGIN\n"),"HTTPS_POLICY_FINGERPRINT_MUTATION_BOUNDARY")?;
    admin.batch_execute(&definition.replacen("BEGIN\n","BEGIN\n    -- owned admission mutation only\n",1))?;
    let denied=LocalPostgresStoredRevisionJobsRepository::connect_with_https_policy(&cfg,rc.clone(),None).is_err();admin.batch_execute(&definition)?;
    check(denied,"HTTPS_POLICY_CHANGED_FUNCTION_BODY_DENIED")?;
    let fields=Meaning::assess_package_field_semantics(&fixture::captured()?,DocumentId::parse("actual-form-document")?,source.receipt().imported.source_package_sha256,SourceImportLimits::default(),limits()?.auxiliary)?;
    let selection=fields.selections().first().ok_or("HTTPS_POLICY_SELECTION")?;let target=HyperlinkTarget::Https{uri:NEW_URI.into()};
    let candidate=source.prepare_https_target_candidate(p,&publisher,&[SourceHttpsTargetChange{reference_id:&selection.reference_id,
        expected_source_field_sha256:selection.source_field_sha256,expected_meaning_sha256:selection.meaning_sha256,target:&target}],limits()?.auxiliary,limits()?.targets,Default::default(),10)?;
    publisher.revoke(&rc,&first.binding)?;check(current(repo).is_err()&&candidate.verify(p,&publisher,10).is_err(),"HTTPS_POLICY_REVOKED_CURRENT_AND_PREPARED_CANDIDATE_DENIED")?;
    check(publisher.revoke(&rc,&first.binding).is_err(),"HTTPS_POLICY_DUPLICATE_REVOCATION_NO_RETRY")?;
    let second=source.prepare_https_policy_registration(p,selected,1,limits()?.targets,10)?.register(p,&publisher,10)?;
    check(second.binding.policy_generation==2&&current(repo)?.version==second.binding.policy_version&&candidate.verify(p,&publisher,10).is_err(),"HTTPS_POLICY_REPLACEMENT_NEVER_REVIVES_OLD_CANDIDATE")?;
    let rows=admin.query_one("SELECT (SELECT count(*) FROM hwpx_agent.source_https_target_policy_versions) AS versions,
        (SELECT count(*) FROM hwpx_agent.source_https_target_policy_revocations) AS revocations",&[])?;
    check(rows.try_get::<_,i64>("versions")?==2&&rows.try_get::<_,i64>("revocations")?==1,"HTTPS_POLICY_EXACT_IMMUTABLE_REGISTRY_ROWS")?;
    // Current guard metadata is restored/admitted before the subsequent actual HTTPS product job.
    check(LocalPostgresStoredRevisionJobsRepository::connect_with_https_policy(&cfg,rc,None).is_ok()
        &&LocalPostgresMetadataRepository::connect_schema25(&artcfg,tenant()?).is_ok(),"HTTPS_POLICY_SECURITY_RESTORED_AND_READMITTED")?;
    Ok(second)
}
