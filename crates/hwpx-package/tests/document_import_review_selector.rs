use hwpx_package::document_import::{ImportedSourcePackage,forms::ImportedDocumentForms,search::{SourceSearchQuery as Query,SourceSearchMode as Mode,
    SourceSearchLimits,SourceSearchLimitConfig as Config,SourceSearchError as E,selector::{SourceIndexScopeSelector as Scope,SourceIndexBoundary as Boundary},
    reviews::{SourceReviewTextPolicy as Policy,SourceTextRegion as Region}}};
use domain_ir::{DocumentId,LogicalId};
use sha2::{Digest as _,Sha256};
#[path="support/review_scope_fixture.rs"] mod fixture;
type TestResult=Result<(),Box<dyn std::error::Error>>;
fn forms(raw:&[u8],id:&str)->Result<ImportedDocumentForms,Box<dyn std::error::Error>> {Ok(ImportedDocumentForms::import(ImportedSourcePackage::import(raw,DocumentId::parse(id)?,Sha256::digest(raw).into(),Default::default())?)?)}
fn query(q:&str)->Query<'_> {Query {query:q,mode:Mode::Literal,case_sensitive:true,whole_word:false,max_results:100}}
fn all()->Policy {Policy {include_hidden_explanations:true,include_memo_bodies:true}}
#[test]
fn review_selector_inventory_contains_actual_supplemental_nodes_and_region_boundaries_without_private_text()->TestResult {
    let raw=fixture::package()?;let forms=forms(&raw,"review-selector")?;let index=forms.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?;
    assert_eq!(inv.inventory.blocks.len(),inv.block_regions.len());
    for region in [Region::HiddenExplanation,Region::MemoBody] {let (i,_)=inv.block_regions.iter().enumerate().find(|(_,r)|**r==region).ok_or("region")?;let block=&inv.inventory.blocks[i];
        let node=inv.inventory.nodes.iter().find(|n|n.source_handle==block.paragraph_handle).ok_or("supplemental node")?;assert_ne!(node.node_id,node.source_handle);
        let found=index.find(query("K"),Scope::NodeSet(&[node.node_id.clone()]),all())?;assert_eq!(found.result().matches().len(),2);assert!(found.match_regions().iter().all(|r|*r==region));}
    let text=String::from_utf8(inv.canonical_json()?)?;assert!(!text.contains("PRIVATE-AUTHOR")&&!text.contains("HIDDEN K"));assert!(!inv.native_visibility_or_execution_authority);Ok(())
}
#[test]
fn review_selector_document_four_policies_exclude_before_caps_and_bind_request_without_widening_scope()->TestResult {
    let raw=fixture::package()?;let forms=forms(&raw,"review-selector")?;let index=forms.source_review_scope_index(&raw,Default::default())?;let mut scopes=Vec::new();let mut requests=Vec::new();
    for (hidden,memo,count) in [(false,false,2),(true,false,4),(false,true,4),(true,true,6)] {
        let found=index.find(Query {max_results:count,..query("K")},Scope::Document,Policy {include_hidden_explanations:hidden,include_memo_bodies:memo})?;
        assert_eq!(found.result().matches().len(),count);scopes.push(found.scope_receipt().scope_sha256);requests.push(found.request_sha256());}
    assert!(scopes.iter().all(|s|*s==scopes[0]));let unique:std::collections::BTreeSet<_>=requests.into_iter().collect();assert_eq!(unique.len(),4);Ok(())
}
#[test]
fn review_selector_excluded_supplemental_node_is_valid_empty_scope_not_foreign_handle()->TestResult {
    let raw=fixture::package()?;let forms=forms(&raw,"review-selector")?;let index=forms.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?;
    for region in [Region::HiddenExplanation,Region::MemoBody] {let position=inv.block_regions.iter().position(|r|*r==region).ok_or("region")?;let handle=&inv.inventory.blocks[position].paragraph_handle;
        let node=inv.inventory.nodes.iter().find(|n|&n.source_handle==handle).ok_or("node")?;
        let excluded=index.find(query("K"),Scope::NodeSet(&[node.node_id.clone()]),Policy::default())?;assert!(excluded.result().matches().is_empty());
        assert_eq!(excluded.scope_receipt().selected_paragraphs,1);let value:serde_json::Value=serde_json::from_slice(&excluded.canonical_json()?)?;
        assert_eq!(value["searched_blocks"],0);assert_eq!(value[if region==Region::MemoBody{"excluded_memo_paragraphs"}else{"excluded_hidden_paragraphs"}],1);}
    Ok(())
}
#[test]
fn review_selector_partial_hidden_and_memo_windows_apply_regex_before_caps_and_keep_global_positions()->TestResult {
    let raw=fixture::package()?;let forms=forms(&raw,"review-selector")?;let index=forms.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?;
    for (region,scalar) in [(Region::HiddenExplanation,9),(Region::MemoBody,7)] {let n=inv.block_regions.iter().position(|r|*r==region).ok_or("region")?;let b=&inv.inventory.blocks[n];
        let start=Boundary {paragraph_handle:b.paragraph_handle.clone(),block_index:b.block_index,normalized_scalar:scalar};let end=Boundary {normalized_scalar:scalar+1,..start.clone()};
        let found=index.find(Query {query:"^K$",mode:Mode::Regex,max_results:1,..query("K")},Scope::Selection {index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},all())?;
        assert_eq!(found.result().matches().len(),1);assert_eq!(found.match_regions(),[region]);assert_eq!(found.result().matches()[0].start_normalized_scalar,scalar);
        assert_eq!(found.result().matches()[0].pieces[0].start_scalar,u32::try_from(scalar)?);}
    Ok(())
}
#[test]
fn review_selector_section_and_parent_node_scope_include_actual_nested_bodies_without_duplicate_matches()->TestResult {
    let raw=fixture::package()?;let forms=forms(&raw,"review-selector")?;let index=forms.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?;
    let section=index.find(query("K"),Scope::Section(&inv.inventory.section_ids),all())?;assert_eq!(section.result().matches().len(),6);
    let parent=forms.body_structure().graph().sections()[0].body.children[0].common().node_id.clone();
    let n=inv.block_regions.iter().position(|r|*r==Region::HiddenExplanation).ok_or("hidden")?;
    let child=inv.inventory.nodes.iter().find(|node|node.source_handle==inv.inventory.blocks[n].paragraph_handle).ok_or("child")?.node_id.clone();
    let both=index.find(query("K"),Scope::NodeSet(&[parent,child]),all())?;assert_eq!(both.result().matches(),section.result().matches());Ok(())
}
#[test]
fn review_selector_multi_block_and_collapsed_selection_do_not_concatenate_or_fabricate_editable_ranges()->TestResult {
    let raw=fixture::package()?;let forms=forms(&raw,"review-selector")?;let index=forms.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?;
    let first=&inv.inventory.blocks[0];let memo=inv.block_regions.iter().position(|r|*r==Region::MemoBody).ok_or("memo")?;let last=&inv.inventory.blocks[memo];
    let start=Boundary {paragraph_handle:first.paragraph_handle.clone(),block_index:first.block_index,normalized_scalar:5};let end=Boundary {paragraph_handle:last.paragraph_handle.clone(),block_index:last.block_index,normalized_scalar:6};
    let scope=Scope::Selection {index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end};assert_eq!(index.find(query("K"),scope,all())?.result().matches().len(),5);
    assert!(index.find(query("K KHIDDEN"),scope,all())?.result().matches().is_empty());
    let empty=index.find(Query {query:"^$",mode:Mode::Regex,..query("K")},Scope::Selection {index_sha256:inv.inventory.index.index_sha256,start:&start,end:&start},all())?;
    assert_eq!(empty.result().matches().len(),1);assert!(empty.result().matches()[0].pieces.is_empty()&&!empty.result().matches()[0].source_scalar_selection_exact);Ok(())
}
#[test]
fn review_selector_stale_forged_foreign_proof_and_invalid_scope_fail_even_for_absent_queries()->TestResult {
    let raw=fixture::package()?;let original=forms(&raw,"review-selector")?;let other=forms(&raw,"review-selector")?;let proof=original.reconstruct_source_for_verification(&raw)?;
    assert!(matches!(proof.source_review_scope_index(&other,Default::default()),Err(E::Source)));
    let index=proof.source_review_scope_index(&original,Default::default())?;let inv=index.scope_inventory()?;let b=&inv.inventory.blocks[0];
    let at=Boundary {paragraph_handle:b.paragraph_handle.clone(),block_index:b.block_index,normalized_scalar:0};
    assert!(matches!(index.find(query("absent"),Scope::Selection {index_sha256:[0;32],start:&at,end:&at},all()),Err(E::Scope)));
    assert!(matches!(index.find(query("absent"),Scope::NodeSet(&[LogicalId::parse("foreign")?]),all()),Err(E::Scope)));Ok(())
}
#[test]
fn review_selector_malformed_review_and_aggregate_response_limits_remain_fail_closed()->TestResult {
    let raw=fixture::package()?;let forms=forms(&raw,"review-selector")?;
    assert!(forms.source_review_scope_index(&raw,SourceSearchLimits::new(Config {result_bytes:1,..Default::default()})?).is_err());
    assert!(forms.source_review_scope_index(&raw,SourceSearchLimits::new(Config {blocks:1,..Default::default()})?).is_err());
    let bad=fixture::with_body(&fixture::body().replace("</hp:hiddenComment>","<hp:subList/></hp:hiddenComment>"))?;
    let original=ImportedDocumentForms::import(ImportedSourcePackage::import(&bad,DocumentId::parse("bad-review")?,Sha256::digest(&bad).into(),Default::default())?)?;
    assert!(original.source_review_scope_index(&bad,Default::default()).is_err());Ok(())
}
