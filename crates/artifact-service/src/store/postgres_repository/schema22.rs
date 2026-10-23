//! Explicit schema22 artifact admission. Keeps original prefix17 constructors and operations unchanged.
use super::{
    ArtifactError, Client, ContentDigest, LocalPostgresConfig, LocalPostgresMetadataRepository,
    MIGRATIONS, PostgresConnectFailure, PostgresConnectStage, TenantId, db_error, value,
};

macro_rules! migration {
    ($file:literal) => {
        include_bytes!(concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/../../migrations/postgres/",
            $file
        ))
        .as_slice()
    };
}
const ADDITIONAL: [&[u8]; 5] = [
    migration!("0018_p09_full_document_ir.up.sql"),
    migration!("0019_p09_authorized_full_ir_intent.up.sql"),
    migration!("0020_p09_source_form_policy.up.sql"),
    migration!("0021_p09_source_formula_policy.up.sql"),
    migration!("0022_p09_formula_issuer_registry.up.sql"),
];

impl LocalPostgresMetadataRepository {
    /// Explicit exact schema1..22 admission for issuer workflows; grants nothing and changes no DB.
    /// Original role/RLS/privilege admission, fixed tenant, loopback and timeout behavior remain required.
    /// # Errors
    /// Denies absent/changed/additional migrations, unsafe roles/rights or transport failure.
    pub fn connect_schema22(
        config: &LocalPostgresConfig,
        tenant: TenantId,
    ) -> Result<Self, ArtifactError> {
        Self::connect_schema22_diagnosed(config, tenant).map_err(PostgresConnectFailure::into_error)
    }

    /// Same explicit admission with closed stages; backend diagnostics and credentials stay private.
    /// # Errors
    /// Returns an original closed error category without retaining backend errors or retrying.
    pub fn connect_schema22_diagnosed(
        config: &LocalPostgresConfig,
        tenant: TenantId,
    ) -> Result<Self, PostgresConnectFailure> {
        let repository = Self::connect_diagnosed(config, tenant)?;
        {
            let mut client = repository
                .client
                .try_lock()
                .map_err(|_| PostgresConnectFailure {
                    stage: PostgresConnectStage::Migrations,
                    error: ArtifactError::StorageFailure,
                })?;
            verify_schema22(&mut client).map_err(|error| PostgresConnectFailure {
                stage: PostgresConnectStage::Migrations,
                error,
            })?;
            verify_nonreplication_role(&mut client).map_err(|error| PostgresConnectFailure {
                stage: PostgresConnectStage::Role,
                error,
            })?;
        }
        Ok(repository)
    }
}

fn verify_nonreplication_role(client: &mut Client) -> Result<(), ArtifactError> {
    let role = client
        .query_one(
            "SELECT rolreplication FROM pg_roles WHERE rolname=current_user",
            &[],
        )
        .map_err(db_error)?;
    if value::<bool>(&role, "rolreplication")? {
        return Err(ArtifactError::AccessDenied);
    }
    Ok(())
}

fn validate(rows: &[(i64, String)]) -> Result<(), ArtifactError> {
    if rows.len() != 22 {
        return Err(ArtifactError::InvalidState);
    }
    for (index, ((version, digest), source)) in rows
        .iter()
        .zip(MIGRATIONS.iter().chain(ADDITIONAL.iter()))
        .enumerate()
    {
        if *version != i64::try_from(index + 1).map_err(|_| ArtifactError::InvalidState)?
            || *digest != ContentDigest::of(source).hex()
        {
            return Err(ArtifactError::InvalidState);
        }
    }
    Ok(())
}
fn verify_schema22(client: &mut Client) -> Result<(), ArtifactError> {
    let rows = client.query("SELECT version,migration_sha256::text FROM hwpx_agent.schema_versions ORDER BY version LIMIT 23", &[])
        .map_err(db_error)?;
    let typed = rows
        .iter()
        .map(|row| {
            Ok((
                value::<i64>(row, "version")?,
                value::<String>(row, "migration_sha256")?,
            ))
        })
        .collect::<Result<Vec<_>, ArtifactError>>()?;
    validate(&typed)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn exact() -> Vec<(i64, String)> {
        (1_i64..)
            .zip(MIGRATIONS.iter().chain(ADDITIONAL.iter()))
            .map(|(version, bytes)| (version, ContentDigest::of(bytes).hex()))
            .collect()
    }
    #[test]
    fn exact_original_22_fingerprints_admitted() {
        assert_eq!(validate(&exact()), Ok(()));
    }
    #[test]
    fn prefix17_is_not_explicit_schema22_admission() {
        assert_eq!(validate(&exact()[..17]), Err(ArtifactError::InvalidState));
    }
    #[test]
    fn additional_unknown_migration_denied() {
        let mut rows = exact();
        rows.push((23, "0".repeat(64)));
        assert_eq!(validate(&rows), Err(ArtifactError::InvalidState));
    }
    #[test]
    fn every_changed_fingerprint_denied() {
        for index in 0..22 {
            let mut rows = exact();
            rows[index].1 = "0".repeat(64);
            assert_eq!(validate(&rows), Err(ArtifactError::InvalidState));
        }
    }
    #[test]
    fn version_reordering_and_gaps_denied() {
        let mut rows = exact();
        rows.swap(17, 18);
        assert_eq!(validate(&rows), Err(ArtifactError::InvalidState));
        let mut rows = exact();
        rows[21].0 = 23;
        assert_eq!(validate(&rows), Err(ArtifactError::InvalidState));
    }
}
