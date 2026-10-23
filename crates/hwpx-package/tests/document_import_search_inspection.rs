use hwpx_package::document_import::{ImportedSourcePackage,SourceImportLimits,structure::ImportedDocumentStructure,
    search::{SourceSearchQuery as Query,SourceSearchMode as Mode,SourceSearchLimits,SourceSearchLimitConfig as Config,SourceSearchError as E,
        scope::SourceSearchScope as Scope,inspection::{SourceDeclaredStyleFilter as Filter,SourceControlKind as Kind}}};
use domain_ir::{DocumentId,LogicalId};
use sha2::{Digest as _,Sha256};
#[allow(dead_code)]
#[path="support/document_import_field_fixture.rs"] mod fixture;
type TestResult=Result<(),Box<dyn std::error::Error>>;
fn source(body:&str)->Result<(Vec<u8>,ImportedDocumentStructure),Box<dyn std::error::Error>> {
    let bytes=fixture::package(body)?;let s=ImportedDocumentStructure::import(ImportedSourcePackage::import(&bytes,
        DocumentId::parse("inspection-document")?,Sha256::digest(&bytes).into(),SourceImportLimits::default())?)?;Ok((bytes,s))
}
fn q(s:&str)->Query<'_> {Query {query:s,mode:Mode::Literal,case_sensitive:true,whole_word:false,max_results:100}}
#[test]
fn declared_style_matches_all_contributing_run_scalars_without_breaking_nfc_provenance()->TestResult {
    let(b,s)=source("<hp:p id='1'><hp:run charPrIDRef='7'><hp:t>e</hp:t></hp:run><hp:run charPrIDRef='8'><hp:t>&#769;</hp:t></hp:run></hp:p><hp:p id='2'><hp:run charPrIDRef='7'><hp:t>é</hp:t></hp:run></hp:p>")?;
    let index=s.source_text_index(&b,Default::default())?;let inspection=index.inspection()?;
    let r=inspection.find_style(q("é"),Scope::MappedDocument,Filter {run_character_property:Some(7),..Default::default()})?;
    assert_eq!(r.text_result().ok_or("text")?.matches().len(),1);assert_eq!(index.find(q("é"))?.matches().len(),2);
    assert!(!inspection.receipt().style_definitions_resolved&&!inspection.receipt().effective_style_or_hidden_visibility_qualified);Ok(())
}
#[test]
fn declared_style_filters_keep_paragraph_run_and_text_reference_axes_distinct_and_missing_not_zero()->TestResult {
    let(b,s)=source("<hp:p id='1' paraPrIDRef='2' styleIDRef='3'><hp:run charPrIDRef='4'><hp:t charStyleIDRef='5'>x</hp:t></hp:run></hp:p><hp:p id='2'><hp:run><hp:t>x</hp:t></hp:run></hp:p>")?;
    let index=s.source_text_index(&b,Default::default())?;let inspection=index.inspection()?;
    let f=Filter {paragraph_property:Some(2),paragraph_style:Some(3),run_character_property:Some(4),text_character_style:Some(5)};
    assert_eq!(inspection.find_style(q("x"),Scope::MappedDocument,f)?.text_result().ok_or("text")?.matches().len(),1);
    for f in [Filter {paragraph_property:Some(0),..Default::default()},Filter {run_character_property:Some(5),..Default::default()},Filter {text_character_style:Some(4),..Default::default()}] {
        assert!(inspection.find_style(q("x"),Scope::MappedDocument,f)?.text_result().ok_or("text")?.matches().is_empty());
    }Ok(())
}
#[test]
fn declared_style_result_limit_counts_only_accepted_candidates_not_other_style_matches()->TestResult {
    let(b,s)=source("<hp:p id='1'><hp:run charPrIDRef='1'><hp:t>x x x</hp:t></hp:run><hp:run charPrIDRef='2'><hp:t>x</hp:t></hp:run></hp:p>")?;
    let index=s.source_text_index(&b,Default::default())?;let inspection=index.inspection()?;let query=Query {max_results:1,..q("x")};
    let result=inspection.find_style(query,Scope::MappedDocument,Filter {run_character_property:Some(2),..Default::default()})?;
    assert_eq!(result.text_result().ok_or("text")?.matches().len(),1);
    assert!(matches!(inspection.find_style(query,Scope::MappedDocument,Filter {run_character_property:Some(1),..Default::default()}),Err(E::Limit)));Ok(())
}
#[test]
fn declared_style_empty_filter_and_zero_width_do_not_invent_source_formatting()->TestResult {
    let(b,s)=source("<hp:p id='1'><hp:run charPrIDRef='2'><hp:t>x</hp:t></hp:run></hp:p>")?;
    let index=s.source_text_index(&b,Default::default())?;let inspection=index.inspection()?;
    assert!(matches!(inspection.find_style(q("x"),Scope::MappedDocument,Default::default()),Err(E::Filter)));
    let result=inspection.find_style(Query {mode:Mode::Regex,..q("^|$")},Scope::MappedDocument,Filter {run_character_property:Some(2),..Default::default()})?;
    assert!(result.text_result().ok_or("text")?.matches().is_empty());Ok(())
}
#[test]
fn structural_controls_include_fields_objects_atoms_and_notes_with_actual_paragraph_anchors()->TestResult {
    let(b,s)=source("<hp:p id='1'><hp:run><hp:t>A<hp:tab width='1' leader='0' type='0'/><hp:lineBreak/></hp:t><hp:ctrl><hp:fieldBegin id='17' type='DATE'/></hp:ctrl><hp:t>CACHE</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='17'/></hp:ctrl><hp:pic/><hp:ctrl><hp:footNote instId='101'><hp:subList><hp:p id='11'><hp:run><hp:t>NOTE<hp:lineBreak/></hp:t></hp:run></hp:p></hp:subList></hp:footNote></hp:ctrl></hp:run></hp:p>")?;
    let index=s.source_text_index(&b,Default::default())?;let inspection=index.inspection()?;
    for (kind,count) in [(Kind::FieldBegin,1),(Kind::FieldEnd,1),(Kind::Picture,1),(Kind::Footnote,1),(Kind::Tab,1),(Kind::LineBreak,2)] {
        let r=inspection.find_control(Scope::MappedDocument,kind,100)?;assert_eq!(r.controls().len(),count);
        for c in r.controls() {s.source().resolve_anchor(&c.control_anchor)?;s.source().resolve_anchor(&c.paragraph_anchor)?;}
    }
    assert!(!inspection.receipt().control_parameter_or_execution_semantics_qualified);Ok(())
}
#[test]
fn structural_control_search_never_descends_foreign_or_unknown_wrappers_or_unmapped_paragraphs()->TestResult {
    let(b,s)=source("<hp:p id='1'><hp:run><hp:t>x</hp:t><u:pic/><u:future><hp:pic/><hp:p id='2'><hp:run><hp:pic/></hp:run></hp:p></u:future><hp:ctrl><u:future><hp:pic/></u:future></hp:ctrl><hp:pic/></hp:run></hp:p>")?;
    let index=s.source_text_index(&b,Default::default())?;let inspection=index.inspection()?;
    assert_eq!(inspection.find_control(Scope::MappedDocument,Kind::Picture,100)?.controls().len(),1);
    assert!(inspection.receipt().skipped_opaque_items>=3);Ok(())
}
#[test]
fn structural_control_scope_result_limits_and_request_digests_remain_bound()->TestResult {
    let(b,s)=source("<hp:p id='1'><hp:run><hp:pic/></hp:run></hp:p><hp:p id='2'><hp:run><hp:pic/></hp:run></hp:p>")?;
    let index=s.source_text_index(&b,Default::default())?;let inspection=index.inspection()?;
    let all=inspection.find_control(Scope::MappedDocument,Kind::Picture,100)?;
    let id=all.controls()[0].paragraph_anchor.opaque_handle.clone();
    let one=inspection.find_control(Scope::Paragraphs(&[id]),Kind::Picture,1)?;assert_eq!(one.controls().len(),1);
    assert_ne!(one.request_sha256(),all.request_sha256());assert!(matches!(inspection.find_control(Scope::MappedDocument,Kind::Picture,1),Err(E::Limit)));
    assert!(matches!(inspection.find_control(Scope::Paragraphs(&[LogicalId::parse("foreign")?]),Kind::Table,100),Err(E::Scope)));Ok(())
}
#[test]
fn inspection_metadata_and_whole_response_are_bounded_without_leaking_query_or_text()->TestResult {
    let(b,s)=source("<hp:p id='1'><hp:run charPrIDRef='1'><hp:t>PRIVATE-SEARCH-TEXT</hp:t></hp:run></hp:p>")?;
    let index=s.source_text_index(&b,Default::default())?;let inspection=index.inspection()?;
    let result=inspection.find_style(q("PRIVATE-SEARCH-TEXT"),Scope::MappedDocument,Filter {run_character_property:Some(1),..Default::default()})?;
    assert!(!String::from_utf8(result.canonical_json()?)?.contains("PRIVATE"));assert!(!format!("{inspection:?}{result:?}").contains("PRIVATE"));
    let tight=s.source_text_index(&b,SourceSearchLimits::new(Config {result_bytes:1,..Default::default()})?)?;
    assert!(matches!(tight.inspection(),Err(E::Output)));Ok(())
}
#[test]
fn structural_controls_respect_official_parent_sites_and_inspect_direct_atoms_even_when_text_is_opaque()->TestResult {
    let(b,s)=source("<hp:p id='1'><hp:run><hp:tab width='1' leader='0' type='0'/><hp:ctrl><hp:pic/></hp:ctrl><hp:t><hp:titleMark ignore='false'/><hp:nbSpace/><u:future><hp:tab width='1' leader='0' type='0'/></u:future></hp:t></hp:run></hp:p>")?;
    let index=s.source_text_index(&b,Default::default())?;let inspection=index.inspection()?;
    assert!(inspection.find_control(Scope::MappedDocument,Kind::Tab,100)?.controls().is_empty());
    assert!(inspection.find_control(Scope::MappedDocument,Kind::Picture,100)?.controls().is_empty());
    assert_eq!(inspection.find_control(Scope::MappedDocument,Kind::TitleMark,100)?.controls().len(),1);
    assert_eq!(inspection.find_control(Scope::MappedDocument,Kind::NonbreakingSpace,100)?.controls().len(),1);Ok(())
}
