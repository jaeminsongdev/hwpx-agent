//! Current sealed Result -> retained read-only format candidates. No bytes, masking, compiler or execution grant.
use super::*;
use hwpx_package::document_import::search::{personal_info::{SourcePersonalInfoDetectionPolicy,SourcePersonalInfoDetectionResult},
    selector::{SourceIndexScopeSelector,SourceIndexScopeReceipt}};
pub const STORED_PERSONAL_INFO_DETECTION_PROFILE:&str="hwpx-agent.stored-personal-info-format-candidates/v1";
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredPersonalInfoDetectionReceipt{
    pub profile:&'static str,pub source:StoredActualFormImportReceipt,pub index:SourceSearchIndexReceipt,pub scope:SourceIndexScopeReceipt,
    pub policy_sha256:[u8;32],pub request_sha256:[u8;32],pub result_sha256:[u8;32],pub review_policy:SourceReviewTextPolicy,pub matched_formats:usize,
    pub native_format_identity_or_execution_qualified:bool,pub whole_package_personal_data_removed:bool,
}
pub struct PreparedStoredPersonalInfoDetection{source:StoredImportedDocumentForms,result:SourcePersonalInfoDetectionResult,receipt:StoredPersonalInfoDetectionReceipt,maximum:usize}
impl fmt::Debug for PreparedStoredPersonalInfoDetection{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedStoredPersonalInfoDetection(<redacted>; read_only_formats_not_identity_or_execution)")}}
#[derive(Debug,Error)]
pub enum StoredPersonalInfoDetectionError{
    #[error("STORED_PERSONAL_INFO_DETECTION_ACCESS_REJECTED")]Source(#[from]StoredActualFormImportError),
    #[error("STORED_PERSONAL_INFO_DETECTION_SEARCH_REJECTED")]Search(#[from]SourceSearchError),
    #[error("STORED_PERSONAL_INFO_DETECTION_BINDING_REJECTED")]Binding,
    #[error("STORED_PERSONAL_INFO_DETECTION_DOCUMENT_WRITE_REQUIRED")]Permission,
    #[error("STORED_PERSONAL_INFO_DETECTION_METADATA_LIMIT")]Limit,
    #[error("STORED_PERSONAL_INFO_DETECTION_ROUTE_UNQUALIFIED")]RouteUnqualified,
}
type D=StoredPersonalInfoDetectionError;
#[derive(Serialize)]pub(crate) struct DetectionEnvelope<'a,R,T>{pub receipt:&'a R,pub result:T}
impl StoredImportedDocumentForms{
    /// # Errors
    /// Move the original source owner; one whole Form proof/review index and one combined candidate scan.
    pub fn into_personal_info_detection<R,B,S,V>(self,provider:&StoredFormProvider<'_,R,B,S,V>,policy:&SourcePersonalInfoDetectionPolicy,
        selector:SourceIndexScopeSelector<'_>,review_policy:SourceReviewTextPolicy,limits:SourceSearchLimits,now:u64)->Result<PreparedStoredPersonalInfoDetection,D>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(D::Permission);}
        let(fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
        let index=proof.source_review_scope_index(&self.imported,limits)?;let result=index.find_personal_info_candidates(policy,selector,review_policy)?;
        if result.search().result().index_receipt().source_package_sha256!=*fresh.digest.as_bytes(){return Err(D::Binding);}
        let receipt=StoredPersonalInfoDetectionReceipt{profile:STORED_PERSONAL_INFO_DETECTION_PROFILE,source:self.receipt.clone(),index:result.search().result().index_receipt().clone(),
            scope:result.search().scope_receipt().clone(),policy_sha256:policy.canonical_sha256(),request_sha256:result.request_sha256(),result_sha256:metadata_sha(&result,limits.maximum_result_bytes())?,
            review_policy,matched_formats:result.rule_matches().len(),native_format_identity_or_execution_qualified:false,whole_package_personal_data_removed:false};
        metadata_bound(&DetectionEnvelope{receipt:&receipt,result:&result},limits.maximum_result_bytes())?;
        provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
        Ok(PreparedStoredPersonalInfoDetection{source:self,result,receipt,maximum:limits.maximum_result_bytes()})
    }
}
impl PreparedStoredPersonalInfoDetection{
    #[must_use]pub const fn receipt(&self)->&StoredPersonalInfoDetectionReceipt{&self.receipt}
    fn fresh<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),D>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(D::Permission);}
        let fresh=self.source.fresh_source(provider,now)?;let r=&self.receipt;
        if r.profile!=STORED_PERSONAL_INFO_DETECTION_PROFILE||r.source!=self.source.receipt||&r.index!=self.result.search().result().index_receipt()
            ||&r.scope!=self.result.search().scope_receipt()||r.index.source_package_sha256!=*fresh.digest.as_bytes()
            ||r.index.graph_sha256!=self.source.imported.receipt().body_graph_sha256||r.request_sha256!=self.result.request_sha256()
            ||r.result_sha256!=metadata_sha(&self.result,self.maximum)?||r.matched_formats!=self.result.rule_matches().len()
            ||r.native_format_identity_or_execution_qualified||r.whole_package_personal_data_removed||r.index.edit_or_service_access_authority
            ||r.index.whole_document_visibility_and_search_qualified||r.scope.whole_document_visibility_native_flow_or_revision_authority{return Err(D::Binding);}Ok(())
    }
    pub(crate) fn check_product_envelope(&self,receipt:&impl Serialize)->Result<(),D>{metadata_bound(&DetectionEnvelope{receipt,result:&self.result},self.maximum)}
    pub(crate) fn check_final_head<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>)->Result<(),D>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(())
    }
    /// Internal projection: bytes are built and bounded before the last head check, then delivered once.
    pub(crate) fn with_verified_projection<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,
        project:impl FnOnce(&SourcePersonalInfoDetectionResult,usize)->Result<Vec<u8>,D>,consume:impl FnOnce(&[u8])->T)->Result<T,D>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.fresh(provider,now)?;let bytes=project(&self.result,self.maximum)?;if bytes.len()>self.maximum{return Err(D::Limit);}
        self.check_final_head(provider)?;Ok(consume(&bytes))
    }
    /// # Errors
    /// Current access/source/integrity, without regex compilation, review indexing or query replay.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<StoredPersonalInfoDetectionReceipt,D>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.fresh(provider,now)?;self.check_final_head(provider)?;Ok(self.receipt.clone())
    }
    /// # Errors
    /// Entire retained metadata only; current authorization and consumer-final head always precede disclosure.
    pub fn with_verified_json<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,D>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.with_verified_projection(provider,now,|result,max|metadata_json(&DetectionEnvelope{receipt:&self.receipt,result},max),consume)
    }
    /// # Errors
    /// Read-only candidates do not qualify execution, CAS, publication, masking or Native defaults.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),D>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.verify(provider,now)?;Err(D::RouteUnqualified)}
}
struct Metadata{bytes:Option<Vec<u8>>,sha:Sha256,length:usize,maximum:usize}
impl std::io::Write for Metadata{
    fn write(&mut self,b:&[u8])->std::io::Result<usize>{self.length=self.length.checked_add(b.len()).filter(|n|*n<=self.maximum).ok_or_else(||std::io::Error::other("personal_info_detection_metadata_limit"))?;
        if let Some(out)=&mut self.bytes{out.try_reserve(b.len()).map_err(|_|std::io::Error::other("personal_info_detection_metadata_allocation"))?;out.extend_from_slice(b);}self.sha.update(b);Ok(b.len())}
    fn flush(&mut self)->std::io::Result<()>{Ok(())}
}
fn serialize(value:&impl Serialize,maximum:usize,bytes:bool)->Result<Metadata,D>{
    if maximum==0||maximum>4*1024*1024{return Err(D::Limit);}let mut out=Metadata{bytes:bytes.then(Vec::new),sha:Sha256::new(),length:0,maximum};
    serde_json::to_writer(&mut out,value).map_err(|_|D::Limit)?;Ok(out)
}
pub(crate) fn metadata_bound(value:&impl Serialize,maximum:usize)->Result<(),D>{serialize(value,maximum,false).map(|_|())}
pub(crate) fn metadata_json(value:&impl Serialize,maximum:usize)->Result<Vec<u8>,D>{serialize(value,maximum,true)?.bytes.ok_or(D::Limit)}
pub(crate) fn metadata_sha(value:&impl Serialize,maximum:usize)->Result<[u8;32],D>{Ok(serialize(value,maximum,false)?.sha.finalize().into())}
