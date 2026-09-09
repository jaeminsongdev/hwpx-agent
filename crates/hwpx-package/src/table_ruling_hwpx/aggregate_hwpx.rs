use std::collections::BTreeSet;
use std::fmt;

use domain_ir::{
    FormulaAstDraft, FormulaCache, FormulaCell, FormulaCellDraft, FormulaError,
    FormulaGridDimensions, FormulaNumberFormat, TABLE_FORMULA_SCHEMA_VERSION,
    TABLE_RULING_SCHEMA_VERSION, TableAggregateBuilder, TableAggregateError, TableAggregatePlan,
    TableAggregateRequest, TableAggregateRequestDraft, TableGrid, TableGridError,
    TableRulingCellDraft, TableRulingError, TableRulingState, TableRulingStateDraft,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use super::{
    TableRulingHwpxBinding, TableRulingHwpxError, TableRulingHwpxLimits, TableRulingHwpxReadback,
    TableRulingHwpxReader,
};
use crate::{
    TableFormulaHwpxError, TableFormulaHwpxLowerer, TableLayoutHwpxError, TablePaginationHwpxError,
    TablePaginationHwpxLimits, TablePaginationHwpxReadback, TablePaginationHwpxReader,
};

pub const TABLE_AGGREGATE_HWPX_SCHEMA_VERSION: &str = "hwpx-agent.table-aggregate-hwpx/v1";
pub const TABLE_AGGREGATE_HWPX_PROFILE_ID: &str =
    "hwpx-agent.table-aggregate-hwpx.hancom-2020-wrapper/1";

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TableAggregateHwpxLimits {
    pub ruling: TableRulingHwpxLimits,
    pub pagination: TablePaginationHwpxLimits,
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableAggregateHwpxReadback {
    pub profile_id: &'static str,
    pub table_ordinal: usize,
    pub ruling: TableRulingHwpxReadback,
    pub pagination: TablePaginationHwpxReadback,
}

impl fmt::Debug for TableAggregateHwpxReadback {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableAggregateHwpxReadback")
            .field("profile_id", &self.profile_id)
            .field("table_ordinal", &self.table_ordinal)
            .field("rows", &self.ruling.grid.rows())
            .field("columns", &self.ruling.grid.columns())
            .field("master_cell_count", &self.ruling.grid.master_cell_count())
            .field("formula_count", &self.ruling.formula_count)
            .field("page_split", &self.pagination.page_split)
            .field("repeat_header_rows", &self.pagination.repeat_header_rows)
            .field("has_caption", &self.pagination.caption.is_some())
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct TableAggregateHwpxReader;

impl TableAggregateHwpxReader {
    /// Reads one exact current-Hangul-2020 table while preserving pagination and caption state.
    ///
    /// The profile admits either no formula or one explicit `SUM`, `AVG`, or `PRODUCT` A1 range
    /// formula. Merged cells and other formula shapes remain outside this adapter.
    ///
    /// # Errors
    ///
    /// Rejects malformed, ambiguous, merged, over-limit or non-profile tables and bindings.
    pub fn read_existing(
        header: &[u8],
        section: &[u8],
        table_ordinal: usize,
        binding: &TableRulingHwpxBinding,
        limits: TableAggregateHwpxLimits,
    ) -> Result<TableAggregateHwpxReadback, TableAggregateHwpxError> {
        let ruling = TableRulingHwpxReader::read_existing_aggregate_preserving_caption(
            header,
            section,
            table_ordinal,
            binding,
            &limits.ruling,
        )?;
        require_unmerged(&ruling.grid)?;
        let pagination =
            TablePaginationHwpxReader::read_in_section(section, table_ordinal, limits.pagination)?;
        if pagination.row_count != ruling.grid.rows()
            || pagination.column_count != ruling.grid.columns()
        {
            return Err(TableAggregateHwpxError::ReadbackMismatch);
        }
        Ok(TableAggregateHwpxReadback {
            profile_id: TABLE_AGGREGATE_HWPX_PROFILE_ID,
            table_ordinal,
            ruling,
            pagination,
        })
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableAggregateHwpxRequestDraft {
    pub schema_version: String,
    pub table_ordinal: usize,
    pub expected_header_sha256: String,
    pub expected_section_sha256: String,
    pub expected_source_state_sha256: String,
    pub expected_source_grid_sha256: String,
    pub expected_document_flow_sha256: String,
    pub target_document_flow_sha256: String,
    pub aggregate: TableAggregateRequestDraft,
    pub target_cache: FormulaCache,
}

impl fmt::Debug for TableAggregateHwpxRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableAggregateHwpxRequestDraft")
            .field("schema_version", &self.schema_version)
            .field("table_ordinal", &self.table_ordinal)
            .field("expected_header_sha256", &"<redacted>")
            .field("expected_section_sha256", &"<redacted>")
            .field("expected_source_state_sha256", &"<redacted>")
            .field("expected_source_grid_sha256", &"<redacted>")
            .field("expected_document_flow_sha256", &"<redacted>")
            .field("target_document_flow_sha256", &"<redacted>")
            .field("aggregate", &self.aggregate)
            .field("target_cache", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableAggregateHwpxRequest {
    schema_version: &'static str,
    capability_id: &'static str,
    table_ordinal: usize,
    expected_header_sha256: String,
    expected_section_sha256: String,
    expected_source_state_sha256: String,
    expected_source_grid_sha256: String,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    aggregate: TableAggregateRequest,
    target_cache: FormulaCache,
}

impl TableAggregateHwpxRequest {
    /// Admits one aggregate insertion bound to exact source parts, state, grid and flow.
    ///
    /// # Errors
    ///
    /// Rejects schema, digest, part, state, grid, flow, destination, cache or profile drift.
    pub fn from_draft(
        draft: TableAggregateHwpxRequestDraft,
        source: &TableAggregateHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableAggregateHwpxLimits,
    ) -> Result<Self, TableAggregateHwpxError> {
        if draft.schema_version != TABLE_AGGREGATE_HWPX_SCHEMA_VERSION {
            return Err(TableAggregateHwpxError::UnsupportedVersion);
        }
        for digest in [
            &draft.expected_header_sha256,
            &draft.expected_section_sha256,
            &draft.expected_source_state_sha256,
            &draft.expected_source_grid_sha256,
            &draft.expected_document_flow_sha256,
            &draft.target_document_flow_sha256,
            current_document_flow_sha256,
        ] {
            require_digest(digest)?;
        }
        if draft.expected_document_flow_sha256 == draft.target_document_flow_sha256 {
            return Err(TableAggregateHwpxError::InvalidBinding);
        }
        let dimensions = dimensions(&source.ruling.grid);
        let aggregate =
            TableAggregateRequest::from_draft(draft.aggregate, dimensions, limits.ruling.formula)?;
        let request = Self {
            schema_version: TABLE_AGGREGATE_HWPX_SCHEMA_VERSION,
            capability_id: aggregate.capability_id(),
            table_ordinal: draft.table_ordinal,
            expected_header_sha256: draft.expected_header_sha256,
            expected_section_sha256: draft.expected_section_sha256,
            expected_source_state_sha256: draft.expected_source_state_sha256,
            expected_source_grid_sha256: draft.expected_source_grid_sha256,
            expected_document_flow_sha256: draft.expected_document_flow_sha256,
            target_document_flow_sha256: draft.target_document_flow_sha256,
            aggregate,
            target_cache: draft.target_cache,
        };
        validate_request_source(&request, source, current_document_flow_sha256, &limits)?;
        let _ = TableAggregateHwpxBuilder::build(
            &request,
            source,
            current_document_flow_sha256,
            limits,
        )?;
        let _ = request.canonical_json(limits)?;
        Ok(request)
    }

    /// Parses bounded strict JSON and applies the same admission as [`Self::from_draft`].
    ///
    /// # Errors
    ///
    /// Rejects empty, oversized, malformed, duplicate, unknown or invalid input.
    pub fn from_json(
        bytes: &[u8],
        source: &TableAggregateHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableAggregateHwpxLimits,
    ) -> Result<Self, TableAggregateHwpxError> {
        if bytes.is_empty() || bytes.len() > limits.ruling.ruling.config().input_bytes {
            return Err(TableAggregateHwpxError::InputLimit);
        }
        reject_duplicate_json_keys(bytes)?;
        let draft =
            serde_json::from_slice(bytes).map_err(|_| TableAggregateHwpxError::InvalidJson)?;
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
    pub const fn aggregate(&self) -> &TableAggregateRequest {
        &self.aggregate
    }

    #[must_use]
    pub fn expected_document_flow_sha256(&self) -> &str {
        &self.expected_document_flow_sha256
    }

    #[must_use]
    pub fn target_document_flow_sha256(&self) -> &str {
        &self.target_document_flow_sha256
    }

    /// Serializes the complete typed request under the ruling bound.
    ///
    /// # Errors
    ///
    /// Rejects serialization or finite output failure.
    pub fn canonical_json(
        &self,
        limits: TableAggregateHwpxLimits,
    ) -> Result<Vec<u8>, TableAggregateHwpxError> {
        serialize_bounded(self, limits.ruling.ruling.config().serialized_bytes)
    }

    /// Hashes the bounded canonical request.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failure.
    pub fn canonical_sha256(
        &self,
        limits: TableAggregateHwpxLimits,
    ) -> Result<[u8; 32], TableAggregateHwpxError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TableAggregateHwpxRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableAggregateHwpxRequest")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("table_ordinal", &self.table_ordinal)
            .field("expected_header_sha256", &"<redacted>")
            .field("expected_section_sha256", &"<redacted>")
            .field("expected_source_state_sha256", &"<redacted>")
            .field("expected_source_grid_sha256", &"<redacted>")
            .field("expected_document_flow_sha256", &"<redacted>")
            .field("target_document_flow_sha256", &"<redacted>")
            .field("aggregate", &self.aggregate)
            .field("target_cache", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableAggregateHwpxPlan {
    schema_version: &'static str,
    capability_id: &'static str,
    request_sha256: String,
    source_state_sha256: String,
    target_state_sha256: String,
    source_grid_sha256: String,
    target_grid_sha256: String,
    source_pagination_sha256: String,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    domain: TableAggregatePlan,
    target_formula: FormulaCell,
    target_state: TableRulingState,
    #[serde(skip)]
    target_grid: TableGrid,
}

impl TableAggregateHwpxPlan {
    #[must_use]
    pub const fn domain(&self) -> &TableAggregatePlan {
        &self.domain
    }

    #[must_use]
    pub const fn target_formula(&self) -> &FormulaCell {
        &self.target_formula
    }

    #[must_use]
    pub const fn target_state(&self) -> &TableRulingState {
        &self.target_state
    }

    #[must_use]
    pub const fn target_grid(&self) -> &TableGrid {
        &self.target_grid
    }

    /// Serializes all semantic and integrity bindings under the ruling bound.
    ///
    /// # Errors
    ///
    /// Rejects serialization or finite output failure.
    pub fn canonical_json(
        &self,
        limits: TableAggregateHwpxLimits,
    ) -> Result<Vec<u8>, TableAggregateHwpxError> {
        serialize_bounded(self, limits.ruling.ruling.config().serialized_bytes)
    }

    /// Hashes the bounded canonical plan.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failure.
    pub fn canonical_sha256(
        &self,
        limits: TableAggregateHwpxLimits,
    ) -> Result<[u8; 32], TableAggregateHwpxError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TableAggregateHwpxPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableAggregateHwpxPlan")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("domain", &self.domain)
            .field("target_formula", &"<redacted>")
            .field("target_state", &self.target_state)
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct TableAggregateHwpxBuilder;

impl TableAggregateHwpxBuilder {
    /// Revalidates the exact source and builds one deterministic aggregate insertion plan.
    ///
    /// # Errors
    ///
    /// Rejects part, state, grid, flow, formula, cache, preservation or finite-bound drift.
    pub fn build(
        request: &TableAggregateHwpxRequest,
        source: &TableAggregateHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableAggregateHwpxLimits,
    ) -> Result<TableAggregateHwpxPlan, TableAggregateHwpxError> {
        validate_request_source(request, source, current_document_flow_sha256, &limits)?;
        let domain =
            TableAggregateBuilder::build(request.aggregate.clone(), limits.ruling.formula)?;
        let target_formula = FormulaCell::from_draft(
            FormulaCellDraft {
                schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
                owner: domain.formula().owner(),
                ast: FormulaAstDraft {
                    schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
                    expression: domain.formula().ast().expression().clone(),
                },
                cache: request.target_cache.clone(),
                number_format: FormulaNumberFormat::General,
            },
            dimensions(&source.ruling.grid),
            limits.ruling.formula,
        )?;
        let target_state = state_with_formula(
            &source.ruling.state,
            &source.ruling.grid,
            &target_formula,
            &limits,
        )?;
        let source_state_sha256 =
            hex(source.ruling.state.canonical_sha256(limits.ruling.ruling)?);
        let target_state_sha256 = hex(target_state.canonical_sha256(limits.ruling.ruling)?);
        let source_grid_sha256 = hex(source.ruling.grid.canonical_sha256()?);
        let source_pagination_sha256 = pagination_digest(&source.pagination);
        let plan = TableAggregateHwpxPlan {
            schema_version: TABLE_AGGREGATE_HWPX_SCHEMA_VERSION,
            capability_id: request.capability_id,
            request_sha256: hex(request.canonical_sha256(limits)?),
            source_state_sha256,
            target_state_sha256,
            source_grid_sha256: source_grid_sha256.clone(),
            target_grid_sha256: source_grid_sha256,
            source_pagination_sha256,
            expected_document_flow_sha256: request.expected_document_flow_sha256.clone(),
            target_document_flow_sha256: request.target_document_flow_sha256.clone(),
            domain,
            target_formula,
            target_state,
            target_grid: source.ruling.grid.clone(),
        };
        let _ = plan.canonical_json(limits)?;
        Ok(plan)
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableAggregateHwpxLoweringReceipt {
    pub profile_id: &'static str,
    pub source_header_sha256: [u8; 32],
    pub output_header_sha256: [u8; 32],
    pub source_section_sha256: [u8; 32],
    pub output_section_sha256: [u8; 32],
    pub source_state_sha256: [u8; 32],
    pub target_state_sha256: [u8; 32],
    pub source_grid_sha256: [u8; 32],
    pub target_grid_sha256: [u8; 32],
    pub target_formula_sha256: [u8; 32],
    pub request_sha256: [u8; 32],
    pub plan_sha256: [u8; 32],
    pub before_document_flow_sha256: [u8; 32],
    pub after_document_flow_sha256: [u8; 32],
    pub preserved_master_cell_count: usize,
    pub preserved_payload_block_count: usize,
    pub preserved_edge_count: usize,
    pub inserted_formula_field_count: usize,
    pub pagination_preserved: bool,
    pub caption_preserved: bool,
}

impl fmt::Debug for TableAggregateHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableAggregateHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field(
                "preserved_master_cell_count",
                &self.preserved_master_cell_count,
            )
            .field(
                "preserved_payload_block_count",
                &self.preserved_payload_block_count,
            )
            .field("preserved_edge_count", &self.preserved_edge_count)
            .field(
                "inserted_formula_field_count",
                &self.inserted_formula_field_count,
            )
            .field("pagination_preserved", &self.pagination_preserved)
            .field("caption_preserved", &self.caption_preserved)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableAggregateHwpxLoweredParts {
    pub header: Vec<u8>,
    pub section: Vec<u8>,
    pub binding: TableRulingHwpxBinding,
    pub receipt: TableAggregateHwpxLoweringReceipt,
}

impl fmt::Debug for TableAggregateHwpxLoweredParts {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableAggregateHwpxLoweredParts")
            .field("header_bytes", &self.header.len())
            .field("section_bytes", &self.section.len())
            .field("binding", &self.binding)
            .field("receipt", &self.receipt)
            .finish()
    }
}

#[derive(Debug)]
pub struct TableAggregateHwpxLowerer;

impl TableAggregateHwpxLowerer {
    /// Inserts one exact native range formula and returns only after complete semantic reopen.
    ///
    /// # Errors
    ///
    /// Rejects source, request, plan, state, grid, flow, native-shape or readback drift without
    /// returning partial parts.
    #[allow(clippy::too_many_arguments)]
    pub fn lower_existing(
        header: &[u8],
        section: &[u8],
        binding: &TableRulingHwpxBinding,
        current_document_flow_sha256: &str,
        request: &TableAggregateHwpxRequest,
        plan: &TableAggregateHwpxPlan,
        limits: TableAggregateHwpxLimits,
    ) -> Result<TableAggregateHwpxLoweredParts, TableAggregateHwpxError> {
        let source = TableAggregateHwpxReader::read_existing(
            header,
            section,
            request.table_ordinal,
            binding,
            limits,
        )?;
        validate_request_source(request, &source, current_document_flow_sha256, &limits)?;
        let rebuilt = TableAggregateHwpxBuilder::build(
            request,
            &source,
            current_document_flow_sha256,
            limits,
        )?;
        if rebuilt != *plan {
            return Err(TableAggregateHwpxError::PlanBindingMismatch);
        }
        let dimensions = dimensions(&source.ruling.grid);
        let (output_section, native_receipt) =
            TableFormulaHwpxLowerer::insert_aggregate_in_section(
                section,
                request.table_ordinal,
                plan.target_formula(),
                dimensions,
                limits.ruling.formula_hwpx,
                limits.ruling.formula,
            )?;
        let reopened = TableAggregateHwpxReader::read_existing(
            header,
            &output_section,
            request.table_ordinal,
            binding,
            limits,
        )?;
        let expected_source_section_sha256: [u8; 32] = Sha256::digest(section).into();
        let expected_output_section_sha256: [u8; 32] = Sha256::digest(&output_section).into();
        if reopened.ruling.grid != *plan.target_grid()
            || reopened.ruling.state != *plan.target_state()
            || !same_pagination_semantics(&reopened.pagination, &source.pagination)
            || reopened.ruling.formula_count != 1
            || native_receipt.owner != plan.target_formula().owner()
            || native_receipt.target_formula_sha256
                != plan
                    .target_formula()
                    .canonical_sha256(limits.ruling.formula)?
            || native_receipt.source_sha256 != expected_source_section_sha256
            || native_receipt.output_sha256 != expected_output_section_sha256
        {
            return Err(TableAggregateHwpxError::ReadbackMismatch);
        }
        let receipt = TableAggregateHwpxLoweringReceipt {
            profile_id: TABLE_AGGREGATE_HWPX_PROFILE_ID,
            source_header_sha256: Sha256::digest(header).into(),
            output_header_sha256: Sha256::digest(header).into(),
            source_section_sha256: Sha256::digest(section).into(),
            output_section_sha256: Sha256::digest(&output_section).into(),
            source_state_sha256: source.ruling.state.canonical_sha256(limits.ruling.ruling)?,
            target_state_sha256: plan.target_state().canonical_sha256(limits.ruling.ruling)?,
            source_grid_sha256: source.ruling.grid.canonical_sha256()?,
            target_grid_sha256: plan.target_grid().canonical_sha256()?,
            target_formula_sha256: plan
                .target_formula()
                .canonical_sha256(limits.ruling.formula)?,
            request_sha256: request.canonical_sha256(limits)?,
            plan_sha256: plan.canonical_sha256(limits)?,
            before_document_flow_sha256: parse_digest(request.expected_document_flow_sha256())?,
            after_document_flow_sha256: parse_digest(request.target_document_flow_sha256())?,
            preserved_master_cell_count: source.ruling.grid.master_cell_count(),
            preserved_payload_block_count: source.ruling.payload_block_count,
            preserved_edge_count: source.ruling.state.edges().len(),
            inserted_formula_field_count: native_receipt.inserted_field_count,
            pagination_preserved: true,
            caption_preserved: true,
        };
        Ok(TableAggregateHwpxLoweredParts {
            header: header.to_vec(),
            section: output_section,
            binding: binding.clone(),
            receipt,
        })
    }
}

#[derive(Debug, Error)]
pub enum TableAggregateHwpxError {
    #[error("unsupported table aggregate HWPX schema version")]
    UnsupportedVersion,
    #[error("table aggregate HWPX input exceeds a finite bound")]
    InputLimit,
    #[error("invalid table aggregate HWPX JSON")]
    InvalidJson,
    #[error("invalid table aggregate HWPX binding")]
    InvalidBinding,
    #[error("table aggregate HWPX source parts, state, grid or flow drifted")]
    SourceBindingMismatch,
    #[error("table aggregate HWPX plan drifted")]
    PlanBindingMismatch,
    #[error("selected table is outside the exact unmerged formula-free source profile")]
    UnsupportedSourceProfile,
    #[error("table aggregate HWPX destination is not an empty master cell")]
    DestinationNotEmpty,
    #[error("table aggregate HWPX semantic readback mismatched")]
    ReadbackMismatch,
    #[error("table aggregate HWPX serialization failed")]
    Serialization,
    #[error("table aggregate HWPX output exceeds a finite bound")]
    OutputLimit,
    #[error(transparent)]
    Aggregate(#[from] TableAggregateError),
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
    FormulaModel(#[from] FormulaError),
}

impl TableAggregateHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::UnsupportedVersion => "table_aggregate_hwpx_unsupported_version",
            Self::InputLimit => "table_aggregate_hwpx_input_limit",
            Self::InvalidJson => "table_aggregate_hwpx_invalid_json",
            Self::InvalidBinding => "table_aggregate_hwpx_invalid_binding",
            Self::SourceBindingMismatch => "table_aggregate_hwpx_source_binding_mismatch",
            Self::PlanBindingMismatch => "table_aggregate_hwpx_plan_binding_mismatch",
            Self::UnsupportedSourceProfile => "table_aggregate_hwpx_unsupported_source_profile",
            Self::DestinationNotEmpty => "table_aggregate_hwpx_destination_not_empty",
            Self::ReadbackMismatch => "table_aggregate_hwpx_readback_mismatch",
            Self::Serialization => "table_aggregate_hwpx_serialization",
            Self::OutputLimit => "table_aggregate_hwpx_output_limit",
            Self::Aggregate(_) => "table_aggregate_hwpx_domain",
            Self::Grid(_) => "table_aggregate_hwpx_grid",
            Self::ModelRuling(_) => "table_aggregate_hwpx_model_ruling",
            Self::Ruling(_) => "table_aggregate_hwpx_ruling",
            Self::Layout(_) => "table_aggregate_hwpx_layout",
            Self::Pagination(_) => "table_aggregate_hwpx_pagination",
            Self::Formula(_) => "table_aggregate_hwpx_formula",
            Self::FormulaModel(_) => "table_aggregate_hwpx_formula_model",
        }
    }
}

fn validate_request_source(
    request: &TableAggregateHwpxRequest,
    source: &TableAggregateHwpxReadback,
    current_document_flow_sha256: &str,
    limits: &TableAggregateHwpxLimits,
) -> Result<(), TableAggregateHwpxError> {
    require_digest(current_document_flow_sha256)?;
    require_unmerged(&source.ruling.grid)?;
    if request.table_ordinal != source.table_ordinal
        || request.expected_header_sha256 != hex(source.ruling.header_sha256)
        || request.expected_section_sha256 != hex(source.ruling.section_sha256)
        || request.expected_source_state_sha256
            != hex(source.ruling.state.canonical_sha256(limits.ruling.ruling)?)
        || request.expected_source_grid_sha256 != hex(source.ruling.grid.canonical_sha256()?)
        || request.expected_document_flow_sha256 != current_document_flow_sha256
    {
        return Err(TableAggregateHwpxError::SourceBindingMismatch);
    }
    if source.ruling.formula_count != 0 {
        return Err(TableAggregateHwpxError::UnsupportedSourceProfile);
    }
    let destination = request.aggregate.destination();
    let span = source
        .ruling
        .grid
        .master_cell_at(destination)
        .map_err(|_| TableAggregateHwpxError::InvalidBinding)?;
    if span.row != destination.row || span.column != destination.column {
        return Err(TableAggregateHwpxError::UnsupportedSourceProfile);
    }
    let cell = source
        .ruling
        .state
        .cell(&span.master_cell_id)
        .ok_or(TableAggregateHwpxError::InvalidBinding)?;
    if !cell.payload().is_empty() || cell.formula().is_some() {
        return Err(TableAggregateHwpxError::DestinationNotEmpty);
    }
    Ok(())
}

fn state_with_formula(
    source: &TableRulingState,
    grid: &TableGrid,
    formula: &FormulaCell,
    limits: &TableAggregateHwpxLimits,
) -> Result<TableRulingState, TableAggregateHwpxError> {
    let mut cells = Vec::new();
    cells
        .try_reserve_exact(source.cells().len())
        .map_err(|_| TableAggregateHwpxError::OutputLimit)?;
    let mut inserted = false;
    for cell in source.cells() {
        let target = cell.coordinate() == formula.owner();
        if target {
            if inserted || !cell.payload().is_empty() || cell.formula().is_some() {
                return Err(TableAggregateHwpxError::DestinationNotEmpty);
            }
            inserted = true;
        } else if cell.formula().is_some() {
            return Err(TableAggregateHwpxError::UnsupportedSourceProfile);
        }
        cells.push(TableRulingCellDraft {
            master_cell_id: cell.master_cell_id().clone(),
            coordinate: cell.coordinate(),
            payload: cell.payload().to_vec(),
            properties: cell.properties().clone(),
            formula: target.then(|| formula_draft(formula)),
        });
    }
    if !inserted {
        return Err(TableAggregateHwpxError::InvalidBinding);
    }
    Ok(TableRulingState::from_draft(
        TableRulingStateDraft {
            schema_version: TABLE_RULING_SCHEMA_VERSION.to_owned(),
            table_id: source.table_id().clone(),
            frame: source.frame(),
            grid_sha256: source.grid_sha256().to_owned(),
            table_properties_sha256: source.table_properties_sha256().to_owned(),
            row_boundaries_hwpunit: source.row_boundaries_hwpunit().to_vec(),
            column_boundaries_hwpunit: source.column_boundaries_hwpunit().to_vec(),
            edges: source.edges().to_vec(),
            cells,
        },
        grid,
        limits.ruling.formula,
        limits.ruling.ruling,
    )?)
}

fn formula_draft(formula: &FormulaCell) -> FormulaCellDraft {
    FormulaCellDraft {
        schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
        owner: formula.owner(),
        ast: FormulaAstDraft {
            schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
            expression: formula.ast().expression().clone(),
        },
        cache: formula.cache().clone(),
        number_format: formula.number_format(),
    }
}

fn dimensions(grid: &TableGrid) -> FormulaGridDimensions {
    FormulaGridDimensions {
        rows: grid.rows(),
        columns: grid.columns(),
    }
}

fn require_unmerged(grid: &TableGrid) -> Result<(), TableAggregateHwpxError> {
    if grid
        .master_cells()
        .iter()
        .any(|cell| cell.row_span != 1 || cell.column_span != 1)
    {
        return Err(TableAggregateHwpxError::UnsupportedSourceProfile);
    }
    Ok(())
}

fn pagination_digest(value: &TablePaginationHwpxReadback) -> String {
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.table-aggregate-hwpx-pagination/v1\0");
    digest.update(match value.page_split {
        domain_ir::TablePageSplitPolicy::Allow => b"allow".as_slice(),
        domain_ir::TablePageSplitPolicy::AvoidRow => b"avoid-row".as_slice(),
        domain_ir::TablePageSplitPolicy::AvoidTable => b"avoid-table".as_slice(),
        domain_ir::TablePageSplitPolicy::RequiredKeep => b"required-keep".as_slice(),
    });
    digest.update(value.repeat_header_rows.to_le_bytes());
    digest.update(value.row_count.to_le_bytes());
    digest.update(value.column_count.to_le_bytes());
    if let Some(caption) = &value.caption {
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

fn same_pagination_semantics(
    left: &TablePaginationHwpxReadback,
    right: &TablePaginationHwpxReadback,
) -> bool {
    left.page_split == right.page_split
        && left.repeat_header_rows == right.repeat_header_rows
        && left.row_count == right.row_count
        && left.column_count == right.column_count
        && left.caption == right.caption
}

fn serialize_bounded<T: Serialize + ?Sized>(
    value: &T,
    maximum: usize,
) -> Result<Vec<u8>, TableAggregateHwpxError> {
    let bytes = serde_json::to_vec(value).map_err(|_| TableAggregateHwpxError::Serialization)?;
    if bytes.len() > maximum {
        return Err(TableAggregateHwpxError::OutputLimit);
    }
    Ok(bytes)
}

fn reject_duplicate_json_keys(bytes: &[u8]) -> Result<(), TableAggregateHwpxError> {
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
        .map_err(|_| TableAggregateHwpxError::InvalidJson)?;
    deserializer
        .end()
        .map_err(|_| TableAggregateHwpxError::InvalidJson)
}

fn require_digest(value: &str) -> Result<(), TableAggregateHwpxError> {
    if value.len() != 64
        || value
            .bytes()
            .any(|byte| !byte.is_ascii_digit() && !(b'a'..=b'f').contains(&byte))
    {
        return Err(TableAggregateHwpxError::InvalidBinding);
    }
    Ok(())
}

fn parse_digest(value: &str) -> Result<[u8; 32], TableAggregateHwpxError> {
    require_digest(value)?;
    let mut output = [0_u8; 32];
    for (index, chunk) in value.as_bytes().chunks_exact(2).enumerate() {
        let text =
            std::str::from_utf8(chunk).map_err(|_| TableAggregateHwpxError::InvalidBinding)?;
        output[index] =
            u8::from_str_radix(text, 16).map_err(|_| TableAggregateHwpxError::InvalidBinding)?;
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
