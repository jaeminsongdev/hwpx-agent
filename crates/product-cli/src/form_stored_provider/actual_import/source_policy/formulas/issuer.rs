//! Mandatory signed formula DATA approval component; no production issuer/config or execution claim.
pub mod product;
pub mod registry;
mod provider;
mod wire;

use super::super::{PolicyReadScope, SourcePolicyVersion};
use super::registration::FormulaPolicyRegistrationRecord;
use artifact_service::{ArtifactId, ContentDigest, TenantId};
use revision_service::ProjectId;
use serde::Serialize;
use std::{
    collections::BTreeMap,
    fmt,
    time::{SystemTime, UNIX_EPOCH},
};
use thiserror::Error;

pub const FORMULA_APPROVAL_MEDIA_TYPE: &str =
    "application/vnd.hwpx-agent.source-formula-approval+json";
const APPROVAL_SCHEMA: &str = "hwpx-agent.source-formula-approval/v1";
const CLAIMS_SCHEMA: &str = "hwpx-agent.source-formula-approval-claims/v1";
const AUDIENCE: &str = "hwpx-agent.source-table-formula-policy";
const OPERATION: &str = "recalculate_table_formulas";
const DOMAIN: &[u8] = b"hwpx-agent.source-formula-approval/ed25519-v1\0";
const MAX_APPROVAL_BYTES: usize = 16384;
const MAX_CLAIMS_BYTES: usize = 8192;
const MAX_LIFETIME: u64 = 86400;

#[derive(Clone, Eq, PartialEq)]
pub struct FormulaIssuerKey {
    key_id: String,
    public_key: [u8; 32],
}
impl FormulaIssuerKey {
    /// # Errors
    /// Rejects malformed key IDs and zero keys. This does not install or trust a key.
    pub fn new(key_id: String, public_key: [u8; 32]) -> Result<Self, FormulaIssuerError> {
        if !identifier(&key_id) || public_key == [0; 32] {
            return Err(FormulaIssuerError::Trust);
        }
        Ok(Self { key_id, public_key })
    }
}
impl fmt::Debug for FormulaIssuerKey {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("FormulaIssuerKey(<redacted>)")
    }
}
/// Explicit trusted server input only. No JSON/default/root trust discovery or credentials.
pub struct FormulaIssuerTrustDraft {
    pub tenant: TenantId,
    pub project: ProjectId,
    pub issuer: String,
    pub generation: u64,
    pub valid_from: u64,
    pub valid_until: u64,
    pub max_approval_lifetime: u64,
    pub active_keys: Vec<FormulaIssuerKey>,
}
impl fmt::Debug for FormulaIssuerTrustDraft {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("FormulaIssuerTrustDraft(<redacted>)")
    }
}
#[derive(Clone, Eq, PartialEq)]
pub struct FormulaIssuerTrust {
    tenant: TenantId,
    project: ProjectId,
    issuer: String,
    generation: u64,
    valid_from: u64,
    valid_until: u64,
    max_approval_lifetime: u64,
    keys: BTreeMap<String, [u8; 32]>,
}
impl FormulaIssuerTrust {
    /// # Errors
    /// Rejects empty/duplicate keys, invalid generations, issuer or lifetime bounds. Not authority by serde.
    pub fn new(d: FormulaIssuerTrustDraft) -> Result<Self, FormulaIssuerError> {
        if !identifier(&d.issuer)
            || d.generation == 0
            || d.generation > i64::MAX as u64
            || d.valid_until <= d.valid_from
            || d.max_approval_lifetime == 0
            || d.max_approval_lifetime > MAX_LIFETIME
            || d.active_keys.is_empty()
            || d.active_keys.len() > 8
        {
            return Err(FormulaIssuerError::Trust);
        }
        let mut keys = BTreeMap::new();
        for k in d.active_keys {
            if keys.insert(k.key_id, k.public_key).is_some() {
                return Err(FormulaIssuerError::Trust);
            }
        }
        Ok(Self {
            tenant: d.tenant,
            project: d.project,
            issuer: d.issuer,
            generation: d.generation,
            valid_from: d.valid_from,
            valid_until: d.valid_until,
            max_approval_lifetime: d.max_approval_lifetime,
            keys,
        })
    }
}
impl fmt::Debug for FormulaIssuerTrust {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("FormulaIssuerTrust(<redacted>)")
    }
}
/// Repository-selected latest attestation, not a public artifact selector or an approval flag.
#[derive(Clone, Eq, PartialEq)]
pub struct FormulaApprovalVersion {
    pub artifact: ArtifactId,
    pub digest: ContentDigest,
}
impl fmt::Debug for FormulaApprovalVersion {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("FormulaApprovalVersion(<redacted>)")
    }
}
/// Authorizes current membership, policy identity/latest/revocation and approval access on every call.
pub trait FormulaApprovalRepository: Send + Sync {
    /// # Errors
    /// Missing/revoked/stale/unauthorized proof must deny; never fall back to an old approval.
    fn read_current_approval(
        &self,
        scope: &PolicyReadScope,
        policy: &SourcePolicyVersion,
    ) -> Result<FormulaApprovalVersion, FormulaIssuerError>;
}
/// Trusted server custody/config boundary. Each read must authorize membership and return current active keys.
pub trait FormulaIssuerTrustRepository: Send + Sync {
    /// # Errors
    /// Denies unavailable/revoked/unauthorized roots; never use an embedded or caller-provided fallback key.
    fn read_formula_issuer_trust(
        &self,
        scope: &PolicyReadScope,
    ) -> Result<FormulaIssuerTrust, FormulaIssuerError>;
}
pub trait FormulaIssuerClock: Send + Sync {
    /// # Errors
    /// Fails closed if trusted server time is unavailable. No caller request timestamp.
    fn now(&self) -> Result<u64, FormulaIssuerError>;
}
#[derive(Debug)]
pub struct SystemFormulaIssuerClock;
impl FormulaIssuerClock for SystemFormulaIssuerClock {
    fn now(&self) -> Result<u64, FormulaIssuerError> {
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_secs())
            .map_err(|_| FormulaIssuerError::Clock)
    }
}
/// Server issuer identity/time input; no policy target, source/artifact selector or private signing key.
pub struct FormulaApprovalIdentity {
    pub issuer: String,
    pub key_id: String,
    pub trust_generation: u64,
    pub issued_at: u64,
    pub not_before: u64,
    pub expires_at: u64,
}
impl fmt::Debug for FormulaApprovalIdentity {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("FormulaApprovalIdentity(<redacted>)")
    }
}
/// Signing input can only originate from a private P118 validated generated registration record.
pub struct PreparedFormulaApproval {
    claims: wire::Claims,
}
impl fmt::Debug for PreparedFormulaApproval {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PreparedFormulaApproval(<redacted>)")
    }
}
impl PreparedFormulaApproval {
    /// # Errors
    /// Rejects malformed issuer/key, generations, unsafe lifetime or a changed generated record.
    pub fn from_registration_record(
        record: &FormulaPolicyRegistrationRecord,
        identity: FormulaApprovalIdentity,
    ) -> Result<Self, FormulaIssuerError> {
        if !identifier(&identity.issuer)
            || !identifier(&identity.key_id)
            || identity.trust_generation == 0
            || identity.trust_generation > i64::MAX as u64
            || identity.issued_at > identity.not_before
            || identity.expires_at <= identity.not_before
            || identity.expires_at.saturating_sub(identity.issued_at) > MAX_LIFETIME
            || record.expected_generation() >= i64::MAX as u64
            || record.version().binding.policy_generation != record.expected_generation() + 1
        {
            return Err(FormulaIssuerError::Payload);
        }
        let v = record.version();
        Ok(Self {
            claims: wire::Claims {
                schema_version: CLAIMS_SCHEMA.into(),
                issuer: identity.issuer,
                key_id: identity.key_id,
                audience: AUDIENCE.into(),
                operation: OPERATION.into(),
                trust_generation: identity.trust_generation,
                binding: v.binding.clone(),
                policy_artifact: v.artifact,
                policy_digest: v.digest,
                issued_at: identity.issued_at,
                not_before: identity.not_before,
                expires_at: identity.expires_at,
            },
        })
    }
    /// Returns bounded domain-separated Ed25519 signing bytes; do not log or publish this private input.
    /// # Errors
    /// Rejects serialization/size errors. This function does not sign or create approval authority.
    pub fn signing_bytes(&self) -> Result<Vec<u8>, FormulaIssuerError> {
        let raw = wire::encode_claims(&self.claims)?;
        Ok(wire::signing_bytes(&raw))
    }
    /// Internal pre-sign admission under current server trust, not an authorization endpoint.
    pub(super) fn validate_for_issuance(
        &self,
        scope: &PolicyReadScope,
        policy: &SourcePolicyVersion,
        trust: &FormulaIssuerTrust,
        now: u64,
    ) -> Result<(), FormulaIssuerError> {
        provider::validate_claims(scope, policy, trust, &self.claims, now)?;
        if !trust.keys.contains_key(&self.claims.key_id) {
            return Err(FormulaIssuerError::Trust);
        }
        Ok(())
    }
    /// Wraps externally produced signature bytes. The consumer still MUST verify it against live server trust.
    /// # Errors
    /// Rejects serialization/size errors; a returned envelope is not a verified grant.
    pub fn envelope(&self, signature: [u8; 64]) -> Result<Vec<u8>, FormulaIssuerError> {
        wire::encode_envelope(&self.claims, signature)
    }
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct FormulaIssuerReceipt {
    pub profile: &'static str,
    pub approval_sha256: ContentDigest,
    pub policy_sha256: ContentDigest,
    pub trust_snapshot_sha256: ContentDigest,
    pub trust_generation: u64,
    pub policy_generation: u64,
    pub qualification: &'static str,
}
fn identifier(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 64
        && value
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b"._-".contains(&b))
}
#[derive(Debug, Error, Eq, PartialEq)]
pub enum FormulaIssuerError {
    #[error("formula_issuer_repository_denied")]
    Repository,
    #[error("formula_issuer_live_trust_denied")]
    Trust,
    #[error("formula_issuer_approval_artifact_denied")]
    Artifact,
    #[error("formula_issuer_strict_approval_payload_invalid")]
    Payload,
    #[error("formula_issuer_ed25519_signature_rejected")]
    Signature,
    #[error("formula_issuer_exact_policy_binding_rejected")]
    Binding,
    #[error("formula_issuer_approval_expired_or_not_yet_valid")]
    Time,
    #[error("formula_issuer_live_clock_unavailable_or_moved_backwards")]
    Clock,
    #[error("formula_issuer_live_state_changed")]
    Drift,
}
