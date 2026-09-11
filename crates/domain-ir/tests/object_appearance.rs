#![allow(clippy::expect_used)] // Test fixtures use expectations to keep failures local.

use domain_ir::{
    AlignStyle, AppearanceOperation, AppearanceTargetKind, ArrowSize, ArrowStyle, ClassicShadow,
    ClassicShadowType, ColorTransform, ColorTransformKind, EffectColor, EffectScalar,
    FillAppearance, GlowEffect, GradientFill, GradientType, ImageAdjustment, ImageEffect,
    ImageFill, ImageFillMode, LineAppearance, LineEndCap, LinePattern, LogicalId,
    OBJECT_APPEARANCE_SCHEMA_VERSION, ObjectAppearance, ObjectAppearanceBuilder,
    ObjectAppearanceError, ObjectAppearanceLimitConfig, ObjectAppearanceLimits,
    ObjectAppearanceRequest, ObjectAppearanceRequestDraft, ObjectHatchStyle, OutlineStyle,
    PictureEffects, PictureShadow, PictureShadowStyle, ReflectionEffect, RgbColor, ScalarPair,
    SoftEdgeEffect, TransparencyChannel, UnitFraction, UnitRange,
};

const FLOW_A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const FLOW_B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";

fn limits() -> ObjectAppearanceLimits {
    ObjectAppearanceLimits::new(ObjectAppearanceLimitConfig::default()).expect("valid limits")
}

fn color(red: u8, green: u8, blue: u8) -> RgbColor {
    RgbColor { red, green, blue }
}

fn alpha(value: u32) -> UnitFraction {
    UnitFraction::new(value).expect("valid alpha")
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
        alpha: alpha(125_000),
    }
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

fn request(
    kind: AppearanceTargetKind,
    operation: AppearanceOperation,
    source: ObjectAppearance,
    target: ObjectAppearance,
) -> Result<ObjectAppearanceRequest, ObjectAppearanceError> {
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
}

#[test]
fn plans_and_builds_line_solid_pattern_gradient_image_and_shape_shadow() {
    let operations = [
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
                    alpha: alpha(100_000),
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
                        alpha: alpha(500_000),
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
                    alpha: alpha(250_000),
                }),
                ..ObjectAppearance::default()
            },
        ),
    ];
    for (operation, target) in operations {
        let request = request(
            AppearanceTargetKind::BasicShape,
            operation,
            ObjectAppearance::default(),
            target.clone(),
        )
        .expect("request");
        assert_eq!(
            request.operation().capability_id(),
            operation.capability_id()
        );
        let plan = ObjectAppearanceBuilder::plan(&request, FLOW_A, limits()).expect("plan");
        let result = ObjectAppearanceBuilder::build(&plan, FLOW_A, limits()).expect("build");
        assert_eq!(result.target(), &target);
        assert_eq!(result.receipt().plan_sha256(), plan.plan_sha256());
    }
}

#[test]
fn plans_and_builds_all_picture_effect_and_adjustment_operations() {
    let full = picture_effects();
    let operations = [
        (
            AppearanceOperation::SetPictureShadow,
            PictureEffects {
                shadow: full.shadow.clone(),
                ..PictureEffects::default()
            },
        ),
        (
            AppearanceOperation::SetGlow,
            PictureEffects {
                glow: full.glow.clone(),
                ..PictureEffects::default()
            },
        ),
        (
            AppearanceOperation::SetSoftEdge,
            PictureEffects {
                soft_edge: full.soft_edge,
                ..PictureEffects::default()
            },
        ),
        (
            AppearanceOperation::SetReflection,
            PictureEffects {
                reflection: full.reflection.clone(),
                ..PictureEffects::default()
            },
        ),
    ];
    for (operation, effects) in operations {
        let target = ObjectAppearance {
            picture_effects: Some(effects),
            ..ObjectAppearance::default()
        };
        let value = request(
            AppearanceTargetKind::Picture,
            operation,
            ObjectAppearance::default(),
            target.clone(),
        )
        .expect("request");
        let plan = ObjectAppearanceBuilder::plan(&value, FLOW_A, limits()).expect("plan");
        assert_eq!(
            ObjectAppearanceBuilder::build(&plan, FLOW_A, limits())
                .expect("build")
                .target(),
            &target
        );
    }

    let adjustment = ImageAdjustment {
        brightness: -25,
        contrast: 75,
        effect: ImageEffect::BlackWhite,
        alpha: alpha(0),
    };
    let target = ObjectAppearance {
        image_adjustment: Some(adjustment),
        ..ObjectAppearance::default()
    };
    let value = request(
        AppearanceTargetKind::Picture,
        AppearanceOperation::SetColorAdjust,
        ObjectAppearance::default(),
        target,
    )
    .expect("request");
    assert_eq!(value.operation().capability_id(), "obj.color_adjust");
}

#[test]
fn transparency_requires_an_exact_single_alpha_delta() {
    let source = ObjectAppearance {
        line: Some(line()),
        ..ObjectAppearance::default()
    };
    let mut target = source.clone();
    target.line.as_mut().expect("line").alpha = alpha(900_000);
    let value = request(
        AppearanceTargetKind::BasicShape,
        AppearanceOperation::SetTransparency {
            channel: TransparencyChannel::Line,
        },
        source.clone(),
        target,
    )
    .expect("alpha-only request");
    assert_eq!(value.operation().capability_id(), "obj.transparency");

    let mut wrong = source.clone();
    wrong.line.as_mut().expect("line").alpha = alpha(900_000);
    wrong.line.as_mut().expect("line").width_hwpunit += 1;
    assert!(matches!(
        request(
            AppearanceTargetKind::BasicShape,
            AppearanceOperation::SetTransparency {
                channel: TransparencyChannel::Line,
            },
            source,
            wrong,
        ),
        Err(ObjectAppearanceError::InvalidOperationDelta)
    ));
}

#[test]
fn rejects_cross_family_effects_invalid_resources_and_ranges() {
    let picture_only = ObjectAppearance {
        picture_effects: Some(picture_effects()),
        ..ObjectAppearance::default()
    };
    assert!(matches!(
        picture_only.validate(AppearanceTargetKind::BasicShape, limits()),
        Err(ObjectAppearanceError::KindMismatch)
    ));

    let invalid_fill = ObjectAppearance {
        fill: Some(FillAppearance::Image {
            image: ImageFill {
                mode: ImageFillMode::Tile,
                binary_item_id_ref: "../secret".to_owned(),
                brightness: 0,
                contrast: 0,
                effect: ImageEffect::RealPicture,
                alpha: alpha(0),
            },
        }),
        ..ObjectAppearance::default()
    };
    assert!(matches!(
        invalid_fill.validate(AppearanceTargetKind::BasicShape, limits()),
        Err(ObjectAppearanceError::InvalidResource)
    ));

    let invalid_alpha = ObjectAppearance {
        line: Some(LineAppearance {
            alpha: UnitFraction(1_000_001),
            ..line()
        }),
        ..ObjectAppearance::default()
    };
    assert!(matches!(
        invalid_alpha.validate(AppearanceTargetKind::BasicShape, limits()),
        Err(ObjectAppearanceError::InvalidAlpha)
    ));
}

#[test]
fn strict_json_rejects_duplicate_unknown_and_flow_drift() {
    let target = ObjectAppearance {
        line: Some(line()),
        ..ObjectAppearance::default()
    };
    let value = request(
        AppearanceTargetKind::BasicShape,
        AppearanceOperation::SetLine,
        ObjectAppearance::default(),
        target,
    )
    .expect("request");
    let json = value.canonical_json(limits()).expect("json");
    assert!(matches!(
        ObjectAppearanceRequest::from_json(&json, FLOW_B, limits()),
        Err(ObjectAppearanceError::FlowDrift)
    ));

    let duplicate = br#"{"schema_version":"hwpx-agent.object-appearance/v1","schema_version":"hwpx-agent.object-appearance/v1"}"#;
    assert!(matches!(
        ObjectAppearanceRequest::from_json(duplicate, FLOW_A, limits()),
        Err(ObjectAppearanceError::DuplicateJsonKey)
    ));

    let mut value: serde_json::Value = serde_json::from_slice(&json).expect("json value");
    value
        .as_object_mut()
        .expect("object")
        .insert("unknown".to_owned(), serde_json::Value::Bool(true));
    assert!(matches!(
        ObjectAppearanceRequest::from_json(
            &serde_json::to_vec(&value).expect("json bytes"),
            FLOW_A,
            limits(),
        ),
        Err(ObjectAppearanceError::InvalidJson)
    ));
}

#[test]
fn build_rejects_flow_drift_and_debug_redacts_identity_and_values() {
    let target = ObjectAppearance {
        fill: Some(FillAppearance::Image {
            image: ImageFill {
                mode: ImageFillMode::Center,
                binary_item_id_ref: "private-asset-id".to_owned(),
                brightness: 12,
                contrast: 34,
                effect: ImageEffect::RealPicture,
                alpha: alpha(56_000),
            },
        }),
        ..ObjectAppearance::default()
    };
    let value = request(
        AppearanceTargetKind::BasicShape,
        AppearanceOperation::SetImageFill,
        ObjectAppearance::default(),
        target,
    )
    .expect("request");
    let plan = ObjectAppearanceBuilder::plan(&value, FLOW_A, limits()).expect("plan");
    assert!(matches!(
        ObjectAppearanceBuilder::build(&plan, FLOW_B, limits()),
        Err(ObjectAppearanceError::BuildDrift)
    ));
    let debug = format!("{plan:?}");
    assert!(!debug.contains("private-asset-id"));
    assert!(!debug.contains("appearance-request"));
    assert!(!debug.contains(FLOW_A));
}
