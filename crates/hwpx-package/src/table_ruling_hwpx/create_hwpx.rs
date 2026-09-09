use std::collections::BTreeSet;
use std::fmt;

use domain_ir::{
    LogicalId, TABLE_RULING_SCHEMA_VERSION, TableGrid, TableGridError, TableOperationError,
    TableOperationReceipt, TableRulingAxis, TableRulingCellDraft, TableRulingEdge,
    TableRulingError, TableRulingFrame, TableRulingState, TableRulingStateDraft,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use super::{
    RawEdit, TableRulingHwpxBinding, TableRulingHwpxError, TableRulingHwpxLimits,
    TableRulingHwpxReadback, TableRulingHwpxReader,
};
use crate::preserving_xml::PreservingXmlDocument;
use crate::{
    TablePaginationHwpxError, TablePaginationHwpxLimits, TablePaginationHwpxReadback,
    TablePaginationHwpxReader,
};

pub const TABLE_CREATE_HWPX_SCHEMA_VERSION: &str = "hwpx-agent.table-create-hwpx/v1";
pub const TABLE_CREATE_HWPX_PROFILE_ID: &str =
    "hwpx-agent.table-create-hwpx.hancom-2020-template/1";

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TableCreateHwpxLimits {
    pub ruling: TableRulingHwpxLimits,
    pub pagination: TablePaginationHwpxLimits,
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableCreateHwpxReadback {
    pub profile_id: &'static str,
    pub placeholder_paragraph_ordinal: usize,
    pub template_table_ordinal: usize,
    pub header_sha256: [u8; 32],
    pub section_sha256: [u8; 32],
    pub template_section_sha256: [u8; 32],
    pub insertion_context_sha256: String,
    pub source_table_count: usize,
    pub template: TableRulingHwpxReadback,
    pub template_pagination: TablePaginationHwpxReadback,
}

impl fmt::Debug for TableCreateHwpxReadback {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableCreateHwpxReadback")
            .field("profile_id", &self.profile_id)
            .field(
                "placeholder_paragraph_ordinal",
                &self.placeholder_paragraph_ordinal,
            )
            .field("template_table_ordinal", &self.template_table_ordinal)
            .field("source_table_count", &self.source_table_count)
            .field("template_rows", &self.template.grid.rows())
            .field("template_columns", &self.template.grid.columns())
            .field("page_split", &self.template_pagination.page_split)
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct TableCreateHwpxReader;

impl TableCreateHwpxReader {
    /// Reads a bound empty insertion paragraph and an exact 2x2 native style template.
    ///
    /// # Errors
    ///
    /// Rejects malformed, ambiguous, nonempty, merged, formula-bearing, captioned, nonuniform or
    /// over-limit source/template input.
    #[allow(clippy::too_many_arguments)]
    pub fn read_context(
        header: &[u8],
        section: &[u8],
        placeholder_paragraph_ordinal: usize,
        template_section: &[u8],
        template_table_ordinal: usize,
        template_binding: &TableRulingHwpxBinding,
        limits: TableCreateHwpxLimits,
    ) -> Result<TableCreateHwpxReadback, TableCreateHwpxError> {
        let document = PreservingXmlDocument::parse(section)?;
        let placeholder = super::selected_empty_top_level_paragraph(
            section,
            &document,
            placeholder_paragraph_ordinal,
        )?;
        let insertion_context_sha256 = super::insertion_context_digest(
            section,
            &document,
            placeholder,
            placeholder_paragraph_ordinal,
        )?;
        let template = TableRulingHwpxReader::read_existing(
            header,
            template_section,
            template_table_ordinal,
            template_binding,
            limits.ruling,
        )?;
        let template_pagination = TablePaginationHwpxReader::read_in_section(
            template_section,
            template_table_ordinal,
            limits.pagination,
        )?;
        require_template_profile(&template, &template_pagination)?;
        let _ = super::insertion_wrapper(template_section, template_table_ordinal)?;
        Ok(TableCreateHwpxReadback {
            profile_id: TABLE_CREATE_HWPX_PROFILE_ID,
            placeholder_paragraph_ordinal,
            template_table_ordinal,
            header_sha256: Sha256::digest(header).into(),
            section_sha256: Sha256::digest(section).into(),
            template_section_sha256: Sha256::digest(template_section).into(),
            insertion_context_sha256,
            source_table_count: TablePaginationHwpxReader::count_in_section(
                section,
                limits.pagination,
            )?,
            template,
            template_pagination,
        })
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableCreateHwpxRequestDraft {
    pub schema_version: String,
    pub placeholder_paragraph_ordinal: usize,
    pub template_table_ordinal: usize,
    pub expected_header_sha256: String,
    pub expected_section_sha256: String,
    pub expected_template_section_sha256: String,
    pub expected_template_state_sha256: String,
    pub expected_template_grid_sha256: String,
    pub expected_insertion_context_sha256: String,
    pub expected_document_flow_sha256: String,
    pub target_document_flow_sha256: String,
    pub table_id: LogicalId,
    pub rows: u32,
    pub columns: u32,
    pub master_cell_ids: Vec<LogicalId>,
    pub row_heights_hwpunit: Vec<u32>,
    pub column_widths_hwpunit: Vec<u32>,
}

impl fmt::Debug for TableCreateHwpxRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableCreateHwpxRequestDraft")
            .field("schema_version", &self.schema_version)
            .field(
                "placeholder_paragraph_ordinal",
                &self.placeholder_paragraph_ordinal,
            )
            .field("template_table_ordinal", &self.template_table_ordinal)
            .field("expected_header_sha256", &"<redacted>")
            .field("expected_section_sha256", &"<redacted>")
            .field("expected_template_section_sha256", &"<redacted>")
            .field("expected_template_state_sha256", &"<redacted>")
            .field("expected_template_grid_sha256", &"<redacted>")
            .field("expected_insertion_context_sha256", &"<redacted>")
            .field("expected_document_flow_sha256", &"<redacted>")
            .field("target_document_flow_sha256", &"<redacted>")
            .field("table_id", &"<redacted>")
            .field("rows", &self.rows)
            .field("columns", &self.columns)
            .field("master_cell_count", &self.master_cell_ids.len())
            .field("row_track_count", &self.row_heights_hwpunit.len())
            .field("column_track_count", &self.column_widths_hwpunit.len())
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableCreateHwpxRequest {
    schema_version: &'static str,
    capability_id: &'static str,
    placeholder_paragraph_ordinal: usize,
    template_table_ordinal: usize,
    expected_header_sha256: String,
    expected_section_sha256: String,
    expected_template_section_sha256: String,
    expected_template_state_sha256: String,
    expected_template_grid_sha256: String,
    expected_insertion_context_sha256: String,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    table_id: LogicalId,
    rows: u32,
    columns: u32,
    master_cell_ids: Vec<LogicalId>,
    row_heights_hwpunit: Vec<u32>,
    column_widths_hwpunit: Vec<u32>,
}

impl TableCreateHwpxRequest {
    /// Binds one complete unmerged create request to source, template, insertion and flow state.
    ///
    /// # Errors
    ///
    /// Rejects schema, digest, source, template, geometry, identity, flow or finite-limit drift.
    pub fn from_draft(
        draft: TableCreateHwpxRequestDraft,
        source: &TableCreateHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableCreateHwpxLimits,
    ) -> Result<Self, TableCreateHwpxError> {
        if draft.schema_version != TABLE_CREATE_HWPX_SCHEMA_VERSION {
            return Err(TableCreateHwpxError::UnsupportedVersion);
        }
        for digest in [
            &draft.expected_header_sha256,
            &draft.expected_section_sha256,
            &draft.expected_template_section_sha256,
            &draft.expected_template_state_sha256,
            &draft.expected_template_grid_sha256,
            &draft.expected_insertion_context_sha256,
            &draft.expected_document_flow_sha256,
            &draft.target_document_flow_sha256,
            current_document_flow_sha256,
        ] {
            require_digest(digest)?;
        }
        let request = Self {
            schema_version: TABLE_CREATE_HWPX_SCHEMA_VERSION,
            capability_id: "table.create",
            placeholder_paragraph_ordinal: draft.placeholder_paragraph_ordinal,
            template_table_ordinal: draft.template_table_ordinal,
            expected_header_sha256: draft.expected_header_sha256,
            expected_section_sha256: draft.expected_section_sha256,
            expected_template_section_sha256: draft.expected_template_section_sha256,
            expected_template_state_sha256: draft.expected_template_state_sha256,
            expected_template_grid_sha256: draft.expected_template_grid_sha256,
            expected_insertion_context_sha256: draft.expected_insertion_context_sha256,
            expected_document_flow_sha256: draft.expected_document_flow_sha256,
            target_document_flow_sha256: draft.target_document_flow_sha256,
            table_id: draft.table_id,
            rows: draft.rows,
            columns: draft.columns,
            master_cell_ids: draft.master_cell_ids,
            row_heights_hwpunit: draft.row_heights_hwpunit,
            column_widths_hwpunit: draft.column_widths_hwpunit,
        };
        validate_request_source(&request, source, current_document_flow_sha256, &limits)?;
        let _ =
            TableCreateHwpxBuilder::build(&request, source, current_document_flow_sha256, limits)?;
        let _ = request.canonical_json(limits)?;
        Ok(request)
    }

    /// Parses strict bounded JSON and applies the same admission as [`Self::from_draft`].
    ///
    /// # Errors
    ///
    /// Rejects empty, oversized, malformed, duplicate, unknown or semantically invalid JSON.
    pub fn from_json(
        bytes: &[u8],
        source: &TableCreateHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableCreateHwpxLimits,
    ) -> Result<Self, TableCreateHwpxError> {
        if bytes.is_empty()
            || bytes.len() > limits.ruling.grid.config().serialized_bytes
            || bytes.len() > limits.ruling.ruling.config().serialized_bytes
        {
            return Err(TableCreateHwpxError::InputLimit);
        }
        reject_duplicate_json_keys(bytes)?;
        let draft = serde_json::from_slice(bytes).map_err(|_| TableCreateHwpxError::InvalidJson)?;
        Self::from_draft(draft, source, current_document_flow_sha256, limits)
    }

    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
    }

    #[must_use]
    pub const fn placeholder_paragraph_ordinal(&self) -> usize {
        self.placeholder_paragraph_ordinal
    }

    #[must_use]
    pub fn target_document_flow_sha256(&self) -> &str {
        &self.target_document_flow_sha256
    }

    /// Serializes the complete typed request under both configured output bounds.
    ///
    /// # Errors
    ///
    /// Rejects serialization or finite output failure.
    pub fn canonical_json(
        &self,
        limits: TableCreateHwpxLimits,
    ) -> Result<Vec<u8>, TableCreateHwpxError> {
        serialize_bounded(self, serialized_limit(&limits))
    }

    /// Hashes the bounded canonical request.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failure.
    pub fn canonical_sha256(
        &self,
        limits: TableCreateHwpxLimits,
    ) -> Result<[u8; 32], TableCreateHwpxError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TableCreateHwpxRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableCreateHwpxRequest")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field(
                "placeholder_paragraph_ordinal",
                &self.placeholder_paragraph_ordinal,
            )
            .field("template_table_ordinal", &self.template_table_ordinal)
            .field("expected_header_sha256", &"<redacted>")
            .field("expected_section_sha256", &"<redacted>")
            .field("expected_template_section_sha256", &"<redacted>")
            .field("expected_template_state_sha256", &"<redacted>")
            .field("expected_template_grid_sha256", &"<redacted>")
            .field("expected_insertion_context_sha256", &"<redacted>")
            .field("expected_document_flow_sha256", &"<redacted>")
            .field("target_document_flow_sha256", &"<redacted>")
            .field("table_id", &"<redacted>")
            .field("rows", &self.rows)
            .field("columns", &self.columns)
            .field("master_cell_count", &self.master_cell_ids.len())
            .field("row_track_count", &self.row_heights_hwpunit.len())
            .field("column_track_count", &self.column_widths_hwpunit.len())
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableCreateHwpxPlan {
    schema_version: &'static str,
    capability_id: &'static str,
    request_sha256: String,
    source_table_count: usize,
    target_table_count: usize,
    source_header_sha256: String,
    source_section_sha256: String,
    template_section_sha256: String,
    insertion_context_sha256: String,
    target_state_sha256: String,
    target_grid_sha256: String,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    operation_receipt: TableOperationReceipt,
    target_state: TableRulingState,
    #[serde(skip)]
    target_grid: TableGrid,
}

impl TableCreateHwpxPlan {
    #[must_use]
    pub const fn target_state(&self) -> &TableRulingState {
        &self.target_state
    }

    #[must_use]
    pub const fn target_grid(&self) -> &TableGrid {
        &self.target_grid
    }

    #[must_use]
    pub const fn operation_receipt(&self) -> &TableOperationReceipt {
        &self.operation_receipt
    }

    /// Serializes all semantic and integrity bindings under finite output bounds.
    ///
    /// # Errors
    ///
    /// Rejects serialization or finite output failure.
    pub fn canonical_json(
        &self,
        limits: TableCreateHwpxLimits,
    ) -> Result<Vec<u8>, TableCreateHwpxError> {
        serialize_bounded(self, serialized_limit(&limits))
    }

    /// Hashes the bounded canonical plan.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failure.
    pub fn canonical_sha256(
        &self,
        limits: TableCreateHwpxLimits,
    ) -> Result<[u8; 32], TableCreateHwpxError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TableCreateHwpxPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableCreateHwpxPlan")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("source_table_count", &self.source_table_count)
            .field("target_table_count", &self.target_table_count)
            .field("target_rows", &self.target_grid.rows())
            .field("target_columns", &self.target_grid.columns())
            .field("operation_receipt", &self.operation_receipt)
            .field("target_state", &self.target_state)
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct TableCreateHwpxBuilder;

impl TableCreateHwpxBuilder {
    /// Revalidates the source/template and builds a complete unmerged native target state.
    ///
    /// # Errors
    ///
    /// Rejects source, flow, identity, geometry, template, grid, state or bound drift.
    pub fn build(
        request: &TableCreateHwpxRequest,
        source: &TableCreateHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableCreateHwpxLimits,
    ) -> Result<TableCreateHwpxPlan, TableCreateHwpxError> {
        validate_request_source(request, source, current_document_flow_sha256, &limits)?;
        validate_tracks(request, &limits)?;
        if request
            .master_cell_ids
            .iter()
            .any(|identifier| identifier == &request.table_id)
        {
            return Err(TableCreateHwpxError::IdentityConflict);
        }
        let result = TableGrid::create_unmerged(
            request.rows,
            request.columns,
            request.master_cell_ids.clone(),
            limits.ruling.grid,
        )?;
        let (target_grid, operation_receipt) = result.into_parts();
        let target_state = build_target_state(request, source, &target_grid, &limits)?;
        let target_table_count = source
            .source_table_count
            .checked_add(1)
            .ok_or(TableCreateHwpxError::OutputLimit)?;
        let plan = TableCreateHwpxPlan {
            schema_version: TABLE_CREATE_HWPX_SCHEMA_VERSION,
            capability_id: request.capability_id,
            request_sha256: hex(request.canonical_sha256(limits)?),
            source_table_count: source.source_table_count,
            target_table_count,
            source_header_sha256: hex(source.header_sha256),
            source_section_sha256: hex(source.section_sha256),
            template_section_sha256: hex(source.template_section_sha256),
            insertion_context_sha256: source.insertion_context_sha256.clone(),
            target_state_sha256: hex(target_state.canonical_sha256(limits.ruling.ruling)?),
            target_grid_sha256: hex(target_grid.canonical_sha256()?),
            expected_document_flow_sha256: request.expected_document_flow_sha256.clone(),
            target_document_flow_sha256: request.target_document_flow_sha256.clone(),
            operation_receipt,
            target_state,
            target_grid,
        };
        let _ = plan.canonical_json(limits)?;
        Ok(plan)
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableCreateHwpxLoweringReceipt {
    pub profile_id: &'static str,
    pub source_header_sha256: [u8; 32],
    pub output_header_sha256: [u8; 32],
    pub source_section_sha256: [u8; 32],
    pub output_section_sha256: [u8; 32],
    pub template_section_sha256: [u8; 32],
    pub insertion_context_sha256: [u8; 32],
    pub target_state_sha256: [u8; 32],
    pub target_grid_sha256: [u8; 32],
    pub request_sha256: [u8; 32],
    pub plan_sha256: [u8; 32],
    pub before_document_flow_sha256: [u8; 32],
    pub after_document_flow_sha256: [u8; 32],
    pub source_table_count: usize,
    pub target_table_count: usize,
    pub target_rows: u32,
    pub target_columns: u32,
    pub created_master_cell_count: usize,
    pub payload_block_count: usize,
    pub formula_count: usize,
    pub added_border_fill_count: usize,
    pub page_split_preserved: bool,
}

impl fmt::Debug for TableCreateHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableCreateHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field("source_table_count", &self.source_table_count)
            .field("target_table_count", &self.target_table_count)
            .field("target_rows", &self.target_rows)
            .field("target_columns", &self.target_columns)
            .field("created_master_cell_count", &self.created_master_cell_count)
            .field("payload_block_count", &self.payload_block_count)
            .field("formula_count", &self.formula_count)
            .field("added_border_fill_count", &self.added_border_fill_count)
            .field("page_split_preserved", &self.page_split_preserved)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableCreateHwpxLoweredParts {
    pub header: Vec<u8>,
    pub section: Vec<u8>,
    pub binding: TableRulingHwpxBinding,
    pub table_ordinal: usize,
    pub receipt: TableCreateHwpxLoweringReceipt,
}

impl fmt::Debug for TableCreateHwpxLoweredParts {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableCreateHwpxLoweredParts")
            .field("header_bytes", &self.header.len())
            .field("section_bytes", &self.section.len())
            .field("binding", &self.binding)
            .field("table_ordinal", &self.table_ordinal)
            .field("receipt", &self.receipt)
            .finish()
    }
}

#[derive(Debug)]
pub struct TableCreateHwpxLowerer;

impl TableCreateHwpxLowerer {
    /// Creates one table and returns coordinated parts only after complete semantic reopen.
    ///
    /// # Errors
    ///
    /// Rejects source, template, request, plan, state, grid, flow, insertion, pagination or
    /// readback drift without returning partial output.
    #[allow(clippy::too_many_arguments)]
    pub fn lower_at_placeholder(
        header: &[u8],
        section: &[u8],
        template_section: &[u8],
        template_binding: &TableRulingHwpxBinding,
        current_document_flow_sha256: &str,
        request: &TableCreateHwpxRequest,
        plan: &TableCreateHwpxPlan,
        limits: TableCreateHwpxLimits,
    ) -> Result<TableCreateHwpxLoweredParts, TableCreateHwpxError> {
        let source = TableCreateHwpxReader::read_context(
            header,
            section,
            request.placeholder_paragraph_ordinal,
            template_section,
            request.template_table_ordinal,
            template_binding,
            limits,
        )?;
        validate_request_source(request, &source, current_document_flow_sha256, &limits)?;
        let rebuilt =
            TableCreateHwpxBuilder::build(request, &source, current_document_flow_sha256, limits)?;
        if rebuilt != *plan {
            return Err(TableCreateHwpxError::PlanBindingMismatch);
        }
        let rendered = super::render_create_from_template(
            header,
            template_section,
            request.template_table_ordinal,
            template_binding,
            &source.template.state,
            plan.target_state(),
            plan.target_grid(),
            &limits.ruling,
        )?;
        let wrapper = super::insertion_wrapper(&rendered.section, request.template_table_ordinal)?;
        super::ensure_native_table_id_available(
            section,
            &rendered.section,
            request.template_table_ordinal,
        )?;
        let document = PreservingXmlDocument::parse(section)?;
        let placeholder = super::selected_empty_top_level_paragraph(
            section,
            &document,
            request.placeholder_paragraph_ordinal,
        )?;
        let placeholder_span = super::element(&document, placeholder)?
            .outer_span()
            .ok_or(TableCreateHwpxError::ReadbackMismatch)?;
        let table_ordinal = super::tables_before_offset(&document, placeholder_span.start());
        let mut edits = vec![RawEdit {
            start: placeholder_span.start(),
            end: placeholder_span.end(),
            replacement: wrapper,
        }];
        let output_section = super::apply_edits(
            section,
            &mut edits,
            limits.ruling.layout.config().output_bytes,
        )?;
        let target_binding = super::binding_from_state(plan.target_state(), plan.target_grid())?;
        let (reopened, target_table_count) = verify_created_output(
            &rendered.header,
            &output_section,
            table_ordinal,
            &target_binding,
            &CreateOutputExpectation {
                request,
                source: &source,
                plan,
                limits,
            },
        )?;
        let receipt = TableCreateHwpxLoweringReceipt {
            profile_id: TABLE_CREATE_HWPX_PROFILE_ID,
            source_header_sha256: source.header_sha256,
            output_header_sha256: Sha256::digest(&rendered.header).into(),
            source_section_sha256: source.section_sha256,
            output_section_sha256: Sha256::digest(&output_section).into(),
            template_section_sha256: source.template_section_sha256,
            insertion_context_sha256: parse_digest(&source.insertion_context_sha256)?,
            target_state_sha256: plan.target_state().canonical_sha256(limits.ruling.ruling)?,
            target_grid_sha256: plan.target_grid().canonical_sha256()?,
            request_sha256: request.canonical_sha256(limits)?,
            plan_sha256: plan.canonical_sha256(limits)?,
            before_document_flow_sha256: parse_digest(&request.expected_document_flow_sha256)?,
            after_document_flow_sha256: parse_digest(&request.target_document_flow_sha256)?,
            source_table_count: source.source_table_count,
            target_table_count,
            target_rows: reopened.grid.rows(),
            target_columns: reopened.grid.columns(),
            created_master_cell_count: reopened.grid.master_cell_count(),
            payload_block_count: reopened.payload_block_count,
            formula_count: reopened.formula_count,
            added_border_fill_count: rendered.added_border_fill_count,
            page_split_preserved: true,
        };
        Ok(TableCreateHwpxLoweredParts {
            header: rendered.header,
            section: output_section,
            binding: target_binding,
            table_ordinal,
            receipt,
        })
    }
}

struct CreateOutputExpectation<'a> {
    request: &'a TableCreateHwpxRequest,
    source: &'a TableCreateHwpxReadback,
    plan: &'a TableCreateHwpxPlan,
    limits: TableCreateHwpxLimits,
}

fn verify_created_output(
    header: &[u8],
    section: &[u8],
    table_ordinal: usize,
    binding: &TableRulingHwpxBinding,
    expectation: &CreateOutputExpectation<'_>,
) -> Result<(TableRulingHwpxReadback, usize), TableCreateHwpxError> {
    let reopened = TableRulingHwpxReader::read_existing(
        header,
        section,
        table_ordinal,
        binding,
        expectation.limits.ruling,
    )?;
    let pagination = TablePaginationHwpxReader::read_in_section(
        section,
        table_ordinal,
        expectation.limits.pagination,
    )?;
    let target_table_count =
        TablePaginationHwpxReader::count_in_section(section, expectation.limits.pagination)?;
    if reopened.grid != *expectation.plan.target_grid()
        || reopened.state != *expectation.plan.target_state()
        || reopened.payload_block_count != 0
        || reopened.formula_count != 0
        || pagination.row_count != expectation.request.rows
        || pagination.column_count != expectation.request.columns
        || pagination.page_split != expectation.source.template_pagination.page_split
        || pagination.repeat_header_rows != 0
        || pagination.caption.is_some()
        || target_table_count != expectation.plan.target_table_count
    {
        return Err(TableCreateHwpxError::ReadbackMismatch);
    }
    Ok((reopened, target_table_count))
}

#[derive(Debug, Error)]
pub enum TableCreateHwpxError {
    #[error("unsupported table create HWPX schema version")]
    UnsupportedVersion,
    #[error("table create HWPX input exceeds a finite bound")]
    InputLimit,
    #[error("invalid table create HWPX JSON")]
    InvalidJson,
    #[error("invalid table create HWPX binding")]
    InvalidBinding,
    #[error("table create HWPX source, template, insertion or flow drifted")]
    SourceBindingMismatch,
    #[error("table create HWPX requires a distinct target document flow")]
    FlowBindingMismatch,
    #[error("table create HWPX table and cell identities conflict")]
    IdentityConflict,
    #[error("table create HWPX physical tracks are invalid")]
    InvalidTracks,
    #[error("table create HWPX template is not the exact blank 2x2 profile")]
    UnsupportedTemplateProfile,
    #[error("table create HWPX plan drifted")]
    PlanBindingMismatch,
    #[error("table create HWPX semantic readback mismatched")]
    ReadbackMismatch,
    #[error("table create HWPX serialization failed")]
    Serialization,
    #[error("table create HWPX output exceeds a finite bound")]
    OutputLimit,
    #[error(transparent)]
    Operation(#[from] TableOperationError),
    #[error(transparent)]
    Grid(#[from] TableGridError),
    #[error(transparent)]
    ModelRuling(#[from] TableRulingError),
    #[error(transparent)]
    Ruling(#[from] TableRulingHwpxError),
    #[error(transparent)]
    Pagination(#[from] TablePaginationHwpxError),
    #[error(transparent)]
    Xml(#[from] crate::preserving_xml::PreservingXmlError),
}

impl TableCreateHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::UnsupportedVersion => "table_create_hwpx_unsupported_version",
            Self::InputLimit => "table_create_hwpx_input_limit",
            Self::InvalidJson => "table_create_hwpx_invalid_json",
            Self::InvalidBinding => "table_create_hwpx_invalid_binding",
            Self::SourceBindingMismatch => "table_create_hwpx_source_binding_mismatch",
            Self::FlowBindingMismatch => "table_create_hwpx_flow_binding_mismatch",
            Self::IdentityConflict => "table_create_hwpx_identity_conflict",
            Self::InvalidTracks => "table_create_hwpx_invalid_tracks",
            Self::UnsupportedTemplateProfile => "table_create_hwpx_unsupported_template_profile",
            Self::PlanBindingMismatch => "table_create_hwpx_plan_binding_mismatch",
            Self::ReadbackMismatch => "table_create_hwpx_readback_mismatch",
            Self::Serialization => "table_create_hwpx_serialization",
            Self::OutputLimit => "table_create_hwpx_output_limit",
            Self::Operation(_) => "table_create_hwpx_operation",
            Self::Grid(_) => "table_create_hwpx_grid",
            Self::ModelRuling(_) => "table_create_hwpx_model_ruling",
            Self::Ruling(_) => "table_create_hwpx_ruling",
            Self::Pagination(_) => "table_create_hwpx_pagination",
            Self::Xml(_) => "table_create_hwpx_xml",
        }
    }
}

fn validate_request_source(
    request: &TableCreateHwpxRequest,
    source: &TableCreateHwpxReadback,
    current_document_flow_sha256: &str,
    limits: &TableCreateHwpxLimits,
) -> Result<(), TableCreateHwpxError> {
    require_digest(current_document_flow_sha256)?;
    require_template_profile(&source.template, &source.template_pagination)?;
    if source.profile_id != TABLE_CREATE_HWPX_PROFILE_ID
        || source.template.profile_id != super::TABLE_RULING_HWPX_PROFILE_ID
        || request.placeholder_paragraph_ordinal != source.placeholder_paragraph_ordinal
        || request.template_table_ordinal != source.template_table_ordinal
        || request.expected_header_sha256 != hex(source.header_sha256)
        || request.expected_section_sha256 != hex(source.section_sha256)
        || request.expected_template_section_sha256 != hex(source.template_section_sha256)
        || request.expected_template_state_sha256
            != hex(source
                .template
                .state
                .canonical_sha256(limits.ruling.ruling)?)
        || request.expected_template_grid_sha256 != hex(source.template.grid.canonical_sha256()?)
        || request.expected_insertion_context_sha256 != source.insertion_context_sha256
        || request.expected_document_flow_sha256 != current_document_flow_sha256
    {
        return Err(TableCreateHwpxError::SourceBindingMismatch);
    }
    if request.expected_document_flow_sha256 == request.target_document_flow_sha256 {
        return Err(TableCreateHwpxError::FlowBindingMismatch);
    }
    Ok(())
}

pub(super) fn require_template_profile(
    template: &TableRulingHwpxReadback,
    pagination: &TablePaginationHwpxReadback,
) -> Result<(), TableCreateHwpxError> {
    if template.grid.rows() != 2
        || template.grid.columns() != 2
        || template.grid.master_cell_count() != 4
        || template
            .grid
            .master_cells()
            .iter()
            .any(|cell| cell.row_span != 1 || cell.column_span != 1)
        || template.payload_block_count != 0
        || template.formula_count != 0
        || template
            .state
            .cells()
            .iter()
            .any(|cell| !cell.payload().is_empty() || cell.formula().is_some())
        || pagination.row_count != 2
        || pagination.column_count != 2
        || pagination.repeat_header_rows != 0
        || pagination.caption.is_some()
    {
        return Err(TableCreateHwpxError::UnsupportedTemplateProfile);
    }
    let first = template
        .state
        .cells()
        .first()
        .ok_or(TableCreateHwpxError::UnsupportedTemplateProfile)?;
    if template
        .state
        .cells()
        .iter()
        .any(|cell| cell.properties() != first.properties())
        || first.properties().slash_diagonal_sha256.is_some()
        || first.properties().back_slash_diagonal_sha256.is_some()
    {
        return Err(TableCreateHwpxError::UnsupportedTemplateProfile);
    }
    for (axis, boundary, count) in [
        (TableRulingAxis::Horizontal, 0, 2),
        (TableRulingAxis::Horizontal, 1, 2),
        (TableRulingAxis::Horizontal, 2, 2),
        (TableRulingAxis::Vertical, 0, 2),
        (TableRulingAxis::Vertical, 1, 2),
        (TableRulingAxis::Vertical, 2, 2),
    ] {
        let _ = uniform_edge(&template.state, axis, boundary, count)?;
    }
    Ok(())
}

fn validate_tracks(
    request: &TableCreateHwpxRequest,
    limits: &TableCreateHwpxLimits,
) -> Result<(), TableCreateHwpxError> {
    if request.row_heights_hwpunit.len() != usize::try_from(request.rows).unwrap_or(usize::MAX)
        || request.column_widths_hwpunit.len()
            != usize::try_from(request.columns).unwrap_or(usize::MAX)
        || request
            .row_heights_hwpunit
            .iter()
            .chain(&request.column_widths_hwpunit)
            .any(|value| *value == 0)
    {
        return Err(TableCreateHwpxError::InvalidTracks);
    }
    let _ = cumulative_boundaries(
        &request.row_heights_hwpunit,
        limits.ruling.ruling.config().dimension_hwpunit,
    )?;
    let _ = cumulative_boundaries(
        &request.column_widths_hwpunit,
        limits.ruling.ruling.config().dimension_hwpunit,
    )?;
    Ok(())
}

fn build_target_state(
    request: &TableCreateHwpxRequest,
    source: &TableCreateHwpxReadback,
    target_grid: &TableGrid,
    limits: &TableCreateHwpxLimits,
) -> Result<TableRulingState, TableCreateHwpxError> {
    build_created_state(
        &request.table_id,
        target_grid,
        &request.row_heights_hwpunit,
        &request.column_widths_hwpunit,
        &source.template,
        limits,
    )
}

pub(super) fn build_created_state(
    table_id: &LogicalId,
    target_grid: &TableGrid,
    row_heights_hwpunit: &[u32],
    column_widths_hwpunit: &[u32],
    template: &TableRulingHwpxReadback,
    limits: &TableCreateHwpxLimits,
) -> Result<TableRulingState, TableCreateHwpxError> {
    let row_boundaries = cumulative_boundaries(
        row_heights_hwpunit,
        limits.ruling.ruling.config().dimension_hwpunit,
    )?;
    let column_boundaries = cumulative_boundaries(
        column_widths_hwpunit,
        limits.ruling.ruling.config().dimension_hwpunit,
    )?;
    let properties = template
        .state
        .cells()
        .first()
        .ok_or(TableCreateHwpxError::UnsupportedTemplateProfile)?
        .properties()
        .clone();
    let cells = target_grid
        .master_cells()
        .iter()
        .map(|span| TableRulingCellDraft {
            master_cell_id: span.master_cell_id.clone(),
            coordinate: domain_ir::CellCoordinate {
                row: span.row,
                column: span.column,
            },
            payload: Vec::new(),
            properties: properties.clone(),
            formula: None,
        })
        .collect();
    let frame = template.state.frame();
    Ok(TableRulingState::from_draft(
        TableRulingStateDraft {
            schema_version: TABLE_RULING_SCHEMA_VERSION.to_owned(),
            table_id: table_id.clone(),
            frame: TableRulingFrame {
                left_hwpunit: frame.left_hwpunit,
                top_hwpunit: frame.top_hwpunit,
                width_hwpunit: *column_boundaries
                    .last()
                    .ok_or(TableCreateHwpxError::InvalidTracks)?,
                height_hwpunit: *row_boundaries
                    .last()
                    .ok_or(TableCreateHwpxError::InvalidTracks)?,
            },
            grid_sha256: hex(target_grid.canonical_sha256()?),
            table_properties_sha256: template.state.table_properties_sha256().to_owned(),
            row_boundaries_hwpunit: row_boundaries,
            column_boundaries_hwpunit: column_boundaries,
            edges: created_edges(&template.state, target_grid.rows(), target_grid.columns())?,
            cells,
        },
        target_grid,
        limits.ruling.formula,
        limits.ruling.ruling,
    )?)
}

fn cumulative_boundaries(tracks: &[u32], maximum: u32) -> Result<Vec<u32>, TableCreateHwpxError> {
    let mut output = Vec::new();
    output
        .try_reserve_exact(tracks.len().saturating_add(1))
        .map_err(|_| TableCreateHwpxError::OutputLimit)?;
    output.push(0);
    let mut cursor = 0_u32;
    for track in tracks {
        cursor = cursor
            .checked_add(*track)
            .filter(|value| *value <= maximum)
            .ok_or(TableCreateHwpxError::InvalidTracks)?;
        output.push(cursor);
    }
    Ok(output)
}

fn created_edges(
    template: &TableRulingState,
    rows: u32,
    columns: u32,
) -> Result<Vec<TableRulingEdge>, TableCreateHwpxError> {
    let top = uniform_edge(template, TableRulingAxis::Horizontal, 0, 2)?;
    let inner_horizontal = uniform_edge(template, TableRulingAxis::Horizontal, 1, 2)?;
    let bottom = uniform_edge(template, TableRulingAxis::Horizontal, 2, 2)?;
    let left = uniform_edge(template, TableRulingAxis::Vertical, 0, 2)?;
    let inner_vertical = uniform_edge(template, TableRulingAxis::Vertical, 1, 2)?;
    let right = uniform_edge(template, TableRulingAxis::Vertical, 2, 2)?;
    let edge_count = usize::try_from(rows.saturating_add(1))
        .ok()
        .and_then(|boundaries| {
            usize::try_from(columns)
                .ok()
                .and_then(|c| boundaries.checked_mul(c))
        })
        .and_then(|horizontal| {
            usize::try_from(columns.saturating_add(1))
                .ok()
                .and_then(|boundaries| {
                    usize::try_from(rows)
                        .ok()
                        .and_then(|r| boundaries.checked_mul(r))
                })
                .and_then(|vertical| horizontal.checked_add(vertical))
        })
        .ok_or(TableCreateHwpxError::OutputLimit)?;
    let mut output = Vec::new();
    output
        .try_reserve_exact(edge_count)
        .map_err(|_| TableCreateHwpxError::OutputLimit)?;
    for boundary in 0..=rows {
        let line = if boundary == 0 {
            &top
        } else if boundary == rows {
            &bottom
        } else {
            &inner_horizontal
        };
        for offset in 0..columns {
            output.push(TableRulingEdge {
                axis: TableRulingAxis::Horizontal,
                boundary,
                offset,
                line_sha256: line.clone(),
            });
        }
    }
    for boundary in 0..=columns {
        let line = if boundary == 0 {
            &left
        } else if boundary == columns {
            &right
        } else {
            &inner_vertical
        };
        for offset in 0..rows {
            output.push(TableRulingEdge {
                axis: TableRulingAxis::Vertical,
                boundary,
                offset,
                line_sha256: line.clone(),
            });
        }
    }
    Ok(output)
}

fn uniform_edge(
    state: &TableRulingState,
    axis: TableRulingAxis,
    boundary: u32,
    count: u32,
) -> Result<Option<String>, TableCreateHwpxError> {
    let first = state
        .edge(axis, boundary, 0)
        .ok_or(TableCreateHwpxError::UnsupportedTemplateProfile)?
        .line_sha256
        .clone();
    if (1..count).any(|offset| {
        state
            .edge(axis, boundary, offset)
            .is_none_or(|edge| edge.line_sha256 != first)
    }) {
        return Err(TableCreateHwpxError::UnsupportedTemplateProfile);
    }
    Ok(first)
}

fn serialized_limit(limits: &TableCreateHwpxLimits) -> usize {
    limits
        .ruling
        .grid
        .config()
        .serialized_bytes
        .min(limits.ruling.ruling.config().serialized_bytes)
}

fn serialize_bounded<T: Serialize + ?Sized>(
    value: &T,
    maximum: usize,
) -> Result<Vec<u8>, TableCreateHwpxError> {
    let bytes = serde_json::to_vec(value).map_err(|_| TableCreateHwpxError::Serialization)?;
    if bytes.len() > maximum {
        return Err(TableCreateHwpxError::OutputLimit);
    }
    Ok(bytes)
}

pub(super) fn reject_duplicate_json_keys(bytes: &[u8]) -> Result<(), TableCreateHwpxError> {
    struct Seed;
    struct Visitor;

    impl<'de> serde::de::DeserializeSeed<'de> for Seed {
        type Value = ();

        fn deserialize<D>(self, deserializer: D) -> Result<Self::Value, D::Error>
        where
            D: serde::Deserializer<'de>,
        {
            deserializer.deserialize_any(Visitor)
        }
    }

    impl<'de> serde::de::Visitor<'de> for Visitor {
        type Value = ();

        fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
            formatter.write_str("JSON without duplicate object keys")
        }

        fn visit_map<A>(self, mut map: A) -> Result<Self::Value, A::Error>
        where
            A: serde::de::MapAccess<'de>,
        {
            let mut keys = BTreeSet::new();
            while let Some(key) = map.next_key::<String>()? {
                if !keys.insert(key) {
                    return Err(serde::de::Error::custom("duplicate key"));
                }
                map.next_value_seed(Seed)?;
            }
            Ok(())
        }

        fn visit_seq<A>(self, mut sequence: A) -> Result<Self::Value, A::Error>
        where
            A: serde::de::SeqAccess<'de>,
        {
            while sequence.next_element_seed(Seed)?.is_some() {}
            Ok(())
        }

        fn visit_bool<E>(self, _value: bool) -> Result<Self::Value, E> {
            Ok(())
        }
        fn visit_i64<E>(self, _value: i64) -> Result<Self::Value, E> {
            Ok(())
        }
        fn visit_u64<E>(self, _value: u64) -> Result<Self::Value, E> {
            Ok(())
        }
        fn visit_f64<E>(self, _value: f64) -> Result<Self::Value, E> {
            Ok(())
        }
        fn visit_str<E>(self, _value: &str) -> Result<Self::Value, E> {
            Ok(())
        }
        fn visit_none<E>(self) -> Result<Self::Value, E> {
            Ok(())
        }
        fn visit_unit<E>(self) -> Result<Self::Value, E> {
            Ok(())
        }
    }

    let mut deserializer = serde_json::Deserializer::from_slice(bytes);
    serde::de::DeserializeSeed::deserialize(Seed, &mut deserializer)
        .map_err(|_| TableCreateHwpxError::InvalidJson)?;
    deserializer
        .end()
        .map_err(|_| TableCreateHwpxError::InvalidJson)
}

pub(super) fn require_digest(value: &str) -> Result<(), TableCreateHwpxError> {
    if value.len() != 64
        || value
            .bytes()
            .any(|byte| !byte.is_ascii_digit() && !(b'a'..=b'f').contains(&byte))
    {
        return Err(TableCreateHwpxError::InvalidBinding);
    }
    Ok(())
}

fn parse_digest(value: &str) -> Result<[u8; 32], TableCreateHwpxError> {
    require_digest(value)?;
    let mut output = [0_u8; 32];
    for (index, chunk) in value.as_bytes().chunks_exact(2).enumerate() {
        let text = std::str::from_utf8(chunk).map_err(|_| TableCreateHwpxError::InvalidBinding)?;
        output[index] =
            u8::from_str_radix(text, 16).map_err(|_| TableCreateHwpxError::InvalidBinding)?;
    }
    Ok(output)
}

pub(super) fn hex(value: impl AsRef<[u8]>) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let bytes = value.as_ref();
    let mut output = String::with_capacity(bytes.len().saturating_mul(2));
    for byte in bytes {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}
