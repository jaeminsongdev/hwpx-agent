use std::collections::BTreeMap;
use std::fmt;

use aes_gcm::aead::{Aead as _, KeyInit as _, Payload};
use aes_gcm::{Aes256Gcm, Nonce};
use serde::Serialize;
use zeroize::Zeroize as _;

use crate::types::{ArtifactError, ArtifactKind, ContentDigest, KeyReference, MediaType, TenantId};

const AES_256_KEY_BYTES: usize = 32;
const GCM_NONCE_BYTES: usize = 12;
const AES_GCM_ALGORITHM: &str = "AES-256-GCM";

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct EncryptionMetadata {
    pub algorithm: &'static str,
    pub key_ref: KeyReference,
    pub nonce: [u8; GCM_NONCE_BYTES],
    pub aad_sha256: ContentDigest,
    pub ciphertext_sha256: ContentDigest,
}

impl fmt::Debug for EncryptionMetadata {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("EncryptionMetadata")
            .field("algorithm", &self.algorithm)
            .field("key_ref", &self.key_ref)
            .field("nonce", &"[REDACTED]")
            .field("aad_sha256", &self.aad_sha256)
            .field("ciphertext_sha256", &self.ciphertext_sha256)
            .finish()
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct EncryptedArtifact {
    pub metadata: EncryptionMetadata,
    pub ciphertext: Vec<u8>,
}

pub struct Aes256GcmKeyring {
    active_key_ref: KeyReference,
    ciphers: BTreeMap<KeyReference, Aes256Gcm>,
}

impl fmt::Debug for Aes256GcmKeyring {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("Aes256GcmKeyring")
            .field("active_key_ref", &self.active_key_ref)
            .field("key_count", &self.ciphers.len())
            .finish_non_exhaustive()
    }
}

impl Aes256GcmKeyring {
    /// Creates a keyring and selects one active AES-256-GCM key reference.
    ///
    /// # Errors
    ///
    /// Returns an error for duplicate references, invalid key material or a missing active key.
    pub fn new(
        active_key_ref: KeyReference,
        keys: impl IntoIterator<Item = (KeyReference, [u8; AES_256_KEY_BYTES])>,
    ) -> Result<Self, ArtifactError> {
        let mut ciphers = BTreeMap::new();
        for (key_ref, mut key_bytes) in keys {
            let cipher = Aes256Gcm::new_from_slice(&key_bytes);
            key_bytes.zeroize();
            let cipher = cipher.map_err(|_| ArtifactError::CryptoFailure)?;
            if ciphers.insert(key_ref, cipher).is_some() {
                return Err(ArtifactError::Conflict);
            }
        }
        if !ciphers.contains_key(&active_key_ref) {
            return Err(ArtifactError::InvalidKeyReference);
        }
        Ok(Self {
            active_key_ref,
            ciphers,
        })
    }

    pub(crate) fn encrypt(
        &self,
        tenant_id: TenantId,
        digest: ContentDigest,
        declared_size: u64,
        media_type: &MediaType,
        kind: ArtifactKind,
        plaintext: &[u8],
    ) -> Result<EncryptedArtifact, ArtifactError> {
        if u64::try_from(plaintext.len()).map_err(|_| ArtifactError::PayloadTooLarge {
            limit_bytes: u64::MAX,
        })? != declared_size
            || ContentDigest::of(plaintext) != digest
        {
            return Err(ArtifactError::IntegrityMismatch);
        }

        let cipher = self
            .ciphers
            .get(&self.active_key_ref)
            .ok_or(ArtifactError::CryptoFailure)?;
        let aad = build_aad(
            tenant_id,
            digest,
            declared_size,
            media_type,
            kind,
            &self.active_key_ref,
        );
        let mut nonce_bytes = [0_u8; GCM_NONCE_BYTES];
        getrandom::fill(&mut nonce_bytes).map_err(|_| ArtifactError::CryptoFailure)?;
        let nonce = Nonce::from(nonce_bytes);
        let ciphertext = cipher
            .encrypt(
                &nonce,
                Payload {
                    msg: plaintext,
                    aad: &aad,
                },
            )
            .map_err(|_| ArtifactError::CryptoFailure)?;
        let metadata = EncryptionMetadata {
            algorithm: AES_GCM_ALGORITHM,
            key_ref: self.active_key_ref.clone(),
            nonce: nonce_bytes,
            aad_sha256: ContentDigest::of(&aad),
            ciphertext_sha256: ContentDigest::of(&ciphertext),
        };
        Ok(EncryptedArtifact {
            metadata,
            ciphertext,
        })
    }

    // Each argument is an independently revalidated AEAD binding from immutable metadata.
    #[allow(clippy::too_many_arguments)]
    pub(crate) fn decrypt(
        &self,
        tenant_id: TenantId,
        digest: ContentDigest,
        declared_size: u64,
        media_type: &MediaType,
        kind: ArtifactKind,
        metadata: &EncryptionMetadata,
        ciphertext: &[u8],
    ) -> Result<Vec<u8>, ArtifactError> {
        if metadata.algorithm != AES_GCM_ALGORITHM
            || ContentDigest::of(ciphertext) != metadata.ciphertext_sha256
        {
            return Err(ArtifactError::IntegrityMismatch);
        }
        let aad = build_aad(
            tenant_id,
            digest,
            declared_size,
            media_type,
            kind,
            &metadata.key_ref,
        );
        if ContentDigest::of(&aad) != metadata.aad_sha256 {
            return Err(ArtifactError::IntegrityMismatch);
        }
        let cipher = self
            .ciphers
            .get(&metadata.key_ref)
            .ok_or(ArtifactError::CryptoFailure)?;
        let nonce = Nonce::from(metadata.nonce);
        let plaintext = cipher
            .decrypt(
                &nonce,
                Payload {
                    msg: ciphertext,
                    aad: &aad,
                },
            )
            .map_err(|_| ArtifactError::CryptoFailure)?;
        if u64::try_from(plaintext.len()).map_err(|_| ArtifactError::IntegrityMismatch)?
            != declared_size
            || ContentDigest::of(&plaintext) != digest
        {
            return Err(ArtifactError::IntegrityMismatch);
        }
        Ok(plaintext)
    }
}

fn build_aad(
    tenant_id: TenantId,
    digest: ContentDigest,
    size: u64,
    media_type: &MediaType,
    kind: ArtifactKind,
    key_ref: &KeyReference,
) -> Vec<u8> {
    let mut aad = Vec::with_capacity(192);
    append_field(&mut aad, b"hwpx-agent.artifact-encryption/v1");
    append_field(&mut aad, tenant_id.as_uuid().as_bytes());
    append_field(&mut aad, digest.as_bytes());
    append_field(&mut aad, &size.to_be_bytes());
    append_field(&mut aad, media_type.as_str().as_bytes());
    append_field(&mut aad, kind.as_str().as_bytes());
    append_field(&mut aad, key_ref.as_str().as_bytes());
    aad
}

fn append_field(target: &mut Vec<u8>, field: &[u8]) {
    let length = u32::try_from(field.len()).unwrap_or(u32::MAX);
    target.extend_from_slice(&length.to_be_bytes());
    target.extend_from_slice(field);
}

#[cfg(test)]
mod tests {
    use super::Aes256GcmKeyring;
    use crate::types::{
        ArtifactError, ArtifactKind, ContentDigest, KeyReference, MediaType, TenantId,
    };
    use uuid::Uuid;

    fn fixture_keyring() -> Aes256GcmKeyring {
        let key_ref = KeyReference::parse("kms.artifact-v1")
            .unwrap_or_else(|error| panic!("key ref: {error}"));
        Aes256GcmKeyring::new(key_ref.clone(), [(key_ref, [7_u8; 32])])
            .unwrap_or_else(|error| panic!("keyring: {error}"))
    }

    #[test]
    fn encrypts_with_random_nonce_and_verifies_round_trip() {
        let keyring = fixture_keyring();
        let tenant =
            TenantId::new(Uuid::new_v4()).unwrap_or_else(|error| panic!("tenant: {error}"));
        let media = MediaType::parse("application/vnd.hancom.hwpx+zip")
            .unwrap_or_else(|error| panic!("media: {error}"));
        let plaintext = b"private hwpx bytes";
        let digest = ContentDigest::of(plaintext);
        let size = u64::try_from(plaintext.len()).unwrap_or(u64::MAX);

        let first = keyring
            .encrypt(
                tenant,
                digest,
                size,
                &media,
                ArtifactKind::Source,
                plaintext,
            )
            .unwrap_or_else(|error| panic!("first encrypt: {error}"));
        let second = keyring
            .encrypt(
                tenant,
                digest,
                size,
                &media,
                ArtifactKind::Source,
                plaintext,
            )
            .unwrap_or_else(|error| panic!("second encrypt: {error}"));
        assert_ne!(first.metadata.nonce, second.metadata.nonce);
        assert_ne!(first.ciphertext, second.ciphertext);
        assert!(
            !first
                .ciphertext
                .windows(plaintext.len())
                .any(|window| window == plaintext)
        );

        let recovered = keyring
            .decrypt(
                tenant,
                digest,
                size,
                &media,
                ArtifactKind::Source,
                &first.metadata,
                &first.ciphertext,
            )
            .unwrap_or_else(|error| panic!("decrypt: {error}"));
        assert_eq!(recovered, plaintext);
    }

    #[test]
    fn fails_closed_on_ciphertext_aad_or_key_tampering() {
        let keyring = fixture_keyring();
        let tenant =
            TenantId::new(Uuid::new_v4()).unwrap_or_else(|error| panic!("tenant: {error}"));
        let other_tenant =
            TenantId::new(Uuid::new_v4()).unwrap_or_else(|error| panic!("other tenant: {error}"));
        let media =
            MediaType::parse("application/pdf").unwrap_or_else(|error| panic!("media: {error}"));
        let plaintext = b"payload";
        let digest = ContentDigest::of(plaintext);
        let encrypted = keyring
            .encrypt(tenant, digest, 7, &media, ArtifactKind::Result, plaintext)
            .unwrap_or_else(|error| panic!("encrypt: {error}"));

        let mut tampered = encrypted.ciphertext.clone();
        tampered[0] ^= 1;
        assert!(matches!(
            keyring.decrypt(
                tenant,
                digest,
                7,
                &media,
                ArtifactKind::Result,
                &encrypted.metadata,
                &tampered,
            ),
            Err(ArtifactError::IntegrityMismatch)
        ));
        assert!(
            keyring
                .decrypt(
                    other_tenant,
                    digest,
                    7,
                    &media,
                    ArtifactKind::Result,
                    &encrypted.metadata,
                    &encrypted.ciphertext,
                )
                .is_err()
        );

        let missing_keyring = Aes256GcmKeyring::new(
            KeyReference::parse("kms.other-v1").unwrap_or_else(|error| panic!("key ref: {error}")),
            [(
                KeyReference::parse("kms.other-v1")
                    .unwrap_or_else(|error| panic!("key ref: {error}")),
                [8_u8; 32],
            )],
        )
        .unwrap_or_else(|error| panic!("keyring: {error}"));
        assert!(matches!(
            missing_keyring.decrypt(
                tenant,
                digest,
                7,
                &media,
                ArtifactKind::Result,
                &encrypted.metadata,
                &encrypted.ciphertext,
            ),
            Err(ArtifactError::CryptoFailure)
        ));
    }
}
