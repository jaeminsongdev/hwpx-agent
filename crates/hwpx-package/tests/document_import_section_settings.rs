use domain_ir::{DocumentGraph, DocumentGraphLimits, DocumentId, Properties};
use hwpx_package::{
    PageSetupLimits, PageSetupReader, SectionColumnLimits, SectionColumnReader,
    document_import::{
        ImportedSourcePackage, SourceImportLimits,
        fields::{
            ImportedDocumentFields,
            semantics::{
                ImportedDocumentFieldSemantics,
                catalog::{
                    ImportedDocumentCatalog,
                    security::{
                        ImportedDocumentActiveSecurity,
                        settings::{ImportedDocumentSectionSettings, SectionSettingsImportError},
                    },
                },
            },
        },
        forms::ImportedDocumentForms,
    },
};
use sha2::{Digest as _, Sha256};
use std::error::Error;
#[path = "support/document_import_catalog_fixture.rs"]
mod fixture;
#[path = "support/document_import_settings_inputs.rs"]
mod inputs;
type TestResult = Result<(), Box<dyn Error>>;
fn forms(bytes: &[u8]) -> Result<ImportedDocumentForms, Box<dyn Error>> {
    Ok(ImportedDocumentForms::import(
        ImportedSourcePackage::import(
            bytes,
            DocumentId::parse("section-settings-source")?,
            Sha256::digest(bytes).into(),
            SourceImportLimits::default(),
        )?,
    )?)
}
fn without(values: &Properties, keys: &[&str]) -> Properties {
    let mut result = Properties::new();
    for (key, value) in values.iter().filter(|(k, _)| !keys.contains(k)) {
        result.insert(key, value.clone());
    }
    result
}
fn check(bytes: &[u8]) -> Result<(usize, usize, usize), Box<dyn Error>> {
    let forms = forms(bytes)?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let catalog = ImportedDocumentCatalog::import(&meanings)?;
    let security = ImportedDocumentActiveSecurity::import(&catalog)?;
    let settings = ImportedDocumentSectionSettings::import(&security)?;
    assert_eq!(settings.verify_source(bytes)?, *settings.receipt());
    assert_eq!(settings.settings().len(), settings.graph().sections().len());
    for row in settings.settings() {
        let part = forms.source().resolve_anchor(&row.source_anchor)?.part();
        let original = fixture::read_part(bytes, part.path().as_str())?;
        let page = PageSetupReader::read(&original, PageSetupLimits::default())?;
        assert_eq!(row.page, page);
        assert_eq!(row.metrics, page.metrics(PageSetupLimits::default())?);
        let columns = SectionColumnReader::read_section(
            &original,
            row.metrics.body_width,
            SectionColumnLimits::default(),
        )?;
        assert_eq!(columns.spans.len(), row.columns.len());
        for (binding, original) in row.columns.iter().zip(columns.spans) {
            assert_eq!(binding.definition, original);
            assert_eq!(
                binding.metrics,
                original.metrics(row.metrics.body_width, SectionColumnLimits::default())?
            );
            assert!(
                forms
                    .source()
                    .resolve_anchor(&binding.source_anchor)?
                    .element()
                    .is_some()
            );
        }
        assert!(
            forms
                .source()
                .resolve_anchor(&row.page_anchor)?
                .element()
                .is_some()
        );
        assert!(
            forms
                .source()
                .resolve_anchor(&row.section_properties_anchor)?
                .element()
                .is_some()
        );
    }
    let mut draft = settings.graph().clone().into_draft();
    draft.metadata = without(
        &draft.metadata,
        &[
            "section_settings_import_profile",
            "section_settings_import_scope",
        ],
    );
    draft.settings = without(
        &draft.settings,
        &["source_header_section_count", "source_section_order"],
    );
    for section in &mut draft.sections {
        section.properties = without(
            &section.properties,
            &[
                "source_page_setup",
                "source_column_spans",
                "source_page_body_width",
                "source_page_body_height",
            ],
        );
    }
    assert_eq!(
        &DocumentGraph::from_draft(draft, DocumentGraphLimits::default())?,
        security.graph()
    );
    assert_eq!(
        format!("{:?}", settings.settings()[0]),
        "ImportedSectionSettings(<redacted>)"
    );
    Ok((
        settings.receipt().sections,
        settings.receipt().column_spans,
        settings.receipt().section_boundaries,
    ))
}
fn rejection(bytes: &[u8]) -> TestResult {
    let forms = forms(bytes)?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let catalog = ImportedDocumentCatalog::import(&meanings)?;
    let security = ImportedDocumentActiveSecurity::import(&catalog)?;
    assert!(matches!(
        ImportedDocumentSectionSettings::import(&security),
        Err(SectionSettingsImportError::Page(_) | SectionSettingsImportError::Columns(_))
    ));
    Ok(())
}
#[test]
fn actual36_original_readers_source_binding_spine_order_and_whole_security_graph_inverse()
-> TestResult {
    let mut sections = 0;
    let mut columns = 0;
    let mut boundaries = 0;
    for bytes in inputs::actual_corpus()? {
        let c = check(&bytes)?;
        sections += c.0;
        columns += c.1;
        boundaries += c.2;
    }
    assert_eq!((sections, columns, boundaries), (44, 44, 8));
    Ok(())
}
#[test]
fn original26_corpus_is_byte_exact_prefix_of_frozen36_without_input_substitution() -> TestResult {
    let legacy = fixture::actual_corpus()?;
    let current = inputs::actual_corpus()?;
    assert_eq!(legacy.as_slice(), &current[..26]);
    Ok(())
}
#[test]
fn original_page_bad_width_margin_and_header_section_count_are_rejected() -> TestResult {
    let bytes = &inputs::actual_corpus()?[25];
    for (path, tag, key, value) in [
        ("Contents/section0.xml", "pagePr", "width", "0"),
        ("Contents/section0.xml", "margin", "left", "999999"),
        ("Contents/header.xml", "head", "secCnt", "99"),
        ("Contents/section0.xml", "colPr", "sameGap", "999999"),
    ] {
        rejection(&fixture::change_attribute(bytes, path, tag, key, value)?)?;
    }
    Ok(())
}
#[test]
fn missing_page_setup_is_not_defaulted_and_duplicate_page_is_not_selected_first() -> TestResult {
    let bytes = &inputs::actual_corpus()?[25];
    for duplicate in [false, true] {
        let bytes = fixture::mutate_part(bytes, "Contents/section0.xml", |text| {
            let xml = hwpx_package::PreservingXmlDocument::parse(text.as_bytes())?;
            let page = xml
                .elements()
                .iter()
                .find(|e| e.name().local_name() == "pagePr")
                .ok_or("page missing")?;
            let span = page.outer_span().ok_or("page span")?;
            let mut changed = text.to_owned();
            if duplicate {
                changed.insert_str(span.end(), &text[span.start()..span.end()]);
            } else {
                changed.replace_range(span.start()..span.end(), "");
            }
            Ok(changed)
        })?;
        rejection(&bytes)?;
    }
    Ok(())
}
#[test]
fn fresh_raw_package_drift_denied_without_changing_original_security_state() -> TestResult {
    let bytes = inputs::actual_corpus()?.remove(25);
    let forms = forms(&bytes)?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let catalog = ImportedDocumentCatalog::import(&meanings)?;
    let security = ImportedDocumentActiveSecurity::import(&catalog)?;
    let settings = ImportedDocumentSectionSettings::import(&security)?;
    let mut drift = bytes;
    drift[0] ^= 1;
    assert!(settings.verify_source(&drift).is_err());
    let before = security.graph().clone().into_draft();
    let after = settings.graph().clone().into_draft();
    assert_eq!(before.security_state, after.security_state);
    Ok(())
}
