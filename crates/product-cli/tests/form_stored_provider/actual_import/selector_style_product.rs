use super::*;
use hwpx_agent_cli::form_product_request::stored_source_search::{SourceSearchProductError as E,
    selector::{review::StoredReviewScopeProductRequest as Discovery,styles::{StoredSelectorStyleProductRequest as Product,
        PreparedStoredSelectorStyleProduct as Prepared,SELECTOR_STYLE_PRODUCT_REQUEST_SCHEMA as SCHEMA}},navigation::SOURCE_SEARCH_NEXT_REQUEST_SCHEMA as NEXT};
use hwpx_package::document_import::search::{SourceSearchLimits,SourceSearchLimitConfig as Config};
use serde_json::{json,Value};
use std::{cell::Cell,sync::atomic::AtomicUsize};
use revision_service as rev;
#[path="../../../../hwpx-package/tests/support/review_style_fixture.rs"] mod fixture;
macro_rules! write_provider{($s:ident,$actor:ident,$p:ident)=>{
    let $actor=RequestContext::new($s.reader.tenant_id(),$s.reader.subject(),[AuthScope::DocumentRead,AuthScope::DocumentWrite]);
    let $p=StoredFormProvider::bind(&$s.artifacts,&$s.revisions,&$actor,&$s.revision_context,$s.project,$s.branch,DocumentId::parse("actual-form-document")?)?;
}}
macro_rules! prepare{($p:expr,$v:expr)=>{Product::prepare_json($p,&wire($v)?,Default::default(),4)}}
macro_rules! response{($p:expr,$v:expr)=>{{let out=prepare!($p,$v)?;let value:Value=out.with_verified_json($p,5,|b|serde_json::from_slice(b))??;value}}}
fn wire(v:&Value)->Result<Vec<u8>,serde_json::Error>{serde_json::to_vec(v)}
fn policy(h:bool,m:bool)->Value{json!({"include_hidden_explanations":h,"include_memo_bodies":m})}
fn filter(definition:bool)->Value{if definition{json!({"kind":"definition","filter":{"character_source":"run_property","bold":true}})}else{json!({"kind":"declared","filter":{"run_character_property":1}})}}
fn envelope(s:&StoredFixture,raw:&[u8],definition:bool)->Result<Value,Box<dyn Error>>{let revision=s.head.revision_id().ok_or("head")?.public_id();Ok(json!({
    "schema_version":SCHEMA,"idempotency_key":"PRIVATE-STYLE-KEY","plan_id":"selector-style-plan","project_id":s.project.public_id(),"document_id":"actual-form-document","base_revision":revision,
    "expected_head_generation":s.head.generation(),"expected_source_package_sha256":ContentDigest::of(raw).hex(),"selector":{"revision_id":revision,"scope":"document"},
    "operation":{"kind":"find_style","query":"K","regex":false,"case_sensitive":true,"whole_word":false,"max_results":100,"style_filter":filter(definition),"review_policy":policy(true,true)}}))}
fn inventory(p:&Provider<'_>,base:&Value)->Result<Value,Box<dyn Error>>{let mut v=base.clone();v["schema_version"]=json!("hwpx-agent.product-source-search-request/v6");v["operation"]=json!({"kind":"scope_inventory"});
    let out=Discovery::prepare_json(p,&wire(&v)?,Default::default(),4)?;Ok(out.with_verified_json(p,5,|b|serde_json::from_slice(b))??)}
fn selection(inv:&Value,region:&str,scalar:usize)->Result<Value,Box<dyn Error>>{let n=inv["block_regions"].as_array().ok_or("regions")?.iter().position(|v|v==region).ok_or("region")?;
    let b=&inv["inventory"]["blocks"][n];let hash:[u8;32]=serde_json::from_value(inv["inventory"]["index"]["index_sha256"].clone())?;
    Ok(json!({"coordinate_space":"index_nfc_unicode_scalars","index_sha256":hex::encode(hash),"start":{"paragraph_handle":b["paragraph_handle"],"block_index":b["block_index"],"normalized_scalar":scalar},
        "end":{"paragraph_handle":b["paragraph_handle"],"block_index":b["block_index"],"normalized_scalar":scalar+1}}))}
fn next(p:&Prepared,cursor:Value,wrap:bool)->Result<Value,Box<dyn Error>>{Ok(json!({"schema_version":NEXT,"search_receipt_sha256":p.navigation_receipt_sha256()?,"navigation":{"direction":"forward","wrap":wrap,"cursor":cursor}}))}
#[test]
fn selector_style_product_both_filter_families_use_discovery_for_all_four_scopes_without_caller_import()->TestResult{
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let inv=inventory(&p,&envelope(&s,&raw,false)?)?;let range=selection(&inv,"memo_body",7)?;
    let node=inv["inventory"]["nodes"].as_array().ok_or("nodes")?.iter().find(|n|n["source_handle"]==range["start"]["paragraph_handle"]).ok_or("node")?;
    for definition in[false,true]{for(scope,count)in[("document",4),("section",4),("node_set",2),("selection",1)]{let mut v=envelope(&s,&raw,definition)?;v["selector"]["scope"]=json!(scope);
        match scope{"section"=>v["selector"]["section_ids"]=inv["inventory"]["section_ids"].clone(),"node_set"=>v["selector"]["range"]=json!({"node_ids":[node["node_id"].clone()]}),"selection"=>v["selector"]["range"]=range.clone(),_=>{}}
        let out=prepare!(&p,&v)?;out.verify(&p,5)?;let value:Value=out.with_verified_json(&p,5,|b|serde_json::from_slice(b))??;
        assert_eq!(value["search"]["result"]["matches"].as_array().ok_or("matches")?.len(),count);assert_eq!(value["definitions"].is_object(),definition);
        assert_eq!(out.receipt().profile,"hwpx-agent.product-source-search-preparation/v7");assert_eq!(out.receipt().stored.profile,"hwpx-agent.stored-source-search/v7");assert_eq!(out.receipt().capability_id,"search.find_style");}}
    Ok(())
}
#[test]
fn selector_style_product_regex_clips_before_matching_and_zero_width_has_no_style_contributors()->TestResult{
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let inv=inventory(&p,&envelope(&s,&raw,false)?)?;
    for definition in[false,true]{let mut v=envelope(&s,&raw,definition)?;v["selector"]["scope"]=json!("selection");v["selector"]["range"]=selection(&inv,"memo_body",7)?;
        v["operation"]["regex"]=json!(true);v["operation"]["query"]=json!("^K$");v["operation"]["max_results"]=json!(1);let out=response!(&p,&v);
        assert_eq!(out["search"]["result"]["matches"].as_array().ok_or("matches")?.len(),1);assert_eq!(out["search"]["result"]["matches"][0]["start_normalized_scalar"],7);
        v["operation"]["query"]=json!("^|$");assert!(response!(&p,&v)["search"]["result"]["matches"].as_array().ok_or("matches")?.is_empty());}
    Ok(())
}
#[test]
fn selector_style_product_four_policies_and_predicates_exclude_before_result_caps()->TestResult{
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
    for definition in[false,true]{let mut digests=BTreeSet::new();for(h,m,count)in[(false,false,2),(true,false,2),(false,true,4),(true,true,4)]{let mut v=envelope(&s,&raw,definition)?;v["operation"]["review_policy"]=policy(h,m);v["operation"]["max_results"]=json!(count);
        let out=prepare!(&p,&v)?;digests.insert(out.receipt().canonical_request_sha256.clone());let value:Value=out.with_verified_json(&p,5,|b|serde_json::from_slice(b))??;assert_eq!(value["search"]["result"]["matches"].as_array().ok_or("matches")?.len(),count);}assert_eq!(digests.len(),4);}
    Ok(())
}
#[test]
fn selector_style_product_strict_envelope_axes_policy_shapes_duplicates_and_revision_reject_before_reads()->TestResult{
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=envelope(&s,&raw,false)?;let before=s.metadata.audit_events()?.len();let mut bad=vec![b"null".to_vec(),b"[]".to_vec(),format!("{} {{}}",serde_json::to_string(&good)?).into_bytes()];
    for key in["schema_version","idempotency_key","plan_id","project_id","document_id","base_revision","expected_head_generation","expected_source_package_sha256","selector","operation"]{let mut v=good.clone();v.as_object_mut().ok_or("object")?.remove(key);bad.push(wire(&v)?);}
    for key in["kind","query","regex","case_sensitive","whole_word","max_results","style_filter","review_policy"]{let mut v=good.clone();v["operation"].as_object_mut().ok_or("operation")?.remove(key);bad.push(wire(&v)?);}
    for f in[json!(null),json!([]),json!({"kind":"declared","filter":{}}),json!({"kind":"declared","filter":{"run_character_property":1},"approved":true}),json!({"kind":"definition","filter":{"bold":true}}),json!({"kind":"definition","filter":{"character_source":"run_property"}}),json!({"kind":"other","filter":{}})]{let mut v=good.clone();v["operation"]["style_filter"]=f;bad.push(wire(&v)?);}
    for f in[json!(null),json!([]),json!({}),json!({"include_hidden_explanations":true}),json!({"include_hidden_explanations":true,"include_memo_bodies":1}),json!({"include_hidden_explanations":true,"include_memo_bodies":true,"allow_cache":true})]{let mut v=good.clone();v["operation"]["review_policy"]=f;bad.push(wire(&v)?);}
    for(key,value)in[("kind",json!("find_control")),("query",json!("")),("query",json!("q".repeat(4097))),("regex",json!(1)),("max_results",json!(0)),("max_results",json!(10001)),("include_hidden",json!(true)),("native_verified",json!(true))]{let mut v=good.clone();v["operation"][key]=value;bad.push(wire(&v)?);}
    for sel in[json!([]),json!({"scope":"document"}),json!({"revision_id":good["base_revision"],"scope":"document","range":null}),json!({"revision_id":good["base_revision"],"scope":"section","section_ids":[]}),json!({"revision_id":rev::RevisionId::generate().public_id(),"scope":"document"})]{let mut v=good.clone();v["selector"]=sel;bad.push(wire(&v)?);}
    for(key,value)in[("scope",json!({})),("operation",json!([])),("approved",json!(true)),("expected_head_generation",json!(0)),("expected_source_package_sha256",json!("A".repeat(64)))]{let mut v=good.clone();v[key]=value;bad.push(wire(&v)?);}
    let text=serde_json::to_string(&good)?;for(from,to)in[("\"regex\":false","\"regex\":false,\"reg\\u0065x\":true"),("\"scope\":\"document\"","\"scope\":\"document\",\"sco\\u0070e\":\"selection\"")]{let v=text.replace(from,to);assert_ne!(v,text);bad.push(v.into_bytes());}
    for raw in bad{assert!(matches!(Product::prepare_json(&p,&raw,Default::default(),4),Err(E::Request)));}assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn selector_style_product_exact_16k_raw_canonical_key_plan_filter_and_policy_bindings()->TestResult{
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=envelope(&s,&raw,false)?;let out=prepare!(&p,&good)?;let mut padded=wire(&good)?;padded.resize(16*1024,b' ');
    let exact=Product::prepare_json(&p,&padded,Default::default(),4)?;assert_ne!(out.receipt().raw_request_sha256,exact.receipt().raw_request_sha256);assert_eq!(out.receipt().canonical_request_sha256,exact.receipt().canonical_request_sha256);
    padded.push(b' ');assert!(matches!(Product::prepare_json(&p,&padded,Default::default(),4),Err(E::Limit)));assert!(matches!(Product::prepare_json(&p,b"",Default::default(),4),Err(E::Limit)));
    for(key,value)in[("idempotency_key",json!("OTHER-KEY")),("plan_id",json!("other-plan"))]{let mut v=good.clone();v[key]=value;let other=prepare!(&p,&v)?;assert_ne!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);assert_ne!(out.receipt().scoped_request_sha256,other.receipt().scoped_request_sha256);assert_eq!(out.receipt().stored.result_sha256,other.receipt().stored.result_sha256);}
    let mut v=good.clone();v["operation"]["style_filter"]=filter(true);let other=prepare!(&p,&v)?;assert_ne!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);assert_ne!(out.receipt().stored.query_sha256,other.receipt().stored.query_sha256);
    let mut v=good;v["operation"]["review_policy"]=policy(false,false);assert_ne!(out.receipt().canonical_request_sha256,prepare!(&p,&v)?.receipt().canonical_request_sha256);Ok(())
}
#[test]
fn selector_style_product_old_v1_through_v6_schemas_do_not_silently_accept_new_combinations()->TestResult{
    use hwpx_agent_cli::form_product_request::stored_source_search::{StoredSourceSearchProductRequest as Legacy,selector::StoredSourceScopeProductRequest as V5};
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=envelope(&s,&raw,false)?;let before=s.metadata.audit_events()?.len();
    for version in 1..=6{let mut v=good.clone();v["schema_version"]=json!(format!("hwpx-agent.product-source-search-request/v{version}"));assert!(matches!(prepare!(&p,&v),Err(E::Request)));
        assert!(matches!(Legacy::prepare_json(&p,&wire(&v)?,Default::default(),4),Err(E::Request)));assert!(matches!(V5::prepare_json(&p,&wire(&v)?,Default::default(),4),Err(E::Request)));assert!(matches!(Discovery::prepare_json(&p,&wire(&v)?,Default::default(),4),Err(E::Request)));}
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn selector_style_product_write_source_head_and_five_foreign_provider_scopes_gate_retained_results()->TestResult{
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=envelope(&s,&raw,true)?;let reader=s.provider()?;
    assert!(prepare!(&reader,&good).is_err());let out=prepare!(&p,&good)?;let called=Cell::new(false);assert!(out.with_verified_json(&reader,5,|_|called.set(true)).is_err());
    for variant in 0..5{let tenant=if variant==4{TenantId::new(Uuid::from_u128(995))?}else{s.reader.tenant_id()};let subject=if variant==3{SubjectDigest::from_authenticated_subject("foreign-selector-style")?}else{s.reader.subject()};
        let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);let context=rev::RevisionRequestContext::new(tenant,subject);let project=if variant==2{rev::ProjectId::parse("prj_70000000000000000000000000000002")?}else{s.project};let branch=if variant==1{rev::BranchId::parse("brn_70000000000000000000000000000002")?}else{s.branch};
        let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&context,project,branch,DocumentId::parse(if variant==0{"foreign-document"}else{"actual-form-document"})?)?;
        assert!(out.verify(&other,5).is_err());assert!(out.with_verified_json(&other,5,|_|called.set(true)).is_err());}
    for(key,value)in[("expected_head_generation",json!(s.head.generation()+1)),("expected_source_package_sha256",json!("0".repeat(64))),("document_id",json!("foreign-document")),("project_id",json!("prj_70000000000000000000000000000002"))]{let mut v=good.clone();v[key]=value;assert!(prepare!(&p,&v).is_err());}
    assert!(!called.get());Ok(())
}
#[test]
fn selector_style_product_both_predicates_recheck_acl_regrant_quarantine_and_aead_before_output_or_next()->TestResult{
    for definition in[false,true]{for mode in 0..3{let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=envelope(&s,&raw,definition)?;let out=prepare!(&p,&v)?;
        let first:Value=out.with_next_verified_json(&p,&wire(&next(&out,Value::Null,false)?)?,5,|b|serde_json::from_slice(b))??;let n=wire(&next(&out,first["cursor"].clone(),false)?)?;
        match mode{0=>{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;},1=>{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("SELECTOR_STYLE_TEST")?,5)?;},_=>s.blobs.tamper.store(true,Ordering::SeqCst)}
        let called=Cell::new(false);assert!(out.verify(&p,6).is_err());assert!(out.with_verified_json(&p,6,|_|called.set(true)).is_err());assert!(out.with_next_verified_json(&p,&n,6,|_|called.set(true)).is_err());assert!(prepare!(&p,&v).is_err());assert!(!called.get());
        if mode==0{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;out.verify(&p,8)?;out.with_next_verified_json(&p,&n,8,|_|())?;}}}
    Ok(())
}
struct BoundaryRepo{inner:rev::InMemoryRevisionRepository,calls:AtomicUsize,trigger:AtomicUsize,context:rev::RevisionRequestContext,advance:rev::RevisionCommitRequest}
impl rev::RevisionRepository for BoundaryRepo{
    fn compare_and_swap(&self,c:&rev::RevisionRequestContext,r:&rev::RevisionCommitRequest)->Result<rev::CommitOutcome,rev::RevisionError>{self.inner.compare_and_swap(c,r)}
    fn head(&self,t:TenantId,p:rev::ProjectId,b:rev::BranchId)->Result<rev::RevisionHead,rev::RevisionError>{let n=self.calls.fetch_add(1,Ordering::SeqCst)+1;if n==self.trigger.load(Ordering::SeqCst){assert!(matches!(self.inner.compare_and_swap(&self.context,&self.advance)?,rev::CommitOutcome::Committed(_)));}self.inner.head(t,p,b)}
    fn node(&self,t:TenantId,p:rev::ProjectId,r:rev::RevisionId)->Result<rev::RevisionNode,rev::RevisionError>{self.inner.node(t,p,r)}
}
#[test]
fn selector_style_product_both_families_prepare_verify_output_and_next_last_head_races_block_delivery()->TestResult{
    for definition in[false,true]{for stage in 0..4{let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=envelope(&s,&raw,definition)?;let bytes=wire(&v)?;let out=prepare!(&p,&v)?;let n=wire(&next(&out,Value::Null,false)?)?;
        let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,ContentDigest::of(b"selector style race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation"),ContentDigest::of(b"transaction"))?;
        let b=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});let bound=StoredFormProvider::bind(&s.artifacts,&b,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
        match stage{0=>{Product::prepare_json(&bound,&bytes,Default::default(),5)?;},1=>{out.verify(&bound,5)?;},2=>{out.with_verified_json(&bound,5,|_|())?;},_=>{out.with_next_verified_json(&bound,&n,5,|_|())?;}}
        let calls=b.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);b.repository().calls.store(0,Ordering::SeqCst);b.repository().trigger.store(calls,Ordering::SeqCst);let called=Cell::new(false);
        match stage{0=>assert!(Product::prepare_json(&bound,&bytes,Default::default(),6).is_err()),1=>assert!(out.verify(&bound,6).is_err()),2=>assert!(out.with_verified_json(&bound,6,|_|called.set(true)).is_err()),_=>assert!(out.with_next_verified_json(&bound,&n,6,|_|called.set(true)).is_err())}
        assert!(!called.get());assert_eq!(b.repository().calls.load(Ordering::SeqCst),calls);}}
    Ok(())
}
#[test]
fn selector_style_product_cursor_binds_filter_policy_raw_and_key_and_preserves_review_regions()->TestResult{
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=envelope(&s,&raw,false)?;let out=prepare!(&p,&good)?;let mut cursor=Value::Null;
    for i in 0..4{let n:Value=out.with_next_verified_json(&p,&wire(&next(&out,cursor,false)?)?,5,|b|serde_json::from_slice(b))??;assert_eq!(n["match_index"],i);assert_eq!(n["region"],if i<2{"body_and_notes"}else{"memo_body"});cursor=n["cursor"].clone();}
    let wrapped:Value=out.with_next_verified_json(&p,&wire(&next(&out,cursor,true)?)?,5,|b|serde_json::from_slice(b))??;assert_eq!(wrapped["wrapped"],true);assert_eq!(wrapped["match_index"],0);
    for mode in 0..4{let mut v=good.clone();match mode{0=>v["operation"]["style_filter"]=filter(true),1=>v["operation"]["review_policy"]=policy(false,false),2=>v["idempotency_key"]=json!("OTHER-KEY"),_=>{}}
        let bytes=if mode==3{serde_json::to_vec_pretty(&v)?}else{wire(&v)?};let other=Product::prepare_json(&p,&bytes,Default::default(),4)?;let called=Cell::new(false);
        assert!(other.with_next_verified_json(&p,&wire(&next(&other,wrapped["cursor"].clone(),false)?)?,5,|_|called.set(true)).is_err());assert!(!called.get());}
    let before=s.metadata.audit_events()?.len();let mut bad=next(&out,Value::Null,false)?;bad["approved"]=json!(true);assert!(matches!(out.with_next_verified_json(&p,&wire(&bad)?,5,|_|()),Err(E::Request)));assert_eq!(s.metadata.audit_events()?.len(),before);
    let mut exact=wire(&next(&out,Value::Null,false)?)?;exact.resize(16*1024,b' ');out.with_next_verified_json(&p,&exact,5,|_|())?;exact.push(b' ');assert!(matches!(out.with_next_verified_json(&p,&exact,5,|_|()),Err(E::Limit)));Ok(())
}
#[test]
fn selector_style_product_missing_axes_dangling_excluded_refs_and_invalid_headers_never_fake_complete_matches()->TestResult{
    let raw=fixture::unstyled_package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=envelope(&s,&raw,false)?;
    v["operation"]["style_filter"]=json!({"kind":"declared","filter":{"run_character_property":0}});assert!(response!(&p,&v)["search"]["result"]["matches"].as_array().ok_or("matches")?.is_empty());
    let body=fixture::body().replace("charPrIDRef='0'","charPrIDRef='999'");let raw=fixture::with_body(&body)?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=envelope(&s,&raw,true)?;v["operation"]["review_policy"]=policy(false,false);v["operation"]["query"]=json!("absent");assert!(prepare!(&p,&v).is_err());
    let header=fixture::definition::header()?.replacen("charProperties itemCnt=\"7\"","charProperties itemCnt=\"8\"",1);let raw=fixture::definition::package_with_header(&fixture::body(),&header)?;
    let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);assert!(prepare!(&p,&envelope(&s,&raw,true)?).is_err());Ok(())
}
#[test]
fn selector_style_product_limits_private_receipts_and_source_head_ingest_preservation_do_not_grant_execution()->TestResult{
    let raw=fixture::package()?;let original=ContentDigest::of(&raw);let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
    for definition in[false,true]{let mut v=envelope(&s,&raw,definition)?;assert!(Product::prepare_json(&p,&wire(&v)?,SourceSearchLimits::new(Config{result_bytes:1,..Default::default()})?,4).is_err());
        v["operation"]["max_results"]=json!(1);assert!(prepare!(&p,&v).is_err());v["operation"]["max_results"]=json!(100);let out=prepare!(&p,&v)?;
        assert!(!format!("{out:?}{:?}",out.receipt()).contains("PRIVATE-STYLE-KEY"));assert!(matches!(out.require_current_product_route(&p,5),Err(E::RouteUnqualified)));
        assert!(!out.receipt().idempotency_key_claimed&&!out.receipt().full_search_product_native_cas_execution_publication_authority);let result=response!(&p,&v);
        assert_eq!(result["effective_style_visibility_or_execution_authority"],false);assert!(!serde_json::to_string(&result)?.contains("PRIVATE-AUTHOR"));}
    assert_eq!(ContentDigest::of(&raw),original);assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
}
