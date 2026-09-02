use std::fmt;

use serde::{Deserialize, Serialize};
use thiserror::Error;

pub const MAX_TYPED_ID_BYTES: usize = 512;

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum IdentityError {
    #[error("typed identity is invalid")]
    InvalidIdentifier,
    #[error("typed identity exceeds its byte limit")]
    IdentifierTooLong,
}

impl IdentityError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidIdentifier => "identity_invalid_identifier",
            Self::IdentifierTooLong => "identity_identifier_too_long",
        }
    }
}

fn validate(value: String) -> Result<String, IdentityError> {
    if value.is_empty() || value.chars().any(char::is_control) {
        return Err(IdentityError::InvalidIdentifier);
    }
    if value.len() > MAX_TYPED_ID_BYTES {
        return Err(IdentityError::IdentifierTooLong);
    }
    Ok(value)
}

macro_rules! typed_id {
    ($name:ident) => {
        #[derive(Clone, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize)]
        #[serde(transparent)]
        pub struct $name(String);

        impl $name {
            /// Creates a bounded typed identifier.
            ///
            /// # Errors
            ///
            /// Rejects empty, control-character or oversized values.
            pub fn parse(value: impl Into<String>) -> Result<Self, IdentityError> {
                validate(value.into()).map(Self)
            }

            #[must_use]
            pub fn as_str(&self) -> &str {
                &self.0
            }
        }

        impl<'de> Deserialize<'de> for $name {
            fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
            where
                D: serde::Deserializer<'de>,
            {
                let value = String::deserialize(deserializer)?;
                validate(value).map(Self).map_err(serde::de::Error::custom)
            }
        }

        impl fmt::Debug for $name {
            fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
                formatter.write_str(concat!(stringify!($name), "(<redacted>)"))
            }
        }
    };
}

typed_id!(ProjectId);
typed_id!(RevisionId);
typed_id!(ArtifactId);
typed_id!(LogicalNodeId);
typed_id!(StyleId);
typed_id!(ResourceId);
typed_id!(BookmarkId);
typed_id!(FieldId);
typed_id!(ChangeId);
typed_id!(BackendOpaqueId);
typed_id!(PlanId);
typed_id!(OperationId);
typed_id!(CapabilityId);
