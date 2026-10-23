use hwpx_package::{
    PreservingXmlDocument,
    document_import::fields::{
        ImportedDocumentFields,
        semantics::{
            ImportedDocumentFieldSemantics,
            catalog::{ImportedDocumentCatalog, fonts::ImportedDocumentFonts},
        },
    },
};
use std::{collections::BTreeSet, error::Error};
#[path = "support/document_import_fonts_fixture.rs"]
mod fixture;
#[path = "support/document_import_settings_inputs.rs"]
mod inputs;
#[path = "support/document_import_catalog_fixture.rs"]
mod mutation;
type TestResult = Result<(), Box<dyn Error>>;
#[test]
fn actual36_whole_font_definitions_all_language_links_fresh_and_graph_inverse() -> TestResult {
    let inputs = inputs::actual_corpus()?;
    assert_eq!(inputs.len(), 36);
    assert_eq!(&inputs[..26], mutation::actual_corpus()?.as_slice());
    for bytes in inputs {
        let forms = fixture::forms(&bytes, "actual-font-test")?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
        let catalog = ImportedDocumentCatalog::import(&meanings)?;
        let fonts = ImportedDocumentFonts::import(&catalog)?;
        fixture::verify_whole(&forms, &catalog, &fonts)?;
        assert_eq!(fonts.verify_source(&bytes)?, *fonts.receipt());
        assert_eq!(fonts.receipt().source_font_groups, 7);
        for chunk in fonts.links().chunks_exact(7) {
            let languages: BTreeSet<_> = chunk.iter().map(|l| l.language).collect();
            assert_eq!(languages.len(), 7);
            assert!(
                chunk
                    .iter()
                    .all(|l| l.character_property_id == chunk[0].character_property_id)
            );
        }
    }
    Ok(())
}
#[test]
fn same_native_font_id_in_seven_languages_never_aliases_logical_identity() -> TestResult {
    let forms = fixture::forms(&inputs::actual_corpus()?[0], "font-identity")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let catalog = ImportedDocumentCatalog::import(&meanings)?;
    let fonts = ImportedDocumentFonts::import(&catalog)?;
    let zeros: Vec<_> = fonts
        .definitions()
        .iter()
        .filter(|f| f.declared.id == 0)
        .collect();
    assert_eq!(zeros.len(), 7);
    assert_eq!(
        zeros
            .iter()
            .map(|f| &f.font_id)
            .collect::<BTreeSet<_>>()
            .len(),
        7
    );
    assert_eq!(
        zeros
            .iter()
            .map(|f| f.language)
            .collect::<BTreeSet<_>>()
            .len(),
        7
    );
    Ok(())
}
#[test]
fn changed_source_declaration_never_reuses_original_binding_or_claims_availability() -> TestResult {
    let bytes = &inputs::actual_corpus()?[0];
    let changed = mutation::change_attribute(
        bytes,
        "Contents/header.xml",
        "font",
        "face",
        "FONT-SOURCE-MARKER",
    )?;
    let forms = fixture::forms(bytes, "font-freshness")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let catalog = ImportedDocumentCatalog::import(&meanings)?;
    let fonts = ImportedDocumentFonts::import(&catalog)?;
    assert!(fonts.verify_source(&changed).is_err());
    let other_forms = fixture::forms(&changed, "font-freshness")?;
    let other_fields = ImportedDocumentFields::import(&other_forms)?;
    let other_meanings = ImportedDocumentFieldSemantics::import(&other_fields)?;
    let other_catalog = ImportedDocumentCatalog::import(&other_meanings)?;
    let other = ImportedDocumentFonts::import(&other_catalog)?;
    assert_eq!(other.definitions()[0].declared.face, "FONT-SOURCE-MARKER");
    assert_ne!(fonts.receipt(), other.receipt());
    fixture::verify_whole(&other_forms, &other_catalog, &other)?;
    assert!(!serde_json::to_string(other.receipt())?.contains("FONT-SOURCE-MARKER"));
    assert_eq!(
        format!("{:?}", other.definitions()[0]),
        "ImportedFontDefinition(<redacted>)"
    );
    Ok(())
}
fn rejects(bytes: &[u8]) -> bool {
    let Ok(forms) = fixture::forms(bytes, "font-reject") else {
        return true;
    };
    let Ok(fields) = ImportedDocumentFields::import(&forms) else {
        return true;
    };
    let Ok(meanings) = ImportedDocumentFieldSemantics::import(&fields) else {
        return true;
    };
    let Ok(catalog) = ImportedDocumentCatalog::import(&meanings) else {
        return true;
    };
    ImportedDocumentFonts::import(&catalog).is_err()
}
#[test]
fn original_reader_rejects_dangling_count_duplicate_and_wrong_language() -> TestResult {
    let bytes = &inputs::actual_corpus()?[0];
    for (tag, key, value) in [
        ("fontRef", "hangul", "4294967295"),
        ("fontface", "fontCnt", "0"),
        ("fontface", "lang", "USER"),
        ("font", "id", "4294967295"),
    ] {
        assert!(rejects(&mutation::change_attribute(
            bytes,
            "Contents/header.xml",
            tag,
            key,
            value
        )?));
    }
    let duplicate = mutation::mutate_part(bytes, "Contents/header.xml", |text| {
        let xml = PreservingXmlDocument::parse(text.as_bytes())?;
        let node = xml
            .elements()
            .iter()
            .find(|e| e.name().local_name() == "fontRef")
            .ok_or("fontRef missing")?;
        let span = node.outer_span().ok_or("fontRef complete span")?;
        let mut result = text.to_owned();
        result.insert_str(span.end(), &text[span.start()..span.end()]);
        Ok(result)
    })?;
    assert!(rejects(&duplicate));
    Ok(())
}
#[test]
fn unknown_font_attributes_survive_raw_source_but_original_typed_reader_rejects() -> TestResult {
    let bytes = &inputs::actual_corpus()?[0];
    let original_header = mutation::read_part(bytes, "Contents/header.xml")?;
    let changed = mutation::mutate_part(bytes, "Contents/header.xml", |text| {
        let xml = PreservingXmlDocument::parse(text.as_bytes())?;
        let node = xml
            .elements()
            .iter()
            .find(|e| e.name().local_name() == "font")
            .ok_or("font missing")?;
        let span = node.start_tag_span();
        let offset = text[span.start()..span.end()]
            .find(' ')
            .ok_or("font attributes")?;
        let mut result = text.to_owned();
        result.insert_str(span.start() + offset, " sourceOpaqueFlag=\"keep\"");
        Ok(result)
    })?;
    assert_ne!(
        mutation::read_part(&changed, "Contents/header.xml")?,
        original_header
    );
    let forms = fixture::forms(&changed, "font-opaque")?;
    forms.source().verify_source(&changed)?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    assert!(matches!(ImportedDocumentCatalog::import(&meanings),
        Err(hwpx_package::document_import::fields::semantics::catalog::CatalogImportError::Character { .. })));
    Ok(())
}
#[test]
fn declared_embedding_flag_is_preserved_without_resolving_or_loading_binary() -> TestResult {
    let bytes = &inputs::actual_corpus()?[0];
    let changed =
        mutation::change_attribute(bytes, "Contents/header.xml", "font", "isEmbedded", "1")?;
    let changed = mutation::mutate_part(&changed, "Contents/header.xml", |text| {
        let xml = PreservingXmlDocument::parse(text.as_bytes())?;
        let node = xml
            .elements()
            .iter()
            .find(|e| e.name().local_name() == "font")
            .ok_or("font missing")?;
        let offset = node.start_name_span().end();
        let mut result = text.to_owned();
        result.insert_str(offset, " binaryItemIDRef=\"DECLARED-BINARY-ONLY\"");
        Ok(result)
    })?;
    let forms = fixture::forms(&changed, "font-embedding-declaration")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let catalog = ImportedDocumentCatalog::import(&meanings)?;
    let fonts = ImportedDocumentFonts::import(&catalog)?;
    assert!(fonts.definitions()[0].declared.is_embedded);
    assert_eq!(
        fonts.definitions()[0]
            .declared
            .binary_item_id_ref
            .as_deref(),
        Some("DECLARED-BINARY-ONLY")
    );
    assert!(fonts.receipt().declarations_with_embedded_flag > 0);
    assert!(fonts.receipt().qualification.contains("not_availability"));
    fixture::verify_whole(&forms, &catalog, &fonts)?;
    assert_eq!(fonts.verify_source(&changed)?, *fonts.receipt());
    Ok(())
}
#[test]
fn missing_language_axis_and_foreign_font_namespace_remain_rejected() -> TestResult {
    let bytes = &inputs::actual_corpus()?[0];
    let missing = mutation::mutate_part(bytes, "Contents/header.xml", |text| {
        let xml = PreservingXmlDocument::parse(text.as_bytes())?;
        let node = xml
            .elements()
            .iter()
            .find(|e| e.name().local_name() == "fontRef")
            .ok_or("fontRef missing")?;
        let attribute = node
            .attributes()
            .iter()
            .find(|a| a.name().local_name() == "hangul")
            .ok_or("hangul axis")?;
        let span = attribute.span();
        let mut result = text.to_owned();
        result.replace_range(span.start()..span.end(), "");
        Ok(result)
    })?;
    assert!(rejects(&missing));
    let foreign = mutation::mutate_part(bytes, "Contents/header.xml", |text| {
        Ok(text.replace(
            "http://www.hancom.co.kr/hwpml/2011/head",
            "urn:untrusted-font-header",
        ))
    })?;
    assert!(rejects(&foreign));
    Ok(())
}
