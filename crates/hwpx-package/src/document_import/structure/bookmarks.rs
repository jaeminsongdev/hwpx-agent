//! Actual point-marker source anchors, not native navigation or link parameters.
use super::{
    DocumentGraphDraft, DocumentGraphLimits, ImportedSourcePackage, ImportedSourcePart, Inline,
    LogicalId, Mapper, Node, Properties, PropertyValue, SECTION_NS, Serialize,
    StructureImportError, children, element, fmt, id, named,
};
use domain_ir::{Reference, SourceAnchorHandle};
use std::collections::BTreeSet;

pub const BOOKMARK_IMPORT_PROFILE: &str = "hwpx-agent.document-import-bookmarks/partial-v1";
pub const BOOKMARK_IMPORT_SCOPE: &str =
    "observed_source_point_anchor_not_native_name_resolution_internal_link_or_execution";

/// Exact XML run and non-bookmark child boundary within the observed paragraph.
/// Not an imported-inline index, flattened LinkPoint, page or native cursor.
#[derive(Clone, Copy, Eq, PartialEq)]
pub struct ImportedBookmarkSourcePoint {
    run_ordinal: u32,
    non_bookmark_inline_ordinal: u32,
}
impl fmt::Debug for ImportedBookmarkSourcePoint {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ImportedBookmarkSourcePoint(<redacted>; source_local_only)")
    }
}
impl ImportedBookmarkSourcePoint {
    #[must_use]
    pub const fn run_ordinal(self) -> u32 {
        self.run_ordinal
    }
    /// Counts original XML run children, excluding all bookmark wrappers.
    #[must_use]
    pub const fn non_bookmark_inline_ordinal(self) -> u32 {
        self.non_bookmark_inline_ordinal
    }
}

/// Original section identity and XML paragraph order, including opaque native
/// paragraphs. Not typed graph traversal order, page flow or native authority.
#[derive(Clone, Eq, PartialEq)]
pub struct ImportedBookmarkSectionLocation {
    section_id: LogicalId,
    paragraph_ordinal: u32,
    source_paragraph_count: u32,
}
impl fmt::Debug for ImportedBookmarkSectionLocation {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ImportedBookmarkSectionLocation(<redacted>; source_xml_order_only)")
    }
}
impl ImportedBookmarkSectionLocation {
    #[must_use]
    pub const fn section_id(&self) -> &LogicalId {
        &self.section_id
    }
    #[must_use]
    pub const fn paragraph_ordinal(&self) -> u32 {
        self.paragraph_ordinal
    }
    #[must_use]
    pub const fn source_paragraph_count(&self) -> u32 {
        self.source_paragraph_count
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ImportedBookmarkObservation {
    pub reference_id: LogicalId,
    pub source_anchor: SourceAnchorHandle,
    pub wrapper_node_id: LogicalId,
    pub paragraph_id: LogicalId,
    /// Raw source name, not normalized or logged as a diagnostic.
    pub name: String,
    /// The marker's actual position in this imported paragraph's inline stream.
    pub control_inline_position: usize,
    // Keep the existing serialized source observation and target fingerprint.
    // This derived point is already computed by the exact original lowerer.
    #[serde(skip)]
    source_point: ImportedBookmarkSourcePoint,
    #[serde(skip)]
    section_location: ImportedBookmarkSectionLocation,
}
impl ImportedBookmarkObservation {
    #[must_use]
    pub const fn source_point(&self) -> ImportedBookmarkSourcePoint {
        self.source_point
    }
    #[must_use]
    pub const fn section_location(&self) -> &ImportedBookmarkSectionLocation {
        &self.section_location
    }
}
impl fmt::Debug for ImportedBookmarkObservation {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ImportedBookmarkObservation(<redacted>)")
    }
}
impl Mapper<'_> {
    pub(super) fn bookmark_wrapper(
        &mut self,
        part: &ImportedSourcePart,
        index: usize,
        inlines: &mut Vec<Inline>,
        attached: &mut Vec<Node>,
    ) -> Result<bool, StructureImportError> {
        let xml = part.xml().ok_or(StructureImportError::Binding)?;
        if !named(element(xml, index)?, "ctrl") {
            return Ok(false);
        }
        let candidates: Vec<_> = children(xml, index)?
            .into_iter()
            .filter(|child| element(xml, *child).is_ok_and(|v| named(v, "bookmark")))
            .collect();
        if candidates.is_empty() {
            return Ok(false);
        }
        if candidates.len() != 1
            || self.bookmarks.len() >= DocumentGraphLimits::default().max_references
        {
            return Err(StructureImportError::Binding);
        }
        let envelope = crate::bookmark_hwpx::read_imported_point_bookmark(xml, candidates[0])
            .map_err(|error| StructureImportError::Bookmark { code: error.code() })?;
        if envelope.wrapper_element != index {
            return Err(StructureImportError::Binding);
        }
        let anchor = part
            .element_anchor(candidates[0])
            .ok_or(StructureImportError::Binding)?;
        self.source.resolve_anchor(anchor)?;
        let reference_id = id("bookmark-reference", anchor)?;
        let paragraph_id = id(
            "node",
            part.element_anchor(envelope.paragraph_element)
                .ok_or(StructureImportError::Binding)?,
        )?;
        let mut wrapper = self.opaque(part, index)?;
        let Node::EmbeddedObject(object) = &mut wrapper else {
            return Err(StructureImportError::Binding);
        };
        object.properties.insert(
            "source_bookmark_reference",
            PropertyValue::Id(reference_id.clone()),
        );
        object.properties.insert(
            "source_bookmark_name",
            PropertyValue::Text(envelope.name.clone()),
        );
        object.properties.insert(
            "source_bookmark_anchor",
            PropertyValue::Id(anchor.opaque_handle.clone()),
        );
        self.bookmarks.push(ImportedBookmarkObservation {
            reference_id: reference_id.clone(),
            source_anchor: anchor.clone(),
            wrapper_node_id: object.common.node_id.clone(),
            paragraph_id,
            name: envelope.name,
            control_inline_position: inlines.len(),
            source_point: ImportedBookmarkSourcePoint {
                run_ordinal: envelope.source_run_ordinal,
                non_bookmark_inline_ordinal: envelope.source_inline_ordinal,
            },
            section_location: ImportedBookmarkSectionLocation {
                section_id: self.source_section_id.clone().ok_or(StructureImportError::Binding)?,
                paragraph_ordinal: u32::try_from(self.source_paragraph_order
                    .binary_search(&envelope.paragraph_element).map_err(|_| StructureImportError::Binding)?)
                    .map_err(|_| StructureImportError::Limit)?,
                source_paragraph_count: u32::try_from(self.source_paragraph_order.len())
                    .map_err(|_| StructureImportError::Limit)?,
            },
        });
        self.stats.nodes += 1;
        if self.stats.nodes > DocumentGraphLimits::default().max_nodes {
            return Err(StructureImportError::Limit);
        }
        // Keep the original control/source wrapper. Add the backend-neutral
        // bookmark anchor at the same point, rather than dropping source data.
        inlines.push(Inline::ControlRef {
            node_id: object.common.node_id.clone(),
        });
        inlines.push(Inline::BookmarkAnchor { reference_id });
        attached.push(wrapper);
        Ok(true)
    }
}
pub(super) fn finish_bookmarks(
    source: &ImportedSourcePackage,
    draft: &mut DocumentGraphDraft,
    observations: &[ImportedBookmarkObservation],
) -> Result<(), StructureImportError> {
    let mut seen = BTreeSet::new();
    for value in observations {
        if !seen.insert(value.source_anchor.opaque_handle.clone()) {
            return Err(StructureImportError::Binding);
        }
        let mut properties = Properties::new();
        properties.insert(
            "source_reference_kind",
            PropertyValue::Text("point_bookmark".into()),
        );
        properties.insert(
            "source_anchor",
            PropertyValue::Id(value.source_anchor.opaque_handle.clone()),
        );
        properties.insert(
            "source_bookmark_name",
            PropertyValue::Text(value.name.clone()),
        );
        properties.insert(
            "source_paragraph_id",
            PropertyValue::Id(value.paragraph_id.clone()),
        );
        properties.insert(
            "qualification",
            PropertyValue::Text(BOOKMARK_IMPORT_SCOPE.into()),
        );
        draft.references.push(Reference {
            reference_id: value.reference_id.clone(),
            target_node_id: Some(value.wrapper_node_id.clone()),
            properties,
        });
    }
    let mut source_bookmarks = BTreeSet::new();
    for path in source.spine() {
        let part = source
            .parts()
            .iter()
            .find(|v| v.path() == path)
            .ok_or(StructureImportError::Binding)?;
        let xml = part.xml().ok_or(StructureImportError::Binding)?;
        let root = element(xml, xml.root_element())?;
        if root.name().namespace() != Some(SECTION_NS) || root.name().local_name() != "sec" {
            continue;
        }
        for (index, marker) in xml.elements().iter().enumerate() {
            if named(marker, "bookmark") {
                source_bookmarks.insert(
                    part.element_anchor(index)
                        .ok_or(StructureImportError::Binding)?
                        .opaque_handle
                        .clone(),
                );
            }
        }
    }
    if seen != source_bookmarks {
        return Err(StructureImportError::Binding);
    }
    if !seen.is_empty() {
        draft.metadata.insert(
            "bookmark_import_profile",
            PropertyValue::Text(BOOKMARK_IMPORT_PROFILE.into()),
        );
        draft.metadata.insert(
            "bookmark_import_scope",
            PropertyValue::Text(BOOKMARK_IMPORT_SCOPE.into()),
        );
    }
    Ok(())
}
