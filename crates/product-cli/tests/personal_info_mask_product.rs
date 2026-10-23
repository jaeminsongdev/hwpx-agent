//! Current service and strict selected-mask product with synthetic data/keys/scanner. No Native/operational DB.
use std::{error::Error,cell::Cell,sync::atomic::AtomicUsize};
use domain_ir::DocumentId;
use serde_json::{json,Value};
use revision_service as rev;
use hwpx_agent_cli::form_product_request::stored_literal_replacement::personal_info::{StoredPersonalInfoMaskProductRequest as Product,PersonalInfoMaskProductError as E,
    PERSONAL_INFO_MASK_PRODUCT_SCHEMA as SCHEMA};
use hwpx_agent_cli::form_stored_provider::actual_import::literal_search_output::personal_info::StoredPersonalInfoMaskError as Stored;
use hwpx_package::{WriterLimits,WriterLimitConfig,document_import::search::{SourceSearchLimits,SourceSearchLimitConfig as Config,selector::SourceIndexScopeSelector as Scope,
    reviews::SourceReviewTextPolicy as Policy,replacement::{SourceLiteralReplacementError as Core,atoms::personal_info::SourcePersonalInfoMaskPolicy as Mask}}};
include!("support/stored_source_fixture.rs");
#[path="../../hwpx-package/tests/support/search_definition_fixture.rs"]#[allow(dead_code)]mod definition;
#[path="../../hwpx-package/tests/support/document_import_catalog_fixture.rs"]#[allow(dead_code)]mod archive;
#[path="../../hwpx-package/tests/support/review_scope_fixture.rs"]#[allow(dead_code)]mod review;
type R=Result<(),Box<dyn Error>>;
fn policy()->Policy{Policy{include_hidden_explanations:false,include_memo_bodies:false}}
fn para(id:u32,text:&str)->String{format!("<hp:p id='{id}' styleIDRef='0' paraPrIDRef='0'><hp:run charPrIDRef='0'><hp:t>{text}</hp:t></hp:run></hp:p>")}
fn raw(text:&str)->Result<Vec<u8>,Box<dyn Error>>{definition::package(&para(1,text))}
fn wire(v:&Value)->Result<Vec<u8>,serde_json::Error>{serde_json::to_vec(v)}
fn request(s:&StoredFixture,bytes:&[u8],preview:bool)->Result<Value,Box<dyn Error>>{let revision=s.head.revision_id().ok_or("head")?.public_id();
    Ok(json!({"schema_version":SCHEMA,"idempotency_key":"PRIVATE-MASK-KEY","plan_id":"personal-mask-plan","project_id":s.project.public_id(),"document_id":"actual-form-document",
        "base_revision":revision,"expected_head_generation":s.head.generation(),"expected_source_package_sha256":ContentDigest::of(bytes).hex(),"selector":{"revision_id":revision,"scope":"document"},
        "operation":{"kind":"mask_selected_personal_info","mask_policy":"per_original_scalar_preserve_slots","max_changed_components":10000,"review_policy":policy(),"preview_only":preview}}))}
macro_rules! writer{($s:ident,$actor:ident,$p:ident)=>{
    let $actor=RequestContext::new($s.reader.tenant_id(),$s.reader.subject(),[AuthScope::DocumentRead,AuthScope::DocumentWrite]);
    let $p=StoredFormProvider::bind(&$s.artifacts,&$s.revisions,&$actor,&$s.revision_context,$s.project,$s.branch,DocumentId::parse("actual-form-document")?)?;
}}
macro_rules! prepare{($p:expr,$v:expr)=>{Product::prepare_json($p,&wire($v)?,Default::default(),Default::default(),4)}}
fn section(bytes:&[u8])->Result<String,Box<dyn Error>>{Ok(String::from_utf8(archive::read_part(bytes,"Contents/section0.xml")?)?)}
fn inventory(p:&Provider<'_>,v:&Value)->Result<Value,Box<dyn Error>>{
    use hwpx_agent_cli::form_product_request::stored_source_search::selector::review::StoredReviewScopeProductRequest;
    let mut v=v.clone();v["schema_version"]=json!("hwpx-agent.product-source-search-request/v6");v["operation"]=json!({"kind":"scope_inventory"});
    Ok(StoredReviewScopeProductRequest::prepare_json(p,&wire(&v)?,Default::default(),4)?.with_verified_json(p,5,|b|serde_json::from_slice::<Value>(b))??)
}
fn selection(inv:&Value,start:usize,end:usize)->Result<Value,Box<dyn Error>>{let b=&inv["inventory"]["blocks"][0];let sha:[u8;32]=serde_json::from_value(inv["inventory"]["index"]["index_sha256"].clone())?;
    Ok(json!({"coordinate_space":"index_nfc_unicode_scalars","index_sha256":hex::encode(sha),"start":{"paragraph_handle":b["paragraph_handle"],"block_index":b["block_index"],"normalized_scalar":start},
        "end":{"paragraph_handle":b["paragraph_handle"],"block_index":b["block_index"],"normalized_scalar":end}}))}
#[test]
fn borrowed_owned_and_product_share_one_original_mask_receipt_and_verified_output()->R{
    let bytes=raw("A&amp;😀각")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let source=p.import_actual_forms(s.head,4)?;
    let a=source.prepare_personal_info_mask_candidate(&p,Scope::Document,policy(),Mask::PerOriginalScalarPreserveSlots,Default::default(),Default::default(),4)?;
    let b=p.import_actual_forms(s.head,4)?.into_personal_info_mask_candidate(&p,Scope::Document,policy(),Mask::PerOriginalScalarPreserveSlots,Default::default(),Default::default(),4)?;
    let v=request(&s,&bytes,false)?;let out=prepare!(&p,&v)?;drop(v);assert_eq!(a.receipt(),b.receipt());assert_eq!(a.receipt(),&out.receipt().stored);
    assert_eq!(a.with_verified_bytes(&p,5,ContentDigest::of)?,out.with_verified_bytes(&p,5,ContentDigest::of)?);assert!(out.with_verified_bytes(&p,5,section)??.contains(">****<"));
    assert_eq!(out.receipt().capability_id,"search.personal_info_replace_direct");out.verify(&p,5)?;Ok(())
}
#[test]
fn preview_discards_output_never_calls_byte_consumer_and_keeps_same_prediction()->R{
    let bytes=raw("PRIVATE-MARKER")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    let mutation=prepare!(&p,&request(&s,&bytes,false)?)?;let preview=prepare!(&p,&request(&s,&bytes,true)?)?;assert_eq!(mutation.receipt().stored.output,preview.receipt().stored.output);
    assert_ne!(mutation.receipt().canonical_request_sha256,preview.receipt().canonical_request_sha256);assert!(preview.receipt().preview_only&&!preview.receipt().stored.candidate_output_retained);
    let called=Cell::new(false);assert!(matches!(preview.with_verified_bytes(&p,5,|_|called.set(true)),Err(E::PreviewOnly)));assert!(!called.get());
    let meta=preview.with_verified_json(&p,5,|b|serde_json::from_slice::<Value>(b))??;assert_eq!(meta["preview_only"],true);assert_eq!(meta["stored"]["candidate_output_retained"],false);Ok(())
}
#[test]
fn direct_service_preview_has_only_bounded_metadata_and_denies_route()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    let preview=p.import_actual_forms(s.head,4)?.into_personal_info_mask_candidate(&p,Scope::Document,policy(),Mask::ThreeAsterisksPerTextGroup,Default::default(),Default::default(),4)?.into_preview()?;
    assert!(preview.with_verified_metadata(&p,5,|r|r.preview_only&&!r.candidate_output_retained)?);preview.verify(&p,5)?;assert!(matches!(preview.require_current_product_route(&p,5),Err(Stored::RouteUnqualified)));Ok(())
}
#[test]
fn explicit_policies_reach_source_without_implicit_native_mask_length()->R{
    let bytes=raw("LONGER-MARKER")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=request(&s,&bytes,false)?;
    let a=prepare!(&p,&v)?;v["operation"]["mask_policy"]=json!("three_asterisks_per_text_group");let b=prepare!(&p,&v)?;
    assert_ne!(a.receipt().stored.output.output_package_sha256,b.receipt().stored.output.output_package_sha256);assert!(b.with_verified_bytes(&p,5,section)??.contains(">***<"));
    assert!(!b.receipt().stored.output.native_mask_semantics_or_service_execution_qualified);Ok(())
}
#[test]
fn document_section_node_and_exact_selection_never_widen_original_scope()->R{
    let bytes=definition::package(&(para(1,"ABC")+&para(2,"DEF")))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes,false)?;let inv=inventory(&p,&good)?;
    let first=&inv["inventory"]["blocks"][0];let node=inv["inventory"]["nodes"].as_array().ok_or("nodes")?.iter().find(|n|n["source_handle"]==first["paragraph_handle"]).ok_or("node")?;
    for mode in 0..4{let mut v=good.clone();match mode{0=>{},1=>{v["selector"]["scope"]=json!("section");v["selector"]["section_ids"]=inv["inventory"]["section_ids"].clone();},
        2=>{v["selector"]["scope"]=json!("node_set");v["selector"]["range"]=json!({"node_ids":[node["node_id"]]});},_=>{v["selector"]["scope"]=json!("selection");v["selector"]["range"]=selection(&inv,1,2)?;}}
        let out=prepare!(&p,&v)?;let text=out.with_verified_bytes(&p,5,section)??;if mode<2{assert_eq!(text.matches(">***<").count(),2);}else if mode==2{assert!(text.contains(">***<")&&text.contains(">DEF<"));}else{assert!(text.contains(">A*C<")&&text.contains(">DEF<"));}}
    Ok(())
}
#[test]
fn review_policy_masks_payloads_but_never_claims_author_metadata_anonymized()->R{
    let bytes=definition::package(&(para(30,"PLAIN")+&review::body()))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes,false)?;let inv=inventory(&p,&good)?;
    let blocks=inv["inventory"]["blocks"].as_array().ok_or("blocks")?;let regions=inv["block_regions"].as_array().ok_or("regions")?;let nodes=inv["inventory"]["nodes"].as_array().ok_or("nodes")?;
    let ids=blocks.iter().zip(regions).filter(|(b,r)|b["block_index"]==0||**r!=json!("body_and_notes")).map(|(b,_)|nodes.iter().find(|n|n["source_handle"]==b["paragraph_handle"]).map(|n|n["node_id"].clone()).ok_or("node")).collect::<Result<Vec<_>,_>>()?;
    for(h,m,count)in [(false,false,1),(true,false,2),(false,true,2),(true,true,3)]{let mut v=good.clone();v["selector"]["scope"]=json!("node_set");v["selector"]["range"]=json!({"node_ids":ids});
        v["operation"]["review_policy"]=json!({"include_hidden_explanations":h,"include_memo_bodies":m});v["operation"]["mask_policy"]=json!("three_asterisks_per_text_group");let out=prepare!(&p,&v)?;
        let text=out.with_verified_bytes(&p,5,section)??;assert_eq!(text.matches(">***").count(),count);assert!(text.contains("CACHE FROZEN")&&text.contains("PRIVATE-AUTHOR"));assert!(!out.receipt().stored.output.whole_package_personal_data_removed);}Ok(())
}
#[test]
fn root_selector_and_operation_fields_are_required_before_artifact_reads()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes,true)?;let before=s.metadata.audit_events()?.len();
    for key in ["schema_version","idempotency_key","project_id","document_id","base_revision","expected_head_generation","expected_source_package_sha256","plan_id","selector","operation"]{
        let mut v=good.clone();v.as_object_mut().ok_or("root")?.remove(key);assert!(matches!(prepare!(&p,&v),Err(E::Request)));}
    for key in ["kind","mask_policy","max_changed_components","review_policy","preview_only"]{let mut v=good.clone();v["operation"].as_object_mut().ok_or("operation")?.remove(key);assert!(matches!(prepare!(&p,&v),Err(E::Request)));}
    for key in ["scope","revision_id"]{let mut v=good.clone();v["selector"].as_object_mut().ok_or("selector")?.remove(key);assert!(matches!(prepare!(&p,&v),Err(E::Request)));}assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn unsupported_generic_query_filters_approval_and_raw_graph_options_reject_before_reads()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes,true)?;let before=s.metadata.audit_events()?.len();
    for key in ["query","replacement","regex","direction","style_filter","approved","raw_xml","graph","whole_package_sanitized"]{let mut v=good.clone();v["operation"][key]=json!(false);assert!(matches!(prepare!(&p,&v),Err(E::Request)));}
    for key in ["approved","graph","source_path"]{let mut v=good.clone();v[key]=json!({});assert!(matches!(prepare!(&p,&v),Err(E::Request)));}assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn enum_object_forms_nulls_unknown_policies_and_wrong_boolean_types_reject_before_reads()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes,true)?;let before=s.metadata.audit_events()?.len();
    for(key,value)in [("kind",json!({"mask_selected_personal_info":null})),("mask_policy",json!({"per_original_scalar_preserve_slots":null})),("mask_policy",json!("native_default")),
        ("mask_policy",Value::Null),("preview_only",json!("true")),("review_policy",json!([]))]{let mut v=good.clone();v["operation"][key]=value;assert!(matches!(prepare!(&p,&v),Err(E::Request)));}
    let mut v=good;v["selector"]["scope"]=json!({"document":null});assert!(matches!(prepare!(&p,&v),Err(E::Request)));assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn duplicate_escaped_keys_trailing_json_wrong_schema_and_empty_envelope_reject_before_reads()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes,true)?;let text=String::from_utf8(wire(&good)?)?;let before=s.metadata.audit_events()?.len();
    for raw in [text.replace("\"preview_only\":true","\"preview_only\":true,\"preview_\\u006fnly\":false"),format!("{text} {{}}"),"null".into(),"[]".into()]{assert!(matches!(Product::prepare_json(&p,raw.as_bytes(),Default::default(),Default::default(),4),Err(E::Request)));}
    let mut v=good;v["schema_version"]=json!("hwpx-agent.product-personal-info-selection-mask-request/v2");assert!(matches!(prepare!(&p,&v),Err(E::Request)));assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn exact_request_byte_limit_and_one_more_byte_are_distinct()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=request(&s,&bytes,true)?;let mut text=wire(&v)?;text.resize(16*1024,b' ');
    let padded=Product::prepare_json(&p,&text,Default::default(),Default::default(),4)?;let ordinary=prepare!(&p,&v)?;assert_eq!(padded.receipt().canonical_request_sha256,ordinary.receipt().canonical_request_sha256);
    assert_ne!(padded.receipt().raw_request_sha256,ordinary.receipt().raw_request_sha256);text.push(b' ');let before=s.metadata.audit_events()?.len();
    assert!(matches!(Product::prepare_json(&p,&text,Default::default(),Default::default(),4),Err(E::Limit)));assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn malformed_selector_shape_revision_and_digest_are_rejected_before_reads()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes,true)?;let before=s.metadata.audit_events()?.len();
    for mode in 0..5{let mut v=good.clone();match mode{0=>v["selector"]["range"]=Value::Null,1=>v["selector"]["section_ids"]=json!([]),
        2=>v["selector"]["revision_id"]=json!(rev::RevisionId::generate().public_id()),3=>v["expected_source_package_sha256"]=json!("F".repeat(64)),_=>v["expected_head_generation"]=json!(0)}assert!(matches!(prepare!(&p,&v),Err(E::Request)));}
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn source_sha_revision_generation_and_stale_index_cannot_select_another_original()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes,false)?;
    for(key,value)in [("expected_source_package_sha256",json!("0".repeat(64))),("expected_head_generation",json!(s.head.generation()+1))]{let mut v=good.clone();v[key]=value;assert!(prepare!(&p,&v).is_err());}
    let inv=inventory(&p,&good)?;let mut v=good;v["selector"]["scope"]=json!("selection");v["selector"]["range"]=selection(&inv,0,1)?;v["selector"]["range"]["index_sha256"]=json!("0".repeat(64));assert!(prepare!(&p,&v).is_err());Ok(())
}
#[test]
fn document_write_is_required_for_service_product_and_retained_modes()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let reader=s.provider()?;let source=reader.import_actual_forms(s.head,4)?;
    assert!(matches!(source.prepare_personal_info_mask_candidate(&reader,Scope::Document,policy(),Mask::PerOriginalScalarPreserveSlots,Default::default(),Default::default(),4),Err(Stored::Permission)));
    for preview in [false,true]{let v=request(&s,&bytes,preview)?;assert!(prepare!(&reader,&v).is_err());let out=prepare!(&p,&v)?;let called=Cell::new(false);assert!(out.verify(&reader,5).is_err());assert!(out.with_verified_json(&reader,5,|_|called.set(true)).is_err());assert!(!called.get());}Ok(())
}
#[test]
fn foreign_request_project_and_document_do_not_read_artifacts()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes,true)?;let before=s.metadata.audit_events()?.len();
    for(key,value)in [("project_id",json!("prj_70000000000000000000000000000002")),("document_id",json!("foreign-document"))]{let mut v=good.clone();v[key]=value;assert!(prepare!(&p,&v).is_err());}assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn five_foreign_provider_scopes_cannot_reuse_either_retained_result_mode()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);for preview in [false,true]{let out=prepare!(&p,&request(&s,&bytes,preview)?)?;let called=Cell::new(false);
        for mode in 0..5{let tenant=if mode==4{TenantId::new(Uuid::from_u128(998))?}else{s.reader.tenant_id()};let subject=if mode==3{SubjectDigest::from_authenticated_subject("foreign-mask")?}else{s.reader.subject()};
            let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);let context=rev::RevisionRequestContext::new(tenant,subject);let project=if mode==2{rev::ProjectId::parse("prj_70000000000000000000000000000002")?}else{s.project};let branch=if mode==1{rev::BranchId::parse("brn_70000000000000000000000000000002")?}else{s.branch};
            let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&context,project,branch,DocumentId::parse(if mode==0{"foreign-document"}else{"actual-form-document"})?)?;
            assert!(out.verify(&other,5).is_err());assert!(out.with_verified_json(&other,5,|_|called.set(true)).is_err());}assert!(!called.get());}Ok(())
}
#[test]
fn acl_revocation_blocks_new_and_retained_modes_and_regrant_rechecks()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let a=prepare!(&p,&request(&s,&bytes,false)?)?;let b=prepare!(&p,&request(&s,&bytes,true)?)?;
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;let called=Cell::new(false);for out in [&a,&b]{assert!(out.verify(&p,6).is_err());assert!(out.with_verified_json(&p,6,|_|called.set(true)).is_err());}
    assert!(prepare!(&p,&request(&s,&bytes,true)?).is_err());assert!(!called.get());s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;a.verify(&p,8)?;b.verify(&p,8)?;Ok(())
}
#[test]
fn quarantine_blocks_new_and_retained_modes_without_callbacks()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let a=prepare!(&p,&request(&s,&bytes,false)?)?;let b=prepare!(&p,&request(&s,&bytes,true)?)?;
    s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("PERSONAL_MASK_TEST")?,5)?;let called=Cell::new(false);for out in [&a,&b]{assert!(out.verify(&p,6).is_err());assert!(out.with_verified_json(&p,6,|_|called.set(true)).is_err());}
    assert!(prepare!(&p,&request(&s,&bytes,true)?).is_err());assert!(!called.get());Ok(())
}
#[test]
fn changed_ciphertext_blocks_new_and_retained_modes_without_callbacks()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let a=prepare!(&p,&request(&s,&bytes,false)?)?;let b=prepare!(&p,&request(&s,&bytes,true)?)?;
    s.blobs.tamper.store(true,Ordering::SeqCst);let called=Cell::new(false);for out in [&a,&b]{assert!(out.verify(&p,6).is_err());assert!(out.with_verified_json(&p,6,|_|called.set(true)).is_err());}assert!(!called.get());assert!(prepare!(&p,&request(&s,&bytes,true)?).is_err());Ok(())
}
#[test]
fn server_component_writer_and_full_metadata_limits_apply_to_both_modes()->R{
    let bytes=definition::package(&(para(1,"A")+&para(2,"B")))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    for preview in [false,true]{let mut v=request(&s,&bytes,preview)?;v["operation"]["max_changed_components"]=json!(1);assert!(matches!(prepare!(&p,&v),Err(E::Stored(Stored::Output(Core::Limit)))));
        v["operation"]["max_changed_components"]=json!(2);let limits=SourceSearchLimits::new(Config{matches:1,..Default::default()})?;assert!(matches!(Product::prepare_json(&p,&wire(&v)?,limits,Default::default(),4),Err(E::Stored(Stored::Output(Core::Limit)))));
        assert!(matches!(Product::prepare_json(&p,&wire(&v)?,Default::default(),WriterLimits::new(WriterLimitConfig{max_output_bytes:1})?,4),Err(E::Stored(Stored::Output(Core::Writer)))));}Ok(())
}
#[test]
fn exact_entire_metadata_envelope_and_one_byte_less_are_enforced_in_both_modes()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);for preview in [false,true]{let v=request(&s,&bytes,preview)?;let out=prepare!(&p,&v)?;let n=out.with_verified_json(&p,5,<[u8]>::len)?;
        let limits=SourceSearchLimits::new(Config{result_bytes:n,..Default::default()})?;let exact=Product::prepare_json(&p,&wire(&v)?,limits,Default::default(),4)?;assert_eq!(exact.with_verified_json(&p,5,<[u8]>::len)?,n);
        let limits=SourceSearchLimits::new(Config{result_bytes:n-1,..Default::default()})?;assert!(matches!(Product::prepare_json(&p,&wire(&v)?,limits,Default::default(),4),Err(E::Limit)));}Ok(())
}
#[test]
fn cached_fields_tracking_and_already_masked_noops_never_become_preview_success()->R{
    let field=para(1,"A</hp:t><hp:ctrl><hp:fieldBegin id='17' type='DATE'/></hp:ctrl><hp:t>***</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='17'/></hp:ctrl><hp:t>TAIL");
    for body in [field,para(1,"***").replace("<hp:p ","<hp:p paraTcId='0' ")]{let bytes=definition::package(&body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);for preview in [false,true]{assert!(prepare!(&p,&request(&s,&bytes,preview)?).is_err());}}
    let bytes=raw("***")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);assert!(matches!(prepare!(&p,&request(&s,&bytes,true)?),Err(E::Stored(Stored::Output(Core::NoChange)))));Ok(())
}
#[test]
fn request_key_plan_policy_and_mode_bind_hashes_without_disclosing_private_body()->R{
    let bytes=raw("PRIVATE-MASK-BODY")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes,true)?;let first=prepare!(&p,&good)?;
    for(key,value)in [("idempotency_key",json!("PRIVATE-SECOND-KEY")),("plan_id",json!("second-mask-plan"))]{let mut v=good.clone();v[key]=value;let next=prepare!(&p,&v)?;assert_ne!(first.receipt().canonical_request_sha256,next.receipt().canonical_request_sha256);assert_eq!(first.receipt().stored.output,next.receipt().stored.output);}
    for text in [format!("{first:?}{:?}",first.receipt()),first.with_verified_json(&p,5,|b|String::from_utf8_lossy(b).into_owned())?]{assert!(!text.contains("PRIVATE-")&&!text.contains("source_span_sha256")&&!text.contains("pieces"));}Ok(())
}
#[test]
fn both_modes_preserve_original_head_and_artifacts_and_never_claim_execution()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);for preview in [false,true]{let out=prepare!(&p,&request(&s,&bytes,preview)?)?;out.verify(&p,5)?;
        assert!(!out.receipt().idempotency_key_claimed&&!out.receipt().full_personal_info_native_cas_execution_publication_authority&&!out.receipt().stored.output.whole_package_personal_data_removed);
        assert!(matches!(out.require_current_product_route(&p,5),Err(E::RouteUnqualified)));}assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);
    assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);assert_eq!(s.artifacts.download(&s.reader,s.result,5)?,bytes);Ok(())
}
#[test]
fn source_kind_and_unverified_scanner_cannot_be_reclassified_as_current_result()->R{
    let bytes=raw("ABC")?;for(kind,unverified)in [(ArtifactKind::Source,false),(ArtifactKind::Result,true)]{
        let s=StoredFixture::new(&bytes,kind,unverified)?;writer!(s,actor,p);for preview in [false,true]{assert!(prepare!(&p,&request(&s,&bytes,preview)?).is_err());}}Ok(())
}
#[test]
fn invalid_component_limits_and_review_policy_shape_reject_before_reads()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes,true)?;let before=s.metadata.audit_events()?.len();
    for n in [0,10001]{let mut v=good.clone();v["operation"]["max_changed_components"]=json!(n);assert!(matches!(prepare!(&p,&v),Err(E::Request)));}
    let mut v=good;v["operation"]["review_policy"]["approved"]=json!(true);assert!(matches!(prepare!(&p,&v),Err(E::Request)));assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
struct BoundaryRepo{inner:rev::InMemoryRevisionRepository,calls:AtomicUsize,trigger:AtomicUsize,context:rev::RevisionRequestContext,advance:rev::RevisionCommitRequest}
impl rev::RevisionRepository for BoundaryRepo{
    fn compare_and_swap(&self,c:&rev::RevisionRequestContext,r:&rev::RevisionCommitRequest)->Result<rev::CommitOutcome,rev::RevisionError>{self.inner.compare_and_swap(c,r)}
    fn head(&self,t:TenantId,p:rev::ProjectId,b:rev::BranchId)->Result<rev::RevisionHead,rev::RevisionError>{let n=self.calls.fetch_add(1,Ordering::SeqCst)+1;
        if n==self.trigger.load(Ordering::SeqCst){assert!(matches!(self.inner.compare_and_swap(&self.context,&self.advance)?,rev::CommitOutcome::Committed(_)));}self.inner.head(t,p,b)}
    fn node(&self,t:TenantId,p:rev::ProjectId,r:rev::RevisionId)->Result<rev::RevisionNode,rev::RevisionError>{self.inner.node(t,p,r)}
}
fn race(preview:bool,stage:usize)->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=request(&s,&bytes,preview)?;let out=prepare!(&p,&v)?;
    let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,
        ContentDigest::of(b"mask-head-race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation fixture"),ContentDigest::of(b"transaction fixture"))?;
    let repo=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
    let bound=StoredFormProvider::bind(&s.artifacts,&repo,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
    match stage{0=>{Product::prepare_json(&bound,&wire(&v)?,Default::default(),Default::default(),5)?;},1=>{out.verify(&bound,5)?;},2=>{out.with_verified_json(&bound,5,|_|())?;},_=>{out.with_verified_bytes(&bound,5,|_|())?;}}
    let count=repo.repository().calls.load(Ordering::SeqCst);assert!(count>=4);repo.repository().calls.store(0,Ordering::SeqCst);repo.repository().trigger.store(count,Ordering::SeqCst);let called=Cell::new(false);
    match stage{0=>assert!(Product::prepare_json(&bound,&wire(&v)?,Default::default(),Default::default(),6).is_err()),1=>assert!(out.verify(&bound,6).is_err()),2=>assert!(out.with_verified_json(&bound,6,|_|called.set(true)).is_err()),_=>assert!(out.with_verified_bytes(&bound,6,|_|called.set(true)).is_err())}
    assert!(!called.get());assert_eq!(repo.repository().calls.load(Ordering::SeqCst),count);Ok(())
}
#[test]fn mutation_preparation_final_head_race_rejects()->R{race(false,0)}
#[test]fn mutation_verify_final_head_race_rejects()->R{race(false,1)}
#[test]fn mutation_metadata_delivery_final_head_race_blocks_consumer()->R{race(false,2)}
#[test]fn mutation_byte_delivery_final_head_race_blocks_consumer()->R{race(false,3)}
#[test]fn preview_preparation_final_head_race_rejects()->R{race(true,0)}
#[test]fn preview_verify_final_head_race_rejects()->R{race(true,1)}
#[test]fn preview_metadata_delivery_final_head_race_blocks_consumer()->R{race(true,2)}

#[path="support/personal_info_mask_compiled.rs"]mod compiled;
#[path="support/personal_info_detection_product.rs"]mod detection;
#[path="support/personal_info_catalog_stored.rs"]mod stored_catalog;
