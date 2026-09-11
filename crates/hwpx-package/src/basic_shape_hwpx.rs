use std::collections::BTreeSet;
use std::fmt::{self, Debug, Write as _};
use std::io::{Read, Seek};

use domain_ir::{
    BasicShape, BasicShapeBuilder, BasicShapeError, BasicShapeLimits, BasicShapePlan, CurveSegment,
    CurveSegmentType, EllipseArcType, EllipseShape, FreeformShape, LineShape, LogicalId,
    ObjectAffineMatrix, ObjectGeometryLimits, ObjectGeometryState, ObjectHeightReference,
    ObjectHorizontalAlignment, ObjectHorizontalReference, ObjectNumberingType, ObjectTextFlow,
    ObjectTextWrap, ObjectVerticalAlignment, ObjectVerticalReference, ObjectWidthReference,
    RectangleShape, ShapePoint, TextBoxContent, TextBoxVerticalAlignment,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{
    BoundedZipReader, GraphError, IdIndexLimits, IdRuleProfile, ObjectGeometryHwpxError,
    ObjectGeometryHwpxLimits, ObjectGeometryHwpxReader, PackageError, PackageGraph,
    PackageGraphLimits, PackageLimits, PackagePath, PartRole, PatchError, PatchIntent, PatchLimits,
    PatchResult, PreservingPatchEngine, PreservingXmlDocument, PreservingXmlError,
    RelationshipKind, SiblingPosition, ValidatedXmlFragment, XmlElementSelector, XmlElementToken,
};

pub const BASIC_SHAPE_HWPX_PROFILE_ID: &str = "hwpx-agent.basic-shape-hwpx.hwpml-2011-static/v1";

const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const CORE_NS: &str = "http://www.hancom.co.kr/hwpml/2011/core";
const SECTION_NS: &str = "http://www.hancom.co.kr/hwpml/2011/section";
const FIXED_SCALE: i64 = 1_000_000;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct BasicShapeHwpxLimitConfig {
    pub section_bytes: usize,
    pub elements: usize,
    pub objects: usize,
    pub serialized_bytes: usize,
    pub fragment_bytes: usize,
}

impl Default for BasicShapeHwpxLimitConfig {
    fn default() -> Self {
        Self {
            section_bytes: 32 * 1024 * 1024,
            elements: 1_000_000,
            objects: 65_536,
            serialized_bytes: 16 * 1024 * 1024,
            fragment_bytes: 4 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct BasicShapeHwpxLimits {
    native: BasicShapeHwpxLimitConfig,
    pub package: PackageLimits,
    pub graph: PackageGraphLimits,
    pub ids: IdIndexLimits,
    pub patch: PatchLimits,
}

impl BasicShapeHwpxLimits {
    pub const HARD_MAX_SECTION_BYTES: usize = 128 * 1024 * 1024;
    pub const HARD_MAX_ELEMENTS: usize = 2_000_000;
    pub const HARD_MAX_OBJECTS: usize = 262_144;
    pub const HARD_MAX_SERIALIZED_BYTES: usize = 32 * 1024 * 1024;
    pub const HARD_MAX_FRAGMENT_BYTES: usize = 16 * 1024 * 1024;

    /// Creates finite static shape-lowering limits.
    ///
    /// # Errors
    ///
    /// Rejects zero, inconsistent or hard-ceiling-exceeding values.
    pub fn new(
        native: BasicShapeHwpxLimitConfig,
        package: PackageLimits,
        graph: PackageGraphLimits,
        ids: IdIndexLimits,
        patch: PatchLimits,
    ) -> Result<Self, BasicShapeHwpxError> {
        if native.section_bytes == 0
            || native.section_bytes > Self::HARD_MAX_SECTION_BYTES
            || native.elements == 0
            || native.elements > Self::HARD_MAX_ELEMENTS
            || native.objects == 0
            || native.objects > Self::HARD_MAX_OBJECTS
            || native.serialized_bytes == 0
            || native.serialized_bytes > Self::HARD_MAX_SERIALIZED_BYTES
            || native.fragment_bytes == 0
            || native.fragment_bytes > Self::HARD_MAX_FRAGMENT_BYTES
            || native.fragment_bytes > native.section_bytes
        {
            return Err(BasicShapeHwpxError::InvalidLimit);
        }
        Ok(Self {
            native,
            package,
            graph,
            ids,
            patch,
        })
    }

    #[must_use]
    pub const fn config(self) -> BasicShapeHwpxLimitConfig {
        self.native
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct BasicShapeHwpxSource {
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
    paragraph_ids_sha256: String,
    sublist_ids_sha256: String,
    object_id_count: usize,
    instance_id_count: usize,
    paragraph_id_count: usize,
    sublist_id_count: usize,
    section_object_count: usize,
    section_instance_count: usize,
    section_shape_count: usize,
}

impl BasicShapeHwpxSource {
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
    pub const fn object_id_count(&self) -> usize {
        self.object_id_count
    }

    #[must_use]
    pub const fn instance_id_count(&self) -> usize {
        self.instance_id_count
    }

    #[must_use]
    pub const fn paragraph_id_count(&self) -> usize {
        self.paragraph_id_count
    }

    #[must_use]
    pub const fn sublist_id_count(&self) -> usize {
        self.sublist_id_count
    }

    /// Serializes the complete source binding without source XML or paths in diagnostics.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit error.
    pub fn canonical_json(
        &self,
        limits: BasicShapeHwpxLimits,
    ) -> Result<Vec<u8>, BasicShapeHwpxError> {
        bounded_json(self, limits)
    }
}

impl Debug for BasicShapeHwpxSource {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("BasicShapeHwpxSource")
            .field("profile_id", &self.profile_id)
            .field("section_part", &"<redacted>")
            .field("paragraph_ordinal", &self.paragraph_ordinal)
            .field("run_ordinal", &self.run_ordinal)
            .field("bindings", &"<redacted>")
            .field("object_id_count", &self.object_id_count)
            .field("instance_id_count", &self.instance_id_count)
            .field("paragraph_id_count", &self.paragraph_id_count)
            .field("sublist_id_count", &self.sublist_id_count)
            .field("section_shape_count", &self.section_shape_count)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct BasicShapeHwpxPlan {
    profile_id: &'static str,
    source: BasicShapeHwpxSource,
    domain_plan: BasicShapePlan,
    domain_plan_sha256: String,
    plan_sha256: String,
}

impl BasicShapeHwpxPlan {
    #[must_use]
    pub const fn source(&self) -> &BasicShapeHwpxSource {
        &self.source
    }

    #[must_use]
    pub const fn domain_plan(&self) -> &BasicShapePlan {
        &self.domain_plan
    }

    #[must_use]
    pub fn plan_sha256(&self) -> &str {
        &self.plan_sha256
    }

    /// Serializes the exact plan and all source bindings within the configured limit.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit error.
    pub fn canonical_json(
        &self,
        limits: BasicShapeHwpxLimits,
    ) -> Result<Vec<u8>, BasicShapeHwpxError> {
        bounded_json(self, limits)
    }
}

impl Debug for BasicShapeHwpxPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("BasicShapeHwpxPlan")
            .field("profile_id", &self.profile_id)
            .field("source", &self.source)
            .field("domain_plan", &self.domain_plan)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct BasicShapeHwpxReadback {
    profile_id: &'static str,
    geometry: ObjectGeometryState,
    shape: BasicShape,
    object_count: usize,
    instance_count: usize,
    shape_count: usize,
    paragraph_count: usize,
    sublist_count: usize,
}

impl BasicShapeHwpxReadback {
    #[must_use]
    pub const fn geometry(&self) -> &ObjectGeometryState {
        &self.geometry
    }

    #[must_use]
    pub const fn shape(&self) -> &BasicShape {
        &self.shape
    }
}

impl Debug for BasicShapeHwpxReadback {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("BasicShapeHwpxReadback")
            .field("profile_id", &self.profile_id)
            .field("shape_kind", &self.shape.object_kind())
            .field("payload", &"<redacted>")
            .field("object_count", &self.object_count)
            .field("instance_count", &self.instance_count)
            .field("shape_count", &self.shape_count)
            .field("paragraph_count", &self.paragraph_count)
            .field("sublist_count", &self.sublist_count)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct BasicShapeHwpxLoweringReceipt {
    profile_id: &'static str,
    plan_sha256: String,
    source_package_state_sha256: String,
    source_section_sha256: String,
    output_section_sha256: String,
    target_document_flow_sha256: String,
    object_count_before: usize,
    object_count_after: usize,
    instance_count_before: usize,
    instance_count_after: usize,
    shape_count_before: usize,
    shape_count_after: usize,
}

impl BasicShapeHwpxLoweringReceipt {
    #[must_use]
    pub fn output_section_sha256(&self) -> &str {
        &self.output_section_sha256
    }

    #[must_use]
    pub fn target_document_flow_sha256(&self) -> &str {
        &self.target_document_flow_sha256
    }
}

impl Debug for BasicShapeHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("BasicShapeHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field("bindings", &"<redacted>")
            .field("object_count_before", &self.object_count_before)
            .field("object_count_after", &self.object_count_after)
            .field("instance_count_before", &self.instance_count_before)
            .field("instance_count_after", &self.instance_count_after)
            .field("shape_count_before", &self.shape_count_before)
            .field("shape_count_after", &self.shape_count_after)
            .finish_non_exhaustive()
    }
}

pub struct BasicShapeHwpxLowered {
    patch: PatchResult,
    receipt: BasicShapeHwpxLoweringReceipt,
}

impl Debug for BasicShapeHwpxLowered {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("BasicShapeHwpxLowered")
            .field("changed_parts", &self.patch.changed_parts())
            .field("added_parts", &self.patch.added_parts())
            .field("receipt", &self.receipt)
            .finish_non_exhaustive()
    }
}

impl BasicShapeHwpxLowered {
    #[must_use]
    pub const fn receipt(&self) -> &BasicShapeHwpxLoweringReceipt {
        &self.receipt
    }

    #[must_use]
    pub const fn patch(&self) -> &PatchResult {
        &self.patch
    }

    #[must_use]
    pub fn into_patch(self) -> PatchResult {
        self.patch
    }
}

#[derive(Debug)]
pub struct BasicShapeHwpxBuilder;

impl BasicShapeHwpxBuilder {
    /// Inspects one exact empty run and binds the complete package and native-ID state.
    ///
    /// # Errors
    ///
    /// Rejects stale, non-spine, ambiguous, non-empty, malformed or limit-excessive targets.
    pub fn inspect_source<R: Read + Seek>(
        reader: &mut BoundedZipReader<R>,
        graph: &PackageGraph,
        section_part: &str,
        paragraph_ordinal: usize,
        run_ordinal: usize,
        limits: BasicShapeHwpxLimits,
    ) -> Result<BasicShapeHwpxSource, BasicShapeHwpxError> {
        inspect_bound_source(
            reader,
            graph,
            section_part,
            paragraph_ordinal,
            run_ordinal,
            limits,
        )
        .map(|bound| bound.source)
    }

    /// Plans one exact shape insertion from a validated semantic plan.
    ///
    /// # Errors
    ///
    /// Rejects domain, package, flow, ID, anchor or serialization drift.
    #[allow(clippy::too_many_arguments)]
    pub fn plan<R: Read + Seek>(
        reader: &mut BoundedZipReader<R>,
        graph: &PackageGraph,
        section_part: &str,
        paragraph_ordinal: usize,
        run_ordinal: usize,
        domain_plan: &BasicShapePlan,
        current_document_flow_sha256: &str,
        shape_limits: BasicShapeLimits,
        geometry_limits: ObjectGeometryLimits,
        limits: BasicShapeHwpxLimits,
    ) -> Result<BasicShapeHwpxPlan, BasicShapeHwpxError> {
        let bound = inspect_bound_source(
            reader,
            graph,
            section_part,
            paragraph_ordinal,
            run_ordinal,
            limits,
        )?;
        let semantic = BasicShapeBuilder::build(
            domain_plan,
            current_document_flow_sha256,
            geometry_limits,
            shape_limits,
        )?;
        validate_collisions(&bound, semantic.geometry(), semantic.shape())?;
        let domain_plan_sha256 =
            hex(Sha256::digest(domain_plan.canonical_json(shape_limits)?).into());
        let plan_sha256 = plan_digest(&bound.source, &domain_plan_sha256, limits)?;
        let plan = BasicShapeHwpxPlan {
            profile_id: BASIC_SHAPE_HWPX_PROFILE_ID,
            source: bound.source,
            domain_plan: domain_plan.clone(),
            domain_plan_sha256,
            plan_sha256,
        };
        let _ = plan.canonical_json(limits)?;
        Ok(plan)
    }
}

#[derive(Debug)]
pub struct BasicShapeHwpxReader;

impl BasicShapeHwpxReader {
    /// Strictly reads one static-profile run-level basic shape.
    ///
    /// # Errors
    ///
    /// Rejects common geometry, native payload, text, identity or structural drift.
    #[allow(clippy::too_many_arguments)]
    pub fn read_in_section(
        bytes: &[u8],
        object_ordinal: usize,
        logical_object_id: LogicalId,
        expected_shape: &BasicShape,
        shape_limits: BasicShapeLimits,
        geometry_limits: ObjectGeometryLimits,
        geometry_hwpx_limits: ObjectGeometryHwpxLimits,
        limits: BasicShapeHwpxLimits,
    ) -> Result<BasicShapeHwpxReadback, BasicShapeHwpxError> {
        read_shape(
            bytes,
            object_ordinal,
            logical_object_id,
            expected_shape,
            shape_limits,
            geometry_limits,
            geometry_hwpx_limits,
            limits,
        )
        .map(|parsed| parsed.readback)
    }
}

#[derive(Debug)]
pub struct BasicShapeHwpxLowerer;

impl BasicShapeHwpxLowerer {
    /// Inserts one basic shape in a preserving package transaction and reopens exact semantics.
    ///
    /// # Errors
    ///
    /// Returns no partial artifact on plan, source, flow, ID, patch, readback or preservation drift.
    #[allow(clippy::too_many_arguments, clippy::too_many_lines)]
    pub fn lower<R: Read + Seek>(
        reader: &mut BoundedZipReader<R>,
        graph: &PackageGraph,
        plan: &BasicShapeHwpxPlan,
        current_document_flow_sha256: &str,
        shape_limits: BasicShapeLimits,
        geometry_limits: ObjectGeometryLimits,
        geometry_hwpx_limits: ObjectGeometryHwpxLimits,
        limits: BasicShapeHwpxLimits,
    ) -> Result<BasicShapeHwpxLowered, BasicShapeHwpxError> {
        if plan.profile_id != BASIC_SHAPE_HWPX_PROFILE_ID {
            return Err(BasicShapeHwpxError::BuildDrift);
        }
        let bound = inspect_bound_source(
            reader,
            graph,
            &plan.source.section_part,
            plan.source.paragraph_ordinal,
            plan.source.run_ordinal,
            limits,
        )?;
        if bound.source != plan.source
            || plan_digest(&plan.source, &plan.domain_plan_sha256, limits)? != plan.plan_sha256
            || hex(Sha256::digest(plan.domain_plan.canonical_json(shape_limits)?).into())
                != plan.domain_plan_sha256
        {
            return Err(BasicShapeHwpxError::BuildDrift);
        }
        let semantic = BasicShapeBuilder::build(
            &plan.domain_plan,
            current_document_flow_sha256,
            geometry_limits,
            shape_limits,
        )?;
        validate_collisions(&bound, semantic.geometry(), semantic.shape())?;
        let fragment_bytes = shape_fragment(semantic.geometry(), semantic.shape(), limits)?;
        let fragment = ValidatedXmlFragment::parse(&fragment_bytes, limits.patch)?;
        let selector =
            XmlElementSelector::bind(&bound.path, &bound.document, bound.target_text_element)?;
        let patch = PreservingPatchEngine::apply_with_limits(
            reader,
            graph,
            limits.graph,
            IdRuleProfile::hwpml_2011_shape_v6(),
            limits.ids,
            limits.patch,
            &[PatchIntent::InsertSibling {
                target: selector,
                position: SiblingPosition::Before,
                fragment,
            }],
        )?;
        patch.verify_artifact_integrity()?;
        if patch.intent_count() != 1 || patch.changed_parts() != 1 || patch.added_parts() != 0 {
            return Err(BasicShapeHwpxError::PreservationMismatch);
        }
        let output_section = patch
            .parts
            .iter()
            .find(|part| part.path == bound.path)
            .ok_or(BasicShapeHwpxError::ReadbackMismatch)?;
        let parsed = read_shape(
            &output_section.bytes,
            bound.insertion_object_ordinal,
            semantic.geometry().object_id().clone(),
            semantic.shape(),
            shape_limits,
            geometry_limits,
            geometry_hwpx_limits,
            limits,
        )?;
        if parsed.readback.geometry != *semantic.geometry()
            || parsed.readback.shape != *semantic.shape()
            || parsed.readback.object_count != bound.source.section_object_count + 1
            || parsed.readback.instance_count != bound.source.section_instance_count + 1
            || parsed.readback.shape_count != bound.source.section_shape_count + 1
        {
            return Err(BasicShapeHwpxError::ReadbackMismatch);
        }
        let text_delta = usize::from(semantic.shape().text_box_content().is_some());
        if parsed.readback.paragraph_count != bound.section_paragraph_ids.len() + text_delta
            || parsed.readback.sublist_count != bound.section_sublist_ids.len() + text_delta
        {
            return Err(BasicShapeHwpxError::ReadbackMismatch);
        }
        let mut restored = Vec::with_capacity(bound.bytes.len());
        restored.extend_from_slice(&output_section.bytes[..parsed.shape_span.start()]);
        restored.extend_from_slice(&output_section.bytes[parsed.shape_span.end()..]);
        if restored != bound.bytes {
            return Err(BasicShapeHwpxError::PreservationMismatch);
        }
        let receipt = BasicShapeHwpxLoweringReceipt {
            profile_id: BASIC_SHAPE_HWPX_PROFILE_ID,
            plan_sha256: plan.plan_sha256.clone(),
            source_package_state_sha256: bound.source.package_state_sha256.clone(),
            source_section_sha256: bound.source.section_sha256.clone(),
            output_section_sha256: hex(Sha256::digest(&output_section.bytes).into()),
            target_document_flow_sha256: plan.domain_plan.target_document_flow_sha256().to_owned(),
            object_count_before: bound.source.section_object_count,
            object_count_after: parsed.readback.object_count,
            instance_count_before: bound.source.section_instance_count,
            instance_count_after: parsed.readback.instance_count,
            shape_count_before: bound.source.section_shape_count,
            shape_count_after: parsed.readback.shape_count,
        };
        Ok(BasicShapeHwpxLowered { patch, receipt })
    }
}

#[derive(Debug, Error)]
pub enum BasicShapeHwpxError {
    #[error("basic-shape HWPX limits are invalid")]
    InvalidLimit,
    #[error("basic-shape HWPX source drifted")]
    SourceDrift,
    #[error("basic-shape HWPX target shape is unsupported")]
    UnsupportedTarget,
    #[error("basic-shape HWPX native identifier collides")]
    IdCollision,
    #[error("basic-shape HWPX plan drifted before build")]
    BuildDrift,
    #[error("basic-shape HWPX strict readback differs")]
    ReadbackMismatch,
    #[error("basic-shape HWPX preservation proof differs")]
    PreservationMismatch,
    #[error("basic-shape HWPX input limit was exceeded")]
    InputLimit,
    #[error("basic-shape HWPX output limit was exceeded")]
    OutputLimit,
    #[error("basic-shape HWPX allocation failed")]
    Allocation,
    #[error("basic-shape semantic validation failed")]
    Domain(#[from] BasicShapeError),
    #[error("basic-shape common geometry readback failed")]
    Geometry(#[from] ObjectGeometryHwpxError),
    #[error("basic-shape package read failed")]
    Package(#[from] PackageError),
    #[error("basic-shape graph validation failed")]
    Graph(#[from] GraphError),
    #[error("basic-shape XML tokenization failed")]
    Xml(#[from] PreservingXmlError),
    #[error("basic-shape preserving patch failed")]
    Patch(#[from] PatchError),
}

impl BasicShapeHwpxError {
    #[must_use]
    pub fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "basic_shape_hwpx_invalid_limit",
            Self::SourceDrift => "basic_shape_hwpx_source_drift",
            Self::UnsupportedTarget => "basic_shape_hwpx_unsupported_target",
            Self::IdCollision => "basic_shape_hwpx_id_collision",
            Self::BuildDrift => "basic_shape_hwpx_build_drift",
            Self::ReadbackMismatch => "basic_shape_hwpx_readback_mismatch",
            Self::PreservationMismatch => "basic_shape_hwpx_preservation_mismatch",
            Self::InputLimit => "basic_shape_hwpx_input_limit",
            Self::OutputLimit => "basic_shape_hwpx_output_limit",
            Self::Allocation => "basic_shape_hwpx_allocation",
            Self::Domain(error) => error.code(),
            Self::Geometry(error) => error.code(),
            Self::Package(error) => error.code(),
            Self::Graph(error) => error.code(),
            Self::Xml(error) => error.code(),
            Self::Patch(error) => error.code(),
        }
    }
}

struct BoundSource {
    source: BasicShapeHwpxSource,
    path: PackagePath,
    bytes: Vec<u8>,
    document: PreservingXmlDocument,
    target_text_element: usize,
    insertion_object_ordinal: usize,
    object_ids: BTreeSet<u32>,
    instance_ids: BTreeSet<u32>,
    paragraph_ids: BTreeSet<u32>,
    sublist_ids: BTreeSet<u32>,
    section_paragraph_ids: BTreeSet<u32>,
    section_sublist_ids: BTreeSet<u32>,
}

struct ParsedShape {
    readback: BasicShapeHwpxReadback,
    shape_span: crate::XmlByteSpan,
}

fn inspect_bound_source<R: Read + Seek>(
    reader: &mut BoundedZipReader<R>,
    graph: &PackageGraph,
    section_part: &str,
    paragraph_ordinal: usize,
    run_ordinal: usize,
    limits: BasicShapeHwpxLimits,
) -> Result<BoundSource, BasicShapeHwpxError> {
    let (path, bytes) = read_spine_part(reader, graph, section_part, limits)?;
    let document = parse_section(&bytes, limits)?;
    let root = element(&document, document.root_element())?;
    if root.name().namespace() != Some(SECTION_NS) || root.name().local_name() != "sec" {
        return Err(BasicShapeHwpxError::UnsupportedTarget);
    }
    let paragraphs = direct_children_named(&document, document.root_element(), "p")?;
    let paragraph = *paragraphs
        .get(paragraph_ordinal)
        .ok_or(BasicShapeHwpxError::UnsupportedTarget)?;
    let runs = direct_children_named(&document, paragraph, "run")?;
    let run = *runs
        .get(run_ordinal)
        .ok_or(BasicShapeHwpxError::UnsupportedTarget)?;
    let run_children = child_indexes(&document, run)?;
    if run_children.len() != 1
        || !has_para_name(element(&document, run_children[0])?, "t")
        || !element(&document, run_children[0])?.is_empty()
    {
        return Err(BasicShapeHwpxError::UnsupportedTarget);
    }
    let section_sets = collect_native_ids(&document, limits)?;
    let package_sets = collect_package_native_ids(reader, graph, limits)?;
    let insertion_object_ordinal = document
        .elements()
        .iter()
        .enumerate()
        .take_while(|(index, _)| *index < run_children[0])
        .filter(|(index, candidate)| is_direct_run_object(&document, *index, candidate))
        .count();
    let paragraph_span = element(&document, paragraph)?
        .outer_span()
        .ok_or(BasicShapeHwpxError::UnsupportedTarget)?;
    let run_span = element(&document, run)?
        .outer_span()
        .ok_or(BasicShapeHwpxError::UnsupportedTarget)?;
    let source = BasicShapeHwpxSource {
        profile_id: BASIC_SHAPE_HWPX_PROFILE_ID,
        section_part: path.as_str().to_owned(),
        paragraph_ordinal,
        run_ordinal,
        package_state_sha256: package_state_sha256(graph),
        section_sha256: hex(Sha256::digest(&bytes).into()),
        paragraph_sha256: hex(
            Sha256::digest(document.source_text(paragraph_span)?.as_bytes()).into(),
        ),
        run_sha256: hex(Sha256::digest(document.source_text(run_span)?.as_bytes()).into()),
        object_ids_sha256: id_set_sha256("object", &package_sets.object_ids),
        instance_ids_sha256: id_set_sha256("instance", &package_sets.instance_ids),
        paragraph_ids_sha256: id_set_sha256("paragraph", &package_sets.paragraph_ids),
        sublist_ids_sha256: id_set_sha256("sublist", &package_sets.sublist_ids),
        object_id_count: package_sets.object_ids.len(),
        instance_id_count: package_sets.instance_ids.len(),
        paragraph_id_count: package_sets.paragraph_ids.len(),
        sublist_id_count: package_sets.sublist_ids.len(),
        section_object_count: section_sets.object_ids.len(),
        section_instance_count: section_sets.instance_ids.len(),
        section_shape_count: section_sets.shape_count,
    };
    Ok(BoundSource {
        source,
        path,
        bytes,
        document,
        target_text_element: run_children[0],
        insertion_object_ordinal,
        object_ids: package_sets.object_ids,
        instance_ids: package_sets.instance_ids,
        paragraph_ids: package_sets.paragraph_ids,
        sublist_ids: package_sets.sublist_ids,
        section_paragraph_ids: section_sets.paragraph_ids,
        section_sublist_ids: section_sets.sublist_ids,
    })
}

fn validate_collisions(
    bound: &BoundSource,
    geometry: &ObjectGeometryState,
    shape: &BasicShape,
) -> Result<(), BasicShapeHwpxError> {
    if bound.object_ids.contains(&geometry.native_object_id())
        || bound.instance_ids.contains(&geometry.native_instance_id())
    {
        return Err(BasicShapeHwpxError::IdCollision);
    }
    if let Some(text) = shape.text_box_content()
        && (bound.paragraph_ids.contains(&text.paragraph_id)
            || bound.sublist_ids.contains(&text.sublist_id))
    {
        return Err(BasicShapeHwpxError::IdCollision);
    }
    Ok(())
}

#[derive(Default)]
struct NativeIds {
    object_ids: BTreeSet<u32>,
    instance_ids: BTreeSet<u32>,
    paragraph_ids: BTreeSet<u32>,
    sublist_ids: BTreeSet<u32>,
    shape_count: usize,
}

fn collect_package_native_ids<R: Read + Seek>(
    reader: &mut BoundedZipReader<R>,
    graph: &PackageGraph,
    limits: BasicShapeHwpxLimits,
) -> Result<NativeIds, BasicShapeHwpxError> {
    let paths = graph
        .spine
        .iter()
        .map(|path| path.as_str().to_owned())
        .collect::<Vec<_>>();
    let mut all = NativeIds::default();
    for path in paths {
        let (_, bytes) = read_spine_part(reader, graph, &path, limits)?;
        let document = parse_section(&bytes, limits)?;
        let part = collect_native_ids(&document, limits)?;
        extend_unique(&mut all.object_ids, part.object_ids)?;
        extend_unique(&mut all.instance_ids, part.instance_ids)?;
        extend_unique(&mut all.paragraph_ids, part.paragraph_ids)?;
        extend_unique(&mut all.sublist_ids, part.sublist_ids)?;
        all.shape_count = all
            .shape_count
            .checked_add(part.shape_count)
            .ok_or(BasicShapeHwpxError::InputLimit)?;
        if all.object_ids.len() > limits.native.objects
            || all.instance_ids.len() > limits.native.objects
            || all.paragraph_ids.len() > limits.native.objects
            || all.sublist_ids.len() > limits.native.objects
        {
            return Err(BasicShapeHwpxError::InputLimit);
        }
    }
    Ok(all)
}

fn extend_unique(
    target: &mut BTreeSet<u32>,
    values: BTreeSet<u32>,
) -> Result<(), BasicShapeHwpxError> {
    for value in values {
        if !target.insert(value) {
            return Err(BasicShapeHwpxError::IdCollision);
        }
    }
    Ok(())
}

fn collect_native_ids(
    document: &PreservingXmlDocument,
    limits: BasicShapeHwpxLimits,
) -> Result<NativeIds, BasicShapeHwpxError> {
    let mut ids = NativeIds::default();
    for candidate in document.elements() {
        if candidate.name().namespace() != Some(PARAGRAPH_NS) {
            continue;
        }
        let name = candidate.name().local_name();
        if is_object_name(name) {
            let object_id = parse_u32(attr(candidate, "id")?)?;
            if object_id == 0 || !ids.object_ids.insert(object_id) {
                return Err(BasicShapeHwpxError::IdCollision);
            }
            if let Some(instance) = optional_attr(candidate, "instid")? {
                let instance = parse_u32(instance)?;
                if instance == 0 || !ids.instance_ids.insert(instance) {
                    return Err(BasicShapeHwpxError::IdCollision);
                }
            }
            if is_basic_shape_name(name) {
                ids.shape_count = ids
                    .shape_count
                    .checked_add(1)
                    .ok_or(BasicShapeHwpxError::InputLimit)?;
            }
        } else if name == "p" {
            let id = parse_u32(attr(candidate, "id")?)?;
            if !ids.paragraph_ids.insert(id) {
                return Err(BasicShapeHwpxError::IdCollision);
            }
        } else if name == "subList" {
            let id = parse_u32(attr(candidate, "id")?)?;
            if !ids.sublist_ids.insert(id) {
                return Err(BasicShapeHwpxError::IdCollision);
            }
        }
        if ids.object_ids.len() > limits.native.objects
            || ids.instance_ids.len() > limits.native.objects
            || ids.paragraph_ids.len() > limits.native.objects
            || ids.sublist_ids.len() > limits.native.objects
            || ids.shape_count > limits.native.objects
        {
            return Err(BasicShapeHwpxError::InputLimit);
        }
    }
    Ok(ids)
}

fn is_object_name(name: &str) -> bool {
    matches!(
        name,
        "equation"
            | "tbl"
            | "pic"
            | "rect"
            | "ellipse"
            | "line"
            | "arc"
            | "polygon"
            | "curve"
            | "connectLine"
            | "container"
            | "ole"
            | "video"
            | "textart"
    )
}

fn is_basic_shape_name(name: &str) -> bool {
    matches!(name, "line" | "rect" | "ellipse" | "polygon" | "curve")
}

fn is_direct_run_object(
    document: &PreservingXmlDocument,
    index: usize,
    candidate: &XmlElementToken,
) -> bool {
    if candidate.name().namespace() != Some(PARAGRAPH_NS)
        || !is_object_name(candidate.name().local_name())
    {
        return false;
    }
    candidate
        .parent()
        .and_then(|parent| document.elements().get(parent))
        .is_some_and(|parent| has_para_name(parent, "run"))
        && index < document.elements().len()
}

fn plan_digest(
    source: &BasicShapeHwpxSource,
    domain_plan_sha256: &str,
    limits: BasicShapeHwpxLimits,
) -> Result<String, BasicShapeHwpxError> {
    #[derive(Serialize)]
    struct Binding<'a> {
        profile_id: &'static str,
        source: &'a BasicShapeHwpxSource,
        domain_plan_sha256: &'a str,
    }
    Ok(hex(Sha256::digest(bounded_json(
        &Binding {
            profile_id: BASIC_SHAPE_HWPX_PROFILE_ID,
            source,
            domain_plan_sha256,
        },
        limits,
    )?)
    .into()))
}

fn shape_fragment(
    geometry: &ObjectGeometryState,
    shape: &BasicShape,
    limits: BasicShapeHwpxLimits,
) -> Result<Vec<u8>, BasicShapeHwpxError> {
    let mut xml = String::new();
    let (tag, extra_attributes) = match shape {
        BasicShape::Line { line } => (
            "line",
            format!(" isReverseHV=\"{}\"", bool01(line.is_reverse_hv)),
        ),
        BasicShape::Rectangle { rectangle } | BasicShape::TextBox { rectangle, .. } => {
            ("rect", format!(" ratio=\"{}\"", rectangle.ratio))
        }
        BasicShape::Ellipse { ellipse } => (
            "ellipse",
            format!(
                " intervalDirty=\"{}\" hasArcPr=\"{}\" arcType=\"{}\"",
                bool01(ellipse.interval_dirty),
                bool01(ellipse.has_arc_properties),
                ellipse_arc_type(ellipse.arc_type)
            ),
        ),
        BasicShape::Freeform {
            freeform: FreeformShape::Polygon { .. },
        } => ("polygon", String::new()),
        BasicShape::Freeform {
            freeform: FreeformShape::Curve { .. },
        } => ("curve", String::new()),
    };
    write!(
        xml,
        "<hp:{tag} xmlns:hp=\"{PARAGRAPH_NS}\" xmlns:hc=\"{CORE_NS}\" id=\"{}\" zOrder=\"{}\" numberingType=\"{}\" textWrap=\"{}\" textFlow=\"{}\" lock=\"{}\" dropcapstyle=\"None\" href=\"\" groupLevel=\"0\" instid=\"{}\"{extra_attributes}>",
        geometry.native_object_id(),
        geometry.z_order(),
        numbering_type(geometry.numbering_type()),
        text_wrap(geometry.wrap().text_wrap),
        text_flow(geometry.wrap().text_flow),
        bool01(geometry.locked()),
        geometry.native_instance_id(),
    )
    .map_err(|_| BasicShapeHwpxError::Allocation)?;
    write_common_component(&mut xml, geometry)?;
    write_shape_payload(&mut xml, shape)?;
    write_size_position_margin(&mut xml, geometry)?;
    write!(xml, "</hp:{tag}>").map_err(|_| BasicShapeHwpxError::Allocation)?;
    if xml.len() > limits.native.fragment_bytes {
        return Err(BasicShapeHwpxError::OutputLimit);
    }
    Ok(xml.into_bytes())
}

fn write_common_component(
    xml: &mut String,
    geometry: &ObjectGeometryState,
) -> Result<(), BasicShapeHwpxError> {
    let component = geometry.component();
    write!(
        xml,
        concat!(
            "<hp:offset x=\"{}\" y=\"{}\"/>",
            "<hp:orgSz width=\"{}\" height=\"{}\"/>",
            "<hp:curSz width=\"{}\" height=\"{}\"/>",
            "<hp:flip horizontal=\"{}\" vertical=\"{}\"/>",
            "<hp:rotationInfo angle=\"{}\" centerX=\"{}\" centerY=\"{}\" rotateimage=\"{}\"/>",
            "<hp:renderingInfo>"
        ),
        component.offset.x_hwpunit,
        component.offset.y_hwpunit,
        component.original_size.width_hwpunit,
        component.original_size.height_hwpunit,
        component.current_size.width_hwpunit,
        component.current_size.height_hwpunit,
        bool01(component.flip.horizontal),
        bool01(component.flip.vertical),
        component.rotation.angle_degrees,
        component.rotation.center_x_hwpunit,
        component.rotation.center_y_hwpunit,
        bool01(component.rotation.rotate_image),
    )
    .map_err(|_| BasicShapeHwpxError::Allocation)?;
    write_matrix(xml, "transMatrix", component.transform.translation)?;
    write_matrix(xml, "scaMatrix", component.transform.scale)?;
    write_matrix(xml, "rotMatrix", component.transform.rotation)?;
    xml.push_str("</hp:renderingInfo>");
    Ok(())
}

fn write_matrix(
    xml: &mut String,
    name: &str,
    matrix: ObjectAffineMatrix,
) -> Result<(), BasicShapeHwpxError> {
    write!(
        xml,
        "<hc:{name} e1=\"{}\" e2=\"{}\" e3=\"{}\" e4=\"{}\" e5=\"{}\" e6=\"{}\"/>",
        fixed_text(matrix.e1_millionths)?,
        fixed_text(matrix.e2_millionths)?,
        fixed_text(matrix.e3_millionths)?,
        fixed_text(matrix.e4_millionths)?,
        fixed_text(matrix.e5_millionths)?,
        fixed_text(matrix.e6_millionths)?,
    )
    .map_err(|_| BasicShapeHwpxError::Allocation)
}

fn write_shape_payload(xml: &mut String, shape: &BasicShape) -> Result<(), BasicShapeHwpxError> {
    match shape {
        BasicShape::Line { line } => {
            write_point(xml, "startPt", line.start)?;
            write_point(xml, "endPt", line.end)?;
        }
        BasicShape::Rectangle { rectangle } => write_rectangle_points(xml, rectangle)?,
        BasicShape::Ellipse { ellipse } => write_ellipse_points(xml, ellipse)?,
        BasicShape::TextBox { rectangle, content } => {
            write_rectangle_points(xml, rectangle)?;
            write_text_box(xml, content)?;
        }
        BasicShape::Freeform { freeform } => match freeform {
            FreeformShape::Polygon { points } => {
                for point in points {
                    write_point(xml, "pt", *point)?;
                }
            }
            FreeformShape::Curve { segments } => {
                for segment in segments {
                    write_segment(xml, *segment)?;
                }
            }
        },
    }
    Ok(())
}

fn write_rectangle_points(
    xml: &mut String,
    rectangle: &RectangleShape,
) -> Result<(), BasicShapeHwpxError> {
    for (name, point) in ["pt0", "pt1", "pt2", "pt3"]
        .into_iter()
        .zip(rectangle.corners)
    {
        write_point(xml, name, point)?;
    }
    Ok(())
}

fn write_ellipse_points(
    xml: &mut String,
    ellipse: &EllipseShape,
) -> Result<(), BasicShapeHwpxError> {
    for (name, point) in [
        ("center", ellipse.center),
        ("ax1", ellipse.axis_1),
        ("ax2", ellipse.axis_2),
        ("start1", ellipse.start_1),
        ("start2", ellipse.start_2),
        ("end1", ellipse.end_1),
        ("end2", ellipse.end_2),
    ] {
        write_point(xml, name, point)?;
    }
    Ok(())
}

fn write_point(xml: &mut String, name: &str, point: ShapePoint) -> Result<(), BasicShapeHwpxError> {
    write!(
        xml,
        "<hc:{name} x=\"{}\" y=\"{}\"/>",
        point.x_hwpunit, point.y_hwpunit
    )
    .map_err(|_| BasicShapeHwpxError::Allocation)
}

fn write_segment(xml: &mut String, segment: CurveSegment) -> Result<(), BasicShapeHwpxError> {
    write!(
        xml,
        "<hp:seg type=\"{}\" x1=\"{}\" y1=\"{}\" x2=\"{}\" y2=\"{}\"/>",
        segment_type(segment.segment_type),
        segment.x1_hwpunit,
        segment.y1_hwpunit,
        segment.x2_hwpunit,
        segment.y2_hwpunit,
    )
    .map_err(|_| BasicShapeHwpxError::Allocation)
}

fn write_text_box(xml: &mut String, content: &TextBoxContent) -> Result<(), BasicShapeHwpxError> {
    let name = escape_xml_attribute(&content.name)?;
    let text = escape_xml_text(&content.text)?;
    write!(
        xml,
        concat!(
            "<hp:drawText lastWidth=\"{}\" name=\"{}\" editable=\"{}\">",
            "<hp:textMargin left=\"{}\" right=\"{}\" top=\"{}\" bottom=\"{}\"/>",
            "<hp:subList id=\"{}\" textDirection=\"HORIZONTAL\" lineWrap=\"BREAK\" vertAlign=\"{}\" ",
            "linkListIDRef=\"0\" linkListNextIDRef=\"0\" textWidth=\"{}\" textHeight=\"{}\" hasTextRef=\"0\" hasNumRef=\"0\">",
            "<hp:p id=\"{}\" paraPrIDRef=\"{}\" styleIDRef=\"{}\" pageBreak=\"0\" columnBreak=\"0\" merged=\"0\">",
            "<hp:run charPrIDRef=\"{}\"><hp:t>{}</hp:t></hp:run></hp:p></hp:subList></hp:drawText>"
        ),
        content.last_width_hwpunit,
        name,
        bool01(content.editable),
        content.margins.left_hwpunit,
        content.margins.right_hwpunit,
        content.margins.top_hwpunit,
        content.margins.bottom_hwpunit,
        content.sublist_id,
        text_vertical_alignment(content.vertical_alignment),
        content.text_width_hwpunit,
        content.text_height_hwpunit,
        content.paragraph_id,
        content.paragraph_properties_id,
        content.style_id,
        content.character_properties_id,
        text,
    )
    .map_err(|_| BasicShapeHwpxError::Allocation)
}

fn write_size_position_margin(
    xml: &mut String,
    geometry: &ObjectGeometryState,
) -> Result<(), BasicShapeHwpxError> {
    let size = geometry.size();
    let anchor = geometry.anchor();
    let position = geometry.position();
    let margin = geometry.outer_margins();
    write!(
        xml,
        concat!(
            "<hp:sz width=\"{}\" widthRelTo=\"{}\" height=\"{}\" heightRelTo=\"{}\" protect=\"{}\"/>",
            "<hp:pos treatAsChar=\"{}\" affectLSpacing=\"{}\" flowWithText=\"{}\" allowOverlap=\"{}\" holdAnchorAndSO=\"{}\" ",
            "vertRelTo=\"{}\" horzRelTo=\"{}\" vertAlign=\"{}\" horzAlign=\"{}\" vertOffset=\"{}\" horzOffset=\"{}\"/>",
            "<hp:outMargin left=\"{}\" right=\"{}\" top=\"{}\" bottom=\"{}\"/>"
        ),
        size.width_hwpunit,
        width_reference(size.width_reference),
        size.height_hwpunit,
        height_reference(size.height_reference),
        bool01(size.protect),
        bool01(anchor.treat_as_character),
        bool01(anchor.affect_line_spacing),
        bool01(anchor.flow_with_text),
        bool01(anchor.allow_overlap),
        bool01(anchor.hold_anchor_and_shape),
        vertical_reference(anchor.vertical_reference),
        horizontal_reference(anchor.horizontal_reference),
        vertical_alignment(position.vertical_alignment),
        horizontal_alignment(position.horizontal_alignment),
        position.vertical_offset_hwpunit,
        position.horizontal_offset_hwpunit,
        margin.left_hwpunit,
        margin.right_hwpunit,
        margin.top_hwpunit,
        margin.bottom_hwpunit,
    )
    .map_err(|_| BasicShapeHwpxError::Allocation)
}

#[allow(clippy::too_many_arguments, clippy::too_many_lines)]
fn read_shape(
    bytes: &[u8],
    object_ordinal: usize,
    logical_object_id: LogicalId,
    expected_shape: &BasicShape,
    shape_limits: BasicShapeLimits,
    geometry_limits: ObjectGeometryLimits,
    geometry_hwpx_limits: ObjectGeometryHwpxLimits,
    limits: BasicShapeHwpxLimits,
) -> Result<ParsedShape, BasicShapeHwpxError> {
    let document = parse_section(bytes, limits)?;
    let object_indexes = document
        .elements()
        .iter()
        .enumerate()
        .filter(|(index, candidate)| is_direct_run_object(&document, *index, candidate))
        .map(|(index, _)| index)
        .collect::<Vec<_>>();
    let root_index = *object_indexes
        .get(object_ordinal)
        .ok_or(BasicShapeHwpxError::UnsupportedTarget)?;
    let root = element(&document, root_index)?;
    if !is_basic_shape_name(root.name().local_name()) {
        return Err(BasicShapeHwpxError::ReadbackMismatch);
    }
    let geometry = ObjectGeometryHwpxReader::read_in_section(
        bytes,
        object_ordinal,
        logical_object_id,
        geometry_limits,
        geometry_hwpx_limits,
    )?
    .state;
    expected_shape.validate_for_geometry(&geometry, shape_limits)?;
    validate_root_attributes(root, expected_shape)?;
    let shape = read_shape_payload(&document, root_index, expected_shape, shape_limits, limits)?;
    shape.validate_for_geometry(&geometry, shape_limits)?;
    if shape != *expected_shape {
        return Err(BasicShapeHwpxError::ReadbackMismatch);
    }
    let sets = collect_native_ids(&document, limits)?;
    let shape_span = root
        .outer_span()
        .ok_or(BasicShapeHwpxError::ReadbackMismatch)?;
    if shape.text_box_content().is_some_and(|content| {
        content.text.len() > shape_limits.config().text_bytes
            || content.name.len() > shape_limits.config().name_bytes
    }) {
        return Err(BasicShapeHwpxError::InputLimit);
    }
    let readback = BasicShapeHwpxReadback {
        profile_id: BASIC_SHAPE_HWPX_PROFILE_ID,
        geometry,
        shape,
        object_count: sets.object_ids.len(),
        instance_count: sets.instance_ids.len(),
        shape_count: sets.shape_count,
        paragraph_count: sets.paragraph_ids.len(),
        sublist_count: sets.sublist_ids.len(),
    };
    Ok(ParsedShape {
        readback,
        shape_span,
    })
}

fn validate_root_attributes(
    root: &XmlElementToken,
    expected: &BasicShape,
) -> Result<(), BasicShapeHwpxError> {
    let common = [
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
    ];
    let mut allowed = common.to_vec();
    match expected {
        BasicShape::Line { .. } => allowed.push("isReverseHV"),
        BasicShape::Rectangle { .. } | BasicShape::TextBox { .. } => allowed.push("ratio"),
        BasicShape::Ellipse { .. } => allowed.extend(["intervalDirty", "hasArcPr", "arcType"]),
        BasicShape::Freeform { .. } => {}
    }
    validate_attributes(root, &allowed)?;
    require_attr(root, "dropcapstyle", "None")?;
    require_attr(root, "href", "")?;
    require_attr(root, "groupLevel", "0")?;
    Ok(())
}

fn read_shape_payload(
    document: &PreservingXmlDocument,
    root: usize,
    expected: &BasicShape,
    shape_limits: BasicShapeLimits,
    limits: BasicShapeHwpxLimits,
) -> Result<BasicShape, BasicShapeHwpxError> {
    let children = child_indexes(document, root)?;
    let common_prefix = [
        "offset",
        "orgSz",
        "curSz",
        "flip",
        "rotationInfo",
        "renderingInfo",
    ];
    let common_suffix = ["sz", "pos", "outMargin"];
    if children.len() < common_prefix.len() + common_suffix.len()
        || children
            .iter()
            .take(common_prefix.len())
            .zip(common_prefix)
            .any(|(index, name)| !has_para_name(&document.elements()[*index], name))
        || children
            .iter()
            .rev()
            .take(common_suffix.len())
            .zip(common_suffix.into_iter().rev())
            .any(|(index, name)| !has_para_name(&document.elements()[*index], name))
    {
        return Err(BasicShapeHwpxError::ReadbackMismatch);
    }
    let payload = &children[common_prefix.len()..children.len() - common_suffix.len()];
    match expected {
        BasicShape::Line { .. } => {
            if payload.len() != 2 {
                return Err(BasicShapeHwpxError::ReadbackMismatch);
            }
            Ok(BasicShape::Line {
                line: LineShape {
                    is_reverse_hv: bool_attr(element(document, root)?, "isReverseHV")?,
                    start: read_point(document, payload[0], "startPt")?,
                    end: read_point(document, payload[1], "endPt")?,
                },
            })
        }
        BasicShape::Rectangle { .. } => {
            if payload.len() != 4 {
                return Err(BasicShapeHwpxError::ReadbackMismatch);
            }
            Ok(BasicShape::Rectangle {
                rectangle: read_rectangle(document, root, payload)?,
            })
        }
        BasicShape::Ellipse { .. } => {
            if payload.len() != 7 {
                return Err(BasicShapeHwpxError::ReadbackMismatch);
            }
            Ok(BasicShape::Ellipse {
                ellipse: read_ellipse(document, root, payload)?,
            })
        }
        BasicShape::TextBox { .. } => {
            if payload.len() != 5 || !has_para_name(element(document, payload[4])?, "drawText") {
                return Err(BasicShapeHwpxError::ReadbackMismatch);
            }
            Ok(BasicShape::TextBox {
                rectangle: read_rectangle(document, root, &payload[..4])?,
                content: read_text_box(document, payload[4], shape_limits, limits)?,
            })
        }
        BasicShape::Freeform {
            freeform: FreeformShape::Polygon { .. },
        } => {
            if payload.len() < 3 || payload.len() > shape_limits.config().points {
                return Err(BasicShapeHwpxError::InputLimit);
            }
            let mut points = Vec::new();
            points
                .try_reserve_exact(payload.len())
                .map_err(|_| BasicShapeHwpxError::Allocation)?;
            for index in payload {
                points.push(read_point(document, *index, "pt")?);
            }
            Ok(BasicShape::Freeform {
                freeform: FreeformShape::Polygon { points },
            })
        }
        BasicShape::Freeform {
            freeform: FreeformShape::Curve { .. },
        } => {
            if payload.is_empty() || payload.len() > shape_limits.config().segments {
                return Err(BasicShapeHwpxError::InputLimit);
            }
            let mut segments = Vec::new();
            segments
                .try_reserve_exact(payload.len())
                .map_err(|_| BasicShapeHwpxError::Allocation)?;
            for index in payload {
                segments.push(read_segment(document, *index)?);
            }
            Ok(BasicShape::Freeform {
                freeform: FreeformShape::Curve { segments },
            })
        }
    }
}

fn read_rectangle(
    document: &PreservingXmlDocument,
    root: usize,
    payload: &[usize],
) -> Result<RectangleShape, BasicShapeHwpxError> {
    let corners = [
        read_point(document, payload[0], "pt0")?,
        read_point(document, payload[1], "pt1")?,
        read_point(document, payload[2], "pt2")?,
        read_point(document, payload[3], "pt3")?,
    ];
    Ok(RectangleShape {
        ratio: parse_u32(attr(element(document, root)?, "ratio")?)?,
        corners,
    })
}

fn read_ellipse(
    document: &PreservingXmlDocument,
    root: usize,
    payload: &[usize],
) -> Result<EllipseShape, BasicShapeHwpxError> {
    let root = element(document, root)?;
    Ok(EllipseShape {
        interval_dirty: bool_attr(root, "intervalDirty")?,
        has_arc_properties: bool_attr(root, "hasArcPr")?,
        arc_type: match attr(root, "arcType")? {
            "NORMAL" => EllipseArcType::Normal,
            "PIE" => EllipseArcType::Pie,
            "CHORD" => EllipseArcType::Chord,
            _ => return Err(BasicShapeHwpxError::ReadbackMismatch),
        },
        center: read_point(document, payload[0], "center")?,
        axis_1: read_point(document, payload[1], "ax1")?,
        axis_2: read_point(document, payload[2], "ax2")?,
        start_1: read_point(document, payload[3], "start1")?,
        start_2: read_point(document, payload[4], "start2")?,
        end_1: read_point(document, payload[5], "end1")?,
        end_2: read_point(document, payload[6], "end2")?,
    })
}

fn read_point(
    document: &PreservingXmlDocument,
    index: usize,
    expected_name: &str,
) -> Result<ShapePoint, BasicShapeHwpxError> {
    let point = element(document, index)?;
    if !has_core_name(point, expected_name) || !point.is_empty() {
        return Err(BasicShapeHwpxError::ReadbackMismatch);
    }
    validate_attributes(point, &["x", "y"])?;
    Ok(ShapePoint {
        x_hwpunit: parse_i32(attr(point, "x")?)?,
        y_hwpunit: parse_i32(attr(point, "y")?)?,
    })
}

fn read_segment(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<CurveSegment, BasicShapeHwpxError> {
    let segment = element(document, index)?;
    if !has_para_name(segment, "seg") || !segment.is_empty() {
        return Err(BasicShapeHwpxError::ReadbackMismatch);
    }
    validate_attributes(segment, &["type", "x1", "y1", "x2", "y2"])?;
    Ok(CurveSegment {
        segment_type: match attr(segment, "type")? {
            "LINE" => CurveSegmentType::Line,
            "CURVE" => CurveSegmentType::Curve,
            _ => return Err(BasicShapeHwpxError::ReadbackMismatch),
        },
        x1_hwpunit: parse_i32(attr(segment, "x1")?)?,
        y1_hwpunit: parse_i32(attr(segment, "y1")?)?,
        x2_hwpunit: parse_i32(attr(segment, "x2")?)?,
        y2_hwpunit: parse_i32(attr(segment, "y2")?)?,
    })
}

#[allow(clippy::too_many_lines)]
fn read_text_box(
    document: &PreservingXmlDocument,
    draw_text_index: usize,
    shape_limits: BasicShapeLimits,
    limits: BasicShapeHwpxLimits,
) -> Result<TextBoxContent, BasicShapeHwpxError> {
    let draw_text = element(document, draw_text_index)?;
    validate_attributes(draw_text, &["lastWidth", "name", "editable"])?;
    let children = child_indexes(document, draw_text_index)?;
    if children.len() != 2
        || !has_para_name(element(document, children[0])?, "textMargin")
        || !has_para_name(element(document, children[1])?, "subList")
    {
        return Err(BasicShapeHwpxError::ReadbackMismatch);
    }
    let margin = element(document, children[0])?;
    if !margin.is_empty() {
        return Err(BasicShapeHwpxError::ReadbackMismatch);
    }
    validate_attributes(margin, &["left", "right", "top", "bottom"])?;
    let sublist = element(document, children[1])?;
    validate_attributes(
        sublist,
        &[
            "id",
            "textDirection",
            "lineWrap",
            "vertAlign",
            "linkListIDRef",
            "linkListNextIDRef",
            "textWidth",
            "textHeight",
            "hasTextRef",
            "hasNumRef",
        ],
    )?;
    for (name, value) in [
        ("textDirection", "HORIZONTAL"),
        ("lineWrap", "BREAK"),
        ("linkListIDRef", "0"),
        ("linkListNextIDRef", "0"),
        ("hasTextRef", "0"),
        ("hasNumRef", "0"),
    ] {
        require_attr(sublist, name, value)?;
    }
    let paragraphs = child_indexes(document, children[1])?;
    if paragraphs.len() != 1 || !has_para_name(element(document, paragraphs[0])?, "p") {
        return Err(BasicShapeHwpxError::ReadbackMismatch);
    }
    let paragraph = element(document, paragraphs[0])?;
    validate_attributes(
        paragraph,
        &[
            "id",
            "paraPrIDRef",
            "styleIDRef",
            "pageBreak",
            "columnBreak",
            "merged",
        ],
    )?;
    for name in ["pageBreak", "columnBreak", "merged"] {
        require_attr(paragraph, name, "0")?;
    }
    let runs = child_indexes(document, paragraphs[0])?;
    if runs.len() != 1 || !has_para_name(element(document, runs[0])?, "run") {
        return Err(BasicShapeHwpxError::ReadbackMismatch);
    }
    let run = element(document, runs[0])?;
    validate_attributes(run, &["charPrIDRef"])?;
    let texts = child_indexes(document, runs[0])?;
    if texts.len() != 1 || !has_para_name(element(document, texts[0])?, "t") {
        return Err(BasicShapeHwpxError::ReadbackMismatch);
    }
    let text = element_text(
        document,
        texts[0],
        shape_limits
            .config()
            .text_bytes
            .min(limits.native.fragment_bytes),
    )?;
    let vertical_alignment = match attr(sublist, "vertAlign")? {
        "TOP" => TextBoxVerticalAlignment::Top,
        "CENTER" => TextBoxVerticalAlignment::Center,
        "BOTTOM" => TextBoxVerticalAlignment::Bottom,
        _ => return Err(BasicShapeHwpxError::ReadbackMismatch),
    };
    Ok(TextBoxContent {
        last_width_hwpunit: parse_u32(attr(draw_text, "lastWidth")?)?,
        name: attr(draw_text, "name")?.to_owned(),
        editable: bool_attr(draw_text, "editable")?,
        margins: domain_ir::TextBoxMargins {
            left_hwpunit: parse_u32(attr(margin, "left")?)?,
            right_hwpunit: parse_u32(attr(margin, "right")?)?,
            top_hwpunit: parse_u32(attr(margin, "top")?)?,
            bottom_hwpunit: parse_u32(attr(margin, "bottom")?)?,
        },
        sublist_id: parse_u32(attr(sublist, "id")?)?,
        paragraph_id: parse_u32(attr(paragraph, "id")?)?,
        paragraph_properties_id: parse_u32(attr(paragraph, "paraPrIDRef")?)?,
        style_id: parse_u32(attr(paragraph, "styleIDRef")?)?,
        character_properties_id: parse_u32(attr(run, "charPrIDRef")?)?,
        text_width_hwpunit: parse_u32(attr(sublist, "textWidth")?)?,
        text_height_hwpunit: parse_u32(attr(sublist, "textHeight")?)?,
        vertical_alignment,
        text,
    })
}

fn read_spine_part<R: Read + Seek>(
    reader: &mut BoundedZipReader<R>,
    graph: &PackageGraph,
    section_part: &str,
    limits: BasicShapeHwpxLimits,
) -> Result<(PackagePath, Vec<u8>), BasicShapeHwpxError> {
    let path = PackagePath::parse(section_part.as_bytes(), 0, limits.package)?;
    let record = graph
        .parts
        .iter()
        .find(|record| record.path == path)
        .ok_or(BasicShapeHwpxError::UnsupportedTarget)?;
    if record.role != PartRole::SpineDocument || !graph.spine.iter().any(|value| value == &path) {
        return Err(BasicShapeHwpxError::UnsupportedTarget);
    }
    let entry = reader
        .entries()
        .iter()
        .find(|entry| entry.path == record.path)
        .map(|entry| entry.index)
        .ok_or(BasicShapeHwpxError::SourceDrift)?;
    let bytes = reader.read_entry(entry)?;
    if bytes.len() > limits.native.section_bytes
        || <[u8; 32]>::from(Sha256::digest(&bytes)) != record.raw_sha256
    {
        return Err(BasicShapeHwpxError::SourceDrift);
    }
    Ok((path, bytes))
}

fn parse_section(
    bytes: &[u8],
    limits: BasicShapeHwpxLimits,
) -> Result<PreservingXmlDocument, BasicShapeHwpxError> {
    if bytes.is_empty() || bytes.len() > limits.native.section_bytes {
        return Err(BasicShapeHwpxError::InputLimit);
    }
    let document = PreservingXmlDocument::parse(bytes)?;
    if document.elements().len() > limits.native.elements {
        return Err(BasicShapeHwpxError::InputLimit);
    }
    Ok(document)
}

fn element(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<&XmlElementToken, BasicShapeHwpxError> {
    document
        .elements()
        .get(index)
        .ok_or(BasicShapeHwpxError::UnsupportedTarget)
}

fn child_indexes(
    document: &PreservingXmlDocument,
    parent: usize,
) -> Result<Vec<usize>, BasicShapeHwpxError> {
    let mut output = Vec::new();
    let mut current = element(document, parent)?.first_child();
    while let Some(index) = current {
        output
            .try_reserve(1)
            .map_err(|_| BasicShapeHwpxError::Allocation)?;
        output.push(index);
        current = element(document, index)?.next_sibling();
    }
    Ok(output)
}

fn direct_children_named(
    document: &PreservingXmlDocument,
    parent: usize,
    local_name: &str,
) -> Result<Vec<usize>, BasicShapeHwpxError> {
    Ok(child_indexes(document, parent)?
        .into_iter()
        .filter(|index| {
            element(document, *index).is_ok_and(|value| has_para_name(value, local_name))
        })
        .collect())
}

fn has_para_name(element: &XmlElementToken, local_name: &str) -> bool {
    element.name().namespace() == Some(PARAGRAPH_NS) && element.name().local_name() == local_name
}

fn has_core_name(element: &XmlElementToken, local_name: &str) -> bool {
    element.name().namespace() == Some(CORE_NS) && element.name().local_name() == local_name
}

fn validate_attributes(
    element: &XmlElementToken,
    allowed: &[&str],
) -> Result<(), BasicShapeHwpxError> {
    let mut seen = BTreeSet::new();
    for attribute in element.attributes() {
        if attribute.is_namespace_declaration() {
            continue;
        }
        let name = attribute.name().local_name();
        if attribute.name().namespace().is_some() || !allowed.contains(&name) || !seen.insert(name)
        {
            return Err(BasicShapeHwpxError::ReadbackMismatch);
        }
    }
    if seen.len() != allowed.len() {
        return Err(BasicShapeHwpxError::ReadbackMismatch);
    }
    Ok(())
}

fn optional_attr<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<Option<&'a str>, BasicShapeHwpxError> {
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
        return Err(BasicShapeHwpxError::ReadbackMismatch);
    }
    Ok(value)
}

fn attr<'a>(element: &'a XmlElementToken, name: &str) -> Result<&'a str, BasicShapeHwpxError> {
    optional_attr(element, name)?.ok_or(BasicShapeHwpxError::ReadbackMismatch)
}

fn require_attr(
    element: &XmlElementToken,
    name: &str,
    expected: &str,
) -> Result<(), BasicShapeHwpxError> {
    if attr(element, name)? != expected {
        return Err(BasicShapeHwpxError::ReadbackMismatch);
    }
    Ok(())
}

fn bool_attr(element: &XmlElementToken, name: &str) -> Result<bool, BasicShapeHwpxError> {
    match attr(element, name)? {
        "0" => Ok(false),
        "1" => Ok(true),
        _ => Err(BasicShapeHwpxError::ReadbackMismatch),
    }
}

fn parse_u32(value: &str) -> Result<u32, BasicShapeHwpxError> {
    if !canonical_unsigned(value) {
        return Err(BasicShapeHwpxError::ReadbackMismatch);
    }
    value
        .parse()
        .map_err(|_| BasicShapeHwpxError::ReadbackMismatch)
}

fn parse_i32(value: &str) -> Result<i32, BasicShapeHwpxError> {
    if value.is_empty()
        || value.starts_with('+')
        || (value.starts_with('0') && value.len() > 1)
        || (value.starts_with("-0"))
        || !match value.strip_prefix('-') {
            Some(rest) => rest,
            None => value,
        }
        .bytes()
        .all(|byte| byte.is_ascii_digit())
    {
        return Err(BasicShapeHwpxError::ReadbackMismatch);
    }
    value
        .parse()
        .map_err(|_| BasicShapeHwpxError::ReadbackMismatch)
}

fn canonical_unsigned(value: &str) -> bool {
    !value.is_empty()
        && value.bytes().all(|byte| byte.is_ascii_digit())
        && (value == "0" || !value.starts_with('0'))
}

fn element_text(
    document: &PreservingXmlDocument,
    index: usize,
    maximum: usize,
) -> Result<String, BasicShapeHwpxError> {
    let element = element(document, index)?;
    if element.first_child().is_some() {
        return Err(BasicShapeHwpxError::ReadbackMismatch);
    }
    let span = element
        .content_span()
        .ok_or(BasicShapeHwpxError::ReadbackMismatch)?;
    let raw = document.source_text(span)?;
    if raw.len() > maximum {
        return Err(BasicShapeHwpxError::InputLimit);
    }
    decode_xml_text(raw)
}

fn decode_xml_text(value: &str) -> Result<String, BasicShapeHwpxError> {
    if value.contains("&#") {
        return Err(BasicShapeHwpxError::ReadbackMismatch);
    }
    Ok(value
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", "\"")
        .replace("&apos;", "'")
        .replace("&amp;", "&"))
}

fn escape_xml_text(value: &str) -> Result<String, BasicShapeHwpxError> {
    if value.chars().any(invalid_xml_character) {
        return Err(BasicShapeHwpxError::ReadbackMismatch);
    }
    Ok(value
        .replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;"))
}

fn escape_xml_attribute(value: &str) -> Result<String, BasicShapeHwpxError> {
    Ok(escape_xml_text(value)?
        .replace('"', "&quot;")
        .replace('\'', "&apos;"))
}

fn invalid_xml_character(character: char) -> bool {
    !matches!(character, '\u{9}' | '\u{a}' | '\u{d}')
        && !('\u{20}'..='\u{d7ff}').contains(&character)
        && !('\u{e000}'..='\u{fffd}').contains(&character)
        && !('\u{10000}'..='\u{10ffff}').contains(&character)
}

fn package_state_sha256(graph: &PackageGraph) -> String {
    let mut digest = Sha256::new();
    digest.update(BASIC_SHAPE_HWPX_PROFILE_ID.as_bytes());
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
    digest.update(BASIC_SHAPE_HWPX_PROFILE_ID.as_bytes());
    digest.update(b"\0");
    digest.update(domain.as_bytes());
    for id in ids {
        digest.update(id.to_be_bytes());
    }
    hex(digest.finalize().into())
}

fn bounded_json<T: Serialize>(
    value: &T,
    limits: BasicShapeHwpxLimits,
) -> Result<Vec<u8>, BasicShapeHwpxError> {
    let bytes = serde_json::to_vec(value).map_err(|_| BasicShapeHwpxError::OutputLimit)?;
    if bytes.len() > limits.native.serialized_bytes {
        return Err(BasicShapeHwpxError::OutputLimit);
    }
    Ok(bytes)
}

fn fixed_text(value: i64) -> Result<String, BasicShapeHwpxError> {
    let negative = value.is_negative();
    let magnitude = value
        .checked_abs()
        .ok_or(BasicShapeHwpxError::OutputLimit)?;
    let whole = magnitude / FIXED_SCALE;
    let fraction = magnitude % FIXED_SCALE;
    let mut output = if fraction == 0 {
        whole.to_string()
    } else {
        let mut digits = format!("{fraction:06}");
        while digits.ends_with('0') {
            let _ = digits.pop();
        }
        format!("{whole}.{digits}")
    };
    if negative && magnitude != 0 {
        output.insert(0, '-');
    }
    Ok(output)
}

const fn bool01(value: bool) -> &'static str {
    if value { "1" } else { "0" }
}

const fn numbering_type(value: ObjectNumberingType) -> &'static str {
    match value {
        ObjectNumberingType::None => "NONE",
        ObjectNumberingType::Picture => "PICTURE",
        ObjectNumberingType::Table => "TABLE",
        ObjectNumberingType::Equation => "EQUATION",
    }
}

const fn text_wrap(value: ObjectTextWrap) -> &'static str {
    match value {
        ObjectTextWrap::Square => "SQUARE",
        ObjectTextWrap::TopAndBottom => "TOP_AND_BOTTOM",
        ObjectTextWrap::BehindText => "BEHIND_TEXT",
        ObjectTextWrap::InFrontOfText => "IN_FRONT_OF_TEXT",
    }
}

const fn text_flow(value: ObjectTextFlow) -> &'static str {
    match value {
        ObjectTextFlow::BothSides => "BOTH_SIDES",
        ObjectTextFlow::LeftOnly => "LEFT_ONLY",
        ObjectTextFlow::RightOnly => "RIGHT_ONLY",
        ObjectTextFlow::LargestOnly => "LARGEST_ONLY",
    }
}

const fn horizontal_reference(value: ObjectHorizontalReference) -> &'static str {
    match value {
        ObjectHorizontalReference::Paper => "PAPER",
        ObjectHorizontalReference::Page => "PAGE",
        ObjectHorizontalReference::Column => "COLUMN",
        ObjectHorizontalReference::Paragraph => "PARA",
    }
}

const fn vertical_reference(value: ObjectVerticalReference) -> &'static str {
    match value {
        ObjectVerticalReference::Paper => "PAPER",
        ObjectVerticalReference::Page => "PAGE",
        ObjectVerticalReference::Paragraph => "PARA",
    }
}

const fn horizontal_alignment(value: ObjectHorizontalAlignment) -> &'static str {
    match value {
        ObjectHorizontalAlignment::Left => "LEFT",
        ObjectHorizontalAlignment::Center => "CENTER",
        ObjectHorizontalAlignment::Right => "RIGHT",
        ObjectHorizontalAlignment::Inside => "INSIDE",
        ObjectHorizontalAlignment::Outside => "OUTSIDE",
    }
}

const fn vertical_alignment(value: ObjectVerticalAlignment) -> &'static str {
    match value {
        ObjectVerticalAlignment::Top => "TOP",
        ObjectVerticalAlignment::Center => "CENTER",
        ObjectVerticalAlignment::Bottom => "BOTTOM",
        ObjectVerticalAlignment::Inside => "INSIDE",
        ObjectVerticalAlignment::Outside => "OUTSIDE",
    }
}

const fn width_reference(value: ObjectWidthReference) -> &'static str {
    match value {
        ObjectWidthReference::Paper => "PAPER",
        ObjectWidthReference::Page => "PAGE",
        ObjectWidthReference::Column => "COLUMN",
        ObjectWidthReference::Paragraph => "PARA",
        ObjectWidthReference::Absolute => "ABSOLUTE",
    }
}

const fn height_reference(value: ObjectHeightReference) -> &'static str {
    match value {
        ObjectHeightReference::Paper => "PAPER",
        ObjectHeightReference::Page => "PAGE",
        ObjectHeightReference::Absolute => "ABSOLUTE",
    }
}

const fn ellipse_arc_type(value: EllipseArcType) -> &'static str {
    match value {
        EllipseArcType::Normal => "NORMAL",
        EllipseArcType::Pie => "PIE",
        EllipseArcType::Chord => "CHORD",
    }
}

const fn segment_type(value: CurveSegmentType) -> &'static str {
    match value {
        CurveSegmentType::Line => "LINE",
        CurveSegmentType::Curve => "CURVE",
    }
}

const fn text_vertical_alignment(value: TextBoxVerticalAlignment) -> &'static str {
    match value {
        TextBoxVerticalAlignment::Top => "TOP",
        TextBoxVerticalAlignment::Center => "CENTER",
        TextBoxVerticalAlignment::Bottom => "BOTTOM",
    }
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
