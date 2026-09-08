use std::collections::BTreeMap;

use domain_ir::{
    TABLE_PROPERTIES_SCHEMA_VERSION, TableCellBorderState, TableCellPropertyDraft,
    TableCellPropertyMutation, TableCellPropertyValue, TableDiagonalApplyMode, TableDiagonalValue,
    TablePropertiesError, TablePropertiesState, TablePropertiesStateDraft, TableStyleBuilder,
    TableStyleDefinition, TableStyleError, TableStyleLimits, TableStylePlan, TableStyleRequest,
    table_diagonal_identity_sha256,
};
use thiserror::Error;

use super::properties_hwpx::{self, ValueMaps};
use super::*;

pub const TABLE_STYLE_HWPX_PROFILE_ID: &str = "hwpx-agent.table-style-hwpx.hancom-2020/1";

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TableStyleHwpxLimits {
    pub properties: TablePropertiesHwpxLimits,
    pub style: TableStyleLimits,
}

/// One reusable visual cell-style value for the current Hangul 2020 HWPX profile.
///
/// Diagonal application provenance is deliberately not part of this reusable value. Existing
/// truthful unified provenance is preserved when the complete group keeps the same diagonal;
/// otherwise the target is materialized as exact per-cell diagonal bindings.
#[derive(Clone, Eq, PartialEq)]
pub struct TableStyleHwpxCellValue {
    pub non_border: TablePropertiesHwpxCellValue,
    pub borders: TableCellBorderState,
    pub background_sha256: Option<String>,
    pub diagonal: Option<TableDiagonalValue>,
}

impl std::fmt::Debug for TableStyleHwpxCellValue {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TableStyleHwpxCellValue")
            .field("non_border", &self.non_border)
            .field("borders", &self.borders)
            .field(
                "background_sha256",
                &self.background_sha256.as_ref().map(|_| "<redacted>"),
            )
            .field("diagonal", &self.diagonal.as_ref().map(|_| "<redacted>"))
            .finish()
    }
}

impl TableStyleHwpxCellValue {
    /// Returns the stable visual identity consumed by `TableStyleDefinition` rules.
    ///
    /// # Errors
    ///
    /// Rejects malformed line/background identities, an invisible diagonal, or serialization
    /// failure. Native backing values are checked against the complete typed catalog separately.
    pub fn canonical_sha256(&self) -> Result<String, TableStyleHwpxError> {
        require_optional_style_digest(self.borders.top_sha256.as_deref())?;
        require_optional_style_digest(self.borders.right_sha256.as_deref())?;
        require_optional_style_digest(self.borders.bottom_sha256.as_deref())?;
        require_optional_style_digest(self.borders.left_sha256.as_deref())?;
        require_optional_style_digest(self.background_sha256.as_deref())?;
        if let Some(value) = &self.diagonal {
            require_style_digest(&value.line_sha256)?;
            if diagonal_is_empty(value) {
                return Err(TableStyleHwpxError::InvalidStyleValue);
            }
        }
        let mut digest = Sha256::new();
        digest.update(b"hwpx-agent.table-style-hwpx-cell-value/v1\0");
        hash_part(&mut digest, self.non_border.canonical_sha256().as_bytes());
        for value in [
            self.borders.top_sha256.as_deref(),
            self.borders.right_sha256.as_deref(),
            self.borders.bottom_sha256.as_deref(),
            self.borders.left_sha256.as_deref(),
            self.background_sha256.as_deref(),
        ] {
            hash_optional(&mut digest, value);
        }
        match &self.diagonal {
            Some(value) => {
                hash_part(&mut digest, b"some");
                let bytes =
                    serde_json::to_vec(value).map_err(|_| TableStyleHwpxError::Serialization)?;
                hash_part(&mut digest, &bytes);
            }
            None => hash_part(&mut digest, b"none"),
        }
        Ok(hex(digest.finalize()))
    }
}

#[derive(Clone, Default, Eq, PartialEq)]
pub struct TableStyleHwpxValueCatalog {
    pub table_values: Vec<TablePropertiesHwpxTableValue>,
    pub cell_styles: Vec<TableStyleHwpxCellValue>,
    pub lines: Vec<BorderLine>,
    pub backgrounds: Vec<FillBrush>,
    pub border_fills: Vec<BorderFill>,
}

impl std::fmt::Debug for TableStyleHwpxValueCatalog {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TableStyleHwpxValueCatalog")
            .field("table_value_count", &self.table_values.len())
            .field("cell_style_count", &self.cell_styles.len())
            .field("line_count", &self.lines.len())
            .field("background_count", &self.backgrounds.len())
            .field("border_fill_count", &self.border_fills.len())
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableStyleHwpxReadback {
    pub profile_id: &'static str,
    pub properties: TablePropertiesHwpxReadback,
    pub cell_style_sha256: Vec<String>,
    pub style_state_sha256: [u8; 32],
}

impl std::fmt::Debug for TableStyleHwpxReadback {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TableStyleHwpxReadback")
            .field("profile_id", &self.profile_id)
            .field("rows", &self.properties.grid.rows())
            .field("columns", &self.properties.grid.columns())
            .field("cell_style_count", &self.cell_style_sha256.len())
            .field("formula_count", &self.properties.formula_count)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableStyleHwpxPartBinding {
    pub header_sha256: String,
    pub section_sha256: String,
    pub document_flow_sha256: String,
    pub source_style_state_sha256: String,
    pub request_sha256: String,
    pub definition_sha256: String,
    pub plan_sha256: String,
}

impl TableStyleHwpxPartBinding {
    /// Binds request-time package parts, complete style state, flow, definition, request and plan.
    ///
    /// # Errors
    ///
    /// Rejects source/request mismatch, plan drift, malformed flow identity, or bounded hashes.
    pub fn from_readback(
        readback: &TableStyleHwpxReadback,
        request: &TableStyleRequest,
        definition: &TableStyleDefinition,
        plan: &TableStylePlan,
        document_flow_sha256: String,
        limits: TableStyleHwpxLimits,
    ) -> Result<Self, TableStyleHwpxError> {
        require_digest(&document_flow_sha256)?;
        validate_request_source(readback, request)?;
        let rebuilt =
            TableStyleBuilder::build(request, definition, &readback.properties.grid, limits.style)?;
        if rebuilt != *plan {
            return Err(TableStyleHwpxError::PlanBindingMismatch);
        }
        Ok(Self {
            header_sha256: hex(readback.properties.header_sha256),
            section_sha256: hex(readback.properties.section_sha256),
            document_flow_sha256,
            source_style_state_sha256: hex(readback.style_state_sha256),
            request_sha256: hex(request.canonical_sha256(limits.style)?),
            definition_sha256: hex(definition.canonical_sha256(limits.style)?),
            plan_sha256: hex(plan.canonical_sha256(limits.style)?),
        })
    }
}

impl std::fmt::Debug for TableStyleHwpxPartBinding {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TableStyleHwpxPartBinding")
            .field("header_sha256", &"<redacted>")
            .field("section_sha256", &"<redacted>")
            .field("document_flow_sha256", &"<redacted>")
            .field("source_style_state_sha256", &"<redacted>")
            .field("request_sha256", &"<redacted>")
            .field("definition_sha256", &"<redacted>")
            .field("plan_sha256", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableStyleHwpxLoweringReceipt {
    pub profile_id: &'static str,
    pub source_header_sha256: [u8; 32],
    pub output_header_sha256: [u8; 32],
    pub source_section_sha256: [u8; 32],
    pub output_section_sha256: [u8; 32],
    pub source_style_state_sha256: [u8; 32],
    pub target_style_state_sha256: [u8; 32],
    pub grid_sha256: [u8; 32],
    pub definition_sha256: [u8; 32],
    pub request_sha256: [u8; 32],
    pub plan_sha256: [u8; 32],
    pub document_flow_sha256: [u8; 32],
    pub added_border_fill_count: usize,
    pub changed_master_cell_count: usize,
    pub preserved_payload_count: usize,
    pub preserved_formula_count: usize,
    pub normalized_unified_diagonal_cell_count: usize,
}

impl std::fmt::Debug for TableStyleHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TableStyleHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field("added_border_fill_count", &self.added_border_fill_count)
            .field("changed_master_cell_count", &self.changed_master_cell_count)
            .field("preserved_payload_count", &self.preserved_payload_count)
            .field("preserved_formula_count", &self.preserved_formula_count)
            .field(
                "normalized_unified_diagonal_cell_count",
                &self.normalized_unified_diagonal_cell_count,
            )
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableStyleHwpxLoweredParts {
    pub header: Vec<u8>,
    pub section: Vec<u8>,
    pub binding: TablePropertiesHwpxBinding,
    pub receipt: TableStyleHwpxLoweringReceipt,
}

impl std::fmt::Debug for TableStyleHwpxLoweredParts {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TableStyleHwpxLoweredParts")
            .field("header_bytes", &self.header.len())
            .field("section_bytes", &self.section.len())
            .field("binding", &self.binding)
            .field("receipt", &self.receipt)
            .finish()
    }
}

#[derive(Debug, Error)]
pub enum TableStyleHwpxError {
    #[error("table-style HWPX binding or digest is invalid")]
    InvalidBinding,
    #[error("table-style HWPX typed style value is invalid")]
    InvalidStyleValue,
    #[error("table-style HWPX source parts, flow or bound state drifted")]
    PartBindingMismatch,
    #[error("table-style HWPX source state differs from the exact request")]
    SourceStateMismatch,
    #[error("table-style HWPX definition, request or plan receipt is inconsistent")]
    PlanBindingMismatch,
    #[error("table-style HWPX typed value is absent from the complete catalog")]
    MissingCatalogValue,
    #[error("table-style HWPX typed catalog contains an ambiguous identity")]
    AmbiguousCatalogValue,
    #[error("table-style HWPX exact semantic readback differs from the target")]
    ReadbackMismatch,
    #[error("table-style HWPX allocation failed")]
    AllocationFailed,
    #[error("table-style HWPX serialization failed")]
    Serialization,
    #[error("table-style HWPX property adapter failed")]
    Properties(#[from] TablePropertiesHwpxError),
    #[error("table-style HWPX property state failed")]
    PropertiesCore(#[from] TablePropertiesError),
    #[error("table-style HWPX logical style planner failed")]
    Style(#[from] TableStyleError),
}

impl TableStyleHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidBinding => "table_style_hwpx_invalid_binding",
            Self::InvalidStyleValue => "table_style_hwpx_invalid_style_value",
            Self::PartBindingMismatch => "table_style_hwpx_part_binding_mismatch",
            Self::SourceStateMismatch => "table_style_hwpx_source_state_mismatch",
            Self::PlanBindingMismatch => "table_style_hwpx_plan_binding_mismatch",
            Self::MissingCatalogValue => "table_style_hwpx_missing_catalog_value",
            Self::AmbiguousCatalogValue => "table_style_hwpx_ambiguous_catalog_value",
            Self::ReadbackMismatch => "table_style_hwpx_readback_mismatch",
            Self::AllocationFailed => "table_style_hwpx_allocation",
            Self::Serialization => "table_style_hwpx_serialization",
            Self::Properties(_) => "table_style_hwpx_properties_adapter",
            Self::PropertiesCore(_) => "table_style_hwpx_properties_core",
            Self::Style(_) => "table_style_hwpx_style_core",
        }
    }
}

#[derive(Debug)]
pub struct TableStyleHwpxReader;

impl TableStyleHwpxReader {
    /// Reads one complete table property state plus reusable visual style identities.
    ///
    /// # Errors
    ///
    /// Propagates strict table-property, formula, payload, grid, catalog and diagonal admission.
    pub fn read_existing(
        header: &[u8],
        section: &[u8],
        table_ordinal: usize,
        binding: &TablePropertiesHwpxBinding,
        limits: TableStyleHwpxLimits,
    ) -> Result<TableStyleHwpxReadback, TableStyleHwpxError> {
        read_existing(header, section, table_ordinal, binding, &limits)
    }
}

#[derive(Debug)]
pub struct TableStyleHwpxLowerer;

impl TableStyleHwpxLowerer {
    /// Applies a complete style plan to one exact existing HWPX table.
    ///
    /// The method rechecks parts, flow, complete source style state, request, definition and plan;
    /// resolves every rule through typed native values; preserves payload/formula state; and reparses
    /// the output before returning coordinated header/section bytes.
    ///
    /// # Errors
    ///
    /// Rejects any binding drift, incomplete or ambiguous catalog, unsupported native shape,
    /// output bound, or semantic reopen mismatch.
    #[allow(clippy::too_many_arguments)]
    pub fn lower_existing(
        header: &[u8],
        section: &[u8],
        table_ordinal: usize,
        binding: &TablePropertiesHwpxBinding,
        part_binding: &TableStyleHwpxPartBinding,
        current_document_flow_sha256: &str,
        request: &TableStyleRequest,
        definition: &TableStyleDefinition,
        plan: &TableStylePlan,
        values: &TableStyleHwpxValueCatalog,
        limits: TableStyleHwpxLimits,
    ) -> Result<TableStyleHwpxLoweredParts, TableStyleHwpxError> {
        validate_part_binding(
            header,
            section,
            part_binding,
            current_document_flow_sha256,
            request,
            definition,
            plan,
            &limits,
        )?;
        let source = read_existing(header, section, table_ordinal, binding, &limits)?;
        if hex(source.style_state_sha256) != part_binding.source_style_state_sha256 {
            return Err(TableStyleHwpxError::PartBindingMismatch);
        }
        validate_request_source(&source, request)?;
        let rebuilt =
            TableStyleBuilder::build(request, definition, &source.properties.grid, limits.style)?;
        if rebuilt != *plan {
            return Err(TableStyleHwpxError::PlanBindingMismatch);
        }
        let target = build_target(header, &source, binding, definition, plan, values, &limits)?;
        let rendered = properties_hwpx::render(
            header,
            section,
            table_ordinal,
            binding,
            &source.properties,
            &target.state,
            &target.binding,
            &target.mutations,
            &target.properties_catalog,
            &limits.properties,
        )?;
        let reopened = read_existing(
            &rendered.header,
            &rendered.section,
            table_ordinal,
            &target.binding,
            &limits,
        )?;
        if reopened.properties.grid != source.properties.grid
            || reopened.properties.state != target.state
            || reopened.cell_style_sha256 != target.style_sha256
        {
            return Err(TableStyleHwpxError::ReadbackMismatch);
        }
        let receipt = TableStyleHwpxLoweringReceipt {
            profile_id: TABLE_STYLE_HWPX_PROFILE_ID,
            source_header_sha256: Sha256::digest(header).into(),
            output_header_sha256: Sha256::digest(&rendered.header).into(),
            source_section_sha256: Sha256::digest(section).into(),
            output_section_sha256: Sha256::digest(&rendered.section).into(),
            source_style_state_sha256: source.style_state_sha256,
            target_style_state_sha256: reopened.style_state_sha256,
            grid_sha256: source
                .properties
                .grid
                .canonical_sha256()
                .map_err(TablePropertiesHwpxError::from)?,
            definition_sha256: definition.canonical_sha256(limits.style)?,
            request_sha256: request.canonical_sha256(limits.style)?,
            plan_sha256: plan.canonical_sha256(limits.style)?,
            document_flow_sha256: parse_digest(current_document_flow_sha256)?,
            added_border_fill_count: rendered.added_border_fill_count,
            changed_master_cell_count: plan.receipt().changed_cell_count,
            preserved_payload_count: plan.receipt().payload_preserved_count,
            preserved_formula_count: plan.receipt().formula_preserved_count,
            normalized_unified_diagonal_cell_count: target.normalized_unified_diagonal_cell_count,
        };
        Ok(TableStyleHwpxLoweredParts {
            header: rendered.header,
            section: rendered.section,
            binding: target.binding,
            receipt,
        })
    }
}

fn read_existing(
    header: &[u8],
    section: &[u8],
    table_ordinal: usize,
    binding: &TablePropertiesHwpxBinding,
    limits: &TableStyleHwpxLimits,
) -> Result<TableStyleHwpxReadback, TableStyleHwpxError> {
    let properties = properties_hwpx::read_existing(
        header,
        section,
        table_ordinal,
        binding,
        &limits.properties,
    )?;
    let cell_style_sha256 = source_style_digests(&properties, binding)?;
    let style_state_sha256 = style_state_sha256(&properties.state, &cell_style_sha256, limits)?;
    Ok(TableStyleHwpxReadback {
        profile_id: TABLE_STYLE_HWPX_PROFILE_ID,
        properties,
        cell_style_sha256,
        style_state_sha256,
    })
}

fn source_style_digests(
    source: &TablePropertiesHwpxReadback,
    binding: &TablePropertiesHwpxBinding,
) -> Result<Vec<String>, TableStyleHwpxError> {
    if source.state.cells().len() != source.cell_values.len()
        || source.state.cells().len() != binding.table.cells.len()
    {
        return Err(TableStyleHwpxError::InvalidBinding);
    }
    let diagonals = diagonal_map(&binding.diagonals)?;
    let mut output = Vec::new();
    output
        .try_reserve_exact(source.state.cells().len())
        .map_err(|_| TableStyleHwpxError::AllocationFailed)?;
    for ((cell, non_border), identity) in source
        .state
        .cells()
        .iter()
        .zip(&source.cell_values)
        .zip(&binding.table.cells)
    {
        if cell.master_cell_id != identity.master_cell_id {
            return Err(TableStyleHwpxError::InvalidBinding);
        }
        let diagonal = diagonals
            .get(&cell.master_cell_id)
            .map(|value| value.value.clone());
        if cell.properties.diagonal_sha256.is_some() != diagonal.is_some() {
            return Err(TableStyleHwpxError::InvalidBinding);
        }
        output.push(
            TableStyleHwpxCellValue {
                non_border: *non_border,
                borders: cell.properties.borders.clone(),
                background_sha256: cell.properties.background_sha256.clone(),
                diagonal,
            }
            .canonical_sha256()?,
        );
    }
    Ok(output)
}

fn validate_request_source(
    source: &TableStyleHwpxReadback,
    request: &TableStyleRequest,
) -> Result<(), TableStyleHwpxError> {
    if request.table_id() != source.properties.state.table_id()
        || request.grid_sha256() != source.properties.state.grid_sha256()
        || request.current_table_properties_sha256()
            != source.properties.state.table_properties_sha256()
        || request.cells().len() != source.properties.state.cells().len()
        || request.cells().len() != source.cell_style_sha256.len()
    {
        return Err(TableStyleHwpxError::SourceStateMismatch);
    }
    for ((expected, actual), style_sha256) in request
        .cells()
        .iter()
        .zip(source.properties.state.cells())
        .zip(&source.cell_style_sha256)
    {
        if expected.master_cell_id != actual.master_cell_id
            || expected.coordinate != actual.coordinate
            || expected.payload_sha256 != actual.payload_sha256
            || expected.formula_sha256 != actual.formula_sha256
            || expected.current_style_sha256 != *style_sha256
        {
            return Err(TableStyleHwpxError::SourceStateMismatch);
        }
    }
    Ok(())
}

#[allow(clippy::too_many_arguments)]
fn validate_part_binding(
    header: &[u8],
    section: &[u8],
    binding: &TableStyleHwpxPartBinding,
    current_document_flow_sha256: &str,
    request: &TableStyleRequest,
    definition: &TableStyleDefinition,
    plan: &TableStylePlan,
    limits: &TableStyleHwpxLimits,
) -> Result<(), TableStyleHwpxError> {
    for value in [
        &binding.header_sha256,
        &binding.section_sha256,
        &binding.document_flow_sha256,
        &binding.source_style_state_sha256,
        &binding.request_sha256,
        &binding.definition_sha256,
        &binding.plan_sha256,
        current_document_flow_sha256,
    ] {
        require_digest(value)?;
    }
    if binding.header_sha256 != hex(Sha256::digest(header))
        || binding.section_sha256 != hex(Sha256::digest(section))
        || binding.document_flow_sha256 != current_document_flow_sha256
        || binding.request_sha256 != hex(request.canonical_sha256(limits.style)?)
        || binding.definition_sha256 != hex(definition.canonical_sha256(limits.style)?)
        || binding.plan_sha256 != hex(plan.canonical_sha256(limits.style)?)
        || request.style_definition_sha256() != binding.definition_sha256
        || request.style_id() != definition.style_id()
    {
        return Err(TableStyleHwpxError::PartBindingMismatch);
    }
    Ok(())
}

struct TargetBuild {
    state: TablePropertiesState,
    binding: TablePropertiesHwpxBinding,
    mutations: Vec<TableCellPropertyMutation>,
    style_sha256: Vec<String>,
    properties_catalog: TablePropertiesHwpxValueCatalog,
    normalized_unified_diagonal_cell_count: usize,
}

struct TargetDiagonalBuild {
    binding: TablePropertiesHwpxBinding,
    normalized_unified_diagonal_cell_count: usize,
}

fn build_target(
    header: &[u8],
    source: &TableStyleHwpxReadback,
    source_binding: &TablePropertiesHwpxBinding,
    definition: &TableStyleDefinition,
    plan: &TableStylePlan,
    values: &TableStyleHwpxValueCatalog,
    limits: &TableStyleHwpxLimits,
) -> Result<TargetBuild, TableStyleHwpxError> {
    if plan.table_properties_sha256() != definition.table_properties_sha256()
        || plan.receipt().table_id != *source.properties.state.table_id()
        || plan.receipt().grid_sha256 != source.properties.state.grid_sha256()
        || plan.mutations().len() != source.properties.state.cells().len()
    {
        return Err(TableStyleHwpxError::PlanBindingMismatch);
    }
    let (style_values, properties_catalog) =
        validate_value_catalog(header, &source.properties, definition, plan, values, limits)?;
    let diagonal_build =
        build_target_diagonal_binding(source, source_binding, plan, &style_values)?;
    let (state, mutations, style_sha256) =
        build_target_cells(source, &diagonal_build.binding, plan, &style_values, limits)?;
    Ok(TargetBuild {
        state,
        binding: diagonal_build.binding,
        mutations,
        style_sha256,
        properties_catalog,
        normalized_unified_diagonal_cell_count: diagonal_build
            .normalized_unified_diagonal_cell_count,
    })
}

fn build_target_diagonal_binding(
    source: &TableStyleHwpxReadback,
    source_binding: &TablePropertiesHwpxBinding,
    plan: &TableStylePlan,
    style_values: &BTreeMap<String, &TableStyleHwpxCellValue>,
) -> Result<TargetDiagonalBuild, TableStyleHwpxError> {
    let mut desired_diagonals = BTreeMap::new();
    for mutation in plan.mutations() {
        let target = style_values
            .get(&mutation.after_style_sha256)
            .ok_or(TableStyleHwpxError::MissingCatalogValue)?;
        if desired_diagonals
            .insert(mutation.master_cell_id.clone(), target.diagonal.clone())
            .is_some()
        {
            return Err(TableStyleHwpxError::PlanBindingMismatch);
        }
    }
    let source_diagonals = diagonal_map(&source_binding.diagonals)?;
    let mut target_diagonals = Vec::new();
    target_diagonals
        .try_reserve_exact(source.properties.state.cells().len())
        .map_err(|_| TableStyleHwpxError::AllocationFailed)?;
    let mut normalized_unified_diagonal_cell_count = 0_usize;
    for cell in source.properties.state.cells() {
        let desired = desired_diagonals
            .get(&cell.master_cell_id)
            .ok_or(TableStyleHwpxError::PlanBindingMismatch)?;
        let source_diagonal = source_diagonals.get(&cell.master_cell_id).copied();
        if let Some(value) = desired {
            if source_diagonal.is_some_and(|binding| {
                binding.apply_mode == TableDiagonalApplyMode::Unified
                    && unified_group_preservable(
                        binding,
                        &source_binding.diagonals,
                        &desired_diagonals,
                    )
            }) {
                target_diagonals.push(
                    source_diagonal
                        .ok_or(TableStyleHwpxError::InvalidBinding)?
                        .clone(),
                );
            } else {
                if source_diagonal
                    .is_some_and(|binding| binding.apply_mode == TableDiagonalApplyMode::Unified)
                {
                    normalized_unified_diagonal_cell_count = normalized_unified_diagonal_cell_count
                        .checked_add(1)
                        .ok_or(TableStyleHwpxError::AllocationFailed)?;
                }
                target_diagonals.push(TablePropertiesHwpxDiagonalBinding {
                    master_cell_id: cell.master_cell_id.clone(),
                    apply_mode: TableDiagonalApplyMode::EachCell,
                    region: None,
                    value: value.clone(),
                });
            }
        }
    }
    Ok(TargetDiagonalBuild {
        binding: TablePropertiesHwpxBinding {
            table: source_binding.table.clone(),
            diagonals: target_diagonals,
        },
        normalized_unified_diagonal_cell_count,
    })
}

fn build_target_cells(
    source: &TableStyleHwpxReadback,
    target_binding: &TablePropertiesHwpxBinding,
    plan: &TableStylePlan,
    style_values: &BTreeMap<String, &TableStyleHwpxCellValue>,
    limits: &TableStyleHwpxLimits,
) -> Result<
    (
        TablePropertiesState,
        Vec<TableCellPropertyMutation>,
        Vec<String>,
    ),
    TableStyleHwpxError,
> {
    let target_diagonal_map = diagonal_map(&target_binding.diagonals)?;
    let mut cells = Vec::new();
    let mut mutations = Vec::new();
    let mut style_sha256 = Vec::new();
    cells
        .try_reserve_exact(source.properties.state.cells().len())
        .map_err(|_| TableStyleHwpxError::AllocationFailed)?;
    mutations
        .try_reserve_exact(source.properties.state.cells().len())
        .map_err(|_| TableStyleHwpxError::AllocationFailed)?;
    style_sha256
        .try_reserve_exact(source.properties.state.cells().len())
        .map_err(|_| TableStyleHwpxError::AllocationFailed)?;
    for (((source_cell, source_style), mutation), span) in source
        .properties
        .state
        .cells()
        .iter()
        .zip(&source.cell_style_sha256)
        .zip(plan.mutations())
        .zip(source.properties.grid.master_cells())
    {
        if source_cell.master_cell_id != mutation.master_cell_id
            || mutation.coordinate != source_cell.coordinate
            || mutation.before_style_sha256 != *source_style
            || mutation.payload_sha256 != source_cell.payload_sha256
            || mutation.formula_sha256 != source_cell.formula_sha256
            || span.master_cell_id != source_cell.master_cell_id
        {
            return Err(TableStyleHwpxError::PlanBindingMismatch);
        }
        let style = style_values
            .get(&mutation.after_style_sha256)
            .ok_or(TableStyleHwpxError::MissingCatalogValue)?;
        let target_diagonal = target_diagonal_map
            .get(&source_cell.master_cell_id)
            .copied();
        let diagonal_sha256 = target_diagonal
            .map(|binding| {
                table_diagonal_identity_sha256(
                    source.properties.state.table_id(),
                    source.properties.state.grid_sha256(),
                    binding.apply_mode,
                    binding.region,
                    &binding.value,
                    limits.properties.properties,
                )
            })
            .transpose()?;
        let after = TableCellPropertyValue {
            non_border_properties_sha256: style.non_border.canonical_sha256(),
            borders: style.borders.clone(),
            background_sha256: style.background_sha256.clone(),
            diagonal_sha256,
        };
        cells.push(TableCellPropertyDraft {
            master_cell_id: source_cell.master_cell_id.clone(),
            coordinate: source_cell.coordinate,
            payload_sha256: source_cell.payload_sha256.clone(),
            formula_sha256: source_cell.formula_sha256.clone(),
            properties: after.clone(),
        });
        mutations.push(TableCellPropertyMutation {
            master_cell_id: source_cell.master_cell_id.clone(),
            coordinate: source_cell.coordinate,
            before: source_cell.properties.clone(),
            after,
            payload_sha256: source_cell.payload_sha256.clone(),
            formula_sha256: source_cell.formula_sha256.clone(),
            border_roles: None,
            diagonal_apply_mode: target_diagonal.map(|binding| binding.apply_mode),
        });
        style_sha256.push(mutation.after_style_sha256.clone());
    }
    let state = TablePropertiesState::from_draft(
        TablePropertiesStateDraft {
            schema_version: TABLE_PROPERTIES_SCHEMA_VERSION.to_owned(),
            table_id: source.properties.state.table_id().clone(),
            grid_sha256: source.properties.state.grid_sha256().to_owned(),
            table_properties_sha256: plan.table_properties_sha256().to_owned(),
            cells,
        },
        &source.properties.grid,
        limits.properties.properties,
    )?;
    Ok((state, mutations, style_sha256))
}

fn validate_value_catalog<'a>(
    header: &[u8],
    source: &TablePropertiesHwpxReadback,
    definition: &TableStyleDefinition,
    plan: &TableStylePlan,
    values: &'a TableStyleHwpxValueCatalog,
    limits: &TableStyleHwpxLimits,
) -> Result<
    (
        BTreeMap<String, &'a TableStyleHwpxCellValue>,
        TablePropertiesHwpxValueCatalog,
    ),
    TableStyleHwpxError,
> {
    let maximum = limits
        .properties
        .native
        .paragraph_style
        .config()
        .border_fills;
    if [
        values.table_values.len(),
        values.cell_styles.len(),
        values.lines.len(),
        values.backgrounds.len(),
        values.border_fills.len(),
    ]
    .into_iter()
    .any(|count| count > maximum)
    {
        return Err(TableStyleHwpxError::Properties(
            TablePropertiesHwpxError::BorderFillLimit,
        ));
    }
    let mut style_values = BTreeMap::new();
    let mut non_border_values = BTreeMap::new();
    for value in &values.cell_styles {
        let digest = value.canonical_sha256()?;
        if let Some(previous) = style_values.insert(digest, value)
            && previous != value
        {
            return Err(TableStyleHwpxError::AmbiguousCatalogValue);
        }
        let digest = value.non_border.canonical_sha256();
        if let Some(previous) = non_border_values.insert(digest, value.non_border)
            && previous != value.non_border
        {
            return Err(TableStyleHwpxError::AmbiguousCatalogValue);
        }
    }
    for rule in definition.rules() {
        if !style_values.contains_key(&rule.cell_style_sha256) {
            return Err(TableStyleHwpxError::MissingCatalogValue);
        }
    }
    for mutation in plan.mutations() {
        if !style_values.contains_key(&mutation.after_style_sha256) {
            return Err(TableStyleHwpxError::MissingCatalogValue);
        }
    }
    let properties_catalog = TablePropertiesHwpxValueCatalog {
        table_values: values.table_values.clone(),
        cell_values: non_border_values.into_values().collect(),
        lines: values.lines.clone(),
        backgrounds: values.backgrounds.clone(),
        border_fills: values.border_fills.clone(),
    };
    properties_hwpx::validate_catalog_bounds(&properties_catalog, &limits.properties)?;
    let catalog =
        ParagraphStyleCatalogReader::read(header, limits.properties.native.paragraph_style)
            .map_err(TablePropertiesHwpxError::from)?;
    let mut resolver =
        StyleResolver::new(catalog.border_fills.clone()).map_err(TablePropertiesHwpxError::from)?;
    let maps = ValueMaps::new(
        &catalog,
        &properties_catalog,
        &mut resolver,
        limits.properties.cell_style,
    )?;
    if plan.table_properties_sha256() != source.state.table_properties_sha256()
        && !maps
            .table_values
            .contains_key(plan.table_properties_sha256())
    {
        return Err(TableStyleHwpxError::MissingCatalogValue);
    }
    for value in style_values.values().copied() {
        if !maps
            .cell_values
            .contains_key(&value.non_border.canonical_sha256())
            || [
                value.borders.top_sha256.as_ref(),
                value.borders.right_sha256.as_ref(),
                value.borders.bottom_sha256.as_ref(),
                value.borders.left_sha256.as_ref(),
            ]
            .into_iter()
            .flatten()
            .any(|digest| !maps.lines.contains_key(digest))
            || value
                .background_sha256
                .as_ref()
                .is_some_and(|digest| !maps.backgrounds.contains_key(digest))
            || value
                .diagonal
                .as_ref()
                .is_some_and(|diagonal| !maps.lines.contains_key(&diagonal.line_sha256))
        {
            return Err(TableStyleHwpxError::MissingCatalogValue);
        }
    }
    Ok((style_values, properties_catalog))
}

fn unified_group_preservable(
    candidate: &TablePropertiesHwpxDiagonalBinding,
    source: &[TablePropertiesHwpxDiagonalBinding],
    desired: &BTreeMap<LogicalId, Option<TableDiagonalValue>>,
) -> bool {
    candidate.apply_mode == TableDiagonalApplyMode::Unified
        && candidate.region.is_some()
        && source
            .iter()
            .filter(|value| {
                value.apply_mode == TableDiagonalApplyMode::Unified
                    && value.region == candidate.region
            })
            .all(|value| {
                value.value == candidate.value
                    && desired.get(&value.master_cell_id) == Some(&Some(candidate.value.clone()))
            })
}

fn diagonal_map(
    values: &[TablePropertiesHwpxDiagonalBinding],
) -> Result<BTreeMap<LogicalId, &TablePropertiesHwpxDiagonalBinding>, TableStyleHwpxError> {
    let mut output = BTreeMap::new();
    for value in values {
        if output.insert(value.master_cell_id.clone(), value).is_some() {
            return Err(TableStyleHwpxError::InvalidBinding);
        }
    }
    Ok(output)
}

fn style_state_sha256(
    state: &TablePropertiesState,
    styles: &[String],
    limits: &TableStyleHwpxLimits,
) -> Result<[u8; 32], TableStyleHwpxError> {
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.table-style-hwpx-state/v1\0");
    hash_part(
        &mut digest,
        &state.canonical_sha256(limits.properties.properties)?,
    );
    hash_part(&mut digest, &styles.len().to_be_bytes());
    for value in styles {
        require_digest(value)?;
        hash_part(&mut digest, value.as_bytes());
    }
    Ok(digest.finalize().into())
}

fn diagonal_is_empty(value: &TableDiagonalValue) -> bool {
    use domain_ir::{TableDiagonalCenterLine, TableDiagonalSlashType};
    value.slash.slash_type == TableDiagonalSlashType::None
        && value.back_slash.slash_type == TableDiagonalSlashType::None
        && value.center_line == TableDiagonalCenterLine::None
}

fn require_optional_style_digest(value: Option<&str>) -> Result<(), TableStyleHwpxError> {
    if let Some(value) = value {
        require_style_digest(value)?;
    }
    Ok(())
}

fn require_style_digest(value: &str) -> Result<(), TableStyleHwpxError> {
    require_digest(value).map_err(|_| TableStyleHwpxError::InvalidStyleValue)
}

fn require_digest(value: &str) -> Result<(), TableStyleHwpxError> {
    if value.len() != 64
        || !value
            .as_bytes()
            .iter()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(byte))
    {
        return Err(TableStyleHwpxError::InvalidBinding);
    }
    Ok(())
}

fn parse_digest(value: &str) -> Result<[u8; 32], TableStyleHwpxError> {
    require_digest(value)?;
    let mut output = [0_u8; 32];
    for (index, slot) in output.iter_mut().enumerate() {
        let offset = index * 2;
        *slot = u8::from_str_radix(&value[offset..offset + 2], 16)
            .map_err(|_| TableStyleHwpxError::InvalidBinding)?;
    }
    Ok(output)
}

fn hash_optional(digest: &mut Sha256, value: Option<&str>) {
    match value {
        Some(value) => {
            hash_part(digest, b"some");
            hash_part(digest, value.as_bytes());
        }
        None => hash_part(digest, b"none"),
    }
}

fn hash_part(digest: &mut Sha256, value: &[u8]) {
    digest.update(u64::try_from(value.len()).unwrap_or(u64::MAX).to_be_bytes());
    digest.update(value);
}

fn hex(value: impl AsRef<[u8]>) -> String {
    let bytes = value.as_ref();
    let mut output = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        use std::fmt::Write as _;
        let _ = write!(&mut output, "{byte:02x}");
    }
    output
}
