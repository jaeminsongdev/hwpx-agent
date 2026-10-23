//! Separate exact26 metadata path. It grants no HTTPS policy/job/lookup authority.
use super::*;
const MIGRATION25:&[u8]=include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"),"/../../migrations/postgres/0025_p09_source_https_target_policy.up.sql"));
const MIGRATION26:&[u8]=include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"),"/../../migrations/postgres/0026_p09_https_policy_atomic_commit.up.sql"));
const LOOKUP:&str="hwpx_agent.read_stored_revision_request_v1(uuid,uuid,uuid,character,uuid,uuid,uuid,character,character,uuid,bigint)";
pub(super) fn validate(rows:&[(i64,String,String)])->Result<(),ArtifactError>{
    if rows.len()!=26||rows[25]!=(26,"p09.https_policy_atomic_commit_v1".into(),ContentDigest::of(MIGRATION26).hex()){return Err(ArtifactError::InvalidState);}
    schema25::validate(&rows[..25])
}
impl LocalPostgresMetadataRepository{
    /// # Errors
    /// Reuses original fixed-tenant/loopback/role/RLS admission, exact1..26 and job/policy separation.
    /// Old schema25 constructors still reject26. No migration, grant or retry is performed.
    pub fn connect_schema26(config:&LocalPostgresConfig,tenant:TenantId)->Result<Self,ArtifactError>{
        let repository=Self::connect(config,tenant)?;
        {
            let mut client=repository.client.try_lock().map_err(|_|ArtifactError::StorageFailure)?;
            let rows=client.query("SELECT version,migration_name,migration_sha256::text FROM hwpx_agent.schema_versions ORDER BY version LIMIT 27",&[]).map_err(db_error)?;
            let rows=rows.iter().map(|r|Ok((value(r,"version")?,value(r,"migration_name")?,value(r,"migration_sha256")?))).collect::<Result<Vec<_>,ArtifactError>>()?;validate(&rows)?;
            let row=client.query_one("SELECT rolreplication FROM pg_roles WHERE rolname=current_user",&[]).map_err(db_error)?;
            if value::<bool>(&row,"rolreplication")?{return Err(ArtifactError::AccessDenied);}schema23::verify_job_separation(&mut client)?;
            let row=client.query_one("SELECT has_function_privilege(current_user,$1::text::regprocedure,'EXECUTE') AS allowed",&[&LOOKUP]).map_err(db_error)?;
            if value::<bool>(&row,"allowed")?{return Err(ArtifactError::AccessDenied);}
            for table in["source_https_target_policy_versions","source_https_target_policy_revocations"]{
                let row=client.query_one("SELECT pg_has_role(c.relowner,'USAGE') OR pg_has_role(c.relowner,'SET')
                    OR has_table_privilege(current_user,c.oid,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')
                    OR has_any_column_privilege(current_user,c.oid,'SELECT,INSERT,UPDATE,REFERENCES') AS unsafe
                    FROM pg_class c WHERE c.oid=$1::text::regclass",&[&format!("hwpx_agent.{table}")]).map_err(db_error)?;
                if value::<bool>(&row,"unsafe")?{return Err(ArtifactError::AccessDenied);}
            }
            let sql=std::str::from_utf8(MIGRATION25).map_err(|_|ArtifactError::InvalidState)?;
            // Every dedicated helper/API, including role/artifact guards, must be unavailable to this role.
            for name in["require_source_https_target_policy_role_v1","require_source_https_target_policy_artifacts_v1",
                "register_source_https_target_policy_v1","read_source_https_target_policy_v1","revoke_source_https_target_policy_v1"]{
                if !sql.contains(&format!("CREATE FUNCTION hwpx_agent.{name}(")){return Err(ArtifactError::InvalidState);}
                let row=client.query_one("SELECT count(*)=1 AND bool_and(NOT has_function_privilege(current_user,p.oid,'EXECUTE')) AS denied
                    FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='hwpx_agent' AND p.proname=$1",&[&name]).map_err(db_error)?;
                if !value::<bool>(&row,"denied")?{return Err(ArtifactError::AccessDenied);}
            }
            let guard="hwpx_agent.require_https_policy_commit_v1(uuid,uuid,uuid,character,text,uuid,bigint,uuid,character,character,character,uuid,bigint,uuid,character)";
            let row=client.query_one("SELECT has_function_privilege(current_user,$1::text::regprocedure,'EXECUTE') AS allowed",&[&guard]).map_err(db_error)?;
            if value::<bool>(&row,"allowed")?{return Err(ArtifactError::AccessDenied);}
        }Ok(repository)
    }
}
