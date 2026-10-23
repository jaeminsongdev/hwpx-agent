use hwpx_package::{CharacterStyleCatalogReader,CharacterStyleLimits,BinaryProperty,document_import::{ImportedSourcePackage,
    SourceImportLimits,structure::ImportedDocumentStructure,search::{SourceSearchLimits,SourceSearchLimitConfig as Config,
    SourceSearchError as E,SourceSearchMode as Mode,SourceSearchQuery as Query,scope::SourceSearchScope as Scope,
    inspection::definitions::{SourceDefinitionStyleFilter as Filter,CharacterDefinitionSource as C,ParagraphDefinitionSource as P,DefinitionAlignment as A}}}};
use domain_ir::{DocumentId,LogicalId};
use sha2::{Digest as _,Sha256};
#[path="support/search_definition_fixture.rs"] mod fixture;
type TestResult=Result<(),Box<dyn std::error::Error>>;
fn import(b:&[u8],doc:&str)->Result<ImportedDocumentStructure,Box<dyn std::error::Error>> {Ok(ImportedDocumentStructure::import(ImportedSourcePackage::import(
    b,DocumentId::parse(doc)?,Sha256::digest(b).into(),SourceImportLimits::default())?)?)}
fn body()->&'static str {"<hp:p id='1' paraPrIDRef='1' styleIDRef='0'><hp:run charPrIDRef='1'><hp:t charStyleIDRef='0'>x</hp:t></hp:run></hp:p><hp:p id='2' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'><hp:t charStyleIDRef='1'>x</hp:t></hp:run></hp:p>"}
fn q(s:&str)->Query<'_> {Query {query:s,mode:Mode::Literal,case_sensitive:true,whole_word:false,max_results:100}}
fn bold()->Filter {Filter {character_source:Some(C::RunProperty),bold:Some(true),..Default::default()}}
#[test]
fn definition_style_search_binds_typed_bold_italic_height_color_and_paragraph_alignment()->TestResult {
    let b=fixture::package(body())?;let source=import(&b,"definitions")?;let text=source.source_text_index(&b,Default::default())?;
    let inspection=text.inspection()?;let definitions=inspection.resolve_style_definitions()?;
    let filter=Filter {italic:Some(true),height_hwpunit:Some(1000),text_rgb:Some([0,0,0]),paragraph_source:Some(P::DirectProperty),alignment:Some(A::Right),..bold()};
    let result=definitions.find(q("x"),Scope::MappedDocument,filter)?;assert_eq!(result.matches().matches().len(),1);
    assert_eq!(definitions.receipt().character_definitions,7);assert_eq!(definitions.receipt().paragraph_definitions,20);
    assert!(definitions.receipt().all_present_indexed_references_resolved);assert!(!definitions.receipt().implicit_cascade_or_hidden_visibility_qualified);
    let oracle=CharacterStyleCatalogReader::read(fixture::header()?.as_bytes(),CharacterStyleLimits::default())?;
    assert_eq!(oracle.styles[1].effects.bold,BinaryProperty::On);assert_eq!(oracle.styles[1].effects.italic,BinaryProperty::On);Ok(())
}
#[test]
fn definition_style_source_axes_distinguish_run_text_and_named_definitions_without_precedence_inference()->TestResult {
    let b=fixture::package(body())?;let source=import(&b,"axes")?;let text=source.source_text_index(&b,Default::default())?;
    let inspection=text.inspection()?;let definitions=inspection.resolve_style_definitions()?;
    let run=definitions.find(q("x"),Scope::MappedDocument,bold())?;
    let span=definitions.find(q("x"),Scope::MappedDocument,Filter {character_source:Some(C::TextStyle),..bold()})?;
    assert_eq!(run.matches().matches().len(),1);assert_eq!(span.matches().matches().len(),1);
    assert_ne!(run.matches().matches()[0].paragraph_anchor,span.matches().matches()[0].paragraph_anchor);
    let named=definitions.find(q("x"),Scope::MappedDocument,Filter {character_source:Some(C::NamedStyle),bold:Some(false),..Default::default()})?;
    assert_eq!(named.matches().matches().len(),2);assert_ne!(run.request_sha256(),span.request_sha256());
    assert!(definitions.find(q("x"),Scope::MappedDocument,Filter {paragraph_source:Some(P::NamedStyle),alignment:Some(A::Right),..Default::default()})?.matches().matches().is_empty());Ok(())
}
#[test]
fn definition_style_absent_direct_axes_never_fall_back_to_zero_or_named_style()->TestResult {
    let b=fixture::package("<hp:p id='1' styleIDRef='0'><hp:run><hp:t>x</hp:t></hp:run></hp:p>")?;let source=import(&b,"missing")?;
    let text=source.source_text_index(&b,Default::default())?;let inspection=text.inspection()?;let definitions=inspection.resolve_style_definitions()?;
    assert_eq!(definitions.receipt().missing_run_references,1);assert_eq!(definitions.receipt().missing_text_references,1);
    assert!(definitions.find(q("x"),Scope::MappedDocument,Filter {bold:Some(false),..bold()})?.matches().matches().is_empty());
    assert_eq!(definitions.find(q("x"),Scope::MappedDocument,Filter {character_source:Some(C::NamedStyle),bold:Some(false),..Default::default()})?.matches().matches().len(),1);Ok(())
}
#[test]
fn definition_style_all_present_reference_axes_reject_dangling_ids_before_matching()->TestResult {
    for (from,to) in [("paraPrIDRef='1'","paraPrIDRef='999'"),("styleIDRef='0'","styleIDRef='999'"),
        ("charPrIDRef='1'","charPrIDRef='999'"),("charStyleIDRef='0'","charStyleIDRef='999'")] {
        let b=fixture::package(&body().replacen(from,to,1))?;let source=import(&b,"dangling")?;
        let text=source.source_text_index(&b,Default::default())?;let inspection=text.inspection()?;
        assert!(matches!(inspection.resolve_style_definitions(),Err(E::Definition)));
    }Ok(())
}
#[test]
fn definition_style_invalid_header_counts_and_named_links_are_not_admitted_as_empty_definitions()->TestResult {
    for header in [fixture::header()?.replacen("charProperties itemCnt=\"7\"","charProperties itemCnt=\"8\"",1),
        fixture::header()?.replacen("nextStyleIDRef=\"0\"","nextStyleIDRef=\"999\"",1)] {
        let b=fixture::package_with_header(body(),&header)?;let source=import(&b,"header-rejection")?;
        let text=source.source_text_index(&b,Default::default())?;let inspection=text.inspection()?;
        assert!(matches!(inspection.resolve_style_definitions(),Err(E::Definition)));
    }Ok(())
}
#[test]
fn definition_style_conditions_need_explicit_used_axes_and_reject_empty_filters()->TestResult {
    for filter in [Filter::default(),Filter {bold:Some(true),..Default::default()},Filter {character_source:Some(C::RunProperty),..Default::default()},
        Filter {alignment:Some(A::Right),..Default::default()},Filter {paragraph_source:Some(P::DirectProperty),..Default::default()}] {
        assert!(matches!(filter.validate(),Err(E::Filter)));
    }
    bold().validate()?;Filter {paragraph_source:Some(P::DirectProperty),alignment:Some(A::Justify),..Default::default()}.validate()?;Ok(())
}
#[test]
fn definition_style_results_obey_scope_zero_width_and_accepted_match_limits()->TestResult {
    let b=fixture::package(body())?;let source=import(&b,"scoped")?;let text=source.source_text_index(&b,Default::default())?;
    let inspection=text.inspection()?;let definitions=inspection.resolve_style_definitions()?;
    let all=definitions.find(Query {max_results:1,..q("x")},Scope::MappedDocument,bold())?;assert_eq!(all.matches().matches().len(),1);
    let id=all.matches().matches()[0].paragraph_anchor.opaque_handle.clone();
    assert_eq!(definitions.find(q("x"),Scope::Paragraphs(&[id]),bold())?.matches().matches().len(),1);
    assert!(definitions.find(Query {mode:Mode::Regex,..q("^|$")},Scope::MappedDocument,bold())?.matches().matches().is_empty());
    assert!(matches!(definitions.find(q("absent"),Scope::Paragraphs(&[LogicalId::parse("foreign")?]),bold()),Err(E::Scope)));Ok(())
}
#[test]
fn definition_style_output_budget_includes_binding_wrapper_and_does_not_expose_text_or_query()->TestResult {
    let b=fixture::package(body())?;let source=import(&b,"bounded")?;let text=source.source_text_index(&b,Default::default())?;
    let inspection=text.inspection()?;let definitions=inspection.resolve_style_definitions()?;
    let result=definitions.find(q("PRIVATE-ABSENT"),Scope::MappedDocument,bold())?;let output=result.canonical_json()?;
    assert!(!String::from_utf8(output.clone())?.contains("PRIVATE"));assert!(!format!("{definitions:?}{result:?}").contains("PRIVATE"));
    let bounded=source.source_text_index(&b,SourceSearchLimits::new(Config {result_bytes:output.len()-1,..Default::default()})?)?;
    let inspection=bounded.inspection()?;let definitions=inspection.resolve_style_definitions()?;
    assert!(matches!(definitions.find(q("PRIVATE-ABSENT"),Scope::MappedDocument,bold()),Err(E::Output)));Ok(())
}
#[test]
fn definition_style_source_and_header_changes_bind_new_results_and_cannot_revalidate_old_index()->TestResult {
    let b=fixture::package(body())?;let changed=fixture::package_with_header(body(),&fixture::header()?.replace("<hh:bold/>",""))?;
    let source=import(&b,"binding")?;let other=import(&changed,"binding")?;let text=source.source_text_index(&b,Default::default())?;
    let other_text=other.source_text_index(&changed,Default::default())?;
    let i=text.inspection()?;let j=other_text.inspection()?;let a=i.resolve_style_definitions()?;let z=j.resolve_style_definitions()?;
    assert_ne!(a.receipt().header_sha256,z.receipt().header_sha256);
    assert_ne!(a.find(q("x"),Scope::MappedDocument,bold())?.request_sha256(),z.find(q("x"),Scope::MappedDocument,bold())?.request_sha256());
    assert!(text.verify_source(&changed).is_err());Ok(())
}

struct FixtureDiagnostic(&'static str);
impl std::fmt::Debug for FixtureDiagnostic {fn fmt(&self,f:&mut std::fmt::Formatter<'_>)->std::fmt::Result {f.write_str(self.0)}}
impl std::fmt::Display for FixtureDiagnostic {fn fmt(&self,f:&mut std::fmt::Formatter<'_>)->std::fmt::Result {f.write_str(self.0)}}
impl std::error::Error for FixtureDiagnostic {}
#[test]
fn definition_fixture_original_typed_readers_and_catalog_join_are_independently_admissible()->TestResult {
    use hwpx_package::{ParagraphStyleCatalogReader,ParagraphStyleLimits,document_import::{forms::ImportedDocumentForms,
        fields::{ImportedDocumentFields,semantics::{ImportedDocumentFieldSemantics,catalog::{ImportedDocumentCatalog,CatalogImportError}}}}};
    let header=fixture::header()?;
    let chars=CharacterStyleCatalogReader::read(header.as_bytes(),Default::default()).map_err(|e|FixtureDiagnostic(e.code()))?;
    let paras=ParagraphStyleCatalogReader::read(header.as_bytes(),ParagraphStyleLimits::default()).map_err(|e|FixtureDiagnostic(e.code()))?;
    paras.validate_character_style_references(&chars).map_err(|e|FixtureDiagnostic(e.code()))?;
    let bytes=fixture::package(body())?;
    let forms=ImportedDocumentForms::import(ImportedSourcePackage::import(&bytes,DocumentId::parse("fixture-diagnostic")?,Sha256::digest(&bytes).into(),SourceImportLimits::default())?)?;
    let fields=ImportedDocumentFields::import(&forms)?;let meanings=ImportedDocumentFieldSemantics::import(&fields)?;
    let _catalog=ImportedDocumentCatalog::import(&meanings).map_err(|e|FixtureDiagnostic(match e {
        CatalogImportError::Character {code}|CatalogImportError::Paragraph {code}=>code,
        CatalogImportError::Header=>"CATALOG_HEADER",CatalogImportError::Count=>"CATALOG_COUNT",CatalogImportError::Id=>"CATALOG_ID",
        CatalogImportError::Duplicate=>"CATALOG_DUPLICATE",CatalogImportError::Dangling=>"CATALOG_DANGLING",_=>"CATALOG_OTHER_JOIN",
    }))?;Ok(())
}
