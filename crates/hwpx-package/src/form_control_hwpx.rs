use std::fmt;

use domain_ir::{
    FORM_CONTROL_SCHEMA_VERSION, FormButtonBackStyle, FormButtonValue, FormControlBuilder,
    FormControlError, FormControlLimits, FormControlPayload, FormControlPlan, FormControlState,
    FormDocumentState, FormListItem, FormNativeBinding, FormScrollBars, FormTabKeyBehavior,
    FormTextAlignment, NativeFormTag,
};
use quick_xml::escape::unescape;
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::preserving_xml::{
    PreservingXmlDocument, PreservingXmlError, XmlAttributeToken, XmlElementToken,
};

pub const FORM_CONTROL_HWPX_PROFILE_ID: &str =
    "hwpx-agent.form-control-hwpx.hwpml-2011-existing-native-form-properties/v1";

const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct FormControlHwpxLimitConfig {
    pub section_bytes: usize,
    pub elements: usize,
    pub controls: usize,
    pub attributes_per_control: usize,
    pub text_bytes: usize,
    pub plan_bytes: usize,
    pub output_bytes: usize,
}

impl Default for FormControlHwpxLimitConfig {
    fn default() -> Self {
        Self {
            section_bytes: 32 * 1024 * 1024,
            elements: 1_000_000,
            controls: 65_536,
            attributes_per_control: 256,
            text_bytes: 64 * 1024,
            plan_bytes: 8 * 1024 * 1024,
            output_bytes: 32 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct FormControlHwpxLimits(FormControlHwpxLimitConfig);

impl FormControlHwpxLimits {
    pub const HARD_MAX_SECTION_BYTES: usize = 128 * 1024 * 1024;
    pub const HARD_MAX_ELEMENTS: usize = 2_000_000;
    pub const HARD_MAX_CONTROLS: usize = 262_144;
    pub const HARD_MAX_ATTRIBUTES: usize = 4096;
    pub const HARD_MAX_TEXT_BYTES: usize = 1024 * 1024;
    pub const HARD_MAX_PLAN_BYTES: usize = 32 * 1024 * 1024;
    pub const HARD_MAX_OUTPUT_BYTES: usize = 128 * 1024 * 1024;

    /// Creates finite exact-section limits without silently clamping values.
    ///
    /// # Errors
    ///
    /// Rejects zero, inconsistent, or hard-ceiling-exceeding limits.
    pub fn new(config: FormControlHwpxLimitConfig) -> Result<Self, FormControlHwpxError> {
        if config.section_bytes == 0
            || config.section_bytes > Self::HARD_MAX_SECTION_BYTES
            || config.elements == 0
            || config.elements > Self::HARD_MAX_ELEMENTS
            || config.controls == 0
            || config.controls > Self::HARD_MAX_CONTROLS
            || config.attributes_per_control == 0
            || config.attributes_per_control > Self::HARD_MAX_ATTRIBUTES
            || config.text_bytes == 0
            || config.text_bytes > Self::HARD_MAX_TEXT_BYTES
            || config.plan_bytes == 0
            || config.plan_bytes > Self::HARD_MAX_PLAN_BYTES
            || config.output_bytes == 0
            || config.output_bytes > Self::HARD_MAX_OUTPUT_BYTES
            || config.section_bytes > config.output_bytes
        {
            return Err(FormControlHwpxError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> FormControlHwpxLimitConfig {
        self.0
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct FormControlHwpxReadback {
    pub state: FormDocumentState,
    pub section_sha256: [u8; 32],
    pub object_sha256: Vec<[u8; 32]>,
    pub control_count: usize,
}

impl fmt::Debug for FormControlHwpxReadback {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FormControlHwpxReadback")
            .field("control_count", &self.control_count)
            .field("state", &"<redacted>")
            .field("digests", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Serialize)]
pub struct FormControlHwpxPlan {
    schema_version: &'static str,
    profile_id: &'static str,
    source_section_sha256: [u8; 32],
    source_object_sha256: Vec<[u8; 32]>,
    source_document_flow_sha256: String,
    domain_plan: FormControlPlan,
    domain_plan_sha256: String,
    plan_sha256: String,
}

impl FormControlHwpxPlan {
    #[must_use]
    pub const fn domain_plan(&self) -> &FormControlPlan {
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
        limits: FormControlHwpxLimits,
    ) -> Result<Vec<u8>, FormControlHwpxError> {
        serialize_bounded(self, limits)
    }
}

impl fmt::Debug for FormControlHwpxPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FormControlHwpxPlan")
            .field("profile_id", &self.profile_id)
            .field("capability_id", &self.domain_plan.capability_id())
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct FormControlHwpxLoweringReceipt {
    pub profile_id: &'static str,
    pub capability_id: &'static str,
    pub source_section_sha256: [u8; 32],
    pub output_section_sha256: [u8; 32],
    pub source_state_sha256: String,
    pub target_state_sha256: String,
    pub plan_sha256: String,
    pub target_document_flow_sha256: String,
    pub modified_attribute_count: usize,
    pub source_bytes: usize,
    pub output_bytes: usize,
}

impl fmt::Debug for FormControlHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FormControlHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field("capability_id", &self.capability_id)
            .field("modified_attribute_count", &self.modified_attribute_count)
            .field("source_bytes", &self.source_bytes)
            .field("output_bytes", &self.output_bytes)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum FormControlHwpxError {
    #[error("form-control HWPX limits are invalid")]
    InvalidLimit,
    #[error("form-control HWPX section exceeds a finite limit")]
    InputLimit,
    #[error("form-control HWPX selection is absent, ambiguous, or unsupported")]
    UnsupportedControl,
    #[error("form-control HWPX attribute is missing, duplicated, or malformed")]
    InvalidAttribute,
    #[error("form-control HWPX native projection differs from the bound state")]
    ProjectionMismatch,
    #[error("form-control HWPX operation is not representable by this closed profile")]
    NonRepresentable,
    #[error("form-control HWPX section, state, object, or flow drifted")]
    SourceDrift,
    #[error("form-control HWPX plan was tampered with")]
    PlanTampered,
    #[error("form-control HWPX semantic readback differs")]
    ReadbackMismatch,
    #[error("form-control HWPX preservation proof failed")]
    PreservationMismatch,
    #[error("form-control HWPX output exceeds a finite limit")]
    OutputLimit,
    #[error("form-control HWPX allocation failed")]
    AllocationFailed,
    #[error("form-control domain validation failed")]
    Domain(#[from] FormControlError),
    #[error("form-control preserving XML admission failed")]
    Preserving(#[from] PreservingXmlError),
}

impl FormControlHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "form_control_hwpx_invalid_limit",
            Self::InputLimit => "form_control_hwpx_input_limit",
            Self::UnsupportedControl => "form_control_hwpx_unsupported_control",
            Self::InvalidAttribute => "form_control_hwpx_invalid_attribute",
            Self::ProjectionMismatch => "form_control_hwpx_projection_mismatch",
            Self::NonRepresentable => "form_control_hwpx_non_representable",
            Self::SourceDrift => "form_control_hwpx_source_drift",
            Self::PlanTampered => "form_control_hwpx_plan_tampered",
            Self::ReadbackMismatch => "form_control_hwpx_readback_mismatch",
            Self::PreservationMismatch => "form_control_hwpx_preservation_mismatch",
            Self::OutputLimit => "form_control_hwpx_output_limit",
            Self::AllocationFailed => "form_control_hwpx_allocation_failed",
            Self::Domain(_) => "form_control_hwpx_domain",
            Self::Preserving(_) => "form_control_hwpx_preserving_xml",
        }
    }
}

#[derive(Debug)]
pub struct FormControlHwpxReader;

impl FormControlHwpxReader {
    /// Verifies every existing native form projection against one complete expected state.
    ///
    /// # Errors
    ///
    /// Rejects malformed, unsupported, ambiguous, stale, or over-limit XML.
    pub fn read_section(
        source: &[u8],
        expected: &FormDocumentState,
        state_limits: FormControlLimits,
        hwpx_limits: FormControlHwpxLimits,
    ) -> Result<FormControlHwpxReadback, FormControlHwpxError> {
        let parsed = parse_forms(source, expected, state_limits, hwpx_limits)?;
        Ok(FormControlHwpxReadback {
            state: expected.clone(),
            section_sha256: Sha256::digest(source).into(),
            object_sha256: parsed.object_sha256,
            control_count: parsed.roots.len(),
        })
    }
}

#[derive(Debug)]
pub struct FormControlHwpxBuilder;

impl FormControlHwpxBuilder {
    /// Binds one exact REF-018 or REF-019 domain plan to a complete section snapshot.
    ///
    /// # Errors
    ///
    /// Rejects unsupported capability, source, flow, projection, plan, or limit drift.
    pub fn plan(
        source: &[u8],
        domain_plan: &FormControlPlan,
        current_document_flow_sha256: &str,
        state_limits: FormControlLimits,
        hwpx_limits: FormControlHwpxLimits,
    ) -> Result<FormControlHwpxPlan, FormControlHwpxError> {
        if !matches!(
            domain_plan.capability_id(),
            "ref.form_properties" | "ref.form_tab_order"
        ) || domain_plan.source_document_flow_sha256() != current_document_flow_sha256
        {
            return Err(FormControlHwpxError::NonRepresentable);
        }
        validate_representable_transition(
            domain_plan.source_state(),
            domain_plan.target_state(),
            domain_plan.capability_id(),
        )?;
        let readback = FormControlHwpxReader::read_section(
            source,
            domain_plan.source_state(),
            state_limits,
            hwpx_limits,
        )?;
        let built = FormControlBuilder::build(
            domain_plan,
            domain_plan.source_state(),
            current_document_flow_sha256,
            state_limits,
        )?;
        if &built.state != domain_plan.target_state() {
            return Err(FormControlHwpxError::PlanTampered);
        }
        let mut plan = FormControlHwpxPlan {
            schema_version: FORM_CONTROL_SCHEMA_VERSION,
            profile_id: FORM_CONTROL_HWPX_PROFILE_ID,
            source_section_sha256: readback.section_sha256,
            source_object_sha256: readback.object_sha256,
            source_document_flow_sha256: current_document_flow_sha256.to_owned(),
            domain_plan: domain_plan.clone(),
            domain_plan_sha256: domain_plan.plan_sha256().to_owned(),
            plan_sha256: String::new(),
        };
        plan.plan_sha256 = plan_binding_sha256(&plan, hwpx_limits)?;
        let _ = plan.canonical_json(hwpx_limits)?;
        Ok(plan)
    }
}

#[derive(Debug)]
pub struct FormControlHwpxLowerer;

impl FormControlHwpxLowerer {
    /// Patches only admitted native property and tab-order attributes.
    ///
    /// # Errors
    ///
    /// Returns no bytes on plan, state, source, flow, preservation, or readback drift.
    pub fn lower_section_with_receipt(
        source: &[u8],
        plan: &FormControlHwpxPlan,
        current_document_flow_sha256: &str,
        state_limits: FormControlLimits,
        hwpx_limits: FormControlHwpxLimits,
    ) -> Result<(Vec<u8>, FormControlHwpxLoweringReceipt), FormControlHwpxError> {
        validate_plan(plan, hwpx_limits)?;
        if Sha256::digest(source).as_slice() != plan.source_section_sha256
            || current_document_flow_sha256 != plan.source_document_flow_sha256
            || current_document_flow_sha256 != plan.domain_plan.source_document_flow_sha256()
            || plan.domain_plan.plan_sha256() != plan.domain_plan_sha256
        {
            return Err(FormControlHwpxError::SourceDrift);
        }
        let source_readback = FormControlHwpxReader::read_section(
            source,
            plan.domain_plan.source_state(),
            state_limits,
            hwpx_limits,
        )?;
        if source_readback.object_sha256 != plan.source_object_sha256 {
            return Err(FormControlHwpxError::SourceDrift);
        }
        let result = FormControlBuilder::build(
            &plan.domain_plan,
            plan.domain_plan.source_state(),
            current_document_flow_sha256,
            state_limits,
        )?;
        validate_representable_transition(
            plan.domain_plan.source_state(),
            &result.state,
            plan.domain_plan.capability_id(),
        )?;
        let parsed = parse_forms(
            source,
            plan.domain_plan.source_state(),
            state_limits,
            hwpx_limits,
        )?;
        let edits = build_edits(
            source,
            &parsed.document,
            &parsed.roots,
            plan.domain_plan.source_state(),
            &result.state,
            plan.domain_plan.capability_id(),
            hwpx_limits,
        )?;
        if edits.is_empty() {
            return Err(FormControlHwpxError::NonRepresentable);
        }
        let output = apply_edits(source, &edits, hwpx_limits)?;
        verify_preservation(source, &output, &edits)?;
        let target_readback =
            FormControlHwpxReader::read_section(&output, &result.state, state_limits, hwpx_limits)?;
        let receipt = FormControlHwpxLoweringReceipt {
            profile_id: FORM_CONTROL_HWPX_PROFILE_ID,
            capability_id: plan.domain_plan.capability_id(),
            source_section_sha256: source_readback.section_sha256,
            output_section_sha256: target_readback.section_sha256,
            source_state_sha256: plan
                .domain_plan
                .source_state()
                .canonical_sha256(state_limits)?,
            target_state_sha256: result.state.canonical_sha256(state_limits)?,
            plan_sha256: plan.plan_sha256.clone(),
            target_document_flow_sha256: plan.domain_plan.target_document_flow_sha256().to_owned(),
            modified_attribute_count: edits.len(),
            source_bytes: source.len(),
            output_bytes: output.len(),
        };
        Ok((output, receipt))
    }

    /// Returns preserving section bytes after the same fail-closed checks.
    ///
    /// # Errors
    ///
    /// Applies the same validation as [`Self::lower_section_with_receipt`].
    pub fn lower_section(
        source: &[u8],
        plan: &FormControlHwpxPlan,
        current_document_flow_sha256: &str,
        state_limits: FormControlLimits,
        hwpx_limits: FormControlHwpxLimits,
    ) -> Result<Vec<u8>, FormControlHwpxError> {
        Ok(Self::lower_section_with_receipt(
            source,
            plan,
            current_document_flow_sha256,
            state_limits,
            hwpx_limits,
        )?
        .0)
    }
}

struct ParsedForms {
    document: PreservingXmlDocument,
    roots: Vec<usize>,
    object_sha256: Vec<[u8; 32]>,
}

fn parse_forms(
    source: &[u8],
    expected: &FormDocumentState,
    state_limits: FormControlLimits,
    limits: FormControlHwpxLimits,
) -> Result<ParsedForms, FormControlHwpxError> {
    if source.is_empty()
        || source.len() > limits.0.section_bytes
        || expected.controls().is_empty()
        || expected.controls().len() > limits.0.controls
    {
        return Err(FormControlHwpxError::InputLimit);
    }
    let _ = expected.canonical_sha256(state_limits)?;
    let document = PreservingXmlDocument::parse(source)?;
    if document.elements().len() > limits.0.elements {
        return Err(FormControlHwpxError::InputLimit);
    }
    let roots = form_roots(&document, limits)?;
    if roots.len() != expected.controls().len() {
        return Err(FormControlHwpxError::ProjectionMismatch);
    }
    let mut object_sha256 = Vec::new();
    object_sha256
        .try_reserve_exact(roots.len())
        .map_err(|_| FormControlHwpxError::AllocationFailed)?;
    for (&root, control) in roots.iter().zip(expected.controls()) {
        verify_projection(source, &document, root, control, limits)?;
        object_sha256.push(digest_span(source, outer_span(element(&document, root)?)?)?);
    }
    document.verify_untouched_round_trip()?;
    Ok(ParsedForms {
        document,
        roots,
        object_sha256,
    })
}

fn form_roots(
    document: &PreservingXmlDocument,
    limits: FormControlHwpxLimits,
) -> Result<Vec<usize>, FormControlHwpxError> {
    let mut roots = Vec::new();
    for (index, candidate) in document.elements().iter().enumerate() {
        if !is_form(candidate) {
            continue;
        }
        let parent = candidate
            .parent()
            .and_then(|value| document.elements().get(value))
            .ok_or(FormControlHwpxError::UnsupportedControl)?;
        if !has_name(parent, "run") {
            return Err(FormControlHwpxError::UnsupportedControl);
        }
        if candidate.attributes().len() > limits.0.attributes_per_control
            || roots.len() >= limits.0.controls
        {
            return Err(FormControlHwpxError::InputLimit);
        }
        roots
            .try_reserve(1)
            .map_err(|_| FormControlHwpxError::AllocationFailed)?;
        roots.push(index);
    }
    Ok(roots)
}

fn verify_projection(
    source: &[u8],
    document: &PreservingXmlDocument,
    root: usize,
    expected: &FormControlState,
    limits: FormControlHwpxLimits,
) -> Result<(), FormControlHwpxError> {
    let root_element = element(document, root)?;
    let expected_tag = match expected.native_binding {
        FormNativeBinding::Exact { tag } => tag,
        FormNativeBinding::UnverifiedDateControl => {
            return Err(FormControlHwpxError::UnsupportedControl);
        }
    };
    if root_element.name().local_name() != tag_name(expected_tag)
        || canonical_u32(source, strict_attribute(root_element, "id")?)?
            != expected.identity.native_object_id
    {
        return Err(FormControlHwpxError::ProjectionMismatch);
    }
    let common = &expected.common;
    expect_string(source, root_element, "name", &common.name, limits)?;
    expect_color(source, root_element, "foreColor", common.fore_color_rgb)?;
    expect_color(source, root_element, "backColor", common.back_color_rgb)?;
    expect_optional_string(
        source,
        root_element,
        "groupName",
        common.group_name.as_deref(),
        limits,
    )?;
    expect_bool(source, root_element, "tabStop", common.tab_stop)?;
    expect_bool(source, root_element, "editable", common.editable)?;
    expect_tab_order(source, root_element, common.tab_order)?;
    expect_bool(source, root_element, "enabled", common.enabled)?;
    expect_u32(
        source,
        root_element,
        "borderTypeIDRef",
        common.border_type_id_ref,
    )?;
    expect_bool(source, root_element, "drawFrame", common.draw_frame)?;
    expect_bool(source, root_element, "printable", common.printable)?;
    expect_command_digest(
        source,
        root_element,
        common.command_sha256.as_deref(),
        limits,
    )?;

    let character_index = only_direct_child(document, root, "formCharPr")?;
    let character = element(document, character_index)?;
    expect_u32(
        source,
        character,
        "charPrIDRef",
        common.character.char_pr_id_ref,
    )?;
    expect_bool(
        source,
        character,
        "followContext",
        common.character.follow_context,
    )?;
    expect_bool(source, character, "autoSz", common.character.auto_size)?;
    expect_bool(source, character, "wordWrap", common.character.word_wrap)?;
    verify_payload(
        source,
        document,
        root,
        root_element,
        &expected.payload,
        limits,
    )
}

fn verify_payload(
    source: &[u8],
    document: &PreservingXmlDocument,
    root: usize,
    root_element: &XmlElementToken,
    payload: &FormControlPayload,
    limits: FormControlHwpxLimits,
) -> Result<(), FormControlHwpxError> {
    match payload {
        FormControlPayload::Text { .. } => {
            verify_text(source, document, root, root_element, payload, limits)
        }
        FormControlPayload::Checkbox { .. } | FormControlPayload::Radio { .. } => {
            verify_button(source, root_element, payload, limits)
        }
        FormControlPayload::Combo { .. } => {
            verify_combo(source, document, root, root_element, payload, limits)
        }
        FormControlPayload::List { .. } => {
            verify_list(source, document, root, root_element, payload, limits)
        }
        FormControlPayload::Date { .. } => Err(FormControlHwpxError::UnsupportedControl),
    }
}

fn verify_text(
    source: &[u8],
    document: &PreservingXmlDocument,
    root: usize,
    element: &XmlElementToken,
    payload: &FormControlPayload,
    limits: FormControlHwpxLimits,
) -> Result<(), FormControlHwpxError> {
    let FormControlPayload::Text {
        value,
        multi_line,
        password_character,
        native_max_length,
        scroll_bars,
        tab_key_behavior,
        number_only,
        read_only,
        alignment,
        ..
    } = payload
    else {
        return Err(FormControlHwpxError::UnsupportedControl);
    };
    expect_bool(source, element, "multiLine", *multi_line)?;
    expect_optional_string(
        source,
        element,
        "passwordChar",
        password_character.as_deref(),
        limits,
    )?;
    expect_u32(source, element, "maxLength", native_max_length.unwrap_or(0))?;
    expect_enum(
        source,
        element,
        "scrollBars",
        scroll_bars_name(*scroll_bars),
    )?;
    expect_enum(
        source,
        element,
        "tabKeyBehavior",
        tab_behavior_name(*tab_key_behavior),
    )?;
    expect_bool(source, element, "numOnly", *number_only)?;
    expect_bool(source, element, "readOnly", *read_only)?;
    expect_enum(source, element, "alignText", alignment_name(*alignment))?;
    let text = only_direct_child(document, root, "text")?;
    expect_element_text(source, document, text, value, limits)
}

fn verify_button(
    source: &[u8],
    element: &XmlElementToken,
    payload: &FormControlPayload,
    limits: FormControlHwpxLimits,
) -> Result<(), FormControlHwpxError> {
    let (caption, value, radio_group_name, tri_state, back_style) = match payload {
        FormControlPayload::Checkbox {
            caption,
            value,
            radio_group_name,
            tri_state,
            back_style,
            ..
        } => (
            caption,
            *value,
            radio_group_name.as_deref(),
            *tri_state,
            *back_style,
        ),
        FormControlPayload::Radio {
            caption,
            value,
            radio_group_name,
            tri_state,
            back_style,
            ..
        } => (
            caption,
            *value,
            Some(radio_group_name.as_str()),
            *tri_state,
            *back_style,
        ),
        _ => return Err(FormControlHwpxError::UnsupportedControl),
    };
    expect_string(source, element, "caption", caption, limits)?;
    expect_enum(source, element, "value", button_value_name(value))?;
    expect_optional_string(source, element, "radioGroupName", radio_group_name, limits)?;
    expect_bool(source, element, "triState", tri_state)?;
    expect_enum(source, element, "backStyle", back_style_name(back_style))
}

fn verify_combo(
    source: &[u8],
    document: &PreservingXmlDocument,
    root: usize,
    element: &XmlElementToken,
    payload: &FormControlPayload,
    limits: FormControlHwpxLimits,
) -> Result<(), FormControlHwpxError> {
    let FormControlPayload::Combo {
        items,
        selected_value,
        list_box_rows,
        list_box_width_hwp_units,
        edit_enable,
        ..
    } = payload
    else {
        return Err(FormControlHwpxError::UnsupportedControl);
    };
    expect_i32_option(source, element, "listBoxRows", *list_box_rows)?;
    expect_i32_option(source, element, "listBoxWidth", *list_box_width_hwp_units)?;
    expect_bool(source, element, "editEnable", *edit_enable)?;
    expect_optional_string(
        source,
        element,
        "selectedValue",
        selected_value.as_deref(),
        limits,
    )?;
    verify_list_items(source, document, root, items, limits)
}

fn verify_list(
    source: &[u8],
    document: &PreservingXmlDocument,
    root: usize,
    element: &XmlElementToken,
    payload: &FormControlPayload,
    limits: FormControlHwpxLimits,
) -> Result<(), FormControlHwpxError> {
    let FormControlPayload::List {
        items,
        selected_value,
        item_height_hwp_units,
        top_index,
        ..
    } = payload
    else {
        return Err(FormControlHwpxError::UnsupportedControl);
    };
    expect_i32_option(source, element, "itemHeight", *item_height_hwp_units)?;
    expect_u32(source, element, "topIdx", *top_index)?;
    expect_optional_string(
        source,
        element,
        "selectedValue",
        selected_value.as_deref(),
        limits,
    )?;
    verify_list_items(source, document, root, items, limits)
}

fn verify_list_items(
    source: &[u8],
    document: &PreservingXmlDocument,
    root: usize,
    expected: &[FormListItem],
    limits: FormControlHwpxLimits,
) -> Result<(), FormControlHwpxError> {
    let children = direct_children_named(document, root, "listItem")?;
    if children.len() != expected.len() {
        return Err(FormControlHwpxError::ProjectionMismatch);
    }
    for (&child, item) in children.iter().zip(expected) {
        let element = element(document, child)?;
        expect_string(source, element, "displayText", &item.display_text, limits)?;
        expect_string(source, element, "value", &item.value, limits)?;
    }
    Ok(())
}

fn validate_representable_transition(
    source: &FormDocumentState,
    target: &FormDocumentState,
    capability_id: &str,
) -> Result<(), FormControlHwpxError> {
    if source.controls().len() != target.controls().len()
        || source.controls().is_empty()
        || source.controls().iter().any(|control| {
            matches!(
                control.native_binding,
                FormNativeBinding::UnverifiedDateControl
            )
        })
    {
        return Err(FormControlHwpxError::NonRepresentable);
    }
    let mut changed = 0_usize;
    for (before, after) in source.controls().iter().zip(target.controls()) {
        if before == after {
            continue;
        }
        changed = changed
            .checked_add(1)
            .ok_or(FormControlHwpxError::InputLimit)?;
        let mut admitted = before.clone();
        match capability_id {
            "ref.form_properties" => {
                if before.common.command_sha256 != after.common.command_sha256 {
                    return Err(FormControlHwpxError::NonRepresentable);
                }
                admitted.common = after.common.clone();
            }
            "ref.form_tab_order" => {
                admitted.common.tab_stop = after.common.tab_stop;
                admitted.common.tab_order = after.common.tab_order;
            }
            _ => return Err(FormControlHwpxError::NonRepresentable),
        }
        if admitted != *after {
            return Err(FormControlHwpxError::NonRepresentable);
        }
    }
    if changed == 0 || (capability_id == "ref.form_properties" && changed != 1) {
        return Err(FormControlHwpxError::NonRepresentable);
    }
    Ok(())
}

#[derive(Debug)]
struct ByteEdit {
    start: usize,
    end: usize,
    replacement: Vec<u8>,
}

fn build_edits(
    source: &[u8],
    document: &PreservingXmlDocument,
    roots: &[usize],
    before: &FormDocumentState,
    after: &FormDocumentState,
    capability_id: &str,
    limits: FormControlHwpxLimits,
) -> Result<Vec<ByteEdit>, FormControlHwpxError> {
    let mut edits = Vec::new();
    for ((&root, source_control), target_control) in
        roots.iter().zip(before.controls()).zip(after.controls())
    {
        if source_control == target_control {
            continue;
        }
        let root_element = element(document, root)?;
        if capability_id == "ref.form_tab_order" {
            push_tab_edits(source, root_element, target_control, &mut edits)?;
            continue;
        }
        push_common_property_edits(
            source,
            document,
            root,
            root_element,
            target_control,
            limits,
            &mut edits,
        )?;
    }
    edits.retain(|edit| source.get(edit.start..edit.end) != Some(edit.replacement.as_slice()));
    if edits.len()
        > limits
            .0
            .controls
            .saturating_mul(limits.0.attributes_per_control)
    {
        return Err(FormControlHwpxError::InputLimit);
    }
    Ok(edits)
}

fn push_tab_edits(
    source: &[u8],
    element: &XmlElementToken,
    target: &FormControlState,
    edits: &mut Vec<ByteEdit>,
) -> Result<(), FormControlHwpxError> {
    push_existing_attribute_edit(
        source,
        element,
        "tabStop",
        bool_name(target.common.tab_stop),
        edits,
    )?;
    push_existing_attribute_edit(
        source,
        element,
        "tabOrder",
        &tab_order_name(target.common.tab_order),
        edits,
    )
}

fn push_common_property_edits(
    source: &[u8],
    document: &PreservingXmlDocument,
    root: usize,
    root_element: &XmlElementToken,
    target: &FormControlState,
    limits: FormControlHwpxLimits,
    edits: &mut Vec<ByteEdit>,
) -> Result<(), FormControlHwpxError> {
    push_existing_attribute_edit(
        source,
        root_element,
        "name",
        &escape_attribute(&target.common.name, limits)?,
        edits,
    )?;
    push_existing_attribute_edit(
        source,
        root_element,
        "foreColor",
        &color_name(target.common.fore_color_rgb)?,
        edits,
    )?;
    push_existing_attribute_edit(
        source,
        root_element,
        "backColor",
        &color_name(target.common.back_color_rgb)?,
        edits,
    )?;
    push_optional_attribute_edit(
        source,
        root_element,
        "groupName",
        target.common.group_name.as_deref(),
        limits,
        edits,
    )?;
    for (name, value) in common_attribute_values(target) {
        push_existing_attribute_edit(source, root_element, name, &value, edits)?;
    }
    let character = element(document, only_direct_child(document, root, "formCharPr")?)?;
    for (name, value) in character_attribute_values(target) {
        push_existing_attribute_edit(source, character, name, &value, edits)?;
    }
    Ok(())
}

fn common_attribute_values(target: &FormControlState) -> [(&'static str, String); 7] {
    [
        ("tabStop", bool_name(target.common.tab_stop).to_owned()),
        ("editable", bool_name(target.common.editable).to_owned()),
        ("tabOrder", tab_order_name(target.common.tab_order)),
        ("enabled", bool_name(target.common.enabled).to_owned()),
        (
            "borderTypeIDRef",
            target.common.border_type_id_ref.to_string(),
        ),
        ("drawFrame", bool_name(target.common.draw_frame).to_owned()),
        ("printable", bool_name(target.common.printable).to_owned()),
    ]
}

fn character_attribute_values(target: &FormControlState) -> [(&'static str, String); 4] {
    [
        (
            "charPrIDRef",
            target.common.character.char_pr_id_ref.to_string(),
        ),
        (
            "followContext",
            bool_name(target.common.character.follow_context).to_owned(),
        ),
        (
            "autoSz",
            bool_name(target.common.character.auto_size).to_owned(),
        ),
        (
            "wordWrap",
            bool_name(target.common.character.word_wrap).to_owned(),
        ),
    ]
}

fn push_existing_attribute_edit(
    source: &[u8],
    element: &XmlElementToken,
    name: &str,
    replacement: &str,
    edits: &mut Vec<ByteEdit>,
) -> Result<(), FormControlHwpxError> {
    let span = strict_attribute(element, name)?.value_span();
    if span.end() > source.len() {
        return Err(FormControlHwpxError::InvalidAttribute);
    }
    edits
        .try_reserve(1)
        .map_err(|_| FormControlHwpxError::AllocationFailed)?;
    edits.push(ByteEdit {
        start: span.start(),
        end: span.end(),
        replacement: replacement.as_bytes().to_vec(),
    });
    Ok(())
}

fn push_optional_attribute_edit(
    source: &[u8],
    element: &XmlElementToken,
    name: &str,
    replacement: Option<&str>,
    limits: FormControlHwpxLimits,
    edits: &mut Vec<ByteEdit>,
) -> Result<(), FormControlHwpxError> {
    let attribute = optional_attribute(element, name)?;
    match (attribute, replacement) {
        (Some(_), value) => push_existing_attribute_edit(
            source,
            element,
            name,
            &escape_attribute(value.unwrap_or_default(), limits)?,
            edits,
        ),
        (None, None) => Ok(()),
        (None, Some(value)) => {
            let start_tag = element.start_tag_span();
            let tag = source
                .get(start_tag.start()..start_tag.end())
                .ok_or(FormControlHwpxError::InvalidAttribute)?;
            let offset = if tag.ends_with(b"/>") {
                start_tag.end().checked_sub(2)
            } else if tag.ends_with(b">") {
                start_tag.end().checked_sub(1)
            } else {
                None
            }
            .ok_or(FormControlHwpxError::InvalidAttribute)?;
            let escaped = escape_attribute(value, limits)?;
            edits
                .try_reserve(1)
                .map_err(|_| FormControlHwpxError::AllocationFailed)?;
            edits.push(ByteEdit {
                start: offset,
                end: offset,
                replacement: format!(" {name}=\"{escaped}\"").into_bytes(),
            });
            Ok(())
        }
    }
}

fn apply_edits(
    source: &[u8],
    edits: &[ByteEdit],
    limits: FormControlHwpxLimits,
) -> Result<Vec<u8>, FormControlHwpxError> {
    let mut order: Vec<usize> = (0..edits.len()).collect();
    order.sort_by_key(|&index| (edits[index].start, edits[index].end));
    let mut cursor = 0_usize;
    let mut output_len = source.len();
    for &index in &order {
        let edit = &edits[index];
        if edit.start < cursor || edit.start > edit.end || edit.end > source.len() {
            return Err(FormControlHwpxError::PreservationMismatch);
        }
        cursor = edit.end;
        output_len = output_len
            .checked_sub(edit.end - edit.start)
            .and_then(|value| value.checked_add(edit.replacement.len()))
            .ok_or(FormControlHwpxError::OutputLimit)?;
    }
    if output_len > limits.0.output_bytes {
        return Err(FormControlHwpxError::OutputLimit);
    }
    let mut output = Vec::new();
    output
        .try_reserve_exact(output_len)
        .map_err(|_| FormControlHwpxError::AllocationFailed)?;
    cursor = 0;
    for &index in &order {
        let edit = &edits[index];
        output.extend_from_slice(&source[cursor..edit.start]);
        output.extend_from_slice(&edit.replacement);
        cursor = edit.end;
    }
    output.extend_from_slice(&source[cursor..]);
    if output.len() != output_len {
        return Err(FormControlHwpxError::OutputLimit);
    }
    Ok(output)
}

fn verify_preservation(
    source: &[u8],
    output: &[u8],
    edits: &[ByteEdit],
) -> Result<(), FormControlHwpxError> {
    let mut order: Vec<usize> = (0..edits.len()).collect();
    order.sort_by_key(|&index| (edits[index].start, edits[index].end));
    let mut source_cursor = 0_usize;
    let mut output_cursor = 0_usize;
    for &index in &order {
        let edit = &edits[index];
        let unchanged = edit.start - source_cursor;
        let unchanged_end = output_cursor
            .checked_add(unchanged)
            .ok_or(FormControlHwpxError::PreservationMismatch)?;
        if source[source_cursor..edit.start] != output[output_cursor..unchanged_end] {
            return Err(FormControlHwpxError::PreservationMismatch);
        }
        output_cursor = unchanged_end;
        let replacement_end = output_cursor
            .checked_add(edit.replacement.len())
            .ok_or(FormControlHwpxError::PreservationMismatch)?;
        if output.get(output_cursor..replacement_end) != Some(edit.replacement.as_slice()) {
            return Err(FormControlHwpxError::PreservationMismatch);
        }
        output_cursor = replacement_end;
        source_cursor = edit.end;
    }
    if source[source_cursor..] != output[output_cursor..] {
        return Err(FormControlHwpxError::PreservationMismatch);
    }
    Ok(())
}

fn expect_string(
    source: &[u8],
    element: &XmlElementToken,
    name: &str,
    expected: &str,
    limits: FormControlHwpxLimits,
) -> Result<(), FormControlHwpxError> {
    let value = decoded_attribute(source, strict_attribute(element, name)?, limits)?;
    if value != expected {
        return Err(FormControlHwpxError::ProjectionMismatch);
    }
    Ok(())
}

fn expect_optional_string(
    source: &[u8],
    element: &XmlElementToken,
    name: &str,
    expected: Option<&str>,
    limits: FormControlHwpxLimits,
) -> Result<(), FormControlHwpxError> {
    let value = optional_attribute(element, name)?
        .map(|attribute| decoded_attribute(source, attribute, limits))
        .transpose()?
        .filter(|value| !value.is_empty());
    if value.as_deref() != expected {
        return Err(FormControlHwpxError::ProjectionMismatch);
    }
    Ok(())
}

fn expect_command_digest(
    source: &[u8],
    element: &XmlElementToken,
    expected: Option<&str>,
    limits: FormControlHwpxLimits,
) -> Result<(), FormControlHwpxError> {
    let value = optional_attribute(element, "command")?
        .map(|attribute| decoded_attribute(source, attribute, limits))
        .transpose()?
        .filter(|value| !value.is_empty())
        .map(|value| hex(Sha256::digest(value.as_bytes()).into()));
    if value.as_deref() != expected {
        return Err(FormControlHwpxError::ProjectionMismatch);
    }
    Ok(())
}

fn expect_color(
    source: &[u8],
    element: &XmlElementToken,
    name: &str,
    expected: u32,
) -> Result<(), FormControlHwpxError> {
    let lexical = lexical_value(source, strict_attribute(element, name)?)?;
    if lexical != color_name(expected)? {
        return Err(FormControlHwpxError::ProjectionMismatch);
    }
    Ok(())
}

fn expect_bool(
    source: &[u8],
    element: &XmlElementToken,
    name: &str,
    expected: bool,
) -> Result<(), FormControlHwpxError> {
    if lexical_value(source, strict_attribute(element, name)?)? != bool_name(expected) {
        return Err(FormControlHwpxError::ProjectionMismatch);
    }
    Ok(())
}

fn expect_tab_order(
    source: &[u8],
    element: &XmlElementToken,
    expected: Option<u32>,
) -> Result<(), FormControlHwpxError> {
    if lexical_value(source, strict_attribute(element, "tabOrder")?)? != tab_order_name(expected) {
        return Err(FormControlHwpxError::ProjectionMismatch);
    }
    Ok(())
}

fn expect_u32(
    source: &[u8],
    element: &XmlElementToken,
    name: &str,
    expected: u32,
) -> Result<(), FormControlHwpxError> {
    if canonical_u32(source, strict_attribute(element, name)?)? != expected {
        return Err(FormControlHwpxError::ProjectionMismatch);
    }
    Ok(())
}

fn expect_i32_option(
    source: &[u8],
    element: &XmlElementToken,
    name: &str,
    expected: Option<u32>,
) -> Result<(), FormControlHwpxError> {
    let expected = expected.map_or_else(|| "-1".to_owned(), |value| value.to_string());
    if lexical_value(source, strict_attribute(element, name)?)? != expected {
        return Err(FormControlHwpxError::ProjectionMismatch);
    }
    Ok(())
}

fn expect_enum(
    source: &[u8],
    element: &XmlElementToken,
    name: &str,
    expected: &str,
) -> Result<(), FormControlHwpxError> {
    if lexical_value(source, strict_attribute(element, name)?)? != expected {
        return Err(FormControlHwpxError::ProjectionMismatch);
    }
    Ok(())
}

fn expect_element_text(
    source: &[u8],
    document: &PreservingXmlDocument,
    index: usize,
    expected: &str,
    limits: FormControlHwpxLimits,
) -> Result<(), FormControlHwpxError> {
    let element = element(document, index)?;
    if element.first_child().is_some() {
        return Err(FormControlHwpxError::UnsupportedControl);
    }
    let span = element
        .content_span()
        .ok_or(FormControlHwpxError::UnsupportedControl)?;
    let lexical = std::str::from_utf8(
        source
            .get(span.start()..span.end())
            .ok_or(FormControlHwpxError::InvalidAttribute)?,
    )
    .map_err(|_| FormControlHwpxError::InvalidAttribute)?;
    if lexical.len() > limits.0.text_bytes {
        return Err(FormControlHwpxError::InputLimit);
    }
    let decoded = unescape(lexical).map_err(|_| FormControlHwpxError::InvalidAttribute)?;
    if decoded.as_ref() != expected {
        return Err(FormControlHwpxError::ProjectionMismatch);
    }
    Ok(())
}

fn strict_attribute<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<&'a XmlAttributeToken, FormControlHwpxError> {
    optional_attribute(element, name)?.ok_or(FormControlHwpxError::InvalidAttribute)
}

fn optional_attribute<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<Option<&'a XmlAttributeToken>, FormControlHwpxError> {
    let mut matches = element.attributes().iter().filter(|attribute| {
        !attribute.is_namespace_declaration() && attribute.name().local_name() == name
    });
    let value = matches.next();
    if value.is_some_and(|attribute| attribute.name().namespace().is_some())
        || matches.next().is_some()
    {
        return Err(FormControlHwpxError::InvalidAttribute);
    }
    Ok(value)
}

fn lexical_value<'a>(
    source: &'a [u8],
    attribute: &XmlAttributeToken,
) -> Result<&'a str, FormControlHwpxError> {
    std::str::from_utf8(
        source
            .get(attribute.value_span().start()..attribute.value_span().end())
            .ok_or(FormControlHwpxError::InvalidAttribute)?,
    )
    .map_err(|_| FormControlHwpxError::InvalidAttribute)
}

fn decoded_attribute(
    source: &[u8],
    attribute: &XmlAttributeToken,
    limits: FormControlHwpxLimits,
) -> Result<String, FormControlHwpxError> {
    let lexical = lexical_value(source, attribute)?;
    if lexical.len() > limits.0.text_bytes {
        return Err(FormControlHwpxError::InputLimit);
    }
    let value = unescape(lexical).map_err(|_| FormControlHwpxError::InvalidAttribute)?;
    if value.len() > limits.0.text_bytes {
        return Err(FormControlHwpxError::InputLimit);
    }
    Ok(value.into_owned())
}

fn canonical_u32(
    source: &[u8],
    attribute: &XmlAttributeToken,
) -> Result<u32, FormControlHwpxError> {
    let value = lexical_value(source, attribute)?;
    if value.is_empty()
        || !value.bytes().all(|byte| byte.is_ascii_digit())
        || (value != "0" && value.starts_with('0'))
    {
        return Err(FormControlHwpxError::InvalidAttribute);
    }
    value
        .parse::<u32>()
        .map_err(|_| FormControlHwpxError::InvalidAttribute)
}

fn escape_attribute(
    value: &str,
    limits: FormControlHwpxLimits,
) -> Result<String, FormControlHwpxError> {
    if value.len() > limits.0.text_bytes || value.chars().any(invalid_xml_character) {
        return Err(FormControlHwpxError::OutputLimit);
    }
    Ok(value
        .replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
        .replace('\'', "&apos;"))
}

const fn invalid_xml_character(value: char) -> bool {
    !matches!(
        value as u32,
        0x9 | 0xA | 0xD | 0x20..=0xD7FF | 0xE000..=0xFFFD | 0x0001_0000..=0x0010_FFFF
    )
}

fn only_direct_child(
    document: &PreservingXmlDocument,
    parent: usize,
    local_name: &str,
) -> Result<usize, FormControlHwpxError> {
    let children = direct_children_named(document, parent, local_name)?;
    if children.len() != 1 {
        return Err(FormControlHwpxError::UnsupportedControl);
    }
    Ok(children[0])
}

fn direct_children_named(
    document: &PreservingXmlDocument,
    parent: usize,
    local_name: &str,
) -> Result<Vec<usize>, FormControlHwpxError> {
    let mut children = Vec::new();
    let mut child = element(document, parent)?.first_child();
    while let Some(index) = child {
        let candidate = element(document, index)?;
        if has_name(candidate, local_name) {
            children
                .try_reserve(1)
                .map_err(|_| FormControlHwpxError::AllocationFailed)?;
            children.push(index);
        }
        child = candidate.next_sibling();
    }
    Ok(children)
}

fn is_form(element: &XmlElementToken) -> bool {
    element.name().namespace() == Some(PARAGRAPH_NS)
        && matches!(
            element.name().local_name(),
            "edit" | "checkBtn" | "radioBtn" | "comboBox" | "listBox"
        )
}

fn has_name(element: &XmlElementToken, local_name: &str) -> bool {
    element.name().namespace() == Some(PARAGRAPH_NS) && element.name().local_name() == local_name
}

fn element(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<&XmlElementToken, FormControlHwpxError> {
    document
        .elements()
        .get(index)
        .ok_or(FormControlHwpxError::UnsupportedControl)
}

fn outer_span(
    element: &XmlElementToken,
) -> Result<crate::preserving_xml::XmlByteSpan, FormControlHwpxError> {
    element
        .outer_span()
        .ok_or(FormControlHwpxError::UnsupportedControl)
}

fn digest_span(
    source: &[u8],
    span: crate::preserving_xml::XmlByteSpan,
) -> Result<[u8; 32], FormControlHwpxError> {
    Ok(Sha256::digest(
        source
            .get(span.start()..span.end())
            .ok_or(FormControlHwpxError::UnsupportedControl)?,
    )
    .into())
}

const fn tag_name(tag: NativeFormTag) -> &'static str {
    match tag {
        NativeFormTag::Edit => "edit",
        NativeFormTag::CheckBtn => "checkBtn",
        NativeFormTag::RadioBtn => "radioBtn",
        NativeFormTag::ComboBox => "comboBox",
        NativeFormTag::ListBox => "listBox",
    }
}

const fn bool_name(value: bool) -> &'static str {
    if value { "1" } else { "0" }
}

fn color_name(value: u32) -> Result<String, FormControlHwpxError> {
    if value > 0x00FF_FFFF {
        return Err(FormControlHwpxError::NonRepresentable);
    }
    Ok(format!("#{value:06X}"))
}

fn tab_order_name(value: Option<u32>) -> String {
    value.map_or_else(|| "-1".to_owned(), |value| value.to_string())
}

const fn scroll_bars_name(value: FormScrollBars) -> &'static str {
    match value {
        FormScrollBars::None => "NONE",
        FormScrollBars::Vertical => "VERTICAL",
        FormScrollBars::Horizontal => "HORIZONTAL",
        FormScrollBars::Both => "BOTH",
    }
}

const fn tab_behavior_name(value: FormTabKeyBehavior) -> &'static str {
    match value {
        FormTabKeyBehavior::NextObject => "NEXT_OBJECT",
        FormTabKeyBehavior::InsertTab => "INSERT_TAB",
    }
}

const fn alignment_name(value: FormTextAlignment) -> &'static str {
    match value {
        FormTextAlignment::Left => "LEFT",
        FormTextAlignment::Center => "CENTER",
        FormTextAlignment::Right => "RIGHT",
    }
}

const fn button_value_name(value: FormButtonValue) -> &'static str {
    match value {
        FormButtonValue::Unchecked => "UNCHECKED",
        FormButtonValue::Checked => "CHECKED",
        FormButtonValue::Indeterminate => "INDETERMINATE",
    }
}

const fn back_style_name(value: FormButtonBackStyle) -> &'static str {
    match value {
        FormButtonBackStyle::Transparent => "TRANSPARENT",
        FormButtonBackStyle::Opaque => "OPAQUE",
    }
}

fn validate_plan(
    plan: &FormControlHwpxPlan,
    limits: FormControlHwpxLimits,
) -> Result<(), FormControlHwpxError> {
    if plan.schema_version != FORM_CONTROL_SCHEMA_VERSION
        || plan.profile_id != FORM_CONTROL_HWPX_PROFILE_ID
        || !matches!(
            plan.domain_plan.capability_id(),
            "ref.form_properties" | "ref.form_tab_order"
        )
        || plan.source_document_flow_sha256 != plan.domain_plan.source_document_flow_sha256()
        || plan.domain_plan.plan_sha256() != plan.domain_plan_sha256
        || plan_binding_sha256(plan, limits)? != plan.plan_sha256
    {
        return Err(FormControlHwpxError::PlanTampered);
    }
    Ok(())
}

fn plan_binding_sha256(
    plan: &FormControlHwpxPlan,
    limits: FormControlHwpxLimits,
) -> Result<String, FormControlHwpxError> {
    let mut unsigned = plan.clone();
    unsigned.plan_sha256.clear();
    Ok(hex(
        Sha256::digest(serialize_bounded(&unsigned, limits)?).into()
    ))
}

fn serialize_bounded<T: Serialize>(
    value: &T,
    limits: FormControlHwpxLimits,
) -> Result<Vec<u8>, FormControlHwpxError> {
    let bytes = serde_json::to_vec(value).map_err(|_| FormControlHwpxError::PlanTampered)?;
    if bytes.len() > limits.0.plan_bytes {
        return Err(FormControlHwpxError::OutputLimit);
    }
    Ok(bytes)
}

fn hex(bytes: [u8; 32]) -> String {
    let mut output = String::with_capacity(64);
    for byte in bytes {
        use std::fmt::Write as _;
        let _ = write!(output, "{byte:02x}");
    }
    output
}

#[cfg(test)]
mod private_tests {
    #![allow(clippy::expect_used, clippy::too_many_lines)] // Fixture construction stays local.

    use super::*;
    use domain_ir::{
        FormCharacterProperties, FormCommonProperties, FormControlAnchor, FormControlIdentity,
        FormControlLimitConfig, FormControlOperation, FormControlRequest, FormControlRequestDraft,
        FormControlState, FormDocumentStateDraft, FormTextValidation, LogicalId,
    };

    const FLOW_A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
    const FLOW_B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";

    fn sealed_plan() -> FormControlHwpxPlan {
        let state_limits =
            FormControlLimits::new(FormControlLimitConfig::default()).expect("state limits");
        let payload = FormControlPayload::Text {
            value: "value".to_owned(),
            default_value: "value".to_owned(),
            validation: FormTextValidation {
                required: false,
                minimum_characters: 0,
                maximum_characters: Some(16),
                external_validator_sha256: None,
            },
            multi_line: false,
            password_character: None,
            native_max_length: Some(16),
            scroll_bars: FormScrollBars::None,
            tab_key_behavior: FormTabKeyBehavior::NextObject,
            number_only: false,
            read_only: false,
            alignment: FormTextAlignment::Left,
        };
        let common = FormCommonProperties {
            name: "control".to_owned(),
            fore_color_rgb: 0,
            back_color_rgb: 0x00ff_ffff,
            group_name: None,
            tab_stop: true,
            tab_order: Some(0),
            editable: true,
            enabled: true,
            border_type_id_ref: 1,
            draw_frame: true,
            printable: true,
            command_sha256: None,
            character: FormCharacterProperties {
                char_pr_id_ref: 1,
                follow_context: false,
                auto_size: false,
                word_wrap: true,
            },
        };
        let control = FormControlState {
            identity: FormControlIdentity {
                logical_control_id: LogicalId::parse("control-1").expect("control id"),
                native_object_id: 1,
            },
            anchor: FormControlAnchor {
                paragraph_id: LogicalId::parse("paragraph-1").expect("paragraph id"),
                run_ordinal: 0,
                inline_ordinal: 0,
            },
            native_binding: FormNativeBinding::Exact {
                tag: NativeFormTag::Edit,
            },
            common: common.clone(),
            payload: payload.clone(),
            shape_locked: false,
            shape_state_sha256: FLOW_A.to_owned(),
            opaque_native_payload_sha256: FLOW_B.to_owned(),
            opaque_properties: Vec::new(),
        };
        let state = FormDocumentState::from_draft(
            FormDocumentStateDraft {
                schema_version: FORM_CONTROL_SCHEMA_VERSION.to_owned(),
                controls: vec![control],
                non_form_content_sha256: FLOW_A.to_owned(),
                style_catalog_sha256: FLOW_B.to_owned(),
                border_catalog_sha256: FLOW_A.to_owned(),
                resource_inventory_sha256: FLOW_B.to_owned(),
                reference_inventory_sha256: FLOW_A.to_owned(),
                document_protection_sha256: FLOW_B.to_owned(),
                opaque_document_state_sha256: FLOW_A.to_owned(),
            },
            state_limits,
        )
        .expect("state");
        let mut replacement = common;
        replacement.enabled = false;
        let request = FormControlRequest::from_draft(
            FormControlRequestDraft {
                schema_version: FORM_CONTROL_SCHEMA_VERSION.to_owned(),
                request_id: LogicalId::parse("request-1").expect("request id"),
                expected_source_state_sha256: state
                    .canonical_sha256(state_limits)
                    .expect("state digest"),
                expected_document_flow_sha256: FLOW_A.to_owned(),
                target_document_flow_sha256: FLOW_B.to_owned(),
                operation: FormControlOperation::ReplaceProperties {
                    target: FormControlIdentity {
                        logical_control_id: LogicalId::parse("control-1").expect("control id"),
                        native_object_id: 1,
                    },
                    common: replacement,
                    payload,
                },
            },
            &state,
            FLOW_A,
            state_limits,
        )
        .expect("request");
        let domain =
            FormControlBuilder::plan(&state, &request, FLOW_A, state_limits).expect("domain plan");
        let source = b"<hp:sec xmlns:hp=\"http://www.hancom.co.kr/hwpml/2011/paragraph\"><hp:run><hp:edit id=\"1\" name=\"control\" foreColor=\"#000000\" backColor=\"#FFFFFF\" tabStop=\"1\" editable=\"1\" tabOrder=\"0\" enabled=\"1\" borderTypeIDRef=\"1\" drawFrame=\"1\" printable=\"1\" multiLine=\"0\" maxLength=\"16\" scrollBars=\"NONE\" tabKeyBehavior=\"NEXT_OBJECT\" numOnly=\"0\" readOnly=\"0\" alignText=\"LEFT\"><hp:formCharPr charPrIDRef=\"1\" followContext=\"0\" autoSz=\"0\" wordWrap=\"1\"/><hp:text>value</hp:text></hp:edit></hp:run></hp:sec>";
        FormControlHwpxBuilder::plan(
            source,
            &domain,
            FLOW_A,
            state_limits,
            FormControlHwpxLimits::new(FormControlHwpxLimitConfig::default()).expect("HWPX limits"),
        )
        .expect("HWPX plan")
    }

    #[test]
    fn public_errors_do_not_contain_source_values() {
        assert_eq!(
            FormControlHwpxError::ProjectionMismatch.code(),
            "form_control_hwpx_projection_mismatch"
        );
        assert!(!format!("{:?}", FormControlHwpxError::SourceDrift).contains("D:\\"));
    }

    #[test]
    fn tampered_private_plan_binding_is_rejected() {
        let mut plan = sealed_plan();
        plan.profile_id = "tampered-profile";
        assert_eq!(
            validate_plan(
                &plan,
                FormControlHwpxLimits::new(FormControlHwpxLimitConfig::default())
                    .expect("HWPX limits"),
            ),
            Err(FormControlHwpxError::PlanTampered)
        );
    }
}
