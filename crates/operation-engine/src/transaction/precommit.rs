use super::*;

/// Expected identity only, before source verification or execution. It is deliberately NOT
/// RevisionCommitRequest, Serialize/Deserialize, a CAS argument or convertible into one.
#[derive(Clone,Eq,PartialEq)]
pub struct PreparedPrecommitIdentity{expected:RevisionCommitRequest}
impl PreparedPrecommitIdentity{
    /// Expected v2 transaction digest, never evidence that execution/validation/publication occurred.
    /// # Errors
    /// Propagates canonical serialization failure.
    pub fn expected_precommit_sha256(&self)->Result<[u8;32],TransactionError>{self.expected.canonical_sha256()}
    #[must_use]pub const fn expected_result_sha256(&self)->[u8;32]{self.expected.result_sha256}
    #[must_use]pub const fn expected_result_size(&self)->u64{self.expected.result_size}
    /// Requires a separately obtained sealed engine callback request; exposes no request conversion.
    #[must_use]pub fn matches_executed(&self,actual:&RevisionCommitRequest)->bool{self.expected==*actual}
}
impl fmt::Debug for PreparedPrecommitIdentity{
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{
        f.debug_struct("PreparedPrecommitIdentity").field("expected_result_size",&self.expected.result_size).finish_non_exhaustive()
    }
}
impl ExecutionManifest{
    /// Derives a finite expected job/effect/precommit identity from retained candidate bytes.
    /// Does not read/write files, verify current source/authority, invoke validation or execute.
    /// It cannot turn an expected identity into the actual engine's sealed CAS request.
    /// # Errors
    /// Applies original transaction limits before hashing candidate bytes; rejects empty/oversized
    /// output, oversized source/manifest and invalid limits. Live checks still occur at execution.
    pub fn prepare_precommit(&self,output:&[u8],limits:TransactionLimits)->Result<PreparedPrecommitIdentity,TransactionError>{
        limits.validate()?;
        if self.expected_source_size()>limits.max_source_bytes{return Err(TransactionError::LimitExceeded);}
        let bytes=self.canonical_json().map_err(|_|TransactionError::InvalidManifest)?;
        if bytes.len()>limits.max_manifest_bytes{return Err(TransactionError::LimitExceeded);}
        let size=u64::try_from(output.len()).map_err(|_|TransactionError::LimitExceeded)?;
        if size==0||size>limits.max_output_bytes{return Err(TransactionError::InvalidOutput);}
        let expected=RevisionCommitRequest::from_manifest_result(self,Sha256::digest(&bytes).into(),Sha256::digest(output).into(),size)?;
        Ok(PreparedPrecommitIdentity{expected})
    }
}
impl RevisionCommitRequest{
    pub(super) fn from_manifest_result(manifest:&ExecutionManifest,manifest_sha256:[u8;32],result_sha256:[u8;32],result_size:u64)
        ->Result<Self,TransactionError>{
        let result_artifact_id=artifact_id(result_sha256)?;
        Ok(Self{transaction_id:manifest.transaction_id().clone(),base_revision:manifest.base_revision().clone(),
            source_artifact_id:manifest.source_artifact_id().clone(),result_artifact_id,manifest_sha256,result_sha256,result_size})
    }
}
