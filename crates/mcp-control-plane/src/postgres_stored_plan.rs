//! Encrypted `PostgreSQL` persistence for short-lived compiled plans on the current PC.
//!
//! Ciphertext and immutable binding metadata survive process/database restart. Every lookup still
//! reauthenticates, rechecks project policy and asks the authoritative source repository for the
//! current revision. A returned plan is review input, not an execution permit or renderer receipt.

use std::collections::BTreeMap;
use std::fmt;
use std::sync::{Arc, Mutex};
use std::time::Duration;

use aes_gcm::aead::{Aead as _, KeyInit as _, Payload};
use aes_gcm::{Aes256Gcm, Nonce};
use artifact_service::{KeyReference, SubjectDigest, TenantId};
use auth_middleware::{AuthContext, AuthMiddleware, AuthScope};
use domain_ir::{CompiledOperationPlan, OperationPlanLimits};
use postgres::types::FromSqlOwned;
use postgres::{Client, Config, IsolationLevel, NoTls, Row, Transaction};
use sha2::{Digest as _, Sha256};
use uuid::Uuid;
use zeroize::{Zeroize as _, Zeroizing};

use crate::policy::ProjectPolicy;
use crate::stored_plan::{
    StoredPlan, authenticate, authorize, bounded_hash, check_source, check_source_identity,
    parse_arguments, public_id,
};
use crate::{
    AuthorizedStoredPlan, CompiledPlanSubmission, PlanLookupRequest, PlanSourceRepository,
    StoredPlanError, StoredPlanLimits,
};

const AES_GCM_ALGORITHM: &str = "AES-256-GCM";
const GCM_NONCE_BYTES: usize = 12;
const GCM_TAG_BYTES: usize = 16;
const MAX_KEYS: usize = 16;

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

pub struct DurablePlanKeyring {
    active_key_ref: KeyReference,
    ciphers: BTreeMap<KeyReference, Aes256Gcm>,
}

impl DurablePlanKeyring {
    /// Builds a bounded keyring for AES-256-GCM encryption and key rotation.
    ///
    /// # Errors
    /// Rejects malformed/duplicate references, an absent active key or an excessive key count.
    pub fn new(
        active_key_ref: impl Into<String>,
        keys: impl IntoIterator<Item = (String, [u8; 32])>,
    ) -> Result<Self, StoredPlanError> {
        let active_key_ref = KeyReference::parse(active_key_ref.into())
            .map_err(|_| StoredPlanError::InvalidConfiguration)?;
        let mut ciphers = BTreeMap::new();
        for (reference, mut key_bytes) in keys {
            if ciphers.len() >= MAX_KEYS {
                key_bytes.zeroize();
                return Err(StoredPlanError::InvalidConfiguration);
            }
            let Ok(reference) = KeyReference::parse(reference) else {
                key_bytes.zeroize();
                return Err(StoredPlanError::InvalidConfiguration);
            };
            let cipher = Aes256Gcm::new_from_slice(&key_bytes)
                .map_err(|_| StoredPlanError::InvalidConfiguration);
            key_bytes.zeroize();
            let cipher = cipher?;
            if ciphers.insert(reference, cipher).is_some() {
                return Err(StoredPlanError::InvalidConfiguration);
            }
        }
        if ciphers.is_empty() || !ciphers.contains_key(&active_key_ref) {
            return Err(StoredPlanError::InvalidConfiguration);
        }
        Ok(Self {
            active_key_ref,
            ciphers,
        })
    }

    fn encrypt(
        &self,
        binding: &PlanCryptoBinding<'_>,
        plaintext: &[u8],
    ) -> Result<EncryptedPlan, StoredPlanError> {
        let cipher = self
            .ciphers
            .get(&self.active_key_ref)
            .ok_or(StoredPlanError::SourceUnavailable)?;
        let aad = binding.aad(&self.active_key_ref)?;
        let mut nonce_bytes = [0_u8; GCM_NONCE_BYTES];
        getrandom::fill(&mut nonce_bytes).map_err(|_| StoredPlanError::SourceUnavailable)?;
        let nonce = Nonce::from(nonce_bytes);
        let ciphertext = cipher
            .encrypt(
                &nonce,
                Payload {
                    msg: plaintext,
                    aad: &aad,
                },
            )
            .map_err(|_| StoredPlanError::SourceUnavailable)?;
        if ciphertext.len() != plaintext.len() + GCM_TAG_BYTES {
            return Err(StoredPlanError::SourceUnavailable);
        }
        Ok(EncryptedPlan {
            key_ref: self.active_key_ref.clone(),
            nonce: nonce_bytes,
            aad_sha256: Sha256::digest(aad).into(),
            ciphertext_sha256: Sha256::digest(&ciphertext).into(),
            ciphertext,
        })
    }

    fn decrypt(
        &self,
        binding: &PlanCryptoBinding<'_>,
        encrypted: &EncryptedPlan,
        plaintext_bytes: usize,
    ) -> Result<Zeroizing<Vec<u8>>, StoredPlanError> {
        if encrypted.ciphertext.len() != plaintext_bytes + GCM_TAG_BYTES
            || Sha256::digest(&encrypted.ciphertext).as_slice() != encrypted.ciphertext_sha256
        {
            return Err(StoredPlanError::SourceUnavailable);
        }
        let aad = binding.aad(&encrypted.key_ref)?;
        if Sha256::digest(&aad).as_slice() != encrypted.aad_sha256 {
            return Err(StoredPlanError::SourceUnavailable);
        }
        let cipher = self
            .ciphers
            .get(&encrypted.key_ref)
            .ok_or(StoredPlanError::SourceUnavailable)?;
        let plaintext = cipher
            .decrypt(
                &Nonce::from(encrypted.nonce),
                Payload {
                    msg: &encrypted.ciphertext,
                    aad: &aad,
                },
            )
            .map_err(|_| StoredPlanError::SourceUnavailable)?;
        if plaintext.len() != plaintext_bytes
            || Sha256::digest(&plaintext).as_slice() != binding.plan_sha256
        {
            return Err(StoredPlanError::SourceUnavailable);
        }
        Ok(Zeroizing::new(plaintext))
    }
}

impl fmt::Debug for DurablePlanKeyring {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("DurablePlanKeyring")
            .field("key_count", &self.ciphers.len())
            .finish_non_exhaustive()
    }
}

pub struct LocalPostgresStoredPlanConfig {
    port: u16,
    database: String,
    user: String,
    password: Zeroizing<String>,
}

impl LocalPostgresStoredPlanConfig {
    /// Configures one loopback-only `PostgreSQL` plan-store connection.
    ///
    /// # Errors
    /// Rejects unsafe/unbounded identifiers, an absent password or an unassigned port.
    pub fn new(
        port: u16,
        database: String,
        user: String,
        password: String,
    ) -> Result<Self, StoredPlanError> {
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
            return Err(StoredPlanError::InvalidConfiguration);
        }
        Ok(Self {
            port,
            database,
            user,
            password,
        })
    }
}

impl fmt::Debug for LocalPostgresStoredPlanConfig {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("LocalPostgresStoredPlanConfig")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum DurablePlanConnectStage {
    Transport,
    Role,
    Migrations,
    Policies,
    Privileges,
}

impl DurablePlanConnectStage {
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

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DurablePlanConnectFailure {
    stage: DurablePlanConnectStage,
    error: StoredPlanError,
}

impl DurablePlanConnectFailure {
    #[must_use]
    pub const fn stage(&self) -> DurablePlanConnectStage {
        self.stage
    }

    #[must_use]
    pub const fn error(&self) -> StoredPlanError {
        self.error
    }

    #[must_use]
    pub const fn into_error(self) -> StoredPlanError {
        self.error
    }
}

impl fmt::Display for DurablePlanConnectFailure {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            formatter,
            "{}:{}",
            self.stage.code(),
            error_code(self.error)
        )
    }
}

impl std::error::Error for DurablePlanConnectFailure {}

pub struct LocalPostgresStoredPlanRegistry {
    tenant: TenantId,
    client: Arc<Mutex<Client>>,
    keyring: DurablePlanKeyring,
    limits: StoredPlanLimits,
    restore_limits: OperationPlanLimits,
    observed_now: Option<u64>,
}

impl LocalPostgresStoredPlanRegistry {
    /// Connects a tenant-bound least-privilege store to the exact v13 schema.
    ///
    /// # Errors
    /// Fails closed on transport, role, migration, RLS/policy or privilege drift.
    pub fn connect(
        config: &LocalPostgresStoredPlanConfig,
        tenant: TenantId,
        keyring: DurablePlanKeyring,
        limits: StoredPlanLimits,
    ) -> Result<Self, StoredPlanError> {
        Self::connect_diagnosed(config, tenant, keyring, limits)
            .map_err(DurablePlanConnectFailure::into_error)
    }

    /// Performs the same admission while returning only a closed diagnostic stage/category.
    ///
    /// # Errors
    /// Returns a stable stage and stored-plan category without database diagnostics or credentials.
    pub fn connect_diagnosed(
        config: &LocalPostgresStoredPlanConfig,
        tenant: TenantId,
        keyring: DurablePlanKeyring,
        limits: StoredPlanLimits,
    ) -> Result<Self, DurablePlanConnectFailure> {
        let mut settings = Config::new();
        settings
            .host("127.0.0.1")
            .port(config.port)
            .dbname(&config.database)
            .user(&config.user)
            .password(config.password.as_bytes())
            .connect_timeout(Duration::from_secs(3))
            .application_name("hwpx-agent-local-durable-plan-store")
            .options("-c statement_timeout=5000 -c lock_timeout=1000 -c idle_in_transaction_session_timeout=5000 -c transaction_timeout=10000 -c search_path=pg_catalog");
        let mut client = settings
            .connect(NoTls)
            .map_err(|error| DurablePlanConnectFailure {
                stage: DurablePlanConnectStage::Transport,
                error: db_error(error),
            })?;
        verify_database(&mut client)?;
        let restore_limits = OperationPlanLimits {
            max_serialized_bytes: limits.plan_bytes(),
            ..OperationPlanLimits::default()
        };
        Ok(Self {
            tenant,
            client: Arc::new(Mutex::new(client)),
            keyring,
            limits,
            restore_limits,
            observed_now: None,
        })
    }

    /// Authenticates, source-binds, encrypts and create-once persists a compiler-issued plan.
    ///
    /// # Errors
    /// Rejects authorization/source drift, identity reuse, capacity, crypto and database failures.
    pub fn insert<P: ProjectPolicy, R: PlanSourceRepository>(
        &mut self,
        auth: &mut AuthMiddleware,
        policy: &P,
        sources: &R,
        request: CompiledPlanSubmission,
    ) -> Result<(), StoredPlanError> {
        let (authorization_header, project_id, plan, now) = request.into_parts();
        self.observe_clock(now)?;
        let context = authenticate(auth, &authorization_header, now, AuthScope::ProjectWrite)?;
        if context.tenant_id() != self.tenant
            || !public_id(&project_id, "prj_")
            || !public_id(plan.plan_id().as_str(), "plan_")
            || !public_id(plan.base_revision().as_str(), "rev_")
        {
            return Err(StoredPlanError::InvalidRequest);
        }
        let project_uuid = database_id(&project_id, "prj_")?;
        let revision_uuid = database_id(plan.base_revision().as_str(), "rev_")?;
        authorize(policy, &context, &project_id, true)?;
        check_source(sources, &context, &project_id, &plan)?;
        let (plan_sha256, plaintext_bytes) = bounded_hash(&plan, self.limits.plan_bytes())?;
        let plaintext = Zeroizing::new(
            plan.canonical_json()
                .map_err(|_| StoredPlanError::SourceUnavailable)?,
        );
        if plaintext.len() != plaintext_bytes
            || Sha256::digest(&plaintext).as_slice() != plan_sha256
        {
            return Err(StoredPlanError::SourceUnavailable);
        }
        let expires_at = now
            .checked_add(self.limits.lifetime_seconds())
            .ok_or(StoredPlanError::InvalidRequest)?
            .min(context.expires_at_unix_seconds());
        if expires_at <= now || now > i64::MAX as u64 || expires_at > i64::MAX as u64 {
            return Err(StoredPlanError::Unauthenticated);
        }
        let binding = PlanCryptoBinding {
            tenant: self.tenant,
            project_uuid,
            plan_id: plan.plan_id().as_str(),
            revision_uuid,
            graph_sha256: plan.base_graph_sha256(),
            owner: context.subject(),
            plan_sha256,
            plaintext_bytes,
            stored_at: now,
            expires_at,
        };
        let encrypted = self.keyring.encrypt(&binding, &plaintext)?;
        self.insert_record(&binding, &encrypted)
    }

    /// Loads and decrypts one exact plan after fresh authentication, policy and source checks.
    ///
    /// # Errors
    /// Rejects invalid JSON, owner/expiry/source drift, tampering, missing keys and database failure.
    pub fn lookup<P: ProjectPolicy, R: PlanSourceRepository>(
        &mut self,
        auth: &mut AuthMiddleware,
        policy: &P,
        sources: &R,
        request: PlanLookupRequest,
    ) -> Result<AuthorizedStoredPlan, StoredPlanError> {
        let (authorization_header, arguments_json, now) = request.into_parts();
        self.observe_clock(now)?;
        let context = authenticate(auth, &authorization_header, now, AuthScope::ProjectRead)?;
        drop(authorization_header);
        if context.tenant_id() != self.tenant {
            return Err(StoredPlanError::NotFound);
        }
        let arguments = parse_arguments(&arguments_json)?;
        drop(arguments_json);
        let project_uuid = database_id(&arguments.project_id, "prj_")?;
        authorize(policy, &context, &arguments.project_id, false)?;
        let row = self.read_record(project_uuid, &arguments.plan_id)?;
        self.preauthorize_record(
            &row,
            &context,
            sources,
            &arguments.project_id,
            &arguments.source_revision_id,
            now,
        )?;
        let record = self.restore_record(
            project_uuid,
            &arguments.project_id,
            &arguments.plan_id,
            &row,
        )?;
        Ok(AuthorizedStoredPlan {
            record: Arc::new(record),
        })
    }

    fn observe_clock(&mut self, now: u64) -> Result<(), StoredPlanError> {
        if self.observed_now.is_some_and(|previous| now < previous) {
            return Err(StoredPlanError::ClockRegression);
        }
        self.observed_now = Some(now);
        Ok(())
    }

    fn scoped<T>(
        &self,
        read_only: bool,
        action: impl FnOnce(&mut Transaction<'_>) -> Result<T, StoredPlanError>,
    ) -> Result<T, StoredPlanError> {
        let mut client = self
            .client
            .try_lock()
            .map_err(|_| StoredPlanError::SourceUnavailable)?;
        let builder = client
            .build_transaction()
            .isolation_level(if read_only {
                IsolationLevel::RepeatableRead
            } else {
                IsolationLevel::Serializable
            })
            .read_only(read_only);
        let mut transaction = builder.start().map_err(db_error)?;
        transaction
            .query_one(
                "SELECT set_config('hwpx_agent.tenant_id', $1, true)",
                &[&self.tenant.as_uuid().hyphenated().to_string()],
            )
            .map_err(db_error)?;
        let result = action(&mut transaction)?;
        transaction.commit().map_err(db_error)?;
        Ok(result)
    }

    fn insert_record(
        &self,
        binding: &PlanCryptoBinding<'_>,
        encrypted: &EncryptedPlan,
    ) -> Result<(), StoredPlanError> {
        let tenant_uuid = self.tenant.as_uuid();
        let graph_sha256 = hex::encode(binding.graph_sha256);
        let owner = binding.owner.hex();
        let plan_sha256 = hex::encode(binding.plan_sha256);
        let aad_sha256 = hex::encode(encrypted.aad_sha256);
        let ciphertext_sha256 = hex::encode(encrypted.ciphertext_sha256);
        let plaintext_bytes = i64::try_from(binding.plaintext_bytes)
            .map_err(|_| StoredPlanError::CapacityExceeded)?;
        let stored_at =
            i64::try_from(binding.stored_at).map_err(|_| StoredPlanError::InvalidRequest)?;
        let expires_at =
            i64::try_from(binding.expires_at).map_err(|_| StoredPlanError::InvalidRequest)?;
        let entry_limit = i64::try_from(self.limits.entries())
            .map_err(|_| StoredPlanError::InvalidConfiguration)?;
        let total_limit = i64::try_from(self.limits.total_bytes())
            .map_err(|_| StoredPlanError::InvalidConfiguration)?;
        self.scoped(false, |transaction| {
            purge_expired(transaction)?;
            transaction
                .query_one(
                    "SELECT pg_advisory_xact_lock(hashtextextended($1::uuid::text,16))",
                    &[&tenant_uuid],
                )
                .map_err(db_error)?;
            if let Some(row) = transaction
                .query_opt(
                    "SELECT created_by_subject_sha256::text FROM hwpx_agent.compiled_plan_records
                     WHERE tenant_id=$1 AND project_id=$2 AND plan_id=$3",
                    &[&tenant_uuid, &binding.project_uuid, &binding.plan_id],
                )
                .map_err(db_error)?
            {
                let existing: String = value(&row, "created_by_subject_sha256")?;
                return Err(if existing == owner {
                    StoredPlanError::Conflict
                } else {
                    StoredPlanError::NotFound
                });
            }
            let capacity = transaction
                .query_one(
                    "SELECT count(*)::bigint AS entries,COALESCE(sum(plaintext_bytes),0)::bigint AS bytes
                     FROM hwpx_agent.compiled_plan_records
                     WHERE tenant_id=$1 AND expires_at_unix_seconds>$2",
                    &[&tenant_uuid, &stored_at],
                )
                .map_err(db_error)?;
            let entries: i64 = value(&capacity, "entries")?;
            let bytes: i64 = value(&capacity, "bytes")?;
            if entries >= entry_limit
                || bytes
                    .checked_add(plaintext_bytes)
                    .is_none_or(|total| total > total_limit)
            {
                return Err(StoredPlanError::CapacityExceeded);
            }
            let inserted = transaction
                .query_opt(
                    "INSERT INTO hwpx_agent.compiled_plan_records(
                        tenant_id,project_id,plan_id,source_revision_id,source_graph_sha256,
                        created_by_subject_sha256,plan_sha256,plaintext_bytes,encryption_algorithm,
                        encryption_key_ref,nonce,aad_sha256,ciphertext_sha256,ciphertext,
                        stored_at_unix_seconds,expires_at_unix_seconds)
                     VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16)
                     ON CONFLICT (tenant_id,project_id,plan_id) DO NOTHING RETURNING plan_id",
                    &[
                        &tenant_uuid,
                        &binding.project_uuid,
                        &binding.plan_id,
                        &binding.revision_uuid,
                        &graph_sha256,
                        &owner,
                        &plan_sha256,
                        &plaintext_bytes,
                        &AES_GCM_ALGORITHM,
                        &encrypted.key_ref.as_str(),
                        &&encrypted.nonce[..],
                        &aad_sha256,
                        &ciphertext_sha256,
                        &encrypted.ciphertext,
                        &stored_at,
                        &expires_at,
                    ],
                )
                .map_err(db_error)?;
            if inserted.is_none() {
                return Err(StoredPlanError::Conflict);
            }
            Ok(())
        })
    }

    fn read_record(&self, project_uuid: Uuid, plan_id: &str) -> Result<Row, StoredPlanError> {
        let tenant_uuid = self.tenant.as_uuid();
        self.scoped(true, |transaction| {
            transaction
                .query_opt(
                    "SELECT source_revision_id,source_graph_sha256::text,
                            created_by_subject_sha256::text,plan_sha256::text,plaintext_bytes,
                            encryption_algorithm,encryption_key_ref,nonce,aad_sha256::text,
                            ciphertext_sha256::text,ciphertext,stored_at_unix_seconds,
                            expires_at_unix_seconds
                     FROM hwpx_agent.compiled_plan_records
                     WHERE tenant_id=$1 AND project_id=$2 AND plan_id=$3",
                    &[&tenant_uuid, &project_uuid, &plan_id],
                )
                .map_err(db_error)?
                .ok_or(StoredPlanError::NotFound)
        })
    }

    fn preauthorize_record<R: PlanSourceRepository>(
        &self,
        row: &Row,
        context: &AuthContext,
        sources: &R,
        project_id: &str,
        requested_revision_id: &str,
        now: u64,
    ) -> Result<(), StoredPlanError> {
        let owner = SubjectDigest::parse(&value::<String>(row, "created_by_subject_sha256")?)
            .map_err(|_| StoredPlanError::SourceUnavailable)?;
        if owner != context.subject() {
            return Err(StoredPlanError::NotFound);
        }
        let stored_at = nonnegative_u64(value(row, "stored_at_unix_seconds")?)?;
        let expires_at = nonnegative_u64(value(row, "expires_at_unix_seconds")?)?;
        if expires_at <= stored_at || expires_at - stored_at > self.limits.lifetime_seconds() {
            return Err(StoredPlanError::SourceUnavailable);
        }
        if now < stored_at || now >= expires_at {
            return Err(StoredPlanError::NotFound);
        }
        let revision_uuid: Uuid = value(row, "source_revision_id")?;
        let revision_id = format!("rev_{}", revision_uuid.simple());
        if revision_id != requested_revision_id {
            return Err(StoredPlanError::StaleSource);
        }
        let graph_sha256 = digest_bytes(&value::<String>(row, "source_graph_sha256")?)?;
        check_source_identity(sources, context, project_id, &revision_id, graph_sha256)
    }

    fn restore_record(
        &self,
        project_uuid: Uuid,
        project_id: &str,
        plan_id: &str,
        row: &Row,
    ) -> Result<StoredPlan, StoredPlanError> {
        let revision_uuid: Uuid = value(row, "source_revision_id")?;
        let graph_sha256 = digest_bytes(&value::<String>(row, "source_graph_sha256")?)?;
        let owner = SubjectDigest::parse(&value::<String>(row, "created_by_subject_sha256")?)
            .map_err(|_| StoredPlanError::SourceUnavailable)?;
        let plan_sha256 = digest_bytes(&value::<String>(row, "plan_sha256")?)?;
        let plaintext_bytes = positive_usize(value(row, "plaintext_bytes")?)?;
        if plaintext_bytes > self.limits.plan_bytes()
            || value::<String>(row, "encryption_algorithm")? != AES_GCM_ALGORITHM
        {
            return Err(StoredPlanError::SourceUnavailable);
        }
        let key_ref = KeyReference::parse(value::<String>(row, "encryption_key_ref")?)
            .map_err(|_| StoredPlanError::SourceUnavailable)?;
        let nonce = value::<Vec<u8>>(row, "nonce")?
            .try_into()
            .map_err(|_| StoredPlanError::SourceUnavailable)?;
        let encrypted = EncryptedPlan {
            key_ref,
            nonce,
            aad_sha256: digest_bytes(&value::<String>(row, "aad_sha256")?)?,
            ciphertext_sha256: digest_bytes(&value::<String>(row, "ciphertext_sha256")?)?,
            ciphertext: value(row, "ciphertext")?,
        };
        let stored_at = nonnegative_u64(value(row, "stored_at_unix_seconds")?)?;
        let expires_at = nonnegative_u64(value(row, "expires_at_unix_seconds")?)?;
        if expires_at <= stored_at || expires_at - stored_at > self.limits.lifetime_seconds() {
            return Err(StoredPlanError::SourceUnavailable);
        }
        let binding = PlanCryptoBinding {
            tenant: self.tenant,
            project_uuid,
            plan_id,
            revision_uuid,
            graph_sha256,
            owner,
            plan_sha256,
            plaintext_bytes,
            stored_at,
            expires_at,
        };
        let plaintext = self
            .keyring
            .decrypt(&binding, &encrypted, plaintext_bytes)?;
        let plan = CompiledOperationPlan::from_canonical_json(&plaintext, self.restore_limits)
            .map_err(|_| StoredPlanError::SourceUnavailable)?;
        if plan.plan_id().as_str() != plan_id
            || plan.base_revision().as_str() != format!("rev_{}", revision_uuid.simple())
            || plan.base_graph_sha256() != graph_sha256
            || plan
                .canonical_sha256()
                .map_err(|_| StoredPlanError::SourceUnavailable)?
                != plan_sha256
            || !public_id(project_id, "prj_")
        {
            return Err(StoredPlanError::SourceUnavailable);
        }
        Ok(StoredPlan {
            tenant: self.tenant,
            project_id: project_id.to_owned(),
            owner,
            plan,
            sha256: plan_sha256,
            stored_at,
            expires_at,
        })
    }
}

impl fmt::Debug for LocalPostgresStoredPlanRegistry {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("LocalPostgresStoredPlanRegistry")
            .field("limits", &self.limits)
            .field("observed_now", &self.observed_now)
            .finish_non_exhaustive()
    }
}

struct PlanCryptoBinding<'a> {
    tenant: TenantId,
    project_uuid: Uuid,
    plan_id: &'a str,
    revision_uuid: Uuid,
    graph_sha256: [u8; 32],
    owner: SubjectDigest,
    plan_sha256: [u8; 32],
    plaintext_bytes: usize,
    stored_at: u64,
    expires_at: u64,
}

impl PlanCryptoBinding<'_> {
    fn aad(&self, key_ref: &KeyReference) -> Result<Vec<u8>, StoredPlanError> {
        let plaintext_bytes =
            u64::try_from(self.plaintext_bytes).map_err(|_| StoredPlanError::CapacityExceeded)?;
        let mut aad = Vec::with_capacity(512);
        append_field(&mut aad, b"hwpx-agent.durable-compiled-plan/v1")?;
        append_field(&mut aad, self.tenant.as_uuid().as_bytes())?;
        append_field(&mut aad, self.project_uuid.as_bytes())?;
        append_field(&mut aad, self.plan_id.as_bytes())?;
        append_field(&mut aad, self.revision_uuid.as_bytes())?;
        append_field(&mut aad, &self.graph_sha256)?;
        append_field(&mut aad, self.owner.as_bytes())?;
        append_field(&mut aad, &self.plan_sha256)?;
        append_field(&mut aad, &plaintext_bytes.to_be_bytes())?;
        append_field(&mut aad, &self.stored_at.to_be_bytes())?;
        append_field(&mut aad, &self.expires_at.to_be_bytes())?;
        append_field(&mut aad, AES_GCM_ALGORITHM.as_bytes())?;
        append_field(&mut aad, key_ref.as_str().as_bytes())?;
        Ok(aad)
    }
}

struct EncryptedPlan {
    key_ref: KeyReference,
    nonce: [u8; GCM_NONCE_BYTES],
    aad_sha256: [u8; 32],
    ciphertext_sha256: [u8; 32],
    ciphertext: Vec<u8>,
}

fn append_field(target: &mut Vec<u8>, field: &[u8]) -> Result<(), StoredPlanError> {
    let length = u32::try_from(field.len()).map_err(|_| StoredPlanError::CapacityExceeded)?;
    target.extend_from_slice(&length.to_be_bytes());
    target.extend_from_slice(field);
    Ok(())
}

fn purge_expired(transaction: &mut Transaction<'_>) -> Result<(), StoredPlanError> {
    let row = transaction
        .query_one(
            "SELECT hwpx_agent.purge_expired_compiled_plan_records() AS purged",
            &[],
        )
        .map_err(db_error)?;
    let purged: i64 = value(&row, "purged")?;
    if !(0..=256).contains(&purged) {
        return Err(StoredPlanError::SourceUnavailable);
    }
    Ok(())
}

fn verify_database(client: &mut Client) -> Result<(), DurablePlanConnectFailure> {
    verify_role(client).map_err(|error| DurablePlanConnectFailure {
        stage: DurablePlanConnectStage::Role,
        error,
    })?;
    verify_migrations(client).map_err(|error| DurablePlanConnectFailure {
        stage: DurablePlanConnectStage::Migrations,
        error,
    })?;
    verify_policies(client).map_err(|error| DurablePlanConnectFailure {
        stage: DurablePlanConnectStage::Policies,
        error,
    })?;
    verify_privileges(client).map_err(|error| DurablePlanConnectFailure {
        stage: DurablePlanConnectStage::Privileges,
        error,
    })
}

fn verify_role(client: &mut Client) -> Result<(), StoredPlanError> {
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
            return Err(StoredPlanError::AccessDenied);
        }
    }
    Ok(())
}

fn verify_migrations(client: &mut Client) -> Result<(), StoredPlanError> {
    let rows = client
        .query(
            "SELECT version,migration_sha256::text FROM hwpx_agent.schema_versions
             ORDER BY version LIMIT 16",
            &[],
        )
        .map_err(db_error)?;
    if rows.len() != MIGRATIONS.len() {
        return Err(StoredPlanError::SourceUnavailable);
    }
    for (index, row) in rows.iter().enumerate() {
        if value::<i64>(row, "version")?
            != i64::try_from(index + 1).map_err(|_| StoredPlanError::SourceUnavailable)?
            || value::<String>(row, "migration_sha256")?
                != hex::encode(Sha256::digest(MIGRATIONS[index]))
        {
            return Err(StoredPlanError::SourceUnavailable);
        }
    }
    Ok(())
}

fn verify_policies(client: &mut Client) -> Result<(), StoredPlanError> {
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
               AND class.relname IN ('tenants','projects','branches','project_acl','artifacts',
                 'revisions','revision_graph_seals','revision_commit_receipts',
                 'revision_graph_bindings','compiled_plan_records')",
            &[],
        )
        .map_err(db_error)?;
    if rows.len() != 10 {
        return Err(StoredPlanError::SourceUnavailable);
    }
    for row in rows {
        if !value::<bool>(&row, "relrowsecurity")?
            || !value::<bool>(&row, "relforcerowsecurity")?
            || value::<bool>(&row, "owner_role")?
            || value::<i64>(&row, "policy_count")? != 1
            || value::<i64>(&row, "policy_match")? != 1
        {
            return Err(StoredPlanError::AccessDenied);
        }
    }
    Ok(())
}

fn verify_privileges(client: &mut Client) -> Result<(), StoredPlanError> {
    let row = client
        .query_one(
            "SELECT has_schema_privilege('hwpx_agent','CREATE')
                 OR NOT has_table_privilege('hwpx_agent.compiled_plan_records','SELECT,INSERT')
                 OR has_table_privilege('hwpx_agent.compiled_plan_records','UPDATE,DELETE,TRUNCATE,TRIGGER,REFERENCES')
                 OR NOT has_table_privilege('hwpx_agent.schema_versions','SELECT')
                 OR has_table_privilege('hwpx_agent.schema_versions','INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER')
                 OR NOT has_table_privilege('hwpx_agent.tenants','SELECT')
                 OR NOT has_table_privilege('hwpx_agent.projects','SELECT')
                 OR NOT has_table_privilege('hwpx_agent.branches','SELECT')
                 OR NOT has_table_privilege('hwpx_agent.project_acl','SELECT')
                 OR NOT has_table_privilege('hwpx_agent.artifacts','SELECT')
                 OR NOT has_table_privilege('hwpx_agent.revisions','SELECT')
                 OR NOT has_table_privilege('hwpx_agent.revision_graph_seals','SELECT')
                 OR NOT has_table_privilege('hwpx_agent.revision_commit_receipts','SELECT')
                 OR NOT has_table_privilege('hwpx_agent.revision_graph_bindings','SELECT')
                 OR has_table_privilege('hwpx_agent.tenants','INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER')
                 OR has_table_privilege('hwpx_agent.projects','INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER')
                 OR has_table_privilege('hwpx_agent.branches','INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER')
                 OR has_table_privilege('hwpx_agent.project_acl','INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER')
                 OR has_table_privilege('hwpx_agent.artifacts','INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER')
                 OR has_table_privilege('hwpx_agent.revisions','INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER')
                 OR has_table_privilege('hwpx_agent.revision_graph_seals','INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER')
                 OR has_table_privilege('hwpx_agent.revision_commit_receipts','INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER')
                 OR has_table_privilege('hwpx_agent.revision_graph_bindings','INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER')
                 OR NOT has_function_privilege('hwpx_agent.purge_expired_compiled_plan_records()','EXECUTE')
                 OR NOT has_function_privilege('hwpx_agent.current_tenant_id()','EXECUTE') AS unsafe",
            &[],
        )
        .map_err(db_error)?;
    if value::<bool>(&row, "unsafe")? {
        return Err(StoredPlanError::AccessDenied);
    }
    Ok(())
}

fn database_id(value: &str, prefix: &str) -> Result<Uuid, StoredPlanError> {
    let tail = value
        .strip_prefix(prefix)
        .filter(|tail| tail.len() == 32)
        .filter(|tail| {
            tail.bytes()
                .all(|byte| byte.is_ascii_digit() || matches!(byte, b'a'..=b'f'))
        })
        .ok_or(StoredPlanError::InvalidRequest)?;
    Uuid::parse_str(tail).map_err(|_| StoredPlanError::InvalidRequest)
}

fn digest_bytes(value: &str) -> Result<[u8; 32], StoredPlanError> {
    let mut bytes = [0_u8; 32];
    hex::decode_to_slice(value, &mut bytes).map_err(|_| StoredPlanError::SourceUnavailable)?;
    Ok(bytes)
}

fn positive_usize(value: i64) -> Result<usize, StoredPlanError> {
    usize::try_from(value)
        .ok()
        .filter(|value| *value > 0)
        .ok_or(StoredPlanError::SourceUnavailable)
}

fn nonnegative_u64(value: i64) -> Result<u64, StoredPlanError> {
    u64::try_from(value).map_err(|_| StoredPlanError::SourceUnavailable)
}

fn db_error(error: postgres::Error) -> StoredPlanError {
    let mapped = match error.code().map(postgres::error::SqlState::code) {
        Some("42501") => StoredPlanError::AccessDenied,
        Some("54000") => StoredPlanError::CapacityExceeded,
        Some("23505") => StoredPlanError::Conflict,
        _ => StoredPlanError::SourceUnavailable,
    };
    drop(error);
    mapped
}

fn value<T: FromSqlOwned>(row: &Row, name: &str) -> Result<T, StoredPlanError> {
    row.try_get(name).map_err(db_error)
}

const fn error_code(error: StoredPlanError) -> &'static str {
    match error {
        StoredPlanError::Unauthenticated => "UNAUTHENTICATED",
        StoredPlanError::InvalidRequest => "INVALID_REQUEST",
        StoredPlanError::InvalidConfiguration => "INVALID_CONFIGURATION",
        StoredPlanError::NotFound => "NOT_FOUND",
        StoredPlanError::AccessDenied => "ACCESS_DENIED",
        StoredPlanError::StaleSource => "STALE_SOURCE",
        StoredPlanError::Conflict => "CONFLICT",
        StoredPlanError::CapacityExceeded => "CAPACITY_EXCEEDED",
        StoredPlanError::SourceUnavailable => "SOURCE_UNAVAILABLE",
        StoredPlanError::ClockRegression => "CLOCK_REGRESSION",
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn binding(tenant: TenantId, owner: SubjectDigest, plan_id: &str) -> PlanCryptoBinding<'_> {
        PlanCryptoBinding {
            tenant,
            project_uuid: Uuid::from_u128(2),
            plan_id,
            revision_uuid: Uuid::from_u128(3),
            graph_sha256: [4; 32],
            owner,
            plan_sha256: Sha256::digest(b"private plan").into(),
            plaintext_bytes: 12,
            stored_at: 100,
            expires_at: 200,
        }
    }

    #[test]
    fn keyring_encrypts_randomly_and_binds_every_identity() {
        let keyring = DurablePlanKeyring::new("kms.plan-v1", [("kms.plan-v1".to_owned(), [7; 32])])
            .unwrap_or_else(|error| panic!("keyring: {error}"));
        let tenant =
            TenantId::new(Uuid::from_u128(1)).unwrap_or_else(|error| panic!("tenant: {error}"));
        let owner = SubjectDigest::from_authenticated_subject("subject")
            .unwrap_or_else(|error| panic!("subject: {error}"));
        let original_binding = binding(tenant, owner, "plan_00000001");
        let first = keyring
            .encrypt(&original_binding, b"private plan")
            .unwrap_or_else(|error| panic!("encrypt: {error}"));
        let second = keyring
            .encrypt(&original_binding, b"private plan")
            .unwrap_or_else(|error| panic!("encrypt: {error}"));
        assert_ne!(first.nonce, second.nonce);
        assert_ne!(first.ciphertext, second.ciphertext);
        let plaintext = keyring
            .decrypt(&original_binding, &first, 12)
            .unwrap_or_else(|error| panic!("decrypt: {error}"));
        assert_eq!(plaintext.as_slice(), b"private plan");
        let drifted = binding(tenant, owner, "plan_00000002");
        assert_eq!(
            keyring.decrypt(&drifted, &first, 12).err(),
            Some(StoredPlanError::SourceUnavailable)
        );
    }

    #[test]
    fn configuration_and_key_debug_are_closed() {
        let config = LocalPostgresStoredPlanConfig::new(
            5432,
            "postgres".to_owned(),
            "plan_reader".to_owned(),
            "private-password".to_owned(),
        )
        .unwrap_or_else(|error| panic!("config: {error}"));
        let keyring = DurablePlanKeyring::new("kms.plan-v1", [("kms.plan-v1".to_owned(), [9; 32])])
            .unwrap_or_else(|error| panic!("keyring: {error}"));
        let rendered = format!("{config:?} {keyring:?}");
        assert!(!rendered.contains("private-password"));
        assert!(!rendered.contains("kms.plan-v1"));
        assert!(!rendered.contains("090909"));
    }

    #[test]
    fn invalid_configuration_and_connection_failure_are_closed() {
        assert_eq!(
            LocalPostgresStoredPlanConfig::new(
                0,
                "postgres".to_owned(),
                "reader".to_owned(),
                "secret".to_owned(),
            )
            .err(),
            Some(StoredPlanError::InvalidConfiguration)
        );
        assert_eq!(
            DurablePlanKeyring::new("bad", [("bad".to_owned(), [0; 32])]).err(),
            Some(StoredPlanError::InvalidConfiguration)
        );
        let failure = DurablePlanConnectFailure {
            stage: DurablePlanConnectStage::Policies,
            error: StoredPlanError::AccessDenied,
        };
        assert_eq!(failure.to_string(), "POLICIES:ACCESS_DENIED");
    }
}
