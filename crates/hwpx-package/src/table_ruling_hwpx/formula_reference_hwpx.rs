use std::fmt;

use domain_ir::{
    CaptionSide, CellCoordinate, FormulaCache, FormulaCachePolicy, FormulaCell, FormulaCellDraft,
    FormulaExpression, FormulaGridDimensions, FormulaLimits, FormulaNumberFormat,
    FormulaReferenceKind, FormulaValue, TablePageSplitPolicy,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use super::create_hwpx;
use crate::{
    TableFormulaHwpxError, TableFormulaHwpxLimits, TableFormulaHwpxLowerer, TableFormulaHwpxReader,
    TableLayoutHwpxError, TableLayoutHwpxLimits, TableLayoutHwpxReader, TablePaginationHwpxError,
    TablePaginationHwpxLimits, TablePaginationHwpxReadback, TablePaginationHwpxReader,
};

pub const TABLE_ABSOLUTE_REFERENCE_HWPX_SCHEMA_VERSION: &str =
    "hwpx-agent.table-absolute-reference-hwpx/v1";
pub const TABLE_ABSOLUTE_REFERENCE_HWPX_PROFILE_ID: &str =
    "hwpx-agent.table-absolute-reference-hwpx.hancom-2020-canonical-field/1";
pub const TABLE_ABSOLUTE_REFERENCE_CAPABILITY_ID: &str = "table.formula_absolute_ref";

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TableAbsoluteReferenceHwpxLimits {
    pub formula: FormulaLimits,
    pub native: TableFormulaHwpxLimits,
    pub layout: TableLayoutHwpxLimits,
    pub pagination: TablePaginationHwpxLimits,
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableAbsoluteReferenceHwpxReadback {
    pub profile_id: &'static str,
    pub table_ordinal: usize,
    pub owner: CellCoordinate,
    pub header_sha256: [u8; 32],
    pub section_sha256: [u8; 32],
    pub table_content_sha256: [u8; 32],
    pub selected_formula_sha256: [u8; 32],
    pub selected_unowned_sha256: [u8; 32],
    pub pagination_policy_sha256: [u8; 32],
    pub source_table_count: usize,
    pub formula_field_count: usize,
    pub rows: u32,
    pub columns: u32,
    pub formula: FormulaCell,
    pub pagination: TablePaginationHwpxReadback,
}

impl fmt::Debug for TableAbsoluteReferenceHwpxReadback {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableAbsoluteReferenceHwpxReadback")
            .field("profile_id", &self.profile_id)
            .field("table_ordinal", &self.table_ordinal)
            .field("owner", &self.owner)
            .field("rows", &self.rows)
            .field("columns", &self.columns)
            .field("formula_field_count", &self.formula_field_count)
            .field("cache", &cache_state(self.formula.cache()))
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct TableAbsoluteReferenceHwpxReader;

impl TableAbsoluteReferenceHwpxReader {
    /// Lifts one selected canonical formula field and exact surrounding table/package state.
    ///
    /// # Errors
    ///
    /// Rejects malformed or ambiguous formula fields, invalid table geometry, pagination drift,
    /// unsupported formula/cache text, or finite-limit failures.
    pub fn read_context(
        header: &[u8],
        section: &[u8],
        table_ordinal: usize,
        owner: CellCoordinate,
        limits: TableAbsoluteReferenceHwpxLimits,
    ) -> Result<TableAbsoluteReferenceHwpxReadback, TableAbsoluteReferenceHwpxError> {
        if header.len() > limits.native.config().input_bytes {
            return Err(TableAbsoluteReferenceHwpxError::InputLimit);
        }
        let formula = TableFormulaHwpxReader::read_canonical_cell_in_section(
            section,
            table_ordinal,
            owner,
            limits.native,
            limits.formula,
        )?;
        let layout = TableLayoutHwpxReader::read_in_section_preserving_caption(
            section,
            table_ordinal,
            limits.layout,
        )?;
        let pagination =
            TablePaginationHwpxReader::read_in_section(section, table_ordinal, limits.pagination)?;
        if formula.rows != layout.rows
            || formula.columns != layout.columns
            || pagination.row_count != layout.rows
            || pagination.column_count != layout.columns
        {
            return Err(TableAbsoluteReferenceHwpxError::SourceBindingMismatch);
        }
        let source_table_count =
            TablePaginationHwpxReader::count_in_section(section, limits.pagination)?;
        Ok(TableAbsoluteReferenceHwpxReadback {
            profile_id: TABLE_ABSOLUTE_REFERENCE_HWPX_PROFILE_ID,
            table_ordinal,
            owner,
            header_sha256: Sha256::digest(header).into(),
            section_sha256: Sha256::digest(section).into(),
            table_content_sha256: layout.content_sha256,
            selected_formula_sha256: formula.formula.canonical_sha256(limits.formula)?,
            selected_unowned_sha256: formula.unowned_sha256,
            pagination_policy_sha256: pagination_policy_sha256(&pagination),
            source_table_count,
            formula_field_count: formula.formula_field_count,
            rows: formula.rows,
            columns: formula.columns,
            formula: formula.formula,
            pagination,
        })
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableAbsoluteReferenceHwpxRequestDraft {
    pub schema_version: String,
    pub capability_id: String,
    pub table_ordinal: usize,
    pub owner: CellCoordinate,
    pub recalculate: bool,
    pub cache_policy: FormulaCachePolicy,
    pub target_formula: FormulaCellDraft,
    pub expected_header_sha256: String,
    pub expected_section_sha256: String,
    pub expected_table_content_sha256: String,
    pub expected_source_formula_sha256: String,
    pub expected_selected_unowned_sha256: String,
    pub expected_pagination_policy_sha256: String,
    pub expected_source_table_count: usize,
    pub expected_formula_field_count: usize,
    pub expected_document_flow_sha256: String,
    pub target_document_flow_sha256: String,
}

impl fmt::Debug for TableAbsoluteReferenceHwpxRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableAbsoluteReferenceHwpxRequestDraft")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("table_ordinal", &self.table_ordinal)
            .field("owner", &self.owner)
            .field("recalculate", &self.recalculate)
            .field("cache_policy", &self.cache_policy)
            .field("target_formula", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableAbsoluteReferenceHwpxRequest {
    schema_version: &'static str,
    capability_id: &'static str,
    table_ordinal: usize,
    owner: CellCoordinate,
    recalculate: bool,
    cache_policy: FormulaCachePolicy,
    expected_header_sha256: String,
    expected_section_sha256: String,
    expected_table_content_sha256: String,
    expected_source_formula_sha256: String,
    expected_selected_unowned_sha256: String,
    expected_pagination_policy_sha256: String,
    expected_source_table_count: usize,
    expected_formula_field_count: usize,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    target_formula: FormulaCell,
}

impl TableAbsoluteReferenceHwpxRequest {
    /// Admits one exact relative-to-absolute reference transition bound to source and flow state.
    ///
    /// # Errors
    ///
    /// Rejects schema, source, formula, cache-policy, reference-transition, flow, or finite-limit
    /// drift.
    pub fn from_draft(
        draft: TableAbsoluteReferenceHwpxRequestDraft,
        source: &TableAbsoluteReferenceHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableAbsoluteReferenceHwpxLimits,
    ) -> Result<Self, TableAbsoluteReferenceHwpxError> {
        if draft.schema_version != TABLE_ABSOLUTE_REFERENCE_HWPX_SCHEMA_VERSION
            || draft.capability_id != TABLE_ABSOLUTE_REFERENCE_CAPABILITY_ID
        {
            return Err(TableAbsoluteReferenceHwpxError::UnsupportedVersion);
        }
        require_digests(&draft, current_document_flow_sha256)?;
        let target_formula = FormulaCell::from_draft(
            draft.target_formula,
            FormulaGridDimensions {
                rows: source.rows,
                columns: source.columns,
            },
            limits.formula,
        )?;
        let request = Self {
            schema_version: TABLE_ABSOLUTE_REFERENCE_HWPX_SCHEMA_VERSION,
            capability_id: TABLE_ABSOLUTE_REFERENCE_CAPABILITY_ID,
            table_ordinal: draft.table_ordinal,
            owner: draft.owner,
            recalculate: draft.recalculate,
            cache_policy: draft.cache_policy,
            expected_header_sha256: draft.expected_header_sha256,
            expected_section_sha256: draft.expected_section_sha256,
            expected_table_content_sha256: draft.expected_table_content_sha256,
            expected_source_formula_sha256: draft.expected_source_formula_sha256,
            expected_selected_unowned_sha256: draft.expected_selected_unowned_sha256,
            expected_pagination_policy_sha256: draft.expected_pagination_policy_sha256,
            expected_source_table_count: draft.expected_source_table_count,
            expected_formula_field_count: draft.expected_formula_field_count,
            expected_document_flow_sha256: draft.expected_document_flow_sha256,
            target_document_flow_sha256: draft.target_document_flow_sha256,
            target_formula,
        };
        validate_request_source(&request, source, current_document_flow_sha256, &limits)?;
        let _ = TableAbsoluteReferenceHwpxBuilder::build(
            &request,
            source,
            current_document_flow_sha256,
            limits,
        )?;
        let _ = request.canonical_json(limits)?;
        Ok(request)
    }

    /// Parses strict bounded JSON and repeats full admission.
    ///
    /// # Errors
    ///
    /// Rejects empty, oversized, duplicate-key, unknown-field, malformed, or invalid requests.
    pub fn from_json(
        bytes: &[u8],
        source: &TableAbsoluteReferenceHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableAbsoluteReferenceHwpxLimits,
    ) -> Result<Self, TableAbsoluteReferenceHwpxError> {
        if bytes.is_empty() || bytes.len() > serialized_limit(&limits) {
            return Err(TableAbsoluteReferenceHwpxError::InputLimit);
        }
        create_hwpx::reject_duplicate_json_keys(bytes)
            .map_err(|_| TableAbsoluteReferenceHwpxError::InvalidJson)?;
        let draft = serde_json::from_slice(bytes)
            .map_err(|_| TableAbsoluteReferenceHwpxError::InvalidJson)?;
        Self::from_draft(draft, source, current_document_flow_sha256, limits)
    }

    #[must_use]
    pub const fn target_formula(&self) -> &FormulaCell {
        &self.target_formula
    }

    #[must_use]
    pub const fn cache_policy(&self) -> FormulaCachePolicy {
        self.cache_policy
    }

    /// Serializes every binding under a finite deterministic limit.
    ///
    /// # Errors
    ///
    /// Rejects serialization or output-limit failure.
    pub fn canonical_json(
        &self,
        limits: TableAbsoluteReferenceHwpxLimits,
    ) -> Result<Vec<u8>, TableAbsoluteReferenceHwpxError> {
        serialize_bounded(self, serialized_limit(&limits))
    }

    /// Hashes the canonical bounded request.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failure.
    pub fn canonical_sha256(
        &self,
        limits: TableAbsoluteReferenceHwpxLimits,
    ) -> Result<[u8; 32], TableAbsoluteReferenceHwpxError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TableAbsoluteReferenceHwpxRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableAbsoluteReferenceHwpxRequest")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("table_ordinal", &self.table_ordinal)
            .field("owner", &self.owner)
            .field("recalculate", &self.recalculate)
            .field("cache_policy", &self.cache_policy)
            .field("target_formula", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableAbsoluteReferenceHwpxPlan {
    schema_version: &'static str,
    capability_id: &'static str,
    request_sha256: String,
    source_formula_sha256: String,
    target_formula_sha256: String,
    selected_unowned_sha256: String,
    pagination_policy_sha256: String,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    source_table_count: usize,
    formula_field_count: usize,
    changed_axis_count: usize,
    semantic_change: bool,
    cache_policy: FormulaCachePolicy,
    target_formula: FormulaCell,
}

impl TableAbsoluteReferenceHwpxPlan {
    #[must_use]
    pub const fn target_formula(&self) -> &FormulaCell {
        &self.target_formula
    }

    #[must_use]
    pub const fn changed_axis_count(&self) -> usize {
        self.changed_axis_count
    }

    #[must_use]
    pub const fn semantic_change(&self) -> bool {
        self.semantic_change
    }

    /// Serializes the complete target and integrity bindings under finite limits.
    ///
    /// # Errors
    ///
    /// Rejects serialization or output-limit failure.
    pub fn canonical_json(
        &self,
        limits: TableAbsoluteReferenceHwpxLimits,
    ) -> Result<Vec<u8>, TableAbsoluteReferenceHwpxError> {
        serialize_bounded(self, serialized_limit(&limits))
    }

    /// Hashes the canonical bounded plan.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failure.
    pub fn canonical_sha256(
        &self,
        limits: TableAbsoluteReferenceHwpxLimits,
    ) -> Result<[u8; 32], TableAbsoluteReferenceHwpxError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TableAbsoluteReferenceHwpxPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableAbsoluteReferenceHwpxPlan")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("source_table_count", &self.source_table_count)
            .field("formula_field_count", &self.formula_field_count)
            .field("changed_axis_count", &self.changed_axis_count)
            .field("semantic_change", &self.semantic_change)
            .field("cache_policy", &self.cache_policy)
            .field("target_formula", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct TableAbsoluteReferenceHwpxBuilder;

impl TableAbsoluteReferenceHwpxBuilder {
    /// Revalidates the complete source and builds one deterministic target plan.
    ///
    /// # Errors
    ///
    /// Rejects source, reference, cache, flow, or request drift.
    pub fn build(
        request: &TableAbsoluteReferenceHwpxRequest,
        source: &TableAbsoluteReferenceHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableAbsoluteReferenceHwpxLimits,
    ) -> Result<TableAbsoluteReferenceHwpxPlan, TableAbsoluteReferenceHwpxError> {
        validate_request_source(request, source, current_document_flow_sha256, &limits)?;
        let changed_axis_count = validate_transition(
            &source.formula,
            &request.target_formula,
            request.cache_policy,
            request.recalculate,
        )?;
        let semantic_change = source.formula != request.target_formula;
        if semantic_change
            == (request.expected_document_flow_sha256 == request.target_document_flow_sha256)
        {
            return Err(TableAbsoluteReferenceHwpxError::FlowBindingMismatch);
        }
        let plan = TableAbsoluteReferenceHwpxPlan {
            schema_version: TABLE_ABSOLUTE_REFERENCE_HWPX_SCHEMA_VERSION,
            capability_id: TABLE_ABSOLUTE_REFERENCE_CAPABILITY_ID,
            request_sha256: create_hwpx::hex(request.canonical_sha256(limits)?),
            source_formula_sha256: create_hwpx::hex(source.selected_formula_sha256),
            target_formula_sha256: create_hwpx::hex(
                request.target_formula.canonical_sha256(limits.formula)?,
            ),
            selected_unowned_sha256: create_hwpx::hex(source.selected_unowned_sha256),
            pagination_policy_sha256: create_hwpx::hex(source.pagination_policy_sha256),
            expected_document_flow_sha256: request.expected_document_flow_sha256.clone(),
            target_document_flow_sha256: request.target_document_flow_sha256.clone(),
            source_table_count: source.source_table_count,
            formula_field_count: source.formula_field_count,
            changed_axis_count,
            semantic_change,
            cache_policy: request.cache_policy,
            target_formula: request.target_formula.clone(),
        };
        let _ = plan.canonical_json(limits)?;
        Ok(plan)
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableAbsoluteReferenceHwpxLoweringReceipt {
    pub profile_id: &'static str,
    pub source_header_sha256: [u8; 32],
    pub output_header_sha256: [u8; 32],
    pub source_section_sha256: [u8; 32],
    pub output_section_sha256: [u8; 32],
    pub source_formula_sha256: [u8; 32],
    pub target_formula_sha256: [u8; 32],
    pub selected_unowned_sha256: [u8; 32],
    pub pagination_policy_sha256: [u8; 32],
    pub request_sha256: [u8; 32],
    pub plan_sha256: [u8; 32],
    pub before_document_flow_sha256: [u8; 32],
    pub after_document_flow_sha256: [u8; 32],
    pub source_table_count: usize,
    pub target_table_count: usize,
    pub formula_field_count: usize,
    pub changed_axis_count: usize,
    pub modified_text_count: usize,
    pub semantic_change: bool,
    pub cache_policy: FormulaCachePolicy,
}

impl fmt::Debug for TableAbsoluteReferenceHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableAbsoluteReferenceHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field("source_table_count", &self.source_table_count)
            .field("target_table_count", &self.target_table_count)
            .field("formula_field_count", &self.formula_field_count)
            .field("changed_axis_count", &self.changed_axis_count)
            .field("modified_text_count", &self.modified_text_count)
            .field("semantic_change", &self.semantic_change)
            .field("cache_policy", &self.cache_policy)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableAbsoluteReferenceHwpxLoweredParts {
    pub header: Vec<u8>,
    pub section: Vec<u8>,
    pub receipt: TableAbsoluteReferenceHwpxLoweringReceipt,
}

impl fmt::Debug for TableAbsoluteReferenceHwpxLoweredParts {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableAbsoluteReferenceHwpxLoweredParts")
            .field("header_bytes", &self.header.len())
            .field("section_bytes", &self.section.len())
            .field("receipt", &self.receipt)
            .finish()
    }
}

#[derive(Debug)]
pub struct TableAbsoluteReferenceHwpxLowerer;

impl TableAbsoluteReferenceHwpxLowerer {
    /// Relifts, rebuilds and lowers one bound absolute-reference operation, then reopens it.
    ///
    /// # Errors
    ///
    /// Rejects source, request, plan, formula, pagination, preservation, flow, or readback drift
    /// without returning partial parts.
    pub fn lower(
        header: &[u8],
        section: &[u8],
        current_document_flow_sha256: &str,
        request: &TableAbsoluteReferenceHwpxRequest,
        plan: &TableAbsoluteReferenceHwpxPlan,
        limits: TableAbsoluteReferenceHwpxLimits,
    ) -> Result<TableAbsoluteReferenceHwpxLoweredParts, TableAbsoluteReferenceHwpxError> {
        let source = TableAbsoluteReferenceHwpxReader::read_context(
            header,
            section,
            request.table_ordinal,
            request.owner,
            limits,
        )?;
        let rebuilt = TableAbsoluteReferenceHwpxBuilder::build(
            request,
            &source,
            current_document_flow_sha256,
            limits,
        )?;
        if rebuilt != *plan {
            return Err(TableAbsoluteReferenceHwpxError::PlanBindingMismatch);
        }
        if header.len() > limits.native.config().output_bytes {
            return Err(TableAbsoluteReferenceHwpxError::OutputLimit);
        }
        let output_header = header.to_vec();
        let (output_section, modified_text_count) = if plan.semantic_change {
            let (output, receipt) =
                TableFormulaHwpxLowerer::lower_canonical_cell_in_section_with_receipt(
                    section,
                    request.table_ordinal,
                    request.owner,
                    &plan.target_formula,
                    FormulaGridDimensions {
                        rows: source.rows,
                        columns: source.columns,
                    },
                    limits.native,
                    limits.formula,
                )?;
            if receipt.unowned_sha256 != source.selected_unowned_sha256 {
                return Err(TableAbsoluteReferenceHwpxError::PreservationMismatch);
            }
            (output, receipt.modified_text_count)
        } else {
            (section.to_vec(), 0)
        };
        let reopened = TableAbsoluteReferenceHwpxReader::read_context(
            &output_header,
            &output_section,
            request.table_ordinal,
            request.owner,
            limits,
        )?;
        if reopened.formula != plan.target_formula
            || reopened.selected_unowned_sha256 != source.selected_unowned_sha256
            || !same_pagination_policy(&source.pagination, &reopened.pagination)
            || reopened.source_table_count != source.source_table_count
            || reopened.formula_field_count != source.formula_field_count
            || reopened.header_sha256 != source.header_sha256
        {
            return Err(TableAbsoluteReferenceHwpxError::ReadbackMismatch);
        }
        let receipt = TableAbsoluteReferenceHwpxLoweringReceipt {
            profile_id: TABLE_ABSOLUTE_REFERENCE_HWPX_PROFILE_ID,
            source_header_sha256: source.header_sha256,
            output_header_sha256: reopened.header_sha256,
            source_section_sha256: source.section_sha256,
            output_section_sha256: reopened.section_sha256,
            source_formula_sha256: source.selected_formula_sha256,
            target_formula_sha256: reopened.selected_formula_sha256,
            selected_unowned_sha256: reopened.selected_unowned_sha256,
            pagination_policy_sha256: reopened.pagination_policy_sha256,
            request_sha256: request.canonical_sha256(limits)?,
            plan_sha256: plan.canonical_sha256(limits)?,
            before_document_flow_sha256: parse_digest(&request.expected_document_flow_sha256)?,
            after_document_flow_sha256: parse_digest(&request.target_document_flow_sha256)?,
            source_table_count: source.source_table_count,
            target_table_count: reopened.source_table_count,
            formula_field_count: reopened.formula_field_count,
            changed_axis_count: plan.changed_axis_count,
            modified_text_count,
            semantic_change: plan.semantic_change,
            cache_policy: plan.cache_policy,
        };
        Ok(TableAbsoluteReferenceHwpxLoweredParts {
            header: output_header,
            section: output_section,
            receipt,
        })
    }
}

#[derive(Debug, Error)]
pub enum TableAbsoluteReferenceHwpxError {
    #[error("unsupported table absolute-reference HWPX schema version")]
    UnsupportedVersion,
    #[error("table absolute-reference HWPX input exceeds a finite bound")]
    InputLimit,
    #[error("invalid table absolute-reference HWPX JSON")]
    InvalidJson,
    #[error("table absolute-reference HWPX source or flow drifted")]
    SourceBindingMismatch,
    #[error("table absolute-reference HWPX transition changes more than reference anchors")]
    InvalidReferenceTransition,
    #[error("table absolute-reference HWPX target cache does not match its policy")]
    CachePolicyMismatch,
    #[error("table absolute-reference HWPX direct profile cannot recalculate formulas")]
    UnsupportedRecalculate,
    #[error("table absolute-reference HWPX document-flow transition drifted")]
    FlowBindingMismatch,
    #[error("table absolute-reference HWPX plan drifted")]
    PlanBindingMismatch,
    #[error("table absolute-reference HWPX unowned bytes changed")]
    PreservationMismatch,
    #[error("table absolute-reference HWPX semantic readback mismatched")]
    ReadbackMismatch,
    #[error("table absolute-reference HWPX allocation failed")]
    Allocation,
    #[error("table absolute-reference HWPX serialization failed")]
    Serialization,
    #[error("table absolute-reference HWPX output exceeds a finite bound")]
    OutputLimit,
    #[error(transparent)]
    Formula(#[from] domain_ir::FormulaError),
    #[error(transparent)]
    Native(#[from] TableFormulaHwpxError),
    #[error(transparent)]
    Layout(#[from] TableLayoutHwpxError),
    #[error(transparent)]
    Pagination(#[from] TablePaginationHwpxError),
}

impl TableAbsoluteReferenceHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::UnsupportedVersion => "table_absolute_reference_hwpx_unsupported_version",
            Self::InputLimit => "table_absolute_reference_hwpx_input_limit",
            Self::InvalidJson => "table_absolute_reference_hwpx_invalid_json",
            Self::SourceBindingMismatch => "table_absolute_reference_hwpx_source_binding_mismatch",
            Self::InvalidReferenceTransition => {
                "table_absolute_reference_hwpx_invalid_reference_transition"
            }
            Self::CachePolicyMismatch => "table_absolute_reference_hwpx_cache_policy_mismatch",
            Self::UnsupportedRecalculate => "table_absolute_reference_hwpx_unsupported_recalculate",
            Self::FlowBindingMismatch => "table_absolute_reference_hwpx_flow_binding_mismatch",
            Self::PlanBindingMismatch => "table_absolute_reference_hwpx_plan_binding_mismatch",
            Self::PreservationMismatch => "table_absolute_reference_hwpx_preservation_mismatch",
            Self::ReadbackMismatch => "table_absolute_reference_hwpx_readback_mismatch",
            Self::Allocation => "table_absolute_reference_hwpx_allocation",
            Self::Serialization => "table_absolute_reference_hwpx_serialization",
            Self::OutputLimit => "table_absolute_reference_hwpx_output_limit",
            Self::Formula(_) => "table_absolute_reference_hwpx_formula",
            Self::Native(_) => "table_absolute_reference_hwpx_native_formula",
            Self::Layout(_) => "table_absolute_reference_hwpx_layout",
            Self::Pagination(_) => "table_absolute_reference_hwpx_pagination",
        }
    }
}

fn require_digests(
    draft: &TableAbsoluteReferenceHwpxRequestDraft,
    current_document_flow_sha256: &str,
) -> Result<(), TableAbsoluteReferenceHwpxError> {
    for digest in [
        &draft.expected_header_sha256,
        &draft.expected_section_sha256,
        &draft.expected_table_content_sha256,
        &draft.expected_source_formula_sha256,
        &draft.expected_selected_unowned_sha256,
        &draft.expected_pagination_policy_sha256,
        &draft.expected_document_flow_sha256,
        &draft.target_document_flow_sha256,
        current_document_flow_sha256,
    ] {
        create_hwpx::require_digest(digest)
            .map_err(|_| TableAbsoluteReferenceHwpxError::SourceBindingMismatch)?;
    }
    Ok(())
}

fn validate_request_source(
    request: &TableAbsoluteReferenceHwpxRequest,
    source: &TableAbsoluteReferenceHwpxReadback,
    current_document_flow_sha256: &str,
    limits: &TableAbsoluteReferenceHwpxLimits,
) -> Result<(), TableAbsoluteReferenceHwpxError> {
    create_hwpx::require_digest(current_document_flow_sha256)
        .map_err(|_| TableAbsoluteReferenceHwpxError::SourceBindingMismatch)?;
    if source.profile_id != TABLE_ABSOLUTE_REFERENCE_HWPX_PROFILE_ID
        || request.table_ordinal != source.table_ordinal
        || request.owner != source.owner
        || request.expected_header_sha256 != create_hwpx::hex(source.header_sha256)
        || request.expected_section_sha256 != create_hwpx::hex(source.section_sha256)
        || request.expected_table_content_sha256 != create_hwpx::hex(source.table_content_sha256)
        || request.expected_source_formula_sha256
            != create_hwpx::hex(source.selected_formula_sha256)
        || request.expected_selected_unowned_sha256
            != create_hwpx::hex(source.selected_unowned_sha256)
        || request.expected_pagination_policy_sha256
            != create_hwpx::hex(source.pagination_policy_sha256)
        || request.expected_source_table_count != source.source_table_count
        || request.expected_formula_field_count != source.formula_field_count
        || request.expected_document_flow_sha256 != current_document_flow_sha256
        || request.target_formula.owner() != source.owner
        || request.target_formula.number_format() != FormulaNumberFormat::General
    {
        return Err(TableAbsoluteReferenceHwpxError::SourceBindingMismatch);
    }
    let _ = request.target_formula.canonical_sha256(limits.formula)?;
    let _ = validate_transition(
        &source.formula,
        &request.target_formula,
        request.cache_policy,
        request.recalculate,
    )?;
    Ok(())
}

fn validate_transition(
    source: &FormulaCell,
    target: &FormulaCell,
    cache_policy: FormulaCachePolicy,
    recalculate: bool,
) -> Result<usize, TableAbsoluteReferenceHwpxError> {
    if recalculate {
        return Err(TableAbsoluteReferenceHwpxError::UnsupportedRecalculate);
    }
    if source.owner() != target.owner()
        || source.number_format() != FormulaNumberFormat::General
        || target.number_format() != FormulaNumberFormat::General
    {
        return Err(TableAbsoluteReferenceHwpxError::InvalidReferenceTransition);
    }
    let changed_axis_count =
        reference_upgrade_count(source.ast().expression(), target.ast().expression())?;
    if changed_axis_count == 0 && source != target {
        return Err(TableAbsoluteReferenceHwpxError::InvalidReferenceTransition);
    }
    if !expression_has_absolute_axis(target.ast().expression()) {
        return Err(TableAbsoluteReferenceHwpxError::InvalidReferenceTransition);
    }
    match cache_policy {
        FormulaCachePolicy::Preserve if source.cache() == target.cache() => {}
        FormulaCachePolicy::Clear if target.cache() == &FormulaCache::Absent => {}
        FormulaCachePolicy::Update
            if matches!(
                target.cache(),
                FormulaCache::Unverified {
                    value: FormulaValue::Decimal { .. }
                }
            ) => {}
        _ => return Err(TableAbsoluteReferenceHwpxError::CachePolicyMismatch),
    }
    Ok(changed_axis_count)
}

fn reference_upgrade_count(
    source: &FormulaExpression,
    target: &FormulaExpression,
) -> Result<usize, TableAbsoluteReferenceHwpxError> {
    match (source, target) {
        (
            FormulaExpression::Decimal { value: source },
            FormulaExpression::Decimal { value: target },
        ) if source == target => Ok(0),
        (
            FormulaExpression::Cell { reference: source },
            FormulaExpression::Cell { reference: target },
        ) => reference_axis_upgrade_count(*source, *target),
        (
            FormulaExpression::Range { range: source },
            FormulaExpression::Range { range: target },
        ) => reference_axis_upgrade_count(source.start, target.start)?
            .checked_add(reference_axis_upgrade_count(source.end, target.end)?)
            .ok_or(TableAbsoluteReferenceHwpxError::Allocation),
        (
            FormulaExpression::Unary {
                operator: source_operator,
                operand: source_operand,
            },
            FormulaExpression::Unary {
                operator: target_operator,
                operand: target_operand,
            },
        ) if source_operator == target_operator => {
            reference_upgrade_count(source_operand, target_operand)
        }
        (
            FormulaExpression::Binary {
                operator: source_operator,
                left: source_left,
                right: source_right,
            },
            FormulaExpression::Binary {
                operator: target_operator,
                left: target_left,
                right: target_right,
            },
        ) if source_operator == target_operator => {
            reference_upgrade_count(source_left, target_left)?
                .checked_add(reference_upgrade_count(source_right, target_right)?)
                .ok_or(TableAbsoluteReferenceHwpxError::Allocation)
        }
        (
            FormulaExpression::Function {
                function: source_function,
                arguments: source_arguments,
            },
            FormulaExpression::Function {
                function: target_function,
                arguments: target_arguments,
            },
        ) if source_function == target_function
            && source_arguments.len() == target_arguments.len() =>
        {
            source_arguments.iter().zip(target_arguments).try_fold(
                0_usize,
                |total, (source, target)| {
                    total
                        .checked_add(reference_upgrade_count(source, target)?)
                        .ok_or(TableAbsoluteReferenceHwpxError::Allocation)
                },
            )
        }
        _ => Err(TableAbsoluteReferenceHwpxError::InvalidReferenceTransition),
    }
}

fn reference_axis_upgrade_count(
    source: domain_ir::FormulaCellReference,
    target: domain_ir::FormulaCellReference,
) -> Result<usize, TableAbsoluteReferenceHwpxError> {
    if source.row != target.row || source.column != target.column {
        return Err(TableAbsoluteReferenceHwpxError::InvalidReferenceTransition);
    }
    let row = axis_upgrade(source.row_kind, target.row_kind)?;
    let column = axis_upgrade(source.column_kind, target.column_kind)?;
    row.checked_add(column)
        .ok_or(TableAbsoluteReferenceHwpxError::Allocation)
}

fn axis_upgrade(
    source: FormulaReferenceKind,
    target: FormulaReferenceKind,
) -> Result<usize, TableAbsoluteReferenceHwpxError> {
    match (source, target) {
        (left, right) if left == right => Ok(0),
        (FormulaReferenceKind::Relative, FormulaReferenceKind::Absolute) => Ok(1),
        _ => Err(TableAbsoluteReferenceHwpxError::InvalidReferenceTransition),
    }
}

fn expression_has_absolute_axis(expression: &FormulaExpression) -> bool {
    match expression {
        FormulaExpression::Decimal { .. } => false,
        FormulaExpression::Cell { reference } => reference_has_absolute_axis(*reference),
        FormulaExpression::Range { range } => {
            reference_has_absolute_axis(range.start) || reference_has_absolute_axis(range.end)
        }
        FormulaExpression::Unary { operand, .. } => expression_has_absolute_axis(operand),
        FormulaExpression::Binary { left, right, .. } => {
            expression_has_absolute_axis(left) || expression_has_absolute_axis(right)
        }
        FormulaExpression::Function { arguments, .. } => {
            arguments.iter().any(expression_has_absolute_axis)
        }
    }
}

fn reference_has_absolute_axis(reference: domain_ir::FormulaCellReference) -> bool {
    reference.row_kind == FormulaReferenceKind::Absolute
        || reference.column_kind == FormulaReferenceKind::Absolute
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
    digest.update(b"hwpx-agent.table-absolute-reference-pagination/v1\0");
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

fn cache_state(value: &FormulaCache) -> &'static str {
    match value {
        FormulaCache::Absent => "absent",
        FormulaCache::Unverified { .. } => "unverified",
    }
}

fn serialized_limit(limits: &TableAbsoluteReferenceHwpxLimits) -> usize {
    limits
        .formula
        .config()
        .serialized_bytes
        .min(limits.native.config().output_bytes)
        .min(limits.layout.config().input_bytes)
}

fn serialize_bounded<T: Serialize + ?Sized>(
    value: &T,
    maximum: usize,
) -> Result<Vec<u8>, TableAbsoluteReferenceHwpxError> {
    let bytes =
        serde_json::to_vec(value).map_err(|_| TableAbsoluteReferenceHwpxError::Serialization)?;
    if bytes.len() > maximum {
        return Err(TableAbsoluteReferenceHwpxError::OutputLimit);
    }
    Ok(bytes)
}

fn parse_digest(value: &str) -> Result<[u8; 32], TableAbsoluteReferenceHwpxError> {
    create_hwpx::require_digest(value)
        .map_err(|_| TableAbsoluteReferenceHwpxError::SourceBindingMismatch)?;
    let mut output = [0_u8; 32];
    for (index, chunk) in value.as_bytes().chunks_exact(2).enumerate() {
        let text = std::str::from_utf8(chunk)
            .map_err(|_| TableAbsoluteReferenceHwpxError::SourceBindingMismatch)?;
        output[index] = u8::from_str_radix(text, 16)
            .map_err(|_| TableAbsoluteReferenceHwpxError::SourceBindingMismatch)?;
    }
    Ok(output)
}
