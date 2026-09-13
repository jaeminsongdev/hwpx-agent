use std::collections::{BTreeMap, BTreeSet};
use std::fmt::{self, Write as _};
use std::io::{Read, Seek};

use domain_ir::{
    FormulaDecimal, TABLE_CHART_FROM_TABLE_CAPABILITY_ID, TableChartLimits, TableChartPlan,
    TableChartSourceState, TableChartValue, TableChartValueOrigin,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{
    AddedPart, BoundedZipReader, GraphError, IdIndexLimits, IdRuleProfile, PackageError,
    PackageGraph, PackageGraphLimits, PackageLimits, PackagePath, PartRole, PatchError,
    PatchIntent, PatchLimits, PatchPartDisposition, PatchResult, PreservationRuleProfile,
    PreservingPatchEngine, PreservingXmlDocument, PreservingXmlError, RelationshipAddition,
    RelationshipKind, RelationshipSpine, SiblingPosition, TableRulingHwpxBinding,
    TableRulingHwpxError, TableRulingHwpxLimits, TableRulingHwpxReader, ValidatedXmlFragment,
    XmlElementSelector, XmlElementToken,
};

pub const TABLE_CHART_HWPX_SCHEMA_VERSION: &str = "hwpx-agent.table-chart-hwpx/v1";
pub const TABLE_CHART_HWPX_PROFILE_ID: &str =
    "hwpx-agent.table-chart-hwpx.hancom-2020-ooxml-chart/1";

const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const SECTION_NS: &str = "http://www.hancom.co.kr/hwpml/2011/section";
const OPF_NS: &str = "http://www.idpf.org/2007/opf";
const HEADER_PART: &str = "Contents/header.xml";
const CHART_MEDIA_TYPE: &str = "application/xml";
const CHART_WIDTH_HWPUNIT: u32 = 32_250;
const CHART_HEIGHT_HWPUNIT: u32 = 18_750;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TableChartHwpxLimitConfig {
    pub section_bytes: usize,
    pub chart_bytes: usize,
    pub serialized_bytes: usize,
    pub elements: usize,
    pub charts: usize,
    pub identifiers_bytes: usize,
}

impl Default for TableChartHwpxLimitConfig {
    fn default() -> Self {
        Self {
            section_bytes: 32 * 1024 * 1024,
            chart_bytes: 16 * 1024 * 1024,
            serialized_bytes: 32 * 1024 * 1024,
            elements: 1_000_000,
            charts: 65_536,
            identifiers_bytes: 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TableChartHwpxLimits {
    native: TableChartHwpxLimitConfig,
    pub package: PackageLimits,
    pub graph: PackageGraphLimits,
    pub ids: IdIndexLimits,
    pub patch: PatchLimits,
    pub ruling: TableRulingHwpxLimits,
}

impl TableChartHwpxLimits {
    pub const HARD_MAX_SECTION_BYTES: usize = 128 * 1024 * 1024;
    pub const HARD_MAX_CHART_BYTES: usize = 64 * 1024 * 1024;
    pub const HARD_MAX_SERIALIZED_BYTES: usize = 128 * 1024 * 1024;
    pub const HARD_MAX_ELEMENTS: usize = 2_000_000;
    pub const HARD_MAX_CHARTS: usize = 262_144;
    pub const HARD_MAX_IDENTIFIER_BYTES: usize = 64 * 1024;

    /// Creates finite bounds for the direct OOXML-chart adapter.
    ///
    /// # Errors
    ///
    /// Rejects zero or over-ceiling native bounds.
    pub fn new(
        native: TableChartHwpxLimitConfig,
        package: PackageLimits,
        graph: PackageGraphLimits,
        ids: IdIndexLimits,
        patch: PatchLimits,
        ruling: TableRulingHwpxLimits,
    ) -> Result<Self, TableChartHwpxError> {
        if native.section_bytes == 0
            || native.section_bytes > Self::HARD_MAX_SECTION_BYTES
            || native.chart_bytes == 0
            || native.chart_bytes > Self::HARD_MAX_CHART_BYTES
            || native.serialized_bytes == 0
            || native.serialized_bytes > Self::HARD_MAX_SERIALIZED_BYTES
            || native.elements == 0
            || native.elements > Self::HARD_MAX_ELEMENTS
            || native.charts == 0
            || native.charts > Self::HARD_MAX_CHARTS
            || native.identifiers_bytes == 0
            || native.identifiers_bytes > Self::HARD_MAX_IDENTIFIER_BYTES
        {
            return Err(TableChartHwpxError::InvalidLimit);
        }
        Ok(Self {
            native,
            package,
            graph,
            ids,
            patch,
            ruling,
        })
    }

    #[must_use]
    pub const fn config(self) -> TableChartHwpxLimitConfig {
        self.native
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableChartHwpxSource {
    profile_id: &'static str,
    section_part: String,
    table_ordinal: usize,
    package_state_sha256: String,
    section_sha256: String,
    table_sha256: String,
    source_state_sha256: String,
    source_grid_sha256: String,
    source_table_state_sha256: String,
    native_table_id: u32,
    next_native_chart_id: u32,
    next_z_order: u32,
    next_chart_part: String,
    source_chart_count: usize,
}

impl TableChartHwpxSource {
    #[must_use]
    pub fn section_part(&self) -> &str {
        &self.section_part
    }

    #[must_use]
    pub const fn table_ordinal(&self) -> usize {
        self.table_ordinal
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
    pub fn table_sha256(&self) -> &str {
        &self.table_sha256
    }

    #[must_use]
    pub fn source_state_sha256(&self) -> &str {
        &self.source_state_sha256
    }

    #[must_use]
    pub fn source_grid_sha256(&self) -> &str {
        &self.source_grid_sha256
    }

    #[must_use]
    pub fn source_table_state_sha256(&self) -> &str {
        &self.source_table_state_sha256
    }

    #[must_use]
    pub const fn native_table_id(&self) -> u32 {
        self.native_table_id
    }

    #[must_use]
    pub const fn next_native_chart_id(&self) -> u32 {
        self.next_native_chart_id
    }

    #[must_use]
    pub const fn next_z_order(&self) -> u32 {
        self.next_z_order
    }

    #[must_use]
    pub fn next_chart_part(&self) -> &str {
        &self.next_chart_part
    }

    #[must_use]
    pub const fn source_chart_count(&self) -> usize {
        self.source_chart_count
    }
}

#[allow(clippy::missing_fields_in_debug)]
impl fmt::Debug for TableChartHwpxSource {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableChartHwpxSource")
            .field("profile_id", &self.profile_id)
            .field("table_ordinal", &self.table_ordinal)
            .field("source_chart_count", &self.source_chart_count)
            .field("bindings", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableChartHwpxRequestDraft {
    pub schema_version: String,
    pub profile_id: String,
    pub section_part: String,
    pub table_ordinal: usize,
    pub expected_package_state_sha256: String,
    pub expected_section_sha256: String,
    pub expected_table_sha256: String,
    pub expected_source_state_sha256: String,
    pub expected_source_grid_sha256: String,
    pub expected_source_table_state_sha256: String,
    pub expected_plan_sha256: String,
    pub expected_document_flow_sha256: String,
    pub target_document_flow_sha256: String,
    pub native_chart_id: u32,
    pub z_order: u32,
    pub chart_part: String,
    pub manifest_item_id: String,
}

#[allow(clippy::missing_fields_in_debug)]
impl fmt::Debug for TableChartHwpxRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableChartHwpxRequestDraft")
            .field("schema_version", &self.schema_version)
            .field("profile_id", &self.profile_id)
            .field("table_ordinal", &self.table_ordinal)
            .field("native_chart_id", &"<redacted>")
            .field("z_order", &self.z_order)
            .field("bindings", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableChartHwpxRequest {
    schema_version: &'static str,
    profile_id: &'static str,
    section_part: String,
    table_ordinal: usize,
    expected_package_state_sha256: String,
    expected_section_sha256: String,
    expected_table_sha256: String,
    expected_source_state_sha256: String,
    expected_source_grid_sha256: String,
    expected_source_table_state_sha256: String,
    expected_plan_sha256: String,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    native_chart_id: u32,
    z_order: u32,
    chart_part: String,
    manifest_item_id: String,
}

impl TableChartHwpxRequest {
    /// Binds an exact domain plan to one fully inspected native table and resource allocation.
    ///
    /// # Errors
    ///
    /// Rejects stale source, plan, flow, identifier, path, or allocation bindings.
    pub fn from_draft(
        draft: TableChartHwpxRequestDraft,
        source: &TableChartHwpxSource,
        plan: &TableChartPlan,
        current_document_flow_sha256: &str,
        limits: TableChartHwpxLimits,
        chart_limits: TableChartLimits,
    ) -> Result<Self, TableChartHwpxError> {
        if draft.schema_version != TABLE_CHART_HWPX_SCHEMA_VERSION {
            return Err(TableChartHwpxError::UnsupportedVersion);
        }
        if draft.profile_id != TABLE_CHART_HWPX_PROFILE_ID {
            return Err(TableChartHwpxError::UnsupportedProfile);
        }
        validate_digest(current_document_flow_sha256)?;
        for digest in [
            &draft.expected_package_state_sha256,
            &draft.expected_section_sha256,
            &draft.expected_table_sha256,
            &draft.expected_source_state_sha256,
            &draft.expected_source_grid_sha256,
            &draft.expected_source_table_state_sha256,
            &draft.expected_plan_sha256,
            &draft.expected_document_flow_sha256,
            &draft.target_document_flow_sha256,
        ] {
            validate_digest(digest)?;
        }
        validate_manifest_id(&draft.manifest_item_id, &limits)?;
        let plan_sha256 = hex(plan.canonical_sha256(chart_limits)?);
        if draft.section_part != source.section_part
            || draft.table_ordinal != source.table_ordinal
            || draft.expected_package_state_sha256 != source.package_state_sha256
            || draft.expected_section_sha256 != source.section_sha256
            || draft.expected_table_sha256 != source.table_sha256
            || draft.expected_source_state_sha256 != source.source_state_sha256
            || draft.expected_source_grid_sha256 != source.source_grid_sha256
            || draft.expected_source_table_state_sha256 != source.source_table_state_sha256
            || draft.expected_plan_sha256 != plan_sha256
            || draft.expected_document_flow_sha256 != current_document_flow_sha256
            || draft.expected_document_flow_sha256 == draft.target_document_flow_sha256
        {
            return Err(TableChartHwpxError::RequestBindingMismatch);
        }
        if draft.native_chart_id != source.next_native_chart_id
            || draft.native_chart_id == source.native_table_id
            || draft.z_order != source.next_z_order
            || draft.chart_part != source.next_chart_part
            || draft.manifest_item_id != plan.data_resource_id().as_str()
        {
            return Err(TableChartHwpxError::AllocationDrift);
        }
        validate_chart_part(&draft.chart_part, &limits)?;
        let request = Self {
            schema_version: TABLE_CHART_HWPX_SCHEMA_VERSION,
            profile_id: TABLE_CHART_HWPX_PROFILE_ID,
            section_part: draft.section_part,
            table_ordinal: draft.table_ordinal,
            expected_package_state_sha256: draft.expected_package_state_sha256,
            expected_section_sha256: draft.expected_section_sha256,
            expected_table_sha256: draft.expected_table_sha256,
            expected_source_state_sha256: draft.expected_source_state_sha256,
            expected_source_grid_sha256: draft.expected_source_grid_sha256,
            expected_source_table_state_sha256: draft.expected_source_table_state_sha256,
            expected_plan_sha256: draft.expected_plan_sha256,
            expected_document_flow_sha256: draft.expected_document_flow_sha256,
            target_document_flow_sha256: draft.target_document_flow_sha256,
            native_chart_id: draft.native_chart_id,
            z_order: draft.z_order,
            chart_part: draft.chart_part,
            manifest_item_id: draft.manifest_item_id,
        };
        let _ = request.canonical_json(limits)?;
        Ok(request)
    }

    /// Parses duplicate-key and unknown-field rejecting bounded JSON.
    ///
    /// # Errors
    ///
    /// Applies the same validation as [`Self::from_draft`].
    pub fn from_json(
        bytes: &[u8],
        source: &TableChartHwpxSource,
        plan: &TableChartPlan,
        current_document_flow_sha256: &str,
        limits: TableChartHwpxLimits,
        chart_limits: TableChartLimits,
    ) -> Result<Self, TableChartHwpxError> {
        if bytes.is_empty() || bytes.len() > limits.native.serialized_bytes {
            return Err(TableChartHwpxError::InputLimit);
        }
        reject_duplicate_json_keys(bytes)?;
        let draft = serde_json::from_slice(bytes).map_err(|_| TableChartHwpxError::InvalidJson)?;
        Self::from_draft(
            draft,
            source,
            plan,
            current_document_flow_sha256,
            limits,
            chart_limits,
        )
    }

    #[must_use]
    pub fn chart_part(&self) -> &str {
        &self.chart_part
    }

    #[must_use]
    pub fn manifest_item_id(&self) -> &str {
        &self.manifest_item_id
    }

    #[must_use]
    pub const fn native_chart_id(&self) -> u32 {
        self.native_chart_id
    }

    /// Emits canonical bounded request JSON.
    ///
    /// # Errors
    ///
    /// Returns an error when serialization fails or exceeds the configured bound.
    pub fn canonical_json(
        &self,
        limits: TableChartHwpxLimits,
    ) -> Result<Vec<u8>, TableChartHwpxError> {
        bounded_json(self, &limits)
    }
}

#[allow(clippy::missing_fields_in_debug)]
impl fmt::Debug for TableChartHwpxRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableChartHwpxRequest")
            .field("schema_version", &self.schema_version)
            .field("profile_id", &self.profile_id)
            .field("table_ordinal", &self.table_ordinal)
            .field("z_order", &self.z_order)
            .field("bindings", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableChartHwpxReadback {
    pub profile_id: &'static str,
    pub chart_part_sha256: [u8; 32],
    pub chart_object_sha256: [u8; 32],
    pub native_chart_id: u32,
    pub z_order: u32,
    pub series_count: usize,
    pub category_count: usize,
    pub data_point_count: u64,
    pub blank_data_point_count: u64,
    pub chart_count: usize,
}

#[allow(clippy::missing_fields_in_debug)]
impl fmt::Debug for TableChartHwpxReadback {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableChartHwpxReadback")
            .field("profile_id", &self.profile_id)
            .field("native_chart_id", &"<redacted>")
            .field("z_order", &self.z_order)
            .field("series_count", &self.series_count)
            .field("category_count", &self.category_count)
            .field("data_point_count", &self.data_point_count)
            .field("blank_data_point_count", &self.blank_data_point_count)
            .field("chart_count", &self.chart_count)
            .finish()
    }
}

#[allow(clippy::struct_excessive_bools)]
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableChartHwpxLoweringReceipt {
    profile_id: &'static str,
    capability_id: &'static str,
    request_sha256: String,
    plan_sha256: String,
    source_package_state_sha256: String,
    source_section_sha256: String,
    output_section_sha256: String,
    source_table_sha256: String,
    source_state_sha256: String,
    source_grid_sha256: String,
    source_table_state_sha256: String,
    chart_part_sha256: String,
    chart_object_sha256: String,
    chart_logical_id_sha256: String,
    data_resource_logical_id_sha256: String,
    before_document_flow_sha256: String,
    after_document_flow_sha256: String,
    native_chart_id: u32,
    z_order: u32,
    source_chart_count: usize,
    output_chart_count: usize,
    changed_parts: usize,
    added_parts: usize,
    untouched_parts: usize,
    source_table_preserved: bool,
    static_readback_verified: bool,
    relationship_closure_verified: bool,
    render_required: bool,
}

impl TableChartHwpxLoweringReceipt {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
    }

    #[must_use]
    pub const fn source_table_preserved(&self) -> bool {
        self.source_table_preserved
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
    pub const fn output_chart_count(&self) -> usize {
        self.output_chart_count
    }

    /// Emits deterministic bounded receipt JSON.
    ///
    /// # Errors
    ///
    /// Returns an error when serialization fails or exceeds the configured bound.
    pub fn canonical_json(
        &self,
        limits: TableChartHwpxLimits,
    ) -> Result<Vec<u8>, TableChartHwpxError> {
        bounded_json(self, &limits)
    }
}

#[allow(clippy::missing_fields_in_debug)]
impl fmt::Debug for TableChartHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableChartHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field("capability_id", &self.capability_id)
            .field("native_chart_id", &"<redacted>")
            .field("z_order", &self.z_order)
            .field("source_chart_count", &self.source_chart_count)
            .field("output_chart_count", &self.output_chart_count)
            .field("changed_parts", &self.changed_parts)
            .field("added_parts", &self.added_parts)
            .field("untouched_parts", &self.untouched_parts)
            .field("source_table_preserved", &self.source_table_preserved)
            .field("static_readback_verified", &self.static_readback_verified)
            .field(
                "relationship_closure_verified",
                &self.relationship_closure_verified,
            )
            .field("render_required", &self.render_required)
            .field("digests", &"<redacted>")
            .finish()
    }
}

pub struct TableChartHwpxLowered {
    patch: PatchResult,
    receipt: TableChartHwpxLoweringReceipt,
}

impl TableChartHwpxLowered {
    #[must_use]
    pub const fn patch(&self) -> &PatchResult {
        &self.patch
    }

    #[must_use]
    pub const fn receipt(&self) -> &TableChartHwpxLoweringReceipt {
        &self.receipt
    }

    #[must_use]
    pub fn into_patch(self) -> PatchResult {
        self.patch
    }
}

impl fmt::Debug for TableChartHwpxLowered {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableChartHwpxLowered")
            .field("patch", &self.patch)
            .field("receipt", &self.receipt)
            .finish()
    }
}

#[derive(Debug)]
pub struct TableChartHwpxBuilder;

impl TableChartHwpxBuilder {
    /// Inspects the exact package, selected native table, complete grid/state and every cell value.
    ///
    /// # Errors
    ///
    /// Rejects graph, table, cell, formula-cache, digest, identifier and finite-limit drift.
    #[allow(clippy::too_many_arguments)]
    pub fn inspect_source<R: Read + Seek>(
        reader: &mut BoundedZipReader<R>,
        graph: &PackageGraph,
        section_part: &str,
        table_ordinal: usize,
        binding: &TableRulingHwpxBinding,
        state: &TableChartSourceState,
        limits: TableChartHwpxLimits,
        chart_limits: TableChartLimits,
    ) -> Result<TableChartHwpxSource, TableChartHwpxError> {
        inspect_bound_source(
            reader,
            graph,
            section_part,
            table_ordinal,
            binding,
            state,
            &limits,
            chart_limits,
        )
        .map(|bound| bound.source)
    }
}

#[derive(Debug)]
pub struct TableChartHwpxReader;

impl TableChartHwpxReader {
    /// Strictly reads the deterministic direct chart object and OOXML chart part.
    ///
    /// # Errors
    ///
    /// Rejects any object, path, chart type, cache, count, resource, or ordering drift.
    pub fn read_from_parts(
        section: &[u8],
        chart_part: &[u8],
        request: &TableChartHwpxRequest,
        plan: &TableChartPlan,
        expected_chart_ordinal: usize,
        limits: TableChartHwpxLimits,
        chart_limits: TableChartLimits,
    ) -> Result<TableChartHwpxReadback, TableChartHwpxError> {
        read_chart_parts(
            section,
            chart_part,
            request,
            plan,
            expected_chart_ordinal,
            &limits,
            chart_limits,
        )
    }
}

#[derive(Debug)]
pub struct TableChartHwpxLowerer;

impl TableChartHwpxLowerer {
    /// Inserts one direct `hp:chart`, its closed manifest relationship and deterministic OOXML part.
    ///
    /// # Errors
    ///
    /// Rechecks source/state/grid/flow/plan bindings and returns no partial artifact unless strict
    /// semantic readback plus byte preservation and package closure all pass.
    #[allow(clippy::too_many_arguments, clippy::too_many_lines)]
    pub fn lower<R: Read + Seek>(
        reader: &mut BoundedZipReader<R>,
        graph: &PackageGraph,
        request: &TableChartHwpxRequest,
        binding: &TableRulingHwpxBinding,
        state: &TableChartSourceState,
        plan: &TableChartPlan,
        current_document_flow_sha256: &str,
        limits: TableChartHwpxLimits,
        chart_limits: TableChartLimits,
    ) -> Result<TableChartHwpxLowered, TableChartHwpxError> {
        let bound = inspect_bound_source(
            reader,
            graph,
            &request.section_part,
            request.table_ordinal,
            binding,
            state,
            &limits,
            chart_limits,
        )?;
        validate_request_against_source(
            request,
            &bound.source,
            plan,
            current_document_flow_sha256,
            chart_limits,
        )?;
        validate_plan_cells(plan, state, &bound.native_cells, chart_limits)?;

        let chart_bytes = chart_xml(plan, &limits, chart_limits)?;
        let chart_fragment = chart_fragment(request, &limits)?;
        let fragment = ValidatedXmlFragment::parse(&chart_fragment, limits.patch)?;
        let selector = XmlElementSelector::bind(&bound.path, &bound.document, bound.table_index)?;
        let relationship = RelationshipAddition::new(
            &request.manifest_item_id,
            &request.chart_part,
            CHART_MEDIA_TYPE,
            RelationshipSpine::NotInSpine,
            limits.package,
            limits.graph,
            limits.patch,
        )?;
        let part = AddedPart::xml(
            &request.chart_part,
            CHART_MEDIA_TYPE,
            &chart_bytes,
            limits.package,
            limits.graph,
            limits.patch,
        )?;
        let intents = [
            PatchIntent::InsertSibling {
                target: selector,
                position: SiblingPosition::After,
                fragment,
            },
            PatchIntent::AddRelationship { relationship },
            PatchIntent::AddPart { part },
        ];
        let original_manifest = read_exact_part(
            reader,
            graph,
            graph.package_document.as_str(),
            &limits,
            limits.native.section_bytes,
        )?;
        let patch = PreservingPatchEngine::apply_with_limits_and_preservation_profile(
            reader,
            graph,
            limits.graph,
            IdRuleProfile::hwpml_2016_ooxml_chart_v7(),
            limits.ids,
            limits.patch,
            PreservationRuleProfile::Hangul2020PreviewTextV2,
            &intents,
        )?;
        patch.verify_artifact_integrity()?;
        if patch.intent_count() != 3
            || patch.changed_parts() != 2
            || patch.added_parts() != 1
            || patch.relationship_count() != 1
        {
            return Err(TableChartHwpxError::PreservationMismatch);
        }
        let output_section = patch_part(&patch, bound.path.as_str())?;
        let output_chart = patch_part(&patch, &request.chart_part)?;
        let readback = read_chart_parts(
            &output_section.bytes,
            &output_chart.bytes,
            request,
            plan,
            bound.source.source_chart_count,
            &limits,
            chart_limits,
        )?;
        let restored = remove_span(
            &output_section.bytes,
            readback_span(
                &output_section.bytes,
                request,
                bound.source.source_chart_count,
                &limits,
            )?,
        )?;
        if restored != bound.bytes {
            return Err(TableChartHwpxError::PreservationMismatch);
        }
        verify_manifest_and_preservation(
            &patch,
            &graph.package_document,
            request,
            &original_manifest,
        )?;
        verify_unrelated_parts(&patch, &bound.path, graph, request)?;

        let receipt = TableChartHwpxLoweringReceipt {
            profile_id: TABLE_CHART_HWPX_PROFILE_ID,
            capability_id: TABLE_CHART_FROM_TABLE_CAPABILITY_ID,
            request_sha256: hex(Sha256::digest(request.canonical_json(limits)?).into()),
            plan_sha256: hex(plan.canonical_sha256(chart_limits)?),
            source_package_state_sha256: bound.source.package_state_sha256,
            source_section_sha256: bound.source.section_sha256,
            output_section_sha256: hex(Sha256::digest(&output_section.bytes).into()),
            source_table_sha256: bound.source.table_sha256,
            source_state_sha256: bound.source.source_state_sha256,
            source_grid_sha256: bound.source.source_grid_sha256,
            source_table_state_sha256: bound.source.source_table_state_sha256,
            chart_part_sha256: hex(readback.chart_part_sha256),
            chart_object_sha256: hex(readback.chart_object_sha256),
            chart_logical_id_sha256: hex(Sha256::digest(plan.chart_id().as_str()).into()),
            data_resource_logical_id_sha256: hex(
                Sha256::digest(plan.data_resource_id().as_str()).into()
            ),
            before_document_flow_sha256: request.expected_document_flow_sha256.clone(),
            after_document_flow_sha256: request.target_document_flow_sha256.clone(),
            native_chart_id: request.native_chart_id,
            z_order: request.z_order,
            source_chart_count: bound.source.source_chart_count,
            output_chart_count: readback.chart_count,
            changed_parts: patch.changed_parts(),
            added_parts: patch.added_parts(),
            untouched_parts: patch.untouched_parts(),
            source_table_preserved: true,
            static_readback_verified: true,
            relationship_closure_verified: true,
            render_required: true,
        };
        let _ = receipt.canonical_json(limits)?;
        Ok(TableChartHwpxLowered { patch, receipt })
    }
}

#[derive(Debug, Error)]
pub enum TableChartHwpxError {
    #[error("table-chart HWPX limit configuration is invalid")]
    InvalidLimit,
    #[error("table-chart HWPX input is empty or exceeds its finite bound")]
    InputLimit,
    #[error("table-chart HWPX JSON is malformed, duplicated, or not strict")]
    InvalidJson,
    #[error("table-chart HWPX request schema is unsupported")]
    UnsupportedVersion,
    #[error("table-chart HWPX native profile is unsupported")]
    UnsupportedProfile,
    #[error("table-chart HWPX digest binding is invalid")]
    InvalidDigest,
    #[error("table-chart HWPX selected table or source state is unsupported")]
    UnsupportedSource,
    #[error("table-chart HWPX request does not match the current source or plan")]
    RequestBindingMismatch,
    #[error("table-chart HWPX native chart identifier, z-order or part allocation drifted")]
    AllocationDrift,
    #[error("table-chart HWPX document flow drifted")]
    FlowDrift,
    #[error("table-chart HWPX source cell value or provenance differs from native bytes")]
    SourceCellMismatch,
    #[error("table-chart HWPX output chart or cache differs from the plan")]
    ReadbackMismatch,
    #[error("table-chart HWPX chart relationship or resource is not closed")]
    RelationshipMismatch,
    #[error("table-chart HWPX changed bytes outside the intended object/relationship/resource")]
    PreservationMismatch,
    #[error("table-chart HWPX result exceeds its finite bound")]
    OutputLimit,
    #[error("table-chart HWPX serialization failed")]
    Serialization,
    #[error("table-chart HWPX allocation failed")]
    Allocation,
    #[error("bounded package read failed")]
    Package(#[from] PackageError),
    #[error("closed package graph validation failed")]
    Graph(#[from] GraphError),
    #[error("preserving XML validation failed")]
    Xml(#[from] PreservingXmlError),
    #[error("preserving package patch failed")]
    Patch(#[from] PatchError),
    #[error("table ruling admission failed")]
    Ruling(#[from] TableRulingHwpxError),
    #[error("table chart domain plan failed")]
    Domain(#[from] domain_ir::TableChartError),
    #[error("table grid digest failed")]
    Grid(#[from] domain_ir::TableGridError),
    #[error("table ruling state digest failed")]
    RulingState(#[from] domain_ir::TableRulingError),
}

impl TableChartHwpxError {
    #[must_use]
    pub fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "table_chart_hwpx_invalid_limit",
            Self::InputLimit => "table_chart_hwpx_input_limit",
            Self::InvalidJson => "table_chart_hwpx_invalid_json",
            Self::UnsupportedVersion => "table_chart_hwpx_unsupported_version",
            Self::UnsupportedProfile => "table_chart_hwpx_unsupported_profile",
            Self::InvalidDigest => "table_chart_hwpx_invalid_digest",
            Self::UnsupportedSource => "table_chart_hwpx_unsupported_source",
            Self::RequestBindingMismatch => "table_chart_hwpx_request_binding_mismatch",
            Self::AllocationDrift => "table_chart_hwpx_allocation_drift",
            Self::FlowDrift => "table_chart_hwpx_flow_drift",
            Self::SourceCellMismatch => "table_chart_hwpx_source_cell_mismatch",
            Self::ReadbackMismatch => "table_chart_hwpx_readback_mismatch",
            Self::RelationshipMismatch => "table_chart_hwpx_relationship_mismatch",
            Self::PreservationMismatch => "table_chart_hwpx_preservation_mismatch",
            Self::OutputLimit => "table_chart_hwpx_output_limit",
            Self::Serialization => "table_chart_hwpx_serialization",
            Self::Allocation => "table_chart_hwpx_allocation",
            Self::Package(error) => error.code(),
            Self::Graph(error) => error.code(),
            Self::Xml(error) => error.code(),
            Self::Patch(error) => error.code(),
            Self::Ruling(error) => error.code(),
            Self::Domain(_) => "table_chart_hwpx_domain",
            Self::Grid(error) => error.code(),
            Self::RulingState(error) => error.code(),
        }
    }
}

struct BoundSource {
    source: TableChartHwpxSource,
    path: PackagePath,
    bytes: Vec<u8>,
    document: PreservingXmlDocument,
    table_index: usize,
    native_cells: BTreeMap<(u32, u32), NativeCell>,
}

struct NativeCell {
    sha256: String,
    display: String,
    formula_sha256: Option<String>,
    cache_sha256: Option<String>,
}

#[allow(clippy::too_many_arguments, clippy::too_many_lines)]
fn inspect_bound_source<R: Read + Seek>(
    reader: &mut BoundedZipReader<R>,
    graph: &PackageGraph,
    section_part: &str,
    table_ordinal: usize,
    binding: &TableRulingHwpxBinding,
    state: &TableChartSourceState,
    limits: &TableChartHwpxLimits,
    chart_limits: TableChartLimits,
) -> Result<BoundSource, TableChartHwpxError> {
    if state.table_id() != &binding.table_id {
        return Err(TableChartHwpxError::UnsupportedSource);
    }
    let path = PackagePath::parse(section_part.as_bytes(), 0, limits.package)?;
    let record = graph
        .parts
        .iter()
        .find(|part| part.path == path)
        .ok_or(TableChartHwpxError::UnsupportedSource)?;
    if record.role != PartRole::SpineDocument || !graph.spine.iter().any(|value| value == &path) {
        return Err(TableChartHwpxError::UnsupportedSource);
    }
    let bytes = read_exact_part(
        reader,
        graph,
        section_part,
        limits,
        limits.native.section_bytes,
    )?;
    let header = read_exact_part(
        reader,
        graph,
        HEADER_PART,
        limits,
        limits.native.section_bytes,
    )?;
    let readback = TableRulingHwpxReader::read_existing(
        &header,
        &bytes,
        table_ordinal,
        binding,
        limits.ruling,
    )?;
    let grid_sha256 = hex(readback.grid.canonical_sha256()?);
    let table_state_sha256 = hex(readback.state.canonical_sha256(limits.ruling.ruling)?);
    let source_state_sha256 = hex(state.canonical_sha256(chart_limits)?);
    if state.grid_sha256() != grid_sha256 || state.table_state_sha256() != table_state_sha256 {
        return Err(TableChartHwpxError::UnsupportedSource);
    }

    let document = parse_section(&bytes, limits)?;
    let root = element(&document, document.root_element())?;
    if root.name().namespace() != Some(SECTION_NS) || root.name().local_name() != "sec" {
        return Err(TableChartHwpxError::UnsupportedSource);
    }
    let tables = indexes_named(&document, "tbl");
    let table_index = *tables
        .get(table_ordinal)
        .ok_or(TableChartHwpxError::UnsupportedSource)?;
    let table = element(&document, table_index)?;
    let table_parent = table
        .parent()
        .ok_or(TableChartHwpxError::UnsupportedSource)?;
    if !has_name(element(&document, table_parent)?, "run") {
        return Err(TableChartHwpxError::UnsupportedSource);
    }
    let table_span = table
        .outer_span()
        .ok_or(TableChartHwpxError::UnsupportedSource)?;
    let native_table_id = parse_u32(attr(table, "id")?)?;
    let native_cells = native_cells(&document, table_index, limits)?;
    if native_cells.len() != state.cells().len() {
        return Err(TableChartHwpxError::SourceCellMismatch);
    }
    for cell in state.cells() {
        let native = native_cells
            .get(&(cell.coordinate().row, cell.coordinate().column))
            .ok_or(TableChartHwpxError::SourceCellMismatch)?;
        validate_native_cell(native, cell)?;
    }

    let (object_ids, max_z_order, package_chart_count) =
        package_object_state(reader, graph, limits)?;
    if package_chart_count >= limits.native.charts {
        return Err(TableChartHwpxError::InputLimit);
    }
    let source_chart_count = indexes_named(&document, "chart").len();
    let next_native_chart_id = object_ids
        .iter()
        .next_back()
        .copied()
        .unwrap_or(0)
        .checked_add(1)
        .ok_or(TableChartHwpxError::AllocationDrift)?;
    if next_native_chart_id == 0 {
        return Err(TableChartHwpxError::AllocationDrift);
    }
    let next_z_order = max_z_order
        .checked_add(1)
        .ok_or(TableChartHwpxError::AllocationDrift)?;
    let next_chart_part = next_chart_part(graph, limits)?;
    let source = TableChartHwpxSource {
        profile_id: TABLE_CHART_HWPX_PROFILE_ID,
        section_part: path.as_str().to_owned(),
        table_ordinal,
        package_state_sha256: package_state_sha256(graph),
        section_sha256: hex(Sha256::digest(&bytes).into()),
        table_sha256: hex(Sha256::digest(document.source_text(table_span)?.as_bytes()).into()),
        source_state_sha256,
        source_grid_sha256: grid_sha256,
        source_table_state_sha256: table_state_sha256,
        native_table_id,
        next_native_chart_id,
        next_z_order,
        next_chart_part,
        source_chart_count,
    };
    Ok(BoundSource {
        source,
        path,
        bytes,
        document,
        table_index,
        native_cells,
    })
}

fn validate_native_cell(
    native: &NativeCell,
    cell: &domain_ir::TableChartCell,
) -> Result<(), TableChartHwpxError> {
    if native.sha256 != cell.source_sha256() {
        return Err(TableChartHwpxError::SourceCellMismatch);
    }
    let value_matches = match cell.value() {
        TableChartValue::Blank => native.display.is_empty(),
        TableChartValue::Text { value } => &native.display == value,
        TableChartValue::Number { value } => decimal_display_matches(&native.display, *value),
    };
    if !value_matches {
        return Err(TableChartHwpxError::SourceCellMismatch);
    }
    match cell.value_origin() {
        TableChartValueOrigin::Literal
            if native.formula_sha256.is_none() && native.cache_sha256.is_none() => {}
        TableChartValueOrigin::FormulaDisplayCache {
            formula_sha256,
            cache_sha256,
        } if native.formula_sha256.as_ref() == Some(formula_sha256)
            && native.cache_sha256.as_ref() == Some(cache_sha256) => {}
        _ => return Err(TableChartHwpxError::SourceCellMismatch),
    }
    Ok(())
}

fn validate_plan_cells(
    plan: &TableChartPlan,
    state: &TableChartSourceState,
    native_cells: &BTreeMap<(u32, u32), NativeCell>,
    chart_limits: TableChartLimits,
) -> Result<(), TableChartHwpxError> {
    if plan.table_id() != state.table_id()
        || plan.receipt().source_state_sha256_before != hex(state.canonical_sha256(chart_limits)?)
    {
        return Err(TableChartHwpxError::RequestBindingMismatch);
    }
    for category in plan.categories() {
        let native = native_cells
            .get(&(category.coordinate().row, category.coordinate().column))
            .ok_or(TableChartHwpxError::SourceCellMismatch)?;
        if native.sha256 != category.source_sha256() || native.display != category.label() {
            return Err(TableChartHwpxError::SourceCellMismatch);
        }
    }
    for series in plan.series() {
        let header = native_cells
            .get(&(
                series.header_coordinate().row,
                series.header_coordinate().column,
            ))
            .ok_or(TableChartHwpxError::SourceCellMismatch)?;
        if header.sha256 != series.header_source_sha256() || header.display != series.label() {
            return Err(TableChartHwpxError::SourceCellMismatch);
        }
        for value in series.values() {
            let native = native_cells
                .get(&(value.coordinate().row, value.coordinate().column))
                .ok_or(TableChartHwpxError::SourceCellMismatch)?;
            if native.sha256 != value.source_sha256()
                || value
                    .value()
                    .is_some_and(|number| !decimal_display_matches(&native.display, number))
                || value.value().is_none() != native.display.is_empty()
            {
                return Err(TableChartHwpxError::SourceCellMismatch);
            }
        }
    }
    Ok(())
}

fn validate_request_against_source(
    request: &TableChartHwpxRequest,
    source: &TableChartHwpxSource,
    plan: &TableChartPlan,
    current_document_flow_sha256: &str,
    chart_limits: TableChartLimits,
) -> Result<(), TableChartHwpxError> {
    validate_digest(current_document_flow_sha256)?;
    if request.section_part != source.section_part
        || request.table_ordinal != source.table_ordinal
        || request.expected_package_state_sha256 != source.package_state_sha256
        || request.expected_section_sha256 != source.section_sha256
        || request.expected_table_sha256 != source.table_sha256
        || request.expected_source_state_sha256 != source.source_state_sha256
        || request.expected_source_grid_sha256 != source.source_grid_sha256
        || request.expected_source_table_state_sha256 != source.source_table_state_sha256
        || request.expected_plan_sha256 != hex(plan.canonical_sha256(chart_limits)?)
    {
        return Err(TableChartHwpxError::RequestBindingMismatch);
    }
    if request.expected_document_flow_sha256 != current_document_flow_sha256
        || request.expected_document_flow_sha256 == request.target_document_flow_sha256
    {
        return Err(TableChartHwpxError::FlowDrift);
    }
    if request.native_chart_id != source.next_native_chart_id
        || request.z_order != source.next_z_order
        || request.chart_part != source.next_chart_part
        || request.manifest_item_id != plan.data_resource_id().as_str()
    {
        return Err(TableChartHwpxError::AllocationDrift);
    }
    Ok(())
}

fn native_cells(
    document: &PreservingXmlDocument,
    table_index: usize,
    limits: &TableChartHwpxLimits,
) -> Result<BTreeMap<(u32, u32), NativeCell>, TableChartHwpxError> {
    let mut output = BTreeMap::new();
    for (index, candidate) in document.elements().iter().enumerate() {
        if !has_name(candidate, "tc") || !is_descendant_of(document, index, table_index)? {
            continue;
        }
        if has_ancestor_between(document, index, table_index, "tbl")? {
            continue;
        }
        let address = child_named(document, index, "cellAddr")?
            .ok_or(TableChartHwpxError::UnsupportedSource)?;
        let row = parse_u32(attr(element(document, address)?, "rowAddr")?)?;
        let column = parse_u32(attr(element(document, address)?, "colAddr")?)?;
        let span = candidate
            .outer_span()
            .ok_or(TableChartHwpxError::UnsupportedSource)?;
        let raw = document.source_text(span)?;
        let display = cell_display_text(document, index, limits)?;
        let formula_elements = descendant_indexes_named(document, index, "fieldBegin")?;
        let (formula_sha256, cache_sha256) = if formula_elements.is_empty() {
            (None, None)
        } else {
            let mut digest = Sha256::new();
            digest.update(TABLE_CHART_HWPX_PROFILE_ID.as_bytes());
            digest.update(b"\0formula-origin\0");
            for formula in formula_elements {
                let formula_span = element(document, formula)?
                    .outer_span()
                    .ok_or(TableChartHwpxError::UnsupportedSource)?;
                digest.update(document.source_text(formula_span)?.as_bytes());
            }
            let mut cache = Sha256::new();
            cache.update(TABLE_CHART_HWPX_PROFILE_ID.as_bytes());
            cache.update(b"\0formula-display-cache\0");
            cache.update(display.as_bytes());
            (
                Some(hex(digest.finalize().into())),
                Some(hex(cache.finalize().into())),
            )
        };
        let cell = NativeCell {
            sha256: hex(Sha256::digest(raw.as_bytes()).into()),
            display,
            formula_sha256,
            cache_sha256,
        };
        if output.insert((row, column), cell).is_some() || output.len() > limits.native.elements {
            return Err(TableChartHwpxError::UnsupportedSource);
        }
    }
    Ok(output)
}

fn cell_display_text(
    document: &PreservingXmlDocument,
    cell: usize,
    limits: &TableChartHwpxLimits,
) -> Result<String, TableChartHwpxError> {
    let mut output = String::new();
    for text in descendant_indexes_named(document, cell, "t")? {
        if has_ancestor_between(document, text, cell, "tbl")? {
            return Err(TableChartHwpxError::UnsupportedSource);
        }
        let element = element(document, text)?;
        if element.first_child().is_some() {
            return Err(TableChartHwpxError::UnsupportedSource);
        }
        let span = element
            .content_span()
            .ok_or(TableChartHwpxError::UnsupportedSource)?;
        let decoded = decode_xml_text(document.source_text(span)?)?;
        output
            .try_reserve(decoded.len())
            .map_err(|_| TableChartHwpxError::Allocation)?;
        output.push_str(&decoded);
        if output.len() > limits.native.identifiers_bytes {
            return Err(TableChartHwpxError::InputLimit);
        }
    }
    Ok(output)
}

fn chart_fragment(
    request: &TableChartHwpxRequest,
    limits: &TableChartHwpxLimits,
) -> Result<Vec<u8>, TableChartHwpxError> {
    let chart_part = escape_xml_attribute(&request.chart_part)?;
    let xml = format!(
        concat!(
            "<hp:chart xmlns:hp=\"{ns}\" id=\"{id}\" zOrder=\"{z}\" ",
            "numberingType=\"PICTURE\" textWrap=\"SQUARE\" textFlow=\"BOTH_SIDES\" ",
            "lock=\"0\" dropcapstyle=\"None\" chartIDRef=\"{part}\">",
            "<hp:sz width=\"{width}\" widthRelTo=\"ABSOLUTE\" height=\"{height}\" ",
            "heightRelTo=\"ABSOLUTE\" protect=\"0\"/>",
            "<hp:pos treatAsChar=\"0\" affectLSpacing=\"0\" flowWithText=\"1\" ",
            "allowOverlap=\"0\" holdAnchorAndSO=\"0\" vertRelTo=\"PARA\" ",
            "horzRelTo=\"COLUMN\" vertAlign=\"TOP\" horzAlign=\"LEFT\" ",
            "vertOffset=\"0\" horzOffset=\"0\"/>",
            "<hp:outMargin left=\"0\" right=\"0\" top=\"0\" bottom=\"0\"/>",
            "</hp:chart>"
        ),
        ns = PARAGRAPH_NS,
        id = request.native_chart_id,
        z = request.z_order,
        part = chart_part,
        width = CHART_WIDTH_HWPUNIT,
        height = CHART_HEIGHT_HWPUNIT,
    );
    if xml.len() > limits.native.serialized_bytes {
        return Err(TableChartHwpxError::OutputLimit);
    }
    Ok(xml.into_bytes())
}

fn chart_xml(
    plan: &TableChartPlan,
    limits: &TableChartHwpxLimits,
    chart_limits: TableChartLimits,
) -> Result<Vec<u8>, TableChartHwpxError> {
    let (category_axis, value_axis) = axis_ids(plan, chart_limits)?;
    let mut series_xml = String::new();
    for (series_index, series) in plan.series().iter().enumerate() {
        let label = escape_xml_text(series.label())?;
        write!(
            series_xml,
            concat!(
                "<c:ser><c:idx val=\"{index}\"/><c:order val=\"{index}\"/>",
                "<c:tx><c:strRef><c:f>Formula</c:f><c:strCache><c:ptCount val=\"1\"/>",
                "<c:pt idx=\"0\"><c:v>{label}</c:v></c:pt></c:strCache></c:strRef></c:tx>",
                "<c:invertIfNegative val=\"0\"/>",
                "<c:cat><c:strRef><c:f>General</c:f><c:strCache><c:ptCount val=\"{categories}\"/>"
            ),
            index = series_index,
            label = label,
            categories = plan.categories().len(),
        )
        .map_err(|_| TableChartHwpxError::Serialization)?;
        for (index, category) in plan.categories().iter().enumerate() {
            write!(
                series_xml,
                "<c:pt idx=\"{index}\"><c:v>{}</c:v></c:pt>",
                escape_xml_text(category.label())?
            )
            .map_err(|_| TableChartHwpxError::Serialization)?;
        }
        write!(
            series_xml,
            concat!(
                "</c:strCache></c:strRef></c:cat>",
                "<c:val><c:numRef><c:f>Formula</c:f><c:numCache>",
                "<c:formatCode>General</c:formatCode><c:ptCount val=\"{}\"/>"
            ),
            series.values().len()
        )
        .map_err(|_| TableChartHwpxError::Serialization)?;
        for (index, point) in series.values().iter().enumerate() {
            if let Some(value) = point.value() {
                write!(
                    series_xml,
                    "<c:pt idx=\"{index}\"><c:v>{}</c:v></c:pt>",
                    decimal_text(value)
                )
                .map_err(|_| TableChartHwpxError::Serialization)?;
            }
        }
        series_xml.push_str("</c:numCache></c:numRef></c:val></c:ser>");
        if series_xml.len() > limits.native.chart_bytes {
            return Err(TableChartHwpxError::OutputLimit);
        }
    }
    let xml = format!(
        concat!(
            "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\" ?>",
            "<c:chartSpace xmlns:a=\"http://schemas.openxmlformats.org/drawingml/2006/main\" ",
            "xmlns:c=\"http://schemas.openxmlformats.org/drawingml/2006/chart\">",
            "<c:date1904 val=\"0\"/><c:style val=\"2\"/><c:roundedCorners val=\"0\"/>",
            "<c:chart><c:title><c:layout/><c:overlay val=\"0\"/></c:title>",
            "<c:autoTitleDeleted val=\"0\"/><c:view3D><c:rAngAx val=\"1\"/>",
            "<c:rotX val=\"15\"/><c:rotY val=\"20\"/><c:perspective val=\"30\"/></c:view3D>",
            "<c:plotArea><c:layout/><c:bar3DChart><c:barDir val=\"col\"/>",
            "<c:grouping val=\"clustered\"/><c:varyColors val=\"0\"/>{series}",
            "<c:gapWidth val=\"150\"/><c:gapDepth val=\"150\"/><c:shape val=\"box\"/>",
            "<c:axId val=\"{cat_axis}\"/><c:axId val=\"{value_axis}\"/></c:bar3DChart>",
            "<c:catAx><c:axId val=\"{cat_axis}\"/><c:scaling><c:orientation val=\"minMax\"/>",
            "</c:scaling><c:axPos val=\"b\"/><c:crossAx val=\"{value_axis}\"/>",
            "<c:delete val=\"0\"/><c:majorTickMark val=\"out\"/><c:minorTickMark val=\"none\"/>",
            "<c:tickLblPos val=\"nextTo\"/><c:crosses val=\"autoZero\"/><c:auto val=\"1\"/>",
            "<c:lblAlgn val=\"ctr\"/><c:lblOffset val=\"100\"/><c:tickMarkSkip val=\"1\"/>",
            "<c:noMultiLvlLbl val=\"0\"/></c:catAx>",
            "<c:valAx><c:axId val=\"{value_axis}\"/><c:scaling><c:orientation val=\"minMax\"/>",
            "</c:scaling><c:axPos val=\"l\"/><c:crossAx val=\"{cat_axis}\"/>",
            "<c:delete val=\"0\"/><c:majorGridlines/><c:numFmt formatCode=\"General\" sourceLinked=\"1\"/>",
            "<c:majorTickMark val=\"out\"/><c:minorTickMark val=\"none\"/>",
            "<c:tickLblPos val=\"nextTo\"/><c:crosses val=\"autoZero\"/>",
            "<c:crossBetween val=\"between\"/></c:valAx></c:plotArea>",
            "<c:legend><c:legendPos val=\"r\"/><c:layout/><c:overlay val=\"0\"/></c:legend>",
            "<c:plotVisOnly val=\"0\"/><c:dispBlanksAs val=\"gap\"/></c:chart></c:chartSpace>"
        ),
        series = series_xml,
        cat_axis = category_axis,
        value_axis = value_axis,
    );
    if xml.len() > limits.native.chart_bytes {
        return Err(TableChartHwpxError::OutputLimit);
    }
    PreservingXmlDocument::parse(xml.as_bytes())?.verify_untouched_round_trip()?;
    Ok(xml.into_bytes())
}

fn read_chart_parts(
    section: &[u8],
    chart_part: &[u8],
    request: &TableChartHwpxRequest,
    plan: &TableChartPlan,
    expected_chart_ordinal: usize,
    limits: &TableChartHwpxLimits,
    chart_limits: TableChartLimits,
) -> Result<TableChartHwpxReadback, TableChartHwpxError> {
    let expected_part = chart_xml(plan, limits, chart_limits)?;
    if chart_part != expected_part || chart_part.len() > limits.native.chart_bytes {
        return Err(TableChartHwpxError::ReadbackMismatch);
    }
    let document = parse_section(section, limits)?;
    let charts = indexes_named(&document, "chart");
    let chart_index = *charts
        .get(expected_chart_ordinal)
        .ok_or(TableChartHwpxError::ReadbackMismatch)?;
    if charts.len() != expected_chart_ordinal + 1 {
        return Err(TableChartHwpxError::ReadbackMismatch);
    }
    let chart = element(&document, chart_index)?;
    if parse_u32(attr(chart, "id")?)? != request.native_chart_id
        || parse_u32(attr(chart, "zOrder")?)? != request.z_order
        || attr(chart, "chartIDRef")? != request.chart_part
        || attr(chart, "numberingType")? != "PICTURE"
        || attr(chart, "textWrap")? != "SQUARE"
        || attr(chart, "textFlow")? != "BOTH_SIDES"
    {
        return Err(TableChartHwpxError::ReadbackMismatch);
    }
    let expected_fragment = chart_fragment(request, limits)?;
    let span = chart
        .outer_span()
        .ok_or(TableChartHwpxError::ReadbackMismatch)?;
    if document.source_text(span)?.as_bytes() != expected_fragment {
        return Err(TableChartHwpxError::ReadbackMismatch);
    }
    Ok(TableChartHwpxReadback {
        profile_id: TABLE_CHART_HWPX_PROFILE_ID,
        chart_part_sha256: Sha256::digest(chart_part).into(),
        chart_object_sha256: Sha256::digest(&expected_fragment).into(),
        native_chart_id: request.native_chart_id,
        z_order: request.z_order,
        series_count: plan.series().len(),
        category_count: plan.categories().len(),
        data_point_count: plan.receipt().data_point_count,
        blank_data_point_count: plan.receipt().blank_data_point_count,
        chart_count: charts.len(),
    })
}

fn readback_span(
    section: &[u8],
    request: &TableChartHwpxRequest,
    expected_chart_ordinal: usize,
    limits: &TableChartHwpxLimits,
) -> Result<crate::XmlByteSpan, TableChartHwpxError> {
    let document = parse_section(section, limits)?;
    let charts = indexes_named(&document, "chart");
    let chart = *charts
        .get(expected_chart_ordinal)
        .ok_or(TableChartHwpxError::ReadbackMismatch)?;
    let element = element(&document, chart)?;
    if attr(element, "chartIDRef")? != request.chart_part {
        return Err(TableChartHwpxError::ReadbackMismatch);
    }
    element
        .outer_span()
        .ok_or(TableChartHwpxError::ReadbackMismatch)
}

fn verify_manifest_and_preservation(
    patch: &PatchResult,
    manifest_path: &PackagePath,
    request: &TableChartHwpxRequest,
    original: &[u8],
) -> Result<(), TableChartHwpxError> {
    let manifest = patch_part(patch, manifest_path.as_str())?;
    let document = PreservingXmlDocument::parse(&manifest.bytes)?;
    let matches = manifest_items(&document, request)?;
    if matches.len() != 1 {
        return Err(TableChartHwpxError::RelationshipMismatch);
    }
    let span = element(&document, matches[0])?
        .outer_span()
        .ok_or(TableChartHwpxError::PreservationMismatch)?;
    if remove_span(&manifest.bytes, span)? != original {
        return Err(TableChartHwpxError::PreservationMismatch);
    }
    let chart = patch_part(patch, &request.chart_part)?;
    if chart.media_type.as_str() != CHART_MEDIA_TYPE {
        return Err(TableChartHwpxError::RelationshipMismatch);
    }
    Ok(())
}

fn manifest_items(
    document: &PreservingXmlDocument,
    request: &TableChartHwpxRequest,
) -> Result<Vec<usize>, TableChartHwpxError> {
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
        if optional_attr(candidate, "id")? == Some(request.manifest_item_id())
            && optional_attr(candidate, "href")? == Some(request.chart_part())
            && optional_attr(candidate, "media-type")? == Some(CHART_MEDIA_TYPE)
        {
            output.push(index);
        }
    }
    Ok(output)
}

fn verify_unrelated_parts(
    patch: &PatchResult,
    section: &PackagePath,
    graph: &PackageGraph,
    request: &TableChartHwpxRequest,
) -> Result<(), TableChartHwpxError> {
    for record in patch.parts() {
        let allowed = record.path() == section
            || record.path() == &graph.package_document
            || record.path().as_str() == request.chart_part;
        if !allowed
            && (record.disposition() != PatchPartDisposition::Untouched
                || record.source_sha256() != Some(record.output_sha256()))
        {
            return Err(TableChartHwpxError::PreservationMismatch);
        }
    }
    Ok(())
}

fn package_object_state<R: Read + Seek>(
    reader: &mut BoundedZipReader<R>,
    graph: &PackageGraph,
    limits: &TableChartHwpxLimits,
) -> Result<(BTreeSet<u32>, u32, usize), TableChartHwpxError> {
    let mut ids = BTreeSet::new();
    let mut max_z_order = 0_u32;
    let mut charts = 0_usize;
    let paths = graph.spine.clone();
    for path in paths {
        let bytes = read_exact_part(
            reader,
            graph,
            path.as_str(),
            limits,
            limits.native.section_bytes,
        )?;
        let document = parse_section(&bytes, limits)?;
        for candidate in document.elements() {
            if candidate.name().namespace() != Some(PARAGRAPH_NS) {
                continue;
            }
            if matches!(
                candidate.name().local_name(),
                "tbl"
                    | "equation"
                    | "pic"
                    | "line"
                    | "rect"
                    | "ellipse"
                    | "polygon"
                    | "curve"
                    | "ole"
                    | "chart"
            ) {
                let id = parse_u32(attr(candidate, "id")?)?;
                if id == 0 || !ids.insert(id) {
                    return Err(TableChartHwpxError::AllocationDrift);
                }
                if let Some(z_order) = optional_attr(candidate, "zOrder")? {
                    max_z_order = max_z_order.max(parse_u32(z_order)?);
                }
                if candidate.name().local_name() == "chart" {
                    charts = charts
                        .checked_add(1)
                        .ok_or(TableChartHwpxError::Allocation)?;
                }
            }
        }
    }
    Ok((ids, max_z_order, charts))
}

fn next_chart_part(
    graph: &PackageGraph,
    limits: &TableChartHwpxLimits,
) -> Result<String, TableChartHwpxError> {
    let keys = graph
        .parts
        .iter()
        .map(|part| part.path.collision_key())
        .collect::<BTreeSet<_>>();
    for index in 1..=limits.native.charts {
        let candidate = format!("Chart/chart{index}.xml");
        let path = PackagePath::parse(candidate.as_bytes(), 0, limits.package)?;
        if !keys.contains(path.collision_key()) {
            return Ok(candidate);
        }
    }
    Err(TableChartHwpxError::AllocationDrift)
}

fn axis_ids(
    plan: &TableChartPlan,
    limits: TableChartLimits,
) -> Result<(u32, u32), TableChartHwpxError> {
    let digest = plan.canonical_sha256(limits)?;
    let mut first = u32::from_be_bytes(
        digest[0..4]
            .try_into()
            .map_err(|_| TableChartHwpxError::Allocation)?,
    ) & 0x7fff_ffff;
    let mut second = u32::from_be_bytes(
        digest[4..8]
            .try_into()
            .map_err(|_| TableChartHwpxError::Allocation)?,
    ) & 0x7fff_ffff;
    if first == 0 {
        first = 1;
    }
    if second == 0 {
        second = 1;
    }
    if first == second {
        second = second
            .checked_add(1)
            .filter(|value| *value <= 0x7fff_ffff)
            .unwrap_or(1);
        if first == second {
            second = 2;
        }
    }
    Ok((first, second))
}

fn parse_section(
    bytes: &[u8],
    limits: &TableChartHwpxLimits,
) -> Result<PreservingXmlDocument, TableChartHwpxError> {
    if bytes.is_empty() || bytes.len() > limits.native.section_bytes {
        return Err(TableChartHwpxError::InputLimit);
    }
    let document = PreservingXmlDocument::parse(bytes)?;
    if document.elements().len() > limits.native.elements {
        return Err(TableChartHwpxError::InputLimit);
    }
    Ok(document)
}

fn read_exact_part<R: Read + Seek>(
    reader: &mut BoundedZipReader<R>,
    graph: &PackageGraph,
    part: &str,
    _limits: &TableChartHwpxLimits,
    maximum: usize,
) -> Result<Vec<u8>, TableChartHwpxError> {
    let record = graph
        .parts
        .iter()
        .find(|record| record.path.as_str() == part)
        .ok_or(TableChartHwpxError::UnsupportedSource)?;
    let entry = reader
        .entries()
        .iter()
        .find(|entry| entry.path == record.path)
        .map(|entry| entry.index)
        .ok_or(TableChartHwpxError::UnsupportedSource)?;
    let bytes = reader.read_entry(entry)?;
    if bytes.len() > maximum || <[u8; 32]>::from(Sha256::digest(&bytes)) != record.raw_sha256 {
        return Err(TableChartHwpxError::UnsupportedSource);
    }
    Ok(bytes)
}

fn patch_part<'a>(
    patch: &'a PatchResult,
    part_path: &str,
) -> Result<&'a crate::patch::VirtualPart, TableChartHwpxError> {
    patch
        .parts
        .iter()
        .find(|part| part.path.as_str() == part_path)
        .ok_or(TableChartHwpxError::ReadbackMismatch)
}

fn element(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<&XmlElementToken, TableChartHwpxError> {
    document
        .elements()
        .get(index)
        .ok_or(TableChartHwpxError::UnsupportedSource)
}

fn has_name(element: &XmlElementToken, local_name: &str) -> bool {
    element.name().namespace() == Some(PARAGRAPH_NS) && element.name().local_name() == local_name
}

fn indexes_named(document: &PreservingXmlDocument, local_name: &str) -> Vec<usize> {
    document
        .elements()
        .iter()
        .enumerate()
        .filter_map(|(index, element)| has_name(element, local_name).then_some(index))
        .collect()
}

fn child_named(
    document: &PreservingXmlDocument,
    parent: usize,
    local_name: &str,
) -> Result<Option<usize>, TableChartHwpxError> {
    let mut matched = None;
    let mut current = element(document, parent)?.first_child();
    while let Some(index) = current {
        let candidate = element(document, index)?;
        if has_name(candidate, local_name) && matched.replace(index).is_some() {
            return Err(TableChartHwpxError::UnsupportedSource);
        }
        current = candidate.next_sibling();
    }
    Ok(matched)
}

fn descendant_indexes_named(
    document: &PreservingXmlDocument,
    ancestor: usize,
    local_name: &str,
) -> Result<Vec<usize>, TableChartHwpxError> {
    let mut output = Vec::new();
    for (index, candidate) in document.elements().iter().enumerate() {
        if has_name(candidate, local_name) && is_descendant_of(document, index, ancestor)? {
            output.push(index);
        }
    }
    Ok(output)
}

fn is_descendant_of(
    document: &PreservingXmlDocument,
    mut child: usize,
    ancestor: usize,
) -> Result<bool, TableChartHwpxError> {
    while let Some(parent) = element(document, child)?.parent() {
        if parent == ancestor {
            return Ok(true);
        }
        child = parent;
    }
    Ok(false)
}

fn has_ancestor_between(
    document: &PreservingXmlDocument,
    mut child: usize,
    ancestor: usize,
    local_name: &str,
) -> Result<bool, TableChartHwpxError> {
    while let Some(parent) = element(document, child)?.parent() {
        if parent == ancestor {
            return Ok(false);
        }
        if has_name(element(document, parent)?, local_name) {
            return Ok(true);
        }
        child = parent;
    }
    Err(TableChartHwpxError::UnsupportedSource)
}

fn attr<'a>(element: &'a XmlElementToken, name: &str) -> Result<&'a str, TableChartHwpxError> {
    optional_attr(element, name)?.ok_or(TableChartHwpxError::UnsupportedSource)
}

fn optional_attr<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<Option<&'a str>, TableChartHwpxError> {
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
        return Err(TableChartHwpxError::UnsupportedSource);
    }
    Ok(value)
}

fn parse_u32(value: &str) -> Result<u32, TableChartHwpxError> {
    if value.is_empty()
        || (value.len() > 1 && value.starts_with('0'))
        || !value.bytes().all(|byte| byte.is_ascii_digit())
    {
        return Err(TableChartHwpxError::UnsupportedSource);
    }
    value
        .parse()
        .map_err(|_| TableChartHwpxError::UnsupportedSource)
}

fn decimal_text(value: FormulaDecimal) -> String {
    let negative = value.coefficient() < 0;
    let mut digits = value.coefficient().unsigned_abs().to_string();
    let scale = usize::from(value.scale());
    if scale > 0 {
        if digits.len() <= scale {
            let padding = scale + 1 - digits.len();
            digits = format!("{}{}", "0".repeat(padding), digits);
        }
        let point = digits.len() - scale;
        digits.insert(point, '.');
    }
    if negative {
        digits.insert(0, '-');
    }
    digits
}

fn decimal_display_matches(display: &str, value: FormulaDecimal) -> bool {
    if display == decimal_text(value) {
        return true;
    }
    let (sign, rest) = display
        .strip_prefix('-')
        .map_or(("", display), |value| ("-", value));
    let (integer, fraction) = rest
        .split_once('.')
        .map_or((rest, None), |(a, b)| (a, Some(b)));
    let groups = integer.split(',').collect::<Vec<_>>();
    if groups.len() < 2
        || groups[0].is_empty()
        || groups[0].len() > 3
        || !groups[0].bytes().all(|byte| byte.is_ascii_digit())
        || groups[1..]
            .iter()
            .any(|group| group.len() != 3 || !group.bytes().all(|byte| byte.is_ascii_digit()))
        || fraction.is_some_and(|value| {
            value.is_empty() || !value.bytes().all(|byte| byte.is_ascii_digit())
        })
    {
        return false;
    }
    let mut normalized = format!("{sign}{}", groups.concat());
    if let Some(fraction) = fraction {
        normalized.push('.');
        normalized.push_str(fraction);
    }
    normalized == decimal_text(value)
}

fn decode_xml_text(raw: &str) -> Result<String, TableChartHwpxError> {
    if raw.contains("&#") {
        return Err(TableChartHwpxError::UnsupportedSource);
    }
    Ok(raw
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", "\"")
        .replace("&apos;", "'")
        .replace("&amp;", "&"))
}

fn escape_xml_text(value: &str) -> Result<String, TableChartHwpxError> {
    if value.chars().any(invalid_xml_character) {
        return Err(TableChartHwpxError::UnsupportedSource);
    }
    Ok(value
        .replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;"))
}

fn escape_xml_attribute(value: &str) -> Result<String, TableChartHwpxError> {
    Ok(escape_xml_text(value)?
        .replace('"', "&quot;")
        .replace('\'', "&apos;"))
}

fn invalid_xml_character(character: char) -> bool {
    matches!(character as u32, 0..=8 | 11..=12 | 14..=31 | 0xFFFE | 0xFFFF)
}

fn validate_manifest_id(
    value: &str,
    limits: &TableChartHwpxLimits,
) -> Result<(), TableChartHwpxError> {
    let mut bytes = value.bytes();
    let first = bytes.next().ok_or(TableChartHwpxError::AllocationDrift)?;
    if value.len() > limits.native.identifiers_bytes
        || !(first.is_ascii_alphabetic() || first == b'_')
        || bytes.any(|byte| !(byte.is_ascii_alphanumeric() || matches!(byte, b'_' | b'-' | b'.')))
    {
        return Err(TableChartHwpxError::AllocationDrift);
    }
    Ok(())
}

#[allow(clippy::case_sensitive_file_extension_comparisons)]
fn validate_chart_part(
    value: &str,
    limits: &TableChartHwpxLimits,
) -> Result<(), TableChartHwpxError> {
    if value.len() > limits.native.identifiers_bytes
        || !value.starts_with("Chart/chart")
        || !value.ends_with(".xml")
    {
        return Err(TableChartHwpxError::AllocationDrift);
    }
    let digits = &value["Chart/chart".len()..value.len() - ".xml".len()];
    if digits.is_empty()
        || (digits.len() > 1 && digits.starts_with('0'))
        || !digits.bytes().all(|byte| byte.is_ascii_digit())
    {
        return Err(TableChartHwpxError::AllocationDrift);
    }
    PackagePath::parse(value.as_bytes(), 0, limits.package)?;
    Ok(())
}

fn remove_span(bytes: &[u8], span: crate::XmlByteSpan) -> Result<Vec<u8>, TableChartHwpxError> {
    if span.start() > span.end() || span.end() > bytes.len() {
        return Err(TableChartHwpxError::PreservationMismatch);
    }
    let mut output = Vec::with_capacity(bytes.len() - span.len());
    output.extend_from_slice(&bytes[..span.start()]);
    output.extend_from_slice(&bytes[span.end()..]);
    Ok(output)
}

fn package_state_sha256(graph: &PackageGraph) -> String {
    let mut digest = Sha256::new();
    digest.update(TABLE_CHART_HWPX_PROFILE_ID.as_bytes());
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

fn bounded_json<T: Serialize>(
    value: &T,
    limits: &TableChartHwpxLimits,
) -> Result<Vec<u8>, TableChartHwpxError> {
    let bytes = serde_json::to_vec(value).map_err(|_| TableChartHwpxError::Serialization)?;
    if bytes.len() > limits.native.serialized_bytes {
        return Err(TableChartHwpxError::OutputLimit);
    }
    Ok(bytes)
}

fn validate_digest(value: &str) -> Result<(), TableChartHwpxError> {
    if value.len() != 64
        || value
            .bytes()
            .any(|byte| !byte.is_ascii_digit() && !(b'a'..=b'f').contains(&byte))
    {
        return Err(TableChartHwpxError::InvalidDigest);
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

fn reject_duplicate_json_keys(bytes: &[u8]) -> Result<(), TableChartHwpxError> {
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
        fn visit_some<D>(self, deserializer: D) -> Result<(), D::Error>
        where
            D: serde::Deserializer<'de>,
        {
            deserializer.deserialize_any(Visitor)
        }
    }
    let mut deserializer = serde_json::Deserializer::from_slice(bytes);
    serde::de::DeserializeSeed::deserialize(Seed, &mut deserializer)
        .map_err(|_| TableChartHwpxError::InvalidJson)?;
    deserializer
        .end()
        .map_err(|_| TableChartHwpxError::InvalidJson)
}
