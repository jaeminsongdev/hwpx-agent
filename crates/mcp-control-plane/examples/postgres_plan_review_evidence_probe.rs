use std::collections::BTreeMap;
use std::env;
use std::error::Error;

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
    ExactTargetProfile, Flow, Inline, LogicalId, OperationDraft, OperationId,
    OperationPlanCompiler, OperationPlanDraft, OperationPlanLimits, ParagraphNode, PlanId,
    PolicyScope, PreservationImpact, PreservationRequirement, Properties, ProtectionState,
    RegistryTrustState, RevisionId, RouteBinding, RouteContext, Section, Selector, SelectorDraft,
    SelectorLimits, SelectorSnapshot, SemanticDiff, SemanticDiffLimits, SemanticDiffSnapshot,
    SemanticDiffSummary, SemanticSummaryLimits, SignatureImpact, SupportState, TargetProfileId,
};
use hmac::{Hmac, Mac as _};
use mcp_control_plane::{
    CompiledPlanSubmission, CurrentPlanSource, DryRunState, DurablePlanKeyring,
    DurablePlanReviewEvidenceKeyring, EstimatedPageEffect, InMemoryProjectPolicy,
    LocalPostgresPlanReviewEvidenceConfig, LocalPostgresPlanReviewEvidenceRepository,
    LocalPostgresStoredPlanConfig, LocalPostgresStoredPlanRegistry, PlanDryRunReceipt,
    PlanExecutionPolicyReceipt, PlanLookupRequest, PlanReviewError, PlanReviewEvidence,
    PlanReviewEvidenceQuery, PlanReviewRenderRequest, PlanReviewRenderer, PlanReviewRisk,
    PlanReviewRouteSet, PlanReviewSignatureImpact, PlanSignatureReceipt, PlanSourceRepository,
    ProjectAccess, ProjectPolicyLimits, StoredPlanError, StoredPlanLimits,
};
use serde_json::json;
use sha2::Sha256;
use uuid::Uuid;

type ProbeResult<T> = Result<T, Box<dyn Error>>;

const NOW: u64 = 2_000_000_000;
const NOW_MS: u64 = NOW * 1_000;
const TENANT: u128 = 1;
const PROJECT: &str = "prj_00000000000000000000000000000101";
const REVISION: &str = "rev_00000000000000000000000000000201";
const PLAN: &str = "plan_00000000000000000000000000000301";
const TARGET_PROFILE: &str = "hancom-hangul-2020-secondary";
const ISSUER: &str = "https://identity.hwpx-agent.example";
const RESOURCE: &str = "https://mcp.hwpx-agent.example";
const REGISTRY_DIGEST: [u8; 32] = [7; 32];
const REGISTRY_SEQUENCE: u64 = 42;
const TOKEN_KEY: &[u8] = b"0123456789abcdef0123456789abcdef";

fn environment(name: &str) -> ProbeResult<String> {
    let value = env::var(name)?;
    if value.is_empty() || value.len() > 2048 || value.contains('\0') {
        return Err("invalid environment".into());
    }
    Ok(value)
}

fn decode_key(name: &str) -> ProbeResult<[u8; 32]> {
    let text = environment(name)?;
    let mut key = [0_u8; 32];
    hex::decode_to_slice(text, &mut key)?;
    if key == [0; 32] {
        return Err("zero key".into());
    }
    Ok(key)
}

fn graph(text: &str) -> ProbeResult<DocumentGraph> {
    Ok(DocumentGraph::from_draft(
        DocumentGraphDraft::new(
            DocumentId::parse("private-document")?,
            vec![Section {
                section_id: LogicalId::parse("private-section")?,
                properties: Properties::new(),
                master_pages: vec![],
                headers_footers: vec![],
                body: Flow {
                    children: vec![domain_ir::Node::Paragraph(ParagraphNode {
                        common: domain_ir::NodeCommon::new(LogicalId::parse("private-paragraph")?),
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

fn compile(source: &DocumentGraph) -> ProbeResult<CompiledOperationPlan> {
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
    Ok(
        OperationPlanCompiler::new(OperationPlanLimits::default())?.compile(
            OperationPlanDraft::new(
                PlanId::parse(PLAN)?,
                revision,
                vec![OperationDraft {
                    operation_id: OperationId::parse("private-operation-0001")?,
                    capability_id,
                    selector: SelectorDraft::one(Selector::by_logical_id(LogicalId::parse(
                        "private-paragraph",
                    )?)),
                    arguments: BTreeMap::from([(
                        "text".to_owned(),
                        ArgumentDraft::Text("PRIVATE REPLACEMENT BODY".to_owned()),
                    )]),
                    depends_on: vec![],
                }],
            ),
            &catalog,
            &snapshot,
            &snapshot.expectation(),
        )?,
    )
}

fn token(tenant: TenantId) -> ProbeResult<String> {
    let header = URL_SAFE_NO_PAD.encode(serde_json::to_vec(
        &json!({"alg":"HS256","kid":"local-key-01","typ":"at+jwt"}),
    )?);
    let claims = URL_SAFE_NO_PAD.encode(serde_json::to_vec(&json!({
        "iss":ISSUER,"sub":"private-owner","aud":RESOURCE,"exp":NOW+3540,
        "nbf":NOW-60,"iat":NOW-60,"jti":"review-owner",
        "scope":"project.read project.write","token_kind":"user","tenant_id":tenant,
    }))?);
    let input = format!("{header}.{claims}");
    let mut signer = <Hmac<Sha256> as hmac::KeyInit>::new_from_slice(TOKEN_KEY)?;
    signer.update(input.as_bytes());
    Ok(format!(
        "Bearer {input}.{}",
        URL_SAFE_NO_PAD.encode(signer.finalize().into_bytes())
    ))
}

#[derive(Debug)]
struct Source {
    tenant: TenantId,
    subject: SubjectDigest,
    graph: DocumentGraph,
}

impl PlanSourceRepository for Source {
    fn current_source(
        &self,
        context: &AuthContext,
        project_id: &str,
    ) -> Result<CurrentPlanSource, StoredPlanError> {
        if context.tenant_id() != self.tenant
            || context.subject() != self.subject
            || project_id != PROJECT
        {
            return Err(StoredPlanError::NotFound);
        }
        CurrentPlanSource::from_graph(self.tenant, PROJECT, REVISION, &self.graph)
    }
}

struct Fixture {
    tenant: TenantId,
    auth: AuthMiddleware,
    policy: InMemoryProjectPolicy,
    source: Source,
    bearer: String,
    before: DocumentGraph,
    after: DocumentGraph,
    plan: CompiledOperationPlan,
}

fn fixture() -> ProbeResult<Fixture> {
    let tenant = TenantId::new(Uuid::from_u128(TENANT))?;
    let mut auth = AuthMiddleware::new(
        RESOURCE,
        format!("{RESOURCE}/.well-known/oauth-protected-resource"),
        60,
        AuthRegistryLimits::product_maximums(),
    )?;
    auth.register_local_hmac_key(ISSUER, "local-key-01", TOKEN_KEY, NOW - 600, NOW + 7200)?;
    let subject = auth.register_user(
        ISSUER,
        "private-owner",
        PrincipalGrant::new(
            tenant,
            TenantRole::Owner,
            [AuthScope::ProjectRead, AuthScope::ProjectWrite],
            NOW - 600,
            NOW + 7200,
        )?,
    )?;
    let mut policy = InMemoryProjectPolicy::new(ProjectPolicyLimits::product_maximums());
    policy.register_project(PROJECT, tenant)?;
    policy.register_membership(PROJECT, subject, ProjectAccess::Owner)?;
    let before = graph("PRIVATE SOURCE BODY")?;
    let after = graph("PRIVATE REPLACEMENT BODY")?;
    let plan = compile(&before)?;
    Ok(Fixture {
        tenant,
        auth,
        policy,
        source: Source {
            tenant,
            subject,
            graph: before.clone(),
        },
        bearer: token(tenant)?,
        before,
        after,
        plan,
    })
}

fn arguments() -> ProbeResult<Vec<u8>> {
    Ok(serde_json::to_vec(&json!({
        "schema_version":"hwpx-agent.plan-review-render-request/v1",
        "client_surface":"codex_local","locale":"ko-KR","project_id":PROJECT,
        "source_revision_id":REVISION,"plan_id":PLAN
    }))?)
}

fn lookup_request(bearer: &str) -> ProbeResult<PlanLookupRequest> {
    Ok(PlanLookupRequest::new(bearer, arguments()?, NOW))
}

fn route_set(plan: &CompiledOperationPlan) -> Result<PlanReviewRouteSet, PlanReviewError> {
    let backend = BackendId::parse("hangul-2020").map_err(|_| PlanReviewError::InvalidEvidence)?;
    let target = ExactTargetProfile::new(
        TargetProfileId::parse(TARGET_PROFILE).map_err(|_| PlanReviewError::InvalidEvidence)?,
        "11.0.0.9136",
        Architecture::X86,
    )
    .map_err(|_| PlanReviewError::InvalidEvidence)?;
    let binding = RouteBinding::new(
        CapabilityId::parse("text.replace").map_err(|_| PlanReviewError::InvalidEvidence)?,
        backend.clone(),
        BackendKind::DesktopAutomation,
        SupportState::Verified,
        target.clone(),
        REGISTRY_DIGEST,
        REGISTRY_SEQUENCE,
        10,
        10,
        PreservationImpact::Exact,
        SignatureImpact::Preserved,
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
            backend,
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

fn evidence(
    query: &PlanReviewEvidenceQuery<'_>,
    before: &DocumentGraph,
    after: &DocumentGraph,
) -> Result<PlanReviewEvidence, PlanReviewError> {
    let before_digest = before
        .canonical_sha256()
        .map_err(|_| PlanReviewError::InvalidEvidence)?;
    let after_digest = after
        .canonical_sha256()
        .map_err(|_| PlanReviewError::InvalidEvidence)?;
    let before_revision =
        RevisionId::parse(REVISION).map_err(|_| PlanReviewError::InvalidEvidence)?;
    let after_revision = RevisionId::parse("rev_candidate0000000000000000000000000001")
        .map_err(|_| PlanReviewError::InvalidEvidence)?;
    let diff = SemanticDiff::between(
        SemanticDiffSnapshot::new(&before_revision, before_digest, before)
            .map_err(|_| PlanReviewError::InvalidEvidence)?,
        SemanticDiffSnapshot::new(&after_revision, after_digest, after)
            .map_err(|_| PlanReviewError::InvalidEvidence)?,
        SemanticDiffLimits::default(),
    )
    .map_err(|_| PlanReviewError::InvalidEvidence)?;
    let summary =
        SemanticDiffSummary::from_diff(&diff, before, after, SemanticSummaryLimits::default())
            .map_err(|_| PlanReviewError::InvalidEvidence)?;
    let routes = route_set(query.plan())?;
    let dry_run = PlanDryRunReceipt::new(
        query.plan(),
        &routes,
        &summary,
        DryRunState::Verified,
        PlanReviewRisk::Low,
        EstimatedPageEffect::Local,
        vec![],
    )?;
    let signature = PlanSignatureReceipt::new(
        query.plan(),
        &routes,
        &summary,
        PlanReviewSignatureImpact::None,
    )?;
    let policy = PlanExecutionPolicyReceipt::new(query, &routes, &dry_run, &signature, true)?;
    Ok(PlanReviewEvidence::new(
        routes, summary, dry_run, signature, policy,
    ))
}

fn plan_keyring() -> ProbeResult<DurablePlanKeyring> {
    Ok(DurablePlanKeyring::new(
        "kms.plan-v1",
        [("kms.plan-v1".to_owned(), decode_key("HWPX_P16_PLAN_KEY")?)],
    )?)
}

fn evidence_keyring(mode: &str) -> ProbeResult<DurablePlanReviewEvidenceKeyring> {
    let v1 = decode_key("HWPX_P16_EVIDENCE_KEY_V1")?;
    let v2 = decode_key("HWPX_P16_EVIDENCE_KEY_V2")?;
    Ok(match mode {
        "seed" => DurablePlanReviewEvidenceKeyring::new(
            "kms.review-v1",
            [("kms.review-v1".to_owned(), v1)],
        )?,
        "wrong-key" => DurablePlanReviewEvidenceKeyring::new(
            "kms.review-v2",
            [("kms.review-v2".to_owned(), v2)],
        )?,
        _ => DurablePlanReviewEvidenceKeyring::new(
            "kms.review-v2",
            [
                ("kms.review-v1".to_owned(), v1),
                ("kms.review-v2".to_owned(), v2),
            ],
        )?,
    })
}

fn run(mode: &str) -> ProbeResult<()> {
    let mut fixture = fixture()?;
    if mode == "facts" {
        println!(
            "{}",
            serde_json::to_string(&json!({
                "owner_sha256":fixture.source.subject,
                "graph_sha256":hex::encode(fixture.before.canonical_sha256()?)
            }))?
        );
        return Ok(());
    }
    let port: u16 = environment("HWPX_P16_PG_PORT")?.parse()?;
    let database = environment("HWPX_P16_PG_DATABASE")?;
    let plan_user = environment("HWPX_P16_PLAN_PG_USER")?;
    let plan_password = environment("HWPX_P16_PLAN_PG_PASSWORD")?;
    let review_user = environment("HWPX_P16_REVIEW_PG_USER")?;
    let review_password = environment("HWPX_P16_REVIEW_PG_PASSWORD")?;
    let plan_config =
        LocalPostgresStoredPlanConfig::new(port, database.clone(), plan_user, plan_password)?;
    let evidence_config =
        LocalPostgresPlanReviewEvidenceConfig::new(port, database, review_user, review_password)?;
    let mut plans = LocalPostgresStoredPlanRegistry::connect(
        &plan_config,
        fixture.tenant,
        plan_keyring()?,
        StoredPlanLimits::product_maximums(),
    )?;
    let evidence_keys = evidence_keyring(mode)?;
    let mut repository = LocalPostgresPlanReviewEvidenceRepository::connect(
        &evidence_config,
        fixture.tenant,
        evidence_keys,
    )?;
    if mode == "seed" {
        plans.insert(
            &mut fixture.auth,
            &fixture.policy,
            &fixture.source,
            CompiledPlanSubmission::new(&fixture.bearer, PROJECT, fixture.plan, NOW),
        )?;
        let authorized = plans.lookup(
            &mut fixture.auth,
            &fixture.policy,
            &fixture.source,
            lookup_request(&fixture.bearer)?,
        )?;
        let query = PlanReviewEvidenceQuery::for_authorized(&authorized);
        let receipts = evidence(&query, &fixture.before, &fixture.after)?;
        repository.store(&authorized, &receipts, NOW)?;
    }
    let rendered = PlanReviewRenderer.render(
        &mut fixture.auth,
        &fixture.policy,
        &fixture.source,
        &mut plans,
        &mut repository,
        PlanReviewRenderRequest::new(&fixture.bearer, arguments()?, NOW),
    );
    if matches!(mode, "wrong-key" | "expect-unavailable") {
        if rendered.err() != Some(PlanReviewError::EvidenceUnavailable) {
            return Err("expected evidence unavailability".into());
        }
    } else {
        let snapshot = rendered?;
        if !snapshot.execution_allowed() {
            return Err("execution unexpectedly denied".into());
        }
        let public = serde_json::to_string(&snapshot.structured_content()?)?;
        for private in ["PRIVATE", "kms.review", "11.0.0.9136"] {
            if public.contains(private) {
                return Err("private output leak".into());
            }
        }
    }
    println!("P16_POSTGRES_PLAN_REVIEW_EVIDENCE_PROBE_PASS mode={mode}");
    Ok(())
}

fn main() {
    let mode = environment("HWPX_P16_PLAN_REVIEW_MODE");
    if let Err(error) = mode.and_then(|mode| run(&mode)) {
        eprintln!("P16_POSTGRES_PLAN_REVIEW_EVIDENCE_PROBE_FAILED category={error}");
        std::process::exit(1);
    }
}
