use std::collections::BTreeMap;
use std::fmt;

use domain_ir::{
    CanvasBounds, CanvasNode, CanvasNodeKind, CanvasResourceKind, DrawingCanvasBuilder,
    DrawingCanvasError, DrawingCanvasLimits, DrawingCanvasOperation, DrawingCanvasPlan,
    DrawingCanvasRequest, DrawingCanvasState, ImageClip, LogicalId,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{PreservingXmlDocument, PreservingXmlError, XmlByteSpan, XmlElementToken};

pub const DRAWING_CANVAS_HWPX_PROFILE_ID: &str =
    "hwpx-agent.drawing-canvas-hwpx.hwpml-2011-static/v1";

const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const CORE_NS: &str = "http://www.hancom.co.kr/hwpml/2011/core";
const WRAPPER_NS: &str = "urn:hwpx-agent:fragment-wrapper";
const EMPTY_SHA256: &str = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct DrawingCanvasHwpxLimitConfig {
    pub section_bytes: usize,
    pub output_bytes: usize,
    pub elements: usize,
    pub nodes: usize,
}

impl Default for DrawingCanvasHwpxLimitConfig {
    fn default() -> Self {
        Self {
            section_bytes: 32 * 1024 * 1024,
            output_bytes: 32 * 1024 * 1024,
            elements: 1_000_000,
            nodes: 65_536,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct DrawingCanvasHwpxLimits(DrawingCanvasHwpxLimitConfig);

impl DrawingCanvasHwpxLimits {
    pub const HARD_MAX_BYTES: usize = 256 * 1024 * 1024;
    pub const HARD_MAX_ELEMENTS: usize = 4_000_000;
    pub const HARD_MAX_NODES: usize = 1_000_000;

    /// Creates finite limits for the static canvas island profile.
    ///
    /// # Errors
    ///
    /// Rejects zero, inconsistent or process-hostile limits.
    pub fn new(config: DrawingCanvasHwpxLimitConfig) -> Result<Self, DrawingCanvasHwpxError> {
        if config.section_bytes == 0
            || config.output_bytes < config.section_bytes
            || config.output_bytes > Self::HARD_MAX_BYTES
            || config.elements == 0
            || config.elements > Self::HARD_MAX_ELEMENTS
            || config.nodes == 0
            || config.nodes > Self::HARD_MAX_NODES
        {
            return Err(DrawingCanvasHwpxError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> DrawingCanvasHwpxLimitConfig {
        self.0
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct DrawingCanvasHwpxReadback {
    profile_id: &'static str,
    section_sha256: String,
    state_sha256: String,
    island_sha256: String,
    run_ordinal: usize,
    node_count: usize,
}

impl DrawingCanvasHwpxReadback {
    #[must_use]
    pub fn section_sha256(&self) -> &str {
        &self.section_sha256
    }

    #[must_use]
    pub fn state_sha256(&self) -> &str {
        &self.state_sha256
    }

    #[must_use]
    pub const fn node_count(&self) -> usize {
        self.node_count
    }
}

impl fmt::Debug for DrawingCanvasHwpxReadback {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("DrawingCanvasHwpxReadback")
            .field("profile_id", &self.profile_id)
            .field("run_ordinal", &self.run_ordinal)
            .field("node_count", &self.node_count)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct DrawingCanvasHwpxPlan {
    profile_id: &'static str,
    capability_id: &'static str,
    domain_plan: DrawingCanvasPlan,
    run_ordinal: usize,
    source_section_sha256: String,
    target_section_sha256: String,
    source_state_sha256: String,
    target_state_sha256: String,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    plan_sha256: String,
}

impl DrawingCanvasHwpxPlan {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
    }

    #[must_use]
    pub fn target_section_sha256(&self) -> &str {
        &self.target_section_sha256
    }

    #[must_use]
    pub fn plan_sha256(&self) -> &str {
        &self.plan_sha256
    }
}

impl fmt::Debug for DrawingCanvasHwpxPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("DrawingCanvasHwpxPlan")
            .field("profile_id", &self.profile_id)
            .field("capability_id", &self.capability_id)
            .field("run_ordinal", &self.run_ordinal)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct DrawingCanvasHwpxLoweringReceipt {
    profile_id: &'static str,
    capability_id: &'static str,
    source_section_sha256: String,
    target_section_sha256: String,
    source_state_sha256: String,
    target_state_sha256: String,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    plan_sha256: String,
    semantic_reopen: bool,
    outside_island_preserved: bool,
}

impl DrawingCanvasHwpxLoweringReceipt {
    #[must_use]
    pub const fn semantic_reopen(&self) -> bool {
        self.semantic_reopen
    }

    #[must_use]
    pub const fn outside_island_preserved(&self) -> bool {
        self.outside_island_preserved
    }
}

impl fmt::Debug for DrawingCanvasHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("DrawingCanvasHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field("capability_id", &self.capability_id)
            .field("semantic_reopen", &self.semantic_reopen)
            .field("outside_island_preserved", &self.outside_island_preserved)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct DrawingCanvasHwpxLowered {
    pub section_xml: Vec<u8>,
    pub readback: DrawingCanvasHwpxReadback,
    pub receipt: DrawingCanvasHwpxLoweringReceipt,
}

impl fmt::Debug for DrawingCanvasHwpxLowered {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("DrawingCanvasHwpxLowered")
            .field("section_bytes", &self.section_xml.len())
            .field("readback", &self.readback)
            .field("receipt", &self.receipt)
            .finish()
    }
}

#[derive(Debug)]
pub struct DrawingCanvasHwpxReader;

impl DrawingCanvasHwpxReader {
    /// Reopens one closed native canvas run and matches every node and image reference.
    ///
    /// # Errors
    ///
    /// Rejects malformed XML or any identity, topology, geometry, clip or resource drift.
    pub fn read(
        section_xml: &[u8],
        state: &DrawingCanvasState,
        run_ordinal: usize,
        state_limits: DrawingCanvasLimits,
        limits: DrawingCanvasHwpxLimits,
    ) -> Result<DrawingCanvasHwpxReadback, DrawingCanvasHwpxError> {
        let island = inspect_island(section_xml, state, run_ordinal, limits)?;
        Ok(DrawingCanvasHwpxReadback {
            profile_id: DRAWING_CANVAS_HWPX_PROFILE_ID,
            section_sha256: sha256(section_xml),
            state_sha256: state.state_sha256(state_limits)?,
            island_sha256: sha256(&island.island_bytes),
            run_ordinal,
            node_count: island.nodes.len(),
        })
    }
}

#[derive(Debug)]
pub struct DrawingCanvasHwpxBuilder;

impl DrawingCanvasHwpxBuilder {
    /// Seals exact source/target XML, complete canvas state and document flow.
    ///
    /// # Errors
    ///
    /// Rejects stale state, an unsupported native profile or non-reopenable output.
    pub fn plan(
        section_xml: &[u8],
        run_ordinal: usize,
        current: &DrawingCanvasState,
        request: &DrawingCanvasRequest,
        current_document_flow_sha256: &str,
        state_limits: DrawingCanvasLimits,
        limits: DrawingCanvasHwpxLimits,
    ) -> Result<DrawingCanvasHwpxPlan, DrawingCanvasHwpxError> {
        if request.source() != current {
            return Err(DrawingCanvasHwpxError::SourceStateDrift);
        }
        if request.before_document_flow_sha256() != current_document_flow_sha256 {
            return Err(DrawingCanvasHwpxError::DocumentFlowDrift);
        }
        if matches!(
            request.operation(),
            DrawingCanvasOperation::SetPictureEffects { .. }
        ) {
            return Err(DrawingCanvasHwpxError::UnsupportedProfile);
        }
        let source_readback =
            DrawingCanvasHwpxReader::read(section_xml, current, run_ordinal, state_limits, limits)?;
        let builder = DrawingCanvasBuilder;
        let domain_plan = builder.plan(
            request.clone(),
            current,
            current_document_flow_sha256,
            state_limits,
        )?;
        let target_xml = render_target(
            section_xml,
            run_ordinal,
            current,
            domain_plan.request().target(),
            limits,
        )?;
        let target_readback = DrawingCanvasHwpxReader::read(
            &target_xml,
            domain_plan.request().target(),
            run_ordinal,
            state_limits,
            limits,
        )?;
        let target_state_sha256 = domain_plan.request().target().state_sha256(state_limits)?;
        let mut plan = DrawingCanvasHwpxPlan {
            profile_id: DRAWING_CANVAS_HWPX_PROFILE_ID,
            capability_id: request.operation().capability_id(),
            domain_plan,
            run_ordinal,
            source_section_sha256: source_readback.section_sha256,
            target_section_sha256: target_readback.section_sha256,
            source_state_sha256: current.state_sha256(state_limits)?,
            target_state_sha256,
            source_document_flow_sha256: current_document_flow_sha256.to_owned(),
            target_document_flow_sha256: request.after_document_flow_sha256().to_owned(),
            plan_sha256: String::new(),
        };
        plan.plan_sha256 = plan_binding_sha256(&plan)?;
        Ok(plan)
    }
}

#[derive(Debug)]
pub struct DrawingCanvasHwpxLowerer;

impl DrawingCanvasHwpxLowerer {
    /// Rechecks the sealed plan and publishes only a strictly reopened preserving result.
    ///
    /// # Errors
    ///
    /// Rejects plan tampering, state/flow drift, preservation failure or semantic drift.
    pub fn lower(
        plan: &DrawingCanvasHwpxPlan,
        current_section_xml: &[u8],
        current: &DrawingCanvasState,
        current_document_flow_sha256: &str,
        state_limits: DrawingCanvasLimits,
        limits: DrawingCanvasHwpxLimits,
    ) -> Result<DrawingCanvasHwpxLowered, DrawingCanvasHwpxError> {
        if plan.profile_id != DRAWING_CANVAS_HWPX_PROFILE_ID
            || plan.capability_id != plan.domain_plan.request().operation().capability_id()
            || plan_binding_sha256(plan)? != plan.plan_sha256
            || plan.source_state_sha256 != current.state_sha256(state_limits)?
            || plan.target_state_sha256
                != plan
                    .domain_plan
                    .request()
                    .target()
                    .state_sha256(state_limits)?
        {
            return Err(DrawingCanvasHwpxError::PlanTampered);
        }
        if sha256(current_section_xml) != plan.source_section_sha256 {
            return Err(DrawingCanvasHwpxError::SourceStateDrift);
        }
        if current_document_flow_sha256 != plan.source_document_flow_sha256 {
            return Err(DrawingCanvasHwpxError::DocumentFlowDrift);
        }
        let source_island = inspect_island(current_section_xml, current, plan.run_ordinal, limits)?;
        let builder = DrawingCanvasBuilder;
        let domain_result = builder.build(
            &plan.domain_plan,
            current,
            current_document_flow_sha256,
            state_limits,
        )?;
        let target_xml = render_target(
            current_section_xml,
            plan.run_ordinal,
            current,
            &domain_result.target,
            limits,
        )?;
        if target_xml.len() > limits.0.output_bytes
            || sha256(&target_xml) != plan.target_section_sha256
        {
            return Err(DrawingCanvasHwpxError::PlanTampered);
        }
        let target_island =
            inspect_island(&target_xml, &domain_result.target, plan.run_ordinal, limits)?;
        if !outside_island_equal(
            current_section_xml,
            source_island.island_span,
            &target_xml,
            target_island.island_span,
        ) {
            return Err(DrawingCanvasHwpxError::PreservationDrift);
        }
        let readback = DrawingCanvasHwpxReader::read(
            &target_xml,
            &domain_result.target,
            plan.run_ordinal,
            state_limits,
            limits,
        )?;
        Ok(DrawingCanvasHwpxLowered {
            section_xml: target_xml,
            readback,
            receipt: DrawingCanvasHwpxLoweringReceipt {
                profile_id: DRAWING_CANVAS_HWPX_PROFILE_ID,
                capability_id: plan.capability_id,
                source_section_sha256: plan.source_section_sha256.clone(),
                target_section_sha256: plan.target_section_sha256.clone(),
                source_state_sha256: plan.source_state_sha256.clone(),
                target_state_sha256: plan.target_state_sha256.clone(),
                source_document_flow_sha256: plan.source_document_flow_sha256.clone(),
                target_document_flow_sha256: plan.target_document_flow_sha256.clone(),
                plan_sha256: plan.plan_sha256.clone(),
                semantic_reopen: true,
                outside_island_preserved: true,
            },
        })
    }
}

#[derive(Debug, Error)]
pub enum DrawingCanvasHwpxError {
    #[error("drawing-canvas HWPX limits are invalid")]
    InvalidLimit,
    #[error("drawing-canvas HWPX input exceeds a finite limit")]
    InputLimit,
    #[error("drawing-canvas HWPX XML is invalid")]
    Xml(#[from] PreservingXmlError),
    #[error("drawing-canvas domain state is invalid")]
    Domain(#[from] DrawingCanvasError),
    #[error("drawing-canvas HWPX profile is unsupported")]
    UnsupportedProfile,
    #[error("drawing-canvas HWPX source state drifted")]
    SourceStateDrift,
    #[error("drawing-canvas HWPX document flow drifted")]
    DocumentFlowDrift,
    #[error("drawing-canvas HWPX plan was tampered with")]
    PlanTampered,
    #[error("drawing-canvas HWPX preservation failed")]
    PreservationDrift,
    #[error("drawing-canvas HWPX output exceeds a finite limit")]
    OutputLimit,
    #[error("drawing-canvas HWPX serialization failed")]
    Serialization,
}

impl DrawingCanvasHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "drawing_canvas_hwpx_invalid_limit",
            Self::InputLimit => "drawing_canvas_hwpx_input_limit",
            Self::Xml(_) => "drawing_canvas_hwpx_xml",
            Self::Domain(_) => "drawing_canvas_hwpx_domain",
            Self::UnsupportedProfile => "drawing_canvas_hwpx_unsupported_profile",
            Self::SourceStateDrift => "drawing_canvas_hwpx_source_state_drift",
            Self::DocumentFlowDrift => "drawing_canvas_hwpx_document_flow_drift",
            Self::PlanTampered => "drawing_canvas_hwpx_plan_tampered",
            Self::PreservationDrift => "drawing_canvas_hwpx_preservation_drift",
            Self::OutputLimit => "drawing_canvas_hwpx_output_limit",
            Self::Serialization => "drawing_canvas_hwpx_serialization",
        }
    }
}

struct NativeNode {
    outer_span: XmlByteSpan,
}

struct ParsedIsland {
    document: PreservingXmlDocument,
    nodes: BTreeMap<LogicalId, NativeNode>,
    island_span: ByteRange,
    island_bytes: Vec<u8>,
}

#[allow(clippy::too_many_lines)] // Keeps native node/resource closure in one reviewed pass.
fn inspect_island(
    section_xml: &[u8],
    state: &DrawingCanvasState,
    run_ordinal: usize,
    limits: DrawingCanvasHwpxLimits,
) -> Result<ParsedIsland, DrawingCanvasHwpxError> {
    if section_xml.is_empty()
        || section_xml.len() > limits.0.section_bytes
        || state.nodes().is_empty()
        || state.nodes().len() > limits.0.nodes
    {
        return Err(DrawingCanvasHwpxError::InputLimit);
    }
    let document = PreservingXmlDocument::parse(section_xml)?;
    if document.elements().len() > limits.0.elements {
        return Err(DrawingCanvasHwpxError::InputLimit);
    }
    let run_index = document
        .elements()
        .iter()
        .enumerate()
        .filter(|(_, element)| has_name(element, PARAGRAPH_NS, "run"))
        .nth(run_ordinal)
        .map(|(index, _)| index)
        .ok_or(DrawingCanvasHwpxError::UnsupportedProfile)?;
    let mut by_native = BTreeMap::new();
    for (index, element) in document.elements().iter().enumerate() {
        if node_tag(element).is_none() {
            continue;
        }
        let native = parse_u32(attribute(element, "id")?)?;
        if by_native.insert(native, index).is_some() {
            return Err(DrawingCanvasHwpxError::UnsupportedProfile);
        }
    }
    let mut nodes = BTreeMap::new();
    for node in state.nodes() {
        let index = *by_native
            .get(&node.native_object_id)
            .ok_or(DrawingCanvasHwpxError::UnsupportedProfile)?;
        let native = element(&document, index)?;
        validate_native_node(&document, native, node, state)?;
        let parent = native
            .parent()
            .ok_or(DrawingCanvasHwpxError::UnsupportedProfile)?;
        if let Some(parent_id) = &node.parent_id {
            let expected = state
                .node(parent_id)
                .ok_or(DrawingCanvasHwpxError::UnsupportedProfile)?;
            let actual = element(&document, parent)?;
            if node_tag(actual) != Some("container")
                || parse_u32(attribute(actual, "id")?)? != expected.native_object_id
            {
                return Err(DrawingCanvasHwpxError::UnsupportedProfile);
            }
        } else if parent != run_index {
            return Err(DrawingCanvasHwpxError::UnsupportedProfile);
        }
        nodes.insert(
            node.node_id.clone(),
            NativeNode {
                outer_span: native
                    .outer_span()
                    .ok_or(DrawingCanvasHwpxError::UnsupportedProfile)?,
            },
        );
    }
    let roots = direct_node_children(&document, run_index)?;
    let expected_roots = ordered_children(state, None);
    if roots.len() != expected_roots.len() {
        return Err(DrawingCanvasHwpxError::UnsupportedProfile);
    }
    for (native_index, expected) in roots.iter().zip(expected_roots) {
        if parse_u32(attribute(element(&document, *native_index)?, "id")?)?
            != expected.native_object_id
        {
            return Err(DrawingCanvasHwpxError::UnsupportedProfile);
        }
    }
    for container in state
        .nodes()
        .iter()
        .filter(|node| node.kind == CanvasNodeKind::Container)
    {
        let native = by_native
            .get(&container.native_object_id)
            .copied()
            .ok_or(DrawingCanvasHwpxError::UnsupportedProfile)?;
        let actual = direct_node_children(&document, native)?;
        let expected = ordered_children(state, Some(&container.node_id));
        if actual.len() != expected.len() {
            return Err(DrawingCanvasHwpxError::UnsupportedProfile);
        }
        for (native_index, expected) in actual.iter().zip(expected) {
            if parse_u32(attribute(element(&document, *native_index)?, "id")?)?
                != expected.native_object_id
            {
                return Err(DrawingCanvasHwpxError::UnsupportedProfile);
            }
        }
    }
    require_whitespace_between(section_xml, &document, &roots)?;
    let first = element(
        &document,
        *roots
            .first()
            .ok_or(DrawingCanvasHwpxError::UnsupportedProfile)?,
    )?
    .outer_span()
    .ok_or(DrawingCanvasHwpxError::UnsupportedProfile)?;
    let last = element(
        &document,
        *roots
            .last()
            .ok_or(DrawingCanvasHwpxError::UnsupportedProfile)?,
    )?
    .outer_span()
    .ok_or(DrawingCanvasHwpxError::UnsupportedProfile)?;
    let island_span = ByteRange::new(section_xml, first.start(), last.end())?;
    let island_bytes = section_xml
        .get(island_span.start..island_span.end)
        .ok_or(DrawingCanvasHwpxError::UnsupportedProfile)?
        .to_vec();
    Ok(ParsedIsland {
        document,
        nodes,
        island_span,
        island_bytes,
    })
}

fn validate_native_node(
    document: &PreservingXmlDocument,
    native: &XmlElementToken,
    node: &CanvasNode,
    state: &DrawingCanvasState,
) -> Result<(), DrawingCanvasHwpxError> {
    if parse_u32(attribute(native, "id")?)? != node.native_object_id
        || parse_u32(attribute(native, "instid")?)? != node.native_instance_id
        || parse_u32(attribute(native, "zOrder")?)? != node.ordinal
        || parse_u32(attribute(native, "groupLevel")?)? != node.group_level
        || node_tag(native) != Some(node_tag_for_kind(node.kind))
        || !node.visible
        || !node.printable
    {
        return Err(DrawingCanvasHwpxError::UnsupportedProfile);
    }
    let offset = unique_child(document, native, PARAGRAPH_NS, "offset")?;
    let size = unique_child(document, native, PARAGRAPH_NS, "curSz")?;
    let sz = unique_child(document, native, PARAGRAPH_NS, "sz")?;
    if (CanvasBounds {
        x_hwpunit: parse_i64(attribute(offset, "x")?)?,
        y_hwpunit: parse_i64(attribute(offset, "y")?)?,
        width_hwpunit: parse_u64(attribute(size, "width")?)?,
        height_hwpunit: parse_u64(attribute(size, "height")?)?,
    }) != node.bounds
        || parse_bool01(attribute(sz, "protect")?)? != node.protected
    {
        return Err(DrawingCanvasHwpxError::UnsupportedProfile);
    }
    match node.kind {
        CanvasNodeKind::Picture => validate_picture(document, native, node, state),
        CanvasNodeKind::Container
        | CanvasNodeKind::Line
        | CanvasNodeKind::Rectangle
        | CanvasNodeKind::Ellipse
        | CanvasNodeKind::Arc
        | CanvasNodeKind::Polygon
        | CanvasNodeKind::Curve
        | CanvasNodeKind::Connector => {
            if !node.resource_refs.is_empty() || node.picture.is_some() {
                return Err(DrawingCanvasHwpxError::UnsupportedProfile);
            }
            Ok(())
        }
        CanvasNodeKind::OpaqueOle => Err(DrawingCanvasHwpxError::UnsupportedProfile),
    }
}

fn validate_picture(
    document: &PreservingXmlDocument,
    native: &XmlElementToken,
    node: &CanvasNode,
    state: &DrawingCanvasState,
) -> Result<(), DrawingCanvasHwpxError> {
    let picture = node
        .picture
        .as_ref()
        .ok_or(DrawingCanvasHwpxError::UnsupportedProfile)?;
    if picture.effects.is_some()
        || node.resource_refs.as_slice() != [picture.image_resource_id.clone()]
    {
        return Err(DrawingCanvasHwpxError::UnsupportedProfile);
    }
    let resource = state
        .resource(&picture.image_resource_id)
        .ok_or(DrawingCanvasHwpxError::UnsupportedProfile)?;
    if resource.kind != CanvasResourceKind::EmbeddedImage {
        return Err(DrawingCanvasHwpxError::UnsupportedProfile);
    }
    let image = unique_child(document, native, CORE_NS, "img")?;
    if attribute(image, "binaryItemIDRef")? != resource.relationship_id {
        return Err(DrawingCanvasHwpxError::UnsupportedProfile);
    }
    let clip = unique_child(document, native, PARAGRAPH_NS, "imgClip")?;
    let expected = picture.clip.unwrap_or(ImageClip {
        left_px: 0,
        right_px: picture.original_width_px,
        top_px: 0,
        bottom_px: picture.original_height_px,
    });
    if read_clip(clip)? != expected {
        return Err(DrawingCanvasHwpxError::UnsupportedProfile);
    }
    let dimensions = unique_child(document, native, PARAGRAPH_NS, "imgDim")?;
    if parse_u32(attribute(dimensions, "dimwidth")?)? != picture.original_width_px
        || parse_u32(attribute(dimensions, "dimheight")?)? != picture.original_height_px
    {
        return Err(DrawingCanvasHwpxError::UnsupportedProfile);
    }
    Ok(())
}

fn render_target(
    source_xml: &[u8],
    run_ordinal: usize,
    source: &DrawingCanvasState,
    target: &DrawingCanvasState,
    limits: DrawingCanvasHwpxLimits,
) -> Result<Vec<u8>, DrawingCanvasHwpxError> {
    let island = inspect_island(source_xml, source, run_ordinal, limits)?;
    let mut rendered = String::new();
    for root in ordered_children(target, None) {
        rendered.push_str(&render_node(&island, source, target, root, limits)?);
        if rendered.len() > limits.0.output_bytes {
            return Err(DrawingCanvasHwpxError::OutputLimit);
        }
    }
    apply_edits(
        source_xml,
        vec![ByteEdit {
            span: island.island_span,
            replacement: rendered,
        }],
        limits,
    )
}

fn render_node(
    island: &ParsedIsland,
    source: &DrawingCanvasState,
    target: &DrawingCanvasState,
    node: &CanvasNode,
    limits: DrawingCanvasHwpxLimits,
) -> Result<String, DrawingCanvasHwpxError> {
    let mut children = String::new();
    for child in ordered_children(target, Some(&node.node_id)) {
        children.push_str(&render_node(island, source, target, child, limits)?);
    }
    if let Some(native) = island.nodes.get(&node.node_id) {
        let source_node = source
            .node(&node.node_id)
            .ok_or(DrawingCanvasHwpxError::UnsupportedProfile)?;
        let mut expected = source_node.clone();
        if source_node.kind == CanvasNodeKind::Picture {
            let target_picture = node
                .picture
                .as_ref()
                .ok_or(DrawingCanvasHwpxError::PreservationDrift)?;
            let expected_picture = expected
                .picture
                .as_mut()
                .ok_or(DrawingCanvasHwpxError::PreservationDrift)?;
            expected_picture.clip = target_picture.clip;
            expected
                .bindings
                .payload_sha256
                .clone_from(&node.bindings.payload_sha256);
        }
        if expected != *node {
            return Err(DrawingCanvasHwpxError::PreservationDrift);
        }
        let fragment = island.document.source_text(native.outer_span)?;
        return patch_existing_fragment(fragment, node, &children, limits);
    }
    generate_node(node, &children, limits)
}

fn patch_existing_fragment(
    fragment: &str,
    target: &CanvasNode,
    rendered_children: &str,
    limits: DrawingCanvasHwpxLimits,
) -> Result<String, DrawingCanvasHwpxError> {
    let prefix = format!(
        "<x:root xmlns:x=\"{WRAPPER_NS}\" xmlns:hp=\"{PARAGRAPH_NS}\" xmlns:hc=\"{CORE_NS}\">"
    );
    let suffix = "</x:root>";
    let wrapped = format!("{prefix}{fragment}{suffix}");
    let document = PreservingXmlDocument::parse(wrapped.as_bytes())?;
    let roots = direct_node_children(&document, document.root_element())?;
    if roots.len() != 1 {
        return Err(DrawingCanvasHwpxError::UnsupportedProfile);
    }
    let root = element(&document, roots[0])?;
    let mut edits = vec![
        value_edit(root, "zOrder", target.ordinal.to_string())?,
        value_edit(root, "groupLevel", target.group_level.to_string())?,
    ];
    let offset = unique_child(&document, root, PARAGRAPH_NS, "offset")?;
    edits.push(value_edit(
        offset,
        "x",
        target.bounds.x_hwpunit.to_string(),
    )?);
    edits.push(value_edit(
        offset,
        "y",
        target.bounds.y_hwpunit.to_string(),
    )?);
    let size = unique_child(&document, root, PARAGRAPH_NS, "curSz")?;
    edits.push(value_edit(
        size,
        "width",
        target.bounds.width_hwpunit.to_string(),
    )?);
    edits.push(value_edit(
        size,
        "height",
        target.bounds.height_hwpunit.to_string(),
    )?);
    let sz = unique_child(&document, root, PARAGRAPH_NS, "sz")?;
    edits.push(value_edit(
        sz,
        "protect",
        if target.protected { "1" } else { "0" }.to_owned(),
    )?);
    if target.kind == CanvasNodeKind::Container {
        let children = direct_node_children(&document, roots[0])?;
        if children.is_empty() {
            return Err(DrawingCanvasHwpxError::UnsupportedProfile);
        }
        require_whitespace_between(wrapped.as_bytes(), &document, &children)?;
        let first = element(&document, children[0])?
            .outer_span()
            .ok_or(DrawingCanvasHwpxError::UnsupportedProfile)?;
        let last = element(
            &document,
            *children
                .last()
                .ok_or(DrawingCanvasHwpxError::UnsupportedProfile)?,
        )?
        .outer_span()
        .ok_or(DrawingCanvasHwpxError::UnsupportedProfile)?;
        edits.push(ByteEdit {
            span: ByteRange::new(wrapped.as_bytes(), first.start(), last.end())?,
            replacement: rendered_children.to_owned(),
        });
    } else if target.kind == CanvasNodeKind::Picture {
        let picture = target
            .picture
            .as_ref()
            .ok_or(DrawingCanvasHwpxError::UnsupportedProfile)?;
        let clip = unique_child(&document, root, PARAGRAPH_NS, "imgClip")?;
        let target_clip = picture.clip.unwrap_or(ImageClip {
            left_px: 0,
            right_px: picture.original_width_px,
            top_px: 0,
            bottom_px: picture.original_height_px,
        });
        edits.push(value_edit(clip, "left", target_clip.left_px.to_string())?);
        edits.push(value_edit(clip, "right", target_clip.right_px.to_string())?);
        edits.push(value_edit(clip, "top", target_clip.top_px.to_string())?);
        edits.push(value_edit(
            clip,
            "bottom",
            target_clip.bottom_px.to_string(),
        )?);
    } else if !rendered_children.is_empty() {
        return Err(DrawingCanvasHwpxError::UnsupportedProfile);
    }
    let output = apply_edits(wrapped.as_bytes(), edits, limits)?;
    let output = std::str::from_utf8(&output).map_err(|_| DrawingCanvasHwpxError::Serialization)?;
    if !output.starts_with(&prefix) || !output.ends_with(suffix) {
        return Err(DrawingCanvasHwpxError::Serialization);
    }
    Ok(output[prefix.len()..output.len() - suffix.len()].to_owned())
}

fn generate_node(
    node: &CanvasNode,
    children: &str,
    limits: DrawingCanvasHwpxLimits,
) -> Result<String, DrawingCanvasHwpxError> {
    require_generated_bindings(node)?;
    let output = match node.kind {
        CanvasNodeKind::Container if !children.is_empty() => format!(
            "<hp:container id=\"{}\" zOrder=\"{}\" numberingType=\"CONTAINER\" textWrap=\"TOP_AND_BOTTOM\" textFlow=\"BOTH_SIDES\" lock=\"0\" dropcapstyle=\"None\" href=\"\" groupLevel=\"{}\" instid=\"{}\">{}{}{}{}{}{}</hp:container>",
            node.native_object_id,
            node.ordinal,
            node.group_level,
            node.native_instance_id,
            common_component(&node.bounds),
            rotation_rendering(),
            size_fragment(&node.bounds, node.protected),
            position_fragment(),
            margin_fragment(),
            children
        ),
        CanvasNodeKind::Rectangle if children.is_empty() => format!(
            "<hp:rect id=\"{}\" zOrder=\"{}\" numberingType=\"DRAWING\" textWrap=\"TOP_AND_BOTTOM\" textFlow=\"BOTH_SIDES\" lock=\"0\" dropcapstyle=\"None\" href=\"\" groupLevel=\"{}\" instid=\"{}\">{}{}{}{}{}<hp:pt0 x=\"0\" y=\"0\"/><hp:pt1 x=\"{}\" y=\"0\"/><hp:pt2 x=\"{}\" y=\"{}\"/><hp:pt3 x=\"0\" y=\"{}\"/></hp:rect>",
            node.native_object_id,
            node.ordinal,
            node.group_level,
            node.native_instance_id,
            common_component(&node.bounds),
            rotation_rendering(),
            size_fragment(&node.bounds, node.protected),
            position_fragment(),
            margin_fragment(),
            node.bounds.width_hwpunit,
            node.bounds.width_hwpunit,
            node.bounds.height_hwpunit,
            node.bounds.height_hwpunit
        ),
        _ => return Err(DrawingCanvasHwpxError::UnsupportedProfile),
    };
    if output.len() > limits.0.output_bytes {
        return Err(DrawingCanvasHwpxError::OutputLimit);
    }
    Ok(output)
}

fn require_generated_bindings(node: &CanvasNode) -> Result<(), DrawingCanvasHwpxError> {
    if !node.visible
        || !node.printable
        || node.bindings.geometry_sha256 != EMPTY_SHA256
        || node.bindings.payload_sha256 != EMPTY_SHA256
        || node.bindings.appearance_sha256 != EMPTY_SHA256
        || node.bindings.composition_sha256 != EMPTY_SHA256
        || node.bindings.opaque_sha256 != EMPTY_SHA256
        || node.bindings.opaque_byte_length != 0
        || !node.resource_refs.is_empty()
        || node.picture.is_some()
    {
        return Err(DrawingCanvasHwpxError::UnsupportedProfile);
    }
    Ok(())
}

fn common_component(bounds: &CanvasBounds) -> String {
    format!(
        "<hp:offset x=\"{}\" y=\"{}\"/><hp:orgSz width=\"{}\" height=\"{}\"/><hp:curSz width=\"{}\" height=\"{}\"/><hp:flip horizontal=\"0\" vertical=\"0\"/>",
        bounds.x_hwpunit,
        bounds.y_hwpunit,
        bounds.width_hwpunit,
        bounds.height_hwpunit,
        bounds.width_hwpunit,
        bounds.height_hwpunit
    )
}

fn rotation_rendering() -> &'static str {
    "<hp:rotationInfo angle=\"0\" centerX=\"0\" centerY=\"0\" rotateimage=\"1\"/><hp:renderingInfo><hc:transMatrix e1=\"1\" e2=\"0\" e3=\"0\" e4=\"1\" e5=\"0\" e6=\"0\"/><hc:scaMatrix e1=\"1\" e2=\"0\" e3=\"0\" e4=\"1\" e5=\"0\" e6=\"0\"/><hc:rotMatrix e1=\"1\" e2=\"0\" e3=\"0\" e4=\"1\" e5=\"0\" e6=\"0\"/></hp:renderingInfo>"
}

fn size_fragment(bounds: &CanvasBounds, protected: bool) -> String {
    format!(
        "<hp:sz width=\"{}\" widthRelTo=\"ABSOLUTE\" height=\"{}\" heightRelTo=\"ABSOLUTE\" protect=\"{}\"/>",
        bounds.width_hwpunit,
        bounds.height_hwpunit,
        u8::from(protected)
    )
}

fn position_fragment() -> &'static str {
    "<hp:pos treatAsChar=\"0\" affectLSpacing=\"0\" flowWithText=\"1\" allowOverlap=\"0\" holdAnchorAndSO=\"1\" vertRelTo=\"PARA\" horzRelTo=\"PARA\" vertAlign=\"TOP\" horzAlign=\"LEFT\" vertOffset=\"0\" horzOffset=\"0\"/>"
}

fn margin_fragment() -> &'static str {
    "<hp:outMargin left=\"0\" right=\"0\" top=\"0\" bottom=\"0\"/>"
}

fn ordered_children<'a>(
    state: &'a DrawingCanvasState,
    parent: Option<&LogicalId>,
) -> Vec<&'a CanvasNode> {
    let mut nodes: Vec<_> = state
        .nodes()
        .iter()
        .filter(|node| node.parent_id.as_ref() == parent)
        .collect();
    nodes.sort_by_key(|node| node.ordinal);
    nodes
}

fn node_tag(element: &XmlElementToken) -> Option<&str> {
    if element.name().namespace() != Some(PARAGRAPH_NS) {
        return None;
    }
    match element.name().local_name() {
        tag @ ("container" | "line" | "rect" | "ellipse" | "arc" | "polygon" | "curve"
        | "connectLine" | "pic" | "ole") => Some(tag),
        _ => None,
    }
}

const fn node_tag_for_kind(kind: CanvasNodeKind) -> &'static str {
    match kind {
        CanvasNodeKind::Container => "container",
        CanvasNodeKind::Line => "line",
        CanvasNodeKind::Rectangle => "rect",
        CanvasNodeKind::Ellipse => "ellipse",
        CanvasNodeKind::Arc => "arc",
        CanvasNodeKind::Polygon => "polygon",
        CanvasNodeKind::Curve => "curve",
        CanvasNodeKind::Connector => "connectLine",
        CanvasNodeKind::Picture => "pic",
        CanvasNodeKind::OpaqueOle => "ole",
    }
}

fn direct_node_children(
    document: &PreservingXmlDocument,
    parent: usize,
) -> Result<Vec<usize>, DrawingCanvasHwpxError> {
    let mut values = Vec::new();
    let mut child = element(document, parent)?.first_child();
    while let Some(index) = child {
        let candidate = element(document, index)?;
        if node_tag(candidate).is_some() {
            values.push(index);
        }
        child = candidate.next_sibling();
    }
    Ok(values)
}

fn unique_child<'a>(
    document: &'a PreservingXmlDocument,
    parent: &XmlElementToken,
    namespace: &str,
    local: &str,
) -> Result<&'a XmlElementToken, DrawingCanvasHwpxError> {
    let mut values = Vec::new();
    let mut child = parent.first_child();
    while let Some(index) = child {
        let candidate = element(document, index)?;
        if has_name(candidate, namespace, local) {
            values.push(candidate);
        }
        child = candidate.next_sibling();
    }
    if values.len() != 1 {
        return Err(DrawingCanvasHwpxError::UnsupportedProfile);
    }
    Ok(values[0])
}

fn has_name(element: &XmlElementToken, namespace: &str, local: &str) -> bool {
    element.name().namespace() == Some(namespace) && element.name().local_name() == local
}

fn element(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<&XmlElementToken, DrawingCanvasHwpxError> {
    document
        .elements()
        .get(index)
        .ok_or(DrawingCanvasHwpxError::UnsupportedProfile)
}

fn attribute<'a>(
    element: &'a XmlElementToken,
    local: &str,
) -> Result<&'a str, DrawingCanvasHwpxError> {
    let mut values = element.attributes().iter().filter(|attribute| {
        !attribute.is_namespace_declaration()
            && attribute.name().namespace().is_none()
            && attribute.name().local_name() == local
    });
    let value = values
        .next()
        .ok_or(DrawingCanvasHwpxError::UnsupportedProfile)?;
    if values.next().is_some() {
        return Err(DrawingCanvasHwpxError::UnsupportedProfile);
    }
    Ok(value.semantic_value())
}

fn read_clip(element: &XmlElementToken) -> Result<ImageClip, DrawingCanvasHwpxError> {
    Ok(ImageClip {
        left_px: parse_u32(attribute(element, "left")?)?,
        right_px: parse_u32(attribute(element, "right")?)?,
        top_px: parse_u32(attribute(element, "top")?)?,
        bottom_px: parse_u32(attribute(element, "bottom")?)?,
    })
}

fn value_edit(
    element: &XmlElementToken,
    local: &str,
    replacement: String,
) -> Result<ByteEdit, DrawingCanvasHwpxError> {
    let attribute = element
        .attributes()
        .iter()
        .find(|attribute| {
            !attribute.is_namespace_declaration()
                && attribute.name().namespace().is_none()
                && attribute.name().local_name() == local
        })
        .ok_or(DrawingCanvasHwpxError::UnsupportedProfile)?;
    Ok(ByteEdit {
        span: attribute.value_span().into(),
        replacement,
    })
}

fn require_whitespace_between(
    source: &[u8],
    document: &PreservingXmlDocument,
    indexes: &[usize],
) -> Result<(), DrawingCanvasHwpxError> {
    for pair in indexes.windows(2) {
        let left = element(document, pair[0])?
            .outer_span()
            .ok_or(DrawingCanvasHwpxError::UnsupportedProfile)?;
        let right = element(document, pair[1])?
            .outer_span()
            .ok_or(DrawingCanvasHwpxError::UnsupportedProfile)?;
        let between = source
            .get(left.end()..right.start())
            .ok_or(DrawingCanvasHwpxError::UnsupportedProfile)?;
        if !std::str::from_utf8(between)
            .map_err(|_| DrawingCanvasHwpxError::Serialization)?
            .trim()
            .is_empty()
        {
            return Err(DrawingCanvasHwpxError::UnsupportedProfile);
        }
    }
    Ok(())
}

fn parse_u32(value: &str) -> Result<u32, DrawingCanvasHwpxError> {
    value
        .parse()
        .map_err(|_| DrawingCanvasHwpxError::UnsupportedProfile)
}

fn parse_u64(value: &str) -> Result<u64, DrawingCanvasHwpxError> {
    value
        .parse()
        .map_err(|_| DrawingCanvasHwpxError::UnsupportedProfile)
}

fn parse_i64(value: &str) -> Result<i64, DrawingCanvasHwpxError> {
    value
        .parse()
        .map_err(|_| DrawingCanvasHwpxError::UnsupportedProfile)
}

fn parse_bool01(value: &str) -> Result<bool, DrawingCanvasHwpxError> {
    match value {
        "0" => Ok(false),
        "1" => Ok(true),
        _ => Err(DrawingCanvasHwpxError::UnsupportedProfile),
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct ByteRange {
    start: usize,
    end: usize,
}

impl ByteRange {
    fn new(source: &[u8], start: usize, end: usize) -> Result<Self, DrawingCanvasHwpxError> {
        let text =
            std::str::from_utf8(source).map_err(|_| DrawingCanvasHwpxError::Serialization)?;
        if start > end
            || end > source.len()
            || !text.is_char_boundary(start)
            || !text.is_char_boundary(end)
        {
            return Err(DrawingCanvasHwpxError::UnsupportedProfile);
        }
        Ok(Self { start, end })
    }

    const fn len(self) -> usize {
        self.end - self.start
    }
}

impl From<XmlByteSpan> for ByteRange {
    fn from(span: XmlByteSpan) -> Self {
        Self {
            start: span.start(),
            end: span.end(),
        }
    }
}

#[derive(Debug)]
struct ByteEdit {
    span: ByteRange,
    replacement: String,
}

fn apply_edits(
    source: &[u8],
    mut edits: Vec<ByteEdit>,
    limits: DrawingCanvasHwpxLimits,
) -> Result<Vec<u8>, DrawingCanvasHwpxError> {
    edits.sort_by_key(|edit| edit.span.start);
    if edits
        .windows(2)
        .any(|pair| pair[0].span.end > pair[1].span.start)
    {
        return Err(DrawingCanvasHwpxError::PreservationDrift);
    }
    let removed: usize = edits.iter().map(|edit| edit.span.len()).sum();
    let added: usize = edits.iter().map(|edit| edit.replacement.len()).sum();
    let capacity = source
        .len()
        .checked_sub(removed)
        .and_then(|value| value.checked_add(added))
        .ok_or(DrawingCanvasHwpxError::OutputLimit)?;
    if capacity > limits.0.output_bytes {
        return Err(DrawingCanvasHwpxError::OutputLimit);
    }
    let mut output = Vec::with_capacity(capacity);
    let mut cursor = 0;
    for edit in edits {
        output.extend_from_slice(
            source
                .get(cursor..edit.span.start)
                .ok_or(DrawingCanvasHwpxError::PreservationDrift)?,
        );
        output.extend_from_slice(edit.replacement.as_bytes());
        cursor = edit.span.end;
    }
    output.extend_from_slice(
        source
            .get(cursor..)
            .ok_or(DrawingCanvasHwpxError::PreservationDrift)?,
    );
    Ok(output)
}

fn outside_island_equal(
    source: &[u8],
    source_span: ByteRange,
    target: &[u8],
    target_span: ByteRange,
) -> bool {
    source.get(..source_span.start) == target.get(..target_span.start)
        && source.get(source_span.end..) == target.get(target_span.end..)
}

fn plan_binding_sha256(plan: &DrawingCanvasHwpxPlan) -> Result<String, DrawingCanvasHwpxError> {
    #[derive(Serialize)]
    struct Binding<'a> {
        profile_id: &'static str,
        capability_id: &'static str,
        domain_plan_sha256: &'a str,
        run_ordinal: usize,
        source_section_sha256: &'a str,
        target_section_sha256: &'a str,
        source_state_sha256: &'a str,
        target_state_sha256: &'a str,
        source_document_flow_sha256: &'a str,
        target_document_flow_sha256: &'a str,
    }
    let bytes = serde_json::to_vec(&Binding {
        profile_id: plan.profile_id,
        capability_id: plan.capability_id,
        domain_plan_sha256: plan.domain_plan.plan_sha256(),
        run_ordinal: plan.run_ordinal,
        source_section_sha256: &plan.source_section_sha256,
        target_section_sha256: &plan.target_section_sha256,
        source_state_sha256: &plan.source_state_sha256,
        target_state_sha256: &plan.target_state_sha256,
        source_document_flow_sha256: &plan.source_document_flow_sha256,
        target_document_flow_sha256: &plan.target_document_flow_sha256,
    })
    .map_err(|_| DrawingCanvasHwpxError::Serialization)?;
    Ok(sha256(&bytes))
}

fn sha256(bytes: &[u8]) -> String {
    let digest: [u8; 32] = Sha256::digest(bytes).into();
    let mut output = String::with_capacity(64);
    for byte in digest {
        use std::fmt::Write as _;
        let _ = write!(&mut output, "{byte:02x}");
    }
    output
}
