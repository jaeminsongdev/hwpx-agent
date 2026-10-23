//! Object-bound caption composition over the existing closed DIGIT field adapter.

use std::fmt;

use domain_ir::{
    FieldDefinition, FieldDocumentState, FieldEngineLimits, FieldNumberFormat, FieldPlan,
    LogicalId, ObjectNumberKind,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::field_auto_number_hwpx::{
    FieldAutoNumberHwpxBuilder, FieldAutoNumberHwpxError, FieldAutoNumberHwpxLimits,
    FieldAutoNumberHwpxLowerer, FieldAutoNumberHwpxLoweringReceipt, FieldAutoNumberHwpxPlan,
    FieldAutoNumberHwpxReader,
};
use crate::preserving_xml::{
    PreservingXmlDocument, PreservingXmlError, XmlByteSpan, XmlElementToken,
};

pub const FIELD_OBJECT_CAPTION_HWPX_PROFILE_ID: &str =
    "hwpx-agent.field-object-caption-hwpx.hwpml-2011-digit/v1";
const PARA_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const SECTION_NS: &str = "http://www.hancom.co.kr/hwpml/2011/section";

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct FieldObjectCaptionHwpxTarget {
    pub logical_object_id: LogicalId,
    pub native_object_id: u32,
    pub object_kind: ObjectNumberKind,
}

impl fmt::Debug for FieldObjectCaptionHwpxTarget {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("FieldObjectCaptionHwpxTarget(<redacted>)")
    }
}

/// Complete field state and paragraph map for the selected object's caption scope.
pub struct FieldObjectCaptionHwpxContext<'a> {
    pub target: &'a FieldObjectCaptionHwpxTarget,
    pub state: &'a FieldDocumentState,
    pub document_flow_sha256: &'a str,
    pub caption_paragraph_ids: &'a [LogicalId],
    pub state_limits: FieldEngineLimits,
    pub hwpx_limits: FieldAutoNumberHwpxLimits,
}

impl fmt::Debug for FieldObjectCaptionHwpxContext<'_> {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("FieldObjectCaptionHwpxContext(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct FieldObjectCaptionHwpxReadback {
    pub state: FieldDocumentState,
    pub section_sha256: [u8; 32],
    pub object_sha256: [u8; 32],
    pub caption_sha256: [u8; 32],
    pub auto_number_count: usize,
}

impl fmt::Debug for FieldObjectCaptionHwpxReadback {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FieldObjectCaptionHwpxReadback")
            .field("auto_number_count", &self.auto_number_count)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Serialize)]
pub struct FieldObjectCaptionHwpxPlan {
    profile_id: &'static str,
    source_section_sha256: [u8; 32],
    source_object_sha256: [u8; 32],
    source_caption_sha256: [u8; 32],
    target: FieldObjectCaptionHwpxTarget,
    inner: FieldAutoNumberHwpxPlan,
    plan_sha256: String,
}

impl FieldObjectCaptionHwpxPlan {
    #[must_use]
    pub fn plan_sha256(&self) -> &str {
        &self.plan_sha256
    }

    /// Serializes the sealed composition plan with finite limits.
    ///
    /// # Errors
    /// Rejects serialization and output-limit failures.
    pub fn canonical_json(
        &self,
        limits: FieldAutoNumberHwpxLimits,
    ) -> Result<Vec<u8>, FieldObjectCaptionHwpxError> {
        serialize(self, limits)
    }
}

impl fmt::Debug for FieldObjectCaptionHwpxPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FieldObjectCaptionHwpxPlan")
            .field("profile_id", &self.profile_id)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone)]
pub struct FieldObjectCaptionHwpxLoweringReceipt {
    pub profile_id: &'static str,
    pub source_section_sha256: [u8; 32],
    pub output_section_sha256: [u8; 32],
    pub source_object_sha256: [u8; 32],
    pub output_object_sha256: [u8; 32],
    pub source_caption_sha256: [u8; 32],
    pub output_caption_sha256: [u8; 32],
    pub plan_sha256: String,
    pub inner: FieldAutoNumberHwpxLoweringReceipt,
}

impl fmt::Debug for FieldObjectCaptionHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FieldObjectCaptionHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum FieldObjectCaptionHwpxError {
    #[error("object-caption number source exceeds its finite limits")]
    InputLimit,
    #[error("object-caption number target identity is missing or ambiguous")]
    InvalidTarget,
    #[error("object-caption number structure or namespace scope is unsupported")]
    UnsupportedStructure,
    #[error("object-caption number kind or state does not match the selected object")]
    KindMismatch,
    #[error("object-caption number source or selector drifted")]
    SourceDrift,
    #[error("object-caption number composition plan was tampered with")]
    PlanTampered,
    #[error("object-caption number preserving splice failed")]
    PreservationMismatch,
    #[error("object-caption number output exceeds its finite limit")]
    OutputLimit,
    #[error("object-caption number allocation failed")]
    AllocationFailed,
    #[error("object-caption number serialization failed")]
    SerializationFailed,
    #[error(transparent)]
    Field(#[from] FieldAutoNumberHwpxError),
    #[error(transparent)]
    Xml(#[from] PreservingXmlError),
}

#[derive(Debug)]
pub struct FieldObjectCaptionHwpxReader;

impl FieldObjectCaptionHwpxReader {
    /// Resolves caption styles without treating native field-pair IDs as object IDs.
    ///
    /// # Errors
    /// Rejects missing/ambiguous objects, captions, namespaces, and style anchors.
    pub fn style_sha256_at(
        source: &[u8],
        target: &FieldObjectCaptionHwpxTarget,
        paragraph_ordinal: u32,
        run_ordinal: u32,
        limits: FieldAutoNumberHwpxLimits,
    ) -> Result<(String, String), FieldObjectCaptionHwpxError> {
        let scope = caption_scope(source, target, limits)?;
        Ok(FieldAutoNumberHwpxReader::style_sha256_at(
            &scope.view,
            paragraph_ordinal,
            run_ordinal,
            limits,
        )?)
    }

    /// Reads the complete caption field scope while binding the full original section.
    ///
    /// # Errors
    /// Rejects wrong object/number kinds, incomplete maps and all legacy field-adapter errors.
    pub fn read_section(
        source: &[u8],
        context: &FieldObjectCaptionHwpxContext<'_>,
    ) -> Result<FieldObjectCaptionHwpxReadback, FieldObjectCaptionHwpxError> {
        verify_fields(context.state, context.target)?;
        let scope = caption_scope(source, context.target, context.hwpx_limits)?;
        let readback = FieldAutoNumberHwpxReader::read_section(
            &scope.view,
            context.state,
            context.caption_paragraph_ids,
            context.state_limits,
            context.hwpx_limits,
        )?;
        Ok(FieldObjectCaptionHwpxReadback {
            state: readback.state,
            section_sha256: hash(source),
            object_sha256: scope.object_sha256,
            caption_sha256: scope.caption_sha256,
            auto_number_count: readback.auto_number_count,
        })
    }
}

#[derive(Debug)]
pub struct FieldObjectCaptionHwpxBuilder;

impl FieldObjectCaptionHwpxBuilder {
    /// Composes a field-domain insertion/update with one exact native object caption.
    ///
    /// # Errors
    /// Rejects unsupported operations and ambiguous, wrong-kind or stale targets before output.
    pub fn plan(
        source: &[u8],
        context: &FieldObjectCaptionHwpxContext<'_>,
        domain: &FieldPlan,
    ) -> Result<FieldObjectCaptionHwpxPlan, FieldObjectCaptionHwpxError> {
        if !matches!(
            domain.capability_id(),
            "ref.field_object_number" | "ref.field_update"
        ) || domain.source_state() != context.state
            || domain.target_state().fields().len() != 1
        {
            return Err(FieldObjectCaptionHwpxError::KindMismatch);
        }
        verify_fields(context.state, context.target)?;
        verify_fields(domain.target_state(), context.target)?;
        let scope = caption_scope(source, context.target, context.hwpx_limits)?;
        let inner = FieldAutoNumberHwpxBuilder::plan(
            &scope.view,
            context.state,
            domain,
            context.document_flow_sha256,
            context.caption_paragraph_ids,
            context.state_limits,
            context.hwpx_limits,
        )?;
        let mut plan = FieldObjectCaptionHwpxPlan {
            profile_id: FIELD_OBJECT_CAPTION_HWPX_PROFILE_ID,
            source_section_sha256: hash(source),
            source_object_sha256: scope.object_sha256,
            source_caption_sha256: scope.caption_sha256,
            target: context.target.clone(),
            inner,
            plan_sha256: String::new(),
        };
        plan.plan_sha256 = binding_hash(&plan, context.hwpx_limits)?;
        let _ = plan.canonical_json(context.hwpx_limits)?;
        Ok(plan)
    }
}

#[derive(Debug)]
pub struct FieldObjectCaptionHwpxLowerer;

impl FieldObjectCaptionHwpxLowerer {
    /// Applies one legacy field edit only inside the selected caption and verifies outer bytes.
    ///
    /// # Errors
    /// Returns no output on source, selector, field-state/flow/map, plan or preservation failure.
    pub fn lower_section_with_receipt(
        source: &[u8],
        plan: &FieldObjectCaptionHwpxPlan,
        context: &FieldObjectCaptionHwpxContext<'_>,
    ) -> Result<(Vec<u8>, FieldObjectCaptionHwpxLoweringReceipt), FieldObjectCaptionHwpxError> {
        if plan.profile_id != FIELD_OBJECT_CAPTION_HWPX_PROFILE_ID
            || plan.plan_sha256 != binding_hash(plan, context.hwpx_limits)?
        {
            return Err(FieldObjectCaptionHwpxError::PlanTampered);
        }
        if hash(source) != plan.source_section_sha256 || *context.target != plan.target {
            return Err(FieldObjectCaptionHwpxError::SourceDrift);
        }
        verify_fields(context.state, context.target)?;
        verify_fields(plan.inner.domain_plan().target_state(), context.target)?;
        let scope = caption_scope(source, context.target, context.hwpx_limits)?;
        if scope.object_sha256 != plan.source_object_sha256
            || scope.caption_sha256 != plan.source_caption_sha256
        {
            return Err(FieldObjectCaptionHwpxError::SourceDrift);
        }
        let (view, inner) = FieldAutoNumberHwpxLowerer::lower_section_with_receipt(
            &scope.view,
            &plan.inner,
            context.state,
            context.document_flow_sha256,
            context.caption_paragraph_ids,
            context.state_limits,
            context.hwpx_limits,
        )?;
        let view_document = PreservingXmlDocument::parse(&view)?;
        let replacement_span = get(&view_document, view_document.root_element())?
            .content_span()
            .ok_or(FieldObjectCaptionHwpxError::PreservationMismatch)?;
        let replacement = slice(&view, replacement_span)?;
        let expected_bytes = source
            .len()
            .checked_sub(scope.content_span.len())
            .and_then(|size| size.checked_add(replacement.len()))
            .ok_or(FieldObjectCaptionHwpxError::OutputLimit)?;
        if expected_bytes > context.hwpx_limits.config().output_bytes {
            return Err(FieldObjectCaptionHwpxError::OutputLimit);
        }
        let mut output = Vec::new();
        output
            .try_reserve_exact(expected_bytes)
            .map_err(|_| FieldObjectCaptionHwpxError::AllocationFailed)?;
        output.extend_from_slice(&source[..scope.content_span.start()]);
        output.extend_from_slice(replacement);
        output.extend_from_slice(&source[scope.content_span.end()..]);
        if output.len() != expected_bytes
            || output[..scope.content_span.start()] != source[..scope.content_span.start()]
            || output[scope.content_span.start() + replacement.len()..]
                != source[scope.content_span.end()..]
        {
            return Err(FieldObjectCaptionHwpxError::PreservationMismatch);
        }
        let target_context = FieldObjectCaptionHwpxContext {
            state: plan.inner.domain_plan().target_state(),
            document_flow_sha256: plan.inner.domain_plan().target_document_flow_sha256(),
            ..*context
        };
        let readback = FieldObjectCaptionHwpxReader::read_section(&output, &target_context)?;
        Ok((
            output,
            FieldObjectCaptionHwpxLoweringReceipt {
                profile_id: FIELD_OBJECT_CAPTION_HWPX_PROFILE_ID,
                source_section_sha256: plan.source_section_sha256,
                output_section_sha256: readback.section_sha256,
                source_object_sha256: scope.object_sha256,
                output_object_sha256: readback.object_sha256,
                source_caption_sha256: scope.caption_sha256,
                output_caption_sha256: readback.caption_sha256,
                plan_sha256: plan.plan_sha256.clone(),
                inner,
            },
        ))
    }
}

struct CaptionScope {
    view: Vec<u8>,
    content_span: XmlByteSpan,
    object_sha256: [u8; 32],
    caption_sha256: [u8; 32],
}

fn caption_scope(
    source: &[u8],
    target: &FieldObjectCaptionHwpxTarget,
    limits: FieldAutoNumberHwpxLimits,
) -> Result<CaptionScope, FieldObjectCaptionHwpxError> {
    if source.is_empty() || source.len() > limits.config().section_bytes {
        return Err(FieldObjectCaptionHwpxError::InputLimit);
    }
    let document = PreservingXmlDocument::parse(source)?;
    if document.elements().len() > limits.config().elements {
        return Err(FieldObjectCaptionHwpxError::InputLimit);
    }
    let root = get(&document, document.root_element())?;
    if root.name().namespace() != Some(SECTION_NS)
        || root.name().local_name() != "sec"
        || root.is_empty()
    {
        return Err(FieldObjectCaptionHwpxError::UnsupportedStructure);
    }
    let object_index = select_object(&document, target)?;
    let object = get(&document, object_index)?;
    if native_kind(object) != Some(target.object_kind)
        || attribute(object, "numberingType")? != kind_name(target.object_kind)
    {
        return Err(FieldObjectCaptionHwpxError::KindMismatch);
    }
    if attribute(object, "lock")? != "0" {
        return Err(FieldObjectCaptionHwpxError::UnsupportedStructure);
    }
    let caption_index = only_child_named(&document, object_index, "caption")?;
    let caption = get(&document, caption_index)?;
    let sublist_index = only_child_named(&document, caption_index, "subList")?;
    if children(&document, caption_index)? != vec![sublist_index] {
        return Err(FieldObjectCaptionHwpxError::UnsupportedStructure);
    }
    let sublist = get(&document, sublist_index)?;
    let content_span = sublist
        .content_span()
        .ok_or(FieldObjectCaptionHwpxError::UnsupportedStructure)?;
    let mut ancestor = Some(sublist_index);
    while let Some(index) = ancestor {
        if index == document.root_element() {
            break;
        }
        let element = get(&document, index)?;
        if element.attributes().iter().any(|attribute| {
            attribute.is_namespace_declaration()
                && !root.attributes().iter().any(|inherited| {
                    inherited.is_namespace_declaration()
                        && inherited.name() == attribute.name()
                        && inherited.semantic_value() == attribute.semantic_value()
                })
        }) {
            return Err(FieldObjectCaptionHwpxError::UnsupportedStructure);
        }
        ancestor = element.parent();
    }
    let start = slice(source, root.start_tag_span())?;
    let content = slice(source, content_span)?;
    let end = slice(
        source,
        root.end_tag_span()
            .ok_or(FieldObjectCaptionHwpxError::UnsupportedStructure)?,
    )?;
    let size = start
        .len()
        .checked_add(content.len())
        .and_then(|size| size.checked_add(end.len()))
        .ok_or(FieldObjectCaptionHwpxError::InputLimit)?;
    if size > limits.config().section_bytes {
        return Err(FieldObjectCaptionHwpxError::InputLimit);
    }
    let mut view = Vec::new();
    view.try_reserve_exact(size)
        .map_err(|_| FieldObjectCaptionHwpxError::AllocationFailed)?;
    view.extend_from_slice(start);
    view.extend_from_slice(content);
    view.extend_from_slice(end);
    document.verify_untouched_round_trip()?;
    Ok(CaptionScope {
        view,
        content_span,
        object_sha256: hash(slice(
            source,
            object
                .outer_span()
                .ok_or(FieldObjectCaptionHwpxError::UnsupportedStructure)?,
        )?),
        caption_sha256: hash(slice(
            source,
            caption
                .outer_span()
                .ok_or(FieldObjectCaptionHwpxError::UnsupportedStructure)?,
        )?),
    })
}

fn select_object(
    document: &PreservingXmlDocument,
    target: &FieldObjectCaptionHwpxTarget,
) -> Result<usize, FieldObjectCaptionHwpxError> {
    let mut selected = None;
    for (index, element) in document.elements().iter().enumerate() {
        if native_kind(element).is_none() {
            continue;
        }
        let parent = element
            .parent()
            .and_then(|parent| document.elements().get(parent));
        if !parent.is_some_and(|parent| named(parent, "run")) {
            continue;
        }
        let id = attribute(element, "id")?;
        let id_value = id
            .parse::<u32>()
            .map_err(|_| FieldObjectCaptionHwpxError::InvalidTarget)?;
        if id_value.to_string() != id {
            return Err(FieldObjectCaptionHwpxError::InvalidTarget);
        }
        if id_value == target.native_object_id && selected.replace(index).is_some() {
            return Err(FieldObjectCaptionHwpxError::InvalidTarget);
        }
    }
    selected.ok_or(FieldObjectCaptionHwpxError::InvalidTarget)
}

fn verify_fields(
    state: &FieldDocumentState,
    target: &FieldObjectCaptionHwpxTarget,
) -> Result<(), FieldObjectCaptionHwpxError> {
    if state.fields().len() > 1
        || state.fields().iter().any(|field| {
            field.definition
                != (FieldDefinition::ObjectNumber {
                    object_kind: target.object_kind,
                    format: FieldNumberFormat::Digit,
                })
        })
    {
        return Err(FieldObjectCaptionHwpxError::KindMismatch);
    }
    Ok(())
}

fn native_kind(element: &XmlElementToken) -> Option<ObjectNumberKind> {
    if element.name().namespace() != Some(PARA_NS) {
        return None;
    }
    match element.name().local_name() {
        "pic" | "rect" | "ellipse" | "line" | "arc" | "polygon" | "curve" | "connectLine" => {
            Some(ObjectNumberKind::Picture)
        }
        "tbl" => Some(ObjectNumberKind::Table),
        "equation" => Some(ObjectNumberKind::Equation),
        _ => None,
    }
}

fn kind_name(kind: ObjectNumberKind) -> &'static str {
    match kind {
        ObjectNumberKind::Picture => "PICTURE",
        ObjectNumberKind::Table => "TABLE",
        ObjectNumberKind::Equation => "EQUATION",
    }
}

fn named(element: &XmlElementToken, name: &str) -> bool {
    element.name().namespace() == Some(PARA_NS) && element.name().local_name() == name
}

fn attribute<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<&'a str, FieldObjectCaptionHwpxError> {
    let mut attributes = element.attributes().iter().filter(|attribute| {
        !attribute.is_namespace_declaration()
            && attribute.name().namespace().is_none()
            && attribute.name().local_name() == name
    });
    let value = attributes
        .next()
        .ok_or(FieldObjectCaptionHwpxError::UnsupportedStructure)?;
    if attributes.next().is_some() {
        return Err(FieldObjectCaptionHwpxError::UnsupportedStructure);
    }
    Ok(value.semantic_value())
}

fn get(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<&XmlElementToken, FieldObjectCaptionHwpxError> {
    document
        .elements()
        .get(index)
        .ok_or(FieldObjectCaptionHwpxError::UnsupportedStructure)
}

fn children(
    document: &PreservingXmlDocument,
    parent: usize,
) -> Result<Vec<usize>, FieldObjectCaptionHwpxError> {
    let mut values = Vec::new();
    let mut child = get(document, parent)?.first_child();
    while let Some(index) = child {
        values
            .try_reserve(1)
            .map_err(|_| FieldObjectCaptionHwpxError::AllocationFailed)?;
        values.push(index);
        child = get(document, index)?.next_sibling();
    }
    Ok(values)
}

fn only_child_named(
    document: &PreservingXmlDocument,
    parent: usize,
    name: &str,
) -> Result<usize, FieldObjectCaptionHwpxError> {
    let mut selected = None;
    let mut child = get(document, parent)?.first_child();
    while let Some(index) = child {
        let element = get(document, index)?;
        if named(element, name) && selected.replace(index).is_some() {
            return Err(FieldObjectCaptionHwpxError::UnsupportedStructure);
        }
        child = element.next_sibling();
    }
    selected.ok_or(FieldObjectCaptionHwpxError::UnsupportedStructure)
}

fn slice(source: &[u8], span: XmlByteSpan) -> Result<&[u8], FieldObjectCaptionHwpxError> {
    source
        .get(span.start()..span.end())
        .ok_or(FieldObjectCaptionHwpxError::PreservationMismatch)
}

fn hash(source: &[u8]) -> [u8; 32] {
    Sha256::digest(source).into()
}

fn serialize(
    plan: &FieldObjectCaptionHwpxPlan,
    limits: FieldAutoNumberHwpxLimits,
) -> Result<Vec<u8>, FieldObjectCaptionHwpxError> {
    let bytes =
        serde_json::to_vec(plan).map_err(|_| FieldObjectCaptionHwpxError::SerializationFailed)?;
    if bytes.len() > limits.config().plan_bytes {
        return Err(FieldObjectCaptionHwpxError::OutputLimit);
    }
    Ok(bytes)
}

fn binding_hash(
    plan: &FieldObjectCaptionHwpxPlan,
    limits: FieldAutoNumberHwpxLimits,
) -> Result<String, FieldObjectCaptionHwpxError> {
    let mut binding = plan.clone();
    binding.plan_sha256.clear();
    let digits = b"0123456789abcdef";
    Ok(hash(&serialize(&binding, limits)?)
        .iter()
        .flat_map(|byte| {
            [
                char::from(digits[usize::from(byte >> 4)]),
                char::from(digits[usize::from(byte & 15)]),
            ]
        })
        .collect())
}

#[cfg(test)]
#[allow(clippy::expect_used)]
mod tests {
    use super::*;
    use crate::FieldAutoNumberHwpxLimitConfig;
    use domain_ir::{
        FIELD_ENGINE_SCHEMA_VERSION, FieldAnchor, FieldCacheStatus, FieldCachedResult,
        FieldDocumentStateDraft, FieldEngineBuilder, FieldEngineLimitConfig, FieldIdentity,
        FieldOperation, FieldRequest, FieldRequestDraft, FieldState, FieldUpdatePolicy,
    };

    const FLOW: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";

    #[test]
    fn sealed_composition_target_and_source_hash_tampering_are_rejected() {
        let source = br#"<s:sec xmlns:s="http://www.hancom.co.kr/hwpml/2011/section" xmlns:p="http://www.hancom.co.kr/hwpml/2011/paragraph"><p:p><p:run><p:tbl id="10" numberingType="TABLE" lock="0"><p:caption><p:subList><p:p><p:run><p:t>Label</p:t></p:run></p:p></p:subList></p:caption></p:tbl></p:run></p:p></s:sec>"#;
        let limits =
            FieldEngineLimits::new(FieldEngineLimitConfig::default()).expect("state limits");
        let hwpx = FieldAutoNumberHwpxLimits::new(FieldAutoNumberHwpxLimitConfig::default())
            .expect("hwpx limits");
        let id = |value| LogicalId::parse(value).expect("id");
        let target = FieldObjectCaptionHwpxTarget {
            logical_object_id: id("object-1"),
            native_object_id: 10,
            object_kind: ObjectNumberKind::Table,
        };
        let state = FieldDocumentState::from_draft(
            FieldDocumentStateDraft {
                schema_version: FIELD_ENGINE_SCHEMA_VERSION.to_owned(),
                fields: Vec::new(),
                non_field_content_sha256: FLOW.to_owned(),
                style_catalog_sha256: FLOW.to_owned(),
                reference_inventory_sha256: FLOW.to_owned(),
                resource_inventory_sha256: FLOW.to_owned(),
                opaque_document_state_sha256: FLOW.to_owned(),
            },
            limits,
        )
        .expect("state");
        let (paragraph_style_sha256, character_style_sha256) =
            FieldObjectCaptionHwpxReader::style_sha256_at(source, &target, 0, 0, hwpx)
                .expect("styles");
        let request = FieldRequest::from_draft(
            FieldRequestDraft {
                schema_version: FIELD_ENGINE_SCHEMA_VERSION.to_owned(),
                request_id: id("request-1"),
                expected_source_state_sha256: state.canonical_sha256(limits).expect("digest"),
                expected_document_flow_sha256: FLOW.to_owned(),
                target_document_flow_sha256: FLOW.to_owned(),
                operation: FieldOperation::Insert {
                    insertion_index: 0,
                    field: FieldState {
                        identity: FieldIdentity {
                            logical_field_id: id("field-1"),
                            native_begin_id: 1,
                            native_end_id: 2,
                        },
                        anchor: FieldAnchor {
                            paragraph_id: id("caption-1"),
                            run_ordinal: 0,
                            inline_ordinal: 1,
                        },
                        definition: FieldDefinition::ObjectNumber {
                            object_kind: ObjectNumberKind::Table,
                            format: FieldNumberFormat::Digit,
                        },
                        cached_result: FieldCachedResult::Number {
                            value: 1,
                            display: "1".to_owned(),
                        },
                        update_policy: FieldUpdatePolicy::RecomputeDirect,
                        cache_status: FieldCacheStatus::Current,
                        locked: false,
                        evaluation_context_sha256: None,
                        paragraph_style_sha256,
                        character_style_sha256,
                        field_payload_sha256:
                            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
                                .to_owned(),
                        opaque_properties: Vec::new(),
                    },
                },
            },
            &state,
            FLOW,
            limits,
        )
        .expect("request");
        let domain = FieldEngineBuilder::plan(&state, &request, FLOW, limits).expect("domain plan");
        let map = [id("caption-1")];
        let ctx = FieldObjectCaptionHwpxContext {
            target: &target,
            state: &state,
            document_flow_sha256: FLOW,
            caption_paragraph_ids: &map,
            state_limits: limits,
            hwpx_limits: hwpx,
        };
        let plan = FieldObjectCaptionHwpxBuilder::plan(source, &ctx, &domain).expect("plan");
        let mut target_drift = plan.clone();
        target_drift.target.native_object_id = 11;
        let mut source_drift = plan.clone();
        source_drift.source_section_sha256[0] ^= 1;
        let mut caption_drift = plan.clone();
        caption_drift.source_caption_sha256[0] ^= 1;
        for corrupted in [target_drift, source_drift, caption_drift] {
            assert!(matches!(
                FieldObjectCaptionHwpxLowerer::lower_section_with_receipt(source, &corrupted, &ctx),
                Err(FieldObjectCaptionHwpxError::PlanTampered)
            ));
        }
    }
}
