use hwpx_package::{document_import::{ImportedSourcePackage,SourceImportLimits,structure::ImportedDocumentStructure,
    search::{SourceTextIndex,SourceSearchLimits,SourceSearchLimitConfig as Config,SourceSearchQuery as Query,SourceSearchMode as Mode,SourceSearchError as E}},
    WriterLimits};
use domain_ir::DocumentId;
use sha2::{Digest as _,Sha256};
use std::error::Error;
use unicode_normalization::UnicodeNormalization as _;
#[allow(dead_code)]
#[path="support/document_import_field_fixture.rs"] mod fixture;
type TestResult=Result<(),Box<dyn Error>>;
fn source(body:&str)->Result<(Vec<u8>,ImportedDocumentStructure),Box<dyn Error>> {
    let bytes=fixture::package(body)?;let structure=import(&bytes,"source-search-document")?;Ok((bytes,structure))
}
fn import(bytes:&[u8],document:&str)->Result<ImportedDocumentStructure,Box<dyn Error>> {
    Ok(ImportedDocumentStructure::import(ImportedSourcePackage::import(bytes,DocumentId::parse(document)?,Sha256::digest(bytes).into(),SourceImportLimits::default())?)?)
}
fn paragraph(text:&str,id:u32)->String {format!("<hp:p id='{id}'><hp:run><hp:t>{}</hp:t></hp:run></hp:p>",quick_xml::escape::escape(text))}
fn query(text:&str)->Query<'_> {Query {query:text,mode:Mode::Literal,case_sensitive:true,whole_word:false,max_results:100}}
fn default_index<'a>(s:&'a ImportedDocumentStructure,b:&[u8])->Result<SourceTextIndex<'a>,E> {s.source_text_index(b,SourceSearchLimits::default())}
#[test]
fn literal_crosses_runs_and_entities_with_exact_decoded_scalar_provenance()->TestResult {
    let(b,s)=source("<hp:p id='1'><hp:run><hp:t>A &amp;</hp:t></hp:run><hp:run><hp:t>B&#x1F600;C</hp:t></hp:run></hp:p>")?;
    let index=default_index(&s,&b)?;let result=index.find(query("&B😀"))?;assert_eq!(result.matches().len(),1);
    let m=&result.matches()[0];assert!(m.source_scalar_selection_exact);assert_eq!((m.start_normalized_scalar,m.end_normalized_scalar),(2,5));
    assert_eq!(m.pieces.iter().map(|p|(p.atom_index,p.start_scalar,p.end_scalar)).collect::<Vec<_>>(),vec![(0,2,3),(0,0,2)]);
    assert_ne!(m.pieces[0].text_anchor,m.pieces[1].text_anchor);index.verify_source(&b)?;Ok(())
}
#[test]
fn hangul_jamo_composes_across_three_runs_without_losing_original_locations()->TestResult {
    let(b,s)=source("<hp:p id='1'><hp:run><hp:t>ᄀ</hp:t></hp:run><hp:run><hp:t>ᅡ</hp:t></hp:run><hp:run><hp:t>ᆨ</hp:t></hp:run></hp:p>")?;
    let index=default_index(&s,&b)?;assert_eq!((index.receipt().original_scalars,index.receipt().normalized_scalars),(3,1));
    let result=index.find(query("각"))?;let m=&result.matches()[0];assert_eq!(m.pieces.len(),3);assert!(m.source_scalar_selection_exact);
    assert_eq!(result.matches(),index.find(query("각"))?.matches());Ok(())
}
#[test]
fn combining_accent_crosses_runs_and_normalizes_literal_query_only()->TestResult {
    let(b,s)=source("<hp:p id='1'><hp:run><hp:t>e</hp:t></hp:run><hp:run><hp:t>&#769;</hp:t></hp:run></hp:p>")?;
    let i=default_index(&s,&b)?;let r=i.find(query("e\u{301}"))?;assert_eq!(r.matches().len(),1);assert_eq!(r.matches()[0].pieces.len(),2);
    assert!(i.find(Query {mode:Mode::Regex,query:r"e\u{301}",..query("x")})?.matches().is_empty());
    assert_eq!(i.find(Query {mode:Mode::Regex,query:r"\u{e9}",..query("x")})?.matches().len(),1);Ok(())
}
#[test]
fn canonical_reordering_maps_nonadjacent_original_scalars_without_swallowing_neighbors()->TestResult {
    let(b,s)=source(&paragraph("a\u{315}\u{300}",1))?;let i=default_index(&s,&b)?;let r=i.find(query("à"))?;let m=&r.matches()[0];
    assert_eq!(m.pieces.iter().map(|p|(p.start_scalar,p.end_scalar)).collect::<Vec<_>>(),vec![(0,1),(2,3)]);assert!(m.source_scalar_selection_exact);
    assert_eq!(i.find(query("\u{315}"))?.matches()[0].pieces[0].start_scalar,1);Ok(())
}
#[test]
fn one_source_scalar_expanding_to_two_nfc_scalars_does_not_claim_an_exact_partial_selection()->TestResult {
    let(b,s)=source(&paragraph("\u{344}",1))?;let i=default_index(&s,&b)?;assert_eq!(i.receipt().normalized_scalars,2);
    let part=i.find(query("\u{308}"))?;assert_eq!(part.matches().len(),1);assert!(!part.matches()[0].source_scalar_selection_exact);
    let all=i.find(query("\u{344}"))?;assert_eq!(all.matches().len(),1);assert!(all.matches()[0].source_scalar_selection_exact);Ok(())
}
#[test]
fn regex_unicode_classes_and_leftmost_nonoverlapping_results_are_deterministic()->TestResult {
    let(b,s)=source(&paragraph("한글12 한글345 banana",1))?;let i=default_index(&s,&b)?;
    let r=i.find(Query {query:r"\p{Hangul}+\d+",mode:Mode::Regex,..query("x")})?;assert_eq!(r.matches().len(),2);
    assert_eq!(i.find(query("ana"))?.matches().len(),1);assert_eq!(r.canonical_json()?,i.find(Query {query:r"\p{Hangul}+\d+",mode:Mode::Regex,..query("x")})?.canonical_json()?);Ok(())
}
#[test]
fn unicode_simple_case_folding_does_not_invent_full_multi_character_casefold()->TestResult {
    let(b,s)=source(&paragraph("ſ S s Straße",1))?;let i=default_index(&s,&b)?;
    assert_eq!(i.find(Query {case_sensitive:false,..query("s")})?.matches().len(),4);
    assert!(i.find(Query {case_sensitive:false,..query("STRASSE")})?.matches().is_empty());Ok(())
}
#[test]
fn whole_word_uses_unicode_word_boundaries_including_underscore()->TestResult {
    let(b,s)=source(&paragraph("cat scatter cat_ cat 한글 한글자",1))?;let i=default_index(&s,&b)?;
    assert_eq!(i.find(Query {whole_word:true,..query("cat")})?.matches().len(),2);
    assert_eq!(i.find(Query {whole_word:true,..query("한글")})?.matches().len(),1);Ok(())
}
#[test]
fn paragraph_boundaries_are_not_concatenated()->TestResult {
    let(b,s)=source(&(paragraph("one",1)+&paragraph("two",2)))?;let i=default_index(&s,&b)?;
    assert!(i.find(query("onetwo"))?.matches().is_empty());assert_eq!(i.receipt().paragraphs,2);assert_eq!(i.receipt().blocks,2);Ok(())
}
#[test]
fn opaque_content_and_unmapped_paragraphs_are_barriers_not_silently_searchable_text()->TestResult {
    let(b,s)=source("<hp:p id='1'><hp:run><hp:t>a</hp:t><u:future><hp:p id='2'><hp:run><hp:t>PRIVATE-UNKNOWN</hp:t></hp:run></hp:p></u:future><hp:t>b</hp:t></hp:run></hp:p>")?;
    let i=default_index(&s,&b)?;assert!(i.find(query("ab"))?.matches().is_empty());assert!(i.find(query("PRIVATE-UNKNOWN"))?.matches().is_empty());
    assert_eq!(i.receipt().skipped_unmapped_source_paragraphs,1);assert!(i.receipt().control_or_opaque_barriers>0);assert!(!i.receipt().whole_document_visibility_and_search_qualified);Ok(())
}
#[test]
fn field_controls_are_barriers_and_caches_are_not_refreshed_or_concatenated()->TestResult {
    let(b,s)=source("<hp:p id='1'><hp:run><hp:t>a</hp:t><hp:ctrl><hp:fieldBegin id='17' type='DATE'/></hp:ctrl><hp:t>b</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='17'/></hp:ctrl><hp:t>c</hp:t></hp:run></hp:p>")?;
    let i=default_index(&s,&b)?;assert!(i.find(query("ab"))?.matches().is_empty());assert!(i.find(query("bc"))?.matches().is_empty());assert_eq!(i.find(query("b"))?.matches().len(),1);Ok(())
}
#[test]
fn tabs_and_linebreaks_keep_distinct_atom_positions()->TestResult {
    let(b,s)=source("<hp:p id='1'><hp:run><hp:t>A<hp:tab width='1' leader='0' type='0'/>B<hp:lineBreak/>C</hp:t></hp:run></hp:p>")?;
    let i=default_index(&s,&b)?;let r=i.find(query("\tB\n"))?;
    assert_eq!(r.matches()[0].pieces.iter().map(|p|p.atom_index).collect::<Vec<_>>(),vec![1,2,3]);Ok(())
}
#[test]
fn stale_package_or_foreign_original_cannot_revalidate_an_index()->TestResult {
    let(b,s)=source(&paragraph("value",1))?;let i=default_index(&s,&b)?;let other=fixture::package(&paragraph("changed",1))?;
    assert!(matches!(i.verify_source(&other),Err(E::Source)));assert!(matches!(s.source_text_index(&other,Default::default()),Err(E::Source)));Ok(())
}
#[test]
fn query_result_and_compiled_pattern_limits_return_errors_not_partial_sets()->TestResult {
    let(b,s)=source(&paragraph("a a",1))?;let i=default_index(&s,&b)?;
    assert!(matches!(i.find(Query {max_results:1,..query("a")}),Err(E::Limit)));
    for q in [query(""),Query {max_results:0,..query("a")},Query {max_results:10_001,..query("a")}] {assert!(matches!(i.find(q),Err(E::Limit)));}
    let config=Config {pattern_bytes:1,..Default::default()};let i=s.source_text_index(&b,SourceSearchLimits::new(config)?)?;
    assert!(matches!(i.find(Query {query:r"\p{L}{100}",mode:Mode::Regex,..query("x")}),Err(E::Pattern)));Ok(())
}
#[test]
fn invalid_regex_backreference_and_lookaround_are_rejected()->TestResult {
    let(b,s)=source(&paragraph("aaa",1))?;let i=default_index(&s,&b)?;
    for pattern in ["[",r"(a)\1",r"(?=a)"] {assert!(matches!(i.find(Query {query:pattern,mode:Mode::Regex,..query("x")}),Err(E::Pattern)));}Ok(())
}
#[test]
fn index_scalars_paragraphs_blocks_and_segments_remain_finitely_bounded()->TestResult {
    assert!(SourceSearchLimits::new(Config {scalars:0,..Default::default()}).is_err());
    let(b,s)=source(&(paragraph("abc",1)+&paragraph("def",2)))?;
    for config in [Config {scalars:2,..Default::default()},Config {paragraphs:1,..Default::default()},Config {blocks:1,..Default::default()},Config {segments:1,..Default::default()}] {
        assert!(matches!(s.source_text_index(&b,SourceSearchLimits::new(config)?),Err(E::Limit)));
    }Ok(())
}
#[test]
fn decomposition_budget_is_global_across_blocks_not_just_composed_output_length()->TestResult {
    let(b,s)=source(&(paragraph("ä",1)+&paragraph("ä",2)))?;
    assert!(matches!(s.source_text_index(&b,SourceSearchLimits::new(Config {decomposed_scalars:3,..Default::default()})?),Err(E::Limit)));Ok(())
}
#[test]
fn response_budget_is_enforced_even_for_a_zero_match_response()->TestResult {
    let(b,s)=source(&paragraph("text",1))?;let i=s.source_text_index(&b,SourceSearchLimits::new(Config {result_bytes:1,..Default::default()})?)?;
    assert!(matches!(i.find(query("absent")),Err(E::Output)));Ok(())
}
#[test]
fn zero_width_results_are_bounded_positions_not_fabricated_editable_source_ranges()->TestResult {
    let(b,s)=source(&paragraph("abc",1))?;let i=default_index(&s,&b)?;let r=i.find(Query {query:"^|$",mode:Mode::Regex,..query("x")})?;
    assert_eq!(r.matches().len(),2);assert!(r.matches().iter().all(|m|m.zero_width&&!m.source_scalar_selection_exact&&m.pieces.is_empty()));Ok(())
}
#[test]
fn empty_mapped_paragraph_keeps_a_zero_length_search_block()->TestResult {
    let(b,s)=source("<hp:p id='1'><hp:run></hp:run></hp:p>")?;let i=default_index(&s,&b)?;
    assert_eq!((i.receipt().paragraphs,i.receipt().blocks,i.receipt().original_scalars),(1,1,0));
    assert_eq!(i.find(Query {query:"^$",mode:Mode::Regex,..query("x")})?.matches().len(),1);Ok(())
}
#[test]
fn normalization_corpus_matches_the_library_oracle_and_original_scalar_selection()->TestResult {
    let values=["e\u{301}","a\u{315}\u{300}","\u{344}","각","각","Å","A\u{30a}","\u{212b}","q\u{307}\u{323}","\u{301}a","한글😀","a\u{308}\u{301}"];
    let original=values.join("|");let expected=original.nfc().collect::<String>();let(b,s)=source(&paragraph(&original,1))?;let i=default_index(&s,&b)?;
    let r=i.find(query(&expected))?;assert_eq!(r.matches().len(),1);assert!(r.matches()[0].source_scalar_selection_exact);
    assert_eq!(r.matches()[0].pieces[0].end_scalar as usize,original.chars().count());Ok(())
}
#[test]
fn source_document_identity_and_request_options_have_distinct_bindings()->TestResult {
    let(b,s)=source(&paragraph("Same",1))?;let other=import(&b,"foreign-document")?;let a=default_index(&s,&b)?;let z=default_index(&other,&b)?;
    assert_ne!(a.receipt().index_sha256,z.receipt().index_sha256);assert_ne!(a.receipt().graph_sha256,z.receipt().graph_sha256);
    assert_ne!(a.find(query("Same"))?.query_sha256(),a.find(Query {case_sensitive:false,..query("Same")})?.query_sha256());Ok(())
}
#[test]
fn results_and_debug_do_not_expose_queries_text_or_upgrade_authority()->TestResult {
    let(b,s)=source(&paragraph("PRIVATE-QUERY-TEXT",1))?;let i=default_index(&s,&b)?;let q=query("PRIVATE-QUERY-TEXT");let r=i.find(q)?;
    assert!(!format!("{i:?}{q:?}{r:?}").contains("PRIVATE-QUERY-TEXT"));let json=String::from_utf8(r.canonical_json()?)?;
    assert!(!json.contains("PRIVATE-QUERY-TEXT"));assert!(json.contains("\"whole_document_visibility_and_search_qualified\":false"));
    assert!(json.contains("\"edit_or_execution_authority\":false"));assert!(json.contains("\"complete_within_indexed_blocks\":true"));Ok(())
}
#[test]
fn mapped_note_paragraphs_are_searchable_without_crossing_the_note_control()->TestResult {
    let(b,s)=source("<hp:p id='1'><hp:run><hp:t>MAIN</hp:t><hp:ctrl><hp:footNote instId='101'><hp:subList><hp:p id='11'><hp:run><hp:t>NOTE</hp:t></hp:run></hp:p></hp:subList></hp:footNote></hp:ctrl><hp:t>TAIL</hp:t></hp:run></hp:p>")?;
    let i=default_index(&s,&b)?;assert_eq!(i.find(query("NOTE"))?.matches().len(),1);assert!(i.find(query("MAINTAIL"))?.matches().is_empty());
    assert_eq!(i.receipt().paragraphs,2);let candidate=s.export_note_file_candidate(&b,hwpx_package::document_import::structure::note_export::NoteFileSelection::Both,hwpx_package::NoteHwpxLimits::new(Default::default())?,WriterLimits::default())?;
    assert_eq!(candidate.receipt().selected_notes,1);Ok(())
}
