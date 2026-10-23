//! Private input adapter; existing file identity/link/containment checks remain the file boundary.
use super::*;
use std::borrow::Cow;

pub(super) enum TransactionSource<'a> {
    File(&'a Path),
    Bytes(&'a [u8]),
}

#[derive(Clone, Eq, PartialEq)]
pub(super) enum Observation {
    File(SourceObservation),
    Bytes { sha256: [u8; 32], size: u64 },
}

impl<'a> TransactionSource<'a> {
    pub(super) fn read_verified(&self, transaction: &WorkspaceTransaction) -> Result<Cow<'a, [u8]>, TransactionError> {
        match *self {
            Self::File(path) => transaction.read_verified_source(path).map(Cow::Owned),
            Self::Bytes(bytes) => {
                let size = u64::try_from(bytes.len()).map_err(|_| TransactionError::LimitExceeded)?;
                if size != transaction.manifest.expected_source_size()
                    || size > transaction.limits.max_source_bytes
                    || <[u8; 32]>::from(Sha256::digest(bytes)) != transaction.manifest.expected_source_sha256()
                {
                    return Err(TransactionError::SourceIdentityMismatch);
                }
                Ok(Cow::Borrowed(bytes))
            }
        }
    }

    pub(super) fn matches(&self, transaction: &WorkspaceTransaction) -> bool {
        match *self {
            Self::File(path) => transaction.source_matches(path),
            Self::Bytes(_) => self.read_verified(transaction).is_ok(),
        }
    }

    pub(super) fn observe(&self, transaction: &WorkspaceTransaction) -> Option<Observation> {
        match *self {
            Self::File(path) => transaction.observe_source(path).map(Observation::File),
            Self::Bytes(bytes) => {
                let size = u64::try_from(bytes.len()).ok()?;
                (size <= transaction.limits.max_source_bytes).then(|| Observation::Bytes {
                    sha256: Sha256::digest(bytes).into(), size,
                })
            }
        }
    }
}
