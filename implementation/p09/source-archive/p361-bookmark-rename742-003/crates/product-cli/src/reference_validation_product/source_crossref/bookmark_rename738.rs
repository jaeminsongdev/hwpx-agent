//! Owned atomic rename candidate; no current service/Native/registry/publication grant.
use super::super::ReferenceValidationProductOperation;
use domain_ir::{DocumentId,ReferenceAuxiliaryLimits};
use hwpx_package::{WriterLimits,document_import::{ImportedSourcePackage,SourceImportLimits,forms::ImportedDocumentForms,
    fields::{ImportedDocumentFields,bookmark_authoring_targets::SourceBookmarkAuthoringContext}}};
pub use hwpx_package::document_import::fields::bookmark_authoring_targets::rename737::{BookmarkRenameRequest,BookmarkRenameError,BookmarkRenameReceipt,SourceBookmarkRenameCandidate};
impl ReferenceValidationProductOperation{
    /// # Errors
    /// Rejects source/target/name/protection/parameter/budget/preservation drift atomically.
    /// Does not overwrite a file, refresh fields, claim a revision or activate Native.
    pub fn prepare_source_bookmark_rename(bytes:&[u8],document:DocumentId,sha256:[u8;32],source_limits:SourceImportLimits,
        limits:ReferenceAuxiliaryLimits,request:BookmarkRenameRequest<'_>,writer:WriterLimits)->Result<SourceBookmarkRenameCandidate,BookmarkRenameError>{
        let source=ImportedSourcePackage::import(bytes,document,sha256,source_limits).map_err(|_|BookmarkRenameError::Source)?;
        let forms=ImportedDocumentForms::import(source).map_err(|_|BookmarkRenameError::Source)?;
        let fields=ImportedDocumentFields::import(&forms).map_err(|_|BookmarkRenameError::Source)?;
        super::super::source::check_whole_source_field_coverage(forms.body_structure(),&fields,limits).map_err(|_|BookmarkRenameError::Source)?;
        let context=SourceBookmarkAuthoringContext::import(&fields,limits).map_err(|_|BookmarkRenameError::Target)?;
        let proof=forms.reconstruct_source_for_verification(bytes).map_err(|_|BookmarkRenameError::Source)?;
        context.rename_target_and_crossrefs(&proof,request,writer)
    }
}
