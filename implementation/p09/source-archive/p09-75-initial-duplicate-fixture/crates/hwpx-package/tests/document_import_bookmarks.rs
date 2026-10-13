use domain_ir::{Inline, Node, PropertyValue};
use hwpx_package::document_import::{
    fields::{ImportedDocumentFields, semantics::ImportedDocumentFieldSemantics},
    structure::StructureImportError,
};
use std::error::Error;
#[path = "support/document_import_bookmark_fixture.rs"]
mod fixture;
type TestResult = Result<(), Box<dyn Error>>;

#[test]
fn source_bookmark_anchor_retains_original_wrapper_and_resolves_actual_source() -> TestResult {
    let bytes = fixture::base::package(&fixture::paragraph(&fixture::marker("private bookmark")))?;
    let forms = fixture::base::forms(&bytes, "bookmark-test")?;
    let observed = forms.observed_bookmark_by_name("private bookmark")?;
    let marker = forms
        .source()
        .resolve_anchor(&observed.source_anchor)?
        .element()
        .ok_or("marker")?;
    assert_eq!(marker.name().local_name(), "bookmark");
    let draft = forms.graph().clone().into_draft();
    let Node::Paragraph(paragraph) = &draft.sections[0].body.children[0] else {
        return Err("paragraph".into());
    };
    assert!(
        matches!(&paragraph.inlines[observed.control_inline_position],Inline::ControlRef{node_id} if node_id==&observed.wrapper_node_id)
    );
    assert!(
        matches!(&paragraph.inlines[observed.control_inline_position+1],Inline::BookmarkAnchor{reference_id} if reference_id==&observed.reference_id)
    );
    let reference = draft
        .references
        .iter()
        .find(|r| r.reference_id == observed.reference_id)
        .ok_or("reference")?;
    assert_eq!(
        reference.target_node_id.as_ref(),
        Some(&observed.wrapper_node_id)
    );
    let wrapper = draft.sections[0]
        .body
        .children
        .iter()
        .find(|n| n.common().node_id == observed.wrapper_node_id)
        .ok_or("wrapper")?;
    let Node::EmbeddedObject(object) = wrapper else {
        return Err("wrapper type changed".into());
    };
    assert_eq!(object.object_type, domain_ir::EmbeddedObjectType::Xml);
    assert!(
        object
            .properties
            .iter()
            .any(|(k, v)| k == "source_local_name"
                && matches!(v,PropertyValue::Text(value) if value=="ctrl"))
    );
    assert_eq!(forms.verify_source(&bytes)?, *forms.receipt());
    Ok(())
}

#[test]
fn generated_whole_package_bookmarks_mix_with_fields_and_notes_without_field_count_confusion()
-> TestResult {
    let mut markers = 0;
    for bytes in fixture::generated()? {
        let forms = fixture::base::forms(&bytes, "bookmark-test")?;
        markers += forms.bookmarks().len();
        let fields = ImportedDocumentFields::import(&forms)?;
        let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
        assert_eq!(
            meanings.graph().clone().into_draft().references.len(),
            fields.fields().len() + forms.bookmarks().len()
        );
        assert_eq!(meanings.verify_source(&bytes)?, *meanings.receipt());
        assert_eq!(
            meanings.receipt().unsupported_meanings,
            fields.fields().len()
        );
    }
    assert_eq!(markers, 10);
    Ok(())
}

#[test]
fn duplicate_names_have_distinct_source_anchors_and_selection_never_picks_first() -> TestResult {
    let bytes = fixture::base::package(&fixture::paragraph(&format!(
        "{}{}",
        fixture::marker("same"),
        fixture::marker("same")
    )))?;
    let forms = fixture::base::forms(&bytes, "bookmark-test")?;
    assert_eq!(forms.bookmarks().len(), 2);
    assert_ne!(
        forms.bookmarks()[0].reference_id,
        forms.bookmarks()[1].reference_id
    );
    assert!(forms.observed_bookmark_by_name("same").is_err());
    assert!(forms.observed_bookmark_by_name("absent").is_err());
    assert_eq!(forms.verify_source(&bytes)?, *forms.receipt());
    Ok(())
}

#[test]
fn raw_source_name_is_not_normalized_or_a_native_name_lookup_claim() -> TestResult {
    let bytes = fixture::base::package(&fixture::paragraph(&fixture::marker("e&#x301;")))?;
    let forms = fixture::base::forms(&bytes, "bookmark-test")?;
    assert_eq!(forms.bookmarks()[0].name, "e\u{301}");
    assert!(forms.observed_bookmark_by_name("é").is_err());
    assert_eq!(
        forms.observed_bookmark_by_name("e\u{301}")?,
        &forms.bookmarks()[0]
    );
    Ok(())
}

#[test]
fn malformed_and_hidden_source_markers_reject_using_original_point_parser() -> TestResult {
    let good = fixture::marker("point");
    for body in [
        good.replace("name='point'", "name=''"),
        good.replace("name='point'", "name='point' unexpected='1'"),
        good.replace("<hp:ctrl>", "<hp:ctrl id='1'>"),
        good.replace(
            "<hp:bookmark name='point'/>",
            "<hp:bookmark name='point'></hp:bookmark>",
        ),
        good.replace("name='point'", "name='&#x1;'"),
        format!("<u:hidden>{good}</u:hidden>"),
        format!("<hp:ctrl>{good}</hp:ctrl>"),
        good.replace("name='point'", &format!("name='{}'", "A".repeat(65537))),
    ] {
        let bytes = fixture::base::package(&fixture::paragraph(&body))?;
        assert!(fixture::base::forms(&bytes, "bookmark-test").is_err());
    }
    Ok(())
}

#[test]
fn default_paragraph_namespace_is_supported_and_foreign_bookmark_is_not_promoted() -> TestResult {
    let body = fixture::paragraph(&fixture::marker("point"));
    let default_body = body.replace("<hp:", "<").replace("</hp:", "</").replacen(
        "<p id=",
        "<p xmlns='http://www.hancom.co.kr/hwpml/2011/paragraph' id=",
        1,
    );
    let forms = fixture::base::forms(&fixture::base::package(&default_body)?, "bookmark-test")?;
    assert_eq!(forms.bookmarks().len(), 1);
    let foreign = body.replace("hp:bookmark", "u:bookmark");
    let forms = fixture::base::forms(&fixture::base::package(&foreign)?, "bookmark-test")?;
    assert!(forms.bookmarks().is_empty());
    assert!(forms.graph().clone().into_draft().references.is_empty());
    Ok(())
}

#[test]
fn table_cell_and_note_table_bookmarks_resolve_source_target_nodes() -> TestResult {
    for body in [
        fixture::paragraph(&fixture::table(&fixture::marker("point"))),
        fixture::paragraph(&fixture::note(&fixture::table(&fixture::marker("point")))),
    ] {
        let bytes = fixture::base::package(&body)?;
        let forms = fixture::base::forms(&bytes, "bookmark-test")?;
        assert_eq!(forms.bookmarks().len(), 1);
        let fields = ImportedDocumentFields::import(&forms)?;
        let meaning = ImportedDocumentFieldSemantics::import(&fields)?;
        assert_eq!(meaning.verify_source(&bytes)?, *meaning.receipt());
        assert!(forms.observed_bookmark_by_name("point").is_ok());
    }
    Ok(())
}

#[test]
fn fresh_name_body_drift_and_debug_receipt_privacy_keep_source_binding() -> TestResult {
    let body = fixture::paragraph(&format!(
        "{}<hp:t>private text</hp:t>",
        fixture::marker("private bookmark")
    ));
    let bytes = fixture::base::package(&body)?;
    let forms = fixture::base::forms(&bytes, "bookmark-test")?;
    for changed in [
        body.replace("private bookmark", "other bookmark"),
        body.replace("private text", "other text"),
    ] {
        assert!(
            forms
                .verify_source(&fixture::base::package(&changed)?)
                .is_err()
        );
    }
    let output = format!(
        "{:?} {} {}",
        forms.bookmarks(),
        serde_json::to_string(forms.receipt())?,
        StructureImportError::BookmarkSelection
    );
    assert!(!output.contains("private bookmark"));
    assert!(!output.contains("private text"));
    Ok(())
}

#[test]
fn existing_native_captured_hyperlink_gets_no_fabricated_bookmarks_or_new_markers() -> TestResult {
    let forms = fixture::base::forms(&fixture::base::captured()?, "bookmark-test")?;
    assert!(forms.bookmarks().is_empty());
    assert!(
        !forms
            .graph()
            .clone()
            .into_draft()
            .metadata
            .iter()
            .any(|(k, _)| k.starts_with("bookmark_import_"))
    );
    let fields = ImportedDocumentFields::import(&forms)?;
    assert_eq!(
        ImportedDocumentFieldSemantics::import(&fields)?
            .receipt()
            .https_targets,
        1
    );
    Ok(())
}

#[test]
fn same_source_bytes_in_two_spine_parts_keep_distinct_point_and_wrapper_identity() -> TestResult {
    let bytes = fixture::two_sections()?;
    let forms = fixture::base::forms(&bytes, "bookmark-test")?;
    assert_eq!(forms.graph().sections().len(), 2);
    assert_eq!(forms.bookmarks().len(), 2);
    assert_ne!(
        forms.bookmarks()[0].source_anchor,
        forms.bookmarks()[1].source_anchor
    );
    assert_ne!(
        forms.bookmarks()[0].reference_id,
        forms.bookmarks()[1].reference_id
    );
    assert_ne!(
        forms.bookmarks()[0].wrapper_node_id,
        forms.bookmarks()[1].wrapper_node_id
    );
    assert!(
        forms
            .observed_bookmark_by_name("same-across-sections")
            .is_err()
    );
    assert_eq!(forms.verify_source(&bytes)?, *forms.receipt());
    Ok(())
}
