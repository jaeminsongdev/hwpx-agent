use std::collections::BTreeMap;
use std::fmt;
use std::sync::{Arc, Mutex, MutexGuard};

use artifact_service::{
    ArtifactDescriptor, ArtifactError, ArtifactId, ArtifactMetadataRepository, ArtifactScanner,
    ArtifactService, AuthScope as ArtifactAuthScope, ContentDigest, EncryptedBlobStore,
    RequestContext, StorageState, SubjectDigest, TenantId, ValidationState,
};
use base64::Engine as _;
use base64::engine::general_purpose::URL_SAFE_NO_PAD;
use hmac::{Hmac, Mac as _};
use serde_json::{Map, Value, json};
use sha2::Sha256;
use thiserror::Error;
use zeroize::Zeroizing;

use crate::ToolKind;
use crate::handler::{AuthorizedToolCall, GatewayError, ToolServiceGateway, ToolServiceOutput};

const DELIVERY_SCHEMA_VERSION: &str = "hwpx-agent.p15-artifact-delivery/v1";
const DELIVERY_META_KEY: &str = "hwpx/artifactDelivery";
const MIN_TTL_SECONDS: u64 = 30;
const PRODUCT_MAX_TTL_SECONDS: u64 = 900;
const PRODUCT_MAX_RANGE_BYTES: u64 = 67_108_864;
const PRODUCT_MAX_BINDINGS: usize = 65_536;
const MAX_SIGNING_KEY_BYTES: usize = 128;
const MIN_SIGNING_KEY_BYTES: usize = 32;
const MAX_URL_BYTES: usize = 2_048;
const MAX_PROJECT_ID_BYTES: usize = 124;
const MAX_KEY_ID_BYTES: usize = 128;
const CLOCK_SKEW_SECONDS: u64 = 30;
const LAST_SCHEMA_UNIX_SECOND: u64 = 253_402_300_799;
const OPERATION: &str = "download";

type HmacSha256 = Hmac<Sha256>;
type BindingKey = (TenantId, String, ArtifactId);
type BindingMap = BTreeMap<BindingKey, BindingState>;

#[derive(Clone, Debug, Error, Eq, PartialEq)]
pub enum ArtifactDeliveryError {
    #[error("artifact delivery configuration is invalid")]
    InvalidConfiguration,
    #[error("artifact delivery request is invalid")]
    InvalidRequest,
    #[error("requested artifact was not found")]
    NotFound,
    #[error("artifact access is denied")]
    AccessDenied,
    #[error("artifact is not available for delivery")]
    NotDeliverable,
    #[error("artifact delivery source is unavailable")]
    SourceUnavailable,
    #[error("artifact delivery integrity verification failed")]
    IntegrityMismatch,
    #[error("artifact delivery token is invalid")]
    InvalidToken,
    #[error("artifact delivery token is expired")]
    ExpiredToken,
    #[error("byte range is invalid")]
    InvalidRange,
    #[error("byte range cannot be satisfied for {total_bytes} bytes")]
    RangeNotSatisfiable { total_bytes: u64 },
    #[error("byte range exceeds the configured response limit")]
    RangeTooLarge,
    #[error("artifact delivery registry reached its bounded capacity")]
    CapacityExceeded,
}

impl From<ArtifactDeliveryError> for GatewayError {
    fn from(error: ArtifactDeliveryError) -> Self {
        match error {
            ArtifactDeliveryError::NotFound
            | ArtifactDeliveryError::AccessDenied
            | ArtifactDeliveryError::NotDeliverable => Self::NotFound,
            ArtifactDeliveryError::CapacityExceeded | ArtifactDeliveryError::SourceUnavailable => {
                Self::Unavailable
            }
            ArtifactDeliveryError::InvalidConfiguration
            | ArtifactDeliveryError::InvalidRequest
            | ArtifactDeliveryError::IntegrityMismatch
            | ArtifactDeliveryError::InvalidToken
            | ArtifactDeliveryError::ExpiredToken
            | ArtifactDeliveryError::InvalidRange
            | ArtifactDeliveryError::RangeNotSatisfiable { .. }
            | ArtifactDeliveryError::RangeTooLarge => Self::Rejected,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ArtifactDeliveryConfig {
    default_ttl_seconds: u64,
    max_ttl_seconds: u64,
    max_range_bytes: u64,
}

impl ArtifactDeliveryConfig {
    /// Creates bounded public delivery limits.
    ///
    /// # Errors
    ///
    /// Rejects TTLs outside the frozen public schema or response ranges above the product bound.
    pub fn new(
        default_ttl_seconds: u64,
        max_ttl_seconds: u64,
        max_range_bytes: u64,
    ) -> Result<Self, ArtifactDeliveryError> {
        if !(MIN_TTL_SECONDS..=PRODUCT_MAX_TTL_SECONDS).contains(&default_ttl_seconds)
            || !(default_ttl_seconds..=PRODUCT_MAX_TTL_SECONDS).contains(&max_ttl_seconds)
            || !(1..=PRODUCT_MAX_RANGE_BYTES).contains(&max_range_bytes)
        {
            return Err(ArtifactDeliveryError::InvalidConfiguration);
        }
        Ok(Self {
            default_ttl_seconds,
            max_ttl_seconds,
            max_range_bytes,
        })
    }

    #[must_use]
    pub const fn default_ttl_seconds(self) -> u64 {
        self.default_ttl_seconds
    }

    #[must_use]
    pub const fn max_ttl_seconds(self) -> u64 {
        self.max_ttl_seconds
    }

    #[must_use]
    pub const fn max_range_bytes(self) -> u64 {
        self.max_range_bytes
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct SignedArtifactUrl(Zeroizing<String>);

impl SignedArtifactUrl {
    /// Accepts an opaque HTTPS token for verification without logging it.
    ///
    /// # Errors
    ///
    /// Rejects empty, oversized, non-HTTPS or control-containing input.
    pub fn parse(value: impl Into<String>) -> Result<Self, ArtifactDeliveryError> {
        let value = Zeroizing::new(value.into());
        if value.is_empty()
            || value.len() > MAX_URL_BYTES
            || !value.starts_with("https://")
            || value.chars().any(char::is_control)
        {
            return Err(ArtifactDeliveryError::InvalidToken);
        }
        Ok(Self(value))
    }

    #[must_use]
    pub fn expose(&self) -> &str {
        &self.0
    }
}

impl fmt::Debug for SignedArtifactUrl {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("SignedArtifactUrl([REDACTED])")
    }
}

#[derive(Clone)]
pub struct ArtifactDeliverySigner {
    base_url: String,
    key_id: String,
    prototype: HmacSha256,
    max_ttl_seconds: u64,
}

impl fmt::Debug for ArtifactDeliverySigner {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ArtifactDeliverySigner")
            .field("base_url", &self.base_url)
            .field("key_id", &self.key_id)
            .field("signing_key", &"[REDACTED]")
            .field("max_ttl_seconds", &self.max_ttl_seconds)
            .finish_non_exhaustive()
    }
}

impl ArtifactDeliverySigner {
    /// Creates an HTTPS-only HMAC reference signer.
    ///
    /// # Errors
    ///
    /// Rejects weak keys, unsafe URLs, malformed key IDs and lifetimes above 900 seconds.
    pub fn new(
        base_url: impl Into<String>,
        key_id: impl Into<String>,
        signing_key: &[u8],
        max_ttl_seconds: u64,
    ) -> Result<Self, ArtifactDeliveryError> {
        let base_url = base_url.into();
        let key_id = key_id.into();
        if !valid_https_base_url(&base_url)
            || !valid_key_id(&key_id)
            || !(MIN_SIGNING_KEY_BYTES..=MAX_SIGNING_KEY_BYTES).contains(&signing_key.len())
            || !(MIN_TTL_SECONDS..=PRODUCT_MAX_TTL_SECONDS).contains(&max_ttl_seconds)
        {
            return Err(ArtifactDeliveryError::InvalidConfiguration);
        }
        let prototype = <HmacSha256 as hmac::KeyInit>::new_from_slice(signing_key)
            .map_err(|_| ArtifactDeliveryError::InvalidConfiguration)?;
        Ok(Self {
            base_url,
            key_id,
            prototype,
            max_ttl_seconds,
        })
    }

    fn issue(&self, claims: &DeliveryClaims) -> Result<SignedArtifactUrl, ArtifactDeliveryError> {
        let lifetime = claims
            .expires_at_unix_seconds
            .checked_sub(claims.issued_at_unix_seconds)
            .ok_or(ArtifactDeliveryError::InvalidRequest)?;
        if !(MIN_TTL_SECONDS..=self.max_ttl_seconds).contains(&lifetime)
            || claims.expires_at_unix_seconds > LAST_SCHEMA_UNIX_SECOND
        {
            return Err(ArtifactDeliveryError::InvalidRequest);
        }
        let canonical = canonical_query(&self.key_id, claims);
        let signature = self.sign(canonical.as_bytes());
        SignedArtifactUrl::parse(format!(
            "{}?{}&sig={}",
            self.base_url,
            canonical,
            URL_SAFE_NO_PAD.encode(signature)
        ))
    }

    fn verify(
        &self,
        signed_url: &SignedArtifactUrl,
        now_unix_seconds: u64,
    ) -> Result<DeliveryClaims, ArtifactDeliveryError> {
        let prefix = format!("{}?", self.base_url);
        let query = signed_url
            .expose()
            .strip_prefix(&prefix)
            .ok_or(ArtifactDeliveryError::InvalidToken)?;
        let (canonical, signature_text) = query
            .rsplit_once("&sig=")
            .ok_or(ArtifactDeliveryError::InvalidToken)?;
        if signature_text.contains('&') {
            return Err(ArtifactDeliveryError::InvalidToken);
        }
        let expected_names = [
            "v", "kid", "tenant", "project", "artifact", "subject", "content", "request",
            "binding", "iat", "exp", "op",
        ];
        let pairs = canonical.split('&').collect::<Vec<_>>();
        if pairs.len() != expected_names.len() {
            return Err(ArtifactDeliveryError::InvalidToken);
        }
        let mut values = Vec::with_capacity(expected_names.len());
        for (pair, expected) in pairs.iter().zip(expected_names) {
            values.push(parse_pair(pair, expected)?);
        }
        if values[0] != "1" || values[1] != self.key_id || values[11] != OPERATION {
            return Err(ArtifactDeliveryError::InvalidToken);
        }
        let signature = URL_SAFE_NO_PAD
            .decode(signature_text)
            .map_err(|_| ArtifactDeliveryError::InvalidToken)?;
        if signature.len() != 32 {
            return Err(ArtifactDeliveryError::InvalidToken);
        }
        let mut verifier = self.prototype.clone();
        verifier.update(canonical.as_bytes());
        verifier
            .verify_slice(&signature)
            .map_err(|_| ArtifactDeliveryError::InvalidToken)?;

        let tenant_uuid =
            uuid::Uuid::parse_str(values[2]).map_err(|_| ArtifactDeliveryError::InvalidToken)?;
        if tenant_uuid.simple().to_string() != values[2] {
            return Err(ArtifactDeliveryError::InvalidToken);
        }
        let tenant_id =
            TenantId::new(tenant_uuid).map_err(|_| ArtifactDeliveryError::InvalidToken)?;
        let project_id = values[3].to_owned();
        if !valid_prefixed_id(&project_id, "prj_") {
            return Err(ArtifactDeliveryError::InvalidToken);
        }
        let artifact_id =
            ArtifactId::parse(values[4]).map_err(|_| ArtifactDeliveryError::InvalidToken)?;
        let subject_sha256 =
            SubjectDigest::parse(values[5]).map_err(|_| ArtifactDeliveryError::InvalidToken)?;
        let content_sha256 =
            ContentDigest::parse(values[6]).map_err(|_| ArtifactDeliveryError::InvalidToken)?;
        let request_sha256 =
            ContentDigest::parse(values[7]).map_err(|_| ArtifactDeliveryError::InvalidToken)?;
        let binding_generation = parse_token_u64(values[8])?;
        if binding_generation == 0 {
            return Err(ArtifactDeliveryError::InvalidToken);
        }
        let issued_at_unix_seconds = parse_token_u64(values[9])?;
        let expires_at_unix_seconds = parse_token_u64(values[10])?;
        let lifetime = expires_at_unix_seconds
            .checked_sub(issued_at_unix_seconds)
            .ok_or(ArtifactDeliveryError::InvalidToken)?;
        if !(MIN_TTL_SECONDS..=self.max_ttl_seconds).contains(&lifetime)
            || issued_at_unix_seconds > now_unix_seconds.saturating_add(CLOCK_SKEW_SECONDS)
        {
            return Err(ArtifactDeliveryError::InvalidToken);
        }
        if now_unix_seconds > expires_at_unix_seconds {
            return Err(ArtifactDeliveryError::ExpiredToken);
        }
        Ok(DeliveryClaims {
            tenant_id,
            project_id,
            artifact_id,
            subject_sha256,
            content_sha256,
            request_sha256,
            binding_generation,
            issued_at_unix_seconds,
            expires_at_unix_seconds,
        })
    }

    fn sign(&self, value: &[u8]) -> [u8; 32] {
        let mut signer = self.prototype.clone();
        signer.update(value);
        signer.finalize().into_bytes().into()
    }
}

#[derive(Clone, Debug)]
struct DeliveryClaims {
    tenant_id: TenantId,
    project_id: String,
    artifact_id: ArtifactId,
    subject_sha256: SubjectDigest,
    content_sha256: ContentDigest,
    request_sha256: ContentDigest,
    binding_generation: u64,
    issued_at_unix_seconds: u64,
    expires_at_unix_seconds: u64,
}

#[derive(Clone, Debug)]
pub struct ArtifactProjectRegistry {
    bindings: Arc<Mutex<BindingMap>>,
    max_bindings: usize,
}

impl ArtifactProjectRegistry {
    /// Creates a finite project-to-artifact binding registry.
    ///
    /// # Errors
    ///
    /// Rejects zero or above-product capacity.
    pub fn new(max_bindings: usize) -> Result<Self, ArtifactDeliveryError> {
        if !(1..=PRODUCT_MAX_BINDINGS).contains(&max_bindings) {
            return Err(ArtifactDeliveryError::InvalidConfiguration);
        }
        Ok(Self {
            bindings: Arc::new(Mutex::new(BTreeMap::new())),
            max_bindings,
        })
    }

    /// Registers or reactivates a generation-fenced tenant/project/artifact membership.
    ///
    /// # Errors
    ///
    /// Rejects malformed projects or a full registry. Exact replay is harmless.
    pub fn register(
        &self,
        tenant_id: TenantId,
        project_id: impl Into<String>,
        artifact_id: ArtifactId,
    ) -> Result<(), ArtifactDeliveryError> {
        let project_id = project_id.into();
        if !valid_prefixed_id(&project_id, "prj_") {
            return Err(ArtifactDeliveryError::InvalidConfiguration);
        }
        let mut bindings = lock(&self.bindings)?;
        let key = (tenant_id, project_id, artifact_id);
        if let Some(state) = bindings.get_mut(&key) {
            if !state.active {
                state.generation = state
                    .generation
                    .checked_add(1)
                    .ok_or(ArtifactDeliveryError::CapacityExceeded)?;
                state.active = true;
            }
            return Ok(());
        }
        if bindings.len() >= self.max_bindings {
            return Err(ArtifactDeliveryError::CapacityExceeded);
        }
        bindings.insert(
            key,
            BindingState {
                generation: 1,
                active: true,
            },
        );
        Ok(())
    }

    /// Revokes a project-to-artifact binding and invalidates previously issued URLs.
    ///
    /// # Errors
    ///
    /// Returns not-found for an absent/inactive binding and fails on generation overflow.
    pub fn revoke(
        &self,
        tenant_id: TenantId,
        project_id: impl Into<String>,
        artifact_id: ArtifactId,
    ) -> Result<(), ArtifactDeliveryError> {
        let project_id = project_id.into();
        if !valid_prefixed_id(&project_id, "prj_") {
            return Err(ArtifactDeliveryError::InvalidConfiguration);
        }
        let mut bindings = lock(&self.bindings)?;
        let state = bindings
            .get_mut(&(tenant_id, project_id, artifact_id))
            .filter(|state| state.active)
            .ok_or(ArtifactDeliveryError::NotFound)?;
        state.generation = state
            .generation
            .checked_add(1)
            .ok_or(ArtifactDeliveryError::CapacityExceeded)?;
        state.active = false;
        Ok(())
    }

    fn active_generation(
        &self,
        tenant_id: TenantId,
        project_id: &str,
        artifact_id: ArtifactId,
    ) -> Result<Option<u64>, ArtifactDeliveryError> {
        Ok(lock(&self.bindings)?
            .get(&(tenant_id, project_id.to_owned(), artifact_id))
            .filter(|state| state.active)
            .map(|state| state.generation))
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct BindingState {
    generation: u64,
    active: bool,
}

pub trait ArtifactDeliverySource: fmt::Debug + Send {
    /// Reads authorized metadata while preserving tenant and artifact ACL checks.
    ///
    /// # Errors
    ///
    /// Returns the source adapter's bounded artifact error.
    fn descriptor(
        &self,
        tenant_id: TenantId,
        subject: SubjectDigest,
        artifact_id: ArtifactId,
        now_unix_seconds: u64,
    ) -> Result<ArtifactDescriptor, ArtifactError>;

    /// Reads and integrity-verifies the full artifact at redemption time.
    ///
    /// # Errors
    ///
    /// Returns the source adapter's bounded artifact error.
    fn download(
        &self,
        tenant_id: TenantId,
        subject: SubjectDigest,
        artifact_id: ArtifactId,
        now_unix_seconds: u64,
    ) -> Result<Vec<u8>, ArtifactError>;
}

impl<R, B, S> ArtifactDeliverySource for ArtifactService<R, B, S>
where
    R: ArtifactMetadataRepository,
    B: EncryptedBlobStore,
    S: ArtifactScanner,
{
    fn descriptor(
        &self,
        tenant_id: TenantId,
        subject: SubjectDigest,
        artifact_id: ArtifactId,
        now_unix_seconds: u64,
    ) -> Result<ArtifactDescriptor, ArtifactError> {
        let context = RequestContext::new(tenant_id, subject, [ArtifactAuthScope::DocumentRead]);
        self.get_descriptor(&context, artifact_id, now_unix_seconds)
    }

    fn download(
        &self,
        tenant_id: TenantId,
        subject: SubjectDigest,
        artifact_id: ArtifactId,
        now_unix_seconds: u64,
    ) -> Result<Vec<u8>, ArtifactError> {
        let context = RequestContext::new(tenant_id, subject, [ArtifactAuthScope::DocumentRead]);
        self.download(&context, artifact_id, now_unix_seconds)
    }
}

#[derive(Clone)]
pub(crate) struct ArtifactToolDelivery {
    resource_link: Option<Value>,
    meta: Value,
}

impl fmt::Debug for ArtifactToolDelivery {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ArtifactToolDelivery")
            .field("has_resource_link", &self.resource_link.is_some())
            .field("meta", &"[REDACTED]")
            .finish()
    }
}

impl ArtifactToolDelivery {
    pub(crate) fn append_to_result(
        mut self,
        content: &mut Vec<Value>,
        meta: &mut Map<String, Value>,
    ) {
        if let Some(resource_link) = self.resource_link.take() {
            content.push(resource_link);
        }
        meta.insert(DELIVERY_META_KEY.to_owned(), std::mem::take(&mut self.meta));
    }
}

impl Drop for ArtifactToolDelivery {
    fn drop(&mut self) {
        if let Some(Value::String(signed_url)) = self.meta.get_mut("signedUrl") {
            zeroize::Zeroize::zeroize(signed_url);
        }
    }
}

#[derive(Debug)]
pub struct ArtifactDeliveryGateway<G, S> {
    delegate: G,
    source: S,
    bindings: ArtifactProjectRegistry,
    signer: ArtifactDeliverySigner,
    config: ArtifactDeliveryConfig,
}

impl<G, S> ArtifactDeliveryGateway<G, S> {
    /// Creates the P15 delivery boundary from explicit, finite dependencies.
    ///
    /// # Errors
    ///
    /// Rejects a signer/config TTL mismatch.
    pub fn new(
        delegate: G,
        source: S,
        bindings: ArtifactProjectRegistry,
        signer: ArtifactDeliverySigner,
        config: ArtifactDeliveryConfig,
    ) -> Result<Self, ArtifactDeliveryError> {
        if signer.max_ttl_seconds != config.max_ttl_seconds {
            return Err(ArtifactDeliveryError::InvalidConfiguration);
        }
        Ok(Self {
            delegate,
            source,
            bindings,
            signer,
            config,
        })
    }

    #[must_use]
    pub const fn source(&self) -> &S {
        &self.source
    }

    /// Redeems one signed delivery URL and applies an optional single HTTP byte range.
    ///
    /// # Errors
    ///
    /// Rechecks signature, expiry, subject, project binding, current artifact ACL and digest. It
    /// rejects multiple, malformed, unsatisfiable or oversized ranges.
    pub fn redeem_range(
        &self,
        tenant_id: TenantId,
        subject: SubjectDigest,
        signed_url: &SignedArtifactUrl,
        range_header: Option<&str>,
        now_unix_seconds: u64,
    ) -> Result<ArtifactRangeResponse, ArtifactDeliveryError>
    where
        S: ArtifactDeliverySource,
    {
        let claims = self.signer.verify(signed_url, now_unix_seconds)?;
        if claims.tenant_id != tenant_id || claims.subject_sha256 != subject {
            return Err(ArtifactDeliveryError::AccessDenied);
        }
        if self
            .bindings
            .active_generation(tenant_id, &claims.project_id, claims.artifact_id)?
            != Some(claims.binding_generation)
        {
            return Err(ArtifactDeliveryError::NotFound);
        }
        let payload = self
            .source
            .download(tenant_id, subject, claims.artifact_id, now_unix_seconds)
            .map_err(|error| map_source_error(&error))?;
        if ContentDigest::of(&payload) != claims.content_sha256 {
            return Err(ArtifactDeliveryError::IntegrityMismatch);
        }
        build_range_response(payload, range_header, self.config.max_range_bytes)
    }

    #[allow(clippy::too_many_lines)]
    fn deliver(&self, call: &AuthorizedToolCall) -> Result<ToolServiceOutput, ArtifactDeliveryError>
    where
        S: ArtifactDeliverySource,
    {
        let project_id = required_string(call.arguments(), "project_id")?;
        let artifact_text = required_string(call.arguments(), "artifact_id")?;
        let artifact_id =
            ArtifactId::parse(artifact_text).map_err(|_| ArtifactDeliveryError::NotFound)?;
        let binding_generation = self
            .bindings
            .active_generation(call.tenant_id(), project_id, artifact_id)?
            .ok_or(ArtifactDeliveryError::NotFound)?;
        let descriptor = self
            .source
            .descriptor(
                call.tenant_id(),
                call.subject(),
                artifact_id,
                call.now_unix_seconds(),
            )
            .map_err(|error| map_source_error(&error))?;
        if descriptor.artifact_id != artifact_id {
            return Err(ArtifactDeliveryError::IntegrityMismatch);
        }
        let disposition = required_string(call.arguments(), "disposition")?;
        let output_artifact = json!({
            "artifact_id": descriptor.artifact_id.public_id(),
            "media_type": descriptor.media_type.as_str(),
            "bytes": descriptor.size_bytes,
            "sha256": descriptor.sha256.hex(),
        });
        if disposition == "metadata" {
            if call.arguments().get("delivery_ttl_seconds").is_some() {
                return Err(ArtifactDeliveryError::InvalidRequest);
            }
            return Ok(ToolServiceOutput::new(json!({
                "schema_version": "hwpx-agent.tool-result/v1",
                "request_id": call.request_id(),
                "outcome": "succeeded",
                "safe_summary": "Authorized artifact metadata is available.",
                "warnings": [],
                "artifact": output_artifact,
                "delivery": "metadata",
                "expires_at": null,
            })));
        }
        if descriptor.storage_state != StorageState::Available
            || descriptor.validation_state != ValidationState::Verified
        {
            return Err(ArtifactDeliveryError::NotDeliverable);
        }
        let ttl = call
            .arguments()
            .get("delivery_ttl_seconds")
            .and_then(Value::as_u64)
            .unwrap_or(self.config.default_ttl_seconds);
        if !(MIN_TTL_SECONDS..=self.config.max_ttl_seconds).contains(&ttl) {
            return Err(ArtifactDeliveryError::InvalidRequest);
        }
        let expires_at = call
            .now_unix_seconds()
            .checked_add(ttl)
            .filter(|value| *value <= LAST_SCHEMA_UNIX_SECOND)
            .ok_or(ArtifactDeliveryError::InvalidRequest)?;
        let request_sha256 = semantic_request_digest(call.arguments(), ttl)?;
        let signed_url = self.signer.issue(&DeliveryClaims {
            tenant_id: call.tenant_id(),
            project_id: project_id.to_owned(),
            artifact_id,
            subject_sha256: call.subject(),
            content_sha256: descriptor.sha256,
            request_sha256,
            binding_generation,
            issued_at_unix_seconds: call.now_unix_seconds(),
            expires_at_unix_seconds: expires_at,
        })?;
        let expires_at_text = format_unix_timestamp(expires_at)?;
        let artifact_uri = format!("hwpx-artifact://download/{}", artifact_id.public_id());
        let meta = json!({
            "schemaVersion": DELIVERY_SCHEMA_VERSION,
            "mode": "signed_url",
            "signedUrl": signed_url.expose(),
            "expiresAt": expires_at_text,
            "artifactUri": artifact_uri,
            "acceptRanges": "bytes",
            "maxRangeBytes": self.config.max_range_bytes,
        });
        let (delivery, safe_summary, resource_link) = match disposition {
            "preview" => (
                "preview_in_meta",
                "A short-lived authorized artifact preview is available.",
                None,
            ),
            "attachment" => (
                "attachment_in_content",
                "A short-lived authorized artifact attachment is available.",
                Some(json!({
                    "type": "resource_link",
                    "uri": artifact_uri,
                    "name": descriptor.file_name.as_str(),
                    "title": "HWPX Agent artifact",
                    "description": "Authorized artifact; resolve with client-only delivery metadata.",
                    "mimeType": descriptor.media_type.as_str(),
                })),
            ),
            _ => return Err(ArtifactDeliveryError::InvalidRequest),
        };
        Ok(ToolServiceOutput::with_artifact_delivery(
            json!({
                "schema_version": "hwpx-agent.tool-result/v1",
                "request_id": call.request_id(),
                "outcome": "succeeded",
                "safe_summary": safe_summary,
                "warnings": [],
                "artifact": output_artifact,
                "delivery": delivery,
                "expires_at": expires_at_text,
            }),
            ArtifactToolDelivery {
                resource_link,
                meta,
            },
        ))
    }
}

impl<G, S> ToolServiceGateway for ArtifactDeliveryGateway<G, S>
where
    G: ToolServiceGateway,
    S: ArtifactDeliverySource,
{
    fn dispatch(&mut self, call: AuthorizedToolCall) -> Result<ToolServiceOutput, GatewayError> {
        if call.tool() == ToolKind::ArtifactGet {
            self.deliver(&call).map_err(GatewayError::from)
        } else {
            self.delegate.dispatch(call)
        }
    }
}

#[derive(Eq, PartialEq)]
pub struct ArtifactRangeResponse {
    status_code: u16,
    total_bytes: u64,
    start: u64,
    end_inclusive: Option<u64>,
    content_range: Option<String>,
    bytes: Zeroizing<Vec<u8>>,
}

impl ArtifactRangeResponse {
    #[must_use]
    pub const fn status_code(&self) -> u16 {
        self.status_code
    }

    #[must_use]
    pub const fn total_bytes(&self) -> u64 {
        self.total_bytes
    }

    #[must_use]
    pub const fn start(&self) -> u64 {
        self.start
    }

    #[must_use]
    pub const fn end_inclusive(&self) -> Option<u64> {
        self.end_inclusive
    }

    #[must_use]
    pub fn content_range(&self) -> Option<&str> {
        self.content_range.as_deref()
    }

    #[must_use]
    pub fn bytes(&self) -> &[u8] {
        &self.bytes
    }
}

impl fmt::Debug for ArtifactRangeResponse {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ArtifactRangeResponse")
            .field("status_code", &self.status_code)
            .field("total_bytes", &self.total_bytes)
            .field("start", &self.start)
            .field("end_inclusive", &self.end_inclusive)
            .field("content_range", &self.content_range)
            .field("bytes", &"[REDACTED]")
            .finish()
    }
}

fn build_range_response(
    payload: Vec<u8>,
    range_header: Option<&str>,
    max_range_bytes: u64,
) -> Result<ArtifactRangeResponse, ArtifactDeliveryError> {
    let total =
        u64::try_from(payload.len()).map_err(|_| ArtifactDeliveryError::SourceUnavailable)?;
    let Some(header) = range_header else {
        if total > max_range_bytes {
            return Err(ArtifactDeliveryError::RangeTooLarge);
        }
        return Ok(ArtifactRangeResponse {
            status_code: 200,
            total_bytes: total,
            start: 0,
            end_inclusive: total.checked_sub(1),
            content_range: None,
            bytes: Zeroizing::new(payload),
        });
    };
    if total == 0 {
        return Err(ArtifactDeliveryError::RangeNotSatisfiable { total_bytes: 0 });
    }
    let (start, end) = parse_single_range(header, total)?;
    let length = end
        .checked_sub(start)
        .and_then(|value| value.checked_add(1))
        .ok_or(ArtifactDeliveryError::InvalidRange)?;
    if length > max_range_bytes {
        return Err(ArtifactDeliveryError::RangeTooLarge);
    }
    let start_index = usize::try_from(start).map_err(|_| ArtifactDeliveryError::InvalidRange)?;
    let end_index = usize::try_from(end).map_err(|_| ArtifactDeliveryError::InvalidRange)?;
    let selected = payload
        .get(start_index..=end_index)
        .ok_or(ArtifactDeliveryError::IntegrityMismatch)?
        .to_vec();
    Ok(ArtifactRangeResponse {
        status_code: 206,
        total_bytes: total,
        start,
        end_inclusive: Some(end),
        content_range: Some(format!("bytes {start}-{end}/{total}")),
        bytes: Zeroizing::new(selected),
    })
}

fn parse_single_range(header: &str, total: u64) -> Result<(u64, u64), ArtifactDeliveryError> {
    if header.is_empty() || header.len() > 128 || header.contains([',', ' ', '\t', '\r', '\n']) {
        return Err(ArtifactDeliveryError::InvalidRange);
    }
    let value = header
        .strip_prefix("bytes=")
        .ok_or(ArtifactDeliveryError::InvalidRange)?;
    let (start_text, end_text) = value
        .split_once('-')
        .ok_or(ArtifactDeliveryError::InvalidRange)?;
    if start_text.is_empty() {
        let suffix = parse_range_u64(end_text)?;
        if suffix == 0 {
            return Err(ArtifactDeliveryError::InvalidRange);
        }
        let length = suffix.min(total);
        return Ok((total - length, total - 1));
    }
    let start = parse_range_u64(start_text)?;
    if start >= total {
        return Err(ArtifactDeliveryError::RangeNotSatisfiable { total_bytes: total });
    }
    let end = if end_text.is_empty() {
        total - 1
    } else {
        let requested = parse_range_u64(end_text)?;
        if requested < start {
            return Err(ArtifactDeliveryError::InvalidRange);
        }
        requested.min(total - 1)
    };
    Ok((start, end))
}

fn map_source_error(error: &ArtifactError) -> ArtifactDeliveryError {
    match error {
        ArtifactError::NotFound => ArtifactDeliveryError::NotFound,
        ArtifactError::AccessDenied => ArtifactDeliveryError::AccessDenied,
        ArtifactError::Quarantined | ArtifactError::InvalidState => {
            ArtifactDeliveryError::NotDeliverable
        }
        ArtifactError::IntegrityMismatch => ArtifactDeliveryError::IntegrityMismatch,
        ArtifactError::StorageFailure | ArtifactError::CryptoFailure => {
            ArtifactDeliveryError::SourceUnavailable
        }
        _ => ArtifactDeliveryError::InvalidRequest,
    }
}

fn semantic_request_digest(
    arguments: &Value,
    ttl: u64,
) -> Result<ContentDigest, ArtifactDeliveryError> {
    let fields = [
        required_string(arguments, "client_surface")?,
        required_string(arguments, "project_id")?,
        required_string(arguments, "idempotency_key")?,
        required_string(arguments, "artifact_id")?,
        required_string(arguments, "disposition")?,
    ];
    let mut framed = Vec::new();
    for field in fields {
        let length =
            u64::try_from(field.len()).map_err(|_| ArtifactDeliveryError::InvalidRequest)?;
        framed.extend_from_slice(&length.to_be_bytes());
        framed.extend_from_slice(field.as_bytes());
    }
    framed.extend_from_slice(&ttl.to_be_bytes());
    Ok(ContentDigest::of(&framed))
}

fn canonical_query(key_id: &str, claims: &DeliveryClaims) -> String {
    format!(
        "v=1&kid={key_id}&tenant={}&project={}&artifact={}&subject={}&content={}&request={}&binding={}&iat={}&exp={}&op={OPERATION}",
        claims.tenant_id.canonical(),
        claims.project_id,
        claims.artifact_id.public_id(),
        claims.subject_sha256.hex(),
        claims.content_sha256.hex(),
        claims.request_sha256.hex(),
        claims.binding_generation,
        claims.issued_at_unix_seconds,
        claims.expires_at_unix_seconds,
    )
}

fn required_string<'a>(value: &'a Value, field: &str) -> Result<&'a str, ArtifactDeliveryError> {
    value
        .get(field)
        .and_then(Value::as_str)
        .filter(|value| !value.is_empty())
        .ok_or(ArtifactDeliveryError::InvalidRequest)
}

fn parse_pair<'a>(pair: &'a str, expected: &str) -> Result<&'a str, ArtifactDeliveryError> {
    let (name, value) = pair
        .split_once('=')
        .ok_or(ArtifactDeliveryError::InvalidToken)?;
    if name != expected || value.is_empty() || value.contains('=') {
        return Err(ArtifactDeliveryError::InvalidToken);
    }
    Ok(value)
}

fn parse_token_u64(value: &str) -> Result<u64, ArtifactDeliveryError> {
    let parsed = value
        .parse::<u64>()
        .map_err(|_| ArtifactDeliveryError::InvalidToken)?;
    if parsed.to_string() != value {
        return Err(ArtifactDeliveryError::InvalidToken);
    }
    Ok(parsed)
}

fn parse_range_u64(value: &str) -> Result<u64, ArtifactDeliveryError> {
    let parsed = value
        .parse::<u64>()
        .map_err(|_| ArtifactDeliveryError::InvalidRange)?;
    if parsed.to_string() != value {
        return Err(ArtifactDeliveryError::InvalidRange);
    }
    Ok(parsed)
}

fn valid_https_base_url(value: &str) -> bool {
    if value.len() > 512
        || !value.starts_with("https://")
        || value.contains(['?', '#', '@'])
        || value.chars().any(char::is_whitespace)
    {
        return false;
    }
    let Some((authority, path)) = value[8..].split_once('/') else {
        return false;
    };
    let (host, port) = authority
        .split_once(':')
        .map_or((authority, None), |(host, port)| (host, Some(port)));
    !host.is_empty()
        && !path.is_empty()
        && host
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'-'))
        && port
            .is_none_or(|port| !port.is_empty() && port.bytes().all(|byte| byte.is_ascii_digit()))
        && path.bytes().all(|byte| {
            byte.is_ascii_alphanumeric() || matches!(byte, b'/' | b'-' | b'_' | b'.' | b'~')
        })
}

fn valid_key_id(value: &str) -> bool {
    (3..=MAX_KEY_ID_BYTES).contains(&value.len())
        && value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'-' | b'_'))
}

fn valid_prefixed_id(value: &str, prefix: &str) -> bool {
    value.len() <= MAX_PROJECT_ID_BYTES
        && value.strip_prefix(prefix).is_some_and(|suffix| {
            (8..=120).contains(&suffix.len())
                && suffix
                    .bytes()
                    .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'_' | b'-'))
        })
}

fn format_unix_timestamp(seconds: u64) -> Result<String, ArtifactDeliveryError> {
    if seconds > LAST_SCHEMA_UNIX_SECOND {
        return Err(ArtifactDeliveryError::InvalidRequest);
    }
    let days =
        i64::try_from(seconds / 86_400).map_err(|_| ArtifactDeliveryError::InvalidRequest)?;
    let seconds_of_day = seconds % 86_400;
    let (year, month, day) = civil_from_days(days);
    let hour = seconds_of_day / 3_600;
    let minute = (seconds_of_day % 3_600) / 60;
    let second = seconds_of_day % 60;
    Ok(format!(
        "{year:04}-{month:02}-{day:02}T{hour:02}:{minute:02}:{second:02}Z"
    ))
}

fn civil_from_days(days_since_epoch: i64) -> (i64, i64, i64) {
    let shifted = days_since_epoch + 719_468;
    let era = shifted / 146_097;
    let day_of_era = shifted - era * 146_097;
    let year_of_era =
        (day_of_era - day_of_era / 1_460 + day_of_era / 36_524 - day_of_era / 146_096) / 365;
    let mut year = year_of_era + era * 400;
    let day_of_year = day_of_era - (365 * year_of_era + year_of_era / 4 - year_of_era / 100);
    let month_prime = (5 * day_of_year + 2) / 153;
    let day = day_of_year - (153 * month_prime + 2) / 5 + 1;
    let month = month_prime + if month_prime < 10 { 3 } else { -9 };
    year += i64::from(month <= 2);
    (year, month, day)
}

fn lock<T>(mutex: &Mutex<T>) -> Result<MutexGuard<'_, T>, ArtifactDeliveryError> {
    mutex
        .lock()
        .map_err(|_| ArtifactDeliveryError::SourceUnavailable)
}
