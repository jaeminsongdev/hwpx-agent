//! SQL22 named metadata writes. No key provisioning, signing, publication or automatic retry.
use super::{
    Arc, BranchId, Client, Config, Duration, FormulaApprovalReadRequest, FormulaApprovalRecord,
    FormulaIssuerTrustRecord, IsolationLevel, LocalPostgresRevisionConfig,
    LocalPostgresRevisionRepository, Mutex, NoTls, ProjectId, RevisionError, RevisionRepository,
    RevisionRequestContext, Row, SubjectDigest, TenantId, Uuid, admit_form_policy_security,
    admit_guarded_writes, admit_policy_security, admit_read_policies, admit_schema22, db_error,
    fmt, generation, value,
};

const REGISTER_TRUST: &str = "SELECT hwpx_agent.register_formula_issuer_trust_v1(
    $1,$2,$3::character(64),$4,$5,$6,$7,$8,$9,$10,$11::character(64)) AS generation";
const REGISTER_APPROVAL: &str = "SELECT hwpx_agent.register_formula_approval_v1(
    $1,$2,$3,$4::character(64),$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15::character(64)) AS generation";
const REVOKE_TRUST: &str = "SELECT hwpx_agent.revoke_formula_issuer_trust_v1(
    $1,$2,$3::character(64),$4,$5)";
const REVOKE_APPROVAL: &str = "SELECT hwpx_agent.revoke_formula_approval_v1(
    $1,$2,$3,$4::character(64),$5,$6,$7,$8)";

/// Admission profile only. Actual project owner/editor authority is checked by named SQL APIs.
/// Each connection permits its two writes, denies both reads, three helpers and the other writes.
#[derive(Clone, Copy, Eq, PartialEq)]
pub enum RegistryManagementCapability {
    Trust,
    Approval,
}

pub struct FormulaIssuerTrustRegistration {
    record: FormulaIssuerTrustRecord,
    expected_generation: i64,
}
impl FormulaIssuerTrustRegistration {
    /// # Errors
    /// Validates a new typed metadata candidate and an unexhausted CAS generation; no key authority.
    pub fn new(
        record: FormulaIssuerTrustRecord,
        expected_generation: u64,
    ) -> Result<Self, RevisionError> {
        let expected_generation = registration_generation(expected_generation, record.generation)?;
        record
            .validate_for(
                &RevisionRequestContext::new(record.tenant, record.creator),
                record.project,
            )
            .map_err(|_| RevisionError::InvalidRequest)?;
        Ok(Self {
            record,
            expected_generation,
        })
    }
    fn validate_for(&self, context: &RevisionRequestContext) -> Result<(), RevisionError> {
        self.record.validate_for(context, self.record.project)?;
        if self.record.creator != context.subject() {
            return Err(RevisionError::NotFound);
        }
        Ok(())
    }
}

pub struct FormulaApprovalRegistration {
    source: FormulaApprovalReadRequest,
    record: FormulaApprovalRecord,
    expected_generation: i64,
}
impl FormulaApprovalRegistration {
    /// # Errors
    /// Requires exact source/policy binding and a new generation. SQL rechecks current head/root/ACL.
    pub fn new(
        source: FormulaApprovalReadRequest,
        record: FormulaApprovalRecord,
        expected_generation: u64,
    ) -> Result<Self, RevisionError> {
        let expected_generation = registration_generation(expected_generation, record.generation)?;
        record
            .validate_for(
                &RevisionRequestContext::new(record.tenant, record.creator),
                &source,
            )
            .map_err(|_| RevisionError::InvalidRequest)?;
        Ok(Self {
            source,
            record,
            expected_generation,
        })
    }
    fn validate_for(&self, context: &RevisionRequestContext) -> Result<(), RevisionError> {
        self.record.validate_for(context, &self.source)?;
        if self.record.creator != context.subject() {
            return Err(RevisionError::NotFound);
        }
        Ok(())
    }
}

pub struct FormulaIssuerTrustRevocation {
    project: ProjectId,
    version: Uuid,
    generation: i64,
}
impl FormulaIssuerTrustRevocation {
    /// # Errors
    /// Rejects nil versions and zero/overflow generations. Revocation allows the final SQL generation.
    pub fn new(
        project: ProjectId,
        version: Uuid,
        expected_generation: u64,
    ) -> Result<Self, RevisionError> {
        if version.is_nil() || !generation(expected_generation) {
            return Err(RevisionError::InvalidRequest);
        }
        Ok(Self {
            project,
            version,
            generation: sql_integer(expected_generation)?,
        })
    }
}

/// Deliberately no source-head or live-root prerequisite: administrative revocation must survive drift.
pub struct FormulaApprovalRevocation {
    project: ProjectId,
    branch: BranchId,
    document: String,
    policy_version: Uuid,
    version: Uuid,
    generation: i64,
}
impl FormulaApprovalRevocation {
    /// # Errors
    /// Rejects malformed document identity, nil versions and zero/overflow generation.
    pub fn new(
        project: ProjectId,
        branch: BranchId,
        document: String,
        policy_version: Uuid,
        version: Uuid,
        expected_generation: u64,
    ) -> Result<Self, RevisionError> {
        let bytes = document.as_bytes();
        if bytes.is_empty()
            || bytes.len() > 128
            || !bytes[0].is_ascii_alphanumeric()
            || !bytes
                .iter()
                .all(|b| b.is_ascii_alphanumeric() || b"._:-".contains(b))
            || policy_version.is_nil()
            || version.is_nil()
            || !generation(expected_generation)
        {
            return Err(RevisionError::InvalidRequest);
        }
        Ok(Self {
            project,
            branch,
            document,
            policy_version,
            version,
            generation: sql_integer(expected_generation)?,
        })
    }
}

#[derive(Clone, Copy, Eq, PartialEq)]
pub enum FormulaRegistryManagementAction {
    RegisterTrust,
    RegisterApproval,
    RevokeTrust,
    RevokeApproval,
}

/// Returned only after original scoped commit acknowledgement. Identity is a request echo;
/// NOT authenticated row readback, artifact validation, signature approval or authority to publish.
#[derive(Clone, Eq, PartialEq)]
pub struct FormulaRegistryManagementReceipt {
    action: FormulaRegistryManagementAction,
    tenant: TenantId,
    project: ProjectId,
    version: Uuid,
    generation: u64,
    actor: SubjectDigest,
}
impl FormulaRegistryManagementReceipt {
    #[must_use]
    pub const fn action(&self) -> FormulaRegistryManagementAction {
        self.action
    }
    #[must_use]
    pub const fn tenant(&self) -> TenantId {
        self.tenant
    }
    #[must_use]
    pub const fn project(&self) -> ProjectId {
        self.project
    }
    #[must_use]
    pub const fn version(&self) -> Uuid {
        self.version
    }
    #[must_use]
    pub const fn generation(&self) -> u64 {
        self.generation
    }
    #[must_use]
    pub const fn actor(&self) -> SubjectDigest {
        self.actor
    }
}

fn registration_generation(expected: u64, proposed: u64) -> Result<i64, RevisionError> {
    let expected = sql_integer(expected)?;
    let next = expected
        .checked_add(1)
        .ok_or(RevisionError::InvalidRequest)?;
    if sql_integer(proposed)? != next {
        return Err(RevisionError::InvalidRequest);
    }
    Ok(expected)
}
fn sql_integer(n: u64) -> Result<i64, RevisionError> {
    i64::try_from(n).map_err(|_| RevisionError::InvalidRequest)
}
fn acknowledged_generation(actual: i64, expected: i64) -> Result<u64, RevisionError> {
    if expected.checked_add(1) != Some(actual) || actual <= 0 {
        return Err(RevisionError::RepositoryFailure);
    }
    u64::try_from(actual).map_err(|_| RevisionError::RepositoryFailure)
}
fn generation_ack(row: &Row, expected: i64) -> Result<u64, RevisionError> {
    if row.columns().len() != 1 || row.columns()[0].type_() != &postgres::types::Type::INT8 {
        return Err(RevisionError::RepositoryFailure);
    }
    acknowledged_generation(value(row, "generation")?, expected)
}
fn void_ack(row: &Row) -> Result<(), RevisionError> {
    if row.columns().len() != 1 || row.columns()[0].type_() != &postgres::types::Type::VOID {
        return Err(RevisionError::RepositoryFailure);
    }
    Ok(())
}
fn receipt(
    context: &RevisionRequestContext,
    project: ProjectId,
    version: Uuid,
    generation: u64,
    action: FormulaRegistryManagementAction,
) -> FormulaRegistryManagementReceipt {
    FormulaRegistryManagementReceipt {
        action,
        tenant: context.tenant_id(),
        project,
        version,
        generation,
        actor: context.subject(),
    }
}

#[derive(Clone)]
pub struct LocalPostgresFormulaRegistryManagementRepository {
    inner: LocalPostgresRevisionRepository,
    capability: RegistryManagementCapability,
}
impl LocalPostgresFormulaRegistryManagementRepository {
    /// Separate exact SQL22 admission. Grants nothing, retains no credentials, exposes no revision lease.
    /// # Errors
    /// Denies changed migrations, unsafe SQL roles/rights, wrong capability profile or transport failure.
    pub fn connect(
        config: &LocalPostgresRevisionConfig,
        context: RevisionRequestContext,
        capability: RegistryManagementCapability,
    ) -> Result<Self, RevisionError> {
        let mut client = Config::new().host("127.0.0.1").port(config.port).dbname(&config.database)
            .user(&config.user).password(config.password.as_bytes()).connect_timeout(Duration::from_secs(3))
            .application_name("hwpx-agent-local-formula-registry-management-schema22")
            .options("-c statement_timeout=5000 -c lock_timeout=1000 -c idle_in_transaction_session_timeout=5000 -c transaction_timeout=10000 -c search_path=pg_catalog")
            .connect(NoTls).map_err(db_error)?;
        admit_schema22(&mut client)?;
        admit_read_policies(&mut client)?;
        admit_guarded_writes(&mut client)?;
        admit_form_policy_security(&mut client)?;
        admit_policy_security(&mut client)?;
        admit_management_security(&mut client, capability)?;
        Ok(Self {
            inner: LocalPostgresRevisionRepository {
                context,
                lease: None,
                client: Arc::new(Mutex::new(client)),
            },
            capability,
        })
    }
    fn authorize(
        &self,
        context: &RevisionRequestContext,
        capability: RegistryManagementCapability,
    ) -> Result<(), RevisionError> {
        self.inner.authorize_context(context)?;
        if self.capability != capability {
            return Err(RevisionError::InvalidRequest);
        }
        Ok(())
    }
    /// Preflight only, not a lease or replacement for named SQL write-time authority checks.
    /// Uses an already-admitted tenant-scoped ACL read; no new SQL22 helper EXECUTE or table grant.
    /// # Errors
    /// Denies foreign context/profile or absent owner/editor role. Any ambiguity denies issuance.
    pub fn check_project_role(
        &self,
        context: &RevisionRequestContext,
        project: ProjectId,
        capability: RegistryManagementCapability,
    ) -> Result<(), RevisionError> {
        self.authorize(context, capability)?;
        let roles = match capability {
            RegistryManagementCapability::Trust => vec!["owner"],
            RegistryManagementCapability::Approval => vec!["owner", "editor"],
        };
        self.inner.scoped(context.tenant_id(), IsolationLevel::ReadCommitted, |tx| {
            let row = tx.query_one("SELECT EXISTS(SELECT 1 FROM hwpx_agent.project_acl
                WHERE tenant_id=$1 AND project_id=$2 AND subject_sha256=$3::character(64)
                    AND role=ANY($4::text[])) AS eligible",
                &[&context.tenant_id().as_uuid(), &project.as_uuid(), &context.subject().hex(), &roles]).map_err(db_error)?;
            if row.columns().len() != 1 || row.columns()[0].type_() != &postgres::types::Type::BOOL {
                return Err(RevisionError::RepositoryFailure);
            }
            if !value::<bool>(&row, "eligible")? { return Err(RevisionError::NotFound); }
            Ok(())
        })
    }
    /// # Errors
    /// SQL checks owner/CAS/artifact-manage ACL. Commit uncertainty remains `CommitOutcomeUnknown`.
    pub fn register_trust(
        &self,
        context: &RevisionRequestContext,
        request: &FormulaIssuerTrustRegistration,
    ) -> Result<FormulaRegistryManagementReceipt, RevisionError> {
        self.authorize(context, RegistryManagementCapability::Trust)?;
        request.validate_for(context)?;
        self.inner
            .scoped(context.tenant_id(), IsolationLevel::ReadCommitted, |tx| {
                let r = &request.record;
                let row = tx
                    .query_one(
                        REGISTER_TRUST,
                        &[
                            &context.tenant_id().as_uuid(),
                            &r.project.as_uuid(),
                            &context.subject().hex(),
                            &r.version,
                            &request.expected_generation,
                            &r.issuer,
                            &sql_integer(r.valid_from)?,
                            &sql_integer(r.valid_until)?,
                            &sql_integer(r.max_approval_lifetime)?,
                            &r.artifact.as_uuid(),
                            &r.digest.hex(),
                        ],
                    )
                    .map_err(db_error)?;
                Ok(receipt(
                    context,
                    r.project,
                    r.version,
                    generation_ack(&row, request.expected_generation)?,
                    FormulaRegistryManagementAction::RegisterTrust,
                ))
            })
    }
    /// # Errors
    /// SQL checks editor/owner, current policy/head/root, CAS, artifact alias and manage ACL; no retry.
    pub fn register_approval(
        &self,
        context: &RevisionRequestContext,
        request: &FormulaApprovalRegistration,
    ) -> Result<FormulaRegistryManagementReceipt, RevisionError> {
        self.authorize(context, RegistryManagementCapability::Approval)?;
        request.validate_for(context)?;
        self.inner
            .scoped(context.tenant_id(), IsolationLevel::ReadCommitted, |tx| {
                let r = &request.record;
                let revision = request
                    .source
                    .head()
                    .revision_id()
                    .ok_or(RevisionError::InvalidHead)?
                    .as_uuid();
                let row = tx
                    .query_one(
                        REGISTER_APPROVAL,
                        &[
                            &context.tenant_id().as_uuid(),
                            &r.project.as_uuid(),
                            &r.branch.as_uuid(),
                            &context.subject().hex(),
                            &r.document,
                            &r.version,
                            &request.expected_generation,
                            &r.policy_version,
                            &sql_integer(r.policy_generation)?,
                            &revision,
                            &sql_integer(request.source.head().generation())?,
                            &r.trust_version,
                            &sql_integer(r.trust_generation)?,
                            &r.artifact.as_uuid(),
                            &r.digest.hex(),
                        ],
                    )
                    .map_err(db_error)?;
                Ok(receipt(
                    context,
                    r.project,
                    r.version,
                    generation_ack(&row, request.expected_generation)?,
                    FormulaRegistryManagementAction::RegisterApproval,
                ))
            })
    }
    /// # Errors
    /// Owner/latest-CAS/duplicate denial and ambiguous commit are not retried. Does not delete artifacts.
    pub fn revoke_trust(
        &self,
        context: &RevisionRequestContext,
        request: &FormulaIssuerTrustRevocation,
    ) -> Result<FormulaRegistryManagementReceipt, RevisionError> {
        self.authorize(context, RegistryManagementCapability::Trust)?;
        self.inner
            .scoped(context.tenant_id(), IsolationLevel::ReadCommitted, |tx| {
                let row = tx
                    .query_one(
                        REVOKE_TRUST,
                        &[
                            &context.tenant_id().as_uuid(),
                            &request.project.as_uuid(),
                            &context.subject().hex(),
                            &request.version,
                            &request.generation,
                        ],
                    )
                    .map_err(db_error)?;
                void_ack(&row)?;
                Ok(receipt(
                    context,
                    request.project,
                    request.version,
                    u64::try_from(request.generation).map_err(|_| RevisionError::InvalidRequest)?,
                    FormulaRegistryManagementAction::RevokeTrust,
                ))
            })
    }
    /// # Errors
    /// Latest approval CAS is independent of current head/live root. Duplicate/ambiguous writes deny.
    pub fn revoke_approval(
        &self,
        context: &RevisionRequestContext,
        request: &FormulaApprovalRevocation,
    ) -> Result<FormulaRegistryManagementReceipt, RevisionError> {
        self.authorize(context, RegistryManagementCapability::Approval)?;
        self.inner
            .scoped(context.tenant_id(), IsolationLevel::ReadCommitted, |tx| {
                let row = tx
                    .query_one(
                        REVOKE_APPROVAL,
                        &[
                            &context.tenant_id().as_uuid(),
                            &request.project.as_uuid(),
                            &request.branch.as_uuid(),
                            &context.subject().hex(),
                            &request.document,
                            &request.policy_version,
                            &request.version,
                            &request.generation,
                        ],
                    )
                    .map_err(db_error)?;
                void_ack(&row)?;
                Ok(receipt(
                    context,
                    request.project,
                    request.version,
                    u64::try_from(request.generation).map_err(|_| RevisionError::InvalidRequest)?,
                    FormulaRegistryManagementAction::RevokeApproval,
                ))
            })
    }
}

macro_rules! redacted_debug {
    ($($name:ident),+ $(,)?) => { $(
        impl fmt::Debug for $name {
            fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
                f.write_str(concat!(stringify!($name), "(<redacted>)"))
            }
        }
    )+ };
}
redacted_debug!(
    RegistryManagementCapability,
    FormulaIssuerTrustRegistration,
    FormulaApprovalRegistration,
    FormulaIssuerTrustRevocation,
    FormulaApprovalRevocation,
    FormulaRegistryManagementAction,
    FormulaRegistryManagementReceipt,
    LocalPostgresFormulaRegistryManagementRepository
);

fn admit_management_security(
    client: &mut Client,
    capability: RegistryManagementCapability,
) -> Result<(), RevisionError> {
    for table in [
        "formula_issuer_trust_versions",
        "formula_issuer_trust_revocations",
        "formula_approval_versions",
        "formula_approval_revocations",
    ] {
        let row = client.query_one("SELECT c.relrowsecurity,c.relforcerowsecurity,
            (pg_has_role(c.relowner,'USAGE') OR pg_has_role(c.relowner,'SET')) AS owner_role,
            has_table_privilege(current_user,c.oid,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER') AS direct,
            (SELECT count(*)=1 AND bool_and(p.policyname='tenant_isolation' AND p.cmd='ALL'
                AND p.permissive='PERMISSIVE' AND p.qual='(tenant_id = hwpx_agent.current_tenant_id())'
                AND p.with_check='(tenant_id = hwpx_agent.current_tenant_id())')
             FROM pg_policies p WHERE p.schemaname='hwpx_agent' AND p.tablename=$1) AS policy,
            EXISTS(SELECT 1 FROM pg_trigger t WHERE t.tgrelid=c.oid AND t.tgname=$3
                AND t.tgenabled='O' AND NOT t.tgisinternal) AS immutable
            FROM pg_class c WHERE c.oid=$2::text::regclass",
            &[&table,&format!("hwpx_agent.{table}"),&format!("{table}_immutable")]).map_err(db_error)?;
        if !value::<bool>(&row, "relrowsecurity")?
            || !value::<bool>(&row, "relforcerowsecurity")?
            || value::<bool>(&row, "owner_role")?
            || value::<bool>(&row, "direct")?
            || !value::<bool>(&row, "policy")?
            || !value::<bool>(&row, "immutable")?
        {
            return Err(RevisionError::InvalidRequest);
        }
    }
    for (signature, expected) in [
        (
            "hwpx_agent.read_formula_issuer_trust_v1(uuid,uuid,character)",
            false,
        ),
        (
            "hwpx_agent.read_formula_approval_v1(uuid,uuid,uuid,character,text,uuid,bigint,uuid,bigint)",
            false,
        ),
        (
            "hwpx_agent.lock_formula_issuer_scope_v1(uuid,uuid,character,boolean)",
            false,
        ),
        (
            "hwpx_agent.require_formula_issuer_owner_v1(uuid,uuid,character)",
            false,
        ),
        (
            "hwpx_agent.require_formula_issuer_artifact_v1(uuid,character,uuid,character,boolean,boolean)",
            false,
        ),
        (
            "hwpx_agent.register_formula_issuer_trust_v1(uuid,uuid,character,uuid,bigint,text,bigint,bigint,bigint,uuid,character)",
            capability == RegistryManagementCapability::Trust,
        ),
        (
            "hwpx_agent.revoke_formula_issuer_trust_v1(uuid,uuid,character,uuid,bigint)",
            capability == RegistryManagementCapability::Trust,
        ),
        (
            "hwpx_agent.register_formula_approval_v1(uuid,uuid,uuid,character,text,uuid,bigint,uuid,bigint,uuid,bigint,uuid,bigint,uuid,character)",
            capability == RegistryManagementCapability::Approval,
        ),
        (
            "hwpx_agent.revoke_formula_approval_v1(uuid,uuid,uuid,character,text,uuid,uuid,bigint)",
            capability == RegistryManagementCapability::Approval,
        ),
    ] {
        let row = client.query_one("SELECT has_function_privilege(current_user,p.oid,'EXECUTE') AS allowed,p.prosecdef,
            p.proconfig=ARRAY['search_path=pg_catalog, hwpx_agent'] AS bounded_path,
            (pg_has_role(p.proowner,'USAGE') OR pg_has_role(p.proowner,'SET')) AS owner_role,
            NOT EXISTS(SELECT 1 FROM aclexplode(COALESCE(p.proacl,acldefault('f',p.proowner)))
                WHERE grantee=0 AND privilege_type='EXECUTE') AS no_public
            FROM pg_proc p WHERE p.oid=$1::text::regprocedure", &[&signature]).map_err(db_error)?;
        if value::<bool>(&row, "allowed")? != expected
            || !value::<bool>(&row, "prosecdef")?
            || !value::<bool>(&row, "bounded_path")?
            || value::<bool>(&row, "owner_role")?
            || !value::<bool>(&row, "no_public")?
        {
            return Err(RevisionError::InvalidRequest);
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::super::{ArtifactId, ContentDigest, SourceFormulaPolicyReadRequest};
    use super::*;
    use crate::{RevisionHead, RevisionId};

    fn context() -> Result<RevisionRequestContext, Box<dyn std::error::Error>> {
        Ok(RevisionRequestContext::new(
            TenantId::new(Uuid::new_v4())?,
            SubjectDigest::from_authenticated_subject("fixture-owner")?,
        ))
    }
    fn root(ctx: &RevisionRequestContext) -> FormulaIssuerTrustRecord {
        FormulaIssuerTrustRecord {
            tenant: ctx.tenant_id(),
            project: ProjectId::generate(),
            version: Uuid::new_v4(),
            generation: 1,
            issuer: "fixture-issuer".into(),
            valid_from: 0,
            valid_until: 100,
            max_approval_lifetime: 60,
            artifact: ArtifactId::generate(),
            digest: ContentDigest::of(b"fixture-root"),
            creator: ctx.subject(),
        }
    }
    fn approval(
        ctx: &RevisionRequestContext,
    ) -> Result<(FormulaApprovalReadRequest, FormulaApprovalRecord), RevisionError> {
        let source = FormulaApprovalReadRequest::new(
            SourceFormulaPolicyReadRequest::new(
                ProjectId::generate(),
                BranchId::generate(),
                "fixture-document".into(),
                RevisionHead::new(Some(RevisionId::generate()), 1)?,
            )?,
            Uuid::new_v4(),
            1,
        )?;
        let record = FormulaApprovalRecord {
            tenant: ctx.tenant_id(),
            project: source.project(),
            branch: source.branch(),
            document: source.document().into(),
            version: Uuid::new_v4(),
            generation: 1,
            policy_version: source.policy_version(),
            policy_generation: source.policy_generation(),
            trust_version: Uuid::new_v4(),
            trust_generation: 1,
            artifact: ArtifactId::generate(),
            digest: ContentDigest::of(b"fixture-approval"),
            creator: ctx.subject(),
        };
        Ok((source, record))
    }
    #[test]
    fn cas_zero_final_generation_and_overflow_are_exact() -> Result<(), RevisionError> {
        assert_eq!(registration_generation(0, 1)?, 0);
        assert_eq!(
            registration_generation(i64::MAX as u64 - 1, i64::MAX as u64)?,
            i64::MAX - 1
        );
        for (old, new) in [
            (0, 0),
            (0, 2),
            (1, 1),
            (i64::MAX as u64, i64::MAX as u64),
            (u64::MAX, 1),
        ] {
            assert!(registration_generation(old, new).is_err());
        }
        Ok(())
    }
    #[test]
    fn root_registration_validates_metadata_not_authority() -> Result<(), Box<dyn std::error::Error>>
    {
        let ctx = context()?;
        FormulaIssuerTrustRegistration::new(root(&ctx), 0)?.validate_for(&ctx)?;
        let mut r = root(&ctx);
        r.version = Uuid::nil();
        assert!(FormulaIssuerTrustRegistration::new(r, 0).is_err());
        for (issuer, from, until, lifetime) in [
            ("bad issuer", 0, 100, 60),
            ("ok", 100, 100, 60),
            ("ok", 0, u64::MAX, 60),
            ("ok", 0, 100, 0),
            ("ok", 0, 100, 86401),
        ] {
            let mut r = root(&ctx);
            r.issuer = issuer.into();
            r.valid_from = from;
            r.valid_until = until;
            r.max_approval_lifetime = lifetime;
            assert!(FormulaIssuerTrustRegistration::new(r, 0).is_err());
        }
        Ok(())
    }
    #[test]
    fn trust_registration_denies_other_tenant_and_creator() -> Result<(), Box<dyn std::error::Error>>
    {
        let ctx = context()?;
        let request = FormulaIssuerTrustRegistration::new(root(&ctx), 0)?;
        assert!(request.validate_for(&context()?).is_err());
        let other = RevisionRequestContext::new(
            ctx.tenant_id(),
            SubjectDigest::from_authenticated_subject("other-owner")?,
        );
        assert!(request.validate_for(&other).is_err());
        Ok(())
    }
    #[test]
    fn approval_registration_binds_current_policy_and_fixed_creator()
    -> Result<(), Box<dyn std::error::Error>> {
        let ctx = context()?;
        let (s, r) = approval(&ctx)?;
        let req = FormulaApprovalRegistration::new(s, r, 0)?;
        req.validate_for(&ctx)?;
        assert!(req.validate_for(&context()?).is_err());
        for n in 0..5 {
            let (s, mut r) = approval(&ctx)?;
            match n {
                0 => r.policy_version = Uuid::new_v4(),
                1 => r.policy_generation = 2,
                2 => r.document = "other-document".into(),
                3 => r.trust_version = Uuid::nil(),
                _ => r.trust_generation = u64::MAX,
            }
            assert!(FormulaApprovalRegistration::new(s, r, 0).is_err());
        }
        let (s, mut r) = approval(&ctx)?;
        r.creator = SubjectDigest::from_authenticated_subject("other-owner")?;
        assert!(
            FormulaApprovalRegistration::new(s, r, 0)?
                .validate_for(&ctx)
                .is_err()
        );
        Ok(())
    }
    #[test]
    fn revocation_rejects_nil_zero_overflow_and_invalid_identity() {
        let project = ProjectId::generate();
        let branch = BranchId::generate();
        for (version, generation) in [
            (Uuid::nil(), 1),
            (Uuid::new_v4(), 0),
            (Uuid::new_v4(), u64::MAX),
        ] {
            assert!(FormulaIssuerTrustRevocation::new(project, version, generation).is_err());
            assert!(
                FormulaApprovalRevocation::new(
                    project,
                    branch,
                    "valid-doc".into(),
                    Uuid::new_v4(),
                    version,
                    generation
                )
                .is_err()
            );
        }
        for document in [
            String::new(),
            ".bad".into(),
            "has space".into(),
            "../path".into(),
            "한글".into(),
            "a".repeat(129),
        ] {
            assert!(
                FormulaApprovalRevocation::new(
                    project,
                    branch,
                    document,
                    Uuid::new_v4(),
                    Uuid::new_v4(),
                    1
                )
                .is_err()
            );
        }
        assert!(
            FormulaApprovalRevocation::new(
                project,
                branch,
                "valid-doc".into(),
                Uuid::nil(),
                Uuid::new_v4(),
                1
            )
            .is_err()
        );
    }
    #[test]
    fn revocation_survives_head_root_absence_and_exhausted_generation() -> Result<(), RevisionError>
    {
        let project = ProjectId::generate();
        let r = FormulaIssuerTrustRevocation::new(project, Uuid::new_v4(), i64::MAX as u64)?;
        assert_eq!(r.generation, i64::MAX);
        let a = FormulaApprovalRevocation::new(
            project,
            BranchId::generate(),
            "a".repeat(128),
            Uuid::new_v4(),
            Uuid::new_v4(),
            i64::MAX as u64,
        )?;
        assert_eq!(a.generation, i64::MAX);
        Ok(())
    }
    #[test]
    fn scalar_acknowledgement_rejects_wrong_generation() -> Result<(), RevisionError> {
        assert_eq!(acknowledged_generation(1, 0)?, 1);
        assert_eq!(
            acknowledged_generation(i64::MAX, i64::MAX - 1)?,
            i64::MAX as u64
        );
        for (actual, expected) in [(0, 0), (-1, 0), (2, 0), (1, 1), (i64::MAX, i64::MAX)] {
            assert!(acknowledged_generation(actual, expected).is_err());
        }
        Ok(())
    }
    #[test]
    fn requests_profiles_and_commit_receipt_are_redacted() -> Result<(), Box<dyn std::error::Error>>
    {
        let ctx = context()?;
        let r = root(&ctx);
        let ack = receipt(
            &ctx,
            r.project,
            r.version,
            1,
            FormulaRegistryManagementAction::RegisterTrust,
        );
        assert_eq!(ack.actor(), ctx.subject());
        assert_eq!(ack.tenant(), ctx.tenant_id());
        assert_eq!(ack.project(), r.project);
        assert_eq!(ack.version(), r.version);
        assert_eq!(ack.generation(), 1);
        assert_eq!(ack.action(), FormulaRegistryManagementAction::RegisterTrust);
        assert_eq!(
            format!("{ack:?}"),
            "FormulaRegistryManagementReceipt(<redacted>)"
        );
        assert_eq!(
            format!("{:?}", FormulaIssuerTrustRegistration::new(r, 0)?),
            "FormulaIssuerTrustRegistration(<redacted>)"
        );
        let (s, r) = approval(&ctx)?;
        assert_eq!(
            format!("{:?}", FormulaApprovalRegistration::new(s, r, 0)?),
            "FormulaApprovalRegistration(<redacted>)"
        );
        assert_eq!(
            format!("{:?}", RegistryManagementCapability::Trust),
            "RegistryManagementCapability(<redacted>)"
        );
        assert_eq!(
            format!(
                "{:?}",
                FormulaIssuerTrustRevocation::new(ProjectId::generate(), Uuid::new_v4(), 1)?
            ),
            "FormulaIssuerTrustRevocation(<redacted>)"
        );
        assert_eq!(
            format!(
                "{:?}",
                FormulaApprovalRevocation::new(
                    ProjectId::generate(),
                    BranchId::generate(),
                    "private-document".into(),
                    Uuid::new_v4(),
                    Uuid::new_v4(),
                    1
                )?
            ),
            "FormulaApprovalRevocation(<redacted>)"
        );
        Ok(())
    }
}
