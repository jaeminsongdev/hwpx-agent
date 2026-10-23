use hwpx_package::{BoundedZipReader,PackageLimits,PreservingXmlDocument,XmlTokenKind,WriterLimits,WriterLimitConfig,
    document_import::{ImportedSourcePackage,forms::ImportedDocumentForms,search::{SourceSearchQuery as Query,SourceSearchMode as Mode,SourceSearchError as Search,
        SourceSearchLimits,SourceSearchLimitConfig as Config,selector::{SourceIndexScopeSelector as Scope,SourceIndexBoundary as Boundary},
        reviews::{SourceReviewTextPolicy as Policy,SourceTextRegion as Region,selector::styles::SourceReviewStyleFilter as Filter},
        inspection::{SourceDeclaredStyleFilter as Declared,definitions::{SourceDefinitionStyleFilter as Definition,CharacterDefinitionSource as Axis}},
        replacement::{SourceLiteralReplacementError as Compile,atoms::styles::{SourceStyleReplacementError as E,text::SourceTextStyleReplacementCandidate as Candidate}}}}};
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
fn forms(raw:&[u8])->Result<ImportedDocumentForms,Box<dyn Error>> {Ok(ImportedDocumentForms::import(ImportedSourcePackage::import(raw,DocumentId::parse("text-style")?,Sha256::digest(raw).into(),Default::default())?)?)}
fn plain(text:&str)->Result<Vec<u8>,Box<dyn Error>> {fixture::package(&format!("<hp:p id='1' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'><hp:t charStyleIDRef='0'>{text}</hp:t></hp:run></hp:p>"))}
fn query(q:&str)->Query<'_>{Query {query:q,mode:Mode::Literal,case_sensitive:true,whole_word:false,max_results:10000}}
fn all()->Policy{Policy {include_hidden_explanations:true,include_memo_bodies:true}}
fn filter()->Filter{Filter::Declared(Declared {text_character_style:Some(0),..Default::default()})}
fn replace(f:&ImportedDocumentForms,raw:&[u8],q:&str,scope:Scope<'_>,policy:Policy)->Result<Candidate,E>{
    f.lower_review_selector_text_style_candidate(raw,query(q),scope,policy,filter(),1,Default::default(),Default::default())}
fn section(raw:&[u8])->Result<String,Box<dyn Error>> {let mut r=BoundedZipReader::open(Cursor::new(raw),PackageLimits::default())?;
    let i=r.entries().iter().position(|e|e.path.as_str()=="Contents/section0.xml").ok_or("part")?;Ok(String::from_utf8(r.read_entry(i)?)?)}
fn values(raw:&[u8])->Result<Vec<(char,Option<u32>,Option<u32>)>,Box<dyn Error>> {
    let raw=section(raw)?;let xml=PreservingXmlDocument::parse(raw.as_bytes())?;let mut out=Vec::new();
    let reference=|node:&hwpx_package::XmlElementToken,name:&str|->Result<Option<u32>,Box<dyn Error>> {
        let Some(a)=node.attributes().iter().find(|a|a.name().namespace().is_none()&&a.name().local_name()==name)else{return Ok(None)};
        Ok(Some(quick_xml::escape::unescape(&raw[a.value_span().start()..a.value_span().end()])?.parse()?))};
    for token in xml.tokens().iter().filter(|t|matches!(t.kind(),XmlTokenKind::Text|XmlTokenKind::Whitespace|XmlTokenKind::Reference)) {
        let Some(t)=token.element_index().and_then(|i|xml.elements().get(i))else{continue};if t.name().local_name()!="t"{continue;}
        let run=&xml.elements()[t.parent().ok_or("run")?];let span=token.span();let decoded=quick_xml::escape::unescape(&raw[span.start()..span.end()])?;
        let r=reference(run,"charPrIDRef")?;let s=reference(t,"charStyleIDRef")?;out.extend(decoded.chars().map(|c|(c,r,s)));
    }Ok(out)
}
fn output(raw:&[u8],candidate:&Candidate)->Result<Vec<u8>,Box<dyn Error>> {
    let bytes=candidate.with_verified_bytes(<[u8]>::to_vec)?;let mut a=BoundedZipReader::open(Cursor::new(raw),Default::default())?;
    let mut b=BoundedZipReader::open(Cursor::new(&bytes),Default::default())?;assert_eq!(a.entries().len(),b.entries().len());
    for i in 0..a.entries().len(){let path=a.entries()[i].path.clone();if path.as_str()=="Contents/section0.xml"{continue;}
        let j=b.entries().iter().position(|e|e.path==path).ok_or("part")?;assert_eq!(a.read_entry(i)?,b.read_entry(j)?);}
    let r=candidate.receipt();assert!(r.original_scalars_controls_and_run_references_preserved&&r.every_original_scalar_text_style_read_back&&r.outside_original_text_edits_exact&&r.original_run_boundaries_preserved);
    assert!(!r.effective_paragraph_named_style_native_or_service_authority);Ok(bytes)
}
#[test]
fn text_style_partial_entity_spelling_and_run_shell_are_preserved()->TestResult {
    let raw=plain("A&#x1F600;B&amp;C")?;let f=forms(&raw)?;let out=replace(&f,&raw,"😀B",Scope::Document,all())?;let bytes=output(&raw,&out)?;
    assert_eq!(values(&bytes)?,vec![('A',Some(0),Some(0)),('😀',Some(0),Some(1)),('B',Some(0),Some(1)),('&',Some(0),Some(0)),('C',Some(0),Some(0))]);
    let xml=section(&bytes)?;assert!(xml.contains("&#x1F600;B")&&xml.contains("&amp;C"));assert_eq!(xml.matches("<hp:run charPrIDRef='0'>").count(),1);
    assert_eq!(out.receipt().original_changed_text_elements,1);assert_eq!(out.receipt().generated_text_fragments,3);Ok(())
}
#[test]
fn text_style_cross_run_nfc_keeps_jamo_and_distinct_run_properties()->TestResult {
    let raw=fixture::package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t charStyleIDRef='0'>Xᄀ</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t charStyleIDRef='0'>ᅡ</hp:t></hp:run><hp:run charPrIDRef='0'><hp:t charStyleIDRef='0'>ᆨY</hp:t></hp:run></hp:p>")?;
    let f=forms(&raw)?;let out=replace(&f,&raw,"각",Scope::Document,all())?;let bytes=output(&raw,&out)?;
    assert_eq!(values(&bytes)?,vec![('X',Some(0),Some(0)),('ᄀ',Some(0),Some(1)),('ᅡ',Some(1),Some(1)),('ᆨ',Some(0),Some(1)),('Y',Some(0),Some(0))]);
    assert_eq!(out.receipt().original_changed_text_elements,3);Ok(())
}
#[test]
fn text_style_control_bytes_and_control_text_style_are_not_restored_as_selected_text()->TestResult {
    let raw=plain(&format!("A{TAB}BC<hp:lineBreak> </hp:lineBreak>D"))?;let f=forms(&raw)?;let out=replace(&f,&raw,"B",Scope::Document,all())?;
    let bytes=output(&raw,&out)?;let xml=section(&bytes)?;assert_eq!(xml.matches(TAB).count(),1);assert_eq!(xml.matches("<hp:lineBreak> </hp:lineBreak>").count(),1);
    assert_eq!(values(&bytes)?.iter().filter(|(_,_,s)|*s==Some(1)).count(),1);
    assert!(matches!(replace(&f,&raw,"\t",Scope::Document,all()),Err(E::Compile(Compile::Selection))));Ok(())
}
#[test]
fn text_style_definition_predicate_targets_same_original_typed_catalog()->TestResult {
    use hwpx_package::document_import::fields::{ImportedDocumentFields,semantics::{ImportedDocumentFieldSemantics,catalog::{ImportedDocumentCatalog,ImportedCatalogKind}}};
    let raw=plain("Cat scatter CAT")?;let f=forms(&raw)?;let fields=ImportedDocumentFields::import(&f)?;
    let semantics=ImportedDocumentFieldSemantics::import(&fields)?;let catalog=ImportedDocumentCatalog::import(&semantics)?;
    let expected=&catalog.definitions().iter().find(|d|d.kind==ImportedCatalogKind::CharacterProperty&&d.native_id==1).ok_or("target")?.source_anchor;
    let definition=Filter::Definition(Definition {character_source:Some(Axis::TextStyle),bold:Some(false),..Default::default()});
    let out=f.lower_review_selector_text_style_candidate(&raw,Query {mode:Mode::Regex,case_sensitive:false,whole_word:true,..query("c[a]t")},Scope::Document,all(),definition,1,Default::default(),Default::default())?;
    assert_eq!(&out.receipt().target_declaration,expected);assert_eq!(out.receipt().matched_occurrences,2);
    assert_eq!(values(&output(&raw,&out)?)?.iter().filter(|(_,_,s)|*s==Some(1)).count(),6);Ok(())
}
#[test]
fn text_style_four_scopes_and_clipped_regex_windows_do_not_widen_edits()->TestResult {
    let raw=fixture::package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t charStyleIDRef='0'>A B</hp:t></hp:run></hp:p><hp:p id='2'><hp:run charPrIDRef='0'><hp:t charStyleIDRef='0'>B C</hp:t></hp:run></hp:p>")?;
    let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?;let b=&inv.inventory.blocks[0];
    let start=Boundary {paragraph_handle:b.paragraph_handle.clone(),block_index:b.block_index,normalized_scalar:2};let end=Boundary {normalized_scalar:3,..start.clone()};
    let ids=[inv.inventory.nodes.iter().find(|n|n.source_handle==b.paragraph_handle).ok_or("node")?.node_id.clone()];
    for(scope,count)in[(Scope::Document,2),(Scope::Section(&inv.inventory.section_ids),2),(Scope::NodeSet(&ids),1),(Scope::Selection {index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},1)] {
        let q=if matches!(scope,Scope::Selection {..}){Query {mode:Mode::Regex,..query("^B$")}}else{query("B")};
        let out=f.lower_review_selector_text_style_candidate(&raw,q,scope,all(),filter(),1,Default::default(),Default::default())?;
        assert_eq!(out.receipt().matched_occurrences,count);assert_eq!(values(&output(&raw,&out)?)?.iter().filter(|(_,_,s)|*s==Some(1)).count(),count);
    }Ok(())
}
#[test]
fn text_style_nested_review_policies_exclude_before_caps_and_cache_is_unchanged()->TestResult {
    let body=review::body().replace("<hp:t>","<hp:t charStyleIDRef='0'>");let raw=fixture::package(&body)?;let f=forms(&raw)?;
    for(h,m,count)in[(false,false,2),(true,false,4),(false,true,4),(true,true,6)] {
        let out=f.lower_review_selector_text_style_candidate(&raw,Query {max_results:count,..query("K")},Scope::Document,Policy {include_hidden_explanations:h,include_memo_bodies:m},filter(),1,Default::default(),Default::default())?;
        let bytes=output(&raw,&out)?;assert_eq!(values(&bytes)?.iter().filter(|(c,_,s)|*c=='K'&&*s==Some(1)).count(),count);assert!(section(&bytes)?.contains("CACHE FROZEN"));
    }
    let index=f.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?;let i=inv.block_regions.iter().position(|r|*r==Region::MemoBody).ok_or("memo")?;
    let b=&inv.inventory.blocks[i];let ids=[inv.inventory.nodes.iter().find(|n|n.source_handle==b.paragraph_handle).ok_or("node")?.node_id.clone()];
    assert!(matches!(replace(&f,&raw,"K",Scope::NodeSet(&ids),Policy::default()),Err(E::Compile(Compile::NoMatches))));Ok(())
}
#[test]
fn text_style_caches_and_enclosing_fields_reject_including_noop_targets()->TestResult {
    let body=review::body().replace("<hp:t>","<hp:t charStyleIDRef='0'>").replace("CACHE FROZEN","CACHE K");let raw=fixture::package(&body)?;let f=forms(&raw)?;
    assert!(matches!(replace(&f,&raw,"K",Scope::Document,all()),Err(E::Compile(Compile::FieldContent))));
    assert!(matches!(f.lower_review_selector_text_style_candidate(&raw,query("K"),Scope::Document,all(),filter(),0,Default::default(),Default::default()),Err(E::Compile(Compile::FieldContent))));
    let raw=fixture::package("<hp:p id='1'><hp:run><hp:ctrl><hp:fieldBegin id='99' type='DOC_DATE' editable='1'/></hp:ctrl><hp:t charStyleIDRef='0'>K</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='99'/></hp:ctrl></hp:run></hp:p>")?;
    let f=forms(&raw)?;assert!(matches!(replace(&f,&raw,"K",Scope::Document,all()),Err(E::Compile(Compile::FieldContent))));Ok(())
}
#[test]
fn text_style_table_cell_and_ancestor_locks_fail_closed()->TestResult {
    let original=table::table(300).replace("<hp:t>","<hp:t charStyleIDRef='0'>");
    for(blocked,body)in[(false,original.clone()),(true,original.replace("lock='0'","lock='1'")),(true,original.replacen("protect='0'","protect='1'",1))] {
        let raw0=assembly::package(&body)?;let raw=archive::mutate_part(&raw0,"Contents/header.xml",|_|fixture::header())?;let f=forms(&raw)?;let out=replace(&f,&raw,"OLD",Scope::Document,all());
        if blocked{assert!(matches!(out,Err(E::Compile(Compile::Protection))));}else{assert_eq!(values(&output(&raw,&out?)?)?.iter().filter(|(_,_,s)|*s==Some(1)).count(),3);}
    }Ok(())
}
#[test]
fn text_style_nfc_ambiguous_and_partial_decompositions_do_not_widen_selection()->TestResult {
    let raw=plain("a&#x315;&#x300;")?;let f=forms(&raw)?;assert!(matches!(replace(&f,&raw,"à",Scope::Document,all()),Err(E::Compile(Compile::Selection))));
    let out=replace(&f,&raw,"à\u{315}",Scope::Document,all())?;assert!(section(&output(&raw,&out)?)?.contains("a&#x315;&#x300;"));
    let raw=plain("&#x344;")?;let f=forms(&raw)?;assert!(matches!(replace(&f,&raw,"\u{308}",Scope::Document,all()),Err(E::Compile(Compile::Selection))));Ok(())
}
#[test]
fn text_style_missing_reference_is_not_materialized_on_unselected_scalars()->TestResult {
    let raw=fixture::package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>ABC</hp:t></hp:run></hp:p>")?;let f=forms(&raw)?;
    let declared=Filter::Declared(Declared {run_character_property:Some(0),..Default::default()});
    let out=f.lower_review_selector_text_style_candidate(&raw,query("B"),Scope::Document,all(),declared,1,Default::default(),Default::default())?;
    assert_eq!(values(&output(&raw,&out)?)?,vec![('A',Some(0),None),('B',Some(0),Some(1)),('C',Some(0),None)]);Ok(())
}
#[test]
fn text_style_namespaces_and_original_control_ids_are_retained_once()->TestResult {
    let raw=fixture::package("<hp:p id='1' xmlns:z='http://www.hancom.co.kr/hwpml/2011/paragraph'><z:run charPrIDRef='0'><z:t charStyleIDRef='0'>AB</z:t><z:ctrl><z:bookmark name='KEEP'/></z:ctrl><z:t charStyleIDRef='0'>CD</z:t></z:run></hp:p>")?;
    let f=forms(&raw)?;let out=replace(&f,&raw,"B",Scope::Document,all())?;let bytes=output(&raw,&out)?;let xml=section(&bytes)?;
    assert_eq!(xml.matches("<z:run charPrIDRef='0'>").count(),1);assert_eq!(xml.matches("<z:bookmark name='KEEP'/>").count(),1);assert_eq!(values(&bytes)?.iter().filter(|(_,_,s)|*s==Some(1)).count(),1);Ok(())
}
#[test]
fn text_style_fresh_source_proof_and_selector_identities_are_required()->TestResult {
    let raw=plain("ABC")?;let f=forms(&raw)?;let other=forms(&raw)?;let proof=f.reconstruct_source_for_verification(&raw)?;
    assert!(matches!(proof.lower_review_selector_text_style_candidate(&other,query("B"),Scope::Document,all(),filter(),1,Default::default(),Default::default()),Err(E::Source)));
    assert!(matches!(replace(&f,&plain("AXC")?,"B",Scope::Document,all()),Err(E::Source)));
    let index=f.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?;let b=&inv.inventory.blocks[0];let start=Boundary {paragraph_handle:b.paragraph_handle.clone(),block_index:b.block_index,normalized_scalar:0};let end=Boundary {normalized_scalar:1,..start.clone()};
    assert!(matches!(replace(&f,&raw,"B",Scope::Selection {index_sha256:[0;32],start:&start,end:&end},all()),Err(E::Search(Search::Scope))));Ok(())
}
#[test]
fn text_style_empty_filters_missing_targets_no_matches_and_noops_are_errors()->TestResult {
    let raw=plain("ABC")?;let f=forms(&raw)?;
    assert!(matches!(f.lower_review_selector_text_style_candidate(&raw,query("A"),Scope::Document,all(),Filter::Declared(Declared::default()),1,Default::default(),Default::default()),Err(E::Search(Search::Filter))));
    assert!(matches!(f.lower_review_selector_text_style_candidate(&raw,query("absent"),Scope::Document,all(),filter(),u32::MAX,Default::default(),Default::default()),Err(E::Search(Search::Definition))));
    assert!(matches!(replace(&f,&raw,"absent",Scope::Document,all()),Err(E::Compile(Compile::NoMatches))));
    assert!(matches!(f.lower_review_selector_text_style_candidate(&raw,query("A"),Scope::Document,all(),filter(),0,Default::default(),Default::default()),Err(E::Compile(Compile::NoChange))));Ok(())
}
#[test]
fn text_style_match_output_writer_and_regex_limits_do_not_return_partial_success()->TestResult {
    let raw=plain("K K")?;let f=forms(&raw)?;
    assert!(f.lower_review_selector_text_style_candidate(&raw,Query {max_results:1,..query("K")},Scope::Document,all(),filter(),1,Default::default(),Default::default()).is_err());
    assert!(f.lower_review_selector_text_style_candidate(&raw,query("K"),Scope::Document,all(),filter(),1,SourceSearchLimits::new(Config {result_bytes:1,..Config::default()})?,Default::default()).is_err());
    assert!(matches!(f.lower_review_selector_text_style_candidate(&raw,query("K"),Scope::Document,all(),filter(),1,Default::default(),WriterLimits::new(WriterLimitConfig {max_output_bytes:1,..Default::default()})?),Err(E::Compile(Compile::Writer))));
    for pattern in["(","^"] {assert!(f.lower_review_selector_text_style_candidate(&raw,Query {mode:Mode::Regex,..query(pattern)},Scope::Document,all(),filter(),1,Default::default(),Default::default()).is_err());}Ok(())
}
#[test]
fn text_style_many_matches_use_one_protection_map_and_preserve_source_privacy()->TestResult {
    let raw=plain(&"K ".repeat(128))?;let original=raw.clone();let f=forms(&raw)?;let out=replace(&f,&raw,"K",Scope::Document,all())?;let bytes=output(&raw,&out)?;
    assert_eq!(out.receipt().matched_occurrences,128);assert_eq!(out.receipt().original_changed_text_elements,1);assert_eq!(values(&bytes)?.iter().filter(|(_,_,s)|*s==Some(1)).count(),128);
    let xml=PreservingXmlDocument::parse(section(&raw)?.as_bytes())?;assert_eq!(out.receipt().observed_protection_element_visits,xml.elements().len()*2);
    assert_eq!(raw,original);assert!(!format!("{out:?}").contains("K "));assert!(!serde_json::to_string(out.receipt())?.contains("K "));Ok(())
}
#[test]
fn text_style_tracked_and_unsupported_text_attributes_do_not_duplicate_identity()->TestResult {
    let raw=plain("ABC")?;let changed=archive::mutate_part(&raw,"Contents/section0.xml",|s|Ok(s.replace("<hp:run charPrIDRef='0'>","<hp:run charPrIDRef='0' charTcId='1'>")))?;let f=forms(&changed)?;
    assert!(matches!(replace(&f,&changed,"B",Scope::Document,all()),Err(E::Compile(Compile::Protection))));
    // Original schema/reader admission or the text compiler must reject identity-bearing unsupported shells.
    let changed=archive::mutate_part(&raw,"Contents/section0.xml",|s|Ok(s.replace("<hp:t charStyleIDRef='0'>","<hp:t charStyleIDRef='0' id='99'>")))?;
    if let Ok(f)=forms(&changed){assert!(replace(&f,&changed,"B",Scope::Document,all()).is_err());}Ok(())
}

fn id_result(raw:&[u8],profile:hwpx_package::IdRuleProfile)->Result<hwpx_package::IdIndex,Box<dyn Error>> {
    let mut reader=BoundedZipReader::open(Cursor::new(raw),Default::default())?;let graph=hwpx_package::PackageGraph::build(&mut reader,Default::default())?;
    Ok(hwpx_package::IdIndex::build(&mut reader,&graph,profile,Default::default())?)
}
#[test]
fn text_style_v9_resolves_exact_original_character_domain_and_old_profiles_stay_closed()->TestResult {
    use hwpx_package::{IdRuleProfile as P,IdIndexError,IdIssueKind};
    let raw=plain("ABC")?;let f=forms(&raw)?;
    for profile in[P::hwpml_2011_shape_v6(),P::hwpml_2011_caption_owner_v8(),P::hwpml_2016_ooxml_chart_v7()] {
        let error=id_result(&raw,profile).expect_err("old profile must reject text-style reference");
        let e=error.downcast_ref::<IdIndexError>().ok_or("typed ID error")?;
        assert!(e.validation().ok_or("report")?.issues().iter().any(|i|i.kind()==IdIssueKind::UnknownIdLikeAttribute));
    }
    let index=id_result(&raw,P::hwpml_2011_text_style_v9())?;assert_eq!(index.profile_version(),"hwpml-2011-text-style-static/v9");
    let out=replace(&f,&raw,"B",Scope::Document,all())?;id_result(&output(&raw,&out)?,P::hwpml_2011_text_style_v9())?;Ok(())
}
#[test]
fn text_style_v9_dangling_and_malformed_target_ids_are_not_ignored()->TestResult {
    use hwpx_package::{IdRuleProfile as P,IdIndexError,IdIssueKind};
    for(value,kind)in[("99",IdIssueKind::DanglingReference),("bogus",IdIssueKind::MalformedValue),("4294967295",IdIssueKind::DanglingReference)] {
        let raw=archive::mutate_part(&plain("A")?,"Contents/section0.xml",|s|Ok(s.replace("charStyleIDRef='0'",&format!("charStyleIDRef='{value}'"))))?;
        let error=id_result(&raw,P::hwpml_2011_text_style_v9()).expect_err("invalid text target");let e=error.downcast_ref::<IdIndexError>().ok_or("ID error")?;
        assert!(e.validation().ok_or("report")?.issues().iter().any(|i|i.kind()==kind));
    }Ok(())
}
#[test]
fn text_style_v9_does_not_admit_wrong_element_or_namespaced_attributes()->TestResult {
    use hwpx_package::{IdRuleProfile as P,IdIndexError,IdIssueKind};
    for body in["<hp:p id='1'><hp:run charStyleIDRef='0'><hp:t>A</hp:t></hp:run></hp:p>",
        "<hp:p id='1' xmlns:x='urn:foreign'><hp:run><hp:t x:charStyleIDRef='0'>A</hp:t></hp:run></hp:p>",
        "<hp:p id='1' charStyleIDRef='0'><hp:run><hp:t>A</hp:t></hp:run></hp:p>"] {
        let raw=fixture::package(body)?;let error=id_result(&raw,P::hwpml_2011_text_style_v9()).expect_err("wrong site/namespace");let e=error.downcast_ref::<IdIndexError>().ok_or("ID error")?;
        assert!(e.validation().ok_or("report")?.issues().iter().any(|i|i.kind()==IdIssueKind::UnknownIdLikeAttribute));
    }Ok(())
}
#[test]
fn text_style_v9_foreign_elements_remain_opaque_not_character_references()->TestResult {
    use hwpx_package::IdRuleProfile as P;
    let raw=fixture::package("<hp:p id='1' xmlns:x='urn:foreign'><hp:run><hp:t>A</hp:t><x:t charStyleIDRef='99'>PRIVATE</x:t></hp:run></hp:p>")?;
    let index=id_result(&raw,P::hwpml_2011_text_style_v9())?;
    assert!(!index.references().iter().any(|r|r.location().part().as_str()=="Contents/section0.xml"&&r.expected_kind()==hwpx_package::IdKind::CharacterProperties));Ok(())
}
#[test]
fn text_style_v9_duplicate_definitions_and_unknown_ids_still_reject()->TestResult {
    use hwpx_package::{IdRuleProfile as P,IdIndexError,IdIssueKind};
    let raw=plain("A")?;let duplicated=archive::mutate_part(&raw,"Contents/header.xml",|s|Ok(s.replacen("<hh:charPr id=\"1\"","<hh:charPr id=\"0\"",1)))?;
    let error=id_result(&duplicated,P::hwpml_2011_text_style_v9()).expect_err("duplicate declaration");let e=error.downcast_ref::<IdIndexError>().ok_or("ID error")?;
    assert!(e.validation().ok_or("report")?.issues().iter().any(|i|i.kind()==IdIssueKind::DuplicateDeclaration));
    let unknown=archive::mutate_part(&raw,"Contents/section0.xml",|s|Ok(s.replace("charStyleIDRef='0'","charStyleIDRef='0' unknownIDRef='1'")))?;
    assert!(id_result(&unknown,P::hwpml_2011_text_style_v9()).is_err());Ok(())
}
