//! Reads an actual output package once for all prepared discovery candidates.
use std::fmt;

use domain_ir::ReferenceAuxiliaryLimits;
use hwpx_package::document_import::{
    ImportedSourcePackage, SourceImportError, SourceImportLimits,
    fields::{
        ImportedDocumentFields,
        cross_reference_observation::{
            CrossReferenceCommandObservations, CrossReferenceObservationError,
        },
    },
    forms::ImportedDocumentForms,
};
use serde::Serialize;

use super::{SourceCrossReferencePreparation, SourceCrossReferencePreparationError as Error};
use super::target_readback::{BudgetCount, BudgetVec, SourceCrossReferenceTargetObservations};

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct SourceCrossReferenceOutputObservations {
    schema_version: &'static str,
    status: &'static str,
    prepared_source_package_sha256: [u8; 32],
    observed_source_package_sha256: [u8; 32],
    commands: CrossReferenceCommandObservations,
    targets: SourceCrossReferenceTargetObservations,
    native_execution_attested: bool,
    native_target_resolution_qualified: bool,
    causal_insertion_or_preservation_proved: bool,
    complete_reference_validation_qualified: bool,
}
impl fmt::Debug for SourceCrossReferenceOutputObservations {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("SourceCrossReferenceOutputObservations(<redacted>; one_source_snapshot_only)")
    }
}
impl SourceCrossReferenceOutputObservations {
    #[must_use]
    pub const fn commands(&self) -> &CrossReferenceCommandObservations {
        &self.commands
    }
    #[must_use]
    pub const fn targets(&self) -> &SourceCrossReferenceTargetObservations {
        &self.targets
    }
    /// # Errors
    /// Applies one aggregate output limit; never allocates an over-limit copy.
    pub fn canonical_json(&self, limits: ReferenceAuxiliaryLimits) -> Result<Vec<u8>, Error> {
        let mut writer = BudgetVec { bytes: Vec::new(), maximum: limits.config().output_bytes };
        serde_json::to_writer(&mut writer, self).map_err(|_| Error::Limit)?;
        Ok(writer.bytes)
    }
}

impl SourceCrossReferencePreparation {
    /// Joins original command and bookmark observations from one immutable output.
    /// Neither side can come from another package, caller mapping or native state.
    /// The existing separate methods and all their checks remain available.
    ///
    /// # Errors
    /// Rejects SHA drift, original form/field/target coverage failures and aggregate
    /// source/work/output limits. A literal match is not native resolution or causality.
    pub fn observe_output_for_discovery(
        &self,
        output: &[u8],
        expected_output_sha256: [u8; 32],
        source_limits: SourceImportLimits,
        reference_limits: ReferenceAuxiliaryLimits,
    ) -> Result<SourceCrossReferenceOutputObservations, Error> {
        self.check_target_observation_budget(reference_limits)?;
        let package = ImportedSourcePackage::import(
            output, self.source.source().document_id().clone(), expected_output_sha256, source_limits,
        ).map_err(|error| match error {
            SourceImportError::SourceChanged => Error::Binding,
            SourceImportError::Limit => Error::Limit,
            _ => Error::Source,
        })?;
        let forms = ImportedDocumentForms::import(package).map_err(|_| Error::Source)?;
        let fields = ImportedDocumentFields::import(&forms).map_err(|_| Error::Source)?;
        let commands = CrossReferenceCommandObservations::inspect(&fields, &self.candidates, reference_limits)
            .map_err(|error| match error {
                CrossReferenceObservationError::Limit => Error::Limit,
                CrossReferenceObservationError::Binding => Error::Binding,
                _ => Error::Source,
            })?;
        let targets = self.observe_bookmark_targets_from_structure(forms.body_structure(), reference_limits)?;
        let result = SourceCrossReferenceOutputObservations {
            schema_version: "hwpx-agent.product.source-crossref-output-observations/v1",
            status: "source_output_observation_only",
            prepared_source_package_sha256: self.source.receipt().source_package_sha256,
            observed_source_package_sha256: forms.source().receipt().source_package_sha256,
            commands, targets,
            native_execution_attested: false,
            native_target_resolution_qualified: false,
            causal_insertion_or_preservation_proved: false,
            complete_reference_validation_qualified: false,
        };
        let mut count = BudgetCount { written: 0, maximum: reference_limits.config().output_bytes };
        serde_json::to_writer(&mut count, &result).map_err(|_| Error::Limit)?;
        Ok(result)
    }

    /// Observes literal command strings in actual source CROSSREF fields, without
    /// assuming a parameter key, causal insertion, preservation or native action.
    /// The source document namespace is retained, but a native current-window/
    /// service-head binding is not attested by supplied package bytes.
    ///
    /// # Errors
    /// Rejects package SHA drift, original form/field admission failures, uncovered
    /// CROSSREF markers and work/output budgets. No package is written or repaired.
    pub fn observe_crossref_output(
        &self,
        output: &[u8],
        expected_output_sha256: [u8; 32],
        source_limits: SourceImportLimits,
        reference_limits: ReferenceAuxiliaryLimits,
    ) -> Result<CrossReferenceCommandObservations, Error> {
        let source = ImportedSourcePackage::import(
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
        let forms = ImportedDocumentForms::import(source).map_err(|_| Error::Source)?;
        let fields = ImportedDocumentFields::import(&forms).map_err(|_| Error::Source)?;
        CrossReferenceCommandObservations::inspect(&fields, &self.candidates, reference_limits)
            .map_err(|error| match error {
                CrossReferenceObservationError::Limit => Error::Limit,
                CrossReferenceObservationError::Binding => Error::Binding,
                _ => Error::Source,
            })
    }
}
