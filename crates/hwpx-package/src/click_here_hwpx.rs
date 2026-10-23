//! Preserving `CLICK_HERE` text-cache lowering over the existing field domain engine.
use std::{collections::BTreeSet, fmt};

use domain_ir::{
    FieldCacheStatus, FieldCachedResult, FieldDefinition, FieldDocumentState, FieldEngineBuilder,
    FieldEngineError, FieldEngineLimits, FieldPlan, FieldUpdatePolicy, LogicalId,
};
use quick_xml::escape::{escape, unescape};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::preserving_xml::{PreservingXmlDocument, PreservingXmlError, XmlElementToken};

pub const CLICK_HERE_HWPX_PROFILE_ID: &str =
    "hwpx-agent.click-here-hwpx.hwpml-2011-preserved-text-cache/v1";
const HP: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const HS: &str = "http://www.hancom.co.kr/hwpml/2011/section";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ClickHereHwpxLimits {
    section_bytes: usize,
    fields: usize,
    text_bytes: usize,
    plan_bytes: usize,
}
impl Default for ClickHereHwpxLimits {
    fn default() -> Self {
        Self {
            section_bytes: 2 * 1024 * 1024,
            fields: 4096,
            text_bytes: 64 * 1024,
            plan_bytes: 4 * 1024 * 1024,
        }
    }
}
impl ClickHereHwpxLimits {
    /// Creates finite bounds without silently clamping input.
    /// # Errors
    /// Rejects zero or parser/hard-ceiling-exceeding bounds.
    pub fn new(
        section_bytes: usize,
        fields: usize,
        text_bytes: usize,
        plan_bytes: usize,
    ) -> Result<Self, ClickHereHwpxError> {
        if section_bytes == 0
            || section_bytes > 2 * 1024 * 1024
            || fields == 0
            || fields > 65_536
            || text_bytes == 0
            || text_bytes > 64 * 1024
            || plan_bytes == 0
            || plan_bytes > 8 * 1024 * 1024
        {
            return Err(ClickHereHwpxError::InvalidLimit);
        }
        Ok(Self {
            section_bytes,
            fields,
            text_bytes,
            plan_bytes,
        })
    }
}

/// Observed native pair identity, not the domain engine's begin/end reservations.
#[derive(Clone, Eq, PartialEq)]
pub struct ClickHereHwpxField {
    pub native_begin_id: u32,
    pub native_field_id: u32,
    pub name: String,
    pub prompt: String,
    pub display: String,
    pub paragraph_id: LogicalId,
    pub run_ordinal: u32,
    pub inline_ordinal: u32,
    pub paragraph_style_sha256: String,
    pub character_style_sha256: String,
    pub parameters_sha256: String,
}
impl fmt::Debug for ClickHereHwpxField {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ClickHereHwpxField(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct ClickHereHwpxReadback {
    pub state: FieldDocumentState,
    pub section_sha256: [u8; 32],
    pub field_count: usize,
}
impl fmt::Debug for ClickHereHwpxReadback {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("ClickHereHwpxReadback")
            .field("field_count", &self.field_count)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ClickHereHwpxPlan {
    profile_id: &'static str,
    source_section_sha256: String,
    source_state: FieldDocumentState,
    domain_plan: FieldPlan,
    paragraph_ids: Vec<LogicalId>,
    plan_sha256: String,
}
impl ClickHereHwpxPlan {
    #[must_use]
    pub fn plan_sha256(&self) -> &str {
        &self.plan_sha256
    }
    /// Serializes the private sealed plan deterministically within its bound.
    /// # Errors
    /// Returns an allocation, serialization or plan-size failure.
    pub fn canonical_json(
        &self,
        limits: ClickHereHwpxLimits,
    ) -> Result<Vec<u8>, ClickHereHwpxError> {
        let bytes = serde_json::to_vec(self).map_err(|_| ClickHereHwpxError::PlanBinding)?;
        if bytes.len() > limits.plan_bytes {
            return Err(ClickHereHwpxError::InputLimit);
        }
        Ok(bytes)
    }
}
impl fmt::Debug for ClickHereHwpxPlan {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ClickHereHwpxPlan(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct ClickHereHwpxLoweringReceipt {
    pub source_section_sha256: [u8; 32],
    pub target_section_sha256: [u8; 32],
    pub outside_declared_edits_byte_exact: bool,
    pub typed_target_readback: ClickHereHwpxReadback,
}
impl fmt::Debug for ClickHereHwpxLoweringReceipt {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ClickHereHwpxLoweringReceipt(<redacted>)")
    }
}

#[derive(Debug, Error)]
pub enum ClickHereHwpxError {
    #[error("CLICK_HERE_INVALID_LIMIT")]
    InvalidLimit,
    #[error("CLICK_HERE_INPUT_LIMIT")]
    InputLimit,
    #[error("CLICK_HERE_UNSUPPORTED_NATIVE_PROFILE")]
    UnsupportedProfile,
    #[error("CLICK_HERE_PROJECTION_MISMATCH")]
    ProjectionMismatch,
    #[error("CLICK_HERE_SOURCE_OR_PLAN_DRIFT")]
    PlanBinding,
    #[error("CLICK_HERE_ALLOCATION_FAILED")]
    Allocation,
    #[error("CLICK_HERE_XML_REJECTED")]
    Xml(#[from] PreservingXmlError),
    #[error("CLICK_HERE_DOMAIN_REJECTED")]
    Domain(#[from] FieldEngineError),
}

#[derive(Debug)]
pub struct ClickHereHwpxReader;
impl ClickHereHwpxReader {
    /// Inspects exact native pairs and plain caches, preserving opaque Command bytes.
    /// # Errors
    /// Rejects unsupported fields, nested/cross-paragraph pairs, rich caches, drift and limits.
    pub fn inspect_section(
        source: &[u8],
        paragraph_ids: &[LogicalId],
        limits: ClickHereHwpxLimits,
    ) -> Result<Vec<ClickHereHwpxField>, ClickHereHwpxError> {
        Ok(parse(source, paragraph_ids, limits)?
            .fields
            .into_iter()
            .map(|p| p.field)
            .collect())
    }
    /// Binds every native `CLICK_HERE` projection to the complete expected domain inventory.
    /// # Errors
    /// Rejects unsupported domain states or any native/anchor/style/payload/cache mismatch.
    pub fn read_section(
        source: &[u8],
        expected: &FieldDocumentState,
        paragraph_ids: &[LogicalId],
        state_limits: FieldEngineLimits,
        limits: ClickHereHwpxLimits,
    ) -> Result<ClickHereHwpxReadback, ClickHereHwpxError> {
        let _ = expected.canonical_sha256(state_limits)?;
        let parsed = parse(source, paragraph_ids, limits)?;
        if parsed.fields.len() != expected.fields().len() {
            return Err(ClickHereHwpxError::ProjectionMismatch);
        }
        for (native, model) in parsed.fields.iter().zip(expected.fields()) {
            let FieldDefinition::ClickHere { prompt } = &model.definition else {
                return Err(ClickHereHwpxError::UnsupportedProfile);
            };
            let FieldCachedResult::Text { display } = &model.cached_result else {
                return Err(ClickHereHwpxError::UnsupportedProfile);
            };
            if model.locked
                || model.update_policy != FieldUpdatePolicy::RecomputeDirect
                || model.cache_status != FieldCacheStatus::Current
                || !model.opaque_properties.is_empty()
            {
                return Err(ClickHereHwpxError::UnsupportedProfile);
            }
            let p = &native.field;
            if prompt != &p.prompt
                || display != &p.display
                || model.anchor.paragraph_id != p.paragraph_id
                || model.anchor.run_ordinal != p.run_ordinal
                || model.anchor.inline_ordinal != p.inline_ordinal
                || model.paragraph_style_sha256 != p.paragraph_style_sha256
                || model.character_style_sha256 != p.character_style_sha256
                || model.field_payload_sha256 != p.parameters_sha256
            {
                return Err(ClickHereHwpxError::ProjectionMismatch);
            }
        }
        Ok(ClickHereHwpxReadback {
            state: expected.clone(),
            section_sha256: Sha256::digest(source).into(),
            field_count: parsed.fields.len(),
        })
    }
}

#[derive(Debug)]
pub struct ClickHereHwpxBuilder;
impl ClickHereHwpxBuilder {
    /// Binds one existing text-result update using the existing field domain plan.
    /// # Errors
    /// Rejects every other operation, stale source/state/flow, projection drift and limits.
    pub fn plan(
        source: &[u8],
        state: &FieldDocumentState,
        domain: &FieldPlan,
        flow: &str,
        paragraph_ids: &[LogicalId],
        state_limits: FieldEngineLimits,
        limits: ClickHereHwpxLimits,
    ) -> Result<ClickHereHwpxPlan, ClickHereHwpxError> {
        if domain.capability_id() != "ref.field_update" || domain.source_state() != state {
            return Err(ClickHereHwpxError::UnsupportedProfile);
        }
        let built = FieldEngineBuilder::build(domain, state, flow, state_limits)?;
        let _ = transition(state, &built.state)?;
        let _ =
            ClickHereHwpxReader::read_section(source, state, paragraph_ids, state_limits, limits)?;
        let mut plan = ClickHereHwpxPlan {
            profile_id: CLICK_HERE_HWPX_PROFILE_ID,
            source_section_sha256: hex(Sha256::digest(source).into()),
            source_state: state.clone(),
            domain_plan: domain.clone(),
            paragraph_ids: paragraph_ids.to_vec(),
            plan_sha256: String::new(),
        };
        plan.plan_sha256 = hex(Sha256::digest(plan.canonical_json(limits)?).into());
        let _ = plan.canonical_json(limits)?;
        Ok(plan)
    }
}

#[derive(Debug)]
pub struct ClickHereHwpxLowerer;
impl ClickHereHwpxLowerer {
    /// Updates only selected plain text spans and dirty=1; preserves native pairs/parameters/styles.
    /// # Errors
    /// Independently rechecks source/state/flow/map/domain/adapter seal and target projection.
    #[allow(clippy::too_many_arguments)]
    pub fn lower_section_with_receipt(
        source: &[u8],
        plan: &ClickHereHwpxPlan,
        state: &FieldDocumentState,
        flow: &str,
        paragraph_ids: &[LogicalId],
        state_limits: FieldEngineLimits,
        limits: ClickHereHwpxLimits,
    ) -> Result<(Vec<u8>, ClickHereHwpxLoweringReceipt), ClickHereHwpxError> {
        let rebuilt = ClickHereHwpxBuilder::plan(
            source,
            state,
            &plan.domain_plan,
            flow,
            paragraph_ids,
            state_limits,
            limits,
        )?;
        if &rebuilt != plan {
            return Err(ClickHereHwpxError::PlanBinding);
        }
        let target = FieldEngineBuilder::build(&plan.domain_plan, state, flow, state_limits)?.state;
        let index = transition(state, &target)?;
        let FieldCachedResult::Text { display } = &target.fields()[index].cached_result else {
            return Err(ClickHereHwpxError::UnsupportedProfile);
        };
        if display.len() > limits.text_bytes || display.chars().any(invalid_character) {
            return Err(ClickHereHwpxError::InputLimit);
        }
        let parsed = parse(source, paragraph_ids, limits)?;
        let selected = &parsed.fields[index];
        let mut edits = vec![(selected.dirty.0, selected.dirty.1, b"1".to_vec())];
        for (ordinal, &element_index) in selected.texts.iter().enumerate() {
            let node = element(&parsed.document, element_index)?;
            let replacement = if ordinal == 0 {
                escape(display).into_owned()
            } else {
                String::new()
            };
            let span = if node.is_empty() {
                let outer = outer(node)?;
                let original = slice(source, outer)?;
                let prefix = original
                    .strip_suffix(b"/>")
                    .ok_or(ClickHereHwpxError::UnsupportedProfile)?;
                let mut value = prefix.to_vec();
                value.extend_from_slice(b">");
                value.extend_from_slice(replacement.as_bytes());
                value.extend_from_slice(format!("</{}>", node.name().qualified_name()).as_bytes());
                (outer.0, outer.1, value)
            } else {
                let content = node
                    .content_span()
                    .ok_or(ClickHereHwpxError::UnsupportedProfile)?;
                (content.start(), content.end(), replacement.into_bytes())
            };
            edits.push(span);
        }
        edits.sort_by_key(|edit| edit.0);
        let mut output = Vec::new();
        output
            .try_reserve_exact(limits.section_bytes)
            .map_err(|_| ClickHereHwpxError::Allocation)?;
        let mut cursor = 0;
        for (start, end, replacement) in &edits {
            if *start < cursor || *end < *start || *end > source.len() {
                return Err(ClickHereHwpxError::PlanBinding);
            }
            output.extend_from_slice(&source[cursor..*start]);
            output.extend_from_slice(replacement);
            cursor = *end;
            if output.len() > limits.section_bytes {
                return Err(ClickHereHwpxError::InputLimit);
            }
        }
        output.extend_from_slice(&source[cursor..]);
        if output.len() > limits.section_bytes {
            return Err(ClickHereHwpxError::InputLimit);
        }
        let readback = ClickHereHwpxReader::read_section(
            &output,
            &target,
            paragraph_ids,
            state_limits,
            limits,
        )?;
        let receipt = ClickHereHwpxLoweringReceipt {
            source_section_sha256: Sha256::digest(source).into(),
            target_section_sha256: readback.section_sha256,
            outside_declared_edits_byte_exact: true,
            typed_target_readback: readback,
        };
        Ok((output, receipt))
    }
}

fn transition(
    before: &FieldDocumentState,
    after: &FieldDocumentState,
) -> Result<usize, ClickHereHwpxError> {
    if before.fields().len() != after.fields().len() {
        return Err(ClickHereHwpxError::UnsupportedProfile);
    }
    let changed: Vec<_> = before
        .fields()
        .iter()
        .zip(after.fields())
        .enumerate()
        .filter_map(|(i, (a, b))| (a != b).then_some(i))
        .collect();
    if changed.len() != 1 {
        return Err(ClickHereHwpxError::UnsupportedProfile);
    }
    let i = changed[0];
    let mut allowed = before.fields()[i].clone();
    allowed.cached_result = after.fields()[i].cached_result.clone();
    allowed.cache_status = after.fields()[i].cache_status;
    allowed
        .evaluation_context_sha256
        .clone_from(&after.fields()[i].evaluation_context_sha256);
    if allowed != after.fields()[i] {
        return Err(ClickHereHwpxError::UnsupportedProfile);
    }
    Ok(i)
}

struct Projection {
    field: ClickHereHwpxField,
    dirty: (usize, usize),
    texts: Vec<usize>,
}
struct Parsed {
    document: PreservingXmlDocument,
    fields: Vec<Projection>,
}
fn parse(
    source: &[u8],
    paragraph_ids: &[LogicalId],
    limits: ClickHereHwpxLimits,
) -> Result<Parsed, ClickHereHwpxError> {
    if source.is_empty() || source.len() > limits.section_bytes {
        return Err(ClickHereHwpxError::InputLimit);
    }
    let document = PreservingXmlDocument::parse(source)?;
    let root = element(&document, document.root_element())?;
    if root.name().namespace() != Some(HS) || root.name().local_name() != "sec" {
        return Err(ClickHereHwpxError::UnsupportedProfile);
    }
    let paragraphs: Vec<_> = children(&document, document.root_element())?
        .into_iter()
        .filter(|i| element(&document, *i).is_ok_and(|e| is(e, "p")))
        .collect();
    if paragraphs.len() != paragraph_ids.len()
        || paragraph_ids.iter().collect::<BTreeSet<_>>().len() != paragraph_ids.len()
    {
        return Err(ClickHereHwpxError::ProjectionMismatch);
    }
    let mut fields = Vec::new();
    let mut ids = BTreeSet::new();
    let mut field_ids = BTreeSet::new();
    let mut seen_controls = BTreeSet::new();
    for (paragraph_ordinal, &p) in paragraphs.iter().enumerate() {
        let runs: Vec<_> = children(&document, p)?
            .into_iter()
            .filter(|i| element(&document, *i).is_ok_and(|e| is(e, "run")))
            .collect();
        let mut pending: Option<(usize, usize, usize, Vec<usize>)> = None;
        for (run_ordinal, &r) in runs.iter().enumerate() {
            whitespace_between_children(source, &document, r)?;
            for (inline_ordinal, i) in children(&document, r)?.into_iter().enumerate() {
                let node = element(&document, i)?;
                if is(node, "ctrl") {
                    let controls = children(&document, i)?;
                    if controls.len() == 1 && is(element(&document, controls[0])?, "fieldBegin") {
                        attributes(node, &[])?;
                        whitespace_between_children(source, &document, i)?;
                        if pending.is_some() {
                            return Err(ClickHereHwpxError::UnsupportedProfile);
                        }
                        pending = Some((controls[0], run_ordinal, inline_ordinal, Vec::new()));
                        seen_controls.insert(controls[0]);
                    } else if controls.len() == 1
                        && is(element(&document, controls[0])?, "fieldEnd")
                    {
                        attributes(node, &[])?;
                        whitespace_between_children(source, &document, i)?;
                        let (begin, begin_run, begin_inline, texts) = pending
                            .take()
                            .ok_or(ClickHereHwpxError::UnsupportedProfile)?;
                        seen_controls.insert(controls[0]);
                        if texts.is_empty() || fields.len() >= limits.fields {
                            return Err(ClickHereHwpxError::InputLimit);
                        }
                        let anchor = NativeAnchor {
                            paragraph: p,
                            paragraph_id: paragraph_ids[paragraph_ordinal].clone(),
                            run: runs[begin_run],
                            run_ordinal: begin_run,
                            inline_ordinal: begin_inline,
                        };
                        let projection = native_pair(
                            source,
                            &document,
                            begin,
                            controls[0],
                            texts,
                            anchor,
                            limits,
                        )?;
                        if !ids.insert(projection.field.native_begin_id)
                            || !field_ids.insert(projection.field.native_field_id)
                        {
                            return Err(ClickHereHwpxError::ProjectionMismatch);
                        }
                        fields.push(projection);
                    } else if pending.is_some() {
                        return Err(ClickHereHwpxError::UnsupportedProfile);
                    }
                } else if let Some((_, _, _, texts)) = &mut pending {
                    if !is(node, "t") {
                        return Err(ClickHereHwpxError::UnsupportedProfile);
                    }
                    texts.push(i);
                }
            }
        }
        if pending.is_some() {
            return Err(ClickHereHwpxError::UnsupportedProfile);
        }
    }
    for (i, e) in document.elements().iter().enumerate() {
        if (is(e, "fieldBegin") || is(e, "fieldEnd")) && !seen_controls.contains(&i) {
            return Err(ClickHereHwpxError::UnsupportedProfile);
        }
    }
    Ok(Parsed { document, fields })
}

struct NativeAnchor {
    paragraph: usize,
    paragraph_id: LogicalId,
    run: usize,
    run_ordinal: usize,
    inline_ordinal: usize,
}
fn native_pair(
    source: &[u8],
    d: &PreservingXmlDocument,
    begin: usize,
    end: usize,
    texts: Vec<usize>,
    anchor: NativeAnchor,
    limits: ClickHereHwpxLimits,
) -> Result<Projection, ClickHereHwpxError> {
    let first = element(d, begin)?;
    let last = element(d, end)?;
    attributes(
        first,
        &[
            "id", "type", "name", "editable", "dirty", "zorder", "fieldid",
        ],
    )?;
    attributes(last, &["beginIDRef", "fieldid"])?;
    if value(first, "type")? != "CLICK_HERE"
        || value(first, "editable")? != "1"
        || value(first, "zorder")? != "-1"
        || !children(d, end)?.is_empty()
        || !whitespace(source, last.content_span().map(|s| (s.start(), s.end())))?
    {
        return Err(ClickHereHwpxError::UnsupportedProfile);
    }
    let id = number(value(first, "id")?)?;
    let field_id = number(value(first, "fieldid")?)?;
    if number(value(last, "beginIDRef")?)? != id || number(value(last, "fieldid")?)? != field_id {
        return Err(ClickHereHwpxError::ProjectionMismatch);
    }
    let parameters = children(d, begin)?;
    if parameters.len() != 1 || !is(element(d, parameters[0])?, "parameters") {
        return Err(ClickHereHwpxError::UnsupportedProfile);
    }
    whitespace_between_children(source, d, begin)?;
    let prompt = parameters_prompt(source, d, parameters[0], limits)?;
    let mut text = String::new();
    for &t in &texts {
        text.push_str(&plain_text(source, d, t, limits)?);
        if text.len() > limits.text_bytes {
            return Err(ClickHereHwpxError::InputLimit);
        }
    }
    let dirty = attribute(first, "dirty")?;
    let display = match dirty.semantic_value() {
        "0" if text == prompt => String::new(),
        "1" => text,
        _ => return Err(ClickHereHwpxError::ProjectionMismatch),
    };
    let name = value(first, "name")?.to_owned();
    if name.is_empty() || name.len() > limits.text_bytes {
        return Err(ClickHereHwpxError::UnsupportedProfile);
    }
    let paragraph = element(d, anchor.paragraph)?.start_tag_span();
    let run = element(d, anchor.run)?.start_tag_span();
    Ok(Projection {
        field: ClickHereHwpxField {
            native_begin_id: id,
            native_field_id: field_id,
            name,
            prompt,
            display,
            paragraph_id: anchor.paragraph_id,
            run_ordinal: u32::try_from(anchor.run_ordinal)
                .map_err(|_| ClickHereHwpxError::InputLimit)?,
            inline_ordinal: u32::try_from(anchor.inline_ordinal)
                .map_err(|_| ClickHereHwpxError::InputLimit)?,
            paragraph_style_sha256: hex(Sha256::digest(slice(
                source,
                (paragraph.start(), paragraph.end()),
            )?)
            .into()),
            character_style_sha256: hex(
                Sha256::digest(slice(source, (run.start(), run.end()))?).into()
            ),
            parameters_sha256: hex(Sha256::digest(slice(
                source,
                outer(element(d, parameters[0])?)?,
            )?)
            .into()),
        },
        dirty: (dirty.value_span().start(), dirty.value_span().end()),
        texts,
    })
}
fn whitespace(source: &[u8], span: Option<(usize, usize)>) -> Result<bool, ClickHereHwpxError> {
    Ok(match span {
        None => true,
        Some(span) => slice(source, span)?.iter().all(u8::is_ascii_whitespace),
    })
}
fn whitespace_between_children(
    source: &[u8],
    d: &PreservingXmlDocument,
    i: usize,
) -> Result<(), ClickHereHwpxError> {
    let Some(content) = element(d, i)?.content_span() else {
        return Ok(());
    };
    let mut cursor = content.start();
    for child in children(d, i)? {
        let span = outer(element(d, child)?)?;
        if !whitespace(source, Some((cursor, span.0)))? {
            return Err(ClickHereHwpxError::UnsupportedProfile);
        }
        cursor = span.1;
    }
    if !whitespace(source, Some((cursor, content.end())))? {
        return Err(ClickHereHwpxError::UnsupportedProfile);
    }
    Ok(())
}
fn parameters_prompt(
    source: &[u8],
    d: &PreservingXmlDocument,
    i: usize,
    limits: ClickHereHwpxLimits,
) -> Result<String, ClickHereHwpxError> {
    let p = element(d, i)?;
    attributes(p, &["cnt", "name"])?;
    if value(p, "cnt")? != "4" || !value(p, "name")?.is_empty() {
        return Err(ClickHereHwpxError::UnsupportedProfile);
    }
    let items = children(d, i)?;
    whitespace_between_children(source, d, i)?;
    if items.len() != 4 {
        return Err(ClickHereHwpxError::UnsupportedProfile);
    }
    let expected = [
        ("integerParam", "Prop"),
        ("stringParam", "Command"),
        ("stringParam", "Direction"),
        ("stringParam", "HelpState"),
    ];
    let mut values = Vec::new();
    for (&child, (tag, name)) in items.iter().zip(expected) {
        let n = element(d, child)?;
        if !is(n, tag) || value(n, "name")? != name {
            return Err(ClickHereHwpxError::UnsupportedProfile);
        }
        for a in n.attributes() {
            if a.is_namespace_declaration() {
                return Err(ClickHereHwpxError::UnsupportedProfile);
            }
            if a.name().namespace().is_none() && a.name().local_name() == "name" {
                continue;
            }
            if name == "Command"
                && a.name().namespace() == Some("http://www.w3.org/XML/1998/namespace")
                && a.name().local_name() == "space"
                && a.semantic_value() == "preserve"
            {
                continue;
            }
            return Err(ClickHereHwpxError::UnsupportedProfile);
        }
        values.push(plain_text(source, d, child, limits)?);
    }
    // Command is deliberately opaque: it is never synthesized, parsed as an action or executed.
    if values[0] != "9" || values[1].is_empty() {
        return Err(ClickHereHwpxError::UnsupportedProfile);
    }
    Ok(values[2].clone())
}
fn plain_text(
    source: &[u8],
    d: &PreservingXmlDocument,
    i: usize,
    limits: ClickHereHwpxLimits,
) -> Result<String, ClickHereHwpxError> {
    let node = element(d, i)?;
    if node.first_child().is_some() {
        return Err(ClickHereHwpxError::UnsupportedProfile);
    }
    if is(node, "t") {
        attributes(node, &[])?;
    }
    let Some(span) = node.content_span() else {
        return Ok(String::new());
    };
    let raw = std::str::from_utf8(slice(source, (span.start(), span.end()))?)
        .map_err(|_| ClickHereHwpxError::UnsupportedProfile)?;
    if raw.contains('<') || raw.len() > limits.text_bytes {
        return Err(ClickHereHwpxError::UnsupportedProfile);
    }
    let decoded = unescape(raw)
        .map_err(|_| ClickHereHwpxError::UnsupportedProfile)?
        .into_owned();
    if decoded.len() > limits.text_bytes || decoded.chars().any(invalid_character) {
        return Err(ClickHereHwpxError::InputLimit);
    }
    Ok(decoded)
}
fn attributes(node: &XmlElementToken, names: &[&str]) -> Result<(), ClickHereHwpxError> {
    if node.attributes().len() != names.len()
        || node.attributes().iter().any(|a| {
            a.is_namespace_declaration()
                || a.name().namespace().is_some()
                || !names.contains(&a.name().local_name())
        })
    {
        return Err(ClickHereHwpxError::UnsupportedProfile);
    }
    Ok(())
}
fn attribute<'a>(
    node: &'a XmlElementToken,
    name: &str,
) -> Result<&'a crate::preserving_xml::XmlAttributeToken, ClickHereHwpxError> {
    node.attributes()
        .iter()
        .find(|a| a.name().namespace().is_none() && a.name().local_name() == name)
        .ok_or(ClickHereHwpxError::UnsupportedProfile)
}
fn value<'a>(node: &'a XmlElementToken, name: &str) -> Result<&'a str, ClickHereHwpxError> {
    Ok(attribute(node, name)?.semantic_value())
}
fn number(value: &str) -> Result<u32, ClickHereHwpxError> {
    let n = value
        .parse::<u32>()
        .map_err(|_| ClickHereHwpxError::UnsupportedProfile)?;
    if n == 0 || n.to_string() != value {
        return Err(ClickHereHwpxError::UnsupportedProfile);
    }
    Ok(n)
}
fn is(e: &XmlElementToken, name: &str) -> bool {
    e.name().namespace() == Some(HP) && e.name().local_name() == name
}
fn element(d: &PreservingXmlDocument, i: usize) -> Result<&XmlElementToken, ClickHereHwpxError> {
    d.elements()
        .get(i)
        .ok_or(ClickHereHwpxError::UnsupportedProfile)
}
fn children(d: &PreservingXmlDocument, i: usize) -> Result<Vec<usize>, ClickHereHwpxError> {
    let mut result = Vec::new();
    let mut next = element(d, i)?.first_child();
    while let Some(child) = next {
        result.push(child);
        next = element(d, child)?.next_sibling();
    }
    Ok(result)
}
fn outer(e: &XmlElementToken) -> Result<(usize, usize), ClickHereHwpxError> {
    let s = e
        .outer_span()
        .ok_or(ClickHereHwpxError::UnsupportedProfile)?;
    Ok((s.start(), s.end()))
}
fn slice(source: &[u8], span: (usize, usize)) -> Result<&[u8], ClickHereHwpxError> {
    source
        .get(span.0..span.1)
        .ok_or(ClickHereHwpxError::PlanBinding)
}
fn hex(bytes: [u8; 32]) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut text = String::with_capacity(64);
    for byte in bytes {
        text.push(char::from(DIGITS[usize::from(byte >> 4)]));
        text.push(char::from(DIGITS[usize::from(byte & 15)]));
    }
    text
}
const fn invalid_character(c: char) -> bool {
    !matches!(c as u32,0x9|0xA|0xD|0x20..=0xD7FF|0xE000..=0xFFFD|0x0001_0000..=0x0010_FFFF)
}
