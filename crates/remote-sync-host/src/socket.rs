use std::fmt;
use std::io::Read;
use std::net::{Shutdown, SocketAddr, TcpListener, TcpStream};
use std::time::Duration;

use remote_sync_wire::{FrameError, ResponseStatus, read_request, write_response};
use thiserror::Error;
use uuid::Uuid;

use crate::{CheckpointDispatcher, CheckpointHost, CheckpointHostFailure};
use local_sync::CheckpointServiceContext;

const MAX_TIMEOUT: Duration = Duration::from_mins(1);
const CONFIGURATION_REQUEST_ID: &str = "req_remote_00000000000000000000000000000000";

#[derive(Clone, Copy, Debug, Error, Eq, PartialEq)]
pub enum CheckpointServerFailure {
    #[error("checkpoint server configuration or frame was rejected")]
    Rejected,
    #[error("checkpoint server outcome is unavailable")]
    Unavailable,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum CheckpointServeOutcome {
    Succeeded,
    Rejected,
    Unavailable,
}

/// Single-listener current-PC checkpoint server restricted to an exact loopback endpoint.
pub struct LoopbackCheckpointServer<D> {
    listener: TcpListener,
    host: CheckpointHost<D>,
    locale: String,
    io_timeout: Duration,
}

impl<D> fmt::Debug for LoopbackCheckpointServer<D> {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("LoopbackCheckpointServer")
            .field("local_addr", &self.listener.local_addr().ok())
            .field("host", &"<redacted>")
            .field("locale", &self.locale)
            .field("io_timeout", &self.io_timeout)
            .finish()
    }
}

impl<D> LoopbackCheckpointServer<D> {
    /// Binds a local-only listener. Port zero is accepted only to obtain an OS-selected local port.
    ///
    /// # Errors
    ///
    /// Rejects non-loopback addresses, malformed locales and timeouts outside 1 ms..=60 s.
    pub fn bind(
        endpoint: SocketAddr,
        host: CheckpointHost<D>,
        locale: String,
        io_timeout: Duration,
    ) -> Result<Self, CheckpointServerFailure> {
        if !endpoint.ip().is_loopback()
            || CheckpointServiceContext::new(CONFIGURATION_REQUEST_ID.to_owned(), locale.clone())
                .is_err()
            || io_timeout < Duration::from_millis(1)
            || io_timeout > MAX_TIMEOUT
        {
            return Err(CheckpointServerFailure::Rejected);
        }
        let listener =
            TcpListener::bind(endpoint).map_err(|_| CheckpointServerFailure::Unavailable)?;
        Ok(Self {
            listener,
            host,
            locale,
            io_timeout,
        })
    }

    /// Returns the exact OS-bound local address.
    ///
    /// # Errors
    ///
    /// Returns unavailable if the socket address can no longer be read.
    pub fn local_addr(&self) -> Result<SocketAddr, CheckpointServerFailure> {
        self.listener
            .local_addr()
            .map_err(|_| CheckpointServerFailure::Unavailable)
    }
}

impl<D> LoopbackCheckpointServer<D>
where
    D: CheckpointDispatcher,
{
    /// Accepts and resolves exactly one connection with a server-derived request identity and time.
    ///
    /// # Errors
    ///
    /// Returns unavailable when accepting or writing the definitive framed outcome fails.
    pub fn serve_one_at(
        &self,
        now_unix_seconds: u64,
    ) -> Result<CheckpointServeOutcome, CheckpointServerFailure> {
        if now_unix_seconds == 0 {
            return Err(CheckpointServerFailure::Rejected);
        }
        let (mut stream, peer) = self
            .listener
            .accept()
            .map_err(|_| CheckpointServerFailure::Unavailable)?;
        if !peer.ip().is_loopback() {
            write_outcome(&mut stream, ResponseStatus::Rejected, &[])?;
            return Ok(CheckpointServeOutcome::Rejected);
        }
        stream
            .set_read_timeout(Some(self.io_timeout))
            .and_then(|()| stream.set_write_timeout(Some(self.io_timeout)))
            .map_err(|_| CheckpointServerFailure::Unavailable)?;
        let request = match read_request(&mut stream) {
            Ok(request) => request,
            Err(FrameError::Rejected) => {
                write_outcome(&mut stream, ResponseStatus::Rejected, &[])?;
                return Ok(CheckpointServeOutcome::Rejected);
            }
            Err(FrameError::Unavailable) => {
                write_outcome(&mut stream, ResponseStatus::Unavailable, &[])?;
                return Ok(CheckpointServeOutcome::Unavailable);
            }
        };
        let mut trailing = [0_u8; 1];
        match stream.read(&mut trailing) {
            Ok(0) => {}
            Ok(_) => {
                write_outcome(&mut stream, ResponseStatus::Rejected, &[])?;
                return Ok(CheckpointServeOutcome::Rejected);
            }
            Err(_) => {
                write_outcome(&mut stream, ResponseStatus::Unavailable, &[])?;
                return Ok(CheckpointServeOutcome::Unavailable);
            }
        }
        let request_id = format!("req_remote_{}", Uuid::new_v4().simple());
        match self.host.handle_checkpoint(
            request.authorization_header(),
            request.payload(),
            request_id,
            self.locale.clone(),
            now_unix_seconds,
        ) {
            Ok(payload) => {
                write_outcome(&mut stream, ResponseStatus::Succeeded, &payload)?;
                Ok(CheckpointServeOutcome::Succeeded)
            }
            Err(CheckpointHostFailure::Rejected) => {
                write_outcome(&mut stream, ResponseStatus::Rejected, &[])?;
                Ok(CheckpointServeOutcome::Rejected)
            }
            Err(CheckpointHostFailure::Unavailable) => {
                write_outcome(&mut stream, ResponseStatus::Unavailable, &[])?;
                Ok(CheckpointServeOutcome::Unavailable)
            }
        }
    }
}

fn write_outcome(
    stream: &mut TcpStream,
    status: ResponseStatus,
    payload: &[u8],
) -> Result<(), CheckpointServerFailure> {
    write_response(stream, status, payload).map_err(|_| CheckpointServerFailure::Unavailable)?;
    stream
        .shutdown(Shutdown::Write)
        .map_err(|_| CheckpointServerFailure::Unavailable)
}
