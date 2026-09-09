//! Current-PC `PostgreSQL` metadata adapter. Connections are loopback-only and tenant-fixed.
//! No TLS/public-server qualification or transparent retry after an uncertain commit is implied.

use std::collections::{BTreeMap, BTreeSet};
use std::fmt;
use std::sync::{Arc, Mutex};
use std::time::Duration;

use postgres::types::FromSqlOwned;
use postgres::{Client, Config, IsolationLevel, NoTls, Row, Transaction};
use sha2::{Digest as _, Sha256};
use uuid::Uuid;
use zeroize::Zeroizing;

use super::{ArtifactMetadataRepository, ArtifactRecord, ObjectKey};
use crate::{
    ArtifactAuditEvent, ArtifactAuditOutcome, ArtifactError, ArtifactId, ArtifactKind,
    ArtifactPermission, ContentDigest, EncryptionMetadata, FileName, KeyReference, MediaType,
    QuarantineReason, ScannerReference, ScannerSignatureVersion, StorageState, SubjectDigest,
    TenantId, ValidationState,
};

const MAX_ACL_ENTRIES: usize = 256;
const MAX_AUDIT_READ: usize = 4096;
const MAX_TIMESTAMP: u64 = 253_402_300_799;
const SELECT_RECORD: &str = "SELECT tenant_id, artifact_id, content_sha256::text,
    size_bytes, media_type, filename, artifact_kind, storage_state, validation_state,
    quarantine_reason_code, scanner_engine_ref, scanner_signature_version,
    encryption_algorithm, encryption_key_ref, encryption_nonce, aad_sha256::text,
    ciphertext_sha256::text, object_key, authorization_generation, service_metadata_version,
    extract(epoch FROM created_at)::bigint AS created_seconds FROM hwpx_agent.artifacts";
const EVENT_NAMES: [&str; 8] = [
    "artifact.ingested",
    "artifact.metadata.read",
    "artifact.download",
    "artifact.signed_url.issued",
    "artifact.signed_url.redeemed",
    "artifact.acl.changed",
    "artifact.quarantined",
    "artifact.ingest.deduplicated",
];

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
const MIGRATIONS: [&[u8]; 15] = [
    migration!("0001_p14_metadata.up.sql"),
    migration!("0002_p14_artifact_service.up.sql"),
    migration!("0003_p14_revision_cas.up.sql"),
    migration!("0004_p14_history_checkpoints.up.sql"),
    migration!("0005_p14_job_state_machine.up.sql"),
    migration!("0006_p14_worker_lease_fencing.up.sql"),
    migration!("0007_p14_idempotency_reconciliation.up.sql"),
    migration!("0008_p14_cancel_cleanup.up.sql"),
    migration!("0009_p14_retention_local_mirror.up.sql"),
    migration!("0010_p16_artifact_repository.up.sql"),
    migration!("0011_p16_plan_source.up.sql"),
    migration!("0012_p16_durable_plan_store.up.sql"),
    migration!("0013_p16_plan_review_evidence.up.sql"),
    migration!("0014_p17_history_checkpoint_note.up.sql"),
    migration!("0015_p17_atomic_mirror_checkpoint.up.sql"),
];

pub struct LocalPostgresConfig {
    port: u16,
    database: String,
    user: String,
    password: Zeroizing<String>,
}

impl LocalPostgresConfig {
    /// Configures one explicitly local development connection. Arbitrary hosts/options are absent.
    ///
    /// # Errors
    /// Rejects empty credentials, unsafe identifiers and an unassigned port.
    pub fn new(
        port: u16,
        database: String,
        user: String,
        password: String,
    ) -> Result<Self, ArtifactError> {
        let password = Zeroizing::new(password);
        let valid_name = |value: &str| {
            !value.is_empty()
                && value.len() <= 63
                && value
                    .bytes()
                    .all(|byte| byte.is_ascii_alphanumeric() || byte == b'_')
        };
        if port == 0
            || !valid_name(&database)
            || !valid_name(&user)
            || password.is_empty()
            || password.len() > 1024
            || password.contains('\0')
        {
            return Err(ArtifactError::InvalidState);
        }
        Ok(Self {
            port,
            database,
            user,
            password,
        })
    }
}

impl fmt::Debug for LocalPostgresConfig {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("LocalPostgresConfig")
            .finish_non_exhaustive()
    }
}

/// Closed local diagnostic stages, never database, SQL, credential or tenant values.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PostgresConnectStage {
    Transport,
    Role,
    Migrations,
    Policies,
    Privileges,
}

impl PostgresConnectStage {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::Transport => "TRANSPORT",
            Self::Role => "ROLE",
            Self::Migrations => "MIGRATIONS",
            Self::Policies => "POLICIES",
            Self::Privileges => "PRIVILEGES",
        }
    }
}

/// Safe support evidence. The backend exception is discarded before constructing this value.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PostgresConnectFailure {
    stage: PostgresConnectStage,
    error: ArtifactError,
}

impl PostgresConnectFailure {
    #[must_use]
    pub const fn stage(&self) -> PostgresConnectStage {
        self.stage
    }

    #[must_use]
    pub const fn error(&self) -> &ArtifactError {
        &self.error
    }

    #[must_use]
    pub fn into_error(self) -> ArtifactError {
        self.error
    }
}

impl fmt::Display for PostgresConnectFailure {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}:{}", self.stage.code(), self.error.code())
    }
}

impl std::error::Error for PostgresConnectFailure {}

/// One live connection shared by clones, permanently bound to one tenant. No credential is kept
/// by this repository for retries. A busy/poisoned connection fails closed rather than queuing.
#[derive(Clone)]
pub struct LocalPostgresMetadataRepository {
    tenant: TenantId,
    client: Arc<Mutex<Client>>,
}

impl fmt::Debug for LocalPostgresMetadataRepository {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("LocalPostgresMetadataRepository")
            .finish_non_exhaustive()
    }
}

impl LocalPostgresMetadataRepository {
    /// Connects with a non-owner, non-superuser, non-BYPASSRLS application role to exact v11 metadata.
    ///
    /// # Errors
    /// Fails closed for unsafe privileges, wrong migrations, disabled RLS or a connection failure.
    /// Server/connect timeouts are bounded; this is not a general network-stall deadline guarantee.
    pub fn connect(config: &LocalPostgresConfig, tenant: TenantId) -> Result<Self, ArtifactError> {
        Self::connect_diagnosed(config, tenant).map_err(PostgresConnectFailure::into_error)
    }

    /// The same admission as `connect`, with closed stage/category evidence for local support.
    /// Never prints diagnostics, retains a backend error or retries an operation.
    ///
    /// # Errors
    /// Returns the exact failed admission stage and stable artifact error category.
    pub fn connect_diagnosed(
        config: &LocalPostgresConfig,
        tenant: TenantId,
    ) -> Result<Self, PostgresConnectFailure> {
        let mut settings = Config::new();
        settings.host("127.0.0.1").port(config.port).dbname(&config.database).user(&config.user)
            .password(config.password.as_bytes()).connect_timeout(Duration::from_secs(3))
            .application_name("hwpx-agent-local-artifact-repository")
            .options("-c statement_timeout=5000 -c lock_timeout=1000 -c idle_in_transaction_session_timeout=5000 -c transaction_timeout=10000 -c search_path=pg_catalog");
        let mut client = settings
            .connect(NoTls)
            .map_err(|error| PostgresConnectFailure {
                stage: PostgresConnectStage::Transport,
                error: db_error(error),
            })?;
        verify_database(&mut client)?;
        Ok(Self {
            tenant,
            client: Arc::new(Mutex::new(client)),
        })
    }

    fn scoped<T>(
        &self,
        tenant: TenantId,
        action: impl FnOnce(&mut Transaction<'_>) -> Result<T, ArtifactError>,
    ) -> Result<T, ArtifactError> {
        if tenant != self.tenant {
            return Err(ArtifactError::NotFound);
        }
        let mut client = self
            .client
            .try_lock()
            .map_err(|_| ArtifactError::StorageFailure)?;
        let mut transaction = client
            .build_transaction()
            .isolation_level(IsolationLevel::RepeatableRead)
            .start()
            .map_err(db_error)?;
        transaction
            .query_one(
                "SELECT set_config('hwpx_agent.tenant_id', $1, true)",
                &[&tenant.as_uuid().hyphenated().to_string()],
            )
            .map_err(db_error)?;
        let result = action(&mut transaction)?;
        transaction.commit().map_err(db_error)?;
        Ok(result)
    }
}

fn verify_database(client: &mut Client) -> Result<(), PostgresConnectFailure> {
    verify_role(client).map_err(|error| PostgresConnectFailure {
        stage: PostgresConnectStage::Role,
        error,
    })?;
    verify_migrations(client).map_err(|error| PostgresConnectFailure {
        stage: PostgresConnectStage::Migrations,
        error,
    })?;
    verify_policies(client).map_err(|error| PostgresConnectFailure {
        stage: PostgresConnectStage::Policies,
        error,
    })?;
    verify_privileges(client).map_err(|error| PostgresConnectFailure {
        stage: PostgresConnectStage::Privileges,
        error,
    })
}

fn verify_role(client: &mut Client) -> Result<(), ArtifactError> {
    let role = client.query_one("SELECT rolsuper, rolbypassrls, rolcreaterole, rolcreatedb FROM pg_roles WHERE rolname = current_user", &[]).map_err(db_error)?;
    for field in ["rolsuper", "rolbypassrls", "rolcreaterole", "rolcreatedb"] {
        if value::<bool>(&role, field)? {
            return Err(ArtifactError::AccessDenied);
        }
    }
    Ok(())
}

fn verify_migrations(client: &mut Client) -> Result<(), ArtifactError> {
    let rows = client.query("SELECT version, migration_sha256::text FROM hwpx_agent.schema_versions ORDER BY version LIMIT 16", &[]).map_err(db_error)?;
    if rows.len() != MIGRATIONS.len() {
        return Err(ArtifactError::InvalidState);
    }
    for (index, row) in rows.iter().enumerate() {
        // The authoritative migration defines version as PostgreSQL bigint (INT8).
        // postgres decodes that wire type as i64, not an implicitly narrowed i32.
        if value::<i64>(row, "version")?
            != i64::try_from(index + 1).map_err(|_| ArtifactError::InvalidState)?
            || value::<String>(row, "migration_sha256")?
                != hex::encode(Sha256::digest(MIGRATIONS[index]))
        {
            return Err(ArtifactError::InvalidState);
        }
    }
    Ok(())
}

fn verify_policies(client: &mut Client) -> Result<(), ArtifactError> {
    let rows = client.query("SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity,
        (pg_has_role(c.relowner, 'USAGE') OR pg_has_role(c.relowner, 'SET')) AS owner_role,
        (SELECT count(*) FROM pg_policy p WHERE p.polrelid=c.oid) AS policy_count,
        (SELECT count(*) FROM pg_policy p WHERE p.polrelid=c.oid AND p.polname='tenant_isolation'
          AND p.polcmd='*' AND p.polpermissive AND p.polroles=ARRAY[0::oid]
          AND pg_get_expr(p.polqual,p.polrelid)='(tenant_id = hwpx_agent.current_tenant_id())'
          AND pg_get_expr(p.polwithcheck,p.polrelid)='(tenant_id = hwpx_agent.current_tenant_id())') AS policy_match
        FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='hwpx_agent' AND c.relname IN ('artifacts','artifact_acl','artifact_service_audit')", &[]).map_err(db_error)?;
    if rows.len() != 3 {
        return Err(ArtifactError::InvalidState);
    }
    for row in rows {
        if !value::<bool>(&row, "relrowsecurity")?
            || !value::<bool>(&row, "relforcerowsecurity")?
            || value::<bool>(&row, "owner_role")?
            || value::<i64>(&row, "policy_count")? != 1
            || value::<i64>(&row, "policy_match")? != 1
        {
            return Err(ArtifactError::AccessDenied);
        }
    }
    Ok(())
}

fn verify_privileges(client: &mut Client) -> Result<(), ArtifactError> {
    let privileges = client.query_one("SELECT has_schema_privilege('hwpx_agent','CREATE')
        OR has_table_privilege('hwpx_agent.artifacts','DELETE,TRUNCATE,TRIGGER')
        OR has_table_privilege('hwpx_agent.artifact_acl','TRUNCATE,TRIGGER')
        OR has_table_privilege('hwpx_agent.artifact_service_audit','UPDATE,DELETE,TRUNCATE,TRIGGER')
        OR has_table_privilege('hwpx_agent.schema_versions','INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER') AS excessive", &[]).map_err(db_error)?;
    if value::<bool>(&privileges, "excessive")? {
        return Err(ArtifactError::AccessDenied);
    }
    Ok(())
}

fn db_error(error: postgres::Error) -> ArtifactError {
    let mapped = match error.code().map(postgres::error::SqlState::code) {
        Some("23505" | "40001" | "40P01") => ArtifactError::Conflict,
        Some("23514" | "23503" | "55000") => ArtifactError::InvalidState,
        Some("42501") => ArtifactError::AccessDenied,
        _ => ArtifactError::StorageFailure,
    };
    // Consume and discard backend diagnostics; callers receive only the stable public category.
    drop(error);
    mapped
}

fn value<T: FromSqlOwned>(row: &Row, name: &str) -> Result<T, ArtifactError> {
    row.try_get(name).map_err(db_error)
}

fn positive(value: i64) -> Result<u64, ArtifactError> {
    u64::try_from(value).map_err(|_| ArtifactError::InvalidState)
}
fn timestamp(value: u64) -> Result<i64, ArtifactError> {
    if value > MAX_TIMESTAMP {
        return Err(ArtifactError::InvalidState);
    }
    i64::try_from(value).map_err(|_| ArtifactError::InvalidState)
}
fn validation_name(state: ValidationState) -> &'static str {
    match state {
        ValidationState::Unverified => "unverified",
        ValidationState::Verified => "verified",
        ValidationState::Failed => "failed",
        ValidationState::Quarantined => "quarantined",
    }
}
fn audit_name(outcome: ArtifactAuditOutcome) -> &'static str {
    match outcome {
        ArtifactAuditOutcome::Allowed => "allowed",
        ArtifactAuditOutcome::Denied => "denied",
        ArtifactAuditOutcome::Quarantined => "quarantined",
    }
}

fn load_record(
    tx: &mut Transaction<'_>,
    tenant: TenantId,
    artifact: ArtifactId,
    lock: bool,
) -> Result<Option<ArtifactRecord>, ArtifactError> {
    let sql = format!(
        "{SELECT_RECORD} WHERE tenant_id=$1 AND artifact_id=$2{}",
        if lock { " FOR UPDATE" } else { "" }
    );
    let row = tx
        .query_opt(&sql, &[&tenant.as_uuid(), &artifact.as_uuid()])
        .map_err(db_error)?;
    row.map(|row| decode_record(tx, &row)).transpose()
}

fn decode_record(tx: &mut Transaction<'_>, row: &Row) -> Result<ArtifactRecord, ArtifactError> {
    if value::<Option<i16>>(row, "service_metadata_version")? != Some(1) {
        return Err(ArtifactError::InvalidState);
    }
    let tenant_id = TenantId::new(value::<Uuid>(row, "tenant_id")?)?;
    let artifact_id = ArtifactId::parse(&format!(
        "art_{}",
        value::<Uuid>(row, "artifact_id")?.simple()
    ))?;
    let kind_name: String = value(row, "artifact_kind")?;
    let kind = [
        ArtifactKind::Source,
        ArtifactKind::Result,
        ArtifactKind::Preview,
        ArtifactKind::Evidence,
        ArtifactKind::Trace,
        ArtifactKind::Diff,
        ArtifactKind::Receipt,
    ]
    .into_iter()
    .find(|kind| kind.as_str() == kind_name)
    .ok_or(ArtifactError::InvalidState)?;
    let storage_name: String = value(row, "storage_state")?;
    let storage_state = [StorageState::Available, StorageState::Quarantined]
        .into_iter()
        .find(|state| state.as_str() == storage_name)
        .ok_or(ArtifactError::InvalidState)?;
    let validation: String = value(row, "validation_state")?;
    let validation_state = [
        ValidationState::Unverified,
        ValidationState::Verified,
        ValidationState::Failed,
        ValidationState::Quarantined,
    ]
    .into_iter()
    .find(|state| validation_name(*state) == validation)
    .ok_or(ArtifactError::InvalidState)?;
    if value::<String>(row, "encryption_algorithm")? != "AES-256-GCM" {
        return Err(ArtifactError::IntegrityMismatch);
    }
    let nonce: Vec<u8> = value(row, "encryption_nonce")?;
    let rows = tx.query("SELECT subject_sha256::text, can_read, can_manage, can_read_quarantine FROM hwpx_agent.artifact_acl
        WHERE tenant_id=$1 AND artifact_id=$2 ORDER BY subject_sha256 LIMIT 257", &[&tenant_id.as_uuid(),&artifact_id.as_uuid()]).map_err(db_error)?;
    if rows.len() > MAX_ACL_ENTRIES {
        return Err(ArtifactError::StorageFailure);
    }
    let mut acl = BTreeMap::new();
    for entry in rows {
        let mut permissions = BTreeSet::new();
        for (column, permission) in [
            ("can_read", ArtifactPermission::Read),
            ("can_manage", ArtifactPermission::Manage),
            ("can_read_quarantine", ArtifactPermission::QuarantineRead),
        ] {
            if value::<bool>(&entry, column)? {
                permissions.insert(permission);
            }
        }
        if permissions.is_empty() {
            return Err(ArtifactError::InvalidState);
        }
        acl.insert(
            SubjectDigest::parse(&value::<String>(&entry, "subject_sha256")?)?,
            permissions,
        );
    }
    let record = ArtifactRecord {
        tenant_id,
        artifact_id,
        kind,
        storage_state,
        validation_state,
        acl,
        content_sha256: ContentDigest::parse(&value::<String>(row, "content_sha256")?)?,
        size_bytes: positive(value(row, "size_bytes")?)?,
        media_type: MediaType::parse(value::<String>(row, "media_type")?)?,
        file_name: FileName::parse(value::<String>(row, "filename")?)?,
        quarantine_reason: value::<Option<String>>(row, "quarantine_reason_code")?
            .map(QuarantineReason::parse)
            .transpose()?,
        scanner_engine: ScannerReference::parse(value::<String>(row, "scanner_engine_ref")?)?,
        scanner_signature_version: ScannerSignatureVersion::parse(value::<String>(
            row,
            "scanner_signature_version",
        )?)?,
        encryption: EncryptionMetadata {
            algorithm: "AES-256-GCM",
            key_ref: KeyReference::parse(value::<String>(row, "encryption_key_ref")?)?,
            nonce: nonce
                .try_into()
                .map_err(|_| ArtifactError::IntegrityMismatch)?,
            aad_sha256: ContentDigest::parse(&value::<String>(row, "aad_sha256")?)?,
            ciphertext_sha256: ContentDigest::parse(&value::<String>(row, "ciphertext_sha256")?)?,
        },
        object_key: ObjectKey::parse(value::<String>(row, "object_key")?)?,
        acl_version: positive(value(row, "authorization_generation")?)?,
        created_at_unix_seconds: positive(value(row, "created_seconds")?)?,
    };
    record.validate()?;
    timestamp(record.created_at_unix_seconds)?;
    Ok(record)
}

impl ArtifactMetadataRepository for LocalPostgresMetadataRepository {
    fn find(
        &self,
        tenant: TenantId,
        artifact: ArtifactId,
    ) -> Result<Option<ArtifactRecord>, ArtifactError> {
        self.scoped(tenant, |tx| load_record(tx, tenant, artifact, false))
    }

    fn find_by_content(
        &self,
        tenant: TenantId,
        digest: ContentDigest,
    ) -> Result<Option<ArtifactRecord>, ArtifactError> {
        self.scoped(tenant, |tx| {
            let row = tx
                .query_opt(
                    &format!("{SELECT_RECORD} WHERE tenant_id=$1 AND content_sha256=$2"),
                    &[&tenant.as_uuid(), &digest.hex()],
                )
                .map_err(db_error)?;
            row.map(|row| decode_record(tx, &row)).transpose()
        })
    }

    fn insert(&self, record: ArtifactRecord) -> Result<(), ArtifactError> {
        record.validate()?;
        if record.acl_version != 1 || record.acl.len() != 1 {
            return Err(ArtifactError::InvalidState);
        }
        self.scoped(record.tenant_id, |tx| {
            let size = i64::try_from(record.size_bytes).map_err(|_| ArtifactError::InvalidState)?;
            let created = timestamp(record.created_at_unix_seconds)?;
            tx.execute("INSERT INTO hwpx_agent.artifacts (
                tenant_id,artifact_id,content_sha256,size_bytes,media_type,artifact_kind,storage_state,
                quarantine_reason_code,encryption_key_ref,created_at,updated_at,verified_at,
                service_metadata_version,filename,object_key,encryption_algorithm,encryption_nonce,
                aad_sha256,ciphertext_sha256,validation_state,scanner_engine_ref,scanner_signature_version,authorization_generation)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,to_timestamp($10::bigint::double precision),
                to_timestamp($10::bigint::double precision),CASE WHEN $7='available' THEN to_timestamp($10::bigint::double precision) ELSE NULL END,
                1,$11,$12,'AES-256-GCM',$13,$14,$15,$16,$17,$18,1)", &[
                &record.tenant_id.as_uuid(),&record.artifact_id.as_uuid(),&record.content_sha256.hex(),&size,
                &record.media_type.as_str(),&record.kind.as_str(),&record.storage_state.as_str(),
                &record.quarantine_reason.as_ref().map(QuarantineReason::as_str),&record.encryption.key_ref.as_str(),&created,
                &record.file_name.as_str(),&record.object_key.as_str(),&&record.encryption.nonce[..],
                &record.encryption.aad_sha256.hex(),&record.encryption.ciphertext_sha256.hex(),&validation_name(record.validation_state),
                &record.scanner_engine.as_str(),&record.scanner_signature_version.as_str(),
            ]).map_err(db_error)?;
            for (subject, permissions) in &record.acl {
                tx.execute("INSERT INTO hwpx_agent.artifact_acl (tenant_id,artifact_id,subject_sha256,can_read,can_manage,can_read_quarantine)
                    VALUES ($1,$2,$3,$4,$5,$6)", &[&record.tenant_id.as_uuid(),&record.artifact_id.as_uuid(),&subject.hex(),
                    &permissions.contains(&ArtifactPermission::Read),&permissions.contains(&ArtifactPermission::Manage),
                    &permissions.contains(&ArtifactPermission::QuarantineRead)]).map_err(db_error)?;
            }
            Ok(())
        })
    }

    fn transition_state(
        &self,
        tenant: TenantId,
        artifact: ArtifactId,
        expected_acl_version: u64,
        expected_state: StorageState,
        new_state: StorageState,
        validation_state: ValidationState,
        reason: Option<QuarantineReason>,
        object_key: ObjectKey,
    ) -> Result<ArtifactRecord, ArtifactError> {
        self.scoped(tenant, |tx| {
            let mut record = load_record(tx,tenant,artifact,true)?.ok_or(ArtifactError::NotFound)?;
            if record.acl_version != expected_acl_version || record.storage_state != expected_state { return Err(ArtifactError::Conflict); }
            record.storage_state = new_state; record.validation_state = validation_state;
            record.quarantine_reason = reason; record.object_key = object_key;
            record.acl_version = record.acl_version.checked_add(1).ok_or(ArtifactError::Conflict)?;
            record.validate()?;
            tx.execute("UPDATE hwpx_agent.artifacts SET storage_state=$3,validation_state=$4,quarantine_reason_code=$5,
                object_key=$6,authorization_generation=authorization_generation+1,
                verified_at=CASE WHEN $3='available' THEN created_at ELSE NULL END
                WHERE tenant_id=$1 AND artifact_id=$2", &[&tenant.as_uuid(),&artifact.as_uuid(),&new_state.as_str(),
                &validation_name(validation_state),&record.quarantine_reason.as_ref().map(QuarantineReason::as_str),&record.object_key.as_str()]).map_err(db_error)?;
            load_record(tx,tenant,artifact,false)?.ok_or(ArtifactError::NotFound)
        })
    }

    fn set_permissions(
        &self,
        tenant: TenantId,
        artifact: ArtifactId,
        expected_acl_version: u64,
        subject: SubjectDigest,
        permissions: BTreeSet<ArtifactPermission>,
    ) -> Result<ArtifactRecord, ArtifactError> {
        self.scoped(tenant, |tx| {
            let record = load_record(tx,tenant,artifact,true)?.ok_or(ArtifactError::NotFound)?;
            if record.acl_version != expected_acl_version { return Err(ArtifactError::Conflict); }
            if !permissions.is_empty() && !record.acl.contains_key(&subject) && record.acl.len() >= MAX_ACL_ENTRIES { return Err(ArtifactError::StorageFailure); }
            if permissions.is_empty() {
                let changed = tx.execute("DELETE FROM hwpx_agent.artifact_acl WHERE tenant_id=$1 AND artifact_id=$2 AND subject_sha256=$3",
                    &[&tenant.as_uuid(),&artifact.as_uuid(),&subject.hex()]).map_err(db_error)?;
                if changed == 0 {
                    tx.execute("UPDATE hwpx_agent.artifacts SET authorization_generation=authorization_generation+1 WHERE tenant_id=$1 AND artifact_id=$2",
                        &[&tenant.as_uuid(),&artifact.as_uuid()]).map_err(db_error)?;
                }
            } else {
                tx.execute("INSERT INTO hwpx_agent.artifact_acl (tenant_id,artifact_id,subject_sha256,can_read,can_manage,can_read_quarantine)
                    VALUES ($1,$2,$3,$4,$5,$6) ON CONFLICT (tenant_id,artifact_id,subject_sha256)
                    DO UPDATE SET can_read=EXCLUDED.can_read,can_manage=EXCLUDED.can_manage,can_read_quarantine=EXCLUDED.can_read_quarantine",
                    &[&tenant.as_uuid(),&artifact.as_uuid(),&subject.hex(),&permissions.contains(&ArtifactPermission::Read),
                    &permissions.contains(&ArtifactPermission::Manage),&permissions.contains(&ArtifactPermission::QuarantineRead)]).map_err(db_error)?;
            }
            let changed = load_record(tx,tenant,artifact,false)?.ok_or(ArtifactError::NotFound)?;
            if expected_acl_version.checked_add(1) != Some(changed.acl_version) { return Err(ArtifactError::Conflict); }
            Ok(changed)
        })
    }

    fn append_audit(&self, event: ArtifactAuditEvent) -> Result<(), ArtifactError> {
        if !EVENT_NAMES.contains(&event.event) {
            return Err(ArtifactError::InvalidState);
        }
        self.scoped(event.tenant_id, |tx| {
            let changed = tx.execute("INSERT INTO hwpx_agent.artifact_service_audit
                (tenant_id,artifact_id,event_type,subject_sha256,content_sha256,outcome,recorded_at_unix_seconds)
                SELECT tenant_id,artifact_id,$3,$4,content_sha256,$5,$6 FROM hwpx_agent.artifacts
                WHERE tenant_id=$1 AND artifact_id=$2 AND content_sha256=$7",
                &[&event.tenant_id.as_uuid(),&event.artifact_id.as_uuid(),&event.event,&event.subject_sha256.hex(),
                &audit_name(event.outcome),&timestamp(event.recorded_at_unix_seconds)?,&event.content_sha256.hex()]).map_err(db_error)?;
            if changed != 1 { return Err(ArtifactError::NotFound); }
            Ok(())
        })
    }

    fn audit_events(&self) -> Result<Vec<ArtifactAuditEvent>, ArtifactError> {
        self.scoped(self.tenant, |tx| {
            let rows = tx.query("SELECT tenant_id,artifact_id,event_type,subject_sha256::text,content_sha256::text,outcome,recorded_at_unix_seconds
                FROM hwpx_agent.artifact_service_audit WHERE tenant_id=$1 ORDER BY event_id LIMIT 4097", &[&self.tenant.as_uuid()]).map_err(db_error)?;
            if rows.len() > MAX_AUDIT_READ { return Err(ArtifactError::StorageFailure); }
            rows.iter().map(|row| {
                let event_name: String = value(row,"event_type")?;
                let event = EVENT_NAMES.into_iter().find(|name| *name == event_name).ok_or(ArtifactError::InvalidState)?;
                let outcome_name: String = value(row,"outcome")?;
                let outcome = [ArtifactAuditOutcome::Allowed,ArtifactAuditOutcome::Denied,ArtifactAuditOutcome::Quarantined]
                    .into_iter().find(|outcome| audit_name(*outcome) == outcome_name).ok_or(ArtifactError::InvalidState)?;
                Ok(ArtifactAuditEvent { event, outcome,
                    tenant_id: TenantId::new(value(row,"tenant_id")?)?,
                    artifact_id: ArtifactId::parse(&format!("art_{}",value::<Uuid>(row,"artifact_id")?.simple()))?,
                    subject_sha256: SubjectDigest::parse(&value::<String>(row,"subject_sha256")?)?,
                    content_sha256: ContentDigest::parse(&value::<String>(row,"content_sha256")?)?,
                    recorded_at_unix_seconds: positive(value(row,"recorded_at_unix_seconds")?)?,
                })
            }).collect()
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::error::Error as _;

    #[test]
    fn local_config_admission_rejects_unsafe_or_unbounded_values() {
        for (port, database, user, password) in [
            (
                0,
                "postgres".to_owned(),
                "app".to_owned(),
                "synthetic".to_owned(),
            ),
            (1, String::new(), "app".to_owned(), "synthetic".to_owned()),
            (
                1,
                "database;statement".to_owned(),
                "app".to_owned(),
                "synthetic".to_owned(),
            ),
            (
                1,
                "postgres".to_owned(),
                "x".repeat(64),
                "synthetic".to_owned(),
            ),
            (1, "postgres".to_owned(), "app".to_owned(), String::new()),
            (1, "postgres".to_owned(), "app".to_owned(), "x".repeat(1025)),
            (
                1,
                "postgres".to_owned(),
                "app".to_owned(),
                "bad\0password".to_owned(),
            ),
        ] {
            assert_eq!(
                LocalPostgresConfig::new(port, database, user, password).err(),
                Some(ArtifactError::InvalidState)
            );
        }
        assert!(
            LocalPostgresConfig::new(65535, "x".repeat(63), "x".repeat(63), "x".repeat(1024))
                .is_ok()
        );
    }

    #[test]
    fn local_config_debug_omits_all_private_connection_values() {
        let config = LocalPostgresConfig::new(
            54321,
            "private_database".to_owned(),
            "private_user".to_owned(),
            "private_synthetic_password".to_owned(),
        )
        .unwrap_or_else(|error| panic!("synthetic configuration: {error}"));
        assert_eq!(format!("{config:?}"), "LocalPostgresConfig { .. }");
    }

    #[test]
    fn diagnosed_failure_keeps_only_closed_stage_and_public_error() {
        let stages = [
            PostgresConnectStage::Transport,
            PostgresConnectStage::Role,
            PostgresConnectStage::Migrations,
            PostgresConnectStage::Policies,
            PostgresConnectStage::Privileges,
        ];
        let codes = ["TRANSPORT", "ROLE", "MIGRATIONS", "POLICIES", "PRIVILEGES"];
        for (stage, code) in stages.into_iter().zip(codes) {
            let failure = PostgresConnectFailure {
                stage,
                error: ArtifactError::AccessDenied,
            };
            assert_eq!(failure.stage(), stage);
            assert_eq!(stage.code(), code);
            assert_eq!(failure.to_string(), format!("{code}:ACCESS_DENIED"));
            assert_eq!(failure.error(), &ArtifactError::AccessDenied);
            assert!(failure.source().is_none());
            assert_eq!(failure.into_error(), ArtifactError::AccessDenied);
        }
    }
}
