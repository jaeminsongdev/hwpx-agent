// The guarded runner supplies a unique nonce and verifies cleanup independently.
// Only these exact three fresh synthetic entries may be written/deleted by this TEST module.
use super::*;
use std::{collections::HashMap,io::{Read as _,Write as _},process::{Command,Stdio},time::{Duration,Instant}};
use keyring_core::api::CredentialStoreApi;
use serde::Deserialize;
use crate::{ArtifactId,DownloadClaims,SignedDownloadUrl,SubjectDigest};
const NONCE_ENV:&str="P09_OWNED_ARTIFACT_CUSTODY_NONCE";
const BASE_URL:&str="https://fixture.example.test/p09-custody";
const REFS:[&str;3]=["p09.aes-old","p09.aes-current","p09.download"];

fn fixture_profile()->Result<ArtifactCustodyProfile,Box<dyn std::error::Error>>{
    let nonce=std::env::var(NONCE_ENV).map_err(|_|"guarded credential fixture nonce required")?;
    let uuid=uuid::Uuid::parse_str(&nonce).map_err(|_|"fixture nonce rejected")?;
    if uuid.get_version_num()!=4||uuid.simple().to_string()!=nonce{return Err("fixture nonce rejected".into());}
    Ok(ArtifactCustodyProfile::parse(format!("p09-owned-custody-{nonce}"))?)
}
fn claims()->Result<DownloadClaims,ArtifactError>{Ok(DownloadClaims{tenant_id:public_tenant()?,artifact_id:ArtifactId::generate(),
    subject_sha256:SubjectDigest::from_authenticated_subject("p09 public custody probe")?,content_sha256:ContentDigest::of(PAYLOAD),
    acl_version:1,issued_at_unix_seconds:100,expires_at_unix_seconds:120})}
struct Cleanup{entries:Vec<keyring_core::Entry>,armed:bool}
impl Cleanup{
    fn close(&mut self)->R{
        for entry in &self.entries{
            match entry.delete_credential(){Ok(())|Err(keyring_core::Error::NoEntry)=>{},Err(_)=>return Err("owned credential cleanup unavailable".into())}
            if !matches!(entry.get_secret(),Err(keyring_core::Error::NoEntry)){return Err("owned credential cleanup not confirmed".into());}
        }self.armed=false;Ok(())
    }
}
impl Drop for Cleanup{fn drop(&mut self){if self.armed{for entry in &self.entries{let _=entry.delete_credential();}}}}

#[test]
#[ignore="guarded live qualification creates/deletes exactly three unique synthetic credential entries"]
fn custody_native_parent_persists_rotated_aes_and_hmac_for_independent_reader()->R{
    let profile=fixture_profile()?;let provider=WindowsArtifactKeyCustody::bind(profile.clone())?;
    let store=windows_native_keyring_store::Store::new().map_err(|_|"fixture store unavailable")?;
    let purposes=[ArtifactKeyPurpose::Aes256Gcm,ArtifactKeyPurpose::Aes256Gcm,ArtifactKeyPurpose::DownloadHmacSha256];
    let references=REFS.into_iter().map(reference).collect::<Result<Vec<_>,_>>()?;
    let mut cleanup=Cleanup{entries:vec![],armed:true};
    for (purpose,reference) in purposes.into_iter().zip(&references){
        let target=profile.credential_target(purpose,reference);
        let entry=store.build("hwpx-agent.artifact-custody",purpose.tag(),Some(&HashMap::from([("target",target.as_str()),("persistence","Local")]))).map_err(|_|"fixture target unavailable")?;
        if !matches!(entry.get_secret(),Err(keyring_core::Error::NoEntry)){return Err("fresh fixture target is not absent".into());}
        // Arm this exact owner before write, including an acknowledgement-lost write failure.
        cleanup.entries.push(entry);let mut key=Zeroizing::new([0;32]);getrandom::fill(key.as_mut_slice()).map_err(|_|"fixture entropy unavailable")?;
        cleanup.entries.last().ok_or("fixture target missing")?.set_secret(&blob(&target,&key)).map_err(|_|"fixture credential write unavailable")?;
    }
    let media=MediaType::parse("application/octet-stream")?;
    let original=provider.load_keyring(references[0].clone(),&references[..1])?;
    let prior=original.encrypt(public_tenant()?,ContentDigest::of(PAYLOAD),PAYLOAD.len()as u64,&media,ArtifactKind::Result,PAYLOAD)?;
    drop(original);
    let rotated=provider.load_keyring(references[1].clone(),&references[..2])?;
    let current=rotated.encrypt(public_tenant()?,ContentDigest::of(PAYLOAD),PAYLOAD.len()as u64,&media,ArtifactKind::Result,PAYLOAD)?;
    drop(rotated);
    let signer=provider.load_download_signer(BASE_URL,references[2].clone(),60)?;let signed=signer.issue(claims()?)?;drop(signer);drop(provider);
    let wire=Zeroizing::new(serde_json::to_vec(&serde_json::json!({"prior":{"metadata":prior.metadata,"ciphertext":prior.ciphertext},
        "current":{"metadata":current.metadata,"ciphertext":current.ciphertext},"download_url":signed.expose()}))?);
    if wire.len()>4096{return Err("fixture IPC bound".into());}drop(signed);
    let mut child=Command::new(std::env::current_exe()?).args(["--exact","key_custody::tests::windows::custody_native_reader",
        "--ignored","--test-threads=1","--quiet","--nocapture"]).stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::null()).spawn()?;
    let write=child.stdin.take().ok_or("fixture stdin missing")?.write_all(&wire);
    if write.is_err(){let _=child.kill();let _=child.wait();return Err("fixture IPC unavailable".into());}
    drop(wire);let deadline=Instant::now()+Duration::from_secs(10);
    let status=loop{if let Some(status)=child.try_wait()?{break status;}
        if Instant::now()>=deadline{let _=child.kill();let _=child.wait();return Err("independent custody reader timeout".into());}
        std::thread::sleep(Duration::from_millis(25));};
    if !status.success(){return Err("independent custody reader rejected".into());}
    let mut proof=Vec::new();child.stdout.take().ok_or("fixture stdout missing")?.take(1025).read_to_end(&mut proof)?;
    let marker=b"P09_OWNED_CUSTODY_READER_COMPLETED_AES2_HMAC1";
    if proof.len()>1024||proof.windows(marker.len()).filter(|p|*p==marker).count()!=1
        ||!proof.windows(b"1 passed; 0 failed; 0 ignored".len()).any(|p|p==b"1 passed; 0 failed; 0 ignored"){
        return Err("independent custody reader completion proof rejected".into());}
    let provider=WindowsArtifactKeyCustody::bind(profile.clone())?;
    let wrong=Zeroizing::new(cleanup.entries[2].get_secret().map_err(|_|"fixture secret unavailable")?);
    cleanup.entries[0].set_secret(&wrong).map_err(|_|"fixture write unavailable")?;
    assert!(matches!(provider.load_keyring(references[0].clone(),&references[..1]),Err(E::Binding)));
    let target=profile.credential_target(ArtifactKeyPurpose::Aes256Gcm,&references[1]);
    let session=store.build("hwpx-agent.artifact-custody","aes256-gcm",Some(&HashMap::from([("target",target.as_str()),("persistence","Session")]))).map_err(|_|"fixture target unavailable")?;
    let body=Zeroizing::new(cleanup.entries[1].get_secret().map_err(|_|"fixture secret unavailable")?);
    session.set_secret(&body).map_err(|_|"fixture session write unavailable")?;
    assert!(matches!(provider.load_keyring(references[1].clone(),&references[1..2]),Err(E::Persistence)));
    cleanup.entries[2].delete_credential().map_err(|_|"fixture delete unavailable")?;
    assert!(matches!(provider.load_download_signer(BASE_URL,references[2].clone(),60),Err(E::Missing)));
    cleanup.close()?;Ok(())
}

#[derive(Deserialize)]#[serde(deny_unknown_fields)]
struct Wire{prior:Encrypted,current:Encrypted,download_url:String}
#[derive(Deserialize)]#[serde(deny_unknown_fields)]
struct Encrypted{metadata:Metadata,ciphertext:Vec<u8>}
#[derive(Deserialize)]#[serde(deny_unknown_fields)]
struct Metadata{algorithm:String,key_ref:KeyReference,nonce:[u8;12],aad_sha256:ContentDigest,ciphertext_sha256:ContentDigest}
impl Metadata{fn original(self)->Result<EncryptionMetadata,Box<dyn std::error::Error>>{
    if self.algorithm!="AES-256-GCM"{return Err("fixture algorithm rejected".into());}
    Ok(EncryptionMetadata{algorithm:"AES-256-GCM",key_ref:self.key_ref,nonce:self.nonce,aad_sha256:self.aad_sha256,ciphertext_sha256:self.ciphertext_sha256})
}}
#[test]
#[ignore="private read-only child of the guarded custody qualification, never a general credential reader"]
fn custody_native_reader()->R{
    let provider=WindowsArtifactKeyCustody::bind(fixture_profile()?)?;let mut wire=Zeroizing::new(Vec::new());
    std::io::stdin().take(4097).read_to_end(&mut wire)?;if wire.len()>4096{return Err("fixture IPC bound".into());}
    let parsed:Wire=serde_json::from_slice(&wire).map_err(|_|"fixture IPC rejected")?;drop(wire);
    let references=REFS.into_iter().map(reference).collect::<Result<Vec<_>,_>>()?;
    let ring=provider.load_keyring(references[1].clone(),&references[..2])?;let media=MediaType::parse("application/octet-stream")?;
    for encrypted in [parsed.prior,parsed.current]{
        let metadata=encrypted.metadata.original()?;
        let decrypted=ring.decrypt(public_tenant()?,ContentDigest::of(PAYLOAD),PAYLOAD.len()as u64,&media,ArtifactKind::Result,&metadata,&encrypted.ciphertext)?;
        if decrypted!=PAYLOAD{return Err("fixture plaintext rejected".into());}
    }
    let signer=provider.load_download_signer(BASE_URL,references[2].clone(),60)?;
    let claims=signer.verify(&SignedDownloadUrl::new(parsed.download_url),110)?;
    if claims.tenant_id!=public_tenant()?||claims.content_sha256!=ContentDigest::of(PAYLOAD)||claims.acl_version!=1{return Err("fixture claims rejected".into());}
    println!("P09_OWNED_CUSTODY_READER_COMPLETED_AES2_HMAC1");Ok(())
}
