use std::collections::BTreeMap;
use std::fmt;

use domain_ir::{
    OBJECT_SPECIAL_SCHEMA_VERSION, ObjectIdentity, ObjectSpecialBuilder, ObjectSpecialError,
    ObjectSpecialLimits, ObjectSpecialOperation, ObjectSpecialPlan, SpecialObjectKind,
    SpecialObjectPayload, SpecialObjectState, StaticFormControlKind, StaticFormPayload,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::preserving_xml::{
    PreservingXmlDocument, PreservingXmlError, XmlAttributeToken, XmlByteSpan, XmlElementToken,
};

pub const OBJECT_FORM_INSERT_HWPX_PROFILE_ID: &str =
    "hwpx-agent.object-form-insert-hwpx.hwpml-2011-static-edit/v1";
pub const OBJECT_FORM_INSERT_STATIC_EDIT_PROFILE_SHA256: &str =
    "44c66873c42bde5824b77b7110506d8f3c4c823a47ba877b4fa39129e3a385a6";

const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ObjectFormInsertHwpxLimitConfig {
    pub section_bytes: usize,
    pub output_bytes: usize,
    pub elements: usize,
    pub objects: usize,
    pub text_bytes: usize,
    pub attributes_per_object: usize,
    pub plan_bytes: usize,
}

impl Default for ObjectFormInsertHwpxLimitConfig {
    fn default() -> Self {
        Self {
            section_bytes: 32 * 1024 * 1024,
            output_bytes: 32 * 1024 * 1024,
            elements: 1_000_000,
            objects: 16_384,
            text_bytes: 64 * 1024,
            attributes_per_object: 64,
            plan_bytes: 8 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct ObjectFormInsertHwpxLimits(ObjectFormInsertHwpxLimitConfig);

impl ObjectFormInsertHwpxLimits {
    pub const HARD_MAX_BYTES: usize = 128 * 1024 * 1024;
    pub const HARD_MAX_ELEMENTS: usize = 4_000_000;
    pub const HARD_MAX_OBJECTS: usize = 1_000_000;
    pub const HARD_MAX_TEXT_BYTES: usize = 1024 * 1024;
    pub const HARD_MAX_ATTRIBUTES: usize = 1024;

    /// Creates finite limits without silently clamping caller values.
    ///
    /// # Errors
    ///
    /// Rejects zero, inconsistent, or hard-ceiling-exceeding values.
    pub const fn new(
        config: ObjectFormInsertHwpxLimitConfig,
    ) -> Result<Self, ObjectFormInsertHwpxError> {
        if config.section_bytes == 0
            || config.output_bytes < config.section_bytes
            || config.output_bytes > Self::HARD_MAX_BYTES
            || config.elements == 0
            || config.elements > Self::HARD_MAX_ELEMENTS
            || config.objects == 0
            || config.objects > Self::HARD_MAX_OBJECTS
            || config.text_bytes == 0
            || config.text_bytes > Self::HARD_MAX_TEXT_BYTES
            || config.attributes_per_object == 0
            || config.attributes_per_object > Self::HARD_MAX_ATTRIBUTES
            || config.plan_bytes == 0
            || config.plan_bytes > Self::HARD_MAX_BYTES
        {
            return Err(ObjectFormInsertHwpxError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> ObjectFormInsertHwpxLimitConfig {
        self.0
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ObjectFormInsertHwpxReadback {
    pub section_sha256: [u8; 32],
    pub object_inventory_sha256: [u8; 32],
    pub inserted_form_sha256: Option<[u8; 32]>,
    pub object_count: usize,
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ObjectFormInsertHwpxPlan {
    schema_version: &'static str,
    profile_id: &'static str,
    source_section_sha256: [u8; 32],
    source_object_inventory_sha256: [u8; 32],
    insertion_index: usize,
    object: SpecialObjectState,
    domain_plan: ObjectSpecialPlan,
    domain_plan_sha256: String,
    plan_sha256: String,
}

impl ObjectFormInsertHwpxPlan {
    #[must_use]
    pub fn plan_sha256(&self) -> &str {
        &self.plan_sha256
    }

    /// Serializes the bound plan within its configured finite limit.
    ///
    /// # Errors
    ///
    /// Rejects serialization or output-limit failures.
    pub fn canonical_json(
        &self,
        limits: ObjectFormInsertHwpxLimits,
    ) -> Result<Vec<u8>, ObjectFormInsertHwpxError> {
        serialize_bounded(self, limits)
    }
}

impl fmt::Debug for ObjectFormInsertHwpxPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectFormInsertHwpxPlan")
            .field("profile_id", &self.profile_id)
            .field("capability_id", &"obj.form_object_insert")
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ObjectFormInsertHwpxLoweringReceipt {
    pub profile_id: &'static str,
    pub capability_id: &'static str,
    pub source_section_sha256: [u8; 32],
    pub output_section_sha256: [u8; 32],
    pub source_object_inventory_sha256: [u8; 32],
    pub output_object_inventory_sha256: [u8; 32],
    pub inserted_form_sha256: [u8; 32],
    pub source_state_sha256: String,
    pub target_state_sha256: String,
    pub plan_sha256: String,
    pub target_document_flow_sha256: String,
    pub modified_span_count: usize,
    pub source_bytes: usize,
    pub output_bytes: usize,
}

impl fmt::Debug for ObjectFormInsertHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectFormInsertHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field("capability_id", &self.capability_id)
            .field("modified_span_count", &self.modified_span_count)
            .finish_non_exhaustive()
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum ObjectFormInsertHwpxError {
    #[error("object-form insertion HWPX limits are invalid")]
    InvalidLimit,
    #[error("object-form insertion HWPX input exceeds a finite limit")]
    InputLimit,
    #[error("object-form insertion HWPX object inventory is unsupported or ambiguous")]
    UnsupportedObject,
    #[error("object-form insertion HWPX identity or order is invalid")]
    InvalidIdentity,
    #[error("object-form insertion HWPX profile cannot represent this form")]
    UnsupportedProfile,
    #[error("object-form insertion HWPX source drifted")]
    SourceDrift,
    #[error("object-form insertion HWPX plan was tampered with")]
    PlanTampered,
    #[error("object-form insertion HWPX readback differs from the target state")]
    ReadbackMismatch,
    #[error("object-form insertion HWPX preservation check failed")]
    PreservationMismatch,
    #[error("object-form insertion HWPX text is invalid")]
    InvalidText,
    #[error("object-form insertion HWPX output exceeds a finite limit")]
    OutputLimit,
    #[error("object-form insertion HWPX allocation failed")]
    AllocationFailed,
    #[error(transparent)]
    Domain(#[from] ObjectSpecialError),
    #[error(transparent)]
    Preserving(#[from] PreservingXmlError),
}

impl ObjectFormInsertHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "object_form_insert_hwpx_invalid_limit",
            Self::InputLimit => "object_form_insert_hwpx_input_limit",
            Self::UnsupportedObject => "object_form_insert_hwpx_unsupported_object",
            Self::InvalidIdentity => "object_form_insert_hwpx_invalid_identity",
            Self::UnsupportedProfile => "object_form_insert_hwpx_unsupported_profile",
            Self::SourceDrift => "object_form_insert_hwpx_source_drift",
            Self::PlanTampered => "object_form_insert_hwpx_plan_tampered",
            Self::ReadbackMismatch => "object_form_insert_hwpx_readback_mismatch",
            Self::PreservationMismatch => "object_form_insert_hwpx_preservation_mismatch",
            Self::InvalidText => "object_form_insert_hwpx_invalid_text",
            Self::OutputLimit => "object_form_insert_hwpx_output_limit",
            Self::AllocationFailed => "object_form_insert_hwpx_allocation_failed",
            Self::Domain(_) => "object_form_insert_hwpx_domain",
            Self::Preserving(_) => "object_form_insert_hwpx_preserving_xml",
        }
    }
}

#[derive(Debug)]
pub struct ObjectFormInsertHwpxReader;

impl ObjectFormInsertHwpxReader {
    /// Reads the complete ordered run-object projection and any qualified inserted form.
    ///
    /// # Errors
    ///
    /// Rejects malformed, ambiguous, unsupported, or semantically different projections.
    pub fn read_in_section(
        source: &[u8],
        expected: &domain_ir::ObjectSpecialDocumentState,
        limits: ObjectFormInsertHwpxLimits,
    ) -> Result<ObjectFormInsertHwpxReadback, ObjectFormInsertHwpxError> {
        let parsed = parse_inventory(source, limits)?;
        let ordered = ordered_identities(expected)?;
        if parsed.roots.len() != ordered.len() {
            return Err(ObjectFormInsertHwpxError::ReadbackMismatch);
        }
        for ((root, native), identity) in parsed
            .roots
            .iter()
            .zip(parsed.identities.iter())
            .zip(ordered.iter())
        {
            if native.0 != identity.native_object_id || native.1 != identity.native_instance_id {
                return Err(ObjectFormInsertHwpxError::ReadbackMismatch);
            }
            let expected_special = expected
                .special_objects()
                .iter()
                .find(|object| object.identity == **identity);
            match expected_special {
                None => {
                    if has_name(element(&parsed.document, *root)?, "edit") {
                        return Err(ObjectFormInsertHwpxError::ReadbackMismatch);
                    }
                }
                Some(object) => {
                    verify_form_object(source, &parsed.document, *root, object, limits)?;
                }
            }
        }
        let inserted_form_sha256 = expected
            .special_objects()
            .iter()
            .find(|object| object.object_kind == SpecialObjectKind::FormObject)
            .map(|object| {
                let position = ordered
                    .iter()
                    .position(|identity| **identity == object.identity)
                    .ok_or(ObjectFormInsertHwpxError::ReadbackMismatch)?;
                digest_span(
                    source,
                    outer_span(element(&parsed.document, parsed.roots[position])?)?,
                )
            })
            .transpose()?;
        parsed.document.verify_untouched_round_trip()?;
        Ok(ObjectFormInsertHwpxReadback {
            section_sha256: Sha256::digest(source).into(),
            object_inventory_sha256: inventory_sha256(source, &parsed)?,
            inserted_form_sha256,
            object_count: parsed.roots.len(),
        })
    }
}

#[derive(Debug)]
pub struct ObjectFormInsertHwpxBuilder;

impl ObjectFormInsertHwpxBuilder {
    /// Binds one exact `obj.form_object_insert` plan to immutable section bytes.
    ///
    /// # Errors
    ///
    /// Rejects capability, profile, identity, source, flow, or plan drift.
    pub fn plan(
        source: &[u8],
        domain_plan: &ObjectSpecialPlan,
        current_document_flow_sha256: &str,
        state_limits: ObjectSpecialLimits,
        hwpx_limits: ObjectFormInsertHwpxLimits,
    ) -> Result<ObjectFormInsertHwpxPlan, ObjectFormInsertHwpxError> {
        let (insertion_index, object) = operation_binding(domain_plan)?;
        verify_form_profile(object)?;
        if domain_plan.source_document_flow_sha256() != current_document_flow_sha256 {
            return Err(ObjectFormInsertHwpxError::SourceDrift);
        }
        let result = ObjectSpecialBuilder::build(
            domain_plan,
            domain_plan.source_state(),
            current_document_flow_sha256,
            state_limits,
        )?;
        if &result.state != domain_plan.target_state() {
            return Err(ObjectFormInsertHwpxError::PlanTampered);
        }
        let source_readback = ObjectFormInsertHwpxReader::read_in_section(
            source,
            domain_plan.source_state(),
            hwpx_limits,
        )?;
        if insertion_index > source_readback.object_count {
            return Err(ObjectFormInsertHwpxError::InvalidIdentity);
        }
        let mut plan = ObjectFormInsertHwpxPlan {
            schema_version: OBJECT_SPECIAL_SCHEMA_VERSION,
            profile_id: OBJECT_FORM_INSERT_HWPX_PROFILE_ID,
            source_section_sha256: source_readback.section_sha256,
            source_object_inventory_sha256: source_readback.object_inventory_sha256,
            insertion_index,
            object: object.clone(),
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
pub struct ObjectFormInsertHwpxLowerer;

impl ObjectFormInsertHwpxLowerer {
    /// Inserts one hash-qualified native static edit and verifies preservation and readback.
    ///
    /// # Errors
    ///
    /// Returns no bytes on plan, source, flow, profile, preservation, or readback drift.
    pub fn lower_in_section_with_receipt(
        source: &[u8],
        plan: &ObjectFormInsertHwpxPlan,
        current_document_flow_sha256: &str,
        state_limits: ObjectSpecialLimits,
        hwpx_limits: ObjectFormInsertHwpxLimits,
    ) -> Result<(Vec<u8>, ObjectFormInsertHwpxLoweringReceipt), ObjectFormInsertHwpxError> {
        validate_plan(plan, hwpx_limits)?;
        if Sha256::digest(source).as_slice() != plan.source_section_sha256
            || current_document_flow_sha256 != plan.domain_plan.source_document_flow_sha256()
        {
            return Err(ObjectFormInsertHwpxError::SourceDrift);
        }
        let source_readback = ObjectFormInsertHwpxReader::read_in_section(
            source,
            plan.domain_plan.source_state(),
            hwpx_limits,
        )?;
        if source_readback.object_inventory_sha256 != plan.source_object_inventory_sha256 {
            return Err(ObjectFormInsertHwpxError::SourceDrift);
        }
        let result = ObjectSpecialBuilder::build(
            &plan.domain_plan,
            plan.domain_plan.source_state(),
            current_document_flow_sha256,
            state_limits,
        )?;
        if &result.state != plan.domain_plan.target_state() {
            return Err(ObjectFormInsertHwpxError::PlanTampered);
        }
        let parsed = parse_inventory(source, hwpx_limits)?;
        let (position, prefix) = insertion_position(&parsed, plan.insertion_index)?;
        let payload = form_payload(&plan.object)?;
        let fragment = form_fragment(prefix, &plan.object.identity, payload, hwpx_limits)?;
        let output = apply_insertion(source, position, fragment.as_bytes(), hwpx_limits)?;
        verify_insertion(source, &output, position, fragment.as_bytes())?;
        let output_readback = ObjectFormInsertHwpxReader::read_in_section(
            &output,
            plan.domain_plan.target_state(),
            hwpx_limits,
        )?;
        let inserted_form_sha256 = output_readback
            .inserted_form_sha256
            .ok_or(ObjectFormInsertHwpxError::ReadbackMismatch)?;
        let receipt = ObjectFormInsertHwpxLoweringReceipt {
            profile_id: OBJECT_FORM_INSERT_HWPX_PROFILE_ID,
            capability_id: "obj.form_object_insert",
            source_section_sha256: source_readback.section_sha256,
            output_section_sha256: output_readback.section_sha256,
            source_object_inventory_sha256: source_readback.object_inventory_sha256,
            output_object_inventory_sha256: output_readback.object_inventory_sha256,
            inserted_form_sha256,
            source_state_sha256: plan
                .domain_plan
                .source_state()
                .canonical_sha256(state_limits)?,
            target_state_sha256: result.state.canonical_sha256(state_limits)?,
            plan_sha256: plan.plan_sha256.clone(),
            target_document_flow_sha256: plan.domain_plan.target_document_flow_sha256().to_owned(),
            modified_span_count: 1,
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
        plan: &ObjectFormInsertHwpxPlan,
        current_document_flow_sha256: &str,
        state_limits: ObjectSpecialLimits,
        hwpx_limits: ObjectFormInsertHwpxLimits,
    ) -> Result<Vec<u8>, ObjectFormInsertHwpxError> {
        Ok(Self::lower_in_section_with_receipt(
            source,
            plan,
            current_document_flow_sha256,
            state_limits,
            hwpx_limits,
        )?
        .0)
    }
}

struct ParsedInventory {
    document: PreservingXmlDocument,
    roots: Vec<usize>,
    identities: Vec<(u32, u32)>,
}

fn parse_inventory(
    source: &[u8],
    limits: ObjectFormInsertHwpxLimits,
) -> Result<ParsedInventory, ObjectFormInsertHwpxError> {
    if source.is_empty() || source.len() > limits.0.section_bytes {
        return Err(ObjectFormInsertHwpxError::InputLimit);
    }
    let document = PreservingXmlDocument::parse(source)?;
    if document.elements().len() > limits.0.elements {
        return Err(ObjectFormInsertHwpxError::InputLimit);
    }
    let mut roots = Vec::new();
    let mut identities: Vec<(u32, u32)> = Vec::new();
    for (index, candidate) in document.elements().iter().enumerate() {
        if !is_run_object(candidate) {
            continue;
        }
        let parent = candidate
            .parent()
            .and_then(|value| document.elements().get(value))
            .ok_or(ObjectFormInsertHwpxError::UnsupportedObject)?;
        if !has_name(parent, "run") {
            continue;
        }
        if roots.len() >= limits.0.objects
            || candidate.attributes().len() > limits.0.attributes_per_object
        {
            return Err(ObjectFormInsertHwpxError::InputLimit);
        }
        let native_object_id = canonical_u32(source, strict_attribute(candidate, "id")?)?;
        let native_instance_id = canonical_u32(source, strict_attribute(candidate, "instid")?)?;
        if native_object_id == 0
            || native_instance_id == 0
            || identities
                .iter()
                .any(|identity| identity.0 == native_object_id || identity.1 == native_instance_id)
        {
            return Err(ObjectFormInsertHwpxError::InvalidIdentity);
        }
        roots
            .try_reserve(1)
            .map_err(|_| ObjectFormInsertHwpxError::AllocationFailed)?;
        identities
            .try_reserve(1)
            .map_err(|_| ObjectFormInsertHwpxError::AllocationFailed)?;
        roots.push(index);
        identities.push((native_object_id, native_instance_id));
    }
    if roots.is_empty() {
        return Err(ObjectFormInsertHwpxError::UnsupportedObject);
    }
    Ok(ParsedInventory {
        document,
        roots,
        identities,
    })
}

fn ordered_identities(
    state: &domain_ir::ObjectSpecialDocumentState,
) -> Result<Vec<&ObjectIdentity>, ObjectFormInsertHwpxError> {
    let mut identities = BTreeMap::new();
    for identity in state.external_objects() {
        if identities
            .insert(&identity.logical_object_id, identity)
            .is_some()
        {
            return Err(ObjectFormInsertHwpxError::InvalidIdentity);
        }
    }
    for object in state.special_objects() {
        if identities
            .insert(&object.identity.logical_object_id, &object.identity)
            .is_some()
        {
            return Err(ObjectFormInsertHwpxError::InvalidIdentity);
        }
    }
    state
        .document_order()
        .iter()
        .map(|id| {
            identities
                .get(id)
                .copied()
                .ok_or(ObjectFormInsertHwpxError::InvalidIdentity)
        })
        .collect()
}

fn operation_binding(
    plan: &ObjectSpecialPlan,
) -> Result<(usize, &SpecialObjectState), ObjectFormInsertHwpxError> {
    if plan.capability_id() != "obj.form_object_insert" {
        return Err(ObjectFormInsertHwpxError::UnsupportedProfile);
    }
    match plan.operation() {
        ObjectSpecialOperation::InsertFormObject {
            insertion_index,
            object,
        } => Ok((*insertion_index, object)),
        _ => Err(ObjectFormInsertHwpxError::UnsupportedProfile),
    }
}

fn form_payload(
    object: &SpecialObjectState,
) -> Result<&StaticFormPayload, ObjectFormInsertHwpxError> {
    match &object.payload {
        SpecialObjectPayload::FormObject { form } => Ok(form),
        _ => Err(ObjectFormInsertHwpxError::UnsupportedProfile),
    }
}

fn verify_form_profile(object: &SpecialObjectState) -> Result<(), ObjectFormInsertHwpxError> {
    let form = form_payload(object)?;
    if object.object_kind != SpecialObjectKind::FormObject
        || form.control_kind != StaticFormControlKind::EditBox
        || form.active_content_present
        || form.form_properties_sha256 != OBJECT_FORM_INSERT_STATIC_EDIT_PROFILE_SHA256
    {
        return Err(ObjectFormInsertHwpxError::UnsupportedProfile);
    }
    Ok(())
}

fn insertion_position(
    parsed: &ParsedInventory,
    insertion_index: usize,
) -> Result<(usize, Option<&str>), ObjectFormInsertHwpxError> {
    if insertion_index > parsed.roots.len() {
        return Err(ObjectFormInsertHwpxError::InvalidIdentity);
    }
    let reference = if insertion_index == parsed.roots.len() {
        *parsed
            .roots
            .last()
            .ok_or(ObjectFormInsertHwpxError::UnsupportedObject)?
    } else {
        parsed.roots[insertion_index]
    };
    let element = element(&parsed.document, reference)?;
    let parent = element
        .parent()
        .ok_or(ObjectFormInsertHwpxError::UnsupportedObject)?;
    if parsed
        .roots
        .iter()
        .any(|root| element_at(&parsed.document, *root).parent() != Some(parent))
    {
        return Err(ObjectFormInsertHwpxError::UnsupportedProfile);
    }
    let position = if insertion_index == parsed.roots.len() {
        outer_span(element)?.end()
    } else {
        element.start_tag_span().start()
    };
    Ok((position, element.name().prefix()))
}

fn form_fragment(
    prefix: Option<&str>,
    identity: &ObjectIdentity,
    form: &StaticFormPayload,
    limits: ObjectFormInsertHwpxLimits,
) -> Result<String, ObjectFormInsertHwpxError> {
    let name_value = escape_xml_attribute(&form.name)?;
    let text_value = escape_xml_text(&form.value)?;
    if name_value.len() > limits.0.text_bytes || text_value.len() > limits.0.text_bytes {
        return Err(ObjectFormInsertHwpxError::OutputLimit);
    }
    let name = |local: &str| match prefix {
        Some(value) => format!("{value}:{local}"),
        None => local.to_owned(),
    };
    Ok(format!(
        concat!(
            "<{edit} id=\"{id}\" zOrder=\"0\" numberingType=\"NONE\" textWrap=\"TOP_AND_BOTTOM\" ",
            "textFlow=\"BOTH_SIDES\" lock=\"0\" dropcapstyle=\"None\" href=\"\" groupLevel=\"0\" instid=\"{instid}\" ",
            "name=\"{name_value}\" foreColor=\"#000000\" backColor=\"#FFFFFF\" groupName=\"\" tabStop=\"1\" editable=\"1\" ",
            "tabOrder=\"0\" enabled=\"{enabled}\" borderTypeIDRef=\"0\" drawFrame=\"1\" printable=\"{printable}\" command=\"\" ",
            "multiLine=\"0\" passwordChar=\"*\" maxLength=\"64\" scrollBars=\"NONE\" tabKeyBehavior=\"NEXT_OBJECT\" ",
            "numOnly=\"0\" readOnly=\"0\" alignText=\"LEFT\">",
            "<{sz} width=\"10800\" widthRelTo=\"ABSOLUTE\" height=\"5400\" heightRelTo=\"ABSOLUTE\" protect=\"0\"/>",
            "<{pos} treatAsChar=\"1\" affectLSpacing=\"1\" flowWithText=\"1\" allowOverlap=\"0\" holdAnchorAndSO=\"0\" ",
            "vertRelTo=\"PARA\" horzRelTo=\"COLUMN\" vertAlign=\"TOP\" horzAlign=\"LEFT\" vertOffset=\"0\" horzOffset=\"0\"/>",
            "<{margin} left=\"0\" right=\"0\" top=\"0\" bottom=\"0\"/>",
            "<{char_pr} charPrIDRef=\"0\" followContext=\"0\" autoSz=\"0\" wordWrap=\"1\"/>",
            "<{text}>{text_value}</{text}></{edit}>"
        ),
        edit = name("edit"),
        id = identity.native_object_id,
        instid = identity.native_instance_id,
        name_value = name_value,
        enabled = bool_text(form.enabled),
        printable = bool_text(form.printable),
        sz = name("sz"),
        pos = name("pos"),
        margin = name("outMargin"),
        char_pr = name("formCharPr"),
        text = name("text"),
        text_value = text_value,
    ))
}

fn verify_form_object(
    source: &[u8],
    document: &PreservingXmlDocument,
    root: usize,
    object: &SpecialObjectState,
    limits: ObjectFormInsertHwpxLimits,
) -> Result<(), ObjectFormInsertHwpxError> {
    verify_form_profile(object)?;
    let form = form_payload(object)?;
    let root_element = element(document, root)?;
    if !has_name(root_element, "edit") {
        return Err(ObjectFormInsertHwpxError::ReadbackMismatch);
    }
    verify_form_root_attributes(source, root_element, object, form)?;
    verify_form_children(source, document, root, form, limits)
}

fn verify_form_root_attributes(
    source: &[u8],
    root_element: &XmlElementToken,
    object: &SpecialObjectState,
    form: &StaticFormPayload,
) -> Result<(), ObjectFormInsertHwpxError> {
    let expected_attributes = [
        ("id", object.identity.native_object_id.to_string()),
        ("zOrder", "0".to_owned()),
        ("numberingType", "NONE".to_owned()),
        ("textWrap", "TOP_AND_BOTTOM".to_owned()),
        ("textFlow", "BOTH_SIDES".to_owned()),
        ("lock", "0".to_owned()),
        ("dropcapstyle", "None".to_owned()),
        ("href", String::new()),
        ("groupLevel", "0".to_owned()),
        ("instid", object.identity.native_instance_id.to_string()),
        ("name", form.name.clone()),
        ("foreColor", "#000000".to_owned()),
        ("backColor", "#FFFFFF".to_owned()),
        ("groupName", String::new()),
        ("tabStop", "1".to_owned()),
        ("editable", "1".to_owned()),
        ("tabOrder", "0".to_owned()),
        ("enabled", bool_text(form.enabled).to_owned()),
        ("borderTypeIDRef", "0".to_owned()),
        ("drawFrame", "1".to_owned()),
        ("printable", bool_text(form.printable).to_owned()),
        ("command", String::new()),
        ("multiLine", "0".to_owned()),
        ("passwordChar", "*".to_owned()),
        ("maxLength", "64".to_owned()),
        ("scrollBars", "NONE".to_owned()),
        ("tabKeyBehavior", "NEXT_OBJECT".to_owned()),
        ("numOnly", "0".to_owned()),
        ("readOnly", "0".to_owned()),
        ("alignText", "LEFT".to_owned()),
    ];
    let non_namespace_count = root_element
        .attributes()
        .iter()
        .filter(|attribute| !attribute.is_namespace_declaration())
        .count();
    if non_namespace_count != expected_attributes.len() {
        return Err(ObjectFormInsertHwpxError::ReadbackMismatch);
    }
    for (name, expected) in expected_attributes {
        let value = xml_unescape(lexical_value(
            source,
            strict_attribute(root_element, name)?,
        )?)?;
        if value != expected {
            return Err(ObjectFormInsertHwpxError::ReadbackMismatch);
        }
    }
    Ok(())
}

fn verify_form_children(
    source: &[u8],
    document: &PreservingXmlDocument,
    root: usize,
    form: &StaticFormPayload,
    limits: ObjectFormInsertHwpxLimits,
) -> Result<(), ObjectFormInsertHwpxError> {
    verify_empty_child(
        source,
        document,
        root,
        "sz",
        &[
            ("width", "10800"),
            ("widthRelTo", "ABSOLUTE"),
            ("height", "5400"),
            ("heightRelTo", "ABSOLUTE"),
            ("protect", "0"),
        ],
    )?;
    verify_empty_child(
        source,
        document,
        root,
        "pos",
        &[
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
        ],
    )?;
    verify_empty_child(
        source,
        document,
        root,
        "outMargin",
        &[("left", "0"), ("right", "0"), ("top", "0"), ("bottom", "0")],
    )?;
    verify_empty_child(
        source,
        document,
        root,
        "formCharPr",
        &[
            ("charPrIDRef", "0"),
            ("followContext", "0"),
            ("autoSz", "0"),
            ("wordWrap", "1"),
        ],
    )?;
    let text = only_direct_child(document, root, "text")?;
    let children = direct_element_children(document, root)?;
    if children.len() != 5
        || children
            != [
                only_direct_child(document, root, "sz")?,
                only_direct_child(document, root, "pos")?,
                only_direct_child(document, root, "outMargin")?,
                only_direct_child(document, root, "formCharPr")?,
                text,
            ]
        || element(document, text)?.first_child().is_some()
    {
        return Err(ObjectFormInsertHwpxError::ReadbackMismatch);
    }
    let span = element(document, text)?
        .content_span()
        .ok_or(ObjectFormInsertHwpxError::UnsupportedProfile)?;
    let lexical = std::str::from_utf8(
        source
            .get(span.start()..span.end())
            .ok_or(ObjectFormInsertHwpxError::InvalidText)?,
    )
    .map_err(|_| ObjectFormInsertHwpxError::InvalidText)?;
    if lexical.len() > limits.0.text_bytes || xml_unescape(lexical)? != form.value {
        return Err(ObjectFormInsertHwpxError::ReadbackMismatch);
    }
    Ok(())
}

fn verify_empty_child(
    source: &[u8],
    document: &PreservingXmlDocument,
    parent: usize,
    local_name: &str,
    expected: &[(&str, &str)],
) -> Result<(), ObjectFormInsertHwpxError> {
    let index = only_direct_child(document, parent, local_name)?;
    let child = element(document, index)?;
    let attributes = child
        .attributes()
        .iter()
        .filter(|attribute| !attribute.is_namespace_declaration())
        .count();
    if !child.is_empty() || attributes != expected.len() {
        return Err(ObjectFormInsertHwpxError::ReadbackMismatch);
    }
    for (name, value) in expected {
        if lexical_value(source, strict_attribute(child, name)?)? != *value {
            return Err(ObjectFormInsertHwpxError::ReadbackMismatch);
        }
    }
    Ok(())
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
                | "chart"
                | "edit"
                | "checkBtn"
                | "radioBtn"
                | "comboBox"
                | "listBox"
                | "btn"
                | "scrollBar"
        )
}

fn has_name(element: &XmlElementToken, local_name: &str) -> bool {
    element.name().namespace() == Some(PARAGRAPH_NS) && element.name().local_name() == local_name
}

fn direct_element_children(
    document: &PreservingXmlDocument,
    parent: usize,
) -> Result<Vec<usize>, ObjectFormInsertHwpxError> {
    let mut values = Vec::new();
    let mut child = element(document, parent)?.first_child();
    while let Some(index) = child {
        values
            .try_reserve(1)
            .map_err(|_| ObjectFormInsertHwpxError::AllocationFailed)?;
        values.push(index);
        child = element(document, index)?.next_sibling();
    }
    Ok(values)
}

fn only_direct_child(
    document: &PreservingXmlDocument,
    parent: usize,
    local_name: &str,
) -> Result<usize, ObjectFormInsertHwpxError> {
    let values = direct_element_children(document, parent)?
        .into_iter()
        .filter(|index| has_name(element_at(document, *index), local_name))
        .collect::<Vec<_>>();
    match values.as_slice() {
        [value] => Ok(*value),
        _ => Err(ObjectFormInsertHwpxError::ReadbackMismatch),
    }
}

fn strict_attribute<'a>(
    element: &'a XmlElementToken,
    local_name: &str,
) -> Result<&'a XmlAttributeToken, ObjectFormInsertHwpxError> {
    let mut matches = element.attributes().iter().filter(|attribute| {
        !attribute.is_namespace_declaration()
            && attribute.name().namespace().is_none()
            && attribute.name().local_name() == local_name
    });
    let value = matches
        .next()
        .ok_or(ObjectFormInsertHwpxError::UnsupportedProfile)?;
    if matches.next().is_some() {
        return Err(ObjectFormInsertHwpxError::UnsupportedProfile);
    }
    Ok(value)
}

fn lexical_value<'a>(
    source: &'a [u8],
    attribute: &XmlAttributeToken,
) -> Result<&'a str, ObjectFormInsertHwpxError> {
    std::str::from_utf8(
        source
            .get(attribute.value_span().start()..attribute.value_span().end())
            .ok_or(ObjectFormInsertHwpxError::UnsupportedProfile)?,
    )
    .map_err(|_| ObjectFormInsertHwpxError::UnsupportedProfile)
}

fn canonical_u32(
    source: &[u8],
    attribute: &XmlAttributeToken,
) -> Result<u32, ObjectFormInsertHwpxError> {
    let value = lexical_value(source, attribute)?;
    if value.is_empty()
        || !value.bytes().all(|byte| byte.is_ascii_digit())
        || (value != "0" && value.starts_with('0'))
    {
        return Err(ObjectFormInsertHwpxError::InvalidIdentity);
    }
    value
        .parse::<u32>()
        .map_err(|_| ObjectFormInsertHwpxError::InvalidIdentity)
}

fn escape_xml_attribute(value: &str) -> Result<String, ObjectFormInsertHwpxError> {
    if value.chars().any(invalid_xml_character) {
        return Err(ObjectFormInsertHwpxError::InvalidText);
    }
    Ok(value
        .replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
        .replace('\'', "&apos;"))
}

fn escape_xml_text(value: &str) -> Result<String, ObjectFormInsertHwpxError> {
    if value.chars().any(invalid_xml_character) {
        return Err(ObjectFormInsertHwpxError::InvalidText);
    }
    Ok(value
        .replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;"))
}

fn xml_unescape(value: &str) -> Result<String, ObjectFormInsertHwpxError> {
    let mut output = String::with_capacity(value.len());
    let mut rest = value;
    while let Some(position) = rest.find('&') {
        output.push_str(&rest[..position]);
        let tail = &rest[position..];
        let (replacement, consumed) = if tail.starts_with("&amp;") {
            ("&", 5)
        } else if tail.starts_with("&lt;") {
            ("<", 4)
        } else if tail.starts_with("&gt;") {
            (">", 4)
        } else if tail.starts_with("&quot;") {
            ("\"", 6)
        } else if tail.starts_with("&apos;") {
            ("'", 6)
        } else {
            return Err(ObjectFormInsertHwpxError::InvalidText);
        };
        output.push_str(replacement);
        rest = &tail[consumed..];
    }
    output.push_str(rest);
    Ok(output)
}

const fn invalid_xml_character(value: char) -> bool {
    !matches!(
        value as u32,
        0x9 | 0xA | 0xD | 0x20..=0xD7FF | 0xE000..=0xFFFD | 0x0001_0000..=0x0010_FFFF
    )
}

const fn bool_text(value: bool) -> &'static str {
    if value { "1" } else { "0" }
}

fn inventory_sha256(
    source: &[u8],
    parsed: &ParsedInventory,
) -> Result<[u8; 32], ObjectFormInsertHwpxError> {
    let mut digest = Sha256::new();
    for root in &parsed.roots {
        let span = outer_span(element(&parsed.document, *root)?)?;
        digest.update(
            source
                .get(span.start()..span.end())
                .ok_or(ObjectFormInsertHwpxError::UnsupportedObject)?,
        );
        digest.update([0]);
    }
    Ok(digest.finalize().into())
}

fn apply_insertion(
    source: &[u8],
    position: usize,
    insertion: &[u8],
    limits: ObjectFormInsertHwpxLimits,
) -> Result<Vec<u8>, ObjectFormInsertHwpxError> {
    let output_len = source
        .len()
        .checked_add(insertion.len())
        .ok_or(ObjectFormInsertHwpxError::OutputLimit)?;
    if position > source.len() || output_len > limits.0.output_bytes {
        return Err(ObjectFormInsertHwpxError::OutputLimit);
    }
    let mut output = Vec::new();
    output
        .try_reserve_exact(output_len)
        .map_err(|_| ObjectFormInsertHwpxError::AllocationFailed)?;
    output.extend_from_slice(&source[..position]);
    output.extend_from_slice(insertion);
    output.extend_from_slice(&source[position..]);
    Ok(output)
}

fn verify_insertion(
    source: &[u8],
    output: &[u8],
    position: usize,
    insertion: &[u8],
) -> Result<(), ObjectFormInsertHwpxError> {
    let insertion_end = position
        .checked_add(insertion.len())
        .ok_or(ObjectFormInsertHwpxError::PreservationMismatch)?;
    if source[..position] != output[..position]
        || insertion != &output[position..insertion_end]
        || source[position..] != output[insertion_end..]
    {
        return Err(ObjectFormInsertHwpxError::PreservationMismatch);
    }
    Ok(())
}

fn validate_plan(
    plan: &ObjectFormInsertHwpxPlan,
    limits: ObjectFormInsertHwpxLimits,
) -> Result<(), ObjectFormInsertHwpxError> {
    let (insertion_index, object) = operation_binding(&plan.domain_plan)?;
    if plan.schema_version != OBJECT_SPECIAL_SCHEMA_VERSION
        || plan.profile_id != OBJECT_FORM_INSERT_HWPX_PROFILE_ID
        || insertion_index != plan.insertion_index
        || object != &plan.object
        || plan.domain_plan.plan_sha256() != plan.domain_plan_sha256
        || plan_binding_sha256(plan, limits)? != plan.plan_sha256
    {
        return Err(ObjectFormInsertHwpxError::PlanTampered);
    }
    verify_form_profile(&plan.object)
}

fn plan_binding_sha256(
    plan: &ObjectFormInsertHwpxPlan,
    limits: ObjectFormInsertHwpxLimits,
) -> Result<String, ObjectFormInsertHwpxError> {
    let mut unsigned = plan.clone();
    unsigned.plan_sha256.clear();
    Ok(hex(
        Sha256::digest(serialize_bounded(&unsigned, limits)?).into()
    ))
}

fn serialize_bounded<T: Serialize>(
    value: &T,
    limits: ObjectFormInsertHwpxLimits,
) -> Result<Vec<u8>, ObjectFormInsertHwpxError> {
    let bytes = serde_json::to_vec(value).map_err(|_| ObjectFormInsertHwpxError::PlanTampered)?;
    if bytes.len() > limits.0.plan_bytes {
        return Err(ObjectFormInsertHwpxError::OutputLimit);
    }
    Ok(bytes)
}

fn element(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<&XmlElementToken, ObjectFormInsertHwpxError> {
    document
        .elements()
        .get(index)
        .ok_or(ObjectFormInsertHwpxError::UnsupportedObject)
}

fn element_at(document: &PreservingXmlDocument, index: usize) -> &XmlElementToken {
    &document.elements()[index]
}

fn outer_span(element: &XmlElementToken) -> Result<XmlByteSpan, ObjectFormInsertHwpxError> {
    element
        .outer_span()
        .ok_or(ObjectFormInsertHwpxError::UnsupportedObject)
}

fn digest_span(source: &[u8], span: XmlByteSpan) -> Result<[u8; 32], ObjectFormInsertHwpxError> {
    Ok(Sha256::digest(
        source
            .get(span.start()..span.end())
            .ok_or(ObjectFormInsertHwpxError::UnsupportedObject)?,
    )
    .into())
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
