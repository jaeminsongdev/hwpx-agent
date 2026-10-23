//! Owned source candidate only; actual current service/route checks remain required.
use super::super::ReferenceValidationProductOperation;
use domain_ir::{DocumentId, ReferenceAuxiliaryLimits};
use hwpx_package::{
    WriterLimits,
    document_import::{
        ImportedSourcePackage, SourceImportLimits,
        fields::{
            ImportedDocumentFields,
            semantics::source_index::{
                SourceFieldMeaningIndex,
                bookmark_updates::{
                    SourceBookmarkCommandCandidate, SourceBookmarkCommandChange,
                    SourceBookmarkCommandError as E,
                },
            },
        },
        forms::ImportedDocumentForms,
    },
};
impl ReferenceValidationProductOperation {
    /// # Errors
    /// Rejects source/selection/protection/coverage/budget/preservation drift.
    /// Does not overwrite source, update a cache, claim/store/publish or launch Native.
    pub fn prepare_source_bookmark_command_changes(
        bytes: &[u8],
        document: DocumentId,
        sha256: [u8; 32],
        source_limits: SourceImportLimits,
        limits: ReferenceAuxiliaryLimits,
        requests: &[SourceBookmarkCommandChange<'_>],
        writer: WriterLimits,
    ) -> Result<SourceBookmarkCommandCandidate, E> {
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
        let index = SourceFieldMeaningIndex::import(&fields, limits).map_err(|e| match e {
            hwpx_package::document_import::fields::semantics::FieldSemanticImportError::Limit => {
                E::Limit
            }
            _ => E::Source,
        })?;
        if requests.is_empty()
            || requests.len() > limits.config().items_per_kind
            || requests.len() > hwpx_package::PatchLimits::default().config().max_intents
        {
            return Err(E::Limit);
        }
        for request in requests {
            hwpx_package::document_import::reference_targets::sdk::authoring_display::PointBookmarkAuthoringDisplay::try_from(request.display)?;
        }
        let proof = forms
            .reconstruct_source_for_verification(bytes)
            .map_err(|_| E::Source)?;
        index.lower_bookmark_command_changes(&proof, requests, writer)
    }
}
