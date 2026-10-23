use super::*;
use hwpx_agent_cli::form_product_request::stored_source_search::{StoredSourceSearchProductRequest as Legacy,SourceSearchProductError as E,
    selector::{StoredSourceScopeProductRequest as Product,SOURCE_SCOPE_PRODUCT_REQUEST_SCHEMA as SCHEMA}};
use hwpx_package::document_import::search::{SourceSearchLimits,SourceSearchLimitConfig as Config};
use serde_json::{json,Value};
use std::{cell::Cell,sync::atomic::AtomicUsize};
use revision_service as rev;
#[path="../../../../hwpx-package/tests/support/source_scope_fixture.rs"] mod fixture;
macro_rules! write_provider {($s:ident,$actor:ident,$provider:ident)=>{
    let $actor=RequestContext::new($s.reader.tenant_id(),$s.reader.subject(),[AuthScope::DocumentRead,AuthScope::DocumentWrite]);
    let $provider=StoredFormProvider::bind(&$s.artifacts,&$s.revisions,&$actor,&$s.revision_context,$s.project,$s.branch,DocumentId::parse("actual-form-document")?)?;
}}
fn envelope(s:&StoredFixture,raw:&[u8])->Result<Value,Box<dyn Error>> {let revision=s.head.revision_id().ok_or("head")?.public_id();Ok(json!({
    "schema_version":SCHEMA,"idempotency_key":"PRIVATE-SCOPE-KEY","plan_id":"scope-plan","project_id":s.project.public_id(),"document_id":"actual-form-document",
    "base_revision":revision,"expected_head_generation":s.head.generation(),"expected_source_package_sha256":ContentDigest::of(raw).hex(),
    "selector":{"revision_id":revision,"scope":"document"},"operation":{"kind":"scope_inventory"}}))}
fn wire(v:&Value)->Result<Vec<u8>,serde_json::Error> {serde_json::to_vec(v)}
fn find(v:&Value)->Value {let mut request=v.clone();request["operation"]=json!({"kind":"find_literal","query":"same","case_sensitive":true,"whole_word":false,"max_results":100});request}
macro_rules! response {($p:expr,$v:expr)=>{{let prepared=Product::prepare_json($p,&wire($v)?,Default::default(),4)?;let value:Value=prepared.with_verified_json($p,5,|b|serde_json::from_slice(b))??;value}}}
#[test]
fn scope_product_discovery_supplies_real_section_node_and_selection_inputs_without_caller_source_import()->TestResult {
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let base=envelope(&s,&raw)?;
    let inventory=response!(&provider,&base);assert_eq!(inventory["section_ids"].as_array().ok_or("sections")?.len(),2);assert_eq!(inventory["nodes"].as_array().ok_or("nodes")?.len(),2);
    assert!(!serde_json::to_string(&inventory)?.contains("PRIVATE-same"));assert_eq!(inventory["full_source_visibility_native_flow_or_revision_authority"],false);
    let all=find(&base);assert_eq!(response!(&provider,&all)["result"]["matches"].as_array().ok_or("matches")?.len(),5);
    let mut section=all.clone();section["selector"]["scope"]=json!("section");section["selector"]["section_ids"]=json!([inventory["section_ids"][0].clone()]);
    assert_eq!(response!(&provider,&section)["result"]["matches"].as_array().ok_or("matches")?.len(),2);
    let block=&inventory["blocks"][0];let node=inventory["nodes"].as_array().ok_or("nodes")?.iter().find(|n|n["source_handle"]==block["paragraph_handle"]).ok_or("node")?;
    let mut selected=all.clone();selected["selector"]["scope"]=json!("node_set");selected["selector"]["range"]=json!({"node_ids":[node["node_id"].clone()]});
    assert_eq!(response!(&provider,&selected)["result"]["matches"].as_array().ok_or("matches")?.len(),2);
    let hash:[u8;32]=serde_json::from_value(inventory["index"]["index_sha256"].clone())?;
    selected["selector"]["scope"]=json!("selection");selected["selector"]["range"]=json!({"coordinate_space":"index_nfc_unicode_scalars","index_sha256":hex::encode(hash),
        "start":{"paragraph_handle":block["paragraph_handle"],"block_index":block["block_index"],"normalized_scalar":2},
        "end":{"paragraph_handle":block["paragraph_handle"],"block_index":block["block_index"],"normalized_scalar":14}});
    selected["operation"]=json!({"kind":"find_regex","query":"^PRIVATE-same$","case_sensitive":true,"whole_word":false,"max_results":100});
    let result=response!(&provider,&selected);let matches=result["result"]["matches"].as_array().ok_or("matches")?;assert_eq!(matches.len(),1);
    assert_eq!((matches[0]["start_normalized_scalar"].as_u64(),matches[0]["end_normalized_scalar"].as_u64()),(Some(2),Some(14)));
    assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);Ok(())
}
#[test]
fn scope_product_strict_shapes_unknown_duplicates_and_revision_mismatch_reject_before_reads()->TestResult {
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=envelope(&s,&raw)?;let before=s.metadata.audit_events()?.len();
    let mut bad=vec!["null".to_owned(),"[]".to_owned(),format!("{} {{}}",serde_json::to_string(&good)?)];
    for key in ["schema_version","idempotency_key","plan_id","project_id","document_id","base_revision","expected_head_generation","expected_source_package_sha256","selector","operation"] {let mut v=good.clone();v.as_object_mut().ok_or("envelope")?.remove(key);bad.push(serde_json::to_string(&v)?);}
    for selector in [json!([]),json!({"scope":"document"}),json!({"revision_id":good["base_revision"],"scope":"document","section_ids":[]}),
        json!({"revision_id":good["base_revision"],"scope":"document","range":null}),json!({"revision_id":good["base_revision"],"scope":"section","section_ids":[]}),
        json!({"revision_id":good["base_revision"],"scope":"node_set","range":{"node_ids":[]}}),json!({"revision_id":rev::RevisionId::generate().public_id(),"scope":"document"}),
        json!({"revision_id":good["base_revision"],"scope":"document","approved":true})] {let mut v=good.clone();v["selector"]=selector;bad.push(serde_json::to_string(&v)?);}
    for operation in [json!([]),json!({"kind":"scope_inventory","query":"ignored"}),json!({"kind":"find_literal","query":"same"}),
        json!({"kind":"find_regex","query":"same","case_sensitive":true,"whole_word":false,"max_results":0}),
        json!({"kind":"find_literal","query":"same","case_sensitive":true,"whole_word":false,"max_results":100,"include_hidden":true})] {
        let mut v=good.clone();v["operation"]=operation;bad.push(serde_json::to_string(&v)?);}
    for (key,value) in [("scope",json!({"kind":"mapped_document","paragraph_handles":[]})),("output_path",json!("D:/do-not-write")),("approved",json!(true)),
        ("expected_head_generation",json!(0)),("expected_source_package_sha256",json!("A".repeat(64)))] {let mut v=good.clone();v[key]=value;bad.push(serde_json::to_string(&v)?);}
    let plain=serde_json::to_string(&good)?;let duplicate=plain.replace("\"scope\":\"document\"","\"scope\":\"document\",\"sco\\u0070e\":\"section\"");assert_ne!(duplicate,plain);bad.push(duplicate);
    for raw in bad {assert!(matches!(Product::prepare_json(&provider,raw.as_bytes(),Default::default(),4),Err(E::Request)));}
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn scope_product_exact_16k_and_raw_canonical_key_plan_and_query_bindings_do_not_claim_execution()->TestResult {
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=envelope(&s,&raw)?;
    let compact=Product::prepare_json(&provider,&wire(&good)?,Default::default(),4)?;let mut padded=wire(&good)?;padded.resize(16*1024,b' ');
    let exact=Product::prepare_json(&provider,&padded,Default::default(),4)?;assert_ne!(compact.receipt().raw_request_sha256,exact.receipt().raw_request_sha256);assert_eq!(compact.receipt().canonical_request_sha256,exact.receipt().canonical_request_sha256);
    padded.push(b' ');assert!(matches!(Product::prepare_json(&provider,&padded,Default::default(),4),Err(E::Limit)));assert!(matches!(Product::prepare_json(&provider,b"",Default::default(),4),Err(E::Limit)));
    for (key,value) in [("idempotency_key",json!("OTHER-KEY")),("plan_id",json!("other-plan"))] {let mut v=good.clone();v[key]=value;let other=Product::prepare_json(&provider,&wire(&v)?,Default::default(),4)?;
        assert_ne!(compact.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);assert_ne!(compact.receipt().scoped_request_sha256,other.receipt().scoped_request_sha256);assert_eq!(compact.receipt().stored.result_sha256,other.receipt().stored.result_sha256);}
    assert_eq!(compact.receipt().profile,"hwpx-agent.product-source-search-preparation/v5");assert_eq!(compact.receipt().stored.profile,"hwpx-agent.stored-source-search/v5");
    assert!(!compact.receipt().idempotency_key_claimed&&!compact.receipt().full_search_product_native_cas_execution_publication_authority);
    assert!(matches!(compact.require_current_product_route(&provider,5),Err(E::RouteUnqualified)));assert!(!format!("{compact:?}{:?}",compact.receipt()).contains("PRIVATE-SCOPE-KEY"));Ok(())
}
#[test]
fn scope_product_write_scope_expected_source_head_and_all_five_provider_scopes_guard_inventory_and_search()->TestResult {
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=envelope(&s,&raw)?;let reader=s.provider()?;let before=s.metadata.audit_events()?.len();
    assert!(Product::prepare_json(&reader,&wire(&good)?,Default::default(),4).is_err());assert_eq!(s.metadata.audit_events()?.len(),before);
    for v in [good.clone(),find(&good)] {let out=Product::prepare_json(&provider,&wire(&v)?,Default::default(),4)?;let called=Cell::new(false);
        assert!(out.with_verified_json(&reader,5,|_|called.set(true)).is_err());assert!(!called.get());
        for variant in 0..5 {let tenant=if variant==4{TenantId::new(uuid::Uuid::from_u128(702))?}else{s.reader.tenant_id()};let subject=if variant==3{s.owner.subject()}else{s.reader.subject()};
            let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);let context=rev::RevisionRequestContext::new(tenant,subject);
            let project=if variant==2{rev::ProjectId::parse("prj_70000000000000000000000000000002")?}else{s.project};let branch=if variant==1{rev::BranchId::parse("brn_70000000000000000000000000000002")?}else{s.branch};
            let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&context,project,branch,DocumentId::parse(if variant==0{"foreign-scope"}else{"actual-form-document"})?)?;
            assert!(out.verify(&other,5).is_err());assert!(out.with_verified_json(&other,5,|_|called.set(true)).is_err());assert!(!called.get());}
    }
    for (key,value) in [("expected_head_generation",json!(s.head.generation()+1)),("expected_source_package_sha256",json!("0".repeat(64))),
        ("document_id",json!("foreign-scope")),("project_id",json!("prj_70000000000000000000000000000002"))] {let mut v=good.clone();v[key]=value;assert!(Product::prepare_json(&provider,&wire(&v)?,Default::default(),4).is_err());}Ok(())
}
#[test]
fn scope_product_acl_quarantine_aead_and_regrant_recheck_retained_discovery_and_search()->TestResult {
    for mode in 0..3 {for search in [false,true] {let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=envelope(&s,&raw)?;if search{v=find(&v);}
        let out=Product::prepare_json(&provider,&wire(&v)?,Default::default(),4)?;let called=Cell::new(false);
        match mode {0=>{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;},1=>{s.artifacts.quarantine(&s.owner,s.result,artifact_service::QuarantineReason::parse("SCOPE_PRODUCT_TEST")?,5)?;},_=>s.blobs.tamper.store(true,Ordering::SeqCst)}
        assert!(out.verify(&provider,6).is_err());assert!(out.with_verified_json(&provider,6,|_|called.set(true)).is_err());assert!(!called.get());assert!(Product::prepare_json(&provider,&wire(&v)?,Default::default(),6).is_err());
        if mode==0{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;out.verify(&provider,8)?;}
    }}Ok(())
}
struct BoundaryRepo {inner:rev::InMemoryRevisionRepository,calls:AtomicUsize,trigger:AtomicUsize,context:rev::RevisionRequestContext,advance:rev::RevisionCommitRequest}
impl rev::RevisionRepository for BoundaryRepo {
    fn compare_and_swap(&self,c:&rev::RevisionRequestContext,r:&rev::RevisionCommitRequest)->Result<rev::CommitOutcome,rev::RevisionError>{self.inner.compare_and_swap(c,r)}
    fn head(&self,t:TenantId,p:rev::ProjectId,b:rev::BranchId)->Result<rev::RevisionHead,rev::RevisionError>{let call=self.calls.fetch_add(1,Ordering::SeqCst)+1;
        if call==self.trigger.load(Ordering::SeqCst){assert!(matches!(self.inner.compare_and_swap(&self.context,&self.advance)?,rev::CommitOutcome::Committed(_)));}self.inner.head(t,p,b)}
    fn node(&self,t:TenantId,p:rev::ProjectId,r:rev::RevisionId)->Result<rev::RevisionNode,rev::RevisionError>{self.inner.node(t,p,r)}
}
#[test]
fn scope_product_prepare_verify_and_final_consumer_head_races_never_expose_stale_metadata_or_matches()->TestResult {
    for search in [false,true] {for stage in 0..3 {let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=envelope(&s,&raw)?;if search{v=find(&v);}let v=wire(&v)?;
        let out=Product::prepare_json(&provider,&v,Default::default(),4)?;
        let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,
            ContentDigest::of(b"scope race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation"),ContentDigest::of(b"transaction"))?;
        let boundary=rev::RevisionService::new(BoundaryRepo {inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
        let bound=StoredFormProvider::bind(&s.artifacts,&boundary,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
        match stage {0=>{Product::prepare_json(&bound,&v,Default::default(),5)?;},1=>{out.verify(&bound,5)?;},_=>{out.with_verified_json(&bound,5,|_|())?;}}
        let calls=boundary.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);boundary.repository().calls.store(0,Ordering::SeqCst);boundary.repository().trigger.store(calls,Ordering::SeqCst);let called=Cell::new(false);
        match stage {0=>assert!(Product::prepare_json(&bound,&v,Default::default(),6).is_err()),1=>assert!(out.verify(&bound,6).is_err()),_=>assert!(out.with_verified_json(&bound,6,|_|called.set(true)).is_err())}assert!(!called.get());assert_eq!(boundary.repository().calls.load(Ordering::SeqCst),calls);
    }}Ok(())
}
#[test]
fn scope_product_selection_rejects_stale_index_foreign_handles_reversed_ranges_and_unknown_boundary_fields()->TestResult {
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=envelope(&s,&raw)?;let inventory=response!(&provider,&v);let block=&inventory["blocks"][0];
    let hash:[u8;32]=serde_json::from_value(inventory["index"]["index_sha256"].clone())?;let mut good=find(&v);good["selector"]["scope"]=json!("selection");
    good["selector"]["range"]=json!({"coordinate_space":"index_nfc_unicode_scalars","index_sha256":hex::encode(hash),
        "start":{"paragraph_handle":block["paragraph_handle"],"block_index":0,"normalized_scalar":2},"end":{"paragraph_handle":block["paragraph_handle"],"block_index":0,"normalized_scalar":14}});
    good["operation"]["query"]=json!("absent");
    for (key,value) in [("index_sha256",json!("0".repeat(64))),("start",json!({"paragraph_handle":"foreign-paragraph","block_index":0,"normalized_scalar":2})),
        ("end",json!({"paragraph_handle":block["paragraph_handle"],"block_index":0,"normalized_scalar":9999})),
        ("start",json!({"paragraph_handle":block["paragraph_handle"],"block_index":0,"normalized_scalar":15}))] {let mut bad=good.clone();bad["selector"]["range"][key]=value;assert!(Product::prepare_json(&provider,&wire(&bad)?,Default::default(),4).is_err());}
    let mut bad=good;bad["selector"]["range"]["start"]["approved"]=json!(true);let before=s.metadata.audit_events()?.len();assert!(matches!(Product::prepare_json(&provider,&wire(&bad)?,Default::default(),4),Err(E::Request)));assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn scope_product_node_and_section_sets_are_digest_canonical_and_selected_before_match_limits()->TestResult {
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=envelope(&s,&raw)?;let inv=response!(&provider,&v);let mut request=find(&v);
    request["selector"]["scope"]=json!("section");request["selector"]["section_ids"]=inv["section_ids"].clone();let a=Product::prepare_json(&provider,&wire(&request)?,Default::default(),4)?;
    request["selector"]["section_ids"].as_array_mut().ok_or("sections")?.reverse();let b=Product::prepare_json(&provider,&wire(&request)?,Default::default(),4)?;
    assert_eq!(a.receipt().stored.result_sha256,b.receipt().stored.result_sha256);assert_ne!(a.receipt().canonical_request_sha256,b.receipt().canonical_request_sha256);
    request["selector"]["section_ids"]=json!([inv["section_ids"][0].clone()]);request["operation"]["max_results"]=json!(2);assert_eq!(response!(&provider,&request)["result"]["matches"].as_array().ok_or("matches")?.len(),2);
    request["selector"]["section_ids"]=json!([inv["section_ids"][0].clone(),inv["section_ids"][0].clone()]);assert!(matches!(Product::prepare_json(&provider,&wire(&request)?,Default::default(),4),Err(E::Request)));Ok(())
}
#[test]
fn scope_product_inventory_and_response_limits_fail_without_partial_metadata_and_source_is_unchanged()->TestResult {
    let raw=fixture::package()?;let original=ContentDigest::of(&raw);let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=envelope(&s,&raw)?;
    for request in [v.clone(),find(&v)] {assert!(Product::prepare_json(&provider,&wire(&request)?,SourceSearchLimits::new(Config {result_bytes:1,..Default::default()})?,4).is_err());}
    let mut too_many=find(&v);too_many["operation"]["max_results"]=json!(1);assert!(Product::prepare_json(&provider,&wire(&too_many)?,Default::default(),4).is_err());
    assert_eq!(ContentDigest::of(&raw),original);assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
}
#[test]
fn scope_product_v5_selector_schema_is_separate_from_all_four_legacy_request_profiles()->TestResult {
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=envelope(&s,&raw)?;let before=s.metadata.audit_events()?.len();
    for version in 1..=4 {let mut bad=v.clone();bad["schema_version"]=json!(format!("hwpx-agent.product-source-search-request/v{version}"));
        assert!(matches!(Product::prepare_json(&provider,&wire(&bad)?,Default::default(),4),Err(E::Request)));assert!(matches!(Legacy::prepare_json(&provider,&wire(&bad)?,Default::default(),4),Err(E::Request)));}
    assert!(matches!(Legacy::prepare_json(&provider,&wire(&v)?,Default::default(),4),Err(E::Request)));assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
