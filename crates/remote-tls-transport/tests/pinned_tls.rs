use std::error::Error;
use std::io::Write;
use std::net::{Ipv4Addr, SocketAddr, TcpListener};
use std::sync::Arc;
use std::thread;
use std::time::Duration;

use local_sync::{RemoteTransport, TransportFailure};
use rcgen::{CertifiedKey, generate_simple_self_signed};
use remote_sync_wire::{ResponseStatus, read_request, write_response};
use remote_tls_transport::{EndpointScope, PinnedTlsTcpTransport};
use rustls::pki_types::{CertificateDer, PrivatePkcs8KeyDer};
use rustls::{ServerConfig, ServerConnection, StreamOwned, version};

type TestResult<T = ()> = Result<T, Box<dyn Error>>;

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

fn spawn_server(
    config: Arc<ServerConfig>,
    response: ResponseStatus,
    trailing: bool,
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
        assert_eq!(request.authorization_header(), "Bearer aaa.bbb.ccc");
        assert_eq!(request.payload(), b"{\"operation\":\"pull\"}");
        let payload = if response == ResponseStatus::Succeeded {
            b"{}".as_slice()
        } else {
            b"".as_slice()
        };
        if write_response(&mut stream, response, payload).is_err() {
            return;
        }
        if trailing && stream.write_all(b"x").is_err() {
            return;
        }
        stream.conn.send_close_notify();
        let _ = stream.flush();
    });
    Ok((endpoint, handle))
}

#[test]
fn exact_pin_name_and_tls13_exchange_succeeds() -> TestResult {
    let (certificate, key) = new_certificate()?;
    let config = server_config(certificate.clone(), key)?;
    let (endpoint, server) = spawn_server(config, ResponseStatus::Succeeded, false)?;
    let mut transport = PinnedTlsTcpTransport::new(
        endpoint,
        EndpointScope::LoopbackQualification,
        "localhost",
        certificate,
        Duration::from_secs(5),
    )?;
    assert_eq!(
        transport.exchange("Bearer aaa.bbb.ccc", b"{\"operation\":\"pull\"}")?,
        b"{}"
    );
    server.join().map_err(|_| "server thread panicked")?;
    Ok(())
}

#[test]
fn wrong_pin_and_wrong_name_fail_before_request_dispatch() -> TestResult {
    let (certificate, key) = new_certificate()?;
    let config = server_config(certificate.clone(), key)?;
    let (other_certificate, _) = new_certificate()?;
    let (endpoint, server) = spawn_server(config, ResponseStatus::Succeeded, false)?;
    let mut wrong_pin = PinnedTlsTcpTransport::new(
        endpoint,
        EndpointScope::LoopbackQualification,
        "localhost",
        other_certificate,
        Duration::from_secs(5),
    )?;
    assert_eq!(
        wrong_pin.exchange("Bearer aaa.bbb.ccc", b"{\"operation\":\"pull\"}"),
        Err(TransportFailure::Rejected)
    );
    server.join().map_err(|_| "server thread panicked")?;

    let (certificate, key) = new_certificate()?;
    let config = server_config(certificate.clone(), key)?;
    let (endpoint, server) = spawn_server(config, ResponseStatus::Succeeded, false)?;
    let mut wrong_name = PinnedTlsTcpTransport::new(
        endpoint,
        EndpointScope::LoopbackQualification,
        "service.invalid",
        certificate,
        Duration::from_secs(5),
    )?;
    assert_eq!(
        wrong_name.exchange("Bearer aaa.bbb.ccc", b"{\"operation\":\"pull\"}"),
        Err(TransportFailure::Rejected)
    );
    server.join().map_err(|_| "server thread panicked")?;
    Ok(())
}

#[test]
fn remote_status_trailing_data_and_unavailable_endpoint_are_typed() -> TestResult {
    for (status, expected) in [
        (ResponseStatus::Rejected, TransportFailure::Rejected),
        (ResponseStatus::Unavailable, TransportFailure::Unavailable),
    ] {
        let (certificate, key) = new_certificate()?;
        let config = server_config(certificate.clone(), key)?;
        let (endpoint, server) = spawn_server(config, status, false)?;
        let mut transport = PinnedTlsTcpTransport::new(
            endpoint,
            EndpointScope::LoopbackQualification,
            "localhost",
            certificate,
            Duration::from_secs(5),
        )?;
        assert_eq!(
            transport.exchange("Bearer aaa.bbb.ccc", b"{\"operation\":\"pull\"}"),
            Err(expected)
        );
        server.join().map_err(|_| "server thread panicked")?;
    }

    let (certificate, key) = new_certificate()?;
    let config = server_config(certificate.clone(), key)?;
    let (endpoint, server) = spawn_server(config, ResponseStatus::Succeeded, true)?;
    let mut transport = PinnedTlsTcpTransport::new(
        endpoint,
        EndpointScope::LoopbackQualification,
        "localhost",
        certificate.clone(),
        Duration::from_secs(5),
    )?;
    assert_eq!(
        transport.exchange("Bearer aaa.bbb.ccc", b"{\"operation\":\"pull\"}"),
        Err(TransportFailure::Rejected)
    );
    server.join().map_err(|_| "server thread panicked")?;

    let listener = TcpListener::bind((Ipv4Addr::LOCALHOST, 0))?;
    let unavailable = listener.local_addr()?;
    drop(listener);
    let mut transport = PinnedTlsTcpTransport::new(
        unavailable,
        EndpointScope::LoopbackQualification,
        "localhost",
        certificate,
        Duration::from_millis(100),
    )?;
    assert_eq!(
        transport.exchange("Bearer aaa.bbb.ccc", b"{\"operation\":\"pull\"}"),
        Err(TransportFailure::Unavailable)
    );
    Ok(())
}

#[test]
fn configuration_and_debug_are_bounded_and_redacted() -> TestResult {
    let (certificate, _) = new_certificate()?;
    let endpoint = SocketAddr::from((Ipv4Addr::LOCALHOST, 8443));
    for invalid in [
        "",
        "UPPER.example",
        "-bad.example",
        "bad-.example",
        "bad..example",
    ] {
        assert!(matches!(
            PinnedTlsTcpTransport::new(
                endpoint,
                EndpointScope::LoopbackQualification,
                invalid,
                certificate.clone(),
                Duration::from_secs(1)
            ),
            Err(TransportFailure::Rejected)
        ));
    }
    assert!(matches!(
        PinnedTlsTcpTransport::new(
            endpoint,
            EndpointScope::LoopbackQualification,
            "localhost",
            Vec::new(),
            Duration::from_secs(1)
        ),
        Err(TransportFailure::Rejected)
    ));
    assert!(matches!(
        PinnedTlsTcpTransport::new(
            endpoint,
            EndpointScope::LoopbackQualification,
            "localhost",
            certificate.clone(),
            Duration::ZERO
        ),
        Err(TransportFailure::Rejected)
    ));
    let transport = PinnedTlsTcpTransport::new(
        endpoint,
        EndpointScope::LoopbackQualification,
        "localhost",
        certificate,
        Duration::from_secs(1),
    )?;
    let debug = format!("{transport:?}");
    assert!(debug.contains("<redacted>"));
    assert!(!debug.contains("localhost"));
    assert!(!debug.contains("8443"));
    Ok(())
}

#[test]
fn endpoint_scope_and_dns_identity_are_exact() -> TestResult {
    let (certificate, _) = new_certificate()?;
    let endpoint = SocketAddr::from((Ipv4Addr::LOCALHOST, 8443));
    for (candidate, scope, server_name) in [
        (
            SocketAddr::from((Ipv4Addr::UNSPECIFIED, 8443)),
            EndpointScope::LoopbackQualification,
            "localhost",
        ),
        (endpoint, EndpointScope::PublicRemote, "localhost"),
        (
            SocketAddr::from(([10, 0, 0, 1], 8443)),
            EndpointScope::PublicRemote,
            "service.example",
        ),
        (
            "[2001:db8::1]:8443".parse()?,
            EndpointScope::PublicRemote,
            "service.example",
        ),
        (
            "[2002::1]:8443".parse()?,
            EndpointScope::PublicRemote,
            "service.example",
        ),
        (
            "[3fff::1]:8443".parse()?,
            EndpointScope::PublicRemote,
            "service.example",
        ),
        (
            "[5f00::1]:8443".parse()?,
            EndpointScope::PublicRemote,
            "service.example",
        ),
        (
            "[ff02::1]:8443".parse()?,
            EndpointScope::PublicRemote,
            "service.example",
        ),
        (endpoint, EndpointScope::LoopbackQualification, "127.0.0.1"),
    ] {
        assert!(matches!(
            PinnedTlsTcpTransport::new(
                candidate,
                scope,
                server_name,
                certificate.clone(),
                Duration::from_secs(1)
            ),
            Err(TransportFailure::Rejected)
        ));
    }

    let (certificate, _) = new_certificate()?;
    PinnedTlsTcpTransport::new(
        SocketAddr::from(([1, 1, 1, 1], 8443)),
        EndpointScope::PublicRemote,
        "service.example",
        certificate,
        Duration::from_secs(1),
    )?;
    let public_ipv6: SocketAddr = "[2606:4700:4700::1111]:8443".parse()?;
    let (certificate, _) = new_certificate()?;
    PinnedTlsTcpTransport::new(
        public_ipv6,
        EndpointScope::PublicRemote,
        "service.example",
        certificate,
        Duration::from_secs(1),
    )?;
    Ok(())
}

#[test]
fn malformed_certificate_and_frame_inputs_fail_closed() -> TestResult {
    let endpoint = SocketAddr::from((Ipv4Addr::LOCALHOST, 8443));
    assert!(matches!(
        PinnedTlsTcpTransport::new(
            endpoint,
            EndpointScope::LoopbackQualification,
            "localhost",
            vec![1, 2, 3],
            Duration::from_secs(1)
        ),
        Err(TransportFailure::Rejected)
    ));

    let (certificate, key) = new_certificate()?;
    let config = server_config(certificate.clone(), key)?;
    let (endpoint, server) = spawn_server(config, ResponseStatus::Succeeded, false)?;
    let mut transport = PinnedTlsTcpTransport::new(
        endpoint,
        EndpointScope::LoopbackQualification,
        "localhost",
        certificate,
        Duration::from_secs(5),
    )?;
    assert_eq!(
        transport.exchange("", b"{\"operation\":\"pull\"}"),
        Err(TransportFailure::Rejected)
    );
    drop(transport);
    server.join().map_err(|_| "server thread panicked")?;
    Ok(())
}
