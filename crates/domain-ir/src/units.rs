use std::fmt;

use serde::{Deserialize, Serialize};
use thiserror::Error;

use crate::LogicalNodeId;

const MAX_INPUT_DENOMINATOR: u32 = 1_000_000_000;
const MAX_DPI: u32 = 1_000_000;

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum UnitError {
    #[error("unit input denominator is invalid")]
    InvalidDenominator,
    #[error("unit DPI is invalid")]
    InvalidDpi,
    #[error("unit conversion overflowed")]
    Overflow,
    #[error("coordinate space and anchor are incompatible")]
    IncompatibleCoordinateSpace,
}

impl UnitError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidDenominator => "unit_invalid_denominator",
            Self::InvalidDpi => "unit_invalid_dpi",
            Self::Overflow => "unit_overflow",
            Self::IncompatibleCoordinateSpace => "unit_incompatible_coordinate_space",
        }
    }
}

#[derive(Clone, Copy, Eq, PartialEq, Serialize)]
pub struct RationalInput {
    numerator: i64,
    denominator: u32,
}

impl<'de> Deserialize<'de> for RationalInput {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        #[derive(Deserialize)]
        #[serde(deny_unknown_fields)]
        struct Wire {
            numerator: i64,
            denominator: u32,
        }

        let wire = Wire::deserialize(deserializer)?;
        Self::new(wire.numerator, wire.denominator).map_err(serde::de::Error::custom)
    }
}

impl RationalInput {
    /// Creates an exact bounded rational input.
    ///
    /// # Errors
    ///
    /// Rejects a zero or excessively large denominator.
    pub fn new(numerator: i64, denominator: u32) -> Result<Self, UnitError> {
        if denominator == 0 || denominator > MAX_INPUT_DENOMINATOR {
            return Err(UnitError::InvalidDenominator);
        }
        Ok(Self {
            numerator,
            denominator,
        })
    }

    #[must_use]
    pub const fn integer(value: i64) -> Self {
        Self {
            numerator: value,
            denominator: 1,
        }
    }

    #[must_use]
    pub const fn numerator(self) -> i64 {
        self.numerator
    }

    #[must_use]
    pub const fn denominator(self) -> u32 {
        self.denominator
    }
}

impl fmt::Debug for RationalInput {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("RationalInput(<redacted>)")
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum UnitKind {
    Millimeter,
    Micrometer,
    Point,
    PointMilli,
    HwpUnit,
    Pixel,
    Ratio,
    RatioMillionths,
    Percent,
    Degree,
    Microdegree,
}

#[derive(Clone, Copy, Eq, PartialEq, Serialize)]
pub struct ConversionReceipt {
    source_unit: UnitKind,
    target_unit: UnitKind,
    source_numerator: i64,
    source_denominator: u32,
    normalized_value: i64,
    rounding_delta_numerator: i64,
    rounding_delta_denominator: u64,
    context_dpi: Option<u32>,
}

impl ConversionReceipt {
    #[must_use]
    pub const fn source_unit(self) -> UnitKind {
        self.source_unit
    }

    #[must_use]
    pub const fn target_unit(self) -> UnitKind {
        self.target_unit
    }

    #[must_use]
    pub const fn source_input(self) -> RationalInput {
        RationalInput {
            numerator: self.source_numerator,
            denominator: self.source_denominator,
        }
    }

    #[must_use]
    pub const fn normalized_value(self) -> i64 {
        self.normalized_value
    }

    #[must_use]
    pub const fn rounding_delta(self) -> (i64, u64) {
        (
            self.rounding_delta_numerator,
            self.rounding_delta_denominator,
        )
    }

    #[must_use]
    pub const fn context_dpi(self) -> Option<u32> {
        self.context_dpi
    }
}

impl fmt::Debug for ConversionReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ConversionReceipt")
            .field("source_unit", &self.source_unit)
            .field("target_unit", &self.target_unit)
            .field("values", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct Conversion<T> {
    value: T,
    receipt: ConversionReceipt,
}

impl<T> Conversion<T> {
    #[must_use]
    pub fn value(&self) -> &T {
        &self.value
    }

    #[must_use]
    pub const fn receipt(&self) -> ConversionReceipt {
        self.receipt
    }

    #[must_use]
    pub fn into_parts(self) -> (T, ConversionReceipt) {
        (self.value, self.receipt)
    }
}

impl<T> fmt::Debug for Conversion<T> {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("Conversion(<redacted>)")
    }
}

macro_rules! fixed_unit {
    ($name:ident) => {
        #[derive(Clone, Copy, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize, Deserialize)]
        #[serde(transparent)]
        pub struct $name(i64);

        impl $name {
            #[must_use]
            pub const fn from_raw(value: i64) -> Self {
                Self(value)
            }

            #[must_use]
            pub const fn as_i64(self) -> i64 {
                self.0
            }
        }

        impl fmt::Debug for $name {
            fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
                formatter.write_str(concat!(stringify!($name), "(<redacted>)"))
            }
        }
    };
}

fixed_unit!(LengthMicrometers);
fixed_unit!(PointMilli);
fixed_unit!(RatioMillionths);
fixed_unit!(AngleMicrodegrees);
fixed_unit!(HwpUnit);

impl LengthMicrometers {
    /// Converts millimeters to integer micrometers with half-away-from-zero rounding.
    ///
    /// # Errors
    ///
    /// Returns `UnitError::Overflow` when the exact rational result cannot fit.
    pub fn from_millimeters(input: RationalInput) -> Result<Conversion<Self>, UnitError> {
        convert(
            input,
            UnitKind::Millimeter,
            UnitKind::Micrometer,
            1_000,
            1,
            None,
            Self,
        )
    }

    /// Converts typographic points to physical micrometers (`1 pt = 3175/9 um`).
    ///
    /// # Errors
    ///
    /// Returns `UnitError::Overflow` when the exact rational result cannot fit.
    pub fn from_points(input: RationalInput) -> Result<Conversion<Self>, UnitError> {
        convert(
            input,
            UnitKind::Point,
            UnitKind::Micrometer,
            3_175,
            9,
            None,
            Self,
        )
    }

    /// Converts official HWP 5 `1/7200 inch` units to micrometers (`127/36 um`).
    ///
    /// # Errors
    ///
    /// Returns `UnitError::Overflow` when the exact rational result cannot fit.
    pub fn from_hwp_unit(input: HwpUnit) -> Result<Conversion<Self>, UnitError> {
        convert(
            RationalInput::integer(input.as_i64()),
            UnitKind::HwpUnit,
            UnitKind::Micrometer,
            127,
            36,
            None,
            Self,
        )
    }

    /// Converts pixels at an explicit positive DPI to micrometers.
    ///
    /// # Errors
    ///
    /// Rejects zero/excessive DPI and arithmetic overflow.
    pub fn from_pixels(input: RationalInput, dpi: u32) -> Result<Conversion<Self>, UnitError> {
        if dpi == 0 || dpi > MAX_DPI {
            return Err(UnitError::InvalidDpi);
        }
        convert(
            input,
            UnitKind::Pixel,
            UnitKind::Micrometer,
            25_400,
            i128::from(dpi),
            Some(dpi),
            Self,
        )
    }

    /// Lowers micrometers to official HWP 5 `1/7200 inch` units.
    ///
    /// # Errors
    ///
    /// Returns `UnitError::Overflow` when the rounded result cannot fit.
    pub fn to_hwp_unit(self) -> Result<Conversion<HwpUnit>, UnitError> {
        convert(
            RationalInput::integer(self.as_i64()),
            UnitKind::Micrometer,
            UnitKind::HwpUnit,
            36,
            127,
            None,
            HwpUnit,
        )
    }

    /// Adds a signed displacement without wrapping.
    ///
    /// # Errors
    ///
    /// Returns `UnitError::Overflow` instead of wrapping an `i64` boundary.
    pub fn checked_add(self, displacement: Self) -> Result<Self, UnitError> {
        self.0
            .checked_add(displacement.0)
            .map(Self)
            .ok_or(UnitError::Overflow)
    }
}

impl PointMilli {
    /// Converts points to thousandths of a point.
    ///
    /// # Errors
    ///
    /// Returns `UnitError::Overflow` when the exact rational result cannot fit.
    pub fn from_points(input: RationalInput) -> Result<Conversion<Self>, UnitError> {
        convert(
            input,
            UnitKind::Point,
            UnitKind::PointMilli,
            1_000,
            1,
            None,
            Self,
        )
    }
}

impl RatioMillionths {
    /// Converts a dimensionless ratio to millionths.
    ///
    /// # Errors
    ///
    /// Returns `UnitError::Overflow` when the exact rational result cannot fit.
    pub fn from_ratio(input: RationalInput) -> Result<Conversion<Self>, UnitError> {
        convert(
            input,
            UnitKind::Ratio,
            UnitKind::RatioMillionths,
            1_000_000,
            1,
            None,
            Self,
        )
    }

    /// Converts percent to ratio millionths (`100% = 1_000_000`).
    ///
    /// # Errors
    ///
    /// Returns `UnitError::Overflow` when the exact rational result cannot fit.
    pub fn from_percent(input: RationalInput) -> Result<Conversion<Self>, UnitError> {
        convert(
            input,
            UnitKind::Percent,
            UnitKind::RatioMillionths,
            10_000,
            1,
            None,
            Self,
        )
    }
}

impl AngleMicrodegrees {
    /// Converts degrees to millionths of a degree.
    ///
    /// # Errors
    ///
    /// Returns `UnitError::Overflow` when the exact rational result cannot fit.
    pub fn from_degrees(input: RationalInput) -> Result<Conversion<Self>, UnitError> {
        convert(
            input,
            UnitKind::Degree,
            UnitKind::Microdegree,
            1_000_000,
            1,
            None,
            Self,
        )
    }
}

fn convert<T>(
    input: RationalInput,
    source_unit: UnitKind,
    target_unit: UnitKind,
    multiplier_numerator: i128,
    multiplier_denominator: i128,
    context_dpi: Option<u32>,
    build: impl FnOnce(i64) -> T,
) -> Result<Conversion<T>, UnitError> {
    let exact_numerator = i128::from(input.numerator)
        .checked_mul(multiplier_numerator)
        .ok_or(UnitError::Overflow)?;
    let exact_denominator = i128::from(input.denominator)
        .checked_mul(multiplier_denominator)
        .ok_or(UnitError::Overflow)?;
    let (normalized_value, delta_numerator, delta_denominator) =
        round_half_away_from_zero(exact_numerator, exact_denominator)?;
    Ok(Conversion {
        value: build(normalized_value),
        receipt: ConversionReceipt {
            source_unit,
            target_unit,
            source_numerator: input.numerator,
            source_denominator: input.denominator,
            normalized_value,
            rounding_delta_numerator: delta_numerator,
            rounding_delta_denominator: delta_denominator,
            context_dpi,
        },
    })
}

fn round_half_away_from_zero(
    numerator: i128,
    denominator: i128,
) -> Result<(i64, i64, u64), UnitError> {
    if denominator <= 0 {
        return Err(UnitError::InvalidDenominator);
    }
    let mut rounded = numerator / denominator;
    let remainder = numerator % denominator;
    if remainder
        .unsigned_abs()
        .checked_mul(2)
        .ok_or(UnitError::Overflow)?
        >= denominator.unsigned_abs()
    {
        rounded = rounded
            .checked_add(if numerator.is_negative() { -1 } else { 1 })
            .ok_or(UnitError::Overflow)?;
    }
    let normalized_value = i64::try_from(rounded).map_err(|_| UnitError::Overflow)?;
    let delta_numerator = rounded
        .checked_mul(denominator)
        .and_then(|value| value.checked_sub(numerator))
        .ok_or(UnitError::Overflow)?;
    let divisor = gcd(delta_numerator.unsigned_abs(), denominator.unsigned_abs());
    let reduced_numerator =
        delta_numerator / i128::try_from(divisor).map_err(|_| UnitError::Overflow)?;
    let reduced_denominator = denominator.unsigned_abs() / divisor;
    Ok((
        normalized_value,
        i64::try_from(reduced_numerator).map_err(|_| UnitError::Overflow)?,
        u64::try_from(reduced_denominator).map_err(|_| UnitError::Overflow)?,
    ))
}

fn gcd(mut left: u128, mut right: u128) -> u128 {
    if left == 0 {
        return right;
    }
    while right != 0 {
        let remainder = left % right;
        left = right;
        right = remainder;
    }
    left
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum CoordinateSpace {
    Page,
    Content,
    Anchor,
    ObjectLocal,
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(tag = "anchor_type", rename_all = "snake_case")]
pub enum CoordinateAnchor {
    Page,
    Content,
    LogicalNode { node_id: LogicalNodeId },
    Object { node_id: LogicalNodeId },
}

impl fmt::Debug for CoordinateAnchor {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::Page => "CoordinateAnchor::Page",
            Self::Content => "CoordinateAnchor::Content",
            Self::LogicalNode { .. } => "CoordinateAnchor::LogicalNode(<redacted>)",
            Self::Object { .. } => "CoordinateAnchor::Object(<redacted>)",
        })
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct Position2D {
    x: LengthMicrometers,
    y: LengthMicrometers,
    space: CoordinateSpace,
    anchor: CoordinateAnchor,
}

impl<'de> Deserialize<'de> for Position2D {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        #[derive(Deserialize)]
        #[serde(deny_unknown_fields)]
        struct Wire {
            x: LengthMicrometers,
            y: LengthMicrometers,
            space: CoordinateSpace,
            anchor: CoordinateAnchor,
        }

        let wire = Wire::deserialize(deserializer)?;
        Self::new(wire.x, wire.y, wire.space, wire.anchor).map_err(serde::de::Error::custom)
    }
}

impl Position2D {
    /// Creates a position only when its coordinate space and anchor are compatible.
    ///
    /// # Errors
    ///
    /// Returns `UnitError::IncompatibleCoordinateSpace` for a mismatched pair.
    pub fn new(
        x: LengthMicrometers,
        y: LengthMicrometers,
        space: CoordinateSpace,
        anchor: CoordinateAnchor,
    ) -> Result<Self, UnitError> {
        let compatible = matches!(
            (&space, &anchor),
            (CoordinateSpace::Page, CoordinateAnchor::Page)
                | (CoordinateSpace::Content, CoordinateAnchor::Content)
                | (
                    CoordinateSpace::Anchor,
                    CoordinateAnchor::LogicalNode { .. }
                )
                | (
                    CoordinateSpace::ObjectLocal,
                    CoordinateAnchor::Object { .. }
                )
        );
        if !compatible {
            return Err(UnitError::IncompatibleCoordinateSpace);
        }
        Ok(Self {
            x,
            y,
            space,
            anchor,
        })
    }

    /// Applies a checked translation while retaining the explicit space and anchor.
    ///
    /// # Errors
    ///
    /// Returns `UnitError::Overflow` if either translated coordinate cannot fit.
    pub fn checked_translate(
        &self,
        delta_x: LengthMicrometers,
        delta_y: LengthMicrometers,
    ) -> Result<Self, UnitError> {
        Ok(Self {
            x: self.x.checked_add(delta_x)?,
            y: self.y.checked_add(delta_y)?,
            space: self.space,
            anchor: self.anchor.clone(),
        })
    }

    #[must_use]
    pub const fn x(&self) -> LengthMicrometers {
        self.x
    }

    #[must_use]
    pub const fn y(&self) -> LengthMicrometers {
        self.y
    }

    #[must_use]
    pub const fn space(&self) -> CoordinateSpace {
        self.space
    }

    #[must_use]
    pub const fn anchor(&self) -> &CoordinateAnchor {
        &self.anchor
    }
}

impl fmt::Debug for Position2D {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("Position2D")
            .field("space", &self.space)
            .field("values", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize, Deserialize)]
#[serde(transparent)]
pub struct ZOrder(i64);

impl ZOrder {
    #[must_use]
    pub const fn new(value: i64) -> Self {
        Self(value)
    }

    #[must_use]
    pub const fn as_i64(self) -> i64 {
        self.0
    }
}

impl fmt::Debug for ZOrder {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("ZOrder(<redacted>)")
    }
}
