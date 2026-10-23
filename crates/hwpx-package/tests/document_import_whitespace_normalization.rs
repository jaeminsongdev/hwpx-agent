use hwpx_package::{BoundedZipReader,PreservingXmlDocument,WriterLimits,WriterLimitConfig,
    document_import::{ImportedSourcePackage,forms::ImportedDocumentForms,search::{SourceSearchQuery as Query,SourceSearchMode as Mode,
        SourceSearchError as Search,SourceSearchLimits,SourceSearchLimitConfig as Config,selector::{SourceIndexScopeSelector as Scope,SourceIndexBoundary as Boundary},
        reviews::{SourceReviewTextPolicy as Body,selector::styles::SourceReviewStyleFilter as Filter},inspection::{SourceDeclaredStyleFilter as Declared,
            definitions::{SourceDefinitionStyleFilter as Definition,CharacterDefinitionSource as Axis}},
        replacement::{SourceLiteralReplacementError as E,SourceReplacementRunPolicy as Run,atoms::whitespace::{SourceWhitespaceNormalizationCandidate as Candidate,
            SourceWhitespacePolicy as Policy,SourceWhitespaceTextPolicy as Text,SourceWhitespaceSequencePolicy as Sequence,SourceWhitespaceOutput as Out,SOURCE_WHITESPACE_NORMALIZATION_PROFILE}}}}};
use domain_ir::DocumentId;
use sha2::{Digest as _,Sha256};
use std::{error::Error,io::Cursor};
#[allow(dead_code)] #[path="support/search_definition_fixture.rs"] mod fixture;
#[allow(dead_code)] #[path="support/review_scope_fixture.rs"] mod review;
#[allow(dead_code)] #[path="support/document_import_review_assembly_fixture.rs"] mod assembly;
#[allow(dead_code)] #[path="support/review_cell_output_fixture.rs"] mod table;
#[path="../src/document_import/search/replacement/atoms/whitespace/lexical.rs"] mod lexical;
type TestResult=Result<(),Box<dyn Error>>;
const RUN:Run=Run::FirstOriginalRunRetainAllRuns;
fn policy()->Policy{Policy{text:Text::AsciiSpace,tabs:true,line_breaks:true,sequence:Sequence::CollapseEachMatchedSequence,output:Out::Spaces{count:1}}}
fn forms(raw:&[u8])->Result<ImportedDocumentForms,Box<dyn Error>>{Ok(ImportedDocumentForms::import(ImportedSourcePackage::import(raw,DocumentId::parse("whitespace-source")?,Sha256::digest(raw).into(),Default::default())?)?)}
fn p(id:u32,text:&str)->String{format!("<hp:p id='{id}' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'><hp:t charStyleIDRef='0'>{text}</hp:t></hp:run></hp:p>")}
fn all()->Body{Body{include_hidden_explanations:true,include_memo_bodies:true}}
fn query(q:&str)->Query<'_>{Query{query:q,mode:Mode::Literal,case_sensitive:true,whole_word:false,max_results:10000}}
fn whole()->Query<'static>{Query{mode:Mode::Regex,..query("(?s:.+)")}}
fn normalize(f:&ImportedDocumentForms,raw:&[u8],q:Query<'_>,scope:Scope<'_>,body:Body,filter:Option<Filter>,policy:Policy)->Result<Candidate,E>{
    f.lower_review_selector_whitespace_candidate(raw,q,scope,body,filter,policy,RUN,Default::default(),Default::default())}
fn section(raw:&[u8])->Result<String,Box<dyn Error>>{let mut zip=BoundedZipReader::open(Cursor::new(raw),Default::default())?;
    let i=zip.entries().iter().position(|e|e.path.as_str()=="Contents/section0.xml").ok_or("section")?;Ok(String::from_utf8(zip.read_entry(i)?)?)}
fn output(raw:&[u8],c:&Candidate)->Result<Vec<u8>,Box<dyn Error>>{let bytes=c.with_verified_bytes(<[u8]>::to_vec)?;
    let mut a=BoundedZipReader::open(Cursor::new(raw),Default::default())?;let mut b=BoundedZipReader::open(Cursor::new(&bytes),Default::default())?;
    assert_eq!(a.entries().len(),b.entries().len());for i in 0..a.entries().len(){let path=a.entries()[i].path.clone();if path.as_str()=="Contents/section0.xml"{continue;}
        let j=b.entries().iter().position(|e|e.path==path).ok_or("part")?;assert_eq!(a.read_entry(i)?,b.read_entry(j)?);}
    let r=c.receipt();assert_eq!(r.profile,SOURCE_WHITESPACE_NORMALIZATION_PROFILE);assert_eq!(r.run_policy,RUN);
    assert!(r.exact_original_selection_verified&&r.original_run_shells_styles_references_and_non_whitespace_preserved&&r.output_uses_first_original_contributor
        &&r.output_spans_and_exact_outside_edits_verified);assert!(!r.full_contract_native_service_or_execution_authority);Ok(bytes)}
fn exact(raw:&[u8],c:&Candidate,old:&str,new:&str)->TestResult{assert_eq!(section(&output(raw,c)?)?,section(raw)?.replace(old,new));Ok(())}
#[test]
fn whitespace_collapse_preserves_letters_entities_styles_and_other_zip_entries()->TestResult{
    let text="&#x1F600;A   &amp;  B&#32;C";let raw=fixture::package(&p(1,text))?;let f=forms(&raw)?;
    let c=normalize(&f,&raw,whole(),Scope::Document,all(),None,policy())?;exact(&raw,&c,text,"&#x1F600;A &amp; B&#32;C")?;assert_eq!(c.receipt().changed_scalar_ranges,2);Ok(())
}
#[test]
fn whitespace_collapse_across_text_tab_linebreak_and_run_boundaries_uses_first_contributor()->TestResult{
    let body="<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>A  <hp:tab width='9' leader='2' type='1'> </hp:tab></hp:t></hp:run><hp:run charPrIDRef='1'><hp:t charStyleIDRef='1'><hp:lineBreak> </hp:lineBreak> B</hp:t></hp:run></hp:p>";
    let raw=fixture::package(body)?;let f=forms(&raw)?;let c=normalize(&f,&raw,whole(),Scope::Document,all(),None,policy())?;
    exact(&raw,&c,body,&body.replace("A  <hp:tab width='9' leader='2' type='1'> </hp:tab>","A ").replace("<hp:lineBreak> </hp:lineBreak> B","B"))?;
    assert_eq!(c.receipt().changed_original_controls,2);assert_eq!(c.receipt().changes.len(),2);Ok(())
}
#[test]
fn whitespace_control_removal_merges_parsed_text_but_preserves_lexical_entities()->TestResult{
    let text="A&#32;<hp:tab width='1' leader='0' type='0'/>B<hp:lineBreak/>C";let raw=fixture::package(&p(1,text))?;let f=forms(&raw)?;
    let c=normalize(&f,&raw,whole(),Scope::Document,all(),None,Policy{text:Text::None,output:Out::Remove,..policy()})?;
    exact(&raw,&c,text,"A&#32;BC")?;assert_eq!(c.receipt().changed_original_controls,2);Ok(())
}
#[test]
fn whitespace_text_to_typed_controls_shifts_later_element_indices_without_losing_readback()->TestResult{
    let body=p(1,"A  B  C")+&p(2,"D  E");let raw=fixture::package(&body)?;let f=forms(&raw)?;
    for(out,render)in[(Out::LineBreak,"<hp:lineBreak/>"),(Out::Tab{width:123,leader:2,tab_type:1},"<hp:tab width=\"123\" leader=\"2\" type=\"1\"/>")]{
        let c=normalize(&f,&raw,whole(),Scope::Document,all(),None,Policy{output:out,..policy()})?;exact(&raw,&c,&body,&body.replace("  ",render))?;assert_eq!(c.receipt().changes.len(),2);}Ok(())
}
#[test]
fn whitespace_unselected_or_semantically_unchanged_control_lexemes_are_exact()->TestResult{
    let text="A<hp:tab width='1' leader='0' type='0'> </hp:tab> B  C<hp:lineBreak> </hp:lineBreak>D";let raw=fixture::package(&p(1,text))?;let f=forms(&raw)?;
    let c=normalize(&f,&raw,whole(),Scope::Document,all(),None,Policy{tabs:false,line_breaks:false,..policy()})?;exact(&raw,&c,text,&text.replace("B  C","B C"))?;
    let c=normalize(&f,&raw,query("\t "),Scope::Document,all(),None,Policy{output:Out::Tab{width:1,leader:0,tab_type:0},..policy()})?;
    exact(&raw,&c,"</hp:tab> B","</hp:tab>B")?;assert_eq!(c.receipt().changed_original_controls,0);Ok(())
}
#[test]
fn whitespace_unicode17_all19_and_breaking16_have_explicit_nonbreaking_exclusions()->TestResult{
    let points=[0x20,0xa0,0x1680,0x2000,0x2001,0x2002,0x2003,0x2004,0x2005,0x2006,0x2007,0x2008,0x2009,0x200a,0x2028,0x2029,0x202f,0x205f,0x3000];
    let input=points.iter().map(|&n|format!("X{}",char::from_u32(n).expect("scalar"))).collect::<String>()+"X\u{200b}\u{feff}";
    let raw=fixture::package(&p(1,&input))?;let f=forms(&raw)?;
    for text in[Text::AsciiSpace,Text::Unicode17Breaking,Text::Unicode17AllModelAdmitted]{let expected=points.iter().map(|&n|{
        let replace=match text{Text::AsciiSpace=>n==0x20,Text::Unicode17Breaking=>!matches!(n,0xa0|0x2007|0x202f),_=>true};
        format!("X{}",if replace{String::new()}else{char::from_u32(n).expect("scalar").to_string()})}).collect::<String>()+"X\u{200b}\u{feff}";
        let c=normalize(&f,&raw,whole(),Scope::Document,all(),None,Policy{text,output:Out::Remove,..policy()})?;exact(&raw,&c,&input,&expected)?;}Ok(())
}
#[test]
fn whitespace_each_scalar_vs_collapsed_sequence_and_separate_matches_are_distinct()->TestResult{
    let raw=fixture::package(&p(1,"A  B"))?;let f=forms(&raw)?;
    let c=normalize(&f,&raw,whole(),Scope::Document,all(),None,Policy{sequence:Sequence::EachOriginalScalar,output:Out::Spaces{count:2},..policy()})?;exact(&raw,&c,"A  B","A    B")?;
    let c=normalize(&f,&raw,Query{mode:Mode::Regex,..query(" ")},Scope::Document,all(),None,Policy{output:Out::Spaces{count:2},..policy()})?;exact(&raw,&c,"A  B","A    B")?;
    let c=normalize(&f,&raw,whole(),Scope::Document,all(),None,policy())?;exact(&raw,&c,"A  B","A B")?;Ok(())
}
#[test]
fn whitespace_preserved_controls_are_sequence_barriers_and_paragraphs_never_merge()->TestResult{
    let text="A  <hp:lineBreak/>  B";let body=p(1,text)+&p(2,"  C");let raw=fixture::package(&body)?;let f=forms(&raw)?;
    let c=normalize(&f,&raw,whole(),Scope::Document,all(),None,Policy{line_breaks:false,..policy()})?;
    exact(&raw,&c,&body,&body.replace("  "," "))?;assert_eq!(c.receipt().whitespace_sequences,3);assert_eq!(c.receipt().changed_original_controls,0);Ok(())
}
#[test]
fn whitespace_four_selectors_keep_clipped_regex_and_exact_original_windows()->TestResult{
    let raw=fixture::package(&(p(1,"A  B")+&p(2,"C  D")))?;let f=forms(&raw)?;let inv=f.source_review_scope_index(&raw,Default::default())?.scope_inventory()?;
    let b=&inv.inventory.blocks[0];let ids=[inv.inventory.nodes.iter().find(|n|n.source_handle==b.paragraph_handle).ok_or("node")?.node_id.clone()];
    let start=Boundary{paragraph_handle:b.paragraph_handle.clone(),block_index:0,normalized_scalar:1};let end=Boundary{normalized_scalar:3,..start.clone()};
    for(scope,n)in[(Scope::Document,2),(Scope::Section(&inv.inventory.section_ids),2),(Scope::NodeSet(&ids),1),(Scope::Selection{index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},1)]{
        let q=if matches!(scope,Scope::Selection{..}){Query{mode:Mode::Regex,..query("^  $")}}else{query("  ")};
        let c=normalize(&f,&raw,q,scope,all(),None,policy())?;let out=section(&output(&raw,&c)?)?;assert!(out.contains("A B"));assert_eq!(out.contains("C  D"),n==1);assert_eq!(c.receipt().search.search().result().matches().len(),n);}Ok(())
}
#[test]
fn whitespace_declared_and_definition_filters_admit_only_all_contributors()->TestResult{
    let body="<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>A </hp:t></hp:run><hp:run charPrIDRef='1'><hp:t> B  C</hp:t></hp:run></hp:p>";
    let raw=fixture::package(body)?;let f=forms(&raw)?;
    for filter in[Filter::Declared(Declared{run_character_property:Some(1),..Default::default()}),Filter::Definition(Definition{character_source:Some(Axis::RunProperty),bold:Some(true),..Default::default()})]{
        let c=normalize(&f,&raw,query("  "),Scope::Document,all(),Some(filter),policy())?;exact(&raw,&c,"B  C","B C")?;assert_eq!(c.receipt().search.search().result().matches().len(),1);}Ok(())
}
#[test]
fn whitespace_review_exclusions_precede_caps_and_metadata_cache_remain_exact()->TestResult{
    let body=review::body().replace("K K","K  K");let raw=fixture::package(&body)?;let f=forms(&raw)?;
    for(h,m,n)in[(false,false,1),(true,false,2),(false,true,2),(true,true,3)]{let c=normalize(&f,&raw,Query{max_results:n,..query("  ")},Scope::Document,
        Body{include_hidden_explanations:h,include_memo_bodies:m},None,Policy{output:Out::LineBreak,..policy()})?;
        let mut expected=body.replace("BODY K  K","BODY K<hp:lineBreak/>K");if h{expected=expected.replace("HIDDEN K  K","HIDDEN K<hp:lineBreak/>K");}if m{expected=expected.replace("MEMO K  K","MEMO K<hp:lineBreak/>K");}
        exact(&raw,&c,&body,&expected)?;assert_eq!(c.receipt().search.search().result().matches().len(),n);}Ok(())
}
#[test]
fn whitespace_field_cache_and_tracked_noops_are_rejected_before_discarding_edits()->TestResult{
    let raw=fixture::package(&review::body())?;let f=forms(&raw)?;assert!(matches!(normalize(&f,&raw,query("FROZEN"),Scope::Document,all(),None,policy()),Err(E::FieldContent)));
    for marker in["charTcId='1'","paraTcId='1'"]{let body=if marker.starts_with("char"){p(1,"A B").replace("charPrIDRef='0'",&format!("charPrIDRef='0' {marker}"))}else{p(1,"A B").replace("paraPrIDRef='0'",&format!("paraPrIDRef='0' {marker}"))};
        let raw=fixture::package(&body)?;let f=forms(&raw)?;assert!(matches!(normalize(&f,&raw,whole(),Scope::Document,all(),None,policy()),Err(E::Protection)));}Ok(())
}
#[test]
fn whitespace_protected_table_selection_rejects_and_unselected_table_is_exact()->TestResult{
    let body=p(1,"A  B")+&format!("<hp:p id='2'><hp:run>{}</hp:run></hp:p>",table::table(300).replace("lock='0'","lock='1'"));let raw=fixture::package(&body)?;let f=forms(&raw)?;
    assert!(matches!(normalize(&f,&raw,query("CELL"),Scope::Document,all(),None,policy()),Err(E::Protection)));
    let c=normalize(&f,&raw,query("A  B"),Scope::Document,all(),None,policy())?;exact(&raw,&c,"A  B","A B")?;Ok(())
}
#[test]
fn whitespace_original_proof_wrong_instance_and_stale_source_never_produce_candidate()->TestResult{
    let raw=fixture::package(&p(1,"A  B"))?;let f=forms(&raw)?;let other=forms(&raw)?;let proof=f.reconstruct_source_for_verification(&raw)?;
    assert!(matches!(proof.lower_review_selector_whitespace_candidate(&other,whole(),Scope::Document,all(),None,policy(),RUN,Default::default(),Default::default()),Err(E::Source)));
    let changed=fixture::package(&p(1,"C  D"))?;assert!(matches!(normalize(&f,&changed,whole(),Scope::Document,all(),None,policy()),Err(E::Source)));Ok(())
}
#[test]
fn whitespace_partial_noncontiguous_nfc_and_zero_width_inverses_are_rejected()->TestResult{
    for(text,q)in[("&#x344;  A","\u{308}"),("à̕  ","à")]{let raw=fixture::package(&p(1,text))?;let f=forms(&raw)?;assert!(matches!(normalize(&f,&raw,query(q),Scope::Document,all(),None,policy()),Err(E::Selection)));}
    let raw=fixture::package(&p(1,"A  B"))?;let f=forms(&raw)?;assert!(matches!(normalize(&f,&raw,Query{mode:Mode::Regex,..query("^|  ")},Scope::Document,all(),None,policy()),Err(E::Selection)));Ok(())
}
#[test]
fn whitespace_no_matches_no_change_and_invalid_policies_are_distinct()->TestResult{
    let raw=fixture::package(&p(1,"A B"))?;let f=forms(&raw)?;assert!(matches!(normalize(&f,&raw,query("ABSENT"),Scope::Document,all(),None,policy()),Err(E::NoMatches)));
    assert!(matches!(normalize(&f,&raw,whole(),Scope::Document,all(),None,policy()),Err(E::NoChange)));
    for invalid in[Policy{text:Text::None,tabs:false,line_breaks:false,..policy()},Policy{output:Out::Spaces{count:0},..policy()},Policy{output:Out::Spaces{count:1025},..policy()}]{
        assert!(matches!(normalize(&f,&raw,whole(),Scope::Document,all(),None,invalid),Err(E::Value)));}Ok(())
}
#[test]
fn whitespace_pattern_match_response_and_writer_limits_do_not_return_partial_outputs()->TestResult{
    let raw=fixture::package(&p(1,"A  B  C"))?;let f=forms(&raw)?;
    assert!(matches!(normalize(&f,&raw,Query{mode:Mode::Regex,..query("(")},Scope::Document,all(),None,policy()),Err(E::Search(Search::Pattern))));
    assert!(matches!(normalize(&f,&raw,Query{max_results:1,..query("  ")},Scope::Document,all(),None,policy()),Err(E::Search(Search::Limit))));
    assert!(f.lower_review_selector_whitespace_candidate(&raw,whole(),Scope::Document,all(),None,policy(),RUN,SourceSearchLimits::new(Config{result_bytes:1,..Default::default()})?,Default::default()).is_err());
    assert!(matches!(f.lower_review_selector_whitespace_candidate(&raw,whole(),Scope::Document,all(),None,policy(),RUN,Default::default(),WriterLimits::new(WriterLimitConfig{max_output_bytes:1,..Default::default()})?),Err(E::Writer)));Ok(())
}
#[test]
fn whitespace_long_sequence_has_one_patch_and_single_part_protection_inventory()->TestResult{
    let spaces=" ".repeat(20000);let text=format!("A{spaces}B");let raw=fixture::package(&p(1,&text))?;let f=forms(&raw)?;
    let c=normalize(&f,&raw,whole(),Scope::Document,all(),None,policy())?;exact(&raw,&c,&text,"A B")?;assert_eq!(c.receipt().changed_scalar_ranges,1);assert_eq!(c.receipt().whitespace_sequences,1);
    let xml=PreservingXmlDocument::parse(section(&raw)?.as_bytes())?;assert_eq!(c.receipt().observed_protection_parts,1);assert_eq!(c.receipt().observed_protection_element_visits,xml.elements().len()*3);Ok(())
}
#[test]
fn whitespace_selected_trim_via_remove_never_changes_unselected_boundary_spaces()->TestResult{
    let text="  A   B  ";let raw=fixture::package(&p(1,text))?;let f=forms(&raw)?;let q=Query{mode:Mode::Regex,..query("^ +| +$")};
    let c=normalize(&f,&raw,q,Scope::Document,all(),None,Policy{output:Out::Remove,..policy()})?;exact(&raw,&c,text,"A   B")?;Ok(())
}
#[test]
fn whitespace_policy_request_binding_and_candidate_debug_do_not_expose_source()->TestResult{
    let raw=fixture::package(&p(1,"PRIVATE-SOURCE  A"))?;let original=raw.clone();let f=forms(&raw)?;
    let a=normalize(&f,&raw,whole(),Scope::Document,all(),None,policy())?;
    let b=normalize(&f,&raw,whole(),Scope::Document,all(),None,Policy{output:Out::LineBreak,..policy()})?;
    assert_ne!(a.receipt().request_sha256,b.receipt().request_sha256);assert!(!serde_json::to_string(a.receipt())?.contains("PRIVATE-SOURCE"));assert!(!format!("{a:?}").contains("PRIVATE-SOURCE"));assert_eq!(raw,original);
    assert!(serde_json::from_str::<Text>("\"all_unicode_controls\"").is_err());assert!(serde_json::from_str::<Policy>("{}").is_err());
    assert!(serde_json::from_str::<Out>("{\"spaces\":{\"count\":1,\"ignored\":true}}").is_err());Ok(())
}
#[test]
fn whitespace_sparse_lexical_readback_rejects_prefix_suffix_output_range_and_overlap_tampering(){
    let e=lexical::LexicalEdit{old:1..4,output:b"<tab/>".to_vec()};assert!(lexical::verify(b"aOLDz",b"a<tab/>z",&[&e]).is_ok());
    for output in[b"b<tab/>z".as_slice(),b"a<tab/>X",b"a<tab/>zX",b"a<bad/>z",b"a<tab/>"]{assert!(lexical::verify(b"aOLDz",output,&[&e]).is_err());}
    assert!(lexical::verify(b"aOLDz",b"a<tab/>z",&[&e,&e]).is_err());for range in[4..2,1..8]{let e=lexical::LexicalEdit{old:range,output:Vec::new()};assert!(lexical::verify(b"aOLDz",b"az",&[&e]).is_err());}
}
#[test]
fn whitespace_multiple_control_only_containers_remain_empty_without_removing_run_shells()->TestResult{
    let body=p(1,"<hp:tab width='3' leader='0' type='0'/>")+&p(2,"<hp:lineBreak/>");let raw=fixture::package(&body)?;let f=forms(&raw)?;
    let c=normalize(&f,&raw,whole(),Scope::Document,all(),None,Policy{output:Out::Remove,..policy()})?;
    exact(&raw,&c,&body,&body.replace("<hp:tab width='3' leader='0' type='0'/>","").replace("<hp:lineBreak/>",""))?;assert_eq!(c.receipt().changes.len(),2);Ok(())
}
#[test]
fn whitespace_tabs_to_fixed_spaces_is_explicit_not_visual_tab_stop_evaluation()->TestResult{
    let text="A<hp:tab width='999' leader='2' type='1'/>B<hp:lineBreak/>C";let raw=fixture::package(&p(1,text))?;let f=forms(&raw)?;
    let c=normalize(&f,&raw,whole(),Scope::Document,all(),None,Policy{text:Text::None,line_breaks:false,output:Out::Spaces{count:4},..policy()})?;
    exact(&raw,&c,text,"A    B<hp:lineBreak/>C")?;assert_eq!(c.receipt().changed_original_controls,1);Ok(())
}
#[test]
fn whitespace_repeated_application_is_semantic_nochange_and_retains_original_input()->TestResult{
    let raw=fixture::package(&p(1,"A  <hp:tab width='3' leader='0' type='0'/>B"))?;let original=raw.clone();let f=forms(&raw)?;
    let c=normalize(&f,&raw,whole(),Scope::Document,all(),None,policy())?;let bytes=output(&raw,&c)?;
    assert!(matches!(normalize(&forms(&bytes)?,&bytes,whole(),Scope::Document,all(),None,policy()),Err(E::NoChange)));assert_eq!(raw,original);Ok(())
}
