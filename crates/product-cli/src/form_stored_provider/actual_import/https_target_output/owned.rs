//! Same borrowed/owned transfer pattern as the existing literal candidate; no graph reimport/clone.
use super::*;
pub(super) enum HttpsSource<'a>{Borrowed(&'a StoredImportedDocumentForms),Owned(Box<StoredImportedDocumentForms>)}
impl std::ops::Deref for HttpsSource<'_>{
    type Target=StoredImportedDocumentForms;
    fn deref(&self)->&Self::Target{match self{Self::Borrowed(source)=>source,Self::Owned(source)=>source}}
}
impl StoredImportedDocumentForms{
    pub(crate) fn into_https_target_candidate<R,B,S,V,P>(self,provider:&StoredFormProvider<'_,R,B,S,V>,repository:&P,
        requests:&[SourceHttpsTargetChange<'_>],limits:ReferenceAuxiliaryLimits,targets:LinkReferenceLimits,writer:WriterLimits,now:u64)
        ->Result<PreparedStoredHttpsTargetCandidate<'static>,StoredHttpsTargetError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository,P:HttpsTargetPolicyRepository{
        let(version,output,receipt,anchors)={let prepared=self.prepare_https_target_candidate(provider,repository,requests,limits,targets,writer,now)?;
            (prepared.version,prepared.output,prepared.receipt,prepared.anchors)};
        Ok(PreparedStoredHttpsTargetCandidate{source:HttpsSource::Owned(Box::new(self)),version,output,receipt,anchors})
    }
}
