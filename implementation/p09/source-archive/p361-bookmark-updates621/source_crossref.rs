//! Read-only actual-source preparation; deliberately no CLI/MCP/raw action route.
use std::{collections::BTreeSet, fmt};

use domain_ir::{DocumentId, LogicalId, ReferenceAuxiliaryLimits};
use hwpx_package::{
    cross_reference_sdk::SdkCrossReferenceDisplay,
    document_import::{
        ImportedSourcePackage, SourceImportLimits,
        reference_targets::sdk::{
            SourceBoundCrossReferenceCandidate, SourceBoundCrossReferenceReceipt,
            SourceCrossReferenceContext, SourceCrossReferenceError,
        },
        structure::ImportedDocumentStructure,
    },
};
use serde::Serialize;
use thiserror::Error;

use super::ReferenceValidationProductOperation;

pub mod readback;
pub mod target_readback;
pub mod bookmark_bindings;
pub mod bookmark_cache_diagnostics;

#[derive(Clone)]
pub struct SourceCrossReferenceSelection {
    pub target_id: LogicalId,
    pub display: SdkCrossReferenceDisplay,
    pub hyperlink: bool,
}
impl fmt::Debug for SourceCrossReferenceSelection {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("SourceCrossReferenceSelection")
            .field("display", &self.display)
            .field("hyperlink", &self.hyperlink)
            .finish_non_exhaustive()
    }
}

pub struct SourceCrossReferencePreparation {
    source: ImportedDocumentStructure,
    candidates: Vec<SourceBoundCrossReferenceCandidate>,
}
impl fmt::Debug for SourceCrossReferencePreparation {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("SourceCrossReferencePreparation")
            .field("candidates", &self.candidates.len())
            .field("native_execution", &"not_run")
            .finish_non_exhaustive()
    }
}
impl SourceCrossReferencePreparation {
    #[must_use]
    pub fn candidates_for_discovery(&self) -> &[SourceBoundCrossReferenceCandidate] {
        &self.candidates
    }

    /// # Errors
    /// Performs one original whole-source/graph verification, not a cached hash
    /// comparison or one repeated reconstruction for each candidate.
    pub fn verify_source(&self, fresh: &[u8]) -> Result<(), SourceCrossReferencePreparationError> {
        self.source
            .verify_source(fresh)
            .map_err(|_| SourceCrossReferencePreparationError::Binding)?;
        Ok(())
    }

    /// Output contains binding receipts, never commands, names, raw selectors or
    /// document contents. Native qualification remains required for every row.
    /// # Errors
    /// Rejects excessive output; no partial/truncated success is returned.
    pub fn canonical_receipts_json(
        &self,
        limits: ReferenceAuxiliaryLimits,
    ) -> Result<Vec<u8>, SourceCrossReferencePreparationError> {
        #[derive(Serialize)]
        struct Output<'a> {
            schema_version: &'static str,
            status: &'static str,
            candidates: Vec<&'a SourceBoundCrossReferenceReceipt>,
        }
        let output = Output {
            schema_version: "hwpx-agent.product.source-crossref-discovery-preparation/v1",
            status: "native_execution_not_run",
            candidates: self
                .candidates
                .iter()
                .map(SourceBoundCrossReferenceCandidate::receipt)
                .collect(),
        };
        let bytes =
            serde_json::to_vec(&output).map_err(|_| SourceCrossReferencePreparationError::Limit)?;
        if bytes.len() > limits.config().output_bytes {
            return Err(SourceCrossReferencePreparationError::Limit);
        }
        Ok(bytes)
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum SourceCrossReferencePreparationError {
    #[error("SOURCE_CROSS_REFERENCE_PREPARATION_INPUT_REJECTED")]
    Source,
    #[error("SOURCE_CROSS_REFERENCE_PREPARATION_BINDING_REJECTED")]
    Binding,
    #[error("SOURCE_CROSS_REFERENCE_PREPARATION_LIMIT")]
    Limit,
    #[error("SOURCE_CROSS_REFERENCE_PREPARATION_EMPTY_OR_DUPLICATE_SELECTION")]
    Selection,
    #[error("SOURCE_CROSS_REFERENCE_PREPARATION_TARGET_REJECTED")]
    Target,
}

impl ReferenceValidationProductOperation {
    /// Imports one actual package/structure/index for a whole all-or-nothing
    /// preparation batch. Does not create/save/update/execute any document.
    /// # Errors
    /// Rejects source drift, unsupported coverage, forged/missing/ambiguous or
    /// native-unqualified targets, duplicate selections and aggregate budgets.
    pub fn prepare_source_crossref_discovery(
        bytes: &[u8],
        document_id: DocumentId,
        expected_package_sha256: [u8; 32],
        source_limits: SourceImportLimits,
        reference_limits: ReferenceAuxiliaryLimits,
        selections: &[SourceCrossReferenceSelection],
    ) -> Result<SourceCrossReferencePreparation, SourceCrossReferencePreparationError> {
        if selections.is_empty() {
            return Err(SourceCrossReferencePreparationError::Selection);
        }
        if selections.len() > reference_limits.config().items_per_kind {
            return Err(SourceCrossReferencePreparationError::Limit);
        }
        let package = ImportedSourcePackage::import(
            bytes,
            document_id,
            expected_package_sha256,
            source_limits,
        )
        .map_err(|e| match e {
            hwpx_package::document_import::SourceImportError::SourceChanged => {
                SourceCrossReferencePreparationError::Binding
            }
            hwpx_package::document_import::SourceImportError::Limit => {
                SourceCrossReferencePreparationError::Limit
            }
            _ => SourceCrossReferencePreparationError::Source,
        })?;
        let source = ImportedDocumentStructure::import(package)
            .map_err(|_| SourceCrossReferencePreparationError::Source)?;
        let context = SourceCrossReferenceContext::import(&source, reference_limits)
            .map_err(map_target_error)?;
        let mut seen = BTreeSet::new();
        let mut candidates = Vec::new();
        let mut total = 256usize; // Fixed response wrapper plus structural punctuation.
        for selection in selections {
            let display = match selection.display {
                SdkCrossReferenceDisplay::Page => 0,
                SdkCrossReferenceDisplay::ObjectNumber => 1,
                SdkCrossReferenceDisplay::BookmarkName => 2,
                SdkCrossReferenceDisplay::Content => 3,
                SdkCrossReferenceDisplay::RelativePosition => 4,
            };
            if !seen.insert((&selection.target_id, display, selection.hyperlink)) {
                return Err(SourceCrossReferencePreparationError::Selection);
            }
            let candidate = context
                .prepare(&selection.target_id, selection.display, selection.hyperlink)
                .map_err(map_target_error)?;
            let receipt_bytes = serde_json::to_vec(candidate.receipt())
                .map_err(|_| SourceCrossReferencePreparationError::Limit)?;
            total = total
                .checked_add(receipt_bytes.len())
                .and_then(|n| n.checked_add(candidate.command_for_discovery().len()))
                .and_then(|n| n.checked_add(1))
                .filter(|n| *n <= reference_limits.config().output_bytes)
                .ok_or(SourceCrossReferencePreparationError::Limit)?;
            candidates
                .try_reserve(1)
                .map_err(|_| SourceCrossReferencePreparationError::Limit)?;
            candidates.push(candidate);
        }
        Ok(SourceCrossReferencePreparation { source, candidates })
    }
}

fn map_target_error(error: SourceCrossReferenceError) -> SourceCrossReferencePreparationError {
    match error {
        SourceCrossReferenceError::Limit => SourceCrossReferencePreparationError::Limit,
        SourceCrossReferenceError::Binding => SourceCrossReferencePreparationError::Binding,
        _ => SourceCrossReferencePreparationError::Target,
    }
}
