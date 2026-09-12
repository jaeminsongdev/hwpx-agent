use std::fmt;

use domain_ir::{
    OBJECT_PROPERTIES_SCHEMA_VERSION, ObjectPropertiesBuilder, ObjectPropertiesError,
    ObjectPropertiesLimits, ObjectPropertiesPlan, ObjectPropertiesState, ObjectPropertyKind,
    ObjectPropertyMargins, ObjectTextBoxVerticalAlignment, TextBoxDirection, TextBoxProperties,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::preserving_xml::{
    PreservingXmlDocument, PreservingXmlError, XmlAttributeToken, XmlByteSpan, XmlElementToken,
};

pub const TEXTBOX_PROPERTIES_HWPX_PROFILE_ID: &str =
    "hwpx-agent.textbox-properties-hwpx.hwpml-2011-attribute-spans/v1";

const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TextBoxPropertiesHwpxLimitConfig {
    pub section_bytes: usize,
    pub elements: usize,
    pub objects: usize,
    pub edits: usize,
    pub output_bytes: usize,
    pub plan_bytes: usize,
}

impl Default for TextBoxPropertiesHwpxLimitConfig {
    fn default() -> Self {
        Self {
            section_bytes: 32 * 1024 * 1024,
            elements: 1_000_000,
            objects: 65_536,
            edits: 6,
            output_bytes: 32 * 1024 * 1024,
            plan_bytes: 2 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TextBoxPropertiesHwpxLimits(TextBoxPropertiesHwpxLimitConfig);

impl TextBoxPropertiesHwpxLimits {
    pub const HARD_MAX_SECTION_BYTES: usize = 128 * 1024 * 1024;
    pub const HARD_MAX_ELEMENTS: usize = 2_000_000;
    pub const HARD_MAX_OBJECTS: usize = 262_144;
    pub const HARD_MAX_EDITS: usize = 6;
    pub const HARD_MAX_OUTPUT_BYTES: usize = 128 * 1024 * 1024;
    pub const HARD_MAX_PLAN_BYTES: usize = 8 * 1024 * 1024;

    /// Creates finite exact-section limits without silently clamping values.
    ///
    /// # Errors
    ///
    /// Rejects zero, inconsistent, or hard-ceiling-exceeding limits.
    pub fn new(
        config: TextBoxPropertiesHwpxLimitConfig,
    ) -> Result<Self, TextBoxPropertiesHwpxError> {
        if config.section_bytes == 0
            || config.section_bytes > Self::HARD_MAX_SECTION_BYTES
            || config.elements == 0
            || config.elements > Self::HARD_MAX_ELEMENTS
            || config.objects == 0
            || config.objects > Self::HARD_MAX_OBJECTS
            || config.edits == 0
            || config.edits > Self::HARD_MAX_EDITS
            || config.output_bytes == 0
            || config.output_bytes > Self::HARD_MAX_OUTPUT_BYTES
            || config.section_bytes > config.output_bytes
            || config.plan_bytes == 0
            || config.plan_bytes > Self::HARD_MAX_PLAN_BYTES
        {
            return Err(TextBoxPropertiesHwpxError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> TextBoxPropertiesHwpxLimitConfig {
        self.0
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TextBoxPropertiesHwpxReadback {
    pub state: ObjectPropertiesState,
    pub properties: TextBoxProperties,
    pub section_sha256: [u8; 32],
    pub object_sha256: [u8; 32],
    pub draw_text_sha256: [u8; 32],
    pub margin_sha256: [u8; 32],
    pub sublist_sha256: [u8; 32],
    pub object_ordinal: usize,
}

impl fmt::Debug for TextBoxPropertiesHwpxReadback {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TextBoxPropertiesHwpxReadback")
            .field("object_ordinal", &self.object_ordinal)
            .field("object_kind", &self.state.object_kind())
            .field("identity", &"<redacted>")
            .field("properties", &"<redacted>")
            .field("digests", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Serialize)]
pub struct TextBoxPropertiesHwpxPlan {
    schema_version: &'static str,
    profile_id: &'static str,
    object_ordinal: usize,
    source_section_sha256: [u8; 32],
    source_object_sha256: [u8; 32],
    source_draw_text_sha256: [u8; 32],
    source_margin_sha256: [u8; 32],
    source_sublist_sha256: [u8; 32],
    source_document_flow_sha256: String,
    domain_plan: ObjectPropertiesPlan,
    domain_plan_sha256: String,
    plan_sha256: String,
}

impl TextBoxPropertiesHwpxPlan {
    #[must_use]
    pub const fn object_ordinal(&self) -> usize {
        self.object_ordinal
    }

    #[must_use]
    pub const fn domain_plan(&self) -> &ObjectPropertiesPlan {
        &self.domain_plan
    }

    #[must_use]
    pub fn plan_sha256(&self) -> &str {
        &self.plan_sha256
    }

    /// Returns deterministic bounded JSON for the immutable HWPX plan.
    ///
    /// # Errors
    ///
    /// Returns serialization or output-limit failure.
    pub fn canonical_json(
        &self,
        limits: TextBoxPropertiesHwpxLimits,
    ) -> Result<Vec<u8>, TextBoxPropertiesHwpxError> {
        serialize_bounded(self, limits)
    }
}

impl fmt::Debug for TextBoxPropertiesHwpxPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TextBoxPropertiesHwpxPlan")
            .field("profile_id", &self.profile_id)
            .field("object_ordinal", &self.object_ordinal)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TextBoxPropertiesHwpxLoweringReceipt {
    pub profile_id: &'static str,
    pub capability_id: &'static str,
    pub source_section_sha256: [u8; 32],
    pub output_section_sha256: [u8; 32],
    pub source_object_sha256: [u8; 32],
    pub output_object_sha256: [u8; 32],
    pub source_state_sha256: String,
    pub target_state_sha256: String,
    pub plan_sha256: String,
    pub target_document_flow_sha256: String,
    pub modified_attribute_count: usize,
    pub source_bytes: usize,
    pub output_bytes: usize,
}

impl fmt::Debug for TextBoxPropertiesHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TextBoxPropertiesHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field("capability_id", &self.capability_id)
            .field("modified_attribute_count", &self.modified_attribute_count)
            .field("source_bytes", &self.source_bytes)
            .field("output_bytes", &self.output_bytes)
            .field("digests", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum TextBoxPropertiesHwpxError {
    #[error("text-box properties HWPX limits are invalid")]
    InvalidLimit,
    #[error("text-box properties HWPX section exceeds a finite limit")]
    InputLimit,
    #[error("text-box properties HWPX target is absent, duplicated, or unsupported")]
    UnsupportedTextBox,
    #[error("text-box properties HWPX attributes are malformed or ambiguous")]
    InvalidAttribute,
    #[error("text-box properties HWPX number is noncanonical or out of range")]
    InvalidNumber,
    #[error("text-box properties HWPX enum is unsupported")]
    InvalidEnum,
    #[error("text-box properties HWPX section, object, payload, state, or flow drifted")]
    SourceDrift,
    #[error("text-box properties HWPX plan was tampered with")]
    PlanTampered,
    #[error("text-box properties HWPX semantic readback differs")]
    ReadbackMismatch,
    #[error("text-box properties HWPX preservation proof failed")]
    PreservationMismatch,
    #[error("text-box properties HWPX output exceeds a finite limit")]
    OutputLimit,
    #[error("text-box properties HWPX allocation failed")]
    AllocationFailed,
    #[error("text-box properties domain validation failed")]
    Domain(#[from] ObjectPropertiesError),
    #[error("text-box properties preserving XML admission failed")]
    Preserving(#[from] PreservingXmlError),
}

impl TextBoxPropertiesHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "textbox_properties_hwpx_invalid_limit",
            Self::InputLimit => "textbox_properties_hwpx_input_limit",
            Self::UnsupportedTextBox => "textbox_properties_hwpx_unsupported_textbox",
            Self::InvalidAttribute => "textbox_properties_hwpx_invalid_attribute",
            Self::InvalidNumber => "textbox_properties_hwpx_invalid_number",
            Self::InvalidEnum => "textbox_properties_hwpx_invalid_enum",
            Self::SourceDrift => "textbox_properties_hwpx_source_drift",
            Self::PlanTampered => "textbox_properties_hwpx_plan_tampered",
            Self::ReadbackMismatch => "textbox_properties_hwpx_readback_mismatch",
            Self::PreservationMismatch => "textbox_properties_hwpx_preservation_mismatch",
            Self::OutputLimit => "textbox_properties_hwpx_output_limit",
            Self::AllocationFailed => "textbox_properties_hwpx_allocation_failed",
            Self::Domain(_) => "textbox_properties_hwpx_domain",
            Self::Preserving(_) => "textbox_properties_hwpx_preserving_xml",
        }
    }
}

#[derive(Debug)]
pub struct TextBoxPropertiesHwpxReader;

impl TextBoxPropertiesHwpxReader {
    /// Reads one exact run-level native text box against a complete expected state.
    ///
    /// # Errors
    ///
    /// Rejects malformed, nested-only, ambiguous, stale, or over-limit XML.
    pub fn read_in_section(
        source: &[u8],
        object_ordinal: usize,
        expected: &ObjectPropertiesState,
        state_limits: ObjectPropertiesLimits,
        hwpx_limits: TextBoxPropertiesHwpxLimits,
    ) -> Result<TextBoxPropertiesHwpxReadback, TextBoxPropertiesHwpxError> {
        let parsed = parse_selected(source, object_ordinal, state_limits, hwpx_limits)?;
        if expected.object_kind() != ObjectPropertyKind::TextBox
            || expected.native_object_id() != parsed.native_object_id
            || expected.native_instance_id() != parsed.native_instance_id
            || expected.text_box() != Some(parsed.properties)
        {
            return Err(TextBoxPropertiesHwpxError::SourceDrift);
        }
        Ok(TextBoxPropertiesHwpxReadback {
            state: expected.clone(),
            properties: parsed.properties,
            section_sha256: Sha256::digest(source).into(),
            object_sha256: parsed.object_sha256,
            draw_text_sha256: parsed.draw_text_sha256,
            margin_sha256: parsed.margin_sha256,
            sublist_sha256: parsed.sublist_sha256,
            object_ordinal,
        })
    }
}

#[derive(Debug)]
pub struct TextBoxPropertiesHwpxBuilder;

impl TextBoxPropertiesHwpxBuilder {
    /// Binds a validated property plan to one exact section/text-box attribute set.
    ///
    /// # Errors
    ///
    /// Rejects domain, source-state, flow, XML, or finite-limit drift.
    pub fn plan(
        source: &[u8],
        object_ordinal: usize,
        domain_plan: &ObjectPropertiesPlan,
        current_document_flow_sha256: &str,
        state_limits: ObjectPropertiesLimits,
        hwpx_limits: TextBoxPropertiesHwpxLimits,
    ) -> Result<TextBoxPropertiesHwpxPlan, TextBoxPropertiesHwpxError> {
        if domain_plan.capability_id() != "obj.textbox_properties"
            || domain_plan.source_document_flow_sha256() != current_document_flow_sha256
        {
            return Err(TextBoxPropertiesHwpxError::SourceDrift);
        }
        let readback = TextBoxPropertiesHwpxReader::read_in_section(
            source,
            object_ordinal,
            domain_plan.source_state(),
            state_limits,
            hwpx_limits,
        )?;
        let _ = ObjectPropertiesBuilder::build(
            domain_plan,
            domain_plan.source_state(),
            current_document_flow_sha256,
            state_limits,
        )?;
        let domain_plan_sha256 = domain_plan.plan_sha256().to_owned();
        let mut plan = TextBoxPropertiesHwpxPlan {
            schema_version: OBJECT_PROPERTIES_SCHEMA_VERSION,
            profile_id: TEXTBOX_PROPERTIES_HWPX_PROFILE_ID,
            object_ordinal,
            source_section_sha256: readback.section_sha256,
            source_object_sha256: readback.object_sha256,
            source_draw_text_sha256: readback.draw_text_sha256,
            source_margin_sha256: readback.margin_sha256,
            source_sublist_sha256: readback.sublist_sha256,
            source_document_flow_sha256: current_document_flow_sha256.to_owned(),
            domain_plan: domain_plan.clone(),
            domain_plan_sha256,
            plan_sha256: String::new(),
        };
        plan.plan_sha256 = plan_binding_sha256(&plan, hwpx_limits)?;
        let _ = plan.canonical_json(hwpx_limits)?;
        Ok(plan)
    }
}

#[derive(Debug)]
pub struct TextBoxPropertiesHwpxLowerer;

impl TextBoxPropertiesHwpxLowerer {
    /// Revalidates and patches only six reviewed native attribute values.
    ///
    /// # Errors
    ///
    /// Returns no bytes on plan, source, state, flow, preservation, or readback drift.
    #[allow(clippy::too_many_lines)]
    pub fn lower_in_section_with_receipt(
        source: &[u8],
        plan: &TextBoxPropertiesHwpxPlan,
        current_document_flow_sha256: &str,
        state_limits: ObjectPropertiesLimits,
        hwpx_limits: TextBoxPropertiesHwpxLimits,
    ) -> Result<(Vec<u8>, TextBoxPropertiesHwpxLoweringReceipt), TextBoxPropertiesHwpxError> {
        validate_plan(plan, hwpx_limits)?;
        if Sha256::digest(source).as_slice() != plan.source_section_sha256
            || current_document_flow_sha256 != plan.source_document_flow_sha256
            || current_document_flow_sha256 != plan.domain_plan.source_document_flow_sha256()
            || plan.domain_plan.plan_sha256() != plan.domain_plan_sha256
        {
            return Err(TextBoxPropertiesHwpxError::SourceDrift);
        }
        let source_readback = TextBoxPropertiesHwpxReader::read_in_section(
            source,
            plan.object_ordinal,
            plan.domain_plan.source_state(),
            state_limits,
            hwpx_limits,
        )?;
        if source_readback.object_sha256 != plan.source_object_sha256
            || source_readback.draw_text_sha256 != plan.source_draw_text_sha256
            || source_readback.margin_sha256 != plan.source_margin_sha256
            || source_readback.sublist_sha256 != plan.source_sublist_sha256
        {
            return Err(TextBoxPropertiesHwpxError::SourceDrift);
        }
        let result = ObjectPropertiesBuilder::build(
            &plan.domain_plan,
            plan.domain_plan.source_state(),
            current_document_flow_sha256,
            state_limits,
        )?;
        let target_state = result.state;
        let source_properties = plan
            .domain_plan
            .source_state()
            .text_box()
            .ok_or(TextBoxPropertiesHwpxError::SourceDrift)?;
        let target_properties = target_state
            .text_box()
            .ok_or(TextBoxPropertiesHwpxError::PlanTampered)?;
        let parsed = parse_selected(source, plan.object_ordinal, state_limits, hwpx_limits)?;
        let mut edits = property_edits(&parsed, source_properties, target_properties, hwpx_limits)?;
        if edits.is_empty() || edits.len() > hwpx_limits.0.edits {
            return Err(TextBoxPropertiesHwpxError::PlanTampered);
        }
        let modified_attribute_count = edits.len();
        let output = apply_edits(source, &mut edits, hwpx_limits)?;
        verify_preservation(source, &output, &edits)?;
        let output_readback = TextBoxPropertiesHwpxReader::read_in_section(
            &output,
            plan.object_ordinal,
            &target_state,
            state_limits,
            hwpx_limits,
        )?;
        if output_readback.properties != target_properties {
            return Err(TextBoxPropertiesHwpxError::ReadbackMismatch);
        }
        let receipt = TextBoxPropertiesHwpxLoweringReceipt {
            profile_id: TEXTBOX_PROPERTIES_HWPX_PROFILE_ID,
            capability_id: "obj.textbox_properties",
            source_section_sha256: source_readback.section_sha256,
            output_section_sha256: output_readback.section_sha256,
            source_object_sha256: source_readback.object_sha256,
            output_object_sha256: output_readback.object_sha256,
            source_state_sha256: plan
                .domain_plan
                .source_state()
                .canonical_sha256(state_limits)?,
            target_state_sha256: target_state.canonical_sha256(state_limits)?,
            plan_sha256: plan.plan_sha256.clone(),
            target_document_flow_sha256: plan.domain_plan.target_document_flow_sha256().to_owned(),
            modified_attribute_count,
            source_bytes: source.len(),
            output_bytes: output.len(),
        };
        Ok((output, receipt))
    }

    /// Returns preserving section bytes after the same fail-closed checks.
    ///
    /// # Errors
    ///
    /// Applies the same validation as [`Self::lower_in_section_with_receipt`].
    pub fn lower_in_section(
        source: &[u8],
        plan: &TextBoxPropertiesHwpxPlan,
        current_document_flow_sha256: &str,
        state_limits: ObjectPropertiesLimits,
        hwpx_limits: TextBoxPropertiesHwpxLimits,
    ) -> Result<Vec<u8>, TextBoxPropertiesHwpxError> {
        Self::lower_in_section_with_receipt(
            source,
            plan,
            current_document_flow_sha256,
            state_limits,
            hwpx_limits,
        )
        .map(|(bytes, _)| bytes)
    }
}

struct ParsedTextBox {
    document: PreservingXmlDocument,
    margin: usize,
    sublist: usize,
    native_object_id: u32,
    native_instance_id: u32,
    properties: TextBoxProperties,
    object_sha256: [u8; 32],
    draw_text_sha256: [u8; 32],
    margin_sha256: [u8; 32],
    sublist_sha256: [u8; 32],
}

#[allow(clippy::too_many_lines)] // Keeps the six reviewed native fields in one auditable parse.
fn parse_selected(
    source: &[u8],
    object_ordinal: usize,
    state_limits: ObjectPropertiesLimits,
    limits: TextBoxPropertiesHwpxLimits,
) -> Result<ParsedTextBox, TextBoxPropertiesHwpxError> {
    if source.is_empty()
        || source.len() > limits.0.section_bytes
        || object_ordinal >= limits.0.objects
    {
        return Err(TextBoxPropertiesHwpxError::InputLimit);
    }
    let document = PreservingXmlDocument::parse(source)?;
    if document.elements().len() > limits.0.elements {
        return Err(TextBoxPropertiesHwpxError::InputLimit);
    }
    let root = selected_run_object(&document, object_ordinal, limits)?;
    let root_element = element(&document, root)?;
    if !has_name(root_element, "rect") {
        return Err(TextBoxPropertiesHwpxError::UnsupportedTextBox);
    }
    let native_object_id = canonical_u32(source, strict_attribute(root_element, "id")?, u32::MAX)?;
    let native_instance_id =
        canonical_u32(source, strict_attribute(root_element, "instid")?, u32::MAX)?;
    if native_object_id == 0 || native_instance_id == 0 {
        return Err(TextBoxPropertiesHwpxError::InvalidNumber);
    }
    let draw_text_children = direct_children_named(&document, root, "drawText")?;
    if draw_text_children.len() != 1
        || descendants_named(&document, root, "drawText")? != draw_text_children
    {
        return Err(TextBoxPropertiesHwpxError::UnsupportedTextBox);
    }
    let draw_text = draw_text_children[0];
    let children = direct_children(&document, draw_text)?;
    if children.len() != 2
        || !has_name(element(&document, children[0])?, "textMargin")
        || !has_name(element(&document, children[1])?, "subList")
    {
        return Err(TextBoxPropertiesHwpxError::UnsupportedTextBox);
    }
    let margin = children[0];
    let sublist = children[1];
    if descendants_named(&document, draw_text, "textMargin")? != vec![margin]
        || descendants_named(&document, draw_text, "subList")? != vec![sublist]
        || !element(&document, margin)?.is_empty()
    {
        return Err(TextBoxPropertiesHwpxError::UnsupportedTextBox);
    }
    let maximum = state_limits.config().extent_hwpunit;
    let margins = ObjectPropertyMargins {
        left_hwpunit: canonical_u32(
            source,
            strict_attribute(element(&document, margin)?, "left")?,
            maximum,
        )?,
        right_hwpunit: canonical_u32(
            source,
            strict_attribute(element(&document, margin)?, "right")?,
            maximum,
        )?,
        top_hwpunit: canonical_u32(
            source,
            strict_attribute(element(&document, margin)?, "top")?,
            maximum,
        )?,
        bottom_hwpunit: canonical_u32(
            source,
            strict_attribute(element(&document, margin)?, "bottom")?,
            maximum,
        )?,
    };
    let direction = match lexical_value(
        source,
        strict_attribute(element(&document, sublist)?, "textDirection")?,
    )? {
        "HORIZONTAL" => TextBoxDirection::Horizontal,
        "VERTICAL" => TextBoxDirection::Vertical,
        "VERTICALALL" => TextBoxDirection::VerticalRightToLeft,
        _ => return Err(TextBoxPropertiesHwpxError::InvalidEnum),
    };
    let vertical_alignment = match lexical_value(
        source,
        strict_attribute(element(&document, sublist)?, "vertAlign")?,
    )? {
        "TOP" => ObjectTextBoxVerticalAlignment::Top,
        "CENTER" => ObjectTextBoxVerticalAlignment::Center,
        "BOTTOM" => ObjectTextBoxVerticalAlignment::Bottom,
        _ => return Err(TextBoxPropertiesHwpxError::InvalidEnum),
    };
    let object_span = outer_span(root_element)?;
    let draw_text_span = outer_span(element(&document, draw_text)?)?;
    let margin_span = outer_span(element(&document, margin)?)?;
    let sublist_span = outer_span(element(&document, sublist)?)?;
    Ok(ParsedTextBox {
        document,
        margin,
        sublist,
        native_object_id,
        native_instance_id,
        properties: TextBoxProperties {
            margins,
            vertical_alignment,
            direction,
        },
        object_sha256: digest_span(source, object_span)?,
        draw_text_sha256: digest_span(source, draw_text_span)?,
        margin_sha256: digest_span(source, margin_span)?,
        sublist_sha256: digest_span(source, sublist_span)?,
    })
}

fn property_edits(
    parsed: &ParsedTextBox,
    source: TextBoxProperties,
    target: TextBoxProperties,
    limits: TextBoxPropertiesHwpxLimits,
) -> Result<Vec<ByteEdit>, TextBoxPropertiesHwpxError> {
    let mut edits = Vec::new();
    edits
        .try_reserve_exact(limits.0.edits)
        .map_err(|_| TextBoxPropertiesHwpxError::AllocationFailed)?;
    for (name, old, new) in [
        (
            "left",
            source.margins.left_hwpunit,
            target.margins.left_hwpunit,
        ),
        (
            "right",
            source.margins.right_hwpunit,
            target.margins.right_hwpunit,
        ),
        (
            "top",
            source.margins.top_hwpunit,
            target.margins.top_hwpunit,
        ),
        (
            "bottom",
            source.margins.bottom_hwpunit,
            target.margins.bottom_hwpunit,
        ),
    ] {
        push_change(
            &parsed.document,
            parsed.margin,
            name,
            old,
            new,
            new.to_string(),
            &mut edits,
        )?;
    }
    push_change(
        &parsed.document,
        parsed.sublist,
        "textDirection",
        source.direction,
        target.direction,
        direction_text(target.direction).to_owned(),
        &mut edits,
    )?;
    push_change(
        &parsed.document,
        parsed.sublist,
        "vertAlign",
        source.vertical_alignment,
        target.vertical_alignment,
        vertical_alignment_text(target.vertical_alignment).to_owned(),
        &mut edits,
    )?;
    Ok(edits)
}

#[derive(Debug)]
struct ByteEdit {
    span: XmlByteSpan,
    replacement: Vec<u8>,
}

#[allow(clippy::needless_pass_by_value)]
fn push_change<T: Eq>(
    document: &PreservingXmlDocument,
    element_index: usize,
    name: &str,
    source: T,
    target: T,
    replacement: String,
    edits: &mut Vec<ByteEdit>,
) -> Result<(), TextBoxPropertiesHwpxError> {
    if source == target {
        return Ok(());
    }
    let attribute = strict_attribute(element(document, element_index)?, name)?;
    edits
        .try_reserve(1)
        .map_err(|_| TextBoxPropertiesHwpxError::AllocationFailed)?;
    edits.push(ByteEdit {
        span: attribute.value_span(),
        replacement: replacement.into_bytes(),
    });
    Ok(())
}

fn apply_edits(
    source: &[u8],
    edits: &mut [ByteEdit],
    limits: TextBoxPropertiesHwpxLimits,
) -> Result<Vec<u8>, TextBoxPropertiesHwpxError> {
    edits.sort_unstable_by_key(|edit| edit.span.start());
    let mut previous_end = 0;
    let mut output_len = source.len();
    for edit in edits.iter() {
        if edit.span.start() < previous_end || edit.span.end() > source.len() {
            return Err(TextBoxPropertiesHwpxError::UnsupportedTextBox);
        }
        previous_end = edit.span.end();
        output_len = output_len
            .checked_sub(edit.span.len())
            .and_then(|value| value.checked_add(edit.replacement.len()))
            .ok_or(TextBoxPropertiesHwpxError::OutputLimit)?;
    }
    if output_len > limits.0.output_bytes {
        return Err(TextBoxPropertiesHwpxError::OutputLimit);
    }
    let mut output = Vec::new();
    output
        .try_reserve_exact(output_len)
        .map_err(|_| TextBoxPropertiesHwpxError::AllocationFailed)?;
    let mut cursor = 0;
    for edit in edits.iter() {
        output.extend_from_slice(&source[cursor..edit.span.start()]);
        output.extend_from_slice(&edit.replacement);
        cursor = edit.span.end();
    }
    output.extend_from_slice(&source[cursor..]);
    if output.len() != output_len {
        return Err(TextBoxPropertiesHwpxError::OutputLimit);
    }
    Ok(output)
}

fn verify_preservation(
    source: &[u8],
    output: &[u8],
    edits: &[ByteEdit],
) -> Result<(), TextBoxPropertiesHwpxError> {
    let mut source_cursor = 0;
    let mut output_cursor = 0_usize;
    for edit in edits {
        let unchanged_len = edit
            .span
            .start()
            .checked_sub(source_cursor)
            .ok_or(TextBoxPropertiesHwpxError::PreservationMismatch)?;
        let output_unchanged_end = output_cursor
            .checked_add(unchanged_len)
            .ok_or(TextBoxPropertiesHwpxError::PreservationMismatch)?;
        let output_replacement_end = output_unchanged_end
            .checked_add(edit.replacement.len())
            .ok_or(TextBoxPropertiesHwpxError::PreservationMismatch)?;
        if output_replacement_end > output.len()
            || source[source_cursor..edit.span.start()]
                != output[output_cursor..output_unchanged_end]
            || edit.replacement != output[output_unchanged_end..output_replacement_end]
        {
            return Err(TextBoxPropertiesHwpxError::PreservationMismatch);
        }
        source_cursor = edit.span.end();
        output_cursor = output_replacement_end;
    }
    if source[source_cursor..] != output[output_cursor..] {
        return Err(TextBoxPropertiesHwpxError::PreservationMismatch);
    }
    Ok(())
}

fn selected_run_object(
    document: &PreservingXmlDocument,
    ordinal: usize,
    limits: TextBoxPropertiesHwpxLimits,
) -> Result<usize, TextBoxPropertiesHwpxError> {
    let mut seen = 0_usize;
    for (index, candidate) in document.elements().iter().enumerate() {
        if !is_run_object(candidate) {
            continue;
        }
        let parent = candidate
            .parent()
            .and_then(|value| document.elements().get(value))
            .ok_or(TextBoxPropertiesHwpxError::UnsupportedTextBox)?;
        if !has_name(parent, "run") {
            continue;
        }
        if seen == ordinal {
            return Ok(index);
        }
        seen = seen
            .checked_add(1)
            .ok_or(TextBoxPropertiesHwpxError::InputLimit)?;
        if seen > limits.0.objects {
            return Err(TextBoxPropertiesHwpxError::InputLimit);
        }
    }
    Err(TextBoxPropertiesHwpxError::UnsupportedTextBox)
}

fn is_run_object(element: &XmlElementToken) -> bool {
    element.name().namespace() == Some(PARAGRAPH_NS)
        && matches!(
            element.name().local_name(),
            "pic"
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

fn direct_children(
    document: &PreservingXmlDocument,
    parent: usize,
) -> Result<Vec<usize>, TextBoxPropertiesHwpxError> {
    let mut children = Vec::new();
    let mut child = element(document, parent)?.first_child();
    while let Some(index) = child {
        children
            .try_reserve(1)
            .map_err(|_| TextBoxPropertiesHwpxError::AllocationFailed)?;
        children.push(index);
        child = element(document, index)?.next_sibling();
    }
    Ok(children)
}

fn direct_children_named(
    document: &PreservingXmlDocument,
    parent: usize,
    local_name: &str,
) -> Result<Vec<usize>, TextBoxPropertiesHwpxError> {
    Ok(direct_children(document, parent)?
        .into_iter()
        .filter(|index| element(document, *index).is_ok_and(|value| has_name(value, local_name)))
        .collect())
}

fn descendants_named(
    document: &PreservingXmlDocument,
    parent: usize,
    local_name: &str,
) -> Result<Vec<usize>, TextBoxPropertiesHwpxError> {
    let mut matches = Vec::new();
    for (index, candidate) in document.elements().iter().enumerate() {
        if has_name(candidate, local_name) && is_descendant(document, index, parent)? {
            matches
                .try_reserve(1)
                .map_err(|_| TextBoxPropertiesHwpxError::AllocationFailed)?;
            matches.push(index);
        }
    }
    Ok(matches)
}

fn is_descendant(
    document: &PreservingXmlDocument,
    candidate: usize,
    ancestor: usize,
) -> Result<bool, TextBoxPropertiesHwpxError> {
    let mut parent = element(document, candidate)?.parent();
    while let Some(index) = parent {
        if index == ancestor {
            return Ok(true);
        }
        parent = element(document, index)?.parent();
    }
    Ok(false)
}

fn strict_attribute<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<&'a XmlAttributeToken, TextBoxPropertiesHwpxError> {
    let mut matches = element.attributes().iter().filter(|attribute| {
        !attribute.is_namespace_declaration() && attribute.name().local_name() == name
    });
    let value = matches
        .next()
        .ok_or(TextBoxPropertiesHwpxError::InvalidAttribute)?;
    if value.name().namespace().is_some() || matches.next().is_some() {
        return Err(TextBoxPropertiesHwpxError::InvalidAttribute);
    }
    Ok(value)
}

fn lexical_value<'a>(
    source: &'a [u8],
    attribute: &XmlAttributeToken,
) -> Result<&'a str, TextBoxPropertiesHwpxError> {
    std::str::from_utf8(
        source
            .get(attribute.value_span().start()..attribute.value_span().end())
            .ok_or(TextBoxPropertiesHwpxError::InvalidAttribute)?,
    )
    .map_err(|_| TextBoxPropertiesHwpxError::InvalidAttribute)
}

fn canonical_u32(
    source: &[u8],
    attribute: &XmlAttributeToken,
    maximum: u32,
) -> Result<u32, TextBoxPropertiesHwpxError> {
    let value = lexical_value(source, attribute)?;
    if value.is_empty()
        || !value.bytes().all(|byte| byte.is_ascii_digit())
        || (value != "0" && value.starts_with('0'))
    {
        return Err(TextBoxPropertiesHwpxError::InvalidNumber);
    }
    let parsed = value
        .parse::<u32>()
        .map_err(|_| TextBoxPropertiesHwpxError::InvalidNumber)?;
    if parsed > maximum {
        return Err(TextBoxPropertiesHwpxError::InvalidNumber);
    }
    Ok(parsed)
}

fn outer_span(element: &XmlElementToken) -> Result<XmlByteSpan, TextBoxPropertiesHwpxError> {
    element
        .outer_span()
        .ok_or(TextBoxPropertiesHwpxError::UnsupportedTextBox)
}

fn digest_span(source: &[u8], span: XmlByteSpan) -> Result<[u8; 32], TextBoxPropertiesHwpxError> {
    Ok(Sha256::digest(
        source
            .get(span.start()..span.end())
            .ok_or(TextBoxPropertiesHwpxError::UnsupportedTextBox)?,
    )
    .into())
}

fn has_name(element: &XmlElementToken, local_name: &str) -> bool {
    element.name().namespace() == Some(PARAGRAPH_NS) && element.name().local_name() == local_name
}

const fn direction_text(value: TextBoxDirection) -> &'static str {
    match value {
        TextBoxDirection::Horizontal => "HORIZONTAL",
        TextBoxDirection::Vertical => "VERTICAL",
        TextBoxDirection::VerticalRightToLeft => "VERTICALALL",
    }
}

const fn vertical_alignment_text(value: ObjectTextBoxVerticalAlignment) -> &'static str {
    match value {
        ObjectTextBoxVerticalAlignment::Top => "TOP",
        ObjectTextBoxVerticalAlignment::Center => "CENTER",
        ObjectTextBoxVerticalAlignment::Bottom => "BOTTOM",
    }
}

fn validate_plan(
    plan: &TextBoxPropertiesHwpxPlan,
    limits: TextBoxPropertiesHwpxLimits,
) -> Result<(), TextBoxPropertiesHwpxError> {
    if plan.schema_version != OBJECT_PROPERTIES_SCHEMA_VERSION
        || plan.profile_id != TEXTBOX_PROPERTIES_HWPX_PROFILE_ID
        || plan.domain_plan.capability_id() != "obj.textbox_properties"
        || plan.source_document_flow_sha256 != plan.domain_plan.source_document_flow_sha256()
        || plan.domain_plan.plan_sha256() != plan.domain_plan_sha256
        || plan_binding_sha256(plan, limits)? != plan.plan_sha256
    {
        return Err(TextBoxPropertiesHwpxError::PlanTampered);
    }
    Ok(())
}

fn plan_binding_sha256(
    plan: &TextBoxPropertiesHwpxPlan,
    limits: TextBoxPropertiesHwpxLimits,
) -> Result<String, TextBoxPropertiesHwpxError> {
    let mut unsigned = plan.clone();
    unsigned.plan_sha256.clear();
    Ok(hex(
        Sha256::digest(serialize_bounded(&unsigned, limits)?).into()
    ))
}

fn serialize_bounded<T: Serialize>(
    value: &T,
    limits: TextBoxPropertiesHwpxLimits,
) -> Result<Vec<u8>, TextBoxPropertiesHwpxError> {
    let bytes = serde_json::to_vec(value).map_err(|_| TextBoxPropertiesHwpxError::PlanTampered)?;
    if bytes.len() > limits.0.plan_bytes {
        return Err(TextBoxPropertiesHwpxError::OutputLimit);
    }
    Ok(bytes)
}

fn element(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<&XmlElementToken, TextBoxPropertiesHwpxError> {
    document
        .elements()
        .get(index)
        .ok_or(TextBoxPropertiesHwpxError::UnsupportedTextBox)
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
