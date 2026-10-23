//! Closed fixture installer + original SQL/HWPX pipeline using the read-only production key provider.
//! Installer writes exactly three nonce-owned synthetic entries; no production provisioning API.
use super::*;
use std::collections::HashMap;
use artifact_service::key_custody::{ArtifactCustodyProfile,ArtifactKeyPurpose,WindowsArtifactKeyCustody};
use keyring_core::api::CredentialStoreApi;
use zeroize::Zeroizing;
const NONCE:&str="P09_OWNED_ARTIFACT_CUSTODY_NONCE";
const REFS:[&str;3]=["p09.aes-old","p09.aes-current","p09.download"];
static WRONG_KEY:std::sync::atomic::AtomicBool=std::sync::atomic::AtomicBool::new(false);
fn profile()->Result<ArtifactCustodyProfile>{
    let nonce=value(NONCE)?;let id=Uuid::parse_str(&nonce)?;
    check(id.get_version_num()==4&&id.simple().to_string()==nonce,"CUSTODY_FIXTURE_NONCE")?;
    Ok(ArtifactCustodyProfile::parse(format!("p09-owned-custody-{nonce}"))?)
}
fn refs()->Result<Vec<KeyReference>>{Ok(REFS.into_iter().map(KeyReference::parse).collect::<std::result::Result<Vec<_>,_>>()?)}
fn no_key_environment()->Result<()>{
    check(env::var_os("P09_STORAGE_AES_HEX").is_none()&&env::var_os("P09_STORAGE_HMAC_HEX").is_none(),"CUSTODY_CRYPTO_ENVIRONMENT_FORBIDDEN")
}
fn install()->Result<Value>{
    no_key_environment()?;
    check(["P09_SQL23_ADMIN_PASSWORD","P09_SQL23_ARTIFACT_PASSWORD","P09_SQL23_REVISION_PASSWORD"].iter().all(|name|env::var_os(name).is_none()),"CUSTODY_INSTALLER_DATABASE_CREDENTIALS_FORBIDDEN")?;
    let profile=profile()?;let store=windows_native_keyring_store::Store::new().map_err(|_|"CUSTODY_FIXTURE_STORE_UNAVAILABLE")?;
    let purposes=[ArtifactKeyPurpose::Aes256Gcm,ArtifactKeyPurpose::Aes256Gcm,ArtifactKeyPurpose::DownloadHmacSha256];
    let mut entries=vec![];
    for(purpose,reference)in purposes.into_iter().zip(refs()?){
        let target=profile.credential_target(purpose,&reference);
        let entry=store.build("hwpx-agent.artifact-custody","owned-sql-fixture",Some(&HashMap::from([("target",target.as_str()),("persistence","Local")]))).map_err(|_|"CUSTODY_FIXTURE_TARGET_UNAVAILABLE")?;
        check(matches!(entry.get_secret(),Err(keyring_core::Error::NoEntry)),"CUSTODY_FIXTURE_TARGET_NOT_ABSENT")?;entries.push((entry,target));
    }
    for(entry,target)in entries{
        // The external owner already armed exact-target cleanup, including a lost write acknowledgement.
        let mut key=Zeroizing::new([0;32]);getrandom::fill(key.as_mut_slice()).map_err(|_|"CUSTODY_FIXTURE_ENTROPY_UNAVAILABLE")?;
        let mut blob=Zeroizing::new(Vec::with_capacity(72));blob.extend_from_slice(b"HWPXKEY1");blob.extend_from_slice(&Sha256::digest(target.as_bytes()));blob.extend_from_slice(key.as_slice());
        entry.set_secret(&blob).map_err(|_|"CUSTODY_FIXTURE_WRITE_UNAVAILABLE")?;
    }
    Ok(json!({"state":"PASS_OWNED_WINDOWS_KEY_INSTALLER_EXIT_WITHOUT_KEY_EXPORT","credential_entries":3,"keys_in_output_or_environment":false,"database_credentials_received":false}))
}
pub(super) fn crypto()->Result<(Aes256GcmKeyring,DownloadSigner)>{
    no_key_environment()?;let provider=WindowsArtifactKeyCustody::bind(profile()?)?;let references=refs()?;
    let ring=if WRONG_KEY.load(std::sync::atomic::Ordering::Relaxed){
        // Deliberately wrong AES only for the closed negative probe; never overwrites the OS key.
        let mut wrong=Zeroizing::new([0;32]);getrandom::fill(wrong.as_mut_slice()).map_err(|_|"CUSTODY_FIXTURE_ENTROPY_UNAVAILABLE")?;
        Aes256GcmKeyring::new(references[1].clone(),[(references[1].clone(),*wrong)])?
    }else{provider.load_keyring(references[1].clone(),&references[..2])?};
    Ok((ring,provider.load_download_signer("https://fixture.example.test/storage",references[2].clone(),60)?))
}
fn signed_readback()->Result<Value>{
    let a=artifacts()?;let actor=actor()?;let result=catalog::result_artifact()?;
    let expected=a.download(&actor,result,20)?;let url=a.issue_download_url(&actor,result,20)?;
    check(a.redeem_download_url(&actor,&url,21)?==expected,"CUSTODY_SQL_SIGNED_ARTIFACT_READBACK")?;
    Ok(json!({"current_SQL_ACL_and_AEAD_readback":true,"download_HMAC_issued_and_redeemed":true,"signed_URL_not_exported":true}))
}
pub(super) fn run(mode:&str)->Result<Value>{
    no_key_environment()?;owned_root()?;
    if mode=="--custody-install-keys"{return install();}
    check(matches!(mode,"--fixture"|"--seed"|"--execute"|"--wrong-key"|"--restart-registered"),"CUSTODY_SQL_CLOSED_MODE")?;
    WRONG_KEY.store(mode=="--wrong-key",std::sync::atomic::Ordering::Relaxed);
    let mut result=lookup24::run(mode)?;
    if matches!(mode,"--execute"|"--restart-registered"){result["windows_signed_artifact_readback"]=signed_readback()?;}
    result["artifact_AES_HMAC_environment_absent"]=json!(true);
    result["artifact_key_source"]=json!(if mode=="--wrong-key"{"deliberate_wrong_AES_negative_probe"}else{"windows_current_user_exact_local_targets"});
    result["key_installer_not_running"]=json!(true);Ok(result)
}
