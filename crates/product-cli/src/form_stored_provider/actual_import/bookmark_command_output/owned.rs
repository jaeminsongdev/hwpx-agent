//! Same source ownership transfer as HTTPS; no clone or second lowering.
use super::*;
pub(super) enum BookmarkSource<'a> {
    Borrowed(&'a StoredImportedDocumentForms),
    Owned(Box<StoredImportedDocumentForms>),
}
impl std::ops::Deref for BookmarkSource<'_> {
    type Target = StoredImportedDocumentForms;
    fn deref(&self) -> &Self::Target {
        match self {
            Self::Borrowed(v) => v,
            Self::Owned(v) => v,
        }
    }
}
impl StoredImportedDocumentForms {
    pub(crate) fn into_bookmark_command_candidate<R, B, S, V>(
        self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        requests: &[SourceBookmarkCommandChange<'_>],
        limits: ReferenceAuxiliaryLimits,
        writer: WriterLimits,
        now: u64,
    ) -> Result<PreparedStoredBookmarkCommandCandidate<'static>, E>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        let (output, receipt, anchors, denied) = {
            let candidate =
                self.prepare_bookmark_command_candidate(provider, requests, limits, writer, now)?;
            (
                candidate.output,
                candidate.receipt,
                candidate.anchors,
                candidate.denied,
            )
        };
        Ok(PreparedStoredBookmarkCommandCandidate {
            source: BookmarkSource::Owned(Box::new(self)),
            output,
            receipt,
            anchors,
            denied,
        })
    }
}
