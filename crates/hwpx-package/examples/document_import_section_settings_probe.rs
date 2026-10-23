//! Fresh whole original section/page/columns consumer; no native execution.
use domain_ir::{DocumentGraph, DocumentGraphLimits, DocumentId, Properties};
use hwpx_package::document_import::{
    ImportedSourcePackage, SourceImportLimits,
    fields::{
        ImportedDocumentFields,
        semantics::{
            ImportedDocumentFieldSemantics,
            catalog::{
                ImportedDocumentCatalog,
                security::{
                    ImportedDocumentActiveSecurity,
                    settings::{ImportedDocumentSectionSettings, SectionSettingsImportReceipt},
                },
            },
        },
    },
    forms::ImportedDocumentForms,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use std::error::Error;
#[path = "../tests/support/document_import_settings_inputs.rs"]
mod inputs;

#[derive(Default, Serialize)]
struct Evidence {
    profile: &'static str,
    historical_inputs: usize,
    page_setups: usize,
    column_spans: usize,
    section_boundaries: usize,
    resolved_anchors: usize,
    whole_previous_graph_inverses: usize,
    receipts: Vec<SectionSettingsImportReceipt>,
}
fn without(properties: &Properties, keys: &[&str]) -> Properties {
    let mut result = Properties::new();
    for (key, value) in properties.iter().filter(|(key, _)| !keys.contains(key)) {
        result.insert(key, value.clone());
    }
    result
}
fn inverse(
    settings: &ImportedDocumentSectionSettings<'_, '_, '_, '_, '_>,
    security: &ImportedDocumentActiveSecurity<'_, '_, '_, '_>,
) -> Result<(), Box<dyn Error>> {
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
    if &DocumentGraph::from_draft(draft, DocumentGraphLimits::default())? != security.graph() {
        return Err("whole previous security graph inverse mismatch".into());
    }
    Ok(())
}
fn consume(bytes: &[u8], evidence: &mut Evidence) -> Result<(), Box<dyn Error>> {
    let source = ImportedSourcePackage::import(
        bytes,
        DocumentId::parse("section-settings-consumer")?,
        Sha256::digest(bytes).into(),
        SourceImportLimits::default(),
    )?;
    let forms = ImportedDocumentForms::import(source)?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let catalog = ImportedDocumentCatalog::import(&meanings)?;
    let security = ImportedDocumentActiveSecurity::import(&catalog)?;
    let settings = ImportedDocumentSectionSettings::import(&security)?;
    if settings.verify_source(bytes)? != *settings.receipt() {
        return Err("whole fresh settings receipt drift".into());
    }
    for section in settings.settings() {
        for anchor in [
            &section.source_anchor,
            &section.section_properties_anchor,
            &section.page_anchor,
        ] {
            forms.source().resolve_anchor(anchor)?;
            evidence.resolved_anchors += 1;
        }
        for column in &section.columns {
            if forms
                .source()
                .resolve_anchor(&column.source_anchor)?
                .element()
                .is_none()
            {
                return Err("column source element missing".into());
            }
            evidence.resolved_anchors += 1;
        }
    }
    inverse(&settings, &security)?;
    evidence.whole_previous_graph_inverses += 1;
    evidence.historical_inputs += 1;
    evidence.page_setups += settings.receipt().page_setups;
    evidence.column_spans += settings.receipt().column_spans;
    evidence.section_boundaries += settings.receipt().section_boundaries;
    evidence.receipts.push(settings.receipt().clone());
    Ok(())
}
fn main() -> Result<(), Box<dyn Error>> {
    let mut evidence = Evidence {
        profile: "hwpx-agent.document-import-section-settings-consumer/partial-v1",
        ..Evidence::default()
    };
    for bytes in inputs::actual_corpus()? {
        consume(&bytes, &mut evidence)?;
    }
    if evidence.historical_inputs != 36
        || evidence.page_setups != 44
        || evidence.column_spans != 44
        || evidence.section_boundaries != 8
        || evidence.resolved_anchors != 176
        || evidence.whole_previous_graph_inverses != 36
    {
        return Err("original consumer settings coverage drift".into());
    }
    println!("{}", serde_json::to_string(&evidence)?);
    Ok(())
}
