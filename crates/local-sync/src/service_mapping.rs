use std::fmt;

use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use uuid::Uuid;

use crate::{
    CheckpointRequest, REMOTE_SYNC_REQUEST_SCHEMA_VERSION, RemoteHead, SyncError,
    strict_json::parse_unique_value, valid_checkpoint_label, valid_checkpoint_note,
    valid_idempotency_key, valid_prefixed_identifier,
};

const CHECKPOINT_IDEMPOTENCY_NAMESPACE: Uuid =
    Uuid::from_u128(0x41af_5ff2_7349_5aa1_a197_a417_38e8_1006);
const MAX_PRIVATE_REQUEST_BYTES: usize = 16_384;

/// Host-owned correlation fields required by the P15 `project_checkpoint` input contract.
#[derive(Clone, Eq, PartialEq)]
pub struct CheckpointServiceContext {
    request_id: String,
    locale: String,
}

impl CheckpointServiceContext {
    /// Creates the fixed local-Codex service context for one private checkpoint exchange.
    ///
    /// # Errors
    ///
    /// Rejects a request identifier or locale outside the exact P15 public schema bounds.
    pub fn new(request_id: String, locale: String) -> Result<Self, SyncError> {
        if !valid_request_id(&request_id) || !valid_locale(&locale) {
            return Err(SyncError::InvalidRequest);
        }
        Ok(Self { request_id, locale })
    }

    #[must_use]
    pub fn request_id(&self) -> &str {
        &self.request_id
    }

    #[must_use]
    pub fn locale(&self) -> &str {
        &self.locale
    }
}

impl fmt::Debug for CheckpointServiceContext {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CheckpointServiceContext")
            .field("request_id", &"<redacted>")
            .field("locale", &self.locale)
            .finish()
    }
}

/// Exact P15 `project_checkpoint` input produced from one private P17 request.
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct CheckpointServiceArguments {
    client_surface: &'static str,
    locale: String,
    request_id: String,
    project_id: String,
    expected_revision: String,
    idempotency_key: String,
    revision_id: String,
    label: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    note: Option<String>,
}

impl CheckpointServiceArguments {
    #[must_use]
    pub const fn client_surface(&self) -> &'static str {
        self.client_surface
    }

    #[must_use]
    pub fn locale(&self) -> &str {
        &self.locale
    }

    #[must_use]
    pub fn request_id(&self) -> &str {
        &self.request_id
    }

    #[must_use]
    pub fn project_id(&self) -> &str {
        &self.project_id
    }

    #[must_use]
    pub fn expected_revision(&self) -> &str {
        &self.expected_revision
    }

    #[must_use]
    pub fn idempotency_key(&self) -> &str {
        &self.idempotency_key
    }

    #[must_use]
    pub fn revision_id(&self) -> &str {
        &self.revision_id
    }

    #[must_use]
    pub fn label(&self) -> &str {
        &self.label
    }

    #[must_use]
    pub fn note(&self) -> Option<&str> {
        self.note.as_deref()
    }

    /// Encodes the exact JSON object passed to the P15 service boundary.
    ///
    /// # Errors
    ///
    /// Returns invalid request if an otherwise valid bounded argument cannot be encoded.
    pub fn encoded(&self) -> Result<Vec<u8>, SyncError> {
        let value = serde_json::to_value(self).map_err(|_| SyncError::InvalidRequest)?;
        serde_json::to_vec(&value).map_err(|_| SyncError::InvalidRequest)
    }
}

impl fmt::Debug for CheckpointServiceArguments {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CheckpointServiceArguments")
            .field("client_surface", &self.client_surface)
            .field("locale", &self.locale)
            .field("request_id", &"<redacted>")
            .field("project_id", &"<redacted>")
            .field("expected_revision", &"<redacted>")
            .field("idempotency_key", &"<redacted>")
            .field("revision_id", &"<redacted>")
            .field("label", &"<redacted>")
            .field("has_note", &self.note.is_some())
            .finish()
    }
}

/// Private mirror binding retained beside the model-visible P15 service arguments.
#[derive(Clone, Eq, PartialEq)]
pub struct CheckpointServiceBinding {
    arguments: CheckpointServiceArguments,
    branch_id: String,
    mirror_id: String,
    expected_generation: u64,
    private_request_sha256: String,
    service_intent_sha256: String,
    service_arguments_sha256: String,
}

impl CheckpointServiceBinding {
    #[must_use]
    pub const fn arguments(&self) -> &CheckpointServiceArguments {
        &self.arguments
    }

    #[must_use]
    pub fn branch_id(&self) -> &str {
        &self.branch_id
    }

    #[must_use]
    pub fn mirror_id(&self) -> &str {
        &self.mirror_id
    }

    #[must_use]
    pub const fn expected_generation(&self) -> u64 {
        self.expected_generation
    }

    #[must_use]
    pub fn private_request_sha256(&self) -> &str {
        &self.private_request_sha256
    }

    #[must_use]
    pub fn service_intent_sha256(&self) -> &str {
        &self.service_intent_sha256
    }

    #[must_use]
    pub fn service_arguments_sha256(&self) -> &str {
        &self.service_arguments_sha256
    }
}

impl fmt::Debug for CheckpointServiceBinding {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CheckpointServiceBinding")
            .field("arguments", &self.arguments)
            .field("branch_id", &"<redacted>")
            .field("mirror_id", &"<redacted>")
            .field("expected_generation", &self.expected_generation)
            .field("private_request_sha256", &"<redacted>")
            .field("service_intent_sha256", &"<redacted>")
            .field("service_arguments_sha256", &"<redacted>")
            .finish()
    }
}

/// Maps one exact private P17 checkpoint request to the exact P15 public service input.
///
/// The returned binding deliberately keeps branch, mirror, generation and the private request
/// digest outside the P15 argument object. A host must verify those private fields against its
/// authenticated mirror registry before dispatching the service arguments.
///
/// # Errors
///
/// Rejects a checkpoint without an exact revision or any serialization failure.
pub fn map_checkpoint_to_service(
    request: &CheckpointRequest,
    context: &CheckpointServiceContext,
) -> Result<CheckpointServiceBinding, SyncError> {
    let revision_id = request
        .expected_head()
        .revision_id()
        .ok_or(SyncError::InvalidRequest)?;
    let idempotency_name = serde_json::to_value(CheckpointIdempotencyName {
        project_id: request.project_id(),
        branch_id: request.branch_id(),
        mirror_id: request.mirror_id(),
        idempotency_key: request.idempotency_key(),
    })
    .map_err(|_| SyncError::InvalidRequest)?;
    let idempotency_name =
        serde_json::to_vec(&idempotency_name).map_err(|_| SyncError::InvalidRequest)?;
    let service_idempotency_key =
        Uuid::new_v5(&CHECKPOINT_IDEMPOTENCY_NAMESPACE, &idempotency_name)
            .hyphenated()
            .to_string();
    let arguments = CheckpointServiceArguments {
        client_surface: "codex_local",
        locale: context.locale.clone(),
        request_id: context.request_id.clone(),
        project_id: request.project_id().to_owned(),
        expected_revision: revision_id.to_owned(),
        idempotency_key: service_idempotency_key,
        revision_id: revision_id.to_owned(),
        label: request.label().to_owned(),
        note: request.note().map(str::to_owned),
    };
    let service_intent = serde_json::to_value(CheckpointServiceIntent {
        project_id: &arguments.project_id,
        expected_revision: &arguments.expected_revision,
        idempotency_key: &arguments.idempotency_key,
        revision_id: &arguments.revision_id,
        label: &arguments.label,
        note: arguments.note.as_deref(),
    })
    .map_err(|_| SyncError::InvalidRequest)?;
    let service_intent_bytes =
        serde_json::to_vec(&service_intent).map_err(|_| SyncError::InvalidRequest)?;
    let service_arguments_sha256 = hex::encode(Sha256::digest(arguments.encoded()?));
    Ok(CheckpointServiceBinding {
        arguments,
        branch_id: request.branch_id().to_owned(),
        mirror_id: request.mirror_id().to_owned(),
        expected_generation: request.expected_head().generation(),
        private_request_sha256: request.wire_sha256()?,
        service_intent_sha256: hex::encode(Sha256::digest(service_intent_bytes)),
        service_arguments_sha256,
    })
}

/// Decodes the exact canonical P17 private checkpoint bytes and maps them to P15 service input.
///
/// # Errors
///
/// Rejects empty/oversized JSON, duplicate or unknown fields, non-v3 requests, non-checkpoint
/// operations, invalid values and any alternate byte encoding of an otherwise equivalent request.
pub fn decode_checkpoint_to_service(
    request_bytes: &[u8],
    context: &CheckpointServiceContext,
) -> Result<CheckpointServiceBinding, SyncError> {
    if request_bytes.is_empty() || request_bytes.len() > MAX_PRIVATE_REQUEST_BYTES {
        return Err(SyncError::InvalidRequest);
    }
    let value = parse_unique_value(request_bytes).map_err(|()| SyncError::InvalidRequest)?;
    let wire: IncomingCheckpointWireRequest =
        serde_json::from_value(value).map_err(|_| SyncError::InvalidRequest)?;
    if wire.schema_version != REMOTE_SYNC_REQUEST_SCHEMA_VERSION
        || wire.operation != "checkpoint"
        || !valid_prefixed_identifier(&wire.project_id, "prj_")
        || !valid_prefixed_identifier(&wire.branch_id, "brn_")
        || !valid_prefixed_identifier(&wire.mirror_id, "mir_")
        || !valid_idempotency_key(&wire.idempotency_key)
        || !valid_checkpoint_label(&wire.label)
        || !valid_checkpoint_note(wire.note.as_deref())
    {
        return Err(SyncError::InvalidRequest);
    }
    let request = CheckpointRequest {
        project_id: wire.project_id,
        branch_id: wire.branch_id,
        mirror_id: wire.mirror_id,
        expected_head: RemoteHead::new(
            wire.expected_head.revision_id,
            wire.expected_head.generation,
        )?,
        idempotency_key: wire.idempotency_key,
        label: wire.label,
        note: wire.note,
    };
    if request.expected_head().revision_id().is_none()
        || request.encoded_wire_request()? != request_bytes
    {
        return Err(SyncError::InvalidRequest);
    }
    map_checkpoint_to_service(&request, context)
}

#[derive(Serialize)]
struct CheckpointIdempotencyName<'a> {
    project_id: &'a str,
    branch_id: &'a str,
    mirror_id: &'a str,
    idempotency_key: &'a str,
}

#[derive(Serialize)]
struct CheckpointServiceIntent<'a> {
    project_id: &'a str,
    expected_revision: &'a str,
    idempotency_key: &'a str,
    revision_id: &'a str,
    label: &'a str,
    #[serde(skip_serializing_if = "Option::is_none")]
    note: Option<&'a str>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct IncomingCheckpointWireRequest {
    schema_version: String,
    operation: String,
    project_id: String,
    branch_id: String,
    mirror_id: String,
    expected_head: IncomingCheckpointWireHead,
    idempotency_key: String,
    label: String,
    note: Option<String>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct IncomingCheckpointWireHead {
    revision_id: Option<String>,
    generation: u64,
}

fn valid_request_id(value: &str) -> bool {
    (12..=124).contains(&value.len())
        && value.starts_with("req_")
        && value[4..]
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_'))
}

fn valid_locale(value: &str) -> bool {
    let parts = value.split('-').collect::<Vec<_>>();
    if !(1..=3).contains(&parts.len())
        || !(2..=3).contains(&parts[0].len())
        || !parts[0].bytes().all(|byte| byte.is_ascii_lowercase())
    {
        return false;
    }
    let mut index = 1;
    if parts.get(index).is_some_and(|part| {
        let bytes = part.as_bytes();
        bytes.len() == 4
            && bytes[0].is_ascii_uppercase()
            && bytes[1..].iter().all(u8::is_ascii_lowercase)
    }) {
        index += 1;
    }
    if let Some(region) = parts.get(index) {
        let bytes = region.as_bytes();
        if !((bytes.len() == 2 && bytes.iter().all(u8::is_ascii_uppercase))
            || (bytes.len() == 3 && bytes.iter().all(u8::is_ascii_digit)))
        {
            return false;
        }
        index += 1;
    }
    index == parts.len()
}
