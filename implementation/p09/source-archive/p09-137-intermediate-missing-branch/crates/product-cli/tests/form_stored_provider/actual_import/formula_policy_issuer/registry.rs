//! Synthetic registry/clock/keys only; genuine encrypted artifacts and unchanged signed product path.
use super::*;
use uuid::Uuid;
use hwpx_agent_cli::form_stored_provider::actual_import::source_policy::formulas::issuer::registry::*;
use revision_service::{RevisionError,postgres::source_formula_policy::issuer_registry::*};

struct Registry<'a> {
    s: &'a StoredFixture,
    root: Mutex<FormulaIssuerTrustRecord>,
    approval: Mutex<FormulaApprovalRecord>,
    denied: AtomicBool,
    calls: AtomicUsize,
    change_at: AtomicUsize,
}
fn payload(row: &FormulaIssuerTrustRecord, pair: &Ed25519KeyPair) -> AnyResult<Vec<u8>> {
    Ok(serde_json::to_vec(
        &json!({"schema_version":FORMULA_ISSUER_TRUST_SCHEMA,
        "tenant":row.tenant,"project":row.project,"trust_version":row.version,
        "generation":row.generation,"issuer":row.issuer,"valid_from":row.valid_from,
        "valid_until":row.valid_until,"max_approval_lifetime":row.max_approval_lifetime,
        "keys":[{"key_id":"P119-test-key","public_key_hex":hex::encode(pair.public_key().as_ref())}]}),
    )?)
}
impl<'a> Registry<'a> {
    fn new(s: &'a StoredFixture, server: &Server<'_>) -> AnyResult<Self> {
        let mut root = FormulaIssuerTrustRecord {
            tenant: s.owner.tenant_id(),
            project: s.project,
            version: Uuid::new_v4(),
            generation: 1,
            issuer: "P119-test-issuer".into(),
            valid_from: 5,
            valid_until: 1000,
            max_approval_lifetime: 600,
            artifact: ArtifactId::generate(),
            digest: ContentDigest::of(b"placeholder"),
            creator: s.owner.subject(),
        };
        let d = s.artifacts.ingest(
            &s.owner,
            IngestRequest {
                bytes: payload(&root, &server.pair)?,
                kind: ArtifactKind::Evidence,
                media_type: MediaType::parse(FORMULA_ISSUER_TRUST_MEDIA_TYPE)?,
                file_name: FileName::parse("synthetic-trust.json")?,
            },
            7,
        )?;
        root.artifact = d.artifact_id;
        root.digest = d.sha256;
        let policy = server.policy()?;
        let proof = server
            .proof
            .lock()
            .map_err(|_| "proof")?
            .clone()
            .ok_or("proof")?;
        let approval = FormulaApprovalRecord {
            tenant: s.owner.tenant_id(),
            project: s.project,
            branch: s.branch,
            document: "actual-form-document".into(),
            version: Uuid::new_v4(),
            generation: 1,
            policy_version: policy.binding.policy_version,
            policy_generation: policy.binding.policy_generation,
            trust_version: root.version,
            trust_generation: 1,
            artifact: proof.artifact,
            digest: proof.digest,
            creator: s.owner.subject(),
        };
        Ok(Self {
            s,
            root: Mutex::new(root),
            approval: Mutex::new(approval),
            denied: AtomicBool::new(false),
            calls: AtomicUsize::new(0),
            change_at: AtomicUsize::new(usize::MAX),
        })
    }
    fn authorized(&self, c: &RevisionRequestContext, project: revision_service::ProjectId) -> bool {
        !self.denied.load(Ordering::SeqCst)
            && c.tenant_id() == self.s.owner.tenant_id()
            && project == self.s.project
            && [self.s.owner.subject(), self.s.reader.subject()].contains(&c.subject())
    }
    fn install(&self, raw: Vec<u8>, kind: ArtifactKind, media: &str) -> AnyResult<()> {
        let d = self.s.artifacts.ingest(
            &self.s.owner,
            IngestRequest {
                bytes: raw,
                kind,
                media_type: MediaType::parse(media)?,
                file_name: FileName::parse("synthetic-trust.json")?,
            },
            7,
        )?;
        let mut row = self.root.lock().map_err(|_| "root")?;
        row.artifact = d.artifact_id;
        row.digest = d.sha256;
        Ok(())
    }
    fn root(&self) -> AnyResult<FormulaIssuerTrustRecord> {
        Ok(self.root.lock().map_err(|_| "root")?.clone())
    }
}
impl FormulaIssuerRegistryRepository for Registry<'_> {
    fn read_trust(
        &self,
        c: &RevisionRequestContext,
        project: revision_service::ProjectId,
    ) -> Result<FormulaIssuerTrustRecord, RevisionError> {
        if !self.authorized(c, project) {
            return Err(RevisionError::NotFound);
        }
        let mut row = self
            .root
            .lock()
            .map_err(|_| RevisionError::RepositoryFailure)?
            .clone();
        if self.calls.fetch_add(1, Ordering::SeqCst) >= self.change_at.load(Ordering::SeqCst) {
            row.digest = ContentDigest::of(b"same-generation-live-drift");
        }
        Ok(row)
    }
    fn read_approval(
        &self,
        c: &RevisionRequestContext,
        r: &FormulaApprovalReadRequest,
    ) -> Result<FormulaApprovalRecord, RevisionError> {
        if !self.authorized(c, r.project()) || r.head() != self.s.head {
            return Err(RevisionError::NotFound);
        }
        Ok(self
            .approval
            .lock()
            .map_err(|_| RevisionError::RepositoryFailure)?
            .clone())
    }
}
struct Capture<'a, 'b> {
    server: &'a Server<'b>,
    scope: Mutex<Option<PolicyReadScope>>,
}
impl FormulaPolicyRepository for Capture<'_, '_> {
    fn read_current_formula_policy(
        &self,
        scope: &PolicyReadScope,
    ) -> Result<SourcePolicyVersion, StoredFormulaPolicyError> {
        *self
            .scope
            .lock()
            .map_err(|_| StoredFormulaPolicyError::Repository)? = Some(scope.clone());
        self.server.read_current_formula_policy(scope)
    }
}
fn scope(s: &StoredFixture, p: &Provider<'_>, server: &Server<'_>) -> AnyResult<PolicyReadScope> {
    let capture = Capture {
        server,
        scope: Mutex::new(None),
    };
    let clock = Clock::default();
    let deps = FormulaIssuerDependencies::new(&capture, server, server, &clock);
    let _prepared =
        StoredProductRequest::prepare_formula_with_issuer(p, &deps, &request(s, &bytes()?)?)?;
    capture
        .scope
        .into_inner()
        .map_err(|_| "scope")?
        .ok_or("scope".into())
}

#[test]
fn registry_genuine_changed_current_and_historical_owner_reader_use_original_ed25519_product()
-> TestResult {
    let original = bytes()?;
    for input in [original.clone(), current(&original)?] {
        let s = StoredFixture::new(&input, ArtifactKind::Result, false)?;
        let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
        let p = writer(&s, &c)?;
        let server = Server::new(&s)?;
        register(&s, &p, &server, true, 0)?;
        let registry = Registry::new(&s, &server)?;
        let clock = Clock::default();
        let approvals = RegistryFormulaApprovalProvider::new(&registry);
        let roots = RegistryFormulaTrustProvider::new(&registry, &s.artifacts, &s.owner, &clock);
        let deps = FormulaIssuerDependencies::new(&server, &approvals, &roots, &clock);
        let prepared =
            StoredProductRequest::prepare_formula_with_issuer(&p, &deps, &request(&s, &input)?)?;
        assert_eq!(
            prepared.with_verified_bytes(&p, &deps, <[u8]>::to_vec)?,
            current(&original)?
        );
        assert_eq!(
            matches!(
                prepared.receipt().product.product.formula,
                FormulaPreparationReceipt::Changed { .. }
            ),
            input == original
        );
        assert!(prepared.require_current_product_route(&p, &deps).is_err());
        for id in [
            server.policy()?.artifact,
            registry.root()?.artifact,
            registry.approval.lock().map_err(|_| "approval")?.artifact,
        ] {
            s.artifacts.set_permissions(
                &s.owner,
                id,
                s.reader.subject(),
                BTreeSet::from([ArtifactPermission::Read]),
                8,
            )?;
        }
        let reader = s.provider()?;
        let reader_roots =
            RegistryFormulaTrustProvider::new(&registry, &s.artifacts, &s.reader, &clock);
        let reader_deps =
            FormulaIssuerDependencies::new(&server, &approvals, &reader_roots, &clock);
        let read = StoredProductRequest::prepare_formula_with_issuer(
            &reader,
            &reader_deps,
            &request(&s, &input)?,
        )?;
        assert_eq!(
            read.with_verified_bytes(&reader, &reader_deps, <[u8]>::to_vec)?,
            current(&original)?
        );
        no_publication(&s)?;
    }
    Ok(())
}
#[test]
fn registry_denial_after_prepare_never_calls_consumer_or_publishes() -> TestResult {
    let original = bytes()?;
    let s = StoredFixture::new(&original, ArtifactKind::Result, false)?;
    let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
    let p = writer(&s, &c)?;
    let server = Server::new(&s)?;
    register(&s, &p, &server, true, 0)?;
    let registry = Registry::new(&s, &server)?;
    let clock = Clock::default();
    let approvals = RegistryFormulaApprovalProvider::new(&registry);
    let roots = RegistryFormulaTrustProvider::new(&registry, &s.artifacts, &s.owner, &clock);
    let deps = FormulaIssuerDependencies::new(&server, &approvals, &roots, &clock);
    let prepared =
        StoredProductRequest::prepare_formula_with_issuer(&p, &deps, &request(&s, &original)?)?;
    registry.denied.store(true, Ordering::SeqCst);
    let called = AtomicBool::new(false);
    assert!(
        prepared
            .with_verified_bytes(&p, &deps, |_| called.store(true, Ordering::SeqCst))
            .is_err()
    );
    assert!(!called.load(Ordering::SeqCst));
    no_publication(&s)?;
    Ok(())
}
#[test]
fn registry_approval_rejects_wrong_policy_root_scope_alias_and_generation() -> TestResult {
    let original = bytes()?;
    let s = StoredFixture::new(&original, ArtifactKind::Result, false)?;
    let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
    let p = writer(&s, &c)?;
    let server = Server::new(&s)?;
    register(&s, &p, &server, true, 0)?;
    let registry = Registry::new(&s, &server)?;
    let scope = scope(&s, &p, &server)?;
    let approvals = RegistryFormulaApprovalProvider::new(&registry);
    let policy = server.policy()?;
    let base = registry.approval.lock().map_err(|_| "approval")?.clone();
    for n in 0..9 {
        let mut row = base.clone();
        match n {
            0 => row.policy_version = Uuid::new_v4(),
            1 => row.policy_generation += 1,
            2 => row.trust_version = Uuid::new_v4(),
            3 => row.trust_generation += 1,
            4 => row.branch = BranchId::generate(),
            5 => row.document = "foreign-doc".into(),
            6 => row.artifact = policy.artifact,
            7 => row.artifact = registry.root()?.artifact,
            _ => row.generation = u64::MAX,
        }
        *registry.approval.lock().map_err(|_| "approval")? = row;
        assert!(
            approvals.read_current_approval(&scope, &policy).is_err(),
            "case {n}"
        );
    }
    *registry.approval.lock().map_err(|_| "approval")? = base;
    let mut wrong = policy.clone();
    wrong.binding.source_head_generation += 1;
    assert!(approvals.read_current_approval(&scope, &wrong).is_err());
    assert_eq!(
        format!("{approvals:?}"),
        "RegistryFormulaApprovalProvider(<redacted>)"
    );
    no_publication(&s)?;
    Ok(())
}
#[test]
fn registry_root_strict_payload_rejects_unknown_duplicate_coercion_positional_and_trailing()
-> TestResult {
    let original = bytes()?;
    let s = StoredFixture::new(&original, ArtifactKind::Result, false)?;
    let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
    let p = writer(&s, &c)?;
    let server = Server::new(&s)?;
    register(&s, &p, &server, true, 0)?;
    let registry = Registry::new(&s, &server)?;
    let scope = scope(&s, &p, &server)?;
    let clock = Clock::default();
    let roots = RegistryFormulaTrustProvider::new(&registry, &s.artifacts, &s.owner, &clock);
    let raw = payload(&registry.root()?, &server.pair)?;
    let value: Value = serde_json::from_slice(&raw)?;
    let mut invalid = Vec::new();
    for (key, v) in [
        ("extra", json!(true)),
        ("generation", json!("1")),
        ("valid_from", json!(5.0)),
        ("valid_until", json!(true)),
        ("trust_version", json!(Uuid::new_v4())),
        ("issuer", json!("foreign")),
        ("keys", json!([])),
        (
            "keys",
            json!([[
                "P119-test-key",
                hex::encode(server.pair.public_key().as_ref())
            ]]),
        ),
    ] {
        let mut x = value.clone();
        x[key] = v;
        invalid.push(serde_json::to_vec(&x)?);
    }
    let mut unknown_key = value.clone();
    unknown_key["keys"][0]["extra"] = json!(0);
    invalid.push(serde_json::to_vec(&unknown_key)?);
    let mut dup = value.clone();
    dup["keys"] = json!([value["keys"][0].clone(), value["keys"][0].clone()]);
    invalid.push(serde_json::to_vec(&dup)?);
    let text = String::from_utf8(raw.clone())?;
    invalid.push(format!("{{\"generation\":1,{}", &text[1..]).into_bytes());
    invalid.push(
        text.replace("\"key_id\":", "\"key_id\":\"duplicate\",\"key_id\":")
            .into_bytes(),
    );
    invalid.push([raw.clone(), b" {}".to_vec()].concat());
    invalid.push(serde_json::to_vec(
        &value
            .as_object()
            .ok_or("object")?
            .values()
            .collect::<Vec<_>>(),
    )?);
    invalid.push(vec![b' '; 32769]);
    for (n, x) in invalid.into_iter().enumerate() {
        registry.install(x, ArtifactKind::Evidence, FORMULA_ISSUER_TRUST_MEDIA_TYPE)?;
        assert!(roots.read_formula_issuer_trust(&scope).is_err(), "case {n}");
    }
    no_publication(&s)?;
    Ok(())
}
#[test]
fn registry_root_artifact_media_kind_digest_acl_and_aead_fail_closed() -> TestResult {
    let original = bytes()?;
    let s = StoredFixture::new(&original, ArtifactKind::Result, false)?;
    let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
    let p = writer(&s, &c)?;
    let server = Server::new(&s)?;
    register(&s, &p, &server, true, 0)?;
    let registry = Registry::new(&s, &server)?;
    let scope = scope(&s, &p, &server)?;
    let clock = Clock::default();
    let roots = RegistryFormulaTrustProvider::new(&registry, &s.artifacts, &s.owner, &clock);
    let raw = payload(&registry.root()?, &server.pair)?;
    for (kind, media) in [
        (ArtifactKind::Result, FORMULA_ISSUER_TRUST_MEDIA_TYPE),
        (ArtifactKind::Evidence, "application/json"),
    ] {
        registry.install(raw.clone(), kind, media)?;
        assert!(roots.read_formula_issuer_trust(&scope).is_err());
    }
    registry.install(raw, ArtifactKind::Evidence, FORMULA_ISSUER_TRUST_MEDIA_TYPE)?;
    roots.read_formula_issuer_trust(&scope)?;
    s.blobs.tamper.store(true, Ordering::SeqCst);
    assert!(roots.read_formula_issuer_trust(&scope).is_err());
    s.blobs.tamper.store(false, Ordering::SeqCst);
    registry.root.lock().map_err(|_| "root")?.digest = ContentDigest::of(b"wrong-digest");
    assert!(roots.read_formula_issuer_trust(&scope).is_err());
    let reader_roots =
        RegistryFormulaTrustProvider::new(&registry, &s.artifacts, &s.reader, &clock);
    assert!(reader_roots.read_formula_issuer_trust(&scope).is_err());
    no_publication(&s)?;
    Ok(())
}
#[test]
fn registry_root_same_generation_change_and_clock_backward_expiry_are_denied() -> TestResult {
    let original = bytes()?;
    let s = StoredFixture::new(&original, ArtifactKind::Result, false)?;
    let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
    let p = writer(&s, &c)?;
    let server = Server::new(&s)?;
    register(&s, &p, &server, true, 0)?;
    let registry = Registry::new(&s, &server)?;
    let scope = scope(&s, &p, &server)?;
    let clock = Clock::default();
    let roots = RegistryFormulaTrustProvider::new(&registry, &s.artifacts, &s.owner, &clock);
    registry.change_at.store(1, Ordering::SeqCst);
    assert_eq!(
        roots.read_formula_issuer_trust(&scope).err(),
        Some(FormulaIssuerError::Drift)
    );
    registry.change_at.store(usize::MAX, Ordering::SeqCst);
    clock.calls.store(0, Ordering::SeqCst);
    clock.jump_at.store(1, Ordering::SeqCst);
    clock.jump_to.store(11, Ordering::SeqCst);
    assert_eq!(
        roots.read_formula_issuer_trust(&scope).err(),
        Some(FormulaIssuerError::Clock)
    );
    clock.calls.store(0, Ordering::SeqCst);
    clock.jump_to.store(1000, Ordering::SeqCst);
    assert_eq!(
        roots.read_formula_issuer_trust(&scope).err(),
        Some(FormulaIssuerError::Time)
    );
    assert_eq!(
        format!("{roots:?}"),
        "RegistryFormulaTrustProvider(<redacted>)"
    );
    assert_eq!(
        format!("{:?}", registry.root()?),
        "FormulaIssuerTrustRecord(<redacted>)"
    );
    no_publication(&s)?;
    Ok(())
}
#[test]
fn registry_trusted_metadata_does_not_replace_ed25519_or_protection_checks() -> TestResult {
    let original = bytes()?;
    let s = StoredFixture::new(&original, ArtifactKind::Result, false)?;
    let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
    let p = writer(&s, &c)?;
    let server = Server::new(&s)?;
    register(&s, &p, &server, false, 0)?;
    let registry = Registry::new(&s, &server)?;
    let clock = Clock::default();
    let approvals = RegistryFormulaApprovalProvider::new(&registry);
    let roots = RegistryFormulaTrustProvider::new(&registry, &s.artifacts, &s.owner, &clock);
    let deps = FormulaIssuerDependencies::new(&server, &approvals, &roots, &clock);
    assert!(
        StoredProductRequest::prepare_formula_with_issuer(&p, &deps, &request(&s, &original)?)
            .is_err()
    );
    register(&s, &p, &server, true, 1)?;
    let registry = Registry::new(&s, &server)?;
    let mut env: Value = serde_json::from_slice(&server.raw()?)?;
    env["signature_hex"] = json!("00".repeat(64));
    server.install(
        serde_json::to_vec(&env)?,
        ArtifactKind::Evidence,
        FORMULA_APPROVAL_MEDIA_TYPE,
    )?;
    let proof = server
        .proof
        .lock()
        .map_err(|_| "proof")?
        .clone()
        .ok_or("proof")?;
    {
        let mut row = registry.approval.lock().map_err(|_| "approval")?;
        row.artifact = proof.artifact;
        row.digest = proof.digest;
    }
    let approvals = RegistryFormulaApprovalProvider::new(&registry);
    let roots = RegistryFormulaTrustProvider::new(&registry, &s.artifacts, &s.owner, &clock);
    let deps = FormulaIssuerDependencies::new(&server, &approvals, &roots, &clock);
    assert!(
        StoredProductRequest::prepare_formula_with_issuer(&p, &deps, &request(&s, &original)?)
            .is_err()
    );
    no_publication(&s)?;
    Ok(())
}
