use domain_ir::{Inline, Node, PropertyValue};
use hwpx_package::document_import::{
    fields::{ImportedDocumentFields, semantics::ImportedDocumentFieldSemantics},
    structure::StructureImportError,
};
use std::error::Error;
#[path = "support/document_import_field_fixture.rs"]
mod base;
#[path = "support/document_import_bookmark_fixture.rs"]
mod fixture;
type TestResult = Result<(), Box<dyn Error>>;

#[test]
fn source_bookmark_point_counts_original_children_not_synthetic_anchors() -> TestResult {
    let body = format!(
        "<hp:t>before</hp:t>{}{}<hp:t>after</hp:t>{}",
        fixture::marker("first"), fixture::marker("second"), fixture::marker("third")
    );
    let bytes = base::package(&fixture::paragraph(&body))?;
    let forms = base::forms(&bytes, "source-point")?;
    let first = forms.observed_bookmark_by_name("first")?;
    let second = forms.observed_bookmark_by_name("second")?;
    let third = forms.observed_bookmark_by_name("third")?;
    assert_ne!(first.control_inline_position, second.control_inline_position);
    assert_eq!(first.source_point(), second.source_point());
    assert_eq!(first.source_point().run_ordinal(), 0);
    assert_eq!(first.source_point().non_bookmark_inline_ordinal(), 1);
    assert_eq!(third.source_point().non_bookmark_inline_ordinal(), 2);
    assert_eq!(forms.verify_source(&bytes)?, *forms.receipt());
    Ok(())
}

#[test]
fn source_bookmark_point_retains_actual_run_boundary_without_flattening() -> TestResult {
    let body = format!(
        "<hp:p id='1'><hp:run><hp:t>one</hp:t></hp:run><hp:run><hp:t>two</hp:t>{}</hp:run></hp:p>",
        fixture::marker("second-run")
    );
    let bytes = base::package(&body)?;
    let forms = base::forms(&bytes, "source-point")?;
    let point = forms.observed_bookmark_by_name("second-run")?.source_point();
    assert_eq!(point.run_ordinal(), 1);
    assert_eq!(point.non_bookmark_inline_ordinal(), 1);
    Ok(())
}

#[test]
fn source_bookmark_point_nested_table_note_uses_its_own_paragraph() -> TestResult {
    let nested = fixture::note(&fixture::table(&format!(
        "<hp:t>nested</hp:t>{}", fixture::marker("inside")
    )));
    let bytes = base::package(&fixture::paragraph(&format!("{}{nested}", fixture::marker("outside"))))?;
    let forms = base::forms(&bytes, "source-point")?;
    let outer = forms.observed_bookmark_by_name("outside")?;
    let inner = forms.observed_bookmark_by_name("inside")?;
    assert_ne!(outer.paragraph_id, inner.paragraph_id);
    assert_eq!(inner.source_point().run_ordinal(), 0);
    assert_eq!(inner.source_point().non_bookmark_inline_ordinal(), 1);
    assert_eq!(forms.verify_source(&bytes)?, *forms.receipt());
    Ok(())
}

#[test]
fn source_bookmark_point_does_not_change_observation_json_or_expose_debug_names() -> TestResult {
    let bytes = base::package(&fixture::paragraph(&fixture::marker("private-point")))?;
    let forms = base::forms(&bytes, "source-point")?;
    let bookmark = forms.observed_bookmark_by_name("private-point")?;
    let value = serde_json::to_value(bookmark)?;
    let keys: std::collections::BTreeSet<_> = value.as_object().ok_or("observation")?.keys().map(String::as_str).collect();
    assert_eq!(keys, std::collections::BTreeSet::from([
        "reference_id", "source_anchor", "wrapper_node_id", "paragraph_id", "name", "control_inline_position"
    ]));
    assert!(!format!("{:?}", bookmark.source_point()).contains("private-point"));
    Ok(())
}

#[test]
fn source_bookmark_anchor_retains_original_wrapper_and_resolves_actual_source() -> TestResult {
    let bytes = base::package(&fixture::paragraph(&fixture::marker("private bookmark")))?;
    let forms = base::forms(&bytes, "bookmark-test")?;
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
        let forms = base::forms(&bytes, "bookmark-test")?;
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
    let bytes = base::package(&fixture::paragraph(&format!(
        "{}{}",
        fixture::marker("same"),
        fixture::marker("same")
    )))?;
    let forms = base::forms(&bytes, "bookmark-test")?;
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
    let bytes = base::package(&fixture::paragraph(&fixture::marker("e&#x301;")))?;
    let forms = base::forms(&bytes, "bookmark-test")?;
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
        let bytes = base::package(&fixture::paragraph(&body))?;
        assert!(base::forms(&bytes, "bookmark-test").is_err());
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
    let forms = base::forms(&base::package(&default_body)?, "bookmark-test")?;
    assert_eq!(forms.bookmarks().len(), 1);
    let foreign = body.replace("hp:bookmark", "u:bookmark");
    let forms = base::forms(&base::package(&foreign)?, "bookmark-test")?;
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
        let bytes = base::package(&body)?;
        let forms = base::forms(&bytes, "bookmark-test")?;
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
    let bytes = base::package(&body)?;
    let forms = base::forms(&bytes, "bookmark-test")?;
    for changed in [
        body.replace("private bookmark", "other bookmark"),
        body.replace("private text", "other text"),
    ] {
        assert!(forms.verify_source(&base::package(&changed)?).is_err());
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
    let forms = base::forms(&base::captured()?, "bookmark-test")?;
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
    let forms = base::forms(&bytes, "bookmark-test")?;
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

#[test]
fn source_section_location_uses_xml_order_across_attached_tables_and_detached_notes() -> TestResult {
    let body = format!("{}{}", fixture::paragraph(&format!("{}{}{}",
        fixture::marker("outer"), fixture::table(&fixture::marker("table")),
        fixture::note(&format!("{}{}", fixture::marker("note"),
            fixture::table(&fixture::marker("note-table")))))),
        fixture::paragraph(&fixture::marker("tail")));
    let bytes = base::package(&body)?;
    let forms = base::forms(&bytes, "source-section-order")?;
    for (name, ordinal) in [("outer", 0), ("table", 1), ("note", 2), ("note-table", 3), ("tail", 4)] {
        let observed = forms.observed_bookmark_by_name(name)?;
        let location = observed.section_location();
        assert_eq!(location.section_id(), &forms.graph().sections()[0].section_id);
        assert_eq!(location.paragraph_ordinal(), ordinal);
        assert_eq!(location.source_paragraph_count(), 5);
        assert_eq!(observed.source_point().run_ordinal(), 0);
    }
    assert_eq!(forms.verify_source(&bytes)?, *forms.receipt());
    Ok(())
}

#[test]
fn source_section_location_counts_opaque_paragraphs_without_claiming_typed_coverage() -> TestResult {
    let opaque = "<u:future><hp:p id='9'><hp:run><hp:t>opaque paragraph</hp:t></hp:run></hp:p></u:future>";
    let body = format!("{}{}", fixture::paragraph(&format!("{}{opaque}", fixture::marker("first"))),
        fixture::paragraph(&fixture::marker("last")));
    let forms = base::forms(&base::package(&body)?, "source-opaque-order")?;
    assert_eq!(forms.body_structure().receipt().paragraphs, 2);
    let last = forms.observed_bookmark_by_name("last")?.section_location();
    assert_eq!(last.paragraph_ordinal(), 2);
    assert_eq!(last.source_paragraph_count(), 3);
    assert!(forms.graph().metadata().iter().any(|(key, _)| key == "scope"));
    Ok(())
}

#[test]
fn source_section_location_resets_per_spine_part_and_preserves_original_json() -> TestResult {
    let forms = base::forms(&fixture::two_sections()?, "source-section-reset")?;
    for (index, bookmark) in forms.bookmarks().iter().enumerate() {
        let location = bookmark.section_location();
        assert_eq!(location.section_id(), &forms.graph().sections()[index].section_id);
        assert_eq!(location.paragraph_ordinal(), 0);
        assert_eq!(location.source_paragraph_count(), 1);
        let value = serde_json::to_value(bookmark)?;
        assert_eq!(value.as_object().ok_or("observation")?.len(), 6);
        assert!(value.get("section_location").is_none());
        assert!(!format!("{location:?}").contains("same-across-sections"));
        assert!(!format!("{location:?}").contains(location.section_id().as_str()));
    }
    assert_ne!(forms.bookmarks()[0].section_location(), forms.bookmarks()[1].section_location());
    Ok(())
}

#[test]
fn source_section_location_cannot_rebind_after_a_new_paragraph_shifts_the_source() -> TestResult {
    let body = fixture::paragraph(&fixture::marker("point"));
    let bytes = base::package(&body)?;
    let forms = base::forms(&bytes, "source-order-drift")?;
    let changed = base::package(&format!("{}{body}", fixture::paragraph("<hp:t>new paragraph</hp:t>")))?;
    let shifted = base::forms(&changed, "source-order-drift")?;
    assert_eq!(forms.bookmarks()[0].section_location().paragraph_ordinal(), 0);
    assert_eq!(shifted.bookmarks()[0].section_location().paragraph_ordinal(), 1);
    assert_ne!(forms.bookmarks()[0].section_location(), shifted.bookmarks()[0].section_location());
    assert!(forms.verify_source(&changed).is_err());
    assert_eq!(forms.verify_source(&bytes)?, *forms.receipt());
    Ok(())
}

#[test]
fn source_section_topology_is_transparent_to_point_bookmarks_but_binds_exact_source() -> TestResult {
    let body = "<hp:p id='1'><hp:run><hp:t>private text</hp:t></hp:run><hp:run><hp:t>second</hp:t></hp:run></hp:p>";
    let plain = base::forms(&base::package(body)?, "source-topology")?;
    let marked_body = body.replacen("<hp:t>", &format!("{}<hp:t>", fixture::marker("private topology name")), 1);
    let marked_bytes = base::package(&marked_body)?;
    let marked = base::forms(&marked_bytes, "source-topology")?;
    let first = &plain.body_structure().section_flows()[0];
    let second = &marked.body_structure().section_flows()[0];
    assert_eq!((first.paragraphs(), first.runs(), first.inline_elements()), (1, 2, 2));
    assert_eq!(first.run_topology_sha256(), second.run_topology_sha256());
    assert_eq!(first.inline_topology_sha256(), second.inline_topology_sha256());
    assert_ne!(first, second);
    assert_eq!(marked.verify_source(&marked_bytes)?, *marked.receipt());
    let value = serde_json::to_value(second)?;
    assert!(value["page_assignment_sha256"].is_null());
    assert!(value["locked"].is_null());
    assert_eq!(value["complete_document_flow_qualified"], false);
    assert!(!value.to_string().contains("private"));
    assert!(!format!("{second:?}").contains(second.section_id().as_str()));
    Ok(())
}

#[test]
fn source_section_topology_distinguishes_run_boundaries_and_inline_kinds() -> TestResult {
    let a = base::forms(&base::package(&fixture::paragraph("<hp:t>a</hp:t>"))?, "topology-kinds")?;
    let b = base::forms(&base::package("<hp:p id='1'><hp:run/><hp:run><hp:t>a</hp:t></hp:run></hp:p>")?, "topology-kinds")?;
    let c = base::forms(&base::package(&fixture::paragraph("<u:future/>"))?, "topology-kinds")?;
    let a = &a.body_structure().section_flows()[0];
    let b = &b.body_structure().section_flows()[0];
    let c = &c.body_structure().section_flows()[0];
    assert_ne!(a.run_topology_sha256(), b.run_topology_sha256());
    assert_ne!(a.inline_topology_sha256(), b.inline_topology_sha256());
    assert_eq!(a.run_topology_sha256(), c.run_topology_sha256());
    assert_ne!(a.inline_topology_sha256(), c.inline_topology_sha256());
    Ok(())
}

#[test]
fn source_section_topology_uses_expanded_names_and_includes_opaque_paragraphs() -> TestResult {
    let body = fixture::paragraph("<hp:t>text</hp:t>");
    let alias = body.replace("hp:", "q:").replacen("<q:p ",
        "<q:p xmlns:q='http://www.hancom.co.kr/hwpml/2011/paragraph' ", 1);
    let a = base::forms(&base::package(&body)?, "topology-namespaces")?;
    let b = base::forms(&base::package(&alias)?, "topology-namespaces")?;
    assert_eq!(a.body_structure().section_flows()[0].run_topology_sha256(),
        b.body_structure().section_flows()[0].run_topology_sha256());
    assert_eq!(a.body_structure().section_flows()[0].inline_topology_sha256(),
        b.body_structure().section_flows()[0].inline_topology_sha256());
    let opaque = fixture::paragraph("<u:future><hp:p id='9'><hp:run><hp:t>opaque</hp:t></hp:run></hp:p></u:future>");
    let forms = base::forms(&base::package(&opaque)?, "topology-opaque")?;
    let flow = &forms.body_structure().section_flows()[0];
    assert_eq!((flow.paragraphs(), flow.runs(), flow.inline_elements()), (2, 2, 2));
    assert_eq!(forms.body_structure().receipt().paragraphs, 1);
    Ok(())
}

#[test]
fn source_section_topology_resets_spine_sections_and_counts_nested_body_runs() -> TestResult {
    let forms = base::forms(&fixture::two_sections()?, "topology-sections")?;
    let flows = forms.body_structure().section_flows();
    assert_eq!(flows.len(), 2);
    assert_ne!(flows[0].section_id(), flows[1].section_id());
    assert_eq!(flows[0].run_topology_sha256(), flows[1].run_topology_sha256());
    assert_eq!(flows[0].inline_topology_sha256(), flows[1].inline_topology_sha256());
    let body = fixture::paragraph(&fixture::note(&fixture::table("<hp:t>nested</hp:t>")));
    let bytes = base::package(&body)?;
    let forms = base::forms(&bytes, "topology-nested")?;
    let flow = &forms.body_structure().section_flows()[0];
    assert_eq!((flow.paragraphs(), flow.runs(), flow.inline_elements()), (3, 3, 3));
    assert_eq!(forms.verify_source(&bytes)?, *forms.receipt());
    Ok(())
}
