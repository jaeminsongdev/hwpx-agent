use std::fmt;

use serde::de::{self, MapAccess, Visitor};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::LogicalId;

pub const OBJECT_APPEARANCE_SCHEMA_VERSION: &str = "hwpx-agent.object-appearance/v1";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ObjectAppearanceLimitConfig {
    pub input_bytes: usize,
    pub output_bytes: usize,
    pub gradient_colors: usize,
    pub color_transforms: usize,
    pub identifier_bytes: usize,
    pub line_width_hwpunit: u32,
    pub offset_magnitude_hwpunit: i32,
    pub scalar_magnitude_millionths: i64,
}

impl Default for ObjectAppearanceLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 512 * 1024,
            output_bytes: 512 * 1024,
            gradient_colors: 256,
            color_transforms: 64,
            identifier_bytes: 255,
            line_width_hwpunit: 10_000_000,
            offset_magnitude_hwpunit: 1_000_000_000,
            scalar_magnitude_millionths: 1_000_000_000_000,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ObjectAppearanceLimits(ObjectAppearanceLimitConfig);

impl ObjectAppearanceLimits {
    pub const HARD_MAX_INPUT_BYTES: usize = 4 * 1024 * 1024;
    pub const HARD_MAX_OUTPUT_BYTES: usize = 4 * 1024 * 1024;
    pub const HARD_MAX_GRADIENT_COLORS: usize = 4_096;
    pub const HARD_MAX_COLOR_TRANSFORMS: usize = 1_024;
    pub const HARD_MAX_IDENTIFIER_BYTES: usize = 4_096;
    pub const HARD_MAX_LINE_WIDTH_HWPUNIT: u32 = 100_000_000;
    pub const HARD_MAX_OFFSET_MAGNITUDE_HWPUNIT: i32 = 1_000_000_000;
    pub const HARD_MAX_SCALAR_MAGNITUDE_MILLIONTHS: i64 = 1_000_000_000_000;

    /// Creates finite appearance limits without silently clamping caller values.
    ///
    /// # Errors
    ///
    /// Rejects zero, inconsistent or hard-ceiling-exceeding values.
    pub fn new(config: ObjectAppearanceLimitConfig) -> Result<Self, ObjectAppearanceError> {
        if config.input_bytes == 0
            || config.input_bytes > Self::HARD_MAX_INPUT_BYTES
            || config.output_bytes == 0
            || config.output_bytes > Self::HARD_MAX_OUTPUT_BYTES
            || config.input_bytes > config.output_bytes
            || config.gradient_colors < 2
            || config.gradient_colors > Self::HARD_MAX_GRADIENT_COLORS
            || config.color_transforms == 0
            || config.color_transforms > Self::HARD_MAX_COLOR_TRANSFORMS
            || config.identifier_bytes == 0
            || config.identifier_bytes > Self::HARD_MAX_IDENTIFIER_BYTES
            || config.line_width_hwpunit == 0
            || config.line_width_hwpunit > Self::HARD_MAX_LINE_WIDTH_HWPUNIT
            || config.offset_magnitude_hwpunit <= 0
            || config.offset_magnitude_hwpunit > Self::HARD_MAX_OFFSET_MAGNITUDE_HWPUNIT
            || config.scalar_magnitude_millionths <= 0
            || config.scalar_magnitude_millionths > Self::HARD_MAX_SCALAR_MAGNITUDE_MILLIONTHS
        {
            return Err(ObjectAppearanceError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> ObjectAppearanceLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct RgbColor {
    pub red: u8,
    pub green: u8,
    pub blue: u8,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(transparent)]
pub struct UnitFraction(pub u32);

impl UnitFraction {
    pub const MAX: u32 = 1_000_000;

    /// Creates an exact 0..1 value represented in millionths.
    ///
    /// # Errors
    ///
    /// Rejects values greater than one million.
    pub const fn new(millionths: u32) -> Result<Self, ObjectAppearanceError> {
        if millionths > Self::MAX {
            return Err(ObjectAppearanceError::InvalidAlpha);
        }
        Ok(Self(millionths))
    }

    #[must_use]
    pub const fn millionths(self) -> u32 {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(transparent)]
pub struct EffectScalar(pub i64);

impl EffectScalar {
    #[must_use]
    pub const fn millionths(self) -> i64 {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum LinePattern {
    None,
    Solid,
    Dot,
    Dash,
    DashDot,
    DashDotDot,
    LongDash,
    Circle,
    DoubleSlim,
    SlimThick,
    ThickSlim,
    SlimThickSlim,
    Wave,
    DoubleWave,
    Thick3d,
    ThickReverse3d,
    ThreeD,
    Reverse3d,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum LineEndCap {
    Round,
    Flat,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ArrowStyle {
    Normal,
    Arrow,
    Spear,
    ConcaveArrow,
    EmptyDiamond,
    EmptyCircle,
    EmptyBox,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ArrowSize {
    SmallSmall,
    SmallMedium,
    SmallLarge,
    MediumSmall,
    MediumMedium,
    MediumLarge,
    LargeSmall,
    LargeMedium,
    LargeLarge,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum OutlineStyle {
    Normal,
    Outer,
    Inner,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct LineAppearance {
    pub color: RgbColor,
    pub width_hwpunit: u32,
    pub pattern: LinePattern,
    pub end_cap: LineEndCap,
    pub head_style: ArrowStyle,
    pub tail_style: ArrowStyle,
    pub head_filled: bool,
    pub tail_filled: bool,
    pub head_size: ArrowSize,
    pub tail_size: ArrowSize,
    pub outline_style: OutlineStyle,
    pub alpha: UnitFraction,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum HatchStyle {
    Horizontal,
    Vertical,
    BackSlash,
    Slash,
    Cross,
    CrossDiagonal,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum GradientType {
    Linear,
    Radial,
    Conical,
    Square,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct GradientFill {
    pub gradient_type: GradientType,
    pub angle_degrees: i32,
    pub center_x_percent: i32,
    pub center_y_percent: i32,
    pub step_percent: i32,
    pub step_center_percent: i32,
    pub colors: Vec<RgbColor>,
    pub alpha: UnitFraction,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ImageFillMode {
    Tile,
    TileHorizontalTop,
    TileHorizontalBottom,
    TileVerticalLeft,
    TileVerticalRight,
    Total,
    Center,
    CenterTop,
    CenterBottom,
    LeftCenter,
    LeftTop,
    LeftBottom,
    RightCenter,
    RightTop,
    RightBottom,
    Zoom,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ImageEffect {
    RealPicture,
    GrayScale,
    BlackWhite,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ImageFill {
    pub mode: ImageFillMode,
    pub binary_item_id_ref: String,
    pub brightness: i32,
    pub contrast: i32,
    pub effect: ImageEffect,
    pub alpha: UnitFraction,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum FillAppearance {
    Solid {
        color: RgbColor,
        alpha: UnitFraction,
    },
    Pattern {
        face_color: RgbColor,
        hatch_color: RgbColor,
        hatch_style: HatchStyle,
        alpha: UnitFraction,
    },
    Gradient {
        gradient: GradientFill,
    },
    Image {
        image: ImageFill,
    },
}

impl FillAppearance {
    #[must_use]
    pub const fn alpha(&self) -> UnitFraction {
        match self {
            Self::Solid { alpha, .. } | Self::Pattern { alpha, .. } => *alpha,
            Self::Gradient { gradient } => gradient.alpha,
            Self::Image { image } => image.alpha,
        }
    }

    fn set_alpha(&mut self, alpha: UnitFraction) {
        match self {
            Self::Solid { alpha: value, .. } | Self::Pattern { alpha: value, .. } => {
                *value = alpha;
            }
            Self::Gradient { gradient } => gradient.alpha = alpha,
            Self::Image { image } => image.alpha = alpha,
        }
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ClassicShadowType {
    ParallelLeftTop,
    ParallelRightTop,
    ParallelLeftBottom,
    ParallelRightBottom,
    ShearLeftTop,
    ShearRightTop,
    ShearLeftBottom,
    ShearRightBottom,
    PerspectiveLeftTop,
    PerspectiveRightTop,
    PerspectiveLeftBottom,
    PerspectiveRightBottom,
    ScaleNarrow,
    ScaleEnlarge,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ClassicShadow {
    pub shadow_type: ClassicShadowType,
    pub color: RgbColor,
    pub offset_x_hwpunit: i32,
    pub offset_y_hwpunit: i32,
    pub alpha: UnitFraction,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ColorTransformKind {
    Alpha,
    AlphaMod,
    AlphaOff,
    Red,
    RedMod,
    RedOff,
    Green,
    GreenMod,
    GreenOff,
    Blue,
    BlueMod,
    BlueOff,
    Hue,
    HueMod,
    HueOff,
    Saturation,
    SaturationMod,
    SaturationOff,
    Luminance,
    LuminanceMod,
    LuminanceOff,
    Shade,
    Tint,
    Gray,
    Complement,
    Gamma,
    InverseGamma,
    Inverse,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ColorTransform {
    pub kind: ColorTransformKind,
    pub value: EffectScalar,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct EffectColor {
    pub rgb: RgbColor,
    pub transforms: Vec<ColorTransform>,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ScalarPair {
    pub x: EffectScalar,
    pub y: EffectScalar,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct UnitRange {
    pub start: UnitFraction,
    pub end: UnitFraction,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum PictureShadowStyle {
    Outside,
    Inside,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum AlignStyle {
    TopLeft,
    Top,
    TopRight,
    Left,
    Center,
    Right,
    BottomLeft,
    Bottom,
    BottomRight,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct PictureShadow {
    pub style: PictureShadowStyle,
    pub alpha: UnitFraction,
    pub radius: EffectScalar,
    pub direction: EffectScalar,
    pub distance: EffectScalar,
    pub align_style: AlignStyle,
    pub rotation_style: bool,
    pub skew: ScalarPair,
    pub scale: ScalarPair,
    pub color: EffectColor,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct GlowEffect {
    pub alpha: UnitFraction,
    pub radius: EffectScalar,
    pub color: EffectColor,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SoftEdgeEffect {
    pub radius: EffectScalar,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ReflectionEffect {
    pub align_style: AlignStyle,
    pub radius: EffectScalar,
    pub direction: EffectScalar,
    pub distance: EffectScalar,
    pub rotation_style: bool,
    pub fade_direction: EffectScalar,
    pub skew: ScalarPair,
    pub scale: ScalarPair,
    pub alpha: UnitRange,
    pub position: UnitRange,
}

#[derive(Clone, Default, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct PictureEffects {
    pub shadow: Option<PictureShadow>,
    pub glow: Option<GlowEffect>,
    pub soft_edge: Option<SoftEdgeEffect>,
    pub reflection: Option<ReflectionEffect>,
}

impl fmt::Debug for PictureEffects {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("PictureEffects")
            .field("shadow", &self.shadow.is_some())
            .field("glow", &self.glow.is_some())
            .field("soft_edge", &self.soft_edge.is_some())
            .field("reflection", &self.reflection.is_some())
            .field("values", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ImageAdjustment {
    pub brightness: i32,
    pub contrast: i32,
    pub effect: ImageEffect,
    pub alpha: UnitFraction,
}

#[derive(Clone, Default, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ObjectAppearance {
    pub line: Option<LineAppearance>,
    pub fill: Option<FillAppearance>,
    pub shadow: Option<ClassicShadow>,
    pub picture_effects: Option<PictureEffects>,
    pub image_adjustment: Option<ImageAdjustment>,
}

impl ObjectAppearance {
    /// Validates every active appearance field for the selected native object family.
    ///
    /// # Errors
    ///
    /// Rejects family, resource, range, cardinality and effect-color violations.
    pub fn validate(
        &self,
        target_kind: AppearanceTargetKind,
        limits: ObjectAppearanceLimits,
    ) -> Result<(), ObjectAppearanceError> {
        match target_kind {
            AppearanceTargetKind::BasicShape => {
                if self.picture_effects.is_some() || self.image_adjustment.is_some() {
                    return Err(ObjectAppearanceError::KindMismatch);
                }
            }
            AppearanceTargetKind::Picture => {
                if self.fill.is_some() || self.shadow.is_some() {
                    return Err(ObjectAppearanceError::KindMismatch);
                }
            }
        }
        if let Some(line) = &self.line {
            if line.width_hwpunit == 0 || line.width_hwpunit > limits.0.line_width_hwpunit {
                return Err(ObjectAppearanceError::InvalidLine);
            }
            validate_fraction(line.alpha)?;
        }
        if let Some(fill) = &self.fill {
            validate_fill(fill, limits)?;
        }
        if let Some(shadow) = &self.shadow {
            validate_offset(shadow.offset_x_hwpunit, limits)?;
            validate_offset(shadow.offset_y_hwpunit, limits)?;
            validate_fraction(shadow.alpha)?;
        }
        if let Some(effects) = &self.picture_effects {
            if effects == &PictureEffects::default() {
                return Err(ObjectAppearanceError::InvalidEffect);
            }
            validate_picture_effects(effects, limits)?;
        }
        if let Some(adjustment) = self.image_adjustment {
            if !(-100..=100).contains(&adjustment.brightness)
                || !(-100..=100).contains(&adjustment.contrast)
            {
                return Err(ObjectAppearanceError::InvalidImageAdjustment);
            }
            validate_fraction(adjustment.alpha)?;
        }
        Ok(())
    }
}

impl fmt::Debug for ObjectAppearance {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectAppearance")
            .field("line", &self.line.is_some())
            .field("fill", &self.fill.as_ref().map(fill_kind))
            .field("shadow", &self.shadow.is_some())
            .field("picture_effects", &self.picture_effects.is_some())
            .field("image_adjustment", &self.image_adjustment.is_some())
            .field("values", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum AppearanceTargetKind {
    BasicShape,
    Picture,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TransparencyChannel {
    Line,
    Fill,
    ShapeShadow,
    Image,
    PictureShadow,
    Glow,
    Reflection,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum AppearanceOperation {
    SetLine,
    SetSolidFill,
    SetGradientFill,
    SetPatternFill,
    SetImageFill,
    SetShapeShadow,
    SetPictureShadow,
    SetReflection,
    SetGlow,
    SetSoftEdge,
    SetTransparency { channel: TransparencyChannel },
    SetColorAdjust,
}

impl AppearanceOperation {
    #[must_use]
    pub const fn capability_id(self) -> &'static str {
        match self {
            Self::SetLine => "obj.line_style",
            Self::SetSolidFill => "obj.fill_solid",
            Self::SetGradientFill => "obj.fill_gradient",
            Self::SetPatternFill => "obj.fill_pattern",
            Self::SetImageFill => "obj.fill_image",
            Self::SetShapeShadow | Self::SetPictureShadow => "obj.shadow",
            Self::SetReflection => "obj.reflection",
            Self::SetGlow => "obj.glow",
            Self::SetSoftEdge => "obj.soft_edge",
            Self::SetTransparency { .. } => "obj.transparency",
            Self::SetColorAdjust => "obj.color_adjust",
        }
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ObjectAppearanceRequestDraft {
    pub schema_version: String,
    pub request_id: LogicalId,
    pub logical_object_id: LogicalId,
    pub native_object_id: u32,
    pub native_instance_id: u32,
    pub expected_document_flow_sha256: String,
    pub target_document_flow_sha256: String,
    pub target_kind: AppearanceTargetKind,
    pub operation: AppearanceOperation,
    pub source: ObjectAppearance,
    pub target: ObjectAppearance,
}

impl fmt::Debug for ObjectAppearanceRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectAppearanceRequestDraft")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.operation.capability_id())
            .field("identity", &"<redacted>")
            .field("state", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ObjectAppearanceRequest {
    schema_version: &'static str,
    request_id: LogicalId,
    logical_object_id: LogicalId,
    native_object_id: u32,
    native_instance_id: u32,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    target_kind: AppearanceTargetKind,
    operation: AppearanceOperation,
    source: ObjectAppearance,
    target: ObjectAppearance,
}

impl ObjectAppearanceRequest {
    /// Validates an exact one-operation state transition at the current document flow.
    ///
    /// # Errors
    ///
    /// Rejects schema, ID, flow, appearance or operation-delta drift.
    pub fn from_draft(
        draft: ObjectAppearanceRequestDraft,
        current_document_flow_sha256: &str,
        limits: ObjectAppearanceLimits,
    ) -> Result<Self, ObjectAppearanceError> {
        if draft.schema_version != OBJECT_APPEARANCE_SCHEMA_VERSION {
            return Err(ObjectAppearanceError::UnsupportedVersion);
        }
        require_digest(&draft.expected_document_flow_sha256)?;
        require_digest(&draft.target_document_flow_sha256)?;
        require_digest(current_document_flow_sha256)?;
        if draft.expected_document_flow_sha256 != current_document_flow_sha256 {
            return Err(ObjectAppearanceError::FlowDrift);
        }
        if draft.native_object_id == 0 || draft.native_instance_id == 0 {
            return Err(ObjectAppearanceError::InvalidIdentity);
        }
        draft.source.validate(draft.target_kind, limits)?;
        draft.target.validate(draft.target_kind, limits)?;
        validate_operation_delta(
            draft.operation,
            draft.target_kind,
            &draft.source,
            &draft.target,
        )?;
        let request = Self {
            schema_version: OBJECT_APPEARANCE_SCHEMA_VERSION,
            request_id: draft.request_id,
            logical_object_id: draft.logical_object_id,
            native_object_id: draft.native_object_id,
            native_instance_id: draft.native_instance_id,
            expected_document_flow_sha256: draft.expected_document_flow_sha256,
            target_document_flow_sha256: draft.target_document_flow_sha256,
            target_kind: draft.target_kind,
            operation: draft.operation,
            source: draft.source,
            target: draft.target,
        };
        let _ = request.canonical_json(limits)?;
        Ok(request)
    }

    /// Parses strict, bounded and duplicate-key-free JSON.
    ///
    /// # Errors
    ///
    /// Rejects malformed, duplicate, unknown, oversized or semantically invalid input.
    pub fn from_json(
        bytes: &[u8],
        current_document_flow_sha256: &str,
        limits: ObjectAppearanceLimits,
    ) -> Result<Self, ObjectAppearanceError> {
        if bytes.is_empty() || bytes.len() > limits.0.input_bytes {
            return Err(ObjectAppearanceError::InputLimit);
        }
        reject_duplicate_json_keys(bytes)?;
        let draft =
            serde_json::from_slice(bytes).map_err(|_| ObjectAppearanceError::InvalidJson)?;
        Self::from_draft(draft, current_document_flow_sha256, limits)
    }

    #[must_use]
    pub const fn target_kind(&self) -> AppearanceTargetKind {
        self.target_kind
    }

    #[must_use]
    pub const fn operation(&self) -> AppearanceOperation {
        self.operation
    }

    #[must_use]
    pub const fn native_object_id(&self) -> u32 {
        self.native_object_id
    }

    #[must_use]
    pub const fn native_instance_id(&self) -> u32 {
        self.native_instance_id
    }

    #[must_use]
    pub fn logical_object_id(&self) -> &LogicalId {
        &self.logical_object_id
    }

    #[must_use]
    pub const fn source(&self) -> &ObjectAppearance {
        &self.source
    }

    #[must_use]
    pub const fn target(&self) -> &ObjectAppearance {
        &self.target
    }

    #[must_use]
    pub fn target_document_flow_sha256(&self) -> &str {
        &self.target_document_flow_sha256
    }

    /// Serializes the complete request deterministically within the configured bound.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit error.
    pub fn canonical_json(
        &self,
        limits: ObjectAppearanceLimits,
    ) -> Result<Vec<u8>, ObjectAppearanceError> {
        serialize_bounded(self, limits)
    }
}

impl fmt::Debug for ObjectAppearanceRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectAppearanceRequest")
            .field("capability_id", &self.operation.capability_id())
            .field("target_kind", &self.target_kind)
            .field("identity", &"<redacted>")
            .field("state", &"<redacted>")
            .field("flow", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ObjectAppearancePlan {
    schema_version: &'static str,
    capability_id: &'static str,
    request_id: LogicalId,
    logical_object_id: LogicalId,
    native_object_id: u32,
    native_instance_id: u32,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    target_kind: AppearanceTargetKind,
    operation: AppearanceOperation,
    source: ObjectAppearance,
    target: ObjectAppearance,
    source_appearance_sha256: String,
    target_appearance_sha256: String,
    request_sha256: String,
    plan_sha256: String,
}

impl ObjectAppearancePlan {
    #[must_use]
    pub const fn target_kind(&self) -> AppearanceTargetKind {
        self.target_kind
    }

    #[must_use]
    pub const fn operation(&self) -> AppearanceOperation {
        self.operation
    }

    #[must_use]
    pub const fn native_object_id(&self) -> u32 {
        self.native_object_id
    }

    #[must_use]
    pub const fn native_instance_id(&self) -> u32 {
        self.native_instance_id
    }

    #[must_use]
    pub fn logical_object_id(&self) -> &LogicalId {
        &self.logical_object_id
    }

    #[must_use]
    pub const fn source(&self) -> &ObjectAppearance {
        &self.source
    }

    #[must_use]
    pub const fn target(&self) -> &ObjectAppearance {
        &self.target
    }

    #[must_use]
    pub fn source_document_flow_sha256(&self) -> &str {
        &self.source_document_flow_sha256
    }

    #[must_use]
    pub fn target_document_flow_sha256(&self) -> &str {
        &self.target_document_flow_sha256
    }

    #[must_use]
    pub fn plan_sha256(&self) -> &str {
        &self.plan_sha256
    }

    /// Serializes the complete plan deterministically within the configured bound.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit error.
    pub fn canonical_json(
        &self,
        limits: ObjectAppearanceLimits,
    ) -> Result<Vec<u8>, ObjectAppearanceError> {
        serialize_bounded(self, limits)
    }
}

impl fmt::Debug for ObjectAppearancePlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectAppearancePlan")
            .field("capability_id", &self.capability_id)
            .field("target_kind", &self.target_kind)
            .field("identity", &"<redacted>")
            .field("state", &"<redacted>")
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ObjectAppearanceReceipt {
    schema_version: &'static str,
    capability_id: &'static str,
    plan_sha256: String,
    target_document_flow_sha256: String,
    source_appearance_sha256: String,
    target_appearance_sha256: String,
}

impl ObjectAppearanceReceipt {
    #[must_use]
    pub fn plan_sha256(&self) -> &str {
        &self.plan_sha256
    }
}

impl fmt::Debug for ObjectAppearanceReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectAppearanceReceipt")
            .field("capability_id", &self.capability_id)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct ObjectAppearanceResult {
    target: ObjectAppearance,
    receipt: ObjectAppearanceReceipt,
}

impl ObjectAppearanceResult {
    #[must_use]
    pub const fn target(&self) -> &ObjectAppearance {
        &self.target
    }

    #[must_use]
    pub const fn receipt(&self) -> &ObjectAppearanceReceipt {
        &self.receipt
    }
}

impl fmt::Debug for ObjectAppearanceResult {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectAppearanceResult")
            .field("target", &"<redacted>")
            .field("receipt", &self.receipt)
            .finish_non_exhaustive()
    }
}

#[derive(Serialize)]
struct PlanBinding<'a> {
    schema_version: &'static str,
    capability_id: &'static str,
    request_id: &'a LogicalId,
    logical_object_id: &'a LogicalId,
    native_object_id: u32,
    native_instance_id: u32,
    source_document_flow_sha256: &'a str,
    target_document_flow_sha256: &'a str,
    target_kind: AppearanceTargetKind,
    operation: AppearanceOperation,
    source_appearance_sha256: &'a str,
    target_appearance_sha256: &'a str,
    request_sha256: &'a str,
}

#[derive(Debug)]
pub struct ObjectAppearanceBuilder;

impl ObjectAppearanceBuilder {
    /// Creates a deterministic appearance transition plan bound to the current flow.
    ///
    /// # Errors
    ///
    /// Rejects request, state, operation-delta, flow or serialization drift.
    pub fn plan(
        request: &ObjectAppearanceRequest,
        current_document_flow_sha256: &str,
        limits: ObjectAppearanceLimits,
    ) -> Result<ObjectAppearancePlan, ObjectAppearanceError> {
        require_digest(current_document_flow_sha256)?;
        if request.expected_document_flow_sha256 != current_document_flow_sha256 {
            return Err(ObjectAppearanceError::FlowDrift);
        }
        request.source.validate(request.target_kind, limits)?;
        request.target.validate(request.target_kind, limits)?;
        validate_operation_delta(
            request.operation,
            request.target_kind,
            &request.source,
            &request.target,
        )?;
        let request_sha256 = hex(Sha256::digest(request.canonical_json(limits)?).into());
        let source_appearance_sha256 = appearance_sha256(&request.source, limits)?;
        let target_appearance_sha256 = appearance_sha256(&request.target, limits)?;
        let binding = PlanBinding {
            schema_version: OBJECT_APPEARANCE_SCHEMA_VERSION,
            capability_id: request.operation.capability_id(),
            request_id: &request.request_id,
            logical_object_id: &request.logical_object_id,
            native_object_id: request.native_object_id,
            native_instance_id: request.native_instance_id,
            source_document_flow_sha256: current_document_flow_sha256,
            target_document_flow_sha256: &request.target_document_flow_sha256,
            target_kind: request.target_kind,
            operation: request.operation,
            source_appearance_sha256: &source_appearance_sha256,
            target_appearance_sha256: &target_appearance_sha256,
            request_sha256: &request_sha256,
        };
        let plan_sha256 = hex(Sha256::digest(serialize_bounded(&binding, limits)?).into());
        let plan = ObjectAppearancePlan {
            schema_version: OBJECT_APPEARANCE_SCHEMA_VERSION,
            capability_id: request.operation.capability_id(),
            request_id: request.request_id.clone(),
            logical_object_id: request.logical_object_id.clone(),
            native_object_id: request.native_object_id,
            native_instance_id: request.native_instance_id,
            source_document_flow_sha256: current_document_flow_sha256.to_owned(),
            target_document_flow_sha256: request.target_document_flow_sha256.clone(),
            target_kind: request.target_kind,
            operation: request.operation,
            source: request.source.clone(),
            target: request.target.clone(),
            source_appearance_sha256,
            target_appearance_sha256,
            request_sha256,
            plan_sha256,
        };
        let _ = plan.canonical_json(limits)?;
        Ok(plan)
    }

    /// Revalidates every plan binding before publishing the target appearance state.
    ///
    /// # Errors
    ///
    /// Rejects tampered plans and current-flow drift.
    pub fn build(
        plan: &ObjectAppearancePlan,
        current_document_flow_sha256: &str,
        limits: ObjectAppearanceLimits,
    ) -> Result<ObjectAppearanceResult, ObjectAppearanceError> {
        require_digest(current_document_flow_sha256)?;
        if plan.schema_version != OBJECT_APPEARANCE_SCHEMA_VERSION
            || plan.source_document_flow_sha256 != current_document_flow_sha256
            || plan.capability_id != plan.operation.capability_id()
            || plan.native_object_id == 0
            || plan.native_instance_id == 0
        {
            return Err(ObjectAppearanceError::BuildDrift);
        }
        plan.source.validate(plan.target_kind, limits)?;
        plan.target.validate(plan.target_kind, limits)?;
        validate_operation_delta(plan.operation, plan.target_kind, &plan.source, &plan.target)?;
        let source_appearance_sha256 = appearance_sha256(&plan.source, limits)?;
        let target_appearance_sha256 = appearance_sha256(&plan.target, limits)?;
        if source_appearance_sha256 != plan.source_appearance_sha256
            || target_appearance_sha256 != plan.target_appearance_sha256
        {
            return Err(ObjectAppearanceError::BuildDrift);
        }
        let binding = PlanBinding {
            schema_version: OBJECT_APPEARANCE_SCHEMA_VERSION,
            capability_id: plan.capability_id,
            request_id: &plan.request_id,
            logical_object_id: &plan.logical_object_id,
            native_object_id: plan.native_object_id,
            native_instance_id: plan.native_instance_id,
            source_document_flow_sha256: &plan.source_document_flow_sha256,
            target_document_flow_sha256: &plan.target_document_flow_sha256,
            target_kind: plan.target_kind,
            operation: plan.operation,
            source_appearance_sha256: &plan.source_appearance_sha256,
            target_appearance_sha256: &plan.target_appearance_sha256,
            request_sha256: &plan.request_sha256,
        };
        if hex(Sha256::digest(serialize_bounded(&binding, limits)?).into()) != plan.plan_sha256 {
            return Err(ObjectAppearanceError::BuildDrift);
        }
        Ok(ObjectAppearanceResult {
            target: plan.target.clone(),
            receipt: ObjectAppearanceReceipt {
                schema_version: OBJECT_APPEARANCE_SCHEMA_VERSION,
                capability_id: plan.capability_id,
                plan_sha256: plan.plan_sha256.clone(),
                target_document_flow_sha256: plan.target_document_flow_sha256.clone(),
                source_appearance_sha256,
                target_appearance_sha256,
            },
        })
    }
}

#[derive(Debug, Error)]
pub enum ObjectAppearanceError {
    #[error("object-appearance limit configuration is invalid")]
    InvalidLimit,
    #[error("object-appearance schema version is unsupported")]
    UnsupportedVersion,
    #[error("object-appearance JSON is malformed")]
    InvalidJson,
    #[error("object-appearance JSON contains a duplicate key")]
    DuplicateJsonKey,
    #[error("object-appearance input limit was exceeded")]
    InputLimit,
    #[error("object-appearance output limit was exceeded")]
    OutputLimit,
    #[error("object-appearance digest is malformed")]
    InvalidDigest,
    #[error("object-appearance document flow drifted")]
    FlowDrift,
    #[error("object-appearance target identity is invalid")]
    InvalidIdentity,
    #[error("object-appearance state does not match the object family")]
    KindMismatch,
    #[error("object-appearance line state is invalid")]
    InvalidLine,
    #[error("object-appearance fill state is invalid")]
    InvalidFill,
    #[error("object-appearance alpha state is invalid")]
    InvalidAlpha,
    #[error("object-appearance offset state is invalid")]
    InvalidOffset,
    #[error("object-appearance effect state is invalid")]
    InvalidEffect,
    #[error("object-appearance image resource is invalid")]
    InvalidResource,
    #[error("object-appearance image adjustment is invalid")]
    InvalidImageAdjustment,
    #[error("object-appearance operation does not describe the exact state delta")]
    InvalidOperationDelta,
    #[error("object-appearance plan drifted before build")]
    BuildDrift,
    #[error("object-appearance serialization failed")]
    Serialization,
}

impl ObjectAppearanceError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "object_appearance_invalid_limit",
            Self::UnsupportedVersion => "object_appearance_unsupported_version",
            Self::InvalidJson => "object_appearance_invalid_json",
            Self::DuplicateJsonKey => "object_appearance_duplicate_json_key",
            Self::InputLimit => "object_appearance_input_limit",
            Self::OutputLimit => "object_appearance_output_limit",
            Self::InvalidDigest => "object_appearance_invalid_digest",
            Self::FlowDrift => "object_appearance_flow_drift",
            Self::InvalidIdentity => "object_appearance_invalid_identity",
            Self::KindMismatch => "object_appearance_kind_mismatch",
            Self::InvalidLine => "object_appearance_invalid_line",
            Self::InvalidFill => "object_appearance_invalid_fill",
            Self::InvalidAlpha => "object_appearance_invalid_alpha",
            Self::InvalidOffset => "object_appearance_invalid_offset",
            Self::InvalidEffect => "object_appearance_invalid_effect",
            Self::InvalidResource => "object_appearance_invalid_resource",
            Self::InvalidImageAdjustment => "object_appearance_invalid_image_adjustment",
            Self::InvalidOperationDelta => "object_appearance_invalid_operation_delta",
            Self::BuildDrift => "object_appearance_build_drift",
            Self::Serialization => "object_appearance_serialization",
        }
    }
}

fn validate_fill(
    fill: &FillAppearance,
    limits: ObjectAppearanceLimits,
) -> Result<(), ObjectAppearanceError> {
    validate_fraction(fill.alpha())?;
    match fill {
        FillAppearance::Solid { .. } | FillAppearance::Pattern { .. } => Ok(()),
        FillAppearance::Gradient { gradient } => {
            if gradient.colors.len() < 2 || gradient.colors.len() > limits.0.gradient_colors {
                return Err(ObjectAppearanceError::InvalidFill);
            }
            if !(-360..=360).contains(&gradient.angle_degrees)
                || !(-100..=100).contains(&gradient.center_x_percent)
                || !(-100..=100).contains(&gradient.center_y_percent)
                || !(0..=100).contains(&gradient.step_percent)
                || !(0..=100).contains(&gradient.step_center_percent)
            {
                return Err(ObjectAppearanceError::InvalidFill);
            }
            Ok(())
        }
        FillAppearance::Image { image } => {
            if image.binary_item_id_ref.is_empty()
                || image.binary_item_id_ref.len() > limits.0.identifier_bytes
                || !image.binary_item_id_ref.is_ascii()
                || image.binary_item_id_ref.bytes().any(|value| {
                    !(value.is_ascii_alphanumeric() || matches!(value, b'_' | b'-' | b'.'))
                })
            {
                return Err(ObjectAppearanceError::InvalidResource);
            }
            if !(-100..=100).contains(&image.brightness) || !(-100..=100).contains(&image.contrast)
            {
                return Err(ObjectAppearanceError::InvalidImageAdjustment);
            }
            Ok(())
        }
    }
}

fn validate_picture_effects(
    effects: &PictureEffects,
    limits: ObjectAppearanceLimits,
) -> Result<(), ObjectAppearanceError> {
    if let Some(shadow) = &effects.shadow {
        validate_fraction(shadow.alpha)?;
        for value in [
            shadow.radius,
            shadow.direction,
            shadow.distance,
            shadow.skew.x,
            shadow.skew.y,
            shadow.scale.x,
            shadow.scale.y,
        ] {
            validate_scalar(value, limits)?;
        }
        validate_effect_color(&shadow.color, limits)?;
    }
    if let Some(glow) = &effects.glow {
        validate_fraction(glow.alpha)?;
        validate_scalar(glow.radius, limits)?;
        validate_effect_color(&glow.color, limits)?;
    }
    if let Some(soft_edge) = effects.soft_edge {
        validate_scalar(soft_edge.radius, limits)?;
        if soft_edge.radius.0 < 0 {
            return Err(ObjectAppearanceError::InvalidEffect);
        }
    }
    if let Some(reflection) = &effects.reflection {
        for value in [
            reflection.radius,
            reflection.direction,
            reflection.distance,
            reflection.fade_direction,
            reflection.skew.x,
            reflection.skew.y,
            reflection.scale.x,
            reflection.scale.y,
        ] {
            validate_scalar(value, limits)?;
        }
        validate_fraction(reflection.alpha.start)?;
        validate_fraction(reflection.alpha.end)?;
        validate_fraction(reflection.position.start)?;
        validate_fraction(reflection.position.end)?;
    }
    Ok(())
}

fn validate_effect_color(
    color: &EffectColor,
    limits: ObjectAppearanceLimits,
) -> Result<(), ObjectAppearanceError> {
    if color.transforms.len() > limits.0.color_transforms {
        return Err(ObjectAppearanceError::InvalidEffect);
    }
    for transform in &color.transforms {
        validate_scalar(transform.value, limits)?;
    }
    Ok(())
}

fn validate_fraction(value: UnitFraction) -> Result<(), ObjectAppearanceError> {
    if value.0 > UnitFraction::MAX {
        return Err(ObjectAppearanceError::InvalidAlpha);
    }
    Ok(())
}

fn validate_scalar(
    value: EffectScalar,
    limits: ObjectAppearanceLimits,
) -> Result<(), ObjectAppearanceError> {
    if value.0.unsigned_abs() > limits.0.scalar_magnitude_millionths.unsigned_abs() {
        return Err(ObjectAppearanceError::InvalidEffect);
    }
    Ok(())
}

fn validate_offset(
    value: i32,
    limits: ObjectAppearanceLimits,
) -> Result<(), ObjectAppearanceError> {
    if value.unsigned_abs() > limits.0.offset_magnitude_hwpunit.unsigned_abs() {
        return Err(ObjectAppearanceError::InvalidOffset);
    }
    Ok(())
}

fn validate_operation_delta(
    operation: AppearanceOperation,
    target_kind: AppearanceTargetKind,
    source: &ObjectAppearance,
    target: &ObjectAppearance,
) -> Result<(), ObjectAppearanceError> {
    if source == target {
        return Err(ObjectAppearanceError::InvalidOperationDelta);
    }
    let matches = match operation {
        AppearanceOperation::SetLine => {
            target.line.is_some() && equal_except(source, target, AppearanceComponent::Line)
        }
        AppearanceOperation::SetSolidFill => {
            matches!(target.fill, Some(FillAppearance::Solid { .. }))
                && equal_except(source, target, AppearanceComponent::Fill)
        }
        AppearanceOperation::SetGradientFill => {
            matches!(target.fill, Some(FillAppearance::Gradient { .. }))
                && equal_except(source, target, AppearanceComponent::Fill)
        }
        AppearanceOperation::SetPatternFill => {
            matches!(target.fill, Some(FillAppearance::Pattern { .. }))
                && equal_except(source, target, AppearanceComponent::Fill)
        }
        AppearanceOperation::SetImageFill => {
            matches!(target.fill, Some(FillAppearance::Image { .. }))
                && equal_except(source, target, AppearanceComponent::Fill)
        }
        AppearanceOperation::SetShapeShadow => {
            target_kind == AppearanceTargetKind::BasicShape
                && target.shadow.is_some()
                && equal_except(source, target, AppearanceComponent::ShapeShadow)
        }
        AppearanceOperation::SetPictureShadow => {
            target_kind == AppearanceTargetKind::Picture
                && target
                    .picture_effects
                    .as_ref()
                    .and_then(|value| value.shadow.as_ref())
                    .is_some()
                && equal_except_picture_effect(source, target, PictureEffectComponent::Shadow)
        }
        AppearanceOperation::SetReflection => {
            target_kind == AppearanceTargetKind::Picture
                && target
                    .picture_effects
                    .as_ref()
                    .and_then(|value| value.reflection.as_ref())
                    .is_some()
                && equal_except_picture_effect(source, target, PictureEffectComponent::Reflection)
        }
        AppearanceOperation::SetGlow => {
            target_kind == AppearanceTargetKind::Picture
                && target
                    .picture_effects
                    .as_ref()
                    .and_then(|value| value.glow.as_ref())
                    .is_some()
                && equal_except_picture_effect(source, target, PictureEffectComponent::Glow)
        }
        AppearanceOperation::SetSoftEdge => {
            target_kind == AppearanceTargetKind::Picture
                && target
                    .picture_effects
                    .as_ref()
                    .and_then(|value| value.soft_edge.as_ref())
                    .is_some()
                && equal_except_picture_effect(source, target, PictureEffectComponent::SoftEdge)
        }
        AppearanceOperation::SetTransparency { channel } => {
            transparency_only(source, target, channel)
        }
        AppearanceOperation::SetColorAdjust => {
            target_kind == AppearanceTargetKind::Picture
                && target.image_adjustment.is_some()
                && equal_except(source, target, AppearanceComponent::ImageAdjustment)
                && match (source.image_adjustment, target.image_adjustment) {
                    (Some(before), Some(after)) => before.alpha == after.alpha,
                    (None, Some(after)) => after.alpha == UnitFraction(0),
                    _ => false,
                }
        }
    };
    if !matches {
        return Err(ObjectAppearanceError::InvalidOperationDelta);
    }
    Ok(())
}

#[derive(Clone, Copy)]
enum AppearanceComponent {
    Line,
    Fill,
    ShapeShadow,
    ImageAdjustment,
}

fn equal_except(
    source: &ObjectAppearance,
    target: &ObjectAppearance,
    component: AppearanceComponent,
) -> bool {
    let mut left = source.clone();
    let mut right = target.clone();
    match component {
        AppearanceComponent::Line => {
            left.line = None;
            right.line = None;
        }
        AppearanceComponent::Fill => {
            left.fill = None;
            right.fill = None;
        }
        AppearanceComponent::ShapeShadow => {
            left.shadow = None;
            right.shadow = None;
        }
        AppearanceComponent::ImageAdjustment => {
            left.image_adjustment = None;
            right.image_adjustment = None;
        }
    }
    left == right
}

#[derive(Clone, Copy)]
enum PictureEffectComponent {
    Shadow,
    Glow,
    SoftEdge,
    Reflection,
}

fn equal_except_picture_effect(
    source: &ObjectAppearance,
    target: &ObjectAppearance,
    component: PictureEffectComponent,
) -> bool {
    let mut left = source.clone();
    let mut right = target.clone();
    let left_effects = left
        .picture_effects
        .get_or_insert_with(PictureEffects::default);
    let right_effects = right
        .picture_effects
        .get_or_insert_with(PictureEffects::default);
    match component {
        PictureEffectComponent::Shadow => {
            left_effects.shadow = None;
            right_effects.shadow = None;
        }
        PictureEffectComponent::Glow => {
            left_effects.glow = None;
            right_effects.glow = None;
        }
        PictureEffectComponent::SoftEdge => {
            left_effects.soft_edge = None;
            right_effects.soft_edge = None;
        }
        PictureEffectComponent::Reflection => {
            left_effects.reflection = None;
            right_effects.reflection = None;
        }
    }
    normalize_effects(&mut left);
    normalize_effects(&mut right);
    left == right
}

fn normalize_effects(appearance: &mut ObjectAppearance) {
    if appearance.picture_effects.as_ref() == Some(&PictureEffects::default()) {
        appearance.picture_effects = None;
    }
}

fn transparency_only(
    source: &ObjectAppearance,
    target: &ObjectAppearance,
    channel: TransparencyChannel,
) -> bool {
    let mut adjusted = target.clone();
    let changed = match channel {
        TransparencyChannel::Line => match (&source.line, &mut adjusted.line) {
            (Some(before), Some(after)) => {
                let changed = before.alpha != after.alpha;
                after.alpha = before.alpha;
                changed
            }
            _ => false,
        },
        TransparencyChannel::Fill => match (&source.fill, &mut adjusted.fill) {
            (Some(before), Some(after)) => {
                let changed = before.alpha() != after.alpha();
                after.set_alpha(before.alpha());
                changed
            }
            _ => false,
        },
        TransparencyChannel::ShapeShadow => match (&source.shadow, &mut adjusted.shadow) {
            (Some(before), Some(after)) => {
                let changed = before.alpha != after.alpha;
                after.alpha = before.alpha;
                changed
            }
            _ => false,
        },
        TransparencyChannel::Image => {
            match (source.image_adjustment, &mut adjusted.image_adjustment) {
                (Some(before), Some(after)) => {
                    let changed = before.alpha != after.alpha;
                    after.alpha = before.alpha;
                    changed
                }
                _ => false,
            }
        }
        TransparencyChannel::PictureShadow => {
            match (
                source
                    .picture_effects
                    .as_ref()
                    .and_then(|value| value.shadow.as_ref()),
                adjusted
                    .picture_effects
                    .as_mut()
                    .and_then(|value| value.shadow.as_mut()),
            ) {
                (Some(before), Some(after)) => {
                    let changed = before.alpha != after.alpha;
                    after.alpha = before.alpha;
                    changed
                }
                _ => false,
            }
        }
        TransparencyChannel::Glow => {
            match (
                source
                    .picture_effects
                    .as_ref()
                    .and_then(|value| value.glow.as_ref()),
                adjusted
                    .picture_effects
                    .as_mut()
                    .and_then(|value| value.glow.as_mut()),
            ) {
                (Some(before), Some(after)) => {
                    let changed = before.alpha != after.alpha;
                    after.alpha = before.alpha;
                    changed
                }
                _ => false,
            }
        }
        TransparencyChannel::Reflection => {
            match (
                source
                    .picture_effects
                    .as_ref()
                    .and_then(|value| value.reflection.as_ref()),
                adjusted
                    .picture_effects
                    .as_mut()
                    .and_then(|value| value.reflection.as_mut()),
            ) {
                (Some(before), Some(after)) => {
                    let changed = before.alpha != after.alpha;
                    after.alpha = before.alpha;
                    changed
                }
                _ => false,
            }
        }
    };
    changed && adjusted == *source
}

fn fill_kind(fill: &FillAppearance) -> &'static str {
    match fill {
        FillAppearance::Solid { .. } => "solid",
        FillAppearance::Pattern { .. } => "pattern",
        FillAppearance::Gradient { .. } => "gradient",
        FillAppearance::Image { .. } => "image",
    }
}

fn appearance_sha256(
    appearance: &ObjectAppearance,
    limits: ObjectAppearanceLimits,
) -> Result<String, ObjectAppearanceError> {
    Ok(hex(
        Sha256::digest(serialize_bounded(appearance, limits)?).into()
    ))
}

fn require_digest(value: &str) -> Result<(), ObjectAppearanceError> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(ObjectAppearanceError::InvalidDigest);
    }
    Ok(())
}

fn serialize_bounded<T: Serialize>(
    value: &T,
    limits: ObjectAppearanceLimits,
) -> Result<Vec<u8>, ObjectAppearanceError> {
    let bytes = serde_json::to_vec(value).map_err(|_| ObjectAppearanceError::Serialization)?;
    if bytes.len() > limits.0.output_bytes {
        return Err(ObjectAppearanceError::OutputLimit);
    }
    Ok(bytes)
}

fn hex(bytes: [u8; 32]) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(64);
    for byte in bytes {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}

fn reject_duplicate_json_keys(bytes: &[u8]) -> Result<(), ObjectAppearanceError> {
    struct DuplicateVisitor;

    impl<'de> Visitor<'de> for DuplicateVisitor {
        type Value = ();

        fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
            formatter.write_str("JSON without duplicate object keys")
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

        fn visit_some<D>(self, deserializer: D) -> Result<Self::Value, D::Error>
        where
            D: serde::Deserializer<'de>,
        {
            deserializer.deserialize_any(DuplicateVisitor)
        }

        fn visit_seq<A>(self, mut sequence: A) -> Result<Self::Value, A::Error>
        where
            A: de::SeqAccess<'de>,
        {
            while sequence.next_element_seed(DuplicateSeed)?.is_some() {}
            Ok(())
        }

        fn visit_map<A>(self, mut map: A) -> Result<Self::Value, A::Error>
        where
            A: MapAccess<'de>,
        {
            let mut keys = std::collections::BTreeSet::new();
            while let Some(key) = map.next_key::<String>()? {
                if !keys.insert(key) {
                    return Err(de::Error::custom("duplicate JSON key"));
                }
                map.next_value_seed(DuplicateSeed)?;
            }
            Ok(())
        }
    }

    struct DuplicateSeed;

    impl<'de> de::DeserializeSeed<'de> for DuplicateSeed {
        type Value = ();

        fn deserialize<D>(self, deserializer: D) -> Result<Self::Value, D::Error>
        where
            D: serde::Deserializer<'de>,
        {
            deserializer.deserialize_any(DuplicateVisitor)
        }
    }

    let mut deserializer = serde_json::Deserializer::from_slice(bytes);
    de::Deserializer::deserialize_any(&mut deserializer, DuplicateVisitor).map_err(|error| {
        if error.to_string().contains("duplicate JSON key") {
            ObjectAppearanceError::DuplicateJsonKey
        } else {
            ObjectAppearanceError::InvalidJson
        }
    })?;
    deserializer
        .end()
        .map_err(|_| ObjectAppearanceError::InvalidJson)
}
