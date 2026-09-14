#![allow(clippy::expect_used)] // Test fixtures keep exact failures local and readable.

use domain_ir::ObjectPropertyKind;
use hwpx_package::{
    OBJECT_HYPERLINK_CURRENT_TARGET_EXECUTABLE_SHA256, OBJECT_HYPERLINK_CURRENT_TARGET_PROFILE_ID,
    ObjectHyperlinkDirectAdmission, ObjectHyperlinkTargetRoute, ObjectHyperlinkTargetRouteError,
    ObjectHyperlinkTargetRouter,
};

fn router() -> ObjectHyperlinkTargetRouter {
    ObjectHyperlinkTargetRouter::qualify(
        "11.0.0.9136",
        "x86",
        "ko-KR",
        OBJECT_HYPERLINK_CURRENT_TARGET_EXECUTABLE_SHA256,
    )
    .expect("exact target")
}

#[test]
fn exact_target_routes_all_five_supported_ir_kinds_to_direct_hwpx() {
    let router = router();
    assert_eq!(
        router.profile_id(),
        OBJECT_HYPERLINK_CURRENT_TARGET_PROFILE_ID
    );
    assert_eq!(router.capability_id(), "obj.object_hyperlink");
    for kind in [
        ObjectPropertyKind::BasicShape,
        ObjectPropertyKind::TextBox,
        ObjectPropertyKind::Picture,
        ObjectPropertyKind::DrawingCanvas,
        ObjectPropertyKind::EmbeddedObject,
    ] {
        assert_eq!(
            router.route(kind, ObjectHyperlinkDirectAdmission::Eligible),
            Ok(ObjectHyperlinkTargetRoute::DirectHwpx)
        );
    }
}

#[test]
fn chart_fails_closed_without_desktop_automation_fallback() {
    for admission in [
        ObjectHyperlinkDirectAdmission::Eligible,
        ObjectHyperlinkDirectAdmission::Rejected,
    ] {
        let error = router()
            .route(ObjectPropertyKind::Chart, admission)
            .expect_err("chart must remain unavailable");
        assert_eq!(
            error,
            ObjectHyperlinkTargetRouteError::CapabilityUnavailableForTarget
        );
        assert_eq!(error.api_error_code(), "CAPABILITY_UNAVAILABLE_FOR_TARGET");
    }
}

#[test]
fn rejected_direct_preflight_never_widens_to_dialog_automation() {
    for kind in [
        ObjectPropertyKind::BasicShape,
        ObjectPropertyKind::TextBox,
        ObjectPropertyKind::Picture,
        ObjectPropertyKind::DrawingCanvas,
        ObjectPropertyKind::EmbeddedObject,
    ] {
        assert_eq!(
            router().route(kind, ObjectHyperlinkDirectAdmission::Rejected),
            Err(ObjectHyperlinkTargetRouteError::CapabilityUnavailableForTarget)
        );
    }
}

#[test]
fn target_drift_and_out_of_scope_ir_kinds_are_rejected() {
    for (build, architecture, locale, executable) in [
        (
            "11.0.0.9137",
            "x86",
            "ko-KR",
            OBJECT_HYPERLINK_CURRENT_TARGET_EXECUTABLE_SHA256,
        ),
        (
            "11.0.0.9136",
            "x86_64",
            "ko-KR",
            OBJECT_HYPERLINK_CURRENT_TARGET_EXECUTABLE_SHA256,
        ),
        (
            "11.0.0.9136",
            "x86",
            "en-US",
            OBJECT_HYPERLINK_CURRENT_TARGET_EXECUTABLE_SHA256,
        ),
        ("11.0.0.9136", "x86", "ko-KR", &"0".repeat(64)),
    ] {
        assert_eq!(
            ObjectHyperlinkTargetRouter::qualify(build, architecture, locale, executable),
            Err(ObjectHyperlinkTargetRouteError::TargetProfileMismatch)
        );
    }

    for kind in [
        ObjectPropertyKind::FormObject,
        ObjectPropertyKind::ParagraphBand,
    ] {
        assert_eq!(
            router().route(kind, ObjectHyperlinkDirectAdmission::Eligible),
            Err(ObjectHyperlinkTargetRouteError::ObjectKindOutOfScope)
        );
    }
}

#[test]
fn diagnostics_expose_policy_only_and_never_target_identity() {
    let debug = format!("{:?}", router());
    assert_eq!(
        debug,
        "ObjectHyperlinkTargetRouter(<exact-target-qualified>)"
    );
    assert!(!debug.contains("11.0.0.9136"));
    assert_eq!(
        ObjectHyperlinkTargetRouteError::CapabilityUnavailableForTarget.code(),
        "object_hyperlink_target_capability_unavailable"
    );
}
