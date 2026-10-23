use hwpx_package::{BoundedZipReader,PackageLimits,WriterLimits,WriterLimitConfig,document_import::{forms::ImportedDocumentForms,
    search::{SourceSearchLimits,SourceSearchLimitConfig,SourceSearchError,selector::{SourceIndexScopeSelector as Scope,SourceIndexBoundary as Boundary},
        reviews::SourceReviewTextPolicy as Policy,replacement::{SourceLiteralReplacementError as Compile,
            atoms::sort::{SourceParagraphSortSpec as Spec,SourceParagraphSortDirection as Direction,SourceParagraphSortComparison as Comparison,
                SourceParagraphSortError as E,SourceParagraphSortCandidate as Candidate}}}}};
use domain_ir::{LogicalId,Node};
use sha2::{Digest as _,Sha256};
use std::{error::Error,io::Cursor};
#[allow(dead_code)] #[path="support/document_import_field_fixture.rs"]mod fixture;
#[allow(dead_code)] #[path="support/document_import_review_assembly_fixture.rs"]mod assembly;
#[allow(dead_code)] #[path="support/review_cell_output_fixture.rs"]mod table;
type TestResult=Result<(),Box<dyn Error>>;
fn p(id:usize,key:&str)->String {format!("<hp:p id='{id}'><hp:run><hp:t>{key}</hp:t></hp:run></hp:p>")}
fn spec()->Spec {Spec {direction:Direction::Ascending,comparison:Comparison::NfcUnicodeScalarLexicographic,max_comparison_bytes:1024*1024}}
fn sort(f:&ImportedDocumentForms,b:&[u8],scope:Scope<'_>,s:Spec)->Result<Candidate,E> {
    f.lower_selector_paragraph_sort_candidate(b,scope,Policy::default(),s,Default::default(),Default::default())
}
fn section(b:&[u8])->Result<String,Box<dyn Error>> {let mut zip=BoundedZipReader::open(Cursor::new(b),PackageLimits::default())?;
    let i=zip.entries().iter().find(|e|e.path.as_str()=="Contents/section0.xml").ok_or("section")?.index;Ok(String::from_utf8(zip.read_entry(i)?)?)}
fn bytes(c:&Candidate)->Result<Vec<u8>,Box<dyn Error>> {Ok(c.with_verified_bytes(<[u8]>::to_vec)?)}

#[test]
fn sort_actual_source_unequal_subtrees_entities_and_all_other_parts_are_preserved()->TestResult {
    let a=p(1,"Z-LONG-PRIVATE");let b=p(2,"A&#38;B");let raw=fixture::package(&(a.clone()+"<!--POSITION-->"+&b))?;
    let before=raw.clone();let f=fixture::forms(&raw,"sort-exact")?;let out=sort(&f,&raw,Scope::Document,spec())?;let next=bytes(&out)?;
    assert!(section(&next)?.contains(&(b+"<!--POSITION-->"+&a)));assert_eq!(raw,before);
    assert_eq!(out.receipt().source_order,vec![1,0]);assert_eq!(out.receipt().moved_paragraphs,2);
    assert_eq!(out.receipt().output_package_sha256,<[u8;32]>::from(Sha256::digest(&next)));
    let mut old=BoundedZipReader::open(Cursor::new(&raw),PackageLimits::default())?;let mut new=BoundedZipReader::open(Cursor::new(&next),PackageLimits::default())?;
    for i in 0..old.entries().len(){let path=old.entries()[i].path.clone();if path.as_str()=="Contents/section0.xml"{continue;}
        let j=new.entries().iter().find(|e|e.path==path).ok_or("part")?.index;assert_eq!(old.read_entry(i)?,new.read_entry(j)?);}Ok(())
}

#[test]
fn sort_descending_retains_original_order_of_equal_keys()->TestResult {
    let raw=fixture::package(&(p(1,"A")+&p(2,"B")+&p(3,"A")))?;let f=fixture::forms(&raw,"sort-desc")?;
    let out=sort(&f,&raw,Scope::Document,Spec{direction:Direction::Descending,..spec()})?;
    assert_eq!(out.receipt().source_order,vec![1,0,2]);assert!(out.receipt().stable_equal_keys);Ok(())
}

#[test]
fn sort_nfc_equivalent_jamo_keys_do_not_rewrite_original_text()->TestResult {
    let a=p(1,"가");let b=p(2,"가");let c=p(3,"Z");let raw=fixture::package(&(a.clone()+&b+&c))?;let f=fixture::forms(&raw,"sort-nfc")?;
    let out=sort(&f,&raw,Scope::Document,spec())?;assert_eq!(out.receipt().source_order,vec![2,0,1]);
    assert_eq!(out.receipt().entries[0].normalized_key_sha256,out.receipt().entries[1].normalized_key_sha256);
    assert!(section(&bytes(&out)?)?.contains(&(c+&a+&b)));Ok(())
}

#[test]
fn sort_run_boundaries_tab_linebreak_and_empty_paragraph_are_kept()->TestResult {
    let a="<hp:p id='1'><hp:run><hp:t>B<hp:tab width='8000' leader='0' type='0'/><hp:lineBreak/></hp:t></hp:run><hp:run><hp:t>TAIL</hp:t></hp:run></hp:p>";
    assert!(matches!(hwpx_package::TextFlowReader::read(b"<hp:p xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph' id='2'/>",Default::default()),Err(hwpx_package::TextFlowError::UnsupportedShape)));
    let b=p(2,"");let raw=fixture::package(&(a.to_owned()+&b))?;let f=fixture::forms(&raw,"sort-controls")?;
    let out=sort(&f,&raw,Scope::Document,spec())?;assert!(section(&bytes(&out)?)?.contains(&(b+a)));Ok(())
}

#[test]
fn sort_discontinuous_node_set_keeps_unselected_sibling_in_its_slot()->TestResult {
    let a=p(1,"Z");let gap=p(2,"MIDDLE");let c=p(3,"A");let raw=fixture::package(&(a.clone()+&gap+&c))?;let f=fixture::forms(&raw,"sort-nodes")?;
    let nodes=&f.body_structure().graph().sections()[0].body.children;let ids=[nodes[2].common().node_id.clone(),nodes[0].common().node_id.clone()];
    let out=sort(&f,&raw,Scope::NodeSet(&ids),spec())?;assert!(section(&bytes(&out)?)?.contains(&(c+&gap+&a)));assert_eq!(out.receipt().scope.kind,"node_set");Ok(())
}

#[test]
fn sort_section_scope_is_bound_to_actual_section_and_request_digest()->TestResult {
    let raw=fixture::package(&(p(1,"Z")+&p(2,"A")))?;let f=fixture::forms(&raw,"sort-section")?;let id=f.body_structure().graph().sections()[0].section_id.clone();
    let a=sort(&f,&raw,Scope::Section(&[id]),spec())?;let b=sort(&f,&raw,Scope::Document,spec())?;
    assert_eq!(a.receipt().source_order,b.receipt().source_order);assert_ne!(a.receipt().request_sha256,b.receipt().request_sha256);Ok(())
}

#[test]
fn sort_selection_requires_complete_original_paragraph_windows()->TestResult {
    let raw=fixture::package(&(p(1,"ZZ")+&p(2,"AA")))?;let f=fixture::forms(&raw,"sort-selection")?;
    let index=f.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?.inventory;
    let mut start=Boundary{paragraph_handle:inv.blocks[0].paragraph_handle.clone(),block_index:0,normalized_scalar:0};
    let end=Boundary{paragraph_handle:inv.blocks[1].paragraph_handle.clone(),block_index:1,normalized_scalar:2};
    let scope=Scope::Selection{index_sha256:inv.index.index_sha256,start:&start,end:&end};assert_eq!(sort(&f,&raw,scope,spec())?.receipt().source_order,vec![1,0]);
    start.normalized_scalar=1;let scope=Scope::Selection{index_sha256:inv.index.index_sha256,start:&start,end:&end};
    assert!(matches!(sort(&f,&raw,scope,spec()),Err(E::IncompleteParagraphScope)));Ok(())
}

#[test]
fn sort_stale_selection_and_invalid_node_ids_fail_without_output()->TestResult {
    let raw=fixture::package(&(p(1,"Z")+&p(2,"A")))?;let f=fixture::forms(&raw,"sort-invalid")?;
    let index=f.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?.inventory;
    let start=Boundary{paragraph_handle:inv.blocks[0].paragraph_handle.clone(),block_index:0,normalized_scalar:0};
    let end=Boundary{paragraph_handle:inv.blocks[1].paragraph_handle.clone(),block_index:1,normalized_scalar:1};
    assert!(matches!(sort(&f,&raw,Scope::Selection{index_sha256:[0;32],start:&start,end:&end},spec()),Err(E::Search(SourceSearchError::Scope))));
    let node=f.body_structure().graph().sections()[0].body.children[0].common().node_id.clone();
    for ids in [vec![],vec![node.clone(),node],vec![LogicalId::parse("foreign")?]] {assert!(matches!(sort(&f,&raw,Scope::NodeSet(&ids),spec()),Err(E::Search(SourceSearchError::Scope))));}Ok(())
}

#[test]
fn sort_whole_form_proof_reuse_and_fresh_source_rejection_are_preserved()->TestResult {
    let raw=fixture::package(&(p(1,"Z")+&p(2,"A")))?;let f=fixture::forms(&raw,"sort-proof")?;
    let proof=f.reconstruct_source_for_verification(&raw)?;let out=proof.lower_selector_paragraph_sort_candidate(&f,Scope::Document,Policy::default(),spec(),Default::default(),Default::default())?;
    assert_eq!(out.receipt(),sort(&f,&raw,Scope::Document,spec())?.receipt());
    let foreign=fixture::package(&(p(1,"OTHER")+&p(2,"A")))?;
    assert!(matches!(sort(&f,&foreign,Scope::Document,spec()),Err(E::Compile(Compile::Source))));let other=fixture::forms(&foreign,"foreign-proof")?;
    assert!(matches!(proof.lower_selector_paragraph_sort_candidate(&other,Scope::Document,Policy::default(),spec(),Default::default(),Default::default()),Err(E::Compile(Compile::Source))));Ok(())
}

#[test]
fn sort_already_sorted_and_single_paragraph_never_return_fake_changes()->TestResult {
    for body in [p(1,"A")+&p(2,"B"),p(1,"A")+&p(2,"A")] {let raw=fixture::package(&body)?;let f=fixture::forms(&raw,"sort-noop")?;
        assert!(matches!(sort(&f,&raw,Scope::Document,spec()),Err(E::Compile(Compile::NoChange))));}
    let raw=fixture::package(&p(1,"A"))?;let f=fixture::forms(&raw,"sort-one")?;assert!(matches!(sort(&f,&raw,Scope::Document,spec()),Err(E::Compile(Compile::NoMatches))));Ok(())
}

#[test]
fn sort_comparison_budget_rejects_long_common_prefix_and_invalid_limits()->TestResult {
    let prefix="X".repeat(4096);let raw=fixture::package(&(p(1,&(prefix.clone()+"Z"))+&p(2,&(prefix+"A"))))?;let f=fixture::forms(&raw,"sort-budget")?;
    for max in [0,64,32*1024*1024+1] {assert!(matches!(sort(&f,&raw,Scope::Document,Spec{max_comparison_bytes:max,..spec()}),Err(E::ComparisonLimit)));}
    assert_eq!(sort(&f,&raw,Scope::Document,spec())?.receipt().comparison_bytes,4097);Ok(())
}

#[test]
fn sort_observed_tracking_is_rejected_before_comparison_even_for_noop_keys()->TestResult {
    let raw=fixture::package(&(p(1,"A").replace("id='1'","id='1' paraTcId='1'")+&p(2,"B")))?;let f=fixture::forms(&raw,"sort-tracking")?;
    assert!(matches!(sort(&f,&raw,Scope::Document,spec()),Err(E::Compile(Compile::Protection))));Ok(())
}

#[test]
fn sort_field_cached_content_is_never_treated_as_plain_reorderable_text()->TestResult {
    let body=p(1,"OUTSIDE</hp:t><hp:ctrl><hp:fieldBegin id='17' type='MEMO' editable='1'/></hp:ctrl><hp:t>CACHE</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='17'/></hp:ctrl><hp:t>TAIL")+&p(2,"A");
    let raw=fixture::package(&body)?;let f=fixture::forms(&raw,"sort-field")?;
    assert!(matches!(sort(&f,&raw,Scope::Document,spec()),Err(E::StructuredKey)|Err(E::Compile(Compile::FieldContent))));Ok(())
}

#[test]
fn sort_multiple_cell_parents_are_rejected_without_silently_sorting_a_subset()->TestResult {
    let raw=assembly::package(&format!("<hp:t>OUTSIDE</hp:t>{}",table::table(300)))?;let f=fixture::forms(&raw,"sort-parents")?;
    let t=f.body_structure().graph().sections()[0].body.children.iter().find_map(|n|if let Node::Table(t)=n{Some(t)}else{None}).ok_or("table")?;
    let ids:Vec<_>=t.cells.iter().map(|c|c.body.children[0].common().node_id.clone()).collect();assert_eq!(ids.len(),2);
    assert!(matches!(sort(&f,&raw,Scope::NodeSet(&ids),spec()),Err(E::ParentScope)));Ok(())
}

#[test]
fn sort_receipt_and_debug_do_not_disclose_plaintext_or_grant_authority()->TestResult {
    let raw=fixture::package(&(p(1,"Z-PRIVATE-TEXT")+&p(2,"A-PRIVATE-TEXT")))?;let f=fixture::forms(&raw,"sort-private")?;let out=sort(&f,&raw,Scope::Document,spec())?;
    assert!(!format!("{out:?} {:?}",out.receipt()).contains("PRIVATE-TEXT"));let json=serde_json::to_string(out.receipt())?;assert!(!json.contains("PRIVATE-TEXT"));
    assert!(!out.receipt().locale_native_full_protection_or_execution_authority);assert!(!out.receipt().scope.whole_document_visibility_native_flow_or_revision_authority);
    assert!(out.receipt().whole_paragraph_scope_verified&&out.receipt().exact_subtrees_and_positional_gaps_read_back);Ok(())
}

#[test]
fn sort_source_output_writer_and_result_limits_remain_fail_closed()->TestResult {
    let raw=fixture::package(&(p(1,"Z")+&p(2,"A")))?;let f=fixture::forms(&raw,"sort-limits")?;
    let limits=SourceSearchLimits::new(SourceSearchLimitConfig{scalars:1,..SourceSearchLimitConfig::default()})?;
    assert!(matches!(f.lower_selector_paragraph_sort_candidate(&raw,Scope::Document,Policy::default(),spec(),limits,Default::default()),Err(E::Search(SourceSearchError::Limit))));
    let limits=SourceSearchLimits::new(SourceSearchLimitConfig{result_bytes:1,..SourceSearchLimitConfig::default()})?;
    assert!(f.lower_selector_paragraph_sort_candidate(&raw,Scope::Document,Policy::default(),spec(),limits,Default::default()).is_err());
    let writer=WriterLimits::new(WriterLimitConfig{max_output_bytes:1,..WriterLimitConfig::default()})?;
    assert!(matches!(f.lower_selector_paragraph_sort_candidate(&raw,Scope::Document,Policy::default(),spec(),Default::default(),writer),Err(E::Compile(Compile::Writer))));Ok(())
}

#[test]
fn sort_hundred_twenty_eight_paragraphs_is_stable_and_deterministic()->TestResult {
    let body=(0..128).rev().map(|i|p(i+1,&format!("KEY-{i:03}"))).collect::<String>();let raw=fixture::package(&body)?;let f=fixture::forms(&raw,"sort-128")?;
    let a=sort(&f,&raw,Scope::Document,spec())?;let b=sort(&f,&raw,Scope::Document,spec())?;
    assert_eq!(a.receipt(),b.receipt());assert_eq!(a.receipt().source_order,(0..128).rev().collect::<Vec<_>>());assert_eq!(bytes(&a)?,bytes(&b)?);Ok(())
}

#[test]
fn sort_hidden_and_memo_sibling_bodies_require_explicit_policy_and_keep_owning_envelopes()->TestResult {
    let a=p(11,"Z");let b=p(12,"A");
    for memo in [false,true] {
        let inner=format!("<hp:subList>{a}{b}</hp:subList>");
        let envelope=if memo{format!("<hp:ctrl><hp:fieldBegin id='17' type='MEMO' editable='0'>{inner}</hp:fieldBegin></hp:ctrl><hp:t>CACHE</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='17'/></hp:ctrl>")}
            else{format!("<hp:ctrl><hp:hiddenComment>{inner}</hp:hiddenComment></hp:ctrl>")};
        let raw=fixture::package(&p(1,&format!("BODY</hp:t>{envelope}<hp:t>TAIL")))?;let f=fixture::forms(&raw,"sort-review")?;
        let index=f.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?.inventory;
        let policy=Policy{include_hidden_explanations:!memo,include_memo_bodies:memo};let mut ids=Vec::new();
        for key in ["Z","A"] {
            let query=hwpx_package::document_import::search::SourceSearchQuery{query:key,mode:hwpx_package::document_import::search::SourceSearchMode::Literal,case_sensitive:true,whole_word:true,max_results:1};
            let found=index.find(query,Scope::Document,policy)?;let handle=&found.result().matches()[0].paragraph_anchor.opaque_handle;
            ids.push(inv.nodes.iter().find(|n|&n.source_handle==handle).ok_or("node")?.node_id.clone());
        }
        assert_eq!(ids.len(),2);
        assert!(matches!(sort(&f,&raw,Scope::NodeSet(&ids),spec()),Err(E::Compile(Compile::NoMatches))));
        let out=f.lower_selector_paragraph_sort_candidate(&raw,Scope::NodeSet(&ids),policy,spec(),Default::default(),Default::default())?;
        assert_eq!(out.receipt().source_order,vec![1,0]);assert!(section(&bytes(&out)?)?.contains(&(b.clone()+&a)));
        if memo{assert!(section(&bytes(&out)?)?.contains("<hp:t>CACHE</hp:t>"));}
    }Ok(())
}

#[test]
fn sort_inside_one_table_cell_preserves_structure_and_original_inherited_lock_guard()->TestResult {
    let body=table::table(300).replace(&table::paragraph(0,"CELL-OLD"),&(table::paragraph(0,"Z")+&table::paragraph(901,"A")));
    for locked in [false,true] {
        let body=if locked{body.replace("lock='0'","lock='1'")}else{body.clone()};
        let raw=assembly::package(&format!("<hp:t>OUTSIDE</hp:t>{body}"))?;let f=fixture::forms(&raw,"sort-cell")?;
        let t=f.body_structure().graph().sections()[0].body.children.iter().find_map(|n|if let Node::Table(t)=n{Some(t)}else{None}).ok_or("table")?;
        let ids:Vec<_>=t.cells[0].body.children.iter().map(|n|n.common().node_id.clone()).collect();assert_eq!(ids.len(),2);
        let out=sort(&f,&raw,Scope::NodeSet(&ids),spec());
        if locked{assert!(matches!(out,Err(E::Compile(Compile::Protection))));}
        else{let out=out?;assert_eq!(out.receipt().source_order,vec![1,0]);let text=section(&bytes(&out)?)?;
            assert!(text.contains(&(table::paragraph(901,"A")+&table::paragraph(0,"Z"))));assert!(text.contains("OTHER-CELL"));}
    }Ok(())
}

#[path="support/paragraph_sort_splice_inventory.rs"]mod splice_inventory_v1;
