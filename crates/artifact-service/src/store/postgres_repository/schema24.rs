//! Explicit exact24 artifact connector. Never grants job or cold-lookup execution privileges.
use super::*;
const MIGRATION24:&[u8]=include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"),"/../../migrations/postgres/0024_p09_stored_request_lookup.up.sql"));
const LOOKUP:&str="hwpx_agent.read_stored_revision_request_v1(uuid,uuid,uuid,character,uuid,uuid,uuid,character,character,uuid,bigint)";
pub(super) fn validate(rows:&[(i64,String,String)])->Result<(),ArtifactError>{
    if rows.len()!=24||rows[23]!=(24,"p09.stored_request_lookup_v1".into(),ContentDigest::of(MIGRATION24).hex()){return Err(ArtifactError::InvalidState);}
    schema23::validate(&rows[..23])
}
impl LocalPostgresMetadataRepository{
    /// # Errors
    /// All original tenant/loopback/role/RLS/privilege guards plus exact1..24 and no job/lookup authority.
    /// Existing schema23 constructors still reject24. Never installs a migration/grant or retries.
    pub fn connect_schema24(config:&LocalPostgresConfig,tenant:TenantId)->Result<Self,ArtifactError>{
        Self::connect_schema24_diagnosed(config,tenant).map_err(PostgresConnectFailure::into_error)
    }
    /// # Errors
    /// Closed original support categories only; no backend details or credentials.
    pub fn connect_schema24_diagnosed(config:&LocalPostgresConfig,tenant:TenantId)->Result<Self,PostgresConnectFailure>{
        let repository=Self::connect_diagnosed(config,tenant)?;
        {
            let mut client=repository.client.try_lock().map_err(|_|PostgresConnectFailure{stage:PostgresConnectStage::Migrations,error:ArtifactError::StorageFailure})?;
            let check=(||->Result<(),ArtifactError>{
                let rows=client.query("SELECT version,migration_name,migration_sha256::text FROM hwpx_agent.schema_versions ORDER BY version LIMIT 25",&[]).map_err(db_error)?;
                let rows=rows.iter().map(|r|Ok((value(r,"version")?,value(r,"migration_name")?,value(r,"migration_sha256")?))).collect::<Result<Vec<_>,ArtifactError>>()?;
                validate(&rows)
            })();check.map_err(|error|PostgresConnectFailure{stage:PostgresConnectStage::Migrations,error})?;
            let check=(||->Result<(),ArtifactError>{
                let row=client.query_one("SELECT rolreplication FROM pg_roles WHERE rolname=current_user",&[]).map_err(db_error)?;
                if value::<bool>(&row,"rolreplication")?{return Err(ArtifactError::AccessDenied);}
                schema23::verify_job_separation(&mut client)?;
                let row=client.query_one("SELECT has_function_privilege(current_user,$1::text::regprocedure,'EXECUTE') AS allowed",&[&LOOKUP]).map_err(db_error)?;
                if value::<bool>(&row,"allowed")?{return Err(ArtifactError::AccessDenied);}Ok(())
            })();check.map_err(|error|PostgresConnectFailure{stage:PostgresConnectStage::Privileges,error})?;
        }Ok(repository)
    }
}
#[cfg(test)]mod tests{
    use super::*;
    fn rows()->Vec<(i64,String,String)>{
        let sql=std::str::from_utf8(MIGRATION24).unwrap_or_default();assert!(sql.contains("REVOKE ALL ON FUNCTION"));
        let mut values=schema23::expected_schema23_rows();values.push((24,"p09.stored_request_lookup_v1".into(),ContentDigest::of(MIGRATION24).hex()));values
    }
    #[test]fn exact24_reuses_original23_sources_and_never_grants_lookup_authority(){assert_eq!(validate(&rows()),Ok(()));assert!(schema23::validate(&rows()).is_err());}
    #[test]fn missing_future_or_wrong24_tail_never_passes(){let values=rows();assert!(validate(&values[..23]).is_err());let mut bad=values.clone();bad.push((25,"future".into(),"0".repeat(64)));assert!(validate(&bad).is_err());
        for column in 0..3{let mut bad=values.clone();match column{0=>bad[23].0=25,1=>bad[23].1="foreign".into(),_=>bad[23].2="0".repeat(64)}assert!(validate(&bad).is_err());}}
    #[test]fn correct24_tail_cannot_replace_original23_validation(){for i in 0..23{let mut bad=rows();bad[i].2="0".repeat(64);assert!(validate(&bad).is_err());}}
}
