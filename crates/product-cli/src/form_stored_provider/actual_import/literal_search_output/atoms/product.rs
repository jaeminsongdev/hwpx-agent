//! Use the existing source owner enum; transferring ownership does not import or clone.
use super::*;
use super::super::product::LiteralSource;
impl StoredImportedDocumentForms {
    pub(crate) fn into_literal_text_atom_candidate<R,B,S,V>(self,provider:&StoredFormProvider<'_,R,B,S,V>,query:SourceSearchQuery<'_>,scope:SourceSearchScope<'_>,
        replacement:&str,run_policy:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredLiteralTextAtomCandidate<'static>,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let (output,receipt)={let prepared=self.prepare_literal_text_atom_candidate(provider,query,scope,replacement,run_policy,limits,writer,now)?;
            (prepared.output,prepared.receipt)};
        Ok(PreparedStoredLiteralTextAtomCandidate {source:LiteralSource::Owned(Box::new(self)),output,receipt})
    }
}
