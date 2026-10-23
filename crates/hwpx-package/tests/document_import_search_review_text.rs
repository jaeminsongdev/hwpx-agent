use hwpx_package::document_import::{ImportedSourcePackage,SourceImportLimits,forms::ImportedDocumentForms,
    search::{SourceSearchLimits,SourceSearchLimitConfig as Config,SourceSearchQuery as Query,SourceSearchMode as Mode,SourceSearchError as E,
        scope::SourceSearchScope as Scope,reviews::{SourceReviewTextPolicy as Policy,SourceTextRegion as Region}}};
use domain_ir::{DocumentId,LogicalId};
use sha2::{Digest as _,Sha256};
#[path="support/search_review_fixture.rs"] mod fixture;
type TestResult=Result<(),Box<dyn std::error::Error>>;
fn import(b:&[u8],id:&str)->Result<ImportedDocumentForms,Box<dyn std::error::Error>> {Ok(ImportedDocumentForms::import(ImportedSourcePackage::import(b,
    DocumentId::parse(id)?,Sha256::digest(b).into(),SourceImportLimits::default())?)?)}
fn query(s:&str)->Query<'_> {Query {query:s,mode:Mode::Literal,case_sensitive:true,whole_word:false,max_results:100}}
#[test]
fn review_text_policy_independently_includes_original_hidden_and_memo_regions_in_source_order()->TestResult {
    let b=fixture::package()?;let forms=import(&b,"review-policy")?;let index=forms.source_review_text_index(&b,Default::default())?;
    for (hidden,memo,expected) in [(false,false,2),(true,false,3),(false,true,3),(true,true,4)] {
        let result=index.find(query("K"),Scope::MappedDocument,Policy {include_hidden_explanations:hidden,include_memo_bodies:memo})?;
        assert_eq!(result.matches().matches().len(),expected);assert_eq!(result.match_regions().len(),expected);
        let mut regions=vec![Region::BodyAndNotes];if hidden {regions.push(Region::HiddenExplanation);}if memo {regions.push(Region::MemoBody);}regions.push(Region::BodyAndNotes);
        assert_eq!(result.match_regions(),regions);assert!(!index.review_receipt().native_visibility_resolution_binding_verified);
    }index.verify_source(&b)?;Ok(())
}
#[test]
fn review_text_policy_exclusions_precede_match_limits_and_are_explicit_in_zero_result_coverage()->TestResult {
    let b=fixture::with_body(&fixture::body().replace("HIDDEN K","HIDDEN HIDDEN K"))?;let forms=import(&b,"exclusions")?;let index=forms.source_review_text_index(&b,Default::default())?;
    let result=index.find(Query {max_results:1,..query("HIDDEN")},Scope::MappedDocument,Policy::default())?;
    assert!(result.matches().matches().is_empty());let json:serde_json::Value=serde_json::from_slice(&result.canonical_json()?)?;
    assert_eq!(json["excluded_hidden_paragraphs"],1);assert_eq!(json["excluded_memo_paragraphs"],1);
    assert_eq!(json["searched_paragraphs"],1);assert_eq!(json["coverage"],"selected_admitted_file_regions");
    assert_eq!(json["app_visibility_cascade_or_full_document_search_qualified"],false);
    assert!(matches!(index.find(Query {max_results:1,..query("HIDDEN")},Scope::MappedDocument,
        Policy {include_hidden_explanations:true,include_memo_bodies:false}),Err(E::Limit)));Ok(())
}
#[test]
fn review_text_paragraph_scope_can_select_hidden_body_without_rejecting_other_corpus_regions()->TestResult {
    let b=fixture::package()?;let forms=import(&b,"review-scope")?;let index=forms.source_review_text_index(&b,Default::default())?;
    let policy=Policy {include_hidden_explanations:true,include_memo_bodies:true};let all=index.find(query("HIDDEN"),Scope::MappedDocument,policy)?;
    let id=all.matches().matches()[0].paragraph_anchor.opaque_handle.clone();
    let selected=index.find(query("HIDDEN"),Scope::Paragraphs(&[id.clone()]),policy)?;assert_eq!(selected.matches().matches().len(),1);
    assert!(index.find(query("HIDDEN"),Scope::Paragraphs(&[id]),Policy::default())?.matches().matches().is_empty());
    assert!(matches!(index.find(query("missing"),Scope::Paragraphs(&[LogicalId::parse("foreign")?]),policy),Err(E::Scope)));Ok(())
}
#[test]
fn review_text_nfc_crosses_runs_inside_bodies_but_never_connects_body_boundaries()->TestResult {
    let body=fixture::body().replace("<hp:t>HIDDEN K</hp:t>","<hp:t>ᄀ</hp:t></hp:run><hp:run><hp:t>ᅡᆨ</hp:t>");
    let b=fixture::with_body(&body)?;let forms=import(&b,"review-nfc")?;let index=forms.source_review_text_index(&b,Default::default())?;
    let policy=Policy {include_hidden_explanations:true,include_memo_bodies:true};let result=index.find(query("각"),Scope::MappedDocument,policy)?;
    assert_eq!(result.match_regions(),[Region::HiddenExplanation]);assert_eq!(result.matches().matches()[0].pieces.len(),2);
    for phrase in ["BODY K각","MEMO KCACHE","CACHE KTAIL"] {assert!(index.find(query(phrase),Scope::MappedDocument,policy)?.matches().matches().is_empty());}Ok(())
}
#[test]
fn review_text_foreign_proof_changed_source_and_empty_review_inventory_do_not_upgrade_visibility()->TestResult {
    let b=fixture::package()?;let forms=import(&b,"proof")?;let foreign=import(&b,"proof")?;let proof=forms.reconstruct_source_for_verification(&b)?;
    assert!(matches!(proof.source_review_text_index(&foreign,Default::default()),Err(E::Source)));
    let index=proof.source_review_text_index(&forms,Default::default())?;let changed=fixture::with_body(&fixture::body().replace("HIDDEN","CHANGED"))?;
    assert!(index.verify_source(&changed).is_err());
    let simple=fixture::with_body("<hp:p id='1'><hp:run><hp:t>plain</hp:t></hp:run></hp:p>")?;let empty=import(&simple,"no-review")?;
    let index=empty.source_review_text_index(&simple,Default::default())?;assert_eq!(index.review_receipt().hidden_explanations,0);
    assert!(!index.index_receipt().whole_document_visibility_and_search_qualified);Ok(())
}
#[test]
fn review_text_original_reader_rejects_malformed_hidden_or_unpaired_memo_instead_of_skipping_them()->TestResult {
    for body in [fixture::body().replace("</hp:hiddenComment>","<hp:subList/></hp:hiddenComment>"),
        fixture::body().replace("<hp:ctrl><hp:fieldEnd beginIDRef='17'/></hp:ctrl>","")] {
        let b=fixture::with_body(&body)?;
        if let Ok(forms)=import(&b,"malformed-review") {assert!(forms.source_review_text_index(&b,Default::default()).is_err());}
    }Ok(())
}
#[test]
fn review_text_aggregate_scalar_paragraph_and_response_limits_include_supplemental_bodies()->TestResult {
    let b=fixture::package()?;let forms=import(&b,"limits")?;
    for limits in [Config {paragraphs:1,..Default::default()},Config {scalars:18,..Default::default()},Config {result_bytes:1,..Default::default()}] {
        assert!(forms.source_review_text_index(&b,SourceSearchLimits::new(limits)?).is_err());
    }
    let index=forms.source_review_text_index(&b,Default::default())?;assert!(matches!(index.find(Query {max_results:1,..query("K")},Scope::MappedDocument,Policy::default()),Err(E::Limit)));Ok(())
}
#[test]
fn review_text_policy_and_extended_corpus_are_digest_bound_without_raw_text_or_query_in_results()->TestResult {
    let b=fixture::package()?;let forms=import(&b,"binding")?;let index=forms.source_review_text_index(&b,Default::default())?;
    let first=index.find(query("PRIVATE-ABSENT"),Scope::MappedDocument,Policy::default())?;
    let other=index.find(query("PRIVATE-ABSENT"),Scope::MappedDocument,Policy {include_hidden_explanations:true,include_memo_bodies:false})?;
    assert_ne!(first.request_sha256(),other.request_sha256());assert!(!String::from_utf8(first.canonical_json()?)?.contains("PRIVATE"));
    assert!(!format!("{index:?}{first:?}").contains("HIDDEN K"));
    let base=forms.body_structure().source_text_index(&b,Default::default())?;assert_ne!(base.receipt().index_sha256,index.index_receipt().index_sha256);Ok(())
}
