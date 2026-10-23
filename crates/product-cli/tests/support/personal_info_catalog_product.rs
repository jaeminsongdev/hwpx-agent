// Strict catalog product integration, synthetic configuration by default; one explicit installed fixture.
use super::*;
use hwpx_agent_cli::form_product_request::stored_source_search::personal_info_catalog::{StoredPersonalInfoCatalogProductRequest as CP,
    PreparedStoredPersonalInfoCatalogProduct as Prepared,PersonalInfoCatalogProductError as PE,
    PERSONAL_INFO_CATALOG_PRODUCT_SCHEMA as CS,PERSONAL_INFO_CATALOG_NEXT_SCHEMA as CN,PERSONAL_INFO_CATALOG_SELECTION_SCHEMA as CQ};
fn req(s:&StoredFixture,bytes:&[u8],f:&Feed)->Result<Value,Box<dyn Error>>{
    let mut v=request(s,bytes,false)?;v["schema_version"]=json!(CS);v["expected_catalog_sha256"]=json!(hex::encode(sha(f)));
    v["operation"]=json!({"kind":"find_personal_info_catalog","families":FAMILIES,"max_results":10000,"review_policy":policy()});Ok(v)
}
macro_rules! product{($p:expr,$s:expr,$b:expr,$f:expr)=>{CP::prepare_json($p,$f,&wire(&req($s,$b,$f)?)?,Default::default(),4)}}
fn next(out:&Prepared,cursor:Value,direction:&str,wrap:bool)->Result<Value,Box<dyn Error>>{
    Ok(json!({"schema_version":CN,"catalog_receipt_sha256":out.continuation_receipt_sha256()?,"navigation":{"direction":direction,"wrap":wrap,"cursor":cursor}}))
}
fn select(out:&Prepared,index:usize)->Result<Value,Box<dyn Error>>{Ok(json!({"schema_version":CQ,"catalog_receipt_sha256":out.continuation_receipt_sha256()?,"occurrence_index":index}))}
#[test]
fn full_catalog_product_and_direct_service_have_same_original_result_and_provenance()->R{
    let bytes=raw("MARK MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let service=detect!(&p,&s,&f)?;
    let out=product!(&p,&s,&bytes,&f)?;assert_eq!(out.receipt().stored,*service.receipt());assert_eq!(out.receipt().stored.selected_patterns,64);
    let a=service.with_verified_json(&p,&f,5,|b|serde_json::from_slice::<Value>(b))??;let b=out.with_verified_json(&p,&f,5,|b|serde_json::from_slice::<Value>(b))??;
    assert_eq!(a["result"],b["result"]);assert_eq!(out.receipt().capability_id,"search.personal_info_find_replace");out.verify(&p,&f,5)?;Ok(())
}
#[test]
fn required_root_operation_and_selector_fields_reject_before_any_config_or_document_read()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let good=req(&s,&bytes,&f)?;let n=s.metadata.audit_events()?.len();
    for key in ["schema_version","idempotency_key","project_id","document_id","base_revision","expected_head_generation","expected_source_package_sha256","expected_catalog_sha256","plan_id","selector","operation"]{
        let mut v=good.clone();v.as_object_mut().ok_or("root")?.remove(key);assert!(matches!(CP::prepare_json(&p,&f,&wire(&v)?,Default::default(),4),Err(PE::Request)));}
    for key in ["kind","families","max_results","review_policy"]{let mut v=good.clone();v["operation"].as_object_mut().ok_or("operation")?.remove(key);assert!(matches!(CP::prepare_json(&p,&f,&wire(&v)?,Default::default(),4),Err(PE::Request)));}
    for key in ["scope","revision_id"]{let mut v=good.clone();v["selector"].as_object_mut().ok_or("selector")?.remove(key);assert!(matches!(CP::prepare_json(&p,&f,&wire(&v)?,Default::default(),4),Err(PE::Request)));}
    assert_eq!(f.reads.get(),0);assert_eq!(s.metadata.audit_events()?.len(),n);Ok(())
}
#[test]
fn patterns_paths_native_defaults_mutations_and_approval_fields_reject_before_reads()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let good=req(&s,&bytes,&f)?;let n=s.metadata.audit_events()?.len();
    for key in ["catalog_path","source_path","patterns","rules","approved","raw_xml","graph"]{let mut v=good.clone();v[key]=json!({});assert!(matches!(CP::prepare_json(&p,&f,&wire(&v)?,Default::default(),4),Err(PE::Request)));}
    for key in ["query","replacement","patterns","rules","native_defaults","preview_only","mask_policy","style_filter","approved"]{let mut v=good.clone();v["operation"][key]=json!(false);assert!(matches!(CP::prepare_json(&p,&f,&wire(&v)?,Default::default(),4),Err(PE::Request)));}
    assert_eq!(f.reads.get(),0);assert_eq!(s.metadata.audit_events()?.len(),n);Ok(())
}
#[test]
fn enum_objects_unknown_family_address_null_and_wrong_policy_types_reject_before_reads()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let good=req(&s,&bytes,&f)?;let n=s.metadata.audit_events()?.len();
    for family in [json!({"telephone":null}),json!("address"),json!("native_auto"),Value::Null,json!(1)]{let mut v=good.clone();v["operation"]["families"]=json!([family]);assert!(matches!(CP::prepare_json(&p,&f,&wire(&v)?,Default::default(),4),Err(PE::Request)));}
    for(key,value)in [("kind",json!({"find_personal_info_catalog":null})),("families",Value::Null),("review_policy",json!([])),("max_results",json!(true))]{let mut v=good.clone();v["operation"][key]=value;assert!(matches!(CP::prepare_json(&p,&f,&wire(&v)?,Default::default(),4),Err(PE::Request)));}
    assert_eq!(f.reads.get(),0);assert_eq!(s.metadata.audit_events()?.len(),n);Ok(())
}
#[test]
fn duplicate_escaped_keys_trailing_json_nonobjects_and_wrong_schema_reject_before_reads()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let good=String::from_utf8(wire(&req(&s,&bytes,&f)?)?)?;let n=s.metadata.audit_events()?.len();
    for text in [good.replace("\"max_results\":10000","\"max_results\":10000,\"max_res\\u0075lts\":1"),format!("{good} {{}}"),"null".into(),"[]".into(),"{}".into(),good.replace(CS,"hwpx-agent.product-personal-info-catalog-request/v2")]{
        assert!(matches!(CP::prepare_json(&p,&f,text.as_bytes(),Default::default(),4),Err(PE::Request)));}assert_eq!(f.reads.get(),0);assert_eq!(s.metadata.audit_events()?.len(),n);Ok(())
}
#[test]
fn empty_duplicate_or_too_many_families_invalid_digests_and_result_counts_reject_before_reads()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let good=req(&s,&bytes,&f)?;
    for families in [json!([]),json!(["telephone","telephone"]),Value::Array((0..12).map(|_|json!("telephone")).collect())]{let mut v=good.clone();v["operation"]["families"]=families;assert!(matches!(CP::prepare_json(&p,&f,&wire(&v)?,Default::default(),4),Err(PE::Request)));}
    for(key,bad)in [("expected_catalog_sha256","F".repeat(64)),("expected_catalog_sha256","0".repeat(63)),("expected_source_package_sha256","x".repeat(64))]{let mut v=good.clone();v[key]=json!(bad);assert!(matches!(CP::prepare_json(&p,&f,&wire(&v)?,Default::default(),4),Err(PE::Request)));}
    for count in [0,10001]{let mut v=good.clone();v["operation"]["max_results"]=json!(count);assert!(matches!(CP::prepare_json(&p,&f,&wire(&v)?,Default::default(),4),Err(PE::Request)));}assert_eq!(f.reads.get(),0);Ok(())
}
#[test]
fn exact_sixteen_kib_request_limit_binds_raw_and_canonical_requests_separately()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let good=req(&s,&bytes,&f)?;let mut padded_bytes=super::wire(&good)?;padded_bytes.resize(16*1024,b' ');
    let padded=CP::prepare_json(&p,&f,&padded_bytes,Default::default(),4)?;let ordinary=product!(&p,&s,&bytes,&f)?;assert_eq!(padded.receipt().canonical_request_sha256,ordinary.receipt().canonical_request_sha256);
    assert_ne!(padded.continuation_receipt_sha256()?,ordinary.continuation_receipt_sha256()?);let n=f.reads.get();padded_bytes.push(b' ');assert!(matches!(CP::prepare_json(&p,&f,&padded_bytes,Default::default(),4),Err(PE::Limit)));assert_eq!(f.reads.get(),n);Ok(())
}
#[test]
fn all_four_original_revision_bound_selectors_remain_available()->R{
    let bytes=definition::package(&(para(1,"MARK MARK")+&para(2,"MARK")))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let good=req(&s,&bytes,&f)?;
    // The existing inventory request does not accept the catalog-only field.
    let mut base=good.clone();base.as_object_mut().ok_or("request")?.remove("expected_catalog_sha256");let inv=inventory(&p,&base)?;
    let node=inv["inventory"]["nodes"].as_array().ok_or("nodes")?.iter().find(|n|n["source_handle"]==inv["inventory"]["blocks"][0]["paragraph_handle"]).ok_or("node")?;
    for mode in 0..4{let mut v=good.clone();match mode{0=>{},1=>{v["selector"]["scope"]=json!("section");v["selector"]["section_ids"]=inv["inventory"]["section_ids"].clone();},
        2=>{v["selector"]["scope"]=json!("node_set");v["selector"]["range"]=json!({"node_ids":[node["node_id"]]});},_=>{v["selector"]["scope"]=json!("selection");v["selector"]["range"]=selection(&inv,5,9)?;}}
        let out=CP::prepare_json(&p,&f,&wire(&v)?,Default::default(),4)?;assert_eq!(out.receipt().stored.matched_formats,if mode<2{3}else if mode==2{2}else{1});}Ok(())
}
#[test]
fn malformed_selector_shapes_foreign_revision_and_stale_index_fail_closed()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let good=req(&s,&bytes,&f)?;
    for mode in 0..5{let mut v=good.clone();match mode{0=>v["selector"]["range"]=Value::Null,1=>v["selector"]["section_ids"]=json!([]),2=>v["selector"]["revision_id"]=json!(rev::RevisionId::generate().public_id()),3=>v["expected_head_generation"]=json!(0),_=>v["selector"]["scope"]=json!({"document":null})}assert!(matches!(CP::prepare_json(&p,&f,&wire(&v)?,Default::default(),4),Err(PE::Request)));}
    assert_eq!(f.reads.get(),0);let mut base=good.clone();base.as_object_mut().ok_or("request")?.remove("expected_catalog_sha256");let inv=inventory(&p,&base)?;
    let mut v=good;v["selector"]["scope"]=json!("selection");v["selector"]["range"]=selection(&inv,0,4)?;v["selector"]["range"]["index_sha256"]=json!("0".repeat(64));assert!(CP::prepare_json(&p,&f,&wire(&v)?,Default::default(),4).is_err());Ok(())
}
#[test]
fn hidden_and_memo_policies_remain_explicit_and_author_values_are_not_disclosed()->R{
    let bytes=definition::package(&review::body())?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("K");let good=req(&s,&bytes,&f)?;
    for(h,m,n)in [(false,false,2),(true,false,4),(false,true,4),(true,true,6)]{let mut v=good.clone();v["operation"]["review_policy"]=json!({"include_hidden_explanations":h,"include_memo_bodies":m});
        let out=CP::prepare_json(&p,&f,&wire(&v)?,Default::default(),4)?;assert_eq!(out.receipt().stored.matched_formats,n);let text=out.with_verified_json(&p,&f,5,|b|String::from_utf8_lossy(b).into_owned())?;assert!(!text.contains("PRIVATE-AUTHOR")&&!text.contains("MEMO K K"));}Ok(())
}
#[test]
fn changed_config_or_mismatched_expected_catalog_digest_is_not_rebound_to_new_defaults()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=product!(&p,&s,&bytes,&f)?;let good=req(&s,&bytes,&f)?;
    f.raw.borrow_mut()[8]^=1;assert!(out.verify(&p,&f,5).is_err());assert!(CP::prepare_json(&p,&f,&wire(&good)?,Default::default(),5).is_err());
    let other=feed("M(ARK)");assert!(CP::prepare_json(&p,&other,&wire(&good)?,Default::default(),5).is_err());Ok(())
}
#[test]
fn final_product_preparation_catalog_race_rejects_after_outer_envelope_binding()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");f.replace_at.set(3);assert!(product!(&p,&s,&bytes,&f).is_err());assert_eq!(f.reads.get(),3);Ok(())
}
#[test]
fn metadata_next_and_selection_final_config_races_never_call_consumer()->R{
    for mode in 0..3{let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=product!(&p,&s,&bytes,&f)?;
        f.replace_at.set(f.reads.get()+2);let called=Cell::new(false);let result=match mode{0=>out.with_verified_json(&p,&f,5,|_|called.set(true)),
            1=>out.with_next_verified_json(&p,&f,&wire(&next(&out,Value::Null,"forward",false)?)?,5,|_|called.set(true)),
            _=>out.with_selection_verified_json(&p,&f,&wire(&select(&out,0)?)?,5,|_|called.set(true))};assert!(result.is_err());assert!(!called.get());}Ok(())
}
#[test]
fn write_permission_is_required_for_initial_verify_metadata_next_and_selection()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=product!(&p,&s,&bytes,&f)?;let reader=s.provider()?;let called=Cell::new(false);
    assert!(product!(&reader,&s,&bytes,&f).is_err());assert!(out.verify(&reader,&f,5).is_err());assert!(out.with_verified_json(&reader,&f,5,|_|called.set(true)).is_err());
    assert!(out.with_next_verified_json(&reader,&f,&wire(&next(&out,Value::Null,"forward",false)?)?,5,|_|called.set(true)).is_err());assert!(out.with_selection_verified_json(&reader,&f,&wire(&select(&out,0)?)?,5,|_|called.set(true)).is_err());assert!(!called.get());Ok(())
}
#[test]
fn foreign_provider_five_scopes_cannot_deliver_retained_positions()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=product!(&p,&s,&bytes,&f)?;let called=Cell::new(false);
    for mode in 0..5{let tenant=if mode==4{TenantId::new(Uuid::from_u128(992))?}else{s.reader.tenant_id()};let subject=if mode==3{SubjectDigest::from_authenticated_subject("foreign-catalog-product")?}else{s.reader.subject()};
        let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);let context=rev::RevisionRequestContext::new(tenant,subject);
        let project=if mode==2{rev::ProjectId::parse("prj_70000000000000000000000000000003")?}else{s.project};let branch=if mode==1{rev::BranchId::parse("brn_70000000000000000000000000000003")?}else{s.branch};
        let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&context,project,branch,DocumentId::parse(if mode==0{"foreign-document"}else{"actual-form-document"})?)?;
        assert!(out.verify(&other,&f,5).is_err());assert!(out.with_selection_verified_json(&other,&f,&wire(&select(&out,0)?)?,5,|_|called.set(true)).is_err());}assert!(!called.get());Ok(())
}
#[test]
fn current_acl_revocation_blocks_all_deliveries_and_regrant_rechecks_access()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=product!(&p,&s,&bytes,&f)?;s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;let called=Cell::new(false);
    assert!(out.verify(&p,&f,6).is_err());assert!(out.with_verified_json(&p,&f,6,|_|called.set(true)).is_err());assert!(out.with_next_verified_json(&p,&f,&wire(&next(&out,Value::Null,"forward",false)?)?,6,|_|called.set(true)).is_err());
    assert!(out.with_selection_verified_json(&p,&f,&wire(&select(&out,0)?)?,6,|_|called.set(true)).is_err());assert!(!called.get());s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;out.verify(&p,&f,8)?;Ok(())
}
#[test]
fn quarantine_aead_corruption_and_config_source_errors_fail_without_callbacks()->R{
    for mode in 0..3{let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=product!(&p,&s,&bytes,&f)?;
        match mode{0=>{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("CATALOG_PRODUCT_TEST")?,5)?;},1=>{s.blobs.tamper.store(true,Ordering::SeqCst);},_=>f.fail.set(true)}
        let called=Cell::new(false);assert!(out.verify(&p,&f,6).is_err());assert!(out.with_selection_verified_json(&p,&f,&wire(&select(&out,0)?)?,6,|_|called.set(true)).is_err());assert!(!called.get());}Ok(())
}
#[test]
fn next_forward_backward_wrap_and_context_are_bound_to_retained_results()->R{
    let bytes=raw("MARK MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=product!(&p,&s,&bytes,&f)?;
    let a=out.with_next_verified_json(&p,&f,&wire(&next(&out,Value::Null,"forward",false)?)?,5,|b|serde_json::from_slice::<Value>(b))??;
    let b=out.with_next_verified_json(&p,&f,&wire(&next(&out,a["result"]["cursor"].clone(),"forward",false)?)?,5,|b|serde_json::from_slice::<Value>(b))??;assert_eq!(a["result"]["match_index"],0);assert_eq!(b["result"]["match_index"],1);
    let back=out.with_next_verified_json(&p,&f,&wire(&next(&out,b["result"]["cursor"].clone(),"backward",false)?)?,5,|b|serde_json::from_slice::<Value>(b))??;assert_eq!(back["result"]["match_index"],0);
    let wrap=out.with_next_verified_json(&p,&f,&wire(&next(&out,b["result"]["cursor"].clone(),"forward",true)?)?,5,|b|serde_json::from_slice::<Value>(b))??;assert_eq!(wrap["result"]["wrapped"],true);Ok(())
}
#[test]
fn key_plan_family_selection_and_raw_request_cannot_reuse_receipt_or_cursor()->R{
    let bytes=raw("MARK MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let good=req(&s,&bytes,&f)?;let out=product!(&p,&s,&bytes,&f)?;
    let first=out.with_next_verified_json(&p,&f,&wire(&next(&out,Value::Null,"forward",false)?)?,5,|b|serde_json::from_slice::<Value>(b))??;
    for mode in 0..4{let mut v=good.clone();match mode{0=>v["idempotency_key"]=json!("other-key"),1=>v["plan_id"]=json!("other-plan"),2=>v["operation"]["families"]=json!(["telephone"]),_=>{}}
        let mut raw=wire(&v)?;if mode==3{raw.push(b' ');}let other=CP::prepare_json(&p,&f,&raw,Default::default(),4)?;assert_ne!(other.continuation_receipt_sha256()?,out.continuation_receipt_sha256()?);
        assert!(other.with_selection_verified_json(&p,&f,&wire(&select(&out,0)?)?,5,|_|()).is_err());let mut n=next(&other,first["result"]["cursor"].clone(),"forward",false)?;
        n["catalog_receipt_sha256"]=json!(other.continuation_receipt_sha256()?);assert!(other.with_next_verified_json(&p,&f,&wire(&n)?,5,|_|()).is_err());}Ok(())
}
#[test]
fn changed_catalog_with_same_match_text_has_different_retained_binding()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=product!(&p,&s,&bytes,&f)?;
    let other=feed("M(ARK)");let second=product!(&p,&s,&bytes,&other)?;assert_eq!(second.receipt().stored.matched_formats,out.receipt().stored.matched_formats);
    assert_ne!(second.continuation_receipt_sha256()?,out.continuation_receipt_sha256()?);assert!(second.with_selection_verified_json(&p,&other,&wire(&select(&out,0)?)?,5,|_|()).is_err());Ok(())
}
#[test]
fn followup_duplicate_unknown_fields_enum_objects_wrong_profiles_and_indices_fail_closed()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=product!(&p,&s,&bytes,&f)?;let good=next(&out,Value::Null,"forward",false)?;let n=f.reads.get();let called=Cell::new(false);
    for mode in 0..5{let mut v=good.clone();match mode{0=>v["schema_version"]=json!(CS),1=>v["navigation"]=json!([]),2=>v["navigation"]["direction"]=json!({"forward":null}),3=>v["navigation"]["approved"]=json!(true),_=>v["navigation"]["cursor"]=json!(false)}assert!(out.with_next_verified_json(&p,&f,&wire(&v)?,5,|_|called.set(true)).is_err());}
    let duplicate=String::from_utf8(wire(&good)?)?.replace("\"wrap\":false","\"wrap\":false,\"wr\\u0061p\":true");assert!(out.with_next_verified_json(&p,&f,duplicate.as_bytes(),5,|_|called.set(true)).is_err());
    let mut v=select(&out,0)?;v["approved"]=json!(true);assert!(out.with_selection_verified_json(&p,&f,&wire(&v)?,5,|_|called.set(true)).is_err());assert_eq!(f.reads.get(),n);
    for index in [1,10000]{assert!(out.with_selection_verified_json(&p,&f,&wire(&select(&out,index)?)?,5,|_|called.set(true)).is_err());}assert!(!called.get());Ok(())
}
#[test]
fn exact_selection_feeds_existing_mask_but_never_implicitly_changes_original()->R{
    let bytes=raw("KEEP MARK TAIL")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=product!(&p,&s,&bytes,&f)?;
    let v=out.with_selection_verified_json(&p,&f,&wire(&select(&out,0)?)?,5,|b|serde_json::from_slice::<Value>(b))??;let c=&v["result"];let sha:[u8;32]=serde_json::from_value(c["index_sha256"].clone())?;
    let mut v=request(&s,&bytes,false)?;v["selector"]["scope"]=json!("selection");v["selector"]["range"]=json!({"coordinate_space":"index_nfc_unicode_scalars","index_sha256":hex::encode(sha),"start":c["start"],"end":c["end"]});
    let candidate=Product::prepare_json(&p,&wire(&v)?,Default::default(),Default::default(),5)?;assert!(candidate.with_verified_bytes(&p,6,section)??.contains("KEEP **** TAIL"));assert_eq!(s.artifacts.download(&s.reader,s.result,6)?,bytes);Ok(())
}
#[test]
fn empty_user_defined_selection_and_partial_nfc_never_fabricate_exact_selection()->R{
    let bytes=raw("\u{344}")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("\u{308}");let out=product!(&p,&s,&bytes,&f)?;assert_eq!(out.receipt().stored.matched_formats,1);
    assert!(out.with_selection_verified_json(&p,&f,&wire(&select(&out,0)?)?,5,|_|()).is_err());let mut v=req(&s,&bytes,&f)?;v["operation"]["families"]=json!(["user_defined"]);let empty=CP::prepare_json(&p,&f,&wire(&v)?,Default::default(),4)?;
    assert_eq!(empty.receipt().stored.matched_formats,0);assert_eq!(empty.receipt().stored.selected_patterns,0);assert!(empty.with_selection_verified_json(&p,&f,&wire(&select(&empty,0)?)?,5,|_|()).is_err());Ok(())
}
#[test]
fn server_match_regex_and_whole_product_response_caps_are_not_silently_truncated()->R{
    let bytes=raw("MARK MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let mut v=req(&s,&bytes,&f)?;v["operation"]["max_results"]=json!(1);assert!(CP::prepare_json(&p,&f,&wire(&v)?,Default::default(),4).is_err());v["operation"]["max_results"]=json!(10000);
    for config in [Config{matches:1,..Default::default()},Config{pattern_bytes:1,..Default::default()},Config{result_bytes:1,..Default::default()}]{assert!(CP::prepare_json(&p,&f,&wire(&v)?,SourceSearchLimits::new(config)?,4).is_err());}Ok(())
}
#[test]
fn exact_whole_product_response_byte_bound_and_one_less_include_outer_receipt()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let good=req(&s,&bytes,&f)?;let out=product!(&p,&s,&bytes,&f)?;let n=out.with_verified_json(&p,&f,5,<[u8]>::len)?;
    let exact=CP::prepare_json(&p,&f,&wire(&good)?,SourceSearchLimits::new(Config{result_bytes:n,..Default::default()})?,4)?;assert_eq!(exact.with_verified_json(&p,&f,5,<[u8]>::len)?,n);
    assert!(CP::prepare_json(&p,&f,&wire(&good)?,SourceSearchLimits::new(Config{result_bytes:n-1,..Default::default()})?,4).is_err());Ok(())
}
#[test]
fn source_kind_unverified_scanner_and_mismatched_source_digest_are_rejected()->R{
    let bytes=raw("MARK")?;let f=feed("MARK");for(kind,unverified)in [(ArtifactKind::Source,false),(ArtifactKind::Result,true)]{let s=StoredFixture::new(&bytes,kind,unverified)?;writer!(s,actor,p);assert!(product!(&p,&s,&bytes,&f).is_err());}
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=req(&s,&bytes,&f)?;v["expected_source_package_sha256"]=json!("0".repeat(64));assert!(CP::prepare_json(&p,&f,&wire(&v)?,Default::default(),4).is_err());Ok(())
}
#[test]
fn metadata_debug_and_followups_redact_original_values_patterns_and_request_secrets()->R{
    let bytes=raw("PRIVATE-CATALOG-MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("PRIVATE-CATALOG-MARK");let out=product!(&p,&s,&bytes,&f)?;
    for text in [format!("{out:?}{:?}",out.receipt()),out.with_verified_json(&p,&f,5,|b|String::from_utf8_lossy(b).into_owned())?,out.with_selection_verified_json(&p,&f,&wire(&select(&out,0)?)?,5,|b|String::from_utf8_lossy(b).into_owned())?]{
        assert!(!text.contains("PRIVATE-")&&!text.contains("NEVERF")&&!text.contains("pattern0=")&&!text.contains("matched_value_sha256"));}Ok(())
}
#[test]
fn readonly_preparation_preserves_source_head_ingest_and_does_not_claim_execution()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=product!(&p,&s,&bytes,&f)?;
    assert!(matches!(out.require_current_product_route(&p,&f,5),Err(PE::RouteUnqualified)));assert!(!out.receipt().idempotency_key_claimed&&!out.receipt().native_identity_cas_execution_publication_authority);
    assert_eq!(s.artifacts.download(&s.reader,s.result,5)?,bytes);assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
}
fn product_race(stage:usize)->R{
    let bytes=raw("MARK MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let v=req(&s,&bytes,&f)?;let out=product!(&p,&s,&bytes,&f)?;
    let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,
        ContentDigest::of(b"catalog-product-head-race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation fixture"),ContentDigest::of(b"transaction fixture"))?;
    let repo=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
    let bound=StoredFormProvider::bind(&s.artifacts,&repo,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
    match stage{0=>{CP::prepare_json(&bound,&f,&wire(&v)?,Default::default(),5)?;},1=>{out.verify(&bound,&f,5)?;},2=>{out.with_verified_json(&bound,&f,5,|_|())?;},
        3=>{out.with_next_verified_json(&bound,&f,&wire(&next(&out,Value::Null,"forward",false)?)?,5,|_|())?;},_=>{out.with_selection_verified_json(&bound,&f,&wire(&select(&out,0)?)?,5,|_|())?;}}
    let count=repo.repository().calls.load(Ordering::SeqCst);assert!(count>=4);repo.repository().calls.store(0,Ordering::SeqCst);repo.repository().trigger.store(count,Ordering::SeqCst);let called=Cell::new(false);
    match stage{0=>assert!(CP::prepare_json(&bound,&f,&wire(&v)?,Default::default(),6).is_err()),1=>assert!(out.verify(&bound,&f,6).is_err()),2=>assert!(out.with_verified_json(&bound,&f,6,|_|called.set(true)).is_err()),
        3=>assert!(out.with_next_verified_json(&bound,&f,&wire(&next(&out,Value::Null,"forward",false)?)?,6,|_|called.set(true)).is_err()),_=>assert!(out.with_selection_verified_json(&bound,&f,&wire(&select(&out,0)?)?,6,|_|called.set(true)).is_err())}
    assert!(!called.get());assert_eq!(repo.repository().calls.load(Ordering::SeqCst),count);Ok(())
}
#[test]fn preparation_final_head_race_rejects()->R{product_race(0)}
#[test]fn verify_final_head_race_rejects()->R{product_race(1)}
#[test]fn metadata_final_head_race_rejects()->R{product_race(2)}
#[test]fn navigation_final_head_race_rejects()->R{product_race(3)}
#[test]fn selection_final_head_race_rejects()->R{product_race(4)}
#[cfg(all(windows,feature="p09-installed-format-fixture"))]
#[test]
fn explicit_installed_catalog_current_store_and_product_bind_all_sixty_four_original_patterns()->R{
    use hwpx_agent_cli::form_stored_provider::actual_import::source_search::personal_info_catalog::InstalledPersonalInfoCatalogSource;
    let catalog=InstalledPersonalInfoCatalogSource;let config=catalog.read_current_catalog()?;
    assert_eq!(config.len(),17020);assert_eq!(ContentDigest::of(&config).hex(),"fe3721e68a749c3d1ec843207d475249fa75e68f1de569fe45468c05b1022434");
    let bytes=raw("010-000-0000")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    let f=feed("MARK");let mut v=req(&s,&bytes,&f)?;v["expected_catalog_sha256"]=json!(ContentDigest::of(&config).hex());let out=CP::prepare_json(&p,&catalog,&wire(&v)?,Default::default(),4)?;
    assert_eq!(out.receipt().stored.catalog.total_patterns,64);assert_eq!(out.receipt().stored.selected_patterns,64);assert!(!out.receipt().stored.catalog.installed_vendor_authenticity_or_native_semantics_qualified);
    out.verify(&p,&catalog,5)?;let data=out.with_verified_json(&p,&catalog,5,|b|serde_json::from_slice::<Value>(b))??;assert_eq!(data["result"]["selected_patterns"],64);
    v["operation"]["families"]=json!(["telephone"]);let telephone=CP::prepare_json(&p,&catalog,&wire(&v)?,Default::default(),5)?;assert_eq!(telephone.receipt().stored.matched_formats,1);
    assert_eq!(telephone.receipt().stored.selected_patterns,8);assert_eq!(s.artifacts.download(&s.reader,s.result,6)?,bytes);Ok(())
}
