use std::collections::BTreeSet;
use std::fmt::Write as _;
use std::fmt::{self, Debug};
use std::io::{Read, Seek};

use domain_ir::{MathAst, MathAstDraft, MathAstLimits};
use equation_engine::{EQEDIT_PROFILE_VERSION, EqEditEngine, EqEditLimits};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{
    BoundedZipReader, GraphError, IdIndexLimits, IdRuleProfile, PackageError, PackageGraph,
    PackageGraphLimits, PackageLimits, PackagePath, PartRole, PatchError, PatchIntent, PatchLimits,
    PatchPartDisposition, PatchResult, PreservingPatchEngine, PreservingXmlDocument,
    PreservingXmlError, SiblingPosition, ValidatedXmlFragment, XmlElementSelector, XmlElementToken,
    XmlTokenKind,
};

pub const EQUATION_HWPX_SCHEMA_VERSION: &str = "hwpx-agent.equation-hwpx/v1";
pub const EQUATION_HWPX_PROFILE_ID: &str =
    "hwpx-agent.equation-hwpx.hangul-2020-11.0.0.9136-x86-ko-KR/v1";

const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const SECTION_NS: &str = "http://www.hancom.co.kr/hwpml/2011/section";
const EQUATION_VERSION: &str = "Equation Version 60";
const EQUATION_FONT: &str = "HancomEQN";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct EquationHwpxLimitConfig {
    pub section_bytes: usize,
    pub elements: usize,
    pub equations: usize,
    pub script_bytes: usize,
    pub serialized_bytes: usize,
    pub extent_hwpunit: u32,
    pub object_id: u32,
}

impl Default for EquationHwpxLimitConfig {
    fn default() -> Self {
        Self {
            section_bytes: 32 * 1024 * 1024,
            elements: 1_000_000,
            equations: 65_536,
            script_bytes: 4 * 1024 * 1024,
            serialized_bytes: 16 * 1024 * 1024,
            extent_hwpunit: 10_000_000,
            object_id: u32::MAX - 1,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct EquationHwpxLimits {
    native: EquationHwpxLimitConfig,
    pub package: PackageLimits,
    pub graph: PackageGraphLimits,
    pub ids: IdIndexLimits,
    pub patch: PatchLimits,
    pub math: MathAstLimits,
    pub eqedit: EqEditLimits,
}

impl EquationHwpxLimits {
    pub const HARD_MAX_SECTION_BYTES: usize = 128 * 1024 * 1024;
    pub const HARD_MAX_ELEMENTS: usize = 2_000_000;
    pub const HARD_MAX_EQUATIONS: usize = 262_144;
    pub const HARD_MAX_SCRIPT_BYTES: usize = 16 * 1024 * 1024;
    pub const HARD_MAX_SERIALIZED_BYTES: usize = 32 * 1024 * 1024;
    pub const HARD_MAX_EXTENT_HWPUNIT: u32 = 100_000_000;

    /// Creates the finite native-object limits while retaining the validated package limits.
    ///
    /// # Errors
    ///
    /// Rejects zero values, immutable ceiling violations, and a native script bound larger than
    /// the configured `EqEdit` output bound.
    pub fn new(
        native: EquationHwpxLimitConfig,
        package: PackageLimits,
        graph: PackageGraphLimits,
        ids: IdIndexLimits,
        patch: PatchLimits,
        math: MathAstLimits,
        eqedit: EqEditLimits,
    ) -> Result<Self, EquationHwpxError> {
        if native.section_bytes == 0
            || native.section_bytes > Self::HARD_MAX_SECTION_BYTES
            || native.elements == 0
            || native.elements > Self::HARD_MAX_ELEMENTS
            || native.equations == 0
            || native.equations > Self::HARD_MAX_EQUATIONS
            || native.script_bytes == 0
            || native.script_bytes > Self::HARD_MAX_SCRIPT_BYTES
            || native.script_bytes > eqedit.config().script_bytes
            || native.serialized_bytes == 0
            || native.serialized_bytes > Self::HARD_MAX_SERIALIZED_BYTES
            || native.extent_hwpunit == 0
            || native.extent_hwpunit > Self::HARD_MAX_EXTENT_HWPUNIT
            || native.object_id == 0
        {
            return Err(EquationHwpxError::InvalidLimit);
        }
        Ok(Self {
            native,
            package,
            graph,
            ids,
            patch,
            math,
            eqedit,
        })
    }

    #[must_use]
    pub const fn config(self) -> EquationHwpxLimitConfig {
        self.native
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum EquationLayout {
    Inline,
    Display,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum EquationExtentSource {
    TargetReadback,
    ValidatedEstimator,
    Provisional,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct EquationExtent {
    pub width_hwpunit: u32,
    pub height_hwpunit: u32,
    pub source: EquationExtentSource,
    pub source_evidence_sha256: Option<String>,
    pub render_required: bool,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct EquationColor {
    pub red: u8,
    pub green: u8,
    pub blue: u8,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct EquationStyle {
    pub base_unit: u32,
    pub baseline_percent: u8,
    pub text_color: EquationColor,
}

impl Default for EquationStyle {
    fn default() -> Self {
        Self {
            base_unit: 1_000,
            baseline_percent: 85,
            text_color: EquationColor {
                red: 0,
                green: 0,
                blue: 0,
            },
        }
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct EquationHwpxRequestDraft {
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
    pub expected_document_flow_sha256: String,
    pub target_document_flow_sha256: String,
    pub object_id: u32,
    pub layout: EquationLayout,
    pub style: EquationStyle,
    pub extent: EquationExtent,
    pub math_ast: MathAstDraft,
}

impl Debug for EquationHwpxRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("EquationHwpxRequestDraft")
            .field("schema_version", &self.schema_version)
            .field("profile_id", &self.profile_id)
            .field("section_part", &"<redacted>")
            .field("paragraph_ordinal", &self.paragraph_ordinal)
            .field("run_ordinal", &self.run_ordinal)
            .field("bindings", &"<redacted>")
            .field("object_id", &"<redacted>")
            .field("layout", &self.layout)
            .field("style", &"<redacted>")
            .field("extent", &"<redacted>")
            .field("math_ast", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct EquationHwpxSource {
    profile_id: &'static str,
    section_part: String,
    paragraph_ordinal: usize,
    run_ordinal: usize,
    layout: EquationLayout,
    package_state_sha256: String,
    section_sha256: String,
    paragraph_sha256: String,
    run_sha256: String,
    object_ids_sha256: String,
    object_id_count: usize,
    equation_count: usize,
}

impl EquationHwpxSource {
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
    pub const fn object_id_count(&self) -> usize {
        self.object_id_count
    }

    #[must_use]
    pub const fn equation_count(&self) -> usize {
        self.equation_count
    }

    /// Serializes the complete source binding without exposing source XML.
    ///
    /// # Errors
    ///
    /// Rejects serialization or the configured output ceiling.
    pub fn canonical_json(&self, limits: EquationHwpxLimits) -> Result<Vec<u8>, EquationHwpxError> {
        bounded_json(self, &limits)
    }
}

impl Debug for EquationHwpxSource {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("EquationHwpxSource")
            .field("profile_id", &self.profile_id)
            .field("section_part", &"<redacted>")
            .field("paragraph_ordinal", &self.paragraph_ordinal)
            .field("run_ordinal", &self.run_ordinal)
            .field("layout", &self.layout)
            .field("bindings", &"<redacted>")
            .field("object_id_count", &self.object_id_count)
            .field("equation_count", &self.equation_count)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct EquationHwpxRequest {
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
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    object_id: u32,
    layout: EquationLayout,
    style: EquationStyle,
    extent: EquationExtent,
    semantic_sha256: String,
    script_sha256: String,
    math_ast: MathAst,
}

impl EquationHwpxRequest {
    /// Validates one strict draft against the exact package/source/flow snapshot.
    ///
    /// # Errors
    ///
    /// Rejects version, profile, state, flow, ID, style, extent, AST or `EqEdit` drift.
    pub fn from_draft(
        draft: EquationHwpxRequestDraft,
        source: &EquationHwpxSource,
        current_document_flow_sha256: &str,
        limits: EquationHwpxLimits,
    ) -> Result<Self, EquationHwpxError> {
        if draft.schema_version != EQUATION_HWPX_SCHEMA_VERSION {
            return Err(EquationHwpxError::UnsupportedVersion);
        }
        if draft.profile_id != EQUATION_HWPX_PROFILE_ID {
            return Err(EquationHwpxError::UnsupportedProfile);
        }
        for digest in [
            &draft.expected_package_state_sha256,
            &draft.expected_section_sha256,
            &draft.expected_paragraph_sha256,
            &draft.expected_run_sha256,
            &draft.expected_object_ids_sha256,
            &draft.expected_document_flow_sha256,
            &draft.target_document_flow_sha256,
            current_document_flow_sha256,
        ] {
            require_digest(digest)?;
        }
        validate_style(&draft.style)?;
        validate_extent(&draft.extent, &limits)?;
        if draft.object_id == 0 || draft.object_id > limits.native.object_id {
            return Err(EquationHwpxError::InvalidObjectId);
        }
        let math_ast = MathAst::from_draft(draft.math_ast, limits.math)
            .map_err(|_| EquationHwpxError::MathAst)?;
        let compiled = EqEditEngine::new(limits.eqedit, limits.math)
            .map_err(|_| EquationHwpxError::EqEdit)?
            .compile(&math_ast)
            .map_err(|_| EquationHwpxError::EqEdit)?;
        if compiled.script_length_bytes() as usize > limits.native.script_bytes {
            return Err(EquationHwpxError::ScriptLimit);
        }
        let request = Self {
            schema_version: EQUATION_HWPX_SCHEMA_VERSION,
            profile_id: EQUATION_HWPX_PROFILE_ID,
            section_part: draft.section_part,
            paragraph_ordinal: draft.paragraph_ordinal,
            run_ordinal: draft.run_ordinal,
            expected_package_state_sha256: draft.expected_package_state_sha256,
            expected_section_sha256: draft.expected_section_sha256,
            expected_paragraph_sha256: draft.expected_paragraph_sha256,
            expected_run_sha256: draft.expected_run_sha256,
            expected_object_ids_sha256: draft.expected_object_ids_sha256,
            expected_document_flow_sha256: draft.expected_document_flow_sha256,
            target_document_flow_sha256: draft.target_document_flow_sha256,
            object_id: draft.object_id,
            layout: draft.layout,
            style: draft.style,
            extent: draft.extent,
            semantic_sha256: compiled.semantic_sha256().to_owned(),
            script_sha256: compiled.script_sha256().to_owned(),
            math_ast,
        };
        validate_request_source(&request, source, current_document_flow_sha256)?;
        let _ = request.canonical_json(limits)?;
        Ok(request)
    }

    /// Parses strict, duplicate-free JSON and applies [`Self::from_draft`].
    ///
    /// # Errors
    ///
    /// Rejects empty, oversized, malformed, duplicate-key, unknown-field or invalid input.
    pub fn from_json(
        bytes: &[u8],
        source: &EquationHwpxSource,
        current_document_flow_sha256: &str,
        limits: EquationHwpxLimits,
    ) -> Result<Self, EquationHwpxError> {
        if bytes.is_empty() || bytes.len() > limits.native.serialized_bytes {
            return Err(EquationHwpxError::InputLimit);
        }
        reject_duplicate_json_keys(bytes)?;
        let draft = serde_json::from_slice(bytes).map_err(|_| EquationHwpxError::InvalidJson)?;
        Self::from_draft(draft, source, current_document_flow_sha256, limits)
    }

    #[must_use]
    pub const fn object_id(&self) -> u32 {
        self.object_id
    }

    #[must_use]
    pub const fn layout(&self) -> EquationLayout {
        self.layout
    }

    #[must_use]
    pub fn semantic_sha256(&self) -> &str {
        &self.semantic_sha256
    }

    #[must_use]
    pub fn target_document_flow_sha256(&self) -> &str {
        &self.target_document_flow_sha256
    }

    /// Serializes every request field deterministically and within a finite bound.
    ///
    /// # Errors
    ///
    /// Rejects serialization or output-limit failure.
    pub fn canonical_json(&self, limits: EquationHwpxLimits) -> Result<Vec<u8>, EquationHwpxError> {
        bounded_json(self, &limits)
    }
}

impl Debug for EquationHwpxRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("EquationHwpxRequest")
            .field("schema_version", &self.schema_version)
            .field("profile_id", &self.profile_id)
            .field("section_part", &"<redacted>")
            .field("paragraph_ordinal", &self.paragraph_ordinal)
            .field("run_ordinal", &self.run_ordinal)
            .field("bindings", &"<redacted>")
            .field("object_id", &"<redacted>")
            .field("layout", &self.layout)
            .field("style", &"<redacted>")
            .field("extent", &"<redacted>")
            .field("semantic_sha256", &"<redacted>")
            .field("script_sha256", &"<redacted>")
            .field("math_ast", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct EquationHwpxReadback {
    profile_id: &'static str,
    object_id: u32,
    layout: EquationLayout,
    style: EquationStyle,
    extent: EquationExtent,
    semantic_sha256: String,
    script_sha256: String,
    script_length_bytes: u32,
    equation_ordinal: usize,
    native_object_count: usize,
    render_required: bool,
    math_ast: MathAst,
}

impl EquationHwpxReadback {
    #[must_use]
    pub const fn object_id(&self) -> u32 {
        self.object_id
    }

    #[must_use]
    pub const fn layout(&self) -> EquationLayout {
        self.layout
    }

    #[must_use]
    pub const fn style(&self) -> &EquationStyle {
        &self.style
    }

    #[must_use]
    pub const fn extent(&self) -> &EquationExtent {
        &self.extent
    }

    #[must_use]
    pub fn semantic_sha256(&self) -> &str {
        &self.semantic_sha256
    }

    #[must_use]
    pub fn script_sha256(&self) -> &str {
        &self.script_sha256
    }

    #[must_use]
    pub const fn math_ast(&self) -> &MathAst {
        &self.math_ast
    }

    #[must_use]
    pub const fn native_object_count(&self) -> usize {
        self.native_object_count
    }

    /// Serializes the complete native readback within the configured finite bound.
    ///
    /// # Errors
    ///
    /// Rejects serialization or output-limit failure.
    pub fn canonical_json(&self, limits: EquationHwpxLimits) -> Result<Vec<u8>, EquationHwpxError> {
        bounded_json(self, &limits)
    }
}

impl Debug for EquationHwpxReadback {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("EquationHwpxReadback")
            .field("profile_id", &self.profile_id)
            .field("object_id", &"<redacted>")
            .field("layout", &self.layout)
            .field("style", &"<redacted>")
            .field("extent", &"<redacted>")
            .field("semantic_sha256", &"<redacted>")
            .field("script_sha256", &"<redacted>")
            .field("script_length_bytes", &"<redacted>")
            .field("equation_ordinal", &self.equation_ordinal)
            .field("native_object_count", &self.native_object_count)
            .field("render_required", &self.render_required)
            .field("math_ast", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct EquationHwpxLoweringReceipt {
    profile_id: &'static str,
    request_sha256: String,
    source_package_state_sha256: String,
    source_section_sha256: String,
    output_section_sha256: String,
    source_paragraph_sha256: String,
    source_run_sha256: String,
    source_object_ids_sha256: String,
    semantic_sha256: String,
    script_sha256: String,
    object_id: u32,
    layout: EquationLayout,
    render_required: bool,
    source_equation_count: usize,
    output_equation_count: usize,
    changed_parts: usize,
    untouched_parts: usize,
    preservation_verified: bool,
    native_readback_verified: bool,
    before_document_flow_sha256: String,
    after_document_flow_sha256: String,
}

impl EquationHwpxLoweringReceipt {
    #[must_use]
    pub const fn preservation_verified(&self) -> bool {
        self.preservation_verified
    }

    #[must_use]
    pub const fn native_readback_verified(&self) -> bool {
        self.native_readback_verified
    }

    #[must_use]
    pub const fn render_required(&self) -> bool {
        self.render_required
    }

    #[must_use]
    pub fn output_section_sha256(&self) -> &str {
        &self.output_section_sha256
    }

    /// Serializes the complete lowering receipt within the configured finite bound.
    ///
    /// # Errors
    ///
    /// Rejects serialization or output-limit failure.
    pub fn canonical_json(&self, limits: EquationHwpxLimits) -> Result<Vec<u8>, EquationHwpxError> {
        bounded_json(self, &limits)
    }
}

impl Debug for EquationHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("EquationHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field("digests", &"<redacted>")
            .field("object_id", &"<redacted>")
            .field("layout", &self.layout)
            .field("render_required", &self.render_required)
            .field("source_equation_count", &self.source_equation_count)
            .field("output_equation_count", &self.output_equation_count)
            .field("changed_parts", &self.changed_parts)
            .field("untouched_parts", &self.untouched_parts)
            .field("preservation_verified", &self.preservation_verified)
            .field("native_readback_verified", &self.native_readback_verified)
            .finish_non_exhaustive()
    }
}

pub struct EquationHwpxLowered {
    patch: PatchResult,
    receipt: EquationHwpxLoweringReceipt,
}

impl EquationHwpxLowered {
    #[must_use]
    pub const fn patch(&self) -> &PatchResult {
        &self.patch
    }

    #[must_use]
    pub const fn receipt(&self) -> &EquationHwpxLoweringReceipt {
        &self.receipt
    }

    #[must_use]
    pub fn into_patch(self) -> PatchResult {
        self.patch
    }
}

impl Debug for EquationHwpxLowered {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("EquationHwpxLowered")
            .field("patch", &self.patch)
            .field("receipt", &self.receipt)
            .finish()
    }
}

#[derive(Debug)]
pub struct EquationHwpxBuilder;

impl EquationHwpxBuilder {
    /// Inspects one exact empty run and binds it to the complete expanded package graph.
    ///
    /// # Errors
    ///
    /// Rejects non-spine targets, stale graph bytes, unsupported inline/display context, limits,
    /// malformed XML, or ambiguous object identifiers.
    pub fn inspect_source<R: Read + Seek>(
        reader: &mut BoundedZipReader<R>,
        graph: &PackageGraph,
        section_part: &str,
        paragraph_ordinal: usize,
        run_ordinal: usize,
        layout: EquationLayout,
        limits: EquationHwpxLimits,
    ) -> Result<EquationHwpxSource, EquationHwpxError> {
        inspect_bound_source(
            reader,
            graph,
            section_part,
            paragraph_ordinal,
            run_ordinal,
            layout,
            &limits,
        )
        .map(|bound| bound.source)
    }
}

#[derive(Debug)]
pub struct EquationHwpxReader;

impl EquationHwpxReader {
    /// Strictly inspects one native equation object from a section part.
    ///
    /// # Errors
    ///
    /// Rejects any unqualified attribute/child shape, script/profile drift, malformed `EqEdit`,
    /// ambiguous layout context, duplicate IDs, or finite-limit failure.
    pub fn read_in_section(
        bytes: &[u8],
        equation_ordinal: usize,
        limits: EquationHwpxLimits,
    ) -> Result<EquationHwpxReadback, EquationHwpxError> {
        read_equation_shape(bytes, equation_ordinal, &limits).map(|shape| shape.readback)
    }

    /// Reads one native equation through the closed package graph and verifies the graph hash.
    ///
    /// # Errors
    ///
    /// Applies the same strict native inspection and package part checks as source binding.
    pub fn read_in_package<R: Read + Seek>(
        reader: &mut BoundedZipReader<R>,
        graph: &PackageGraph,
        section_part: &str,
        equation_ordinal: usize,
        limits: EquationHwpxLimits,
    ) -> Result<EquationHwpxReadback, EquationHwpxError> {
        let (_, bytes) = read_spine_part(reader, graph, section_part, &limits)?;
        Self::read_in_section(&bytes, equation_ordinal, limits)
    }
}

#[derive(Debug)]
pub struct EquationHwpxLowerer;

impl EquationHwpxLowerer {
    /// Compiles the bound AST, inserts one native equation, executes the preserving package patch,
    /// and requires semantic native readback plus byte-exact removal preservation before return.
    ///
    /// # Errors
    ///
    /// Fails without a partial artifact on request/build drift, source/flow drift, ID collision,
    /// package patch failure, native readback mismatch, or any unrelated-byte mutation.
    #[allow(clippy::too_many_lines)]
    pub fn lower<R: Read + Seek>(
        reader: &mut BoundedZipReader<R>,
        graph: &PackageGraph,
        request: &EquationHwpxRequest,
        current_document_flow_sha256: &str,
        limits: EquationHwpxLimits,
    ) -> Result<EquationHwpxLowered, EquationHwpxError> {
        let bound = inspect_bound_source(
            reader,
            graph,
            &request.section_part,
            request.paragraph_ordinal,
            request.run_ordinal,
            request.layout,
            &limits,
        )?;
        validate_request_source(request, &bound.source, current_document_flow_sha256)?;
        if bound.object_ids.contains(&request.object_id) {
            return Err(EquationHwpxError::ObjectIdCollision);
        }
        let compiled = EqEditEngine::new(limits.eqedit, limits.math)
            .map_err(|_| EquationHwpxError::EqEdit)?
            .compile(&request.math_ast)
            .map_err(|_| EquationHwpxError::EqEdit)?;
        if compiled.semantic_sha256() != request.semantic_sha256
            || compiled.script_sha256() != request.script_sha256
            || compiled.script_length_bytes() as usize > limits.native.script_bytes
        {
            return Err(EquationHwpxError::BuildDrift);
        }
        let fragment_bytes = equation_fragment(request, compiled.script())?;
        let fragment = ValidatedXmlFragment::parse(&fragment_bytes, limits.patch)?;
        let selector =
            XmlElementSelector::bind(&bound.path, &bound.document, bound.target_text_element)?;
        let intent = PatchIntent::InsertSibling {
            target: selector,
            position: SiblingPosition::Before,
            fragment,
        };
        let patch = PreservingPatchEngine::apply_with_limits(
            reader,
            graph,
            limits.graph,
            IdRuleProfile::current_hancom_2020_equation_v4(),
            limits.ids,
            limits.patch,
            &[intent],
        )?;
        patch.verify_artifact_integrity()?;
        if patch.changed_parts() != 1 || patch.added_parts() != 0 || patch.intent_count() != 1 {
            return Err(EquationHwpxError::PreservationMismatch);
        }
        let output_part = patch
            .parts
            .iter()
            .find(|part| part.path == bound.path)
            .ok_or(EquationHwpxError::ReadbackMismatch)?;
        let output_shape = read_equation_shape(
            &output_part.bytes,
            bound.insertion_equation_ordinal,
            &limits,
        )?;
        if output_shape.readback.object_id != request.object_id
            || output_shape.readback.layout != request.layout
            || output_shape.readback.style != request.style
            || output_shape.readback.extent != request.extent
            || output_shape.readback.semantic_sha256 != request.semantic_sha256
            || output_shape.readback.script_sha256 != request.script_sha256
            || !request
                .math_ast
                .semantically_eq(&output_shape.readback.math_ast)
            || output_shape.readback.native_object_count != bound.source.equation_count + 1
        {
            return Err(EquationHwpxError::ReadbackMismatch);
        }
        let equation_span = output_shape.equation_span;
        let mut restored = Vec::with_capacity(bound.bytes.len());
        restored.extend_from_slice(&output_part.bytes[..equation_span.start()]);
        restored.extend_from_slice(&output_part.bytes[equation_span.end()..]);
        if restored != bound.bytes {
            return Err(EquationHwpxError::PreservationMismatch);
        }
        for record in patch.parts() {
            if record.path() != &bound.path
                && (record.disposition() != PatchPartDisposition::Untouched
                    || record.source_sha256() != Some(record.output_sha256()))
            {
                return Err(EquationHwpxError::PreservationMismatch);
            }
        }
        let receipt = EquationHwpxLoweringReceipt {
            profile_id: EQUATION_HWPX_PROFILE_ID,
            request_sha256: hex(request_sha256(request, &limits)?),
            source_package_state_sha256: bound.source.package_state_sha256.clone(),
            source_section_sha256: bound.source.section_sha256.clone(),
            output_section_sha256: hex(Sha256::digest(&output_part.bytes).into()),
            source_paragraph_sha256: bound.source.paragraph_sha256.clone(),
            source_run_sha256: bound.source.run_sha256.clone(),
            source_object_ids_sha256: bound.source.object_ids_sha256.clone(),
            semantic_sha256: request.semantic_sha256.clone(),
            script_sha256: request.script_sha256.clone(),
            object_id: request.object_id,
            layout: request.layout,
            render_required: request.extent.render_required,
            source_equation_count: bound.source.equation_count,
            output_equation_count: output_shape.readback.native_object_count,
            changed_parts: patch.changed_parts(),
            untouched_parts: patch.untouched_parts(),
            preservation_verified: true,
            native_readback_verified: true,
            before_document_flow_sha256: request.expected_document_flow_sha256.clone(),
            after_document_flow_sha256: request.target_document_flow_sha256.clone(),
        };
        let _ = receipt.canonical_json(limits)?;
        Ok(EquationHwpxLowered { patch, receipt })
    }
}

#[derive(Debug, Error)]
pub enum EquationHwpxError {
    #[error("native equation limit configuration is invalid")]
    InvalidLimit,
    #[error("native equation input is empty or exceeds its finite bound")]
    InputLimit,
    #[error("native equation JSON is malformed, duplicated, or not strict")]
    InvalidJson,
    #[error("native equation request schema is unsupported")]
    UnsupportedVersion,
    #[error("native equation target profile is unsupported")]
    UnsupportedProfile,
    #[error("native equation digest binding is invalid")]
    InvalidBinding,
    #[error("native equation source state drifted")]
    SourceDrift,
    #[error("native equation document flow drifted")]
    FlowDrift,
    #[error("native equation insertion target has an unsupported shape")]
    UnsupportedTarget,
    #[error("native equation style is outside the current profile")]
    UnsupportedStyle,
    #[error("native equation extent is invalid or lacks required evidence")]
    InvalidExtent,
    #[error("native equation object identifier is invalid")]
    InvalidObjectId,
    #[error("native equation object identifier collides with the source package")]
    ObjectIdCollision,
    #[error("native equation AST admission failed")]
    MathAst,
    #[error("native equation EqEdit compilation or parsing failed")]
    EqEdit,
    #[error("native equation script exceeds its finite bound")]
    ScriptLimit,
    #[error("native equation request and build products drifted")]
    BuildDrift,
    #[error("native equation output failed strict semantic readback")]
    ReadbackMismatch,
    #[error("native equation patch modified bytes outside the inserted object")]
    PreservationMismatch,
    #[error("native equation output exceeds its finite bound")]
    OutputLimit,
    #[error("native equation result serialization failed")]
    Serialization,
    #[error("native equation allocation failed")]
    Allocation,
    #[error("bounded package read failed")]
    Package(#[from] PackageError),
    #[error("closed package graph validation failed")]
    Graph(#[from] GraphError),
    #[error("preserving XML validation failed")]
    Xml(#[from] PreservingXmlError),
    #[error("preserving package patch failed")]
    Patch(#[from] PatchError),
}

impl EquationHwpxError {
    #[must_use]
    pub fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "equation_hwpx_invalid_limit",
            Self::InputLimit => "equation_hwpx_input_limit",
            Self::InvalidJson => "equation_hwpx_invalid_json",
            Self::UnsupportedVersion => "equation_hwpx_unsupported_version",
            Self::UnsupportedProfile => "equation_hwpx_unsupported_profile",
            Self::InvalidBinding => "equation_hwpx_invalid_binding",
            Self::SourceDrift => "equation_hwpx_source_drift",
            Self::FlowDrift => "equation_hwpx_flow_drift",
            Self::UnsupportedTarget => "equation_hwpx_unsupported_target",
            Self::UnsupportedStyle => "equation_hwpx_unsupported_style",
            Self::InvalidExtent => "equation_hwpx_invalid_extent",
            Self::InvalidObjectId => "equation_hwpx_invalid_object_id",
            Self::ObjectIdCollision => "equation_hwpx_object_id_collision",
            Self::MathAst => "equation_hwpx_math_ast",
            Self::EqEdit => "equation_hwpx_eqedit",
            Self::ScriptLimit => "equation_hwpx_script_limit",
            Self::BuildDrift => "equation_hwpx_build_drift",
            Self::ReadbackMismatch => "equation_hwpx_readback_mismatch",
            Self::PreservationMismatch => "equation_hwpx_preservation_mismatch",
            Self::OutputLimit => "equation_hwpx_output_limit",
            Self::Serialization => "equation_hwpx_serialization",
            Self::Allocation => "equation_hwpx_allocation",
            Self::Package(error) => error.code(),
            Self::Graph(error) => error.code(),
            Self::Xml(error) => error.code(),
            Self::Patch(error) => error.code(),
        }
    }
}

struct BoundSource {
    source: EquationHwpxSource,
    path: PackagePath,
    bytes: Vec<u8>,
    document: PreservingXmlDocument,
    target_text_element: usize,
    insertion_equation_ordinal: usize,
    object_ids: BTreeSet<u32>,
}

struct EquationShape {
    readback: EquationHwpxReadback,
    equation_span: crate::XmlByteSpan,
}

fn inspect_bound_source<R: Read + Seek>(
    reader: &mut BoundedZipReader<R>,
    graph: &PackageGraph,
    section_part: &str,
    paragraph_ordinal: usize,
    run_ordinal: usize,
    layout: EquationLayout,
    limits: &EquationHwpxLimits,
) -> Result<BoundSource, EquationHwpxError> {
    let (path, bytes) = read_spine_part(reader, graph, section_part, limits)?;
    let document = parse_section(&bytes, limits)?;
    let root = element(&document, document.root_element())?;
    if root.name().namespace() != Some(SECTION_NS) || root.name().local_name() != "sec" {
        return Err(EquationHwpxError::UnsupportedTarget);
    }
    let paragraphs = direct_children_named(&document, document.root_element(), "p")?;
    let paragraph = *paragraphs
        .get(paragraph_ordinal)
        .ok_or(EquationHwpxError::UnsupportedTarget)?;
    let runs = direct_children_named(&document, paragraph, "run")?;
    let run = *runs
        .get(run_ordinal)
        .ok_or(EquationHwpxError::UnsupportedTarget)?;
    let run_children = child_indexes(&document, run)?;
    if run_children.len() != 1
        || !has_name(element(&document, run_children[0])?, "t")
        || !element(&document, run_children[0])?.is_empty()
    {
        return Err(EquationHwpxError::UnsupportedTarget);
    }
    match layout {
        EquationLayout::Display if runs.len() != 1 => {
            return Err(EquationHwpxError::UnsupportedTarget);
        }
        EquationLayout::Inline
            if !paragraph_has_other_visible_content(&document, paragraph, run)? =>
        {
            return Err(EquationHwpxError::UnsupportedTarget);
        }
        _ => {}
    }
    let (_, equation_count) = object_ids(&document, limits)?;
    let object_ids = package_object_ids(reader, graph, limits)?;
    let insertion_equation_ordinal = document
        .elements()
        .iter()
        .take(run_children[0])
        .filter(|candidate| has_name(candidate, "equation"))
        .count();
    let paragraph_span = element(&document, paragraph)?
        .outer_span()
        .ok_or(EquationHwpxError::UnsupportedTarget)?;
    let run_span = element(&document, run)?
        .outer_span()
        .ok_or(EquationHwpxError::UnsupportedTarget)?;
    let source = EquationHwpxSource {
        profile_id: EQUATION_HWPX_PROFILE_ID,
        section_part: path.as_str().to_owned(),
        paragraph_ordinal,
        run_ordinal,
        layout,
        package_state_sha256: package_state_sha256(graph),
        section_sha256: hex(Sha256::digest(&bytes).into()),
        paragraph_sha256: hex(
            Sha256::digest(document.source_text(paragraph_span)?.as_bytes()).into(),
        ),
        run_sha256: hex(Sha256::digest(document.source_text(run_span)?.as_bytes()).into()),
        object_ids_sha256: object_ids_sha256(&object_ids),
        object_id_count: object_ids.len(),
        equation_count,
    };
    let target_text_element = run_children[0];
    Ok(BoundSource {
        source,
        path,
        bytes,
        document,
        target_text_element,
        insertion_equation_ordinal,
        object_ids,
    })
}

fn package_object_ids<R: Read + Seek>(
    reader: &mut BoundedZipReader<R>,
    graph: &PackageGraph,
    limits: &EquationHwpxLimits,
) -> Result<BTreeSet<u32>, EquationHwpxError> {
    let paths = graph
        .spine
        .iter()
        .map(|path| path.as_str().to_owned())
        .collect::<Vec<_>>();
    let mut package_ids = BTreeSet::new();
    for path in paths {
        let (_, bytes) = read_spine_part(reader, graph, &path, limits)?;
        let document = parse_section(&bytes, limits)?;
        let (part_ids, _) = object_ids(&document, limits)?;
        for id in part_ids {
            if !package_ids.insert(id) {
                return Err(EquationHwpxError::ObjectIdCollision);
            }
            if package_ids.len() > limits.native.equations {
                return Err(EquationHwpxError::InputLimit);
            }
        }
    }
    Ok(package_ids)
}

fn read_spine_part<R: Read + Seek>(
    reader: &mut BoundedZipReader<R>,
    graph: &PackageGraph,
    section_part: &str,
    limits: &EquationHwpxLimits,
) -> Result<(PackagePath, Vec<u8>), EquationHwpxError> {
    let path = PackagePath::parse(section_part.as_bytes(), 0, limits.package)?;
    let record = graph
        .parts
        .iter()
        .find(|record| record.path == path)
        .ok_or(EquationHwpxError::UnsupportedTarget)?;
    if record.role != PartRole::SpineDocument || !graph.spine.iter().any(|value| value == &path) {
        return Err(EquationHwpxError::UnsupportedTarget);
    }
    let entry = reader
        .entries()
        .iter()
        .find(|entry| entry.path == path)
        .map(|entry| entry.index)
        .ok_or(EquationHwpxError::UnsupportedTarget)?;
    let bytes = reader.read_entry(entry)?;
    if bytes.len() > limits.native.section_bytes
        || <[u8; 32]>::from(Sha256::digest(&bytes)) != record.raw_sha256
    {
        return Err(EquationHwpxError::SourceDrift);
    }
    Ok((path, bytes))
}

fn validate_request_source(
    request: &EquationHwpxRequest,
    source: &EquationHwpxSource,
    current_document_flow_sha256: &str,
) -> Result<(), EquationHwpxError> {
    require_digest(current_document_flow_sha256)?;
    if request.section_part != source.section_part
        || request.paragraph_ordinal != source.paragraph_ordinal
        || request.run_ordinal != source.run_ordinal
        || request.layout != source.layout
        || request.expected_package_state_sha256 != source.package_state_sha256
        || request.expected_section_sha256 != source.section_sha256
        || request.expected_paragraph_sha256 != source.paragraph_sha256
        || request.expected_run_sha256 != source.run_sha256
        || request.expected_object_ids_sha256 != source.object_ids_sha256
    {
        return Err(EquationHwpxError::SourceDrift);
    }
    if request.expected_document_flow_sha256 != current_document_flow_sha256
        || request.expected_document_flow_sha256 == request.target_document_flow_sha256
    {
        return Err(EquationHwpxError::FlowDrift);
    }
    Ok(())
}

fn validate_style(style: &EquationStyle) -> Result<(), EquationHwpxError> {
    if !(100..=20_000).contains(&style.base_unit) || style.baseline_percent > 100 {
        return Err(EquationHwpxError::UnsupportedStyle);
    }
    Ok(())
}

fn validate_extent(
    extent: &EquationExtent,
    limits: &EquationHwpxLimits,
) -> Result<(), EquationHwpxError> {
    if extent.width_hwpunit == 0
        || extent.height_hwpunit == 0
        || extent.width_hwpunit > limits.native.extent_hwpunit
        || extent.height_hwpunit > limits.native.extent_hwpunit
    {
        return Err(EquationHwpxError::InvalidExtent);
    }
    // P07-07 owns estimator qualification. P07-05 may carry the future enum in its versioned
    // protocol, but it only admits an explicitly provisional extent and therefore cannot silently
    // turn an arbitrary constant or caller assertion into verified layout evidence.
    if extent.source != EquationExtentSource::Provisional
        || extent.source_evidence_sha256.is_some()
        || !extent.render_required
    {
        return Err(EquationHwpxError::InvalidExtent);
    }
    Ok(())
}

fn equation_fragment(
    request: &EquationHwpxRequest,
    script: &str,
) -> Result<Vec<u8>, EquationHwpxError> {
    let color = format!(
        "#{:02X}{:02X}{:02X}",
        request.style.text_color.red, request.style.text_color.green, request.style.text_color.blue
    );
    let escaped = escape_xml_text(script)?;
    let xml = format!(
        concat!(
            "<hp:equation xmlns:hp=\"{ns}\" id=\"{id}\" zOrder=\"0\" numberingType=\"EQUATION\" ",
            "textWrap=\"TOP_AND_BOTTOM\" textFlow=\"BOTH_SIDES\" lock=\"0\" dropcapstyle=\"None\" ",
            "version=\"{version}\" baseLine=\"{baseline}\" textColor=\"{color}\" baseUnit=\"{base_unit}\" ",
            "lineMode=\"CHAR\" font=\"{font}\">",
            "<hp:sz width=\"{width}\" widthRelTo=\"ABSOLUTE\" height=\"{height}\" heightRelTo=\"ABSOLUTE\" protect=\"0\"/>",
            "<hp:pos treatAsChar=\"1\" affectLSpacing=\"1\" flowWithText=\"1\" allowOverlap=\"0\" ",
            "holdAnchorAndSO=\"0\" vertRelTo=\"PARA\" horzRelTo=\"COLUMN\" vertAlign=\"TOP\" ",
            "horzAlign=\"LEFT\" vertOffset=\"0\" horzOffset=\"0\"/>",
            "<hp:outMargin left=\"0\" right=\"0\" top=\"0\" bottom=\"0\"/>",
            "<hp:script>{script}</hp:script></hp:equation>"
        ),
        ns = PARAGRAPH_NS,
        id = request.object_id,
        version = EQUATION_VERSION,
        baseline = request.style.baseline_percent,
        color = color,
        base_unit = request.style.base_unit,
        font = EQUATION_FONT,
        width = request.extent.width_hwpunit,
        height = request.extent.height_hwpunit,
        script = escaped,
    );
    Ok(xml.into_bytes())
}

#[allow(clippy::too_many_lines)]
fn read_equation_shape(
    bytes: &[u8],
    equation_ordinal: usize,
    limits: &EquationHwpxLimits,
) -> Result<EquationShape, EquationHwpxError> {
    let document = parse_section(bytes, limits)?;
    let root = element(&document, document.root_element())?;
    if root.name().namespace() != Some(SECTION_NS) || root.name().local_name() != "sec" {
        return Err(EquationHwpxError::UnsupportedTarget);
    }
    let equations = document
        .elements()
        .iter()
        .enumerate()
        .filter(|(_, candidate)| has_name(candidate, "equation"))
        .map(|(index, _)| index)
        .collect::<Vec<_>>();
    if equations.len() > limits.native.equations {
        return Err(EquationHwpxError::InputLimit);
    }
    let equation_index = *equations
        .get(equation_ordinal)
        .ok_or(EquationHwpxError::UnsupportedTarget)?;
    let equation = element(&document, equation_index)?;
    validate_attributes(
        equation,
        &[
            "id",
            "zOrder",
            "numberingType",
            "textWrap",
            "textFlow",
            "lock",
            "dropcapstyle",
            "version",
            "baseLine",
            "textColor",
            "baseUnit",
            "lineMode",
            "font",
        ],
    )?;
    require_attr(equation, "zOrder", "0")?;
    require_attr(equation, "numberingType", "EQUATION")?;
    require_attr(equation, "textWrap", "TOP_AND_BOTTOM")?;
    require_attr(equation, "textFlow", "BOTH_SIDES")?;
    require_attr(equation, "lock", "0")?;
    require_attr(equation, "dropcapstyle", "None")?;
    require_attr(equation, "version", EQUATION_VERSION)?;
    require_attr(equation, "lineMode", "CHAR")?;
    require_attr(equation, "font", EQUATION_FONT)?;
    let object_id = parse_u32(attr(equation, "id")?)?;
    let baseline_percent = parse_u8(attr(equation, "baseLine")?)?;
    let base_unit = parse_u32(attr(equation, "baseUnit")?)?;
    let text_color = parse_color(attr(equation, "textColor")?)?;
    let layout = infer_layout_context(&document, equation_index)?;
    let children = child_indexes(&document, equation_index)?;
    if children.len() != 4
        || !has_name(element(&document, children[0])?, "sz")
        || !has_name(element(&document, children[1])?, "pos")
        || !has_name(element(&document, children[2])?, "outMargin")
        || !has_name(element(&document, children[3])?, "script")
    {
        return Err(EquationHwpxError::ReadbackMismatch);
    }
    let size = element(&document, children[0])?;
    validate_attributes(
        size,
        &["width", "widthRelTo", "height", "heightRelTo", "protect"],
    )?;
    require_attr(size, "widthRelTo", "ABSOLUTE")?;
    require_attr(size, "heightRelTo", "ABSOLUTE")?;
    require_attr(size, "protect", "0")?;
    let position = element(&document, children[1])?;
    validate_attributes(
        position,
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
    )?;
    for (name, value) in [
        ("treatAsChar", "1"),
        ("affectLSpacing", "1"),
        ("flowWithText", "1"),
        ("allowOverlap", "0"),
        ("holdAnchorAndSO", "0"),
        ("vertRelTo", "PARA"),
        ("horzRelTo", "COLUMN"),
        ("vertAlign", "TOP"),
        ("horzAlign", "LEFT"),
        ("vertOffset", "0"),
        ("horzOffset", "0"),
    ] {
        require_attr(position, name, value)?;
    }
    let margin = element(&document, children[2])?;
    validate_attributes(margin, &["left", "right", "top", "bottom"])?;
    for name in ["left", "right", "top", "bottom"] {
        require_attr(margin, name, "0")?;
    }
    let script_element = element(&document, children[3])?;
    validate_attributes(script_element, &[])?;
    if script_element.first_child().is_some() || script_element.is_empty() {
        return Err(EquationHwpxError::ReadbackMismatch);
    }
    let script = element_text(&document, children[3], limits.native.script_bytes)?;
    if script.is_empty() {
        return Err(EquationHwpxError::ReadbackMismatch);
    }
    let parsed = EqEditEngine::new(limits.eqedit, limits.math)
        .map_err(|_| EquationHwpxError::EqEdit)?
        .parse(equation_engine::EqEditParseRequestDraft {
            schema_version: equation_engine::EQEDIT_ADAPTER_SCHEMA_VERSION.to_owned(),
            profile_version: EQEDIT_PROFILE_VERSION.to_owned(),
            source: script.clone(),
        })
        .map_err(|_| EquationHwpxError::EqEdit)?;
    let style = EquationStyle {
        base_unit,
        baseline_percent,
        text_color,
    };
    validate_style(&style)?;
    let extent = EquationExtent {
        width_hwpunit: parse_u32(attr(size, "width")?)?,
        height_hwpunit: parse_u32(attr(size, "height")?)?,
        source: EquationExtentSource::Provisional,
        source_evidence_sha256: None,
        render_required: true,
    };
    // Evidence digests are protocol bindings and are intentionally not written into HWPX. A
    // readback can prove native values but not reconstruct the external receipt.
    validate_extent(&extent, limits)?;
    let ids = equation_ids(&document, limits)?;
    if ids.len() != equations.len() || !ids.contains(&object_id) {
        return Err(EquationHwpxError::ObjectIdCollision);
    }
    let equation_span = equation
        .outer_span()
        .ok_or(EquationHwpxError::ReadbackMismatch)?;
    Ok(EquationShape {
        readback: EquationHwpxReadback {
            profile_id: EQUATION_HWPX_PROFILE_ID,
            object_id,
            layout,
            style,
            extent,
            semantic_sha256: hex(parsed
                .ast()
                .semantic_sha256(limits.math)
                .map_err(|_| EquationHwpxError::MathAst)?),
            script_sha256: hex(Sha256::digest(script.as_bytes()).into()),
            script_length_bytes: u32::try_from(script.len())
                .map_err(|_| EquationHwpxError::ScriptLimit)?,
            equation_ordinal,
            native_object_count: equations.len(),
            render_required: true,
            math_ast: parsed.ast().clone(),
        },
        equation_span,
    })
}

fn infer_layout_context(
    document: &PreservingXmlDocument,
    equation: usize,
) -> Result<EquationLayout, EquationHwpxError> {
    let run = element(document, equation)?
        .parent()
        .ok_or(EquationHwpxError::ReadbackMismatch)?;
    if !has_name(element(document, run)?, "run") {
        return Err(EquationHwpxError::ReadbackMismatch);
    }
    let paragraph = element(document, run)?
        .parent()
        .ok_or(EquationHwpxError::ReadbackMismatch)?;
    if !has_name(element(document, paragraph)?, "p") {
        return Err(EquationHwpxError::ReadbackMismatch);
    }
    let runs = direct_children_named(document, paragraph, "run")?;
    let paragraph_children = child_indexes(document, paragraph)?;
    let run_children = child_indexes(document, run)?;
    if paragraph_children.len() != runs.len()
        || run_children.len() != 2
        || run_children[0] != equation
        || !has_name(element(document, run_children[1])?, "t")
        || !element(document, run_children[1])?.is_empty()
    {
        return Err(EquationHwpxError::ReadbackMismatch);
    }
    if runs.len() == 1 {
        Ok(EquationLayout::Display)
    } else if paragraph_has_other_visible_content(document, paragraph, run)? {
        Ok(EquationLayout::Inline)
    } else {
        Err(EquationHwpxError::ReadbackMismatch)
    }
}

fn paragraph_has_other_visible_content(
    document: &PreservingXmlDocument,
    paragraph: usize,
    selected_run: usize,
) -> Result<bool, EquationHwpxError> {
    let paragraph_span = element(document, paragraph)?
        .outer_span()
        .ok_or(EquationHwpxError::UnsupportedTarget)?;
    for token in document.tokens() {
        let Some(owner) = token.element_index() else {
            continue;
        };
        if token.span().start() < paragraph_span.start()
            || token.span().end() > paragraph_span.end()
        {
            continue;
        }
        if ancestor_is(document, owner, selected_run)? {
            continue;
        }
        if matches!(token.kind(), XmlTokenKind::Text | XmlTokenKind::Reference)
            && !document.source_text(token.span())?.trim().is_empty()
        {
            return Ok(true);
        }
    }
    Ok(false)
}

fn ancestor_is(
    document: &PreservingXmlDocument,
    mut element_index: usize,
    ancestor: usize,
) -> Result<bool, EquationHwpxError> {
    loop {
        if element_index == ancestor {
            return Ok(true);
        }
        let Some(parent) = element(document, element_index)?.parent() else {
            return Ok(false);
        };
        element_index = parent;
    }
}

fn object_ids(
    document: &PreservingXmlDocument,
    limits: &EquationHwpxLimits,
) -> Result<(BTreeSet<u32>, usize), EquationHwpxError> {
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
    let mut ids = BTreeSet::new();
    let mut equation_count = 0;
    for candidate in document.elements() {
        if has_name(candidate, "equation") {
            equation_count += 1;
        }
        if candidate.name().namespace() == Some(PARAGRAPH_NS)
            && object_names.contains(&candidate.name().local_name())
        {
            let id = parse_u32(attr(candidate, "id")?)?;
            if id == 0 || !ids.insert(id) {
                return Err(EquationHwpxError::ObjectIdCollision);
            }
            if ids.len() > limits.native.equations {
                return Err(EquationHwpxError::InputLimit);
            }
        }
    }
    Ok((ids, equation_count))
}

fn equation_ids(
    document: &PreservingXmlDocument,
    limits: &EquationHwpxLimits,
) -> Result<BTreeSet<u32>, EquationHwpxError> {
    let mut ids = BTreeSet::new();
    for equation in document
        .elements()
        .iter()
        .filter(|value| has_name(value, "equation"))
    {
        let id = parse_u32(attr(equation, "id")?)?;
        if id == 0 || !ids.insert(id) || ids.len() > limits.native.equations {
            return Err(EquationHwpxError::ObjectIdCollision);
        }
    }
    Ok(ids)
}

fn object_ids_sha256(ids: &BTreeSet<u32>) -> String {
    let mut digest = Sha256::new();
    digest.update(EQUATION_HWPX_PROFILE_ID.as_bytes());
    digest.update(b"\0object-ids\0");
    for id in ids {
        digest.update(id.to_be_bytes());
    }
    hex(digest.finalize().into())
}

fn package_state_sha256(graph: &PackageGraph) -> String {
    let mut digest = Sha256::new();
    digest.update(EQUATION_HWPX_PROFILE_ID.as_bytes());
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
    hex(digest.finalize().into())
}

fn parse_section(
    bytes: &[u8],
    limits: &EquationHwpxLimits,
) -> Result<PreservingXmlDocument, EquationHwpxError> {
    if bytes.is_empty() || bytes.len() > limits.native.section_bytes {
        return Err(EquationHwpxError::InputLimit);
    }
    let document = PreservingXmlDocument::parse(bytes)?;
    if document.elements().len() > limits.native.elements {
        return Err(EquationHwpxError::InputLimit);
    }
    Ok(document)
}

fn element(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<&XmlElementToken, EquationHwpxError> {
    document
        .elements()
        .get(index)
        .ok_or(EquationHwpxError::UnsupportedTarget)
}

fn has_name(element: &XmlElementToken, local_name: &str) -> bool {
    element.name().namespace() == Some(PARAGRAPH_NS) && element.name().local_name() == local_name
}

fn child_indexes(
    document: &PreservingXmlDocument,
    parent: usize,
) -> Result<Vec<usize>, EquationHwpxError> {
    let mut output = Vec::new();
    let mut current = element(document, parent)?.first_child();
    while let Some(index) = current {
        output
            .try_reserve(1)
            .map_err(|_| EquationHwpxError::Allocation)?;
        output.push(index);
        current = element(document, index)?.next_sibling();
    }
    Ok(output)
}

fn direct_children_named(
    document: &PreservingXmlDocument,
    parent: usize,
    local_name: &str,
) -> Result<Vec<usize>, EquationHwpxError> {
    Ok(child_indexes(document, parent)?
        .into_iter()
        .filter(|index| element(document, *index).is_ok_and(|value| has_name(value, local_name)))
        .collect())
}

fn validate_attributes(
    element: &XmlElementToken,
    allowed: &[&str],
) -> Result<(), EquationHwpxError> {
    let mut seen = BTreeSet::new();
    for attribute in element.attributes() {
        if attribute.is_namespace_declaration() {
            continue;
        }
        let name = attribute.name().local_name();
        if attribute.name().namespace().is_some() || !allowed.contains(&name) || !seen.insert(name)
        {
            return Err(EquationHwpxError::ReadbackMismatch);
        }
    }
    if seen.len() != allowed.len() {
        return Err(EquationHwpxError::ReadbackMismatch);
    }
    Ok(())
}

fn attr<'a>(element: &'a XmlElementToken, name: &str) -> Result<&'a str, EquationHwpxError> {
    let mut values = element
        .attributes()
        .iter()
        .filter(|attribute| {
            !attribute.is_namespace_declaration()
                && attribute.name().namespace().is_none()
                && attribute.name().local_name() == name
        })
        .map(crate::XmlAttributeToken::semantic_value);
    let value = values.next().ok_or(EquationHwpxError::ReadbackMismatch)?;
    if values.next().is_some() {
        return Err(EquationHwpxError::ReadbackMismatch);
    }
    Ok(value)
}

fn require_attr(
    element: &XmlElementToken,
    name: &str,
    value: &str,
) -> Result<(), EquationHwpxError> {
    if attr(element, name)? != value {
        return Err(EquationHwpxError::ReadbackMismatch);
    }
    Ok(())
}

fn element_text(
    document: &PreservingXmlDocument,
    element_index: usize,
    maximum: usize,
) -> Result<String, EquationHwpxError> {
    let span = element(document, element_index)?
        .content_span()
        .ok_or(EquationHwpxError::ReadbackMismatch)?;
    let raw = document.source_text(span)?;
    if raw.len() > maximum {
        return Err(EquationHwpxError::ScriptLimit);
    }
    decode_xml_text(raw)
}

fn decode_xml_text(raw: &str) -> Result<String, EquationHwpxError> {
    let value = raw
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", "\"")
        .replace("&apos;", "'")
        .replace("&amp;", "&");
    if value.contains('&') && raw.contains("&#") {
        return Err(EquationHwpxError::ReadbackMismatch);
    }
    Ok(value)
}

fn escape_xml_text(value: &str) -> Result<String, EquationHwpxError> {
    if value
        .chars()
        .any(|character| matches!(character as u32, 0..=8 | 11..=12 | 14..=31 | 0xFFFE | 0xFFFF))
    {
        return Err(EquationHwpxError::EqEdit);
    }
    Ok(value
        .replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;"))
}

fn parse_u32(value: &str) -> Result<u32, EquationHwpxError> {
    if value.is_empty()
        || (value.len() > 1 && value.starts_with('0'))
        || !value.bytes().all(|byte| byte.is_ascii_digit())
    {
        return Err(EquationHwpxError::ReadbackMismatch);
    }
    value
        .parse()
        .map_err(|_| EquationHwpxError::ReadbackMismatch)
}

fn parse_u8(value: &str) -> Result<u8, EquationHwpxError> {
    let value = parse_u32(value)?;
    u8::try_from(value).map_err(|_| EquationHwpxError::ReadbackMismatch)
}

fn parse_color(value: &str) -> Result<EquationColor, EquationHwpxError> {
    let hex = value
        .strip_prefix('#')
        .ok_or(EquationHwpxError::ReadbackMismatch)?;
    if hex.len() != 6
        || !hex.bytes().all(|byte| byte.is_ascii_hexdigit())
        || hex.bytes().any(|byte| byte.is_ascii_lowercase())
    {
        return Err(EquationHwpxError::ReadbackMismatch);
    }
    Ok(EquationColor {
        red: u8::from_str_radix(&hex[0..2], 16).map_err(|_| EquationHwpxError::ReadbackMismatch)?,
        green: u8::from_str_radix(&hex[2..4], 16)
            .map_err(|_| EquationHwpxError::ReadbackMismatch)?,
        blue: u8::from_str_radix(&hex[4..6], 16)
            .map_err(|_| EquationHwpxError::ReadbackMismatch)?,
    })
}

fn request_sha256(
    request: &EquationHwpxRequest,
    limits: &EquationHwpxLimits,
) -> Result<[u8; 32], EquationHwpxError> {
    Ok(Sha256::digest(bounded_json(request, limits)?).into())
}

fn bounded_json<T: Serialize>(
    value: &T,
    limits: &EquationHwpxLimits,
) -> Result<Vec<u8>, EquationHwpxError> {
    let bytes = serde_json::to_vec(value).map_err(|_| EquationHwpxError::Serialization)?;
    if bytes.len() > limits.native.serialized_bytes {
        return Err(EquationHwpxError::OutputLimit);
    }
    Ok(bytes)
}

fn require_digest(value: &str) -> Result<(), EquationHwpxError> {
    if value.len() != 64
        || value
            .bytes()
            .any(|byte| !byte.is_ascii_digit() && !(b'a'..=b'f').contains(&byte))
    {
        return Err(EquationHwpxError::InvalidBinding);
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

fn reject_duplicate_json_keys(bytes: &[u8]) -> Result<(), EquationHwpxError> {
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
        .map_err(|_| EquationHwpxError::InvalidJson)?;
    deserializer
        .end()
        .map_err(|_| EquationHwpxError::InvalidJson)
}
