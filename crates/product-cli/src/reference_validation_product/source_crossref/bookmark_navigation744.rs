//! Whole-source field-to-cursor binding; application cursor execution is not granted here.
use super::super::ReferenceValidationProductOperation;
use domain_ir::{DocumentId,LogicalId,ReferenceAuxiliaryLimits};
use hwpx_package::document_import::{ImportedSourcePackage,SourceImportLimits,forms::ImportedDocumentForms,
    fields::{ImportedDocumentFields,bookmark_authoring_targets::SourceBookmarkAuthoringContext}};
pub use hwpx_package::document_import::fields::bookmark_authoring_targets::navigation743::{BookmarkNavigationError,
    BookmarkNavigationStatus,BookmarkNavigationReceipt,BookmarkSourceDestination,BookmarkNavigationResult,PreparedBookmarkNavigation};
impl ReferenceValidationProductOperation{
    /// # Errors
    /// Fresh source/whole field coverage precedes selection and strict Command/RefPath resolution.
    pub fn prepare_source_bookmark_navigation(bytes:&[u8],document:DocumentId,sha256:[u8;32],source_limits:SourceImportLimits,
        limits:ReferenceAuxiliaryLimits,selected_fields:&[LogicalId])->Result<PreparedBookmarkNavigation,BookmarkNavigationError>{
        let source=ImportedSourcePackage::import(bytes,document,sha256,source_limits).map_err(|_|BookmarkNavigationError::Source)?;
        let forms=ImportedDocumentForms::import(source).map_err(|_|BookmarkNavigationError::Source)?;
        let fields=ImportedDocumentFields::import(&forms).map_err(|_|BookmarkNavigationError::Source)?;
        super::super::source::check_whole_source_field_coverage(forms.body_structure(),&fields,limits).map_err(|_|BookmarkNavigationError::Source)?;
        let context=SourceBookmarkAuthoringContext::import(&fields,limits).map_err(|_|BookmarkNavigationError::Target)?;
        context.prepare_navigation(bytes,selected_fields)
    }
}
