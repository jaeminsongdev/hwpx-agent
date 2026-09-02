use std::any::TypeId;
use std::error::Error;

use domain_ir::{
    AngleMicrodegrees, ArtifactId, BackendOpaqueId, BookmarkId, ChangeId, CoordinateAnchor,
    CoordinateSpace, FieldId, HwpUnit, IdentityError, LengthMicrometers, LogicalNodeId,
    MAX_TYPED_ID_BYTES, PointMilli, Position2D, ProjectId, RatioMillionths, RationalInput,
    ResourceId, RevisionId, StyleId, UnitError, UnitKind, ZOrder,
};

type TestResult = Result<(), Box<dyn Error>>;

#[test]
fn official_hwpunit_point_and_a4_constants_are_exact() -> TestResult {
    let inch = LengthMicrometers::from_hwp_unit(HwpUnit::from_raw(7_200))?;
    assert_eq!(inch.value().as_i64(), 25_400);
    assert_eq!(inch.receipt().rounding_delta(), (0, 1));

    let points = LengthMicrometers::from_points(RationalInput::integer(10))?;
    assert_eq!(points.value().as_i64(), 3_528);
    assert_eq!(points.receipt().rounding_delta(), (2, 9));
    assert_eq!(points.value().to_hwp_unit()?.value().as_i64(), 1_000);
    assert_eq!(
        PointMilli::from_points(RationalInput::integer(10))?
            .value()
            .as_i64(),
        10_000
    );

    let a4_width = LengthMicrometers::from_millimeters(RationalInput::integer(210))?;
    assert_eq!(a4_width.value().as_i64(), 210_000);
    assert_eq!(a4_width.value().to_hwp_unit()?.value().as_i64(), 59_528);
    Ok(())
}

#[test]
fn half_away_from_zero_is_symmetric_and_receipted() -> TestResult {
    let positive = LengthMicrometers::from_millimeters(RationalInput::new(1, 2_000)?)?;
    let negative = LengthMicrometers::from_millimeters(RationalInput::new(-1, 2_000)?)?;
    assert_eq!(positive.value().as_i64(), 1);
    assert_eq!(negative.value().as_i64(), -1);
    assert_eq!(positive.receipt().rounding_delta(), (1, 2));
    assert_eq!(negative.receipt().rounding_delta(), (-1, 2));
    assert_eq!(positive.receipt().source_unit(), UnitKind::Millimeter);
    assert_eq!(positive.receipt().target_unit(), UnitKind::Micrometer);
    Ok(())
}

#[test]
fn pixels_require_explicit_bounded_dpi() -> TestResult {
    let inch = LengthMicrometers::from_pixels(RationalInput::integer(96), 96)?;
    assert_eq!(inch.value().as_i64(), 25_400);
    assert_eq!(inch.receipt().context_dpi(), Some(96));
    assert_eq!(
        LengthMicrometers::from_pixels(RationalInput::integer(1), 0),
        Err(UnitError::InvalidDpi)
    );
    assert_eq!(
        LengthMicrometers::from_pixels(RationalInput::integer(1), 1_000_001),
        Err(UnitError::InvalidDpi)
    );
    Ok(())
}

#[test]
fn ratio_percent_and_degree_normalization_use_fixed_point() -> TestResult {
    assert_eq!(
        RatioMillionths::from_percent(RationalInput::integer(100))?
            .value()
            .as_i64(),
        1_000_000
    );
    let third = RatioMillionths::from_ratio(RationalInput::new(1, 3)?)?;
    assert_eq!(third.value().as_i64(), 333_333);
    assert_eq!(third.receipt().rounding_delta(), (-1, 3));
    assert_eq!(third.receipt().target_unit(), UnitKind::RatioMillionths);
    assert_eq!(
        AngleMicrodegrees::from_degrees(RationalInput::integer(90))?
            .value()
            .as_i64(),
        90_000_000
    );
    Ok(())
}

#[test]
fn invalid_denominators_and_arithmetic_overflow_fail_closed() {
    assert_eq!(RationalInput::new(1, 0), Err(UnitError::InvalidDenominator));
    assert_eq!(
        RationalInput::new(1, 1_000_000_001),
        Err(UnitError::InvalidDenominator)
    );
    assert_eq!(
        LengthMicrometers::from_millimeters(RationalInput::integer(i64::MAX)),
        Err(UnitError::Overflow)
    );
    assert_eq!(
        LengthMicrometers::from_raw(i64::MAX).checked_add(LengthMicrometers::from_raw(1)),
        Err(UnitError::Overflow)
    );
    assert!(serde_json::from_str::<RationalInput>(r#"{"numerator":1,"denominator":0}"#).is_err());
}

#[test]
fn fixed_seed_hwpunit_roundtrip_property_holds() -> TestResult {
    let mut state = 0x4d59_5df4_d0f3_3173_u64;
    for _ in 0..10_000 {
        state = state
            .wrapping_mul(6_364_136_223_846_793_005)
            .wrapping_add(1_442_695_040_888_963_407);
        let raw = i64::try_from((state >> 1) % 2_000_000_001)? - 1_000_000_000;
        let normalized = LengthMicrometers::from_hwp_unit(HwpUnit::from_raw(raw))?;
        let lowered = normalized.value().to_hwp_unit()?;
        assert_eq!(lowered.value().as_i64(), raw);
    }
    Ok(())
}

#[test]
fn typed_ids_validate_deserialization_and_remain_distinct() -> TestResult {
    let project = ProjectId::parse("project-alpha")?;
    let revision = RevisionId::parse("revision-alpha")?;
    let _ = ArtifactId::parse("artifact-alpha")?;
    let _ = LogicalNodeId::parse("node-alpha")?;
    let _ = StyleId::parse("style-alpha")?;
    let _ = ResourceId::parse("resource-alpha")?;
    let _ = BookmarkId::parse("bookmark-alpha")?;
    let _ = FieldId::parse("field-alpha")?;
    let _ = ChangeId::parse("change-alpha")?;
    let _ = BackendOpaqueId::parse("backend-alpha")?;

    assert_ne!(TypeId::of::<ProjectId>(), TypeId::of::<RevisionId>());
    assert_eq!(serde_json::to_string(&project)?, "\"project-alpha\"");
    assert_eq!(
        serde_json::from_str::<ProjectId>("\"project-alpha\"")?,
        project
    );
    assert_eq!(ProjectId::parse(""), Err(IdentityError::InvalidIdentifier));
    assert_eq!(
        ProjectId::parse("x".repeat(MAX_TYPED_ID_BYTES + 1)),
        Err(IdentityError::IdentifierTooLong)
    );
    assert!(serde_json::from_str::<RevisionId>("\"bad\\nvalue\"").is_err());
    assert!(!format!("{project:?}{revision:?}").contains("alpha"));
    Ok(())
}

#[test]
fn coordinate_space_requires_a_compatible_anchor_and_checked_translation() -> TestResult {
    let page = Position2D::new(
        LengthMicrometers::from_raw(10),
        LengthMicrometers::from_raw(20),
        CoordinateSpace::Page,
        CoordinateAnchor::Page,
    )?;
    assert_eq!(page.space(), CoordinateSpace::Page);
    assert_eq!(page.x().as_i64(), 10);
    assert_eq!(
        serde_json::from_str::<Position2D>(&serde_json::to_string(&page)?)?,
        page
    );
    assert_eq!(
        Position2D::new(
            LengthMicrometers::from_raw(0),
            LengthMicrometers::from_raw(0),
            CoordinateSpace::Page,
            CoordinateAnchor::Content,
        ),
        Err(UnitError::IncompatibleCoordinateSpace)
    );
    assert!(
        serde_json::from_str::<Position2D>(
            r#"{"x":0,"y":0,"space":"page","anchor":{"anchor_type":"content"}}"#
        )
        .is_err()
    );

    let node_id = LogicalNodeId::parse("private-node-id")?;
    let anchored = Position2D::new(
        LengthMicrometers::from_raw(1),
        LengthMicrometers::from_raw(2),
        CoordinateSpace::Anchor,
        CoordinateAnchor::LogicalNode { node_id },
    )?;
    assert!(!format!("{anchored:?}").contains("private-node-id"));

    let maximum = Position2D::new(
        LengthMicrometers::from_raw(i64::MAX),
        LengthMicrometers::from_raw(0),
        CoordinateSpace::Page,
        CoordinateAnchor::Page,
    )?;
    assert_eq!(
        maximum.checked_translate(
            LengthMicrometers::from_raw(1),
            LengthMicrometers::from_raw(0)
        ),
        Err(UnitError::Overflow)
    );
    assert!(ZOrder::new(-10) < ZOrder::new(10));
    Ok(())
}

#[test]
fn conversion_debug_redacts_raw_numeric_values() -> TestResult {
    let conversion = LengthMicrometers::from_millimeters(RationalInput::new(424_242, 7)?)?;
    let debug = format!("{conversion:?} {:?}", conversion.receipt());
    assert!(!debug.contains("424242"));
    assert!(debug.contains("<redacted>"));
    Ok(())
}
