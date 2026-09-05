use std::collections::{BTreeMap, BTreeSet};
use std::error::Error;
use std::sync::atomic::{AtomicUsize, Ordering};

use artifact_service::{SubjectDigest, TenantId};
use auth_middleware::{
    AuthContext, AuthMiddleware, AuthRegistryLimits, AuthScope, PrincipalGrant, TenantRole,
};
use base64::{Engine as _, engine::general_purpose::URL_SAFE_NO_PAD};
use domain_ir::{
    Architecture, ArgumentDraft, ArgumentKind, ArgumentSpec, BackendHealth, BackendHealthState,
    BackendId, BackendKind, CapabilityCatalog, CapabilityDefinitionDraft, CapabilityId,
    CapabilityRouteCatalog, CapabilityRouter, CapabilityRouterLimits, CompiledOperationPlan,
    DefaultPolicy, DocumentGraph, DocumentGraphDraft, DocumentGraphLimits, DocumentId,
    ExactTargetProfile, Flow, Inline, LogicalId, Node, NodeCommon, OperationDraft, OperationId,
    OperationPlanCompiler, OperationPlanDraft, OperationPlanLimits, ParagraphNode, PlanId,
    PolicyScope, PreservationImpact, PreservationRequirement, Properties, ProtectionState,
    RegistryTrustState, RevisionId, RouteBinding, RouteContext, Selector, SelectorDraft,
    SelectorLimits, SelectorSnapshot, SemanticDiff, SemanticDiffLimits, SemanticDiffSnapshot,
    SemanticDiffSummary, SemanticSummaryLimits, SignatureImpact as DomainSignatureImpact,
    SupportState, TargetProfileId,
};
use hmac::{Hmac, Mac as _};
use mcp_control_plane::{
    CompiledPlanSubmission, CurrentPlanSource, DryRunState, EstimatedPageEffect,
    InMemoryProjectPolicy, PlanDryRunReceipt, PlanExecutionPolicyReceipt, PlanReviewError,
    PlanReviewEvidence, PlanReviewEvidenceQuery, PlanReviewEvidenceRepository,
    PlanReviewRenderRequest, PlanReviewRenderer, PlanReviewRisk, PlanReviewRouteSet,
    PlanReviewSignatureImpact, PlanReviewWarning, PlanReviewWarningKind, PlanReviewWarningSeverity,
    PlanSignatureReceipt, PlanSourceRepository, ProjectAccess, ProjectPolicyLimits,
    StoredPlanError, StoredPlanLimits, StoredPlanRegistry,
};
use serde_json::{Value, json};
use sha2::Sha256;
use uuid::Uuid;

type TestResult = Result<(), Box<dyn Error>>;

const NOW: u64 = 2_000_000_000;
const NOW_MS: u64 = NOW * 1_000;
const PROJECT: &str = "prj_private001";
const REVISION: &str = "rev_private001";
const PLAN: &str = "plan_private001";
const TARGET_PROFILE: &str = "hancom-hangul-2020-secondary";
const ISSUER: &str = "https://identity.hwpx-agent.example";
const RESOURCE: &str = "https://mcp.hwpx-agent.example";
const REGISTRY_DIGEST: [u8; 32] = [7; 32];
const REGISTRY_SEQUENCE: u64 = 42;
// Disposable local test key, never a user credential.
const KEY: &[u8] = b"0123456789abcdef0123456789abcdef";

fn graph(text: &str) -> Result<DocumentGraph, Box<dyn Error>> {
    Ok(DocumentGraph::from_draft(
        DocumentGraphDraft::new(
            DocumentId::parse("private-document")?,
            vec![domain_ir::Section {
                section_id: LogicalId::parse("private-section")?,
                properties: Properties::new(),
                master_pages: vec![],
                headers_footers: vec![],
                body: Flow {
                    children: vec![Node::Paragraph(ParagraphNode {
                        common: NodeCommon::new(LogicalId::parse("private-paragraph")?),
                        inlines: vec![Inline::Text {
                            text: text.to_owned(),
                        }],
                        paragraph_properties: Properties::new(),
                    })],
                },
            }],
        ),
        DocumentGraphLimits::default(),
    )?)
}

fn compile(
    source: &DocumentGraph,
    plan_id: &str,
    replacement: &str,
) -> Result<CompiledOperationPlan, Box<dyn Error>> {
    compile_operations(source, plan_id, replacement, 1)
}

fn compile_operations(
    source: &DocumentGraph,
    plan_id: &str,
    replacement: &str,
    operation_count: usize,
) -> Result<CompiledOperationPlan, Box<dyn Error>> {
    let revision = RevisionId::parse(REVISION)?;
    let snapshot = SelectorSnapshot::build(source, revision.clone(), SelectorLimits::default())?;
    let capability_id = CapabilityId::parse("text.replace")?;
    let mut definition = CapabilityDefinitionDraft::new(capability_id.clone());
    definition.arguments.insert(
        "text".to_owned(),
        ArgumentSpec {
            kind: ArgumentKind::Text {
                max_bytes: 256 * 1024,
            },
            required: true,
            default: None,
            default_policy: DefaultPolicy::Fallback,
        },
    );
    let catalog = CapabilityCatalog::from_drafts(vec![definition])?;
    let operations = (0..operation_count)
        .map(|index| {
            Ok(OperationDraft {
                operation_id: OperationId::parse(format!("private-operation-{index}"))?,
                capability_id: capability_id.clone(),
                selector: SelectorDraft::one(Selector::by_logical_id(LogicalId::parse(
                    "private-paragraph",
                )?)),
                arguments: BTreeMap::from([(
                    "text".to_owned(),
                    ArgumentDraft::Text(replacement.to_owned()),
                )]),
                depends_on: vec![],
            })
        })
        .collect::<Result<Vec<_>, Box<dyn Error>>>()?;
    Ok(
        OperationPlanCompiler::new(OperationPlanLimits::default())?.compile(
            OperationPlanDraft::new(PlanId::parse(plan_id)?, revision, operations),
            &catalog,
            &snapshot,
            &snapshot.expectation(),
        )?,
    )
}

fn token(tenant: TenantId, expires: u64) -> Result<String, Box<dyn Error>> {
    let header = URL_SAFE_NO_PAD.encode(serde_json::to_vec(
        &json!({"alg":"HS256","kid":"local-key-01","typ":"at+jwt"}),
    )?);
    let claims = URL_SAFE_NO_PAD.encode(serde_json::to_vec(&json!({
        "iss": ISSUER, "sub": "private-owner", "aud": RESOURCE, "exp": expires,
        "nbf": NOW - 60, "iat": NOW - 60, "jti": "plan-review-owner",
        "scope": "project.read project.write", "token_kind": "user", "tenant_id": tenant,
    }))?);
    let input = format!("{header}.{claims}");
    let mut signer = <Hmac<Sha256> as hmac::KeyInit>::new_from_slice(KEY)?;
    signer.update(input.as_bytes());
    Ok(format!(
        "Bearer {input}.{}",
        URL_SAFE_NO_PAD.encode(signer.finalize().into_bytes())
    ))
}

struct Source {
    tenant: TenantId,
    graph: DocumentGraph,
    allowed: BTreeSet<SubjectDigest>,
    calls: AtomicUsize,
    deny: bool,
}

impl std::fmt::Debug for Source {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter.write_str("Source(<redacted>)")
    }
}

impl PlanSourceRepository for Source {
    fn current_source(
        &self,
        context: &AuthContext,
        project_id: &str,
    ) -> Result<CurrentPlanSource, StoredPlanError> {
        self.calls.fetch_add(1, Ordering::SeqCst);
        if self.deny
            || context.tenant_id() != self.tenant
            || project_id != PROJECT
            || !self.allowed.contains(&context.subject())
        {
            return Err(StoredPlanError::NotFound);
        }
        CurrentPlanSource::from_graph(self.tenant, PROJECT, REVISION, &self.graph)
    }
}

struct Fixture {
    registry: StoredPlanRegistry,
    auth: AuthMiddleware,
    policy: InMemoryProjectPolicy,
    source: Source,
    bearer: String,
    before: DocumentGraph,
    after: DocumentGraph,
}

impl Fixture {
    fn new() -> Result<Self, Box<dyn Error>> {
        let tenant = TenantId::new(Uuid::from_u128(1))?;
        let mut auth = AuthMiddleware::new(
            RESOURCE,
            format!("{RESOURCE}/.well-known/oauth-protected-resource"),
            60,
            AuthRegistryLimits::product_maximums(),
        )?;
        auth.register_local_hmac_key(ISSUER, "local-key-01", KEY, NOW - 600, NOW + 7_200)?;
        let subject = auth.register_user(
            ISSUER,
            "private-owner",
            PrincipalGrant::new(
                tenant,
                TenantRole::Owner,
                [AuthScope::ProjectRead, AuthScope::ProjectWrite],
                NOW - 600,
                NOW + 7_200,
            )?,
        )?;
        let mut policy = InMemoryProjectPolicy::new(ProjectPolicyLimits::product_maximums());
        policy.register_project(PROJECT, tenant)?;
        policy.register_membership(PROJECT, subject, ProjectAccess::Owner)?;
        let before = graph("PRIVATE SOURCE BODY")?;
        let after = graph("PRIVATE REPLACEMENT BODY")?;
        let mut fixture = Self {
            registry: StoredPlanRegistry::new(StoredPlanLimits::product_maximums()),
            auth,
            policy,
            source: Source {
                tenant,
                graph: before.clone(),
                allowed: BTreeSet::from([subject]),
                calls: AtomicUsize::new(0),
                deny: false,
            },
            bearer: token(tenant, NOW + 600)?,
            before,
            after,
        };
        let plan = compile(&fixture.before, PLAN, "PRIVATE REPLACEMENT BODY")?;
        fixture.registry.insert(
            &mut fixture.auth,
            &fixture.policy,
            &fixture.source,
            CompiledPlanSubmission::new(&fixture.bearer, PROJECT, plan, NOW),
        )?;
        Ok(fixture)
    }

    fn render(
        &mut self,
        evidence: &mut EvidenceRepository,
    ) -> Result<mcp_control_plane::PlanReviewSnapshot, PlanReviewError> {
        PlanReviewRenderer.render(
            &mut self.auth,
            &self.policy,
            &self.source,
            &mut self.registry,
            evidence,
            PlanReviewRenderRequest::new(
                &self.bearer,
                serde_json::to_vec(&arguments())
                    .map_err(|_| PlanReviewError::SerializationFailed)?,
                NOW,
            ),
        )
    }
}

fn arguments() -> Value {
    json!({
        "schema_version":"hwpx-agent.plan-review-render-request/v1",
        "client_surface":"codex_local",
        "locale":"ko-KR",
        "project_id":PROJECT,
        "source_revision_id":REVISION,
        "plan_id":PLAN
    })
}

#[derive(Clone, Copy, Debug)]
enum EvidenceMode {
    Valid,
    PolicyDenied,
    BlockingWarning,
    PartialDryRun,
    SignatureUnknown,
    WrongPlan,
}

#[derive(Debug)]
struct EvidenceRepository {
    before: DocumentGraph,
    after: DocumentGraph,
    mode: EvidenceMode,
    calls: usize,
}

impl EvidenceRepository {
    fn new(fixture: &Fixture, mode: EvidenceMode) -> Self {
        Self {
            before: fixture.before.clone(),
            after: fixture.after.clone(),
            mode,
            calls: 0,
        }
    }
}

impl PlanReviewEvidenceRepository for EvidenceRepository {
    fn load(
        &mut self,
        query: &PlanReviewEvidenceQuery<'_>,
    ) -> Result<PlanReviewEvidence, PlanReviewError> {
        self.calls += 1;
        let alternate_plan;
        let plan = if matches!(self.mode, EvidenceMode::WrongPlan) {
            alternate_plan = compile(&self.before, "plan_other001", "PRIVATE REPLACEMENT BODY")
                .map_err(|_| PlanReviewError::EvidenceUnavailable)?;
            &alternate_plan
        } else {
            query.plan()
        };
        let diff = semantic_summary(&self.before, &self.after)?;
        let route_set = route_set(plan, TARGET_PROFILE)?;
        let warnings = if matches!(self.mode, EvidenceMode::BlockingWarning) {
            vec![PlanReviewWarning::new(
                "LAYOUT_REVIEW_REQUIRED",
                PlanReviewWarningSeverity::Blocking,
                PlanReviewWarningKind::Layout,
            )?]
        } else {
            vec![]
        };
        let dry_run = PlanDryRunReceipt::new(
            plan,
            &route_set,
            &diff,
            if matches!(self.mode, EvidenceMode::PartialDryRun) {
                DryRunState::Partial
            } else {
                DryRunState::Verified
            },
            PlanReviewRisk::Low,
            EstimatedPageEffect::Local,
            warnings,
        )?;
        let signature = PlanSignatureReceipt::new(
            plan,
            &route_set,
            &diff,
            if matches!(self.mode, EvidenceMode::SignatureUnknown) {
                PlanReviewSignatureImpact::Unknown
            } else {
                PlanReviewSignatureImpact::None
            },
        )?;
        let policy = PlanExecutionPolicyReceipt::new(
            query,
            &route_set,
            &dry_run,
            &signature,
            !matches!(self.mode, EvidenceMode::PolicyDenied),
        )?;
        Ok(PlanReviewEvidence::new(
            route_set, diff, dry_run, signature, policy,
        ))
    }
}

fn semantic_summary(
    before: &DocumentGraph,
    after: &DocumentGraph,
) -> Result<SemanticDiffSummary, PlanReviewError> {
    let before_revision =
        RevisionId::parse(REVISION).map_err(|_| PlanReviewError::InvalidEvidence)?;
    let after_revision =
        RevisionId::parse("rev_candidate001").map_err(|_| PlanReviewError::InvalidEvidence)?;
    let before_digest = before
        .canonical_sha256()
        .map_err(|_| PlanReviewError::InvalidEvidence)?;
    let after_digest = after
        .canonical_sha256()
        .map_err(|_| PlanReviewError::InvalidEvidence)?;
    let diff = SemanticDiff::between(
        SemanticDiffSnapshot::new(&before_revision, before_digest, before)
            .map_err(|_| PlanReviewError::InvalidEvidence)?,
        SemanticDiffSnapshot::new(&after_revision, after_digest, after)
            .map_err(|_| PlanReviewError::InvalidEvidence)?,
        SemanticDiffLimits::default(),
    )
    .map_err(|_| PlanReviewError::InvalidEvidence)?;
    SemanticDiffSummary::from_diff(&diff, before, after, SemanticSummaryLimits::default())
        .map_err(|_| PlanReviewError::InvalidEvidence)
}

fn route_set(
    plan: &CompiledOperationPlan,
    target_profile_id: &str,
) -> Result<PlanReviewRouteSet, PlanReviewError> {
    let backend_id =
        BackendId::parse("hangul-2020").map_err(|_| PlanReviewError::InvalidEvidence)?;
    let target = ExactTargetProfile::new(
        TargetProfileId::parse(target_profile_id).map_err(|_| PlanReviewError::InvalidEvidence)?,
        "11.0.0.9136",
        Architecture::X86,
    )
    .map_err(|_| PlanReviewError::InvalidEvidence)?;
    let binding = RouteBinding::new(
        CapabilityId::parse("text.replace").map_err(|_| PlanReviewError::InvalidEvidence)?,
        backend_id.clone(),
        BackendKind::DesktopAutomation,
        SupportState::Verified,
        target.clone(),
        REGISTRY_DIGEST,
        REGISTRY_SEQUENCE,
        10,
        10,
        PreservationImpact::Exact,
        DomainSignatureImpact::Preserved,
    );
    let catalog = CapabilityRouteCatalog::from_bindings(vec![binding])
        .map_err(|_| PlanReviewError::InvalidEvidence)?;
    let context = RouteContext::new(
        target.clone(),
        REGISTRY_DIGEST,
        REGISTRY_SEQUENCE,
        RegistryTrustState::SignatureVerified,
        PolicyScope::CurrentPcPersonalLocalDevelopment,
        PreservationRequirement::Exact,
        ProtectionState::Unprotected,
        NOW_MS,
        vec![BackendHealth::new(
            backend_id,
            BackendHealthState::Healthy,
            3,
            NOW_MS - 100,
            60_000,
        )],
    )
    .map_err(|_| PlanReviewError::InvalidEvidence)?;
    let router = CapabilityRouter::new(CapabilityRouterLimits::default())
        .map_err(|_| PlanReviewError::InvalidEvidence)?;
    let decisions = plan
        .operations()
        .iter()
        .map(|operation| {
            router
                .route(operation, &context, &catalog)
                .map_err(|_| PlanReviewError::InvalidEvidence)
        })
        .collect::<Result<Vec<_>, _>>()?;
    PlanReviewRouteSet::from_decisions(plan, &target, decisions)
}

#[test]
fn authorized_exact_receipts_render_the_closed_content_free_snapshot() -> TestResult {
    let mut fixture = Fixture::new()?;
    let mut evidence = EvidenceRepository::new(&fixture, EvidenceMode::Valid);
    let snapshot = fixture.render(&mut evidence)?;
    assert!(snapshot.execution_allowed());
    assert_eq!(evidence.calls, 1);
    let value = snapshot.structured_content()?;
    let expected_keys = BTreeSet::from([
        "schema_version",
        "client_surface",
        "locale",
        "project_id",
        "source_revision_id",
        "plan_id",
        "risk_level",
        "estimated_page_effect",
        "route",
        "route_digest",
        "diff",
        "warnings",
        "signature_impact",
        "dry_run_state",
        "execution_allowed",
    ]);
    let actual_keys = value
        .as_object()
        .map(|object| object.keys().map(String::as_str).collect::<BTreeSet<_>>());
    assert_eq!(actual_keys, Some(expected_keys));
    assert_eq!(value["schema_version"], "hwpx-agent.plan-review/v1");
    assert_eq!(value["route"][0]["capability_id"], "text.replace");
    assert_eq!(value["route"][0]["selected_backend"], "hancom_2020");
    assert_eq!(value["route"][0]["support_level"], "verified");
    assert_eq!(value["route"][0]["supported"], true);
    assert_eq!(value["diff"]["modified"], 1);
    assert_eq!(value["dry_run_state"], "verified");
    assert_eq!(value["signature_impact"], "none");
    assert_eq!(value["execution_allowed"], true);
    assert_eq!(value["route_digest"].as_str().map(str::len), Some(64));
    let serialized = serde_json::to_string(&value)?;
    for secret in [
        "PRIVATE SOURCE BODY",
        "PRIVATE REPLACEMENT BODY",
        fixture.bearer.as_str(),
        "11.0.0.9136",
    ] {
        assert!(!serialized.contains(secret));
    }
    Ok(())
}

#[test]
fn authentication_and_strict_input_fail_before_evidence_loading() -> TestResult {
    let mut fixture = Fixture::new()?;
    let mut evidence = EvidenceRepository::new(&fixture, EvidenceMode::Valid);
    let bad_auth = PlanReviewRenderer.render(
        &mut fixture.auth,
        &fixture.policy,
        &fixture.source,
        &mut fixture.registry,
        &mut evidence,
        PlanReviewRenderRequest::new("Bearer invalid", serde_json::to_vec(&arguments())?, NOW),
    );
    assert_eq!(
        bad_auth.err(),
        Some(PlanReviewError::StoredPlan(
            StoredPlanError::Unauthenticated
        ))
    );
    let mut unknown = arguments();
    unknown["document_body"] = json!("PRIVATE SOURCE BODY");
    let bad_input = PlanReviewRenderer.render(
        &mut fixture.auth,
        &fixture.policy,
        &fixture.source,
        &mut fixture.registry,
        &mut evidence,
        PlanReviewRenderRequest::new(&fixture.bearer, serde_json::to_vec(&unknown)?, NOW),
    );
    assert_eq!(
        bad_input.err(),
        Some(PlanReviewError::StoredPlan(StoredPlanError::InvalidRequest))
    );
    assert_eq!(evidence.calls, 0);
    Ok(())
}

#[test]
fn current_source_acl_is_rechecked_before_evidence_loading() -> TestResult {
    let mut fixture = Fixture::new()?;
    let mut evidence = EvidenceRepository::new(&fixture, EvidenceMode::Valid);
    fixture.source.deny = true;
    assert_eq!(
        fixture.render(&mut evidence).err(),
        Some(PlanReviewError::StoredPlan(StoredPlanError::NotFound))
    );
    assert_eq!(evidence.calls, 0);
    Ok(())
}

#[test]
fn every_execution_guard_is_server_derived_and_fail_closed() -> TestResult {
    for mode in [
        EvidenceMode::PolicyDenied,
        EvidenceMode::BlockingWarning,
        EvidenceMode::PartialDryRun,
        EvidenceMode::SignatureUnknown,
    ] {
        let mut fixture = Fixture::new()?;
        let mut evidence = EvidenceRepository::new(&fixture, mode);
        let snapshot = fixture.render(&mut evidence)?;
        assert!(!snapshot.execution_allowed(), "mode {mode:?}");
        assert_eq!(
            snapshot.structured_content()?["execution_allowed"],
            false,
            "mode {mode:?}"
        );
    }
    Ok(())
}

#[test]
fn evidence_for_another_compiled_plan_is_rejected() -> TestResult {
    let mut fixture = Fixture::new()?;
    let mut evidence = EvidenceRepository::new(&fixture, EvidenceMode::WrongPlan);
    assert_eq!(
        fixture.render(&mut evidence).err(),
        Some(PlanReviewError::InvalidEvidence)
    );
    assert_eq!(evidence.calls, 1);
    Ok(())
}

#[test]
fn route_receipts_require_the_exact_current_hangul_2020_profile() -> TestResult {
    let fixture = Fixture::new()?;
    let plan = compile(&fixture.before, PLAN, "PRIVATE REPLACEMENT BODY")?;
    assert_eq!(
        route_set(&plan, "hangul-2022-secondary").err(),
        Some(PlanReviewError::InvalidEvidence)
    );
    assert_eq!(
        PlanReviewRouteSet::from_decisions(
            &plan,
            &ExactTargetProfile::new(
                TargetProfileId::parse(TARGET_PROFILE)?,
                "11.0.0.9136",
                Architecture::X86,
            )?,
            vec![],
        )
        .err(),
        Some(PlanReviewError::InvalidEvidence)
    );
    let valid_routes = route_set(&plan, TARGET_PROFILE)?;
    for target in [
        ExactTargetProfile::new(
            TargetProfileId::parse(TARGET_PROFILE)?,
            "11.0.0.9999",
            Architecture::X86,
        )?,
        ExactTargetProfile::new(
            TargetProfileId::parse(TARGET_PROFILE)?,
            "11.0.0.9136",
            Architecture::X86_64,
        )?,
    ] {
        assert_eq!(
            PlanReviewRouteSet::from_decisions(&plan, &target, valid_routes.decisions().to_vec(),)
                .err(),
            Some(PlanReviewError::InvalidEvidence)
        );
    }
    let two_operation_plan = compile_operations(
        &fixture.before,
        "plan_two_operations",
        "PRIVATE REPLACEMENT BODY",
        2,
    )?;
    let ordered = route_set(&two_operation_plan, TARGET_PROFILE)?;
    let mut reordered = ordered.decisions().to_vec();
    reordered.reverse();
    let exact_target = ExactTargetProfile::new(
        TargetProfileId::parse(TARGET_PROFILE)?,
        "11.0.0.9136",
        Architecture::X86,
    )?;
    assert_eq!(
        PlanReviewRouteSet::from_decisions(&two_operation_plan, &exact_target, reordered).err(),
        Some(PlanReviewError::InvalidEvidence)
    );
    Ok(())
}

#[test]
fn warnings_are_bounded_deduplicated_and_content_free() -> TestResult {
    assert_eq!(
        PlanReviewWarning::new(
            "contains private prose",
            PlanReviewWarningSeverity::Warning,
            PlanReviewWarningKind::Other,
        )
        .err(),
        Some(PlanReviewError::InvalidEvidence)
    );
    let fixture = Fixture::new()?;
    let plan = compile(&fixture.before, PLAN, "PRIVATE REPLACEMENT BODY")?;
    let routes = route_set(&plan, TARGET_PROFILE)?;
    let diff = semantic_summary(&fixture.before, &fixture.after)?;
    let duplicate = PlanReviewWarning::new(
        "LAYOUT_REVIEW_REQUIRED",
        PlanReviewWarningSeverity::Warning,
        PlanReviewWarningKind::Layout,
    )?;
    assert_eq!(
        PlanDryRunReceipt::new(
            &plan,
            &routes,
            &diff,
            DryRunState::Verified,
            PlanReviewRisk::Low,
            EstimatedPageEffect::Local,
            vec![duplicate.clone(), duplicate],
        )
        .err(),
        Some(PlanReviewError::InvalidEvidence)
    );
    let too_many = (0..9)
        .map(|index| {
            PlanReviewWarning::new(
                format!("WARNING_CODE_{index}"),
                PlanReviewWarningSeverity::Notice,
                PlanReviewWarningKind::Validation,
            )
        })
        .collect::<Result<Vec<_>, _>>()?;
    assert_eq!(
        PlanDryRunReceipt::new(
            &plan,
            &routes,
            &diff,
            DryRunState::Verified,
            PlanReviewRisk::Low,
            EstimatedPageEffect::Local,
            too_many,
        )
        .err(),
        Some(PlanReviewError::LimitExceeded)
    );
    Ok(())
}

#[test]
fn debug_output_redacts_requests_queries_receipts_and_snapshots() -> TestResult {
    let mut fixture = Fixture::new()?;
    let mut evidence = EvidenceRepository::new(&fixture, EvidenceMode::Valid);
    let request =
        PlanReviewRenderRequest::new(&fixture.bearer, serde_json::to_vec(&arguments())?, NOW);
    let request_debug = format!("{request:?}");
    assert!(!request_debug.contains(&fixture.bearer));
    let snapshot = PlanReviewRenderer.render(
        &mut fixture.auth,
        &fixture.policy,
        &fixture.source,
        &mut fixture.registry,
        &mut evidence,
        request,
    )?;
    let snapshot_debug = format!("{snapshot:?}");
    assert!(!snapshot_debug.contains(PROJECT));
    assert!(!snapshot_debug.contains(PLAN));
    assert!(!snapshot_debug.contains("PRIVATE"));
    Ok(())
}
