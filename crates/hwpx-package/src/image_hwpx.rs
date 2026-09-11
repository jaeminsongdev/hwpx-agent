use std::collections::BTreeSet;
use std::fmt::Write as _;
use std::fmt::{self, Debug};
use std::io::{Read, Seek};

use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{
    AssetDisposition, AssetError, AssetLimits, AssetMedia, AssetPlan, AssetStoreAdapter,
    BoundedZipReader, GraphError, IdIndexLimits, IdRuleProfile, PackageError, PackageGraph,
    PackageGraphLimits, PackageLimits, PackagePath, PartRole, PatchError, PatchIntent, PatchLimits,
    PatchPartDisposition, PatchResult, PreservingPatchEngine, PreservingXmlDocument,
    PreservingXmlError, RelationshipKind, SiblingPosition, ValidatedXmlFragment,
    XmlElementSelector, XmlElementToken,
};

pub const IMAGE_HWPX_SCHEMA_VERSION: &str = "hwpx-agent.image-hwpx/v1";
pub const IMAGE_HWPX_PROFILE_ID: &str = "hwpx-agent.image-hwpx.hwpml-2011-static-embed/v1";

const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const SECTION_NS: &str = "http://www.hancom.co.kr/hwpml/2011/section";
const OPF_NS: &str = "http://www.idpf.org/2007/opf";
const HWPUNIT_PER_INCH: u64 = 7_200;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ImageHwpxLimitConfig {
    pub section_bytes: usize,
    pub elements: usize,
    pub pictures: usize,
    pub serialized_bytes: usize,
    pub extent_hwpunit: u32,
    pub object_id: u32,
    pub instance_id: u32,
    pub dpi: u32,
    pub alt_text_bytes: usize,
}

impl Default for ImageHwpxLimitConfig {
    fn default() -> Self {
        Self {
            section_bytes: 32 * 1024 * 1024,
            elements: 1_000_000,
            pictures: 65_536,
            serialized_bytes: 16 * 1024 * 1024,
            extent_hwpunit: 10_000_000,
            object_id: u32::MAX - 1,
            instance_id: u32::MAX - 1,
            dpi: 2_400,
            alt_text_bytes: 4 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct ImageHwpxLimits {
    native: ImageHwpxLimitConfig,
    pub package: PackageLimits,
    pub graph: PackageGraphLimits,
    pub ids: IdIndexLimits,
    pub patch: PatchLimits,
    pub asset: AssetLimits,
}

impl ImageHwpxLimits {
    pub const HARD_MAX_SECTION_BYTES: usize = 128 * 1024 * 1024;
    pub const HARD_MAX_ELEMENTS: usize = 2_000_000;
    pub const HARD_MAX_PICTURES: usize = 262_144;
    pub const HARD_MAX_SERIALIZED_BYTES: usize = 32 * 1024 * 1024;
    pub const HARD_MAX_EXTENT_HWPUNIT: u32 = 100_000_000;
    pub const HARD_MAX_DPI: u32 = 100_000;
    pub const HARD_MAX_ALT_TEXT_BYTES: usize = 64 * 1024;

    /// Creates the finite static-picture limits without silently clamping caller values.
    ///
    /// # Errors
    ///
    /// Returns a stable invalid-limit error for any zero or hard-ceiling violation.
    pub fn new(
        native: ImageHwpxLimitConfig,
        package: PackageLimits,
        graph: PackageGraphLimits,
        ids: IdIndexLimits,
        patch: PatchLimits,
        asset: AssetLimits,
    ) -> Result<Self, ImageHwpxError> {
        if native.section_bytes == 0
            || native.section_bytes > Self::HARD_MAX_SECTION_BYTES
            || native.elements == 0
            || native.elements > Self::HARD_MAX_ELEMENTS
            || native.pictures == 0
            || native.pictures > Self::HARD_MAX_PICTURES
            || native.serialized_bytes == 0
            || native.serialized_bytes > Self::HARD_MAX_SERIALIZED_BYTES
            || native.extent_hwpunit == 0
            || native.extent_hwpunit > Self::HARD_MAX_EXTENT_HWPUNIT
            || native.object_id == 0
            || native.instance_id == 0
            || native.dpi == 0
            || native.dpi > Self::HARD_MAX_DPI
            || native.alt_text_bytes == 0
            || native.alt_text_bytes > Self::HARD_MAX_ALT_TEXT_BYTES
        {
            return Err(ImageHwpxError::InvalidLimit);
        }
        Ok(Self {
            native,
            package,
            graph,
            ids,
            patch,
            asset,
        })
    }

    #[must_use]
    pub const fn config(self) -> ImageHwpxLimitConfig {
        self.native
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ImageLinkMode {
    Embed,
    Link,
    PackageRelationship,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ImageCrop {
    pub left_px: u32,
    pub top_px: u32,
    pub right_px: u32,
    pub bottom_px: u32,
}

impl ImageCrop {
    #[must_use]
    pub const fn full(width_px: u32, height_px: u32) -> Self {
        Self {
            left_px: 0,
            top_px: 0,
            right_px: width_px,
            bottom_px: height_px,
        }
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ImageGeometry {
    pub width_hwpunit: u32,
    pub height_hwpunit: u32,
    pub dpi_x: u32,
    pub dpi_y: u32,
    pub crop: ImageCrop,
    pub render_required: bool,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ImageAssetBinding {
    disposition: AssetDisposition,
    media: AssetMedia,
    plan_sha256: String,
    source_graph_sha256: String,
    content_sha256: String,
    relationship_id: String,
    target_path: String,
    width_px: u32,
    height_px: u32,
}

impl ImageAssetBinding {
    #[must_use]
    pub fn from_plan(plan: &AssetPlan) -> Self {
        Self {
            disposition: plan.disposition(),
            media: plan.media(),
            plan_sha256: plan.plan_sha256().to_owned(),
            source_graph_sha256: plan.source_graph_sha256().to_owned(),
            content_sha256: plan.content_sha256().to_owned(),
            relationship_id: plan.relationship_id().to_owned(),
            target_path: plan.target_path().as_str().to_owned(),
            width_px: plan.width_px(),
            height_px: plan.height_px(),
        }
    }

    #[must_use]
    pub const fn disposition(&self) -> AssetDisposition {
        self.disposition
    }

    #[must_use]
    pub const fn media(&self) -> AssetMedia {
        self.media
    }

    #[must_use]
    pub fn relationship_id(&self) -> &str {
        &self.relationship_id
    }

    #[must_use]
    pub fn target_path(&self) -> &str {
        &self.target_path
    }

    #[must_use]
    pub fn content_sha256(&self) -> &str {
        &self.content_sha256
    }

    #[must_use]
    pub const fn width_px(&self) -> u32 {
        self.width_px
    }

    #[must_use]
    pub const fn height_px(&self) -> u32 {
        self.height_px
    }
}

impl Debug for ImageAssetBinding {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ImageAssetBinding")
            .field("disposition", &self.disposition)
            .field("media", &self.media)
            .field("identity", &"<redacted>")
            .field("width_px", &self.width_px)
            .field("height_px", &self.height_px)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ImageHwpxRequestDraft {
    pub schema_version: String,
    pub profile_id: String,
    pub section_part: String,
    pub paragraph_ordinal: usize,
    pub run_ordinal: usize,
    pub expected_package_state_sha256: String,
    pub expected_section_sha256: String,
    pub expected_paragraph_sha256: String,
    pub expected_run_sha256: String,
    pub expected_object_ids_sha256: String,
    pub expected_instance_ids_sha256: String,
    pub expected_document_flow_sha256: String,
    pub target_document_flow_sha256: String,
    pub object_id: u32,
    pub instance_id: u32,
    pub link_mode: ImageLinkMode,
    pub geometry: ImageGeometry,
    pub alt_text: String,
    pub asset: ImageAssetBinding,
}

impl Debug for ImageHwpxRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ImageHwpxRequestDraft")
            .field("schema_version", &self.schema_version)
            .field("profile_id", &self.profile_id)
            .field("section_part", &"<redacted>")
            .field("paragraph_ordinal", &self.paragraph_ordinal)
            .field("run_ordinal", &self.run_ordinal)
            .field("bindings", &"<redacted>")
            .field("object_id", &"<redacted>")
            .field("instance_id", &"<redacted>")
            .field("link_mode", &self.link_mode)
            .field("geometry", &"<redacted>")
            .field("alt_text", &"<redacted>")
            .field("asset", &self.asset)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ImageHwpxSource {
    profile_id: &'static str,
    section_part: String,
    paragraph_ordinal: usize,
    run_ordinal: usize,
    package_state_sha256: String,
    section_sha256: String,
    paragraph_sha256: String,
    run_sha256: String,
    object_ids_sha256: String,
    instance_ids_sha256: String,
    object_id_count: usize,
    instance_id_count: usize,
    section_object_count: usize,
    section_instance_count: usize,
    picture_count: usize,
}

impl ImageHwpxSource {
    #[must_use]
    pub fn section_part(&self) -> &str {
        &self.section_part
    }

    #[must_use]
    pub fn package_state_sha256(&self) -> &str {
        &self.package_state_sha256
    }

    #[must_use]
    pub fn section_sha256(&self) -> &str {
        &self.section_sha256
    }

    #[must_use]
    pub fn paragraph_sha256(&self) -> &str {
        &self.paragraph_sha256
    }

    #[must_use]
    pub fn run_sha256(&self) -> &str {
        &self.run_sha256
    }

    #[must_use]
    pub fn object_ids_sha256(&self) -> &str {
        &self.object_ids_sha256
    }

    #[must_use]
    pub fn instance_ids_sha256(&self) -> &str {
        &self.instance_ids_sha256
    }

    #[must_use]
    pub const fn object_id_count(&self) -> usize {
        self.object_id_count
    }

    #[must_use]
    pub const fn instance_id_count(&self) -> usize {
        self.instance_id_count
    }

    #[must_use]
    pub const fn section_instance_count(&self) -> usize {
        self.section_instance_count
    }

    #[must_use]
    pub const fn picture_count(&self) -> usize {
        self.picture_count
    }

    /// Serializes the complete source binding without exposing source XML.
    ///
    /// # Errors
    ///
    /// Returns an output-limit or serialization error.
    pub fn canonical_json(&self, limits: ImageHwpxLimits) -> Result<Vec<u8>, ImageHwpxError> {
        bounded_json(self, &limits)
    }
}

impl Debug for ImageHwpxSource {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ImageHwpxSource")
            .field("profile_id", &self.profile_id)
            .field("section_part", &"<redacted>")
            .field("paragraph_ordinal", &self.paragraph_ordinal)
            .field("run_ordinal", &self.run_ordinal)
            .field("bindings", &"<redacted>")
            .field("object_id_count", &self.object_id_count)
            .field("instance_id_count", &self.instance_id_count)
            .field("section_object_count", &self.section_object_count)
            .field("section_instance_count", &self.section_instance_count)
            .field("picture_count", &self.picture_count)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ImageHwpxRequest {
    schema_version: &'static str,
    profile_id: &'static str,
    section_part: String,
    paragraph_ordinal: usize,
    run_ordinal: usize,
    expected_package_state_sha256: String,
    expected_section_sha256: String,
    expected_paragraph_sha256: String,
    expected_run_sha256: String,
    expected_object_ids_sha256: String,
    expected_instance_ids_sha256: String,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    object_id: u32,
    instance_id: u32,
    link_mode: ImageLinkMode,
    geometry: ImageGeometry,
    alt_text: String,
    asset: ImageAssetBinding,
    #[serde(skip_serializing)]
    asset_plan: AssetPlan,
}

impl ImageHwpxRequest {
    /// Admits a request only when source, flow, asset, crop, resolution and object identities agree.
    ///
    /// # Errors
    ///
    /// Rejects unsupported link modes, stale bindings, invalid geometry/alt text and ID collisions.
    pub fn from_draft(
        draft: ImageHwpxRequestDraft,
        source: &ImageHwpxSource,
        asset_plan: &AssetPlan,
        current_document_flow_sha256: &str,
        limits: ImageHwpxLimits,
    ) -> Result<Self, ImageHwpxError> {
        if draft.schema_version != IMAGE_HWPX_SCHEMA_VERSION {
            return Err(ImageHwpxError::UnsupportedVersion);
        }
        if draft.profile_id != IMAGE_HWPX_PROFILE_ID {
            return Err(ImageHwpxError::UnsupportedProfile);
        }
        if draft.link_mode != ImageLinkMode::Embed {
            return Err(ImageHwpxError::UnsupportedLinkMode);
        }
        for digest in [
            &draft.expected_package_state_sha256,
            &draft.expected_section_sha256,
            &draft.expected_paragraph_sha256,
            &draft.expected_run_sha256,
            &draft.expected_object_ids_sha256,
            &draft.expected_instance_ids_sha256,
            &draft.expected_document_flow_sha256,
            &draft.target_document_flow_sha256,
            &draft.asset.plan_sha256,
            &draft.asset.source_graph_sha256,
            &draft.asset.content_sha256,
            current_document_flow_sha256,
        ] {
            require_digest(digest)?;
        }
        if draft.object_id == 0
            || draft.object_id > limits.native.object_id
            || draft.instance_id == 0
            || draft.instance_id > limits.native.instance_id
            || draft.object_id == draft.instance_id
        {
            return Err(ImageHwpxError::InvalidObjectId);
        }
        validate_alt_text(&draft.alt_text, &limits)?;
        validate_geometry(&draft.geometry, &draft.asset, &limits)?;
        if draft.asset != ImageAssetBinding::from_plan(asset_plan) {
            return Err(ImageHwpxError::AssetDrift);
        }
        let request = Self {
            schema_version: IMAGE_HWPX_SCHEMA_VERSION,
            profile_id: IMAGE_HWPX_PROFILE_ID,
            section_part: draft.section_part,
            paragraph_ordinal: draft.paragraph_ordinal,
            run_ordinal: draft.run_ordinal,
            expected_package_state_sha256: draft.expected_package_state_sha256,
            expected_section_sha256: draft.expected_section_sha256,
            expected_paragraph_sha256: draft.expected_paragraph_sha256,
            expected_run_sha256: draft.expected_run_sha256,
            expected_object_ids_sha256: draft.expected_object_ids_sha256,
            expected_instance_ids_sha256: draft.expected_instance_ids_sha256,
            expected_document_flow_sha256: draft.expected_document_flow_sha256,
            target_document_flow_sha256: draft.target_document_flow_sha256,
            object_id: draft.object_id,
            instance_id: draft.instance_id,
            link_mode: draft.link_mode,
            geometry: draft.geometry,
            alt_text: draft.alt_text,
            asset: draft.asset,
            asset_plan: asset_plan.clone(),
        };
        validate_request_source(&request, source, current_document_flow_sha256)?;
        let _ = request.canonical_json(limits)?;
        Ok(request)
    }

    /// Parses strict duplicate-free request JSON and applies [`Self::from_draft`].
    ///
    /// # Errors
    ///
    /// Rejects empty, oversized, malformed, duplicated, unknown or drifted input.
    pub fn from_json(
        bytes: &[u8],
        source: &ImageHwpxSource,
        asset_plan: &AssetPlan,
        current_document_flow_sha256: &str,
        limits: ImageHwpxLimits,
    ) -> Result<Self, ImageHwpxError> {
        if bytes.is_empty() || bytes.len() > limits.native.serialized_bytes {
            return Err(ImageHwpxError::InputLimit);
        }
        reject_duplicate_json_keys(bytes)?;
        let draft = serde_json::from_slice(bytes).map_err(|_| ImageHwpxError::InvalidJson)?;
        Self::from_draft(
            draft,
            source,
            asset_plan,
            current_document_flow_sha256,
            limits,
        )
    }

    #[must_use]
    pub const fn object_id(&self) -> u32 {
        self.object_id
    }

    #[must_use]
    pub const fn instance_id(&self) -> u32 {
        self.instance_id
    }

    #[must_use]
    pub const fn geometry(&self) -> &ImageGeometry {
        &self.geometry
    }

    #[must_use]
    pub const fn asset(&self) -> &ImageAssetBinding {
        &self.asset
    }

    #[must_use]
    pub fn target_document_flow_sha256(&self) -> &str {
        &self.target_document_flow_sha256
    }

    /// Serializes all non-payload request fields deterministically within the configured bound.
    ///
    /// # Errors
    ///
    /// Returns an output-limit or serialization error.
    pub fn canonical_json(&self, limits: ImageHwpxLimits) -> Result<Vec<u8>, ImageHwpxError> {
        bounded_json(self, &limits)
    }
}

impl Debug for ImageHwpxRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ImageHwpxRequest")
            .field("schema_version", &self.schema_version)
            .field("profile_id", &self.profile_id)
            .field("section_part", &"<redacted>")
            .field("paragraph_ordinal", &self.paragraph_ordinal)
            .field("run_ordinal", &self.run_ordinal)
            .field("bindings", &"<redacted>")
            .field("object_id", &"<redacted>")
            .field("instance_id", &"<redacted>")
            .field("link_mode", &self.link_mode)
            .field("geometry", &"<redacted>")
            .field("alt_text", &"<redacted>")
            .field("asset", &self.asset)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ImageHwpxReadback {
    profile_id: &'static str,
    object_id: u32,
    instance_id: u32,
    link_mode: ImageLinkMode,
    geometry: ImageGeometry,
    alt_text: String,
    asset: ImageAssetBinding,
    picture_ordinal: usize,
    native_object_count: usize,
    native_instance_count: usize,
    picture_count: usize,
    render_required: bool,
}

impl ImageHwpxReadback {
    #[must_use]
    pub const fn object_id(&self) -> u32 {
        self.object_id
    }

    #[must_use]
    pub const fn instance_id(&self) -> u32 {
        self.instance_id
    }

    #[must_use]
    pub const fn geometry(&self) -> &ImageGeometry {
        &self.geometry
    }

    #[must_use]
    pub const fn asset(&self) -> &ImageAssetBinding {
        &self.asset
    }

    #[must_use]
    pub const fn native_object_count(&self) -> usize {
        self.native_object_count
    }

    #[must_use]
    pub const fn native_instance_count(&self) -> usize {
        self.native_instance_count
    }

    #[must_use]
    pub const fn picture_count(&self) -> usize {
        self.picture_count
    }

    /// Serializes the complete strict static readback within the configured bound.
    ///
    /// # Errors
    ///
    /// Returns an output-limit or serialization error.
    pub fn canonical_json(&self, limits: ImageHwpxLimits) -> Result<Vec<u8>, ImageHwpxError> {
        bounded_json(self, &limits)
    }
}

impl Debug for ImageHwpxReadback {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ImageHwpxReadback")
            .field("profile_id", &self.profile_id)
            .field("identifiers", &"<redacted>")
            .field("link_mode", &self.link_mode)
            .field("geometry", &"<redacted>")
            .field("alt_text", &"<redacted>")
            .field("asset", &self.asset)
            .field("picture_ordinal", &self.picture_ordinal)
            .field("native_object_count", &self.native_object_count)
            .field("native_instance_count", &self.native_instance_count)
            .field("picture_count", &self.picture_count)
            .field("render_required", &self.render_required)
            .finish_non_exhaustive()
    }
}

#[allow(clippy::struct_excessive_bools)]
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ImageHwpxLoweringReceipt {
    profile_id: &'static str,
    request_sha256: String,
    source_package_state_sha256: String,
    source_section_sha256: String,
    output_section_sha256: String,
    source_paragraph_sha256: String,
    source_run_sha256: String,
    source_object_ids_sha256: String,
    source_instance_ids_sha256: String,
    asset_plan_sha256: String,
    asset_content_sha256: String,
    relationship_id_sha256: String,
    target_path_sha256: String,
    object_id: u32,
    instance_id: u32,
    source_picture_count: usize,
    output_picture_count: usize,
    source_instance_count: usize,
    output_instance_count: usize,
    changed_parts: usize,
    added_parts: usize,
    untouched_parts: usize,
    preservation_verified: bool,
    static_readback_verified: bool,
    relationship_closure_verified: bool,
    render_required: bool,
    before_document_flow_sha256: String,
    after_document_flow_sha256: String,
}

impl ImageHwpxLoweringReceipt {
    #[must_use]
    pub const fn preservation_verified(&self) -> bool {
        self.preservation_verified
    }

    #[must_use]
    pub const fn static_readback_verified(&self) -> bool {
        self.static_readback_verified
    }

    #[must_use]
    pub const fn relationship_closure_verified(&self) -> bool {
        self.relationship_closure_verified
    }

    #[must_use]
    pub const fn render_required(&self) -> bool {
        self.render_required
    }

    #[must_use]
    pub fn output_section_sha256(&self) -> &str {
        &self.output_section_sha256
    }

    /// Serializes the bounded deterministic lowering receipt.
    ///
    /// # Errors
    ///
    /// Returns an output-limit or serialization error.
    pub fn canonical_json(&self, limits: ImageHwpxLimits) -> Result<Vec<u8>, ImageHwpxError> {
        bounded_json(self, &limits)
    }
}

impl Debug for ImageHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ImageHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field("digests", &"<redacted>")
            .field("identifiers", &"<redacted>")
            .field("source_picture_count", &self.source_picture_count)
            .field("output_picture_count", &self.output_picture_count)
            .field("source_instance_count", &self.source_instance_count)
            .field("output_instance_count", &self.output_instance_count)
            .field("changed_parts", &self.changed_parts)
            .field("added_parts", &self.added_parts)
            .field("untouched_parts", &self.untouched_parts)
            .field("preservation_verified", &self.preservation_verified)
            .field("static_readback_verified", &self.static_readback_verified)
            .field(
                "relationship_closure_verified",
                &self.relationship_closure_verified,
            )
            .field("render_required", &self.render_required)
            .finish_non_exhaustive()
    }
}

pub struct ImageHwpxLowered {
    patch: PatchResult,
    receipt: ImageHwpxLoweringReceipt,
}

impl ImageHwpxLowered {
    #[must_use]
    pub const fn patch(&self) -> &PatchResult {
        &self.patch
    }

    #[must_use]
    pub const fn receipt(&self) -> &ImageHwpxLoweringReceipt {
        &self.receipt
    }

    #[must_use]
    pub fn into_patch(self) -> PatchResult {
        self.patch
    }
}

impl Debug for ImageHwpxLowered {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ImageHwpxLowered")
            .field("patch", &self.patch)
            .field("receipt", &self.receipt)
            .finish()
    }
}

#[derive(Debug)]
pub struct ImageHwpxBuilder;

impl ImageHwpxBuilder {
    /// Inspects one exact empty run and binds all package, object, instance and anchor state.
    ///
    /// # Errors
    ///
    /// Rejects non-spine, stale, ambiguous, non-empty or limit-excessive targets.
    pub fn inspect_source<R: Read + Seek>(
        reader: &mut BoundedZipReader<R>,
        graph: &PackageGraph,
        section_part: &str,
        paragraph_ordinal: usize,
        run_ordinal: usize,
        limits: ImageHwpxLimits,
    ) -> Result<ImageHwpxSource, ImageHwpxError> {
        inspect_bound_source(
            reader,
            graph,
            section_part,
            paragraph_ordinal,
            run_ordinal,
            &limits,
        )
        .map(|bound| bound.source)
    }
}

#[derive(Debug)]
pub struct ImageHwpxReader;

impl ImageHwpxReader {
    /// Strictly reads one static-profile picture control from section XML.
    ///
    /// # Errors
    ///
    /// Rejects unknown attributes/children, geometry, crop, resolution, IDs or asset drift.
    pub fn read_in_section(
        bytes: &[u8],
        picture_ordinal: usize,
        expected_asset: &ImageAssetBinding,
        expected_geometry: &ImageGeometry,
        expected_alt_text: &str,
        limits: ImageHwpxLimits,
    ) -> Result<ImageHwpxReadback, ImageHwpxError> {
        read_image_shape(
            bytes,
            picture_ordinal,
            expected_asset,
            expected_geometry,
            expected_alt_text,
            &limits,
        )
        .map(|shape| shape.readback)
    }
}

#[derive(Debug)]
pub struct ImageHwpxLowerer;

impl ImageHwpxLowerer {
    /// Inserts one static picture and its embedded asset in one preserving package transaction.
    ///
    /// # Errors
    ///
    /// Returns no partial artifact on request/build/source/flow/asset drift, collision, patch,
    /// strict readback, relationship closure or byte-preservation failure.
    #[allow(clippy::too_many_lines)]
    pub fn lower<R: Read + Seek>(
        reader: &mut BoundedZipReader<R>,
        graph: &PackageGraph,
        request: &ImageHwpxRequest,
        current_document_flow_sha256: &str,
        limits: ImageHwpxLimits,
    ) -> Result<ImageHwpxLowered, ImageHwpxError> {
        let bound = inspect_bound_source(
            reader,
            graph,
            &request.section_part,
            request.paragraph_ordinal,
            request.run_ordinal,
            &limits,
        )?;
        validate_request_source(request, &bound.source, current_document_flow_sha256)?;
        if bound.object_ids.contains(&request.object_id)
            || bound.instance_ids.contains(&request.instance_id)
        {
            return Err(ImageHwpxError::ObjectIdCollision);
        }
        if request.asset != ImageAssetBinding::from_plan(&request.asset_plan) {
            return Err(ImageHwpxError::AssetDrift);
        }
        validate_geometry(&request.geometry, &request.asset, &limits)?;
        validate_alt_text(&request.alt_text, &limits)?;

        let original_manifest =
            read_exact_part(reader, graph, graph.package_document.as_str(), &limits)?;
        let mut intents =
            AssetStoreAdapter::new(limits.asset, limits.package, limits.graph, limits.patch)
                .build_patch_intents(&request.asset_plan, graph)?;
        let fragment =
            ValidatedXmlFragment::parse(&image_fragment(request, &limits)?, limits.patch)?;
        let selector =
            XmlElementSelector::bind(&bound.path, &bound.document, bound.target_text_element)?;
        intents.push(PatchIntent::InsertSibling {
            target: selector,
            position: SiblingPosition::Before,
            fragment,
        });
        let expected_intents = match request.asset.disposition {
            AssetDisposition::ReusedExisting => 1,
            AssetDisposition::AddNew => 3,
        };
        if intents.len() != expected_intents {
            return Err(ImageHwpxError::BuildDrift);
        }
        let patch = PreservingPatchEngine::apply_with_limits(
            reader,
            graph,
            limits.graph,
            IdRuleProfile::hwpml_2011_picture_v5(),
            limits.ids,
            limits.patch,
            &intents,
        )?;
        patch.verify_artifact_integrity()?;
        let (expected_changed, expected_added) = match request.asset.disposition {
            AssetDisposition::ReusedExisting => (1, 0),
            AssetDisposition::AddNew => (2, 1),
        };
        if patch.intent_count() != expected_intents
            || patch.changed_parts() != expected_changed
            || patch.added_parts() != expected_added
        {
            return Err(ImageHwpxError::PreservationMismatch);
        }
        let output_section = patch
            .parts
            .iter()
            .find(|part| part.path == bound.path)
            .ok_or(ImageHwpxError::ReadbackMismatch)?;
        let output_shape = read_image_shape(
            &output_section.bytes,
            bound.insertion_picture_ordinal,
            &request.asset,
            &request.geometry,
            &request.alt_text,
            &limits,
        )?;
        if output_shape.readback.object_id != request.object_id
            || output_shape.readback.instance_id != request.instance_id
            || output_shape.readback.asset != request.asset
            || output_shape.readback.geometry != request.geometry
            || output_shape.readback.alt_text != request.alt_text
            || output_shape.readback.picture_count != bound.source.picture_count + 1
            || output_shape.readback.native_object_count != bound.source.section_object_count + 1
            || output_shape.readback.native_instance_count
                != bound.source.section_instance_count + 1
        {
            return Err(ImageHwpxError::ReadbackMismatch);
        }
        let mut restored_section = Vec::with_capacity(bound.bytes.len());
        restored_section
            .extend_from_slice(&output_section.bytes[..output_shape.picture_span.start()]);
        restored_section
            .extend_from_slice(&output_section.bytes[output_shape.picture_span.end()..]);
        if restored_section != bound.bytes {
            return Err(ImageHwpxError::PreservationMismatch);
        }
        verify_output_relationship_and_asset(&patch, &graph.package_document, request, &limits)?;
        verify_manifest_preservation(&patch, &graph.package_document, request, &original_manifest)?;
        verify_unrelated_parts(&patch, &bound.path, graph, request)?;

        let receipt = ImageHwpxLoweringReceipt {
            profile_id: IMAGE_HWPX_PROFILE_ID,
            request_sha256: hex(Sha256::digest(request.canonical_json(limits)?).into()),
            source_package_state_sha256: bound.source.package_state_sha256.clone(),
            source_section_sha256: bound.source.section_sha256.clone(),
            output_section_sha256: hex(Sha256::digest(&output_section.bytes).into()),
            source_paragraph_sha256: bound.source.paragraph_sha256.clone(),
            source_run_sha256: bound.source.run_sha256.clone(),
            source_object_ids_sha256: bound.source.object_ids_sha256.clone(),
            source_instance_ids_sha256: bound.source.instance_ids_sha256.clone(),
            asset_plan_sha256: request.asset.plan_sha256.clone(),
            asset_content_sha256: request.asset.content_sha256.clone(),
            relationship_id_sha256: hex(
                Sha256::digest(request.asset.relationship_id.as_bytes()).into()
            ),
            target_path_sha256: hex(Sha256::digest(request.asset.target_path.as_bytes()).into()),
            object_id: request.object_id,
            instance_id: request.instance_id,
            source_picture_count: bound.source.picture_count,
            output_picture_count: output_shape.readback.picture_count,
            source_instance_count: bound.source.section_instance_count,
            output_instance_count: output_shape.readback.native_instance_count,
            changed_parts: patch.changed_parts(),
            added_parts: patch.added_parts(),
            untouched_parts: patch.untouched_parts(),
            preservation_verified: true,
            static_readback_verified: true,
            relationship_closure_verified: true,
            render_required: true,
            before_document_flow_sha256: request.expected_document_flow_sha256.clone(),
            after_document_flow_sha256: request.target_document_flow_sha256.clone(),
        };
        let _ = receipt.canonical_json(limits)?;
        Ok(ImageHwpxLowered { patch, receipt })
    }
}

#[derive(Debug, Error)]
pub enum ImageHwpxError {
    #[error("image HWPX limit configuration is invalid")]
    InvalidLimit,
    #[error("image HWPX input is empty or exceeds its finite bound")]
    InputLimit,
    #[error("image HWPX JSON is malformed, duplicated, or not strict")]
    InvalidJson,
    #[error("image HWPX request schema is unsupported")]
    UnsupportedVersion,
    #[error("image HWPX profile is unsupported")]
    UnsupportedProfile,
    #[error("linked image modes are outside the static embedded profile")]
    UnsupportedLinkMode,
    #[error("image HWPX digest binding is invalid")]
    InvalidBinding,
    #[error("image HWPX source state drifted")]
    SourceDrift,
    #[error("image HWPX document flow drifted")]
    FlowDrift,
    #[error("image HWPX insertion target has an unsupported shape")]
    UnsupportedTarget,
    #[error("image HWPX object or instance identifier is invalid")]
    InvalidObjectId,
    #[error("image HWPX object or instance identifier collides")]
    ObjectIdCollision,
    #[error("image HWPX asset binding drifted")]
    AssetDrift,
    #[error("image HWPX crop, resolution, or extent is invalid")]
    InvalidGeometry,
    #[error("image HWPX alternate text is invalid")]
    InvalidAltText,
    #[error("image HWPX request and build products drifted")]
    BuildDrift,
    #[error("image HWPX output failed strict static readback")]
    ReadbackMismatch,
    #[error("image HWPX relationship or embedded part is not closed")]
    RelationshipMismatch,
    #[error("image HWPX patch modified bytes outside the intended object/relationship/asset")]
    PreservationMismatch,
    #[error("image HWPX result exceeds its finite bound")]
    OutputLimit,
    #[error("image HWPX result serialization failed")]
    Serialization,
    #[error("image HWPX allocation failed")]
    Allocation,
    #[error("bounded package read failed")]
    Package(#[from] PackageError),
    #[error("closed package graph validation failed")]
    Graph(#[from] GraphError),
    #[error("embedded asset pipeline failed")]
    Asset(#[from] AssetError),
    #[error("preserving XML validation failed")]
    Xml(#[from] PreservingXmlError),
    #[error("preserving package patch failed")]
    Patch(#[from] PatchError),
}

impl ImageHwpxError {
    #[must_use]
    pub fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "image_hwpx_invalid_limit",
            Self::InputLimit => "image_hwpx_input_limit",
            Self::InvalidJson => "image_hwpx_invalid_json",
            Self::UnsupportedVersion => "image_hwpx_unsupported_version",
            Self::UnsupportedProfile => "image_hwpx_unsupported_profile",
            Self::UnsupportedLinkMode => "image_hwpx_unsupported_link_mode",
            Self::InvalidBinding => "image_hwpx_invalid_binding",
            Self::SourceDrift => "image_hwpx_source_drift",
            Self::FlowDrift => "image_hwpx_flow_drift",
            Self::UnsupportedTarget => "image_hwpx_unsupported_target",
            Self::InvalidObjectId => "image_hwpx_invalid_object_id",
            Self::ObjectIdCollision => "image_hwpx_object_id_collision",
            Self::AssetDrift => "image_hwpx_asset_drift",
            Self::InvalidGeometry => "image_hwpx_invalid_geometry",
            Self::InvalidAltText => "image_hwpx_invalid_alt_text",
            Self::BuildDrift => "image_hwpx_build_drift",
            Self::ReadbackMismatch => "image_hwpx_readback_mismatch",
            Self::RelationshipMismatch => "image_hwpx_relationship_mismatch",
            Self::PreservationMismatch => "image_hwpx_preservation_mismatch",
            Self::OutputLimit => "image_hwpx_output_limit",
            Self::Serialization => "image_hwpx_serialization",
            Self::Allocation => "image_hwpx_allocation",
            Self::Package(error) => error.code(),
            Self::Graph(error) => error.code(),
            Self::Asset(error) => error.code(),
            Self::Xml(error) => error.code(),
            Self::Patch(error) => error.code(),
        }
    }
}

struct BoundSource {
    source: ImageHwpxSource,
    path: PackagePath,
    bytes: Vec<u8>,
    document: PreservingXmlDocument,
    target_text_element: usize,
    insertion_picture_ordinal: usize,
    object_ids: BTreeSet<u32>,
    instance_ids: BTreeSet<u32>,
}

struct ImageShape {
    readback: ImageHwpxReadback,
    picture_span: crate::XmlByteSpan,
}

fn inspect_bound_source<R: Read + Seek>(
    reader: &mut BoundedZipReader<R>,
    graph: &PackageGraph,
    section_part: &str,
    paragraph_ordinal: usize,
    run_ordinal: usize,
    limits: &ImageHwpxLimits,
) -> Result<BoundSource, ImageHwpxError> {
    let (path, bytes) = read_spine_part(reader, graph, section_part, limits)?;
    let document = parse_section(&bytes, limits)?;
    let root = element(&document, document.root_element())?;
    if root.name().namespace() != Some(SECTION_NS) || root.name().local_name() != "sec" {
        return Err(ImageHwpxError::UnsupportedTarget);
    }
    let paragraphs = direct_children_named(&document, document.root_element(), "p")?;
    let paragraph = *paragraphs
        .get(paragraph_ordinal)
        .ok_or(ImageHwpxError::UnsupportedTarget)?;
    let runs = direct_children_named(&document, paragraph, "run")?;
    let run = *runs
        .get(run_ordinal)
        .ok_or(ImageHwpxError::UnsupportedTarget)?;
    let run_children = child_indexes(&document, run)?;
    if run_children.len() != 1
        || !has_name(element(&document, run_children[0])?, "t")
        || !element(&document, run_children[0])?.is_empty()
    {
        return Err(ImageHwpxError::UnsupportedTarget);
    }
    let (section_ids, section_instances, section_picture_count) =
        object_and_instance_ids(&document, limits)?;
    let (object_ids, instance_ids) = package_object_and_instance_ids(reader, graph, limits)?;
    let insertion_picture_ordinal = document
        .elements()
        .iter()
        .take(run_children[0])
        .filter(|candidate| has_name(candidate, "pic"))
        .count();
    let paragraph_span = element(&document, paragraph)?
        .outer_span()
        .ok_or(ImageHwpxError::UnsupportedTarget)?;
    let run_span = element(&document, run)?
        .outer_span()
        .ok_or(ImageHwpxError::UnsupportedTarget)?;
    let source = ImageHwpxSource {
        profile_id: IMAGE_HWPX_PROFILE_ID,
        section_part: path.as_str().to_owned(),
        paragraph_ordinal,
        run_ordinal,
        package_state_sha256: package_state_sha256(graph),
        section_sha256: hex(Sha256::digest(&bytes).into()),
        paragraph_sha256: hex(
            Sha256::digest(document.source_text(paragraph_span)?.as_bytes()).into(),
        ),
        run_sha256: hex(Sha256::digest(document.source_text(run_span)?.as_bytes()).into()),
        object_ids_sha256: id_set_sha256("object-ids", &object_ids),
        instance_ids_sha256: id_set_sha256("instance-ids", &instance_ids),
        object_id_count: object_ids.len(),
        instance_id_count: instance_ids.len(),
        section_object_count: section_ids.len(),
        section_instance_count: section_instances.len(),
        picture_count: section_picture_count,
    };
    Ok(BoundSource {
        source,
        path,
        bytes,
        document,
        target_text_element: run_children[0],
        insertion_picture_ordinal,
        object_ids,
        instance_ids,
    })
}

fn package_object_and_instance_ids<R: Read + Seek>(
    reader: &mut BoundedZipReader<R>,
    graph: &PackageGraph,
    limits: &ImageHwpxLimits,
) -> Result<(BTreeSet<u32>, BTreeSet<u32>), ImageHwpxError> {
    let paths = graph
        .spine
        .iter()
        .map(|path| path.as_str().to_owned())
        .collect::<Vec<_>>();
    let mut object_ids = BTreeSet::new();
    let mut instance_ids = BTreeSet::new();
    for path in paths {
        let (_, bytes) = read_spine_part(reader, graph, &path, limits)?;
        let document = parse_section(&bytes, limits)?;
        let (part_objects, part_instances, _) = object_and_instance_ids(&document, limits)?;
        for id in part_objects {
            if !object_ids.insert(id) {
                return Err(ImageHwpxError::ObjectIdCollision);
            }
        }
        for id in part_instances {
            if !instance_ids.insert(id) {
                return Err(ImageHwpxError::ObjectIdCollision);
            }
        }
        if object_ids.len() > limits.native.pictures || instance_ids.len() > limits.native.pictures
        {
            return Err(ImageHwpxError::InputLimit);
        }
    }
    Ok((object_ids, instance_ids))
}

fn object_and_instance_ids(
    document: &PreservingXmlDocument,
    limits: &ImageHwpxLimits,
) -> Result<(BTreeSet<u32>, BTreeSet<u32>, usize), ImageHwpxError> {
    let object_names = [
        "equation",
        "tbl",
        "pic",
        "rect",
        "ellipse",
        "line",
        "arc",
        "polygon",
        "curve",
        "connectLine",
        "container",
        "ole",
        "video",
    ];
    let mut object_ids = BTreeSet::new();
    let mut instance_ids = BTreeSet::new();
    let mut picture_count = 0;
    for candidate in document.elements() {
        if has_name(candidate, "pic") {
            picture_count += 1;
        }
        if candidate.name().namespace() == Some(PARAGRAPH_NS)
            && object_names.contains(&candidate.name().local_name())
        {
            let object_id = parse_u32(attr(candidate, "id")?)?;
            if object_id == 0 || !object_ids.insert(object_id) {
                return Err(ImageHwpxError::ObjectIdCollision);
            }
            if let Some(instance_id) = optional_attr(candidate, "instid")? {
                let instance_id = parse_u32(instance_id)?;
                if instance_id == 0 || !instance_ids.insert(instance_id) {
                    return Err(ImageHwpxError::ObjectIdCollision);
                }
            }
        }
        if object_ids.len() > limits.native.pictures
            || instance_ids.len() > limits.native.pictures
            || picture_count > limits.native.pictures
        {
            return Err(ImageHwpxError::InputLimit);
        }
    }
    Ok((object_ids, instance_ids, picture_count))
}

fn read_spine_part<R: Read + Seek>(
    reader: &mut BoundedZipReader<R>,
    graph: &PackageGraph,
    section_part: &str,
    limits: &ImageHwpxLimits,
) -> Result<(PackagePath, Vec<u8>), ImageHwpxError> {
    let path = PackagePath::parse(section_part.as_bytes(), 0, limits.package)?;
    let record = graph
        .parts
        .iter()
        .find(|record| record.path == path)
        .ok_or(ImageHwpxError::UnsupportedTarget)?;
    if record.role != PartRole::SpineDocument || !graph.spine.iter().any(|value| value == &path) {
        return Err(ImageHwpxError::UnsupportedTarget);
    }
    let bytes = read_exact_part(reader, graph, path.as_str(), limits)?;
    Ok((path, bytes))
}

fn read_exact_part<R: Read + Seek>(
    reader: &mut BoundedZipReader<R>,
    graph: &PackageGraph,
    part: &str,
    limits: &ImageHwpxLimits,
) -> Result<Vec<u8>, ImageHwpxError> {
    let record = graph
        .parts
        .iter()
        .find(|record| record.path.as_str() == part)
        .ok_or(ImageHwpxError::SourceDrift)?;
    let entry = reader
        .entries()
        .iter()
        .find(|entry| entry.path == record.path)
        .map(|entry| entry.index)
        .ok_or(ImageHwpxError::SourceDrift)?;
    let bytes = reader.read_entry(entry)?;
    if bytes.len() > limits.native.section_bytes
        || <[u8; 32]>::from(Sha256::digest(&bytes)) != record.raw_sha256
    {
        return Err(ImageHwpxError::SourceDrift);
    }
    Ok(bytes)
}

fn validate_request_source(
    request: &ImageHwpxRequest,
    source: &ImageHwpxSource,
    current_document_flow_sha256: &str,
) -> Result<(), ImageHwpxError> {
    require_digest(current_document_flow_sha256)?;
    if request.section_part != source.section_part
        || request.paragraph_ordinal != source.paragraph_ordinal
        || request.run_ordinal != source.run_ordinal
        || request.expected_package_state_sha256 != source.package_state_sha256
        || request.expected_section_sha256 != source.section_sha256
        || request.expected_paragraph_sha256 != source.paragraph_sha256
        || request.expected_run_sha256 != source.run_sha256
        || request.expected_object_ids_sha256 != source.object_ids_sha256
        || request.expected_instance_ids_sha256 != source.instance_ids_sha256
    {
        return Err(ImageHwpxError::SourceDrift);
    }
    if request.expected_document_flow_sha256 != current_document_flow_sha256
        || request.expected_document_flow_sha256 == request.target_document_flow_sha256
    {
        return Err(ImageHwpxError::FlowDrift);
    }
    Ok(())
}

fn validate_geometry(
    geometry: &ImageGeometry,
    asset: &ImageAssetBinding,
    limits: &ImageHwpxLimits,
) -> Result<(), ImageHwpxError> {
    if geometry.width_hwpunit == 0
        || geometry.height_hwpunit == 0
        || geometry.width_hwpunit > limits.native.extent_hwpunit
        || geometry.height_hwpunit > limits.native.extent_hwpunit
        || geometry.dpi_x == 0
        || geometry.dpi_y == 0
        || geometry.dpi_x > limits.native.dpi
        || geometry.dpi_y > limits.native.dpi
        || geometry.crop.left_px >= geometry.crop.right_px
        || geometry.crop.top_px >= geometry.crop.bottom_px
        || geometry.crop.right_px > asset.width_px
        || geometry.crop.bottom_px > asset.height_px
        || !geometry.render_required
    {
        return Err(ImageHwpxError::InvalidGeometry);
    }
    let original_width = pixels_to_hwpunit(asset.width_px, geometry.dpi_x, limits)?;
    let original_height = pixels_to_hwpunit(asset.height_px, geometry.dpi_y, limits)?;
    let clip_left = pixels_to_hwpunit_allow_zero(geometry.crop.left_px, geometry.dpi_x, limits)?;
    let clip_right = pixels_to_hwpunit(geometry.crop.right_px, geometry.dpi_x, limits)?;
    let clip_top = pixels_to_hwpunit_allow_zero(geometry.crop.top_px, geometry.dpi_y, limits)?;
    let clip_bottom = pixels_to_hwpunit(geometry.crop.bottom_px, geometry.dpi_y, limits)?;
    if clip_left >= clip_right
        || clip_top >= clip_bottom
        || clip_right > original_width
        || clip_bottom > original_height
    {
        return Err(ImageHwpxError::InvalidGeometry);
    }
    Ok(())
}

fn validate_alt_text(value: &str, limits: &ImageHwpxLimits) -> Result<(), ImageHwpxError> {
    if value.trim().is_empty()
        || value.len() > limits.native.alt_text_bytes
        || value.chars().any(invalid_xml_character)
    {
        return Err(ImageHwpxError::InvalidAltText);
    }
    Ok(())
}

fn invalid_xml_character(character: char) -> bool {
    matches!(character as u32, 0..=8 | 11..=12 | 14..=31 | 0xFFFE | 0xFFFF)
}

fn pixels_to_hwpunit(
    pixels: u32,
    dpi: u32,
    limits: &ImageHwpxLimits,
) -> Result<u32, ImageHwpxError> {
    let value = pixels_to_hwpunit_allow_zero(pixels, dpi, limits)?;
    if value == 0 {
        return Err(ImageHwpxError::InvalidGeometry);
    }
    Ok(value)
}

fn pixels_to_hwpunit_allow_zero(
    pixels: u32,
    dpi: u32,
    limits: &ImageHwpxLimits,
) -> Result<u32, ImageHwpxError> {
    let numerator = u64::from(pixels)
        .checked_mul(HWPUNIT_PER_INCH)
        .and_then(|value| value.checked_add(u64::from(dpi) / 2))
        .ok_or(ImageHwpxError::InvalidGeometry)?;
    let value = numerator / u64::from(dpi);
    if value > u64::from(limits.native.extent_hwpunit) {
        return Err(ImageHwpxError::InvalidGeometry);
    }
    u32::try_from(value).map_err(|_| ImageHwpxError::InvalidGeometry)
}

fn image_fragment(
    request: &ImageHwpxRequest,
    limits: &ImageHwpxLimits,
) -> Result<Vec<u8>, ImageHwpxError> {
    let geometry = &request.geometry;
    let original_width = pixels_to_hwpunit(request.asset.width_px, geometry.dpi_x, limits)?;
    let original_height = pixels_to_hwpunit(request.asset.height_px, geometry.dpi_y, limits)?;
    let clip_left = pixels_to_hwpunit_allow_zero(geometry.crop.left_px, geometry.dpi_x, limits)?;
    let clip_right = pixels_to_hwpunit(geometry.crop.right_px, geometry.dpi_x, limits)?;
    let clip_top = pixels_to_hwpunit_allow_zero(geometry.crop.top_px, geometry.dpi_y, limits)?;
    let clip_bottom = pixels_to_hwpunit(geometry.crop.bottom_px, geometry.dpi_y, limits)?;
    let escaped_alt = escape_xml_text(&request.alt_text)?;
    let escaped_relationship = escape_xml_attribute(&request.asset.relationship_id)?;
    let xml = format!(
        concat!(
            "<hp:pic xmlns:hp=\"{ns}\" id=\"{object_id}\" zOrder=\"0\" numberingType=\"PICTURE\" ",
            "textWrap=\"TOP_AND_BOTTOM\" textFlow=\"BOTH_SIDES\" lock=\"0\" dropcapstyle=\"None\" ",
            "href=\"\" groupLevel=\"0\" instid=\"{instance_id}\" reverse=\"0\">",
            "<hp:offset x=\"0\" y=\"0\"/>",
            "<hp:orgSz width=\"{width}\" height=\"{height}\"/>",
            "<hp:curSz width=\"0\" height=\"0\"/>",
            "<hp:flip horizontal=\"0\" vertical=\"0\"/>",
            "<hp:rotationInfo angle=\"0\" centerX=\"{center_x}\" centerY=\"{center_y}\" rotateimage=\"1\"/>",
            "<hp:renderingInfo>",
            "<hp:transMatrix e1=\"1\" e2=\"0\" e3=\"0\" e4=\"0\" e5=\"1\" e6=\"0\"/>",
            "<hp:scaMatrix e1=\"1\" e2=\"0\" e3=\"0\" e4=\"0\" e5=\"1\" e6=\"0\"/>",
            "<hp:rotMatrix e1=\"1\" e2=\"0\" e3=\"0\" e4=\"0\" e5=\"1\" e6=\"0\"/>",
            "</hp:renderingInfo>",
            "<hp:img binaryItemIDRef=\"{relationship}\" bright=\"0\" contrast=\"0\" effect=\"REAL_PIC\" alpha=\"0\"/>",
            "<hp:imgRect><hp:pt0 x=\"0\" y=\"0\"/><hp:pt1 x=\"{width}\" y=\"0\"/>",
            "<hp:pt2 x=\"{width}\" y=\"{height}\"/><hp:pt3 x=\"0\" y=\"{height}\"/></hp:imgRect>",
            "<hp:imgClip left=\"{clip_left}\" right=\"{clip_right}\" top=\"{clip_top}\" bottom=\"{clip_bottom}\"/>",
            "<hp:inMargin left=\"0\" right=\"0\" top=\"0\" bottom=\"0\"/>",
            "<hp:imgDim dimwidth=\"{original_width}\" dimheight=\"{original_height}\"/>",
            "<hp:effects/>",
            "<hp:sz width=\"{width}\" widthRelTo=\"ABSOLUTE\" height=\"{height}\" heightRelTo=\"ABSOLUTE\" protect=\"0\"/>",
            "<hp:pos treatAsChar=\"1\" affectLSpacing=\"1\" flowWithText=\"1\" allowOverlap=\"0\" ",
            "holdAnchorAndSO=\"0\" vertRelTo=\"PARA\" horzRelTo=\"COLUMN\" vertAlign=\"TOP\" ",
            "horzAlign=\"LEFT\" vertOffset=\"0\" horzOffset=\"0\"/>",
            "<hp:outMargin left=\"0\" right=\"0\" top=\"0\" bottom=\"0\"/>",
            "<hp:shapeComment>{alt}</hp:shapeComment></hp:pic>"
        ),
        ns = PARAGRAPH_NS,
        object_id = request.object_id,
        instance_id = request.instance_id,
        width = geometry.width_hwpunit,
        height = geometry.height_hwpunit,
        center_x = geometry.width_hwpunit / 2,
        center_y = geometry.height_hwpunit / 2,
        relationship = escaped_relationship,
        clip_left = clip_left,
        clip_right = clip_right,
        clip_top = clip_top,
        clip_bottom = clip_bottom,
        original_width = original_width,
        original_height = original_height,
        alt = escaped_alt,
    );
    if xml.len() > limits.native.serialized_bytes {
        return Err(ImageHwpxError::OutputLimit);
    }
    Ok(xml.into_bytes())
}

#[allow(clippy::too_many_lines)]
fn read_image_shape(
    bytes: &[u8],
    picture_ordinal: usize,
    expected_asset: &ImageAssetBinding,
    expected_geometry: &ImageGeometry,
    expected_alt_text: &str,
    limits: &ImageHwpxLimits,
) -> Result<ImageShape, ImageHwpxError> {
    validate_geometry(expected_geometry, expected_asset, limits)?;
    validate_alt_text(expected_alt_text, limits)?;
    let document = parse_section(bytes, limits)?;
    let root = element(&document, document.root_element())?;
    if root.name().namespace() != Some(SECTION_NS) || root.name().local_name() != "sec" {
        return Err(ImageHwpxError::UnsupportedTarget);
    }
    let pictures = document
        .elements()
        .iter()
        .enumerate()
        .filter(|(_, candidate)| has_name(candidate, "pic"))
        .map(|(index, _)| index)
        .collect::<Vec<_>>();
    if pictures.len() > limits.native.pictures {
        return Err(ImageHwpxError::InputLimit);
    }
    let picture_index = *pictures
        .get(picture_ordinal)
        .ok_or(ImageHwpxError::UnsupportedTarget)?;
    let picture = element(&document, picture_index)?;
    validate_attributes(
        picture,
        &[
            "id",
            "zOrder",
            "numberingType",
            "textWrap",
            "textFlow",
            "lock",
            "dropcapstyle",
            "href",
            "groupLevel",
            "instid",
            "reverse",
        ],
    )?;
    for (name, value) in [
        ("zOrder", "0"),
        ("numberingType", "PICTURE"),
        ("textWrap", "TOP_AND_BOTTOM"),
        ("textFlow", "BOTH_SIDES"),
        ("lock", "0"),
        ("dropcapstyle", "None"),
        ("href", ""),
        ("groupLevel", "0"),
        ("reverse", "0"),
    ] {
        require_attr(picture, name, value)?;
    }
    let object_id = parse_u32(attr(picture, "id")?)?;
    let instance_id = parse_u32(attr(picture, "instid")?)?;
    if object_id == 0 || instance_id == 0 || object_id == instance_id {
        return Err(ImageHwpxError::ObjectIdCollision);
    }
    let children = child_indexes(&document, picture_index)?;
    let names = [
        "offset",
        "orgSz",
        "curSz",
        "flip",
        "rotationInfo",
        "renderingInfo",
        "img",
        "imgRect",
        "imgClip",
        "inMargin",
        "imgDim",
        "effects",
        "sz",
        "pos",
        "outMargin",
        "shapeComment",
    ];
    if children.len() != names.len()
        || children.iter().zip(names).any(|(index, name)| {
            element(&document, *index).is_err() || !has_name(&document.elements()[*index], name)
        })
    {
        return Err(ImageHwpxError::ReadbackMismatch);
    }
    exact_empty_attributes(element(&document, children[0])?, &["x", "y"], &["0", "0"])?;
    exact_empty_attributes(
        element(&document, children[1])?,
        &["width", "height"],
        &[
            &expected_geometry.width_hwpunit.to_string(),
            &expected_geometry.height_hwpunit.to_string(),
        ],
    )?;
    exact_empty_attributes(
        element(&document, children[2])?,
        &["width", "height"],
        &["0", "0"],
    )?;
    exact_empty_attributes(
        element(&document, children[3])?,
        &["horizontal", "vertical"],
        &["0", "0"],
    )?;
    exact_empty_attributes(
        element(&document, children[4])?,
        &["angle", "centerX", "centerY", "rotateimage"],
        &[
            "0",
            &expected_geometry
                .width_hwpunit
                .saturating_div(2)
                .to_string(),
            &expected_geometry
                .height_hwpunit
                .saturating_div(2)
                .to_string(),
            "1",
        ],
    )?;
    let rendering = element(&document, children[5])?;
    validate_attributes(rendering, &[])?;
    let matrices = child_indexes(&document, children[5])?;
    if matrices.len() != 3
        || !has_name(element(&document, matrices[0])?, "transMatrix")
        || !has_name(element(&document, matrices[1])?, "scaMatrix")
        || !has_name(element(&document, matrices[2])?, "rotMatrix")
    {
        return Err(ImageHwpxError::ReadbackMismatch);
    }
    for matrix in matrices {
        exact_empty_attributes(
            element(&document, matrix)?,
            &["e1", "e2", "e3", "e4", "e5", "e6"],
            &["1", "0", "0", "0", "1", "0"],
        )?;
    }
    exact_empty_attributes(
        element(&document, children[6])?,
        &["binaryItemIDRef", "bright", "contrast", "effect", "alpha"],
        &[expected_asset.relationship_id(), "0", "0", "REAL_PIC", "0"],
    )?;
    let image_rect = element(&document, children[7])?;
    validate_attributes(image_rect, &[])?;
    let points = child_indexes(&document, children[7])?;
    let width = expected_geometry.width_hwpunit.to_string();
    let height = expected_geometry.height_hwpunit.to_string();
    let point_values = [("0", "0"), (&width, "0"), (&width, &height), ("0", &height)];
    if points.len() != 4 {
        return Err(ImageHwpxError::ReadbackMismatch);
    }
    for ((expected_name, point), (x, y)) in ["pt0", "pt1", "pt2", "pt3"]
        .iter()
        .zip(points)
        .zip(point_values)
    {
        let point = element(&document, point)?;
        if !has_name(point, expected_name) {
            return Err(ImageHwpxError::ReadbackMismatch);
        }
        exact_empty_attributes(point, &["x", "y"], &[x, y])?;
    }
    let original_width =
        pixels_to_hwpunit(expected_asset.width_px, expected_geometry.dpi_x, limits)?;
    let original_height =
        pixels_to_hwpunit(expected_asset.height_px, expected_geometry.dpi_y, limits)?;
    let clip = [
        pixels_to_hwpunit_allow_zero(
            expected_geometry.crop.left_px,
            expected_geometry.dpi_x,
            limits,
        )?,
        pixels_to_hwpunit(
            expected_geometry.crop.right_px,
            expected_geometry.dpi_x,
            limits,
        )?,
        pixels_to_hwpunit_allow_zero(
            expected_geometry.crop.top_px,
            expected_geometry.dpi_y,
            limits,
        )?,
        pixels_to_hwpunit(
            expected_geometry.crop.bottom_px,
            expected_geometry.dpi_y,
            limits,
        )?,
    ];
    let clip_strings = clip.map(|value| value.to_string());
    exact_empty_attributes(
        element(&document, children[8])?,
        &["left", "right", "top", "bottom"],
        &[
            &clip_strings[0],
            &clip_strings[1],
            &clip_strings[2],
            &clip_strings[3],
        ],
    )?;
    exact_empty_attributes(
        element(&document, children[9])?,
        &["left", "right", "top", "bottom"],
        &["0", "0", "0", "0"],
    )?;
    exact_empty_attributes(
        element(&document, children[10])?,
        &["dimwidth", "dimheight"],
        &[&original_width.to_string(), &original_height.to_string()],
    )?;
    exact_empty_attributes(element(&document, children[11])?, &[], &[])?;
    exact_empty_attributes(
        element(&document, children[12])?,
        &["width", "widthRelTo", "height", "heightRelTo", "protect"],
        &[&width, "ABSOLUTE", &height, "ABSOLUTE", "0"],
    )?;
    exact_empty_attributes(
        element(&document, children[13])?,
        &[
            "treatAsChar",
            "affectLSpacing",
            "flowWithText",
            "allowOverlap",
            "holdAnchorAndSO",
            "vertRelTo",
            "horzRelTo",
            "vertAlign",
            "horzAlign",
            "vertOffset",
            "horzOffset",
        ],
        &[
            "1", "1", "1", "0", "0", "PARA", "COLUMN", "TOP", "LEFT", "0", "0",
        ],
    )?;
    exact_empty_attributes(
        element(&document, children[14])?,
        &["left", "right", "top", "bottom"],
        &["0", "0", "0", "0"],
    )?;
    let shape_comment = element(&document, children[15])?;
    validate_attributes(shape_comment, &[])?;
    if shape_comment.is_empty()
        || element_text(&document, children[15], limits.native.alt_text_bytes)? != expected_alt_text
    {
        return Err(ImageHwpxError::ReadbackMismatch);
    }
    let (object_ids, instance_ids, picture_count) = object_and_instance_ids(&document, limits)?;
    if !object_ids.contains(&object_id) || !instance_ids.contains(&instance_id) {
        return Err(ImageHwpxError::ObjectIdCollision);
    }
    let picture_span = picture
        .outer_span()
        .ok_or(ImageHwpxError::ReadbackMismatch)?;
    Ok(ImageShape {
        readback: ImageHwpxReadback {
            profile_id: IMAGE_HWPX_PROFILE_ID,
            object_id,
            instance_id,
            link_mode: ImageLinkMode::Embed,
            geometry: expected_geometry.clone(),
            alt_text: expected_alt_text.to_owned(),
            asset: expected_asset.clone(),
            picture_ordinal,
            native_object_count: object_ids.len(),
            native_instance_count: instance_ids.len(),
            picture_count,
            render_required: true,
        },
        picture_span,
    })
}

fn verify_output_relationship_and_asset(
    patch: &PatchResult,
    manifest_path: &PackagePath,
    request: &ImageHwpxRequest,
    limits: &ImageHwpxLimits,
) -> Result<(), ImageHwpxError> {
    let manifest = patch
        .parts
        .iter()
        .find(|part| &part.path == manifest_path)
        .ok_or(ImageHwpxError::RelationshipMismatch)?;
    let document = PreservingXmlDocument::parse(&manifest.bytes)?;
    let matches = manifest_items(
        &document,
        &request.asset,
        request.asset.disposition == AssetDisposition::AddNew,
    )?;
    if matches.len() != 1 {
        return Err(ImageHwpxError::RelationshipMismatch);
    }
    let asset_part = patch
        .parts
        .iter()
        .find(|part| part.path.as_str() == request.asset.target_path)
        .ok_or(ImageHwpxError::RelationshipMismatch)?;
    if asset_part.media_type.as_str() != request.asset.media.media_type()
        || hex(Sha256::digest(&asset_part.bytes).into()) != request.asset.content_sha256
        || asset_part.bytes.len() != request.asset_plan.content_bytes()
        || asset_part.bytes.len() > limits.patch.config().max_added_part_bytes
    {
        return Err(ImageHwpxError::RelationshipMismatch);
    }
    Ok(())
}

fn verify_manifest_preservation(
    patch: &PatchResult,
    manifest_path: &PackagePath,
    request: &ImageHwpxRequest,
    original: &[u8],
) -> Result<(), ImageHwpxError> {
    let manifest = patch
        .parts
        .iter()
        .find(|part| &part.path == manifest_path)
        .ok_or(ImageHwpxError::PreservationMismatch)?;
    match request.asset.disposition {
        AssetDisposition::ReusedExisting => {
            if manifest.bytes != original {
                return Err(ImageHwpxError::PreservationMismatch);
            }
        }
        AssetDisposition::AddNew => {
            let document = PreservingXmlDocument::parse(&manifest.bytes)?;
            let matches = manifest_items(&document, &request.asset, true)?;
            if matches.len() != 1 {
                return Err(ImageHwpxError::PreservationMismatch);
            }
            let span = element(&document, matches[0])?
                .outer_span()
                .ok_or(ImageHwpxError::PreservationMismatch)?;
            let mut restored = Vec::with_capacity(original.len());
            restored.extend_from_slice(&manifest.bytes[..span.start()]);
            restored.extend_from_slice(&manifest.bytes[span.end()..]);
            if restored != original {
                return Err(ImageHwpxError::PreservationMismatch);
            }
        }
    }
    Ok(())
}

fn verify_unrelated_parts(
    patch: &PatchResult,
    section: &PackagePath,
    graph: &PackageGraph,
    request: &ImageHwpxRequest,
) -> Result<(), ImageHwpxError> {
    for record in patch.parts() {
        let allowed = record.path() == section
            || record.path() == &graph.package_document
            || record.path().as_str() == request.asset.target_path;
        if !allowed
            && (record.disposition() != PatchPartDisposition::Untouched
                || record.source_sha256() != Some(record.output_sha256()))
        {
            return Err(ImageHwpxError::PreservationMismatch);
        }
    }
    Ok(())
}

fn manifest_items(
    document: &PreservingXmlDocument,
    asset: &ImageAssetBinding,
    require_exact_href: bool,
) -> Result<Vec<usize>, ImageHwpxError> {
    let mut output = Vec::new();
    for (index, candidate) in document.elements().iter().enumerate() {
        if candidate.name().local_name() != "item"
            || candidate
                .name()
                .namespace()
                .is_none_or(|value| value.trim_end_matches('/') != OPF_NS)
        {
            continue;
        }
        let href = optional_attr(candidate, "href")?;
        if optional_attr(candidate, "id")? == Some(asset.relationship_id())
            && optional_attr(candidate, "media-type")? == Some(asset.media.media_type())
            && (!require_exact_href || href == Some(asset.target_path()))
        {
            output.push(index);
        }
    }
    Ok(output)
}

fn parse_section(
    bytes: &[u8],
    limits: &ImageHwpxLimits,
) -> Result<PreservingXmlDocument, ImageHwpxError> {
    if bytes.is_empty() || bytes.len() > limits.native.section_bytes {
        return Err(ImageHwpxError::InputLimit);
    }
    let document = PreservingXmlDocument::parse(bytes)?;
    if document.elements().len() > limits.native.elements {
        return Err(ImageHwpxError::InputLimit);
    }
    Ok(document)
}

fn element(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<&XmlElementToken, ImageHwpxError> {
    document
        .elements()
        .get(index)
        .ok_or(ImageHwpxError::UnsupportedTarget)
}

fn has_name(element: &XmlElementToken, local_name: &str) -> bool {
    element.name().namespace() == Some(PARAGRAPH_NS) && element.name().local_name() == local_name
}

fn child_indexes(
    document: &PreservingXmlDocument,
    parent: usize,
) -> Result<Vec<usize>, ImageHwpxError> {
    let mut output = Vec::new();
    let mut current = element(document, parent)?.first_child();
    while let Some(index) = current {
        output
            .try_reserve(1)
            .map_err(|_| ImageHwpxError::Allocation)?;
        output.push(index);
        current = element(document, index)?.next_sibling();
    }
    Ok(output)
}

fn direct_children_named(
    document: &PreservingXmlDocument,
    parent: usize,
    local_name: &str,
) -> Result<Vec<usize>, ImageHwpxError> {
    Ok(child_indexes(document, parent)?
        .into_iter()
        .filter(|index| element(document, *index).is_ok_and(|value| has_name(value, local_name)))
        .collect())
}

fn validate_attributes(element: &XmlElementToken, allowed: &[&str]) -> Result<(), ImageHwpxError> {
    let mut seen = BTreeSet::new();
    for attribute in element.attributes() {
        if attribute.is_namespace_declaration() {
            continue;
        }
        let name = attribute.name().local_name();
        if attribute.name().namespace().is_some() || !allowed.contains(&name) || !seen.insert(name)
        {
            return Err(ImageHwpxError::ReadbackMismatch);
        }
    }
    if seen.len() != allowed.len() {
        return Err(ImageHwpxError::ReadbackMismatch);
    }
    Ok(())
}

fn exact_empty_attributes(
    element: &XmlElementToken,
    names: &[&str],
    values: &[&str],
) -> Result<(), ImageHwpxError> {
    if names.len() != values.len() || !element.is_empty() {
        return Err(ImageHwpxError::ReadbackMismatch);
    }
    validate_attributes(element, names)?;
    for (name, value) in names.iter().zip(values) {
        require_attr(element, name, value)?;
    }
    Ok(())
}

fn attr<'a>(element: &'a XmlElementToken, name: &str) -> Result<&'a str, ImageHwpxError> {
    optional_attr(element, name)?.ok_or(ImageHwpxError::ReadbackMismatch)
}

fn optional_attr<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<Option<&'a str>, ImageHwpxError> {
    let mut values = element
        .attributes()
        .iter()
        .filter(|attribute| {
            !attribute.is_namespace_declaration()
                && attribute.name().namespace().is_none()
                && attribute.name().local_name() == name
        })
        .map(crate::XmlAttributeToken::semantic_value);
    let value = values.next();
    if values.next().is_some() {
        return Err(ImageHwpxError::ReadbackMismatch);
    }
    Ok(value)
}

fn require_attr(element: &XmlElementToken, name: &str, value: &str) -> Result<(), ImageHwpxError> {
    if attr(element, name)? != value {
        return Err(ImageHwpxError::ReadbackMismatch);
    }
    Ok(())
}

fn element_text(
    document: &PreservingXmlDocument,
    element_index: usize,
    maximum: usize,
) -> Result<String, ImageHwpxError> {
    let element = element(document, element_index)?;
    if element.first_child().is_some() {
        return Err(ImageHwpxError::ReadbackMismatch);
    }
    let span = element
        .content_span()
        .ok_or(ImageHwpxError::ReadbackMismatch)?;
    let raw = document.source_text(span)?;
    if raw.len() > maximum {
        return Err(ImageHwpxError::InvalidAltText);
    }
    decode_xml_text(raw)
}

fn decode_xml_text(raw: &str) -> Result<String, ImageHwpxError> {
    if raw.contains("&#") {
        return Err(ImageHwpxError::ReadbackMismatch);
    }
    Ok(raw
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", "\"")
        .replace("&apos;", "'")
        .replace("&amp;", "&"))
}

fn escape_xml_text(value: &str) -> Result<String, ImageHwpxError> {
    if value.chars().any(invalid_xml_character) {
        return Err(ImageHwpxError::InvalidAltText);
    }
    Ok(value
        .replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;"))
}

fn escape_xml_attribute(value: &str) -> Result<String, ImageHwpxError> {
    if value.chars().any(invalid_xml_character) {
        return Err(ImageHwpxError::AssetDrift);
    }
    Ok(value
        .replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
        .replace('\'', "&apos;"))
}

fn parse_u32(value: &str) -> Result<u32, ImageHwpxError> {
    if value.is_empty()
        || (value.len() > 1 && value.starts_with('0'))
        || !value.bytes().all(|byte| byte.is_ascii_digit())
    {
        return Err(ImageHwpxError::ReadbackMismatch);
    }
    value.parse().map_err(|_| ImageHwpxError::ReadbackMismatch)
}

fn package_state_sha256(graph: &PackageGraph) -> String {
    let mut digest = Sha256::new();
    digest.update(IMAGE_HWPX_PROFILE_ID.as_bytes());
    digest.update(b"\0package-state\0");
    digest.update(graph.package_document.as_str().as_bytes());
    for part in &graph.parts {
        digest.update(b"\0part\0");
        digest.update(part.path.as_str().as_bytes());
        digest.update([match part.role {
            PartRole::Infrastructure => 0,
            PartRole::ManifestListed => 1,
            PartRole::SpineDocument => 2,
        }]);
        digest.update(part.media_type.as_str().as_bytes());
        digest.update(part.expanded_size.to_be_bytes());
        digest.update(part.raw_sha256);
    }
    for relationship in &graph.relationships {
        digest.update(b"\0relationship\0");
        digest.update(relationship.id.as_bytes());
        digest.update(relationship.source.as_str().as_bytes());
        digest.update(relationship.target.as_str().as_bytes());
        digest.update(relationship.media_type.as_str().as_bytes());
        digest.update([match relationship.kind {
            RelationshipKind::ManifestItem => 0,
            RelationshipKind::SpineItem => 1,
        }]);
        digest.update([u8::from(relationship.linear)]);
    }
    for path in &graph.spine {
        digest.update(b"\0spine\0");
        digest.update(path.as_str().as_bytes());
    }
    hex(digest.finalize().into())
}

fn id_set_sha256(domain: &str, ids: &BTreeSet<u32>) -> String {
    let mut digest = Sha256::new();
    digest.update(IMAGE_HWPX_PROFILE_ID.as_bytes());
    digest.update(b"\0");
    digest.update(domain.as_bytes());
    for id in ids {
        digest.update(id.to_be_bytes());
    }
    hex(digest.finalize().into())
}

fn bounded_json<T: Serialize>(
    value: &T,
    limits: &ImageHwpxLimits,
) -> Result<Vec<u8>, ImageHwpxError> {
    let bytes = serde_json::to_vec(value).map_err(|_| ImageHwpxError::Serialization)?;
    if bytes.len() > limits.native.serialized_bytes {
        return Err(ImageHwpxError::OutputLimit);
    }
    Ok(bytes)
}

fn require_digest(value: &str) -> Result<(), ImageHwpxError> {
    if value.len() != 64
        || value
            .bytes()
            .any(|byte| !byte.is_ascii_digit() && !(b'a'..=b'f').contains(&byte))
    {
        return Err(ImageHwpxError::InvalidBinding);
    }
    Ok(())
}

fn hex(value: [u8; 32]) -> String {
    let mut output = String::with_capacity(64);
    for byte in value {
        let _ = write!(output, "{byte:02x}");
    }
    output
}

fn reject_duplicate_json_keys(bytes: &[u8]) -> Result<(), ImageHwpxError> {
    struct Seed;
    struct Visitor;

    impl<'de> serde::de::DeserializeSeed<'de> for Seed {
        type Value = ();
        fn deserialize<D>(self, deserializer: D) -> Result<(), D::Error>
        where
            D: serde::Deserializer<'de>,
        {
            deserializer.deserialize_any(Visitor)
        }
    }
    impl<'de> serde::de::Visitor<'de> for Visitor {
        type Value = ();
        fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
            formatter.write_str("JSON without duplicate object keys")
        }
        fn visit_map<A>(self, mut map: A) -> Result<(), A::Error>
        where
            A: serde::de::MapAccess<'de>,
        {
            let mut keys = BTreeSet::new();
            while let Some(key) = map.next_key::<String>()? {
                if !keys.insert(key) {
                    return Err(serde::de::Error::custom("duplicate key"));
                }
                map.next_value_seed(Seed)?;
            }
            Ok(())
        }
        fn visit_seq<A>(self, mut sequence: A) -> Result<(), A::Error>
        where
            A: serde::de::SeqAccess<'de>,
        {
            while sequence.next_element_seed(Seed)?.is_some() {}
            Ok(())
        }
        fn visit_bool<E>(self, _: bool) -> Result<(), E> {
            Ok(())
        }
        fn visit_i64<E>(self, _: i64) -> Result<(), E> {
            Ok(())
        }
        fn visit_u64<E>(self, _: u64) -> Result<(), E> {
            Ok(())
        }
        fn visit_f64<E>(self, _: f64) -> Result<(), E> {
            Ok(())
        }
        fn visit_str<E>(self, _: &str) -> Result<(), E> {
            Ok(())
        }
        fn visit_none<E>(self) -> Result<(), E> {
            Ok(())
        }
        fn visit_unit<E>(self) -> Result<(), E> {
            Ok(())
        }
    }
    let mut deserializer = serde_json::Deserializer::from_slice(bytes);
    serde::de::DeserializeSeed::deserialize(Seed, &mut deserializer)
        .map_err(|_| ImageHwpxError::InvalidJson)?;
    deserializer.end().map_err(|_| ImageHwpxError::InvalidJson)
}
