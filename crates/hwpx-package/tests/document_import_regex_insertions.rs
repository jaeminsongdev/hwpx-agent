use hwpx_package::{BoundedZipReader,PackageLimits,WriterLimits,WriterLimitConfig,PreservingXmlDocument,
    document_import::{ImportedSourcePackage,forms::ImportedDocumentForms,search::{SourceSearchQuery as Query,SourceSearchMode as Mode,
        SourceSearchError,selector::{SourceIndexScopeSelector as Scope,SourceIndexBoundary as Boundary},reviews::{SourceReviewTextPolicy as Policy,SourceTextRegion as Region},
        replacement::{SourceLiteralReplacementError as Compile,SourceReplacementRunPolicy as Run,atoms::regex::{SourceSelectorRegexInsertionCandidate as Candidate,
            SourceRegexInsertionPolicy as Insert,SourceRegexReplacementError as E,SOURCE_SELECTOR_REGEX_INSERTION_PROFILE,SOURCE_REGEX_INSERTION_ATOM_PROFILE}}}}};
use domain_ir::DocumentId;
use sha2::{Digest as _,Sha256};
use std::{error::Error,io::Cursor};
#[allow(dead_code)] #[path="support/review_scope_fixture.rs"] mod fixture;
#[allow(dead_code)] #[path="support/search_definition_fixture.rs"] mod definition;
#[allow(dead_code)] #[path="support/document_import_review_assembly_fixture.rs"] mod assembly;
#[allow(dead_code)] #[path="support/review_cell_output_fixture.rs"] mod table;
type TestResult=Result<(),Box<dyn Error>>;
const TAB:&str="<hp:tab width='1' leader='0' type='0'> </hp:tab>";
fn forms(raw:&[u8])->Result<ImportedDocumentForms,Box<dyn Error>> {Ok(ImportedDocumentForms::import(ImportedSourcePackage::import(raw,DocumentId::parse("regex-insertion")?,Sha256::digest(raw).into(),Default::default())?)?)}
fn query(q:&str)->Query<'_>{Query {query:q,mode:Mode::Regex,case_sensitive:true,whole_word:false,max_results:10000}}
fn all()->Policy{Policy {include_hidden_explanations:true,include_memo_bodies:true}}
fn package(text:&str)->Result<Vec<u8>,Box<dyn Error>> {fixture::with_body(&format!("<hp:p id='1'><hp:run><hp:t>{text}</hp:t></hp:run></hp:p>"))}
fn replace(f:&ImportedDocumentForms,raw:&[u8],q:&str,scope:Scope<'_>,policy:Policy,value:&str)->Result<Candidate,E> {
    f.lower_review_selector_regex_insertion_candidate(raw,query(q),scope,policy,value,Run::FirstOriginalRunRetainAllRuns,Insert::RightOriginalPointElseLeftFirstEmptyText,Default::default(),Default::default())
}
fn section(raw:&[u8])->Result<String,Box<dyn Error>> {let mut r=BoundedZipReader::open(Cursor::new(raw),PackageLimits::default())?;
    let i=r.entries().iter().position(|e|e.path.as_str()=="Contents/section0.xml").ok_or("part")?;Ok(String::from_utf8(r.read_entry(i)?)?)}
fn exact(raw:&[u8],out:&Candidate,expected:String)->TestResult {
    let bytes=out.with_verified_bytes(<[u8]>::to_vec)?;assert_eq!(section(&bytes)?,expected);
    let mut a=BoundedZipReader::open(Cursor::new(raw),Default::default())?;let mut b=BoundedZipReader::open(Cursor::new(&bytes),Default::default())?;
    assert_eq!(a.entries().len(),b.entries().len());for i in 0..a.entries().len(){let path=a.entries()[i].path.clone();if path.as_str()=="Contents/section0.xml"{continue;}
        let j=b.entries().iter().position(|e|e.path==path).ok_or("part")?;assert_eq!(a.read_entry(i)?,b.read_entry(j)?);}
    let receipt=out.receipt();assert_eq!(receipt.profile,SOURCE_SELECTOR_REGEX_INSERTION_PROFILE);assert_eq!(receipt.output.output.profile,SOURCE_REGEX_INSERTION_ATOM_PROFILE);
    assert!(receipt.exact_original_cut_verified&&receipt.output.output.original_control_bytes_preserved);
    assert!(!receipt.control_replacement_field_cache_native_or_execution_authority&&!receipt.output.zero_width_control_or_field_cache_edit_qualified&&!receipt.output.native_or_execution_authority);Ok(())
}
fn at(b:&hwpx_package::document_import::search::selector::inventory::SourceIndexBlockDescriptor,n:usize)->Boundary {Boundary {paragraph_handle:b.paragraph_handle.clone(),block_index:b.block_index,normalized_scalar:n}}

#[test]
fn insertions_endpoints_preserve_original_entities_and_escape_only_inserted_text()->TestResult {
    let raw=package("&#65;&#x1F600;&amp;Z")?;let f=forms(&raw)?;let out=replace(&f,&raw,"^|$",Scope::Document,all(),"<&")?;
    exact(&raw,&out,section(&raw)?.replace("&#65;&#x1F600;&amp;Z","&lt;&amp;&#65;&#x1F600;&amp;Z&lt;&amp;"))?;
    assert_eq!(out.receipt().zero_width_matches,2);assert_eq!(out.receipt().output.output.matched_occurrences,2);Ok(())
}
#[test]
fn insertions_empty_pattern_visits_unicode_scalar_boundaries_not_utf8_or_utf16_offsets()->TestResult {
    let raw=package("A&#x1F600;Ω")?;let f=forms(&raw)?;let out=replace(&f,&raw,"(?:)",Scope::Document,all(),"X")?;
    exact(&raw,&out,section(&raw)?.replace("A&#x1F600;Ω","XAX&#x1F600;XΩX"))?;assert_eq!(out.receipt().zero_width_matches,4);Ok(())
}
#[test]
fn insertions_run_boundary_chooses_right_original_run_and_retains_both_styles()->TestResult {
    let body="<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>A</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>B</hp:t></hp:run></hp:p>";
    let raw=definition::package(body)?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?;
    let start=at(&inv.inventory.blocks[0],1);let end=start.clone();let scope=Scope::Selection {index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end};
    let out=replace(&f,&raw,"^$",scope,all(),"X")?;exact(&raw,&out,section(&raw)?.replace("<hp:t>B</hp:t>","<hp:t>XB</hp:t>"))?;
    assert!(matches!(f.lower_review_selector_regex_candidate(&raw,query("^$"),scope,all(),"X",Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default()),Err(E::Compile(Compile::Selection))));Ok(())
}
#[test]
fn insertions_cross_run_hangul_nfc_projects_complete_cluster_cuts_to_original_scalars()->TestResult {
    let raw=fixture::with_body("<hp:p id='1'><hp:run><hp:t>Xᄀ</hp:t></hp:run><hp:run><hp:t>ᅡ</hp:t></hp:run><hp:run><hp:t>ᆨY</hp:t></hp:run></hp:p>")?;
    let f=forms(&raw)?;let out=replace(&f,&raw,"(?:)",Scope::Document,all(),"!")?;
    exact(&raw,&out,section(&raw)?.replace("Xᄀ","!X!ᄀ").replace("ᆨY","ᆨ!Y!"))?;assert_eq!(out.receipt().zero_width_matches,4);Ok(())
}
#[test]
fn insertions_reordered_nfc_interior_cut_rejects_entire_candidate_but_endpoints_are_exact()->TestResult {
    let raw=package("a&#x315;&#x300;")?;let f=forms(&raw)?;
    assert!(matches!(replace(&f,&raw,"(?:)",Scope::Document,all(),"X"),Err(E::Compile(Compile::Selection))));
    let out=replace(&f,&raw,"^|$",Scope::Document,all(),"X")?;exact(&raw,&out,section(&raw)?.replace("a&#x315;&#x300;","Xa&#x315;&#x300;X"))?;Ok(())
}
#[test]
fn insertions_cannot_split_two_normalized_contributions_of_one_original_scalar()->TestResult {
    let raw=package("&#x344;")?;let f=forms(&raw)?;
    assert!(matches!(replace(&f,&raw,"(?:)",Scope::Document,all(),"X"),Err(E::Compile(Compile::Selection))));
    exact(&raw,&replace(&f,&raw,"^|$",Scope::Document,all(),"X")?,section(&raw)?.replace("&#x344;","X&#x344;X"))?;Ok(())
}
#[test]
fn insertions_control_only_span_creates_text_in_empty_slots_without_editing_controls()->TestResult {
    let old=format!("{TAB}<hp:lineBreak> </hp:lineBreak>");let raw=package(&old)?;let f=forms(&raw)?;let out=replace(&f,&raw,"(?:)",Scope::Document,all(),"X")?;
    exact(&raw,&out,section(&raw)?.replace(&old,&format!("X{TAB}X<hp:lineBreak> </hp:lineBreak>X")))?;
    assert_eq!(out.receipt().zero_width_matches,3);assert_eq!(out.receipt().output.output.changes[0].changed_original_text_atoms,0);Ok(())
}
#[test]
fn insertions_leading_trailing_and_interleaved_controls_keep_every_original_control_byte()->TestResult {
    let old=format!("{TAB}A&amp;<hp:lineBreak/>B{TAB}");let raw=package(&old)?;let f=forms(&raw)?;let out=replace(&f,&raw,"(?:)",Scope::Document,all(),"X")?;
    let expected=format!("X{TAB}XAX&amp;X<hp:lineBreak/>XBX{TAB}X");exact(&raw,&out,section(&raw)?.replace(&old,&expected))?;
    assert_eq!(out.receipt().zero_width_matches,7);assert_eq!(out.receipt().output.output.changes[0].preserved_controls,3);Ok(())
}
#[test]
fn insertions_empty_original_paired_and_self_closing_text_choose_first_admitted_text()->TestResult {
    for first in["<hp:t></hp:t>","<hp:t xmlns:k='urn:keep' />"] {
        let body=format!("<hp:p id='1'><hp:run>{first}<hp:t/></hp:run><hp:run><hp:t/></hp:run></hp:p>");let raw=fixture::with_body(&body)?;let f=forms(&raw)?;
        let out=replace(&f,&raw,"^$",Scope::Document,all(),"<&")?;
        let new=if first.contains("xmlns"){"<hp:t xmlns:k='urn:keep' >&lt;&amp;</hp:t>"}else{"<hp:t>&lt;&amp;</hp:t>"};
        exact(&raw,&out,section(&raw)?.replacen(first,new,1))?;assert_eq!(out.receipt().zero_width_matches,1);
    }Ok(())
}
#[test]
fn insertions_no_original_text_owner_and_opaque_text_do_not_get_invented_runs()->TestResult {
    for body in["<hp:p id='1'><hp:run/></hp:p>","<hp:p id='1'><hp:run><hp:t><!--opaque--></hp:t></hp:run></hp:p>"] {
        let raw=fixture::with_body(body)?;let f=forms(&raw)?;assert!(matches!(replace(&f,&raw,"^$",Scope::Document,all(),"X"),Err(E::Compile(Compile::Selection))));
    }Ok(())
}
#[test]
fn insertions_all_four_selectors_keep_clipped_coordinates_and_unselected_source_exact()->TestResult {
    let raw=fixture::with_body("<hp:p id='1'><hp:run><hp:t>AB</hp:t></hp:run></hp:p><hp:p id='2'><hp:run><hp:t>CD</hp:t></hp:run></hp:p>")?;
    let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?;let b=&inv.inventory.blocks[1];
    let node=inv.inventory.nodes.iter().find(|n|n.source_handle==b.paragraph_handle).ok_or("node")?;let ids=[node.node_id.clone()];let start=at(b,1);let end=start.clone();
    for(scope,count,kind)in[(Scope::Document,2,0),(Scope::Section(&inv.inventory.section_ids),2,0),(Scope::NodeSet(&ids),1,1),
        (Scope::Selection {index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},1,2)] {
        let out=replace(&f,&raw,"^",scope,all(),"X")?;let mut expected=section(&raw)?;
        if kind==0{expected=expected.replace(">AB<",">XAB<").replace(">CD<",">XCD<");}else if kind==1{expected=expected.replace(">CD<",">XCD<");}else{expected=expected.replace(">CD<",">CXD<");}
        exact(&raw,&out,expected)?;assert_eq!(out.receipt().zero_width_matches,count);
    }Ok(())
}
#[test]
fn insertions_review_policies_filter_before_matches_and_never_write_memo_cache()->TestResult {
    let raw=fixture::package()?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?;
    let ids:Vec<_>=inv.block_regions.iter().enumerate().filter(|(_,r)|**r!=Region::BodyAndNotes).map(|(i,_)| {
        let b=&inv.inventory.blocks[i];inv.inventory.nodes.iter().find(|n|n.source_handle==b.paragraph_handle).map(|n|n.node_id.clone()).ok_or("node")
    }).collect::<Result<_,_>>()?;
    for(h,m,count)in[(false,false,0),(true,false,1),(false,true,1),(true,true,2)] {
        let policy=Policy {include_hidden_explanations:h,include_memo_bodies:m};let out=replace(&f,&raw,"^",Scope::NodeSet(&ids),policy,"X");
        if count==0{assert!(matches!(out,Err(E::Compile(Compile::NoMatches))));continue;}
        let out=out?;let mut expected=section(&raw)?;if h{expected=expected.replace("HIDDEN K K","XHIDDEN K K");}if m{expected=expected.replace("MEMO K K","XMEMO K K");}
        exact(&raw,&out,expected)?;assert_eq!(out.receipt().zero_width_matches,count);
    }
    assert!(matches!(replace(&f,&raw,"^",Scope::Document,all(),"X"),Err(E::Compile(Compile::FieldContent))));Ok(())
}
#[test]
fn insertions_table_lock_cell_and_ancestor_protection_still_precede_writes()->TestResult {
    let body=table::table(300);for(blocked,body)in[(false,body.clone()),(true,body.replace("lock='0'","lock='1'")),(true,body.replacen("protect='0'","protect='1'",1))] {
        let raw=assembly::package(&body)?;let f=forms(&raw)?;let out=replace(&f,&raw,"^",Scope::Document,all(),"X");
        if blocked{assert!(matches!(out,Err(E::Compile(Compile::Protection))));}else{let out=out?;assert!(out.receipt().zero_width_matches>0);}
    }Ok(())
}
#[test]
fn insertions_mixed_nonempty_and_empty_matches_share_one_original_transaction_and_template_pass()->TestResult {
    let raw=package("AA Z")?;let f=forms(&raw)?;let out=replace(&f,&raw,"A|$",Scope::Document,all(),"[${0}]")?;
    exact(&raw,&out,section(&raw)?.replace("AA Z","[A][A] Z[]"))?;assert_eq!(out.receipt().zero_width_matches,1);assert_eq!(out.receipt().output.output.matched_occurrences,3);
    let raw=package("AB")?;let f=forms(&raw)?;let out=replace(&f,&raw,"^|B",Scope::Document,all(),"[${0}]")?;
    exact(&raw,&out,section(&raw)?.replace(">AB<",">[]A[B]<"))?;Ok(())
}
#[test]
fn insertions_empty_replacement_noop_match_and_patch_budgets_do_not_return_partial_success()->TestResult {
    let raw=package("AB")?;let f=forms(&raw)?;
    assert!(matches!(replace(&f,&raw,"(?:)",Scope::Document,all(),""),Err(E::Compile(Compile::NoChange))));
    assert!(matches!(f.lower_review_selector_regex_insertion_candidate(&raw,Query {max_results:1,..query("(?:)")},Scope::Document,all(),"X",Run::FirstOriginalRunRetainAllRuns,
        Insert::RightOriginalPointElseLeftFirstEmptyText,Default::default(),Default::default()),Err(E::Search(SourceSearchError::Limit))));
    let raw=package(&"A".repeat(4096))?;let f=forms(&raw)?;assert!(matches!(replace(&f,&raw,"(?:)",Scope::Document,all(),"X"),Err(E::Compile(Compile::Limit))));Ok(())
}
#[test]
fn insertions_original_proof_writer_scope_and_privacy_boundaries_are_not_authority()->TestResult {
    let raw=package("PRIVATE-SOURCE")?;let f=forms(&raw)?;let other=forms(&raw)?;let proof=f.reconstruct_source_for_verification(&raw)?;
    assert!(matches!(proof.lower_review_selector_regex_insertion_candidate(&other,query("^"),Scope::Document,all(),"PRIVATE-VALUE",Run::FirstOriginalRunRetainAllRuns,
        Insert::RightOriginalPointElseLeftFirstEmptyText,Default::default(),Default::default()),Err(E::Source)));
    assert!(f.lower_review_selector_regex_insertion_candidate(&raw,query("^"),Scope::Document,all(),"X",Run::FirstOriginalRunRetainAllRuns,
        Insert::RightOriginalPointElseLeftFirstEmptyText,Default::default(),WriterLimits::new(WriterLimitConfig {max_output_bytes:1})?).is_err());
    let out=replace(&f,&raw,"^",Scope::Document,all(),"PRIVATE-VALUE")?;assert!(!format!("{out:?}{:?}{}",out.receipt(),serde_json::to_string(out.receipt())?).contains("PRIVATE"));Ok(())
}
#[test]
fn insertions_many_control_boundaries_share_one_protection_map_and_keep_old_v1_rejection()->TestResult {
    let old=TAB.repeat(1000);let raw=package(&old)?;let f=forms(&raw)?;let out=replace(&f,&raw,"(?:)",Scope::Document,all(),"X")?;
    exact(&raw,&out,section(&raw)?.replace(&old,&format!("X{}",format!("{TAB}X").repeat(1000))))?;
    let receipt=out.receipt();let xml=PreservingXmlDocument::parse(section(&raw)?.as_bytes())?;
    assert_eq!(receipt.zero_width_matches,1001);assert_eq!(receipt.output.output.observed_protection_parts,1);
    assert_eq!(receipt.output.output.observed_protection_element_visits,2*xml.elements().len());
    assert!(matches!(f.lower_review_selector_regex_candidate(&raw,query("(?:)"),Scope::Document,all(),"X",Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default()),Err(E::Compile(Compile::Selection))));Ok(())
}
#[test]
fn insertions_control_boundary_patch_rejects_noncontrol_duplicate_unsorted_and_out_of_range_coordinates()->TestResult {
    use hwpx_package::{PackageGraph,PatchIntent,TextAtomRangeReplacement as Range,XmlElementSelector,PreservingPatchEngine,
        IdRuleProfile,PreservationRuleProfile,PatchLimits,PatchLimitConfig};
    let raw=package(&format!("{TAB}A<hp:lineBreak/>"))?;let mut reader=BoundedZipReader::open(Cursor::new(&raw),Default::default())?;
    let graph=PackageGraph::build(&mut reader,Default::default())?;let i=reader.entries().iter().position(|e|e.path.as_str()=="Contents/section0.xml").ok_or("part")?;
    let path=reader.entries()[i].path.clone();let xml=PreservingXmlDocument::parse(&reader.read_entry(i)?)?;
    let element=xml.elements().iter().position(|e|e.name().local_name()=="t").ok_or("text")?;
    let target=XmlElementSelector::bind(&path,&xml,element)?;
    for ordinals in[vec![1],vec![4],vec![0,0],vec![3,0]] {
        let ranges=ordinals.into_iter().map(|a|Range::at_control_boundary(a,"X")).collect::<Result<Vec<_>,_>>()?;
        let intent=PatchIntent::ReplaceTextAtomScalarRanges {target:target.clone(),ranges};
        assert!(PreservingPatchEngine::apply_with_limits_and_preservation_profile(&mut reader,&graph,Default::default(),IdRuleProfile::hwpml_2011_shape_v6(),
            Default::default(),Default::default(),PreservationRuleProfile::Hangul2020PreviewTextV2,&[intent]).is_err());
    }
    let intent=PatchIntent::ReplaceTextAtomScalarRanges {target,ranges:vec![Range::at_control_boundary(0,"&")?,Range::at_control_boundary(3,"&")?]};
    for limits in[PatchLimits::new(PatchLimitConfig {max_intents:1,..Default::default()})?,PatchLimits::new(PatchLimitConfig {max_total_output_growth:9,..Default::default()})?] {
        assert!(PreservingPatchEngine::apply_with_limits_and_preservation_profile(&mut reader,&graph,Default::default(),IdRuleProfile::hwpml_2011_shape_v6(),
            Default::default(),limits,PreservationRuleProfile::Hangul2020PreviewTextV2,&[intent.clone()]).is_err());
    }
    for value in["\t","\n","\r","\u{0}"] {assert!(Range::at_control_boundary(0,value).is_err());}Ok(())
}
#[test]
fn insertions_empty_query_remains_rejected_separately_from_a_regex_that_matches_empty()->TestResult {
    let raw=package("AB")?;let f=forms(&raw)?;
    assert!(matches!(replace(&f,&raw,"",Scope::Document,all(),"X"),Err(E::Search(SourceSearchError::Limit))));
    let out=replace(&f,&raw,"(?:)",Scope::Document,all(),"X")?;exact(&raw,&out,section(&raw)?.replace(">AB<",">XAXBX<"))?;Ok(())
}
