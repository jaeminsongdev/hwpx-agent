//! Actual immutable source binding for inert SDK discovery, not an action permit.
use std::{collections::BTreeMap, fmt};

use domain_ir::{LogicalId, ReferenceAuxiliaryLimits, ReferenceTargetKind};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use super::{ImportedDocumentStructure, ImportedReferenceTargets, ReferenceTargetImportReceipt};
use crate::{
    cross_reference_sdk::{
        SdkCrossReferenceCandidate, SdkCrossReferenceDisplay, SdkCrossReferenceError,
        SdkCrossReferenceTarget,
    },
    document_import::structure::bookmarks::{
        ImportedBookmarkObservation, ImportedBookmarkSectionLocation, ImportedBookmarkSourcePoint,
    },
};

pub const SOURCE_BOUND_CROSS_REFERENCE_PROFILE: &str =
    "hwpx-agent.cross-reference-sdk/source-bound-discovery-candidate-v1";

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct SourceBoundCrossReferenceReceipt {
    profile: &'static str,
    source: ReferenceTargetImportReceipt,
    logical_target_id_sha256: [u8; 32],
    target_state_sha256: String,
    command_sha256: [u8; 32],
    requires_native_target_qualification: bool,
}
impl fmt::Debug for SourceBoundCrossReferenceReceipt {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("SourceBoundCrossReferenceReceipt")
            .field(
                "qualification",
                &"source_snapshot_only_not_native_authority",
            )
            .finish_non_exhaustive()
    }
}

pub struct SourceBoundCrossReferenceCandidate {
    candidate: SdkCrossReferenceCandidate,
    receipt: SourceBoundCrossReferenceReceipt,
    source_paragraph_id: LogicalId,
    source_point: ImportedBookmarkSourcePoint,
    source_section_location: ImportedBookmarkSectionLocation,
}
impl fmt::Debug for SourceBoundCrossReferenceCandidate {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("SourceBoundCrossReferenceCandidate(<redacted>; native_not_qualified)")
    }
}
impl SourceBoundCrossReferenceCandidate {
    /// Actual source paragraph identity, including nested table/note paragraphs.
    /// It does not authorize a flattened LinkAnchor or native navigation.
    #[must_use]
    pub const fn source_paragraph_id(&self) -> &LogicalId {
        &self.source_paragraph_id
    }

    #[must_use]
    pub const fn source_point(&self) -> ImportedBookmarkSourcePoint {
        self.source_point
    }

    /// Original XML paragraph order, not normalized graph order or native flow.
    #[must_use]
    pub const fn source_section_location(&self) -> &ImportedBookmarkSectionLocation {
        &self.source_section_location
    }

    /// Opaque identity of the original imported target, not a native target ID.
    #[must_use]
    pub const fn source_logical_target_id_sha256(&self) -> [u8; 32] {
        self.receipt.logical_target_id_sha256
    }

    /// Hash of the exact imported target state, not a current service capability.
    #[must_use]
    pub fn source_target_state_sha256(&self) -> &str {
        &self.receipt.target_state_sha256
    }

    #[must_use]
    pub fn command_for_discovery(&self) -> &str {
        self.candidate.command_for_discovery()
    }
    #[must_use]
    pub const fn receipt(&self) -> &SourceBoundCrossReferenceReceipt {
        &self.receipt
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum SourceCrossReferenceError {
    #[error("SOURCE_CROSS_REFERENCE_COVERAGE_REJECTED")]
    Coverage,
    #[error("SOURCE_CROSS_REFERENCE_LIMIT")]
    Limit,
    #[error("SOURCE_CROSS_REFERENCE_BINDING_REJECTED")]
    Binding,
    #[error("SOURCE_CROSS_REFERENCE_TARGET_MISSING")]
    Missing,
    #[error("SOURCE_CROSS_REFERENCE_NAME_AMBIGUOUS")]
    Ambiguous,
    #[error("SOURCE_CROSS_REFERENCE_NATIVE_TARGET_KIND_UNQUALIFIED")]
    NativeTargetKindUnqualified,
    #[error("SOURCE_CROSS_REFERENCE_COMMAND_REJECTED")]
    Command,
}

/// One import and two indexes for a whole preparation batch, not one complete
/// source/structure reconstruction per selected display or hyperlink setting.
pub struct SourceCrossReferenceContext<'a> {
    targets: ImportedReferenceTargets<'a>,
    kinds: BTreeMap<LogicalId, ReferenceTargetKind>,
    bookmarks: BTreeMap<&'a LogicalId, &'a ImportedBookmarkObservation>,
}
impl fmt::Debug for SourceCrossReferenceContext<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("SourceCrossReferenceContext(<redacted>)")
    }
}

impl<'a> SourceCrossReferenceContext<'a> {
    /// # Errors
    /// Rejects original source/target coverage, budgets or duplicate identities.
    pub fn import(
        source: &'a ImportedDocumentStructure,
        limits: ReferenceAuxiliaryLimits,
    ) -> Result<Self, SourceCrossReferenceError> {
        let targets = ImportedReferenceTargets::import(source, limits).map_err(|e| match e {
            super::ReferenceTargetImportError::Limit => SourceCrossReferenceError::Limit,
            super::ReferenceTargetImportError::Coverage => SourceCrossReferenceError::Coverage,
            _ => SourceCrossReferenceError::Binding,
        })?;
        let mut kinds = BTreeMap::new();
        for target in targets.targets() {
            if kinds
                .insert(target.logical_target_id.clone(), target.target_kind)
                .is_some()
            {
                return Err(SourceCrossReferenceError::Binding);
            }
        }
        let mut bookmarks = BTreeMap::new();
        for bookmark in source.bookmarks() {
            if bookmarks.insert(&bookmark.reference_id, bookmark).is_some() {
                return Err(SourceCrossReferenceError::Binding);
            }
        }
        Ok(Self {
            targets,
            kinds,
            bookmarks,
        })
    }

    /// Binds a selected actual logical ID, never a caller-supplied native name,
    /// instance ID, note index, graph or parameter string.
    ///
    /// # Errors
    /// Rejects missing/ambiguous names and unqualified native kind mappings.
    /// Bookmark identity is source-local; native normalization and current-head
    /// authorization are NOT proved by exact imported-source name matching.
    pub fn prepare(
        &self,
        target_id: &LogicalId,
        display: SdkCrossReferenceDisplay,
        hyperlink: bool,
    ) -> Result<SourceBoundCrossReferenceCandidate, SourceCrossReferenceError> {
        let kind = self
            .kinds
            .get(target_id)
            .ok_or(SourceCrossReferenceError::Missing)?;
        if *kind != ReferenceTargetKind::Bookmark {
            // HWPX table id is not a qualified HML InstId mapping. A note's
            // instId/display number is not a qualified SDK source-order INDEX.
            return Err(SourceCrossReferenceError::NativeTargetKindUnqualified);
        }
        let bookmark = self
            .bookmarks
            .get(target_id)
            .ok_or(SourceCrossReferenceError::Binding)?;
        let target = self
            .targets
            .by_exact_source_name(&bookmark.name)
            .map_err(|e| match e {
                super::ReferenceTargetImportError::Ambiguous => {
                    SourceCrossReferenceError::Ambiguous
                }
                _ => SourceCrossReferenceError::Binding,
            })?;
        if &target.logical_target_id != target_id {
            return Err(SourceCrossReferenceError::Binding);
        }
        let candidate = SdkCrossReferenceCandidate::build(
            SdkCrossReferenceTarget::Bookmark {
                exact_source_name: &bookmark.name,
            },
            display,
            hyperlink,
        )
        .map_err(|e| match e {
            SdkCrossReferenceError::Limit => SourceCrossReferenceError::Limit,
            _ => SourceCrossReferenceError::Command,
        })?;
        let receipt = SourceBoundCrossReferenceReceipt {
            profile: SOURCE_BOUND_CROSS_REFERENCE_PROFILE,
            source: self.targets.receipt().clone(),
            logical_target_id_sha256: Sha256::digest(target_id.as_str().as_bytes()).into(),
            target_state_sha256: target.target_state_sha256.clone(),
            command_sha256: Sha256::digest(candidate.command_for_discovery().as_bytes()).into(),
            requires_native_target_qualification: true,
        };
        Ok(SourceBoundCrossReferenceCandidate {
            candidate,
            receipt,
            source_paragraph_id: bookmark.paragraph_id.clone(),
            source_point: bookmark.source_point(),
            source_section_location: bookmark.section_location().clone(),
        })
    }

    /// Reconstructs the whole fresh source and structure once per batch boundary.
    /// # Errors
    /// Rejects changed bytes/identity/topology, without granting native execution.
    pub fn verify_source(
        &self,
        fresh: &[u8],
    ) -> Result<ReferenceTargetImportReceipt, SourceCrossReferenceError> {
        self.targets
            .verify_source(fresh)
            .map_err(|_| SourceCrossReferenceError::Binding)
    }
}
