//! Historical manifest data only. Never deserializes or constructs an executable manifest.
use super::*;
use serde::Deserialize;
const MAX_BYTES:usize=16*1024;

/// Bounded canonical historical data, not an executor/route/lease/validation permit.
///
/// ```compile_fail
/// use operation_engine::{ArchivedExecutionManifest,ExecutionManifest};
/// fn execution_from_archive(data:ArchivedExecutionManifest)->ExecutionManifest{data.into()}
/// ```
/// ```compile_fail
/// use operation_engine::ArchivedExecutionManifest;
/// let data:ArchivedExecutionManifest=serde_json::from_slice(b"{}").unwrap();
/// ```
#[derive(Clone,Eq,PartialEq)]
pub struct ArchivedExecutionManifest{snapshot:Snapshot,canonical:Vec<u8>,sha256:[u8;32]}
impl fmt::Debug for ArchivedExecutionManifest{
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("ArchivedExecutionManifest(<redacted>; historical_data_not_execution_authority)")}
}
// Field order is the original canonical v1 manifest order, not a new authority schema.
#[derive(Clone,Eq,PartialEq,Serialize,Deserialize)]#[serde(deny_unknown_fields)]
struct Snapshot{
    schema_version:String,transaction_id:TransactionId,plan_id:PlanId,source_artifact_id:ArtifactId,base_revision:RevisionId,
    expected_source_sha256:[u8;32],expected_source_size:u64,compiled_plan_sha256:[u8;32],route_set_sha256:[u8;32],route_count:usize,
    target_profile_id:TargetProfileId,registry_payload_sha256:[u8;32],registry_sequence:u64,
}
#[derive(Serialize,Deserialize)]#[serde(deny_unknown_fields)]
struct Precommit{
    transaction_id:TransactionId,base_revision:RevisionId,source_artifact_id:ArtifactId,result_artifact_id:ArtifactId,
    manifest_sha256:[u8;32],result_sha256:[u8;32],result_size:u64,
}
#[derive(Clone,Copy,Debug,Eq,Error,PartialEq)]
pub enum ManifestArchiveError{
    #[error("MANIFEST_ARCHIVE_LIMIT")]Limit,
    #[error("MANIFEST_ARCHIVE_SHAPE")]Shape,
    #[error("MANIFEST_ARCHIVE_BINDING")]Binding,
    #[error("MANIFEST_ARCHIVE_NOT_CANONICAL")]Canonical,
    #[error("MANIFEST_ARCHIVE_PRECOMMIT_BINDING")]Precommit,
}
type A=ManifestArchiveError;
impl ArchivedExecutionManifest{
    /// # Errors
    /// Captures the original immutable bytes; no worker, source/import, compiler or authority is issued.
    pub fn capture(manifest:&ExecutionManifest)->Result<Self,A>{
        let bytes=manifest.canonical_json().map_err(|_|A::Shape)?;
        let sha=Sha256::digest(&bytes).into();Self::from_canonical_json(&bytes,sha)
    }
    /// # Errors
    /// Exact bounded canonical v1 shape and expected whole SHA are mandatory; no fallback or executable conversion.
    pub fn from_canonical_json(bytes:&[u8],expected_sha256:[u8;32])->Result<Self,A>{
        if bytes.is_empty()||bytes.len()>MAX_BYTES{return Err(A::Limit);}
        if expected_sha256==[0;32]||<[u8;32]>::from(Sha256::digest(bytes))!=expected_sha256{return Err(A::Binding);}
        let snapshot:Snapshot=serde_json::from_slice(bytes).map_err(|_|A::Shape)?;
        if snapshot.schema_version!=EXECUTION_MANIFEST_SCHEMA_VERSION||snapshot.expected_source_size==0||snapshot.route_count==0
            ||snapshot.registry_sequence==0||[snapshot.expected_source_sha256,snapshot.compiled_plan_sha256,snapshot.route_set_sha256,snapshot.registry_payload_sha256].contains(&[0;32]){
            return Err(A::Binding);}
        if serde_json::to_vec(&snapshot).map_err(|_|A::Shape)?!=bytes{return Err(A::Canonical);}
        Ok(Self{snapshot,canonical:bytes.to_vec(),sha256:expected_sha256})
    }
    #[must_use]pub fn canonical_json(&self)->&[u8]{&self.canonical}
    #[must_use]pub const fn canonical_sha256(&self)->[u8;32]{self.sha256}
    #[must_use]pub const fn source_artifact_id(&self)->&ArtifactId{&self.snapshot.source_artifact_id}
    #[must_use]pub const fn base_revision(&self)->&RevisionId{&self.snapshot.base_revision}
    #[must_use]pub const fn expected_source_sha256(&self)->[u8;32]{self.snapshot.expected_source_sha256}
    #[must_use]pub const fn expected_source_size(&self)->u64{self.snapshot.expected_source_size}
    #[must_use]pub const fn compiled_plan_sha256(&self)->[u8;32]{self.snapshot.compiled_plan_sha256}
    /// # Errors
    /// Checks the exact original engine precommit bytes, including content artifact ID, against archived identity/result.
    /// Caller must independently authenticate the precommit whole SHA/ACL/AEAD and registered request.
    pub fn verify_precommit(&self,bytes:&[u8],result_sha256:[u8;32],result_size:u64)->Result<(),A>{
        if bytes.is_empty()||bytes.len()>MAX_BYTES{return Err(A::Limit);}
        let record:Precommit=serde_json::from_slice(bytes).map_err(|_|A::Shape)?;
        if serde_json::to_vec(&record).map_err(|_|A::Shape)?!=bytes{return Err(A::Canonical);}
        if result_sha256==[0;32]||result_size==0||record.transaction_id!=self.snapshot.transaction_id||record.base_revision!=self.snapshot.base_revision
            ||record.source_artifact_id!=self.snapshot.source_artifact_id||record.manifest_sha256!=self.sha256||record.result_sha256!=result_sha256||record.result_size!=result_size
            ||record.result_artifact_id!=crate::transaction::artifact_id(result_sha256).map_err(|_|A::Precommit)?{return Err(A::Precommit);}
        Ok(())
    }
}
