use domain_ir::{DocumentId, PropertyValue};
use hwpx_package::document_import::{
    ImportedSourcePackage, SourceImportLimits,
    fields::{
        ImportedDocumentFields,
        semantics::{
            ImportedDocumentFieldSemantics,
            catalog::{
                ImportedCatalogKind, ImportedDocumentCatalog, MemoCatalogBinding,
                assembly::ImportedDocumentAssembly,
            },
        },
    },
    forms::ImportedDocumentForms,
};
use sha2::{Digest as _, Sha256};
use std::error::Error;
#[path = "support/document_import_memo_catalog_fixture.rs"]
mod fixture;
#[path = "support/document_import_settings_inputs.rs"]
mod inputs;
type TestResult = Result<(), Box<dyn Error>>;
fn forms(bytes: &[u8]) -> Result<ImportedDocumentForms, Box<dyn Error>> {
    Ok(ImportedDocumentForms::import(
        ImportedSourcePackage::import(
            bytes,
            DocumentId::parse("memo-catalog")?,
            Sha256::digest(bytes).into(),
            SourceImportLimits::default(),
        )?,
    )?)
}
#[test]
fn exact_memo_definition_section_reference_and_review_use_are_in_original_catalog_and_assembly()
-> TestResult {
    let bytes = fixture::package(
        &fixture::table(&format!("{}{}", fixture::style(12), fixture::style(0)), 2),
        Some("12"),
    )?;
    let forms = forms(&bytes)?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let catalog = ImportedDocumentCatalog::import(&meanings)?;
    assert_eq!(catalog.receipt().memo_properties, 2);
    assert_eq!(catalog.receipt().explicit_memo_shape_uses, 1);
    assert_eq!(catalog.receipt().unresolved_memo_shape_uses, 0);
    assert_eq!(catalog.definitions().len(), catalog.graph().styles().len());
    let style = catalog
        .definitions()
        .iter()
        .find(|d| d.kind == ImportedCatalogKind::MemoProperty && d.native_id == 12)
        .ok_or("style")?;
    assert!(
        forms
            .source()
            .resolve_anchor(&style.source_anchor)?
            .element()
            .is_some()
    );
    assert_eq!(
        style
            .native_attributes
            .iter()
            .find(|(k, _)| *k == "x:opaque")
            .map(|(_, v)| v),
        Some(&PropertyValue::Text("PRIVATE-MEMO-STYLE".into()))
    );
    let usage = &catalog.memo_uses()[0];
    assert_eq!(usage.native_reference, Some(12));
    assert_eq!(
        usage.binding,
        MemoCatalogBinding::Resolved {
            catalog_id: style.catalog_id.clone()
        }
    );
    assert!(
        catalog.graph().sections()[0]
            .properties
            .iter()
            .any(|(k, v)| k == "source_memo_shape_catalog"
                && *v == PropertyValue::Id(style.catalog_id.clone()))
    );
    let assembly = ImportedDocumentAssembly::import(&catalog)?;
    assert_eq!(assembly.memo_catalog_uses(), catalog.memo_uses());
    let memo = assembly
        .review_bodies()
        .iter()
        .find(|b| {
            b.source.kind
                == hwpx_package::document_import::structure::review::ReviewBodyKind::MemoField
        })
        .ok_or("memo")?;
    assert_eq!(
        memo.memo_catalog_section_id.as_ref(),
        Some(&usage.section_id)
    );
    assert!(assembly.review_bodies().iter().filter(|b|b.source.kind==hwpx_package::document_import::structure::review::ReviewBodyKind::HiddenExplanation).all(|b|b.memo_catalog_section_id.is_none()));
    assert_eq!(catalog.verify_source(&bytes)?, *catalog.receipt());
    assert_eq!(assembly.verify_source(&bytes)?, *assembly.receipt());
    assert!(
        !format!("{catalog:?} {:?} {assembly:?}", catalog.memo_uses()).contains("PRIVATE-MEMO")
    );
    Ok(())
}
#[test]
fn missing_or_unresolved_reference_is_explicit_without_fabricated_default_style() -> TestResult {
    for reference in [None, Some("0"), Some("999")] {
        let bytes = fixture::package("", reference)?;
        let forms = forms(&bytes)?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
        let catalog = ImportedDocumentCatalog::import(&meanings)?;
        assert_eq!(catalog.receipt().memo_properties, 0);
        assert_eq!(
            catalog.memo_uses()[0].native_reference,
            reference.map(str::parse).transpose()?
        );
        assert_eq!(
            catalog.memo_uses()[0].binding,
            if reference.is_some() {
                MemoCatalogBinding::UnresolvedMissingDefinition
            } else {
                MemoCatalogBinding::NoExplicitReference
            }
        );
        assert!(
            !catalog.graph().sections()[0]
                .properties
                .iter()
                .any(|(k, _)| k == "source_memo_shape_catalog")
        );
        assert_eq!(catalog.verify_source(&bytes)?, *catalog.receipt());
    }
    Ok(())
}
#[test]
fn malformed_duplicate_count_and_unknown_native_tokens_fail_closed() -> TestResult {
    let style = fixture::style(12);
    let mut tables = vec![
        fixture::table(&style, 2),
        fixture::table(&format!("{style}{style}"), 2),
        format!("{}{}", fixture::table(&style, 1), fixture::table(&style, 1)),
        fixture::table(&style.replace("width='55'", "width='-1'"), 1),
        fixture::table(&style.replace("lineWidth='1'", "lineWidth='16'"), 1),
        fixture::table(&style.replace("lineWidth='1'", "lineWidth='0.12 mm'"), 1),
        fixture::table(&style.replace("memoType='NOMAL'", "memoType='NORMAL'"), 1),
        fixture::table(&style.replace("lineType='SOLID'", "lineType='UNKNOWN'"), 1),
        fixture::table(&style.replace("lineColor='#010203'", "lineColor='bad'"), 1),
        fixture::table(&style.replace("width='55'", ""), 1),
        fixture::table(&style.replace("/>", "><hh:unknown/></hh:memoPr>"), 1),
        fixture::table(&style.replace("/>", ">NOT-NATIVE-CHILD</hh:memoPr>"), 1),
    ];
    tables.push(fixture::table(
        &style.replace("id='12'", "id='4294967296'"),
        1,
    ));
    for table in tables {
        let bytes = fixture::package(&table, Some("12"))?;
        let forms = forms(&bytes)?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
        assert!(ImportedDocumentCatalog::import(&meanings).is_err());
    }
    let bytes = fixture::package(&fixture::table(&style, 1), Some("invalid"))?;
    let forms = forms(&bytes)?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    assert!(ImportedDocumentCatalog::import(&meanings).is_err());
    Ok(())
}
#[test]
fn every_original_native_memo_line_and_width_token_is_bounded_not_defaulted() -> TestResult {
    let style = fixture::style(12);
    let mut styles = Vec::new();
    for width in 0..16 {
        styles.push(style.replace("lineWidth='1'", &format!("lineWidth='{width}'")));
    }
    for line in [
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
    ] {
        styles.push(style.replace("lineType='SOLID'", &format!("lineType='{line}'")));
    }
    for memo in ["NOMAL", "USER_INSERT", "USER_DELETE", "USER_UPDATE"] {
        styles.push(style.replace("memoType='NOMAL'", &format!("memoType='{memo}'")));
    }
    for style in styles {
        let bytes = fixture::package(&fixture::table(&style, 1), Some("12"))?;
        let forms = forms(&bytes)?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
        let catalog = ImportedDocumentCatalog::import(&meanings)?;
        assert!(matches!(
            catalog.memo_uses()[0].binding,
            MemoCatalogBinding::Resolved { .. }
        ));
        assert_eq!(catalog.receipt().memo_properties, 1);
    }
    Ok(())
}
#[test]
fn source_style_or_section_reference_drift_invalidates_whole_cached_catalog_and_assembly()
-> TestResult {
    let style = fixture::style(12);
    let table = fixture::table(&style, 1);
    let bytes = fixture::package(&table, Some("12"))?;
    let forms = forms(&bytes)?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let catalog = ImportedDocumentCatalog::import(&meanings)?;
    let assembly = ImportedDocumentAssembly::import(&catalog)?;
    for changed in [
        fixture::package(&table.replace("width='55'", "width='60'"), Some("12"))?,
        fixture::package(&table, Some("999"))?,
    ] {
        assert!(catalog.verify_source(&changed).is_err());
        assert!(assembly.verify_source(&changed).is_err());
    }
    assert_eq!(assembly.verify_source(&bytes)?, *assembly.receipt());
    Ok(())
}
#[test]
fn all_locked_actual36_keep_missing_memo_definitions_explicit_and_previous_graph_results()
-> TestResult {
    let corpus = inputs::actual_corpus()?;
    assert_eq!(corpus.len(), 36);
    let mut refs = 0;
    for bytes in corpus {
        let forms = forms(&bytes)?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
        let catalog = ImportedDocumentCatalog::import(&meanings)?;
        assert_eq!(catalog.receipt().memo_properties, 0);
        refs += catalog.receipt().explicit_memo_shape_uses;
        assert_eq!(
            catalog.receipt().unresolved_memo_shape_uses,
            catalog.receipt().explicit_memo_shape_uses
        );
        assert!(
            catalog
                .memo_uses()
                .iter()
                .all(|v| !matches!(v.binding, MemoCatalogBinding::Resolved { .. }))
        );
        assert!(catalog.graph().sections().iter().all(|s| {
            !s.properties
                .iter()
                .any(|(k, _)| k == "source_memo_shape_catalog")
        }));
        assert_eq!(catalog.verify_source(&bytes)?, *catalog.receipt());
    }
    assert_eq!(refs, 44);
    Ok(())
}
