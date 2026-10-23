//! First source insertion candidate, never a bypass of the service/Native route.
use super::super::ReferenceValidationProductOperation;
use domain_ir::{DocumentId, ReferenceAuxiliaryLimits};
use hwpx_package::{
    WriterLimits,
    document_import::{
        ImportedSourcePackage, SourceImportLimits,
        fields::{
            ImportedDocumentFields,
            bookmark_insertion::{
                SourceBookmarkInsertion, SourceBookmarkInsertionError as E,
                generated::SourceBookmarkCreationCandidate,
            },
        },
        forms::ImportedDocumentForms,
    },
};
impl ReferenceValidationProductOperation {
    /// # Errors
    /// Fresh source/coverage/target/selection/protection/limits/preservation and
    /// complete parameter readback are required. No overwrite/store/job/Native.
    pub fn prepare_source_bookmark_reference_insertion(
        bytes: &[u8],
        document: DocumentId,
        sha256: [u8; 32],
        source_limits: SourceImportLimits,
        limits: ReferenceAuxiliaryLimits,
        request: SourceBookmarkInsertion<'_>,
        writer: WriterLimits,
    ) -> Result<SourceBookmarkCreationCandidate, E> {
        let source = ImportedSourcePackage::import(bytes, document, sha256, source_limits)
            .map_err(|_| E::Source)?;
        let forms = ImportedDocumentForms::import(source).map_err(|_| E::Source)?;
        let fields = ImportedDocumentFields::import(&forms).map_err(|_| E::Source)?;
        super::super::source::check_whole_source_field_coverage(
            forms.body_structure(),
            &fields,
            limits,
        )
        .map_err(|_| E::Source)?;
        let proof = forms
            .reconstruct_source_for_verification(bytes)
            .map_err(|_| E::Source)?;
        fields.create_bookmark_reference(&proof, request, limits, writer)
    }
}
