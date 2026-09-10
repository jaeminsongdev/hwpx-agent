//! TLS 1.3 transport for one exact remote-sync endpoint and certificate.

#![forbid(unsafe_code)]

use std::fmt;
use std::io::Read;
use std::net::{IpAddr, Ipv4Addr, Ipv6Addr, SocketAddr, TcpStream};
use std::sync::Arc;
use std::time::Duration;

use local_sync::{RemoteTransport, TransportFailure};
use remote_sync_wire::{FrameError, ResponseStatus, read_response, write_request};
use rustls::pki_types::{CertificateDer, ServerName};
use rustls::{ClientConfig, ClientConnection, RootCertStore, StreamOwned, version};
use sha2::{Digest as _, Sha256};

const MAX_TIMEOUT: Duration = Duration::from_mins(1);
const MAX_CERTIFICATE_BYTES: usize = 32_768;
const MAX_SERVER_NAME_BYTES: usize = 253;

/// Admits either an internet-routable product endpoint or an explicit local qualification target.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum EndpointScope {
    /// Requires a globally routable IP address.
    PublicRemote,
    /// Requires a loopback IP address and must not be used as production evidence.
    LoopbackQualification,
}

/// One exact endpoint, DNS identity and leaf-certificate pin using TLS 1.3 only.
pub struct PinnedTlsTcpTransport {
    endpoint: SocketAddr,
    endpoint_scope: EndpointScope,
    server_name: ServerName<'static>,
    expected_leaf_sha256: [u8; 32],
    config: Arc<ClientConfig>,
    timeout: Duration,
}

impl fmt::Debug for PinnedTlsTcpTransport {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("PinnedTlsTcpTransport")
            .field("endpoint", &"<redacted>")
            .field("endpoint_scope", &self.endpoint_scope)
            .field("server_name", &"<redacted>")
            .field("expected_leaf_sha256", &"<redacted>")
            .field("config", &"<redacted>")
            .field("tls_version", &"TLS1.3")
            .field("timeout", &self.timeout)
            .finish()
    }
}

impl PinnedTlsTcpTransport {
    /// Constructs a bounded transport without DNS resolution or ambient trust roots.
    ///
    /// The supplied DER certificate is the only trust anchor and its exact leaf digest must also
    /// match after a successful `WebPKI` handshake. This keeps name, validity and signature checks
    /// active while preventing fallback to an operating-system or bundled root set.
    ///
    /// # Errors
    ///
    /// Rejects unsafe endpoints, non-canonical DNS names, invalid/oversized certificates and
    /// timeouts outside 1 ms..=60 s.
    pub fn new(
        endpoint: SocketAddr,
        endpoint_scope: EndpointScope,
        server_name: &str,
        pinned_certificate_der: Vec<u8>,
        timeout: Duration,
    ) -> Result<Self, TransportFailure> {
        validate_endpoint(endpoint, endpoint_scope)?;
        validate_server_name(server_name)?;
        if pinned_certificate_der.is_empty() || pinned_certificate_der.len() > MAX_CERTIFICATE_BYTES
        {
            return Err(TransportFailure::Rejected);
        }
        if timeout < Duration::from_millis(1) || timeout > MAX_TIMEOUT {
            return Err(TransportFailure::Rejected);
        }

        let certificate = CertificateDer::from(pinned_certificate_der);
        let expected_leaf_sha256 = Sha256::digest(certificate.as_ref()).into();
        let mut roots = RootCertStore::empty();
        roots
            .add(certificate)
            .map_err(|_| TransportFailure::Rejected)?;
        let provider = Arc::new(rustls::crypto::ring::default_provider());
        let config = ClientConfig::builder_with_provider(Arc::clone(&provider))
            .with_protocol_versions(&[&version::TLS13])
            .map_err(|_| TransportFailure::Rejected)?
            .with_root_certificates(roots)
            .with_no_client_auth();
        let server_name =
            ServerName::try_from(server_name.to_owned()).map_err(|_| TransportFailure::Rejected)?;
        if !matches!(server_name, ServerName::DnsName(_)) {
            return Err(TransportFailure::Rejected);
        }
        Ok(Self {
            endpoint,
            endpoint_scope,
            server_name,
            expected_leaf_sha256,
            config: Arc::new(config),
            timeout,
        })
    }
}

impl RemoteTransport for PinnedTlsTcpTransport {
    fn exchange(
        &mut self,
        authorization_header: &str,
        request: &[u8],
    ) -> Result<Vec<u8>, TransportFailure> {
        let mut socket = TcpStream::connect_timeout(&self.endpoint, self.timeout)
            .map_err(|_| TransportFailure::Unavailable)?;
        socket
            .set_read_timeout(Some(self.timeout))
            .and_then(|()| socket.set_write_timeout(Some(self.timeout)))
            .map_err(|_| TransportFailure::Unavailable)?;
        let mut connection =
            ClientConnection::new(Arc::clone(&self.config), self.server_name.clone())
                .map_err(|_| TransportFailure::Rejected)?;
        connection
            .complete_io(&mut socket)
            .map_err(|error| classify_tls_io_error(&error))?;
        let peer = connection
            .peer_certificates()
            .and_then(|certificates| certificates.first())
            .ok_or(TransportFailure::Rejected)?;
        let actual_leaf_sha256: [u8; 32] = Sha256::digest(peer.as_ref()).into();
        if actual_leaf_sha256 != self.expected_leaf_sha256 {
            return Err(TransportFailure::Rejected);
        }

        let mut stream = StreamOwned::new(connection, socket);
        write_request(&mut stream, authorization_header, request).map_err(map_frame_error)?;
        let response = read_response(&mut stream).map_err(map_frame_error)?;
        let mut trailing = [0_u8; 1];
        match stream.read(&mut trailing) {
            Ok(0) => {}
            Ok(_) => return Err(TransportFailure::Rejected),
            Err(error) => return Err(classify_tls_io_error(&error)),
        }
        match response.status() {
            ResponseStatus::Succeeded => Ok(response.payload().to_vec()),
            ResponseStatus::Rejected => Err(TransportFailure::Rejected),
            ResponseStatus::Unavailable => Err(TransportFailure::Unavailable),
        }
    }
}

fn validate_endpoint(
    endpoint: SocketAddr,
    endpoint_scope: EndpointScope,
) -> Result<(), TransportFailure> {
    let rejected = endpoint.port() == 0
        || match endpoint_scope {
            EndpointScope::PublicRemote => !is_public_remote_ip(endpoint.ip()),
            EndpointScope::LoopbackQualification => !endpoint.ip().is_loopback(),
        };
    if rejected {
        return Err(TransportFailure::Rejected);
    }
    Ok(())
}

fn is_public_remote_ip(address: IpAddr) -> bool {
    match address {
        IpAddr::V4(address) => is_public_remote_ipv4(address),
        IpAddr::V6(address) => is_public_remote_ipv6(address),
    }
}

fn is_public_remote_ipv4(address: Ipv4Addr) -> bool {
    let [first, second, third, fourth] = address.octets();
    !(first == 0
        || address.is_private()
        || (first == 100 && (64..=127).contains(&second))
        || address.is_loopback()
        || address.is_link_local()
        || (first == 192 && second == 0 && third == 0 && fourth != 9 && fourth != 10)
        || address.is_documentation()
        || (first == 198 && (second == 18 || second == 19))
        || first >= 240
        || address.is_broadcast()
        || address.is_multicast())
}

fn is_public_remote_ipv6(address: Ipv6Addr) -> bool {
    let segments = address.segments();
    let bits = u128::from_be_bytes(address.octets());
    let global_ietf_exception = bits == 0x2001_0001_0000_0000_0000_0000_0000_0001
        || bits == 0x2001_0001_0000_0000_0000_0000_0000_0002
        || matches!(segments, [0x2001, 3, ..])
        || matches!(segments, [0x2001, 4, 0x112, ..])
        || matches!(segments, [0x2001, second, ..] if (0x20..=0x3f).contains(&second));
    let nonglobal_ietf_assignment =
        matches!(segments, [0x2001, second, ..] if second < 0x200) && !global_ietf_exception;
    let documentation = matches!(segments, [0x2001, 0x0db8, ..])
        || matches!(segments, [0x3fff, second, ..] if second <= 0x0fff);
    !(address.is_unspecified()
        || address.is_loopback()
        || address.is_multicast()
        || matches!(segments, [0, 0, 0, 0, 0, 0xffff, _, _])
        || matches!(segments, [0x64, 0xff9b, 1, ..])
        || matches!(segments, [0x100, 0, 0, 0, ..])
        || nonglobal_ietf_assignment
        || matches!(segments, [0x2002, ..])
        || documentation
        || matches!(segments, [0x5f00, ..])
        || address.is_unique_local()
        || address.is_unicast_link_local())
}

fn validate_server_name(value: &str) -> Result<(), TransportFailure> {
    if value.is_empty()
        || value.len() > MAX_SERVER_NAME_BYTES
        || !value.is_ascii()
        || value.ends_with('.')
    {
        return Err(TransportFailure::Rejected);
    }
    for label in value.split('.') {
        if label.is_empty()
            || label.len() > 63
            || label.starts_with('-')
            || label.ends_with('-')
            || !label
                .bytes()
                .all(|byte| byte.is_ascii_lowercase() || byte.is_ascii_digit() || byte == b'-')
        {
            return Err(TransportFailure::Rejected);
        }
    }
    Ok(())
}

fn classify_tls_io_error(error: &std::io::Error) -> TransportFailure {
    if error
        .get_ref()
        .and_then(|inner| inner.downcast_ref::<rustls::Error>())
        .is_some()
    {
        TransportFailure::Rejected
    } else {
        TransportFailure::Unavailable
    }
}

const fn map_frame_error(error: FrameError) -> TransportFailure {
    match error {
        FrameError::Rejected => TransportFailure::Rejected,
        FrameError::Unavailable => TransportFailure::Unavailable,
    }
}
