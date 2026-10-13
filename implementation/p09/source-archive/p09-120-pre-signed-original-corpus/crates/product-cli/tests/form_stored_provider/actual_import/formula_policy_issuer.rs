//! Synthetic issuer/root/clock/server; real Ed25519 + original source/AEAD/product checks, not production trust.
use super::super::{FaultBlob, FixtureScanner, Provider};
use super::formula_compiler::fixture;
use super::*;
use artifact_service::{
    Aes256GcmKeyring, ArtifactId, ArtifactPermission, ArtifactService, ArtifactServiceConfig,
    DownloadSigner, EncryptedBlobStore, FileName, IngestRequest, KeyReference, MediaType,
    ObjectKey,
};
use hwpx_agent_cli::{
    form_product_request::stored_operations::{
        StoredProductRequest,
        formula::{FormulaPreparationReceipt, PRODUCT_OPERATION_REQUEST_SCHEMA},
    },
    form_stored_provider::actual_import::source_policy::{
        PolicyReadScope, SourcePolicyVersion,
        formulas::{
            FormulaPolicyRepository, StoredFormulaPolicyError,
            issuer::{product::*, *},
            registration::{
                FormulaPolicyDecision, FormulaPolicyRegistrationError,
                FormulaPolicyRegistrationRecord, FormulaPolicyRegistrationRepository,
            },
        },
    },
};
use hwpx_package::document_import::fields::semantics::ImportedFieldMeaning;
use revision_service::RevisionRequestContext;
use ring::signature::{Ed25519KeyPair, KeyPair as _};
use serde_json::{Value, json};
use std::sync::{
    Arc, Mutex,
    atomic::{AtomicBool, AtomicU64, AtomicUsize},
};
type AnyResult<T> = Result<T, Box<dyn std::error::Error>>;
const DOMAIN: &[u8] = b"hwpx-agent.source-formula-approval/ed25519-v1\0";

struct Clock {
    value: AtomicU64,
    calls: AtomicUsize,
    jump_at: AtomicUsize,
    jump_to: AtomicU64,
    fail: AtomicBool,
}
impl Default for Clock {
    fn default() -> Self {
        Self {
            value: AtomicU64::new(12),
            calls: AtomicUsize::new(0),
            jump_at: AtomicUsize::new(usize::MAX),
            jump_to: AtomicU64::new(300),
            fail: AtomicBool::new(false),
        }
    }
}
impl FormulaIssuerClock for Clock {
    fn now(&self) -> Result<u64, FormulaIssuerError> {
        if self.fail.load(Ordering::SeqCst) {
            return Err(FormulaIssuerError::Clock);
        }
        let n = self.calls.fetch_add(1, Ordering::SeqCst);
        Ok(if n >= self.jump_at.load(Ordering::SeqCst) {
            self.jump_to.load(Ordering::SeqCst)
        } else {
            self.value.load(Ordering::SeqCst)
        })
    }
}
struct Server<'a> {
    s: &'a StoredFixture,
    pair: Ed25519KeyPair,
    policy: Mutex<Option<SourcePolicyVersion>>,
    proof: Mutex<Option<FormulaApprovalVersion>>,
    raw: Mutex<Vec<u8>>,
    trust: Mutex<FormulaIssuerTrust>,
    proof_revoked: AtomicBool,
    trust_calls: AtomicUsize,
    deny_at: AtomicUsize,
    change_at: AtomicUsize,
}
fn trust(
    s: &StoredFixture,
    pair: &Ed25519KeyPair,
    generation: u64,
    lifetime: u64,
) -> AnyResult<FormulaIssuerTrust> {
    Ok(FormulaIssuerTrust::new(FormulaIssuerTrustDraft {
        tenant: s.owner.tenant_id(),
        project: s.project,
        issuer: "P119-test-issuer".into(),
        generation,
        valid_from: 5,
        valid_until: 1000,
        max_approval_lifetime: lifetime,
        active_keys: vec![FormulaIssuerKey::new(
            "P119-test-key".into(),
            pair.public_key().as_ref().try_into()?,
        )?],
    })?)
}
impl<'a> Server<'a> {
    fn new(s: &'a StoredFixture) -> AnyResult<Self> {
        let pair =
            Ed25519KeyPair::from_seed_unchecked(&[119; 32]).map_err(|_| "synthetic Ed25519 key")?;
        let root = trust(s, &pair, 1, 600)?;
        Ok(Self {
            s,
            pair,
            policy: Mutex::new(None),
            proof: Mutex::new(None),
            raw: Mutex::new(Vec::new()),
            trust: Mutex::new(root),
            proof_revoked: AtomicBool::new(false),
            trust_calls: AtomicUsize::new(0),
            deny_at: AtomicUsize::new(usize::MAX),
            change_at: AtomicUsize::new(usize::MAX),
        })
    }
    fn authorized(&self, scope: &PolicyReadScope) -> bool {
        scope.tenant() == self.s.owner.tenant_id()
            && scope.project() == self.s.project
            && scope.branch() == self.s.branch
            && scope.document().as_str() == "actual-form-document"
            && scope.head() == self.s.head
            && (scope.subject() == self.s.owner.subject()
                || scope.subject() == self.s.reader.subject())
    }
    fn install(&self, raw: Vec<u8>, kind: ArtifactKind, media: &str) -> AnyResult<()> {
        let d = self.s.artifacts.ingest(
            &self.s.owner,
            IngestRequest {
                bytes: raw.clone(),
                kind,
                media_type: MediaType::parse(media)?,
                file_name: FileName::parse("test-formula-approval.json")?,
            },
            7,
        )?;
        *self.proof.lock().map_err(|_| "proof")? = Some(FormulaApprovalVersion {
            artifact: d.artifact_id,
            digest: d.sha256,
        });
        *self.raw.lock().map_err(|_| "raw")? = raw;
        Ok(())
    }
    fn raw(&self) -> AnyResult<Vec<u8>> {
        Ok(self.raw.lock().map_err(|_| "raw")?.clone())
    }
    fn policy(&self) -> AnyResult<SourcePolicyVersion> {
        self.policy
            .lock()
            .map_err(|_| "row")?
            .clone()
            .ok_or("row".into())
    }
    fn resign(&self, env: &mut Value, claims: &str, domain: &[u8]) {
        let sig = self.pair.sign(&[domain, claims.as_bytes()].concat());
        env["signed_claims"] = json!(claims);
        env["signature_hex"] = json!(hex::encode(sig.as_ref()));
    }
}
impl FormulaPolicyRegistrationRepository for Server<'_> {
    fn register_formula_policy(
        &self,
        scope: &PolicyReadScope,
        record: &FormulaPolicyRegistrationRecord,
    ) -> Result<SourcePolicyVersion, FormulaPolicyRegistrationError> {
        if !self.authorized(scope) || scope.subject() != record.version().binding.creator_subject {
            return Err(FormulaPolicyRegistrationError::Repository);
        }
        let approval = PreparedFormulaApproval::from_registration_record(
            record,
            FormulaApprovalIdentity {
                issuer: "P119-test-issuer".into(),
                key_id: "P119-test-key".into(),
                trust_generation: 1,
                issued_at: 6,
                not_before: 6,
                expires_at: 300,
            },
        )
        .map_err(|_| FormulaPolicyRegistrationError::Repository)?;
        assert_eq!(
            format!("{approval:?}"),
            "PreparedFormulaApproval(<redacted>)"
        );
        let sig = self.pair.sign(
            &approval
                .signing_bytes()
                .map_err(|_| FormulaPolicyRegistrationError::Repository)?,
        );
        let bytes = approval
            .envelope(
                sig.as_ref()
                    .try_into()
                    .map_err(|_| FormulaPolicyRegistrationError::Repository)?,
            )
            .map_err(|_| FormulaPolicyRegistrationError::Repository)?;
        let mut row = self
            .policy
            .lock()
            .map_err(|_| FormulaPolicyRegistrationError::Repository)?;
        if row.as_ref().map_or(0, |r| r.binding.policy_generation) != record.expected_generation() {
            return Err(FormulaPolicyRegistrationError::Repository);
        }
        self.install(bytes, ArtifactKind::Evidence, FORMULA_APPROVAL_MEDIA_TYPE)
            .map_err(|_| FormulaPolicyRegistrationError::Repository)?;
        *row = Some(record.version().clone());
        Ok(record.version().clone())
    }
}
impl FormulaPolicyRepository for Server<'_> {
    fn read_current_formula_policy(
        &self,
        scope: &PolicyReadScope,
    ) -> Result<SourcePolicyVersion, StoredFormulaPolicyError> {
        if !self.authorized(scope) {
            return Err(StoredFormulaPolicyError::Repository);
        }
        self.policy
            .lock()
            .map_err(|_| StoredFormulaPolicyError::Repository)?
            .clone()
            .ok_or(StoredFormulaPolicyError::Repository)
    }
}
impl FormulaApprovalRepository for Server<'_> {
    fn read_current_approval(
        &self,
        scope: &PolicyReadScope,
        policy: &SourcePolicyVersion,
    ) -> Result<FormulaApprovalVersion, FormulaIssuerError> {
        if !self.authorized(scope)
            || self.proof_revoked.load(Ordering::SeqCst)
            || self.policy().map_err(|_| FormulaIssuerError::Repository)? != *policy
        {
            return Err(FormulaIssuerError::Repository);
        }
        self.proof
            .lock()
            .map_err(|_| FormulaIssuerError::Repository)?
            .clone()
            .ok_or(FormulaIssuerError::Repository)
    }
}
impl FormulaIssuerTrustRepository for Server<'_> {
    fn read_formula_issuer_trust(
        &self,
        scope: &PolicyReadScope,
    ) -> Result<FormulaIssuerTrust, FormulaIssuerError> {
        let n = self.trust_calls.fetch_add(1, Ordering::SeqCst);
        if !self.authorized(scope) || n >= self.deny_at.load(Ordering::SeqCst) {
            return Err(FormulaIssuerError::Trust);
        }
        if n >= self.change_at.load(Ordering::SeqCst) {
            return trust(self.s, &self.pair, 1, 601).map_err(|_| FormulaIssuerError::Trust);
        }
        Ok(self
            .trust
            .lock()
            .map_err(|_| FormulaIssuerError::Trust)?
            .clone())
    }
}
fn bytes() -> AnyResult<Vec<u8>> {
    fixture::two_sections(&fixture::batch("5")?, &fixture::batch("101")?)
}
fn writer<'a>(s: &'a StoredFixture, c: &'a RevisionRequestContext) -> AnyResult<Provider<'a>> {
    Ok(StoredFormProvider::bind(
        &s.artifacts,
        &s.revisions,
        &s.owner,
        c,
        s.project,
        s.branch,
        DocumentId::parse("actual-form-document")?,
    )?)
}
fn register(
    s: &StoredFixture,
    p: &Provider<'_>,
    server: &Server<'_>,
    allow: bool,
    expected: u64,
) -> TestResult {
    let source = p.import_actual_forms(s.head, 4)?;
    let fields = source.import_field_ranges(p, 4)?;
    let meanings = fields.import_semantics(p, 4)?;
    let decisions: Vec<_> = meanings
        .observations()
        .iter()
        .filter(|m| matches!(m.meaning, ImportedFieldMeaning::TableFormula { .. }))
        .map(|m| FormulaPolicyDecision::new(m.reference_id.clone(), allow))
        .collect();
    source
        .prepare_formula_policy_registration(p, &decisions, expected, 5)?
        .register(p, server, 6)?;
    Ok(())
}
fn request(s: &StoredFixture, bytes: &[u8]) -> AnyResult<Vec<u8>> {
    Ok(serde_json::to_vec(
        &json!({"schema_version": PRODUCT_OPERATION_REQUEST_SCHEMA,
    "idempotency_key":"P119-private-test-key", "project_id":s.project.public_id(), "document_id":"actual-form-document",
    "base_revision":s.head.revision_id().ok_or("head")?.public_id(), "expected_head_generation":s.head.generation(),
    "expected_source_package_sha256":ContentDigest::of(bytes), "plan_id":"signed-formula-plan", "operation":{"kind":"recalculate_table_formulas"}}),
    )?)
}
fn current(bytes: &[u8]) -> AnyResult<Vec<u8>> {
    let forms = super::field_ranges::fixture::forms(bytes, "actual-form-document")?;
    let fields = hwpx_package::document_import::fields::ImportedDocumentFields::import(&forms)?;
    let meanings =
        hwpx_package::document_import::fields::semantics::ImportedDocumentFieldSemantics::import(
            &fields,
        )?;
    Ok(hwpx_package::document_import::fields::semantics::evaluation::ImportedSourceFormulaEvaluation::import(&meanings)?
        .lower_results(bytes, hwpx_package::WriterLimits::default())?.with_verified_bytes(<[u8]>::to_vec)?)
}
fn no_publication(s: &StoredFixture) -> TestResult {
    assert_eq!(
        s.revisions.head(&s.revision_context, s.project, s.branch)?,
        s.head
    );
    assert_eq!(
        s.metadata
            .audit_events()?
            .iter()
            .filter(|e| e.event == "artifact.ingested" && e.artifact_id == s.result)
            .count(),
        1
    );
    Ok(())
}

#[test]
fn genuine_ed25519_generated_policy_gates_original_changed_and_current_products_and_authorized_reader()
-> TestResult {
    let original = bytes()?;
    for bytes in [original.clone(), current(&original)?] {
        let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
        let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
        let p = writer(&s, &c)?;
        let server = Server::new(&s)?;
        let clock = Clock::default();
        register(&s, &p, &server, true, 0)?;
        let deps = FormulaIssuerDependencies::new(&server, &server, &server, &clock);
        let prepared =
            StoredProductRequest::prepare_formula_with_issuer(&p, &deps, &request(&s, &bytes)?)?;
        assert_eq!(prepared.verify(&p, &deps)?, *prepared.receipt());
        assert_eq!(
            prepared.with_verified_bytes(&p, &deps, <[u8]>::to_vec)?,
            current(&original)?
        );
        assert_eq!(
            matches!(
                prepared.receipt().product.product.formula,
                FormulaPreparationReceipt::Changed { .. }
            ),
            bytes == original
        );
        assert!(prepared.require_current_product_route(&p, &deps).is_err());
        for artifact in [
            server.policy()?.artifact,
            server
                .proof
                .lock()
                .map_err(|_| "proof")?
                .as_ref()
                .ok_or("proof")?
                .artifact,
        ] {
            s.artifacts.set_permissions(
                &s.owner,
                artifact,
                s.reader.subject(),
                BTreeSet::from([ArtifactPermission::Read]),
                8,
            )?;
        }
        let reader = s.provider()?;
        let read = StoredProductRequest::prepare_formula_with_issuer(
            &reader,
            &deps,
            &request(&s, &bytes)?,
        )?;
        assert_eq!(
            read.with_verified_bytes(&reader, &deps, <[u8]>::to_vec)?,
            current(&original)?
        );
        let raw = serde_json::to_string(prepared.receipt())?;
        for value in [
            "P119-test-issuer",
            "P119-test-key",
            "actual-form-document",
            "creator_subject",
            "signature_hex",
            "signed_claims",
            "P119-private-test-key",
        ] {
            assert!(!raw.contains(value));
        }
        assert_eq!(
            format!("{prepared:?}"),
            "PreparedIssuerFormulaProduct(<redacted>)"
        );
        assert_eq!(format!("{deps:?}"), "FormulaIssuerDependencies(<redacted>)");
        no_publication(&s)?;
    }
    Ok(())
}
#[test]
fn genuine_signature_cannot_approve_foreign_source_policy_binding_audience_operation_or_root_generation()
-> TestResult {
    let bytes = bytes()?;
    let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
    let p = writer(&s, &c)?;
    let server = Server::new(&s)?;
    register(&s, &p, &server, true, 0)?;
    let base: Value = serde_json::from_slice(&server.raw()?)?;
    let clock = Clock::default();
    let deps = FormulaIssuerDependencies::new(&server, &server, &server, &clock);
    for case in 0..22 {
        let mut env = base.clone();
        let mut claims: Value =
            serde_json::from_str(env["signed_claims"].as_str().ok_or("claims")?)?;
        match case {
            0 => claims["binding"]["tenant"] = json!(TenantId::new(uuid::Uuid::from_u128(11999))?),
            1 => claims["binding"]["project"] = json!(revision_service::ProjectId::generate()),
            2 => claims["binding"]["branch"] = json!(revision_service::BranchId::generate()),
            3 => claims["binding"]["document"] = json!("foreign-document"),
            4 => {
                claims["binding"]["source_revision"] =
                    json!(revision_service::RevisionId::generate());
            }
            5 => claims["binding"]["source_head_generation"] = json!(2),
            6 => claims["binding"]["source_result_artifact"] = json!(ArtifactId::generate()),
            7 => {
                claims["binding"]["source_package_sha256"] =
                    json!(ContentDigest::of(b"different source"));
            }
            8 => {
                claims["binding"]["source_provenance_sha256"] =
                    json!(ContentDigest::of(b"different provenance"));
            }
            9 => {
                claims["binding"]["observed_graph_sha256"] =
                    json!(ContentDigest::of(b"different graph"));
            }
            10 => claims["binding"]["policy_version"] = json!(uuid::Uuid::new_v4()),
            11 => claims["binding"]["policy_generation"] = json!(2),
            12 => claims["binding"]["creator_subject"] = json!(s.reader.subject()),
            13 => claims["policy_artifact"] = json!(ArtifactId::generate()),
            14 => claims["policy_digest"] = json!(ContentDigest::of(b"different policy")),
            15 => claims["audience"] = json!("remote.sync"),
            16 => claims["operation"] = json!("set_form_value"),
            17 => claims["trust_generation"] = json!(2),
            18 => claims["issuer"] = json!("foreign-issuer"),
            19 => claims["key_id"] = json!("foreign-key"),
            20 => claims["schema_version"] = json!("foreign-claims-schema"),
            _ => claims["binding"]["policy_version"] = json!(uuid::Uuid::nil()),
        }
        server.resign(&mut env, &serde_json::to_string(&claims)?, DOMAIN);
        server.install(
            serde_json::to_vec(&env)?,
            ArtifactKind::Evidence,
            FORMULA_APPROVAL_MEDIA_TYPE,
        )?;
        assert!(
            StoredProductRequest::prepare_formula_with_issuer(&p, &deps, &request(&s, &bytes)?)
                .is_err(),
            "binding_case={case}"
        );
    }
    no_publication(&s)
}
#[test]
fn malformed_unknown_duplicate_coerced_positional_and_trailing_approval_never_grants_permission()
-> TestResult {
    let bytes = bytes()?;
    let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
    let p = writer(&s, &c)?;
    let server = Server::new(&s)?;
    register(&s, &p, &server, true, 0)?;
    let base: Value = serde_json::from_slice(&server.raw()?)?;
    let clock = Clock::default();
    let deps = FormulaIssuerDependencies::new(&server, &server, &server, &clock);
    let mut bad = vec![Vec::new(), b"{invalid".to_vec(), vec![b' '; 16385]];
    for case in 0..11 {
        let mut env = base.clone();
        match case {
            0 => env["approved"] = json!(true),
            1 => env["schema_version"] = json!("wrong"),
            2 => env["signature_hex"] = json!("0".repeat(127)),
            3 => {
                env["signature_hex"] =
                    json!(env["signature_hex"].as_str().ok_or("sig")?.to_uppercase());
            }
            4 => env["signature_hex"] = Value::Null,
            5 => env["signed_claims"] = json!({}),
            _ => {
                let mut claims: Value =
                    serde_json::from_str(env["signed_claims"].as_str().ok_or("claims")?)?;
                match case {
                    6 => claims["approval"] = json!(true),
                    7 => claims["binding"]["issuer_verified"] = json!(true),
                    8 => claims["issued_at"] = json!("6"),
                    9 => claims["not_before"] = Value::Null,
                    _ => claims["binding"] = json!([]),
                }
                server.resign(&mut env, &serde_json::to_string(&claims)?, DOMAIN);
            }
        }
        bad.push(serde_json::to_vec(&env)?);
    }
    let claims = base["signed_claims"].as_str().ok_or("claims")?;
    for positional in positional_approval_claims(claims)? {
        let mut env = base.clone();
        server.resign(&mut env, &serde_json::to_string(&positional)?, DOMAIN);
        bad.push(serde_json::to_vec(&env)?);
    }
    for raw in [
        format!("{claims} {{}}"),
        claims.replacen("\"issuer\":", "\"issuer\":\"wrong\",\"iss\\u0075er\":", 1),
        claims.replacen(
            "\"policy_generation\":1",
            "\"policy_generation\":1,\"policy_generation\":1",
            1,
        ),
    ] {
        let mut env = base.clone();
        server.resign(&mut env, &raw, DOMAIN);
        bad.push(serde_json::to_vec(&env)?);
    }
    let whole = serde_json::to_string(&base)?;
    bad.push(format!("{whole} {{}}").into_bytes());
    bad.push(
        whole
            .replacen(
                "\"schema_version\":",
                "\"schema_version\":\"wrong\",\"schema_version\":",
                1,
            )
            .into_bytes(),
    );
    bad.push(serde_json::to_vec(&json!([
        base["schema_version"],
        base["signed_claims"],
        base["signature_hex"]
    ]))?);
    for (case, raw) in bad.into_iter().enumerate() {
        server.install(raw, ArtifactKind::Evidence, FORMULA_APPROVAL_MEDIA_TYPE)?;
        assert!(
            StoredProductRequest::prepare_formula_with_issuer(&p, &deps, &request(&s, &bytes)?)
                .is_err(),
            "shape_case={case}"
        );
    }
    no_publication(&s)
}
fn positional_approval_claims(claims: &str) -> AnyResult<[Value; 2]> {
    let original_claims: Value = serde_json::from_str(claims)?;
    let mut positional_binding = original_claims.clone();
    positional_binding["binding"] = json!([
        original_claims["binding"]["tenant"],
        original_claims["binding"]["project"],
        original_claims["binding"]["branch"],
        original_claims["binding"]["document"],
        original_claims["binding"]["source_revision"],
        original_claims["binding"]["source_head_generation"],
        original_claims["binding"]["source_result_artifact"],
        original_claims["binding"]["source_package_sha256"],
        original_claims["binding"]["source_provenance_sha256"],
        original_claims["binding"]["observed_graph_sha256"],
        original_claims["binding"]["policy_version"],
        original_claims["binding"]["policy_generation"],
        original_claims["binding"]["creator_subject"]
    ]);
    let positional_claims = json!([
        original_claims["schema_version"],
        original_claims["issuer"],
        original_claims["key_id"],
        original_claims["audience"],
        original_claims["operation"],
        original_claims["trust_generation"],
        original_claims["binding"],
        original_claims["policy_artifact"],
        original_claims["policy_digest"],
        original_claims["issued_at"],
        original_claims["not_before"],
        original_claims["expires_at"]
    ]);
    Ok([positional_binding, positional_claims])
}
#[test]
fn one_bit_bad_signature_wrong_domain_foreign_key_and_missing_latest_approval_are_denied()
-> TestResult {
    let bytes = bytes()?;
    let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
    let p = writer(&s, &c)?;
    let server = Server::new(&s)?;
    register(&s, &p, &server, true, 0)?;
    let base: Value = serde_json::from_slice(&server.raw()?)?;
    let clock = Clock::default();
    let deps = FormulaIssuerDependencies::new(&server, &server, &server, &clock);
    for case in 0..3 {
        let mut env = base.clone();
        let claims = base["signed_claims"].as_str().ok_or("claims")?;
        match case {
            0 => {
                let mut sig = hex::decode(env["signature_hex"].as_str().ok_or("sig")?)?;
                sig[0] ^= 1;
                env["signature_hex"] = json!(hex::encode(sig));
            }
            1 => server.resign(
                &mut env,
                claims,
                b"hwpx-agent.remote-credential-other-domain\0",
            ),
            _ => {
                let other =
                    Ed25519KeyPair::from_seed_unchecked(&[118; 32]).map_err(|_| "test key")?;
                env["signature_hex"] = json!(hex::encode(
                    other.sign(&[DOMAIN, claims.as_bytes()].concat()).as_ref()
                ));
            }
        }
        server.install(
            serde_json::to_vec(&env)?,
            ArtifactKind::Evidence,
            FORMULA_APPROVAL_MEDIA_TYPE,
        )?;
        assert!(
            StoredProductRequest::prepare_formula_with_issuer(&p, &deps, &request(&s, &bytes)?)
                .is_err()
        );
    }
    *server.proof.lock().map_err(|_| "proof")? = None;
    assert!(
        StoredProductRequest::prepare_formula_with_issuer(&p, &deps, &request(&s, &bytes)?)
            .is_err()
    );
    no_publication(&s)
}
#[test]
fn issuer_expiry_not_before_root_bounds_clock_failure_and_backwards_time_deny_cached_bytes()
-> TestResult {
    let bytes = bytes()?;
    let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
    let p = writer(&s, &c)?;
    let server = Server::new(&s)?;
    register(&s, &p, &server, true, 0)?;
    let clock = Clock::default();
    let deps = FormulaIssuerDependencies::new(&server, &server, &server, &clock);
    let prepared =
        StoredProductRequest::prepare_formula_with_issuer(&p, &deps, &request(&s, &bytes)?)?;
    for now in [0, 4, 5, 300, 1000, u64::MAX] {
        clock.value.store(now, Ordering::SeqCst);
        let called = std::cell::Cell::new(false);
        assert!(
            prepared
                .with_verified_bytes(&p, &deps, |_| called.set(true))
                .is_err()
        );
        assert!(!called.get());
    }
    clock.value.store(12, Ordering::SeqCst);
    clock.fail.store(true, Ordering::SeqCst);
    assert!(prepared.verify(&p, &deps).is_err());
    clock.fail.store(false, Ordering::SeqCst);
    clock
        .jump_at
        .store(clock.calls.load(Ordering::SeqCst) + 2, Ordering::SeqCst);
    clock.jump_to.store(11, Ordering::SeqCst);
    assert!(
        StoredProductRequest::prepare_formula_with_issuer(&p, &deps, &request(&s, &bytes)?)
            .is_err()
    );
    clock.jump_at.store(usize::MAX, Ordering::SeqCst);
    let base: Value = serde_json::from_slice(&server.raw()?)?;
    for case in 0..5 {
        let mut env = base.clone();
        let mut claims: Value =
            serde_json::from_str(env["signed_claims"].as_str().ok_or("claims")?)?;
        match case {
            0 => claims["issued_at"] = json!(4),
            1 => claims["issued_at"] = json!(7),
            2 => claims["not_before"] = json!(13),
            3 => claims["expires_at"] = json!(1001),
            _ => claims["expires_at"] = json!(607),
        }
        server.resign(&mut env, &serde_json::to_string(&claims)?, DOMAIN);
        server.install(
            serde_json::to_vec(&env)?,
            ArtifactKind::Evidence,
            FORMULA_APPROVAL_MEDIA_TYPE,
        )?;
        assert!(
            StoredProductRequest::prepare_formula_with_issuer(&p, &deps, &request(&s, &bytes)?)
                .is_err()
        );
    }
    no_publication(&s)
}
#[test]
fn key_revocation_same_counter_trust_change_and_mid_read_change_never_use_cached_root() -> TestResult
{
    let bytes = bytes()?;
    let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
    let p = writer(&s, &c)?;
    let server = Server::new(&s)?;
    register(&s, &p, &server, true, 0)?;
    let clock = Clock::default();
    let deps = FormulaIssuerDependencies::new(&server, &server, &server, &clock);
    let prepared =
        StoredProductRequest::prepare_formula_with_issuer(&p, &deps, &request(&s, &bytes)?)?;
    let other = Ed25519KeyPair::from_seed_unchecked(&[118; 32]).map_err(|_| "test key")?;
    for root in [
        trust(&s, &other, 1, 600)?,
        trust(&s, &server.pair, 2, 600)?,
        trust(&s, &server.pair, 1, 601)?,
    ] {
        *server.trust.lock().map_err(|_| "trust")? = root;
        let called = std::cell::Cell::new(false);
        assert!(
            prepared
                .with_verified_bytes(&p, &deps, |_| called.set(true))
                .is_err()
        );
        assert!(!called.get());
    }
    *server.trust.lock().map_err(|_| "trust")? = trust(&s, &server.pair, 1, 600)?;
    server.change_at.store(
        server.trust_calls.load(Ordering::SeqCst) + 1,
        Ordering::SeqCst,
    );
    assert!(
        StoredProductRequest::prepare_formula_with_issuer(&p, &deps, &request(&s, &bytes)?)
            .is_err()
    );
    server.change_at.store(usize::MAX, Ordering::SeqCst);
    server.deny_at.store(0, Ordering::SeqCst);
    assert!(prepared.verify(&p, &deps).is_err());
    no_publication(&s)
}
#[test]
fn proof_and_clock_revocation_immediately_before_candidate_callback_never_call_consumer()
-> TestResult {
    for clock_failure in [false, true] {
        let bytes = bytes()?;
        let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
        let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
        let p = writer(&s, &c)?;
        let server = Server::new(&s)?;
        register(&s, &p, &server, true, 0)?;
        let clock = Clock::default();
        let deps = FormulaIssuerDependencies::new(&server, &server, &server, &clock);
        let prepared =
            StoredProductRequest::prepare_formula_with_issuer(&p, &deps, &request(&s, &bytes)?)?;
        if clock_failure {
            clock
                .jump_at
                .store(clock.calls.load(Ordering::SeqCst) + 20, Ordering::SeqCst);
        } else {
            server.deny_at.store(
                server.trust_calls.load(Ordering::SeqCst) + 18,
                Ordering::SeqCst,
            );
        }
        let called = std::cell::Cell::new(false);
        assert!(
            prepared
                .with_verified_bytes(&p, &deps, |_| called.set(true))
                .is_err()
        );
        assert!(!called.get());
        no_publication(&s)?;
    }
    Ok(())
}
#[test]
fn approval_only_acl_quarantine_aead_and_latest_revocation_deny_fresh_and_cached_products()
-> TestResult {
    let bytes = bytes()?;
    let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
    let p = writer(&s, &c)?;
    let server = Server::new(&s)?;
    register(&s, &p, &server, true, 0)?;
    let clock = Clock::default();
    let deps = FormulaIssuerDependencies::new(&server, &server, &server, &clock);
    let proof = server
        .proof
        .lock()
        .map_err(|_| "proof")?
        .as_ref()
        .ok_or("proof")?
        .artifact;
    for id in [server.policy()?.artifact, proof] {
        s.artifacts.set_permissions(
            &s.owner,
            id,
            s.reader.subject(),
            BTreeSet::from([ArtifactPermission::Read]),
            8,
        )?;
    }
    let reader = s.provider()?;
    let prepared =
        StoredProductRequest::prepare_formula_with_issuer(&reader, &deps, &request(&s, &bytes)?)?;
    s.artifacts
        .set_permissions(&s.owner, proof, s.reader.subject(), BTreeSet::new(), 9)?;
    let called = std::cell::Cell::new(false);
    assert!(
        prepared
            .with_verified_bytes(&reader, &deps, |_| called.set(true))
            .is_err()
    );
    assert!(!called.get());
    s.artifacts.set_permissions(
        &s.owner,
        proof,
        s.reader.subject(),
        BTreeSet::from([ArtifactPermission::Read]),
        10,
    )?;
    prepared.verify(&reader, &deps)?;
    server.proof_revoked.store(true, Ordering::SeqCst);
    assert!(prepared.verify(&reader, &deps).is_err());
    server.proof_revoked.store(false, Ordering::SeqCst);
    s.blobs.tamper.store(true, Ordering::SeqCst);
    assert!(prepared.verify(&reader, &deps).is_err());
    s.blobs.tamper.store(false, Ordering::SeqCst);
    s.artifacts.quarantine(
        &s.owner,
        proof,
        artifact_service::QuarantineReason::parse("P119_SYNTHETIC_ONLY")?,
        11,
    )?;
    assert!(prepared.verify(&reader, &deps).is_err());
    assert!(
        StoredProductRequest::prepare_formula_with_issuer(&reader, &deps, &request(&s, &bytes)?)
            .is_err()
    );
    no_publication(&s)
}
#[test]
fn wrong_approval_media_role_and_artifact_alias_cannot_use_policy_or_other_domain_as_signature()
-> TestResult {
    let bytes = bytes()?;
    for (kind, media) in [
        (ArtifactKind::Evidence, "application/json"),
        (ArtifactKind::Result, FORMULA_APPROVAL_MEDIA_TYPE),
    ] {
        let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
        let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
        let p = writer(&s, &c)?;
        let server = Server::new(&s)?;
        register(&s, &p, &server, true, 0)?;
        let raw = server.raw()?;
        // Whole raw bytes dedup is preserved: use semantically equivalent new envelope whitespace.
        let mut changed = raw;
        changed.push(b' ');
        server.install(changed, kind, media)?;
        let clock = Clock::default();
        let deps = FormulaIssuerDependencies::new(&server, &server, &server, &clock);
        assert!(
            StoredProductRequest::prepare_formula_with_issuer(&p, &deps, &request(&s, &bytes)?)
                .is_err()
        );
        for id in [s.result, server.policy()?.artifact] {
            *server.proof.lock().map_err(|_| "proof")? = Some(FormulaApprovalVersion {
                artifact: id,
                digest: server.policy()?.digest,
            });
            assert!(
                StoredProductRequest::prepare_formula_with_issuer(&p, &deps, &request(&s, &bytes)?)
                    .is_err()
            );
        }
        no_publication(&s)?;
    }
    Ok(())
}
#[test]
fn signed_data_never_overrides_denied_targets_native_protection_or_invalid_second_section()
-> TestResult {
    for (bytes, allow) in [
        (bytes()?, false),
        (current(&bytes()?)?, false),
        (
            fixture::protect(&bytes()?, "Contents/section1.xml", 1)?,
            true,
        ),
        (
            fixture::protect(&current(&bytes()?)?, "Contents/section1.xml", 1)?,
            true,
        ),
        (
            fixture::two_sections(&fixture::batch("5")?, &fixture::batch("NON-NUMERIC")?)?,
            true,
        ),
    ] {
        let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
        let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
        let p = writer(&s, &c)?;
        let server = Server::new(&s)?;
        register(&s, &p, &server, allow, 0)?;
        let clock = Clock::default();
        let deps = FormulaIssuerDependencies::new(&server, &server, &server, &clock);
        assert!(
            StoredProductRequest::prepare_formula_with_issuer(&p, &deps, &request(&s, &bytes)?)
                .is_err()
        );
        no_publication(&s)?;
    }
    Ok(())
}
#[test]
fn public_request_cannot_supply_issuer_approval_keys_clock_or_signature_before_server_reads()
-> TestResult {
    let bytes = bytes()?;
    let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
    let p = writer(&s, &c)?;
    let server = Server::new(&s)?;
    register(&s, &p, &server, true, 0)?;
    let clock = Clock::default();
    let deps = FormulaIssuerDependencies::new(&server, &server, &server, &clock);
    let base: Value = serde_json::from_slice(&request(&s, &bytes)?)?;
    let audit = s.metadata.audit_events()?.len();
    for key in [
        "issuer",
        "approval",
        "public_key",
        "signature_hex",
        "trust_generation",
        "now",
    ] {
        let mut v = base.clone();
        v[key] = json!(true);
        assert!(
            StoredProductRequest::prepare_formula_with_issuer(&p, &deps, &serde_json::to_vec(&v)?)
                .is_err()
        );
    }
    assert_eq!(server.trust_calls.load(Ordering::SeqCst), 0);
    assert_eq!(s.metadata.audit_events()?.len(), audit);
    no_publication(&s)
}
#[test]
fn server_trust_requires_explicit_nonempty_unique_keys_exact_scope_generation_and_lifetime()
-> TestResult {
    let s = StoredFixture::new(&bytes()?, ArtifactKind::Result, false)?;
    let server = Server::new(&s)?;
    for case in 0..9 {
        let key =
            FormulaIssuerKey::new("key".into(), server.pair.public_key().as_ref().try_into()?)?;
        let mut d = FormulaIssuerTrustDraft {
            tenant: s.owner.tenant_id(),
            project: s.project,
            issuer: "issuer".into(),
            generation: 1,
            valid_from: 5,
            valid_until: 1000,
            max_approval_lifetime: 600,
            active_keys: vec![key.clone()],
        };
        match case {
            0 => d.active_keys.clear(),
            1 => d.active_keys.push(key),
            2 => d.active_keys = vec![key; 9],
            3 => d.generation = 0,
            4 => d.generation = u64::MAX,
            5 => d.issuer = "bad\nissuer".into(),
            6 => d.valid_until = 5,
            7 => d.max_approval_lifetime = 0,
            _ => d.max_approval_lifetime = 86401,
        }
        assert_eq!(
            FormulaIssuerTrust::new(d).err(),
            Some(FormulaIssuerError::Trust)
        );
    }
    assert!(FormulaIssuerKey::new("key".into(), [0; 32]).is_err());
    assert!(FormulaIssuerKey::new("bad key".into(), [119; 32]).is_err());
    assert_eq!(
        format!("{:?}", server.trust.lock().map_err(|_| "trust")?),
        "FormulaIssuerTrust(<redacted>)"
    );
    Ok(())
}

#[test]
fn cached_signed_product_denies_five_foreign_scopes_new_policy_and_old_signature_replay()
-> TestResult {
    let bytes = bytes()?;
    let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
    let p = writer(&s, &c)?;
    let server = Server::new(&s)?;
    register(&s, &p, &server, true, 0)?;
    let clock = Clock::default();
    let deps = FormulaIssuerDependencies::new(&server, &server, &server, &clock);
    let prepared =
        StoredProductRequest::prepare_formula_with_issuer(&p, &deps, &request(&s, &bytes)?)?;
    for case in 0..5 {
        let tenant = if case == 4 {
            TenantId::new(uuid::Uuid::from_u128(11999))?
        } else {
            s.owner.tenant_id()
        };
        let subject = if case == 3 {
            s.reader.subject()
        } else {
            s.owner.subject()
        };
        let actor = RequestContext::new(tenant, subject, [AuthScope::DocumentRead]);
        let revision_actor = RevisionRequestContext::new(tenant, subject);
        let project = if case == 2 {
            revision_service::ProjectId::generate()
        } else {
            s.project
        };
        let branch = if case == 1 {
            revision_service::BranchId::generate()
        } else {
            s.branch
        };
        let document = if case == 0 {
            "other-document"
        } else {
            "actual-form-document"
        };
        let other = StoredFormProvider::bind(
            &s.artifacts,
            &s.revisions,
            &actor,
            &revision_actor,
            project,
            branch,
            DocumentId::parse(document)?,
        )?;
        let called = std::cell::Cell::new(false);
        assert!(
            prepared
                .with_verified_bytes(&other, &deps, |_| called.set(true))
                .is_err()
        );
        assert!(!called.get());
    }
    let old_approval = server.raw()?;
    register(&s, &p, &server, true, 1)?;
    assert_eq!(server.policy()?.binding.policy_generation, 2);
    let called = std::cell::Cell::new(false);
    assert!(
        prepared
            .with_verified_bytes(&p, &deps, |_| called.set(true))
            .is_err()
    );
    assert!(!called.get());
    let fresh =
        StoredProductRequest::prepare_formula_with_issuer(&p, &deps, &request(&s, &bytes)?)?;
    assert_eq!(
        fresh.with_verified_bytes(&p, &deps, <[u8]>::to_vec)?,
        current(&bytes)?
    );
    server.install(
        old_approval,
        ArtifactKind::Evidence,
        FORMULA_APPROVAL_MEDIA_TYPE,
    )?;
    assert!(
        StoredProductRequest::prepare_formula_with_issuer(&p, &deps, &request(&s, &bytes)?)
            .is_err()
    );
    let called = std::cell::Cell::new(false);
    assert!(
        fresh
            .with_verified_bytes(&p, &deps, |_| called.set(true))
            .is_err()
    );
    assert!(!called.get());
    no_publication(&s)
}

#[derive(Debug)]
struct ApprovalTamperBlob {
    inner: FaultBlob,
    target: ObjectKey,
    matches: Arc<AtomicUsize>,
}
impl EncryptedBlobStore for ApprovalTamperBlob {
    fn put_if_absent(
        &self,
        key: &ObjectKey,
        bytes: &[u8],
    ) -> Result<(), artifact_service::ArtifactError> {
        self.inner.put_if_absent(key, bytes)
    }
    fn get(&self, key: &ObjectKey) -> Result<Option<Vec<u8>>, artifact_service::ArtifactError> {
        let mut bytes = self.inner.get(key)?;
        if key == &self.target
            && let Some(b) = &mut bytes
            && let Some(first) = b.first_mut()
        {
            *first ^= 1;
            self.matches.fetch_add(1, Ordering::SeqCst);
        }
        Ok(bytes)
    }
    fn relocate_if_absent(
        &self,
        source: &ObjectKey,
        target: &ObjectKey,
    ) -> Result<(), artifact_service::ArtifactError> {
        self.inner.relocate_if_absent(source, target)
    }
}
#[test]
fn approval_only_aead_tamper_denies_candidate_with_source_and_original_policy_still_valid()
-> TestResult {
    let bytes = bytes()?;
    let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
    let p = writer(&s, &c)?;
    let server = Server::new(&s)?;
    register(&s, &p, &server, true, 0)?;
    let clock = Clock::default();
    let deps = FormulaIssuerDependencies::new(&server, &server, &server, &clock);
    let prepared =
        StoredProductRequest::prepare_formula_with_issuer(&p, &deps, &request(&s, &bytes)?)?;
    let source = p.import_actual_forms(s.head, 12)?;
    let proof = server
        .proof
        .lock()
        .map_err(|_| "proof")?
        .clone()
        .ok_or("proof")?;
    assert_ne!(proof.digest, server.policy()?.digest);
    assert_ne!(proof.digest, ContentDigest::of(&bytes));
    let matches = Arc::new(AtomicUsize::new(0));
    let r = KeyReference::parse("fixture.p45-aes")?;
    let artifacts = ArtifactService::new(
        s.metadata.clone(),
        ApprovalTamperBlob {
            inner: s.blobs.clone(),
            target: ObjectKey::for_artifact(
                s.owner.tenant_id(),
                ArtifactKind::Evidence,
                artifact_service::StorageState::Available,
                proof.digest,
            )?,
            matches: matches.clone(),
        },
        FixtureScanner { unavailable: false },
        Aes256GcmKeyring::new(r.clone(), [(r, [45; 32])])?,
        DownloadSigner::new(
            "https://fixture.example.test/download",
            KeyReference::parse("fixture.p45-hmac")?,
            &[46; 32],
            60,
        )?,
        ArtifactServiceConfig::new(32 * 1024 * 1024, 60)?,
    );
    let corrupt = StoredFormProvider::bind(
        &artifacts,
        &s.revisions,
        &s.owner,
        &c,
        s.project,
        s.branch,
        DocumentId::parse("actual-form-document")?,
    )?;
    source.verify(&corrupt, 12)?;
    source.bind_stored_formula_policy(&corrupt, &server, 12)?;
    assert_eq!(matches.load(Ordering::SeqCst), 0);
    let called = std::cell::Cell::new(false);
    assert!(
        prepared
            .with_verified_bytes(&corrupt, &deps, |_| called.set(true))
            .is_err()
    );
    assert!(!called.get());
    assert!(matches.load(Ordering::SeqCst) > 0);
    assert!(
        StoredProductRequest::prepare_formula_with_issuer(&corrupt, &deps, &request(&s, &bytes)?)
            .is_err()
    );
    no_publication(&s)
}
