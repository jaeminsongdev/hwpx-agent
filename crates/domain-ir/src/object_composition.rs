use std::collections::{BTreeMap, BTreeSet};
use std::fmt;

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use thiserror::Error;

use crate::LogicalId;

pub const OBJECT_COMPOSITION_SCHEMA_VERSION: &str = "hwpx-agent.object-composition/v1";

const COUNT_LIMIT_CEILING: usize = 1_000_000;
const DEPTH_LIMIT_CEILING: usize = 256;
const BYTE_LIMIT_CEILING: usize = 256 * 1024 * 1024;
const COORDINATE_LIMIT_CEILING: i64 = 1_000_000_000_000;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ObjectCompositionLimitConfig {
    pub input_bytes: usize,
    pub serialized_bytes: usize,
    pub objects: usize,
    pub selection: usize,
    pub resources_per_object: usize,
    pub control_points: usize,
    pub depth: usize,
    pub identifier_bytes: usize,
    pub coordinate_magnitude_hwpunit: i64,
    pub content_bytes: u64,
    pub connection_index: u32,
}

impl Default for ObjectCompositionLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 4 * 1024 * 1024,
            serialized_bytes: 16 * 1024 * 1024,
            objects: 65_536,
            selection: 65_536,
            resources_per_object: 4_096,
            control_points: 4_096,
            depth: 64,
            identifier_bytes: 512,
            coordinate_magnitude_hwpunit: 1_000_000_000,
            content_bytes: 256 * 1024 * 1024,
            connection_index: 65_535,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ObjectCompositionLimits(ObjectCompositionLimitConfig);

impl ObjectCompositionLimits {
    /// Creates finite limits for untrusted composition graphs and requests.
    ///
    /// # Errors
    ///
    /// Rejects zero, inconsistent or process-hostile limit configurations.
    pub fn new(config: ObjectCompositionLimitConfig) -> Result<Self, ObjectCompositionError> {
        if config.input_bytes == 0
            || config.serialized_bytes == 0
            || config.input_bytes > config.serialized_bytes
            || config.serialized_bytes > BYTE_LIMIT_CEILING
            || config.objects < 3
            || config.objects > COUNT_LIMIT_CEILING
            || config.selection < 3
            || config.selection > config.objects
            || config.resources_per_object == 0
            || config.resources_per_object > COUNT_LIMIT_CEILING
            || config.control_points == 0
            || config.control_points > COUNT_LIMIT_CEILING
            || config.depth == 0
            || config.depth > DEPTH_LIMIT_CEILING
            || config.identifier_bytes == 0
            || config.identifier_bytes > 4 * 1024 * 1024
            || config.coordinate_magnitude_hwpunit <= 0
            || config.coordinate_magnitude_hwpunit > COORDINATE_LIMIT_CEILING
            || config.content_bytes == 0
            || config.content_bytes > u64::try_from(BYTE_LIMIT_CEILING).unwrap_or(u64::MAX)
            || config.connection_index == 0
        {
            return Err(ObjectCompositionError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> ObjectCompositionLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CompositionBounds {
    pub x_hwpunit: i64,
    pub y_hwpunit: i64,
    pub width_hwpunit: u64,
    pub height_hwpunit: u64,
}

impl CompositionBounds {
    fn right(self) -> Result<i64, ObjectCompositionError> {
        self.x_hwpunit
            .checked_add(
                i64::try_from(self.width_hwpunit)
                    .map_err(|_| ObjectCompositionError::InvalidGeometry)?,
            )
            .ok_or(ObjectCompositionError::InvalidGeometry)
    }

    fn bottom(self) -> Result<i64, ObjectCompositionError> {
        self.y_hwpunit
            .checked_add(
                i64::try_from(self.height_hwpunit)
                    .map_err(|_| ObjectCompositionError::InvalidGeometry)?,
            )
            .ok_or(ObjectCompositionError::InvalidGeometry)
    }
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CompositionObjectContent {
    pub state_sha256: String,
    pub byte_length: u64,
    pub resource_refs: Vec<LogicalId>,
}

impl fmt::Debug for CompositionObjectContent {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CompositionObjectContent")
            .field("byte_length", &self.byte_length)
            .field("resource_count", &self.resource_refs.len())
            .field("state", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CompositionObjectKind {
    Group,
    BasicShape,
    Picture,
    Chart,
    TextBox,
    Embedded,
    Connector,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ConnectorKind {
    StraightNoArrow,
    StraightOneWay,
    StraightBoth,
    StrokeNoArrow,
    StrokeOneWay,
    StrokeBoth,
    ArcNoArrow,
    ArcOneWay,
    ArcBoth,
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ConnectorSubject {
    pub object_id: LogicalId,
    pub connection_index: u32,
}

impl fmt::Debug for ConnectorSubject {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ConnectorSubject")
            .field("object_id", &"<redacted>")
            .field("connection_index", &self.connection_index)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ConnectorEndpoint {
    pub x_hwpunit: i64,
    pub y_hwpunit: i64,
    pub subject: Option<ConnectorSubject>,
}

impl fmt::Debug for ConnectorEndpoint {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ConnectorEndpoint")
            .field("point", &"<redacted>")
            .field("attached", &self.subject.is_some())
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ConnectorControlPoint {
    pub x_hwpunit: i64,
    pub y_hwpunit: i64,
    pub point_type: u32,
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ConnectorTopology {
    pub kind: ConnectorKind,
    pub start: ConnectorEndpoint,
    pub end: ConnectorEndpoint,
    pub control_points: Vec<ConnectorControlPoint>,
}

impl fmt::Debug for ConnectorTopology {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ConnectorTopology")
            .field("kind", &self.kind)
            .field("start_attached", &self.start.subject.is_some())
            .field("end_attached", &self.end.subject.is_some())
            .field("control_points", &self.control_points.len())
            .field("coordinates", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CompositionObject {
    pub object_id: LogicalId,
    pub native_object_id: u32,
    pub native_instance_id: u32,
    pub kind: CompositionObjectKind,
    pub parent_group_id: Option<LogicalId>,
    pub z_order: u32,
    pub group_level: u32,
    pub bounds: CompositionBounds,
    pub visible: bool,
    pub printable: bool,
    pub content: CompositionObjectContent,
    pub connector: Option<ConnectorTopology>,
}

impl fmt::Debug for CompositionObject {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CompositionObject")
            .field("kind", &self.kind)
            .field("z_order", &self.z_order)
            .field("group_level", &self.group_level)
            .field("visible", &self.visible)
            .field("printable", &self.printable)
            .field("identity", &"<redacted>")
            .field("bounds", &"<redacted>")
            .field("content", &self.content)
            .field("connector", &self.connector)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ObjectCompositionGraphDraft {
    pub schema_version: String,
    pub objects: Vec<CompositionObject>,
}

impl fmt::Debug for ObjectCompositionGraphDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectCompositionGraphDraft")
            .field("objects", &self.objects.len())
            .field("state", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ObjectCompositionGraph {
    schema_version: &'static str,
    objects: Vec<CompositionObject>,
}

impl ObjectCompositionGraph {
    /// Validates and canonicalizes a complete object-composition graph.
    ///
    /// # Errors
    ///
    /// Rejects identity, ordering, containment, bounds, content and connector violations.
    pub fn from_draft(
        mut draft: ObjectCompositionGraphDraft,
        limits: ObjectCompositionLimits,
    ) -> Result<Self, ObjectCompositionError> {
        if draft.schema_version != OBJECT_COMPOSITION_SCHEMA_VERSION {
            return Err(ObjectCompositionError::UnsupportedVersion);
        }
        if draft.objects.is_empty() || draft.objects.len() > limits.0.objects {
            return Err(ObjectCompositionError::InputLimit);
        }
        draft
            .objects
            .sort_by(|left, right| left.object_id.cmp(&right.object_id));
        let graph = Self {
            schema_version: OBJECT_COMPOSITION_SCHEMA_VERSION,
            objects: draft.objects,
        };
        graph.validate(limits)?;
        let _ = graph.canonical_json(limits)?;
        Ok(graph)
    }

    /// Parses bounded duplicate-key-free strict JSON into a validated graph.
    ///
    /// # Errors
    ///
    /// Rejects malformed, duplicate, unknown, oversized or invalid graph input.
    pub fn from_json(
        bytes: &[u8],
        limits: ObjectCompositionLimits,
    ) -> Result<Self, ObjectCompositionError> {
        if bytes.is_empty() || bytes.len() > limits.0.input_bytes {
            return Err(ObjectCompositionError::InputLimit);
        }
        reject_duplicate_json_keys(bytes)?;
        let draft =
            serde_json::from_slice(bytes).map_err(|_| ObjectCompositionError::InvalidJson)?;
        Self::from_draft(draft, limits)
    }

    #[must_use]
    pub fn objects(&self) -> &[CompositionObject] {
        &self.objects
    }

    #[must_use]
    pub fn object(&self, object_id: &LogicalId) -> Option<&CompositionObject> {
        self.objects
            .binary_search_by(|candidate| candidate.object_id.cmp(object_id))
            .ok()
            .and_then(|index| self.objects.get(index))
    }

    /// Emits compact deterministic JSON within the configured bound.
    ///
    /// # Errors
    ///
    /// Returns serialization or output-limit failures.
    pub fn canonical_json(
        &self,
        limits: ObjectCompositionLimits,
    ) -> Result<Vec<u8>, ObjectCompositionError> {
        serialize_bounded(self, limits)
    }

    /// Returns the canonical complete-state digest.
    ///
    /// # Errors
    ///
    /// Returns serialization or output-limit failures.
    pub fn canonical_sha256(
        &self,
        limits: ObjectCompositionLimits,
    ) -> Result<String, ObjectCompositionError> {
        Ok(hex(Sha256::digest(self.canonical_json(limits)?).into()))
    }

    fn validate(&self, limits: ObjectCompositionLimits) -> Result<(), ObjectCompositionError> {
        if self.schema_version != OBJECT_COMPOSITION_SCHEMA_VERSION
            || self.objects.is_empty()
            || self.objects.len() > limits.0.objects
        {
            return Err(ObjectCompositionError::InvalidGraph);
        }
        let mut ids = BTreeSet::new();
        let mut native_ids = BTreeSet::new();
        let mut instance_ids = BTreeSet::new();
        for object in &self.objects {
            validate_id(&object.object_id, limits)?;
            if !ids.insert(object.object_id.clone())
                || object.native_object_id == 0
                || !native_ids.insert(object.native_object_id)
                || object.native_instance_id == 0
                || !instance_ids.insert(object.native_instance_id)
            {
                return Err(ObjectCompositionError::DuplicateIdentity);
            }
            validate_bounds(object.bounds, object.kind, limits)?;
            validate_content(&object.content, limits)?;
            if (object.kind == CompositionObjectKind::Connector) != object.connector.is_some() {
                return Err(ObjectCompositionError::InvalidConnector);
            }
        }
        let index = self.index();
        let mut siblings: BTreeMap<Option<LogicalId>, Vec<&CompositionObject>> = BTreeMap::new();
        for object in &self.objects {
            if let Some(parent) = &object.parent_group_id {
                let parent_object = index
                    .get(parent)
                    .ok_or(ObjectCompositionError::DanglingEdge)?;
                if parent_object.kind != CompositionObjectKind::Group || parent == &object.object_id
                {
                    return Err(ObjectCompositionError::InvalidContainment);
                }
            }
            siblings
                .entry(object.parent_group_id.clone())
                .or_default()
                .push(object);
        }
        for children in siblings.values_mut() {
            children.sort_by_key(|object| object.z_order);
            for (expected, object) in children.iter().enumerate() {
                if usize::try_from(object.z_order).ok() != Some(expected) {
                    return Err(ObjectCompositionError::InvalidZOrder);
                }
            }
        }
        for object in &self.objects {
            let depth = depth_of(object, &index, limits)?;
            if usize::try_from(object.group_level).ok() != Some(depth) {
                return Err(ObjectCompositionError::InvalidContainment);
            }
            if object.kind == CompositionObjectKind::Group {
                let children = siblings
                    .get(&Some(object.object_id.clone()))
                    .ok_or(ObjectCompositionError::InvalidContainment)?;
                if children.len() < 2
                    || union_bounds(children.iter().copied(), limits)? != object.bounds
                {
                    return Err(ObjectCompositionError::InvalidGroupBounds);
                }
            }
            if let Some(connector) = &object.connector {
                validate_connector(object, connector, &index, limits)?;
            }
        }
        Ok(())
    }

    fn index(&self) -> BTreeMap<LogicalId, &CompositionObject> {
        self.objects
            .iter()
            .map(|object| (object.object_id.clone(), object))
            .collect()
    }

    fn apply(
        &self,
        operation: &ObjectCompositionOperation,
        limits: ObjectCompositionLimits,
    ) -> Result<Self, ObjectCompositionError> {
        let mut target = self.clone();
        match operation {
            ObjectCompositionOperation::Group { group, member_ids } => {
                target.apply_group(group, member_ids, limits)?;
            }
            ObjectCompositionOperation::Ungroup { group_id } => {
                target.apply_ungroup(group_id, limits)?;
            }
            ObjectCompositionOperation::SetZOrder {
                object_id,
                movement,
            } => {
                target.apply_z_order(object_id, *movement)?;
            }
            ObjectCompositionOperation::Align { object_ids, mode } => {
                target.apply_align(object_ids, *mode, limits)?;
            }
            ObjectCompositionOperation::Distribute { object_ids, axis } => {
                target.apply_distribute(object_ids, *axis, limits)?;
            }
            ObjectCompositionOperation::CreateConnector { connector } => {
                target.apply_create_connector(connector, limits)?;
            }
            ObjectCompositionOperation::UpdateConnector {
                connector_id,
                topology,
            } => target.apply_update_connector(connector_id, topology, limits)?,
        }
        target
            .objects
            .sort_by(|left, right| left.object_id.cmp(&right.object_id));
        recompute_levels(&mut target.objects, limits)?;
        recompute_group_bounds(&mut target.objects, limits)?;
        target.validate(limits)?;
        if target == *self {
            return Err(ObjectCompositionError::NoChange);
        }
        Ok(target)
    }

    fn apply_group(
        &mut self,
        group: &NewGroup,
        member_ids: &[LogicalId],
        limits: ObjectCompositionLimits,
    ) -> Result<(), ObjectCompositionError> {
        validate_selection(member_ids, 2, limits)?;
        validate_new_identity(
            &self.objects,
            &group.object_id,
            group.native_object_id,
            group.native_instance_id,
            limits,
        )?;
        validate_content(&group.content, limits)?;
        let selected: BTreeSet<_> = member_ids.iter().cloned().collect();
        let mut members: Vec<_> = self
            .objects
            .iter()
            .filter(|object| selected.contains(&object.object_id))
            .cloned()
            .collect();
        if members.len() != member_ids.len() {
            return Err(ObjectCompositionError::ObjectNotFound);
        }
        let parent = members[0].parent_group_id.clone();
        if members
            .iter()
            .any(|object| object.parent_group_id != parent)
        {
            return Err(ObjectCompositionError::MixedParents);
        }
        members.sort_by_key(|object| object.z_order);
        let group_z = members[0].z_order;
        let bounds = union_bounds(members.iter(), limits)?;
        let mut parent_order = sibling_ids(&self.objects, parent.as_ref());
        parent_order.retain(|id| !selected.contains(id));
        let insertion =
            usize::try_from(group_z).map_err(|_| ObjectCompositionError::InvalidZOrder)?;
        if insertion > parent_order.len() {
            return Err(ObjectCompositionError::InvalidZOrder);
        }
        parent_order.insert(insertion, group.object_id.clone());
        for (z_order, member) in members.iter().enumerate() {
            let target = object_mut(&mut self.objects, &member.object_id)?;
            target.parent_group_id = Some(group.object_id.clone());
            target.z_order =
                u32::try_from(z_order).map_err(|_| ObjectCompositionError::InputLimit)?;
        }
        self.objects.push(CompositionObject {
            object_id: group.object_id.clone(),
            native_object_id: group.native_object_id,
            native_instance_id: group.native_instance_id,
            kind: CompositionObjectKind::Group,
            parent_group_id: parent.clone(),
            z_order: group_z,
            group_level: 0,
            bounds,
            visible: group.visible,
            printable: group.printable,
            content: group.content.clone(),
            connector: None,
        });
        set_sibling_order(&mut self.objects, parent.as_ref(), &parent_order)?;
        Ok(())
    }

    fn apply_ungroup(
        &mut self,
        group_id: &LogicalId,
        limits: ObjectCompositionLimits,
    ) -> Result<(), ObjectCompositionError> {
        validate_id(group_id, limits)?;
        let group = self
            .object(group_id)
            .cloned()
            .ok_or(ObjectCompositionError::ObjectNotFound)?;
        if group.kind != CompositionObjectKind::Group {
            return Err(ObjectCompositionError::InvalidOperation);
        }
        let mut child_ids = sibling_ids(&self.objects, Some(group_id));
        if child_ids.len() < 2 {
            return Err(ObjectCompositionError::InvalidContainment);
        }
        let mut parent_order = sibling_ids(&self.objects, group.parent_group_id.as_ref());
        let position = parent_order
            .iter()
            .position(|id| id == group_id)
            .ok_or(ObjectCompositionError::InvalidContainment)?;
        parent_order.remove(position);
        for (offset, child_id) in child_ids.iter().enumerate() {
            parent_order.insert(position + offset, child_id.clone());
            object_mut(&mut self.objects, child_id)?
                .parent_group_id
                .clone_from(&group.parent_group_id);
        }
        self.objects.retain(|object| &object.object_id != group_id);
        set_sibling_order(
            &mut self.objects,
            group.parent_group_id.as_ref(),
            &parent_order,
        )?;
        child_ids.clear();
        Ok(())
    }

    fn apply_z_order(
        &mut self,
        object_id: &LogicalId,
        movement: ZOrderMove,
    ) -> Result<(), ObjectCompositionError> {
        let object = self
            .object(object_id)
            .cloned()
            .ok_or(ObjectCompositionError::ObjectNotFound)?;
        let mut order = sibling_ids(&self.objects, object.parent_group_id.as_ref());
        let source = order
            .iter()
            .position(|id| id == object_id)
            .ok_or(ObjectCompositionError::InvalidZOrder)?;
        let destination = match movement {
            ZOrderMove::BringToFront => order.len().saturating_sub(1),
            ZOrderMove::SendToBack => 0,
            ZOrderMove::ForwardOne => source.saturating_add(1).min(order.len().saturating_sub(1)),
            ZOrderMove::BackwardOne => source.saturating_sub(1),
        };
        if destination == source {
            return Err(ObjectCompositionError::NoChange);
        }
        let moved = order.remove(source);
        order.insert(destination, moved);
        set_sibling_order(&mut self.objects, object.parent_group_id.as_ref(), &order)
    }

    fn apply_align(
        &mut self,
        object_ids: &[LogicalId],
        mode: ObjectAlignMode,
        limits: ObjectCompositionLimits,
    ) -> Result<(), ObjectCompositionError> {
        let selected = selected_objects(&self.objects, object_ids, 2, limits)?;
        require_movable_siblings(&selected)?;
        let envelope = union_bounds(selected.iter(), limits)?;
        for object in selected {
            let (new_x, new_y) = match mode {
                ObjectAlignMode::Left => (envelope.x_hwpunit, object.bounds.y_hwpunit),
                ObjectAlignMode::HorizontalCenter => (
                    centered_start(
                        envelope.x_hwpunit,
                        envelope.width_hwpunit,
                        object.bounds.width_hwpunit,
                    )?,
                    object.bounds.y_hwpunit,
                ),
                ObjectAlignMode::Right => (
                    envelope
                        .right()?
                        .checked_sub(
                            i64::try_from(object.bounds.width_hwpunit)
                                .map_err(|_| ObjectCompositionError::InvalidGeometry)?,
                        )
                        .ok_or(ObjectCompositionError::InvalidGeometry)?,
                    object.bounds.y_hwpunit,
                ),
                ObjectAlignMode::Top => (object.bounds.x_hwpunit, envelope.y_hwpunit),
                ObjectAlignMode::VerticalMiddle => (
                    object.bounds.x_hwpunit,
                    centered_start(
                        envelope.y_hwpunit,
                        envelope.height_hwpunit,
                        object.bounds.height_hwpunit,
                    )?,
                ),
                ObjectAlignMode::Bottom => (
                    object.bounds.x_hwpunit,
                    envelope
                        .bottom()?
                        .checked_sub(
                            i64::try_from(object.bounds.height_hwpunit)
                                .map_err(|_| ObjectCompositionError::InvalidGeometry)?,
                        )
                        .ok_or(ObjectCompositionError::InvalidGeometry)?,
                ),
            };
            translate_subtree(
                &mut self.objects,
                &object.object_id,
                new_x
                    .checked_sub(object.bounds.x_hwpunit)
                    .ok_or(ObjectCompositionError::InvalidGeometry)?,
                new_y
                    .checked_sub(object.bounds.y_hwpunit)
                    .ok_or(ObjectCompositionError::InvalidGeometry)?,
                limits,
            )?;
        }
        Ok(())
    }

    fn apply_distribute(
        &mut self,
        object_ids: &[LogicalId],
        axis: CompositionAxis,
        limits: ObjectCompositionLimits,
    ) -> Result<(), ObjectCompositionError> {
        let mut selected = selected_objects(&self.objects, object_ids, 3, limits)?;
        require_movable_siblings(&selected)?;
        selected.sort_by(|left, right| {
            let left_start = axis_start(left.bounds, axis);
            let right_start = axis_start(right.bounds, axis);
            left_start
                .cmp(&right_start)
                .then_with(|| left.object_id.cmp(&right.object_id))
        });
        let first_start = axis_start(selected[0].bounds, axis);
        let last_end = axis_end(selected[selected.len() - 1].bounds, axis)?;
        let extent_sum = selected.iter().try_fold(0_i64, |sum, object| {
            sum.checked_add(axis_extent(object.bounds, axis)?)
                .ok_or(ObjectCompositionError::InvalidGeometry)
        })?;
        let total_gap = last_end
            .checked_sub(first_start)
            .and_then(|value| value.checked_sub(extent_sum))
            .ok_or(ObjectCompositionError::InvalidGeometry)?;
        let gap_count =
            i64::try_from(selected.len() - 1).map_err(|_| ObjectCompositionError::InputLimit)?;
        let base_gap = total_gap.div_euclid(gap_count);
        let remainder = usize::try_from(total_gap.rem_euclid(gap_count))
            .map_err(|_| ObjectCompositionError::InvalidGeometry)?;
        let mut cursor = first_start;
        for (index, object) in selected.iter().enumerate() {
            if index > 0 {
                let previous = selected[index - 1].bounds;
                cursor = cursor
                    .checked_add(axis_extent(previous, axis)?)
                    .and_then(|value| value.checked_add(base_gap))
                    .and_then(|value| value.checked_add(i64::from(index <= remainder)))
                    .ok_or(ObjectCompositionError::InvalidGeometry)?;
            }
            if index + 1 == selected.len() {
                cursor = axis_start(object.bounds, axis);
            }
            let delta = cursor
                .checked_sub(axis_start(object.bounds, axis))
                .ok_or(ObjectCompositionError::InvalidGeometry)?;
            let (dx, dy) = match axis {
                CompositionAxis::Horizontal => (delta, 0),
                CompositionAxis::Vertical => (0, delta),
            };
            translate_subtree(&mut self.objects, &object.object_id, dx, dy, limits)?;
        }
        Ok(())
    }

    fn apply_create_connector(
        &mut self,
        connector: &NewConnector,
        limits: ObjectCompositionLimits,
    ) -> Result<(), ObjectCompositionError> {
        validate_new_identity(
            &self.objects,
            &connector.object_id,
            connector.native_object_id,
            connector.native_instance_id,
            limits,
        )?;
        validate_content(&connector.content, limits)?;
        let mut order = sibling_ids(&self.objects, connector.parent_group_id.as_ref());
        let insertion = usize::try_from(connector.z_order)
            .map_err(|_| ObjectCompositionError::InvalidZOrder)?;
        if insertion > order.len() {
            return Err(ObjectCompositionError::InvalidZOrder);
        }
        order.insert(insertion, connector.object_id.clone());
        self.objects.push(CompositionObject {
            object_id: connector.object_id.clone(),
            native_object_id: connector.native_object_id,
            native_instance_id: connector.native_instance_id,
            kind: CompositionObjectKind::Connector,
            parent_group_id: connector.parent_group_id.clone(),
            z_order: connector.z_order,
            group_level: 0,
            bounds: connector_bounds(&connector.topology, limits)?,
            visible: connector.visible,
            printable: connector.printable,
            content: connector.content.clone(),
            connector: Some(connector.topology.clone()),
        });
        set_sibling_order(
            &mut self.objects,
            connector.parent_group_id.as_ref(),
            &order,
        )
    }

    fn apply_update_connector(
        &mut self,
        connector_id: &LogicalId,
        topology: &ConnectorTopology,
        limits: ObjectCompositionLimits,
    ) -> Result<(), ObjectCompositionError> {
        let bounds = connector_bounds(topology, limits)?;
        let connector = object_mut(&mut self.objects, connector_id)?;
        if connector.kind != CompositionObjectKind::Connector {
            return Err(ObjectCompositionError::InvalidOperation);
        }
        connector.bounds = bounds;
        connector.connector = Some(topology.clone());
        Ok(())
    }
}

impl fmt::Debug for ObjectCompositionGraph {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        let groups = self
            .objects
            .iter()
            .filter(|object| object.kind == CompositionObjectKind::Group)
            .count();
        let connectors = self
            .objects
            .iter()
            .filter(|object| object.kind == CompositionObjectKind::Connector)
            .count();
        formatter
            .debug_struct("ObjectCompositionGraph")
            .field("objects", &self.objects.len())
            .field("groups", &groups)
            .field("connectors", &connectors)
            .field("state", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct NewGroup {
    pub object_id: LogicalId,
    pub native_object_id: u32,
    pub native_instance_id: u32,
    pub visible: bool,
    pub printable: bool,
    pub content: CompositionObjectContent,
}

impl fmt::Debug for NewGroup {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("NewGroup")
            .field("identity", &"<redacted>")
            .field("visible", &self.visible)
            .field("printable", &self.printable)
            .field("content", &self.content)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct NewConnector {
    pub object_id: LogicalId,
    pub native_object_id: u32,
    pub native_instance_id: u32,
    pub parent_group_id: Option<LogicalId>,
    pub z_order: u32,
    pub visible: bool,
    pub printable: bool,
    pub content: CompositionObjectContent,
    pub topology: ConnectorTopology,
}

impl fmt::Debug for NewConnector {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("NewConnector")
            .field("identity", &"<redacted>")
            .field("z_order", &self.z_order)
            .field("visible", &self.visible)
            .field("printable", &self.printable)
            .field("topology", &self.topology)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ZOrderMove {
    BringToFront,
    SendToBack,
    ForwardOne,
    BackwardOne,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ObjectAlignMode {
    Left,
    HorizontalCenter,
    Right,
    Top,
    VerticalMiddle,
    Bottom,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CompositionAxis {
    Horizontal,
    Vertical,
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum ObjectCompositionOperation {
    Group {
        group: NewGroup,
        member_ids: Vec<LogicalId>,
    },
    Ungroup {
        group_id: LogicalId,
    },
    SetZOrder {
        object_id: LogicalId,
        movement: ZOrderMove,
    },
    Align {
        object_ids: Vec<LogicalId>,
        mode: ObjectAlignMode,
    },
    Distribute {
        object_ids: Vec<LogicalId>,
        axis: CompositionAxis,
    },
    CreateConnector {
        connector: NewConnector,
    },
    UpdateConnector {
        connector_id: LogicalId,
        topology: ConnectorTopology,
    },
}

impl ObjectCompositionOperation {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        match self {
            Self::Group { .. } => "obj.group",
            Self::Ungroup { .. } => "obj.ungroup",
            Self::SetZOrder { .. } => "obj.z_order",
            Self::Align { .. } => "obj.align",
            Self::Distribute { .. } => "obj.distribute",
            Self::CreateConnector { .. } | Self::UpdateConnector { .. } => "obj.connector",
        }
    }
}

impl fmt::Debug for ObjectCompositionOperation {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectCompositionOperation")
            .field("capability_id", &self.capability_id())
            .field("details", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ObjectCompositionRequestDraft {
    pub schema_version: String,
    pub request_id: LogicalId,
    pub expected_source_state_sha256: String,
    pub expected_document_flow_sha256: String,
    pub target_document_flow_sha256: String,
    pub operation: ObjectCompositionOperation,
}

impl fmt::Debug for ObjectCompositionRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectCompositionRequestDraft")
            .field("capability_id", &self.operation.capability_id())
            .field("identity", &"<redacted>")
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ObjectCompositionRequest {
    schema_version: &'static str,
    request_id: LogicalId,
    expected_source_state_sha256: String,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    operation: ObjectCompositionOperation,
}

impl ObjectCompositionRequest {
    /// Admits one exact state/flow-bound graph transition request.
    ///
    /// # Errors
    ///
    /// Rejects malformed bindings, graph drift and invalid/no-op operations.
    pub fn from_draft(
        draft: ObjectCompositionRequestDraft,
        source: &ObjectCompositionGraph,
        current_document_flow_sha256: &str,
        limits: ObjectCompositionLimits,
    ) -> Result<Self, ObjectCompositionError> {
        if draft.schema_version != OBJECT_COMPOSITION_SCHEMA_VERSION {
            return Err(ObjectCompositionError::UnsupportedVersion);
        }
        validate_id(&draft.request_id, limits)?;
        require_digest(&draft.expected_source_state_sha256)?;
        require_digest(&draft.expected_document_flow_sha256)?;
        require_digest(&draft.target_document_flow_sha256)?;
        require_digest(current_document_flow_sha256)?;
        if source.canonical_sha256(limits)? != draft.expected_source_state_sha256 {
            return Err(ObjectCompositionError::SourceStateDrift);
        }
        if draft.expected_document_flow_sha256 != current_document_flow_sha256 {
            return Err(ObjectCompositionError::DocumentFlowDrift);
        }
        let _ = source.apply(&draft.operation, limits)?;
        let request = Self {
            schema_version: OBJECT_COMPOSITION_SCHEMA_VERSION,
            request_id: draft.request_id,
            expected_source_state_sha256: draft.expected_source_state_sha256,
            expected_document_flow_sha256: draft.expected_document_flow_sha256,
            target_document_flow_sha256: draft.target_document_flow_sha256,
            operation: draft.operation,
        };
        let _ = request.canonical_json(limits)?;
        Ok(request)
    }

    /// Parses bounded duplicate-key-free strict JSON and validates the exact source.
    ///
    /// # Errors
    ///
    /// Rejects malformed, duplicate, unknown, oversized or stale requests.
    pub fn from_json(
        bytes: &[u8],
        source: &ObjectCompositionGraph,
        current_document_flow_sha256: &str,
        limits: ObjectCompositionLimits,
    ) -> Result<Self, ObjectCompositionError> {
        if bytes.is_empty() || bytes.len() > limits.0.input_bytes {
            return Err(ObjectCompositionError::InputLimit);
        }
        reject_duplicate_json_keys(bytes)?;
        let draft =
            serde_json::from_slice(bytes).map_err(|_| ObjectCompositionError::InvalidJson)?;
        Self::from_draft(draft, source, current_document_flow_sha256, limits)
    }

    #[must_use]
    pub const fn operation(&self) -> &ObjectCompositionOperation {
        &self.operation
    }

    #[must_use]
    pub fn expected_source_state_sha256(&self) -> &str {
        &self.expected_source_state_sha256
    }

    #[must_use]
    pub fn expected_document_flow_sha256(&self) -> &str {
        &self.expected_document_flow_sha256
    }

    #[must_use]
    pub fn target_document_flow_sha256(&self) -> &str {
        &self.target_document_flow_sha256
    }

    /// Emits the complete request as bounded compact deterministic JSON.
    ///
    /// # Errors
    ///
    /// Returns serialization or output-limit failures.
    pub fn canonical_json(
        &self,
        limits: ObjectCompositionLimits,
    ) -> Result<Vec<u8>, ObjectCompositionError> {
        serialize_bounded(self, limits)
    }
}

impl fmt::Debug for ObjectCompositionRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectCompositionRequest")
            .field("capability_id", &self.operation.capability_id())
            .field("identity", &"<redacted>")
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ObjectCompositionPlan {
    schema_version: &'static str,
    capability_id: &'static str,
    request_id: LogicalId,
    source_state_sha256: String,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    operation: ObjectCompositionOperation,
    target_state: ObjectCompositionGraph,
    target_state_sha256: String,
    request_sha256: String,
    plan_sha256: String,
}

impl ObjectCompositionPlan {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
    }

    #[must_use]
    pub const fn target_state(&self) -> &ObjectCompositionGraph {
        &self.target_state
    }

    #[must_use]
    pub fn plan_sha256(&self) -> &str {
        &self.plan_sha256
    }
}

impl fmt::Debug for ObjectCompositionPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectCompositionPlan")
            .field("capability_id", &self.capability_id)
            .field("objects", &self.target_state.objects.len())
            .field("identity", &"<redacted>")
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ObjectCompositionReceipt {
    schema_version: &'static str,
    capability_id: &'static str,
    source_state_sha256: String,
    target_state_sha256: String,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    plan_sha256: String,
}

impl fmt::Debug for ObjectCompositionReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectCompositionReceipt")
            .field("capability_id", &self.capability_id)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct ObjectCompositionResult {
    pub state: ObjectCompositionGraph,
    pub receipt: ObjectCompositionReceipt,
}

impl fmt::Debug for ObjectCompositionResult {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectCompositionResult")
            .field("objects", &self.state.objects.len())
            .field("receipt", &self.receipt)
            .field("state", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct ObjectCompositionBuilder;

impl ObjectCompositionBuilder {
    /// Produces a deterministic exact target graph and sealed plan.
    ///
    /// # Errors
    ///
    /// Rejects source/flow drift and every graph-invariant violation.
    pub fn plan(
        source: &ObjectCompositionGraph,
        request: &ObjectCompositionRequest,
        current_document_flow_sha256: &str,
        limits: ObjectCompositionLimits,
    ) -> Result<ObjectCompositionPlan, ObjectCompositionError> {
        require_digest(current_document_flow_sha256)?;
        let source_state_sha256 = source.canonical_sha256(limits)?;
        if source_state_sha256 != request.expected_source_state_sha256 {
            return Err(ObjectCompositionError::SourceStateDrift);
        }
        if current_document_flow_sha256 != request.expected_document_flow_sha256 {
            return Err(ObjectCompositionError::DocumentFlowDrift);
        }
        let target_state = source.apply(&request.operation, limits)?;
        let target_state_sha256 = target_state.canonical_sha256(limits)?;
        let request_sha256 = hex(Sha256::digest(request.canonical_json(limits)?).into());
        let mut plan = ObjectCompositionPlan {
            schema_version: OBJECT_COMPOSITION_SCHEMA_VERSION,
            capability_id: request.operation.capability_id(),
            request_id: request.request_id.clone(),
            source_state_sha256,
            source_document_flow_sha256: request.expected_document_flow_sha256.clone(),
            target_document_flow_sha256: request.target_document_flow_sha256.clone(),
            operation: request.operation.clone(),
            target_state,
            target_state_sha256,
            request_sha256,
            plan_sha256: String::new(),
        };
        plan.plan_sha256 = plan_digest(&plan, limits)?;
        let _ = serialize_bounded(&plan, limits)?;
        Ok(plan)
    }

    /// Revalidates the current graph, flow, target and sealed plan before publishing.
    ///
    /// # Errors
    ///
    /// Rejects plan tampering, current drift or a non-reproducible target transition.
    pub fn build(
        plan: &ObjectCompositionPlan,
        current: &ObjectCompositionGraph,
        current_document_flow_sha256: &str,
        limits: ObjectCompositionLimits,
    ) -> Result<ObjectCompositionResult, ObjectCompositionError> {
        require_digest(current_document_flow_sha256)?;
        if plan.schema_version != OBJECT_COMPOSITION_SCHEMA_VERSION
            || plan.capability_id != plan.operation.capability_id()
            || plan_digest(plan, limits)? != plan.plan_sha256
        {
            return Err(ObjectCompositionError::PlanTampered);
        }
        let source_state_sha256 = current.canonical_sha256(limits)?;
        if source_state_sha256 != plan.source_state_sha256 {
            return Err(ObjectCompositionError::SourceStateDrift);
        }
        if current_document_flow_sha256 != plan.source_document_flow_sha256 {
            return Err(ObjectCompositionError::DocumentFlowDrift);
        }
        let rebuilt = current.apply(&plan.operation, limits)?;
        let rebuilt_sha256 = rebuilt.canonical_sha256(limits)?;
        if rebuilt != plan.target_state || rebuilt_sha256 != plan.target_state_sha256 {
            return Err(ObjectCompositionError::PlanTampered);
        }
        Ok(ObjectCompositionResult {
            state: rebuilt,
            receipt: ObjectCompositionReceipt {
                schema_version: OBJECT_COMPOSITION_SCHEMA_VERSION,
                capability_id: plan.capability_id,
                source_state_sha256,
                target_state_sha256: rebuilt_sha256,
                source_document_flow_sha256: plan.source_document_flow_sha256.clone(),
                target_document_flow_sha256: plan.target_document_flow_sha256.clone(),
                plan_sha256: plan.plan_sha256.clone(),
            },
        })
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum ObjectCompositionError {
    #[error("object composition limits are invalid")]
    InvalidLimit,
    #[error("object composition input exceeds a finite limit")]
    InputLimit,
    #[error("object composition output exceeds a finite limit")]
    OutputLimit,
    #[error("object composition JSON is malformed or not strict")]
    InvalidJson,
    #[error("object composition schema version is unsupported")]
    UnsupportedVersion,
    #[error("object composition digest is malformed")]
    InvalidDigest,
    #[error("object composition graph is invalid")]
    InvalidGraph,
    #[error("object composition identity is duplicated or invalid")]
    DuplicateIdentity,
    #[error("object composition object was not found")]
    ObjectNotFound,
    #[error("object composition containment is invalid")]
    InvalidContainment,
    #[error("object composition edge is dangling")]
    DanglingEdge,
    #[error("object composition sibling z-order is invalid")]
    InvalidZOrder,
    #[error("object composition group bounds are invalid")]
    InvalidGroupBounds,
    #[error("object composition geometry is invalid")]
    InvalidGeometry,
    #[error("object composition content binding is invalid")]
    InvalidContent,
    #[error("object composition connector is invalid")]
    InvalidConnector,
    #[error("object composition selection is invalid")]
    InvalidSelection,
    #[error("object composition selection contains mixed parents")]
    MixedParents,
    #[error("object composition operation is invalid for the selected object")]
    InvalidOperation,
    #[error("object composition operation would not change state")]
    NoChange,
    #[error("object composition source state drifted")]
    SourceStateDrift,
    #[error("object composition document flow drifted")]
    DocumentFlowDrift,
    #[error("object composition plan was tampered with")]
    PlanTampered,
    #[error("object composition serialization failed")]
    Serialization,
}

impl ObjectCompositionError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "object_composition_invalid_limit",
            Self::InputLimit => "object_composition_input_limit",
            Self::OutputLimit => "object_composition_output_limit",
            Self::InvalidJson => "object_composition_invalid_json",
            Self::UnsupportedVersion => "object_composition_unsupported_version",
            Self::InvalidDigest => "object_composition_invalid_digest",
            Self::InvalidGraph => "object_composition_invalid_graph",
            Self::DuplicateIdentity => "object_composition_duplicate_identity",
            Self::ObjectNotFound => "object_composition_object_not_found",
            Self::InvalidContainment => "object_composition_invalid_containment",
            Self::DanglingEdge => "object_composition_dangling_edge",
            Self::InvalidZOrder => "object_composition_invalid_z_order",
            Self::InvalidGroupBounds => "object_composition_invalid_group_bounds",
            Self::InvalidGeometry => "object_composition_invalid_geometry",
            Self::InvalidContent => "object_composition_invalid_content",
            Self::InvalidConnector => "object_composition_invalid_connector",
            Self::InvalidSelection => "object_composition_invalid_selection",
            Self::MixedParents => "object_composition_mixed_parents",
            Self::InvalidOperation => "object_composition_invalid_operation",
            Self::NoChange => "object_composition_no_change",
            Self::SourceStateDrift => "object_composition_source_state_drift",
            Self::DocumentFlowDrift => "object_composition_document_flow_drift",
            Self::PlanTampered => "object_composition_plan_tampered",
            Self::Serialization => "object_composition_serialization",
        }
    }
}

fn validate_id(
    id: &LogicalId,
    limits: ObjectCompositionLimits,
) -> Result<(), ObjectCompositionError> {
    if id.as_str().is_empty() || id.as_str().len() > limits.0.identifier_bytes {
        return Err(ObjectCompositionError::DuplicateIdentity);
    }
    Ok(())
}

fn validate_content(
    content: &CompositionObjectContent,
    limits: ObjectCompositionLimits,
) -> Result<(), ObjectCompositionError> {
    require_digest(&content.state_sha256)?;
    if content.byte_length > limits.0.content_bytes
        || content.resource_refs.len() > limits.0.resources_per_object
    {
        return Err(ObjectCompositionError::InvalidContent);
    }
    let mut previous: Option<&LogicalId> = None;
    for resource in &content.resource_refs {
        validate_id(resource, limits)?;
        if previous.is_some_and(|value| value >= resource) {
            return Err(ObjectCompositionError::InvalidContent);
        }
        previous = Some(resource);
    }
    Ok(())
}

fn validate_bounds(
    bounds: CompositionBounds,
    kind: CompositionObjectKind,
    limits: ObjectCompositionLimits,
) -> Result<(), ObjectCompositionError> {
    if bounds
        .x_hwpunit
        .checked_abs()
        .is_none_or(|value| value > limits.0.coordinate_magnitude_hwpunit)
        || bounds
            .y_hwpunit
            .checked_abs()
            .is_none_or(|value| value > limits.0.coordinate_magnitude_hwpunit)
        || bounds.width_hwpunit
            > u64::try_from(limits.0.coordinate_magnitude_hwpunit).unwrap_or(u64::MAX)
        || bounds.height_hwpunit
            > u64::try_from(limits.0.coordinate_magnitude_hwpunit).unwrap_or(u64::MAX)
        || (kind == CompositionObjectKind::Connector
            && bounds.width_hwpunit == 0
            && bounds.height_hwpunit == 0)
        || (kind != CompositionObjectKind::Connector
            && (bounds.width_hwpunit == 0 || bounds.height_hwpunit == 0))
    {
        return Err(ObjectCompositionError::InvalidGeometry);
    }
    let right = bounds.right()?;
    let bottom = bounds.bottom()?;
    if right
        .checked_abs()
        .is_none_or(|value| value > limits.0.coordinate_magnitude_hwpunit)
        || bottom
            .checked_abs()
            .is_none_or(|value| value > limits.0.coordinate_magnitude_hwpunit)
    {
        return Err(ObjectCompositionError::InvalidGeometry);
    }
    Ok(())
}

fn depth_of(
    object: &CompositionObject,
    index: &BTreeMap<LogicalId, &CompositionObject>,
    limits: ObjectCompositionLimits,
) -> Result<usize, ObjectCompositionError> {
    let mut seen = BTreeSet::new();
    let mut parent = object.parent_group_id.as_ref();
    let mut depth = 0_usize;
    while let Some(id) = parent {
        if !seen.insert(id) {
            return Err(ObjectCompositionError::InvalidContainment);
        }
        depth = depth
            .checked_add(1)
            .ok_or(ObjectCompositionError::InputLimit)?;
        if depth > limits.0.depth {
            return Err(ObjectCompositionError::InvalidContainment);
        }
        parent = index
            .get(id)
            .ok_or(ObjectCompositionError::DanglingEdge)?
            .parent_group_id
            .as_ref();
    }
    Ok(depth)
}

fn union_bounds<'a>(
    objects: impl IntoIterator<Item = &'a CompositionObject>,
    limits: ObjectCompositionLimits,
) -> Result<CompositionBounds, ObjectCompositionError> {
    let mut values = objects.into_iter();
    let first = values
        .next()
        .ok_or(ObjectCompositionError::InvalidSelection)?;
    let mut left = first.bounds.x_hwpunit;
    let mut top = first.bounds.y_hwpunit;
    let mut right = first.bounds.right()?;
    let mut bottom = first.bounds.bottom()?;
    for object in values {
        left = left.min(object.bounds.x_hwpunit);
        top = top.min(object.bounds.y_hwpunit);
        right = right.max(object.bounds.right()?);
        bottom = bottom.max(object.bounds.bottom()?);
    }
    let bounds = CompositionBounds {
        x_hwpunit: left,
        y_hwpunit: top,
        width_hwpunit: u64::try_from(
            right
                .checked_sub(left)
                .ok_or(ObjectCompositionError::InvalidGeometry)?,
        )
        .map_err(|_| ObjectCompositionError::InvalidGeometry)?,
        height_hwpunit: u64::try_from(
            bottom
                .checked_sub(top)
                .ok_or(ObjectCompositionError::InvalidGeometry)?,
        )
        .map_err(|_| ObjectCompositionError::InvalidGeometry)?,
    };
    validate_bounds(bounds, CompositionObjectKind::Group, limits)?;
    Ok(bounds)
}

fn validate_connector(
    owner: &CompositionObject,
    topology: &ConnectorTopology,
    index: &BTreeMap<LogicalId, &CompositionObject>,
    limits: ObjectCompositionLimits,
) -> Result<(), ObjectCompositionError> {
    if topology.control_points.len() > limits.0.control_points
        || connector_bounds(topology, limits)? != owner.bounds
    {
        return Err(ObjectCompositionError::InvalidConnector);
    }
    for endpoint in [&topology.start, &topology.end] {
        validate_point(endpoint.x_hwpunit, endpoint.y_hwpunit, limits)?;
        if let Some(subject) = &endpoint.subject {
            validate_id(&subject.object_id, limits)?;
            if subject.object_id == owner.object_id
                || subject.connection_index > limits.0.connection_index
            {
                return Err(ObjectCompositionError::InvalidConnector);
            }
            let subject_object = index
                .get(&subject.object_id)
                .ok_or(ObjectCompositionError::DanglingEdge)?;
            if subject_object.kind == CompositionObjectKind::Connector
                || subject_object.parent_group_id != owner.parent_group_id
                || endpoint.x_hwpunit < subject_object.bounds.x_hwpunit
                || endpoint.x_hwpunit > subject_object.bounds.right()?
                || endpoint.y_hwpunit < subject_object.bounds.y_hwpunit
                || endpoint.y_hwpunit > subject_object.bounds.bottom()?
            {
                return Err(ObjectCompositionError::InvalidConnector);
            }
        }
    }
    for point in &topology.control_points {
        validate_point(point.x_hwpunit, point.y_hwpunit, limits)?;
    }
    Ok(())
}

fn connector_bounds(
    topology: &ConnectorTopology,
    limits: ObjectCompositionLimits,
) -> Result<CompositionBounds, ObjectCompositionError> {
    let mut left = topology.start.x_hwpunit.min(topology.end.x_hwpunit);
    let mut right = topology.start.x_hwpunit.max(topology.end.x_hwpunit);
    let mut top = topology.start.y_hwpunit.min(topology.end.y_hwpunit);
    let mut bottom = topology.start.y_hwpunit.max(topology.end.y_hwpunit);
    if topology.control_points.len() > limits.0.control_points {
        return Err(ObjectCompositionError::InputLimit);
    }
    for point in &topology.control_points {
        left = left.min(point.x_hwpunit);
        right = right.max(point.x_hwpunit);
        top = top.min(point.y_hwpunit);
        bottom = bottom.max(point.y_hwpunit);
    }
    let bounds = CompositionBounds {
        x_hwpunit: left,
        y_hwpunit: top,
        width_hwpunit: u64::try_from(
            right
                .checked_sub(left)
                .ok_or(ObjectCompositionError::InvalidGeometry)?,
        )
        .map_err(|_| ObjectCompositionError::InvalidGeometry)?,
        height_hwpunit: u64::try_from(
            bottom
                .checked_sub(top)
                .ok_or(ObjectCompositionError::InvalidGeometry)?,
        )
        .map_err(|_| ObjectCompositionError::InvalidGeometry)?,
    };
    validate_bounds(bounds, CompositionObjectKind::Connector, limits)?;
    Ok(bounds)
}

fn validate_point(
    x: i64,
    y: i64,
    limits: ObjectCompositionLimits,
) -> Result<(), ObjectCompositionError> {
    if x.checked_abs()
        .is_none_or(|value| value > limits.0.coordinate_magnitude_hwpunit)
        || y.checked_abs()
            .is_none_or(|value| value > limits.0.coordinate_magnitude_hwpunit)
    {
        return Err(ObjectCompositionError::InvalidGeometry);
    }
    Ok(())
}

fn validate_selection(
    ids: &[LogicalId],
    minimum: usize,
    limits: ObjectCompositionLimits,
) -> Result<(), ObjectCompositionError> {
    if ids.len() < minimum || ids.len() > limits.0.selection {
        return Err(ObjectCompositionError::InvalidSelection);
    }
    let mut unique = BTreeSet::new();
    for id in ids {
        validate_id(id, limits)?;
        if !unique.insert(id) {
            return Err(ObjectCompositionError::InvalidSelection);
        }
    }
    Ok(())
}

fn selected_objects(
    objects: &[CompositionObject],
    ids: &[LogicalId],
    minimum: usize,
    limits: ObjectCompositionLimits,
) -> Result<Vec<CompositionObject>, ObjectCompositionError> {
    validate_selection(ids, minimum, limits)?;
    let selected: BTreeSet<_> = ids.iter().collect();
    let values: Vec<_> = objects
        .iter()
        .filter(|object| selected.contains(&object.object_id))
        .cloned()
        .collect();
    if values.len() != ids.len() {
        return Err(ObjectCompositionError::ObjectNotFound);
    }
    Ok(values)
}

fn require_movable_siblings(objects: &[CompositionObject]) -> Result<(), ObjectCompositionError> {
    let parent = objects[0].parent_group_id.as_ref();
    if objects
        .iter()
        .any(|object| object.parent_group_id.as_ref() != parent)
    {
        return Err(ObjectCompositionError::MixedParents);
    }
    if objects
        .iter()
        .any(|object| object.kind == CompositionObjectKind::Connector)
    {
        return Err(ObjectCompositionError::InvalidOperation);
    }
    Ok(())
}

fn sibling_ids(objects: &[CompositionObject], parent: Option<&LogicalId>) -> Vec<LogicalId> {
    let mut siblings: Vec<_> = objects
        .iter()
        .filter(|object| object.parent_group_id.as_ref() == parent)
        .collect();
    siblings.sort_by_key(|object| object.z_order);
    siblings
        .into_iter()
        .map(|object| object.object_id.clone())
        .collect()
}

fn set_sibling_order(
    objects: &mut [CompositionObject],
    parent: Option<&LogicalId>,
    order: &[LogicalId],
) -> Result<(), ObjectCompositionError> {
    let expected: BTreeSet<_> = objects
        .iter()
        .filter(|object| object.parent_group_id.as_ref() == parent)
        .map(|object| object.object_id.clone())
        .collect();
    if expected != order.iter().cloned().collect() || expected.len() != order.len() {
        return Err(ObjectCompositionError::InvalidZOrder);
    }
    for (z_order, id) in order.iter().enumerate() {
        object_mut(objects, id)?.z_order =
            u32::try_from(z_order).map_err(|_| ObjectCompositionError::InputLimit)?;
    }
    Ok(())
}

fn object_mut<'a>(
    objects: &'a mut [CompositionObject],
    id: &LogicalId,
) -> Result<&'a mut CompositionObject, ObjectCompositionError> {
    objects
        .iter_mut()
        .find(|object| &object.object_id == id)
        .ok_or(ObjectCompositionError::ObjectNotFound)
}

fn validate_new_identity(
    objects: &[CompositionObject],
    object_id: &LogicalId,
    native_object_id: u32,
    native_instance_id: u32,
    limits: ObjectCompositionLimits,
) -> Result<(), ObjectCompositionError> {
    validate_id(object_id, limits)?;
    if native_object_id == 0
        || native_instance_id == 0
        || objects.iter().any(|object| {
            &object.object_id == object_id
                || object.native_object_id == native_object_id
                || object.native_instance_id == native_instance_id
        })
        || objects.len() >= limits.0.objects
    {
        return Err(ObjectCompositionError::DuplicateIdentity);
    }
    Ok(())
}

fn recompute_levels(
    objects: &mut [CompositionObject],
    limits: ObjectCompositionLimits,
) -> Result<(), ObjectCompositionError> {
    let snapshot = objects.to_vec();
    let index: BTreeMap<_, _> = snapshot
        .iter()
        .map(|object| (object.object_id.clone(), object))
        .collect();
    for object in objects {
        let source = index
            .get(&object.object_id)
            .ok_or(ObjectCompositionError::ObjectNotFound)?;
        object.group_level = u32::try_from(depth_of(source, &index, limits)?)
            .map_err(|_| ObjectCompositionError::InvalidContainment)?;
    }
    Ok(())
}

fn recompute_group_bounds(
    objects: &mut [CompositionObject],
    limits: ObjectCompositionLimits,
) -> Result<(), ObjectCompositionError> {
    let max_depth = objects
        .iter()
        .map(|object| object.group_level)
        .max()
        .unwrap_or(0);
    for depth in (0..=max_depth).rev() {
        let group_ids: Vec<_> = objects
            .iter()
            .filter(|object| {
                object.kind == CompositionObjectKind::Group && object.group_level == depth
            })
            .map(|object| object.object_id.clone())
            .collect();
        for group_id in group_ids {
            let children: Vec<_> = objects
                .iter()
                .filter(|object| object.parent_group_id.as_ref() == Some(&group_id))
                .cloned()
                .collect();
            let bounds = union_bounds(children.iter(), limits)?;
            object_mut(objects, &group_id)?.bounds = bounds;
        }
    }
    Ok(())
}

fn translate_subtree(
    objects: &mut [CompositionObject],
    root: &LogicalId,
    dx: i64,
    dy: i64,
    limits: ObjectCompositionLimits,
) -> Result<(), ObjectCompositionError> {
    if dx == 0 && dy == 0 {
        return Ok(());
    }
    let mut move_ids = BTreeSet::new();
    move_ids.insert(root.clone());
    for _ in 0..limits.0.depth {
        let before = move_ids.len();
        for object in objects.iter() {
            if object
                .parent_group_id
                .as_ref()
                .is_some_and(|parent| move_ids.contains(parent))
            {
                move_ids.insert(object.object_id.clone());
            }
        }
        if move_ids.len() == before {
            break;
        }
    }
    for object in objects
        .iter_mut()
        .filter(|object| move_ids.contains(&object.object_id))
    {
        object.bounds.x_hwpunit = object
            .bounds
            .x_hwpunit
            .checked_add(dx)
            .ok_or(ObjectCompositionError::InvalidGeometry)?;
        object.bounds.y_hwpunit = object
            .bounds
            .y_hwpunit
            .checked_add(dy)
            .ok_or(ObjectCompositionError::InvalidGeometry)?;
        if let Some(connector) = object.connector.as_mut() {
            connector.start.x_hwpunit = connector
                .start
                .x_hwpunit
                .checked_add(dx)
                .ok_or(ObjectCompositionError::InvalidGeometry)?;
            connector.start.y_hwpunit = connector
                .start
                .y_hwpunit
                .checked_add(dy)
                .ok_or(ObjectCompositionError::InvalidGeometry)?;
            connector.end.x_hwpunit = connector
                .end
                .x_hwpunit
                .checked_add(dx)
                .ok_or(ObjectCompositionError::InvalidGeometry)?;
            connector.end.y_hwpunit = connector
                .end
                .y_hwpunit
                .checked_add(dy)
                .ok_or(ObjectCompositionError::InvalidGeometry)?;
            for point in &mut connector.control_points {
                point.x_hwpunit = point
                    .x_hwpunit
                    .checked_add(dx)
                    .ok_or(ObjectCompositionError::InvalidGeometry)?;
                point.y_hwpunit = point
                    .y_hwpunit
                    .checked_add(dy)
                    .ok_or(ObjectCompositionError::InvalidGeometry)?;
            }
        }
        validate_bounds(object.bounds, object.kind, limits)?;
    }
    Ok(())
}

fn centered_start(
    envelope_start: i64,
    envelope_extent: u64,
    object_extent: u64,
) -> Result<i64, ObjectCompositionError> {
    let difference = i128::from(envelope_extent) - i128::from(object_extent);
    let offset = difference.div_euclid(2);
    i64::try_from(i128::from(envelope_start) + offset)
        .map_err(|_| ObjectCompositionError::InvalidGeometry)
}

fn axis_start(bounds: CompositionBounds, axis: CompositionAxis) -> i64 {
    match axis {
        CompositionAxis::Horizontal => bounds.x_hwpunit,
        CompositionAxis::Vertical => bounds.y_hwpunit,
    }
}

fn axis_extent(
    bounds: CompositionBounds,
    axis: CompositionAxis,
) -> Result<i64, ObjectCompositionError> {
    i64::try_from(match axis {
        CompositionAxis::Horizontal => bounds.width_hwpunit,
        CompositionAxis::Vertical => bounds.height_hwpunit,
    })
    .map_err(|_| ObjectCompositionError::InvalidGeometry)
}

fn axis_end(
    bounds: CompositionBounds,
    axis: CompositionAxis,
) -> Result<i64, ObjectCompositionError> {
    match axis {
        CompositionAxis::Horizontal => bounds.right(),
        CompositionAxis::Vertical => bounds.bottom(),
    }
}

fn plan_digest(
    plan: &ObjectCompositionPlan,
    limits: ObjectCompositionLimits,
) -> Result<String, ObjectCompositionError> {
    #[derive(Serialize)]
    struct Binding<'a> {
        schema_version: &'static str,
        capability_id: &'static str,
        request_id: &'a LogicalId,
        source_state_sha256: &'a str,
        source_document_flow_sha256: &'a str,
        target_document_flow_sha256: &'a str,
        operation: &'a ObjectCompositionOperation,
        target_state_sha256: &'a str,
        request_sha256: &'a str,
    }
    let binding = Binding {
        schema_version: OBJECT_COMPOSITION_SCHEMA_VERSION,
        capability_id: plan.capability_id,
        request_id: &plan.request_id,
        source_state_sha256: &plan.source_state_sha256,
        source_document_flow_sha256: &plan.source_document_flow_sha256,
        target_document_flow_sha256: &plan.target_document_flow_sha256,
        operation: &plan.operation,
        target_state_sha256: &plan.target_state_sha256,
        request_sha256: &plan.request_sha256,
    };
    Ok(hex(
        Sha256::digest(serialize_bounded(&binding, limits)?).into()
    ))
}

fn require_digest(value: &str) -> Result<(), ObjectCompositionError> {
    if value.len() != 64
        || value
            .bytes()
            .any(|byte| !matches!(byte, b'0'..=b'9' | b'a'..=b'f'))
    {
        return Err(ObjectCompositionError::InvalidDigest);
    }
    Ok(())
}

fn serialize_bounded<T: Serialize>(
    value: &T,
    limits: ObjectCompositionLimits,
) -> Result<Vec<u8>, ObjectCompositionError> {
    let bytes = serde_json::to_vec(value).map_err(|_| ObjectCompositionError::Serialization)?;
    if bytes.len() > limits.0.serialized_bytes {
        return Err(ObjectCompositionError::OutputLimit);
    }
    Ok(bytes)
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

#[allow(clippy::too_many_lines)]
fn reject_duplicate_json_keys(bytes: &[u8]) -> Result<(), ObjectCompositionError> {
    struct RootVisitor;
    struct AnyVisitor;
    struct Seed;

    impl<'de> serde::de::DeserializeSeed<'de> for Seed {
        type Value = ();

        fn deserialize<D>(self, deserializer: D) -> Result<Self::Value, D::Error>
        where
            D: serde::Deserializer<'de>,
        {
            deserializer.deserialize_any(AnyVisitor)
        }
    }

    fn visit_map<'de, A>(mut map: A) -> Result<(), A::Error>
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

    impl<'de> serde::de::Visitor<'de> for RootVisitor {
        type Value = ();

        fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
            formatter.write_str("JSON object without duplicate keys")
        }

        fn visit_map<A>(self, map: A) -> Result<Self::Value, A::Error>
        where
            A: serde::de::MapAccess<'de>,
        {
            visit_map(map)
        }
    }

    impl<'de> serde::de::Visitor<'de> for AnyVisitor {
        type Value = ();

        fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
            formatter.write_str("any JSON value")
        }

        fn visit_map<A>(self, map: A) -> Result<Self::Value, A::Error>
        where
            A: serde::de::MapAccess<'de>,
        {
            visit_map(map)
        }

        fn visit_seq<A>(self, mut sequence: A) -> Result<Self::Value, A::Error>
        where
            A: serde::de::SeqAccess<'de>,
        {
            while sequence.next_element_seed(Seed)?.is_some() {}
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

        fn visit_none<E>(self) -> Result<Self::Value, E> {
            Ok(())
        }

        fn visit_unit<E>(self) -> Result<Self::Value, E> {
            Ok(())
        }
    }

    let mut deserializer = serde_json::Deserializer::from_slice(bytes);
    serde::de::Deserializer::deserialize_map(&mut deserializer, RootVisitor)
        .map_err(|_| ObjectCompositionError::InvalidJson)?;
    deserializer
        .end()
        .map_err(|_| ObjectCompositionError::InvalidJson)
}

#[cfg(test)]
#[allow(clippy::expect_used)] // Test setup uses expectations only to isolate private-plan tampering.
mod tests {
    use super::*;

    #[test]
    fn private_plan_tampering_is_rejected() {
        let limits =
            ObjectCompositionLimits::new(ObjectCompositionLimitConfig::default()).expect("limits");
        let source = ObjectCompositionGraph::from_draft(
            ObjectCompositionGraphDraft {
                schema_version: OBJECT_COMPOSITION_SCHEMA_VERSION.to_owned(),
                objects: vec![
                    sample_object("a", 1, 11, 0, 0),
                    sample_object("b", 2, 12, 1, 20),
                    sample_object("c", 3, 13, 2, 40),
                ],
            },
            limits,
        )
        .expect("source");
        let digest = source.canonical_sha256(limits).expect("digest");
        let request = ObjectCompositionRequest::from_draft(
            ObjectCompositionRequestDraft {
                schema_version: OBJECT_COMPOSITION_SCHEMA_VERSION.to_owned(),
                request_id: LogicalId::parse("request").expect("request id"),
                expected_source_state_sha256: digest,
                expected_document_flow_sha256: "1".repeat(64),
                target_document_flow_sha256: "2".repeat(64),
                operation: ObjectCompositionOperation::SetZOrder {
                    object_id: LogicalId::parse("a").expect("object id"),
                    movement: ZOrderMove::BringToFront,
                },
            },
            &source,
            &"1".repeat(64),
            limits,
        )
        .expect("request");
        let mut plan = ObjectCompositionBuilder::plan(&source, &request, &"1".repeat(64), limits)
            .expect("plan");
        plan.target_state_sha256 = "f".repeat(64);
        assert_eq!(
            ObjectCompositionBuilder::build(&plan, &source, &"1".repeat(64), limits),
            Err(ObjectCompositionError::PlanTampered)
        );
    }

    fn sample_object(
        name: &str,
        native: u32,
        instance: u32,
        z_order: u32,
        x: i64,
    ) -> CompositionObject {
        CompositionObject {
            object_id: LogicalId::parse(name).expect("id"),
            native_object_id: native,
            native_instance_id: instance,
            kind: CompositionObjectKind::BasicShape,
            parent_group_id: None,
            z_order,
            group_level: 0,
            bounds: CompositionBounds {
                x_hwpunit: x,
                y_hwpunit: 0,
                width_hwpunit: 10,
                height_hwpunit: 10,
            },
            visible: true,
            printable: true,
            content: CompositionObjectContent {
                state_sha256: format!("{native:064x}"),
                byte_length: 10,
                resource_refs: Vec::new(),
            },
            connector: None,
        }
    }
}
