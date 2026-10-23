use super::*;
use hwpx_package::document_import::{ImportedSourcePackage,forms::ImportedDocumentForms};
#[allow(dead_code)]
#[path="../../../../../../hwpx-package/tests/support/search_definition_fixture.rs"] mod fixture;
type TestResult=Result<(),Box<dyn std::error::Error>>;
fn forms(text:&str)->Result<ImportedDocumentForms,Box<dyn std::error::Error>>{
    let bytes=fixture::package(&format!("<hp:p id='1'><hp:run><hp:t>{text}</hp:t></hp:run></hp:p>"))?;
    Ok(ImportedDocumentForms::import(ImportedSourcePackage::import(&bytes,DocumentId::parse("compiler-owner-unit")?,Sha256::digest(&bytes).into(),Default::default())?)?)
}
fn text_anchor(forms:&ImportedDocumentForms)->Result<SourceAnchorHandle,Box<dyn std::error::Error>>{
    for part in forms.source().parts(){if part.path().as_str()=="Contents/section0.xml"{let xml=part.xml().ok_or("xml")?;
        for(i,e)in xml.elements().iter().enumerate(){if e.name().local_name()=="t"{return Ok(part.element_anchor(i).ok_or("anchor")?.clone());}}
    }}Err("text".into())
}
#[test]
fn actual_parent_owner_is_resolved_from_source_not_an_invented_node()->TestResult{
    let f=forms("K")?;let anchor=text_anchor(&f)?;let result=resolve_parts(f.graph(),f.source(),&[projection::Edit{anchor:&anchor,subtree:None}])?;
    assert_eq!(result,[f.graph().sections()[0].body.children[0].common().node_id.clone()]);Ok(())
}
#[test]
fn actual_header_anchor_has_no_body_owner_and_is_not_redirected_to_first_paragraph()->TestResult{
    let f=forms("K")?;let part=f.source().parts().iter().find(|p|p.path().as_str()=="Contents/header.xml").ok_or("header")?;
    let anchor=part.element_anchor(0).ok_or("anchor")?;
    assert!(matches!(resolve_parts(f.graph(),f.source(),&[projection::Edit{anchor,subtree:None}]),Err(CompiledSearchError::Target)));Ok(())
}
#[test]
fn forged_fingerprint_and_foreign_package_anchor_fail_closed()->TestResult{
    let f=forms("K")?;let mut anchor=text_anchor(&f)?;anchor.fingerprint_sha256[0]^=1;
    assert!(matches!(resolve_parts(f.graph(),f.source(),&[projection::Edit{anchor:&anchor,subtree:None}]),Err(CompiledSearchError::Target)));
    let other=forms("OTHER")?;let anchor=text_anchor(&other)?;
    assert!(matches!(resolve_parts(f.graph(),f.source(),&[projection::Edit{anchor:&anchor,subtree:None}]),Err(CompiledSearchError::Target)));Ok(())
}
#[test]
fn duplicate_source_edits_are_rejected_instead_of_silently_deduplicated()->TestResult{
    let f=forms("K")?;let anchor=text_anchor(&f)?;
    assert!(matches!(resolve_parts(f.graph(),f.source(),&[projection::Edit{anchor:&anchor,subtree:None},projection::Edit{anchor:&anchor,subtree:None}]),Err(CompiledSearchError::Target)));Ok(())
}
#[test]
fn wrong_final_subtree_extent_is_not_accepted_as_an_edit_permission()->TestResult{
    let f=forms("K")?;let anchor=text_anchor(&f)?;let span=f.source().resolve_anchor(&anchor)?.element().and_then(|e|e.outer_span()).ok_or("span")?;
    assert!(matches!(resolve_parts(f.graph(),f.source(),&[projection::Edit{anchor:&anchor,subtree:Some((span.start(),span.end()+1))}]),Err(CompiledSearchError::Target)));Ok(())
}
#[test]
fn ambiguous_actual_source_owner_is_rejected_instead_of_selecting_first_id()->TestResult{
    let f=forms("K")?;let anchor=text_anchor(&f)?;let mut draft=f.graph().clone().into_draft();
    let Node::Paragraph(mut duplicate)=draft.sections[0].body.children[0].clone()else{return Err("paragraph".into())};
    duplicate.common.node_id=LogicalId::parse("second-node-same-actual-anchor")?;draft.sections[0].body.children.push(Node::Paragraph(duplicate));
    let error=domain_ir::DocumentGraph::from_draft(draft,Default::default()).err().ok_or("ambiguous source graph admitted")?;
    assert_eq!(error,domain_ir::DocumentGraphError::DuplicateIdentifier);
    let owner=f.graph().sections()[0].body.children[0].common().source_anchor.as_ref().ok_or("owner")?;
    let outer=f.source().resolve_anchor(owner)?.element().and_then(|e|e.outer_span()).ok_or("outer")?;
    let inner=f.source().resolve_anchor(&anchor)?.element().and_then(|e|e.outer_span()).ok_or("inner")?;
    assert!(outer.start()<=inner.start()&&inner.end()<=outer.end());Ok(())
}
