use std::fmt;
use std::io;

use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{LengthMicrometers, TableGrid, TableGridError};

pub const TABLE_PAGINATION_SCHEMA_VERSION: &str = "hwpx-agent.table-pagination/v1";
pub const TABLE_PAGINATION_OBSERVATION_SCHEMA_VERSION: &str =
    "hwpx-agent.table-pagination-observation/v1";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TablePaginationLimitConfig {
    pub rows: usize,
    pub pages: usize,
    pub fragments: usize,
    pub dimension_micrometers: u64,
    pub serialized_bytes: usize,
}

impl Default for TablePaginationLimitConfig {
    fn default() -> Self {
        Self {
            rows: 10_000,
            pages: 20_000,
            fragments: 1_000_000,
            dimension_micrometers: 1_000_000_000,
            serialized_bytes: 32 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TablePaginationLimits(TablePaginationLimitConfig);

impl TablePaginationLimits {
    pub const HARD_MAX_ROWS: usize = 10_000;
    pub const HARD_MAX_PAGES: usize = 100_000;
    pub const HARD_MAX_FRAGMENTS: usize = 10_000_000;
    pub const HARD_MAX_DIMENSION_MICROMETERS: u64 = 1_000_000_000;
    pub const HARD_MAX_SERIALIZED_BYTES: usize = 256 * 1024 * 1024;

    /// Creates finite limits for the P06-07 pagination boundary.
    ///
    /// # Errors
    ///
    /// Rejects zero values, values over the hard ceilings, and a fragment limit smaller than the
    /// row limit.
    pub fn new(config: TablePaginationLimitConfig) -> Result<Self, TablePaginationError> {
        if config.rows == 0
            || config.rows > Self::HARD_MAX_ROWS
            || config.pages == 0
            || config.pages > Self::HARD_MAX_PAGES
            || config.fragments < config.rows
            || config.fragments > Self::HARD_MAX_FRAGMENTS
            || config.dimension_micrometers == 0
            || config.dimension_micrometers > Self::HARD_MAX_DIMENSION_MICROMETERS
            || config.serialized_bytes == 0
            || config.serialized_bytes > Self::HARD_MAX_SERIALIZED_BYTES
        {
            return Err(TablePaginationError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> TablePaginationLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TablePageSplitPolicy {
    Allow,
    AvoidRow,
    AvoidTable,
    RequiredKeep,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum RowSplitEligibility {
    Allowed,
    Forbidden,
    NestedTable,
    UnbreakableObject,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CaptionSide {
    Top,
    Bottom,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableCaption {
    pub side: CaptionSide,
    pub block_height: LengthMicrometers,
    pub gap: LengthMicrometers,
    pub keep_with_table: bool,
    pub content_sha256: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TablePaginationRow {
    pub row: u32,
    pub height: LengthMicrometers,
    pub split_eligibility: RowSplitEligibility,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TablePaginationPolicy {
    pub schema_version: String,
    pub page_split: TablePageSplitPolicy,
    pub repeat_header_rows: u32,
    pub rows: Vec<TablePaginationRow>,
    pub caption: Option<TableCaption>,
}

impl TablePaginationPolicy {
    /// Deserializes an untrusted bounded policy document.
    ///
    /// # Errors
    ///
    /// Rejects oversized JSON, duplicate/unknown fields, malformed values, and allocation or
    /// serialization failures. Semantic validation is performed by [`TablePaginationValidator`].
    pub fn from_json(
        bytes: &[u8],
        limits: TablePaginationLimits,
    ) -> Result<Self, TablePaginationError> {
        if bytes.len() > limits.0.serialized_bytes {
            return Err(TablePaginationError::InputLimit);
        }
        serde_json::from_slice(bytes).map_err(|_| TablePaginationError::InvalidJson)
    }

    /// Serializes the policy to bounded canonical JSON.
    ///
    /// # Errors
    ///
    /// Returns a stable serialization or size error.
    pub fn canonical_json(
        &self,
        limits: TablePaginationLimits,
    ) -> Result<Vec<u8>, TablePaginationError> {
        serialize_bounded(self, limits.0.serialized_bytes)
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum TablePageItem {
    RepeatedHeader {
        row: u32,
    },
    RowFragment {
        row: u32,
        fragment_index: u32,
        height: LengthMicrometers,
        begins_row: bool,
        ends_row: bool,
    },
    Caption {
        side: CaptionSide,
    },
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TablePage {
    pub page_index: u32,
    pub items: Vec<TablePageItem>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TablePaginationObservation {
    pub schema_version: String,
    pub anchor_page_index: u32,
    pub first_page_available_height: LengthMicrometers,
    pub continuation_page_height: LengthMicrometers,
    pub pages: Vec<TablePage>,
}

impl TablePaginationObservation {
    /// Deserializes an untrusted bounded renderer observation.
    ///
    /// # Errors
    ///
    /// Rejects oversized JSON, duplicate/unknown fields, malformed values, and allocation or
    /// serialization failures. Semantic validation is performed by [`TablePaginationValidator`].
    pub fn from_json(
        bytes: &[u8],
        limits: TablePaginationLimits,
    ) -> Result<Self, TablePaginationError> {
        if bytes.len() > limits.0.serialized_bytes {
            return Err(TablePaginationError::InputLimit);
        }
        serde_json::from_slice(bytes).map_err(|_| TablePaginationError::InvalidJson)
    }

    /// Serializes the observation to bounded canonical JSON.
    ///
    /// # Errors
    ///
    /// Returns a stable serialization or size error.
    pub fn canonical_json(
        &self,
        limits: TablePaginationLimits,
    ) -> Result<Vec<u8>, TablePaginationError> {
        serialize_bounded(self, limits.0.serialized_bytes)
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TablePaginationReceipt {
    schema_version: &'static str,
    grid_sha256: String,
    policy_sha256: String,
    observation_sha256: String,
    first_page_index: u32,
    last_page_index: u32,
    page_count: usize,
    row_fragment_count: usize,
    split_row_count: usize,
    repeated_header_copy_count: usize,
    caption_page_index: Option<u32>,
}

impl TablePaginationReceipt {
    #[must_use]
    pub const fn schema_version(&self) -> &'static str {
        self.schema_version
    }

    #[must_use]
    pub fn grid_sha256(&self) -> &str {
        &self.grid_sha256
    }

    #[must_use]
    pub fn policy_sha256(&self) -> &str {
        &self.policy_sha256
    }

    #[must_use]
    pub fn observation_sha256(&self) -> &str {
        &self.observation_sha256
    }

    #[must_use]
    pub const fn first_page_index(&self) -> u32 {
        self.first_page_index
    }

    #[must_use]
    pub const fn last_page_index(&self) -> u32 {
        self.last_page_index
    }

    #[must_use]
    pub const fn page_count(&self) -> usize {
        self.page_count
    }

    #[must_use]
    pub const fn row_fragment_count(&self) -> usize {
        self.row_fragment_count
    }

    #[must_use]
    pub const fn split_row_count(&self) -> usize {
        self.split_row_count
    }

    #[must_use]
    pub const fn repeated_header_copy_count(&self) -> usize {
        self.repeated_header_copy_count
    }

    #[must_use]
    pub const fn caption_page_index(&self) -> Option<u32> {
        self.caption_page_index
    }

    /// Serializes the verified receipt to bounded canonical JSON.
    ///
    /// # Errors
    ///
    /// Returns a stable serialization or size error.
    pub fn canonical_json(
        &self,
        limits: TablePaginationLimits,
    ) -> Result<Vec<u8>, TablePaginationError> {
        serialize_bounded(self, limits.0.serialized_bytes)
    }

    /// Hashes the bounded canonical receipt.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failures.
    pub fn canonical_sha256(
        &self,
        limits: TablePaginationLimits,
    ) -> Result<[u8; 32], TablePaginationError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TablePaginationReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TablePaginationReceipt")
            .field("schema_version", &self.schema_version)
            .field("grid_sha256", &self.grid_sha256)
            .field("policy_sha256", &self.policy_sha256)
            .field("observation_sha256", &self.observation_sha256)
            .field("first_page_index", &self.first_page_index)
            .field("last_page_index", &self.last_page_index)
            .field("page_count", &self.page_count)
            .field("row_fragment_count", &self.row_fragment_count)
            .field("split_row_count", &self.split_row_count)
            .field(
                "repeated_header_copy_count",
                &self.repeated_header_copy_count,
            )
            .field("caption_page_index", &self.caption_page_index)
            .finish()
    }
}

#[derive(Debug)]
pub struct TablePaginationValidator;

impl TablePaginationValidator {
    /// Validates an observed page layout against the exact table policy and logical grid.
    ///
    /// The observation must account for every row height exactly, use contiguous page indexes,
    /// repeat only the configured header prefix, and obey row/cell/table keep constraints. This
    /// validator does not infer renderer output and therefore cannot by itself prove a Hancom page
    /// count.
    ///
    /// # Errors
    ///
    /// Fails closed on unsupported schemas, malformed policy, incomplete/duplicate fragments,
    /// capacity overflow, illegal page splits, caption drift, or bounded-resource violations.
    pub fn validate(
        grid: &TableGrid,
        policy: &TablePaginationPolicy,
        observation: &TablePaginationObservation,
        limits: TablePaginationLimits,
    ) -> Result<TablePaginationReceipt, TablePaginationError> {
        validate_policy(grid, policy, limits)?;
        validate_observation_shape(observation, limits)?;

        let mut state = ValidationState::new(policy.rows.len())?;
        for (page_offset, page) in observation.pages.iter().enumerate() {
            validate_page_identity(observation, page, page_offset)?;
            validate_page(policy, observation, page, page_offset, limits, &mut state)?;
        }
        state.finish(grid, policy, observation)?;

        let policy_bytes = serialize_bounded(policy, limits.0.serialized_bytes)?;
        let observation_bytes = serialize_bounded(observation, limits.0.serialized_bytes)?;
        let grid_sha256 = hex_digest(grid.canonical_sha256()?);
        let first_page_index = observation.pages[0].page_index;
        let last_page_index = observation.pages[observation.pages.len() - 1].page_index;
        Ok(TablePaginationReceipt {
            schema_version: TABLE_PAGINATION_SCHEMA_VERSION,
            grid_sha256,
            policy_sha256: hex_digest(Sha256::digest(policy_bytes).into()),
            observation_sha256: hex_digest(Sha256::digest(observation_bytes).into()),
            first_page_index,
            last_page_index,
            page_count: observation.pages.len(),
            row_fragment_count: state.fragment_count,
            split_row_count: state.split_row_count,
            repeated_header_copy_count: state.repeated_header_copy_count,
            caption_page_index: state.caption_page_index,
        })
    }
}

#[derive(Debug)]
struct ValidationState {
    next_row: usize,
    current_row_height: u64,
    current_fragment_index: u32,
    current_fragment_count: usize,
    fragment_count: usize,
    split_row_count: usize,
    repeated_header_copy_count: usize,
    caption_page_index: Option<u32>,
    row_page_indexes: Vec<Option<(u32, u32)>>,
}

#[derive(Clone, Copy, Debug)]
struct ObservedRowFragment {
    page_index: u32,
    row: u32,
    fragment_index: u32,
    height: LengthMicrometers,
    begins_row: bool,
    ends_row: bool,
}

impl ValidationState {
    fn new(rows: usize) -> Result<Self, TablePaginationError> {
        let mut row_page_indexes = Vec::new();
        row_page_indexes
            .try_reserve_exact(rows)
            .map_err(|_| TablePaginationError::AllocationFailed)?;
        row_page_indexes.resize(rows, None);
        Ok(Self {
            next_row: 0,
            current_row_height: 0,
            current_fragment_index: 0,
            current_fragment_count: 0,
            fragment_count: 0,
            split_row_count: 0,
            repeated_header_copy_count: 0,
            caption_page_index: None,
            row_page_indexes,
        })
    }

    fn observe_fragment(
        &mut self,
        policy: &TablePaginationPolicy,
        fragment: ObservedRowFragment,
        limits: TablePaginationLimits,
    ) -> Result<(), TablePaginationError> {
        let row_index =
            usize::try_from(fragment.row).map_err(|_| TablePaginationError::RowOrder)?;
        if row_index != self.next_row {
            return Err(TablePaginationError::RowOrder);
        }
        let expected = policy
            .rows
            .get(row_index)
            .ok_or(TablePaginationError::RowOrder)?;
        if fragment.fragment_index != self.current_fragment_index
            || fragment.begins_row != (fragment.fragment_index == 0)
            || (fragment.fragment_index > 0 && self.current_fragment_count == 0)
        {
            return Err(TablePaginationError::FragmentSequence);
        }
        let raw_height = positive_dimension(fragment.height, limits.0.dimension_micrometers)?;
        self.current_row_height = self
            .current_row_height
            .checked_add(raw_height)
            .ok_or(TablePaginationError::ArithmeticOverflow)?;
        let expected_height = positive_dimension(expected.height, limits.0.dimension_micrometers)?;
        if self.current_row_height > expected_height
            || (fragment.ends_row && self.current_row_height != expected_height)
            || (!fragment.ends_row && self.current_row_height == expected_height)
        {
            return Err(TablePaginationError::RowHeightMismatch);
        }
        if fragment.fragment_index > 0 && !matches!(policy.page_split, TablePageSplitPolicy::Allow)
        {
            return Err(TablePaginationError::RowSplitForbidden);
        }
        if fragment.fragment_index > 0 && fragment.row < policy.repeat_header_rows {
            return Err(TablePaginationError::HeaderRowSplit);
        }
        if fragment.fragment_index > 0 && expected.split_eligibility != RowSplitEligibility::Allowed
        {
            return Err(match expected.split_eligibility {
                RowSplitEligibility::NestedTable => TablePaginationError::NestedTableSplit,
                RowSplitEligibility::UnbreakableObject => {
                    TablePaginationError::UnbreakableObjectSplit
                }
                RowSplitEligibility::Allowed => TablePaginationError::InternalInvariant,
                RowSplitEligibility::Forbidden => TablePaginationError::RowSplitForbidden,
            });
        }

        let pages = self
            .row_page_indexes
            .get_mut(row_index)
            .ok_or(TablePaginationError::InternalInvariant)?;
        match pages {
            None => *pages = Some((fragment.page_index, fragment.page_index)),
            Some((_, last)) => {
                if fragment.page_index
                    != last.checked_add(1).ok_or(TablePaginationError::PageIndex)?
                {
                    return Err(TablePaginationError::FragmentPageOrder);
                }
                *last = fragment.page_index;
            }
        }

        self.fragment_count = self
            .fragment_count
            .checked_add(1)
            .filter(|count| *count <= limits.0.fragments)
            .ok_or(TablePaginationError::FragmentLimit)?;
        self.current_fragment_count = self
            .current_fragment_count
            .checked_add(1)
            .ok_or(TablePaginationError::ArithmeticOverflow)?;
        if fragment.ends_row {
            if self.current_fragment_count > 1 {
                self.split_row_count = self
                    .split_row_count
                    .checked_add(1)
                    .ok_or(TablePaginationError::ArithmeticOverflow)?;
            }
            self.next_row = self
                .next_row
                .checked_add(1)
                .ok_or(TablePaginationError::ArithmeticOverflow)?;
            self.current_row_height = 0;
            self.current_fragment_index = 0;
            self.current_fragment_count = 0;
        } else {
            self.current_fragment_index = self
                .current_fragment_index
                .checked_add(1)
                .ok_or(TablePaginationError::ArithmeticOverflow)?;
        }
        Ok(())
    }

    fn finish(
        &self,
        grid: &TableGrid,
        policy: &TablePaginationPolicy,
        observation: &TablePaginationObservation,
    ) -> Result<(), TablePaginationError> {
        if self.next_row != policy.rows.len()
            || self.current_row_height != 0
            || self.fragment_count < policy.rows.len()
        {
            return Err(TablePaginationError::IncompleteRows);
        }
        if matches!(
            policy.page_split,
            TablePageSplitPolicy::AvoidTable | TablePageSplitPolicy::RequiredKeep
        ) && observation.pages.len() != 1
        {
            return Err(TablePaginationError::TableSplitForbidden);
        }
        if policy.page_split == TablePageSplitPolicy::AvoidRow {
            validate_merged_cell_page_boundaries(grid, &self.row_page_indexes)?;
        }
        if policy.page_split == TablePageSplitPolicy::RequiredKeep
            && policy
                .caption
                .as_ref()
                .is_some_and(|caption| !caption.keep_with_table)
        {
            return Err(TablePaginationError::RequiredKeepMissing);
        }
        if policy.caption.is_some() != self.caption_page_index.is_some() {
            return Err(TablePaginationError::CaptionMissing);
        }
        Ok(())
    }
}

fn validate_policy(
    grid: &TableGrid,
    policy: &TablePaginationPolicy,
    limits: TablePaginationLimits,
) -> Result<(), TablePaginationError> {
    if policy.schema_version != TABLE_PAGINATION_SCHEMA_VERSION {
        return Err(TablePaginationError::UnsupportedVersion);
    }
    let grid_rows = usize::try_from(grid.rows()).map_err(|_| TablePaginationError::RowLimit)?;
    if grid_rows == 0 || grid_rows > limits.0.rows || policy.rows.len() != grid_rows {
        return Err(TablePaginationError::RowCountMismatch);
    }
    for (index, row) in policy.rows.iter().enumerate() {
        if usize::try_from(row.row).map_err(|_| TablePaginationError::RowOrder)? != index {
            return Err(TablePaginationError::RowOrder);
        }
        let _ = positive_dimension(row.height, limits.0.dimension_micrometers)?;
    }
    let repeat = usize::try_from(policy.repeat_header_rows)
        .map_err(|_| TablePaginationError::HeaderRange)?;
    if repeat > grid_rows {
        return Err(TablePaginationError::HeaderRange);
    }
    if repeat > 0 {
        validate_header_prefix(grid, policy.repeat_header_rows)?;
    }
    if let Some(caption) = &policy.caption {
        let _ = positive_dimension(caption.block_height, limits.0.dimension_micrometers)?;
        let _ = nonnegative_dimension(caption.gap, limits.0.dimension_micrometers)?;
        if !is_lower_hex_sha256(&caption.content_sha256) {
            return Err(TablePaginationError::CaptionDigest);
        }
    }
    let _ = serialize_bounded(policy, limits.0.serialized_bytes)?;
    Ok(())
}

fn validate_header_prefix(grid: &TableGrid, header_rows: u32) -> Result<(), TablePaginationError> {
    for cell in grid.master_cells() {
        if cell.row < header_rows {
            let end = cell
                .row
                .checked_add(cell.row_span)
                .ok_or(TablePaginationError::HeaderSpanCrossesBody)?;
            if end > header_rows {
                return Err(TablePaginationError::HeaderSpanCrossesBody);
            }
        }
    }
    Ok(())
}

fn validate_observation_shape(
    observation: &TablePaginationObservation,
    limits: TablePaginationLimits,
) -> Result<(), TablePaginationError> {
    if observation.schema_version != TABLE_PAGINATION_OBSERVATION_SCHEMA_VERSION {
        return Err(TablePaginationError::UnsupportedObservationVersion);
    }
    if observation.pages.is_empty() || observation.pages.len() > limits.0.pages {
        return Err(TablePaginationError::PageLimit);
    }
    let _ = positive_dimension(
        observation.first_page_available_height,
        limits.0.dimension_micrometers,
    )?;
    let _ = positive_dimension(
        observation.continuation_page_height,
        limits.0.dimension_micrometers,
    )?;
    let _ = serialize_bounded(observation, limits.0.serialized_bytes)?;
    Ok(())
}

fn validate_page_identity(
    observation: &TablePaginationObservation,
    page: &TablePage,
    page_offset: usize,
) -> Result<(), TablePaginationError> {
    let offset = u32::try_from(page_offset).map_err(|_| TablePaginationError::PageIndex)?;
    let expected = observation
        .anchor_page_index
        .checked_add(offset)
        .ok_or(TablePaginationError::PageIndex)?;
    if page.page_index != expected || page.items.is_empty() {
        return Err(TablePaginationError::PageIndex);
    }
    Ok(())
}

#[allow(clippy::too_many_arguments)]
fn validate_page(
    policy: &TablePaginationPolicy,
    observation: &TablePaginationObservation,
    page: &TablePage,
    page_offset: usize,
    limits: TablePaginationLimits,
    state: &mut ValidationState,
) -> Result<(), TablePaginationError> {
    let expected_headers = if page_offset == 0 {
        0
    } else {
        usize::try_from(policy.repeat_header_rows).map_err(|_| TablePaginationError::HeaderRange)?
    };
    validate_header_items(page, expected_headers, policy, state)?;
    validate_caption_order(page, page_offset, observation.pages.len(), policy, state)?;

    let mut consumed = 0_u64;
    let mut body_items = 0_usize;
    let mut last_body_ends = true;
    for (item_index, item) in page.items.iter().enumerate() {
        let item_height = match item {
            TablePageItem::RepeatedHeader { row } => {
                let index = usize::try_from(*row).map_err(|_| TablePaginationError::HeaderRange)?;
                positive_dimension(
                    policy
                        .rows
                        .get(index)
                        .ok_or(TablePaginationError::HeaderRange)?
                        .height,
                    limits.0.dimension_micrometers,
                )?
            }
            TablePageItem::RowFragment {
                row,
                fragment_index,
                height,
                begins_row,
                ends_row,
            } => {
                if !last_body_ends && item_index != expected_headers {
                    return Err(TablePaginationError::FragmentPageOrder);
                }
                state.observe_fragment(
                    policy,
                    ObservedRowFragment {
                        page_index: page.page_index,
                        row: *row,
                        fragment_index: *fragment_index,
                        height: *height,
                        begins_row: *begins_row,
                        ends_row: *ends_row,
                    },
                    limits,
                )?;
                body_items = body_items
                    .checked_add(1)
                    .ok_or(TablePaginationError::ArithmeticOverflow)?;
                last_body_ends = *ends_row;
                positive_dimension(*height, limits.0.dimension_micrometers)?
            }
            TablePageItem::Caption { .. } => caption_height(policy, limits)?,
        };
        consumed = consumed
            .checked_add(item_height)
            .ok_or(TablePaginationError::ArithmeticOverflow)?;
    }
    if body_items == 0 {
        return Err(TablePaginationError::EmptyTablePage);
    }
    let capacity = if page_offset == 0 {
        positive_dimension(
            observation.first_page_available_height,
            limits.0.dimension_micrometers,
        )?
    } else {
        positive_dimension(
            observation.continuation_page_height,
            limits.0.dimension_micrometers,
        )?
    };
    if consumed > capacity {
        return Err(TablePaginationError::PageOverflow);
    }
    if !last_body_ends && page_offset + 1 == observation.pages.len() {
        return Err(TablePaginationError::IncompleteRows);
    }
    Ok(())
}

fn validate_header_items(
    page: &TablePage,
    expected_headers: usize,
    policy: &TablePaginationPolicy,
    state: &mut ValidationState,
) -> Result<(), TablePaginationError> {
    for index in 0..expected_headers {
        match page.items.get(index) {
            Some(TablePageItem::RepeatedHeader { row })
                if usize::try_from(*row).ok() == Some(index) => {}
            _ => return Err(TablePaginationError::HeaderMismatch),
        }
    }
    if page
        .items
        .iter()
        .skip(expected_headers)
        .any(|item| matches!(item, TablePageItem::RepeatedHeader { .. }))
    {
        return Err(TablePaginationError::HeaderMismatch);
    }
    state.repeated_header_copy_count = state
        .repeated_header_copy_count
        .checked_add(expected_headers)
        .ok_or(TablePaginationError::ArithmeticOverflow)?;
    if expected_headers == policy.rows.len() {
        return Err(TablePaginationError::HeaderRange);
    }
    Ok(())
}

fn validate_caption_order(
    page: &TablePage,
    page_offset: usize,
    page_count: usize,
    policy: &TablePaginationPolicy,
    state: &mut ValidationState,
) -> Result<(), TablePaginationError> {
    let mut caption_index = None;
    for (index, item) in page.items.iter().enumerate() {
        if matches!(item, TablePageItem::Caption { .. }) && caption_index.replace(index).is_some() {
            return Err(TablePaginationError::CaptionDuplicate);
        }
    }
    let Some(index) = caption_index else {
        return Ok(());
    };
    if state.caption_page_index.is_some() {
        return Err(TablePaginationError::CaptionDuplicate);
    }
    let caption = policy
        .caption
        .as_ref()
        .ok_or(TablePaginationError::UnexpectedCaption)?;
    let TablePageItem::Caption { side } = &page.items[index] else {
        return Err(TablePaginationError::InternalInvariant);
    };
    if *side != caption.side {
        return Err(TablePaginationError::CaptionMismatch);
    }
    match caption.side {
        CaptionSide::Top if page_offset == 0 && index == 0 => {}
        CaptionSide::Bottom if page_offset + 1 == page_count && index + 1 == page.items.len() => {}
        _ => return Err(TablePaginationError::CaptionOrder),
    }
    state.caption_page_index = Some(page.page_index);
    Ok(())
}

fn validate_merged_cell_page_boundaries(
    grid: &TableGrid,
    row_pages: &[Option<(u32, u32)>],
) -> Result<(), TablePaginationError> {
    for cell in grid.master_cells() {
        if cell.row_span <= 1 {
            continue;
        }
        let first = usize::try_from(cell.row).map_err(|_| TablePaginationError::RowOrder)?;
        let last_row = cell
            .row
            .checked_add(cell.row_span - 1)
            .ok_or(TablePaginationError::RowOrder)?;
        let last = usize::try_from(last_row).map_err(|_| TablePaginationError::RowOrder)?;
        let first_pages = row_pages
            .get(first)
            .and_then(|value| *value)
            .ok_or(TablePaginationError::IncompleteRows)?;
        let last_pages = row_pages
            .get(last)
            .and_then(|value| *value)
            .ok_or(TablePaginationError::IncompleteRows)?;
        if first_pages.0 != last_pages.1 {
            return Err(TablePaginationError::MergedCellSplit);
        }
    }
    Ok(())
}

fn caption_height(
    policy: &TablePaginationPolicy,
    limits: TablePaginationLimits,
) -> Result<u64, TablePaginationError> {
    let caption = policy
        .caption
        .as_ref()
        .ok_or(TablePaginationError::UnexpectedCaption)?;
    positive_dimension(caption.block_height, limits.0.dimension_micrometers)?
        .checked_add(nonnegative_dimension(
            caption.gap,
            limits.0.dimension_micrometers,
        )?)
        .filter(|height| *height <= limits.0.dimension_micrometers)
        .ok_or(TablePaginationError::DimensionLimit)
}

fn positive_dimension(value: LengthMicrometers, maximum: u64) -> Result<u64, TablePaginationError> {
    let value = nonnegative_dimension(value, maximum)?;
    if value == 0 {
        return Err(TablePaginationError::InvalidDimension);
    }
    Ok(value)
}

fn nonnegative_dimension(
    value: LengthMicrometers,
    maximum: u64,
) -> Result<u64, TablePaginationError> {
    let value =
        u64::try_from(value.as_i64()).map_err(|_| TablePaginationError::InvalidDimension)?;
    if value > maximum {
        return Err(TablePaginationError::DimensionLimit);
    }
    Ok(value)
}

fn is_lower_hex_sha256(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn serialize_bounded<T: Serialize>(
    value: &T,
    maximum: usize,
) -> Result<Vec<u8>, TablePaginationError> {
    let mut writer = BoundedWriter::new(maximum);
    if serde_json::to_writer(&mut writer, value).is_err() {
        return match writer.failure {
            WriterFailure::Limit => Err(TablePaginationError::OutputLimit),
            WriterFailure::Allocation => Err(TablePaginationError::AllocationFailed),
            WriterFailure::None => Err(TablePaginationError::SerializationFailed),
        };
    }
    Ok(writer.bytes)
}

fn hex_digest(value: [u8; 32]) -> String {
    const HEX: &[u8; 16] = b"0123456789abcdef";
    let mut result = String::with_capacity(64);
    for byte in value {
        result.push(char::from(HEX[usize::from(byte >> 4)]));
        result.push(char::from(HEX[usize::from(byte & 0x0f)]));
    }
    result
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum TablePaginationError {
    #[error("table pagination limits are invalid")]
    InvalidLimit,
    #[error("table pagination schema version is unsupported")]
    UnsupportedVersion,
    #[error("table pagination observation schema version is unsupported")]
    UnsupportedObservationVersion,
    #[error("table pagination input exceeds its finite limit")]
    InputLimit,
    #[error("table pagination JSON is invalid")]
    InvalidJson,
    #[error("table pagination row count differs from the logical grid")]
    RowCountMismatch,
    #[error("table pagination row order is invalid")]
    RowOrder,
    #[error("table pagination row limit was exceeded")]
    RowLimit,
    #[error("table pagination page limit was exceeded")]
    PageLimit,
    #[error("table pagination fragment limit was exceeded")]
    FragmentLimit,
    #[error("table pagination dimension must be positive")]
    InvalidDimension,
    #[error("table pagination dimension exceeds its finite limit")]
    DimensionLimit,
    #[error("table pagination repeat-header range is invalid")]
    HeaderRange,
    #[error("table pagination header span crosses into the body")]
    HeaderSpanCrossesBody,
    #[error("table pagination repeated-header observation differs")]
    HeaderMismatch,
    #[error("table pagination logical header row cannot split")]
    HeaderRowSplit,
    #[error("table pagination caption digest is invalid")]
    CaptionDigest,
    #[error("table pagination caption is missing")]
    CaptionMissing,
    #[error("table pagination contains an unexpected caption")]
    UnexpectedCaption,
    #[error("table pagination contains duplicate captions")]
    CaptionDuplicate,
    #[error("table pagination caption properties differ")]
    CaptionMismatch,
    #[error("table pagination caption order differs")]
    CaptionOrder,
    #[error("table pagination page index is invalid")]
    PageIndex,
    #[error("table pagination page has no logical table row")]
    EmptyTablePage,
    #[error("table pagination page exceeds its available height")]
    PageOverflow,
    #[error("table pagination row fragment sequence is invalid")]
    FragmentSequence,
    #[error("table pagination row fragments are not on consecutive pages")]
    FragmentPageOrder,
    #[error("table pagination row fragment heights differ from the row height")]
    RowHeightMismatch,
    #[error("table pagination row split is forbidden")]
    RowSplitForbidden,
    #[error("table pagination nested-table row cannot split")]
    NestedTableSplit,
    #[error("table pagination unbreakable-object row cannot split")]
    UnbreakableObjectSplit,
    #[error("table pagination table split is forbidden")]
    TableSplitForbidden,
    #[error("table pagination vertically merged cell split is forbidden")]
    MergedCellSplit,
    #[error("table pagination required keep policy is not present")]
    RequiredKeepMissing,
    #[error("table pagination rows are incomplete")]
    IncompleteRows,
    #[error("table pagination arithmetic overflowed")]
    ArithmeticOverflow,
    #[error("table pagination allocation failed")]
    AllocationFailed,
    #[error("table pagination serialization failed")]
    SerializationFailed,
    #[error("table pagination output exceeds its finite limit")]
    OutputLimit,
    #[error("table pagination internal invariant failed")]
    InternalInvariant,
    #[error(transparent)]
    Grid(#[from] TableGridError),
}

impl TablePaginationError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidLimit => "table_pagination_invalid_limit",
            Self::UnsupportedVersion => "table_pagination_unsupported_version",
            Self::UnsupportedObservationVersion => {
                "table_pagination_unsupported_observation_version"
            }
            Self::InputLimit => "table_pagination_input_limit",
            Self::InvalidJson => "table_pagination_invalid_json",
            Self::RowCountMismatch => "table_pagination_row_count_mismatch",
            Self::RowOrder => "table_pagination_row_order",
            Self::RowLimit => "table_pagination_row_limit",
            Self::PageLimit => "table_pagination_page_limit",
            Self::FragmentLimit => "table_pagination_fragment_limit",
            Self::InvalidDimension => "table_pagination_invalid_dimension",
            Self::DimensionLimit => "table_pagination_dimension_limit",
            Self::HeaderRange => "table_pagination_header_range",
            Self::HeaderSpanCrossesBody => "table_pagination_header_span_crosses_body",
            Self::HeaderMismatch => "table_pagination_header_mismatch",
            Self::HeaderRowSplit => "table_pagination_header_row_split",
            Self::CaptionDigest => "table_pagination_caption_digest",
            Self::CaptionMissing => "table_pagination_caption_missing",
            Self::UnexpectedCaption => "table_pagination_unexpected_caption",
            Self::CaptionDuplicate => "table_pagination_caption_duplicate",
            Self::CaptionMismatch => "table_pagination_caption_mismatch",
            Self::CaptionOrder => "table_pagination_caption_order",
            Self::PageIndex => "table_pagination_page_index",
            Self::EmptyTablePage => "table_pagination_empty_table_page",
            Self::PageOverflow => "table_pagination_page_overflow",
            Self::FragmentSequence => "table_pagination_fragment_sequence",
            Self::FragmentPageOrder => "table_pagination_fragment_page_order",
            Self::RowHeightMismatch => "table_pagination_row_height_mismatch",
            Self::RowSplitForbidden => "table_pagination_row_split_forbidden",
            Self::NestedTableSplit => "table_pagination_nested_table_split",
            Self::UnbreakableObjectSplit => "table_pagination_unbreakable_object_split",
            Self::TableSplitForbidden => "table_pagination_table_split_forbidden",
            Self::MergedCellSplit => "table_pagination_merged_cell_split",
            Self::RequiredKeepMissing => "table_pagination_required_keep_missing",
            Self::IncompleteRows => "table_pagination_incomplete_rows",
            Self::ArithmeticOverflow => "table_pagination_arithmetic_overflow",
            Self::AllocationFailed => "table_pagination_allocation_failed",
            Self::SerializationFailed => "table_pagination_serialization_failed",
            Self::OutputLimit => "table_pagination_output_limit",
            Self::InternalInvariant => "table_pagination_internal_invariant",
            Self::Grid(error) => error.code(),
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
    maximum: usize,
    failure: WriterFailure,
}

impl BoundedWriter {
    const fn new(maximum: usize) -> Self {
        Self {
            bytes: Vec::new(),
            maximum,
            failure: WriterFailure::None,
        }
    }
}

impl io::Write for BoundedWriter {
    fn write(&mut self, buffer: &[u8]) -> io::Result<usize> {
        let Some(next) = self.bytes.len().checked_add(buffer.len()) else {
            self.failure = WriterFailure::Limit;
            return Err(io::Error::other("table pagination output limit"));
        };
        if next > self.maximum {
            self.failure = WriterFailure::Limit;
            return Err(io::Error::other("table pagination output limit"));
        }
        if self.bytes.try_reserve(buffer.len()).is_err() {
            self.failure = WriterFailure::Allocation;
            return Err(io::Error::other("table pagination allocation"));
        }
        self.bytes.extend_from_slice(buffer);
        Ok(buffer.len())
    }

    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}
