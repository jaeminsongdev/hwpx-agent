//! Readonly exact historic public trust and private signed evidence; never reads a private key.
use super::PinnedP02RegistryBytes;
use std::{error::Error,fs::File,io::Read,path::Path};
pub const ENVELOPE:&str="implementation/p02/evidence/signing-runs/7b63d0ede07ea116e64d084fa00015a0fefb4ec3/signed-registry.json";
pub const POLICY:&str="implementation/p02/trust/p02-current-pc-local-trust-policy.json";
pub const KEY:&str="implementation/p02/trust/p02-current-pc-local-ed25519-public.pem";
pub struct Material{pub envelope:Vec<u8>,pub policy:Vec<u8>,pub key:Vec<u8>}
impl Material{pub fn input(&self)->PinnedP02RegistryBytes<'_>{PinnedP02RegistryBytes{envelope:&self.envelope,policy:&self.policy,public_key:&self.key}}}
pub fn load()->Result<Material,Box<dyn Error>>{
    let root=Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
    fn read(root:&Path,name:&str,limit:u64)->Result<Vec<u8>,Box<dyn Error>>{
        let path=root.join(name);let m=std::fs::symlink_metadata(&path)?;
        if !m.is_file()||m.file_type().is_symlink()||m.len()>limit{return Err("pinned fixture file identity".into());}
        let mut out=Vec::new();File::open(path)?.take(limit+1).read_to_end(&mut out)?;
        if out.len()as u64!=m.len(){return Err("pinned fixture length drift".into());}Ok(out)
    }
    Ok(Material{envelope:read(&root,ENVELOPE,1024*1024)?,policy:read(&root,POLICY,64*1024)?,key:read(&root,KEY,64*1024)?})
}
