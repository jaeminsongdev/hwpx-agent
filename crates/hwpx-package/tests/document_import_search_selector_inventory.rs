use hwpx_package::document_import::{ImportedSourcePackage,SourceImportLimits,structure::ImportedDocumentStructure,
    search::{SourceSearchQuery as Query,SourceSearchMode as Mode,SourceSearchLimitConfig as Config,SourceSearchLimits,SourceSearchError as E,
        selector::{SourceIndexScopeSelector as Scope,SourceIndexBoundary as Boundary}}};
use domain_ir::DocumentId;
use sha2::{Digest as _,Sha256};
#[path="support/source_scope_fixture.rs"] mod fixture;
type TestResult=Result<(),Box<dyn std::error::Error>>;
fn import(raw:&[u8],document:&str)->Result<ImportedDocumentStructure,Box<dyn std::error::Error>> {Ok(ImportedDocumentStructure::import(
    ImportedSourcePackage::import(raw,DocumentId::parse(document)?,Sha256::digest(raw).into(),SourceImportLimits::default())?)?)}
fn query(q:&str)->Query<'_> {Query {query:q,mode:Mode::Literal,case_sensitive:true,whole_word:false,max_results:100}}
#[test]
fn inventory_two_sections_nodes_and_block_boundaries_drive_all_four_actual_scope_forms()->TestResult {
    let raw=fixture::package()?;let s=import(&raw,"inventory")?;let i=s.source_text_index(&raw,Default::default())?;let inv=i.scope_inventory()?;
    assert_eq!((inv.section_ids.len(),inv.nodes.len(),inv.blocks.len()),(2,2,2));assert_ne!(inv.section_ids[0],inv.section_ids[1]);
    assert_eq!(inv.index.index_sha256,i.receipt().index_sha256);assert!(!inv.full_source_visibility_native_flow_or_revision_authority);
    assert_eq!(i.find_selector(query("same"),Scope::Document)?.result().matches().len(),5);
    assert_eq!(i.find_selector(query("same"),Scope::Section(&inv.section_ids[..1]))?.result().matches().len(),2);
    let b=&inv.blocks[0];let node=inv.nodes.iter().find(|n|n.source_handle==b.paragraph_handle).ok_or("node binding")?;
    assert_ne!(node.node_id,node.source_handle);assert_eq!(i.find_selector(query("same"),Scope::NodeSet(&[node.node_id.clone()]))?.result().matches().len(),2);
    let start=Boundary {paragraph_handle:b.paragraph_handle.clone(),block_index:b.block_index,normalized_scalar:2};let end=Boundary {normalized_scalar:14,..start.clone()};
    let result=i.find_selector(Query {query:"^PRIVATE-same$",mode:Mode::Regex,..query("unused")},Scope::Selection {index_sha256:inv.index.index_sha256,start:&start,end:&end})?;
    assert_eq!(result.result().matches().len(),1);assert_eq!((result.result().matches()[0].start_normalized_scalar,result.result().matches()[0].end_normalized_scalar),(2,14));Ok(())
}
#[test]
fn inventory_canonical_digest_is_source_bound_and_descriptors_do_not_disclose_body_text()->TestResult {
    let raw=fixture::package()?;let s=import(&raw,"inventory")?;let i=s.source_text_index(&raw,Default::default())?;let a=i.scope_inventory()?;let b=i.scope_inventory()?;
    assert_eq!(a.canonical_json()?,b.canonical_json()?);assert_eq!(a.binding_sha256()?,b.binding_sha256()?);
    assert!(!String::from_utf8(a.canonical_json()?)?.contains("PRIVATE-same"));assert!(!format!("{a:?}").contains("PRIVATE-same"));
    let other=import(&raw,"foreign-inventory")?;let foreign=other.source_text_index(&raw,Default::default())?.scope_inventory()?;assert_ne!(a.binding_sha256()?,foreign.binding_sha256()?);Ok(())
}
#[test]
fn inventory_full_descriptor_response_and_catalog_counts_fail_instead_of_truncating()->TestResult {
    let raw=fixture::package()?;let s=import(&raw,"inventory")?;let i=s.source_text_index(&raw,Default::default())?;let length=i.scope_inventory()?.canonical_json()?.len();
    let exact=s.source_text_index(&raw,SourceSearchLimits::new(Config {result_bytes:length,..Default::default()})?)?;assert_eq!(exact.scope_inventory()?.canonical_json()?.len(),length);
    let small=s.source_text_index(&raw,SourceSearchLimits::new(Config {result_bytes:length-1,..Default::default()})?)?;assert!(matches!(small.scope_inventory(),Err(E::Output)));Ok(())
}
#[test]
fn inventory_boundary_json_rejects_extra_fields_and_native_validation_still_rejects_forged_coordinates()->TestResult {
    let raw=fixture::package()?;let s=import(&raw,"inventory")?;let i=s.source_text_index(&raw,Default::default())?;let inventory=i.scope_inventory()?;let b=&inventory.blocks[0];
    let value=serde_json::json!({"paragraph_handle":b.paragraph_handle,"block_index":b.block_index,"normalized_scalar":0});
    let start:Boundary=serde_json::from_value(value.clone())?;let mut bad=value;bad["approved"]=serde_json::json!(true);assert!(serde_json::from_value::<Boundary>(bad).is_err());
    let end=Boundary {normalized_scalar:b.normalized_scalars+1,..start.clone()};assert!(matches!(i.find_selector(query("absent"),Scope::Selection {index_sha256:inventory.index.index_sha256,start:&start,end:&end}),Err(E::Scope)));Ok(())
}
