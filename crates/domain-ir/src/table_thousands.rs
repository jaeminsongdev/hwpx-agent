use std::collections::BTreeMap;
use std::fmt;

use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{
    CellCoordinate, FormulaAstDraft, FormulaCell, FormulaCellDraft, FormulaError,
    FormulaGridDimensions, FormulaLimits, FormulaNumberFormat, TABLE_FORMULA_SCHEMA_VERSION,
};

pub const TABLE_THOUSANDS_SCHEMA_VERSION: &str = "hwpx-agent.table-thousands/v1";

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableThousandsMode {
    Add,
    Remove,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableThousandsRequestDraft {
    pub schema_version: String,
    pub mode: TableThousandsMode,
    pub selected_cells: Vec<CellCoordinate>,
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableThousandsRequest {
    schema_version: &'static str,
    dimensions: FormulaGridDimensions,
    mode: TableThousandsMode,
    selected_cells: Vec<CellCoordinate>,
}

impl TableThousandsRequest {
    /// Validates and canonicalizes one exact formula-cell selection.
    ///
    /// # Errors
    ///
    /// Rejects schema drift, invalid dimensions, empty or oversized selections, duplicate cells,
    /// and coordinates outside the exact table dimensions.
    pub fn from_draft(
        draft: TableThousandsRequestDraft,
        dimensions: FormulaGridDimensions,
        limits: FormulaLimits,
    ) -> Result<Self, TableThousandsError> {
        if draft.schema_version != TABLE_THOUSANDS_SCHEMA_VERSION {
            return Err(TableThousandsError::UnsupportedVersion);
        }
        validate_dimensions(dimensions, limits)?;
        if draft.selected_cells.is_empty() {
            return Err(TableThousandsError::EmptySelection);
        }
        if draft.selected_cells.len() > limits.config().function_arguments {
            return Err(TableThousandsError::SelectionLimit);
        }
        let mut selected_cells = draft.selected_cells;
        selected_cells.sort_unstable();
        if selected_cells.windows(2).any(|pair| pair[0] == pair[1]) {
            return Err(TableThousandsError::DuplicateSelection);
        }
        if selected_cells
            .iter()
            .any(|coordinate| !inside(*coordinate, dimensions))
        {
            return Err(TableThousandsError::CoordinateOutOfBounds);
        }
        Ok(Self {
            schema_version: TABLE_THOUSANDS_SCHEMA_VERSION,
            dimensions,
            mode: draft.mode,
            selected_cells,
        })
    }

    /// Parses strict bounded JSON and validates it against exact table dimensions.
    ///
    /// # Errors
    ///
    /// Rejects empty, oversized, malformed, duplicate-key or unknown-field JSON and every invalid
    /// semantic request rejected by [`Self::from_draft`].
    pub fn from_json(
        bytes: &[u8],
        dimensions: FormulaGridDimensions,
        limits: FormulaLimits,
    ) -> Result<Self, TableThousandsError> {
        if bytes.is_empty() || bytes.len() > limits.config().input_bytes {
            return Err(TableThousandsError::InputLimit);
        }
        let draft = serde_json::from_slice(bytes).map_err(|_| TableThousandsError::InvalidJson)?;
        Self::from_draft(draft, dimensions, limits)
    }

    #[must_use]
    pub const fn dimensions(&self) -> FormulaGridDimensions {
        self.dimensions
    }

    #[must_use]
    pub const fn mode(&self) -> TableThousandsMode {
        self.mode
    }

    #[must_use]
    pub fn selected_cells(&self) -> &[CellCoordinate] {
        &self.selected_cells
    }

    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        match self.mode {
            TableThousandsMode::Add => "table.thousands_add",
            TableThousandsMode::Remove => "table.thousands_remove",
        }
    }
}

impl fmt::Debug for TableThousandsRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableThousandsRequest")
            .field("schema_version", &self.schema_version)
            .field("dimensions", &self.dimensions)
            .field("mode", &self.mode)
            .field("selected_cells", &self.selected_cells)
            .finish()
    }
}

#[derive(Eq, PartialEq, Serialize)]
pub struct TableThousandsPlan {
    schema_version: &'static str,
    capability_id: &'static str,
    request: TableThousandsRequest,
    formatted_cells: Vec<FormulaCell>,
}

impl TableThousandsPlan {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
    }

    #[must_use]
    pub const fn request(&self) -> &TableThousandsRequest {
        &self.request
    }

    #[must_use]
    pub fn formatted_cells(&self) -> &[FormulaCell] {
        &self.formatted_cells
    }

    /// Serializes the validated plan to bounded canonical JSON.
    ///
    /// # Errors
    ///
    /// Returns an error if serialization fails or exceeds the formula serialization limit.
    pub fn canonical_json(&self, limits: FormulaLimits) -> Result<Vec<u8>, TableThousandsError> {
        let bytes = serde_json::to_vec(self).map_err(|_| TableThousandsError::Serialization)?;
        if bytes.len() > limits.config().serialized_bytes {
            return Err(TableThousandsError::OutputLimit);
        }
        Ok(bytes)
    }

    /// Returns SHA-256 over canonical plan JSON.
    ///
    /// # Errors
    ///
    /// Propagates bounded canonical serialization failures.
    pub fn canonical_sha256(&self, limits: FormulaLimits) -> Result<[u8; 32], TableThousandsError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TableThousandsPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableThousandsPlan")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("request", &self.request)
            .field("formatted_cells", &"<redacted>")
            .finish()
    }
}

#[derive(Debug)]
pub struct TableThousandsBuilder;

impl TableThousandsBuilder {
    /// Applies only the grouping flag to an exact set of numeric formula-cell formats.
    ///
    /// # Errors
    ///
    /// Rejects missing, extra or duplicate supplied cells, non-number formats, formula cells that
    /// do not validate against the request's exact dimensions, and oversized output. No partial
    /// plan is returned.
    pub fn build(
        request: TableThousandsRequest,
        cells: &[FormulaCell],
        limits: FormulaLimits,
    ) -> Result<TableThousandsPlan, TableThousandsError> {
        if cells.len() != request.selected_cells.len() {
            return Err(TableThousandsError::SelectionMismatch);
        }
        let mut supplied = BTreeMap::new();
        for cell in cells {
            if supplied.insert(cell.owner(), cell).is_some() {
                return Err(TableThousandsError::SelectionMismatch);
            }
        }
        if supplied
            .keys()
            .copied()
            .ne(request.selected_cells.iter().copied())
        {
            return Err(TableThousandsError::SelectionMismatch);
        }

        let use_grouping = request.mode == TableThousandsMode::Add;
        let mut formatted_cells = Vec::with_capacity(request.selected_cells.len());
        for coordinate in &request.selected_cells {
            let cell = supplied
                .get(coordinate)
                .ok_or(TableThousandsError::SelectionMismatch)?;
            let FormulaNumberFormat::Number { decimal_places, .. } = cell.number_format() else {
                return Err(TableThousandsError::UnsupportedFormat);
            };
            formatted_cells.push(FormulaCell::from_draft(
                FormulaCellDraft {
                    schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
                    owner: cell.owner(),
                    ast: FormulaAstDraft {
                        schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
                        expression: cell.ast().expression().clone(),
                    },
                    cache: cell.cache().clone(),
                    number_format: FormulaNumberFormat::Number {
                        decimal_places,
                        use_grouping,
                    },
                },
                request.dimensions,
                limits,
            )?);
        }

        let plan = TableThousandsPlan {
            schema_version: TABLE_THOUSANDS_SCHEMA_VERSION,
            capability_id: request.capability_id(),
            request,
            formatted_cells,
        };
        let _ = plan.canonical_json(limits)?;
        Ok(plan)
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum TableThousandsError {
    #[error("table thousands schema version is unsupported")]
    UnsupportedVersion,
    #[error("table thousands JSON input is empty or oversized")]
    InputLimit,
    #[error("table thousands JSON is invalid")]
    InvalidJson,
    #[error("table thousands dimensions or coordinates are invalid")]
    CoordinateOutOfBounds,
    #[error("table thousands selection is empty")]
    EmptySelection,
    #[error("table thousands selection exceeds its cell limit")]
    SelectionLimit,
    #[error("table thousands selection contains a duplicate cell")]
    DuplicateSelection,
    #[error("table thousands supplied cells do not exactly match the selection")]
    SelectionMismatch,
    #[error("table thousands requires an existing numeric formula-cell format")]
    UnsupportedFormat,
    #[error("table thousands plan exceeds its output limit")]
    OutputLimit,
    #[error("table thousands plan serialization failed")]
    Serialization,
    #[error("table thousands formula validation failed: {0}")]
    Formula(#[from] FormulaError),
}

impl TableThousandsError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::UnsupportedVersion => "table_thousands_unsupported_version",
            Self::InputLimit => "table_thousands_input_limit",
            Self::InvalidJson => "table_thousands_invalid_json",
            Self::CoordinateOutOfBounds => "table_thousands_coordinate_out_of_bounds",
            Self::EmptySelection => "table_thousands_empty_selection",
            Self::SelectionLimit => "table_thousands_selection_limit",
            Self::DuplicateSelection => "table_thousands_duplicate_selection",
            Self::SelectionMismatch => "table_thousands_selection_mismatch",
            Self::UnsupportedFormat => "table_thousands_unsupported_format",
            Self::OutputLimit => "table_thousands_output_limit",
            Self::Serialization => "table_thousands_serialization",
            Self::Formula(_) => "table_thousands_formula",
        }
    }
}

fn validate_dimensions(
    dimensions: FormulaGridDimensions,
    limits: FormulaLimits,
) -> Result<(), TableThousandsError> {
    if dimensions.rows == 0
        || dimensions.columns == 0
        || dimensions.rows > limits.config().rows
        || dimensions.columns > limits.config().columns
    {
        return Err(TableThousandsError::CoordinateOutOfBounds);
    }
    Ok(())
}

const fn inside(coordinate: CellCoordinate, dimensions: FormulaGridDimensions) -> bool {
    coordinate.row < dimensions.rows && coordinate.column < dimensions.columns
}
