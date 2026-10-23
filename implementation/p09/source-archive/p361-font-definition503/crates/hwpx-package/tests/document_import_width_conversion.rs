use hwpx_package::{BoundedZipReader,PreservingXmlDocument,XmlTokenKind,WriterLimits,WriterLimitConfig,
    document_import::{ImportedSourcePackage,forms::ImportedDocumentForms,search::{SourceSearchQuery as Query,SourceSearchMode as SearchMode,
        SourceSearchError as Search,SourceSearchLimits,SourceSearchLimitConfig as Config,selector::{SourceIndexScopeSelector as Scope,SourceIndexBoundary as Boundary},
        reviews::{SourceReviewTextPolicy as Body,selector::styles::SourceReviewStyleFilter as Filter},inspection::{SourceDeclaredStyleFilter as Declared,
            definitions::{SourceDefinitionStyleFilter as Definition,CharacterDefinitionSource as Axis}},
        replacement::{SourceLiteralReplacementError as E,SourceReplacementRunPolicy as Run,atoms::width::{SourceWidthConversionCandidate as Candidate,
            SourceWidthMode as Mode,SourceWidthPolicy as Policy,SOURCE_WIDTH_CONVERSION_PROFILE}}}}};
use domain_ir::DocumentId;
use sha2::{Digest as _,Sha256};
use std::{error::Error,io::Cursor};
#[allow(dead_code)] #[path="support/search_definition_fixture.rs"] mod fixture;
#[allow(dead_code)] #[path="support/review_scope_fixture.rs"] mod review;
#[allow(dead_code)] #[path="support/document_import_review_assembly_fixture.rs"] mod assembly;
#[allow(dead_code)] #[path="support/review_cell_output_fixture.rs"] mod table;
type TestResult=Result<(),Box<dyn Error>>;
const POLICY:Policy=Policy::Unicode17WidthPairsWithKanaPairs;
const RUN:Run=Run::FirstOriginalRunRetainAllRuns;
fn forms(raw:&[u8])->Result<ImportedDocumentForms,Box<dyn Error>>{Ok(ImportedDocumentForms::import(ImportedSourcePackage::import(raw,DocumentId::parse("width-source")?,Sha256::digest(raw).into(),Default::default())?)?)}
fn p(id:u32,text:&str)->String{format!("<hp:p id='{id}' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'><hp:t charStyleIDRef='0'>{text}</hp:t></hp:run></hp:p>")}
fn escape(text:&str)->String{text.replace('&',"&amp;").replace('<',"&lt;").replace('>',"&gt;")}
fn all()->Body{Body {include_hidden_explanations:true,include_memo_bodies:true}}
fn query(q:&str)->Query<'_>{Query {query:q,mode:SearchMode::Literal,case_sensitive:true,whole_word:false,max_results:10000}}
fn whole()->Query<'static>{Query {mode:SearchMode::Regex,..query("(?s:.+)")}}
fn convert(f:&ImportedDocumentForms,raw:&[u8],q:Query<'_>,scope:Scope<'_>,body:Body,filter:Option<Filter>,mode:Mode)->Result<Candidate,E>{
    f.lower_review_selector_width_candidate(raw,q,scope,body,filter,mode,POLICY,RUN,Default::default(),Default::default())}
fn section(raw:&[u8])->Result<String,Box<dyn Error>>{let mut zip=BoundedZipReader::open(Cursor::new(raw),Default::default())?;
    let i=zip.entries().iter().position(|e|e.path.as_str()=="Contents/section0.xml").ok_or("section")?;Ok(String::from_utf8(zip.read_entry(i)?)?)}
fn output(raw:&[u8],c:&Candidate)->Result<Vec<u8>,Box<dyn Error>>{let bytes=c.with_verified_bytes(<[u8]>::to_vec)?;
    let mut a=BoundedZipReader::open(Cursor::new(raw),Default::default())?;let mut b=BoundedZipReader::open(Cursor::new(&bytes),Default::default())?;
    assert_eq!(a.entries().len(),b.entries().len());for i in 0..a.entries().len(){let path=a.entries()[i].path.clone();if path.as_str()=="Contents/section0.xml"{continue;}
        let j=b.entries().iter().position(|e|e.path==path).ok_or("part")?;assert_eq!(a.read_entry(i)?,b.read_entry(j)?);}
    let r=c.receipt();assert_eq!(r.profile,SOURCE_WIDTH_CONVERSION_PROFILE);assert_eq!(r.width_unicode_version,(17,0,0));assert_eq!(r.policy,POLICY);assert_eq!(r.run_policy,RUN);
    assert_eq!(r.mapping_source_sha256,"2e1efc1dcb59c575eedf5ccae60f95229f706ee6d031835247d843c11d96470c");assert_eq!((r.width_pair_count,r.kana_pair_count),(226,28));
    assert!(r.exact_original_selection_verified&&r.original_run_shells_declared_styles_controls_and_references_preserved&&r.composed_output_uses_first_original_contributor
        &&r.unrelated_compatibility_and_canonical_text_unchanged&&r.output_spans_and_outside_slots_verified);assert!(!r.general_normalization_icu_native_or_service_authority);Ok(bytes)}
fn exact(raw:&[u8],c:&Candidate,old:&str,new:&str)->TestResult{assert_eq!(section(&output(raw,c)?)?,section(raw)?.replace(old,new));Ok(())}
fn decoded(raw:&[u8])->Result<String,Box<dyn Error>>{let s=section(raw)?;let xml=PreservingXmlDocument::parse(s.as_bytes())?;let mut out=String::new();
    for t in xml.tokens(){if matches!(t.kind(),XmlTokenKind::Text|XmlTokenKind::Whitespace|XmlTokenKind::Reference)&&t.element_index().is_some_and(|i|xml.elements()[i].name().local_name()=="t"){
        let p=t.span();out.push_str(&quick_xml::escape::unescape(&s[p.start()..p.end()])?);}}Ok(out)}
fn point(hex:&str)->Result<char,Box<dyn Error>>{char::from_u32(u32::from_str_radix(hex,16)?).ok_or_else(||"codepoint".into())}
fn rows()->Vec<Vec<&'static str>>{include_str!("support/unicode17_width_pairs.tsv").lines().filter(|l|!l.starts_with('#')&&!l.is_empty()).map(|l|l.split('\t').collect()).collect()}
#[test]
fn width_all226_ucd_pairs_convert_both_directions_against_independent_extracted_fixture()->TestResult{
    let(mut wide,mut half)=(Vec::new(),Vec::new());for r in rows().into_iter().filter(|r|r[0]!="kana"){
        let(a,b)=(point(r[1])?,point(r[2])?);let(w,h)=if r[0]=="wide"{(a,b)}else{(b,a)};wide.push(w.to_string());half.push(h.to_string());}
    assert_eq!(wide.len(),226);for(input,expected,mode)in[(half.join("界"),wide.join("界"),Mode::Fullwidth),(wide.join("界"),half.join("界"),Mode::Halfwidth)]{
        let raw=fixture::package(&p(1,&escape(&input)))?;let f=forms(&raw)?;let c=convert(&f,&raw,whole(),Scope::Document,all(),None,mode)?;assert_eq!(decoded(&output(&raw,&c)?)?,expected);}Ok(())
}
#[test]
fn width_all28_representable_kana_pairs_fuse_and_expand_against_ucd_canonical_rows()->TestResult{
    let rs=rows();let mut half=Vec::new();let mut wide=Vec::new();for r in rs.iter().filter(|r|r[0]=="kana"){
        wide.push(point(r[1])?.to_string());let mut h=String::new();for cp in[r[2],r[3]]{h.push(point(rs.iter().find(|p|p[0]=="narrow"&&p[2]==cp).ok_or("narrow counterpart")?[1])?);}half.push(h);}
    assert_eq!(wide.len(),28);for(input,expected,mode)in[(half.join("界"),wide.join("界"),Mode::Fullwidth),(wide.join("界"),half.join("界"),Mode::Halfwidth)]{
        let raw=fixture::package(&p(1,&input))?;let f=forms(&raw)?;let c=convert(&f,&raw,whole(),Scope::Document,all(),None,mode)?;assert_eq!(decoded(&output(&raw,&c)?)?,expected);}Ok(())
}
#[test]
fn width_space_currency_brackets_and_macron_are_width_pairs_not_nfkc()->TestResult{
    for(input,expected,mode)in[(" A¢£¬¯¦¥₩⦅⦆","　Ａ￠￡￢￣￤￥￦｟｠",Mode::Fullwidth),("　Ａ￠￡￢￣￤￥￦｟｠"," A¢£¬¯¦¥₩⦅⦆",Mode::Halfwidth)]{
        let raw=fixture::package(&p(1,input))?;let f=forms(&raw)?;let c=convert(&f,&raw,whole(),Scope::Document,all(),None,mode)?;assert_eq!(decoded(&output(&raw,&c)?)?,expected);}Ok(())
}
#[test]
fn width_hangul_uses_explicit_compatibility_jamo_pairs_without_syllable_decomposition()->TestResult{
    let raw=fixture::package(&p(1,"ﾡ가ㄱ"))?;let f=forms(&raw)?;for(mode,expected)in[(Mode::Fullwidth,"ㄱ가ㄱ"),(Mode::Halfwidth,"ﾡ가ﾡ")]{let c=convert(&f,&raw,whole(),Scope::Document,all(),None,mode)?;exact(&raw,&c,"ﾡ가ㄱ",expected)?;}Ok(())
}
#[test]
fn width_only_kana_components_with_a_width_change_compose_unrelated_nfd_remains_exact()->TestResult{
    let input="ガ界ｶ゙界カﾞ界ｶﾞ界ヸヹヾ";let raw=fixture::package(&p(1,input))?;let f=forms(&raw)?;
    for(mode,expected)in[(Mode::Fullwidth,"ガ界ガ界ガ界ガ界ヸヹヾ"),(Mode::Halfwidth,"ｶﾞ界ｶﾞ界ｶﾞ界ｶﾞ界ヸヹヾ")]{let c=convert(&f,&raw,whole(),Scope::Document,all(),None,mode)?;exact(&raw,&c,input,expected)?;}Ok(())
}
#[test]
fn width_kana_fusion_across_runs_uses_first_contributor_and_keeps_suffix_style()->TestResult{
    let body="<hp:p id='1'><hp:run charPrIDRef='0'><hp:t charStyleIDRef='0'>界ﾊ</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t charStyleIDRef='1'>ﾟ界</hp:t></hp:run></hp:p>";
    let raw=fixture::package(body)?;let f=forms(&raw)?;let c=convert(&f,&raw,whole(),Scope::Document,all(),None,Mode::Fullwidth)?;
    exact(&raw,&c,body,&body.replace("界ﾊ<","界パ<").replace(">ﾟ界<",">界<"))?;assert_eq!(c.receipt().changed_components,1);assert_eq!(c.receipt().changed_scalar_ranges,2);Ok(())
}
#[test]
fn width_kana_expansion_stays_in_origin_atom_with_other_entities_and_references_exact()->TestResult{
    let body="<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>&#x1F600;Ｘ</hp:t><hp:ctrl><hp:bookmark name='KEEP'/></hp:ctrl></hp:run><hp:run charPrIDRef='1'><hp:t charStyleIDRef='1'>ガ</hp:t></hp:run><hp:run><hp:t>&#x26;界</hp:t></hp:run></hp:p>";
    let raw=fixture::package(body)?;let f=forms(&raw)?;let c=convert(&f,&raw,query("ガ"),Scope::Document,all(),None,Mode::Halfwidth)?;exact(&raw,&c,">ガ<",">ｶﾞ<")?;assert_eq!(c.receipt().changes.len(),1);Ok(())
}
#[test]
fn width_long_ascii_word_has_one_patch_with_match_limit_one()->TestResult{
    let text="a".repeat(20000);let raw=fixture::package(&p(1,&text))?;let f=forms(&raw)?;let limits=SourceSearchLimits::new(Config {matches:1,..Default::default()})?;
    let c=f.lower_review_selector_width_candidate(&raw,Query {max_results:1,..whole()},Scope::Document,all(),None,Mode::Fullwidth,POLICY,RUN,limits,Default::default())?;
    exact(&raw,&c,&text,&"ａ".repeat(20000))?;assert_eq!(c.receipt().changed_components,1);assert_eq!(c.receipt().changed_scalar_ranges,1);Ok(())
}
#[test]
fn width_no_matches_no_change_and_zero_width_are_distinct_errors()->TestResult{
    let raw=fixture::package(&p(1,"Ａｶ"))?;let f=forms(&raw)?;assert!(matches!(convert(&f,&raw,query("ABSENT"),Scope::Document,all(),None,Mode::Fullwidth),Err(E::NoMatches)));
    assert!(matches!(convert(&f,&raw,query("Ａ"),Scope::Document,all(),None,Mode::Fullwidth),Err(E::NoChange)));
    assert!(matches!(convert(&f,&raw,Query {mode:SearchMode::Regex,..query("^|ｶ")},Scope::Document,all(),None,Mode::Fullwidth),Err(E::Selection)));Ok(())
}
#[test]
fn width_four_selectors_keep_clipped_regex_and_original_scope_boundaries()->TestResult{
    let raw=fixture::package(&(p(1,"X abc Z")+&p(2,"Y abc Z")))?;let f=forms(&raw)?;let inv=f.source_review_scope_index(&raw,Default::default())?.scope_inventory()?;let b=&inv.inventory.blocks[0];
    let ids=[inv.inventory.nodes.iter().find(|n|n.source_handle==b.paragraph_handle).ok_or("node")?.node_id.clone()];let start=Boundary {paragraph_handle:b.paragraph_handle.clone(),block_index:0,normalized_scalar:2};let end=Boundary {normalized_scalar:5,..start.clone()};
    for(scope,n)in[(Scope::Document,2),(Scope::Section(&inv.inventory.section_ids),2),(Scope::NodeSet(&ids),1),(Scope::Selection {index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},1)]{
        let q=if matches!(scope,Scope::Selection {..}){Query {mode:SearchMode::Regex,..query("^abc$")}}else{query("abc")};let c=convert(&f,&raw,q,scope,all(),None,Mode::Fullwidth)?;
        let out=c.with_verified_bytes(section)??;assert!(out.contains("X ａｂｃ Z"));assert_eq!(out.contains("Y abc Z"),n==1);assert_eq!(c.receipt().search.search().result().matches().len(),n);}Ok(())
}
#[test]
fn width_regex_casefold_and_whole_word_select_without_folding_original_case()->TestResult{
    let input="abc xabcx ABC";let raw=fixture::package(&p(1,input))?;let f=forms(&raw)?;let q=Query {mode:SearchMode::Regex,case_sensitive:false,whole_word:true,..query("a[b]c")};
    let c=convert(&f,&raw,q,Scope::Document,all(),None,Mode::Fullwidth)?;exact(&raw,&c,input,"ａｂｃ xabcx ＡＢＣ")?;assert_eq!(c.receipt().search.search().result().matches().len(),2);Ok(())
}
#[test]
fn width_declared_definition_filters_cover_all_original_contributors_before_caps()->TestResult{
    let body="<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>a</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>bc abc</hp:t></hp:run></hp:p>";let raw=fixture::package(body)?;let f=forms(&raw)?;
    for filter in[Filter::Declared(Declared {run_character_property:Some(1),..Default::default()}),Filter::Definition(Definition {character_source:Some(Axis::RunProperty),bold:Some(true),..Default::default()})]{let c=convert(&f,&raw,Query {max_results:1,..query("abc")},Scope::Document,all(),Some(filter),Mode::Fullwidth)?;exact(&raw,&c,">bc abc<",">bc ａｂｃ<")?;}Ok(())
}
#[test]
fn width_review_policy_excludes_before_caps_and_keeps_cache_and_author_metadata()->TestResult{
    let body=review::body();let raw=fixture::package(&body)?;let f=forms(&raw)?;for(h,m,n)in[(false,false,2),(true,false,4),(false,true,4),(true,true,6)]{
        let c=convert(&f,&raw,Query {max_results:n,..query("K")},Scope::Document,Body {include_hidden_explanations:h,include_memo_bodies:m},None,Mode::Fullwidth)?;let mut expected=body.replace("BODY K K","BODY Ｋ Ｋ");
        if h{expected=expected.replace("HIDDEN K K","HIDDEN Ｋ Ｋ");}if m{expected=expected.replace("MEMO K K","MEMO Ｋ Ｋ");}exact(&raw,&c,&body,&expected)?;assert_eq!(c.receipt().search.search().result().matches().len(),n);}Ok(())
}
#[test]
fn width_tabs_and_linebreaks_are_exact_and_prevent_kana_composition_across_controls()->TestResult{
    let text="ｶ<hp:tab width='1' leader='0' type='0'> </hp:tab>ﾞ<hp:lineBreak> </hp:lineBreak>ﾊﾟ";let raw=fixture::package(&p(1,text))?;let f=forms(&raw)?;
    let c=convert(&f,&raw,whole(),Scope::Document,all(),None,Mode::Fullwidth)?;exact(&raw,&c,text,"カ<hp:tab width='1' leader='0' type='0'> </hp:tab>゙<hp:lineBreak> </hp:lineBreak>パ")?;assert_eq!(c.receipt().converted_text_groups,3);Ok(())
}
#[test]
fn width_separate_matches_and_unselected_marks_never_join_conversion_contexts()->TestResult{
    let raw=fixture::package(&p(1,"ｶﾞ"))?;let f=forms(&raw)?;let c=convert(&f,&raw,query("ｶ"),Scope::Document,all(),None,Mode::Fullwidth)?;exact(&raw,&c,"ｶﾞ","カﾞ")?;
    let c=convert(&f,&raw,Query {mode:SearchMode::Regex,..query(".")},Scope::Document,all(),None,Mode::Fullwidth)?;exact(&raw,&c,"ｶﾞ","ガ")?;
    let c=convert(&f,&raw,whole(),Scope::Document,all(),None,Mode::Fullwidth)?;exact(&raw,&c,"ｶﾞ","ガ")?;Ok(())
}
#[test]
fn width_partial_and_noncontiguous_nfc_inverses_reject_without_widening()->TestResult{
    for(text,q)in[("&#x344;A","\u{308}"),("à̕","à")]{let raw=fixture::package(&p(1,text))?;let f=forms(&raw)?;assert!(matches!(convert(&f,&raw,query(q),Scope::Document,all(),None,Mode::Fullwidth),Err(E::Selection)));}Ok(())
}
#[test]
fn width_protected_noops_reject_but_unmatched_protected_table_content_stays_exact()->TestResult{
    let raw=fixture::package(&p(1,"ABC").replace("charPrIDRef='0'","charPrIDRef='0' charTcId='1'"))?;let f=forms(&raw)?;assert!(matches!(convert(&f,&raw,query("ABC"),Scope::Document,all(),None,Mode::Halfwidth),Err(E::Protection)));
    let raw=fixture::package(&(p(1,"Ａ")+&format!("<hp:p id='2'><hp:run>{}</hp:run></hp:p>",table::table(300).replace("lock='0'","lock='1'"))))?;let f=forms(&raw)?;
    assert!(matches!(convert(&f,&raw,query("CELL"),Scope::Document,all(),None,Mode::Halfwidth),Err(E::Protection)));let c=convert(&f,&raw,query("Ａ"),Scope::Document,all(),None,Mode::Halfwidth)?;exact(&raw,&c,">Ａ<",">A<")?;Ok(())
}
#[test]
fn width_matching_field_cache_is_blocked_even_when_conversion_is_a_noop()->TestResult{
    let raw=fixture::package(&review::body())?;let f=forms(&raw)?;assert!(matches!(convert(&f,&raw,query("FROZEN"),Scope::Document,all(),None,Mode::Halfwidth),Err(E::FieldContent)));
    let c=convert(&f,&raw,query("K"),Scope::Document,all(),None,Mode::Fullwidth)?;assert!(c.with_verified_bytes(section)??.contains("CACHE FROZEN"));Ok(())
}
#[test]
fn width_original_proof_stale_source_and_invalid_filters_reject_before_success()->TestResult{
    let raw=fixture::package(&p(1,"abc"))?;let f=forms(&raw)?;let other=forms(&raw)?;let proof=f.reconstruct_source_for_verification(&raw)?;
    assert!(matches!(proof.lower_review_selector_width_candidate(&other,whole(),Scope::Document,all(),None,Mode::Fullwidth,POLICY,RUN,Default::default(),Default::default()),Err(E::Source)));
    let changed=fixture::package(&p(1,"xyz"))?;assert!(matches!(convert(&f,&changed,whole(),Scope::Document,all(),None,Mode::Fullwidth),Err(E::Source)));
    for filter in[Filter::Declared(Declared::default()),Filter::Definition(Definition {bold:Some(true),..Default::default()})]{assert!(matches!(convert(&f,&raw,query("ABSENT"),Scope::Document,all(),Some(filter),Mode::Fullwidth),Err(E::Search(Search::Filter))));}Ok(())
}
#[test]
fn width_pattern_match_decomposition_response_and_writer_limits_never_yield_partial_candidates()->TestResult{
    let raw=fixture::package(&p(1,"abc abc"))?;let f=forms(&raw)?;assert!(matches!(convert(&f,&raw,Query {mode:SearchMode::Regex,..query("(")},Scope::Document,all(),None,Mode::Fullwidth),Err(E::Search(Search::Pattern))));
    assert!(matches!(convert(&f,&raw,Query {max_results:1,..query("abc")},Scope::Document,all(),None,Mode::Fullwidth),Err(E::Search(Search::Limit))));
    assert!(f.lower_review_selector_width_candidate(&raw,query("abc"),Scope::Document,all(),None,Mode::Fullwidth,POLICY,RUN,SourceSearchLimits::new(Config {result_bytes:1,..Default::default()})?,Default::default()).is_err());
    assert!(matches!(f.lower_review_selector_width_candidate(&raw,query("abc"),Scope::Document,all(),None,Mode::Fullwidth,POLICY,RUN,Default::default(),WriterLimits::new(WriterLimitConfig {max_output_bytes:1,..Default::default()})?),Err(E::Writer)));
    let raw=fixture::package(&p(1,"ガ"))?;let f=forms(&raw)?;assert!(matches!(f.lower_review_selector_width_candidate(&raw,query("ガ"),Scope::Document,all(),None,Mode::Halfwidth,POLICY,RUN,SourceSearchLimits::new(Config {decomposed_scalars:1,..Default::default()})?,Default::default()),Err(E::Search(Search::Limit))));Ok(())
}
#[test]
fn width_long_kana_chain_uses_one_component_and_one_part_protection_map()->TestResult{
    for(input,expected,mode)in[("ﾊﾟ".repeat(4096),"パ".repeat(4096),Mode::Fullwidth),("パ".repeat(4096),"ﾊﾟ".repeat(4096),Mode::Halfwidth)]{
        let raw=fixture::package(&p(1,&input))?;let f=forms(&raw)?;let c=convert(&f,&raw,whole(),Scope::Document,all(),None,mode)?;exact(&raw,&c,&input,&expected)?;assert_eq!(c.receipt().changed_components,1);assert_eq!(c.receipt().changed_scalar_ranges,1);
        let xml=PreservingXmlDocument::parse(section(&raw)?.as_bytes())?;assert_eq!(c.receipt().observed_protection_element_visits,xml.elements().len()*3);}Ok(())
}
#[test]
fn width_manifest_counts_unique_pairs_and_idempotence_are_exact()->TestResult{
    let rs=rows();assert_eq!(rs.iter().filter(|r|r[0]=="wide").count(),104);assert_eq!(rs.iter().filter(|r|r[0]=="narrow").count(),122);assert_eq!(rs.iter().filter(|r|r[0]=="kana").count(),28);
    let raw=fixture::package(&p(1,"Ａｶﾞﾡ①ﬃé"))?;let f=forms(&raw)?;for mode in[Mode::Fullwidth,Mode::Halfwidth]{let c=convert(&f,&raw,whole(),Scope::Document,all(),None,mode)?;let bytes=output(&raw,&c)?;
        assert!(matches!(convert(&forms(&bytes)?,&bytes,whole(),Scope::Document,all(),None,mode),Err(E::NoChange)));}Ok(())
}
#[test]
fn width_unpaired_marks_and_unrelated_compatibility_characters_are_not_general_normalization()->TestResult{
    let input="ﾞﾟヸヹヾ①ℍﬃ\u{a0}é";let raw=fixture::package(&p(1,input))?;let f=forms(&raw)?;let c=convert(&f,&raw,whole(),Scope::Document,all(),None,Mode::Fullwidth)?;exact(&raw,&c,input,"゙゚ヸヹヾ①ℍﬃ\u{a0}é")?;Ok(())
}
#[test]
fn width_mode_policy_binding_and_receipt_redaction_preserve_original_source()->TestResult{
    let raw=fixture::package(&p(1,"PRIVATE-SOURCE Ａa"))?;let original=raw.clone();let f=forms(&raw)?;let a=convert(&f,&raw,whole(),Scope::Document,all(),None,Mode::Fullwidth)?;let b=convert(&f,&raw,whole(),Scope::Document,all(),None,Mode::Halfwidth)?;
    assert_ne!(a.receipt().request_sha256,b.receipt().request_sha256);assert!(!serde_json::to_string(a.receipt())?.contains("PRIVATE-SOURCE"));assert!(!format!("{a:?}").contains("PRIVATE-SOURCE"));assert_eq!(raw,original);
    assert!(serde_json::from_str::<Mode>("\"nfkc\"").is_err());assert!(serde_json::from_str::<Policy>("\"native_width\"").is_err());Ok(())
}
