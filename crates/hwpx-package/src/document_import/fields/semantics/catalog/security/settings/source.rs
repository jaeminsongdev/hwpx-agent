use super::{ImportedColumnSettings, ImportedSectionSettings, SectionSettingsImportError};
use crate::{
    BoundedZipReader, PageSetupLimits, PageSetupReader, PreservingXmlDocument, SectionColumnLimits,
    SectionColumnReader,
    document_import::{ImportedSourcePackage, ImportedSourcePart},
};
use domain_ir::{LogicalId, PropertyValue, Section, SourceAnchorHandle};
use sha2::{Digest as _, Sha256};
use std::{collections::BTreeMap, io::Cursor};
const HS: &str = "http://www.hancom.co.kr/hwpml/2011/section";
const HP: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";

pub(super) fn bind(
    source: &ImportedSourcePackage,
    sections: &mut [Section],
) -> Result<(Vec<ImportedSectionSettings>, [u8; 32]), SectionSettingsImportError> {
    let mut reader = BoundedZipReader::open(
        Cursor::new(source.original.as_ref()),
        source
            .limits
            .zip()
            .map_err(|_| SectionSettingsImportError::Binding)?,
    )
    .map_err(|_| SectionSettingsImportError::Binding)?;
    let indexes: BTreeMap<_, _> = reader
        .entries()
        .iter()
        .enumerate()
        .map(|(i, e)| (e.path.as_str().to_owned(), i))
        .collect();
    let header = source
        .parts()
        .iter()
        .find(|p| p.path().as_str() == "Contents/header.xml")
        .ok_or(SectionSettingsImportError::Binding)?;
    let header_bytes = read_part(&mut reader, &indexes, header)?;
    let parts: BTreeMap<_, _> = source.parts().iter().map(|p| (p.path(), p)).collect();
    let mut ordered = Vec::new();
    for path in source.spine() {
        let part = *parts.get(path).ok_or(SectionSettingsImportError::Binding)?;
        let xml = part.xml().ok_or(SectionSettingsImportError::Binding)?;
        let root = &xml.elements()[xml.root_element()];
        if root.name().namespace() == Some(HS) && root.name().local_name() == "sec" {
            ordered.push((part, read_part(&mut reader, &indexes, part)?));
        }
    }
    if sections.len() != ordered.len() {
        return Err(SectionSettingsImportError::Binding);
    }
    let mut pages = Vec::new();
    for (_, bytes) in &ordered {
        let page = PageSetupReader::read(bytes, PageSetupLimits::default())?;
        pages.push((page, page.metrics(PageSetupLimits::default())?));
    }
    let input: Vec<_> = ordered
        .iter()
        .zip(&pages)
        .map(|((_, bytes), (_, metrics))| (bytes.as_slice(), metrics.body_width))
        .collect();
    let columns = SectionColumnReader::read_sequence_with_header(
        &header_bytes,
        &input,
        SectionColumnLimits::default(),
    )?;
    let mut result = Vec::new();
    for (((part, _), (page, metrics)), (section, columns)) in ordered
        .iter()
        .zip(pages)
        .zip(sections.iter_mut().zip(columns.sections))
    {
        result.push(bind_section(source, part, section, page, metrics, columns)?);
    }
    Ok((result, header.anchor().fingerprint_sha256))
}
fn bind_section(
    source: &ImportedSourcePackage,
    part: &ImportedSourcePart,
    section: &mut Section,
    page: crate::PageSetup,
    metrics: crate::PageSetupMetrics,
    columns: crate::SectionColumns,
) -> Result<ImportedSectionSettings, SectionSettingsImportError> {
    let id = LogicalId::parse(format!("section-{}", part.anchor().opaque_handle.as_str()))
        .map_err(|_| SectionSettingsImportError::Graph)?;
    let resource = LogicalId::parse(format!("resource-{}", part.anchor().opaque_handle.as_str()))
        .map_err(|_| SectionSettingsImportError::Graph)?;
    if section.section_id != id
        || !section
            .properties
            .iter()
            .any(|(k, v)| k == "source_part" && *v == PropertyValue::Id(resource.clone()))
    {
        return Err(SectionSettingsImportError::Binding);
    }
    let xml = part.xml().ok_or(SectionSettingsImportError::Binding)?;
    let sec_index = unique_index(xml, "secPr")?;
    let page_index = unique_index(xml, "pagePr")?;
    let col_indexes: Vec<_> = xml
        .elements()
        .iter()
        .enumerate()
        .filter(|(_, e)| e.name().namespace() == Some(HP) && e.name().local_name() == "colPr")
        .map(|(i, _)| i)
        .collect();
    if columns.spans.len() != col_indexes.len() {
        return Err(SectionSettingsImportError::Binding);
    }
    let mut bindings = Vec::new();
    for (index, definition) in col_indexes.iter().zip(columns.spans) {
        let column_metrics =
            definition.metrics(metrics.body_width, SectionColumnLimits::default())?;
        bindings.push(ImportedColumnSettings {
            source_anchor: anchor(source, part, *index)?,
            definition,
            metrics: column_metrics,
        });
    }
    section
        .properties
        .insert("source_page_setup", source_tree(part, page_index)?);
    section.properties.insert(
        "source_column_spans",
        PropertyValue::List(
            col_indexes
                .iter()
                .map(|i| source_tree(part, *i))
                .collect::<Result<Vec<_>, _>>()?,
        ),
    );
    section.properties.insert(
        "source_page_body_width",
        PropertyValue::Integer(i64::from(metrics.body_width)),
    );
    section.properties.insert(
        "source_page_body_height",
        PropertyValue::Integer(i64::from(metrics.body_height)),
    );
    Ok(ImportedSectionSettings {
        section_id: id,
        source_anchor: part.anchor().clone(),
        section_properties_anchor: anchor(source, part, sec_index)?,
        page_anchor: anchor(source, part, page_index)?,
        page,
        metrics,
        columns: bindings,
    })
}

fn read_part(
    reader: &mut BoundedZipReader<Cursor<&[u8]>>,
    indexes: &BTreeMap<String, usize>,
    part: &ImportedSourcePart,
) -> Result<Vec<u8>, SectionSettingsImportError> {
    let index = *indexes
        .get(part.path().as_str())
        .ok_or(SectionSettingsImportError::Binding)?;
    let bytes = reader
        .read_entry(index)
        .map_err(|_| SectionSettingsImportError::Binding)?;
    if <[u8; 32]>::from(Sha256::digest(&bytes)) != part.anchor().fingerprint_sha256 {
        return Err(SectionSettingsImportError::Binding);
    }
    Ok(bytes)
}
fn unique_index(
    xml: &PreservingXmlDocument,
    tag: &str,
) -> Result<usize, SectionSettingsImportError> {
    let mut found = xml
        .elements()
        .iter()
        .enumerate()
        .filter(|(_, e)| e.name().namespace() == Some(HP) && e.name().local_name() == tag);
    let (index, _) = found.next().ok_or(SectionSettingsImportError::Binding)?;
    if found.next().is_some() {
        return Err(SectionSettingsImportError::Binding);
    }
    Ok(index)
}
fn anchor(
    source: &ImportedSourcePackage,
    part: &ImportedSourcePart,
    index: usize,
) -> Result<SourceAnchorHandle, SectionSettingsImportError> {
    let anchor = part
        .element_anchor(index)
        .ok_or(SectionSettingsImportError::Binding)?;
    source
        .resolve_anchor(anchor)
        .map_err(|_| SectionSettingsImportError::Binding)?;
    Ok(anchor.clone())
}
fn source_tree(
    part: &ImportedSourcePart,
    index: usize,
) -> Result<PropertyValue, SectionSettingsImportError> {
    let xml = part.xml().ok_or(SectionSettingsImportError::Binding)?;
    let element = xml
        .elements()
        .get(index)
        .ok_or(SectionSettingsImportError::Binding)?;
    let mut record = BTreeMap::new();
    record.insert(
        "source_anchor".into(),
        PropertyValue::Id(
            part.element_anchor(index)
                .ok_or(SectionSettingsImportError::Binding)?
                .opaque_handle
                .clone(),
        ),
    );
    record.insert(
        "native_attributes".into(),
        PropertyValue::Object(
            element
                .attributes()
                .iter()
                .filter(|a| !a.is_namespace_declaration())
                .map(|a| {
                    (
                        a.name().local_name().to_owned(),
                        PropertyValue::Text(a.semantic_value().to_owned()),
                    )
                })
                .collect(),
        ),
    );
    let mut children = Vec::new();
    let mut child = element.first_child();
    while let Some(child_index) = child {
        children.push(source_tree(part, child_index)?);
        child = xml
            .elements()
            .get(child_index)
            .ok_or(SectionSettingsImportError::Binding)?
            .next_sibling();
    }
    record.insert("children".into(), PropertyValue::List(children));
    Ok(PropertyValue::Object(record))
}
