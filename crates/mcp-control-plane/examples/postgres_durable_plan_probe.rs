//! Disposable `PostgreSQL` acceptance probe for encrypted durable compiled-plan storage.
//! It uses synthetic plans only and emits closed markers without credentials or database details.

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
    CompiledPlanSubmission, DurablePlanConnectStage, DurablePlanKeyring, InMemoryProjectPolicy,
    LocalPostgresPlanSourceConfig, LocalPostgresPlanSourceRepository,
    LocalPostgresStoredPlanConfig, LocalPostgresStoredPlanRegistry, PlanLookupRequest,
    ProjectAccess, ProjectPolicyLimits, StoredPlanError, StoredPlanLimits, StoredPlanRegistry,
};
use serde_json::json;
use sha2::Sha256;
use uuid::Uuid;
use zeroize::{Zeroize as _, Zeroizing};

const NOW: u64 = 2_000_000_000;
const TENANT: u128 = 1;
const PROJECT: &str = "prj_00000000000000000000000000000101";
const REVISION: &str = "rev_00000000000000000000000000000201";
const PLAN_V1: &str = "plan_00000000000000000000000000000301";
const PLAN_V2: &str = "plan_00000000000000000000000000000302";
const PLAN_V3: &str = "plan_00000000000000000000000000000303";
const ISSUER: &str = "https://identity.hwpx-agent.example";
const RESOURCE: &str = "https://mcp.hwpx-agent.example";
const OWNER: &str = "synthetic-plan-owner";
const OTHER: &str = "synthetic-plan-other";
const AUTH_KEY: &[u8] = b"0123456789abcdef0123456789abcdef";

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
            Self::Adapter(StoredPlanError::Unauthenticated) => "UNAUTHENTICATED",
            Self::Adapter(StoredPlanError::InvalidRequest) => "INVALID_REQUEST",
            Self::Adapter(StoredPlanError::InvalidConfiguration) => "INVALID_CONFIGURATION",
            Self::Adapter(StoredPlanError::NotFound) => "NOT_FOUND",
            Self::Adapter(StoredPlanError::AccessDenied) => "ACCESS_DENIED",
            Self::Adapter(StoredPlanError::StaleSource) => "STALE_SOURCE",
            Self::Adapter(StoredPlanError::Conflict) => "CONFLICT",
            Self::Adapter(StoredPlanError::CapacityExceeded) => "CAPACITY_EXCEEDED",
            Self::Adapter(StoredPlanError::SourceUnavailable) => "SOURCE_UNAVAILABLE",
            Self::Adapter(StoredPlanError::ClockRegression) => "CLOCK_REGRESSION",
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

fn environment(name: &str) -> ProbeResult<Zeroizing<String>> {
    std::env::var(name)
        .map(Zeroizing::new)
        .map_err(|_| ProbeError::Fixture)
}

fn graph() -> ProbeResult<DocumentGraph> {
    fixture(DocumentGraph::from_draft(
        DocumentGraphDraft::new(
            fixture(DocumentId::parse("synthetic-durable-plan-document"))?,
            vec![Section {
                section_id: fixture(LogicalId::parse("synthetic-durable-plan-section"))?,
                properties: Properties::new(),
                master_pages: vec![],
                headers_footers: vec![],
                body: Flow {
                    children: vec![Node::Paragraph(ParagraphNode {
                        common: NodeCommon::new(fixture(LogicalId::parse(
                            "synthetic-durable-plan-paragraph",
                        ))?),
                        inlines: vec![Inline::Text {
                            text: "SYNTHETIC DURABLE PLAN SOURCE".to_owned(),
                        }],
                        paragraph_properties: Properties::new(),
                    })],
                },
            }],
        ),
        DocumentGraphLimits::default(),
    ))
}

fn compile(source: &DocumentGraph, plan_id: &str) -> ProbeResult<CompiledOperationPlan> {
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
            fixture(PlanId::parse(plan_id))?,
            fixture(RevisionId::parse(REVISION))?,
            vec![OperationDraft {
                operation_id: fixture(OperationId::parse("synthetic-durable-operation"))?,
                capability_id,
                selector: SelectorDraft::one(Selector::by_logical_id(fixture(LogicalId::parse(
                    "synthetic-durable-plan-paragraph",
                ))?)),
                arguments: BTreeMap::from([(
                    "text".to_owned(),
                    ArgumentDraft::Text(format!("SYNTHETIC REPLACEMENT {plan_id}")),
                )]),
                depends_on: vec![],
            }],
        ),
        &catalog,
        &snapshot,
        &snapshot.expectation(),
    ))
}

fn bearer(tenant: TenantId, subject: &str) -> ProbeResult<String> {
    let header = URL_SAFE_NO_PAD.encode(fixture(serde_json::to_vec(
        &json!({"alg":"HS256","kid":"local-key-01","typ":"at+jwt"}),
    ))?);
    let claims = URL_SAFE_NO_PAD.encode(fixture(serde_json::to_vec(&json!({
        "iss": ISSUER, "sub": subject, "aud": RESOURCE, "exp": NOW + 3_540,
        "nbf": NOW - 60, "iat": NOW - 60, "jti": format!("durable-token-{subject}"),
        "scope": "project.read project.write", "token_kind": "user", "tenant_id": tenant,
    })))?);
    let input = format!("{header}.{claims}");
    let mut signer = fixture(<Hmac<Sha256> as hmac::KeyInit>::new_from_slice(AUTH_KEY))?;
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
    source: DocumentGraph,
}

fn auth_fixture(subject_name: &str) -> ProbeResult<Fixture> {
    let tenant = fixture(TenantId::new(Uuid::from_u128(TENANT)))?;
    let mut auth = fixture(AuthMiddleware::new(
        RESOURCE,
        format!("{RESOURCE}/.well-known/oauth-protected-resource"),
        60,
        AuthRegistryLimits::product_maximums(),
    ))?;
    fixture(auth.register_local_hmac_key(
        ISSUER,
        "local-key-01",
        AUTH_KEY,
        NOW - 600,
        NOW + 10_000,
    ))?;
    let subject = fixture(auth.register_user(
        ISSUER,
        subject_name,
        fixture(PrincipalGrant::new(
            tenant,
            TenantRole::Owner,
            [AuthScope::ProjectRead, AuthScope::ProjectWrite],
            NOW - 600,
            NOW + 10_000,
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
        bearer: bearer(tenant, subject_name)?,
        source: graph()?,
    })
}

fn decode_key(name: &str) -> ProbeResult<[u8; 32]> {
    let mut encoded = environment(name)?;
    let mut bytes = [0_u8; 32];
    let result =
        hex::decode_to_slice(encoded.as_bytes(), &mut bytes).map_err(|_| ProbeError::Fixture);
    encoded.zeroize();
    result?;
    Ok(bytes)
}

fn database_configs() -> ProbeResult<(LocalPostgresStoredPlanConfig, LocalPostgresPlanSourceConfig)>
{
    let port = fixture(environment("HWPX_P16_PG_PORT")?.parse())?;
    let user = environment("HWPX_P16_PG_USER")?;
    let password = environment("HWPX_P16_PG_PASSWORD")?;
    Ok((
        fixture(LocalPostgresStoredPlanConfig::new(
            port,
            "postgres".to_owned(),
            user.to_string(),
            password.to_string(),
        ))?,
        fixture(LocalPostgresPlanSourceConfig::new(
            port,
            "postgres".to_owned(),
            user.to_string(),
            password.to_string(),
        ))?,
    ))
}

fn keyring(mode: &str) -> ProbeResult<DurablePlanKeyring> {
    let first = decode_key(if mode == "wrong-key" {
        "HWPX_P16_PLAN_WRONG_KEY"
    } else {
        "HWPX_P16_PLAN_KEY_V1"
    })?;
    if matches!(mode, "rotate-seed" | "verify-rotation") {
        fixture(DurablePlanKeyring::new(
            "kms.plan-v2",
            [
                ("kms.plan-v1".to_owned(), first),
                (
                    "kms.plan-v2".to_owned(),
                    decode_key("HWPX_P16_PLAN_KEY_V2")?,
                ),
            ],
        ))
    } else {
        fixture(DurablePlanKeyring::new(
            "kms.plan-v1",
            [("kms.plan-v1".to_owned(), first)],
        ))
    }
}

fn arguments(plan_id: &str, revision: &str) -> ProbeResult<Vec<u8>> {
    fixture(serde_json::to_vec(&json!({
        "schema_version":"hwpx-agent.plan-review-render-request/v1",
        "client_surface":"codex_local", "locale":"ko-KR", "project_id":PROJECT,
        "source_revision_id":revision, "plan_id":plan_id,
    })))
}

fn connect_store(
    config: &LocalPostgresStoredPlanConfig,
    tenant: TenantId,
    keys: DurablePlanKeyring,
    limits: StoredPlanLimits,
) -> ProbeResult<LocalPostgresStoredPlanRegistry> {
    LocalPostgresStoredPlanRegistry::connect_diagnosed(config, tenant, keys, limits).map_err(
        |failure| {
            eprintln!(
                "P16_POSTGRES_DURABLE_PLAN_CONNECT_FAILED stage={}",
                failure.stage().code()
            );
            ProbeError::Adapter(failure.into_error())
        },
    )
}

fn expect_connect_rejection(
    mode: &str,
    config: &LocalPostgresStoredPlanConfig,
    tenant: TenantId,
) -> ProbeResult<()> {
    let expected = match mode {
        "reject-role" => DurablePlanConnectStage::Role,
        "reject-migrations" => DurablePlanConnectStage::Migrations,
        "reject-policies" => DurablePlanConnectStage::Policies,
        "reject-privileges" => DurablePlanConnectStage::Privileges,
        _ => return Err(ProbeError::Fixture),
    };
    let result = LocalPostgresStoredPlanRegistry::connect_diagnosed(
        config,
        tenant,
        keyring("verify")?,
        StoredPlanLimits::product_maximums(),
    );
    check(matches!(result, Err(ref failure) if failure.stage() == expected))
}

fn insert(
    state: &mut Fixture,
    registry: &mut LocalPostgresStoredPlanRegistry,
    source: &LocalPostgresPlanSourceRepository,
    plan_id: &str,
    now: u64,
) -> ProbeResult<[u8; 32]> {
    eprintln!("P16_POSTGRES_DURABLE_PLAN_STAGE stage=COMPILE");
    let plan = compile(&state.source, plan_id)?;
    let digest = fixture(plan.canonical_sha256())?;
    let mut volatile = StoredPlanRegistry::new(StoredPlanLimits::product_maximums());
    volatile
        .insert(
            &mut state.auth,
            &state.policy,
            source,
            CompiledPlanSubmission::new(&state.bearer, PROJECT, plan.clone(), now),
        )
        .map_err(ProbeError::Adapter)?;
    eprintln!("P16_POSTGRES_DURABLE_PLAN_STAGE stage=VOLATILE_PASS");
    registry
        .insert(
            &mut state.auth,
            &state.policy,
            source,
            CompiledPlanSubmission::new(&state.bearer, PROJECT, plan, now),
        )
        .map_err(ProbeError::Adapter)?;
    Ok(digest)
}

fn lookup(
    state: &mut Fixture,
    registry: &mut LocalPostgresStoredPlanRegistry,
    source: &LocalPostgresPlanSourceRepository,
    plan_id: &str,
    revision: &str,
    now: u64,
) -> ProbeResult<[u8; 32]> {
    eprintln!("P16_POSTGRES_DURABLE_PLAN_STAGE stage=LOOKUP");
    registry
        .lookup(
            &mut state.auth,
            &state.policy,
            source,
            PlanLookupRequest::new(&state.bearer, arguments(plan_id, revision)?, now),
        )
        .map(|authorized| authorized.compiled_plan_sha256())
        .map_err(ProbeError::Adapter)
}

fn verify_one(
    state: &mut Fixture,
    registry: &mut LocalPostgresStoredPlanRegistry,
    source: &LocalPostgresPlanSourceRepository,
    plan_id: &str,
    now: u64,
) -> ProbeResult<()> {
    let expected = fixture(compile(&state.source, plan_id)?.canonical_sha256())?;
    check(lookup(state, registry, source, plan_id, REVISION, now)? == expected)
}

fn expect_lookup_error(
    state: &mut Fixture,
    registry: &mut LocalPostgresStoredPlanRegistry,
    source: &LocalPostgresPlanSourceRepository,
    plan_id: &str,
    revision: &str,
    now: u64,
    expected: StoredPlanError,
) -> ProbeResult<()> {
    let result = lookup(state, registry, source, plan_id, revision, now);
    check(matches!(result, Err(ProbeError::Adapter(error)) if error == expected))
}

fn execute_mode(
    mode: &str,
    state: &mut Fixture,
    registry: &mut LocalPostgresStoredPlanRegistry,
    source: &LocalPostgresPlanSourceRepository,
) -> ProbeResult<()> {
    match mode {
        "seed" => {
            let expected = insert(state, registry, source, PLAN_V1, NOW)?;
            check(lookup(state, registry, source, PLAN_V1, REVISION, NOW + 1)? == expected)
        }
        "verify" => verify_one(state, registry, source, PLAN_V1, NOW + 2),
        "rotate-seed" => {
            verify_one(state, registry, source, PLAN_V1, NOW + 2)?;
            let expected = insert(state, registry, source, PLAN_V2, NOW + 2)?;
            check(lookup(state, registry, source, PLAN_V2, REVISION, NOW + 3)? == expected)
        }
        "verify-rotation" => {
            verify_one(state, registry, source, PLAN_V1, NOW + 4)?;
            verify_one(state, registry, source, PLAN_V2, NOW + 4)
        }
        "wrong-key" | "expect-source-unavailable" => expect_lookup_error(
            state,
            registry,
            source,
            PLAN_V1,
            REVISION,
            NOW + 2,
            StoredPlanError::SourceUnavailable,
        ),
        "capacity" => {
            let result = insert(state, registry, source, PLAN_V3, NOW);
            check(matches!(
                result,
                Err(ProbeError::Adapter(StoredPlanError::CapacityExceeded))
            ))
        }
        "expired" => expect_lookup_error(
            state,
            registry,
            source,
            PLAN_V1,
            REVISION,
            NOW + 900,
            StoredPlanError::NotFound,
        ),
        "other-owner" | "expect-not-found" => expect_lookup_error(
            state,
            registry,
            source,
            PLAN_V1,
            REVISION,
            NOW + 2,
            StoredPlanError::NotFound,
        ),
        "stale-argument" => expect_lookup_error(
            state,
            registry,
            source,
            PLAN_V1,
            "rev_00000000000000000000000000000202",
            NOW + 2,
            StoredPlanError::StaleSource,
        ),
        _ => Err(ProbeError::Fixture),
    }
}

fn run() -> ProbeResult<()> {
    let mode = environment("HWPX_P16_DURABLE_PLAN_MODE")?;
    if mode.as_str() == "identity" {
        let owner = auth_fixture(OWNER)?;
        let other = auth_fixture(OTHER)?;
        println!(
            "P16_POSTGRES_DURABLE_PLAN_IDENTITY owner_sha256={} other_sha256={} graph_sha256={}",
            owner.subject.hex(),
            other.subject.hex(),
            hex::encode(fixture(owner.source.canonical_sha256())?)
        );
        return Ok(());
    }
    let subject_name = if mode.as_str() == "other-owner" {
        OTHER
    } else {
        OWNER
    };
    let mut state = auth_fixture(subject_name)?;
    let (store_config, source_config) = database_configs()?;
    if mode.starts_with("reject-") {
        expect_connect_rejection(&mode, &store_config, state.tenant)?;
        println!(
            "P16_POSTGRES_DURABLE_PLAN_PROBE_PASS mode={}",
            mode.as_str()
        );
        return Ok(());
    }
    let limits = if mode.as_str() == "capacity" {
        StoredPlanLimits::new(2, 1024 * 1024, 16 * 1024 * 1024, 900).map_err(ProbeError::Adapter)?
    } else {
        StoredPlanLimits::product_maximums()
    };
    eprintln!("P16_POSTGRES_DURABLE_PLAN_STAGE stage=CONNECT_STORE");
    let mut registry = connect_store(&store_config, state.tenant, keyring(&mode)?, limits)?;
    eprintln!("P16_POSTGRES_DURABLE_PLAN_STAGE stage=CONNECT_SOURCE");
    let source = LocalPostgresPlanSourceRepository::connect_diagnosed(&source_config, state.tenant)
        .map_err(|failure| {
            eprintln!(
                "P16_POSTGRES_DURABLE_PLAN_SOURCE_CONNECT_FAILED stage={}",
                failure.stage().code()
            );
            ProbeError::Adapter(failure.into_error())
        })?;
    execute_mode(&mode, &mut state, &mut registry, &source)?;
    println!(
        "P16_POSTGRES_DURABLE_PLAN_PROBE_PASS mode={}",
        mode.as_str()
    );
    Ok(())
}

fn main() {
    if let Err(error) = run() {
        eprintln!(
            "P16_POSTGRES_DURABLE_PLAN_PROBE_FAILED code={}",
            error.code()
        );
        std::process::exit(1);
    }
}
