use std::error::Error;
use std::io::Write;
use std::net::{Ipv4Addr, SocketAddr, TcpListener};
use std::sync::Arc;
use std::thread;
use std::time::Duration;

use rcgen::{CertifiedKey, generate_simple_self_signed};
use remote_credential_broker::{
    CredentialIssuerTransport, IssuerAuthorization, IssuerReply, IssuerTransportFailure,
};
use remote_credential_wire::{ResponseStatus, read_request, write_response};
use remote_tls_transport::{EndpointScope, PinnedCredentialIssuerTlsTransport};
use rustls::pki_types::{CertificateDer, PrivatePkcs8KeyDer};
use rustls::{ServerConfig, ServerConnection, StreamOwned, version};
use sha2::{Digest as _, Sha256};

type TestResult<T = ()> = Result<T, Box<dyn Error>>;
const REQUEST: &[u8] = br#"{"operation":"issue"}"#;

fn new_certificate() -> TestResult<(Vec<u8>, PrivatePkcs8KeyDer<'static>)> {
    let CertifiedKey { cert, signing_key } =
        generate_simple_self_signed(vec!["localhost".to_owned()])?;
    Ok((
        cert.der().to_vec(),
        PrivatePkcs8KeyDer::from(signing_key.serialize_der()),
    ))
}

fn server_config(
    certificate: Vec<u8>,
    key: PrivatePkcs8KeyDer<'static>,
) -> TestResult<Arc<ServerConfig>> {
    let provider = Arc::new(rustls::crypto::ring::default_provider());
    let config = ServerConfig::builder_with_provider(provider)
        .with_protocol_versions(&[&version::TLS13])?
        .with_no_client_auth()
        .with_single_cert(vec![CertificateDer::from(certificate)], key.into())?;
    Ok(Arc::new(config))
}

#[derive(Clone, Copy)]
enum Behavior {
    Access,
    Rejected,
    WrongDigest,
    NonCanonical,
    Unavailable,
    Trailing,
}

fn spawn_server(
    config: Arc<ServerConfig>,
    behavior: Behavior,
) -> TestResult<(SocketAddr, thread::JoinHandle<()>)> {
    let listener = TcpListener::bind((Ipv4Addr::LOCALHOST, 0))?;
    let endpoint = listener.local_addr()?;
    let handle = thread::spawn(move || {
        let Ok((socket, _)) = listener.accept() else {
            return;
        };
        let Ok(connection) = ServerConnection::new(config) else {
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
        assert_eq!(request.payload(), REQUEST);
        let request_sha256 = hex::encode(Sha256::digest(request.payload()));
        let (status, payload) = match behavior {
            Behavior::Access | Behavior::Trailing => (
                ResponseStatus::Completed,
                format!(
                    "{{\"outcome\":\"access\",\"schema_version\":\"hwpx-agent.remote-credential-issuer-response/v1\",\"request_sha256\":\"{request_sha256}\",\"token\":\"ddd.eee.fff\"}}"
                )
                .into_bytes(),
            ),
            Behavior::Rejected => (
                ResponseStatus::Completed,
                format!(
                    "{{\"outcome\":\"rejected\",\"schema_version\":\"hwpx-agent.remote-credential-issuer-response/v1\",\"request_sha256\":\"{request_sha256}\"}}"
                )
                .into_bytes(),
            ),
            Behavior::WrongDigest => (
                ResponseStatus::Completed,
                b"{\"outcome\":\"rejected\",\"schema_version\":\"hwpx-agent.remote-credential-issuer-response/v1\",\"request_sha256\":\"0000000000000000000000000000000000000000000000000000000000000000\"}".to_vec(),
            ),
            Behavior::NonCanonical => (
                ResponseStatus::Completed,
                format!(
                    " {{\"outcome\":\"rejected\",\"schema_version\":\"hwpx-agent.remote-credential-issuer-response/v1\",\"request_sha256\":\"{request_sha256}\"}}"
                )
                .into_bytes(),
            ),
            Behavior::Unavailable => (ResponseStatus::Unavailable, Vec::new()),
        };
        if write_response(&mut stream, status, &payload).is_err() {
            return;
        }
        if matches!(behavior, Behavior::Trailing) && stream.write_all(b"x").is_err() {
            return;
        }
        stream.conn.send_close_notify();
        let _ = stream.flush();
    });
    Ok((endpoint, handle))
}

fn authorization() -> TestResult<IssuerAuthorization> {
    IssuerAuthorization::new("Bearer aaa.bbb.ccc".to_owned())
        .map_err(|error| format!("authorization: {error:?}").into())
}

#[test]
fn exact_pin_name_tls13_and_request_binding_succeed() -> TestResult {
    for behavior in [Behavior::Access, Behavior::Rejected] {
        let (certificate, key) = new_certificate()?;
        let config = server_config(certificate.clone(), key)?;
        let (endpoint, server) = spawn_server(config, behavior)?;
        let mut transport = PinnedCredentialIssuerTlsTransport::new(
            endpoint,
            EndpointScope::LoopbackQualification,
            "localhost",
            certificate,
            Duration::from_secs(5),
        )?;
        let reply = transport.exchange(&authorization()?, REQUEST)?;
        match behavior {
            Behavior::Access => assert!(matches!(reply, IssuerReply::Access(_))),
            Behavior::Rejected => assert!(matches!(reply, IssuerReply::DefinitiveRejection)),
            _ => unreachable!("bounded behavior list"),
        }
        let debug = format!("{transport:?}");
        assert!(debug.contains("<redacted>"));
        assert!(!debug.contains("localhost"));
        assert!(!debug.contains(&endpoint.port().to_string()));
        server.join().map_err(|_| "server thread panicked")?;
    }
    Ok(())
}

#[test]
fn wrong_pin_and_name_are_peer_rejections() -> TestResult {
    let (certificate, key) = new_certificate()?;
    let config = server_config(certificate.clone(), key)?;
    let (other_certificate, _) = new_certificate()?;
    let (endpoint, server) = spawn_server(config, Behavior::Access)?;
    let mut transport = PinnedCredentialIssuerTlsTransport::new(
        endpoint,
        EndpointScope::LoopbackQualification,
        "localhost",
        other_certificate,
        Duration::from_secs(5),
    )?;
    assert_eq!(
        transport.exchange(&authorization()?, REQUEST).err(),
        Some(IssuerTransportFailure::PeerRejected)
    );
    server.join().map_err(|_| "server thread panicked")?;

    let (certificate, key) = new_certificate()?;
    let config = server_config(certificate.clone(), key)?;
    let (endpoint, server) = spawn_server(config, Behavior::Access)?;
    let mut transport = PinnedCredentialIssuerTlsTransport::new(
        endpoint,
        EndpointScope::LoopbackQualification,
        "service.invalid",
        certificate,
        Duration::from_secs(5),
    )?;
    assert_eq!(
        transport.exchange(&authorization()?, REQUEST).err(),
        Some(IssuerTransportFailure::PeerRejected)
    );
    server.join().map_err(|_| "server thread panicked")?;
    Ok(())
}

#[test]
fn unavailable_malformed_digest_and_trailing_outcomes_remain_nondefinitive() -> TestResult {
    for (behavior, expected) in [
        (Behavior::Unavailable, IssuerTransportFailure::Unavailable),
        (
            Behavior::WrongDigest,
            IssuerTransportFailure::InvalidResponse,
        ),
        (
            Behavior::NonCanonical,
            IssuerTransportFailure::InvalidResponse,
        ),
        (Behavior::Trailing, IssuerTransportFailure::InvalidResponse),
    ] {
        let (certificate, key) = new_certificate()?;
        let config = server_config(certificate.clone(), key)?;
        let (endpoint, server) = spawn_server(config, behavior)?;
        let mut transport = PinnedCredentialIssuerTlsTransport::new(
            endpoint,
            EndpointScope::LoopbackQualification,
            "localhost",
            certificate,
            Duration::from_secs(5),
        )?;
        assert_eq!(
            transport.exchange(&authorization()?, REQUEST).err(),
            Some(expected)
        );
        server.join().map_err(|_| "server thread panicked")?;
    }
    Ok(())
}

#[test]
fn issuer_transport_configuration_is_bounded() -> TestResult {
    let (certificate, _) = new_certificate()?;
    let endpoint = SocketAddr::from((Ipv4Addr::LOCALHOST, 8443));
    for invalid_name in ["", "UPPER.example", "bad..example", "127.0.0.1"] {
        assert!(matches!(
            PinnedCredentialIssuerTlsTransport::new(
                endpoint,
                EndpointScope::LoopbackQualification,
                invalid_name,
                certificate.clone(),
                Duration::from_secs(1),
            ),
            Err(IssuerTransportFailure::ConfigurationRejected)
        ));
    }
    assert!(matches!(
        PinnedCredentialIssuerTlsTransport::new(
            endpoint,
            EndpointScope::LoopbackQualification,
            "localhost",
            Vec::new(),
            Duration::from_secs(1),
        ),
        Err(IssuerTransportFailure::ConfigurationRejected)
    ));
    Ok(())
}
