use hwpx_package::{BoundedZipReader,PackageLimits,WriterLimits,WriterLimitConfig,document_import::{ImportedSourcePackage,forms::ImportedDocumentForms,
    search::{SourceSearchQuery as Query,SourceSearchMode as Mode,SourceSearchLimits,SourceSearchLimitConfig as Config,
        selector::{SourceIndexScopeSelector as Scope,SourceIndexBoundary as Boundary},reviews::{SourceReviewTextPolicy as Policy,SourceTextRegion as Region},
        replacement::{SourceLiteralReplacementError as E,SourceReplacementRunPolicy as Run,atoms::review::selector::{SourceSelectorLiteralCandidate,SOURCE_SELECTOR_LITERAL_PROFILE}}}}};
use domain_ir::DocumentId;
use sha2::{Digest as _,Sha256};
use std::{error::Error,io::Cursor};
#[path="support/review_scope_fixture.rs"] mod fixture;
#[allow(dead_code)] #[path="support/document_import_review_assembly_fixture.rs"] mod assembly;
#[allow(dead_code)] #[path="support/review_cell_output_fixture.rs"] mod table;
type TestResult=Result<(),Box<dyn Error>>;
fn forms(raw:&[u8],id:&str)->Result<ImportedDocumentForms,Box<dyn Error>> {Ok(ImportedDocumentForms::import(ImportedSourcePackage::import(raw,DocumentId::parse(id)?,Sha256::digest(raw).into(),Default::default())?)?)}
fn query(q:&str)->Query<'_> {Query {query:q,mode:Mode::Literal,case_sensitive:true,whole_word:false,max_results:100}}
fn all()->Policy {Policy {include_hidden_explanations:true,include_memo_bodies:true}}
fn selected(f:&ImportedDocumentForms,raw:&[u8],region:Region)->Result<([u8;32],Boundary,Boundary),Box<dyn Error>> {
    let index=f.source_review_scope_index(raw,Default::default())?;let found=index.find(query("K"),Scope::Document,all())?;
    let (m,_)=found.result().matches().iter().zip(found.match_regions()).rev().find(|(_,r)|**r==region).ok_or("selected region")?;
    let start=Boundary {paragraph_handle:m.paragraph_anchor.opaque_handle.clone(),block_index:m.block_index,normalized_scalar:m.start_normalized_scalar};
    let end=Boundary {normalized_scalar:m.end_normalized_scalar,..start.clone()};Ok((found.scope_receipt().index_sha256,start,end))
}
fn replace(f:&ImportedDocumentForms,raw:&[u8],q:&str,scope:Scope<'_>,policy:Policy,value:&str)->Result<SourceSelectorLiteralCandidate,E> {
    f.lower_review_selector_literal_candidate(raw,query(q),scope,policy,value,Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default())
}
fn section(raw:&[u8])->Result<String,Box<dyn Error>> {let mut r=BoundedZipReader::open(Cursor::new(raw),PackageLimits::default())?;
    let n=r.entries().iter().position(|e|e.path.as_str()=="Contents/section0.xml").ok_or("section")?;Ok(String::from_utf8(r.read_entry(n)?)?)}
#[test]
fn selector_literal_partial_body_hidden_and_memo_replace_only_second_match_not_whole_paragraph()->TestResult {
    let raw=fixture::package()?;let f=forms(&raw,"selector-literal")?;
    for (region,label) in [(Region::BodyAndNotes,"BODY"),(Region::HiddenExplanation,"HIDDEN"),(Region::MemoBody,"MEMO")] {
        let (hash,start,end)=selected(&f,&raw,region)?;let output=replace(&f,&raw,"K",Scope::Selection {index_sha256:hash,start:&start,end:&end},all(),"X<&")?;
        let actual=output.with_verified_bytes(section)??;assert_eq!(actual,section(&raw)?.replace(&format!("{label} K K"),&format!("{label} K X&lt;&amp;")));
        assert_eq!(output.receipt().profile,SOURCE_SELECTOR_LITERAL_PROFILE);assert_eq!(output.receipt().body_candidate.output.matched_occurrences,1);
        assert!(output.receipt().scope_window_enforced&&!output.receipt().native_or_execution_authority);
        assert_eq!(output.receipt().selector.scope_sha256,output.receipt().body_candidate.output.scope_sha256);
    }Ok(())
}
#[test]
fn selector_literal_document_policies_and_supplemental_node_scope_preserve_cache_metadata_and_controls()->TestResult {
    let raw=fixture::package()?;let f=forms(&raw,"selector-literal")?;
    for (hidden,memo,count) in [(false,false,2),(true,false,4),(false,true,4),(true,true,6)] {
        let out=replace(&f,&raw,"K",Scope::Document,Policy {include_hidden_explanations:hidden,include_memo_bodies:memo},"X")?;let actual=out.with_verified_bytes(section)??;
        let mut expected=section(&raw)?.replace("BODY K K","BODY X X");if hidden{expected=expected.replace("HIDDEN K K","HIDDEN X X");}if memo{expected=expected.replace("MEMO K K","MEMO X X");}
        assert_eq!(actual,expected);assert_eq!(out.receipt().body_candidate.output.matched_occurrences,count);
        assert!(actual.contains("CACHE FROZEN")&&actual.contains("PRIVATE-AUTHOR")&&actual.contains("<hp:lineBreak/>"));}
    let index=f.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?;
    let position=inv.block_regions.iter().position(|r|*r==Region::MemoBody).ok_or("memo")?;let b=&inv.inventory.blocks[position];let node=inv.inventory.nodes.iter().find(|n|n.source_handle==b.paragraph_handle).ok_or("node")?;
    let out=replace(&f,&raw,"K",Scope::NodeSet(&[node.node_id.clone()]),all(),"X")?;
    assert_eq!(out.with_verified_bytes(section)??,section(&raw)?.replace("MEMO K K","MEMO X X"));Ok(())
}
#[test]
fn selector_literal_cache_match_outside_selection_does_not_expand_batch_but_selected_cache_stays_blocked()->TestResult {
    let raw=fixture::with_body(&fixture::body().replace("CACHE FROZEN","CACHE K"))?;let f=forms(&raw,"selector-cache")?;
    assert!(matches!(replace(&f,&raw,"K",Scope::Document,all(),"X"),Err(E::FieldContent)));
    let (hash,start,end)=selected(&f,&raw,Region::MemoBody)?;let out=replace(&f,&raw,"K",Scope::Selection {index_sha256:hash,start:&start,end:&end},all(),"X")?;
    assert_eq!(out.with_verified_bytes(section)??,section(&raw)?.replace("MEMO K K","MEMO K X"));
    assert!(matches!(replace(&f,&raw,"CACHE K",Scope::Document,all(),"X"),Err(E::FieldContent)));Ok(())
}
#[test]
fn selector_literal_owning_memo_payload_never_bypasses_an_enclosing_field_or_excluded_body_policy()->TestResult {
    let outer=format!("<hp:p id='1'><hp:run><hp:ctrl><hp:fieldBegin id='99' type='DOC_DATE' editable='1'/></hp:ctrl>{}<hp:ctrl><hp:fieldEnd beginIDRef='99'/></hp:ctrl></hp:run></hp:p>",fixture::run_body());
    let raw=fixture::with_body(&outer)?;let f=forms(&raw,"outer-selector")?;let (hash,start,end)=selected(&f,&raw,Region::MemoBody)?;
    assert!(matches!(replace(&f,&raw,"K",Scope::Selection {index_sha256:hash,start:&start,end:&end},all(),"X"),Err(E::FieldContent)));
    assert!(matches!(replace(&f,&raw,"K",Scope::Selection {index_sha256:hash,start:&start,end:&end},Policy::default(),"X"),Err(E::NoMatches)));Ok(())
}
#[test]
fn selector_literal_zero_width_control_regex_noop_and_invalid_values_never_become_output_candidates()->TestResult {
    let raw=fixture::package()?;let f=forms(&raw,"selector-values")?;let (hash,start,end)=selected(&f,&raw,Region::HiddenExplanation)?;
    assert!(matches!(replace(&f,&raw,"K",Scope::Selection {index_sha256:hash,start:&start,end:&start},all(),"X"),Err(E::NoMatches)));
    assert!(matches!(replace(&f,&raw,"K",Scope::Selection {index_sha256:hash,start:&start,end:&end},all(),"K"),Err(E::NoChange)));
    assert!(matches!(replace(&f,&raw,"\n",Scope::Document,all(),"X"),Err(E::Selection)));
    assert!(matches!(replace(&f,&raw,"K",Scope::Document,all(),"\n"),Err(E::Value)));
    assert!(matches!(f.lower_review_selector_literal_candidate(&raw,Query {mode:Mode::Regex,..query("K")},Scope::Document,all(),"X",Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default()),Err(E::Value)));Ok(())
}
#[test]
fn selector_literal_selected_memo_body_retains_table_cell_and_ancestor_protection()->TestResult {
    let table=table::table(300).replace("<hp:t>CELL-OLD</hp:t>",&fixture::run_body());
    for (blocked,body) in [(false,table.clone()),(true,table.replace("lock='0'","lock='1'")),(true,table.replacen("protect='0'","protect='1'",1))] {
        let raw=assembly::package(&body)?;let f=forms(&raw,"protected-selector")?;let (hash,start,end)=selected(&f,&raw,Region::MemoBody)?;
        let out=replace(&f,&raw,"K",Scope::Selection {index_sha256:hash,start:&start,end:&end},all(),"X");
        if blocked{assert!(matches!(out,Err(E::Protection)));}else{assert!(out.is_ok());}}
    Ok(())
}
#[test]
fn selector_literal_nfc_across_memo_runs_keeps_unselected_scalars_and_original_run_structure()->TestResult {
    let body=fixture::body().replace("<hp:t>MEMO K K</hp:t>","<hp:t>Xᄀ</hp:t></hp:run><hp:run><hp:t>ᅡ</hp:t></hp:run><hp:run><hp:t>ᆨY</hp:t>");
    let raw=fixture::with_body(&body)?;let f=forms(&raw,"nfc-selector")?;let index=f.source_review_scope_index(&raw,Default::default())?;
    let found=index.find(query("각"),Scope::Document,all())?;let m=&found.result().matches()[0];let start=Boundary {paragraph_handle:m.paragraph_anchor.opaque_handle.clone(),block_index:m.block_index,normalized_scalar:1};let end=Boundary {normalized_scalar:2,..start.clone()};
    let out=replace(&f,&raw,"각",Scope::Selection {index_sha256:found.scope_receipt().index_sha256,start:&start,end:&end},all(),"NEW")?;
    assert_eq!(out.with_verified_bytes(section)??,section(&raw)?.replace("<hp:t>Xᄀ</hp:t></hp:run><hp:run><hp:t>ᅡ</hp:t></hp:run><hp:run><hp:t>ᆨY</hp:t>","<hp:t>XNEW</hp:t></hp:run><hp:run><hp:t></hp:t></hp:run><hp:run><hp:t>Y</hp:t>"));
    assert_eq!(out.receipt().body_candidate.output.changed_scalar_ranges,3);Ok(())
}
#[test]
fn selector_literal_foreign_proof_stale_selection_response_writer_caps_and_receipts_remain_bounded_and_redacted()->TestResult {
    let raw=fixture::package()?;let f=forms(&raw,"selector-proof")?;let other=forms(&raw,"selector-proof")?;let proof=f.reconstruct_source_for_verification(&raw)?;
    assert!(matches!(proof.lower_review_selector_literal_candidate(&other,query("K"),Scope::Document,all(),"X",Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default()),Err(E::Source)));
    let (_,start,end)=selected(&f,&raw,Region::MemoBody)?;assert!(replace(&f,&raw,"K",Scope::Selection {index_sha256:[0;32],start:&start,end:&end},all(),"X").is_err());
    assert!(f.lower_review_selector_literal_candidate(&raw,query("K"),Scope::Document,all(),"X",Run::FirstOriginalRunRetainAllRuns,Default::default(),WriterLimits::new(WriterLimitConfig {max_output_bytes:1})?).is_err());
    assert!(f.lower_review_selector_literal_candidate(&raw,query("K"),Scope::Document,all(),"X",Run::FirstOriginalRunRetainAllRuns,SourceSearchLimits::new(Config {result_bytes:1,..Default::default()})?,Default::default()).is_err());
    let out=replace(&f,&raw,"K",Scope::Document,all(),"PRIVATE-REPLACEMENT")?;assert!(!serde_json::to_string(out.receipt())?.contains("PRIVATE"));assert!(!format!("{out:?}{:?}",out.receipt()).contains("PRIVATE"));
    assert!(!out.receipt().body_candidate.output.field_cached_content_edit_qualified&&!out.receipt().body_candidate.native_author_visibility_resolution_or_execution_qualified);Ok(())
}
