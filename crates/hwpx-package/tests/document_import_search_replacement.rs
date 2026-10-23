use hwpx_package::{WriterLimits,WriterLimitConfig,BoundedZipReader,PackageLimits,document_import::{ImportedSourcePackage,SourceImportLimits,forms::ImportedDocumentForms,
    search::{SourceSearchQuery as Query,SourceSearchMode as Mode,SourceSearchLimits,SourceSearchLimitConfig as Config,scope::SourceSearchScope as Scope,
        replacement::{SourceLiteralReplacementError as E,SourceReplacementRunPolicy as Policy,SourceLiteralReplacementCandidate}}}};
use domain_ir::{DocumentId,LogicalId};
use sha2::{Digest as _,Sha256};
use std::{error::Error,io::Cursor};
#[allow(dead_code)] #[path="support/search_definition_fixture.rs"] mod fixture;
#[allow(dead_code)] #[path="support/document_import_review_assembly_fixture.rs"] mod assembly;
#[allow(dead_code)] #[path="support/review_cell_output_fixture.rs"] mod table;
type TestResult=Result<(),Box<dyn Error>>;
fn forms(b:&[u8],id:&str)->Result<ImportedDocumentForms,Box<dyn Error>> {Ok(ImportedDocumentForms::import(ImportedSourcePackage::import(b,
    DocumentId::parse(id)?,Sha256::digest(b).into(),SourceImportLimits::default())?)?)}
fn query(q:&str)->Query<'_> {Query {query:q,mode:Mode::Literal,case_sensitive:true,whole_word:false,max_results:100}}
fn replace(forms:&ImportedDocumentForms,b:&[u8],q:&str,value:&str)->Result<SourceLiteralReplacementCandidate,E> {
    forms.lower_literal_search_candidate(b,query(q),Scope::MappedDocument,value,Policy::FirstOriginalRunRetainAllRuns,Default::default(),Default::default())}
fn section(b:&[u8])->Result<String,Box<dyn Error>> {let mut r=BoundedZipReader::open(Cursor::new(b),PackageLimits::default())?;
    let i=r.entries().iter().position(|e|e.path.as_str()=="Contents/section0.xml").ok_or("section")?;Ok(String::from_utf8(r.read_entry(i)?)?)}
#[test]
fn literal_replacement_crosses_styled_runs_and_preserves_empty_runs_entities_and_other_parts()->TestResult {
    let b=fixture::package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>A&#x26;B</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>CD&#38;Z</hp:t></hp:run></hp:p>")?;
    let f=forms(&b,"runs")?;let output=replace(&f,&b,"BCD","X<&")?;let next=output.with_verified_bytes(<[u8]>::to_vec)?;
    assert!(section(&next)?.contains("<hp:run charPrIDRef='0'><hp:t>A&#x26;X&lt;&amp;</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>&#38;Z</hp:t>"));
    assert_eq!(output.receipt().matched_occurrences,1);assert_eq!(output.receipt().changes.len(),2);
    let mut old=BoundedZipReader::open(Cursor::new(&b),PackageLimits::default())?;let mut new=BoundedZipReader::open(Cursor::new(&next),PackageLimits::default())?;
    for i in 0..old.entries().len(){let path=&old.entries()[i].path;if path.as_str()=="Contents/section0.xml"{continue;}
        let j=new.entries().iter().position(|e|&e.path==path).ok_or("part")?;assert_eq!(old.read_entry(i)?,new.read_entry(j)?);}assert!(section(&b)?.contains("A&#x26;B"));Ok(())
}
#[test]
fn literal_replacement_nfc_jamo_provenance_spans_three_original_runs_without_deleting_structure()->TestResult {
    let b=fixture::package("<hp:p id='1'><hp:run><hp:t>ᄀ</hp:t></hp:run><hp:run><hp:t>ᅡ</hp:t></hp:run><hp:run><hp:t>ᆨ</hp:t></hp:run></hp:p>")?;
    let f=forms(&b,"jamo")?;let output=replace(&f,&b,"각","한")?;
    assert!(output.with_verified_bytes(section)??.contains("<hp:t>한</hp:t></hp:run><hp:run><hp:t></hp:t></hp:run><hp:run><hp:t></hp:t>"));
    assert_eq!(output.receipt().changed_scalar_ranges,3);assert!(output.receipt().original_selection_contiguity_verified);Ok(())
}
#[test]
fn literal_replacement_canonical_reordering_requires_contiguous_complete_original_selection()->TestResult {
    let b=fixture::package("<hp:p id='1'><hp:run><hp:t>a&#x315;&#x300;</hp:t></hp:run></hp:p>")?;let f=forms(&b,"reorder")?;
    assert!(matches!(replace(&f,&b,"à","X"),Err(E::Selection)));
    assert!(replace(&f,&b,"à\u{315}","X")?.with_verified_bytes(section)??.contains("<hp:t>X</hp:t>"));
    let b=fixture::package("<hp:p id='1'><hp:run><hp:t>&#x344;</hp:t></hp:run></hp:p>")?;let f=forms(&b,"expansion")?;
    assert!(matches!(replace(&f,&b,"\u{308}","X"),Err(E::Selection)));Ok(())
}
#[test]
fn literal_replacement_multiple_occurrences_share_leaf_delete_and_reject_unqualified_control_text()->TestResult {
    let b=fixture::package("<hp:p id='1'><hp:run><hp:t>K&#38;K TAIL</hp:t></hp:run></hp:p>")?;let f=forms(&b,"multiple")?;
    let out=replace(&f,&b,"K","X")?;assert_eq!(out.receipt().matched_occurrences,2);assert_eq!(out.receipt().changes.len(),1);
    assert!(out.with_verified_bytes(section)??.contains("X&#38;X TAIL"));
    assert!(replace(&f,&b,"K","")?.with_verified_bytes(section)??.contains("<hp:t>&#38; TAIL</hp:t>"));
    for value in ["X\r","X\n","X\t","\u{1fffe}"] {assert!(matches!(replace(&f,&b,"K",value),Err(E::Value)));}Ok(())
}
#[test]
fn literal_replacement_scope_whole_word_and_casefold_bind_real_original_matches()->TestResult {
    let b=fixture::package("<hp:p id='1'><hp:run><hp:t>Cat scatter CAT</hp:t></hp:run></hp:p><hp:p id='2'><hp:run><hp:t>cat</hp:t></hp:run></hp:p>")?;let f=forms(&b,"scope")?;
    let index=f.body_structure().source_text_index(&b,Default::default())?;let matches=index.find(query("Cat"))?;let id=matches.matches()[0].paragraph_anchor.opaque_handle.clone();
    let q=Query {case_sensitive:false,whole_word:true,..query("cat")};let out=f.lower_literal_search_candidate(&b,q,Scope::Paragraphs(&[id]),"DOG",Policy::FirstOriginalRunRetainAllRuns,Default::default(),Default::default())?;
    let text=out.with_verified_bytes(section)??;assert!(text.contains("DOG scatter DOG"));assert!(text.contains("<hp:t>cat</hp:t>"));assert_eq!(out.receipt().matched_occurrences,2);
    assert!(f.lower_literal_search_candidate(&b,q,Scope::Paragraphs(&[LogicalId::parse("foreign")?]),"X",Policy::FirstOriginalRunRetainAllRuns,Default::default(),Default::default()).is_err());Ok(())
}
#[test]
fn literal_replacement_observed_table_cell_and_size_protection_reject_the_whole_candidate()->TestResult {
    let ordinary=table::table(300);let original=assembly::package(&ordinary)?;let f=forms(&original,"table")?;
    assert!(replace(&f,&original,"CELL-OLD","NEW")?.with_verified_bytes(section)??.contains("NEW"));
    for protected in [ordinary.replace("lock='0'","lock='1'"),ordinary.replacen("protect='0'","protect='1'",1),
        ordinary.replace("hasMargin='0' protect='0'","hasMargin='0' protect='1'")] {
        let b=assembly::package(&protected)?;let f=forms(&b,"protected")?;assert!(matches!(replace(&f,&b,"CELL-OLD","NEW"),Err(E::Protection)));}Ok(())
}
#[test]
fn literal_replacement_field_cached_results_are_not_overwritten_even_when_editable_is_declared()->TestResult {
    for editable in ["0","1"] {let b=fixture::package(&format!("<hp:p id='1'><hp:run><hp:t>OUTSIDE</hp:t><hp:ctrl><hp:fieldBegin id='17' type='MEMO' editable='{editable}'/></hp:ctrl><hp:t>CACHE</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='17'/></hp:ctrl></hp:run></hp:p>"))?;
        let f=forms(&b,"field")?;assert!(matches!(replace(&f,&b,"CACHE","X"),Err(E::FieldContent)));assert!(replace(&f,&b,"OUTSIDE","X").is_ok());}Ok(())
}
#[test]
fn literal_replacement_mixed_atoms_controls_opaque_and_paragraph_boundaries_never_become_plain_leaf_edits()->TestResult {
    let b=fixture::package("<hp:p id='1'><hp:run><hp:t>A<hp:tab width='8000' leader='0' type='0'/>B</hp:t><u:future/><hp:t>C</hp:t></hp:run></hp:p><hp:p id='2'><hp:run><hp:t>D</hp:t></hp:run></hp:p>")?;
    let f=forms(&b,"barriers")?;assert!(matches!(replace(&f,&b,"A","X"),Err(E::Selection)));
    for q in ["BC","CD"] {assert!(matches!(replace(&f,&b,q,"X"),Err(E::NoMatches)));}Ok(())
}
#[test]
fn literal_replacement_stale_foreign_proofs_invalid_values_regex_noop_and_zero_matches_are_closed()->TestResult {
    let b=fixture::package("<hp:p id='1'><hp:run><hp:t>K</hp:t></hp:run></hp:p>")?;let f=forms(&b,"proof")?;let other=forms(&b,"proof")?;let proof=f.reconstruct_source_for_verification(&b)?;
    assert!(matches!(proof.lower_literal_search_candidate(&other,query("K"),Scope::MappedDocument,"X",Policy::FirstOriginalRunRetainAllRuns,Default::default(),Default::default()),Err(E::Source)));
    let changed=fixture::package("<hp:p id='1'><hp:run><hp:t>CHANGED</hp:t></hp:run></hp:p>")?;assert!(matches!(replace(&f,&changed,"K","X"),Err(E::Source)));
    assert!(matches!(replace(&f,&b,"K","K"),Err(E::NoChange)));assert!(matches!(replace(&f,&b,"missing","X"),Err(E::NoMatches)));assert!(matches!(replace(&f,&b,"K","\u{0000}"),Err(E::Value)));
    assert!(matches!(f.lower_literal_search_candidate(&b,Query {mode:Mode::Regex,..query("K")},Scope::MappedDocument,"X",Policy::FirstOriginalRunRetainAllRuns,Default::default(),Default::default()),Err(E::Value)));Ok(())
}
#[test]
fn literal_replacement_match_writer_output_limits_and_redacted_receipts_never_return_partial_success()->TestResult {
    let b=fixture::package("<hp:p id='1'><hp:run><hp:t>K K</hp:t></hp:run></hp:p>")?;let f=forms(&b,"limits")?;
    assert!(f.lower_literal_search_candidate(&b,Query {max_results:1,..query("K")},Scope::MappedDocument,"X",Policy::FirstOriginalRunRetainAllRuns,Default::default(),Default::default()).is_err());
    assert!(f.lower_literal_search_candidate(&b,query("K"),Scope::MappedDocument,"X",Policy::FirstOriginalRunRetainAllRuns,
        SourceSearchLimits::new(Config {result_bytes:1,..Default::default()})?,Default::default()).is_err());
    assert!(f.lower_literal_search_candidate(&b,query("K"),Scope::MappedDocument,"X",Policy::FirstOriginalRunRetainAllRuns,Default::default(),WriterLimits::new(WriterLimitConfig {max_output_bytes:1})?).is_err());
    let out=replace(&f,&b,"K","PRIVATE-REPLACEMENT")?;let receipt=serde_json::to_string(out.receipt())?;assert!(!receipt.contains("PRIVATE"));assert!(!format!("{out:?}{:?}",out.receipt()).contains("PRIVATE"));
    assert!(!out.receipt().full_protection_native_or_execution_authority);assert!(out.receipt().outside_selected_leaf_contents_exact&&out.receipt().output_plain_leaf_values_verified);Ok(())
}
