//! Immutable historical note corpus, metadata-only source import evidence.
use domain_ir::DocumentId;
use hwpx_package::document_import::{
    ImportedSourcePackage, SourceImportLimits,
    fields::{ImportedDocumentFields, semantics::ImportedDocumentFieldSemantics},
    forms::ImportedDocumentForms,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use std::error::Error;
#[path = "../tests/support/document_import_note_fixture.rs"]
mod inputs;

#[derive(Serialize)]
struct Case {
    lane: &'static str,
    source_package_sha256: [u8; 32],
    original_form_graph_sha256: [u8; 32],
    final_field_semantic_graph_sha256: [u8; 32],
    notes: usize,
    footnotes: usize,
    endnotes: usize,
    fields: usize,
}
#[derive(Serialize)]
struct Evidence {
    profile: &'static str,
    packages: usize,
    note_observations: usize,
    footnotes: usize,
    endnotes: usize,
    generated_packages: usize,
    saved_packages: usize,
    reopened_packages: usize,
    cases: Vec<Case>,
    original_native_note_state: &'static str,
    native_activated: bool,
    numbering_render_or_product_qualified: bool,
    p09_complete: bool,
}
fn main() -> Result<(), Box<dyn Error>> {
    let mut evidence = Evidence {
        profile: "hwpx-agent.document-import-notes-probe/partial-v1",
        packages: 0,
        note_observations: 0,
        footnotes: 0,
        endnotes: 0,
        generated_packages: 0,
        saved_packages: 0,
        reopened_packages: 0,
        cases: vec![],
        original_native_note_state: "failed_semantic_non_green",
        native_activated: false,
        numbering_render_or_product_qualified: false,
        p09_complete: false,
    };
    for input in inputs::actual_inputs()? {
        let forms = ImportedDocumentForms::import(ImportedSourcePackage::import(
            &input.bytes,
            DocumentId::parse("actual-notes-probe")?,
            Sha256::digest(&input.bytes).into(),
            SourceImportLimits::default(),
        )?)?;
        if forms.notes().len() != input.expected_notes {
            return Err("actual note coverage drift".into());
        }
        for note in forms.notes() {
            if forms
                .source()
                .resolve_anchor(&note.source_anchor)?
                .element()
                .is_none()
                || forms
                    .source()
                    .resolve_anchor(&note.body_anchor)?
                    .element()
                    .is_none()
            {
                return Err("actual note anchors absent".into());
            }
        }
        let fields = ImportedDocumentFields::import(&forms)?;
        let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
        if forms.verify_source(&input.bytes)? != *forms.receipt()
            || meanings.verify_source(&input.bytes)? != *meanings.receipt()
        {
            return Err("whole fresh note graph drift".into());
        }
        let footnotes = forms
            .notes()
            .iter()
            .filter(|n| n.native_kind == "footNote")
            .count();
        let endnotes = forms
            .notes()
            .iter()
            .filter(|n| n.native_kind == "endNote")
            .count();
        if footnotes + endnotes != forms.notes().len() {
            return Err("actual unknown note kind".into());
        }
        evidence.packages += 1;
        evidence.note_observations += forms.notes().len();
        evidence.footnotes += footnotes;
        evidence.endnotes += endnotes;
        match input.lane {
            "generated" => evidence.generated_packages += 1,
            "saved" => evidence.saved_packages += 1,
            "reopened" => evidence.reopened_packages += 1,
            _ => return Err("unknown lane".into()),
        }
        evidence.cases.push(Case {
            lane: input.lane,
            source_package_sha256: forms.receipt().source_package_sha256,
            original_form_graph_sha256: forms.receipt().graph_sha256,
            final_field_semantic_graph_sha256: meanings.receipt().graph_sha256,
            notes: forms.notes().len(),
            footnotes,
            endnotes,
            fields: fields.fields().len(),
        });
    }
    println!("{}", serde_json::to_string_pretty(&evidence)?);
    Ok(())
}
