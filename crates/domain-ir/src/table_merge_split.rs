use std::fmt;
use std::io;

use serde::{Deserialize, Serialize};
use thiserror::Error;

use crate::{CellCoordinate, LogicalId, TableCellSpan, TableGrid, TableGridError, TableGridLimits};

pub const TABLE_MERGE_SPLIT_SCHEMA_VERSION: &str = "hwpx-agent.table-merge-split/v1";

const HARD_MAX_RECEIPT_BYTES: usize = 256 * 1024 * 1024;

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ContentPreservationPolicy {
    Concatenate,
    First,
    Distribute,
    RejectIfMultiple,
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableCellContent {
    master_cell_id: LogicalId,
    content_block_ids: Vec<LogicalId>,
}

impl TableCellContent {
    #[must_use]
    pub fn new(master_cell_id: LogicalId, content_block_ids: Vec<LogicalId>) -> Self {
        Self {
            master_cell_id,
            content_block_ids,
        }
    }

    #[must_use]
    pub const fn master_cell_id(&self) -> &LogicalId {
        &self.master_cell_id
    }

    #[must_use]
    pub fn content_block_ids(&self) -> &[LogicalId] {
        &self.content_block_ids
    }
}

impl fmt::Debug for TableCellContent {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableCellContent")
            .field("master_cell_id", &"<redacted>")
            .field("content_block_count", &self.content_block_ids.len())
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableContentState {
    grid_sha256: [u8; 32],
    cells: Vec<TableCellContent>,
    cell_indexes_by_id: Vec<usize>,
}

impl TableContentState {
    /// Binds one exact content entry to every master cell in the supplied grid.
    ///
    /// Content block identifiers are ownership identifiers and therefore must be unique across the
    /// whole table. Entries are canonicalized to master-cell coordinate order.
    ///
    /// # Errors
    ///
    /// Rejects an inexact master set, duplicate content ownership, identifier/count limits,
    /// allocation failure, or an invalid grid digest.
    pub fn new(
        grid: &TableGrid,
        mut cells: Vec<TableCellContent>,
        limits: TableGridLimits,
    ) -> Result<Self, TableMergeSplitError> {
        if cells.len() != grid.master_cell_count() {
            return Err(TableMergeSplitError::ContentMasterSetMismatch);
        }

        let config = limits.config();
        let mut block_count = 0usize;
        let mut content_identifiers = fallible_vec(0)?;
        for cell in &cells {
            validate_identifier(&cell.master_cell_id, config.identifier_bytes)?;
            block_count = block_count
                .checked_add(cell.content_block_ids.len())
                .ok_or(TableMergeSplitError::ContentBlockLimitExceeded)?;
            if block_count > config.slots {
                return Err(TableMergeSplitError::ContentBlockLimitExceeded);
            }
            content_identifiers
                .try_reserve(cell.content_block_ids.len())
                .map_err(|_| TableMergeSplitError::AllocationFailed)?;
            for identifier in &cell.content_block_ids {
                validate_identifier(identifier, config.identifier_bytes)?;
                content_identifiers.push(identifier);
            }
        }
        content_identifiers.sort_unstable();
        if content_identifiers
            .windows(2)
            .any(|pair| pair[0] == pair[1])
        {
            return Err(TableMergeSplitError::DuplicateContentBlock);
        }

        cells.sort_by(|left, right| left.master_cell_id.cmp(&right.master_cell_id));
        if cells
            .windows(2)
            .any(|pair| pair[0].master_cell_id == pair[1].master_cell_id)
        {
            return Err(TableMergeSplitError::DuplicateContentMaster);
        }

        let mut canonical = fallible_vec(cells.len())?;
        for master_cell in grid.master_cells() {
            let position = cells
                .binary_search_by(|entry| entry.master_cell_id.cmp(&master_cell.master_cell_id))
                .map_err(|_| TableMergeSplitError::ContentMasterSetMismatch)?;
            canonical.push(
                cells
                    .get(position)
                    .ok_or(TableMergeSplitError::ContentMasterSetMismatch)?
                    .clone(),
            );
        }
        let mut cell_indexes_by_id = fallible_vec(canonical.len())?;
        cell_indexes_by_id.extend(0..canonical.len());
        cell_indexes_by_id.sort_unstable_by(|left, right| {
            canonical[*left]
                .master_cell_id
                .cmp(&canonical[*right].master_cell_id)
        });
        Ok(Self {
            grid_sha256: grid.canonical_sha256()?,
            cells: canonical,
            cell_indexes_by_id,
        })
    }

    #[must_use]
    pub const fn grid_sha256(&self) -> &[u8; 32] {
        &self.grid_sha256
    }

    #[must_use]
    pub fn cells(&self) -> &[TableCellContent] {
        &self.cells
    }

    #[must_use]
    pub fn cell(&self, master_cell_id: &LogicalId) -> Option<&TableCellContent> {
        let position = self
            .cell_indexes_by_id
            .binary_search_by(|index| self.cells[*index].master_cell_id.cmp(master_cell_id))
            .ok()?;
        self.cell_indexes_by_id
            .get(position)
            .and_then(|index| self.cells.get(*index))
    }

    fn ensure_grid(&self, grid: &TableGrid) -> Result<(), TableMergeSplitError> {
        if self.grid_sha256 != grid.canonical_sha256()? {
            return Err(TableMergeSplitError::ContentGridMismatch);
        }
        Ok(())
    }
}

impl fmt::Debug for TableContentState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableContentState")
            .field("master_cell_count", &self.cells.len())
            .field(
                "content_block_count",
                &self
                    .cells
                    .iter()
                    .map(|cell| cell.content_block_ids.len())
                    .sum::<usize>(),
            )
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
pub struct TableRegion {
    row: u32,
    column: u32,
    row_span: u32,
    column_span: u32,
}

impl TableRegion {
    #[must_use]
    pub const fn row(self) -> u32 {
        self.row
    }

    #[must_use]
    pub const fn column(self) -> u32 {
        self.column
    }

    #[must_use]
    pub const fn row_span(self) -> u32 {
        self.row_span
    }

    #[must_use]
    pub const fn column_span(self) -> u32 {
        self.column_span
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableMergeSplitKind {
    Merge,
    Split,
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableSplitRequest {
    master_cell_id: LogicalId,
    rows: u32,
    columns: u32,
    new_master_cell_ids: Vec<LogicalId>,
    content_policy: ContentPreservationPolicy,
}

impl TableSplitRequest {
    #[must_use]
    pub fn new(
        master_cell_id: LogicalId,
        rows: u32,
        columns: u32,
        new_master_cell_ids: Vec<LogicalId>,
        content_policy: ContentPreservationPolicy,
    ) -> Self {
        Self {
            master_cell_id,
            rows,
            columns,
            new_master_cell_ids,
            content_policy,
        }
    }

    #[must_use]
    pub const fn master_cell_id(&self) -> &LogicalId {
        &self.master_cell_id
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
    pub fn new_master_cell_ids(&self) -> &[LogicalId] {
        &self.new_master_cell_ids
    }

    #[must_use]
    pub const fn content_policy(&self) -> ContentPreservationPolicy {
        self.content_policy
    }
}

impl fmt::Debug for TableSplitRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableSplitRequest")
            .field("master_cell_id", &"<redacted>")
            .field("rows", &self.rows)
            .field("columns", &self.columns)
            .field("new_master_cell_count", &self.new_master_cell_ids.len())
            .field("content_policy", &self.content_policy)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableContentTransfer {
    from_master_cell_id: LogicalId,
    to_master_cell_id: LogicalId,
    content_block_ids: Vec<LogicalId>,
}

impl TableContentTransfer {
    #[must_use]
    pub const fn from_master_cell_id(&self) -> &LogicalId {
        &self.from_master_cell_id
    }

    #[must_use]
    pub const fn to_master_cell_id(&self) -> &LogicalId {
        &self.to_master_cell_id
    }

    #[must_use]
    pub fn content_block_ids(&self) -> &[LogicalId] {
        &self.content_block_ids
    }
}

impl fmt::Debug for TableContentTransfer {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableContentTransfer")
            .field("from_master_cell_id", &"<redacted>")
            .field("to_master_cell_id", &"<redacted>")
            .field("content_block_count", &self.content_block_ids.len())
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableMergeSplitReceipt {
    schema_version: &'static str,
    operation: TableMergeSplitKind,
    content_policy: ContentPreservationPolicy,
    region: TableRegion,
    before_grid_sha256: [u8; 32],
    after_grid_sha256: [u8; 32],
    preserved_master_cell_id: LogicalId,
    retired_master_cell_ids: Vec<LogicalId>,
    created_master_cell_ids: Vec<LogicalId>,
    content_transfers: Vec<TableContentTransfer>,
    discarded_content_block_ids: Vec<LogicalId>,
}

impl TableMergeSplitReceipt {
    #[must_use]
    pub const fn schema_version(&self) -> &'static str {
        self.schema_version
    }

    #[must_use]
    pub const fn operation(&self) -> TableMergeSplitKind {
        self.operation
    }

    #[must_use]
    pub const fn content_policy(&self) -> ContentPreservationPolicy {
        self.content_policy
    }

    #[must_use]
    pub const fn region(&self) -> TableRegion {
        self.region
    }

    #[must_use]
    pub const fn before_grid_sha256(&self) -> &[u8; 32] {
        &self.before_grid_sha256
    }

    #[must_use]
    pub const fn after_grid_sha256(&self) -> &[u8; 32] {
        &self.after_grid_sha256
    }

    #[must_use]
    pub const fn preserved_master_cell_id(&self) -> &LogicalId {
        &self.preserved_master_cell_id
    }

    #[must_use]
    pub fn retired_master_cell_ids(&self) -> &[LogicalId] {
        &self.retired_master_cell_ids
    }

    #[must_use]
    pub fn created_master_cell_ids(&self) -> &[LogicalId] {
        &self.created_master_cell_ids
    }

    #[must_use]
    pub fn content_transfers(&self) -> &[TableContentTransfer] {
        &self.content_transfers
    }

    #[must_use]
    pub fn discarded_content_block_ids(&self) -> &[LogicalId] {
        &self.discarded_content_block_ids
    }

    /// Emits deterministic compact JSON under the hard receipt ceiling.
    ///
    /// # Errors
    ///
    /// Returns a stable limit, allocation, or serialization error.
    pub fn canonical_json(&self) -> Result<Vec<u8>, TableMergeSplitError> {
        self.canonical_json_with_max_bytes(HARD_MAX_RECEIPT_BYTES)
    }

    /// Emits deterministic compact JSON under a caller-provided finite bound.
    ///
    /// # Errors
    ///
    /// Rejects zero/over-ceiling limits and fails closed if serialization exceeds the bound.
    pub fn canonical_json_with_max_bytes(
        &self,
        max_bytes: usize,
    ) -> Result<Vec<u8>, TableMergeSplitError> {
        if max_bytes == 0 || max_bytes > HARD_MAX_RECEIPT_BYTES {
            return Err(TableMergeSplitError::InvalidReceiptLimit);
        }
        let mut writer = BoundedWriter::new(max_bytes);
        if serde_json::to_writer(&mut writer, self).is_err() {
            return Err(match writer.failure {
                WriterFailure::Limit => TableMergeSplitError::ReceiptOutputLimitExceeded,
                WriterFailure::Allocation => TableMergeSplitError::AllocationFailed,
                WriterFailure::None => TableMergeSplitError::ReceiptSerializationFailed,
            });
        }
        Ok(writer.bytes)
    }
}

impl fmt::Debug for TableMergeSplitReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableMergeSplitReceipt")
            .field("schema_version", &self.schema_version)
            .field("operation", &self.operation)
            .field("content_policy", &self.content_policy)
            .field("region", &self.region)
            .field("preserved_master_cell_id", &"<redacted>")
            .field(
                "retired_master_cell_count",
                &self.retired_master_cell_ids.len(),
            )
            .field(
                "created_master_cell_count",
                &self.created_master_cell_ids.len(),
            )
            .field("content_transfer_count", &self.content_transfers.len())
            .field(
                "discarded_content_block_count",
                &self.discarded_content_block_ids.len(),
            )
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableMergeSplitResult {
    grid: TableGrid,
    content: TableContentState,
    receipt: TableMergeSplitReceipt,
}

impl TableMergeSplitResult {
    #[must_use]
    pub const fn grid(&self) -> &TableGrid {
        &self.grid
    }

    #[must_use]
    pub const fn content(&self) -> &TableContentState {
        &self.content
    }

    #[must_use]
    pub const fn receipt(&self) -> &TableMergeSplitReceipt {
        &self.receipt
    }

    #[must_use]
    pub fn into_parts(self) -> (TableGrid, TableContentState, TableMergeSplitReceipt) {
        (self.grid, self.content, self.receipt)
    }
}

impl fmt::Debug for TableMergeSplitResult {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableMergeSplitResult")
            .field("grid", &self.grid)
            .field("content", &self.content)
            .field("receipt", &self.receipt)
            .finish()
    }
}

impl TableGrid {
    /// Merges an explicit rectangular slot set and preserves the top-left master identity.
    ///
    /// # Errors
    ///
    /// Rejects empty, duplicate, nonrectangular, out-of-bounds or partially intersecting requests,
    /// no-op selections, mismatched content state, policy conflicts, limits and allocation failures.
    pub fn merge_cells(
        &self,
        selected_slots: Vec<CellCoordinate>,
        content: &TableContentState,
        content_policy: ContentPreservationPolicy,
        limits: TableGridLimits,
    ) -> Result<TableMergeSplitResult, TableMergeSplitError> {
        content.ensure_grid(self)?;
        let region = validate_region(selected_slots, self, limits)?;

        let mut selected = fallible_vec(self.master_cell_count())?;
        for master_cell in self.master_cells() {
            if span_intersects(master_cell, region)? {
                if !span_contained(master_cell, region)? {
                    return Err(TableMergeSplitError::PartialMasterSelection);
                }
                selected.push(master_cell);
            }
        }
        if selected.len() < 2 {
            return Err(TableMergeSplitError::NoStructuralChange);
        }

        let survivor = self.master_cell_at(CellCoordinate {
            row: region.row,
            column: region.column,
        })?;
        let mut selected_ids = fallible_vec(selected.len())?;
        for master_cell in &selected {
            selected_ids.push(master_cell.master_cell_id.clone());
        }
        selected_ids.sort_unstable();

        let content_plan =
            plan_merge_content(&selected, &survivor.master_cell_id, content, content_policy)?;
        let expected_masters = self
            .master_cell_count()
            .checked_sub(selected.len())
            .and_then(|value| value.checked_add(1))
            .ok_or(TableMergeSplitError::DimensionOverflow)?;
        let grid = build_merged_grid(
            self,
            region,
            &survivor.master_cell_id,
            &selected_ids,
            expected_masters,
            limits,
        )?;
        let output_content = build_merged_content(
            content,
            &survivor.master_cell_id,
            &selected_ids,
            &content_plan.merged_content,
            expected_masters,
        )?;
        let content = TableContentState::new(&grid, output_content, limits)?;

        let mut retired = fallible_vec(selected.len().saturating_sub(1))?;
        for master_cell in selected {
            if master_cell.master_cell_id != survivor.master_cell_id {
                retired.push(master_cell.master_cell_id.clone());
            }
        }
        let receipt = TableMergeSplitReceipt {
            schema_version: TABLE_MERGE_SPLIT_SCHEMA_VERSION,
            operation: TableMergeSplitKind::Merge,
            content_policy,
            region,
            before_grid_sha256: self.canonical_sha256()?,
            after_grid_sha256: grid.canonical_sha256()?,
            preserved_master_cell_id: survivor.master_cell_id.clone(),
            retired_master_cell_ids: retired,
            created_master_cell_ids: Vec::new(),
            content_transfers: content_plan.transfers,
            discarded_content_block_ids: content_plan.discarded,
        };
        let _ = receipt.canonical_json_with_max_bytes(limits.config().serialized_bytes)?;
        Ok(TableMergeSplitResult {
            grid,
            content,
            receipt,
        })
    }

    /// Splits one master span into an evenly divisible row-major rectangle.
    ///
    /// The top-left result retains the source master identity. Every other result identity is
    /// caller-supplied. `Distribute` assigns stable contiguous, balanced content chunks; the other
    /// explicit policies keep all source content in the preserved top-left result.
    ///
    /// # Errors
    ///
    /// Rejects a missing target, zero/non-divisible/no-op subdivision, inexact or colliding new
    /// identifiers, mismatched content state, limits and allocation failures.
    pub fn split_cell(
        &self,
        request: TableSplitRequest,
        content: &TableContentState,
        limits: TableGridLimits,
    ) -> Result<TableMergeSplitResult, TableMergeSplitError> {
        content.ensure_grid(self)?;
        if request.rows == 0 || request.columns == 0 {
            return Err(TableMergeSplitError::InvalidSplitDimensions);
        }
        let part_count = checked_product(request.rows, request.columns)?;
        if part_count < 2 {
            return Err(TableMergeSplitError::NoStructuralChange);
        }
        let source = self
            .master_cells()
            .iter()
            .find(|cell| cell.master_cell_id == request.master_cell_id)
            .ok_or(TableMergeSplitError::MasterCellNotFound)?;
        if source.row_span % request.rows != 0 || source.column_span % request.columns != 0 {
            return Err(TableMergeSplitError::SplitNotDivisible);
        }
        let expected_new = part_count
            .checked_sub(1)
            .ok_or(TableMergeSplitError::DimensionOverflow)?;
        if request.new_master_cell_ids.len() != expected_new {
            return Err(TableMergeSplitError::NewMasterCellCountMismatch);
        }

        let mut result_ids = fallible_vec(part_count)?;
        result_ids.push(source.master_cell_id.clone());
        result_ids.extend(request.new_master_cell_ids);

        let expected_masters = self
            .master_cell_count()
            .checked_sub(1)
            .and_then(|value| value.checked_add(part_count))
            .ok_or(TableMergeSplitError::DimensionOverflow)?;
        if expected_masters > limits.config().master_cells {
            return Err(TableGridError::MasterCellLimitExceeded.into());
        }
        let grid = build_split_grid(
            self,
            source,
            request.rows,
            request.columns,
            &result_ids,
            expected_masters,
            limits,
        )?;
        let content_plan = build_split_content(
            &grid,
            content,
            source,
            &result_ids,
            request.content_policy,
            limits,
        )?;
        let created_master_cell_ids = clone_ids(
            result_ids
                .get(1..)
                .ok_or(TableMergeSplitError::DimensionOverflow)?,
        )?;
        let region = TableRegion {
            row: source.row,
            column: source.column,
            row_span: source.row_span,
            column_span: source.column_span,
        };
        let receipt = TableMergeSplitReceipt {
            schema_version: TABLE_MERGE_SPLIT_SCHEMA_VERSION,
            operation: TableMergeSplitKind::Split,
            content_policy: request.content_policy,
            region,
            before_grid_sha256: self.canonical_sha256()?,
            after_grid_sha256: grid.canonical_sha256()?,
            preserved_master_cell_id: source.master_cell_id.clone(),
            retired_master_cell_ids: Vec::new(),
            created_master_cell_ids,
            content_transfers: content_plan.transfers,
            discarded_content_block_ids: Vec::new(),
        };
        let _ = receipt.canonical_json_with_max_bytes(limits.config().serialized_bytes)?;
        Ok(TableMergeSplitResult {
            grid,
            content: content_plan.content,
            receipt,
        })
    }
}

struct MergeContentPlan {
    merged_content: Vec<LogicalId>,
    transfers: Vec<TableContentTransfer>,
    discarded: Vec<LogicalId>,
}

fn plan_merge_content(
    selected: &[&TableCellSpan],
    survivor_id: &LogicalId,
    content: &TableContentState,
    policy: ContentPreservationPolicy,
) -> Result<MergeContentPlan, TableMergeSplitError> {
    let nonempty_count = selected
        .iter()
        .filter(|master_cell| {
            content
                .cell(&master_cell.master_cell_id)
                .is_some_and(|entry| !entry.content_block_ids.is_empty())
        })
        .count();
    if policy == ContentPreservationPolicy::RejectIfMultiple && nonempty_count > 1 {
        return Err(TableMergeSplitError::MultipleNonemptyCells);
    }

    let mut merged_content = fallible_vec(0)?;
    let mut transfers = fallible_vec(selected.len())?;
    let mut discarded = fallible_vec(0)?;
    for (index, master_cell) in selected.iter().enumerate() {
        let entry = content
            .cell(&master_cell.master_cell_id)
            .ok_or(TableMergeSplitError::ContentMasterSetMismatch)?;
        let keep = match policy {
            ContentPreservationPolicy::First => index == 0,
            ContentPreservationPolicy::RejectIfMultiple => {
                nonempty_count == 0 || !entry.content_block_ids.is_empty()
            }
            ContentPreservationPolicy::Concatenate | ContentPreservationPolicy::Distribute => true,
        };
        if keep {
            append_ids(&mut merged_content, &entry.content_block_ids)?;
            if !entry.content_block_ids.is_empty() {
                transfers.push(TableContentTransfer {
                    from_master_cell_id: entry.master_cell_id.clone(),
                    to_master_cell_id: survivor_id.clone(),
                    content_block_ids: clone_ids(&entry.content_block_ids)?,
                });
            }
        } else {
            append_ids(&mut discarded, &entry.content_block_ids)?;
        }
    }
    Ok(MergeContentPlan {
        merged_content,
        transfers,
        discarded,
    })
}

fn build_merged_grid(
    source: &TableGrid,
    region: TableRegion,
    survivor_id: &LogicalId,
    selected_ids: &[LogicalId],
    expected_masters: usize,
    limits: TableGridLimits,
) -> Result<TableGrid, TableMergeSplitError> {
    let mut master_cells = fallible_vec(expected_masters)?;
    for master_cell in source.master_cells() {
        if master_cell.master_cell_id == *survivor_id {
            master_cells.push(TableCellSpan {
                master_cell_id: survivor_id.clone(),
                row: region.row,
                column: region.column,
                row_span: region.row_span,
                column_span: region.column_span,
            });
        } else if selected_ids
            .binary_search(&master_cell.master_cell_id)
            .is_err()
        {
            master_cells.push(master_cell.clone());
        }
    }
    Ok(TableGrid::new(
        source.rows(),
        source.columns(),
        master_cells,
        limits,
    )?)
}

fn build_merged_content(
    source: &TableContentState,
    survivor_id: &LogicalId,
    selected_ids: &[LogicalId],
    merged_content: &[LogicalId],
    expected_masters: usize,
) -> Result<Vec<TableCellContent>, TableMergeSplitError> {
    let mut output = fallible_vec(expected_masters)?;
    for entry in source.cells() {
        if entry.master_cell_id == *survivor_id {
            output.push(TableCellContent::new(
                survivor_id.clone(),
                clone_ids(merged_content)?,
            ));
        } else if selected_ids.binary_search(&entry.master_cell_id).is_err() {
            output.push(entry.clone());
        }
    }
    Ok(output)
}

fn build_split_grid(
    grid: &TableGrid,
    source: &TableCellSpan,
    split_rows: u32,
    split_columns: u32,
    result_ids: &[LogicalId],
    expected_masters: usize,
    limits: TableGridLimits,
) -> Result<TableGrid, TableMergeSplitError> {
    let mut master_cells = fallible_vec(expected_masters)?;
    for master_cell in grid.master_cells() {
        if master_cell.master_cell_id != source.master_cell_id {
            master_cells.push(master_cell.clone());
            continue;
        }
        append_split_cells(
            &mut master_cells,
            source,
            split_rows,
            split_columns,
            result_ids,
        )?;
    }
    Ok(TableGrid::new(
        grid.rows(),
        grid.columns(),
        master_cells,
        limits,
    )?)
}

fn append_split_cells(
    master_cells: &mut Vec<TableCellSpan>,
    source: &TableCellSpan,
    split_rows: u32,
    split_columns: u32,
    result_ids: &[LogicalId],
) -> Result<(), TableMergeSplitError> {
    let row_span = source.row_span / split_rows;
    let column_span = source.column_span / split_columns;
    for row_index in 0..split_rows {
        for column_index in 0..split_columns {
            let part_index = checked_row_major(row_index, column_index, split_columns)?;
            let row_offset = row_index
                .checked_mul(row_span)
                .ok_or(TableMergeSplitError::DimensionOverflow)?;
            let column_offset = column_index
                .checked_mul(column_span)
                .ok_or(TableMergeSplitError::DimensionOverflow)?;
            let result_id = result_ids
                .get(part_index)
                .ok_or(TableMergeSplitError::DimensionOverflow)?;
            master_cells.push(TableCellSpan {
                master_cell_id: result_id.clone(),
                row: source
                    .row
                    .checked_add(row_offset)
                    .ok_or(TableMergeSplitError::DimensionOverflow)?,
                column: source
                    .column
                    .checked_add(column_offset)
                    .ok_or(TableMergeSplitError::DimensionOverflow)?,
                row_span,
                column_span,
            });
        }
    }
    Ok(())
}

struct SplitContentPlan {
    content: TableContentState,
    transfers: Vec<TableContentTransfer>,
}

fn build_split_content(
    grid: &TableGrid,
    source_content: &TableContentState,
    source: &TableCellSpan,
    result_ids: &[LogicalId],
    policy: ContentPreservationPolicy,
    limits: TableGridLimits,
) -> Result<SplitContentPlan, TableMergeSplitError> {
    let source_entry = source_content
        .cell(&source.master_cell_id)
        .ok_or(TableMergeSplitError::ContentMasterSetMismatch)?;
    let part_count = result_ids.len();
    let distributed = distribute_content(
        &source_entry.content_block_ids,
        part_count,
        policy == ContentPreservationPolicy::Distribute,
    )?;
    let mut replacement = fallible_vec(part_count)?;
    let mut transfers = fallible_vec(part_count)?;
    for (part_index, identifiers) in distributed.into_iter().enumerate() {
        let result_id = result_ids
            .get(part_index)
            .ok_or(TableMergeSplitError::DimensionOverflow)?;
        if !identifiers.is_empty() {
            transfers.push(TableContentTransfer {
                from_master_cell_id: source.master_cell_id.clone(),
                to_master_cell_id: result_id.clone(),
                content_block_ids: clone_ids(&identifiers)?,
            });
        }
        replacement.push(TableCellContent::new(result_id.clone(), identifiers));
    }

    let mut output = fallible_vec(grid.master_cell_count())?;
    for entry in source_content.cells() {
        if entry.master_cell_id == source.master_cell_id {
            output.extend(replacement.iter().cloned());
        } else {
            output.push(entry.clone());
        }
    }
    Ok(SplitContentPlan {
        content: TableContentState::new(grid, output, limits)?,
        transfers,
    })
}

fn validate_region(
    mut selected_slots: Vec<CellCoordinate>,
    grid: &TableGrid,
    limits: TableGridLimits,
) -> Result<TableRegion, TableMergeSplitError> {
    if selected_slots.is_empty() {
        return Err(TableMergeSplitError::EmptySelection);
    }
    if selected_slots.len() > limits.config().slots {
        return Err(TableMergeSplitError::SelectionLimitExceeded);
    }
    selected_slots.sort_unstable();
    if selected_slots.windows(2).any(|pair| pair[0] == pair[1]) {
        return Err(TableMergeSplitError::DuplicateSelectedSlot);
    }
    let first = *selected_slots
        .first()
        .ok_or(TableMergeSplitError::EmptySelection)?;
    let mut first_row = first.row;
    let mut first_column = first.column;
    let mut last_row = first.row;
    let mut last_column = first.column;
    for coordinate in &selected_slots {
        if coordinate.row >= grid.rows() || coordinate.column >= grid.columns() {
            return Err(TableMergeSplitError::SelectionOutOfBounds);
        }
        first_row = first_row.min(coordinate.row);
        first_column = first_column.min(coordinate.column);
        last_row = last_row.max(coordinate.row);
        last_column = last_column.max(coordinate.column);
    }
    let row_span = last_row
        .checked_sub(first_row)
        .and_then(|value| value.checked_add(1))
        .ok_or(TableMergeSplitError::DimensionOverflow)?;
    let column_span = last_column
        .checked_sub(first_column)
        .and_then(|value| value.checked_add(1))
        .ok_or(TableMergeSplitError::DimensionOverflow)?;
    if checked_product(row_span, column_span)? != selected_slots.len() {
        return Err(TableMergeSplitError::NonRectangularSelection);
    }
    Ok(TableRegion {
        row: first_row,
        column: first_column,
        row_span,
        column_span,
    })
}

fn span_intersects(
    master_cell: &TableCellSpan,
    region: TableRegion,
) -> Result<bool, TableMergeSplitError> {
    let master_row_end = master_cell
        .row
        .checked_add(master_cell.row_span)
        .ok_or(TableMergeSplitError::DimensionOverflow)?;
    let master_column_end = master_cell
        .column
        .checked_add(master_cell.column_span)
        .ok_or(TableMergeSplitError::DimensionOverflow)?;
    let region_row_end = region
        .row
        .checked_add(region.row_span)
        .ok_or(TableMergeSplitError::DimensionOverflow)?;
    let region_column_end = region
        .column
        .checked_add(region.column_span)
        .ok_or(TableMergeSplitError::DimensionOverflow)?;
    Ok(master_cell.row < region_row_end
        && master_row_end > region.row
        && master_cell.column < region_column_end
        && master_column_end > region.column)
}

fn span_contained(
    master_cell: &TableCellSpan,
    region: TableRegion,
) -> Result<bool, TableMergeSplitError> {
    let master_row_end = master_cell
        .row
        .checked_add(master_cell.row_span)
        .ok_or(TableMergeSplitError::DimensionOverflow)?;
    let master_column_end = master_cell
        .column
        .checked_add(master_cell.column_span)
        .ok_or(TableMergeSplitError::DimensionOverflow)?;
    let region_row_end = region
        .row
        .checked_add(region.row_span)
        .ok_or(TableMergeSplitError::DimensionOverflow)?;
    let region_column_end = region
        .column
        .checked_add(region.column_span)
        .ok_or(TableMergeSplitError::DimensionOverflow)?;
    Ok(master_cell.row >= region.row
        && master_row_end <= region_row_end
        && master_cell.column >= region.column
        && master_column_end <= region_column_end)
}

fn distribute_content(
    source: &[LogicalId],
    part_count: usize,
    distribute: bool,
) -> Result<Vec<Vec<LogicalId>>, TableMergeSplitError> {
    let mut result = fallible_vec(part_count)?;
    if !distribute {
        result.push(clone_ids(source)?);
        for _ in 1..part_count {
            result.push(Vec::new());
        }
        return Ok(result);
    }

    let base = source.len() / part_count;
    let remainder = source.len() % part_count;
    let mut offset = 0usize;
    for index in 0..part_count {
        let count = base + usize::from(index < remainder);
        let end = offset
            .checked_add(count)
            .ok_or(TableMergeSplitError::DimensionOverflow)?;
        result.push(clone_ids(&source[offset..end])?);
        offset = end;
    }
    Ok(result)
}

fn validate_identifier(
    identifier: &LogicalId,
    max_bytes: usize,
) -> Result<(), TableMergeSplitError> {
    if identifier.as_str().len() > max_bytes {
        return Err(TableMergeSplitError::IdentifierLimitExceeded);
    }
    Ok(())
}

fn checked_product(left: u32, right: u32) -> Result<usize, TableMergeSplitError> {
    let left = usize::try_from(left).map_err(|_| TableMergeSplitError::DimensionOverflow)?;
    let right = usize::try_from(right).map_err(|_| TableMergeSplitError::DimensionOverflow)?;
    left.checked_mul(right)
        .ok_or(TableMergeSplitError::DimensionOverflow)
}

fn checked_row_major(row: u32, column: u32, columns: u32) -> Result<usize, TableMergeSplitError> {
    let row = usize::try_from(row).map_err(|_| TableMergeSplitError::DimensionOverflow)?;
    let column = usize::try_from(column).map_err(|_| TableMergeSplitError::DimensionOverflow)?;
    let columns = usize::try_from(columns).map_err(|_| TableMergeSplitError::DimensionOverflow)?;
    row.checked_mul(columns)
        .and_then(|offset| offset.checked_add(column))
        .ok_or(TableMergeSplitError::DimensionOverflow)
}

fn fallible_vec<T>(capacity: usize) -> Result<Vec<T>, TableMergeSplitError> {
    let mut values = Vec::new();
    values
        .try_reserve_exact(capacity)
        .map_err(|_| TableMergeSplitError::AllocationFailed)?;
    Ok(values)
}

fn clone_ids(values: &[LogicalId]) -> Result<Vec<LogicalId>, TableMergeSplitError> {
    let mut cloned = fallible_vec(values.len())?;
    cloned.extend(values.iter().cloned());
    Ok(cloned)
}

fn append_ids(
    destination: &mut Vec<LogicalId>,
    source: &[LogicalId],
) -> Result<(), TableMergeSplitError> {
    destination
        .try_reserve(source.len())
        .map_err(|_| TableMergeSplitError::AllocationFailed)?;
    destination.extend(source.iter().cloned());
    Ok(())
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
            return Err(io::Error::other("table merge/split receipt output limit"));
        };
        if next_length > self.max_bytes {
            self.failure = WriterFailure::Limit;
            return Err(io::Error::other("table merge/split receipt output limit"));
        }
        if self.bytes.try_reserve(buffer.len()).is_err() {
            self.failure = WriterFailure::Allocation;
            return Err(io::Error::other("table merge/split receipt allocation"));
        }
        self.bytes.extend_from_slice(buffer);
        Ok(buffer.len())
    }

    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum TableMergeSplitError {
    #[error("table content master set does not exactly match the grid")]
    ContentMasterSetMismatch,
    #[error("table content contains a duplicate master-cell entry")]
    DuplicateContentMaster,
    #[error("table content block identity is owned by more than one position")]
    DuplicateContentBlock,
    #[error("table content block count exceeds the configured limit")]
    ContentBlockLimitExceeded,
    #[error("table content identifier exceeds the configured limit")]
    IdentifierLimitExceeded,
    #[error("table content state is bound to a different grid")]
    ContentGridMismatch,
    #[error("table merge selection must be nonempty")]
    EmptySelection,
    #[error("table merge selection exceeds the configured slot limit")]
    SelectionLimitExceeded,
    #[error("table merge selection contains a duplicate slot")]
    DuplicateSelectedSlot,
    #[error("table merge selection is outside the grid")]
    SelectionOutOfBounds,
    #[error("table merge selection is not one complete rectangle")]
    NonRectangularSelection,
    #[error("table merge selection partially intersects a master-cell span")]
    PartialMasterSelection,
    #[error("table merge/split request makes no structural change")]
    NoStructuralChange,
    #[error("table merge rejected multiple nonempty source cells")]
    MultipleNonemptyCells,
    #[error("table split dimensions must be nonzero")]
    InvalidSplitDimensions,
    #[error("table split target master cell was not found")]
    MasterCellNotFound,
    #[error("table split dimensions do not evenly divide the source span")]
    SplitNotDivisible,
    #[error("table split new master-cell identifier count is inexact")]
    NewMasterCellCountMismatch,
    #[error("table merge/split dimension arithmetic overflowed")]
    DimensionOverflow,
    #[error("table merge/split receipt limit is invalid")]
    InvalidReceiptLimit,
    #[error("table merge/split receipt exceeds its output limit")]
    ReceiptOutputLimitExceeded,
    #[error("table merge/split receipt serialization failed")]
    ReceiptSerializationFailed,
    #[error("table merge/split allocation failed")]
    AllocationFailed,
    #[error(transparent)]
    Grid(#[from] TableGridError),
}

impl TableMergeSplitError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::ContentMasterSetMismatch => "table_merge_split_content_master_set_mismatch",
            Self::DuplicateContentMaster => "table_merge_split_duplicate_content_master",
            Self::DuplicateContentBlock => "table_merge_split_duplicate_content_block",
            Self::ContentBlockLimitExceeded => "table_merge_split_content_block_limit_exceeded",
            Self::IdentifierLimitExceeded => "table_merge_split_identifier_limit_exceeded",
            Self::ContentGridMismatch => "table_merge_split_content_grid_mismatch",
            Self::EmptySelection => "table_merge_split_empty_selection",
            Self::SelectionLimitExceeded => "table_merge_split_selection_limit_exceeded",
            Self::DuplicateSelectedSlot => "table_merge_split_duplicate_selected_slot",
            Self::SelectionOutOfBounds => "table_merge_split_selection_out_of_bounds",
            Self::NonRectangularSelection => "table_merge_split_non_rectangular_selection",
            Self::PartialMasterSelection => "table_merge_split_partial_master_selection",
            Self::NoStructuralChange => "table_merge_split_no_structural_change",
            Self::MultipleNonemptyCells => "table_merge_split_multiple_nonempty_cells",
            Self::InvalidSplitDimensions => "table_merge_split_invalid_split_dimensions",
            Self::MasterCellNotFound => "table_merge_split_master_cell_not_found",
            Self::SplitNotDivisible => "table_merge_split_not_divisible",
            Self::NewMasterCellCountMismatch => "table_merge_split_new_master_cell_count_mismatch",
            Self::DimensionOverflow => "table_merge_split_dimension_overflow",
            Self::InvalidReceiptLimit => "table_merge_split_invalid_receipt_limit",
            Self::ReceiptOutputLimitExceeded => "table_merge_split_receipt_output_limit_exceeded",
            Self::ReceiptSerializationFailed => "table_merge_split_receipt_serialization_failed",
            Self::AllocationFailed => "table_merge_split_allocation_failed",
            Self::Grid(error) => error.code(),
        }
    }
}
