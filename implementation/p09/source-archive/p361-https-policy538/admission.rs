use super::*;
use crate::postgres::READ_TABLES;

const NAMES:[&str;23]=["p14.metadata_v1","p14.artifact_service_v1","p14.revision_cas_v1","p14.history_checkpoints_v1",
    "p14.job_state_machine_v1","p14.worker_lease_fencing_v1","p14.idempotency_reconciliation_v2","p14.cancel_cleanup_v1",
    "p14.retention_local_mirror_v1","p16.artifact_repository_v1","p16.plan_source_v1","p16.durable_plan_store_v1",
    "p16.plan_review_evidence_v1","p17.history_checkpoint_note_v2","p17.atomic_mirror_checkpoint_v3","p17.durable_git_mirror_push_v1",
    "p17.durable_git_mirror_pull_v1","p09.full_document_ir_v1","p09.authorized_full_ir_intent_v1","p09.source_form_policy_v1",
    "p09.source_formula_policy_v1","p09.formula_issuer_registry_v1","p09.stored_revision_jobs_v1"];
fn migrations()->Vec<&'static[u8]>{MIGRATIONS.iter().copied().chain([MIGRATION20,MIGRATION21,MIGRATION22,MIGRATION23]).collect()}
fn schema(rows:&[(i64,String,String)])->Result<(),RevisionError>{
    if rows.len()!=23{return Err(RevisionError::InvalidRequest);}
    for(i,(row,bytes))in rows.iter().zip(migrations()).enumerate(){
        if row.0!=i64::try_from(i+1).map_err(|_|RevisionError::InvalidRequest)?||row.1!=NAMES[i]||row.2!=ContentDigest::of(bytes).hex(){
            return Err(RevisionError::InvalidRequest);
        }
    }Ok(())
}
fn role(flags:&[bool;6])->Result<(),RevisionError>{if flags.iter().any(|f|*f){Err(RevisionError::InvalidRequest)}else{Ok(())}}
#[derive(Clone)]
struct FunctionSecurity{allowed:bool,definer:bool,path:bool,owner:bool,no_public:bool,body:ContentDigest}
impl FunctionSecurity{
    fn validate(&self,allowed:bool,body:ContentDigest)->Result<(),RevisionError>{
        if self.allowed!=allowed||!self.definer||!self.path||self.owner||!self.no_public||self.body!=body{Err(RevisionError::InvalidRequest)}else{Ok(())}
    }
}
#[derive(Clone)]
struct TableSecurity{rls:bool,forced:bool,owner:bool,direct:bool,policy:bool,immutable:bool,guard:bool}
impl TableSecurity{
    fn validate(&self)->Result<(),RevisionError>{
        if !self.rls||!self.forced||self.owner||self.direct||!self.policy||!self.immutable||!self.guard{Err(RevisionError::InvalidRequest)}else{Ok(())}
    }
}
fn functions()->Result<Vec<(&'static str,bool,ContentDigest)>,RevisionError>{
    let sql=std::str::from_utf8(MIGRATION23).map_err(|_|RevisionError::InvalidRequest)?;
    let mut result=Vec::new();
    for line in sql.lines(){
        let Some(signature)=line.strip_prefix("REVOKE ALL ON FUNCTION ").and_then(|v|v.strip_suffix(" FROM PUBLIC;"))else{continue};
        let name=signature.split('(').next().ok_or(RevisionError::InvalidRequest)?;
        let start=sql.find(&format!("CREATE FUNCTION {name}(")).ok_or(RevisionError::InvalidRequest)?;
        let text=&sql[start..];let body_start=text.find("AS $$").ok_or(RevisionError::InvalidRequest)?+5;
        let body_end=text[body_start..].find("$$;").ok_or(RevisionError::InvalidRequest)?+body_start;
        let allowed=matches!(name,"hwpx_agent.register_stored_revision_commit_intent_v1"|"hwpx_agent.read_stored_revision_commit_intent_v1"
            |"hwpx_agent.claim_stored_revision_job_v1"|"hwpx_agent.lease_stored_revision_job_v1"|"hwpx_agent.schedule_stored_revision_retry_v1"
            |"hwpx_agent.complete_stored_revision_job_success_v1"|"hwpx_agent.reconcile_stored_revision_job_v1");
        result.push((signature,allowed,ContentDigest::of(text[body_start..body_end].as_bytes())));
    }
    if result.len()!=11||result.iter().map(|v|v.0).collect::<std::collections::BTreeSet<_>>().len()!=11{return Err(RevisionError::InvalidRequest);}
    Ok(result)
}
pub(super) fn admit(client:&mut Client)->Result<(),RevisionError>{
    admit_mode(client,false)
}
pub(super) fn admit_with_lookup(client:&mut Client)->Result<(),RevisionError>{admit_mode(client,true)}
fn admit_mode(client:&mut Client,lookup:bool)->Result<(),RevisionError>{
    let r=client.query_one("SELECT rolsuper,rolbypassrls,rolcreaterole,rolcreatedb,rolreplication,
        has_schema_privilege(current_user,'hwpx_agent','CREATE') AS writable_schema FROM pg_roles WHERE rolname=current_user",&[]).map_err(db_error)?;
    role(&[value(&r,"rolsuper")?,value(&r,"rolbypassrls")?,value(&r,"rolcreaterole")?,value(&r,"rolcreatedb")?,value(&r,"rolreplication")?,value(&r,"writable_schema")?])?;
    for table in READ_TABLES.into_iter().chain(["jobs","job_attempts","idempotency_records","idempotency_commit_authorizations","schema_versions"]){
        let name=format!("hwpx_agent.{table}");
        let r=client.query_one("SELECT (pg_has_role(c.relowner,'USAGE') OR pg_has_role(c.relowner,'SET')
            OR has_table_privilege(current_user,c.oid,'INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')
            OR has_any_column_privilege(current_user,c.oid,'INSERT,UPDATE,REFERENCES')) AS unsafe
            FROM pg_class c WHERE c.oid=$1::text::regclass",&[&name]).map_err(db_error)?;
        if value::<bool>(&r,"unsafe")?{return Err(RevisionError::InvalidRequest);}
    }
    let rows=client.query(if lookup{"SELECT version,migration_name,migration_sha256::text FROM hwpx_agent.schema_versions ORDER BY version LIMIT 25"}
        else{"SELECT version,migration_name,migration_sha256::text FROM hwpx_agent.schema_versions ORDER BY version LIMIT 24"},&[]).map_err(db_error)?;
    let rows=rows.iter().map(|r|Ok((value(r,"version")?,value(r,"migration_name")?,value(r,"migration_sha256")?))).collect::<Result<Vec<_>,RevisionError>>()?;
    if lookup{request_lookup::schema24(&rows)?;schema(&rows[..23])?;}else{schema(&rows)?;}
    let r=client.query_one("SELECT c.relrowsecurity,c.relforcerowsecurity,
        (pg_has_role(c.relowner,'USAGE') OR pg_has_role(c.relowner,'SET')) AS owner_role,
        (has_table_privilege(current_user,c.oid,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER')
         OR has_any_column_privilege(current_user,c.oid,'SELECT,INSERT,UPDATE,REFERENCES')) AS direct,
        (SELECT count(*)=1 AND bool_and(p.policyname='tenant_isolation' AND p.cmd='ALL' AND p.permissive='PERMISSIVE'
            AND p.qual='(tenant_id = hwpx_agent.current_tenant_id())' AND p.with_check='(tenant_id = hwpx_agent.current_tenant_id())')
         FROM pg_policies p WHERE p.schemaname='hwpx_agent' AND p.tablename='stored_revision_commit_intents') AS policy,
        EXISTS(SELECT 1 FROM pg_trigger t WHERE t.tgrelid=c.oid AND t.tgname='stored_revision_commit_intents_immutable'
            AND t.tgfoid='hwpx_agent.reject_immutable_change()'::regprocedure AND t.tgenabled='O' AND NOT t.tgisinternal) AS immutable,
        EXISTS(SELECT 1 FROM pg_trigger t WHERE t.tgrelid='hwpx_agent.revision_commit_receipts'::regclass
            AND t.tgname='revision_commit_receipts_stored_intent_guard' AND t.tgenabled='O' AND NOT t.tgisinternal
            AND t.tgfoid='hwpx_agent.guard_stored_revision_commit_intent_v1()'::regprocedure) AS guard
        FROM pg_class c WHERE c.oid='hwpx_agent.stored_revision_commit_intents'::regclass",&[]).map_err(db_error)?;
    TableSecurity{rls:value(&r,"relrowsecurity")?,forced:value(&r,"relforcerowsecurity")?,owner:value(&r,"owner_role")?,direct:value(&r,"direct")?,
        policy:value(&r,"policy")?,immutable:value(&r,"immutable")?,guard:value(&r,"guard")?}.validate()?;
    for(signature,allowed,body)in functions()?{
        let r=client.query_one("SELECT has_function_privilege(current_user,p.oid,'EXECUTE') AS allowed,p.prosecdef,
            p.proconfig=ARRAY['search_path=pg_catalog, hwpx_agent'] AS bounded_path,p.prosrc,
            (pg_has_role(p.proowner,'USAGE') OR pg_has_role(p.proowner,'SET')) AS owner_role,
            NOT EXISTS(SELECT 1 FROM aclexplode(COALESCE(p.proacl,acldefault('f',p.proowner))) WHERE grantee=0 AND privilege_type='EXECUTE') AS no_public
            FROM pg_proc p WHERE p.oid=$1::text::regprocedure",&[&signature]).map_err(db_error)?;
        FunctionSecurity{allowed:value(&r,"allowed")?,definer:value(&r,"prosecdef")?,path:value(&r,"bounded_path")?,owner:value(&r,"owner_role")?,
            no_public:value(&r,"no_public")?,body:ContentDigest::of(value::<String>(&r,"prosrc")?.as_bytes())}.validate(allowed,body)?;
    }
    for signature in[
        "hwpx_agent.claim_idempotent_job_v2(uuid,uuid,uuid,character,uuid,uuid,uuid,uuid,uuid,bigint,character,character,character,character,character,character,text,character,integer,integer,integer,integer,character)",
        "hwpx_agent.lease_idempotent_job_v2(uuid,uuid,character,uuid,uuid,uuid,uuid,integer,character)",
        "hwpx_agent.schedule_idempotent_retry_v2(uuid,uuid,character,uuid,uuid,uuid,uuid,integer,bigint,text,uuid,character)",
        "hwpx_agent.complete_idempotent_job_success_v2(uuid,uuid,character,uuid,uuid,uuid,uuid,integer,bigint,uuid,uuid,character)",
        "hwpx_agent.reconcile_idempotent_job_v2(uuid,uuid,character,uuid,uuid,text,uuid,uuid,character)"]{
        let r=client.query_one("SELECT has_function_privilege(current_user,$1::text::regprocedure,'EXECUTE') AS allowed",&[&signature]).map_err(db_error)?;
        if value::<bool>(&r,"allowed")?{return Err(RevisionError::InvalidRequest);}
    }
    if lookup{request_lookup::admit(client)?;}Ok(())
}

#[cfg(test)]
mod tests{
    use super::*;
    #[test]fn lookup24_is_explicit_and_preserves_all_original23_schema_checks()->Result<(),RevisionError>{
        let mut rows=migrations().iter().enumerate().map(|(i,m)|((i+1)as i64,NAMES[i].into(),ContentDigest::of(m).hex())).collect::<Vec<_>>();
        assert!(request_lookup::schema24(&rows).is_err());rows.push((24,"p09.stored_request_lookup_v1".into(),ContentDigest::of(request_lookup::MIGRATION24).hex()));
        request_lookup::schema24(&rows)?;schema(&rows[..23])?;assert!(schema(&rows).is_err());
        for field in 0..3{let mut bad=rows.clone();match field{0=>bad[23].0=25,1=>bad[23].1="foreign".into(),_=>bad[23].2="0".repeat(64)}assert!(request_lookup::schema24(&bad).is_err());}
        let mut bad=rows.clone();bad[7].2="0".repeat(64);assert!(schema(&bad[..23]).is_err());rows.push((25,"future".into(),"0".repeat(64)));assert!(request_lookup::schema24(&rows).is_err());Ok(())
    }
    // Pure admission models only, NOT PostgreSQL query/catalog/privilege execution evidence.
    #[test]fn exact23_versions_names_and_all_source_hashes_are_required()->Result<(),RevisionError>{
        let rows=migrations().iter().enumerate().map(|(i,m)|((i+1)as i64,NAMES[i].into(),ContentDigest::of(m).hex())).collect::<Vec<_>>();schema(&rows)?;
        for field in 0..3{let mut changed=rows.clone();match field{0=>changed[7].0+=1,1=>changed[7].1="foreign".into(),_=>changed[7].2="0".repeat(64)}assert!(schema(&changed).is_err());}
        assert!(schema(&rows[..22]).is_err());let mut future=rows.clone();future.push((24,"future".into(),"0".repeat(64)));assert!(schema(&future).is_err());Ok(())
    }
    #[test]fn every_dangerous_role_or_schema_flag_is_denied(){assert!(role(&[false;6]).is_ok());for i in 0..6{let mut flags=[false;6];flags[i]=true;assert!(role(&flags).is_err());}}
    #[test]fn new_sql_function_sources_are_closed_unique_and_seven_entry_points_only()->Result<(),RevisionError>{let f=functions()?;assert_eq!(f.len(),11);assert_eq!(f.iter().filter(|v|v.1).count(),7);assert!(f.iter().all(|v|v.2.as_bytes()!=&[0;32]));Ok(())}
    #[test]fn function_rights_path_owner_public_and_exact_body_all_fail_closed(){
        let hash=ContentDigest::of(b"expected body");let good=FunctionSecurity{allowed:true,definer:true,path:true,owner:false,no_public:true,body:hash};assert!(good.validate(true,hash).is_ok());
        for i in 0..6{let mut bad=good.clone();match i{0=>bad.allowed=false,1=>bad.definer=false,2=>bad.path=false,3=>bad.owner=true,4=>bad.no_public=false,_=>bad.body=ContentDigest::of(b"changed body")};assert!(bad.validate(true,hash).is_err());}
    }
    #[test]fn table_rls_owner_direct_privilege_policy_and_both_triggers_all_fail_closed(){
        let good=TableSecurity{rls:true,forced:true,owner:false,direct:false,policy:true,immutable:true,guard:true};assert!(good.validate().is_ok());
        for i in 0..7{let mut bad=good.clone();match i{0=>bad.rls=false,1=>bad.forced=false,2=>bad.owner=true,3=>bad.direct=true,4=>bad.policy=false,5=>bad.immutable=false,_=>bad.guard=false};assert!(bad.validate().is_err());}
    }
}
