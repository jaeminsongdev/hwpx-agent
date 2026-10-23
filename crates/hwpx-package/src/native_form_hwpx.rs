//! Observed native-form identity/anchor profile; component IDs are never written as native IDs.
use std::{collections::BTreeSet, fmt};

use domain_ir::{
    FormButtonBackStyle, FormButtonValue, FormCharacterProperties, FormCommonProperties,
    FormControlBuilder, FormControlError, FormControlIdentity, FormControlLimits,
    FormControlPayload, FormControlPlan, FormDocumentState, FormListItem, FormScrollBars,
    FormTabKeyBehavior, FormTextAlignment, LogicalId, NativeFormTag,
};
use quick_xml::escape::unescape;
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::preserving_xml::{
    PreservingXmlDocument, PreservingXmlError, XmlAttributeToken, XmlElementToken,
};

pub const NATIVE_FORM_HWPX_PROFILE_ID: &str =
    "hwpx-agent.native-form-hwpx.hwpml-2011-observed-identity/v1";
const HP: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const HS: &str = "http://www.hancom.co.kr/hwpml/2011/section";
const COMMON: [&str; 11] = [
    "name",
    "foreColor",
    "backColor",
    "groupName",
    "tabStop",
    "editable",
    "tabOrder",
    "enabled",
    "borderTypeIDRef",
    "drawFrame",
    "printable",
];
const CHARACTER: [&str; 4] = ["charPrIDRef", "followContext", "autoSz", "wordWrap"];

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct NativeFormHwpxLimits {
    section_bytes: usize,
    elements: usize,
    controls: usize,
    text_bytes: usize,
    plan_bytes: usize,
}
impl Default for NativeFormHwpxLimits {
    fn default() -> Self {
        Self {
            section_bytes: 2 * 1024 * 1024,
            elements: 65_536,
            controls: 1024,
            text_bytes: 64 * 1024,
            plan_bytes: 4 * 1024 * 1024,
        }
    }
}
impl NativeFormHwpxLimits {
    /// Creates finite component limits without silent clamping.
    /// # Errors
    /// Rejects zero or hard-ceiling-exceeding bounds.
    pub fn new(
        section_bytes: usize,
        elements: usize,
        controls: usize,
        text_bytes: usize,
        plan_bytes: usize,
    ) -> Result<Self, NativeFormHwpxError> {
        if section_bytes == 0
            || section_bytes > 2 * 1024 * 1024
            || elements == 0
            || elements > 65_536
            || controls == 0
            || controls > 4096
            || text_bytes == 0
            || text_bytes > 64 * 1024
            || plan_bytes == 0
            || plan_bytes > 8 * 1024 * 1024
        {
            return Err(NativeFormHwpxError::InvalidLimit);
        }
        Ok(Self {
            section_bytes,
            elements,
            controls,
            text_bytes,
            plan_bytes,
        })
    }
}

/// Complete logical map, explicitly distinct from optional native identities.
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct NativeFormHwpxMap {
    pub paragraph_ids: Vec<LogicalId>,
    pub component_controls: Vec<FormControlIdentity>,
}
impl fmt::Debug for NativeFormHwpxMap {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("NativeFormHwpxMap(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum NativeFormObservedIdentity {
    Missing,
    Observed {
        object_id: Option<u32>,
        instance_id: Option<u32>,
        instance_attribute: Option<String>,
    },
}
impl fmt::Debug for NativeFormObservedIdentity {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("NativeFormObservedIdentity(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct NativeFormPhysicalAnchor {
    pub paragraph_id: LogicalId,
    pub paragraph_ordinal: usize,
    pub paragraph_child_path: Vec<usize>,
    pub run_ordinal: u32,
    pub inline_ordinal: u32,
}
impl fmt::Debug for NativeFormPhysicalAnchor {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("NativeFormPhysicalAnchor(<redacted>)")
    }
}

/// Only observed native values; defaults and validation policy are not inferred from XML.
#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum NativeFormObservedPayload {
    Text {
        value: String,
        multi_line: bool,
        password_character: Option<String>,
        native_max_length: Option<u32>,
        scroll_bars: FormScrollBars,
        tab_key_behavior: FormTabKeyBehavior,
        number_only: bool,
        read_only: bool,
        alignment: FormTextAlignment,
    },
    Button {
        caption: String,
        value: FormButtonValue,
        radio_group_name: Option<String>,
        tri_state: bool,
        back_style: FormButtonBackStyle,
    },
    Combo {
        items: Vec<FormListItem>,
        selected_value: Option<String>,
        list_box_rows: Option<u32>,
        list_box_width_hwp_units: Option<u32>,
        edit_enable: bool,
    },
    List {
        items: Vec<FormListItem>,
        selected_value: Option<String>,
        item_height_hwp_units: Option<u32>,
        top_index: u32,
    },
}
impl fmt::Debug for NativeFormObservedPayload {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("NativeFormObservedPayload(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct NativeFormControlObservation {
    pub component_identity: FormControlIdentity,
    pub native_identity: NativeFormObservedIdentity,
    pub tag: NativeFormTag,
    pub anchor: NativeFormPhysicalAnchor,
    pub common: FormCommonProperties,
    pub payload: NativeFormObservedPayload,
    pub shape_locked: bool,
    pub geometry_sha256: String,
    pub preserved_opaque_sha256: String,
    pub raw_control_sha256: String,
}
impl fmt::Debug for NativeFormControlObservation {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("NativeFormControlObservation(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct NativeFormHwpxReadback {
    section_sha256: String,
    map: NativeFormHwpxMap,
    controls: Vec<NativeFormControlObservation>,
    non_form_content_sha256: String,
}
impl NativeFormHwpxReadback {
    #[must_use]
    pub fn controls(&self) -> &[NativeFormControlObservation] {
        &self.controls
    }
    #[must_use]
    pub fn section_sha256(&self) -> &str {
        &self.section_sha256
    }
    #[must_use]
    pub fn non_form_content_sha256(&self) -> &str {
        &self.non_form_content_sha256
    }
    /// Verifies a complete typed state using actual observations, not caller-refreshed hashes.
    /// # Errors
    /// Rejects any control identity, physical anchor, native tag/value, shape or opaque mismatch.
    pub fn verify_domain_state(
        &self,
        state: &FormDocumentState,
        limits: FormControlLimits,
    ) -> Result<(), NativeFormHwpxError> {
        let _ = state.canonical_sha256(limits)?;
        if state.controls().len() != self.controls.len() {
            return Err(NativeFormHwpxError::ProjectionMismatch);
        }
        for (observed, expected) in self.controls.iter().zip(state.controls()) {
            if expected.identity != observed.component_identity
                || expected.anchor.paragraph_id != observed.anchor.paragraph_id
                || expected.anchor.run_ordinal != observed.anchor.run_ordinal
                || expected.anchor.inline_ordinal != observed.anchor.inline_ordinal
                || expected.native_binding
                    != (domain_ir::FormNativeBinding::Exact { tag: observed.tag })
                || expected.common != observed.common
                || !payload_matches(&observed.payload, &expected.payload)
                || expected.shape_locked != observed.shape_locked
                || expected.shape_state_sha256 != observed.geometry_sha256
                || expected.opaque_native_payload_sha256 != observed.preserved_opaque_sha256
                || !expected.opaque_properties.is_empty()
            {
                return Err(NativeFormHwpxError::ProjectionMismatch);
            }
        }
        // Other package-part bindings remain external; this component never claims to read them.
        let draft: serde_json::Value = serde_json::from_slice(&state.canonical_json(limits)?)
            .map_err(|_| NativeFormHwpxError::PlanBinding)?;
        if draft
            .get("non_form_content_sha256")
            .and_then(serde_json::Value::as_str)
            != Some(&self.non_form_content_sha256)
        {
            return Err(NativeFormHwpxError::ProjectionMismatch);
        }
        Ok(())
    }
}
impl fmt::Debug for NativeFormHwpxReadback {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("NativeFormHwpxReadback")
            .field("control_count", &self.controls.len())
            .finish_non_exhaustive()
    }
}

#[derive(Debug, Error)]
pub enum NativeFormHwpxError {
    #[error("NATIVE_FORM_INVALID_LIMIT")]
    InvalidLimit,
    #[error("NATIVE_FORM_INPUT_LIMIT")]
    InputLimit,
    #[error("NATIVE_FORM_UNSUPPORTED_PROFILE")]
    UnsupportedProfile,
    #[error("NATIVE_FORM_ATTRIBUTE_INVALID")]
    Attribute,
    #[error("NATIVE_FORM_PROJECTION_MISMATCH")]
    ProjectionMismatch,
    #[error("NATIVE_FORM_SOURCE_OR_PLAN_DRIFT")]
    PlanBinding,
    #[error("NATIVE_FORM_TRANSITION_NOT_REPRESENTABLE")]
    NonRepresentable,
    #[error("NATIVE_FORM_PRESERVATION_MISMATCH")]
    Preservation,
    #[error("NATIVE_FORM_ALLOCATION_FAILED")]
    Allocation,
    #[error("NATIVE_FORM_DOMAIN_REJECTED")]
    Domain(#[from] FormControlError),
    #[error("NATIVE_FORM_XML_REJECTED")]
    Xml(#[from] PreservingXmlError),
}

#[derive(Debug)]
pub struct NativeFormHwpxReader;
impl NativeFormHwpxReader {
    /// Observes the complete ordered native inventory without adding IDs or trusting expected values.
    /// # Errors
    /// Rejects ambiguous/incomplete maps, unsupported native structure, malformed attributes or limits.
    pub fn read_section(
        source: &[u8],
        map: &NativeFormHwpxMap,
        limits: NativeFormHwpxLimits,
    ) -> Result<NativeFormHwpxReadback, NativeFormHwpxError> {
        Ok(parse(source, map, limits)?.readback)
    }
    /// Rereads the actual section and compares every sealed observation and complete logical map.
    /// # Errors
    /// Rejects source, map, anchor, identity, common/payload, geometry or opaque drift.
    pub fn verify_section(
        source: &[u8],
        bound: &NativeFormHwpxReadback,
        limits: NativeFormHwpxLimits,
    ) -> Result<(), NativeFormHwpxError> {
        if &Self::read_section(source, &bound.map, limits)? != bound {
            return Err(NativeFormHwpxError::PlanBinding);
        }
        Ok(())
    }
}

#[derive(Clone, Serialize)]
pub struct NativeFormHwpxPlan {
    profile_id: &'static str,
    source: NativeFormHwpxReadback,
    domain_plan: FormControlPlan,
    plan_sha256: String,
}
impl NativeFormHwpxPlan {
    #[must_use]
    pub fn plan_sha256(&self) -> &str {
        &self.plan_sha256
    }
    /// Returns private deterministic bounded JSON; never render it in public logs.
    /// # Errors
    /// Rejects serialization or output-bound failure.
    pub fn canonical_json(
        &self,
        limits: NativeFormHwpxLimits,
    ) -> Result<Vec<u8>, NativeFormHwpxError> {
        bounded_json(self, limits)
    }
}
impl fmt::Debug for NativeFormHwpxPlan {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("NativeFormHwpxPlan(<redacted>)")
    }
}

#[derive(Debug)]
pub struct NativeFormHwpxBuilder;
impl NativeFormHwpxBuilder {
    /// Binds actual ID-optional controls to a sealed typed property/tab-order transition.
    /// # Errors
    /// Rejects unrepresentable operations or any domain/source/physical observation drift.
    pub fn plan(
        source: &[u8],
        observed: &NativeFormHwpxReadback,
        domain_plan: &FormControlPlan,
        flow: &str,
        domain_limits: FormControlLimits,
        limits: NativeFormHwpxLimits,
    ) -> Result<NativeFormHwpxPlan, NativeFormHwpxError> {
        NativeFormHwpxReader::verify_section(source, observed, limits)?;
        observed.verify_domain_state(domain_plan.source_state(), domain_limits)?;
        let built = FormControlBuilder::build(
            domain_plan,
            domain_plan.source_state(),
            flow,
            domain_limits,
        )?;
        validate_transition(
            domain_plan.source_state(),
            &built.state,
            domain_plan.capability_id(),
        )?;
        let mut plan = NativeFormHwpxPlan {
            profile_id: NATIVE_FORM_HWPX_PROFILE_ID,
            source: observed.clone(),
            domain_plan: domain_plan.clone(),
            plan_sha256: String::new(),
        };
        plan.plan_sha256 = sha(&bounded_json(&plan, limits)?);
        let _ = plan.canonical_json(limits)?;
        Ok(plan)
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct NativeFormHwpxLoweringReceipt {
    pub source_section_sha256: String,
    pub output_section_sha256: String,
    pub changed_attribute_count: usize,
    pub outside_declared_edits_byte_exact: bool,
    pub target_readback: NativeFormHwpxReadback,
}
impl fmt::Debug for NativeFormHwpxLoweringReceipt {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("NativeFormHwpxLoweringReceipt(<redacted>)")
    }
}

#[derive(Debug)]
pub struct NativeFormHwpxLowerer;
impl NativeFormHwpxLowerer {
    /// Applies only declared common/character/tab attributes; native IDs and all other bytes survive.
    /// # Errors
    /// Returns no output on stale source/flow, tampered plan, unsupported transition or failed readback.
    pub fn lower_section(
        source: &[u8],
        plan: &NativeFormHwpxPlan,
        flow: &str,
        domain_limits: FormControlLimits,
        limits: NativeFormHwpxLimits,
    ) -> Result<(Vec<u8>, NativeFormHwpxLoweringReceipt), NativeFormHwpxError> {
        let mut unsealed = plan.clone();
        unsealed.plan_sha256.clear();
        if plan.profile_id != NATIVE_FORM_HWPX_PROFILE_ID
            || sha(&bounded_json(&unsealed, limits)?) != plan.plan_sha256
        {
            return Err(NativeFormHwpxError::PlanBinding);
        }
        let parsed = parse(source, &plan.source.map, limits)?;
        if parsed.readback != plan.source {
            return Err(NativeFormHwpxError::PlanBinding);
        }
        parsed
            .readback
            .verify_domain_state(plan.domain_plan.source_state(), domain_limits)?;
        let result = FormControlBuilder::build(
            &plan.domain_plan,
            plan.domain_plan.source_state(),
            flow,
            domain_limits,
        )?;
        validate_transition(
            plan.domain_plan.source_state(),
            &result.state,
            plan.domain_plan.capability_id(),
        )?;
        let edits = edits(
            source,
            &parsed,
            &result.state,
            plan.domain_plan.capability_id(),
            limits,
        )?;
        if edits.is_empty() {
            return Err(NativeFormHwpxError::NonRepresentable);
        }
        let output = apply(source, &edits, limits)?;
        let target = NativeFormHwpxReader::read_section(&output, &plan.source.map, limits)?;
        target.verify_domain_state(&result.state, domain_limits)?;
        for (before, after) in plan.source.controls.iter().zip(&target.controls) {
            if before.native_identity != after.native_identity
                || before.tag != after.tag
                || before.anchor != after.anchor
                || before.geometry_sha256 != after.geometry_sha256
                || before.preserved_opaque_sha256 != after.preserved_opaque_sha256
            {
                return Err(NativeFormHwpxError::Preservation);
            }
        }
        let receipt = NativeFormHwpxLoweringReceipt {
            source_section_sha256: plan.source.section_sha256.clone(),
            output_section_sha256: target.section_sha256.clone(),
            changed_attribute_count: edits.len(),
            outside_declared_edits_byte_exact: true,
            target_readback: target,
        };
        Ok((output, receipt))
    }
}

struct Parsed {
    document: PreservingXmlDocument,
    roots: Vec<usize>,
    readback: NativeFormHwpxReadback,
}
fn parse(
    source: &[u8],
    map: &NativeFormHwpxMap,
    limits: NativeFormHwpxLimits,
) -> Result<Parsed, NativeFormHwpxError> {
    if source.is_empty()
        || source.len() > limits.section_bytes
        || map.component_controls.is_empty()
        || map.component_controls.len() > limits.controls
        || map.paragraph_ids.len() > limits.elements
    {
        return Err(NativeFormHwpxError::InputLimit);
    }
    let document = PreservingXmlDocument::parse(source)?;
    if document.elements().len() > limits.elements
        || document
            .elements()
            .iter()
            .any(|e| e.attributes().len() > 256)
    {
        return Err(NativeFormHwpxError::InputLimit);
    }
    let root = element(&document, 0)?;
    if root.parent().is_some()
        || root.name().namespace() != Some(HS)
        || root.name().local_name() != "sec"
    {
        return Err(NativeFormHwpxError::UnsupportedProfile);
    }
    let paragraphs: Vec<_> = document
        .elements()
        .iter()
        .enumerate()
        .filter(|(_, n)| named(n, "p"))
        .map(|(i, _)| i)
        .collect();
    let roots: Vec<_> = document
        .elements()
        .iter()
        .enumerate()
        .filter(|(_, n)| tag(n.name().local_name()).is_some())
        .map(|(i, _)| i)
        .collect();
    validate_map(map, paragraphs.len(), roots.len())?;
    let mut controls = Vec::new();
    controls
        .try_reserve_exact(roots.len())
        .map_err(|_| NativeFormHwpxError::Allocation)?;
    let mut native_ids = BTreeSet::new();
    let mut native_instances = BTreeSet::new();
    let mut non_form = Sha256::new();
    let mut cursor = 0;
    for (&index, component) in roots.iter().zip(&map.component_controls) {
        let native = observe(
            source,
            &document,
            index,
            component,
            &paragraphs,
            &map.paragraph_ids,
            limits,
        )?;
        if let NativeFormObservedIdentity::Observed {
            object_id,
            instance_id,
            ..
        } = native.native_identity
            && (object_id.is_some_and(|id| !native_ids.insert(id))
                || instance_id.is_some_and(|id| !native_instances.insert(id)))
        {
            return Err(NativeFormHwpxError::ProjectionMismatch);
        }
        let span = element(&document, index)?
            .outer_span()
            .ok_or(NativeFormHwpxError::UnsupportedProfile)?;
        if span.start() < cursor {
            return Err(NativeFormHwpxError::UnsupportedProfile);
        }
        frame(&mut non_form, &source[cursor..span.start()]);
        cursor = span.end();
        controls.push(native);
    }
    frame(&mut non_form, &source[cursor..]);
    document.verify_untouched_round_trip()?;
    Ok(Parsed {
        document,
        roots,
        readback: NativeFormHwpxReadback {
            section_sha256: sha(source),
            map: map.clone(),
            controls,
            non_form_content_sha256: hex(non_form.finalize()),
        },
    })
}

fn validate_map(
    map: &NativeFormHwpxMap,
    paragraph_count: usize,
    control_count: usize,
) -> Result<(), NativeFormHwpxError> {
    if paragraph_count != map.paragraph_ids.len()
        || control_count != map.component_controls.len()
        || map.paragraph_ids.iter().collect::<BTreeSet<_>>().len() != paragraph_count
        || map
            .component_controls
            .iter()
            .map(|c| &c.logical_control_id)
            .collect::<BTreeSet<_>>()
            .len()
            != control_count
        || map
            .component_controls
            .iter()
            .map(|c| c.native_object_id)
            .collect::<BTreeSet<_>>()
            .len()
            != control_count
        || map
            .component_controls
            .iter()
            .any(|c| c.native_object_id == 0)
    {
        return Err(NativeFormHwpxError::ProjectionMismatch);
    }
    Ok(())
}

fn observe(
    source: &[u8],
    document: &PreservingXmlDocument,
    index: usize,
    component: &FormControlIdentity,
    paragraphs: &[usize],
    paragraph_ids: &[LogicalId],
    limits: NativeFormHwpxLimits,
) -> Result<NativeFormControlObservation, NativeFormHwpxError> {
    let node = element(document, index)?;
    if node.name().namespace() != Some(HP) {
        return Err(NativeFormHwpxError::UnsupportedProfile);
    }
    let native_tag =
        tag(node.name().local_name()).ok_or(NativeFormHwpxError::UnsupportedProfile)?;
    let run = node
        .parent()
        .ok_or(NativeFormHwpxError::UnsupportedProfile)?;
    let paragraph = element(document, run)?
        .parent()
        .ok_or(NativeFormHwpxError::UnsupportedProfile)?;
    if !named(element(document, run)?, "run") || !named(element(document, paragraph)?, "p") {
        return Err(NativeFormHwpxError::UnsupportedProfile);
    }
    let paragraph_ordinal = paragraphs
        .iter()
        .position(|&i| i == paragraph)
        .ok_or(NativeFormHwpxError::ProjectionMismatch)?;
    let run_ordinal = children(document, paragraph)?
        .into_iter()
        .filter(|&i| named(&document.elements()[i], "run"))
        .position(|i| i == run)
        .ok_or(NativeFormHwpxError::ProjectionMismatch)?;
    let inline_ordinal = children(document, run)?
        .iter()
        .position(|&i| i == index)
        .ok_or(NativeFormHwpxError::ProjectionMismatch)?;
    let anchor = NativeFormPhysicalAnchor {
        paragraph_id: paragraph_ids[paragraph_ordinal].clone(),
        paragraph_ordinal,
        paragraph_child_path: child_path(document, paragraph)?,
        run_ordinal: u32::try_from(run_ordinal).map_err(|_| NativeFormHwpxError::InputLimit)?,
        inline_ordinal: u32::try_from(inline_ordinal)
            .map_err(|_| NativeFormHwpxError::InputLimit)?,
    };
    let native_identity = identity(source, node, limits)?;
    let character_index = child(document, index, "formCharPr")?;
    let character = element(document, character_index)?;
    let common = common(source, node, character, limits)?;
    let mut geometry = Sha256::new();
    for name in ["sz", "pos", "outMargin"] {
        let i = child(document, index, name)?;
        if element(document, i)?.first_child().is_some() {
            return Err(NativeFormHwpxError::UnsupportedProfile);
        }
        frame(&mut geometry, outer(source, element(document, i)?)?);
    }
    let shape_locked = boolean(
        source,
        element(document, child(document, index, "sz")?)?,
        "protect",
        limits,
    )?;
    let mut opaque = Sha256::new();
    frame(&mut opaque, node.name().qualified_name().as_bytes());
    opaque_attributes(source, node, &COMMON, &mut opaque)?;
    opaque_child_gaps(source, document, index, &mut opaque)?;
    for i in children(document, index)? {
        if i == character_index {
            frame(&mut opaque, character.name().qualified_name().as_bytes());
            opaque_attributes(source, character, &CHARACTER, &mut opaque)?;
            if let Some(span) = character.content_span() {
                frame(&mut opaque, &source[span.start()..span.end()]);
            }
            if let Some(span) = character.end_tag_span() {
                frame(&mut opaque, &source[span.start()..span.end()]);
            }
        } else {
            frame(&mut opaque, outer(source, element(document, i)?)?);
        }
    }
    Ok(NativeFormControlObservation {
        component_identity: component.clone(),
        native_identity,
        tag: native_tag,
        anchor,
        common,
        payload: payload(source, document, index, native_tag, limits)?,
        shape_locked,
        geometry_sha256: hex(geometry.finalize()),
        preserved_opaque_sha256: hex(opaque.finalize()),
        raw_control_sha256: sha(outer(source, node)?),
    })
}

fn common(
    source: &[u8],
    node: &XmlElementToken,
    character: &XmlElementToken,
    limits: NativeFormHwpxLimits,
) -> Result<FormCommonProperties, NativeFormHwpxError> {
    Ok(FormCommonProperties {
        name: value(source, node, "name", limits)?,
        fore_color_rgb: color(source, node, "foreColor", limits)?,
        back_color_rgb: color(source, node, "backColor", limits)?,
        group_name: optional_text(source, node, "groupName", limits)?,
        tab_stop: boolean(source, node, "tabStop", limits)?,
        tab_order: signed_option(source, node, "tabOrder", limits)?,
        editable: boolean(source, node, "editable", limits)?,
        enabled: boolean(source, node, "enabled", limits)?,
        border_type_id_ref: uint(source, node, "borderTypeIDRef", limits)?,
        draw_frame: boolean(source, node, "drawFrame", limits)?,
        printable: boolean(source, node, "printable", limits)?,
        command_sha256: optional_text(source, node, "command", limits)?.map(|v| sha(v.as_bytes())),
        character: FormCharacterProperties {
            char_pr_id_ref: uint(source, character, "charPrIDRef", limits)?,
            follow_context: boolean(source, character, "followContext", limits)?,
            auto_size: boolean(source, character, "autoSz", limits)?,
            word_wrap: boolean(source, character, "wordWrap", limits)?,
        },
    })
}

fn identity(
    source: &[u8],
    node: &XmlElementToken,
    limits: NativeFormHwpxLimits,
) -> Result<NativeFormObservedIdentity, NativeFormHwpxError> {
    let object_id = attr(node, "id")?
        .map(|_| uint(source, node, "id", limits))
        .transpose()?;
    let lower = attr(node, "instid")?;
    let camel = attr(node, "instId")?;
    if lower.is_some() && camel.is_some() {
        return Err(NativeFormHwpxError::Attribute);
    }
    let instance_attribute = if lower.is_some() {
        Some("instid")
    } else if camel.is_some() {
        Some("instId")
    } else {
        None
    };
    let instance_id = instance_attribute
        .map(|key| uint(source, node, key, limits))
        .transpose()?;
    if object_id.is_none() && instance_id.is_none() {
        Ok(NativeFormObservedIdentity::Missing)
    } else {
        Ok(NativeFormObservedIdentity::Observed {
            object_id,
            instance_id,
            instance_attribute: instance_attribute.map(str::to_owned),
        })
    }
}

fn payload(
    source: &[u8],
    document: &PreservingXmlDocument,
    index: usize,
    native_tag: NativeFormTag,
    limits: NativeFormHwpxLimits,
) -> Result<NativeFormObservedPayload, NativeFormHwpxError> {
    let node = element(document, index)?;
    Ok(match native_tag {
        NativeFormTag::Edit => NativeFormObservedPayload::Text {
            value: text(
                source,
                element(document, child(document, index, "text")?)?,
                limits,
            )?,
            multi_line: boolean(source, node, "multiLine", limits)?,
            password_character: optional_text(source, node, "passwordChar", limits)?,
            native_max_length: match uint(source, node, "maxLength", limits)? {
                0 => None,
                n => Some(n),
            },
            scroll_bars: match value(source, node, "scrollBars", limits)?.as_str() {
                "NONE" => FormScrollBars::None,
                "VERTICAL" => FormScrollBars::Vertical,
                "HORIZONTAL" => FormScrollBars::Horizontal,
                "BOTH" => FormScrollBars::Both,
                _ => return Err(NativeFormHwpxError::Attribute),
            },
            tab_key_behavior: match value(source, node, "tabKeyBehavior", limits)?.as_str() {
                "NEXT_OBJECT" => FormTabKeyBehavior::NextObject,
                "INSERT_TAB" => FormTabKeyBehavior::InsertTab,
                _ => return Err(NativeFormHwpxError::Attribute),
            },
            number_only: boolean(source, node, "numOnly", limits)?,
            read_only: boolean(source, node, "readOnly", limits)?,
            alignment: match value(source, node, "alignText", limits)?.as_str() {
                "LEFT" => FormTextAlignment::Left,
                "CENTER" => FormTextAlignment::Center,
                "RIGHT" => FormTextAlignment::Right,
                _ => return Err(NativeFormHwpxError::Attribute),
            },
        },
        NativeFormTag::CheckBtn | NativeFormTag::RadioBtn => NativeFormObservedPayload::Button {
            caption: value(source, node, "caption", limits)?,
            value: match value(source, node, "value", limits)?.as_str() {
                "UNCHECKED" => FormButtonValue::Unchecked,
                "CHECKED" => FormButtonValue::Checked,
                "INDETERMINATE" => FormButtonValue::Indeterminate,
                _ => return Err(NativeFormHwpxError::Attribute),
            },
            radio_group_name: optional_text(source, node, "radioGroupName", limits)?,
            tri_state: boolean(source, node, "triState", limits)?,
            back_style: match value(source, node, "backStyle", limits)?.as_str() {
                "TRANSPARENT" => FormButtonBackStyle::Transparent,
                "OPAQUE" => FormButtonBackStyle::Opaque,
                _ => return Err(NativeFormHwpxError::Attribute),
            },
        },
        NativeFormTag::ComboBox => NativeFormObservedPayload::Combo {
            items: items(source, document, index, limits)?,
            selected_value: optional_text(source, node, "selectedValue", limits)?,
            list_box_rows: signed_option(source, node, "listBoxRows", limits)?,
            list_box_width_hwp_units: signed_option(source, node, "listBoxWidth", limits)?,
            edit_enable: boolean(source, node, "editEnable", limits)?,
        },
        NativeFormTag::ListBox => NativeFormObservedPayload::List {
            items: items(source, document, index, limits)?,
            selected_value: optional_text(source, node, "selectedValue", limits)?,
            item_height_hwp_units: signed_option(source, node, "itemHeight", limits)?,
            top_index: uint(source, node, "topIdx", limits)?,
        },
    })
}

fn payload_matches(observed: &NativeFormObservedPayload, expected: &FormControlPayload) -> bool {
    let projected = match expected {
        FormControlPayload::Text {
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
        } => NativeFormObservedPayload::Text {
            value: value.clone(),
            multi_line: *multi_line,
            password_character: password_character.clone(),
            native_max_length: *native_max_length,
            scroll_bars: *scroll_bars,
            tab_key_behavior: *tab_key_behavior,
            number_only: *number_only,
            read_only: *read_only,
            alignment: *alignment,
        },
        FormControlPayload::Checkbox {
            caption,
            value,
            radio_group_name,
            tri_state,
            back_style,
            ..
        } => NativeFormObservedPayload::Button {
            caption: caption.clone(),
            value: *value,
            radio_group_name: radio_group_name.clone(),
            tri_state: *tri_state,
            back_style: *back_style,
        },
        FormControlPayload::Radio {
            caption,
            value,
            radio_group_name,
            tri_state,
            back_style,
            ..
        } => NativeFormObservedPayload::Button {
            caption: caption.clone(),
            value: *value,
            radio_group_name: Some(radio_group_name.clone()),
            tri_state: *tri_state,
            back_style: *back_style,
        },
        FormControlPayload::Combo {
            items,
            selected_value,
            list_box_rows,
            list_box_width_hwp_units,
            edit_enable,
            ..
        } => NativeFormObservedPayload::Combo {
            items: items.clone(),
            selected_value: selected_value.clone(),
            list_box_rows: *list_box_rows,
            list_box_width_hwp_units: *list_box_width_hwp_units,
            edit_enable: *edit_enable,
        },
        FormControlPayload::List {
            items,
            selected_value,
            item_height_hwp_units,
            top_index,
            ..
        } => NativeFormObservedPayload::List {
            items: items.clone(),
            selected_value: selected_value.clone(),
            item_height_hwp_units: *item_height_hwp_units,
            top_index: *top_index,
        },
        FormControlPayload::Date { .. } => return false,
    };
    observed == &projected
}

fn validate_transition(
    source: &FormDocumentState,
    target: &FormDocumentState,
    capability: &str,
) -> Result<(), NativeFormHwpxError> {
    if source.controls().len() != target.controls().len()
        || !matches!(capability, "ref.form_properties" | "ref.form_tab_order")
    {
        return Err(NativeFormHwpxError::NonRepresentable);
    }
    let mut changed = 0;
    for (before, after) in source.controls().iter().zip(target.controls()) {
        if before == after {
            continue;
        }
        changed += 1;
        let mut admitted = before.clone();
        if capability == "ref.form_properties" {
            if before.common.command_sha256 != after.common.command_sha256 {
                return Err(NativeFormHwpxError::NonRepresentable);
            }
            admitted.common = after.common.clone();
        } else {
            admitted.common.tab_stop = after.common.tab_stop;
            admitted.common.tab_order = after.common.tab_order;
        }
        if &admitted != after {
            return Err(NativeFormHwpxError::NonRepresentable);
        }
    }
    if changed == 0 || (capability == "ref.form_properties" && changed != 1) {
        return Err(NativeFormHwpxError::NonRepresentable);
    }
    Ok(())
}

struct Edit {
    start: usize,
    end: usize,
    replacement: Vec<u8>,
}
fn edits(
    source: &[u8],
    parsed: &Parsed,
    target: &FormDocumentState,
    capability: &str,
    limits: NativeFormHwpxLimits,
) -> Result<Vec<Edit>, NativeFormHwpxError> {
    let mut edits = Vec::new();
    for ((&root, before), after) in parsed
        .roots
        .iter()
        .zip(&parsed.readback.controls)
        .zip(target.controls())
    {
        let node = element(&parsed.document, root)?;
        let common = &after.common;
        let values = [
            common.name.clone(),
            format!("#{:06X}", common.fore_color_rgb),
            format!("#{:06X}", common.back_color_rgb),
            common.group_name.clone().unwrap_or_default(),
            bit(common.tab_stop),
            bit(common.editable),
            common
                .tab_order
                .map_or_else(|| "-1".into(), |n| n.to_string()),
            bit(common.enabled),
            common.border_type_id_ref.to_string(),
            bit(common.draw_frame),
            bit(common.printable),
        ];
        for (name, replacement) in COMMON.iter().zip(&values) {
            if capability == "ref.form_tab_order" && !matches!(*name, "tabStop" | "tabOrder") {
                continue;
            }
            push_edit(source, node, name, replacement, limits, &mut edits)?;
        }
        if capability == "ref.form_properties" && before.common.character != common.character {
            let character = element(
                &parsed.document,
                child(&parsed.document, root, "formCharPr")?,
            )?;
            let values = [
                common.character.char_pr_id_ref.to_string(),
                bit(common.character.follow_context),
                bit(common.character.auto_size),
                bit(common.character.word_wrap),
            ];
            for (name, replacement) in CHARACTER.iter().zip(values) {
                push_edit(source, character, name, &replacement, limits, &mut edits)?;
            }
        }
    }
    edits.sort_by_key(|e| (e.start, e.end));
    Ok(edits)
}
fn push_edit(
    source: &[u8],
    node: &XmlElementToken,
    name: &str,
    replacement: &str,
    limits: NativeFormHwpxLimits,
    edits: &mut Vec<Edit>,
) -> Result<(), NativeFormHwpxError> {
    if replacement.len() > limits.text_bytes || replacement.chars().any(|c| !matches!(c as u32, 0x9 | 0xA | 0xD | 0x20..=0xD7FF | 0xE000..=0xFFFD | 0x0001_0000..=0x0010_FFFF)) { return Err(NativeFormHwpxError::InputLimit); }
    let escaped = replacement
        .replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
        .replace('\'', "&apos;");
    let edit = if let Some(attribute) = attr(node, name)? {
        let span = attribute.value_span();
        if source.get(span.start()..span.end()) == Some(escaped.as_bytes()) {
            return Ok(());
        }
        Edit {
            start: span.start(),
            end: span.end(),
            replacement: escaped.into_bytes(),
        }
    } else if name == "groupName" {
        if replacement.is_empty() {
            return Ok(());
        }
        let end = node.start_tag_span().end();
        let offset = end
            .checked_sub(if source.get(end.saturating_sub(2)..end) == Some(b"/>") {
                2
            } else {
                1
            })
            .ok_or(NativeFormHwpxError::Attribute)?;
        Edit {
            start: offset,
            end: offset,
            replacement: format!(" groupName=\"{escaped}\"").into_bytes(),
        }
    } else {
        return Err(NativeFormHwpxError::Attribute);
    };
    edits
        .try_reserve(1)
        .map_err(|_| NativeFormHwpxError::Allocation)?;
    edits.push(edit);
    Ok(())
}
fn apply(
    source: &[u8],
    edits: &[Edit],
    limits: NativeFormHwpxLimits,
) -> Result<Vec<u8>, NativeFormHwpxError> {
    let mut length = source.len();
    let mut cursor = 0;
    for edit in edits {
        if edit.start < cursor || edit.start > edit.end || edit.end > source.len() {
            return Err(NativeFormHwpxError::Preservation);
        }
        length = length
            .checked_sub(edit.end - edit.start)
            .and_then(|n| n.checked_add(edit.replacement.len()))
            .ok_or(NativeFormHwpxError::InputLimit)?;
        cursor = edit.end;
    }
    if length > limits.section_bytes {
        return Err(NativeFormHwpxError::InputLimit);
    }
    let mut output = Vec::new();
    output
        .try_reserve_exact(length)
        .map_err(|_| NativeFormHwpxError::Allocation)?;
    cursor = 0;
    for edit in edits {
        output.extend_from_slice(&source[cursor..edit.start]);
        output.extend_from_slice(&edit.replacement);
        cursor = edit.end;
    }
    output.extend_from_slice(&source[cursor..]);
    cursor = 0;
    let mut out_cursor = 0;
    for edit in edits {
        let unchanged = edit.start - cursor;
        if output.get(out_cursor..out_cursor + unchanged) != source.get(cursor..edit.start) {
            return Err(NativeFormHwpxError::Preservation);
        }
        out_cursor += unchanged;
        if output.get(out_cursor..out_cursor + edit.replacement.len())
            != Some(edit.replacement.as_slice())
        {
            return Err(NativeFormHwpxError::Preservation);
        }
        out_cursor += edit.replacement.len();
        cursor = edit.end;
    }
    if output.len() != length || output.get(out_cursor..) != source.get(cursor..) {
        return Err(NativeFormHwpxError::Preservation);
    }
    Ok(output)
}

fn element(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<&XmlElementToken, NativeFormHwpxError> {
    document
        .elements()
        .get(index)
        .ok_or(NativeFormHwpxError::UnsupportedProfile)
}
fn named(node: &XmlElementToken, name: &str) -> bool {
    node.name().namespace() == Some(HP) && node.name().local_name() == name
}
fn tag(name: &str) -> Option<NativeFormTag> {
    match name {
        "edit" => Some(NativeFormTag::Edit),
        "checkBtn" => Some(NativeFormTag::CheckBtn),
        "radioBtn" => Some(NativeFormTag::RadioBtn),
        "comboBox" => Some(NativeFormTag::ComboBox),
        "listBox" => Some(NativeFormTag::ListBox),
        _ => None,
    }
}
fn children(
    document: &PreservingXmlDocument,
    parent: usize,
) -> Result<Vec<usize>, NativeFormHwpxError> {
    let mut result = Vec::new();
    let mut child = element(document, parent)?.first_child();
    while let Some(index) = child {
        result
            .try_reserve(1)
            .map_err(|_| NativeFormHwpxError::Allocation)?;
        result.push(index);
        child = element(document, index)?.next_sibling();
    }
    Ok(result)
}
fn child(
    document: &PreservingXmlDocument,
    parent: usize,
    name: &str,
) -> Result<usize, NativeFormHwpxError> {
    let candidates: Vec<_> = children(document, parent)?
        .into_iter()
        .filter(|&i| document.elements()[i].name().local_name() == name)
        .collect();
    if candidates.len() != 1 || !named(&document.elements()[candidates[0]], name) {
        return Err(NativeFormHwpxError::UnsupportedProfile);
    }
    Ok(candidates[0])
}
fn child_path(
    document: &PreservingXmlDocument,
    mut index: usize,
) -> Result<Vec<usize>, NativeFormHwpxError> {
    let mut path = Vec::new();
    while let Some(parent) = element(document, index)?.parent() {
        if path.len() >= 64 {
            return Err(NativeFormHwpxError::InputLimit);
        }
        path.push(
            children(document, parent)?
                .iter()
                .position(|&i| i == index)
                .ok_or(NativeFormHwpxError::UnsupportedProfile)?,
        );
        index = parent;
    }
    path.reverse();
    Ok(path)
}
fn attr<'a>(
    node: &'a XmlElementToken,
    name: &str,
) -> Result<Option<&'a XmlAttributeToken>, NativeFormHwpxError> {
    let mut candidates = node
        .attributes()
        .iter()
        .filter(|a| !a.is_namespace_declaration() && a.name().local_name() == name);
    let found = candidates.next();
    if found.is_some_and(|a| a.name().namespace().is_some()) || candidates.next().is_some() {
        return Err(NativeFormHwpxError::Attribute);
    }
    Ok(found)
}
fn decoded(
    source: &[u8],
    attribute: &XmlAttributeToken,
    limits: NativeFormHwpxLimits,
) -> Result<String, NativeFormHwpxError> {
    let span = attribute.value_span();
    let raw = std::str::from_utf8(
        source
            .get(span.start()..span.end())
            .ok_or(NativeFormHwpxError::Attribute)?,
    )
    .map_err(|_| NativeFormHwpxError::Attribute)?;
    if raw.len() > limits.text_bytes {
        return Err(NativeFormHwpxError::InputLimit);
    }
    Ok(unescape(raw)
        .map_err(|_| NativeFormHwpxError::Attribute)?
        .into_owned())
}
fn value(
    source: &[u8],
    node: &XmlElementToken,
    name: &str,
    limits: NativeFormHwpxLimits,
) -> Result<String, NativeFormHwpxError> {
    decoded(
        source,
        attr(node, name)?.ok_or(NativeFormHwpxError::Attribute)?,
        limits,
    )
}
fn optional_text(
    source: &[u8],
    node: &XmlElementToken,
    name: &str,
    limits: NativeFormHwpxLimits,
) -> Result<Option<String>, NativeFormHwpxError> {
    Ok(attr(node, name)?
        .map(|a| decoded(source, a, limits))
        .transpose()?
        .filter(|v| !v.is_empty()))
}
fn parse_u32(value: &str) -> Result<u32, NativeFormHwpxError> {
    if value.is_empty()
        || !value.bytes().all(|c| c.is_ascii_digit())
        || (value != "0" && value.starts_with('0'))
    {
        return Err(NativeFormHwpxError::Attribute);
    }
    value.parse().map_err(|_| NativeFormHwpxError::Attribute)
}
fn uint(
    source: &[u8],
    node: &XmlElementToken,
    name: &str,
    limits: NativeFormHwpxLimits,
) -> Result<u32, NativeFormHwpxError> {
    parse_u32(&value(source, node, name, limits)?)
}
fn signed_option(
    source: &[u8],
    node: &XmlElementToken,
    name: &str,
    limits: NativeFormHwpxLimits,
) -> Result<Option<u32>, NativeFormHwpxError> {
    let value = value(source, node, name, limits)?;
    if value == "-1" {
        Ok(None)
    } else {
        Ok(Some(parse_u32(&value)?))
    }
}
fn boolean(
    source: &[u8],
    node: &XmlElementToken,
    name: &str,
    limits: NativeFormHwpxLimits,
) -> Result<bool, NativeFormHwpxError> {
    match value(source, node, name, limits)?.as_str() {
        "0" => Ok(false),
        "1" => Ok(true),
        _ => Err(NativeFormHwpxError::Attribute),
    }
}
fn color(
    source: &[u8],
    node: &XmlElementToken,
    name: &str,
    limits: NativeFormHwpxLimits,
) -> Result<u32, NativeFormHwpxError> {
    let color = value(source, node, name, limits)?;
    if color.len() != 7
        || !color.starts_with('#')
        || !color[1..]
            .bytes()
            .all(|c| c.is_ascii_digit() || (b'A'..=b'F').contains(&c))
    {
        return Err(NativeFormHwpxError::Attribute);
    }
    u32::from_str_radix(&color[1..], 16).map_err(|_| NativeFormHwpxError::Attribute)
}
fn text(
    source: &[u8],
    node: &XmlElementToken,
    limits: NativeFormHwpxLimits,
) -> Result<String, NativeFormHwpxError> {
    if node.first_child().is_some() {
        return Err(NativeFormHwpxError::UnsupportedProfile);
    }
    if node.is_empty() {
        return Ok(String::new());
    }
    let span = node
        .content_span()
        .ok_or(NativeFormHwpxError::UnsupportedProfile)?;
    let raw = std::str::from_utf8(&source[span.start()..span.end()])
        .map_err(|_| NativeFormHwpxError::Attribute)?;
    if raw.len() > limits.text_bytes || raw.contains('<') {
        return Err(NativeFormHwpxError::UnsupportedProfile);
    }
    Ok(unescape(raw)
        .map_err(|_| NativeFormHwpxError::Attribute)?
        .into_owned())
}
fn items(
    source: &[u8],
    document: &PreservingXmlDocument,
    root: usize,
    limits: NativeFormHwpxLimits,
) -> Result<Vec<FormListItem>, NativeFormHwpxError> {
    let indices: Vec<_> = children(document, root)?
        .into_iter()
        .filter(|&i| document.elements()[i].name().local_name() == "listItem")
        .collect();
    if indices.len() > limits.controls {
        return Err(NativeFormHwpxError::InputLimit);
    }
    indices
        .into_iter()
        .map(|i| {
            let node = element(document, i)?;
            if !named(node, "listItem") || node.first_child().is_some() {
                return Err(NativeFormHwpxError::UnsupportedProfile);
            }
            Ok(FormListItem {
                display_text: value(source, node, "displayText", limits)?,
                value: value(source, node, "value", limits)?,
            })
        })
        .collect()
}
fn outer<'a>(source: &'a [u8], node: &XmlElementToken) -> Result<&'a [u8], NativeFormHwpxError> {
    let span = node
        .outer_span()
        .ok_or(NativeFormHwpxError::UnsupportedProfile)?;
    source
        .get(span.start()..span.end())
        .ok_or(NativeFormHwpxError::UnsupportedProfile)
}
fn opaque_attributes(
    source: &[u8],
    node: &XmlElementToken,
    editable: &[&str],
    hash: &mut Sha256,
) -> Result<(), NativeFormHwpxError> {
    for attribute in node.attributes() {
        if !attribute.is_namespace_declaration()
            && attribute.name().namespace().is_none()
            && editable.contains(&attribute.name().local_name())
        {
            continue;
        }
        let span = attribute.span();
        frame(
            hash,
            source
                .get(span.start()..span.end())
                .ok_or(NativeFormHwpxError::Attribute)?,
        );
    }
    Ok(())
}
fn opaque_child_gaps(
    source: &[u8],
    document: &PreservingXmlDocument,
    root: usize,
    hash: &mut Sha256,
) -> Result<(), NativeFormHwpxError> {
    let Some(span) = element(document, root)?.content_span() else {
        return Ok(());
    };
    let mut cursor = span.start();
    for index in children(document, root)? {
        let child = element(document, index)?
            .outer_span()
            .ok_or(NativeFormHwpxError::UnsupportedProfile)?;
        if child.start() < cursor || child.end() > span.end() {
            return Err(NativeFormHwpxError::UnsupportedProfile);
        }
        frame(hash, &source[cursor..child.start()]);
        cursor = child.end();
    }
    frame(hash, &source[cursor..span.end()]);
    Ok(())
}
fn bounded_json<T: Serialize>(
    value: &T,
    limits: NativeFormHwpxLimits,
) -> Result<Vec<u8>, NativeFormHwpxError> {
    let raw = serde_json::to_vec(value).map_err(|_| NativeFormHwpxError::PlanBinding)?;
    if raw.len() > limits.plan_bytes {
        return Err(NativeFormHwpxError::InputLimit);
    }
    Ok(raw)
}
fn bit(value: bool) -> String {
    if value { "1".into() } else { "0".into() }
}
fn frame(hash: &mut Sha256, bytes: &[u8]) {
    hash.update((bytes.len() as u64).to_le_bytes());
    hash.update(bytes);
}
fn sha(bytes: &[u8]) -> String {
    hex(Sha256::digest(bytes))
}
fn hex(bytes: impl AsRef<[u8]>) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(bytes.as_ref().len() * 2);
    for &byte in bytes.as_ref() {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 15)]));
    }
    output
}
