//! Source-local bookmark observations across different package snapshots.
//! A matching name is not native resolution, causal preservation or authority.
use std::{collections::BTreeMap, fmt, io};

use domain_ir::{ReferenceAuxiliaryLimits, ReferenceTargetKind};
use hwpx_package::document_import::{
    ImportedSourcePackage, SourceImportError, SourceImportLimits,
    reference_targets::{
        ImportedReferenceTargets, ReferenceTargetImportError, ReferenceTargetImportReceipt,
    },
    structure::ImportedDocumentStructure,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};

use super::{SourceCrossReferencePreparation, SourceCrossReferencePreparationError as Error};

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum BookmarkTargetObservation {
    UniqueExactNameObserved,
    NotObserved,
    AmbiguousExactName,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct CandidateBookmarkTargetObservation {
    expected_candidate_receipt_sha256: [u8; 32],
    expected_source_logical_target_id_sha256: [u8; 32],
    exact_decoded_source_name_sha256: [u8; 32],
    observation: BookmarkTargetObservation,
    observed_source_logical_target_id_sha256: Option<[u8; 32]>,
    observed_source_target_state_sha256: Option<String>,
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct SourceCrossReferenceTargetObservations {
    schema_version: &'static str,
    status: &'static str,
    prepared_source_package_sha256: [u8; 32],
    observed_targets: ReferenceTargetImportReceipt,
    candidates: Vec<CandidateBookmarkTargetObservation>,
    native_execution_attested: bool,
    native_target_resolution_qualified: bool,
    causal_insertion_or_preservation_proved: bool,
    complete_reference_validation_qualified: bool,
}
impl fmt::Debug for SourceCrossReferenceTargetObservations {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("SourceCrossReferenceTargetObservations")
            .field("candidates", &self.candidates.len())
            .field("scope", &"source_target_observation_only")
            .finish_non_exhaustive()
    }
}
impl SourceCrossReferenceTargetObservations {
    /// # Errors
    /// Bounded serialization never allocates a complete over-limit JSON output.
    pub fn canonical_json(&self, limits: ReferenceAuxiliaryLimits) -> Result<Vec<u8>, Error> {
        let mut writer = BudgetVec {
            bytes: Vec::new(),
            maximum: limits.config().output_bytes,
        };
        serde_json::to_writer(&mut writer, self).map_err(|_| Error::Limit)?;
        Ok(writer.bytes)
    }
}

impl SourceCrossReferencePreparation {
    /// Imports one actual output structure and name index for the entire batch.
    /// Expected names come only from this preparation's immutable source and
    /// candidates. There is no caller-supplied name/target/state/graph mapping.
    /// Changed source-local logical IDs are reported, not equated across saves.
    ///
    /// # Errors
    /// Rejects SHA drift, unsupported target coverage, invalid bindings and
    /// finite source/work/text/output limits. Missing/ambiguous names are distinct
    /// observations, never a first-match target or native qualification.
    pub fn observe_bookmark_targets_in_output(
        &self,
        output: &[u8],
        expected_output_sha256: [u8; 32],
        source_limits: SourceImportLimits,
        reference_limits: ReferenceAuxiliaryLimits,
    ) -> Result<SourceCrossReferenceTargetObservations, Error> {
        self.check_target_observation_budget(reference_limits)?;
        let package = ImportedSourcePackage::import(
            output,
            self.source.source().document_id().clone(),
            expected_output_sha256,
            source_limits,
        )
        .map_err(|error| match error {
            SourceImportError::SourceChanged => Error::Binding,
            SourceImportError::Limit => Error::Limit,
            _ => Error::Source,
        })?;
        let observed = ImportedDocumentStructure::import(package).map_err(|_| Error::Source)?;
        self.observe_bookmark_targets_from_structure(&observed, reference_limits)
    }

    pub(super) fn check_target_observation_budget(
        &self,
        reference_limits: ReferenceAuxiliaryLimits,
    ) -> Result<(), Error> {
        let config = reference_limits.config();
        if self.candidates.len() > config.items_per_kind
            || self.source.bookmarks().len() > config.items_per_kind
            || self
                .candidates
                .len()
                .checked_mul(512)
                .is_none_or(|n| n > config.output_bytes)
        {
            return Err(Error::Limit);
        }
        Ok(())
    }

    pub(super) fn observe_bookmark_targets_from_structure(
        &self,
        observed: &ImportedDocumentStructure,
        reference_limits: ReferenceAuxiliaryLimits,
    ) -> Result<SourceCrossReferenceTargetObservations, Error> {
        self.check_target_observation_budget(reference_limits)?;
        if observed.source().document_id() != self.source.source().document_id() {
            return Err(Error::Binding);
        }
        let config = reference_limits.config();
        let targets =
            ImportedReferenceTargets::import(observed, reference_limits).map_err(|e| match e {
                ReferenceTargetImportError::Limit => Error::Limit,
                _ => Error::Source,
            })?;
        let mut original = BTreeMap::new();
        for bookmark in self.source.bookmarks() {
            if bookmark.name.len() > config.text_bytes {
                return Err(Error::Limit);
            }
            let key: [u8; 32] = Sha256::digest(bookmark.reference_id.as_str().as_bytes()).into();
            if original.insert(key, bookmark).is_some() {
                return Err(Error::Binding);
            }
        }
        let mut candidates = Vec::new();
        for candidate in &self.candidates {
            let source_id = candidate.source_logical_target_id_sha256();
            let expected = original.get(&source_id).ok_or(Error::Binding)?;
            let (observation, observed_id, state) = match targets
                .by_exact_source_name(&expected.name)
            {
                Ok(target) => {
                    if target.target_kind != ReferenceTargetKind::Bookmark {
                        return Err(Error::Binding);
                    }
                    (
                        BookmarkTargetObservation::UniqueExactNameObserved,
                        Some(Sha256::digest(target.logical_target_id.as_str().as_bytes()).into()),
                        Some(target.target_state_sha256.clone()),
                    )
                }
                Err(ReferenceTargetImportError::Missing) => {
                    (BookmarkTargetObservation::NotObserved, None, None)
                }
                Err(ReferenceTargetImportError::Ambiguous) => {
                    (BookmarkTargetObservation::AmbiguousExactName, None, None)
                }
                Err(_) => return Err(Error::Binding),
            };
            let receipt = serde_json::to_vec(candidate.receipt()).map_err(|_| Error::Limit)?;
            candidates.try_reserve(1).map_err(|_| Error::Limit)?;
            candidates.push(CandidateBookmarkTargetObservation {
                expected_candidate_receipt_sha256: Sha256::digest(receipt).into(),
                expected_source_logical_target_id_sha256: source_id,
                exact_decoded_source_name_sha256: Sha256::digest(expected.name.as_bytes()).into(),
                observation,
                observed_source_logical_target_id_sha256: observed_id,
                observed_source_target_state_sha256: state,
            });
        }
        let result = SourceCrossReferenceTargetObservations {
            schema_version: "hwpx-agent.product.source-crossref-target-observations/v1",
            status: "source_target_observation_only",
            prepared_source_package_sha256: self.source.receipt().source_package_sha256,
            observed_targets: targets.receipt().clone(),
            candidates,
            native_execution_attested: false,
            native_target_resolution_qualified: false,
            causal_insertion_or_preservation_proved: false,
            complete_reference_validation_qualified: false,
        };
        // Enforce the actual aggregate JSON budget without creating/discarding a full copy.
        let mut count = BudgetCount {
            written: 0,
            maximum: config.output_bytes,
        };
        serde_json::to_writer(&mut count, &result).map_err(|_| Error::Limit)?;
        Ok(result)
    }
}

pub(super) struct BudgetCount {
    pub(super) written: usize,
    pub(super) maximum: usize,
}
impl io::Write for BudgetCount {
    fn write(&mut self, bytes: &[u8]) -> io::Result<usize> {
        self.written = self
            .written
            .checked_add(bytes.len())
            .filter(|n| *n <= self.maximum)
            .ok_or_else(|| io::Error::other("SOURCE_TARGET_OBSERVATION_OUTPUT_LIMIT"))?;
        Ok(bytes.len())
    }
    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}
pub(super) struct BudgetVec {
    pub(super) bytes: Vec<u8>,
    pub(super) maximum: usize,
}
impl io::Write for BudgetVec {
    fn write(&mut self, bytes: &[u8]) -> io::Result<usize> {
        let next = self
            .bytes
            .len()
            .checked_add(bytes.len())
            .filter(|n| *n <= self.maximum)
            .ok_or_else(|| io::Error::other("SOURCE_TARGET_OBSERVATION_OUTPUT_LIMIT"))?;
        self.bytes
            .try_reserve(next - self.bytes.len())
            .map_err(|_| io::Error::other("SOURCE_TARGET_OBSERVATION_OUTPUT_LIMIT"))?;
        self.bytes.extend_from_slice(bytes);
        Ok(bytes.len())
    }
    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}
