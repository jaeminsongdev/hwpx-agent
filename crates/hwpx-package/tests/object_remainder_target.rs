#![allow(clippy::expect_used)] // Exact route fixtures keep failures local and readable.

use domain_ir::ObjectPropertyKind;
use hwpx_package::{
    OBJECT_REMAINDER_CURRENT_TARGET_EXECUTABLE_SHA256, OBJECT_REMAINDER_CURRENT_TARGET_PROFILE_ID,
    ObjectRemainderCapability, ObjectRemainderDirectAdmission, ObjectRemainderTargetRoute,
    ObjectRemainderTargetRouteError, ObjectRemainderTargetRouter,
};

fn router() -> ObjectRemainderTargetRouter {
    ObjectRemainderTargetRouter::qualify(
        "11.0.0.9136",
        "x86",
        "ko-KR",
        OBJECT_REMAINDER_CURRENT_TARGET_EXECUTABLE_SHA256,
    )
    .expect("exact target")
}

#[test]
fn exact_target_routes_eight_bounded_native_profiles() {
    let router = router();
    assert_eq!(
        router.profile_id(),
        OBJECT_REMAINDER_CURRENT_TARGET_PROFILE_ID
    );
    for (capability, kind) in [
        (
            ObjectRemainderCapability::MarginCaption,
            ObjectPropertyKind::BasicShape,
        ),
        (
            ObjectRemainderCapability::ImageProperties,
            ObjectPropertyKind::Picture,
        ),
        (
            ObjectRemainderCapability::Printable,
            ObjectPropertyKind::FormObject,
        ),
        (
            ObjectRemainderCapability::AltText,
            ObjectPropertyKind::DrawingCanvas,
        ),
        (
            ObjectRemainderCapability::FormObjectInsert,
            ObjectPropertyKind::FormObject,
        ),
        (
            ObjectRemainderCapability::CaptionInsert,
            ObjectPropertyKind::BasicShape,
        ),
        (
            ObjectRemainderCapability::DrawingGallery,
            ObjectPropertyKind::BasicShape,
        ),
        (
            ObjectRemainderCapability::ParagraphBandObject,
            ObjectPropertyKind::ParagraphBand,
        ),
    ] {
        assert_eq!(
            router.route(capability, kind, ObjectRemainderDirectAdmission::Eligible),
            Ok(ObjectRemainderTargetRoute::DirectHwpx),
            "{}",
            capability.capability_id()
        );
    }
}

#[test]
fn aspect_lock_remains_unqualified_with_a_specific_stable_reason() {
    let error = router()
        .route(
            ObjectRemainderCapability::AspectLock,
            ObjectPropertyKind::BasicShape,
            ObjectRemainderDirectAdmission::Eligible,
        )
        .expect_err("unqualified semantic must fail closed");
    assert_eq!(
        error,
        ObjectRemainderTargetRouteError::AspectLockNativeFieldUnqualified
    );
    assert_eq!(error.api_error_code(), "CAPABILITY_UNAVAILABLE_FOR_TARGET");
}

#[test]
fn rejected_direct_preflight_never_widens_to_unverified_automation() {
    for (capability, kind) in [
        (
            ObjectRemainderCapability::MarginCaption,
            ObjectPropertyKind::TextBox,
        ),
        (
            ObjectRemainderCapability::ImageProperties,
            ObjectPropertyKind::Picture,
        ),
        (
            ObjectRemainderCapability::Printable,
            ObjectPropertyKind::FormObject,
        ),
        (
            ObjectRemainderCapability::AltText,
            ObjectPropertyKind::Chart,
        ),
        (
            ObjectRemainderCapability::FormObjectInsert,
            ObjectPropertyKind::FormObject,
        ),
        (
            ObjectRemainderCapability::CaptionInsert,
            ObjectPropertyKind::BasicShape,
        ),
        (
            ObjectRemainderCapability::DrawingGallery,
            ObjectPropertyKind::BasicShape,
        ),
        (
            ObjectRemainderCapability::ParagraphBandObject,
            ObjectPropertyKind::ParagraphBand,
        ),
    ] {
        assert_eq!(
            router().route(capability, kind, ObjectRemainderDirectAdmission::Rejected),
            Err(ObjectRemainderTargetRouteError::DirectProfileRejected)
        );
    }
}

#[test]
fn kind_mismatch_and_target_drift_are_rejected() {
    for (capability, kind) in [
        (
            ObjectRemainderCapability::ImageProperties,
            ObjectPropertyKind::BasicShape,
        ),
        (
            ObjectRemainderCapability::Printable,
            ObjectPropertyKind::Picture,
        ),
        (
            ObjectRemainderCapability::MarginCaption,
            ObjectPropertyKind::ParagraphBand,
        ),
        (
            ObjectRemainderCapability::AltText,
            ObjectPropertyKind::ParagraphBand,
        ),
        (
            ObjectRemainderCapability::FormObjectInsert,
            ObjectPropertyKind::BasicShape,
        ),
        (
            ObjectRemainderCapability::CaptionInsert,
            ObjectPropertyKind::Picture,
        ),
        (
            ObjectRemainderCapability::DrawingGallery,
            ObjectPropertyKind::Picture,
        ),
        (
            ObjectRemainderCapability::ParagraphBandObject,
            ObjectPropertyKind::BasicShape,
        ),
    ] {
        assert_eq!(
            router().route(capability, kind, ObjectRemainderDirectAdmission::Eligible),
            Err(ObjectRemainderTargetRouteError::ObjectKindOutOfScope)
        );
    }

    for (build, architecture, locale, executable) in [
        (
            "11.0.0.9137",
            "x86",
            "ko-KR",
            OBJECT_REMAINDER_CURRENT_TARGET_EXECUTABLE_SHA256,
        ),
        (
            "11.0.0.9136",
            "x86_64",
            "ko-KR",
            OBJECT_REMAINDER_CURRENT_TARGET_EXECUTABLE_SHA256,
        ),
        (
            "11.0.0.9136",
            "x86",
            "en-US",
            OBJECT_REMAINDER_CURRENT_TARGET_EXECUTABLE_SHA256,
        ),
        ("11.0.0.9136", "x86", "ko-KR", &"0".repeat(64)),
    ] {
        assert_eq!(
            ObjectRemainderTargetRouter::qualify(build, architecture, locale, executable),
            Err(ObjectRemainderTargetRouteError::TargetProfileMismatch)
        );
    }
}

#[test]
fn diagnostics_reveal_policy_only() {
    assert_eq!(
        format!("{:?}", router()),
        "ObjectRemainderTargetRouter(<exact-target-qualified>)"
    );
    assert!(!format!("{:?}", router()).contains("11.0.0.9136"));
    assert_eq!(
        ObjectRemainderTargetRouteError::AspectLockNativeFieldUnqualified.code(),
        "object_remainder_aspect_lock_native_field_unqualified"
    );
}
