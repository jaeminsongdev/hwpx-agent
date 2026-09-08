use std::fmt;

use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{
    CellCoordinate, FormulaAst, FormulaAstDraft, FormulaCache, FormulaCell, FormulaCellDraft,
    FormulaCellReference, FormulaError, FormulaExpression, FormulaFunction, FormulaGridDimensions,
    FormulaLimits, FormulaNumberFormat, FormulaRange, FormulaReferenceKind,
    TABLE_FORMULA_SCHEMA_VERSION,
};

pub const TABLE_AGGREGATE_SCHEMA_VERSION: &str = "hwpx-agent.table-aggregate/v1";

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableAggregateAxis {
    Block,
    Horizontal,
    Vertical,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableAggregateRange {
    pub start: CellCoordinate,
    pub end: CellCoordinate,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableAggregateRequestDraft {
    pub schema_version: String,
    pub axis: TableAggregateAxis,
    pub function: FormulaFunction,
    pub source: TableAggregateRange,
    pub destination: CellCoordinate,
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableAggregateRequest {
    schema_version: &'static str,
    dimensions: FormulaGridDimensions,
    axis: TableAggregateAxis,
    function: FormulaFunction,
    source: TableAggregateRange,
    destination: CellCoordinate,
}

impl TableAggregateRequest {
    /// Validates a bounded aggregate request against exact table dimensions.
    ///
    /// Horizontal requests consume a contiguous range strictly to the left of the destination;
    /// vertical requests consume one strictly above it. Block requests admit any nonempty ordered
    /// rectangle that does not contain the destination.
    ///
    /// # Errors
    ///
    /// Rejects schema drift, invalid dimensions or coordinates, reversed ranges, self-reference,
    /// and ranges that do not match the declared axis.
    pub fn from_draft(
        draft: TableAggregateRequestDraft,
        dimensions: FormulaGridDimensions,
        limits: FormulaLimits,
    ) -> Result<Self, TableAggregateError> {
        let TableAggregateRequestDraft {
            schema_version,
            axis,
            function,
            source,
            destination,
        } = draft;
        if schema_version != TABLE_AGGREGATE_SCHEMA_VERSION {
            return Err(TableAggregateError::UnsupportedVersion);
        }
        validate_dimensions(dimensions, limits)?;
        validate_coordinate(source.start, dimensions)?;
        validate_coordinate(source.end, dimensions)?;
        validate_coordinate(destination, dimensions)?;
        if source.start.row > source.end.row || source.start.column > source.end.column {
            return Err(TableAggregateError::RangeOrder);
        }
        if contains(source, destination) {
            return Err(TableAggregateError::SelfReference);
        }
        match axis {
            TableAggregateAxis::Block => {}
            TableAggregateAxis::Horizontal => {
                if source.start.row != destination.row
                    || source.end.row != destination.row
                    || source.end.column >= destination.column
                {
                    return Err(TableAggregateError::AxisMismatch);
                }
            }
            TableAggregateAxis::Vertical => {
                if source.start.column != destination.column
                    || source.end.column != destination.column
                    || source.end.row >= destination.row
                {
                    return Err(TableAggregateError::AxisMismatch);
                }
            }
        }
        Ok(Self {
            schema_version: TABLE_AGGREGATE_SCHEMA_VERSION,
            dimensions,
            axis,
            function,
            source,
            destination,
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
    ) -> Result<Self, TableAggregateError> {
        if bytes.is_empty() || bytes.len() > limits.config().serialized_bytes {
            return Err(TableAggregateError::InputLimit);
        }
        reject_duplicate_json_keys(bytes)?;
        let draft = serde_json::from_slice(bytes).map_err(|_| TableAggregateError::InvalidJson)?;
        Self::from_draft(draft, dimensions, limits)
    }

    #[must_use]
    pub const fn dimensions(&self) -> FormulaGridDimensions {
        self.dimensions
    }

    #[must_use]
    pub const fn axis(&self) -> TableAggregateAxis {
        self.axis
    }

    #[must_use]
    pub const fn function(&self) -> FormulaFunction {
        self.function
    }

    #[must_use]
    pub const fn source(&self) -> TableAggregateRange {
        self.source
    }

    #[must_use]
    pub const fn destination(&self) -> CellCoordinate {
        self.destination
    }

    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        match (self.axis, self.function) {
            (TableAggregateAxis::Block, FormulaFunction::Sum) => "table.block_sum",
            (TableAggregateAxis::Block, FormulaFunction::Average) => "table.block_average",
            (TableAggregateAxis::Block, FormulaFunction::Product) => "table.block_product",
            (TableAggregateAxis::Horizontal, FormulaFunction::Sum) => "table.horizontal_sum",
            (TableAggregateAxis::Horizontal, FormulaFunction::Average) => {
                "table.horizontal_average"
            }
            (TableAggregateAxis::Horizontal, FormulaFunction::Product) => {
                "table.horizontal_product"
            }
            (TableAggregateAxis::Vertical, FormulaFunction::Sum) => "table.vertical_sum",
            (TableAggregateAxis::Vertical, FormulaFunction::Average) => "table.vertical_average",
            (TableAggregateAxis::Vertical, FormulaFunction::Product) => "table.vertical_product",
        }
    }
}

impl fmt::Debug for TableAggregateRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableAggregateRequest")
            .field("schema_version", &self.schema_version)
            .field("dimensions", &self.dimensions)
            .field("axis", &self.axis)
            .field("function", &self.function)
            .field("source", &self.source)
            .field("destination", &self.destination)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableAggregatePlan {
    schema_version: &'static str,
    capability_id: &'static str,
    request: TableAggregateRequest,
    formula: FormulaCell,
}

impl TableAggregatePlan {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
    }

    #[must_use]
    pub const fn request(&self) -> &TableAggregateRequest {
        &self.request
    }

    #[must_use]
    pub const fn formula(&self) -> &FormulaCell {
        &self.formula
    }

    /// Serializes the validated plan to bounded canonical JSON.
    ///
    /// # Errors
    ///
    /// Returns an error if serialization fails or exceeds the formula serialization limit.
    pub fn canonical_json(&self, limits: FormulaLimits) -> Result<Vec<u8>, TableAggregateError> {
        let bytes = serde_json::to_vec(self).map_err(|_| TableAggregateError::Serialization)?;
        if bytes.len() > limits.config().serialized_bytes {
            return Err(TableAggregateError::OutputLimit);
        }
        Ok(bytes)
    }

    /// Returns SHA-256 over canonical plan JSON.
    ///
    /// # Errors
    ///
    /// Propagates bounded canonical serialization failures.
    pub fn canonical_sha256(&self, limits: FormulaLimits) -> Result<[u8; 32], TableAggregateError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TableAggregatePlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableAggregatePlan")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("request", &self.request)
            .field("formula", &"<redacted>")
            .finish()
    }
}

#[derive(Debug)]
pub struct TableAggregateBuilder;

impl TableAggregateBuilder {
    /// Compiles one validated aggregate request into a cache-cleared locale-neutral formula plan.
    ///
    /// # Errors
    ///
    /// Rejects invalid requests or any formula/dimension/serialization failure. No partial plan is
    /// returned.
    pub fn build(
        request: TableAggregateRequest,
        limits: FormulaLimits,
    ) -> Result<TableAggregatePlan, TableAggregateError> {
        let function = request.function;
        let range = FormulaRange {
            start: relative_reference(request.source.start),
            end: relative_reference(request.source.end),
        };
        let ast = FormulaAst::from_draft(
            FormulaAstDraft {
                schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
                expression: FormulaExpression::Function {
                    function,
                    arguments: vec![FormulaExpression::Range { range }],
                },
            },
            limits,
        )?;
        let formula = FormulaCell::from_draft(
            FormulaCellDraft {
                schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
                owner: request.destination,
                ast: FormulaAstDraft {
                    schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
                    expression: ast.expression().clone(),
                },
                cache: FormulaCache::Absent,
                number_format: FormulaNumberFormat::General,
            },
            request.dimensions,
            limits,
        )?;
        let plan = TableAggregatePlan {
            schema_version: TABLE_AGGREGATE_SCHEMA_VERSION,
            capability_id: request.capability_id(),
            request,
            formula,
        };
        let _ = plan.canonical_json(limits)?;
        Ok(plan)
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum TableAggregateError {
    #[error("table aggregate schema version is unsupported")]
    UnsupportedVersion,
    #[error("table aggregate JSON input is empty or oversized")]
    InputLimit,
    #[error("table aggregate JSON is invalid")]
    InvalidJson,
    #[error("table aggregate dimensions or coordinates are invalid")]
    CoordinateOutOfBounds,
    #[error("table aggregate source range is reversed")]
    RangeOrder,
    #[error("table aggregate destination is inside its source range")]
    SelfReference,
    #[error("table aggregate range does not match its declared axis")]
    AxisMismatch,
    #[error("table aggregate plan exceeds its output limit")]
    OutputLimit,
    #[error("table aggregate plan serialization failed")]
    Serialization,
    #[error("table aggregate formula validation failed: {0}")]
    Formula(#[from] FormulaError),
}

impl TableAggregateError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::UnsupportedVersion => "table_aggregate_unsupported_version",
            Self::InputLimit => "table_aggregate_input_limit",
            Self::InvalidJson => "table_aggregate_invalid_json",
            Self::CoordinateOutOfBounds => "table_aggregate_coordinate_out_of_bounds",
            Self::RangeOrder => "table_aggregate_range_order",
            Self::SelfReference => "table_aggregate_self_reference",
            Self::AxisMismatch => "table_aggregate_axis_mismatch",
            Self::OutputLimit => "table_aggregate_output_limit",
            Self::Serialization => "table_aggregate_serialization",
            Self::Formula(_) => "table_aggregate_formula",
        }
    }
}

fn relative_reference(coordinate: CellCoordinate) -> FormulaCellReference {
    FormulaCellReference {
        row: coordinate.row,
        column: coordinate.column,
        row_kind: FormulaReferenceKind::Relative,
        column_kind: FormulaReferenceKind::Relative,
    }
}

fn validate_dimensions(
    dimensions: FormulaGridDimensions,
    limits: FormulaLimits,
) -> Result<(), TableAggregateError> {
    if dimensions.rows == 0
        || dimensions.columns == 0
        || dimensions.rows > limits.config().rows
        || dimensions.columns > limits.config().columns
    {
        return Err(TableAggregateError::CoordinateOutOfBounds);
    }
    Ok(())
}

fn validate_coordinate(
    coordinate: CellCoordinate,
    dimensions: FormulaGridDimensions,
) -> Result<(), TableAggregateError> {
    if coordinate.row >= dimensions.rows || coordinate.column >= dimensions.columns {
        return Err(TableAggregateError::CoordinateOutOfBounds);
    }
    Ok(())
}

fn contains(range: TableAggregateRange, coordinate: CellCoordinate) -> bool {
    coordinate.row >= range.start.row
        && coordinate.row <= range.end.row
        && coordinate.column >= range.start.column
        && coordinate.column <= range.end.column
}

fn reject_duplicate_json_keys(bytes: &[u8]) -> Result<(), TableAggregateError> {
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
            use std::collections::BTreeSet;

            let mut keys = BTreeSet::new();
            while let Some(key) = map.next_key::<String>()? {
                if !keys.insert(key) {
                    return Err(serde::de::Error::custom("duplicate key"));
                }
                map.next_value_seed(DuplicateRejectingSeed)?;
            }
            Ok(())
        }
    }

    struct DuplicateRejectingSeed;

    impl<'de> serde::de::DeserializeSeed<'de> for DuplicateRejectingSeed {
        type Value = ();

        fn deserialize<D>(self, deserializer: D) -> Result<Self::Value, D::Error>
        where
            D: serde::Deserializer<'de>,
        {
            deserializer.deserialize_any(DuplicateRejectingAnyVisitor)
        }
    }

    struct DuplicateRejectingAnyVisitor;

    impl<'de> serde::de::Visitor<'de> for DuplicateRejectingAnyVisitor {
        type Value = ();

        fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
            formatter.write_str("any JSON value")
        }

        fn visit_map<A>(self, mut map: A) -> Result<Self::Value, A::Error>
        where
            A: serde::de::MapAccess<'de>,
        {
            use std::collections::BTreeSet;

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
    serde::de::Deserializer::deserialize_map(&mut deserializer, DuplicateRejectingVisitor)
        .map_err(|_| TableAggregateError::InvalidJson)?;
    deserializer
        .end()
        .map_err(|_| TableAggregateError::InvalidJson)
}
