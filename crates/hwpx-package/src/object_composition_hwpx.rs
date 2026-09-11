use std::collections::{BTreeMap, BTreeSet};
use std::fmt;
use std::fmt::Write as _;

use domain_ir::{
    CompositionBounds, CompositionObject, CompositionObjectKind, ConnectorEndpoint, ConnectorKind,
    ConnectorTopology, LogicalId, ObjectCompositionBuilder, ObjectCompositionError,
    ObjectCompositionGraph, ObjectCompositionLimits, ObjectCompositionPlan,
    ObjectCompositionRequest,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{PreservingXmlDocument, PreservingXmlError, XmlByteSpan, XmlElementToken};

pub const OBJECT_COMPOSITION_HWPX_PROFILE_ID: &str =
    "hwpx-agent.object-composition-hwpx.hwpml-2011-static/v1";

const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const CORE_NS: &str = "http://www.hancom.co.kr/hwpml/2011/core";
const WRAPPER_NS: &str = "urn:hwpx-agent:fragment-wrapper";
const EMPTY_SHA256: &str = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ObjectCompositionHwpxLimitConfig {
    pub section_bytes: usize,
    pub output_bytes: usize,
    pub elements: usize,
    pub objects: usize,
}

impl Default for ObjectCompositionHwpxLimitConfig {
    fn default() -> Self {
        Self {
            section_bytes: 32 * 1024 * 1024,
            output_bytes: 32 * 1024 * 1024,
            elements: 1_000_000,
            objects: 65_536,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ObjectCompositionHwpxLimits(ObjectCompositionHwpxLimitConfig);

impl ObjectCompositionHwpxLimits {
    pub const HARD_MAX_BYTES: usize = 256 * 1024 * 1024;
    pub const HARD_MAX_ELEMENTS: usize = 4_000_000;
    pub const HARD_MAX_OBJECTS: usize = 1_000_000;

    /// Creates finite limits for one native composition island.
    ///
    /// # Errors
    ///
    /// Rejects zero, inconsistent or process-hostile limits.
    pub fn new(
        config: ObjectCompositionHwpxLimitConfig,
    ) -> Result<Self, ObjectCompositionHwpxError> {
        if config.section_bytes == 0
            || config.output_bytes < config.section_bytes
            || config.output_bytes > Self::HARD_MAX_BYTES
            || config.elements == 0
            || config.elements > Self::HARD_MAX_ELEMENTS
            || config.objects == 0
            || config.objects > Self::HARD_MAX_OBJECTS
        {
            return Err(ObjectCompositionHwpxError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> ObjectCompositionHwpxLimitConfig {
        self.0
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ObjectCompositionHwpxReadback {
    profile_id: &'static str,
    section_sha256: String,
    graph_sha256: String,
    island_sha256: String,
    object_count: usize,
}

impl ObjectCompositionHwpxReadback {
    #[must_use]
    pub fn section_sha256(&self) -> &str {
        &self.section_sha256
    }

    #[must_use]
    pub fn graph_sha256(&self) -> &str {
        &self.graph_sha256
    }

    #[must_use]
    pub fn island_sha256(&self) -> &str {
        &self.island_sha256
    }

    #[must_use]
    pub const fn object_count(&self) -> usize {
        self.object_count
    }
}

impl fmt::Debug for ObjectCompositionHwpxReadback {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectCompositionHwpxReadback")
            .field("profile_id", &self.profile_id)
            .field("object_count", &self.object_count)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ObjectCompositionHwpxPlan {
    profile_id: &'static str,
    capability_id: &'static str,
    domain_plan: ObjectCompositionPlan,
    source_section_sha256: String,
    target_section_sha256: String,
    source_graph_sha256: String,
    target_graph_sha256: String,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    plan_sha256: String,
}

impl ObjectCompositionHwpxPlan {
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

impl fmt::Debug for ObjectCompositionHwpxPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectCompositionHwpxPlan")
            .field("profile_id", &self.profile_id)
            .field("capability_id", &self.capability_id)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ObjectCompositionHwpxLoweringReceipt {
    profile_id: &'static str,
    capability_id: &'static str,
    source_section_sha256: String,
    target_section_sha256: String,
    source_graph_sha256: String,
    target_graph_sha256: String,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    plan_sha256: String,
    semantic_reopen: bool,
    outside_island_preserved: bool,
}

impl ObjectCompositionHwpxLoweringReceipt {
    #[must_use]
    pub const fn semantic_reopen(&self) -> bool {
        self.semantic_reopen
    }

    #[must_use]
    pub const fn outside_island_preserved(&self) -> bool {
        self.outside_island_preserved
    }
}

impl fmt::Debug for ObjectCompositionHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectCompositionHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field("capability_id", &self.capability_id)
            .field("semantic_reopen", &self.semantic_reopen)
            .field("outside_island_preserved", &self.outside_island_preserved)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct ObjectCompositionHwpxLowered {
    pub section_xml: Vec<u8>,
    pub readback: ObjectCompositionHwpxReadback,
    pub receipt: ObjectCompositionHwpxLoweringReceipt,
}

impl fmt::Debug for ObjectCompositionHwpxLowered {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectCompositionHwpxLowered")
            .field("section_bytes", &self.section_xml.len())
            .field("readback", &self.readback)
            .field("receipt", &self.receipt)
            .finish()
    }
}

#[derive(Debug)]
pub struct ObjectCompositionHwpxReader;

impl ObjectCompositionHwpxReader {
    /// Reopens one closed native object island and matches it to the complete domain graph.
    ///
    /// # Errors
    ///
    /// Rejects malformed XML, non-closed islands and any identity, topology or geometry drift.
    pub fn read(
        section_xml: &[u8],
        graph: &ObjectCompositionGraph,
        graph_limits: ObjectCompositionLimits,
        limits: ObjectCompositionHwpxLimits,
    ) -> Result<ObjectCompositionHwpxReadback, ObjectCompositionHwpxError> {
        let island = inspect_island(section_xml, graph, limits)?;
        Ok(ObjectCompositionHwpxReadback {
            profile_id: OBJECT_COMPOSITION_HWPX_PROFILE_ID,
            section_sha256: sha256(section_xml),
            graph_sha256: graph.canonical_sha256(graph_limits)?,
            island_sha256: sha256(island.island_bytes()),
            object_count: island.objects.len(),
        })
    }
}

#[derive(Debug)]
pub struct ObjectCompositionHwpxBuilder;

impl ObjectCompositionHwpxBuilder {
    /// Seals exact source/target XML, graph and flow bindings before lowering.
    ///
    /// # Errors
    ///
    /// Rejects stale source state, unsupported native structure or non-reopenable output.
    pub fn plan(
        section_xml: &[u8],
        source: &ObjectCompositionGraph,
        request: &ObjectCompositionRequest,
        current_document_flow_sha256: &str,
        graph_limits: ObjectCompositionLimits,
        limits: ObjectCompositionHwpxLimits,
    ) -> Result<ObjectCompositionHwpxPlan, ObjectCompositionHwpxError> {
        if request.expected_source_state_sha256() != source.canonical_sha256(graph_limits)? {
            return Err(ObjectCompositionHwpxError::SourceStateDrift);
        }
        if request.expected_document_flow_sha256() != current_document_flow_sha256 {
            return Err(ObjectCompositionHwpxError::DocumentFlowDrift);
        }
        let source_readback =
            ObjectCompositionHwpxReader::read(section_xml, source, graph_limits, limits)?;
        let domain_plan = ObjectCompositionBuilder::plan(
            source,
            request,
            current_document_flow_sha256,
            graph_limits,
        )?;
        let target_xml = render_target(section_xml, source, domain_plan.target_state(), limits)?;
        let target_readback = ObjectCompositionHwpxReader::read(
            &target_xml,
            domain_plan.target_state(),
            graph_limits,
            limits,
        )?;
        let target_graph_sha256 = domain_plan.target_state().canonical_sha256(graph_limits)?;
        let mut plan = ObjectCompositionHwpxPlan {
            profile_id: OBJECT_COMPOSITION_HWPX_PROFILE_ID,
            capability_id: domain_plan.capability_id(),
            domain_plan,
            source_section_sha256: source_readback.section_sha256,
            target_section_sha256: target_readback.section_sha256,
            source_graph_sha256: source.canonical_sha256(graph_limits)?,
            target_graph_sha256,
            source_document_flow_sha256: current_document_flow_sha256.to_owned(),
            target_document_flow_sha256: request.target_document_flow_sha256().to_owned(),
            plan_sha256: String::new(),
        };
        plan.plan_sha256 = plan_binding_sha256(&plan)?;
        Ok(plan)
    }
}

#[derive(Debug)]
pub struct ObjectCompositionHwpxLowerer;

impl ObjectCompositionHwpxLowerer {
    /// Rechecks every binding, replaces only the closed island and strictly reopens the result.
    ///
    /// # Errors
    ///
    /// Rejects plan tampering, source/flow drift, preservation failure or semantic readback drift.
    pub fn lower(
        plan: &ObjectCompositionHwpxPlan,
        current_section_xml: &[u8],
        current: &ObjectCompositionGraph,
        current_document_flow_sha256: &str,
        graph_limits: ObjectCompositionLimits,
        limits: ObjectCompositionHwpxLimits,
    ) -> Result<ObjectCompositionHwpxLowered, ObjectCompositionHwpxError> {
        if plan.profile_id != OBJECT_COMPOSITION_HWPX_PROFILE_ID
            || plan.capability_id != plan.domain_plan.capability_id()
            || plan_binding_sha256(plan)? != plan.plan_sha256
            || plan.source_graph_sha256 != current.canonical_sha256(graph_limits)?
            || plan.target_graph_sha256
                != plan
                    .domain_plan
                    .target_state()
                    .canonical_sha256(graph_limits)?
        {
            return Err(ObjectCompositionHwpxError::PlanTampered);
        }
        if sha256(current_section_xml) != plan.source_section_sha256 {
            return Err(ObjectCompositionHwpxError::SourceStateDrift);
        }
        if current_document_flow_sha256 != plan.source_document_flow_sha256 {
            return Err(ObjectCompositionHwpxError::DocumentFlowDrift);
        }
        let source_island = inspect_island(current_section_xml, current, limits)?;
        let domain_result = ObjectCompositionBuilder::build(
            &plan.domain_plan,
            current,
            current_document_flow_sha256,
            graph_limits,
        )?;
        let target_xml = render_target(current_section_xml, current, &domain_result.state, limits)?;
        if target_xml.len() > limits.0.output_bytes
            || sha256(&target_xml) != plan.target_section_sha256
        {
            return Err(ObjectCompositionHwpxError::PlanTampered);
        }
        let target_island = inspect_island(&target_xml, &domain_result.state, limits)?;
        let outside_preserved = outside_island_equal(
            current_section_xml,
            source_island.island_span,
            &target_xml,
            target_island.island_span,
        );
        if !outside_preserved {
            return Err(ObjectCompositionHwpxError::PreservationDrift);
        }
        let readback = ObjectCompositionHwpxReader::read(
            &target_xml,
            &domain_result.state,
            graph_limits,
            limits,
        )?;
        Ok(ObjectCompositionHwpxLowered {
            section_xml: target_xml,
            readback,
            receipt: ObjectCompositionHwpxLoweringReceipt {
                profile_id: OBJECT_COMPOSITION_HWPX_PROFILE_ID,
                capability_id: plan.capability_id,
                source_section_sha256: plan.source_section_sha256.clone(),
                target_section_sha256: plan.target_section_sha256.clone(),
                source_graph_sha256: plan.source_graph_sha256.clone(),
                target_graph_sha256: plan.target_graph_sha256.clone(),
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
pub enum ObjectCompositionHwpxError {
    #[error("object-composition HWPX limits are invalid")]
    InvalidLimit,
    #[error("object-composition HWPX input exceeds a finite limit")]
    InputLimit,
    #[error("object-composition HWPX XML is invalid")]
    Xml(#[from] PreservingXmlError),
    #[error("object-composition domain state is invalid")]
    Domain(#[from] ObjectCompositionError),
    #[error("object-composition HWPX profile is unsupported")]
    UnsupportedProfile,
    #[error("object-composition HWPX source state drifted")]
    SourceStateDrift,
    #[error("object-composition HWPX document flow drifted")]
    DocumentFlowDrift,
    #[error("object-composition HWPX plan was tampered with")]
    PlanTampered,
    #[error("object-composition HWPX preservation failed")]
    PreservationDrift,
    #[error("object-composition HWPX output exceeds a finite limit")]
    OutputLimit,
    #[error("object-composition HWPX serialization failed")]
    Serialization,
}

impl ObjectCompositionHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "object_composition_hwpx_invalid_limit",
            Self::InputLimit => "object_composition_hwpx_input_limit",
            Self::Xml(_) => "object_composition_hwpx_xml",
            Self::Domain(_) => "object_composition_hwpx_domain",
            Self::UnsupportedProfile => "object_composition_hwpx_unsupported_profile",
            Self::SourceStateDrift => "object_composition_hwpx_source_state_drift",
            Self::DocumentFlowDrift => "object_composition_hwpx_document_flow_drift",
            Self::PlanTampered => "object_composition_hwpx_plan_tampered",
            Self::PreservationDrift => "object_composition_hwpx_preservation_drift",
            Self::OutputLimit => "object_composition_hwpx_output_limit",
            Self::Serialization => "object_composition_hwpx_serialization",
        }
    }
}

struct NativeObject {
    element_index: usize,
    outer_span: XmlByteSpan,
}

struct ParsedIsland {
    document: PreservingXmlDocument,
    objects: BTreeMap<LogicalId, NativeObject>,
    island_span: ByteRange,
    island_bytes: Vec<u8>,
}

impl ParsedIsland {
    fn island_bytes(&self) -> &[u8] {
        &self.island_bytes
    }
}

#[allow(clippy::too_many_lines)] // One reviewed pass keeps native identity/topology closure atomic.
fn inspect_island(
    section_xml: &[u8],
    graph: &ObjectCompositionGraph,
    limits: ObjectCompositionHwpxLimits,
) -> Result<ParsedIsland, ObjectCompositionHwpxError> {
    if section_xml.is_empty() || section_xml.len() > limits.0.section_bytes {
        return Err(ObjectCompositionHwpxError::InputLimit);
    }
    if graph.objects().len() > limits.0.objects {
        return Err(ObjectCompositionHwpxError::InputLimit);
    }
    let document = PreservingXmlDocument::parse(section_xml)?;
    if document.elements().len() > limits.0.elements {
        return Err(ObjectCompositionHwpxError::InputLimit);
    }
    let mut by_native = BTreeMap::new();
    for (index, element) in document.elements().iter().enumerate() {
        if object_tag(element).is_none() {
            continue;
        }
        let native_id = parse_u32(attribute(element, "id")?)?;
        if by_native.insert(native_id, index).is_some() {
            return Err(ObjectCompositionHwpxError::UnsupportedProfile);
        }
    }
    let mut objects = BTreeMap::new();
    let mut root_parent = None;
    let graph_ids: BTreeSet<_> = graph
        .objects()
        .iter()
        .map(|object| object.object_id.clone())
        .collect();
    for object in graph.objects() {
        let index = *by_native
            .get(&object.native_object_id)
            .ok_or(ObjectCompositionHwpxError::UnsupportedProfile)?;
        let native_element = element(&document, index)?;
        validate_native_object(&document, native_element, object, graph)?;
        let xml_parent = native_element
            .parent()
            .ok_or(ObjectCompositionHwpxError::UnsupportedProfile)?;
        if let Some(parent_id) = &object.parent_group_id {
            let parent = graph
                .object(parent_id)
                .ok_or(ObjectCompositionHwpxError::UnsupportedProfile)?;
            let parent_element = element(&document, xml_parent)?;
            if object_tag(parent_element) != Some("container")
                || parse_u32(attribute(parent_element, "id")?)? != parent.native_object_id
            {
                return Err(ObjectCompositionHwpxError::UnsupportedProfile);
            }
        } else {
            if !has_name(element(&document, xml_parent)?, "run") {
                return Err(ObjectCompositionHwpxError::UnsupportedProfile);
            }
            if root_parent
                .replace(xml_parent)
                .is_some_and(|prior| prior != xml_parent)
            {
                return Err(ObjectCompositionHwpxError::UnsupportedProfile);
            }
        }
        objects.insert(
            object.object_id.clone(),
            NativeObject {
                element_index: index,
                outer_span: native_element
                    .outer_span()
                    .ok_or(ObjectCompositionHwpxError::UnsupportedProfile)?,
            },
        );
    }
    let root_parent = root_parent.ok_or(ObjectCompositionHwpxError::UnsupportedProfile)?;
    let root_elements = direct_object_children(&document, root_parent)?;
    if root_elements.len()
        != graph
            .objects()
            .iter()
            .filter(|object| object.parent_group_id.is_none())
            .count()
    {
        return Err(ObjectCompositionHwpxError::UnsupportedProfile);
    }
    for index in root_elements.iter().copied() {
        let native = parse_u32(attribute(element(&document, index)?, "id")?)?;
        let Some(object) = graph
            .objects()
            .iter()
            .find(|object| object.native_object_id == native)
        else {
            return Err(ObjectCompositionHwpxError::UnsupportedProfile);
        };
        if !graph_ids.contains(&object.object_id) || object.parent_group_id.is_some() {
            return Err(ObjectCompositionHwpxError::UnsupportedProfile);
        }
    }
    for group in graph
        .objects()
        .iter()
        .filter(|object| object.kind == CompositionObjectKind::Group)
    {
        let native = objects
            .get(&group.object_id)
            .ok_or(ObjectCompositionHwpxError::UnsupportedProfile)?;
        let children = direct_object_children(&document, native.element_index)?;
        let expected: Vec<_> = ordered_children(graph, Some(&group.object_id))
            .into_iter()
            .map(|object| object.native_object_id)
            .collect();
        let actual: Result<Vec<_>, _> = children
            .iter()
            .map(|index| parse_u32(attribute(element(&document, *index)?, "id")?))
            .collect();
        if actual? != expected {
            return Err(ObjectCompositionHwpxError::UnsupportedProfile);
        }
    }
    let first = element(
        &document,
        *root_elements
            .first()
            .ok_or(ObjectCompositionHwpxError::UnsupportedProfile)?,
    )?
    .outer_span()
    .ok_or(ObjectCompositionHwpxError::UnsupportedProfile)?;
    let last = element(
        &document,
        *root_elements
            .last()
            .ok_or(ObjectCompositionHwpxError::UnsupportedProfile)?,
    )?
    .outer_span()
    .ok_or(ObjectCompositionHwpxError::UnsupportedProfile)?;
    let island_span = ByteRange::new(section_xml, first.start(), last.end())?;
    require_whitespace_between(section_xml, &document, &root_elements)?;
    let island_bytes = section_xml
        .get(island_span.start..island_span.end)
        .ok_or(ObjectCompositionHwpxError::UnsupportedProfile)?
        .to_vec();
    Ok(ParsedIsland {
        document,
        objects,
        island_span,
        island_bytes,
    })
}

fn validate_native_object(
    document: &PreservingXmlDocument,
    element: &XmlElementToken,
    object: &CompositionObject,
    graph: &ObjectCompositionGraph,
) -> Result<(), ObjectCompositionHwpxError> {
    if parse_u32(attribute(element, "id")?)? != object.native_object_id
        || parse_u32(attribute(element, "instid")?)? != object.native_instance_id
        || parse_u32(attribute(element, "zOrder")?)? != object.z_order
        || parse_u32(attribute(element, "groupLevel")?)? != object.group_level
        || !kind_matches(document, element, object.kind)?
        || !object.visible
        || !object.printable
    {
        return Err(ObjectCompositionHwpxError::UnsupportedProfile);
    }
    let offset = unique_direct_child(document, element, "offset")?;
    let size = unique_direct_child(document, element, "curSz")?;
    let bounds = CompositionBounds {
        x_hwpunit: parse_i64(attribute(offset, "x")?)?,
        y_hwpunit: parse_i64(attribute(offset, "y")?)?,
        width_hwpunit: parse_u64(attribute(size, "width")?)?,
        height_hwpunit: parse_u64(attribute(size, "height")?)?,
    };
    if bounds != object.bounds {
        return Err(ObjectCompositionHwpxError::UnsupportedProfile);
    }
    if let Some(topology) = &object.connector {
        validate_connector(document, element, topology, graph)?;
    }
    Ok(())
}

fn kind_matches(
    document: &PreservingXmlDocument,
    element: &XmlElementToken,
    kind: CompositionObjectKind,
) -> Result<bool, ObjectCompositionHwpxError> {
    let tag = object_tag(element).ok_or(ObjectCompositionHwpxError::UnsupportedProfile)?;
    Ok(match kind {
        CompositionObjectKind::Group => tag == "container",
        CompositionObjectKind::BasicShape => {
            matches!(
                tag,
                "line" | "rect" | "ellipse" | "arc" | "polygon" | "curve"
            ) && direct_children_named(document, element, "drawText")?.is_empty()
        }
        CompositionObjectKind::Picture => tag == "pic",
        CompositionObjectKind::Chart => tag == "chart",
        CompositionObjectKind::TextBox => {
            tag == "rect" && direct_children_named(document, element, "drawText")?.len() == 1
        }
        CompositionObjectKind::Embedded => tag == "ole",
        CompositionObjectKind::Connector => tag == "connectLine",
    })
}

fn validate_connector(
    document: &PreservingXmlDocument,
    element: &XmlElementToken,
    topology: &ConnectorTopology,
    graph: &ObjectCompositionGraph,
) -> Result<(), ObjectCompositionHwpxError> {
    if attribute(element, "type")? != connector_kind(topology.kind) {
        return Err(ObjectCompositionHwpxError::UnsupportedProfile);
    }
    let start = unique_direct_child(document, element, "startPt")?;
    let end = unique_direct_child(document, element, "endPt")?;
    validate_endpoint(start, &topology.start, graph)?;
    validate_endpoint(end, &topology.end, graph)?;
    let controls = unique_direct_child(document, element, "controlPoints")?;
    let points = direct_children_named(document, controls, "point")?;
    if points.len() != topology.control_points.len() {
        return Err(ObjectCompositionHwpxError::UnsupportedProfile);
    }
    for (native, expected) in points.into_iter().zip(&topology.control_points) {
        if parse_i64(attribute(native, "x")?)? != expected.x_hwpunit
            || parse_i64(attribute(native, "y")?)? != expected.y_hwpunit
            || parse_u32(attribute(native, "type")?)? != expected.point_type
        {
            return Err(ObjectCompositionHwpxError::UnsupportedProfile);
        }
    }
    Ok(())
}

fn validate_endpoint(
    native: &XmlElementToken,
    endpoint: &ConnectorEndpoint,
    graph: &ObjectCompositionGraph,
) -> Result<(), ObjectCompositionHwpxError> {
    let (subject_id, subject_index) = match &endpoint.subject {
        Some(subject) => (
            graph
                .object(&subject.object_id)
                .ok_or(ObjectCompositionHwpxError::UnsupportedProfile)?
                .native_object_id,
            subject.connection_index,
        ),
        None => (0, 0),
    };
    if parse_i64(attribute(native, "x")?)? != endpoint.x_hwpunit
        || parse_i64(attribute(native, "y")?)? != endpoint.y_hwpunit
        || parse_u32(attribute(native, "subjectIDRef")?)? != subject_id
        || parse_u32(attribute(native, "subjectIdx")?)? != subject_index
    {
        return Err(ObjectCompositionHwpxError::UnsupportedProfile);
    }
    Ok(())
}

fn render_target(
    source_xml: &[u8],
    source: &ObjectCompositionGraph,
    target: &ObjectCompositionGraph,
    limits: ObjectCompositionHwpxLimits,
) -> Result<Vec<u8>, ObjectCompositionHwpxError> {
    let island = inspect_island(source_xml, source, limits)?;
    let roots = ordered_children(target, None);
    let mut rendered = String::new();
    for root in roots {
        rendered.push_str(&render_object(&island, source, target, root, limits)?);
        if rendered.len() > limits.0.output_bytes {
            return Err(ObjectCompositionHwpxError::OutputLimit);
        }
    }
    replace_span(source_xml, island.island_span, rendered.as_bytes(), limits)
}

fn render_object(
    island: &ParsedIsland,
    source: &ObjectCompositionGraph,
    target: &ObjectCompositionGraph,
    object: &CompositionObject,
    limits: ObjectCompositionHwpxLimits,
) -> Result<String, ObjectCompositionHwpxError> {
    let mut children = String::new();
    for child in ordered_children(target, Some(&object.object_id)) {
        children.push_str(&render_object(island, source, target, child, limits)?);
        if children.len() > limits.0.output_bytes {
            return Err(ObjectCompositionHwpxError::OutputLimit);
        }
    }
    if let Some(native) = island.objects.get(&object.object_id) {
        let source_object = source
            .object(&object.object_id)
            .ok_or(ObjectCompositionHwpxError::UnsupportedProfile)?;
        if source_object.content != object.content
            || source_object.native_object_id != object.native_object_id
            || source_object.native_instance_id != object.native_instance_id
            || source_object.kind != object.kind
            || source_object.visible != object.visible
            || source_object.printable != object.printable
        {
            return Err(ObjectCompositionHwpxError::PreservationDrift);
        }
        let fragment = island.document.source_text(native.outer_span)?;
        return patch_existing_fragment(fragment, object, target, &children, limits);
    }
    match object.kind {
        CompositionObjectKind::Group => new_group_fragment(object, &children, limits),
        CompositionObjectKind::Connector => new_connector_fragment(object, target, limits),
        _ => Err(ObjectCompositionHwpxError::UnsupportedProfile),
    }
}

fn patch_existing_fragment(
    fragment: &str,
    target: &CompositionObject,
    target_graph: &ObjectCompositionGraph,
    rendered_children: &str,
    limits: ObjectCompositionHwpxLimits,
) -> Result<String, ObjectCompositionHwpxError> {
    let prefix = format!(
        "<x:root xmlns:x=\"{WRAPPER_NS}\" xmlns:hp=\"{PARAGRAPH_NS}\" xmlns:hc=\"{CORE_NS}\">"
    );
    let suffix = "</x:root>";
    let wrapped = format!("{prefix}{fragment}{suffix}");
    let document = PreservingXmlDocument::parse(wrapped.as_bytes())?;
    let root = direct_object_children(&document, document.root_element())?;
    if root.len() != 1 {
        return Err(ObjectCompositionHwpxError::UnsupportedProfile);
    }
    let root_index = root[0];
    let native = element(&document, root_index)?;
    let mut edits = vec![
        value_edit(native, "zOrder", target.z_order.to_string())?,
        value_edit(native, "groupLevel", target.group_level.to_string())?,
    ];
    let offset = unique_direct_child(&document, native, "offset")?;
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
    let size = unique_direct_child(&document, native, "curSz")?;
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
    if target.kind == CompositionObjectKind::Group {
        let children = direct_object_children(&document, root_index)?;
        if children.is_empty() {
            return Err(ObjectCompositionHwpxError::UnsupportedProfile);
        }
        require_whitespace_between(wrapped.as_bytes(), &document, &children)?;
        let first = element(&document, children[0])?
            .outer_span()
            .ok_or(ObjectCompositionHwpxError::UnsupportedProfile)?;
        let last = element(
            &document,
            *children
                .last()
                .ok_or(ObjectCompositionHwpxError::UnsupportedProfile)?,
        )?
        .outer_span()
        .ok_or(ObjectCompositionHwpxError::UnsupportedProfile)?;
        edits.push(ByteEdit {
            span: ByteRange::new(wrapped.as_bytes(), first.start(), last.end())?,
            replacement: rendered_children.to_owned(),
        });
    } else if target.kind == CompositionObjectKind::Connector {
        let topology = target
            .connector
            .as_ref()
            .ok_or(ObjectCompositionHwpxError::UnsupportedProfile)?;
        edits.push(value_edit(
            native,
            "type",
            connector_kind(topology.kind).to_owned(),
        )?);
        let start = unique_direct_child(&document, native, "startPt")?
            .outer_span()
            .ok_or(ObjectCompositionHwpxError::UnsupportedProfile)?;
        let controls = unique_direct_child(&document, native, "controlPoints")?
            .outer_span()
            .ok_or(ObjectCompositionHwpxError::UnsupportedProfile)?;
        edits.push(ByteEdit {
            span: ByteRange::new(wrapped.as_bytes(), start.start(), controls.end())?,
            replacement: connector_topology_fragment(topology, target_graph)?,
        });
    } else if !rendered_children.is_empty() {
        return Err(ObjectCompositionHwpxError::UnsupportedProfile);
    }
    let output = apply_edits(wrapped.as_bytes(), edits, limits)?;
    let output =
        std::str::from_utf8(&output).map_err(|_| ObjectCompositionHwpxError::Serialization)?;
    if !output.starts_with(&prefix) || !output.ends_with(suffix) {
        return Err(ObjectCompositionHwpxError::Serialization);
    }
    Ok(output[prefix.len()..output.len() - suffix.len()].to_owned())
}

fn new_group_fragment(
    object: &CompositionObject,
    children: &str,
    limits: ObjectCompositionHwpxLimits,
) -> Result<String, ObjectCompositionHwpxError> {
    require_empty_generated_content(object)?;
    if children.is_empty() {
        return Err(ObjectCompositionHwpxError::UnsupportedProfile);
    }
    let mut output = format!(
        "<hp:container id=\"{}\" zOrder=\"{}\" numberingType=\"CONTAINER\" textWrap=\"TOP_AND_BOTTOM\" textFlow=\"BOTH_SIDES\" lock=\"0\" dropcapstyle=\"None\" href=\"\" groupLevel=\"{}\" instid=\"{}\">{}{}{}{}{}{}{}{}{}",
        object.native_object_id,
        object.z_order,
        object.group_level,
        object.native_instance_id,
        common_component(&object.bounds),
        "<hp:flip horizontal=\"0\" vertical=\"0\"/>",
        rotation_fragment(&object.bounds),
        rendering_fragment(),
        size_fragment(&object.bounds),
        position_fragment(),
        "<hp:outMargin left=\"0\" right=\"0\" top=\"0\" bottom=\"0\"/>",
        children,
        "</hp:container>"
    );
    if output.len() > limits.0.output_bytes {
        return Err(ObjectCompositionHwpxError::OutputLimit);
    }
    output.shrink_to_fit();
    Ok(output)
}

fn new_connector_fragment(
    object: &CompositionObject,
    graph: &ObjectCompositionGraph,
    limits: ObjectCompositionHwpxLimits,
) -> Result<String, ObjectCompositionHwpxError> {
    require_empty_generated_content(object)?;
    let topology = object
        .connector
        .as_ref()
        .ok_or(ObjectCompositionHwpxError::UnsupportedProfile)?;
    let output = format!(
        "<hp:connectLine id=\"{}\" zOrder=\"{}\" numberingType=\"DRAWING\" textWrap=\"TOP_AND_BOTTOM\" textFlow=\"BOTH_SIDES\" lock=\"0\" dropcapstyle=\"None\" href=\"\" groupLevel=\"{}\" instid=\"{}\" type=\"{}\">{}{}{}{}<hp:lineShape color=\"#000000\" width=\"1\" style=\"SOLID\" endCap=\"FLAT\" headStyle=\"NORMAL\" tailStyle=\"NORMAL\" headfill=\"1\" tailfill=\"1\" headSz=\"SMALL_SMALL\" tailSz=\"SMALL_SMALL\" outlineStyle=\"NORMAL\" alpha=\"0\"/>{}{}{}{}{}</hp:connectLine>",
        object.native_object_id,
        object.z_order,
        object.group_level,
        object.native_instance_id,
        connector_kind(topology.kind),
        common_component(&object.bounds),
        "<hp:flip horizontal=\"0\" vertical=\"0\"/>",
        rotation_fragment(&object.bounds),
        rendering_fragment(),
        connector_topology_fragment(topology, graph)?,
        size_fragment(&object.bounds),
        position_fragment(),
        "<hp:outMargin left=\"0\" right=\"0\" top=\"0\" bottom=\"0\"/>",
        ""
    );
    if output.len() > limits.0.output_bytes {
        return Err(ObjectCompositionHwpxError::OutputLimit);
    }
    Ok(output)
}

fn common_component(bounds: &CompositionBounds) -> String {
    format!(
        "<hp:offset x=\"{}\" y=\"{}\"/><hp:orgSz width=\"{}\" height=\"{}\"/><hp:curSz width=\"{}\" height=\"{}\"/>",
        bounds.x_hwpunit,
        bounds.y_hwpunit,
        bounds.width_hwpunit,
        bounds.height_hwpunit,
        bounds.width_hwpunit,
        bounds.height_hwpunit
    )
}

fn rotation_fragment(bounds: &CompositionBounds) -> String {
    format!(
        "<hp:rotationInfo angle=\"0\" centerX=\"{}\" centerY=\"{}\" rotateimage=\"1\"/>",
        bounds.width_hwpunit / 2,
        bounds.height_hwpunit / 2
    )
}

fn rendering_fragment() -> &'static str {
    "<hp:renderingInfo><hc:transMatrix e1=\"1\" e2=\"0\" e3=\"0\" e4=\"1\" e5=\"0\" e6=\"0\"/><hc:scaMatrix e1=\"1\" e2=\"0\" e3=\"0\" e4=\"1\" e5=\"0\" e6=\"0\"/><hc:rotMatrix e1=\"1\" e2=\"0\" e3=\"0\" e4=\"1\" e5=\"0\" e6=\"0\"/></hp:renderingInfo>"
}

fn size_fragment(bounds: &CompositionBounds) -> String {
    format!(
        "<hp:sz width=\"{}\" widthRelTo=\"ABSOLUTE\" height=\"{}\" heightRelTo=\"ABSOLUTE\" protect=\"0\"/>",
        bounds.width_hwpunit, bounds.height_hwpunit
    )
}

fn position_fragment() -> &'static str {
    "<hp:pos treatAsChar=\"0\" affectLSpacing=\"0\" flowWithText=\"1\" allowOverlap=\"0\" holdAnchorAndSO=\"1\" vertRelTo=\"PARA\" horzRelTo=\"PARA\" vertAlign=\"TOP\" horzAlign=\"LEFT\" vertOffset=\"0\" horzOffset=\"0\"/>"
}

fn connector_topology_fragment(
    topology: &ConnectorTopology,
    graph: &ObjectCompositionGraph,
) -> Result<String, ObjectCompositionHwpxError> {
    let mut output = String::new();
    output.push_str(&endpoint_fragment("startPt", &topology.start, graph)?);
    output.push_str(&endpoint_fragment("endPt", &topology.end, graph)?);
    output.push_str("<hp:controlPoints>");
    for point in &topology.control_points {
        let _ = write!(
            output,
            "<hp:point x=\"{}\" y=\"{}\" type=\"{}\"/>",
            point.x_hwpunit, point.y_hwpunit, point.point_type
        );
    }
    output.push_str("</hp:controlPoints>");
    Ok(output)
}

fn endpoint_fragment(
    name: &str,
    endpoint: &ConnectorEndpoint,
    graph: &ObjectCompositionGraph,
) -> Result<String, ObjectCompositionHwpxError> {
    let (subject, index) = match &endpoint.subject {
        Some(subject) => (
            graph
                .object(&subject.object_id)
                .ok_or(ObjectCompositionHwpxError::UnsupportedProfile)?
                .native_object_id,
            subject.connection_index,
        ),
        None => (0, 0),
    };
    Ok(format!(
        "<hp:{name} x=\"{}\" y=\"{}\" subjectIDRef=\"{subject}\" subjectIdx=\"{index}\"/>",
        endpoint.x_hwpunit, endpoint.y_hwpunit
    ))
}

fn require_empty_generated_content(
    object: &CompositionObject,
) -> Result<(), ObjectCompositionHwpxError> {
    if !object.visible
        || !object.printable
        || object.content.state_sha256 != EMPTY_SHA256
        || object.content.byte_length != 0
        || !object.content.resource_refs.is_empty()
    {
        return Err(ObjectCompositionHwpxError::UnsupportedProfile);
    }
    Ok(())
}

fn ordered_children<'a>(
    graph: &'a ObjectCompositionGraph,
    parent: Option<&LogicalId>,
) -> Vec<&'a CompositionObject> {
    let mut children: Vec<_> = graph
        .objects()
        .iter()
        .filter(|object| object.parent_group_id.as_ref() == parent)
        .collect();
    children.sort_by_key(|object| object.z_order);
    children
}

fn object_tag(element: &XmlElementToken) -> Option<&str> {
    if element.name().namespace() != Some(PARAGRAPH_NS) {
        return None;
    }
    match element.name().local_name() {
        tag @ ("container" | "line" | "rect" | "ellipse" | "arc" | "polygon" | "curve"
        | "connectLine" | "pic" | "ole" | "chart") => Some(tag),
        _ => None,
    }
}

fn connector_kind(kind: ConnectorKind) -> &'static str {
    match kind {
        ConnectorKind::StraightNoArrow => "STRAIGHT_NOARROW",
        ConnectorKind::StraightOneWay => "STRAIGHT_ONEWAY",
        ConnectorKind::StraightBoth => "STRAIGHT_BOTH",
        ConnectorKind::StrokeNoArrow => "STROKE_NOARROW",
        ConnectorKind::StrokeOneWay => "STROKE_ONEWAY",
        ConnectorKind::StrokeBoth => "STROKE_BOTH",
        ConnectorKind::ArcNoArrow => "ARC_NOARROW",
        ConnectorKind::ArcOneWay => "ARC_ONEWAY",
        ConnectorKind::ArcBoth => "ARC_BOTH",
    }
}

fn direct_object_children(
    document: &PreservingXmlDocument,
    parent: usize,
) -> Result<Vec<usize>, ObjectCompositionHwpxError> {
    let mut values = Vec::new();
    let mut child = element(document, parent)?.first_child();
    while let Some(index) = child {
        let candidate = element(document, index)?;
        if object_tag(candidate).is_some() {
            values.push(index);
        }
        child = candidate.next_sibling();
    }
    Ok(values)
}

fn direct_children_named<'a>(
    document: &'a PreservingXmlDocument,
    parent: &XmlElementToken,
    name: &str,
) -> Result<Vec<&'a XmlElementToken>, ObjectCompositionHwpxError> {
    let mut values = Vec::new();
    let mut child = parent.first_child();
    while let Some(index) = child {
        let candidate = element(document, index)?;
        if has_name(candidate, name) {
            values.push(candidate);
        }
        child = candidate.next_sibling();
    }
    Ok(values)
}

fn unique_direct_child<'a>(
    document: &'a PreservingXmlDocument,
    parent: &XmlElementToken,
    name: &str,
) -> Result<&'a XmlElementToken, ObjectCompositionHwpxError> {
    let values = direct_children_named(document, parent, name)?;
    if values.len() != 1 {
        return Err(ObjectCompositionHwpxError::UnsupportedProfile);
    }
    Ok(values[0])
}

fn require_whitespace_between(
    source: &[u8],
    document: &PreservingXmlDocument,
    indexes: &[usize],
) -> Result<(), ObjectCompositionHwpxError> {
    for pair in indexes.windows(2) {
        let left = element(document, pair[0])?
            .outer_span()
            .ok_or(ObjectCompositionHwpxError::UnsupportedProfile)?;
        let right = element(document, pair[1])?
            .outer_span()
            .ok_or(ObjectCompositionHwpxError::UnsupportedProfile)?;
        let between = source
            .get(left.end()..right.start())
            .ok_or(ObjectCompositionHwpxError::UnsupportedProfile)?;
        if !std::str::from_utf8(between)
            .map_err(|_| ObjectCompositionHwpxError::Serialization)?
            .trim()
            .is_empty()
        {
            return Err(ObjectCompositionHwpxError::UnsupportedProfile);
        }
    }
    Ok(())
}

fn element(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<&XmlElementToken, ObjectCompositionHwpxError> {
    document
        .elements()
        .get(index)
        .ok_or(ObjectCompositionHwpxError::UnsupportedProfile)
}

fn has_name(element: &XmlElementToken, local: &str) -> bool {
    element.name().namespace() == Some(PARAGRAPH_NS) && element.name().local_name() == local
}

fn attribute<'a>(
    element: &'a XmlElementToken,
    local: &str,
) -> Result<&'a str, ObjectCompositionHwpxError> {
    let mut matches = element.attributes().iter().filter(|attribute| {
        !attribute.is_namespace_declaration()
            && attribute.name().namespace().is_none()
            && attribute.name().local_name() == local
    });
    let value = matches
        .next()
        .ok_or(ObjectCompositionHwpxError::UnsupportedProfile)?;
    if matches.next().is_some() {
        return Err(ObjectCompositionHwpxError::UnsupportedProfile);
    }
    Ok(value.semantic_value())
}

fn value_edit(
    element: &XmlElementToken,
    local: &str,
    replacement: String,
) -> Result<ByteEdit, ObjectCompositionHwpxError> {
    let attribute = element
        .attributes()
        .iter()
        .find(|attribute| {
            !attribute.is_namespace_declaration()
                && attribute.name().namespace().is_none()
                && attribute.name().local_name() == local
        })
        .ok_or(ObjectCompositionHwpxError::UnsupportedProfile)?;
    Ok(ByteEdit {
        span: attribute.value_span().into(),
        replacement,
    })
}

fn parse_u32(value: &str) -> Result<u32, ObjectCompositionHwpxError> {
    value
        .parse()
        .map_err(|_| ObjectCompositionHwpxError::UnsupportedProfile)
}

fn parse_u64(value: &str) -> Result<u64, ObjectCompositionHwpxError> {
    value
        .parse()
        .map_err(|_| ObjectCompositionHwpxError::UnsupportedProfile)
}

fn parse_i64(value: &str) -> Result<i64, ObjectCompositionHwpxError> {
    value
        .parse()
        .map_err(|_| ObjectCompositionHwpxError::UnsupportedProfile)
}

#[derive(Debug)]
struct ByteEdit {
    span: ByteRange,
    replacement: String,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct ByteRange {
    start: usize,
    end: usize,
}

impl ByteRange {
    fn new(source: &[u8], start: usize, end: usize) -> Result<Self, ObjectCompositionHwpxError> {
        let text =
            std::str::from_utf8(source).map_err(|_| ObjectCompositionHwpxError::Serialization)?;
        if start > end
            || end > source.len()
            || !text.is_char_boundary(start)
            || !text.is_char_boundary(end)
        {
            return Err(ObjectCompositionHwpxError::UnsupportedProfile);
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

fn apply_edits(
    source: &[u8],
    mut edits: Vec<ByteEdit>,
    limits: ObjectCompositionHwpxLimits,
) -> Result<Vec<u8>, ObjectCompositionHwpxError> {
    edits.sort_by_key(|edit| edit.span.start);
    if edits
        .windows(2)
        .any(|pair| pair[0].span.end > pair[1].span.start)
    {
        return Err(ObjectCompositionHwpxError::PreservationDrift);
    }
    let removed: usize = edits.iter().map(|edit| edit.span.len()).sum();
    let added: usize = edits.iter().map(|edit| edit.replacement.len()).sum();
    let capacity = source
        .len()
        .checked_sub(removed)
        .and_then(|value| value.checked_add(added))
        .ok_or(ObjectCompositionHwpxError::OutputLimit)?;
    if capacity > limits.0.output_bytes {
        return Err(ObjectCompositionHwpxError::OutputLimit);
    }
    let mut output = Vec::with_capacity(capacity);
    let mut cursor = 0;
    for edit in edits {
        output.extend_from_slice(
            source
                .get(cursor..edit.span.start)
                .ok_or(ObjectCompositionHwpxError::PreservationDrift)?,
        );
        output.extend_from_slice(edit.replacement.as_bytes());
        cursor = edit.span.end;
    }
    output.extend_from_slice(
        source
            .get(cursor..)
            .ok_or(ObjectCompositionHwpxError::PreservationDrift)?,
    );
    Ok(output)
}

fn replace_span(
    source: &[u8],
    span: ByteRange,
    replacement: &[u8],
    limits: ObjectCompositionHwpxLimits,
) -> Result<Vec<u8>, ObjectCompositionHwpxError> {
    apply_edits(
        source,
        vec![ByteEdit {
            span,
            replacement: std::str::from_utf8(replacement)
                .map_err(|_| ObjectCompositionHwpxError::Serialization)?
                .to_owned(),
        }],
        limits,
    )
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

fn plan_binding_sha256(
    plan: &ObjectCompositionHwpxPlan,
) -> Result<String, ObjectCompositionHwpxError> {
    #[derive(Serialize)]
    struct Binding<'a> {
        profile_id: &'static str,
        capability_id: &'static str,
        domain_plan_sha256: &'a str,
        source_section_sha256: &'a str,
        target_section_sha256: &'a str,
        source_graph_sha256: &'a str,
        target_graph_sha256: &'a str,
        source_document_flow_sha256: &'a str,
        target_document_flow_sha256: &'a str,
    }
    let bytes = serde_json::to_vec(&Binding {
        profile_id: plan.profile_id,
        capability_id: plan.capability_id,
        domain_plan_sha256: plan.domain_plan.plan_sha256(),
        source_section_sha256: &plan.source_section_sha256,
        target_section_sha256: &plan.target_section_sha256,
        source_graph_sha256: &plan.source_graph_sha256,
        target_graph_sha256: &plan.target_graph_sha256,
        source_document_flow_sha256: &plan.source_document_flow_sha256,
        target_document_flow_sha256: &plan.target_document_flow_sha256,
    })
    .map_err(|_| ObjectCompositionHwpxError::Serialization)?;
    Ok(sha256(&bytes))
}

fn sha256(bytes: &[u8]) -> String {
    let digest: [u8; 32] = Sha256::digest(bytes).into();
    let mut output = String::with_capacity(64);
    for byte in digest {
        let _ = write!(&mut output, "{byte:02x}");
    }
    output
}
