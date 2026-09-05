use std::collections::{BTreeMap, BTreeSet};
use std::error::Error;
use std::sync::atomic::{AtomicUsize, Ordering};

use artifact_service::{SubjectDigest, TenantId};
use auth_middleware::{
    AuthContext, AuthMiddleware, AuthRegistryLimits, AuthScope, PrincipalGrant, TenantRole,
};
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
    AuthorizedStoredPlan, CompiledPlanSubmission, CurrentPlanSource, InMemoryProjectPolicy,
    PlanLookupRequest, PlanSourceRepository, ProjectAccess, ProjectPolicyLimits, StoredPlanError,
    StoredPlanLimits, StoredPlanRegistry,
};
use serde_json::{Value, json};
use sha2::Sha256;
use uuid::Uuid;

type TestResult = Result<(), Box<dyn Error>>;
const NOW: u64 = 2_000_000_000;
const PROJECT: &str = "prj_private001";
const REVISION: &str = "rev_private001";
const PLAN: &str = "plan_private001";
const ISSUER: &str = "https://identity.hwpx-agent.example";
const RESOURCE: &str = "https://mcp.hwpx-agent.example";
// Disposable local test key, never a user credential.
const KEY: &[u8] = b"0123456789abcdef0123456789abcdef";

fn graph(text: &str) -> Result<DocumentGraph, Box<dyn Error>> {
    Ok(DocumentGraph::from_draft(
        DocumentGraphDraft::new(
            DocumentId::parse("private-document")?,
            vec![Section {
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
    graph: &DocumentGraph,
    revision: &str,
    plan: &str,
    text: &str,
) -> Result<CompiledOperationPlan, Box<dyn Error>> {
    let snapshot = SelectorSnapshot::build(
        graph,
        RevisionId::parse(revision)?,
        SelectorLimits::default(),
    )?;
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
                PlanId::parse(plan)?,
                RevisionId::parse(revision)?,
                vec![OperationDraft {
                    operation_id: OperationId::parse("private-operation")?,
                    capability_id,
                    selector: SelectorDraft::one(Selector::by_logical_id(LogicalId::parse(
                        "private-paragraph",
                    )?)),
                    arguments: BTreeMap::from([(
                        "text".to_owned(),
                        ArgumentDraft::Text(text.to_owned()),
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

fn token(
    tenant: TenantId,
    subject: &str,
    scopes: &str,
    expires: u64,
) -> Result<String, Box<dyn Error>> {
    let header = URL_SAFE_NO_PAD.encode(serde_json::to_vec(
        &json!({"alg":"HS256","kid":"local-key-01","typ":"at+jwt"}),
    )?);
    let claims = URL_SAFE_NO_PAD.encode(serde_json::to_vec(&json!({
        "iss": ISSUER, "sub": subject, "aud": RESOURCE, "exp": expires,
        "nbf": NOW - 60, "iat": NOW - 60, "jti": format!("token-{subject}"),
        "scope": scopes, "token_kind": "user", "tenant_id": tenant,
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
    project: String,
    revision: String,
    graph: DocumentGraph,
    allowed: BTreeSet<SubjectDigest>,
    calls: AtomicUsize,
    deny: bool,
    corrupt_scope: bool,
}

impl std::fmt::Debug for Source {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str("Source(<redacted>)")
    }
}

impl PlanSourceRepository for Source {
    fn current_source(
        &self,
        context: &AuthContext,
        project: &str,
    ) -> Result<CurrentPlanSource, StoredPlanError> {
        self.calls.fetch_add(1, Ordering::SeqCst);
        if self.deny
            || context.tenant_id() != self.tenant
            || project != self.project
            || !self.allowed.contains(&context.subject())
        {
            return Err(StoredPlanError::NotFound);
        }
        CurrentPlanSource::from_graph(
            self.tenant,
            if self.corrupt_scope {
                "prj_wrong001"
            } else {
                &self.project
            },
            &self.revision,
            &self.graph,
        )
    }
}

struct Fixture {
    registry: StoredPlanRegistry,
    auth: AuthMiddleware,
    policy: InMemoryProjectPolicy,
    source: Source,
    tenant: TenantId,
    bearer: String,
    other_bearer: String,
    foreign_bearer: String,
}

impl Fixture {
    fn new() -> Result<Self, Box<dyn Error>> {
        let tenant = TenantId::new(Uuid::from_u128(1))?;
        let foreign_tenant = TenantId::new(Uuid::from_u128(2))?;
        let mut auth = AuthMiddleware::new(
            RESOURCE,
            format!("{RESOURCE}/.well-known/oauth-protected-resource"),
            60,
            AuthRegistryLimits::product_maximums(),
        )?;
        auth.register_local_hmac_key(ISSUER, "local-key-01", KEY, NOW - 600, NOW + 7200)?;
        let mut policy = InMemoryProjectPolicy::new(ProjectPolicyLimits::product_maximums());
        policy.register_project(PROJECT, tenant)?;
        let mut allowed = BTreeSet::new();
        for (name, id) in [
            ("private-owner", tenant),
            ("private-other", tenant),
            ("private-foreign", foreign_tenant),
        ] {
            let subject = auth.register_user(
                ISSUER,
                name,
                PrincipalGrant::new(
                    id,
                    TenantRole::Owner,
                    [AuthScope::ProjectRead, AuthScope::ProjectWrite],
                    NOW - 600,
                    NOW + 7200,
                )?,
            )?;
            if id == tenant {
                policy.register_membership(PROJECT, subject, ProjectAccess::Owner)?;
                allowed.insert(subject);
            }
        }
        Ok(Self {
            registry: StoredPlanRegistry::new(StoredPlanLimits::product_maximums()),
            auth,
            policy,
            source: Source {
                tenant,
                project: PROJECT.to_owned(),
                revision: REVISION.to_owned(),
                graph: graph("PRIVATE SOURCE BODY")?,
                allowed,
                calls: AtomicUsize::new(0),
                deny: false,
                corrupt_scope: false,
            },
            tenant,
            bearer: token(
                tenant,
                "private-owner",
                "project.read project.write",
                NOW + 600,
            )?,
            other_bearer: token(
                tenant,
                "private-other",
                "project.read project.write",
                NOW + 600,
            )?,
            foreign_bearer: token(
                foreign_tenant,
                "private-foreign",
                "project.read project.write",
                NOW + 600,
            )?,
        })
    }

    fn insert(&mut self, plan_id: &str, text: &str) -> Result<(), Box<dyn Error>> {
        let plan = compile(&self.source.graph, REVISION, plan_id, text)?;
        self.registry.insert(
            &mut self.auth,
            &self.policy,
            &self.source,
            CompiledPlanSubmission::new(&self.bearer, PROJECT, plan, NOW),
        )?;
        Ok(())
    }

    fn load(
        &mut self,
        bearer: String,
        value: &Value,
        now: u64,
    ) -> Result<AuthorizedStoredPlan, StoredPlanError> {
        self.raw_load(
            bearer,
            serde_json::to_vec(value).map_err(|_| StoredPlanError::InvalidRequest)?,
            now,
        )
    }

    fn raw_load(
        &mut self,
        bearer: String,
        json: Vec<u8>,
        now: u64,
    ) -> Result<AuthorizedStoredPlan, StoredPlanError> {
        self.registry.lookup(
            &mut self.auth,
            &self.policy,
            &self.source,
            PlanLookupRequest::new(bearer, json, now),
        )
    }
}

fn arguments() -> Value {
    json!({"schema_version":"hwpx-agent.plan-review-render-request/v1","client_surface":"codex_local",
        "locale":"ko-KR","project_id":PROJECT,"source_revision_id":REVISION,"plan_id":PLAN})
}

#[test]
fn exact_compiler_receipt_is_returned_after_fresh_repository_read() -> TestResult {
    let mut f = Fixture::new()?;
    let expected = compile(&f.source.graph, REVISION, PLAN, "PRIVATE REPLACEMENT")?;
    assert_eq!(
        expected.base_graph_sha256(),
        f.source.graph.canonical_sha256()?
    );
    f.insert(PLAN, "PRIVATE REPLACEMENT")?;
    let loaded = f.load(f.bearer.clone(), &arguments(), NOW)?;
    assert_eq!(loaded.compiled_plan(), &expected);
    assert_eq!(loaded.compiled_plan_sha256(), expected.canonical_sha256()?);
    f.load(f.bearer.clone(), &arguments(), NOW + 1)?;
    assert_eq!(f.source.calls.load(Ordering::SeqCst), 3);
    Ok(())
}

#[test]
fn tenant_project_and_plan_owner_cannot_be_substituted() -> TestResult {
    let mut f = Fixture::new()?;
    f.insert(PLAN, "private")?;
    for bearer in [f.other_bearer.clone(), f.foreign_bearer.clone()] {
        assert_eq!(
            f.load(bearer, &arguments(), NOW).err(),
            Some(StoredPlanError::NotFound)
        );
    }
    let mut wrong = arguments();
    wrong["project_id"] = json!("prj_unknown01");
    assert_eq!(
        f.load(f.bearer.clone(), &wrong, NOW).err(),
        Some(StoredPlanError::NotFound)
    );
    wrong = arguments();
    wrong["plan_id"] = json!("plan_unknown01");
    assert_eq!(
        f.load(f.bearer.clone(), &wrong, NOW).err(),
        Some(StoredPlanError::NotFound)
    );
    assert_eq!(f.source.calls.load(Ordering::SeqCst), 1);
    Ok(())
}

#[test]
fn every_lookup_reauthenticates_revocation_expiry_and_read_scope() -> TestResult {
    let mut f = Fixture::new()?;
    f.insert(PLAN, "private")?;
    for bearer in [
        "Bearer invalid".to_owned(),
        token(f.tenant, "private-owner", "project.write", NOW + 600)?,
    ] {
        assert_eq!(
            f.load(bearer, &arguments(), NOW).err(),
            Some(StoredPlanError::Unauthenticated)
        );
    }
    f.load(f.bearer.clone(), &arguments(), NOW)?;
    f.auth.revoke_token_id(ISSUER, "token-private-owner", NOW)?;
    assert_eq!(
        f.load(f.bearer.clone(), &arguments(), NOW).err(),
        Some(StoredPlanError::Unauthenticated)
    );
    let mut expired = Fixture::new()?;
    expired.insert(PLAN, "private")?;
    assert_eq!(
        expired
            .load(expired.bearer.clone(), &arguments(), NOW + 600)
            .err(),
        Some(StoredPlanError::Unauthenticated)
    );
    Ok(())
}

#[test]
fn source_acl_and_project_acl_are_not_cached() -> TestResult {
    let mut f = Fixture::new()?;
    f.insert(PLAN, "private")?;
    f.source.deny = true;
    assert_eq!(
        f.load(f.bearer.clone(), &arguments(), NOW).err(),
        Some(StoredPlanError::NotFound)
    );
    f.source.deny = false;
    f.policy = InMemoryProjectPolicy::new(ProjectPolicyLimits::product_maximums());
    f.policy.register_project(PROJECT, f.tenant)?;
    assert_eq!(
        f.load(f.bearer.clone(), &arguments(), NOW).err(),
        Some(StoredPlanError::NotFound)
    );
    assert_eq!(f.source.calls.load(Ordering::SeqCst), 2);
    Ok(())
}

#[test]
fn source_revision_graph_and_repository_scope_must_all_match() -> TestResult {
    let mut f = Fixture::new()?;
    f.insert(PLAN, "private")?;
    let mut wrong = arguments();
    wrong["source_revision_id"] = json!("rev_changed01");
    assert_eq!(
        f.load(f.bearer.clone(), &wrong, NOW).err(),
        Some(StoredPlanError::StaleSource)
    );
    f.source.revision = "rev_changed01".to_owned();
    assert_eq!(
        f.load(f.bearer.clone(), &arguments(), NOW).err(),
        Some(StoredPlanError::StaleSource)
    );
    f.source.revision = REVISION.to_owned();
    f.source.graph = graph("changed source with SAME revision")?;
    assert_eq!(
        f.load(f.bearer.clone(), &arguments(), NOW).err(),
        Some(StoredPlanError::StaleSource)
    );
    f.source.corrupt_scope = true;
    assert_eq!(
        f.load(f.bearer.clone(), &arguments(), NOW).err(),
        Some(StoredPlanError::SourceUnavailable)
    );
    Ok(())
}

#[test]
fn insertion_checks_write_scope_and_role_and_exact_compiler_source() -> TestResult {
    let mut f = Fixture::new()?;
    let compiled = compile(&f.source.graph, REVISION, PLAN, "private")?;
    let read_only = token(f.tenant, "private-owner", "project.read", NOW + 600)?;
    assert_eq!(
        f.registry.insert(
            &mut f.auth,
            &f.policy,
            &f.source,
            CompiledPlanSubmission::new(read_only, PROJECT, compiled.clone(), NOW)
        ),
        Err(StoredPlanError::Unauthenticated)
    );
    let context = f
        .auth
        .authenticate_public_mcp(&f.bearer, NOW, [AuthScope::ProjectRead])?;
    let mut reader_policy = InMemoryProjectPolicy::new(ProjectPolicyLimits::product_maximums());
    reader_policy.register_project(PROJECT, f.tenant)?;
    reader_policy.register_membership(PROJECT, context.subject(), ProjectAccess::Reader)?;
    assert_eq!(
        f.registry.insert(
            &mut f.auth,
            &reader_policy,
            &f.source,
            CompiledPlanSubmission::new(&f.bearer, PROJECT, compiled.clone(), NOW)
        ),
        Err(StoredPlanError::AccessDenied)
    );
    f.source.graph = graph("different source")?;
    assert_eq!(
        f.registry.insert(
            &mut f.auth,
            &f.policy,
            &f.source,
            CompiledPlanSubmission::new(&f.bearer, PROJECT, compiled, NOW)
        ),
        Err(StoredPlanError::StaleSource)
    );
    assert_eq!(
        f.load(f.bearer.clone(), &arguments(), NOW).err(),
        Some(StoredPlanError::NotFound)
    );
    Ok(())
}

#[test]
fn identities_are_never_overwritten_even_after_expiry() -> TestResult {
    let mut f = Fixture::new()?;
    f.insert(PLAN, "original")?;
    let original = f
        .load(f.bearer.clone(), &arguments(), NOW)?
        .compiled_plan_sha256();
    for (bearer, expected) in [
        (f.bearer.clone(), StoredPlanError::Conflict),
        (f.other_bearer.clone(), StoredPlanError::NotFound),
    ] {
        let plan = compile(&f.source.graph, REVISION, PLAN, "replacement")?;
        assert_eq!(
            f.registry.insert(
                &mut f.auth,
                &f.policy,
                &f.source,
                CompiledPlanSubmission::new(bearer, PROJECT, plan, NOW)
            ),
            Err(expected)
        );
    }
    assert_eq!(
        f.load(f.bearer.clone(), &arguments(), NOW)?
            .compiled_plan_sha256(),
        original
    );
    let renewed = token(
        f.tenant,
        "private-owner",
        "project.read project.write",
        NOW + 1200,
    )?;
    assert_eq!(
        f.load(renewed.clone(), &arguments(), NOW + 600).err(),
        Some(StoredPlanError::NotFound)
    );
    let plan = compile(&f.source.graph, REVISION, PLAN, "replacement")?;
    assert_eq!(
        f.registry.insert(
            &mut f.auth,
            &f.policy,
            &f.source,
            CompiledPlanSubmission::new(renewed, PROJECT, plan, NOW + 600)
        ),
        Err(StoredPlanError::Conflict)
    );
    Ok(())
}

#[test]
fn lifetime_and_clock_rollback_do_not_rearm_lookup() -> TestResult {
    let mut f = Fixture::new()?;
    f.registry = StoredPlanRegistry::new(StoredPlanLimits::new(4, 4096, 16384, 2)?);
    f.insert(PLAN, "private")?;
    f.load(f.bearer.clone(), &arguments(), NOW + 1)?;
    for (time, expected) in [
        (NOW - 1, StoredPlanError::ClockRegression),
        (NOW + 2, StoredPlanError::NotFound),
    ] {
        assert_eq!(
            f.load(f.bearer.clone(), &arguments(), time).err(),
            Some(expected)
        );
    }
    assert!(
        f.load(f.bearer.clone(), &arguments(), NOW + 1).is_err(),
        "clock rollback after expiry must not revive a plan"
    );
    Ok(())
}

#[test]
fn capacity_failure_neither_evicts_nor_changes_existing_receipts() -> TestResult {
    let mut f = Fixture::new()?;
    f.registry = StoredPlanRegistry::new(StoredPlanLimits::new(1, 4096, 4096, 600)?);
    f.insert(PLAN, "private")?;
    let plan = compile(&f.source.graph, REVISION, "plan_second01", "other")?;
    assert_eq!(
        f.registry.insert(
            &mut f.auth,
            &f.policy,
            &f.source,
            CompiledPlanSubmission::new(&f.bearer, PROJECT, plan, NOW)
        ),
        Err(StoredPlanError::CapacityExceeded)
    );
    f.load(f.bearer.clone(), &arguments(), NOW)?;
    // A new registry represents a new server run, not an eviction or retry permit.
    f.registry = StoredPlanRegistry::new(StoredPlanLimits::product_maximums());
    assert_eq!(
        f.load(f.bearer.clone(), &arguments(), NOW).err(),
        Some(StoredPlanError::NotFound)
    );
    f.insert(PLAN, "new server run")?;
    Ok(())
}

#[test]
fn individual_and_aggregate_byte_limits_are_enforced_without_truncation() -> TestResult {
    let mut f = Fixture::new()?;
    let plan = compile(&f.source.graph, REVISION, PLAN, "private")?;
    let bytes = plan.canonical_json()?.len();
    f.registry = StoredPlanRegistry::new(StoredPlanLimits::new(4, bytes - 1, bytes * 2, 600)?);
    assert_eq!(
        f.registry.insert(
            &mut f.auth,
            &f.policy,
            &f.source,
            CompiledPlanSubmission::new(&f.bearer, PROJECT, plan.clone(), NOW)
        ),
        Err(StoredPlanError::CapacityExceeded)
    );
    f.registry = StoredPlanRegistry::new(StoredPlanLimits::new(4, bytes, bytes, 600)?);
    f.registry.insert(
        &mut f.auth,
        &f.policy,
        &f.source,
        CompiledPlanSubmission::new(&f.bearer, PROJECT, plan, NOW),
    )?;
    let second = compile(&f.source.graph, REVISION, "plan_private002", "private")?;
    assert_eq!(second.canonical_json()?.len(), bytes);
    assert_eq!(
        f.registry.insert(
            &mut f.auth,
            &f.policy,
            &f.source,
            CompiledPlanSubmission::new(&f.bearer, PROJECT, second, NOW)
        ),
        Err(StoredPlanError::CapacityExceeded)
    );
    f.load(f.bearer.clone(), &arguments(), NOW)?;
    Ok(())
}

#[test]
fn untrusted_security_fields_duplicates_paths_and_oversize_are_rejected() -> TestResult {
    let mut f = Fixture::new()?;
    f.insert(PLAN, "private")?;
    for field in [
        "execution_allowed",
        "warnings",
        "route",
        "diff",
        "owner",
        "tenant_id",
        "now_unix_seconds",
        "file_path",
    ] {
        let mut args = arguments();
        args[field] = json!(true);
        assert_eq!(
            f.load(f.bearer.clone(), &args, NOW).err(),
            Some(StoredPlanError::InvalidRequest)
        );
    }
    for field in [
        "schema_version",
        "client_surface",
        "locale",
        "project_id",
        "source_revision_id",
        "plan_id",
    ] {
        let mut args = arguments();
        args.as_object_mut().ok_or("object")?.remove(field);
        assert_eq!(
            f.load(f.bearer.clone(), &args, NOW).err(),
            Some(StoredPlanError::InvalidRequest)
        );
    }
    let original = serde_json::to_string(&arguments())?;
    let duplicate = format!("{{\"plan_id\":\"{PLAN}\",{}", &original[1..]);
    for raw in [duplicate.into_bytes(), vec![b' '; 2049], b"{}{}".to_vec()] {
        assert_eq!(
            f.raw_load(f.bearer.clone(), raw, NOW).err(),
            Some(StoredPlanError::InvalidRequest)
        );
    }
    let mut args = arguments();
    args["plan_id"] = json!("D:\\private\\document.hwpx");
    assert_eq!(
        f.load(f.bearer.clone(), &args, NOW).err(),
        Some(StoredPlanError::InvalidRequest)
    );
    assert_eq!(f.source.calls.load(Ordering::SeqCst), 1);
    Ok(())
}

#[test]
fn locale_surface_and_identifier_boundaries_match_renderer_contract() -> TestResult {
    let mut f = Fixture::new()?;
    f.insert(PLAN, "private")?;
    for locale in [
        "ko",
        "ko-KR",
        "en-US",
        "zh-Hant-TW",
        "es-419",
        "abc-Latn-001",
    ] {
        for surface in ["chatgpt_web", "codex_remote", "codex_local"] {
            let mut args = arguments();
            args["locale"] = json!(locale);
            args["client_surface"] = json!(surface);
            f.load(f.bearer.clone(), &args, NOW)?;
        }
    }
    for locale in [
        "k",
        "KO-kr",
        "ko-kr",
        "ko-",
        "en-latn",
        "zh-Hant-TW-extra",
        "abcd",
        "../../",
    ] {
        let mut args = arguments();
        args["locale"] = json!(locale);
        assert_eq!(
            f.load(f.bearer.clone(), &args, NOW).err(),
            Some(StoredPlanError::InvalidRequest)
        );
    }
    let longest = format!("plan_{}", "a".repeat(119));
    f.insert(&longest, "private")?;
    let mut args = arguments();
    args["plan_id"] = json!(longest);
    f.load(f.bearer.clone(), &args, NOW)?;
    args["plan_id"] = json!(format!("plan_{}", "a".repeat(120)));
    assert_eq!(
        f.load(f.bearer.clone(), &args, NOW).err(),
        Some(StoredPlanError::InvalidRequest)
    );
    Ok(())
}

#[test]
fn debug_outputs_do_not_leak_compiler_arguments_graphs_ids_or_tokens() -> TestResult {
    let mut f = Fixture::new()?;
    let plan = compile(&f.source.graph, REVISION, PLAN, "PRIVATE REPLACEMENT")?;
    let submission = CompiledPlanSubmission::new(&f.bearer, PROJECT, plan, NOW);
    let lookup = PlanLookupRequest::new(&f.bearer, serde_json::to_vec(&arguments())?, NOW);
    let mut outputs = vec![
        format!("{submission:?}"),
        format!("{lookup:?}"),
        format!(
            "{:?}",
            CurrentPlanSource::from_graph(f.tenant, PROJECT, REVISION, &f.source.graph)?
        ),
    ];
    f.registry
        .insert(&mut f.auth, &f.policy, &f.source, submission)?;
    outputs.push(format!(
        "{:?}",
        f.registry
            .lookup(&mut f.auth, &f.policy, &f.source, lookup)?
    ));
    outputs.push(format!("{:?}", f.registry));
    for output in outputs {
        for secret in ["private", "PRIVATE", PROJECT, REVISION, PLAN, &f.bearer] {
            assert!(!output.contains(secret));
        }
    }
    Ok(())
}

#[test]
fn invalid_limits_and_non_public_compiler_ids_fail_closed() -> TestResult {
    for values in [
        (0, 1, 1, 1),
        (257, 1, 1, 1),
        (1, 0, 1, 1),
        (1, 2, 1, 1),
        (1, 1, 1, 0),
        (1, 1, 1, 901),
        (1, 1, 16_777_217, 1),
    ] {
        assert_eq!(
            StoredPlanLimits::new(values.0, values.1, values.2, values.3).err(),
            Some(StoredPlanError::InvalidConfiguration)
        );
    }
    let mut f = Fixture::new()?;
    let plan = compile(&f.source.graph, REVISION, "internal-plan-id", "private")?;
    assert_eq!(
        f.registry.insert(
            &mut f.auth,
            &f.policy,
            &f.source,
            CompiledPlanSubmission::new(&f.bearer, PROJECT, plan, NOW)
        ),
        Err(StoredPlanError::InvalidRequest)
    );
    assert_eq!(f.source.calls.load(Ordering::SeqCst), 0);
    Ok(())
}
