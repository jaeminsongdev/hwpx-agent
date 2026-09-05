use std::collections::BTreeMap;
use std::error::Error;

use domain_ir::{
    Architecture, BackendHealth, BackendHealthState, BackendId, BackendKind, CapabilityCatalog,
    CapabilityDefinitionDraft, CapabilityId, CapabilityRouteCatalog, CapabilityRouter,
    CapabilityRouterError, CapabilityRouterLimits, CompiledOperationPlan, DocumentGraph,
    DocumentGraphDraft, DocumentGraphLimits, DocumentId, ExactTargetProfile, Flow, Inline,
    LogicalId, Node, NodeCommon, OperationDraft, OperationId, OperationPlanCompiler,
    OperationPlanDraft, OperationPlanLimits, ParagraphNode, PlanId, PolicyScope,
    PreservationImpact, PreservationRequirement, Properties, ProtectionState, RegistryTrustState,
    RevisionId, RouteBinding, RouteContext, RouteRestriction, Section, Selector, SelectorDraft,
    SelectorLimits, SelectorSnapshot, SignatureImpact, SupportState, TargetProfileId,
};

type TestResult = Result<(), Box<dyn Error>>;

const NOW_MS: u64 = 1_000_000;
const REGISTRY_DIGEST: [u8; 32] = [7; 32];
const REGISTRY_SEQUENCE: u64 = 42;

#[test]
fn chooses_one_verified_exact_healthy_route_and_emits_stable_receipt() -> TestResult {
    let plan = compiled_plan()?;
    let direct = binding_kind("direct", BackendKind::DirectHwpx, 20, 20)?;
    let hybrid = binding_kind("hybrid", BackendKind::Hybrid, 15, 15)?;
    let automation = binding_kind("automation", BackendKind::DesktopAutomation, 10, 5)?;
    let catalog = CapabilityRouteCatalog::from_bindings(vec![automation, hybrid, direct])?;
    let context = context(
        PolicyScope::CurrentPcPersonalLocalDevelopment,
        PreservationRequirement::Exact,
        ProtectionState::Unprotected,
        vec![
            healthy("direct")?,
            healthy("hybrid")?,
            healthy("automation")?,
        ],
    )?;
    let router = router()?;
    let first = router.route(&plan.operations()[0], &context, &catalog)?;
    let second = router.route(&plan.operations()[0], &context, &catalog)?;
    assert_eq!(first.backend_id().as_str(), "direct");
    assert_eq!(first.backend_kind(), BackendKind::DirectHwpx);
    assert_eq!(first.health_generation(), 3);
    assert_eq!(first.canonical_json()?, second.canonical_json()?);
    assert_eq!(first.canonical_sha256()?, second.canonical_sha256()?);
    let canonical = first.canonical_json()?;
    assert_eq!(
        domain_ir::RouteDecision::from_canonical_json(&canonical)?,
        first
    );
    let mut noncanonical = canonical.clone();
    noncanonical.push(b'\n');
    assert_error(
        domain_ir::RouteDecision::from_canonical_json(&noncanonical),
        "capability_router_invalid_route_receipt",
    );
    let mut drifted: serde_json::Value = serde_json::from_slice(&canonical)?;
    drifted["health_generation"] = serde_json::json!(0);
    assert_error(
        domain_ir::RouteDecision::from_canonical_json(&serde_json::to_vec(&drifted)?),
        "capability_router_invalid_route_receipt",
    );
    Ok(())
}

#[test]
fn exact_profile_id_build_and_architecture_are_all_required() -> TestResult {
    let plan = compiled_plan()?;
    let context = standard_context("direct")?;
    let cases = [
        ExactTargetProfile::new(
            profile_id("other-profile")?,
            "2020.0.1",
            Architecture::X86_64,
        )?,
        ExactTargetProfile::new(
            profile_id("hangul-2020-current")?,
            "2020.0.2",
            Architecture::X86_64,
        )?,
        ExactTargetProfile::new(
            profile_id("hangul-2020-current")?,
            "2020.0.1",
            Architecture::X86,
        )?,
    ];
    for target in cases {
        let catalog = CapabilityRouteCatalog::from_bindings(vec![binding_for(
            "direct",
            target,
            REGISTRY_DIGEST,
            REGISTRY_SEQUENCE,
            SupportState::Verified,
        )?])?;
        assert_error(
            router()?.route(&plan.operations()[0], &context, &catalog),
            "capability_router_target_profile_mismatch",
        );
    }
    assert_error(
        ExactTargetProfile::new(profile_id("profile")?, "bad build value", Architecture::X86),
        "capability_router_invalid_target_profile",
    );
    Ok(())
}

#[test]
fn registry_digest_sequence_and_duplicate_binding_fail_closed() -> TestResult {
    let plan = compiled_plan()?;
    let context = standard_context("direct")?;
    for (digest, sequence) in [([8; 32], REGISTRY_SEQUENCE), (REGISTRY_DIGEST, 43)] {
        let catalog = CapabilityRouteCatalog::from_bindings(vec![binding_for(
            "direct",
            target_profile()?,
            digest,
            sequence,
            SupportState::Verified,
        )?])?;
        assert_error(
            router()?.route(&plan.operations()[0], &context, &catalog),
            "capability_router_registry_mismatch",
        );
    }
    let exact = binding("direct", 10, 10)?;
    assert_error(
        CapabilityRouteCatalog::from_bindings(vec![exact.clone(), exact]),
        "capability_router_duplicate_binding",
    );
    assert_error(
        CapabilityRouteCatalog::from_bindings(vec![binding_for(
            "direct",
            target_profile()?,
            [0; 32],
            REGISTRY_SEQUENCE,
            SupportState::Verified,
        )?]),
        "capability_router_invalid_registry_evidence",
    );
    assert_error(
        RouteContext::new(
            target_profile()?,
            REGISTRY_DIGEST,
            REGISTRY_SEQUENCE,
            RegistryTrustState::Unverified,
            PolicyScope::CurrentPcPersonalLocalDevelopment,
            PreservationRequirement::Exact,
            ProtectionState::Unprotected,
            NOW_MS,
            vec![healthy("direct")?],
        ),
        "capability_router_invalid_registry_evidence",
    );
    Ok(())
}

#[test]
fn only_verified_support_evidence_is_routable() -> TestResult {
    let plan = compiled_plan()?;
    let context = standard_context("direct")?;
    for state in [
        SupportState::CandidateUnverified,
        SupportState::Unavailable,
        SupportState::Failed,
        SupportState::RiskBlocked,
        SupportState::NotRun,
    ] {
        let catalog = CapabilityRouteCatalog::from_bindings(vec![binding_for(
            "direct",
            target_profile()?,
            REGISTRY_DIGEST,
            REGISTRY_SEQUENCE,
            state,
        )?])?;
        assert_error(
            router()?.route(&plan.operations()[0], &context, &catalog),
            "capability_router_support_unavailable",
        );
    }
    Ok(())
}

#[test]
fn production_provider_unsafe_network_and_confirmation_policies_are_denied() -> TestResult {
    let plan = compiled_plan()?;
    let catalog = CapabilityRouteCatalog::from_bindings(vec![binding("direct", 10, 10)?])?;
    for scope in [PolicyScope::Production, PolicyScope::ExternalProvider] {
        let context = context(
            scope,
            PreservationRequirement::Exact,
            ProtectionState::Unprotected,
            vec![healthy("direct")?],
        )?;
        assert_error(
            router()?.route(&plan.operations()[0], &context, &catalog),
            "capability_router_policy_denied",
        );
    }
    for restriction in [
        RouteRestriction::RequiresNetwork,
        RouteRestriction::RequiresExternalProvider,
        RouteRestriction::UnsafeAction,
    ] {
        let restricted = binding("direct", 10, 10)?.with_restriction(restriction);
        let restricted_catalog = CapabilityRouteCatalog::from_bindings(vec![restricted])?;
        assert_error(
            router()?.route(
                &plan.operations()[0],
                &standard_context("direct")?,
                &restricted_catalog,
            ),
            "capability_router_policy_denied",
        );
    }
    let confirmation = CapabilityRouteCatalog::from_bindings(vec![
        binding("direct", 10, 10)?.with_restriction(RouteRestriction::ConfirmationRequired),
    ])?;
    assert_error(
        router()?.route(
            &plan.operations()[0],
            &standard_context("direct")?,
            &confirmation,
        ),
        "capability_router_confirmation_required",
    );
    let protected = context(
        PolicyScope::CurrentPcPersonalLocalDevelopment,
        PreservationRequirement::Exact,
        ProtectionState::Protected,
        vec![healthy("direct")?],
    )?;
    assert_error(
        router()?.route(&plan.operations()[0], &protected, &catalog),
        "capability_router_confirmation_required",
    );
    Ok(())
}

#[test]
fn preservation_strength_opaque_loss_and_signature_impact_are_enforced() -> TestResult {
    let plan = compiled_plan()?;
    let surgical = RouteBinding::new(
        capability_id("edit.noop")?,
        backend_id("direct")?,
        BackendKind::DirectHwpx,
        SupportState::Verified,
        target_profile()?,
        REGISTRY_DIGEST,
        REGISTRY_SEQUENCE,
        10,
        10,
        PreservationImpact::Surgical,
        SignatureImpact::Preserved,
    );
    let catalog = CapabilityRouteCatalog::from_bindings(vec![surgical])?;
    assert_error(
        router()?.route(
            &plan.operations()[0],
            &standard_context("direct")?,
            &catalog,
        ),
        "capability_router_preservation_denied",
    );
    let surgical_context = context(
        PolicyScope::CurrentPcPersonalLocalDevelopment,
        PreservationRequirement::Surgical,
        ProtectionState::Unprotected,
        vec![healthy("direct")?],
    )?;
    assert!(
        router()?
            .route(&plan.operations()[0], &surgical_context, &catalog)
            .is_ok()
    );

    for (impact, signature, protection) in [
        (
            PreservationImpact::OpaqueLoss,
            SignatureImpact::Preserved,
            ProtectionState::Unprotected,
        ),
        (
            PreservationImpact::Exact,
            SignatureImpact::Invalidated,
            ProtectionState::Signed,
        ),
        (
            PreservationImpact::Exact,
            SignatureImpact::Unknown,
            ProtectionState::Signed,
        ),
    ] {
        let candidate = RouteBinding::new(
            capability_id("edit.noop")?,
            backend_id("direct")?,
            BackendKind::DirectHwpx,
            SupportState::Verified,
            target_profile()?,
            REGISTRY_DIGEST,
            REGISTRY_SEQUENCE,
            10,
            10,
            impact,
            signature,
        );
        let catalog = CapabilityRouteCatalog::from_bindings(vec![candidate])?;
        let context = context(
            PolicyScope::CurrentPcPersonalLocalDevelopment,
            PreservationRequirement::Normalized,
            protection,
            vec![healthy("direct")?],
        )?;
        assert_error(
            router()?.route(&plan.operations()[0], &context, &catalog),
            "capability_router_preservation_denied",
        );
    }
    Ok(())
}

#[test]
fn health_generation_ttl_and_degraded_opt_in_are_exact() -> TestResult {
    let plan = compiled_plan()?;
    let base_catalog = CapabilityRouteCatalog::from_bindings(vec![binding("direct", 10, 10)?])?;
    for health in [
        health("direct", BackendHealthState::Degraded, 3, NOW_MS - 10, 100)?,
        health("direct", BackendHealthState::Unhealthy, 3, NOW_MS - 10, 100)?,
        health("direct", BackendHealthState::Unknown, 3, NOW_MS - 10, 100)?,
        health("direct", BackendHealthState::Healthy, 3, NOW_MS - 101, 100)?,
        health("direct", BackendHealthState::Healthy, 3, NOW_MS + 1, 100)?,
        health("direct", BackendHealthState::Healthy, 0, NOW_MS - 10, 100)?,
        health("direct", BackendHealthState::Healthy, 3, NOW_MS - 10, 0)?,
        health(
            "direct",
            BackendHealthState::Healthy,
            3,
            NOW_MS - 10,
            CapabilityRouterLimits::default().max_health_ttl_ms + 1,
        )?,
    ] {
        let context = context(
            PolicyScope::CurrentPcPersonalLocalDevelopment,
            PreservationRequirement::Exact,
            ProtectionState::Unprotected,
            vec![health],
        )?;
        assert_error(
            router()?.route(&plan.operations()[0], &context, &base_catalog),
            "capability_router_health_unavailable",
        );
    }

    let degraded_catalog = CapabilityRouteCatalog::from_bindings(vec![
        binding("direct", 10, 10)?.with_degraded_health(true),
    ])?;
    let degraded_context = context(
        PolicyScope::CurrentPcPersonalLocalDevelopment,
        PreservationRequirement::Exact,
        ProtectionState::Unprotected,
        vec![health(
            "direct",
            BackendHealthState::Degraded,
            4,
            NOW_MS,
            100,
        )?],
    )?;
    assert_eq!(
        router()?
            .route(&plan.operations()[0], &degraded_context, &degraded_catalog,)?
            .health_generation(),
        4
    );
    assert_error(
        context(
            PolicyScope::CurrentPcPersonalLocalDevelopment,
            PreservationRequirement::Exact,
            ProtectionState::Unprotected,
            vec![healthy("direct")?, healthy("direct")?],
        ),
        "capability_router_duplicate_health_evidence",
    );
    Ok(())
}

#[test]
fn ranking_never_weakens_filters_and_equal_top_routes_are_ambiguous() -> TestResult {
    let plan = compiled_plan()?;
    let unverified = binding_for(
        "fast-unverified",
        target_profile()?,
        REGISTRY_DIGEST,
        REGISTRY_SEQUENCE,
        SupportState::CandidateUnverified,
    )?;
    let verified = binding("verified", 10, 50)?;
    let catalog = CapabilityRouteCatalog::from_bindings(vec![unverified, verified])?;
    let route_context = context(
        PolicyScope::CurrentPcPersonalLocalDevelopment,
        PreservationRequirement::Exact,
        ProtectionState::Unprotected,
        vec![healthy("fast-unverified")?, healthy("verified")?],
    )?;
    assert_eq!(
        router()?
            .route(&plan.operations()[0], &route_context, &catalog)?
            .backend_id()
            .as_str(),
        "verified"
    );

    let tied = CapabilityRouteCatalog::from_bindings(vec![
        binding("alpha", 20, 5)?,
        binding("omega", 20, 5)?,
    ])?;
    let tied_context = context(
        PolicyScope::CurrentPcPersonalLocalDevelopment,
        PreservationRequirement::Exact,
        ProtectionState::Unprotected,
        vec![healthy("omega")?, healthy("alpha")?],
    )?;
    assert_error(
        router()?.route(&plan.operations()[0], &tied_context, &tied),
        "capability_router_ambiguous_route",
    );
    Ok(())
}

#[test]
fn finite_limits_missing_capability_order_independence_and_debug_redaction_hold() -> TestResult {
    assert_error(
        CapabilityRouter::new(CapabilityRouterLimits {
            max_bindings_considered: 0,
            ..CapabilityRouterLimits::default()
        }),
        "capability_router_invalid_limit",
    );
    let plan = compiled_plan()?;
    let missing = CapabilityRouteCatalog::from_bindings(vec![RouteBinding::new(
        capability_id("different")?,
        backend_id("private-backend")?,
        BackendKind::DirectHwpx,
        SupportState::Verified,
        target_profile()?,
        REGISTRY_DIGEST,
        REGISTRY_SEQUENCE,
        10,
        10,
        PreservationImpact::Exact,
        SignatureImpact::Preserved,
    )])?;
    assert_error(
        router()?.route(
            &plan.operations()[0],
            &standard_context("private-backend")?,
            &missing,
        ),
        "capability_router_capability_not_found",
    );

    let limited = CapabilityRouter::new(CapabilityRouterLimits {
        max_bindings_considered: 1,
        ..CapabilityRouterLimits::default()
    })?;
    let oversized = CapabilityRouteCatalog::from_bindings(vec![
        binding("private-alpha", 20, 10)?,
        binding("private-beta", 10, 10)?,
    ])?;
    assert_error(
        limited.route(
            &plan.operations()[0],
            &context(
                PolicyScope::CurrentPcPersonalLocalDevelopment,
                PreservationRequirement::Exact,
                ProtectionState::Unprotected,
                vec![healthy("private-alpha")?, healthy("private-beta")?],
            )?,
            &oversized,
        ),
        "capability_router_limit_exceeded",
    );

    let first_catalog = CapabilityRouteCatalog::from_bindings(vec![
        binding("private-low", 10, 10)?,
        binding("private-high", 20, 10)?,
    ])?;
    let second_catalog = CapabilityRouteCatalog::from_bindings(vec![
        binding("private-high", 20, 10)?,
        binding("private-low", 10, 10)?,
    ])?;
    let first_context = context(
        PolicyScope::CurrentPcPersonalLocalDevelopment,
        PreservationRequirement::Exact,
        ProtectionState::Unprotected,
        vec![healthy("private-low")?, healthy("private-high")?],
    )?;
    let second_context = context(
        PolicyScope::CurrentPcPersonalLocalDevelopment,
        PreservationRequirement::Exact,
        ProtectionState::Unprotected,
        vec![healthy("private-high")?, healthy("private-low")?],
    )?;
    let first = router()?.route(&plan.operations()[0], &first_context, &first_catalog)?;
    let second = router()?.route(&plan.operations()[0], &second_context, &second_catalog)?;
    assert_eq!(first.canonical_json()?, second.canonical_json()?);
    for rendered in [
        format!("{first:?}"),
        format!("{first_context:?}"),
        format!("{:?}", binding("private-high", 20, 10)?),
    ] {
        assert!(!rendered.contains("private-high"));
        assert!(!rendered.contains("hangul-2020-current"));
        assert!(!rendered.contains("2020.0.1"));
    }
    Ok(())
}

fn router() -> Result<CapabilityRouter, CapabilityRouterError> {
    CapabilityRouter::new(CapabilityRouterLimits::default())
}

fn assert_error<T>(result: Result<T, CapabilityRouterError>, expected: &str) {
    assert_eq!(
        result.err().map(CapabilityRouterError::code),
        Some(expected)
    );
}

fn binding(backend: &str, priority: u16, cost: u32) -> Result<RouteBinding, Box<dyn Error>> {
    binding_kind(backend, BackendKind::DirectHwpx, priority, cost)
}

fn binding_kind(
    backend: &str,
    kind: BackendKind,
    priority: u16,
    cost: u32,
) -> Result<RouteBinding, Box<dyn Error>> {
    Ok(RouteBinding::new(
        capability_id("edit.noop")?,
        backend_id(backend)?,
        kind,
        SupportState::Verified,
        target_profile()?,
        REGISTRY_DIGEST,
        REGISTRY_SEQUENCE,
        priority,
        cost,
        PreservationImpact::Exact,
        SignatureImpact::Preserved,
    ))
}

fn binding_for(
    backend: &str,
    profile: ExactTargetProfile,
    digest: [u8; 32],
    sequence: u64,
    support: SupportState,
) -> Result<RouteBinding, Box<dyn Error>> {
    Ok(RouteBinding::new(
        capability_id("edit.noop")?,
        backend_id(backend)?,
        BackendKind::DirectHwpx,
        support,
        profile,
        digest,
        sequence,
        10,
        10,
        PreservationImpact::Exact,
        SignatureImpact::Preserved,
    ))
}

fn context(
    scope: PolicyScope,
    preservation: PreservationRequirement,
    protection: ProtectionState,
    health: Vec<BackendHealth>,
) -> Result<RouteContext, CapabilityRouterError> {
    RouteContext::new(
        target_profile().map_err(|_| CapabilityRouterError::InvalidTargetProfile)?,
        REGISTRY_DIGEST,
        REGISTRY_SEQUENCE,
        RegistryTrustState::SignatureVerified,
        scope,
        preservation,
        protection,
        NOW_MS,
        health,
    )
}

fn standard_context(backend: &str) -> Result<RouteContext, Box<dyn Error>> {
    Ok(context(
        PolicyScope::CurrentPcPersonalLocalDevelopment,
        PreservationRequirement::Exact,
        ProtectionState::Unprotected,
        vec![healthy(backend)?],
    )?)
}

fn healthy(backend: &str) -> Result<BackendHealth, domain_ir::IdentityError> {
    health(backend, BackendHealthState::Healthy, 3, NOW_MS - 100, 500)
}

fn health(
    backend: &str,
    state: BackendHealthState,
    generation: u64,
    observed_at: u64,
    ttl: u64,
) -> Result<BackendHealth, domain_ir::IdentityError> {
    Ok(BackendHealth::new(
        backend_id(backend)?,
        state,
        generation,
        observed_at,
        ttl,
    ))
}

fn target_profile() -> Result<ExactTargetProfile, Box<dyn Error>> {
    Ok(ExactTargetProfile::new(
        profile_id("hangul-2020-current")?,
        "2020.0.1",
        Architecture::X86_64,
    )?)
}

fn compiled_plan() -> Result<CompiledOperationPlan, Box<dyn Error>> {
    let draft = DocumentGraphDraft::new(
        DocumentId::parse("router-document")?,
        vec![Section {
            section_id: LogicalId::parse("section-1")?,
            properties: Properties::new(),
            master_pages: Vec::new(),
            headers_footers: Vec::new(),
            body: Flow {
                children: vec![Node::Paragraph(ParagraphNode {
                    common: NodeCommon::new(LogicalId::parse("p-1")?),
                    inlines: vec![Inline::Text {
                        text: "synthetic router target".into(),
                    }],
                    paragraph_properties: Properties::new(),
                })],
            },
        }],
    );
    let graph = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())?;
    let revision = RevisionId::parse("revision-1")?;
    let snapshot = SelectorSnapshot::build(&graph, revision.clone(), SelectorLimits::default())?;
    let capability = capability_id("edit.noop")?;
    let catalog =
        CapabilityCatalog::from_drafts(vec![CapabilityDefinitionDraft::new(capability.clone())])?;
    OperationPlanCompiler::new(OperationPlanLimits::default())?
        .compile(
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
        )
        .map_err(Into::into)
}

fn backend_id(value: &str) -> Result<BackendId, domain_ir::IdentityError> {
    BackendId::parse(value)
}

fn capability_id(value: &str) -> Result<CapabilityId, domain_ir::IdentityError> {
    CapabilityId::parse(value)
}

fn profile_id(value: &str) -> Result<TargetProfileId, domain_ir::IdentityError> {
    TargetProfileId::parse(value)
}
