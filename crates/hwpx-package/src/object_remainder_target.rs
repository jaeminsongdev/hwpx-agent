use std::fmt;

use domain_ir::ObjectPropertyKind;
use thiserror::Error;

pub const OBJECT_REMAINDER_CURRENT_TARGET_PROFILE_ID: &str =
    "hwpx-agent.object-remainder-target.hangul-2020-11.0.0.9136-x86-ko-KR/v1";
pub const OBJECT_REMAINDER_CURRENT_TARGET_EXECUTABLE_SHA256: &str =
    "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce";

const CURRENT_TARGET_BUILD: &str = "11.0.0.9136";
const CURRENT_TARGET_ARCHITECTURE: &str = "x86";
const CURRENT_TARGET_LOCALE: &str = "ko-KR";
const API_CAPABILITY_UNAVAILABLE: &str = "CAPABILITY_UNAVAILABLE_FOR_TARGET";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ObjectRemainderCapability {
    DrawingGallery,
    FormObjectInsert,
    CaptionInsert,
    ParagraphBandObject,
    MarginCaption,
    ImageProperties,
    AspectLock,
    Printable,
    AltText,
}

impl ObjectRemainderCapability {
    #[must_use]
    pub const fn capability_id(self) -> &'static str {
        match self {
            Self::DrawingGallery => "obj.drawing_gallery",
            Self::FormObjectInsert => "obj.form_object_insert",
            Self::CaptionInsert => "obj.caption_insert",
            Self::ParagraphBandObject => "obj.paragraph_band_object",
            Self::MarginCaption => "obj.margin_caption",
            Self::ImageProperties => "obj.image_properties",
            Self::AspectLock => "obj.aspect_lock",
            Self::Printable => "obj.printable",
            Self::AltText => "obj.alt_text",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ObjectRemainderDirectAdmission {
    Eligible,
    Rejected,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ObjectRemainderTargetRoute {
    DirectHwpx,
}

#[derive(Clone, Copy, Debug, Error, Eq, PartialEq)]
pub enum ObjectRemainderTargetRouteError {
    #[error("object-remainder target profile does not match the qualified build")]
    TargetProfileMismatch,
    #[error("drawing-gallery payload does not contain a qualified native object template")]
    DrawingGalleryTemplateUnqualified,
    #[error("form insertion payload does not contain the complete native form-control state")]
    FormInsertionStateIncomplete,
    #[error("caption insertion has no qualified exact subtree insertion profile")]
    CaptionInsertionUnqualified,
    #[error("paragraph band has no qualified distinct HWPML native construct")]
    ParagraphBandNativeConstructUnqualified,
    #[error("aspect lock has no qualified HWPML field and is not size protection")]
    AspectLockNativeFieldUnqualified,
    #[error("object kind is outside the qualified direct profile")]
    ObjectKindOutOfScope,
    #[error("the direct profile rejected this exact source and no unattended fallback exists")]
    DirectProfileRejected,
}

impl ObjectRemainderTargetRouteError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::TargetProfileMismatch => "object_remainder_target_profile_mismatch",
            Self::DrawingGalleryTemplateUnqualified => {
                "object_remainder_drawing_gallery_template_unqualified"
            }
            Self::FormInsertionStateIncomplete => {
                "object_remainder_form_insertion_state_incomplete"
            }
            Self::CaptionInsertionUnqualified => "object_remainder_caption_insertion_unqualified",
            Self::ParagraphBandNativeConstructUnqualified => {
                "object_remainder_paragraph_band_native_construct_unqualified"
            }
            Self::AspectLockNativeFieldUnqualified => {
                "object_remainder_aspect_lock_native_field_unqualified"
            }
            Self::ObjectKindOutOfScope => "object_remainder_target_object_kind_out_of_scope",
            Self::DirectProfileRejected => "object_remainder_target_direct_profile_rejected",
        }
    }

    #[must_use]
    pub const fn api_error_code(self) -> &'static str {
        API_CAPABILITY_UNAVAILABLE
    }
}

/// Exact current-PC route policy for the nine P08 remainder capabilities.
///
/// Four capabilities have bounded direct-HWPX subsets. Five stay explicitly unavailable until a
/// lossless native representation is qualified. A direct preflight rejection never widens to an
/// unverified dialog or desktop action after the source has been inspected.
#[derive(Clone, Copy, Eq, PartialEq)]
pub struct ObjectRemainderTargetRouter {
    _qualified: (),
}

impl ObjectRemainderTargetRouter {
    /// Qualifies the exact installed target identity used by this policy.
    ///
    /// # Errors
    ///
    /// Rejects every other build, architecture, locale, or executable digest.
    pub fn qualify(
        build: &str,
        architecture: &str,
        locale: &str,
        executable_sha256: &str,
    ) -> Result<Self, ObjectRemainderTargetRouteError> {
        if build != CURRENT_TARGET_BUILD
            || architecture != CURRENT_TARGET_ARCHITECTURE
            || locale != CURRENT_TARGET_LOCALE
            || executable_sha256 != OBJECT_REMAINDER_CURRENT_TARGET_EXECUTABLE_SHA256
        {
            return Err(ObjectRemainderTargetRouteError::TargetProfileMismatch);
        }
        Ok(Self { _qualified: () })
    }

    #[must_use]
    pub const fn profile_id(self) -> &'static str {
        OBJECT_REMAINDER_CURRENT_TARGET_PROFILE_ID
    }

    /// Selects a qualified direct route or returns a stable no-effect reason.
    ///
    /// # Errors
    ///
    /// Returns `CAPABILITY_UNAVAILABLE_FOR_TARGET` for every rejected or unqualified route.
    pub fn route(
        self,
        capability: ObjectRemainderCapability,
        object_kind: ObjectPropertyKind,
        direct_admission: ObjectRemainderDirectAdmission,
    ) -> Result<ObjectRemainderTargetRoute, ObjectRemainderTargetRouteError> {
        match capability {
            ObjectRemainderCapability::DrawingGallery => {
                Err(ObjectRemainderTargetRouteError::DrawingGalleryTemplateUnqualified)
            }
            ObjectRemainderCapability::FormObjectInsert => {
                Err(ObjectRemainderTargetRouteError::FormInsertionStateIncomplete)
            }
            ObjectRemainderCapability::CaptionInsert => {
                Err(ObjectRemainderTargetRouteError::CaptionInsertionUnqualified)
            }
            ObjectRemainderCapability::ParagraphBandObject => {
                Err(ObjectRemainderTargetRouteError::ParagraphBandNativeConstructUnqualified)
            }
            ObjectRemainderCapability::AspectLock => {
                Err(ObjectRemainderTargetRouteError::AspectLockNativeFieldUnqualified)
            }
            ObjectRemainderCapability::MarginCaption | ObjectRemainderCapability::AltText => {
                match object_kind {
                    ObjectPropertyKind::ParagraphBand => {
                        Err(ObjectRemainderTargetRouteError::ObjectKindOutOfScope)
                    }
                    _ => direct_route(direct_admission),
                }
            }
            ObjectRemainderCapability::ImageProperties => {
                if object_kind == ObjectPropertyKind::Picture {
                    direct_route(direct_admission)
                } else {
                    Err(ObjectRemainderTargetRouteError::ObjectKindOutOfScope)
                }
            }
            ObjectRemainderCapability::Printable => {
                if object_kind == ObjectPropertyKind::FormObject {
                    direct_route(direct_admission)
                } else {
                    Err(ObjectRemainderTargetRouteError::ObjectKindOutOfScope)
                }
            }
        }
    }
}

const fn direct_route(
    admission: ObjectRemainderDirectAdmission,
) -> Result<ObjectRemainderTargetRoute, ObjectRemainderTargetRouteError> {
    match admission {
        ObjectRemainderDirectAdmission::Eligible => Ok(ObjectRemainderTargetRoute::DirectHwpx),
        ObjectRemainderDirectAdmission::Rejected => {
            Err(ObjectRemainderTargetRouteError::DirectProfileRejected)
        }
    }
}

impl fmt::Debug for ObjectRemainderTargetRouter {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("ObjectRemainderTargetRouter(<exact-target-qualified>)")
    }
}
