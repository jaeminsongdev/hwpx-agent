//! Original catalog extension for source memoPr definitions and secPr references.
//! No default memo style, native metadata, `CommentState` or mutation authority.
use super::{
    CatalogImportError as Error, DefinitionIndex, ImportedCatalogDefinition, ImportedCatalogKind,
    attribute, attributes, children, element, named, number,
};
use crate::{
    HANCOM_2020_HEAD_NAMESPACE as HH, HANCOM_2020_PARAGRAPH_NAMESPACE as HP, PreservingXmlDocument,
    XmlElementToken,
    document_import::{ImportedSourcePackage, ImportedSourcePart},
};
use domain_ir::{
    DocumentGraphLimits, LogicalId, Properties, PropertyValue, Section, SourceAnchorHandle,
};
use serde::Serialize;
use std::fmt;
#[cfg(test)]
mod tests;

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(tag = "state", rename_all = "snake_case")]
pub enum MemoCatalogBinding {
    NoExplicitReference,
    UnresolvedMissingDefinition,
    Resolved { catalog_id: LogicalId },
}
impl fmt::Debug for MemoCatalogBinding {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("MemoCatalogBinding(<redacted>)")
    }
}
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ImportedSectionMemoCatalogUse {
    pub section_id: LogicalId,
    pub section_anchor: SourceAnchorHandle,
    pub section_properties_anchor: Option<SourceAnchorHandle>,
    pub native_reference: Option<u32>,
    pub native_attributes: Option<Properties>,
    pub binding: MemoCatalogBinding,
}
impl fmt::Debug for ImportedSectionMemoCatalogUse {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ImportedSectionMemoCatalogUse(<redacted>)")
    }
}

pub(super) fn extend_header(
    source: &ImportedSourcePackage,
    part: &ImportedSourcePart,
    xml: &PreservingXmlDocument,
    ref_list: usize,
    definitions: &mut Vec<ImportedCatalogDefinition>,
    index: &mut DefinitionIndex,
) -> Result<(), Error> {
    let matches: Vec<_> = children(xml, ref_list)?
        .into_iter()
        .filter(|i| {
            xml.elements()
                .get(*i)
                .is_some_and(|e| named(e, HH, "memoProperties"))
        })
        .collect();
    if matches.len() > 1 {
        return Err(Error::Duplicate);
    }
    let Some(container) = matches.first().copied() else {
        return Ok(());
    };
    let nodes = children(xml, container)?;
    if number(element(xml, container)?, "itemCnt")? as usize != nodes.len() {
        return Err(Error::Count);
    }
    for node in nodes {
        let e = element(xml, node)?;
        if !named(e, HH, "memoPr") || !children(xml, node)?.is_empty() {
            return Err(Error::Header);
        }
        if let Some(span) = e.content_span()
            && !xml.with_source_bytes(|bytes| {
                bytes[span.start()..span.end()]
                    .iter()
                    .all(u8::is_ascii_whitespace)
            })
        {
            return Err(Error::Header);
        }
        validate_attributes(e)?;
        if definitions.len() >= DocumentGraphLimits::default().max_styles {
            return Err(Error::Limit);
        }
        let native_id = number(e, "id")?;
        let source_anchor = part.element_anchor(node).ok_or(Error::Binding)?.clone();
        source
            .resolve_anchor(&source_anchor)
            .map_err(|_| Error::Binding)?;
        let catalog_id =
            LogicalId::parse(format!("catalog-{}", source_anchor.opaque_handle.as_str()))
                .map_err(|_| Error::Graph)?;
        if index
            .insert(
                (ImportedCatalogKind::MemoProperty, native_id),
                catalog_id.clone(),
            )
            .is_some()
        {
            return Err(Error::Duplicate);
        }
        definitions.push(ImportedCatalogDefinition {
            catalog_id,
            kind: ImportedCatalogKind::MemoProperty,
            native_id,
            source_anchor,
            native_attributes: attributes(e),
            relationships: Properties::new(),
        });
    }
    Ok(())
}
fn validate_attributes(e: &XmlElementToken) -> Result<(), Error> {
    // The pinned native MemoShapeType writes unsigned width/lineWidth, unlike other width tags.
    number(e, "width")?;
    if number(e, "lineWidth")? > 15 {
        return Err(Error::Header);
    }
    let line = attribute(e, "lineType").ok_or(Error::Header)?;
    if ![
        "NONE",
        "SOLID",
        "DOT",
        "DASH",
        "DASH_DOT",
        "DASH_DOT_DOT",
        "LONG_DASH",
        "CIRCLE",
        "DOUBLE_SLIM",
        "SLIM_THICK",
        "THICK_SLIM",
        "SLIM_THICK_SLIM",
        "WAVE",
        "DOUBLEWAVE",
        "THICK3D",
        "THICKREV3D",
        "3D",
        "REV3D",
    ]
    .contains(&line)
    {
        return Err(Error::Header);
    }
    if !["NOMAL", "USER_INSERT", "USER_DELETE", "USER_UPDATE"]
        .contains(&attribute(e, "memoType").ok_or(Error::Header)?)
    {
        return Err(Error::Header);
    }
    for key in ["lineColor", "fillColor", "activeColor"] {
        let value = attribute(e, key).ok_or(Error::Header)?;
        if !(value.eq_ignore_ascii_case("none")
            || (value.len() == 7
                && value.starts_with('#')
                && value.as_bytes()[1..].iter().all(u8::is_ascii_hexdigit)))
        {
            return Err(Error::Header);
        }
    }
    Ok(())
}
pub(super) fn bind_sections(
    source: &ImportedSourcePackage,
    sections: &mut [Section],
    index: &DefinitionIndex,
) -> Result<Vec<ImportedSectionMemoCatalogUse>, Error> {
    let mut uses = Vec::new();
    let mut sections = sections.iter_mut();
    for path in source.spine() {
        let part = source
            .parts()
            .iter()
            .find(|p| p.path() == path)
            .ok_or(Error::Binding)?;
        let xml = part.xml().ok_or(Error::Binding)?;
        if !named(
            element(xml, xml.root_element())?,
            "http://www.hancom.co.kr/hwpml/2011/section",
            "sec",
        ) {
            continue;
        }
        let section = sections.next().ok_or(Error::Binding)?;
        let section_id =
            LogicalId::parse(format!("section-{}", part.anchor().opaque_handle.as_str()))
                .map_err(|_| Error::Graph)?;
        if section.section_id != section_id {
            return Err(Error::Binding);
        }
        let mut found = xml
            .elements()
            .iter()
            .enumerate()
            .filter(|(_, e)| named(e, HP, "secPr"));
        let record = found.next();
        if found.next().is_some() {
            return Err(Error::Duplicate);
        }
        let (anchor, native, native_attributes) = if let Some((i, e)) = record {
            let anchor = part.element_anchor(i).ok_or(Error::Binding)?.clone();
            source.resolve_anchor(&anchor).map_err(|_| Error::Binding)?;
            let native = attribute(e, "memoShapeIDRef")
                .map(super::parse_number)
                .transpose()?;
            (Some(anchor), native, Some(attributes(e)))
        } else {
            (None, None, None)
        };
        let binding = if let Some(native) = native {
            if let Some(catalog_id) = index.get(&(ImportedCatalogKind::MemoProperty, native)) {
                if section
                    .properties
                    .iter()
                    .any(|(k, _)| k == "source_memo_shape_catalog")
                {
                    return Err(Error::Binding);
                }
                section.properties.insert(
                    "source_memo_shape_catalog",
                    PropertyValue::Id(catalog_id.clone()),
                );
                MemoCatalogBinding::Resolved {
                    catalog_id: catalog_id.clone(),
                }
            } else {
                MemoCatalogBinding::UnresolvedMissingDefinition
            }
        } else {
            MemoCatalogBinding::NoExplicitReference
        };
        // Real captured sources have explicit zero refs but NO memoPr definitions.
        // Preserve that unresolved source fact; do not synthesize a default Style or mutate graph.
        uses.push(ImportedSectionMemoCatalogUse {
            section_id,
            section_anchor: part.anchor().clone(),
            section_properties_anchor: anchor,
            native_reference: native,
            native_attributes,
            binding,
        });
    }
    if sections.next().is_some() {
        return Err(Error::Binding);
    }
    Ok(uses)
}
