//! Credential-bound SQL22 adapter probe. Synthetic metadata, NOT crypto/native/product evidence.
use artifact_service::{ArtifactId, ContentDigest, SubjectDigest, TenantId};
use revision_service::{
    BranchId, ProjectId, RevisionError, RevisionHead, RevisionId, RevisionRequestContext,
    postgres::{
        LocalPostgresRevisionConfig,
        source_formula_policy::{
            SourceFormulaPolicyReadRequest,
            issuer_registry::{
                FormulaApprovalReadRequest, FormulaApprovalRecord, FormulaIssuerRegistryRepository,
                FormulaIssuerTrustRecord, LocalPostgresFormulaIssuerRegistryRepository,
                management::{
                    FormulaApprovalRegistration, FormulaApprovalRevocation,
                    FormulaIssuerTrustRegistration, FormulaIssuerTrustRevocation,
                    FormulaRegistryManagementAction, FormulaRegistryManagementReceipt,
                    LocalPostgresFormulaRegistryManagementRepository, RegistryManagementCapability,
                },
            },
        },
    },
};
use uuid::Uuid;

fn uuid(text: &str) -> Result<Uuid, RevisionError> {
    Uuid::parse_str(text).map_err(|_| RevisionError::InvalidIdentifier)
}
fn project() -> Result<ProjectId, RevisionError> {
    ProjectId::parse("prj_62000000000000000000000000000001")
}
fn branch() -> Result<BranchId, RevisionError> {
    BranchId::parse("brn_63000000000000000000000000000001")
}
fn context(subject: char) -> Result<RevisionRequestContext, RevisionError> {
    Ok(RevisionRequestContext::new(
        TenantId::new(uuid("60000000-0000-0000-0000-000000000001")?)
            .map_err(|_| RevisionError::InvalidIdentifier)?,
        SubjectDigest::parse(&subject.to_string().repeat(64))
            .map_err(|_| RevisionError::InvalidIdentifier)?,
    ))
}
fn digest(value: char) -> Result<ContentDigest, RevisionError> {
    ContentDigest::parse(&value.to_string().repeat(64))
        .map_err(|_| RevisionError::InvalidIdentifier)
}
fn artifact(number: u8) -> Result<ArtifactId, RevisionError> {
    ArtifactId::parse(&format!("art_71000000000000000000{number:012}"))
        .map_err(|_| RevisionError::InvalidIdentifier)
}
fn request() -> Result<FormulaApprovalReadRequest, RevisionError> {
    FormulaApprovalReadRequest::new(
        SourceFormulaPolicyReadRequest::new(
            project()?,
            branch()?,
            "p140-formula".into(),
            RevisionHead::new(
                Some(RevisionId::parse("rev_65000000000000000000000000000001")?),
                1,
            )?,
        )?,
        uuid("72000000-0000-0000-0000-000000000001")?,
        1,
    )
}
fn config(user: &str) -> Result<LocalPostgresRevisionConfig, RevisionError> {
    let database = std::env::var("P141_DB_DATABASE").map_err(|_| RevisionError::InvalidRequest)?;
    if !matches!(
        database.as_str(),
        "postgres" | "p141_changed_schema" | "p141_correct_schema"
    ) {
        return Err(RevisionError::InvalidRequest);
    }
    LocalPostgresRevisionConfig::new(
        std::env::var("P141_DB_PORT")
            .map_err(|_| RevisionError::InvalidRequest)?
            .parse()
            .map_err(|_| RevisionError::InvalidRequest)?,
        database,
        user.into(),
        std::env::var("P141_DB_PASSWORD").map_err(|_| RevisionError::InvalidRequest)?,
    )
}

#[derive(Default)]
struct Probe {
    checks: Vec<&'static str>,
    stage: &'static str,
}
impl Probe {
    fn check(&mut self, name: &'static str, ok: bool) -> Result<(), RevisionError> {
        self.stage = name;
        if !ok {
            return Err(RevisionError::InvalidRequest);
        }
        self.checks.push(name);
        Ok(())
    }
    fn step<T>(
        &mut self,
        name: &'static str,
        result: Result<T, RevisionError>,
    ) -> Result<T, RevisionError> {
        self.stage = name;
        let value = result?;
        self.checks.push(name);
        Ok(value)
    }
    fn acknowledgement(
        &mut self,
        name: &'static str,
        receipt: &FormulaRegistryManagementReceipt,
        action: FormulaRegistryManagementAction,
        version: Uuid,
        ctx: &RevisionRequestContext,
    ) -> Result<(), RevisionError> {
        self.check(
            name,
            receipt.action() == action
                && receipt.version() == version
                && receipt.generation() == 3
                && receipt.project() == project()?
                && receipt.tenant() == ctx.tenant_id()
                && receipt.actor() == ctx.subject(),
        )
    }
}

struct Connections {
    reader: LocalPostgresFormulaIssuerRegistryRepository,
    root: LocalPostgresFormulaRegistryManagementRepository,
    approval: LocalPostgresFormulaRegistryManagementRepository,
}
fn connect(probe: &mut Probe) -> Result<Connections, RevisionError> {
    let ctx = context('a')?;
    let reader = probe.step(
        "reader_exact_admission",
        LocalPostgresFormulaIssuerRegistryRepository::connect(
            &config("p141_reader")?,
            ctx.clone(),
            None,
        ),
    )?;
    let root = probe.step(
        "root_exact_admission",
        LocalPostgresFormulaRegistryManagementRepository::connect(
            &config("p141_root")?,
            ctx.clone(),
            RegistryManagementCapability::Trust,
        ),
    )?;
    let approval = probe.step(
        "approval_exact_admission",
        LocalPostgresFormulaRegistryManagementRepository::connect(
            &config("p141_approval")?,
            context('e')?,
            RegistryManagementCapability::Approval,
        ),
    )?;
    for (name, user) in [
        ("root_credentials_cannot_admit_reader", "p141_root"),
        ("approval_credentials_cannot_admit_reader", "p141_approval"),
        ("unsafe_direct_table_grant_denied", "p141_bad_direct"),
        ("unsafe_helper_execute_grant_denied", "p141_bad_helper"),
    ] {
        probe.check(
            name,
            matches!(
                LocalPostgresFormulaIssuerRegistryRepository::connect(
                    &config(user)?,
                    ctx.clone(),
                    None
                ),
                Err(RevisionError::InvalidRequest)
            ),
        )?;
    }
    probe.check(
        "reader_credentials_cannot_admit_writer",
        matches!(
            LocalPostgresFormulaRegistryManagementRepository::connect(
                &config("p141_reader")?,
                ctx.clone(),
                RegistryManagementCapability::Trust
            ),
            Err(RevisionError::InvalidRequest)
        ),
    )?;
    probe.check(
        "root_credentials_cannot_admit_approval_writer",
        matches!(
            LocalPostgresFormulaRegistryManagementRepository::connect(
                &config("p141_root")?,
                ctx,
                RegistryManagementCapability::Approval
            ),
            Err(RevisionError::InvalidRequest)
        ),
    )?;
    Ok(Connections {
        reader,
        root,
        approval,
    })
}
fn read_checks(probe: &mut Probe, db: &Connections) -> Result<(), RevisionError> {
    let ctx = context('a')?;
    let root = probe.step("typed_root_read", db.reader.read_trust(&ctx, project()?))?;
    probe.check(
        "typed_root_exact_identity",
        root.tenant == ctx.tenant_id()
            && root.project == project()?
            && root.version == uuid("73000000-0000-0000-0000-000000000002")?
            && root.generation == 2
            && root.issuer == "p140-test"
            && root.valid_from == 0
            && root.valid_until > 0
            && root.max_approval_lifetime == 600
            && root.artifact == artifact(4)?
            && root.digest == digest('d')?
            && root.creator == ctx.subject(),
    )?;
    let approval = probe.step(
        "typed_approval_read",
        db.reader.read_approval(&ctx, &request()?),
    )?;
    probe.check(
        "typed_approval_exact_identity",
        approval.tenant == ctx.tenant_id()
            && approval.project == project()?
            && approval.branch == branch()?
            && approval.document == "p140-formula"
            && approval.version == uuid("74000000-0000-0000-0000-000000000002")?
            && approval.generation == 2
            && approval.policy_version == uuid("72000000-0000-0000-0000-000000000001")?
            && approval.policy_generation == 1
            && approval.trust_version == root.version
            && approval.trust_generation == 2
            && approval.artifact == artifact(5)?
            && approval.digest == digest('e')?
            && approval.creator == ctx.subject(),
    )?;
    Ok(())
}
fn context_checks(probe: &mut Probe, db: &Connections) -> Result<(), RevisionError> {
    let ctx = context('a')?;
    probe.check(
        "fixed_subject_context_denied",
        matches!(
            db.reader.read_trust(&context('b')?, project()?),
            Err(RevisionError::NotFound)
        ),
    )?;
    let foreign = RevisionRequestContext::new(
        TenantId::new(uuid("60000000-0000-0000-0000-000000000002")?)
            .map_err(|_| RevisionError::InvalidIdentifier)?,
        ctx.subject(),
    );
    probe.check(
        "fixed_tenant_context_denied",
        matches!(
            db.reader.read_trust(&foreign, project()?),
            Err(RevisionError::NotFound)
        ),
    )?;
    let nonmember = probe.step(
        "nonmember_transport_admitted",
        LocalPostgresFormulaIssuerRegistryRepository::connect(
            &config("p141_reader")?,
            context('c')?,
            None,
        ),
    )?;
    probe.check(
        "nonmember_named_read_denied",
        matches!(
            nonmember.read_trust(&context('c')?, project()?),
            Err(RevisionError::InvalidRequest)
        ),
    )?;
    probe.step(
        "owner_root_preflight",
        db.root
            .check_project_role(&ctx, project()?, RegistryManagementCapability::Trust),
    )?;
    probe.step(
        "editor_approval_preflight",
        db.approval.check_project_role(
            &context('e')?,
            project()?,
            RegistryManagementCapability::Approval,
        ),
    )?;
    probe.check(
        "management_foreign_context_denied",
        matches!(
            db.root.check_project_role(
                &context('e')?,
                project()?,
                RegistryManagementCapability::Trust
            ),
            Err(RevisionError::NotFound)
        ),
    )?;
    probe.check(
        "management_wrong_capability_denied",
        matches!(
            db.root
                .check_project_role(&ctx, project()?, RegistryManagementCapability::Approval),
            Err(RevisionError::InvalidRequest)
        ),
    )?;
    Ok(())
}
fn rotate_root(
    probe: &mut Probe,
    db: &Connections,
) -> Result<FormulaIssuerTrustRecord, RevisionError> {
    let ctx = context('a')?;
    let old = db.reader.read_trust(&ctx, project()?)?;
    let root = FormulaIssuerTrustRecord {
        version: uuid("73000000-0000-0000-0000-000000000003")?,
        generation: 3,
        artifact: artifact(6)?,
        digest: digest('f')?,
        ..old
    };
    let wrong = FormulaIssuerTrustRegistration::new(
        FormulaIssuerTrustRecord {
            digest: digest('e')?,
            ..root.clone()
        },
        2,
    )?;
    probe.check(
        "root_wrong_artifact_digest_denied",
        matches!(
            db.root.register_trust(&ctx, &wrong),
            Err(RevisionError::InvalidRequest)
        ),
    )?;
    let registration = FormulaIssuerTrustRegistration::new(root.clone(), 2)?;
    let ack = probe.step(
        "root_generation_three_commit",
        db.root.register_trust(&ctx, &registration),
    )?;
    probe.acknowledgement(
        "root_commit_ack_exact",
        &ack,
        FormulaRegistryManagementAction::RegisterTrust,
        root.version,
        &ctx,
    )?;
    probe.check(
        "root_same_cas_no_retry",
        matches!(
            db.root.register_trust(&ctx, &registration),
            Err(RevisionError::RepositoryFailure)
        ),
    )?;
    let actual = probe.step(
        "root_fresh_named_readback",
        db.reader.read_trust(&ctx, project()?),
    )?;
    probe.check("root_readback_all_fields_exact", actual == root)?;
    probe.check(
        "root_rotation_denies_old_approval",
        matches!(
            db.reader.read_approval(&ctx, &request()?),
            Err(RevisionError::InvalidRequest)
        ),
    )?;
    Ok(root)
}
fn rotate_approval(
    probe: &mut Probe,
    db: &Connections,
    root: &FormulaIssuerTrustRecord,
) -> Result<FormulaApprovalRecord, RevisionError> {
    let ctx = context('e')?;
    let approval = FormulaApprovalRecord {
        tenant: ctx.tenant_id(),
        project: project()?,
        branch: branch()?,
        document: "p140-formula".into(),
        version: uuid("74000000-0000-0000-0000-000000000003")?,
        generation: 3,
        policy_version: uuid("72000000-0000-0000-0000-000000000001")?,
        policy_generation: 1,
        trust_version: root.version,
        trust_generation: 3,
        artifact: artifact(7)?,
        digest: digest('7')?,
        creator: ctx.subject(),
    };
    let stale = FormulaApprovalRegistration::new(
        request()?,
        FormulaApprovalRecord {
            trust_version: uuid("73000000-0000-0000-0000-000000000002")?,
            trust_generation: 2,
            ..approval.clone()
        },
        2,
    )?;
    probe.check(
        "approval_stale_root_denied",
        matches!(
            db.approval.register_approval(&ctx, &stale),
            Err(RevisionError::RepositoryFailure)
        ),
    )?;
    let registration = FormulaApprovalRegistration::new(request()?, approval.clone(), 2)?;
    let ack = probe.step(
        "editor_approval_generation_three_commit",
        db.approval.register_approval(&ctx, &registration),
    )?;
    probe.acknowledgement(
        "approval_commit_ack_exact",
        &ack,
        FormulaRegistryManagementAction::RegisterApproval,
        approval.version,
        &ctx,
    )?;
    probe.check(
        "approval_same_cas_no_retry",
        matches!(
            db.approval.register_approval(&ctx, &registration),
            Err(RevisionError::RepositoryFailure)
        ),
    )?;
    let actual = probe.step(
        "approval_fresh_named_readback",
        db.reader.read_approval(&context('a')?, &request()?),
    )?;
    probe.check("approval_readback_all_fields_exact", actual == approval)?;
    Ok(approval)
}
fn revoke(
    probe: &mut Probe,
    db: &Connections,
    root: &FormulaIssuerTrustRecord,
    approval: &FormulaApprovalRecord,
) -> Result<(), RevisionError> {
    let ctx = context('a')?;
    let root_request = FormulaIssuerTrustRevocation::new(project()?, root.version, 3)?;
    let ack = probe.step(
        "root_revoke_commit",
        db.root.revoke_trust(&ctx, &root_request),
    )?;
    probe.acknowledgement(
        "root_revoke_ack_exact",
        &ack,
        FormulaRegistryManagementAction::RevokeTrust,
        root.version,
        &ctx,
    )?;
    probe.check(
        "revoked_root_named_read_denied",
        matches!(
            db.reader.read_trust(&ctx, project()?),
            Err(RevisionError::InvalidRequest)
        ),
    )?;
    probe.check(
        "revoked_root_approval_read_denied",
        matches!(
            db.reader.read_approval(&ctx, &request()?),
            Err(RevisionError::InvalidRequest)
        ),
    )?;
    probe.check(
        "root_duplicate_revoke_no_retry",
        matches!(
            db.root.revoke_trust(&ctx, &root_request),
            Err(RevisionError::RepositoryFailure)
        ),
    )?;
    let editor = context('e')?;
    let approval_request = FormulaApprovalRevocation::new(
        project()?,
        branch()?,
        "p140-formula".into(),
        approval.policy_version,
        approval.version,
        3,
    )?;
    let ack = probe.step(
        "approval_admin_revoke_after_root_revoked",
        db.approval.revoke_approval(&editor, &approval_request),
    )?;
    probe.acknowledgement(
        "approval_revoke_ack_exact",
        &ack,
        FormulaRegistryManagementAction::RevokeApproval,
        approval.version,
        &editor,
    )?;
    probe.check(
        "approval_duplicate_revoke_no_retry",
        matches!(
            db.approval.revoke_approval(&editor, &approval_request),
            Err(RevisionError::RepositoryFailure)
        ),
    )?;
    Ok(())
}
fn execute(probe: &mut Probe, mode: &str) -> Result<(), RevisionError> {
    if mode == "correct_schema_admitted" {
        probe.step(
            "correct_schema22_fingerprint_control_admitted",
            LocalPostgresFormulaIssuerRegistryRepository::connect(
                &config("p141_reader")?,
                context('a')?,
                None,
            ),
        )?;
        return Ok(());
    }
    if mode == "changed_schema_denied" {
        return probe.check(
            "changed_schema22_fingerprint_denied",
            matches!(
                LocalPostgresFormulaIssuerRegistryRepository::connect(
                    &config("p141_reader")?,
                    context('a')?,
                    None
                ),
                Err(RevisionError::InvalidRequest)
            ),
        );
    }
    if mode != "metadata" {
        return Err(RevisionError::InvalidRequest);
    }
    let db = connect(probe)?;
    read_checks(probe, &db)?;
    context_checks(probe, &db)?;
    let root = rotate_root(probe, &db)?;
    let approval = rotate_approval(probe, &db, &root)?;
    revoke(probe, &db, &root, &approval)
}
fn main() {
    let mut probe = Probe::default();
    let mode = std::env::args().nth(1).unwrap_or_default();
    let result = execute(&mut probe, &mode);
    let success = result.is_ok();
    println!(
        "{}",
        serde_json::json!({
            "state": if success {"PASS_RUST_SQL22_METADATA_NOT_CRYPTO_NATIVE_OR_GATE"} else {"FAIL_CLOSED"},
            "mode": mode, "checks": probe.checks, "failed_stage": if success {None} else {Some(probe.stage)},
            "error_code": result.err().map(|e| e.code()), "real_crypto_executed": false,
            "P09_gate": "OPEN", "product_complete": false,
        })
    );
    if !success {
        std::process::exit(1);
    }
}
