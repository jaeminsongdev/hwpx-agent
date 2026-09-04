//! Fail-closed OAuth/OIDC resource-server authentication for the P15 MCP boundary.
//!
//! The HMAC verifier is a bounded local reference adapter. Production deployments must replace it
//! with an established identity provider and asymmetric JWKS verification before qualification.

use std::collections::{BTreeMap, BTreeSet};
use std::fmt;

use artifact_service::{ContentDigest, SubjectDigest, TenantId};
use base64::Engine as _;
use base64::engine::general_purpose::URL_SAFE_NO_PAD;
use hmac::{Hmac, Mac as _};
use serde::Deserialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;
use zeroize::Zeroizing;

type HmacSha256 = Hmac<Sha256>;

pub const MAX_BEARER_TOKEN_BYTES: usize = 8_192;
pub const MAX_HEADER_JSON_BYTES: usize = 1_024;
pub const MAX_CLAIMS_JSON_BYTES: usize = 4_096;
pub const MAX_ISSUER_BYTES: usize = 256;
pub const MAX_SUBJECT_BYTES: usize = 200;
pub const MAX_KEY_ID_BYTES: usize = 64;
pub const MAX_TOKEN_ID_BYTES: usize = 128;
pub const MAX_SCOPE_COUNT: usize = 32;
pub const MAX_CLOCK_SKEW_SECONDS: u64 = 300;
pub const MAX_USER_TOKEN_LIFETIME_SECONDS: u64 = 3_600;
pub const MAX_SERVICE_TOKEN_LIFETIME_SECONDS: u64 = 300;
pub const MAX_SIGNING_KEYS: usize = 64;
pub const MAX_PRINCIPALS: usize = 4_096;
pub const MAX_REVOCATIONS: usize = 8_192;
pub const MAX_CONSUMED_SERVICE_TOKENS: usize = 8_192;
const MIN_HMAC_KEY_BYTES: usize = 32;
const MAX_HMAC_KEY_BYTES: usize = 128;

#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum AuthScope {
    ArtifactRead,
    ArtifactWrite,
    JobCancel,
    JobSubmit,
    MirrorSync,
    ProjectRead,
    ProjectWrite,
    RetentionManage,
}

impl AuthScope {
    #[must_use]
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::ArtifactRead => "artifact.read",
            Self::ArtifactWrite => "artifact.write",
            Self::JobCancel => "job.cancel",
            Self::JobSubmit => "job.submit",
            Self::MirrorSync => "mirror.sync",
            Self::ProjectRead => "project.read",
            Self::ProjectWrite => "project.write",
            Self::RetentionManage => "retention.manage",
        }
    }

    fn parse(value: &str) -> Result<Self, AuthError> {
        match value {
            "artifact.read" => Ok(Self::ArtifactRead),
            "artifact.write" => Ok(Self::ArtifactWrite),
            "job.cancel" => Ok(Self::JobCancel),
            "job.submit" => Ok(Self::JobSubmit),
            "mirror.sync" => Ok(Self::MirrorSync),
            "project.read" => Ok(Self::ProjectRead),
            "project.write" => Ok(Self::ProjectWrite),
            "retention.manage" => Ok(Self::RetentionManage),
            _ => Err(AuthError::InvalidScope),
        }
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum PrincipalKind {
    User,
    Service,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum TenantRole {
    Reader,
    Editor,
    Owner,
    Worker,
}

impl TenantRole {
    const fn allows(self, scope: AuthScope) -> bool {
        match self {
            Self::Reader => matches!(scope, AuthScope::ArtifactRead | AuthScope::ProjectRead),
            Self::Editor => !matches!(scope, AuthScope::RetentionManage),
            Self::Owner => true,
            Self::Worker => matches!(
                scope,
                AuthScope::ArtifactRead
                    | AuthScope::ArtifactWrite
                    | AuthScope::JobCancel
                    | AuthScope::JobSubmit
                    | AuthScope::MirrorSync
                    | AuthScope::ProjectRead
            ),
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct AuthRegistryLimits {
    signing_keys: usize,
    principals: usize,
    revocations: usize,
    consumed_service_tokens: usize,
}

impl AuthRegistryLimits {
    /// Creates finite in-memory registry limits within the product hard maxima.
    ///
    /// # Errors
    ///
    /// Rejects zero or above-maximum capacities.
    pub fn new(
        signing_keys: usize,
        principals: usize,
        revocations: usize,
        consumed_service_tokens: usize,
    ) -> Result<Self, AuthError> {
        if !(1..=MAX_SIGNING_KEYS).contains(&signing_keys)
            || !(1..=MAX_PRINCIPALS).contains(&principals)
            || !(1..=MAX_REVOCATIONS).contains(&revocations)
            || !(1..=MAX_CONSUMED_SERVICE_TOKENS).contains(&consumed_service_tokens)
        {
            return Err(AuthError::InvalidConfiguration);
        }
        Ok(Self {
            signing_keys,
            principals,
            revocations,
            consumed_service_tokens,
        })
    }

    #[must_use]
    pub const fn product_maximums() -> Self {
        Self {
            signing_keys: MAX_SIGNING_KEYS,
            principals: MAX_PRINCIPALS,
            revocations: MAX_REVOCATIONS,
            consumed_service_tokens: MAX_CONSUMED_SERVICE_TOKENS,
        }
    }
}

#[derive(Clone)]
pub struct PrincipalGrant {
    tenant_id: TenantId,
    tenant_role: TenantRole,
    allowed_scopes: BTreeSet<AuthScope>,
    active_from_unix_seconds: u64,
    active_until_unix_seconds: u64,
}

impl PrincipalGrant {
    /// Creates one bounded tenant grant for a registered principal.
    ///
    /// # Errors
    ///
    /// Rejects empty/excessive scope sets and invalid activation windows.
    pub fn new(
        tenant_id: TenantId,
        tenant_role: TenantRole,
        allowed_scopes: impl IntoIterator<Item = AuthScope>,
        active_from_unix_seconds: u64,
        active_until_unix_seconds: u64,
    ) -> Result<Self, AuthError> {
        if active_from_unix_seconds >= active_until_unix_seconds {
            return Err(AuthError::InvalidConfiguration);
        }
        let allowed_scopes = collect_scopes(allowed_scopes)?;
        if !allowed_scopes
            .iter()
            .all(|scope| tenant_role.allows(*scope))
        {
            return Err(AuthError::InvalidConfiguration);
        }
        Ok(Self {
            tenant_id,
            tenant_role,
            allowed_scopes,
            active_from_unix_seconds,
            active_until_unix_seconds,
        })
    }
}

impl fmt::Debug for PrincipalGrant {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("PrincipalGrant")
            .field("tenant_id", &"<redacted>")
            .field("tenant_role", &self.tenant_role)
            .field("allowed_scope_count", &self.allowed_scopes.len())
            .field("active_from_unix_seconds", &self.active_from_unix_seconds)
            .field("active_until_unix_seconds", &self.active_until_unix_seconds)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct AuthContext {
    tenant_id: TenantId,
    subject: SubjectDigest,
    principal_kind: PrincipalKind,
    tenant_role: TenantRole,
    scopes: BTreeSet<AuthScope>,
    expires_at_unix_seconds: u64,
    token_sha256: ContentDigest,
}

impl AuthContext {
    #[must_use]
    pub const fn tenant_id(&self) -> TenantId {
        self.tenant_id
    }

    #[must_use]
    pub const fn subject(&self) -> SubjectDigest {
        self.subject
    }

    #[must_use]
    pub const fn principal_kind(&self) -> PrincipalKind {
        self.principal_kind
    }

    #[must_use]
    pub const fn tenant_role(&self) -> TenantRole {
        self.tenant_role
    }

    #[must_use]
    pub fn has_scope(&self, scope: AuthScope) -> bool {
        self.scopes.contains(&scope)
    }

    #[must_use]
    pub const fn expires_at_unix_seconds(&self) -> u64 {
        self.expires_at_unix_seconds
    }

    #[must_use]
    pub const fn token_sha256(&self) -> ContentDigest {
        self.token_sha256
    }
}

impl fmt::Debug for AuthContext {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("AuthContext")
            .field("tenant_id", &"<redacted>")
            .field("subject", &"<redacted>")
            .field("principal_kind", &self.principal_kind)
            .field("tenant_role", &self.tenant_role)
            .field("scope_count", &self.scopes.len())
            .field("expires_at_unix_seconds", &self.expires_at_unix_seconds)
            .field("token_sha256", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AuthChallenge {
    resource_metadata: String,
    scopes: BTreeSet<AuthScope>,
}

impl AuthChallenge {
    #[must_use]
    pub fn resource_metadata(&self) -> &str {
        &self.resource_metadata
    }

    #[must_use]
    pub fn scopes(&self) -> &BTreeSet<AuthScope> {
        &self.scopes
    }

    #[must_use]
    pub fn www_authenticate(&self) -> String {
        let scopes = self
            .scopes
            .iter()
            .map(|scope| scope.as_str())
            .collect::<Vec<_>>()
            .join(" ");
        format!(
            "Bearer resource_metadata=\"{}\", scope=\"{scopes}\"",
            self.resource_metadata
        )
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum AuthErrorCode {
    ConfigurationInvalid,
    AuthorizationHeaderInvalid,
    TokenTooLarge,
    TokenMalformed,
    AlgorithmUnsupported,
    SigningKeyUnknown,
    SignatureInvalid,
    IssuerMismatch,
    AudienceMismatch,
    TokenExpired,
    TokenNotYetValid,
    TokenIssuedInFuture,
    TokenLifetimeInvalid,
    TokenRevoked,
    TokenReplay,
    PrincipalUnknown,
    PrincipalInactive,
    PrincipalKindDenied,
    TenantMismatch,
    ScopeInvalid,
    ScopeDenied,
    CapacityExceeded,
    IdentityConflict,
}

#[derive(Clone, Copy, Debug, Error, Eq, PartialEq)]
pub enum AuthError {
    #[error("authentication configuration is invalid")]
    InvalidConfiguration,
    #[error("authorization header is invalid")]
    InvalidAuthorizationHeader,
    #[error("bearer token exceeds the configured limit")]
    TokenTooLarge,
    #[error("bearer token is malformed")]
    MalformedToken,
    #[error("token signing algorithm is unsupported")]
    UnsupportedAlgorithm,
    #[error("token signing key is unknown")]
    UnknownKey,
    #[error("token signature is invalid")]
    InvalidSignature,
    #[error("token issuer is invalid")]
    IssuerMismatch,
    #[error("token audience is invalid")]
    AudienceMismatch,
    #[error("token has expired")]
    TokenExpired,
    #[error("token is not active yet")]
    TokenNotYetValid,
    #[error("token was issued in the future")]
    TokenIssuedInFuture,
    #[error("token lifetime is invalid")]
    TokenLifetimeInvalid,
    #[error("token has been revoked")]
    TokenRevoked,
    #[error("single-use service token was replayed")]
    TokenReplay,
    #[error("authenticated principal is unknown")]
    UnknownPrincipal,
    #[error("authenticated principal is inactive")]
    PrincipalInactive,
    #[error("principal kind is not accepted on this boundary")]
    PrincipalKindDenied,
    #[error("token tenant does not match the registered identity")]
    TenantMismatch,
    #[error("token scope is invalid")]
    InvalidScope,
    #[error("required scope is not granted")]
    ScopeDenied,
    #[error("authentication registry capacity is exhausted")]
    CapacityExceeded,
    #[error("identity or key already exists")]
    Conflict,
}

impl AuthError {
    #[must_use]
    pub const fn code(self) -> AuthErrorCode {
        match self {
            Self::InvalidConfiguration => AuthErrorCode::ConfigurationInvalid,
            Self::InvalidAuthorizationHeader => AuthErrorCode::AuthorizationHeaderInvalid,
            Self::TokenTooLarge => AuthErrorCode::TokenTooLarge,
            Self::MalformedToken => AuthErrorCode::TokenMalformed,
            Self::UnsupportedAlgorithm => AuthErrorCode::AlgorithmUnsupported,
            Self::UnknownKey => AuthErrorCode::SigningKeyUnknown,
            Self::InvalidSignature => AuthErrorCode::SignatureInvalid,
            Self::IssuerMismatch => AuthErrorCode::IssuerMismatch,
            Self::AudienceMismatch => AuthErrorCode::AudienceMismatch,
            Self::TokenExpired => AuthErrorCode::TokenExpired,
            Self::TokenNotYetValid => AuthErrorCode::TokenNotYetValid,
            Self::TokenIssuedInFuture => AuthErrorCode::TokenIssuedInFuture,
            Self::TokenLifetimeInvalid => AuthErrorCode::TokenLifetimeInvalid,
            Self::TokenRevoked => AuthErrorCode::TokenRevoked,
            Self::TokenReplay => AuthErrorCode::TokenReplay,
            Self::UnknownPrincipal => AuthErrorCode::PrincipalUnknown,
            Self::PrincipalInactive => AuthErrorCode::PrincipalInactive,
            Self::PrincipalKindDenied => AuthErrorCode::PrincipalKindDenied,
            Self::TenantMismatch => AuthErrorCode::TenantMismatch,
            Self::InvalidScope => AuthErrorCode::ScopeInvalid,
            Self::ScopeDenied => AuthErrorCode::ScopeDenied,
            Self::CapacityExceeded => AuthErrorCode::CapacityExceeded,
            Self::Conflict => AuthErrorCode::IdentityConflict,
        }
    }
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct JwtHeader {
    alg: String,
    kid: String,
    typ: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct JwtClaims {
    iss: String,
    sub: String,
    aud: String,
    exp: u64,
    nbf: u64,
    iat: u64,
    jti: String,
    scope: String,
    token_kind: PrincipalKind,
    tenant_id: TenantId,
    service_id: Option<String>,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
struct ExternalIdentityDigest([u8; 32]);

struct LocalHmacKey {
    secret: Zeroizing<Vec<u8>>,
    active_from_unix_seconds: u64,
    active_until_unix_seconds: u64,
}

impl fmt::Debug for LocalHmacKey {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("LocalHmacKey")
            .field("secret", &"<redacted>")
            .field("active_from_unix_seconds", &self.active_from_unix_seconds)
            .field("active_until_unix_seconds", &self.active_until_unix_seconds)
            .finish()
    }
}

#[derive(Clone)]
struct PrincipalBinding {
    tenant_id: TenantId,
    subject: SubjectDigest,
    kind: PrincipalKind,
    tenant_role: TenantRole,
    allowed_scopes: BTreeSet<AuthScope>,
    active_from_unix_seconds: u64,
    active_until_unix_seconds: u64,
    service_id_digest: Option<ExternalIdentityDigest>,
}

impl fmt::Debug for PrincipalBinding {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("PrincipalBinding")
            .field("tenant_id", &"<redacted>")
            .field("subject", &"<redacted>")
            .field("kind", &self.kind)
            .field("tenant_role", &self.tenant_role)
            .field("allowed_scope_count", &self.allowed_scopes.len())
            .field("active_from_unix_seconds", &self.active_from_unix_seconds)
            .field("active_until_unix_seconds", &self.active_until_unix_seconds)
            .field("service_id", &self.service_id_digest.map(|_| "<redacted>"))
            .finish()
    }
}

pub struct AuthMiddleware {
    canonical_resource: String,
    resource_metadata: String,
    clock_skew_seconds: u64,
    limits: AuthRegistryLimits,
    keys: BTreeMap<(String, String), LocalHmacKey>,
    principals: BTreeMap<(String, ExternalIdentityDigest), PrincipalBinding>,
    revoked_tokens: BTreeMap<(String, String), u64>,
    consumed_service_tokens: BTreeMap<(String, String), u64>,
}

impl AuthMiddleware {
    /// Creates a local resource-server verifier with an exact HTTPS resource identifier.
    ///
    /// # Errors
    ///
    /// Rejects non-HTTPS, ambiguous or oversized identifiers and excessive clock skew.
    pub fn new(
        canonical_resource: impl Into<String>,
        resource_metadata: impl Into<String>,
        clock_skew_seconds: u64,
        limits: AuthRegistryLimits,
    ) -> Result<Self, AuthError> {
        let canonical_resource = canonical_resource.into();
        let resource_metadata = resource_metadata.into();
        if !is_https_identifier(&canonical_resource, MAX_ISSUER_BYTES)
            || canonical_resource.ends_with('/')
            || resource_metadata
                != format!("{canonical_resource}/.well-known/oauth-protected-resource")
            || clock_skew_seconds > MAX_CLOCK_SKEW_SECONDS
        {
            return Err(AuthError::InvalidConfiguration);
        }
        Ok(Self {
            canonical_resource,
            resource_metadata,
            clock_skew_seconds,
            limits,
            keys: BTreeMap::new(),
            principals: BTreeMap::new(),
            revoked_tokens: BTreeMap::new(),
            consumed_service_tokens: BTreeMap::new(),
        })
    }

    /// Registers one bounded local HMAC verification key.
    ///
    /// # Errors
    ///
    /// Rejects invalid issuers, identifiers, weak keys, invalid activation windows and duplicates.
    pub fn register_local_hmac_key(
        &mut self,
        issuer: impl Into<String>,
        key_id: impl Into<String>,
        secret: impl Into<Vec<u8>>,
        active_from_unix_seconds: u64,
        active_until_unix_seconds: u64,
    ) -> Result<(), AuthError> {
        let issuer = issuer.into();
        let key_id = key_id.into();
        let secret = secret.into();
        if !is_https_identifier(&issuer, MAX_ISSUER_BYTES)
            || !is_identifier(&key_id, 3, MAX_KEY_ID_BYTES)
            || !(MIN_HMAC_KEY_BYTES..=MAX_HMAC_KEY_BYTES).contains(&secret.len())
            || active_from_unix_seconds >= active_until_unix_seconds
        {
            return Err(AuthError::InvalidConfiguration);
        }
        let lookup = (issuer, key_id);
        if self.keys.contains_key(&lookup) {
            return Err(AuthError::Conflict);
        }
        if self.keys.len() >= self.limits.signing_keys {
            return Err(AuthError::CapacityExceeded);
        }
        self.keys.insert(
            lookup,
            LocalHmacKey {
                secret: Zeroizing::new(secret),
                active_from_unix_seconds,
                active_until_unix_seconds,
            },
        );
        Ok(())
    }

    /// Registers an OIDC subject-to-tenant mapping without retaining the raw subject.
    ///
    /// # Errors
    ///
    /// Rejects malformed identities, worker roles, invalid windows, invalid scope sets and duplicates.
    pub fn register_user(
        &mut self,
        issuer: impl Into<String>,
        external_subject: impl AsRef<str>,
        grant: PrincipalGrant,
    ) -> Result<SubjectDigest, AuthError> {
        if grant.tenant_role == TenantRole::Worker {
            return Err(AuthError::InvalidConfiguration);
        }
        let issuer = issuer.into();
        self.register_principal(
            &issuer,
            external_subject.as_ref(),
            PrincipalKind::User,
            grant,
            None,
        )
    }

    /// Registers an internal one-shot service-token identity.
    ///
    /// # Errors
    ///
    /// Rejects malformed identities, non-worker roles, invalid windows/scope sets and duplicates.
    pub fn register_service(
        &mut self,
        issuer: impl Into<String>,
        service_id: impl AsRef<str>,
        grant: PrincipalGrant,
    ) -> Result<SubjectDigest, AuthError> {
        if grant.tenant_role != TenantRole::Worker {
            return Err(AuthError::InvalidConfiguration);
        }
        let service_id = service_id.as_ref();
        let service_id_digest = external_identity_digest("service", service_id)?;
        let issuer = issuer.into();
        self.register_principal(
            &issuer,
            service_id,
            PrincipalKind::Service,
            grant,
            Some(service_id_digest),
        )
    }

    fn register_principal(
        &mut self,
        issuer: &str,
        external_subject: &str,
        kind: PrincipalKind,
        grant: PrincipalGrant,
        service_id_digest: Option<ExternalIdentityDigest>,
    ) -> Result<SubjectDigest, AuthError> {
        if !is_https_identifier(issuer, MAX_ISSUER_BYTES) || !is_external_subject(external_subject)
        {
            return Err(AuthError::InvalidConfiguration);
        }
        let external_digest = external_identity_digest(issuer, external_subject)?;
        let lookup = (issuer.to_owned(), external_digest);
        if self.principals.contains_key(&lookup) {
            return Err(AuthError::Conflict);
        }
        if self.principals.len() >= self.limits.principals {
            return Err(AuthError::CapacityExceeded);
        }
        let subject = internal_subject_digest(issuer, external_subject, kind)?;
        self.principals.insert(
            lookup,
            PrincipalBinding {
                tenant_id: grant.tenant_id,
                subject,
                kind,
                tenant_role: grant.tenant_role,
                allowed_scopes: grant.allowed_scopes,
                active_from_unix_seconds: grant.active_from_unix_seconds,
                active_until_unix_seconds: grant.active_until_unix_seconds,
                service_id_digest,
            },
        );
        Ok(subject)
    }

    /// Revokes one exact issuer/token-id pair without storing the bearer token.
    ///
    /// # Errors
    ///
    /// Rejects malformed issuer or token identifiers and duplicate revocations.
    pub fn revoke_token_id(
        &mut self,
        issuer: impl Into<String>,
        token_id: impl Into<String>,
        now_unix_seconds: u64,
    ) -> Result<(), AuthError> {
        let issuer = issuer.into();
        let token_id = token_id.into();
        if !is_https_identifier(&issuer, MAX_ISSUER_BYTES)
            || !is_identifier(&token_id, 8, MAX_TOKEN_ID_BYTES)
        {
            return Err(AuthError::InvalidConfiguration);
        }
        let expires_at_unix_seconds = now_unix_seconds
            .checked_add(MAX_USER_TOKEN_LIFETIME_SECONDS)
            .and_then(|value| value.checked_add(self.clock_skew_seconds))
            .ok_or(AuthError::InvalidConfiguration)?;
        self.revoked_tokens
            .retain(|_, expires_at| *expires_at > now_unix_seconds);
        let lookup = (issuer, token_id);
        if self.revoked_tokens.contains_key(&lookup) {
            return Err(AuthError::Conflict);
        }
        if self.revoked_tokens.len() >= self.limits.revocations {
            return Err(AuthError::CapacityExceeded);
        }
        self.revoked_tokens.insert(lookup, expires_at_unix_seconds);
        Ok(())
    }

    /// Authenticates an end-user OAuth bearer for the public MCP boundary.
    ///
    /// # Errors
    ///
    /// Fails closed for invalid headers/tokens, non-user principals or missing required scopes.
    pub fn authenticate_public_mcp(
        &mut self,
        authorization_header: &str,
        now_unix_seconds: u64,
        required_scopes: impl IntoIterator<Item = AuthScope>,
    ) -> Result<AuthContext, AuthError> {
        self.authenticate(
            authorization_header,
            now_unix_seconds,
            required_scopes,
            PrincipalKind::User,
            false,
        )
    }

    /// Authenticates and consumes one internal single-use service bearer.
    ///
    /// # Errors
    ///
    /// Fails closed for invalid tokens, non-service principals, missing scopes or replay.
    pub fn authenticate_internal_service_once(
        &mut self,
        authorization_header: &str,
        now_unix_seconds: u64,
        required_scopes: impl IntoIterator<Item = AuthScope>,
    ) -> Result<AuthContext, AuthError> {
        self.authenticate(
            authorization_header,
            now_unix_seconds,
            required_scopes,
            PrincipalKind::Service,
            true,
        )
    }

    fn authenticate(
        &mut self,
        authorization_header: &str,
        now_unix_seconds: u64,
        required_scopes: impl IntoIterator<Item = AuthScope>,
        required_kind: PrincipalKind,
        consume_once: bool,
    ) -> Result<AuthContext, AuthError> {
        let required_scopes = collect_scopes(required_scopes)?;
        let token = parse_bearer_header(authorization_header)?;
        let token_sha256 = ContentDigest::of(token.as_bytes());
        let verified = self.verify_token(token, now_unix_seconds)?;
        if verified.claims.token_kind != required_kind {
            return Err(AuthError::PrincipalKindDenied);
        }
        let external_digest = external_identity_digest(&verified.claims.iss, &verified.claims.sub)?;
        let binding = self
            .principals
            .get(&(verified.claims.iss.clone(), external_digest))
            .ok_or(AuthError::UnknownPrincipal)?;
        if binding.kind != verified.claims.token_kind {
            return Err(AuthError::PrincipalKindDenied);
        }
        if now_unix_seconds < binding.active_from_unix_seconds
            || now_unix_seconds >= binding.active_until_unix_seconds
        {
            return Err(AuthError::PrincipalInactive);
        }
        if binding.tenant_id != verified.claims.tenant_id {
            return Err(AuthError::TenantMismatch);
        }
        if !verified.scopes.is_subset(&binding.allowed_scopes)
            || !required_scopes.is_subset(&verified.scopes)
        {
            return Err(AuthError::ScopeDenied);
        }
        match (verified.claims.token_kind, &verified.claims.service_id) {
            (PrincipalKind::User, None) => {}
            (PrincipalKind::Service, Some(service_id)) => {
                if Some(external_identity_digest("service", service_id)?)
                    != binding.service_id_digest
                    || service_id != &verified.claims.sub
                {
                    return Err(AuthError::UnknownPrincipal);
                }
            }
            _ => return Err(AuthError::MalformedToken),
        }
        let replay_key = (verified.claims.iss.clone(), verified.claims.jti.clone());
        self.revoked_tokens
            .retain(|_, expires_at| *expires_at > now_unix_seconds);
        if self.revoked_tokens.contains_key(&replay_key) {
            return Err(AuthError::TokenRevoked);
        }
        if consume_once {
            self.consumed_service_tokens
                .retain(|_, expires_at| *expires_at > now_unix_seconds);
            if self.consumed_service_tokens.contains_key(&replay_key) {
                return Err(AuthError::TokenReplay);
            }
            if self.consumed_service_tokens.len() >= self.limits.consumed_service_tokens {
                return Err(AuthError::CapacityExceeded);
            }
            self.consumed_service_tokens
                .insert(replay_key, verified.claims.exp);
        }
        Ok(AuthContext {
            tenant_id: binding.tenant_id,
            subject: binding.subject,
            principal_kind: binding.kind,
            tenant_role: binding.tenant_role,
            scopes: verified.scopes,
            expires_at_unix_seconds: verified.claims.exp,
            token_sha256,
        })
    }

    fn verify_token(&self, token: &str, now_unix_seconds: u64) -> Result<VerifiedToken, AuthError> {
        let mut parts = token.split('.');
        let encoded_header = parts.next().ok_or(AuthError::MalformedToken)?;
        let encoded_claims = parts.next().ok_or(AuthError::MalformedToken)?;
        let encoded_signature = parts.next().ok_or(AuthError::MalformedToken)?;
        if encoded_header.is_empty()
            || encoded_claims.is_empty()
            || encoded_signature.is_empty()
            || parts.next().is_some()
        {
            return Err(AuthError::MalformedToken);
        }
        let header_bytes = decode_segment(encoded_header, MAX_HEADER_JSON_BYTES)?;
        let claims_bytes = decode_segment(encoded_claims, MAX_CLAIMS_JSON_BYTES)?;
        let header: JwtHeader =
            serde_json::from_slice(&header_bytes).map_err(|_| AuthError::MalformedToken)?;
        let claims: JwtClaims =
            serde_json::from_slice(&claims_bytes).map_err(|_| AuthError::MalformedToken)?;
        if header.alg != "HS256" {
            return Err(AuthError::UnsupportedAlgorithm);
        }
        if !is_identifier(&header.kid, 3, MAX_KEY_ID_BYTES)
            || !is_https_identifier(&claims.iss, MAX_ISSUER_BYTES)
            || !is_external_subject(&claims.sub)
            || !is_identifier(&claims.jti, 8, MAX_TOKEN_ID_BYTES)
        {
            return Err(AuthError::MalformedToken);
        }
        let expected_type = match claims.token_kind {
            PrincipalKind::User => "at+jwt",
            PrincipalKind::Service => "hwpx-service+jwt",
        };
        if header.typ != expected_type {
            return Err(AuthError::MalformedToken);
        }
        let key = self
            .keys
            .get(&(claims.iss.clone(), header.kid))
            .ok_or(AuthError::UnknownKey)?;
        if now_unix_seconds < key.active_from_unix_seconds
            || now_unix_seconds >= key.active_until_unix_seconds
        {
            return Err(AuthError::UnknownKey);
        }
        let signature = URL_SAFE_NO_PAD
            .decode(encoded_signature)
            .map_err(|_| AuthError::MalformedToken)?;
        let mut verifier = <HmacSha256 as hmac::KeyInit>::new_from_slice(&key.secret)
            .map_err(|_| AuthError::InvalidConfiguration)?;
        verifier.update(format!("{encoded_header}.{encoded_claims}").as_bytes());
        verifier
            .verify_slice(&signature)
            .map_err(|_| AuthError::InvalidSignature)?;
        if claims.aud != self.canonical_resource {
            return Err(AuthError::AudienceMismatch);
        }
        validate_times(&claims, now_unix_seconds, self.clock_skew_seconds)?;
        let scopes = parse_scope_claim(&claims.scope)?;
        Ok(VerifiedToken { claims, scopes })
    }

    /// Builds the exact OAuth discovery challenge for one non-empty scope set.
    ///
    /// # Errors
    ///
    /// Rejects empty, duplicate-free-overflowing or otherwise invalid scope sets.
    pub fn challenge(
        &self,
        required_scopes: impl IntoIterator<Item = AuthScope>,
    ) -> Result<AuthChallenge, AuthError> {
        Ok(AuthChallenge {
            resource_metadata: self.resource_metadata.clone(),
            scopes: collect_scopes(required_scopes)?,
        })
    }
}

impl fmt::Debug for AuthMiddleware {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("AuthMiddleware")
            .field("canonical_resource", &self.canonical_resource)
            .field("resource_metadata", &self.resource_metadata)
            .field("clock_skew_seconds", &self.clock_skew_seconds)
            .field("limits", &self.limits)
            .field("key_count", &self.keys.len())
            .field("principal_count", &self.principals.len())
            .field("revoked_token_count", &self.revoked_tokens.len())
            .field(
                "consumed_service_token_count",
                &self.consumed_service_tokens.len(),
            )
            .finish()
    }
}

struct VerifiedToken {
    claims: JwtClaims,
    scopes: BTreeSet<AuthScope>,
}

fn parse_bearer_header(header: &str) -> Result<&str, AuthError> {
    if header.as_bytes().iter().any(u8::is_ascii_control) {
        return Err(AuthError::InvalidAuthorizationHeader);
    }
    let token = header
        .strip_prefix("Bearer ")
        .ok_or(AuthError::InvalidAuthorizationHeader)?;
    if token.is_empty()
        || token.len() > MAX_BEARER_TOKEN_BYTES
        || token
            .bytes()
            .any(|byte| !(byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_' | b'.')))
    {
        return Err(if token.len() > MAX_BEARER_TOKEN_BYTES {
            AuthError::TokenTooLarge
        } else {
            AuthError::InvalidAuthorizationHeader
        });
    }
    Ok(token)
}

fn decode_segment(value: &str, maximum: usize) -> Result<Vec<u8>, AuthError> {
    if value.len() > maximum.saturating_mul(2) {
        return Err(AuthError::TokenTooLarge);
    }
    let decoded = URL_SAFE_NO_PAD
        .decode(value)
        .map_err(|_| AuthError::MalformedToken)?;
    if decoded.len() > maximum {
        return Err(AuthError::TokenTooLarge);
    }
    Ok(decoded)
}

fn validate_times(
    claims: &JwtClaims,
    now_unix_seconds: u64,
    clock_skew_seconds: u64,
) -> Result<(), AuthError> {
    if now_unix_seconds >= claims.exp {
        return Err(AuthError::TokenExpired);
    }
    let latest_acceptable = now_unix_seconds.saturating_add(clock_skew_seconds);
    if claims.nbf > latest_acceptable {
        return Err(AuthError::TokenNotYetValid);
    }
    if claims.iat > latest_acceptable {
        return Err(AuthError::TokenIssuedInFuture);
    }
    let lifetime = claims
        .exp
        .checked_sub(claims.iat)
        .ok_or(AuthError::TokenLifetimeInvalid)?;
    let maximum = match claims.token_kind {
        PrincipalKind::User => MAX_USER_TOKEN_LIFETIME_SECONDS,
        PrincipalKind::Service => MAX_SERVICE_TOKEN_LIFETIME_SECONDS,
    };
    if lifetime == 0 || lifetime > maximum || claims.nbf < claims.iat || claims.nbf >= claims.exp {
        return Err(AuthError::TokenLifetimeInvalid);
    }
    Ok(())
}

fn parse_scope_claim(value: &str) -> Result<BTreeSet<AuthScope>, AuthError> {
    if value.is_empty() || value.len() > 1_024 || value.contains("  ") {
        return Err(AuthError::InvalidScope);
    }
    let mut scopes = BTreeSet::new();
    for value in value.split(' ') {
        if value.is_empty() || !scopes.insert(AuthScope::parse(value)?) {
            return Err(AuthError::InvalidScope);
        }
    }
    if scopes.len() > MAX_SCOPE_COUNT {
        return Err(AuthError::InvalidScope);
    }
    Ok(scopes)
}

fn collect_scopes(
    values: impl IntoIterator<Item = AuthScope>,
) -> Result<BTreeSet<AuthScope>, AuthError> {
    let scopes: BTreeSet<_> = values.into_iter().collect();
    if scopes.is_empty() || scopes.len() > MAX_SCOPE_COUNT {
        return Err(AuthError::InvalidConfiguration);
    }
    Ok(scopes)
}

fn external_identity_digest(
    issuer: &str,
    external_subject: &str,
) -> Result<ExternalIdentityDigest, AuthError> {
    if issuer.len() > MAX_ISSUER_BYTES || !is_external_subject(external_subject) {
        return Err(AuthError::InvalidConfiguration);
    }
    let framed = format!(
        "{}:{issuer}:{}:{external_subject}",
        issuer.len(),
        external_subject.len()
    );
    Ok(ExternalIdentityDigest(
        Sha256::digest(framed.as_bytes()).into(),
    ))
}

fn internal_subject_digest(
    issuer: &str,
    external_subject: &str,
    kind: PrincipalKind,
) -> Result<SubjectDigest, AuthError> {
    let kind = match kind {
        PrincipalKind::User => "user",
        PrincipalKind::Service => "service",
    };
    let framed = format!(
        "{kind}:{}:{issuer}:{}:{external_subject}",
        issuer.len(),
        external_subject.len()
    );
    SubjectDigest::from_authenticated_subject(&framed).map_err(|_| AuthError::InvalidConfiguration)
}

fn is_external_subject(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= MAX_SUBJECT_BYTES
        && value
            .bytes()
            .all(|byte| byte.is_ascii_graphic() && byte != b'\\')
}

fn is_identifier(value: &str, minimum: usize, maximum: usize) -> bool {
    (minimum..=maximum).contains(&value.len())
        && value
            .as_bytes()
            .first()
            .is_some_and(u8::is_ascii_alphanumeric)
        && value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'_' | b'-' | b':'))
}

fn is_https_identifier(value: &str, maximum: usize) -> bool {
    if value.len() < 12
        || value.len() > maximum
        || !value.starts_with("https://")
        || !value.is_ascii()
        || value.bytes().any(|byte| {
            byte.is_ascii_control() || matches!(byte, b' ' | b'?' | b'#' | b'@' | b'\\')
        })
        || !value.bytes().all(|byte| {
            byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'-' | b':' | b'/' | b'_' | b'~')
        })
    {
        return false;
    }
    let authority = value[8..].split('/').next().unwrap_or_default();
    !authority.is_empty()
        && !authority.starts_with('.')
        && !authority.ends_with('.')
        && authority.contains('.')
        && authority
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'-' | b':'))
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde::Serialize;
    use serde_json::{Value, json};
    use uuid::Uuid;

    const RESOURCE: &str = "https://mcp.hwpx-agent.example";
    const METADATA: &str = "https://mcp.hwpx-agent.example/.well-known/oauth-protected-resource";
    const ISSUER: &str = "https://identity.hwpx-agent.example";
    const OTHER_ISSUER: &str = "https://other-identity.hwpx-agent.example";
    const KEY_ID: &str = "local-key-01";
    const SECRET: &[u8] = b"0123456789abcdef0123456789abcdef";
    const NOW: u64 = 2_000_000_000;

    #[derive(Clone, Serialize)]
    struct TestClaims {
        iss: String,
        sub: String,
        aud: String,
        exp: u64,
        nbf: u64,
        iat: u64,
        jti: String,
        scope: String,
        token_kind: String,
        tenant_id: TenantId,
        #[serde(skip_serializing_if = "Option::is_none")]
        service_id: Option<String>,
    }

    struct Fixture {
        middleware: AuthMiddleware,
        tenant: TenantId,
        user_subject: SubjectDigest,
        service_subject: SubjectDigest,
    }

    fn tenant(value: u128) -> TenantId {
        TenantId::new(Uuid::from_u128(value))
            .unwrap_or_else(|error| panic!("tenant fixture: {error}"))
    }

    fn grant(
        tenant_id: TenantId,
        tenant_role: TenantRole,
        scopes: impl IntoIterator<Item = AuthScope>,
    ) -> PrincipalGrant {
        PrincipalGrant::new(tenant_id, tenant_role, scopes, NOW - 600, NOW + 7_200)
            .unwrap_or_else(|error| panic!("grant fixture: {error}"))
    }

    fn fixture() -> Fixture {
        let tenant = tenant(1);
        let mut middleware = AuthMiddleware::new(
            RESOURCE,
            METADATA,
            60,
            AuthRegistryLimits::product_maximums(),
        )
        .unwrap_or_else(|error| panic!("middleware fixture: {error}"));
        middleware
            .register_local_hmac_key(ISSUER, KEY_ID, SECRET, NOW - 600, NOW + 7_200)
            .unwrap_or_else(|error| panic!("key fixture: {error}"));
        let user_subject = middleware
            .register_user(
                ISSUER,
                "oidc-user-42",
                grant(
                    tenant,
                    TenantRole::Owner,
                    [
                        AuthScope::ProjectRead,
                        AuthScope::ProjectWrite,
                        AuthScope::JobSubmit,
                        AuthScope::ArtifactRead,
                    ],
                ),
            )
            .unwrap_or_else(|error| panic!("user fixture: {error}"));
        let service_subject = middleware
            .register_service(
                ISSUER,
                "worker-01",
                grant(
                    tenant,
                    TenantRole::Worker,
                    [AuthScope::ArtifactRead, AuthScope::MirrorSync],
                ),
            )
            .unwrap_or_else(|error| panic!("service fixture: {error}"));
        Fixture {
            middleware,
            tenant,
            user_subject,
            service_subject,
        }
    }

    fn user_claims(tenant_id: TenantId) -> TestClaims {
        TestClaims {
            iss: ISSUER.to_owned(),
            sub: "oidc-user-42".to_owned(),
            aud: RESOURCE.to_owned(),
            exp: NOW + 600,
            nbf: NOW - 60,
            iat: NOW - 60,
            jti: "user-token-0001".to_owned(),
            scope: "project.read project.write job.submit artifact.read".to_owned(),
            token_kind: "user".to_owned(),
            tenant_id,
            service_id: None,
        }
    }

    fn service_claims(tenant_id: TenantId) -> TestClaims {
        TestClaims {
            iss: ISSUER.to_owned(),
            sub: "worker-01".to_owned(),
            aud: RESOURCE.to_owned(),
            exp: NOW + 120,
            nbf: NOW - 10,
            iat: NOW - 10,
            jti: "service-token-0001".to_owned(),
            scope: "artifact.read mirror.sync".to_owned(),
            token_kind: "service".to_owned(),
            tenant_id,
            service_id: Some("worker-01".to_owned()),
        }
    }

    fn sign(claims: &TestClaims, token_type: &str, key_id: &str, secret: &[u8]) -> String {
        let header = json!({"alg": "HS256", "kid": key_id, "typ": token_type});
        sign_values(
            &header,
            &serde_json::to_value(claims)
                .unwrap_or_else(|error| panic!("serialize claims fixture: {error}")),
            secret,
        )
    }

    fn sign_values(header: &Value, claims: &Value, secret: &[u8]) -> String {
        let header = URL_SAFE_NO_PAD.encode(
            serde_json::to_vec(header)
                .unwrap_or_else(|error| panic!("serialize header fixture: {error}")),
        );
        let claims = URL_SAFE_NO_PAD.encode(
            serde_json::to_vec(claims)
                .unwrap_or_else(|error| panic!("serialize claims value fixture: {error}")),
        );
        let signing_input = format!("{header}.{claims}");
        let mut signer = <HmacSha256 as hmac::KeyInit>::new_from_slice(secret)
            .unwrap_or_else(|error| panic!("signing fixture: {error}"));
        signer.update(signing_input.as_bytes());
        format!(
            "{signing_input}.{}",
            URL_SAFE_NO_PAD.encode(signer.finalize().into_bytes())
        )
    }

    fn bearer(token: &str) -> String {
        format!("Bearer {token}")
    }

    #[test]
    fn valid_user_token_maps_exact_tenant_subject_role_and_scopes() {
        let mut fixture = fixture();
        let token = sign(&user_claims(fixture.tenant), "at+jwt", KEY_ID, SECRET);
        let context = fixture
            .middleware
            .authenticate_public_mcp(
                &bearer(&token),
                NOW,
                [AuthScope::ProjectWrite, AuthScope::JobSubmit],
            )
            .unwrap_or_else(|error| panic!("authenticate user: {error}"));
        assert_eq!(context.tenant_id(), fixture.tenant);
        assert_eq!(context.subject(), fixture.user_subject);
        assert_eq!(context.principal_kind(), PrincipalKind::User);
        assert_eq!(context.tenant_role(), TenantRole::Owner);
        assert!(context.has_scope(AuthScope::ProjectRead));
        assert_eq!(context.expires_at_unix_seconds(), NOW + 600);
        assert_eq!(context.token_sha256(), ContentDigest::of(token.as_bytes()));
    }

    #[test]
    fn authorization_header_and_token_shape_are_exact_and_bounded() {
        let mut fixture = fixture();
        let token = sign(&user_claims(fixture.tenant), "at+jwt", KEY_ID, SECRET);
        for invalid in [
            token.as_str(),
            &format!("bearer {token}"),
            &format!("Bearer  {token}"),
            "Bearer a.b",
            "Bearer a.b.c.d",
            "Bearer a+b.c.d",
        ] {
            assert!(
                fixture
                    .middleware
                    .authenticate_public_mcp(invalid, NOW, [AuthScope::ProjectRead])
                    .is_err()
            );
        }
        let oversized = format!("Bearer {}", "a".repeat(MAX_BEARER_TOKEN_BYTES + 1));
        assert_eq!(
            fixture
                .middleware
                .authenticate_public_mcp(&oversized, NOW, [AuthScope::ProjectRead]),
            Err(AuthError::TokenTooLarge)
        );
    }

    #[test]
    fn signature_algorithm_key_and_tamper_fail_closed() {
        let mut fixture = fixture();
        let claims = user_claims(fixture.tenant);
        let wrong_alg = sign_values(
            &json!({"alg": "none", "kid": KEY_ID, "typ": "at+jwt"}),
            &serde_json::to_value(&claims)
                .unwrap_or_else(|error| panic!("claims fixture: {error}")),
            SECRET,
        );
        assert_eq!(
            fixture.middleware.authenticate_public_mcp(
                &bearer(&wrong_alg),
                NOW,
                [AuthScope::ProjectRead]
            ),
            Err(AuthError::UnsupportedAlgorithm)
        );
        let unknown = sign(&claims, "at+jwt", "unknown-key", SECRET);
        assert_eq!(
            fixture.middleware.authenticate_public_mcp(
                &bearer(&unknown),
                NOW,
                [AuthScope::ProjectRead]
            ),
            Err(AuthError::UnknownKey)
        );
        let invalid = sign(
            &claims,
            "at+jwt",
            KEY_ID,
            b"abcdef0123456789abcdef0123456789",
        );
        assert_eq!(
            fixture.middleware.authenticate_public_mcp(
                &bearer(&invalid),
                NOW,
                [AuthScope::ProjectRead]
            ),
            Err(AuthError::InvalidSignature)
        );
    }

    #[test]
    fn exact_issuer_audience_and_tenant_mapping_are_required() {
        let mut fixture = fixture();
        let mut claims = user_claims(fixture.tenant);
        claims.aud = "https://other-resource.example".to_owned();
        let token = sign(&claims, "at+jwt", KEY_ID, SECRET);
        assert_eq!(
            fixture.middleware.authenticate_public_mcp(
                &bearer(&token),
                NOW,
                [AuthScope::ProjectRead]
            ),
            Err(AuthError::AudienceMismatch)
        );
        claims = user_claims(tenant(2));
        let token = sign(&claims, "at+jwt", KEY_ID, SECRET);
        assert_eq!(
            fixture.middleware.authenticate_public_mcp(
                &bearer(&token),
                NOW,
                [AuthScope::ProjectRead]
            ),
            Err(AuthError::TenantMismatch)
        );
        claims = user_claims(fixture.tenant);
        claims.sub = "unknown-user".to_owned();
        let token = sign(&claims, "at+jwt", KEY_ID, SECRET);
        assert_eq!(
            fixture.middleware.authenticate_public_mcp(
                &bearer(&token),
                NOW,
                [AuthScope::ProjectRead]
            ),
            Err(AuthError::UnknownPrincipal)
        );
    }

    #[test]
    fn expiration_not_before_future_issue_and_lifetime_are_distinct() {
        let cases = [
            (NOW - 1, NOW - 100, NOW - 100, AuthError::TokenExpired),
            (NOW + 600, NOW + 61, NOW, AuthError::TokenNotYetValid),
            (NOW + 600, NOW + 61, NOW + 61, AuthError::TokenNotYetValid),
            (
                NOW + MAX_USER_TOKEN_LIFETIME_SECONDS + 1,
                NOW,
                NOW,
                AuthError::TokenLifetimeInvalid,
            ),
        ];
        for (exp, nbf, iat, expected) in cases {
            let mut fixture = fixture();
            let mut claims = user_claims(fixture.tenant);
            claims.exp = exp;
            claims.nbf = nbf;
            claims.iat = iat;
            let token = sign(&claims, "at+jwt", KEY_ID, SECRET);
            assert_eq!(
                fixture.middleware.authenticate_public_mcp(
                    &bearer(&token),
                    NOW,
                    [AuthScope::ProjectRead]
                ),
                Err(expected)
            );
        }
        let mut fixture = fixture();
        let mut claims = user_claims(fixture.tenant);
        claims.nbf = NOW;
        claims.iat = NOW + 61;
        let token = sign(&claims, "at+jwt", KEY_ID, SECRET);
        assert_eq!(
            fixture.middleware.authenticate_public_mcp(
                &bearer(&token),
                NOW,
                [AuthScope::ProjectRead]
            ),
            Err(AuthError::TokenIssuedInFuture)
        );
    }

    #[test]
    fn token_and_binding_scopes_are_both_enforced() {
        let mut fixture = fixture();
        let mut claims = user_claims(fixture.tenant);
        claims.scope = "project.read retention.manage".to_owned();
        let token = sign(&claims, "at+jwt", KEY_ID, SECRET);
        assert_eq!(
            fixture.middleware.authenticate_public_mcp(
                &bearer(&token),
                NOW,
                [AuthScope::ProjectRead]
            ),
            Err(AuthError::ScopeDenied)
        );
        let token = sign(&user_claims(fixture.tenant), "at+jwt", KEY_ID, SECRET);
        assert_eq!(
            fixture.middleware.authenticate_public_mcp(
                &bearer(&token),
                NOW,
                [AuthScope::RetentionManage]
            ),
            Err(AuthError::ScopeDenied)
        );
    }

    #[test]
    fn unknown_duplicate_and_noncanonical_scopes_are_rejected() {
        for scope in [
            "project.read unknown.scope",
            "project.read project.read",
            "project.read  job.submit",
            "project.read\tjob.submit",
        ] {
            let mut fixture = fixture();
            let mut claims = user_claims(fixture.tenant);
            claims.scope = scope.to_owned();
            let token = sign(&claims, "at+jwt", KEY_ID, SECRET);
            assert_eq!(
                fixture.middleware.authenticate_public_mcp(
                    &bearer(&token),
                    NOW,
                    [AuthScope::ProjectRead]
                ),
                Err(AuthError::InvalidScope)
            );
        }
    }

    #[test]
    fn public_user_and_internal_service_boundaries_never_mix() {
        let mut fixture = fixture();
        let user = sign(&user_claims(fixture.tenant), "at+jwt", KEY_ID, SECRET);
        assert_eq!(
            fixture.middleware.authenticate_internal_service_once(
                &bearer(&user),
                NOW,
                [AuthScope::ArtifactRead]
            ),
            Err(AuthError::PrincipalKindDenied)
        );
        let service = sign(
            &service_claims(fixture.tenant),
            "hwpx-service+jwt",
            KEY_ID,
            SECRET,
        );
        assert_eq!(
            fixture.middleware.authenticate_public_mcp(
                &bearer(&service),
                NOW,
                [AuthScope::ArtifactRead]
            ),
            Err(AuthError::PrincipalKindDenied)
        );
    }

    #[test]
    fn service_token_is_single_use_and_bound_to_service_identity() {
        let mut fixture = fixture();
        let token = sign(
            &service_claims(fixture.tenant),
            "hwpx-service+jwt",
            KEY_ID,
            SECRET,
        );
        let context = fixture
            .middleware
            .authenticate_internal_service_once(&bearer(&token), NOW, [AuthScope::MirrorSync])
            .unwrap_or_else(|error| panic!("authenticate service: {error}"));
        assert_eq!(context.subject(), fixture.service_subject);
        assert_eq!(context.tenant_role(), TenantRole::Worker);
        assert_eq!(
            fixture.middleware.authenticate_internal_service_once(
                &bearer(&token),
                NOW,
                [AuthScope::MirrorSync]
            ),
            Err(AuthError::TokenReplay)
        );
        let mut mismatch = service_claims(fixture.tenant);
        mismatch.jti = "service-token-0002".to_owned();
        mismatch.service_id = Some("worker-02".to_owned());
        let token = sign(&mismatch, "hwpx-service+jwt", KEY_ID, SECRET);
        assert_eq!(
            fixture.middleware.authenticate_internal_service_once(
                &bearer(&token),
                NOW,
                [AuthScope::MirrorSync]
            ),
            Err(AuthError::UnknownPrincipal)
        );
    }

    #[test]
    fn revocation_and_inactive_keys_and_principals_fail_closed() {
        let mut fixture = fixture();
        fixture
            .middleware
            .revoke_token_id(ISSUER, "user-token-0001", NOW)
            .unwrap_or_else(|error| panic!("revoke fixture: {error}"));
        let token = sign(&user_claims(fixture.tenant), "at+jwt", KEY_ID, SECRET);
        assert_eq!(
            fixture.middleware.authenticate_public_mcp(
                &bearer(&token),
                NOW,
                [AuthScope::ProjectRead]
            ),
            Err(AuthError::TokenRevoked)
        );
        assert_eq!(
            fixture
                .middleware
                .revoke_token_id(ISSUER, "user-token-0001", NOW),
            Err(AuthError::Conflict)
        );

        let mut inactive = AuthMiddleware::new(
            RESOURCE,
            METADATA,
            0,
            AuthRegistryLimits::product_maximums(),
        )
        .unwrap_or_else(|error| panic!("inactive middleware: {error}"));
        inactive
            .register_local_hmac_key(ISSUER, KEY_ID, SECRET, NOW + 1, NOW + 600)
            .unwrap_or_else(|error| panic!("inactive key: {error}"));
        assert_eq!(
            inactive.authenticate_public_mcp(&bearer(&token), NOW, [AuthScope::ProjectRead]),
            Err(AuthError::UnknownKey)
        );
    }

    #[test]
    fn duplicate_key_and_identity_registration_are_side_effect_free() {
        let mut fixture = fixture();
        assert_eq!(
            fixture.middleware.register_local_hmac_key(
                ISSUER,
                KEY_ID,
                b"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                NOW,
                NOW + 60
            ),
            Err(AuthError::Conflict)
        );
        assert_eq!(
            fixture.middleware.register_user(
                ISSUER,
                "oidc-user-42",
                grant(tenant(2), TenantRole::Reader, [AuthScope::ProjectRead])
            ),
            Err(AuthError::Conflict)
        );
        let token = sign(&user_claims(fixture.tenant), "at+jwt", KEY_ID, SECRET);
        assert!(
            fixture
                .middleware
                .authenticate_public_mcp(&bearer(&token), NOW, [AuthScope::ProjectRead])
                .is_ok()
        );
    }

    #[test]
    fn registries_are_bounded_and_expired_replay_state_is_pruned() {
        let limits = AuthRegistryLimits::new(1, 2, 1, 1)
            .unwrap_or_else(|error| panic!("bounded limits fixture: {error}"));
        let mut middleware = AuthMiddleware::new(RESOURCE, METADATA, 0, limits)
            .unwrap_or_else(|error| panic!("bounded middleware fixture: {error}"));
        middleware
            .register_local_hmac_key(ISSUER, KEY_ID, SECRET, NOW - 600, NOW + 7_200)
            .unwrap_or_else(|error| panic!("bounded key fixture: {error}"));
        assert_eq!(
            middleware.register_local_hmac_key(OTHER_ISSUER, "other-key", SECRET, NOW, NOW + 60),
            Err(AuthError::CapacityExceeded)
        );
        middleware
            .register_user(
                ISSUER,
                "oidc-user-42",
                grant(tenant(1), TenantRole::Reader, [AuthScope::ProjectRead]),
            )
            .unwrap_or_else(|error| panic!("bounded user fixture: {error}"));
        middleware
            .register_service(
                ISSUER,
                "worker-01",
                grant(
                    tenant(1),
                    TenantRole::Worker,
                    [AuthScope::ArtifactRead, AuthScope::MirrorSync],
                ),
            )
            .unwrap_or_else(|error| panic!("bounded service fixture: {error}"));
        assert_eq!(
            middleware.register_user(
                ISSUER,
                "another-user",
                grant(tenant(1), TenantRole::Reader, [AuthScope::ProjectRead])
            ),
            Err(AuthError::CapacityExceeded)
        );

        middleware
            .revoke_token_id(ISSUER, "revoked-token-01", NOW)
            .unwrap_or_else(|error| panic!("bounded revoke fixture: {error}"));
        assert_eq!(
            middleware.revoke_token_id(ISSUER, "revoked-token-02", NOW),
            Err(AuthError::CapacityExceeded)
        );
        middleware
            .revoke_token_id(
                ISSUER,
                "revoked-token-02",
                NOW + MAX_USER_TOKEN_LIFETIME_SECONDS,
            )
            .unwrap_or_else(|error| panic!("pruned revoke fixture: {error}"));

        let mut first = service_claims(tenant(1));
        first.exp = NOW + 1;
        let first = sign(&first, "hwpx-service+jwt", KEY_ID, SECRET);
        assert!(
            middleware
                .authenticate_internal_service_once(&bearer(&first), NOW, [AuthScope::ArtifactRead])
                .is_ok()
        );
        let mut second = service_claims(tenant(1));
        second.jti = "service-token-0002".to_owned();
        let second = sign(&second, "hwpx-service+jwt", KEY_ID, SECRET);
        assert_eq!(
            middleware.authenticate_internal_service_once(
                &bearer(&second),
                NOW,
                [AuthScope::ArtifactRead]
            ),
            Err(AuthError::CapacityExceeded)
        );
        assert!(
            middleware
                .authenticate_internal_service_once(
                    &bearer(&second),
                    NOW + 1,
                    [AuthScope::ArtifactRead]
                )
                .is_ok()
        );
        assert!(AuthRegistryLimits::new(0, 1, 1, 1).is_err());
        assert!(AuthRegistryLimits::new(1, MAX_PRINCIPALS + 1, 1, 1).is_err());
    }

    #[test]
    fn malformed_duplicate_unknown_and_multiaudience_claims_are_rejected() {
        let mut fixture = fixture();
        let base = serde_json::to_value(user_claims(fixture.tenant))
            .unwrap_or_else(|error| panic!("base claims fixture: {error}"));
        let mut unknown = base.clone();
        unknown
            .as_object_mut()
            .unwrap_or_else(|| panic!("claims object fixture"))
            .insert("unexpected".to_owned(), json!(true));
        let token = sign_values(
            &json!({"alg": "HS256", "kid": KEY_ID, "typ": "at+jwt"}),
            &unknown,
            SECRET,
        );
        assert_eq!(
            fixture.middleware.authenticate_public_mcp(
                &bearer(&token),
                NOW,
                [AuthScope::ProjectRead]
            ),
            Err(AuthError::MalformedToken)
        );

        let raw_claims = format!(
            "{{\"iss\":\"{ISSUER}\",\"iss\":\"{OTHER_ISSUER}\",\"sub\":\"oidc-user-42\",\"aud\":\"{RESOURCE}\",\"exp\":{},\"nbf\":{},\"iat\":{},\"jti\":\"duplicate-token\",\"scope\":\"project.read\",\"token_kind\":\"user\",\"tenant_id\":\"{}\",\"service_id\":null}}",
            NOW + 60,
            NOW,
            NOW,
            fixture.tenant.canonical()
        );
        let header = URL_SAFE_NO_PAD.encode(
            serde_json::to_vec(&json!({"alg": "HS256", "kid": KEY_ID, "typ": "at+jwt"}))
                .unwrap_or_else(|error| panic!("header fixture: {error}")),
        );
        let claims = URL_SAFE_NO_PAD.encode(raw_claims);
        let input = format!("{header}.{claims}");
        let mut signer = <HmacSha256 as hmac::KeyInit>::new_from_slice(SECRET)
            .unwrap_or_else(|error| panic!("duplicate signing fixture: {error}"));
        signer.update(input.as_bytes());
        let token = format!(
            "{input}.{}",
            URL_SAFE_NO_PAD.encode(signer.finalize().into_bytes())
        );
        assert_eq!(
            fixture.middleware.authenticate_public_mcp(
                &bearer(&token),
                NOW,
                [AuthScope::ProjectRead]
            ),
            Err(AuthError::MalformedToken)
        );

        let mut multi_audience = base;
        multi_audience
            .as_object_mut()
            .unwrap_or_else(|| panic!("claims object fixture"))
            .insert("aud".to_owned(), json!([RESOURCE, "https://other.example"]));
        let token = sign_values(
            &json!({"alg": "HS256", "kid": KEY_ID, "typ": "at+jwt"}),
            &multi_audience,
            SECRET,
        );
        assert_eq!(
            fixture.middleware.authenticate_public_mcp(
                &bearer(&token),
                NOW,
                [AuthScope::ProjectRead]
            ),
            Err(AuthError::MalformedToken)
        );
    }

    #[test]
    fn challenge_is_exact_and_requires_a_scope() {
        let fixture = fixture();
        let challenge = fixture
            .middleware
            .challenge([AuthScope::ProjectWrite, AuthScope::ProjectRead])
            .unwrap_or_else(|error| panic!("challenge fixture: {error}"));
        assert_eq!(challenge.resource_metadata(), METADATA);
        assert_eq!(
            challenge.www_authenticate(),
            concat!(
                "Bearer resource_metadata=\"https://mcp.hwpx-agent.example/",
                ".well-known/oauth-protected-resource\", ",
                "scope=\"project.read project.write\""
            )
        );
        assert_eq!(
            fixture.middleware.challenge([]),
            Err(AuthError::InvalidConfiguration)
        );
    }

    #[test]
    fn configuration_and_identity_inputs_are_bounded_and_canonical() {
        let limits = AuthRegistryLimits::product_maximums();
        assert!(AuthMiddleware::new("http://mcp.example", METADATA, 0, limits).is_err());
        assert!(
            AuthMiddleware::new(RESOURCE, "https://other.example/metadata", 0, limits).is_err()
        );
        assert!(
            AuthMiddleware::new(RESOURCE, METADATA, MAX_CLOCK_SKEW_SECONDS + 1, limits).is_err()
        );

        let mut middleware = AuthMiddleware::new(RESOURCE, METADATA, 0, limits)
            .unwrap_or_else(|error| panic!("configuration fixture: {error}"));
        assert!(
            middleware
                .register_local_hmac_key(ISSUER, "bad key", SECRET, 0, 1)
                .is_err()
        );
        assert!(
            middleware
                .register_local_hmac_key(ISSUER, KEY_ID, b"too-short", 0, 1)
                .is_err()
        );
        assert!(
            middleware
                .register_local_hmac_key(ISSUER, KEY_ID, SECRET, 1, 1)
                .is_err()
        );
        assert!(
            PrincipalGrant::new(
                tenant(1),
                TenantRole::Reader,
                [AuthScope::ProjectRead],
                1,
                1
            )
            .is_err()
        );
        assert!(
            PrincipalGrant::new(
                tenant(1),
                TenantRole::Reader,
                [AuthScope::ProjectWrite],
                0,
                1
            )
            .is_err()
        );
        assert!(
            PrincipalGrant::new(
                tenant(1),
                TenantRole::Worker,
                [AuthScope::RetentionManage],
                0,
                1
            )
            .is_err()
        );
        assert!(
            middleware
                .register_user(
                    ISSUER,
                    "",
                    grant(tenant(1), TenantRole::Reader, [AuthScope::ProjectRead])
                )
                .is_err()
        );
        assert!(
            middleware
                .register_user(
                    ISSUER,
                    "user",
                    grant(tenant(1), TenantRole::Worker, [AuthScope::ProjectRead])
                )
                .is_err()
        );
    }

    #[test]
    fn debug_output_never_contains_secrets_tokens_or_external_subjects() {
        let mut fixture = fixture();
        let token = sign(&user_claims(fixture.tenant), "at+jwt", KEY_ID, SECRET);
        let context = fixture
            .middleware
            .authenticate_public_mcp(&bearer(&token), NOW, [AuthScope::ProjectRead])
            .unwrap_or_else(|error| panic!("debug context fixture: {error}"));
        let debug = format!("{:?} {:?}", fixture.middleware, context);
        assert!(!debug.contains("oidc-user-42"));
        assert!(!debug.contains("worker-01"));
        assert!(!debug.contains(std::str::from_utf8(SECRET).unwrap_or_default()));
        assert!(!debug.contains(&token));
        assert!(!debug.contains(&fixture.tenant.canonical()));
        assert!(!debug.contains(&fixture.user_subject.hex()));
    }

    #[test]
    fn error_codes_are_stable_and_do_not_include_untrusted_values() {
        let cases = [
            (AuthError::TokenExpired, AuthErrorCode::TokenExpired),
            (AuthError::ScopeDenied, AuthErrorCode::ScopeDenied),
            (AuthError::TenantMismatch, AuthErrorCode::TenantMismatch),
            (AuthError::TokenReplay, AuthErrorCode::TokenReplay),
        ];
        for (error, code) in cases {
            assert_eq!(error.code(), code);
            assert!(!error.to_string().contains("oidc-user-42"));
            assert!(!error.to_string().contains(RESOURCE));
        }
    }
}
