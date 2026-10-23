//! Inert SDK discovery candidates, not native execution or direct HWPX lowering.
//!
//! Syntax: pinned ParameterSetTable 2504 pages 1, 175, 176 and ActionTable
//! pages 16, 23. The installed 11.0.0.9136 type library declares the Command
//! BSTR property, but does NOT qualify action behavior, note index origins,
//! cached display, HWPX field parameters or save/reopen. No public product route
//! consumes raw commands. A later authorized native discovery must bind actual
//! document targets; a serialized candidate alone is not an execution permit.
use std::{fmt, fmt::Write as _};

use thiserror::Error;

pub const CROSS_REFERENCE_SDK_CANDIDATE_PROFILE: &str =
    "hwpx-agent.cross-reference-sdk/current-document-discovery-candidate-v1";
pub const CROSS_REFERENCE_SDK_COMMAND_MAX_BYTES: usize = 4096;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SdkObjectKind {
    Table,
    Picture,
    Equation,
    Outline,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SdkNoteKind {
    Footnote,
    Endnote,
}

/// This index is NOT a native note instId or displayed number. Its actual
/// source ordering and origin must be qualified by later native discovery.
#[derive(Clone, Copy, Eq, PartialEq)]
pub struct SdkNoteSourceOrderIndex(u32);
impl SdkNoteSourceOrderIndex {
    /// # Errors
    /// Rejects zero; this candidate profile only admits positive specimen indices.
    pub fn positive_specimen(value: u32) -> Result<Self, SdkCrossReferenceError> {
        if value == 0 {
            return Err(SdkCrossReferenceError::Identity);
        }
        Ok(Self(value))
    }
}
impl fmt::Debug for SdkNoteSourceOrderIndex {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("SdkNoteSourceOrderIndex(<redacted>)")
    }
}

#[derive(Clone, Copy)]
pub enum SdkCrossReferenceTarget<'a> {
    Object {
        kind: SdkObjectKind,
        observed_instance_id: u32,
    },
    Note {
        kind: SdkNoteKind,
        source_order_index: SdkNoteSourceOrderIndex,
    },
    Bookmark {
        exact_source_name: &'a str,
    },
}
impl fmt::Debug for SdkCrossReferenceTarget<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("SdkCrossReferenceTarget(<redacted>)")
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SdkCrossReferenceDisplay {
    Page,
    ObjectNumber,
    BookmarkName,
    Content,
    RelativePosition,
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum SdkCrossReferenceError {
    #[error("CROSS_REFERENCE_SDK_SOURCE_IDENTITY_REJECTED")]
    Identity,
    #[error("CROSS_REFERENCE_SDK_DISPLAY_REJECTED")]
    Display,
    #[error("CROSS_REFERENCE_SDK_BOOKMARK_ENCODING_UNQUALIFIED")]
    BookmarkEncoding,
    #[error("CROSS_REFERENCE_SDK_COMMAND_LIMIT")]
    Limit,
}

/// Has no Deserialize/Serialize or native executor. External document routes,
/// ambiguous escaping and automatic target selection are not admitted here.
pub struct SdkCrossReferenceCandidate {
    command: String,
}
impl fmt::Debug for SdkCrossReferenceCandidate {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("SdkCrossReferenceCandidate")
            .field(
                "qualification",
                &"manual_syntax_only_native_behavior_unverified",
            )
            .finish_non_exhaustive()
    }
}

impl SdkCrossReferenceCandidate {
    /// Builds only a same-document specimen. The final option is zero because
    /// external-window navigation is not part of this discovery profile.
    ///
    /// # Errors
    /// Rejects unsupported kind/display combinations, unknown bookmark escaping,
    /// zero object identity, output limits and allocation failure. Native target
    /// existence/uniqueness, note ordering and current-document authority are
    /// intentionally NOT asserted by this pure syntax stage.
    pub fn build(
        target: SdkCrossReferenceTarget<'_>,
        display: SdkCrossReferenceDisplay,
        hyperlink: bool,
    ) -> Result<Self, SdkCrossReferenceError> {
        let (kind, numeric, name) = match target {
            SdkCrossReferenceTarget::Object {
                kind,
                observed_instance_id,
            } => {
                if observed_instance_id == 0 {
                    return Err(SdkCrossReferenceError::Identity);
                }
                let code = match kind {
                    SdkObjectKind::Table => 0,
                    SdkObjectKind::Picture => 1,
                    SdkObjectKind::Equation => 2,
                    SdkObjectKind::Outline => 5,
                };
                (code, Some(observed_instance_id), None)
            }
            SdkCrossReferenceTarget::Note {
                kind,
                source_order_index,
            } => (
                match kind {
                    SdkNoteKind::Footnote => 3,
                    SdkNoteKind::Endnote => 4,
                },
                Some(source_order_index.0),
                None,
            ),
            SdkCrossReferenceTarget::Bookmark { exact_source_name } => {
                if exact_source_name.len() > CROSS_REFERENCE_SDK_COMMAND_MAX_BYTES {
                    return Err(SdkCrossReferenceError::Limit);
                }
                if exact_source_name.is_empty()
                    || exact_source_name.starts_with('#')
                    || exact_source_name
                        .chars()
                        .any(|c| c.is_control() || matches!(c, ';' | '?' | '\\' | '/' | ':'))
                {
                    return Err(SdkCrossReferenceError::BookmarkEncoding);
                }
                (6, None, Some(exact_source_name))
            }
        };
        let display_code = match display {
            SdkCrossReferenceDisplay::Page => 0,
            SdkCrossReferenceDisplay::ObjectNumber if kind != 6 => 1,
            SdkCrossReferenceDisplay::BookmarkName if kind == 6 => 1,
            SdkCrossReferenceDisplay::Content if kind != 3 && kind != 4 => 2,
            SdkCrossReferenceDisplay::RelativePosition => 3,
            _ => return Err(SdkCrossReferenceError::Display),
        };
        // Numeric payloads need at most '#'+10 decimal digits. Borrowed names
        // are bounded before allocating or copying any source string.
        let capacity = name
            .map_or(11, str::len)
            .checked_add(9)
            .filter(|n| *n <= CROSS_REFERENCE_SDK_COMMAND_MAX_BYTES)
            .ok_or(SdkCrossReferenceError::Limit)?;
        let mut command = String::new();
        command
            .try_reserve_exact(capacity)
            .map_err(|_| SdkCrossReferenceError::Limit)?;
        command.push('?');
        if let Some(value) = numeric {
            write!(&mut command, "#{value}").map_err(|_| SdkCrossReferenceError::Limit)?;
        } else {
            command.push_str(name.ok_or(SdkCrossReferenceError::Identity)?);
        }
        write!(
            &mut command,
            ";{kind};{display_code};{};0",
            u8::from(hyperlink)
        )
        .map_err(|_| SdkCrossReferenceError::Limit)?;
        Ok(Self { command })
    }

    /// Private-backend discovery input only. Does not invoke/authorize an action.
    #[must_use]
    pub fn command_for_discovery(&self) -> &str {
        &self.command
    }

    #[must_use]
    pub const fn requires_native_target_qualification(&self) -> bool {
        true
    }
}
