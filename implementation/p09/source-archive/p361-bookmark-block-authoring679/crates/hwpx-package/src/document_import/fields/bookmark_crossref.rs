//! Strict source-local CROSSREF Command binding, not Native execution or approval.
//! Names are obtained only from admitted source XML, never a caller target map.
use super::{
    FieldRangeImportReceipt, ImportedDocumentFields,
    cross_reference_observation::CrossReferenceCommandObservations,
};
use crate::{
    HANCOM_2020_PARAGRAPH_NAMESPACE as HP,
    cross_reference_sdk::{
        SdkCrossReferenceCandidate, SdkCrossReferenceDisplay as SdkDisplay, SdkCrossReferenceTarget,
    },
    document_import::reference_targets::{
        ImportedReferenceTargets, ReferenceTargetImportError, ReferenceTargetImportReceipt,
    },
};
use domain_ir::{LogicalId, ReferenceAuxiliaryLimits, ReferenceTargetKind};
use quick_xml::escape::unescape;
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use std::{fmt, io};
use thiserror::Error;

pub const PROFILE: &str = "hwpx-agent.source-crossref-bookmark-command-bindings/v1";
pub mod cache_diagnostics;
#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum BookmarkCrossReferenceDisplay {
    Page,
    BookmarkName,
    Content,
    RelativePosition,
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(tag = "resolution", rename_all = "snake_case")]
pub enum SourceBookmarkResolution {
    Bound {
        logical_target_id: LogicalId,
        target_state_sha256: String,
    },
    Missing,
    Ambiguous,
}
impl fmt::Debug for SourceBookmarkResolution {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("SourceBookmarkResolution(<redacted>)")
    }
}
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct SourceBookmarkCrossReference {
    pub field_reference_id: LogicalId,
    pub command_sha256: [u8; 32],
    pub exact_target_name_sha256: [u8; 32],
    pub display: BookmarkCrossReferenceDisplay,
    pub hyperlink: bool,
    pub target: SourceBookmarkResolution,
}
impl fmt::Debug for SourceBookmarkCrossReference {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("SourceBookmarkCrossReference(<redacted>)")
    }
}
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct SourceBookmarkCrossReferenceBindings {
    schema_version: &'static str,
    scope: &'static str,
    field_import: FieldRangeImportReceipt,
    target_import: ReferenceTargetImportReceipt,
    bindings: Vec<SourceBookmarkCrossReference>,
    native_execution_attested: bool,
    native_target_resolution_qualified: bool,
    complete_reference_validation_qualified: bool,
}
impl fmt::Debug for SourceBookmarkCrossReferenceBindings {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("SourceBookmarkCrossReferenceBindings")
            .field("bindings", &self.bindings.len())
            .field("scope", &"source_local_only")
            .finish()
    }
}
#[derive(Clone, Copy, Debug, Eq, PartialEq, Error)]
pub enum BookmarkCrossReferenceError {
    #[error("SOURCE_BOOKMARK_CROSSREF_BINDING_REJECTED")]
    Binding,
    #[error("SOURCE_BOOKMARK_CROSSREF_COVERAGE_REJECTED")]
    Coverage,
    #[error("SOURCE_BOOKMARK_CROSSREF_COMMAND_PARAMETER_REJECTED")]
    Parameter,
    #[error("SOURCE_BOOKMARK_CROSSREF_COMMAND_SYNTAX_REJECTED")]
    Command,
    #[error("SOURCE_BOOKMARK_CROSSREF_TARGET_KIND_UNQUALIFIED")]
    UnqualifiedKind,
    #[error("SOURCE_BOOKMARK_CROSSREF_LIMIT")]
    Limit,
}
type Error = BookmarkCrossReferenceError;

/// Count output BEFORE retaining each row; bounded serialization never first
/// allocates a complete oversized report. No raw command or target name leaves.
struct Writer {
    written: usize,
    maximum: usize,
    bytes: Option<Vec<u8>>,
}
impl io::Write for Writer {
    fn write(&mut self, bytes: &[u8]) -> io::Result<usize> {
        self.written = self
            .written
            .checked_add(bytes.len())
            .filter(|n| *n <= self.maximum)
            .ok_or_else(|| io::Error::other("SOURCE_BOOKMARK_CROSSREF_LIMIT"))?;
        if let Some(out) = &mut self.bytes {
            out.try_reserve(bytes.len())
                .map_err(|_| io::Error::other("SOURCE_BOOKMARK_CROSSREF_LIMIT"))?;
            out.extend_from_slice(bytes);
        }
        Ok(bytes.len())
    }
    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}

impl SourceBookmarkCrossReferenceBindings {
    #[must_use]
    pub fn bindings(&self) -> &[SourceBookmarkCrossReference] {
        &self.bindings
    }
    /// # Errors
    /// Keeps all original source/field/target coverage checks. Missing/ambiguous
    /// names are typed outcomes, not first-match selection or Native resolution.
    /// Other CROSSREF kinds/syntax are explicitly rejected by this bookmark API.
    pub fn import(
        fields: &ImportedDocumentFields<'_>,
        limits: ReferenceAuxiliaryLimits,
    ) -> Result<Self, Error> {
        Self::import_selected(fields, limits, false, None)
    }

    /// The general meaning inventory keeps other target kinds explicitly
    /// Unsupported. This internal path must not turn a subset into a public
    /// whole-CROSSREF binding report or bypass malformed bookmark parameters.
    pub(super) fn supported_meanings(
        fields: &ImportedDocumentFields<'_>,
        limits: ReferenceAuxiliaryLimits,
        targets: Option<&ImportedReferenceTargets<'_>>,
    ) -> Result<Vec<SourceBookmarkCrossReference>, Error> {
        Ok(Self::import_selected(fields, limits, true, targets)?.bindings)
    }

    fn import_selected(
        fields: &ImportedDocumentFields<'_>,
        limits: ReferenceAuxiliaryLimits,
        keep_other_kinds_unsupported: bool,
        reused_targets: Option<&ImportedReferenceTargets<'_>>,
    ) -> Result<Self, Error> {
        let config = limits.config();
        CrossReferenceCommandObservations::inspect(fields, &[], limits).map_err(
            |error| match error {
                super::cross_reference_observation::CrossReferenceObservationError::Limit => {
                    Error::Limit
                }
                super::cross_reference_observation::CrossReferenceObservationError::Coverage => {
                    Error::Coverage
                }
                _ => Error::Binding,
            },
        )?;
        let owned_targets;
        let targets = if let Some(targets) = reused_targets {
            if !targets.matches_original_limits(fields.forms.body_structure(), limits) {
                return Err(Error::Binding);
            }
            targets
        } else {
            owned_targets = ImportedReferenceTargets::import(fields.forms.body_structure(), limits)
            .map_err(|error| match error {
                ReferenceTargetImportError::Limit => Error::Limit,
                ReferenceTargetImportError::Coverage => Error::Coverage,
                _ => Error::Binding,
            })?;
            &owned_targets
        };
        if targets.receipt().source_package_sha256 != fields.receipt().source_package_sha256 {
            return Err(Error::Binding);
        }
        let source = fields.forms.source();
        let mut result = Self {
            schema_version: PROFILE,
            scope: "source_local_command_and_bookmark_only_not_native_or_complete_validation",
            field_import: fields.receipt().clone(),
            target_import: targets.receipt().clone(),
            bindings: Vec::new(),
            native_execution_attested: false,
            native_target_resolution_qualified: false,
            complete_reference_validation_qualified: false,
        };
        let mut count = Writer {
            written: 0,
            maximum: config.output_bytes,
            bytes: None,
        };
        serde_json::to_writer(&mut count, &result).map_err(|_| Error::Limit)?;
        let mut total = count.written;
        let mut work = 0usize;
        for field in fields
            .fields()
            .iter()
            .filter(|field| field.native_kind == "CROSSREF")
        {
            if result.bindings.len() >= config.items_per_kind {
                return Err(Error::Limit);
            }
            let begin = source
                .resolve_anchor(&field.begin_anchor)
                .map_err(|_| Error::Binding)?;
            let Some(parameter_anchor) = field.parameter_anchor.as_ref() else {
                if keep_other_kinds_unsupported { continue; }
                return Err(Error::Parameter);
            };
            let parameters = source
                .resolve_anchor(parameter_anchor)
                .map_err(|_| Error::Binding)?;
            let element = parameters.element().ok_or(Error::Binding)?;
            if parameters.part().anchor() != begin.part().anchor()
                || element.parent() != begin.element_index()
            {
                return Err(Error::Binding);
            }
            let xml = parameters.part().xml().ok_or(Error::Binding)?;
            let mut child = element.first_child();
            let mut command = None;
            while let Some(index) = child {
                work = work
                    .checked_add(1)
                    .filter(|n| *n <= config.output_bytes)
                    .ok_or(Error::Limit)?;
                let leaf = xml.elements().get(index).ok_or(Error::Binding)?;
                child = leaf.next_sibling();
                let is_command = leaf.attributes().iter().any(|a| {
                    a.name().namespace().is_none()
                        && a.name().local_name() == "name"
                        && a.semantic_value() == "Command"
                });
                if !is_command {
                    continue;
                }
                if command.is_some()
                    || leaf.name().namespace() != Some(HP)
                    || leaf.name().local_name() != "stringParam"
                    || leaf.first_child().is_some()
                {
                    return Err(Error::Parameter);
                }
                let lexical = xml
                    .source_text(leaf.content_span().ok_or(Error::Parameter)?)
                    .map_err(|_| Error::Binding)?;
                if lexical.len() > config.text_bytes { return Err(Error::Limit); }
                if lexical.len()
                        > crate::cross_reference_sdk::CROSS_REFERENCE_SDK_COMMAND_MAX_BYTES
                    || lexical.contains('<')
                {
                    return Err(Error::Parameter);
                }
                let decoded = unescape(lexical).map_err(|_| Error::Parameter)?;
                if decoded.len() > config.text_bytes {
                    return Err(Error::Limit);
                }
                command = Some(decoded);
            }
            let Some(command) = command else {
                if keep_other_kinds_unsupported { continue; }
                return Err(Error::Parameter);
            };
            let (name, display, hyperlink) = match decode_bookmark_command(&command) {
                Err(Error::UnqualifiedKind) if keep_other_kinds_unsupported => continue,
                result => result?,
            };
            let target = match targets.by_exact_source_name(name) {
                Ok(target) => {
                    if target.target_kind != ReferenceTargetKind::Bookmark {
                        return Err(Error::Binding);
                    }
                    SourceBookmarkResolution::Bound {
                        logical_target_id: target.logical_target_id.clone(),
                        target_state_sha256: target.target_state_sha256.clone(),
                    }
                }
                Err(ReferenceTargetImportError::Missing) => SourceBookmarkResolution::Missing,
                Err(ReferenceTargetImportError::Ambiguous) => SourceBookmarkResolution::Ambiguous,
                Err(_) => return Err(Error::Binding),
            };
            let row = SourceBookmarkCrossReference {
                field_reference_id: field.reference_id.clone(),
                command_sha256: Sha256::digest(command.as_bytes()).into(),
                exact_target_name_sha256: Sha256::digest(name.as_bytes()).into(),
                display,
                hyperlink,
                target,
            };
            let mut count = Writer {
                written: 0,
                maximum: config.output_bytes,
                bytes: None,
            };
            serde_json::to_writer(&mut count, &row).map_err(|_| Error::Limit)?;
            total = total
                .checked_add(count.written)
                .and_then(|n| n.checked_add(1))
                .filter(|n| *n <= config.output_bytes)
                .ok_or(Error::Limit)?;
            result.bindings.try_reserve(1).map_err(|_| Error::Limit)?;
            result.bindings.push(row);
        }
        let mut count = Writer {
            written: 0,
            maximum: config.output_bytes,
            bytes: None,
        };
        serde_json::to_writer(&mut count, &result).map_err(|_| Error::Limit)?;
        Ok(result)
    }
    /// # Errors
    /// Refuses excessive output without truncating or returning private strings.
    pub fn canonical_json(&self, limits: ReferenceAuxiliaryLimits) -> Result<Vec<u8>, Error> {
        let mut writer = Writer {
            written: 0,
            maximum: limits.config().output_bytes,
            bytes: Some(Vec::new()),
        };
        serde_json::to_writer(&mut writer, self).map_err(|_| Error::Limit)?;
        writer.bytes.ok_or(Error::Limit)
    }
}

fn decode_bookmark_command(
    command: &str,
) -> Result<(&str, BookmarkCrossReferenceDisplay, bool), Error> {
    if command.len() > crate::cross_reference_sdk::CROSS_REFERENCE_SDK_COMMAND_MAX_BYTES {
        return Err(Error::Limit);
    }
    let mut parts = command.split(';');
    let name = parts
        .next()
        .and_then(|p| p.strip_prefix('?'))
        .ok_or(Error::Command)?;
    if parts.next() != Some("6") {
        return Err(Error::UnqualifiedKind);
    }
    let (display, sdk) = match parts.next() {
        Some("0") => (BookmarkCrossReferenceDisplay::Page, SdkDisplay::Page),
        Some("1") => (
            BookmarkCrossReferenceDisplay::BookmarkName,
            SdkDisplay::BookmarkName,
        ),
        Some("2") => (BookmarkCrossReferenceDisplay::Content, SdkDisplay::Content),
        Some("3") => (
            BookmarkCrossReferenceDisplay::RelativePosition,
            SdkDisplay::RelativePosition,
        ),
        _ => return Err(Error::Command),
    };
    let hyperlink = match parts.next() {
        Some("0") => false,
        Some("1") => true,
        _ => return Err(Error::Command),
    };
    if parts.next() != Some("0") || parts.next().is_some() {
        return Err(Error::Command);
    }
    let candidate = SdkCrossReferenceCandidate::build(
        SdkCrossReferenceTarget::Bookmark {
            exact_source_name: name,
        },
        sdk,
        hyperlink,
    )
    .map_err(|_| Error::Command)?;
    if candidate.command_for_discovery() != command {
        return Err(Error::Command);
    }
    Ok((name, display, hyperlink))
}
