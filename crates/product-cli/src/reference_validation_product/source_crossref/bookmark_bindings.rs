//! Read-only real-package Command binding; no saved permit, Native or raw action route.
use super::super::ReferenceValidationProductOperation;
use domain_ir::{DocumentId, ReferenceAuxiliaryLimits};
use hwpx_package::document_import::{
    ImportedSourcePackage, SourceImportLimits,
    fields::{
        ImportedDocumentFields,
        bookmark_crossref::{BookmarkCrossReferenceError, SourceBookmarkCrossReferenceBindings},
    },
    forms::ImportedDocumentForms,
};
use thiserror::Error;

#[derive(Clone, Copy, Debug, Eq, PartialEq, Error)]
pub enum SourceBookmarkCrossReferenceProductError {
    #[error("PRODUCT_SOURCE_BOOKMARK_CROSSREF_SOURCE_REJECTED")]
    Source,
    #[error("PRODUCT_SOURCE_BOOKMARK_CROSSREF_SHA_REJECTED")]
    Binding,
    #[error("PRODUCT_SOURCE_BOOKMARK_CROSSREF_LIMIT")]
    Limit,
    #[error("PRODUCT_SOURCE_BOOKMARK_CROSSREF_PARAMETERS_REJECTED")]
    Parameters,
    #[error("PRODUCT_SOURCE_BOOKMARK_CROSSREF_KIND_UNQUALIFIED")]
    UnqualifiedKind,
}
impl ReferenceValidationProductOperation {
    /// Imports the package/forms/fields once and derives every binding from the
    /// same immutable source and indexed bookmark targets. Never accepts names,
    /// commands, target maps, caller graphs, Native approval or cached results.
    /// # Errors
    /// Rejects original coverage/SHA/field failures, non-Command/malformed values,
    /// unsupported target kinds and output/work limits. Missing/ambiguous source
    /// bookmarks are typed diagnostic outcomes, not a silent first match.
    pub fn read_source_bookmark_crossrefs(
        bytes: &[u8],
        document: DocumentId,
        expected_sha256: [u8; 32],
        source_limits: SourceImportLimits,
        limits: ReferenceAuxiliaryLimits,
    ) -> Result<SourceBookmarkCrossReferenceBindings, SourceBookmarkCrossReferenceProductError>
    {
        use SourceBookmarkCrossReferenceProductError as E;
        let package =
            ImportedSourcePackage::import(bytes, document, expected_sha256, source_limits)
                .map_err(|error| match error {
                    hwpx_package::document_import::SourceImportError::SourceChanged => E::Binding,
                    hwpx_package::document_import::SourceImportError::Limit => E::Limit,
                    _ => E::Source,
                })?;
        let forms = ImportedDocumentForms::import(package).map_err(|_| E::Source)?;
        let fields = ImportedDocumentFields::import(&forms).map_err(|_| E::Source)?;
        super::super::source::check_whole_source_field_coverage(
            forms.body_structure(),
            &fields,
            limits,
        )
        .map_err(|_| E::Source)?;
        SourceBookmarkCrossReferenceBindings::import(&fields, limits).map_err(|error| match error {
            BookmarkCrossReferenceError::Limit => E::Limit,
            BookmarkCrossReferenceError::Parameter | BookmarkCrossReferenceError::Command => {
                E::Parameters
            }
            BookmarkCrossReferenceError::UnqualifiedKind => E::UnqualifiedKind,
            _ => E::Source,
        })
    }
}
