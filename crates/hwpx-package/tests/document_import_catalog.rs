use domain_ir::{DocumentGraph, DocumentGraphLimits, Flow, Node, Properties, PropertyValue};
use hwpx_package::{
    PreservingXmlDocument,
    document_import::fields::{
        ImportedDocumentFields,
        semantics::{
            ImportedDocumentFieldSemantics,
            catalog::{CatalogImportError, ImportedCatalogKind, ImportedDocumentCatalog},
        },
    },
};
use std::{collections::BTreeSet, error::Error};
#[path = "support/document_import_field_fixture.rs"]
mod base;
#[path = "support/document_import_catalog_fixture.rs"]
mod fixture;
type TestResult = Result<(), Box<dyn Error>>;

fn without(properties: &Properties, key: &str) -> Properties {
    let mut result = Properties::new();
    for (name, value) in properties.iter().filter(|(name, _)| *name != key) {
        result.insert(name, value.clone());
    }
    result
}
fn restore(flow: &mut Flow) {
    for node in &mut flow.children {
        match node {
            Node::Paragraph(paragraph) => {
                paragraph.common.style_refs.clear();
                paragraph.paragraph_properties = without(
                    &paragraph.paragraph_properties,
                    "source_paragraph_property_catalog",
                );
                let mut segments = paragraph
                    .paragraph_properties
                    .iter()
                    .find(|(key, _)| *key == "run_segments")
                    .map(|(_, value)| value.clone());
                if let Some(PropertyValue::List(ref mut segments)) = segments {
                    for segment in segments.iter_mut() {
                        if let PropertyValue::Object(record) = segment {
                            record.remove("source_character_property_catalog");
                        }
                    }
                    paragraph
                        .paragraph_properties
                        .insert("run_segments", PropertyValue::List(segments.clone()));
                }
            }
            Node::Table(table) => {
                for cell in &mut table.cells {
                    restore(&mut cell.body);
                }
            }
            Node::Drawing(drawing) => restore(&mut drawing.children),
            _ => (),
        }
    }
}
#[test]
fn locked_actual26_catalogs_and_source_uses_preserve_whole_original_graph() -> TestResult {
    let mut styles = 0;
    let mut paras = 0;
    let mut chars = 0;
    for bytes in fixture::actual_corpus()? {
        let forms = base::forms(&bytes, "catalog-whole-source")?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
        let catalog = ImportedDocumentCatalog::import(&meanings)?;
        assert_eq!(catalog.verify_source(&bytes)?, *catalog.receipt());
        assert_eq!(catalog.definitions().len(), catalog.graph().styles().len());
        assert_eq!(
            catalog.receipt().paragraph_properties,
            catalog.paragraph_catalog().styles.len()
        );
        assert_eq!(
            catalog.receipt().character_properties,
            catalog.character_catalog().styles.len()
        );
        let ids: BTreeSet<_> = catalog
            .definitions()
            .iter()
            .map(|v| &v.catalog_id)
            .collect();
        assert_eq!(ids.len(), catalog.definitions().len());
        for definition in catalog.definitions() {
            let resolved = forms.source().resolve_anchor(&definition.source_anchor)?;
            assert!(resolved.element().is_some());
            for (_, target) in definition.relationships.iter() {
                let PropertyValue::Id(target) = target else {
                    return Err("source relationship kind".into());
                };
                assert!(ids.contains(target));
            }
        }
        for used in catalog.uses() {
            assert!(
                forms
                    .source()
                    .resolve_anchor(&used.source_anchor)?
                    .element()
                    .is_some()
            );
            for target in [&used.named_style, &used.paragraph_property]
                .into_iter()
                .flatten()
            {
                assert!(ids.contains(target));
            }
            for run in &used.runs {
                assert!(
                    forms
                        .source()
                        .resolve_anchor(&run.source_anchor)?
                        .element()
                        .is_some()
                );
                if let Some(target) = &run.character_property {
                    assert!(ids.contains(target));
                }
            }
        }
        // Removing exactly this stage's additions restores EVERY original field,
        // note/bookmark/form/body/security/resource/opaque/source property.
        let mut draft = catalog.graph().clone().into_draft();
        draft.styles.clear();
        draft.metadata = meanings.graph().clone().into_draft().metadata;
        for section in &mut draft.sections {
            restore(&mut section.body);
        }
        for note in &mut draft.notes {
            restore(&mut note.body);
        }
        assert_eq!(
            DocumentGraph::from_draft(draft, DocumentGraphLimits::default())?,
            *meanings.graph()
        );
        styles += catalog.receipt().named_styles;
        paras += catalog.receipt().paragraph_properties;
        chars += catalog.receipt().character_properties;
    }
    assert_eq!((styles, paras, chars), (572, 520, 183));
    Ok(())
}
fn reject(bytes: &[u8], predicate: impl FnOnce(&CatalogImportError) -> bool) -> TestResult {
    let forms = base::forms(bytes, "catalog-rejection")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let error = ImportedDocumentCatalog::import(&meanings)
        .err()
        .ok_or("unexpected catalog acceptance")?;
    assert!(predicate(&error));
    Ok(())
}
#[test]
fn each_body_style_paragraph_and_character_reference_must_resolve() -> TestResult {
    let captured = base::captured()?;
    for (tag, key) in [
        ("p", "styleIDRef"),
        ("p", "paraPrIDRef"),
        ("run", "charPrIDRef"),
    ] {
        let bytes =
            fixture::change_attribute(&captured, "Contents/section0.xml", tag, key, "4294967295")?;
        reject(&bytes, |e| matches!(e, CatalogImportError::Dangling))?;
    }
    Ok(())
}
#[test]
fn each_named_style_relationship_resolves_without_guessing_inheritance() -> TestResult {
    let captured = base::captured()?;
    for key in ["nextStyleIDRef", "charPrIDRef", "paraPrIDRef"] {
        let bytes = fixture::change_attribute(
            &captured,
            "Contents/header.xml",
            "style",
            key,
            "4294967295",
        )?;
        reject(&bytes, |e| matches!(e, CatalogImportError::Dangling))?;
    }
    let forms = base::forms(&captured, "next-is-not-inheritance")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let catalog = ImportedDocumentCatalog::import(&meanings)?;
    assert!(
        catalog
            .graph()
            .styles()
            .iter()
            .all(|v| v.based_on.is_none())
    );
    assert!(
        catalog
            .definitions()
            .iter()
            .filter(|v| v.kind == ImportedCatalogKind::NamedStyle)
            .all(|v| v.relationships.len() == 3)
    );
    Ok(())
}
#[test]
fn missing_attributes_do_not_invent_defaults_and_original_foreign_guard_stays_closed() -> TestResult
{
    let header = String::from_utf8(fixture::read_part(
        &base::captured()?,
        "Contents/header.xml",
    )?)?;
    let foreign = base::package(
        "<hp:p id='1' u:styleIDRef='999999' u:paraPrIDRef='999999'><hp:run u:charPrIDRef='999999'><hp:t>source only</hp:t></hp:run></hp:p>",
    )?;
    assert!(base::forms(&foreign, "original-foreign-guard").is_err());
    let package = base::package("<hp:p id='1'><hp:run><hp:t>source only</hp:t></hp:run></hp:p>")?;
    let package = fixture::mutate_part(&package, "Contents/header.xml", |_| Ok(header))?;
    let forms = base::forms(&package, "no-caller-defaults")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let catalog = ImportedDocumentCatalog::import(&meanings)?;
    assert_eq!(catalog.receipt().paragraphs, 1);
    assert_eq!(catalog.receipt().runs, 1);
    assert_eq!(catalog.receipt().explicit_named_style_uses, 0);
    assert_eq!(catalog.receipt().explicit_paragraph_property_uses, 0);
    assert_eq!(catalog.receipt().explicit_character_property_uses, 0);
    assert_eq!(catalog.verify_source(&package)?, *catalog.receipt());
    Ok(())
}
#[test]
fn duplicate_named_ids_and_declared_counts_are_rejected() -> TestResult {
    let captured = base::captured()?;
    let count_bad =
        fixture::change_attribute(&captured, "Contents/header.xml", "styles", "itemCnt", "23")?;
    reject(&count_bad, |e| matches!(e, CatalogImportError::Count))?;
    let duplicate = fixture::mutate_part(&captured, "Contents/header.xml", |text| {
        let xml = PreservingXmlDocument::parse(text.as_bytes())?;
        let first = xml
            .elements()
            .iter()
            .find(|e| e.name().local_name() == "style")
            .ok_or("style missing")?;
        let span = first.start_tag_span();
        let fragment = &text[span.start()..span.end()];
        let end = text.find("</hh:styles>").ok_or("styles end missing")?;
        let mut changed = text.to_owned();
        changed.insert_str(end, fragment);
        Ok(changed)
    })?;
    let duplicate =
        fixture::change_attribute(&duplicate, "Contents/header.xml", "styles", "itemCnt", "23")?;
    reject(&duplicate, |e| matches!(e, CatalogImportError::Duplicate))?;
    Ok(())
}
#[test]
fn original_typed_readers_reject_bad_values_without_source_only_fallback() -> TestResult {
    let captured = base::captured()?;
    let character_bad = fixture::change_attribute(
        &captured,
        "Contents/header.xml",
        "charPr",
        "height",
        "invalid",
    )?;
    reject(&character_bad, |e| {
        matches!(e, CatalogImportError::Character { .. })
    })?;
    let paragraph_bad = fixture::change_attribute(
        &captured,
        "Contents/header.xml",
        "paraPr",
        "condense",
        "999",
    )?;
    reject(&paragraph_bad, |e| {
        matches!(e, CatalogImportError::Paragraph { .. })
    })?;
    let minimal = base::package("<hp:p id='1'><hp:run><hp:t>body</hp:t></hp:run></hp:p>")?;
    reject(&minimal, |e| matches!(e, CatalogImportError::Header))?;
    Ok(())
}
#[test]
fn numeric_reference_errors_fresh_drift_and_debug_are_closed() -> TestResult {
    let captured = base::captured()?;
    for bad in ["-1", "+0", " 0", "4294967296", ""] {
        let bytes = fixture::change_attribute(
            &captured,
            "Contents/header.xml",
            "style",
            "nextStyleIDRef",
            bad,
        )?;
        reject(&bytes, |e| matches!(e, CatalogImportError::Id))?;
    }
    let forms = base::forms(&captured, "catalog-privacy")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let catalog = ImportedDocumentCatalog::import(&meanings)?;
    let changed = fixture::change_attribute(
        &captured,
        "Contents/header.xml",
        "style",
        "nextStyleIDRef",
        "1",
    )?;
    assert!(catalog.verify_source(&changed).is_err());
    assert!(!format!("{catalog:?}").contains("catalog-privacy"));
    assert_eq!(
        format!("{:?}", catalog.definitions()[0]),
        "ImportedCatalogDefinition(<redacted>)"
    );
    assert_eq!(
        format!("{:?}", catalog.uses()[0]),
        "ImportedParagraphCatalogUse(<redacted>)"
    );
    assert!(!serde_json::to_string(catalog.receipt())?.contains("native_attributes"));
    Ok(())
}
