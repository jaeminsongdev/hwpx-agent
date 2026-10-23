use hwpx_package::{BoundedZipReader,PreservingXmlDocument,WriterLimits,WriterLimitConfig,
    document_import::{ImportedSourcePackage,forms::ImportedDocumentForms,search::{SourceSearchQuery as Query,SourceSearchMode as Mode,
        SourceSearchError as Search,SourceSearchLimits,SourceSearchLimitConfig as Config,selector::{SourceIndexScopeSelector as Scope,SourceIndexBoundary as Boundary},
        reviews::{SourceReviewTextPolicy as Policy,selector::styles::SourceReviewStyleFilter as Filter},inspection::{SourceDeclaredStyleFilter as Declared,
            definitions::{SourceDefinitionStyleFilter as Definition,CharacterDefinitionSource as Axis,ParagraphDefinitionSource as ParaAxis,DefinitionAlignment as Align}},
        replacement::{SourceLiteralReplacementError as E,SourceReplacementRunPolicy as Run,atoms::unicode::{SourceUnicodeNormalizationForm as Form,
            matches::{SourceUnicodeMatchCandidate as Candidate,SourceUnicodeMatchSearch as Found,SOURCE_UNICODE_MATCH_PROFILE,SOURCE_UNICODE_MATCH_OUTPUT_PROFILE}}}}}};
use domain_ir::DocumentId;
use sha2::{Digest as _,Sha256};
use std::{error::Error,io::Cursor};
#[allow(dead_code)] #[path="support/search_definition_fixture.rs"] mod fixture;
#[allow(dead_code)] #[path="support/review_scope_fixture.rs"] mod review;
#[allow(dead_code)] #[path="support/document_import_review_assembly_fixture.rs"] mod assembly;
#[allow(dead_code)] #[path="support/review_cell_output_fixture.rs"] mod table;
type TestResult=Result<(),Box<dyn Error>>;
fn forms(raw:&[u8])->Result<ImportedDocumentForms,Box<dyn Error>> {Ok(ImportedDocumentForms::import(ImportedSourcePackage::import(raw,DocumentId::parse("unicode-matches")?,Sha256::digest(raw).into(),Default::default())?)?)}
fn p(id:u32,text:&str)->String {format!("<hp:p id='{id}' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'><hp:t>{text}</hp:t></hp:run></hp:p>")}
fn all()->Policy{Policy {include_hidden_explanations:true,include_memo_bodies:true}}
fn query(q:&str)->Query<'_>{Query {query:q,mode:Mode::Literal,case_sensitive:true,whole_word:false,max_results:10000}}
fn run(f:&ImportedDocumentForms,raw:&[u8],q:Query<'_>,scope:Scope<'_>,policy:Policy,filter:Option<Filter>,form:Form)->Result<Candidate,E> {
    f.lower_review_selector_unicode_matches(raw,q,scope,policy,filter,form,Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default())}
fn section(raw:&[u8])->Result<String,Box<dyn Error>> {let mut zip=BoundedZipReader::open(Cursor::new(raw),Default::default())?;
    let i=zip.entries().iter().position(|e|e.path.as_str()=="Contents/section0.xml").ok_or("section")?;Ok(String::from_utf8(zip.read_entry(i)?)?)}
fn exact(raw:&[u8],c:&Candidate,old:&str,new:&str)->TestResult {
    let bytes=c.with_verified_bytes(<[u8]>::to_vec)?;assert_eq!(section(&bytes)?,section(raw)?.replace(old,new));
    let mut a=BoundedZipReader::open(Cursor::new(raw),Default::default())?;let mut b=BoundedZipReader::open(Cursor::new(&bytes),Default::default())?;
    assert_eq!(a.entries().len(),b.entries().len());for i in 0..a.entries().len(){let path=a.entries()[i].path.clone();if path.as_str()=="Contents/section0.xml"{continue;}
        let j=b.entries().iter().position(|e|e.path==path).ok_or("part")?;assert_eq!(a.read_entry(i)?,b.read_entry(j)?);}
    let r=c.receipt();assert_eq!(r.profile,SOURCE_UNICODE_MATCH_PROFILE);assert_eq!(r.output.profile,SOURCE_UNICODE_MATCH_OUTPUT_PROFILE);
    assert_eq!(r.request_sha256,r.output.request_sha256);assert!(r.output.exact_original_selection_verified&&r.output.unchanged_components_keep_original_placement
        &&r.output.original_controls_and_all_reference_shells_preserved&&r.output.independent_normalization_oracle_verified&&r.output.output_text_spans_and_outside_slots_verified);
    assert!(!r.full_contract_native_service_or_execution_authority&&!r.output.full_contract_native_service_or_execution_authority);Ok(())
}
#[test]
fn unicode_match_literal_nfc_search_edits_decomposed_original_and_keeps_normalized_match()->TestResult {
    let raw=fixture::package(&p(1,"à à KEEP é"))?;let f=forms(&raw)?;let c=run(&f,&raw,query("à"),Scope::Document,all(),None,Form::Nfc)?;
    exact(&raw,&c,"à à KEEP é","à à KEEP é")?;assert_eq!(c.receipt().search.search().result().matches().len(),2);
    assert_eq!(c.receipt().output.selected_original_scalars,3);assert_eq!(c.receipt().output.changed_components,1);Ok(())
}
#[test]
fn unicode_match_regex_casefold_and_whole_word_preserve_original_letter_case()->TestResult {
    let raw=fixture::package(&p(1,"À MÀ à"))?;let f=forms(&raw)?;let q=Query {mode:Mode::Regex,case_sensitive:false,whole_word:true,..query("à")};
    let c=run(&f,&raw,q,Scope::Document,all(),None,Form::Nfd)?;exact(&raw,&c,"À MÀ à","À MÀ à")?;assert_eq!(c.receipt().search.search().result().matches().len(),2);Ok(())
}
#[test]
fn unicode_match_declared_style_filters_whole_original_contributor_set_before_match_limit()->TestResult {
    let body="<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>ᄀ</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>ᅡ 가</hp:t></hp:run></hp:p>";
    let raw=fixture::package(body)?;let f=forms(&raw)?;let filter=Some(Filter::Declared(Declared {run_character_property:Some(1),..Default::default()}));
    let c=run(&f,&raw,Query {max_results:1,..query("가")},Scope::Document,all(),filter,Form::Nfc)?;
    exact(&raw,&c,">ᅡ 가<",">ᅡ 가<")?;assert_eq!(c.receipt().search.search().result().matches().len(),1);Ok(())
}
#[test]
fn unicode_match_definition_filter_uses_actual_typed_values_not_reference_number_as_style()->TestResult {
    let body="<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>à</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>à</hp:t></hp:run></hp:p>";
    let raw=fixture::package(body)?;let f=forms(&raw)?;let filter=Some(Filter::Definition(Definition {character_source:Some(Axis::RunProperty),bold:Some(true),..Default::default()}));
    let c=run(&f,&raw,query("à"),Scope::Document,all(),filter,Form::Nfc)?;
    exact(&raw,&c,"<hp:run charPrIDRef='1'><hp:t>à</hp:t>","<hp:run charPrIDRef='1'><hp:t>à</hp:t>")?;
    let Found::Style(found)=&c.receipt().search else{return Err("style result".into())};assert!(found.definition_receipt().is_some());Ok(())
}
#[test]
fn unicode_match_all_four_forms_use_original_values_not_matched_nfc_text()->TestResult {
    let text="각 à①ﬃ";let raw=fixture::package(&p(1,text))?;let f=forms(&raw)?;
    for(form,out)in[(Form::Nfc,"각 à①ﬃ"),(Form::Nfd,"각 à①ﬃ"),(Form::Nfkc,"각 à1ffi"),(Form::Nfkd,"각 à1ffi")] {
        let c=run(&f,&raw,Query {mode:Mode::Regex,..query(".+")},Scope::Document,all(),None,form)?;exact(&raw,&c,text,out)?;
    }Ok(())
}
#[test]
fn unicode_match_four_selectors_clip_regex_windows_before_matching_and_never_widen()->TestResult {
    let raw=fixture::package(&(p(1,"X à Z")+&p(2,"Y à Z")))?;let f=forms(&raw)?;let inv=f.source_review_scope_index(&raw,Default::default())?.scope_inventory()?;let b=&inv.inventory.blocks[0];
    let ids=[inv.inventory.nodes.iter().find(|n|n.source_handle==b.paragraph_handle).ok_or("node")?.node_id.clone()];
    let start=Boundary {paragraph_handle:b.paragraph_handle.clone(),block_index:0,normalized_scalar:2};let end=Boundary {normalized_scalar:3,..start.clone()};
    for(scope,n)in[(Scope::Document,2),(Scope::Section(&inv.inventory.section_ids),2),(Scope::NodeSet(&ids),1),(Scope::Selection {index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},1)] {
        let q=Query {mode:Mode::Regex,..query(if matches!(scope,Scope::Selection {..}){"^à$"}else{"à"})};let c=run(&f,&raw,q,scope,all(),None,Form::Nfc)?;
        assert_eq!(c.receipt().search.search().result().matches().len(),n);let out=c.with_verified_bytes(section)??;assert!(out.contains("X à Z"));assert_eq!(out.contains("Y à Z"),n==1);
    }Ok(())
}
#[test]
fn unicode_match_noncontiguous_and_partial_original_inverse_are_rejected_not_expanded()->TestResult {
    for(text,q)in[("à̕","à"),("&#x344;","\u{308}")] {let raw=fixture::package(&p(1,text))?;let f=forms(&raw)?;
        assert!(matches!(run(&f,&raw,query(q),Scope::Document,all(),None,Form::Nfc),Err(E::Selection)));}
    let raw=fixture::package(&p(1,"à̕"))?;let f=forms(&raw)?;let c=run(&f,&raw,query("à̕"),Scope::Document,all(),None,Form::Nfc)?;exact(&raw,&c,"à̕","à̕")?;Ok(())
}
#[test]
fn unicode_match_zero_width_no_matches_and_no_change_are_distinct_failures()->TestResult {
    let raw=fixture::package(&p(1,"ABC à"))?;let f=forms(&raw)?;
    assert!(matches!(run(&f,&raw,query("ABSENT"),Scope::Document,all(),None,Form::Nfc),Err(E::NoMatches)));
    assert!(matches!(run(&f,&raw,query("ABC"),Scope::Document,all(),None,Form::Nfc),Err(E::NoChange)));
    for q in["^","^|à"]{assert!(matches!(run(&f,&raw,Query {mode:Mode::Regex,..query(q)},Scope::Document,all(),None,Form::Nfc),Err(E::Selection)));}Ok(())
}
#[test]
fn unicode_match_review_exclusion_precedes_limits_and_unmatched_cache_stays_frozen()->TestResult {
    let raw=fixture::package(&review::body().replace("K K","à"))?;let f=forms(&raw)?;
    for(h,m,n)in[(false,false,1),(true,false,2),(false,true,2),(true,true,3)]{let policy=Policy {include_hidden_explanations:h,include_memo_bodies:m};
        let c=run(&f,&raw,Query {max_results:n,..query("à")},Scope::Document,policy,None,Form::Nfc)?;let out=c.with_verified_bytes(section)??;
        assert_eq!(out.matches('à').count(),n);assert!(out.contains("CACHE FROZEN"));assert_eq!(c.receipt().search.search().result().matches().len(),n);
    }
    assert!(matches!(run(&f,&raw,query("FROZEN"),Scope::Document,all(),None,Form::Nfc),Err(E::FieldContent)));Ok(())
}
#[test]
fn unicode_match_selected_tab_is_retained_and_splits_normalization_groups()->TestResult {
    let text="a<hp:tab width='1' leader='0' type='0'> </hp:tab>̀à";let raw=fixture::package(&p(1,text))?;let f=forms(&raw)?;
    assert!(matches!(run(&f,&raw,Query {mode:Mode::Regex,..query("a\t̀à")},Scope::Document,all(),None,Form::Nfc),Err(E::NoMatches)));
    let c=run(&f,&raw,Query {mode:Mode::Regex,..query("a\t̀à")},Scope::Document,all(),None,Form::Nfc)?;
    exact(&raw,&c,text,&text.replace("̀à","̀à"))?;assert_eq!(c.receipt().output.normalized_text_groups,2);Ok(())
}
#[test]
fn unicode_match_protected_noops_reject_but_unmatched_protected_content_is_not_edited()->TestResult {
    let tracked=p(1,"ABC").replace("charPrIDRef='0'","charPrIDRef='0' charTcId='1'");let raw=fixture::package(&tracked)?;let f=forms(&raw)?;
    assert!(matches!(run(&f,&raw,query("ABC"),Scope::Document,all(),None,Form::Nfc),Err(E::Protection)));
    let body=p(1,"à")+&format!("<hp:p id='2'><hp:run>{}</hp:run></hp:p>",table::table(300).replace("lock='0'","lock='1'"));let raw=fixture::package(&body)?;let f=forms(&raw)?;
    let c=run(&f,&raw,query("à"),Scope::Document,all(),None,Form::Nfc)?;exact(&raw,&c,"à","à")?;Ok(())
}
#[test]
fn unicode_match_adjacent_occurrences_are_not_joined_into_one_compatibility_normalization_group()->TestResult {
    let raw=fixture::package(&p(1,"ㄱㅏ"))?;let f=forms(&raw)?;let q=Query {mode:Mode::Regex,..query(".")};let c=run(&f,&raw,q,Scope::Document,all(),None,Form::Nfkc)?;
    exact(&raw,&c,"ㄱㅏ","가")?;assert_eq!(c.receipt().output.normalized_text_groups,2);
    let c=run(&f,&raw,Query {query:".+",..q},Scope::Document,all(),None,Form::Nfkc)?;exact(&raw,&c,"ㄱㅏ","가")?;Ok(())
}
#[test]
fn unicode_match_partial_scope_preserves_unselected_decomposed_entity_bytes()->TestResult {
    let raw=fixture::package(&p(1,"à &#x65;&#x301;"))?;let f=forms(&raw)?;let inv=f.source_review_scope_index(&raw,Default::default())?.scope_inventory()?;let b=&inv.inventory.blocks[0];
    let start=Boundary {paragraph_handle:b.paragraph_handle.clone(),block_index:0,normalized_scalar:0};let end=Boundary {normalized_scalar:1,..start.clone()};
    let c=run(&f,&raw,Query {mode:Mode::Regex,..query("^à$")},Scope::Selection {index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},all(),None,Form::Nfc)?;
    exact(&raw,&c,"à &#x65;&#x301;","à &#x65;&#x301;")?;Ok(())
}
#[test]
fn unicode_match_original_proof_stale_source_and_invalid_filter_are_rejected()->TestResult {
    let raw=fixture::package(&p(1,"à"))?;let f=forms(&raw)?;let other=forms(&raw)?;let proof=f.reconstruct_source_for_verification(&raw)?;
    assert!(matches!(proof.lower_review_selector_unicode_matches(&other,query("à"),Scope::Document,all(),None,Form::Nfc,Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default()),Err(E::Source)));
    let changed=fixture::package(&p(1,"é"))?;assert!(matches!(run(&f,&changed,query("à"),Scope::Document,all(),None,Form::Nfc),Err(E::Source)));
    for filter in[Filter::Declared(Declared::default()),Filter::Definition(Definition {bold:Some(true),..Default::default()})]{assert!(matches!(run(&f,&raw,query("ABSENT"),Scope::Document,all(),Some(filter),Form::Nfc),Err(E::Search(Search::Filter))));}Ok(())
}
#[test]
fn unicode_match_pattern_match_expansion_receipt_and_writer_limits_return_no_partial_output()->TestResult {
    let raw=fixture::package(&p(1,"à à ﬃ"))?;let f=forms(&raw)?;
    assert!(matches!(run(&f,&raw,Query {max_results:1,..query("à")},Scope::Document,all(),None,Form::Nfc),Err(E::Search(Search::Limit))));
    assert!(matches!(run(&f,&raw,Query {mode:Mode::Regex,..query("(")},Scope::Document,all(),None,Form::Nfc),Err(E::Search(Search::Pattern))));
    assert!(f.lower_review_selector_unicode_matches(&raw,query("à"),Scope::Document,all(),None,Form::Nfc,Run::FirstOriginalRunRetainAllRuns,
        SourceSearchLimits::new(Config {result_bytes:1,..Default::default()})?,Default::default()).is_err());
    assert!(matches!(f.lower_review_selector_unicode_matches(&raw,query("à"),Scope::Document,all(),None,Form::Nfc,Run::FirstOriginalRunRetainAllRuns,Default::default(),
        WriterLimits::new(WriterLimitConfig {max_output_bytes:1,..Default::default()})?),Err(E::Writer)));
    let raw=fixture::package(&p(1,"ﬃ"))?;let f=forms(&raw)?;assert!(matches!(f.lower_review_selector_unicode_matches(&raw,query("ﬃ"),Scope::Document,all(),None,Form::Nfkd,Run::FirstOriginalRunRetainAllRuns,
        SourceSearchLimits::new(Config {decomposed_scalars:2,..Default::default()})?,Default::default()),Err(E::Limit)));Ok(())
}
#[test]
fn unicode_match_receipt_binds_query_filter_form_policy_and_does_not_disclose_source_text()->TestResult {
    let raw=fixture::package(&p(1,"PRIVATE-SOURCE à"))?;let original=raw.clone();let f=forms(&raw)?;let q=Query {mode:Mode::Regex,..query(".+")};
    let c=run(&f,&raw,q,Scope::Document,all(),None,Form::Nfc)?;let filter=Some(Filter::Declared(Declared {run_character_property:Some(0),..Default::default()}));
    let other=run(&f,&raw,q,Scope::Document,all(),filter,Form::Nfc)?;assert_ne!(c.receipt().request_sha256,other.receipt().request_sha256);
    let other=run(&f,&raw,query("à"),Scope::Document,all(),None,Form::Nfc)?;assert_ne!(c.receipt().request_sha256,other.receipt().request_sha256);
    let other=run(&f,&raw,q,Scope::Document,Policy {include_hidden_explanations:false,include_memo_bodies:false},None,Form::Nfc)?;assert_ne!(c.receipt().request_sha256,other.receipt().request_sha256);
    assert!(!serde_json::to_string(c.receipt())?.contains("PRIVATE-SOURCE"));assert!(!format!("{c:?}").contains("PRIVATE-SOURCE"));assert_eq!(raw,original);Ok(())
}
#[test]
fn unicode_match_many_matches_share_original_span_cache_and_part_guard()->TestResult {
    let raw=fixture::package(&p(1,&"à ".repeat(128)))?;let f=forms(&raw)?;let c=run(&f,&raw,query("à"),Scope::Document,all(),None,Form::Nfc)?;
    exact(&raw,&c,&"à ".repeat(128),&"à ".repeat(128))?;let r=&c.receipt().output;assert_eq!(r.normalized_text_groups,128);assert_eq!(r.changes.len(),1);assert_eq!(r.observed_protection_parts,1);
    let xml=PreservingXmlDocument::parse(section(&raw)?.as_bytes())?;assert_eq!(r.observed_protection_element_visits,xml.elements().len()*3);Ok(())
}
#[test]
fn unicode_match_named_character_and_paragraph_axes_are_explicit_not_effective_style_claims()->TestResult {
    let body="<hp:p id='1' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'><hp:t>à</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>à</hp:t></hp:run></hp:p>";
    let raw=fixture::package(body)?;let f=forms(&raw)?;let filter=Some(Filter::Definition(Definition {character_source:Some(Axis::NamedStyle),bold:Some(false),
        paragraph_source:Some(ParaAxis::NamedStyle),alignment:Some(Align::Justify),..Default::default()}));
    let c=run(&f,&raw,query("à"),Scope::Document,all(),filter,Form::Nfc)?;exact(&raw,&c,"à","à")?;assert_eq!(c.receipt().search.search().result().matches().len(),2);Ok(())
}
