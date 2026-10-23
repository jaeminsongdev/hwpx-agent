use hwpx_package::{BoundedZipReader,PreservingXmlDocument,WriterLimits,WriterLimitConfig,
    document_import::{ImportedSourcePackage,forms::ImportedDocumentForms,search::{SourceSearchQuery as Query,SourceSearchMode as SearchMode,
        SourceSearchError as Search,SourceSearchLimits,SourceSearchLimitConfig as Config,selector::{SourceIndexScopeSelector as Scope,SourceIndexBoundary as Boundary},
        reviews::{SourceReviewTextPolicy as Body,selector::styles::SourceReviewStyleFilter as Filter},inspection::{SourceDeclaredStyleFilter as Declared,
            definitions::{SourceDefinitionStyleFilter as Definition,CharacterDefinitionSource as Axis}},
        replacement::{SourceLiteralReplacementError as E,atoms::case::{SourceCaseConversionCandidate as Candidate,SourceCaseMode as Mode,
            SourceCasePolicy as Policy,SOURCE_CASE_CONVERSION_PROFILE}}}}};
use domain_ir::DocumentId;
use sha2::{Digest as _,Sha256};
use std::{error::Error,io::Cursor};
#[allow(dead_code)] #[path="support/search_definition_fixture.rs"] mod fixture;
#[allow(dead_code)] #[path="support/review_scope_fixture.rs"] mod review;
#[allow(dead_code)] #[path="support/document_import_review_assembly_fixture.rs"] mod assembly;
#[allow(dead_code)] #[path="support/review_cell_output_fixture.rs"] mod table;
type TestResult=Result<(),Box<dyn Error>>;
const POLICY:Policy=Policy::UnicodeDefaultEachMatchedTextGroup;
fn forms(raw:&[u8])->Result<ImportedDocumentForms,Box<dyn Error>> {Ok(ImportedDocumentForms::import(ImportedSourcePackage::import(raw,DocumentId::parse("case-source")?,Sha256::digest(raw).into(),Default::default())?)?)}
fn p(id:u32,text:&str)->String{format!("<hp:p id='{id}' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'><hp:t charStyleIDRef='0'>{text}</hp:t></hp:run></hp:p>")}
fn all()->Body{Body {include_hidden_explanations:true,include_memo_bodies:true}}
fn query(q:&str)->Query<'_>{Query {query:q,mode:SearchMode::Literal,case_sensitive:true,whole_word:false,max_results:10000}}
fn whole()->Query<'static>{Query {mode:SearchMode::Regex,..query("(?s:.+)")}}
fn convert(f:&ImportedDocumentForms,raw:&[u8],q:Query<'_>,scope:Scope<'_>,body:Body,filter:Option<Filter>,mode:Mode)->Result<Candidate,E>{
    f.lower_review_selector_case_candidate(raw,q,scope,body,filter,mode,POLICY,Default::default(),Default::default())}
fn section(raw:&[u8])->Result<String,Box<dyn Error>>{let mut zip=BoundedZipReader::open(Cursor::new(raw),Default::default())?;
    let i=zip.entries().iter().position(|e|e.path.as_str()=="Contents/section0.xml").ok_or("section")?;Ok(String::from_utf8(zip.read_entry(i)?)?)}
fn exact(raw:&[u8],candidate:&Candidate,old:&str,new:&str)->TestResult{
    let bytes=candidate.with_verified_bytes(<[u8]>::to_vec)?;assert_eq!(section(&bytes)?,section(raw)?.replace(old,new));
    let mut a=BoundedZipReader::open(Cursor::new(raw),Default::default())?;let mut b=BoundedZipReader::open(Cursor::new(&bytes),Default::default())?;
    assert_eq!(a.entries().len(),b.entries().len());for i in 0..a.entries().len(){let path=a.entries()[i].path.clone();if path.as_str()=="Contents/section0.xml"{continue;}
        let j=b.entries().iter().position(|e|e.path==path).ok_or("part")?;assert_eq!(a.read_entry(i)?,b.read_entry(j)?);}
    let r=candidate.receipt();assert_eq!(r.profile,SOURCE_CASE_CONVERSION_PROFILE);assert_eq!(r.case_unicode_version,(17,0,0));assert_eq!(r.policy,POLICY);
    assert!(r.exact_original_selection_verified&&r.every_original_scalar_retains_its_text_atom_style&&r.original_controls_and_reference_shells_preserved
        &&r.whole_string_mapping_and_scalar_partition_verified&&r.output_spans_and_outside_slots_verified);
    assert!(!r.locale_tailoring_titlecase_casefold_normalization_native_or_service_authority);Ok(())
}
#[test]
fn case_ascii_changed_neighbors_coalesce_into_one_original_atom_range()->TestResult{
    let raw=fixture::package(&p(1,"abc XYZ"))?;let f=forms(&raw)?;
    let upper=convert(&f,&raw,whole(),Scope::Document,all(),None,Mode::Uppercase)?;exact(&raw,&upper,"abc XYZ","ABC XYZ")?;
    let lower=convert(&f,&raw,whole(),Scope::Document,all(),None,Mode::Lowercase)?;exact(&raw,&lower,"abc XYZ","abc xyz")?;
    assert_eq!(upper.receipt().changed_components,1);assert_eq!(upper.receipt().changed_scalar_ranges,1);Ok(())
}
#[test]
fn case_upper_full_mapping_expands_sharp_s_ligature_and_j_with_caron()->TestResult{
    let raw=fixture::package(&p(1,"straße ﬃ ǰ"))?;let f=forms(&raw)?;let c=convert(&f,&raw,whole(),Scope::Document,all(),None,Mode::Uppercase)?;
    exact(&raw,&c,"straße ﬃ ǰ","STRASSE FFI J̌")?;assert!(c.receipt().mapped_scalars>c.receipt().selected_original_scalars);Ok(())
}
#[test]
fn case_lower_default_dotted_i_is_not_a_turkish_or_azeri_tailoring()->TestResult{
    let raw=fixture::package(&p(1,"Iİıi"))?;let f=forms(&raw)?;let c=convert(&f,&raw,whole(),Scope::Document,all(),None,Mode::Lowercase)?;
    exact(&raw,&c,"Iİıi","ii̇ıi")?;assert_eq!(c.receipt().mapped_scalars,5);Ok(())
}
#[test]
fn case_lower_final_sigma_respects_case_ignorable_and_overlapping_cased_properties()->TestResult{
    for(before,after)in[("AΣ","aς"),("ΣA","σa"),("Σ","σ"),("AΣA","aσa"),("AΣ'́","aς'́"),("ͅΣ","ͅσ"),("AΣͅ","aςͅ"),("AΣͅA","aσͅa")]{
        let raw=fixture::package(&p(1,before))?;let f=forms(&raw)?;let c=convert(&f,&raw,whole(),Scope::Document,all(),None,Mode::Lowercase)?;exact(&raw,&c,before,after)?;
    }Ok(())
}
#[test]
fn case_lower_sigma_context_crosses_runs_without_moving_their_individual_styles()->TestResult{
    let body="<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>A</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t charStyleIDRef='1'>Σ</hp:t></hp:run><hp:run><hp:t>ͅ</hp:t></hp:run></hp:p>";
    let raw=fixture::package(body)?;let f=forms(&raw)?;let c=convert(&f,&raw,whole(),Scope::Document,all(),None,Mode::Lowercase)?;
    exact(&raw,&c,body,&body.replace(">A<",">a<").replace(">Σ<",">ς<"))?;assert_eq!(c.receipt().changes.len(),2);Ok(())
}
#[test]
fn case_expansion_stays_in_original_text_atom_and_unselected_entities_remain_exact()->TestResult{
    let body="<hp:p id='1'><hp:run charPrIDRef='0'><hp:t charStyleIDRef='0'>A&#x26;</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t charStyleIDRef='1'>ß</hp:t></hp:run><hp:run><hp:t>&#x1F600;B</hp:t></hp:run></hp:p>";
    let raw=fixture::package(body)?;let f=forms(&raw)?;let c=convert(&f,&raw,whole(),Scope::Document,all(),None,Mode::Uppercase)?;
    exact(&raw,&c,">ß<",">SS<")?;assert_eq!(c.receipt().changes.len(),1);Ok(())
}
#[test]
fn case_does_not_silently_normalize_combining_text_or_change_uncased_scripts()->TestResult{
    let text="a&#x300; 한글😀";let raw=fixture::package(&p(1,text))?;let f=forms(&raw)?;let c=convert(&f,&raw,whole(),Scope::Document,all(),None,Mode::Uppercase)?;
    exact(&raw,&c,text,"A&#x300; 한글😀")?;assert_eq!(c.receipt().changed_scalar_ranges,1);Ok(())
}
#[test]
fn case_regex_casefold_and_whole_word_select_but_do_not_rewrite_unmatched_text()->TestResult{
    let raw=fixture::package(&p(1,"Cat scatter CAT"))?;let f=forms(&raw)?;let q=Query {mode:SearchMode::Regex,case_sensitive:false,whole_word:true,..query("c[a]t")};
    let c=convert(&f,&raw,q,Scope::Document,all(),None,Mode::Uppercase)?;exact(&raw,&c,"Cat scatter CAT","CAT scatter CAT")?;
    assert_eq!(c.receipt().search.search().result().matches().len(),2);assert_eq!(c.receipt().changed_components,1);Ok(())
}
#[test]
fn case_four_selectors_keep_clipped_regex_and_original_scope_boundaries()->TestResult{
    let raw=fixture::package(&(p(1,"X abc Z")+&p(2,"Y abc Z")))?;let f=forms(&raw)?;let inv=f.source_review_scope_index(&raw,Default::default())?.scope_inventory()?;let b=&inv.inventory.blocks[0];
    let ids=[inv.inventory.nodes.iter().find(|n|n.source_handle==b.paragraph_handle).ok_or("node")?.node_id.clone()];
    let start=Boundary {paragraph_handle:b.paragraph_handle.clone(),block_index:0,normalized_scalar:2};let end=Boundary {normalized_scalar:5,..start.clone()};
    for(scope,n)in[(Scope::Document,2),(Scope::Section(&inv.inventory.section_ids),2),(Scope::NodeSet(&ids),1),(Scope::Selection {index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},1)]{
        let q=if matches!(scope,Scope::Selection {..}){Query {mode:SearchMode::Regex,..query("^abc$")}}else{query("abc")};let c=convert(&f,&raw,q,scope,all(),None,Mode::Uppercase)?;
        let out=c.with_verified_bytes(section)??;assert!(out.contains("X ABC Z"));assert_eq!(out.contains("Y abc Z"),n==1);assert_eq!(c.receipt().search.search().result().matches().len(),n);
    }Ok(())
}
#[test]
fn case_declared_and_definition_filters_cover_all_original_contributors_before_limits()->TestResult{
    let body="<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>a</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>bc abc</hp:t></hp:run></hp:p>";
    let raw=fixture::package(body)?;let f=forms(&raw)?;
    for filter in[Filter::Declared(Declared {run_character_property:Some(1),..Default::default()}),Filter::Definition(Definition {character_source:Some(Axis::RunProperty),bold:Some(true),..Default::default()})]{
        let c=convert(&f,&raw,Query {max_results:1,..query("abc")},Scope::Document,all(),Some(filter),Mode::Uppercase)?;exact(&raw,&c,">bc abc<",">bc ABC<")?;
        assert_eq!(c.receipt().search.search().result().matches().len(),1);
    }Ok(())
}
#[test]
fn case_review_policy_excludes_before_caps_and_retains_cache_and_metadata()->TestResult{
    let raw=fixture::package(&review::body())?;let f=forms(&raw)?;
    for(h,m,n)in[(false,false,2),(true,false,4),(false,true,4),(true,true,6)]{let c=convert(&f,&raw,Query {max_results:n,..query("K")},Scope::Document,Body {include_hidden_explanations:h,include_memo_bodies:m},None,Mode::Lowercase)?;
        let mut expected=review::body().replace("BODY K K","BODY k k");
        if h{expected=expected.replace("HIDDEN K K","HIDDEN k k");}if m{expected=expected.replace("MEMO K K","MEMO k k");}
        exact(&raw,&c,&review::body(),&expected)?;
        let out=c.with_verified_bytes(section)??;assert!(out.contains("CACHE FROZEN"));assert!(out.contains("PRIVATE-AUTHOR"));
        assert_eq!(c.receipt().search.search().result().matches().len(),n);
    }Ok(())
}
#[test]
fn case_tabs_and_paired_linebreaks_are_immutable_context_barriers()->TestResult{
    let text="A<hp:tab width='1' leader='0' type='0'> </hp:tab>Σ<hp:lineBreak> </hp:lineBreak>AΣ";
    let raw=fixture::package(&p(1,text))?;let f=forms(&raw)?;let c=convert(&f,&raw,whole(),Scope::Document,all(),None,Mode::Lowercase)?;
    exact(&raw,&c,text,&text.replace("A<","a<").replace(">Σ<",">σ<").replace(">AΣ",">aς"))?;assert_eq!(c.receipt().converted_text_groups,3);Ok(())
}
#[test]
fn case_context_is_explicitly_match_local_and_adjacent_matches_do_not_merge()->TestResult{
    let raw=fixture::package(&p(1,"AΣ"))?;let f=forms(&raw)?;let c=convert(&f,&raw,query("Σ"),Scope::Document,all(),None,Mode::Lowercase)?;exact(&raw,&c,"AΣ","Aσ")?;
    let c=convert(&f,&raw,Query {mode:SearchMode::Regex,..query(".")},Scope::Document,all(),None,Mode::Lowercase)?;exact(&raw,&c,"AΣ","aσ")?;
    let c=convert(&f,&raw,whole(),Scope::Document,all(),None,Mode::Lowercase)?;exact(&raw,&c,"AΣ","aς")?;Ok(())
}
#[test]
fn case_partial_and_noncontiguous_normalized_inverses_are_rejected_without_widening()->TestResult{
    for(text,q)in[("&#x344;ABC","\u{308}"),("à̕","à")]{let raw=fixture::package(&p(1,text))?;let f=forms(&raw)?;
        assert!(matches!(convert(&f,&raw,query(q),Scope::Document,all(),None,Mode::Uppercase),Err(E::Selection)));}Ok(())
}
#[test]
fn case_no_matches_no_change_and_zero_width_are_distinct_failures()->TestResult{
    let raw=fixture::package(&p(1,"ABC"))?;let f=forms(&raw)?;
    assert!(matches!(convert(&f,&raw,query("ABSENT"),Scope::Document,all(),None,Mode::Uppercase),Err(E::NoMatches)));
    assert!(matches!(convert(&f,&raw,query("ABC"),Scope::Document,all(),None,Mode::Uppercase),Err(E::NoChange)));
    assert!(matches!(convert(&f,&raw,Query {mode:SearchMode::Regex,..query("^|ABC")},Scope::Document,all(),None,Mode::Lowercase),Err(E::Selection)));Ok(())
}
#[test]
fn case_protected_noops_reject_but_unmatched_protected_content_is_not_touched()->TestResult{
    let tracked=p(1,"ABC").replace("charPrIDRef='0'","charPrIDRef='0' charTcId='1'");let raw=fixture::package(&tracked)?;let f=forms(&raw)?;
    assert!(matches!(convert(&f,&raw,query("ABC"),Scope::Document,all(),None,Mode::Uppercase),Err(E::Protection)));
    let raw=fixture::package(&(p(1,"abc")+&format!("<hp:p id='2'><hp:run>{}</hp:run></hp:p>",table::table(300).replace("lock='0'","lock='1'"))))?;let f=forms(&raw)?;
    assert!(matches!(convert(&f,&raw,query("CELL"),Scope::Document,all(),None,Mode::Uppercase),Err(E::Protection)));
    let c=convert(&f,&raw,query("abc"),Scope::Document,all(),None,Mode::Uppercase)?;exact(&raw,&c,"abc","ABC")?;Ok(())
}
#[test]
fn case_matching_field_cache_is_blocked_even_when_mapping_would_be_a_noop()->TestResult{
    let raw=fixture::package(&review::body())?;let f=forms(&raw)?;
    assert!(matches!(convert(&f,&raw,query("FROZEN"),Scope::Document,all(),None,Mode::Uppercase),Err(E::FieldContent)));
    let c=convert(&f,&raw,query("K"),Scope::Document,all(),None,Mode::Lowercase)?;assert!(c.with_verified_bytes(section)??.contains("CACHE FROZEN"));Ok(())
}
#[test]
fn case_original_proof_stale_source_and_invalid_filters_fail_before_success()->TestResult{
    let raw=fixture::package(&p(1,"abc"))?;let f=forms(&raw)?;let other=forms(&raw)?;let proof=f.reconstruct_source_for_verification(&raw)?;
    assert!(matches!(proof.lower_review_selector_case_candidate(&other,whole(),Scope::Document,all(),None,Mode::Uppercase,POLICY,Default::default(),Default::default()),Err(E::Source)));
    let changed=fixture::package(&p(1,"xyz"))?;assert!(matches!(convert(&f,&changed,whole(),Scope::Document,all(),None,Mode::Uppercase),Err(E::Source)));
    for filter in[Filter::Declared(Declared::default()),Filter::Definition(Definition {bold:Some(true),..Default::default()})]{assert!(matches!(convert(&f,&raw,query("ABSENT"),Scope::Document,all(),Some(filter),Mode::Uppercase),Err(E::Search(Search::Filter))));}Ok(())
}
#[test]
fn case_pattern_match_mapping_response_and_writer_caps_never_return_partial_candidates()->TestResult{
    let raw=fixture::package(&p(1,"abc abc"))?;let f=forms(&raw)?;
    assert!(matches!(convert(&f,&raw,Query {mode:SearchMode::Regex,..query("(")},Scope::Document,all(),None,Mode::Uppercase),Err(E::Search(Search::Pattern))));
    assert!(matches!(convert(&f,&raw,Query {max_results:1,..query("abc")},Scope::Document,all(),None,Mode::Uppercase),Err(E::Search(Search::Limit))));
    assert!(f.lower_review_selector_case_candidate(&raw,query("abc"),Scope::Document,all(),None,Mode::Uppercase,POLICY,SourceSearchLimits::new(Config {result_bytes:1,..Default::default()})?,Default::default()).is_err());
    assert!(matches!(f.lower_review_selector_case_candidate(&raw,query("abc"),Scope::Document,all(),None,Mode::Uppercase,POLICY,Default::default(),WriterLimits::new(WriterLimitConfig {max_output_bytes:1,..Default::default()})?),Err(E::Writer)));
    let raw=fixture::package(&p(1,"ß"))?;let f=forms(&raw)?;assert!(matches!(f.lower_review_selector_case_candidate(&raw,query("ß"),Scope::Document,all(),None,Mode::Uppercase,POLICY,
        SourceSearchLimits::new(Config {decomposed_scalars:1,..Default::default()})?,Default::default()),Err(E::Limit)));Ok(())
}
#[test]
fn case_long_ascii_word_is_one_patch_not_one_patch_per_character()->TestResult{
    let text="a".repeat(20000);let raw=fixture::package(&p(1,&text))?;let f=forms(&raw)?;let limits=SourceSearchLimits::new(Config {matches:1,..Default::default()})?;
    let c=f.lower_review_selector_case_candidate(&raw,Query {max_results:1,..whole()},Scope::Document,all(),None,Mode::Uppercase,POLICY,limits,Default::default())?;
    exact(&raw,&c,&text,&"A".repeat(20000))?;assert_eq!(c.receipt().changed_components,1);assert_eq!(c.receipt().changed_scalar_ranges,1);
    assert_eq!(c.receipt().selected_original_scalars,20000);let xml=PreservingXmlDocument::parse(section(&raw)?.as_bytes())?;assert_eq!(c.receipt().observed_protection_element_visits,xml.elements().len()*3);Ok(())
}
#[test]
fn case_long_ignorable_context_uses_whole_group_mapping_with_two_original_change_ranges()->TestResult{
    let marks="́".repeat(4096);let text=format!("AΣ{marks}Σ");let raw=fixture::package(&p(1,&text))?;let f=forms(&raw)?;
    let c=convert(&f,&raw,whole(),Scope::Document,all(),None,Mode::Lowercase)?;exact(&raw,&c,&text,&format!("aσ{marks}ς"))?;assert_eq!(c.receipt().changed_scalar_ranges,2);Ok(())
}
#[test]
fn case_multiscript_default_case_is_not_casefold_and_receipts_do_not_disclose_source()->TestResult{
    for(text,lower,upper)in[("Ꭰꭰ","ꭰꭰ","ᎠᎠ"),("𐐀𐐨","𐐨𐐨","𐐀𐐀"),("Აა","აა","ᲐᲐ"),("Ａａ","ａａ","ＡＡ"),("ς ẞ ß","ς ß ß","Σ ẞ SS")]{
        let raw=fixture::package(&p(1,text))?;let f=forms(&raw)?;for(mode,expected)in[(Mode::Lowercase,lower),(Mode::Uppercase,upper)]{let c=convert(&f,&raw,whole(),Scope::Document,all(),None,mode)?;exact(&raw,&c,text,expected)?;}}
    let raw=fixture::package(&p(1,"PRIVATE-SOURCE abc"))?;let original=raw.clone();let f=forms(&raw)?;let c=convert(&f,&raw,whole(),Scope::Document,all(),None,Mode::Uppercase)?;
    assert!(!serde_json::to_string(c.receipt())?.contains("PRIVATE-SOURCE"));assert!(!format!("{c:?}").contains("PRIVATE-SOURCE"));assert_eq!(raw,original);Ok(())
}
