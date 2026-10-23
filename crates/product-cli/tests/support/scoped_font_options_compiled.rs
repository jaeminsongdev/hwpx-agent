//! Common v2 mutation plans and a physically separate nonmutating preview dispatch.
use super::*;
use sha2::{Digest as _,Sha256};
use hwpx_agent_cli::form_product_request::{stored_literal_replacement::fonts::options::{StoredFontOptionsProductRequest as Options,
    StoredFontOptionsMutationRequest as Mutation,FontOptionsProductError as X,FONT_OPTIONS_REQUEST_SCHEMA as V2},
    stored_operations::{StoredProductRequest as Dispatch,PreparedStoredProductOperation as Operation,StoredProductOperationError as CommonError,
        search_mutations::{SearchMutationLimits as Limits,SearchMutationReceiptRef as Receipt,SEARCH_MUTATION_REQUEST_SCHEMAS as SCHEMAS},
        compiled_search::{PreparedCompiledSearchMutation as Compiled,CompiledSearchError}}};
use hwpx_package::document_import::search::replacement::atoms::styles::fonts::inventory::SourceFontEditInventory as Inventory;
fn v2(s:&StoredFixture,bytes:&[u8],preview:bool)->Result<Value,Box<dyn Error>>{let mut v=request(s,bytes)?;v["schema_version"]=json!(V2);v["operation"]["preview_only"]=json!(preview);v["operation"]["style_filter"]=json!({"kind":"declared","filter":{"run_character_property":0}});Ok(v)}
fn common(p:&Provider<'_>,v:&Value)->Result<Operation,Box<dyn Error>>{Ok(Dispatch::prepare_json(p,&wire(v)?,None,4)?)}
fn compile(p:&Provider<'_>,v:&Value)->Result<Compiled,Box<dyn Error>>{Ok(Dispatch::prepare_compiled_search_json(p,&wire(v)?,Limits::standard()?,4)?)}
fn arg<'a>(op:&'a domain_ir::CompiledOperation,key:&str)->Result<&'a str,Box<dyn Error>>{let domain_ir::CanonicalArgumentValue::Text(v)=op.arguments().get(key).ok_or("locked argument")?.value()else{return Err("text argument".into())};Ok(v)}
fn check(p:&Provider<'_>,v:&Value,out:&Compiled)->R{
    let direct=Mutation::prepare_json(p,&wire(v)?,Default::default(),Default::default(),4)?;let inv:Inventory=direct.with_verified_edit_inventory(p,5,Clone::clone)?;
    assert_eq!(out.receipt().request_schema,V2);assert_eq!(out.receipt().source_edit_operations,inv.body_splices().count());assert!(!out.receipt().execution_authority);
    assert_eq!(out.receipt().mutation_receipt_sha256,<[u8;32]>::from(Sha256::digest(serde_json::to_vec(&direct.receipt().stored.output)?)));
    assert_eq!(out.receipt().compiled_plan_sha256,<[u8;32]>::from(Sha256::digest(serde_json::to_vec(out.compiled())?)));
    let headers:Vec<_>=inv.header_effects().collect();assert_eq!(headers.len(),2);
    for(op,body)in out.compiled().operations().iter().zip(inv.body_splices()){
        assert_eq!(op.arguments().len(),15);assert_eq!(arg(op,"request_schema")?,V2);assert_eq!(arg(op,"source_edit_domain")?,"final_font_body_splices_with_header_resources");
        assert_eq!(arg(op,"edit_inventory_sha256")?,hex::encode(inv.canonical_sha256()));assert_eq!(arg(op,"mutation_receipt_sha256")?,hex::encode(out.receipt().mutation_receipt_sha256));
        assert_eq!(serde_json::from_str::<Value>(arg(op,"source_anchor_json")?)?,serde_json::to_value(body.source_anchor())?);
        for(key,e)in [("source_font_header_count_effect_json",headers[0]),("source_font_header_append_effect_json",headers[1])]{assert_eq!(serde_json::from_str::<Value>(arg(op,key)?)?,serde_json::to_value(e)?);}
        assert_eq!(arg(op,"source_font_resource_binding_profile")?,"exact_header_effects_once_per_inventory_with_actual_body_owner/v1");
    }Ok(())
}
#[test]
fn appended_v2_family_preserves_all_nineteen_original_schema_positions()->R{
    use hwpx_agent_cli::form_product_request::stored_literal_replacement as l;
    let old=[l::LITERAL_REPLACEMENT_PRODUCT_REQUEST_SCHEMA,l::atoms::LITERAL_TEXT_ATOM_PRODUCT_REQUEST_SCHEMA,l::review::REVIEW_LITERAL_PRODUCT_REQUEST_SCHEMA,
        l::selector::SELECTOR_LITERAL_PRODUCT_REQUEST_SCHEMA,l::regex::REGEX_REPLACEMENT_PRODUCT_REQUEST_SCHEMA,l::regex::insertions::REGEX_INSERTION_PRODUCT_REQUEST_SCHEMA,
        l::styles::CHARACTER_STYLE_PRODUCT_REQUEST_SCHEMA,l::text_styles::TEXT_STYLE_PRODUCT_REQUEST_SCHEMA,l::paragraph_styles::PARAGRAPH_STYLE_PRODUCT_REQUEST_SCHEMA,
        l::unicode::UNICODE_PRODUCT_REQUEST_SCHEMA,l::unicode::matches::UNICODE_MATCH_PRODUCT_REQUEST_SCHEMA,l::case::CASE_PRODUCT_REQUEST_SCHEMA,
        l::width::WIDTH_PRODUCT_REQUEST_SCHEMA,l::whitespace::WHITESPACE_PRODUCT_REQUEST_SCHEMA,l::controls::CONTROL_PRODUCT_REQUEST_SCHEMA,
        l::number_controls::NUMBER_CONTROL_PRODUCT_REQUEST_SCHEMA,l::sort::PARAGRAPH_SORT_PRODUCT_REQUEST_SCHEMA,l::sort_groups::PARAGRAPH_SORT_GROUPS_PRODUCT_REQUEST_SCHEMA,SCHEMA];
    assert_eq!(&SCHEMAS[..19],&old);assert_eq!(SCHEMAS[19],V2);assert_eq!(SCHEMAS[20],hwpx_agent_cli::form_product_request::stored_literal_replacement::named_styles::NAMED_STYLE_PRODUCT_REQUEST_SCHEMA);assert_eq!(SCHEMAS.len(),23);assert_eq!(SCHEMAS.iter().copied().collect::<BTreeSet<_>>().len(),23);Ok(())
}
#[test]
fn common_mutation_owns_original_v2_receipt_and_output_not_a_reprepared_source()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=v2(&s,&bytes,false)?;
    let direct=Options::prepare_json(&p,&wire(&v)?,Default::default(),Default::default(),4)?;let out=common(&p,&v)?;
    let Operation::SearchMutation(c)=&out else{return Err("mutation kind".into())};let Receipt::FontOptions(r)=c.receipt()else{return Err("font v2 family".into())};
    assert_eq!(r,direct.receipt());c.verify(&p,5)?;assert_eq!(out.with_verified_bytes(&p,None,5,ContentDigest::of)?,direct.with_verified_bytes(&p,5,ContentDigest::of)?);Ok(())
}
#[test]
fn common_preview_is_separate_variant_json_only_and_matches_standalone_metadata()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=v2(&s,&bytes,true)?;let out=common(&p,&v)?;
    let Operation::SearchPreview(preview)=&out else{return Err("preview kind".into())};assert!(preview.receipt().preview_only);assert!(!preview.receipt().stored.candidate_output_retained);
    let direct=Options::prepare_json(&p,&wire(&v)?,Default::default(),Default::default(),4)?;assert_eq!(preview.verify(&p,5)?,direct.verify(&p,5)?);
    assert_eq!(out.with_verified_preview_json(&p,None,5,<[u8]>::to_vec)?,direct.with_verified_json(&p,5,<[u8]>::to_vec)?);
    let called=Cell::new(false);assert!(matches!(out.with_verified_bytes(&p,None,5,|_|called.set(true)),Err(CommonError::PreviewOnly)));assert!(!called.get());Ok(())
}
#[test]
fn compiler_and_mutation_only_request_reject_preview_before_artifact_reads()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=v2(&s,&bytes,true)?;let before=s.metadata.audit_events()?.len();
    assert!(matches!(Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4),Err(CompiledSearchError::Kind)));
    assert!(matches!(Mutation::prepare_json(&p,&wire(&v)?,Default::default(),Default::default(),4),Err(X::PreviewOnly)));assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn mutation_cannot_use_preview_json_delivery_or_claim_a_nonmutating_result()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let out=common(&p,&v2(&s,&bytes,false)?)?;let called=Cell::new(false);
    assert!(matches!(out.with_verified_preview_json(&p,None,5,|_|called.set(true)),Err(CommonError::PreviewKind)));assert!(!called.get());Ok(())
}
#[test]
fn v2_plan_binds_exact_header_resources_to_actual_selected_second_owner()->R{
    let bytes=package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>ONE</hp:t></hp:run></hp:p><hp:p id='2'><hp:run charPrIDRef='0'><hp:t>TWO</hp:t></hp:run></hp:p>")?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let source=p.import_actual_forms(s.head,4)?;let second=&source.imported().graph().sections()[0].body.children[1].common().node_id;
    let mut v=v2(&s,&bytes,false)?;v["selector"]["scope"]=json!("node_set");v["selector"]["range"]=json!({"node_ids":[second.as_str()]});let out=compile(&p,&v)?;check(&p,&v,&out)?;
    assert_eq!(out.compiled().operations().len(),1);assert_eq!(out.compiled().operations()[0].target().node_id(),second);Ok(())
}
#[test]
fn two_body_owners_share_exact_once_per_inventory_header_resource_group()->R{
    let bytes=package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>ONE</hp:t></hp:run></hp:p><hp:p id='2'><hp:run charPrIDRef='0'><hp:t>TWO</hp:t></hp:run></hp:p>")?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=v2(&s,&bytes,false)?;let out=compile(&p,&v)?;check(&p,&v,&out)?;
    assert_eq!(out.compiled().operations().len(),2);assert_eq!(out.receipt().structural_owner_nodes,2);let ops=out.compiled().operations();assert_eq!(arg(&ops[0],"source_font_header_append_effect_json")?,arg(&ops[1],"source_font_header_append_effect_json")?);Ok(())
}
#[test]
fn definition_filter_compiles_only_matching_style_with_original_nonselected_run()->R{
    let bytes=package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>A</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>B</hp:t></hp:run></hp:p>")?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=v2(&s,&bytes,false)?;v["operation"]["query"]=json!(name(&bytes,1)?);
    v["operation"]["style_filter"]=json!({"kind":"definition","filter":{"character_source":"run_property","bold":true}});let out=compile(&p,&v)?;check(&p,&v,&out)?;
    let values=out.with_verified_bytes(&p,5,refs)??;assert_eq!(values[0].1,0);assert_ne!(values[1].1,1);Ok(())
}
#[test]
fn text_axis_and_nfc_window_use_actual_text_owner_not_normalized_positions_as_nodes()->R{
    let bytes=package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t charStyleIDRef='1'>X각Y</hp:t></hp:run></hp:p>")?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=v2(&s,&bytes,false)?;let inv=inventory(&p,&request(&s,&bytes)?)?;
    v["operation"]["axis"]=json!("text_style");v["operation"]["query"]=json!(name(&bytes,1)?);v["operation"]["style_filter"]=json!({"kind":"declared","filter":{"text_character_style":1}});
    v["selector"]["scope"]=json!("selection");v["selector"]["range"]=selection(&inv,1,2)?;let out=compile(&p,&v)?;check(&p,&v,&out)?;
    let values=out.with_verified_bytes(&p,5,refs)??;assert!(values.iter().all(|v|v.1==0));assert_eq!(values.iter().map(|v|v.0.as_str()).collect::<String>(),"X각Y");Ok(())
}
#[test]
fn full_filter_receipt_changes_plan_even_when_v1_source_receipt_output_and_inventory_match()->R{
    let bytes=package("<hp:p id='1' paraPrIDRef='0'><hp:run charPrIDRef='0'><hp:t>ABC</hp:t></hp:run></hp:p>")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    let mut v=v2(&s,&bytes,false)?;let first=compile(&p,&v)?;v["operation"]["style_filter"]=json!({"kind":"declared","filter":{"paragraph_property":0}});let second=compile(&p,&v)?;
    assert_eq!(first.receipt().output_package_sha256,second.receipt().output_package_sha256);assert_eq!(first.receipt().edit_inventory_sha256,second.receipt().edit_inventory_sha256);
    assert_ne!(first.receipt().mutation_receipt_sha256,second.receipt().mutation_receipt_sha256);assert_ne!(first.receipt().compiled_plan_sha256,second.receipt().compiled_plan_sha256);check(&p,&v,&second)?;Ok(())
}
#[test]
fn absent_filter_can_compile_but_plan_remains_distinct_from_v1_schema()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=v2(&s,&bytes,false)?;v["operation"].as_object_mut().ok_or("op")?.remove("style_filter");
    let out=compile(&p,&v)?;let old=Dispatch::prepare_compiled_search_json(&p,&wire(&request(&s,&bytes)?)?,Limits::standard()?,4)?;
    assert_eq!(out.receipt().output_package_sha256,old.receipt().output_package_sha256);assert_ne!(out.receipt().compiled_plan_sha256,old.receipt().compiled_plan_sha256);check(&p,&v,&out)?;Ok(())
}
#[test]
fn malformed_preview_flags_unknown_filter_and_caller_header_effects_reject_before_reads()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let before=s.metadata.audit_events()?.len();
    for preview in [false,true]{let good=v2(&s,&bytes,preview)?;for(key,value)in [("preview_only",json!("false")),("style_filter",json!({})),("source_font_header_append_effect_json",json!("injected"))]{
        let mut v=good.clone();v["operation"][key]=value;assert!(Dispatch::prepare_json(&p,&wire(&v)?,None,4).is_err());}}
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn common_limits_apply_to_preview_and_mutation_compiler_without_partial_success()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    for preview in [false,true]{let v=v2(&s,&bytes,preview)?;for writer_limit in [false,true]{let mut limits=Limits::standard()?;
        if writer_limit{limits.writer=WriterLimits::new(WriterLimitConfig{max_output_bytes:1})?;}else{limits.search=SourceSearchLimits::new(Config{matches:1,..Default::default()})?;}
        assert!(Dispatch::prepare_json_with_search_limits(&p,&wire(&v)?,None,limits,4).is_err());if !preview{assert!(Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,limits,4).is_err());}}}Ok(())
}
#[test]
fn preview_and_compiled_plan_require_current_write_access_and_same_provider()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let preview=common(&p,&v2(&s,&bytes,true)?)?;let compiled=compile(&p,&v2(&s,&bytes,false)?)?;
    let reader=s.provider()?;let called=Cell::new(false);assert!(preview.with_verified_preview_json(&reader,None,5,|_|called.set(true)).is_err());assert!(compiled.with_verified_bytes(&reader,5,|_|called.set(true)).is_err());
    let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("foreign-font-options")?)?;
    assert!(preview.with_verified_preview_json(&other,None,5,|_|called.set(true)).is_err());assert!(compiled.with_verified_bytes(&other,5,|_|called.set(true)).is_err());assert!(!called.get());Ok(())
}
#[test]
fn acl_revocation_blocks_common_preview_and_compiled_output_until_regrant()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let preview=common(&p,&v2(&s,&bytes,true)?)?;let compiled=compile(&p,&v2(&s,&bytes,false)?)?;
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;let called=Cell::new(false);assert!(preview.with_verified_preview_json(&p,None,6,|_|called.set(true)).is_err());
    assert!(compiled.verify(&p,6).is_err());assert!(compiled.with_verified_bytes(&p,6,|_|called.set(true)).is_err());assert!(!called.get());
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;compiled.verify(&p,8)?;preview.with_verified_preview_json(&p,None,8,|_|())?;Ok(())
}
#[test]
fn quarantine_and_aead_tamper_block_both_retained_common_result_modes()->R{
    for tamper in [false,true]{let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let preview=common(&p,&v2(&s,&bytes,true)?)?;let compiled=compile(&p,&v2(&s,&bytes,false)?)?;
        if tamper{s.blobs.tamper.store(true,Ordering::SeqCst);}else{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("COMMON_FONT_OPTIONS_TEST")?,5)?;}
        let called=Cell::new(false);assert!(preview.with_verified_preview_json(&p,None,6,|_|called.set(true)).is_err());assert!(compiled.with_verified_bytes(&p,6,|_|called.set(true)).is_err());assert!(!called.get());}Ok(())
}
#[test]
fn source_sha_and_head_generation_are_required_in_both_common_modes()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    for preview in [false,true]{for(key,value)in [("expected_source_package_sha256",json!("0".repeat(64))),("expected_head_generation",json!(s.head.generation()+1))]{let mut v=v2(&s,&bytes,preview)?;v[key]=value;assert!(Dispatch::prepare_json(&p,&wire(&v)?,None,4).is_err());}}Ok(())
}
#[test]
fn common_preview_and_plan_keep_original_head_ingest_count_and_route_denials()->R{
    let bytes=raw("PRIVATE-SOURCE")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let preview=common(&p,&v2(&s,&bytes,true)?)?;let compiled=compile(&p,&v2(&s,&bytes,false)?)?;
    assert!(preview.require_current_product_route(&p,None,5).is_err());assert!(compiled.require_current_product_route(&p,5).is_err());assert!(!compiled.receipt().execution_authority);
    for text in [serde_json::to_string(compiled.compiled())?,format!("{compiled:?}{preview:?}")]{assert!(!text.contains("PRIVATE-")&&!text.contains("<hp:")&&!text.contains("<hh:"));}
    assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
}
fn race(stage:usize)->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let pv=v2(&s,&bytes,true)?;let mv=v2(&s,&bytes,false)?;let preview=common(&p,&pv)?;let compiled=compile(&p,&mv)?;
    let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,
        ContentDigest::of(b"common-font-options-race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation fixture"),ContentDigest::of(b"transaction fixture"))?;
    let repo=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
    let bound=StoredFormProvider::bind(&s.artifacts,&repo,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
    match stage{0=>{Dispatch::prepare_json(&bound,&wire(&pv)?,None,5)?;},1=>{preview.with_verified_preview_json(&bound,None,5,|_|())?;},
        2=>{Dispatch::prepare_compiled_search_json(&bound,&wire(&mv)?,Limits::standard()?,5)?;},3=>{compiled.verify(&bound,5)?;},_=>{compiled.with_verified_bytes(&bound,5,|_|())?;}}
    let calls=repo.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);repo.repository().calls.store(0,Ordering::SeqCst);repo.repository().trigger.store(calls,Ordering::SeqCst);let called=Cell::new(false);
    match stage{0=>assert!(Dispatch::prepare_json(&bound,&wire(&pv)?,None,6).is_err()),1=>assert!(preview.with_verified_preview_json(&bound,None,6,|_|called.set(true)).is_err()),
        2=>assert!(Dispatch::prepare_compiled_search_json(&bound,&wire(&mv)?,Limits::standard()?,6).is_err()),3=>assert!(compiled.verify(&bound,6).is_err()),_=>assert!(compiled.with_verified_bytes(&bound,6,|_|called.set(true)).is_err())}
    assert!(!called.get());assert_eq!(repo.repository().calls.load(Ordering::SeqCst),calls);Ok(())
}
#[test]fn common_preview_preparation_final_head_race_rejects()->R{race(0)}
#[test]fn common_preview_delivery_final_head_race_blocks_consumer()->R{race(1)}
#[test]fn compiled_v2_post_compiler_final_head_race_rejects()->R{race(2)}
#[test]fn compiled_v2_retained_verification_final_head_race_rejects()->R{race(3)}
#[test]fn compiled_v2_output_delivery_final_head_race_blocks_consumer()->R{race(4)}
