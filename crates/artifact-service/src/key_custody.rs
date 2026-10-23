//! Read-only artifact key custody. No token/bearer store reuse, enumeration, creation,
//! overwrite, deletion, environment/file fallback or automatic key regeneration.
//! A loaded crypto object is not a current authorization/key-revocation lease.
use std::fmt;
#[cfg(any(windows,test))]use std::collections::BTreeSet;
use sha2::{Digest as _,Sha256};
use thiserror::Error;
#[cfg(any(windows,test))]use zeroize::Zeroizing;
use crate::{ArtifactError,KeyReference};
#[cfg(any(windows,test))]use crate::Aes256GcmKeyring;

#[cfg(any(windows,test))]const MAGIC:&[u8;8]=b"HWPXKEY1";
#[cfg(any(windows,test))]const BLOB_BYTES:usize=8+32+32;
#[cfg(any(windows,test))]const MAX_KEYS:usize=16;

#[derive(Clone,Copy,Debug,Eq,PartialEq)]
pub enum ArtifactKeyPurpose{Aes256Gcm,DownloadHmacSha256}
impl ArtifactKeyPurpose{
    fn tag(self)->&'static str{match self{Self::Aes256Gcm=>"aes256-gcm",Self::DownloadHmacSha256=>"download-hmac-sha256"}}
}

#[derive(Clone,Eq,PartialEq)]
pub struct ArtifactCustodyProfile(String);
impl ArtifactCustodyProfile{
    /// # Errors
    /// Trusted launcher configuration only: bounded ASCII locator, never public request text.
    pub fn parse(profile:impl Into<String>)->Result<Self,ArtifactKeyCustodyError>{
        let profile=profile.into();
        if profile.is_empty()||profile.len()>120||!profile.bytes().all(|b|b.is_ascii_alphanumeric()||matches!(b,b'.'|b'_'|b'-')){
            return Err(ArtifactKeyCustodyError::Profile);}
        Ok(Self(profile))
    }
    /// Exact non-secret installer locator. This does not access the credential store.
    #[must_use]
    pub fn credential_target(&self,purpose:ArtifactKeyPurpose,reference:&KeyReference)->String{
        let mut hash=Sha256::new();
        // 길이와 용도를 각각 결속해 구분자 모호성과 다른 용도 키의 재사용을 막는다.
        for field in [b"hwpx-agent.artifact-custody/v1".as_slice(),self.0.as_bytes(),purpose.tag().as_bytes(),reference.as_str().as_bytes()]{
            hash.update((field.len()as u64).to_be_bytes());hash.update(field);
        }
        format!("hwpx-agent.artifact-custody.v1:{}:{}",purpose.tag(),hex::encode(hash.finalize()))
    }
}
impl fmt::Debug for ArtifactCustodyProfile{
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("ArtifactCustodyProfile(<redacted>)")}
}

#[derive(Clone,Debug,Eq,Error,PartialEq)]
pub enum ArtifactKeyCustodyError{
    #[error("ARTIFACT_KEY_CUSTODY_PROFILE_REJECTED")]Profile,
    #[error("ARTIFACT_KEY_CUSTODY_KEY_SET_REJECTED")]KeySet,
    #[error("ARTIFACT_KEY_CUSTODY_MISSING")]Missing,
    #[error("ARTIFACT_KEY_CUSTODY_UNAVAILABLE")]Unavailable,
    #[error("ARTIFACT_KEY_CUSTODY_MALFORMED")]Malformed,
    #[error("ARTIFACT_KEY_CUSTODY_BINDING_REJECTED")]Binding,
    #[error("ARTIFACT_KEY_CUSTODY_PERSISTENCE_REJECTED")]Persistence,
    #[error("ARTIFACT_KEY_CUSTODY_CRYPTO_REJECTED")]Crypto(#[from]ArtifactError),
}
type E=ArtifactKeyCustodyError;

#[cfg(any(windows,test))]
fn decode(target:&str,blob:Zeroizing<Vec<u8>>)->Result<Zeroizing<[u8;32]>,E>{
    if blob.len()!=BLOB_BYTES||&blob[..8]!=MAGIC{return Err(E::Malformed);}
    if blob[8..40]!=Sha256::digest(target.as_bytes())[..]{return Err(E::Binding);}
    let mut secret=Zeroizing::new([0;32]);secret.copy_from_slice(&blob[40..]);Ok(secret)
}

#[cfg(any(windows,test))]
fn keyring(active:KeyReference,references:&[KeyReference],mut load:impl FnMut(&KeyReference)->Result<Zeroizing<[u8;32]>,E>)
    ->Result<Aes256GcmKeyring,E>{
    // 전체 참조를 먼저 검증한다. 잘못된 집합이면 OS 저장소에 접근하지 않는다.
    if references.is_empty()||references.len()>MAX_KEYS||!references.contains(&active)
        ||references.iter().collect::<BTreeSet<_>>().len()!=references.len(){return Err(E::KeySet);}
    let mut loaded=Vec::with_capacity(references.len());
    for reference in references{loaded.push((reference.clone(),load(reference)?));}
    // 미소비/실패 경로의 비밀도 Zeroizing으로 정리한다. 원 constructor도 받은 copy를 즉시 지운다.
    Ok(Aes256GcmKeyring::new(active,loaded.into_iter().map(|(reference,key)|(reference,*key)))?)
}

#[cfg(windows)]mod windows;
#[cfg(windows)]pub use windows::WindowsArtifactKeyCustody;
#[cfg(test)]mod tests;
