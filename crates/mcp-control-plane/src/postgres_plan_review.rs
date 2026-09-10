//! Encrypted, tenant-isolated persistence for authoritative plan-review evidence.
//!
//! The repository stores only a bounded canonical receipt envelope and restores its typed receipts
//! against the plan that the renderer has already freshly authenticated and source-authorized.

use std::collections::BTreeMap;
use std::fmt;
use std::sync::{Arc, Mutex};
use std::time::Duration;

use aes_gcm::aead::{Aead as _, KeyInit as _, Payload};
use aes_gcm::{Aes256Gcm, Nonce};
use artifact_service::{KeyReference, SubjectDigest, TenantId};
use postgres::types::FromSqlOwned;
use postgres::{Client, Config, IsolationLevel, NoTls, Row, Transaction};
use sha2::{Digest as _, Sha256};
use uuid::Uuid;
use zeroize::{Zeroize as _, Zeroizing};

use crate::plan_review::{PlanReviewEvidenceQuery, PlanReviewEvidenceStorageBinding};
use crate::{
    AuthorizedStoredPlan, PlanReviewError, PlanReviewEvidence, PlanReviewEvidenceRepository,
};

const AES_GCM_ALGORITHM: &str = "AES-256-GCM";
const GCM_NONCE_BYTES: usize = 12;
const GCM_TAG_BYTES: usize = 16;
const MAX_KEYS: usize = 16;
const MAX_EVIDENCE_BYTES: usize = 1024 * 1024;

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

const MIGRATIONS: [&[u8]; 16] = [
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
    migration!("0016_p17_durable_git_mirror_push.up.sql"),
];

/// Bounded encryption keyring for persisted review evidence and key rotation.
pub struct DurablePlanReviewEvidenceKeyring {
    active_key_ref: KeyReference,
    ciphers: BTreeMap<KeyReference, Aes256Gcm>,
}

impl DurablePlanReviewEvidenceKeyring {
    /// Creates an AES-256-GCM keyring.
    ///
    /// # Errors
    /// Rejects malformed or duplicate references, zero keys and an absent active key.
    pub fn new(
        active_key_ref: impl Into<String>,
        keys: impl IntoIterator<Item = (String, [u8; 32])>,
    ) -> Result<Self, PlanReviewError> {
        let active_key_ref = KeyReference::parse(active_key_ref.into())
            .map_err(|_| PlanReviewError::InvalidEvidence)?;
        let mut ciphers = BTreeMap::new();
        for (reference, mut key_bytes) in keys {
            if ciphers.len() >= MAX_KEYS || key_bytes == [0; 32] {
                key_bytes.zeroize();
                return Err(PlanReviewError::InvalidEvidence);
            }
            let Ok(reference) = KeyReference::parse(reference) else {
                key_bytes.zeroize();
                return Err(PlanReviewError::InvalidEvidence);
            };
            let cipher =
                Aes256Gcm::new_from_slice(&key_bytes).map_err(|_| PlanReviewError::InvalidEvidence);
            key_bytes.zeroize();
            if ciphers.insert(reference, cipher?).is_some() {
                return Err(PlanReviewError::InvalidEvidence);
            }
        }
        if ciphers.is_empty() || !ciphers.contains_key(&active_key_ref) {
            return Err(PlanReviewError::InvalidEvidence);
        }
        Ok(Self {
            active_key_ref,
            ciphers,
        })
    }

    fn encrypt(
        &self,
        binding: &EvidenceCryptoBinding<'_>,
        plaintext: &[u8],
    ) -> Result<EncryptedEvidence, PlanReviewError> {
        let cipher = self
            .ciphers
            .get(&self.active_key_ref)
            .ok_or(PlanReviewError::EvidenceUnavailable)?;
        let aad = binding.aad(&self.active_key_ref)?;
        let mut nonce_bytes = [0_u8; GCM_NONCE_BYTES];
        getrandom::fill(&mut nonce_bytes).map_err(|_| PlanReviewError::EvidenceUnavailable)?;
        let ciphertext = cipher
            .encrypt(
                &Nonce::from(nonce_bytes),
                Payload {
                    msg: plaintext,
                    aad: &aad,
                },
            )
            .map_err(|_| PlanReviewError::EvidenceUnavailable)?;
        if ciphertext.len() != plaintext.len() + GCM_TAG_BYTES {
            return Err(PlanReviewError::EvidenceUnavailable);
        }
        Ok(EncryptedEvidence {
            key_ref: self.active_key_ref.clone(),
            nonce: nonce_bytes,
            aad_digest: Sha256::digest(aad).into(),
            ciphertext_digest: Sha256::digest(&ciphertext).into(),
            ciphertext,
        })
    }

    fn decrypt(
        &self,
        binding: &EvidenceCryptoBinding<'_>,
        encrypted: &EncryptedEvidence,
    ) -> Result<Zeroizing<Vec<u8>>, PlanReviewError> {
        if encrypted.ciphertext.len() != binding.plaintext_bytes + GCM_TAG_BYTES
            || Sha256::digest(&encrypted.ciphertext).as_slice() != encrypted.ciphertext_digest
        {
            return Err(PlanReviewError::EvidenceUnavailable);
        }
        let aad = binding.aad(&encrypted.key_ref)?;
        if Sha256::digest(&aad).as_slice() != encrypted.aad_digest {
            return Err(PlanReviewError::EvidenceUnavailable);
        }
        let cipher = self
            .ciphers
            .get(&encrypted.key_ref)
            .ok_or(PlanReviewError::EvidenceUnavailable)?;
        let plaintext = cipher
            .decrypt(
                &Nonce::from(encrypted.nonce),
                Payload {
                    msg: &encrypted.ciphertext,
                    aad: &aad,
                },
            )
            .map_err(|_| PlanReviewError::EvidenceUnavailable)?;
        if plaintext.len() != binding.plaintext_bytes
            || Sha256::digest(&plaintext).as_slice() != binding.evidence_digest
        {
            return Err(PlanReviewError::EvidenceUnavailable);
        }
        Ok(Zeroizing::new(plaintext))
    }
}

impl fmt::Debug for DurablePlanReviewEvidenceKeyring {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("DurablePlanReviewEvidenceKeyring")
            .field("key_count", &self.ciphers.len())
            .finish_non_exhaustive()
    }
}

/// Loopback-only database coordinates for the review-evidence role.
pub struct LocalPostgresPlanReviewEvidenceConfig {
    port: u16,
    database: String,
    user: String,
    password: Zeroizing<String>,
}

impl LocalPostgresPlanReviewEvidenceConfig {
    /// Creates bounded local connection settings.
    ///
    /// # Errors
    /// Rejects an unassigned port, malformed names and empty or oversized credentials.
    pub fn new(
        port: u16,
        database: String,
        user: String,
        password: String,
    ) -> Result<Self, PlanReviewError> {
        let valid_name = |value: &str| {
            !value.is_empty()
                && value.len() <= 63
                && value
                    .bytes()
                    .all(|byte| byte.is_ascii_alphanumeric() || byte == b'_')
        };
        let password = Zeroizing::new(password);
        if port == 0
            || !valid_name(&database)
            || !valid_name(&user)
            || password.is_empty()
            || password.len() > 1024
            || password.contains('\0')
        {
            return Err(PlanReviewError::InvalidEvidence);
        }
        Ok(Self {
            port,
            database,
            user,
            password,
        })
    }
}

impl fmt::Debug for LocalPostgresPlanReviewEvidenceConfig {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("LocalPostgresPlanReviewEvidenceConfig")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PlanReviewEvidenceConnectStage {
    Transport,
    Role,
    Migrations,
    Policies,
    Privileges,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct PlanReviewEvidenceConnectFailure {
    pub stage: PlanReviewEvidenceConnectStage,
    pub error: PlanReviewError,
}

impl fmt::Display for PlanReviewEvidenceConnectFailure {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "{:?}:{:?}", self.stage, self.error)
    }
}

impl std::error::Error for PlanReviewEvidenceConnectFailure {}

/// Tenant-bound authoritative review-evidence repository.
pub struct LocalPostgresPlanReviewEvidenceRepository {
    tenant: TenantId,
    client: Arc<Mutex<Client>>,
    keyring: DurablePlanReviewEvidenceKeyring,
}

impl LocalPostgresPlanReviewEvidenceRepository {
    /// Connects to the exact v13 schema after checking role, RLS and privileges.
    ///
    /// # Errors
    /// Fails closed with a stable admission stage.
    pub fn connect(
        config: &LocalPostgresPlanReviewEvidenceConfig,
        tenant: TenantId,
        keyring: DurablePlanReviewEvidenceKeyring,
    ) -> Result<Self, PlanReviewEvidenceConnectFailure> {
        let mut settings = Config::new();
        settings
            .host("127.0.0.1")
            .port(config.port)
            .dbname(&config.database)
            .user(&config.user)
            .password(config.password.as_bytes())
            .connect_timeout(Duration::from_secs(3))
            .application_name("hwpx-agent-local-plan-review-evidence")
            .options("-c statement_timeout=5000 -c lock_timeout=1000 -c idle_in_transaction_session_timeout=5000 -c transaction_timeout=10000 -c search_path=pg_catalog");
        let mut client = settings.connect(NoTls).map_err(|error| {
            drop(error);
            PlanReviewEvidenceConnectFailure {
                stage: PlanReviewEvidenceConnectStage::Transport,
                error: PlanReviewError::EvidenceUnavailable,
            }
        })?;
        verify_database(&mut client)?;
        Ok(Self {
            tenant,
            client: Arc::new(Mutex::new(client)),
            keyring,
        })
    }

    /// Encrypts and create-once stores one complete receipt bundle for an authorized plan.
    ///
    /// # Errors
    /// Rejects plan/evidence drift, expiry, limits, conflicts, crypto or database failure.
    pub fn store(
        &self,
        authorized: &AuthorizedStoredPlan,
        evidence: &PlanReviewEvidence,
        now_unix_seconds: u64,
    ) -> Result<(), PlanReviewError> {
        let record = &authorized.record;
        if record.tenant != self.tenant
            || now_unix_seconds < record.stored_at
            || now_unix_seconds >= record.expires_at
        {
            return Err(PlanReviewError::EvidenceUnavailable);
        }
        let query = PlanReviewEvidenceQuery::for_authorized(authorized);
        let plaintext = Zeroizing::new(evidence.canonical_storage_json(&query)?);
        if plaintext.is_empty() || plaintext.len() > MAX_EVIDENCE_BYTES {
            return Err(PlanReviewError::LimitExceeded);
        }
        let project_uuid = database_id(query.project_id(), "prj_")?;
        let binding_values = evidence.storage_binding();
        let binding = EvidenceCryptoBinding {
            tenant: self.tenant,
            project_uuid,
            plan_id: query.plan().plan_id().as_str(),
            owner: query.subject(),
            plan_digest: query.compiled_plan_sha256(),
            receipt_binding: binding_values,
            evidence_digest: Sha256::digest(&plaintext).into(),
            plaintext_bytes: plaintext.len(),
            stored_at: now_unix_seconds,
            expires_at: record.expires_at,
        };
        let encrypted = self.keyring.encrypt(&binding, &plaintext)?;
        self.insert_record(&binding, &encrypted)
    }

    fn scoped<T>(
        &self,
        read_only: bool,
        action: impl FnOnce(&mut Transaction<'_>) -> Result<T, PlanReviewError>,
    ) -> Result<T, PlanReviewError> {
        let mut client = self
            .client
            .try_lock()
            .map_err(|_| PlanReviewError::EvidenceUnavailable)?;
        let mut transaction = client
            .build_transaction()
            .isolation_level(if read_only {
                IsolationLevel::RepeatableRead
            } else {
                IsolationLevel::Serializable
            })
            .read_only(read_only)
            .start()
            .map_err(db_error)?;
        transaction
            .query_one(
                "SELECT set_config('hwpx_agent.tenant_id',$1,true)",
                &[&self.tenant.as_uuid().hyphenated().to_string()],
            )
            .map_err(db_error)?;
        let result = action(&mut transaction)?;
        transaction.commit().map_err(db_error)?;
        Ok(result)
    }

    fn insert_record(
        &self,
        binding: &EvidenceCryptoBinding<'_>,
        encrypted: &EncryptedEvidence,
    ) -> Result<(), PlanReviewError> {
        let tenant = binding.tenant.as_uuid();
        let owner = binding.owner.hex();
        let plan_digest = hex::encode(binding.plan_digest);
        let route_digest = hex::encode(binding.receipt_binding.route_set);
        let diff_digest = hex::encode(binding.receipt_binding.semantic_diff);
        let result_digest = hex::encode(binding.receipt_binding.result_graph);
        let evidence_digest = hex::encode(binding.evidence_digest);
        let aad_digest = hex::encode(encrypted.aad_digest);
        let ciphertext_digest = hex::encode(encrypted.ciphertext_digest);
        let plaintext_bytes =
            i64::try_from(binding.plaintext_bytes).map_err(|_| PlanReviewError::LimitExceeded)?;
        let stored_at =
            i64::try_from(binding.stored_at).map_err(|_| PlanReviewError::InvalidEvidence)?;
        let expires_at =
            i64::try_from(binding.expires_at).map_err(|_| PlanReviewError::InvalidEvidence)?;
        self.scoped(false, |transaction| {
            purge_expired(transaction)?;
            let row = transaction
                .query_opt(
                    "INSERT INTO hwpx_agent.plan_review_evidence_records(
                       tenant_id,project_id,plan_id,created_by_subject_sha256,
                       compiled_plan_sha256,route_set_sha256,semantic_diff_sha256,
                       result_graph_sha256,evidence_sha256,plaintext_bytes,encryption_algorithm,
                       encryption_key_ref,nonce,aad_sha256,ciphertext_sha256,ciphertext,
                       stored_at_unix_seconds,expires_at_unix_seconds)
                     VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18)
                     ON CONFLICT (tenant_id,project_id,plan_id) DO NOTHING RETURNING plan_id",
                    &[
                        &tenant,
                        &binding.project_uuid,
                        &binding.plan_id,
                        &owner,
                        &plan_digest,
                        &route_digest,
                        &diff_digest,
                        &result_digest,
                        &evidence_digest,
                        &plaintext_bytes,
                        &AES_GCM_ALGORITHM,
                        &encrypted.key_ref.as_str(),
                        &&encrypted.nonce[..],
                        &aad_digest,
                        &ciphertext_digest,
                        &encrypted.ciphertext,
                        &stored_at,
                        &expires_at,
                    ],
                )
                .map_err(db_error)?;
            if row.is_none() {
                return Err(PlanReviewError::InvalidEvidence);
            }
            Ok(())
        })
    }

    fn read_record(&self, project_uuid: Uuid, plan_id: &str) -> Result<Row, PlanReviewError> {
        let tenant = self.tenant.as_uuid();
        self.scoped(true, |transaction| {
            transaction
                .query_opt(
                    "SELECT created_by_subject_sha256::text,compiled_plan_sha256::text,
                            route_set_sha256::text,semantic_diff_sha256::text,
                            result_graph_sha256::text,evidence_sha256::text,plaintext_bytes,
                            encryption_algorithm,encryption_key_ref,nonce,aad_sha256::text,
                            ciphertext_sha256::text,ciphertext,stored_at_unix_seconds,
                            expires_at_unix_seconds
                     FROM hwpx_agent.plan_review_evidence_records
                     WHERE tenant_id=$1 AND project_id=$2 AND plan_id=$3",
                    &[&tenant, &project_uuid, &plan_id],
                )
                .map_err(db_error)?
                .ok_or(PlanReviewError::EvidenceUnavailable)
        })
    }

    fn restore_record(
        &self,
        query: &PlanReviewEvidenceQuery<'_>,
        project_uuid: Uuid,
        row: &Row,
    ) -> Result<PlanReviewEvidence, PlanReviewError> {
        let owner = SubjectDigest::parse(&value::<String>(row, "created_by_subject_sha256")?)
            .map_err(|_| PlanReviewError::EvidenceUnavailable)?;
        let plan_digest = digest_bytes(&value::<String>(row, "compiled_plan_sha256")?)?;
        let receipt_binding = PlanReviewEvidenceStorageBinding {
            route_set: digest_bytes(&value::<String>(row, "route_set_sha256")?)?,
            semantic_diff: digest_bytes(&value::<String>(row, "semantic_diff_sha256")?)?,
            result_graph: digest_bytes(&value::<String>(row, "result_graph_sha256")?)?,
        };
        let evidence_digest = digest_bytes(&value::<String>(row, "evidence_sha256")?)?;
        let plaintext_bytes = positive_usize(value(row, "plaintext_bytes")?)?;
        if owner != query.subject()
            || plan_digest != query.compiled_plan_sha256()
            || plaintext_bytes > MAX_EVIDENCE_BYTES
            || value::<String>(row, "encryption_algorithm")? != AES_GCM_ALGORITHM
        {
            return Err(PlanReviewError::EvidenceUnavailable);
        }
        let key_ref = KeyReference::parse(value::<String>(row, "encryption_key_ref")?)
            .map_err(|_| PlanReviewError::EvidenceUnavailable)?;
        let nonce = value::<Vec<u8>>(row, "nonce")?
            .try_into()
            .map_err(|_| PlanReviewError::EvidenceUnavailable)?;
        let encrypted = EncryptedEvidence {
            key_ref,
            nonce,
            aad_digest: digest_bytes(&value::<String>(row, "aad_sha256")?)?,
            ciphertext_digest: digest_bytes(&value::<String>(row, "ciphertext_sha256")?)?,
            ciphertext: value(row, "ciphertext")?,
        };
        let stored_at = nonnegative_u64(value(row, "stored_at_unix_seconds")?)?;
        let expires_at = nonnegative_u64(value(row, "expires_at_unix_seconds")?)?;
        if expires_at <= stored_at || expires_at - stored_at > 900 {
            return Err(PlanReviewError::EvidenceUnavailable);
        }
        let binding = EvidenceCryptoBinding {
            tenant: self.tenant,
            project_uuid,
            plan_id: query.plan().plan_id().as_str(),
            owner,
            plan_digest,
            receipt_binding,
            evidence_digest,
            plaintext_bytes,
            stored_at,
            expires_at,
        };
        let plaintext = self.keyring.decrypt(&binding, &encrypted)?;
        let evidence = PlanReviewEvidence::from_canonical_storage_json(query, &plaintext)?;
        if evidence.storage_binding() != receipt_binding {
            return Err(PlanReviewError::EvidenceUnavailable);
        }
        Ok(evidence)
    }
}

impl PlanReviewEvidenceRepository for LocalPostgresPlanReviewEvidenceRepository {
    fn load(
        &mut self,
        query: &PlanReviewEvidenceQuery<'_>,
    ) -> Result<PlanReviewEvidence, PlanReviewError> {
        if query.tenant_id() != self.tenant {
            return Err(PlanReviewError::EvidenceUnavailable);
        }
        let project_uuid = database_id(query.project_id(), "prj_")?;
        let row = self.read_record(project_uuid, query.plan().plan_id().as_str())?;
        self.restore_record(query, project_uuid, &row)
    }
}

impl fmt::Debug for LocalPostgresPlanReviewEvidenceRepository {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("LocalPostgresPlanReviewEvidenceRepository")
            .finish_non_exhaustive()
    }
}

struct EvidenceCryptoBinding<'a> {
    tenant: TenantId,
    project_uuid: Uuid,
    plan_id: &'a str,
    owner: SubjectDigest,
    plan_digest: [u8; 32],
    receipt_binding: PlanReviewEvidenceStorageBinding,
    evidence_digest: [u8; 32],
    plaintext_bytes: usize,
    stored_at: u64,
    expires_at: u64,
}

impl EvidenceCryptoBinding<'_> {
    fn aad(&self, key_ref: &KeyReference) -> Result<Vec<u8>, PlanReviewError> {
        let plaintext_bytes =
            u64::try_from(self.plaintext_bytes).map_err(|_| PlanReviewError::LimitExceeded)?;
        let mut aad = Vec::with_capacity(640);
        append_field(&mut aad, b"hwpx-agent.durable-plan-review-evidence/v1")?;
        append_field(&mut aad, self.tenant.as_uuid().as_bytes())?;
        append_field(&mut aad, self.project_uuid.as_bytes())?;
        append_field(&mut aad, self.plan_id.as_bytes())?;
        append_field(&mut aad, self.owner.as_bytes())?;
        append_field(&mut aad, &self.plan_digest)?;
        append_field(&mut aad, &self.receipt_binding.route_set)?;
        append_field(&mut aad, &self.receipt_binding.semantic_diff)?;
        append_field(&mut aad, &self.receipt_binding.result_graph)?;
        append_field(&mut aad, &self.evidence_digest)?;
        append_field(&mut aad, &plaintext_bytes.to_be_bytes())?;
        append_field(&mut aad, &self.stored_at.to_be_bytes())?;
        append_field(&mut aad, &self.expires_at.to_be_bytes())?;
        append_field(&mut aad, AES_GCM_ALGORITHM.as_bytes())?;
        append_field(&mut aad, key_ref.as_str().as_bytes())?;
        Ok(aad)
    }
}

struct EncryptedEvidence {
    key_ref: KeyReference,
    nonce: [u8; GCM_NONCE_BYTES],
    aad_digest: [u8; 32],
    ciphertext_digest: [u8; 32],
    ciphertext: Vec<u8>,
}

fn append_field(target: &mut Vec<u8>, field: &[u8]) -> Result<(), PlanReviewError> {
    let length = u32::try_from(field.len()).map_err(|_| PlanReviewError::LimitExceeded)?;
    target.extend_from_slice(&length.to_be_bytes());
    target.extend_from_slice(field);
    Ok(())
}

fn purge_expired(transaction: &mut Transaction<'_>) -> Result<(), PlanReviewError> {
    let row = transaction
        .query_one(
            "SELECT hwpx_agent.purge_expired_plan_review_evidence_records() AS purged",
            &[],
        )
        .map_err(db_error)?;
    let purged: i64 = value(&row, "purged")?;
    if !(0..=256).contains(&purged) {
        return Err(PlanReviewError::EvidenceUnavailable);
    }
    Ok(())
}

fn verify_database(client: &mut Client) -> Result<(), PlanReviewEvidenceConnectFailure> {
    verify_role(client).map_err(|error| PlanReviewEvidenceConnectFailure {
        stage: PlanReviewEvidenceConnectStage::Role,
        error,
    })?;
    verify_migrations(client).map_err(|error| PlanReviewEvidenceConnectFailure {
        stage: PlanReviewEvidenceConnectStage::Migrations,
        error,
    })?;
    verify_policies(client).map_err(|error| PlanReviewEvidenceConnectFailure {
        stage: PlanReviewEvidenceConnectStage::Policies,
        error,
    })?;
    verify_privileges(client).map_err(|error| PlanReviewEvidenceConnectFailure {
        stage: PlanReviewEvidenceConnectStage::Privileges,
        error,
    })
}

fn verify_role(client: &mut Client) -> Result<(), PlanReviewError> {
    let row = client
        .query_one(
            "SELECT rolsuper,rolbypassrls,rolcreaterole,rolcreatedb,rolreplication
             FROM pg_roles WHERE rolname=current_user",
            &[],
        )
        .map_err(db_error)?;
    for field in [
        "rolsuper",
        "rolbypassrls",
        "rolcreaterole",
        "rolcreatedb",
        "rolreplication",
    ] {
        if value::<bool>(&row, field)? {
            return Err(PlanReviewError::EvidenceUnavailable);
        }
    }
    Ok(())
}

fn verify_migrations(client: &mut Client) -> Result<(), PlanReviewError> {
    let rows = client
        .query(
            "SELECT version,migration_sha256::text FROM hwpx_agent.schema_versions
             ORDER BY version LIMIT 17",
            &[],
        )
        .map_err(db_error)?;
    if rows.len() != MIGRATIONS.len() {
        return Err(PlanReviewError::EvidenceUnavailable);
    }
    for (index, row) in rows.iter().enumerate() {
        if value::<i64>(row, "version")?
            != i64::try_from(index + 1).map_err(|_| PlanReviewError::EvidenceUnavailable)?
            || value::<String>(row, "migration_sha256")?
                != hex::encode(Sha256::digest(MIGRATIONS[index]))
        {
            return Err(PlanReviewError::EvidenceUnavailable);
        }
    }
    Ok(())
}

fn verify_policies(client: &mut Client) -> Result<(), PlanReviewError> {
    let rows = client
        .query(
            "SELECT class.relrowsecurity,class.relforcerowsecurity,
                    (pg_has_role(class.relowner,'USAGE') OR pg_has_role(class.relowner,'SET')) AS owner_role,
                    (SELECT count(*) FROM pg_policy policy WHERE policy.polrelid=class.oid) AS policy_count,
                    (SELECT count(*) FROM pg_policy policy WHERE policy.polrelid=class.oid
                      AND policy.polname='tenant_isolation' AND policy.polcmd='*'
                      AND policy.polpermissive AND policy.polroles=ARRAY[0::oid]
                      AND pg_get_expr(policy.polqual,policy.polrelid)='(tenant_id = hwpx_agent.current_tenant_id())'
                      AND pg_get_expr(policy.polwithcheck,policy.polrelid)='(tenant_id = hwpx_agent.current_tenant_id())') AS policy_match
             FROM pg_class AS class JOIN pg_namespace AS namespace ON namespace.oid=class.relnamespace
             WHERE namespace.nspname='hwpx_agent'
               AND class.relname IN ('compiled_plan_records','plan_review_evidence_records')",
            &[],
        )
        .map_err(db_error)?;
    if rows.len() != 2 {
        return Err(PlanReviewError::EvidenceUnavailable);
    }
    for row in rows {
        if !value::<bool>(&row, "relrowsecurity")?
            || !value::<bool>(&row, "relforcerowsecurity")?
            || value::<bool>(&row, "owner_role")?
            || value::<i64>(&row, "policy_count")? != 1
            || value::<i64>(&row, "policy_match")? != 1
        {
            return Err(PlanReviewError::EvidenceUnavailable);
        }
    }
    Ok(())
}

fn verify_privileges(client: &mut Client) -> Result<(), PlanReviewError> {
    let row = client
        .query_one(
            "SELECT has_schema_privilege('hwpx_agent','CREATE')
                 OR NOT has_table_privilege('hwpx_agent.plan_review_evidence_records','SELECT,INSERT')
                 OR has_table_privilege('hwpx_agent.plan_review_evidence_records','UPDATE,DELETE,TRUNCATE,TRIGGER,REFERENCES')
                 OR NOT has_table_privilege('hwpx_agent.compiled_plan_records','SELECT')
                 OR has_table_privilege('hwpx_agent.compiled_plan_records','INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER,REFERENCES')
                 OR NOT has_table_privilege('hwpx_agent.schema_versions','SELECT')
                 OR has_table_privilege('hwpx_agent.schema_versions','INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER')
                 OR NOT has_function_privilege('hwpx_agent.purge_expired_plan_review_evidence_records()','EXECUTE')
                 OR NOT has_function_privilege('hwpx_agent.current_tenant_id()','EXECUTE') AS unsafe",
            &[],
        )
        .map_err(db_error)?;
    if value::<bool>(&row, "unsafe")? {
        return Err(PlanReviewError::EvidenceUnavailable);
    }
    Ok(())
}

fn database_id(value: &str, prefix: &str) -> Result<Uuid, PlanReviewError> {
    let tail = value
        .strip_prefix(prefix)
        .filter(|tail| tail.len() == 32)
        .filter(|tail| {
            tail.bytes()
                .all(|byte| byte.is_ascii_digit() || matches!(byte, b'a'..=b'f'))
        })
        .ok_or(PlanReviewError::InvalidEvidence)?;
    Uuid::parse_str(tail).map_err(|_| PlanReviewError::InvalidEvidence)
}

fn digest_bytes(value: &str) -> Result<[u8; 32], PlanReviewError> {
    let mut bytes = [0_u8; 32];
    hex::decode_to_slice(value, &mut bytes).map_err(|_| PlanReviewError::EvidenceUnavailable)?;
    Ok(bytes)
}

fn positive_usize(value: i64) -> Result<usize, PlanReviewError> {
    usize::try_from(value)
        .ok()
        .filter(|value| *value > 0)
        .ok_or(PlanReviewError::EvidenceUnavailable)
}

fn nonnegative_u64(value: i64) -> Result<u64, PlanReviewError> {
    u64::try_from(value).map_err(|_| PlanReviewError::EvidenceUnavailable)
}

fn db_error(error: postgres::Error) -> PlanReviewError {
    let mapped = match error.code().map(postgres::error::SqlState::code) {
        Some("54000") => PlanReviewError::LimitExceeded,
        Some("23505" | "55000") => PlanReviewError::InvalidEvidence,
        _ => PlanReviewError::EvidenceUnavailable,
    };
    drop(error);
    mapped
}

fn value<T: FromSqlOwned>(row: &Row, name: &str) -> Result<T, PlanReviewError> {
    row.try_get(name).map_err(db_error)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn keyring_and_configuration_debug_are_redacted() {
        let keyring = DurablePlanReviewEvidenceKeyring::new(
            "kms.review-v1",
            [("kms.review-v1".to_owned(), [9; 32])],
        )
        .unwrap_or_else(|error| panic!("keyring: {error}"));
        let config = LocalPostgresPlanReviewEvidenceConfig::new(
            5432,
            "postgres".to_owned(),
            "review_reader".to_owned(),
            "private-password".to_owned(),
        )
        .unwrap_or_else(|error| panic!("config: {error}"));
        let rendered = format!("{keyring:?} {config:?}");
        assert!(!rendered.contains("private-password"));
        assert!(!rendered.contains("kms.review-v1"));
        assert!(!rendered.contains("090909"));
    }

    #[test]
    fn invalid_keyring_and_configuration_fail_closed() {
        assert_eq!(
            DurablePlanReviewEvidenceKeyring::new("bad", [("bad".to_owned(), [0; 32])]).err(),
            Some(PlanReviewError::InvalidEvidence)
        );
        assert_eq!(
            LocalPostgresPlanReviewEvidenceConfig::new(
                0,
                "postgres".to_owned(),
                "reader".to_owned(),
                "secret".to_owned(),
            )
            .err(),
            Some(PlanReviewError::InvalidEvidence)
        );
    }
}
