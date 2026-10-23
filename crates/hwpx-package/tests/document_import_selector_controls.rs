use hwpx_package::{BoundedZipReader,document_import::{ImportedSourcePackage,forms::ImportedDocumentForms,search::{
    SourceSearchQuery as Query,SourceSearchMode as Mode,SourceSearchLimits,SourceSearchLimitConfig as Config,SourceSearchError as E,
    selector::{SourceIndexScopeSelector as Scope,SourceIndexBoundary as Boundary},reviews::{SourceReviewTextPolicy as Policy,SourceTextRegion as Region},
    inspection::SourceControlKind as Kind,navigation::{SourceSearchNavigationRequest as Next,SourceSearchDirection as Direction}}}};
use domain_ir::{DocumentId,LogicalId,Node};
use sha2::{Digest as _,Sha256};
use std::io::{Cursor,Write};
use zip::{ZipWriter,CompressionMethod,write::SimpleFileOptions};
#[path="support/review_scope_fixture.rs"] mod fixture;
#[allow(dead_code)] #[path="support/document_import_review_assembly_fixture.rs"] mod assembly;
#[allow(dead_code)] #[path="support/review_cell_output_fixture.rs"] mod table;
type TestResult=Result<(),Box<dyn std::error::Error>>;
const TAB:&str="<hp:tab width='1' leader='0' type='0'/>";
fn forms(raw:&[u8])->Result<ImportedDocumentForms,Box<dyn std::error::Error>> {Ok(ImportedDocumentForms::import(ImportedSourcePackage::import(raw,
    DocumentId::parse("selector-controls")?,Sha256::digest(raw).into(),Default::default())?)?)}
fn all()->Policy{Policy{include_hidden_explanations:true,include_memo_bodies:true}}
fn query(q:&str)->Query<'_>{Query{query:q,mode:Mode::Literal,case_sensitive:true,whole_word:false,max_results:100}}
fn at(block:&hwpx_package::document_import::search::selector::inventory::SourceIndexBlockDescriptor,cut:usize)->Boundary{
    Boundary{paragraph_handle:block.paragraph_handle.clone(),block_index:block.block_index,normalized_scalar:cut}}
fn review_controls()->String{fixture::body().replace("BODY K K",&format!("BODY{TAB} K K")).replace("MEMO K K",&format!("MEMO{TAB} K K"))}
fn two_parts()->Result<Vec<u8>,Box<dyn std::error::Error>>{
    let raw=fixture::with_body("<hp:p id='1'><hp:run><hp:t>A<hp:lineBreak/></hp:t></hp:run></hp:p>")?;
    let mut reader=BoundedZipReader::open(Cursor::new(&raw),Default::default())?;let names:Vec<_>=reader.entries().iter().map(|e|e.path.as_str().to_owned()).collect();
    let mut writer=ZipWriter::new(Cursor::new(Vec::new()));for(i,name)in names.iter().enumerate(){let bytes=reader.read_entry(i)?;
        writer.start_file(name,SimpleFileOptions::default().compression_method(CompressionMethod::Stored))?;
        if name=="Contents/content.hpf"{let opf=String::from_utf8(bytes)?.replace("</o:manifest>","<o:item id='s2' href='Contents/section1.xml' media-type='application/xml'/></o:manifest>")
            .replace("</o:spine>","<o:itemref idref='s2'/></o:spine>");writer.write_all(opf.as_bytes())?;}else{writer.write_all(&bytes)?;}}
    writer.start_file("Contents/section1.xml",SimpleFileOptions::default().compression_method(CompressionMethod::Stored))?;
    write!(writer,"<hs:sec xmlns:hs='http://www.hancom.co.kr/hwpml/2011/section' xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph'><hp:p id='1'><hp:run><hp:t>B<hp:lineBreak/><hp:lineBreak/></hp:t></hp:run></hp:p></hs:sec>")?;
    Ok(writer.finish()?.into_inner())
}
#[test]
fn selector_controls_actual_object_node_selects_its_anchor_even_when_parent_paragraph_is_outside()->TestResult{
    let raw=assembly::package(&format!("<hp:t>OUTSIDE</hp:t>{}<hp:t>AFTER</hp:t>",table::table(300)))?;let f=forms(&raw)?;
    let node=f.body_structure().graph().sections()[0].body.children.iter().find_map(|n|if let Node::Table(t)=n{Some(t)}else{None}).ok_or("table")?;
    let index=f.source_review_scope_index(&raw,Default::default())?;let nodes=[node.common.node_id.clone()];
    let found=index.find_control(Scope::NodeSet(&nodes),all(),Kind::Table,1)?;assert_eq!(found.controls().len(),1);
    assert_eq!(found.controls()[0].control_anchor,node.common.source_anchor.clone().ok_or("anchor")?);
    assert_ne!(found.controls()[0].paragraph_anchor.opaque_handle,found.controls()[0].control_anchor.opaque_handle);Ok(())
}
#[test]
fn selector_controls_document_section_and_nested_nodes_do_not_duplicate_or_use_parent_membership()->TestResult{
    let raw=fixture::with_body(&review_controls())?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?;
    let doc=index.find_control(Scope::Document,all(),Kind::Tab,2)?;let section=index.find_control(Scope::Section(&inv.inventory.section_ids),all(),Kind::Tab,2)?;
    assert_eq!(doc.controls(),section.controls());let memo=inv.block_regions.iter().position(|r|*r==Region::MemoBody).ok_or("memo")?;
    let node=inv.inventory.nodes.iter().find(|n|n.source_handle==inv.inventory.blocks[memo].paragraph_handle).ok_or("node")?.node_id.clone();
    let one=index.find_control(Scope::NodeSet(&[node.clone()]),all(),Kind::Tab,1)?;assert_eq!(one.match_regions(),[Region::MemoBody]);
    let parent=f.body_structure().graph().sections()[0].body.children[0].common().node_id.clone();
    let both=index.find_control(Scope::NodeSet(&[parent.clone(),node.clone()]),all(),Kind::Tab,2)?;
    assert_eq!(both.controls(),doc.controls());assert_eq!(both.canonical_json()?,index.find_control(Scope::NodeSet(&[node,parent]),all(),Kind::Tab,2)?.canonical_json()?);
    assert_ne!(doc.request_sha256(),section.request_sha256());Ok(())
}
#[test]
fn selector_controls_partial_nfc_windows_select_tab_and_linebreak_atoms_not_the_whole_paragraph()->TestResult{
    let raw=fixture::with_body(&format!("<hp:p id='1'><hp:run><hp:t>A{TAB}B<hp:lineBreak/>C{TAB}D</hp:t></hp:run></hp:p>"))?;
    let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?;let b=&inv.inventory.blocks[0];
    for (a,z,kind,count)in[(1,2,Kind::Tab,1),(2,3,Kind::Tab,0),(3,4,Kind::LineBreak,1),(4,5,Kind::Tab,0),(5,6,Kind::Tab,1),(1,1,Kind::Tab,0),(2,2,Kind::Tab,0)]{
        let start=at(b,a);let end=at(b,z);let found=index.find_control(Scope::Selection{index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},all(),kind,1)?;
        assert_eq!(found.controls().len(),count);}
    Ok(())
}
#[test]
fn selector_controls_cross_block_gaps_include_only_actual_intervening_control_starts()->TestResult{
    let raw=fixture::with_body("<hp:p id='1'><hp:run><hp:pic/><hp:t>A</hp:t><hp:pic/><hp:t>B</hp:t><hp:pic/></hp:run></hp:p>")?;
    let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?;assert_eq!(inv.inventory.blocks.len(),2);
    let start=at(&inv.inventory.blocks[0],1);let end=at(&inv.inventory.blocks[1],0);let found=index.find_control(Scope::Selection{index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},all(),Kind::Picture,1)?;
    assert_eq!(found.controls().len(),1);assert_eq!(found.scope_receipt().selected_normalized_scalars,0);
    assert_eq!(index.find_control(Scope::Document,all(),Kind::Picture,3)?.controls().len(),3);Ok(())
}
#[test]
fn selector_controls_policy_exclusions_precede_caps_and_supplemental_scope_stays_valid_when_excluded()->TestResult{
    let body=review_controls().replace("HIDDEN K K",&format!("HIDDEN{TAB} K K"));let raw=fixture::with_body(&body)?;let f=forms(&raw)?;
    let index=f.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?;let mut digests=std::collections::BTreeSet::new();
    for(hidden,memo,count)in[(false,false,1),(true,false,2),(false,true,2),(true,true,3)]{
        let found=index.find_control(Scope::Document,Policy{include_hidden_explanations:hidden,include_memo_bodies:memo},Kind::Tab,count)?;
        assert_eq!(found.controls().len(),count);digests.insert(found.request_sha256());}
    assert_eq!(digests.len(),4);assert!(matches!(index.find_control(Scope::Document,all(),Kind::Tab,2),Err(E::Limit)));
    let i=inv.block_regions.iter().position(|r|*r==Region::MemoBody).ok_or("memo")?;let node=inv.inventory.nodes.iter().find(|n|n.source_handle==inv.inventory.blocks[i].paragraph_handle).ok_or("node")?;
    let excluded=index.find_control(Scope::NodeSet(&[node.node_id.clone()]),Policy::default(),Kind::Tab,1)?;
    assert!(excluded.controls().is_empty());assert_eq!(serde_json::from_slice::<serde_json::Value>(&excluded.canonical_json()?)?["excluded_memo_controls"],1);Ok(())
}
#[test]
fn selector_controls_sections_and_cross_part_selection_use_spine_not_lexicographic_or_local_ids()->TestResult{
    let raw=two_parts()?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?;
    for(i,count)in[(0,1),(1,2)]{assert_eq!(index.find_control(Scope::Section(&[inv.inventory.section_ids[i].clone()]),all(),Kind::LineBreak,count)?.controls().len(),count);}
    let start=at(&inv.inventory.blocks[0],1);let end=at(&inv.inventory.blocks[1],2);
    let selected=index.find_control(Scope::Selection{index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},all(),Kind::LineBreak,2)?;
    assert_eq!(selected.controls().len(),2);assert_ne!(selected.controls()[0].paragraph_anchor.opaque_handle,selected.controls()[1].paragraph_anchor.opaque_handle);Ok(())
}
#[test]
fn selector_controls_xml_references_and_crlf_preserve_original_atom_and_scalar_order()->TestResult{
    // Literal/reference control characters are rejected by the original text reader, not admitted
    // as lineBreak atoms. Preserve that policy and check its exact import error before projection.
    for prefix in["A&amp;&#13;\r\n","A&#13;","A\r\n"]{
        let raw=fixture::with_body(&format!("<hp:p id='1'><hp:run><hp:t>{prefix}{TAB}Z</hp:t></hp:run></hp:p>"))?;
        let source=ImportedSourcePackage::import(&raw,DocumentId::parse("selector-controls")?,Sha256::digest(&raw).into(),Default::default())?;
        assert!(matches!(ImportedDocumentForms::import(source),Err(hwpx_package::document_import::forms::FormImportError::Body(
            hwpx_package::document_import::structure::StructureImportError::Paragraph{code:"text_flow_invalid_text"}))));
    }
    for prefix in["A&amp;&#x41;","Aé각","A&#x65;&#769;"]{
        let raw=fixture::with_body(&format!("<hp:p id='1'><hp:run><hp:t>{prefix}{TAB}Z<hp:lineBreak/></hp:t></hp:run></hp:p>"))?;
        let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?;
        let text=index.find(query("\t"),Scope::Document,all())?;let m=&text.result().matches()[0];let b=&inv.inventory.blocks[m.block_index];
        let start=at(b,m.start_normalized_scalar);let end=at(b,m.end_normalized_scalar);
        let scope=Scope::Selection{index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end};
        assert_eq!(index.find_control(scope,all(),Kind::Tab,1)?.controls().len(),1);assert!(index.find_control(scope,all(),Kind::LineBreak,1)?.controls().is_empty());}
    Ok(())
}
#[test]
fn selector_controls_nfc_reordering_cannot_be_guessed_into_a_contiguous_original_boundary()->TestResult{
    let raw=fixture::with_body(&format!("<hp:p id='1'><hp:run><hp:t>x\u{315}\u{300}{TAB}Z</hp:t></hp:run></hp:p>"))?;
    let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?;let b=&inv.inventory.blocks[0];
    let start=at(b,2);let end=at(b,4);let scope=Scope::Selection{index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end};
    assert!(index.find(query("\t"),scope,all()).is_ok());assert!(matches!(index.find_control(scope,all(),Kind::Tab,1),Err(E::Scope)));
    let start=at(b,3);assert_eq!(index.find_control(Scope::Selection{index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},all(),Kind::Tab,1)?.controls().len(),1);Ok(())
}
#[test]
fn selector_controls_empty_paragraphs_and_opaque_text_do_not_widen_text_only_selection()->TestResult{
    let raw=fixture::with_body("<hp:p id='1'><hp:run><hp:pic/></hp:run></hp:p><hp:p id='2'><hp:run><hp:t>A</hp:t></hp:run></hp:p>")?;
    let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?;let start=at(&inv.inventory.blocks[0],0);let end=at(&inv.inventory.blocks[1],0);
    assert!(index.find_control(Scope::Selection{index_sha256:inv.inventory.index.index_sha256,start:&start,end:&start},all(),Kind::Picture,1)?.controls().is_empty());
    assert_eq!(index.find_control(Scope::Selection{index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},all(),Kind::Picture,1)?.controls().len(),1);
    let raw=fixture::with_body("<hp:p id='1'><hp:run><hp:t>A<hp:nbSpace/></hp:t><hp:t>B</hp:t><u:future><hp:pic/></u:future></hp:run></hp:p>")?;
    let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;
    assert_eq!(index.find_control(Scope::Document,all(),Kind::NonbreakingSpace,1)?.controls().len(),1);
    assert!(index.find_control(Scope::Document,all(),Kind::Picture,1)?.controls().is_empty());Ok(())
}
#[test]
fn selector_controls_forged_stale_duplicate_reversed_and_out_of_range_scopes_fail_without_hits()->TestResult{
    let raw=fixture::package()?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?;let b=&inv.inventory.blocks[0];let start=at(b,0);let end=at(b,1);
    let foreign=LogicalId::parse("foreign")?;for ids in[vec![],vec![inv.inventory.section_ids[0].clone();2],vec![foreign.clone()]]{assert!(matches!(index.find_control(Scope::Section(&ids),all(),Kind::Video,1),Err(E::Scope)));}
    for ids in[vec![],vec![inv.inventory.nodes[0].node_id.clone();2],vec![foreign.clone()]]{assert!(matches!(index.find_control(Scope::NodeSet(&ids),all(),Kind::Video,1),Err(E::Scope)));}
    for(sha,a,z)in[([0;32],start.clone(),end.clone()),(inv.inventory.index.index_sha256,end.clone(),start.clone()),
        (inv.inventory.index.index_sha256,Boundary{paragraph_handle:foreign,..start.clone()},end.clone()),
        (inv.inventory.index.index_sha256,start.clone(),at(b,b.normalized_scalars+1))]{
        assert!(matches!(index.find_control(Scope::Selection{index_sha256:sha,start:&a,end:&z},all(),Kind::Video,1),Err(E::Scope)));}
    for max in[0,10_001]{assert!(matches!(index.find_control(Scope::Document,all(),Kind::Video,max),Err(E::Limit)));}Ok(())
}
#[test]
fn selector_controls_navigation_is_actual_source_order_with_regions_and_full_scope_policy_binding()->TestResult{
    let body=review_controls().replace("CACHE FROZEN",&format!("CACHE{TAB} FROZEN"));let raw=fixture::with_body(&body)?;let f=forms(&raw)?;
    let index=f.source_review_scope_index(&raw,Default::default())?;let found=index.find_control(Scope::Document,all(),Kind::Tab,3)?;
    assert_eq!(found.match_regions(),[Region::BodyAndNotes,Region::MemoBody,Region::BodyAndNotes]);
    let first=found.navigate(&Next{direction:Direction::Forward,wrap:false,cursor:None},[3;32])?;let request=Next{direction:Direction::Forward,wrap:false,cursor:first.cursor().cloned()};
    let second=found.navigate(&request,[3;32])?;assert_eq!(serde_json::from_slice::<serde_json::Value>(&second.canonical_json()?)?["region"],"memo_body");
    let other=index.find_control(Scope::Document,Policy::default(),Kind::Tab,3)?;assert!(matches!(other.navigate(&request,[3;32]),Err(E::Cursor)));
    assert!(matches!(found.navigate(&request,[4;32]),Err(E::Cursor)));let inv=index.scope_inventory()?;
    let other=index.find_control(Scope::Section(&inv.inventory.section_ids),all(),Kind::Tab,3)?;assert!(matches!(other.navigate(&request,[3;32]),Err(E::Cursor)));
    let last=found.navigate(&Next{direction:Direction::Backward,wrap:false,cursor:None},[3;32])?;
    let exhausted=found.navigate(&Next{direction:Direction::Forward,wrap:false,cursor:last.cursor().cloned()},[3;32])?;assert!(exhausted.exhausted());assert_eq!(exhausted.cursor(),last.cursor());
    assert!(found.navigate(&Next{direction:Direction::Forward,wrap:true,cursor:last.cursor().cloned()},[3;32])?.wrapped());Ok(())
}
#[test]
fn selector_controls_exact_whole_response_limit_privacy_and_original_preservation()->TestResult{
    let raw=fixture::with_body(&review_controls())?;let original=Sha256::digest(&raw);let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;
    let bytes=index.find_control(Scope::Document,all(),Kind::Tab,2)?.canonical_json()?;let size=bytes.len();
    let exact=f.source_review_scope_index(&raw,SourceSearchLimits::new(Config{result_bytes:size,..Default::default()})?)?;
    assert_eq!(exact.find_control(Scope::Document,all(),Kind::Tab,2)?.canonical_json()?,bytes);
    let limited=f.source_review_scope_index(&raw,SourceSearchLimits::new(Config{result_bytes:size-1,..Default::default()})?)?;
    assert!(matches!(limited.find_control(Scope::Document,all(),Kind::Tab,2),Err(E::Output)));
    let value:serde_json::Value=serde_json::from_slice(&bytes)?;assert_eq!(value["native_visibility_flow_control_semantics_or_execution_authority"],false);
    let text=String::from_utf8(bytes)?;assert!(!text.contains("PRIVATE-AUTHOR")&&!text.contains("BODY K")&&!text.contains("MEMO K"));
    assert_eq!(Sha256::digest(&raw),original);Ok(())
}
