use std::cell::Cell;
use std::collections::BTreeMap;
use std::error::Error;
use std::fs;
use std::path::{Path, PathBuf};

use domain_ir::{
    Architecture, ArtifactId, BackendHealth, BackendHealthState, BackendId, BackendKind,
    CapabilityCatalog, CapabilityDefinitionDraft, CapabilityId, CapabilityRouteCatalog,
    CapabilityRouter, CapabilityRouterLimits, DocumentGraph, DocumentGraphDraft,
    DocumentGraphLimits, DocumentId, ExactTargetProfile, Flow, Inline, LogicalId, Node, NodeCommon,
    OperationDraft, OperationId, OperationPlanCompiler, OperationPlanDraft, OperationPlanLimits,
    ParagraphNode, PlanId, PolicyScope, PreservationImpact, PreservationRequirement, Properties,
    ProtectionState, RegistryTrustState, RevisionId, RouteBinding, RouteContext, Section, Selector,
    SelectorDraft, SelectorLimits, SelectorSnapshot, SignatureImpact, SupportState,
    TargetProfileId, TransactionId,
};
use operation_engine::{
    ArtifactDisposition, ExecutionManifest, ExecutionManifestError, FaultMoment, FaultPlan,
    FaultPoint, RevisionCasOutcome, RevisionCommitRequest, StateMachineError, TransactionError,
    TransactionLimits, TransactionState, TransactionStateMachine, TransactionStep,
    ValidationOutcome, WorkspaceTransaction,
};
use sha2::{Digest as _, Sha256};

type TestResult = Result<(), Box<dyn Error>>;

const SOURCE: &[u8] = b"synthetic immutable source artifact";
const OUTPUT: &[u8] = b"synthetic complete output artifact";
const REGISTRY_DIGEST: [u8; 32] = [9; 32];

#[test]
fn manifest_binds_complete_plan_route_and_source_identity() -> TestResult {
    let plan = compiled_plan("edit.noop")?;
    let route_receipt = route(&plan, "direct")?;
    let first = manifest(
        "tx-manifest",
        SOURCE,
        &plan,
        std::slice::from_ref(&route_receipt),
    )?;
    let second = manifest(
        "tx-manifest",
        SOURCE,
        &plan,
        std::slice::from_ref(&route_receipt),
    )?;
    assert_eq!(first.canonical_json()?, second.canonical_json()?);
    assert_eq!(first.canonical_sha256()?, second.canonical_sha256()?);
    assert_eq!(first.route_count(), 1);

    assert_manifest_error(
        ExecutionManifest::from_receipts(
            TransactionId::parse("tx-empty")?,
            ArtifactId::parse("source-artifact")?,
            Sha256::digest(SOURCE).into(),
            u64::try_from(SOURCE.len())?,
            &plan,
            &[],
        ),
        "execution_manifest_route_set_mismatch",
    );
    assert_manifest_error(
        ExecutionManifest::from_receipts(
            TransactionId::parse("tx-zero")?,
            ArtifactId::parse("source-artifact")?,
            [0; 32],
            u64::try_from(SOURCE.len())?,
            &plan,
            &[route(&plan, "direct")?],
        ),
        "execution_manifest_invalid_source_identity",
    );

    let other_plan = compiled_plan("edit.other")?;
    assert_manifest_error(
        ExecutionManifest::from_receipts(
            TransactionId::parse("tx-route-drift")?,
            ArtifactId::parse("source-artifact")?,
            Sha256::digest(SOURCE).into(),
            u64::try_from(SOURCE.len())?,
            &other_plan,
            &[route(&plan, "direct")?],
        ),
        "execution_manifest_route_set_mismatch",
    );
    Ok(())
}

#[test]
fn state_machine_rejects_skip_repeat_backward_and_terminal_transition() -> TestResult {
    let mut machine = TransactionStateMachine::default();
    assert_state_error(
        machine.advance(TransactionState::PreconditionsVerified),
        "workspace_transaction_invalid_transition",
    );
    for state in [
        TransactionState::Planned,
        TransactionState::PreconditionsVerified,
        TransactionState::WorkspacePrepared,
        TransactionState::Executing,
        TransactionState::Readback,
        TransactionState::Validating,
        TransactionState::ArtifactCommitted,
        TransactionState::RevisionCasCommitted,
        TransactionState::Completed,
    ] {
        machine.advance(state)?;
    }
    assert_state_error(
        machine.advance(TransactionState::Completed),
        "workspace_transaction_terminal_state",
    );
    assert_eq!(machine.state(), TransactionState::Completed);
    Ok(())
}

#[test]
fn successful_transaction_is_complete_deterministic_and_source_read_only() -> TestResult {
    let first_root = tempfile::tempdir()?;
    let second_root = tempfile::tempdir()?;
    let first_source = write_source(first_root.path(), SOURCE)?;
    let second_source = write_source(second_root.path(), SOURCE)?;
    let fixture = fixture_manifest("tx-success", SOURCE)?;

    let first_workspace = first_root.path().join("workspace");
    let mut first = WorkspaceTransaction::create(
        &first_workspace,
        fixture.clone(),
        TransactionLimits::default(),
    )?;
    let mut validator = |bytes: &[u8]| {
        if bytes == OUTPUT {
            ValidationOutcome::Valid
        } else {
            ValidationOutcome::Rejected
        }
    };
    let cas_seen = Cell::new(false);
    let mut cas = |request: &RevisionCommitRequest| {
        cas_seen.set(request.result_sha256() == <[u8; 32]>::from(Sha256::digest(OUTPUT)));
        RevisionCasOutcome::Committed
    };
    let first_receipt = first.execute(
        &first_source,
        OUTPUT,
        &mut validator,
        &mut cas,
        &mut FaultPlan::none(),
    )?;
    assert!(cas_seen.get());
    assert_eq!(first_receipt.state(), TransactionState::Completed);
    assert!(first_receipt.source_unchanged());
    assert_eq!(
        first_receipt.artifact_disposition(),
        ArtifactDisposition::Committed
    );
    assert_eq!(fs::read(&first_source)?, SOURCE);
    assert_eq!(read_only_file(&first_workspace.join("output"))?, OUTPUT);

    let second_workspace = second_root.path().join("workspace");
    let mut second =
        WorkspaceTransaction::create(&second_workspace, fixture, TransactionLimits::default())?;
    let mut second_validator = |_bytes: &[u8]| ValidationOutcome::Valid;
    let mut second_cas = |_request: &RevisionCommitRequest| RevisionCasOutcome::Committed;
    let second_receipt = second.execute(
        &second_source,
        OUTPUT,
        &mut second_validator,
        &mut second_cas,
        &mut FaultPlan::none(),
    )?;
    assert_eq!(
        first_receipt.canonical_json()?,
        second_receipt.canonical_json()?
    );
    Ok(())
}

#[test]
fn validation_rejection_rolls_back_without_public_output_or_source_mutation() -> TestResult {
    let temporary = tempfile::tempdir()?;
    let source = write_source(temporary.path(), SOURCE)?;
    let workspace = temporary.path().join("workspace");
    let mut transaction = WorkspaceTransaction::create(
        &workspace,
        fixture_manifest("tx-reject", SOURCE)?,
        TransactionLimits::default(),
    )?;
    let mut validator = |_bytes: &[u8]| ValidationOutcome::Rejected;
    let mut cas = |_request: &RevisionCommitRequest| RevisionCasOutcome::Committed;
    let failure = transaction
        .execute(
            &source,
            OUTPUT,
            &mut validator,
            &mut cas,
            &mut FaultPlan::none(),
        )
        .err()
        .ok_or("validation rejection unexpectedly succeeded")?;
    assert_eq!(failure.primary(), TransactionError::ValidationRejected);
    assert_eq!(failure.receipt().state(), TransactionState::RolledBack);
    assert!(failure.receipt().source_unchanged());
    assert_eq!(
        failure.receipt().artifact_disposition(),
        ArtifactDisposition::Absent
    );
    assert_eq!(fs::read(source)?, SOURCE);
    assert_eq!(file_count(&workspace.join("output"))?, 0);
    Ok(())
}

#[test]
fn source_drift_workspace_overlap_and_finite_limits_fail_before_publication() -> TestResult {
    let temporary = tempfile::tempdir()?;
    let source = write_source(temporary.path(), SOURCE)?;
    let workspace = temporary.path().join("workspace");
    let fixture = fixture_manifest("tx-source-drift", SOURCE)?;
    fs::write(&source, b"changed source")?;
    let mut transaction =
        WorkspaceTransaction::create(&workspace, fixture, TransactionLimits::default())?;
    let failure = execute_valid(
        &mut transaction,
        &source,
        OUTPUT,
        RevisionCasOutcome::Committed,
    )
    .err()
    .ok_or("source drift unexpectedly succeeded")?;
    assert_eq!(failure.primary(), TransactionError::SourceIdentityMismatch);
    assert!(failure.receipt().source_unchanged());
    assert_eq!(file_count(&workspace.join("output"))?, 0);

    fs::write(&source, SOURCE)?;
    let mutation_workspace = temporary.path().join("mutation-workspace");
    let mut mutation = WorkspaceTransaction::create(
        &mutation_workspace,
        fixture_manifest("tx-midflight-mutation", SOURCE)?,
        TransactionLimits::default(),
    )?;
    let source_for_validator = source.clone();
    let mut mutating_validator = move |_bytes: &[u8]| {
        let _ = fs::write(&source_for_validator, b"external concurrent mutation");
        ValidationOutcome::Valid
    };
    let mut committed_cas = |_request: &RevisionCommitRequest| RevisionCasOutcome::Committed;
    let mutation_failure = mutation
        .execute(
            &source,
            OUTPUT,
            &mut mutating_validator,
            &mut committed_cas,
            &mut FaultPlan::none(),
        )
        .err()
        .ok_or("midflight source mutation unexpectedly succeeded")?;
    assert_eq!(
        mutation_failure.primary(),
        TransactionError::SourceMutationDetected
    );
    assert!(!mutation_failure.receipt().source_unchanged());
    assert_eq!(file_count(&mutation_workspace.join("output"))?, 0);

    let overlap_root = temporary.path().join("overlap-workspace");
    fs::create_dir_all(&overlap_root)?;
    let overlap_source = overlap_root.join("source.hwpx");
    fs::write(&overlap_source, SOURCE)?;
    let mut overlap = WorkspaceTransaction::create(
        &overlap_root,
        fixture_manifest("tx-overlap", SOURCE)?,
        TransactionLimits::default(),
    )?;
    let overlap_failure = execute_valid(
        &mut overlap,
        &overlap_source,
        OUTPUT,
        RevisionCasOutcome::Committed,
    )
    .err()
    .ok_or("workspace-overlap source unexpectedly succeeded")?;
    assert_eq!(overlap_failure.primary(), TransactionError::InvalidSource);
    assert!(overlap_failure.receipt().source_unchanged());

    let link_target = temporary.path().join("link-target.hwpx");
    let link_source = temporary.path().join("linked-source.hwpx");
    fs::write(&link_target, SOURCE)?;
    create_file_link(&link_target, &link_source)?;
    let link_workspace = temporary.path().join("link-workspace");
    let mut linked = WorkspaceTransaction::create(
        &link_workspace,
        fixture_manifest("tx-linked-source", SOURCE)?,
        TransactionLimits::default(),
    )?;
    let link_failure = execute_valid(
        &mut linked,
        &link_source,
        OUTPUT,
        RevisionCasOutcome::Committed,
    )
    .err()
    .ok_or("linked source unexpectedly succeeded")?;
    assert_eq!(link_failure.primary(), TransactionError::InvalidSource);
    assert_eq!(file_count(&link_workspace.join("output"))?, 0);

    assert_eq!(
        WorkspaceTransaction::create(
            temporary.path().join("tiny-workspace"),
            fixture_manifest("tx-tiny", SOURCE)?,
            TransactionLimits {
                max_source_bytes: 1,
                ..TransactionLimits::default()
            },
        )
        .err(),
        Some(TransactionError::LimitExceeded)
    );
    Ok(())
}

#[test]
fn revision_conflict_quarantines_complete_artifact_and_keeps_source() -> TestResult {
    let temporary = tempfile::tempdir()?;
    let source = write_source(temporary.path(), SOURCE)?;
    let workspace = temporary.path().join("workspace");
    let mut transaction = WorkspaceTransaction::create(
        &workspace,
        fixture_manifest("tx-cas-conflict", SOURCE)?,
        TransactionLimits::default(),
    )?;
    let failure = execute_valid(
        &mut transaction,
        &source,
        OUTPUT,
        RevisionCasOutcome::Conflict,
    )
    .err()
    .ok_or("CAS conflict unexpectedly succeeded")?;
    assert_eq!(failure.primary(), TransactionError::RevisionConflict);
    assert_eq!(failure.receipt().state(), TransactionState::Quarantined);
    assert_eq!(
        failure.receipt().artifact_disposition(),
        ArtifactDisposition::Quarantined
    );
    assert!(failure.receipt().source_unchanged());
    assert_eq!(fs::read(source)?, SOURCE);
    assert_eq!(file_count(&workspace.join("output"))?, 0);
    assert_eq!(read_only_file(&workspace.join("quarantine"))?, OUTPUT);
    Ok(())
}

#[test]
fn every_normal_transition_fault_is_absent_quarantined_or_complete() -> TestResult {
    for step in TransactionStep::NORMAL {
        for moment in [FaultMoment::Before, FaultMoment::After] {
            let temporary = tempfile::tempdir()?;
            let source = write_source(temporary.path(), SOURCE)?;
            let workspace = temporary.path().join("workspace");
            let transaction_name = format!("tx-fault-{step:?}-{moment:?}");
            let mut transaction = WorkspaceTransaction::create(
                &workspace,
                fixture_manifest(&transaction_name, SOURCE)?,
                TransactionLimits::default(),
            )?;
            let mut validator = |_bytes: &[u8]| ValidationOutcome::Valid;
            let mut cas = |_request: &RevisionCommitRequest| RevisionCasOutcome::Committed;
            let failure = transaction
                .execute(
                    &source,
                    OUTPUT,
                    &mut validator,
                    &mut cas,
                    &mut FaultPlan::at(FaultPoint::new(step, moment)),
                )
                .err()
                .ok_or("fault injection unexpectedly succeeded")?;
            assert_eq!(failure.primary(), TransactionError::InjectedFault);
            assert!(failure.receipt().source_unchanged());
            assert_eq!(fs::read(&source)?, SOURCE);
            let public_files = file_count(&workspace.join("output"))?;
            match failure.receipt().state() {
                TransactionState::RolledBack => {
                    assert_eq!(public_files, 0);
                    assert_eq!(
                        failure.receipt().artifact_disposition(),
                        ArtifactDisposition::Absent
                    );
                }
                TransactionState::Quarantined => {
                    assert_eq!(public_files, 0);
                    assert_eq!(read_only_file(&workspace.join("quarantine"))?, OUTPUT);
                }
                TransactionState::RevisionCasCommitted | TransactionState::Completed => {
                    assert_eq!(public_files, 1);
                    assert_eq!(read_only_file(&workspace.join("output"))?, OUTPUT);
                }
                state => return Err(format!("unexpected fault terminal state: {state:?}").into()),
            }
        }
    }
    Ok(())
}

#[test]
fn recovery_faults_are_explicit_and_never_create_partial_bytes() -> TestResult {
    for moment in [FaultMoment::Before, FaultMoment::After] {
        let temporary = tempfile::tempdir()?;
        let source = write_source(temporary.path(), SOURCE)?;
        let workspace = temporary.path().join("rollback-workspace");
        let mut transaction = WorkspaceTransaction::create(
            &workspace,
            fixture_manifest(&format!("tx-rollback-{moment:?}"), SOURCE)?,
            TransactionLimits::default(),
        )?;
        let mut validator = |_bytes: &[u8]| ValidationOutcome::Rejected;
        let mut cas = |_request: &RevisionCommitRequest| RevisionCasOutcome::Committed;
        let failure = transaction
            .execute(
                &source,
                OUTPUT,
                &mut validator,
                &mut cas,
                &mut FaultPlan::at(FaultPoint::new(TransactionStep::Rollback, moment)),
            )
            .err()
            .ok_or("rollback recovery fault unexpectedly succeeded")?;
        assert_eq!(failure.primary(), TransactionError::ValidationRejected);
        assert_eq!(failure.recovery(), Some(TransactionError::InjectedFault));
        assert!(failure.receipt().source_unchanged());
        assert_eq!(file_count(&workspace.join("output"))?, 0);
    }

    for moment in [FaultMoment::Before, FaultMoment::After] {
        let temporary = tempfile::tempdir()?;
        let source = write_source(temporary.path(), SOURCE)?;
        let workspace = temporary.path().join("quarantine-workspace");
        let mut transaction = WorkspaceTransaction::create(
            &workspace,
            fixture_manifest(&format!("tx-quarantine-{moment:?}"), SOURCE)?,
            TransactionLimits::default(),
        )?;
        let mut validator = |_bytes: &[u8]| ValidationOutcome::Valid;
        let mut cas = |_request: &RevisionCommitRequest| RevisionCasOutcome::Conflict;
        let failure = transaction
            .execute(
                &source,
                OUTPUT,
                &mut validator,
                &mut cas,
                &mut FaultPlan::at(FaultPoint::new(TransactionStep::Quarantine, moment)),
            )
            .err()
            .ok_or("quarantine recovery fault unexpectedly succeeded")?;
        assert_eq!(failure.primary(), TransactionError::RevisionConflict);
        assert_eq!(failure.recovery(), Some(TransactionError::InjectedFault));
        assert!(failure.receipt().source_unchanged());
        let visible = file_count(&workspace.join("output"))?;
        let quarantined = file_count(&workspace.join("quarantine"))?;
        assert_eq!(visible + quarantined, 1);
        let root = if visible == 1 {
            workspace.join("output")
        } else {
            workspace.join("quarantine")
        };
        assert_eq!(read_only_file(&root)?, OUTPUT);
    }
    Ok(())
}

#[test]
fn no_overwrite_single_use_and_debug_redaction_hold() -> TestResult {
    let temporary = tempfile::tempdir()?;
    let source = write_source(temporary.path(), SOURCE)?;
    let workspace = temporary.path().join("workspace");
    let mut first = WorkspaceTransaction::create(
        &workspace,
        fixture_manifest("private-transaction-one", SOURCE)?,
        TransactionLimits::default(),
    )?;
    let first_receipt = execute_valid(&mut first, &source, OUTPUT, RevisionCasOutcome::Committed)?;
    let original = read_only_file(&workspace.join("output"))?;

    let mut second = WorkspaceTransaction::create(
        &workspace,
        fixture_manifest("../private/transaction-two", SOURCE)?,
        TransactionLimits::default(),
    )?;
    let failure = execute_valid(&mut second, &source, OUTPUT, RevisionCasOutcome::Committed)
        .err()
        .ok_or("no-overwrite transaction unexpectedly succeeded")?;
    assert_eq!(failure.primary(), TransactionError::ArtifactExists);
    assert_eq!(read_only_file(&workspace.join("output"))?, original);

    let second_failure = execute_valid(&mut first, &source, OUTPUT, RevisionCasOutcome::Committed)
        .err()
        .ok_or("single-use transaction unexpectedly ran twice")?;
    assert_eq!(second_failure.primary(), TransactionError::InvalidState);
    assert_eq!(
        second_failure.receipt().state(),
        TransactionState::Completed
    );

    for rendered in [
        format!("{first:?}"),
        format!("{first_receipt:?}"),
        format!("{failure:?}"),
        format!("{:?}", fixture_manifest("private-secret-id", SOURCE)?),
    ] {
        assert!(!rendered.contains("private"));
        assert!(!rendered.contains("source-artifact"));
        assert!(!rendered.contains("synthetic-2020"));
        assert!(!rendered.contains(temporary.path().to_string_lossy().as_ref()));
    }
    Ok(())
}

fn fixture_manifest(id: &str, source: &[u8]) -> Result<ExecutionManifest, Box<dyn Error>> {
    let plan = compiled_plan("edit.noop")?;
    let route = route(&plan, "direct")?;
    manifest(id, source, &plan, &[route])
}

fn manifest(
    id: &str,
    source: &[u8],
    plan: &domain_ir::CompiledOperationPlan,
    routes: &[domain_ir::RouteDecision],
) -> Result<ExecutionManifest, Box<dyn Error>> {
    Ok(ExecutionManifest::from_receipts(
        TransactionId::parse(id)?,
        ArtifactId::parse("source-artifact")?,
        Sha256::digest(source).into(),
        u64::try_from(source.len())?,
        plan,
        routes,
    )?)
}

fn compiled_plan(
    capability_name: &str,
) -> Result<domain_ir::CompiledOperationPlan, Box<dyn Error>> {
    let draft = DocumentGraphDraft::new(
        DocumentId::parse("transaction-document")?,
        vec![Section {
            section_id: LogicalId::parse("section-1")?,
            properties: Properties::new(),
            master_pages: Vec::new(),
            headers_footers: Vec::new(),
            body: Flow {
                children: vec![Node::Paragraph(ParagraphNode {
                    common: NodeCommon::new(LogicalId::parse("p-1")?),
                    inlines: vec![Inline::Text {
                        text: "synthetic transaction target".into(),
                    }],
                    paragraph_properties: Properties::new(),
                })],
            },
        }],
    );
    let graph = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())?;
    let revision = RevisionId::parse("revision-1")?;
    let snapshot = SelectorSnapshot::build(&graph, revision.clone(), SelectorLimits::default())?;
    let capability = CapabilityId::parse(capability_name)?;
    let catalog =
        CapabilityCatalog::from_drafts(vec![CapabilityDefinitionDraft::new(capability.clone())])?;
    Ok(
        OperationPlanCompiler::new(OperationPlanLimits::default())?.compile(
            OperationPlanDraft::new(
                PlanId::parse("plan-1")?,
                revision,
                vec![OperationDraft {
                    operation_id: OperationId::parse("operation-1")?,
                    capability_id: capability,
                    selector: SelectorDraft::one(Selector::by_logical_id(LogicalId::parse("p-1")?)),
                    arguments: BTreeMap::new(),
                    depends_on: Vec::new(),
                }],
            ),
            &catalog,
            &snapshot,
            &snapshot.expectation(),
        )?,
    )
}

fn route(
    plan: &domain_ir::CompiledOperationPlan,
    backend: &str,
) -> Result<domain_ir::RouteDecision, Box<dyn Error>> {
    let profile = ExactTargetProfile::new(
        TargetProfileId::parse("synthetic-2020-current")?,
        "synthetic-2020-build",
        Architecture::X86,
    )?;
    let backend_id = BackendId::parse(backend)?;
    let catalog = CapabilityRouteCatalog::from_bindings(vec![RouteBinding::new(
        plan.operations()[0].capability_id().clone(),
        backend_id.clone(),
        BackendKind::DirectHwpx,
        SupportState::Verified,
        profile.clone(),
        REGISTRY_DIGEST,
        7,
        10,
        10,
        PreservationImpact::Exact,
        SignatureImpact::Preserved,
    )])?;
    let context = RouteContext::new(
        profile,
        REGISTRY_DIGEST,
        7,
        RegistryTrustState::SignatureVerified,
        PolicyScope::CurrentPcPersonalLocalDevelopment,
        PreservationRequirement::Exact,
        ProtectionState::Unprotected,
        1_000,
        vec![BackendHealth::new(
            backend_id,
            BackendHealthState::Healthy,
            3,
            900,
            500,
        )],
    )?;
    Ok(
        CapabilityRouter::new(CapabilityRouterLimits::default())?.route(
            &plan.operations()[0],
            &context,
            &catalog,
        )?,
    )
}

fn write_source(root: &Path, bytes: &[u8]) -> Result<PathBuf, Box<dyn Error>> {
    let path = root.join("source.hwpx");
    fs::write(&path, bytes)?;
    Ok(path)
}

#[cfg(unix)]
fn create_file_link(target: &Path, link: &Path) -> std::io::Result<()> {
    std::os::unix::fs::symlink(target, link)
}

#[cfg(windows)]
fn create_file_link(target: &Path, link: &Path) -> std::io::Result<()> {
    std::os::windows::fs::symlink_file(target, link)
}

fn execute_valid(
    transaction: &mut WorkspaceTransaction,
    source: &Path,
    output: &[u8],
    cas_outcome: RevisionCasOutcome,
) -> Result<operation_engine::TransactionReceipt, operation_engine::TransactionFailure> {
    let mut validator = |_bytes: &[u8]| ValidationOutcome::Valid;
    let mut cas = move |_request: &RevisionCommitRequest| cas_outcome;
    transaction.execute(
        source,
        output,
        &mut validator,
        &mut cas,
        &mut FaultPlan::none(),
    )
}

fn file_count(root: &Path) -> Result<usize, Box<dyn Error>> {
    if !root.exists() {
        return Ok(0);
    }
    let mut count = 0_usize;
    let mut pending = vec![root.to_path_buf()];
    while let Some(next) = pending.pop() {
        for entry in fs::read_dir(next)? {
            let entry = entry?;
            if entry.file_type()?.is_dir() {
                pending.push(entry.path());
            } else {
                count = count.saturating_add(1);
            }
        }
    }
    Ok(count)
}

fn read_only_file(root: &Path) -> Result<Vec<u8>, Box<dyn Error>> {
    let mut files = Vec::new();
    let mut pending = vec![root.to_path_buf()];
    while let Some(next) = pending.pop() {
        if !next.exists() {
            continue;
        }
        for entry in fs::read_dir(next)? {
            let entry = entry?;
            if entry.file_type()?.is_dir() {
                pending.push(entry.path());
            } else {
                files.push(entry.path());
            }
        }
    }
    if files.len() != 1 {
        return Err(format!("expected one complete file, found {}", files.len()).into());
    }
    Ok(fs::read(&files[0])?)
}

fn assert_manifest_error<T>(result: Result<T, ExecutionManifestError>, expected: &str) {
    assert_eq!(
        result.err().map(ExecutionManifestError::code),
        Some(expected)
    );
}

fn assert_state_error(result: Result<(), StateMachineError>, expected: &str) {
    assert_eq!(result.err().map(StateMachineError::code), Some(expected));
}
#[path="support/bytes_transaction.rs"]mod bytes_v1;
#[path="support/unknown_cas_transaction.rs"]mod unknown_cas;
#[path="support/prepared_precommit.rs"]mod prepared_precommit;
#[path="support/archived_manifest.rs"]mod archived_manifest;
