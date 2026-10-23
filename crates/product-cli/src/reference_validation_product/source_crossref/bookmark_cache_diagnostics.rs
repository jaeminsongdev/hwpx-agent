//! One admitted package/fields import for source-only bookmark name diagnostics.
use super::super::ReferenceValidationProductOperation;
use super::bookmark_bindings::SourceBookmarkCrossReferenceProductError as Error;
use domain_ir::{DocumentId, ReferenceAuxiliaryLimits};
use hwpx_package::document_import::{
    ImportedSourcePackage, SourceImportError, SourceImportLimits,
    fields::{
        FieldRangeImportError, ImportedDocumentFields,
        bookmark_crossref::{
            BookmarkCrossReferenceError, SourceBookmarkCrossReferenceBindings,
            cache_diagnostics::SourceBookmarkNameCacheDiagnostics,
        },
        cached_source::{FieldCachedSourceError, SourceFieldCachedInlines},
    },
    forms::ImportedDocumentForms,
};
impl ReferenceValidationProductOperation {
    /// Pure read-only diagnostics; no caller names/maps, writes, native action,
    /// source overwrite, policy/current-head or cache-currentness authority.
    /// # Errors
    /// Keeps exact SHA, whole-field coverage and finite budget checks.
    pub fn diagnose_source_bookmark_name_caches(
        bytes: &[u8],
        document: DocumentId,
        sha256: [u8; 32],
        source_limits: SourceImportLimits,
        limits: ReferenceAuxiliaryLimits,
    ) -> Result<SourceBookmarkNameCacheDiagnostics, Error> {
        let package = ImportedSourcePackage::import(bytes, document, sha256, source_limits)
            .map_err(|e| match e {
                SourceImportError::SourceChanged => Error::Binding,
                SourceImportError::Limit => Error::Limit,
                _ => Error::Source,
            })?;
        let forms = ImportedDocumentForms::import(package).map_err(|_| Error::Source)?;
        let fields = ImportedDocumentFields::import(&forms).map_err(|e| match e {
            FieldRangeImportError::Limit => Error::Limit,
            _ => Error::Source,
        })?;
        super::super::source::check_whole_source_field_coverage(
            forms.body_structure(),
            &fields,
            limits,
        )
        .map_err(|e| match e {
            super::super::source::ReferenceSourceError::InputLimit => Error::Limit,
            _ => Error::Source,
        })?;
        let caches = SourceFieldCachedInlines::import(&fields, limits).map_err(|e| match e {
            FieldCachedSourceError::Limit => Error::Limit,
            _ => Error::Source,
        })?;
        let bindings =
            SourceBookmarkCrossReferenceBindings::import(&fields, limits).map_err(map)?;
        bindings
            .diagnose_cached_source(&caches, limits)
            .map_err(map)
    }
}
fn map(e: BookmarkCrossReferenceError) -> Error {
    match e {
        BookmarkCrossReferenceError::Limit => Error::Limit,
        BookmarkCrossReferenceError::Binding => Error::Binding,
        BookmarkCrossReferenceError::Parameter | BookmarkCrossReferenceError::Command => {
            Error::Parameters
        }
        BookmarkCrossReferenceError::UnqualifiedKind => Error::UnqualifiedKind,
        _ => Error::Source,
    }
}
