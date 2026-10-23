//! Separate exact-schema23 artifact admission, not a job authority or a live DB qualification.
use super::{ArtifactError,Client,ContentDigest,LocalPostgresConfig,LocalPostgresMetadataRepository,
    MIGRATIONS,PostgresConnectFailure,PostgresConnectStage,TenantId,db_error,value};

macro_rules! migration{($file:literal)=>{include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"),"/../../migrations/postgres/",$file)).as_slice()};}
const ADDITIONAL:[&[u8];6]=[
    migration!("0018_p09_full_document_ir.up.sql"),migration!("0019_p09_authorized_full_ir_intent.up.sql"),
    migration!("0020_p09_source_form_policy.up.sql"),migration!("0021_p09_source_formula_policy.up.sql"),
    migration!("0022_p09_formula_issuer_registry.up.sql"),migration!("0023_p09_stored_revision_jobs.up.sql")];
const NAMES:[&str;23]=["p14.metadata_v1","p14.artifact_service_v1","p14.revision_cas_v1","p14.history_checkpoints_v1",
    "p14.job_state_machine_v1","p14.worker_lease_fencing_v1","p14.idempotency_reconciliation_v2","p14.cancel_cleanup_v1",
    "p14.retention_local_mirror_v1","p16.artifact_repository_v1","p16.plan_source_v1","p16.durable_plan_store_v1",
    "p16.plan_review_evidence_v1","p17.history_checkpoint_note_v2","p17.atomic_mirror_checkpoint_v3","p17.durable_git_mirror_push_v1",
    "p17.durable_git_mirror_pull_v1","p09.full_document_ir_v1","p09.authorized_full_ir_intent_v1","p09.source_form_policy_v1",
    "p09.source_formula_policy_v1","p09.formula_issuer_registry_v1","p09.stored_revision_jobs_v1"];

impl LocalPostgresMetadataRepository{
    /// Reuses original fixed-tenant/loopback/role/RLS/privilege admission, then checks exact1..23
    /// and denies job-table or SQL23-function authority. No migrations or grants are installed.
    /// # Errors
    /// Rejects changed/future schema, unsafe rights and transport failure; never retries.
    pub fn connect_schema23(config:&LocalPostgresConfig,tenant:TenantId)->Result<Self,ArtifactError>{
        Self::connect_schema23_diagnosed(config,tenant).map_err(PostgresConnectFailure::into_error)
    }
    /// # Errors
    /// Returns only original closed support stages; raw backend diagnostics remain private.
    pub fn connect_schema23_diagnosed(config:&LocalPostgresConfig,tenant:TenantId)->Result<Self,PostgresConnectFailure>{
        let repository=Self::connect_diagnosed(config,tenant)?;
        {
            let mut client=repository.client.try_lock().map_err(|_|PostgresConnectFailure{stage:PostgresConnectStage::Migrations,error:ArtifactError::StorageFailure})?;
            verify_schema23(&mut client).map_err(|error|PostgresConnectFailure{stage:PostgresConnectStage::Migrations,error})?;
            let role=client.query_one("SELECT rolreplication FROM pg_roles WHERE rolname=current_user",&[])
                .map_err(|e|PostgresConnectFailure{stage:PostgresConnectStage::Role,error:db_error(e)})?;
            reject(value(&role,"rolreplication").map_err(|error|PostgresConnectFailure{stage:PostgresConnectStage::Role,error})?)
                .map_err(|error|PostgresConnectFailure{stage:PostgresConnectStage::Role,error})?;
            verify_job_separation(&mut client).map_err(|error|PostgresConnectFailure{stage:PostgresConnectStage::Privileges,error})?;
        }
        Ok(repository)
    }
}
fn reject(unsafe_right:bool)->Result<(),ArtifactError>{if unsafe_right{Err(ArtifactError::AccessDenied)}else{Ok(())}}
pub(super) fn validate(rows:&[(i64,String,String)])->Result<(),ArtifactError>{
    if rows.len()!=23{return Err(ArtifactError::InvalidState);}
    for(i,(row,source))in rows.iter().zip(MIGRATIONS.iter().chain(ADDITIONAL.iter())).enumerate(){
        if row.0!=i64::try_from(i+1).map_err(|_|ArtifactError::InvalidState)?||row.1!=NAMES[i]
            ||row.2!=ContentDigest::of(source).hex(){return Err(ArtifactError::InvalidState);}
    }Ok(())
}
fn verify_schema23(client:&mut Client)->Result<(),ArtifactError>{
    let rows=client.query("SELECT version,migration_name,migration_sha256::text FROM hwpx_agent.schema_versions ORDER BY version LIMIT 24",&[]).map_err(db_error)?;
    let rows=rows.iter().map(|r|Ok((value(r,"version")?,value(r,"migration_name")?,value(r,"migration_sha256")?))).collect::<Result<Vec<_>,ArtifactError>>()?;
    validate(&rows)
}
#[cfg(test)]pub(super) fn expected_schema23_rows()->Vec<(i64,String,String)>{
    MIGRATIONS.iter().chain(ADDITIONAL.iter()).enumerate().map(|(i,m)|((i+1)as i64,NAMES[i].into(),ContentDigest::of(m).hex())).collect()
}
fn job_functions()->Result<Vec<&'static str>,ArtifactError>{
    let sql=std::str::from_utf8(ADDITIONAL[5]).map_err(|_|ArtifactError::InvalidState)?;
    let signatures=sql.lines().filter_map(|line|line.strip_prefix("REVOKE ALL ON FUNCTION ").and_then(|v|v.strip_suffix(" FROM PUBLIC;"))).collect::<Vec<_>>();
    if signatures.len()!=11||signatures.iter().collect::<std::collections::BTreeSet<_>>().len()!=11{return Err(ArtifactError::InvalidState);}Ok(signatures)
}
pub(super) fn verify_job_separation(client:&mut Client)->Result<(),ArtifactError>{
    for table in["jobs","job_attempts","idempotency_records","idempotency_commit_authorizations","stored_revision_commit_intents"]{
        let name=format!("hwpx_agent.{table}");
        let r=client.query_one("SELECT (pg_has_role(c.relowner,'USAGE') OR pg_has_role(c.relowner,'SET')
            OR has_table_privilege(current_user,c.oid,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')
            OR has_any_column_privilege(current_user,c.oid,'SELECT,INSERT,UPDATE,REFERENCES')) AS excessive
            FROM pg_class c WHERE c.oid=$1::text::regclass",&[&name]).map_err(db_error)?;
        reject(value(&r,"excessive")?)?;
    }
    let r=client.query_one("SELECT (pg_has_role(c.relowner,'USAGE') OR pg_has_role(c.relowner,'SET')
        OR has_table_privilege(current_user,c.oid,'INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')
        OR has_any_column_privilege(current_user,c.oid,'INSERT,UPDATE,REFERENCES')) AS excessive
        FROM pg_class c WHERE c.oid='hwpx_agent.schema_versions'::regclass",&[]).map_err(db_error)?;
    reject(value(&r,"excessive")?)?;
    for signature in job_functions()?{
        let r=client.query_one("SELECT has_function_privilege(current_user,$1::text::regprocedure,'EXECUTE') AS allowed",&[&signature]).map_err(db_error)?;
        reject(value(&r,"allowed")?)?;
    }Ok(())
}

#[cfg(test)]
mod tests{
    use super::*;
    // Pure models. These do not execute a PostgreSQL query or qualify actual role privileges.
    fn exact()->Vec<(i64,String,String)>{MIGRATIONS.iter().chain(ADDITIONAL.iter()).enumerate()
        .map(|(i,m)|((i+1)as i64,NAMES[i].into(),ContentDigest::of(m).hex())).collect()}
    #[test]fn exact23_names_versions_and_fingerprints_are_admitted(){assert_eq!(validate(&exact()),Ok(()));}
    #[test]fn old_prefix_missing_middle_and_future_schema_are_denied(){
        let rows=exact();for size in[17,22]{assert_eq!(validate(&rows[..size]),Err(ArtifactError::InvalidState));}
        let mut missing=rows.clone();missing.remove(9);assert!(validate(&missing).is_err());
        let mut future=rows;future.push((24,"future".into(),"0".repeat(64)));assert!(validate(&future).is_err());
    }
    #[test]fn every_changed_fingerprint_is_denied(){for i in 0..23{let mut rows=exact();rows[i].2="0".repeat(64);assert!(validate(&rows).is_err());}}
    #[test]fn every_renamed_version_gap_or_reordering_is_denied(){
        for i in 0..23{let mut rows=exact();rows[i].1="foreign".into();assert!(validate(&rows).is_err());let mut rows=exact();rows[i].0+=1;assert!(validate(&rows).is_err());}
        let mut rows=exact();rows.swap(18,19);assert!(validate(&rows).is_err());
    }
    #[test]fn replication_owner_column_table_or_function_authority_is_denied(){assert_eq!(reject(false),Ok(()));assert_eq!(reject(true),Err(ArtifactError::AccessDenied));}
    #[test]fn all11_job_functions_are_closed_and_no_execution_is_granted()->Result<(),ArtifactError>{let f=job_functions()?;assert_eq!(f.len(),11);assert!(f.iter().all(|s|s.starts_with("hwpx_agent.")));Ok(())}
}
