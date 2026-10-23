//! Uninterpreted source observations for discovery, never a native success.
//! Matches decoded direct string leaves without assuming any parameter key.
use std::{
    collections::{BTreeMap, BTreeSet},
    fmt,
};

use domain_ir::ReferenceAuxiliaryLimits;
use quick_xml::escape::unescape;
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use super::ImportedDocumentFields;
use crate::{
    HANCOM_2020_PARAGRAPH_NAMESPACE as HP,
    document_import::reference_targets::sdk::SourceBoundCrossReferenceCandidate,
};

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CommandLeafObservation {
    NotObserved,
    SingleDecodedLeafObserved,
    AmbiguousDecodedLeaves,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct CandidateCommandObservation {
    expected_candidate_receipt_sha256: [u8; 32],
    observation: CommandLeafObservation,
    matching_leaves: usize,
    matching_fields: usize,
    shares_field_with_other_candidates: bool,
    only_matching_field_reference_sha256: Option<[u8; 32]>,
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct CrossReferenceCommandObservations {
    schema_version: &'static str,
    status: &'static str,
    observed_source_package_sha256: [u8; 32],
    observed_field_graph_sha256: [u8; 32],
    crossref_fields: usize,
    plain_string_leaves: usize,
    opaque_parameter_children: usize,
    crossrefs_without_parameters: usize,
    candidates: Vec<CandidateCommandObservation>,
    parameter_key_semantics_qualified: bool,
    native_execution_attested: bool,
    causal_insertion_or_preservation_proved: bool,
    complete_reference_validation_qualified: bool,
}
impl fmt::Debug for CrossReferenceCommandObservations {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("CrossReferenceCommandObservations")
            .field("crossref_fields", &self.crossref_fields)
            .field("qualification", &"source_observation_only")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum CrossReferenceObservationError {
    #[error("CROSS_REFERENCE_OBSERVATION_LIMIT")]
    Limit,
    #[error("CROSS_REFERENCE_OBSERVATION_SOURCE_BINDING")]
    Binding,
    #[error("CROSS_REFERENCE_OBSERVATION_UNCOVERED_SOURCE")]
    Coverage,
    #[error("CROSS_REFERENCE_OBSERVATION_DUPLICATE_CANDIDATE")]
    Duplicate,
}

impl CrossReferenceCommandObservations {
    /// Decodes each admitted direct string leaf once and indexes all expected
    /// commands once, instead of rescanning XML for each candidate. This is not
    /// a field-meaning parser: any native parameter name remains uninterpreted.
    ///
    /// # Errors
    /// Rejects missed CROSSREF markers in any imported XML part, invalid source
    /// anchors, duplicate expected commands and finite aggregate work/output limits.
    pub fn inspect(
        fields: &ImportedDocumentFields<'_>,
        expected: &[SourceBoundCrossReferenceCandidate],
        limits: ReferenceAuxiliaryLimits,
    ) -> Result<Self, CrossReferenceObservationError> {
        let config = limits.config();
        if expected.len() > config.items_per_kind
            || expected
                .len()
                .checked_mul(256)
                .is_none_or(|n| n > config.output_bytes)
        {
            return Err(CrossReferenceObservationError::Limit);
        }
        let mut lookup = BTreeMap::new();
        let mut observations = Vec::new();
        for (index, candidate) in expected.iter().enumerate() {
            if lookup
                .insert(candidate.command_for_discovery(), index)
                .is_some()
            {
                return Err(CrossReferenceObservationError::Duplicate);
            }
            let receipt = serde_json::to_vec(candidate.receipt())
                .map_err(|_| CrossReferenceObservationError::Limit)?;
            observations.push(CandidateCommandObservation {
                expected_candidate_receipt_sha256: Sha256::digest(&receipt).into(),
                observation: CommandLeafObservation::NotObserved,
                matching_leaves: 0,
                matching_fields: 0,
                shares_field_with_other_candidates: false,
                only_matching_field_reference_sha256: None,
            });
        }
        let source = fields.forms.source();
        let mut seen = BTreeSet::new();
        let mut result = Self {
            schema_version: "hwpx-agent.cross-reference-command-observations/v1",
            status: "source_observation_only",
            observed_source_package_sha256: fields.receipt().source_package_sha256,
            observed_field_graph_sha256: fields.receipt().graph_sha256,
            crossref_fields: 0,
            plain_string_leaves: 0,
            opaque_parameter_children: 0,
            crossrefs_without_parameters: 0,
            candidates: Vec::new(),
            parameter_key_semantics_qualified: false,
            native_execution_attested: false,
            causal_insertion_or_preservation_proved: false,
            complete_reference_validation_qualified: false,
        };
        let mut lexical_bytes = 0usize;
        for range in fields
            .fields()
            .iter()
            .filter(|range| range.native_kind == "CROSSREF")
        {
            result.crossref_fields += 1;
            if result.crossref_fields > config.items_per_kind
                || !seen.insert(&range.begin_anchor.opaque_handle)
            {
                return Err(CrossReferenceObservationError::Limit);
            }
            let begin = source
                .resolve_anchor(&range.begin_anchor)
                .map_err(|_| CrossReferenceObservationError::Binding)?;
            let Some(parameters) = &range.parameter_anchor else {
                result.crossrefs_without_parameters += 1;
                continue;
            };
            let resolved = source
                .resolve_anchor(parameters)
                .map_err(|_| CrossReferenceObservationError::Binding)?;
            let element = resolved
                .element()
                .ok_or(CrossReferenceObservationError::Binding)?;
            if resolved.part().anchor() != begin.part().anchor()
                || element.parent() != begin.element_index()
            {
                return Err(CrossReferenceObservationError::Binding);
            }
            let xml = resolved
                .part()
                .xml()
                .ok_or(CrossReferenceObservationError::Binding)?;
            let mut child = element.first_child();
            let mut matched_in_field = BTreeSet::new();
            while let Some(index) = child {
                let leaf = xml
                    .elements()
                    .get(index)
                    .ok_or(CrossReferenceObservationError::Binding)?;
                child = leaf.next_sibling();
                if leaf.name().namespace() != Some(HP)
                    || leaf.name().local_name() != "stringParam"
                    || leaf.first_child().is_some()
                {
                    result.opaque_parameter_children += 1;
                    continue;
                }
                let span = leaf
                    .content_span()
                    .ok_or(CrossReferenceObservationError::Binding)?;
                let lexical = xml
                    .source_text(span)
                    .map_err(|_| CrossReferenceObservationError::Binding)?;
                lexical_bytes = lexical_bytes
                    .checked_add(lexical.len())
                    .filter(|n| *n <= config.output_bytes)
                    .ok_or(CrossReferenceObservationError::Limit)?;
                if lexical.len() > config.text_bytes {
                    return Err(CrossReferenceObservationError::Limit);
                }
                // Comments/structured content are not concatenated into a
                // purported SDK command. CDATA/DTD are rejected upstream.
                if lexical.contains('<') {
                    result.opaque_parameter_children += 1;
                    continue;
                }
                let decoded =
                    unescape(lexical).map_err(|_| CrossReferenceObservationError::Binding)?;
                if decoded.len() > config.text_bytes {
                    return Err(CrossReferenceObservationError::Limit);
                }
                result.plain_string_leaves += 1;
                if let Some(index) = lookup.get(decoded.as_ref()) {
                    let observation = &mut observations[*index];
                    observation.matching_leaves += 1;
                    if matched_in_field.insert(*index) {
                        observation.matching_fields += 1;
                        observation.only_matching_field_reference_sha256 =
                            Some(Sha256::digest(range.reference_id.as_str().as_bytes()).into());
                    }
                }
            }
            if matched_in_field.len() > 1 {
                for index in matched_in_field {
                    observations[index].shares_field_with_other_candidates = true;
                }
            }
        }
        // Do not silently omit CROSSREF fields hidden in headers, opaque parts
        // or any other XML source outside the original field-range coverage.
        let mut covered = 0usize;
        for part in source.parts() {
            let Some(xml) = part.xml() else { continue };
            for (index, element) in xml.elements().iter().enumerate() {
                if element.name().namespace() == Some(HP)
                    && element.name().local_name() == "fieldBegin"
                    && element.attributes().iter().any(|a| {
                        a.name().namespace().is_none()
                            && a.name().local_name() == "type"
                            && a.semantic_value() == "CROSSREF"
                    })
                {
                    let anchor = part
                        .element_anchor(index)
                        .ok_or(CrossReferenceObservationError::Binding)?;
                    if !seen.contains(&anchor.opaque_handle) {
                        return Err(CrossReferenceObservationError::Coverage);
                    }
                    covered += 1;
                }
            }
        }
        if covered != result.crossref_fields {
            return Err(CrossReferenceObservationError::Coverage);
        }
        for observation in &mut observations {
            observation.observation = match observation.matching_leaves {
                0 => CommandLeafObservation::NotObserved,
                1 if !observation.shares_field_with_other_candidates => {
                    CommandLeafObservation::SingleDecodedLeafObserved
                }
                _ => CommandLeafObservation::AmbiguousDecodedLeaves,
            };
            if observation.observation != CommandLeafObservation::SingleDecodedLeafObserved {
                observation.only_matching_field_reference_sha256 = None;
            }
        }
        result.candidates = observations;
        if serde_json::to_vec(&result)
            .map_err(|_| CrossReferenceObservationError::Limit)?
            .len()
            > config.output_bytes
        {
            return Err(CrossReferenceObservationError::Limit);
        }
        Ok(result)
    }

    /// # Errors
    /// Rejects an excessive report instead of truncating observations.
    pub fn canonical_json(
        &self,
        limits: ReferenceAuxiliaryLimits,
    ) -> Result<Vec<u8>, CrossReferenceObservationError> {
        let bytes = serde_json::to_vec(self).map_err(|_| CrossReferenceObservationError::Limit)?;
        if bytes.len() > limits.config().output_bytes {
            return Err(CrossReferenceObservationError::Limit);
        }
        Ok(bytes)
    }
}
