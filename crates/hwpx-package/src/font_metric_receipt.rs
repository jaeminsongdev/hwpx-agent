use std::{collections::BTreeSet, fmt};

use domain_ir::{
    FontMetricEvidence, FontMetricStatus, LengthMicrometers, LogicalId, TableCellMeasure,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

pub const CURRENT_FONT_METRIC_PROFILE_ID: &str =
    "hwpx-agent.font-metric.gdiplus-typographic-96dpi/1";

const RECEIPT_SCHEMA_VERSION: &str = "hwpx-agent.p06-05-current-font-metric-receipt/v1";
const RECEIPT_SCOPE: &str = "current_pc_named_synthetic_fixture_only";
const HANGUL_BUILD: &str = "11.0.0.9136";
const HANGUL_EXECUTABLE_SHA256: &str =
    "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce";
const FONT_FILE_NAME: &str = "HANBatang.ttf";
const FONT_FILE_BYTES: u64 = 28_412_796;
const FONT_FILE_SHA256: &str = "0dbeb7b129fcec63f8d6b7f1d3b5bb991c1d599e725286518ccc598de643f014";
const FONT_FAMILY: &str = "함초롬바탕";
const MEASUREMENT_PROVIDER: &str = "System.Drawing.GDIPlus.GenericTypographic/1";
const MEASUREMENT_CONVERSION: &str = "micrometers=round_away_from_zero(pixels*25400/96)";
const EXPECTED_MEASUREMENT_SET_SHA256: &str =
    "96e3ad33591b098d3ca15c88242303aa7b11dc1730cf2a499273afe3ad7790a9";
const EXPECTED_CELLS: [(&str, &str); 4] = [
    (
        "cell-a",
        "df47d07aa15a6493ed52bcddfbd594ff255d9566138ab7137f90b13fedd2ed98",
    ),
    (
        "cell-b",
        "b81461d5ac0a8865284ef84c147e0743da482750e1a499d80126e31c7324ee7b",
    ),
    (
        "cell-c",
        "25dfcb4b0c5e694cf7bf977f1870cd2025fa363bfa2a26118ea00f305a3afdd3",
    ),
    (
        "cell-d",
        "d932f7dee69be5f5763a0647e1ed14067e5231e783b4039a9aabbf8387405845",
    ),
];

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct CurrentFontMetricLimits {
    input_bytes: usize,
    cells: usize,
    dimension_micrometers: i64,
}

impl Default for CurrentFontMetricLimits {
    fn default() -> Self {
        Self {
            input_bytes: 256 * 1024,
            cells: 4,
            dimension_micrometers: 1_000_000_000,
        }
    }
}

impl CurrentFontMetricLimits {
    pub const HARD_MAX_INPUT_BYTES: usize = 1024 * 1024;
    pub const HARD_MAX_CELLS: usize = 1024;
    pub const HARD_MAX_DIMENSION_MICROMETERS: i64 = 1_000_000_000;

    /// Creates finite limits for the current-PC font-metric receipt adapter.
    ///
    /// # Errors
    ///
    /// Rejects zero, negative, or above-ceiling values.
    pub fn new(
        input_bytes: usize,
        cells: usize,
        dimension_micrometers: i64,
    ) -> Result<Self, FontMetricReceiptError> {
        if input_bytes == 0
            || input_bytes > Self::HARD_MAX_INPUT_BYTES
            || cells == 0
            || cells > Self::HARD_MAX_CELLS
            || dimension_micrometers <= 0
            || dimension_micrometers > Self::HARD_MAX_DIMENSION_MICROMETERS
        {
            return Err(FontMetricReceiptError::InvalidLimit);
        }
        Ok(Self {
            input_bytes,
            cells,
            dimension_micrometers,
        })
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct CurrentFontMetricCell {
    cell_id: LogicalId,
    minimum_content_width: LengthMicrometers,
    preferred_content_width: LengthMicrometers,
    line_height: LengthMicrometers,
}

impl CurrentFontMetricCell {
    #[must_use]
    pub const fn cell_id(&self) -> &LogicalId {
        &self.cell_id
    }

    #[must_use]
    pub const fn minimum_content_width(&self) -> LengthMicrometers {
        self.minimum_content_width
    }

    #[must_use]
    pub const fn preferred_content_width(&self) -> LengthMicrometers {
        self.preferred_content_width
    }

    #[must_use]
    pub const fn line_height(&self) -> LengthMicrometers {
        self.line_height
    }
}

impl fmt::Debug for CurrentFontMetricCell {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("CurrentFontMetricCell(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct CurrentFontMetricReceipt {
    receipt_sha256: String,
    measurement_set_sha256: String,
    cells: Vec<CurrentFontMetricCell>,
    dimension_limit: i64,
}

impl CurrentFontMetricReceipt {
    /// Parses and validates the exact current-PC named synthetic font receipt.
    ///
    /// # Errors
    ///
    /// Rejects oversized JSON, unknown or duplicate fields, target drift, noncanonical digests,
    /// malformed cells, unsafe claims, or metric values outside the configured finite limits.
    pub fn parse(
        source: &[u8],
        limits: CurrentFontMetricLimits,
    ) -> Result<Self, FontMetricReceiptError> {
        if source.is_empty() || source.len() > limits.input_bytes {
            return Err(FontMetricReceiptError::InputLimit);
        }
        let raw: RawReceipt =
            serde_json::from_slice(source).map_err(|_| FontMetricReceiptError::MalformedJson)?;
        validate_envelope(&raw)?;
        if raw.cells.len() != EXPECTED_CELLS.len() || raw.cells.len() > limits.cells {
            return Err(FontMetricReceiptError::CellLimit);
        }
        let canonical_cells =
            serde_json::to_vec(&raw.cells).map_err(|_| FontMetricReceiptError::MalformedJson)?;
        let observed_measurement_sha256 = hex_digest(Sha256::digest(canonical_cells).into());
        if !is_lower_hex(&raw.measurement_set_sha256)
            || raw.measurement_set_sha256 != observed_measurement_sha256
            || raw.measurement_set_sha256 != EXPECTED_MEASUREMENT_SET_SHA256
        {
            return Err(FontMetricReceiptError::MeasurementDigestMismatch);
        }

        let mut seen = BTreeSet::new();
        let mut cells = Vec::new();
        cells
            .try_reserve_exact(raw.cells.len())
            .map_err(|_| FontMetricReceiptError::AllocationFailed)?;
        for (raw_cell, (expected_id, expected_text_sha256)) in
            raw.cells.into_iter().zip(EXPECTED_CELLS)
        {
            if raw_cell.cell_id != expected_id
                || raw_cell.text_sha256 != expected_text_sha256
                || !is_lower_hex(&raw_cell.text_sha256)
                || !seen.insert(raw_cell.cell_id.clone())
            {
                return Err(FontMetricReceiptError::CellIdentityMismatch);
            }
            let minimum = dimension(
                raw_cell.minimum_content_width_micrometers,
                limits.dimension_micrometers,
            )?;
            let preferred = dimension(
                raw_cell.preferred_content_width_micrometers,
                limits.dimension_micrometers,
            )?;
            let line_height = dimension(
                raw_cell.line_height_micrometers,
                limits.dimension_micrometers,
            )?;
            if preferred < minimum {
                return Err(FontMetricReceiptError::MetricInvalid);
            }
            cells.push(CurrentFontMetricCell {
                cell_id: LogicalId::parse(raw_cell.cell_id)
                    .map_err(|_| FontMetricReceiptError::CellIdentityMismatch)?,
                minimum_content_width: minimum,
                preferred_content_width: preferred,
                line_height,
            });
        }
        Ok(Self {
            receipt_sha256: hex_digest(Sha256::digest(source).into()),
            measurement_set_sha256: raw.measurement_set_sha256,
            cells,
            dimension_limit: limits.dimension_micrometers,
        })
    }

    #[must_use]
    pub fn receipt_sha256(&self) -> &str {
        &self.receipt_sha256
    }

    #[must_use]
    pub fn measurement_set_sha256(&self) -> &str {
        &self.measurement_set_sha256
    }

    #[must_use]
    pub fn cells(&self) -> &[CurrentFontMetricCell] {
        &self.cells
    }

    /// Builds one verified solver measurement without exposing the source text.
    ///
    /// # Errors
    ///
    /// Rejects an unknown cell, negative or oversized margin, or a checked outer-width overflow.
    pub fn table_cell_measure(
        &self,
        cell_id: &LogicalId,
        leading_margin: LengthMicrometers,
        trailing_margin: LengthMicrometers,
    ) -> Result<TableCellMeasure, FontMetricReceiptError> {
        validate_margin(leading_margin, self.dimension_limit)?;
        validate_margin(trailing_margin, self.dimension_limit)?;
        let cell = self
            .cells
            .iter()
            .find(|candidate| candidate.cell_id == *cell_id)
            .ok_or(FontMetricReceiptError::CellMissing)?;
        let outer = leading_margin
            .as_i64()
            .checked_add(trailing_margin.as_i64())
            .and_then(|value| value.checked_add(cell.preferred_content_width.as_i64()))
            .filter(|value| *value <= self.dimension_limit)
            .ok_or(FontMetricReceiptError::MetricInvalid)?;
        if outer <= 0 {
            return Err(FontMetricReceiptError::MetricInvalid);
        }
        Ok(TableCellMeasure {
            master_cell_id: cell.cell_id.clone(),
            leading_margin,
            trailing_margin,
            unbreakable_content_width: cell.minimum_content_width,
            preferred_content_width: cell.preferred_content_width,
            line_height: cell.line_height,
            font_metric_evidence: FontMetricEvidence {
                status: FontMetricStatus::Verified,
                profile_id: Some(CURRENT_FONT_METRIC_PROFILE_ID.to_owned()),
                source_sha256: Some(self.receipt_sha256.clone()),
            },
        })
    }
}

impl fmt::Debug for CurrentFontMetricReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CurrentFontMetricReceipt")
            .field("cell_count", &self.cells.len())
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum FontMetricReceiptError {
    #[error("font metric receipt limits are invalid")]
    InvalidLimit,
    #[error("font metric receipt input exceeds its finite limit")]
    InputLimit,
    #[error("font metric receipt JSON is malformed or ambiguous")]
    MalformedJson,
    #[error("font metric receipt target or profile is unsupported")]
    UnsupportedTarget,
    #[error("font metric receipt cell count exceeds the exact profile")]
    CellLimit,
    #[error("font metric receipt measurement digest differs")]
    MeasurementDigestMismatch,
    #[error("font metric receipt cell identity differs")]
    CellIdentityMismatch,
    #[error("font metric receipt cell is missing")]
    CellMissing,
    #[error("font metric receipt dimension is invalid")]
    MetricInvalid,
    #[error("font metric receipt allocation failed")]
    AllocationFailed,
}

impl FontMetricReceiptError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidLimit => "font_metric_receipt_invalid_limit",
            Self::InputLimit => "font_metric_receipt_input_limit",
            Self::MalformedJson => "font_metric_receipt_malformed_json",
            Self::UnsupportedTarget => "font_metric_receipt_unsupported_target",
            Self::CellLimit => "font_metric_receipt_cell_limit",
            Self::MeasurementDigestMismatch => "font_metric_receipt_measurement_digest_mismatch",
            Self::CellIdentityMismatch => "font_metric_receipt_cell_identity_mismatch",
            Self::CellMissing => "font_metric_receipt_cell_missing",
            Self::MetricInvalid => "font_metric_receipt_metric_invalid",
            Self::AllocationFailed => "font_metric_receipt_allocation_failed",
        }
    }
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct RawReceipt {
    schema_version: String,
    run_id: String,
    scope: String,
    state: String,
    profile_id: String,
    target: RawTarget,
    measurement: RawMeasurement,
    cells: Vec<RawCell>,
    measurement_set_sha256: String,
    visible_text_present: RawBooleanClaim,
    user_document_opened: RawBooleanClaim,
    hwp_process_created: RawBooleanClaim,
    external_network_invoked: RawBooleanClaim,
    registry_or_system_setting_changed: RawBooleanClaim,
    computer_use_click_or_type_invoked: RawBooleanClaim,
    actual_hangul_renderer: RawBooleanClaim,
    other_pc_or_version: RawBooleanClaim,
    product_complete: RawBooleanClaim,
}

#[derive(Deserialize)]
#[serde(transparent)]
struct RawBooleanClaim(bool);

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct RawTarget {
    hangul_build: String,
    architecture: String,
    executable_sha256: String,
    font_file_name: String,
    font_file_bytes: u64,
    font_file_sha256: String,
    font_family: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct RawMeasurement {
    provider: String,
    dpi: u32,
    font_size_millipoints: u32,
    repeat_count: u32,
    conversion: String,
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct RawCell {
    cell_id: String,
    text_sha256: String,
    minimum_content_width_micrometers: i64,
    preferred_content_width_micrometers: i64,
    line_height_micrometers: i64,
}

fn validate_envelope(raw: &RawReceipt) -> Result<(), FontMetricReceiptError> {
    if raw.schema_version != RECEIPT_SCHEMA_VERSION
        || raw.scope != RECEIPT_SCOPE
        || raw.state != "pass"
        || raw.profile_id != CURRENT_FONT_METRIC_PROFILE_ID
        || raw.run_id.len() != 32
        || !raw
            .run_id
            .bytes()
            .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
        || raw.target.hangul_build != HANGUL_BUILD
        || raw.target.architecture != "x86"
        || raw.target.executable_sha256 != HANGUL_EXECUTABLE_SHA256
        || raw.target.font_file_name != FONT_FILE_NAME
        || raw.target.font_file_bytes != FONT_FILE_BYTES
        || raw.target.font_file_sha256 != FONT_FILE_SHA256
        || raw.target.font_family != FONT_FAMILY
        || raw.measurement.provider != MEASUREMENT_PROVIDER
        || raw.measurement.dpi != 96
        || raw.measurement.font_size_millipoints != 10_000
        || raw.measurement.repeat_count != 2
        || raw.measurement.conversion != MEASUREMENT_CONVERSION
        || raw.visible_text_present.0
        || raw.user_document_opened.0
        || raw.hwp_process_created.0
        || raw.external_network_invoked.0
        || raw.registry_or_system_setting_changed.0
        || raw.computer_use_click_or_type_invoked.0
        || raw.actual_hangul_renderer.0
        || raw.other_pc_or_version.0
        || raw.product_complete.0
    {
        return Err(FontMetricReceiptError::UnsupportedTarget);
    }
    Ok(())
}

fn dimension(value: i64, limit: i64) -> Result<LengthMicrometers, FontMetricReceiptError> {
    if value <= 0 || value > limit {
        return Err(FontMetricReceiptError::MetricInvalid);
    }
    Ok(LengthMicrometers::from_raw(value))
}

fn validate_margin(value: LengthMicrometers, limit: i64) -> Result<(), FontMetricReceiptError> {
    if value.as_i64() < 0 || value.as_i64() > limit {
        return Err(FontMetricReceiptError::MetricInvalid);
    }
    Ok(())
}

fn is_lower_hex(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
}

fn hex_digest(value: [u8; 32]) -> String {
    const HEX: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(64);
    for byte in value {
        output.push(char::from(HEX[usize::from(byte >> 4)]));
        output.push(char::from(HEX[usize::from(byte & 0x0f)]));
    }
    output
}
