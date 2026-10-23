//! Stable project-scoped request identities, not a key claim, lease, retry or execution permit.
use super::*;
use artifact_service::TenantId;
use domain_ir::IdempotencyKey;
use sha2::{Digest as _,Sha256};

const PROFILE:&str="hwpx-agent.stored-public-key-identity/v1";
/// Server retry policy only. Original StoredJobClaim validation still enforces every SQL limit.
#[derive(Clone,Copy,Debug)]
pub struct StoredJobPolicy{pub max_attempts:i32,pub base_delay_seconds:i32,pub max_delay_seconds:i32,pub ttl_seconds:i32}
impl Default for StoredJobPolicy{fn default()->Self{Self{max_attempts:3,base_delay_seconds:1,max_delay_seconds:60,ttl_seconds:600}}}

/// Private origin from the strict request and authenticated provider. Never deserialized as authority.
/// Same tenant/project/public key maps to the SAME IDs despite changed content/head/actor/document.
/// Those changes must conflict with the DB's immutable full binding, never get a fresh key.
#[derive(Clone,Eq,PartialEq)]
pub struct StoredRequestJobIdentity{project:ProjectId,key:Uuid,job:Uuid,request:Uuid,canonical:ContentDigest,scoped:ContentDigest}
impl fmt::Debug for StoredRequestJobIdentity{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("StoredRequestJobIdentity(<redacted>; unclaimed)")}}
fn digest(value:&impl serde::Serialize)->Result<[u8;32],StoredCommitError>{
    let bytes=serde_json::to_vec(value).map_err(|_|StoredCommitError::Binding)?;
    if bytes.len()>4096{return Err(StoredCommitError::Binding);}Ok(Sha256::digest(bytes).into())
}
fn identifier(hash:[u8;32])->Uuid{
    let mut bytes=[0;16];bytes.copy_from_slice(&hash[..16]);
    // Fixed custom/version8 layout. Full canonical/scoped bindings remain separate, never truncated.
    bytes[6]=(bytes[6]&15)|0x80;bytes[8]=(bytes[8]&63)|0x80;Uuid::from_bytes(bytes)
}
impl StoredRequestJobIdentity{
    pub(crate) fn bind(tenant:TenantId,project:ProjectId,key:&IdempotencyKey,canonical:&str,scoped:&str)->Result<Self,StoredCommitError>{
        let canonical=ContentDigest::parse(canonical).map_err(|_|StoredCommitError::Binding)?;
        let scoped=ContentDigest::parse(scoped).map_err(|_|StoredCommitError::Binding)?;
        if canonical.as_bytes()==&[0;32]||scoped.as_bytes()==&[0;32]{return Err(StoredCommitError::Binding);}
        let full=digest(&(PROFILE,"key",tenant.as_uuid(),project.as_uuid(),key.as_str()))?;
        Ok(Self{project,key:identifier(full),job:identifier(digest(&(PROFILE,"job",full))?),
            request:identifier(digest(&(PROFILE,"request",full))?),canonical,scoped})
    }
    #[must_use]pub const fn key(&self)->Uuid{self.key}
    #[must_use]pub const fn job(&self)->Uuid{self.job}
    #[must_use]pub const fn request(&self)->Uuid{self.request}
    pub(crate) fn matches(&self,project:ProjectId,canonical:&str,scoped:&str)->bool{
        self.project==project&&self.canonical.hex()==canonical&&self.scoped.hex()==scoped
    }
    pub(crate) fn options(&self,capability_sha:ContentDigest,p:StoredJobPolicy)->StoredJobOptions{
        StoredJobOptions{key:self.key,job:self.job,request:self.request,request_sha:self.canonical,capability_sha,
            max_attempts:p.max_attempts,base_delay_seconds:p.base_delay_seconds,max_delay_seconds:p.max_delay_seconds,ttl_seconds:p.ttl_seconds}
    }
    pub(crate) fn lookup(&self,branch:BranchId,source:ContentDigest,head:RevisionHead)
        ->Result<revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::request_lookup::StoredRequestLookup,revision_service::RevisionError>{
        revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::request_lookup::StoredRequestLookup::new(
            self.project,branch,self.key,self.job,self.request,self.canonical,source,head)
    }
}

#[cfg(test)]mod tests{
    use super::*;
    type R=Result<(),Box<dyn std::error::Error>>;
    fn bound(tenant:u128,project:u128,key:&str,canonical:&str,scoped:&str)->Result<StoredRequestJobIdentity,Box<dyn std::error::Error>>{
        Ok(StoredRequestJobIdentity::bind(TenantId::new(Uuid::from_u128(tenant))?,ProjectId::parse(&format!("prj_{}",Uuid::from_u128(project).simple()))?,
            &IdempotencyKey::parse(key)?,canonical,scoped)?)
    }
    fn make(t:u128,p:u128,k:&str)->Result<StoredRequestJobIdentity,Box<dyn std::error::Error>>{bound(t,p,k,&ContentDigest::of(b"request").hex(),&ContentDigest::of(b"scope").hex())}
    #[test]fn fixed_cross_process_vector_has_three_distinct_non_nil_identities()->R{
        let i=make(1,2,"public-example")?;
        assert_eq!(i.key().to_string(),"81cac361-f8df-8395-b217-be1d1b439719");
        assert_eq!(i.job().to_string(),"aa5cdbf2-68fa-8a5a-bd01-bd155911f0f1");
        assert_eq!(i.request().to_string(),"027faf09-8dde-8bce-8b49-f29216973b7e");Ok(())
    }
    #[test]fn changed_content_actor_document_head_or_schema_cannot_rekey_same_project_key()->R{
        let a=make(1,2,"public-example")?;let b=bound(1,2,"public-example",&ContentDigest::of(b"changed body/head/schema").hex(),&ContentDigest::of(b"changed actor/branch/document").hex())?;
        assert_eq!((a.key,a.job,a.request),(b.key,b.job,b.request));assert_ne!(a,b);assert!(!b.matches(a.project,&a.canonical.hex(),&a.scoped.hex()));Ok(())
    }
    #[test]fn tenant_and_project_are_the_existing_sql_key_namespace()->R{
        let a=make(1,2,"same")?;
        for b in[make(2,2,"same")?,make(1,3,"same")?]{assert_ne!(a.key,b.key);assert_ne!(a.job,b.job);assert_ne!(a.request,b.request);}Ok(())
    }
    #[test]fn key_bytes_are_exact_not_unicode_normalized_or_concatenated()->R{
        let a=make(1,2,"é")?;let b=make(1,2,"e\u{301}")?;assert_ne!(a.key,b.key);
        assert_ne!(make(1,23,"4")?.key,make(1,2,"34")?.key);assert_ne!(make(1,2,"a/b")?.key,make(1,2,"ab")?.key);Ok(())
    }
    #[test]fn invalid_digests_and_nil_scope_are_rejected_before_job_preparation()->R{
        for bad in["", "INVALID", &"0".repeat(64)]{assert!(bound(1,2,"key",bad,&ContentDigest::of(b"scope").hex()).is_err());
            assert!(bound(1,2,"key",&ContentDigest::of(b"request").hex(),bad).is_err());}
        assert!(make(0,2,"key").is_err());assert!(make(1,0,"key").is_err());Ok(())
    }
    #[test]fn debug_is_redacted_and_original_canonical_and_route_digests_stay_full_width()->R{
        let a=make(1,2,"PRIVATE-ORIGINAL")?;assert_eq!(format!("{a:?}"),"StoredRequestJobIdentity(<redacted>; unclaimed)");
        let cap=ContentDigest::of(b"route");let opts=a.options(cap,Default::default());assert_eq!(opts.request_sha,a.canonical);assert_eq!(opts.capability_sha,cap);
        assert_eq!((opts.key,opts.job,opts.request),(a.key,a.job,a.request));assert_eq!(a,a.clone());Ok(())
    }
}
