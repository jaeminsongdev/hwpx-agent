use std::collections::BTreeSet;
use std::fmt;

use domain_ir::{
    LogicalId, TABLE_RULING_SCHEMA_VERSION, TABLE_TEXT_CONVERSION_SCHEMA_VERSION, TableDelimiter,
    TableGrid, TableOperationError, TableOperationReceipt, TableRulingCellDraft, TableRulingError,
    TableRulingPayloadBlock, TableRulingState, TableRulingStateDraft, TableTextConversionError,
    TableTextConversionLimits, TableTextGrid, TableTextGridDraft,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use super::create_hwpx::{self, TableCreateHwpxError, TableCreateHwpxLimits, build_created_state};
use super::{
    RawEdit, TableRulingHwpxBinding, TableRulingHwpxError, TableRulingHwpxReadback,
    TableRulingHwpxReader,
};
use crate::preserving_xml::PreservingXmlDocument;
use crate::{
    HANCOM_2020_PARAGRAPH_NAMESPACE, ParagraphChild, TablePaginationHwpxError,
    TablePaginationHwpxReadback, TablePaginationHwpxReader, TextAtom, TextFlow, TextFlowError,
    TextFlowLimits, TextFlowReader, TextFlowWriter, TextParagraphProperties, TextRun, TextRunItem,
    TextSpan,
};

pub const TABLE_TEXT_TO_TABLE_HWPX_SCHEMA_VERSION: &str = "hwpx-agent.table-text-to-table-hwpx/v1";
pub const TABLE_TEXT_TO_TABLE_HWPX_PROFILE_ID: &str =
    "hwpx-agent.table-text-to-table-hwpx.hancom-2020-template/1";
const XML_DECLARATION: &[u8] = b"<?xml version=\"1.0\" encoding=\"UTF-8\"?>";

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TableTextToTableHwpxLimits {
    pub create: TableCreateHwpxLimits,
    pub text: TableTextConversionLimits,
    pub flow: TextFlowLimits,
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableTextToTableHwpxReadback {
    pub profile_id: &'static str,
    pub paragraph_ordinal: usize,
    pub template_table_ordinal: usize,
    pub delimiter: TableDelimiter,
    pub header_sha256: [u8; 32],
    pub section_sha256: [u8; 32],
    pub template_section_sha256: [u8; 32],
    pub paragraph_sha256: [u8; 32],
    pub paragraph_context_sha256: String,
    pub source_table_count: usize,
    pub text_grid: TableTextGrid,
    pub template: TableRulingHwpxReadback,
    pub template_pagination: TablePaginationHwpxReadback,
}

impl fmt::Debug for TableTextToTableHwpxReadback {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableTextToTableHwpxReadback")
            .field("profile_id", &self.profile_id)
            .field("paragraph_ordinal", &self.paragraph_ordinal)
            .field("template_table_ordinal", &self.template_table_ordinal)
            .field("delimiter", &self.delimiter)
            .field("source_table_count", &self.source_table_count)
            .field("rows", &self.text_grid.row_count())
            .field("columns", &self.text_grid.column_count())
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct TableTextToTableHwpxReader;

impl TableTextToTableHwpxReader {
    /// Reads one complete top-level text paragraph and one exact blank 2x2 table template.
    ///
    /// # Errors
    ///
    /// Rejects malformed, opaque, empty, nonrectangular, ambiguous, formula-bearing or over-limit
    /// source/template input.
    #[allow(clippy::too_many_arguments)]
    pub fn read_context(
        header: &[u8],
        section: &[u8],
        paragraph_ordinal: usize,
        delimiter: TableDelimiter,
        template_section: &[u8],
        template_table_ordinal: usize,
        template_binding: &TableRulingHwpxBinding,
        limits: TableTextToTableHwpxLimits,
    ) -> Result<TableTextToTableHwpxReadback, TableTextToTableHwpxError> {
        let document = PreservingXmlDocument::parse(section)?;
        let paragraph = selected_top_level_paragraph(&document, paragraph_ordinal)?;
        let paragraph_bytes = super::element_bytes(section, super::element(&document, paragraph)?)?;
        let standalone = standalone_paragraph(paragraph_bytes)?;
        let flow = TextFlowReader::read(&standalone, limits.flow)?;
        require_plain_text_flow(&flow)?;
        let visible = flow.visible_text_nfc()?;
        let text_grid = TableTextGrid::parse_delimited(visible.as_bytes(), delimiter, limits.text)?;
        let template = TableRulingHwpxReader::read_existing(
            header,
            template_section,
            template_table_ordinal,
            template_binding,
            limits.create.ruling,
        )?;
        let template_pagination = TablePaginationHwpxReader::read_in_section(
            template_section,
            template_table_ordinal,
            limits.create.pagination,
        )?;
        create_hwpx::require_template_profile(&template, &template_pagination)?;
        create_hwpx::require_native_template_wrapper(template_section, template_table_ordinal)?;
        require_canonical_blank_template(
            template_section,
            template_table_ordinal,
            &template,
            &limits,
        )?;
        let _ = super::insertion_wrapper(template_section, template_table_ordinal)?;
        let paragraph_sha256 = Sha256::digest(paragraph_bytes).into();
        let paragraph_context_sha256 = paragraph_context_digest(
            section,
            paragraph_ordinal,
            paragraph_sha256,
            delimiter,
            &text_grid,
            limits.text,
        )?;
        Ok(TableTextToTableHwpxReadback {
            profile_id: TABLE_TEXT_TO_TABLE_HWPX_PROFILE_ID,
            paragraph_ordinal,
            template_table_ordinal,
            delimiter,
            header_sha256: Sha256::digest(header).into(),
            section_sha256: Sha256::digest(section).into(),
            template_section_sha256: Sha256::digest(template_section).into(),
            paragraph_sha256,
            paragraph_context_sha256,
            source_table_count: TablePaginationHwpxReader::count_in_section(
                section,
                limits.create.pagination,
            )?,
            text_grid,
            template,
            template_pagination,
        })
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableTextToTableHwpxRequestDraft {
    pub schema_version: String,
    pub paragraph_ordinal: usize,
    pub template_table_ordinal: usize,
    pub delimiter: TableDelimiter,
    pub expected_header_sha256: String,
    pub expected_section_sha256: String,
    pub expected_template_section_sha256: String,
    pub expected_template_state_sha256: String,
    pub expected_template_grid_sha256: String,
    pub expected_paragraph_sha256: String,
    pub expected_paragraph_context_sha256: String,
    pub expected_text_grid_sha256: String,
    pub expected_document_flow_sha256: String,
    pub target_document_flow_sha256: String,
    pub table_id: LogicalId,
    pub master_cell_ids: Vec<LogicalId>,
    pub payload_block_ids: Vec<Option<LogicalId>>,
    pub row_heights_hwpunit: Vec<u32>,
    pub column_widths_hwpunit: Vec<u32>,
}

impl fmt::Debug for TableTextToTableHwpxRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableTextToTableHwpxRequestDraft")
            .field("schema_version", &self.schema_version)
            .field("paragraph_ordinal", &self.paragraph_ordinal)
            .field("template_table_ordinal", &self.template_table_ordinal)
            .field("delimiter", &self.delimiter)
            .field("master_cell_count", &self.master_cell_ids.len())
            .field("payload_identity_slots", &self.payload_block_ids.len())
            .field("row_track_count", &self.row_heights_hwpunit.len())
            .field("column_track_count", &self.column_widths_hwpunit.len())
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableTextToTableHwpxRequest {
    schema_version: &'static str,
    capability_id: &'static str,
    paragraph_ordinal: usize,
    template_table_ordinal: usize,
    delimiter: TableDelimiter,
    expected_header_sha256: String,
    expected_section_sha256: String,
    expected_template_section_sha256: String,
    expected_template_state_sha256: String,
    expected_template_grid_sha256: String,
    expected_paragraph_sha256: String,
    expected_paragraph_context_sha256: String,
    expected_text_grid_sha256: String,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    table_id: LogicalId,
    master_cell_ids: Vec<LogicalId>,
    payload_block_ids: Vec<Option<LogicalId>>,
    row_heights_hwpunit: Vec<u32>,
    column_widths_hwpunit: Vec<u32>,
}

impl TableTextToTableHwpxRequest {
    /// Binds a complete semantic text grid and all native construction inputs to exact source state.
    ///
    /// # Errors
    ///
    /// Rejects schema, digest, source, identity, geometry, flow or finite-limit drift.
    pub fn from_draft(
        draft: TableTextToTableHwpxRequestDraft,
        source: &TableTextToTableHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableTextToTableHwpxLimits,
    ) -> Result<Self, TableTextToTableHwpxError> {
        if draft.schema_version != TABLE_TEXT_TO_TABLE_HWPX_SCHEMA_VERSION {
            return Err(TableTextToTableHwpxError::UnsupportedVersion);
        }
        for digest in [
            &draft.expected_header_sha256,
            &draft.expected_section_sha256,
            &draft.expected_template_section_sha256,
            &draft.expected_template_state_sha256,
            &draft.expected_template_grid_sha256,
            &draft.expected_paragraph_sha256,
            &draft.expected_paragraph_context_sha256,
            &draft.expected_text_grid_sha256,
            &draft.expected_document_flow_sha256,
            &draft.target_document_flow_sha256,
            current_document_flow_sha256,
        ] {
            create_hwpx::require_digest(digest)?;
        }
        let request = Self {
            schema_version: TABLE_TEXT_TO_TABLE_HWPX_SCHEMA_VERSION,
            capability_id: "table.text_to_table",
            paragraph_ordinal: draft.paragraph_ordinal,
            template_table_ordinal: draft.template_table_ordinal,
            delimiter: draft.delimiter,
            expected_header_sha256: draft.expected_header_sha256,
            expected_section_sha256: draft.expected_section_sha256,
            expected_template_section_sha256: draft.expected_template_section_sha256,
            expected_template_state_sha256: draft.expected_template_state_sha256,
            expected_template_grid_sha256: draft.expected_template_grid_sha256,
            expected_paragraph_sha256: draft.expected_paragraph_sha256,
            expected_paragraph_context_sha256: draft.expected_paragraph_context_sha256,
            expected_text_grid_sha256: draft.expected_text_grid_sha256,
            expected_document_flow_sha256: draft.expected_document_flow_sha256,
            target_document_flow_sha256: draft.target_document_flow_sha256,
            table_id: draft.table_id,
            master_cell_ids: draft.master_cell_ids,
            payload_block_ids: draft.payload_block_ids,
            row_heights_hwpunit: draft.row_heights_hwpunit,
            column_widths_hwpunit: draft.column_widths_hwpunit,
        };
        validate_request_source(&request, source, current_document_flow_sha256, &limits)?;
        let _ = TableTextToTableHwpxBuilder::build(
            &request,
            source,
            current_document_flow_sha256,
            limits,
        )?;
        let _ = request.canonical_json(limits)?;
        Ok(request)
    }

    /// Parses strict bounded JSON and applies identical semantic admission.
    ///
    /// # Errors
    ///
    /// Rejects empty, oversized, malformed, duplicate, unknown or invalid input.
    pub fn from_json(
        bytes: &[u8],
        source: &TableTextToTableHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableTextToTableHwpxLimits,
    ) -> Result<Self, TableTextToTableHwpxError> {
        if bytes.is_empty() || bytes.len() > serialized_limit(&limits) {
            return Err(TableTextToTableHwpxError::InputLimit);
        }
        create_hwpx::reject_duplicate_json_keys(bytes)
            .map_err(|_| TableTextToTableHwpxError::InvalidJson)?;
        let draft =
            serde_json::from_slice(bytes).map_err(|_| TableTextToTableHwpxError::InvalidJson)?;
        Self::from_draft(draft, source, current_document_flow_sha256, limits)
    }

    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
    }

    #[must_use]
    pub fn target_document_flow_sha256(&self) -> &str {
        &self.target_document_flow_sha256
    }

    /// Serializes the complete typed request under every configured bound.
    ///
    /// # Errors
    ///
    /// Rejects serialization or finite output failure.
    pub fn canonical_json(
        &self,
        limits: TableTextToTableHwpxLimits,
    ) -> Result<Vec<u8>, TableTextToTableHwpxError> {
        serialize_bounded(self, serialized_limit(&limits))
    }

    /// Hashes the bounded canonical request.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failure.
    pub fn canonical_sha256(
        &self,
        limits: TableTextToTableHwpxLimits,
    ) -> Result<[u8; 32], TableTextToTableHwpxError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TableTextToTableHwpxRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableTextToTableHwpxRequest")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("paragraph_ordinal", &self.paragraph_ordinal)
            .field("template_table_ordinal", &self.template_table_ordinal)
            .field("delimiter", &self.delimiter)
            .field("master_cell_count", &self.master_cell_ids.len())
            .field("payload_identity_slots", &self.payload_block_ids.len())
            .field("row_track_count", &self.row_heights_hwpunit.len())
            .field("column_track_count", &self.column_widths_hwpunit.len())
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableTextToTableHwpxPlan {
    schema_version: &'static str,
    capability_id: &'static str,
    request_sha256: String,
    source_table_count: usize,
    target_table_count: usize,
    source_header_sha256: String,
    source_section_sha256: String,
    template_section_sha256: String,
    paragraph_context_sha256: String,
    text_grid_sha256: String,
    target_state_sha256: String,
    target_grid_sha256: String,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    operation_receipt: TableOperationReceipt,
    target_state: TableRulingState,
    #[serde(skip)]
    target_grid: TableGrid,
}

impl TableTextToTableHwpxPlan {
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
        limits: TableTextToTableHwpxLimits,
    ) -> Result<Vec<u8>, TableTextToTableHwpxError> {
        serialize_bounded(self, serialized_limit(&limits))
    }

    /// Hashes the bounded canonical plan.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failure.
    pub fn canonical_sha256(
        &self,
        limits: TableTextToTableHwpxLimits,
    ) -> Result<[u8; 32], TableTextToTableHwpxError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TableTextToTableHwpxPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableTextToTableHwpxPlan")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("source_table_count", &self.source_table_count)
            .field("target_table_count", &self.target_table_count)
            .field("target_rows", &self.target_grid.rows())
            .field("target_columns", &self.target_grid.columns())
            .field("operation_receipt", &self.operation_receipt)
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct TableTextToTableHwpxBuilder;

impl TableTextToTableHwpxBuilder {
    /// Revalidates the source and builds an exact table state including generated cell payloads.
    ///
    /// # Errors
    ///
    /// Rejects source, flow, identity, geometry, template, grid, payload, state or bound drift.
    pub fn build(
        request: &TableTextToTableHwpxRequest,
        source: &TableTextToTableHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableTextToTableHwpxLimits,
    ) -> Result<TableTextToTableHwpxPlan, TableTextToTableHwpxError> {
        validate_request_source(request, source, current_document_flow_sha256, &limits)?;
        validate_geometry_and_identities(request, source)?;
        let rows = u32::try_from(source.text_grid.row_count())
            .map_err(|_| TableTextToTableHwpxError::Geometry)?;
        let columns = u32::try_from(source.text_grid.column_count())
            .map_err(|_| TableTextToTableHwpxError::Geometry)?;
        let result = TableGrid::create_unmerged(
            rows,
            columns,
            request.master_cell_ids.clone(),
            limits.create.ruling.grid,
        )?;
        let (target_grid, operation_receipt) = result.into_parts();
        let blank_state = build_created_state(
            &request.table_id,
            &target_grid,
            &request.row_heights_hwpunit,
            &request.column_widths_hwpunit,
            &source.template,
            &limits.create,
        )?;
        let target_state = state_with_text_payloads(
            &blank_state,
            &target_grid,
            &source.text_grid,
            &request.payload_block_ids,
            &limits,
        )?;
        let target_table_count = source
            .source_table_count
            .checked_add(1)
            .ok_or(TableTextToTableHwpxError::OutputLimit)?;
        let plan = TableTextToTableHwpxPlan {
            schema_version: TABLE_TEXT_TO_TABLE_HWPX_SCHEMA_VERSION,
            capability_id: request.capability_id,
            request_sha256: create_hwpx::hex(request.canonical_sha256(limits)?),
            source_table_count: source.source_table_count,
            target_table_count,
            source_header_sha256: create_hwpx::hex(source.header_sha256),
            source_section_sha256: create_hwpx::hex(source.section_sha256),
            template_section_sha256: create_hwpx::hex(source.template_section_sha256),
            paragraph_context_sha256: source.paragraph_context_sha256.clone(),
            text_grid_sha256: create_hwpx::hex(source.text_grid.canonical_sha256(limits.text)?),
            target_state_sha256: create_hwpx::hex(
                target_state.canonical_sha256(limits.create.ruling.ruling)?,
            ),
            target_grid_sha256: create_hwpx::hex(target_grid.canonical_sha256()?),
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
pub struct TableTextToTableHwpxLoweringReceipt {
    pub profile_id: &'static str,
    pub source_header_sha256: [u8; 32],
    pub output_header_sha256: [u8; 32],
    pub source_section_sha256: [u8; 32],
    pub output_section_sha256: [u8; 32],
    pub template_section_sha256: [u8; 32],
    pub paragraph_context_sha256: [u8; 32],
    pub text_grid_sha256: [u8; 32],
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
    pub nonempty_cell_count: usize,
    pub payload_block_count: usize,
    pub formula_count: usize,
    pub added_border_fill_count: usize,
    pub page_split_preserved: bool,
}

impl fmt::Debug for TableTextToTableHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableTextToTableHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field("source_table_count", &self.source_table_count)
            .field("target_table_count", &self.target_table_count)
            .field("target_rows", &self.target_rows)
            .field("target_columns", &self.target_columns)
            .field("nonempty_cell_count", &self.nonempty_cell_count)
            .field("payload_block_count", &self.payload_block_count)
            .field("formula_count", &self.formula_count)
            .field("added_border_fill_count", &self.added_border_fill_count)
            .field("page_split_preserved", &self.page_split_preserved)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableTextToTableHwpxLoweredParts {
    pub header: Vec<u8>,
    pub section: Vec<u8>,
    pub binding: TableRulingHwpxBinding,
    pub table_ordinal: usize,
    pub receipt: TableTextToTableHwpxLoweringReceipt,
}

struct VerifiedTextToTableLowering {
    header: Vec<u8>,
    section: Vec<u8>,
    binding: TableRulingHwpxBinding,
    table_ordinal: usize,
    reopened: TableRulingHwpxReadback,
    target_table_count: usize,
    added_border_fill_count: usize,
}

impl fmt::Debug for TableTextToTableHwpxLoweredParts {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableTextToTableHwpxLoweredParts")
            .field("header_bytes", &self.header.len())
            .field("section_bytes", &self.section.len())
            .field("table_ordinal", &self.table_ordinal)
            .field("receipt", &self.receipt)
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct TableTextToTableHwpxLowerer;

impl TableTextToTableHwpxLowerer {
    /// Converts one bound text paragraph to a template-derived table and returns only after reopen.
    ///
    /// # Errors
    ///
    /// Rejects source, template, request, plan, state, grid, flow, payload, pagination or readback
    /// drift without returning partial output.
    #[allow(clippy::too_many_arguments)]
    pub fn lower(
        header: &[u8],
        section: &[u8],
        template_section: &[u8],
        template_binding: &TableRulingHwpxBinding,
        current_document_flow_sha256: &str,
        request: &TableTextToTableHwpxRequest,
        plan: &TableTextToTableHwpxPlan,
        limits: TableTextToTableHwpxLimits,
    ) -> Result<TableTextToTableHwpxLoweredParts, TableTextToTableHwpxError> {
        let source = TableTextToTableHwpxReader::read_context(
            header,
            section,
            request.paragraph_ordinal,
            request.delimiter,
            template_section,
            request.template_table_ordinal,
            template_binding,
            limits,
        )?;
        validate_request_source(request, &source, current_document_flow_sha256, &limits)?;
        let rebuilt = TableTextToTableHwpxBuilder::build(
            request,
            &source,
            current_document_flow_sha256,
            limits,
        )?;
        if rebuilt != *plan {
            return Err(TableTextToTableHwpxError::PlanBindingMismatch);
        }
        let verified = execute_and_verify_text_to_table(
            header,
            section,
            template_section,
            template_binding,
            request,
            plan,
            &source,
            &limits,
        )?;
        let receipt = TableTextToTableHwpxLoweringReceipt {
            profile_id: TABLE_TEXT_TO_TABLE_HWPX_PROFILE_ID,
            source_header_sha256: source.header_sha256,
            output_header_sha256: Sha256::digest(&verified.header).into(),
            source_section_sha256: source.section_sha256,
            output_section_sha256: Sha256::digest(&verified.section).into(),
            template_section_sha256: source.template_section_sha256,
            paragraph_context_sha256: parse_digest(&source.paragraph_context_sha256)?,
            text_grid_sha256: source.text_grid.canonical_sha256(limits.text)?,
            target_state_sha256: plan
                .target_state()
                .canonical_sha256(limits.create.ruling.ruling)?,
            target_grid_sha256: plan.target_grid().canonical_sha256()?,
            request_sha256: request.canonical_sha256(limits)?,
            plan_sha256: plan.canonical_sha256(limits)?,
            before_document_flow_sha256: parse_digest(&request.expected_document_flow_sha256)?,
            after_document_flow_sha256: parse_digest(&request.target_document_flow_sha256)?,
            source_table_count: source.source_table_count,
            target_table_count: verified.target_table_count,
            target_rows: verified.reopened.grid.rows(),
            target_columns: verified.reopened.grid.columns(),
            nonempty_cell_count: nonempty_cell_count(&source.text_grid),
            payload_block_count: verified.reopened.payload_block_count,
            formula_count: verified.reopened.formula_count,
            added_border_fill_count: verified.added_border_fill_count,
            page_split_preserved: true,
        };
        Ok(TableTextToTableHwpxLoweredParts {
            header: verified.header,
            section: verified.section,
            binding: verified.binding,
            table_ordinal: verified.table_ordinal,
            receipt,
        })
    }
}

#[allow(clippy::too_many_arguments)]
fn execute_and_verify_text_to_table(
    header: &[u8],
    section: &[u8],
    template_section: &[u8],
    template_binding: &TableRulingHwpxBinding,
    request: &TableTextToTableHwpxRequest,
    plan: &TableTextToTableHwpxPlan,
    source: &TableTextToTableHwpxReadback,
    limits: &TableTextToTableHwpxLimits,
) -> Result<VerifiedTextToTableLowering, TableTextToTableHwpxError> {
    let blank_state = state_without_payloads(plan.target_state(), plan.target_grid(), limits)?;
    let rendered = super::render_create_from_template(
        header,
        template_section,
        request.template_table_ordinal,
        template_binding,
        &source.template.state,
        &blank_state,
        plan.target_grid(),
        &limits.create.ruling,
    )?;
    let native_section = create_hwpx::require_native_created_cell_scaffolds(
        &rendered.section,
        request.template_table_ordinal,
        plan.target_grid().master_cell_count(),
        limits.create.ruling.layout.config().output_bytes,
    )?;
    let payload_section = patch_target_cell_text(
        &native_section,
        request.template_table_ordinal,
        plan.target_grid(),
        &source.text_grid,
        limits,
    )?;
    let wrapper = super::insertion_wrapper(&payload_section, request.template_table_ordinal)?;
    super::ensure_native_table_id_available(
        section,
        &payload_section,
        request.template_table_ordinal,
    )?;
    let document = PreservingXmlDocument::parse(section)?;
    let paragraph = selected_top_level_paragraph(&document, request.paragraph_ordinal)?;
    let paragraph_span = super::element(&document, paragraph)?
        .outer_span()
        .ok_or(TableTextToTableHwpxError::ReadbackMismatch)?;
    let table_ordinal = super::tables_before_offset(&document, paragraph_span.start());
    let mut edits = vec![RawEdit {
        start: paragraph_span.start(),
        end: paragraph_span.end(),
        replacement: wrapper,
    }];
    let output_section = super::apply_edits(
        section,
        &mut edits,
        limits.create.ruling.layout.config().output_bytes,
    )?;
    let binding = super::binding_from_state(plan.target_state(), plan.target_grid())?;
    let reopened = TableRulingHwpxReader::read_existing(
        &rendered.header,
        &output_section,
        table_ordinal,
        &binding,
        limits.create.ruling,
    )?;
    let pagination = TablePaginationHwpxReader::read_in_section(
        &output_section,
        table_ordinal,
        limits.create.pagination,
    )?;
    let reopened_text =
        read_unmerged_text_grid(&output_section, table_ordinal, plan.target_grid(), limits)?;
    let target_table_count =
        TablePaginationHwpxReader::count_in_section(&output_section, limits.create.pagination)?;
    if reopened.grid != *plan.target_grid()
        || reopened.state != *plan.target_state()
        || reopened.formula_count != 0
        || reopened.payload_block_count != nonempty_cell_count(&source.text_grid)
        || reopened_text != source.text_grid
        || pagination.page_split != source.template_pagination.page_split
        || pagination.repeat_header_rows != 0
        || pagination.caption.is_some()
        || target_table_count != plan.target_table_count
    {
        return Err(TableTextToTableHwpxError::ReadbackMismatch);
    }
    Ok(VerifiedTextToTableLowering {
        header: rendered.header,
        section: output_section,
        binding,
        table_ordinal,
        reopened,
        target_table_count,
        added_border_fill_count: rendered.added_border_fill_count,
    })
}

#[derive(Debug, Error)]
pub enum TableTextToTableHwpxError {
    #[error("unsupported text-to-table HWPX schema version")]
    UnsupportedVersion,
    #[error("text-to-table HWPX input exceeds a finite bound")]
    InputLimit,
    #[error("invalid text-to-table HWPX JSON")]
    InvalidJson,
    #[error("text-to-table HWPX source, template, paragraph or flow drifted")]
    SourceBindingMismatch,
    #[error("text-to-table HWPX requires a distinct target document flow")]
    FlowBindingMismatch,
    #[error("text-to-table HWPX dimensions or physical tracks are invalid")]
    Geometry,
    #[error("text-to-table HWPX logical identities are invalid or collide")]
    IdentityConflict,
    #[error("text-to-table HWPX plan drifted")]
    PlanBindingMismatch,
    #[error("text-to-table HWPX semantic readback mismatched")]
    ReadbackMismatch,
    #[error("text-to-table HWPX serialization failed")]
    Serialization,
    #[error("text-to-table HWPX output exceeds a finite bound")]
    OutputLimit,
    #[error(transparent)]
    Create(#[from] TableCreateHwpxError),
    #[error(transparent)]
    Operation(#[from] TableOperationError),
    #[error(transparent)]
    Grid(#[from] domain_ir::TableGridError),
    #[error(transparent)]
    RulingModel(#[from] TableRulingError),
    #[error(transparent)]
    TextModel(#[from] TableTextConversionError),
    #[error(transparent)]
    TextFlow(#[from] TextFlowError),
    #[error(transparent)]
    Ruling(#[from] TableRulingHwpxError),
    #[error(transparent)]
    Pagination(#[from] TablePaginationHwpxError),
    #[error(transparent)]
    Xml(#[from] crate::preserving_xml::PreservingXmlError),
}

impl TableTextToTableHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::UnsupportedVersion => "table_text_to_table_hwpx_unsupported_version",
            Self::InputLimit => "table_text_to_table_hwpx_input_limit",
            Self::InvalidJson => "table_text_to_table_hwpx_invalid_json",
            Self::SourceBindingMismatch => "table_text_to_table_hwpx_source_binding_mismatch",
            Self::FlowBindingMismatch => "table_text_to_table_hwpx_flow_binding_mismatch",
            Self::Geometry => "table_text_to_table_hwpx_geometry",
            Self::IdentityConflict => "table_text_to_table_hwpx_identity_conflict",
            Self::PlanBindingMismatch => "table_text_to_table_hwpx_plan_binding_mismatch",
            Self::ReadbackMismatch => "table_text_to_table_hwpx_readback_mismatch",
            Self::Serialization => "table_text_to_table_hwpx_serialization",
            Self::OutputLimit => "table_text_to_table_hwpx_output_limit",
            Self::Create(_) => "table_text_to_table_hwpx_create",
            Self::Operation(_) => "table_text_to_table_hwpx_operation",
            Self::Grid(_) => "table_text_to_table_hwpx_grid",
            Self::RulingModel(_) => "table_text_to_table_hwpx_ruling_model",
            Self::TextModel(_) => "table_text_to_table_hwpx_text_model",
            Self::TextFlow(_) => "table_text_to_table_hwpx_text_flow",
            Self::Ruling(_) => "table_text_to_table_hwpx_ruling",
            Self::Pagination(_) => "table_text_to_table_hwpx_pagination",
            Self::Xml(_) => "table_text_to_table_hwpx_xml",
        }
    }
}

fn validate_request_source(
    request: &TableTextToTableHwpxRequest,
    source: &TableTextToTableHwpxReadback,
    current_document_flow_sha256: &str,
    limits: &TableTextToTableHwpxLimits,
) -> Result<(), TableTextToTableHwpxError> {
    create_hwpx::require_digest(current_document_flow_sha256)?;
    create_hwpx::require_template_profile(&source.template, &source.template_pagination)?;
    if source.profile_id != TABLE_TEXT_TO_TABLE_HWPX_PROFILE_ID
        || source.template.profile_id != super::TABLE_RULING_HWPX_PROFILE_ID
        || request.paragraph_ordinal != source.paragraph_ordinal
        || request.template_table_ordinal != source.template_table_ordinal
        || request.delimiter != source.delimiter
        || request.expected_header_sha256 != create_hwpx::hex(source.header_sha256)
        || request.expected_section_sha256 != create_hwpx::hex(source.section_sha256)
        || request.expected_template_section_sha256
            != create_hwpx::hex(source.template_section_sha256)
        || request.expected_template_state_sha256
            != create_hwpx::hex(
                source
                    .template
                    .state
                    .canonical_sha256(limits.create.ruling.ruling)?,
            )
        || request.expected_template_grid_sha256
            != create_hwpx::hex(source.template.grid.canonical_sha256()?)
        || request.expected_paragraph_sha256 != create_hwpx::hex(source.paragraph_sha256)
        || request.expected_paragraph_context_sha256 != source.paragraph_context_sha256
        || request.expected_text_grid_sha256
            != create_hwpx::hex(source.text_grid.canonical_sha256(limits.text)?)
        || request.expected_document_flow_sha256 != current_document_flow_sha256
    {
        return Err(TableTextToTableHwpxError::SourceBindingMismatch);
    }
    if request.expected_document_flow_sha256 == request.target_document_flow_sha256 {
        return Err(TableTextToTableHwpxError::FlowBindingMismatch);
    }
    Ok(())
}

fn validate_geometry_and_identities(
    request: &TableTextToTableHwpxRequest,
    source: &TableTextToTableHwpxReadback,
) -> Result<(), TableTextToTableHwpxError> {
    let rows = source.text_grid.row_count();
    let columns = source.text_grid.column_count();
    let cells = rows
        .checked_mul(columns)
        .ok_or(TableTextToTableHwpxError::Geometry)?;
    if request.master_cell_ids.len() != cells
        || request.payload_block_ids.len() != cells
        || request.row_heights_hwpunit.len() != rows
        || request.column_widths_hwpunit.len() != columns
        || request
            .row_heights_hwpunit
            .iter()
            .chain(&request.column_widths_hwpunit)
            .any(|value| *value == 0)
    {
        return Err(TableTextToTableHwpxError::Geometry);
    }
    let mut identities = BTreeSet::new();
    if !identities.insert(request.table_id.clone()) {
        return Err(TableTextToTableHwpxError::IdentityConflict);
    }
    for id in &request.master_cell_ids {
        if !identities.insert(id.clone()) {
            return Err(TableTextToTableHwpxError::IdentityConflict);
        }
    }
    for (index, id) in request.payload_block_ids.iter().enumerate() {
        let row = index / columns;
        let column = index % columns;
        let nonempty = source
            .text_grid
            .cell(row, column)
            .is_some_and(|value| !value.is_empty());
        if nonempty != id.is_some()
            || id
                .as_ref()
                .is_some_and(|value| !identities.insert(value.clone()))
        {
            return Err(TableTextToTableHwpxError::IdentityConflict);
        }
    }
    Ok(())
}

fn state_with_text_payloads(
    blank: &TableRulingState,
    grid: &TableGrid,
    text_grid: &TableTextGrid,
    payload_ids: &[Option<LogicalId>],
    limits: &TableTextToTableHwpxLimits,
) -> Result<TableRulingState, TableTextToTableHwpxError> {
    let columns = text_grid.column_count();
    let mut cells = Vec::new();
    cells
        .try_reserve_exact(blank.cells().len())
        .map_err(|_| TableTextToTableHwpxError::OutputLimit)?;
    for cell in blank.cells() {
        let coordinate = cell.coordinate();
        let index = usize::try_from(coordinate.row)
            .ok()
            .and_then(|row| row.checked_mul(columns))
            .and_then(|base| {
                usize::try_from(coordinate.column)
                    .ok()
                    .and_then(|column| base.checked_add(column))
            })
            .ok_or(TableTextToTableHwpxError::Geometry)?;
        let text = text_grid
            .cell(
                usize::try_from(coordinate.row).map_err(|_| TableTextToTableHwpxError::Geometry)?,
                usize::try_from(coordinate.column)
                    .map_err(|_| TableTextToTableHwpxError::Geometry)?,
            )
            .ok_or(TableTextToTableHwpxError::Geometry)?;
        let payload = match payload_ids
            .get(index)
            .ok_or(TableTextToTableHwpxError::IdentityConflict)?
        {
            Some(id) => vec![TableRulingPayloadBlock {
                block_id: id.clone(),
                payload_sha256: create_hwpx::hex(Sha256::digest(native_text_paragraph(
                    text,
                    limits.flow,
                )?)),
            }],
            None if text.is_empty() => Vec::new(),
            None => return Err(TableTextToTableHwpxError::IdentityConflict),
        };
        cells.push(TableRulingCellDraft {
            master_cell_id: cell.master_cell_id().clone(),
            coordinate,
            payload,
            properties: cell.properties().clone(),
            formula: None,
        });
    }
    Ok(TableRulingState::from_draft(
        TableRulingStateDraft {
            schema_version: TABLE_RULING_SCHEMA_VERSION.to_owned(),
            table_id: blank.table_id().clone(),
            frame: blank.frame(),
            grid_sha256: blank.grid_sha256().to_owned(),
            table_properties_sha256: blank.table_properties_sha256().to_owned(),
            row_boundaries_hwpunit: blank.row_boundaries_hwpunit().to_vec(),
            column_boundaries_hwpunit: blank.column_boundaries_hwpunit().to_vec(),
            edges: blank.edges().to_vec(),
            cells,
        },
        grid,
        limits.create.ruling.formula,
        limits.create.ruling.ruling,
    )?)
}

fn state_without_payloads(
    state: &TableRulingState,
    grid: &TableGrid,
    limits: &TableTextToTableHwpxLimits,
) -> Result<TableRulingState, TableTextToTableHwpxError> {
    let cells = state
        .cells()
        .iter()
        .map(|cell| TableRulingCellDraft {
            master_cell_id: cell.master_cell_id().clone(),
            coordinate: cell.coordinate(),
            payload: Vec::new(),
            properties: cell.properties().clone(),
            formula: None,
        })
        .collect();
    Ok(TableRulingState::from_draft(
        TableRulingStateDraft {
            schema_version: TABLE_RULING_SCHEMA_VERSION.to_owned(),
            table_id: state.table_id().clone(),
            frame: state.frame(),
            grid_sha256: state.grid_sha256().to_owned(),
            table_properties_sha256: state.table_properties_sha256().to_owned(),
            row_boundaries_hwpunit: state.row_boundaries_hwpunit().to_vec(),
            column_boundaries_hwpunit: state.column_boundaries_hwpunit().to_vec(),
            edges: state.edges().to_vec(),
            cells,
        },
        grid,
        limits.create.ruling.formula,
        limits.create.ruling.ruling,
    )?)
}

fn patch_target_cell_text(
    section: &[u8],
    table_ordinal: usize,
    grid: &TableGrid,
    text_grid: &TableTextGrid,
    limits: &TableTextToTableHwpxLimits,
) -> Result<Vec<u8>, TableTextToTableHwpxError> {
    let document = PreservingXmlDocument::parse(section)?;
    let table = super::selected_table(&document, table_ordinal)?;
    let cells = super::selected_cells(&document, table, grid.master_cell_count())?;
    let mut edits = Vec::new();
    for (cell, coordinate) in cells {
        let text = text_grid
            .cell(
                usize::try_from(coordinate.row).map_err(|_| TableTextToTableHwpxError::Geometry)?,
                usize::try_from(coordinate.column)
                    .map_err(|_| TableTextToTableHwpxError::Geometry)?,
            )
            .ok_or(TableTextToTableHwpxError::Geometry)?;
        if text.is_empty() {
            continue;
        }
        let sub_list = super::unique_child(&document, cell, "subList")?;
        let span = super::element(&document, sub_list)?
            .content_span()
            .ok_or(TableTextToTableHwpxError::ReadbackMismatch)?;
        edits.push(RawEdit {
            start: span.start(),
            end: span.end(),
            replacement: native_text_paragraph(text, limits.flow)?,
        });
    }
    Ok(super::apply_edits(
        section,
        &mut edits,
        limits.create.ruling.layout.config().output_bytes,
    )?)
}

pub(super) fn read_unmerged_text_grid(
    section: &[u8],
    table_ordinal: usize,
    grid: &TableGrid,
    limits: &TableTextToTableHwpxLimits,
) -> Result<TableTextGrid, TableTextToTableHwpxError> {
    if grid
        .master_cells()
        .iter()
        .any(|cell| cell.row_span != 1 || cell.column_span != 1)
    {
        return Err(TableTextToTableHwpxError::ReadbackMismatch);
    }
    let document = PreservingXmlDocument::parse(section)?;
    let table = super::selected_table(&document, table_ordinal)?;
    let cells = super::selected_cells(&document, table, grid.master_cell_count())?;
    let rows = usize::try_from(grid.rows()).map_err(|_| TableTextToTableHwpxError::Geometry)?;
    let columns =
        usize::try_from(grid.columns()).map_err(|_| TableTextToTableHwpxError::Geometry)?;
    let mut values = vec![vec![String::new(); columns]; rows];
    for (cell, coordinate) in cells {
        let sub_list = super::unique_child(&document, cell, "subList")?;
        let paragraphs = super::direct_children_named(&document, sub_list, "p")?;
        if paragraphs.len() != 1 {
            return Err(TableTextToTableHwpxError::ReadbackMismatch);
        }
        let paragraph = paragraphs[0];
        let value = if super::is_empty_scaffold(section, &document, paragraph)? {
            String::new()
        } else {
            let bytes = super::element_bytes(section, super::element(&document, paragraph)?)?;
            let standalone = standalone_paragraph(bytes)?;
            let flow = TextFlowReader::read(&standalone, limits.flow)?;
            require_plain_text_flow(&flow)?;
            flow.visible_text_nfc()?
        };
        let row =
            usize::try_from(coordinate.row).map_err(|_| TableTextToTableHwpxError::Geometry)?;
        let column =
            usize::try_from(coordinate.column).map_err(|_| TableTextToTableHwpxError::Geometry)?;
        *values
            .get_mut(row)
            .and_then(|row| row.get_mut(column))
            .ok_or(TableTextToTableHwpxError::Geometry)? = value;
    }
    Ok(TableTextGrid::from_draft(
        TableTextGridDraft {
            schema_version: TABLE_TEXT_CONVERSION_SCHEMA_VERSION.to_owned(),
            rows: values,
        },
        limits.text,
    )?)
}

fn selected_top_level_paragraph(
    document: &PreservingXmlDocument,
    paragraph_ordinal: usize,
) -> Result<usize, TableTextToTableHwpxError> {
    let root = document.root_element();
    document
        .elements()
        .iter()
        .enumerate()
        .filter(|(_, value)| value.parent() == Some(root) && super::has_name(value, "p"))
        .nth(paragraph_ordinal)
        .map(|(index, _)| index)
        .ok_or(TableTextToTableHwpxError::SourceBindingMismatch)
}

pub(super) fn require_plain_text_flow(flow: &TextFlow) -> Result<(), TableTextToTableHwpxError> {
    if flow.children.iter().any(|child| match child {
        ParagraphChild::Run(run) => run
            .items
            .iter()
            .any(|item| !matches!(item, TextRunItem::Text(_))),
        ParagraphChild::Opaque(opaque) => opaque.may_contain_visible_text(),
    }) {
        return Err(TableTextToTableHwpxError::SourceBindingMismatch);
    }
    Ok(())
}

fn require_canonical_blank_template(
    section: &[u8],
    table_ordinal: usize,
    template: &TableRulingHwpxReadback,
    limits: &TableTextToTableHwpxLimits,
) -> Result<(), TableTextToTableHwpxError> {
    let grid = &template.grid;
    let text = read_unmerged_text_grid(section, table_ordinal, grid, limits)?;
    if text.rows().iter().flatten().any(|value| !value.is_empty()) {
        return Err(TableTextToTableHwpxError::ReadbackMismatch);
    }
    Ok(())
}

fn paragraph_context_digest(
    section: &[u8],
    paragraph_ordinal: usize,
    paragraph_sha256: [u8; 32],
    delimiter: TableDelimiter,
    grid: &TableTextGrid,
    limits: TableTextConversionLimits,
) -> Result<String, TableTextToTableHwpxError> {
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.table-text-to-table-hwpx-paragraph-context/v1\0");
    digest.update(Sha256::digest(section));
    digest.update(paragraph_ordinal.to_le_bytes());
    digest.update(paragraph_sha256);
    digest.update([match delimiter {
        TableDelimiter::Tab => 0,
        TableDelimiter::Comma => 1,
        TableDelimiter::Semicolon => 2,
    }]);
    digest.update(grid.canonical_sha256(limits)?);
    Ok(create_hwpx::hex(digest.finalize()))
}

pub(super) fn standalone_paragraph(fragment: &[u8]) -> Result<Vec<u8>, TableTextToTableHwpxError> {
    const PREFIX: &[u8] = b"<hp:p";
    if !fragment.starts_with(PREFIX) {
        return Err(TableTextToTableHwpxError::ReadbackMismatch);
    }
    let opening_end = fragment
        .iter()
        .position(|byte| *byte == b'>')
        .ok_or(TableTextToTableHwpxError::ReadbackMismatch)?;
    if fragment[..opening_end]
        .windows(b"xmlns:hp=".len())
        .any(|window| window == b"xmlns:hp=")
    {
        return Ok(fragment.to_vec());
    }
    let mut output = Vec::new();
    output
        .try_reserve_exact(
            fragment
                .len()
                .checked_add(HANCOM_2020_PARAGRAPH_NAMESPACE.len())
                .and_then(|value| value.checked_add(12))
                .ok_or(TableTextToTableHwpxError::OutputLimit)?,
        )
        .map_err(|_| TableTextToTableHwpxError::OutputLimit)?;
    output.extend_from_slice(PREFIX);
    output.extend_from_slice(b" xmlns:hp=\"");
    output.extend_from_slice(HANCOM_2020_PARAGRAPH_NAMESPACE.as_bytes());
    output.push(b'"');
    output.extend_from_slice(&fragment[PREFIX.len()..]);
    Ok(output)
}

pub(super) fn canonical_text_paragraph(
    text: &str,
    limits: TextFlowLimits,
) -> Result<Vec<u8>, TableTextToTableHwpxError> {
    if text.is_empty() {
        return Err(TableTextToTableHwpxError::ReadbackMismatch);
    }
    let mut atoms = Vec::new();
    let mut plain = String::new();
    for character in text.chars() {
        match character {
            '\t' | '\n' => {
                if !plain.is_empty() {
                    atoms.push(TextAtom::Text(std::mem::take(&mut plain)));
                }
                atoms.push(match character {
                    '\t' => TextAtom::Tab {
                        width: 0,
                        leader: 0,
                        tab_type: 0,
                    },
                    _ => TextAtom::LineBreak,
                });
            }
            _ => plain.push(character),
        }
    }
    if !plain.is_empty() {
        atoms.push(TextAtom::Text(plain));
    }
    let flow = TextFlow {
        paragraph: TextParagraphProperties {
            id: 0,
            paragraph_property_id_ref: Some(0),
            style_id_ref: Some(0),
            page_break: false,
            column_break: false,
            merged: false,
            paragraph_change_id: None,
        },
        children: vec![ParagraphChild::Run(TextRun {
            character_property_id_ref: Some(0),
            character_change_id: None,
            items: vec![TextRunItem::Text(TextSpan {
                character_style_id_ref: None,
                atoms,
            })],
        })],
    };
    let lowered = TextFlowWriter::lower(&flow, limits)?;
    lowered
        .strip_prefix(XML_DECLARATION)
        .map(ToOwned::to_owned)
        .ok_or(TableTextToTableHwpxError::ReadbackMismatch)
}

fn native_text_paragraph(
    text: &str,
    limits: TextFlowLimits,
) -> Result<Vec<u8>, TableTextToTableHwpxError> {
    let standalone = canonical_text_paragraph(text, limits)?;
    native_paragraph_fragment(&standalone)
}

pub(super) fn native_paragraph_fragment(
    standalone: &[u8],
) -> Result<Vec<u8>, TableTextToTableHwpxError> {
    const PREFIX: &[u8] = b"<hp:p";
    let namespace = format!(r#" xmlns:hp="{HANCOM_2020_PARAGRAPH_NAMESPACE}""#);
    let namespace = namespace.as_bytes();
    if !standalone.starts_with(PREFIX)
        || standalone.get(PREFIX.len()..PREFIX.len() + namespace.len()) != Some(namespace)
    {
        return Err(TableTextToTableHwpxError::ReadbackMismatch);
    }
    let mut fragment = Vec::new();
    fragment
        .try_reserve_exact(
            standalone
                .len()
                .checked_sub(namespace.len())
                .ok_or(TableTextToTableHwpxError::OutputLimit)?,
        )
        .map_err(|_| TableTextToTableHwpxError::OutputLimit)?;
    fragment.extend_from_slice(PREFIX);
    fragment.extend_from_slice(
        standalone
            .get(PREFIX.len() + namespace.len()..)
            .ok_or(TableTextToTableHwpxError::ReadbackMismatch)?,
    );
    Ok(fragment)
}

fn nonempty_cell_count(grid: &TableTextGrid) -> usize {
    grid.rows()
        .iter()
        .flatten()
        .filter(|value| !value.is_empty())
        .count()
}

fn serialized_limit(limits: &TableTextToTableHwpxLimits) -> usize {
    limits
        .text
        .config()
        .serialized_bytes
        .min(limits.create.ruling.grid.config().serialized_bytes)
        .min(limits.create.ruling.ruling.config().serialized_bytes)
}

fn serialize_bounded<T: Serialize + ?Sized>(
    value: &T,
    maximum: usize,
) -> Result<Vec<u8>, TableTextToTableHwpxError> {
    let bytes = serde_json::to_vec(value).map_err(|_| TableTextToTableHwpxError::Serialization)?;
    if bytes.len() > maximum {
        return Err(TableTextToTableHwpxError::OutputLimit);
    }
    Ok(bytes)
}

fn parse_digest(value: &str) -> Result<[u8; 32], TableTextToTableHwpxError> {
    create_hwpx::require_digest(value)?;
    let mut output = [0_u8; 32];
    for (index, chunk) in value.as_bytes().chunks_exact(2).enumerate() {
        let text = std::str::from_utf8(chunk)
            .map_err(|_| TableTextToTableHwpxError::SourceBindingMismatch)?;
        output[index] = u8::from_str_radix(text, 16)
            .map_err(|_| TableTextToTableHwpxError::SourceBindingMismatch)?;
    }
    Ok(output)
}
