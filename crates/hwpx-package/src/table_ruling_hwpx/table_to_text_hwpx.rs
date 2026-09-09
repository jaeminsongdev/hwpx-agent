use std::collections::BTreeSet;
use std::fmt;
use std::str;

use domain_ir::{
    LogicalId, TableDelimiter, TableGrid, TableGridError, TableLineEnding, TablePageSplitPolicy,
    TableRulingError, TableRulingState, TableTextConversionError, TableTextConversionLimits,
    TableTextGrid,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use super::create_hwpx::{self, TableCreateHwpxError};
use super::text_conversion_hwpx::{
    TableTextToTableHwpxError, read_unmerged_text_grid, require_plain_text_flow,
    standalone_paragraph,
};
use super::{
    RawEdit, TableRulingHwpxBinding, TableRulingHwpxError, TableRulingHwpxLimits,
    TableRulingHwpxReadback, TableRulingHwpxReader,
};
use crate::preserving_xml::{PreservingXmlDocument, XmlByteSpan};
use crate::{
    ParagraphChild, TablePaginationHwpxError, TablePaginationHwpxLimits,
    TablePaginationHwpxReadback, TablePaginationHwpxReader, TextAtom, TextFlow, TextFlowError,
    TextFlowLimits, TextFlowReader, TextFlowWriter, TextRun, TextRunItem, TextSpan,
};

pub const TABLE_TABLE_TO_TEXT_HWPX_SCHEMA_VERSION: &str = "hwpx-agent.table-table-to-text-hwpx/v1";
pub const TABLE_TABLE_TO_TEXT_HWPX_PROFILE_ID: &str =
    "hwpx-agent.table-table-to-text-hwpx.hancom-2020-plain-grid/1";
const XML_DECLARATION: &[u8] = b"<?xml version=\"1.0\" encoding=\"UTF-8\"?>";

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TableTableToTextHwpxLimits {
    pub ruling: TableRulingHwpxLimits,
    pub pagination: TablePaginationHwpxLimits,
    pub text: TableTextConversionLimits,
    pub flow: TextFlowLimits,
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableTableToTextHwpxReadback {
    pub profile_id: &'static str,
    pub table_ordinal: usize,
    pub paragraph_ordinal: usize,
    pub delimiter: TableDelimiter,
    pub line_ending: TableLineEnding,
    pub header_sha256: [u8; 32],
    pub section_sha256: [u8; 32],
    pub wrapper_sha256: [u8; 32],
    pub wrapper_context_sha256: String,
    pub source_table_count: usize,
    pub serialized_text_sha256: [u8; 32],
    pub target_paragraph_sha256: [u8; 32],
    pub ruling: TableRulingHwpxReadback,
    pub pagination: TablePaginationHwpxReadback,
    pub text_grid: TableTextGrid,
    wrapper_flow: TextFlow,
    target_flow: TextFlow,
    serialized_text: Vec<u8>,
    target_paragraph: Vec<u8>,
}

impl fmt::Debug for TableTableToTextHwpxReadback {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableTableToTextHwpxReadback")
            .field("profile_id", &self.profile_id)
            .field("table_ordinal", &self.table_ordinal)
            .field("paragraph_ordinal", &self.paragraph_ordinal)
            .field("delimiter", &self.delimiter)
            .field("line_ending", &self.line_ending)
            .field("source_table_count", &self.source_table_count)
            .field("rows", &self.text_grid.row_count())
            .field("columns", &self.text_grid.column_count())
            .field("serialized_text_bytes", &self.serialized_text.len())
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct TableTableToTextHwpxReader;

impl TableTableToTextHwpxReader {
    /// Reads one exact top-level table wrapper as a complete plain rectangular text grid.
    ///
    /// # Errors
    ///
    /// Rejects malformed, merged, formula-bearing, captioned, multi-paragraph, opaque, dynamic,
    /// ambiguous or over-limit input.
    pub fn read_context(
        header: &[u8],
        section: &[u8],
        table_ordinal: usize,
        binding: &TableRulingHwpxBinding,
        delimiter: TableDelimiter,
        line_ending: TableLineEnding,
        limits: TableTableToTextHwpxLimits,
    ) -> Result<TableTableToTextHwpxReadback, TableTableToTextHwpxError> {
        let wrapper = exact_table_wrapper(section, table_ordinal, limits.flow)?;
        let ruling = TableRulingHwpxReader::read_existing(
            header,
            section,
            table_ordinal,
            binding,
            limits.ruling,
        )?;
        require_plain_unmerged_source(&ruling)?;
        let pagination =
            TablePaginationHwpxReader::read_in_section(section, table_ordinal, limits.pagination)?;
        if pagination.caption.is_some() {
            return Err(TableTableToTextHwpxError::UnsupportedCaption);
        }
        let text_grid = read_unmerged_text_grid(
            section,
            table_ordinal,
            &ruling.grid,
            &super::text_conversion_hwpx::TableTextToTableHwpxLimits {
                create: super::create_hwpx::TableCreateHwpxLimits {
                    ruling: limits.ruling,
                    pagination: limits.pagination,
                },
                text: limits.text,
                flow: limits.flow,
            },
        )?;
        let serialized_text = text_grid.to_delimited(delimiter, line_ending, limits.text)?;
        let semantic_text = semantic_document_text(&serialized_text, line_ending)?;
        let target_flow = target_flow(&wrapper.flow, &semantic_text)?;
        let target_paragraph = lower_flow(&target_flow, limits.flow)?;
        let source_table_count =
            TablePaginationHwpxReader::count_in_section(section, limits.pagination)?;
        let wrapper_sha256 = Sha256::digest(&wrapper.bytes).into();
        let serialized_text_sha256 = Sha256::digest(&serialized_text).into();
        let target_paragraph_sha256 = Sha256::digest(&target_paragraph).into();
        let wrapper_context_sha256 = wrapper_context_digest(
            section,
            table_ordinal,
            wrapper.paragraph_ordinal,
            wrapper_sha256,
            &ruling,
            &text_grid,
            delimiter,
            line_ending,
            &limits,
        )?;
        Ok(TableTableToTextHwpxReadback {
            profile_id: TABLE_TABLE_TO_TEXT_HWPX_PROFILE_ID,
            table_ordinal,
            paragraph_ordinal: wrapper.paragraph_ordinal,
            delimiter,
            line_ending,
            header_sha256: Sha256::digest(header).into(),
            section_sha256: Sha256::digest(section).into(),
            wrapper_sha256,
            wrapper_context_sha256,
            source_table_count,
            serialized_text_sha256,
            target_paragraph_sha256,
            ruling,
            pagination,
            text_grid,
            wrapper_flow: wrapper.flow,
            target_flow,
            serialized_text,
            target_paragraph,
        })
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableTableToTextHwpxRequestDraft {
    pub schema_version: String,
    pub table_ordinal: usize,
    pub expected_paragraph_ordinal: usize,
    pub delimiter: TableDelimiter,
    pub line_ending: TableLineEnding,
    pub expected_header_sha256: String,
    pub expected_section_sha256: String,
    pub expected_wrapper_sha256: String,
    pub expected_wrapper_context_sha256: String,
    pub expected_table_content_sha256: String,
    pub expected_source_state_sha256: String,
    pub expected_source_grid_sha256: String,
    pub expected_text_grid_sha256: String,
    pub expected_serialized_text_sha256: String,
    pub expected_target_paragraph_sha256: String,
    pub expected_source_table_count: usize,
    pub expected_document_flow_sha256: String,
    pub target_document_flow_sha256: String,
    pub output_text_block_id: LogicalId,
}

impl fmt::Debug for TableTableToTextHwpxRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableTableToTextHwpxRequestDraft")
            .field("schema_version", &self.schema_version)
            .field("table_ordinal", &self.table_ordinal)
            .field(
                "expected_paragraph_ordinal",
                &self.expected_paragraph_ordinal,
            )
            .field("delimiter", &self.delimiter)
            .field("line_ending", &self.line_ending)
            .field(
                "expected_source_table_count",
                &self.expected_source_table_count,
            )
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableTableToTextHwpxRequest {
    schema_version: &'static str,
    capability_id: &'static str,
    table_ordinal: usize,
    expected_paragraph_ordinal: usize,
    delimiter: TableDelimiter,
    line_ending: TableLineEnding,
    expected_header_sha256: String,
    expected_section_sha256: String,
    expected_wrapper_sha256: String,
    expected_wrapper_context_sha256: String,
    expected_table_content_sha256: String,
    expected_source_state_sha256: String,
    expected_source_grid_sha256: String,
    expected_text_grid_sha256: String,
    expected_serialized_text_sha256: String,
    expected_target_paragraph_sha256: String,
    expected_source_table_count: usize,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    output_text_block_id: LogicalId,
}

impl TableTableToTextHwpxRequest {
    /// Binds an exact source table and deterministic text replacement to current document flow.
    ///
    /// # Errors
    ///
    /// Rejects schema, digest, source, identity, flow or finite-limit drift.
    pub fn from_draft(
        draft: TableTableToTextHwpxRequestDraft,
        source: &TableTableToTextHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableTableToTextHwpxLimits,
    ) -> Result<Self, TableTableToTextHwpxError> {
        if draft.schema_version != TABLE_TABLE_TO_TEXT_HWPX_SCHEMA_VERSION {
            return Err(TableTableToTextHwpxError::UnsupportedVersion);
        }
        for digest in [
            &draft.expected_header_sha256,
            &draft.expected_section_sha256,
            &draft.expected_wrapper_sha256,
            &draft.expected_wrapper_context_sha256,
            &draft.expected_table_content_sha256,
            &draft.expected_source_state_sha256,
            &draft.expected_source_grid_sha256,
            &draft.expected_text_grid_sha256,
            &draft.expected_serialized_text_sha256,
            &draft.expected_target_paragraph_sha256,
            &draft.expected_document_flow_sha256,
            &draft.target_document_flow_sha256,
            current_document_flow_sha256,
        ] {
            create_hwpx::require_digest(digest)?;
        }
        let request = Self {
            schema_version: TABLE_TABLE_TO_TEXT_HWPX_SCHEMA_VERSION,
            capability_id: "table.table_to_text",
            table_ordinal: draft.table_ordinal,
            expected_paragraph_ordinal: draft.expected_paragraph_ordinal,
            delimiter: draft.delimiter,
            line_ending: draft.line_ending,
            expected_header_sha256: draft.expected_header_sha256,
            expected_section_sha256: draft.expected_section_sha256,
            expected_wrapper_sha256: draft.expected_wrapper_sha256,
            expected_wrapper_context_sha256: draft.expected_wrapper_context_sha256,
            expected_table_content_sha256: draft.expected_table_content_sha256,
            expected_source_state_sha256: draft.expected_source_state_sha256,
            expected_source_grid_sha256: draft.expected_source_grid_sha256,
            expected_text_grid_sha256: draft.expected_text_grid_sha256,
            expected_serialized_text_sha256: draft.expected_serialized_text_sha256,
            expected_target_paragraph_sha256: draft.expected_target_paragraph_sha256,
            expected_source_table_count: draft.expected_source_table_count,
            expected_document_flow_sha256: draft.expected_document_flow_sha256,
            target_document_flow_sha256: draft.target_document_flow_sha256,
            output_text_block_id: draft.output_text_block_id,
        };
        validate_request_source(&request, source, current_document_flow_sha256, &limits)?;
        let _ = TableTableToTextHwpxBuilder::build(
            &request,
            source,
            current_document_flow_sha256,
            limits,
        )?;
        let _ = request.canonical_json(limits)?;
        Ok(request)
    }

    /// Parses bounded strict JSON and applies the same semantic admission as [`Self::from_draft`].
    ///
    /// # Errors
    ///
    /// Rejects empty, oversized, malformed, duplicate, unknown or semantically invalid input.
    pub fn from_json(
        bytes: &[u8],
        source: &TableTableToTextHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableTableToTextHwpxLimits,
    ) -> Result<Self, TableTableToTextHwpxError> {
        if bytes.is_empty() || bytes.len() > serialized_limit(&limits) {
            return Err(TableTableToTextHwpxError::InputLimit);
        }
        create_hwpx::reject_duplicate_json_keys(bytes)
            .map_err(|_| TableTableToTextHwpxError::InvalidJson)?;
        let draft =
            serde_json::from_slice(bytes).map_err(|_| TableTableToTextHwpxError::InvalidJson)?;
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

    /// Serializes the full typed request within the configured finite bound.
    ///
    /// # Errors
    ///
    /// Rejects serialization or output-limit failure.
    pub fn canonical_json(
        &self,
        limits: TableTableToTextHwpxLimits,
    ) -> Result<Vec<u8>, TableTableToTextHwpxError> {
        serialize_bounded(self, serialized_limit(&limits))
    }

    /// Hashes the bounded canonical request.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failure.
    pub fn canonical_sha256(
        &self,
        limits: TableTableToTextHwpxLimits,
    ) -> Result<[u8; 32], TableTableToTextHwpxError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TableTableToTextHwpxRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableTableToTextHwpxRequest")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("table_ordinal", &self.table_ordinal)
            .field(
                "expected_paragraph_ordinal",
                &self.expected_paragraph_ordinal,
            )
            .field("delimiter", &self.delimiter)
            .field("line_ending", &self.line_ending)
            .field(
                "expected_source_table_count",
                &self.expected_source_table_count,
            )
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableTableToTextHwpxPlan {
    schema_version: &'static str,
    capability_id: &'static str,
    request_sha256: String,
    table_ordinal: usize,
    paragraph_ordinal: usize,
    source_table_count: usize,
    target_table_count: usize,
    source_header_sha256: String,
    source_section_sha256: String,
    wrapper_context_sha256: String,
    source_state_sha256: String,
    source_grid_sha256: String,
    text_grid_sha256: String,
    serialized_text_sha256: String,
    target_paragraph_sha256: String,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    output_text_block_id: LogicalId,
    source_state: TableRulingState,
    #[serde(skip)]
    source_grid: TableGrid,
    #[serde(skip)]
    target_flow: TextFlow,
    #[serde(skip)]
    serialized_text: Vec<u8>,
    #[serde(skip)]
    target_paragraph: Vec<u8>,
}

impl TableTableToTextHwpxPlan {
    #[must_use]
    pub const fn source_state(&self) -> &TableRulingState {
        &self.source_state
    }

    #[must_use]
    pub const fn source_grid(&self) -> &TableGrid {
        &self.source_grid
    }

    #[must_use]
    pub fn serialized_text_sha256(&self) -> &str {
        &self.serialized_text_sha256
    }

    /// Serializes all non-content semantic and integrity bindings under finite output limits.
    ///
    /// # Errors
    ///
    /// Rejects serialization or output-limit failure.
    pub fn canonical_json(
        &self,
        limits: TableTableToTextHwpxLimits,
    ) -> Result<Vec<u8>, TableTableToTextHwpxError> {
        serialize_bounded(self, serialized_limit(&limits))
    }

    /// Hashes the bounded canonical plan.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failure.
    pub fn canonical_sha256(
        &self,
        limits: TableTableToTextHwpxLimits,
    ) -> Result<[u8; 32], TableTableToTextHwpxError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TableTableToTextHwpxPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableTableToTextHwpxPlan")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("table_ordinal", &self.table_ordinal)
            .field("paragraph_ordinal", &self.paragraph_ordinal)
            .field("source_table_count", &self.source_table_count)
            .field("target_table_count", &self.target_table_count)
            .field("rows", &self.source_grid.rows())
            .field("columns", &self.source_grid.columns())
            .field("serialized_text_bytes", &self.serialized_text.len())
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct TableTableToTextHwpxBuilder;

impl TableTableToTextHwpxBuilder {
    /// Revalidates the complete source and builds the exact deterministic table-to-text plan.
    ///
    /// # Errors
    ///
    /// Rejects source, state, grid, text, identity, flow or output drift.
    pub fn build(
        request: &TableTableToTextHwpxRequest,
        source: &TableTableToTextHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableTableToTextHwpxLimits,
    ) -> Result<TableTableToTextHwpxPlan, TableTableToTextHwpxError> {
        validate_request_source(request, source, current_document_flow_sha256, &limits)?;
        let target_table_count = source
            .source_table_count
            .checked_sub(1)
            .ok_or(TableTableToTextHwpxError::SourceBindingMismatch)?;
        let plan = TableTableToTextHwpxPlan {
            schema_version: TABLE_TABLE_TO_TEXT_HWPX_SCHEMA_VERSION,
            capability_id: request.capability_id,
            request_sha256: create_hwpx::hex(request.canonical_sha256(limits)?),
            table_ordinal: source.table_ordinal,
            paragraph_ordinal: source.paragraph_ordinal,
            source_table_count: source.source_table_count,
            target_table_count,
            source_header_sha256: create_hwpx::hex(source.header_sha256),
            source_section_sha256: create_hwpx::hex(source.section_sha256),
            wrapper_context_sha256: source.wrapper_context_sha256.clone(),
            source_state_sha256: create_hwpx::hex(
                source.ruling.state.canonical_sha256(limits.ruling.ruling)?,
            ),
            source_grid_sha256: create_hwpx::hex(source.ruling.grid.canonical_sha256()?),
            text_grid_sha256: create_hwpx::hex(source.text_grid.canonical_sha256(limits.text)?),
            serialized_text_sha256: create_hwpx::hex(source.serialized_text_sha256),
            target_paragraph_sha256: create_hwpx::hex(source.target_paragraph_sha256),
            expected_document_flow_sha256: request.expected_document_flow_sha256.clone(),
            target_document_flow_sha256: request.target_document_flow_sha256.clone(),
            output_text_block_id: request.output_text_block_id.clone(),
            source_state: source.ruling.state.clone(),
            source_grid: source.ruling.grid.clone(),
            target_flow: source.target_flow.clone(),
            serialized_text: source.serialized_text.clone(),
            target_paragraph: source.target_paragraph.clone(),
        };
        let _ = plan.canonical_json(limits)?;
        Ok(plan)
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableTableToTextHwpxLoweringReceipt {
    pub profile_id: &'static str,
    pub source_header_sha256: [u8; 32],
    pub output_header_sha256: [u8; 32],
    pub source_section_sha256: [u8; 32],
    pub output_section_sha256: [u8; 32],
    pub wrapper_context_sha256: [u8; 32],
    pub source_state_sha256: [u8; 32],
    pub source_grid_sha256: [u8; 32],
    pub text_grid_sha256: [u8; 32],
    pub serialized_text_sha256: [u8; 32],
    pub target_paragraph_sha256: [u8; 32],
    pub request_sha256: [u8; 32],
    pub plan_sha256: [u8; 32],
    pub before_document_flow_sha256: [u8; 32],
    pub after_document_flow_sha256: [u8; 32],
    pub output_text_block_id: LogicalId,
    pub paragraph_ordinal: usize,
    pub source_table_count: usize,
    pub target_table_count: usize,
    pub rows: u32,
    pub columns: u32,
    pub master_cell_count: usize,
    pub payload_block_count: usize,
    pub formula_count: usize,
    pub serialized_text_bytes: usize,
    pub source_page_split: TablePageSplitPolicy,
    pub source_repeat_header_rows: u32,
}

impl fmt::Debug for TableTableToTextHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableTableToTextHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field("paragraph_ordinal", &self.paragraph_ordinal)
            .field("source_table_count", &self.source_table_count)
            .field("target_table_count", &self.target_table_count)
            .field("rows", &self.rows)
            .field("columns", &self.columns)
            .field("master_cell_count", &self.master_cell_count)
            .field("payload_block_count", &self.payload_block_count)
            .field("formula_count", &self.formula_count)
            .field("serialized_text_bytes", &self.serialized_text_bytes)
            .field("source_page_split", &self.source_page_split)
            .field("source_repeat_header_rows", &self.source_repeat_header_rows)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableTableToTextHwpxLoweredParts {
    pub header: Vec<u8>,
    pub section: Vec<u8>,
    pub text: Vec<u8>,
    pub receipt: TableTableToTextHwpxLoweringReceipt,
}

impl fmt::Debug for TableTableToTextHwpxLoweredParts {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableTableToTextHwpxLoweredParts")
            .field("header_bytes", &self.header.len())
            .field("section_bytes", &self.section.len())
            .field("text_bytes", &self.text.len())
            .field("receipt", &self.receipt)
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct TableTableToTextHwpxLowerer;

impl TableTableToTextHwpxLowerer {
    /// Replaces one exact table wrapper with deterministic text and returns only after reopen.
    ///
    /// # Errors
    ///
    /// Rejects source, state, grid, wrapper, text, flow, plan, table-count or readback drift without
    /// returning partial output.
    #[allow(clippy::too_many_arguments)]
    pub fn lower(
        header: &[u8],
        section: &[u8],
        binding: &TableRulingHwpxBinding,
        delimiter: TableDelimiter,
        line_ending: TableLineEnding,
        current_document_flow_sha256: &str,
        request: &TableTableToTextHwpxRequest,
        plan: &TableTableToTextHwpxPlan,
        limits: TableTableToTextHwpxLimits,
    ) -> Result<TableTableToTextHwpxLoweredParts, TableTableToTextHwpxError> {
        let source = TableTableToTextHwpxReader::read_context(
            header,
            section,
            request.table_ordinal,
            binding,
            delimiter,
            line_ending,
            limits,
        )?;
        validate_request_source(request, &source, current_document_flow_sha256, &limits)?;
        let rebuilt = TableTableToTextHwpxBuilder::build(
            request,
            &source,
            current_document_flow_sha256,
            limits,
        )?;
        if rebuilt != *plan {
            return Err(TableTableToTextHwpxError::PlanBindingMismatch);
        }
        let wrapper = exact_table_wrapper(section, request.table_ordinal, limits.flow)?;
        if Sha256::digest(&wrapper.bytes).as_slice() != source.wrapper_sha256 {
            return Err(TableTableToTextHwpxError::SourceBindingMismatch);
        }
        let mut edits = vec![RawEdit {
            start: wrapper.outer.start(),
            end: wrapper.outer.end(),
            replacement: plan.target_paragraph.clone(),
        }];
        let output_section =
            super::apply_edits(section, &mut edits, limits.pagination.config().output_bytes)?;
        verify_output(&output_section, plan, &limits)?;
        let output_header = header.to_vec();
        let receipt = TableTableToTextHwpxLoweringReceipt {
            profile_id: TABLE_TABLE_TO_TEXT_HWPX_PROFILE_ID,
            source_header_sha256: source.header_sha256,
            output_header_sha256: Sha256::digest(&output_header).into(),
            source_section_sha256: source.section_sha256,
            output_section_sha256: Sha256::digest(&output_section).into(),
            wrapper_context_sha256: parse_digest(&source.wrapper_context_sha256)?,
            source_state_sha256: source.ruling.state.canonical_sha256(limits.ruling.ruling)?,
            source_grid_sha256: source.ruling.grid.canonical_sha256()?,
            text_grid_sha256: source.text_grid.canonical_sha256(limits.text)?,
            serialized_text_sha256: source.serialized_text_sha256,
            target_paragraph_sha256: source.target_paragraph_sha256,
            request_sha256: request.canonical_sha256(limits)?,
            plan_sha256: plan.canonical_sha256(limits)?,
            before_document_flow_sha256: parse_digest(&request.expected_document_flow_sha256)?,
            after_document_flow_sha256: parse_digest(&request.target_document_flow_sha256)?,
            output_text_block_id: request.output_text_block_id.clone(),
            paragraph_ordinal: source.paragraph_ordinal,
            source_table_count: source.source_table_count,
            target_table_count: plan.target_table_count,
            rows: source.ruling.grid.rows(),
            columns: source.ruling.grid.columns(),
            master_cell_count: source.ruling.grid.master_cell_count(),
            payload_block_count: source.ruling.payload_block_count,
            formula_count: source.ruling.formula_count,
            serialized_text_bytes: source.serialized_text.len(),
            source_page_split: source.pagination.page_split,
            source_repeat_header_rows: source.pagination.repeat_header_rows,
        };
        Ok(TableTableToTextHwpxLoweredParts {
            header: output_header,
            section: output_section,
            text: plan.serialized_text.clone(),
            receipt,
        })
    }
}

#[derive(Debug, Error)]
pub enum TableTableToTextHwpxError {
    #[error("unsupported table-to-text HWPX schema version")]
    UnsupportedVersion,
    #[error("table-to-text HWPX input exceeds a finite bound")]
    InputLimit,
    #[error("invalid table-to-text HWPX JSON")]
    InvalidJson,
    #[error("table-to-text HWPX source, wrapper, table or flow drifted")]
    SourceBindingMismatch,
    #[error("table-to-text HWPX requires a distinct target document flow")]
    FlowBindingMismatch,
    #[error("table-to-text HWPX requires one exact top-level current-profile wrapper")]
    UnsupportedWrapper,
    #[error("table-to-text HWPX merged-cell semantics are not admitted")]
    UnsupportedMergedCells,
    #[error("table-to-text HWPX formula/cache flattening is not admitted")]
    UnsupportedFormula,
    #[error("table-to-text HWPX caption flattening is not admitted")]
    UnsupportedCaption,
    #[error("table-to-text HWPX output identity collides with source state")]
    IdentityConflict,
    #[error("table-to-text HWPX plan drifted")]
    PlanBindingMismatch,
    #[error("table-to-text HWPX semantic readback mismatched")]
    ReadbackMismatch,
    #[error("table-to-text HWPX serialization failed")]
    Serialization,
    #[error("table-to-text HWPX output exceeds a finite bound")]
    OutputLimit,
    #[error(transparent)]
    Create(#[from] TableCreateHwpxError),
    #[error(transparent)]
    Grid(#[from] TableGridError),
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
    TextAdapter(#[from] TableTextToTableHwpxError),
    #[error(transparent)]
    Xml(#[from] crate::preserving_xml::PreservingXmlError),
}

impl TableTableToTextHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::UnsupportedVersion => "table_table_to_text_hwpx_unsupported_version",
            Self::InputLimit => "table_table_to_text_hwpx_input_limit",
            Self::InvalidJson => "table_table_to_text_hwpx_invalid_json",
            Self::SourceBindingMismatch => "table_table_to_text_hwpx_source_binding_mismatch",
            Self::FlowBindingMismatch => "table_table_to_text_hwpx_flow_binding_mismatch",
            Self::UnsupportedWrapper => "table_table_to_text_hwpx_unsupported_wrapper",
            Self::UnsupportedMergedCells => "table_table_to_text_hwpx_unsupported_merged_cells",
            Self::UnsupportedFormula => "table_table_to_text_hwpx_unsupported_formula",
            Self::UnsupportedCaption => "table_table_to_text_hwpx_unsupported_caption",
            Self::IdentityConflict => "table_table_to_text_hwpx_identity_conflict",
            Self::PlanBindingMismatch => "table_table_to_text_hwpx_plan_binding_mismatch",
            Self::ReadbackMismatch => "table_table_to_text_hwpx_readback_mismatch",
            Self::Serialization => "table_table_to_text_hwpx_serialization",
            Self::OutputLimit => "table_table_to_text_hwpx_output_limit",
            Self::Create(_) => "table_table_to_text_hwpx_create",
            Self::Grid(_) => "table_table_to_text_hwpx_grid",
            Self::RulingModel(_) => "table_table_to_text_hwpx_ruling_model",
            Self::TextModel(_) => "table_table_to_text_hwpx_text_model",
            Self::TextFlow(_) => "table_table_to_text_hwpx_text_flow",
            Self::Ruling(_) => "table_table_to_text_hwpx_ruling",
            Self::Pagination(_) => "table_table_to_text_hwpx_pagination",
            Self::TextAdapter(_) => "table_table_to_text_hwpx_text_adapter",
            Self::Xml(_) => "table_table_to_text_hwpx_xml",
        }
    }
}

fn validate_request_source(
    request: &TableTableToTextHwpxRequest,
    source: &TableTableToTextHwpxReadback,
    current_document_flow_sha256: &str,
    limits: &TableTableToTextHwpxLimits,
) -> Result<(), TableTableToTextHwpxError> {
    create_hwpx::require_digest(current_document_flow_sha256)?;
    require_plain_unmerged_source(&source.ruling)?;
    if source.profile_id != TABLE_TABLE_TO_TEXT_HWPX_PROFILE_ID
        || source.ruling.profile_id != super::TABLE_RULING_HWPX_PROFILE_ID
        || request.table_ordinal != source.table_ordinal
        || request.expected_paragraph_ordinal != source.paragraph_ordinal
        || request.delimiter != source.delimiter
        || request.line_ending != source.line_ending
        || request.expected_header_sha256 != create_hwpx::hex(source.header_sha256)
        || request.expected_section_sha256 != create_hwpx::hex(source.section_sha256)
        || request.expected_wrapper_sha256 != create_hwpx::hex(source.wrapper_sha256)
        || request.expected_wrapper_context_sha256 != source.wrapper_context_sha256
        || request.expected_table_content_sha256
            != create_hwpx::hex(source.ruling.table_content_sha256)
        || request.expected_source_state_sha256
            != create_hwpx::hex(source.ruling.state.canonical_sha256(limits.ruling.ruling)?)
        || request.expected_source_grid_sha256
            != create_hwpx::hex(source.ruling.grid.canonical_sha256()?)
        || request.expected_text_grid_sha256
            != create_hwpx::hex(source.text_grid.canonical_sha256(limits.text)?)
        || request.expected_serialized_text_sha256
            != create_hwpx::hex(source.serialized_text_sha256)
        || request.expected_target_paragraph_sha256
            != create_hwpx::hex(source.target_paragraph_sha256)
        || request.expected_source_table_count != source.source_table_count
        || request.expected_document_flow_sha256 != current_document_flow_sha256
    {
        return Err(TableTableToTextHwpxError::SourceBindingMismatch);
    }
    if request.expected_document_flow_sha256 == request.target_document_flow_sha256 {
        return Err(TableTableToTextHwpxError::FlowBindingMismatch);
    }
    validate_output_identity(&request.output_text_block_id, &source.ruling.state)?;
    Ok(())
}

fn validate_output_identity(
    output: &LogicalId,
    source: &TableRulingState,
) -> Result<(), TableTableToTextHwpxError> {
    let mut identities = BTreeSet::new();
    identities.insert(source.table_id().clone());
    for cell in source.cells() {
        identities.insert(cell.master_cell_id().clone());
        for payload in cell.payload() {
            identities.insert(payload.block_id.clone());
        }
    }
    if identities.contains(output) {
        return Err(TableTableToTextHwpxError::IdentityConflict);
    }
    Ok(())
}

fn require_plain_unmerged_source(
    source: &TableRulingHwpxReadback,
) -> Result<(), TableTableToTextHwpxError> {
    if source.formula_count != 0
        || source
            .state
            .cells()
            .iter()
            .any(|cell| cell.formula().is_some())
    {
        return Err(TableTableToTextHwpxError::UnsupportedFormula);
    }
    if source
        .grid
        .master_cells()
        .iter()
        .any(|cell| cell.row_span != 1 || cell.column_span != 1)
    {
        return Err(TableTableToTextHwpxError::UnsupportedMergedCells);
    }
    Ok(())
}

struct ExactTableWrapper {
    paragraph_ordinal: usize,
    outer: XmlByteSpan,
    bytes: Vec<u8>,
    flow: TextFlow,
}

fn exact_table_wrapper(
    section: &[u8],
    table_ordinal: usize,
    flow_limits: TextFlowLimits,
) -> Result<ExactTableWrapper, TableTableToTextHwpxError> {
    let bytes = super::insertion_wrapper(section, table_ordinal)?;
    let document = PreservingXmlDocument::parse(section)?;
    let table = super::selected_table(&document, table_ordinal)?;
    let control = super::element(&document, table)?
        .parent()
        .ok_or(TableTableToTextHwpxError::UnsupportedWrapper)?;
    let run = super::element(&document, control)?
        .parent()
        .ok_or(TableTableToTextHwpxError::UnsupportedWrapper)?;
    let paragraph = super::element(&document, run)?
        .parent()
        .ok_or(TableTableToTextHwpxError::UnsupportedWrapper)?;
    let text = super::direct_children_named(&document, run, "t")?;
    if !super::has_name(super::element(&document, control)?, "ctrl")
        || !super::has_name(super::element(&document, run)?, "run")
        || !super::has_name(super::element(&document, paragraph)?, "p")
        || super::element(&document, paragraph)?.parent() != Some(document.root_element())
        || text.len() != 1
        || !has_exact_direct_children(&document, paragraph, &[run])
        || !has_exact_direct_children(&document, run, &[control, text[0]])
        || !has_exact_direct_children(&document, control, &[table])
    {
        return Err(TableTableToTextHwpxError::UnsupportedWrapper);
    }
    let paragraph_ordinal = document
        .elements()
        .iter()
        .enumerate()
        .filter(|(_, value)| {
            value.parent() == Some(document.root_element()) && super::has_name(value, "p")
        })
        .position(|(index, _)| index == paragraph)
        .ok_or(TableTableToTextHwpxError::UnsupportedWrapper)?;
    let outer = super::element(&document, paragraph)?
        .outer_span()
        .ok_or(TableTableToTextHwpxError::UnsupportedWrapper)?;
    if section.get(outer.start()..outer.end()) != Some(bytes.as_slice()) {
        return Err(TableTableToTextHwpxError::UnsupportedWrapper);
    }
    let flow = TextFlowReader::read(&standalone_paragraph(&bytes)?, flow_limits)?;
    require_exact_wrapper_flow(&flow)?;
    Ok(ExactTableWrapper {
        paragraph_ordinal,
        outer,
        bytes,
        flow,
    })
}

fn require_exact_wrapper_flow(flow: &TextFlow) -> Result<(), TableTableToTextHwpxError> {
    let [ParagraphChild::Run(run)] = flow.children.as_slice() else {
        return Err(TableTableToTextHwpxError::UnsupportedWrapper);
    };
    let [TextRunItem::Opaque(_), TextRunItem::Text(span)] = run.items.as_slice() else {
        return Err(TableTableToTextHwpxError::UnsupportedWrapper);
    };
    if !span.atoms.is_empty() {
        return Err(TableTableToTextHwpxError::UnsupportedWrapper);
    }
    Ok(())
}

fn has_exact_direct_children(
    document: &PreservingXmlDocument,
    parent: usize,
    expected: &[usize],
) -> bool {
    document
        .elements()
        .iter()
        .enumerate()
        .filter_map(|(index, value)| (value.parent() == Some(parent)).then_some(index))
        .eq(expected.iter().copied())
}

fn target_flow(wrapper: &TextFlow, text: &str) -> Result<TextFlow, TableTableToTextHwpxError> {
    require_exact_wrapper_flow(wrapper)?;
    let ParagraphChild::Run(source_run) = &wrapper.children[0] else {
        return Err(TableTableToTextHwpxError::UnsupportedWrapper);
    };
    let character_style_id_ref = source_run.items.iter().find_map(|item| match item {
        TextRunItem::Text(span) => Some(span.character_style_id_ref),
        _ => None,
    });
    let mut atoms = Vec::new();
    atoms
        .try_reserve(text.chars().count())
        .map_err(|_| TableTableToTextHwpxError::OutputLimit)?;
    let mut plain = String::new();
    plain
        .try_reserve(text.len())
        .map_err(|_| TableTableToTextHwpxError::OutputLimit)?;
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
    Ok(TextFlow {
        paragraph: wrapper.paragraph.clone(),
        children: vec![ParagraphChild::Run(TextRun {
            character_property_id_ref: source_run.character_property_id_ref,
            character_change_id: source_run.character_change_id,
            items: vec![TextRunItem::Text(TextSpan {
                character_style_id_ref: character_style_id_ref.flatten(),
                atoms,
            })],
        })],
    })
}

fn lower_flow(
    flow: &TextFlow,
    limits: TextFlowLimits,
) -> Result<Vec<u8>, TableTableToTextHwpxError> {
    let lowered = TextFlowWriter::lower(flow, limits)?;
    lowered
        .strip_prefix(XML_DECLARATION)
        .map(ToOwned::to_owned)
        .ok_or(TableTableToTextHwpxError::ReadbackMismatch)
}

fn semantic_document_text(
    bytes: &[u8],
    line_ending: TableLineEnding,
) -> Result<String, TableTableToTextHwpxError> {
    let source = str::from_utf8(bytes).map_err(|_| TableTableToTextHwpxError::ReadbackMismatch)?;
    let mut output = String::new();
    output
        .try_reserve_exact(source.len())
        .map_err(|_| TableTableToTextHwpxError::OutputLimit)?;
    let mut characters = source.chars().peekable();
    while let Some(character) = characters.next() {
        match (line_ending, character) {
            (TableLineEnding::CrLf, '\r') => {
                if characters.next() != Some('\n') {
                    return Err(TableTableToTextHwpxError::ReadbackMismatch);
                }
                output.push('\n');
            }
            (TableLineEnding::CrLf, '\n') => {
                return Err(TableTableToTextHwpxError::ReadbackMismatch);
            }
            (_, value) => output.push(value),
        }
    }
    Ok(output)
}

fn verify_output(
    output_section: &[u8],
    plan: &TableTableToTextHwpxPlan,
    limits: &TableTableToTextHwpxLimits,
) -> Result<(), TableTableToTextHwpxError> {
    let document = PreservingXmlDocument::parse(output_section)?;
    let paragraph = select_top_level_paragraph(&document, plan.paragraph_ordinal)?;
    let bytes = super::element_bytes(output_section, super::element(&document, paragraph)?)?;
    let flow = TextFlowReader::read(&standalone_paragraph(bytes)?, limits.flow)?;
    require_plain_text_flow(&flow)?;
    let visible = flow.visible_text_nfc()?;
    let expected_visible = plan.target_flow.visible_text_nfc()?;
    let table_count =
        TablePaginationHwpxReader::count_in_section(output_section, limits.pagination)?;
    if bytes != plan.target_paragraph
        || flow != plan.target_flow
        || visible != expected_visible
        || table_count != plan.target_table_count
    {
        return Err(TableTableToTextHwpxError::ReadbackMismatch);
    }
    Ok(())
}

fn select_top_level_paragraph(
    document: &PreservingXmlDocument,
    paragraph_ordinal: usize,
) -> Result<usize, TableTableToTextHwpxError> {
    let root = document.root_element();
    document
        .elements()
        .iter()
        .enumerate()
        .filter(|(_, value)| value.parent() == Some(root) && super::has_name(value, "p"))
        .nth(paragraph_ordinal)
        .map(|(index, _)| index)
        .ok_or(TableTableToTextHwpxError::ReadbackMismatch)
}

#[allow(clippy::too_many_arguments)]
fn wrapper_context_digest(
    section: &[u8],
    table_ordinal: usize,
    paragraph_ordinal: usize,
    wrapper_sha256: [u8; 32],
    ruling: &TableRulingHwpxReadback,
    text_grid: &TableTextGrid,
    delimiter: TableDelimiter,
    line_ending: TableLineEnding,
    limits: &TableTableToTextHwpxLimits,
) -> Result<String, TableTableToTextHwpxError> {
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.table-table-to-text-hwpx-wrapper-context/v1\0");
    digest.update(Sha256::digest(section));
    digest.update(table_ordinal.to_le_bytes());
    digest.update(paragraph_ordinal.to_le_bytes());
    digest.update(wrapper_sha256);
    digest.update(ruling.state.canonical_sha256(limits.ruling.ruling)?);
    digest.update(ruling.grid.canonical_sha256()?);
    digest.update(text_grid.canonical_sha256(limits.text)?);
    digest.update([
        match delimiter {
            TableDelimiter::Tab => 0,
            TableDelimiter::Comma => 1,
            TableDelimiter::Semicolon => 2,
        },
        match line_ending {
            TableLineEnding::Lf => 0,
            TableLineEnding::CrLf => 1,
        },
    ]);
    Ok(create_hwpx::hex(digest.finalize()))
}

fn serialized_limit(limits: &TableTableToTextHwpxLimits) -> usize {
    limits
        .text
        .config()
        .serialized_bytes
        .min(limits.flow.config().input_bytes)
        .min(limits.ruling.grid.config().serialized_bytes)
        .min(limits.ruling.ruling.config().serialized_bytes)
}

fn serialize_bounded<T: Serialize + ?Sized>(
    value: &T,
    maximum: usize,
) -> Result<Vec<u8>, TableTableToTextHwpxError> {
    let bytes = serde_json::to_vec(value).map_err(|_| TableTableToTextHwpxError::Serialization)?;
    if bytes.len() > maximum {
        return Err(TableTableToTextHwpxError::OutputLimit);
    }
    Ok(bytes)
}

fn parse_digest(value: &str) -> Result<[u8; 32], TableTableToTextHwpxError> {
    create_hwpx::require_digest(value)?;
    let mut output = [0_u8; 32];
    for (index, chunk) in value.as_bytes().chunks_exact(2).enumerate() {
        let text =
            str::from_utf8(chunk).map_err(|_| TableTableToTextHwpxError::SourceBindingMismatch)?;
        output[index] = u8::from_str_radix(text, 16)
            .map_err(|_| TableTableToTextHwpxError::SourceBindingMismatch)?;
    }
    Ok(output)
}
