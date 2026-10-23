use domain_ir::{
    AlignStyle, AppearanceOperation, AppearanceTargetKind, ArrowSize, ArrowStyle, ClassicShadow,
    ClassicShadowType, ColorTransform, ColorTransformKind, EffectColor, EffectScalar,
    FillAppearance, GlowEffect, GradientFill, GradientType, ImageAdjustment, ImageEffect,
    ImageFill, ImageFillMode, LineAppearance, LineEndCap, LinePattern, LogicalId,
    OBJECT_APPEARANCE_SCHEMA_VERSION, ObjectAppearance, ObjectAppearanceBuilder,
    ObjectAppearanceLimitConfig, ObjectAppearanceLimits, ObjectAppearanceRequest,
    ObjectAppearanceRequestDraft, ObjectHatchStyle, OutlineStyle, PictureEffects, ReflectionEffect,
    RgbColor, ScalarPair, SoftEdgeEffect, TransparencyChannel, UnitFraction, UnitRange,
};
use hwpx_package::{
    ObjectAppearanceHwpxBuilder, ObjectAppearanceHwpxLimits, ObjectAppearanceHwpxLowerer,
    ObjectAppearanceHwpxLoweringReceipt, ObjectAppearanceHwpxReader,
};

use super::common::{
    AnyError, FLOW_AFTER, FLOW_BEFORE, LoweringEvidence, PreparedCase, hex, package_with_section,
    prepared_from_section, section_from_package,
};

const SHAPE_ID: u32 = 8_101;
const SHAPE_INSTANCE_ID: u32 = 18_101;
const PICTURE_ID: u32 = 8_102;
const PICTURE_INSTANCE_ID: u32 = 18_102;

#[allow(clippy::too_many_lines)] // One ordered table keeps all eleven appearance rows auditable.
pub fn cases(shape_package: &[u8], image_package: &[u8]) -> Result<Vec<PreparedCase>, AnyError> {
    let mut cases = Vec::with_capacity(11);
    cases.push(shape_case(
        shape_package,
        "P08-19-C11",
        "OBJ-020",
        "obj-020-line-style.hwpx",
        AppearanceOperation::SetLine,
        |target| {
            target.line = Some(line()?);
            Ok(())
        },
    )?);
    cases.push(shape_case(
        shape_package,
        "P08-19-C12",
        "OBJ-021",
        "obj-021-fill-solid.hwpx",
        AppearanceOperation::SetSolidFill,
        |target| {
            target.fill = Some(FillAppearance::Solid {
                color: color(42, 125, 220),
                alpha: fraction(200_000)?,
            });
            Ok(())
        },
    )?);
    cases.push(shape_case(
        shape_package,
        "P08-19-C13",
        "OBJ-022",
        "obj-022-fill-gradient.hwpx",
        AppearanceOperation::SetGradientFill,
        |target| {
            target.fill = Some(FillAppearance::Gradient {
                gradient: GradientFill {
                    gradient_type: GradientType::Linear,
                    angle_degrees: 45,
                    center_x_percent: 0,
                    center_y_percent: 0,
                    step_percent: 25,
                    step_center_percent: 50,
                    colors: vec![color(30, 90, 200), color(230, 245, 255)],
                    alpha: fraction(200_000)?,
                },
            });
            Ok(())
        },
    )?);
    cases.push(shape_case(
        shape_package,
        "P08-19-C14",
        "OBJ-023",
        "obj-023-fill-pattern.hwpx",
        AppearanceOperation::SetPatternFill,
        |target| {
            target.fill = Some(FillAppearance::Pattern {
                face_color: color(245, 245, 245),
                hatch_color: color(35, 35, 35),
                hatch_style: ObjectHatchStyle::CrossDiagonal,
                alpha: fraction(200_000)?,
            });
            Ok(())
        },
    )?);
    cases.push(image_fill_case(shape_package, image_package)?);
    cases.push(shape_case(
        shape_package,
        "P08-19-C16",
        "OBJ-026",
        "obj-026-shadow.hwpx",
        AppearanceOperation::SetShapeShadow,
        |target| {
            target.shadow = Some(ClassicShadow {
                shadow_type: ClassicShadowType::PerspectiveRightBottom,
                color: color(40, 50, 70),
                offset_x_hwpunit: 600,
                offset_y_hwpunit: 800,
                alpha: fraction(200_000)?,
            });
            Ok(())
        },
    )?);
    cases.push(picture_effect_case(
        image_package,
        "P08-19-C17",
        "OBJ-027",
        "obj-027-reflection.hwpx",
        AppearanceOperation::SetReflection,
        |effects| {
            effects.reflection = Some(reflection()?);
            Ok(())
        },
    )?);
    cases.push(picture_effect_case(
        image_package,
        "P08-19-C18",
        "OBJ-028",
        "obj-028-glow.hwpx",
        AppearanceOperation::SetGlow,
        |effects| {
            effects.glow = Some(glow()?);
            Ok(())
        },
    )?);
    cases.push(picture_effect_case(
        image_package,
        "P08-19-C19",
        "OBJ-029",
        "obj-029-soft-edge.hwpx",
        AppearanceOperation::SetSoftEdge,
        |effects| {
            effects.soft_edge = Some(SoftEdgeEffect {
                radius: EffectScalar(500_000),
            });
            Ok(())
        },
    )?);
    cases.push(transparency_case(shape_package)?);
    cases.push(picture_case(
        image_package,
        "P08-19-C21",
        "OBJ-035",
        "obj-035-color-adjust.hwpx",
        AppearanceOperation::SetColorAdjust,
        |target| {
            target.image_adjustment = Some(ImageAdjustment {
                brightness: -20,
                contrast: 35,
                effect: ImageEffect::GrayScale,
                alpha: fraction(0)?,
            });
            Ok(())
        },
    )?);
    Ok(cases)
}

fn shape_case<F>(
    source_package: &[u8],
    case_id: &str,
    feature_id: &str,
    file: &str,
    operation: AppearanceOperation,
    mutate: F,
) -> Result<PreparedCase, AnyError>
where
    F: FnOnce(&mut ObjectAppearance) -> Result<(), AnyError>,
{
    build_case(
        source_package,
        case_id,
        feature_id,
        file,
        0,
        SHAPE_ID,
        SHAPE_INSTANCE_ID,
        AppearanceTargetKind::BasicShape,
        "rectangle",
        false,
        operation,
        mutate,
    )
}

fn picture_case<F>(
    source_package: &[u8],
    case_id: &str,
    feature_id: &str,
    file: &str,
    operation: AppearanceOperation,
    mutate: F,
) -> Result<PreparedCase, AnyError>
where
    F: FnOnce(&mut ObjectAppearance) -> Result<(), AnyError>,
{
    build_case(
        source_package,
        case_id,
        feature_id,
        file,
        0,
        PICTURE_ID,
        PICTURE_INSTANCE_ID,
        AppearanceTargetKind::Picture,
        "picture",
        true,
        operation,
        mutate,
    )
}

#[allow(clippy::too_many_arguments)]
fn build_case<F>(
    source_package: &[u8],
    case_id: &str,
    feature_id: &str,
    file: &str,
    object_ordinal: usize,
    native_object_id: u32,
    native_instance_id: u32,
    target_kind: AppearanceTargetKind,
    object_kind: &str,
    resource_integrity_expected: bool,
    operation: AppearanceOperation,
    mutate: F,
) -> Result<PreparedCase, AnyError>
where
    F: FnOnce(&mut ObjectAppearance) -> Result<(), AnyError>,
{
    let section = section_from_package(source_package)?;
    let source = read_appearance(
        &section,
        object_ordinal,
        native_object_id,
        native_instance_id,
    )?;
    if source.target_kind != target_kind {
        return Err("appearance target kind drifted".into());
    }
    let mut target = source.appearance.clone();
    mutate(&mut target)?;
    let (output, receipt) = lower(
        &section,
        object_ordinal,
        native_object_id,
        native_instance_id,
        target_kind,
        operation,
        source.appearance,
        target,
    )?;
    if receipt.capability_id != operation.capability_id() {
        return Err("appearance receipt capability drifted".into());
    }
    prepared_from_section(
        case_id,
        feature_id,
        operation.capability_id(),
        file,
        source_package,
        &output,
        vec![evidence(&receipt)],
        object_kind,
        native_object_id,
        native_instance_id,
        resource_integrity_expected,
    )
}

fn image_fill_case(shape_package: &[u8], image_package: &[u8]) -> Result<PreparedCase, AnyError> {
    let shape_section = section_from_package(shape_package)?;
    let image_section = section_from_package(image_package)?;
    let shape_fragment = direct_object_fragment(&shape_section, "<hp:rect ", "</hp:rect>")?;
    let insertion = image_section
        .windows(b"<hp:t/></hp:run></hp:p></hs:sec>".len())
        .rposition(|window| window == b"<hp:t/></hp:run></hp:p></hs:sec>")
        .ok_or("image section target run is missing")?;
    let mut combined_section = Vec::with_capacity(image_section.len() + shape_fragment.len());
    combined_section.extend_from_slice(&image_section[..insertion]);
    combined_section.extend_from_slice(shape_fragment);
    combined_section.extend_from_slice(&image_section[insertion..]);
    let combined_package = package_with_section(image_package, &combined_section)?;
    let resource_id = attribute_value(&image_section, b"binaryItemIDRef=\"")?;
    build_case(
        &combined_package,
        "P08-19-C15",
        "OBJ-024",
        "obj-024-fill-image.hwpx",
        1,
        SHAPE_ID,
        SHAPE_INSTANCE_ID,
        AppearanceTargetKind::BasicShape,
        "rectangle",
        true,
        AppearanceOperation::SetImageFill,
        |target| {
            target.fill = Some(FillAppearance::Image {
                image: ImageFill {
                    mode: ImageFillMode::Zoom,
                    binary_item_id_ref: resource_id,
                    brightness: 10,
                    contrast: 20,
                    effect: ImageEffect::RealPicture,
                    alpha: fraction(200_000)?,
                },
            });
            Ok(())
        },
    )
}

fn picture_effect_case<F>(
    source_package: &[u8],
    case_id: &str,
    feature_id: &str,
    file: &str,
    operation: AppearanceOperation,
    mutate: F,
) -> Result<PreparedCase, AnyError>
where
    F: FnOnce(&mut PictureEffects) -> Result<(), AnyError>,
{
    picture_case(
        source_package,
        case_id,
        feature_id,
        file,
        operation,
        |target| {
            let mut effects = PictureEffects::default();
            mutate(&mut effects)?;
            target.picture_effects = Some(effects);
            Ok(())
        },
    )
}

fn transparency_case(source_package: &[u8]) -> Result<PreparedCase, AnyError> {
    let section = section_from_package(source_package)?;
    let source = read_appearance(&section, 0, SHAPE_ID, SHAPE_INSTANCE_ID)?.appearance;
    let mut lined = source.clone();
    lined.line = Some(line()?);
    let (lined_section, line_receipt) = lower(
        &section,
        0,
        SHAPE_ID,
        SHAPE_INSTANCE_ID,
        AppearanceTargetKind::BasicShape,
        AppearanceOperation::SetLine,
        source,
        lined.clone(),
    )?;
    let mut transparent = lined.clone();
    transparent
        .line
        .as_mut()
        .ok_or("line was not created")?
        .alpha = fraction(800_000)?;
    let (output, transparency_receipt) = lower(
        &lined_section,
        0,
        SHAPE_ID,
        SHAPE_INSTANCE_ID,
        AppearanceTargetKind::BasicShape,
        AppearanceOperation::SetTransparency {
            channel: TransparencyChannel::Line,
        },
        lined,
        transparent,
    )?;
    prepared_from_section(
        "P08-19-C20",
        "OBJ-034",
        "obj.transparency",
        "obj-034-transparency.hwpx",
        source_package,
        &output,
        vec![evidence(&line_receipt), evidence(&transparency_receipt)],
        "rectangle",
        SHAPE_ID,
        SHAPE_INSTANCE_ID,
        false,
    )
}

#[allow(clippy::too_many_arguments)]
pub(super) fn lower(
    section: &[u8],
    object_ordinal: usize,
    native_object_id: u32,
    native_instance_id: u32,
    target_kind: AppearanceTargetKind,
    operation: AppearanceOperation,
    source: ObjectAppearance,
    target: ObjectAppearance,
) -> Result<(Vec<u8>, ObjectAppearanceHwpxLoweringReceipt), AnyError> {
    let appearance_limits = ObjectAppearanceLimits::new(ObjectAppearanceLimitConfig::default())?;
    let request = ObjectAppearanceRequest::from_draft(
        ObjectAppearanceRequestDraft {
            schema_version: OBJECT_APPEARANCE_SCHEMA_VERSION.to_owned(),
            request_id: LogicalId::parse("p08-19-appearance-request")?,
            logical_object_id: LogicalId::parse(format!("object-{native_object_id}"))?,
            native_object_id,
            native_instance_id,
            expected_document_flow_sha256: FLOW_BEFORE.to_owned(),
            target_document_flow_sha256: FLOW_AFTER.to_owned(),
            target_kind,
            operation,
            source,
            target,
        },
        FLOW_BEFORE,
        appearance_limits,
    )?;
    let domain = ObjectAppearanceBuilder::plan(&request, FLOW_BEFORE, appearance_limits)?;
    let plan = ObjectAppearanceHwpxBuilder::plan(
        section,
        object_ordinal,
        &domain,
        FLOW_BEFORE,
        appearance_limits,
        ObjectAppearanceHwpxLimits::default(),
    )?;
    Ok(ObjectAppearanceHwpxLowerer::lower_in_section_with_receipt(
        section,
        &plan,
        FLOW_BEFORE,
        appearance_limits,
        ObjectAppearanceHwpxLimits::default(),
    )?)
}

pub(super) fn read_appearance(
    section: &[u8],
    object_ordinal: usize,
    native_object_id: u32,
    native_instance_id: u32,
) -> Result<hwpx_package::ObjectAppearanceHwpxReadback, AnyError> {
    let appearance_limits = ObjectAppearanceLimits::new(ObjectAppearanceLimitConfig::default())?;
    Ok(ObjectAppearanceHwpxReader::read_in_section(
        section,
        object_ordinal,
        native_object_id,
        native_instance_id,
        appearance_limits,
        ObjectAppearanceHwpxLimits::default(),
    )?)
}

fn line() -> Result<LineAppearance, AnyError> {
    Ok(LineAppearance {
        color: color(20, 60, 160),
        width_hwpunit: 120,
        pattern: LinePattern::DashDot,
        end_cap: LineEndCap::Round,
        head_style: ArrowStyle::Arrow,
        tail_style: ArrowStyle::EmptyDiamond,
        head_filled: true,
        tail_filled: false,
        head_size: ArrowSize::MediumLarge,
        tail_size: ArrowSize::LargeSmall,
        outline_style: OutlineStyle::Outer,
        alpha: fraction(200_000)?,
    })
}

fn reflection() -> Result<ReflectionEffect, AnyError> {
    Ok(ReflectionEffect {
        align_style: AlignStyle::Bottom,
        radius: EffectScalar(250_000),
        direction: EffectScalar(90_000_000),
        distance: EffectScalar(100_000),
        rotation_style: false,
        fade_direction: EffectScalar(90_000_000),
        skew: ScalarPair {
            x: EffectScalar(0),
            y: EffectScalar(0),
        },
        scale: ScalarPair {
            x: EffectScalar(1_000_000),
            y: EffectScalar(1_000_000),
        },
        alpha: UnitRange {
            start: fraction(600_000)?,
            end: fraction(0)?,
        },
        position: UnitRange {
            start: fraction(0)?,
            end: fraction(1_000_000)?,
        },
    })
}

fn glow() -> Result<GlowEffect, AnyError> {
    Ok(GlowEffect {
        alpha: fraction(300_000)?,
        radius: EffectScalar(1_000_000),
        color: EffectColor {
            rgb: color(60, 100, 220),
            transforms: vec![ColorTransform {
                kind: ColorTransformKind::Tint,
                value: EffectScalar(250_000),
            }],
        },
    })
}

fn direct_object_fragment<'a>(
    section: &'a [u8],
    opening: &str,
    closing: &str,
) -> Result<&'a [u8], AnyError> {
    let text = std::str::from_utf8(section)?;
    let start = text
        .find(opening)
        .ok_or("source object opening is missing")?;
    let end = text[start..]
        .find(closing)
        .map(|offset| start + offset + closing.len())
        .ok_or("source object closing is missing")?;
    Ok(&section[start..end])
}

fn attribute_value(section: &[u8], prefix: &[u8]) -> Result<String, AnyError> {
    let start = section
        .windows(prefix.len())
        .position(|window| window == prefix)
        .map(|offset| offset + prefix.len())
        .ok_or("resource attribute is missing")?;
    let end = section[start..]
        .iter()
        .position(|&byte| byte == b'\"')
        .map(|offset| start + offset)
        .ok_or("resource attribute is unterminated")?;
    Ok(std::str::from_utf8(&section[start..end])?.to_owned())
}

pub(super) fn evidence(receipt: &ObjectAppearanceHwpxLoweringReceipt) -> LoweringEvidence {
    LoweringEvidence {
        profile_id: receipt.profile_id.to_owned(),
        capability_id: receipt.capability_id.to_owned(),
        plan_sha256: receipt.plan_sha256.clone(),
        source_section_sha256: hex(receipt.source_section_sha256),
        output_section_sha256: hex(receipt.output_section_sha256),
        modified_unit_count: receipt.modified_region_count,
    }
}

pub(super) const fn color(red: u8, green: u8, blue: u8) -> RgbColor {
    RgbColor { red, green, blue }
}

pub(super) fn fraction(value: u32) -> Result<UnitFraction, AnyError> {
    Ok(UnitFraction::new(value)?)
}
