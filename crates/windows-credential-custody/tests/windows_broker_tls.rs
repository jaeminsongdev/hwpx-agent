#![cfg(windows)]

use std::collections::HashMap;
use std::error::Error;
use std::net::{Ipv4Addr, SocketAddr, TcpListener};
use std::sync::Arc;
use std::thread;
use std::time::Duration;

use base64::{Engine as _, engine::general_purpose::URL_SAFE_NO_PAD};
use keyring_core::api::CredentialStoreApi;
use local_sync::RemoteCredentialProvider;
use rcgen::{CertifiedKey, generate_simple_self_signed};
use remote_credential_broker::{
    AppendOnlyCredentialStateStore, AuthorizationFailure, CredentialBroker, CredentialVault,
    DriveOutcome, IssuerAuthorization, IssuerAuthorizationProvider, VaultObservation,
};
use remote_credential_lifecycle::{
    CredentialState, IssuerKey, LifecycleOperation, LifecyclePolicy,
};
use remote_credential_wire::{ResponseStatus, read_request, write_response};
use remote_tls_transport::{EndpointScope, PinnedCredentialIssuerTlsTransport};
use ring::{
    rand::SystemRandom,
    signature::{Ed25519KeyPair, KeyPair as _},
};
use rustls::pki_types::{CertificateDer, PrivatePkcs8KeyDer};
use rustls::{ServerConfig, ServerConnection, StreamOwned, version};
use serde::{Deserialize, Serialize};
use serde_json::json;
use sha2::{Digest as _, Sha256};
use tempfile::tempdir;
use uuid::Uuid;
use windows_credential_custody::{WindowsCredentialManagerProvider, WindowsCredentialManagerVault};
use zeroize::Zeroizing;

type TestResult<T = ()> = Result<T, Box<dyn Error>>;
const NOW: u64 = 1_800_000_000;
const ISSUER: &str = "https://issuer.example";
const SUBJECT: &str = "service-account-0001";
const AUDIENCE: &str = "hwpx-agent-remote-sync";
const KEY_ID: &str = "issuer-key-0001";

struct CredentialCleanup {
    entry: keyring_core::Entry,
    armed: bool,
}

impl Drop for CredentialCleanup {
    fn drop(&mut self) {
        if self.armed {
            let _ = self.entry.delete_credential();
        }
    }
}

#[derive(Debug, Default)]
struct StaticAuthorization;

impl IssuerAuthorizationProvider for StaticAuthorization {
    fn authorization(&mut self) -> Result<IssuerAuthorization, AuthorizationFailure> {
        IssuerAuthorization::new("Bearer aaa.bbb.ccc".to_owned())
    }
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct LifecycleRequest {
    schema_version: String,
    operation: LifecycleOperation,
    operation_id: String,
    binding_sha256: String,
    expected_generation: u64,
    expected_key_generation: u64,
    prior_credential_sha256: Option<String>,
    requested_at: u64,
}

#[derive(Serialize)]
struct Header<'a> {
    alg: &'a str,
    typ: &'a str,
    kid: &'a str,
}

#[derive(Serialize)]
struct AccessClaims<'a> {
    iss: &'a str,
    sub: &'a str,
    aud: &'a str,
    scope: &'a str,
    iat: u64,
    nbf: u64,
    exp: u64,
    jti: String,
    operation_id: &'a str,
    request_sha256: &'a str,
    generation: u64,
    key_generation: u64,
}

#[derive(Serialize)]
struct RevocationClaims<'a> {
    iss: &'a str,
    sub: &'a str,
    aud: &'a str,
    iat: u64,
    jti: String,
    operation_id: &'a str,
    request_sha256: &'a str,
    generation: u64,
    key_generation: u64,
    credential_sha256: &'a str,
    revoked: bool,
}

fn signed_jwt(
    pair: &Ed25519KeyPair,
    token_type: &str,
    claims: &impl Serialize,
) -> TestResult<String> {
    let header = serde_json::to_vec(&Header {
        alg: "EdDSA",
        typ: token_type,
        kid: KEY_ID,
    })?;
    let payload = serde_json::to_vec(claims)?;
    let signing_input = format!(
        "{}.{}",
        URL_SAFE_NO_PAD.encode(header),
        URL_SAFE_NO_PAD.encode(payload)
    );
    let signature = pair.sign(signing_input.as_bytes());
    Ok(format!(
        "{signing_input}.{}",
        URL_SAFE_NO_PAD.encode(signature.as_ref())
    ))
}

fn issuer_response(pair: &Ed25519KeyPair, request_bytes: &[u8]) -> TestResult<Vec<u8>> {
    let request: LifecycleRequest = serde_json::from_slice(request_bytes)?;
    if serde_json::to_vec(&request)? != request_bytes
        || request.schema_version != "hwpx-agent.remote-credential-lifecycle-request/v1"
    {
        return Err("noncanonical lifecycle request".into());
    }
    let request_sha256 = hex::encode(Sha256::digest(request_bytes));
    let response = match request.operation {
        LifecycleOperation::Issue | LifecycleOperation::Refresh | LifecycleOperation::Rotate => {
            let claims = AccessClaims {
                iss: ISSUER,
                sub: SUBJECT,
                aud: AUDIENCE,
                scope: "mirror.sync",
                iat: request.requested_at,
                nbf: request.requested_at,
                exp: request.requested_at + 600,
                jti: format!(
                    "credential-jti-{:08}-{}",
                    request.expected_generation, request.expected_key_generation
                ),
                operation_id: &request.operation_id,
                request_sha256: &request_sha256,
                generation: request.expected_generation,
                key_generation: request.expected_key_generation,
            };
            let token = signed_jwt(pair, "hwpx-agent-service+jwt", &claims)?;
            format!(
                "{{\"outcome\":\"access\",\"schema_version\":\"hwpx-agent.remote-credential-issuer-response/v1\",\"request_sha256\":\"{request_sha256}\",\"token\":\"{token}\"}}"
            )
        }
        LifecycleOperation::Revoke => {
            let prior = request
                .prior_credential_sha256
                .as_deref()
                .ok_or("revocation prior digest missing")?;
            let claims = RevocationClaims {
                iss: ISSUER,
                sub: SUBJECT,
                aud: AUDIENCE,
                iat: request.requested_at,
                jti: format!("revocation-jti-{:08}", request.expected_generation),
                operation_id: &request.operation_id,
                request_sha256: &request_sha256,
                generation: request.expected_generation,
                key_generation: request.expected_key_generation,
                credential_sha256: prior,
                revoked: true,
            };
            let receipt = signed_jwt(pair, "hwpx-agent-revocation+jwt", &claims)?;
            format!(
                "{{\"outcome\":\"revocation\",\"schema_version\":\"hwpx-agent.remote-credential-issuer-response/v1\",\"request_sha256\":\"{request_sha256}\",\"receipt\":\"{receipt}\"}}"
            )
        }
    };
    Ok(response.into_bytes())
}

fn new_signer_and_policy() -> TestResult<(Ed25519KeyPair, LifecyclePolicy)> {
    let random = SystemRandom::new();
    let document =
        Ed25519KeyPair::generate_pkcs8(&random).map_err(|_| "Ed25519 PKCS#8 generation failed")?;
    let pair = Ed25519KeyPair::from_pkcs8(document.as_ref())
        .map_err(|_| "Ed25519 PKCS#8 decoding failed")?;
    let mut public_key = [0_u8; 32];
    public_key.copy_from_slice(pair.public_key().as_ref());
    let policy = LifecyclePolicy::new(
        ISSUER.to_owned(),
        SUBJECT.to_owned(),
        AUDIENCE.to_owned(),
        vec![IssuerKey::new(KEY_ID.to_owned(), public_key)?],
        300,
        900,
        120,
        30,
        120,
    )?;
    Ok((pair, policy))
}

fn new_tls_server(
    pair: Ed25519KeyPair,
) -> TestResult<(SocketAddr, Vec<u8>, thread::JoinHandle<()>)> {
    let CertifiedKey { cert, signing_key } =
        generate_simple_self_signed(vec!["localhost".to_owned()])?;
    let certificate = cert.der().to_vec();
    let key = PrivatePkcs8KeyDer::from(signing_key.serialize_der());
    let provider = Arc::new(rustls::crypto::ring::default_provider());
    let config = ServerConfig::builder_with_provider(provider)
        .with_protocol_versions(&[&version::TLS13])?
        .with_no_client_auth()
        .with_single_cert(vec![CertificateDer::from(certificate.clone())], key.into())?;
    let config = Arc::new(config);
    let listener = TcpListener::bind((Ipv4Addr::LOCALHOST, 0))?;
    let endpoint = listener.local_addr()?;
    let handle = thread::spawn(move || {
        for _ in 0..2 {
            let Ok((socket, _)) = listener.accept() else {
                return;
            };
            let Ok(connection) = ServerConnection::new(Arc::clone(&config)) else {
                return;
            };
            let mut stream = StreamOwned::new(connection, socket);
            let Ok(request) = read_request(&mut stream) else {
                return;
            };
            assert_eq!(
                request.with_authorization(str::to_owned),
                "Bearer aaa.bbb.ccc"
            );
            let Ok(response) = issuer_response(&pair, request.payload()) else {
                return;
            };
            if write_response(&mut stream, ResponseStatus::Completed, &response).is_err() {
                return;
            }
            stream.conn.send_close_notify();
            let _ = std::io::Write::flush(&mut stream);
        }
    });
    Ok((endpoint, certificate, handle))
}

fn emit_receipt(target: &str, record_count: usize) -> TestResult {
    let receipt = json!({
        "schema_version": "hwpx-agent.windows-credential-broker-runtime/v1",
        "backend": "windows_credential_manager",
        "transport": "pinned_loopback_tls_1_3",
        "credential_target_sha256": hex::encode(Sha256::digest(target.as_bytes())),
        "checks": {
            "unique_target_preflight_absent": true,
            "pending_persisted_before_dispatch": true,
            "issuer_request_digest_bound": true,
            "access_jws_verified": true,
            "product_vault_written_and_observed": true,
            "product_provider_read": true,
            "revocation_jws_verified": true,
            "product_vault_deleted": true,
            "post_cleanup_absent": true,
            "append_only_records": record_count
        },
        "claims": {
            "synthetic_ephemeral_issuer_only": true,
            "loopback_transport_only": true,
            "existing_credentials_enumerated": false,
            "real_service_credential": false,
            "external_remote_network": false,
            "registered_host": false,
            "production": false,
            "p17_06_complete": false,
            "product_complete": false
        }
    });
    println!(
        "HWPX_AGENT_WINDOWS_CREDENTIAL_BROKER_RECEIPT={}",
        serde_json::to_string(&receipt)?
    );
    Ok(())
}

#[test]
#[ignore = "creates and deletes one unique synthetic Windows Credential Manager entry"]
fn current_user_broker_pinned_tls_issue_and_revoke() -> TestResult {
    let nonce = Uuid::new_v4().simple().to_string();
    let service = format!("broker-qualification.{nonce}");
    let account = format!("synthetic.{nonce}");
    let mut vault = WindowsCredentialManagerVault::new(&service, &account)?;
    let target = vault.target_name().to_owned();
    let store = windows_native_keyring_store::Store::new()?;
    let modifiers = HashMap::from([("target", target.as_str()), ("persistence", "Local")]);
    let entry = store.build(
        "hwpx-agent.remote-sync",
        "brokered-service-bearer",
        Some(&modifiers),
    )?;
    let mut cleanup = CredentialCleanup { entry, armed: true };
    if vault.observe()? != VaultObservation::Absent {
        return Err("unique preflight credential is not exactly absent".into());
    }

    let (pair, policy) = new_signer_and_policy()?;
    let (endpoint, certificate, server) = new_tls_server(pair)?;
    let state_directory = tempdir()?;
    let state_store = AppendOnlyCredentialStateStore::new(state_directory.path())?;
    let transport = PinnedCredentialIssuerTlsTransport::new(
        endpoint,
        EndpointScope::LoopbackQualification,
        "localhost",
        certificate,
        Duration::from_secs(5),
    )?;
    let mut broker =
        CredentialBroker::open(policy, state_store, vault, StaticAuthorization, transport)?;
    broker.begin(
        LifecycleOperation::Issue,
        "operation-issue-0001".to_owned(),
        NOW,
    )?;
    let active = match broker.drive(NOW)? {
        DriveOutcome::Completed(state @ CredentialState::Active { .. }) => state,
        outcome => return Err(format!("unexpected issue outcome: {outcome:?}").into()),
    };
    let CredentialState::Active { credential } = &active else {
        return Err("active metadata missing".into());
    };
    let expected_digest = credential.credential_sha256().to_owned();

    let mut provider = WindowsCredentialManagerProvider::new(&service, &account)?;
    let authorization = provider.authorization_header()?;
    assert!(format!("{authorization:?}").contains("<redacted>"));
    let stored_secret = Zeroizing::new(cleanup.entry.get_secret()?);
    assert_eq!(
        hex::encode(Sha256::digest(&*stored_secret)),
        expected_digest
    );

    broker.begin(
        LifecycleOperation::Revoke,
        "operation-revoke-0001".to_owned(),
        NOW + 1,
    )?;
    assert!(matches!(
        broker.drive(NOW + 1)?,
        DriveOutcome::Completed(CredentialState::Revoked { .. })
    ));
    let (_, mut vault, _, _) = broker.into_parts();
    assert_eq!(vault.observe()?, VaultObservation::Absent);
    cleanup.armed = false;
    assert!(matches!(
        cleanup.entry.get_secret(),
        Err(keyring_core::Error::NoEntry)
    ));
    server.join().map_err(|_| "issuer server thread panicked")?;

    let record_count = std::fs::read_dir(state_directory.path())?
        .filter_map(Result::ok)
        .filter(|entry| {
            entry
                .path()
                .extension()
                .is_some_and(|value| value == "json")
        })
        .count();
    assert_eq!(record_count, 7);
    emit_receipt(&target, record_count)?;
    Ok(())
}
