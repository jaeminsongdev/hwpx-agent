use hwpx_package::{BoundedZipReader,PreservingXmlDocument,TextAtom,WriterLimits,WriterLimitConfig,
    document_import::{ImportedSourcePackage,forms::ImportedDocumentForms,search::{SourceSearchLimits,SourceSearchLimitConfig as Config,
        SourceSearchError as Search,selector::{SourceIndexScopeSelector as Scope,SourceIndexBoundary as Boundary},
        reviews::{SourceReviewTextPolicy as Body,SourceTextRegion as Region},inspection::SourceControlKind as Kind,
        replacement::{SourceLiteralReplacementError as E,atoms::controls::{SourceControlReplacementCandidate as Candidate,
            SourceControlReplacementError as C,SOURCE_CONTROL_REPLACEMENT_PROFILE}}}}};
use domain_ir::DocumentId;
use sha2::{Digest as _,Sha256};
use std::{error::Error,io::{Cursor,Write}};
use zip::{ZipWriter,CompressionMethod,write::SimpleFileOptions};
#[allow(dead_code)] #[path="support/search_definition_fixture.rs"] mod fixture;
#[allow(dead_code)] #[path="support/review_scope_fixture.rs"] mod review;
#[allow(dead_code)] #[path="support/document_import_review_assembly_fixture.rs"] mod assembly;
#[allow(dead_code)] #[path="support/review_cell_output_fixture.rs"] mod table;
type TestResult=Result<(),Box<dyn Error>>;
const TAB:&str="<hp:tab width='1' leader='0' type='0'/>";
fn text(value:&str)->TextAtom{TextAtom::Text(value.to_owned())}
fn tab()->TextAtom{TextAtom::Tab{width:1,leader:0,tab_type:0}}
fn p(id:u32,text:&str)->String{format!("<hp:p id='{id}' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'><hp:t charStyleIDRef='0'>{text}</hp:t></hp:run></hp:p>")}
fn all()->Body{Body{include_hidden_explanations:true,include_memo_bodies:true}}
fn forms(bytes:&[u8])->Result<ImportedDocumentForms,Box<dyn Error>>{Ok(ImportedDocumentForms::import(ImportedSourcePackage::import(bytes,DocumentId::parse("control-replacement")?,Sha256::digest(bytes).into(),Default::default())?)?)}
fn replace(f:&ImportedDocumentForms,bytes:&[u8],scope:Scope<'_>,body:Body,kind:Kind,max:usize,output:&[TextAtom])->Result<Candidate,C>{
    f.lower_review_selector_control_candidate(bytes,scope,body,kind,max,output,Default::default(),Default::default())}
fn section(bytes:&[u8])->Result<String,Box<dyn Error>>{let mut r=BoundedZipReader::open(Cursor::new(bytes),Default::default())?;let i=r.entries().iter().position(|e|e.path.as_str()=="Contents/section0.xml").ok_or("section")?;Ok(String::from_utf8(r.read_entry(i)?)?)}
fn output(raw:&[u8],c:&Candidate)->Result<Vec<u8>,Box<dyn Error>>{let bytes=c.with_verified_bytes(<[u8]>::to_vec)?;
    let mut a=BoundedZipReader::open(Cursor::new(raw),Default::default())?;let mut b=BoundedZipReader::open(Cursor::new(&bytes),Default::default())?;assert_eq!(a.entries().len(),b.entries().len());
    for i in 0..a.entries().len(){let path=a.entries()[i].path.clone();if c.receipt().changed_parts==2&&path.as_str()=="Contents/section1.xml"{continue;}if path.as_str()=="Contents/section0.xml"{continue;}
        let j=b.entries().iter().position(|e|e.path==path).ok_or("part")?;assert_eq!(a.read_entry(i)?,b.read_entry(j)?);}
    let r=c.receipt();assert_eq!(r.profile,SOURCE_CONTROL_REPLACEMENT_PROFILE);assert_eq!(r.changed_controls,r.changes.len());assert!(r.selected_controls>=r.changed_controls);
    assert!(r.whole_atomic_control_selection_verified&&r.original_text_run_shells_styles_references_and_outside_control_bytes_preserved&&r.output_spans_and_exact_outside_edits_verified);
    assert!(!r.full_control_contract_native_service_or_execution_authority);Ok(bytes)}
fn exact(raw:&[u8],c:&Candidate,old:&str,new:&str)->TestResult{assert_eq!(section(&output(raw,c)?)?,section(raw)?.replace(old,new));Ok(())}
fn review_body()->String{review::body().replace("BODY K K",&format!("BODY{TAB} K K")).replace("HIDDEN K K",&format!("HIDDEN{TAB} K K")).replace("MEMO K K",&format!("MEMO{TAB} K K"))}
fn two_parts()->Result<Vec<u8>,Box<dyn Error>>{
    let bytes=fixture::package(&p(1,&format!("A{TAB}B")))?;let mut r=BoundedZipReader::open(Cursor::new(&bytes),Default::default())?;
    let names:Vec<_>=r.entries().iter().map(|e|e.path.as_str().to_owned()).collect();let mut w=ZipWriter::new(Cursor::new(Vec::new()));
    for(i,name)in names.iter().enumerate(){let bytes=r.read_entry(i)?;w.start_file(name,SimpleFileOptions::default().compression_method(CompressionMethod::Stored))?;
        if name=="Contents/content.hpf"{let opf=String::from_utf8(bytes)?.replace("</o:manifest>","<o:item id='s2' href='Contents/section1.xml' media-type='application/xml'/></o:manifest>").replace("</o:spine>","<o:itemref idref='s2'/></o:spine>");w.write_all(opf.as_bytes())?;}else{w.write_all(&bytes)?;}}
    w.start_file("Contents/section1.xml",SimpleFileOptions::default().compression_method(CompressionMethod::Stored))?;
    write!(w,"<hs:sec xmlns:hs='http://www.hancom.co.kr/hwpml/2011/section' xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph'>{}</hs:sec>",p(1,&format!("C{TAB}D")))?;Ok(w.finish()?.into_inner())
}
#[test]
fn control_source_tab_to_arbitrary_unicode_text_preserves_original_entities_styles_and_zip_parts()->TestResult{
    let input=format!("&#x1F600;A{TAB}B&#38;");let raw=fixture::package(&p(1,&input))?;let f=forms(&raw)?;let c=replace(&f,&raw,Scope::Document,all(),Kind::Tab,100,&[text("한글😀&<hp:tab/>e\u{301}")])?;
    exact(&raw,&c,&input,"&#x1F600;A한글😀&amp;&lt;hp:tab/&gt;e\u{301}B&#38;")?;assert_eq!(c.receipt().span_changes[0].changed_original_text_atoms,0);Ok(())
}
#[test]
fn control_source_linebreak_to_mixed_typed_atoms_and_adjacent_texts_read_back_exactly()->TestResult{
    let raw=fixture::package(&(p(1,"A<hp:lineBreak/>B")+&p(2,"C<hp:lineBreak/>D")))?;let f=forms(&raw)?;
    let c=replace(&f,&raw,Scope::Document,all(),Kind::LineBreak,2,&[text("X"),text("Y"),tab(),TextAtom::LineBreak,text("Z")])?;
    exact(&raw,&c,"<hp:lineBreak/>","XY<hp:tab width=\"1\" leader=\"0\" type=\"0\"/><hp:lineBreak/>Z")?;assert_eq!(c.receipt().changed_controls,2);Ok(())
}
#[test]
fn control_source_removes_only_selected_kind_and_never_existing_text_or_other_control()->TestResult{
    let input=format!("A{TAB}B<hp:lineBreak> </hp:lineBreak>C{TAB}D");let raw=fixture::package(&p(1,&input))?;let f=forms(&raw)?;
    let c=replace(&f,&raw,Scope::Document,all(),Kind::Tab,2,&[])?;exact(&raw,&c,&input,&input.replace(TAB,""))?;assert_eq!(c.receipt().span_changes[0].preserved_controls,1);Ok(())
}
#[test]
fn control_source_semantic_noops_keep_paired_original_lexemes_while_other_controls_change()->TestResult{
    let first="<hp:tab width='1' leader='0' type='0'> </hp:tab>";let second="<hp:tab width='2' leader='0' type='0'/>";
    let raw=fixture::package(&p(1,&format!("A{first}B{second}C")))?;let f=forms(&raw)?;let c=replace(&f,&raw,Scope::Document,all(),Kind::Tab,2,&[tab()])?;
    exact(&raw,&c,second,"<hp:tab width=\"1\" leader=\"0\" type=\"0\"/>")?;assert_eq!(c.receipt().selected_controls,2);assert_eq!(c.receipt().changed_controls,1);assert_eq!(c.receipt().changes[0].original_atom,3);Ok(())
}
#[test]
fn control_source_four_selectors_keep_exact_half_open_atomic_control_coverage()->TestResult{
    let raw=fixture::package(&(p(1,&format!("A{TAB}B"))+&p(2,&format!("C{TAB}D"))))?;let f=forms(&raw)?;
    let inv=f.source_review_scope_index(&raw,Default::default())?.scope_inventory()?;let b=&inv.inventory.blocks[0];let ids=[inv.inventory.nodes.iter().find(|n|n.source_handle==b.paragraph_handle).ok_or("node")?.node_id.clone()];
    let start=Boundary{paragraph_handle:b.paragraph_handle.clone(),block_index:0,normalized_scalar:1};let end=Boundary{normalized_scalar:2,..start.clone()};
    for(scope,n)in[(Scope::Document,2),(Scope::Section(&inv.inventory.section_ids),2),(Scope::NodeSet(&ids),1),(Scope::Selection{index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},1)]{
        let c=replace(&f,&raw,scope,all(),Kind::Tab,2,&[text("X")])?;let out=section(&output(&raw,&c)?)?;assert!(out.contains("AXB"));assert_eq!(out.contains(&format!("C{TAB}D")),n==1);assert_eq!(c.receipt().changed_controls,n);}Ok(())
}
#[test]
fn control_source_empty_and_neighbor_only_selection_never_widens_to_control()->TestResult{
    let raw=fixture::package(&p(1,&format!("A{TAB}B")))?;let f=forms(&raw)?;let inv=f.source_review_scope_index(&raw,Default::default())?.scope_inventory()?;let b=&inv.inventory.blocks[0];
    for(a,z)in[(0,1),(2,3),(1,1),(2,2)]{let start=Boundary{paragraph_handle:b.paragraph_handle.clone(),block_index:0,normalized_scalar:a};let end=Boundary{normalized_scalar:z,..start.clone()};
        assert!(matches!(replace(&f,&raw,Scope::Selection{index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},all(),Kind::Tab,1,&[text("X")]),Err(C::Output(E::NoMatches))));}Ok(())
}
#[test]
fn control_source_nfc_reordered_endpoint_is_rejected_instead_of_guessed()->TestResult{
    let raw=fixture::package(&p(1,&format!("x\u{315}\u{300}{TAB}Z")))?;let f=forms(&raw)?;let inv=f.source_review_scope_index(&raw,Default::default())?.scope_inventory()?;let b=&inv.inventory.blocks[0];
    let mut start=Boundary{paragraph_handle:b.paragraph_handle.clone(),block_index:0,normalized_scalar:2};let end=Boundary{normalized_scalar:4,..start.clone()};
    assert!(matches!(replace(&f,&raw,Scope::Selection{index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},all(),Kind::Tab,1,&[text("X")]),Err(C::Output(E::Search(Search::Scope)))));
    start.normalized_scalar=3;let c=replace(&f,&raw,Scope::Selection{index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},all(),Kind::Tab,1,&[text("X")])?;exact(&raw,&c,TAB,"X")?;Ok(())
}
#[test]
fn control_source_review_exclusions_precede_caps_and_preserve_metadata_and_frozen_cache()->TestResult{
    let body=review_body();let raw=fixture::package(&body)?;let f=forms(&raw)?;
    for(h,m,n)in[(false,false,1),(true,false,2),(false,true,2),(true,true,3)]{let c=replace(&f,&raw,Scope::Document,Body{include_hidden_explanations:h,include_memo_bodies:m},Kind::Tab,n,&[text("Q")])?;
        let mut expected=body.replace(&format!("BODY{TAB}"),"BODYQ");if h{expected=expected.replace(&format!("HIDDEN{TAB}"),"HIDDENQ");}if m{expected=expected.replace(&format!("MEMO{TAB}"),"MEMOQ");}
        exact(&raw,&c,&body,&expected)?;assert_eq!(c.receipt().selected_controls,n);}Ok(())
}
#[test]
fn control_source_review_node_selection_uses_real_supplemental_node_and_explicit_policy()->TestResult{
    let raw=fixture::package(&review_body())?;let f=forms(&raw)?;let inv=f.source_review_scope_index(&raw,Default::default())?.scope_inventory()?;let i=inv.block_regions.iter().position(|r|*r==Region::MemoBody).ok_or("memo")?;
    let ids=[inv.inventory.nodes.iter().find(|n|n.source_handle==inv.inventory.blocks[i].paragraph_handle).ok_or("node")?.node_id.clone()];
    let c=replace(&f,&raw,Scope::NodeSet(&ids),all(),Kind::Tab,1,&[text("Q")])?;exact(&raw,&c,&format!("MEMO{TAB}"),"MEMOQ")?;
    assert!(matches!(replace(&f,&raw,Scope::NodeSet(&ids),Body::default(),Kind::Tab,1,&[text("Q")]),Err(C::Output(E::NoMatches))));Ok(())
}
#[test]
fn control_source_other_observed_kinds_are_unavailable_not_raw_xml_or_implicit_fallback()->TestResult{
    let raw=fixture::package(&p(1,&format!("A{TAB}B")))?;let f=forms(&raw)?;
    for kind in[Kind::Table,Kind::FieldBegin,Kind::FieldEnd,Kind::Footnote,Kind::Endnote,Kind::Bookmark,Kind::Picture,Kind::NonbreakingSpace,Kind::UnknownCharacter]{
        assert!(matches!(replace(&f,&raw,Scope::Document,all(),kind,1,&[text("X")]),Err(C::UnsupportedKind)));}Ok(())
}
#[test]
fn control_source_foreign_proof_and_changed_original_reject_before_candidate()->TestResult{
    let raw=fixture::package(&p(1,&format!("A{TAB}B")))?;let f=forms(&raw)?;let other=forms(&raw)?;let proof=f.reconstruct_source_for_verification(&raw)?;
    assert!(matches!(proof.lower_review_selector_control_candidate(&other,Scope::Document,all(),Kind::Tab,1,&[text("X")],Default::default(),Default::default()),Err(C::Output(E::Source))));
    let changed=fixture::package(&p(1,&format!("C{TAB}D")))?;assert!(matches!(replace(&f,&changed,Scope::Document,all(),Kind::Tab,1,&[text("X")]),Err(C::Output(E::Source))));Ok(())
}
#[test]
fn control_source_tracked_noops_are_rejected_before_discarding_unchanged_controls()->TestResult{
    for marker in["charTcId='1'","paraTcId='1'"]{let body=p(1,&format!("A{TAB}B"));let body=if marker.starts_with("char"){body.replace("charPrIDRef='0'",&format!("charPrIDRef='0' {marker}"))}else{body.replace("paraPrIDRef='0'",&format!("paraPrIDRef='0' {marker}"))};
        let raw=fixture::package(&body)?;let f=forms(&raw)?;assert!(matches!(replace(&f,&raw,Scope::Document,all(),Kind::Tab,1,&[tab()]),Err(C::Output(E::Protection))));}Ok(())
}
#[test]
fn control_source_locked_table_controls_reject_but_unselected_protected_content_is_exact()->TestResult{
    let tbl=table::table(300).replace("lock='0'","lock='1'").replace("CELL-OLD",&format!("CELL-OLD{TAB}"));let body=p(1,&format!("A{TAB}B"))+&format!("<hp:p id='2'><hp:run>{tbl}</hp:run></hp:p>");let raw=fixture::package(&body)?;let f=forms(&raw)?;
    assert!(matches!(replace(&f,&raw,Scope::Document,all(),Kind::Tab,2,&[text("X")]),Err(C::Output(E::Protection))));
    let inv=f.source_review_scope_index(&raw,Default::default())?.scope_inventory()?;let ids=[inv.inventory.nodes.iter().find(|n|n.source_handle==inv.inventory.blocks[0].paragraph_handle).ok_or("node")?.node_id.clone()];
    let c=replace(&f,&raw,Scope::NodeSet(&ids),all(),Kind::Tab,1,&[text("X")])?;exact(&raw,&c,&format!("A{TAB}B"),"AXB")?;Ok(())
}
#[test]
fn control_source_field_cache_is_blocked_even_if_control_output_is_a_noop()->TestResult{
    let raw=fixture::package(&review::body().replace("CACHE FROZEN",&format!("CACHE{TAB} FROZEN")))?;let f=forms(&raw)?;
    assert!(matches!(replace(&f,&raw,Scope::Document,all(),Kind::Tab,1,&[tab()]),Err(C::Output(E::FieldContent))));Ok(())
}
#[test]
fn control_source_observed_tab_in_opaque_parent_does_not_gain_write_authority()->TestResult{
    let raw=fixture::package(&p(1,&format!("A{TAB}<hp:nbSpace/>B")))?;let f=forms(&raw)?;
    assert!(matches!(replace(&f,&raw,Scope::Document,all(),Kind::Tab,1,&[text("X")]),Err(C::Output(E::Selection))));Ok(())
}
#[test]
fn control_source_raw_control_empty_text_noncharacter_and_excessive_outputs_are_rejected()->TestResult{
    let raw=fixture::package(&p(1,&format!("A{TAB}B")))?;let f=forms(&raw)?;
    for bad in[vec![text("")],vec![text("\t")],vec![text("\r")],vec![text("\n")],vec![text("\u{ffff}")]]{assert!(matches!(replace(&f,&raw,Scope::Document,all(),Kind::Tab,1,&bad),Err(C::Output(E::Value))));}
    for bad in[vec![TextAtom::LineBreak;4097],vec![text(&"x".repeat(1024*1024+1))]]{assert!(matches!(replace(&f,&raw,Scope::Document,all(),Kind::Tab,1,&bad),Err(C::Output(E::Limit))));}Ok(())
}
#[test]
fn control_source_no_matches_nochange_and_match_caps_remain_distinct()->TestResult{
    let raw=fixture::package(&p(1,&format!("A{TAB}B{TAB}C")))?;let f=forms(&raw)?;
    assert!(matches!(replace(&f,&raw,Scope::Document,all(),Kind::LineBreak,2,&[text("X")]),Err(C::Output(E::NoMatches))));
    assert!(matches!(replace(&f,&raw,Scope::Document,all(),Kind::Tab,2,&[tab()]),Err(C::Output(E::NoChange))));
    for max in[0,1,10001]{assert!(matches!(replace(&f,&raw,Scope::Document,all(),Kind::Tab,max,&[text("X")]),Err(C::Output(E::Search(Search::Limit)))));}Ok(())
}
#[test]
fn control_source_response_work_and_writer_limits_never_yield_partial_candidates()->TestResult{
    let raw=fixture::package(&p(1,&format!("A{TAB}B")))?;let f=forms(&raw)?;
    assert!(f.lower_review_selector_control_candidate(&raw,Scope::Document,all(),Kind::Tab,1,&[text("X")],SourceSearchLimits::new(Config{result_bytes:1,..Default::default()})?,Default::default()).is_err());
    assert!(f.lower_review_selector_control_candidate(&raw,Scope::Document,all(),Kind::Tab,1,&[text("X")],SourceSearchLimits::new(Config{decomposed_scalars:1,..Default::default()})?,Default::default()).is_err());
    assert!(matches!(f.lower_review_selector_control_candidate(&raw,Scope::Document,all(),Kind::Tab,1,&[text("X")],Default::default(),WriterLimits::new(WriterLimitConfig{max_output_bytes:1,..Default::default()})?),Err(C::Output(E::Writer))));Ok(())
}
#[test]
fn control_source_repeated_large_output_is_bounded_before_per_control_clones_and_writer()->TestResult{
    let raw=fixture::package(&p(1,&TAB.repeat(8)))?;let f=forms(&raw)?;let digest=Sha256::digest(&raw);
    assert!(matches!(replace(&f,&raw,Scope::Document,all(),Kind::Tab,8,&[text(&"&".repeat(128*1024))]),Err(C::Output(E::Limit))));
    assert_eq!(Sha256::digest(&raw),digest);Ok(())
}
#[test]
fn control_source_many_controls_share_one_parent_map_protection_scan_and_ordered_receipt()->TestResult{
    let input=format!("A{}B",TAB.repeat(2000));let raw=fixture::package(&p(1,&input))?;let f=forms(&raw)?;let c=replace(&f,&raw,Scope::Document,all(),Kind::Tab,2000,&[text("X")])?;
    exact(&raw,&c,&input,&format!("A{}B","X".repeat(2000)))?;let r=c.receipt();assert_eq!(r.span_changes.len(),1);assert_eq!(r.changed_controls,2000);
    assert!(r.changes.iter().enumerate().all(|(i,c)|c.original_atom==i as u32+1));let xml=PreservingXmlDocument::parse(section(&raw)?.as_bytes())?;
    assert_eq!(r.observed_protection_element_visits,xml.elements().len()*3);Ok(())
}
#[test]
fn control_source_alias_default_namespace_and_source_lexemes_are_retained()->TestResult{
    for(prefix,decl)in[("q:"," xmlns:q='http://www.hancom.co.kr/hwpml/2011/paragraph'"),(""," xmlns='http://www.hancom.co.kr/hwpml/2011/paragraph'")]{
        let body=p(1,&format!("A{TAB}B&#38;")).replace("hp:",prefix).replacen(&format!("<{prefix}p "),&format!("<{prefix}p{decl} "),1);let raw=fixture::package(&body)?;let f=forms(&raw)?;
        let c=replace(&f,&raw,Scope::Document,all(),Kind::Tab,1,&[TextAtom::LineBreak])?;
        exact(&raw,&c,&format!("<{prefix}tab width='1' leader='0' type='0'/>"),&format!("<{prefix}lineBreak/>"))?;}Ok(())
}
#[test]
fn control_source_two_parts_with_colliding_local_ids_keep_actual_anchors_and_spine_order()->TestResult{
    let raw=two_parts()?;let f=forms(&raw)?;let c=replace(&f,&raw,Scope::Document,all(),Kind::Tab,2,&[text("X")])?;
    let bytes=output(&raw,&c)?;assert_eq!(c.receipt().changed_parts,2);let expected=f.source_review_scope_index(&raw,Default::default())?.find_control(Scope::Document,all(),Kind::Tab,2)?;
    assert_eq!(c.receipt().changes.iter().map(|c|&c.source_control_anchor).collect::<Vec<_>>(),expected.controls().iter().map(|c|&c.control_anchor).collect::<Vec<_>>());
    let mut a=BoundedZipReader::open(Cursor::new(&raw),Default::default())?;let mut b=BoundedZipReader::open(Cursor::new(&bytes),Default::default())?;
    for part in["Contents/section0.xml","Contents/section1.xml"]{let i=a.entries().iter().position(|e|e.path.as_str()==part).ok_or("part")?;let j=b.entries().iter().position(|e|e.path.as_str()==part).ok_or("part")?;
        assert_eq!(String::from_utf8(b.read_entry(j)?)?,String::from_utf8(a.read_entry(i)?)?.replace(TAB,"X"));}Ok(())
}
#[test]
fn control_source_stale_index_and_invalid_scope_never_produce_candidate()->TestResult{
    let raw=fixture::package(&p(1,&format!("A{TAB}B")))?;let f=forms(&raw)?;let inv=f.source_review_scope_index(&raw,Default::default())?.scope_inventory()?;let b=&inv.inventory.blocks[0];
    let start=Boundary{paragraph_handle:b.paragraph_handle.clone(),block_index:0,normalized_scalar:1};let end=Boundary{normalized_scalar:2,..start.clone()};
    assert!(matches!(replace(&f,&raw,Scope::Selection{index_sha256:[0;32],start:&start,end:&end},all(),Kind::Tab,1,&[text("X")]),Err(C::Output(E::Search(Search::Scope)))));
    assert!(matches!(replace(&f,&raw,Scope::NodeSet(&[]),all(),Kind::Tab,1,&[text("X")]),Err(C::Output(E::Search(Search::Scope)))));Ok(())
}
#[test]
fn control_source_request_hash_binds_replacement_vector_scope_and_review_without_text_disclosure()->TestResult{
    let raw=fixture::package(&p(1,&format!("PRIVATE-SOURCE{TAB}B")))?;let f=forms(&raw)?;let before=Sha256::digest(&raw);
    let c=replace(&f,&raw,Scope::Document,all(),Kind::Tab,1,&[text("PRIVATE-OUTPUT")])?;
    for s in[serde_json::to_string(c.receipt())?,format!("{c:?}{:?}",c.receipt())]{assert!(!s.contains("PRIVATE-SOURCE"));assert!(!s.contains("PRIVATE-OUTPUT"));}
    let other=replace(&f,&raw,Scope::Document,Body::default(),Kind::Tab,1,&[text("PRIVATE-OUTPUT")])?;assert_ne!(c.receipt().request_sha256,other.receipt().request_sha256);
    let a=replace(&f,&raw,Scope::Document,all(),Kind::Tab,1,&[text("a"),text("b")])?;let b=replace(&f,&raw,Scope::Document,all(),Kind::Tab,1,&[text("ab")])?;
    assert_ne!(a.receipt().replacement_sha256,b.receipt().replacement_sha256);assert_eq!(a.receipt().output_package_sha256,b.receipt().output_package_sha256);assert_eq!(Sha256::digest(&raw),before);Ok(())
}
