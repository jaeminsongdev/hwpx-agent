use std::fmt;
use std::io::Read;
use std::net::{Shutdown, SocketAddr, TcpStream};
use std::time::Duration;

use remote_sync_wire::{FrameError, ResponseStatus, read_response, write_request};

use crate::{RemoteTransport, TransportFailure};

const MAX_TIMEOUT: Duration = Duration::from_mins(1);

/// Current-PC transport that can connect only to an explicit loopback socket.
pub struct LoopbackTcpTransport {
    endpoint: SocketAddr,
    timeout: Duration,
}

impl fmt::Debug for LoopbackTcpTransport {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("LoopbackTcpTransport")
            .field("endpoint", &self.endpoint)
            .field("timeout", &self.timeout)
            .finish()
    }
}

impl LoopbackTcpTransport {
    /// Creates a bounded transport for an exact local-only endpoint.
    ///
    /// # Errors
    ///
    /// Rejects wildcard, non-loopback and zero-port endpoints or timeouts outside 1 ms..=60 s.
    pub fn new(endpoint: SocketAddr, timeout: Duration) -> Result<Self, TransportFailure> {
        if !endpoint.ip().is_loopback()
            || endpoint.port() == 0
            || timeout < Duration::from_millis(1)
            || timeout > MAX_TIMEOUT
        {
            return Err(TransportFailure::Rejected);
        }
        Ok(Self { endpoint, timeout })
    }

    #[must_use]
    pub const fn endpoint(&self) -> SocketAddr {
        self.endpoint
    }
}

impl RemoteTransport for LoopbackTcpTransport {
    fn exchange(
        &mut self,
        authorization_header: &str,
        request: &[u8],
    ) -> Result<Vec<u8>, TransportFailure> {
        let mut stream = TcpStream::connect_timeout(&self.endpoint, self.timeout)
            .map_err(|_| TransportFailure::Unavailable)?;
        stream
            .set_read_timeout(Some(self.timeout))
            .and_then(|()| stream.set_write_timeout(Some(self.timeout)))
            .map_err(|_| TransportFailure::Unavailable)?;
        write_request(&mut stream, authorization_header, request).map_err(map_frame_error)?;
        stream
            .shutdown(Shutdown::Write)
            .map_err(|_| TransportFailure::Unavailable)?;
        let response = read_response(&mut stream).map_err(map_frame_error)?;
        let mut trailing = [0_u8; 1];
        match stream.read(&mut trailing) {
            Ok(0) => {}
            Ok(_) => return Err(TransportFailure::Rejected),
            Err(_) => return Err(TransportFailure::Unavailable),
        }
        match response.status() {
            ResponseStatus::Succeeded => Ok(response.payload().to_vec()),
            ResponseStatus::Rejected => Err(TransportFailure::Rejected),
            ResponseStatus::Unavailable => Err(TransportFailure::Unavailable),
        }
    }
}

const fn map_frame_error(error: FrameError) -> TransportFailure {
    match error {
        FrameError::Rejected => TransportFailure::Rejected,
        FrameError::Unavailable => TransportFailure::Unavailable,
    }
}

#[cfg(test)]
mod tests {
    use std::io::Write;
    use std::net::{Ipv4Addr, TcpListener};
    use std::thread;

    use remote_sync_wire::{ResponseStatus, read_request, write_response};

    use super::*;

    #[test]
    fn constructor_rejects_non_loopback_and_unbounded_configuration() {
        let public = SocketAddr::from((Ipv4Addr::new(192, 0, 2, 1), 8443));
        assert!(matches!(
            LoopbackTcpTransport::new(public, Duration::from_secs(1)),
            Err(TransportFailure::Rejected)
        ));
        let wildcard = SocketAddr::from((Ipv4Addr::UNSPECIFIED, 8443));
        assert!(matches!(
            LoopbackTcpTransport::new(wildcard, Duration::from_secs(1)),
            Err(TransportFailure::Rejected)
        ));
        let local = SocketAddr::from((Ipv4Addr::LOCALHOST, 8443));
        assert!(matches!(
            LoopbackTcpTransport::new(local, Duration::ZERO),
            Err(TransportFailure::Rejected)
        ));
        assert!(matches!(
            LoopbackTcpTransport::new(local, Duration::from_secs(61)),
            Err(TransportFailure::Rejected)
        ));
    }

    #[test]
    fn trailing_response_bytes_are_rejected() {
        let listener = TcpListener::bind((Ipv4Addr::LOCALHOST, 0))
            .unwrap_or_else(|error| panic!("bind: {error}"));
        let endpoint = listener
            .local_addr()
            .unwrap_or_else(|error| panic!("address: {error}"));
        let server = thread::spawn(move || {
            let (mut stream, _) = listener
                .accept()
                .unwrap_or_else(|error| panic!("accept: {error}"));
            read_request(&mut stream).unwrap_or_else(|error| panic!("request: {error}"));
            write_response(&mut stream, ResponseStatus::Succeeded, b"{}")
                .unwrap_or_else(|error| panic!("response: {error}"));
            stream
                .write_all(b"x")
                .unwrap_or_else(|error| panic!("trailing: {error}"));
        });
        let mut transport = LoopbackTcpTransport::new(endpoint, Duration::from_secs(5))
            .unwrap_or_else(|error| panic!("transport: {error}"));
        assert_eq!(
            transport.exchange("Bearer aaa.bbb.ccc", b"{}"),
            Err(TransportFailure::Rejected)
        );
        server
            .join()
            .unwrap_or_else(|_| panic!("server thread panicked"));
    }
}
