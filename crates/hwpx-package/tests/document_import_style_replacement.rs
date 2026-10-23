use hwpx_package::{BoundedZipReader,PackageLimits,PreservingXmlDocument,XmlTokenKind,WriterLimits,WriterLimitConfig,
    document_import::{ImportedSourcePackage,forms::ImportedDocumentForms,search::{SourceSearchQuery as Query,SourceSearchMode as Mode,SourceSearchError as Search,
        SourceSearchLimits,SourceSearchLimitConfig as Config,selector::{SourceIndexScopeSelector as Scope,SourceIndexBoundary as Boundary},
        reviews::{SourceReviewTextPolicy as Policy,SourceTextRegion as Region,selector::styles::SourceReviewStyleFilter as Filter},
        inspection::{SourceDeclaredStyleFilter as Declared,definitions::{SourceDefinitionStyleFilter as Definition,CharacterDefinitionSource as Axis}},
        replacement::{SourceLiteralReplacementError as Compile,atoms::styles::{SourceStyleReplacementCandidate as Candidate,SourceStyleReplacementError as E}}}}};
use domain_ir::DocumentId;
use sha2::{Digest as _,Sha256};
use std::{error::Error,io::Cursor};
#[allow(dead_code)] #[path="support/search_definition_fixture.rs"] mod fixture;
#[allow(dead_code)] #[path="support/review_scope_fixture.rs"] mod review;
#[allow(dead_code)] #[path="support/document_import_review_assembly_fixture.rs"] mod assembly;
#[allow(dead_code)] #[path="support/review_cell_output_fixture.rs"] mod table;
#[allow(dead_code)] #[path="support/document_import_catalog_fixture.rs"] mod archive;
type TestResult=Result<(),Box<dyn Error>>;
const TAB:&str="<hp:tab width='1' leader='0' type='0'> </hp:tab>";
fn forms(raw:&[u8])->Result<ImportedDocumentForms,Box<dyn Error>> {Ok(ImportedDocumentForms::import(ImportedSourcePackage::import(raw,DocumentId::parse("style-replacement")?,Sha256::digest(raw).into(),Default::default())?)?)}
fn plain(text:&str)->Result<Vec<u8>,Box<dyn Error>> {fixture::package(&format!("<hp:p id='1' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'><hp:t>{text}</hp:t></hp:run></hp:p>"))}
fn query(q:&str)->Query<'_>{Query {query:q,mode:Mode::Literal,case_sensitive:true,whole_word:false,max_results:10000}}
fn all()->Policy{Policy {include_hidden_explanations:true,include_memo_bodies:true}}
fn declared()->Filter{Filter::Declared(Declared {run_character_property:Some(0),..Default::default()})}
fn replace(f:&ImportedDocumentForms,raw:&[u8],q:&str,scope:Scope<'_>,policy:Policy)->Result<Candidate,E>{
    f.lower_review_selector_style_candidate(raw,query(q),scope,policy,declared(),1,Default::default(),Default::default())}
fn section(raw:&[u8])->Result<String,Box<dyn Error>> {let mut r=BoundedZipReader::open(Cursor::new(raw),PackageLimits::default())?;
    let i=r.entries().iter().position(|e|e.path.as_str()=="Contents/section0.xml").ok_or("part")?;Ok(String::from_utf8(r.read_entry(i)?)?)}
fn values(raw:&[u8])->Result<Vec<(char,Option<u32>)>,Box<dyn Error>> {
    let raw=section(raw)?;let xml=PreservingXmlDocument::parse(raw.as_bytes())?;let mut values=Vec::new();
    for token in xml.tokens().iter().filter(|t|matches!(t.kind(),XmlTokenKind::Text|XmlTokenKind::Whitespace|XmlTokenKind::Reference)) {
        let Some(t)=token.element_index().and_then(|i|xml.elements().get(i))else{continue};if t.name().local_name()!="t"{continue;}
        let run=&xml.elements()[t.parent().ok_or("run")?];let style=run.attributes().iter().find(|a|a.name().local_name()=="charPrIDRef").map(|a|raw[a.value_span().start()..a.value_span().end()].parse::<u32>()).transpose()?;
        let span=token.span();let decoded=quick_xml::escape::unescape(&raw[span.start()..span.end()])?;
        values.extend(decoded.chars().map(|c|(c,style)));
    }Ok(values)
}
fn output(raw:&[u8],candidate:&Candidate)->Result<Vec<u8>,Box<dyn Error>> {
    let bytes=candidate.with_verified_bytes(<[u8]>::to_vec)?;let mut a=BoundedZipReader::open(Cursor::new(raw),Default::default())?;
    let mut b=BoundedZipReader::open(Cursor::new(&bytes),Default::default())?;assert_eq!(a.entries().len(),b.entries().len());
    for i in 0..a.entries().len(){let path=a.entries()[i].path.clone();if path.as_str()=="Contents/section0.xml"{continue;}
        let j=b.entries().iter().position(|e|e.path==path).ok_or("part")?;assert_eq!(a.read_entry(i)?,b.read_entry(j)?);}
    let r=candidate.receipt();assert!(r.all_original_scalars_and_control_values_preserved&&r.every_original_scalar_style_read_back&&r.outside_original_run_edits_exact&&r.original_run_boundaries_not_merged);
    assert!(!r.paragraph_named_text_style_effective_visibility_or_execution_qualified&&!r.full_protection_native_or_service_authority);Ok(bytes)
}
#[test]
fn style_replacement_partial_run_keeps_unselected_scalar_styles_and_original_entities()->TestResult {
    let raw=plain("A&#x1F600;B&amp;C")?;let f=forms(&raw)?;let out=replace(&f,&raw,"😀B",Scope::Document,all())?;let bytes=output(&raw,&out)?;
    assert_eq!(values(&bytes)?,vec![('A',Some(0)),('😀',Some(1)),('B',Some(1)),('&',Some(0)),('C',Some(0))]);
    assert!(section(&bytes)?.contains("&#x1F600;B")&&section(&bytes)?.contains("&amp;C"));assert_eq!(out.receipt().original_changed_runs,1);assert_eq!(out.receipt().generated_run_fragments,3);Ok(())
}
#[test]
fn style_replacement_adjacent_and_many_matches_are_one_original_coordinate_batch()->TestResult {
    let raw=plain("ABAB AB")?;let f=forms(&raw)?;let out=replace(&f,&raw,"AB",Scope::Document,all())?;let bytes=output(&raw,&out)?;
    assert_eq!(values(&bytes)?.iter().map(|(_,s)|*s).collect::<Vec<_>>(),vec![Some(1),Some(1),Some(1),Some(1),Some(0),Some(1),Some(1)]);
    assert_eq!(out.receipt().matched_occurrences,3);assert_eq!(out.receipt().original_changed_runs,1);Ok(())
}
#[test]
fn style_replacement_cross_original_runs_and_hangul_nfc_keep_original_spelling_and_boundaries()->TestResult {
    let raw=fixture::package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>Xᄀ</hp:t></hp:run><hp:run charPrIDRef='0'><hp:t>ᅡ</hp:t></hp:run><hp:run charPrIDRef='0'><hp:t>ᆨY</hp:t></hp:run></hp:p>")?;
    let f=forms(&raw)?;let out=replace(&f,&raw,"각",Scope::Document,all())?;let bytes=output(&raw,&out)?;
    assert_eq!(values(&bytes)?,vec![('X',Some(0)),('ᄀ',Some(1)),('ᅡ',Some(1)),('ᆨ',Some(1)),('Y',Some(0))]);
    assert_eq!(out.receipt().original_changed_runs,3);assert_eq!(out.receipt().generated_run_fragments,5);Ok(())
}
#[test]
fn style_replacement_controls_keep_exact_bytes_and_original_style_context()->TestResult {
    let old=format!("A{TAB}BC<hp:lineBreak> </hp:lineBreak>D");let raw=plain(&old)?;let f=forms(&raw)?;let out=replace(&f,&raw,"B",Scope::Document,all())?;let bytes=output(&raw,&out)?;
    assert!(section(&bytes)?.contains(TAB)&&section(&bytes)?.contains("<hp:lineBreak> </hp:lineBreak>"));
    assert_eq!(values(&bytes)?,vec![('A',Some(0)),('B',Some(1)),('C',Some(0)),('D',Some(0))]);
    assert!(matches!(replace(&f,&raw,"\t",Scope::Document,all()),Err(E::Compile(Compile::Selection))));Ok(())
}
#[test]
fn style_replacement_declared_and_definition_predicates_use_the_original_typed_header()->TestResult {
    let raw=plain("A A")?;let f=forms(&raw)?;let filter=Filter::Definition(Definition {character_source:Some(Axis::RunProperty),bold:Some(false),..Default::default()});
    let out=f.lower_review_selector_style_candidate(&raw,query("A"),Scope::Document,all(),filter,1,Default::default(),Default::default())?;
    assert_eq!(values(&output(&raw,&out)?)?,vec![('A',Some(1)),(' ',Some(0)),('A',Some(1))]);
    assert!(matches!(f.lower_review_selector_style_candidate(&raw,query("absent"),Scope::Document,all(),declared(),u32::MAX,Default::default(),Default::default()),Err(E::Search(Search::Definition))));Ok(())
}
#[test]
fn style_replacement_all_four_selector_scopes_clip_regex_before_style_matching()->TestResult {
    let raw=fixture::package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>A B</hp:t></hp:run></hp:p><hp:p id='2'><hp:run charPrIDRef='0'><hp:t>B C</hp:t></hp:run></hp:p>")?;
    let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?;let block=&inv.inventory.blocks[0];
    let start=Boundary {paragraph_handle:block.paragraph_handle.clone(),block_index:block.block_index,normalized_scalar:2};let end=Boundary {normalized_scalar:3,..start.clone()};
    let node=inv.inventory.nodes.iter().find(|n|n.source_handle==block.paragraph_handle).ok_or("node")?;let ids=[node.node_id.clone()];
    for(scope,count)in[(Scope::Document,2),(Scope::Section(&inv.inventory.section_ids),2),(Scope::NodeSet(&ids),1),(Scope::Selection {index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},1)] {
        let q=if matches!(scope,Scope::Selection {..}){Query {mode:Mode::Regex,..query("^B$")}}else{query("B")};
        let out=f.lower_review_selector_style_candidate(&raw,q,scope,all(),declared(),1,Default::default(),Default::default())?;
        assert_eq!(out.receipt().matched_occurrences,count);assert_eq!(values(&output(&raw,&out)?)?.iter().filter(|(_,s)|*s==Some(1)).count(),count);
    }Ok(())
}
#[test]
fn style_replacement_nested_hidden_and_memo_runs_compose_without_overlapping_patch_edits()->TestResult {
    let body=review::body().replace("<hp:run>","<hp:run charPrIDRef='0'>");let raw=fixture::package(&body)?;let f=forms(&raw)?;
    let out=replace(&f,&raw,"K",Scope::Document,all())?;let bytes=output(&raw,&out)?;let actual=values(&bytes)?;
    assert_eq!(actual.iter().filter(|(ch,s)|*ch=='K'&&*s==Some(1)).count(),6);assert!(actual.iter().filter(|(ch,_)|*ch!='K').all(|(_,s)|*s==Some(0)));
    assert_eq!(out.receipt().source_review_import.hidden_explanations,out.receipt().output_review_import.hidden_explanations);
    assert!(section(&bytes)?.contains("PRIVATE-AUTHOR")&&section(&bytes)?.contains("CACHE FROZEN"));Ok(())
}
#[test]
fn style_replacement_review_policies_exclude_before_caps_and_never_widen_excluded_nodes()->TestResult {
    let raw=fixture::package(&review::body().replace("<hp:run>","<hp:run charPrIDRef='0'>"))?;let f=forms(&raw)?;
    for(h,m,count)in[(false,false,2),(true,false,4),(false,true,4),(true,true,6)] {
        let policy=Policy {include_hidden_explanations:h,include_memo_bodies:m};let out=f.lower_review_selector_style_candidate(&raw,Query {max_results:count,..query("K")},Scope::Document,policy,declared(),1,Default::default(),Default::default())?;
        assert_eq!(values(&output(&raw,&out)?)?.iter().filter(|(_,s)|*s==Some(1)).count(),count);assert_eq!(out.receipt().matched_occurrences,count);
    }
    let index=f.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?;let i=inv.block_regions.iter().position(|r|*r==Region::MemoBody).ok_or("memo")?;
    let b=&inv.inventory.blocks[i];let ids=[inv.inventory.nodes.iter().find(|n|n.source_handle==b.paragraph_handle).ok_or("node")?.node_id.clone()];
    assert!(matches!(replace(&f,&raw,"K",Scope::NodeSet(&ids),Policy::default()),Err(E::Compile(Compile::NoMatches))));Ok(())
}
#[test]
fn style_replacement_cache_and_enclosing_fields_reject_even_noops_before_output()->TestResult {
    let body=review::body().replace("<hp:run>","<hp:run charPrIDRef='0'>").replace("CACHE FROZEN","CACHE K");let raw=fixture::package(&body)?;let f=forms(&raw)?;
    assert!(matches!(replace(&f,&raw,"K",Scope::Document,all()),Err(E::Compile(Compile::FieldContent))));
    assert!(matches!(f.lower_review_selector_style_candidate(&raw,query("K"),Scope::Document,all(),declared(),0,Default::default(),Default::default()),Err(E::Compile(Compile::FieldContent))));
    let body=format!("<hp:p id='1'><hp:run charPrIDRef='0'><hp:ctrl><hp:fieldBegin id='99' type='DOC_DATE' editable='1'/></hp:ctrl>{}<hp:ctrl><hp:fieldEnd beginIDRef='99'/></hp:ctrl></hp:run></hp:p>",review::run_body().replace("<hp:run>","<hp:run charPrIDRef='0'>"));
    let raw=fixture::package(&body)?;let f=forms(&raw)?;assert!(matches!(replace(&f,&raw,"K",Scope::Document,all()),Err(E::Compile(Compile::FieldContent))));Ok(())
}
#[test]
fn style_replacement_table_cell_size_and_ancestor_locks_are_preserved()->TestResult {
    let original=table::table(300).replace("<hp:run>","<hp:run charPrIDRef='0'>");
    for(blocked,body)in[(false,original.clone()),(true,original.replace("lock='0'","lock='1'")),(true,original.replacen("protect='0'","protect='1'",1))] {
        let raw0=assembly::package(&body)?;let raw=archive::mutate_part(&raw0,"Contents/header.xml",|_|fixture::header())?;let f=forms(&raw)?;let out=replace(&f,&raw,"OLD",Scope::Document,all());
        if blocked{assert!(matches!(out,Err(E::Compile(Compile::Protection))));}else{let bytes=output(&raw,&out?)?;assert_eq!(values(&bytes)?.iter().filter(|(_,s)|*s==Some(1)).count(),3);}
    }Ok(())
}
#[test]
fn style_replacement_nfc_reordering_and_partial_decomposition_cannot_widen_source_selection()->TestResult {
    let raw=plain("a&#x315;&#x300;")?;let f=forms(&raw)?;assert!(matches!(replace(&f,&raw,"à",Scope::Document,all()),Err(E::Compile(Compile::Selection))));
    let out=replace(&f,&raw,"à\u{315}",Scope::Document,all())?;let bytes=output(&raw,&out)?;assert!(section(&bytes)?.contains("a&#x315;&#x300;"));assert!(values(&bytes)?.iter().all(|(_,s)|*s==Some(1)));
    let raw=plain("&#x344;")?;let f=forms(&raw)?;assert!(matches!(replace(&f,&raw,"\u{308}",Scope::Document,all()),Err(E::Compile(Compile::Selection))));Ok(())
}
#[test]
fn style_replacement_missing_explicit_run_reference_is_not_materialized_on_unselected_text()->TestResult {
    let raw=fixture::package("<hp:p id='1' paraPrIDRef='0'><hp:run><hp:t>ABC</hp:t></hp:run></hp:p>")?;let f=forms(&raw)?;
    let filter=Filter::Declared(Declared {paragraph_property:Some(0),..Default::default()});let out=f.lower_review_selector_style_candidate(&raw,query("B"),Scope::Document,all(),filter,1,Default::default(),Default::default())?;
    assert_eq!(values(&output(&raw,&out)?)?,vec![('A',None),('B',Some(1)),('C',None)]);Ok(())
}
#[test]
fn style_replacement_original_namespace_aliases_and_control_names_are_preserved_once()->TestResult {
    let raw=fixture::package("<hp:p id='1' xmlns:z='http://www.hancom.co.kr/hwpml/2011/paragraph'><z:run charPrIDRef='0'><z:t>AB</z:t><z:ctrl><z:bookmark name='KEEP'/></z:ctrl><z:t>CD</z:t></z:run></hp:p>")?;
    let f=forms(&raw)?;let out=replace(&f,&raw,"B",Scope::Document,all())?;let bytes=output(&raw,&out)?;let xml=section(&bytes)?;
    assert_eq!(xml.matches("<z:bookmark name='KEEP'/>").count(),1);assert!(xml.contains("<z:run")&&xml.contains("<z:t>B</z:t>"));Ok(())
}
#[test]
fn style_replacement_stale_source_foreign_proof_and_scope_require_original_binding()->TestResult {
    let raw=plain("ABC")?;let f=forms(&raw)?;let other=forms(&raw)?;let proof=f.reconstruct_source_for_verification(&raw)?;
    assert!(matches!(proof.lower_review_selector_style_candidate(&other,query("B"),Scope::Document,all(),declared(),1,Default::default(),Default::default()),Err(E::Source)));
    assert!(matches!(replace(&f,&plain("AXC")?,"B",Scope::Document,all()),Err(E::Source)));
    let index=f.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?;let b=&inv.inventory.blocks[0];let start=Boundary {paragraph_handle:b.paragraph_handle.clone(),block_index:b.block_index,normalized_scalar:0};
    let end=Boundary {normalized_scalar:1,..start.clone()};assert!(matches!(replace(&f,&raw,"B",Scope::Selection {index_sha256:[0;32],start:&start,end:&end},all()),Err(E::Search(Search::Scope))));Ok(())
}
#[test]
fn style_replacement_empty_invalid_filters_zero_width_no_matches_and_noop_are_not_success()->TestResult {
    let raw=plain("ABC")?;let f=forms(&raw)?;
    assert!(matches!(f.lower_review_selector_style_candidate(&raw,query("B"),Scope::Document,all(),Filter::Declared(Default::default()),1,Default::default(),Default::default()),Err(E::Search(Search::Filter))));
    assert!(matches!(replace(&f,&raw,"absent",Scope::Document,all()),Err(E::Compile(Compile::NoMatches))));
    assert!(matches!(f.lower_review_selector_style_candidate(&raw,query("B"),Scope::Document,all(),declared(),0,Default::default(),Default::default()),Err(E::Compile(Compile::NoChange))));
    assert!(matches!(f.lower_review_selector_style_candidate(&raw,Query {mode:Mode::Regex,..query("^")},Scope::Document,all(),declared(),1,Default::default(),Default::default()),Err(E::Compile(Compile::NoMatches))));Ok(())
}
#[test]
fn style_replacement_match_fragment_output_writer_and_tracked_change_limits_fail_without_partial_output()->TestResult {
    let raw=plain("ABAB")?;let f=forms(&raw)?;
    assert!(matches!(f.lower_review_selector_style_candidate(&raw,Query {max_results:1,..query("B")},Scope::Document,all(),declared(),1,Default::default(),Default::default()),Err(E::Search(Search::Limit))));
    assert!(f.lower_review_selector_style_candidate(&raw,query("B"),Scope::Document,all(),declared(),1,SourceSearchLimits::new(Config {result_bytes:500,..Default::default()})?,Default::default()).is_err());
    assert!(f.lower_review_selector_style_candidate(&raw,query("B"),Scope::Document,all(),declared(),1,Default::default(),WriterLimits::new(WriterLimitConfig {max_output_bytes:1})?).is_err());
    let raw=fixture::package("<hp:p id='1'><hp:run charPrIDRef='0' charTcId='2'><hp:t>ABC</hp:t></hp:run></hp:p>")?;let f=forms(&raw)?;
    assert!(matches!(replace(&f,&raw,"B",Scope::Document,all()),Err(E::Compile(Compile::Protection))));Ok(())
}
#[test]
fn style_replacement_many_partial_matches_share_one_protection_map_and_keep_receipts_private()->TestResult {
    let raw=plain(&"PRIVATE K ".repeat(256))?;let original=Sha256::digest(&raw);let f=forms(&raw)?;let out=replace(&f,&raw,"K",Scope::Document,all())?;let bytes=output(&raw,&out)?;
    assert_eq!(values(&bytes)?.iter().filter(|(_,s)|*s==Some(1)).count(),256);let xml=PreservingXmlDocument::parse(section(&raw)?.as_bytes())?;
    assert_eq!(out.receipt().observed_protection_parts,1);assert_eq!(out.receipt().observed_protection_element_visits,2*xml.elements().len());
    assert!(!format!("{out:?}{:?}{}",out.receipt(),serde_json::to_string(out.receipt())?).contains("PRIVATE"));assert_eq!(Sha256::digest(&raw),original);Ok(())
}
#[test]
fn style_replacement_casefold_whole_word_and_multiple_text_elements_preserve_unselected_atoms()->TestResult {
    let raw=fixture::package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>Cat scatter </hp:t><hp:t>CAT</hp:t><hp:t/></hp:run></hp:p>")?;let f=forms(&raw)?;
    let out=f.lower_review_selector_style_candidate(&raw,Query {case_sensitive:false,whole_word:true,..query("cat")},Scope::Document,all(),declared(),1,Default::default(),Default::default())?;
    let result=values(&output(&raw,&out)?)?;assert_eq!(result.iter().filter(|(_,s)|*s==Some(1)).count(),6);assert_eq!(result.iter().map(|(c,_)|*c).collect::<String>(),"Cat scatter CAT");Ok(())
}
#[test]
fn style_replacement_target_receipt_uses_exact_original_typed_catalog_declaration()->TestResult {
    use hwpx_package::document_import::fields::{ImportedDocumentFields,semantics::{ImportedDocumentFieldSemantics,catalog::{ImportedDocumentCatalog,ImportedCatalogKind}}};
    let raw=plain("ABC")?;let f=forms(&raw)?;let fields=ImportedDocumentFields::import(&f)?;
    let semantics=ImportedDocumentFieldSemantics::import(&fields)?;let catalog=ImportedDocumentCatalog::import(&semantics)?;
    let expected=&catalog.definitions().iter().find(|d|d.kind==ImportedCatalogKind::CharacterProperty&&d.native_id==1).ok_or("declaration")?.source_anchor;
    let out=replace(&f,&raw,"B",Scope::Document,all())?;assert_eq!(&out.receipt().target_declaration,expected);
    assert_eq!(out.receipt().character_property,1);output(&raw,&out)?;Ok(())
}
