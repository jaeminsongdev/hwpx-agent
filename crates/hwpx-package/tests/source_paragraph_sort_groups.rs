use hwpx_package::{BoundedZipReader,PackageLimits,WriterLimits,WriterLimitConfig,document_import::{forms::ImportedDocumentForms,
    search::{SourceSearchLimits,SourceSearchLimitConfig,SourceSearchError,selector::{SourceIndexScopeSelector as Scope,SourceIndexBoundary as Boundary},
        reviews::SourceReviewTextPolicy as Policy,replacement::{SourceLiteralReplacementError as Compile,atoms::sort::{
            SourceParagraphSortSpec as Spec,SourceParagraphSortDirection as Direction,SourceParagraphSortComparison as Comparison,
            SourceParagraphSortError as E,groups::SourceParagraphSortGroupsCandidate as Candidate}}}}};
use domain_ir::{LogicalId,Node};
use sha2::{Digest as _,Sha256};
use std::{error::Error,io::{Cursor,Write}};
#[allow(dead_code)] #[path="support/document_import_field_fixture.rs"]mod fixture;
#[allow(dead_code)] #[path="support/document_import_review_assembly_fixture.rs"]mod assembly;
#[allow(dead_code)] #[path="support/review_cell_output_fixture.rs"]mod table;
type TestResult=Result<(),Box<dyn Error>>;
fn spec()->Spec{Spec{direction:Direction::Ascending,comparison:Comparison::NfcUnicodeScalarLexicographic,max_comparison_bytes:1024*1024}}
fn p(id:usize,key:&str)->String{format!("<hp:p id='{id}'><hp:run><hp:t>{key}</hp:t></hp:run></hp:p>")}
fn sort(f:&ImportedDocumentForms,b:&[u8],scope:Scope<'_>,s:Spec)->Result<Candidate,E>{
    f.lower_selector_paragraph_sort_groups_candidate(b,scope,Policy::default(),s,Default::default(),Default::default())
}
fn bytes(c:&Candidate)->Result<Vec<u8>,Box<dyn Error>>{Ok(c.with_verified_bytes(<[u8]>::to_vec)?)}
fn part(b:&[u8],path:&str)->Result<Vec<u8>,Box<dyn Error>>{
    let mut zip=BoundedZipReader::open(Cursor::new(b),PackageLimits::default())?;
    let i=zip.entries().iter().find(|e|e.path.as_str()==path).ok_or("part")?.index;Ok(zip.read_entry(i)?)
}
fn cell_package(left:&[&str],right:&[&str])->Result<Vec<u8>,Box<dyn Error>>{
    let body=table::table(300).replace(&table::paragraph(0,"CELL-OLD"),&left.iter().enumerate().map(|(i,k)|table::paragraph(901+i as u32,k)).collect::<String>())
        .replace(&table::paragraph(0,"OTHER-CELL"),&right.iter().enumerate().map(|(i,k)|table::paragraph(1001+i as u32,k)).collect::<String>());
    assembly::package(&format!("<hp:t>OUTSIDE</hp:t>{body}"))
}
fn cells(f:&ImportedDocumentForms)->Result<Vec<Vec<LogicalId>>,Box<dyn Error>>{
    let t=f.body_structure().graph().sections()[0].body.children.iter().find_map(|n|if let Node::Table(t)=n{Some(t)}else{None}).ok_or("table")?;
    Ok(t.cells.iter().map(|c|c.body.children.iter().map(|n|n.common().node_id.clone()).collect()).collect())
}
fn two_parts(first:&str,second:&str)->Result<Vec<u8>,Box<dyn Error>>{
    use zip::{ZipWriter,CompressionMethod,write::SimpleFileOptions};
    let raw=fixture::package(first)?;let mut reader=BoundedZipReader::open(Cursor::new(&raw),Default::default())?;
    let names:Vec<_>=reader.entries().iter().map(|e|e.path.as_str().to_owned()).collect();let mut writer=ZipWriter::new(Cursor::new(Vec::new()));
    for(i,name)in names.iter().enumerate(){let data=reader.read_entry(i)?;
        writer.start_file(name,SimpleFileOptions::default().compression_method(CompressionMethod::Stored))?;
        if name=="Contents/content.hpf"{let text=String::from_utf8(data)?.replace("</o:manifest>","<o:item id='s2' href='Contents/section1.xml' media-type='application/xml'/></o:manifest>")
            .replace("</o:spine>","<o:itemref idref='s2'/></o:spine>");writer.write_all(text.as_bytes())?;}else{writer.write_all(&data)?;}}
    writer.start_file("Contents/section1.xml",SimpleFileOptions::default().compression_method(CompressionMethod::Stored))?;
    writer.write_all(format!("<hs:sec xmlns:hs='http://www.hancom.co.kr/hwpml/2011/section' xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph'>{second}</hs:sec>").as_bytes())?;
    Ok(writer.finish()?.into_inner())
}

#[test]
fn groups_two_cells_move_unequal_original_subtrees_without_crossing_parents()->TestResult{
    let raw=cell_package(&["Z-LONG","A&amp;B"],&["Y","B-LONGER"])?;let before=raw.clone();let f=fixture::forms(&raw,"groups-cells")?;
    let ids:Vec<_>=cells(&f)?.into_iter().flatten().collect();let out=sort(&f,&raw,Scope::NodeSet(&ids),spec())?;
    let text=String::from_utf8(part(&bytes(&out)?,"Contents/section0.xml")?)?;
    assert!(text.contains(&(table::paragraph(902,"A&amp;B")+&table::paragraph(901,"Z-LONG"))));
    assert!(text.contains(&(table::paragraph(1002,"B-LONGER")+&table::paragraph(1001,"Y"))));
    assert_eq!(raw,before);let r=out.receipt();assert_eq!((r.groups.len(),r.changed_groups,r.changed_parts,r.moved_paragraphs),(2,2,1,4));
    assert!(r.groups.iter().all(|g|g.source_order==[1,0]));Ok(())
}
#[test]
fn groups_descending_equal_keys_keep_original_order_in_each_group()->TestResult{
    let raw=cell_package(&["A","B","A"],&["C","Z","C"])?;let f=fixture::forms(&raw,"groups-stable")?;
    let ids:Vec<_>=cells(&f)?.into_iter().flatten().collect();let out=sort(&f,&raw,Scope::NodeSet(&ids),Spec{direction:Direction::Descending,..spec()})?;
    assert!(out.receipt().groups.iter().all(|g|g.source_order==[1,0,2]));assert!(out.receipt().stable_equal_keys);Ok(())
}
#[test]
fn groups_discontinuous_selections_leave_unselected_slots_in_both_cells()->TestResult{
    let raw=cell_package(&["Z","KEEP-LEFT","A"],&["Y","KEEP-RIGHT","B"])?;let f=fixture::forms(&raw,"groups-slots")?;let ids=cells(&f)?;
    let chosen=[ids[1][2].clone(),ids[0][0].clone(),ids[1][0].clone(),ids[0][2].clone()];
    let out=sort(&f,&raw,Scope::NodeSet(&chosen),spec())?;let text=String::from_utf8(part(&bytes(&out)?,"Contents/section0.xml")?)?;
    assert!(text.contains(&(table::paragraph(903,"A")+&table::paragraph(902,"KEEP-LEFT")+&table::paragraph(901,"Z"))));
    assert!(text.contains(&(table::paragraph(1003,"B")+&table::paragraph(1002,"KEEP-RIGHT")+&table::paragraph(1001,"Y"))));Ok(())
}
#[test]
fn groups_singleton_is_retained_and_not_silently_dropped_from_receipt()->TestResult{
    let raw=cell_package(&["Z","A"],&["SINGLE"])?;let f=fixture::forms(&raw,"groups-single")?;
    let ids:Vec<_>=cells(&f)?.into_iter().flatten().collect();let out=sort(&f,&raw,Scope::NodeSet(&ids),spec())?;
    assert_eq!((out.receipt().selected_paragraphs,out.receipt().changed_groups,out.receipt().groups.len()),(3,1,2));
    let singleton=out.receipt().groups.iter().find(|g|g.entries.len()==1).ok_or("single")?;assert_eq!(singleton.source_order,[0]);assert_eq!(singleton.moved_paragraphs,0);Ok(())
}
#[test]
fn groups_all_singletons_and_already_sorted_groups_have_no_fake_changes()->TestResult{
    for(left,right,nomatch)in[(vec!["Z"],vec!["A"],true),(vec!["A","B"],vec!["C","D"],false)]{
        let raw=cell_package(&left,&right)?;let f=fixture::forms(&raw,"groups-noop")?;let ids:Vec<_>=cells(&f)?.into_iter().flatten().collect();
        let error=sort(&f,&raw,Scope::NodeSet(&ids),spec()).expect_err("no change");
        assert_eq!(error,E::Compile(if nomatch{Compile::NoMatches}else{Compile::NoChange}));
    }Ok(())
}
#[test]
fn groups_comparison_budget_is_global_not_reset_for_each_parent()->TestResult{
    let raw=cell_package(&["Z","A"],&["Y","B"])?;let f=fixture::forms(&raw,"groups-budget")?;let ids:Vec<_>=cells(&f)?.into_iter().flatten().collect();
    assert_eq!(sort(&f,&raw,Scope::NodeSet(&ids),Spec{max_comparison_bytes:1,..spec()}).expect_err("total budget"),E::ComparisonLimit);
    assert_eq!(sort(&f,&raw,Scope::NodeSet(&ids),Spec{max_comparison_bytes:2,..spec()})?.receipt().comparison_bytes,2);
    for maximum in [0,32*1024*1024+1]{assert_eq!(sort(&f,&raw,Scope::NodeSet(&ids),Spec{max_comparison_bytes:maximum,..spec()}).expect_err("invalid"),E::ComparisonLimit);}Ok(())
}
#[test]
fn groups_actual_two_parts_use_local_ids_and_preserve_all_nonsection_bytes()->TestResult{
    let raw=two_parts(&(p(1,"Z-LONG")+"<!--GAP-->"+&p(2,"A")),&(p(1,"Y")+&p(2,"B-LONG")))?;let f=fixture::forms(&raw,"groups-parts")?;
    let out=sort(&f,&raw,Scope::Document,spec())?;let next=bytes(&out)?;
    assert_eq!((out.receipt().groups.len(),out.receipt().changed_parts),(2,2));
    assert!(String::from_utf8(part(&next,"Contents/section0.xml")?)?.contains(&(p(2,"A")+"<!--GAP-->"+&p(1,"Z-LONG"))));
    assert!(String::from_utf8(part(&next,"Contents/section1.xml")?)?.contains(&(p(2,"B-LONG")+&p(1,"Y"))));
    for name in ["mimetype","version.xml","META-INF/container.xml","Contents/content.hpf","Contents/header.xml"]{assert_eq!(part(&raw,name)?,part(&next,name)?);}Ok(())
}
#[test]
fn groups_section_scope_does_not_include_other_section_and_binds_scope_digest()->TestResult{
    let raw=two_parts(&(p(1,"Z")+&p(2,"A")),&(p(1,"Y")+&p(2,"B")))?;let f=fixture::forms(&raw,"groups-section")?;
    let ids=[f.body_structure().graph().sections()[1].section_id.clone()];let out=sort(&f,&raw,Scope::Section(&ids),spec())?;
    assert_eq!(out.receipt().groups.len(),1);assert_eq!(part(&raw,"Contents/section0.xml")?,part(&bytes(&out)?,"Contents/section0.xml")?);
    assert_ne!(out.receipt().request_sha256,sort(&f,&raw,Scope::Document,spec())?.receipt().request_sha256);Ok(())
}
#[test]
fn groups_selection_requires_complete_windows_and_rejects_stale_index()->TestResult{
    let raw=two_parts(&(p(1,"ZZ")+&p(2,"AA")),&(p(1,"YY")+&p(2,"BB")))?;let f=fixture::forms(&raw,"groups-selection")?;
    let index=f.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?.inventory;assert_eq!(inv.blocks.len(),4);
    let mut start=Boundary{paragraph_handle:inv.blocks[0].paragraph_handle.clone(),block_index:0,normalized_scalar:0};
    let end=Boundary{paragraph_handle:inv.blocks[3].paragraph_handle.clone(),block_index:3,normalized_scalar:2};
    let out=sort(&f,&raw,Scope::Selection{index_sha256:inv.index.index_sha256,start:&start,end:&end},spec())?;assert_eq!(out.receipt().changed_groups,2);
    start.normalized_scalar=1;assert_eq!(sort(&f,&raw,Scope::Selection{index_sha256:inv.index.index_sha256,start:&start,end:&end},spec()).expect_err("partial"),E::IncompleteParagraphScope);
    assert!(matches!(sort(&f,&raw,Scope::Selection{index_sha256:[0;32],start:&start,end:&end},spec()),Err(E::Search(SourceSearchError::Scope))));Ok(())
}
#[test]
fn groups_current_whole_proof_and_fresh_original_are_required()->TestResult{
    let raw=two_parts(&(p(1,"Z")+&p(2,"A")),&(p(1,"Y")+&p(2,"B")))?;let f=fixture::forms(&raw,"groups-proof")?;
    let proof=f.reconstruct_source_for_verification(&raw)?;let out=proof.lower_selector_paragraph_sort_groups_candidate(&f,Scope::Document,Policy::default(),spec(),Default::default(),Default::default())?;
    assert_eq!(out.receipt(),sort(&f,&raw,Scope::Document,spec())?.receipt());
    let foreign=two_parts(&(p(1,"OTHER")+&p(2,"A")),&(p(1,"Y")+&p(2,"B")))?;let other=fixture::forms(&foreign,"groups-foreign")?;
    assert_eq!(sort(&f,&foreign,Scope::Document,spec()).expect_err("fresh"),E::Compile(Compile::Source));
    assert_eq!(proof.lower_selector_paragraph_sort_groups_candidate(&other,Scope::Document,Policy::default(),spec(),Default::default(),Default::default()).expect_err("proof"),E::Compile(Compile::Source));Ok(())
}
#[test]
fn groups_protected_unchanged_group_rejects_the_whole_candidate()->TestResult{
    let raw=two_parts(&(p(1,"Z")+&p(2,"A")),&(p(1,"A").replace("id='1'","id='1' paraTcId='1'")+&p(2,"B")))?;
    let f=fixture::forms(&raw,"groups-guard")?;assert_eq!(sort(&f,&raw,Scope::Document,spec()).expect_err("protected"),E::Compile(Compile::Protection));Ok(())
}
#[test]
fn groups_structured_ancestor_is_rejected_not_skipped_for_its_cells()->TestResult{
    let raw=cell_package(&["Z","A"],&["Y","B"])?;let f=fixture::forms(&raw,"groups-structured")?;
    assert!(matches!(sort(&f,&raw,Scope::Document,spec()),Err(E::StructuredKey)|Err(E::Compile(Compile::FieldContent))));
    let ids:Vec<_>=cells(&f)?.into_iter().flatten().collect();assert_eq!(sort(&f,&raw,Scope::NodeSet(&ids),spec())?.receipt().changed_groups,2);Ok(())
}
#[test]
fn groups_hidden_bodies_require_explicit_policy_for_every_selected_group()->TestResult{
    let mut controls=String::new();for(base,a,b)in[(10,"Z","A"),(20,"Y","B")]{controls.push_str(&format!("<hp:ctrl><hp:hiddenComment><hp:subList>{}{}</hp:subList></hp:hiddenComment></hp:ctrl>",p(base+1,a),p(base+2,b)));}
    let raw=fixture::package(&p(1,&format!("BODY</hp:t>{controls}<hp:t>TAIL")))?;let f=fixture::forms(&raw,"groups-review")?;
    let policy=Policy{include_hidden_explanations:true,include_memo_bodies:false};let index=f.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?.inventory;
    let mut ids=Vec::new();for key in["Z","A","Y","B"]{let query=hwpx_package::document_import::search::SourceSearchQuery{query:key,mode:hwpx_package::document_import::search::SourceSearchMode::Literal,case_sensitive:true,whole_word:true,max_results:1};
        let found=index.find(query,Scope::Document,policy)?;let handle=&found.result().matches()[0].paragraph_anchor.opaque_handle;
        ids.push(inv.nodes.iter().find(|n|&n.source_handle==handle).ok_or("node")?.node_id.clone());}
    assert_eq!(sort(&f,&raw,Scope::NodeSet(&ids),spec()).expect_err("excluded"),E::Compile(Compile::NoMatches));
    let out=f.lower_selector_paragraph_sort_groups_candidate(&raw,Scope::NodeSet(&ids),policy,spec(),Default::default(),Default::default())?;
    assert_eq!(out.receipt().changed_groups,2);let text=String::from_utf8(part(&bytes(&out)?,"Contents/section0.xml")?)?;
    for(base,a,b)in[(10,"Z","A"),(20,"Y","B")]{assert!(text.contains(&(p(base+2,b)+&p(base+1,a))));}Ok(())
}
#[test]
fn groups_receipt_redaction_determinism_and_original_single_group_api_are_preserved()->TestResult{
    let raw=cell_package(&["Z-PRIVATE","A-PRIVATE"],&["Y-PRIVATE","B-PRIVATE"])?;let f=fixture::forms(&raw,"groups-private")?;let ids:Vec<_>=cells(&f)?.into_iter().flatten().collect();
    let a=sort(&f,&raw,Scope::NodeSet(&ids),spec())?;let b=sort(&f,&raw,Scope::NodeSet(&ids),spec())?;assert_eq!(a.receipt(),b.receipt());assert_eq!(bytes(&a)?,bytes(&b)?);
    assert!(!format!("{a:?} {:?} {}",a.receipt(),serde_json::to_string(a.receipt())?).contains("PRIVATE"));
    assert!(!a.receipt().locale_native_full_protection_or_execution_authority);assert!(a.receipt().exact_subtrees_and_positional_gaps_read_back);
    assert_eq!(a.receipt().output_package_sha256,<[u8;32]>::from(Sha256::digest(bytes(&a)?)));
    assert_eq!(f.lower_selector_paragraph_sort_candidate(&raw,Scope::NodeSet(&ids),Policy::default(),spec(),Default::default(),Default::default()).expect_err("legacy"),E::ParentScope);Ok(())
}
#[test]
fn groups_source_response_writer_limits_and_invalid_selectors_remain_closed()->TestResult{
    let raw=two_parts(&(p(1,"Z")+&p(2,"A")),&(p(1,"Y")+&p(2,"B")))?;let f=fixture::forms(&raw,"groups-limits")?;
    for config in[SourceSearchLimitConfig{scalars:1,..Default::default()},SourceSearchLimitConfig{result_bytes:1,..Default::default()}]{
        let limits=SourceSearchLimits::new(config)?;assert!(f.lower_selector_paragraph_sort_groups_candidate(&raw,Scope::Document,Policy::default(),spec(),limits,Default::default()).is_err());}
    let writer=WriterLimits::new(WriterLimitConfig{max_output_bytes:1,..Default::default()})?;
    assert_eq!(f.lower_selector_paragraph_sort_groups_candidate(&raw,Scope::Document,Policy::default(),spec(),Default::default(),writer).expect_err("writer"),E::Compile(Compile::Writer));
    for ids in[vec![],vec![LogicalId::parse("foreign")?]]{assert!(matches!(sort(&f,&raw,Scope::NodeSet(&ids),spec()),Err(E::Search(SourceSearchError::Scope))));}Ok(())
}
#[test]
fn groups_128_paragraphs_share_bounded_work_and_one_output_package()->TestResult{
    let first=(0..64).rev().map(|i|p(i+1,&format!("L-{i:03}"))).collect::<String>();let second=(0..64).rev().map(|i|p(i+1,&format!("R-{i:03}"))).collect::<String>();
    let raw=two_parts(&first,&second)?;let f=fixture::forms(&raw,"groups-128")?;let out=sort(&f,&raw,Scope::Document,spec())?;let r=out.receipt();
    assert_eq!((r.selected_paragraphs,r.moved_paragraphs,r.changed_groups,r.changed_parts),(128,128,2,2));
    assert_eq!(r.comparison_bytes,r.groups.iter().map(|g|g.comparison_bytes).sum::<usize>());assert!(r.groups.iter().all(|g|g.source_order==(0..64).rev().collect::<Vec<_>>()));Ok(())
}
#[path="support/paragraph_sort_groups_splices.rs"]mod splices_v1;
