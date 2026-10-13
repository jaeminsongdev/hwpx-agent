//! Actual hidden-explanation/MEMO body structure; native author/time/state mappings remain unknown.
pub mod body_output;
use super::{
    Mapper, StructureImportError, attributes, children, element, id, named, properties_object,
};
use crate::document_import::{
    ImportedSourcePackage, SourceImportError,
    fields::{FieldRangeImportError, ImportedDocumentFields},
    forms::{FormImportError, ImportedDocumentForms},
};
use domain_ir::{
    DocumentGraph, DocumentGraphLimits, Flow, LogicalId, Properties, PropertyValue, ReviewEntry,
    SourceAnchorHandle,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    fmt, io,
};
use thiserror::Error;

pub const REVIEW_BODY_IMPORT_PROFILE: &str = "hwpx-agent.document-import-review-bodies/partial-v1";
pub const REVIEW_BODY_IMPORT_SCOPE: &str = "observed_source_hidden_and_memo_body_not_author_time_visibility_resolution_full_comment_or_execution";
pub(crate) const MAX_BYTES: usize = 8 * 1024 * 1024;

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ReviewBodyKind {
    HiddenExplanation,
    MemoField,
}

/// Missing semantic metadata is explicit; it is not replaced by an author/time/default state.
#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ReviewNativeMetadata {
    UnverifiedNativeMapping,
}

/// Exact native string-value element identity. JSON/native meaning remains uninterpreted.
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ImportedReviewMetaTag {
    pub source_anchor: SourceAnchorHandle,
    pub element_sha256: [u8; 32],
    pub raw_bytes: usize,
}
impl fmt::Debug for ImportedReviewMetaTag {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ImportedReviewMetaTag(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ImportedReviewBodyObservation {
    pub review_id: LogicalId,
    pub target_node_id: LogicalId,
    pub kind: ReviewBodyKind,
    pub marker_anchor: SourceAnchorHandle,
    pub end_anchor: Option<SourceAnchorHandle>,
    pub parameter_anchor: Option<SourceAnchorHandle>,
    pub body_anchor: Option<SourceAnchorHandle>,
    /// Only actual marker/subList attributes and complete body structure are retained.
    pub native_attributes: Properties,
    pub body_attributes: Option<Properties>,
    pub body: Option<Flow>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub meta_tag: Option<ImportedReviewMetaTag>,
    pub metadata: ReviewNativeMetadata,
}
impl fmt::Debug for ImportedReviewBodyObservation {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ImportedReviewBodyObservation(<redacted>)")
    }
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct ReviewBodyImportReceipt {
    pub profile: &'static str,
    pub qualification: &'static str,
    pub source_package_sha256: [u8; 32],
    pub source_provenance_sha256: [u8; 32],
    pub original_field_graph_sha256: [u8; 32],
    pub graph_sha256: [u8; 32],
    pub body_observations_sha256: [u8; 32],
    pub hidden_explanations: usize,
    pub memo_fields: usize,
    pub memo_fields_without_body: usize,
    pub native_author_time_binding_verified: bool,
    pub native_visibility_resolution_binding_verified: bool,
}

pub struct ImportedDocumentReviewBodies<'a> {
    forms: &'a ImportedDocumentForms,
    graph: DocumentGraph,
    observations: Vec<ImportedReviewBodyObservation>,
    receipt: ReviewBodyImportReceipt,
}
impl fmt::Debug for ImportedDocumentReviewBodies<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ImportedDocumentReviewBodies(<redacted>)")
    }
}
impl<'a> ImportedDocumentReviewBodies<'a> {
    /// Uses the actual immutable source, original paired field collector and original body mapper.
    /// Source XML is never supplied separately, normalized, executed or rewritten.
    /// # Errors
    /// Rejects source/field/parent/envelope/body/budget/graph inconsistencies. Unknown metadata stays explicit.
    pub fn import(forms: &'a ImportedDocumentForms) -> Result<Self, ReviewBodyImportError> {
        let fields = ImportedDocumentFields::import(forms)?;
        Self::import_bound_fields(forms, &fields)
    }
    // Only an immutable original collector is accepted; assembly reuses it
    // instead of parsing/pairing all original fields for a second time.
    pub(crate) fn import_bound_fields(
        forms: &'a ImportedDocumentForms,
        fields: &ImportedDocumentFields<'_>,
    ) -> Result<Self, ReviewBodyImportError> {
        if fields.graph().document_id() != forms.graph().document_id()
            || fields.receipt().source_package_sha256 != forms.receipt().source_package_sha256
            || fields.receipt().source_provenance_sha256 != forms.receipt().source_provenance_sha256
            || fields.receipt().original_form_graph_sha256 != forms.receipt().graph_sha256
        {
            return Err(ReviewBodyImportError::Binding);
        }
        let observations = collect_observations(forms.source(), fields)?;
        let mut draft = fields.graph().clone().into_draft();
        for observation in &observations {
            draft.review.push(review_entry(observation)?);
        }
        draft.metadata.insert(
            "review_body_import_profile",
            PropertyValue::Text(REVIEW_BODY_IMPORT_PROFILE.into()),
        );
        draft.metadata.insert(
            "review_body_import_scope",
            PropertyValue::Text(REVIEW_BODY_IMPORT_SCOPE.into()),
        );
        let graph = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())
            .map_err(|_| ReviewBodyImportError::Graph)?;
        validate_observation_flows(&graph, &observations)?;
        let receipt = ReviewBodyImportReceipt {
            profile: REVIEW_BODY_IMPORT_PROFILE,
            qualification: REVIEW_BODY_IMPORT_SCOPE,
            source_package_sha256: forms.receipt().source_package_sha256,
            source_provenance_sha256: forms.receipt().source_provenance_sha256,
            original_field_graph_sha256: fields.receipt().graph_sha256,
            graph_sha256: graph
                .canonical_sha256()
                .map_err(|_| ReviewBodyImportError::Graph)?,
            body_observations_sha256: bounded_digest(&observations)?,
            hidden_explanations: observations
                .iter()
                .filter(|o| o.kind == ReviewBodyKind::HiddenExplanation)
                .count(),
            memo_fields: observations
                .iter()
                .filter(|o| o.kind == ReviewBodyKind::MemoField)
                .count(),
            memo_fields_without_body: observations
                .iter()
                .filter(|o| o.kind == ReviewBodyKind::MemoField && o.body.is_none())
                .count(),
            native_author_time_binding_verified: false,
            native_visibility_resolution_binding_verified: false,
        };
        Ok(Self {
            forms,
            graph,
            observations,
            receipt,
        })
    }
    #[must_use]
    pub const fn graph(&self) -> &DocumentGraph {
        &self.graph
    }
    #[must_use]
    pub fn observations(&self) -> &[ImportedReviewBodyObservation] {
        &self.observations
    }
    #[must_use]
    pub const fn receipt(&self) -> &ReviewBodyImportReceipt {
        &self.receipt
    }

    /// Whole original source/graph/field/body reconstruction, not just a hash refresh.
    /// # Errors
    /// Rejects any whole source, body, paired-field, graph, observation or receipt change.
    pub fn verify_source(
        &self,
        fresh: &[u8],
    ) -> Result<ReviewBodyImportReceipt, ReviewBodyImportError> {
        self.forms.verify_source(fresh)?;
        let old = self.forms.source();
        let forms = ImportedDocumentForms::import(ImportedSourcePackage::import(
            fresh,
            old.document_id.clone(),
            old.source_sha256,
            old.limits,
        )?)?;
        let rebuilt = ImportedDocumentReviewBodies::import(&forms)?;
        if rebuilt.graph != self.graph
            || rebuilt.observations != self.observations
            || rebuilt.receipt != self.receipt
        {
            return Err(ReviewBodyImportError::Binding);
        }
        Ok(rebuilt.receipt)
    }
}
fn collect_observations(
    source: &ImportedSourcePackage,
    fields: &ImportedDocumentFields<'_>,
) -> Result<Vec<ImportedReviewBodyObservation>, ReviewBodyImportError> {
    let by_anchor: BTreeMap<_, _> = fields
        .fields()
        .iter()
        .filter(|f| f.native_kind == "MEMO")
        .map(|f| (f.begin_anchor.opaque_handle.clone(), f))
        .collect();
    let mut mapper = Mapper::new(source);
    let mut observations = Vec::new();
    let mut seen_memo = BTreeSet::new();
    let mut observation_budget = DigestBudget {
        seen: 0,
        sha: Sha256::new(),
    };
    for path in source.spine() {
        let part = source
            .parts()
            .iter()
            .find(|p| p.path() == path)
            .ok_or(ReviewBodyImportError::Binding)?;
        let xml = part.xml().ok_or(ReviewBodyImportError::Binding)?;
        if element(xml, xml.root_element())?.name().namespace() != Some(super::SECTION_NS) {
            continue;
        }
        for (index, marker) in xml.elements().iter().enumerate() {
            let kind = if named(marker, "hiddenComment") {
                ReviewBodyKind::HiddenExplanation
            } else if named(marker, "fieldBegin")
                && actual_attribute(marker, "type") == Some("MEMO")
            {
                ReviewBodyKind::MemoField
            } else {
                continue;
            };
            if observations.len() >= DocumentGraphLimits::default().max_review_entries {
                return Err(ReviewBodyImportError::Budget);
            }
            let anchor = part
                .element_anchor(index)
                .ok_or(ReviewBodyImportError::Binding)?;
            let range = by_anchor.get(&anchor.opaque_handle).copied();
            if kind == ReviewBodyKind::MemoField && !seen_memo.insert(anchor.opaque_handle.clone())
            {
                return Err(ReviewBodyImportError::Binding);
            }
            let observation = observe_marker(source, part, index, kind, range, &mut mapper)?;
            // Bound aggregate retention before constructing the next body.
            serde_json::to_writer(&mut observation_budget, &observation)
                .map_err(|_| ReviewBodyImportError::Budget)?;
            observations.push(observation);
        }
    }
    if seen_memo.len() != by_anchor.len()
        || !mapper.notes.is_empty()
        || !mapper.bookmarks.is_empty()
    {
        return Err(ReviewBodyImportError::Binding);
    }
    Ok(observations)
}
fn observe_marker(
    source: &ImportedSourcePackage,
    part: &crate::document_import::ImportedSourcePart,
    index: usize,
    kind: ReviewBodyKind,
    range: Option<&crate::document_import::fields::ImportedFieldRange>,
    mapper: &mut Mapper<'_>,
) -> Result<ImportedReviewBodyObservation, ReviewBodyImportError> {
    let xml = part.xml().ok_or(ReviewBodyImportError::Binding)?;
    let marker = element(xml, index)?;
    let anchor = part
        .element_anchor(index)
        .ok_or(ReviewBodyImportError::Binding)?;
    let resolved = source.resolve_anchor(anchor)?;
    let parent = resolved
        .element()
        .ok_or(ReviewBodyImportError::Binding)?
        .parent()
        .ok_or(ReviewBodyImportError::Binding)?;
    let parent_element = element(xml, parent)?;
    let target = if named(parent_element, "ctrl") {
        if children(xml, parent)?.len() != 1 {
            return Err(ReviewBodyImportError::Binding);
        }
        id(
            "node",
            part.element_anchor(parent)
                .ok_or(ReviewBodyImportError::Binding)?,
        )?
    } else if named(parent_element, "run") && kind == ReviewBodyKind::HiddenExplanation {
        id("node", anchor)?
    } else {
        return Err(ReviewBodyImportError::Binding);
    };
    if kind == ReviewBodyKind::MemoField
        && range.ok_or(ReviewBodyImportError::Binding)?.begin_node_id != target
    {
        return Err(ReviewBodyImportError::Binding);
    }
    let payload = children(xml, index)?;
    let body = payload
        .iter()
        .copied()
        .find(|i| element(xml, *i).is_ok_and(|e| named(e, "subList")));
    if payload.iter().any(|i| {
        !element(xml, *i).is_ok_and(|e| {
            named(e, "subList")
                || (kind == ReviewBodyKind::MemoField
                    && (named(e, "parameters") || named(e, "metaTag")))
        })
    }) || payload
        .iter()
        .filter(|i| element(xml, **i).is_ok_and(|e| named(e, "subList")))
        .count()
        > 1
        || (kind == ReviewBodyKind::HiddenExplanation && payload.len() != 1)
    {
        return Err(ReviewBodyImportError::Envelope);
    }
    if let Some(body) = body {
        validate_body_envelope(xml, body)?;
    }
    let meta_tag = observe_meta_tag(source, part, &payload)?;
    let body_anchor = body
        .map(|i| {
            part.element_anchor(i)
                .cloned()
                .ok_or(ReviewBodyImportError::Binding)
        })
        .transpose()?;
    let body_flow = body.map(|i| mapper.flow(part, i, 1)).transpose()?;
    Ok(ImportedReviewBodyObservation {
        review_id: id("review", anchor)?,
        target_node_id: target,
        kind,
        marker_anchor: anchor.clone(),
        end_anchor: range.map(|f| f.end_anchor.clone()),
        parameter_anchor: range.and_then(|f| f.parameter_anchor.clone()),
        body_anchor,
        native_attributes: attributes(marker),
        body_attributes: body.map(|i| attributes(&xml.elements()[i])),
        body: body_flow,
        meta_tag,
        metadata: ReviewNativeMetadata::UnverifiedNativeMapping,
    })
}

fn observe_meta_tag(
    source: &ImportedSourcePackage,
    part: &crate::document_import::ImportedSourcePart,
    payload: &[usize],
) -> Result<Option<ImportedReviewMetaTag>, ReviewBodyImportError> {
    let xml = part.xml().ok_or(ReviewBodyImportError::Binding)?;
    let mut metas = payload
        .iter()
        .copied()
        .filter(|i| named(&xml.elements()[*i], "metaTag"));
    let Some(index) = metas.next() else {
        return Ok(None);
    };
    if metas.next().is_some() || payload.last() != Some(&index) {
        return Err(ReviewBodyImportError::Envelope);
    }
    let span = crate::text_flow::source_memo_meta_tag_span(xml, index)
        .map_err(|_| ReviewBodyImportError::Envelope)?;
    let source_anchor = part
        .element_anchor(index)
        .ok_or(ReviewBodyImportError::Binding)?
        .clone();
    source.resolve_anchor(&source_anchor)?;
    Ok(Some(ImportedReviewMetaTag {
        source_anchor,
        element_sha256: xml
            .with_source_bytes(|raw| Sha256::digest(&raw[span.start()..span.end()]).into()),
        raw_bytes: span.len(),
    }))
}
fn review_entry(
    observation: &ImportedReviewBodyObservation,
) -> Result<ReviewEntry, ReviewBodyImportError> {
    let mut properties = Properties::new();
    properties.insert(
        "source_marker_anchor",
        PropertyValue::Id(observation.marker_anchor.opaque_handle.clone()),
    );
    properties.insert(
        "source_body_observation_sha256",
        PropertyValue::Text(crate::document_import::hex_digest(bounded_digest(
            observation,
        )?)),
    );
    properties.insert(
        "native_attributes",
        properties_object(&observation.native_attributes),
    );
    properties.insert(
        "qualification",
        PropertyValue::Text(REVIEW_BODY_IMPORT_SCOPE.into()),
    );
    properties.insert(
        "native_metadata_binding",
        PropertyValue::Text("unverified_native_mapping".into()),
    );
    Ok(ReviewEntry {
        review_id: observation.review_id.clone(),
        target_node_id: observation.target_node_id.clone(),
        properties,
    })
}
fn actual_attribute<'a>(element: &'a crate::XmlElementToken, name: &str) -> Option<&'a str> {
    element
        .attributes()
        .iter()
        .find(|a| {
            !a.is_namespace_declaration()
                && a.name().namespace().is_none()
                && a.name().local_name() == name
        })
        .map(crate::XmlAttributeToken::semantic_value)
}
fn validate_body_envelope(
    xml: &crate::PreservingXmlDocument,
    body: usize,
) -> Result<(), ReviewBodyImportError> {
    let paragraphs = children(xml, body)?;
    if paragraphs.is_empty()
        || paragraphs
            .iter()
            .any(|i| !element(xml, *i).is_ok_and(|e| named(e, "p")))
    {
        return Err(ReviewBodyImportError::Envelope);
    }
    let span = element(xml, body)?
        .outer_span()
        .ok_or(ReviewBodyImportError::Envelope)?;
    let last_token = element(xml, body)?
        .end_token()
        .ok_or(ReviewBodyImportError::Envelope)?;
    for e in xml.elements()[body..]
        .iter()
        .take_while(|e| e.start_token() <= last_token)
    {
        if !e
            .outer_span()
            .is_some_and(|s| span.start() <= s.start() && s.end() <= span.end())
        {
            return Err(ReviewBodyImportError::Envelope);
        }
        if [
            "fieldBegin",
            "fieldEnd",
            "hiddenComment",
            "footNote",
            "endNote",
            "bookmark",
        ]
        .iter()
        .any(|n| named(e, n))
        {
            return Err(ReviewBodyImportError::Envelope);
        }
    }
    Ok(())
}
fn validate_observation_flows(
    graph: &DocumentGraph,
    observations: &[ImportedReviewBodyObservation],
) -> Result<(), ReviewBodyImportError> {
    // A disposable draft validates the complete main + observation node set
    // against the original domain validator, including IDs/resources/control
    // references and aggregate limits. It is NEVER the returned document graph:
    // review text must not become visible main text or full CommentState.
    let mut check = graph.clone().into_draft();
    let section = check
        .sections
        .first_mut()
        .ok_or(ReviewBodyImportError::Graph)?;
    for observation in observations {
        if let Some(body) = &observation.body {
            section.body.children.extend(body.children.clone());
        }
    }
    DocumentGraph::from_draft(check, DocumentGraphLimits::default())
        .map_err(|_| ReviewBodyImportError::Graph)?;
    Ok(())
}
pub(crate) fn bounded_digest(value: &impl Serialize) -> Result<[u8; 32], ReviewBodyImportError> {
    bounded_digest_and_size(value).map(|(sha, _)| sha)
}
pub(crate) fn bounded_digest_and_size(
    value: &impl Serialize,
) -> Result<([u8; 32], usize), ReviewBodyImportError> {
    let mut writer = DigestBudget {
        seen: 0,
        sha: Sha256::new(),
    };
    serde_json::to_writer(&mut writer, value).map_err(|_| ReviewBodyImportError::Budget)?;
    Ok((writer.sha.finalize().into(), writer.seen))
}
struct DigestBudget {
    seen: usize,
    sha: Sha256,
}
impl io::Write for DigestBudget {
    fn write(&mut self, bytes: &[u8]) -> io::Result<usize> {
        let seen = self
            .seen
            .checked_add(bytes.len())
            .ok_or_else(|| io::Error::other("review budget"))?;
        if seen > MAX_BYTES {
            return Err(io::Error::other("review budget"));
        }
        self.seen = seen;
        self.sha.update(bytes);
        Ok(bytes.len())
    }
    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}
#[derive(Debug, Error)]
pub enum ReviewBodyImportError {
    #[error("review_body_source_rejected")]
    Source(#[from] SourceImportError),
    #[error("review_body_original_forms_rejected")]
    Forms(#[from] FormImportError),
    #[error("review_body_original_fields_rejected")]
    Fields(#[from] FieldRangeImportError),
    #[error("review_body_original_structure_rejected")]
    Structure(#[from] StructureImportError),
    #[error("review_body_binding_rejected")]
    Binding,
    #[error("review_body_envelope_rejected")]
    Envelope,
    #[error("review_body_budget_rejected")]
    Budget,
    #[error("review_body_graph_rejected")]
    Graph,
}
