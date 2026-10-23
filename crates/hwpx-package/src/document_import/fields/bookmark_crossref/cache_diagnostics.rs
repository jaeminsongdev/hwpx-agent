//! Same-snapshot stored name diagnostics; not stale/current/Native evaluation.
use super::{
    BookmarkCrossReferenceDisplay as Display, BookmarkCrossReferenceError as Error,
    SourceBookmarkCrossReferenceBindings, SourceBookmarkResolution, Writer,
};
use crate::document_import::fields::cached_source::{FieldCacheSnapshot, SourceFieldCachedInlines};
use domain_ir::{LogicalId, ReferenceAuxiliaryLimits};
use serde::Serialize;
use std::{collections::BTreeMap, fmt};
#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum BookmarkNameCacheDiagnosticKind {
    StoredNameMatchesCommand,
    StoredNameDiffersFromCommand,
    StructuredCacheUnqualified,
    SourceTargetMissing,
    SourceTargetAmbiguous,
    OtherDisplayNotCompared,
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct BookmarkNameCacheDiagnostic {
    pub field_reference_id: LogicalId,
    pub kind: BookmarkNameCacheDiagnosticKind,
    pub command_sha256: [u8; 32],
    pub cached_decoded_text_sha256: Option<[u8; 32]>,
}
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct SourceBookmarkNameCacheDiagnostics {
    schema_version: &'static str,
    scope: &'static str,
    source_package_sha256: [u8; 32],
    field_graph_sha256: [u8; 32],
    observations: Vec<BookmarkNameCacheDiagnostic>,
    native_display_or_target_resolution_qualified: bool,
    cache_currentness_qualified: bool,
    complete_reference_validation_qualified: bool,
}
impl fmt::Debug for SourceBookmarkNameCacheDiagnostics {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("SourceBookmarkNameCacheDiagnostics")
            .field("fields", &self.observations.len())
            .field("scope", &"same_source_only_not_currentness")
            .finish()
    }
}
impl SourceBookmarkNameCacheDiagnostics {
    #[must_use]
    pub fn observations(&self) -> &[BookmarkNameCacheDiagnostic] {
        &self.observations
    }
    /// # Errors
    /// Rejects excessive output without truncation or raw cached/name values.
    pub fn canonical_json(&self, limits: ReferenceAuxiliaryLimits) -> Result<Vec<u8>, Error> {
        let mut out = Writer {
            written: 0,
            maximum: limits.config().output_bytes,
            bytes: Some(Vec::new()),
        };
        serde_json::to_writer(&mut out, self).map_err(|_| Error::Limit)?;
        out.bytes.ok_or(Error::Limit)
    }
}
impl SourceBookmarkCrossReferenceBindings {
    /// Joins only immutable imports of the exact same package/document/field
    /// graph. A mismatching stored name is a diagnostic, never a stale verdict.
    /// Empty/other-display/structured/unresolved outcomes never become success.
    /// # Errors
    /// Rejects foreign snapshot, missing/duplicate joins and requested budgets.
    pub fn diagnose_cached_source(
        &self,
        caches: &SourceFieldCachedInlines,
        limits: ReferenceAuxiliaryLimits,
    ) -> Result<SourceBookmarkNameCacheDiagnostics, Error> {
        if &self.field_import != caches.field_import() {
            return Err(Error::Binding);
        }
        let config = limits.config();
        if self.bindings.len() > config.items_per_kind
            || caches.observations().len() > config.items_per_kind
        {
            return Err(Error::Limit);
        }
        let mut by_id = BTreeMap::new();
        let mut text_bytes = 0usize;
        for cache in caches.observations() {
            if let FieldCacheSnapshot::DecodedTextNotEvaluated { utf8_bytes, .. } = &cache.cache {
                if *utf8_bytes > config.text_bytes {
                    return Err(Error::Limit);
                }
                text_bytes = text_bytes
                    .checked_add(*utf8_bytes)
                    .filter(|v| *v <= config.input_bytes)
                    .ok_or(Error::Limit)?;
            }
            if by_id
                .insert(&cache.field_reference_id, &cache.cache)
                .is_some()
            {
                return Err(Error::Binding);
            }
        }
        if by_id.len() != self.field_import.field_ranges {
            return Err(Error::Binding);
        }
        let mut result = SourceBookmarkNameCacheDiagnostics {
            schema_version: "hwpx-agent.source-bookmark-name-cache-diagnostics/v1",
            scope: "stored_decoded_name_vs_same_source_command_only_not_native_evaluation_or_currentness",
            source_package_sha256: self.field_import.source_package_sha256,
            field_graph_sha256: self.field_import.graph_sha256,
            observations: Vec::new(),
            native_display_or_target_resolution_qualified: false,
            cache_currentness_qualified: false,
            complete_reference_validation_qualified: false,
        };
        let mut count = Writer {
            written: 0,
            maximum: config.output_bytes,
            bytes: None,
        };
        serde_json::to_writer(&mut count, &result).map_err(|_| Error::Limit)?;
        let mut total = count.written;
        for binding in &self.bindings {
            let cache = by_id
                .get(&binding.field_reference_id)
                .ok_or(Error::Binding)?;
            let decoded = match cache {
                FieldCacheSnapshot::DecodedTextNotEvaluated {
                    decoded_text_sha256,
                    ..
                } => Some(*decoded_text_sha256),
                _ => None,
            };
            let kind = match &binding.target {
                SourceBookmarkResolution::Missing => {
                    BookmarkNameCacheDiagnosticKind::SourceTargetMissing
                }
                SourceBookmarkResolution::Ambiguous => {
                    BookmarkNameCacheDiagnosticKind::SourceTargetAmbiguous
                }
                SourceBookmarkResolution::Bound { .. }
                    if binding.display != Display::BookmarkName =>
                {
                    BookmarkNameCacheDiagnosticKind::OtherDisplayNotCompared
                }
                SourceBookmarkResolution::Bound { .. } => match decoded {
                    None => BookmarkNameCacheDiagnosticKind::StructuredCacheUnqualified,
                    Some(sha) if sha == binding.exact_target_name_sha256 => {
                        BookmarkNameCacheDiagnosticKind::StoredNameMatchesCommand
                    }
                    Some(_) => BookmarkNameCacheDiagnosticKind::StoredNameDiffersFromCommand,
                },
            };
            let row = BookmarkNameCacheDiagnostic {
                field_reference_id: binding.field_reference_id.clone(),
                kind,
                command_sha256: binding.command_sha256,
                cached_decoded_text_sha256: decoded,
            };
            let mut count = Writer {
                written: 0,
                maximum: config.output_bytes,
                bytes: None,
            };
            serde_json::to_writer(&mut count, &row).map_err(|_| Error::Limit)?;
            total = total
                .checked_add(count.written)
                .and_then(|v| v.checked_add(usize::from(!result.observations.is_empty())))
                .filter(|v| *v <= config.output_bytes)
                .ok_or(Error::Limit)?;
            result
                .observations
                .try_reserve(1)
                .map_err(|_| Error::Limit)?;
            result.observations.push(row);
        }
        let mut count = Writer {
            written: 0,
            maximum: config.output_bytes,
            bytes: None,
        };
        serde_json::to_writer(&mut count, &result).map_err(|_| Error::Limit)?;
        Ok(result)
    }
}
