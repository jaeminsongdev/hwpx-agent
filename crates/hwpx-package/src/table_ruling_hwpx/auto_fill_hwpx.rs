use std::collections::{BTreeMap, BTreeSet};
use std::fmt;

use domain_ir::{
    CaptionSide, CellCoordinate, FormulaCache, FormulaError, FormulaExpression, FormulaValue,
    LogicalId, TABLE_AUTO_FILL_SCHEMA_VERSION, TABLE_RULING_SCHEMA_VERSION, TableAutoFillBuilder,
    TableAutoFillError, TableAutoFillFormulaPolicy, TableAutoFillLimits, TableAutoFillMutation,
    TableAutoFillOrder, TableAutoFillPlan, TableAutoFillRegion, TableAutoFillRequest,
    TableAutoFillRequestDraft, TableAutoFillSeries, TableAutoFillValue, TableGrid, TableGridError,
    TablePageSplitPolicy, TableRulingCellDraft, TableRulingError, TableRulingPayloadBlock,
    TableRulingState, TableRulingStateDraft,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use super::create_hwpx;
use super::text_conversion_hwpx::{
    TableTextToTableHwpxError, canonical_text_paragraph, standalone_paragraph,
};
use super::{
    RawEdit, TableRulingHwpxBinding, TableRulingHwpxError, TableRulingHwpxLimits,
    TableRulingHwpxReadback, TableRulingHwpxReader,
};
use crate::preserving_xml::{PreservingXmlDocument, PreservingXmlError};
use crate::{
    ParagraphChild, TablePaginationHwpxError, TablePaginationHwpxLimits,
    TablePaginationHwpxReadback, TablePaginationHwpxReader, TextAtom, TextFlowError,
    TextFlowLimits, TextFlowReader, TextRunItem,
};

pub const TABLE_AUTO_FILL_HWPX_SCHEMA_VERSION: &str = "hwpx-agent.table-auto-fill-hwpx/v1";
pub const TABLE_AUTO_FILL_HWPX_PROFILE_ID: &str =
    "hwpx-agent.table-auto-fill-hwpx.hancom-2020-single-run/1";

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TableAutoFillHwpxLimits {
    pub native: TableRulingHwpxLimits,
    pub pagination: TablePaginationHwpxLimits,
    pub flow: TextFlowLimits,
    pub auto_fill: TableAutoFillLimits,
}

#[derive(Clone, Eq, PartialEq)]
struct ScalarCell {
    coordinate: CellCoordinate,
    visible_text: String,
    style_sha256: [u8; 32],
    paragraph_bytes: Vec<u8>,
    run_content_start: usize,
    run_content_end: usize,
    section_run_content_start: usize,
    section_run_content_end: usize,
}

impl fmt::Debug for ScalarCell {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ScalarCell")
            .field("coordinate", &self.coordinate)
            .field("visible_text", &"<redacted>")
            .field("style_sha256", &"<redacted>")
            .field("paragraph_bytes", &self.paragraph_bytes.len())
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableAutoFillHwpxReadback {
    pub profile_id: &'static str,
    pub table_ordinal: usize,
    pub region: TableAutoFillRegion,
    pub header_sha256: [u8; 32],
    pub section_sha256: [u8; 32],
    pub source_table_count: usize,
    pub ruling: TableRulingHwpxReadback,
    pub pagination: TablePaginationHwpxReadback,
    pub scalar_state_sha256: [u8; 32],
    pub pagination_policy_sha256: [u8; 32],
    cells: Vec<ScalarCell>,
}

impl fmt::Debug for TableAutoFillHwpxReadback {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableAutoFillHwpxReadback")
            .field("profile_id", &self.profile_id)
            .field("table_ordinal", &self.table_ordinal)
            .field("region", &self.region)
            .field("source_table_count", &self.source_table_count)
            .field("selected_cell_count", &self.cells.len())
            .field("formula_count", &self.ruling.formula_count)
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct TableAutoFillHwpxReader;

impl TableAutoFillHwpxReader {
    /// Lifts one exact merge-free region whose cells each contain one supported paragraph/run.
    ///
    /// # Errors
    ///
    /// Rejects malformed, merged, multi-paragraph, multi-run, inline-styled, opaque, ambiguous,
    /// formula-cache, pagination, identity, or finite-limit input.
    pub fn read_context(
        header: &[u8],
        section: &[u8],
        table_ordinal: usize,
        region: TableAutoFillRegion,
        binding: &TableRulingHwpxBinding,
        limits: TableAutoFillHwpxLimits,
    ) -> Result<TableAutoFillHwpxReadback, TableAutoFillHwpxError> {
        let ruling = TableRulingHwpxReader::read_existing_preserving_caption(
            header,
            section,
            table_ordinal,
            binding,
            &limits.native,
        )?;
        validate_region(region, &ruling.grid, limits.auto_fill)?;
        let pagination =
            TablePaginationHwpxReader::read_in_section(section, table_ordinal, limits.pagination)?;
        let cells = read_scalar_cells(section, table_ordinal, region, &ruling, &limits)?;
        let scalar_state_sha256 = scalar_state_sha256(&cells, &ruling.state, &limits)?;
        let source_table_count =
            TablePaginationHwpxReader::count_in_section(section, limits.pagination)?;
        Ok(TableAutoFillHwpxReadback {
            profile_id: TABLE_AUTO_FILL_HWPX_PROFILE_ID,
            table_ordinal,
            region,
            header_sha256: Sha256::digest(header).into(),
            section_sha256: Sha256::digest(section).into(),
            source_table_count,
            scalar_state_sha256,
            pagination_policy_sha256: pagination_policy_sha256(&pagination),
            ruling,
            pagination,
            cells,
        })
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableAutoFillHwpxRequestDraft {
    pub schema_version: String,
    pub table_ordinal: usize,
    pub region: TableAutoFillRegion,
    pub order: TableAutoFillOrder,
    pub start_index: u64,
    pub formula_policy: TableAutoFillFormulaPolicy,
    pub expected_header_sha256: String,
    pub expected_section_sha256: String,
    pub expected_table_content_sha256: String,
    pub expected_source_state_sha256: String,
    pub expected_source_grid_sha256: String,
    pub expected_scalar_state_sha256: String,
    pub expected_pagination_policy_sha256: String,
    pub expected_series_sha256: String,
    pub expected_source_table_count: usize,
    pub expected_document_flow_sha256: String,
    pub target_document_flow_sha256: String,
    pub target_payload_block_ids: Vec<Option<LogicalId>>,
}

impl fmt::Debug for TableAutoFillHwpxRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableAutoFillHwpxRequestDraft")
            .field("schema_version", &self.schema_version)
            .field("table_ordinal", &self.table_ordinal)
            .field("region", &self.region)
            .field("order", &self.order)
            .field("start_index", &"<redacted>")
            .field("formula_policy", &self.formula_policy)
            .field("target_payload_slots", &self.target_payload_block_ids.len())
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableAutoFillHwpxRequest {
    schema_version: &'static str,
    capability_id: &'static str,
    table_ordinal: usize,
    expected_header_sha256: String,
    expected_section_sha256: String,
    expected_table_content_sha256: String,
    expected_source_state_sha256: String,
    expected_source_grid_sha256: String,
    expected_scalar_state_sha256: String,
    expected_pagination_policy_sha256: String,
    expected_series_sha256: String,
    expected_source_table_count: usize,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    target_payload_block_ids: Vec<Option<LogicalId>>,
    semantic: TableAutoFillRequest,
}

impl TableAutoFillHwpxRequest {
    /// Binds source-derived scalar semantics and exact target payload identities to document flow.
    ///
    /// # Errors
    ///
    /// Rejects schema, source, series, state, grid, scalar, payload, pagination, flow, or bound
    /// drift.
    pub fn from_draft(
        draft: TableAutoFillHwpxRequestDraft,
        series: &TableAutoFillSeries,
        source: &TableAutoFillHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableAutoFillHwpxLimits,
    ) -> Result<Self, TableAutoFillHwpxError> {
        if draft.schema_version != TABLE_AUTO_FILL_HWPX_SCHEMA_VERSION {
            return Err(TableAutoFillHwpxError::UnsupportedVersion);
        }
        require_request_digests(&draft, current_document_flow_sha256)?;
        let series_sha256 = create_hwpx::hex(series.canonical_sha256(limits.auto_fill)?);
        if draft.expected_series_sha256 != series_sha256 {
            return Err(TableAutoFillHwpxError::SourceBindingMismatch);
        }
        let semantic = semantic_request(
            source,
            series,
            draft.region,
            draft.order,
            draft.start_index,
            draft.formula_policy,
            &limits,
        )?;
        let request = Self {
            schema_version: TABLE_AUTO_FILL_HWPX_SCHEMA_VERSION,
            capability_id: semantic.capability_id(),
            table_ordinal: draft.table_ordinal,
            expected_header_sha256: draft.expected_header_sha256,
            expected_section_sha256: draft.expected_section_sha256,
            expected_table_content_sha256: draft.expected_table_content_sha256,
            expected_source_state_sha256: draft.expected_source_state_sha256,
            expected_source_grid_sha256: draft.expected_source_grid_sha256,
            expected_scalar_state_sha256: draft.expected_scalar_state_sha256,
            expected_pagination_policy_sha256: draft.expected_pagination_policy_sha256,
            expected_series_sha256: draft.expected_series_sha256,
            expected_source_table_count: draft.expected_source_table_count,
            expected_document_flow_sha256: draft.expected_document_flow_sha256,
            target_document_flow_sha256: draft.target_document_flow_sha256,
            target_payload_block_ids: draft.target_payload_block_ids,
            semantic,
        };
        validate_request_source(
            &request,
            series,
            source,
            current_document_flow_sha256,
            &limits,
        )?;
        let _ = TableAutoFillHwpxBuilder::build(
            &request,
            series,
            source,
            current_document_flow_sha256,
            limits,
        )?;
        let _ = request.canonical_json(limits)?;
        Ok(request)
    }

    /// Parses strict bounded JSON and repeats the complete source-derived admission.
    ///
    /// # Errors
    ///
    /// Rejects empty, oversized, malformed, duplicate, unknown, or semantically invalid input.
    pub fn from_json(
        bytes: &[u8],
        series: &TableAutoFillSeries,
        source: &TableAutoFillHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableAutoFillHwpxLimits,
    ) -> Result<Self, TableAutoFillHwpxError> {
        if bytes.is_empty() || bytes.len() > serialized_limit(&limits) {
            return Err(TableAutoFillHwpxError::InputLimit);
        }
        create_hwpx::reject_duplicate_json_keys(bytes)
            .map_err(|_| TableAutoFillHwpxError::InvalidJson)?;
        let draft =
            serde_json::from_slice(bytes).map_err(|_| TableAutoFillHwpxError::InvalidJson)?;
        Self::from_draft(draft, series, source, current_document_flow_sha256, limits)
    }

    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
    }

    #[must_use]
    pub const fn semantic(&self) -> &TableAutoFillRequest {
        &self.semantic
    }

    #[must_use]
    pub fn target_document_flow_sha256(&self) -> &str {
        &self.target_document_flow_sha256
    }

    /// Serializes every semantic and native identity binding under finite limits.
    ///
    /// # Errors
    ///
    /// Rejects serialization or output-limit failure.
    pub fn canonical_json(
        &self,
        limits: TableAutoFillHwpxLimits,
    ) -> Result<Vec<u8>, TableAutoFillHwpxError> {
        serialize_bounded(self, serialized_limit(&limits))
    }

    /// Hashes the bounded deterministic request.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failure.
    pub fn canonical_sha256(
        &self,
        limits: TableAutoFillHwpxLimits,
    ) -> Result<[u8; 32], TableAutoFillHwpxError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TableAutoFillHwpxRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableAutoFillHwpxRequest")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("table_ordinal", &self.table_ordinal)
            .field("region", &self.semantic.region())
            .field("order", &self.semantic.order())
            .field("start_index", &"<redacted>")
            .field("formula_policy", &self.semantic.formula_policy())
            .field("target_payload_slots", &self.target_payload_block_ids.len())
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableAutoFillHwpxPlan {
    schema_version: &'static str,
    capability_id: &'static str,
    request_sha256: String,
    source_state_sha256: String,
    target_state_sha256: String,
    grid_sha256: String,
    source_scalar_state_sha256: String,
    target_scalar_state_sha256: String,
    pagination_policy_sha256: String,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    source_table_count: usize,
    fill: TableAutoFillPlan,
    target_state: TableRulingState,
    #[serde(skip)]
    target_grid: TableGrid,
}

impl TableAutoFillHwpxPlan {
    #[must_use]
    pub const fn fill_plan(&self) -> &TableAutoFillPlan {
        &self.fill
    }

    #[must_use]
    pub const fn target_state(&self) -> &TableRulingState {
        &self.target_state
    }

    #[must_use]
    pub const fn target_grid(&self) -> &TableGrid {
        &self.target_grid
    }

    /// Serializes all HWPX lowering semantics and integrity bindings under finite limits.
    ///
    /// # Errors
    ///
    /// Rejects serialization or output-limit failure.
    pub fn canonical_json(
        &self,
        limits: TableAutoFillHwpxLimits,
    ) -> Result<Vec<u8>, TableAutoFillHwpxError> {
        serialize_bounded(self, serialized_limit(&limits))
    }

    /// Hashes the bounded deterministic plan.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failure.
    pub fn canonical_sha256(
        &self,
        limits: TableAutoFillHwpxLimits,
    ) -> Result<[u8; 32], TableAutoFillHwpxError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TableAutoFillHwpxPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableAutoFillHwpxPlan")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("source_table_count", &self.source_table_count)
            .field("rows", &self.target_grid.rows())
            .field("columns", &self.target_grid.columns())
            .field("mutation_count", &self.fill.mutations().len())
            .field(
                "semantic_change_count",
                &self.fill.receipt().semantic_change_count(),
            )
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct TableAutoFillHwpxBuilder;

impl TableAutoFillHwpxBuilder {
    /// Revalidates source-derived cells and builds exact target content and formula state.
    ///
    /// # Errors
    ///
    /// Rejects source, series, request, payload identity, state, grid, flow, or bound drift.
    pub fn build(
        request: &TableAutoFillHwpxRequest,
        series: &TableAutoFillSeries,
        source: &TableAutoFillHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableAutoFillHwpxLimits,
    ) -> Result<TableAutoFillHwpxPlan, TableAutoFillHwpxError> {
        validate_request_source(
            request,
            series,
            source,
            current_document_flow_sha256,
            &limits,
        )?;
        let fill = TableAutoFillBuilder::build(request.semantic.clone(), series, limits.auto_fill)?;
        let semantic_noop = fill.receipt().semantic_change_count() == 0;
        if semantic_noop
            != (request.expected_document_flow_sha256 == request.target_document_flow_sha256)
        {
            return Err(TableAutoFillHwpxError::FlowBindingMismatch);
        }
        let target_grid = source.ruling.grid.clone();
        let (target_state, target_cells) =
            target_state(request, source, &fill, &target_grid, &limits)?;
        let target_scalar_state_sha256 =
            scalar_state_sha256(&target_cells, &target_state, &limits)?;
        let plan = TableAutoFillHwpxPlan {
            schema_version: TABLE_AUTO_FILL_HWPX_SCHEMA_VERSION,
            capability_id: request.capability_id,
            request_sha256: create_hwpx::hex(request.canonical_sha256(limits)?),
            source_state_sha256: create_hwpx::hex(
                source.ruling.state.canonical_sha256(limits.native.ruling)?,
            ),
            target_state_sha256: create_hwpx::hex(
                target_state.canonical_sha256(limits.native.ruling)?,
            ),
            grid_sha256: create_hwpx::hex(target_grid.canonical_sha256()?),
            source_scalar_state_sha256: create_hwpx::hex(source.scalar_state_sha256),
            target_scalar_state_sha256: create_hwpx::hex(target_scalar_state_sha256),
            pagination_policy_sha256: create_hwpx::hex(source.pagination_policy_sha256),
            expected_document_flow_sha256: request.expected_document_flow_sha256.clone(),
            target_document_flow_sha256: request.target_document_flow_sha256.clone(),
            source_table_count: source.source_table_count,
            fill,
            target_state,
            target_grid,
        };
        let _ = plan.canonical_json(limits)?;
        Ok(plan)
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableAutoFillHwpxLoweringReceipt {
    pub profile_id: &'static str,
    pub source_header_sha256: [u8; 32],
    pub output_header_sha256: [u8; 32],
    pub source_section_sha256: [u8; 32],
    pub output_section_sha256: [u8; 32],
    pub source_state_sha256: [u8; 32],
    pub target_state_sha256: [u8; 32],
    pub grid_sha256: [u8; 32],
    pub source_scalar_state_sha256: [u8; 32],
    pub target_scalar_state_sha256: [u8; 32],
    pub pagination_policy_sha256: [u8; 32],
    pub series_sha256: [u8; 32],
    pub request_sha256: [u8; 32],
    pub plan_sha256: [u8; 32],
    pub before_document_flow_sha256: [u8; 32],
    pub after_document_flow_sha256: [u8; 32],
    pub source_table_count: usize,
    pub target_table_count: usize,
    pub rows: u32,
    pub columns: u32,
    pub selected_cell_count: usize,
    pub semantic_change_count: usize,
    pub source_formula_count: usize,
    pub target_formula_count: usize,
    pub payload_block_count: usize,
    pub page_split: TablePageSplitPolicy,
    pub repeat_header_rows: u32,
    pub caption_preserved: bool,
}

impl fmt::Debug for TableAutoFillHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableAutoFillHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field("source_table_count", &self.source_table_count)
            .field("target_table_count", &self.target_table_count)
            .field("rows", &self.rows)
            .field("columns", &self.columns)
            .field("selected_cell_count", &self.selected_cell_count)
            .field("semantic_change_count", &self.semantic_change_count)
            .field("source_formula_count", &self.source_formula_count)
            .field("target_formula_count", &self.target_formula_count)
            .field("payload_block_count", &self.payload_block_count)
            .field("page_split", &self.page_split)
            .field("repeat_header_rows", &self.repeat_header_rows)
            .field("caption_preserved", &self.caption_preserved)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableAutoFillHwpxLoweredParts {
    pub header: Vec<u8>,
    pub section: Vec<u8>,
    pub binding: TableRulingHwpxBinding,
    pub receipt: TableAutoFillHwpxLoweringReceipt,
}

impl fmt::Debug for TableAutoFillHwpxLoweredParts {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableAutoFillHwpxLoweredParts")
            .field("header_bytes", &self.header.len())
            .field("section_bytes", &self.section.len())
            .field("binding", &self.binding)
            .field("receipt", &self.receipt)
            .finish()
    }
}

#[derive(Debug)]
pub struct TableAutoFillHwpxLowerer;

impl TableAutoFillHwpxLowerer {
    /// Rewrites only selected run content and returns after exact semantic and pagination reopen.
    ///
    /// # Errors
    ///
    /// Rejects source, series, state, scalar, style, payload, plan, flow, pagination, or readback
    /// drift without returning partial parts.
    #[allow(clippy::too_many_arguments)]
    pub fn lower(
        header: &[u8],
        section: &[u8],
        binding: &TableRulingHwpxBinding,
        current_document_flow_sha256: &str,
        series: &TableAutoFillSeries,
        request: &TableAutoFillHwpxRequest,
        plan: &TableAutoFillHwpxPlan,
        limits: TableAutoFillHwpxLimits,
    ) -> Result<TableAutoFillHwpxLoweredParts, TableAutoFillHwpxError> {
        let source = TableAutoFillHwpxReader::read_context(
            header,
            section,
            request.table_ordinal,
            request.semantic.region(),
            binding,
            limits,
        )?;
        validate_request_source(
            request,
            series,
            &source,
            current_document_flow_sha256,
            &limits,
        )?;
        let rebuilt = TableAutoFillHwpxBuilder::build(
            request,
            series,
            &source,
            current_document_flow_sha256,
            limits,
        )?;
        if rebuilt != *plan {
            return Err(TableAutoFillHwpxError::PlanBindingMismatch);
        }
        let changed = plan.fill.receipt().semantic_change_count() != 0;
        let output_section = if changed {
            patch_selected_runs(section, &source, &plan.fill, &limits)?
        } else {
            section.to_vec()
        };
        if header.len() > limits.native.layout.config().output_bytes {
            return Err(TableAutoFillHwpxError::OutputLimit);
        }
        let output_header = header.to_vec();
        let target_binding = super::binding_from_state(&plan.target_state, &plan.target_grid)?;
        let reopened = TableAutoFillHwpxReader::read_context(
            &output_header,
            &output_section,
            request.table_ordinal,
            request.semantic.region(),
            &target_binding,
            limits,
        )?;
        if reopened.ruling.state != plan.target_state
            || reopened.ruling.grid != plan.target_grid
            || create_hwpx::hex(reopened.scalar_state_sha256) != plan.target_scalar_state_sha256
            || !same_pagination_policy(&source.pagination, &reopened.pagination)
            || reopened.source_table_count != source.source_table_count
        {
            return Err(TableAutoFillHwpxError::ReadbackMismatch);
        }
        let receipt = TableAutoFillHwpxLoweringReceipt {
            profile_id: TABLE_AUTO_FILL_HWPX_PROFILE_ID,
            source_header_sha256: source.header_sha256,
            output_header_sha256: Sha256::digest(&output_header).into(),
            source_section_sha256: source.section_sha256,
            output_section_sha256: Sha256::digest(&output_section).into(),
            source_state_sha256: source.ruling.state.canonical_sha256(limits.native.ruling)?,
            target_state_sha256: reopened
                .ruling
                .state
                .canonical_sha256(limits.native.ruling)?,
            grid_sha256: reopened.ruling.grid.canonical_sha256()?,
            source_scalar_state_sha256: source.scalar_state_sha256,
            target_scalar_state_sha256: reopened.scalar_state_sha256,
            pagination_policy_sha256: source.pagination_policy_sha256,
            series_sha256: series.canonical_sha256(limits.auto_fill)?,
            request_sha256: request.canonical_sha256(limits)?,
            plan_sha256: plan.canonical_sha256(limits)?,
            before_document_flow_sha256: parse_digest(&request.expected_document_flow_sha256)?,
            after_document_flow_sha256: parse_digest(&request.target_document_flow_sha256)?,
            source_table_count: source.source_table_count,
            target_table_count: reopened.source_table_count,
            rows: reopened.ruling.grid.rows(),
            columns: reopened.ruling.grid.columns(),
            selected_cell_count: plan.fill.mutations().len(),
            semantic_change_count: plan.fill.receipt().semantic_change_count(),
            source_formula_count: source.ruling.formula_count,
            target_formula_count: reopened.ruling.formula_count,
            payload_block_count: reopened.ruling.payload_block_count,
            page_split: reopened.pagination.page_split,
            repeat_header_rows: reopened.pagination.repeat_header_rows,
            caption_preserved: reopened.pagination.caption.is_some(),
        };
        Ok(TableAutoFillHwpxLoweredParts {
            header: output_header,
            section: output_section,
            binding: target_binding,
            receipt,
        })
    }
}

#[derive(Debug, Error)]
pub enum TableAutoFillHwpxError {
    #[error("unsupported table-auto-fill HWPX schema version")]
    UnsupportedVersion,
    #[error("table-auto-fill HWPX input exceeds a finite bound")]
    InputLimit,
    #[error("invalid table-auto-fill HWPX JSON")]
    InvalidJson,
    #[error("table-auto-fill HWPX source, state, scalar, series, or flow drifted")]
    SourceBindingMismatch,
    #[error("table-auto-fill HWPX document-flow transition drifted")]
    FlowBindingMismatch,
    #[error("table-auto-fill HWPX selected region must be merge-free")]
    UnsupportedMergedCells,
    #[error("table-auto-fill HWPX selected cell content is rich or ambiguous")]
    UnsupportedRichContent,
    #[error("table-auto-fill HWPX selected formula cache cannot be represented exactly")]
    UnsupportedFormulaCache,
    #[error("table-auto-fill HWPX would stale an unselected formula cache")]
    UnsupportedFormulaDependency,
    #[error("table-auto-fill HWPX target payload identities are missing or conflicting")]
    PayloadIdentityMismatch,
    #[error("table-auto-fill HWPX plan drifted")]
    PlanBindingMismatch,
    #[error("table-auto-fill HWPX semantic readback mismatched")]
    ReadbackMismatch,
    #[error("table-auto-fill HWPX allocation failed")]
    Allocation,
    #[error("table-auto-fill HWPX serialization failed")]
    Serialization,
    #[error("table-auto-fill HWPX output exceeds a finite bound")]
    OutputLimit,
    #[error(transparent)]
    Grid(#[from] TableGridError),
    #[error(transparent)]
    RulingModel(#[from] TableRulingError),
    #[error(transparent)]
    AutoFill(#[from] TableAutoFillError),
    #[error(transparent)]
    Formula(#[from] FormulaError),
    #[error(transparent)]
    Native(#[from] TableRulingHwpxError),
    #[error(transparent)]
    Pagination(#[from] TablePaginationHwpxError),
    #[error(transparent)]
    TextFlow(#[from] TextFlowError),
    #[error(transparent)]
    TextAdapter(#[from] TableTextToTableHwpxError),
    #[error(transparent)]
    Preserving(#[from] PreservingXmlError),
}

impl TableAutoFillHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::UnsupportedVersion => "table_auto_fill_hwpx_unsupported_version",
            Self::InputLimit => "table_auto_fill_hwpx_input_limit",
            Self::InvalidJson => "table_auto_fill_hwpx_invalid_json",
            Self::SourceBindingMismatch => "table_auto_fill_hwpx_source_binding_mismatch",
            Self::FlowBindingMismatch => "table_auto_fill_hwpx_flow_binding_mismatch",
            Self::UnsupportedMergedCells => "table_auto_fill_hwpx_unsupported_merged_cells",
            Self::UnsupportedRichContent => "table_auto_fill_hwpx_unsupported_rich_content",
            Self::UnsupportedFormulaCache => "table_auto_fill_hwpx_unsupported_formula_cache",
            Self::UnsupportedFormulaDependency => {
                "table_auto_fill_hwpx_unsupported_formula_dependency"
            }
            Self::PayloadIdentityMismatch => "table_auto_fill_hwpx_payload_identity_mismatch",
            Self::PlanBindingMismatch => "table_auto_fill_hwpx_plan_binding_mismatch",
            Self::ReadbackMismatch => "table_auto_fill_hwpx_readback_mismatch",
            Self::Allocation => "table_auto_fill_hwpx_allocation",
            Self::Serialization => "table_auto_fill_hwpx_serialization",
            Self::OutputLimit => "table_auto_fill_hwpx_output_limit",
            Self::Grid(_) => "table_auto_fill_hwpx_grid",
            Self::RulingModel(_) => "table_auto_fill_hwpx_ruling_model",
            Self::AutoFill(_) => "table_auto_fill_hwpx_domain",
            Self::Formula(_) => "table_auto_fill_hwpx_formula",
            Self::Native(_) => "table_auto_fill_hwpx_native",
            Self::Pagination(_) => "table_auto_fill_hwpx_pagination",
            Self::TextFlow(_) => "table_auto_fill_hwpx_text_flow",
            Self::TextAdapter(_) => "table_auto_fill_hwpx_text_adapter",
            Self::Preserving(_) => "table_auto_fill_hwpx_preserving_xml",
        }
    }
}

fn require_request_digests(
    draft: &TableAutoFillHwpxRequestDraft,
    current_document_flow_sha256: &str,
) -> Result<(), TableAutoFillHwpxError> {
    for digest in [
        &draft.expected_header_sha256,
        &draft.expected_section_sha256,
        &draft.expected_table_content_sha256,
        &draft.expected_source_state_sha256,
        &draft.expected_source_grid_sha256,
        &draft.expected_scalar_state_sha256,
        &draft.expected_pagination_policy_sha256,
        &draft.expected_series_sha256,
        &draft.expected_document_flow_sha256,
        &draft.target_document_flow_sha256,
        current_document_flow_sha256,
    ] {
        create_hwpx::require_digest(digest)
            .map_err(|_| TableAutoFillHwpxError::SourceBindingMismatch)?;
    }
    Ok(())
}

fn validate_request_source(
    request: &TableAutoFillHwpxRequest,
    series: &TableAutoFillSeries,
    source: &TableAutoFillHwpxReadback,
    current_document_flow_sha256: &str,
    limits: &TableAutoFillHwpxLimits,
) -> Result<(), TableAutoFillHwpxError> {
    create_hwpx::require_digest(current_document_flow_sha256)
        .map_err(|_| TableAutoFillHwpxError::SourceBindingMismatch)?;
    let rebuilt_semantic = semantic_request(
        source,
        series,
        request.semantic.region(),
        request.semantic.order(),
        request.semantic.start_index(),
        request.semantic.formula_policy(),
        limits,
    )?;
    if source.profile_id != TABLE_AUTO_FILL_HWPX_PROFILE_ID
        || source.ruling.profile_id != super::TABLE_RULING_HWPX_PROFILE_ID
        || request.table_ordinal != source.table_ordinal
        || request.semantic.region() != source.region
        || request.expected_header_sha256 != create_hwpx::hex(source.header_sha256)
        || request.expected_section_sha256 != create_hwpx::hex(source.section_sha256)
        || request.expected_table_content_sha256
            != create_hwpx::hex(source.ruling.table_content_sha256)
        || request.expected_source_state_sha256
            != create_hwpx::hex(source.ruling.state.canonical_sha256(limits.native.ruling)?)
        || request.expected_source_grid_sha256
            != create_hwpx::hex(source.ruling.grid.canonical_sha256()?)
        || request.expected_scalar_state_sha256 != create_hwpx::hex(source.scalar_state_sha256)
        || request.expected_pagination_policy_sha256
            != create_hwpx::hex(source.pagination_policy_sha256)
        || request.expected_series_sha256
            != create_hwpx::hex(series.canonical_sha256(limits.auto_fill)?)
        || request.expected_source_table_count != source.source_table_count
        || request.expected_document_flow_sha256 != current_document_flow_sha256
        || request.semantic != rebuilt_semantic
    {
        return Err(TableAutoFillHwpxError::SourceBindingMismatch);
    }
    validate_target_payload_ids(request, source, series)?;
    Ok(())
}

fn semantic_request(
    source: &TableAutoFillHwpxReadback,
    series: &TableAutoFillSeries,
    region: TableAutoFillRegion,
    order: TableAutoFillOrder,
    start_index: u64,
    formula_policy: TableAutoFillFormulaPolicy,
    limits: &TableAutoFillHwpxLimits,
) -> Result<TableAutoFillRequest, TableAutoFillHwpxError> {
    if region != source.region {
        return Err(TableAutoFillHwpxError::SourceBindingMismatch);
    }
    let mut cells = Vec::new();
    cells
        .try_reserve_exact(source.cells.len())
        .map_err(|_| TableAutoFillHwpxError::Allocation)?;
    for scalar in &source.cells {
        let span = source.ruling.grid.master_cell_at(scalar.coordinate)?;
        if span.row != scalar.coordinate.row
            || span.column != scalar.coordinate.column
            || span.row_span != 1
            || span.column_span != 1
        {
            return Err(TableAutoFillHwpxError::UnsupportedMergedCells);
        }
        let state_cell = source
            .ruling
            .state
            .cell(&span.master_cell_id)
            .ok_or(TableAutoFillHwpxError::SourceBindingMismatch)?;
        let generated =
            generated_value_for_coordinate(series, region, order, start_index, scalar.coordinate)?;
        let generated_text = value_text(&generated)?;
        let current_value = if scalar.visible_text == generated_text {
            generated
        } else if let Some(formula) = state_cell.formula() {
            formula_cache_value(formula.cache())?
        } else {
            classify_value(&scalar.visible_text)?
        };
        if let Some(formula) = state_cell.formula() {
            let formula_text = value_text(&formula_cache_value(formula.cache())?)?;
            if formula_text != scalar.visible_text {
                return Err(TableAutoFillHwpxError::UnsupportedFormulaCache);
            }
        }
        cells.push(domain_ir::TableAutoFillCellDraft {
            coordinate: scalar.coordinate,
            payload_sha256: aggregate_payload_digest(state_cell.payload())?,
            formula_sha256: state_cell
                .formula()
                .map(|formula| {
                    formula
                        .canonical_sha256(limits.native.formula)
                        .map(create_hwpx::hex)
                })
                .transpose()?,
            style_sha256: create_hwpx::hex(scalar.style_sha256),
            current_value,
        });
    }
    Ok(TableAutoFillRequest::from_draft(
        TableAutoFillRequestDraft {
            schema_version: TABLE_AUTO_FILL_SCHEMA_VERSION.to_owned(),
            table_id: source.ruling.state.table_id().clone(),
            region,
            order,
            series_id: series.series_id().clone(),
            series_sha256: create_hwpx::hex(series.canonical_sha256(limits.auto_fill)?),
            start_index,
            formula_policy,
            cells,
        },
        series,
        &source.ruling.grid,
        limits.auto_fill,
    )?)
}

fn validate_target_payload_ids(
    request: &TableAutoFillHwpxRequest,
    source: &TableAutoFillHwpxReadback,
    series: &TableAutoFillSeries,
) -> Result<(), TableAutoFillHwpxError> {
    if request.target_payload_block_ids.len() != source.cells.len() {
        return Err(TableAutoFillHwpxError::PayloadIdentityMismatch);
    }
    let mut existing = BTreeSet::new();
    if !existing.insert(source.ruling.state.table_id().clone()) {
        return Err(TableAutoFillHwpxError::PayloadIdentityMismatch);
    }
    for cell in source.ruling.state.cells() {
        if !existing.insert(cell.master_cell_id().clone()) {
            return Err(TableAutoFillHwpxError::PayloadIdentityMismatch);
        }
        for payload in cell.payload() {
            if !existing.insert(payload.block_id.clone()) {
                return Err(TableAutoFillHwpxError::PayloadIdentityMismatch);
            }
        }
    }
    let mut new_ids = BTreeSet::new();
    for (index, scalar) in source.cells.iter().enumerate() {
        let target = request
            .target_payload_block_ids
            .get(index)
            .ok_or(TableAutoFillHwpxError::PayloadIdentityMismatch)?;
        let span = source.ruling.grid.master_cell_at(scalar.coordinate)?;
        let state_cell = source
            .ruling
            .state
            .cell(&span.master_cell_id)
            .ok_or(TableAutoFillHwpxError::SourceBindingMismatch)?;
        let generated = generated_value_for_coordinate(
            series,
            request.semantic.region(),
            request.semantic.order(),
            request.semantic.start_index(),
            scalar.coordinate,
        )?;
        let nonempty = !value_text(&generated)?.is_empty();
        match (nonempty, state_cell.payload(), target) {
            (false, _, None) => {}
            (true, [payload], Some(id)) if *id == payload.block_id => {}
            (true, [], Some(id)) if !existing.contains(id) && new_ids.insert(id.clone()) => {}
            _ => return Err(TableAutoFillHwpxError::PayloadIdentityMismatch),
        }
    }
    Ok(())
}

fn target_state(
    request: &TableAutoFillHwpxRequest,
    source: &TableAutoFillHwpxReadback,
    fill: &TableAutoFillPlan,
    target_grid: &TableGrid,
    limits: &TableAutoFillHwpxLimits,
) -> Result<(TableRulingState, Vec<ScalarCell>), TableAutoFillHwpxError> {
    let mutations = fill
        .mutations()
        .iter()
        .map(|mutation| (mutation.coordinate(), mutation))
        .collect::<BTreeMap<_, _>>();
    if mutations.len() != fill.mutations().len() || mutations.len() != source.cells.len() {
        return Err(TableAutoFillHwpxError::PlanBindingMismatch);
    }
    let changed_coordinates = changed_coordinates(source, &mutations)?;
    validate_unselected_formula_dependencies(source, &mutations, &changed_coordinates)?;
    let target_ids = source
        .cells
        .iter()
        .zip(&request.target_payload_block_ids)
        .map(|(cell, id)| (cell.coordinate, id.clone()))
        .collect::<BTreeMap<_, _>>();
    if target_ids.len() != source.cells.len() {
        return Err(TableAutoFillHwpxError::PayloadIdentityMismatch);
    }
    let source_scalars = source
        .cells
        .iter()
        .map(|cell| (cell.coordinate, cell))
        .collect::<BTreeMap<_, _>>();
    let mut cells = Vec::new();
    cells
        .try_reserve_exact(source.ruling.state.cells().len())
        .map_err(|_| TableAutoFillHwpxError::Allocation)?;
    for source_cell in source.ruling.state.cells() {
        let coordinate = source_cell.coordinate();
        let (payload, formula) = if let Some(mutation) = mutations.get(&coordinate) {
            let scalar = source_scalars
                .get(&coordinate)
                .copied()
                .ok_or(TableAutoFillHwpxError::PlanBindingMismatch)?;
            validate_mutation_source(mutation, source_cell, scalar, limits)?;
            let text = value_text(mutation.generated_value())?;
            let changed = scalar.visible_text != text || mutation.clear_formula();
            if !changed {
                (
                    source_cell.payload().to_vec(),
                    source_cell.formula().map(super::formula_draft),
                )
            } else if text.is_empty() {
                (Vec::new(), None)
            } else {
                let id = target_ids
                    .get(&coordinate)
                    .and_then(Option::as_ref)
                    .ok_or(TableAutoFillHwpxError::PayloadIdentityMismatch)?;
                let paragraph = target_paragraph(scalar, &text, limits)?;
                (
                    vec![TableRulingPayloadBlock {
                        block_id: id.clone(),
                        payload_sha256: create_hwpx::hex(Sha256::digest(paragraph)),
                    }],
                    None,
                )
            }
        } else {
            (
                source_cell.payload().to_vec(),
                source_cell.formula().map(super::formula_draft),
            )
        };
        cells.push(TableRulingCellDraft {
            master_cell_id: source_cell.master_cell_id().clone(),
            coordinate,
            payload,
            properties: source_cell.properties().clone(),
            formula,
        });
    }
    let state = TableRulingState::from_draft(
        TableRulingStateDraft {
            schema_version: TABLE_RULING_SCHEMA_VERSION.to_owned(),
            table_id: source.ruling.state.table_id().clone(),
            frame: source.ruling.state.frame(),
            grid_sha256: source.ruling.state.grid_sha256().to_owned(),
            table_properties_sha256: source.ruling.state.table_properties_sha256().to_owned(),
            row_boundaries_hwpunit: source.ruling.state.row_boundaries_hwpunit().to_vec(),
            column_boundaries_hwpunit: source.ruling.state.column_boundaries_hwpunit().to_vec(),
            edges: source.ruling.state.edges().to_vec(),
            cells,
        },
        target_grid,
        limits.native.formula,
        limits.native.ruling,
    )?;
    let target_scalars = target_scalar_cells(source, &mutations, limits)?;
    Ok((state, target_scalars))
}

fn changed_coordinates(
    source: &TableAutoFillHwpxReadback,
    mutations: &BTreeMap<CellCoordinate, &TableAutoFillMutation>,
) -> Result<BTreeSet<CellCoordinate>, TableAutoFillHwpxError> {
    let mut changed = BTreeSet::new();
    for scalar in &source.cells {
        let mutation = mutations
            .get(&scalar.coordinate)
            .ok_or(TableAutoFillHwpxError::PlanBindingMismatch)?;
        if scalar.visible_text != value_text(mutation.generated_value())?
            || mutation.clear_formula()
        {
            changed.insert(scalar.coordinate);
        }
    }
    Ok(changed)
}

fn validate_unselected_formula_dependencies(
    source: &TableAutoFillHwpxReadback,
    mutations: &BTreeMap<CellCoordinate, &TableAutoFillMutation>,
    changed: &BTreeSet<CellCoordinate>,
) -> Result<(), TableAutoFillHwpxError> {
    for cell in source.ruling.state.cells() {
        if mutations.contains_key(&cell.coordinate()) {
            continue;
        }
        if cell
            .formula()
            .is_some_and(|formula| formula_references_any(formula.ast().expression(), changed))
        {
            return Err(TableAutoFillHwpxError::UnsupportedFormulaDependency);
        }
    }
    Ok(())
}

fn target_scalar_cells(
    source: &TableAutoFillHwpxReadback,
    mutations: &BTreeMap<CellCoordinate, &TableAutoFillMutation>,
    limits: &TableAutoFillHwpxLimits,
) -> Result<Vec<ScalarCell>, TableAutoFillHwpxError> {
    let mut target = Vec::new();
    target
        .try_reserve_exact(source.cells.len())
        .map_err(|_| TableAutoFillHwpxError::Allocation)?;
    for scalar in &source.cells {
        let mutation = mutations
            .get(&scalar.coordinate)
            .ok_or(TableAutoFillHwpxError::PlanBindingMismatch)?;
        let text = value_text(mutation.generated_value())?;
        if scalar.visible_text == text && !mutation.clear_formula() {
            target.push((*scalar).clone());
            continue;
        }
        target.push(ScalarCell {
            coordinate: scalar.coordinate,
            visible_text: text.clone(),
            style_sha256: scalar.style_sha256,
            paragraph_bytes: target_paragraph(scalar, &text, limits)?,
            run_content_start: scalar.run_content_start,
            run_content_end: scalar.run_content_start,
            section_run_content_start: scalar.section_run_content_start,
            section_run_content_end: scalar.section_run_content_start,
        });
    }
    Ok(target)
}

fn validate_mutation_source(
    mutation: &TableAutoFillMutation,
    state_cell: &domain_ir::TableRulingCell,
    scalar: &ScalarCell,
    limits: &TableAutoFillHwpxLimits,
) -> Result<(), TableAutoFillHwpxError> {
    let formula_sha256 = state_cell
        .formula()
        .map(|formula| {
            formula
                .canonical_sha256(limits.native.formula)
                .map(create_hwpx::hex)
        })
        .transpose()?;
    if mutation.prior_payload_sha256() != aggregate_payload_digest(state_cell.payload())?
        || mutation.prior_formula_sha256() != formula_sha256.as_deref()
        || mutation.preserved_style_sha256() != create_hwpx::hex(scalar.style_sha256)
        || mutation.clear_formula() != state_cell.formula().is_some()
    {
        return Err(TableAutoFillHwpxError::PlanBindingMismatch);
    }
    Ok(())
}

fn read_scalar_cells(
    section: &[u8],
    table_ordinal: usize,
    region: TableAutoFillRegion,
    ruling: &TableRulingHwpxReadback,
    limits: &TableAutoFillHwpxLimits,
) -> Result<Vec<ScalarCell>, TableAutoFillHwpxError> {
    let document = PreservingXmlDocument::parse(section)?;
    let table = super::selected_table(&document, table_ordinal)?;
    let native_cells = super::selected_cells(&document, table, ruling.grid.master_cell_count())?;
    let expected = selected_cell_count(region)?;
    let mut cells = Vec::new();
    cells
        .try_reserve_exact(expected)
        .map_err(|_| TableAutoFillHwpxError::Allocation)?;
    for (cell, coordinate) in native_cells {
        if coordinate.row < region.start.row
            || coordinate.row > region.end.row
            || coordinate.column < region.start.column
            || coordinate.column > region.end.column
        {
            continue;
        }
        let span = ruling.grid.master_cell_at(coordinate)?;
        if span.row != coordinate.row
            || span.column != coordinate.column
            || span.row_span != 1
            || span.column_span != 1
        {
            return Err(TableAutoFillHwpxError::UnsupportedMergedCells);
        }
        let state_cell = ruling
            .state
            .cell(&span.master_cell_id)
            .ok_or(TableAutoFillHwpxError::SourceBindingMismatch)?;
        let sub_list = unique_direct_child(&document, cell, "subList")?;
        let paragraph = only_direct_child(&document, sub_list, "p")?;
        let run = only_direct_child(&document, paragraph, "run")?;
        let paragraph_element = super::element(&document, paragraph)?;
        let paragraph_span = paragraph_element
            .outer_span()
            .ok_or(TableAutoFillHwpxError::UnsupportedRichContent)?;
        let run_span = super::element(&document, run)?
            .content_span()
            .ok_or(TableAutoFillHwpxError::UnsupportedRichContent)?;
        if run_span.start() < paragraph_span.start() || run_span.end() > paragraph_span.end() {
            return Err(TableAutoFillHwpxError::UnsupportedRichContent);
        }
        let paragraph_bytes = section
            .get(paragraph_span.start()..paragraph_span.end())
            .ok_or(TableAutoFillHwpxError::UnsupportedRichContent)?
            .to_vec();
        let visible_text = if let Some(formula) = state_cell.formula() {
            if formula.owner() != coordinate {
                return Err(TableAutoFillHwpxError::SourceBindingMismatch);
            }
            let value = formula_cache_value(formula.cache())?;
            value_text(&value)?
        } else {
            let standalone = standalone_paragraph(&paragraph_bytes)?;
            let flow = TextFlowReader::read(&standalone, limits.flow)?;
            plain_visible_text(&flow)?
        };
        let relative_start = run_span.start() - paragraph_span.start();
        let relative_end = run_span.end() - paragraph_span.start();
        let style_sha256 = style_sha256(&paragraph_bytes, relative_start, relative_end)?;
        cells.push(ScalarCell {
            coordinate,
            visible_text,
            style_sha256,
            paragraph_bytes,
            run_content_start: relative_start,
            run_content_end: relative_end,
            section_run_content_start: run_span.start(),
            section_run_content_end: run_span.end(),
        });
    }
    if cells.len() != expected {
        return Err(TableAutoFillHwpxError::SourceBindingMismatch);
    }
    cells.sort_by_key(|cell| cell.coordinate);
    Ok(cells)
}

fn only_direct_child(
    document: &PreservingXmlDocument,
    parent: usize,
    local_name: &str,
) -> Result<usize, TableAutoFillHwpxError> {
    let mut child = super::element(document, parent)?.first_child();
    let mut found = None;
    let mut saw_layout_cache = false;
    while let Some(index) = child {
        let value = super::element(document, index)?;
        if super::has_name(value, local_name) {
            if found.replace(index).is_some() {
                return Err(TableAutoFillHwpxError::UnsupportedRichContent);
            }
        } else if local_name == "run" && super::has_name(value, "linesegarray") {
            if saw_layout_cache {
                return Err(TableAutoFillHwpxError::UnsupportedRichContent);
            }
            saw_layout_cache = true;
        } else {
            return Err(TableAutoFillHwpxError::UnsupportedRichContent);
        }
        child = value.next_sibling();
    }
    found.ok_or(TableAutoFillHwpxError::UnsupportedRichContent)
}

fn unique_direct_child(
    document: &PreservingXmlDocument,
    parent: usize,
    local_name: &str,
) -> Result<usize, TableAutoFillHwpxError> {
    let mut child = super::element(document, parent)?.first_child();
    let mut found = None;
    while let Some(index) = child {
        let value = super::element(document, index)?;
        if super::has_name(value, local_name) && found.replace(index).is_some() {
            return Err(TableAutoFillHwpxError::UnsupportedRichContent);
        }
        child = value.next_sibling();
    }
    found.ok_or(TableAutoFillHwpxError::UnsupportedRichContent)
}

fn plain_visible_text(flow: &crate::TextFlow) -> Result<String, TableAutoFillHwpxError> {
    let mut run = None;
    for child in &flow.children {
        match child {
            ParagraphChild::Run(value) if run.replace(value).is_none() => {}
            ParagraphChild::Opaque(value) if !value.may_contain_visible_text() => {}
            _ => return Err(TableAutoFillHwpxError::UnsupportedRichContent),
        }
    }
    let run = run.ok_or(TableAutoFillHwpxError::UnsupportedRichContent)?;
    let [TextRunItem::Text(span)] = run.items.as_slice() else {
        return Err(TableAutoFillHwpxError::UnsupportedRichContent);
    };
    if span.character_style_id_ref.is_some() {
        return Err(TableAutoFillHwpxError::UnsupportedRichContent);
    }
    let mut output = String::new();
    for atom in &span.atoms {
        match atom {
            TextAtom::Text(value) => output
                .try_reserve(value.len())
                .map_err(|_| TableAutoFillHwpxError::Allocation)
                .map(|()| output.push_str(value))?,
            TextAtom::Tab { .. } => output.push('\t'),
            TextAtom::LineBreak => output.push('\n'),
        }
    }
    Ok(output)
}

fn scalar_state_sha256(
    cells: &[ScalarCell],
    state: &TableRulingState,
    limits: &TableAutoFillHwpxLimits,
) -> Result<[u8; 32], TableAutoFillHwpxError> {
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.table-auto-fill-hwpx-scalar-state/v1\0");
    digest.update(
        u64::try_from(cells.len())
            .map_err(|_| TableAutoFillHwpxError::Allocation)?
            .to_le_bytes(),
    );
    for scalar in cells {
        let state_cell = state
            .cells()
            .iter()
            .find(|cell| cell.coordinate() == scalar.coordinate)
            .ok_or(TableAutoFillHwpxError::SourceBindingMismatch)?;
        digest.update(scalar.coordinate.row.to_le_bytes());
        digest.update(scalar.coordinate.column.to_le_bytes());
        hash_bytes(&mut digest, scalar.visible_text.as_bytes())?;
        digest.update(scalar.style_sha256);
        hash_bytes(
            &mut digest,
            aggregate_payload_digest(state_cell.payload())?.as_bytes(),
        )?;
        match state_cell.formula() {
            None => digest.update([0]),
            Some(formula) => {
                digest.update([1]);
                digest.update(formula.canonical_sha256(limits.native.formula)?);
            }
        }
    }
    Ok(digest.finalize().into())
}

fn style_sha256(
    paragraph: &[u8],
    run_content_start: usize,
    run_content_end: usize,
) -> Result<[u8; 32], TableAutoFillHwpxError> {
    if run_content_start > run_content_end || run_content_end > paragraph.len() {
        return Err(TableAutoFillHwpxError::UnsupportedRichContent);
    }
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.table-auto-fill-hwpx-cell-style/v1\0");
    hash_bytes(&mut digest, &paragraph[..run_content_start])?;
    hash_bytes(&mut digest, &paragraph[run_content_end..])?;
    Ok(digest.finalize().into())
}

fn target_paragraph(
    source: &ScalarCell,
    text: &str,
    limits: &TableAutoFillHwpxLimits,
) -> Result<Vec<u8>, TableAutoFillHwpxError> {
    let replacement = canonical_run_content(text, limits)?;
    replace_range(
        &source.paragraph_bytes,
        source.run_content_start,
        source.run_content_end,
        &replacement,
        limits.native.layout.config().output_bytes,
    )
}

fn canonical_run_content(
    text: &str,
    limits: &TableAutoFillHwpxLimits,
) -> Result<Vec<u8>, TableAutoFillHwpxError> {
    if text.is_empty() {
        return Ok(b"<hp:t/>".to_vec());
    }
    let paragraph = canonical_text_paragraph(text, limits.flow)?;
    let document = PreservingXmlDocument::parse(&paragraph)?;
    let run = only_direct_child(&document, document.root_element(), "run")?;
    let span = super::element(&document, run)?
        .content_span()
        .ok_or(TableAutoFillHwpxError::UnsupportedRichContent)?;
    paragraph
        .get(span.start()..span.end())
        .map(ToOwned::to_owned)
        .ok_or(TableAutoFillHwpxError::UnsupportedRichContent)
}

fn patch_selected_runs(
    section: &[u8],
    source: &TableAutoFillHwpxReadback,
    fill: &TableAutoFillPlan,
    limits: &TableAutoFillHwpxLimits,
) -> Result<Vec<u8>, TableAutoFillHwpxError> {
    let mutations = fill
        .mutations()
        .iter()
        .map(|mutation| (mutation.coordinate(), mutation))
        .collect::<BTreeMap<_, _>>();
    let mut edits = Vec::new();
    edits
        .try_reserve_exact(source.cells.len())
        .map_err(|_| TableAutoFillHwpxError::Allocation)?;
    for scalar in &source.cells {
        let mutation = mutations
            .get(&scalar.coordinate)
            .ok_or(TableAutoFillHwpxError::PlanBindingMismatch)?;
        let text = value_text(mutation.generated_value())?;
        if scalar.visible_text == text && !mutation.clear_formula() {
            continue;
        }
        edits.push(RawEdit {
            start: scalar.section_run_content_start,
            end: scalar.section_run_content_end,
            replacement: canonical_run_content(&text, limits)?,
        });
    }
    Ok(super::apply_edits(
        section,
        &mut edits,
        limits.native.layout.config().output_bytes,
    )?)
}

fn replace_range(
    source: &[u8],
    start: usize,
    end: usize,
    replacement: &[u8],
    maximum: usize,
) -> Result<Vec<u8>, TableAutoFillHwpxError> {
    if start > end || end > source.len() {
        return Err(TableAutoFillHwpxError::UnsupportedRichContent);
    }
    let output_len = source
        .len()
        .checked_sub(end - start)
        .and_then(|value| value.checked_add(replacement.len()))
        .ok_or(TableAutoFillHwpxError::OutputLimit)?;
    if output_len > maximum {
        return Err(TableAutoFillHwpxError::OutputLimit);
    }
    let mut output = Vec::new();
    output
        .try_reserve_exact(output_len)
        .map_err(|_| TableAutoFillHwpxError::Allocation)?;
    output.extend_from_slice(&source[..start]);
    output.extend_from_slice(replacement);
    output.extend_from_slice(&source[end..]);
    Ok(output)
}

fn generated_value_for_coordinate(
    series: &TableAutoFillSeries,
    region: TableAutoFillRegion,
    order: TableAutoFillOrder,
    start_index: u64,
    coordinate: CellCoordinate,
) -> Result<TableAutoFillValue, TableAutoFillHwpxError> {
    if coordinate.row < region.start.row
        || coordinate.row > region.end.row
        || coordinate.column < region.start.column
        || coordinate.column > region.end.column
    {
        return Err(TableAutoFillHwpxError::SourceBindingMismatch);
    }
    let rows = u64::from(region.end.row - region.start.row + 1);
    let columns = u64::from(region.end.column - region.start.column + 1);
    let row = u64::from(coordinate.row - region.start.row);
    let column = u64::from(coordinate.column - region.start.column);
    let offset = match order {
        TableAutoFillOrder::RowMajor => row
            .checked_mul(columns)
            .and_then(|value| value.checked_add(column)),
        TableAutoFillOrder::ColumnMajor => column
            .checked_mul(rows)
            .and_then(|value| value.checked_add(row)),
    }
    .ok_or(TableAutoFillHwpxError::SourceBindingMismatch)?;
    let index = start_index
        .checked_add(offset)
        .ok_or(TableAutoFillError::GenerationOverflow)?;
    Ok(series.value_at(index)?)
}

fn formula_references_any(
    expression: &FormulaExpression,
    coordinates: &BTreeSet<CellCoordinate>,
) -> bool {
    match expression {
        FormulaExpression::Decimal { .. } => false,
        FormulaExpression::Cell { reference } => coordinates.contains(&CellCoordinate {
            row: reference.row,
            column: reference.column,
        }),
        FormulaExpression::Range { range } => coordinates.iter().any(|coordinate| {
            coordinate.row >= range.start.row.min(range.end.row)
                && coordinate.row <= range.start.row.max(range.end.row)
                && coordinate.column >= range.start.column.min(range.end.column)
                && coordinate.column <= range.start.column.max(range.end.column)
        }),
        FormulaExpression::Unary { operand, .. } => formula_references_any(operand, coordinates),
        FormulaExpression::Binary { left, right, .. } => {
            formula_references_any(left, coordinates) || formula_references_any(right, coordinates)
        }
        FormulaExpression::Function { arguments, .. } => arguments
            .iter()
            .any(|argument| formula_references_any(argument, coordinates)),
    }
}

fn value_text(value: &TableAutoFillValue) -> Result<String, TableAutoFillHwpxError> {
    match value {
        TableAutoFillValue::Blank => Ok(String::new()),
        TableAutoFillValue::Boolean { value } => Ok(value.to_string()),
        TableAutoFillValue::Integer { value } => Ok(value.to_string()),
        TableAutoFillValue::Decimal { coefficient, scale } => decimal_text(*coefficient, *scale),
        TableAutoFillValue::DateDays {
            days_since_unix_epoch,
        } => Ok(date_text(*days_since_unix_epoch)),
        TableAutoFillValue::Text { value } => Ok(value.clone()),
    }
}

fn decimal_text(coefficient: i64, scale: u8) -> Result<String, TableAutoFillHwpxError> {
    if scale == 0 || scale > 18 {
        return Err(TableAutoFillHwpxError::SourceBindingMismatch);
    }
    let negative = coefficient < 0;
    let magnitude = i128::from(coefficient).abs().to_string();
    let scale = usize::from(scale);
    let mut output = String::new();
    let required = magnitude
        .len()
        .max(scale.saturating_add(1))
        .checked_add(usize::from(negative))
        .and_then(|value| value.checked_add(1))
        .ok_or(TableAutoFillHwpxError::Allocation)?;
    output
        .try_reserve_exact(required)
        .map_err(|_| TableAutoFillHwpxError::Allocation)?;
    if negative {
        output.push('-');
    }
    if magnitude.len() <= scale {
        output.push('0');
        output.push('.');
        for _ in 0..(scale - magnitude.len()) {
            output.push('0');
        }
        output.push_str(&magnitude);
    } else {
        let split = magnitude.len() - scale;
        output.push_str(&magnitude[..split]);
        output.push('.');
        output.push_str(&magnitude[split..]);
    }
    Ok(output)
}

fn date_text(days_since_unix_epoch: i32) -> String {
    let z = i64::from(days_since_unix_epoch) + 719_468;
    let era = if z >= 0 { z } else { z - 146_096 } / 146_097;
    let day_of_era = z - era * 146_097;
    let year_of_era =
        (day_of_era - day_of_era / 1_460 + day_of_era / 36_524 - day_of_era / 146_096) / 365;
    let mut year = year_of_era + era * 400;
    let day_of_year = day_of_era - (365 * year_of_era + year_of_era / 4 - year_of_era / 100);
    let month_prime = (5 * day_of_year + 2) / 153;
    let day = day_of_year - (153 * month_prime + 2) / 5 + 1;
    let month = month_prime + if month_prime < 10 { 3 } else { -9 };
    year += i64::from(month <= 2);
    let year_text = match year {
        0..=9_999 => format!("{year:04}"),
        value if value < 0 => format!("-{value:04}", value = value.unsigned_abs()),
        value => format!("+{value}"),
    };
    format!("{year_text}-{month:02}-{day:02}")
}

fn formula_cache_value(cache: &FormulaCache) -> Result<TableAutoFillValue, TableAutoFillHwpxError> {
    let FormulaCache::Unverified {
        value: FormulaValue::Decimal { value },
    } = cache
    else {
        return Err(TableAutoFillHwpxError::UnsupportedFormulaCache);
    };
    if value.scale() == 0 {
        Ok(TableAutoFillValue::Integer {
            value: value.coefficient(),
        })
    } else {
        Ok(TableAutoFillValue::Decimal {
            coefficient: value.coefficient(),
            scale: value.scale(),
        })
    }
}

fn classify_value(value: &str) -> Result<TableAutoFillValue, TableAutoFillHwpxError> {
    if value.is_empty() {
        return Ok(TableAutoFillValue::Blank);
    }
    if value == "false" || value == "true" {
        return Ok(TableAutoFillValue::Boolean {
            value: value == "true",
        });
    }
    if canonical_integer_syntax(value) {
        return value
            .parse::<i64>()
            .map(|value| TableAutoFillValue::Integer { value })
            .map_err(|_| TableAutoFillHwpxError::UnsupportedRichContent);
    }
    if let Some((integer, fraction)) = canonical_decimal_parts(value) {
        if fraction.len() > 18 {
            return Err(TableAutoFillHwpxError::UnsupportedRichContent);
        }
        let mut coefficient = String::new();
        coefficient
            .try_reserve(integer.len().saturating_add(fraction.len()))
            .map_err(|_| TableAutoFillHwpxError::Allocation)?;
        coefficient.push_str(integer);
        coefficient.push_str(fraction);
        return Ok(TableAutoFillValue::Decimal {
            coefficient: coefficient
                .parse::<i64>()
                .map_err(|_| TableAutoFillHwpxError::UnsupportedRichContent)?,
            scale: u8::try_from(fraction.len())
                .map_err(|_| TableAutoFillHwpxError::UnsupportedRichContent)?,
        });
    }
    Ok(TableAutoFillValue::Text {
        value: value.to_owned(),
    })
}

fn canonical_integer_syntax(value: &str) -> bool {
    let unsigned = value.strip_prefix('-').unwrap_or(value);
    !unsigned.is_empty()
        && unsigned.bytes().all(|byte| byte.is_ascii_digit())
        && (unsigned == "0" || !unsigned.starts_with('0'))
        && value != "-0"
}

fn canonical_decimal_parts(value: &str) -> Option<(&str, &str)> {
    let (integer, fraction) = value.split_once('.')?;
    let unsigned = integer.strip_prefix('-').unwrap_or(integer);
    if unsigned.is_empty()
        || fraction.is_empty()
        || !unsigned.bytes().all(|byte| byte.is_ascii_digit())
        || !fraction.bytes().all(|byte| byte.is_ascii_digit())
        || (unsigned != "0" && unsigned.starts_with('0'))
        || integer == "-0" && fraction.bytes().all(|byte| byte == b'0')
    {
        return None;
    }
    Some((integer, fraction))
}

fn validate_region(
    region: TableAutoFillRegion,
    grid: &TableGrid,
    limits: TableAutoFillLimits,
) -> Result<(), TableAutoFillHwpxError> {
    if region.start.row > region.end.row || region.start.column > region.end.column {
        return Err(TableAutoFillError::RegionOrder.into());
    }
    if region.end.row >= grid.rows() || region.end.column >= grid.columns() {
        return Err(TableAutoFillError::RegionOutOfBounds.into());
    }
    let count = selected_cell_count(region)?;
    if count > limits.config().selected_cells {
        return Err(TableAutoFillError::SelectionLimit.into());
    }
    for row in region.start.row..=region.end.row {
        for column in region.start.column..=region.end.column {
            let span = grid.master_cell_at(CellCoordinate { row, column })?;
            if span.row != row
                || span.column != column
                || span.row_span != 1
                || span.column_span != 1
            {
                return Err(TableAutoFillHwpxError::UnsupportedMergedCells);
            }
        }
    }
    Ok(())
}

fn selected_cell_count(region: TableAutoFillRegion) -> Result<usize, TableAutoFillHwpxError> {
    usize::try_from(region.end.row - region.start.row + 1)
        .ok()
        .and_then(|rows| {
            usize::try_from(region.end.column - region.start.column + 1)
                .ok()
                .and_then(|columns| rows.checked_mul(columns))
        })
        .ok_or(TableAutoFillHwpxError::Allocation)
}

fn aggregate_payload_digest(
    values: &[TableRulingPayloadBlock],
) -> Result<String, TableAutoFillHwpxError> {
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.table-auto-fill-hwpx-payload/v1\0");
    digest.update(
        u64::try_from(values.len())
            .map_err(|_| TableAutoFillHwpxError::Allocation)?
            .to_le_bytes(),
    );
    for value in values {
        hash_bytes(&mut digest, value.block_id.as_str().as_bytes())?;
        hash_bytes(&mut digest, value.payload_sha256.as_bytes())?;
    }
    Ok(create_hwpx::hex(digest.finalize()))
}

fn hash_bytes(digest: &mut Sha256, value: &[u8]) -> Result<(), TableAutoFillHwpxError> {
    digest.update(
        u64::try_from(value.len())
            .map_err(|_| TableAutoFillHwpxError::Allocation)?
            .to_le_bytes(),
    );
    digest.update(value);
    Ok(())
}

fn same_pagination_policy(
    source: &TablePaginationHwpxReadback,
    target: &TablePaginationHwpxReadback,
) -> bool {
    source.page_split == target.page_split
        && source.repeat_header_rows == target.repeat_header_rows
        && source.row_count == target.row_count
        && source.column_count == target.column_count
        && source.caption == target.caption
}

fn pagination_policy_sha256(value: &TablePaginationHwpxReadback) -> [u8; 32] {
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.table-auto-fill-hwpx-pagination-policy/v1\0");
    digest.update([match value.page_split {
        TablePageSplitPolicy::Allow => 0,
        TablePageSplitPolicy::AvoidRow => 1,
        TablePageSplitPolicy::AvoidTable => 2,
        TablePageSplitPolicy::RequiredKeep => 3,
    }]);
    digest.update(value.repeat_header_rows.to_le_bytes());
    digest.update(value.row_count.to_le_bytes());
    digest.update(value.column_count.to_le_bytes());
    match &value.caption {
        None => digest.update([0]),
        Some(caption) => {
            digest.update([1]);
            digest.update([match caption.side {
                CaptionSide::Top => 0,
                CaptionSide::Bottom => 1,
            }]);
            digest.update([u8::from(caption.full_size)]);
            digest.update(caption.width_hwpunit.to_le_bytes());
            digest.update(caption.gap_hwpunit.to_le_bytes());
            digest.update(caption.last_width_hwpunit.to_le_bytes());
            digest.update(caption.content_sha256);
        }
    }
    digest.finalize().into()
}

fn serialized_limit(limits: &TableAutoFillHwpxLimits) -> usize {
    limits
        .auto_fill
        .config()
        .serialized_bytes
        .min(limits.native.ruling.config().serialized_bytes)
        .min(limits.native.grid.config().serialized_bytes)
        .min(limits.flow.config().input_bytes)
}

fn serialize_bounded<T: Serialize + ?Sized>(
    value: &T,
    maximum: usize,
) -> Result<Vec<u8>, TableAutoFillHwpxError> {
    let bytes = serde_json::to_vec(value).map_err(|_| TableAutoFillHwpxError::Serialization)?;
    if bytes.len() > maximum {
        return Err(TableAutoFillHwpxError::OutputLimit);
    }
    Ok(bytes)
}

fn parse_digest(value: &str) -> Result<[u8; 32], TableAutoFillHwpxError> {
    create_hwpx::require_digest(value)
        .map_err(|_| TableAutoFillHwpxError::SourceBindingMismatch)?;
    let mut output = [0_u8; 32];
    for (index, chunk) in value.as_bytes().chunks_exact(2).enumerate() {
        let text = std::str::from_utf8(chunk)
            .map_err(|_| TableAutoFillHwpxError::SourceBindingMismatch)?;
        output[index] = u8::from_str_radix(text, 16)
            .map_err(|_| TableAutoFillHwpxError::SourceBindingMismatch)?;
    }
    Ok(output)
}
