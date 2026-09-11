use std::collections::BTreeSet;
use std::fmt;

use serde::de::{self, MapAccess, Visitor};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{
    BasicShape, BasicShapeLimits, FreeformShape, LogicalId, ObjectGeometryLimits,
    ObjectGeometryState, ObjectGeometryStateDraft,
};

pub const SHAPE_POINTS_SCHEMA_VERSION: &str = "hwpx-agent.shape-points/v1";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ShapePointsLimitConfig {
    pub input_bytes: usize,
    pub output_bytes: usize,
}

impl Default for ShapePointsLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 512 * 1024,
            output_bytes: 512 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ShapePointsLimits(ShapePointsLimitConfig);

impl ShapePointsLimits {
    pub const HARD_MAX_BYTES: usize = 4 * 1024 * 1024;

    /// Creates finite JSON limits without silently clamping caller values.
    ///
    /// # Errors
    ///
    /// Rejects zero, inconsistent or hard-ceiling-exceeding values.
    pub fn new(config: ShapePointsLimitConfig) -> Result<Self, ShapePointsError> {
        if config.input_bytes == 0
            || config.output_bytes == 0
            || config.input_bytes > config.output_bytes
            || config.output_bytes > Self::HARD_MAX_BYTES
        {
            return Err(ShapePointsError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> ShapePointsLimitConfig {
        self.0
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ShapePointsStateDraft {
    pub schema_version: String,
    pub geometry: ObjectGeometryStateDraft,
    pub freeform: FreeformShape,
    pub appearance_state_sha256: String,
    pub property_state_sha256: String,
    pub resource_inventory_sha256: String,
    pub embedded_content_state_sha256: String,
    pub opaque_state_sha256: String,
}

impl fmt::Debug for ShapePointsStateDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ShapePointsStateDraft")
            .field("state", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ShapePointsState {
    schema_version: &'static str,
    geometry: ObjectGeometryState,
    freeform: FreeformShape,
    appearance_state_sha256: String,
    property_state_sha256: String,
    resource_inventory_sha256: String,
    embedded_content_state_sha256: String,
    opaque_state_sha256: String,
}

impl ShapePointsState {
    /// Validates and seals the complete editable freeform object state.
    ///
    /// # Errors
    ///
    /// Rejects schema, geometry, topology, digest or output drift.
    pub fn from_draft(
        draft: ShapePointsStateDraft,
        geometry_limits: ObjectGeometryLimits,
        shape_limits: BasicShapeLimits,
        limits: ShapePointsLimits,
    ) -> Result<Self, ShapePointsError> {
        if draft.schema_version != SHAPE_POINTS_SCHEMA_VERSION {
            return Err(ShapePointsError::UnsupportedVersion);
        }
        let geometry = ObjectGeometryState::from_draft(draft.geometry, geometry_limits)
            .map_err(|_| ShapePointsError::GeometryStateInvalid)?;
        for digest in [
            &draft.appearance_state_sha256,
            &draft.property_state_sha256,
            &draft.resource_inventory_sha256,
            &draft.embedded_content_state_sha256,
            &draft.opaque_state_sha256,
        ] {
            require_digest(digest)?;
        }
        validate_freeform(&draft.freeform, &geometry, shape_limits)?;
        let state = Self {
            schema_version: SHAPE_POINTS_SCHEMA_VERSION,
            geometry,
            freeform: draft.freeform,
            appearance_state_sha256: draft.appearance_state_sha256,
            property_state_sha256: draft.property_state_sha256,
            resource_inventory_sha256: draft.resource_inventory_sha256,
            embedded_content_state_sha256: draft.embedded_content_state_sha256,
            opaque_state_sha256: draft.opaque_state_sha256,
        };
        let _ = state.canonical_json(limits)?;
        Ok(state)
    }

    #[must_use]
    pub const fn geometry(&self) -> &ObjectGeometryState {
        &self.geometry
    }

    #[must_use]
    pub const fn freeform(&self) -> &FreeformShape {
        &self.freeform
    }

    /// Serializes the complete state deterministically within the configured bound.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit error.
    pub fn canonical_json(&self, limits: ShapePointsLimits) -> Result<Vec<u8>, ShapePointsError> {
        serialize_bounded(self, limits)
    }

    /// Returns the SHA-256 of the complete canonical state.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit error.
    pub fn canonical_sha256(&self, limits: ShapePointsLimits) -> Result<String, ShapePointsError> {
        Ok(hex(Sha256::digest(self.canonical_json(limits)?).into()))
    }
}

impl fmt::Debug for ShapePointsState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ShapePointsState")
            .field("object_kind", &self.geometry.object_kind())
            .field("identity", &"<redacted>")
            .field("path", &"<redacted>")
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ShapePointsRequestDraft {
    pub schema_version: String,
    pub request_id: LogicalId,
    pub expected_source_state_sha256: String,
    pub expected_document_flow_sha256: String,
    pub target_document_flow_sha256: String,
    pub target_freeform: FreeformShape,
}

impl fmt::Debug for ShapePointsRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ShapePointsRequestDraft")
            .field("capability_id", &"obj.shape_edit_points")
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ShapePointsRequest {
    schema_version: &'static str,
    request_id: LogicalId,
    expected_source_state_sha256: String,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    target_freeform: FreeformShape,
}

impl ShapePointsRequest {
    /// Validates an exact path edit against current object state and document flow.
    ///
    /// # Errors
    ///
    /// Rejects version, state, flow, topology, no-op or output drift.
    pub fn from_draft(
        draft: ShapePointsRequestDraft,
        current: &ShapePointsState,
        current_document_flow_sha256: &str,
        shape_limits: BasicShapeLimits,
        limits: ShapePointsLimits,
    ) -> Result<Self, ShapePointsError> {
        if draft.schema_version != SHAPE_POINTS_SCHEMA_VERSION {
            return Err(ShapePointsError::UnsupportedVersion);
        }
        require_digest(&draft.expected_source_state_sha256)?;
        require_digest(&draft.expected_document_flow_sha256)?;
        require_digest(&draft.target_document_flow_sha256)?;
        require_digest(current_document_flow_sha256)?;
        if current.canonical_sha256(limits)? != draft.expected_source_state_sha256 {
            return Err(ShapePointsError::SourceStateDrift);
        }
        if current_document_flow_sha256 != draft.expected_document_flow_sha256 {
            return Err(ShapePointsError::DocumentFlowDrift);
        }
        validate_freeform(&draft.target_freeform, &current.geometry, shape_limits)?;
        if draft.target_freeform == current.freeform {
            return Err(ShapePointsError::Noop);
        }
        let request = Self {
            schema_version: SHAPE_POINTS_SCHEMA_VERSION,
            request_id: draft.request_id,
            expected_source_state_sha256: draft.expected_source_state_sha256,
            expected_document_flow_sha256: draft.expected_document_flow_sha256,
            target_document_flow_sha256: draft.target_document_flow_sha256,
            target_freeform: draft.target_freeform,
        };
        let _ = request.canonical_json(limits)?;
        Ok(request)
    }

    /// Parses strict, bounded and duplicate-key-free request JSON.
    ///
    /// # Errors
    ///
    /// Rejects malformed, duplicate, unknown, oversized, stale or invalid input.
    pub fn from_json(
        bytes: &[u8],
        current: &ShapePointsState,
        current_document_flow_sha256: &str,
        shape_limits: BasicShapeLimits,
        limits: ShapePointsLimits,
    ) -> Result<Self, ShapePointsError> {
        if bytes.is_empty() || bytes.len() > limits.0.input_bytes {
            return Err(ShapePointsError::InputLimit);
        }
        reject_duplicate_json_keys(bytes)?;
        let draft = serde_json::from_slice(bytes).map_err(|_| ShapePointsError::InvalidJson)?;
        Self::from_draft(
            draft,
            current,
            current_document_flow_sha256,
            shape_limits,
            limits,
        )
    }

    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        "obj.shape_edit_points"
    }

    /// Serializes the complete request deterministically within the configured bound.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit error.
    pub fn canonical_json(&self, limits: ShapePointsLimits) -> Result<Vec<u8>, ShapePointsError> {
        serialize_bounded(self, limits)
    }
}

impl fmt::Debug for ShapePointsRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ShapePointsRequest")
            .field("capability_id", &self.capability_id())
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ShapePointsPlan {
    schema_version: &'static str,
    capability_id: &'static str,
    request_id: LogicalId,
    source_state: ShapePointsState,
    source_state_sha256: String,
    target_state: ShapePointsState,
    target_state_sha256: String,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    plan_sha256: String,
}

impl ShapePointsPlan {
    #[must_use]
    pub const fn target_state(&self) -> &ShapePointsState {
        &self.target_state
    }

    #[must_use]
    pub fn plan_sha256(&self) -> &str {
        &self.plan_sha256
    }
}

impl fmt::Debug for ShapePointsPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ShapePointsPlan")
            .field("capability_id", &self.capability_id)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct ShapePointsBuilder;

impl ShapePointsBuilder {
    /// Creates a deterministic point-edit plan after rechecking exact state and flow.
    ///
    /// # Errors
    ///
    /// Rejects source-state, document-flow, topology or output drift.
    pub fn plan(
        current: &ShapePointsState,
        request: &ShapePointsRequest,
        current_document_flow_sha256: &str,
        shape_limits: BasicShapeLimits,
        limits: ShapePointsLimits,
    ) -> Result<ShapePointsPlan, ShapePointsError> {
        let source_state_sha256 = current.canonical_sha256(limits)?;
        if source_state_sha256 != request.expected_source_state_sha256 {
            return Err(ShapePointsError::SourceStateDrift);
        }
        if current_document_flow_sha256 != request.expected_document_flow_sha256 {
            return Err(ShapePointsError::DocumentFlowDrift);
        }
        validate_freeform(&request.target_freeform, &current.geometry, shape_limits)?;
        if request.target_freeform == current.freeform {
            return Err(ShapePointsError::Noop);
        }
        let mut target_state = current.clone();
        target_state.freeform.clone_from(&request.target_freeform);
        let target_state_sha256 = target_state.canonical_sha256(limits)?;
        let mut plan = ShapePointsPlan {
            schema_version: SHAPE_POINTS_SCHEMA_VERSION,
            capability_id: "obj.shape_edit_points",
            request_id: request.request_id.clone(),
            source_state: current.clone(),
            source_state_sha256,
            target_state,
            target_state_sha256,
            source_document_flow_sha256: request.expected_document_flow_sha256.clone(),
            target_document_flow_sha256: request.target_document_flow_sha256.clone(),
            plan_sha256: String::new(),
        };
        plan.plan_sha256 = plan_binding_sha256(&plan, limits)?;
        let _ = serialize_bounded(&plan, limits)?;
        Ok(plan)
    }

    /// Rechecks plan integrity, exact current state and current flow before publishing.
    ///
    /// # Errors
    ///
    /// Rejects plan tampering, source-state drift and document-flow drift.
    pub fn build(
        plan: &ShapePointsPlan,
        current: &ShapePointsState,
        current_document_flow_sha256: &str,
        shape_limits: BasicShapeLimits,
        limits: ShapePointsLimits,
    ) -> Result<ShapePointsResult, ShapePointsError> {
        if plan.schema_version != SHAPE_POINTS_SCHEMA_VERSION
            || plan.capability_id != "obj.shape_edit_points"
            || plan_binding_sha256(plan, limits)? != plan.plan_sha256
            || plan.source_state.canonical_sha256(limits)? != plan.source_state_sha256
            || plan.target_state.canonical_sha256(limits)? != plan.target_state_sha256
        {
            return Err(ShapePointsError::PlanTampered);
        }
        if current.canonical_sha256(limits)? != plan.source_state_sha256 {
            return Err(ShapePointsError::SourceStateDrift);
        }
        if current_document_flow_sha256 != plan.source_document_flow_sha256 {
            return Err(ShapePointsError::DocumentFlowDrift);
        }
        validate_freeform(
            &plan.target_state.freeform,
            &plan.target_state.geometry,
            shape_limits,
        )?;
        let mut expected = plan.source_state.clone();
        expected.freeform.clone_from(&plan.target_state.freeform);
        if expected != plan.target_state || expected == plan.source_state {
            return Err(ShapePointsError::PlanTampered);
        }
        Ok(ShapePointsResult {
            state: plan.target_state.clone(),
            receipt: ShapePointsReceipt {
                schema_version: SHAPE_POINTS_SCHEMA_VERSION,
                capability_id: "obj.shape_edit_points",
                source_state_sha256: plan.source_state_sha256.clone(),
                target_state_sha256: plan.target_state_sha256.clone(),
                source_document_flow_sha256: plan.source_document_flow_sha256.clone(),
                target_document_flow_sha256: plan.target_document_flow_sha256.clone(),
                plan_sha256: plan.plan_sha256.clone(),
            },
        })
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ShapePointsReceipt {
    schema_version: &'static str,
    capability_id: &'static str,
    source_state_sha256: String,
    target_state_sha256: String,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    plan_sha256: String,
}

impl fmt::Debug for ShapePointsReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ShapePointsReceipt")
            .field("capability_id", &self.capability_id)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct ShapePointsResult {
    pub state: ShapePointsState,
    pub receipt: ShapePointsReceipt,
}

impl fmt::Debug for ShapePointsResult {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ShapePointsResult")
            .field("state", &"<redacted>")
            .field("receipt", &self.receipt)
            .finish()
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum ShapePointsError {
    #[error("shape-point limits are invalid")]
    InvalidLimit,
    #[error("shape-point input exceeds a finite limit")]
    InputLimit,
    #[error("shape-point JSON is malformed, duplicated, or not strict")]
    InvalidJson,
    #[error("shape-point schema version is unsupported")]
    UnsupportedVersion,
    #[error("shape-point digest is invalid")]
    InvalidDigest,
    #[error("shape-point geometry state is invalid")]
    GeometryStateInvalid,
    #[error("shape-point topology is invalid")]
    TopologyInvalid,
    #[error("shape-point edit is a no-op")]
    Noop,
    #[error("shape-point source state drifted")]
    SourceStateDrift,
    #[error("shape-point document flow drifted")]
    DocumentFlowDrift,
    #[error("shape-point plan was tampered with")]
    PlanTampered,
    #[error("shape-point serialization failed")]
    Serialization,
    #[error("shape-point output exceeds a finite limit")]
    OutputLimit,
}

impl ShapePointsError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "shape_points_invalid_limit",
            Self::InputLimit => "shape_points_input_limit",
            Self::InvalidJson => "shape_points_invalid_json",
            Self::UnsupportedVersion => "shape_points_unsupported_version",
            Self::InvalidDigest => "shape_points_invalid_digest",
            Self::GeometryStateInvalid => "shape_points_geometry_state_invalid",
            Self::TopologyInvalid => "shape_points_topology_invalid",
            Self::Noop => "shape_points_noop",
            Self::SourceStateDrift => "shape_points_source_state_drift",
            Self::DocumentFlowDrift => "shape_points_document_flow_drift",
            Self::PlanTampered => "shape_points_plan_tampered",
            Self::Serialization => "shape_points_serialization",
            Self::OutputLimit => "shape_points_output_limit",
        }
    }
}

fn validate_freeform(
    freeform: &FreeformShape,
    geometry: &ObjectGeometryState,
    limits: BasicShapeLimits,
) -> Result<(), ShapePointsError> {
    BasicShape::Freeform {
        freeform: freeform.clone(),
    }
    .validate_for_geometry(geometry, limits)
    .map_err(|_| ShapePointsError::TopologyInvalid)
}

fn require_digest(value: &str) -> Result<(), ShapePointsError> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(ShapePointsError::InvalidDigest);
    }
    Ok(())
}

fn plan_binding_sha256(
    plan: &ShapePointsPlan,
    limits: ShapePointsLimits,
) -> Result<String, ShapePointsError> {
    #[derive(Serialize)]
    struct Binding<'a> {
        schema_version: &'static str,
        capability_id: &'static str,
        request_id: &'a LogicalId,
        source_state_sha256: &'a str,
        target_state_sha256: &'a str,
        source_document_flow_sha256: &'a str,
        target_document_flow_sha256: &'a str,
    }
    let binding = Binding {
        schema_version: plan.schema_version,
        capability_id: plan.capability_id,
        request_id: &plan.request_id,
        source_state_sha256: &plan.source_state_sha256,
        target_state_sha256: &plan.target_state_sha256,
        source_document_flow_sha256: &plan.source_document_flow_sha256,
        target_document_flow_sha256: &plan.target_document_flow_sha256,
    };
    Ok(hex(
        Sha256::digest(serialize_bounded(&binding, limits)?).into()
    ))
}

fn serialize_bounded<T: Serialize>(
    value: &T,
    limits: ShapePointsLimits,
) -> Result<Vec<u8>, ShapePointsError> {
    let bytes = serde_json::to_vec(value).map_err(|_| ShapePointsError::Serialization)?;
    if bytes.len() > limits.0.output_bytes {
        return Err(ShapePointsError::OutputLimit);
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

fn reject_duplicate_json_keys(bytes: &[u8]) -> Result<(), ShapePointsError> {
    struct DuplicateVisitor;
    impl<'de> Visitor<'de> for DuplicateVisitor {
        type Value = ();
        fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
            formatter.write_str("JSON without duplicate object keys")
        }
        fn visit_bool<E>(self, _: bool) -> Result<Self::Value, E> {
            Ok(())
        }
        fn visit_i64<E>(self, _: i64) -> Result<Self::Value, E> {
            Ok(())
        }
        fn visit_u64<E>(self, _: u64) -> Result<Self::Value, E> {
            Ok(())
        }
        fn visit_f64<E>(self, _: f64) -> Result<Self::Value, E> {
            Ok(())
        }
        fn visit_str<E>(self, _: &str) -> Result<Self::Value, E> {
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
            deserializer.deserialize_any(DuplicateVisitor)
        }
        fn visit_seq<A>(self, mut sequence: A) -> Result<Self::Value, A::Error>
        where
            A: de::SeqAccess<'de>,
        {
            while sequence.next_element_seed(DuplicateSeed)?.is_some() {}
            Ok(())
        }
        fn visit_map<A>(self, mut map: A) -> Result<Self::Value, A::Error>
        where
            A: MapAccess<'de>,
        {
            let mut keys = BTreeSet::new();
            while let Some(key) = map.next_key::<String>()? {
                if !keys.insert(key) {
                    return Err(de::Error::custom("duplicate JSON key"));
                }
                map.next_value_seed(DuplicateSeed)?;
            }
            Ok(())
        }
    }
    struct DuplicateSeed;
    impl<'de> de::DeserializeSeed<'de> for DuplicateSeed {
        type Value = ();
        fn deserialize<D>(self, deserializer: D) -> Result<Self::Value, D::Error>
        where
            D: serde::Deserializer<'de>,
        {
            deserializer.deserialize_any(DuplicateVisitor)
        }
    }
    let mut deserializer = serde_json::Deserializer::from_slice(bytes);
    de::DeserializeSeed::deserialize(DuplicateSeed, &mut deserializer)
        .map_err(|_| ShapePointsError::InvalidJson)?;
    deserializer
        .end()
        .map_err(|_| ShapePointsError::InvalidJson)
}

#[cfg(test)]
mod private_tests {
    use super::*;

    #[test]
    fn error_code_is_content_free() {
        assert_eq!(
            ShapePointsError::PlanTampered.code(),
            "shape_points_plan_tampered"
        );
    }
}
