use std::collections::{BTreeMap, BTreeSet};
use std::fmt;

use serde::de::{self, MapAccess, Visitor};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::LogicalId;

pub const FORM_CONTROL_SCHEMA_VERSION: &str = "hwpx-agent.form-control/v1";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct FormControlLimitConfig {
    pub input_bytes: usize,
    pub output_bytes: usize,
    pub controls: usize,
    pub items_per_control: usize,
    pub text_bytes: usize,
    pub name_bytes: usize,
    pub opaque_entries: usize,
}

impl Default for FormControlLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 1024 * 1024,
            output_bytes: 1024 * 1024,
            controls: 65_536,
            items_per_control: 65_536,
            text_bytes: 64 * 1024,
            name_bytes: 1024,
            opaque_entries: 4096,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct FormControlLimits(FormControlLimitConfig);

impl FormControlLimits {
    pub const HARD_MAX_BYTES: usize = 8 * 1024 * 1024;
    pub const HARD_MAX_CONTROLS: usize = 1_000_000;
    pub const HARD_MAX_ITEMS: usize = 1_000_000;
    pub const HARD_MAX_TEXT_BYTES: usize = 1024 * 1024;
    pub const HARD_MAX_NAME_BYTES: usize = 16 * 1024;
    pub const HARD_MAX_OPAQUE_ENTRIES: usize = 65_536;

    /// Creates finite form-control limits without silently clamping values.
    ///
    /// # Errors
    ///
    /// Rejects zero, inconsistent, or hard-ceiling-exceeding values.
    pub fn new(config: FormControlLimitConfig) -> Result<Self, FormControlError> {
        if config.input_bytes == 0
            || config.output_bytes == 0
            || config.input_bytes > config.output_bytes
            || config.output_bytes > Self::HARD_MAX_BYTES
            || config.controls == 0
            || config.controls > Self::HARD_MAX_CONTROLS
            || config.items_per_control == 0
            || config.items_per_control > Self::HARD_MAX_ITEMS
            || config.text_bytes == 0
            || config.text_bytes > Self::HARD_MAX_TEXT_BYTES
            || config.name_bytes == 0
            || config.name_bytes > Self::HARD_MAX_NAME_BYTES
            || config.opaque_entries == 0
            || config.opaque_entries > Self::HARD_MAX_OPAQUE_ENTRIES
        {
            return Err(FormControlError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> FormControlLimitConfig {
        self.0
    }
}

#[derive(Clone, Deserialize, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FormControlIdentity {
    pub logical_control_id: LogicalId,
    pub native_object_id: u32,
}

impl fmt::Debug for FormControlIdentity {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("FormControlIdentity(<redacted>)")
    }
}

#[derive(Clone, Deserialize, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FormControlAnchor {
    pub paragraph_id: LogicalId,
    pub run_ordinal: u32,
    pub inline_ordinal: u32,
}

impl fmt::Debug for FormControlAnchor {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("FormControlAnchor(<redacted>)")
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum NativeFormTag {
    Edit,
    CheckBtn,
    RadioBtn,
    ComboBox,
    ListBox,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum FormNativeBinding {
    Exact { tag: NativeFormTag },
    UnverifiedDateControl,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FormCharacterProperties {
    pub char_pr_id_ref: u32,
    pub follow_context: bool,
    pub auto_size: bool,
    pub word_wrap: bool,
}

impl fmt::Debug for FormCharacterProperties {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("FormCharacterProperties(<redacted>)")
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
#[allow(clippy::struct_excessive_bools)] // Mirrors independent native form attributes exactly.
pub struct FormCommonProperties {
    pub name: String,
    pub fore_color_rgb: u32,
    pub back_color_rgb: u32,
    pub group_name: Option<String>,
    pub tab_stop: bool,
    pub tab_order: Option<u32>,
    pub editable: bool,
    pub enabled: bool,
    pub border_type_id_ref: u32,
    pub draw_frame: bool,
    pub printable: bool,
    pub command_sha256: Option<String>,
    pub character: FormCharacterProperties,
}

impl fmt::Debug for FormCommonProperties {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FormCommonProperties")
            .field("tab_stop", &self.tab_stop)
            .field("editable", &self.editable)
            .field("enabled", &self.enabled)
            .field("payload", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FormTextValidation {
    pub required: bool,
    pub minimum_characters: u32,
    pub maximum_characters: Option<u32>,
    pub external_validator_sha256: Option<String>,
}

impl fmt::Debug for FormTextValidation {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("FormTextValidation(<redacted>)")
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FormSelectionValidation {
    pub required: bool,
    pub external_validator_sha256: Option<String>,
}

impl fmt::Debug for FormSelectionValidation {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("FormSelectionValidation(<redacted>)")
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FormDateValidation {
    pub required: bool,
    pub earliest: Option<String>,
    pub latest: Option<String>,
    pub external_validator_sha256: Option<String>,
}

impl fmt::Debug for FormDateValidation {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("FormDateValidation(<redacted>)")
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum FormScrollBars {
    None,
    Vertical,
    Horizontal,
    Both,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum FormTabKeyBehavior {
    NextObject,
    InsertTab,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum FormTextAlignment {
    Left,
    Center,
    Right,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum FormButtonValue {
    Unchecked,
    Checked,
    Indeterminate,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum FormButtonBackStyle {
    Transparent,
    Opaque,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FormListItem {
    pub display_text: String,
    pub value: String,
}

impl fmt::Debug for FormListItem {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("FormListItem(<redacted>)")
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum FormControlPayload {
    Text {
        value: String,
        default_value: String,
        validation: FormTextValidation,
        multi_line: bool,
        password_character: Option<String>,
        native_max_length: Option<u32>,
        scroll_bars: FormScrollBars,
        tab_key_behavior: FormTabKeyBehavior,
        number_only: bool,
        read_only: bool,
        alignment: FormTextAlignment,
    },
    Checkbox {
        caption: String,
        value: FormButtonValue,
        default_value: FormButtonValue,
        must_be_checked: bool,
        radio_group_name: Option<String>,
        tri_state: bool,
        back_style: FormButtonBackStyle,
    },
    Radio {
        caption: String,
        value: FormButtonValue,
        default_value: FormButtonValue,
        radio_group_name: String,
        group_required: bool,
        tri_state: bool,
        back_style: FormButtonBackStyle,
    },
    Combo {
        items: Vec<FormListItem>,
        selected_value: Option<String>,
        default_selected_value: Option<String>,
        validation: FormSelectionValidation,
        list_box_rows: Option<u32>,
        list_box_width_hwp_units: Option<u32>,
        edit_enable: bool,
    },
    List {
        items: Vec<FormListItem>,
        selected_value: Option<String>,
        default_selected_value: Option<String>,
        validation: FormSelectionValidation,
        item_height_hwp_units: Option<u32>,
        top_index: u32,
    },
    Date {
        value: Option<String>,
        default_value: Option<String>,
        format: String,
        locale: String,
        validation: FormDateValidation,
    },
}

impl FormControlPayload {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        match self {
            Self::Text { .. } => "ref.form_text",
            Self::Checkbox { .. } => "ref.form_checkbox",
            Self::Radio { .. } => "ref.form_radio",
            Self::Combo { .. } => "ref.form_combo",
            Self::List { .. } => "ref.form_list",
            Self::Date { .. } => "ref.form_date",
        }
    }

    const fn expected_native_binding(&self) -> FormNativeBinding {
        match self {
            Self::Text { .. } => FormNativeBinding::Exact {
                tag: NativeFormTag::Edit,
            },
            Self::Checkbox { .. } => FormNativeBinding::Exact {
                tag: NativeFormTag::CheckBtn,
            },
            Self::Radio { .. } => FormNativeBinding::Exact {
                tag: NativeFormTag::RadioBtn,
            },
            Self::Combo { .. } => FormNativeBinding::Exact {
                tag: NativeFormTag::ComboBox,
            },
            Self::List { .. } => FormNativeBinding::Exact {
                tag: NativeFormTag::ListBox,
            },
            Self::Date { .. } => FormNativeBinding::UnverifiedDateControl,
        }
    }
}

impl fmt::Debug for FormControlPayload {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FormControlPayload")
            .field("capability_id", &self.capability_id())
            .field("payload", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct OpaqueFormProperty {
    pub namespace: String,
    pub name: String,
    pub value_sha256: String,
}

impl fmt::Debug for OpaqueFormProperty {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("OpaqueFormProperty(<redacted>)")
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FormControlState {
    pub identity: FormControlIdentity,
    pub anchor: FormControlAnchor,
    pub native_binding: FormNativeBinding,
    pub common: FormCommonProperties,
    pub payload: FormControlPayload,
    pub shape_locked: bool,
    pub shape_state_sha256: String,
    pub opaque_native_payload_sha256: String,
    pub opaque_properties: Vec<OpaqueFormProperty>,
}

impl fmt::Debug for FormControlState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FormControlState")
            .field("capability_id", &self.payload.capability_id())
            .field("native_binding", &self.native_binding)
            .field("shape_locked", &self.shape_locked)
            .field("state", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FormDocumentStateDraft {
    pub schema_version: String,
    pub controls: Vec<FormControlState>,
    pub non_form_content_sha256: String,
    pub style_catalog_sha256: String,
    pub border_catalog_sha256: String,
    pub resource_inventory_sha256: String,
    pub reference_inventory_sha256: String,
    pub document_protection_sha256: String,
    pub opaque_document_state_sha256: String,
}

impl fmt::Debug for FormDocumentStateDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("FormDocumentStateDraft(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct FormDocumentState {
    schema_version: &'static str,
    controls: Vec<FormControlState>,
    non_form_content_sha256: String,
    style_catalog_sha256: String,
    border_catalog_sha256: String,
    resource_inventory_sha256: String,
    reference_inventory_sha256: String,
    document_protection_sha256: String,
    opaque_document_state_sha256: String,
}

impl FormDocumentState {
    /// Validates and seals a complete ordered form-control inventory.
    ///
    /// # Errors
    ///
    /// Rejects version, identity, anchor, native binding, input, protection, or limit failures.
    pub fn from_draft(
        draft: FormDocumentStateDraft,
        limits: FormControlLimits,
    ) -> Result<Self, FormControlError> {
        if draft.schema_version != FORM_CONTROL_SCHEMA_VERSION {
            return Err(FormControlError::UnsupportedVersion);
        }
        let state = Self {
            schema_version: FORM_CONTROL_SCHEMA_VERSION,
            controls: draft.controls,
            non_form_content_sha256: draft.non_form_content_sha256,
            style_catalog_sha256: draft.style_catalog_sha256,
            border_catalog_sha256: draft.border_catalog_sha256,
            resource_inventory_sha256: draft.resource_inventory_sha256,
            reference_inventory_sha256: draft.reference_inventory_sha256,
            document_protection_sha256: draft.document_protection_sha256,
            opaque_document_state_sha256: draft.opaque_document_state_sha256,
        };
        validate_document_state(&state, limits)?;
        let _ = state.canonical_json(limits)?;
        Ok(state)
    }

    #[must_use]
    pub fn controls(&self) -> &[FormControlState] {
        &self.controls
    }

    /// Serializes the complete state deterministically within the configured bound.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit failure.
    pub fn canonical_json(&self, limits: FormControlLimits) -> Result<Vec<u8>, FormControlError> {
        serialize_bounded(self, limits)
    }

    /// Returns the SHA-256 of the complete canonical form state.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit failure.
    pub fn canonical_sha256(&self, limits: FormControlLimits) -> Result<String, FormControlError> {
        Ok(hex(Sha256::digest(self.canonical_json(limits)?).into()))
    }
}

impl fmt::Debug for FormDocumentState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FormDocumentState")
            .field("control_count", &self.controls.len())
            .field("state", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FormTabAssignment {
    pub target: FormControlIdentity,
    pub tab_stop: bool,
    pub tab_order: Option<u32>,
}

impl fmt::Debug for FormTabAssignment {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("FormTabAssignment(<redacted>)")
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum FormControlOperation {
    Insert {
        insertion_index: usize,
        control: FormControlState,
    },
    ReplaceProperties {
        target: FormControlIdentity,
        common: FormCommonProperties,
        payload: FormControlPayload,
    },
    SetTabOrder {
        assignments: Vec<FormTabAssignment>,
    },
}

impl FormControlOperation {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        match self {
            Self::Insert { control, .. } => control.payload.capability_id(),
            Self::ReplaceProperties { .. } => "ref.form_properties",
            Self::SetTabOrder { .. } => "ref.form_tab_order",
        }
    }
}

impl fmt::Debug for FormControlOperation {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FormControlOperation")
            .field("capability_id", &self.capability_id())
            .field("payload", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FormControlRequestDraft {
    pub schema_version: String,
    pub request_id: LogicalId,
    pub expected_source_state_sha256: String,
    pub expected_document_flow_sha256: String,
    pub target_document_flow_sha256: String,
    pub operation: FormControlOperation,
}

impl fmt::Debug for FormControlRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("FormControlRequestDraft(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct FormControlRequest {
    schema_version: &'static str,
    request_id: LogicalId,
    expected_source_state_sha256: String,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    operation: FormControlOperation,
}

impl FormControlRequest {
    /// Validates one exact form transition against current state and document flow.
    ///
    /// # Errors
    ///
    /// Rejects schema, source-state, flow, operation, protection, or limit failures.
    pub fn from_draft(
        draft: FormControlRequestDraft,
        current: &FormDocumentState,
        current_document_flow_sha256: &str,
        limits: FormControlLimits,
    ) -> Result<Self, FormControlError> {
        if draft.schema_version != FORM_CONTROL_SCHEMA_VERSION {
            return Err(FormControlError::UnsupportedVersion);
        }
        require_digest(&draft.expected_source_state_sha256)?;
        require_digest(&draft.expected_document_flow_sha256)?;
        require_digest(&draft.target_document_flow_sha256)?;
        require_digest(current_document_flow_sha256)?;
        if current.canonical_sha256(limits)? != draft.expected_source_state_sha256 {
            return Err(FormControlError::SourceStateDrift);
        }
        if current_document_flow_sha256 != draft.expected_document_flow_sha256 {
            return Err(FormControlError::DocumentFlowDrift);
        }
        let _ = apply_operation(current, &draft.operation, limits)?;
        let request = Self {
            schema_version: FORM_CONTROL_SCHEMA_VERSION,
            request_id: draft.request_id,
            expected_source_state_sha256: draft.expected_source_state_sha256,
            expected_document_flow_sha256: draft.expected_document_flow_sha256,
            target_document_flow_sha256: draft.target_document_flow_sha256,
            operation: draft.operation,
        };
        let _ = request.canonical_json(limits)?;
        Ok(request)
    }

    /// Parses strict, bounded, duplicate-key-free request JSON.
    ///
    /// # Errors
    ///
    /// Rejects malformed, duplicated, unknown, oversized, stale, or invalid input.
    pub fn from_json(
        bytes: &[u8],
        current: &FormDocumentState,
        current_document_flow_sha256: &str,
        limits: FormControlLimits,
    ) -> Result<Self, FormControlError> {
        if bytes.is_empty() || bytes.len() > limits.0.input_bytes {
            return Err(FormControlError::InputLimit);
        }
        reject_duplicate_json_keys(bytes)?;
        let draft = serde_json::from_slice(bytes).map_err(|_| FormControlError::InvalidJson)?;
        Self::from_draft(draft, current, current_document_flow_sha256, limits)
    }

    #[must_use]
    pub fn operation(&self) -> &FormControlOperation {
        &self.operation
    }

    /// Serializes the request deterministically within the configured bound.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit failure.
    pub fn canonical_json(&self, limits: FormControlLimits) -> Result<Vec<u8>, FormControlError> {
        serialize_bounded(self, limits)
    }
}

impl fmt::Debug for FormControlRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FormControlRequest")
            .field("capability_id", &self.operation.capability_id())
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct FormControlPlan {
    schema_version: &'static str,
    capability_id: &'static str,
    request_id: LogicalId,
    source_state: FormDocumentState,
    source_state_sha256: String,
    target_state: FormDocumentState,
    target_state_sha256: String,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    operation: FormControlOperation,
    plan_sha256: String,
}

impl FormControlPlan {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
    }

    #[must_use]
    pub const fn source_state(&self) -> &FormDocumentState {
        &self.source_state
    }

    #[must_use]
    pub const fn target_state(&self) -> &FormDocumentState {
        &self.target_state
    }

    #[must_use]
    pub fn source_document_flow_sha256(&self) -> &str {
        &self.source_document_flow_sha256
    }

    #[must_use]
    pub fn target_document_flow_sha256(&self) -> &str {
        &self.target_document_flow_sha256
    }

    #[must_use]
    pub fn plan_sha256(&self) -> &str {
        &self.plan_sha256
    }

    /// Serializes the sealed plan deterministically within the configured bound.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit failure.
    pub fn canonical_json(&self, limits: FormControlLimits) -> Result<Vec<u8>, FormControlError> {
        serialize_bounded(self, limits)
    }
}

impl fmt::Debug for FormControlPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FormControlPlan")
            .field("capability_id", &self.capability_id)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct FormControlBuilder;

impl FormControlBuilder {
    /// Builds and seals an immutable plan from current state and a validated request.
    ///
    /// # Errors
    ///
    /// Rejects source-state, flow, operation, protection, or output drift.
    pub fn plan(
        current: &FormDocumentState,
        request: &FormControlRequest,
        current_document_flow_sha256: &str,
        limits: FormControlLimits,
    ) -> Result<FormControlPlan, FormControlError> {
        require_digest(current_document_flow_sha256)?;
        let source_state_sha256 = current.canonical_sha256(limits)?;
        if source_state_sha256 != request.expected_source_state_sha256 {
            return Err(FormControlError::SourceStateDrift);
        }
        if current_document_flow_sha256 != request.expected_document_flow_sha256 {
            return Err(FormControlError::DocumentFlowDrift);
        }
        let target_state = apply_operation(current, &request.operation, limits)?;
        let target_state_sha256 = target_state.canonical_sha256(limits)?;
        let mut plan = FormControlPlan {
            schema_version: FORM_CONTROL_SCHEMA_VERSION,
            capability_id: request.operation.capability_id(),
            request_id: request.request_id.clone(),
            source_state: current.clone(),
            source_state_sha256,
            target_state,
            target_state_sha256,
            source_document_flow_sha256: request.expected_document_flow_sha256.clone(),
            target_document_flow_sha256: request.target_document_flow_sha256.clone(),
            operation: request.operation.clone(),
            plan_sha256: String::new(),
        };
        plan.plan_sha256 = plan_binding_sha256(&plan, limits)?;
        let _ = plan.canonical_json(limits)?;
        Ok(plan)
    }

    /// Revalidates a sealed plan against current state and flow before returning a result.
    ///
    /// # Errors
    ///
    /// Rejects source-state, flow, plan binding, operation, protection, or output drift.
    pub fn build(
        plan: &FormControlPlan,
        current: &FormDocumentState,
        current_document_flow_sha256: &str,
        limits: FormControlLimits,
    ) -> Result<FormControlResult, FormControlError> {
        validate_document_state(current, limits)?;
        if plan.schema_version != FORM_CONTROL_SCHEMA_VERSION
            || plan.capability_id != plan.operation.capability_id()
            || plan.plan_sha256 != plan_binding_sha256(plan, limits)?
        {
            return Err(FormControlError::PlanTampered);
        }
        if current.canonical_sha256(limits)? != plan.source_state_sha256
            || current != &plan.source_state
        {
            return Err(FormControlError::SourceStateDrift);
        }
        if current_document_flow_sha256 != plan.source_document_flow_sha256 {
            return Err(FormControlError::DocumentFlowDrift);
        }
        let recomputed = apply_operation(&plan.source_state, &plan.operation, limits)?;
        if recomputed != plan.target_state
            || recomputed.canonical_sha256(limits)? != plan.target_state_sha256
        {
            return Err(FormControlError::PlanTampered);
        }
        let receipt = FormControlReceipt {
            schema_version: FORM_CONTROL_SCHEMA_VERSION,
            capability_id: plan.capability_id,
            source_state_sha256: plan.source_state_sha256.clone(),
            target_state_sha256: plan.target_state_sha256.clone(),
            source_document_flow_sha256: plan.source_document_flow_sha256.clone(),
            target_document_flow_sha256: plan.target_document_flow_sha256.clone(),
            plan_sha256: plan.plan_sha256.clone(),
        };
        let _ = serialize_bounded(&receipt, limits)?;
        Ok(FormControlResult {
            state: plan.target_state.clone(),
            receipt,
        })
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct FormControlReceipt {
    schema_version: &'static str,
    capability_id: &'static str,
    source_state_sha256: String,
    target_state_sha256: String,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    plan_sha256: String,
}

impl fmt::Debug for FormControlReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FormControlReceipt")
            .field("capability_id", &self.capability_id)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct FormControlResult {
    pub state: FormDocumentState,
    pub receipt: FormControlReceipt,
}

impl fmt::Debug for FormControlResult {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FormControlResult")
            .field("state", &"<redacted>")
            .field("receipt", &self.receipt)
            .finish()
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum FormControlError {
    #[error("form-control limits are invalid")]
    InvalidLimit,
    #[error("form-control input exceeds a finite limit")]
    InputLimit,
    #[error("form-control JSON is malformed, duplicated, or not strict")]
    InvalidJson,
    #[error("form-control schema version is unsupported")]
    UnsupportedVersion,
    #[error("form-control identity, name, or anchor is invalid or colliding")]
    InvalidIdentity,
    #[error("form-control digest is malformed")]
    InvalidDigest,
    #[error("form-control common properties are invalid")]
    InvalidProperties,
    #[error("form-control native binding is incompatible or unverified")]
    InvalidNativeBinding,
    #[error("form-control input or validation state is invalid")]
    InvalidInput,
    #[error("form-control list items or selection are invalid")]
    InvalidSelection,
    #[error("form-control radio group is invalid")]
    InvalidRadioGroup,
    #[error("form-control tab-order replacement is incomplete or invalid")]
    InvalidTabOrder,
    #[error("form-control insertion index is invalid")]
    InvalidInsertionIndex,
    #[error("form-control target does not exist or is ambiguous")]
    ControlNotFound,
    #[error("form-control or containing document is protected")]
    Protected,
    #[error("form-control operation is a no-op")]
    Noop,
    #[error("form-control source state drifted")]
    SourceStateDrift,
    #[error("form-control document flow drifted")]
    DocumentFlowDrift,
    #[error("form-control plan was tampered with")]
    PlanTampered,
    #[error("form-control serialization failed")]
    Serialization,
    #[error("form-control serialized output exceeds a finite limit")]
    OutputLimit,
}

impl FormControlError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "form_control_invalid_limit",
            Self::InputLimit => "form_control_input_limit",
            Self::InvalidJson => "form_control_invalid_json",
            Self::UnsupportedVersion => "form_control_unsupported_version",
            Self::InvalidIdentity => "form_control_invalid_identity",
            Self::InvalidDigest => "form_control_invalid_digest",
            Self::InvalidProperties => "form_control_invalid_properties",
            Self::InvalidNativeBinding => "form_control_invalid_native_binding",
            Self::InvalidInput => "form_control_invalid_input",
            Self::InvalidSelection => "form_control_invalid_selection",
            Self::InvalidRadioGroup => "form_control_invalid_radio_group",
            Self::InvalidTabOrder => "form_control_invalid_tab_order",
            Self::InvalidInsertionIndex => "form_control_invalid_insertion_index",
            Self::ControlNotFound => "form_control_not_found",
            Self::Protected => "form_control_protected",
            Self::Noop => "form_control_noop",
            Self::SourceStateDrift => "form_control_source_state_drift",
            Self::DocumentFlowDrift => "form_control_document_flow_drift",
            Self::PlanTampered => "form_control_plan_tampered",
            Self::Serialization => "form_control_serialization",
            Self::OutputLimit => "form_control_output_limit",
        }
    }
}

fn apply_operation(
    source: &FormDocumentState,
    operation: &FormControlOperation,
    limits: FormControlLimits,
) -> Result<FormDocumentState, FormControlError> {
    validate_document_state(source, limits)?;
    let mut target = source.clone();
    match operation {
        FormControlOperation::Insert {
            insertion_index,
            control,
        } => {
            if *insertion_index > source.controls.len() {
                return Err(FormControlError::InvalidInsertionIndex);
            }
            validate_control(control, limits)?;
            if source.controls.iter().any(|existing| {
                existing.identity.logical_control_id == control.identity.logical_control_id
                    || existing.identity.native_object_id == control.identity.native_object_id
                    || existing.anchor == control.anchor
                    || existing.common.name == control.common.name
            }) {
                return Err(FormControlError::InvalidIdentity);
            }
            target.controls.insert(*insertion_index, control.clone());
        }
        FormControlOperation::ReplaceProperties {
            target: identity,
            common,
            payload,
        } => {
            let index = exact_target_index(&target.controls, identity)?;
            if target.controls[index].shape_locked {
                return Err(FormControlError::Protected);
            }
            if payload.expected_native_binding() != target.controls[index].native_binding {
                return Err(FormControlError::InvalidNativeBinding);
            }
            if target.controls[index].payload.capability_id() != payload.capability_id() {
                return Err(FormControlError::InvalidProperties);
            }
            if target.controls[index].common == *common
                && target.controls[index].payload == *payload
            {
                return Err(FormControlError::Noop);
            }
            target.controls[index].common.clone_from(common);
            target.controls[index].payload.clone_from(payload);
        }
        FormControlOperation::SetTabOrder { assignments } => {
            if assignments.len() != source.controls.len() || assignments.is_empty() {
                return Err(FormControlError::InvalidTabOrder);
            }
            let mut seen_targets = BTreeSet::new();
            let mut enabled_orders = BTreeSet::new();
            for assignment in assignments {
                if !seen_targets.insert(&assignment.target)
                    || assignment.tab_stop != assignment.tab_order.is_some()
                {
                    return Err(FormControlError::InvalidTabOrder);
                }
                if let Some(order) = assignment.tab_order
                    && !enabled_orders.insert(order)
                {
                    return Err(FormControlError::InvalidTabOrder);
                }
                let index = exact_target_index(&target.controls, &assignment.target)?;
                if target.controls[index].shape_locked {
                    return Err(FormControlError::Protected);
                }
                target.controls[index].common.tab_stop = assignment.tab_stop;
                target.controls[index].common.tab_order = assignment.tab_order;
            }
            if seen_targets.len() != source.controls.len()
                || !source
                    .controls
                    .iter()
                    .all(|control| seen_targets.contains(&control.identity))
                || enabled_orders
                    .iter()
                    .copied()
                    .ne(0..u32::try_from(enabled_orders.len())
                        .map_err(|_| FormControlError::InvalidTabOrder)?)
            {
                return Err(FormControlError::InvalidTabOrder);
            }
        }
    }
    validate_document_state(&target, limits)?;
    if &target == source {
        return Err(FormControlError::Noop);
    }
    Ok(target)
}

fn exact_target_index(
    controls: &[FormControlState],
    identity: &FormControlIdentity,
) -> Result<usize, FormControlError> {
    let mut matches = controls
        .iter()
        .enumerate()
        .filter(|(_, control)| control.identity == *identity)
        .map(|(index, _)| index);
    let target = matches.next().ok_or(FormControlError::ControlNotFound)?;
    if matches.next().is_some() {
        return Err(FormControlError::ControlNotFound);
    }
    Ok(target)
}

fn validate_document_state(
    state: &FormDocumentState,
    limits: FormControlLimits,
) -> Result<(), FormControlError> {
    if state.schema_version != FORM_CONTROL_SCHEMA_VERSION
        || state.controls.len() > limits.0.controls
    {
        return Err(FormControlError::InvalidProperties);
    }
    for digest in [
        &state.non_form_content_sha256,
        &state.style_catalog_sha256,
        &state.border_catalog_sha256,
        &state.resource_inventory_sha256,
        &state.reference_inventory_sha256,
        &state.document_protection_sha256,
        &state.opaque_document_state_sha256,
    ] {
        require_digest(digest)?;
    }
    let mut logical_ids = BTreeSet::new();
    let mut native_ids = BTreeSet::new();
    let mut anchors = BTreeSet::new();
    let mut names = BTreeSet::new();
    let mut tab_orders = BTreeSet::new();
    let mut radio_groups: BTreeMap<&str, (bool, bool, bool, bool)> = BTreeMap::new();
    for control in &state.controls {
        validate_control(control, limits)?;
        if !logical_ids.insert(&control.identity.logical_control_id)
            || !native_ids.insert(control.identity.native_object_id)
            || !anchors.insert(&control.anchor)
            || !names.insert(control.common.name.as_str())
        {
            return Err(FormControlError::InvalidIdentity);
        }
        if let Some(order) = control.common.tab_order
            && !tab_orders.insert(order)
        {
            return Err(FormControlError::InvalidTabOrder);
        }
        if let FormControlPayload::Radio {
            value,
            default_value,
            radio_group_name,
            group_required,
            ..
        } = &control.payload
        {
            let selected = matches!(value, FormButtonValue::Checked);
            let default_selected = matches!(default_value, FormButtonValue::Checked);
            let group = radio_groups.entry(radio_group_name).or_insert((
                *group_required,
                false,
                false,
                false,
            ));
            if group.0 != *group_required || (group.1 && selected) || (group.2 && default_selected)
            {
                return Err(FormControlError::InvalidRadioGroup);
            }
            group.1 |= selected;
            group.2 |= default_selected;
            group.3 = true;
        }
    }
    if radio_groups
        .values()
        .any(|(required, selected, _, present)| *present && *required && !*selected)
    {
        return Err(FormControlError::InvalidRadioGroup);
    }
    Ok(())
}

fn validate_control(
    control: &FormControlState,
    limits: FormControlLimits,
) -> Result<(), FormControlError> {
    if control.identity.native_object_id == 0 {
        return Err(FormControlError::InvalidIdentity);
    }
    validate_common(&control.common, limits)?;
    validate_payload(&control.payload, limits)?;
    if control.native_binding != control.payload.expected_native_binding() {
        return Err(FormControlError::InvalidNativeBinding);
    }
    require_digest(&control.shape_state_sha256)?;
    require_digest(&control.opaque_native_payload_sha256)?;
    if control.opaque_properties.len() > limits.0.opaque_entries {
        return Err(FormControlError::InvalidProperties);
    }
    let mut keys = BTreeSet::new();
    for property in &control.opaque_properties {
        if !valid_token(&property.namespace, limits.0.name_bytes)
            || !valid_token(&property.name, limits.0.name_bytes)
            || require_digest(&property.value_sha256).is_err()
            || !keys.insert((&property.namespace, &property.name))
        {
            return Err(FormControlError::InvalidProperties);
        }
    }
    Ok(())
}

fn validate_common(
    common: &FormCommonProperties,
    limits: FormControlLimits,
) -> Result<(), FormControlError> {
    if !valid_name(&common.name, limits.0.name_bytes)
        || common
            .group_name
            .as_deref()
            .is_some_and(|value| !valid_name(value, limits.0.name_bytes))
        || common.fore_color_rgb > 0x00ff_ffff
        || common.back_color_rgb > 0x00ff_ffff
        || (!common.tab_stop && common.tab_order.is_some())
        || common
            .command_sha256
            .as_deref()
            .is_some_and(|value| require_digest(value).is_err())
    {
        return Err(FormControlError::InvalidProperties);
    }
    Ok(())
}

fn validate_payload(
    payload: &FormControlPayload,
    limits: FormControlLimits,
) -> Result<(), FormControlError> {
    match payload {
        FormControlPayload::Text { .. } => validate_text_payload(payload, limits),
        FormControlPayload::Checkbox { .. } => validate_checkbox_payload(payload, limits),
        FormControlPayload::Radio { .. } => validate_radio_payload(payload, limits),
        FormControlPayload::Combo { .. } => validate_combo_payload(payload, limits),
        FormControlPayload::List { .. } => validate_list_payload(payload, limits),
        FormControlPayload::Date { .. } => validate_date_payload(payload, limits),
    }
}

fn validate_text_payload(
    payload: &FormControlPayload,
    limits: FormControlLimits,
) -> Result<(), FormControlError> {
    let FormControlPayload::Text {
        value,
        default_value,
        validation,
        multi_line,
        password_character,
        native_max_length,
        scroll_bars,
        tab_key_behavior,
        number_only,
        ..
    } = payload
    else {
        return Err(FormControlError::InvalidInput);
    };
    validate_text_validation(validation)?;
    validate_external_digest(validation.external_validator_sha256.as_deref())?;
    if !valid_text(value, limits.0.text_bytes, true)
        || !valid_text(default_value, limits.0.text_bytes, true)
        || !text_satisfies(value, validation)
        || !text_satisfies(default_value, validation)
        || password_character
            .as_deref()
            .is_some_and(|text| !valid_text(text, 4, false) || text.chars().count() != 1)
        || native_max_length.is_some_and(|maximum| {
            maximum == 0
                || u32::try_from(value.chars().count()).map_or(true, |count| count > maximum)
                || u32::try_from(default_value.chars().count())
                    .map_or(true, |count| count > maximum)
        })
        || (!*multi_line && (value.contains(['\n', '\r']) || default_value.contains(['\n', '\r'])))
        || (*number_only
            && (!numeric_text(value, validation.required)
                || !numeric_text(default_value, validation.required)))
        || (!*multi_line && matches!(scroll_bars, FormScrollBars::Vertical | FormScrollBars::Both))
        || (!*multi_line && matches!(tab_key_behavior, FormTabKeyBehavior::InsertTab))
    {
        return Err(FormControlError::InvalidInput);
    }
    Ok(())
}

fn validate_checkbox_payload(
    payload: &FormControlPayload,
    limits: FormControlLimits,
) -> Result<(), FormControlError> {
    let FormControlPayload::Checkbox {
        value,
        default_value,
        must_be_checked,
        radio_group_name,
        tri_state,
        caption,
        ..
    } = payload
    else {
        return Err(FormControlError::InvalidInput);
    };
    if !valid_text(caption, limits.0.text_bytes, true)
        || radio_group_name
            .as_deref()
            .is_some_and(|name| !valid_name(name, limits.0.name_bytes))
        || (!*tri_state
            && (matches!(value, FormButtonValue::Indeterminate)
                || matches!(default_value, FormButtonValue::Indeterminate)))
        || (*must_be_checked && !matches!(value, FormButtonValue::Checked))
    {
        return Err(FormControlError::InvalidInput);
    }
    Ok(())
}

fn validate_radio_payload(
    payload: &FormControlPayload,
    limits: FormControlLimits,
) -> Result<(), FormControlError> {
    let FormControlPayload::Radio {
        caption,
        value,
        default_value,
        radio_group_name,
        tri_state,
        ..
    } = payload
    else {
        return Err(FormControlError::InvalidRadioGroup);
    };
    if !valid_text(caption, limits.0.text_bytes, true)
        || !valid_name(radio_group_name, limits.0.name_bytes)
        || (!*tri_state
            && (matches!(value, FormButtonValue::Indeterminate)
                || matches!(default_value, FormButtonValue::Indeterminate)))
    {
        return Err(FormControlError::InvalidRadioGroup);
    }
    Ok(())
}

fn validate_combo_payload(
    payload: &FormControlPayload,
    limits: FormControlLimits,
) -> Result<(), FormControlError> {
    let FormControlPayload::Combo {
        items,
        selected_value,
        default_selected_value,
        validation,
        list_box_rows,
        list_box_width_hwp_units,
        edit_enable,
    } = payload
    else {
        return Err(FormControlError::InvalidSelection);
    };
    validate_selection(
        items,
        selected_value.as_deref(),
        default_selected_value.as_deref(),
        validation,
        *edit_enable,
        limits,
    )?;
    if list_box_rows.is_some_and(|value| value == 0)
        || list_box_width_hwp_units.is_some_and(|value| value == 0)
    {
        return Err(FormControlError::InvalidProperties);
    }
    Ok(())
}

fn validate_list_payload(
    payload: &FormControlPayload,
    limits: FormControlLimits,
) -> Result<(), FormControlError> {
    let FormControlPayload::List {
        items,
        selected_value,
        default_selected_value,
        validation,
        item_height_hwp_units,
        top_index,
    } = payload
    else {
        return Err(FormControlError::InvalidSelection);
    };
    validate_selection(
        items,
        selected_value.as_deref(),
        default_selected_value.as_deref(),
        validation,
        false,
        limits,
    )?;
    if item_height_hwp_units.is_some_and(|value| value == 0)
        || (items.is_empty() && *top_index != 0)
        || (!items.is_empty()
            && usize::try_from(*top_index).map_or(true, |index| index >= items.len()))
    {
        return Err(FormControlError::InvalidSelection);
    }
    Ok(())
}

fn validate_date_payload(
    payload: &FormControlPayload,
    limits: FormControlLimits,
) -> Result<(), FormControlError> {
    let FormControlPayload::Date {
        value,
        default_value,
        format,
        locale,
        validation,
    } = payload
    else {
        return Err(FormControlError::InvalidInput);
    };
    validate_external_digest(validation.external_validator_sha256.as_deref())?;
    if !valid_text(format, limits.0.name_bytes, false)
        || !valid_locale(locale, limits.0.name_bytes)
        || value.as_deref().is_some_and(|date| !valid_date(date))
        || default_value
            .as_deref()
            .is_some_and(|date| !valid_date(date))
        || validation
            .earliest
            .as_deref()
            .is_some_and(|date| !valid_date(date))
        || validation
            .latest
            .as_deref()
            .is_some_and(|date| !valid_date(date))
        || validation
            .earliest
            .as_ref()
            .zip(validation.latest.as_ref())
            .is_some_and(|(earliest, latest)| earliest > latest)
        || validation.required && value.is_none()
        || value
            .as_deref()
            .is_some_and(|date| !date_in_range(date, validation))
        || default_value
            .as_deref()
            .is_some_and(|date| !date_in_range(date, validation))
    {
        return Err(FormControlError::InvalidInput);
    }
    Ok(())
}

fn validate_text_validation(validation: &FormTextValidation) -> Result<(), FormControlError> {
    if validation
        .maximum_characters
        .is_some_and(|maximum| maximum < validation.minimum_characters)
    {
        return Err(FormControlError::InvalidInput);
    }
    Ok(())
}

fn text_satisfies(value: &str, validation: &FormTextValidation) -> bool {
    let Ok(count) = u32::try_from(value.chars().count()) else {
        return false;
    };
    (!validation.required || !value.is_empty())
        && count >= validation.minimum_characters
        && validation
            .maximum_characters
            .is_none_or(|maximum| count <= maximum)
}

fn numeric_text(value: &str, required: bool) -> bool {
    (!required && value.is_empty()) || (!value.is_empty() && value.chars().all(char::is_numeric))
}

fn validate_selection(
    items: &[FormListItem],
    selected: Option<&str>,
    default_selected: Option<&str>,
    validation: &FormSelectionValidation,
    custom_values: bool,
    limits: FormControlLimits,
) -> Result<(), FormControlError> {
    validate_external_digest(validation.external_validator_sha256.as_deref())?;
    if items.len() > limits.0.items_per_control || (validation.required && selected.is_none()) {
        return Err(FormControlError::InvalidSelection);
    }
    let mut values = BTreeSet::new();
    for item in items {
        if !valid_text(&item.display_text, limits.0.text_bytes, true)
            || !valid_text(&item.value, limits.0.text_bytes, false)
            || !values.insert(item.value.as_str())
        {
            return Err(FormControlError::InvalidSelection);
        }
    }
    for value in [selected, default_selected].into_iter().flatten() {
        if !valid_text(value, limits.0.text_bytes, false)
            || (!custom_values && !values.contains(value))
        {
            return Err(FormControlError::InvalidSelection);
        }
    }
    Ok(())
}

fn date_in_range(value: &str, validation: &FormDateValidation) -> bool {
    validation
        .earliest
        .as_deref()
        .is_none_or(|earliest| value >= earliest)
        && validation
            .latest
            .as_deref()
            .is_none_or(|latest| value <= latest)
}

fn valid_date(value: &str) -> bool {
    let bytes = value.as_bytes();
    if bytes.len() != 10
        || bytes[4] != b'-'
        || bytes[7] != b'-'
        || bytes
            .iter()
            .enumerate()
            .any(|(index, byte)| index != 4 && index != 7 && !byte.is_ascii_digit())
    {
        return false;
    }
    let Ok(year) = value[0..4].parse::<u32>() else {
        return false;
    };
    let Ok(month) = value[5..7].parse::<u32>() else {
        return false;
    };
    let Ok(day) = value[8..10].parse::<u32>() else {
        return false;
    };
    let leap = year.is_multiple_of(4) && (!year.is_multiple_of(100) || year.is_multiple_of(400));
    let maximum = match month {
        1 | 3 | 5 | 7 | 8 | 10 | 12 => 31,
        4 | 6 | 9 | 11 => 30,
        2 if leap => 29,
        2 => 28,
        _ => return false,
    };
    year != 0 && (1..=maximum).contains(&day)
}

fn validate_external_digest(value: Option<&str>) -> Result<(), FormControlError> {
    if value.is_some_and(|digest| require_digest(digest).is_err()) {
        return Err(FormControlError::InvalidInput);
    }
    Ok(())
}

fn valid_name(value: &str, max_bytes: usize) -> bool {
    !value.is_empty()
        && value.len() <= max_bytes
        && !value.chars().any(|character| {
            character == '\0' || character == '\\' || character == '/' || character.is_control()
        })
}

fn valid_locale(value: &str, max_bytes: usize) -> bool {
    !value.is_empty()
        && value.len() <= max_bytes
        && value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || byte == b'-')
}

fn valid_token(value: &str, max_bytes: usize) -> bool {
    !value.is_empty()
        && value.len() <= max_bytes
        && value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'_' | b'-' | b'.'))
}

fn valid_text(value: &str, max_bytes: usize, allow_empty: bool) -> bool {
    (allow_empty || !value.is_empty())
        && value.len() <= max_bytes
        && !value.chars().any(|character| {
            character == '\0'
                || (character.is_control() && !matches!(character, '\n' | '\r' | '\t'))
        })
}

fn require_digest(value: &str) -> Result<(), FormControlError> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(FormControlError::InvalidDigest);
    }
    Ok(())
}

fn plan_binding_sha256(
    plan: &FormControlPlan,
    limits: FormControlLimits,
) -> Result<String, FormControlError> {
    #[derive(Serialize)]
    struct Binding<'a> {
        schema_version: &'static str,
        capability_id: &'static str,
        request_id: &'a LogicalId,
        source_state_sha256: &'a str,
        target_state_sha256: &'a str,
        source_document_flow_sha256: &'a str,
        target_document_flow_sha256: &'a str,
        operation: &'a FormControlOperation,
    }
    let binding = Binding {
        schema_version: plan.schema_version,
        capability_id: plan.capability_id,
        request_id: &plan.request_id,
        source_state_sha256: &plan.source_state_sha256,
        target_state_sha256: &plan.target_state_sha256,
        source_document_flow_sha256: &plan.source_document_flow_sha256,
        target_document_flow_sha256: &plan.target_document_flow_sha256,
        operation: &plan.operation,
    };
    Ok(hex(
        Sha256::digest(serialize_bounded(&binding, limits)?).into()
    ))
}

fn serialize_bounded<T: Serialize>(
    value: &T,
    limits: FormControlLimits,
) -> Result<Vec<u8>, FormControlError> {
    let bytes = serde_json::to_vec(value).map_err(|_| FormControlError::Serialization)?;
    if bytes.len() > limits.0.output_bytes {
        return Err(FormControlError::OutputLimit);
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

fn reject_duplicate_json_keys(bytes: &[u8]) -> Result<(), FormControlError> {
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
        .map_err(|_| FormControlError::InvalidJson)?;
    deserializer
        .end()
        .map_err(|_| FormControlError::InvalidJson)
}

#[cfg(test)]
#[allow(clippy::expect_used)] // Private setup keeps sealed-plan tampering local.
mod private_tests {
    use super::*;

    const DIGEST: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";

    fn limits() -> FormControlLimits {
        FormControlLimits::new(FormControlLimitConfig::default()).expect("limits")
    }

    fn common() -> FormCommonProperties {
        FormCommonProperties {
            name: "private-control".to_owned(),
            fore_color_rgb: 0,
            back_color_rgb: 0x00ff_ffff,
            group_name: None,
            tab_stop: true,
            tab_order: None,
            editable: true,
            enabled: true,
            border_type_id_ref: 0,
            draw_frame: true,
            printable: true,
            command_sha256: None,
            character: FormCharacterProperties {
                char_pr_id_ref: 0,
                follow_context: false,
                auto_size: false,
                word_wrap: false,
            },
        }
    }

    fn state() -> FormDocumentState {
        FormDocumentState::from_draft(
            FormDocumentStateDraft {
                schema_version: FORM_CONTROL_SCHEMA_VERSION.to_owned(),
                controls: Vec::new(),
                non_form_content_sha256: DIGEST.to_owned(),
                style_catalog_sha256: DIGEST.to_owned(),
                border_catalog_sha256: DIGEST.to_owned(),
                resource_inventory_sha256: DIGEST.to_owned(),
                reference_inventory_sha256: DIGEST.to_owned(),
                document_protection_sha256: DIGEST.to_owned(),
                opaque_document_state_sha256: DIGEST.to_owned(),
            },
            limits(),
        )
        .expect("state")
    }

    #[test]
    fn private_plan_tampering_is_rejected() {
        let source = state();
        let control = FormControlState {
            identity: FormControlIdentity {
                logical_control_id: LogicalId::parse("form-1").expect("id"),
                native_object_id: 1,
            },
            anchor: FormControlAnchor {
                paragraph_id: LogicalId::parse("paragraph-1").expect("id"),
                run_ordinal: 0,
                inline_ordinal: 0,
            },
            native_binding: FormNativeBinding::Exact {
                tag: NativeFormTag::Edit,
            },
            common: common(),
            payload: FormControlPayload::Text {
                value: String::new(),
                default_value: String::new(),
                validation: FormTextValidation {
                    required: false,
                    minimum_characters: 0,
                    maximum_characters: None,
                    external_validator_sha256: None,
                },
                multi_line: false,
                password_character: None,
                native_max_length: None,
                scroll_bars: FormScrollBars::None,
                tab_key_behavior: FormTabKeyBehavior::NextObject,
                number_only: false,
                read_only: false,
                alignment: FormTextAlignment::Left,
            },
            shape_locked: false,
            shape_state_sha256: DIGEST.to_owned(),
            opaque_native_payload_sha256: DIGEST.to_owned(),
            opaque_properties: Vec::new(),
        };
        let request = FormControlRequest::from_draft(
            FormControlRequestDraft {
                schema_version: FORM_CONTROL_SCHEMA_VERSION.to_owned(),
                request_id: LogicalId::parse("request-1").expect("id"),
                expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
                expected_document_flow_sha256: DIGEST.to_owned(),
                target_document_flow_sha256: DIGEST.to_owned(),
                operation: FormControlOperation::Insert {
                    insertion_index: 0,
                    control,
                },
            },
            &source,
            DIGEST,
            limits(),
        )
        .expect("request");
        let mut plan = FormControlBuilder::plan(&source, &request, DIGEST, limits()).expect("plan");
        plan.capability_id = "ref.form_properties";
        assert_eq!(
            FormControlBuilder::build(&plan, &source, DIGEST, limits()),
            Err(FormControlError::PlanTampered)
        );
    }
}
