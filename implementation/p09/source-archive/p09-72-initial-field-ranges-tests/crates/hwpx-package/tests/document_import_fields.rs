use domain_ir::{DocumentGraph, DocumentGraphLimits, Flow, Inline, Node, Properties};
use hwpx_package::document_import::fields::{FieldRangeImportError, ImportedDocumentFields};
use std::error::Error;
#[path = "support/document_import_field_fixture.rs"]
mod fixture;
type TestResult = Result<(), Box<dyn Error>>;

fn paragraph(body: &str) -> String {
    format!("<hp:p id='1'><hp:run>{body}</hp:run></hp:p>")
}
fn begin(id: u32, kind: &str) -> String {
    format!("<hp:ctrl><hp:fieldBegin id='{id}' type='{kind}'/></hp:ctrl>")
}
fn end(id: u32) -> String {
    format!("<hp:ctrl><hp:fieldEnd beginIDRef='{id}'/></hp:ctrl>")
}
fn node<'a>(flow: &'a Flow, id: &domain_ir::LogicalId) -> Result<&'a Node, Box<dyn Error>> {
    flow.children
        .iter()
        .find(|n| &n.common().node_id == id)
        .ok_or_else(|| "missing source node".into())
}
#[test]
fn nested_ranges_across_runs_keep_order_and_every_original_non_field_value() -> TestResult {
    let body = format!(
        "<hp:p id='1'><hp:run>{}<hp:t>A</hp:t></hp:run><hp:run>{}<hp:t>B</hp:t>{}<hp:t>C</hp:t>{}</hp:run></hp:p>",
        begin(1, "FORMULA"),
        begin(2, "BOOKMARK"),
        end(2),
        end(1)
    );
    let bytes = fixture::package(&body)?;
    let original = fixture::forms(&bytes, "field-test")?;
    let imported = ImportedDocumentFields::import(&original)?;
    assert_eq!(
        (
            imported.receipt().field_ranges,
            imported.receipt().nested_ranges
        ),
        (2, 1)
    );
    let outer = &imported.fields()[0];
    let inner = &imported.fields()[1];
    assert_eq!(
        inner.parent_reference_id.as_ref(),
        Some(&outer.reference_id)
    );
    assert!(outer.inline_start < inner.inline_start && inner.inline_end < outer.inline_end);
    let flow = &imported.graph().sections()[0].body;
    let Node::Paragraph(p) = &flow.children[0] else {
        return Err("paragraph".into());
    };
    let Node::Paragraph(before) = &original.graph().sections()[0].body.children[0] else {
        return Err("paragraph".into());
    };
    assert_eq!(p, before);
    assert!(
        p.inlines
            .iter()
            .any(|v| matches!(v,Inline::Text{text} if text=="B"))
    );
    let mut restored = imported.graph().clone().into_draft();
    for item in &mut restored.sections[0].body.children {
        if matches!(item, Node::Field(_)) {
            *item = node(&original.graph().sections()[0].body, &item.common().node_id)?.clone();
        }
    }
    restored.references = original.graph().clone().into_draft().references;
    let mut metadata = Properties::new();
    for (key, value) in restored.metadata.iter() {
        if !key.starts_with("field_range_import_") {
            metadata.insert(key, value.clone());
        }
    }
    restored.metadata = metadata;
    assert_eq!(
        DocumentGraph::from_draft(restored, DocumentGraphLimits::default())?,
        *original.graph()
    );
    assert_eq!(imported.verify_source(&bytes)?, *imported.receipt());
    Ok(())
}
#[test]
fn all_original_field_kinds_are_observed_without_default_or_destination_invention() -> TestResult {
    for kind in [
        "CLICK_HERE",
        "HYPERLINK",
        "BOOKMARK",
        "FORMULA",
        "SUMMERY",
        "USER_INFO",
        "DATE",
        "DOC_DATE",
        "PATH",
        "CROSSREF",
        "MAILMERGE",
        "MEMO",
        "PROOFREADING_MARKS",
        "PRIVATE_INFO",
        "METATAG",
    ] {
        let bytes = fixture::package(&paragraph(&format!(
            "{}<hp:t>cached</hp:t>{}",
            begin(1, kind),
            end(1)
        )))?;
        let source = fixture::forms(&bytes, "field-test")?;
        let imported = ImportedDocumentFields::import(&source)?;
        assert_eq!(imported.fields()[0].native_kind, kind);
        let draft = imported.graph().clone().into_draft();
        assert!(draft.references.iter().all(|v| v.target_node_id.is_none()));
        assert!(
            !imported.fields()[0]
                .native_header_attributes
                .iter()
                .any(|(k, _)| k == "editable" || k == "dirty")
        );
        assert_eq!(imported.verify_source(&bytes)?, *imported.receipt());
    }
    Ok(())
}
#[test]
fn equal_native_ids_in_different_paragraphs_do_not_create_identity_collisions() -> TestResult {
    let p = paragraph(&format!("{}<hp:t>A</hp:t>{}", begin(1, "DATE"), end(1)));
    let bytes = fixture::package(&format!("{p}{p}"))?;
    let source = fixture::forms(&bytes, "field-test")?;
    let fields = ImportedDocumentFields::import(&source)?;
    assert_eq!(fields.fields().len(), 2);
    assert_eq!(
        fields.fields()[0].native_begin_id,
        fields.fields()[1].native_begin_id
    );
    assert_ne!(
        fields.fields()[0].reference_id,
        fields.fields()[1].reference_id
    );
    assert_ne!(
        fields.fields()[0].begin_anchor,
        fields.fields()[1].begin_anchor
    );
    Ok(())
}
#[test]
fn parameter_tree_anchor_is_exact_uninterpreted_and_does_not_evaluate_cached_text() -> TestResult {
    let begin = "<hp:ctrl><hp:fieldBegin id='1' type='FORMULA' editable='0' dirty='1'><hp:parameters cnt='1'><hp:stringParam name='Command'>SECRET_FORMULA</hp:stringParam></hp:parameters></hp:fieldBegin></hp:ctrl>";
    let bytes = fixture::package(&paragraph(&format!("{begin}<hp:t>cached</hp:t>{}", end(1))))?;
    let source = fixture::forms(&bytes, "field-test")?;
    let fields = ImportedDocumentFields::import(&source)?;
    assert_eq!(fields.receipt().parameterized_ranges, 1);
    let anchor = fields.fields()[0]
        .parameter_anchor
        .as_ref()
        .ok_or("parameters")?;
    assert_eq!(
        source
            .source()
            .resolve_anchor(anchor)?
            .element()
            .ok_or("parameters")?
            .name()
            .local_name(),
        "parameters"
    );
    assert!(!format!("{fields:?}").contains("SECRET_FORMULA"));
    assert!(!format!("{:?}", fields.fields()[0]).contains("SECRET_FORMULA"));
    let receipt = serde_json::to_string(fields.receipt())?;
    assert!(!receipt.contains("SECRET_FORMULA") && !receipt.contains("cached"));
    assert_eq!(fields.verify_source(&bytes)?, *fields.receipt());
    Ok(())
}
#[test]
fn malformed_headers_pairing_and_parameter_envelopes_keep_original_rejections() -> TestResult {
    let b = begin(1, "FORMULA");
    let e = end(1);
    for body in [
        format!("{b}<hp:t>A</hp:t>"),
        format!("{b}{}", end(2)),
        format!(
            "{}{}{}{}",
            begin(1, "DATE"),
            begin(2, "PATH"),
            end(1),
            end(2)
        ),
        format!("{}<hp:t>A</hp:t>{e}", b.replace("id='1'", "id='invalid'")),
        format!("{}<hp:t>A</hp:t>{e}", b.replace("FORMULA", "UNKNOWN")),
        format!(
            "<hp:ctrl><hp:fieldBegin id='1' type='FORMULA'><hp:parameters cnt='2'/></hp:fieldBegin></hp:ctrl>{e}"
        ),
    ] {
        let bytes = fixture::package(&paragraph(&body))?;
        assert!(fixture::forms(&bytes, "field-test").is_err());
    }
    Ok(())
}
#[test]
fn fields_hidden_in_unmapped_objects_are_not_successfully_omitted() -> TestResult {
    let bytes = fixture::package(&paragraph(&format!(
        "<u:future>{}{}</u:future>",
        begin(1, "DATE"),
        end(1)
    )))?;
    let source = fixture::forms(&bytes, "field-test")?;
    assert!(matches!(
        ImportedDocumentFields::import(&source),
        Err(FieldRangeImportError::Unrepresented)
    ));
    Ok(())
}
#[test]
fn attributed_control_wrapper_cannot_bypass_header_and_pair_validation() -> TestResult {
    let b = begin(1, "DATE").replace("<hp:ctrl>", "<hp:ctrl unknown='1'>");
    let bytes = fixture::package(&paragraph(&format!("{b}{}", end(1))))?;
    let source = fixture::forms(&bytes, "field-test")?;
    assert!(matches!(
        ImportedDocumentFields::import(&source),
        Err(FieldRangeImportError::Binding)
    ));
    Ok(())
}
#[test]
fn fresh_source_change_and_forged_anchor_are_rejected() -> TestResult {
    let body = paragraph(&format!("{}<hp:t>A</hp:t>{}", begin(1, "DATE"), end(1)));
    let bytes = fixture::package(&body)?;
    let source = fixture::forms(&bytes, "field-test")?;
    let fields = ImportedDocumentFields::import(&source)?;
    let changed = fixture::package(&body.replace(">A<", ">B<"))?;
    assert!(fields.verify_source(&changed).is_err());
    let mut anchor = fields.fields()[0].begin_anchor.clone();
    anchor.fingerprint_sha256[0] ^= 1;
    assert!(source.source().resolve_anchor(&anchor).is_err());
    Ok(())
}
#[test]
fn historical_captured_hyperlink_gets_actual_range_not_new_native_acceptance() -> TestResult {
    let bytes = fixture::captured()?;
    let source = fixture::forms(&bytes, "field-test")?;
    let fields = ImportedDocumentFields::import(&source)?;
    assert_eq!(
        (
            fields.receipt().field_ranges,
            fields.receipt().parameterized_ranges
        ),
        (1, 1)
    );
    assert_eq!(fields.fields()[0].native_kind, "HYPERLINK");
    for anchor in [
        &fields.fields()[0].begin_anchor,
        &fields.fields()[0].end_anchor,
    ] {
        assert!(source.source().resolve_anchor(anchor)?.element().is_some());
    }
    assert_eq!(fields.verify_source(&bytes)?, *fields.receipt());
    Ok(())
}
#[test]
fn empty_range_import_preserves_whole_original_body_and_resources() -> TestResult {
    let bytes = fixture::package(&paragraph("<hp:t>A</hp:t>"))?;
    let source = fixture::forms(&bytes, "field-test")?;
    let fields = ImportedDocumentFields::import(&source)?;
    assert!(fields.fields().is_empty());
    let mut draft = fields.graph().clone().into_draft();
    draft.metadata = source.graph().clone().into_draft().metadata;
    assert_eq!(
        DocumentGraph::from_draft(draft, DocumentGraphLimits::default())?,
        *source.graph()
    );
    Ok(())
}
