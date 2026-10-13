//! Additive exact schema21 admission. The original schema17 connector stays unchanged.
use super::*;

const ADDITIONS: [&[u8]; 4] = [
    include_bytes!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../migrations/postgres/0018_p09_full_document_ir.up.sql"
    )),
    include_bytes!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../migrations/postgres/0019_p09_authorized_full_ir_intent.up.sql"
    )),
    include_bytes!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../migrations/postgres/0020_p09_source_form_policy.up.sql"
    )),
    include_bytes!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../migrations/postgres/0021_p09_source_formula_policy.up.sql"
    )),
];
/// Uses the unchanged artifact repository with a separately exact schema1~21 profile.
/// # Errors
/// Rejects unsafe original role/policy/privileges and any missing/changed/future migration.
impl LocalPostgresMetadataRepository {
    /// Connects the unchanged metadata service under the exact schema21 profile.
    /// # Errors
    /// Rejects unsafe role/policy/privileges, missing/future migrations or transport failure.
    pub fn connect_source_form_policy_schema21(
        config: &LocalPostgresConfig,
        tenant: TenantId,
    ) -> Result<LocalPostgresMetadataRepository, ArtifactError> {
        let mut client = Config::new().host("127.0.0.1").port(config.port).dbname(&config.database)
        .user(&config.user).password(config.password.as_bytes()).connect_timeout(Duration::from_secs(3))
        .application_name("hwpx-agent-local-policy-artifacts-schema21")
        .options("-c statement_timeout=5000 -c lock_timeout=1000 -c idle_in_transaction_session_timeout=5000 -c transaction_timeout=10000 -c search_path=pg_catalog")
        .connect(NoTls).map_err(db_error)?;
        verify_role(&mut client)?;
        let role = client
            .query_one(
                "SELECT rolreplication FROM pg_roles WHERE rolname=current_user",
                &[],
            )
            .map_err(db_error)?;
        if value::<bool>(&role, "rolreplication")? {
            return Err(ArtifactError::AccessDenied);
        }
        let rows = client.query("SELECT version,migration_sha256::text FROM hwpx_agent.schema_versions ORDER BY version LIMIT 22", &[]).map_err(db_error)?;
        if rows.len() != 21 {
            return Err(ArtifactError::InvalidState);
        }
        for (i, (row, migration)) in rows
            .iter()
            .zip(MIGRATIONS.iter().chain(ADDITIONS.iter()))
            .enumerate()
        {
            if value::<i64>(row, "version")?
                != i64::try_from(i + 1).map_err(|_| ArtifactError::InvalidState)?
                || value::<String>(row, "migration_sha256")? != ContentDigest::of(migration).hex()
            {
                return Err(ArtifactError::InvalidState);
            }
        }
        verify_policies(&mut client)?;
        verify_privileges(&mut client)?;
        Ok(LocalPostgresMetadataRepository {
            tenant,
            client: Arc::new(Mutex::new(client)),
        })
    }
}
