use std::fmt;

use domain_ir::ObjectPropertyKind;
use thiserror::Error;

pub const OBJECT_HYPERLINK_CURRENT_TARGET_PROFILE_ID: &str =
    "hwpx-agent.object-hyperlink-target.hangul-2020-11.0.0.9136-x86-ko-KR/v1";
pub const OBJECT_HYPERLINK_CURRENT_TARGET_EXECUTABLE_SHA256: &str =
    "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce";

const CURRENT_TARGET_BUILD: &str = "11.0.0.9136";
const CURRENT_TARGET_ARCHITECTURE: &str = "x86";
const CURRENT_TARGET_LOCALE: &str = "ko-KR";
const CAPABILITY_ID: &str = "obj.object_hyperlink";
const API_CAPABILITY_UNAVAILABLE: &str = "CAPABILITY_UNAVAILABLE_FOR_TARGET";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ObjectHyperlinkDirectAdmission {
    Eligible,
    Rejected,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ObjectHyperlinkTargetRoute {
    DirectHwpx,
}

#[derive(Clone, Copy, Debug, Error, Eq, PartialEq)]
pub enum ObjectHyperlinkTargetRouteError {
    #[error("object-hyperlink target profile does not match the qualified build")]
    TargetProfileMismatch,
    #[error("object kind is outside the object-hyperlink capability contract")]
    ObjectKindOutOfScope,
    #[error("object hyperlink is unavailable for this target and object kind")]
    CapabilityUnavailableForTarget,
}

impl ObjectHyperlinkTargetRouteError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::TargetProfileMismatch => "object_hyperlink_target_profile_mismatch",
            Self::ObjectKindOutOfScope => "object_hyperlink_target_object_kind_out_of_scope",
            Self::CapabilityUnavailableForTarget => {
                "object_hyperlink_target_capability_unavailable"
            }
        }
    }

    #[must_use]
    pub const fn api_error_code(self) -> &'static str {
        API_CAPABILITY_UNAVAILABLE
    }
}

/// Exact current-PC route policy for `obj.object_hyperlink`.
///
/// The qualified Hangul 2020 surface exposes a dialog-mediated generic-shape command, while the
/// chart selection surface does not enable that command. Neither surface is an unattended,
/// verified fallback. Therefore this router admits only the preserving direct-HWPX profile and
/// fails closed before any mutation when that profile cannot accept the selected object.
#[derive(Clone, Copy, Eq, PartialEq)]
pub struct ObjectHyperlinkTargetRouter {
    _qualified: (),
}

impl ObjectHyperlinkTargetRouter {
    /// Qualifies the exact installed target identity used by the P08-16 policy.
    ///
    /// # Errors
    ///
    /// Rejects every other build, architecture, locale, or executable digest.
    pub fn qualify(
        build: &str,
        architecture: &str,
        locale: &str,
        executable_sha256: &str,
    ) -> Result<Self, ObjectHyperlinkTargetRouteError> {
        if build != CURRENT_TARGET_BUILD
            || architecture != CURRENT_TARGET_ARCHITECTURE
            || locale != CURRENT_TARGET_LOCALE
            || executable_sha256 != OBJECT_HYPERLINK_CURRENT_TARGET_EXECUTABLE_SHA256
        {
            return Err(ObjectHyperlinkTargetRouteError::TargetProfileMismatch);
        }
        Ok(Self { _qualified: () })
    }

    #[must_use]
    pub const fn profile_id(self) -> &'static str {
        OBJECT_HYPERLINK_CURRENT_TARGET_PROFILE_ID
    }

    #[must_use]
    pub const fn capability_id(self) -> &'static str {
        CAPABILITY_ID
    }

    /// Selects the only verified route for the object kind, or fails before effect.
    ///
    /// # Errors
    ///
    /// Charts return `CAPABILITY_UNAVAILABLE_FOR_TARGET`; form objects and paragraph bands are
    /// outside the catalogued capability IR. A rejected direct preflight never widens to desktop
    /// automation because the current target has no verified unattended fallback.
    pub const fn route(
        self,
        object_kind: ObjectPropertyKind,
        direct_admission: ObjectHyperlinkDirectAdmission,
    ) -> Result<ObjectHyperlinkTargetRoute, ObjectHyperlinkTargetRouteError> {
        match object_kind {
            ObjectPropertyKind::Chart => {
                Err(ObjectHyperlinkTargetRouteError::CapabilityUnavailableForTarget)
            }
            ObjectPropertyKind::FormObject | ObjectPropertyKind::ParagraphBand => {
                Err(ObjectHyperlinkTargetRouteError::ObjectKindOutOfScope)
            }
            ObjectPropertyKind::BasicShape
            | ObjectPropertyKind::TextBox
            | ObjectPropertyKind::Picture
            | ObjectPropertyKind::DrawingCanvas
            | ObjectPropertyKind::EmbeddedObject => match direct_admission {
                ObjectHyperlinkDirectAdmission::Eligible => {
                    Ok(ObjectHyperlinkTargetRoute::DirectHwpx)
                }
                ObjectHyperlinkDirectAdmission::Rejected => {
                    Err(ObjectHyperlinkTargetRouteError::CapabilityUnavailableForTarget)
                }
            },
        }
    }
}

impl fmt::Debug for ObjectHyperlinkTargetRouter {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("ObjectHyperlinkTargetRouter(<exact-target-qualified>)")
    }
}
