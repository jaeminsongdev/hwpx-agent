//! Source-bound block bookmarks observed in Native670. Point markers remain a
//! separate family. This inventory confers no Native or cross-reference authority.
use super::cached_source::{FieldCacheSnapshot, SourceFieldCachedInlines};
use super::{FieldRangeImportReceipt, ImportedDocumentFields};
use crate::{HANCOM_2020_PARAGRAPH_NAMESPACE as HP, XmlElementToken};
use domain_ir::{LogicalId, ReferenceAuxiliaryLimits, SourceAnchorHandle};
use serde::Serialize;
use std::{collections::BTreeMap, fmt};
use thiserror::Error;

#[derive(Clone, Eq, PartialEq)]
pub struct ImportedBlockBookmark {
    field_reference_id: LogicalId,
    paragraph_id: LogicalId,
    begin_anchor: SourceAnchorHandle,
    end_anchor: SourceAnchorHandle,
    name: String,
    selected_source: FieldCacheSnapshot,
}
impl fmt::Debug for ImportedBlockBookmark {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ImportedBlockBookmark(<redacted>; source_local_only)")
    }
}
impl ImportedBlockBookmark {
    #[must_use]
    pub fn name(&self) -> &str {
        &self.name
    }
    #[must_use]
    pub const fn field_reference_id(&self) -> &LogicalId {
        &self.field_reference_id
    }
    #[must_use]
    pub const fn paragraph_id(&self) -> &LogicalId {
        &self.paragraph_id
    }
    #[must_use]
    pub const fn begin_anchor(&self) -> &SourceAnchorHandle {
        &self.begin_anchor
    }
    #[must_use]
    pub const fn end_anchor(&self) -> &SourceAnchorHandle {
        &self.end_anchor
    }
    /// Original selected inline bytes, never a recomputed CROSSREF display.
    #[must_use]
    pub const fn selected_source(&self) -> &FieldCacheSnapshot {
        &self.selected_source
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct BlockBookmarkImportReceipt {
    pub profile: &'static str,
    pub field_import: FieldRangeImportReceipt,
    pub block_bookmarks: usize,
    pub native_or_cross_reference_execution_qualified: bool,
}

#[derive(Clone, Eq, PartialEq)]
pub struct ImportedBlockBookmarks {
    receipt: BlockBookmarkImportReceipt,
    observations: Vec<ImportedBlockBookmark>,
    names: BTreeMap<String, Option<usize>>,
}
impl fmt::Debug for ImportedBlockBookmarks {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("ImportedBlockBookmarks")
            .field("block_bookmarks", &self.observations.len())
            .field("scope", &"source_local_only")
            .finish()
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Error)]
pub enum BlockBookmarkImportError {
    #[error("BLOCK_BOOKMARK_SOURCE_BINDING_REJECTED")]
    Binding,
    #[error("BLOCK_BOOKMARK_PARAMETER_PROFILE_UNSUPPORTED")]
    Unsupported,
    #[error("BLOCK_BOOKMARK_IMPORT_LIMIT")]
    Limit,
    #[error("BLOCK_BOOKMARK_NAME_MISSING")]
    Missing,
    #[error("BLOCK_BOOKMARK_NAME_AMBIGUOUS")]
    Ambiguous,
}
type Error = BlockBookmarkImportError;

fn attribute<'a>(e: &'a XmlElementToken, key: &str) -> Result<&'a str, Error> {
    let mut found = e
        .attributes()
        .iter()
        .filter(|a| a.name().namespace().is_none() && a.name().local_name() == key);
    let value = found.next().ok_or(Error::Binding)?.semantic_value();
    if found.next().is_some() {
        return Err(Error::Binding);
    }
    Ok(value)
}

impl ImportedBlockBookmarks {
    /// Uses the existing whole-source field coverage and optimized inline
    /// inventory once, including notes/table paragraphs. No per-name graph clone.
    /// # Errors
    /// Rejects invalid source anchors, unsupported BOOKMARK parameter profiles,
    /// structured content and finite limits. Duplicate names stay ambiguous.
    pub fn import(
        fields: &ImportedDocumentFields<'_>,
        limits: ReferenceAuxiliaryLimits,
    ) -> Result<Self, Error> {
        let config = limits.config();
        let cached = SourceFieldCachedInlines::import(fields, limits).map_err(|e| match e {
            super::cached_source::FieldCachedSourceError::Limit => Error::Limit,
            _ => Error::Binding,
        })?;
        let cache_by_id: BTreeMap<_, _> = cached
            .observations()
            .iter()
            .map(|v| (&v.field_reference_id, &v.cache))
            .collect();
        let source = fields.forms.source();
        let mut result = Self {
            receipt: BlockBookmarkImportReceipt {
                profile: "hwpx-agent.source-block-bookmarks/observed-bookmark-prop2-v1",
                field_import: fields.receipt().clone(),
                block_bookmarks: 0,
                native_or_cross_reference_execution_qualified: false,
            },
            observations: Vec::new(),
            names: BTreeMap::new(),
        };
        let mut name_bytes = 0usize;
        for field in fields
            .fields()
            .iter()
            .filter(|v| v.native_kind == "BOOKMARK")
        {
            if result.observations.len() >= config.items_per_kind {
                return Err(Error::Limit);
            }
            let begin = source
                .resolve_anchor(&field.begin_anchor)
                .map_err(|_| Error::Binding)?;
            let end = source
                .resolve_anchor(&field.end_anchor)
                .map_err(|_| Error::Binding)?;
            let header = begin.element().ok_or(Error::Binding)?;
            let tail = end.element().ok_or(Error::Binding)?;
            if header.name().namespace() != Some(HP)
                || header.name().local_name() != "fieldBegin"
                || tail.name().namespace() != Some(HP)
                || tail.name().local_name() != "fieldEnd"
                || attribute(header, "type")? != "BOOKMARK"
                || attribute(header, "id")? != attribute(tail, "beginIDRef")?
                || begin.part().anchor() != end.part().anchor()
            {
                return Err(Error::Binding);
            }
            // fieldid is an opaque native attribute. Native670 shares it across
            // all eight ranges; never use it as the pairing/target identity.
            let name = attribute(header, "name")?;
            if name.is_empty() || name.chars().any(char::is_control) {
                return Err(Error::Unsupported);
            }
            name_bytes = name_bytes
                .checked_add(name.len().checked_mul(2).ok_or(Error::Limit)?)
                .filter(|v| *v <= config.input_bytes)
                .ok_or(Error::Limit)?;
            if name.len() > config.text_bytes {
                return Err(Error::Limit);
            }
            let anchor = field.parameter_anchor.as_ref().ok_or(Error::Unsupported)?;
            let parameters = source.resolve_anchor(anchor).map_err(|_| Error::Binding)?;
            let parameter = parameters.element().ok_or(Error::Binding)?;
            if parameters.part().anchor() != begin.part().anchor()
                || parameter.parent() != begin.element_index()
                || parameter.name().namespace() != Some(HP)
                || parameter.name().local_name() != "parameters"
                || attribute(parameter, "cnt")? != "1"
                || attribute(parameter, "name")? != ""
            {
                return Err(Error::Unsupported);
            }
            let xml = parameters.part().xml().ok_or(Error::Binding)?;
            let prop = xml
                .elements()
                .get(parameter.first_child().ok_or(Error::Unsupported)?)
                .ok_or(Error::Binding)?;
            if prop.next_sibling().is_some()
                || prop.first_child().is_some()
                || prop.name().namespace() != Some(HP)
                || prop.name().local_name() != "integerParam"
                || attribute(prop, "name")? != "Prop"
            {
                return Err(Error::Unsupported);
            }
            let text = xml
                .source_text(prop.content_span().ok_or(Error::Unsupported)?)
                .map_err(|_| Error::Binding)?;
            if text != "2" {
                return Err(Error::Unsupported);
            }
            let selected = *cache_by_id.get(&field.reference_id).ok_or(Error::Binding)?;
            if !matches!(selected, FieldCacheSnapshot::DecodedTextNotEvaluated { .. }) {
                return Err(Error::Unsupported);
            }
            let index = result.observations.len();
            result
                .names
                .entry(name.to_owned())
                .and_modify(|v| *v = None)
                .or_insert(Some(index));
            result.observations.push(ImportedBlockBookmark {
                field_reference_id: field.reference_id.clone(),
                paragraph_id: field.paragraph_id.clone(),
                begin_anchor: field.begin_anchor.clone(),
                end_anchor: field.end_anchor.clone(),
                name: name.to_owned(),
                selected_source: selected.clone(),
            });
        }
        result.receipt.block_bookmarks = result.observations.len();
        Ok(result)
    }
    #[must_use]
    pub fn observations(&self) -> &[ImportedBlockBookmark] {
        &self.observations
    }
    #[must_use]
    pub const fn receipt(&self) -> &BlockBookmarkImportReceipt {
        &self.receipt
    }
    /// Exact source-local name only; no case folding, fallback or service permit.
    /// # Errors
    /// Rejects missing or duplicate source names.
    pub fn by_exact_source_name(&self, name: &str) -> Result<&ImportedBlockBookmark, Error> {
        match self.names.get(name) {
            None => Err(Error::Missing),
            Some(None) => Err(Error::Ambiguous),
            Some(Some(index)) => self.observations.get(*index).ok_or(Error::Binding),
        }
    }
    /// Rebuilds the whole original fields from fresh bytes before checking this
    /// derived inventory. A retained receipt alone cannot establish currentness.
    /// # Errors
    /// Rejects foreign models, changed bytes or changed limits/inventory.
    pub fn verify_source(
        &self,
        fields: &ImportedDocumentFields<'_>,
        fresh: &[u8],
        limits: ReferenceAuxiliaryLimits,
    ) -> Result<BlockBookmarkImportReceipt, Error> {
        if fields.receipt() != &self.receipt.field_import {
            return Err(Error::Binding);
        }
        fields.verify_source(fresh).map_err(|_| Error::Binding)?;
        if &Self::import(fields, limits)? != self {
            return Err(Error::Binding);
        }
        Ok(self.receipt.clone())
    }
}
