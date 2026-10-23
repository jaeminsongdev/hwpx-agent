use hwpx_package::document_import::{ImportedSourcePackage,SourceImportLimits,forms::ImportedDocumentForms,
    structure::ImportedDocumentStructure,search::{SourceSearchQuery as Query,SourceSearchMode as Mode,SourceSearchLimits,
    SourceSearchLimitConfig as Config,SourceSearchError as E,scope::SourceSearchScope as Scope}};
use domain_ir::{DocumentId,LogicalId};
use sha2::{Digest as _,Sha256};
#[allow(dead_code)]
#[path="support/document_import_field_fixture.rs"] mod fixture;
type TestResult=Result<(),Box<dyn std::error::Error>>;
fn bytes()->Result<Vec<u8>,Box<dyn std::error::Error>> {fixture::package("<hp:p id='1'><hp:run><hp:t>same</hp:t><u:barrier/><hp:t>same</hp:t></hp:run></hp:p><hp:p id='2'><hp:run><hp:t>same</hp:t></hp:run></hp:p>")}
fn imported(b:&[u8])->Result<ImportedSourcePackage,Box<dyn std::error::Error>> {Ok(ImportedSourcePackage::import(b,DocumentId::parse("scope-document")?,Sha256::digest(b).into(),SourceImportLimits::default())?)}
fn query()->Query<'static> {Query {query:"same",mode:Mode::Literal,case_sensitive:true,whole_word:false,max_results:100}}
#[test]
fn scoped_search_resolves_actual_paragraphs_and_retains_global_block_positions()->TestResult {
    let b=bytes()?;let s=ImportedDocumentStructure::import(imported(&b)?)?;let i=s.source_text_index(&b,Default::default())?;
    let all=i.find_scoped(query(),Scope::MappedDocument)?;assert_eq!(all.result().matches().len(),3);
    assert_eq!((all.scope_receipt().selected_paragraphs,all.scope_receipt().selected_blocks),(2,3));
    let handle=all.result().matches()[2].paragraph_anchor.opaque_handle.clone();
    let one=i.find_scoped(query(),Scope::Paragraphs(&[handle]))?;assert_eq!(one.result().matches(),&all.result().matches()[2..]);
    assert_eq!((one.scope_receipt().selected_paragraphs,one.scope_receipt().selected_blocks),(1,1));
    assert_ne!(one.scope_receipt().scope_sha256,all.scope_receipt().scope_sha256);assert!(!one.scope_receipt().whole_document_visibility_qualified);Ok(())
}
#[test]
fn scoped_search_rejects_duplicate_empty_foreign_and_unmapped_handles_even_without_matches()->TestResult {
    let b=bytes()?;let s=ImportedDocumentStructure::import(imported(&b)?)?;let i=s.source_text_index(&b,Default::default())?;
    let all=i.find(query())?;let id=all.matches()[0].paragraph_anchor.opaque_handle.clone();
    let missing=LogicalId::parse("foreign-paragraph")?;let mut absent=query();absent.query="missing";
    for selected in [vec![],vec![id.clone(),id],vec![missing]] {assert!(matches!(i.find_scoped(absent,Scope::Paragraphs(&selected)),Err(E::Scope)));}Ok(())
}
#[test]
fn scoped_search_digest_is_set_canonical_but_distinguishes_all_mapped_from_explicit_selection()->TestResult {
    let b=bytes()?;let s=ImportedDocumentStructure::import(imported(&b)?)?;let i=s.source_text_index(&b,Default::default())?;
    let all=i.find(query())?;let a=all.matches()[0].paragraph_anchor.opaque_handle.clone();let z=all.matches()[2].paragraph_anchor.opaque_handle.clone();
    let first=i.find_scoped(query(),Scope::Paragraphs(&[a.clone(),z.clone()]))?;
    let reverse=i.find_scoped(query(),Scope::Paragraphs(&[z,a]))?;
    assert_eq!(first.canonical_json()?,reverse.canonical_json()?);
    assert_ne!(first.scope_receipt().scope_sha256,i.find_scoped(query(),Scope::MappedDocument)?.scope_receipt().scope_sha256);Ok(())
}
#[test]
fn scoped_search_whole_response_budget_includes_scope_wrapper_without_truncating()->TestResult {
    let b=bytes()?;let s=ImportedDocumentStructure::import(imported(&b)?)?;let i=s.source_text_index(&b,Default::default())?;
    let mut q=query();q.query="absent";let plain=i.find(q)?.canonical_json()?;
    let tight=SourceSearchLimits::new(Config {result_bytes:plain.len(),..Default::default()})?;
    let index=s.source_text_index(&b,tight)?;assert!(index.find(q).is_ok());
    assert!(matches!(index.find_scoped(q,Scope::MappedDocument),Err(E::Output)));Ok(())
}
#[test]
fn scoped_search_reuses_whole_form_reconstruction_only_for_its_exact_original()->TestResult {
    let b=bytes()?;let original=ImportedDocumentForms::import(imported(&b)?)?;let foreign=ImportedDocumentForms::import(imported(&b)?)?;
    let proof=original.reconstruct_source_for_verification(&b)?;
    let shared=proof.source_text_index(&original,Default::default())?;
    let direct=original.body_structure().source_text_index(&b,Default::default())?;
    assert_eq!(shared.find_scoped(query(),Scope::MappedDocument)?.canonical_json()?,direct.find_scoped(query(),Scope::MappedDocument)?.canonical_json()?);
    assert!(matches!(proof.source_text_index(&foreign,Default::default()),Err(E::Source)));Ok(())
}
#[test]
fn scoped_search_empty_original_retains_zero_match_coverage_without_a_full_document_claim()->TestResult {
    let b=fixture::package("<hp:p id='1'><hp:run/></hp:p>")?;let s=ImportedDocumentStructure::import(imported(&b)?)?;
    let result=s.source_text_index(&b,Default::default())?.find_scoped(query(),Scope::MappedDocument)?;
    assert!(result.result().matches().is_empty());assert_eq!(result.scope_receipt().selected_paragraphs,1);
    assert!(!result.scope_receipt().whole_document_visibility_qualified);Ok(())
}
