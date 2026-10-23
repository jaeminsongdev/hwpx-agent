use hwpx_package::{BoundedZipReader,document_import::{ImportedSourcePackage,SourceImportLimits,
    structure::ImportedDocumentStructure,forms::ImportedDocumentForms,search::{SourceSearchQuery as Query,SourceSearchMode as Mode,
        SourceSearchLimits,SourceSearchLimitConfig as Config,SourceSearchError as E,selector::{SourceIndexScopeSelector as Scope,SourceIndexBoundary as Boundary}}}};
use domain_ir::{DocumentId,LogicalId,Node};
use sha2::{Digest as _,Sha256};
use std::{error::Error,io::{Cursor,Write}};
use zip::{ZipWriter,CompressionMethod,write::SimpleFileOptions};
#[allow(dead_code)] #[path="support/document_import_field_fixture.rs"] mod fixture;
#[allow(dead_code)] #[path="support/document_import_review_assembly_fixture.rs"] mod assembly;
#[allow(dead_code)] #[path="support/review_cell_output_fixture.rs"] mod table;
type TestResult=Result<(),Box<dyn Error>>;
fn paragraph(text:&str,id:u32)->String {format!("<hp:p id='{id}'><hp:run><hp:t>{}</hp:t></hp:run></hp:p>",quick_xml::escape::escape(text))}
fn query(q:&str)->Query<'_> {Query {query:q,mode:Mode::Literal,case_sensitive:true,whole_word:false,max_results:100}}
fn import(bytes:&[u8],document:&str)->Result<ImportedDocumentStructure,Box<dyn Error>> {Ok(ImportedDocumentStructure::import(
    ImportedSourcePackage::import(bytes,DocumentId::parse(document)?,Sha256::digest(bytes).into(),SourceImportLimits::default())?)?)}
fn boundary(found:&hwpx_package::document_import::search::SourceSearchMatch,scalar:usize)->Boundary {
    Boundary {paragraph_handle:found.paragraph_anchor.opaque_handle.clone(),block_index:found.block_index,normalized_scalar:scalar}
}
fn two_sections()->Result<Vec<u8>,Box<dyn Error>> {
    let raw=fixture::package(&paragraph("PRIVATE-same",1))?;let mut reader=BoundedZipReader::open(Cursor::new(&raw),Default::default())?;
    let names:Vec<_>=reader.entries().iter().map(|e|e.path.as_str().to_owned()).collect();let mut writer=ZipWriter::new(Cursor::new(Vec::new()));
    for (i,name) in names.iter().enumerate() {let bytes=reader.read_entry(i)?;writer.start_file(name,SimpleFileOptions::default().compression_method(CompressionMethod::Stored))?;
        if name=="Contents/content.hpf" {let opf=String::from_utf8(bytes)?.replace("</o:manifest>","<o:item id='s2' href='Contents/section1.xml' media-type='application/xml'/></o:manifest>")
            .replace("</o:spine>","<o:itemref idref='s2'/></o:spine>");writer.write_all(opf.as_bytes())?;}else{writer.write_all(&bytes)?;}}
    writer.start_file("Contents/section1.xml",SimpleFileOptions::default().compression_method(CompressionMethod::Stored))?;
    write!(writer,"<hs:sec xmlns:hs='http://www.hancom.co.kr/hwpml/2011/section' xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph'>{}</hs:sec>",paragraph("same same same",1))?;
    Ok(writer.finish()?.into_inner())
}
#[test]
fn selector_document_retains_original_matches_and_explicit_partial_source_authority()->TestResult {
    let raw=fixture::package(&format!("{}{}",paragraph("PRIVATE-same same",1),paragraph("same",2)))?;let s=import(&raw,"scope-selector")?;let i=s.source_text_index(&raw,Default::default())?;
    let found=i.find_selector(query("same"),Scope::Document)?;assert_eq!(found.result().matches(),i.find(query("same"))?.matches());
    assert_eq!(found.scope_receipt().kind,"document");assert_eq!(found.scope_receipt().selected_paragraphs,2);
    assert!(!found.scope_receipt().whole_document_visibility_native_flow_or_revision_authority);
    let json=String::from_utf8(found.canonical_json()?)?;assert!(!json.contains("PRIVATE-same"));assert!(!format!("{found:?}").contains("PRIVATE-same"));Ok(())
}
#[test]
fn selector_actual_section_ids_separate_identical_local_paragraph_ids_and_exclude_before_match_caps()->TestResult {
    let raw=two_sections()?;let s=import(&raw,"two-sections")?;let i=s.source_text_index(&raw,Default::default())?;
    let first=s.graph().sections()[0].section_id.clone();let second=s.graph().sections()[1].section_id.clone();assert_ne!(first,second);
    let one=i.find_selector(Query {max_results:1,..query("same")},Scope::Section(&[first]))?;
    assert_eq!(one.result().matches().len(),1);assert_eq!(one.result().matches()[0].block_index,0);assert_eq!(one.scope_receipt().selected_sections,1);
    let other=i.find_selector(query("same"),Scope::Section(&[second]))?;assert_eq!(other.result().matches().len(),3);assert_eq!(other.result().matches()[0].block_index,1);
    assert_ne!(one.scope_receipt().scope_sha256,other.scope_receipt().scope_sha256);Ok(())
}
#[test]
fn selector_section_sets_are_canonical_and_reject_empty_duplicate_foreign_ids_without_query_hits()->TestResult {
    let raw=two_sections()?;let s=import(&raw,"two-sections")?;let i=s.source_text_index(&raw,Default::default())?;
    let a=s.graph().sections()[0].section_id.clone();let b=s.graph().sections()[1].section_id.clone();
    let forward=i.find_selector(query("absent"),Scope::Section(&[a.clone(),b.clone()]))?;let reverse=i.find_selector(query("absent"),Scope::Section(&[b,a.clone()]))?;
    assert_eq!(forward.canonical_json()?,reverse.canonical_json()?);assert_ne!(forward.scope_receipt().scope_sha256,i.find_selector(query("absent"),Scope::Document)?.scope_receipt().scope_sha256);
    for bad in [vec![],vec![a.clone(),a],vec![LogicalId::parse("foreign-section")?]] {assert!(matches!(i.find_selector(query("absent"),Scope::Section(&bad)),Err(E::Scope)));}Ok(())
}
#[test]
fn selector_node_set_resolves_actual_graph_ids_not_source_paragraph_handle_aliases()->TestResult {
    let raw=fixture::package(&format!("{}{}",paragraph("same same",1),paragraph("same",2)))?;let s=import(&raw,"nodes")?;let i=s.source_text_index(&raw,Default::default())?;
    let nodes=&s.graph().sections()[0].body.children;let a=nodes[0].common().node_id.clone();let b=nodes[1].common().node_id.clone();
    let one=i.find_selector(Query {max_results:1,..query("same")},Scope::NodeSet(&[b.clone()]))?;assert_eq!(one.result().matches()[0].block_index,1);
    assert_eq!(one.scope_receipt().selected_nodes,1);assert_eq!(one.scope_receipt().selected_paragraphs,1);
    let x=i.find_selector(query("same"),Scope::NodeSet(&[a.clone(),b.clone()]))?;let y=i.find_selector(query("same"),Scope::NodeSet(&[b,a.clone()]))?;assert_eq!(x.canonical_json()?,y.canonical_json()?);
    let source_handle=nodes[0].common().source_anchor.as_ref().ok_or("anchor")?.opaque_handle.clone();assert_ne!(source_handle,a);
    for bad in [vec![],vec![a.clone(),a],vec![source_handle],vec![LogicalId::parse("foreign-node")?]] {assert!(matches!(i.find_selector(query("absent"),Scope::NodeSet(&bad)),Err(E::Scope)));}Ok(())
}
#[test]
fn selector_table_node_includes_descendant_cells_and_overlapping_selected_nodes_do_not_duplicate_matches()->TestResult {
    let raw=assembly::package(&format!("<hp:t>OUTSIDE-CELL</hp:t>{}",table::table(300)))?;let s=import(&raw,"table-selector")?;let i=s.source_text_index(&raw,Default::default())?;
    let node=s.graph().sections()[0].body.children.iter().find_map(|n|if let Node::Table(t)=n{Some(t)}else{None}).ok_or("table node")?;
    let table_id=node.common.node_id.clone();let cell_id=node.cells[0].body.children[0].common().node_id.clone();
    let one=i.find_selector(query("CELL"),Scope::NodeSet(&[table_id.clone()]))?;assert_eq!(one.result().matches().len(),2);
    let both=i.find_selector(query("CELL"),Scope::NodeSet(&[table_id,cell_id]))?;assert_eq!(both.result().matches(),one.result().matches());assert_eq!(both.scope_receipt().selected_nodes,2);Ok(())
}
#[test]
fn selector_selection_clips_before_regex_and_whole_word_checks_with_global_result_coordinates()->TestResult {
    let raw=fixture::package(&paragraph("xxsameyy",1))?;let s=import(&raw,"selection")?;let i=s.source_text_index(&raw,Default::default())?;
    let all=i.find(query("same"))?;let start=boundary(&all.matches()[0],2);let end=boundary(&all.matches()[0],6);let scope=Scope::Selection {index_sha256:i.receipt().index_sha256,start:&start,end:&end};
    assert!(i.find(Query {whole_word:true,..query("same")})?.matches().is_empty());
    for q in [Query {query:"^same$",mode:Mode::Regex,..query("same")},Query {whole_word:true,..query("same")}] {
        let found=i.find_selector(q,scope)?;assert_eq!(found.result().matches().len(),1);let m=&found.result().matches()[0];
        assert_eq!((m.start_normalized_scalar,m.end_normalized_scalar),(2,6));assert_eq!((m.pieces[0].start_scalar,m.pieces[0].end_scalar),(2,6));}
    assert_eq!(i.find_selector(query("same"),scope)?.scope_receipt().selected_normalized_scalars,4);Ok(())
}
#[test]
fn selector_selection_cross_run_hangul_nfc_preserves_three_original_scalar_contributions()->TestResult {
    let raw=fixture::package("<hp:p id='1'><hp:run><hp:t>Xᄀ</hp:t></hp:run><hp:run><hp:t>ᅡ</hp:t></hp:run><hp:run><hp:t>ᆨY</hp:t></hp:run></hp:p>")?;
    let s=import(&raw,"nfc-selector")?;let i=s.source_text_index(&raw,Default::default())?;let all=i.find(query("각"))?;
    let start=boundary(&all.matches()[0],1);let end=boundary(&all.matches()[0],2);
    let found=i.find_selector(query("각"),Scope::Selection {index_sha256:i.receipt().index_sha256,start:&start,end:&end})?;
    assert_eq!(found.result().matches(),all.matches());assert_eq!(found.result().matches()[0].pieces.len(),3);assert!(found.result().matches()[0].source_scalar_selection_exact);Ok(())
}
#[test]
fn selector_selection_across_paragraphs_and_opaque_barriers_does_not_concatenate_fragments()->TestResult {
    let raw=fixture::package("<hp:p id='1'><hp:run><hp:t>AA123</hp:t><u:barrier/><hp:t>456BB</hp:t></hp:run></hp:p><hp:p id='2'><hp:run><hp:t>CC789DD</hp:t></hp:run></hp:p>")?;
    let s=import(&raw,"barrier-selector")?;let i=s.source_text_index(&raw,Default::default())?;let found=i.find(Query {query:r"\d+",mode:Mode::Regex,..query("unused")})?;
    let start=boundary(&found.matches()[0],2);let end=boundary(&found.matches()[2],5);let scope=Scope::Selection {index_sha256:i.receipt().index_sha256,start:&start,end:&end};
    assert_eq!(i.find_selector(Query {query:r"\d+",mode:Mode::Regex,..query("unused")},scope)?.result().matches(),found.matches());
    assert!(i.find_selector(query("123456"),scope)?.result().matches().is_empty());assert_eq!(i.find_selector(query("absent"),scope)?.scope_receipt().selected_blocks,3);Ok(())
}
#[test]
fn selector_collapsed_selection_is_a_bounded_zero_width_position_not_an_editable_range()->TestResult {
    let raw=fixture::package(&paragraph("abc",1))?;let s=import(&raw,"caret-selector")?;let i=s.source_text_index(&raw,Default::default())?;let found=i.find(query("b"))?;
    let at=boundary(&found.matches()[0],1);let scope=Scope::Selection {index_sha256:i.receipt().index_sha256,start:&at,end:&at};
    assert!(i.find_selector(query("b"),scope)?.result().matches().is_empty());let empty=i.find_selector(Query {query:"^$",mode:Mode::Regex,..query("x")},scope)?;
    assert_eq!(empty.result().matches().len(),1);let m=&empty.result().matches()[0];assert_eq!((m.start_normalized_scalar,m.end_normalized_scalar),(1,1));
    assert!(m.zero_width&&m.pieces.is_empty()&&!m.source_scalar_selection_exact);assert_eq!(empty.scope_receipt().selected_normalized_scalars,0);Ok(())
}
#[test]
fn selector_selection_rejects_stale_forged_reverse_out_of_bounds_and_partial_nfc_contribution_boundaries()->TestResult {
    let raw=fixture::package(&paragraph("1\u{0344}z",1))?;let s=import(&raw,"invalid-selector")?;let i=s.source_text_index(&raw,Default::default())?;
    let all=i.find(query("1"))?;let start=boundary(&all.matches()[0],0);let end=boundary(&all.matches()[0],4);
    assert!(i.find_selector(query("absent"),Scope::Selection {index_sha256:i.receipt().index_sha256,start:&start,end:&end}).is_ok());
    let mut bad=start.clone();bad.normalized_scalar=2;assert!(matches!(i.find_selector(query("absent"),Scope::Selection {index_sha256:i.receipt().index_sha256,start:&bad,end:&end}),Err(E::Scope)));
    for (a,b,hash) in [(start.clone(),end.clone(),[0;32]),(end.clone(),start.clone(),i.receipt().index_sha256),
        (Boundary {normalized_scalar:5,..start.clone()},end.clone(),i.receipt().index_sha256),
        (Boundary {block_index:usize::MAX,..start.clone()},end.clone(),i.receipt().index_sha256),
        (Boundary {paragraph_handle:LogicalId::parse("foreign-paragraph")?,..start.clone()},end.clone(),i.receipt().index_sha256)] {
        assert!(matches!(i.find_selector(query("absent"),Scope::Selection {index_sha256:hash,start:&a,end:&b}),Err(E::Scope)));}
    Ok(())
}
#[test]
fn selector_original_proof_and_document_source_identity_remain_required_without_revision_attestation()->TestResult {
    let raw=fixture::package(&paragraph("same",1))?;
    let forms=ImportedDocumentForms::import(ImportedSourcePackage::import(&raw,DocumentId::parse("selector-proof")?,Sha256::digest(&raw).into(),Default::default())?)?;
    let proof=forms.reconstruct_source_for_verification(&raw)?;let shared=proof.source_text_index(&forms,Default::default())?;
    let direct=forms.body_structure().source_text_index(&raw,Default::default())?;
    assert_eq!(shared.find_selector(query("same"),Scope::Document)?.canonical_json()?,direct.find_selector(query("same"),Scope::Document)?.canonical_json()?);
    let other=import(&raw,"foreign-selector")?;let foreign=other.source_text_index(&raw,Default::default())?;
    assert_ne!(direct.find_selector(query("same"),Scope::Document)?.scope_receipt().scope_sha256,foreign.find_selector(query("same"),Scope::Document)?.scope_receipt().scope_sha256);
    let changed=fixture::package(&paragraph("changed",1))?;assert!(shared.verify_source(&changed).is_err());Ok(())
}
#[test]
fn selector_wrapper_scope_hash_catalog_and_selected_result_limits_are_finitely_bounded()->TestResult {
    let raw=fixture::package(&format!("{}{}",paragraph("same same",1),paragraph("same",2)))?;let s=import(&raw,"bounded-selector")?;
    let i=s.source_text_index(&raw,Default::default())?;let len=i.find(query("absent"))?.canonical_json()?.len();
    let small=s.source_text_index(&raw,SourceSearchLimits::new(Config {result_bytes:len,..Default::default()})?)?;
    assert!(small.find(query("absent")).is_ok());assert!(matches!(small.find_selector(query("absent"),Scope::Document),Err(E::Output)));
    assert!(matches!(i.find_selector(Query {max_results:1,..query("same")},Scope::Document),Err(E::Limit)));
    let raw=fixture::package("<hp:p id='1'><hp:run><u:a/><u:b/><u:c/><hp:t>same</hp:t></hp:run></hp:p>")?;let s=import(&raw,"bounded-node-catalog")?;
    let i=s.source_text_index(&raw,SourceSearchLimits::new(Config {blocks:1,..Default::default()})?)?;let id=s.graph().sections()[0].body.children[0].common().node_id.clone();
    assert!(matches!(i.find_selector(query("same"),Scope::NodeSet(&[id])),Err(E::Limit)));Ok(())
}
