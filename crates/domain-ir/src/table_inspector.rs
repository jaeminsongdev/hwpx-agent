use std::collections::BTreeMap;
use std::fmt;
use std::io;

use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{
    CellCoordinate, DocumentGraph, Flow, LogicalId, Node, NodeKind, RevisionId, StructuralPath,
    StructuralRoot, StructuralStep, TableCellSpan, TableGrid, TableGridError, TableGridLimits,
    TableNode,
};

pub const TABLE_INSPECTION_SCHEMA_VERSION: &str = "hwpx-agent.table-inspection/v1";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TableInspectionLimitConfig {
    pub tables: usize,
    pub master_cells: usize,
    pub path_steps: usize,
    pub nested_depth: usize,
    pub serialized_bytes: usize,
}

impl Default for TableInspectionLimitConfig {
    fn default() -> Self {
        Self {
            tables: 100_000,
            master_cells: 1_000_000,
            path_steps: 64,
            nested_depth: 64,
            serialized_bytes: 32 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TableInspectionLimits(TableInspectionLimitConfig);

impl TableInspectionLimits {
    pub const HARD_MAX_TABLES: usize = 1_000_000;
    pub const HARD_MAX_MASTER_CELLS: usize = 1_000_000;
    pub const HARD_MAX_PATH_STEPS: usize = 256;
    pub const HARD_MAX_NESTED_DEPTH: usize = 256;
    pub const HARD_MAX_SERIALIZED_BYTES: usize = 256 * 1024 * 1024;

    /// Creates finite limits for one immutable table-inspection snapshot.
    ///
    /// # Errors
    ///
    /// Rejects zero values and values above the hard ceilings.
    pub fn new(config: TableInspectionLimitConfig) -> Result<Self, TableInspectionError> {
        if config.tables == 0
            || config.tables > Self::HARD_MAX_TABLES
            || config.master_cells == 0
            || config.master_cells > Self::HARD_MAX_MASTER_CELLS
            || config.path_steps == 0
            || config.path_steps > Self::HARD_MAX_PATH_STEPS
            || config.nested_depth == 0
            || config.nested_depth > Self::HARD_MAX_NESTED_DEPTH
            || config.serialized_bytes == 0
            || config.serialized_bytes > Self::HARD_MAX_SERIALIZED_BYTES
        {
            return Err(TableInspectionError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> TableInspectionLimitConfig {
        self.0
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableInspectionExpectation {
    revision_id: RevisionId,
    graph_sha256: [u8; 32],
}

impl TableInspectionExpectation {
    #[must_use]
    pub fn new(revision_id: RevisionId, graph_sha256: [u8; 32]) -> Self {
        Self {
            revision_id,
            graph_sha256,
        }
    }

    #[must_use]
    pub const fn revision_id(&self) -> &RevisionId {
        &self.revision_id
    }

    #[must_use]
    pub const fn graph_sha256(&self) -> [u8; 32] {
        self.graph_sha256
    }
}

impl fmt::Debug for TableInspectionExpectation {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("TableInspectionExpectation(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableSelector {
    table_id: LogicalId,
    structural_path: StructuralPath,
    table_fingerprint_sha256: [u8; 32],
}

impl TableSelector {
    /// Restores a previously persisted stable table selector.
    ///
    /// # Errors
    ///
    /// Rejects a zero fingerprint or a path that does not terminate at a table node.
    pub fn restore(
        table_id: LogicalId,
        structural_path: StructuralPath,
        table_fingerprint_sha256: [u8; 32],
    ) -> Result<Self, TableInspectionError> {
        if table_fingerprint_sha256 == [0; 32] || !valid_table_path(&structural_path) {
            return Err(TableInspectionError::InvalidSelector);
        }
        Ok(Self {
            table_id,
            structural_path,
            table_fingerprint_sha256,
        })
    }

    #[must_use]
    pub const fn table_id(&self) -> &LogicalId {
        &self.table_id
    }

    #[must_use]
    pub const fn structural_path(&self) -> &StructuralPath {
        &self.structural_path
    }

    #[must_use]
    pub const fn table_fingerprint_sha256(&self) -> [u8; 32] {
        self.table_fingerprint_sha256
    }
}

impl fmt::Debug for TableSelector {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("TableSelector(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableCellSelector {
    table: TableSelector,
    requested_coordinate: CellCoordinate,
    master_cell_id: LogicalId,
    master_cell_fingerprint_sha256: [u8; 32],
}

impl TableCellSelector {
    /// Restores a previously persisted stable table-cell selector.
    ///
    /// # Errors
    ///
    /// Rejects a zero master-cell fingerprint. Grid bounds and all anchors are checked on resolve.
    pub fn restore(
        table: TableSelector,
        requested_coordinate: CellCoordinate,
        master_cell_id: LogicalId,
        master_cell_fingerprint_sha256: [u8; 32],
    ) -> Result<Self, TableInspectionError> {
        if master_cell_fingerprint_sha256 == [0; 32] {
            return Err(TableInspectionError::InvalidSelector);
        }
        Ok(Self {
            table,
            requested_coordinate,
            master_cell_id,
            master_cell_fingerprint_sha256,
        })
    }

    #[must_use]
    pub const fn table(&self) -> &TableSelector {
        &self.table
    }

    #[must_use]
    pub const fn requested_coordinate(&self) -> CellCoordinate {
        self.requested_coordinate
    }

    #[must_use]
    pub const fn master_cell_id(&self) -> &LogicalId {
        &self.master_cell_id
    }

    #[must_use]
    pub const fn master_cell_fingerprint_sha256(&self) -> [u8; 32] {
        self.master_cell_fingerprint_sha256
    }
}

impl fmt::Debug for TableCellSelector {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("TableCellSelector(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableInspection {
    table_id: LogicalId,
    structural_path: StructuralPath,
    rows: u32,
    columns: u32,
    master_cell_count: usize,
    direct_nested_table_ids: Vec<LogicalId>,
    table_fingerprint_sha256: [u8; 32],
    grid_sha256: [u8; 32],
}

impl TableInspection {
    #[must_use]
    pub const fn table_id(&self) -> &LogicalId {
        &self.table_id
    }

    #[must_use]
    pub const fn structural_path(&self) -> &StructuralPath {
        &self.structural_path
    }

    #[must_use]
    pub const fn rows(&self) -> u32 {
        self.rows
    }

    #[must_use]
    pub const fn columns(&self) -> u32 {
        self.columns
    }

    #[must_use]
    pub const fn master_cell_count(&self) -> usize {
        self.master_cell_count
    }

    #[must_use]
    pub fn direct_nested_table_ids(&self) -> &[LogicalId] {
        &self.direct_nested_table_ids
    }

    #[must_use]
    pub const fn table_fingerprint_sha256(&self) -> [u8; 32] {
        self.table_fingerprint_sha256
    }

    #[must_use]
    pub const fn grid_sha256(&self) -> [u8; 32] {
        self.grid_sha256
    }
}

impl fmt::Debug for TableInspection {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableInspection")
            .field("rows", &self.rows)
            .field("columns", &self.columns)
            .field("master_cell_count", &self.master_cell_count)
            .field(
                "direct_nested_table_count",
                &self.direct_nested_table_ids.len(),
            )
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ResolvedTableCell {
    table_id: LogicalId,
    table_path: StructuralPath,
    requested_coordinate: CellCoordinate,
    master_cell_id: LogicalId,
    master_coordinate: CellCoordinate,
    row_span: u32,
    column_span: u32,
    direct_nested_table_ids: Vec<LogicalId>,
    master_cell_fingerprint_sha256: [u8; 32],
}

impl ResolvedTableCell {
    #[must_use]
    pub const fn table_id(&self) -> &LogicalId {
        &self.table_id
    }

    #[must_use]
    pub const fn table_path(&self) -> &StructuralPath {
        &self.table_path
    }

    #[must_use]
    pub const fn requested_coordinate(&self) -> CellCoordinate {
        self.requested_coordinate
    }

    #[must_use]
    pub const fn master_cell_id(&self) -> &LogicalId {
        &self.master_cell_id
    }

    #[must_use]
    pub const fn master_coordinate(&self) -> CellCoordinate {
        self.master_coordinate
    }

    #[must_use]
    pub const fn row_span(&self) -> u32 {
        self.row_span
    }

    #[must_use]
    pub const fn column_span(&self) -> u32 {
        self.column_span
    }

    #[must_use]
    pub fn direct_nested_table_ids(&self) -> &[LogicalId] {
        &self.direct_nested_table_ids
    }

    #[must_use]
    pub const fn master_cell_fingerprint_sha256(&self) -> [u8; 32] {
        self.master_cell_fingerprint_sha256
    }
}

impl fmt::Debug for ResolvedTableCell {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ResolvedTableCell")
            .field("requested_coordinate", &self.requested_coordinate)
            .field("master_coordinate", &self.master_coordinate)
            .field("row_span", &self.row_span)
            .field("column_span", &self.column_span)
            .field(
                "direct_nested_table_count",
                &self.direct_nested_table_ids.len(),
            )
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum TableInspectionError {
    #[error("table inspection limits are invalid")]
    InvalidLimit,
    #[error("table inspection limit exceeded")]
    LimitExceeded,
    #[error("table inspection graph is invalid")]
    InvalidGraph,
    #[error("table inspection serialization failed")]
    SerializationFailed,
    #[error("table inspection allocation failed")]
    AllocationFailed,
    #[error("table inspection selector is invalid")]
    InvalidSelector,
    #[error("table inspection snapshot is stale")]
    Stale,
    #[error("table inspection table was not found")]
    TableNotFound,
    #[error("table inspection cell was not found")]
    CellNotFound,
    #[error("table inspection coordinate is outside the table")]
    CoordinateOutOfBounds,
}

impl TableInspectionError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidLimit => "table_inspection_invalid_limit",
            Self::LimitExceeded => "table_inspection_limit_exceeded",
            Self::InvalidGraph => "table_inspection_invalid_graph",
            Self::SerializationFailed => "table_inspection_serialization_failed",
            Self::AllocationFailed => "table_inspection_allocation_failed",
            Self::InvalidSelector => "table_inspection_invalid_selector",
            Self::Stale => "table_inspection_stale",
            Self::TableNotFound => "table_inspection_table_not_found",
            Self::CellNotFound => "table_inspection_cell_not_found",
            Self::CoordinateOutOfBounds => "table_inspection_coordinate_out_of_bounds",
        }
    }
}

struct CellRecord {
    master_cell_id: LogicalId,
    coordinate: CellCoordinate,
    row_span: u32,
    column_span: u32,
    fingerprint_sha256: [u8; 32],
    direct_nested_table_ids: Vec<LogicalId>,
}

struct TableRecord {
    table_id: LogicalId,
    path: StructuralPath,
    table_fingerprint_sha256: [u8; 32],
    grid_sha256: [u8; 32],
    grid: TableGrid,
    cells: Vec<CellRecord>,
    by_cell_id: BTreeMap<LogicalId, usize>,
}

pub struct TableInspectionSnapshot {
    revision_id: RevisionId,
    graph_sha256: [u8; 32],
    limits: TableInspectionLimits,
    records: Vec<TableRecord>,
    by_table_id: BTreeMap<LogicalId, usize>,
    by_path: BTreeMap<StructuralPath, usize>,
    master_cell_count: usize,
}

impl TableInspectionSnapshot {
    /// Builds an immutable index of every top-level and nested table in a validated graph.
    ///
    /// # Errors
    ///
    /// Fails closed on invalid limits, graph/grid inconsistencies, excessive nesting, duplicate
    /// anchors, allocation failure, or bounded serialization failure.
    pub fn build(
        graph: &DocumentGraph,
        revision_id: RevisionId,
        limits: TableInspectionLimits,
    ) -> Result<Self, TableInspectionError> {
        TableInspectionLimits::new(limits.0)?;
        let graph_sha256 = graph
            .canonical_sha256()
            .map_err(|_| TableInspectionError::SerializationFailed)?;
        let mut snapshot = Self {
            revision_id,
            graph_sha256,
            limits,
            records: Vec::new(),
            by_table_id: BTreeMap::new(),
            by_path: BTreeMap::new(),
            master_cell_count: 0,
        };

        for (section_index, section) in graph.sections().iter().enumerate() {
            let index =
                u32::try_from(section_index).map_err(|_| TableInspectionError::LimitExceeded)?;
            snapshot.index_flow(
                &section.body,
                StructuralRoot::Section { index },
                &mut Vec::new(),
                None,
                0,
            )?;
        }
        for (note_index, note) in graph.draft().notes.iter().enumerate() {
            let index =
                u32::try_from(note_index).map_err(|_| TableInspectionError::LimitExceeded)?;
            snapshot.index_flow(
                &note.body,
                StructuralRoot::Note { index },
                &mut Vec::new(),
                None,
                0,
            )?;
        }
        for record in &mut snapshot.records {
            for cell in &mut record.cells {
                cell.direct_nested_table_ids.sort();
            }
        }
        let _ = snapshot.canonical_json()?;
        Ok(snapshot)
    }

    #[must_use]
    pub fn expectation(&self) -> TableInspectionExpectation {
        TableInspectionExpectation::new(self.revision_id.clone(), self.graph_sha256)
    }

    #[must_use]
    pub fn table_count(&self) -> usize {
        self.records.len()
    }

    #[must_use]
    pub const fn master_cell_count(&self) -> usize {
        self.master_cell_count
    }

    /// Creates a stable selector anchored by logical ID, structural path, and table fingerprint.
    ///
    /// # Errors
    ///
    /// Returns `TableNotFound` for an unknown table ID.
    pub fn table_selector_for(
        &self,
        table_id: &LogicalId,
    ) -> Result<TableSelector, TableInspectionError> {
        let record = self.table_record_by_id(table_id)?;
        TableSelector::restore(
            record.table_id.clone(),
            record.path.clone(),
            record.table_fingerprint_sha256,
        )
    }

    /// Creates a stable selector for the master cell covering one logical coordinate.
    ///
    /// # Errors
    ///
    /// Returns a table, coordinate, or graph error without choosing a fallback cell.
    pub fn cell_selector_at(
        &self,
        table_id: &LogicalId,
        requested_coordinate: CellCoordinate,
    ) -> Result<TableCellSelector, TableInspectionError> {
        let table = self.table_record_by_id(table_id)?;
        let span = table
            .grid
            .master_cell_at(requested_coordinate)
            .map_err(map_coordinate_error)?;
        let cell = table
            .by_cell_id
            .get(&span.master_cell_id)
            .and_then(|index| table.cells.get(*index))
            .ok_or(TableInspectionError::InvalidGraph)?;
        TableCellSelector::restore(
            self.table_selector_for(table_id)?,
            requested_coordinate,
            cell.master_cell_id.clone(),
            cell.fingerprint_sha256,
        )
    }

    /// Creates a stable selector for one exact master-cell logical ID.
    ///
    /// # Errors
    ///
    /// Returns a table or cell not-found error. Covered non-master slots have no separate ID.
    pub fn cell_selector_for(
        &self,
        table_id: &LogicalId,
        master_cell_id: &LogicalId,
    ) -> Result<TableCellSelector, TableInspectionError> {
        let table = self.table_record_by_id(table_id)?;
        let cell = table
            .by_cell_id
            .get(master_cell_id)
            .and_then(|index| table.cells.get(*index))
            .ok_or(TableInspectionError::CellNotFound)?;
        TableCellSelector::restore(
            self.table_selector_for(table_id)?,
            cell.coordinate,
            cell.master_cell_id.clone(),
            cell.fingerprint_sha256,
        )
    }

    /// Resolves exactly one table against the pinned revision and all selector anchors.
    ///
    /// # Errors
    ///
    /// Checks staleness before lookup and never falls back to an index-only match.
    pub fn resolve_table(
        &self,
        expectation: &TableInspectionExpectation,
        selector: &TableSelector,
    ) -> Result<TableInspection, TableInspectionError> {
        inspect_table(self.validated_table_record(expectation, selector)?)
    }

    /// Resolves one requested logical slot to its exact canonical master cell.
    ///
    /// # Errors
    ///
    /// Rejects stale revision, table path/fingerprint, master identity, cell fingerprint, and
    /// out-of-range coordinates before returning a result.
    pub fn resolve_cell(
        &self,
        expectation: &TableInspectionExpectation,
        selector: &TableCellSelector,
    ) -> Result<ResolvedTableCell, TableInspectionError> {
        let table = self.validated_table_record(expectation, &selector.table)?;
        let span = table
            .grid
            .master_cell_at(selector.requested_coordinate)
            .map_err(map_coordinate_error)?;
        if span.master_cell_id != selector.master_cell_id {
            return Err(TableInspectionError::Stale);
        }
        let cell = table
            .by_cell_id
            .get(&span.master_cell_id)
            .and_then(|index| table.cells.get(*index))
            .ok_or(TableInspectionError::InvalidGraph)?;
        if cell.fingerprint_sha256 != selector.master_cell_fingerprint_sha256 {
            return Err(TableInspectionError::Stale);
        }
        Ok(resolve_cell(table, cell, selector.requested_coordinate))
    }

    /// Emits a bounded, canonical metadata-only snapshot. Cell bodies are never included.
    ///
    /// # Errors
    ///
    /// Returns a stable output limit, allocation, or serialization error.
    pub fn canonical_json(&self) -> Result<Vec<u8>, TableInspectionError> {
        let mut tables = Vec::new();
        tables
            .try_reserve_exact(self.records.len())
            .map_err(|_| TableInspectionError::AllocationFailed)?;
        for index in self.by_table_id.values() {
            let record = self
                .records
                .get(*index)
                .ok_or(TableInspectionError::InvalidGraph)?;
            tables.push(CanonicalTableRecord::try_from(record)?);
        }
        let canonical = CanonicalSnapshot {
            schema_version: TABLE_INSPECTION_SCHEMA_VERSION,
            revision_id: &self.revision_id,
            graph_sha256: self.graph_sha256,
            tables,
        };
        let mut writer = BoundedWriter::new(self.limits.0.serialized_bytes);
        if serde_json::to_writer(&mut writer, &canonical).is_err() {
            return Err(match writer.failure {
                WriterFailure::Limit => TableInspectionError::LimitExceeded,
                WriterFailure::Allocation => TableInspectionError::AllocationFailed,
                WriterFailure::None => TableInspectionError::SerializationFailed,
            });
        }
        Ok(writer.bytes)
    }

    /// Hashes the canonical metadata-only snapshot.
    ///
    /// # Errors
    ///
    /// Propagates bounded canonical serialization failures.
    pub fn canonical_sha256(&self) -> Result<[u8; 32], TableInspectionError> {
        Ok(Sha256::digest(self.canonical_json()?).into())
    }

    fn validate_expectation(
        &self,
        expectation: &TableInspectionExpectation,
    ) -> Result<(), TableInspectionError> {
        if expectation.revision_id != self.revision_id
            || expectation.graph_sha256 != self.graph_sha256
        {
            return Err(TableInspectionError::Stale);
        }
        Ok(())
    }

    fn table_record_by_id(
        &self,
        table_id: &LogicalId,
    ) -> Result<&TableRecord, TableInspectionError> {
        self.by_table_id
            .get(table_id)
            .and_then(|index| self.records.get(*index))
            .ok_or(TableInspectionError::TableNotFound)
    }

    fn validated_table_record(
        &self,
        expectation: &TableInspectionExpectation,
        selector: &TableSelector,
    ) -> Result<&TableRecord, TableInspectionError> {
        self.validate_expectation(expectation)?;
        let record = self.table_record_by_id(&selector.table_id)?;
        if record.path != selector.structural_path
            || record.table_fingerprint_sha256 != selector.table_fingerprint_sha256
            || self.by_path.get(&selector.structural_path).copied()
                != self.by_table_id.get(&selector.table_id).copied()
        {
            return Err(TableInspectionError::Stale);
        }
        Ok(record)
    }

    fn index_flow(
        &mut self,
        flow: &Flow,
        root: StructuralRoot,
        prefix: &mut Vec<StructuralStep>,
        container_cell: Option<(usize, usize)>,
        table_depth: usize,
    ) -> Result<(), TableInspectionError> {
        for (child_index, node) in flow.children.iter().enumerate() {
            let index =
                u32::try_from(child_index).map_err(|_| TableInspectionError::LimitExceeded)?;
            prefix.push(StructuralStep::FlowChild {
                index,
                expected_kind: node_kind(node),
            });
            if prefix.len() > self.limits.0.path_steps {
                return Err(TableInspectionError::LimitExceeded);
            }
            match node {
                Node::Table(table) => {
                    let next_depth = table_depth
                        .checked_add(1)
                        .ok_or(TableInspectionError::LimitExceeded)?;
                    if next_depth > self.limits.0.nested_depth {
                        return Err(TableInspectionError::LimitExceeded);
                    }
                    let path = structural_path(root, prefix.clone())?;
                    let record_index = self.add_table(table, path)?;
                    if let Some((parent_table_index, parent_cell_index)) = container_cell {
                        let nested_id = self.records[record_index].table_id.clone();
                        self.records
                            .get_mut(parent_table_index)
                            .and_then(|record| record.cells.get_mut(parent_cell_index))
                            .ok_or(TableInspectionError::InvalidGraph)?
                            .direct_nested_table_ids
                            .push(nested_id);
                    }
                    for cell in &table.cells {
                        let cell_index = self.records[record_index]
                            .by_cell_id
                            .get(&cell.cell_id)
                            .copied()
                            .ok_or(TableInspectionError::InvalidGraph)?;
                        prefix.push(StructuralStep::TableCell {
                            row: cell.row,
                            column: cell.column,
                        });
                        if prefix.len() > self.limits.0.path_steps {
                            return Err(TableInspectionError::LimitExceeded);
                        }
                        self.index_flow(
                            &cell.body,
                            root,
                            prefix,
                            Some((record_index, cell_index)),
                            next_depth,
                        )?;
                        let _ = prefix.pop();
                    }
                }
                Node::Drawing(drawing) => {
                    self.index_flow(&drawing.children, root, prefix, container_cell, table_depth)?;
                }
                Node::Paragraph(_)
                | Node::Equation(_)
                | Node::Chart(_)
                | Node::Field(_)
                | Node::FormControl(_)
                | Node::Break(_)
                | Node::EmbeddedObject(_) => {}
            }
            let _ = prefix.pop();
        }
        Ok(())
    }

    fn add_table(
        &mut self,
        table: &TableNode,
        path: StructuralPath,
    ) -> Result<usize, TableInspectionError> {
        if self.records.len() >= self.limits.0.tables {
            return Err(TableInspectionError::LimitExceeded);
        }
        self.master_cell_count = self
            .master_cell_count
            .checked_add(table.cells.len())
            .ok_or(TableInspectionError::LimitExceeded)?;
        if self.master_cell_count > self.limits.0.master_cells {
            return Err(TableInspectionError::LimitExceeded);
        }
        let mut cells = Vec::new();
        cells
            .try_reserve_exact(table.cells.len())
            .map_err(|_| TableInspectionError::AllocationFailed)?;
        for cell in &table.cells {
            cells.push(CellRecord {
                master_cell_id: cell.cell_id.clone(),
                coordinate: CellCoordinate {
                    row: cell.row,
                    column: cell.column,
                },
                row_span: cell.row_span,
                column_span: cell.column_span,
                fingerprint_sha256: fingerprint(cell)?,
                direct_nested_table_ids: Vec::new(),
            });
        }
        cells.sort_by(|left, right| {
            (left.coordinate, &left.master_cell_id).cmp(&(right.coordinate, &right.master_cell_id))
        });
        let by_cell_id: BTreeMap<LogicalId, usize> = cells
            .iter()
            .enumerate()
            .map(|(index, cell)| (cell.master_cell_id.clone(), index))
            .collect();
        if by_cell_id.len() != cells.len() {
            return Err(TableInspectionError::InvalidGraph);
        }

        let spans = cells
            .iter()
            .map(|cell| TableCellSpan {
                master_cell_id: cell.master_cell_id.clone(),
                row: cell.coordinate.row,
                column: cell.coordinate.column,
                row_span: cell.row_span,
                column_span: cell.column_span,
            })
            .collect();
        let grid = TableGrid::new(table.rows, table.columns, spans, TableGridLimits::default())
            .map_err(map_grid_build_error)?;
        let record = TableRecord {
            table_id: table.common.node_id.clone(),
            path: path.clone(),
            table_fingerprint_sha256: fingerprint(table)?,
            grid_sha256: grid.canonical_sha256().map_err(map_grid_build_error)?,
            grid,
            cells,
            by_cell_id,
        };
        let index = self.records.len();
        if self
            .by_table_id
            .insert(record.table_id.clone(), index)
            .is_some()
            || self.by_path.insert(path, index).is_some()
        {
            return Err(TableInspectionError::InvalidGraph);
        }
        self.records.push(record);
        Ok(index)
    }
}

impl fmt::Debug for TableInspectionSnapshot {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableInspectionSnapshot")
            .field("table_count", &self.records.len())
            .field("master_cell_count", &self.master_cell_count)
            .finish_non_exhaustive()
    }
}

fn inspect_table(record: &TableRecord) -> Result<TableInspection, TableInspectionError> {
    let nested_count = record.cells.iter().try_fold(0_usize, |count, cell| {
        count
            .checked_add(cell.direct_nested_table_ids.len())
            .ok_or(TableInspectionError::LimitExceeded)
    })?;
    let mut direct_nested_table_ids = Vec::new();
    direct_nested_table_ids
        .try_reserve_exact(nested_count)
        .map_err(|_| TableInspectionError::AllocationFailed)?;
    for cell in &record.cells {
        direct_nested_table_ids.extend(cell.direct_nested_table_ids.iter().cloned());
    }
    direct_nested_table_ids.sort();
    Ok(TableInspection {
        table_id: record.table_id.clone(),
        structural_path: record.path.clone(),
        rows: record.grid.rows(),
        columns: record.grid.columns(),
        master_cell_count: record.grid.master_cell_count(),
        direct_nested_table_ids,
        table_fingerprint_sha256: record.table_fingerprint_sha256,
        grid_sha256: record.grid_sha256,
    })
}

fn resolve_cell(
    table: &TableRecord,
    cell: &CellRecord,
    requested_coordinate: CellCoordinate,
) -> ResolvedTableCell {
    let mut direct_nested_table_ids = cell.direct_nested_table_ids.clone();
    direct_nested_table_ids.sort();
    ResolvedTableCell {
        table_id: table.table_id.clone(),
        table_path: table.path.clone(),
        requested_coordinate,
        master_cell_id: cell.master_cell_id.clone(),
        master_coordinate: cell.coordinate,
        row_span: cell.row_span,
        column_span: cell.column_span,
        direct_nested_table_ids,
        master_cell_fingerprint_sha256: cell.fingerprint_sha256,
    }
}

fn structural_path(
    root: StructuralRoot,
    steps: Vec<StructuralStep>,
) -> Result<StructuralPath, TableInspectionError> {
    match root {
        StructuralRoot::Section { index } => StructuralPath::new(index, steps),
        StructuralRoot::Note { index } => StructuralPath::new_note(index, steps),
    }
    .map_err(|_| TableInspectionError::InvalidGraph)
}

fn valid_table_path(path: &StructuralPath) -> bool {
    let steps = path.steps();
    matches!(steps.first(), Some(StructuralStep::FlowChild { .. }))
        && matches!(
            steps.last(),
            Some(StructuralStep::FlowChild {
                expected_kind: NodeKind::Table,
                ..
            })
        )
        && steps.windows(2).all(|pair| {
            matches!(
                (&pair[0], &pair[1]),
                (
                    StructuralStep::FlowChild {
                        expected_kind: NodeKind::Table,
                        ..
                    },
                    StructuralStep::TableCell { .. },
                ) | (
                    StructuralStep::FlowChild {
                        expected_kind: NodeKind::Drawing,
                        ..
                    },
                    StructuralStep::FlowChild { .. },
                ) | (
                    StructuralStep::TableCell { .. },
                    StructuralStep::FlowChild { .. },
                )
            )
        })
}

const fn node_kind(node: &Node) -> NodeKind {
    match node {
        Node::Paragraph(_) => NodeKind::Paragraph,
        Node::Table(_) => NodeKind::Table,
        Node::Equation(_) => NodeKind::Equation,
        Node::Drawing(_) => NodeKind::Drawing,
        Node::Chart(_) => NodeKind::Chart,
        Node::Field(_) => NodeKind::Field,
        Node::FormControl(_) => NodeKind::FormControl,
        Node::Break(_) => NodeKind::Break,
        Node::EmbeddedObject(_) => NodeKind::EmbeddedObject,
    }
}

fn fingerprint<T: Serialize>(value: &T) -> Result<[u8; 32], TableInspectionError> {
    let mut writer = DigestWriter::new(TableInspectionLimits::HARD_MAX_SERIALIZED_BYTES);
    if serde_json::to_writer(&mut writer, value).is_err() {
        return Err(if writer.limit_exceeded {
            TableInspectionError::LimitExceeded
        } else {
            TableInspectionError::SerializationFailed
        });
    }
    Ok(writer.hasher.finalize().into())
}

fn map_grid_build_error(error: TableGridError) -> TableInspectionError {
    match error {
        TableGridError::InvalidLimit
        | TableGridError::DimensionLimitExceeded
        | TableGridError::SlotCapacityOverflow
        | TableGridError::SlotLimitExceeded
        | TableGridError::MasterCellLimitExceeded
        | TableGridError::IdentifierLimitExceeded
        | TableGridError::OutputLimitExceeded
        | TableGridError::InputLimitExceeded => TableInspectionError::LimitExceeded,
        TableGridError::AllocationFailed => TableInspectionError::AllocationFailed,
        TableGridError::SerializationFailed => TableInspectionError::SerializationFailed,
        TableGridError::UnsupportedVersion
        | TableGridError::InvalidJson
        | TableGridError::EmptyGrid
        | TableGridError::DuplicateMasterCell
        | TableGridError::EmptySpan
        | TableGridError::SpanOverflow
        | TableGridError::SpanOutOfBounds
        | TableGridError::DuplicateCoveredSlot
        | TableGridError::NonRectangularSpan
        | TableGridError::OverlappingSpan
        | TableGridError::UncoveredSlot
        | TableGridError::CoordinateOutOfBounds => TableInspectionError::InvalidGraph,
    }
}

fn map_coordinate_error(error: TableGridError) -> TableInspectionError {
    match error {
        TableGridError::CoordinateOutOfBounds => TableInspectionError::CoordinateOutOfBounds,
        other => map_grid_build_error(other),
    }
}

#[derive(Serialize)]
struct CanonicalSnapshot<'a> {
    schema_version: &'static str,
    revision_id: &'a RevisionId,
    graph_sha256: [u8; 32],
    tables: Vec<CanonicalTableRecord<'a>>,
}

#[derive(Serialize)]
struct CanonicalTableRecord<'a> {
    table_id: &'a LogicalId,
    structural_path: &'a StructuralPath,
    rows: u32,
    columns: u32,
    table_fingerprint_sha256: [u8; 32],
    grid_sha256: [u8; 32],
    cells: Vec<CanonicalCellRecord<'a>>,
}

impl<'a> TryFrom<&'a TableRecord> for CanonicalTableRecord<'a> {
    type Error = TableInspectionError;

    fn try_from(record: &'a TableRecord) -> Result<Self, Self::Error> {
        let mut cells = Vec::new();
        cells
            .try_reserve_exact(record.cells.len())
            .map_err(|_| TableInspectionError::AllocationFailed)?;
        for cell in &record.cells {
            cells.push(CanonicalCellRecord::from(cell));
        }
        Ok(Self {
            table_id: &record.table_id,
            structural_path: &record.path,
            rows: record.grid.rows(),
            columns: record.grid.columns(),
            table_fingerprint_sha256: record.table_fingerprint_sha256,
            grid_sha256: record.grid_sha256,
            cells,
        })
    }
}

#[derive(Serialize)]
struct CanonicalCellRecord<'a> {
    master_cell_id: &'a LogicalId,
    coordinate: CellCoordinate,
    row_span: u32,
    column_span: u32,
    fingerprint_sha256: [u8; 32],
    direct_nested_table_ids: &'a [LogicalId],
}

impl<'a> From<&'a CellRecord> for CanonicalCellRecord<'a> {
    fn from(record: &'a CellRecord) -> Self {
        Self {
            master_cell_id: &record.master_cell_id,
            coordinate: record.coordinate,
            row_span: record.row_span,
            column_span: record.column_span,
            fingerprint_sha256: record.fingerprint_sha256,
            direct_nested_table_ids: &record.direct_nested_table_ids,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum WriterFailure {
    None,
    Limit,
    Allocation,
}

struct BoundedWriter {
    bytes: Vec<u8>,
    max_bytes: usize,
    failure: WriterFailure,
}

struct DigestWriter {
    hasher: Sha256,
    bytes_written: usize,
    max_bytes: usize,
    limit_exceeded: bool,
}

impl DigestWriter {
    fn new(max_bytes: usize) -> Self {
        Self {
            hasher: Sha256::new(),
            bytes_written: 0,
            max_bytes,
            limit_exceeded: false,
        }
    }
}

impl io::Write for DigestWriter {
    fn write(&mut self, buffer: &[u8]) -> io::Result<usize> {
        let Some(next_length) = self.bytes_written.checked_add(buffer.len()) else {
            self.limit_exceeded = true;
            return Err(io::Error::other("table inspection digest limit"));
        };
        if next_length > self.max_bytes {
            self.limit_exceeded = true;
            return Err(io::Error::other("table inspection digest limit"));
        }
        self.hasher.update(buffer);
        self.bytes_written = next_length;
        Ok(buffer.len())
    }

    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}

impl BoundedWriter {
    const fn new(max_bytes: usize) -> Self {
        Self {
            bytes: Vec::new(),
            max_bytes,
            failure: WriterFailure::None,
        }
    }
}

impl io::Write for BoundedWriter {
    fn write(&mut self, buffer: &[u8]) -> io::Result<usize> {
        let Some(next_length) = self.bytes.len().checked_add(buffer.len()) else {
            self.failure = WriterFailure::Limit;
            return Err(io::Error::other("table inspection output limit"));
        };
        if next_length > self.max_bytes {
            self.failure = WriterFailure::Limit;
            return Err(io::Error::other("table inspection output limit"));
        }
        if self.bytes.try_reserve(buffer.len()).is_err() {
            self.failure = WriterFailure::Allocation;
            return Err(io::Error::other("table inspection allocation"));
        }
        self.bytes.extend_from_slice(buffer);
        Ok(buffer.len())
    }

    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}
