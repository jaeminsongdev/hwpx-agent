#![allow(clippy::expect_used)] // Test fixtures keep failures local.

use domain_ir::{
    AlignStyle, AppearanceOperation, AppearanceTargetKind, ArrowSize, ArrowStyle, ClassicShadow,
    ClassicShadowType, ColorTransform, ColorTransformKind, EffectColor, EffectScalar,
    FillAppearance, GlowEffect, GradientFill, GradientType, ImageAdjustment, ImageEffect,
    ImageFill, ImageFillMode, LineAppearance, LineEndCap, LinePattern, LogicalId,
    OBJECT_APPEARANCE_SCHEMA_VERSION, ObjectAppearance, ObjectAppearanceBuilder,
    ObjectAppearanceLimitConfig, ObjectAppearanceLimits, ObjectAppearanceRequest,
    ObjectAppearanceRequestDraft, ObjectHatchStyle, OutlineStyle, PictureEffects, PictureShadow,
    PictureShadowStyle, ReflectionEffect, RgbColor, ScalarPair, SoftEdgeEffect,
    TransparencyChannel, UnitFraction, UnitRange,
};
use hwpx_package::{
    ObjectAppearanceHwpxBuilder, ObjectAppearanceHwpxError, ObjectAppearanceHwpxLimitConfig,
    ObjectAppearanceHwpxLimits, ObjectAppearanceHwpxLowerer, ObjectAppearanceHwpxReader,
};

const FLOW_A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const FLOW_B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
const PARA_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const CORE_NS: &str = "http://www.hancom.co.kr/hwpml/2011/core";

fn limits() -> ObjectAppearanceLimits {
    ObjectAppearanceLimits::new(ObjectAppearanceLimitConfig::default()).expect("limits")
}

fn hwpx_limits() -> ObjectAppearanceHwpxLimits {
    ObjectAppearanceHwpxLimits::new(ObjectAppearanceHwpxLimitConfig::default()).expect("limits")
}

fn color(red: u8, green: u8, blue: u8) -> RgbColor {
    RgbColor { red, green, blue }
}

fn alpha(value: u32) -> UnitFraction {
    UnitFraction::new(value).expect("alpha")
}

fn scalar(value: i64) -> EffectScalar {
    EffectScalar(value)
}

fn line() -> LineAppearance {
    LineAppearance {
        color: color(10, 20, 30),
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
        alpha: alpha(200_000),
    }
}

fn default_adjustment() -> ImageAdjustment {
    ImageAdjustment {
        brightness: 0,
        contrast: 0,
        effect: ImageEffect::RealPicture,
        alpha: alpha(0),
    }
}

fn shape_section() -> Vec<u8> {
    format!(
        concat!(
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
            "<hs:sec xmlns:hs=\"urn:test:section\" xmlns:hp=\"{}\" xmlns:hc=\"{}\">",
            "<hp:p><hp:run><hp:rect id=\"41\" instid=\"141\">",
            "<hp:renderingInfo/><hp:sz width=\"100\" height=\"100\"/>",
            "</hp:rect></hp:run></hp:p></hs:sec>"
        ),
        PARA_NS, CORE_NS,
    )
    .into_bytes()
}

fn picture_section() -> Vec<u8> {
    format!(
        concat!(
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
            "<hs:sec xmlns:hs=\"urn:test:section\" xmlns:hp=\"{}\" xmlns:hc=\"{}\">",
            "<hp:p><hp:run><hp:pic id=\"41\" instid=\"141\">",
            "<hp:renderingInfo/><hp:effects/>",
            "<hc:img binaryItemIDRef=\"image-1\" bright=\"0\" contrast=\"0\" effect=\"REAL_PIC\" alpha=\"0\"/>",
            "<hp:sz width=\"100\" height=\"100\"/>",
            "</hp:pic></hp:run></hp:p></hs:sec>"
        ),
        PARA_NS, CORE_NS,
    )
    .into_bytes()
}

fn request(
    kind: AppearanceTargetKind,
    operation: AppearanceOperation,
    source: ObjectAppearance,
    target: ObjectAppearance,
) -> ObjectAppearanceRequest {
    ObjectAppearanceRequest::from_draft(
        ObjectAppearanceRequestDraft {
            schema_version: OBJECT_APPEARANCE_SCHEMA_VERSION.to_owned(),
            request_id: LogicalId::parse("appearance-request").expect("request id"),
            logical_object_id: LogicalId::parse("object-1").expect("object id"),
            native_object_id: 41,
            native_instance_id: 141,
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            target_kind: kind,
            operation,
            source,
            target,
        },
        FLOW_A,
        limits(),
    )
    .expect("request")
}

fn lower(
    section: &[u8],
    request: &ObjectAppearanceRequest,
) -> Result<Vec<u8>, ObjectAppearanceHwpxError> {
    let domain_plan =
        ObjectAppearanceBuilder::plan(request, FLOW_A, limits()).expect("domain plan");
    let plan = ObjectAppearanceHwpxBuilder::plan(
        section,
        0,
        &domain_plan,
        FLOW_A,
        limits(),
        hwpx_limits(),
    )?;
    ObjectAppearanceHwpxLowerer::lower_in_section(section, &plan, FLOW_A, limits(), hwpx_limits())
}

fn effect_color() -> EffectColor {
    EffectColor {
        rgb: color(60, 70, 80),
        transforms: vec![ColorTransform {
            kind: ColorTransformKind::Tint,
            value: scalar(250_000),
        }],
    }
}

fn picture_effects() -> PictureEffects {
    PictureEffects {
        shadow: Some(PictureShadow {
            style: PictureShadowStyle::Outside,
            alpha: alpha(200_000),
            radius: scalar(1_500_000),
            direction: scalar(45_000_000),
            distance: scalar(2_000_000),
            align_style: AlignStyle::BottomRight,
            rotation_style: true,
            skew: ScalarPair {
                x: scalar(0),
                y: scalar(0),
            },
            scale: ScalarPair {
                x: scalar(1_000_000),
                y: scalar(1_000_000),
            },
            color: effect_color(),
        }),
        glow: Some(GlowEffect {
            alpha: alpha(300_000),
            radius: scalar(1_000_000),
            color: effect_color(),
        }),
        soft_edge: Some(SoftEdgeEffect {
            radius: scalar(500_000),
        }),
        reflection: Some(ReflectionEffect {
            align_style: AlignStyle::Bottom,
            radius: scalar(250_000),
            direction: scalar(90_000_000),
            distance: scalar(100_000),
            rotation_style: false,
            fade_direction: scalar(90_000_000),
            skew: ScalarPair {
                x: scalar(0),
                y: scalar(0),
            },
            scale: ScalarPair {
                x: scalar(1_000_000),
                y: scalar(1_000_000),
            },
            alpha: UnitRange {
                start: alpha(600_000),
                end: alpha(0),
            },
            position: UnitRange {
                start: alpha(0),
                end: alpha(1_000_000),
            },
        }),
    }
}

#[test]
#[allow(clippy::too_many_lines)] // One table keeps all six reviewed shape families auditable.
fn lowers_every_shape_appearance_family_with_strict_readback() {
    let targets = [
        (
            AppearanceOperation::SetLine,
            ObjectAppearance {
                line: Some(line()),
                ..ObjectAppearance::default()
            },
        ),
        (
            AppearanceOperation::SetSolidFill,
            ObjectAppearance {
                fill: Some(FillAppearance::Solid {
                    color: color(1, 2, 3),
                    alpha: alpha(0),
                }),
                ..ObjectAppearance::default()
            },
        ),
        (
            AppearanceOperation::SetPatternFill,
            ObjectAppearance {
                fill: Some(FillAppearance::Pattern {
                    face_color: color(1, 2, 3),
                    hatch_color: color(4, 5, 6),
                    hatch_style: ObjectHatchStyle::CrossDiagonal,
                    alpha: alpha(200_000),
                }),
                ..ObjectAppearance::default()
            },
        ),
        (
            AppearanceOperation::SetGradientFill,
            ObjectAppearance {
                fill: Some(FillAppearance::Gradient {
                    gradient: GradientFill {
                        gradient_type: GradientType::Radial,
                        angle_degrees: 360,
                        center_x_percent: -100,
                        center_y_percent: 100,
                        step_percent: 0,
                        step_center_percent: 100,
                        colors: vec![color(0, 0, 0), color(255, 255, 255)],
                        alpha: alpha(1_000_000),
                    },
                }),
                ..ObjectAppearance::default()
            },
        ),
        (
            AppearanceOperation::SetImageFill,
            ObjectAppearance {
                fill: Some(FillAppearance::Image {
                    image: ImageFill {
                        mode: ImageFillMode::Zoom,
                        binary_item_id_ref: "image-1".to_owned(),
                        brightness: -100,
                        contrast: 100,
                        effect: ImageEffect::GrayScale,
                        alpha: alpha(800_000),
                    },
                }),
                ..ObjectAppearance::default()
            },
        ),
        (
            AppearanceOperation::SetShapeShadow,
            ObjectAppearance {
                shadow: Some(ClassicShadow {
                    shadow_type: ClassicShadowType::PerspectiveRightBottom,
                    color: color(9, 8, 7),
                    offset_x_hwpunit: -1_000_000_000,
                    offset_y_hwpunit: 1_000_000_000,
                    alpha: alpha(200_000),
                }),
                ..ObjectAppearance::default()
            },
        ),
    ];
    for (operation, target) in targets {
        let source = shape_section();
        let output = lower(
            &source,
            &request(
                AppearanceTargetKind::BasicShape,
                operation,
                ObjectAppearance::default(),
                target.clone(),
            ),
        )
        .expect("lower");
        let readback = ObjectAppearanceHwpxReader::read_in_section(
            &output,
            0,
            41,
            141,
            limits(),
            hwpx_limits(),
        )
        .expect("readback");
        assert_eq!(readback.appearance, target);
        assert_ne!(source, output);
    }
}

#[test]
fn lowers_all_picture_effects_line_and_color_adjustment() {
    let source_state = ObjectAppearance {
        image_adjustment: Some(default_adjustment()),
        ..ObjectAppearance::default()
    };
    let all = picture_effects();
    let effect_targets = [
        (
            AppearanceOperation::SetPictureShadow,
            PictureEffects {
                shadow: all.shadow.clone(),
                ..PictureEffects::default()
            },
        ),
        (
            AppearanceOperation::SetGlow,
            PictureEffects {
                glow: all.glow.clone(),
                ..PictureEffects::default()
            },
        ),
        (
            AppearanceOperation::SetSoftEdge,
            PictureEffects {
                soft_edge: all.soft_edge,
                ..PictureEffects::default()
            },
        ),
        (
            AppearanceOperation::SetReflection,
            PictureEffects {
                reflection: all.reflection.clone(),
                ..PictureEffects::default()
            },
        ),
    ];
    for (operation, effects) in effect_targets {
        let target = ObjectAppearance {
            picture_effects: Some(effects),
            ..source_state.clone()
        };
        let output = lower(
            &picture_section(),
            &request(
                AppearanceTargetKind::Picture,
                operation,
                source_state.clone(),
                target.clone(),
            ),
        )
        .expect("effect lower");
        assert_eq!(
            ObjectAppearanceHwpxReader::read_in_section(
                &output,
                0,
                41,
                141,
                limits(),
                hwpx_limits(),
            )
            .expect("readback")
            .appearance,
            target
        );
    }

    let line_target = ObjectAppearance {
        line: Some(line()),
        ..source_state.clone()
    };
    lower(
        &picture_section(),
        &request(
            AppearanceTargetKind::Picture,
            AppearanceOperation::SetLine,
            source_state.clone(),
            line_target,
        ),
    )
    .expect("line lower");

    let adjust_target = ObjectAppearance {
        image_adjustment: Some(ImageAdjustment {
            brightness: -25,
            contrast: 75,
            effect: ImageEffect::BlackWhite,
            alpha: alpha(0),
        }),
        ..ObjectAppearance::default()
    };
    lower(
        &picture_section(),
        &request(
            AppearanceTargetKind::Picture,
            AppearanceOperation::SetColorAdjust,
            source_state,
            adjust_target,
        ),
    )
    .expect("adjust lower");
}

#[test]
fn lowers_transparency_from_an_existing_line_and_preserves_other_bytes() {
    let initial = ObjectAppearance {
        line: Some(line()),
        ..ObjectAppearance::default()
    };
    let with_line = lower(
        &shape_section(),
        &request(
            AppearanceTargetKind::BasicShape,
            AppearanceOperation::SetLine,
            ObjectAppearance::default(),
            initial.clone(),
        ),
    )
    .expect("initial line");
    let mut target = initial.clone();
    target.line.as_mut().expect("line").alpha = alpha(800_000);
    let output = lower(
        &with_line,
        &request(
            AppearanceTargetKind::BasicShape,
            AppearanceOperation::SetTransparency {
                channel: TransparencyChannel::Line,
            },
            initial,
            target.clone(),
        ),
    )
    .expect("transparency");
    assert_eq!(
        ObjectAppearanceHwpxReader::read_in_section(&output, 0, 41, 141, limits(), hwpx_limits(),)
            .expect("readback")
            .appearance,
        target
    );
    assert!(
        String::from_utf8(output)
            .expect("utf8")
            .contains("<hp:sz width=\"100\" height=\"100\"/>")
    );
}

#[test]
fn core_alpha_uses_exact_bytes_and_rejects_lossy_values() {
    let target = ObjectAppearance {
        line: Some(line()),
        ..ObjectAppearance::default()
    };
    let encoded = lower(
        &shape_section(),
        &request(
            AppearanceTargetKind::BasicShape,
            AppearanceOperation::SetLine,
            ObjectAppearance::default(),
            target,
        ),
    )
    .expect("byte alpha lower");
    let encoded_text = String::from_utf8(encoded).expect("utf8");
    assert!(encoded_text.contains("alpha=\"51\""));

    let native = encoded_text
        .replacen("alpha=\"51\"", "alpha=\"32\"", 1)
        .into_bytes();
    let native_readback =
        ObjectAppearanceHwpxReader::read_in_section(&native, 0, 41, 141, limits(), hwpx_limits())
            .expect("native byte alpha readback");
    assert_eq!(
        native_readback
            .appearance
            .line
            .as_ref()
            .expect("line")
            .alpha
            .millionths(),
        125_490
    );
    let mut changed = native_readback.appearance.clone();
    changed.line.as_mut().expect("line").color = color(90, 80, 70);
    let rewritten = lower(
        &native,
        &request(
            AppearanceTargetKind::BasicShape,
            AppearanceOperation::SetLine,
            native_readback.appearance,
            changed.clone(),
        ),
    )
    .expect("native byte alpha rewrite");
    assert!(
        String::from_utf8(rewritten.clone())
            .expect("utf8")
            .contains("alpha=\"32\"")
    );
    assert_eq!(
        ObjectAppearanceHwpxReader::read_in_section(
            &rewritten,
            0,
            41,
            141,
            limits(),
            hwpx_limits(),
        )
        .expect("rewritten readback")
        .appearance,
        changed
    );

    let decimal = String::from_utf8(native)
        .expect("utf8")
        .replacen("alpha=\"32\"", "alpha=\"0.2\"", 1)
        .into_bytes();
    assert!(matches!(
        ObjectAppearanceHwpxReader::read_in_section(&decimal, 0, 41, 141, limits(), hwpx_limits(),),
        Err(ObjectAppearanceHwpxError::InvalidNumber)
    ));

    let unrepresentable = ObjectAppearance {
        line: Some(LineAppearance {
            alpha: alpha(125_000),
            ..line()
        }),
        ..ObjectAppearance::default()
    };
    assert!(matches!(
        lower(
            &shape_section(),
            &request(
                AppearanceTargetKind::BasicShape,
                AppearanceOperation::SetLine,
                ObjectAppearance::default(),
                unrepresentable,
            ),
        ),
        Err(ObjectAppearanceHwpxError::InvalidNumber)
    ));
}

#[test]
fn picture_effect_alpha_remains_fractional() {
    let source_state = ObjectAppearance {
        image_adjustment: Some(default_adjustment()),
        ..ObjectAppearance::default()
    };
    let glow_target = ObjectAppearance {
        picture_effects: Some(PictureEffects {
            glow: picture_effects().glow,
            ..PictureEffects::default()
        }),
        ..source_state.clone()
    };
    let glow_output = lower(
        &picture_section(),
        &request(
            AppearanceTargetKind::Picture,
            AppearanceOperation::SetGlow,
            source_state,
            glow_target,
        ),
    )
    .expect("fractional effect alpha lower");
    assert!(
        String::from_utf8(glow_output)
            .expect("utf8")
            .contains("<hp:glow alpha=\"0.3\"")
    );
}

#[test]
fn rejects_source_identity_state_and_flow_drift() {
    let target = ObjectAppearance {
        line: Some(line()),
        ..ObjectAppearance::default()
    };
    let request = request(
        AppearanceTargetKind::BasicShape,
        AppearanceOperation::SetLine,
        ObjectAppearance::default(),
        target,
    );
    let domain_plan = ObjectAppearanceBuilder::plan(&request, FLOW_A, limits()).expect("plan");
    let plan = ObjectAppearanceHwpxBuilder::plan(
        &shape_section(),
        0,
        &domain_plan,
        FLOW_A,
        limits(),
        hwpx_limits(),
    )
    .expect("HWPX plan");
    let mut drift = shape_section();
    drift.push(b' ');
    assert!(matches!(
        ObjectAppearanceHwpxLowerer::lower_in_section(
            &drift,
            &plan,
            FLOW_A,
            limits(),
            hwpx_limits(),
        ),
        Err(ObjectAppearanceHwpxError::SourceDrift)
    ));
    assert!(matches!(
        ObjectAppearanceHwpxLowerer::lower_in_section(
            &shape_section(),
            &plan,
            FLOW_B,
            limits(),
            hwpx_limits(),
        ),
        Err(ObjectAppearanceHwpxError::Domain(_))
    ));
}

#[test]
fn rejects_duplicate_appearance_unknown_attributes_and_unsupported_effect_color() {
    let duplicate = format!(
        concat!(
            "<s xmlns:hp=\"{}\"><hp:p><hp:run><hp:rect id=\"41\" instid=\"141\">",
            "<hp:renderingInfo/><hp:lineShape color=\"#000000\" width=\"1\" style=\"SOLID\" endCap=\"FLAT\" ",
            "headStyle=\"NORMAL\" tailStyle=\"NORMAL\" headfill=\"0\" tailfill=\"0\" headSz=\"SMALL_SMALL\" ",
            "tailSz=\"SMALL_SMALL\" outlineStyle=\"NORMAL\" alpha=\"0\"/><hp:lineShape color=\"#000000\" ",
            "width=\"1\" style=\"SOLID\" endCap=\"FLAT\" headStyle=\"NORMAL\" tailStyle=\"NORMAL\" headfill=\"0\" ",
            "tailfill=\"0\" headSz=\"SMALL_SMALL\" tailSz=\"SMALL_SMALL\" outlineStyle=\"NORMAL\" alpha=\"0\"/>",
            "</hp:rect></hp:run></hp:p></s>"
        ),
        PARA_NS,
    );
    assert!(matches!(
        ObjectAppearanceHwpxReader::read_in_section(
            duplicate.as_bytes(),
            0,
            41,
            141,
            limits(),
            hwpx_limits(),
        ),
        Err(ObjectAppearanceHwpxError::UnsupportedTarget)
    ));

    let unknown = String::from_utf8(shape_section()).expect("utf8").replace(
        "<hp:renderingInfo/>",
        "<hp:renderingInfo/><hp:lineShape surprise=\"1\"/>",
    );
    assert!(matches!(
        ObjectAppearanceHwpxReader::read_in_section(
            unknown.as_bytes(),
            0,
            41,
            141,
            limits(),
            hwpx_limits(),
        ),
        Err(ObjectAppearanceHwpxError::InvalidAttribute)
    ));

    let nondefault_inactive_hatch = String::from_utf8(shape_section()).expect("utf8").replace(
        "<hp:renderingInfo/>",
        concat!(
            "<hp:renderingInfo/><hc:fillBrush><hc:winBrush faceColor=\"#010203\" ",
            "hatchColor=\"#040506\" alpha=\"0\"/></hc:fillBrush>"
        ),
    );
    assert!(matches!(
        ObjectAppearanceHwpxReader::read_in_section(
            nondefault_inactive_hatch.as_bytes(),
            0,
            41,
            141,
            limits(),
            hwpx_limits(),
        ),
        Err(ObjectAppearanceHwpxError::UnsupportedTarget)
    ));

    let non_rgb = String::from_utf8(picture_section()).expect("utf8").replace(
        "<hp:effects/>",
        concat!(
            "<hp:effects><hp:glow alpha=\"0\" radius=\"1\"><hp:effectsColor type=\"SCHEME\" ",
            "schemeIdx=\"0\" systemIdx=\"0\" presetIdx=\"0\"><hp:rgb r=\"0\" g=\"0\" b=\"0\"/>",
            "</hp:effectsColor></hp:glow></hp:effects>"
        ),
    );
    assert!(matches!(
        ObjectAppearanceHwpxReader::read_in_section(
            non_rgb.as_bytes(),
            0,
            41,
            141,
            limits(),
            hwpx_limits(),
        ),
        Err(ObjectAppearanceHwpxError::UnsupportedTarget)
    ));

    let wrong_rgb_sentinels = String::from_utf8(picture_section()).expect("utf8").replace(
        "<hp:effects/>",
        concat!(
            "<hp:effects><hp:glow alpha=\"0\" radius=\"1\"><hp:effectsColor type=\"RGB\" ",
            "schemeIdx=\"0\" systemIdx=\"0\" presetIdx=\"0\"><hp:rgb r=\"0\" g=\"0\" b=\"0\"/>",
            "</hp:effectsColor></hp:glow></hp:effects>"
        ),
    );
    assert!(matches!(
        ObjectAppearanceHwpxReader::read_in_section(
            wrong_rgb_sentinels.as_bytes(),
            0,
            41,
            141,
            limits(),
            hwpx_limits(),
        ),
        Err(ObjectAppearanceHwpxError::UnsupportedTarget)
    ));
}

#[test]
fn output_limits_and_debug_are_fail_closed_and_redacted() {
    let target = ObjectAppearance {
        fill: Some(FillAppearance::Image {
            image: ImageFill {
                mode: ImageFillMode::Center,
                binary_item_id_ref: "private-asset-id".to_owned(),
                brightness: 0,
                contrast: 0,
                effect: ImageEffect::RealPicture,
                alpha: alpha(0),
            },
        }),
        ..ObjectAppearance::default()
    };
    let request = request(
        AppearanceTargetKind::BasicShape,
        AppearanceOperation::SetImageFill,
        ObjectAppearance::default(),
        target,
    );
    let domain_plan = ObjectAppearanceBuilder::plan(&request, FLOW_A, limits()).expect("plan");
    let plan = ObjectAppearanceHwpxBuilder::plan(
        &shape_section(),
        0,
        &domain_plan,
        FLOW_A,
        limits(),
        hwpx_limits(),
    )
    .expect("HWPX plan");
    let debug = format!("{plan:?}");
    assert!(!debug.contains("private-asset-id"));
    assert!(!debug.contains(FLOW_A));

    let mut config = ObjectAppearanceHwpxLimitConfig::default();
    config.output_bytes = shape_section().len();
    config.section_bytes = config.output_bytes;
    config.fragment_bytes = 32;
    let tiny = ObjectAppearanceHwpxLimits::new(config).expect("tiny limits");
    assert!(matches!(
        ObjectAppearanceHwpxLowerer::lower_in_section(
            &shape_section(),
            &plan,
            FLOW_A,
            limits(),
            tiny,
        ),
        Err(ObjectAppearanceHwpxError::OutputLimit | ObjectAppearanceHwpxError::PlanTampered)
    ));
}
