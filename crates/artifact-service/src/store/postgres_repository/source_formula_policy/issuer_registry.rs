//! Explicit artifact metadata admission for SQL22; original SQL17/21 constructors are unchanged.
use super::{
    ADDITIONS, Arc, ArtifactError, Config, ContentDigest, Duration, LocalPostgresConfig,
    LocalPostgresMetadataRepository, MIGRATIONS, Mutex, NoTls, TenantId, db_error, value,
    verify_policies, verify_privileges, verify_role,
};
const MIGRATION22: &[u8] = include_bytes!(concat!(
    env!("CARGO_MANIFEST_DIR"),
    "/../../migrations/postgres/0022_p09_formula_issuer_registry.up.sql"
));
impl LocalPostgresMetadataRepository {
    /// Connects the original ACL/AEAD metadata service with exact schema1..22 fingerprints.
    /// # Errors
    /// Denies unsafe original role/policy/table privileges, future/changed schema and transport failure.
    pub fn connect_formula_issuer_registry_schema22(
        config: &LocalPostgresConfig,
        tenant: TenantId,
    ) -> Result<Self, ArtifactError> {
        let mut client = Config::new().host("127.0.0.1").port(config.port).dbname(&config.database)
            .user(&config.user).password(config.password.as_bytes()).connect_timeout(Duration::from_secs(3))
            .application_name("hwpx-agent-local-formula-registry-artifacts-schema22")
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
        let rows=client.query("SELECT version,migration_sha256::text FROM hwpx_agent.schema_versions ORDER BY version LIMIT 23",&[]).map_err(db_error)?;
        if rows.len() != 22 {
            return Err(ArtifactError::InvalidState);
        }
        for (i, (row, migration)) in rows
            .iter()
            .zip(
                MIGRATIONS
                    .iter()
                    .chain(ADDITIONS.iter())
                    .chain([MIGRATION22].iter()),
            )
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
        Ok(Self {
            tenant,
            client: Arc::new(Mutex::new(client)),
        })
    }
}
