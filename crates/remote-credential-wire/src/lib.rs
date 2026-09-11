//! Bounded framing for an authenticated credential-issuer exchange.

#![forbid(unsafe_code)]

use std::fmt;
use std::io::{Read, Write};

use thiserror::Error;
use zeroize::Zeroizing;

const REQUEST_MAGIC: &[u8; 8] = b"HWPXCIQ1";
const RESPONSE_MAGIC: &[u8; 8] = b"HWPXCIP1";
pub const MAX_AUTHORIZATION_BYTES: usize = 8_199;
pub const MAX_REQUEST_BYTES: usize = 16_384;
pub const MAX_RESPONSE_BYTES: usize = 8_192;

#[derive(Clone, Copy, Debug, Error, Eq, PartialEq)]
pub enum FrameError {
    #[error("credential issuer frame was rejected")]
    Rejected,
    #[error("credential issuer frame outcome is unavailable")]
    Unavailable,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[repr(u8)]
pub enum ResponseStatus {
    Completed = 0,
    Unavailable = 1,
}

impl ResponseStatus {
    fn parse(value: u8) -> Result<Self, FrameError> {
        match value {
            0 => Ok(Self::Completed),
            1 => Ok(Self::Unavailable),
            _ => Err(FrameError::Rejected),
        }
    }
}

pub struct ServerRequest {
    authorization_header: Zeroizing<String>,
    payload: Vec<u8>,
}

impl fmt::Debug for ServerRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ServerRequest")
            .field("authorization_header", &"<redacted>")
            .field("payload_bytes", &self.payload.len())
            .finish_non_exhaustive()
    }
}

impl ServerRequest {
    pub fn with_authorization<R>(&self, operation: impl FnOnce(&str) -> R) -> R {
        operation(self.authorization_header.as_str())
    }

    #[must_use]
    pub fn payload(&self) -> &[u8] {
        &self.payload
    }
}

pub struct ServerResponse {
    status: ResponseStatus,
    payload: Zeroizing<Vec<u8>>,
}

impl fmt::Debug for ServerResponse {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ServerResponse")
            .field("status", &self.status)
            .field("payload", &"<redacted>")
            .field("payload_bytes", &self.payload.len())
            .finish_non_exhaustive()
    }
}

impl ServerResponse {
    #[must_use]
    pub const fn status(&self) -> ResponseStatus {
        self.status
    }

    pub fn with_payload<R>(&self, operation: impl FnOnce(&[u8]) -> R) -> R {
        operation(self.payload.as_slice())
    }
}

/// Writes one complete credential-issuer request frame.
///
/// # Errors
///
/// Rejects empty or oversized fields. I/O failures are unavailable outcomes.
pub fn write_request(
    writer: &mut impl Write,
    authorization_header: &str,
    payload: &[u8],
) -> Result<(), FrameError> {
    if authorization_header.is_empty()
        || authorization_header.len() > MAX_AUTHORIZATION_BYTES
        || payload.is_empty()
        || payload.len() > MAX_REQUEST_BYTES
    {
        return Err(FrameError::Rejected);
    }
    writer
        .write_all(REQUEST_MAGIC)
        .and_then(|()| writer.write_all(&usize_to_u32(authorization_header.len())?.to_be_bytes()))
        .and_then(|()| writer.write_all(&usize_to_u32(payload.len())?.to_be_bytes()))
        .and_then(|()| writer.write_all(authorization_header.as_bytes()))
        .and_then(|()| writer.write_all(payload))
        .and_then(|()| writer.flush())
        .map_err(|_| FrameError::Unavailable)
}

/// Reads one complete credential-issuer request frame.
///
/// # Errors
///
/// Rejects malformed framing or UTF-8 and treats incomplete I/O as unavailable.
pub fn read_request(reader: &mut impl Read) -> Result<ServerRequest, FrameError> {
    let mut magic = [0_u8; 8];
    read_exact(reader, &mut magic)?;
    if &magic != REQUEST_MAGIC {
        return Err(FrameError::Rejected);
    }
    let authorization_bytes = read_bounded_length(reader, MAX_AUTHORIZATION_BYTES)?;
    let payload_bytes = read_bounded_length(reader, MAX_REQUEST_BYTES)?;
    if authorization_bytes == 0 || payload_bytes == 0 {
        return Err(FrameError::Rejected);
    }
    let mut authorization = Zeroizing::new(vec![0_u8; authorization_bytes]);
    read_exact(reader, authorization.as_mut_slice())?;
    let authorization_header = std::str::from_utf8(&authorization)
        .map(str::to_owned)
        .map(Zeroizing::new)
        .map_err(|_| FrameError::Rejected)?;
    let mut payload = vec![0_u8; payload_bytes];
    read_exact(reader, &mut payload)?;
    Ok(ServerRequest {
        authorization_header,
        payload,
    })
}

/// Writes a completed response payload or an empty unavailable outcome.
///
/// # Errors
///
/// Rejects invalid status/payload combinations and maps I/O failures to unavailable.
pub fn write_response(
    writer: &mut impl Write,
    status: ResponseStatus,
    payload: &[u8],
) -> Result<(), FrameError> {
    if payload.len() > MAX_RESPONSE_BYTES
        || (status == ResponseStatus::Completed && payload.is_empty())
        || (status == ResponseStatus::Unavailable && !payload.is_empty())
    {
        return Err(FrameError::Rejected);
    }
    writer
        .write_all(RESPONSE_MAGIC)
        .and_then(|()| writer.write_all(&[status as u8]))
        .and_then(|()| writer.write_all(&usize_to_u32(payload.len())?.to_be_bytes()))
        .and_then(|()| writer.write_all(payload))
        .and_then(|()| writer.flush())
        .map_err(|_| FrameError::Unavailable)
}

/// Reads one complete response and zeroizes its credential-bearing payload on drop.
///
/// # Errors
///
/// Rejects malformed status/payload combinations and treats incomplete I/O as unavailable.
pub fn read_response(reader: &mut impl Read) -> Result<ServerResponse, FrameError> {
    let mut magic = [0_u8; 8];
    read_exact(reader, &mut magic)?;
    if &magic != RESPONSE_MAGIC {
        return Err(FrameError::Rejected);
    }
    let mut encoded_status = [0_u8; 1];
    read_exact(reader, &mut encoded_status)?;
    let status = ResponseStatus::parse(encoded_status[0])?;
    let payload_bytes = read_bounded_length(reader, MAX_RESPONSE_BYTES)?;
    if (status == ResponseStatus::Completed && payload_bytes == 0)
        || (status == ResponseStatus::Unavailable && payload_bytes != 0)
    {
        return Err(FrameError::Rejected);
    }
    let mut payload = Zeroizing::new(vec![0_u8; payload_bytes]);
    read_exact(reader, payload.as_mut_slice())?;
    Ok(ServerResponse { status, payload })
}

fn read_bounded_length(reader: &mut impl Read, maximum: usize) -> Result<usize, FrameError> {
    let mut encoded = [0_u8; 4];
    read_exact(reader, &mut encoded)?;
    let value = usize::try_from(u32::from_be_bytes(encoded)).map_err(|_| FrameError::Rejected)?;
    if value > maximum {
        return Err(FrameError::Rejected);
    }
    Ok(value)
}

fn read_exact(reader: &mut impl Read, buffer: &mut [u8]) -> Result<(), FrameError> {
    reader
        .read_exact(buffer)
        .map_err(|_| FrameError::Unavailable)
}

fn usize_to_u32(value: usize) -> Result<u32, std::io::Error> {
    u32::try_from(value).map_err(|_| std::io::Error::other("frame length exceeds u32"))
}

#[cfg(test)]
mod tests {
    use std::io::Cursor;

    use super::*;

    #[test]
    fn exact_frames_round_trip_and_redact_secrets() {
        let mut request_bytes = Vec::new();
        write_request(
            &mut request_bytes,
            "Bearer aaa.bbb.ccc",
            br#"{"operation":"issue"}"#,
        )
        .unwrap_or_else(|error| panic!("write request: {error}"));
        let request = read_request(&mut Cursor::new(request_bytes))
            .unwrap_or_else(|error| panic!("read request: {error}"));
        assert_eq!(
            request.with_authorization(str::to_owned),
            "Bearer aaa.bbb.ccc"
        );
        assert_eq!(request.payload(), br#"{"operation":"issue"}"#);
        assert!(!format!("{request:?}").contains("aaa"));

        let mut response_bytes = Vec::new();
        write_response(
            &mut response_bytes,
            ResponseStatus::Completed,
            br#"{"outcome":"access","token":"ddd.eee.fff"}"#,
        )
        .unwrap_or_else(|error| panic!("write response: {error}"));
        let response = read_response(&mut Cursor::new(response_bytes))
            .unwrap_or_else(|error| panic!("read response: {error}"));
        assert_eq!(response.status(), ResponseStatus::Completed);
        assert!(response.with_payload(|value| value.ends_with(b"fff\"}")));
        assert!(!format!("{response:?}").contains("ddd"));
    }

    #[test]
    fn malformed_and_status_drift_fail_closed() {
        assert_eq!(
            write_request(&mut Vec::new(), "", b"{}").err(),
            Some(FrameError::Rejected)
        );
        assert_eq!(
            write_response(&mut Vec::new(), ResponseStatus::Unavailable, b"unexpected").err(),
            Some(FrameError::Rejected)
        );
        let mut wrong_magic = b"HWPXRSQ1".to_vec();
        wrong_magic.extend_from_slice(&0_u32.to_be_bytes());
        assert_eq!(
            read_request(&mut Cursor::new(wrong_magic)).err(),
            Some(FrameError::Rejected)
        );
    }
}
