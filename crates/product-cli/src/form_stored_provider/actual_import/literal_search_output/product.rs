//! Ownership transfer only; the original preparation/access/byte methods stay shared.
use super::*;
pub(super) enum LiteralSource<'a> {Borrowed(&'a StoredImportedDocumentForms),Owned(Box<StoredImportedDocumentForms>)}
impl std::ops::Deref for LiteralSource<'_> {
    type Target=StoredImportedDocumentForms;
    fn deref(&self)->&Self::Target {match self {Self::Borrowed(s)=>s,Self::Owned(s)=>s}}
}
impl StoredImportedDocumentForms {
    pub(crate) fn into_literal_search_candidate<R,B,S,V>(self,provider:&StoredFormProvider<'_,R,B,S,V>,query:SourceSearchQuery<'_>,scope:SourceSearchScope<'_>,
        replacement:&str,run_policy:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredLiteralSearchCandidate<'static>,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let (output,receipt)={let prepared=self.prepare_literal_search_candidate(provider,query,scope,replacement,run_policy,limits,writer,now)?;
            (prepared.output,prepared.receipt)};
        Ok(PreparedStoredLiteralSearchCandidate {source:LiteralSource::Owned(Box::new(self)),output,receipt})
    }
}
