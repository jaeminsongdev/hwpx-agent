use std::collections::BTreeSet;
use std::fmt;

use domain_ir::{
    FormulaCell, FormulaGridDimensions, TableGridError, TableRulingError, TableStructureBuilder,
    TableStructureError, TableStructureLimits, TableStructureOperation, TableStructurePlan,
    TableStructureRequest, TableStructureRequestDraft,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use super::{
    TableRulingHwpxBinding, TableRulingHwpxError, TableRulingHwpxLimits, TableRulingHwpxReadback,
    TableRulingHwpxReader,
};
use crate::{
    PreservingXmlDocument, PreservingXmlError, TableCaptionHwpxTarget, TableFormulaHwpxError,
    TableFormulaHwpxLowerer, TableLayoutHwpxError, TableLayoutHwpxReader, TablePaginationHwpxError,
    TablePaginationHwpxLimits, TablePaginationHwpxLowerer, TablePaginationHwpxReadback,
    TablePaginationHwpxReader, TablePaginationHwpxTarget,
};

pub const TABLE_STRUCTURE_HWPX_SCHEMA_VERSION: &str = "hwpx-agent.table-structure-hwpx/v1";
pub const TABLE_STRUCTURE_HWPX_PROFILE_ID: &str =
    "hwpx-agent.table-structure-hwpx.hancom-2020-wrapper/1";

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TableStructureHwpxLimits {
    pub structure: TableStructureLimits,
    pub ruling: TableRulingHwpxLimits,
    pub pagination: TablePaginationHwpxLimits,
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableStructureHwpxReadback {
    pub profile_id: &'static str,
    pub table_ordinal: usize,
    pub ruling: TableRulingHwpxReadback,
    pub pagination: TablePaginationHwpxReadback,
    pub wrapper_sha256: [u8; 32],
    pub wrapper_paragraph_id: u32,
    pub native_table_id: u32,
}

impl fmt::Debug for TableStructureHwpxReadback {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableStructureHwpxReadback")
            .field("profile_id", &self.profile_id)
            .field("table_ordinal", &self.table_ordinal)
            .field("rows", &self.ruling.grid.rows())
            .field("columns", &self.ruling.grid.columns())
            .field("master_cell_count", &self.ruling.grid.master_cell_count())
            .field("formula_count", &self.ruling.formula_count)
            .field("page_split", &self.pagination.page_split)
            .field("repeat_header_rows", &self.pagination.repeat_header_rows)
            .field("has_caption", &self.pagination.caption.is_some())
            .field("wrapper_paragraph_id", &self.wrapper_paragraph_id)
            .field("native_table_id", &self.native_table_id)
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct TableStructureHwpxReader;

impl TableStructureHwpxReader {
    /// Reads one exact top-level current-Hangul-2020 table wrapper, including its complete ruling,
    /// grid, payload, properties, formula/cache, pagination and caption state.
    ///
    /// # Errors
    ///
    /// Rejects malformed, ambiguous, over-limit or non-profile source parts and bindings.
    pub fn read_existing(
        header: &[u8],
        section: &[u8],
        table_ordinal: usize,
        binding: &TableRulingHwpxBinding,
        limits: TableStructureHwpxLimits,
    ) -> Result<TableStructureHwpxReadback, TableStructureHwpxError> {
        let ruling = TableRulingHwpxReader::read_existing_preserving_caption(
            header,
            section,
            table_ordinal,
            binding,
            &limits.ruling,
        )?;
        let pagination =
            TablePaginationHwpxReader::read_in_section(section, table_ordinal, limits.pagination)?;
        if pagination.row_count != ruling.grid.rows()
            || pagination.column_count != ruling.grid.columns()
        {
            return Err(TableStructureHwpxError::ReadbackMismatch);
        }
        let wrapper = wrapper_shape(section, table_ordinal)?;
        Ok(TableStructureHwpxReadback {
            profile_id: TABLE_STRUCTURE_HWPX_PROFILE_ID,
            table_ordinal,
            ruling,
            pagination,
            wrapper_sha256: wrapper.sha256,
            wrapper_paragraph_id: wrapper.paragraph_id,
            native_table_id: wrapper.table_id,
        })
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct TableStructureHwpxRequestDraft {
    pub schema_version: String,
    pub table_ordinal: usize,
    pub expected_header_sha256: String,
    pub expected_section_sha256: String,
    pub expected_wrapper_sha256: String,
    pub structure: TableStructureRequestDraft,
}

impl fmt::Debug for TableStructureHwpxRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableStructureHwpxRequestDraft")
            .field("schema_version", &self.schema_version)
            .field("table_ordinal", &self.table_ordinal)
            .field("expected_header_sha256", &"<redacted>")
            .field("expected_section_sha256", &"<redacted>")
            .field("expected_wrapper_sha256", &"<redacted>")
            .field("structure", &self.structure)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableStructureHwpxRequest {
    schema_version: &'static str,
    capability_id: &'static str,
    table_ordinal: usize,
    expected_header_sha256: String,
    expected_section_sha256: String,
    expected_wrapper_sha256: String,
    structure: TableStructureRequest,
}

impl TableStructureHwpxRequest {
    /// Admits one exact row/column structural request bound to source parts, wrapper, state, grid
    /// and document flow.
    ///
    /// # Errors
    ///
    /// Rejects schema, digest, part, wrapper, domain-transition or finite-bound drift.
    pub fn from_draft(
        draft: TableStructureHwpxRequestDraft,
        source: &TableStructureHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableStructureHwpxLimits,
    ) -> Result<Self, TableStructureHwpxError> {
        if draft.schema_version != TABLE_STRUCTURE_HWPX_SCHEMA_VERSION {
            return Err(TableStructureHwpxError::UnsupportedVersion);
        }
        for digest in [
            &draft.expected_header_sha256,
            &draft.expected_section_sha256,
            &draft.expected_wrapper_sha256,
            current_document_flow_sha256,
        ] {
            require_digest(digest)?;
        }
        let structure = TableStructureRequest::from_draft(
            draft.structure,
            &source.ruling.state,
            &source.ruling.grid,
            current_document_flow_sha256,
            limits.structure,
        )?;
        let request = Self {
            schema_version: TABLE_STRUCTURE_HWPX_SCHEMA_VERSION,
            capability_id: structure.capability_id(),
            table_ordinal: draft.table_ordinal,
            expected_header_sha256: draft.expected_header_sha256,
            expected_section_sha256: draft.expected_section_sha256,
            expected_wrapper_sha256: draft.expected_wrapper_sha256,
            structure,
        };
        validate_request_source(&request, source)?;
        let _ = TableStructureHwpxBuilder::build(
            &request,
            source,
            current_document_flow_sha256,
            limits,
        )?;
        let _ = request.canonical_json(limits)?;
        Ok(request)
    }

    /// Parses strict bounded JSON and applies the same exact admission as [`Self::from_draft`].
    ///
    /// # Errors
    ///
    /// Rejects empty, oversized, malformed, duplicate, unknown or semantically invalid input.
    pub fn from_json(
        bytes: &[u8],
        source: &TableStructureHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableStructureHwpxLimits,
    ) -> Result<Self, TableStructureHwpxError> {
        if bytes.is_empty()
            || bytes.len() > limits.structure.config().input_bytes
            || bytes.len() > limits.ruling.ruling.config().input_bytes
        {
            return Err(TableStructureHwpxError::InputLimit);
        }
        reject_duplicate_json_keys(bytes)?;
        let draft =
            serde_json::from_slice(bytes).map_err(|_| TableStructureHwpxError::InvalidJson)?;
        Self::from_draft(draft, source, current_document_flow_sha256, limits)
    }

    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
    }

    #[must_use]
    pub const fn table_ordinal(&self) -> usize {
        self.table_ordinal
    }

    #[must_use]
    pub const fn structure(&self) -> &TableStructureRequest {
        &self.structure
    }

    /// Serializes the complete typed request under its finite bound.
    ///
    /// # Errors
    ///
    /// Rejects serialization or output-limit failure.
    pub fn canonical_json(
        &self,
        limits: TableStructureHwpxLimits,
    ) -> Result<Vec<u8>, TableStructureHwpxError> {
        serialize_bounded(self, limits.structure.config().serialized_bytes)
    }

    /// Hashes the bounded canonical request.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failure.
    pub fn canonical_sha256(
        &self,
        limits: TableStructureHwpxLimits,
    ) -> Result<[u8; 32], TableStructureHwpxError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TableStructureHwpxRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableStructureHwpxRequest")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("table_ordinal", &self.table_ordinal)
            .field("expected_header_sha256", &"<redacted>")
            .field("expected_section_sha256", &"<redacted>")
            .field("expected_wrapper_sha256", &"<redacted>")
            .field("structure", &self.structure)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableStructureHwpxPlan {
    schema_version: &'static str,
    capability_id: &'static str,
    request_sha256: String,
    source_pagination_sha256: String,
    target_pagination_sha256: String,
    target_repeat_header_rows: u32,
    domain: TableStructurePlan,
    #[serde(skip)]
    target_pagination: TablePaginationHwpxTarget,
}

impl TableStructureHwpxPlan {
    #[must_use]
    pub const fn domain(&self) -> &TableStructurePlan {
        &self.domain
    }

    #[must_use]
    pub const fn target_repeat_header_rows(&self) -> u32 {
        self.target_repeat_header_rows
    }

    /// Serializes the complete semantic target and pagination bindings under a finite bound.
    ///
    /// # Errors
    ///
    /// Rejects serialization or output-limit failure.
    pub fn canonical_json(
        &self,
        limits: TableStructureHwpxLimits,
    ) -> Result<Vec<u8>, TableStructureHwpxError> {
        serialize_bounded(self, limits.structure.config().serialized_bytes)
    }

    /// Hashes the bounded canonical plan.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failure.
    pub fn canonical_sha256(
        &self,
        limits: TableStructureHwpxLimits,
    ) -> Result<[u8; 32], TableStructureHwpxError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TableStructureHwpxPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableStructureHwpxPlan")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("target_repeat_header_rows", &self.target_repeat_header_rows)
            .field("domain", &self.domain)
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct TableStructureHwpxBuilder;

impl TableStructureHwpxBuilder {
    /// Revalidates the exact source and builds one HWPX structural plan, including the transformed
    /// repeat-header state and preserved page-split/caption state.
    ///
    /// # Errors
    ///
    /// Rejects part, wrapper, flow, domain, pagination, formula/cache or finite-bound drift.
    pub fn build(
        request: &TableStructureHwpxRequest,
        source: &TableStructureHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableStructureHwpxLimits,
    ) -> Result<TableStructureHwpxPlan, TableStructureHwpxError> {
        validate_request_source(request, source)?;
        require_digest(current_document_flow_sha256)?;
        let domain = TableStructureBuilder::build(
            &request.structure,
            &source.ruling.state,
            &source.ruling.grid,
            current_document_flow_sha256,
            limits.structure,
        )?;
        let target_repeat_header_rows = transformed_repeat_header_rows(
            request.structure.operation(),
            request.structure.index(),
            request.structure.count(),
            source.pagination.repeat_header_rows,
        )?;
        if target_repeat_header_rows > domain.after_grid().rows() {
            return Err(TableStructureHwpxError::UnsupportedPaginationTransition);
        }
        if (source.pagination.repeat_header_rows == 0) != (target_repeat_header_rows == 0) {
            return Err(TableStructureHwpxError::UnsupportedPaginationTransition);
        }
        let target_pagination = TablePaginationHwpxTarget {
            page_split: source.pagination.page_split,
            repeat_header_rows: target_repeat_header_rows,
            caption: TableCaptionHwpxTarget::Preserve,
        };
        if let Some(formula) = single_formula(domain.after_state())? {
            TableFormulaHwpxLowerer::validate_target(formula, limits.ruling.formula_hwpx)
                .map_err(|_| TableStructureHwpxError::UnsupportedFormulaProfile)?;
        }
        let plan = TableStructureHwpxPlan {
            schema_version: TABLE_STRUCTURE_HWPX_SCHEMA_VERSION,
            capability_id: request.capability_id,
            request_sha256: hex(request.canonical_sha256(limits)?),
            source_pagination_sha256: pagination_digest(
                source.pagination.page_split,
                source.pagination.repeat_header_rows,
                source.pagination.row_count,
                source.pagination.column_count,
                source.pagination.caption.as_ref(),
            ),
            target_pagination_sha256: pagination_digest(
                target_pagination.page_split,
                target_pagination.repeat_header_rows,
                domain.after_grid().rows(),
                domain.after_grid().columns(),
                source.pagination.caption.as_ref(),
            ),
            target_repeat_header_rows,
            domain,
            target_pagination,
        };
        let _ = plan.canonical_json(limits)?;
        Ok(plan)
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableStructureHwpxLoweringReceipt {
    pub profile_id: &'static str,
    pub source_header_sha256: [u8; 32],
    pub output_header_sha256: [u8; 32],
    pub source_section_sha256: [u8; 32],
    pub output_section_sha256: [u8; 32],
    pub source_wrapper_sha256: [u8; 32],
    pub output_wrapper_sha256: [u8; 32],
    pub source_state_sha256: [u8; 32],
    pub target_state_sha256: [u8; 32],
    pub source_grid_sha256: [u8; 32],
    pub target_grid_sha256: [u8; 32],
    pub request_sha256: [u8; 32],
    pub plan_sha256: [u8; 32],
    pub before_document_flow_sha256: [u8; 32],
    pub after_document_flow_sha256: [u8; 32],
    pub source_table_count: usize,
    pub target_table_count: usize,
    pub preserved_master_cell_count: usize,
    pub inserted_master_cell_count: usize,
    pub deleted_master_cell_count: usize,
    pub preserved_payload_block_count: usize,
    pub formula_rebased_count: usize,
    pub formula_deleted_count: usize,
    pub pagination_modified_attribute_count: usize,
    pub formula_modified_text_count: usize,
    pub added_border_fill_count: usize,
}

impl fmt::Debug for TableStructureHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableStructureHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field("source_table_count", &self.source_table_count)
            .field("target_table_count", &self.target_table_count)
            .field(
                "preserved_master_cell_count",
                &self.preserved_master_cell_count,
            )
            .field(
                "inserted_master_cell_count",
                &self.inserted_master_cell_count,
            )
            .field("deleted_master_cell_count", &self.deleted_master_cell_count)
            .field(
                "preserved_payload_block_count",
                &self.preserved_payload_block_count,
            )
            .field("formula_rebased_count", &self.formula_rebased_count)
            .field("formula_deleted_count", &self.formula_deleted_count)
            .field(
                "pagination_modified_attribute_count",
                &self.pagination_modified_attribute_count,
            )
            .field(
                "formula_modified_text_count",
                &self.formula_modified_text_count,
            )
            .field("added_border_fill_count", &self.added_border_fill_count)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableStructureHwpxLoweredParts {
    pub header: Vec<u8>,
    pub section: Vec<u8>,
    pub binding: TableRulingHwpxBinding,
    pub receipt: TableStructureHwpxLoweringReceipt,
}

impl fmt::Debug for TableStructureHwpxLoweredParts {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableStructureHwpxLoweredParts")
            .field("header_bytes", &self.header.len())
            .field("section_bytes", &self.section.len())
            .field("binding", &self.binding)
            .field("receipt", &self.receipt)
            .finish()
    }
}

#[derive(Debug)]
pub struct TableStructureHwpxLowerer;

impl TableStructureHwpxLowerer {
    /// Lowers one exact structural edit and returns only after complete ruling/grid/payload/
    /// properties/formula/cache/pagination/caption semantic reopen succeeds.
    ///
    /// # Errors
    ///
    /// Rejects source, flow, request or plan drift, nonrepresentable native state, finite output
    /// failure, native identity drift or final semantic readback mismatch.
    #[allow(clippy::too_many_arguments)]
    pub fn lower_existing(
        header: &[u8],
        section: &[u8],
        binding: &TableRulingHwpxBinding,
        current_document_flow_sha256: &str,
        request: &TableStructureHwpxRequest,
        plan: &TableStructureHwpxPlan,
        limits: TableStructureHwpxLimits,
    ) -> Result<TableStructureHwpxLoweredParts, TableStructureHwpxError> {
        let source = TableStructureHwpxReader::read_existing(
            header,
            section,
            request.table_ordinal,
            binding,
            limits,
        )?;
        validate_request_source(request, &source)?;
        let rebuilt = TableStructureHwpxBuilder::build(
            request,
            &source,
            current_document_flow_sha256,
            limits,
        )?;
        if rebuilt != *plan {
            return Err(TableStructureHwpxError::PlanBindingMismatch);
        }
        let native =
            lower_native_and_reopen(header, section, binding, request, plan, &source, &limits)?;
        let domain_receipt = plan.domain.receipt();
        let receipt = TableStructureHwpxLoweringReceipt {
            profile_id: TABLE_STRUCTURE_HWPX_PROFILE_ID,
            source_header_sha256: Sha256::digest(header).into(),
            output_header_sha256: Sha256::digest(&native.header).into(),
            source_section_sha256: Sha256::digest(section).into(),
            output_section_sha256: Sha256::digest(&native.section).into(),
            source_wrapper_sha256: source.wrapper_sha256,
            output_wrapper_sha256: native.output_wrapper_sha256,
            source_state_sha256: source.ruling.state.canonical_sha256(limits.ruling.ruling)?,
            target_state_sha256: plan
                .domain
                .after_state()
                .canonical_sha256(limits.ruling.ruling)?,
            source_grid_sha256: source.ruling.grid.canonical_sha256()?,
            target_grid_sha256: plan.domain.after_grid().canonical_sha256()?,
            request_sha256: request.canonical_sha256(limits)?,
            plan_sha256: plan.canonical_sha256(limits)?,
            before_document_flow_sha256: parse_digest(
                request.structure.expected_document_flow_sha256(),
            )?,
            after_document_flow_sha256: parse_digest(
                request.structure.target_document_flow_sha256(),
            )?,
            source_table_count: native.source_table_count,
            target_table_count: native.target_table_count,
            preserved_master_cell_count: domain_receipt.preserved_master_cell_count(),
            inserted_master_cell_count: domain_receipt.inserted_master_cell_count(),
            deleted_master_cell_count: domain_receipt.deleted_master_cell_count(),
            preserved_payload_block_count: plan.domain.after_state().cells().iter().try_fold(
                0_usize,
                |total, cell| {
                    total
                        .checked_add(cell.payload().len())
                        .ok_or(TableStructureHwpxError::OutputLimit)
                },
            )?,
            formula_rebased_count: domain_receipt.formula_rebased_count(),
            formula_deleted_count: domain_receipt.formula_deleted_count(),
            pagination_modified_attribute_count: native.pagination_modified_attribute_count,
            formula_modified_text_count: native.formula_modified_text_count,
            added_border_fill_count: native.added_border_fill_count,
        };
        Ok(TableStructureHwpxLoweredParts {
            header: native.header,
            section: native.section,
            binding: native.binding,
            receipt,
        })
    }
}

struct NativeStructureLowering {
    header: Vec<u8>,
    section: Vec<u8>,
    binding: TableRulingHwpxBinding,
    output_wrapper_sha256: [u8; 32],
    source_table_count: usize,
    target_table_count: usize,
    pagination_modified_attribute_count: usize,
    formula_modified_text_count: usize,
    added_border_fill_count: usize,
}

fn lower_native_and_reopen(
    header: &[u8],
    section: &[u8],
    binding: &TableRulingHwpxBinding,
    request: &TableStructureHwpxRequest,
    plan: &TableStructureHwpxPlan,
    source: &TableStructureHwpxReadback,
    limits: &TableStructureHwpxLimits,
) -> Result<NativeStructureLowering, TableStructureHwpxError> {
    let rendered = super::render_structure_existing(
        header,
        section,
        request.table_ordinal,
        binding,
        &source.ruling.state,
        plan.domain.after_state(),
        plan.domain.after_grid(),
        &limits.ruling,
    )?;
    let (mut output_section, pagination_receipt) =
        TablePaginationHwpxLowerer::lower_in_section_with_receipt(
            &rendered.section,
            request.table_ordinal,
            &plan.target_pagination,
            limits.pagination,
        )?;
    let formula_modified_text_count =
        if let Some(formula) = single_formula(plan.domain.after_state())? {
            let dimensions = FormulaGridDimensions {
                rows: plan.domain.after_grid().rows(),
                columns: plan.domain.after_grid().columns(),
            };
            let (lowered, receipt) =
                TableFormulaHwpxLowerer::lower_in_section_preserving_merged_topology(
                    &output_section,
                    request.table_ordinal,
                    formula,
                    dimensions,
                    limits.ruling.formula_hwpx,
                    limits.ruling.formula,
                )?;
            output_section = lowered;
            receipt.modified_text_count
        } else {
            0
        };
    let source_table_count =
        TableLayoutHwpxReader::count_in_section(section, limits.ruling.layout)?;
    let target_table_count =
        TableLayoutHwpxReader::count_in_section(&output_section, limits.ruling.layout)?;
    if target_table_count != source_table_count {
        return Err(TableStructureHwpxError::ReadbackMismatch);
    }
    let target_binding =
        super::binding_from_state(plan.domain.after_state(), plan.domain.after_grid())?;
    let reopened = TableStructureHwpxReader::read_existing(
        &rendered.header,
        &output_section,
        request.table_ordinal,
        &target_binding,
        *limits,
    )?;
    if reopened.ruling.grid != *plan.domain.after_grid()
        || reopened.ruling.state != *plan.domain.after_state()
        || reopened.pagination.page_split != plan.target_pagination.page_split
        || reopened.pagination.repeat_header_rows != plan.target_pagination.repeat_header_rows
        || reopened.pagination.caption != source.pagination.caption
        || reopened.wrapper_paragraph_id != source.wrapper_paragraph_id
        || reopened.native_table_id != source.native_table_id
    {
        return Err(TableStructureHwpxError::ReadbackMismatch);
    }
    Ok(NativeStructureLowering {
        header: rendered.header,
        section: output_section,
        binding: target_binding,
        output_wrapper_sha256: reopened.wrapper_sha256,
        source_table_count,
        target_table_count,
        pagination_modified_attribute_count: pagination_receipt.modified_attribute_count,
        formula_modified_text_count,
        added_border_fill_count: rendered.added_border_fill_count,
    })
}

#[derive(Debug, Error)]
pub enum TableStructureHwpxError {
    #[error("unsupported table structure HWPX schema version")]
    UnsupportedVersion,
    #[error("table structure HWPX input exceeds a finite bound")]
    InputLimit,
    #[error("invalid table structure HWPX JSON")]
    InvalidJson,
    #[error("invalid table structure HWPX binding")]
    InvalidBinding,
    #[error("table structure HWPX source parts or wrapper drifted")]
    SourceBindingMismatch,
    #[error("table structure HWPX plan drifted")]
    PlanBindingMismatch,
    #[error("selected table is not the exact top-level Hangul wrapper profile")]
    UnsupportedWrapper,
    #[error("repeat-header transition has no exact preserving mapping")]
    UnsupportedPaginationTransition,
    #[error("surviving formula is outside the exact native left-prefix decimal-cache profile")]
    UnsupportedFormulaProfile,
    #[error("table structure HWPX semantic readback mismatched")]
    ReadbackMismatch,
    #[error("table structure HWPX allocation failed")]
    AllocationFailed,
    #[error("table structure HWPX serialization failed")]
    Serialization,
    #[error("table structure HWPX output exceeds a finite bound")]
    OutputLimit,
    #[error(transparent)]
    Structure(#[from] TableStructureError),
    #[error(transparent)]
    Grid(#[from] TableGridError),
    #[error(transparent)]
    ModelRuling(#[from] TableRulingError),
    #[error(transparent)]
    Ruling(#[from] TableRulingHwpxError),
    #[error(transparent)]
    Layout(#[from] TableLayoutHwpxError),
    #[error(transparent)]
    Pagination(#[from] TablePaginationHwpxError),
    #[error(transparent)]
    Formula(#[from] TableFormulaHwpxError),
    #[error(transparent)]
    Xml(#[from] PreservingXmlError),
}

impl TableStructureHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::UnsupportedVersion => "table_structure_hwpx_unsupported_version",
            Self::InputLimit => "table_structure_hwpx_input_limit",
            Self::InvalidJson => "table_structure_hwpx_invalid_json",
            Self::InvalidBinding => "table_structure_hwpx_invalid_binding",
            Self::SourceBindingMismatch => "table_structure_hwpx_source_binding_mismatch",
            Self::PlanBindingMismatch => "table_structure_hwpx_plan_binding_mismatch",
            Self::UnsupportedWrapper => "table_structure_hwpx_unsupported_wrapper",
            Self::UnsupportedPaginationTransition => {
                "table_structure_hwpx_unsupported_pagination_transition"
            }
            Self::UnsupportedFormulaProfile => "table_structure_hwpx_unsupported_formula_profile",
            Self::ReadbackMismatch => "table_structure_hwpx_readback_mismatch",
            Self::AllocationFailed => "table_structure_hwpx_allocation_failed",
            Self::Serialization => "table_structure_hwpx_serialization",
            Self::OutputLimit => "table_structure_hwpx_output_limit",
            Self::Structure(_) => "table_structure_hwpx_domain",
            Self::Grid(_) => "table_structure_hwpx_grid",
            Self::ModelRuling(_) => "table_structure_hwpx_model_ruling",
            Self::Ruling(_) => "table_structure_hwpx_ruling",
            Self::Layout(_) => "table_structure_hwpx_layout",
            Self::Pagination(_) => "table_structure_hwpx_pagination",
            Self::Formula(_) => "table_structure_hwpx_formula",
            Self::Xml(_) => "table_structure_hwpx_invalid_xml",
        }
    }
}

fn validate_request_source(
    request: &TableStructureHwpxRequest,
    source: &TableStructureHwpxReadback,
) -> Result<(), TableStructureHwpxError> {
    if request.table_ordinal != source.table_ordinal
        || request.expected_header_sha256 != hex(source.ruling.header_sha256)
        || request.expected_section_sha256 != hex(source.ruling.section_sha256)
        || request.expected_wrapper_sha256 != hex(source.wrapper_sha256)
    {
        return Err(TableStructureHwpxError::SourceBindingMismatch);
    }
    Ok(())
}

fn transformed_repeat_header_rows(
    operation: TableStructureOperation,
    index: u32,
    count: u32,
    source: u32,
) -> Result<u32, TableStructureHwpxError> {
    match operation {
        TableStructureOperation::InsertRows if index < source => source
            .checked_add(count)
            .ok_or(TableStructureHwpxError::OutputLimit),
        TableStructureOperation::DeleteRows if index < source => {
            let end = index
                .checked_add(count)
                .ok_or(TableStructureHwpxError::OutputLimit)?;
            let overlap = end
                .min(source)
                .checked_sub(index)
                .ok_or(TableStructureHwpxError::UnsupportedPaginationTransition)?;
            source
                .checked_sub(overlap)
                .ok_or(TableStructureHwpxError::UnsupportedPaginationTransition)
        }
        _ => Ok(source),
    }
}

fn single_formula(
    state: &domain_ir::TableRulingState,
) -> Result<Option<&FormulaCell>, TableStructureHwpxError> {
    let mut result = None;
    for formula in state.cells().iter().filter_map(|cell| cell.formula()) {
        if result.replace(formula).is_some() {
            return Err(TableStructureHwpxError::ReadbackMismatch);
        }
    }
    Ok(result)
}

#[derive(Clone, Copy, Debug)]
struct WrapperShape {
    sha256: [u8; 32],
    paragraph_id: u32,
    table_id: u32,
}

fn wrapper_shape(
    section: &[u8],
    table_ordinal: usize,
) -> Result<WrapperShape, TableStructureHwpxError> {
    let document = PreservingXmlDocument::parse(section)?;
    let table = super::selected_table(&document, table_ordinal)?;
    let run = super::element(&document, table)?
        .parent()
        .ok_or(TableStructureHwpxError::UnsupportedWrapper)?;
    let paragraph = super::element(&document, run)?
        .parent()
        .ok_or(TableStructureHwpxError::UnsupportedWrapper)?;
    if !super::has_name(super::element(&document, run)?, "run")
        || !super::has_name(super::element(&document, paragraph)?, "p")
        || super::element(&document, paragraph)?.parent() != Some(document.root_element())
    {
        return Err(TableStructureHwpxError::UnsupportedWrapper);
    }
    let wrapper = super::insertion_wrapper(section, table_ordinal)?;
    Ok(WrapperShape {
        sha256: Sha256::digest(wrapper).into(),
        paragraph_id: super::required_u32(super::element(&document, paragraph)?, "id")?,
        table_id: super::required_u32(super::element(&document, table)?, "id")?,
    })
}

fn pagination_digest(
    page_split: domain_ir::TablePageSplitPolicy,
    repeat_header_rows: u32,
    rows: u32,
    columns: u32,
    caption: Option<&crate::TableCaptionHwpxProperties>,
) -> String {
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.table-structure-hwpx-pagination/v1\0");
    digest.update(match page_split {
        domain_ir::TablePageSplitPolicy::Allow => b"allow".as_slice(),
        domain_ir::TablePageSplitPolicy::AvoidRow => b"avoid_row".as_slice(),
        domain_ir::TablePageSplitPolicy::AvoidTable => b"avoid_table".as_slice(),
        domain_ir::TablePageSplitPolicy::RequiredKeep => b"required_keep".as_slice(),
    });
    digest.update(repeat_header_rows.to_le_bytes());
    digest.update(rows.to_le_bytes());
    digest.update(columns.to_le_bytes());
    if let Some(caption) = caption {
        digest.update(b"caption\0");
        digest.update(match caption.side {
            domain_ir::CaptionSide::Top => b"top".as_slice(),
            domain_ir::CaptionSide::Bottom => b"bottom".as_slice(),
        });
        digest.update([u8::from(caption.full_size)]);
        digest.update(caption.width_hwpunit.to_le_bytes());
        digest.update(caption.gap_hwpunit.to_le_bytes());
        digest.update(caption.last_width_hwpunit.to_le_bytes());
        digest.update(caption.content_sha256);
    } else {
        digest.update(b"no-caption\0");
    }
    hex(digest.finalize())
}

fn serialize_bounded<T: Serialize + ?Sized>(
    value: &T,
    maximum: usize,
) -> Result<Vec<u8>, TableStructureHwpxError> {
    let bytes = serde_json::to_vec(value).map_err(|_| TableStructureHwpxError::Serialization)?;
    if bytes.len() > maximum {
        return Err(TableStructureHwpxError::OutputLimit);
    }
    Ok(bytes)
}

fn reject_duplicate_json_keys(bytes: &[u8]) -> Result<(), TableStructureHwpxError> {
    struct DuplicateRejectingSeed;

    impl<'de> serde::de::DeserializeSeed<'de> for DuplicateRejectingSeed {
        type Value = ();

        fn deserialize<D>(self, deserializer: D) -> Result<Self::Value, D::Error>
        where
            D: serde::Deserializer<'de>,
        {
            deserializer.deserialize_any(DuplicateRejectingVisitor)
        }
    }

    struct DuplicateRejectingVisitor;

    impl<'de> serde::de::Visitor<'de> for DuplicateRejectingVisitor {
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
                map.next_value_seed(DuplicateRejectingSeed)?;
            }
            Ok(())
        }

        fn visit_seq<A>(self, mut sequence: A) -> Result<Self::Value, A::Error>
        where
            A: serde::de::SeqAccess<'de>,
        {
            while sequence
                .next_element_seed(DuplicateRejectingSeed)?
                .is_some()
            {}
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
    serde::de::DeserializeSeed::deserialize(DuplicateRejectingSeed, &mut deserializer)
        .map_err(|_| TableStructureHwpxError::InvalidJson)?;
    deserializer
        .end()
        .map_err(|_| TableStructureHwpxError::InvalidJson)
}

fn require_digest(value: &str) -> Result<(), TableStructureHwpxError> {
    if value.len() != 64
        || value
            .bytes()
            .any(|byte| !byte.is_ascii_digit() && !(b'a'..=b'f').contains(&byte))
    {
        return Err(TableStructureHwpxError::InvalidBinding);
    }
    Ok(())
}

fn parse_digest(value: &str) -> Result<[u8; 32], TableStructureHwpxError> {
    require_digest(value)?;
    let mut output = [0_u8; 32];
    for (index, chunk) in value.as_bytes().chunks_exact(2).enumerate() {
        let text =
            std::str::from_utf8(chunk).map_err(|_| TableStructureHwpxError::InvalidBinding)?;
        output[index] =
            u8::from_str_radix(text, 16).map_err(|_| TableStructureHwpxError::InvalidBinding)?;
    }
    Ok(output)
}

fn hex(value: impl AsRef<[u8]>) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let bytes = value.as_ref();
    let mut output = String::with_capacity(bytes.len().saturating_mul(2));
    for byte in bytes {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}
