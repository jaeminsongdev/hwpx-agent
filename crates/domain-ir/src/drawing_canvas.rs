use std::collections::{BTreeMap, BTreeSet};
use std::fmt;

use serde::de::{self, DeserializeSeed, MapAccess, Visitor};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use thiserror::Error;
use unicode_normalization::UnicodeNormalization;

use crate::{
    AppearanceTargetKind, LogicalId, ObjectAppearance, ObjectAppearanceLimitConfig,
    ObjectAppearanceLimits, PictureEffects,
};

pub const DRAWING_CANVAS_SCHEMA_VERSION: &str = "hwpx-agent.drawing-canvas/v1";

const COUNT_LIMIT_CEILING: usize = 1_000_000;
const BYTE_LIMIT_CEILING: usize = 256 * 1024 * 1024;
const DEPTH_LIMIT_CEILING: usize = 256;
const COORDINATE_LIMIT_CEILING: i64 = 1_000_000_000_000;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct DrawingCanvasLimitConfig {
    pub input_bytes: usize,
    pub output_bytes: usize,
    pub nodes: usize,
    pub resources: usize,
    pub resources_per_node: usize,
    pub depth: usize,
    pub identifier_bytes: usize,
    pub media_type_bytes: usize,
    pub opaque_bytes: u64,
    pub coordinate_magnitude_hwpunit: i64,
    pub image_dimension: u32,
}

impl Default for DrawingCanvasLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 4 * 1024 * 1024,
            output_bytes: 16 * 1024 * 1024,
            nodes: 65_536,
            resources: 65_536,
            resources_per_node: 4_096,
            depth: 64,
            identifier_bytes: 512,
            media_type_bytes: 255,
            opaque_bytes: 256 * 1024 * 1024,
            coordinate_magnitude_hwpunit: 1_000_000_000,
            image_dimension: 1_000_000,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct DrawingCanvasLimits(DrawingCanvasLimitConfig);

impl DrawingCanvasLimits {
    /// Creates finite limits for untrusted canvas states and requests.
    ///
    /// # Errors
    ///
    /// Rejects zero, inconsistent or process-hostile limits.
    pub fn new(config: DrawingCanvasLimitConfig) -> Result<Self, DrawingCanvasError> {
        if config.input_bytes == 0
            || config.output_bytes == 0
            || config.input_bytes > config.output_bytes
            || config.output_bytes > BYTE_LIMIT_CEILING
            || config.nodes == 0
            || config.nodes > COUNT_LIMIT_CEILING
            || config.resources == 0
            || config.resources > COUNT_LIMIT_CEILING
            || config.resources_per_node == 0
            || config.resources_per_node > config.resources
            || config.depth == 0
            || config.depth > DEPTH_LIMIT_CEILING
            || config.identifier_bytes == 0
            || config.identifier_bytes > 4 * 1024 * 1024
            || config.media_type_bytes == 0
            || config.media_type_bytes > 4 * 1024 * 1024
            || config.opaque_bytes == 0
            || config.opaque_bytes > u64::try_from(BYTE_LIMIT_CEILING).unwrap_or(u64::MAX)
            || config.coordinate_magnitude_hwpunit <= 0
            || config.coordinate_magnitude_hwpunit > COORDINATE_LIMIT_CEILING
            || config.image_dimension == 0
        {
            return Err(DrawingCanvasError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> DrawingCanvasLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CanvasNodeKind {
    Container,
    Line,
    Rectangle,
    Ellipse,
    Arc,
    Polygon,
    Curve,
    Connector,
    Picture,
    OpaqueOle,
}

#[derive(Clone, Copy, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CanvasBounds {
    pub x_hwpunit: i64,
    pub y_hwpunit: i64,
    pub width_hwpunit: u64,
    pub height_hwpunit: u64,
}

impl fmt::Debug for CanvasBounds {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CanvasBounds")
            .field("geometry", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CanvasBindings {
    pub geometry_sha256: String,
    pub payload_sha256: String,
    pub appearance_sha256: String,
    pub composition_sha256: String,
    pub opaque_sha256: String,
    pub opaque_byte_length: u64,
}

impl fmt::Debug for CanvasBindings {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CanvasBindings")
            .field("opaque_byte_length", &self.opaque_byte_length)
            .field("digests", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ImageClip {
    pub left_px: u32,
    pub right_px: u32,
    pub top_px: u32,
    pub bottom_px: u32,
}

impl fmt::Debug for ImageClip {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ImageClip")
            .field("coordinates", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CanvasPictureState {
    pub image_resource_id: LogicalId,
    pub original_width_px: u32,
    pub original_height_px: u32,
    pub clip: Option<ImageClip>,
    pub effects: Option<PictureEffects>,
}

impl fmt::Debug for CanvasPictureState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CanvasPictureState")
            .field("has_clip", &self.clip.is_some())
            .field("has_effects", &self.effects.is_some())
            .field("resource", &"<redacted>")
            .field("dimensions", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CanvasNode {
    pub node_id: LogicalId,
    pub native_object_id: u32,
    pub native_instance_id: u32,
    pub kind: CanvasNodeKind,
    pub parent_id: Option<LogicalId>,
    pub ordinal: u32,
    pub group_level: u32,
    pub bounds: CanvasBounds,
    pub visible: bool,
    pub printable: bool,
    pub protected: bool,
    pub bindings: CanvasBindings,
    pub resource_refs: Vec<LogicalId>,
    pub picture: Option<CanvasPictureState>,
}

impl fmt::Debug for CanvasNode {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CanvasNode")
            .field("kind", &self.kind)
            .field("ordinal", &self.ordinal)
            .field("group_level", &self.group_level)
            .field("visible", &self.visible)
            .field("printable", &self.printable)
            .field("protected", &self.protected)
            .field("resource_count", &self.resource_refs.len())
            .field("picture", &self.picture)
            .field("identity", &"<redacted>")
            .field("bounds", &"<redacted>")
            .field("bindings", &self.bindings)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CanvasResourceKind {
    EmbeddedImage,
    LinkedImage,
    ImageFill,
    OpaqueOle,
    Preview,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ActiveContentPolicy {
    Blocked,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CanvasResource {
    pub resource_id: LogicalId,
    pub relationship_id: String,
    pub kind: CanvasResourceKind,
    pub media_type: String,
    pub content_sha256: String,
    pub byte_length: u64,
    pub external_target_sha256: Option<String>,
    pub active_content_policy: Option<ActiveContentPolicy>,
}

impl fmt::Debug for CanvasResource {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CanvasResource")
            .field("kind", &self.kind)
            .field("byte_length", &self.byte_length)
            .field("is_external", &self.external_target_sha256.is_some())
            .field("active_content_policy", &self.active_content_policy)
            .field("identity", &"<redacted>")
            .field("media_type", &"<redacted>")
            .field("digests", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct DrawingCanvasStateDraft {
    pub schema_version: String,
    pub document_id: LogicalId,
    pub nodes: Vec<CanvasNode>,
    pub resources: Vec<CanvasResource>,
    pub opaque_document_state_sha256: String,
}

impl fmt::Debug for DrawingCanvasStateDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("DrawingCanvasStateDraft")
            .field("schema_version", &self.schema_version)
            .field("nodes", &self.nodes.len())
            .field("resources", &self.resources.len())
            .field("identity", &"<redacted>")
            .field("state", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct DrawingCanvasState {
    schema_version: String,
    document_id: LogicalId,
    nodes: Vec<CanvasNode>,
    resources: Vec<CanvasResource>,
    opaque_document_state_sha256: String,
}

impl fmt::Debug for DrawingCanvasState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("DrawingCanvasState")
            .field("schema_version", &self.schema_version)
            .field("nodes", &self.nodes.len())
            .field("resources", &self.resources.len())
            .field("identity", &"<redacted>")
            .field("state", &"<redacted>")
            .finish_non_exhaustive()
    }
}

impl DrawingCanvasState {
    /// Builds and validates one complete ordered canvas/resource projection.
    ///
    /// # Errors
    ///
    /// Rejects invalid identity, topology, clip, effects, resource closure or limits.
    pub fn from_draft(
        mut draft: DrawingCanvasStateDraft,
        limits: DrawingCanvasLimits,
    ) -> Result<Self, DrawingCanvasError> {
        draft
            .nodes
            .sort_by(|left, right| left.node_id.cmp(&right.node_id));
        draft
            .resources
            .sort_by(|left, right| left.resource_id.cmp(&right.resource_id));
        let state = Self {
            schema_version: draft.schema_version,
            document_id: draft.document_id,
            nodes: draft.nodes,
            resources: draft.resources,
            opaque_document_state_sha256: draft.opaque_document_state_sha256,
        };
        state.validate(limits)?;
        Ok(state)
    }

    /// Parses strict, duplicate-key-free bounded JSON.
    ///
    /// # Errors
    ///
    /// Rejects malformed, duplicate, unknown, oversized or invalid state JSON.
    pub fn from_json(
        bytes: &[u8],
        limits: DrawingCanvasLimits,
    ) -> Result<Self, DrawingCanvasError> {
        if bytes.len() > limits.0.input_bytes {
            return Err(DrawingCanvasError::InputTooLarge);
        }
        reject_duplicate_json_keys(bytes)?;
        let draft: DrawingCanvasStateDraft =
            serde_json::from_slice(bytes).map_err(|_| DrawingCanvasError::InvalidJson)?;
        Self::from_draft(draft, limits)
    }

    #[must_use]
    pub fn document_id(&self) -> &LogicalId {
        &self.document_id
    }

    #[must_use]
    pub fn nodes(&self) -> &[CanvasNode] {
        &self.nodes
    }

    #[must_use]
    pub fn resources(&self) -> &[CanvasResource] {
        &self.resources
    }

    #[must_use]
    pub fn node(&self, id: &LogicalId) -> Option<&CanvasNode> {
        self.nodes
            .binary_search_by(|node| node.node_id.cmp(id))
            .ok()
            .map(|index| &self.nodes[index])
    }

    #[must_use]
    pub fn resource(&self, id: &LogicalId) -> Option<&CanvasResource> {
        self.resources
            .binary_search_by(|resource| resource.resource_id.cmp(id))
            .ok()
            .map(|index| &self.resources[index])
    }

    /// Returns deterministic bounded JSON for state and drift binding.
    ///
    /// # Errors
    ///
    /// Rejects serialization beyond the configured bound.
    pub fn to_canonical_json(
        &self,
        limits: DrawingCanvasLimits,
    ) -> Result<Vec<u8>, DrawingCanvasError> {
        bounded_json(self, limits.0.output_bytes)
    }

    /// Returns the SHA-256 of deterministic state JSON.
    ///
    /// # Errors
    ///
    /// Rejects serialization beyond the configured bound.
    pub fn state_sha256(&self, limits: DrawingCanvasLimits) -> Result<String, DrawingCanvasError> {
        sha256_json(self, limits.0.output_bytes)
    }

    fn validate(&self, limits: DrawingCanvasLimits) -> Result<(), DrawingCanvasError> {
        if self.schema_version != DRAWING_CANVAS_SCHEMA_VERSION {
            return Err(DrawingCanvasError::SchemaMismatch);
        }
        validate_identifier(self.document_id.as_str(), limits)?;
        validate_sha256(&self.opaque_document_state_sha256)?;
        if self.nodes.len() > limits.0.nodes || self.resources.len() > limits.0.resources {
            return Err(DrawingCanvasError::CountLimitExceeded);
        }

        let mut node_ids = BTreeSet::new();
        let mut native_objects = BTreeSet::new();
        let mut native_instances = BTreeSet::new();
        let mut node_map = BTreeMap::new();
        for node in &self.nodes {
            validate_identifier(node.node_id.as_str(), limits)?;
            if !node_ids.insert(node.node_id.clone())
                || node.native_object_id == 0
                || node.native_instance_id == 0
                || !native_objects.insert(node.native_object_id)
                || !native_instances.insert(node.native_instance_id)
            {
                return Err(DrawingCanvasError::DuplicateIdentity);
            }
            validate_bounds(node.bounds, limits)?;
            validate_bindings(&node.bindings, limits)?;
            if node.resource_refs.len() > limits.0.resources_per_node {
                return Err(DrawingCanvasError::CountLimitExceeded);
            }
            if !strictly_sorted_unique_ids(&node.resource_refs) {
                return Err(DrawingCanvasError::InvalidResourceClosure);
            }
            node_map.insert(node.node_id.clone(), node);
        }

        let mut resource_ids = BTreeSet::new();
        let mut relationship_ids = BTreeSet::new();
        let mut resource_map = BTreeMap::new();
        for resource in &self.resources {
            validate_resource(resource, limits)?;
            if !resource_ids.insert(resource.resource_id.clone())
                || !relationship_ids.insert(resource.relationship_id.clone())
            {
                return Err(DrawingCanvasError::DuplicateIdentity);
            }
            resource_map.insert(resource.resource_id.clone(), resource);
        }

        let mut referenced_resources = BTreeSet::new();
        let mut sibling_orders: BTreeMap<Option<LogicalId>, BTreeSet<u32>> = BTreeMap::new();
        for node in &self.nodes {
            let depth = node_depth(node, &node_map, limits)?;
            if depth != usize::try_from(node.group_level).unwrap_or(usize::MAX) {
                return Err(DrawingCanvasError::InvalidTopology);
            }
            if let Some(parent_id) = &node.parent_id {
                let parent = node_map
                    .get(parent_id)
                    .ok_or(DrawingCanvasError::InvalidTopology)?;
                if parent.kind != CanvasNodeKind::Container {
                    return Err(DrawingCanvasError::InvalidTopology);
                }
            } else if node.kind != CanvasNodeKind::Container {
                return Err(DrawingCanvasError::InvalidTopology);
            }
            insert_sibling_ordinal(&mut sibling_orders, node)?;
            for resource_id in &node.resource_refs {
                if !resource_map.contains_key(resource_id) {
                    return Err(DrawingCanvasError::InvalidResourceClosure);
                }
                referenced_resources.insert(resource_id.clone());
            }
            validate_picture_node(node, &resource_map, limits)?;
            validate_ole_node(node, &resource_map)?;
        }
        for orders in sibling_orders.values() {
            if orders.len()
                != orders.iter().next_back().map_or(0, |last| {
                    usize::try_from(*last)
                        .unwrap_or(usize::MAX)
                        .saturating_add(1)
                })
            {
                return Err(DrawingCanvasError::InvalidTopology);
            }
        }
        for node in &self.nodes {
            if node.kind == CanvasNodeKind::Container
                && !self
                    .nodes
                    .iter()
                    .any(|candidate| candidate.parent_id.as_ref() == Some(&node.node_id))
            {
                return Err(DrawingCanvasError::InvalidTopology);
            }
        }
        if referenced_resources != resource_ids {
            return Err(DrawingCanvasError::InvalidResourceClosure);
        }
        Ok(())
    }
}

fn insert_sibling_ordinal(
    sibling_orders: &mut BTreeMap<Option<LogicalId>, BTreeSet<u32>>,
    node: &CanvasNode,
) -> Result<(), DrawingCanvasError> {
    if !sibling_orders
        .entry(node.parent_id.clone())
        .or_default()
        .insert(node.ordinal)
    {
        return Err(DrawingCanvasError::InvalidTopology);
    }
    Ok(())
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CanvasIdentityReservation {
    pub node_ids: Vec<LogicalId>,
    pub native_object_ids: Vec<u32>,
    pub native_instance_ids: Vec<u32>,
    pub resource_ids: Vec<LogicalId>,
    pub allocator_proof_sha256: String,
}

impl fmt::Debug for CanvasIdentityReservation {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CanvasIdentityReservation")
            .field("nodes", &self.node_ids.len())
            .field("resources", &self.resource_ids.len())
            .field("identity", &"<redacted>")
            .field("proof", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum DrawingCanvasOperation {
    InsertCanvas {
        root_canvas_id: LogicalId,
        reservation: CanvasIdentityReservation,
    },
    SetPictureClip {
        picture_id: LogicalId,
    },
    SetPictureEffects {
        picture_id: LogicalId,
    },
}

impl DrawingCanvasOperation {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        match self {
            Self::InsertCanvas { .. } => "obj.drawing_object_insert",
            Self::SetPictureClip { .. } => "obj.crop",
            Self::SetPictureEffects { .. } => "obj.picture_effects",
        }
    }
}

impl fmt::Debug for DrawingCanvasOperation {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::InsertCanvas { reservation, .. } => formatter
                .debug_struct("InsertCanvas")
                .field("reservation", reservation)
                .field("target", &"<redacted>")
                .finish(),
            Self::SetPictureClip { .. } => formatter
                .debug_struct("SetPictureClip")
                .field("target", &"<redacted>")
                .finish(),
            Self::SetPictureEffects { .. } => formatter
                .debug_struct("SetPictureEffects")
                .field("target", &"<redacted>")
                .finish(),
        }
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct DrawingCanvasRequestDraft {
    pub schema_version: String,
    pub request_id: String,
    pub source: DrawingCanvasStateDraft,
    pub target: DrawingCanvasStateDraft,
    pub operation: DrawingCanvasOperation,
    pub source_state_sha256: String,
    pub before_document_flow_sha256: String,
    pub after_document_flow_sha256: String,
}

impl fmt::Debug for DrawingCanvasRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("DrawingCanvasRequestDraft")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.operation.capability_id())
            .field("request_id", &"<redacted>")
            .field("state", &"<redacted>")
            .field("flows", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct DrawingCanvasRequest {
    schema_version: String,
    request_id: String,
    source: DrawingCanvasState,
    target: DrawingCanvasState,
    operation: DrawingCanvasOperation,
    source_state_sha256: String,
    before_document_flow_sha256: String,
    after_document_flow_sha256: String,
}

impl fmt::Debug for DrawingCanvasRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("DrawingCanvasRequest")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.operation.capability_id())
            .field("request_id", &"<redacted>")
            .field("state", &"<redacted>")
            .field("flows", &"<redacted>")
            .finish_non_exhaustive()
    }
}

impl DrawingCanvasRequest {
    /// Builds an exact request and proves that its target is the named single transition.
    ///
    /// # Errors
    ///
    /// Rejects state, flow, digest, no-op or preservation violations.
    pub fn from_draft(
        draft: DrawingCanvasRequestDraft,
        limits: DrawingCanvasLimits,
    ) -> Result<Self, DrawingCanvasError> {
        if draft.schema_version != DRAWING_CANVAS_SCHEMA_VERSION {
            return Err(DrawingCanvasError::SchemaMismatch);
        }
        validate_text(&draft.request_id, limits)?;
        for digest in [
            &draft.source_state_sha256,
            &draft.before_document_flow_sha256,
            &draft.after_document_flow_sha256,
        ] {
            validate_sha256(digest)?;
        }
        let source = DrawingCanvasState::from_draft(draft.source, limits)?;
        let target = DrawingCanvasState::from_draft(draft.target, limits)?;
        if source.document_id != target.document_id
            || source.state_sha256(limits)? != draft.source_state_sha256
        {
            return Err(DrawingCanvasError::SourceStateDrift);
        }
        validate_transition(
            &source,
            &target,
            &draft.operation,
            &draft.before_document_flow_sha256,
            &draft.after_document_flow_sha256,
            limits,
        )?;
        Ok(Self {
            schema_version: draft.schema_version,
            request_id: draft.request_id,
            source,
            target,
            operation: draft.operation,
            source_state_sha256: draft.source_state_sha256,
            before_document_flow_sha256: draft.before_document_flow_sha256,
            after_document_flow_sha256: draft.after_document_flow_sha256,
        })
    }

    /// Parses strict, duplicate-key-free bounded JSON.
    ///
    /// # Errors
    ///
    /// Rejects malformed, duplicate, unknown, oversized or invalid request JSON.
    pub fn from_json(
        bytes: &[u8],
        limits: DrawingCanvasLimits,
    ) -> Result<Self, DrawingCanvasError> {
        if bytes.len() > limits.0.input_bytes {
            return Err(DrawingCanvasError::InputTooLarge);
        }
        reject_duplicate_json_keys(bytes)?;
        let draft: DrawingCanvasRequestDraft =
            serde_json::from_slice(bytes).map_err(|_| DrawingCanvasError::InvalidJson)?;
        Self::from_draft(draft, limits)
    }

    #[must_use]
    pub fn source(&self) -> &DrawingCanvasState {
        &self.source
    }

    #[must_use]
    pub fn target(&self) -> &DrawingCanvasState {
        &self.target
    }

    #[must_use]
    pub fn operation(&self) -> &DrawingCanvasOperation {
        &self.operation
    }

    #[must_use]
    pub fn before_document_flow_sha256(&self) -> &str {
        &self.before_document_flow_sha256
    }

    #[must_use]
    pub fn after_document_flow_sha256(&self) -> &str {
        &self.after_document_flow_sha256
    }

    /// Returns deterministic bounded request JSON.
    ///
    /// # Errors
    ///
    /// Rejects serialization beyond the configured bound.
    pub fn to_canonical_json(
        &self,
        limits: DrawingCanvasLimits,
    ) -> Result<Vec<u8>, DrawingCanvasError> {
        bounded_json(self, limits.0.output_bytes)
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct DrawingCanvasPlan {
    schema_version: String,
    request: DrawingCanvasRequest,
    request_sha256: String,
    source_state_sha256: String,
    target_state_sha256: String,
    before_document_flow_sha256: String,
    after_document_flow_sha256: String,
    plan_sha256: String,
}

impl fmt::Debug for DrawingCanvasPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("DrawingCanvasPlan")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.request.operation.capability_id())
            .field("digests", &"<redacted>")
            .finish_non_exhaustive()
    }
}

impl DrawingCanvasPlan {
    #[must_use]
    pub fn request(&self) -> &DrawingCanvasRequest {
        &self.request
    }

    #[must_use]
    pub fn target_state_sha256(&self) -> &str {
        &self.target_state_sha256
    }

    #[must_use]
    pub fn plan_sha256(&self) -> &str {
        &self.plan_sha256
    }

    /// Returns deterministic bounded plan JSON.
    ///
    /// # Errors
    ///
    /// Rejects serialization beyond the configured bound.
    pub fn to_canonical_json(
        &self,
        limits: DrawingCanvasLimits,
    ) -> Result<Vec<u8>, DrawingCanvasError> {
        bounded_json(self, limits.0.output_bytes)
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct DrawingCanvasReceipt {
    schema_version: String,
    capability_id: String,
    source_state_sha256: String,
    target_state_sha256: String,
    before_document_flow_sha256: String,
    after_document_flow_sha256: String,
    plan_sha256: String,
}

impl fmt::Debug for DrawingCanvasReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("DrawingCanvasReceipt")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("digests", &"<redacted>")
            .finish_non_exhaustive()
    }
}

impl DrawingCanvasReceipt {
    #[must_use]
    pub fn capability_id(&self) -> &str {
        &self.capability_id
    }

    #[must_use]
    pub fn target_state_sha256(&self) -> &str {
        &self.target_state_sha256
    }

    /// Returns deterministic bounded receipt JSON.
    ///
    /// # Errors
    ///
    /// Rejects serialization beyond the configured bound.
    pub fn to_canonical_json(
        &self,
        limits: DrawingCanvasLimits,
    ) -> Result<Vec<u8>, DrawingCanvasError> {
        bounded_json(self, limits.0.output_bytes)
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DrawingCanvasResult {
    pub target: DrawingCanvasState,
    pub receipt: DrawingCanvasReceipt,
}

#[derive(Clone, Copy, Debug, Default)]
pub struct DrawingCanvasBuilder;

impl DrawingCanvasBuilder {
    /// Seals an exact request against current state and document flow.
    ///
    /// # Errors
    ///
    /// Rejects source/flow drift or an invalid transition.
    pub fn plan(
        &self,
        request: DrawingCanvasRequest,
        current_state: &DrawingCanvasState,
        current_document_flow_sha256: &str,
        limits: DrawingCanvasLimits,
    ) -> Result<DrawingCanvasPlan, DrawingCanvasError> {
        validate_current(
            &request,
            current_state,
            current_document_flow_sha256,
            limits,
        )?;
        validate_transition(
            &request.source,
            &request.target,
            &request.operation,
            &request.before_document_flow_sha256,
            &request.after_document_flow_sha256,
            limits,
        )?;
        let request_sha256 = sha256_json(&request, limits.0.output_bytes)?;
        let target_state_sha256 = request.target.state_sha256(limits)?;
        let plan_sha256 = plan_digest(
            &request_sha256,
            &request.source_state_sha256,
            &target_state_sha256,
            &request.before_document_flow_sha256,
            &request.after_document_flow_sha256,
            request.operation.capability_id(),
        );
        Ok(DrawingCanvasPlan {
            schema_version: DRAWING_CANVAS_SCHEMA_VERSION.to_owned(),
            source_state_sha256: request.source_state_sha256.clone(),
            before_document_flow_sha256: request.before_document_flow_sha256.clone(),
            after_document_flow_sha256: request.after_document_flow_sha256.clone(),
            request,
            request_sha256,
            target_state_sha256,
            plan_sha256,
        })
    }

    /// Rechecks a sealed plan and returns the exact target state.
    ///
    /// # Errors
    ///
    /// Rejects source/flow drift, invalid target or plan tampering.
    pub fn build(
        &self,
        plan: &DrawingCanvasPlan,
        current_state: &DrawingCanvasState,
        current_document_flow_sha256: &str,
        limits: DrawingCanvasLimits,
    ) -> Result<DrawingCanvasResult, DrawingCanvasError> {
        if plan.schema_version != DRAWING_CANVAS_SCHEMA_VERSION {
            return Err(DrawingCanvasError::PlanTampered);
        }
        validate_current(
            &plan.request,
            current_state,
            current_document_flow_sha256,
            limits,
        )?;
        validate_transition(
            &plan.request.source,
            &plan.request.target,
            &plan.request.operation,
            &plan.request.before_document_flow_sha256,
            &plan.request.after_document_flow_sha256,
            limits,
        )?;
        let request_sha256 = sha256_json(&plan.request, limits.0.output_bytes)?;
        let target_state_sha256 = plan.request.target.state_sha256(limits)?;
        let expected_plan_sha256 = plan_digest(
            &request_sha256,
            &plan.request.source_state_sha256,
            &target_state_sha256,
            &plan.request.before_document_flow_sha256,
            &plan.request.after_document_flow_sha256,
            plan.request.operation.capability_id(),
        );
        if request_sha256 != plan.request_sha256
            || plan.source_state_sha256 != plan.request.source_state_sha256
            || target_state_sha256 != plan.target_state_sha256
            || plan.before_document_flow_sha256 != plan.request.before_document_flow_sha256
            || plan.after_document_flow_sha256 != plan.request.after_document_flow_sha256
            || expected_plan_sha256 != plan.plan_sha256
        {
            return Err(DrawingCanvasError::PlanTampered);
        }
        Ok(DrawingCanvasResult {
            target: plan.request.target.clone(),
            receipt: DrawingCanvasReceipt {
                schema_version: DRAWING_CANVAS_SCHEMA_VERSION.to_owned(),
                capability_id: plan.request.operation.capability_id().to_owned(),
                source_state_sha256: plan.source_state_sha256.clone(),
                target_state_sha256: plan.target_state_sha256.clone(),
                before_document_flow_sha256: plan.before_document_flow_sha256.clone(),
                after_document_flow_sha256: plan.after_document_flow_sha256.clone(),
                plan_sha256: plan.plan_sha256.clone(),
            },
        })
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum DrawingCanvasError {
    #[error("drawing-canvas schema does not match")]
    SchemaMismatch,
    #[error("drawing-canvas limits are invalid")]
    InvalidLimit,
    #[error("drawing-canvas JSON is invalid")]
    InvalidJson,
    #[error("drawing-canvas JSON contains a duplicate key")]
    DuplicateJsonKey,
    #[error("drawing-canvas input is too large")]
    InputTooLarge,
    #[error("drawing-canvas output is too large")]
    OutputTooLarge,
    #[error("drawing-canvas count limit was exceeded")]
    CountLimitExceeded,
    #[error("drawing-canvas identifier is invalid")]
    InvalidIdentifier,
    #[error("drawing-canvas digest is invalid")]
    InvalidDigest,
    #[error("drawing-canvas identity is duplicated or zero")]
    DuplicateIdentity,
    #[error("drawing-canvas geometry is invalid")]
    InvalidGeometry,
    #[error("drawing-canvas topology is invalid")]
    InvalidTopology,
    #[error("drawing-canvas resource state is invalid")]
    InvalidResource,
    #[error("drawing-canvas resource closure is invalid")]
    InvalidResourceClosure,
    #[error("drawing-canvas picture state is invalid")]
    InvalidPicture,
    #[error("drawing-canvas clip is invalid")]
    InvalidClip,
    #[error("drawing-canvas effects are invalid")]
    InvalidEffects,
    #[error("drawing-canvas OLE activation must remain blocked")]
    ActiveContentNotBlocked,
    #[error("drawing-canvas operation has no effect")]
    NoOp,
    #[error("drawing-canvas transition does not preserve untargeted state")]
    PreservationViolation,
    #[error("drawing-canvas identity reservation is invalid")]
    InvalidReservation,
    #[error("drawing-canvas source state drifted")]
    SourceStateDrift,
    #[error("drawing-canvas document flow drifted")]
    DocumentFlowDrift,
    #[error("drawing-canvas plan was tampered")]
    PlanTampered,
}

impl DrawingCanvasError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::SchemaMismatch => "drawing_canvas_schema_mismatch",
            Self::InvalidLimit => "drawing_canvas_invalid_limit",
            Self::InvalidJson => "drawing_canvas_invalid_json",
            Self::DuplicateJsonKey => "drawing_canvas_duplicate_json_key",
            Self::InputTooLarge => "drawing_canvas_input_too_large",
            Self::OutputTooLarge => "drawing_canvas_output_too_large",
            Self::CountLimitExceeded => "drawing_canvas_count_limit_exceeded",
            Self::InvalidIdentifier => "drawing_canvas_invalid_identifier",
            Self::InvalidDigest => "drawing_canvas_invalid_digest",
            Self::DuplicateIdentity => "drawing_canvas_duplicate_identity",
            Self::InvalidGeometry => "drawing_canvas_invalid_geometry",
            Self::InvalidTopology => "drawing_canvas_invalid_topology",
            Self::InvalidResource => "drawing_canvas_invalid_resource",
            Self::InvalidResourceClosure => "drawing_canvas_invalid_resource_closure",
            Self::InvalidPicture => "drawing_canvas_invalid_picture",
            Self::InvalidClip => "drawing_canvas_invalid_clip",
            Self::InvalidEffects => "drawing_canvas_invalid_effects",
            Self::ActiveContentNotBlocked => "drawing_canvas_active_content_not_blocked",
            Self::NoOp => "drawing_canvas_no_op",
            Self::PreservationViolation => "drawing_canvas_preservation_violation",
            Self::InvalidReservation => "drawing_canvas_invalid_reservation",
            Self::SourceStateDrift => "drawing_canvas_source_state_drift",
            Self::DocumentFlowDrift => "drawing_canvas_document_flow_drift",
            Self::PlanTampered => "drawing_canvas_plan_tampered",
        }
    }
}

fn validate_transition(
    source: &DrawingCanvasState,
    target: &DrawingCanvasState,
    operation: &DrawingCanvasOperation,
    before_flow: &str,
    after_flow: &str,
    limits: DrawingCanvasLimits,
) -> Result<(), DrawingCanvasError> {
    source.validate(limits)?;
    target.validate(limits)?;
    if source == target {
        return Err(DrawingCanvasError::NoOp);
    }
    match operation {
        DrawingCanvasOperation::InsertCanvas {
            root_canvas_id,
            reservation,
        } => validate_insert(source, target, root_canvas_id, reservation, limits),
        DrawingCanvasOperation::SetPictureClip { picture_id } => {
            if before_flow != after_flow {
                return Err(DrawingCanvasError::DocumentFlowDrift);
            }
            validate_picture_delta(source, target, picture_id, true)
        }
        DrawingCanvasOperation::SetPictureEffects { picture_id } => {
            if before_flow != after_flow {
                return Err(DrawingCanvasError::DocumentFlowDrift);
            }
            validate_picture_delta(source, target, picture_id, false)
        }
    }
}

fn validate_insert(
    source: &DrawingCanvasState,
    target: &DrawingCanvasState,
    root_canvas_id: &LogicalId,
    reservation: &CanvasIdentityReservation,
    limits: DrawingCanvasLimits,
) -> Result<(), DrawingCanvasError> {
    validate_sha256(&reservation.allocator_proof_sha256)?;
    if !strictly_sorted_unique_ids(&reservation.node_ids)
        || !strictly_sorted_unique_numbers(&reservation.native_object_ids)
        || !strictly_sorted_unique_numbers(&reservation.native_instance_ids)
        || !strictly_sorted_unique_ids(&reservation.resource_ids)
    {
        return Err(DrawingCanvasError::InvalidReservation);
    }
    if target.nodes.len() <= source.nodes.len() {
        return Err(DrawingCanvasError::InvalidReservation);
    }
    for source_node in &source.nodes {
        if target.node(&source_node.node_id) != Some(source_node) {
            return Err(DrawingCanvasError::PreservationViolation);
        }
    }
    for source_resource in &source.resources {
        if target.resource(&source_resource.resource_id) != Some(source_resource) {
            return Err(DrawingCanvasError::PreservationViolation);
        }
    }
    let source_node_ids: BTreeSet<_> = source.nodes.iter().map(|node| &node.node_id).collect();
    let source_resource_ids: BTreeSet<_> = source
        .resources
        .iter()
        .map(|resource| &resource.resource_id)
        .collect();
    let new_nodes: Vec<_> = target
        .nodes
        .iter()
        .filter(|node| !source_node_ids.contains(&node.node_id))
        .collect();
    let new_resources: Vec<_> = target
        .resources
        .iter()
        .filter(|resource| !source_resource_ids.contains(&resource.resource_id))
        .collect();
    let mut actual_node_ids: Vec<_> = new_nodes.iter().map(|node| node.node_id.clone()).collect();
    let mut actual_native_objects: Vec<_> =
        new_nodes.iter().map(|node| node.native_object_id).collect();
    let mut actual_native_instances: Vec<_> = new_nodes
        .iter()
        .map(|node| node.native_instance_id)
        .collect();
    let mut actual_resource_ids: Vec<_> = new_resources
        .iter()
        .map(|resource| resource.resource_id.clone())
        .collect();
    actual_node_ids.sort();
    actual_native_objects.sort_unstable();
    actual_native_instances.sort_unstable();
    actual_resource_ids.sort();
    if actual_node_ids != reservation.node_ids
        || actual_native_objects != reservation.native_object_ids
        || actual_native_instances != reservation.native_instance_ids
        || actual_resource_ids != reservation.resource_ids
    {
        return Err(DrawingCanvasError::InvalidReservation);
    }
    let root = target
        .node(root_canvas_id)
        .ok_or(DrawingCanvasError::InvalidReservation)?;
    if root.kind != CanvasNodeKind::Container
        || root.parent_id.is_some()
        || source_node_ids.contains(root_canvas_id)
    {
        return Err(DrawingCanvasError::InvalidReservation);
    }
    let source_root_count = source
        .nodes
        .iter()
        .filter(|node| node.parent_id.is_none())
        .count();
    if usize::try_from(root.ordinal).unwrap_or(usize::MAX) != source_root_count {
        return Err(DrawingCanvasError::InvalidReservation);
    }
    for node in new_nodes {
        if &node.node_id != root_canvas_id
            && !descends_from(&node.node_id, root_canvas_id, target, limits)?
        {
            return Err(DrawingCanvasError::InvalidReservation);
        }
    }
    Ok(())
}

fn validate_picture_delta(
    source: &DrawingCanvasState,
    target: &DrawingCanvasState,
    picture_id: &LogicalId,
    clip_delta: bool,
) -> Result<(), DrawingCanvasError> {
    if source.resources != target.resources
        || source.opaque_document_state_sha256 != target.opaque_document_state_sha256
        || source.nodes.len() != target.nodes.len()
    {
        return Err(DrawingCanvasError::PreservationViolation);
    }
    let source_picture = source
        .node(picture_id)
        .ok_or(DrawingCanvasError::InvalidPicture)?;
    let target_picture = target
        .node(picture_id)
        .ok_or(DrawingCanvasError::InvalidPicture)?;
    if source_picture.kind != CanvasNodeKind::Picture
        || target_picture.kind != CanvasNodeKind::Picture
    {
        return Err(DrawingCanvasError::InvalidPicture);
    }
    for source_node in &source.nodes {
        let target_node = target
            .node(&source_node.node_id)
            .ok_or(DrawingCanvasError::PreservationViolation)?;
        if &source_node.node_id != picture_id && source_node != target_node {
            return Err(DrawingCanvasError::PreservationViolation);
        }
    }
    let mut expected = source_picture.clone();
    let target_image = target_picture
        .picture
        .as_ref()
        .ok_or(DrawingCanvasError::InvalidPicture)?;
    let expected_image = expected
        .picture
        .as_mut()
        .ok_or(DrawingCanvasError::InvalidPicture)?;
    if clip_delta {
        if expected_image.clip == target_image.clip {
            return Err(DrawingCanvasError::NoOp);
        }
        expected_image.clip = target_image.clip;
        if expected.bindings.payload_sha256 == target_picture.bindings.payload_sha256 {
            return Err(DrawingCanvasError::PreservationViolation);
        }
        expected
            .bindings
            .payload_sha256
            .clone_from(&target_picture.bindings.payload_sha256);
    } else {
        if expected_image.effects == target_image.effects {
            return Err(DrawingCanvasError::NoOp);
        }
        expected_image.effects.clone_from(&target_image.effects);
        if expected.bindings.appearance_sha256 == target_picture.bindings.appearance_sha256 {
            return Err(DrawingCanvasError::PreservationViolation);
        }
        expected
            .bindings
            .appearance_sha256
            .clone_from(&target_picture.bindings.appearance_sha256);
    }
    if expected != *target_picture {
        return Err(DrawingCanvasError::PreservationViolation);
    }
    Ok(())
}

fn validate_current(
    request: &DrawingCanvasRequest,
    current_state: &DrawingCanvasState,
    current_flow: &str,
    limits: DrawingCanvasLimits,
) -> Result<(), DrawingCanvasError> {
    validate_sha256(current_flow)?;
    if request.source_state_sha256 != current_state.state_sha256(limits)?
        || request.source != *current_state
    {
        return Err(DrawingCanvasError::SourceStateDrift);
    }
    if request.before_document_flow_sha256 != current_flow {
        return Err(DrawingCanvasError::DocumentFlowDrift);
    }
    Ok(())
}

fn validate_bounds(
    bounds: CanvasBounds,
    limits: DrawingCanvasLimits,
) -> Result<(), DrawingCanvasError> {
    if bounds.width_hwpunit == 0 || bounds.height_hwpunit == 0 {
        return Err(DrawingCanvasError::InvalidGeometry);
    }
    let max = limits.0.coordinate_magnitude_hwpunit;
    if bounds.x_hwpunit.abs() > max
        || bounds.y_hwpunit.abs() > max
        || bounds.width_hwpunit > u64::try_from(max).unwrap_or(u64::MAX)
        || bounds.height_hwpunit > u64::try_from(max).unwrap_or(u64::MAX)
    {
        return Err(DrawingCanvasError::InvalidGeometry);
    }
    bounds
        .x_hwpunit
        .checked_add(
            i64::try_from(bounds.width_hwpunit).map_err(|_| DrawingCanvasError::InvalidGeometry)?,
        )
        .ok_or(DrawingCanvasError::InvalidGeometry)?;
    bounds
        .y_hwpunit
        .checked_add(
            i64::try_from(bounds.height_hwpunit)
                .map_err(|_| DrawingCanvasError::InvalidGeometry)?,
        )
        .ok_or(DrawingCanvasError::InvalidGeometry)?;
    Ok(())
}

fn validate_bindings(
    bindings: &CanvasBindings,
    limits: DrawingCanvasLimits,
) -> Result<(), DrawingCanvasError> {
    for digest in [
        &bindings.geometry_sha256,
        &bindings.payload_sha256,
        &bindings.appearance_sha256,
        &bindings.composition_sha256,
        &bindings.opaque_sha256,
    ] {
        validate_sha256(digest)?;
    }
    if bindings.opaque_byte_length > limits.0.opaque_bytes {
        return Err(DrawingCanvasError::CountLimitExceeded);
    }
    Ok(())
}

fn validate_resource(
    resource: &CanvasResource,
    limits: DrawingCanvasLimits,
) -> Result<(), DrawingCanvasError> {
    validate_identifier(resource.resource_id.as_str(), limits)?;
    validate_text(&resource.relationship_id, limits)?;
    let Some(relationship_number) = resource.relationship_id.strip_prefix("rId") else {
        return Err(DrawingCanvasError::InvalidResource);
    };
    if relationship_number.is_empty() || !relationship_number.chars().all(|ch| ch.is_ascii_digit())
    {
        return Err(DrawingCanvasError::InvalidResource);
    }
    if resource.media_type.is_empty()
        || resource.media_type.len() > limits.0.media_type_bytes
        || !resource.media_type.is_ascii()
        || resource.media_type.chars().any(char::is_whitespace)
        || !resource.media_type.contains('/')
    {
        return Err(DrawingCanvasError::InvalidResource);
    }
    validate_sha256(&resource.content_sha256)?;
    if resource.byte_length == 0 || resource.byte_length > limits.0.opaque_bytes {
        return Err(DrawingCanvasError::InvalidResource);
    }
    if let Some(digest) = &resource.external_target_sha256 {
        validate_sha256(digest)?;
    }
    match resource.kind {
        CanvasResourceKind::LinkedImage => {
            if resource.external_target_sha256.is_none() || resource.active_content_policy.is_some()
            {
                return Err(DrawingCanvasError::InvalidResource);
            }
        }
        CanvasResourceKind::OpaqueOle => {
            if resource.external_target_sha256.is_some()
                || resource.active_content_policy != Some(ActiveContentPolicy::Blocked)
            {
                return Err(DrawingCanvasError::ActiveContentNotBlocked);
            }
        }
        CanvasResourceKind::EmbeddedImage
        | CanvasResourceKind::ImageFill
        | CanvasResourceKind::Preview => {
            if resource.external_target_sha256.is_some() || resource.active_content_policy.is_some()
            {
                return Err(DrawingCanvasError::InvalidResource);
            }
        }
    }
    Ok(())
}

fn validate_picture_node(
    node: &CanvasNode,
    resources: &BTreeMap<LogicalId, &CanvasResource>,
    limits: DrawingCanvasLimits,
) -> Result<(), DrawingCanvasError> {
    if node.kind != CanvasNodeKind::Picture {
        if node.picture.is_some() {
            return Err(DrawingCanvasError::InvalidPicture);
        }
        return Ok(());
    }
    let picture = node
        .picture
        .as_ref()
        .ok_or(DrawingCanvasError::InvalidPicture)?;
    if picture.original_width_px == 0
        || picture.original_height_px == 0
        || picture.original_width_px > limits.0.image_dimension
        || picture.original_height_px > limits.0.image_dimension
        || node
            .resource_refs
            .binary_search(&picture.image_resource_id)
            .is_err()
    {
        return Err(DrawingCanvasError::InvalidPicture);
    }
    let resource = resources
        .get(&picture.image_resource_id)
        .ok_or(DrawingCanvasError::InvalidResourceClosure)?;
    if !matches!(
        resource.kind,
        CanvasResourceKind::EmbeddedImage | CanvasResourceKind::LinkedImage
    ) {
        return Err(DrawingCanvasError::InvalidPicture);
    }
    if let Some(clip) = picture.clip
        && (clip.left_px >= clip.right_px
            || clip.top_px >= clip.bottom_px
            || clip.right_px > picture.original_width_px
            || clip.bottom_px > picture.original_height_px)
    {
        return Err(DrawingCanvasError::InvalidClip);
    }
    if let Some(effects) = &picture.effects {
        let appearance = ObjectAppearance {
            picture_effects: Some(effects.clone()),
            ..ObjectAppearance::default()
        };
        let effect_limits = ObjectAppearanceLimits::new(ObjectAppearanceLimitConfig::default())
            .map_err(|_| DrawingCanvasError::InvalidEffects)?;
        appearance
            .validate(AppearanceTargetKind::Picture, effect_limits)
            .map_err(|_| DrawingCanvasError::InvalidEffects)?;
    }
    Ok(())
}

fn validate_ole_node(
    node: &CanvasNode,
    resources: &BTreeMap<LogicalId, &CanvasResource>,
) -> Result<(), DrawingCanvasError> {
    let ole_count = node
        .resource_refs
        .iter()
        .filter(|resource_id| {
            resources
                .get(*resource_id)
                .is_some_and(|resource| resource.kind == CanvasResourceKind::OpaqueOle)
        })
        .count();
    if node.kind == CanvasNodeKind::OpaqueOle {
        if ole_count != 1 || node.picture.is_some() {
            return Err(DrawingCanvasError::InvalidResourceClosure);
        }
    } else if ole_count != 0 {
        return Err(DrawingCanvasError::InvalidResourceClosure);
    }
    Ok(())
}

fn node_depth(
    node: &CanvasNode,
    node_map: &BTreeMap<LogicalId, &CanvasNode>,
    limits: DrawingCanvasLimits,
) -> Result<usize, DrawingCanvasError> {
    let mut depth = 0usize;
    let mut parent = node.parent_id.as_ref();
    let mut visited = BTreeSet::new();
    visited.insert(node.node_id.clone());
    while let Some(parent_id) = parent {
        if !visited.insert(parent_id.clone()) {
            return Err(DrawingCanvasError::InvalidTopology);
        }
        depth = depth.saturating_add(1);
        if depth > limits.0.depth {
            return Err(DrawingCanvasError::InvalidTopology);
        }
        parent = node_map
            .get(parent_id)
            .ok_or(DrawingCanvasError::InvalidTopology)?
            .parent_id
            .as_ref();
    }
    Ok(depth)
}

fn descends_from(
    node_id: &LogicalId,
    ancestor_id: &LogicalId,
    state: &DrawingCanvasState,
    limits: DrawingCanvasLimits,
) -> Result<bool, DrawingCanvasError> {
    let mut current = state
        .node(node_id)
        .ok_or(DrawingCanvasError::InvalidTopology)?;
    for _ in 0..=limits.0.depth {
        let Some(parent_id) = &current.parent_id else {
            return Ok(false);
        };
        if parent_id == ancestor_id {
            return Ok(true);
        }
        current = state
            .node(parent_id)
            .ok_or(DrawingCanvasError::InvalidTopology)?;
    }
    Err(DrawingCanvasError::InvalidTopology)
}

fn validate_identifier(value: &str, limits: DrawingCanvasLimits) -> Result<(), DrawingCanvasError> {
    if value.is_empty()
        || value.len() > limits.0.identifier_bytes
        || value.chars().any(char::is_control)
        || value.nfc().collect::<String>() != value
    {
        return Err(DrawingCanvasError::InvalidIdentifier);
    }
    Ok(())
}

fn validate_text(value: &str, limits: DrawingCanvasLimits) -> Result<(), DrawingCanvasError> {
    validate_identifier(value, limits)
}

fn validate_sha256(value: &str) -> Result<(), DrawingCanvasError> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
    {
        return Err(DrawingCanvasError::InvalidDigest);
    }
    Ok(())
}

fn strictly_sorted_unique_ids(values: &[LogicalId]) -> bool {
    values.windows(2).all(|pair| pair[0] < pair[1])
}

fn strictly_sorted_unique_numbers(values: &[u32]) -> bool {
    values.windows(2).all(|pair| pair[0] < pair[1]) && values.iter().all(|value| *value != 0)
}

fn plan_digest(
    request: &str,
    source: &str,
    target: &str,
    before_flow: &str,
    after_flow: &str,
    capability_id: &str,
) -> String {
    let mut hasher = Sha256::new();
    for value in [
        DRAWING_CANVAS_SCHEMA_VERSION,
        request,
        source,
        target,
        before_flow,
        after_flow,
        capability_id,
    ] {
        hasher.update(value.as_bytes());
        hasher.update([0]);
    }
    hex(hasher.finalize().into())
}

fn sha256_json<T: Serialize>(value: &T, limit: usize) -> Result<String, DrawingCanvasError> {
    let bytes = bounded_json(value, limit)?;
    Ok(hex(Sha256::digest(bytes).into()))
}

fn hex(bytes: [u8; 32]) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(64);
    for byte in bytes {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}

fn bounded_json<T: Serialize>(value: &T, limit: usize) -> Result<Vec<u8>, DrawingCanvasError> {
    let bytes = serde_json::to_vec(value).map_err(|_| DrawingCanvasError::InvalidJson)?;
    if bytes.len() > limit {
        return Err(DrawingCanvasError::OutputTooLarge);
    }
    Ok(bytes)
}

fn reject_duplicate_json_keys(bytes: &[u8]) -> Result<(), DrawingCanvasError> {
    struct NoDuplicates;

    impl<'de> serde::de::DeserializeSeed<'de> for NoDuplicates {
        type Value = ();

        fn deserialize<D>(self, deserializer: D) -> Result<Self::Value, D::Error>
        where
            D: serde::Deserializer<'de>,
        {
            deserializer.deserialize_any(NoDuplicatesVisitor)
        }
    }

    struct NoDuplicatesVisitor;

    impl<'de> Visitor<'de> for NoDuplicatesVisitor {
        type Value = ();

        fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
            formatter.write_str("JSON without duplicate object keys")
        }

        fn visit_map<A>(self, mut map: A) -> Result<Self::Value, A::Error>
        where
            A: MapAccess<'de>,
        {
            let mut keys = BTreeSet::new();
            while let Some(key) = map.next_key::<String>()? {
                if !keys.insert(key) {
                    return Err(de::Error::custom("duplicate key"));
                }
                map.next_value_seed(NoDuplicates)?;
            }
            Ok(())
        }

        fn visit_seq<A>(self, mut sequence: A) -> Result<Self::Value, A::Error>
        where
            A: serde::de::SeqAccess<'de>,
        {
            while sequence.next_element_seed(NoDuplicates)?.is_some() {}
            Ok(())
        }

        fn visit_bool<E>(self, _value: bool) -> Result<Self::Value, E> {
            Ok(())
        }

        fn visit_i64<E>(self, _value: i64) -> Result<Self::Value, E> {
            Ok(())
        }

        fn visit_u64<E>(self, _value: u64) -> Result<Self::Value, E> {
            Ok(())
        }

        fn visit_f64<E>(self, _value: f64) -> Result<Self::Value, E> {
            Ok(())
        }

        fn visit_str<E>(self, _value: &str) -> Result<Self::Value, E> {
            Ok(())
        }

        fn visit_string<E>(self, _value: String) -> Result<Self::Value, E> {
            Ok(())
        }

        fn visit_none<E>(self) -> Result<Self::Value, E> {
            Ok(())
        }

        fn visit_unit<E>(self) -> Result<Self::Value, E> {
            Ok(())
        }

        fn visit_some<D>(self, deserializer: D) -> Result<Self::Value, D::Error>
        where
            D: serde::Deserializer<'de>,
        {
            NoDuplicates.deserialize(deserializer)
        }
    }

    let mut deserializer = serde_json::Deserializer::from_slice(bytes);
    NoDuplicates
        .deserialize(&mut deserializer)
        .map_err(|error| {
            if error.to_string().contains("duplicate key") {
                DrawingCanvasError::DuplicateJsonKey
            } else {
                DrawingCanvasError::InvalidJson
            }
        })?;
    deserializer
        .end()
        .map_err(|_| DrawingCanvasError::InvalidJson)
}

#[cfg(test)]
mod private_tests {
    use super::*;

    type TestResult<T = ()> = Result<T, Box<dyn std::error::Error>>;

    fn id(value: &str) -> TestResult<LogicalId> {
        Ok(LogicalId::parse(value)?)
    }

    fn sha(value: u8) -> String {
        format!("{value:02x}").repeat(32)
    }

    fn empty_state(limits: DrawingCanvasLimits) -> TestResult<DrawingCanvasState> {
        Ok(DrawingCanvasState::from_draft(
            DrawingCanvasStateDraft {
                schema_version: DRAWING_CANVAS_SCHEMA_VERSION.to_owned(),
                document_id: id("document")?,
                nodes: Vec::new(),
                resources: Vec::new(),
                opaque_document_state_sha256: sha(1),
            },
            limits,
        )?)
    }

    fn inserted_target(limits: DrawingCanvasLimits) -> TestResult<DrawingCanvasState> {
        let resource = CanvasResource {
            resource_id: id("image")?,
            relationship_id: "rId1".to_owned(),
            kind: CanvasResourceKind::EmbeddedImage,
            media_type: "image/png".to_owned(),
            content_sha256: sha(2),
            byte_length: 10,
            external_target_sha256: None,
            active_content_policy: None,
        };
        let binding = CanvasBindings {
            geometry_sha256: sha(3),
            payload_sha256: sha(4),
            appearance_sha256: sha(5),
            composition_sha256: sha(6),
            opaque_sha256: sha(7),
            opaque_byte_length: 0,
        };
        let root = CanvasNode {
            node_id: id("canvas")?,
            native_object_id: 1,
            native_instance_id: 2,
            kind: CanvasNodeKind::Container,
            parent_id: None,
            ordinal: 0,
            group_level: 0,
            bounds: CanvasBounds {
                x_hwpunit: 0,
                y_hwpunit: 0,
                width_hwpunit: 100,
                height_hwpunit: 100,
            },
            visible: true,
            printable: true,
            protected: false,
            bindings: binding.clone(),
            resource_refs: Vec::new(),
            picture: None,
        };
        let picture = CanvasNode {
            node_id: id("picture")?,
            native_object_id: 3,
            native_instance_id: 4,
            kind: CanvasNodeKind::Picture,
            parent_id: Some(id("canvas")?),
            ordinal: 0,
            group_level: 1,
            bounds: root.bounds,
            visible: true,
            printable: true,
            protected: false,
            bindings: binding,
            resource_refs: vec![id("image")?],
            picture: Some(CanvasPictureState {
                image_resource_id: id("image")?,
                original_width_px: 10,
                original_height_px: 10,
                clip: None,
                effects: None,
            }),
        };
        Ok(DrawingCanvasState::from_draft(
            DrawingCanvasStateDraft {
                schema_version: DRAWING_CANVAS_SCHEMA_VERSION.to_owned(),
                document_id: id("document")?,
                nodes: vec![root, picture],
                resources: vec![resource],
                opaque_document_state_sha256: sha(1),
            },
            limits,
        )?)
    }

    #[test]
    fn private_plan_seal_rejects_tampering() -> TestResult {
        let limits = DrawingCanvasLimits::new(DrawingCanvasLimitConfig::default())?;
        let source = empty_state(limits)?;
        let target = inserted_target(limits)?;
        let request = DrawingCanvasRequest::from_draft(
            DrawingCanvasRequestDraft {
                schema_version: DRAWING_CANVAS_SCHEMA_VERSION.to_owned(),
                request_id: "request".to_owned(),
                source: DrawingCanvasStateDraft {
                    schema_version: DRAWING_CANVAS_SCHEMA_VERSION.to_owned(),
                    document_id: id("document")?,
                    nodes: Vec::new(),
                    resources: Vec::new(),
                    opaque_document_state_sha256: sha(1),
                },
                target: DrawingCanvasStateDraft {
                    schema_version: DRAWING_CANVAS_SCHEMA_VERSION.to_owned(),
                    document_id: id("document")?,
                    nodes: target.nodes.clone(),
                    resources: target.resources.clone(),
                    opaque_document_state_sha256: sha(1),
                },
                operation: DrawingCanvasOperation::InsertCanvas {
                    root_canvas_id: id("canvas")?,
                    reservation: CanvasIdentityReservation {
                        node_ids: vec![id("canvas")?, id("picture")?],
                        native_object_ids: vec![1, 3],
                        native_instance_ids: vec![2, 4],
                        resource_ids: vec![id("image")?],
                        allocator_proof_sha256: sha(8),
                    },
                },
                source_state_sha256: source.state_sha256(limits)?,
                before_document_flow_sha256: sha(9),
                after_document_flow_sha256: sha(10),
            },
            limits,
        )?;
        let builder = DrawingCanvasBuilder;
        let mut plan = builder.plan(request, &source, &sha(9), limits)?;
        plan.target_state_sha256 = sha(11);
        assert_eq!(
            builder.build(&plan, &source, &sha(9), limits),
            Err(DrawingCanvasError::PlanTampered)
        );
        Ok(())
    }
}
