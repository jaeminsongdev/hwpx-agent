use super::*;
use std::{collections::HashMap,sync::Arc};
use keyring_core::api::CredentialStoreApi;
use crate::DownloadSigner;

/// Only exact, purpose-separated artifact entries in the current user's Windows store.
/// No provisioning methods and no default/global keyring store mutation.
pub struct WindowsArtifactKeyCustody{
    profile:ArtifactCustodyProfile,store:Arc<windows_native_keyring_store::Store>,
}
impl fmt::Debug for WindowsArtifactKeyCustody{
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("WindowsArtifactKeyCustody(<redacted>; read_only_exact_targets)")}
}
impl WindowsArtifactKeyCustody{
    /// # Errors
    /// Binds a trusted profile without any credential read, enumeration or write.
    pub fn bind(profile:ArtifactCustodyProfile)->Result<Self,E>{
        let store=windows_native_keyring_store::Store::new().map_err(map_error)?;Ok(Self{profile,store})
    }
    /// # Errors
    /// At most16 explicitly configured AES references, including active and retained decrypt keys.
    /// Missing, wrong-purpose, malformed or non-local credentials fail without regeneration/fallback.
    pub fn load_keyring(&self,active:KeyReference,references:&[KeyReference])->Result<Aes256GcmKeyring,E>{
        keyring(active,references,|reference|self.read(ArtifactKeyPurpose::Aes256Gcm,reference))
    }
    /// # Errors
    /// Loads a separate HMAC purpose; the existing HTTPS/lifetime/signature checks are unchanged.
    pub fn load_download_signer(&self,base_url:impl Into<String>,reference:KeyReference,max_ttl_seconds:u64)->Result<DownloadSigner,E>{
        let key=self.read(ArtifactKeyPurpose::DownloadHmacSha256,&reference)?;
        Ok(DownloadSigner::new(base_url,reference,key.as_slice(),max_ttl_seconds)?)
    }
    fn read(&self,purpose:ArtifactKeyPurpose,reference:&KeyReference)->Result<Zeroizing<[u8;32]>,E>{
        let target=self.profile.credential_target(purpose,reference);
        let entry=self.store.build("hwpx-agent.artifact-custody",purpose.tag(),Some(&HashMap::from([("target",target.as_str())]))).map_err(map_error)?;
        // Local is verified on the EXISTING entry; a build modifier cannot change read persistence.
        require_local(&entry)?;let blob=Zeroizing::new(entry.get_secret().map_err(map_error)?);require_local(&entry)?;
        decode(&target,blob)
    }
}
fn require_local(entry:&keyring_core::Entry)->Result<(),E>{
    let attributes=entry.get_attributes().map_err(map_error)?;
    if attributes.get("persistence").map(String::as_str)!=Some("Local"){return Err(E::Persistence);}Ok(())
}
fn map_error(error:keyring_core::Error)->E{
    match error{
        keyring_core::Error::NoEntry=>E::Missing,
        keyring_core::Error::BadEncoding(bytes)|keyring_core::Error::BadDataFormat(bytes,_)=>{let _secret=Zeroizing::new(bytes);E::Malformed},
        _=>E::Unavailable,
    }
}
