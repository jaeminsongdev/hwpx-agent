//! Source-owner/read-only product integration with synthetic markers/scanner/keys. No Native or operational DB.
use super::*;
use hwpx_agent_cli::form_product_request::stored_source_search::personal_info::{StoredPersonalInfoDetectionProductRequest as Detect,
    PreparedStoredPersonalInfoDetectionProduct as Detected,PersonalInfoDetectionProductError as DE,
    PERSONAL_INFO_DETECTION_PRODUCT_SCHEMA as DS,PERSONAL_INFO_DETECTION_NEXT_SCHEMA as NS,PERSONAL_INFO_DETECTION_SELECTION_SCHEMA as SS};
use hwpx_agent_cli::form_stored_provider::actual_import::source_search::personal_info::StoredPersonalInfoDetectionError as SE;
use hwpx_package::document_import::search::{SourceSearchError as SearchError,personal_info::{SourcePersonalInfoDetectionPolicy as Formats,SourcePersonalInfoRule as Rule,SourcePersonalInfoKind as Kind}};
fn formats()->Result<Formats,SearchError>{Formats::new(vec![Rule{rule_id:"custom".into(),kind:Kind::Custom,query:"MARK".into(),regex:false,case_sensitive:true,whole_word:false}])}
fn drequest(s:&StoredFixture,bytes:&[u8])->Result<Value,Box<dyn Error>>{let mut v=request(s,bytes,false)?;v["schema_version"]=json!(DS);
    v["operation"]=json!({"kind":"find_personal_info_formats","rules":[{"rule_id":"custom","kind":"custom","query":"MARK","regex":false,"case_sensitive":true,"whole_word":false}],"max_results":10000,"review_policy":policy()});Ok(v)}
macro_rules! detection{($p:expr,$v:expr)=>{Detect::prepare_json($p,&wire($v)?,Default::default(),4)}}
fn metadata(out:&Detected,p:&Provider<'_>)->Result<Value,Box<dyn Error>>{Ok(out.with_verified_json(p,5,|b|serde_json::from_slice::<Value>(b))??)}
fn next(out:&Detected,cursor:Value,direction:&str,wrap:bool)->Result<Value,Box<dyn Error>>{
    Ok(json!({"schema_version":NS,"detection_receipt_sha256":out.continuation_receipt_sha256()?,"navigation":{"direction":direction,"wrap":wrap,"cursor":cursor}}))}
fn select(out:&Detected,index:usize)->Result<Value,Box<dyn Error>>{Ok(json!({"schema_version":SS,"detection_receipt_sha256":out.continuation_receipt_sha256()?,"occurrence_index":index}))}
#[test]
fn owned_service_and_product_retain_the_same_original_result_and_policy()->R{
    let bytes=raw("MARK MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    let service=p.import_actual_forms(s.head,4)?.into_personal_info_detection(&p,&formats()?,Scope::Document,policy(),Default::default(),4)?;
    let out=detection!(&p,&drequest(&s,&bytes)?)?;assert_eq!(service.receipt(),&out.receipt().stored);assert_eq!(out.receipt().stored.matched_formats,2);
    assert_eq!(out.receipt().capability_id,"search.personal_info_find_replace");let v=metadata(&out,&p)?;assert_eq!(v["result"]["rule_matches"].as_array().ok_or("labels")?.len(),2);
    let direct=service.with_verified_json(&p,5,|b|serde_json::from_slice::<Value>(b))??;assert_eq!(direct["result"],v["result"]);service.verify(&p,5)?;out.verify(&p,5)?;Ok(())
}
#[test]
fn exact_selected_result_can_feed_existing_mask_without_widening_or_implicit_write()->R{
    let bytes=raw("KEEP MARK TAIL")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let out=detection!(&p,&drequest(&s,&bytes)?)?;
    let v=out.with_selection_verified_json(&p,&wire(&select(&out,0)?)?,5,|b|serde_json::from_slice::<Value>(b))??;let coordinates=&v["result"];
    let sha:[u8;32]=serde_json::from_value(coordinates["index_sha256"].clone())?;let mut mask_request=request(&s,&bytes,false)?;mask_request["selector"]["scope"]=json!("selection");
    mask_request["selector"]["range"]=json!({"coordinate_space":"index_nfc_unicode_scalars","index_sha256":hex::encode(sha),"start":coordinates["start"],"end":coordinates["end"]});
    let masked=super::Product::prepare_json(&p,&wire(&mask_request)?,Default::default(),Default::default(),5)?;
    assert!(masked.with_verified_bytes(&p,6,section)??.contains("KEEP **** TAIL"));assert_eq!(s.artifacts.download(&s.reader,s.result,6)?,bytes);
    assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);Ok(())
}
#[test]
fn zero_results_stay_read_only_and_selection_does_not_invoke_consumer()->R{
    let bytes=raw("OTHER")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let out=detection!(&p,&drequest(&s,&bytes)?)?;assert_eq!(out.receipt().stored.matched_formats,0);
    let v=out.with_next_verified_json(&p,&wire(&next(&out,Value::Null,"forward",true)?)?,5,|b|serde_json::from_slice::<Value>(b))??;assert_eq!(v["result"]["exhausted"],true);
    let called=Cell::new(false);assert!(out.with_selection_verified_json(&p,&wire(&select(&out,0)?)?,5,|_|called.set(true)).is_err());assert!(!called.get());Ok(())
}
#[test]
fn literal_regex_categories_and_explicit_case_policy_reach_the_original_core()->R{
    let bytes=raw("mark MARK AX AB")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=drequest(&s,&bytes)?;
    v["operation"]["rules"][0]["case_sensitive"]=json!(false);v["operation"]["rules"].as_array_mut().ok_or("rules")?.push(json!({"rule_id":"pattern","kind":"email","query":"A[XB]","regex":true,"case_sensitive":true,"whole_word":true}));
    let out=detection!(&p,&v)?;assert_eq!(out.receipt().stored.matched_formats,4);let v=metadata(&out,&p)?;assert_eq!(v["result"]["rule_matches"][2]["kind"],"email");Ok(())
}
#[test]
fn document_section_node_and_selection_use_original_revision_and_source_coordinates()->R{
    let bytes=definition::package(&(para(1,"MARK MARK")+&para(2,"MARK")))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=drequest(&s,&bytes)?;let inv=inventory(&p,&good)?;
    let b=&inv["inventory"]["blocks"][0];let node=inv["inventory"]["nodes"].as_array().ok_or("nodes")?.iter().find(|n|n["source_handle"]==b["paragraph_handle"]).ok_or("node")?;
    for mode in 0..4{let mut v=good.clone();match mode{0=>{},1=>{v["selector"]["scope"]=json!("section");v["selector"]["section_ids"]=inv["inventory"]["section_ids"].clone();},
        2=>{v["selector"]["scope"]=json!("node_set");v["selector"]["range"]=json!({"node_ids":[node["node_id"]]});},_=>{v["selector"]["scope"]=json!("selection");v["selector"]["range"]=selection(&inv,5,9)?;}}
        assert_eq!(detection!(&p,&v)?.receipt().stored.matched_formats,if mode<2{3}else if mode==2{2}else{1});}Ok(())
}
#[test]
fn hidden_and_memo_policy_remains_explicit_and_author_metadata_is_not_exposed()->R{
    let bytes=definition::package(&review::body())?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=drequest(&s,&bytes)?;
    for(h,m,n)in [(false,false,2),(true,false,4),(false,true,4),(true,true,6)]{let mut v=good.clone();v["operation"]["rules"][0]["query"]=json!("K");v["operation"]["review_policy"]=json!({"include_hidden_explanations":h,"include_memo_bodies":m});
        let out=detection!(&p,&v)?;assert_eq!(out.receipt().stored.matched_formats,n);let text=out.with_verified_json(&p,5,|b|String::from_utf8_lossy(b).into_owned())?;assert!(!text.contains("PRIVATE-AUTHOR")&&!text.contains("MEMO K K"));}Ok(())
}
#[test]
fn required_request_operation_rule_and_selector_fields_reject_before_reads()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=drequest(&s,&bytes)?;let before=s.metadata.audit_events()?.len();
    for key in ["schema_version","idempotency_key","project_id","document_id","base_revision","expected_head_generation","expected_source_package_sha256","plan_id","selector","operation"]{let mut v=good.clone();v.as_object_mut().ok_or("root")?.remove(key);assert!(matches!(detection!(&p,&v),Err(DE::Request)));}
    for key in ["kind","rules","max_results","review_policy"]{let mut v=good.clone();v["operation"].as_object_mut().ok_or("operation")?.remove(key);assert!(matches!(detection!(&p,&v),Err(DE::Request)));}
    for key in ["rule_id","kind","query","regex","case_sensitive","whole_word"]{let mut v=good.clone();v["operation"]["rules"][0].as_object_mut().ok_or("rule")?.remove(key);assert!(matches!(detection!(&p,&v),Err(DE::Request)));}
    for key in ["scope","revision_id"]{let mut v=good.clone();v["selector"].as_object_mut().ok_or("scope")?.remove(key);assert!(matches!(detection!(&p,&v),Err(DE::Request)));}assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn mutation_preview_generic_filter_raw_graph_and_approval_fields_reject_before_reads()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=drequest(&s,&bytes)?;let before=s.metadata.audit_events()?.len();
    for key in ["replacement","preview_only","mask_policy","style_filter","direction","query","approved","raw_xml","whole_package_sanitized"]{let mut v=good.clone();v["operation"][key]=json!(false);assert!(matches!(detection!(&p,&v),Err(DE::Request)));}
    for key in ["source_path","approved","graph"]{let mut v=good.clone();v[key]=json!({});assert!(matches!(detection!(&p,&v),Err(DE::Request)));}
    let mut v=good;v["operation"]["rules"][0]["replacement"]=json!("***");assert!(matches!(detection!(&p,&v),Err(DE::Request)));assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn enum_object_forms_unknown_kinds_nulls_wrong_boolean_types_and_schema_reject_before_reads()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=drequest(&s,&bytes)?;let before=s.metadata.audit_events()?.len();
    for(key,value)in [("kind",json!({"find_personal_info_formats":null})),("rules",Value::Null),("rules",json!({})),("review_policy",json!([]))]{let mut v=good.clone();v["operation"][key]=value;assert!(matches!(detection!(&p,&v),Err(DE::Request)));}
    for(key,value)in [("kind",json!({"custom":null})),("kind",json!("native_auto")),("regex",json!("true")),("query",Value::Null)]{let mut v=good.clone();v["operation"]["rules"][0][key]=value;assert!(matches!(detection!(&p,&v),Err(DE::Request)));}
    let mut v=good;v["schema_version"]=json!("hwpx-agent.product-personal-info-format-detection-request/v2");assert!(matches!(detection!(&p,&v),Err(DE::Request)));assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn duplicate_escaped_keys_trailing_json_arrays_and_empty_envelopes_reject_before_reads()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=String::from_utf8(wire(&drequest(&s,&bytes)?)?)?;let before=s.metadata.audit_events()?.len();
    for text in [good.replace("\"regex\":false","\"regex\":false,\"r\\u0065gex\":true"),format!("{good} {{}}"),"null".into(),"[]".into(),"{}".into()]{assert!(matches!(Detect::prepare_json(&p,text.as_bytes(),Default::default(),4),Err(DE::Request)));}assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn exact_sixteen_kib_request_limit_preserves_canonical_binding_and_rejects_one_more_byte()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=drequest(&s,&bytes)?;let mut text=wire(&v)?;text.resize(16*1024,b' ');
    let padded=Detect::prepare_json(&p,&text,Default::default(),4)?;let ordinary=detection!(&p,&v)?;assert_eq!(padded.receipt().canonical_request_sha256,ordinary.receipt().canonical_request_sha256);assert_ne!(padded.continuation_receipt_sha256()?,ordinary.continuation_receipt_sha256()?);
    text.push(b' ');let before=s.metadata.audit_events()?.len();assert!(matches!(Detect::prepare_json(&p,&text,Default::default(),4),Err(DE::Limit)));assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn invalid_rule_ids_duplicate_ids_count_query_and_match_limits_reject_before_reads()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=drequest(&s,&bytes)?;let before=s.metadata.audit_events()?.len();
    for mode in 0..8{let mut v=good.clone();match mode{0=>v["operation"]["rules"]=json!([]),1=>v["operation"]["rules"][0]["query"]=json!(""),2=>v["operation"]["rules"][0]["rule_id"]=json!("../outside"),
        3=>v["operation"]["rules"]=json!([good["operation"]["rules"][0],good["operation"]["rules"][0]]),4=>v["operation"]["rules"][0]["query"]=json!("X".repeat(4097)),5=>v["operation"]["max_results"]=json!(0),6=>v["operation"]["max_results"]=json!(10001),
        _=>v["operation"]["rules"]=Value::Array((0..17).map(|i|{let mut r=good["operation"]["rules"][0].clone();r["rule_id"]=json!(format!("rule{i}"));r}).collect())}assert!(matches!(detection!(&p,&v),Err(DE::Request)));}
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn malformed_selector_shapes_revision_and_digest_reject_before_reads()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=drequest(&s,&bytes)?;let before=s.metadata.audit_events()?.len();
    for mode in 0..6{let mut v=good.clone();match mode{0=>v["selector"]["range"]=Value::Null,1=>v["selector"]["section_ids"]=json!([]),2=>v["selector"]["revision_id"]=json!(rev::RevisionId::generate().public_id()),
        3=>v["expected_head_generation"]=json!(0),4=>v["expected_source_package_sha256"]=json!("F".repeat(64)),_=>v["selector"]["scope"]=json!({"document":null})}assert!(matches!(detection!(&p,&v),Err(DE::Request)));}assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn source_digest_head_and_stale_index_are_not_rebound_to_a_different_original()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=drequest(&s,&bytes)?;
    for(key,value)in [("expected_source_package_sha256",json!("0".repeat(64))),("expected_head_generation",json!(s.head.generation()+1))]{let mut v=good.clone();v[key]=value;assert!(detection!(&p,&v).is_err());}
    let inv=inventory(&p,&good)?;let mut v=good;v["selector"]["scope"]=json!("selection");v["selector"]["range"]=selection(&inv,0,4)?;v["selector"]["range"]["index_sha256"]=json!("0".repeat(64));assert!(detection!(&p,&v).is_err());Ok(())
}
#[test]
fn document_write_is_required_for_initial_and_retained_metadata_navigation_and_selection()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let out=detection!(&p,&drequest(&s,&bytes)?)?;let reader=s.provider()?;let called=Cell::new(false);
    assert!(detection!(&reader,&drequest(&s,&bytes)?).is_err());assert!(out.verify(&reader,5).is_err());assert!(out.with_verified_json(&reader,5,|_|called.set(true)).is_err());
    assert!(out.with_next_verified_json(&reader,&wire(&next(&out,Value::Null,"forward",false)?)?,5,|_|called.set(true)).is_err());assert!(out.with_selection_verified_json(&reader,&wire(&select(&out,0)?)?,5,|_|called.set(true)).is_err());assert!(!called.get());Ok(())
}
#[test]
fn foreign_provider_five_scopes_cannot_deliver_retained_coordinates()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let out=detection!(&p,&drequest(&s,&bytes)?)?;let called=Cell::new(false);
    for mode in 0..5{let tenant=if mode==4{TenantId::new(Uuid::from_u128(997))?}else{s.reader.tenant_id()};let subject=if mode==3{SubjectDigest::from_authenticated_subject("foreign-detection")?}else{s.reader.subject()};
        let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);let context=rev::RevisionRequestContext::new(tenant,subject);let project=if mode==2{rev::ProjectId::parse("prj_70000000000000000000000000000003")?}else{s.project};let branch=if mode==1{rev::BranchId::parse("brn_70000000000000000000000000000003")?}else{s.branch};
        let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&context,project,branch,DocumentId::parse(if mode==0{"foreign-document"}else{"actual-form-document"})?)?;
        assert!(out.verify(&other,5).is_err());assert!(out.with_selection_verified_json(&other,&wire(&select(&out,0)?)?,5,|_|called.set(true)).is_err());}assert!(!called.get());Ok(())
}
#[test]
fn acl_revocation_blocks_all_delivery_paths_and_regrant_rechecks_current_access()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let out=detection!(&p,&drequest(&s,&bytes)?)?;
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;let called=Cell::new(false);assert!(out.verify(&p,6).is_err());assert!(out.with_verified_json(&p,6,|_|called.set(true)).is_err());
    assert!(out.with_next_verified_json(&p,&wire(&next(&out,Value::Null,"forward",false)?)?,6,|_|called.set(true)).is_err());assert!(out.with_selection_verified_json(&p,&wire(&select(&out,0)?)?,6,|_|called.set(true)).is_err());assert!(detection!(&p,&drequest(&s,&bytes)?).is_err());assert!(!called.get());
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;out.verify(&p,8)?;Ok(())
}
#[test]
fn quarantine_and_ciphertext_tamper_block_retained_selection_without_callbacks()->R{
    for tamper in [false,true]{let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let out=detection!(&p,&drequest(&s,&bytes)?)?;
        if tamper{s.blobs.tamper.store(true,Ordering::SeqCst);}else{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("DETECTION_TEST")?,5)?;}
        let called=Cell::new(false);assert!(out.verify(&p,6).is_err());assert!(out.with_verified_json(&p,6,|_|called.set(true)).is_err());assert!(out.with_selection_verified_json(&p,&wire(&select(&out,0)?)?,6,|_|called.set(true)).is_err());assert!(!called.get());assert!(detection!(&p,&drequest(&s,&bytes)?).is_err());}Ok(())
}
#[test]
fn navigation_is_bound_to_retained_receipt_and_moves_without_reapplying_patterns()->R{
    let bytes=raw("MARK MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let out=detection!(&p,&drequest(&s,&bytes)?)?;
    let a=out.with_next_verified_json(&p,&wire(&next(&out,Value::Null,"forward",false)?)?,5,|b|serde_json::from_slice::<Value>(b))??;assert_eq!(a["result"]["match_index"],0);
    let b=out.with_next_verified_json(&p,&wire(&next(&out,a["result"]["cursor"].clone(),"forward",false)?)?,5,|b|serde_json::from_slice::<Value>(b))??;assert_eq!(b["result"]["match_index"],1);
    let back=out.with_next_verified_json(&p,&wire(&next(&out,b["result"]["cursor"].clone(),"backward",false)?)?,5,|b|serde_json::from_slice::<Value>(b))??;assert_eq!(back["result"]["match_index"],0);
    let wrap=out.with_next_verified_json(&p,&wire(&next(&out,b["result"]["cursor"].clone(),"forward",true)?)?,5,|b|serde_json::from_slice::<Value>(b))??;assert_eq!(wrap["result"]["wrapped"],true);Ok(())
}
#[test]
fn another_key_plan_rule_or_raw_request_cannot_reuse_navigation_or_selection_binding()->R{
    let bytes=raw("MARK MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=drequest(&s,&bytes)?;let out=detection!(&p,&good)?;
    let first=out.with_next_verified_json(&p,&wire(&next(&out,Value::Null,"forward",false)?)?,5,|b|serde_json::from_slice::<Value>(b))??;
    for mode in 0..3{let mut v=good.clone();match mode{0=>v["idempotency_key"]=json!("other-key"),1=>v["plan_id"]=json!("other-plan"),_=>v["operation"]["rules"][0]["kind"]=json!("email")};let other=detection!(&p,&v)?;
        assert_ne!(other.continuation_receipt_sha256()?,out.continuation_receipt_sha256()?);assert!(other.with_next_verified_json(&p,&wire(&next(&out,first["result"]["cursor"].clone(),"forward",false)?)?,5,|_|()).is_err());assert!(other.with_selection_verified_json(&p,&wire(&select(&out,0)?)?,5,|_|()).is_err());}Ok(())
}
#[test]
fn malformed_followup_schemas_shapes_duplicate_keys_and_out_of_range_selection_fail_closed()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let out=detection!(&p,&drequest(&s,&bytes)?)?;let called=Cell::new(false);let good=next(&out,Value::Null,"forward",false)?;
    for mode in 0..5{let mut v=good.clone();match mode{0=>v["schema_version"]=json!(DS),1=>v["navigation"]=json!([]),2=>v["navigation"]["direction"]=json!("all"),3=>v["navigation"]["direction"]=json!({"forward":null}),_=>v["navigation"]["approved"]=json!(true)}assert!(out.with_next_verified_json(&p,&wire(&v)?,5,|_|called.set(true)).is_err());}
    let duplicate=String::from_utf8(wire(&good)?)?.replace("\"wrap\":false","\"wrap\":false,\"wr\\u0061p\":true");assert!(out.with_next_verified_json(&p,duplicate.as_bytes(),5,|_|called.set(true)).is_err());
    for index in [1,10000]{assert!(out.with_selection_verified_json(&p,&wire(&select(&out,index)?)?,5,|_|called.set(true)).is_err());}
    let mut v=select(&out,0)?;v["approved"]=json!(true);assert!(out.with_selection_verified_json(&p,&wire(&v)?,5,|_|called.set(true)).is_err());assert!(!called.get());Ok(())
}
#[test]
fn request_and_server_match_query_regex_and_response_limits_are_intersected()->R{
    let bytes=raw("MARK MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=drequest(&s,&bytes)?;v["operation"]["max_results"]=json!(1);assert!(detection!(&p,&v).is_err());v["operation"]["max_results"]=json!(10000);
    for config in [Config{matches:1,..Default::default()},Config{query_bytes:3,..Default::default()},Config{result_bytes:1,..Default::default()}]{assert!(Detect::prepare_json(&p,&wire(&v)?,SourceSearchLimits::new(config)?,4).is_err());}
    v["operation"]["rules"][0]["regex"]=json!(true);v["operation"]["rules"][0]["query"]=json!("M[AR]+K");assert!(Detect::prepare_json(&p,&wire(&v)?,SourceSearchLimits::new(Config{pattern_bytes:1,..Default::default()})?,4).is_err());Ok(())
}
#[test]
fn exact_entire_product_metadata_response_bound_and_one_byte_less_are_enforced()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=drequest(&s,&bytes)?;let out=detection!(&p,&v)?;let n=out.with_verified_json(&p,5,<[u8]>::len)?;
    let exact=Detect::prepare_json(&p,&wire(&v)?,SourceSearchLimits::new(Config{result_bytes:n,..Default::default()})?,4)?;assert_eq!(exact.with_verified_json(&p,5,<[u8]>::len)?,n);
    assert!(matches!(Detect::prepare_json(&p,&wire(&v)?,SourceSearchLimits::new(Config{result_bytes:n-1,..Default::default()})?,4),Err(DE::Stored(SE::Limit))));Ok(())
}
#[test]
fn invalid_regex_and_partial_nfc_candidate_do_not_produce_an_edit_selection()->R{
    let bytes=raw("\u{344}")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=drequest(&s,&bytes)?;v["operation"]["rules"][0]["regex"]=json!(true);v["operation"]["rules"][0]["query"]=json!("(");assert!(detection!(&p,&v).is_err());
    v["operation"]["rules"][0]["query"]=json!("\u{308}");let out=detection!(&p,&v)?;assert_eq!(out.receipt().stored.matched_formats,1);let called=Cell::new(false);assert!(out.with_selection_verified_json(&p,&wire(&select(&out,0)?)?,5,|_|called.set(true)).is_err());assert!(!called.get());Ok(())
}
#[test]
fn metadata_debug_and_followups_never_contain_private_rule_query_key_or_body()->R{
    let bytes=raw("PRIVATE-DETECTION-BODY")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=drequest(&s,&bytes)?;v["operation"]["rules"][0]["query"]=json!("PRIVATE-DETECTION-BODY");let out=detection!(&p,&v)?;
    let follow=out.with_selection_verified_json(&p,&wire(&select(&out,0)?)?,5,|b|String::from_utf8_lossy(b).into_owned())?;
    for text in [format!("{out:?}{:?}",out.receipt()),out.with_verified_json(&p,5,|b|String::from_utf8_lossy(b).into_owned())?,follow]{assert!(!text.contains("PRIVATE-")&&!text.contains("\"query\":")&&!text.contains("matched_value_sha256"));}Ok(())
}
#[test]
fn read_only_result_preserves_source_head_and_ingest_count_and_denies_execution_route()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let out=detection!(&p,&drequest(&s,&bytes)?)?;
    assert!(!out.receipt().idempotency_key_claimed&&!out.receipt().native_identity_cas_execution_publication_authority&&!out.receipt().stored.whole_package_personal_data_removed);
    assert!(matches!(out.require_current_product_route(&p,5),Err(DE::RouteUnqualified)));assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);
    assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);assert_eq!(s.artifacts.download(&s.reader,s.result,5)?,bytes);Ok(())
}
#[test]
fn source_artifact_and_unverified_scanner_are_not_reclassified_as_current_result()->R{
    let bytes=raw("MARK")?;for(kind,unverified)in [(ArtifactKind::Source,false),(ArtifactKind::Result,true)]{let s=StoredFixture::new(&bytes,kind,unverified)?;writer!(s,actor,p);assert!(detection!(&p,&drequest(&s,&bytes)?).is_err());}Ok(())
}
fn detection_race(stage:usize)->R{
    let bytes=raw("MARK MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=drequest(&s,&bytes)?;let out=detection!(&p,&v)?;
    let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,
        ContentDigest::of(b"detection-head-race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation fixture"),ContentDigest::of(b"transaction fixture"))?;
    let repo=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
    let bound=StoredFormProvider::bind(&s.artifacts,&repo,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;let nav=wire(&next(&out,Value::Null,"forward",false)?)?;let selection=wire(&select(&out,0)?)?;
    match stage{0=>{Detect::prepare_json(&bound,&wire(&v)?,Default::default(),5)?;},1=>{out.verify(&bound,5)?;},2=>{out.with_verified_json(&bound,5,|_|())?;},3=>{out.with_next_verified_json(&bound,&nav,5,|_|())?;},_=>{out.with_selection_verified_json(&bound,&selection,5,|_|())?;}}
    let count=repo.repository().calls.load(Ordering::SeqCst);assert!(count>=4);repo.repository().calls.store(0,Ordering::SeqCst);repo.repository().trigger.store(count,Ordering::SeqCst);let called=Cell::new(false);
    match stage{0=>assert!(Detect::prepare_json(&bound,&wire(&v)?,Default::default(),6).is_err()),1=>assert!(out.verify(&bound,6).is_err()),2=>assert!(out.with_verified_json(&bound,6,|_|called.set(true)).is_err()),3=>assert!(out.with_next_verified_json(&bound,&nav,6,|_|called.set(true)).is_err()),_=>assert!(out.with_selection_verified_json(&bound,&selection,6,|_|called.set(true)).is_err())}
    assert!(!called.get());assert_eq!(repo.repository().calls.load(Ordering::SeqCst),count);Ok(())
}
#[test]fn preparation_consumer_final_head_race_rejects()->R{detection_race(0)}
#[test]fn verify_consumer_final_head_race_rejects()->R{detection_race(1)}
#[test]fn metadata_consumer_final_head_race_rejects()->R{detection_race(2)}
#[test]fn navigation_consumer_final_head_race_rejects()->R{detection_race(3)}
#[test]fn selection_consumer_final_head_race_rejects()->R{detection_race(4)}
