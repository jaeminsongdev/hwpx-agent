use std::fmt;

use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{CellCoordinate, LogicalId, TableCellSpan, TableGrid};

pub const TABLE_STYLE_SCHEMA_VERSION: &str = "hwpx-agent.table-style/v1";
pub const TABLE_STYLE_DEFINITION_SCHEMA_VERSION: &str = "hwpx-agent.table-style-definition/v1";
pub const TABLE_STYLE_CAPABILITY_ID: &str = "table.table_style";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TableStyleLimitConfig {
    pub input_bytes: usize,
    pub master_cells: usize,
    pub style_rules: usize,
    pub identifier_bytes: usize,
    pub serialized_bytes: usize,
}

impl Default for TableStyleLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 8 * 1024 * 1024,
            master_cells: 1_000_000,
            style_rules: 13,
            identifier_bytes: 256,
            serialized_bytes: 64 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TableStyleLimits(TableStyleLimitConfig);

impl TableStyleLimits {
    pub const HARD_MAX_INPUT_BYTES: usize = 64 * 1024 * 1024;
    pub const HARD_MAX_MASTER_CELLS: usize = 1_000_000;
    pub const HARD_MAX_STYLE_RULES: usize = 13;
    pub const HARD_MAX_IDENTIFIER_BYTES: usize = 1_024;
    pub const HARD_MAX_SERIALIZED_BYTES: usize = 256 * 1024 * 1024;

    /// Creates finite limits for table-style definition admission and resolution.
    ///
    /// # Errors
    ///
    /// Rejects zero, over-ceiling or internally inconsistent values.
    pub fn new(config: TableStyleLimitConfig) -> Result<Self, TableStyleError> {
        if config.input_bytes == 0
            || config.input_bytes > Self::HARD_MAX_INPUT_BYTES
            || config.master_cells == 0
            || config.master_cells > Self::HARD_MAX_MASTER_CELLS
            || config.style_rules == 0
            || config.style_rules > Self::HARD_MAX_STYLE_RULES
            || config.identifier_bytes == 0
            || config.identifier_bytes > Self::HARD_MAX_IDENTIFIER_BYTES
            || config.serialized_bytes == 0
            || config.serialized_bytes > Self::HARD_MAX_SERIALIZED_BYTES
            || config.input_bytes > config.serialized_bytes
        {
            return Err(TableStyleError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> TableStyleLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableStyleRegion {
    WholeTable,
    HeaderRows,
    FooterRows,
    FirstColumn,
    LastColumn,
    OddRowBand,
    EvenRowBand,
    OddColumnBand,
    EvenColumnBand,
    TopLeftCell,
    TopRightCell,
    BottomLeftCell,
    BottomRightCell,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableStyleBandPrecedence {
    RowsFirst,
    ColumnsFirst,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableStyleMergedCellPolicy {
    RejectMixedResolvedStyle,
    UseMasterAnchor,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableStyleColumnEmphasis {
    None,
    First,
    Last,
    FirstAndLast,
}

impl TableStyleColumnEmphasis {
    const fn includes_first(self) -> bool {
        matches!(self, Self::First | Self::FirstAndLast)
    }

    const fn includes_last(self) -> bool {
        matches!(self, Self::Last | Self::FirstAndLast)
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableStyleBanding {
    None,
    Rows,
    Columns,
    RowsAndColumns,
}

impl TableStyleBanding {
    const fn includes_rows(self) -> bool {
        matches!(self, Self::Rows | Self::RowsAndColumns)
    }

    const fn includes_columns(self) -> bool {
        matches!(self, Self::Columns | Self::RowsAndColumns)
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableStyleRule {
    pub region: TableStyleRegion,
    pub cell_style_sha256: String,
}

impl fmt::Debug for TableStyleRule {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableStyleRule")
            .field("region", &self.region)
            .field("cell_style_sha256", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableStyleDefinitionDraft {
    pub schema_version: String,
    pub style_id: LogicalId,
    pub table_properties_sha256: String,
    pub rules: Vec<TableStyleRule>,
}

impl fmt::Debug for TableStyleDefinitionDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableStyleDefinitionDraft")
            .field("schema_version", &self.schema_version)
            .field("style_id", &"<redacted>")
            .field("table_properties_sha256", &"<redacted>")
            .field("rule_count", &self.rules.len())
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableStyleDefinition {
    schema_version: &'static str,
    style_id: LogicalId,
    table_properties_sha256: String,
    rules: Vec<TableStyleRule>,
}

impl TableStyleDefinition {
    /// Validates and canonicalizes a complete backend-neutral table-style definition.
    ///
    /// A whole-table rule is mandatory. Every optional region may occur at most once and resolution
    /// order is fixed by this contract rather than by caller input order.
    ///
    /// # Errors
    ///
    /// Rejects version, identifier, digest, missing/duplicate rule and finite-limit violations.
    pub fn from_draft(
        draft: TableStyleDefinitionDraft,
        limits: TableStyleLimits,
    ) -> Result<Self, TableStyleError> {
        if draft.schema_version != TABLE_STYLE_DEFINITION_SCHEMA_VERSION {
            return Err(TableStyleError::UnsupportedDefinitionVersion);
        }
        validate_identifier(&draft.style_id, limits)?;
        validate_digest(&draft.table_properties_sha256)?;
        if draft.rules.is_empty() || draft.rules.len() > limits.0.style_rules {
            return Err(TableStyleError::RuleLimit);
        }
        let mut rules = draft.rules;
        rules.sort_by_key(|rule| rule.region);
        if rules
            .windows(2)
            .any(|pair| pair[0].region == pair[1].region)
        {
            return Err(TableStyleError::DuplicateRule);
        }
        if rules
            .iter()
            .all(|rule| rule.region != TableStyleRegion::WholeTable)
        {
            return Err(TableStyleError::MissingWholeTableRule);
        }
        for rule in &rules {
            validate_digest(&rule.cell_style_sha256)?;
        }
        let definition = Self {
            schema_version: TABLE_STYLE_DEFINITION_SCHEMA_VERSION,
            style_id: draft.style_id,
            table_properties_sha256: draft.table_properties_sha256,
            rules,
        };
        let _ = definition.canonical_json(limits)?;
        Ok(definition)
    }

    /// Parses strict bounded JSON into a validated table-style definition.
    ///
    /// # Errors
    ///
    /// Rejects empty, oversized, malformed, duplicate-key or unknown-field JSON and every semantic
    /// failure reported by [`Self::from_draft`].
    pub fn from_json(bytes: &[u8], limits: TableStyleLimits) -> Result<Self, TableStyleError> {
        validate_input(bytes, limits)?;
        let draft = serde_json::from_slice(bytes).map_err(|_| TableStyleError::InvalidJson)?;
        Self::from_draft(draft, limits)
    }

    #[must_use]
    pub const fn style_id(&self) -> &LogicalId {
        &self.style_id
    }

    #[must_use]
    pub fn table_properties_sha256(&self) -> &str {
        &self.table_properties_sha256
    }

    #[must_use]
    pub fn rules(&self) -> &[TableStyleRule] {
        &self.rules
    }

    /// Serializes the canonical definition under the configured output bound.
    ///
    /// # Errors
    ///
    /// Rejects serialization failure or output beyond the finite bound.
    pub fn canonical_json(&self, limits: TableStyleLimits) -> Result<Vec<u8>, TableStyleError> {
        serialize_bounded(self, limits.0.serialized_bytes)
    }

    /// Returns SHA-256 over the bounded canonical definition.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failures.
    pub fn canonical_sha256(&self, limits: TableStyleLimits) -> Result<[u8; 32], TableStyleError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }

    fn rule(&self, region: TableStyleRegion) -> Option<&str> {
        self.rules
            .binary_search_by_key(&region, |rule| rule.region)
            .ok()
            .and_then(|index| self.rules.get(index))
            .map(|rule| rule.cell_style_sha256.as_str())
    }
}

impl fmt::Debug for TableStyleDefinition {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableStyleDefinition")
            .field("schema_version", &self.schema_version)
            .field("style_id", &"<redacted>")
            .field("table_properties_sha256", &"<redacted>")
            .field("rule_count", &self.rules.len())
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableStyleCellDraft {
    pub master_cell_id: LogicalId,
    pub coordinate: CellCoordinate,
    pub payload_sha256: String,
    pub formula_sha256: Option<String>,
    pub current_style_sha256: String,
}

impl fmt::Debug for TableStyleCellDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableStyleCellDraft")
            .field("master_cell_id", &"<redacted>")
            .field("coordinate", &self.coordinate)
            .field("payload_sha256", &"<redacted>")
            .field(
                "formula_sha256",
                &self.formula_sha256.as_ref().map(|_| "<redacted>"),
            )
            .field("current_style_sha256", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableStyleRequestDraft {
    pub schema_version: String,
    pub table_id: LogicalId,
    pub style_id: LogicalId,
    pub style_definition_sha256: String,
    pub current_table_properties_sha256: String,
    pub header_rows: u32,
    pub footer_rows: u32,
    pub column_emphasis: TableStyleColumnEmphasis,
    pub banding: TableStyleBanding,
    pub row_band_size: u32,
    pub column_band_size: u32,
    pub band_precedence: TableStyleBandPrecedence,
    pub merged_cell_policy: TableStyleMergedCellPolicy,
    pub cells: Vec<TableStyleCellDraft>,
}

impl fmt::Debug for TableStyleRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableStyleRequestDraft")
            .field("schema_version", &self.schema_version)
            .field("table_id", &"<redacted>")
            .field("style_id", &"<redacted>")
            .field("style_definition_sha256", &"<redacted>")
            .field("current_table_properties_sha256", &"<redacted>")
            .field("header_rows", &self.header_rows)
            .field("footer_rows", &self.footer_rows)
            .field("column_emphasis", &self.column_emphasis)
            .field("banding", &self.banding)
            .field("row_band_size", &self.row_band_size)
            .field("column_band_size", &self.column_band_size)
            .field("band_precedence", &self.band_precedence)
            .field("merged_cell_policy", &self.merged_cell_policy)
            .field("cell_count", &self.cells.len())
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableStyleRequest {
    schema_version: &'static str,
    capability_id: &'static str,
    table_id: LogicalId,
    grid_sha256: String,
    style_id: LogicalId,
    style_definition_sha256: String,
    current_table_properties_sha256: String,
    header_rows: u32,
    footer_rows: u32,
    column_emphasis: TableStyleColumnEmphasis,
    banding: TableStyleBanding,
    row_band_size: u32,
    column_band_size: u32,
    band_precedence: TableStyleBandPrecedence,
    merged_cell_policy: TableStyleMergedCellPolicy,
    cells: Vec<TableStyleCellDraft>,
}

impl TableStyleRequest {
    /// Validates a complete style application request against an exact definition and table grid.
    ///
    /// # Errors
    ///
    /// Rejects definition binding, header/footer overlap, band, grid, cell-set, digest, identifier
    /// and finite-limit drift.
    pub fn from_draft(
        draft: TableStyleRequestDraft,
        definition: &TableStyleDefinition,
        grid: &TableGrid,
        limits: TableStyleLimits,
    ) -> Result<Self, TableStyleError> {
        let TableStyleRequestDraft {
            schema_version,
            table_id,
            style_id,
            style_definition_sha256,
            current_table_properties_sha256,
            header_rows,
            footer_rows,
            column_emphasis,
            banding,
            row_band_size,
            column_band_size,
            band_precedence,
            merged_cell_policy,
            mut cells,
        } = draft;
        if schema_version != TABLE_STYLE_SCHEMA_VERSION {
            return Err(TableStyleError::UnsupportedRequestVersion);
        }
        validate_identifier(&table_id, limits)?;
        validate_identifier(&style_id, limits)?;
        validate_digest(&style_definition_sha256)?;
        validate_digest(&current_table_properties_sha256)?;
        if style_id != definition.style_id
            || style_definition_sha256 != hex(definition.canonical_sha256(limits)?)
        {
            return Err(TableStyleError::DefinitionBindingMismatch);
        }
        let designated_rows = header_rows
            .checked_add(footer_rows)
            .ok_or(TableStyleError::RegionInvalid)?;
        if designated_rows > grid.rows()
            || row_band_size == 0
            || column_band_size == 0
            || row_band_size > grid.rows()
            || column_band_size > grid.columns()
        {
            return Err(TableStyleError::RegionInvalid);
        }
        if cells.len() != grid.master_cell_count() || cells.len() > limits.0.master_cells {
            return Err(TableStyleError::CellSetMismatch);
        }
        cells.sort_by(|left, right| {
            (left.coordinate, &left.master_cell_id).cmp(&(right.coordinate, &right.master_cell_id))
        });
        if cells.windows(2).any(|pair| {
            pair[0].coordinate == pair[1].coordinate
                || pair[0].master_cell_id == pair[1].master_cell_id
        }) {
            return Err(TableStyleError::CellSetMismatch);
        }
        for (cell, span) in cells.iter().zip(grid.master_cells()) {
            if cell.master_cell_id != span.master_cell_id
                || cell.coordinate
                    != (CellCoordinate {
                        row: span.row,
                        column: span.column,
                    })
            {
                return Err(TableStyleError::CellSetMismatch);
            }
            validate_identifier(&cell.master_cell_id, limits)?;
            validate_digest(&cell.payload_sha256)?;
            validate_optional_digest(cell.formula_sha256.as_deref())?;
            validate_digest(&cell.current_style_sha256)?;
        }
        let request = Self {
            schema_version: TABLE_STYLE_SCHEMA_VERSION,
            capability_id: TABLE_STYLE_CAPABILITY_ID,
            table_id,
            grid_sha256: hex(grid
                .canonical_sha256()
                .map_err(|_| TableStyleError::GridMismatch)?),
            style_id,
            style_definition_sha256,
            current_table_properties_sha256,
            header_rows,
            footer_rows,
            column_emphasis,
            banding,
            row_band_size,
            column_band_size,
            band_precedence,
            merged_cell_policy,
            cells,
        };
        let _ = request.canonical_json(limits)?;
        Ok(request)
    }

    /// Parses strict bounded JSON and validates it against an exact definition and grid.
    ///
    /// # Errors
    ///
    /// Rejects empty, oversized, malformed, duplicate-key or unknown-field JSON and every failure
    /// reported by [`Self::from_draft`].
    pub fn from_json(
        bytes: &[u8],
        definition: &TableStyleDefinition,
        grid: &TableGrid,
        limits: TableStyleLimits,
    ) -> Result<Self, TableStyleError> {
        validate_input(bytes, limits)?;
        let draft = serde_json::from_slice(bytes).map_err(|_| TableStyleError::InvalidJson)?;
        Self::from_draft(draft, definition, grid, limits)
    }

    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
    }

    #[must_use]
    pub const fn table_id(&self) -> &LogicalId {
        &self.table_id
    }

    #[must_use]
    pub fn cells(&self) -> &[TableStyleCellDraft] {
        &self.cells
    }

    /// Serializes the validated request under the configured output bound.
    ///
    /// # Errors
    ///
    /// Rejects serialization failure or output beyond the finite bound.
    pub fn canonical_json(&self, limits: TableStyleLimits) -> Result<Vec<u8>, TableStyleError> {
        serialize_bounded(self, limits.0.serialized_bytes)
    }

    /// Returns SHA-256 over the bounded canonical request.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failures.
    pub fn canonical_sha256(&self, limits: TableStyleLimits) -> Result<[u8; 32], TableStyleError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TableStyleRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableStyleRequest")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("table_id", &"<redacted>")
            .field("grid_sha256", &"<redacted>")
            .field("style_id", &"<redacted>")
            .field("style_definition_sha256", &"<redacted>")
            .field("current_table_properties_sha256", &"<redacted>")
            .field("header_rows", &self.header_rows)
            .field("footer_rows", &self.footer_rows)
            .field("column_emphasis", &self.column_emphasis)
            .field("banding", &self.banding)
            .field("row_band_size", &self.row_band_size)
            .field("column_band_size", &self.column_band_size)
            .field("band_precedence", &self.band_precedence)
            .field("merged_cell_policy", &self.merged_cell_policy)
            .field("cell_count", &self.cells.len())
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableStyleMutation {
    pub master_cell_id: LogicalId,
    pub coordinate: CellCoordinate,
    pub resolved_region: TableStyleRegion,
    pub before_style_sha256: String,
    pub after_style_sha256: String,
    pub payload_sha256: String,
    pub formula_sha256: Option<String>,
}

impl fmt::Debug for TableStyleMutation {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableStyleMutation")
            .field("master_cell_id", &"<redacted>")
            .field("coordinate", &self.coordinate)
            .field("resolved_region", &self.resolved_region)
            .field("before_style_sha256", &"<redacted>")
            .field("after_style_sha256", &"<redacted>")
            .field("payload_sha256", &"<redacted>")
            .field(
                "formula_sha256",
                &self.formula_sha256.as_ref().map(|_| "<redacted>"),
            )
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableStyleReceipt {
    pub schema_version: &'static str,
    pub capability_id: &'static str,
    pub table_id: LogicalId,
    pub style_id: LogicalId,
    pub grid_sha256: String,
    pub style_definition_sha256: String,
    pub request_sha256: String,
    pub before_table_properties_sha256: String,
    pub after_table_properties_sha256: String,
    pub master_cell_count: usize,
    pub changed_cell_count: usize,
    pub unchanged_cell_count: usize,
    pub merged_cell_count: usize,
    pub payload_preserved_count: usize,
    pub formula_preserved_count: usize,
}

impl fmt::Debug for TableStyleReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableStyleReceipt")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("table_id", &"<redacted>")
            .field("style_id", &"<redacted>")
            .field("grid_sha256", &"<redacted>")
            .field("style_definition_sha256", &"<redacted>")
            .field("request_sha256", &"<redacted>")
            .field("before_table_properties_sha256", &"<redacted>")
            .field("after_table_properties_sha256", &"<redacted>")
            .field("master_cell_count", &self.master_cell_count)
            .field("changed_cell_count", &self.changed_cell_count)
            .field("unchanged_cell_count", &self.unchanged_cell_count)
            .field("merged_cell_count", &self.merged_cell_count)
            .field("payload_preserved_count", &self.payload_preserved_count)
            .field("formula_preserved_count", &self.formula_preserved_count)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableStylePlan {
    schema_version: &'static str,
    capability_id: &'static str,
    table_properties_sha256: String,
    mutations: Vec<TableStyleMutation>,
    receipt: TableStyleReceipt,
}

impl TableStylePlan {
    #[must_use]
    pub fn table_properties_sha256(&self) -> &str {
        &self.table_properties_sha256
    }

    #[must_use]
    pub fn mutations(&self) -> &[TableStyleMutation] {
        &self.mutations
    }

    #[must_use]
    pub const fn receipt(&self) -> &TableStyleReceipt {
        &self.receipt
    }

    /// Serializes the complete atomic style plan under the configured output bound.
    ///
    /// # Errors
    ///
    /// Rejects serialization failure or output beyond the finite bound.
    pub fn canonical_json(&self, limits: TableStyleLimits) -> Result<Vec<u8>, TableStyleError> {
        serialize_bounded(self, limits.0.serialized_bytes)
    }

    /// Returns SHA-256 over the bounded canonical plan.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failures.
    pub fn canonical_sha256(&self, limits: TableStyleLimits) -> Result<[u8; 32], TableStyleError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TableStylePlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableStylePlan")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("table_properties_sha256", &"<redacted>")
            .field("mutation_count", &self.mutations.len())
            .field("receipt", &"<redacted>")
            .finish()
    }
}

#[derive(Debug)]
pub struct TableStyleBuilder;

impl TableStyleBuilder {
    /// Resolves a deterministic style for every master cell and returns one atomic plan.
    ///
    /// For `reject_mixed_resolved_style`, every covered slot of a merged cell must resolve to the
    /// same style digest. `use_master_anchor` resolves only the span's top-left coordinate. Content
    /// and formula digests are bound and preserved by the plan.
    ///
    /// # Errors
    ///
    /// Rejects definition/grid drift, merged-region conflicts, allocation failure and bounded
    /// output failure. No partial plan or receipt is returned.
    pub fn build(
        request: &TableStyleRequest,
        definition: &TableStyleDefinition,
        grid: &TableGrid,
        limits: TableStyleLimits,
    ) -> Result<TableStylePlan, TableStyleError> {
        let grid_sha256 = hex(grid
            .canonical_sha256()
            .map_err(|_| TableStyleError::GridMismatch)?);
        if request.grid_sha256 != grid_sha256
            || request.style_id != definition.style_id
            || request.style_definition_sha256 != hex(definition.canonical_sha256(limits)?)
            || request.cells.len() != grid.master_cell_count()
        {
            return Err(TableStyleError::BindingDrift);
        }
        let mut mutations = Vec::new();
        mutations
            .try_reserve_exact(request.cells.len())
            .map_err(|_| TableStyleError::AllocationFailed)?;
        let mut changed_cell_count = 0_usize;
        let mut merged_cell_count = 0_usize;
        let mut formula_preserved_count = 0_usize;
        for (cell, span) in request.cells.iter().zip(grid.master_cells()) {
            let (resolved_region, after_style_sha256) =
                resolve_span_style(request, definition, grid, span)?;
            if span.row_span != 1 || span.column_span != 1 {
                merged_cell_count = merged_cell_count
                    .checked_add(1)
                    .ok_or(TableStyleError::MasterCellLimit)?;
            }
            if cell.current_style_sha256 != after_style_sha256 {
                changed_cell_count = changed_cell_count
                    .checked_add(1)
                    .ok_or(TableStyleError::MasterCellLimit)?;
            }
            if cell.formula_sha256.is_some() {
                formula_preserved_count = formula_preserved_count
                    .checked_add(1)
                    .ok_or(TableStyleError::MasterCellLimit)?;
            }
            mutations.push(TableStyleMutation {
                master_cell_id: cell.master_cell_id.clone(),
                coordinate: cell.coordinate,
                resolved_region,
                before_style_sha256: cell.current_style_sha256.clone(),
                after_style_sha256: after_style_sha256.to_owned(),
                payload_sha256: cell.payload_sha256.clone(),
                formula_sha256: cell.formula_sha256.clone(),
            });
        }
        let unchanged_cell_count = request
            .cells
            .len()
            .checked_sub(changed_cell_count)
            .ok_or(TableStyleError::MasterCellLimit)?;
        let receipt = TableStyleReceipt {
            schema_version: TABLE_STYLE_SCHEMA_VERSION,
            capability_id: TABLE_STYLE_CAPABILITY_ID,
            table_id: request.table_id.clone(),
            style_id: request.style_id.clone(),
            grid_sha256,
            style_definition_sha256: request.style_definition_sha256.clone(),
            request_sha256: hex(request.canonical_sha256(limits)?),
            before_table_properties_sha256: request.current_table_properties_sha256.clone(),
            after_table_properties_sha256: definition.table_properties_sha256.clone(),
            master_cell_count: request.cells.len(),
            changed_cell_count,
            unchanged_cell_count,
            merged_cell_count,
            payload_preserved_count: request.cells.len(),
            formula_preserved_count,
        };
        let plan = TableStylePlan {
            schema_version: TABLE_STYLE_SCHEMA_VERSION,
            capability_id: TABLE_STYLE_CAPABILITY_ID,
            table_properties_sha256: definition.table_properties_sha256.clone(),
            mutations,
            receipt,
        };
        let _ = plan.canonical_json(limits)?;
        Ok(plan)
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum TableStyleError {
    #[error("table style limits are invalid")]
    InvalidLimit,
    #[error("table style definition schema version is unsupported")]
    UnsupportedDefinitionVersion,
    #[error("table style request schema version is unsupported")]
    UnsupportedRequestVersion,
    #[error("table style JSON input is empty or oversized")]
    InputLimit,
    #[error("table style JSON is invalid")]
    InvalidJson,
    #[error("table style identifier exceeds its configured bound")]
    IdentifierLimit,
    #[error("table style digest is invalid")]
    DigestInvalid,
    #[error("table style rule count exceeds its configured bound")]
    RuleLimit,
    #[error("table style contains a duplicate region rule")]
    DuplicateRule,
    #[error("table style is missing its mandatory whole-table rule")]
    MissingWholeTableRule,
    #[error("table style definition identity or digest does not match")]
    DefinitionBindingMismatch,
    #[error("table style header, footer or band region is invalid")]
    RegionInvalid,
    #[error("table style master-cell set does not exactly match the grid")]
    CellSetMismatch,
    #[error("table style grid cannot be bound canonically")]
    GridMismatch,
    #[error("table style request, definition or grid changed before build")]
    BindingDrift,
    #[error("a merged table cell crosses regions that resolve to different styles")]
    MergedRegionConflict,
    #[error("table style master-cell work exceeds its configured bound")]
    MasterCellLimit,
    #[error("table style output exceeds its configured bound")]
    OutputLimit,
    #[error("table style serialization failed")]
    Serialization,
    #[error("table style allocation failed")]
    AllocationFailed,
}

impl TableStyleError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidLimit => "table_style_invalid_limit",
            Self::UnsupportedDefinitionVersion => "table_style_unsupported_definition_version",
            Self::UnsupportedRequestVersion => "table_style_unsupported_request_version",
            Self::InputLimit => "table_style_input_limit",
            Self::InvalidJson => "table_style_invalid_json",
            Self::IdentifierLimit => "table_style_identifier_limit",
            Self::DigestInvalid => "table_style_digest_invalid",
            Self::RuleLimit => "table_style_rule_limit",
            Self::DuplicateRule => "table_style_duplicate_rule",
            Self::MissingWholeTableRule => "table_style_missing_whole_table_rule",
            Self::DefinitionBindingMismatch => "table_style_definition_binding_mismatch",
            Self::RegionInvalid => "table_style_region_invalid",
            Self::CellSetMismatch => "table_style_cell_set_mismatch",
            Self::GridMismatch => "table_style_grid_mismatch",
            Self::BindingDrift => "table_style_binding_drift",
            Self::MergedRegionConflict => "table_style_merged_region_conflict",
            Self::MasterCellLimit => "table_style_master_cell_limit",
            Self::OutputLimit => "table_style_output_limit",
            Self::Serialization => "table_style_serialization",
            Self::AllocationFailed => "table_style_allocation",
        }
    }
}

fn resolve_span_style<'a>(
    request: &TableStyleRequest,
    definition: &'a TableStyleDefinition,
    grid: &TableGrid,
    span: &TableCellSpan,
) -> Result<(TableStyleRegion, &'a str), TableStyleError> {
    let anchor = CellCoordinate {
        row: span.row,
        column: span.column,
    };
    let resolved = resolve_coordinate_style(request, definition, grid, anchor)?;
    if request.merged_cell_policy == TableStyleMergedCellPolicy::UseMasterAnchor
        || (span.row_span == 1 && span.column_span == 1)
    {
        return Ok(resolved);
    }
    let row_end = span
        .row
        .checked_add(span.row_span)
        .ok_or(TableStyleError::RegionInvalid)?;
    let column_end = span
        .column
        .checked_add(span.column_span)
        .ok_or(TableStyleError::RegionInvalid)?;
    for row in span.row..row_end {
        for column in span.column..column_end {
            let candidate = resolve_coordinate_style(
                request,
                definition,
                grid,
                CellCoordinate { row, column },
            )?;
            if candidate.1 != resolved.1 {
                return Err(TableStyleError::MergedRegionConflict);
            }
        }
    }
    Ok(resolved)
}

fn resolve_coordinate_style<'a>(
    request: &TableStyleRequest,
    definition: &'a TableStyleDefinition,
    grid: &TableGrid,
    coordinate: CellCoordinate,
) -> Result<(TableStyleRegion, &'a str), TableStyleError> {
    let last_row = grid.rows() - 1;
    let last_column = grid.columns() - 1;
    let corner = if request.header_rows > 0
        && request.column_emphasis.includes_first()
        && coordinate.row == 0
        && coordinate.column == 0
    {
        Some(TableStyleRegion::TopLeftCell)
    } else if request.header_rows > 0
        && request.column_emphasis.includes_last()
        && coordinate.row == 0
        && coordinate.column == last_column
    {
        Some(TableStyleRegion::TopRightCell)
    } else if request.footer_rows > 0
        && request.column_emphasis.includes_first()
        && coordinate.row == last_row
        && coordinate.column == 0
    {
        Some(TableStyleRegion::BottomLeftCell)
    } else if request.footer_rows > 0
        && request.column_emphasis.includes_last()
        && coordinate.row == last_row
        && coordinate.column == last_column
    {
        Some(TableStyleRegion::BottomRightCell)
    } else {
        None
    };
    if let Some(region) = corner
        && let Some(style) = definition.rule(region)
    {
        return Ok((region, style));
    }
    if coordinate.row < request.header_rows
        && let Some(style) = definition.rule(TableStyleRegion::HeaderRows)
    {
        return Ok((TableStyleRegion::HeaderRows, style));
    }
    if request.footer_rows > 0
        && coordinate.row >= grid.rows() - request.footer_rows
        && let Some(style) = definition.rule(TableStyleRegion::FooterRows)
    {
        return Ok((TableStyleRegion::FooterRows, style));
    }
    if request.column_emphasis.includes_first()
        && coordinate.column == 0
        && let Some(style) = definition.rule(TableStyleRegion::FirstColumn)
    {
        return Ok((TableStyleRegion::FirstColumn, style));
    }
    if request.column_emphasis.includes_last()
        && coordinate.column == last_column
        && let Some(style) = definition.rule(TableStyleRegion::LastColumn)
    {
        return Ok((TableStyleRegion::LastColumn, style));
    }

    let row_region = request.banding.includes_rows().then(|| {
        let body_row = coordinate.row.saturating_sub(request.header_rows);
        if (body_row / request.row_band_size).is_multiple_of(2) {
            TableStyleRegion::OddRowBand
        } else {
            TableStyleRegion::EvenRowBand
        }
    });
    let column_region = request.banding.includes_columns().then(|| {
        if (coordinate.column / request.column_band_size).is_multiple_of(2) {
            TableStyleRegion::OddColumnBand
        } else {
            TableStyleRegion::EvenColumnBand
        }
    });
    let band_order = match request.band_precedence {
        TableStyleBandPrecedence::RowsFirst => [row_region, column_region],
        TableStyleBandPrecedence::ColumnsFirst => [column_region, row_region],
    };
    for region in band_order.into_iter().flatten() {
        if let Some(style) = definition.rule(region) {
            return Ok((region, style));
        }
    }
    let style = definition
        .rule(TableStyleRegion::WholeTable)
        .ok_or(TableStyleError::MissingWholeTableRule)?;
    Ok((TableStyleRegion::WholeTable, style))
}

fn validate_input(bytes: &[u8], limits: TableStyleLimits) -> Result<(), TableStyleError> {
    if bytes.is_empty() || bytes.len() > limits.0.input_bytes {
        return Err(TableStyleError::InputLimit);
    }
    Ok(())
}

fn validate_identifier(
    identifier: &LogicalId,
    limits: TableStyleLimits,
) -> Result<(), TableStyleError> {
    if identifier.as_str().len() > limits.0.identifier_bytes {
        return Err(TableStyleError::IdentifierLimit);
    }
    Ok(())
}

fn validate_optional_digest(value: Option<&str>) -> Result<(), TableStyleError> {
    if let Some(value) = value {
        validate_digest(value)?;
    }
    Ok(())
}

fn validate_digest(value: &str) -> Result<(), TableStyleError> {
    if value.len() != 64
        || value
            .bytes()
            .any(|byte| !byte.is_ascii_digit() && !(b'a'..=b'f').contains(&byte))
    {
        return Err(TableStyleError::DigestInvalid);
    }
    Ok(())
}

fn serialize_bounded<T: Serialize>(value: &T, maximum: usize) -> Result<Vec<u8>, TableStyleError> {
    let bytes = serde_json::to_vec(value).map_err(|_| TableStyleError::Serialization)?;
    if bytes.len() > maximum {
        return Err(TableStyleError::OutputLimit);
    }
    Ok(bytes)
}

fn hex(value: [u8; 32]) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(64);
    for byte in value {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}
