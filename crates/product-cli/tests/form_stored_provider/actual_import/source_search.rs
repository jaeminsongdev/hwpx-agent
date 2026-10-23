use super::*;
use super::field_ranges::fixture;
use hwpx_agent_cli::form_product_request::stored_source_search::{StoredSourceSearchProductRequest as Product,
    SourceSearchProductError as E,SOURCE_SEARCH_PRODUCT_REQUEST_SCHEMA,SOURCE_SEARCH_PRODUCT_MAX_REQUEST_BYTES};
use hwpx_agent_cli::form_stored_provider::actual_import::source_search::StoredSourceSearchError;
use hwpx_package::document_import::search::{SourceSearchLimits,SourceSearchLimitConfig as Config};
use serde_json::{json,Value};
use std::{cell::Cell,sync::atomic::AtomicUsize};
use revision_service as rev;
macro_rules! write_provider {($s:ident,$actor:ident,$provider:ident)=>{
    let $actor=RequestContext::new($s.reader.tenant_id(),$s.reader.subject(),[AuthScope::DocumentRead,AuthScope::DocumentWrite]);
    let $provider=StoredFormProvider::bind(&$s.artifacts,&$s.revisions,&$actor,&$s.revision_context,$s.project,$s.branch,DocumentId::parse("actual-form-document")?)?;
}}
fn bytes()->Result<Vec<u8>,Box<dyn std::error::Error>> {fixture::package("<hp:p id='1'><hp:run><hp:t>PRIVATE-</hp:t></hp:run><hp:run><hp:t>QUERY</hp:t></hp:run></hp:p><hp:p id='2'><hp:run><hp:t>PRIVATE-QUERY</hp:t></hp:run></hp:p>")}
fn envelope(s:&StoredFixture,b:&[u8])->Result<Value,Box<dyn std::error::Error>> {Ok(json!({
    "schema_version":SOURCE_SEARCH_PRODUCT_REQUEST_SCHEMA,"idempotency_key":"PRIVATE-SEARCH-KEY",
    "project_id":s.project.public_id(),"document_id":"actual-form-document","base_revision":s.head.revision_id().ok_or("head")?.public_id(),
    "expected_head_generation":s.head.generation(),"expected_source_package_sha256":ContentDigest::of(b).hex(),"plan_id":"source-search-plan",
    "scope":{"kind":"mapped_document","paragraph_handles":[]},
    "operation":{"kind":"find_literal","query":"PRIVATE-QUERY","case_sensitive":true,"whole_word":false,"max_results":100}}))}
fn wire(v:&Value)->Result<Vec<u8>,serde_json::Error> {serde_json::to_vec(v)}
#[test]
fn search_product_literal_regex_and_paragraph_scope_run_on_provider_source_without_caller_import()->TestResult {
    let raw=bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for kind in ["find_literal","find_regex"] {
        let mut v=envelope(&s,&raw)?;v["operation"]["kind"]=json!(kind);
        let result=Product::prepare_json(&provider,&wire(&v)?,Default::default(),4)?;
        result.verify(&provider,5)?;
        let all:Value=result.with_verified_json(&provider,5,|b|serde_json::from_slice(b))??;
        assert_eq!(all["result"]["matches"].as_array().ok_or("matches")?.len(),2);
        assert_eq!(all["scope"]["selected_paragraphs"],2);assert_eq!(all["scope"]["whole_document_visibility_qualified"],false);
        v["scope"]=json!({"kind":"paragraphs","paragraph_handles":[all["result"]["matches"][0]["paragraph_anchor"]["opaque_handle"].clone()]});
        let selected=Product::prepare_json(&provider,&wire(&v)?,Default::default(),5)?;
        let one:Value=selected.with_verified_json(&provider,5,|b|serde_json::from_slice(b))??;
        assert_eq!(one["result"]["matches"].as_array().ok_or("matches")?.len(),1);
        assert_ne!(result.receipt().stored.scope.scope_sha256,selected.receipt().stored.scope.scope_sha256);
        assert!(matches!(selected.require_current_product_route(&provider,5),Err(E::RouteUnqualified)));
    }
    assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);
    assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);Ok(())
}
#[test]
fn search_product_strict_json_and_unsupported_full_search_options_fail_before_artifact_reads()->TestResult {
    let raw=bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let v=envelope(&s,&raw)?;let good=serde_json::to_string(&v)?;let before=s.metadata.audit_events()?.len();
    let mut bad=vec!["null".into(),"[]".into(),format!("{good} {{}}"),format!("{{\"schema_version\":\"bad\",{}",&good[1..]),
        good.replace("\"query\":\"PRIVATE-QUERY\"","\"query\":\"PRIVATE-QUERY\",\"qu\\u0065ry\":\"OTHER\"")];
    for key in ["schema_version","idempotency_key","project_id","document_id","base_revision","expected_head_generation","expected_source_package_sha256","plan_id","scope","operation"] {
        let mut x=v.clone();x.as_object_mut().ok_or("object")?.remove(key);bad.push(serde_json::to_string(&x)?);
    }
    for (key,value) in [("schema_version",json!("other-schema")),("operation",json!(["find_literal"])),("scope",json!(["mapped_document"])),
        ("output_path",json!("D:/do-not-write")),("approved",json!(true)),("expected_head_generation",json!(0)),
        ("expected_source_package_sha256",json!("A".repeat(64))),("document_id",json!("d".repeat(1025)))] {
        let mut x=v.clone();x[key]=value;bad.push(serde_json::to_string(&x)?);
    }
    for (key,value) in [("include_hidden",json!(true)),("style_filter",json!({})),("regex",json!(true)),("native_verified",json!(true)),
        ("query",json!("")),("query",json!("q".repeat(4097))),("max_results",json!(0)),("max_results",json!(10001)),("kind",json!("replace_literal"))] {
        let mut x=v.clone();x["operation"][key]=value;bad.push(serde_json::to_string(&x)?);
    }
    for scope in [json!({"kind":"paragraphs","paragraph_handles":[]}),json!({"kind":"mapped_document","paragraph_handles":["foreign"]}),
        json!({"kind":"paragraphs","paragraph_handles":["same","same"]}),json!({"kind":"mapped_document","paragraph_handles":[],"whole_document_qualified":true})] {
        let mut x=v.clone();x["scope"]=scope;bad.push(serde_json::to_string(&x)?);
    }
    for b in bad {assert!(matches!(Product::prepare_json(&provider,b.as_bytes(),Default::default(),4),Err(E::Request)));}
    assert_eq!(s.metadata.audit_events()?.len(),before);
    let mut exact=good.into_bytes();exact.resize(SOURCE_SEARCH_PRODUCT_MAX_REQUEST_BYTES,b' ');
    Product::prepare_json(&provider,&exact,Default::default(),4)?;exact.push(b' ');
    assert!(matches!(Product::prepare_json(&provider,&exact,Default::default(),4),Err(E::Limit)));
    assert!(matches!(Product::prepare_json(&provider,b"",Default::default(),4),Err(E::Limit)));Ok(())
}
#[test]
fn search_product_raw_canonical_key_plan_query_and_scope_bindings_do_not_claim_idempotency()->TestResult {
    let raw=bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let v=envelope(&s,&raw)?;let first=Product::prepare_json(&provider,&wire(&v)?,Default::default(),4)?;
    let pretty=Product::prepare_json(&provider,&serde_json::to_vec_pretty(&v)?,Default::default(),4)?;
    assert_ne!(first.receipt().raw_request_sha256,pretty.receipt().raw_request_sha256);
    assert_eq!(first.receipt().canonical_request_sha256,pretty.receipt().canonical_request_sha256);
    for (key,value) in [("idempotency_key",json!("PRIVATE-SECOND-KEY")),("plan_id",json!("another-search-plan"))] {
        let mut x=v.clone();x[key]=value;let other=Product::prepare_json(&provider,&wire(&x)?,Default::default(),4)?;
        assert_ne!(first.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);
        assert_ne!(first.receipt().scoped_request_sha256,other.receipt().scoped_request_sha256);
        assert_eq!(first.receipt().stored.result_sha256,other.receipt().stored.result_sha256);
    }
    let mut x=v.clone();x["operation"]["case_sensitive"]=json!(false);let other=Product::prepare_json(&provider,&wire(&x)?,Default::default(),4)?;
    assert_ne!(first.receipt().stored.query_sha256,other.receipt().stored.query_sha256);
    let mut forged=first.receipt().clone();forged.idempotency_key_claimed=true;
    assert_ne!(forged,first.verify(&provider,5)?);assert!(!first.receipt().full_search_product_native_cas_execution_publication_authority);Ok(())
}
#[test]
fn search_product_write_scope_and_foreign_head_source_bindings_are_required()->TestResult {
    let raw=bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;let reader=s.provider()?;
    let v=envelope(&s,&raw)?;let before=s.metadata.audit_events()?.len();
    assert!(matches!(Product::prepare_json(&reader,&wire(&v)?,Default::default(),4),Err(E::Stored(StoredSourceSearchError::Permission))));
    assert_eq!(s.metadata.audit_events()?.len(),before);write_provider!(s,actor,provider);
    let prepared=Product::prepare_json(&provider,&wire(&v)?,Default::default(),4)?;
    let called=Cell::new(false);assert!(prepared.with_verified_json(&reader,5,|_|called.set(true)).is_err());assert!(!called.get());
    for (key,value) in [("project_id",json!("prj_70000000000000000000000000000002")),("document_id",json!("other-document")),
        ("base_revision",json!(rev::RevisionId::generate().public_id())),("expected_head_generation",json!(s.head.generation()+1)),
        ("expected_source_package_sha256",json!("0".repeat(64)))] {
        let mut wrong=v.clone();wrong[key]=value;assert!(Product::prepare_json(&provider,&wire(&wrong)?,Default::default(),5).is_err());
    }Ok(())
}
#[test]
fn search_product_each_foreign_provider_scope_cannot_reauthorize_retained_results()->TestResult {
    let raw=bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let prepared=Product::prepare_json(&provider,&wire(&envelope(&s,&raw)?)?,Default::default(),4)?;
    for variant in 0..5 {
        let tenant=if variant==4 {TenantId::new(uuid::Uuid::from_u128(702))?}else{s.reader.tenant_id()};
        let subject=if variant==3 {s.owner.subject()}else{s.reader.subject()};
        let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);
        let context=rev::RevisionRequestContext::new(tenant,subject);
        let project=if variant==2 {rev::ProjectId::parse("prj_70000000000000000000000000000002")?}else{s.project};
        let branch=if variant==1 {rev::BranchId::parse("brn_70000000000000000000000000000002")?}else{s.branch};
        let document=DocumentId::parse(if variant==0 {"other-document"}else{"actual-form-document"})?;
        let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&context,project,branch,document)?;
        let called=Cell::new(false);assert!(prepared.with_verified_json(&other,5,|_|called.set(true)).is_err());assert!(!called.get());
        assert!(prepared.verify(&other,5).is_err());
    }Ok(())
}
#[test]
fn search_product_revoked_acl_quarantine_aead_and_regrant_recheck_current_access()->TestResult {
    for mode in 0..3 {
        let raw=bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
        let v=wire(&envelope(&s,&raw)?)?;let prepared=Product::prepare_json(&provider,&v,Default::default(),4)?;let _receipt=prepared.verify(&provider,4)?;
        match mode {0=>{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;},
            1=>{s.artifacts.quarantine(&s.owner,s.result,artifact_service::QuarantineReason::parse("SEARCH_TEST_QUARANTINE")?,5)?;},
            _=>s.blobs.tamper.store(true,Ordering::SeqCst)}
        let called=Cell::new(false);assert!(prepared.with_verified_json(&provider,6,|_|called.set(true)).is_err());assert!(!called.get());
        assert!(prepared.verify(&provider,6).is_err());assert!(Product::prepare_json(&provider,&v,Default::default(),6).is_err());
        if mode==0 {s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([artifact_service::ArtifactPermission::Read]),7)?;
            prepared.verify(&provider,8)?;}
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
fn search_product_prepare_verify_and_final_consumer_head_races_reject_results()->TestResult {
    for stage in 0..3 {
        let raw=bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
        let v=wire(&envelope(&s,&raw)?)?;let prepared=Product::prepare_json(&provider,&v,Default::default(),4)?;
        let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),
            s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,ContentDigest::of(b"search race"),
            rev::RevisionValidationState::Verified,ContentDigest::of(b"validation fixture"),ContentDigest::of(b"transaction fixture"))?;
        let boundary=rev::RevisionService::new(BoundaryRepo {inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
        let bound=StoredFormProvider::bind(&s.artifacts,&boundary,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
        match stage {0=>{Product::prepare_json(&bound,&v,Default::default(),5)?;},1=>{prepared.verify(&bound,5)?;},_=>{prepared.with_verified_json(&bound,5,|_|())?;}}
        let calls=boundary.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);
        boundary.repository().calls.store(0,Ordering::SeqCst);boundary.repository().trigger.store(calls,Ordering::SeqCst);
        let called=Cell::new(false);
        match stage {0=>assert!(Product::prepare_json(&bound,&v,Default::default(),6).is_err()),
            1=>assert!(prepared.verify(&bound,6).is_err()),_=>assert!(prepared.with_verified_json(&bound,6,|_|called.set(true)).is_err())}
        assert!(!called.get());assert_eq!(boundary.repository().calls.load(Ordering::SeqCst),calls);assert!(prepared.verify(&provider,7).is_err());
    }Ok(())
}
#[test]
fn search_product_invalid_pattern_foreign_paragraph_and_resource_limits_never_return_partial_matches()->TestResult {
    let raw=bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let v=envelope(&s,&raw)?;
    for config in [Config {scalars:1,..Default::default()},Config {result_bytes:1,..Default::default()},Config {matches:1,..Default::default()}] {
        assert!(Product::prepare_json(&provider,&wire(&v)?,SourceSearchLimits::new(config)?,4).is_err());
    }
    let mut x=v.clone();x["operation"]["kind"]=json!("find_regex");x["operation"]["query"]=json!("[");
    assert!(Product::prepare_json(&provider,&wire(&x)?,Default::default(),4).is_err());
    x=v.clone();x["scope"]=json!({"kind":"paragraphs","paragraph_handles":["foreign-handle"]});x["operation"]["query"]=json!("no-match");
    assert!(Product::prepare_json(&provider,&wire(&x)?,Default::default(),4).is_err());Ok(())
}
#[test]
fn search_product_zero_matches_are_explicit_partial_coverage_and_do_not_disclose_text_or_query()->TestResult {
    let raw=bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let mut v=envelope(&s,&raw)?;v["operation"]["query"]=json!("PRIVATE-ABSENT");
    let result=Product::prepare_json(&provider,&wire(&v)?,Default::default(),4)?;
    let output=result.with_verified_json(&provider,5,<[u8]>::to_vec)?;let json:Value=serde_json::from_slice(&output)?;
    assert_eq!(json["result"]["matches"],json!([]));assert_eq!(json["result"]["index"]["whole_document_visibility_and_search_qualified"],false);
    assert!(!String::from_utf8(output)?.contains("PRIVATE"));assert!(!format!("{result:?}{:?}",result.receipt()).contains("PRIVATE"));
    assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
}

// Additive v2 inspection cases; all nine original v1 test bodies above remain unchanged.
fn inspection_bytes()->Result<Vec<u8>,Box<dyn std::error::Error>> {fixture::package("<hp:p id='1' paraPrIDRef='2'><hp:run charPrIDRef='4'><hp:t>PRIVATE-QUERY</hp:t><hp:pic/></hp:run></hp:p><hp:p id='2'><hp:run charPrIDRef='5'><hp:t>PRIVATE-QUERY</hp:t><hp:ctrl><hp:fieldBegin id='17' type='DATE'/></hp:ctrl><hp:ctrl><hp:fieldEnd beginIDRef='17'/></hp:ctrl></hp:run></hp:p>")}
fn inspection_envelope(s:&StoredFixture,b:&[u8],style:bool)->Result<Value,Box<dyn std::error::Error>> {
    let mut value=envelope(s,b)?;
    value["schema_version"]=json!(hwpx_agent_cli::form_product_request::stored_source_search::SOURCE_SEARCH_INSPECTION_REQUEST_SCHEMA);
    if style {value["operation"]["kind"]=json!("find_declared_style");value["operation"]["style_filter"]=json!({"run_character_property":4});}
    else {value["operation"]["kind"]=json!("find_control");value["operation"]["query"]=json!("picture");}
    Ok(value)
}
#[test]
fn search_inspection_product_v2_style_and_control_searches_deliver_original_positions_with_partial_coverage()->TestResult {
    let raw=inspection_bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for style in [false,true] {
        let v=inspection_envelope(&s,&raw,style)?;let result=Product::prepare_json(&provider,&wire(&v)?,Default::default(),4)?;
        assert_eq!(result.receipt().profile,"hwpx-agent.product-source-search-preparation/v2");
        assert_eq!(result.receipt().stored.profile,"hwpx-agent.stored-source-search/v2");result.verify(&provider,5)?;
        let json:Value=result.with_verified_json(&provider,5,|b|serde_json::from_slice(b))??;
        if style {assert_eq!(json["text_matches"]["matches"].as_array().ok_or("matches")?.len(),1);assert_eq!(json["control_matches"],json!([]));}
        else {assert_eq!(json["control_matches"].as_array().ok_or("controls")?.len(),1);assert!(json["text_matches"].is_null());}
        assert_eq!(json["inspection"]["style_definitions_resolved"],false);assert_eq!(json["inspection"]["effective_style_or_hidden_visibility_qualified"],false);
        assert!(!result.receipt().idempotency_key_claimed);assert!(matches!(result.require_current_product_route(&provider,5),Err(E::RouteUnqualified)));
    }
    assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);
    assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);Ok(())
}
#[test]
fn search_inspection_product_v1_rejects_new_operations_and_v2_rejects_ambiguous_or_inapplicable_filters_before_reads()->TestResult {
    let raw=inspection_bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let style=inspection_envelope(&s,&raw,true)?;let control=inspection_envelope(&s,&raw,false)?;let mut invalid=Vec::new();
    for original in [&style,&control] {let mut v=original.clone();v["schema_version"]=json!(SOURCE_SEARCH_PRODUCT_REQUEST_SCHEMA);invalid.push(v);}
    for filter in [json!({}),json!(null),json!([]),json!([null,null,4,null]),json!({"bold":true}),json!({"run_character_property":-1}),json!({"run_character_property":4294967296u64})] {
        let mut v=style.clone();v["operation"]["style_filter"]=filter;invalid.push(v);
    }
    for (key,value) in [("case_sensitive",json!(false)),("whole_word",json!(true)),("style_filter",json!({"run_character_property":4})),("query",json!("hp:pic")),("query",json!("arbitrary-native-action"))] {
        let mut v=control.clone();v["operation"][key]=value;invalid.push(v);
    }
    let mut v=envelope(&s,&raw)?;v["operation"]["style_filter"]=json!(null);invalid.push(v);
    let before=s.metadata.audit_events()?.len();
    for v in invalid {assert!(matches!(Product::prepare_json(&provider,&wire(&v)?,Default::default(),4),Err(E::Request)));}
    let duplicate=serde_json::to_string(&style)?.replace("\"run_character_property\":4","\"run_character_property\":4,\"run_character_propert\\u0079\":5");
    assert!(matches!(Product::prepare_json(&provider,duplicate.as_bytes(),Default::default(),4),Err(E::Request)));
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn search_inspection_product_filters_and_control_kinds_bind_request_result_digests_without_text_disclosure()->TestResult {
    let raw=inspection_bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let mut v=inspection_envelope(&s,&raw,true)?;let first=Product::prepare_json(&provider,&wire(&v)?,Default::default(),4)?;
    v["operation"]["style_filter"]["run_character_property"]=json!(5);let other=Product::prepare_json(&provider,&wire(&v)?,Default::default(),4)?;
    assert_ne!(first.receipt().stored.query_sha256,other.receipt().stored.query_sha256);assert_ne!(first.receipt().stored.result_sha256,other.receipt().stored.result_sha256);
    let json=first.with_verified_json(&provider,5,|b|String::from_utf8(b.to_vec()))??;assert!(!json.contains("PRIVATE"));
    let mut v=inspection_envelope(&s,&raw,false)?;v["operation"]["query"]=json!("field_begin");let field=Product::prepare_json(&provider,&wire(&v)?,Default::default(),4)?;
    let json:Value=field.with_verified_json(&provider,5,|b|serde_json::from_slice(b))??;assert_eq!(json["control_matches"][0]["kind"],"field_begin");
    assert_ne!(first.receipt().stored.query_sha256,field.receipt().stored.query_sha256);Ok(())
}
#[test]
fn search_inspection_product_both_variants_recheck_write_scope_acl_quarantine_and_aead_before_delivery()->TestResult {
    for style in [false,true] {for mode in 0..3 {
        let raw=inspection_bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
        let v=wire(&inspection_envelope(&s,&raw,style)?)?;let reader=s.provider()?;
        assert!(Product::prepare_json(&reader,&v,Default::default(),4).is_err());
        let result=Product::prepare_json(&provider,&v,Default::default(),4)?;let called=Cell::new(false);
        assert!(result.with_verified_json(&reader,5,|_|called.set(true)).is_err());assert!(!called.get());
        match mode {0=>{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;},
            1=>{s.artifacts.quarantine(&s.owner,s.result,artifact_service::QuarantineReason::parse("INSPECTION_TEST_QUARANTINE")?,5)?;},
            _=>s.blobs.tamper.store(true,Ordering::SeqCst)}
        assert!(result.with_verified_json(&provider,6,|_|called.set(true)).is_err());assert!(!called.get());assert!(result.verify(&provider,6).is_err());
        assert!(Product::prepare_json(&provider,&v,Default::default(),6).is_err());
    }}Ok(())
}
#[test]
fn search_inspection_product_both_variants_reject_prepare_verify_and_final_consumer_head_races()->TestResult {
    for style in [false,true] {for stage in 0..3 {
        let raw=inspection_bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
        let v=wire(&inspection_envelope(&s,&raw,style)?)?;let prepared=Product::prepare_json(&provider,&v,Default::default(),4)?;
        let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),
            s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,ContentDigest::of(b"inspection race"),
            rev::RevisionValidationState::Verified,ContentDigest::of(b"validation fixture"),ContentDigest::of(b"transaction fixture"))?;
        let boundary=rev::RevisionService::new(BoundaryRepo {inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
        let bound=StoredFormProvider::bind(&s.artifacts,&boundary,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
        match stage {0=>{Product::prepare_json(&bound,&v,Default::default(),5)?;},1=>{prepared.verify(&bound,5)?;},_=>{prepared.with_verified_json(&bound,5,|_|())?;}}
        let calls=boundary.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);boundary.repository().calls.store(0,Ordering::SeqCst);boundary.repository().trigger.store(calls,Ordering::SeqCst);
        let called=Cell::new(false);match stage {0=>assert!(Product::prepare_json(&bound,&v,Default::default(),6).is_err()),
            1=>assert!(prepared.verify(&bound,6).is_err()),_=>assert!(prepared.with_verified_json(&bound,6,|_|called.set(true)).is_err())}
        assert!(!called.get());assert_eq!(boundary.repository().calls.load(Ordering::SeqCst),calls);
    }}Ok(())
}

// Additive v3 definition cases; the fourteen existing v1/v2 bodies remain unchanged.
#[path="../../../../hwpx-package/tests/support/search_definition_fixture.rs"] mod definition_fixture;
fn definition_bytes()->Result<Vec<u8>,Box<dyn std::error::Error>> {definition_fixture::package(
    "<hp:p id='1' paraPrIDRef='1' styleIDRef='0'><hp:run charPrIDRef='1'><hp:t>PRIVATE-QUERY</hp:t></hp:run></hp:p><hp:p id='2' paraPrIDRef='0'><hp:run charPrIDRef='0'><hp:t>PRIVATE-QUERY</hp:t></hp:run></hp:p>")}
fn definition_envelope(s:&StoredFixture,b:&[u8])->Result<Value,Box<dyn std::error::Error>> {
    let mut v=envelope(s,b)?;v["schema_version"]=json!(hwpx_agent_cli::form_product_request::stored_source_search::SOURCE_SEARCH_DEFINITION_REQUEST_SCHEMA);
    v["operation"]["kind"]=json!("find_definition_style");v["operation"]["definition_filter"]=json!({"character_source":"run_property","bold":true});Ok(v)
}
#[test]
fn search_definition_product_returns_real_typed_style_values_over_current_source_without_caller_catalog()->TestResult {
    let raw=definition_bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let mut v=definition_envelope(&s,&raw)?;v["operation"]["definition_filter"]=json!({"character_source":"run_property","bold":true,
        "italic":true,"height_hwpunit":1000,"text_rgb":[0,0,0],"paragraph_source":"direct_property","alignment":"right"});
    let result=Product::prepare_json(&provider,&wire(&v)?,Default::default(),4)?;result.verify(&provider,5)?;
    assert_eq!(result.receipt().profile,"hwpx-agent.product-source-search-preparation/v3");assert_eq!(result.receipt().stored.profile,"hwpx-agent.stored-source-search/v3");
    let json:Value=result.with_verified_json(&provider,5,|b|serde_json::from_slice(b))??;
    assert_eq!(json["matches"]["matches"].as_array().ok_or("matches")?.len(),1);
    assert_eq!(json["definitions"]["all_present_indexed_references_resolved"],true);
    assert_eq!(json["definitions"]["implicit_cascade_or_hidden_visibility_qualified"],false);
    assert!(matches!(result.require_current_product_route(&provider,5),Err(E::RouteUnqualified)));
    assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);
    assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);Ok(())
}
#[test]
fn search_definition_product_filter_scope_and_canonical_request_bindings_do_not_grant_authority_or_expose_queries()->TestResult {
    let raw=definition_bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let v=definition_envelope(&s,&raw)?;let first=Product::prepare_json(&provider,&wire(&v)?,Default::default(),4)?;
    let pretty=Product::prepare_json(&provider,&serde_json::to_vec_pretty(&v)?,Default::default(),4)?;
    assert_eq!(first.receipt().canonical_request_sha256,pretty.receipt().canonical_request_sha256);assert_ne!(first.receipt().raw_request_sha256,pretty.receipt().raw_request_sha256);
    let json:Value=first.with_verified_json(&provider,5,|b|serde_json::from_slice(b))??;
    let mut selected=v.clone();selected["scope"]=json!({"kind":"paragraphs","paragraph_handles":[json["matches"]["matches"][0]["paragraph_anchor"]["opaque_handle"].clone()]});
    let one=Product::prepare_json(&provider,&wire(&selected)?,Default::default(),4)?;assert_ne!(first.receipt().stored.query_sha256,one.receipt().stored.query_sha256);
    let mut other=v.clone();other["operation"]["definition_filter"]["bold"]=json!(false);let other=Product::prepare_json(&provider,&wire(&other)?,Default::default(),4)?;
    assert_ne!(first.receipt().stored.query_sha256,other.receipt().stored.query_sha256);
    assert!(!first.with_verified_json(&provider,5,|b|String::from_utf8(b.to_vec()))??.contains("PRIVATE"));
    assert!(!format!("{first:?}{:?}",first.receipt()).contains("PRIVATE"));assert!(!first.receipt().idempotency_key_claimed);Ok(())
}
#[test]
fn search_definition_product_strict_axes_filters_and_legacy_schemas_reject_before_artifact_reads()->TestResult {
    let raw=definition_bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let good=definition_envelope(&s,&raw)?;let mut invalid=Vec::new();
    for schema in [SOURCE_SEARCH_PRODUCT_REQUEST_SCHEMA,hwpx_agent_cli::form_product_request::stored_source_search::SOURCE_SEARCH_INSPECTION_REQUEST_SCHEMA] {
        let mut v=good.clone();v["schema_version"]=json!(schema);invalid.push(v);
        let mut v=envelope(&s,&raw)?;v["schema_version"]=json!(schema);v["operation"]["definition_filter"]=json!(null);invalid.push(v);
    }
    for filter in [json!({}),json!(null),json!([]),json!(["run_property",true,null,null,null,null,null]),json!({"bold":true}),
        json!({"character_source":"run_property"}),json!({"alignment":"right"}),json!({"paragraph_source":"direct_property"}),
        json!({"character_source":"effective","bold":true}),json!({"character_source":"run_property","bold":true,"text_rgb":[256,0,0]}),
        json!({"character_source":"run_property","bold":true,"unknown":true})] {
        let mut v=good.clone();v["operation"]["definition_filter"]=filter;invalid.push(v);
    }
    let mut both=good.clone();both["operation"]["style_filter"]=json!({"run_character_property":1});invalid.push(both);
    let mut ignored=good.clone();ignored["operation"]["kind"]=json!("find_literal");invalid.push(ignored);
    let before=s.metadata.audit_events()?.len();
    for v in invalid {assert!(matches!(Product::prepare_json(&provider,&wire(&v)?,Default::default(),4),Err(E::Request)));}
    let duplicated=serde_json::to_string(&good)?.replace("\"bold\":true","\"bold\":true,\"bo\\u006cd\":false");
    assert!(matches!(Product::prepare_json(&provider,duplicated.as_bytes(),Default::default(),4),Err(E::Request)));
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn search_definition_product_invalid_header_dangling_references_and_bounds_cannot_return_partial_success()->TestResult {
    for raw in [bytes()?,definition_fixture::package("<hp:p id='1'><hp:run charPrIDRef='999'><hp:t>PRIVATE-QUERY</hp:t></hp:run></hp:p>")?] {
        let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
        assert!(Product::prepare_json(&provider,&wire(&definition_envelope(&s,&raw)?)?,Default::default(),4).is_err());
    }
    let raw=definition_bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let v=wire(&definition_envelope(&s,&raw)?)?;
    for config in [Config {scalars:1,..Default::default()},Config {result_bytes:1,..Default::default()}] {
        assert!(Product::prepare_json(&provider,&v,SourceSearchLimits::new(config)?,4).is_err());
    }Ok(())
}
#[test]
fn search_definition_product_current_write_acl_scope_quarantine_and_aead_protect_retained_results()->TestResult {
    for mode in 0..3 {
        let raw=definition_bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
        let v=wire(&definition_envelope(&s,&raw)?)?;let reader=s.provider()?;assert!(Product::prepare_json(&reader,&v,Default::default(),4).is_err());
        let result=Product::prepare_json(&provider,&v,Default::default(),4)?;let called=Cell::new(false);
        assert!(result.with_verified_json(&reader,5,|_|called.set(true)).is_err());assert!(!called.get());
        let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("foreign")?)?;
        assert!(result.with_verified_json(&other,5,|_|called.set(true)).is_err());assert!(!called.get());
        match mode {0=>{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;},
            1=>{s.artifacts.quarantine(&s.owner,s.result,artifact_service::QuarantineReason::parse("DEFINITION_TEST_QUARANTINE")?,5)?;},
            _=>s.blobs.tamper.store(true,Ordering::SeqCst)}
        assert!(result.with_verified_json(&provider,6,|_|called.set(true)).is_err());assert!(!called.get());assert!(result.verify(&provider,6).is_err());
        if mode==0 {s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([artifact_service::ArtifactPermission::Read]),7)?;result.verify(&provider,8)?;}
    }Ok(())
}
#[test]
fn search_definition_product_prepare_verify_and_final_delivery_head_races_do_not_expose_matches()->TestResult {
    for stage in 0..3 {
        let raw=definition_bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
        let v=wire(&definition_envelope(&s,&raw)?)?;let prepared=Product::prepare_json(&provider,&v,Default::default(),4)?;
        let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),
            s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,ContentDigest::of(b"definition race"),
            rev::RevisionValidationState::Verified,ContentDigest::of(b"validation fixture"),ContentDigest::of(b"transaction fixture"))?;
        let boundary=rev::RevisionService::new(BoundaryRepo {inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
        let bound=StoredFormProvider::bind(&s.artifacts,&boundary,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
        match stage {0=>{Product::prepare_json(&bound,&v,Default::default(),5)?;},1=>{prepared.verify(&bound,5)?;},_=>{prepared.with_verified_json(&bound,5,|_|())?;}}
        let calls=boundary.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);boundary.repository().calls.store(0,Ordering::SeqCst);boundary.repository().trigger.store(calls,Ordering::SeqCst);
        let called=Cell::new(false);match stage {0=>assert!(Product::prepare_json(&bound,&v,Default::default(),6).is_err()),
            1=>assert!(prepared.verify(&bound,6).is_err()),_=>assert!(prepared.with_verified_json(&bound,6,|_|called.set(true)).is_err())}
        assert!(!called.get());assert_eq!(boundary.repository().calls.load(Ordering::SeqCst),calls);
    }Ok(())
}

// Additive v4 review-text cases; the twenty existing product bodies remain unchanged.
#[path="../../../../hwpx-package/tests/support/search_review_fixture.rs"] mod review_text_fixture;
fn review_text_envelope(s:&StoredFixture,b:&[u8],hidden:bool,memo:bool)->Result<Value,Box<dyn std::error::Error>> {
    let mut v=envelope(s,b)?;v["schema_version"]=json!(hwpx_agent_cli::form_product_request::stored_source_search::SOURCE_SEARCH_REVIEW_REQUEST_SCHEMA);
    v["operation"]["kind"]=json!("find_review_literal");v["operation"]["query"]=json!("K");
    v["operation"]["review_policy"]=json!({"include_hidden_explanations":hidden,"include_memo_bodies":memo});Ok(v)
}
#[test]
fn search_review_product_literal_regex_and_all_four_explicit_policies_use_original_body_positions()->TestResult {
    let raw=review_text_fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for kind in ["find_review_literal","find_review_regex"] {for (hidden,memo,count) in [(false,false,2),(true,false,3),(false,true,3),(true,true,4)] {
        let mut v=review_text_envelope(&s,&raw,hidden,memo)?;v["operation"]["kind"]=json!(kind);
        let result=Product::prepare_json(&provider,&wire(&v)?,Default::default(),4)?;result.verify(&provider,5)?;
        assert_eq!(result.receipt().profile,"hwpx-agent.product-source-search-preparation/v4");assert_eq!(result.receipt().stored.profile,"hwpx-agent.stored-source-search/v4");
        let json:Value=result.with_verified_json(&provider,5,|b|serde_json::from_slice(b))??;
        assert_eq!(json["matches"]["matches"].as_array().ok_or("matches")?.len(),count);assert_eq!(json["match_regions"].as_array().ok_or("regions")?.len(),count);
        assert_eq!(json["excluded_hidden_paragraphs"],if hidden {0}else{1});assert_eq!(json["excluded_memo_paragraphs"],if memo {0}else{1});
        assert_eq!(json["app_visibility_cascade_or_full_document_search_qualified"],false);assert!(matches!(result.require_current_product_route(&provider,5),Err(E::RouteUnqualified)));
    }}
    assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);
    assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);Ok(())
}
#[test]
fn search_review_product_scope_and_policy_digests_bind_excluded_zero_results_without_text_disclosure()->TestResult {
    let raw=review_text_fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let mut v=review_text_envelope(&s,&raw,true,true)?;v["operation"]["query"]=json!("HIDDEN");
    let included=Product::prepare_json(&provider,&wire(&v)?,Default::default(),4)?;
    let all:Value=included.with_verified_json(&provider,5,|b|serde_json::from_slice(b))??;
    v["scope"]=json!({"kind":"paragraphs","paragraph_handles":[all["matches"]["matches"][0]["paragraph_anchor"]["opaque_handle"].clone()]});
    v["operation"]["review_policy"]["include_hidden_explanations"]=json!(false);
    let excluded=Product::prepare_json(&provider,&wire(&v)?,Default::default(),4)?;
    let json:Value=excluded.with_verified_json(&provider,5,|b|serde_json::from_slice(b))??;
    assert_eq!(json["matches"]["matches"],json!([]));assert_eq!(json["searched_paragraphs"],0);assert_eq!(json["excluded_hidden_paragraphs"],1);
    assert_ne!(included.receipt().stored.query_sha256,excluded.receipt().stored.query_sha256);
    assert!(!included.with_verified_json(&provider,5,|b|String::from_utf8(b.to_vec()))??.contains("HIDDEN"));assert!(!format!("{included:?}{:?}",included.receipt()).contains("HIDDEN"));Ok(())
}
#[test]
fn search_review_product_strict_explicit_policy_and_legacy_version_rejections_precede_source_reads()->TestResult {
    let raw=review_text_fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let good=review_text_envelope(&s,&raw,false,false)?;let mut invalid=Vec::new();
    for schema in [SOURCE_SEARCH_PRODUCT_REQUEST_SCHEMA,hwpx_agent_cli::form_product_request::stored_source_search::SOURCE_SEARCH_INSPECTION_REQUEST_SCHEMA,
        hwpx_agent_cli::form_product_request::stored_source_search::SOURCE_SEARCH_DEFINITION_REQUEST_SCHEMA] {
        let mut v=good.clone();v["schema_version"]=json!(schema);invalid.push(v);
        let mut v=envelope(&s,&raw)?;v["schema_version"]=json!(schema);v["operation"]["review_policy"]=json!(null);invalid.push(v);
    }
    for policy in [json!({}),json!(null),json!([]),json!([false,false]),json!({"include_hidden_explanations":false}),
        json!({"include_hidden_explanations":false,"include_memo_bodies":false,"native_visibility_qualified":true}),
        json!({"include_hidden_explanations":0,"include_memo_bodies":false})] {
        let mut v=good.clone();v["operation"]["review_policy"]=policy;invalid.push(v);
    }
    for (key,value) in [("style_filter",json!({"run_character_property":0})),("definition_filter",json!({"character_source":"run_property","bold":true})),("include_hidden",json!(true))] {
        let mut v=good.clone();v["operation"][key]=value;invalid.push(v);
    }
    let mut ignored=good.clone();ignored["operation"]["kind"]=json!("find_literal");invalid.push(ignored);
    let before=s.metadata.audit_events()?.len();for v in invalid {assert!(matches!(Product::prepare_json(&provider,&wire(&v)?,Default::default(),4),Err(E::Request)));}
    let duplicate=serde_json::to_string(&good)?.replace("\"include_memo_bodies\":false","\"include_memo_bodies\":false,\"include_memo_bodie\\u0073\":true");
    assert!(matches!(Product::prepare_json(&provider,duplicate.as_bytes(),Default::default(),4),Err(E::Request)));assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn search_review_product_current_write_scope_acl_quarantine_and_aead_guard_retained_body_results()->TestResult {
    for mode in 0..3 {
        let raw=review_text_fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
        let v=wire(&review_text_envelope(&s,&raw,true,true)?)?;let reader=s.provider()?;
        assert!(Product::prepare_json(&reader,&v,Default::default(),4).is_err());let result=Product::prepare_json(&provider,&v,Default::default(),4)?;
        let called=Cell::new(false);assert!(result.with_verified_json(&reader,5,|_|called.set(true)).is_err());assert!(!called.get());
        let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("foreign-review")?)?;
        assert!(result.with_verified_json(&other,5,|_|called.set(true)).is_err());assert!(!called.get());
        match mode {0=>{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;},
            1=>{s.artifacts.quarantine(&s.owner,s.result,artifact_service::QuarantineReason::parse("REVIEW_TEXT_TEST_QUARANTINE")?,5)?;},
            _=>s.blobs.tamper.store(true,Ordering::SeqCst)}
        assert!(result.with_verified_json(&provider,6,|_|called.set(true)).is_err());assert!(!called.get());assert!(result.verify(&provider,6).is_err());
    }Ok(())
}
#[test]
fn search_review_product_prepare_verify_and_final_delivery_head_races_never_expose_matches()->TestResult {
    for stage in 0..3 {
        let raw=review_text_fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
        let v=wire(&review_text_envelope(&s,&raw,true,true)?)?;let prepared=Product::prepare_json(&provider,&v,Default::default(),4)?;
        let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),
            s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,ContentDigest::of(b"review text race"),
            rev::RevisionValidationState::Verified,ContentDigest::of(b"validation fixture"),ContentDigest::of(b"transaction fixture"))?;
        let boundary=rev::RevisionService::new(BoundaryRepo {inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
        let bound=StoredFormProvider::bind(&s.artifacts,&boundary,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
        match stage {0=>{Product::prepare_json(&bound,&v,Default::default(),5)?;},1=>{prepared.verify(&bound,5)?;},_=>{prepared.with_verified_json(&bound,5,|_|())?;}}
        let calls=boundary.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);boundary.repository().calls.store(0,Ordering::SeqCst);boundary.repository().trigger.store(calls,Ordering::SeqCst);
        let called=Cell::new(false);match stage {0=>assert!(Product::prepare_json(&bound,&v,Default::default(),6).is_err()),
            1=>assert!(prepared.verify(&bound,6).is_err()),_=>assert!(prepared.with_verified_json(&bound,6,|_|called.set(true)).is_err())}
        assert!(!called.get());assert_eq!(boundary.repository().calls.load(Ordering::SeqCst),calls);
    }Ok(())
}
#[test]
fn search_review_product_malformed_or_excessive_body_corpora_fail_without_partial_success()->TestResult {
    let bad=review_text_fixture::with_body(&review_text_fixture::body().replace("</hp:hiddenComment>","<hp:subList/></hp:hiddenComment>"))?;
    let s=StoredFixture::new(&bad,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    assert!(Product::prepare_json(&provider,&wire(&review_text_envelope(&s,&bad,true,true)?)?,Default::default(),4).is_err());
    let raw=review_text_fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let v=wire(&review_text_envelope(&s,&raw,true,true)?)?;
    for config in [Config {paragraphs:1,..Default::default()},Config {scalars:18,..Default::default()},Config {result_bytes:1,..Default::default()}] {
        assert!(Product::prepare_json(&provider,&v,SourceSearchLimits::new(config)?,4).is_err());
    }Ok(())
}
