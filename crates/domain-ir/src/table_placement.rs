use std::fmt;

use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{LengthMicrometers, LogicalId};

pub const TABLE_PLACEMENT_SCHEMA_VERSION: &str = "hwpx-agent.table-placement/v1";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TablePlacementLimitConfig {
    pub input_bytes: usize,
    pub offset_micrometers: u64,
    pub margin_micrometers: u64,
    pub serialized_bytes: usize,
}

impl Default for TablePlacementLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 64 * 1024,
            offset_micrometers: 1_000_000_000,
            margin_micrometers: 1_000_000_000,
            serialized_bytes: 64 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TablePlacementLimits(TablePlacementLimitConfig);

impl TablePlacementLimits {
    pub const HARD_MAX_INPUT_BYTES: usize = 4 * 1024 * 1024;
    pub const HARD_MAX_OFFSET_MICROMETERS: u64 = 10_000_000_000;
    pub const HARD_MAX_MARGIN_MICROMETERS: u64 = 10_000_000_000;
    pub const HARD_MAX_SERIALIZED_BYTES: usize = 4 * 1024 * 1024;

    /// Creates finite limits for the table-placement boundary.
    ///
    /// # Errors
    ///
    /// Rejects zero and over-ceiling limits, or an input limit larger than the output limit.
    pub fn new(config: TablePlacementLimitConfig) -> Result<Self, TablePlacementError> {
        if config.input_bytes == 0
            || config.input_bytes > Self::HARD_MAX_INPUT_BYTES
            || config.offset_micrometers == 0
            || config.offset_micrometers > Self::HARD_MAX_OFFSET_MICROMETERS
            || config.margin_micrometers == 0
            || config.margin_micrometers > Self::HARD_MAX_MARGIN_MICROMETERS
            || config.serialized_bytes == 0
            || config.serialized_bytes > Self::HARD_MAX_SERIALIZED_BYTES
            || config.input_bytes > config.serialized_bytes
        {
            return Err(TablePlacementError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> TablePlacementLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableHorizontalReference {
    Paper,
    Page,
    Column,
    Paragraph,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableVerticalReference {
    Paper,
    Page,
    Paragraph,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableHorizontalAlignment {
    Left,
    Center,
    Right,
    Inside,
    Outside,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableVerticalAlignment {
    Top,
    Center,
    Bottom,
    Inside,
    Outside,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableTextWrap {
    Square,
    TopAndBottom,
    BehindText,
    InFrontOfText,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableTextFlow {
    BothSides,
    LeftOnly,
    RightOnly,
    LargestOnly,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableOuterMargins {
    pub left: LengthMicrometers,
    pub right: LengthMicrometers,
    pub top: LengthMicrometers,
    pub bottom: LengthMicrometers,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableFloatingPlacement {
    pub horizontal_reference: TableHorizontalReference,
    pub vertical_reference: TableVerticalReference,
    pub horizontal_alignment: TableHorizontalAlignment,
    pub vertical_alignment: TableVerticalAlignment,
    pub horizontal_offset: LengthMicrometers,
    pub vertical_offset: LengthMicrometers,
    pub flow_with_text: bool,
    pub allow_overlap: bool,
    pub hold_anchor_and_shape: bool,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case", tag = "kind", deny_unknown_fields)]
pub enum TableAttachmentMode {
    Inline { affect_line_spacing: bool },
    Floating { placement: TableFloatingPlacement },
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TablePlacementStateDraft {
    pub schema_version: String,
    pub table_id: LogicalId,
    pub attachment: TableAttachmentMode,
    pub text_wrap: TableTextWrap,
    pub text_flow: TableTextFlow,
    pub outer_margins: TableOuterMargins,
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TablePlacementState {
    schema_version: &'static str,
    table_id: LogicalId,
    attachment: TableAttachmentMode,
    text_wrap: TableTextWrap,
    text_flow: TableTextFlow,
    outer_margins: TableOuterMargins,
}

impl TablePlacementState {
    /// Validates a complete table placement state.
    ///
    /// # Errors
    ///
    /// Rejects schema drift, out-of-range offsets or margins, and oversized serialization.
    pub fn from_draft(
        draft: TablePlacementStateDraft,
        limits: TablePlacementLimits,
    ) -> Result<Self, TablePlacementError> {
        if draft.schema_version != TABLE_PLACEMENT_SCHEMA_VERSION {
            return Err(TablePlacementError::UnsupportedVersion);
        }
        validate_attachment(draft.attachment, limits)?;
        validate_margins(draft.outer_margins, limits)?;
        let state = Self {
            schema_version: TABLE_PLACEMENT_SCHEMA_VERSION,
            table_id: draft.table_id,
            attachment: draft.attachment,
            text_wrap: draft.text_wrap,
            text_flow: draft.text_flow,
            outer_margins: draft.outer_margins,
        };
        let _ = state.canonical_json(limits)?;
        Ok(state)
    }

    /// Parses strict bounded JSON and validates every state invariant.
    ///
    /// # Errors
    ///
    /// Rejects empty, oversized, malformed, duplicate-key or unknown-field JSON.
    pub fn from_json(
        bytes: &[u8],
        limits: TablePlacementLimits,
    ) -> Result<Self, TablePlacementError> {
        if bytes.is_empty() || bytes.len() > limits.0.input_bytes {
            return Err(TablePlacementError::InputLimit);
        }
        let draft = serde_json::from_slice(bytes).map_err(|_| TablePlacementError::InvalidJson)?;
        Self::from_draft(draft, limits)
    }

    #[must_use]
    pub const fn table_id(&self) -> &LogicalId {
        &self.table_id
    }

    #[must_use]
    pub const fn attachment(&self) -> TableAttachmentMode {
        self.attachment
    }

    #[must_use]
    pub const fn text_wrap(&self) -> TableTextWrap {
        self.text_wrap
    }

    #[must_use]
    pub const fn text_flow(&self) -> TableTextFlow {
        self.text_flow
    }

    #[must_use]
    pub const fn outer_margins(&self) -> TableOuterMargins {
        self.outer_margins
    }

    /// Applies one semantic placement operation without mutating the source state.
    ///
    /// # Errors
    ///
    /// Position and wrap operations reject inline tables because those values are inactive there.
    /// Every candidate is fully revalidated before a result and receipt are returned.
    pub fn apply(
        &self,
        operation: TablePlacementOperation,
        limits: TablePlacementLimits,
    ) -> Result<TablePlacementResult, TablePlacementError> {
        validate_state(self, limits)?;
        let source_sha256 = self.canonical_sha256(limits)?;
        let mut output = self.clone();
        match operation {
            TablePlacementOperation::SetPosition { placement } => {
                if !matches!(self.attachment, TableAttachmentMode::Floating { .. }) {
                    return Err(TablePlacementError::RequiresFloating);
                }
                validate_floating(placement, limits)?;
                output.attachment = TableAttachmentMode::Floating { placement };
            }
            TablePlacementOperation::SetInline {
                affect_line_spacing,
            } => {
                output.attachment = TableAttachmentMode::Inline {
                    affect_line_spacing,
                };
            }
            TablePlacementOperation::SetFloating { placement } => {
                validate_floating(placement, limits)?;
                output.attachment = TableAttachmentMode::Floating { placement };
            }
            TablePlacementOperation::SetWrap {
                text_wrap,
                text_flow,
            } => {
                if !matches!(self.attachment, TableAttachmentMode::Floating { .. }) {
                    return Err(TablePlacementError::RequiresFloating);
                }
                output.text_wrap = text_wrap;
                output.text_flow = text_flow;
            }
            TablePlacementOperation::SetOuterMargins { margins } => {
                validate_margins(margins, limits)?;
                output.outer_margins = margins;
            }
        }
        validate_state(&output, limits)?;
        let output_sha256 = output.canonical_sha256(limits)?;
        let receipt = TablePlacementReceipt {
            schema_version: TABLE_PLACEMENT_SCHEMA_VERSION,
            capability_id: operation.capability_id(),
            operation,
            table_id: self.table_id.clone(),
            source_state_sha256: hex(source_sha256),
            output_state_sha256: hex(output_sha256),
            changed: output != *self,
        };
        let _ = receipt.canonical_json(limits)?;
        Ok(TablePlacementResult {
            state: output,
            receipt,
        })
    }

    /// Emits deterministic compact JSON under the configured finite output limit.
    ///
    /// # Errors
    ///
    /// Rejects serialization failure or output beyond the configured bound.
    pub fn canonical_json(
        &self,
        limits: TablePlacementLimits,
    ) -> Result<Vec<u8>, TablePlacementError> {
        serialize_bounded(self, limits.0.serialized_bytes)
    }

    /// Hashes bounded canonical state JSON.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failures.
    pub fn canonical_sha256(
        &self,
        limits: TablePlacementLimits,
    ) -> Result<[u8; 32], TablePlacementError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TablePlacementState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TablePlacementState")
            .field("schema_version", &self.schema_version)
            .field("table_id", &"<redacted>")
            .field("attachment_kind", &attachment_label(self.attachment))
            .field("text_wrap", &self.text_wrap)
            .field("text_flow", &self.text_flow)
            .field("outer_margins", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case", tag = "kind", deny_unknown_fields)]
pub enum TablePlacementOperation {
    SetPosition {
        placement: TableFloatingPlacement,
    },
    SetInline {
        affect_line_spacing: bool,
    },
    SetFloating {
        placement: TableFloatingPlacement,
    },
    SetWrap {
        text_wrap: TableTextWrap,
        text_flow: TableTextFlow,
    },
    SetOuterMargins {
        margins: TableOuterMargins,
    },
}

impl TablePlacementOperation {
    #[must_use]
    pub const fn capability_id(self) -> &'static str {
        match self {
            Self::SetPosition { .. } => "table.position",
            Self::SetInline { .. } | Self::SetFloating { .. } => "table.inline_floating",
            Self::SetWrap { .. } => "table.wrap",
            Self::SetOuterMargins { .. } => "table.outer_margin",
        }
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TablePlacementReceipt {
    schema_version: &'static str,
    capability_id: &'static str,
    operation: TablePlacementOperation,
    table_id: LogicalId,
    source_state_sha256: String,
    output_state_sha256: String,
    changed: bool,
}

impl TablePlacementReceipt {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
    }

    #[must_use]
    pub const fn operation(&self) -> TablePlacementOperation {
        self.operation
    }

    #[must_use]
    pub const fn table_id(&self) -> &LogicalId {
        &self.table_id
    }

    #[must_use]
    pub fn source_state_sha256(&self) -> &str {
        &self.source_state_sha256
    }

    #[must_use]
    pub fn output_state_sha256(&self) -> &str {
        &self.output_state_sha256
    }

    #[must_use]
    pub const fn changed(&self) -> bool {
        self.changed
    }

    /// Emits deterministic compact JSON under the configured finite output limit.
    ///
    /// # Errors
    ///
    /// Rejects serialization failure or output beyond the configured bound.
    pub fn canonical_json(
        &self,
        limits: TablePlacementLimits,
    ) -> Result<Vec<u8>, TablePlacementError> {
        serialize_bounded(self, limits.0.serialized_bytes)
    }
}

impl fmt::Debug for TablePlacementReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TablePlacementReceipt")
            .field("capability_id", &self.capability_id)
            .field("operation_kind", &operation_label(self.operation))
            .field("table_id", &"<redacted>")
            .field("changed", &self.changed)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TablePlacementResult {
    state: TablePlacementState,
    receipt: TablePlacementReceipt,
}

impl TablePlacementResult {
    #[must_use]
    pub const fn state(&self) -> &TablePlacementState {
        &self.state
    }

    #[must_use]
    pub const fn receipt(&self) -> &TablePlacementReceipt {
        &self.receipt
    }

    #[must_use]
    pub fn into_parts(self) -> (TablePlacementState, TablePlacementReceipt) {
        (self.state, self.receipt)
    }
}

impl fmt::Debug for TablePlacementResult {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TablePlacementResult")
            .field("state", &self.state)
            .field("receipt", &self.receipt)
            .finish()
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum TablePlacementError {
    #[error("table placement limits are invalid")]
    InvalidLimit,
    #[error("table placement schema version is unsupported")]
    UnsupportedVersion,
    #[error("table placement JSON input is empty or oversized")]
    InputLimit,
    #[error("table placement JSON is invalid")]
    InvalidJson,
    #[error("table placement offset is outside the configured signed bound")]
    OffsetOutOfRange,
    #[error("table placement margin is negative or outside the configured bound")]
    MarginOutOfRange,
    #[error("table placement operation requires a floating table")]
    RequiresFloating,
    #[error("table placement output exceeds its configured bound")]
    OutputLimit,
    #[error("table placement serialization failed")]
    Serialization,
}

impl TablePlacementError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidLimit => "table_placement_invalid_limit",
            Self::UnsupportedVersion => "table_placement_unsupported_version",
            Self::InputLimit => "table_placement_input_limit",
            Self::InvalidJson => "table_placement_invalid_json",
            Self::OffsetOutOfRange => "table_placement_offset_out_of_range",
            Self::MarginOutOfRange => "table_placement_margin_out_of_range",
            Self::RequiresFloating => "table_placement_requires_floating",
            Self::OutputLimit => "table_placement_output_limit",
            Self::Serialization => "table_placement_serialization",
        }
    }
}

fn validate_state(
    state: &TablePlacementState,
    limits: TablePlacementLimits,
) -> Result<(), TablePlacementError> {
    validate_attachment(state.attachment, limits)?;
    validate_margins(state.outer_margins, limits)?;
    let _ = state.canonical_json(limits)?;
    Ok(())
}

fn validate_attachment(
    attachment: TableAttachmentMode,
    limits: TablePlacementLimits,
) -> Result<(), TablePlacementError> {
    if let TableAttachmentMode::Floating { placement } = attachment {
        validate_floating(placement, limits)?;
    }
    Ok(())
}

fn validate_floating(
    placement: TableFloatingPlacement,
    limits: TablePlacementLimits,
) -> Result<(), TablePlacementError> {
    validate_signed(placement.horizontal_offset, limits.0.offset_micrometers)?;
    validate_signed(placement.vertical_offset, limits.0.offset_micrometers)
}

fn validate_margins(
    margins: TableOuterMargins,
    limits: TablePlacementLimits,
) -> Result<(), TablePlacementError> {
    for value in [margins.left, margins.right, margins.top, margins.bottom] {
        let raw = value.as_i64();
        if raw < 0 || u64::try_from(raw).map_or(true, |value| value > limits.0.margin_micrometers) {
            return Err(TablePlacementError::MarginOutOfRange);
        }
    }
    Ok(())
}

fn validate_signed(value: LengthMicrometers, maximum: u64) -> Result<(), TablePlacementError> {
    if value.as_i64().unsigned_abs() > maximum {
        return Err(TablePlacementError::OffsetOutOfRange);
    }
    Ok(())
}

fn serialize_bounded<T: Serialize>(
    value: &T,
    maximum: usize,
) -> Result<Vec<u8>, TablePlacementError> {
    let bytes = serde_json::to_vec(value).map_err(|_| TablePlacementError::Serialization)?;
    if bytes.len() > maximum {
        return Err(TablePlacementError::OutputLimit);
    }
    Ok(bytes)
}

const fn attachment_label(value: TableAttachmentMode) -> &'static str {
    match value {
        TableAttachmentMode::Inline { .. } => "inline",
        TableAttachmentMode::Floating { .. } => "floating",
    }
}

const fn operation_label(value: TablePlacementOperation) -> &'static str {
    match value {
        TablePlacementOperation::SetPosition { .. } => "set_position",
        TablePlacementOperation::SetInline { .. } => "set_inline",
        TablePlacementOperation::SetFloating { .. } => "set_floating",
        TablePlacementOperation::SetWrap { .. } => "set_wrap",
        TablePlacementOperation::SetOuterMargins { .. } => "set_outer_margins",
    }
}

fn hex(value: [u8; 32]) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(64);
    for byte in value {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}
