//! Generated-package point-anchor probe. No positive actual native bookmarks.
use hwpx_package::document_import::fields::{
    ImportedDocumentFields, semantics::ImportedDocumentFieldSemantics,
};
use serde::Serialize;
use std::error::Error;
#[path = "../tests/support/document_import_field_fixture.rs"]
mod base;
#[path = "../tests/support/document_import_bookmark_fixture.rs"]
mod fixture;

#[derive(Serialize)]
struct Case {
    source_package_sha256: [u8; 32],
    source_anchor_graph_sha256: [u8; 32],
    final_graph_sha256: [u8; 32],
    sections: usize,
    notes: usize,
    bookmarks: usize,
    fields: usize,
}
#[derive(Serialize)]
struct Evidence {
    scope: &'static str,
    generated_packages: usize,
    generated_bookmarks: usize,
    cases: Vec<Case>,
    actual_captured_negative_packages: usize,
    actual_captured_bookmarks: usize,
    native_bookmark_name_or_internal_link_resolution_qualified: bool,
    native_activated: bool,
    p09_complete: bool,
}
fn main() -> Result<(), Box<dyn Error>> {
    let mut evidence = Evidence {
        scope: "generated_whole_source_point_anchor_not_positive_native_bookmark_or_internal_link_evidence",
        generated_packages: 0,
        generated_bookmarks: 0,
        cases: vec![],
        actual_captured_negative_packages: 0,
        actual_captured_bookmarks: 0,
        native_bookmark_name_or_internal_link_resolution_qualified: false,
        native_activated: false,
        p09_complete: false,
    };
    for bytes in fixture::generated()? {
        let forms = base::forms(&bytes, "generated-bookmarks-probe")?;
        let draft = forms.graph().clone().into_draft();
        for bookmark in forms.bookmarks() {
            if forms
                .source()
                .resolve_anchor(&bookmark.source_anchor)?
                .element()
                .is_none()
                || !draft.references.iter().any(|r| {
                    r.reference_id == bookmark.reference_id
                        && r.target_node_id.as_ref() == Some(&bookmark.wrapper_node_id)
                })
            {
                return Err("generated bookmark source/reference drift".into());
            }
        }
        let fields = ImportedDocumentFields::import(&forms)?;
        let meaning = ImportedDocumentFieldSemantics::import(&fields)?;
        if forms.verify_source(&bytes)? != *forms.receipt()
            || meaning.verify_source(&bytes)? != *meaning.receipt()
        {
            return Err("whole generated graph drift".into());
        }
        evidence.generated_packages += 1;
        evidence.generated_bookmarks += forms.bookmarks().len();
        evidence.cases.push(Case {
            source_package_sha256: forms.receipt().source_package_sha256,
            source_anchor_graph_sha256: forms.receipt().graph_sha256,
            final_graph_sha256: meaning.receipt().graph_sha256,
            sections: draft.sections.len(),
            notes: forms.notes().len(),
            bookmarks: forms.bookmarks().len(),
            fields: fields.fields().len(),
        });
    }
    let captured = base::captured()?;
    let forms = base::forms(&captured, "generated-bookmarks-probe")?;
    if !forms.bookmarks().is_empty() || forms.verify_source(&captured)? != *forms.receipt() {
        return Err("negative captured bookmark evidence drift".into());
    }
    evidence.actual_captured_negative_packages = 1;
    evidence.actual_captured_bookmarks = forms.bookmarks().len();
    println!("{}", serde_json::to_string_pretty(&evidence)?);
    Ok(())
}
