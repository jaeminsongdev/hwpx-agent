use std::error::Error;
use domain_ir::{Flow, Node, Properties, PropertyValue};
use hwpx_package::document_import::{
    fields::{ImportedDocumentFields, semantics::ImportedDocumentFieldSemantics},
    structure::ImportedDocumentStructure,
};
#[path="support/document_import_field_fixture.rs"]
mod fixture;
#[path="support/document_import_note_fixture.rs"]
mod notes;
type TestResult = Result<(), Box<dyn Error>>;

fn note(kind: &str, attrs: &str, body: &str) -> String {
    format!("<hp:ctrl><hp:{kind} {attrs}><hp:subList><hp:p id='9'><hp:run>{body}</hp:run></hp:p></hp:subList></hp:{kind}></hp:ctrl>")
}
fn paragraph(body: &str) -> String { format!("<hp:p id='1'><hp:run>{body}</hp:run></hp:p>") }
fn count(flow: &Flow) -> usize {
    flow.children.iter().map(|n| match n {
        Node::Paragraph(_) => 1,
        Node::Table(t) => t.cells.iter().map(|c| count(&c.body)).sum(),
        Node::Drawing(d) => count(&d.children),
        _=>0,
    }).sum()
}
#[test]
fn note_source_attrs_body_anchor_and_wrapper_link_are_real_without_number_defaults() -> TestResult {
    let bytes=fixture::package(&paragraph(&note("footNote", "instId='101'", "<hp:t>private note body</hp:t>")))?;
    let forms=fixture::forms(&bytes,"notes-test")?;
    assert_eq!(forms.notes().len(),1);
    let observed=&forms.notes()[0];
    assert_eq!(observed.native_instance_id,101);
    assert!(observed.native_attributes.iter().all(|(k,_)| k!="number"&&k!="flag"));
    assert!(forms.source().resolve_anchor(&observed.source_anchor)?.element().is_some());
    assert!(forms.source().resolve_anchor(&observed.body_anchor)?.element().is_some());
    let draft=forms.graph().clone().into_draft();
    assert_eq!(draft.notes.len(),1);
    assert_eq!(count(&draft.notes[0].body),1);
    let wrapper=draft.sections[0].body.children.iter().find(|n| n.common().node_id==observed.wrapper_node_id).ok_or("wrapper")?;
    let Node::EmbeddedObject(wrapper)=wrapper else{return Err("wrapper changed type".into());};
    assert!(wrapper.properties.iter().any(|(k,v)|k=="source_note_id"&&matches!(v,PropertyValue::Id(id) if id==&observed.note_id)));
    assert_eq!(forms.verify_source(&bytes)?,*forms.receipt());
    Ok(())
}
#[test]
fn same_native_instance_id_is_not_a_fabricated_global_or_persistent_identity() -> TestResult {
    let body=paragraph(&format!("{}{}",note("footNote","instId='101' number='1'","<hp:t>A</hp:t>"),note("endNote","instId='101' number='1'","<hp:t>B</hp:t>")));
    let forms=fixture::forms(&fixture::package(&body)?,"notes-test")?;
    assert_eq!(forms.notes().len(),2);
    assert_ne!(forms.notes()[0].note_id,forms.notes()[1].note_id);
    assert_eq!(forms.notes()[0].native_instance_id,forms.notes()[1].native_instance_id);
    Ok(())
}
#[test]
fn malformed_hidden_and_nested_native_notes_reject_instead_of_disappearing() -> TestResult {
    let good=note("footNote","instId='101'","<hp:t>A</hp:t>");
    for body in [good.replace("instId='101'","instId='0'"),good.replace("instId='101'","number='1'"),
        good.replace("<hp:ctrl>","<hp:ctrl unknown='1'>"),
        format!("<u:hidden>{good}</u:hidden>"),
        note("footNote","instId='102'",&good),
        good.replace("instId='101'","instId='101' number='70000'"),
    ] {
        let bytes=fixture::package(&paragraph(&body))?;
        assert!(fixture::forms(&bytes,"notes-test").is_err());
    }
    Ok(())
}
#[test]
fn note_body_fields_and_source_sorted_reference_identity_are_connected() -> TestResult {
    let mut fields=String::new();
    for id in 1..=24 { fields.push_str(&format!("<hp:ctrl><hp:fieldBegin id='{id}' type='DATE'/></hp:ctrl><hp:t>cache</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='{id}'/></hp:ctrl>")); }
    let bytes=fixture::package(&paragraph(&note("footNote","instId='101'",&fields)))?;
    let forms=fixture::forms(&bytes,"notes-test")?;
    let ranges=ImportedDocumentFields::import(&forms)?;
    assert_eq!(ranges.fields().len(),24);
    let source_order:Vec<_>=ranges.fields().iter().map(|f|f.reference_id.clone()).collect();
    let canonical_order:Vec<_>=ranges.graph().clone().into_draft().references.iter().map(|r|r.reference_id.clone()).collect();
    assert_ne!(source_order,canonical_order);
    let meanings=ImportedDocumentFieldSemantics::import(&ranges)?;
    assert_eq!(meanings.receipt().unsupported_meanings,24);
    let draft=meanings.graph().clone().into_draft();
    assert_eq!(draft.notes.len(),1);
    assert_eq!(draft.references.len(),24);
    assert_eq!(meanings.verify_source(&bytes)?,*meanings.receipt());
    Ok(())
}
#[test]
fn all_nine_generated_saved_reopened_note_packages_import_without_upgrading_old_failures() -> TestResult {
    let inputs=notes::actual_inputs()?;
    let mut lanes=[0usize;3];
    let mut observed=0usize;
    for input in inputs {
        let forms=fixture::forms(&input.bytes,"notes-test")?;
        assert_eq!(forms.notes().len(),input.expected_notes);
        assert_eq!(forms.graph().clone().into_draft().notes.len(),input.expected_notes);
        for note in forms.notes() {
            assert!(forms.source().resolve_anchor(&note.body_anchor)?.element().is_some());
        }
        let fields=ImportedDocumentFields::import(&forms)?;
        let meanings=ImportedDocumentFieldSemantics::import(&fields)?;
        assert_eq!(meanings.verify_source(&input.bytes)?,*meanings.receipt());
        observed+=forms.notes().len();
        lanes[match input.lane {"generated"=>0,"saved"=>1,"reopened"=>2,_=>return Err("lane".into())}]+=1;
    }
    assert_eq!(lanes,[3,3,3]);
    assert!(observed>=9);
    Ok(())
}
#[test]
fn fresh_note_text_change_is_rejected_and_metadata_debug_do_not_disclose_body() -> TestResult {
    let body=paragraph(&note("footNote","instId='101'","<hp:t>private note body</hp:t>"));
    let bytes=fixture::package(&body)?;
    let forms=fixture::forms(&bytes,"notes-test")?;
    let changed=fixture::package(&body.replace("private note body","changed note body"))?;
    assert!(forms.verify_source(&changed).is_err());
    assert!(!format!("{:?}{}",forms.notes(),serde_json::to_string(forms.receipt())?).contains("private note body"));
    Ok(())
}
#[test]
fn no_note_sources_keep_empty_note_table_without_new_note_qualifiers() -> TestResult {
    let bytes=fixture::package(&paragraph("<hp:t>plain</hp:t>"))?;
    let source=hwpx_package::document_import::ImportedSourcePackage::import(&bytes,domain_ir::DocumentId::parse("notes-test")?,
        sha2::Sha256::digest(&bytes).into(),hwpx_package::document_import::SourceImportLimits::default())?;
    let body=ImportedDocumentStructure::import(source)?;
    assert!(body.notes().is_empty());
    assert!(body.graph().clone().into_draft().notes.is_empty());
    let keys:Vec<_>=body.graph().clone().into_draft().metadata.iter().map(|(k,_)|k.to_owned()).collect();
    assert!(!keys.iter().any(|k|k.starts_with("note_import_")));
    let _=Properties::new();
    Ok(())
}
