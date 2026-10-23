//! Transfer the already prepared v3 output and source owner, without cloning or reimport.
use super::*;
use super::super::super::product::LiteralSource;
impl StoredImportedDocumentForms {
    pub(crate) fn into_review_literal_candidate<R,B,S,V>(self,provider:&StoredFormProvider<'_,R,B,S,V>,query:SourceSearchQuery<'_>,scope:SourceSearchScope<'_>,policy:SourceReviewTextPolicy,
        replacement:&str,run_policy:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredReviewLiteralCandidate<'static>,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let (output,receipt)={let prepared=self.prepare_review_literal_candidate(provider,query,scope,policy,replacement,run_policy,limits,writer,now)?;
            (prepared.output,prepared.receipt)};
        Ok(PreparedStoredReviewLiteralCandidate {source:LiteralSource::Owned(Box::new(self)),output,receipt})
    }
}
