use super::super::{
    ImportedCatalogKind, ImportedDocumentCatalog, attributes, children, element, named, number,
    object, one_child,
};
use super::{
    FontCatalogImportError as Error, ImportedCharacterFontLink, ImportedFontDefinition,
    ImportedFontLanguage as Language,
};
use crate::{HANCOM_2020_HEAD_NAMESPACE as HH, LanguageSlot, LanguageValues};
use domain_ir::{LogicalId, Properties, PropertyValue, Style};
use sha2::{Digest as _, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    io,
};
const LANGUAGES: [(LanguageSlot, Language); 7] = [
    (LanguageSlot::Hangul, Language::Hangul),
    (LanguageSlot::Latin, Language::Latin),
    (LanguageSlot::Hanja, Language::Hanja),
    (LanguageSlot::Japanese, Language::Japanese),
    (LanguageSlot::Other, Language::Other),
    (LanguageSlot::Symbol, Language::Symbol),
    (LanguageSlot::User, Language::User),
];
const MAX_WORK: usize = 8_000_000;
pub(super) fn bind(
    catalog: &ImportedDocumentCatalog<'_, '_, '_>,
    styles: &mut Vec<Style>,
) -> Result<(Vec<ImportedFontDefinition>, Vec<ImportedCharacterFontLink>), Error> {
    let source = catalog.meanings.fields.forms.source();
    let part = source
        .parts()
        .iter()
        .find(|p| p.path().as_str() == "Contents/header.xml")
        .ok_or(Error::Binding)?;
    let xml = part.xml().ok_or(Error::Binding)?;
    let root = xml.root_element();
    if !named(element(xml, root)?, HH, "head") {
        return Err(Error::Binding);
    }
    let mapping = one_child(xml, root, "refList")?;
    let fontfaces = one_child(xml, mapping, "fontfaces")?;
    let groups = children(xml, fontfaces)?;
    let original = &catalog.character_catalog().font_faces;
    if groups.len() != original.len() || original.len() != LANGUAGES.len() {
        return Err(Error::Binding);
    }
    let mut definitions = Vec::new();
    let mut index = BTreeMap::new();
    let mut work = 0;
    let mut graph_ids: BTreeSet<_> = styles.iter().map(|s| s.style_id.clone()).collect();
    for ((group_index, read), (slot, language)) in groups.iter().zip(original).zip(LANGUAGES) {
        let group = element(xml, *group_index)?;
        let lang = group
            .attributes()
            .iter()
            .find(|a| a.name().namespace().is_none() && a.name().local_name() == "lang")
            .ok_or(Error::Binding)?;
        if !named(group, HH, "fontface")
            || read.language != slot
            || lang.semantic_value() != language.name().to_ascii_uppercase()
        {
            return Err(Error::Binding);
        }
        let font_indexes = children(xml, *group_index)?;
        if font_indexes.len() != read.fonts.len() {
            return Err(Error::Binding);
        }
        for (font_index, declared) in font_indexes.into_iter().zip(&read.fonts) {
            add_work(&mut work, 1)?;
            let node = element(xml, font_index)?;
            if !named(node, HH, "font") || number(node, "id")? != declared.id {
                return Err(Error::Binding);
            }
            let anchor = part
                .element_anchor(font_index)
                .ok_or(Error::Binding)?
                .clone();
            source.resolve_anchor(&anchor).map_err(|_| Error::Binding)?;
            let font_id = LogicalId::parse(format!("font-{}", anchor.opaque_handle.as_str()))
                .map_err(|_| Error::Graph)?;
            if index
                .insert((language, declared.id), font_id.clone())
                .is_some()
                || !graph_ids.insert(font_id.clone())
            {
                return Err(Error::Binding);
            }
            let mut properties = Properties::new();
            properties.insert(
                "source_font_definition",
                PropertyValue::Text(language.name().into()),
            );
            properties.insert(
                "source_anchor",
                PropertyValue::Id(anchor.opaque_handle.clone()),
            );
            properties.insert("native_attributes", object(&attributes(node)));
            properties.insert(
                "source_payload_sha256",
                PropertyValue::Text(crate::document_import::hex_digest(
                    anchor.fingerprint_sha256,
                )),
            );
            styles.push(Style {
                style_id: font_id.clone(),
                based_on: None,
                properties,
            });
            definitions.push(ImportedFontDefinition {
                font_id,
                language,
                source_anchor: anchor,
                declared: declared.clone(),
            });
        }
    }
    let mut links = Vec::new();
    for definition in catalog
        .definitions()
        .iter()
        .filter(|d| d.kind == ImportedCatalogKind::CharacterProperty)
    {
        let declared = catalog
            .character_catalog()
            .styles
            .iter()
            .find(|c| c.id == definition.native_id)
            .ok_or(Error::Binding)?;
        let resolved = source
            .resolve_anchor(&definition.source_anchor)
            .map_err(|_| Error::Binding)?;
        if resolved.part().anchor() != part.anchor() {
            return Err(Error::Binding);
        }
        let char_index = resolved.element_index().ok_or(Error::Binding)?;
        if !named(element(xml, char_index)?, HH, "charPr") {
            return Err(Error::Binding);
        }
        let fontref_index = one_child(xml, char_index, "fontRef")?;
        let node = element(xml, fontref_index)?;
        let anchor = part
            .element_anchor(fontref_index)
            .ok_or(Error::Binding)?
            .clone();
        source.resolve_anchor(&anchor).map_err(|_| Error::Binding)?;
        let style = styles
            .iter_mut()
            .find(|s| s.style_id == definition.catalog_id)
            .ok_or(Error::Binding)?;
        if style.properties.get("source_font_links").is_some() {
            return Err(Error::Binding);
        }
        let mut source_links = Vec::new();
        for (_, language) in LANGUAGES {
            add_work(&mut work, 1)?;
            let native_id = value(&declared.font_refs, language);
            if number(node, language.name())? != native_id {
                return Err(Error::Binding);
            }
            let font_id = index
                .get(&(language, native_id))
                .ok_or(Error::Binding)?
                .clone();
            let mut data = BTreeMap::new();
            data.insert(
                "language".into(),
                PropertyValue::Text(language.name().into()),
            );
            data.insert("font".into(), PropertyValue::Id(font_id.clone()));
            data.insert(
                "source_anchor".into(),
                PropertyValue::Id(anchor.opaque_handle.clone()),
            );
            source_links.push(PropertyValue::Object(data));
            links.push(ImportedCharacterFontLink {
                character_property_id: definition.catalog_id.clone(),
                font_reference_anchor: anchor.clone(),
                language,
                font_id,
            });
        }
        style
            .properties
            .insert("source_font_links", PropertyValue::List(source_links));
    }
    if links.len()
        != catalog
            .character_catalog()
            .styles
            .len()
            .checked_mul(7)
            .ok_or(Error::Limit)?
    {
        return Err(Error::Binding);
    }
    Ok((definitions, links))
}
fn value(values: &LanguageValues<u32>, language: Language) -> u32 {
    match language {
        Language::Hangul => values.hangul,
        Language::Latin => values.latin,
        Language::Hanja => values.hanja,
        Language::Japanese => values.japanese,
        Language::Other => values.other,
        Language::Symbol => values.symbol,
        Language::User => values.user,
    }
}
fn add_work(work: &mut usize, n: usize) -> Result<(), Error> {
    *work = work
        .checked_add(n)
        .filter(|n| *n <= MAX_WORK)
        .ok_or(Error::Limit)?;
    Ok(())
}
struct BoundedHash {
    hash: Sha256,
    bytes: usize,
}
impl io::Write for BoundedHash {
    fn write(&mut self, bytes: &[u8]) -> io::Result<usize> {
        self.bytes = self
            .bytes
            .checked_add(bytes.len())
            .filter(|n| *n <= 16 * 1024 * 1024)
            .ok_or_else(|| io::Error::other("font links evidence budget"))?;
        self.hash.update(bytes);
        Ok(bytes.len())
    }
    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}
pub(super) fn digest(links: &[ImportedCharacterFontLink]) -> Result<[u8; 32], Error> {
    let mut writer = BoundedHash {
        hash: Sha256::new(),
        bytes: 0,
    };
    serde_json::to_writer(&mut writer, links).map_err(|_| Error::Limit)?;
    Ok(writer.hash.finalize().into())
}
