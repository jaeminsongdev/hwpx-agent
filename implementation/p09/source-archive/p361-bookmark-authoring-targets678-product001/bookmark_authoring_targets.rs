//! Shared source-bound target selection for point and block bookmark authoring.
//! No caller-controlled block flag, source names, service grant or Native permit.
use super::block_bookmarks::{BlockBookmarkImportError, ImportedBlockBookmarks};
use super::{FieldRangeImportReceipt, ImportedDocumentFields};
use crate::cross_reference_sdk::{
    SdkCrossReferenceCandidate, SdkCrossReferenceDisplay, SdkCrossReferenceError,
    SdkCrossReferenceTarget,
};
use crate::document_import::reference_targets::sdk::authoring_display::PointBookmarkAuthoringDisplay;
use crate::document_import::reference_targets::sdk::{
    SourceCrossReferenceContext, SourceCrossReferenceError,
};
use domain_ir::{LogicalId, ReferenceAuxiliaryLimits};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    fmt,
};
use thiserror::Error;

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum SourceBookmarkFamily {
    Point,
    Block,
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct BookmarkAuthoringTargetReceipt {
    pub profile: &'static str,
    pub field_import: FieldRangeImportReceipt,
    pub family: SourceBookmarkFamily,
    pub logical_target_id_sha256: [u8; 32],
    pub target_state_sha256: String,
    pub command_sha256: [u8; 32],
    pub requires_native_target_qualification: bool,
    pub service_or_execution_authority: bool,
}
impl fmt::Debug for BookmarkAuthoringTargetReceipt {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("BookmarkAuthoringTargetReceipt")
            .field("family", &self.family)
            .field("scope", &"source_only_not_execution_authority")
            .finish_non_exhaustive()
    }
}
pub struct SourceBookmarkAuthoringTarget {
    candidate: SdkCrossReferenceCandidate,
    receipt: BookmarkAuthoringTargetReceipt,
}
impl fmt::Debug for SourceBookmarkAuthoringTarget {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("SourceBookmarkAuthoringTarget(<redacted>; inert)")
    }
}
impl SourceBookmarkAuthoringTarget {
    #[must_use]
    pub fn command_for_preparation(&self) -> &str {
        self.candidate.command_for_discovery()
    }
    #[must_use]
    pub const fn receipt(&self) -> &BookmarkAuthoringTargetReceipt {
        &self.receipt
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Error)]
pub enum BookmarkAuthoringTargetError {
    #[error("BOOKMARK_AUTHORING_SOURCE_BINDING_REJECTED")]
    Binding,
    #[error("BOOKMARK_AUTHORING_TARGET_MISSING")]
    Missing,
    #[error("BOOKMARK_AUTHORING_SOURCE_NAME_AMBIGUOUS")]
    Ambiguous,
    #[error("BOOKMARK_AUTHORING_POINT_CONTENT_REQUIRES_BLOCK")]
    ContentRequiresBlockBookmark,
    #[error("BOOKMARK_AUTHORING_TARGET_PROFILE_UNSUPPORTED")]
    Unsupported,
    #[error("BOOKMARK_AUTHORING_TARGET_LIMIT")]
    Limit,
    #[error("BOOKMARK_AUTHORING_COMMAND_REJECTED")]
    Command,
}
type Error = BookmarkAuthoringTargetError;

pub struct SourceBookmarkAuthoringContext<'a> {
    fields: &'a ImportedDocumentFields<'a>,
    points: SourceCrossReferenceContext<'a>,
    point_ids: BTreeMap<&'a LogicalId, &'a str>,
    point_names: BTreeSet<&'a str>,
    blocks: Option<ImportedBlockBookmarks>,
    block_ids: BTreeMap<LogicalId, usize>,
    limits: ReferenceAuxiliaryLimits,
}
impl fmt::Debug for SourceBookmarkAuthoringContext<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("SourceBookmarkAuthoringContext(<redacted>)")
    }
}
fn point_error(error: SourceCrossReferenceError) -> Error {
    match error {
        SourceCrossReferenceError::Missing => Error::Missing,
        SourceCrossReferenceError::Ambiguous => Error::Ambiguous,
        SourceCrossReferenceError::Limit => Error::Limit,
        SourceCrossReferenceError::Command => Error::Command,
        SourceCrossReferenceError::NativeTargetKindUnqualified => Error::Unsupported,
        _ => Error::Binding,
    }
}
impl<'a> SourceBookmarkAuthoringContext<'a> {
    /// Imports indexes once per preparation batch. Existing point discovery
    /// commands/target state remain unchanged; block targets use actual fields.
    /// # Errors
    /// Rejects incomplete source coverage, unsupported block profiles or limits.
    pub fn import(
        fields: &'a ImportedDocumentFields<'a>,
        limits: ReferenceAuxiliaryLimits,
    ) -> Result<Self, Error> {
        let structure = fields.forms.body_structure();
        let points = SourceCrossReferenceContext::import(structure, limits).map_err(point_error)?;
        let mut point_ids = BTreeMap::new();
        let mut point_names = BTreeSet::new();
        for row in structure.bookmarks() {
            if point_ids
                .insert(&row.reference_id, row.name.as_str())
                .is_some()
            {
                return Err(Error::Binding);
            }
            point_names.insert(row.name.as_str());
        }
        // No BOOKMARK fields means no extra cached-inline walk for point-only
        // documents. Cross-family name checks remain indexed, never per-case scans.
        let blocks = if fields.fields().iter().any(|v| v.native_kind == "BOOKMARK") {
            Some(
                ImportedBlockBookmarks::import(fields, limits).map_err(|e| match e {
                    BlockBookmarkImportError::Limit => Error::Limit,
                    BlockBookmarkImportError::Unsupported => Error::Unsupported,
                    _ => Error::Binding,
                })?,
            )
        } else {
            None
        };
        let mut block_ids = BTreeMap::new();
        if let Some(blocks) = &blocks {
            for (index, row) in blocks.observations().iter().enumerate() {
                if point_ids.contains_key(row.field_reference_id())
                    || block_ids
                        .insert(row.field_reference_id().clone(), index)
                        .is_some()
                {
                    return Err(Error::Binding);
                }
            }
        }
        Ok(Self {
            fields,
            points,
            point_ids,
            point_names,
            blocks,
            block_ids,
            limits,
        })
    }
    /// Only an actual imported logical target can select the family. Raw SDK
    /// syntax and a display option cannot turn a point marker into a block.
    /// # Errors
    /// Rejects missing/ambiguous names across both families, invalid displays,
    /// unsupported SDK escaping and limits. Output remains an inert candidate.
    pub fn prepare(
        &self,
        target: &LogicalId,
        display: SdkCrossReferenceDisplay,
        hyperlink: bool,
    ) -> Result<SourceBookmarkAuthoringTarget, Error> {
        let (name, family, state) = if let Some(index) = self.block_ids.get(target) {
            let blocks = self.blocks.as_ref().ok_or(Error::Binding)?;
            let row = blocks.observations().get(*index).ok_or(Error::Binding)?;
            if self.point_names.contains(row.name()) {
                return Err(Error::Ambiguous);
            }
            blocks
                .by_exact_source_name(row.name())
                .map_err(|e| match e {
                    BlockBookmarkImportError::Ambiguous => Error::Ambiguous,
                    _ => Error::Binding,
                })?;
            if display == SdkCrossReferenceDisplay::ObjectNumber {
                return Err(Error::Unsupported);
            }
            let state = serde_json::to_vec(&(
                "source-block-bookmark-prop2/v1",
                self.fields.receipt(),
                row.field_reference_id(),
                row.begin_anchor(),
                row.end_anchor(),
                <[u8; 32]>::from(Sha256::digest(row.name().as_bytes())),
                row.selected_source(),
            ))
            .map_err(|_| Error::Limit)?;
            if state.len() > self.limits.config().output_bytes {
                return Err(Error::Limit);
            }
            (
                row.name(),
                SourceBookmarkFamily::Block,
                hex::encode(Sha256::digest(&state)),
            )
        } else {
            let name = *self.point_ids.get(target).ok_or(Error::Missing)?;
            if let Some(blocks) = &self.blocks {
                if !matches!(
                    blocks.by_exact_source_name(name),
                    Err(BlockBookmarkImportError::Missing)
                ) {
                    return Err(Error::Ambiguous);
                }
            }
            PointBookmarkAuthoringDisplay::try_from(display).map_err(|e|match e{
                crate::document_import::reference_targets::sdk::authoring_display::PointBookmarkDisplayError::ContentRequiresBlockBookmark=>Error::ContentRequiresBlockBookmark,
                _=>Error::Unsupported,
            })?;
            let point = self
                .points
                .prepare(target, display, hyperlink)
                .map_err(point_error)?;
            (
                name,
                SourceBookmarkFamily::Point,
                point.source_target_state_sha256().to_owned(),
            )
        };
        let candidate = SdkCrossReferenceCandidate::build(
            SdkCrossReferenceTarget::Bookmark {
                exact_source_name: name,
            },
            display,
            hyperlink,
        )
        .map_err(|e| match e {
            SdkCrossReferenceError::Limit => Error::Limit,
            _ => Error::Command,
        })?;
        let receipt = BookmarkAuthoringTargetReceipt {
            profile: "hwpx-agent.source-bookmark-authoring-target/point-or-block-v1",
            field_import: self.fields.receipt().clone(),
            family,
            logical_target_id_sha256: Sha256::digest(target.as_str().as_bytes()).into(),
            target_state_sha256: state,
            command_sha256: Sha256::digest(candidate.command_for_discovery().as_bytes()).into(),
            requires_native_target_qualification: true,
            service_or_execution_authority: false,
        };
        Ok(SourceBookmarkAuthoringTarget { candidate, receipt })
    }
    /// # Errors
    /// Requires whole fresh source/fields reconstruction, never a retained hash alone.
    pub fn verify_source(&self, fresh: &[u8]) -> Result<FieldRangeImportReceipt, Error> {
        self.fields.verify_source(fresh).map_err(|_| Error::Binding)
    }
}
