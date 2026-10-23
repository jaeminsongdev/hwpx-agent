//! Atomic value-only input under explicit caller policy; no native/security proof.
//! Kept separate from the immutable form-control/v1 property transition contract.
use std::{collections::BTreeSet, fmt};

use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{
    FormButtonValue, FormControlIdentity, FormControlLimits, FormControlPayload, FormControlState,
    FormDocumentState, FormDocumentStateDraft, LogicalId,
};

pub const FORM_INPUT_SCHEMA_VERSION: &str = "hwpx-agent.form-input.atomic-values/v1";

/// Explicit caller decision bound to the complete current protection digest.
/// This is NOT a native protection probe, credential, permission or trust proof.
#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FormInputAccessPolicy {
    pub document_protection_sha256: String,
    pub input_allowed: bool,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum FormInputValue {
    Text { value: String },
    Checkbox { value: FormButtonValue },
    Radio { value: FormButtonValue },
    Combo { selected_value: Option<String> },
    List { selected_value: Option<String> },
    Date { value: Option<String> },
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FormInputAssignment {
    pub target: FormControlIdentity,
    pub value: FormInputValue,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum FormInputOperation {
    SetValues {
        assignments: Vec<FormInputAssignment>,
    },
    ResetDefaults {
        targets: Vec<FormControlIdentity>,
    },
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FormInputRequestDraft {
    pub schema_version: String,
    pub request_id: LogicalId,
    pub expected_source_state_sha256: String,
    pub expected_document_flow_sha256: String,
    pub access: FormInputAccessPolicy,
    pub operation: FormInputOperation,
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct FormInputRequest {
    draft: FormInputRequestDraft,
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct FormInputPlan {
    profile: &'static str,
    request: FormInputRequest,
    source: FormDocumentState,
    target: FormDocumentState,
    source_state_sha256: String,
    target_state_sha256: String,
    document_flow_sha256: String,
    changed_controls: usize,
    plan_sha256: String,
}

#[derive(Clone, Copy, Eq, PartialEq, Serialize, Debug)]
#[serde(rename_all = "snake_case")]
pub enum FormInputQualification {
    CallerPolicyOnlyNativeProtectionExternalValidationAndOutputUnqualified,
}

#[derive(Clone, Eq, PartialEq, Serialize, Debug)]
pub struct FormInputReceipt {
    pub profile: &'static str,
    pub source_state_sha256: String,
    pub target_state_sha256: String,
    pub document_flow_sha256: String,
    pub plan_sha256: String,
    pub changed_controls: usize,
    pub qualification: FormInputQualification,
}

#[derive(Clone, Eq, PartialEq)]
pub struct FormInputResult {
    pub state: FormDocumentState,
    pub receipt: FormInputReceipt,
}

macro_rules! redacted_debug {
    ($($name:ty),+ $(,)?) => {$ (
        impl fmt::Debug for $name {
            fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
                f.write_str(concat!(stringify!($name), "(<redacted>)"))
            }
        }
    )+ };
}
redacted_debug!(
    FormInputAccessPolicy,
    FormInputValue,
    FormInputAssignment,
    FormInputOperation,
    FormInputRequestDraft,
    FormInputRequest,
    FormInputPlan,
    FormInputResult
);

#[derive(Debug, Error, Eq, PartialEq)]
pub enum FormInputError {
    #[error("FORM_INPUT_LIMIT")]
    Limit,
    #[error("FORM_INPUT_SCHEMA_REJECTED")]
    Schema,
    #[error("FORM_INPUT_JSON_REJECTED")]
    Json,
    #[error("FORM_INPUT_SOURCE_OR_FLOW_DRIFT")]
    Drift,
    #[error("FORM_INPUT_CALLER_ACCESS_REJECTED")]
    Access,
    #[error("FORM_INPUT_TARGET_MISSING_OR_DUPLICATED")]
    Target,
    #[error("FORM_INPUT_TARGET_PROTECTED")]
    Protected,
    #[error("FORM_INPUT_VALUE_KIND_MISMATCH")]
    Kind,
    #[error("FORM_INPUT_VALIDATION_REJECTED")]
    Validation,
    #[error("FORM_INPUT_EXTERNAL_VALIDATION_UNQUALIFIED")]
    ExternalValidationUnqualified,
    #[error("FORM_INPUT_NOOP")]
    Noop,
    #[error("FORM_INPUT_PLAN_TAMPERED")]
    Plan,
}

impl FormInputRequest {
    /// Validates an atomic operation, all current bindings and caller access.
    /// # Errors
    /// Rejects drift, protection, missing/duplicate targets, kinds or validation.
    pub fn from_draft(
        draft: FormInputRequestDraft,
        current: &FormDocumentState,
        flow: &str,
        limits: FormControlLimits,
    ) -> Result<Self, FormInputError> {
        if draft.schema_version != FORM_INPUT_SCHEMA_VERSION {
            return Err(FormInputError::Schema);
        }
        digest(flow)?;
        digest(&draft.expected_source_state_sha256)?;
        digest(&draft.expected_document_flow_sha256)?;
        if draft.expected_source_state_sha256 != state_sha(current, limits)?
            || draft.expected_document_flow_sha256 != flow
        {
            return Err(FormInputError::Drift);
        }
        let request = Self { draft };
        // Typed callers must respect request limits as strictly as JSON callers.
        let _ = bounded(&request.draft, limits.config().input_bytes)?;
        let _ = apply(
            current,
            &request.draft.access,
            &request.draft.operation,
            limits,
        )?;
        Ok(request)
    }

    /// Strict duplicate-free and bounded JSON; every unknown field rejects.
    /// # Errors
    /// Rejects malformed/coerced/unknown/duplicate JSON and invalid operations.
    pub fn from_json(
        bytes: &[u8],
        current: &FormDocumentState,
        flow: &str,
        limits: FormControlLimits,
    ) -> Result<Self, FormInputError> {
        if bytes.is_empty() || bytes.len() > limits.config().input_bytes {
            return Err(FormInputError::Limit);
        }
        let mut reader = serde_json::Deserializer::from_slice(bytes);
        let _ = UniqueJson::deserialize(&mut reader).map_err(|_| FormInputError::Json)?;
        reader.end().map_err(|_| FormInputError::Json)?;
        let draft = serde_json::from_slice(bytes).map_err(|_| FormInputError::Json)?;
        Self::from_draft(draft, current, flow, limits)
    }

    /// Serializes the caller request, not a public evidence artifact.
    /// # Errors
    /// Rejects serialization or the configured finite input limit.
    pub fn canonical_json(&self, limits: FormControlLimits) -> Result<Vec<u8>, FormInputError> {
        bounded(&self.draft, limits.config().input_bytes)
    }
}

impl FormInputPlan {
    #[must_use]
    pub const fn source_state(&self) -> &FormDocumentState {
        &self.source
    }
    #[must_use]
    pub const fn target_state(&self) -> &FormDocumentState {
        &self.target
    }
    #[must_use]
    pub fn plan_sha256(&self) -> &str {
        &self.plan_sha256
    }
    /// Serializes a private sealed plan; contains document values, not public logs.
    /// # Errors
    /// Rejects serialization or the finite configured output bound.
    pub fn canonical_json(&self, limits: FormControlLimits) -> Result<Vec<u8>, FormInputError> {
        bounded(self, limits.config().output_bytes)
    }
}

#[derive(Debug)]
pub struct FormInputBuilder;
impl FormInputBuilder {
    /// Seals one full-document atomic value-only operation.
    /// # Errors
    /// Rejects state/flow/access/validation drift or a finite plan limit.
    pub fn plan(
        source: &FormDocumentState,
        request: &FormInputRequest,
        flow: &str,
        limits: FormControlLimits,
    ) -> Result<FormInputPlan, FormInputError> {
        let fresh = FormInputRequest::from_draft(request.draft.clone(), source, flow, limits)?;
        let target = apply(source, &fresh.draft.access, &fresh.draft.operation, limits)?;
        let changed_controls = source
            .controls()
            .iter()
            .zip(target.controls())
            .filter(|(a, b)| a != b)
            .count();
        let mut plan = FormInputPlan {
            profile: FORM_INPUT_SCHEMA_VERSION,
            request: fresh,
            source: source.clone(),
            source_state_sha256: state_sha(source, limits)?,
            target_state_sha256: state_sha(&target, limits)?,
            target,
            document_flow_sha256: flow.into(),
            changed_controls,
            plan_sha256: String::new(),
        };
        plan.plan_sha256 = seal(&plan, limits)?;
        let _ = plan.canonical_json(limits)?;
        Ok(plan)
    }

    /// Independently recomputes the complete atomic result before returning it.
    /// # Errors
    /// Rejects source/flow/access drift, tampering or changed target validation.
    pub fn build(
        plan: &FormInputPlan,
        current: &FormDocumentState,
        flow: &str,
        current_access: &FormInputAccessPolicy,
        limits: FormControlLimits,
    ) -> Result<FormInputResult, FormInputError> {
        if plan.profile != FORM_INPUT_SCHEMA_VERSION || seal(plan, limits)? != plan.plan_sha256 {
            return Err(FormInputError::Plan);
        }
        if current_access != &plan.request.draft.access || !current_access.input_allowed {
            return Err(FormInputError::Access);
        }
        if current != &plan.source
            || state_sha(current, limits)? != plan.source_state_sha256
            || flow != plan.document_flow_sha256
        {
            return Err(FormInputError::Drift);
        }
        let fresh = Self::plan(current, &plan.request, flow, limits)?;
        if &fresh != plan {
            return Err(FormInputError::Plan);
        }
        let receipt = FormInputReceipt {
            profile: FORM_INPUT_SCHEMA_VERSION,
            source_state_sha256: plan.source_state_sha256.clone(),
            target_state_sha256: plan.target_state_sha256.clone(),
            document_flow_sha256: plan.document_flow_sha256.clone(),
            plan_sha256: plan.plan_sha256.clone(),
            changed_controls: plan.changed_controls,
            qualification: FormInputQualification::CallerPolicyOnlyNativeProtectionExternalValidationAndOutputUnqualified,
        };
        let _ = bounded(&receipt, limits.config().output_bytes)?;
        Ok(FormInputResult {
            state: fresh.target,
            receipt,
        })
    }
}

fn apply(
    source: &FormDocumentState,
    access: &FormInputAccessPolicy,
    operation: &FormInputOperation,
    limits: FormControlLimits,
) -> Result<FormDocumentState, FormInputError> {
    let mut draft: FormDocumentStateDraft = serde_json::from_slice(
        &source
            .canonical_json(limits)
            .map_err(|_| FormInputError::Limit)?,
    )
    .map_err(|_| FormInputError::Validation)?;
    digest(&access.document_protection_sha256)?;
    if !access.input_allowed
        || access.document_protection_sha256 != draft.document_protection_sha256
    {
        return Err(FormInputError::Access);
    }
    let count = match operation {
        FormInputOperation::SetValues { assignments } => assignments.len(),
        FormInputOperation::ResetDefaults { targets } => targets.len(),
    };
    if count == 0 || count > limits.config().controls || count > draft.controls.len() {
        return Err(FormInputError::Target);
    }
    let mut seen = BTreeSet::new();
    match operation {
        FormInputOperation::SetValues { assignments } => {
            for assignment in assignments {
                let control = target(&mut draft.controls, &assignment.target, &mut seen)?;
                admit(control)?;
                set_value(&mut control.payload, &assignment.value)?;
            }
        }
        FormInputOperation::ResetDefaults { targets } => {
            for identity in targets {
                let control = target(&mut draft.controls, identity, &mut seen)?;
                admit(control)?;
                let value = default_value(&control.payload);
                set_value(&mut control.payload, &value)?;
            }
        }
    }
    // Validate ONCE after the complete group mutation. Never expose an interim
    // radio group with zero/two checked members or partially applied input.
    let result =
        FormDocumentState::from_draft(draft, limits).map_err(|_| FormInputError::Validation)?;
    if &result == source {
        return Err(FormInputError::Noop);
    }
    Ok(result)
}

fn target<'a>(
    controls: &'a mut [FormControlState],
    identity: &FormControlIdentity,
    seen: &mut BTreeSet<FormControlIdentity>,
) -> Result<&'a mut FormControlState, FormInputError> {
    if !seen.insert(identity.clone()) {
        return Err(FormInputError::Target);
    }
    controls
        .iter_mut()
        .find(|c| c.identity == *identity)
        .ok_or(FormInputError::Target)
}

fn admit(control: &FormControlState) -> Result<(), FormInputError> {
    if control.shape_locked
        || !control.common.enabled
        || !control.common.editable
        || matches!(
            &control.payload,
            FormControlPayload::Text {
                read_only: true,
                ..
            }
        )
    {
        return Err(FormInputError::Protected);
    }
    let external = match &control.payload {
        FormControlPayload::Text { validation, .. } => &validation.external_validator_sha256,
        FormControlPayload::Combo { validation, .. }
        | FormControlPayload::List { validation, .. } => &validation.external_validator_sha256,
        FormControlPayload::Date { validation, .. } => &validation.external_validator_sha256,
        FormControlPayload::Checkbox { .. } | FormControlPayload::Radio { .. } => return Ok(()),
    };
    if external.is_some() {
        return Err(FormInputError::ExternalValidationUnqualified);
    }
    Ok(())
}

fn set_value(
    payload: &mut FormControlPayload,
    input: &FormInputValue,
) -> Result<(), FormInputError> {
    match (payload, input) {
        (FormControlPayload::Text { value, .. }, FormInputValue::Text { value: new }) => {
            value.clone_from(new);
        }
        (FormControlPayload::Checkbox { value, .. }, FormInputValue::Checkbox { value: new })
        | (FormControlPayload::Radio { value, .. }, FormInputValue::Radio { value: new }) => {
            *value = *new;
        }
        (
            FormControlPayload::Combo { selected_value, .. },
            FormInputValue::Combo {
                selected_value: new,
            },
        )
        | (
            FormControlPayload::List { selected_value, .. },
            FormInputValue::List {
                selected_value: new,
            },
        ) => selected_value.clone_from(new),
        (FormControlPayload::Date { value, .. }, FormInputValue::Date { value: new }) => {
            value.clone_from(new);
        }
        _ => return Err(FormInputError::Kind),
    }
    Ok(())
}

fn default_value(payload: &FormControlPayload) -> FormInputValue {
    match payload {
        FormControlPayload::Text { default_value, .. } => FormInputValue::Text {
            value: default_value.clone(),
        },
        FormControlPayload::Checkbox { default_value, .. } => FormInputValue::Checkbox {
            value: *default_value,
        },
        FormControlPayload::Radio { default_value, .. } => FormInputValue::Radio {
            value: *default_value,
        },
        FormControlPayload::Combo {
            default_selected_value,
            ..
        } => FormInputValue::Combo {
            selected_value: default_selected_value.clone(),
        },
        FormControlPayload::List {
            default_selected_value,
            ..
        } => FormInputValue::List {
            selected_value: default_selected_value.clone(),
        },
        FormControlPayload::Date { default_value, .. } => FormInputValue::Date {
            value: default_value.clone(),
        },
    }
}

fn state_sha(
    state: &FormDocumentState,
    limits: FormControlLimits,
) -> Result<String, FormInputError> {
    state
        .canonical_sha256(limits)
        .map_err(|_| FormInputError::Limit)
}
fn seal(plan: &FormInputPlan, limits: FormControlLimits) -> Result<String, FormInputError> {
    let mut input = plan.clone();
    input.plan_sha256.clear();
    Ok(hex(&Sha256::digest(bounded(
        &input,
        limits.config().output_bytes,
    )?)))
}
fn digest(value: &str) -> Result<(), FormInputError> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
    {
        return Err(FormInputError::Drift);
    }
    Ok(())
}
fn bounded<T: Serialize>(value: &T, maximum: usize) -> Result<Vec<u8>, FormInputError> {
    let mut output = LimitedJson {
        bytes: Vec::new(),
        maximum,
    };
    serde_json::to_writer(&mut output, value).map_err(|_| FormInputError::Limit)?;
    Ok(output.bytes)
}
struct LimitedJson {
    bytes: Vec<u8>,
    maximum: usize,
}
impl std::io::Write for LimitedJson {
    fn write(&mut self, bytes: &[u8]) -> std::io::Result<usize> {
        let length = self
            .bytes
            .len()
            .checked_add(bytes.len())
            .ok_or_else(|| std::io::Error::other("limit"))?;
        if length > self.maximum {
            return Err(std::io::Error::other("limit"));
        }
        self.bytes
            .try_reserve(bytes.len())
            .map_err(|_| std::io::Error::other("allocation"))?;
        self.bytes.extend_from_slice(bytes);
        Ok(bytes.len())
    }
    fn flush(&mut self) -> std::io::Result<()> {
        Ok(())
    }
}
fn hex(raw: &[u8]) -> String {
    const HEX: &[u8; 16] = b"0123456789abcdef";
    raw.iter()
        .flat_map(|b| {
            [
                char::from(HEX[usize::from(b >> 4)]),
                char::from(HEX[usize::from(b & 15)]),
            ]
        })
        .collect()
}

// Recursive duplicate-key guard, including ignored/nested objects. No raw
// document value or parser error is attached to the returned public error.
struct UniqueJson;
impl<'de> Deserialize<'de> for UniqueJson {
    fn deserialize<D: serde::Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        struct UniqueVisitor;
        impl<'de> serde::de::Visitor<'de> for UniqueVisitor {
            type Value = UniqueJson;
            fn expecting(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
                f.write_str("unique bounded JSON")
            }
            fn visit_map<A: serde::de::MapAccess<'de>>(
                self,
                mut map: A,
            ) -> Result<Self::Value, A::Error> {
                let mut keys = BTreeSet::new();
                while let Some(key) = map.next_key::<String>()? {
                    if !keys.insert(key) {
                        return Err(serde::de::Error::custom("duplicate key"));
                    }
                    let _ = map.next_value::<UniqueJson>()?;
                }
                Ok(UniqueJson)
            }
            fn visit_seq<A: serde::de::SeqAccess<'de>>(
                self,
                mut seq: A,
            ) -> Result<Self::Value, A::Error> {
                while seq.next_element::<UniqueJson>()?.is_some() {}
                Ok(UniqueJson)
            }
            fn visit_bool<E: serde::de::Error>(self, _: bool) -> Result<Self::Value, E> {
                Ok(UniqueJson)
            }
            fn visit_i64<E: serde::de::Error>(self, _: i64) -> Result<Self::Value, E> {
                Ok(UniqueJson)
            }
            fn visit_u64<E: serde::de::Error>(self, _: u64) -> Result<Self::Value, E> {
                Ok(UniqueJson)
            }
            fn visit_f64<E: serde::de::Error>(self, _: f64) -> Result<Self::Value, E> {
                Ok(UniqueJson)
            }
            fn visit_str<E: serde::de::Error>(self, _: &str) -> Result<Self::Value, E> {
                Ok(UniqueJson)
            }
            fn visit_unit<E: serde::de::Error>(self) -> Result<Self::Value, E> {
                Ok(UniqueJson)
            }
        }
        deserializer.deserialize_any(UniqueVisitor)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    fn fixture()
    -> Result<(FormDocumentState, FormInputRequest, FormControlLimits), Box<dyn std::error::Error>>
    {
        use crate::{
            FormCharacterProperties, FormCommonProperties, FormControlAnchor,
            FormControlLimitConfig, FormNativeBinding, FormScrollBars, FormTabKeyBehavior,
            FormTextAlignment, FormTextValidation, NativeFormTag,
        };
        let limits = FormControlLimits::new(FormControlLimitConfig::default())?;
        let identity = FormControlIdentity {
            logical_control_id: LogicalId::parse("control-1")?,
            native_object_id: 1,
        };
        let state = FormDocumentState::from_draft(
            FormDocumentStateDraft {
                schema_version: crate::FORM_CONTROL_SCHEMA_VERSION.into(),
                controls: vec![FormControlState {
                    identity: identity.clone(),
                    anchor: FormControlAnchor {
                        paragraph_id: LogicalId::parse("p-1")?,
                        run_ordinal: 0,
                        inline_ordinal: 0,
                    },
                    native_binding: FormNativeBinding::Exact {
                        tag: NativeFormTag::Edit,
                    },
                    common: FormCommonProperties {
                        name: "redacted".into(),
                        fore_color_rgb: 0,
                        back_color_rgb: 0,
                        group_name: None,
                        tab_stop: false,
                        tab_order: None,
                        editable: true,
                        enabled: true,
                        border_type_id_ref: 0,
                        draw_frame: false,
                        printable: true,
                        command_sha256: None,
                        character: FormCharacterProperties {
                            char_pr_id_ref: 0,
                            follow_context: false,
                            auto_size: false,
                            word_wrap: true,
                        },
                    },
                    payload: FormControlPayload::Text {
                        value: "old".into(),
                        default_value: "default".into(),
                        validation: FormTextValidation {
                            required: false,
                            minimum_characters: 0,
                            maximum_characters: None,
                            external_validator_sha256: None,
                        },
                        multi_line: true,
                        password_character: None,
                        native_max_length: None,
                        scroll_bars: FormScrollBars::None,
                        tab_key_behavior: FormTabKeyBehavior::NextObject,
                        number_only: false,
                        read_only: false,
                        alignment: FormTextAlignment::Left,
                    },
                    shape_locked: false,
                    shape_state_sha256: "a".repeat(64),
                    opaque_native_payload_sha256: "a".repeat(64),
                    opaque_properties: vec![],
                }],
                non_form_content_sha256: "a".repeat(64),
                style_catalog_sha256: "a".repeat(64),
                border_catalog_sha256: "a".repeat(64),
                resource_inventory_sha256: "a".repeat(64),
                reference_inventory_sha256: "a".repeat(64),
                document_protection_sha256: "a".repeat(64),
                opaque_document_state_sha256: "a".repeat(64),
            },
            limits,
        )?;
        let request = FormInputRequest::from_draft(
            FormInputRequestDraft {
                schema_version: FORM_INPUT_SCHEMA_VERSION.into(),
                request_id: LogicalId::parse("input-1")?,
                expected_source_state_sha256: state_sha(&state, limits)?,
                expected_document_flow_sha256: "a".repeat(64),
                access: FormInputAccessPolicy {
                    document_protection_sha256: "a".repeat(64),
                    input_allowed: true,
                },
                operation: FormInputOperation::SetValues {
                    assignments: vec![FormInputAssignment {
                        target: identity,
                        value: FormInputValue::Text {
                            value: "new".into(),
                        },
                    }],
                },
            },
            &state,
            &"a".repeat(64),
            limits,
        )?;
        Ok((state, request, limits))
    }
    #[test]
    fn private_seal_fields_cannot_be_forged() -> Result<(), Box<dyn std::error::Error>> {
        let (source, request, limits) = fixture()?;
        let flow = &"a".repeat(64);
        let plan = super::FormInputBuilder::plan(&source, &request, flow, limits)?;
        let mut changed = plan.clone();
        changed.target_state_sha256 = "0".repeat(64);
        assert_eq!(
            super::FormInputBuilder::build(&changed, &source, flow, &request.draft.access, limits),
            Err(super::FormInputError::Plan)
        );
        let mut changed = plan.clone();
        changed.changed_controls += 1;
        assert_eq!(
            super::FormInputBuilder::build(&changed, &source, flow, &request.draft.access, limits),
            Err(super::FormInputError::Plan)
        );
        let mut changed = plan;
        changed.request.draft.access.input_allowed = false;
        assert_eq!(
            super::FormInputBuilder::build(&changed, &source, flow, &request.draft.access, limits),
            Err(super::FormInputError::Plan)
        );
        Ok(())
    }

    #[test]
    fn private_bounded_serializer_rejects_before_over_limit_allocation()
    -> Result<(), Box<dyn std::error::Error>> {
        use std::io::Write as _;
        let mut output = LimitedJson {
            bytes: Vec::new(),
            maximum: 2,
        };
        output.write_all(b"ok")?;
        let capacity = output.bytes.capacity();
        assert!(output.write_all(&[0; 1024]).is_err());
        assert_eq!(output.bytes, b"ok");
        assert_eq!(output.bytes.capacity(), capacity);
        assert_eq!(bounded(&"large", 2), Err(FormInputError::Limit));
        Ok(())
    }
}
