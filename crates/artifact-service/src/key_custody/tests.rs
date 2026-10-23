use super::*;
use crate::{ArtifactKind,ContentDigest,EncryptionMetadata,MediaType,TenantId};
type R=Result<(),Box<dyn std::error::Error>>;
fn reference(name:&str)->Result<KeyReference,ArtifactError>{KeyReference::parse(name)}
fn blob(target:&str,key:&[u8;32])->Zeroizing<Vec<u8>>{
    let mut bytes=Zeroizing::new(Vec::with_capacity(BLOB_BYTES));bytes.extend_from_slice(MAGIC);
    bytes.extend_from_slice(&Sha256::digest(target.as_bytes()));bytes.extend_from_slice(key);bytes
}
fn public_tenant()->Result<TenantId,ArtifactError>{TenantId::new(uuid::Uuid::from_u128(461))}
const PAYLOAD:&[u8]=b"P09 public synthetic artifact custody probe";

#[test]
fn profiles_reject_path_control_unicode_and_oversize_locators()->R{
    for bad in["","a/b","a\\b","a:b","a b","a\n","한글","*"]{assert!(matches!(ArtifactCustodyProfile::parse(bad),Err(E::Profile)));}
    assert!(ArtifactCustodyProfile::parse("a".repeat(121)).is_err());assert!(ArtifactCustodyProfile::parse("a".repeat(120)).is_ok());Ok(())
}
#[test]
fn exact_targets_are_stable_and_separate_profile_purpose_and_reference()->R{
    let profile=ArtifactCustodyProfile::parse("owned.test")?;let other=ArtifactCustodyProfile::parse("owned.other")?;
    let key=reference("p09.aes")?;let old=reference("p09.aes-old")?;let purpose=ArtifactKeyPurpose::Aes256Gcm;
    let target=profile.credential_target(purpose,&key);assert_eq!(target,profile.credential_target(purpose,&key));
    assert_ne!(target,profile.credential_target(ArtifactKeyPurpose::DownloadHmacSha256,&key));
    assert_ne!(target,other.credential_target(purpose,&key));assert_ne!(target,profile.credential_target(purpose,&old));
    assert!(!target.contains("owned.test"));assert!(!target.starts_with("hwpx-agent.remote-sync"));Ok(())
}
#[test]
fn envelope_requires_exact_size_version_and_whole_target_binding()->R{
    let profile=ArtifactCustodyProfile::parse("owned.test")?;let key=reference("p09.aes")?;
    let target=profile.credential_target(ArtifactKeyPurpose::Aes256Gcm,&key);let secret=decode(&target,blob(&target,&[23;32]))?;
    assert!(secret[..]==[23;32]);let mut extra=blob(&target,&[23;32]);extra.push(0);assert!(matches!(decode(&target,extra),Err(E::Malformed)));
    let mut version=blob(&target,&[23;32]);version[7]=b'2';assert!(matches!(decode(&target,version),Err(E::Malformed)));
    assert!(matches!(decode(&target,Zeroizing::new(vec![0;31])),Err(E::Malformed)));
    let other=profile.credential_target(ArtifactKeyPurpose::DownloadHmacSha256,&key);
    assert!(matches!(decode(&other,blob(&target,&[23;32])),Err(E::Binding)));Ok(())
}
#[test]
fn invalid_key_sets_are_rejected_before_any_secret_read()->R{
    let active=reference("p09.active")?;let other=reference("p09.other")?;
    for keys in[vec![],vec![other],vec![active.clone(),active.clone()],(0..17).map(|n|reference(&format!("p09.k{n}"))).collect::<Result<Vec<_>,_>>()?]{
        let mut reads=0;let out=keyring(active.clone(),&keys,|_|{reads+=1;Ok(Zeroizing::new([1;32]))});
        assert!(matches!(out,Err(E::KeySet)));assert_eq!(reads,0);
    }Ok(())
}
#[test]
fn load_error_is_preserved_without_regeneration_or_partial_ring()->R{
    let old=reference("p09.old")?;let active=reference("p09.active")?;let keys=[old.clone(),active.clone()];let mut calls=vec![];
    let out=keyring(active,&keys,|key|{calls.push(key.clone());if key==&old{Ok(Zeroizing::new([2;32]))}else{Err(E::Missing)}});
    assert!(matches!(out,Err(E::Missing)));assert_eq!(calls,keys);Ok(())
}
#[test]
fn retained_old_key_decrypts_after_active_key_rotation()->R{
    let old=reference("p09.old")?;let active=reference("p09.active")?;let media=MediaType::parse("application/octet-stream")?;
    let original=keyring(old.clone(),std::slice::from_ref(&old),|_|Ok(Zeroizing::new([2;32])))?;
    let encrypted=original.encrypt(public_tenant()?,ContentDigest::of(PAYLOAD),PAYLOAD.len()as u64,&media,ArtifactKind::Result,PAYLOAD)?;
    let rotated=keyring(active.clone(),&[old.clone(),active.clone()],|key|Ok(Zeroizing::new(if key==&old{[2;32]}else{[3;32]})))?;
    assert!(rotated.decrypt(public_tenant()?,ContentDigest::of(PAYLOAD),PAYLOAD.len()as u64,&media,ArtifactKind::Result,&encrypted.metadata,&encrypted.ciphertext)?==PAYLOAD);
    let current=rotated.encrypt(public_tenant()?,ContentDigest::of(PAYLOAD),PAYLOAD.len()as u64,&media,ArtifactKind::Result,PAYLOAD)?;
    assert_eq!(current.metadata.key_ref,active);Ok(())
}
#[test]
fn missing_or_wrong_key_cannot_turn_old_ciphertext_into_success()->R{
    let old=reference("p09.old")?;let active=reference("p09.active")?;let media=MediaType::parse("application/octet-stream")?;
    let original=keyring(old.clone(),std::slice::from_ref(&old),|_|Ok(Zeroizing::new([2;32])))?;
    let encrypted=original.encrypt(public_tenant()?,ContentDigest::of(PAYLOAD),PAYLOAD.len()as u64,&media,ArtifactKind::Result,PAYLOAD)?;
    for bad in[keyring(active.clone(),std::slice::from_ref(&active),|_|Ok(Zeroizing::new([3;32])))?,
        keyring(old.clone(),std::slice::from_ref(&old),|_|Ok(Zeroizing::new([4;32])))?]{
        assert!(bad.decrypt(public_tenant()?,ContentDigest::of(PAYLOAD),PAYLOAD.len()as u64,&media,ArtifactKind::Result,&encrypted.metadata,&encrypted.ciphertext).is_err());
    }Ok(())
}
#[test]
fn debug_is_redacted_and_errors_never_embed_backend_values()->R{
    let profile=ArtifactCustodyProfile::parse("owned.private.profile")?;assert_eq!(format!("{profile:?}"),"ArtifactCustodyProfile(<redacted>)");
    for error in[E::Profile,E::KeySet,E::Missing,E::Unavailable,E::Malformed,E::Binding,E::Persistence]{assert!(error.to_string().starts_with("ARTIFACT_KEY_CUSTODY_"));}
    #[cfg(windows)]assert_eq!(format!("{:?}",WindowsArtifactKeyCustody::bind(profile)?),"WindowsArtifactKeyCustody(<redacted>; read_only_exact_targets)");Ok(())
}

#[cfg(windows)]mod windows;
