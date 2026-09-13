use std::collections::{BTreeMap, BTreeSet};
use std::fmt;

use domain_ir::{TableNumberFormatError, TableNumberFormatLimits, TableNumberFormatPlan};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use super::*;

pub const TABLE_NUMBER_FORMAT_HWPX_SCHEMA_VERSION: &str = "hwpx-agent.table-number-format-hwpx/v1";
pub const TABLE_NUMBER_FORMAT_HWPX_PROFILE_ID: &str =
    "hwpx-agent.table-number-format-hwpx.hancom-2020/1";

#[derive(Clone, Eq, PartialEq)]
pub struct TableNumberFormatHwpxReadback {
    profile_id: &'static str,
    rows: u32,
    columns: u32,
    selected_formulas: Vec<FormulaCell>,
    selected_native_grouping: Vec<bool>,
    formula_field_count: usize,
    section_sha256: [u8; 32],
    selected_state_sha256: [u8; 32],
    grid_sha256: [u8; 32],
    unowned_sha256: [u8; 32],
}

impl TableNumberFormatHwpxReadback {
    #[must_use]
    pub const fn profile_id(&self) -> &'static str {
        self.profile_id
    }

    #[must_use]
    pub const fn dimensions(&self) -> FormulaGridDimensions {
        FormulaGridDimensions {
            rows: self.rows,
            columns: self.columns,
        }
    }

    #[must_use]
    pub fn selected_formulas(&self) -> &[FormulaCell] {
        &self.selected_formulas
    }

    #[must_use]
    pub fn selected_native_grouping(&self) -> &[bool] {
        &self.selected_native_grouping
    }

    #[must_use]
    pub const fn formula_field_count(&self) -> usize {
        self.formula_field_count
    }

    #[must_use]
    pub const fn section_sha256(&self) -> [u8; 32] {
        self.section_sha256
    }

    #[must_use]
    pub const fn selected_state_sha256(&self) -> [u8; 32] {
        self.selected_state_sha256
    }

    #[must_use]
    pub const fn grid_sha256(&self) -> [u8; 32] {
        self.grid_sha256
    }

    #[must_use]
    pub const fn unowned_sha256(&self) -> [u8; 32] {
        self.unowned_sha256
    }
}

impl fmt::Debug for TableNumberFormatHwpxReadback {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableNumberFormatHwpxReadback")
            .field("profile_id", &self.profile_id)
            .field("rows", &self.rows)
            .field("columns", &self.columns)
            .field("selected_formula_count", &self.selected_formulas.len())
            .field("selected_native_grouping", &"<redacted>")
            .field("formula_field_count", &self.formula_field_count)
            .field("section_sha256", &"<redacted>")
            .field("selected_state_sha256", &"<redacted>")
            .field("grid_sha256", &"<redacted>")
            .field("unowned_sha256", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableNumberFormatHwpxRequestDraft {
    pub schema_version: String,
    pub table_ordinal: usize,
    pub expected_section_sha256: String,
    pub expected_source_state_sha256: String,
    pub expected_source_grid_sha256: String,
    pub expected_document_flow_sha256: String,
    pub expected_plan_sha256: String,
}

impl fmt::Debug for TableNumberFormatHwpxRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableNumberFormatHwpxRequestDraft")
            .field("schema_version", &self.schema_version)
            .field("table_ordinal", &self.table_ordinal)
            .field("expected_section_sha256", &"<redacted>")
            .field("expected_source_state_sha256", &"<redacted>")
            .field("expected_source_grid_sha256", &"<redacted>")
            .field("expected_document_flow_sha256", &"<redacted>")
            .field("expected_plan_sha256", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableNumberFormatHwpxRequest {
    schema_version: &'static str,
    table_ordinal: usize,
    expected_section_sha256: String,
    expected_source_state_sha256: String,
    expected_source_grid_sha256: String,
    expected_document_flow_sha256: String,
    expected_plan_sha256: String,
}

impl TableNumberFormatHwpxRequest {
    /// Binds one exact number-format plan to the selected native formula fields and section.
    ///
    /// # Errors
    ///
    /// Rejects stale bindings, unsupported native formats or values, and plans that change any
    /// selected formula state other than its number format.
    pub fn from_draft(
        draft: TableNumberFormatHwpxRequestDraft,
        section: &[u8],
        plan: &TableNumberFormatPlan,
        current_document_flow_sha256: &str,
        limits: TableFormulaHwpxLimits,
        number_format_limits: TableNumberFormatLimits,
        formula_limits: FormulaLimits,
    ) -> Result<Self, TableNumberFormatHwpxError> {
        if draft.schema_version != TABLE_NUMBER_FORMAT_HWPX_SCHEMA_VERSION {
            return Err(TableNumberFormatHwpxError::UnsupportedVersion);
        }
        if draft.table_ordinal >= limits.config().tables {
            return Err(TableNumberFormatHwpxError::TableOrdinalLimit);
        }
        validate_digest(current_document_flow_sha256)?;
        for digest in [
            &draft.expected_section_sha256,
            &draft.expected_source_state_sha256,
            &draft.expected_source_grid_sha256,
            &draft.expected_document_flow_sha256,
            &draft.expected_plan_sha256,
        ] {
            validate_digest(digest)?;
        }
        let shape = read_selected_shape(
            section,
            draft.table_ordinal,
            plan.request().selected_cells(),
            limits,
            formula_limits,
        )?;
        let targets = validate_plan_against_source(plan, &shape.readback)?;
        validate_native_outputs(&shape.selected, &targets)?;
        let plan_sha256 = plan.canonical_sha256(number_format_limits)?;
        if draft.expected_section_sha256 != hex(shape.readback.section_sha256)
            || draft.expected_source_state_sha256 != hex(shape.readback.selected_state_sha256)
            || draft.expected_source_grid_sha256 != hex(shape.readback.grid_sha256)
            || draft.expected_document_flow_sha256 != current_document_flow_sha256
            || draft.expected_plan_sha256 != hex(plan_sha256)
        {
            return Err(TableNumberFormatHwpxError::RequestBindingMismatch);
        }
        let request = Self {
            schema_version: TABLE_NUMBER_FORMAT_HWPX_SCHEMA_VERSION,
            table_ordinal: draft.table_ordinal,
            expected_section_sha256: draft.expected_section_sha256,
            expected_source_state_sha256: draft.expected_source_state_sha256,
            expected_source_grid_sha256: draft.expected_source_grid_sha256,
            expected_document_flow_sha256: draft.expected_document_flow_sha256,
            expected_plan_sha256: draft.expected_plan_sha256,
        };
        let _ = request.canonical_json(limits)?;
        Ok(request)
    }

    /// Parses strict bounded JSON and applies the same bindings as [`Self::from_draft`].
    ///
    /// # Errors
    ///
    /// Rejects empty, oversized, duplicate-key, unknown-field and semantically invalid requests.
    pub fn from_json(
        bytes: &[u8],
        section: &[u8],
        plan: &TableNumberFormatPlan,
        current_document_flow_sha256: &str,
        limits: TableFormulaHwpxLimits,
        number_format_limits: TableNumberFormatLimits,
        formula_limits: FormulaLimits,
    ) -> Result<Self, TableNumberFormatHwpxError> {
        if bytes.is_empty() || bytes.len() > limits.config().text_bytes {
            return Err(TableNumberFormatHwpxError::InputLimit);
        }
        let draft =
            serde_json::from_slice(bytes).map_err(|_| TableNumberFormatHwpxError::InvalidJson)?;
        Self::from_draft(
            draft,
            section,
            plan,
            current_document_flow_sha256,
            limits,
            number_format_limits,
            formula_limits,
        )
    }

    #[must_use]
    pub const fn table_ordinal(&self) -> usize {
        self.table_ordinal
    }

    #[must_use]
    pub fn expected_document_flow_sha256(&self) -> &str {
        &self.expected_document_flow_sha256
    }

    /// Returns deterministic bounded request JSON.
    ///
    /// # Errors
    ///
    /// Returns an error when serialization fails or exceeds the configured bound.
    pub fn canonical_json(
        &self,
        limits: TableFormulaHwpxLimits,
    ) -> Result<Vec<u8>, TableNumberFormatHwpxError> {
        let bytes =
            serde_json::to_vec(self).map_err(|_| TableNumberFormatHwpxError::Serialization)?;
        if bytes.len() > limits.config().text_bytes {
            return Err(TableNumberFormatHwpxError::OutputLimit);
        }
        Ok(bytes)
    }
}

impl fmt::Debug for TableNumberFormatHwpxRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableNumberFormatHwpxRequest")
            .field("schema_version", &self.schema_version)
            .field("table_ordinal", &self.table_ordinal)
            .field("expected_section_sha256", &"<redacted>")
            .field("expected_source_state_sha256", &"<redacted>")
            .field("expected_source_grid_sha256", &"<redacted>")
            .field("expected_document_flow_sha256", &"<redacted>")
            .field("expected_plan_sha256", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableNumberFormatHwpxLoweringReceipt {
    profile_id: &'static str,
    capability_id: &'static str,
    source_section_sha256: [u8; 32],
    output_section_sha256: [u8; 32],
    source_state_sha256: [u8; 32],
    target_state_sha256: [u8; 32],
    grid_sha256_before: [u8; 32],
    grid_sha256_after: [u8; 32],
    document_flow_sha256_before: [u8; 32],
    document_flow_sha256_after: [u8; 32],
    plan_sha256: [u8; 32],
    unowned_sha256: [u8; 32],
    selected_formula_cells: usize,
    modified_text_count: usize,
}

impl TableNumberFormatHwpxLoweringReceipt {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
    }

    #[must_use]
    pub const fn selected_formula_cells(&self) -> usize {
        self.selected_formula_cells
    }

    #[must_use]
    pub const fn modified_text_count(&self) -> usize {
        self.modified_text_count
    }

    #[must_use]
    pub fn grid_preserved(&self) -> bool {
        self.grid_sha256_before == self.grid_sha256_after
    }

    #[must_use]
    pub fn document_flow_preserved(&self) -> bool {
        self.document_flow_sha256_before == self.document_flow_sha256_after
    }

    #[must_use]
    pub const fn source_section_sha256(&self) -> [u8; 32] {
        self.source_section_sha256
    }

    #[must_use]
    pub const fn output_section_sha256(&self) -> [u8; 32] {
        self.output_section_sha256
    }
}

impl fmt::Debug for TableNumberFormatHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableNumberFormatHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field("capability_id", &self.capability_id)
            .field("source_section_sha256", &"<redacted>")
            .field("output_section_sha256", &"<redacted>")
            .field("source_state_sha256", &"<redacted>")
            .field("target_state_sha256", &"<redacted>")
            .field("grid_sha256_before", &"<redacted>")
            .field("grid_sha256_after", &"<redacted>")
            .field("document_flow_sha256_before", &"<redacted>")
            .field("document_flow_sha256_after", &"<redacted>")
            .field("plan_sha256", &"<redacted>")
            .field("unowned_sha256", &"<redacted>")
            .field("selected_formula_cells", &self.selected_formula_cells)
            .field("modified_text_count", &self.modified_text_count)
            .finish()
    }
}

#[derive(Debug)]
pub struct TableNumberFormatHwpxReader;

impl TableNumberFormatHwpxReader {
    /// Reads selected exact-target native formula number formats from one section table.
    ///
    /// # Errors
    ///
    /// Rejects merged or ambiguous grids, non-integer result values, unknown native tokens,
    /// malformed metadata, and selected formula ownership ambiguity.
    pub fn read_selected_in_section(
        section: &[u8],
        table_ordinal: usize,
        selected_cells: &[CellCoordinate],
        limits: TableFormulaHwpxLimits,
        formula_limits: FormulaLimits,
    ) -> Result<TableNumberFormatHwpxReadback, TableNumberFormatHwpxError> {
        Ok(read_selected_shape(
            section,
            table_ordinal,
            selected_cells,
            limits,
            formula_limits,
        )?
        .readback)
    }
}

#[derive(Debug)]
pub struct TableNumberFormatHwpxLowerer;

impl TableNumberFormatHwpxLowerer {
    /// Applies one exact native number-format plan to selected formula fields.
    ///
    /// Only `Command`, `ResultFormat`, `LastResult` and visible-result text are mutable. Formula
    /// source, field identity, grid, every unselected field and all other section bytes are exact.
    ///
    /// # Errors
    ///
    /// Rechecks section/state/grid/flow/plan bindings, applies bounded edits and returns no bytes
    /// unless semantic readback plus unowned-byte preservation both pass.
    pub fn lower_in_section_with_receipt(
        request: &TableNumberFormatHwpxRequest,
        section: &[u8],
        plan: &TableNumberFormatPlan,
        current_document_flow_sha256: &str,
        limits: TableFormulaHwpxLimits,
        number_format_limits: TableNumberFormatLimits,
        formula_limits: FormulaLimits,
    ) -> Result<(Vec<u8>, TableNumberFormatHwpxLoweringReceipt), TableNumberFormatHwpxError> {
        validate_digest(current_document_flow_sha256)?;
        if request.expected_document_flow_sha256 != current_document_flow_sha256 {
            return Err(TableNumberFormatHwpxError::FlowBindingMismatch);
        }
        let source_shape = read_selected_shape(
            section,
            request.table_ordinal,
            plan.request().selected_cells(),
            limits,
            formula_limits,
        )?;
        let targets = validate_plan_against_source(plan, &source_shape.readback)?;
        let native_outputs = validate_native_outputs(&source_shape.selected, &targets)?;
        let plan_sha256 = plan.canonical_sha256(number_format_limits)?;
        if request.expected_section_sha256 != hex(source_shape.readback.section_sha256) {
            return Err(TableNumberFormatHwpxError::SectionBindingMismatch);
        }
        if request.expected_source_state_sha256 != hex(source_shape.readback.selected_state_sha256)
        {
            return Err(TableNumberFormatHwpxError::StateBindingMismatch);
        }
        if request.expected_source_grid_sha256 != hex(source_shape.readback.grid_sha256) {
            return Err(TableNumberFormatHwpxError::GridBindingMismatch);
        }
        if request.expected_plan_sha256 != hex(plan_sha256) {
            return Err(TableNumberFormatHwpxError::PlanBindingMismatch);
        }

        let mut edits = native_edits(&source_shape.selected, &native_outputs)?;
        let modified_text_count = edits.len();
        let output = apply_edits(section, &mut edits, limits)?;
        let output_shape = read_selected_shape(
            &output,
            request.table_ordinal,
            plan.request().selected_cells(),
            limits,
            formula_limits,
        )?;
        if output_shape.readback.selected_formulas != targets.formulas
            || output_shape.readback.selected_native_grouping != targets.native_grouping
            || output_shape.readback.grid_sha256 != source_shape.readback.grid_sha256
            || output_shape.readback.formula_field_count
                != source_shape.readback.formula_field_count
        {
            return Err(TableNumberFormatHwpxError::ReadbackMismatch);
        }
        if output_shape.readback.unowned_sha256 != source_shape.readback.unowned_sha256 {
            return Err(TableNumberFormatHwpxError::PreservationMismatch);
        }
        let flow = parse_digest(current_document_flow_sha256)?;
        let receipt = TableNumberFormatHwpxLoweringReceipt {
            profile_id: TABLE_NUMBER_FORMAT_HWPX_PROFILE_ID,
            capability_id: plan.request().capability_id(),
            source_section_sha256: source_shape.readback.section_sha256,
            output_section_sha256: output_shape.readback.section_sha256,
            source_state_sha256: source_shape.readback.selected_state_sha256,
            target_state_sha256: output_shape.readback.selected_state_sha256,
            grid_sha256_before: source_shape.readback.grid_sha256,
            grid_sha256_after: output_shape.readback.grid_sha256,
            document_flow_sha256_before: flow,
            document_flow_sha256_after: flow,
            plan_sha256,
            unowned_sha256: output_shape.readback.unowned_sha256,
            selected_formula_cells: output_shape.readback.selected_formulas.len(),
            modified_text_count,
        };
        Ok((output, receipt))
    }
}

#[derive(Debug, Error)]
pub enum TableNumberFormatHwpxError {
    #[error("table number-format HWPX input is empty or oversized")]
    InputLimit,
    #[error("table number-format HWPX JSON is invalid")]
    InvalidJson,
    #[error("table number-format HWPX schema version is unsupported")]
    UnsupportedVersion,
    #[error("table number-format HWPX table ordinal exceeds its limit")]
    TableOrdinalLimit,
    #[error("table number-format HWPX digest is invalid")]
    InvalidDigest,
    #[error("table number-format HWPX request binding does not match current source")]
    RequestBindingMismatch,
    #[error("table number-format HWPX section binding does not match")]
    SectionBindingMismatch,
    #[error("table number-format HWPX selected-state binding does not match")]
    StateBindingMismatch,
    #[error("table number-format HWPX grid binding does not match")]
    GridBindingMismatch,
    #[error("table number-format HWPX document-flow binding does not match")]
    FlowBindingMismatch,
    #[error("table number-format HWPX plan binding does not match")]
    PlanBindingMismatch,
    #[error("table number-format HWPX plan changes unsupported state")]
    PlanMismatch,
    #[error("table number-format HWPX target format is outside the native profile")]
    UnsupportedTargetFormat,
    #[error("table number-format HWPX native formula profile is unsupported")]
    UnsupportedNativeProfile,
    #[error("table number-format HWPX semantic readback does not match")]
    ReadbackMismatch,
    #[error("table number-format HWPX unowned bytes changed")]
    PreservationMismatch,
    #[error("table number-format HWPX output exceeds its limit")]
    OutputLimit,
    #[error("table number-format HWPX serialization failed")]
    Serialization,
    #[error("table number-format HWPX allocation failed")]
    AllocationFailed,
    #[error("table number-format HWPX core plan failed: {0}")]
    Plan(#[from] TableNumberFormatError),
    #[error("table number-format HWPX formula state failed: {0}")]
    Formula(#[from] FormulaError),
    #[error("table number-format HWPX formula section failed: {0}")]
    FormulaHwpx(#[from] TableFormulaHwpxError),
}

impl TableNumberFormatHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InputLimit => "table_number_format_hwpx_input_limit",
            Self::InvalidJson => "table_number_format_hwpx_invalid_json",
            Self::UnsupportedVersion => "table_number_format_hwpx_unsupported_version",
            Self::TableOrdinalLimit => "table_number_format_hwpx_table_ordinal_limit",
            Self::InvalidDigest => "table_number_format_hwpx_invalid_digest",
            Self::RequestBindingMismatch => "table_number_format_hwpx_request_binding_mismatch",
            Self::SectionBindingMismatch => "table_number_format_hwpx_section_binding_mismatch",
            Self::StateBindingMismatch => "table_number_format_hwpx_state_binding_mismatch",
            Self::GridBindingMismatch => "table_number_format_hwpx_grid_binding_mismatch",
            Self::FlowBindingMismatch => "table_number_format_hwpx_flow_binding_mismatch",
            Self::PlanBindingMismatch => "table_number_format_hwpx_plan_binding_mismatch",
            Self::PlanMismatch => "table_number_format_hwpx_plan_mismatch",
            Self::UnsupportedTargetFormat => "table_number_format_hwpx_unsupported_target_format",
            Self::UnsupportedNativeProfile => "table_number_format_hwpx_unsupported_native_profile",
            Self::ReadbackMismatch => "table_number_format_hwpx_readback_mismatch",
            Self::PreservationMismatch => "table_number_format_hwpx_preservation_mismatch",
            Self::OutputLimit => "table_number_format_hwpx_output_limit",
            Self::Serialization => "table_number_format_hwpx_serialization",
            Self::AllocationFailed => "table_number_format_hwpx_allocation",
            Self::Plan(_) => "table_number_format_hwpx_core_plan",
            Self::Formula(_) => "table_number_format_hwpx_formula_state",
            Self::FormulaHwpx(_) => "table_number_format_hwpx_formula_section",
        }
    }
}

struct SelectedShape {
    readback: TableNumberFormatHwpxReadback,
    selected: Vec<SelectedNativeFormula>,
}

struct SelectedNativeFormula {
    command_span: XmlByteSpan,
    command: String,
    result_format_span: XmlByteSpan,
    result_format: String,
    last_result_span: XmlByteSpan,
    last_result: String,
    visible_result_span: XmlByteSpan,
    visible_result: String,
    native_formula: String,
    value: FormulaDecimal,
    use_grouping: bool,
}

fn read_selected_shape(
    section: &[u8],
    table_ordinal: usize,
    selected_cells: &[CellCoordinate],
    limits: TableFormulaHwpxLimits,
    formula_limits: FormulaLimits,
) -> Result<SelectedShape, TableNumberFormatHwpxError> {
    if selected_cells.is_empty() || selected_cells.len() > limits.config().formula_fields {
        return Err(TableNumberFormatHwpxError::UnsupportedNativeProfile);
    }
    let selected_set = selected_cells.iter().copied().collect::<BTreeSet<_>>();
    if selected_set.len() != selected_cells.len() {
        return Err(TableNumberFormatHwpxError::UnsupportedNativeProfile);
    }
    let document = parse_document(section, limits)?;
    validate_document_envelope(&document)?;
    validate_section_root(&document)?;
    let table = table_indexes(&document, limits)?
        .get(table_ordinal)
        .copied()
        .ok_or(TableNumberFormatHwpxError::UnsupportedNativeProfile)?;
    let grid = read_cells(&document, table, limits, false)?;
    let dimensions = FormulaGridDimensions {
        rows: grid.rows,
        columns: grid.columns,
    };
    if selected_cells
        .iter()
        .any(|coordinate| coordinate.row >= grid.rows || coordinate.column >= grid.columns)
    {
        return Err(TableNumberFormatHwpxError::UnsupportedNativeProfile);
    }
    let fields = formula_fields(&document, table, limits)?;
    let mut by_owner = BTreeMap::new();
    for field_begin in &fields {
        let cell = owning_direct_cell(&document, *field_begin, table)?;
        let owner = grid
            .cells
            .iter()
            .find_map(|(index, coordinate)| (*index == cell).then_some(*coordinate))
            .ok_or(TableNumberFormatHwpxError::UnsupportedNativeProfile)?;
        if !selected_set.contains(&owner) {
            continue;
        }
        let selected = read_selected_native_formula(
            &document,
            *field_begin,
            owner,
            dimensions,
            limits,
            formula_limits,
        )?;
        if by_owner.insert(owner, selected).is_some() {
            return Err(TableNumberFormatHwpxError::UnsupportedNativeProfile);
        }
    }
    if by_owner.len() != selected_cells.len() {
        return Err(TableNumberFormatHwpxError::UnsupportedNativeProfile);
    }
    let (selected, formulas, grouping) =
        collect_selected(by_owner, selected_set, selected_cells.len())?;
    let spans = selected
        .iter()
        .flat_map(|value| {
            [
                value.command_span,
                value.result_format_span,
                value.last_result_span,
                value.visible_result_span,
            ]
        })
        .collect::<Vec<_>>();
    let selected_state_sha256 = selected_state_digest(&formulas, &grouping, formula_limits)?;
    let grid_sha256 = grid_digest(&grid);
    let unowned_sha256 = digest_excluding(section, &spans, TABLE_NUMBER_FORMAT_HWPX_PROFILE_ID)?;
    Ok(SelectedShape {
        readback: TableNumberFormatHwpxReadback {
            profile_id: TABLE_NUMBER_FORMAT_HWPX_PROFILE_ID,
            rows: grid.rows,
            columns: grid.columns,
            selected_formulas: formulas,
            selected_native_grouping: grouping,
            formula_field_count: fields.len(),
            section_sha256: Sha256::digest(section).into(),
            selected_state_sha256,
            grid_sha256,
            unowned_sha256,
        },
        selected,
    })
}

struct ParsedSelectedFormula {
    formula: FormulaCell,
    native: SelectedNativeFormula,
}

type CollectedSelected = (Vec<SelectedNativeFormula>, Vec<FormulaCell>, Vec<bool>);

fn collect_selected(
    mut by_owner: BTreeMap<CellCoordinate, ParsedSelectedFormula>,
    selected_set: BTreeSet<CellCoordinate>,
    selected_len: usize,
) -> Result<CollectedSelected, TableNumberFormatHwpxError> {
    let mut selected = Vec::new();
    let mut formulas = Vec::new();
    let mut grouping = Vec::new();
    selected
        .try_reserve_exact(selected_len)
        .map_err(|_| TableNumberFormatHwpxError::AllocationFailed)?;
    formulas
        .try_reserve_exact(selected_len)
        .map_err(|_| TableNumberFormatHwpxError::AllocationFailed)?;
    grouping
        .try_reserve_exact(selected_len)
        .map_err(|_| TableNumberFormatHwpxError::AllocationFailed)?;
    for coordinate in selected_set {
        let value = by_owner
            .remove(&coordinate)
            .ok_or(TableNumberFormatHwpxError::UnsupportedNativeProfile)?;
        formulas.push(value.formula);
        grouping.push(value.native.use_grouping);
        selected.push(value.native);
    }
    Ok((selected, formulas, grouping))
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum NativeNumberFormat {
    General,
    Number { decimal_places: u8 },
}

impl NativeNumberFormat {
    const fn token(self) -> &'static str {
        match self {
            Self::General => "%g,",
            Self::Number { decimal_places: 0 } => "%.0f,",
            Self::Number { decimal_places: 1 } => "%.1f,",
            Self::Number { decimal_places: 2 } => "%.2f,",
            Self::Number { decimal_places: 3 } => "%.3f,",
            Self::Number { decimal_places: 4 } => "%.4f,",
            Self::Number { .. } => "",
        }
    }
}

fn read_selected_native_formula(
    document: &PreservingXmlDocument,
    field_begin: usize,
    owner: CellCoordinate,
    dimensions: FormulaGridDimensions,
    limits: TableFormulaHwpxLimits,
    formula_limits: FormulaLimits,
) -> Result<ParsedSelectedFormula, TableNumberFormatHwpxError> {
    let envelope = validate_field_envelope(document, field_begin, limits)?;
    let parameters = read_field_parameters(document, envelope.parameters, limits)?;
    if parameters.native_formula.text != NATIVE_LEFT_FORMULA {
        return Err(TableNumberFormatHwpxError::UnsupportedNativeProfile);
    }
    let native_format = parse_native_format(parameters.result_format.text)?;
    if parameters.command.text
        != format!(
            "{}??{};;{}",
            parameters.native_formula.text,
            native_format.token(),
            parameters.last_result.text
        )
    {
        return Err(TableNumberFormatHwpxError::UnsupportedNativeProfile);
    }
    let visible = leaf_text_with_span(document, envelope.visible_result, limits)?;
    let (value, grouped_result, plain_result, decimal_places) =
        parse_grouped_integer_result(parameters.last_result.text, formula_limits)?;
    if value.scale() != 0
        || match native_format {
            NativeNumberFormat::General => decimal_places != 0,
            NativeNumberFormat::Number {
                decimal_places: expected,
            } => decimal_places != expected,
        }
    {
        return Err(TableNumberFormatHwpxError::UnsupportedNativeProfile);
    }
    let use_grouping = if visible.text == grouped_result {
        true
    } else if visible.text == plain_result {
        false
    } else {
        return Err(TableNumberFormatHwpxError::UnsupportedNativeProfile);
    };
    let number_format = match native_format {
        NativeNumberFormat::General => FormulaNumberFormat::General,
        NativeNumberFormat::Number { decimal_places } => FormulaNumberFormat::Number {
            decimal_places,
            use_grouping,
        },
    };
    let ast = left_prefix_ast(owner, formula_limits)?;
    let formula = FormulaCell::from_draft(
        FormulaCellDraft {
            schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
            owner,
            ast: FormulaAstDraft {
                schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
                expression: ast.expression().clone(),
            },
            cache: FormulaCache::Unverified {
                value: FormulaValue::Decimal { value },
            },
            number_format,
        },
        dimensions,
        formula_limits,
    )?;
    Ok(ParsedSelectedFormula {
        formula,
        native: SelectedNativeFormula {
            command_span: parameters.command.span,
            command: parameters.command.text.to_owned(),
            result_format_span: parameters.result_format.span,
            result_format: parameters.result_format.text.to_owned(),
            last_result_span: parameters.last_result.span,
            last_result: parameters.last_result.text.to_owned(),
            visible_result_span: visible.span,
            visible_result: visible.text.to_owned(),
            native_formula: parameters.native_formula.text.to_owned(),
            value,
            use_grouping,
        },
    })
}

fn parse_native_format(source: &str) -> Result<NativeNumberFormat, TableNumberFormatHwpxError> {
    match source {
        "%g," => Ok(NativeNumberFormat::General),
        "%.0f," => Ok(NativeNumberFormat::Number { decimal_places: 0 }),
        "%.1f," => Ok(NativeNumberFormat::Number { decimal_places: 1 }),
        "%.2f," => Ok(NativeNumberFormat::Number { decimal_places: 2 }),
        "%.3f," => Ok(NativeNumberFormat::Number { decimal_places: 3 }),
        "%.4f," => Ok(NativeNumberFormat::Number { decimal_places: 4 }),
        _ => Err(TableNumberFormatHwpxError::UnsupportedNativeProfile),
    }
}

fn parse_grouped_integer_result(
    source: &str,
    formula_limits: FormulaLimits,
) -> Result<(FormulaDecimal, String, String, u8), TableNumberFormatHwpxError> {
    if source.is_empty()
        || source.len() > formula_limits.config().cache_text_bytes
        || !source.is_ascii()
    {
        return Err(TableNumberFormatHwpxError::UnsupportedNativeProfile);
    }
    let (sign, unsigned) = source
        .strip_prefix('-')
        .map_or(("", source), |value| ("-", value));
    let (integer, fraction) = match unsigned.split_once('.') {
        Some((integer, fraction))
            if !fraction.is_empty()
                && !fraction.contains('.')
                && fraction.bytes().all(|byte| byte.is_ascii_digit()) =>
        {
            (integer, Some(fraction))
        }
        Some(_) => return Err(TableNumberFormatHwpxError::UnsupportedNativeProfile),
        None => (unsigned, None),
    };
    let decimal_places = fraction
        .map(|value| u8::try_from(value.len()))
        .transpose()
        .map_err(|_| TableNumberFormatHwpxError::UnsupportedNativeProfile)?
        .unwrap_or(0);
    let groups = integer.split(',').collect::<Vec<_>>();
    if groups.len() < 2
        || groups[0].is_empty()
        || groups[0].len() > 3
        || (groups[0].len() > 1 && groups[0].starts_with('0'))
        || groups[0].bytes().any(|byte| !byte.is_ascii_digit())
        || groups[1..]
            .iter()
            .any(|group| group.len() != 3 || group.bytes().any(|byte| !byte.is_ascii_digit()))
    {
        return Err(TableNumberFormatHwpxError::UnsupportedNativeProfile);
    }
    let mut plain = String::new();
    plain
        .try_reserve(source.len())
        .map_err(|_| TableNumberFormatHwpxError::AllocationFailed)?;
    plain.push_str(sign);
    for group in groups {
        plain.push_str(group);
    }
    if let Some(fraction) = fraction {
        plain.push('.');
        plain.push_str(fraction);
    }
    let canonical = match fraction {
        Some(fraction) => {
            let significant = fraction.trim_end_matches('0');
            if significant.is_empty() {
                format!("{sign}{}", integer.replace(',', ""))
            } else {
                format!("{sign}{}.{significant}", integer.replace(',', ""))
            }
        }
        None => plain.clone(),
    };
    let value = parse_canonical_decimal(&canonical, formula_limits)?;
    Ok((value, source.to_owned(), plain, decimal_places))
}

struct TargetShape {
    formulas: Vec<FormulaCell>,
    native_grouping: Vec<bool>,
}

fn validate_plan_against_source(
    plan: &TableNumberFormatPlan,
    source: &TableNumberFormatHwpxReadback,
) -> Result<TargetShape, TableNumberFormatHwpxError> {
    let selected = plan.request().selected_cells();
    if plan.request().capability_id() != "table.number_format"
        || selected.len() != source.selected_formulas.len()
        || plan.receipt().selected_formula_cells() != selected.len()
        || !plan.receipt().non_format_state_preserved()
        || selected
            .iter()
            .copied()
            .ne(source.selected_formulas.iter().map(FormulaCell::owner))
    {
        return Err(TableNumberFormatHwpxError::PlanMismatch);
    }
    let mut formulas = Vec::new();
    let mut native_grouping = Vec::new();
    formulas
        .try_reserve_exact(selected.len())
        .map_err(|_| TableNumberFormatHwpxError::AllocationFailed)?;
    native_grouping
        .try_reserve_exact(selected.len())
        .map_err(|_| TableNumberFormatHwpxError::AllocationFailed)?;
    for ((coordinate, before), before_grouping) in selected
        .iter()
        .zip(&source.selected_formulas)
        .zip(&source.selected_native_grouping)
    {
        let target = plan
            .after_state()
            .cells()
            .binary_search_by_key(coordinate, domain_ir::TableNumberFormatCell::coordinate)
            .ok()
            .and_then(|index| plan.after_state().cells().get(index))
            .and_then(|cell| cell.formula())
            .ok_or(TableNumberFormatHwpxError::PlanMismatch)?;
        if before.owner() != target.owner()
            || before.ast() != target.ast()
            || before.cache() != target.cache()
            || target.number_format() != plan.request().target_format()
        {
            return Err(TableNumberFormatHwpxError::PlanMismatch);
        }
        let grouping = match target.number_format() {
            FormulaNumberFormat::General => *before_grouping,
            FormulaNumberFormat::Number {
                decimal_places,
                use_grouping,
            } if decimal_places <= 4 => use_grouping,
            _ => return Err(TableNumberFormatHwpxError::UnsupportedTargetFormat),
        };
        formulas.push(target.clone());
        native_grouping.push(grouping);
    }
    Ok(TargetShape {
        formulas,
        native_grouping,
    })
}

struct NativeOutput {
    command: String,
    result_format: String,
    last_result: String,
    visible_result: String,
}

fn validate_native_outputs(
    selected: &[SelectedNativeFormula],
    targets: &TargetShape,
) -> Result<Vec<NativeOutput>, TableNumberFormatHwpxError> {
    if selected.len() != targets.formulas.len() || selected.len() != targets.native_grouping.len() {
        return Err(TableNumberFormatHwpxError::PlanMismatch);
    }
    selected
        .iter()
        .zip(&targets.formulas)
        .zip(&targets.native_grouping)
        .map(|((source, target), grouping)| native_output(source, target, *grouping))
        .collect()
}

fn native_output(
    source: &SelectedNativeFormula,
    target: &FormulaCell,
    use_grouping: bool,
) -> Result<NativeOutput, TableNumberFormatHwpxError> {
    let FormulaCache::Unverified {
        value: FormulaValue::Decimal { value },
    } = target.cache()
    else {
        return Err(TableNumberFormatHwpxError::UnsupportedNativeProfile);
    };
    if value.scale() != 0 || *value != source.value {
        return Err(TableNumberFormatHwpxError::UnsupportedNativeProfile);
    }
    let (format, decimal_places) = match target.number_format() {
        FormulaNumberFormat::General => (NativeNumberFormat::General, 0),
        FormulaNumberFormat::Number {
            decimal_places,
            use_grouping: target_grouping,
        } if decimal_places <= 4 && target_grouping == use_grouping => (
            NativeNumberFormat::Number { decimal_places },
            decimal_places,
        ),
        FormulaNumberFormat::Number { .. }
        | FormulaNumberFormat::Percent { .. }
        | FormulaNumberFormat::Scientific { .. } => {
            return Err(TableNumberFormatHwpxError::UnsupportedTargetFormat);
        }
    };
    let (mut grouped, mut plain) = integer_display_pair(*value)?;
    if decimal_places > 0 {
        grouped.push('.');
        plain.push('.');
        for _ in 0..decimal_places {
            grouped.push('0');
            plain.push('0');
        }
    }
    let result_format = format.token().to_owned();
    let command = format!("{}??{};;{}", source.native_formula, result_format, grouped);
    let visible_result = if use_grouping { grouped.clone() } else { plain };
    Ok(NativeOutput {
        command,
        result_format,
        last_result: grouped,
        visible_result,
    })
}

fn integer_display_pair(
    value: FormulaDecimal,
) -> Result<(String, String), TableNumberFormatHwpxError> {
    if value.scale() != 0 {
        return Err(TableNumberFormatHwpxError::UnsupportedNativeProfile);
    }
    let coefficient = value.coefficient();
    let negative = coefficient < 0;
    let digits = coefficient.unsigned_abs().to_string();
    if digits.len() < 4 {
        return Err(TableNumberFormatHwpxError::UnsupportedNativeProfile);
    }
    let separator_count = digits.len().saturating_sub(1) / 3;
    let capacity = digits
        .len()
        .checked_add(separator_count)
        .and_then(|value| value.checked_add(usize::from(negative)))
        .ok_or(TableNumberFormatHwpxError::OutputLimit)?;
    let mut grouped = String::new();
    grouped
        .try_reserve(capacity)
        .map_err(|_| TableNumberFormatHwpxError::AllocationFailed)?;
    if negative {
        grouped.push('-');
    }
    let first = digits.len() % 3;
    let mut cursor = 0;
    if first != 0 {
        grouped.push_str(&digits[..first]);
        cursor = first;
    }
    while cursor < digits.len() {
        if cursor > 0 {
            grouped.push(',');
        }
        grouped.push_str(&digits[cursor..cursor + 3]);
        cursor += 3;
    }
    let plain = coefficient.to_string();
    Ok((grouped, plain))
}

fn push_changed(edits: &mut Vec<ByteEdit>, span: XmlByteSpan, source: &str, target: &str) {
    if source != target {
        edits.push(ByteEdit::new(span, target.as_bytes().to_vec()));
    }
}

fn native_edits(
    selected: &[SelectedNativeFormula],
    outputs: &[NativeOutput],
) -> Result<Vec<ByteEdit>, TableNumberFormatHwpxError> {
    let capacity = selected
        .len()
        .checked_mul(4)
        .ok_or(TableNumberFormatHwpxError::OutputLimit)?;
    let mut edits = Vec::new();
    edits
        .try_reserve_exact(capacity)
        .map_err(|_| TableNumberFormatHwpxError::AllocationFailed)?;
    for (source, target) in selected.iter().zip(outputs) {
        push_changed(
            &mut edits,
            source.command_span,
            &source.command,
            &target.command,
        );
        push_changed(
            &mut edits,
            source.result_format_span,
            &source.result_format,
            &target.result_format,
        );
        push_changed(
            &mut edits,
            source.last_result_span,
            &source.last_result,
            &target.last_result,
        );
        push_changed(
            &mut edits,
            source.visible_result_span,
            &source.visible_result,
            &target.visible_result,
        );
    }
    Ok(edits)
}

fn selected_state_digest(
    formulas: &[FormulaCell],
    grouping: &[bool],
    formula_limits: FormulaLimits,
) -> Result<[u8; 32], TableNumberFormatHwpxError> {
    if formulas.len() != grouping.len() {
        return Err(TableNumberFormatHwpxError::UnsupportedNativeProfile);
    }
    let mut digest = Sha256::new();
    digest.update(TABLE_NUMBER_FORMAT_HWPX_PROFILE_ID.as_bytes());
    digest.update((formulas.len() as u64).to_be_bytes());
    for (formula, use_grouping) in formulas.iter().zip(grouping) {
        let bytes = formula.canonical_json(formula_limits)?;
        digest.update((bytes.len() as u64).to_be_bytes());
        digest.update(bytes);
        digest.update([u8::from(*use_grouping)]);
    }
    Ok(digest.finalize().into())
}

fn grid_digest(grid: &TableGridCells) -> [u8; 32] {
    let mut coordinates = grid
        .cells
        .iter()
        .map(|(_, coordinate)| *coordinate)
        .collect::<Vec<_>>();
    coordinates.sort_unstable();
    let mut digest = Sha256::new();
    digest.update(TABLE_NUMBER_FORMAT_HWPX_PROFILE_ID.as_bytes());
    digest.update(grid.rows.to_be_bytes());
    digest.update(grid.columns.to_be_bytes());
    digest.update((coordinates.len() as u64).to_be_bytes());
    for coordinate in coordinates {
        digest.update(coordinate.row.to_be_bytes());
        digest.update(coordinate.column.to_be_bytes());
    }
    digest.finalize().into()
}

fn validate_digest(value: &str) -> Result<(), TableNumberFormatHwpxError> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(TableNumberFormatHwpxError::InvalidDigest);
    }
    Ok(())
}

fn parse_digest(value: &str) -> Result<[u8; 32], TableNumberFormatHwpxError> {
    validate_digest(value)?;
    let mut result = [0_u8; 32];
    for (index, pair) in value.as_bytes().chunks_exact(2).enumerate() {
        let text =
            std::str::from_utf8(pair).map_err(|_| TableNumberFormatHwpxError::InvalidDigest)?;
        result[index] =
            u8::from_str_radix(text, 16).map_err(|_| TableNumberFormatHwpxError::InvalidDigest)?;
    }
    Ok(result)
}

fn hex(bytes: impl AsRef<[u8]>) -> String {
    use std::fmt::Write as _;

    bytes
        .as_ref()
        .iter()
        .fold(String::new(), |mut output, byte| {
            let _ = write!(output, "{byte:02x}");
            output
        })
}
