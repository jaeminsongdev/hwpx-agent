#![forbid(unsafe_code)]

pub mod comment_operation;
pub mod form_color_preparation;
pub mod form_product_request;
pub mod form_stored_provider;
pub mod form_value_operation;
pub mod form_value_preparation;
pub mod reference_validation_product;

use std::collections::BTreeMap;
use std::fmt;
use std::fs::File;
use std::io::{Read, Take};
use std::path::{Path, PathBuf};

use domain_ir::{
    Architecture, ArtifactId, BackendHealth, BackendHealthState, BackendId, BackendKind,
    CapabilityCatalog, CapabilityDefinitionDraft, CapabilityId, CapabilityRouteCatalog,
    CapabilityRouter, CapabilityRouterLimits, DocumentGraph, DocumentGraphDraft,
    DocumentGraphLimits, DocumentId, ExactTargetProfile, Flow, IdempotencyKey, Inline, LogicalId,
    Node, NodeCommon, OperationDraft, OperationId, OperationPlanCompiler, OperationPlanDraft,
    OperationPlanLimits, ParagraphNode, PlanId, PolicyScope, PreservationImpact,
    PreservationRequirement, ProjectId, Properties, ProtectionState, RegistryTrustState,
    RevisionId, RouteBinding, RouteContext, Section, Selector, SelectorDraft, SelectorLimits,
    SelectorSnapshot, SignatureImpact, Style, SupportState, TargetProfileId, TransactionId,
};
use hwpx_package::{Hancom2020Vs0Artifact, Hancom2020Vs0Builder, Hancom2020Vs0Error};
use operation_engine::{
    ArtifactDisposition, ClaimLease, ClaimOutcome, CommittedResult, ExecutionManifest, FaultPlan,
    IdempotencyBinding, IdempotencyError, IdempotencyLimits, IdempotencyReceipt,
    IdempotencyService, OwnerToken, RevisionCasOutcome, RevisionCommit, RevisionStreamKey,
    TerminalFailure, TransactionLimits, ValidationOutcome, WorkspaceTransaction,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;
use uuid::Uuid;

pub const VS0_REQUEST_SCHEMA_VERSION: &str = "hwpx-agent.vs0-create-request/v1";
pub const VS0_RESULT_SCHEMA_VERSION: &str = "hwpx-agent.vs0-create-result/v1";
const MAX_REQUEST_BYTES: u64 = 16 * 1024;
const TARGET_PROFILE_ID: &str = "hancom-hangul-2020-secondary";
const TARGET_BUILD: &str = "11.0.0.9136";
const ROUTE_EVIDENCE_SEQUENCE: u64 = 1;
const ROUTE_ATTESTATION: &[u8] =
    include_bytes!("../../../implementation/p04/trust/p04-direct-route-attestation.json");
const ROUTE_ATTESTATION_SIGNATURE_HEX: &str =
    include_str!("../../../implementation/p04/trust/p04-direct-route-attestation.sig");
const ROUTE_ATTESTATION_SHA256: [u8; 32] = [
    0x63, 0x62, 0xab, 0x5d, 0xba, 0x0f, 0x6d, 0xbd, 0xa4, 0xe5, 0x98, 0x37, 0xc9, 0xe4, 0xdd, 0xcd,
    0x96, 0x7a, 0xe4, 0xf9, 0x97, 0x60, 0xf9, 0xeb, 0xd0, 0xa6, 0xcc, 0xe6, 0x34, 0xdc, 0xfe, 0x00,
];
const ROUTE_SIGNATURE_SHA256: [u8; 32] = [
    0x8a, 0xbb, 0x88, 0xc9, 0x8c, 0xea, 0x2b, 0xc3, 0x2f, 0xe5, 0xcf, 0xbc, 0x49, 0x69, 0xb3, 0xa1,
    0xfd, 0xcd, 0xf0, 0x0f, 0xb0, 0xcd, 0x22, 0x4e, 0xb1, 0x1b, 0x0c, 0x01, 0x97, 0xe4, 0x92, 0x68,
];

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Vs0Request {
    schema_version: String,
    idempotency_key: String,
    project_id: String,
    document_id: String,
    base_revision: String,
    expected_head_generation: u64,
    page_preset: String,
    style: String,
    text: String,
}

struct ValidatedRequest {
    key: IdempotencyKey,
    project_id: ProjectId,
    document_id: DocumentId,
    base_revision: RevisionId,
    expected_head_generation: u64,
    text: String,
}

struct PreparedExecution {
    request: ValidatedRequest,
    request_sha256: [u8; 32],
    artifact: Hancom2020Vs0Artifact,
    artifact_size: u64,
    new_revision: RevisionId,
    transaction_id: TransactionId,
    manifest: ExecutionManifest,
    manifest_sha256: [u8; 32],
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum Vs0Disposition {
    Created,
    Replayed,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Vs0Result {
    schema_version: &'static str,
    state: &'static str,
    disposition: Vs0Disposition,
    artifact_relative: String,
    artifact_sha256: String,
    artifact_size: u64,
    revision_id: String,
    target_profile_id: &'static str,
    exact_build: &'static str,
    route: &'static str,
    source_unchanged: bool,
}

impl Vs0Result {
    #[must_use]
    pub const fn disposition(&self) -> Vs0Disposition {
        self.disposition
    }

    #[must_use]
    pub fn artifact_relative(&self) -> &str {
        &self.artifact_relative
    }

    #[must_use]
    pub fn artifact_sha256(&self) -> &str {
        &self.artifact_sha256
    }

    #[must_use]
    pub const fn artifact_size(&self) -> u64 {
        self.artifact_size
    }

    /// Emits bounded public output without request text, keys or absolute paths.
    ///
    /// # Errors
    ///
    /// Returns a stable serialization failure.
    pub fn public_json(&self) -> Result<Vec<u8>, Vs0Error> {
        serde_json::to_vec(self).map_err(|_| Vs0Error::Serialization)
    }
}

pub struct Vs0Engine {
    idempotency: IdempotencyService,
    idempotency_limits: IdempotencyLimits,
}

impl Vs0Engine {
    /// Creates the current in-process P04 reference engine.
    ///
    /// # Errors
    ///
    /// Rejects invalid finite idempotency limits.
    pub fn new() -> Result<Self, Vs0Error> {
        let limits = IdempotencyLimits::default();
        Ok(Self {
            idempotency: IdempotencyService::new(limits).map_err(map_idempotency)?,
            idempotency_limits: limits,
        })
    }

    /// Executes one explicit bounded JSON request through graph compilation, direct routing,
    /// HWPX graph validation, isolated publication and revision/idempotency CAS.
    ///
    /// # Errors
    ///
    /// Fails closed on malformed input, identity drift, route/precondition mismatch, package
    /// rejection, no-overwrite publication failure or revision conflict.
    pub fn execute_file(
        &self,
        request_path: impl AsRef<Path>,
        workspace_root: impl AsRef<Path>,
    ) -> Result<Vs0Result, Vs0Error> {
        let request_path = request_path.as_ref();
        let workspace_root = workspace_root.as_ref();
        let request_bytes = read_request(request_path)?;
        let prepared = prepare_execution(&request_bytes)?;
        let stream = RevisionStreamKey::new(
            prepared.request.project_id.clone(),
            prepared.request.document_id.clone(),
        );
        match self.idempotency.head(&stream) {
            Ok(_) => {}
            Err(IdempotencyError::RevisionStreamMissing) => {
                let _ = self
                    .idempotency
                    .initialize_stream(stream.clone(), prepared.request.base_revision.clone())
                    .map_err(map_idempotency)?;
            }
            Err(error) => return Err(map_idempotency(error)),
        }
        let binding = IdempotencyBinding::new(
            prepared.request.key.clone(),
            prepared.request_sha256,
            prepared.manifest_sha256,
            stream,
            prepared.request.base_revision.clone(),
            prepared.request.expected_head_generation,
            prepared.transaction_id.clone(),
        )
        .map_err(map_idempotency)?;
        let owner_seed = Sha256::digest(
            [
                Uuid::new_v4().as_bytes().as_slice(),
                prepared.request_sha256.as_slice(),
            ]
            .concat(),
        );
        let owner = OwnerToken::new(owner_seed.into()).map_err(map_idempotency)?;
        let lease = match self
            .idempotency
            .claim(binding.clone(), &owner)
            .map_err(map_idempotency)?
        {
            ClaimOutcome::Acquired(lease) => lease,
            ClaimOutcome::Replayed(receipt) => {
                return result_from_receipt(
                    &receipt,
                    Vs0Disposition::Replayed,
                    workspace_root,
                    true,
                );
            }
            ClaimOutcome::Duplicate(_) => return Err(Vs0Error::DuplicateInProgress),
        };
        self.idempotency.start(&lease).map_err(map_idempotency)?;
        self.execute_claimed(prepared, request_path, workspace_root, &lease)
    }

    fn execute_claimed(
        &self,
        prepared: PreparedExecution,
        request_path: &Path,
        workspace_root: &Path,
        lease: &ClaimLease,
    ) -> Result<Vs0Result, Vs0Error> {
        let PreparedExecution {
            artifact,
            artifact_size,
            new_revision,
            manifest,
            ..
        } = prepared;

        let mut transaction =
            WorkspaceTransaction::create(workspace_root, manifest, TransactionLimits::default())
                .map_err(|_| Vs0Error::Transaction)?;
        let expected_artifact_sha256 = artifact.sha256();
        let mut validator = move |bytes: &[u8]| {
            if <[u8; 32]>::from(Sha256::digest(bytes)) == expected_artifact_sha256 {
                ValidationOutcome::Valid
            } else {
                ValidationOutcome::Rejected
            }
        };
        let mut committed_receipt: Option<IdempotencyReceipt> = None;
        let mut cas = |commit_request: &operation_engine::RevisionCommitRequest| {
            let Ok(precommit_sha256) = commit_request.canonical_sha256() else {
                return RevisionCasOutcome::Failed;
            };
            let Ok(commit) = RevisionCommit::new(
                new_revision.clone(),
                commit_request.result_artifact_id().clone(),
                commit_request.result_sha256(),
                commit_request.result_size(),
                precommit_sha256,
                self.idempotency_limits,
            ) else {
                return RevisionCasOutcome::Failed;
            };
            match self.idempotency.commit_success(lease, &commit) {
                Ok(receipt) => {
                    committed_receipt = Some(receipt);
                    RevisionCasOutcome::Committed
                }
                Err(IdempotencyError::RevisionConflict) => RevisionCasOutcome::Conflict,
                Err(_) => RevisionCasOutcome::Failed,
            }
        };
        let execution = artifact
            .with_verified_bytes(|bytes| {
                transaction.execute(
                    request_path,
                    bytes,
                    &mut validator,
                    &mut cas,
                    &mut FaultPlan::none(),
                )
            })
            .map_err(map_builder)?;
        let Ok(transaction_receipt) = execution else {
            if committed_receipt.is_none() {
                let _ = self
                    .idempotency
                    .fail_terminal(lease, TerminalFailure::OperationFailed);
            }
            return Err(Vs0Error::Transaction);
        };
        if !transaction_receipt.source_unchanged()
            || transaction_receipt.artifact_disposition() != ArtifactDisposition::Committed
        {
            return Err(Vs0Error::Transaction);
        }
        let receipt = committed_receipt.ok_or(Vs0Error::RevisionCas)?;
        if artifact_size != receipt.result().map_or(0, CommittedResult::artifact_size) {
            return Err(Vs0Error::ArtifactMismatch);
        }
        result_from_receipt(
            &receipt,
            Vs0Disposition::Created,
            workspace_root,
            transaction_receipt.source_unchanged(),
        )
    }
}

impl fmt::Debug for Vs0Engine {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("Vs0Engine")
            .field("idempotency_limits", &self.idempotency_limits)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum Vs0Error {
    #[error("VS-0 request is invalid")]
    InvalidRequest,
    #[error("VS-0 request exceeds its finite limit")]
    Limit,
    #[error("VS-0 identity is invalid")]
    Identity,
    #[error("VS-0 graph or operation plan failed")]
    Plan,
    #[error("VS-0 direct route failed closed")]
    Route,
    #[error("VS-0 execution manifest failed")]
    Manifest,
    #[error("VS-0 package construction failed")]
    Package,
    #[error("VS-0 idempotency operation failed")]
    Idempotency,
    #[error("VS-0 request is already in progress")]
    DuplicateInProgress,
    #[error("VS-0 workspace transaction failed")]
    Transaction,
    #[error("VS-0 revision CAS did not produce a receipt")]
    RevisionCas,
    #[error("VS-0 published artifact is missing or changed")]
    ArtifactMismatch,
    #[error("VS-0 public receipt serialization failed")]
    Serialization,
}

impl Vs0Error {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidRequest => "vs0_invalid_request",
            Self::Limit => "vs0_limit_exceeded",
            Self::Identity => "vs0_invalid_identity",
            Self::Plan => "vs0_plan_failed",
            Self::Route => "vs0_route_failed",
            Self::Manifest => "vs0_manifest_failed",
            Self::Package => "vs0_package_failed",
            Self::Idempotency => "vs0_idempotency_failed",
            Self::DuplicateInProgress => "vs0_duplicate_in_progress",
            Self::Transaction => "vs0_transaction_failed",
            Self::RevisionCas => "vs0_revision_cas_failed",
            Self::ArtifactMismatch => "vs0_artifact_mismatch",
            Self::Serialization => "vs0_serialization_failed",
        }
    }
}

fn read_request(path: &Path) -> Result<Vec<u8>, Vs0Error> {
    let file = File::open(path).map_err(|_| Vs0Error::InvalidRequest)?;
    let metadata = file.metadata().map_err(|_| Vs0Error::InvalidRequest)?;
    if !metadata.is_file() || metadata.len() == 0 || metadata.len() > MAX_REQUEST_BYTES {
        return Err(Vs0Error::Limit);
    }
    let mut bytes =
        Vec::with_capacity(usize::try_from(metadata.len()).map_err(|_| Vs0Error::Limit)?);
    let mut bounded: Take<File> = file.take(MAX_REQUEST_BYTES.saturating_add(1));
    bounded
        .read_to_end(&mut bytes)
        .map_err(|_| Vs0Error::InvalidRequest)?;
    if bytes.len() != usize::try_from(metadata.len()).map_err(|_| Vs0Error::Limit)? {
        return Err(Vs0Error::InvalidRequest);
    }
    Ok(bytes)
}

fn validate_request(bytes: &[u8]) -> Result<ValidatedRequest, Vs0Error> {
    let request: Vs0Request =
        serde_json::from_slice(bytes).map_err(|_| Vs0Error::InvalidRequest)?;
    if request.schema_version != VS0_REQUEST_SCHEMA_VERSION
        || request.expected_head_generation != 1
        || request.page_preset != "a4_portrait"
        || request.style != "default"
    {
        return Err(Vs0Error::InvalidRequest);
    }
    Hancom2020Vs0Builder::build(&request.text).map_err(map_builder)?;
    Ok(ValidatedRequest {
        key: IdempotencyKey::parse(request.idempotency_key).map_err(|_| Vs0Error::Identity)?,
        project_id: ProjectId::parse(request.project_id).map_err(|_| Vs0Error::Identity)?,
        document_id: DocumentId::parse(request.document_id).map_err(|_| Vs0Error::Identity)?,
        base_revision: RevisionId::parse(request.base_revision).map_err(|_| Vs0Error::Identity)?,
        expected_head_generation: request.expected_head_generation,
        text: request.text,
    })
}

fn prepare_execution(request_bytes: &[u8]) -> Result<PreparedExecution, Vs0Error> {
    let request_sha256: [u8; 32] = Sha256::digest(request_bytes).into();
    let request = validate_request(request_bytes)?;
    let artifact = Hancom2020Vs0Builder::build(&request.text).map_err(map_builder)?;
    let artifact_size = u64::try_from(artifact.size_bytes()).map_err(|_| Vs0Error::Limit)?;
    let new_revision = RevisionId::parse(format!(
        "vs0-revision-{}",
        &hex::encode(artifact.sha256())[..24]
    ))
    .map_err(|_| Vs0Error::Identity)?;
    let (plan, route) = compile_and_route(&request)?;
    let transaction_id = TransactionId::parse(format!(
        "vs0-transaction-{}",
        &hex::encode(request_sha256)[..24]
    ))
    .map_err(|_| Vs0Error::Identity)?;
    let manifest = ExecutionManifest::from_receipts(
        transaction_id.clone(),
        artifact_id(request_sha256)?,
        request_sha256,
        u64::try_from(request_bytes.len()).map_err(|_| Vs0Error::Limit)?,
        &plan,
        &[route],
    )
    .map_err(|_| Vs0Error::Manifest)?;
    let manifest_sha256 = manifest
        .canonical_sha256()
        .map_err(|_| Vs0Error::Manifest)?;
    Ok(PreparedExecution {
        request,
        request_sha256,
        artifact,
        artifact_size,
        new_revision,
        transaction_id,
        manifest,
        manifest_sha256,
    })
}

fn compile_and_route(
    request: &ValidatedRequest,
) -> Result<(domain_ir::CompiledOperationPlan, domain_ir::RouteDecision), Vs0Error> {
    let (plan, capability) = compile_plan(request)?;
    let decision = route_plan(&plan, capability)?;
    Ok((plan, decision))
}

fn compile_plan(
    request: &ValidatedRequest,
) -> Result<(domain_ir::CompiledOperationPlan, CapabilityId), Vs0Error> {
    let paragraph_id = LogicalId::parse("vs0-paragraph-1").map_err(|_| Vs0Error::Identity)?;
    let mut draft = DocumentGraphDraft::new(
        request.document_id.clone(),
        vec![Section {
            section_id: LogicalId::parse("vs0-section-1").map_err(|_| Vs0Error::Identity)?,
            properties: Properties::new(),
            master_pages: Vec::new(),
            headers_footers: Vec::new(),
            body: Flow {
                children: vec![Node::Paragraph(ParagraphNode {
                    common: NodeCommon::new(paragraph_id.clone()),
                    inlines: vec![Inline::Text {
                        text: request.text.clone(),
                    }],
                    paragraph_properties: Properties::new(),
                })],
            },
        }],
    );
    draft.styles.push(Style {
        style_id: LogicalId::parse("vs0-style-default").map_err(|_| Vs0Error::Identity)?,
        based_on: None,
        properties: Properties::new(),
    });
    let graph = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())
        .map_err(|_| Vs0Error::Plan)?;
    let snapshot = SelectorSnapshot::build(
        &graph,
        request.base_revision.clone(),
        SelectorLimits::default(),
    )
    .map_err(|_| Vs0Error::Plan)?;
    let capability = CapabilityId::parse("document.create_vs0").map_err(|_| Vs0Error::Identity)?;
    let catalog =
        CapabilityCatalog::from_drafts(vec![CapabilityDefinitionDraft::new(capability.clone())])
            .map_err(|_| Vs0Error::Plan)?;
    let plan = OperationPlanCompiler::new(OperationPlanLimits::default())
        .map_err(|_| Vs0Error::Plan)?
        .compile(
            OperationPlanDraft::new(
                PlanId::parse("vs0-create-plan").map_err(|_| Vs0Error::Identity)?,
                request.base_revision.clone(),
                vec![OperationDraft {
                    operation_id: OperationId::parse("vs0-create-operation")
                        .map_err(|_| Vs0Error::Identity)?,
                    capability_id: capability.clone(),
                    selector: SelectorDraft::one(Selector::by_logical_id(paragraph_id)),
                    arguments: BTreeMap::new(),
                    depends_on: Vec::new(),
                }],
            ),
            &catalog,
            &snapshot,
            &snapshot.expectation(),
        )
        .map_err(|_| Vs0Error::Plan)?;
    Ok((plan, capability))
}

fn route_plan(
    plan: &domain_ir::CompiledOperationPlan,
    capability: CapabilityId,
) -> Result<domain_ir::RouteDecision, Vs0Error> {
    let registry_digest = verify_route_attestation()?;
    let profile = ExactTargetProfile::new(
        TargetProfileId::parse(TARGET_PROFILE_ID).map_err(|_| Vs0Error::Identity)?,
        TARGET_BUILD,
        Architecture::X86,
    )
    .map_err(|_| Vs0Error::Route)?;
    let backend_id = BackendId::parse("direct-hwpx-vs0").map_err(|_| Vs0Error::Identity)?;
    let routes = CapabilityRouteCatalog::from_bindings(vec![RouteBinding::new(
        capability,
        backend_id.clone(),
        BackendKind::DirectHwpx,
        SupportState::Verified,
        profile.clone(),
        registry_digest,
        ROUTE_EVIDENCE_SEQUENCE,
        100,
        1,
        PreservationImpact::Normalized,
        SignatureImpact::Preserved,
    )])
    .map_err(|_| Vs0Error::Route)?;
    let context = RouteContext::new(
        profile,
        registry_digest,
        ROUTE_EVIDENCE_SEQUENCE,
        RegistryTrustState::SignatureVerified,
        PolicyScope::CurrentPcPersonalLocalDevelopment,
        PreservationRequirement::Normalized,
        ProtectionState::Unprotected,
        1_000,
        vec![BackendHealth::new(
            backend_id,
            BackendHealthState::Healthy,
            1,
            900,
            500,
        )],
    )
    .map_err(|_| Vs0Error::Route)?;
    CapabilityRouter::new(CapabilityRouterLimits::default())
        .map_err(|_| Vs0Error::Route)?
        .route(&plan.operations()[0], &context, &routes)
        .map_err(|_| Vs0Error::Route)
}

fn verify_route_attestation() -> Result<[u8; 32], Vs0Error> {
    verify_route_attestation_bytes(ROUTE_ATTESTATION, ROUTE_ATTESTATION_SIGNATURE_HEX)
}

fn verify_route_attestation_bytes(
    attestation: &[u8],
    signature_hex: &str,
) -> Result<[u8; 32], Vs0Error> {
    let signature_bytes: [u8; 64] = hex::decode(signature_hex.trim())
        .map_err(|_| Vs0Error::Route)?
        .try_into()
        .map_err(|_| Vs0Error::Route)?;
    if <[u8; 32]>::from(Sha256::digest(attestation)) != ROUTE_ATTESTATION_SHA256
        || <[u8; 32]>::from(Sha256::digest(signature_bytes)) != ROUTE_SIGNATURE_SHA256
    {
        return Err(Vs0Error::Route);
    }
    let value: serde_json::Value =
        serde_json::from_slice(attestation).map_err(|_| Vs0Error::Route)?;
    let expected = [
        ("/schema_version", "hwpx-agent.direct-route-attestation/v1"),
        ("/target/profile_id", TARGET_PROFILE_ID),
        ("/target/exact_build", TARGET_BUILD),
        ("/target/architecture", "x86"),
        ("/route/capability_id", "document.create_vs0"),
        ("/route/backend_id", "direct-hwpx-vs0"),
        ("/route/backend_kind", "direct_hwpx"),
        ("/route/support", "verified_current_pc_local"),
        ("/scope/host", "current_pc_exact_identity_only"),
    ];
    if expected.iter().any(|(pointer, text)| {
        value.pointer(pointer).and_then(serde_json::Value::as_str) != Some(text)
    }) || value
        .pointer("/sequence")
        .and_then(serde_json::Value::as_u64)
        != Some(ROUTE_EVIDENCE_SEQUENCE)
        || value
            .pointer("/scope/direct_hwpx_route_allowed")
            .and_then(serde_json::Value::as_bool)
            != Some(true)
        || [
            "/scope/production_allowed",
            "/scope/provider_allowed",
            "/scope/network_allowed",
            "/scope/desktop_automation_route_allowed",
        ]
        .iter()
        .any(|pointer| value.pointer(pointer).and_then(serde_json::Value::as_bool) != Some(false))
    {
        return Err(Vs0Error::Route);
    }
    Ok(ROUTE_ATTESTATION_SHA256)
}

fn artifact_id(digest: [u8; 32]) -> Result<ArtifactId, Vs0Error> {
    ArtifactId::parse(format!("sha256-{}", hex::encode(digest))).map_err(|_| Vs0Error::Identity)
}

fn result_from_receipt(
    receipt: &IdempotencyReceipt,
    disposition: Vs0Disposition,
    workspace_root: &Path,
    source_unchanged: bool,
) -> Result<Vs0Result, Vs0Error> {
    let result = receipt.result().ok_or(Vs0Error::Idempotency)?;
    let sha256 = result.artifact_sha256();
    let relative = PathBuf::from("output")
        .join("artifacts")
        .join(format!("{}.hwpx", hex::encode(sha256)));
    verify_published(workspace_root, &relative, sha256, result.artifact_size())?;
    Ok(Vs0Result {
        schema_version: VS0_RESULT_SCHEMA_VERSION,
        state: "pass",
        disposition,
        artifact_relative: relative.to_string_lossy().replace('\\', "/"),
        artifact_sha256: hex::encode(sha256),
        artifact_size: result.artifact_size(),
        revision_id: result.revision_id().as_str().to_owned(),
        target_profile_id: TARGET_PROFILE_ID,
        exact_build: TARGET_BUILD,
        route: "direct_hwpx",
        source_unchanged,
    })
}

fn verify_published(
    workspace_root: &Path,
    relative: &Path,
    expected_sha256: [u8; 32],
    expected_size: u64,
) -> Result<(), Vs0Error> {
    let path = workspace_root.join(relative);
    let file = File::open(path).map_err(|_| Vs0Error::ArtifactMismatch)?;
    let metadata = file.metadata().map_err(|_| Vs0Error::ArtifactMismatch)?;
    if !metadata.is_file() || metadata.len() != expected_size || expected_size > 1024 * 1024 {
        return Err(Vs0Error::ArtifactMismatch);
    }
    let mut bytes =
        Vec::with_capacity(usize::try_from(expected_size).map_err(|_| Vs0Error::Limit)?);
    file.take(expected_size.saturating_add(1))
        .read_to_end(&mut bytes)
        .map_err(|_| Vs0Error::ArtifactMismatch)?;
    if u64::try_from(bytes.len()).map_err(|_| Vs0Error::Limit)? != expected_size
        || <[u8; 32]>::from(Sha256::digest(bytes)) != expected_sha256
    {
        return Err(Vs0Error::ArtifactMismatch);
    }
    Ok(())
}

fn map_builder(_error: Hancom2020Vs0Error) -> Vs0Error {
    Vs0Error::Package
}

fn map_idempotency(error: IdempotencyError) -> Vs0Error {
    if error == IdempotencyError::KeyReuseConflict {
        Vs0Error::Idempotency
    } else if error == IdempotencyError::RevisionConflict {
        Vs0Error::RevisionCas
    } else {
        Vs0Error::Idempotency
    }
}

#[cfg(test)]
mod tests {
    use super::{
        ROUTE_ATTESTATION, ROUTE_ATTESTATION_SIGNATURE_HEX, Vs0Error, verify_route_attestation,
        verify_route_attestation_bytes,
    };

    #[test]
    fn route_attestation_signature_and_scope_are_required() {
        assert!(verify_route_attestation().is_ok());

        let mut changed = ROUTE_ATTESTATION.to_vec();
        if let Some(first) = changed.first_mut() {
            *first ^= 1;
        }
        assert_eq!(
            verify_route_attestation_bytes(&changed, ROUTE_ATTESTATION_SIGNATURE_HEX,),
            Err(Vs0Error::Route)
        );

        let wrong_signature = "00".repeat(64);
        assert_eq!(
            verify_route_attestation_bytes(ROUTE_ATTESTATION, &wrong_signature,),
            Err(Vs0Error::Route)
        );
    }
}
