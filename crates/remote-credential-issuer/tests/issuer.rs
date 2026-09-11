use std::fmt;
use std::fs;
use std::io::{Cursor, Read, Write};
use std::net::{Ipv4Addr, SocketAddr};
use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};
use std::sync::{Arc, Barrier, Mutex, MutexGuard};
use std::time::Duration;

use base64::{Engine as _, engine::general_purpose::URL_SAFE_NO_PAD};
use rcgen::{CertifiedKey, generate_simple_self_signed};
use remote_credential_broker::{CredentialIssuerTransport, IssuerAuthorization};
use remote_credential_broker::{IssuerReply, parse_issuer_response};
use remote_credential_issuer::{
    AppendOnlyIssuerStateStore, CredentialIssuer, CredentialIssuerTlsServer, CredentialTokenSigner,
    ExchangeStatus, IssuerBindScope, IssuerError, IssuerPolicy, IssuerStateStore,
    IssuerTlsServerConfig, IssuerTlsServerFailure, SignerFailure, StoreFailure, StoredRecord,
    StoredRevision, VerificationKey, serve_one,
};
use remote_credential_lifecycle::{
    CredentialState, IssuerKey, LifecycleOperation, LifecyclePolicy, begin_transition,
    verify_access_token, verify_revocation,
};
use remote_credential_wire::{ResponseStatus, read_response, write_request};
use remote_tls_transport::{EndpointScope, PinnedCredentialIssuerTlsTransport};
use ring::rand::SystemRandom;
use ring::signature::{Ed25519KeyPair, KeyPair as _};
use rustls::pki_types::{CertificateDer, PrivatePkcs8KeyDer};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use tempfile::tempdir;

type TestResult<T = ()> = Result<T, Box<dyn std::error::Error>>;

const NOW: u64 = 1_800_000_000;
const CLIENT_ISSUER: &str = "https://client.example";
const CLIENT_SUBJECT: &str = "hwpx-agent-client-0001";
const CLIENT_AUDIENCE: &str = "credential-issuer";
const CLIENT_KEY_ID: &str = "client-key-0001";
const SERVICE_ISSUER: &str = "https://issuer.example";
const SERVICE_SUBJECT: &str = "service-account-0001";
const SERVICE_AUDIENCE: &str = "hwpx-agent-remote-sync";
const SERVICE_KEY_ID: &str = "issuer-key-0001";

fn must_ok<T, E: fmt::Debug>(result: Result<T, E>) -> T {
    match result {
        Ok(value) => value,
        Err(error) => panic!("unexpected error: {error:?}"),
    }
}

fn lock<T>(value: &Mutex<T>) -> MutexGuard<'_, T> {
    match value.lock() {
        Ok(guard) => guard,
        Err(poisoned) => poisoned.into_inner(),
    }
}

fn keypair_document() -> TestResult<Vec<u8>> {
    let document = Ed25519KeyPair::generate_pkcs8(&SystemRandom::new())
        .map_err(|_| "Ed25519 key generation failed")?;
    Ok(document.as_ref().to_vec())
}

fn keypair(document: &[u8]) -> TestResult<Ed25519KeyPair> {
    Ed25519KeyPair::from_pkcs8(document).map_err(|_| "Ed25519 key decoding failed".into())
}

fn public_key(document: &[u8]) -> TestResult<[u8; 32]> {
    let pair = keypair(document)?;
    let mut public = [0_u8; 32];
    public.copy_from_slice(pair.public_key().as_ref());
    Ok(public)
}

#[derive(Clone)]
struct KeyMaterial {
    client_document: Vec<u8>,
    service_document: Vec<u8>,
}

impl KeyMaterial {
    fn generate() -> TestResult<Self> {
        Ok(Self {
            client_document: keypair_document()?,
            service_document: keypair_document()?,
        })
    }
}

fn tls_material() -> TestResult<(Vec<u8>, PrivatePkcs8KeyDer<'static>)> {
    let CertifiedKey { cert, signing_key } =
        generate_simple_self_signed(vec!["localhost".to_owned()])?;
    Ok((
        cert.der().to_vec(),
        PrivatePkcs8KeyDer::from(signing_key.serialize_der()),
    ))
}

fn policies(keys: &KeyMaterial) -> TestResult<(LifecyclePolicy, IssuerPolicy)> {
    let lifecycle = LifecyclePolicy::new(
        SERVICE_ISSUER.to_owned(),
        SERVICE_SUBJECT.to_owned(),
        SERVICE_AUDIENCE.to_owned(),
        vec![IssuerKey::new(
            SERVICE_KEY_ID.to_owned(),
            public_key(&keys.service_document)?,
        )?],
        300,
        900,
        120,
        30,
        120,
    )?;
    let issuer = IssuerPolicy::new(
        lifecycle.binding_sha256()?,
        CLIENT_ISSUER.to_owned(),
        CLIENT_SUBJECT.to_owned(),
        CLIENT_AUDIENCE.to_owned(),
        vec![VerificationKey::new(
            CLIENT_KEY_ID.to_owned(),
            public_key(&keys.client_document)?,
        )?],
        VerificationKey::new(
            SERVICE_KEY_ID.to_owned(),
            public_key(&keys.service_document)?,
        )?,
        SERVICE_ISSUER.to_owned(),
        SERVICE_SUBJECT.to_owned(),
        SERVICE_AUDIENCE.to_owned(),
        600,
        120,
        30,
        120,
    )?;
    Ok((lifecycle, issuer))
}

#[derive(Debug, Clone, Copy, Eq, PartialEq)]
enum NextAppend {
    Succeed,
    Conflict,
    Unavailable,
}

#[derive(Debug)]
struct MemoryState {
    records: Vec<StoredRecord>,
    next_append: NextAppend,
}

#[derive(Clone, Debug)]
struct MemoryStore {
    state: Arc<Mutex<MemoryState>>,
}

impl Default for MemoryStore {
    fn default() -> Self {
        Self {
            state: Arc::new(Mutex::new(MemoryState {
                records: Vec::new(),
                next_append: NextAppend::Succeed,
            })),
        }
    }
}

impl MemoryStore {
    fn record_count(&self) -> usize {
        lock(&self.state).records.len()
    }

    fn fail_next(&self, failure: NextAppend) {
        lock(&self.state).next_append = failure;
    }

    fn tamper_first(&self, operation: impl FnOnce(&[u8]) -> Vec<u8>) {
        let mut state = lock(&self.state);
        if let Some(record) = state.records.first_mut() {
            let bytes = operation(record.bytes());
            *record = must_ok(StoredRecord::committed(1, bytes));
        }
    }
}

impl IssuerStateStore for MemoryStore {
    fn load_all(&mut self) -> Result<Vec<StoredRecord>, StoreFailure> {
        Ok(lock(&self.state).records.clone())
    }

    fn append(
        &mut self,
        expected: Option<&StoredRevision>,
        bytes: &[u8],
    ) -> Result<StoredRecord, StoreFailure> {
        let mut state = lock(&self.state);
        let next = state.next_append;
        state.next_append = NextAppend::Succeed;
        match next {
            NextAppend::Conflict => return Err(StoreFailure::Conflict),
            NextAppend::Unavailable => return Err(StoreFailure::Unavailable),
            NextAppend::Succeed => {}
        }
        if state.records.last().map(StoredRecord::revision) != expected {
            return Err(StoreFailure::Conflict);
        }
        let sequence = u64::try_from(state.records.len())
            .map_err(|_| StoreFailure::Rejected)?
            .checked_add(1)
            .ok_or(StoreFailure::Rejected)?;
        let record = StoredRecord::committed(sequence, bytes.to_vec())?;
        state.records.push(record.clone());
        Ok(record)
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum SignMode {
    Valid,
    Rejected,
    Unavailable,
    InvalidSignature,
}

struct TestSigner {
    pair: Ed25519KeyPair,
    calls: Arc<AtomicUsize>,
    mode: Arc<Mutex<SignMode>>,
}

impl fmt::Debug for TestSigner {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TestSigner")
            .field("key", &"<redacted>")
            .field("calls", &self.calls.load(Ordering::SeqCst))
            .finish_non_exhaustive()
    }
}

impl TestSigner {
    fn new(document: &[u8]) -> TestResult<(Self, SignerControl)> {
        let calls = Arc::new(AtomicUsize::new(0));
        let mode = Arc::new(Mutex::new(SignMode::Valid));
        Ok((
            Self {
                pair: keypair(document)?,
                calls: Arc::clone(&calls),
                mode: Arc::clone(&mode),
            },
            SignerControl { calls, mode },
        ))
    }
}

impl CredentialTokenSigner for TestSigner {
    fn key_id(&self) -> &str {
        SERVICE_KEY_ID
    }

    fn sign(&mut self, signing_input: &[u8]) -> Result<[u8; 64], SignerFailure> {
        self.calls.fetch_add(1, Ordering::SeqCst);
        match *lock(&self.mode) {
            SignMode::Rejected => Err(SignerFailure::Rejected),
            SignMode::Unavailable => Err(SignerFailure::Unavailable),
            SignMode::InvalidSignature => Ok([0_u8; 64]),
            SignMode::Valid => {
                let mut signature = [0_u8; 64];
                signature.copy_from_slice(self.pair.sign(signing_input).as_ref());
                Ok(signature)
            }
        }
    }
}

#[derive(Clone, Debug)]
struct SignerControl {
    calls: Arc<AtomicUsize>,
    mode: Arc<Mutex<SignMode>>,
}

impl SignerControl {
    fn calls(&self) -> usize {
        self.calls.load(Ordering::SeqCst)
    }

    fn set_mode(&self, mode: SignMode) {
        *lock(&self.mode) = mode;
    }
}

#[derive(Serialize)]
struct Header<'a> {
    alg: &'a str,
    typ: &'a str,
    kid: &'a str,
}

#[derive(Serialize)]
struct AssertionClaims<'a> {
    iss: &'a str,
    sub: &'a str,
    aud: &'a str,
    scope: &'a str,
    iat: u64,
    nbf: u64,
    exp: u64,
    jti: &'a str,
    request_sha256: &'a str,
}

#[allow(clippy::too_many_arguments)]
fn client_assertion(
    document: &[u8],
    request: &[u8],
    jti: &str,
    iat: u64,
    nbf: u64,
    exp: u64,
    issuer: &str,
    request_sha256_override: Option<&str>,
) -> TestResult<String> {
    let request_sha256 = hex::encode(Sha256::digest(request));
    let header = serde_json::to_vec(&Header {
        alg: "EdDSA",
        typ: "hwpx-agent-issuer-client+jwt",
        kid: CLIENT_KEY_ID,
    })?;
    let claims = serde_json::to_vec(&AssertionClaims {
        iss: issuer,
        sub: CLIENT_SUBJECT,
        aud: CLIENT_AUDIENCE,
        scope: "credential.manage",
        iat,
        nbf,
        exp,
        jti,
        request_sha256: request_sha256_override.unwrap_or(&request_sha256),
    })?;
    let input = format!(
        "{}.{}",
        URL_SAFE_NO_PAD.encode(header),
        URL_SAFE_NO_PAD.encode(claims)
    );
    let signature = keypair(document)?.sign(input.as_bytes());
    Ok(format!(
        "Bearer {input}.{}",
        URL_SAFE_NO_PAD.encode(signature.as_ref())
    ))
}

fn valid_assertion(keys: &KeyMaterial, request: &[u8], jti: &str, now: u64) -> TestResult<String> {
    client_assertion(
        &keys.client_document,
        request,
        jti,
        now,
        now,
        now + 60,
        CLIENT_ISSUER,
        None,
    )
}

fn exchange_payload<S: IssuerStateStore, T: CredentialTokenSigner>(
    issuer: &mut CredentialIssuer<S, T>,
    authorization: &str,
    request: &[u8],
    now: u64,
) -> (ExchangeStatus, Option<Vec<u8>>) {
    let exchange = issuer.exchange(authorization, request, now);
    let status = exchange.status();
    let payload = exchange.with_payload(|payload| payload.map(<[u8]>::to_vec));
    (status, payload)
}

fn issue_request(
    lifecycle: &LifecyclePolicy,
    operation_id: &str,
    now: u64,
) -> TestResult<(remote_credential_lifecycle::PendingTransition, Vec<u8>)> {
    let pending = begin_transition(
        lifecycle,
        &CredentialState::Absent,
        LifecycleOperation::Issue,
        operation_id.to_owned(),
        now,
    )?;
    let request = pending.retry_request(lifecycle, now)?;
    Ok((pending, request))
}

fn access_state(
    lifecycle: &LifecyclePolicy,
    pending: &remote_credential_lifecycle::PendingTransition,
    request: &[u8],
    payload: &[u8],
    now: u64,
) -> TestResult<CredentialState> {
    let reply = parse_issuer_response(request, payload)?;
    let IssuerReply::Access(secret) = reply else {
        return Err("expected access response".into());
    };
    let token = secret.with_secret(str::to_owned);
    let verified = verify_access_token(lifecycle, pending, token, now)?;
    Ok(CredentialState::Active {
        credential: verified.metadata().clone(),
    })
}

fn complete_access_transition(
    issuer: &mut CredentialIssuer<MemoryStore, TestSigner>,
    lifecycle: &LifecyclePolicy,
    keys: &KeyMaterial,
    state: &CredentialState,
    case: (LifecycleOperation, &str, &str, u64),
) -> TestResult<CredentialState> {
    let (operation, operation_id, assertion_jti, now) = case;
    let pending = begin_transition(lifecycle, state, operation, operation_id.to_owned(), now)?;
    let request = pending.retry_request(lifecycle, now)?;
    let authorization = valid_assertion(keys, &request, assertion_jti, now)?;
    let (status, payload) = exchange_payload(issuer, &authorization, &request, now);
    assert_eq!(status, ExchangeStatus::Completed);
    access_state(
        lifecycle,
        &pending,
        &request,
        payload.as_deref().ok_or("access payload missing")?,
        now,
    )
}

fn assert_active_generation(
    state: &CredentialState,
    generation: u64,
    key_generation: u64,
) -> TestResult {
    let active = state.active().ok_or("active state missing")?;
    assert_eq!(active.generation(), generation);
    assert_eq!(active.key_generation(), key_generation);
    Ok(())
}

#[test]
fn issue_refresh_rotate_and_revoke_are_exact_and_client_verifiable() -> TestResult {
    let keys = KeyMaterial::generate()?;
    let (lifecycle, policy) = policies(&keys)?;
    let store = MemoryStore::default();
    let observer = store.clone();
    let (signer, _) = TestSigner::new(&keys.service_document)?;
    let mut issuer = CredentialIssuer::new(policy, store, signer)?;

    let mut state = complete_access_transition(
        &mut issuer,
        &lifecycle,
        &keys,
        &CredentialState::Absent,
        (
            LifecycleOperation::Issue,
            "operation-issue-0001",
            "assertion-jti-issue-0001",
            NOW,
        ),
    )?;
    assert_active_generation(&state, 1, 1)?;

    let refresh_at = state.active().ok_or("active state missing")?.refresh_at();
    state = complete_access_transition(
        &mut issuer,
        &lifecycle,
        &keys,
        &state,
        (
            LifecycleOperation::Refresh,
            "operation-refresh-0002",
            "assertion-jti-refresh-0002",
            refresh_at,
        ),
    )?;
    assert_active_generation(&state, 2, 1)?;

    let rotate_at = refresh_at + 1;
    state = complete_access_transition(
        &mut issuer,
        &lifecycle,
        &keys,
        &state,
        (
            LifecycleOperation::Rotate,
            "operation-rotate-0003",
            "assertion-jti-rotate-0003",
            rotate_at,
        ),
    )?;
    assert_active_generation(&state, 3, 2)?;

    let revoke_at = rotate_at + 1;
    let revoke = begin_transition(
        &lifecycle,
        &state,
        LifecycleOperation::Revoke,
        "operation-revoke-0004".to_owned(),
        revoke_at,
    )?;
    let revoke_request = revoke.retry_request(&lifecycle, revoke_at)?;
    let revoke_authorization = valid_assertion(
        &keys,
        &revoke_request,
        "assertion-jti-revoke-0004",
        revoke_at,
    )?;
    let (status, payload) = exchange_payload(
        &mut issuer,
        &revoke_authorization,
        &revoke_request,
        revoke_at,
    );
    assert_eq!(status, ExchangeStatus::Completed);
    let payload = payload.as_deref().ok_or("revoke payload missing")?;
    let IssuerReply::Revocation(receipt) = parse_issuer_response(&revoke_request, payload)? else {
        return Err("expected revocation response".into());
    };
    let receipt = receipt.with_secret(str::to_owned);
    let revoked = verify_revocation(&lifecycle, &revoke, &receipt, revoke_at)?;
    state = CredentialState::Revoked {
        credential: revoked,
    };
    assert!(state.active().is_none());
    assert_eq!(observer.record_count(), 4);
    Ok(())
}

#[test]
fn exact_assertion_retry_is_byte_exact_without_second_record() -> TestResult {
    let keys = KeyMaterial::generate()?;
    let (lifecycle, policy) = policies(&keys)?;
    let store = MemoryStore::default();
    let observer = store.clone();
    let (signer, control) = TestSigner::new(&keys.service_document)?;
    let mut issuer = CredentialIssuer::new(policy, store, signer)?;
    let (_, request) = issue_request(&lifecycle, "operation-issue-retry-0001", NOW)?;
    let authorization = valid_assertion(&keys, &request, "assertion-jti-retry-0001", NOW)?;
    let first = exchange_payload(&mut issuer, &authorization, &request, NOW);
    let second = exchange_payload(&mut issuer, &authorization, &request, NOW);
    assert_eq!(first.0, ExchangeStatus::Completed);
    assert_eq!(second.0, ExchangeStatus::Completed);
    assert_eq!(first.1, second.1);
    assert_eq!(observer.record_count(), 1);
    assert_eq!(control.calls(), 2);
    Ok(())
}

#[test]
fn fresh_assertion_retry_is_durable_and_byte_exact() -> TestResult {
    let keys = KeyMaterial::generate()?;
    let (lifecycle, policy) = policies(&keys)?;
    let store = MemoryStore::default();
    let observer = store.clone();
    let (signer, _) = TestSigner::new(&keys.service_document)?;
    let mut issuer = CredentialIssuer::new(policy, store, signer)?;
    let (_, request) = issue_request(&lifecycle, "operation-fresh-retry-0001", NOW)?;
    let first = exchange_payload(
        &mut issuer,
        &valid_assertion(&keys, &request, "assertion-jti-fresh-0001", NOW)?,
        &request,
        NOW,
    );
    let second = exchange_payload(
        &mut issuer,
        &valid_assertion(&keys, &request, "assertion-jti-fresh-0002", NOW)?,
        &request,
        NOW,
    );
    assert_eq!(first.1, second.1);
    assert_eq!(observer.record_count(), 2);
    Ok(())
}

#[test]
fn assertion_jti_cannot_authorize_a_different_request() -> TestResult {
    let keys = KeyMaterial::generate()?;
    let (lifecycle, policy) = policies(&keys)?;
    let store = MemoryStore::default();
    let observer = store.clone();
    let (signer, control) = TestSigner::new(&keys.service_document)?;
    let mut issuer = CredentialIssuer::new(policy, store, signer)?;
    let (_, first_request) = issue_request(&lifecycle, "operation-first-jti-0001", NOW)?;
    let (_, second_request) = issue_request(&lifecycle, "operation-second-jti-0002", NOW)?;
    let jti = "assertion-jti-reused-0001";
    let first = exchange_payload(
        &mut issuer,
        &valid_assertion(&keys, &first_request, jti, NOW)?,
        &first_request,
        NOW,
    );
    let calls = control.calls();
    let second = exchange_payload(
        &mut issuer,
        &valid_assertion(&keys, &second_request, jti, NOW)?,
        &second_request,
        NOW,
    );
    assert_eq!(first.0, ExchangeStatus::Completed);
    assert_eq!(second.0, ExchangeStatus::DefinitiveRejection);
    assert_eq!(control.calls(), calls);
    assert_eq!(observer.record_count(), 1);
    Ok(())
}

#[test]
fn assertion_signature_identity_time_and_request_binding_fail_closed() -> TestResult {
    let keys = KeyMaterial::generate()?;
    let wrong_keys = KeyMaterial::generate()?;
    let (lifecycle, policy) = policies(&keys)?;
    let store = MemoryStore::default();
    let observer = store.clone();
    let (signer, control) = TestSigner::new(&keys.service_document)?;
    let mut issuer = CredentialIssuer::new(policy, store, signer)?;
    let (_, request) = issue_request(&lifecycle, "operation-auth-negative-0001", NOW)?;
    let wrong_digest = "0".repeat(64);
    let invalid = [
        client_assertion(
            &wrong_keys.client_document,
            &request,
            "assertion-wrong-signature-0001",
            NOW,
            NOW,
            NOW + 60,
            CLIENT_ISSUER,
            None,
        )?,
        client_assertion(
            &keys.client_document,
            &request,
            "assertion-wrong-issuer-0002",
            NOW,
            NOW,
            NOW + 60,
            "https://other.example",
            None,
        )?,
        client_assertion(
            &keys.client_document,
            &request,
            "assertion-expired-0003",
            NOW - 200,
            NOW - 200,
            NOW - 100,
            CLIENT_ISSUER,
            None,
        )?,
        client_assertion(
            &keys.client_document,
            &request,
            "assertion-wrong-request-0004",
            NOW,
            NOW,
            NOW + 60,
            CLIENT_ISSUER,
            Some(&wrong_digest),
        )?,
        "bearer aaa.bbb.ccc".to_owned(),
    ];
    for authorization in invalid {
        let exchange = issuer.exchange(&authorization, &request, NOW);
        assert_eq!(exchange.status(), ExchangeStatus::DefinitiveRejection);
    }
    assert_eq!(observer.record_count(), 0);
    assert_eq!(control.calls(), 0);
    Ok(())
}

#[test]
fn malformed_noncanonical_and_policy_drifted_requests_are_rejected() -> TestResult {
    let keys = KeyMaterial::generate()?;
    let (lifecycle, policy) = policies(&keys)?;
    let store = MemoryStore::default();
    let observer = store.clone();
    let (signer, control) = TestSigner::new(&keys.service_document)?;
    let mut issuer = CredentialIssuer::new(policy, store, signer)?;
    let (_, request) = issue_request(&lifecycle, "operation-request-negative-0001", NOW)?;
    let text = String::from_utf8(request.clone())?;
    let invalid = [
        format!(" {text}").into_bytes(),
        text.replace(
            "\"binding_sha256\":\"",
            "\"unknown\":0,\"binding_sha256\":\"",
        )
        .into_bytes(),
        text.replace(&lifecycle.binding_sha256()?, &"0".repeat(64))
            .into_bytes(),
        Vec::new(),
    ];
    for (index, raw) in invalid.iter().enumerate() {
        let authorization = valid_assertion(
            &keys,
            raw,
            &format!("assertion-request-negative-{index:04}"),
            NOW,
        )?;
        assert_eq!(
            issuer.exchange(&authorization, raw, NOW).status(),
            ExchangeStatus::DefinitiveRejection
        );
    }
    assert_eq!(observer.record_count(), 0);
    assert_eq!(control.calls(), 0);
    Ok(())
}

#[test]
fn invalid_state_transition_never_calls_signer_or_mutates_state() -> TestResult {
    let keys = KeyMaterial::generate()?;
    let (lifecycle, policy) = policies(&keys)?;
    let store = MemoryStore::default();
    let observer = store.clone();
    let (signer, control) = TestSigner::new(&keys.service_document)?;
    let mut issuer = CredentialIssuer::new(policy, store, signer)?;
    let (_, first_request) = issue_request(&lifecycle, "operation-valid-issue-0001", NOW)?;
    assert_eq!(
        issuer
            .exchange(
                &valid_assertion(&keys, &first_request, "assertion-valid-issue-0001", NOW)?,
                &first_request,
                NOW,
            )
            .status(),
        ExchangeStatus::Completed
    );
    let calls = control.calls();
    let (_, second_request) = issue_request(&lifecycle, "operation-invalid-issue-0002", NOW + 1)?;
    assert_eq!(
        issuer
            .exchange(
                &valid_assertion(
                    &keys,
                    &second_request,
                    "assertion-invalid-issue-0002",
                    NOW + 1,
                )?,
                &second_request,
                NOW + 1,
            )
            .status(),
        ExchangeStatus::DefinitiveRejection
    );
    assert_eq!(control.calls(), calls);
    assert_eq!(observer.record_count(), 1);
    Ok(())
}

#[test]
fn append_failure_is_unavailable_and_retry_commits_once() -> TestResult {
    let keys = KeyMaterial::generate()?;
    let (lifecycle, policy) = policies(&keys)?;
    let store = MemoryStore::default();
    let observer = store.clone();
    let (signer, _) = TestSigner::new(&keys.service_document)?;
    let mut issuer = CredentialIssuer::new(policy, store, signer)?;
    let (_, request) = issue_request(&lifecycle, "operation-append-failure-0001", NOW)?;
    let authorization = valid_assertion(&keys, &request, "assertion-append-failure-0001", NOW)?;

    observer.fail_next(NextAppend::Unavailable);
    let unavailable = issuer.exchange(&authorization, &request, NOW);
    assert_eq!(unavailable.status(), ExchangeStatus::Unavailable);
    assert!(unavailable.with_payload(|payload| payload.is_none()));
    assert_eq!(observer.record_count(), 0);

    let completed = issuer.exchange(&authorization, &request, NOW);
    assert_eq!(completed.status(), ExchangeStatus::Completed);
    assert_eq!(observer.record_count(), 1);
    observer.fail_next(NextAppend::Conflict);
    assert_eq!(
        issuer
            .exchange(
                &valid_assertion(&keys, &request, "assertion-append-conflict-0002", NOW + 1,)?,
                &request,
                NOW + 1,
            )
            .status(),
        ExchangeStatus::Unavailable
    );
    assert_eq!(observer.record_count(), 1);
    Ok(())
}

#[test]
fn signer_failures_are_unavailable_without_records() -> TestResult {
    let keys = KeyMaterial::generate()?;
    let (lifecycle, policy) = policies(&keys)?;
    let store = MemoryStore::default();
    let observer = store.clone();
    let (signer, control) = TestSigner::new(&keys.service_document)?;
    let mut issuer = CredentialIssuer::new(policy, store, signer)?;
    let (_, request) = issue_request(&lifecycle, "operation-signer-failure-0001", NOW)?;
    let authorization = valid_assertion(&keys, &request, "assertion-signer-failure-0001", NOW)?;
    for mode in [
        SignMode::Rejected,
        SignMode::Unavailable,
        SignMode::InvalidSignature,
    ] {
        control.set_mode(mode);
        assert_eq!(
            issuer.exchange(&authorization, &request, NOW).status(),
            ExchangeStatus::Unavailable
        );
        assert_eq!(observer.record_count(), 0);
    }
    Ok(())
}

#[test]
fn durable_store_reopens_and_replays_without_secret_state() -> TestResult {
    let directory = tempdir()?;
    let keys = KeyMaterial::generate()?;
    let (lifecycle, policy) = policies(&keys)?;
    let (_, request) = issue_request(&lifecycle, "operation-durable-reopen-0001", NOW)?;
    let authorization = valid_assertion(&keys, &request, "assertion-durable-reopen-0001", NOW)?;

    let (signer, _) = TestSigner::new(&keys.service_document)?;
    let store = AppendOnlyIssuerStateStore::new(directory.path())?;
    let mut issuer = CredentialIssuer::new(policy.clone(), store, signer)?;
    let first = exchange_payload(&mut issuer, &authorization, &request, NOW);
    assert_eq!(first.0, ExchangeStatus::Completed);
    drop(issuer);

    let (signer, _) = TestSigner::new(&keys.service_document)?;
    let store = AppendOnlyIssuerStateStore::new(directory.path())?;
    let mut reopened = CredentialIssuer::new(policy, store, signer)?;
    let second = exchange_payload(&mut reopened, &authorization, &request, NOW);
    assert_eq!(second.0, ExchangeStatus::Completed);
    assert_eq!(first.1, second.1);
    let files = fs::read_dir(directory.path())?.collect::<Result<Vec<_>, _>>()?;
    assert_eq!(files.len(), 1);
    let stored = fs::read(files[0].path())?;
    let stored_text = String::from_utf8(stored)?;
    assert!(!stored_text.contains("hwpx-agent-service+jwt"));
    assert!(!stored_text.contains("Bearer "));
    assert!(!stored_text.contains("operation-durable-reopen-0001"));
    Ok(())
}

#[test]
fn durable_store_allows_only_one_writer_per_sequence_slot() -> TestResult {
    const WRITERS: usize = 32;

    let directory = tempdir()?;
    let root = directory.path().to_path_buf();
    let barrier = Arc::new(Barrier::new(WRITERS + 1));
    let mut handles = Vec::with_capacity(WRITERS);
    for writer in 0..WRITERS {
        let root = root.clone();
        let barrier = Arc::clone(&barrier);
        handles.push(std::thread::spawn(move || {
            let mut store = AppendOnlyIssuerStateStore::new(root)?;
            let bytes = format!(r#"{{"writer":{writer}}}"#);
            barrier.wait();
            store.append(None, bytes.as_bytes())
        }));
    }
    barrier.wait();

    let mut completed = 0_usize;
    let mut conflicts = 0_usize;
    for handle in handles {
        match handle
            .join()
            .map_err(|_| std::io::Error::other("issuer writer thread panicked"))?
        {
            Ok(_) => completed += 1,
            Err(StoreFailure::Conflict) => conflicts += 1,
            Err(error) => return Err(format!("unexpected store failure: {error:?}").into()),
        }
    }
    assert_eq!(completed, 1);
    assert_eq!(conflicts, WRITERS - 1);

    let mut reopened = AppendOnlyIssuerStateStore::new(&root)?;
    assert_eq!(reopened.load_all()?.len(), 1);
    let names = fs::read_dir(&root)?
        .map(|entry| entry.map(|entry| entry.file_name().to_string_lossy().into_owned()))
        .collect::<Result<Vec<_>, _>>()?;
    assert_eq!(names, ["00000000000000000001.json"]);
    Ok(())
}

#[test]
fn durable_store_bounds_abandoned_temporary_files() -> TestResult {
    let recoverable = tempdir()?;
    fs::write(
        recoverable
            .path()
            .join(".pending-00000000000000000001-00000000000000000000000000000001.tmp"),
        b"partial",
    )?;
    let mut store = AppendOnlyIssuerStateStore::new(recoverable.path())?;
    assert!(store.load_all()?.is_empty());
    assert_eq!(
        store
            .append(None, b"{}")
            .map(|record| record.revision().sequence()),
        Ok(1)
    );

    let exhausted = tempdir()?;
    for index in 0_u64..=64 {
        fs::write(
            exhausted
                .path()
                .join(format!(".pending-{index:020}-{index:032x}.tmp")),
            b"partial",
        )?;
    }
    assert_eq!(
        AppendOnlyIssuerStateStore::new(exhausted.path())?
            .load_all()
            .err(),
        Some(StoreFailure::Rejected)
    );
    Ok(())
}

#[test]
fn durable_and_memory_history_tamper_fail_unavailable() -> TestResult {
    let keys = KeyMaterial::generate()?;
    let (lifecycle, policy) = policies(&keys)?;
    let store = MemoryStore::default();
    let observer = store.clone();
    let (signer, _) = TestSigner::new(&keys.service_document)?;
    let mut issuer = CredentialIssuer::new(policy.clone(), store, signer)?;
    let (_, request) = issue_request(&lifecycle, "operation-history-tamper-0001", NOW)?;
    let authorization = valid_assertion(&keys, &request, "assertion-history-tamper-0001", NOW)?;
    assert_eq!(
        issuer.exchange(&authorization, &request, NOW).status(),
        ExchangeStatus::Completed
    );
    let policy_binding = policy.binding_sha256()?;
    observer.tamper_first(|bytes| {
        String::from_utf8_lossy(bytes)
            .replace(&policy_binding, &"0".repeat(64))
            .into_bytes()
    });
    assert_eq!(
        issuer.exchange(&authorization, &request, NOW).status(),
        ExchangeStatus::Unavailable
    );

    let directory = tempdir()?;
    fs::write(directory.path().join("00000000000000000002-"), b"tampered")?;
    assert_eq!(
        AppendOnlyIssuerStateStore::new(directory.path())?
            .load_all()
            .err(),
        Some(StoreFailure::Rejected)
    );
    Ok(())
}

#[derive(Debug)]
struct Duplex {
    input: Cursor<Vec<u8>>,
    output: Vec<u8>,
    fail_write: Arc<AtomicBool>,
}

impl Read for Duplex {
    fn read(&mut self, buffer: &mut [u8]) -> std::io::Result<usize> {
        self.input.read(buffer)
    }
}

impl Write for Duplex {
    fn write(&mut self, buffer: &[u8]) -> std::io::Result<usize> {
        if self.fail_write.load(Ordering::SeqCst) {
            return Err(std::io::Error::other("injected"));
        }
        self.output.extend_from_slice(buffer);
        Ok(buffer.len())
    }

    fn flush(&mut self) -> std::io::Result<()> {
        Ok(())
    }
}

#[test]
fn wire_adapter_maps_completed_rejection_and_unavailable() -> TestResult {
    let keys = KeyMaterial::generate()?;
    let (lifecycle, policy) = policies(&keys)?;
    let store = MemoryStore::default();
    let (signer, _) = TestSigner::new(&keys.service_document)?;
    let mut issuer = CredentialIssuer::new(policy, store, signer)?;
    let (_, request) = issue_request(&lifecycle, "operation-wire-adapter-0001", NOW)?;
    let authorization = valid_assertion(&keys, &request, "assertion-wire-adapter-0001", NOW)?;
    let mut input = Vec::new();
    write_request(&mut input, &authorization, &request)?;
    let mut duplex = Duplex {
        input: Cursor::new(input),
        output: Vec::new(),
        fail_write: Arc::new(AtomicBool::new(false)),
    };
    serve_one(&mut issuer, &mut duplex, NOW)?;
    let response = read_response(&mut Cursor::new(duplex.output))?;
    assert_eq!(response.status(), ResponseStatus::Completed);
    assert!(response.with_payload(|payload| !payload.is_empty()));

    let (_, second_request) = issue_request(&lifecycle, "operation-wire-adapter-0002", NOW + 1)?;
    let mut input = Vec::new();
    write_request(
        &mut input,
        &valid_assertion(
            &keys,
            &second_request,
            "assertion-wire-adapter-0002",
            NOW + 1,
        )?,
        &second_request,
    )?;
    let mut rejected = Duplex {
        input: Cursor::new(input),
        output: Vec::new(),
        fail_write: Arc::new(AtomicBool::new(false)),
    };
    serve_one(&mut issuer, &mut rejected, NOW + 1)?;
    let response = read_response(&mut Cursor::new(rejected.output))?;
    assert_eq!(response.status(), ResponseStatus::Completed);
    assert!(response.with_payload(|payload| {
        String::from_utf8_lossy(payload).contains("\"outcome\":\"rejected\"")
    }));

    let fresh_keys = KeyMaterial::generate()?;
    let (fresh_lifecycle, fresh_policy) = policies(&fresh_keys)?;
    let (fresh_signer, _) = TestSigner::new(&fresh_keys.service_document)?;
    let fresh_store = MemoryStore::default();
    fresh_store.fail_next(NextAppend::Unavailable);
    let mut unavailable_issuer = CredentialIssuer::new(fresh_policy, fresh_store, fresh_signer)?;
    let (_, fresh_request) =
        issue_request(&fresh_lifecycle, "operation-wire-unavailable-0003", NOW)?;
    let mut input = Vec::new();
    write_request(
        &mut input,
        &valid_assertion(
            &fresh_keys,
            &fresh_request,
            "assertion-wire-unavailable-0003",
            NOW,
        )?,
        &fresh_request,
    )?;
    let mut unavailable = Duplex {
        input: Cursor::new(input),
        output: Vec::new(),
        fail_write: Arc::new(AtomicBool::new(false)),
    };
    serve_one(&mut unavailable_issuer, &mut unavailable, NOW)?;
    let response = read_response(&mut Cursor::new(unavailable.output))?;
    assert_eq!(response.status(), ResponseStatus::Unavailable);
    assert!(response.with_payload(<[u8]>::is_empty));
    Ok(())
}

#[test]
fn independent_tls13_server_interoperates_with_pinned_client() -> TestResult {
    let keys = KeyMaterial::generate()?;
    let (lifecycle, policy) = policies(&keys)?;
    let store = MemoryStore::default();
    let observer = store.clone();
    let (signer, _) = TestSigner::new(&keys.service_document)?;
    let issuer = CredentialIssuer::new(policy, store, signer)?;
    let (certificate, private_key) = tls_material()?;
    let config = IssuerTlsServerConfig::new(
        vec![CertificateDer::from(certificate.clone())],
        private_key.into(),
    )?;
    let expected_leaf_sha256: [u8; 32] = Sha256::digest(&certificate).into();
    assert_eq!(config.leaf_certificate_sha256(), expected_leaf_sha256);
    let mut server = CredentialIssuerTlsServer::bind(
        SocketAddr::from((Ipv4Addr::LOCALHOST, 0)),
        IssuerBindScope::LoopbackQualification,
        issuer,
        config,
        Duration::from_secs(5),
    )?;
    let endpoint = server.local_addr()?;
    let serving = std::thread::spawn(move || server.serve_one_at(NOW));

    let (pending, request) = issue_request(&lifecycle, "operation-tls-server-0001", NOW)?;
    let authorization = IssuerAuthorization::new(valid_assertion(
        &keys,
        &request,
        "assertion-tls-server-0001",
        NOW,
    )?)?;
    let mut client = PinnedCredentialIssuerTlsTransport::new(
        endpoint,
        EndpointScope::LoopbackQualification,
        "localhost",
        certificate,
        Duration::from_secs(5),
    )?;
    let IssuerReply::Access(secret) = client.exchange(&authorization, &request)? else {
        return Err("expected pinned TLS access response".into());
    };
    let token = secret.with_secret(str::to_owned);
    let verified = verify_access_token(&lifecycle, &pending, token, NOW)?;
    assert_eq!(verified.metadata().generation(), 1);
    assert_eq!(observer.record_count(), 1);
    let status = serving
        .join()
        .map_err(|_| std::io::Error::other("issuer TLS server thread panicked"))??;
    assert_eq!(status, ExchangeStatus::Completed);
    Ok(())
}

#[test]
fn tls_server_configuration_and_bind_scope_fail_closed() -> TestResult {
    let (_, private_key) = tls_material()?;
    assert_eq!(
        IssuerTlsServerConfig::new(Vec::new(), private_key.into()).err(),
        Some(IssuerTlsServerFailure::Rejected)
    );

    let keys = KeyMaterial::generate()?;
    let (_, policy) = policies(&keys)?;
    let (signer, _) = TestSigner::new(&keys.service_document)?;
    let issuer = CredentialIssuer::new(policy, MemoryStore::default(), signer)?;
    let (certificate, private_key) = tls_material()?;
    let config =
        IssuerTlsServerConfig::new(vec![CertificateDer::from(certificate)], private_key.into())?;
    assert_eq!(
        CredentialIssuerTlsServer::bind(
            SocketAddr::from((Ipv4Addr::LOCALHOST, 0)),
            IssuerBindScope::ExplicitDeployment,
            issuer,
            config,
            Duration::from_secs(5),
        )
        .err(),
        Some(IssuerTlsServerFailure::Rejected)
    );
    Ok(())
}

#[test]
fn policy_bounds_and_debug_output_are_fail_closed_and_redacted() -> TestResult {
    let keys = KeyMaterial::generate()?;
    let (lifecycle, policy) = policies(&keys)?;
    let store = MemoryStore::default();
    let (signer, _) = TestSigner::new(&keys.service_document)?;
    let issuer = CredentialIssuer::new(policy.clone(), store, signer)?;
    let debug = format!("{issuer:?} {policy:?}");
    for private in [
        CLIENT_ISSUER,
        CLIENT_SUBJECT,
        SERVICE_ISSUER,
        SERVICE_SUBJECT,
        SERVICE_KEY_ID,
    ] {
        assert!(!debug.contains(private));
    }
    assert!(debug.contains("<redacted>"));

    assert_eq!(
        VerificationKey::new(String::new(), [1_u8; 32]).err(),
        Some(IssuerError::Rejected)
    );
    assert_eq!(
        VerificationKey::new(CLIENT_KEY_ID.to_owned(), [0_u8; 32]).err(),
        Some(IssuerError::Rejected)
    );
    let invalid = IssuerPolicy::new(
        lifecycle.binding_sha256()?,
        CLIENT_ISSUER.to_owned(),
        CLIENT_SUBJECT.to_owned(),
        CLIENT_AUDIENCE.to_owned(),
        vec![VerificationKey::new(
            CLIENT_KEY_ID.to_owned(),
            public_key(&keys.client_document)?,
        )?],
        VerificationKey::new(
            SERVICE_KEY_ID.to_owned(),
            public_key(&keys.service_document)?,
        )?,
        SERVICE_ISSUER.to_owned(),
        SERVICE_SUBJECT.to_owned(),
        SERVICE_AUDIENCE.to_owned(),
        59,
        120,
        30,
        120,
    );
    assert_eq!(invalid.err(), Some(IssuerError::Rejected));
    Ok(())
}
