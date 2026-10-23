use hwpx_package::{BoundedZipReader,PackageLimits,PreservingXmlDocument,WriterLimits,WriterLimitConfig,XmlTokenKind,
    document_import::{ImportedSourcePackage,forms::ImportedDocumentForms,search::{SourceSearchLimits,SourceSearchLimitConfig as Config,
        selector::{SourceIndexScopeSelector as Scope,SourceIndexBoundary as Boundary},reviews::SourceReviewTextPolicy as Policy,
        replacement::{SourceLiteralReplacementError as E,SourceReplacementRunPolicy as Run,
            atoms::unicode::{SourceUnicodeNormalizationForm as Form,SourceUnicodeNormalizationCandidate as Candidate}}}}};
use domain_ir::DocumentId;
use sha2::{Digest as _,Sha256};
use std::{error::Error,io::Cursor};
use unicode_normalization::UnicodeNormalization as _;
#[allow(dead_code)] #[path="support/search_definition_fixture.rs"] mod fixture;
#[allow(dead_code)] #[path="support/review_scope_fixture.rs"] mod review;
#[allow(dead_code)] #[path="support/document_import_review_assembly_fixture.rs"] mod assembly;
#[allow(dead_code)] #[path="support/review_cell_output_fixture.rs"] mod table;
type TestResult=Result<(),Box<dyn Error>>;
fn forms(raw:&[u8])->Result<ImportedDocumentForms,Box<dyn Error>> {Ok(ImportedDocumentForms::import(ImportedSourcePackage::import(raw,
    DocumentId::parse("unicode-source")?,Sha256::digest(raw).into(),Default::default())?)?)}
fn para(id:u32,text:&str)->String {format!("<hp:p id='{id}'><hp:run charPrIDRef='0'><hp:t charStyleIDRef='0'>{text}</hp:t></hp:run></hp:p>")}
fn all()->Policy{Policy {include_hidden_explanations:true,include_memo_bodies:true}}
fn norm(f:&ImportedDocumentForms,raw:&[u8],scope:Scope<'_>,policy:Policy,form:Form)->Result<Candidate,E>{
    f.lower_review_selector_unicode_candidate(raw,scope,policy,form,Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default())}
fn section(raw:&[u8])->Result<String,Box<dyn Error>> {let mut r=BoundedZipReader::open(Cursor::new(raw),PackageLimits::default())?;
    let i=r.entries().iter().position(|e|e.path.as_str()=="Contents/section0.xml").ok_or("section")?;Ok(String::from_utf8(r.read_entry(i)?)?)}
fn output(raw:&[u8],c:&Candidate)->Result<Vec<u8>,Box<dyn Error>> {let bytes=c.with_verified_bytes(<[u8]>::to_vec)?;
    let mut a=BoundedZipReader::open(Cursor::new(raw),PackageLimits::default())?;let mut b=BoundedZipReader::open(Cursor::new(&bytes),PackageLimits::default())?;
    assert_eq!(a.entries().len(),b.entries().len());for i in 0..a.entries().len(){let path=a.entries()[i].path.clone();if path.as_str()=="Contents/section0.xml"{continue;}
        let j=b.entries().iter().position(|e|e.path==path).ok_or("part")?;assert_eq!(a.read_entry(i)?,b.read_entry(j)?);}
    let r=c.receipt();assert!(r.exact_original_selection_verified&&r.unchanged_components_keep_original_placement&&r.original_controls_and_all_reference_shells_preserved
        &&r.independent_normalization_oracle_verified&&r.output_text_spans_and_outside_slots_verified);
    assert_eq!(r.unicode_version,unicode_normalization::UNICODE_VERSION);assert!(!r.full_contract_native_service_or_execution_authority);Ok(bytes)}
fn exact(raw:&[u8],c:&Candidate,old:&str,new:&str)->TestResult{let bytes=output(raw,c)?;assert_eq!(section(&bytes)?,section(raw)?.replace(old,new));Ok(())}
fn oracle(text:&str,form:Form)->String {match form {Form::Nfc=>text.nfc().collect(),Form::Nfd=>text.nfd().collect(),Form::Nfkc=>text.nfkc().collect(),Form::Nfkd=>text.nfkd().collect()}}
fn decoded(raw:&[u8])->Result<String,Box<dyn Error>> {let s=section(raw)?;let xml=PreservingXmlDocument::parse(s.as_bytes())?;let mut out=String::new();
    for t in xml.tokens(){if matches!(t.kind(),XmlTokenKind::Text|XmlTokenKind::Whitespace|XmlTokenKind::Reference)
        &&t.element_index().is_some_and(|i|xml.elements()[i].name().local_name()=="t") {let p=t.span();out.push_str(&quick_xml::escape::unescape(&s[p.start()..p.end()])?);}}
    Ok(out)}
#[test]
fn unicode_four_explicit_forms_transform_original_not_only_nfc_index()->TestResult {
    let text="a\u{300}각①ﬃＡℍ\u{a0}";let raw=fixture::package(&para(1,text))?;let f=forms(&raw)?;
    for form in[Form::Nfc,Form::Nfd,Form::Nfkc,Form::Nfkd]{let c=norm(&f,&raw,Scope::Document,all(),form)?;let bytes=output(&raw,&c)?;
        assert_eq!(decoded(&bytes)?,oracle(text,form));assert!(matches!(norm(&forms(&bytes)?,&bytes,Scope::Document,all(),form),Err(E::NoChange)));}
    Ok(())
}
#[test]
fn unicode_cross_run_hangul_changes_only_composition_component_and_retains_shells()->TestResult {
    let body="<hp:p id='1'><hp:run charPrIDRef='0'><hp:t charStyleIDRef='0'>Xᄀ</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t charStyleIDRef='1'>ᅡ</hp:t></hp:run><hp:run charPrIDRef='0'><hp:t>ᆨY</hp:t></hp:run></hp:p>";
    let raw=fixture::package(body)?;let f=forms(&raw)?;let c=norm(&f,&raw,Scope::Document,all(),Form::Nfc)?;
    exact(&raw,&c,body,&body.replace('ᄀ',"각").replace(['ᅡ','ᆨ'],""))?;assert_eq!(c.receipt().changed_components,1);assert_eq!(c.receipt().changed_scalar_ranges,3);Ok(())
}
#[test]
fn unicode_adjacent_text_elements_compose_without_moving_unchanged_suffix_style()->TestResult {
    let body="<hp:p id='1'><hp:run charPrIDRef='1'><hp:t charStyleIDRef='0'>A e</hp:t><hp:t charStyleIDRef='1'>́Z</hp:t></hp:run></hp:p>";
    let raw=fixture::package(body)?;let f=forms(&raw)?;let c=norm(&f,&raw,Scope::Document,all(),Form::Nfc)?;
    exact(&raw,&c,body,&body.replace("A e</hp:t>","A é</hp:t>").replace(">́Z<",">Z<"))?;Ok(())
}
#[test]
fn unicode_nfd_reordering_keeps_unchanged_base_in_its_own_run()->TestResult {
    let body="<hp:p id='1'><hp:run charPrIDRef='1'><hp:t>a</hp:t></hp:run><hp:run charPrIDRef='0'><hp:t>̕</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>̀Z</hp:t></hp:run></hp:p>";
    let raw=fixture::package(body)?;let f=forms(&raw)?;let c=norm(&f,&raw,Scope::Document,all(),Form::Nfd)?;
    exact(&raw,&c,body,&body.replace(">̕<",">̀̕<").replace(">̀Z<",">Z<"))?;assert_eq!(c.receipt().changes.len(),2);Ok(())
}
#[test]
fn unicode_nfc_reordering_composition_closure_covers_intervening_original_marks()->TestResult {
    let text="a\u{315}\u{300}Z";let raw=fixture::package(&para(1,text))?;let f=forms(&raw)?;let c=norm(&f,&raw,Scope::Document,all(),Form::Nfc)?;
    exact(&raw,&c,text,"à\u{315}Z")?;assert_eq!(c.receipt().changed_components,1);Ok(())
}
#[test]
fn unicode_unchanged_entities_and_non_bmp_scalars_remain_byte_exact()->TestResult {
    let text="&#x1F600;&#38;a&#x300;Z&#x26;TAIL";let raw=fixture::package(&para(1,text))?;let f=forms(&raw)?;
    let c=norm(&f,&raw,Scope::Document,all(),Form::Nfc)?;exact(&raw,&c,text,"&#x1F600;&#38;àZ&#x26;TAIL")?;assert_eq!(c.receipt().changed_scalar_ranges,1);Ok(())
}
#[test]
fn unicode_tabs_and_paired_linebreaks_are_immutable_normalization_barriers()->TestResult {
    let text="a<hp:tab width='1' leader='0' type='0'> </hp:tab>̀à<hp:lineBreak> </hp:lineBreak>ᄀ<hp:lineBreak/>ᅡ";
    let raw=fixture::package(&para(1,text))?;let f=forms(&raw)?;let c=norm(&f,&raw,Scope::Document,all(),Form::Nfc)?;
    exact(&raw,&c,text,&text.replace("̀à<","̀à<"))?;assert_eq!(c.receipt().changes[0].preserved_controls,3);Ok(())
}
#[test]
fn unicode_bookmark_control_splits_blocks_and_is_not_crossed()->TestResult {
    let body="<hp:p id='1'><hp:run><hp:t>a</hp:t><hp:ctrl><hp:bookmark name='KEEP'/></hp:ctrl><hp:t>̀à</hp:t></hp:run></hp:p>";
    let raw=fixture::package(body)?;let f=forms(&raw)?;let c=norm(&f,&raw,Scope::Document,all(),Form::Nfc)?;
    exact(&raw,&c,">̀à<",">̀à<")?;assert_eq!(c.receipt().normalized_text_groups,2);Ok(())
}
#[test]
fn unicode_paragraph_boundaries_never_compose_across_paragraphs()->TestResult {
    let body=format!("{}{}",para(1,"a"),para(2,"̀à"));let raw=fixture::package(&body)?;let f=forms(&raw)?;
    let c=norm(&f,&raw,Scope::Document,all(),Form::Nfc)?;exact(&raw,&c,">̀à<",">̀à<")?;Ok(())
}
#[test]
fn unicode_all_four_selectors_keep_the_original_scope_and_never_widen()->TestResult {
    let body=format!("{}{}",para(1,"àZ"),para(2,"éZ"));let raw=fixture::package(&body)?;let f=forms(&raw)?;
    let i=f.source_review_scope_index(&raw,Default::default())?;let inv=i.scope_inventory()?;let b=&inv.inventory.blocks[0];
    let ids=[inv.inventory.nodes.iter().find(|n|n.source_handle==b.paragraph_handle).ok_or("node")?.node_id.clone()];
    let start=Boundary {paragraph_handle:b.paragraph_handle.clone(),block_index:b.block_index,normalized_scalar:0};let end=Boundary {normalized_scalar:1,..start.clone()};
    for(scope,n)in[(Scope::Document,2),(Scope::Section(&inv.inventory.section_ids),2),(Scope::NodeSet(&ids),1),
        (Scope::Selection {index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},1)] {
        let c=norm(&f,&raw,scope,all(),Form::Nfc)?;assert_eq!(c.receipt().changed_components,n);
        let s=section(&output(&raw,&c)?)?;assert!(s.contains("àZ"));assert_eq!(s.contains("éZ"),n==1);
    }Ok(())
}
#[test]
fn unicode_selection_does_not_pull_combining_context_from_outside_selection()->TestResult {
    let raw=fixture::package(&para(1,"à̕Z"))?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;let inv=i.scope_inventory()?;let b=&inv.inventory.blocks[0];
    let start=Boundary {paragraph_handle:b.paragraph_handle.clone(),block_index:b.block_index,normalized_scalar:0};let end=Boundary {normalized_scalar:1,..start.clone()};
    assert!(matches!(norm(&f,&raw,Scope::Selection {index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},all(),Form::Nfc),Err(E::Selection)));
    Ok(())
}
#[test]
fn unicode_partial_inverse_of_one_expanding_original_scalar_is_rejected()->TestResult {
    let raw=fixture::package(&para(1,"&#x344;à"))?;let f=forms(&raw)?;let inv=f.source_review_scope_index(&raw,Default::default())?.scope_inventory()?;let b=&inv.inventory.blocks[0];
    let start=Boundary {paragraph_handle:b.paragraph_handle.clone(),block_index:b.block_index,normalized_scalar:0};let end=Boundary {normalized_scalar:1,..start.clone()};
    assert!(matches!(norm(&f,&raw,Scope::Selection {index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},all(),Form::Nfd),Err(E::Search(hwpx_package::document_import::search::SourceSearchError::Scope))));
    Ok(())
}
#[test]
fn unicode_hidden_and_memo_policies_are_applied_before_edit_limits_and_keep_cache()->TestResult {
    let body=format!("{}{}",para(30,"à"),review::body().replace("K K","à"));let raw=fixture::package(&body)?;let f=forms(&raw)?;
    let inv=f.source_review_scope_index(&raw,Default::default())?.scope_inventory()?;
    let ids:Vec<_>=inv.inventory.blocks.iter().zip(&inv.block_regions).filter(|(b,r)|b.block_index==0||**r!=hwpx_package::document_import::search::reviews::SourceTextRegion::BodyAndNotes)
        .map(|(b,_)|inv.inventory.nodes.iter().find(|n|n.source_handle==b.paragraph_handle).map(|n|n.node_id.clone()).ok_or("node")).collect::<Result<_,_>>()?;
    for(h,m,n)in[(false,false,1),(true,false,2),(false,true,2),(true,true,3)]{let p=Policy {include_hidden_explanations:h,include_memo_bodies:m};
        let c=norm(&f,&raw,Scope::NodeSet(&ids),p,Form::Nfc)?;let s=section(&output(&raw,&c)?)?;assert_eq!(s.matches('à').count(),n);assert!(s.contains("CACHE FROZEN"));
        assert_eq!(c.receipt().changed_components,n);assert_eq!(c.receipt().excluded_hidden_paragraphs,usize::from(!h));assert_eq!(c.receipt().excluded_memo_paragraphs,usize::from(!m));
    }Ok(())
}
#[test]
fn unicode_observed_table_protection_is_checked_even_for_noop_text()->TestResult {
    let body=format!("<hp:p id='1'><hp:run>{}</hp:run></hp:p>",table::table(300).replace("lock='0'","lock='1'"));
    let raw=fixture::package(&body)?;let f=forms(&raw)?;assert!(matches!(norm(&f,&raw,Scope::Document,all(),Form::Nfc),Err(E::Protection)));Ok(())
}
#[test]
fn unicode_ancestor_tracking_is_checked_before_noop_elimination()->TestResult {
    for body in[para(1,"ABC").replace("<hp:p id='1'","<hp:p paraTcId='0' id='1'"),para(1,"ABC").replace("<hp:run ","<hp:run charTcId='0' ")] {
        let raw=fixture::package(&body)?;let f=forms(&raw)?;assert!(matches!(norm(&f,&raw,Scope::Document,all(),Form::Nfc),Err(E::Protection)));
    }Ok(())
}
#[test]
fn unicode_field_cache_is_rejected_even_when_text_is_already_normalized()->TestResult {
    let raw=fixture::package(&review::body())?;let f=forms(&raw)?;let inv=f.source_review_scope_index(&raw,Default::default())?.scope_inventory()?;
    // Select the actual cache's original paragraph, not the permitted MEMO payload subList.
    let b=&inv.inventory.blocks.iter().find(|b|b.normalized_scalars==12).ok_or("cache block")?;
    let start=Boundary {paragraph_handle:b.paragraph_handle.clone(),block_index:b.block_index,normalized_scalar:0};let end=Boundary {normalized_scalar:12,..start.clone()};
    assert!(matches!(norm(&f,&raw,Scope::Selection {index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},all(),Form::Nfc),Err(E::FieldContent)));Ok(())
}
#[test]
fn unicode_foreign_original_proof_and_stale_selection_are_rejected()->TestResult {
    let raw=fixture::package(&para(1,"à"))?;let f=forms(&raw)?;let other=forms(&raw)?;let proof=f.reconstruct_source_for_verification(&raw)?;
    assert!(matches!(proof.lower_review_selector_unicode_candidate(&other,Scope::Document,all(),Form::Nfc,Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default()),Err(E::Source)));
    let inv=f.source_review_scope_index(&raw,Default::default())?.scope_inventory()?;let b=&inv.inventory.blocks[0];let start=Boundary {paragraph_handle:b.paragraph_handle.clone(),block_index:0,normalized_scalar:0};let end=Boundary {normalized_scalar:1,..start.clone()};
    assert!(norm(&f,&raw,Scope::Selection {index_sha256:[0;32],start:&start,end:&end},all(),Form::Nfc).is_err());
    let changed=fixture::package(&para(1,"é"))?;assert!(matches!(norm(&f,&changed,Scope::Document,all(),Form::Nfc),Err(E::Source)));Ok(())
}
#[test]
fn unicode_limits_reject_components_expansion_receipt_and_writer_without_partial_output()->TestResult {
    let raw=fixture::package(&para(1,"à à ﬃ"))?;let f=forms(&raw)?;
    for config in[Config {matches:1,..Default::default()},Config {result_bytes:1,..Default::default()},Config {decomposed_scalars:2,..Default::default()}] {
        assert!(f.lower_review_selector_unicode_candidate(&raw,Scope::Document,all(),Form::Nfkc,Run::FirstOriginalRunRetainAllRuns,SourceSearchLimits::new(config)?,Default::default()).is_err());}
    let expanded=fixture::package(&para(1,"ﬃ"))?;let ef=forms(&expanded)?;
    assert!(matches!(ef.lower_review_selector_unicode_candidate(&expanded,Scope::Document,all(),Form::Nfkd,Run::FirstOriginalRunRetainAllRuns,
        SourceSearchLimits::new(Config {decomposed_scalars:2,..Default::default()})?,Default::default()),Err(E::Limit)));
    assert!(matches!(f.lower_review_selector_unicode_candidate(&raw,Scope::Document,all(),Form::Nfc,Run::FirstOriginalRunRetainAllRuns,Default::default(),
        WriterLimits::new(WriterLimitConfig {max_output_bytes:1,..Default::default()})?),Err(E::Writer)));Ok(())
}
#[test]
fn unicode_form_policy_scope_and_source_are_bound_without_plaintext_receipt()->TestResult {
    let raw=fixture::package(&para(1,"PRIVATE-MARKER à ﬃ"))?;let f=forms(&raw)?;let a=norm(&f,&raw,Scope::Document,all(),Form::Nfc)?;
    let b=norm(&f,&raw,Scope::Document,all(),Form::Nfkc)?;let d=norm(&f,&raw,Scope::Document,Policy {include_hidden_explanations:false,include_memo_bodies:false},Form::Nfc)?;
    assert_ne!(a.receipt().request_sha256,b.receipt().request_sha256);assert_ne!(a.receipt().request_sha256,d.receipt().request_sha256);
    assert!(!serde_json::to_string(a.receipt())?.contains("PRIVATE-MARKER"));assert!(!format!("{a:?}").contains("PRIVATE-MARKER"));assert_eq!(a.receipt().source_package_sha256,<[u8;32]>::from(Sha256::digest(&raw)));Ok(())
}
#[test]
fn unicode_many_components_share_one_part_guard_and_one_span_plan()->TestResult {
    let raw=fixture::package(&para(1,&"à ".repeat(128)))?;let original=raw.clone();let f=forms(&raw)?;let c=norm(&f,&raw,Scope::Document,all(),Form::Nfc)?;
    assert_eq!(decoded(&output(&raw,&c)?)?,"à ".repeat(128));assert_eq!(c.receipt().changed_components,128);assert_eq!(c.receipt().changes.len(),1);
    assert_eq!(c.receipt().observed_protection_parts,1);let xml=PreservingXmlDocument::parse(section(&raw)?.as_bytes())?;
    assert_eq!(c.receipt().observed_protection_element_visits,xml.elements().len()*3);assert_eq!(raw,original);Ok(())
}
#[test]
fn unicode_empty_selection_and_already_normalized_text_have_no_candidate()->TestResult {
    let raw=fixture::package(&para(1,"ABC"))?;let f=forms(&raw)?;assert!(matches!(norm(&f,&raw,Scope::Document,all(),Form::Nfc),Err(E::NoChange)));
    let inv=f.source_review_scope_index(&raw,Default::default())?.scope_inventory()?;let b=&inv.inventory.blocks[0];let at=Boundary {paragraph_handle:b.paragraph_handle.clone(),block_index:0,normalized_scalar:1};
    assert!(matches!(norm(&f,&raw,Scope::Selection {index_sha256:inv.inventory.index.index_sha256,start:&at,end:&at},all(),Form::Nfd),Err(E::NoChange)));Ok(())
}
#[test]
fn unicode_namespace_aliases_and_bookmark_ids_keep_their_exact_original_shells()->TestResult {
    let body="<hp:p id='1' xmlns:z='http://www.hancom.co.kr/hwpml/2011/paragraph'><z:run charPrIDRef='1'><z:t charStyleIDRef='0'>à</z:t><z:ctrl><z:bookmark name='KEEP'/></z:ctrl><z:t>TAIL</z:t></z:run></hp:p>";
    let raw=fixture::package(body)?;let f=forms(&raw)?;let c=norm(&f,&raw,Scope::Document,all(),Form::Nfc)?;exact(&raw,&c,"à","à")?;Ok(())
}
#[test]
fn unicode_bounded_multiscript_corpus_matches_independent_library_for_all_forms()->TestResult {
    let seed="각각 àa\u{315}\u{300} ΩΩ ÅÅ ①ﬃＡℍ\u{a0} Ḋ\u{323} 𝓗 ﾊﾟ 😀 \u{344} ";let text=seed.repeat(4);
    let raw=fixture::package(&para(1,&text))?;let f=forms(&raw)?;
    for form in[Form::Nfc,Form::Nfd,Form::Nfkc,Form::Nfkd]{let c=norm(&f,&raw,Scope::Document,all(),form)?;assert_eq!(decoded(&output(&raw,&c)?)?,oracle(&text,form));}
    Ok(())
}
#[test]
fn unicode_selected_component_preserves_outside_decomposed_text_and_entity_spelling()->TestResult {
    let raw=fixture::package(&para(1,"à &#x65;&#x301;"))?;let f=forms(&raw)?;let inv=f.source_review_scope_index(&raw,Default::default())?.scope_inventory()?;let b=&inv.inventory.blocks[0];
    let start=Boundary {paragraph_handle:b.paragraph_handle.clone(),block_index:0,normalized_scalar:0};let end=Boundary {normalized_scalar:1,..start.clone()};
    let c=norm(&f,&raw,Scope::Selection {index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},all(),Form::Nfc)?;
    exact(&raw,&c,"à &#x65;&#x301;","à &#x65;&#x301;")?;Ok(())
}
