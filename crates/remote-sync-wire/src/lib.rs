//! Bounded binary framing shared by the current-PC P17 loopback client and host.

#![forbid(unsafe_code)]

use std::fmt;
use std::io::{Read, Write};

use thiserror::Error;
use zeroize::Zeroizing;

const REQUEST_MAGIC: &[u8; 8] = b"HWPXRSQ1";
const RESPONSE_MAGIC: &[u8; 8] = b"HWPXRSP1";
pub const MAX_AUTHORIZATION_BYTES: usize = 8_199;
pub const MAX_REQUEST_BYTES: usize = 16_384;
pub const MAX_RESPONSE_BYTES: usize = 65_536;

#[derive(Clone, Copy, Debug, Error, Eq, PartialEq)]
pub enum FrameError {
    #[error("remote sync frame was rejected")]
    Rejected,
    #[error("remote sync frame outcome is unavailable")]
    Unavailable,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[repr(u8)]
pub enum ResponseStatus {
    Succeeded = 0,
    Rejected = 1,
    Unavailable = 2,
}

impl ResponseStatus {
    fn parse(value: u8) -> Result<Self, FrameError> {
        match value {
            0 => Ok(Self::Succeeded),
            1 => Ok(Self::Rejected),
            2 => Ok(Self::Unavailable),
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
            .finish()
    }
}

impl ServerRequest {
    #[must_use]
    pub fn authorization_header(&self) -> &str {
        self.authorization_header.as_str()
    }

    #[must_use]
    pub fn payload(&self) -> &[u8] {
        &self.payload
    }
}

#[derive(Debug, Eq, PartialEq)]
pub struct ServerResponse {
    status: ResponseStatus,
    payload: Vec<u8>,
}

impl ServerResponse {
    #[must_use]
    pub const fn status(&self) -> ResponseStatus {
        self.status
    }

    #[must_use]
    pub fn payload(&self) -> &[u8] {
        &self.payload
    }
}

/// Writes one complete, bounded client request frame.
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

/// Reads one complete, bounded client request frame.
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

/// Writes one complete, bounded host response frame.
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
        || (status == ResponseStatus::Succeeded && payload.is_empty())
        || (status != ResponseStatus::Succeeded && !payload.is_empty())
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

/// Reads one complete, bounded host response frame.
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
    if (status == ResponseStatus::Succeeded && payload_bytes == 0)
        || (status != ResponseStatus::Succeeded && payload_bytes != 0)
    {
        return Err(FrameError::Rejected);
    }
    let mut payload = vec![0_u8; payload_bytes];
    read_exact(reader, &mut payload)?;
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
    fn request_round_trip_redacts_authorization() {
        let mut encoded = Vec::new();
        write_request(
            &mut encoded,
            "Bearer aaa.bbb.ccc",
            br#"{"operation":"checkpoint"}"#,
        )
        .unwrap_or_else(|error| panic!("write: {error}"));
        let request =
            read_request(&mut Cursor::new(encoded)).unwrap_or_else(|error| panic!("read: {error}"));
        assert_eq!(request.authorization_header(), "Bearer aaa.bbb.ccc");
        assert_eq!(request.payload(), br#"{"operation":"checkpoint"}"#);
        assert!(!format!("{request:?}").contains("aaa"));
    }

    #[test]
    fn every_response_status_round_trips() {
        for (status, payload) in [
            (ResponseStatus::Succeeded, b"{}".as_slice()),
            (ResponseStatus::Rejected, b"".as_slice()),
            (ResponseStatus::Unavailable, b"".as_slice()),
        ] {
            let mut encoded = Vec::new();
            write_response(&mut encoded, status, payload)
                .unwrap_or_else(|error| panic!("write: {error}"));
            let response = read_response(&mut Cursor::new(encoded))
                .unwrap_or_else(|error| panic!("read: {error}"));
            assert_eq!(response.status(), status);
            assert_eq!(response.payload(), payload);
        }
    }

    #[test]
    fn malformed_or_oversized_frames_fail_closed() {
        let mut oversized = Vec::from(REQUEST_MAGIC.as_slice());
        oversized.extend_from_slice(&u32::MAX.to_be_bytes());
        oversized.extend_from_slice(&1_u32.to_be_bytes());
        assert!(matches!(
            read_request(&mut Cursor::new(oversized)),
            Err(FrameError::Rejected)
        ));

        let mut truncated = Vec::new();
        write_request(&mut truncated, "Bearer aaa.bbb.ccc", b"{}")
            .unwrap_or_else(|error| panic!("write: {error}"));
        truncated.pop();
        assert!(matches!(
            read_request(&mut Cursor::new(truncated)),
            Err(FrameError::Unavailable)
        ));

        assert_eq!(
            write_response(&mut Vec::new(), ResponseStatus::Rejected, b"payload"),
            Err(FrameError::Rejected)
        );
    }
}
