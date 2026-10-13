//! Actual note source anchors and body flow, not generated numbering/render proof.
use super::*;
use domain_ir::{Note, SourceAnchorHandle};
use std::collections::BTreeSet;

pub const NOTE_IMPORT_PROFILE: &str = "hwpx-agent.document-import-notes/partial-v1";
pub const NOTE_IMPORT_SCOPE: &str =
    "source_note_body_marker_attributes_not_numbering_render_native_identity_or_execution";

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ImportedNoteObservation {
    pub note_id: LogicalId,
    pub wrapper_node_id: LogicalId,
    pub source_anchor: SourceAnchorHandle,
    pub body_anchor: SourceAnchorHandle,
    pub paragraph_id: LogicalId,
    pub native_kind: String,
    pub native_instance_id: u32,
    /// Only attributes actually present. No synthesized flags/number/defaults.
    pub native_attributes: Properties,
}
impl fmt::Debug for ImportedNoteObservation {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ImportedNoteObservation(<redacted>)")
    }
}
impl Mapper<'_> {
    /// Keeps the original wrapper node/inline/common/opaque properties. The
    /// typed Note body is source-anchored and linked through source_note_id.
    pub(super) fn note_wrapper(
        &mut self,
        part: &ImportedSourcePart,
        index: usize,
        depth: usize,
        inlines: &mut Vec<Inline>,
        attached: &mut Vec<Node>,
    ) -> Result<bool, StructureImportError> {
        let xml = part.xml().ok_or(StructureImportError::Binding)?;
        if !named(element(xml, index)?, "ctrl") {
            return Ok(false);
        }
        let candidates: Vec<_> = children(xml, index)?
            .into_iter()
            .filter(|child| {
                element(xml, *child).is_ok_and(|v| named(v, "footNote") || named(v, "endNote"))
            })
            .collect();
        if candidates.is_empty() {
            return Ok(false);
        }
        if candidates.len() != 1 || self.notes.len() >= DocumentGraphLimits::default().max_notes {
            return Err(StructureImportError::Binding);
        }
        let marker_index = candidates[0];
        let envelope = crate::note_hwpx::read_imported_note_envelope(xml, marker_index)
            .map_err(|error| StructureImportError::Note { code: error.code() })?;
        let marker = element(xml, marker_index)?;
        let source_anchor = part
            .element_anchor(marker_index)
            .ok_or(StructureImportError::Binding)?;
        let body_anchor = part
            .element_anchor(envelope.body_element)
            .ok_or(StructureImportError::Binding)?;
        self.source.resolve_anchor(source_anchor)?;
        self.source.resolve_anchor(body_anchor)?;
        let note_id = id("note", source_anchor)?;
        let mut wrapper = self.opaque(part, index)?;
        let Node::EmbeddedObject(object) = &mut wrapper else {
            return Err(StructureImportError::Binding);
        };
        object
            .properties
            .insert("source_note_id", PropertyValue::Id(note_id.clone()));
        let paragraph = element(xml, envelope.paragraph_element)?;
        if !named(paragraph, "p") {
            return Err(StructureImportError::Binding);
        }
        let paragraph_id = id(
            "node",
            part.element_anchor(envelope.paragraph_element)
                .ok_or(StructureImportError::Binding)?,
        )?;
        let mut properties = Properties::new();
        properties.insert(
            "native_kind",
            PropertyValue::Text(marker.name().local_name().into()),
        );
        properties.insert("native_attributes", properties_object(&attributes(marker)));
        properties.insert(
            "source_anchor",
            PropertyValue::Id(source_anchor.opaque_handle.clone()),
        );
        properties.insert(
            "body_anchor",
            PropertyValue::Id(body_anchor.opaque_handle.clone()),
        );
        properties.insert(
            "source_wrapper_node_id",
            PropertyValue::Id(object.common.node_id.clone()),
        );
        properties.insert(
            "source_paragraph_id",
            PropertyValue::Id(paragraph_id.clone()),
        );
        properties.insert(
            "qualification",
            PropertyValue::Text(NOTE_IMPORT_SCOPE.into()),
        );
        let body = self.flow(part, envelope.body_element, depth + 1)?;
        if body.children.is_empty() {
            return Err(StructureImportError::Binding);
        }
        self.notes.push(Note {
            note_id: note_id.clone(),
            body,
            properties,
        });
        self.note_observations.push(ImportedNoteObservation {
            note_id,
            wrapper_node_id: object.common.node_id.clone(),
            source_anchor: source_anchor.clone(),
            body_anchor: body_anchor.clone(),
            paragraph_id,
            native_kind: marker.name().local_name().into(),
            native_instance_id: envelope.native_instance_id,
            native_attributes: attributes(marker),
        });
        // Equivalent node budget accounting to the original self.node path.
        self.stats.nodes += 1;
        if self.stats.nodes > DocumentGraphLimits::default().max_nodes {
            return Err(StructureImportError::Limit);
        }
        inlines.push(Inline::ControlRef {
            node_id: object.common.node_id.clone(),
        });
        attached.push(wrapper);
        Ok(true)
    }
}
pub(super) fn finish_notes(
    source: &ImportedSourcePackage,
    draft: &mut DocumentGraphDraft,
    observations: &[ImportedNoteObservation],
) -> Result<(), StructureImportError> {
    let mut seen = BTreeSet::new();
    for observation in observations {
        if !seen.insert(observation.source_anchor.opaque_handle.clone()) {
            return Err(StructureImportError::Binding);
        }
    }
    let mut source_notes = BTreeSet::new();
    for path in source.spine() {
        let part = source
            .parts()
            .iter()
            .find(|p| p.path() == path)
            .ok_or(StructureImportError::Binding)?;
        let xml = part.xml().ok_or(StructureImportError::Binding)?;
        let root = element(xml, xml.root_element())?;
        if root.name().namespace() != Some(SECTION_NS) || root.name().local_name() != "sec" {
            continue;
        }
        for (index, node) in xml.elements().iter().enumerate() {
            if named(node, "footNote") || named(node, "endNote") {
                source_notes.insert(
                    part.element_anchor(index)
                        .ok_or(StructureImportError::Binding)?
                        .opaque_handle
                        .clone(),
                );
            }
        }
    }
    if seen != source_notes {
        return Err(StructureImportError::Binding);
    }
    if !seen.is_empty() {
        draft.metadata.insert(
            "note_import_profile",
            PropertyValue::Text(NOTE_IMPORT_PROFILE.into()),
        );
        draft.metadata.insert(
            "note_import_scope",
            PropertyValue::Text(NOTE_IMPORT_SCOPE.into()),
        );
    }
    Ok(())
}
