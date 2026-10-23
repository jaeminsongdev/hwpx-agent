//! Synthetic writer/registry/clock/custody; real source generation, Ed25519, AEAD and unchanged consumer.
use super::*;
use artifact_service::{AuthScope, RequestContext, SubjectDigest};
use hwpx_agent_cli::form_stored_provider::actual_import::source_policy::formulas::issuer::registry::{
    RegistryFormulaApprovalProvider, RegistryFormulaTrustProvider, provision::*};
use revision_service::{ProjectId, RevisionError, postgres::source_formula_policy::issuer_registry::{
    FormulaApprovalReadRequest, FormulaApprovalRecord, FormulaIssuerRegistryRepository, FormulaIssuerTrustRecord}};
use uuid::Uuid;

fn denied<T>(
    result: Result<T, FormulaIssuerWorkflowFailure>,
) -> AnyResult<FormulaIssuerWorkflowFailure> {
    match result {
        Err(error) => Ok(error),
        Ok(_) => Err("issuer operation unexpectedly accepted".into()),
    }
}

struct Registry<'a> {
    s: &'a StoredFixture,
    root: Mutex<Option<FormulaIssuerTrustRecord>>,
    approval: Mutex<Option<FormulaApprovalRecord>>,
    root_mode: AtomicUsize,
    approval_mode: AtomicUsize,
    root_writes: AtomicUsize,
    approval_writes: AtomicUsize,
    read_denied: AtomicBool,
    preflight_denied: AtomicBool,
    root_read_drift: AtomicBool,
    approval_read_drift: AtomicBool,
}
impl<'a> Registry<'a> {
    fn new(s: &'a StoredFixture) -> Self {
        Self {
            s,
            root: Mutex::new(None),
            approval: Mutex::new(None),
            root_mode: AtomicUsize::new(0),
            approval_mode: AtomicUsize::new(0),
            root_writes: AtomicUsize::new(0),
            approval_writes: AtomicUsize::new(0),
            read_denied: AtomicBool::new(false),
            preflight_denied: AtomicBool::new(false),
            root_read_drift: AtomicBool::new(false),
            approval_read_drift: AtomicBool::new(false),
        }
    }
    fn authorized(&self, ctx: &RevisionRequestContext, project: ProjectId) -> bool {
        ctx.tenant_id() == self.s.owner.tenant_id()
            && project == self.s.project
            && [self.s.owner.subject(), self.s.reader.subject()].contains(&ctx.subject())
            && !self.read_denied.load(Ordering::SeqCst)
    }
}
impl FormulaIssuerRegistryRepository for Registry<'_> {
    fn read_trust(
        &self,
        ctx: &RevisionRequestContext,
        project: ProjectId,
    ) -> Result<FormulaIssuerTrustRecord, RevisionError> {
        if !self.authorized(ctx, project) {
            return Err(RevisionError::NotFound);
        }
        let mut row = self
            .root
            .lock()
            .map_err(|_| RevisionError::RepositoryFailure)?
            .clone()
            .ok_or(RevisionError::NotFound)?;
        if self.root_read_drift.load(Ordering::SeqCst) {
            row.creator = SubjectDigest::from_authenticated_subject("drift-owner")
                .map_err(|_| RevisionError::RepositoryFailure)?;
        }
        Ok(row)
    }
    fn read_approval(
        &self,
        ctx: &RevisionRequestContext,
        req: &FormulaApprovalReadRequest,
    ) -> Result<FormulaApprovalRecord, RevisionError> {
        if !self.authorized(ctx, req.project()) || req.head() != self.s.head {
            return Err(RevisionError::NotFound);
        }
        let mut row = self
            .approval
            .lock()
            .map_err(|_| RevisionError::RepositoryFailure)?
            .clone()
            .ok_or(RevisionError::NotFound)?;
        row.validate_for(ctx, req)?;
        if self.approval_read_drift.load(Ordering::SeqCst) {
            row.creator = SubjectDigest::from_authenticated_subject("drift-owner")
                .map_err(|_| RevisionError::RepositoryFailure)?;
        }
        Ok(row)
    }
}
impl FormulaIssuerRegistryWriteGateway for Registry<'_> {
    fn authorize_root(
        &self,
        ctx: &RevisionRequestContext,
        project: ProjectId,
    ) -> Result<(), FormulaIssuerError> {
        if !self.authorized(ctx, project)
            || ctx.subject() != self.s.owner.subject()
            || self.preflight_denied.load(Ordering::SeqCst)
        {
            return Err(FormulaIssuerError::Repository);
        }
        Ok(())
    }
    fn authorize_approval(
        &self,
        ctx: &RevisionRequestContext,
        scope: &PolicyReadScope,
    ) -> Result<(), FormulaIssuerError> {
        if scope.tenant() != ctx.tenant_id()
            || scope.subject() != ctx.subject()
            || scope.head() != self.s.head
        {
            return Err(FormulaIssuerError::Binding);
        }
        self.authorize_root(ctx, scope.project())
    }
    fn register_trust(
        &self,
        ctx: &RevisionRequestContext,
        row: &FormulaIssuerTrustRecord,
        expected: u64,
    ) -> Result<(), RegistryGatewayError> {
        self.root_writes.fetch_add(1, Ordering::SeqCst);
        if !self.authorized(ctx, row.project)
            || ctx.subject() != self.s.owner.subject()
            || row.creator != ctx.subject()
            || self
                .root
                .lock()
                .map_err(|_| RegistryGatewayError::Denied)?
                .as_ref()
                .map_or(0, |r| r.generation)
                != expected
        {
            return Err(RegistryGatewayError::Denied);
        }
        match self.root_mode.load(Ordering::SeqCst) {
            1 => return Err(RegistryGatewayError::Denied),
            2 => {
                *self.root.lock().map_err(|_| RegistryGatewayError::Denied)? = Some(row.clone());
                return Err(RegistryGatewayError::CommitOutcomeUnknown);
            }
            _ => {}
        }
        *self.root.lock().map_err(|_| RegistryGatewayError::Denied)? = Some(row.clone());
        if self.root_mode.load(Ordering::SeqCst) == 3 {
            return Err(RegistryGatewayError::AcknowledgedReceiptMismatch);
        }
        if self.root_mode.load(Ordering::SeqCst) == 4 {
            self.root_read_drift.store(true, Ordering::SeqCst);
        }
        Ok(())
    }
    fn register_approval(
        &self,
        ctx: &RevisionRequestContext,
        scope: &PolicyReadScope,
        row: &FormulaApprovalRecord,
        expected: u64,
    ) -> Result<(), RegistryGatewayError> {
        self.approval_writes.fetch_add(1, Ordering::SeqCst);
        let root = self
            .read_trust(ctx, scope.project())
            .map_err(|_| RegistryGatewayError::Denied)?;
        if ctx.subject() != self.s.owner.subject()
            || row.creator != ctx.subject()
            || scope.head() != self.s.head
            || row.trust_version != root.version
            || row.trust_generation != root.generation
            || self
                .approval
                .lock()
                .map_err(|_| RegistryGatewayError::Denied)?
                .as_ref()
                .map_or(0, |r| r.generation)
                != expected
        {
            return Err(RegistryGatewayError::Denied);
        }
        match self.approval_mode.load(Ordering::SeqCst) {
            1 => return Err(RegistryGatewayError::Denied),
            2 => {
                *self
                    .approval
                    .lock()
                    .map_err(|_| RegistryGatewayError::Denied)? = Some(row.clone());
                return Err(RegistryGatewayError::CommitOutcomeUnknown);
            }
            _ => {}
        }
        *self
            .approval
            .lock()
            .map_err(|_| RegistryGatewayError::Denied)? = Some(row.clone());
        if self.approval_mode.load(Ordering::SeqCst) == 3 {
            return Err(RegistryGatewayError::AcknowledgedReceiptMismatch);
        }
        if self.approval_mode.load(Ordering::SeqCst) == 4 {
            self.approval_read_drift.store(true, Ordering::SeqCst);
        }
        Ok(())
    }
}
struct Signer<'a> {
    pair: &'a Ed25519KeyPair,
    calls: AtomicUsize,
    mode: usize,
    hook: Option<Box<dyn Fn() + Send + Sync + 'a>>,
}
impl<'a> Signer<'a> {
    fn new(pair: &'a Ed25519KeyPair) -> Self {
        Self {
            pair,
            calls: AtomicUsize::new(0),
            mode: 0,
            hook: None,
        }
    }
}
impl FormulaApprovalSigner for Signer<'_> {
    fn key_id(&self) -> &str {
        if self.mode == 1 {
            "missing-key"
        } else {
            "P119-test-key"
        }
    }
    fn sign(&self, raw: &[u8]) -> Result<[u8; 64], FormulaIssuerError> {
        self.calls.fetch_add(1, Ordering::SeqCst);
        if let Some(hook) = &self.hook {
            hook();
        }
        if self.mode == 2 {
            return Ok([0; 64]);
        }
        if self.mode == 3 {
            return Err(FormulaIssuerError::Signature);
        }
        self.pair
            .sign(raw)
            .as_ref()
            .try_into()
            .map_err(|_| FormulaIssuerError::Signature)
    }
}
fn draft(s: &StoredFixture, pair: &Ed25519KeyPair) -> AnyResult<FormulaIssuerTrustDraft> {
    Ok(FormulaIssuerTrustDraft {
        tenant: s.owner.tenant_id(),
        project: s.project,
        issuer: "P119-test-issuer".into(),
        generation: 1,
        valid_from: 5,
        valid_until: 1000,
        max_approval_lifetime: 600,
        active_keys: vec![FormulaIssuerKey::new(
            "P119-test-key".into(),
            pair.public_key().as_ref().try_into()?,
        )?],
    })
}
struct Capture<'a, 'b, F> {
    server: &'a Server<'b>,
    callback: F,
    result: Mutex<Option<Result<FormulaIssuerProvisioningReceipt, FormulaIssuerWorkflowFailure>>>,
    scope: Mutex<Option<PolicyReadScope>>,
}
impl<'a, 'b, F> Capture<'a, 'b, F> {
    fn new(server: &'a Server<'b>, callback: F) -> Self {
        Self {
            server,
            callback,
            result: Mutex::new(None),
            scope: Mutex::new(None),
        }
    }
    fn take(
        &self,
    ) -> AnyResult<Result<FormulaIssuerProvisioningReceipt, FormulaIssuerWorkflowFailure>> {
        self.result
            .lock()
            .map_err(|_| "capture")?
            .take()
            .ok_or("capture".into())
    }
}
impl<F> FormulaPolicyRegistrationRepository for Capture<'_, '_, F>
where
    F: Fn(
            &PolicyReadScope,
            &FormulaPolicyRegistrationRecord,
        ) -> Result<FormulaIssuerProvisioningReceipt, FormulaIssuerWorkflowFailure>
        + Send
        + Sync,
{
    fn register_formula_policy(
        &self,
        scope: &PolicyReadScope,
        record: &FormulaPolicyRegistrationRecord,
    ) -> Result<SourcePolicyVersion, FormulaPolicyRegistrationError> {
        let row = self.server.register_formula_policy(scope, record)?;
        *self
            .scope
            .lock()
            .map_err(|_| FormulaPolicyRegistrationError::Repository)? = Some(scope.clone());
        *self
            .result
            .lock()
            .map_err(|_| FormulaPolicyRegistrationError::Repository)? =
            Some((self.callback)(scope, record));
        Ok(row)
    }
}
fn generate(
    s: &StoredFixture,
    p: &Provider<'_>,
    capture: &impl FormulaPolicyRegistrationRepository,
) -> TestResult {
    let source = p.import_actual_forms(s.head, 4)?;
    let fields = source.import_field_ranges(p, 4)?;
    let meanings = fields.import_semantics(p, 4)?;
    let decisions: Vec<_> = meanings
        .observations()
        .iter()
        .filter(|m| matches!(m.meaning, ImportedFieldMeaning::TableFormula { .. }))
        .map(|m| FormulaPolicyDecision::new(m.reference_id.clone(), true))
        .collect();
    source
        .prepare_formula_policy_registration(p, &decisions, 0, 5)?
        .register(p, capture, 6)?;
    Ok(())
}
fn evidence_count(s: &StoredFixture) -> AnyResult<usize> {
    Ok(s.metadata
        .audit_events()?
        .iter()
        .filter(|e| e.event == "artifact.ingested")
        .count())
}

#[test]
fn provision_genuine_root_and_approval_drive_original_changed_and_current_product() -> TestResult {
    let original = bytes()?;
    for input in [original.clone(), current(&original)?] {
        let s = StoredFixture::new(&input, ArtifactKind::Result, false)?;
        let ctx = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
        let p = writer(&s, &ctx)?;
        let server = Server::new(&s)?;
        let store = Registry::new(&s);
        let clock = Clock::default();
        let service = RegistryFormulaProvisioner::new(
            &store,
            &store,
            &server,
            &s.artifacts,
            &s.owner,
            &clock,
        );
        let root = service.install_trust(draft(&s, &server.pair)?, 0)?;
        assert!(root.qualification().contains("NOT_production_key_custody"));
        let signer = Signer::new(&server.pair);
        let capture = Capture::new(
            &server,
            |scope: &PolicyReadScope, record: &FormulaPolicyRegistrationRecord| {
                service.issue_approval(scope, record, &signer, 0, 60)
            },
        );
        generate(&s, &p, &capture)?;
        let approval = capture.take()??;
        assert_ne!(root.artifact(), approval.artifact());
        assert_eq!(signer.calls.load(Ordering::SeqCst), 1);
        let approvals = RegistryFormulaApprovalProvider::new(&store);
        let trust = RegistryFormulaTrustProvider::new(&store, &s.artifacts, &s.owner, &clock);
        let deps = FormulaIssuerDependencies::new(&server, &approvals, &trust, &clock);
        let prepared =
            StoredProductRequest::prepare_formula_with_issuer(&p, &deps, &request(&s, &input)?)?;
        assert_eq!(
            prepared.with_verified_bytes(&p, &deps, <[u8]>::to_vec)?,
            current(&original)?
        );
        assert!(prepared.require_current_product_route(&p, &deps).is_err());
        assert_eq!(
            format!("{approval:?}"),
            "FormulaIssuerProvisioningReceipt(<redacted>)"
        );
        no_publication(&s)?;
    }
    Ok(())
}
#[test]
fn provision_root_scope_time_and_generation_fail_before_artifact_or_registry() -> TestResult {
    let s = StoredFixture::new(&bytes()?, ArtifactKind::Result, false)?;
    let server = Server::new(&s)?;
    let store = Registry::new(&s);
    let clock = Clock::default();
    let service =
        RegistryFormulaProvisioner::new(&store, &store, &server, &s.artifacts, &s.owner, &clock);
    let before = evidence_count(&s)?;
    for mode in 0..8 {
        let mut d = draft(&s, &server.pair)?;
        match mode {
            0 => d.generation = 2,
            1 => d.valid_from = 13,
            2 => d.valid_until = 12,
            3 => d.max_approval_lifetime = 0,
            4 => d.active_keys.clear(),
            5 => d.valid_until = u64::MAX,
            6 => d.tenant = artifact_service::TenantId::new(Uuid::new_v4())?,
            _ => store.preflight_denied.store(true, Ordering::SeqCst),
        }
        let err = denied(service.install_trust(d, 0))?;
        assert_eq!(err.write_outcome(), FormulaIssuerWriteOutcome::NotAttempted);
        assert_eq!(err.artifact(), None);
    }
    store.preflight_denied.store(false, Ordering::SeqCst);
    let ctx = RequestContext::new(
        s.owner.tenant_id(),
        s.owner.subject(),
        [AuthScope::DocumentWrite],
    );
    let no_read =
        RegistryFormulaProvisioner::new(&store, &store, &server, &s.artifacts, &ctx, &clock);
    assert!(no_read.install_trust(draft(&s, &server.pair)?, 0).is_err());
    assert_eq!(evidence_count(&s)?, before);
    assert_eq!(store.root_writes.load(Ordering::SeqCst), 0);
    no_publication(&s)
}
#[test]
fn provision_root_failure_keeps_artifact_and_distinguishes_commit_outcome() -> TestResult {
    for mode in 1..5 {
        let s = StoredFixture::new(&bytes()?, ArtifactKind::Result, false)?;
        let server = Server::new(&s)?;
        let store = Registry::new(&s);
        let clock = Clock::default();
        store.root_mode.store(mode, Ordering::SeqCst);
        let service = RegistryFormulaProvisioner::new(
            &store,
            &store,
            &server,
            &s.artifacts,
            &s.owner,
            &clock,
        );
        let err = denied(service.install_trust(draft(&s, &server.pair)?, 0))?;
        assert_eq!(
            err.write_outcome(),
            match mode {
                1 => FormulaIssuerWriteOutcome::Denied,
                2 => FormulaIssuerWriteOutcome::CommitOutcomeUnknown,
                _ => FormulaIssuerWriteOutcome::Acknowledged,
            }
        );
        let id = err.artifact().ok_or("residue identity")?;
        assert!(!s.artifacts.download(&s.owner, id, 12)?.is_empty());
        assert_eq!(store.root_writes.load(Ordering::SeqCst), 1);
        assert_eq!(
            format!("{err:?}"),
            "FormulaIssuerWorkflowFailure(<redacted>)"
        );
        no_publication(&s)?;
    }
    Ok(())
}
#[test]
fn provision_signer_key_signature_lifetime_and_clock_fail_closed_before_approval_write()
-> TestResult {
    for mode in 0..8 {
        let s = StoredFixture::new(&bytes()?, ArtifactKind::Result, false)?;
        let ctx = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
        let p = writer(&s, &ctx)?;
        let server = Server::new(&s)?;
        let store = Registry::new(&s);
        let clock = Clock::default();
        let service = RegistryFormulaProvisioner::new(
            &store,
            &store,
            &server,
            &s.artifacts,
            &s.owner,
            &clock,
        );
        let mut root_draft = draft(&s, &server.pair)?;
        if mode == 6 {
            root_draft.valid_from = 0;
        }
        service.install_trust(root_draft, 0)?;
        let mut signer = Signer::new(&server.pair);
        signer.mode = match mode {
            0 => 1,
            1 => 2,
            2 => 3,
            _ => 0,
        };
        if mode == 6 {
            signer.hook = Some(Box::new(|| {
                clock.value.store(0, Ordering::SeqCst);
            }));
        }
        let capture = Capture::new(
            &server,
            |scope: &PolicyReadScope, record: &FormulaPolicyRegistrationRecord| {
                if mode == 5 {
                    clock.fail.store(true, Ordering::SeqCst);
                }
                if mode == 7 {
                    store.preflight_denied.store(true, Ordering::SeqCst);
                }
                service.issue_approval(
                    scope,
                    record,
                    &signer,
                    0,
                    match mode {
                        3 => 0,
                        4 => 601,
                        _ => 60,
                    },
                )
            },
        );
        generate(&s, &p, &capture)?;
        let err = denied(capture.take()?)?;
        assert_eq!(err.artifact(), None);
        assert_eq!(err.write_outcome(), FormulaIssuerWriteOutcome::NotAttempted);
        assert_eq!(store.approval_writes.load(Ordering::SeqCst), 0);
        assert_eq!(
            signer.calls.load(Ordering::SeqCst),
            usize::from(matches!(mode, 1 | 2 | 6))
        );
        no_publication(&s)?;
    }
    Ok(())
}
#[test]
fn provision_same_generation_root_or_policy_drift_stops_before_approval_ingest() -> TestResult {
    for mode in 0..2 {
        let s = StoredFixture::new(&bytes()?, ArtifactKind::Result, false)?;
        let ctx = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
        let p = writer(&s, &ctx)?;
        let server = Server::new(&s)?;
        let store = Registry::new(&s);
        let clock = Clock::default();
        let service = RegistryFormulaProvisioner::new(
            &store,
            &store,
            &server,
            &s.artifacts,
            &s.owner,
            &clock,
        );
        service.install_trust(draft(&s, &server.pair)?, 0)?;
        let mut signer = Signer::new(&server.pair);
        signer.hook = Some(Box::new(|| {
            if mode == 0 {
                store.root_read_drift.store(true, Ordering::SeqCst);
            } else if let Ok(mut row) = server.policy.lock()
                && let Some(row) = row.as_mut()
            {
                row.digest = ContentDigest::of(b"same-generation-policy-drift");
            }
        }));
        let capture = Capture::new(
            &server,
            |scope: &PolicyReadScope, record: &FormulaPolicyRegistrationRecord| {
                service.issue_approval(scope, record, &signer, 0, 60)
            },
        );
        generate(&s, &p, &capture)?;
        let err = denied(capture.take()?)?;
        assert_eq!(err.artifact(), None);
        assert_eq!(store.approval_writes.load(Ordering::SeqCst), 0);
        no_publication(&s)?;
    }
    Ok(())
}
#[test]
fn provision_approval_write_and_postcommit_failures_preserve_exact_outcome_without_retry()
-> TestResult {
    for mode in 1..5 {
        let s = StoredFixture::new(&bytes()?, ArtifactKind::Result, false)?;
        let ctx = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
        let p = writer(&s, &ctx)?;
        let server = Server::new(&s)?;
        let store = Registry::new(&s);
        let clock = Clock::default();
        let service = RegistryFormulaProvisioner::new(
            &store,
            &store,
            &server,
            &s.artifacts,
            &s.owner,
            &clock,
        );
        service.install_trust(draft(&s, &server.pair)?, 0)?;
        store.approval_mode.store(mode, Ordering::SeqCst);
        let signer = Signer::new(&server.pair);
        let capture = Capture::new(
            &server,
            |scope: &PolicyReadScope, record: &FormulaPolicyRegistrationRecord| {
                service.issue_approval(scope, record, &signer, 0, 60)
            },
        );
        generate(&s, &p, &capture)?;
        let err = denied(capture.take()?)?;
        assert_eq!(
            err.write_outcome(),
            match mode {
                1 => FormulaIssuerWriteOutcome::Denied,
                2 => FormulaIssuerWriteOutcome::CommitOutcomeUnknown,
                _ => FormulaIssuerWriteOutcome::Acknowledged,
            }
        );
        assert!(
            !s.artifacts
                .download(&s.owner, err.artifact().ok_or("residue")?, 12)?
                .is_empty()
        );
        assert_eq!(store.approval_writes.load(Ordering::SeqCst), 1);
        no_publication(&s)?;
    }
    Ok(())
}
#[test]
fn provision_scanner_and_aead_failures_never_register_root() -> TestResult {
    for unverified in [true, false] {
        let s = StoredFixture::new(&bytes()?, ArtifactKind::Result, unverified)?;
        let server = Server::new(&s)?;
        let store = Registry::new(&s);
        let clock = Clock::default();
        if !unverified {
            s.blobs.tamper.store(true, Ordering::SeqCst);
        }
        let service = RegistryFormulaProvisioner::new(
            &store,
            &store,
            &server,
            &s.artifacts,
            &s.owner,
            &clock,
        );
        let err = denied(service.install_trust(draft(&s, &server.pair)?, 0))?;
        assert_eq!(err.stage(), FormulaIssuerWorkflowStage::ArtifactReadback);
        assert!(err.artifact().is_some());
        assert_eq!(err.write_outcome(), FormulaIssuerWriteOutcome::NotAttempted);
        assert_eq!(store.root_writes.load(Ordering::SeqCst), 0);
        s.blobs.tamper.store(false, Ordering::SeqCst);
        no_publication(&s)?;
    }
    Ok(())
}
#[test]
fn provision_live_registry_revocation_blocks_original_consumer_callback_and_publication()
-> TestResult {
    let input = bytes()?;
    let s = StoredFixture::new(&input, ArtifactKind::Result, false)?;
    let ctx = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
    let p = writer(&s, &ctx)?;
    let server = Server::new(&s)?;
    let store = Registry::new(&s);
    let clock = Clock::default();
    let service =
        RegistryFormulaProvisioner::new(&store, &store, &server, &s.artifacts, &s.owner, &clock);
    service.install_trust(draft(&s, &server.pair)?, 0)?;
    let signer = Signer::new(&server.pair);
    let capture = Capture::new(
        &server,
        |scope: &PolicyReadScope, record: &FormulaPolicyRegistrationRecord| {
            service.issue_approval(scope, record, &signer, 0, 60)
        },
    );
    generate(&s, &p, &capture)?;
    capture.take()??;
    let approvals = RegistryFormulaApprovalProvider::new(&store);
    let trust = RegistryFormulaTrustProvider::new(&store, &s.artifacts, &s.owner, &clock);
    let deps = FormulaIssuerDependencies::new(&server, &approvals, &trust, &clock);
    let prepared =
        StoredProductRequest::prepare_formula_with_issuer(&p, &deps, &request(&s, &input)?)?;
    store.read_denied.store(true, Ordering::SeqCst);
    let called = AtomicBool::new(false);
    assert!(
        prepared
            .with_verified_bytes(&p, &deps, |_| called.store(true, Ordering::SeqCst))
            .is_err()
    );
    assert!(!called.load(Ordering::SeqCst));
    assert!(prepared.require_current_product_route(&p, &deps).is_err());
    no_publication(&s)
}
