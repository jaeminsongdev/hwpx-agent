use hwpx_package::{BoundedZipReader,PackageLimits,PreservingXmlDocument,WriterLimits,WriterLimitConfig,PatchLimits,
    document_import::{ImportedSourcePackage,forms::ImportedDocumentForms,search::{SourceSearchQuery as Query,SourceSearchMode as Mode,
        SourceSearchLimits,SourceSearchLimitConfig as Config,SourceSearchError,selector::{SourceIndexScopeSelector as Scope,SourceIndexBoundary as Boundary},
        reviews::{SourceReviewTextPolicy as Policy,SourceTextRegion as Region},replacement::{SourceLiteralReplacementError as Compile,SourceReplacementRunPolicy as Run,
            atoms::regex::{SourceSelectorRegexCandidate as Candidate,SourceRegexReplacementError as E,validate_regex_replacement_template}}}}};
use domain_ir::DocumentId;
use sha2::{Digest as _,Sha256};
use std::{error::Error,io::Cursor};
#[path="support/review_scope_fixture.rs"] mod fixture;
#[allow(dead_code)] #[path="support/search_definition_fixture.rs"] mod definition;
#[allow(dead_code)] #[path="support/document_import_review_assembly_fixture.rs"] mod assembly;
#[allow(dead_code)] #[path="support/review_cell_output_fixture.rs"] mod table;
type TestResult=Result<(),Box<dyn Error>>;
const TAB:&str="<hp:tab width='1' leader='0' type='0'/>";
fn forms(raw:&[u8])->Result<ImportedDocumentForms,Box<dyn Error>> {Ok(ImportedDocumentForms::import(ImportedSourcePackage::import(raw,DocumentId::parse("regex-replacement")?,Sha256::digest(raw).into(),Default::default())?)?)}
fn query(q:&str)->Query<'_>{Query{query:q,mode:Mode::Regex,case_sensitive:true,whole_word:false,max_results:10000}}
fn all()->Policy{Policy{include_hidden_explanations:true,include_memo_bodies:true}}
fn package(text:&str)->Result<Vec<u8>,Box<dyn Error>>{fixture::with_body(&format!("<hp:p id='1'><hp:run><hp:t>{text}</hp:t></hp:run></hp:p>"))}
fn replace(f:&ImportedDocumentForms,raw:&[u8],q:&str,scope:Scope<'_>,policy:Policy,value:&str)->Result<Candidate,E>{
    f.lower_review_selector_regex_candidate(raw,query(q),scope,policy,value,Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default())}
fn section(raw:&[u8])->Result<String,Box<dyn Error>>{let mut r=BoundedZipReader::open(Cursor::new(raw),PackageLimits::default())?;
    let i=r.entries().iter().position(|e|e.path.as_str()=="Contents/section0.xml").ok_or("section")?;Ok(String::from_utf8(r.read_entry(i)?)?)}
fn exact(raw:&[u8],out:&Candidate,expected:String)->TestResult{
    let bytes=out.with_verified_bytes(<[u8]>::to_vec)?;assert_eq!(section(&bytes)?,expected);
    let mut a=BoundedZipReader::open(Cursor::new(raw),Default::default())?;let mut b=BoundedZipReader::open(Cursor::new(&bytes),Default::default())?;
    assert_eq!(a.entries().len(),b.entries().len());for i in 0..a.entries().len(){let path=a.entries()[i].path.clone();if path.as_str()=="Contents/section0.xml"{continue;}
        let j=b.entries().iter().position(|e|e.path==path).ok_or("part")?;assert_eq!(a.read_entry(i)?,b.read_entry(j)?);}Ok(())
}
fn at(block:&hwpx_package::document_import::search::selector::inventory::SourceIndexBlockDescriptor,n:usize)->Boundary{
    Boundary{paragraph_handle:block.paragraph_handle.clone(),block_index:block.block_index,normalized_scalar:n}}
#[test]
fn regex_replacement_numbered_named_whole_match_optional_groups_and_dollars_expand_per_occurrence()->TestResult{
    let raw=package("A12 B3 b")?;let f=forms(&raw)?;
    let out=replace(&f,&raw,r"(?P<letter>[AB])(?P<number>[0-9]+)|(?P<optional>a)?b",Scope::Document,all(),"${number}-$letter-${0}-$$-${optional}")?;
    exact(&raw,&out,section(&raw)?.replace("A12 B3 b","12-A-A12-$- 3-B-B3-$- --b-$-"))?;
    assert_eq!(out.receipt().output.matched_occurrences,3);assert!(out.receipt().captures_from_one_original_match_pass);
    let raw=package("Cat scatter CAT")?;let f=forms(&raw)?;let out=f.lower_review_selector_regex_candidate(&raw,
        Query{case_sensitive:false,whole_word:true,..query("(?P<word>cat)")},Scope::Document,all(),"${word}!",Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default())?;
    exact(&raw,&out,section(&raw)?.replace("Cat scatter CAT","Cat! scatter CAT!"))?;Ok(())
}
#[test]
fn regex_replacement_adjacent_different_expansions_and_empty_template_delete_only_original_ranges()->TestResult{
    let raw=package("a1b22c333")?;let f=forms(&raw)?;let out=replace(&f,&raw,r"([a-z])([0-9]+)",Scope::Document,all(),"${2}${1}Z")?;
    exact(&raw,&out,section(&raw)?.replace("a1b22c333","1aZ22bZ333cZ"))?;assert_eq!(out.receipt().output.changed_scalar_ranges,3);
    let deleted=replace(&f,&raw,r"[0-9]+",Scope::Document,all(),"")?;exact(&raw,&deleted,section(&raw)?.replace("a1b22c333","abc"))?;
    assert_eq!(deleted.receipt().expanded_replacement_bytes,0);Ok(())
}
#[test]
fn regex_replacement_all_four_scopes_clip_regex_before_captures_and_keep_unselected_text_exact()->TestResult{
    let raw=fixture::package()?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?;
    let i=inv.block_regions.iter().position(|r|*r==Region::MemoBody).ok_or("memo")?;let b=&inv.inventory.blocks[i];let start=at(b,7);let end=at(b,8);
    let node=inv.inventory.nodes.iter().find(|n|n.source_handle==b.paragraph_handle).ok_or("node")?;let ids=[node.node_id.clone()];
    for(scope,count)in[(Scope::Document,6),(Scope::Section(&inv.inventory.section_ids),6),(Scope::NodeSet(&ids),2),
        (Scope::Selection{index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},1)]{
        let pattern=if count==1{"^(K)$"}else{"(K)"};let out=replace(&f,&raw,pattern,scope,all(),"${1}X")?;assert_eq!(out.receipt().output.matched_occurrences,count);
        let old=section(&raw)?;let expected=if count==6{old.replace("K K","KX KX")}else if count==2{old.replace("MEMO K K","MEMO KX KX")}else{old.replace("MEMO K K","MEMO K KX")};exact(&raw,&out,expected)?;
    }Ok(())
}
#[test]
fn regex_replacement_review_policies_exclude_before_capture_and_match_limits_and_bind_receipts()->TestResult{
    let raw=fixture::package()?;let f=forms(&raw)?;let mut digests=std::collections::BTreeSet::new();
    for(h,m,count)in[(false,false,2),(true,false,4),(false,true,4),(true,true,6)]{let policy=Policy{include_hidden_explanations:h,include_memo_bodies:m};
        let out=f.lower_review_selector_regex_candidate(&raw,Query{max_results:count,..query("(K)")},Scope::Document,policy,"${1}X",Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default())?;
        assert_eq!(out.receipt().output.matched_occurrences,count);digests.insert(out.receipt().search_request_sha256);let mut expected=section(&raw)?.replace("BODY K K","BODY KX KX");
        if h{expected=expected.replace("HIDDEN K K","HIDDEN KX KX");}if m{expected=expected.replace("MEMO K K","MEMO KX KX");}exact(&raw,&out,expected)?;}
    assert_eq!(digests.len(),4);Ok(())
}
#[test]
fn regex_replacement_cross_run_captures_use_first_original_run_and_retain_all_styles_and_runs()->TestResult{
    let old="<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>A1</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>2B</hp:t></hp:run></hp:p>";
    let stub=fixture::with_body(old)?;let f=forms(&stub)?;assert!(replace(&f,&stub,r"A([0-9]+)(B)",Scope::Document,all(),"[$2/$1]").is_err());
    let raw=definition::package(old)?;let f=forms(&raw)?;let out=replace(&f,&raw,r"A([0-9]+)(B)",Scope::Document,all(),"[$2/$1]")?;
    exact(&raw,&out,section(&raw)?.replace("<hp:t>A1</hp:t>","<hp:t>[B/12]</hp:t>").replace("<hp:t>2B</hp:t>","<hp:t></hp:t>"))?;
    assert_eq!(out.receipt().output.changed_scalar_ranges,2);assert_eq!(out.receipt().output.changes.len(),2);Ok(())
}
#[test]
fn regex_replacement_hangul_nfc_captures_across_three_runs_emit_index_text_without_flattening_structure()->TestResult{
    let old="<hp:p id='1'><hp:run><hp:t>Xᄀ</hp:t></hp:run><hp:run><hp:t>ᅡ</hp:t></hp:run><hp:run><hp:t>ᆨY</hp:t></hp:run></hp:p>";
    let raw=fixture::with_body(old)?;let f=forms(&raw)?;let out=replace(&f,&raw,"(?P<syllable>각)",Scope::Document,all(),"${syllable}!")?;
    exact(&raw,&out,section(&raw)?.replace("Xᄀ","X각!").replace('ᅡ',"").replace("ᆨY","Y"))?;
    assert_eq!(out.receipt().output.changed_scalar_ranges,3);assert!(out.receipt().capture_values_are_index_nfc_text);Ok(())
}
#[test]
fn regex_replacement_partial_nfc_expansion_and_noncontiguous_original_contributors_reject_without_output()->TestResult{
    let raw=package("a&#x315;&#x300;")?;let f=forms(&raw)?;
    assert!(matches!(replace(&f,&raw,"à",Scope::Document,all(),"X"),Err(E::Compile(Compile::Selection))));
    exact(&raw,&replace(&f,&raw,"à\u{315}",Scope::Document,all(),"X")?,section(&raw)?.replace("a&#x315;&#x300;","X"))?;
    let raw=package("&#x344;")?;let f=forms(&raw)?;assert!(matches!(replace(&f,&raw,"\u{308}",Scope::Document,all(),"X"),Err(E::Compile(Compile::Selection))));Ok(())
}
#[test]
fn regex_replacement_unchanged_expansions_preserve_entity_bytes_and_noop_is_not_a_candidate()->TestResult{
    let raw=package("&#65; B")?;let f=forms(&raw)?;
    assert!(matches!(replace(&f,&raw,"(A)",Scope::Document,all(),"$0"),Err(E::Compile(Compile::NoChange))));
    let out=replace(&f,&raw,"(A)|(B)",Scope::Document,all(),"${1}")?;exact(&raw,&out,section(&raw)?.replace("&#65; B","&#65; "))?;
    assert_eq!(out.receipt().output.matched_occurrences,2);assert_eq!(out.receipt().output.changed_scalar_ranges,1);Ok(())
}
#[test]
fn regex_replacement_control_bytes_are_preserved_and_control_matches_or_captured_controls_cannot_be_text_edits()->TestResult{
    let old=format!("A1{TAB}B2<hp:lineBreak> </hp:lineBreak>C3");let raw=package(&old)?;let f=forms(&raw)?;
    let out=replace(&f,&raw,r"([A-Z])([0-9])",Scope::Document,all(),"$2$1")?;
    exact(&raw,&out,section(&raw)?.replace("A1","1A").replace("B2","2B").replace("C3","3C"))?;
    assert_eq!(out.receipt().output.changes[0].preserved_controls,2);assert!(out.receipt().output.original_control_bytes_preserved);
    for q in[r"\t",r"A1\tB2",r"B2\nC3"]{assert!(matches!(replace(&f,&raw,q,Scope::Document,all(),"X"),Err(E::Compile(Compile::Selection))));}
    assert!(matches!(replace(&f,&raw,r"(\t)",Scope::Document,all(),"$1"),Err(E::Template)));Ok(())
}
#[test]
fn regex_replacement_memo_payload_is_writable_but_its_cache_and_enclosing_fields_remain_protected()->TestResult{
    let body=fixture::body().replace("CACHE FROZEN","CACHE K");let raw=fixture::with_body(&body)?;let f=forms(&raw)?;
    assert!(matches!(replace(&f,&raw,"(K)",Scope::Document,all(),"${1}X"),Err(E::Compile(Compile::FieldContent))));
    let index=f.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?;let i=inv.block_regions.iter().position(|r|*r==Region::MemoBody).ok_or("memo")?;
    let node=inv.inventory.nodes.iter().find(|n|n.source_handle==inv.inventory.blocks[i].paragraph_handle).ok_or("node")?;
    let out=replace(&f,&raw,"(K)",Scope::NodeSet(&[node.node_id.clone()]),all(),"${1}X")?;exact(&raw,&out,section(&raw)?.replace("MEMO K K","MEMO KX KX"))?;
    let outer=format!("<hp:p id='1'><hp:run><hp:ctrl><hp:fieldBegin id='99' type='DOC_DATE' editable='1'/></hp:ctrl>{}<hp:ctrl><hp:fieldEnd beginIDRef='99'/></hp:ctrl></hp:run></hp:p>",fixture::run_body());
    let raw=fixture::with_body(&outer)?;let f=forms(&raw)?;assert!(matches!(replace(&f,&raw,"MEMO (K)",Scope::Document,all(),"X"),Err(E::Compile(Compile::FieldContent))));Ok(())
}
#[test]
fn regex_replacement_table_cell_size_and_ancestor_protection_precede_writes()->TestResult{
    let body=table::table(300);for(blocked,body)in[(false,body.clone()),(true,body.replace("lock='0'","lock='1'")),(true,body.replacen("protect='0'","protect='1'",1)),(true,body.replace("hasMargin='0' protect='0'","hasMargin='0' protect='1'"))]{
        let raw=assembly::package(&body)?;let f=forms(&raw)?;let out=replace(&f,&raw,"CELL-(OLD)",Scope::Document,all(),"NEW-$1");
        if blocked{assert!(matches!(out,Err(E::Compile(Compile::Protection))));}else{exact(&raw,&out?,section(&raw)?.replace("CELL-OLD","NEW-OLD"))?;}}
    Ok(())
}
#[test]
fn regex_replacement_template_syntax_unknown_references_mode_and_pattern_fail_before_any_candidate()->TestResult{
    let raw=package("K")?;let f=forms(&raw)?;
    for template in["$","$!","${}","${unfinished","\n","\t","\u{0000}"]{assert!(matches!(validate_regex_replacement_template(template),Err(E::Template)));}
    for template in["$9","${missing}","$name_suffix","$184467440737095516160"]{assert!(matches!(replace(&f,&raw,"(?P<name>absent)",Scope::Document,all(),template),Err(E::Template)));}
    assert!(matches!(replace(&f,&raw,"(",Scope::Document,all(),"$0"),Err(E::Search(SourceSearchError::Pattern))));
    assert!(matches!(f.lower_review_selector_regex_candidate(&raw,Query{mode:Mode::Literal,..query("K")},Scope::Document,all(),"X",Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default()),Err(E::Mode)));
    let out=replace(&f,&raw,"K",Scope::Document,all(),"$${literal}")?;exact(&raw,&out,section(&raw)?.replace(">K<",">${literal}<"))?;Ok(())
}
#[test]
fn regex_replacement_match_provenance_expansion_total_and_per_value_budgets_fail_without_truncation()->TestResult{
    let raw=package("K K")?;let f=forms(&raw)?;
    assert!(matches!(f.lower_review_selector_regex_candidate(&raw,Query{max_results:1,..query("K")},Scope::Document,all(),"X",Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default()),Err(E::Search(SourceSearchError::Limit))));
    let limits=SourceSearchLimits::new(Config{result_bytes:50_000,..Default::default()})?;
    assert!(matches!(f.lower_review_selector_regex_candidate(&raw,query("K"),Scope::Document,all(),&"X".repeat(30_000),Run::FirstOriginalRunRetainAllRuns,limits,Default::default()),Err(E::Limit)));
    let raw=package(&"A".repeat(8192))?;let f=forms(&raw)?;assert!(matches!(replace(&f,&raw,"(?P<a>A+)",Scope::Document,all(),&"${a}".repeat(129)),Err(E::Limit)));
    assert!(matches!(validate_regex_replacement_template(&"X".repeat(PatchLimits::default().config().max_value_bytes+1)),Err(E::Limit)));Ok(())
}
#[test]
fn regex_replacement_original_proof_stale_source_scope_and_writer_bounds_remain_required()->TestResult{
    let raw=fixture::package()?;let f=forms(&raw)?;let other=forms(&raw)?;let proof=f.reconstruct_source_for_verification(&raw)?;
    assert!(matches!(proof.lower_review_selector_regex_candidate(&other,query("K"),Scope::Document,all(),"X",Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default()),Err(E::Source)));
    let changed=fixture::with_body(&fixture::body().replace("MEMO K K","DIFFERENT"))?;assert!(matches!(replace(&f,&changed,"K",Scope::Document,all(),"X"),Err(E::Source)));
    let index=f.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?;let start=at(&inv.inventory.blocks[0],0);let end=at(&inv.inventory.blocks[0],1);
    assert!(matches!(replace(&f,&raw,"K",Scope::Selection{index_sha256:[0;32],start:&start,end:&end},all(),"X"),Err(E::Search(SourceSearchError::Scope))));
    assert!(f.lower_review_selector_regex_candidate(&raw,query("K"),Scope::Document,all(),"X",Run::FirstOriginalRunRetainAllRuns,Default::default(),WriterLimits::new(WriterLimitConfig{max_output_bytes:1})?).is_err());Ok(())
}
#[test]
fn regex_replacement_zero_width_is_not_silently_skipped_and_no_matches_are_not_success()->TestResult{
    // An empty match immediately after a nonempty match is suppressed by the original engine.
    // Keep that behavior, then use a nonmatching gap to ensure the terminal empty match exists.
    let raw=package("AA")?;let f=forms(&raw)?;let out=replace(&f,&raw,"A|$",Scope::Document,all(),"X")?;exact(&raw,&out,section(&raw)?.replace(">AA<",">XX<"))?;
    let raw=package("AA Z")?;let f=forms(&raw)?;let original=Sha256::digest(&raw);
    for q in["^","A|$"]{let index=f.source_review_scope_index(&raw,Default::default())?;assert!(index.find(query(q),Scope::Document,all())?.result().matches().iter().any(|m|m.zero_width));
        assert!(matches!(replace(&f,&raw,q,Scope::Document,all(),"X"),Err(E::Compile(Compile::Selection))));}
    assert!(matches!(replace(&f,&raw,"absent",Scope::Document,all(),"X"),Err(E::Compile(Compile::NoMatches))));assert_eq!(Sha256::digest(&raw),original);Ok(())
}
#[test]
fn regex_replacement_many_distinct_expansions_share_one_protection_map_and_keep_receipts_private()->TestResult{
    let text=(0..100).map(|i|format!("Q{}&amp;",i%10)).collect::<String>();let body=fixture::body().replace("HIDDEN K K",&format!("{TAB}{text}<hp:lineBreak/>")).replace("MEMO K K",&text.replace("&amp;","&#x26;"));
    let raw=fixture::with_body(&body)?;let f=forms(&raw)?;let out=replace(&f,&raw,"Q(?P<d>[0-9])",Scope::Document,all(),"${d}X")?;
    let mut expected=section(&raw)?;for i in 0..10{expected=expected.replace(&format!("Q{i}"),&format!("{i}X"));}exact(&raw,&out,expected)?;
    let receipt=out.receipt();let xml=PreservingXmlDocument::parse(section(&raw)?.as_bytes())?;assert_eq!(receipt.output.observed_protection_element_visits,xml.elements().len()*2);
    assert_eq!(receipt.output.observed_protection_parts,1);assert_eq!(receipt.output.matched_occurrences,200);assert_eq!(receipt.expanded_replacement_bytes,400);
    assert!(!serde_json::to_string(receipt)?.contains("PRIVATE")&&!format!("{out:?}{receipt:?}").contains("PRIVATE"));
    assert!(!receipt.native_or_execution_authority&&!receipt.zero_width_control_or_field_cache_edit_qualified);assert_eq!(receipt.expansion_sha256,receipt.output.replacement_sha256);Ok(())
}
#[test]
fn regex_replacement_empty_optional_capture_work_is_bounded_even_without_output_growth()->TestResult{
    let template="${1}".repeat(32);let limits=SourceSearchLimits::new(Config{decomposed_scalars:512,..Default::default()})?;
    let raw=package(&"b".repeat(15))?;let f=forms(&raw)?;let out=f.lower_review_selector_regex_candidate(&raw,query("(a)?b"),Scope::Document,all(),&template,
        Run::FirstOriginalRunRetainAllRuns,limits,Default::default())?;
    assert_eq!(out.receipt().expanded_replacement_bytes,0);assert_eq!(out.receipt().expansion_work_units,512);assert_eq!(out.receipt().expansion_work_limit,512);
    let raw=package(&"b".repeat(16))?;let f=forms(&raw)?;assert!(matches!(f.lower_review_selector_regex_candidate(&raw,query("(a)?b"),Scope::Document,all(),&template,
        Run::FirstOriginalRunRetainAllRuns,limits,Default::default()),Err(E::Limit)));Ok(())
}
