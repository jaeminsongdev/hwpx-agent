use super::*;
use hwpx_agent_cli::form_product_request::stored_source_search::{StoredSourceSearchProductRequest as Product,
    PreparedStoredSourceSearchProduct as Prepared,SourceSearchProductError as E,SOURCE_SEARCH_PRODUCT_MAX_REQUEST_BYTES,
    navigation::SOURCE_SEARCH_NEXT_REQUEST_SCHEMA};
use serde_json::{json,Value};
use std::{cell::Cell,sync::atomic::AtomicUsize};
use revision_service as rev;
#[path="../../../../hwpx-package/tests/support/search_review_fixture.rs"] mod review;
#[path="../../../../hwpx-package/tests/support/search_definition_fixture.rs"] mod definition;
macro_rules! write_provider {($s:ident,$actor:ident,$provider:ident)=>{
    let $actor=RequestContext::new($s.reader.tenant_id(),$s.reader.subject(),[AuthScope::DocumentRead,AuthScope::DocumentWrite]);
    let $provider=StoredFormProvider::bind(&$s.artifacts,&$s.revisions,&$actor,&$s.revision_context,$s.project,$s.branch,DocumentId::parse("actual-form-document")?)?;
}}
fn bytes()->Result<Vec<u8>,Box<dyn std::error::Error>> {review::with_body("<hp:p id='1'><hp:run><hp:t>PRIVATE K K</hp:t></hp:run></hp:p><hp:p id='2'><hp:run><hp:t>K</hp:t></hp:run></hp:p>")}
fn envelope(s:&StoredFixture,b:&[u8])->Result<Value,Box<dyn std::error::Error>> {Ok(json!({
    "schema_version":"hwpx-agent.product-source-search-request/v1","idempotency_key":"PRIVATE-NAVIGATION-KEY",
    "project_id":s.project.public_id(),"document_id":"actual-form-document","base_revision":s.head.revision_id().ok_or("head")?.public_id(),
    "expected_head_generation":s.head.generation(),"expected_source_package_sha256":ContentDigest::of(b).hex(),"plan_id":"navigation-plan",
    "scope":{"kind":"mapped_document","paragraph_handles":[]},
    "operation":{"kind":"find_literal","query":"K","case_sensitive":true,"whole_word":false,"max_results":100}}))}
fn next(prepared:&Prepared,cursor:Value,direction:&str,wrap:bool)->Result<Value,Box<dyn std::error::Error>> {Ok(json!({
    "schema_version":SOURCE_SEARCH_NEXT_REQUEST_SCHEMA,"search_receipt_sha256":prepared.navigation_receipt_sha256()?,
    "navigation":{"direction":direction,"wrap":wrap,"cursor":cursor}}))}
#[test]
fn navigation_product_all_retained_search_variants_advance_without_new_search_ingest_or_revision()->TestResult {
    let body=review::body().replacen("<hp:run>","<hp:run charPrIDRef='1'>",1);let raw=definition::package(&body)?;
    let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for (kind,version,count) in [("find_literal",1,2),("find_regex",1,2),("find_declared_style",2,2),
        ("find_control",2,1),("find_definition_style",3,2),("find_review_literal",4,4),("find_review_regex",4,4)] {
        let mut v=envelope(&s,&raw)?;v["schema_version"]=json!(format!("hwpx-agent.product-source-search-request/v{version}"));v["operation"]["kind"]=json!(kind);
        match kind {"find_declared_style"=>v["operation"]["style_filter"]=json!({"run_character_property":1}),
            "find_definition_style"=>v["operation"]["definition_filter"]=json!({"character_source":"run_property","bold":true}),
            "find_control"=>v["operation"]["query"]=json!("hidden_comment"),
            "find_review_literal"|"find_review_regex"=>v["operation"]["review_policy"]=json!({"include_hidden_explanations":true,"include_memo_bodies":true}),_=>{}}
        let prepared=Product::prepare_json(&provider,&serde_json::to_vec(&v)?,Default::default(),4)?;let mut cursor=Value::Null;
        for i in 0..count {let request=serde_json::to_vec(&next(&prepared,cursor,"forward",false)?)?;
            let result:Value=prepared.with_next_verified_json(&provider,&request,5,|b|serde_json::from_slice(b))??;
            assert_eq!(result["match_index"],i);assert_eq!(result["total_matches"],count);assert_eq!(result["exhausted"],false);
            assert_eq!(result["full_search_native_or_execution_authority"],false);assert_eq!(result["selection"]["kind"],if kind=="find_control" {"control"}else{"text"});
            if kind.starts_with("find_review")&&i==1 {assert_eq!(result["region"],"hidden_explanation");}cursor=result["cursor"].clone();
        }
        let request=serde_json::to_vec(&next(&prepared,cursor.clone(),"forward",false)?)?;
        let exhausted:Value=prepared.with_next_verified_json(&provider,&request,5,|b|serde_json::from_slice(b))??;assert_eq!(exhausted["exhausted"],true);assert_eq!(exhausted["cursor"],cursor);
        let wrapped:Value=prepared.with_next_verified_json(&provider,&serde_json::to_vec(&next(&prepared,cursor,"forward",true)?)?,5,|b|serde_json::from_slice(b))??;
        assert_eq!(wrapped["match_index"],0);assert_eq!(wrapped["wrapped"],true);assert!(matches!(prepared.require_current_product_route(&provider,5),Err(E::RouteUnqualified)));
    }
    assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);Ok(())
}
#[test]
fn navigation_product_cursor_context_binds_original_key_plan_query_scope_and_raw_preparation()->TestResult {
    let raw=bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let v=envelope(&s,&raw)?;let prepared=Product::prepare_json(&provider,&serde_json::to_vec(&v)?,Default::default(),4)?;
    let first:Value=prepared.with_next_verified_json(&provider,&serde_json::to_vec(&next(&prepared,Value::Null,"forward",false)?)?,5,|b|serde_json::from_slice(b))??;
    for mode in 0..5 {let mut changed=v.clone();match mode {0=>changed["idempotency_key"]=json!("OTHER-KEY"),1=>changed["plan_id"]=json!("other-plan"),
        2=>changed["operation"]["case_sensitive"]=json!(false),3=>changed["scope"]=json!({"kind":"paragraphs","paragraph_handles":[first["selection"]["match"]["paragraph_anchor"]["opaque_handle"].clone()]}),_=>{}}
        let wire=if mode==4 {serde_json::to_vec_pretty(&changed)?}else{serde_json::to_vec(&changed)?};let other=Product::prepare_json(&provider,&wire,Default::default(),4)?;
        let called=Cell::new(false);assert!(other.with_next_verified_json(&provider,&serde_json::to_vec(&next(&other,first["cursor"].clone(),"forward",false)?)?,5,|_|called.set(true)).is_err());assert!(!called.get());
    }assert!(!format!("{prepared:?}{:?}",prepared.receipt()).contains("PRIVATE-NAVIGATION-KEY"));Ok(())
}
#[test]
fn navigation_product_strict_json_and_mismatched_preparation_fail_before_artifact_reads()->TestResult {
    let raw=bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let prepared=Product::prepare_json(&provider,&serde_json::to_vec(&envelope(&s,&raw)?)?,Default::default(),4)?;
    let good=next(&prepared,Value::Null,"forward",false)?;let before=s.metadata.audit_events()?.len();let mut invalid=vec![b"null".to_vec(),b"[]".to_vec(),b"".to_vec()];
    for (key,value) in [("schema_version",json!("other")),("search_receipt_sha256",json!("A".repeat(64))),
        ("navigation",json!(["forward",false])),("approved",json!(true)),("query",json!("K")),("output_path",json!("D:/do-not-write"))] {
        let mut v=good.clone();v[key]=value;invalid.push(serde_json::to_vec(&v)?);}
    for value in [json!({"direction":"all","wrap":false}),json!({"direction":"forward","wrap":0}),json!({"direction":"forward"}),
        json!({"direction":"forward","wrap":false,"cursor":[]}),json!({"direction":"forward","wrap":false,"cursor":{},"native_verified":true})] {
        let mut v=good.clone();v["navigation"]=value;invalid.push(serde_json::to_vec(&v)?);}
    let duplicate=serde_json::to_string(&good)?.replace("\"wrap\":false","\"wrap\":false,\"wr\\u0061p\":true");invalid.push(duplicate.into_bytes());
    for value in invalid {assert!(prepared.with_next_verified_json(&provider,&value,5,|_|()).is_err());}
    let mut foreign=good.clone();foreign["search_receipt_sha256"]=json!("0".repeat(64));assert!(matches!(prepared.with_next_verified_json(&provider,&serde_json::to_vec(&foreign)?,5,|_|()),Err(E::Binding)));
    assert_eq!(s.metadata.audit_events()?.len(),before);
    let mut exact=serde_json::to_vec(&good)?;exact.resize(SOURCE_SEARCH_PRODUCT_MAX_REQUEST_BYTES,b' ');prepared.with_next_verified_json(&provider,&exact,5,|_|())?;
    exact.push(b' ');assert!(matches!(prepared.with_next_verified_json(&provider,&exact,5,|_|()),Err(E::Limit)));Ok(())
}
#[test]
fn navigation_product_write_scope_foreign_provider_and_revoked_acl_never_expose_retained_selection()->TestResult {
    let raw=bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let prepared=Product::prepare_json(&provider,&serde_json::to_vec(&envelope(&s,&raw)?)?,Default::default(),4)?;let request=serde_json::to_vec(&next(&prepared,Value::Null,"forward",false)?)?;
    let called=Cell::new(false);let reader=s.provider()?;assert!(prepared.with_next_verified_json(&reader,&request,5,|_|called.set(true)).is_err());assert!(!called.get());
    let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("foreign-navigation")?)?;
    assert!(prepared.with_next_verified_json(&other,&request,5,|_|called.set(true)).is_err());assert!(!called.get());
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;
    assert!(prepared.with_next_verified_json(&provider,&request,6,|_|called.set(true)).is_err());assert!(!called.get());Ok(())
}
#[test]
fn navigation_product_quarantine_and_aead_tampering_deny_each_retained_cursor_output()->TestResult {
    for tamper in [false,true] {let raw=bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
        let prepared=Product::prepare_json(&provider,&serde_json::to_vec(&envelope(&s,&raw)?)?,Default::default(),4)?;
        let first:Value=prepared.with_next_verified_json(&provider,&serde_json::to_vec(&next(&prepared,Value::Null,"forward",false)?)?,5,|b|serde_json::from_slice(b))??;
        if tamper {s.blobs.tamper.store(true,Ordering::SeqCst);}else{s.artifacts.quarantine(&s.owner,s.result,artifact_service::QuarantineReason::parse("NAVIGATION_QUARANTINE")?,5)?;}
        let called=Cell::new(false);assert!(prepared.with_next_verified_json(&provider,&serde_json::to_vec(&next(&prepared,first["cursor"].clone(),"forward",false)?)?,6,|_|called.set(true)).is_err());assert!(!called.get());
    }Ok(())
}
struct BoundaryRepo {inner:rev::InMemoryRevisionRepository,calls:AtomicUsize,trigger:AtomicUsize,context:rev::RevisionRequestContext,advance:rev::RevisionCommitRequest}
impl rev::RevisionRepository for BoundaryRepo {
    fn compare_and_swap(&self,c:&rev::RevisionRequestContext,r:&rev::RevisionCommitRequest)->Result<rev::CommitOutcome,rev::RevisionError>{self.inner.compare_and_swap(c,r)}
    fn head(&self,t:TenantId,p:rev::ProjectId,b:rev::BranchId)->Result<rev::RevisionHead,rev::RevisionError>{let call=self.calls.fetch_add(1,Ordering::SeqCst)+1;
        if call==self.trigger.load(Ordering::SeqCst){assert!(matches!(self.inner.compare_and_swap(&self.context,&self.advance)?,rev::CommitOutcome::Committed(_)));}self.inner.head(t,p,b)}
    fn node(&self,t:TenantId,p:rev::ProjectId,r:rev::RevisionId)->Result<rev::RevisionNode,rev::RevisionError>{self.inner.node(t,p,r)}
}
#[test]
fn navigation_product_last_head_boundary_rejects_selection_before_consumer_delivery()->TestResult {
    let raw=bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let prepared=Product::prepare_json(&provider,&serde_json::to_vec(&envelope(&s,&raw)?)?,Default::default(),4)?;let request=serde_json::to_vec(&next(&prepared,Value::Null,"forward",false)?)?;
    let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),
        artifact_service::ArtifactId::generate(),s.result,None,ContentDigest::of(b"navigation race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation"),ContentDigest::of(b"transaction"))?;
    let boundary=rev::RevisionService::new(BoundaryRepo {inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
    let bound=StoredFormProvider::bind(&s.artifacts,&boundary,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
    prepared.with_next_verified_json(&bound,&request,5,|_|())?;let calls=boundary.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);
    boundary.repository().calls.store(0,Ordering::SeqCst);boundary.repository().trigger.store(calls,Ordering::SeqCst);let called=Cell::new(false);
    assert!(prepared.with_next_verified_json(&bound,&request,6,|_|called.set(true)).is_err());assert!(!called.get());assert_eq!(boundary.repository().calls.load(Ordering::SeqCst),calls);Ok(())
}
#[test]
fn navigation_product_zero_width_exhaustion_empty_result_and_stale_cursor_are_explicit_and_private()->TestResult {
    let raw=bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let mut v=envelope(&s,&raw)?;v["operation"]["kind"]=json!("find_regex");v["operation"]["query"]=json!("^|$");
    let prepared=Product::prepare_json(&provider,&serde_json::to_vec(&v)?,Default::default(),4)?;let mut cursor=Value::Null;
    for expected in 0..4 {let n:Value=prepared.with_next_verified_json(&provider,&serde_json::to_vec(&next(&prepared,cursor,"forward",false)?)?,5,|b|serde_json::from_slice(b))??;
        assert_eq!(n["match_index"],expected);assert_eq!(n["selection"]["match"]["zero_width"],true);assert!(!serde_json::to_string(&n)?.contains("PRIVATE"));cursor=n["cursor"].clone();}
    v["operation"]["query"]=json!("NO-MATCH-PRIVATE");let empty=Product::prepare_json(&provider,&serde_json::to_vec(&v)?,Default::default(),4)?;
    let n:Value=empty.with_next_verified_json(&provider,&serde_json::to_vec(&next(&empty,Value::Null,"backward",true)?)?,5,|b|serde_json::from_slice(b))??;
    assert_eq!(n["total_matches"],0);assert_eq!(n["exhausted"],true);assert!(n["cursor"].is_null());assert!(!serde_json::to_string(&n)?.contains("PRIVATE"));
    let called=Cell::new(false);assert!(empty.with_next_verified_json(&provider,&serde_json::to_vec(&next(&empty,cursor,"forward",false)?)?,5,|_|called.set(true)).is_err());assert!(!called.get());Ok(())
}
