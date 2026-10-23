//! Real common dispatcher/compiler, with exact header resources and actual source owners.
use super::*;
use sha2::{Digest as _,Sha256};
use hwpx_agent_cli::form_product_request::stored_operations::{StoredProductRequest as Dispatch,PreparedStoredProductOperation as Operation,
    search_mutations::{SearchMutationLimits as Limits,SearchMutationReceiptRef as Receipt,SEARCH_MUTATION_REQUEST_SCHEMAS as SCHEMAS},
    compiled_search::PreparedCompiledSearchMutation as Compiled};
use hwpx_package::document_import::search::replacement::atoms::styles::fonts::inventory::{SourceFontEditInventory as Inventory,SourceFontEditKind as Kind};
fn compile(p:&Provider<'_>,v:&Value)->Result<Compiled,Box<dyn Error>>{Ok(Dispatch::prepare_compiled_search_json(p,&wire(v)?,Limits::standard()?,4)?)}
fn arg<'a>(op:&'a domain_ir::CompiledOperation,key:&str)->Result<&'a str,Box<dyn Error>>{
    let domain_ir::CanonicalArgumentValue::Text(value)=op.arguments().get(key).ok_or("missing locked argument")?.value()else{return Err("argument kind".into())};Ok(value)
}
fn check(out:&Compiled,inventory:&Inventory)->R{
    let ops=out.compiled().operations();assert_eq!(ops.len(),inventory.body_splices().count());assert_eq!(out.receipt().source_edit_operations,ops.len());assert!(!ops.is_empty());
    assert_eq!(out.receipt().request_schema,SCHEMA);assert_eq!(out.receipt().capability_id,"search.replace_fonts");assert!(!out.receipt().execution_authority);
    assert_eq!(out.receipt().compiled_plan_sha256,<[u8;32]>::from(Sha256::digest(serde_json::to_vec(out.compiled())?)));
    let headers:Vec<_>=inventory.header_effects().collect();assert_eq!(headers.len(),2);
    for(i,(op,body))in ops.iter().zip(inventory.body_splices()).enumerate(){
        assert_eq!(op.arguments().len(),15);assert_eq!(op.capability_id().as_str(),"search.replace_fonts");assert_eq!(arg(op,"source_edit_index")?,i.to_string());
        assert_eq!(arg(op,"source_edit_domain")?,"final_font_body_splices_with_header_resources");assert_eq!(arg(op,"edit_inventory_sha256")?,hex::encode(inventory.canonical_sha256()));
        assert_eq!(serde_json::from_str::<Value>(arg(op,"source_anchor_json")?)?,serde_json::to_value(body.source_anchor())?);
        assert_eq!(serde_json::from_str::<Value>(arg(op,"source_font_header_count_effect_json")?)?,serde_json::to_value(headers[0])?);
        assert_eq!(serde_json::from_str::<Value>(arg(op,"source_font_header_append_effect_json")?)?,serde_json::to_value(headers[1])?);
        assert_eq!(arg(op,"source_font_resource_binding_profile")?,"exact_header_effects_once_per_inventory_with_actual_body_owner/v1");
        assert!(arg(op,"source_font_header_count_effect_json")?.len()<=2048&&arg(op,"source_font_header_append_effect_json")?.len()<=2048);
    }Ok(())
}
fn inventory_for(p:&Provider<'_>,v:&Value)->Result<Inventory,Box<dyn Error>>{Ok(prepare!(p,v)?.with_verified_edit_inventory(p,5,Clone::clone)?)}
#[test]
fn common_dispatch_font_receipt_and_output_match_standalone_and_keep_route_denied()->R{
    assert_eq!(SCHEMAS.len(),23);assert_eq!(SCHEMAS[18],SCHEMA);assert_eq!(SCHEMAS[19],hwpx_agent_cli::form_product_request::stored_literal_replacement::fonts::options::FONT_OPTIONS_REQUEST_SCHEMA);assert_eq!(SCHEMAS[20],hwpx_agent_cli::form_product_request::stored_literal_replacement::named_styles::NAMED_STYLE_PRODUCT_REQUEST_SCHEMA);assert_eq!(SCHEMAS.iter().copied().collect::<BTreeSet<_>>().len(),23);
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=request(&s,&bytes)?;let direct=prepare!(&p,&v)?;
    let out=Dispatch::prepare_json(&p,&wire(&v)?,None,4)?;let Operation::SearchMutation(candidate)=&out else{return Err("search kind".into())};
    let Receipt::Font(receipt)=candidate.receipt()else{return Err("font kind".into())};assert_eq!(receipt,direct.receipt());candidate.verify(&p,5)?;
    assert_eq!(out.with_verified_bytes(&p,None,5,ContentDigest::of)?,direct.with_verified_bytes(&p,5,ContentDigest::of)?);assert!(out.require_current_product_route(&p,None,5).is_err());
    assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
}
#[test]
fn compiled_font_plan_has_one_actual_body_owner_and_two_locked_header_resources()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=request(&s,&bytes)?;let out=compile(&p,&v)?;let inv=inventory_for(&p,&v)?;check(&out,&inv)?;
    let source=p.import_actual_forms(s.head,4)?;assert_eq!(out.compiled().operations()[0].target().node_id(),&source.imported().graph().sections()[0].body.children[0].common().node_id);
    out.verify(&p,5)?;assert!(out.require_current_product_route(&p,5).is_err());assert_eq!(out.receipt().output_package_sha256,*out.with_verified_bytes(&p,5,ContentDigest::of)?.as_bytes());Ok(())
}
#[test]
fn selected_second_paragraph_uses_its_owner_not_first_paragraph_or_header_surrogate()->R{
    let bytes=package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>ONE</hp:t></hp:run></hp:p><hp:p id='2'><hp:run charPrIDRef='0'><hp:t>TWO</hp:t></hp:run></hp:p>")?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=request(&s,&bytes)?;let source=p.import_actual_forms(s.head,4)?;let second=&source.imported().graph().sections()[0].body.children[1].common().node_id;
    v["selector"]["scope"]=json!("node_set");v["selector"]["range"]=json!({"node_ids":[second.as_str()]});let out=compile(&p,&v)?;check(&out,&inventory_for(&p,&v)?)?;
    assert_eq!(out.compiled().operations().len(),1);assert_eq!(out.compiled().operations()[0].target().node_id(),second);Ok(())
}
#[test]
fn two_body_operations_share_one_inventory_resource_group_without_duplicate_header_operations()->R{
    let bytes=package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>ONE</hp:t></hp:run></hp:p><hp:p id='2'><hp:run charPrIDRef='0'><hp:t>TWO</hp:t></hp:run></hp:p>")?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=request(&s,&bytes)?;let out=compile(&p,&v)?;let inv=inventory_for(&p,&v)?;check(&out,&inv)?;
    assert_eq!(out.compiled().operations().len(),2);assert_eq!(inv.edits().len(),4);assert_eq!(out.receipt().structural_owner_nodes,2);
    let ops=out.compiled().operations();assert_eq!(arg(&ops[0],"source_font_header_append_effect_json")?,arg(&ops[1],"source_font_header_append_effect_json")?);Ok(())
}
#[test]
fn separate_original_properties_bind_exact_two_clone_append_not_one_resource_per_match()->R{
    let bytes=package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>A</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>B</hp:t></hp:run></hp:p>")?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=request(&s,&bytes)?;v["operation"]["query"]=json!(".+");v["operation"]["regex"]=json!(true);
    let out=compile(&p,&v)?;let inv=inventory_for(&p,&v)?;check(&out,&inv)?;assert!(inv.header_effects().any(|e|e.kind()==Kind::AppendCharacterProperties{appended_items:2}));assert_eq!(out.receipt().structural_owner_nodes,1);Ok(())
}
#[test]
fn text_axis_body_domain_and_resources_keep_actual_text_anchor()->R{
    let bytes=package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t charStyleIDRef='1'>ABCD</hp:t></hp:run></hp:p>")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    let mut v=request(&s,&bytes)?;v["operation"]["axis"]=json!("text_style");v["operation"]["query"]=json!(name(&bytes,1)?);let out=compile(&p,&v)?;let inv=inventory_for(&p,&v)?;check(&out,&inv)?;assert!(inv.body_splices().all(|e|e.kind()==Kind::TextSubtree));Ok(())
}
#[test]
fn partial_nfc_selection_compiles_final_splice_not_normalized_scalar_as_fake_node()->R{
    let bytes=raw("X각Y")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=request(&s,&bytes)?;let scope=inventory(&p,&v)?;
    v["selector"]["scope"]=json!("selection");v["selector"]["range"]=selection(&scope,1,2)?;let out=compile(&p,&v)?;let inv=inventory_for(&p,&v)?;check(&out,&inv)?;assert_eq!(out.compiled().operations().len(),1);Ok(())
}
#[test]
fn plan_key_and_request_digests_bind_compiled_plan_without_text_or_font_disclosure()->R{
    let bytes=raw("PRIVATE-COMPILED-TEXT")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes)?;let first=compile(&p,&good)?;
    for(key,value)in [("plan_id",json!("font-plan-2")),("idempotency_key",json!("font-key-2"))]{let mut v=good.clone();v[key]=value;let other=compile(&p,&v)?;
        assert_ne!(first.receipt().compiled_plan_sha256,other.receipt().compiled_plan_sha256);assert_eq!(first.receipt().output_package_sha256,other.receipt().output_package_sha256);}
    for text in [serde_json::to_string(first.compiled())?,format!("{first:?}{:?}",first.receipt())]{assert!(!text.contains("PRIVATE-")&&!text.contains("<hp:")&&!text.contains("<hh:"));}Ok(())
}
#[test]
fn caller_resource_arguments_and_unknown_schemas_reject_before_source_reads()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();
    for key in ["source_font_header_count_effect_json","source_font_header_append_effect_json","source_font_resource_binding_profile","approved"]{let mut v=good.clone();v["operation"][key]=json!("injected");assert!(compile(&p,&v).is_err());}
    let mut v=good;v["schema_version"]=json!("unqualified-font-schema");assert!(compile(&p,&v).is_err());assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn common_compiler_preserves_server_search_and_writer_limits()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=request(&s,&bytes)?;
    let mut limits=Limits::standard()?;limits.search=SourceSearchLimits::new(Config{matches:1,..Default::default()})?;assert!(Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,limits,4).is_err());
    let mut limits=Limits::standard()?;limits.writer=WriterLimits::new(WriterLimitConfig{max_output_bytes:1})?;assert!(Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,limits,4).is_err());compile(&p,&v)?;Ok(())
}
#[test]
fn held_compiled_plan_requires_current_write_and_same_provider_document()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=request(&s,&bytes)?;let out=compile(&p,&v)?;let reader=s.provider()?;let called=Cell::new(false);
    assert!(compile(&reader,&v).is_err());assert!(out.verify(&reader,5).is_err());assert!(out.with_verified_bytes(&reader,5,|_|called.set(true)).is_err());
    let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("foreign-font-plan")?)?;
    assert!(out.with_verified_bytes(&other,5,|_|called.set(true)).is_err());assert!(!called.get());Ok(())
}
#[test]
fn revoked_acl_blocks_compiled_verification_and_delivery_until_current_regrant()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let out=compile(&p,&request(&s,&bytes)?)?;s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;
    let called=Cell::new(false);assert!(out.verify(&p,6).is_err());assert!(out.with_verified_bytes(&p,6,|_|called.set(true)).is_err());assert!(!called.get());
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;out.verify(&p,8)?;Ok(())
}
#[test]
fn quarantine_and_aead_tamper_block_held_compiled_plan_consumers()->R{
    for tamper in [false,true]{let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let out=compile(&p,&request(&s,&bytes)?)?;
        if tamper{s.blobs.tamper.store(true,Ordering::SeqCst);}else{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("FONT_COMPILED_TEST")?,5)?;}
        let called=Cell::new(false);assert!(out.verify(&p,6).is_err());assert!(out.with_verified_bytes(&p,6,|_|called.set(true)).is_err());assert!(!called.get());}Ok(())
}
fn race_compiled(stage:usize)->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=request(&s,&bytes)?;let out=compile(&p,&v)?;
    let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,
        ContentDigest::of(b"font-compiled-race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation fixture"),ContentDigest::of(b"transaction fixture"))?;
    let repo=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
    let bound=StoredFormProvider::bind(&s.artifacts,&repo,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
    match stage{0=>{Dispatch::prepare_compiled_search_json(&bound,&wire(&v)?,Limits::standard()?,5)?;},1=>{out.verify(&bound,5)?;},_=>{out.with_verified_bytes(&bound,5,|_|())?;}}
    let calls=repo.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);repo.repository().calls.store(0,Ordering::SeqCst);repo.repository().trigger.store(calls,Ordering::SeqCst);let called=Cell::new(false);
    match stage{0=>assert!(Dispatch::prepare_compiled_search_json(&bound,&wire(&v)?,Limits::standard()?,6).is_err()),1=>assert!(out.verify(&bound,6).is_err()),_=>assert!(out.with_verified_bytes(&bound,6,|_|called.set(true)).is_err())}
    assert!(!called.get());assert_eq!(repo.repository().calls.load(Ordering::SeqCst),calls);Ok(())
}
#[test]fn compiler_final_head_race_rejects_after_plan_build()->R{race_compiled(0)}
#[test]fn compiled_verification_final_head_race_rejects()->R{race_compiled(1)}
#[test]fn compiled_delivery_final_head_race_rejects_before_consumer()->R{race_compiled(2)}
fn legacy(mode:usize)->R{
    let bytes=if mode==3{package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>B</hp:t></hp:run></hp:p><hp:p id='2'><hp:run charPrIDRef='0'><hp:t>A</hp:t></hp:run></hp:p>")?}else{raw("AB")?};
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=request(&s,&bytes)?;
    let(suffix,operation)=match mode{
        0=>("width-conversion",json!({"kind":"convert_width_matches","query":"AB","regex":false,"case_sensitive":true,"whole_word":false,"max_matches":100,"mode":"fullwidth","width_policy":"unicode17_width_pairs_with_kana_pairs","run_policy":"first_original_run_retain_all_runs","review_policy":policy()})),
        1=>("character-style-replacement",json!({"kind":"replace_character_property","query":"B","regex":false,"case_sensitive":true,"whole_word":false,"max_replacements":100,"style_filter":{"kind":"declared","filter":{"run_character_property":0}},"replacement":{"axis":"run_character_property","declaration_id":1},"review_policy":policy()})),
        2=>("regex-replacement",json!({"kind":"replace_regex","query":"B","replacement":"C","regex":true,"case_sensitive":true,"whole_word":false,"max_replacements":100,"run_policy":"first_original_run_retain_all_runs","review_policy":policy()})),
        _=>("paragraph-sort",json!({"kind":"sort_sibling_paragraphs","sort_spec":{"direction":"ascending","comparison":"nfc_unicode_scalar_lexicographic","max_comparison_bytes":1048576},"review_policy":policy()})),
    };v["schema_version"]=json!(format!("hwpx-agent.product-{suffix}-request/v1"));v["operation"]=operation;let out=compile(&p,&v)?;out.verify(&p,5)?;
    assert!(out.compiled().operations().iter().all(|op|op.arguments().len()==12&&!op.arguments().contains_key("source_font_resource_binding_profile")));out.with_verified_bytes(&p,5,|_|())?;assert!(out.require_current_product_route(&p,5).is_err());Ok(())
}
#[test]fn legacy_width_keeps_original_twelve_argument_compiler_path()->R{legacy(0)}
#[test]fn legacy_style_splices_keep_original_twelve_argument_compiler_path()->R{legacy(1)}
#[test]fn legacy_regex_keeps_original_twelve_argument_compiler_path()->R{legacy(2)}
#[test]fn legacy_permutation_keeps_original_twelve_argument_compiler_path()->R{legacy(3)}
