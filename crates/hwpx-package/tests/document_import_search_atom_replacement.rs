use hwpx_package::{WriterLimits,WriterLimitConfig,BoundedZipReader,PackageLimits,PreservingXmlDocument,
    document_import::{ImportedSourcePackage,SourceImportLimits,forms::ImportedDocumentForms,
        search::{SourceSearchQuery as Query,SourceSearchMode as Mode,SourceSearchLimits,SourceSearchLimitConfig as Config,
            scope::SourceSearchScope as Scope,replacement::{SourceLiteralReplacementError as E,SourceReplacementRunPolicy as Policy,
                atoms::{SourceLiteralTextAtomCandidate,SOURCE_LITERAL_TEXT_ATOM_PROFILE}}}}};
use domain_ir::{DocumentId,LogicalId};
use sha2::{Digest as _,Sha256};
use std::{error::Error,io::Cursor};
#[allow(dead_code)] #[path="support/search_definition_fixture.rs"] mod fixture;
#[allow(dead_code)] #[path="support/document_import_review_assembly_fixture.rs"] mod assembly;
#[allow(dead_code)] #[path="support/review_cell_output_fixture.rs"] mod table;
type TestResult=Result<(),Box<dyn Error>>;
const TAB:&str="<hp:tab width='8000' leader='0' type='0'/>";
fn package(text:&str)->Result<Vec<u8>,Box<dyn Error>> {fixture::package(&format!("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>{text}</hp:t></hp:run></hp:p>"))}
fn forms(b:&[u8],id:&str)->Result<ImportedDocumentForms,Box<dyn Error>> {Ok(ImportedDocumentForms::import(ImportedSourcePackage::import(b,
    DocumentId::parse(id)?,Sha256::digest(b).into(),SourceImportLimits::default())?)?)}
fn query(q:&str)->Query<'_> {Query {query:q,mode:Mode::Literal,case_sensitive:true,whole_word:false,max_results:10000}}
fn replace(f:&ImportedDocumentForms,b:&[u8],q:&str,value:&str)->Result<SourceLiteralTextAtomCandidate,E> {
    f.lower_literal_text_atom_candidate(b,query(q),Scope::MappedDocument,value,Policy::FirstOriginalRunRetainAllRuns,Default::default(),Default::default())
}
fn section(b:&[u8])->Result<String,Box<dyn Error>> {let mut r=BoundedZipReader::open(Cursor::new(b),PackageLimits::default())?;
    let i=r.entries().iter().position(|p|p.path.as_str()=="Contents/section0.xml").ok_or("section")?;Ok(String::from_utf8(r.read_entry(i)?)?)}
fn only_rewrite(b:&[u8],candidate:&SourceLiteralTextAtomCandidate,old:&str,new:&str)->TestResult {
    let output=candidate.with_verified_bytes(<[u8]>::to_vec)?;assert_eq!(section(&output)?,section(b)?.replacen(old,new,1));
    let mut before=BoundedZipReader::open(Cursor::new(b),PackageLimits::default())?;
    let mut after=BoundedZipReader::open(Cursor::new(&output),PackageLimits::default())?;
    for i in 0..before.entries().len() {
        let path=&before.entries()[i].path;if path.as_str()=="Contents/section0.xml"{continue;}
        let j=after.entries().iter().position(|p|&p.path==path).ok_or("other part")?;
        assert_eq!(before.read_entry(i)?,after.read_entry(j)?);
    }Ok(())
}
#[test]
fn atom_literal_multiple_matches_before_between_after_controls_preserve_source_bytes_and_receipt()->TestResult {
    let old=format!("K&#38;U{TAB}K&#x1F600;<hp:lineBreak> </hp:lineBreak>K&#x26;TAIL");
    let b=package(&old)?;let f=forms(&b,"mixed")?;let out=replace(&f,&b,"K","X<&")?;
    only_rewrite(&b,&out,&old,&old.replace('K',"X&lt;&amp;"))?;
    let r=out.receipt();assert_eq!(r.profile,SOURCE_LITERAL_TEXT_ATOM_PROFILE);assert_eq!(r.matched_occurrences,3);
    assert_eq!(r.changed_scalar_ranges,3);assert_eq!(r.changes.len(),1);assert_eq!(r.changes[0].changed_original_text_atoms,3);assert_eq!(r.changes[0].preserved_controls,2);
    assert!(r.original_control_bytes_preserved&&r.output_text_span_values_verified&&r.outside_selected_text_atoms_exact);
    assert!(!r.control_atom_replacement_qualified&&!r.field_cached_content_edit_qualified&&!r.full_protection_native_or_execution_authority);Ok(())
}
#[test]
fn atom_literal_complete_deletions_rebase_atom_indices_without_losing_adjacent_or_paired_controls()->TestResult {
    let old=format!("{TAB}K<hp:lineBreak/>K{TAB}<hp:lineBreak> </hp:lineBreak>K");
    let b=package(&old)?;let f=forms(&b,"delete")?;let out=replace(&f,&b,"K","")?;
    only_rewrite(&b,&out,&old,&old.replace('K',""))?;
    assert_eq!(out.receipt().changes[0].changed_original_text_atoms,3);assert_eq!(out.receipt().changes[0].preserved_controls,4);
    assert_eq!(out.receipt().changes[0].output_text_bytes,0);Ok(())
}
#[test]
fn atom_literal_cross_run_match_retains_original_runs_styles_and_control_layout()->TestResult {
    let body=format!("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>{TAB}A</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>B<hp:lineBreak/>TAIL</hp:t></hp:run></hp:p>");
    let b=fixture::package(&body)?;let f=forms(&b,"runs")?;let out=replace(&f,&b,"AB","Z")?;
    only_rewrite(&b,&out,&body,&body.replace("/>A</hp:t>","/>Z</hp:t>").replace("<hp:t>B<hp:lineBreak/>","<hp:t><hp:lineBreak/>"))?;
    assert_eq!(out.receipt().changes.len(),2);assert_eq!(out.receipt().changed_scalar_ranges,2);Ok(())
}
#[test]
fn atom_literal_hangul_nfc_match_across_three_runs_uses_first_original_run_policy()->TestResult {
    let body=format!("<hp:p id='1'><hp:run><hp:t>{TAB}ᄀ</hp:t></hp:run><hp:run><hp:t>ᅡ</hp:t></hp:run><hp:run><hp:t>ᆨ<hp:lineBreak/></hp:t></hp:run></hp:p>");
    let b=fixture::package(&body)?;let f=forms(&b,"jamo")?;let out=replace(&f,&b,"각","한")?;
    only_rewrite(&b,&out,&body,&body.replace('ᄀ',"한").replace(['ᅡ','ᆨ'],""))?;
    assert_eq!(out.receipt().matched_occurrences,1);assert_eq!(out.receipt().changed_scalar_ranges,3);assert!(out.receipt().original_selection_contiguity_verified);Ok(())
}
#[test]
fn atom_literal_nfc_reorder_partial_expansion_and_control_crossing_reject_without_partial_output()->TestResult {
    let old=format!("{TAB}a&#x315;&#x300;<hp:lineBreak/>K");let b=package(&old)?;let f=forms(&b,"nfc")?;
    assert!(matches!(replace(&f,&b,"à","X"),Err(E::Selection)));
    only_rewrite(&b,&replace(&f,&b,"à\u{315}","X")?,&old,&format!("{TAB}X<hp:lineBreak/>K"))?;
    let b=package(&format!("{TAB}&#x344;<hp:lineBreak/>K"))?;let f=forms(&b,"expansion")?;
    assert!(matches!(replace(&f,&b,"\u{308}","X"),Err(E::Selection)));
    let b=package(&format!("A{TAB}B<hp:lineBreak/>C"))?;let f=forms(&b,"control")?;
    for q in ["\t","\n","A\tB","B\nC"] {assert!(matches!(replace(&f,&b,q,"X"),Err(E::Selection)));}Ok(())
}
#[test]
fn atom_literal_scoped_casefold_whole_word_keeps_unselected_mixed_paragraph_exact()->TestResult {
    let body=format!("<hp:p id='1'><hp:run><hp:t>Cat scatter{TAB}CAT</hp:t></hp:run></hp:p><hp:p id='2'><hp:run><hp:t>cat<hp:lineBreak/>cat</hp:t></hp:run></hp:p>");
    let b=fixture::package(&body)?;let f=forms(&b,"scope")?;let index=f.body_structure().source_text_index(&b,Default::default())?;
    let found=index.find(query("Cat"))?;let id=found.matches()[0].paragraph_anchor.opaque_handle.clone();
    let q=Query {case_sensitive:false,whole_word:true,..query("cat")};let out=f.lower_literal_text_atom_candidate(&b,q,Scope::Paragraphs(&[id]),"DOG",Policy::FirstOriginalRunRetainAllRuns,Default::default(),Default::default())?;
    only_rewrite(&b,&out,&body,&body.replace("Cat scatter","DOG scatter").replace("/>CAT</hp:t>","/>DOG</hp:t>"))?;
    assert_eq!(out.receipt().matched_occurrences,2);
    assert!(f.lower_literal_text_atom_candidate(&b,q,Scope::Paragraphs(&[LogicalId::parse("foreign")?]),"X",Policy::FirstOriginalRunRetainAllRuns,Default::default(),Default::default()).is_err());Ok(())
}
#[test]
fn atom_literal_field_caches_remain_unqualified_even_for_editable_fields_and_mixed_all_match_batches()->TestResult {
    for editable in ["0","1"] {
        let body=format!("<hp:p id='1'><hp:run><hp:t>OUTK{TAB}TAIL</hp:t><hp:ctrl><hp:fieldBegin id='17' type='MEMO' editable='{editable}'/></hp:ctrl><hp:t>CACHEK<hp:lineBreak/>TAIL</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='17'/></hp:ctrl></hp:run></hp:p>");
        let b=fixture::package(&body)?;let f=forms(&b,"cache")?;
        for q in ["CACHEK","K"] {assert!(matches!(replace(&f,&b,q,"X"),Err(E::FieldContent)));}
        assert!(replace(&f,&b,"OUTK","X").is_ok());assert_eq!(section(&b)?.matches("CACHEK").count(),1);
    }Ok(())
}
#[test]
fn atom_literal_observed_table_cell_size_and_ancestor_protection_apply_before_editing()->TestResult {
    let body=table::table(300).replace("CELL-OLD",&format!("{TAB}CELL-OLD<hp:lineBreak/>"));
    let b=assembly::package(&body)?;let f=forms(&b,"table")?;assert!(replace(&f,&b,"CELL-OLD","NEW")?.with_verified_bytes(section)??.contains("NEW<hp:lineBreak/>"));
    for protected in [body.replace("lock='0'","lock='1'"),body.replacen("protect='0'","protect='1'",1),body.replace("hasMargin='0' protect='0'","hasMargin='0' protect='1'")] {
        let b=assembly::package(&protected)?;let f=forms(&b,"protected")?;assert!(matches!(replace(&f,&b,"CELL-OLD","NEW"),Err(E::Protection)));
    }Ok(())
}
#[test]
fn atom_literal_same_value_matches_do_not_rewrite_original_entities_or_unchanged_atom_slots()->TestResult {
    let old=format!("&#75;{TAB}k<hp:lineBreak/>TAIL");let b=package(&old)?;let f=forms(&b,"noop")?;
    assert!(matches!(replace(&f,&b,"K","K"),Err(E::NoChange)));
    let q=Query {case_sensitive:false,..query("K")};let out=f.lower_literal_text_atom_candidate(&b,q,Scope::MappedDocument,"K",Policy::FirstOriginalRunRetainAllRuns,Default::default(),Default::default())?;
    only_rewrite(&b,&out,&old,&old.replace("/>k<","/>K<"))?;
    assert_eq!(out.receipt().matched_occurrences,2);assert_eq!(out.receipt().changed_scalar_ranges,1);assert_eq!(out.receipt().changes[0].changed_original_text_atoms,1);Ok(())
}
#[test]
fn atom_literal_original_proof_stale_source_regex_bad_values_and_old_v1_boundary_are_retained()->TestResult {
    let b=package(&format!("K{TAB}TAIL"))?;let f=forms(&b,"proof")?;let other=forms(&b,"proof")?;
    let proof=f.reconstruct_source_for_verification(&b)?;
    assert!(matches!(proof.lower_literal_text_atom_candidate(&other,query("K"),Scope::MappedDocument,"X",Policy::FirstOriginalRunRetainAllRuns,Default::default(),Default::default()),Err(E::Source)));
    let changed=package(&format!("CHANGED{TAB}TAIL"))?;assert!(matches!(replace(&f,&changed,"K","X"),Err(E::Source)));
    assert!(matches!(f.lower_literal_text_atom_candidate(&b,Query {mode:Mode::Regex,..query("K")},Scope::MappedDocument,"X",Policy::FirstOriginalRunRetainAllRuns,Default::default(),Default::default()),Err(E::Value)));
    for value in ["\t","\n","\r","\u{0000}","\u{1fffe}"] {assert!(matches!(replace(&f,&b,"K",value),Err(E::Value)));}
    assert!(matches!(replace(&f,&b,"missing","X"),Err(E::NoMatches)));
    assert!(matches!(f.lower_literal_search_candidate(&b,query("K"),Scope::MappedDocument,"X",Policy::FirstOriginalRunRetainAllRuns,Default::default(),Default::default()),Err(E::Selection)));
    assert!(replace(&f,&b,"K","X").is_ok());Ok(())
}
#[test]
fn atom_literal_match_range_response_and_writer_caps_never_return_partial_success_or_private_receipts()->TestResult {
    let b=package(&format!("K{TAB}K"))?;let f=forms(&b,"limits")?;
    assert!(f.lower_literal_text_atom_candidate(&b,Query {max_results:1,..query("K")},Scope::MappedDocument,"X",Policy::FirstOriginalRunRetainAllRuns,Default::default(),Default::default()).is_err());
    assert!(f.lower_literal_text_atom_candidate(&b,query("K"),Scope::MappedDocument,"X",Policy::FirstOriginalRunRetainAllRuns,
        SourceSearchLimits::new(Config {result_bytes:1,..Default::default()})?,Default::default()).is_err());
    assert!(f.lower_literal_text_atom_candidate(&b,query("K"),Scope::MappedDocument,"X",Policy::FirstOriginalRunRetainAllRuns,Default::default(),WriterLimits::new(WriterLimitConfig {max_output_bytes:1})?).is_err());
    let out=replace(&f,&b,"K","PRIVATE-REPLACEMENT")?;assert!(!serde_json::to_string(out.receipt())?.contains("PRIVATE"));assert!(!format!("{out:?}{:?}",out.receipt()).contains("PRIVATE"));
    let b=package(&format!("{TAB}{}","K".repeat(4097)))?;let f=forms(&b,"ranges")?;assert!(matches!(replace(&f,&b,"K","X"),Err(E::Limit)));Ok(())
}
#[test]
fn atom_literal_many_matches_share_one_protection_map_and_original_coordinate_batch()->TestResult {
    let old=format!("{TAB}{}<hp:lineBreak/>{}","K&amp;".repeat(100),"K&#x26;".repeat(100));
    let b=package(&old)?;let f=forms(&b,"many")?;let out=replace(&f,&b,"K","X")?;
    only_rewrite(&b,&out,&old,&old.replace('K',"X"))?;
    let xml=PreservingXmlDocument::parse(section(&b)?.as_bytes())?;
    assert_eq!(out.receipt().observed_protection_element_visits,xml.elements().len()*2);assert_eq!(out.receipt().observed_protection_parts,1);
    assert_eq!(out.receipt().matched_occurrences,200);assert_eq!(out.receipt().changed_scalar_ranges,200);assert_eq!(out.receipt().changes.len(),1);
    assert_eq!(out.receipt().changes[0].changed_original_text_atoms,2);Ok(())
}
