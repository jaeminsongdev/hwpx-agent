use std::fmt;

use artifact_service::{ArtifactId, SubjectDigest, TenantId};
use base64::Engine as _;
use base64::engine::general_purpose::URL_SAFE_NO_PAD;
use hmac::{Hmac, Mac as _};
use revision_service::{BranchId, ProjectId, RevisionHead, RevisionId};
use serde::{Deserialize, Serialize};
use sha2::Sha256;
use zeroize::Zeroizing;

use crate::types::{HistoryError, HistoryRequestContext, MAX_HISTORY_PAGE_SIZE};

type HmacSha256 = Hmac<Sha256>;
const CURSOR_VERSION: &str = "v1";
const MAX_CURSOR_BYTES: usize = 4_096;
const MIN_KEY_BYTES: usize = 32;
const MAX_KEY_BYTES: usize = 128;
const MAX_TTL_SECONDS: u64 = 900;

#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub(crate) enum CursorClaims {
    History {
        tenant_id: TenantId,
        subject_sha256: SubjectDigest,
        project_id: ProjectId,
        branch_id: BranchId,
        snapshot_head: RevisionHead,
        next_index: u32,
        page_size: u16,
        expires_at_unix_seconds: u64,
    },
    SemanticDiff {
        tenant_id: TenantId,
        subject_sha256: SubjectDigest,
        project_id: ProjectId,
        revision_id: RevisionId,
        artifact_id: ArtifactId,
        expires_at_unix_seconds: u64,
    },
}

impl CursorClaims {
    const fn expires_at_unix_seconds(&self) -> u64 {
        match self {
            Self::History {
                expires_at_unix_seconds,
                ..
            }
            | Self::SemanticDiff {
                expires_at_unix_seconds,
                ..
            } => *expires_at_unix_seconds,
        }
    }

    const fn tenant_id(&self) -> TenantId {
        match self {
            Self::History { tenant_id, .. } | Self::SemanticDiff { tenant_id, .. } => *tenant_id,
        }
    }

    const fn subject(&self) -> SubjectDigest {
        match self {
            Self::History { subject_sha256, .. } | Self::SemanticDiff { subject_sha256, .. } => {
                *subject_sha256
            }
        }
    }
}

#[derive(Clone)]
pub struct CursorCodec {
    key: Zeroizing<Vec<u8>>,
    ttl_seconds: u64,
}

impl CursorCodec {
    /// Creates a bounded HMAC cursor codec.
    ///
    /// # Errors
    ///
    /// Rejects weak/oversized keys and zero or excessive lifetimes.
    pub fn new(key: impl Into<Vec<u8>>, ttl_seconds: u64) -> Result<Self, HistoryError> {
        let key = key.into();
        if !(MIN_KEY_BYTES..=MAX_KEY_BYTES).contains(&key.len())
            || !(1..=MAX_TTL_SECONDS).contains(&ttl_seconds)
        {
            return Err(HistoryError::InvalidRequest);
        }
        Ok(Self {
            key: Zeroizing::new(key),
            ttl_seconds,
        })
    }

    pub(crate) fn expiration(&self, now: u64) -> Result<u64, HistoryError> {
        now.checked_add(self.ttl_seconds)
            .ok_or(HistoryError::InvalidRequest)
    }

    pub(crate) fn encode(&self, claims: &CursorClaims) -> Result<String, HistoryError> {
        let body = serde_json::to_vec(claims).map_err(|_| HistoryError::Serialization)?;
        let encoded_body = URL_SAFE_NO_PAD.encode(body);
        let signing_input = format!("{CURSOR_VERSION}.{encoded_body}");
        let mut signer = <HmacSha256 as hmac::KeyInit>::new_from_slice(&self.key)
            .map_err(|_| HistoryError::CryptoFailure)?;
        signer.update(signing_input.as_bytes());
        let signature = URL_SAFE_NO_PAD.encode(signer.finalize().into_bytes());
        let token = format!("{signing_input}.{signature}");
        if token.len() > MAX_CURSOR_BYTES {
            return Err(HistoryError::InvalidCursor);
        }
        Ok(token)
    }

    pub(crate) fn decode(
        &self,
        context: &HistoryRequestContext,
        token: &str,
    ) -> Result<CursorClaims, HistoryError> {
        if token.is_empty() || token.len() > MAX_CURSOR_BYTES {
            return Err(HistoryError::InvalidCursor);
        }
        let mut parts = token.split('.');
        let version = parts.next().ok_or(HistoryError::InvalidCursor)?;
        let encoded_body = parts.next().ok_or(HistoryError::InvalidCursor)?;
        let encoded_signature = parts.next().ok_or(HistoryError::InvalidCursor)?;
        if version != CURSOR_VERSION || parts.next().is_some() {
            return Err(HistoryError::InvalidCursor);
        }
        let signature = URL_SAFE_NO_PAD
            .decode(encoded_signature)
            .map_err(|_| HistoryError::InvalidCursor)?;
        let signing_input = format!("{version}.{encoded_body}");
        let mut verifier = <HmacSha256 as hmac::KeyInit>::new_from_slice(&self.key)
            .map_err(|_| HistoryError::CryptoFailure)?;
        verifier.update(signing_input.as_bytes());
        verifier
            .verify_slice(&signature)
            .map_err(|_| HistoryError::InvalidCursor)?;
        let body = URL_SAFE_NO_PAD
            .decode(encoded_body)
            .map_err(|_| HistoryError::InvalidCursor)?;
        let claims: CursorClaims =
            serde_json::from_slice(&body).map_err(|_| HistoryError::InvalidCursor)?;
        if claims.tenant_id() != context.tenant_id() || claims.subject() != context.subject() {
            return Err(HistoryError::InvalidCursor);
        }
        if context.now_unix_seconds() >= claims.expires_at_unix_seconds() {
            return Err(HistoryError::CursorExpired);
        }
        if let CursorClaims::History {
            next_index,
            page_size,
            snapshot_head,
            ..
        } = &claims
            && (*next_index == 0
                || !(1..=MAX_HISTORY_PAGE_SIZE).contains(page_size)
                || snapshot_head.revision_id().is_none())
        {
            return Err(HistoryError::InvalidCursor);
        }
        Ok(claims)
    }
}

impl fmt::Debug for CursorCodec {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CursorCodec")
            .field("key", &"<redacted>")
            .field("ttl_seconds", &self.ttl_seconds)
            .finish()
    }
}
