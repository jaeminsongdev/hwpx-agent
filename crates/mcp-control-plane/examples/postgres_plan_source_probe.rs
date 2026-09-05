//! Disposable `PostgreSQL` acceptance probe for the authoritative plan-source adapter.
//! It uses only a synthetic graph and emits closed markers without database diagnostics.

use std::collections::BTreeMap;
use std::error::Error;
use std::fmt;

use artifact_service::{SubjectDigest, TenantId};
use auth_middleware::{AuthMiddleware, AuthRegistryLimits, AuthScope, PrincipalGrant, TenantRole};
use base64::{Engine as _, engine::general_purpose::URL_SAFE_NO_PAD};
use domain_ir::{
    ArgumentDraft, ArgumentKind, ArgumentSpec, CapabilityCatalog, CapabilityDefinitionDraft,
    CapabilityId, CompiledOperationPlan, DefaultPolicy, DocumentGraph, DocumentGraphDraft,
    DocumentGraphLimits, DocumentId, Flow, Inline, LogicalId, Node, NodeCommon, OperationDraft,
    OperationId, OperationPlanCompiler, OperationPlanDraft, OperationPlanLimits, ParagraphNode,
    PlanId, Properties, RevisionId, Section, Selector, SelectorDraft, SelectorLimits,
    SelectorSnapshot,
};
use hmac::{Hmac, Mac as _};
use mcp_control_plane::{
    CompiledPlanSubmission, InMemoryProjectPolicy, LocalPostgresPlanSourceConfig,
    LocalPostgresPlanSourceRepository, PlanLookupRequest, PlanSourceConnectStage,
    PlanSourceRepository, ProjectAccess, ProjectPolicyLimits, StoredPlanError, StoredPlanLimits,
    StoredPlanRegistry,
};
use serde_json::json;
use sha2::Sha256;
use uuid::Uuid;

const NOW: u64 = 2_000_000_000;
const TENANT: u128 = 1;
const PROJECT: &str = "prj_00000000000000000000000000000101";
const REVISION: &str = "rev_00000000000000000000000000000201";
const PLAN: &str = "plan_00000000000000000000000000000301";
const ISSUER: &str = "https://identity.hwpx-agent.example";
const RESOURCE: &str = "https://mcp.hwpx-agent.example";
const SUBJECT: &str = "synthetic-plan-owner";
const KEY: &[u8] = b"0123456789abcdef0123456789abcdef";

#[derive(Clone, Copy, Debug)]
enum ProbeError {
    Fixture,
    Assertion,
    Adapter(StoredPlanError),
}

impl ProbeError {
    const fn code(self) -> &'static str {
        match self {
            Self::Fixture => "FIXTURE",
            Self::Assertion => "ASSERTION",
            Self::Adapter(StoredPlanError::NotFound) => "NOT_FOUND",
            Self::Adapter(StoredPlanError::AccessDenied) => "ACCESS_DENIED",
            Self::Adapter(StoredPlanError::StaleSource) => "STALE_SOURCE",
            Self::Adapter(StoredPlanError::SourceUnavailable) => "SOURCE_UNAVAILABLE",
            Self::Adapter(_) => "ADAPTER",
        }
    }
}

impl fmt::Display for ProbeError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(self.code())
    }
}

impl Error for ProbeError {}

type ProbeResult<T> = Result<T, ProbeError>;

fn fixture<T>(result: Result<T, impl Error>) -> ProbeResult<T> {
    result.map_err(|_| ProbeError::Fixture)
}

fn check(value: bool) -> ProbeResult<()> {
    if value {
        Ok(())
    } else {
        Err(ProbeError::Assertion)
    }
}

fn environment(name: &str) -> ProbeResult<String> {
    std::env::var(name).map_err(|_| ProbeError::Fixture)
}

fn graph(text: &str) -> ProbeResult<DocumentGraph> {
    fixture(DocumentGraph::from_draft(
        DocumentGraphDraft::new(
            fixture(DocumentId::parse("synthetic-plan-document"))?,
            vec![Section {
                section_id: fixture(LogicalId::parse("synthetic-plan-section"))?,
                properties: Properties::new(),
                master_pages: vec![],
                headers_footers: vec![],
                body: Flow {
                    children: vec![Node::Paragraph(ParagraphNode {
                        common: NodeCommon::new(fixture(LogicalId::parse(
                            "synthetic-plan-paragraph",
                        ))?),
                        inlines: vec![Inline::Text {
                            text: text.to_owned(),
                        }],
                        paragraph_properties: Properties::new(),
                    })],
                },
            }],
        ),
        DocumentGraphLimits::default(),
    ))
}

fn compile(source: &DocumentGraph) -> ProbeResult<CompiledOperationPlan> {
    let snapshot = fixture(SelectorSnapshot::build(
        source,
        fixture(RevisionId::parse(REVISION))?,
        SelectorLimits::default(),
    ))?;
    let capability_id = fixture(CapabilityId::parse("text.replace"))?;
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
    let catalog = fixture(CapabilityCatalog::from_drafts(vec![definition]))?;
    let compiler = fixture(OperationPlanCompiler::new(OperationPlanLimits::default()))?;
    fixture(compiler.compile(
        OperationPlanDraft::new(
            fixture(PlanId::parse(PLAN))?,
            fixture(RevisionId::parse(REVISION))?,
            vec![OperationDraft {
                operation_id: fixture(OperationId::parse("synthetic-plan-operation"))?,
                capability_id,
                selector: SelectorDraft::one(Selector::by_logical_id(fixture(LogicalId::parse(
                    "synthetic-plan-paragraph",
                ))?)),
                arguments: BTreeMap::from([(
                    "text".to_owned(),
                    ArgumentDraft::Text("SYNTHETIC REPLACEMENT".to_owned()),
                )]),
                depends_on: vec![],
            }],
        ),
        &catalog,
        &snapshot,
        &snapshot.expectation(),
    ))
}

fn bearer(tenant: TenantId) -> ProbeResult<String> {
    let header = URL_SAFE_NO_PAD.encode(fixture(serde_json::to_vec(
        &json!({"alg":"HS256","kid":"local-key-01","typ":"at+jwt"}),
    ))?);
    let claims = URL_SAFE_NO_PAD.encode(fixture(serde_json::to_vec(&json!({
        "iss": ISSUER, "sub": SUBJECT, "aud": RESOURCE, "exp": NOW + 600,
        "nbf": NOW - 60, "iat": NOW - 60, "jti": "synthetic-plan-token",
        "scope": "project.read project.write", "token_kind": "user", "tenant_id": tenant,
    })))?);
    let input = format!("{header}.{claims}");
    let mut signer = fixture(<Hmac<Sha256> as hmac::KeyInit>::new_from_slice(KEY))?;
    signer.update(input.as_bytes());
    Ok(format!(
        "Bearer {input}.{}",
        URL_SAFE_NO_PAD.encode(signer.finalize().into_bytes())
    ))
}

struct Fixture {
    tenant: TenantId,
    subject: SubjectDigest,
    auth: AuthMiddleware,
    policy: InMemoryProjectPolicy,
    bearer: String,
}

fn auth_fixture() -> ProbeResult<Fixture> {
    let tenant = fixture(TenantId::new(Uuid::from_u128(TENANT)))?;
    let mut auth = fixture(AuthMiddleware::new(
        RESOURCE,
        format!("{RESOURCE}/.well-known/oauth-protected-resource"),
        60,
        AuthRegistryLimits::product_maximums(),
    ))?;
    fixture(auth.register_local_hmac_key(ISSUER, "local-key-01", KEY, NOW - 600, NOW + 7_200))?;
    let subject = fixture(auth.register_user(
        ISSUER,
        SUBJECT,
        fixture(PrincipalGrant::new(
            tenant,
            TenantRole::Owner,
            [AuthScope::ProjectRead, AuthScope::ProjectWrite],
            NOW - 600,
            NOW + 7_200,
        ))?,
    ))?;
    let mut policy = InMemoryProjectPolicy::new(ProjectPolicyLimits::product_maximums());
    fixture(policy.register_project(PROJECT, tenant))?;
    fixture(policy.register_membership(PROJECT, subject, ProjectAccess::Owner))?;
    Ok(Fixture {
        tenant,
        subject,
        auth,
        policy,
        bearer: bearer(tenant)?,
    })
}

fn config() -> ProbeResult<LocalPostgresPlanSourceConfig> {
    fixture(LocalPostgresPlanSourceConfig::new(
        fixture(environment("HWPX_P16_PG_PORT")?.parse())?,
        "postgres".to_owned(),
        environment("HWPX_P16_PG_USER")?,
        environment("HWPX_P16_PG_PASSWORD")?,
    ))
}

fn connect(
    config: &LocalPostgresPlanSourceConfig,
    tenant: TenantId,
) -> ProbeResult<LocalPostgresPlanSourceRepository> {
    LocalPostgresPlanSourceRepository::connect_diagnosed(config, tenant).map_err(|failure| {
        eprintln!(
            "P16_POSTGRES_PLAN_SOURCE_CONNECT_FAILED stage={}",
            failure.stage().code()
        );
        ProbeError::Adapter(failure.into_error())
    })
}

fn expect_connect_rejection(
    mode: &str,
    config: &LocalPostgresPlanSourceConfig,
    tenant: TenantId,
) -> ProbeResult<()> {
    let expected_stage = match mode {
        "reject-role" => PlanSourceConnectStage::Role,
        "reject-migrations" => PlanSourceConnectStage::Migrations,
        "reject-policies" => PlanSourceConnectStage::Policies,
        "reject-privileges" => PlanSourceConnectStage::Privileges,
        _ => return Err(ProbeError::Fixture),
    };
    let expected_error = if expected_stage == PlanSourceConnectStage::Migrations {
        StoredPlanError::SourceUnavailable
    } else {
        StoredPlanError::AccessDenied
    };
    let result = LocalPostgresPlanSourceRepository::connect_diagnosed(config, tenant);
    check(
        matches!(result, Err(ref failure) if failure.stage() == expected_stage
        && failure.error() == expected_error),
    )
}

fn run_registry(
    state: &mut Fixture,
    repository: &LocalPostgresPlanSourceRepository,
    source: &DocumentGraph,
) -> ProbeResult<()> {
    let plan = compile(source)?;
    let expected_digest = fixture(plan.canonical_sha256())?;
    let mut registry = StoredPlanRegistry::new(StoredPlanLimits::product_maximums());
    registry
        .insert(
            &mut state.auth,
            &state.policy,
            repository,
            CompiledPlanSubmission::new(&state.bearer, PROJECT, plan, NOW),
        )
        .map_err(ProbeError::Adapter)?;
    let arguments = fixture(serde_json::to_vec(&json!({
        "schema_version":"hwpx-agent.plan-review-render-request/v1",
        "client_surface":"codex_local", "locale":"ko-KR", "project_id":PROJECT,
        "source_revision_id":REVISION, "plan_id":PLAN,
    })))?;
    let authorized = registry
        .lookup(
            &mut state.auth,
            &state.policy,
            repository,
            PlanLookupRequest::new(&state.bearer, arguments, NOW + 1),
        )
        .map_err(ProbeError::Adapter)?;
    check(authorized.compiled_plan_sha256() == expected_digest)
}

fn run() -> ProbeResult<()> {
    let mode = environment("HWPX_P16_PLAN_SOURCE_MODE")?;
    let source = graph("SYNTHETIC PLAN SOURCE")?;
    let mut state = auth_fixture()?;
    if mode == "identity" {
        println!(
            "P16_POSTGRES_PLAN_SOURCE_IDENTITY subject_sha256={} graph_sha256={}",
            state.subject.hex(),
            hex::encode(fixture(source.canonical_sha256())?)
        );
        return Ok(());
    }
    let config = config()?;
    if mode.starts_with("reject-") {
        expect_connect_rejection(&mode, &config, state.tenant)?;
        println!("P16_POSTGRES_PLAN_SOURCE_PROBE_PASS mode={mode}");
        return Ok(());
    }
    let repository = connect(&config, state.tenant)?;
    match mode.as_str() {
        "verify" => run_registry(&mut state, &repository, &source)?,
        "expect-not-found" | "expect-source-unavailable" => {
            let context = state
                .auth
                .authenticate_public_mcp(&state.bearer, NOW, [AuthScope::ProjectRead])
                .map_err(|_| ProbeError::Fixture)?;
            let expected = if mode == "expect-not-found" {
                StoredPlanError::NotFound
            } else {
                StoredPlanError::SourceUnavailable
            };
            check(matches!(
                repository.current_source(&context, PROJECT),
                Err(error) if error == expected
            ))?;
        }
        "expect-stale" => {
            let stale_graph = graph("SYNTHETIC DIFFERENT SOURCE")?;
            let result = run_registry(&mut state, &repository, &stale_graph);
            check(matches!(
                result,
                Err(ProbeError::Adapter(StoredPlanError::StaleSource))
            ))?;
        }
        _ => return Err(ProbeError::Fixture),
    }
    println!("P16_POSTGRES_PLAN_SOURCE_PROBE_PASS mode={mode}");
    Ok(())
}

fn main() {
    if let Err(error) = run() {
        eprintln!(
            "P16_POSTGRES_PLAN_SOURCE_PROBE_FAILED code={}",
            error.code()
        );
        std::process::exit(1);
    }
}
