//! Read-only source text oracle and actual field readback, no cache-as-layout inference.
use super::ReferenceValidationProductOperation;
use domain_ir::{DocumentId,ReferenceAuxiliaryLimits};
use hwpx_package::document_import::{ImportedSourcePackage,SourceImportLimits,forms::ImportedDocumentForms,
    fields::{ImportedDocumentFields,bookmark_authoring_targets::SourceBookmarkAuthoringContext}};
pub use hwpx_package::document_import::fields::bookmark_authoring_targets::result726::{BookmarkResultSelection,
    BookmarkResultError,BookmarkResultStatus,BookmarkResultAssessment,PreparedBookmarkResultExpectation};
pub use hwpx_package::document_import::fields::bookmark_authoring_targets::result726::single_page731::{
    SinglePageObservation,SinglePageResultStatus,SinglePageResultAssessment};
impl ReferenceValidationProductOperation{
    /// # Errors
    /// Conditional source-layout interpretation only; capture provenance and locale
    /// must be verified by the host. Caller metadata never grants Native authority.
    pub fn assess_source_bookmark_single_page(expectation:&PreparedBookmarkResultExpectation,original_fresh:&[u8],actual:&[u8],
        document:DocumentId,sha256:[u8;32],source_limits:SourceImportLimits,observation:&SinglePageObservation)
        ->Result<SinglePageResultAssessment,BookmarkResultError>{
        expectation.verify_original(original_fresh)?;
        let source=ImportedSourcePackage::import(actual,document,sha256,source_limits).map_err(|_|BookmarkResultError::Source)?;
        let forms=ImportedDocumentForms::import(source).map_err(|_|BookmarkResultError::Source)?;
        let fields=ImportedDocumentFields::import(&forms).map_err(|_|BookmarkResultError::Source)?;
        expectation.assess_single_page_observation(original_fresh,&fields,actual,observation)
    }
    /// Imports the original only once and reconstructs it once for a bounded batch of private oracles.
    /// # Errors
    /// Expected text is source-derived; no expected hash/text, layout assertion or Native receipt input.
    pub fn prepare_source_bookmark_result_expectations(bytes:&[u8],document:DocumentId,sha256:[u8;32],
        source_limits:SourceImportLimits,limits:ReferenceAuxiliaryLimits,selections:&[BookmarkResultSelection])
        ->Result<Vec<PreparedBookmarkResultExpectation>,BookmarkResultError>{
        let source=ImportedSourcePackage::import(bytes,document,sha256,source_limits).map_err(|_|BookmarkResultError::Source)?;
        let forms=ImportedDocumentForms::import(source).map_err(|_|BookmarkResultError::Source)?;
        let fields=ImportedDocumentFields::import(&forms).map_err(|_|BookmarkResultError::Source)?;
        let context=SourceBookmarkAuthoringContext::import(&fields,limits).map_err(|_|BookmarkResultError::Target)?;
        context.prepare_result_expectations(bytes,selections)
    }
    /// # Errors
    /// Current bytes must match both immutable originals. No document/field update, Native or publication occurs.
    pub fn assess_source_bookmark_result(expectation:&PreparedBookmarkResultExpectation,original_fresh:&[u8],actual:&[u8],
        document:DocumentId,sha256:[u8;32],source_limits:SourceImportLimits)->Result<BookmarkResultAssessment,BookmarkResultError>{
        expectation.verify_original(original_fresh)?;
        let source=ImportedSourcePackage::import(actual,document,sha256,source_limits).map_err(|_|BookmarkResultError::Source)?;
        let forms=ImportedDocumentForms::import(source).map_err(|_|BookmarkResultError::Source)?;
        let fields=ImportedDocumentFields::import(&forms).map_err(|_|BookmarkResultError::Source)?;
        expectation.assess(original_fresh,&fields,actual)
    }
}
