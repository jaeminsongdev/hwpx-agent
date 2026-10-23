use hwpx_package::{BoundedZipReader,PackageLimits,PreservingXmlDocument,WriterLimits,WriterLimitConfig,
    document_import::{ImportedSourcePackage,SourceImportLimits,forms::ImportedDocumentForms,
        search::{SourceSearchQuery as Query,SourceSearchMode as Mode,SourceSearchLimits,SourceSearchLimitConfig as Config,
            scope::SourceSearchScope as Scope,reviews::{SourceReviewTextPolicy as Policy,SourceTextRegion as Region},
            replacement::{SourceLiteralReplacementError as E,SourceReplacementRunPolicy as Run,
                atoms::review::{SourceReviewLiteralCandidate,SOURCE_REVIEW_LITERAL_PROFILE}}}}};
use domain_ir::{DocumentId,LogicalId};
use sha2::{Digest as _,Sha256};
use std::{error::Error,io::Cursor};
#[allow(dead_code)] #[path="support/document_import_field_fixture.rs"] mod fixture;
#[allow(dead_code)] #[path="support/document_import_review_assembly_fixture.rs"] mod assembly;
#[allow(dead_code)] #[path="support/review_cell_output_fixture.rs"] mod table;
type TestResult=Result<(),Box<dyn Error>>;
const TAB:&str="<hp:tab width='8000' leader='0' type='0'/>";
fn run_body()->String {"<hp:t>BODY K</hp:t><hp:ctrl><hp:hiddenComment><hp:subList><hp:p id='11'><hp:run><hp:t>HIDDEN K</hp:t></hp:run></hp:p></hp:subList></hp:hiddenComment></hp:ctrl><hp:ctrl><hp:fieldBegin id='17' type='MEMO' editable='0'><hp:parameters cnt='0'/><hp:subList><hp:p id='12'><hp:run><hp:t>MEMO K</hp:t></hp:run></hp:p></hp:subList><hp:metaTag>{&quot;author&quot;:&quot;PRIVATE-AUTHOR&quot;}</hp:metaTag></hp:fieldBegin></hp:ctrl><hp:t>CACHE FROZEN</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='17'/></hp:ctrl><hp:t>TAIL</hp:t>".into()}
fn body()->String {format!("<hp:p id='1'><hp:run>{}</hp:run></hp:p>",run_body())}
fn all()->Policy {Policy {include_hidden_explanations:true,include_memo_bodies:true}}
fn query(q:&str)->Query<'_> {Query {query:q,mode:Mode::Literal,case_sensitive:true,whole_word:false,max_results:10000}}
fn forms(b:&[u8],id:&str)->Result<ImportedDocumentForms,Box<dyn Error>> {Ok(ImportedDocumentForms::import(ImportedSourcePackage::import(b,DocumentId::parse(id)?,Sha256::digest(b).into(),SourceImportLimits::default())?)?)}
fn replace(f:&ImportedDocumentForms,b:&[u8],q:&str,policy:Policy,value:&str)->Result<SourceReviewLiteralCandidate,E> {
    f.lower_review_literal_candidate(b,query(q),Scope::MappedDocument,policy,value,Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default())
}
fn section(b:&[u8])->Result<String,Box<dyn Error>> {let mut r=BoundedZipReader::open(Cursor::new(b),PackageLimits::default())?;
    let i=r.entries().iter().position(|e|e.path.as_str()=="Contents/section0.xml").ok_or("section")?;Ok(String::from_utf8(r.read_entry(i)?)?)}
fn exact(b:&[u8],out:&SourceReviewLiteralCandidate,old:&str,new:&str)->TestResult {
    let output=out.with_verified_bytes(<[u8]>::to_vec)?;assert_eq!(section(&output)?,section(b)?.replacen(old,new,1));
    let mut a=BoundedZipReader::open(Cursor::new(b),PackageLimits::default())?;let mut z=BoundedZipReader::open(Cursor::new(&output),PackageLimits::default())?;
    for i in 0..a.entries().len() {let path=&a.entries()[i].path;if path.as_str()=="Contents/section0.xml"{continue;}
        let j=z.entries().iter().position(|e|&e.path==path).ok_or("part")?;assert_eq!(a.read_entry(i)?,z.read_entry(j)?);}
    assert_eq!(out.receipt().output_review_import.source_package_sha256,out.receipt().output.output_package_sha256);Ok(())
}
#[test]
fn review_literal_four_explicit_policies_replace_only_selected_file_regions_and_preserve_cache()->TestResult {
    let old=body();let b=fixture::package(&old)?;let f=forms(&b,"policies")?;
    for (hidden,memo,count) in [(false,false,1),(true,false,2),(false,true,2),(true,true,3)] {
        let policy=Policy {include_hidden_explanations:hidden,include_memo_bodies:memo};let out=replace(&f,&b,"K",policy,"X")?;
        let mut expected=old.replace("BODY K","BODY X");if hidden{expected=expected.replace("HIDDEN K","HIDDEN X");}if memo{expected=expected.replace("MEMO K","MEMO X");}
        exact(&b,&out,&old,&expected)?;let r=out.receipt();assert_eq!(r.profile,SOURCE_REVIEW_LITERAL_PROFILE);assert_eq!(r.output.profile,SOURCE_REVIEW_LITERAL_PROFILE);
        assert_eq!(r.output.matched_occurrences,count);assert_eq!(r.permitted_memo_payload_bodies,usize::from(memo));
        let mut regions=vec![Region::BodyAndNotes];if hidden{regions.push(Region::HiddenExplanation);}if memo{regions.push(Region::MemoBody);}assert_eq!(r.match_regions,regions);
        assert_eq!(r.source_review_import.hidden_explanations,r.output_review_import.hidden_explanations);assert_eq!(r.source_review_import.memo_fields,r.output_review_import.memo_fields);
        assert!(!r.output.field_cached_content_edit_qualified&&!r.native_author_visibility_resolution_or_execution_qualified);assert!(r.memo_payload_not_cached_result_verified);
    }Ok(())
}
#[test]
fn review_literal_memo_payload_is_not_cached_text_and_editable_flags_do_not_grant_cache_writes()->TestResult {
    for flag in ["0","1"] {let old=body().replace("editable='0'",&format!("editable='{flag}'"));let b=fixture::package(&old)?;let f=forms(&b,"memo-cache")?;
        let out=replace(&f,&b,"MEMO K",all(),"NEW<&")?;exact(&b,&out,&old,&old.replace("MEMO K","NEW&lt;&amp;"))?;
        assert!(matches!(replace(&f,&b,"CACHE FROZEN",all(),"X"),Err(E::FieldContent)));assert!(!out.receipt().output_review_import.native_author_time_binding_verified);
    }Ok(())
}
#[test]
fn review_literal_owning_memo_exemption_never_bypasses_an_enclosing_other_field_or_hidden_cache()->TestResult {
    let wrapped=format!("<hp:p id='1'><hp:run><hp:ctrl><hp:fieldBegin id='99' type='DOC_DATE' editable='1'/></hp:ctrl>{}<hp:ctrl><hp:fieldEnd beginIDRef='99'/></hp:ctrl></hp:run></hp:p>",run_body());
    let b=fixture::package(&wrapped)?;let f=forms(&b,"outer-cache")?;let index=f.source_review_text_index(&b,Default::default())?;
    for (q,region) in [("MEMO K",Region::MemoBody),("HIDDEN K",Region::HiddenExplanation)] {
        assert_eq!(index.find(query(q),Scope::MappedDocument,all())?.match_regions(),[region]);
        assert!(matches!(replace(&f,&b,q,all(),"X"),Err(E::FieldContent)));
    }Ok(())
}
#[test]
fn review_literal_malformed_or_nested_field_review_bodies_are_not_skipped_even_when_excluded()->TestResult {
    let old=body();
    for invalid in [old.replace("</hp:hiddenComment>","<hp:subList/></hp:hiddenComment>"),old.replace("<hp:ctrl><hp:fieldEnd beginIDRef='17'/></hp:ctrl>",""),
        old.replace("MEMO K","<hp:ctrl><hp:fieldBegin id='88' type='MEMO'/></hp:ctrl>nested<hp:ctrl><hp:fieldEnd beginIDRef='88'/></hp:ctrl>")] {
        let b=fixture::package(&invalid)?;if let Ok(f)=forms(&b,"invalid") {assert!(replace(&f,&b,"BODY",Policy::default(),"X").is_err());}
    }Ok(())
}
#[test]
fn review_literal_exclusions_precede_match_caps_and_excluded_selected_bodies_return_no_matches()->TestResult {
    let old=body().replace("HIDDEN K","HIDDEN K K");let b=fixture::package(&old)?;let f=forms(&b,"limits-policy")?;
    let q=Query {max_results:1,..query("K")};f.lower_review_literal_candidate(&b,q,Scope::MappedDocument,Policy::default(),"X",Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default())?;
    assert!(f.lower_review_literal_candidate(&b,q,Scope::MappedDocument,all(),"X",Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default()).is_err());
    let index=f.source_review_text_index(&b,Default::default())?;let found=index.find(query("HIDDEN"),Scope::MappedDocument,all())?;let id=found.matches().matches()[0].paragraph_anchor.opaque_handle.clone();
    assert!(matches!(f.lower_review_literal_candidate(&b,query("HIDDEN"),Scope::Paragraphs(&[id]),Policy::default(),"X",Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default()),Err(E::NoMatches)));
    assert!(f.lower_review_literal_candidate(&b,query("missing"),Scope::Paragraphs(&[LogicalId::parse("foreign")?]),all(),"X",Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default()).is_err());Ok(())
}
#[test]
fn review_literal_cross_run_hangul_nfc_and_mixed_controls_keep_original_metadata_and_wrapper_bytes()->TestResult {
    let old=body().replace("<hp:t>HIDDEN K</hp:t>",&format!("<hp:t>{TAB}ᄀ</hp:t></hp:run><hp:run><hp:t>ᅡᆨ<hp:lineBreak/></hp:t>"))
        .replace("<hp:t>MEMO K</hp:t>",&format!("<hp:t>ᄀ</hp:t></hp:run><hp:run><hp:t>ᅡᆨ{TAB}TAIL</hp:t>"));
    let b=fixture::package(&old)?;let f=forms(&b,"nfc")?;let out=replace(&f,&b,"각",all(),"한")?;
    exact(&b,&out,&old,&old.replace('ᄀ',"한").replace(['ᅡ','ᆨ'],""))?;assert_eq!(out.receipt().match_regions,[Region::HiddenExplanation,Region::MemoBody]);
    assert_eq!(out.receipt().output.changed_scalar_ranges,4);assert!(matches!(replace(&f,&b,"\t",all(),"X"),Err(E::Selection)));Ok(())
}
#[test]
fn review_literal_containing_table_cell_size_and_ancestor_protection_are_not_hidden_by_review_bodies()->TestResult {
    let original=table::table(300).replace("<hp:t>CELL-OLD</hp:t>",&run_body());let b=assembly::package(&original)?;let f=forms(&b,"table")?;
    assert!(replace(&f,&b,"MEMO K",all(),"X").is_ok());
    for blocked in [original.replace("lock='0'","lock='1'"),original.replacen("protect='0'","protect='1'",1),original.replace("hasMargin='0' protect='0'","hasMargin='0' protect='1'")] {
        let b=assembly::package(&blocked)?;let f=forms(&b,"protected")?;for q in ["MEMO K","HIDDEN K"] {assert!(matches!(replace(&f,&b,q,all(),"X"),Err(E::Protection)));}
    }Ok(())
}
#[test]
fn review_literal_cache_hit_aborts_the_whole_batch_and_bodyless_memo_has_no_exemption()->TestResult {
    let old=body().replace("CACHE FROZEN","CACHE K");let b=fixture::package(&old)?;let f=forms(&b,"cache-all")?;let digest:[u8;32]=Sha256::digest(&b).into();
    assert!(matches!(replace(&f,&b,"K",all(),"X"),Err(E::FieldContent)));assert_eq!(<[u8;32]>::from(Sha256::digest(&b)),digest);
    let old=old.replace("<hp:subList><hp:p id='12'><hp:run><hp:t>MEMO K</hp:t></hp:run></hp:p></hp:subList>","");
    let b=fixture::package(&old)?;let f=forms(&b,"bodyless")?;assert!(matches!(replace(&f,&b,"MEMO K",all(),"X"),Err(E::NoMatches)));
    assert!(matches!(replace(&f,&b,"CACHE K",all(),"X"),Err(E::FieldContent)));Ok(())
}
#[test]
fn review_literal_foreign_proof_stale_source_regex_controls_noop_and_no_match_fail_closed()->TestResult {
    let b=fixture::package(&body())?;let f=forms(&b,"proof")?;let foreign=forms(&b,"proof")?;let proof=f.reconstruct_source_for_verification(&b)?;
    assert!(matches!(proof.lower_review_literal_candidate(&foreign,query("K"),Scope::MappedDocument,all(),"X",Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default()),Err(E::Source)));
    let changed=fixture::package(&body().replace("MEMO K","CHANGED"))?;assert!(matches!(replace(&f,&changed,"K",all(),"X"),Err(E::Source)));
    assert!(matches!(f.lower_review_literal_candidate(&b,Query {mode:Mode::Regex,..query("K")},Scope::MappedDocument,all(),"X",Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default()),Err(E::Value)));
    for value in ["\t","\n","\r","\u{0000}","\u{1fffe}"] {assert!(matches!(replace(&f,&b,"K",all(),value),Err(E::Value)));}
    assert!(matches!(replace(&f,&b,"BODY K",all(),"BODY K"),Err(E::NoChange)));assert!(matches!(replace(&f,&b,"missing",all(),"X"),Err(E::NoMatches)));Ok(())
}
#[test]
fn review_literal_extended_corpus_scalar_paragraph_range_response_and_writer_caps_are_finite()->TestResult {
    let b=fixture::package(&body())?;let f=forms(&b,"bounds")?;f.body_structure().source_text_index(&b,SourceSearchLimits::new(Config {scalars:28,..Default::default()})?)?;
    for limits in [Config {scalars:28,..Default::default()},Config {paragraphs:1,..Default::default()},Config {result_bytes:1,..Default::default()}] {
        assert!(f.lower_review_literal_candidate(&b,query("K"),Scope::MappedDocument,Policy::default(),"X",Run::FirstOriginalRunRetainAllRuns,SourceSearchLimits::new(limits)?,Default::default()).is_err());
    }
    assert!(f.lower_review_literal_candidate(&b,query("K"),Scope::MappedDocument,all(),"X",Run::FirstOriginalRunRetainAllRuns,Default::default(),WriterLimits::new(WriterLimitConfig {max_output_bytes:1})?).is_err());
    let b=fixture::package(&body().replace("MEMO K",&"Q".repeat(4097)))?;let f=forms(&b,"range-cap")?;assert!(matches!(replace(&f,&b,"Q",all(),"X"),Err(E::Limit)));Ok(())
}
#[test]
fn review_literal_policy_and_original_review_projection_are_bound_without_private_metadata_or_values()->TestResult {
    let b=fixture::package(&body())?;let f=forms(&b,"binding")?;let first=replace(&f,&b,"BODY",Policy::default(),"PRIVATE-REPLACEMENT")?;
    let other=replace(&f,&b,"BODY",all(),"PRIVATE-REPLACEMENT")?;
    assert_ne!(first.receipt().review_search_request_sha256,other.receipt().review_search_request_sha256);assert_eq!(first.receipt().output.output_package_sha256,other.receipt().output.output_package_sha256);
    assert!(!serde_json::to_string(other.receipt())?.contains("PRIVATE"));assert!(!format!("{other:?}{:?}",other.receipt()).contains("PRIVATE"));
    let plain=fixture::package("<hp:p id='1'><hp:run><hp:t>plain</hp:t></hp:run></hp:p>")?;let f=forms(&plain,"empty-inventory")?;
    let out=replace(&f,&plain,"plain",all(),"X")?;assert_eq!(out.receipt().source_review_import.memo_fields,0);assert_eq!(out.receipt().permitted_memo_payload_bodies,0);Ok(())
}
#[test]
fn review_literal_many_matches_share_one_part_protection_map_and_one_original_body_projection()->TestResult {
    let old=body().replace("HIDDEN K",&format!("{TAB}{}<hp:lineBreak/>","Q&amp;".repeat(100))).replace("MEMO K",&"Q&#x26;".repeat(100));
    let b=fixture::package(&old)?;let f=forms(&b,"many")?;let out=replace(&f,&b,"Q",all(),"X")?;exact(&b,&out,&old,&old.replace('Q',"X"))?;
    let xml=PreservingXmlDocument::parse(section(&b)?.as_bytes())?;assert_eq!(out.receipt().output.observed_protection_element_visits,xml.elements().len()*2);
    assert_eq!(out.receipt().output.observed_protection_parts,1);assert_eq!(out.receipt().permitted_memo_payload_bodies,1);assert_eq!(out.receipt().output.matched_occurrences,200);Ok(())
}
