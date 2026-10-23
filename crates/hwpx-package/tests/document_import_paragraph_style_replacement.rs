use hwpx_package::{BoundedZipReader,PackageLimits,PreservingXmlDocument,WriterLimits,WriterLimitConfig,
    document_import::{ImportedSourcePackage,forms::ImportedDocumentForms,search::{SourceSearchQuery as Query,SourceSearchMode as Mode,SourceSearchError as Search,
        SourceSearchLimits,SourceSearchLimitConfig as Config,selector::{SourceIndexScopeSelector as Scope,SourceIndexBoundary as Boundary},
        reviews::{SourceReviewTextPolicy as Policy,selector::styles::SourceReviewStyleFilter as Filter},
        inspection::{SourceDeclaredStyleFilter as Declared,definitions::{SourceDefinitionStyleFilter as Definition,ParagraphDefinitionSource as Axis,DefinitionAlignment as Alignment}},
        replacement::{SourceLiteralReplacementError as Compile,atoms::styles::paragraphs::{SourceParagraphStyleReplacementCandidate as Candidate,
            SourceParagraphStyleReplacementError as E,SourceParagraphStyleTarget as Target,SourceParagraphStyleExtent as Extent}}}}};
use domain_ir::DocumentId;
use sha2::{Digest as _,Sha256};
use std::{error::Error,io::Cursor};
#[allow(dead_code)] #[path="support/search_definition_fixture.rs"] mod fixture;
#[allow(dead_code)] #[path="support/review_scope_fixture.rs"] mod review;
#[allow(dead_code)] #[path="support/document_import_review_assembly_fixture.rs"] mod assembly;
#[allow(dead_code)] #[path="support/review_cell_output_fixture.rs"] mod table;
#[allow(dead_code)] #[path="support/document_import_catalog_fixture.rs"] mod archive;
type TestResult=Result<(),Box<dyn Error>>;
#[path="support/named_paragraph_style_replacement.rs"]mod named;
const EXTENT:Extent=Extent::WholeMatchedParagraphWithinScope;
const TAB:&str="<hp:tab width='1' leader='0' type='0'> </hp:tab>";
fn forms(raw:&[u8])->Result<ImportedDocumentForms,Box<dyn Error>> {Ok(ImportedDocumentForms::import(ImportedSourcePackage::import(raw,DocumentId::parse("paragraph-style")?,Sha256::digest(raw).into(),Default::default())?)?)}
fn p(id:u32,text:&str)->String{format!("<hp:p id='{id}' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'><hp:t>{text}</hp:t></hp:run></hp:p>")}
fn raw(text:&str)->Result<Vec<u8>,Box<dyn Error>>{fixture::package(&p(1,text))}
fn query(q:&str)->Query<'_>{Query {query:q,mode:Mode::Literal,case_sensitive:true,whole_word:false,max_results:10000}}
fn all()->Policy{Policy {include_hidden_explanations:true,include_memo_bodies:true}}
fn filter()->Filter{Filter::Declared(Declared {paragraph_property:Some(0),..Default::default()})}
fn replace(f:&ImportedDocumentForms,raw:&[u8],q:&str,scope:Scope<'_>,target:Target)->Result<Candidate,E>{
    f.lower_review_selector_paragraph_style_candidate(raw,query(q),scope,all(),filter(),target,EXTENT,Default::default(),Default::default())}
fn section(raw:&[u8])->Result<String,Box<dyn Error>> {let mut r=BoundedZipReader::open(Cursor::new(raw),PackageLimits::default())?;
    let i=r.entries().iter().position(|e|e.path.as_str()=="Contents/section0.xml").ok_or("part")?;Ok(String::from_utf8(r.read_entry(i)?)?)}
fn references(raw:&[u8])->Result<Vec<(u32,Option<u32>,Option<u32>)>,Box<dyn Error>> {
    let raw=section(raw)?;let xml=PreservingXmlDocument::parse(raw.as_bytes())?;let mut out=Vec::new();
    for node in xml.elements().iter().filter(|n|n.name().namespace()==Some(hwpx_package::HANCOM_2020_PARAGRAPH_NAMESPACE)&&n.name().local_name()=="p") {
        let get=|name:&str|->Result<Option<u32>,Box<dyn Error>>{Ok(node.attributes().iter().find(|a|a.name().namespace().is_none()&&a.name().local_name()==name)
            .map(|a|quick_xml::escape::unescape(&raw[a.value_span().start()..a.value_span().end()]).map(|s|s.parse::<u32>())).transpose()?.transpose()?)};
        out.push((get("id")?.ok_or("id")?,get("paraPrIDRef")?,get("styleIDRef")?));
    }Ok(out)
}
fn output(raw:&[u8],candidate:&Candidate)->Result<Vec<u8>,Box<dyn Error>> {
    let bytes=candidate.with_verified_bytes(<[u8]>::to_vec)?;let mut a=BoundedZipReader::open(Cursor::new(raw),Default::default())?;
    let mut b=BoundedZipReader::open(Cursor::new(&bytes),Default::default())?;assert_eq!(a.entries().len(),b.entries().len());
    for i in 0..a.entries().len(){let path=a.entries()[i].path.clone();if path.as_str()=="Contents/section0.xml"{continue;}
        let j=b.entries().iter().position(|e|e.path==path).ok_or("part")?;assert_eq!(a.read_entry(i)?,b.read_entry(j)?);}
    let r=candidate.receipt();assert!(r.whole_paragraph_scope_verified&&r.all_original_scalars_controls_run_and_text_references_preserved&&r.every_paragraph_reference_read_back&&r.outside_selected_attribute_edits_exact);
    assert!(!r.effective_style_native_or_service_authority);Ok(bytes)
}
#[test]
fn paragraph_style_two_axes_change_only_the_selected_original_reference_value()->TestResult {
    let bytes=raw("A&amp;B")?;let f=forms(&bytes)?;
    for(target,expected)in[(Target::ParagraphProperty(1),(1,Some(1),Some(0))),(Target::ParagraphStyle(1),(1,Some(0),Some(1)))] {
        let out=replace(&f,&bytes,"B",Scope::Document,target)?;let after=output(&bytes,&out)?;assert_eq!(references(&after)?,vec![expected]);
        let old=section(&bytes)?;let new=section(&after)?;let expected=old.replacen(&format!("{}='0'",target.attribute()),&format!("{}='1'",target.attribute()),1);
        assert_eq!(new,expected);assert_eq!(out.receipt().matched_occurrences,1);assert_eq!(out.receipt().changes.len(),1);
    }Ok(())
}
#[test]
fn paragraph_style_partial_query_explicitly_changes_whole_matched_paragraph_not_other_paragraphs()->TestResult {
    let bytes=fixture::package(&(p(1,"A K B")+&p(2,"KEEP")))?;let f=forms(&bytes)?;let out=replace(&f,&bytes," K ",Scope::Document,Target::ParagraphProperty(1))?;
    assert_eq!(references(&output(&bytes,&out)?)?,vec![(1,Some(1),Some(0)),(2,Some(0),Some(0))]);
    assert_eq!(out.receipt().extent,EXTENT);assert_eq!(out.receipt().matched_paragraphs,1);Ok(())
}
#[test]
fn paragraph_style_four_scopes_require_the_whole_paragraph_and_reject_partial_selection()->TestResult {
    let bytes=fixture::package(&(p(1,"A K B")+&p(2,"K C")))?;let f=forms(&bytes)?;let index=f.source_review_scope_index(&bytes,Default::default())?;let inv=index.scope_inventory()?;
    let b=&inv.inventory.blocks[0];let start=Boundary {paragraph_handle:b.paragraph_handle.clone(),block_index:b.block_index,normalized_scalar:0};let end=Boundary {normalized_scalar:5,..start.clone()};
    let ids=[inv.inventory.nodes.iter().find(|n|n.source_handle==b.paragraph_handle).ok_or("node")?.node_id.clone()];
    for(scope,total)in[(Scope::Document,2),(Scope::Section(&inv.inventory.section_ids),2),(Scope::NodeSet(&ids),1),(Scope::Selection {index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},1)] {
        let out=replace(&f,&bytes,"K",scope,Target::ParagraphProperty(1))?;assert_eq!(out.receipt().matched_paragraphs,total);output(&bytes,&out)?;
    }
    let start=Boundary {normalized_scalar:2,..start};let end=Boundary {normalized_scalar:3,..end};
    assert!(matches!(replace(&f,&bytes,"K",Scope::Selection {index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},Target::ParagraphProperty(1)),Err(E::IncompleteParagraphScope)));Ok(())
}
#[test]
fn paragraph_style_partial_block_selection_cannot_omit_other_blocks_or_control_bytes()->TestResult {
    let bytes=raw(&format!("K{TAB}END<hp:lineBreak> </hp:lineBreak>TAIL"))?;let f=forms(&bytes)?;let out=replace(&f,&bytes,"K",Scope::Document,Target::ParagraphProperty(1))?;
    let after=output(&bytes,&out)?;assert_eq!(section(&after)?.matches(TAB).count(),1);assert!(section(&after)?.contains("<hp:lineBreak> </hp:lineBreak>"));
    let index=f.source_review_scope_index(&bytes,Default::default())?;let inv=index.scope_inventory()?;let b=&inv.inventory.blocks[0];let start=Boundary {paragraph_handle:b.paragraph_handle.clone(),block_index:b.block_index,normalized_scalar:0};let end=Boundary {normalized_scalar:1,..start.clone()};
    assert!(matches!(replace(&f,&bytes,"K",Scope::Selection {index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},Target::ParagraphProperty(1)),Err(E::IncompleteParagraphScope)));Ok(())
}
#[test]
fn paragraph_style_cross_run_hangul_keeps_original_spelling_and_character_axes()->TestResult {
    let bytes=fixture::package("<hp:p id='1' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'><hp:t charStyleIDRef='0'>Xᄀ</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t charStyleIDRef='1'>ᅡᆨY</hp:t></hp:run></hp:p>")?;
    let f=forms(&bytes)?;let out=replace(&f,&bytes,"각",Scope::Document,Target::ParagraphStyle(1))?;let after=output(&bytes,&out)?;
    assert_eq!(section(&after)?,section(&bytes)?.replacen("styleIDRef='0'","styleIDRef='1'",1));Ok(())
}
#[test]
fn paragraph_style_declared_and_definition_filters_use_original_direct_and_named_values()->TestResult {
    let bytes=fixture::package(&(p(1,"K")+&p(2,"K").replace("paraPrIDRef='0'","paraPrIDRef='1'").replace("styleIDRef='0'","styleIDRef='1'")))?;let f=forms(&bytes)?;
    for axis in[Axis::DirectProperty,Axis::NamedStyle] {
        let filter=Filter::Definition(Definition {paragraph_source:Some(axis),alignment:Some(Alignment::Justify),..Default::default()});
        let out=f.lower_review_selector_paragraph_style_candidate(&bytes,query("K"),Scope::Document,all(),filter,Target::ParagraphProperty(1),EXTENT,Default::default(),Default::default())?;
        assert_eq!(out.receipt().matched_occurrences,1);assert_eq!(out.receipt().changes.len(),1);output(&bytes,&out)?;
    }Ok(())
}
#[test]
fn paragraph_style_target_anchor_is_the_exact_original_typed_catalog_declaration()->TestResult {
    use hwpx_package::document_import::fields::{ImportedDocumentFields,semantics::{ImportedDocumentFieldSemantics,catalog::{ImportedDocumentCatalog,ImportedCatalogKind as Kind}}};
    let bytes=raw("K")?;let f=forms(&bytes)?;let fields=ImportedDocumentFields::import(&f)?;let meanings=ImportedDocumentFieldSemantics::import(&fields)?;let catalog=ImportedDocumentCatalog::import(&meanings)?;
    for(target,kind)in[(Target::ParagraphProperty(1),Kind::ParagraphProperty),(Target::ParagraphStyle(1),Kind::NamedStyle)] {
        let expected=&catalog.definitions().iter().find(|d|d.kind==kind&&d.native_id==1).ok_or("definition")?.source_anchor;
        let out=replace(&f,&bytes,"K",Scope::Document,target)?;assert_eq!(&out.receipt().target_declaration,expected);output(&bytes,&out)?;
    }Ok(())
}
#[test]
fn paragraph_style_invalid_targets_and_character_named_style_do_not_become_paragraph_styles()->TestResult {
    let bytes=raw("K")?;let f=forms(&bytes)?;
    for target in[Target::ParagraphProperty(u32::MAX),Target::ParagraphStyle(u32::MAX),Target::ParagraphStyle(12)] {
        assert!(matches!(replace(&f,&bytes,"K",Scope::Document,target),Err(E::Search(Search::Definition))));
    }
    let bytes=fixture::package_with_header(&p(1,"K"),&fixture::header()?.replacen("id=\"1\" type=\"PARA\"","id=\"1\" type=\"FUTURE\"",1))?;let f=forms(&bytes)?;
    assert!(matches!(replace(&f,&bytes,"K",Scope::Document,Target::ParagraphStyle(1)),Err(E::Search(Search::Definition))));Ok(())
}
#[test]
fn paragraph_style_missing_references_are_inserted_only_on_the_chosen_axis_and_paragraph()->TestResult {
    let bytes=fixture::package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>K</hp:t></hp:run></hp:p><hp:p id='2'><hp:run charPrIDRef='0'><hp:t>KEEP</hp:t></hp:run></hp:p>")?;let f=forms(&bytes)?;
    let filter=Filter::Declared(Declared {run_character_property:Some(0),..Default::default()});
    for target in[Target::ParagraphProperty(1),Target::ParagraphStyle(1)] {
        let out=f.lower_review_selector_paragraph_style_candidate(&bytes,query("^K$"),Scope::Document,all(),filter.clone(),target,EXTENT,Default::default(),Default::default());
        // Literal ^K$ does not match; the explicit regex path below does not expand selection.
        assert!(matches!(out,Err(E::Compile(Compile::NoMatches))));
        let out=f.lower_review_selector_paragraph_style_candidate(&bytes,Query {mode:Mode::Regex,..query("^K$")},Scope::Document,all(),filter.clone(),target,EXTENT,Default::default(),Default::default())?;
        let expected=if matches!(target,Target::ParagraphProperty(_)){(1,Some(1),None)}else{(1,None,Some(1))};assert_eq!(references(&output(&bytes,&out)?)?,vec![expected,(2,None,None)]);
        assert_eq!(out.receipt().changes[0].previous_reference,None);
    }Ok(())
}
fn review_bytes()->Result<Vec<u8>,Box<dyn Error>> {
    fixture::package(&review::body().replace("BODY K K","BODY").replace("<hp:p id='1'>","<hp:p id='1' paraPrIDRef='0' styleIDRef='0'>")
        .replace("<hp:p id='11'>","<hp:p id='11' paraPrIDRef='0' styleIDRef='0'>").replace("<hp:p id='12'>","<hp:p id='12' paraPrIDRef='0' styleIDRef='0'>"))
}
#[test]
fn paragraph_style_nested_hidden_and_memo_policies_never_modify_outer_cache_or_paragraph()->TestResult {
    let bytes=review_bytes()?;let f=forms(&bytes)?;
    for(h,m,total)in[(false,false,0),(true,false,1),(false,true,1),(true,true,2)] {
        let policy=Policy {include_hidden_explanations:h,include_memo_bodies:m};
        let result=f.lower_review_selector_paragraph_style_candidate(&bytes,query("K"),Scope::Document,policy,filter(),Target::ParagraphProperty(1),EXTENT,Default::default(),Default::default());
        if total==0{assert!(matches!(result,Err(E::Compile(Compile::NoMatches))));continue;}
        let out=result?;let after=output(&bytes,&out)?;assert_eq!(out.receipt().matched_paragraphs,total);assert_eq!(out.receipt().matched_occurrences,total*2);
        assert_eq!(references(&after)?[0],(1,Some(0),Some(0)));assert!(section(&after)?.contains("CACHE FROZEN"));
    }Ok(())
}
#[test]
fn paragraph_style_unqueried_cached_field_inside_the_matched_paragraph_still_blocks()->TestResult {
    let body=review::body().replace("<hp:p id='1'>","<hp:p id='1' paraPrIDRef='0' styleIDRef='0'>");let bytes=fixture::package(&body)?;let f=forms(&bytes)?;
    for target in[Target::ParagraphProperty(1),Target::ParagraphStyle(1),Target::ParagraphProperty(0)] {
        assert!(matches!(replace(&f,&bytes,"BODY",Scope::Document,target),Err(E::Compile(Compile::FieldContent))));
    }Ok(())
}
#[test]
fn paragraph_style_unqueried_locked_descendant_protects_whole_paragraph_including_noop()->TestResult {
    let table=table::table(300).replace("lock='0'","lock='1'");let bytes=fixture::package(&p(1,&format!("K</hp:t>{table}<hp:t>TAIL")))?;let f=forms(&bytes)?;
    for target in[Target::ParagraphProperty(1),Target::ParagraphProperty(0),Target::ParagraphStyle(1)] {
        assert!(matches!(replace(&f,&bytes,"K",Scope::Document,target),Err(E::Compile(Compile::Protection))));
    }Ok(())
}
#[test]
fn paragraph_style_tracked_paragraph_run_and_unqueried_marker_fail_before_noop_elimination()->TestResult {
    let original=p(1,"K");
    for body in[original.replace("id='1'","id='1' paraTcId='1'"),original.replace("charPrIDRef='0'","charPrIDRef='0' charTcId='1'"),
        p(1,"K<hp:insertBegin id='42'/>TAIL")] {
        let bytes=fixture::package(&body)?;if let Ok(f)=forms(&bytes){assert!(replace(&f,&bytes,"K",Scope::Document,Target::ParagraphProperty(0)).is_err());}
    }Ok(())
}
#[test]
fn paragraph_style_original_namespace_aliases_and_attribute_quotes_remain_exact()->TestResult {
    let bytes=fixture::package("<z:p xmlns:z='http://www.hancom.co.kr/hwpml/2011/paragraph' id='1' paraPrIDRef='&#48;' styleIDRef=\"0\"><z:run charPrIDRef='0'><z:t>K&amp;KEEP</z:t><z:ctrl><z:bookmark name='KEEP'/></z:ctrl></z:run></z:p>")?;let f=forms(&bytes)?;
    let out=replace(&f,&bytes,"K",Scope::Document,Target::ParagraphProperty(1))?;assert_eq!(section(&output(&bytes,&out)?)?,section(&bytes)?.replacen("paraPrIDRef='&#48;'","paraPrIDRef='1'",1));Ok(())
}
#[test]
fn paragraph_style_stale_source_foreign_proof_and_wrong_index_scope_reject()->TestResult {
    let bytes=raw("K")?;let f=forms(&bytes)?;let other=forms(&bytes)?;let proof=f.reconstruct_source_for_verification(&bytes)?;
    assert!(matches!(proof.lower_review_selector_paragraph_style_candidate(&other,query("K"),Scope::Document,all(),filter(),Target::ParagraphProperty(1),EXTENT,Default::default(),Default::default()),Err(E::Source)));
    assert!(matches!(replace(&f,&raw("OTHER")?,"K",Scope::Document,Target::ParagraphProperty(1)),Err(E::Source)));
    let index=f.source_review_scope_index(&bytes,Default::default())?;let inv=index.scope_inventory()?;let b=&inv.inventory.blocks[0];let start=Boundary {paragraph_handle:b.paragraph_handle.clone(),block_index:b.block_index,normalized_scalar:0};let end=Boundary {normalized_scalar:1,..start.clone()};
    assert!(matches!(replace(&f,&bytes,"K",Scope::Selection {index_sha256:[0;32],start:&start,end:&end},Target::ParagraphProperty(1)),Err(E::Search(Search::Scope))));Ok(())
}
#[test]
fn paragraph_style_regex_case_word_options_preserve_query_and_target_identities()->TestResult {
    let bytes=fixture::package(&(p(1,"Cat")+&p(2,"scatter")+&p(3,"CAT")))?;let f=forms(&bytes)?;
    let out=f.lower_review_selector_paragraph_style_candidate(&bytes,Query {mode:Mode::Regex,case_sensitive:false,whole_word:true,..query("c[a]t")},Scope::Document,all(),filter(),Target::ParagraphStyle(1),EXTENT,Default::default(),Default::default())?;
    assert_eq!(references(&output(&bytes,&out)?)?,vec![(1,Some(0),Some(1)),(2,Some(0),Some(0)),(3,Some(0),Some(1))]);assert_eq!(out.receipt().matched_occurrences,2);Ok(())
}
#[test]
fn paragraph_style_invalid_filter_no_matches_noop_zero_width_and_resource_limits_are_not_success()->TestResult {
    let bytes=raw("K K")?;let f=forms(&bytes)?;
    assert!(matches!(f.lower_review_selector_paragraph_style_candidate(&bytes,query("K"),Scope::Document,all(),Filter::Declared(Declared::default()),Target::ParagraphProperty(1),EXTENT,Default::default(),Default::default()),Err(E::Search(Search::Filter))));
    assert!(matches!(replace(&f,&bytes,"absent",Scope::Document,Target::ParagraphProperty(1)),Err(E::Compile(Compile::NoMatches))));
    assert!(matches!(replace(&f,&bytes,"K",Scope::Document,Target::ParagraphProperty(0)),Err(E::Compile(Compile::NoChange))));
    assert!(f.lower_review_selector_paragraph_style_candidate(&bytes,Query {max_results:1,..query("K")},Scope::Document,all(),filter(),Target::ParagraphProperty(1),EXTENT,Default::default(),Default::default()).is_err());
    assert!(f.lower_review_selector_paragraph_style_candidate(&bytes,query("K"),Scope::Document,all(),filter(),Target::ParagraphProperty(1),EXTENT,SourceSearchLimits::new(Config {result_bytes:1,..Default::default()})?,Default::default()).is_err());
    assert!(matches!(f.lower_review_selector_paragraph_style_candidate(&bytes,query("K"),Scope::Document,all(),filter(),Target::ParagraphProperty(1),EXTENT,Default::default(),WriterLimits::new(WriterLimitConfig {max_output_bytes:1})?),Err(E::Compile(Compile::Writer))));
    for pattern in["(","^"]{assert!(f.lower_review_selector_paragraph_style_candidate(&bytes,Query {mode:Mode::Regex,..query(pattern)},Scope::Document,all(),filter(),Target::ParagraphProperty(1),EXTENT,Default::default(),Default::default()).is_err());}Ok(())
}
#[test]
fn paragraph_style_many_paragraphs_share_one_linear_protection_map_and_keep_private_text_hidden()->TestResult {
    let body=(1..=128).map(|id|p(id,"PRIVATE K")).collect::<String>();let bytes=fixture::package(&body)?;let original=bytes.clone();let f=forms(&bytes)?;
    let out=replace(&f,&bytes,"K",Scope::Document,Target::ParagraphProperty(1))?;let after=output(&bytes,&out)?;assert_eq!(out.receipt().matched_paragraphs,128);assert_eq!(out.receipt().changes.len(),128);
    assert!(references(&after)?.iter().all(|(_,v,_)|*v==Some(1)));let xml=PreservingXmlDocument::parse(section(&bytes)?.as_bytes())?;
    assert_eq!(out.receipt().observed_protection_element_visits,xml.elements().len()*3);assert_eq!(bytes,original);
    assert!(!format!("{out:?}{:?}{}",out.receipt(),serde_json::to_string(out.receipt())?).contains("PRIVATE"));Ok(())
}
#[test]
fn paragraph_style_repeated_matches_in_one_paragraph_are_one_atomic_attribute_edit()->TestResult {
    let bytes=raw(&"K ".repeat(128))?;let f=forms(&bytes)?;let out=replace(&f,&bytes,"K",Scope::Document,Target::ParagraphProperty(1))?;
    assert_eq!(out.receipt().matched_occurrences,128);assert_eq!(out.receipt().matched_paragraphs,1);assert_eq!(out.receipt().changes.len(),1);
    assert_eq!(section(&output(&bytes,&out)?)?,section(&bytes)?.replacen("paraPrIDRef='0'","paraPrIDRef='1'",1));Ok(())
}
#[test]
fn paragraph_style_one_protected_request_rejects_the_whole_multi_paragraph_batch()->TestResult {
    let locked=table::table(300).replace("lock='0'","lock='1'");let bytes=fixture::package(&(p(1,"K")+&p(2,&format!("K</hp:t>{locked}<hp:t>TAIL"))))?;let original=bytes.clone();let f=forms(&bytes)?;
    assert!(matches!(replace(&f,&bytes,"K",Scope::Document,Target::ParagraphProperty(1)),Err(E::Compile(Compile::Protection))));assert_eq!(bytes,original);Ok(())
}
