use super::*;
use hwpx_agent_cli::form_product_request::stored_source_search::{SourceSearchProductError as E,
    selector::{review::StoredReviewScopeProductRequest as Discovery,controls::{StoredSelectorControlProductRequest as Product,
        PreparedStoredSelectorControlProduct as Prepared,SELECTOR_CONTROL_PRODUCT_REQUEST_SCHEMA as SCHEMA}},navigation::SOURCE_SEARCH_NEXT_REQUEST_SCHEMA as NEXT};
use hwpx_package::document_import::search::{SourceSearchLimits,SourceSearchLimitConfig as Config,SourceSearchError as SearchError,
    selector::SourceIndexScopeSelector,inspection::SourceControlKind,reviews::SourceReviewTextPolicy};
use serde_json::{json,Value};
use std::{cell::Cell,sync::atomic::AtomicUsize};
use revision_service as rev;
#[path="../../../../hwpx-package/tests/support/review_scope_fixture.rs"] mod fixture;
#[allow(dead_code)] #[path="../../../../hwpx-package/tests/support/document_import_review_assembly_fixture.rs"] mod assembly;
#[allow(dead_code)] #[path="../../../../hwpx-package/tests/support/review_cell_output_fixture.rs"] mod table;
const TAB:&str="<hp:tab width='1' leader='0' type='0'/>";
fn body()->String{fixture::body().replace("BODY K K",&format!("BODY{TAB} K K")).replace("MEMO K K",&format!("MEMO{TAB} K K"))}
fn raw()->Result<Vec<u8>,Box<dyn Error>>{fixture::with_body(&body())}
macro_rules! write_provider{($s:ident,$actor:ident,$p:ident)=>{
    let $actor=RequestContext::new($s.reader.tenant_id(),$s.reader.subject(),[AuthScope::DocumentRead,AuthScope::DocumentWrite]);
    let $p=StoredFormProvider::bind(&$s.artifacts,&$s.revisions,&$actor,&$s.revision_context,$s.project,$s.branch,DocumentId::parse("actual-form-document")?)?;
}}
macro_rules! prepare{($p:expr,$v:expr)=>{Product::prepare_json($p,&wire($v)?,Default::default(),4)}}
macro_rules! response{($p:expr,$v:expr)=>{{let out=prepare!($p,$v)?;let value:Value=out.with_verified_json($p,5,|b|serde_json::from_slice(b))??;value}}}
fn wire(v:&Value)->Result<Vec<u8>,serde_json::Error>{serde_json::to_vec(v)}
fn policy(h:bool,m:bool)->Value{json!({"include_hidden_explanations":h,"include_memo_bodies":m})}
fn envelope(s:&StoredFixture,raw:&[u8])->Result<Value,Box<dyn Error>>{let revision=s.head.revision_id().ok_or("head")?.public_id();Ok(json!({
    "schema_version":SCHEMA,"idempotency_key":"PRIVATE-CONTROL-KEY","plan_id":"selector-control-plan","project_id":s.project.public_id(),"document_id":"actual-form-document","base_revision":revision,
    "expected_head_generation":s.head.generation(),"expected_source_package_sha256":ContentDigest::of(raw).hex(),"selector":{"revision_id":revision,"scope":"document"},
    "operation":{"kind":"find_control","query":"tab","regex":false,"case_sensitive":true,"whole_word":false,"max_results":100,"review_policy":policy(true,true)}}))}
fn inventory(p:&Provider<'_>,base:&Value)->Result<Value,Box<dyn Error>>{let mut v=base.clone();v["schema_version"]=json!("hwpx-agent.product-source-search-request/v6");v["operation"]=json!({"kind":"scope_inventory"});
    let out=Discovery::prepare_json(p,&wire(&v)?,Default::default(),4)?;Ok(out.with_verified_json(p,5,|b|serde_json::from_slice(b))??)}
fn selection(inv:&Value,block:usize,a:usize,z:usize)->Result<Value,Box<dyn Error>>{let b=&inv["inventory"]["blocks"][block];let hash:[u8;32]=serde_json::from_value(inv["inventory"]["index"]["index_sha256"].clone())?;
    Ok(json!({"coordinate_space":"index_nfc_unicode_scalars","index_sha256":hex::encode(hash),"start":{"paragraph_handle":b["paragraph_handle"],"block_index":b["block_index"],"normalized_scalar":a},
        "end":{"paragraph_handle":b["paragraph_handle"],"block_index":b["block_index"],"normalized_scalar":z}}))}
fn next(p:&Prepared,cursor:Value,wrap:bool)->Result<Value,Box<dyn Error>>{Ok(json!({"schema_version":NEXT,"search_receipt_sha256":p.navigation_receipt_sha256()?,"navigation":{"direction":"forward","wrap":wrap,"cursor":cursor}}))}
#[test]
fn selector_control_product_discovery_builds_all_four_scopes_without_caller_form_import()->TestResult{
    let raw=raw()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let inv=inventory(&p,&envelope(&s,&raw)?)?;
    let i=inv["block_regions"].as_array().ok_or("regions")?.iter().position(|v|v=="memo_body").ok_or("memo")?;let range=selection(&inv,i,4,5)?;
    let node=inv["inventory"]["nodes"].as_array().ok_or("nodes")?.iter().find(|n|n["source_handle"]==range["start"]["paragraph_handle"]).ok_or("node")?;
    for(scope,count)in[("document",2),("section",2),("node_set",1),("selection",1)]{let mut v=envelope(&s,&raw)?;v["selector"]["scope"]=json!(scope);
        match scope{"section"=>v["selector"]["section_ids"]=inv["inventory"]["section_ids"].clone(),"node_set"=>v["selector"]["range"]=json!({"node_ids":[node["node_id"].clone()]}),"selection"=>v["selector"]["range"]=range.clone(),_=>{}}
        let out=prepare!(&p,&v)?;out.verify(&p,5)?;let value:Value=out.with_verified_json(&p,5,|b|serde_json::from_slice(b))??;
        assert_eq!(value["control_matches"].as_array().ok_or("controls")?.len(),count);assert_eq!(out.receipt().profile,"hwpx-agent.product-source-search-preparation/v8");
        assert_eq!(out.receipt().stored.profile,"hwpx-agent.stored-source-search/v8");assert_eq!(out.receipt().capability_id,"search.find_control");}
    Ok(())
}
#[test]
fn selector_control_product_object_anchor_and_typed_stored_route_do_not_require_parent_paragraph_selection()->TestResult{
    let raw=assembly::package(&format!("<hp:t>OUTSIDE</hp:t>{}<hp:t>AFTER</hp:t>",table::table(300)))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
    let mut v=envelope(&s,&raw)?;v["operation"]["query"]=json!("table");let all=response!(&p,&v);let inv=inventory(&p,&v)?;
    let anchor=&all["control_matches"][0]["control_anchor"]["opaque_handle"];
    let node=inv["inventory"]["nodes"].as_array().ok_or("nodes")?.iter().find(|n|&n["source_handle"]==anchor).ok_or("table node")?;
    v["selector"]["scope"]=json!("node_set");v["selector"]["range"]=json!({"node_ids":[node["node_id"].clone()]});
    let product=prepare!(&p,&v)?;assert_eq!(response!(&p,&v)["control_matches"],all["control_matches"]);
    let nodes:Vec<domain_ir::LogicalId>=serde_json::from_value(v["selector"]["range"]["node_ids"].clone())?;
    let stored=p.import_actual_forms(s.head,4)?.into_review_control_search(&p,SourceIndexScopeSelector::NodeSet(&nodes),
        SourceReviewTextPolicy{include_hidden_explanations:true,include_memo_bodies:true},SourceControlKind::Table,100,Default::default(),4)?;
    stored.verify(&p,5)?;assert_eq!(stored.receipt(),&product.receipt().stored);Ok(())
}
#[test]
fn selector_control_product_partial_atoms_and_zero_text_cross_block_gap_never_widen_to_whole_paragraph()->TestResult{
    let raw=fixture::with_body(&format!("<hp:p id='1'><hp:run><hp:pic/><hp:t>A{TAB}B</hp:t><hp:pic/><hp:t>C</hp:t><hp:pic/></hp:run></hp:p>"))?;
    let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=envelope(&s,&raw)?;let inv=inventory(&p,&v)?;v["selector"]["scope"]=json!("selection");
    for(a,z,count)in[(1,2,1),(2,3,0),(1,1,0)]{v["selector"]["range"]=selection(&inv,0,a,z)?;assert_eq!(response!(&p,&v)["control_matches"].as_array().ok_or("controls")?.len(),count);}
    let mut gap=selection(&inv,0,3,3)?;gap["end"]=selection(&inv,1,0,0)?["end"].clone();v["selector"]["range"]=gap;v["operation"]["query"]=json!("picture");v["operation"]["max_results"]=json!(1);
    let value=response!(&p,&v);assert_eq!(value["control_matches"].as_array().ok_or("controls")?.len(),1);assert_eq!(value["scope"]["selected_normalized_scalars"],0);Ok(())
}
#[test]
fn selector_control_product_all_policies_apply_before_caps_and_excluded_review_nodes_remain_valid()->TestResult{
    let raw=fixture::with_body(&body().replace("HIDDEN K K",&format!("HIDDEN{TAB} K K")))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut digests=BTreeSet::new();
    for(h,m,count)in[(false,false,1),(true,false,2),(false,true,2),(true,true,3)]{let mut v=envelope(&s,&raw)?;v["operation"]["review_policy"]=policy(h,m);v["operation"]["max_results"]=json!(count);
        let out=prepare!(&p,&v)?;digests.insert(out.receipt().stored.query_sha256);assert_eq!(response!(&p,&v)["control_matches"].as_array().ok_or("controls")?.len(),count);}assert_eq!(digests.len(),4);
    let mut v=envelope(&s,&raw)?;let inv=inventory(&p,&v)?;let i=inv["block_regions"].as_array().ok_or("regions")?.iter().position(|r|r=="memo_body").ok_or("memo")?;
    let node=inv["inventory"]["nodes"].as_array().ok_or("nodes")?.iter().find(|n|n["source_handle"]==inv["inventory"]["blocks"][i]["paragraph_handle"]).ok_or("node")?;
    v["selector"]["scope"]=json!("node_set");v["selector"]["range"]=json!({"node_ids":[node["node_id"].clone()]});v["operation"]["review_policy"]=policy(false,false);v["operation"]["max_results"]=json!(1);
    let out=response!(&p,&v);assert!(out["control_matches"].as_array().ok_or("controls")?.is_empty());assert_eq!(out["excluded_memo_controls"],1);Ok(())
}
#[test]
fn selector_control_product_strict_fields_kind_fixed_options_policy_and_revision_reject_before_reads()->TestResult{
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=envelope(&s,&raw)?;let before=s.metadata.audit_events()?.len();let mut bad=vec![b"null".to_vec(),b"[]".to_vec(),format!("{} {{}}",serde_json::to_string(&good)?).into_bytes()];
    for key in["schema_version","idempotency_key","plan_id","project_id","document_id","base_revision","expected_head_generation","expected_source_package_sha256","selector","operation"]{let mut v=good.clone();v.as_object_mut().ok_or("object")?.remove(key);bad.push(wire(&v)?);}
    for key in["kind","query","regex","case_sensitive","whole_word","max_results","review_policy"]{let mut v=good.clone();v["operation"].as_object_mut().ok_or("operation")?.remove(key);bad.push(wire(&v)?);}
    for value in[json!(null),json!([]),json!({}),json!({"include_hidden_explanations":true}),json!({"include_hidden_explanations":true,"include_memo_bodies":1}),json!({"include_hidden_explanations":true,"include_memo_bodies":true,"approved":true})]{let mut v=good.clone();v["operation"]["review_policy"]=value;bad.push(wire(&v)?);}
    for(key,value)in[("kind",json!("find_style")),("query",json!("hp:tab")),("query",json!("Tab")),("query",json!({"kind":"tab"})),("query",Value::Null),("query",json!("")),("regex",json!(true)),("case_sensitive",json!(false)),("whole_word",json!(true)),("max_results",json!(0)),("max_results",json!(10001)),("style_filter",json!({})),("include_hidden",json!(true)),("native_verified",json!(true))]{let mut v=good.clone();v["operation"][key]=value;bad.push(wire(&v)?);}
    for sel in[json!([]),json!({"scope":"document"}),json!({"revision_id":good["base_revision"],"scope":"document","range":null}),json!({"revision_id":good["base_revision"],"scope":"section","section_ids":[]}),json!({"revision_id":rev::RevisionId::generate().public_id(),"scope":"document"})]{let mut v=good.clone();v["selector"]=sel;bad.push(wire(&v)?);}
    for(key,value)in[("scope",json!({})),("operation",json!([])),("approved",json!(true)),("expected_head_generation",json!(0)),("expected_source_package_sha256",json!("A".repeat(64)))]{let mut v=good.clone();v[key]=value;bad.push(wire(&v)?);}
    let text=serde_json::to_string(&good)?;for(from,to)in[("\"query\":\"tab\"","\"query\":\"tab\",\"qu\\u0065ry\":\"picture\""),("\"scope\":\"document\"","\"scope\":\"document\",\"sco\\u0070e\":\"selection\"")]{let v=text.replace(from,to);assert_ne!(v,text);bad.push(v.into_bytes());}
    for raw in bad{assert!(matches!(Product::prepare_json(&p,&raw,Default::default(),4),Err(E::Request)));}assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn selector_control_product_exact_16k_raw_canonical_key_plan_kind_and_policy_are_bound()->TestResult{
    let raw=raw()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=envelope(&s,&raw)?;let out=prepare!(&p,&good)?;let mut bytes=wire(&good)?;bytes.resize(16*1024,b' ');
    let exact=Product::prepare_json(&p,&bytes,Default::default(),4)?;assert_ne!(out.receipt().raw_request_sha256,exact.receipt().raw_request_sha256);assert_eq!(out.receipt().canonical_request_sha256,exact.receipt().canonical_request_sha256);
    bytes.push(b' ');assert!(matches!(Product::prepare_json(&p,&bytes,Default::default(),4),Err(E::Limit)));assert!(matches!(Product::prepare_json(&p,b"",Default::default(),4),Err(E::Limit)));
    for(key,value)in[("idempotency_key",json!("OTHER-KEY")),("plan_id",json!("other-plan"))]{let mut v=good.clone();v[key]=value;let other=prepare!(&p,&v)?;assert_ne!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);assert_ne!(out.receipt().scoped_request_sha256,other.receipt().scoped_request_sha256);assert_eq!(out.receipt().stored.result_sha256,other.receipt().stored.result_sha256);}
    let mut v=good.clone();v["operation"]["query"]=json!("line_break");assert_ne!(out.receipt().stored.query_sha256,prepare!(&p,&v)?.receipt().stored.query_sha256);
    let mut v=good;v["operation"]["review_policy"]=policy(false,false);assert_ne!(out.receipt().canonical_request_sha256,prepare!(&p,&v)?.receipt().canonical_request_sha256);Ok(())
}
#[test]
fn selector_control_product_legacy_v1_through_v7_parsers_reject_the_new_control_scope_combination()->TestResult{
    use hwpx_agent_cli::form_product_request::stored_source_search::{StoredSourceSearchProductRequest as Legacy,selector::{StoredSourceScopeProductRequest as V5,styles::StoredSelectorStyleProductRequest as V7}};
    let raw=raw()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=envelope(&s,&raw)?;let before=s.metadata.audit_events()?.len();
    for version in 1..=7{let mut v=good.clone();v["schema_version"]=json!(format!("hwpx-agent.product-source-search-request/v{version}"));let bytes=wire(&v)?;
        assert!(matches!(Product::prepare_json(&p,&bytes,Default::default(),4),Err(E::Request)));assert!(matches!(Legacy::prepare_json(&p,&bytes,Default::default(),4),Err(E::Request)));
        assert!(matches!(V5::prepare_json(&p,&bytes,Default::default(),4),Err(E::Request)));assert!(matches!(Discovery::prepare_json(&p,&bytes,Default::default(),4),Err(E::Request)));assert!(matches!(V7::prepare_json(&p,&bytes,Default::default(),4),Err(E::Request)));}
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn selector_control_product_current_write_source_head_and_five_provider_scopes_gate_json_and_next()->TestResult{
    let raw=raw()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=envelope(&s,&raw)?;let reader=s.provider()?;
    assert!(prepare!(&reader,&v).is_err());let out=prepare!(&p,&v)?;let n=wire(&next(&out,Value::Null,false)?)?;let called=Cell::new(false);
    assert!(out.with_verified_json(&reader,5,|_|called.set(true)).is_err());assert!(out.with_next_verified_json(&reader,&n,5,|_|called.set(true)).is_err());
    for variant in 0..5{let tenant=if variant==4{TenantId::new(Uuid::from_u128(996))?}else{s.reader.tenant_id()};let subject=if variant==3{SubjectDigest::from_authenticated_subject("foreign-selector-control")?}else{s.reader.subject()};
        let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);let context=rev::RevisionRequestContext::new(tenant,subject);let project=if variant==2{rev::ProjectId::parse("prj_70000000000000000000000000000002")?}else{s.project};let branch=if variant==1{rev::BranchId::parse("brn_70000000000000000000000000000002")?}else{s.branch};
        let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&context,project,branch,DocumentId::parse(if variant==0{"foreign-document"}else{"actual-form-document"})?)?;
        assert!(out.verify(&other,5).is_err());assert!(out.with_verified_json(&other,5,|_|called.set(true)).is_err());assert!(out.with_next_verified_json(&other,&n,5,|_|called.set(true)).is_err());}
    for(key,value)in[("expected_head_generation",json!(s.head.generation()+1)),("expected_source_package_sha256",json!("0".repeat(64))),("document_id",json!("foreign-document")),("project_id",json!("prj_70000000000000000000000000000002"))]{let mut bad=v.clone();bad[key]=value;assert!(prepare!(&p,&bad).is_err());}assert!(!called.get());Ok(())
}
#[test]
fn selector_control_product_acl_regrant_quarantine_and_aead_recheck_before_verify_json_next_and_prepare()->TestResult{
    for mode in 0..3{let raw=raw()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=envelope(&s,&raw)?;let out=prepare!(&p,&v)?;
        let n=wire(&next(&out,Value::Null,false)?)?;match mode{0=>{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;},1=>{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("SELECTOR_CONTROL_TEST")?,5)?;},_=>s.blobs.tamper.store(true,Ordering::SeqCst)}
        let called=Cell::new(false);assert!(out.verify(&p,6).is_err());assert!(out.with_verified_json(&p,6,|_|called.set(true)).is_err());assert!(out.with_next_verified_json(&p,&n,6,|_|called.set(true)).is_err());assert!(prepare!(&p,&v).is_err());assert!(!called.get());
        if mode==0{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;out.verify(&p,8)?;out.with_next_verified_json(&p,&n,8,|_|())?;}}
    Ok(())
}
struct BoundaryRepo{inner:rev::InMemoryRevisionRepository,calls:AtomicUsize,trigger:AtomicUsize,context:rev::RevisionRequestContext,advance:rev::RevisionCommitRequest}
impl rev::RevisionRepository for BoundaryRepo{
    fn compare_and_swap(&self,c:&rev::RevisionRequestContext,r:&rev::RevisionCommitRequest)->Result<rev::CommitOutcome,rev::RevisionError>{self.inner.compare_and_swap(c,r)}
    fn head(&self,t:TenantId,p:rev::ProjectId,b:rev::BranchId)->Result<rev::RevisionHead,rev::RevisionError>{let n=self.calls.fetch_add(1,Ordering::SeqCst)+1;if n==self.trigger.load(Ordering::SeqCst){assert!(matches!(self.inner.compare_and_swap(&self.context,&self.advance)?,rev::CommitOutcome::Committed(_)));}self.inner.head(t,p,b)}
    fn node(&self,t:TenantId,p:rev::ProjectId,r:rev::RevisionId)->Result<rev::RevisionNode,rev::RevisionError>{self.inner.node(t,p,r)}
}
#[test]
fn selector_control_product_prepare_verify_json_and_next_final_head_races_block_disclosure()->TestResult{
    for stage in 0..4{let raw=raw()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=envelope(&s,&raw)?;let bytes=wire(&v)?;let out=prepare!(&p,&v)?;let n=wire(&next(&out,Value::Null,false)?)?;
        let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,ContentDigest::of(b"selector control race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation"),ContentDigest::of(b"transaction"))?;
        let b=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});let bound=StoredFormProvider::bind(&s.artifacts,&b,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
        match stage{0=>{Product::prepare_json(&bound,&bytes,Default::default(),5)?;},1=>{out.verify(&bound,5)?;},2=>{out.with_verified_json(&bound,5,|_|())?;},_=>{out.with_next_verified_json(&bound,&n,5,|_|())?;}}
        let calls=b.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);b.repository().calls.store(0,Ordering::SeqCst);b.repository().trigger.store(calls,Ordering::SeqCst);let called=Cell::new(false);
        match stage{0=>assert!(Product::prepare_json(&bound,&bytes,Default::default(),6).is_err()),1=>assert!(out.verify(&bound,6).is_err()),2=>assert!(out.with_verified_json(&bound,6,|_|called.set(true)).is_err()),_=>assert!(out.with_next_verified_json(&bound,&n,6,|_|called.set(true)).is_err())}
        assert!(!called.get());assert_eq!(b.repository().calls.load(Ordering::SeqCst),calls);}
    Ok(())
}
#[test]
fn selector_control_product_cursor_preserves_regions_and_binds_scope_policy_kind_raw_key_and_strict_next()->TestResult{
    let raw=fixture::with_body(&body().replace("CACHE FROZEN",&format!("CACHE{TAB} FROZEN")))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=envelope(&s,&raw)?;let out=prepare!(&p,&good)?;let mut cursor=Value::Null;
    for i in 0..3{let value:Value=out.with_next_verified_json(&p,&wire(&next(&out,cursor,false)?)?,5,|b|serde_json::from_slice(b))??;assert_eq!(value["match_index"],i);assert_eq!(value["region"],if i==1{"memo_body"}else{"body_and_notes"});assert_eq!(value["selection"]["kind"],"control");cursor=value["cursor"].clone();}
    let exhausted:Value=out.with_next_verified_json(&p,&wire(&next(&out,cursor.clone(),false)?)?,5,|b|serde_json::from_slice(b))??;assert_eq!(exhausted["exhausted"],true);assert_eq!(exhausted["cursor"],cursor);
    let first:Value=out.with_next_verified_json(&p,&wire(&next(&out,cursor,true)?)?,5,|b|serde_json::from_slice(b))??;assert_eq!(first["wrapped"],true);assert_eq!(first["match_index"],0);
    let inv=inventory(&p,&good)?;for mode in 0..5{let mut v=good.clone();match mode{0=>v["operation"]["query"]=json!("line_break"),1=>v["operation"]["review_policy"]=policy(false,false),2=>v["idempotency_key"]=json!("OTHER-KEY"),3=>{v["selector"]["scope"]=json!("section");v["selector"]["section_ids"]=inv["inventory"]["section_ids"].clone();},_=>{}}
        let bytes=if mode==4{serde_json::to_vec_pretty(&v)?}else{wire(&v)?};let other=Product::prepare_json(&p,&bytes,Default::default(),4)?;let called=Cell::new(false);assert!(other.with_next_verified_json(&p,&wire(&next(&other,first["cursor"].clone(),false)?)?,5,|_|called.set(true)).is_err());assert!(!called.get());}
    let before=s.metadata.audit_events()?.len();let mut bad=next(&out,Value::Null,false)?;bad["approved"]=json!(true);assert!(matches!(out.with_next_verified_json(&p,&wire(&bad)?,5,|_|()),Err(E::Request)));assert_eq!(s.metadata.audit_events()?.len(),before);
    let mut bytes=wire(&next(&out,Value::Null,false)?)?;bytes.resize(16*1024,b' ');out.with_next_verified_json(&p,&bytes,5,|_|())?;bytes.push(b' ');assert!(matches!(out.with_next_verified_json(&p,&bytes,5,|_|()),Err(E::Limit)));Ok(())
}
#[test]
fn selector_control_product_cross_run_nfc_and_ambiguous_reordered_stale_or_foreign_boundaries_remain_exact()->TestResult{
    for reorder in[false,true]{let body=if reorder{format!("<hp:p id='1'><hp:run><hp:t>x\u{315}\u{300}{TAB}Z</hp:t></hp:run></hp:p>")}else{format!("<hp:p id='1'><hp:run><hp:t>Aᄀ</hp:t></hp:run><hp:run><hp:t>ᅡ</hp:t></hp:run><hp:run><hp:t>ᆨ{TAB}Z</hp:t></hp:run></hp:p>")};
        let raw=fixture::with_body(&body)?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=envelope(&s,&raw)?;let inv=inventory(&p,&v)?;
        v["selector"]["scope"]=json!("selection");v["selector"]["range"]=selection(&inv,0,2,if reorder{4}else{3})?;
        if reorder{assert!(matches!(prepare!(&p,&v),Err(E::Stored(hwpx_agent_cli::form_stored_provider::actual_import::source_search::StoredSourceSearchError::Search(SearchError::Scope)))));v["selector"]["range"]=selection(&inv,0,3,4)?;}
        assert_eq!(response!(&p,&v)["control_matches"].as_array().ok_or("controls")?.len(),1);
        for key in["index_sha256","paragraph_handle"]{let mut bad=v.clone();if key=="index_sha256"{bad["selector"]["range"][key]=json!("0".repeat(64));}else{bad["selector"]["range"]["start"][key]=json!("foreign");}assert!(prepare!(&p,&bad).is_err());}}
    Ok(())
}
#[test]
fn selector_control_product_limits_owned_results_private_receipts_and_original_preservation_do_not_grant_execution()->TestResult{
    let raw=raw()?;let original=ContentDigest::of(&raw);let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=envelope(&s,&raw)?;
    assert!(Product::prepare_json(&p,&wire(&v)?,SourceSearchLimits::new(Config{result_bytes:1,..Default::default()})?,4).is_err());
    v["operation"]["max_results"]=json!(1);assert!(prepare!(&p,&v).is_err());v["operation"]["max_results"]=json!(100);
    let out=prepare!(&p,&v)?;drop(v);out.verify(&p,5)?;let value:Value=out.with_verified_json(&p,5,|b|serde_json::from_slice(b))??;
    assert_eq!(value["native_visibility_flow_control_semantics_or_execution_authority"],false);assert!(!serde_json::to_string(&value)?.contains("PRIVATE-AUTHOR"));assert!(!format!("{out:?}{:?}",out.receipt()).contains("PRIVATE-CONTROL-KEY"));
    assert!(matches!(out.require_current_product_route(&p,5),Err(E::RouteUnqualified)));assert!(!out.receipt().idempotency_key_claimed&&!out.receipt().full_search_product_native_cas_execution_publication_authority);
    assert_eq!(ContentDigest::of(&raw),original);assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
}
