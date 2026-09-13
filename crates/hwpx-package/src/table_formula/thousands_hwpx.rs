use std::collections::{BTreeMap, BTreeSet};
use std::fmt;

use domain_ir::{TableThousandsError, TableThousandsMode, TableThousandsPlan};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use super::*;

pub const TABLE_THOUSANDS_HWPX_SCHEMA_VERSION: &str = "hwpx-agent.table-thousands-hwpx/v1";
pub const TABLE_THOUSANDS_HWPX_PROFILE_ID: &str = "hwpx-agent.table-thousands-hwpx.hancom-2020/1";

#[derive(Clone, Eq, PartialEq)]
pub struct TableThousandsHwpxReadback {
    profile_id: &'static str,
    rows: u32,
    columns: u32,
    selected_formulas: Vec<FormulaCell>,
    formula_field_count: usize,
    section_sha256: [u8; 32],
    selected_state_sha256: [u8; 32],
    grid_sha256: [u8; 32],
    unowned_sha256: [u8; 32],
}

impl TableThousandsHwpxReadback {
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

impl fmt::Debug for TableThousandsHwpxReadback {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableThousandsHwpxReadback")
            .field("profile_id", &self.profile_id)
            .field("rows", &self.rows)
            .field("columns", &self.columns)
            .field("selected_formula_count", &self.selected_formulas.len())
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
pub struct TableThousandsHwpxRequestDraft {
    pub schema_version: String,
    pub table_ordinal: usize,
    pub expected_section_sha256: String,
    pub expected_source_state_sha256: String,
    pub expected_source_grid_sha256: String,
    pub expected_document_flow_sha256: String,
    pub expected_plan_sha256: String,
}

impl fmt::Debug for TableThousandsHwpxRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableThousandsHwpxRequestDraft")
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
pub struct TableThousandsHwpxRequest {
    schema_version: &'static str,
    table_ordinal: usize,
    expected_section_sha256: String,
    expected_source_state_sha256: String,
    expected_source_grid_sha256: String,
    expected_document_flow_sha256: String,
    expected_plan_sha256: String,
}

impl TableThousandsHwpxRequest {
    /// Binds one already validated thousands plan to the exact section, grid, selected formula
    /// state and document flow observed at request time.
    ///
    /// # Errors
    ///
    /// Rejects schema/digest drift, an unsupported native profile, a plan that changes anything
    /// except grouping, or any mismatch between the supplied bindings and current source.
    pub fn from_draft(
        draft: TableThousandsHwpxRequestDraft,
        section: &[u8],
        plan: &TableThousandsPlan,
        current_document_flow_sha256: &str,
        limits: TableFormulaHwpxLimits,
        formula_limits: FormulaLimits,
    ) -> Result<Self, TableThousandsHwpxError> {
        if draft.schema_version != TABLE_THOUSANDS_HWPX_SCHEMA_VERSION {
            return Err(TableThousandsHwpxError::UnsupportedVersion);
        }
        if draft.table_ordinal >= limits.config().tables {
            return Err(TableThousandsHwpxError::TableOrdinalLimit);
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
        validate_plan_against_source(plan, &shape.readback)?;
        let plan_sha256 = plan.canonical_sha256(formula_limits)?;
        if draft.expected_section_sha256 != hex(shape.readback.section_sha256)
            || draft.expected_source_state_sha256 != hex(shape.readback.selected_state_sha256)
            || draft.expected_source_grid_sha256 != hex(shape.readback.grid_sha256)
            || draft.expected_document_flow_sha256 != current_document_flow_sha256
            || draft.expected_plan_sha256 != hex(plan_sha256)
        {
            return Err(TableThousandsHwpxError::RequestBindingMismatch);
        }
        let request = Self {
            schema_version: TABLE_THOUSANDS_HWPX_SCHEMA_VERSION,
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

    /// Parses bounded strict JSON and applies the same exact request-time bindings as
    /// [`Self::from_draft`].
    ///
    /// # Errors
    ///
    /// Rejects invalid or oversized JSON and every semantic error from [`Self::from_draft`].
    pub fn from_json(
        bytes: &[u8],
        section: &[u8],
        plan: &TableThousandsPlan,
        current_document_flow_sha256: &str,
        limits: TableFormulaHwpxLimits,
        formula_limits: FormulaLimits,
    ) -> Result<Self, TableThousandsHwpxError> {
        if bytes.is_empty() || bytes.len() > limits.config().text_bytes {
            return Err(TableThousandsHwpxError::InputLimit);
        }
        let draft =
            serde_json::from_slice(bytes).map_err(|_| TableThousandsHwpxError::InvalidJson)?;
        Self::from_draft(
            draft,
            section,
            plan,
            current_document_flow_sha256,
            limits,
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
    /// Returns an error if serialization fails or exceeds the configured text bound.
    pub fn canonical_json(
        &self,
        limits: TableFormulaHwpxLimits,
    ) -> Result<Vec<u8>, TableThousandsHwpxError> {
        let bytes = serde_json::to_vec(self).map_err(|_| TableThousandsHwpxError::Serialization)?;
        if bytes.len() > limits.config().text_bytes {
            return Err(TableThousandsHwpxError::OutputLimit);
        }
        Ok(bytes)
    }
}

impl fmt::Debug for TableThousandsHwpxRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableThousandsHwpxRequest")
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
pub struct TableThousandsHwpxLoweringReceipt {
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

impl TableThousandsHwpxLoweringReceipt {
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

impl fmt::Debug for TableThousandsHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableThousandsHwpxLoweringReceipt")
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
pub struct TableThousandsHwpxReader;

impl TableThousandsHwpxReader {
    /// Reads selected native thousands-action formula fields from one section table.
    ///
    /// # Errors
    ///
    /// Rejects merged/ambiguous grids, missing selected fields, native metadata drift, ambiguous
    /// values that cannot display a separator, malformed grouping, and all finite-limit failures.
    pub fn read_selected_in_section(
        section: &[u8],
        table_ordinal: usize,
        selected_cells: &[CellCoordinate],
        limits: TableFormulaHwpxLimits,
        formula_limits: FormulaLimits,
    ) -> Result<TableThousandsHwpxReadback, TableThousandsHwpxError> {
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
pub struct TableThousandsHwpxLowerer;

impl TableThousandsHwpxLowerer {
    /// Applies one exact plan by changing only selected formula visible-result text.
    ///
    /// The native `Command`, `Formula`, `ResultFormat`, `LastResult`, every unselected formula,
    /// complete table payload/properties and all bytes outside selected visible results are exact.
    ///
    /// # Errors
    ///
    /// Rechecks section/state/grid/flow/plan bindings at build time, rejects unsupported native
    /// shapes and returns no bytes after any preservation or semantic readback mismatch.
    pub fn lower_in_section_with_receipt(
        request: &TableThousandsHwpxRequest,
        section: &[u8],
        plan: &TableThousandsPlan,
        current_document_flow_sha256: &str,
        limits: TableFormulaHwpxLimits,
        formula_limits: FormulaLimits,
    ) -> Result<(Vec<u8>, TableThousandsHwpxLoweringReceipt), TableThousandsHwpxError> {
        validate_digest(current_document_flow_sha256)?;
        if request.expected_document_flow_sha256 != current_document_flow_sha256 {
            return Err(TableThousandsHwpxError::FlowBindingMismatch);
        }
        let source_shape = read_selected_shape(
            section,
            request.table_ordinal,
            plan.request().selected_cells(),
            limits,
            formula_limits,
        )?;
        validate_plan_against_source(plan, &source_shape.readback)?;
        let plan_sha256 = plan.canonical_sha256(formula_limits)?;
        if request.expected_section_sha256 != hex(source_shape.readback.section_sha256) {
            return Err(TableThousandsHwpxError::SectionBindingMismatch);
        }
        if request.expected_source_state_sha256 != hex(source_shape.readback.selected_state_sha256)
        {
            return Err(TableThousandsHwpxError::StateBindingMismatch);
        }
        if request.expected_source_grid_sha256 != hex(source_shape.readback.grid_sha256) {
            return Err(TableThousandsHwpxError::GridBindingMismatch);
        }
        if request.expected_plan_sha256 != hex(plan_sha256) {
            return Err(TableThousandsHwpxError::PlanBindingMismatch);
        }

        let mut edits = Vec::new();
        edits
            .try_reserve_exact(source_shape.selected.len())
            .map_err(|_| TableThousandsHwpxError::AllocationFailed)?;
        for (source, target) in source_shape.selected.iter().zip(plan.formatted_cells()) {
            let FormulaNumberFormat::Number { use_grouping, .. } = target.number_format() else {
                return Err(TableThousandsHwpxError::PlanMismatch);
            };
            let desired = if use_grouping {
                &source.grouped_result
            } else {
                &source.plain_result
            };
            if source.visible_result != *desired {
                edits.push(ByteEdit::new(
                    source.visible_result_span,
                    desired.as_bytes().to_vec(),
                ));
            }
        }
        let modified_text_count = edits.len();
        let output = apply_edits(section, &mut edits, limits)?;
        let output_shape = read_selected_shape(
            &output,
            request.table_ordinal,
            plan.request().selected_cells(),
            limits,
            formula_limits,
        )?;
        if output_shape.readback.selected_formulas != plan.formatted_cells()
            || output_shape.readback.grid_sha256 != source_shape.readback.grid_sha256
            || output_shape.readback.formula_field_count
                != source_shape.readback.formula_field_count
        {
            return Err(TableThousandsHwpxError::ReadbackMismatch);
        }
        if output_shape.readback.unowned_sha256 != source_shape.readback.unowned_sha256 {
            return Err(TableThousandsHwpxError::PreservationMismatch);
        }
        let flow = parse_digest(current_document_flow_sha256)?;
        let receipt = TableThousandsHwpxLoweringReceipt {
            profile_id: TABLE_THOUSANDS_HWPX_PROFILE_ID,
            capability_id: plan.capability_id(),
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
pub enum TableThousandsHwpxError {
    #[error("table thousands HWPX input is empty or oversized")]
    InputLimit,
    #[error("table thousands HWPX JSON is invalid")]
    InvalidJson,
    #[error("table thousands HWPX schema version is unsupported")]
    UnsupportedVersion,
    #[error("table thousands HWPX table ordinal exceeds its limit")]
    TableOrdinalLimit,
    #[error("table thousands HWPX digest is invalid")]
    InvalidDigest,
    #[error("table thousands HWPX request binding does not match current source")]
    RequestBindingMismatch,
    #[error("table thousands HWPX section binding does not match")]
    SectionBindingMismatch,
    #[error("table thousands HWPX selected-state binding does not match")]
    StateBindingMismatch,
    #[error("table thousands HWPX grid binding does not match")]
    GridBindingMismatch,
    #[error("table thousands HWPX document-flow binding does not match")]
    FlowBindingMismatch,
    #[error("table thousands HWPX plan binding does not match")]
    PlanBindingMismatch,
    #[error("table thousands HWPX plan changes unsupported state")]
    PlanMismatch,
    #[error("table thousands HWPX native formula profile is unsupported")]
    UnsupportedNativeProfile,
    #[error("table thousands HWPX semantic readback does not match")]
    ReadbackMismatch,
    #[error("table thousands HWPX unowned bytes changed")]
    PreservationMismatch,
    #[error("table thousands HWPX output exceeds its limit")]
    OutputLimit,
    #[error("table thousands HWPX serialization failed")]
    Serialization,
    #[error("table thousands HWPX allocation failed")]
    AllocationFailed,
    #[error("table thousands HWPX core plan failed: {0}")]
    Plan(#[from] TableThousandsError),
    #[error("table thousands HWPX formula state failed: {0}")]
    Formula(#[from] FormulaError),
    #[error("table thousands HWPX formula section failed: {0}")]
    FormulaHwpx(#[from] TableFormulaHwpxError),
}

impl TableThousandsHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InputLimit => "table_thousands_hwpx_input_limit",
            Self::InvalidJson => "table_thousands_hwpx_invalid_json",
            Self::UnsupportedVersion => "table_thousands_hwpx_unsupported_version",
            Self::TableOrdinalLimit => "table_thousands_hwpx_table_ordinal_limit",
            Self::InvalidDigest => "table_thousands_hwpx_invalid_digest",
            Self::RequestBindingMismatch => "table_thousands_hwpx_request_binding_mismatch",
            Self::SectionBindingMismatch => "table_thousands_hwpx_section_binding_mismatch",
            Self::StateBindingMismatch => "table_thousands_hwpx_state_binding_mismatch",
            Self::GridBindingMismatch => "table_thousands_hwpx_grid_binding_mismatch",
            Self::FlowBindingMismatch => "table_thousands_hwpx_flow_binding_mismatch",
            Self::PlanBindingMismatch => "table_thousands_hwpx_plan_binding_mismatch",
            Self::PlanMismatch => "table_thousands_hwpx_plan_mismatch",
            Self::UnsupportedNativeProfile => "table_thousands_hwpx_unsupported_native_profile",
            Self::ReadbackMismatch => "table_thousands_hwpx_readback_mismatch",
            Self::PreservationMismatch => "table_thousands_hwpx_preservation_mismatch",
            Self::OutputLimit => "table_thousands_hwpx_output_limit",
            Self::Serialization => "table_thousands_hwpx_serialization",
            Self::AllocationFailed => "table_thousands_hwpx_allocation_failed",
            Self::Plan(_) => "table_thousands_hwpx_core_plan",
            Self::Formula(_) => "table_thousands_hwpx_formula_state",
            Self::FormulaHwpx(_) => "table_thousands_hwpx_formula_section",
        }
    }
}

struct SelectedShape {
    readback: TableThousandsHwpxReadback,
    selected: Vec<SelectedNativeFormula>,
}

struct SelectedNativeFormula {
    visible_result_span: XmlByteSpan,
    visible_result: String,
    grouped_result: String,
    plain_result: String,
}

fn read_selected_shape(
    section: &[u8],
    table_ordinal: usize,
    selected_cells: &[CellCoordinate],
    limits: TableFormulaHwpxLimits,
    formula_limits: FormulaLimits,
) -> Result<SelectedShape, TableThousandsHwpxError> {
    if selected_cells.is_empty() || selected_cells.len() > limits.config().formula_fields {
        return Err(TableThousandsHwpxError::UnsupportedNativeProfile);
    }
    let selected_set = selected_cells.iter().copied().collect::<BTreeSet<_>>();
    if selected_set.len() != selected_cells.len() {
        return Err(TableThousandsHwpxError::UnsupportedNativeProfile);
    }
    let document = parse_document(section, limits)?;
    validate_document_envelope(&document)?;
    validate_section_root(&document)?;
    let table = table_indexes(&document, limits)?
        .get(table_ordinal)
        .copied()
        .ok_or(TableThousandsHwpxError::UnsupportedNativeProfile)?;
    let grid = read_cells(&document, table, limits, false)?;
    let dimensions = FormulaGridDimensions {
        rows: grid.rows,
        columns: grid.columns,
    };
    if selected_cells
        .iter()
        .any(|coordinate| coordinate.row >= grid.rows || coordinate.column >= grid.columns)
    {
        return Err(TableThousandsHwpxError::UnsupportedNativeProfile);
    }
    let fields = formula_fields(&document, table, limits)?;
    let mut by_owner = BTreeMap::new();
    for field_begin in &fields {
        let cell = owning_direct_cell(&document, *field_begin, table)?;
        let owner = grid
            .cells
            .iter()
            .find_map(|(index, coordinate)| (*index == cell).then_some(*coordinate))
            .ok_or(TableThousandsHwpxError::UnsupportedNativeProfile)?;
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
            return Err(TableThousandsHwpxError::UnsupportedNativeProfile);
        }
    }
    if by_owner.len() != selected_cells.len() {
        return Err(TableThousandsHwpxError::UnsupportedNativeProfile);
    }
    let mut selected = Vec::new();
    let mut formulas = Vec::new();
    selected
        .try_reserve_exact(selected_cells.len())
        .map_err(|_| TableThousandsHwpxError::AllocationFailed)?;
    formulas
        .try_reserve_exact(selected_cells.len())
        .map_err(|_| TableThousandsHwpxError::AllocationFailed)?;
    for coordinate in selected_set {
        let value = by_owner
            .remove(&coordinate)
            .ok_or(TableThousandsHwpxError::UnsupportedNativeProfile)?;
        formulas.push(value.formula);
        selected.push(value.native);
    }
    let spans = selected
        .iter()
        .map(|value| value.visible_result_span)
        .collect::<Vec<_>>();
    let selected_state_sha256 = selected_state_digest(&formulas, formula_limits)?;
    let grid_sha256 = grid_digest(&grid);
    let unowned_sha256 = digest_excluding(section, &spans, TABLE_THOUSANDS_HWPX_PROFILE_ID)?;
    Ok(SelectedShape {
        readback: TableThousandsHwpxReadback {
            profile_id: TABLE_THOUSANDS_HWPX_PROFILE_ID,
            rows: grid.rows,
            columns: grid.columns,
            selected_formulas: formulas,
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

fn read_selected_native_formula(
    document: &PreservingXmlDocument,
    field_begin: usize,
    owner: CellCoordinate,
    dimensions: FormulaGridDimensions,
    limits: TableFormulaHwpxLimits,
    formula_limits: FormulaLimits,
) -> Result<ParsedSelectedFormula, TableThousandsHwpxError> {
    let envelope = validate_field_envelope(document, field_begin, limits)?;
    let parameters = read_field_parameters(document, envelope.parameters, limits)?;
    if parameters.native_formula.text != NATIVE_LEFT_FORMULA
        || parameters.result_format.text != NATIVE_GENERAL_FORMAT
        || parameters.command.text
            != format!(
                "{}??{NATIVE_GENERAL_FORMAT};;{}",
                parameters.native_formula.text, parameters.last_result.text
            )
    {
        return Err(TableThousandsHwpxError::UnsupportedNativeProfile);
    }
    let visible = leaf_text_with_span(document, envelope.visible_result, limits)?;
    let (value, grouped_result, plain_result) =
        parse_grouped_result(parameters.last_result.text, formula_limits)?;
    let use_grouping = if visible.text == grouped_result {
        true
    } else if visible.text == plain_result {
        false
    } else {
        return Err(TableThousandsHwpxError::UnsupportedNativeProfile);
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
            number_format: FormulaNumberFormat::Number {
                decimal_places: value.scale(),
                use_grouping,
            },
        },
        dimensions,
        formula_limits,
    )?;
    Ok(ParsedSelectedFormula {
        formula,
        native: SelectedNativeFormula {
            visible_result_span: visible.span,
            visible_result: visible.text.to_owned(),
            grouped_result,
            plain_result,
        },
    })
}

fn parse_grouped_result(
    source: &str,
    formula_limits: FormulaLimits,
) -> Result<(FormulaDecimal, String, String), TableThousandsHwpxError> {
    if source.is_empty()
        || source.len() > formula_limits.config().cache_text_bytes
        || !source.is_ascii()
    {
        return Err(TableThousandsHwpxError::UnsupportedNativeProfile);
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
        Some(_) => return Err(TableThousandsHwpxError::UnsupportedNativeProfile),
        None => (unsigned, None),
    };
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
        return Err(TableThousandsHwpxError::UnsupportedNativeProfile);
    }
    let mut plain = String::new();
    plain
        .try_reserve(source.len())
        .map_err(|_| TableThousandsHwpxError::AllocationFailed)?;
    plain.push_str(sign);
    for group in groups {
        plain.push_str(group);
    }
    if let Some(fraction) = fraction {
        plain.push('.');
        plain.push_str(fraction);
    }
    let value = parse_canonical_decimal(&plain, formula_limits)?;
    Ok((value, source.to_owned(), plain))
}

fn validate_plan_against_source(
    plan: &TableThousandsPlan,
    source: &TableThousandsHwpxReadback,
) -> Result<(), TableThousandsHwpxError> {
    if plan.request().dimensions() != source.dimensions()
        || plan.request().selected_cells().len() != source.selected_formulas.len()
        || plan.formatted_cells().len() != source.selected_formulas.len()
        || plan.capability_id() != plan.request().capability_id()
        || plan
            .request()
            .selected_cells()
            .iter()
            .copied()
            .ne(source.selected_formulas.iter().map(FormulaCell::owner))
    {
        return Err(TableThousandsHwpxError::PlanMismatch);
    }
    let expected_grouping = plan.request().mode() == TableThousandsMode::Add;
    for (before, after) in source.selected_formulas.iter().zip(plan.formatted_cells()) {
        let FormulaNumberFormat::Number {
            decimal_places: before_places,
            ..
        } = before.number_format()
        else {
            return Err(TableThousandsHwpxError::PlanMismatch);
        };
        let FormulaNumberFormat::Number {
            decimal_places: after_places,
            use_grouping,
        } = after.number_format()
        else {
            return Err(TableThousandsHwpxError::PlanMismatch);
        };
        if before.owner() != after.owner()
            || before.ast() != after.ast()
            || before.cache() != after.cache()
            || before_places != after_places
            || use_grouping != expected_grouping
        {
            return Err(TableThousandsHwpxError::PlanMismatch);
        }
    }
    Ok(())
}

fn selected_state_digest(
    formulas: &[FormulaCell],
    formula_limits: FormulaLimits,
) -> Result<[u8; 32], TableThousandsHwpxError> {
    let mut digest = Sha256::new();
    digest.update(TABLE_THOUSANDS_HWPX_PROFILE_ID.as_bytes());
    digest.update((formulas.len() as u64).to_be_bytes());
    for formula in formulas {
        let bytes = formula.canonical_json(formula_limits)?;
        digest.update((bytes.len() as u64).to_be_bytes());
        digest.update(bytes);
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
    digest.update(TABLE_THOUSANDS_HWPX_PROFILE_ID.as_bytes());
    digest.update(grid.rows.to_be_bytes());
    digest.update(grid.columns.to_be_bytes());
    digest.update((coordinates.len() as u64).to_be_bytes());
    for coordinate in coordinates {
        digest.update(coordinate.row.to_be_bytes());
        digest.update(coordinate.column.to_be_bytes());
    }
    digest.finalize().into()
}

fn validate_digest(value: &str) -> Result<(), TableThousandsHwpxError> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(TableThousandsHwpxError::InvalidDigest);
    }
    Ok(())
}

fn parse_digest(value: &str) -> Result<[u8; 32], TableThousandsHwpxError> {
    validate_digest(value)?;
    let mut result = [0_u8; 32];
    for (index, pair) in value.as_bytes().chunks_exact(2).enumerate() {
        let text = std::str::from_utf8(pair).map_err(|_| TableThousandsHwpxError::InvalidDigest)?;
        result[index] =
            u8::from_str_radix(text, 16).map_err(|_| TableThousandsHwpxError::InvalidDigest)?;
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
