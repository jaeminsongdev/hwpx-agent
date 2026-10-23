//! Assessed direct-formatting v9 search shares current stored access and retained navigation.
use super::*;
use hwpx_agent_cli::form_product_request::stored_source_search::{SourceSearchProductError as PE,
    selector::resolved_styles::{StoredResolvedStyleProductRequest as Resolved,PreparedStoredResolvedStyleProduct as Prepared,RESOLVED_STYLE_PRODUCT_REQUEST_SCHEMA as RES_SCHEMA}};
use hwpx_agent_cli::form_stored_provider::actual_import::source_search::StoredSourceSearchError as SE;
use hwpx_package::document_import::search::{inspection::definitions::resolved::SourceResolvedStyleFilter as Filter,
    reviews::selector::resolved_styles::SourceResolvedStyleSearchError as RE};
#[allow(dead_code)] #[path="../../../../hwpx-package/tests/support/search_definition_fixture.rs"] mod definition;
macro_rules! resolved {($provider:expr,$v:expr)=>{Resolved::prepare_json($provider,&wire($v)?,Default::default(),4)}}
#[path="character_detail_product.rs"] mod character_details;
#[path="paragraph_detail_product.rs"] mod paragraph_details;
fn body()->String {fixture::body().replace("<hp:p id='1'>","<hp:p id='1' paraPrIDRef='1' styleIDRef='0'>")
    .replace("<hp:p id='11'>","<hp:p id='11' paraPrIDRef='1' styleIDRef='0'>").replace("<hp:p id='12'>","<hp:p id='12' paraPrIDRef='1' styleIDRef='0'>")
    .replace("<hp:run>","<hp:run charPrIDRef='1'>")}
fn p(id:u32,text:&str)->String {format!("<hp:p id='{id}' paraPrIDRef='1' styleIDRef='0'><hp:run charPrIDRef='1'><hp:t>{text}</hp:t></hp:run></hp:p>")}
fn request(s:&StoredFixture,raw:&[u8])->Result<Value,Box<dyn Error>> {let mut v=envelope(s,raw)?;v["schema_version"]=json!(RES_SCHEMA);v["operation"]=json!({
    "kind":"find_resolved_style","query":"K","regex":false,"case_sensitive":true,"whole_word":false,"max_results":100,
    "style_filter":{"bold":true},"review_policy":policy(true,true)});Ok(v)}
fn data(out:&Prepared,provider:&Provider<'_>)->Result<Value,Box<dyn Error>> {Ok(out.with_verified_json(provider,5,|b|serde_json::from_slice(b))??)}
fn count(data:&Value)->Result<usize,Box<dyn Error>> {Ok(data["search"]["result"]["matches"].as_array().ok_or("matches")?.len())}
fn next(out:&Prepared,cursor:Value,direction:&str,wrap:bool)->Result<Value,Box<dyn Error>> {Ok(json!({
    "schema_version":"hwpx-agent.product-source-search-next-request/v1","search_receipt_sha256":out.navigation_receipt_sha256()?,
    "navigation":{"direction":direction,"wrap":wrap,"cursor":cursor}}))}
#[test]
fn resolved_product_discovery_four_scopes_and_owned_request_drop_preserve_selected_coverage()->TestResult {
    let raw=definition::package(&body())?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let base=request(&s,&raw)?;let inv=inventory(&provider,&base)?;
    let range=window(&inv,"memo_body",7,8)?;let node=inv["inventory"]["nodes"].as_array().ok_or("nodes")?.iter().find(|n|n["source_handle"]==range["start"]["paragraph_handle"]).ok_or("node")?;
    for(scope,total)in[("document",6),("section",6),("node_set",2),("selection",1)] {let mut v=base.clone();v["selector"]["scope"]=json!(scope);
        match scope {"section"=>v["selector"]["section_ids"]=inv["inventory"]["section_ids"].clone(),"node_set"=>v["selector"]["range"]=json!({"node_ids":[node["node_id"].clone()]}),"selection"=>v["selector"]["range"]=range.clone(),_=>{}}
        let out=resolved!(&provider,&v)?;drop(v);out.verify(&provider,5)?;let found=data(&out,&provider)?;assert_eq!(count(&found)?,total);
        assert_eq!(found["coverage"]["requested_character_axis_complete"],true);assert_eq!(out.receipt().stored.profile,"hwpx-agent.stored-source-search/v9");
    }Ok(())
}
#[test]
fn resolved_product_direct_values_false_and_combined_predicates_match_original_source()->TestResult {
    let raw=definition::package(&(p(1,"K")+&p(2,"K").replace("charPrIDRef='1'","charPrIDRef='0'").replace("paraPrIDRef='1'","paraPrIDRef='0'")))?;
    let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for(filter,total)in[(json!({"bold":true,"italic":true,"height_hwpunit":1000,"text_rgb":[0,0,0],"alignment":"right"}),1),
        (json!({"bold":false,"italic":false,"alignment":"justify"}),1),(json!({"bold":true,"alignment":"justify"}),0)] {
        let mut v=request(&s,&raw)?;v["operation"]["style_filter"]=filter;assert_eq!(count(&data(&resolved!(&provider,&v)?,&provider)?)?,total);
    }Ok(())
}
#[test]
fn resolved_product_unresolved_required_axes_remain_typed_errors_even_for_absent_queries()->TestResult {
    for body in[p(1,"K").replace("charPrIDRef='1'",""),p(1,"K").replace("<hp:t>","<hp:t charStyleIDRef='0'>"),p(1,"K").replace("paraPrIDRef='1'","")] {
        let raw=definition::package(&body)?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
        for query in["K","ABSENT"] {let mut v=request(&s,&raw)?;v["operation"]["query"]=json!(query);v["operation"]["style_filter"]=json!({"bold":true,"alignment":"right"});
            assert!(matches!(resolved!(&provider,&v),Err(PE::Stored(SE::Resolution(RE::Unresolved(_))))));
        }
    }Ok(())
}
#[test]
fn resolved_product_unrequested_axis_and_outside_scope_uncertainty_do_not_override_selected_contract()->TestResult {
    for(body,filter)in[(p(1,"K").replace("charPrIDRef='1'","").replace("<hp:t>","<hp:t charStyleIDRef='1'>"),json!({"alignment":"right"})),
        (p(1,"K").replace("paraPrIDRef='1'",""),json!({"bold":true}))] {
        let raw=definition::package(&body)?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=request(&s,&raw)?;v["operation"]["style_filter"]=filter;
        assert_eq!(count(&data(&resolved!(&provider,&v)?,&provider)?)?,1);
    }
    let raw=definition::package(&(p(1,"K")+&p(2,"BAD").replace("charPrIDRef='1'","")))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let mut v=request(&s,&raw)?;let inv=inventory(&provider,&v)?;let b=&inv["inventory"]["blocks"][0];let node=inv["inventory"]["nodes"].as_array().ok_or("nodes")?.iter().find(|n|n["source_handle"]==b["paragraph_handle"]).ok_or("node")?;
    v["selector"]["scope"]=json!("node_set");v["selector"]["range"]=json!({"node_ids":[node["node_id"].clone()]});assert_eq!(count(&data(&resolved!(&provider,&v)?,&provider)?)?,1);Ok(())
}
#[test]
fn resolved_product_four_body_policies_exclude_before_resolution_and_match_caps()->TestResult {
    let raw=definition::package(&body())?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut hashes=BTreeSet::new();
    for(h,m,total)in[(false,false,2),(true,false,4),(false,true,4),(true,true,6)] {let mut v=request(&s,&raw)?;v["operation"]["review_policy"]=policy(h,m);v["operation"]["max_results"]=json!(total);
        let out=resolved!(&provider,&v)?;hashes.insert(out.receipt().stored.query_sha256);assert_eq!(count(&data(&out,&provider)?)?,total);
    }assert_eq!(hashes.len(),4);
    let raw=definition::package(&body().replace("<hp:t>HIDDEN","<hp:t charStyleIDRef='1'>HIDDEN"))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=request(&s,&raw)?;
    assert!(matches!(resolved!(&provider,&v),Err(PE::Stored(SE::Resolution(RE::Unresolved(_))))));v["operation"]["review_policy"]=policy(false,false);
    assert_eq!(count(&data(&resolved!(&provider,&v)?,&provider)?)?,2);Ok(())
}
#[test]
fn resolved_product_closed_required_shapes_values_and_decoded_duplicates_reject_before_reads()->TestResult {
    let raw=definition::package(&p(1,"K"))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=request(&s,&raw)?;let before=s.metadata.audit_events()?.len();let mut bad=vec![b"null".to_vec(),b"[]".to_vec()];
    for key in["schema_version","idempotency_key","project_id","document_id","base_revision","expected_head_generation","expected_source_package_sha256","plan_id","selector","operation"] {
        let mut v=good.clone();v.as_object_mut().ok_or("envelope")?.remove(key);bad.push(wire(&v)?);
    }
    for key in["kind","query","regex","case_sensitive","whole_word","max_results","style_filter","review_policy"] {let mut v=good.clone();v["operation"].as_object_mut().ok_or("operation")?.remove(key);bad.push(wire(&v)?);}
    for filter in[json!({}),json!(null),json!([]),json!({"bold":1}),json!({"bold":true,"character_source":"run_property"}),json!({"height_hwpunit":-1}),json!({"text_rgb":[256,0,0]}),json!({"alignment":"unknown"}),json!({"approved":true})] {
        let mut v=good.clone();v["operation"]["style_filter"]=filter;bad.push(wire(&v)?);
    }
    for(key,value)in[("kind",json!("find_style")),("query",json!("")),("query",json!("Q".repeat(4097))),("regex",json!(1)),("max_results",json!(0)),("max_results",json!(10001)),
        ("include_hidden",json!(true)),("preview_only",json!(false)),("review_policy",json!({"include_memo_bodies":true}))] {let mut v=good.clone();v["operation"][key]=value;bad.push(wire(&v)?);}
    for(key,value)in[("approved",json!(true)),("source_graph",json!({})),("expected_head_generation",json!(0)),("expected_source_package_sha256",json!("A".repeat(64)))] {let mut v=good.clone();v[key]=value;bad.push(wire(&v)?);}
    let mut v=good.clone();v["selector"]["revision_id"]=json!(rev::RevisionId::generate().public_id());bad.push(wire(&v)?);
    let text=serde_json::to_string(&good)?;for(from,to)in[("\"bold\":true","\"bold\":true,\"bo\\u006cd\":false"),("\"regex\":false","\"regex\":false,\"reg\\u0065x\":true")] {let v=text.replace(from,to);assert_ne!(v,text);bad.push(v.into_bytes());}
    for raw in bad {assert!(matches!(Resolved::prepare_json(&provider,&raw,Default::default(),4),Err(PE::Request)));}assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn resolved_product_old_search_v1_through_v8_and_new_v9_do_not_accept_each_others_operations()->TestResult {
    use hwpx_agent_cli::form_product_request::stored_source_search::{StoredSourceSearchProductRequest as Old,selector::{StoredSourceScopeProductRequest as V5,
        review::StoredReviewScopeProductRequest as V6,styles::StoredSelectorStyleProductRequest as V7,controls::StoredSelectorControlProductRequest as V8}};
    let raw=definition::package(&p(1,"K"))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=request(&s,&raw)?;let before=s.metadata.audit_events()?.len();
    for version in 1..=9 {let mut v=good.clone();v["schema_version"]=json!(format!("hwpx-agent.product-source-search-request/v{version}"));let raw=wire(&v)?;
        assert!(Old::prepare_json(&provider,&raw,Default::default(),4).is_err());assert!(V5::prepare_json(&provider,&raw,Default::default(),4).is_err());
        assert!(V6::prepare_json(&provider,&raw,Default::default(),4).is_err());assert!(V7::prepare_json(&provider,&raw,Default::default(),4).is_err());assert!(V8::prepare_json(&provider,&raw,Default::default(),4).is_err());
        if version<9{assert!(matches!(Resolved::prepare_json(&provider,&raw,Default::default(),4),Err(PE::Request)));}
    }
    for kind in["find_style","find_literal","find_control","scope_inventory"] {let mut v=good.clone();v["operation"]["kind"]=json!(kind);assert!(matches!(resolved!(&provider,&v),Err(PE::Request)));}
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn resolved_product_exact_16k_raw_canonical_scope_key_plan_predicate_and_policy_bindings_are_distinct()->TestResult {
    let raw=definition::package(&body())?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=request(&s,&raw)?;let out=resolved!(&provider,&good)?;
    let mut padded=wire(&good)?;padded.resize(16*1024,b' ');let other=Resolved::prepare_json(&provider,&padded,Default::default(),4)?;
    assert_ne!(out.receipt().raw_request_sha256,other.receipt().raw_request_sha256);assert_eq!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);
    padded.push(b' ');assert!(matches!(Resolved::prepare_json(&provider,&padded,Default::default(),4),Err(PE::Limit)));assert!(matches!(Resolved::prepare_json(&provider,b"",Default::default(),4),Err(PE::Limit)));
    for(key,value)in[("idempotency_key",json!("OTHER-KEY")),("plan_id",json!("other-plan"))] {let mut v=good.clone();v[key]=value;let other=resolved!(&provider,&v)?;
        assert_ne!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);assert_ne!(out.receipt().scoped_request_sha256,other.receipt().scoped_request_sha256);assert_eq!(out.receipt().stored.result_sha256,other.receipt().stored.result_sha256);
    }
    let mut v=good.clone();v["operation"]["style_filter"]=json!({"italic":true});let other=resolved!(&provider,&v)?;assert_ne!(out.receipt().stored.query_sha256,other.receipt().stored.query_sha256);
    v["operation"]["review_policy"]=policy(false,false);assert_ne!(out.receipt().canonical_request_sha256,resolved!(&provider,&v)?.receipt().canonical_request_sha256);Ok(())
}
#[test]
fn resolved_product_current_write_and_five_foreign_scopes_deny_full_result_and_navigation()->TestResult {
    let raw=definition::package(&p(1,"K"))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=request(&s,&raw)?;let reader=s.provider()?;assert!(resolved!(&reader,&v).is_err());
    let out=resolved!(&provider,&v)?;let called=Cell::new(false);let continuation=wire(&next(&out,Value::Null,"forward",false)?)?;
    assert!(out.with_verified_json(&reader,5,|_|called.set(true)).is_err());assert!(out.with_next_verified_json(&reader,&continuation,5,|_|called.set(true)).is_err());
    let source=reader.import_actual_forms(s.head,4)?;assert!(matches!(source.into_resolved_style_search(&reader,Query {mode:Mode::Literal,..query("K")},Scope::Document,all(),Filter {bold:Some(true),..Default::default()},Default::default(),4),Err(SE::Permission)));
    for variant in 0..5 {let tenant=if variant==4{TenantId::new(Uuid::from_u128(997))?}else{s.reader.tenant_id()};let subject=if variant==3{SubjectDigest::from_authenticated_subject("foreign-resolved-style")?}else{s.reader.subject()};
        let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);let context=rev::RevisionRequestContext::new(tenant,subject);
        let project=if variant==2{rev::ProjectId::parse("prj_70000000000000000000000000000002")?}else{s.project};let branch=if variant==1{rev::BranchId::parse("brn_70000000000000000000000000000002")?}else{s.branch};
        let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&context,project,branch,DocumentId::parse(if variant==0{"foreign-document"}else{"actual-form-document"})?)?;
        assert!(out.verify(&other,5).is_err());assert!(out.with_verified_json(&other,5,|_|called.set(true)).is_err());assert!(out.with_next_verified_json(&other,&continuation,5,|_|called.set(true)).is_err());
    }assert!(!called.get());Ok(())
}
#[test]
fn resolved_product_acl_revoke_regrant_quarantine_and_aead_deny_retained_and_new_searches()->TestResult {
    for mode in 0..3 {let raw=definition::package(&p(1,"K"))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=request(&s,&raw)?;let out=resolved!(&provider,&v)?;let continuation=wire(&next(&out,Value::Null,"forward",false)?)?;
        match mode {0=>{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;},1=>{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("RESOLVED_STYLE_TEST")?,5)?;},_=>s.blobs.tamper.store(true,Ordering::SeqCst)}
        let called=Cell::new(false);assert!(out.verify(&provider,6).is_err());assert!(out.with_verified_json(&provider,6,|_|called.set(true)).is_err());assert!(out.with_next_verified_json(&provider,&continuation,6,|_|called.set(true)).is_err());assert!(resolved!(&provider,&v).is_err());assert!(!called.get());
        if mode==0{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;out.verify(&provider,8)?;out.with_next_verified_json(&provider,&continuation,8,|_|())?;}
    }Ok(())
}
#[test]
fn resolved_product_prepare_verify_json_and_next_final_head_races_block_consumers()->TestResult {
    for stage in 0..4 {let raw=definition::package(&p(1,"K"))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=request(&s,&raw)?;let request=wire(&v)?;let out=resolved!(&provider,&v)?;let continuation=wire(&next(&out,Value::Null,"forward",false)?)?;
        let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,ContentDigest::of(b"resolved race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation"),ContentDigest::of(b"transaction"))?;
        let b=rev::RevisionService::new(BoundaryRepo {inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
        let bound=StoredFormProvider::bind(&s.artifacts,&b,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
        match stage {0=>{Resolved::prepare_json(&bound,&request,Default::default(),5)?;},1=>{out.verify(&bound,5)?;},2=>{out.with_verified_json(&bound,5,|_|())?;},_=>{out.with_next_verified_json(&bound,&continuation,5,|_|())?;}}
        let calls=b.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);b.repository().calls.store(0,Ordering::SeqCst);b.repository().trigger.store(calls,Ordering::SeqCst);let called=Cell::new(false);
        match stage {0=>assert!(Resolved::prepare_json(&bound,&request,Default::default(),6).is_err()),1=>assert!(out.verify(&bound,6).is_err()),2=>assert!(out.with_verified_json(&bound,6,|_|called.set(true)).is_err()),_=>assert!(out.with_next_verified_json(&bound,&continuation,6,|_|called.set(true)).is_err())}
        assert!(!called.get());assert_eq!(b.repository().calls.load(Ordering::SeqCst),calls);
    }Ok(())
}
#[test]
fn resolved_product_owned_direct_stored_and_json_requests_share_original_receipt_and_bytes()->TestResult {
    let raw=definition::package(&p(1,"K"))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=request(&s,&raw)?;let out=resolved!(&provider,&v)?;
    let stored=provider.import_actual_forms(s.head,4)?.into_resolved_style_search(&provider,Query {mode:Mode::Literal,..query("K")},Scope::Document,all(),Filter {bold:Some(true),..Default::default()},Default::default(),4)?;
    assert_eq!(stored.verify(&provider,5)?,out.receipt().stored);assert_eq!(stored.with_verified_json(&provider,5,<[u8]>::to_vec)?,out.with_verified_json(&provider,5,<[u8]>::to_vec)?);Ok(())
}
#[test]
fn resolved_product_retained_navigation_forward_backward_exhaustion_and_wrap_are_exact()->TestResult {
    let raw=definition::package(&p(1,"K K"))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let out=resolved!(&provider,&request(&s,&raw)?)?;
    let first:Value=out.with_next_verified_json(&provider,&wire(&next(&out,Value::Null,"forward",false)?)?,5,|b|serde_json::from_slice(b))??;assert_eq!(first["match_index"],0);
    let second:Value=out.with_next_verified_json(&provider,&wire(&next(&out,first["cursor"].clone(),"forward",false)?)?,5,|b|serde_json::from_slice(b))??;assert_eq!(second["match_index"],1);
    let exhausted:Value=out.with_next_verified_json(&provider,&wire(&next(&out,second["cursor"].clone(),"forward",false)?)?,5,|b|serde_json::from_slice(b))??;assert_eq!(exhausted["exhausted"],true);
    let wrapped:Value=out.with_next_verified_json(&provider,&wire(&next(&out,second["cursor"].clone(),"forward",true)?)?,5,|b|serde_json::from_slice(b))??;assert_eq!(wrapped["match_index"],0);assert_eq!(wrapped["wrapped"],true);
    let backward:Value=out.with_next_verified_json(&provider,&wire(&next(&out,second["cursor"].clone(),"backward",false)?)?,5,|b|serde_json::from_slice(b))??;assert_eq!(backward["match_index"],0);assert_eq!(backward["region"],"body_and_notes");Ok(())
}
#[test]
fn resolved_product_next_parser_is_strict_bounded_and_receipt_cursor_bound_before_reads()->TestResult {
    let raw=definition::package(&p(1,"K K"))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=request(&s,&raw)?;let out=resolved!(&provider,&good)?;let valid=next(&out,Value::Null,"forward",false)?;
    let mut padded=wire(&valid)?;padded.resize(16*1024,b' ');out.with_next_verified_json(&provider,&padded,5,|_|())?;padded.push(b' ');
    assert!(matches!(out.with_next_verified_json(&provider,&padded,5,|_|()),Err(PE::Limit)));let before=s.metadata.audit_events()?.len();let called=Cell::new(false);
    for v in[json!(null),json!([]),json!({}),json!({"schema_version":"bad","search_receipt_sha256":"0".repeat(64),"navigation":{}})] {assert!(out.with_next_verified_json(&provider,&wire(&v)?,5,|_|called.set(true)).is_err());}
    let text=serde_json::to_string(&valid)?;let duplicate=text.replace("\"wrap\":false","\"wrap\":false,\"wr\\u0061p\":true");assert_ne!(duplicate,text);
    assert!(matches!(out.with_next_verified_json(&provider,duplicate.as_bytes(),5,|_|called.set(true)),Err(PE::Request)));assert_eq!(s.metadata.audit_events()?.len(),before);
    let first:Value=out.with_next_verified_json(&provider,&wire(&valid)?,5,|b|serde_json::from_slice(b))??;let mut v=good.clone();v["plan_id"]=json!("other-plan");let other=resolved!(&provider,&v)?;
    assert!(other.with_next_verified_json(&provider,&wire(&next(&out,first["cursor"].clone(),"forward",false)?)?,5,|_|called.set(true)).is_err());
    assert!(other.with_next_verified_json(&provider,&wire(&next(&other,first["cursor"].clone(),"forward",false)?)?,5,|_|called.set(true)).is_err());assert!(!called.get());Ok(())
}
#[test]
fn resolved_product_wrong_source_head_document_project_and_index_reject_preparation()->TestResult {
    let raw=definition::package(&p(1,"K"))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=request(&s,&raw)?;
    for(key,value)in[("expected_head_generation",json!(s.head.generation()+1)),("expected_source_package_sha256",json!("0".repeat(64))),("document_id",json!("foreign-document")),("project_id",json!("prj_70000000000000000000000000000002"))] {let mut v=good.clone();v[key]=value;assert!(resolved!(&provider,&v).is_err());}
    let inv=inventory(&provider,&good)?;let mut v=good;v["selector"]["scope"]=json!("selection");let b=&inv["inventory"]["blocks"][0];v["selector"]["range"]=json!({"coordinate_space":"index_nfc_unicode_scalars","index_sha256":"0".repeat(64),
        "start":{"paragraph_handle":b["paragraph_handle"],"block_index":b["block_index"],"normalized_scalar":0},"end":{"paragraph_handle":b["paragraph_handle"],"block_index":b["block_index"],"normalized_scalar":1}});
    assert!(resolved!(&provider,&v).is_err());Ok(())
}
#[test]
fn resolved_product_exact_output_budget_match_and_pattern_limits_reject_without_truncation()->TestResult {
    let raw=definition::package(&p(1,"K K"))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=request(&s,&raw)?;let out=resolved!(&provider,&good)?;let bytes=out.with_verified_json(&provider,5,<[u8]>::to_vec)?;
    let exact=Resolved::prepare_json(&provider,&wire(&good)?,SourceSearchLimits::new(Config {result_bytes:bytes.len(),..Default::default()})?,4)?;
    assert_eq!(exact.with_verified_json(&provider,5,<[u8]>::to_vec)?,bytes);assert!(Resolved::prepare_json(&provider,&wire(&good)?,SourceSearchLimits::new(Config {result_bytes:bytes.len()-1,..Default::default()})?,4).is_err());
    let mut v=good.clone();v["operation"]["max_results"]=json!(1);assert!(resolved!(&provider,&v).is_err());v["operation"]["max_results"]=json!(100);v["operation"]["regex"]=json!(true);v["operation"]["query"]=json!("(");assert!(resolved!(&provider,&v).is_err());Ok(())
}
#[test]
fn resolved_product_entities_cross_run_nfc_regex_and_original_contributors_are_preserved()->TestResult {
    for mixed in[false,true] {let body=format!("<hp:p id='1' paraPrIDRef='1' styleIDRef='0'><hp:run charPrIDRef='1'><hp:t>Xᄀ</hp:t></hp:run><hp:run charPrIDRef='{}'><hp:t>ᅡᆨY&#x1F600;</hp:t></hp:run></hp:p>",if mixed{0}else{1});
        let raw=definition::package(&body)?;let original=ContentDigest::of(&raw);let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=request(&s,&raw)?;v["operation"]["query"]=json!("각");
        let found=data(&resolved!(&provider,&v)?,&provider)?;assert_eq!(count(&found)?,usize::from(!mixed));assert_eq!(found["coverage"]["observed_segment_visits"],2);assert_eq!(ContentDigest::of(&raw),original);
    }Ok(())
}
#[test]
fn resolved_product_many_matches_share_one_assessment_per_original_segment()->TestResult {
    let body=(0..128).map(|_|"<hp:run charPrIDRef='1'><hp:t>K</hp:t></hp:run>").collect::<String>();let raw=definition::package(&format!("<hp:p id='1' paraPrIDRef='1' styleIDRef='0'>{body}</hp:p>"))?;
    let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=request(&s,&raw)?;v["operation"]["max_results"]=json!(128);let found=data(&resolved!(&provider,&v)?,&provider)?;
    assert_eq!(count(&found)?,128);assert_eq!(found["coverage"]["selected_text_segments"],128);assert_eq!(found["coverage"]["observed_segment_visits"],128);Ok(())
}
#[test]
fn resolved_product_privacy_original_head_ingest_and_closed_execution_route_remain_unchanged()->TestResult {
    let raw=definition::package(&body())?;let original=ContentDigest::of(&raw);let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=request(&s,&raw)?;v["operation"]["query"]=json!("PRIVATE-QUERY");let out=resolved!(&provider,&v)?;
    let text=String::from_utf8(out.with_verified_json(&provider,5,<[u8]>::to_vec)?)?;for secret in["PRIVATE-QUERY","PRIVATE-AUTHOR","CACHE FROZEN"] {assert!(!text.contains(secret));assert!(!format!("{out:?}{:?}",out.receipt()).contains(secret));}
    assert!(matches!(out.require_current_product_route(&provider,5),Err(PE::RouteUnqualified)));assert!(!out.receipt().idempotency_key_claimed&&!out.receipt().full_search_product_native_cas_execution_publication_authority);
    assert_eq!(ContentDigest::of(&raw),original);assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
}
#[test]
fn resolved_product_empty_selection_and_zero_width_do_not_invent_source_style_matches()->TestResult {
    let raw=definition::package(&body())?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=request(&s,&raw)?;let inv=inventory(&provider,&v)?;
    v["selector"]["scope"]=json!("selection");v["selector"]["range"]=window(&inv,"memo_body",8,8)?;v["operation"]["query"]=json!("^|$");v["operation"]["regex"]=json!(true);
    let found=data(&resolved!(&provider,&v)?,&provider)?;assert_eq!(count(&found)?,0);assert_eq!(found["coverage"]["selected_text_segments"],0);Ok(())
}
#[path="resolved_style_control_product.rs"] mod control_context;
