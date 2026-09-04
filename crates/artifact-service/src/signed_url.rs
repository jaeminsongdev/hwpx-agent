use std::fmt;

use base64::Engine as _;
use base64::engine::general_purpose::URL_SAFE_NO_PAD;
use hmac::{Hmac, Mac as _};
use sha2::Sha256;
use uuid::Uuid;

use crate::types::{
    ArtifactError, ArtifactId, ContentDigest, KeyReference, SignedDownloadUrl, SubjectDigest,
    TenantId,
};

const VERSION: &str = "1";
const OPERATION: &str = "download";
const MIN_SIGNING_KEY_BYTES: usize = 32;
const MAX_URL_BYTES: usize = 2_048;
const CLOCK_SKEW_SECONDS: u64 = 30;

type HmacSha256 = Hmac<Sha256>;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct DownloadClaims {
    pub tenant_id: TenantId,
    pub artifact_id: ArtifactId,
    pub subject_sha256: SubjectDigest,
    pub content_sha256: ContentDigest,
    pub acl_version: u64,
    pub issued_at_unix_seconds: u64,
    pub expires_at_unix_seconds: u64,
}

#[derive(Clone)]
pub struct DownloadSigner {
    base_url: String,
    key_id: KeyReference,
    prototype: HmacSha256,
    max_ttl_seconds: u64,
}

impl fmt::Debug for DownloadSigner {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("DownloadSigner")
            .field("base_url", &self.base_url)
            .field("key_id", &self.key_id)
            .field("signing_key", &"[REDACTED]")
            .field("max_ttl_seconds", &self.max_ttl_seconds)
            .finish_non_exhaustive()
    }
}

impl DownloadSigner {
    /// Creates an HTTPS-only signer with a bounded maximum token lifetime.
    ///
    /// # Errors
    ///
    /// Returns an error for an unsafe base URL, a weak key, an invalid key identifier or a TTL
    /// outside one through 300 seconds.
    pub fn new(
        base_url: impl Into<String>,
        key_id: KeyReference,
        signing_key: &[u8],
        max_ttl_seconds: u64,
    ) -> Result<Self, ArtifactError> {
        let base_url = base_url.into();
        if !valid_https_base_url(&base_url)
            || signing_key.len() < MIN_SIGNING_KEY_BYTES
            || !(1..=300).contains(&max_ttl_seconds)
        {
            return Err(ArtifactError::InvalidSignedUrl);
        }
        let prototype = <HmacSha256 as hmac::KeyInit>::new_from_slice(signing_key)
            .map_err(|_| ArtifactError::CryptoFailure)?;
        Ok(Self {
            base_url,
            key_id,
            prototype,
            max_ttl_seconds,
        })
    }

    /// Signs claims whose complete lifetime is already fixed by the caller.
    ///
    /// # Errors
    ///
    /// Returns an error when the ACL generation is zero, the lifetime is empty or it exceeds the
    /// configured maximum.
    pub fn issue(&self, claims: DownloadClaims) -> Result<SignedDownloadUrl, ArtifactError> {
        if claims.acl_version == 0
            || claims.expires_at_unix_seconds <= claims.issued_at_unix_seconds
            || claims.expires_at_unix_seconds - claims.issued_at_unix_seconds > self.max_ttl_seconds
        {
            return Err(ArtifactError::InvalidSignedUrlLifetime);
        }
        let canonical = canonical_query(&self.key_id, claims);
        let signature = self.sign(canonical.as_bytes());
        Ok(SignedDownloadUrl::new(format!(
            "{}?{}&sig={}",
            self.base_url,
            canonical,
            URL_SAFE_NO_PAD.encode(signature)
        )))
    }

    /// Verifies the signature, canonical encoding, operation binding and short lifetime.
    ///
    /// # Errors
    ///
    /// Returns an error when any field, signature, binding or time constraint is invalid.
    pub fn verify(
        &self,
        signed_url: &SignedDownloadUrl,
        now_unix_seconds: u64,
    ) -> Result<DownloadClaims, ArtifactError> {
        let raw = signed_url.expose();
        if raw.len() > MAX_URL_BYTES {
            return Err(ArtifactError::InvalidSignedUrl);
        }
        let prefix = format!("{}?", self.base_url);
        let query = raw
            .strip_prefix(&prefix)
            .ok_or(ArtifactError::InvalidSignedUrl)?;
        let pairs = query.split('&').collect::<Vec<_>>();
        if pairs.len() != 11 {
            return Err(ArtifactError::InvalidSignedUrl);
        }
        let expected_names = [
            "v", "kid", "tenant", "artifact", "subject", "content", "acl", "iat", "exp", "op",
        ];
        let mut values = Vec::with_capacity(expected_names.len());
        for (pair, expected_name) in pairs[..10].iter().zip(expected_names.iter()) {
            values.push(parse_pair(pair, expected_name)?);
        }
        if values[9] != OPERATION {
            return Err(ArtifactError::InvalidSignedUrl);
        }

        // Re-split once to avoid accepting duplicate or reordered fields.
        let (canonical, signature_pair) = query
            .rsplit_once("&sig=")
            .ok_or(ArtifactError::InvalidSignedUrl)?;
        let canonical_pairs = canonical.split('&').collect::<Vec<_>>();
        if canonical_pairs.len() != 10 || signature_pair.contains('&') {
            return Err(ArtifactError::InvalidSignedUrl);
        }
        let signature = URL_SAFE_NO_PAD
            .decode(signature_pair)
            .map_err(|_| ArtifactError::InvalidSignedUrl)?;
        if signature.len() != 32 {
            return Err(ArtifactError::InvalidSignedUrl);
        }
        let mut verifier = self.prototype.clone();
        verifier.update(canonical.as_bytes());
        verifier
            .verify_slice(&signature)
            .map_err(|_| ArtifactError::InvalidSignedUrl)?;

        if values[0] != VERSION || values[1] != self.key_id.as_str() {
            return Err(ArtifactError::InvalidSignedUrl);
        }
        let tenant_uuid =
            Uuid::parse_str(values[2]).map_err(|_| ArtifactError::InvalidSignedUrl)?;
        if tenant_uuid.simple().to_string() != values[2] {
            return Err(ArtifactError::InvalidSignedUrl);
        }
        let tenant_id = TenantId::new(tenant_uuid).map_err(|_| ArtifactError::InvalidSignedUrl)?;
        let artifact_id =
            ArtifactId::parse(values[3]).map_err(|_| ArtifactError::InvalidSignedUrl)?;
        let subject_sha256 =
            SubjectDigest::parse(values[4]).map_err(|_| ArtifactError::InvalidSignedUrl)?;
        let content_sha256 =
            ContentDigest::parse(values[5]).map_err(|_| ArtifactError::InvalidSignedUrl)?;
        let acl_version = parse_canonical_u64(values[6])?;
        let issued_at = parse_canonical_u64(values[7])?;
        let expires_at = parse_canonical_u64(values[8])?;
        if acl_version == 0
            || expires_at <= issued_at
            || expires_at - issued_at > self.max_ttl_seconds
            || now_unix_seconds > expires_at
            || issued_at > now_unix_seconds.saturating_add(CLOCK_SKEW_SECONDS)
        {
            return Err(ArtifactError::InvalidSignedUrlLifetime);
        }
        Ok(DownloadClaims {
            tenant_id,
            artifact_id,
            subject_sha256,
            content_sha256,
            acl_version,
            issued_at_unix_seconds: issued_at,
            expires_at_unix_seconds: expires_at,
        })
    }

    fn sign(&self, canonical: &[u8]) -> [u8; 32] {
        let mut signer = self.prototype.clone();
        signer.update(canonical);
        signer.finalize().into_bytes().into()
    }
}

fn canonical_query(key_id: &KeyReference, claims: DownloadClaims) -> String {
    format!(
        "v={VERSION}&kid={}&tenant={}&artifact={}&subject={}&content={}&acl={}&iat={}&exp={}&op={OPERATION}",
        key_id.as_str(),
        claims.tenant_id.canonical(),
        claims.artifact_id.public_id(),
        claims.subject_sha256.hex(),
        claims.content_sha256.hex(),
        claims.acl_version,
        claims.issued_at_unix_seconds,
        claims.expires_at_unix_seconds,
    )
}

fn parse_pair<'a>(pair: &'a str, expected_name: &str) -> Result<&'a str, ArtifactError> {
    let (name, value) = pair
        .split_once('=')
        .ok_or(ArtifactError::InvalidSignedUrl)?;
    if name != expected_name || value.is_empty() || value.contains('=') {
        return Err(ArtifactError::InvalidSignedUrl);
    }
    Ok(value)
}

fn parse_canonical_u64(value: &str) -> Result<u64, ArtifactError> {
    let parsed = value
        .parse::<u64>()
        .map_err(|_| ArtifactError::InvalidSignedUrl)?;
    if parsed.to_string() != value {
        return Err(ArtifactError::InvalidSignedUrl);
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
        && host
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'-'))
        && port
            .is_none_or(|port| !port.is_empty() && port.bytes().all(|byte| byte.is_ascii_digit()))
        && path.bytes().all(|byte| {
            byte.is_ascii_alphanumeric() || matches!(byte, b'/' | b'.' | b'_' | b'~' | b'-')
        })
}

#[cfg(test)]
mod tests {
    use super::{DownloadClaims, DownloadSigner};
    use crate::types::{
        ArtifactError, ArtifactId, ContentDigest, KeyReference, SignedDownloadUrl, SubjectDigest,
        TenantId,
    };
    use uuid::Uuid;

    fn signer() -> DownloadSigner {
        DownloadSigner::new(
            "https://artifacts.example.test/v1/download",
            KeyReference::parse("hmac.download-v1")
                .unwrap_or_else(|error| panic!("key id: {error}")),
            &[23_u8; 32],
            300,
        )
        .unwrap_or_else(|error| panic!("signer: {error}"))
    }

    fn claims() -> DownloadClaims {
        DownloadClaims {
            tenant_id: TenantId::new(Uuid::new_v4())
                .unwrap_or_else(|error| panic!("tenant: {error}")),
            artifact_id: ArtifactId::generate(),
            subject_sha256: SubjectDigest::from_authenticated_subject("oidc:user:1")
                .unwrap_or_else(|error| panic!("subject: {error}")),
            content_sha256: ContentDigest::of(b"payload"),
            acl_version: 7,
            issued_at_unix_seconds: 1_000,
            expires_at_unix_seconds: 1_060,
        }
    }

    #[test]
    fn signs_and_verifies_all_security_bindings() {
        let signer = signer();
        let claims = claims();
        let url = signer
            .issue(claims)
            .unwrap_or_else(|error| panic!("issue: {error}"));
        let verified = signer
            .verify(&url, 1_030)
            .unwrap_or_else(|error| panic!("verify: {error}"));
        assert_eq!(verified.tenant_id, claims.tenant_id);
        assert_eq!(verified.artifact_id, claims.artifact_id);
        assert_eq!(verified.subject_sha256, claims.subject_sha256);
        assert_eq!(verified.content_sha256, claims.content_sha256);
        assert_eq!(verified.acl_version, claims.acl_version);
        assert_eq!(verified.expires_at_unix_seconds, 1_060);
        assert!(!format!("{url:?}").contains("sig="));
    }

    #[test]
    fn rejects_tampering_expiry_reordering_and_wrong_key() {
        let signer = signer();
        let url = signer
            .issue(claims())
            .unwrap_or_else(|error| panic!("issue: {error}"));
        assert!(matches!(
            signer.verify(&url, 1_061),
            Err(ArtifactError::InvalidSignedUrlLifetime)
        ));

        let tampered = SignedDownloadUrl::new(url.expose().replace("op=download", "op=upload"));
        assert!(matches!(
            signer.verify(&tampered, 1_001),
            Err(ArtifactError::InvalidSignedUrl)
        ));

        let reordered = SignedDownloadUrl::new(url.expose().replace("v=1&kid=", "kid=x&v=1&kid="));
        assert!(signer.verify(&reordered, 1_001).is_err());

        let other = DownloadSigner::new(
            "https://artifacts.example.test/v1/download",
            KeyReference::parse("hmac.download-v1")
                .unwrap_or_else(|error| panic!("key id: {error}")),
            &[24_u8; 32],
            300,
        )
        .unwrap_or_else(|error| panic!("other signer: {error}"));
        assert!(matches!(
            other.verify(&url, 1_001),
            Err(ArtifactError::InvalidSignedUrl)
        ));
    }

    #[test]
    fn rejects_weak_configuration_and_noncanonical_lifetimes() {
        let key_id = KeyReference::parse("hmac.download-v1")
            .unwrap_or_else(|error| panic!("key id: {error}"));
        assert!(
            DownloadSigner::new("http://example.test/a", key_id.clone(), &[1_u8; 32], 60).is_err()
        );
        assert!(
            DownloadSigner::new(
                "https://user@example.test/a",
                key_id.clone(),
                &[1_u8; 32],
                60
            )
            .is_err()
        );
        assert!(
            DownloadSigner::new(
                "https://example.test/a?x=1",
                key_id.clone(),
                &[1_u8; 32],
                60
            )
            .is_err()
        );
        assert!(
            DownloadSigner::new("https://example.test/a", key_id.clone(), &[1_u8; 16], 60).is_err()
        );
        assert!(DownloadSigner::new("https://example.test/a", key_id, &[1_u8; 32], 301).is_err());
        assert!(matches!(
            signer().issue(DownloadClaims {
                expires_at_unix_seconds: 1_000,
                ..claims()
            }),
            Err(ArtifactError::InvalidSignedUrlLifetime)
        ));
    }
}
