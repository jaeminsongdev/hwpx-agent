use super::*;
use hwpx_agent_cli::form_product_request::stored_literal_replacement::{StoredLiteralReplacementProductRequest as V1,
    LiteralReplacementProductError as E,LITERAL_REPLACEMENT_PRODUCT_REQUEST_SCHEMA as V1_SCHEMA,
    atoms::{StoredLiteralTextAtomProductRequest as V2,LITERAL_TEXT_ATOM_PRODUCT_REQUEST_SCHEMA as V2_SCHEMA},
    review::{StoredReviewLiteralProductRequest as Product,REVIEW_LITERAL_PRODUCT_REQUEST_SCHEMA as SCHEMA,
        REVIEW_LITERAL_PRODUCT_MAX_REQUEST_BYTES as MAXIMUM}};
use hwpx_package::{WriterLimits,document_import::search::{SourceSearchLimits,SourceSearchLimitConfig as Config}};
use serde_json::{json,Value};
use std::{cell::Cell,io::Cursor,sync::atomic::AtomicUsize};
use revision_service as rev;
#[allow(dead_code)] #[path="../../../../hwpx-package/tests/support/document_import_field_fixture.rs"] mod fixture;
macro_rules! write_provider {($s:ident,$actor:ident,$provider:ident)=>{
    let $actor=RequestContext::new($s.reader.tenant_id(),$s.reader.subject(),[AuthScope::DocumentRead,AuthScope::DocumentWrite]);
    let $provider=StoredFormProvider::bind(&$s.artifacts,&$s.revisions,&$actor,&$s.revision_context,$s.project,$s.branch,DocumentId::parse("actual-form-document")?)?;
}}
fn body()->&'static str {"<hp:p id='1'><hp:run><hp:t>BODY PRIVATE-K</hp:t><hp:ctrl><hp:hiddenComment><hp:subList><hp:p id='11'><hp:run><hp:t>HIDDEN PRIVATE-K<hp:lineBreak/></hp:t></hp:run></hp:p></hp:subList></hp:hiddenComment></hp:ctrl><hp:ctrl><hp:fieldBegin id='17' type='MEMO' editable='0'><hp:subList><hp:p id='12'><hp:run><hp:t>MEMO PRIVATE-K</hp:t></hp:run></hp:p></hp:subList></hp:fieldBegin></hp:ctrl><hp:t>CACHE FROZEN</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='17'/></hp:ctrl></hp:run></hp:p>"}
fn envelope(s:&StoredFixture,b:&[u8])->Result<Value,Box<dyn std::error::Error>> {Ok(json!({
    "schema_version":SCHEMA,"idempotency_key":"PRIVATE-REVIEW-KEY","plan_id":"review-literal-plan",
    "project_id":s.project.public_id(),"document_id":"actual-form-document","base_revision":s.head.revision_id().ok_or("head")?.public_id(),
    "expected_head_generation":s.head.generation(),"expected_source_package_sha256":ContentDigest::of(b).hex(),
    "scope":{"kind":"mapped_document","paragraph_handles":[]},
    "operation":{"kind":"replace_literal","query":"PRIVATE-K","replacement":"NEW<&","case_sensitive":true,"whole_word":false,
        "max_replacements":100,"run_policy":"first_original_run_retain_all_runs",
        "review_policy":{"include_hidden_explanations":true,"include_memo_bodies":true}}}))}
fn wire(v:&Value)->Result<Vec<u8>,serde_json::Error> {serde_json::to_vec(v)}
fn section(b:&[u8])->Result<String,Box<dyn std::error::Error>> {let mut r=hwpx_package::BoundedZipReader::open(Cursor::new(b),hwpx_package::PackageLimits::default())?;
    let i=r.entries().iter().position(|e|e.path.as_str()=="Contents/section0.xml").ok_or("section")?;Ok(String::from_utf8(r.read_entry(i)?)?)}
#[test]
fn review_product_owned_four_explicit_policies_replace_actual_regions_and_preserve_cache_controls_and_head()->TestResult {
    let raw=fixture::package(body())?;let original=section(&raw)?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for (hidden,memo,count) in [(false,false,1),(true,false,2),(false,true,2),(true,true,3)] {
        let mut v=envelope(&s,&raw)?;v["operation"]["review_policy"]=json!({"include_hidden_explanations":hidden,"include_memo_bodies":memo});
        let bytes=wire(&v)?;let out=Product::prepare_json(&provider,&bytes,Default::default(),Default::default(),4)?;drop(bytes);drop(v);
        out.verify(&provider,5)?;let text=out.with_verified_bytes(&provider,5,section)??;
        let mut expected=original.replace("BODY PRIVATE-K","BODY NEW&lt;&amp;");if hidden{expected=expected.replace("HIDDEN PRIVATE-K","HIDDEN NEW&lt;&amp;");}if memo{expected=expected.replace("MEMO PRIVATE-K","MEMO NEW&lt;&amp;");}
        assert_eq!(text,expected);let receipt=out.receipt();assert_eq!(receipt.profile,"hwpx-agent.product-literal-replacement-preparation/v3");
        assert_eq!(receipt.stored.output.output.matched_occurrences,count);assert_eq!(receipt.stored.output.body_policy.include_hidden_explanations,hidden);
        assert_eq!(receipt.stored.output.body_policy.include_memo_bodies,memo);assert!(receipt.stored.output.memo_payload_not_cached_result_verified);
        assert!(!receipt.stored.output.native_author_visibility_resolution_or_execution_qualified&&!receipt.stored.output.output.field_cached_content_edit_qualified);
        assert!(!receipt.idempotency_key_claimed&&!receipt.full_search_native_cas_execution_publication_authority);
        assert!(matches!(out.require_current_product_route(&provider,5),Err(E::RouteUnqualified)));
        assert!(!format!("{out:?}{receipt:?}").contains("PRIVATE-REVIEW-KEY"));assert!(!format!("{out:?}{receipt:?}").contains("PRIVATE-K"));
    }
    assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);
    assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(section(&raw)?,original);Ok(())
}
#[test]
fn review_product_strict_policy_envelope_duplicates_and_unsupported_values_reject_before_source_reads()->TestResult {
    let raw=fixture::package(body())?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=envelope(&s,&raw)?;
    let before=s.metadata.audit_events()?.len();let mut bad=vec!["[]".to_owned(),"null".to_owned(),format!("{} {{}}",serde_json::to_string(&good)?)];
    for key in ["schema_version","idempotency_key","plan_id","project_id","document_id","base_revision","expected_head_generation","expected_source_package_sha256","scope","operation"] {
        let mut v=good.clone();v.as_object_mut().ok_or("object")?.remove(key);bad.push(serde_json::to_string(&v)?);}
    for key in ["kind","query","replacement","case_sensitive","whole_word","max_replacements","run_policy","review_policy"] {
        let mut v=good.clone();v["operation"].as_object_mut().ok_or("operation")?.remove(key);bad.push(serde_json::to_string(&v)?);}
    for policy in [json!({}),json!(null),json!([]),json!(true),json!({"include_hidden_explanations":true}),json!({"include_memo_bodies":true}),
        json!({"include_hidden_explanations":1,"include_memo_bodies":true}),json!({"include_hidden_explanations":true,"include_memo_bodies":null}),
        json!({"include_hidden_explanations":true,"include_memo_bodies":true,"allow_cache":true})] {
        let mut v=good.clone();v["operation"]["review_policy"]=policy;bad.push(serde_json::to_string(&v)?);}
    for (key,value) in [("kind",json!("replace_regex")),("query",json!("")),("query",json!("q".repeat(4097))),
        ("replacement",json!(null)),("replacement",json!("bad\r")),("replacement",json!("bad\n")),("replacement",json!("bad\t")),("replacement",json!("\u{1fffe}")),
        ("case_sensitive",json!(1)),("max_replacements",json!(0)),("max_replacements",json!(10001)),("run_policy",json!("last_run")),
        ("include_hidden",json!(true)),("style_filter",json!({})),("allow_protected",json!(true)),("native_verified",json!(true))] {
        let mut v=good.clone();v["operation"][key]=value;bad.push(serde_json::to_string(&v)?);}
    for (key,value) in [("scope",json!([])),("operation",json!([])),("expected_head_generation",json!(0)),("expected_source_package_sha256",json!("A".repeat(64))),
        ("output_path",json!("D:/do-not-write")),("approved",json!(true)),("review_policy",json!({}))] {let mut v=good.clone();v[key]=value;bad.push(serde_json::to_string(&v)?);}
    let plain=serde_json::to_string(&good)?;
    for needle in ["\"include_memo_bodies\":true","\"include_hidden_explanations\":true"] {
        let name=if needle.contains("memo") {"include_memo_bodies"}else{"include_hidden_explanations"};
        let duplicate=plain.replace(needle,&format!("{needle},\"{name}\":false"));assert_ne!(duplicate,plain);bad.push(duplicate);
    }
    let escaped=plain.replace("\"include_memo_bodies\":true","\"include_memo_bodies\":true,\"include_memo_bodie\\u0073\":false");assert_ne!(escaped,plain);bad.push(escaped);
    for bytes in bad {assert!(matches!(Product::prepare_json(&provider,bytes.as_bytes(),Default::default(),Default::default(),4),Err(E::Request)));}
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn review_product_exact_request_limit_raw_canonical_policy_key_plan_and_value_digests_are_bound()->TestResult {
    let raw=fixture::package(body())?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=envelope(&s,&raw)?;
    let first=Product::prepare_json(&provider,&wire(&v)?,Default::default(),Default::default(),4)?;let mut padded=wire(&v)?;padded.resize(MAXIMUM,b' ');
    let at_limit=Product::prepare_json(&provider,&padded,Default::default(),Default::default(),4)?;
    assert_ne!(first.receipt().raw_request_sha256,at_limit.receipt().raw_request_sha256);assert_eq!(first.receipt().canonical_request_sha256,at_limit.receipt().canonical_request_sha256);
    padded.push(b' ');assert!(matches!(Product::prepare_json(&provider,&padded,Default::default(),Default::default(),4),Err(E::Limit)));
    assert!(matches!(Product::prepare_json(&provider,b"",Default::default(),Default::default(),4),Err(E::Limit)));
    let pretty=Product::prepare_json(&provider,&serde_json::to_vec_pretty(&v)?,Default::default(),Default::default(),4)?;
    assert_eq!(first.receipt().canonical_request_sha256,pretty.receipt().canonical_request_sha256);
    for (key,value) in [("idempotency_key",json!("OTHER-KEY")),("plan_id",json!("other-plan"))] {let mut x=v.clone();x[key]=value;
        let other=Product::prepare_json(&provider,&wire(&x)?,Default::default(),Default::default(),4)?;assert_ne!(first.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);
        assert_ne!(first.receipt().scoped_request_sha256,other.receipt().scoped_request_sha256);assert_eq!(first.receipt().stored.output.output.output_package_sha256,other.receipt().stored.output.output.output_package_sha256);}
    for (key,value) in [("replacement",json!("OTHER")),("case_sensitive",json!(false)),("whole_word",json!(true))] {let mut x=v.clone();x["operation"][key]=value;
        let other=Product::prepare_json(&provider,&wire(&x)?,Default::default(),Default::default(),4)?;assert_ne!(first.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);}
    for key in ["include_hidden_explanations","include_memo_bodies"] {let mut x=v.clone();x["operation"]["review_policy"][key]=json!(false);
        let other=Product::prepare_json(&provider,&wire(&x)?,Default::default(),Default::default(),4)?;assert_ne!(first.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);
        assert_ne!(first.receipt().scoped_request_sha256,other.receipt().scoped_request_sha256);assert_ne!(first.receipt().stored.output.review_search_request_sha256,other.receipt().stored.output.review_search_request_sha256);
        assert_ne!(first.receipt().stored.output.output.output_package_sha256,other.receipt().stored.output.output.output_package_sha256);}
    Ok(())
}
#[test]
fn review_product_authenticated_review_search_selects_hidden_and_memo_paragraphs_without_caller_import()->TestResult {
    use hwpx_agent_cli::form_product_request::stored_source_search::StoredSourceSearchProductRequest as Search;
    let raw=fixture::package(body())?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for region in ["HIDDEN","MEMO"] {let mut v=envelope(&s,&raw)?;let mut lookup=v.clone();lookup["schema_version"]=json!("hwpx-agent.product-source-search-request/v4");
        lookup["operation"]=json!({"kind":"find_review_literal","query":region,"case_sensitive":true,"whole_word":false,"max_results":100,
            "review_policy":{"include_hidden_explanations":true,"include_memo_bodies":true}});
        let found=Search::prepare_json(&provider,&wire(&lookup)?,Default::default(),4)?;let result:Value=found.with_verified_json(&provider,5,|b|serde_json::from_slice(b))??;
        let handle=result["matches"]["matches"][0]["paragraph_anchor"]["opaque_handle"].clone();assert!(handle.is_string());
        v["scope"]=json!({"kind":"paragraphs","paragraph_handles":[handle.clone()]});v["operation"]["replacement"]=json!("");
        let out=Product::prepare_json(&provider,&wire(&v)?,Default::default(),Default::default(),5)?;let text=out.with_verified_bytes(&provider,6,section)??;
        assert_eq!(out.receipt().stored.output.output.matched_occurrences,1);assert_eq!(text,section(&raw)?.replace(&format!("{region} PRIVATE-K"),&format!("{region} ")));
        v["operation"]["review_policy"][if region=="HIDDEN"{"include_hidden_explanations"}else{"include_memo_bodies"}]=json!(false);
        assert!(Product::prepare_json(&provider,&wire(&v)?,Default::default(),Default::default(),5).is_err());
        v["scope"]["paragraph_handles"]=json!([handle.clone(),handle]);assert!(matches!(Product::prepare_json(&provider,&wire(&v)?,Default::default(),Default::default(),5),Err(E::Request)));
    }Ok(())
}
#[test]
fn review_product_current_write_source_head_and_five_provider_scopes_remain_required()->TestResult {
    let raw=fixture::package(body())?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=envelope(&s,&raw)?;let reader=s.provider()?;
    let before=s.metadata.audit_events()?.len();assert!(Product::prepare_json(&reader,&wire(&v)?,Default::default(),Default::default(),4).is_err());assert_eq!(s.metadata.audit_events()?.len(),before);
    let out=Product::prepare_json(&provider,&wire(&v)?,Default::default(),Default::default(),4)?;let called=Cell::new(false);
    assert!(out.with_verified_bytes(&reader,5,|_|called.set(true)).is_err());assert!(!called.get());
    for (key,value) in [("project_id",json!("prj_70000000000000000000000000000002")),("document_id",json!("foreign-review")),("base_revision",json!(rev::RevisionId::generate().public_id())),
        ("expected_head_generation",json!(s.head.generation()+1)),("expected_source_package_sha256",json!("0".repeat(64)))] {let mut x=v.clone();x[key]=value;assert!(Product::prepare_json(&provider,&wire(&x)?,Default::default(),Default::default(),5).is_err());}
    for variant in 0..5 {let tenant=if variant==4{TenantId::new(uuid::Uuid::from_u128(702))?}else{s.reader.tenant_id()};let subject=if variant==3{s.owner.subject()}else{s.reader.subject()};
        let other_actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);let context=rev::RevisionRequestContext::new(tenant,subject);
        let project=if variant==2{rev::ProjectId::parse("prj_70000000000000000000000000000002")?}else{s.project};let branch=if variant==1{rev::BranchId::parse("brn_70000000000000000000000000000002")?}else{s.branch};
        let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&other_actor,&context,project,branch,DocumentId::parse(if variant==0{"foreign-review"}else{"actual-form-document"})?)?;
        assert!(out.verify(&other,5).is_err());assert!(out.with_verified_bytes(&other,5,|_|called.set(true)).is_err());assert!(!called.get());}
    Ok(())
}
#[test]
fn review_product_acl_quarantine_aead_and_regrant_never_turn_owned_candidates_into_access()->TestResult {
    for mode in 0..3 {let raw=fixture::package(body())?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=wire(&envelope(&s,&raw)?)?;
        let out=Product::prepare_json(&provider,&v,Default::default(),Default::default(),4)?;let called=Cell::new(false);
        match mode {0=>{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;},1=>{s.artifacts.quarantine(&s.owner,s.result,artifact_service::QuarantineReason::parse("REVIEW_PRODUCT_TEST")?,5)?;},_=>s.blobs.tamper.store(true,Ordering::SeqCst)}
        assert!(out.verify(&provider,6).is_err());assert!(out.with_verified_bytes(&provider,6,|_|called.set(true)).is_err());assert!(!called.get());assert!(Product::prepare_json(&provider,&v,Default::default(),Default::default(),6).is_err());
        if mode==0{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([artifact_service::ArtifactPermission::Read]),7)?;out.verify(&provider,8)?;}
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
fn review_product_prepare_verify_and_final_consumer_head_races_fail_before_delivery()->TestResult {
    for stage in 0..3 {let raw=fixture::package(body())?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=wire(&envelope(&s,&raw)?)?;
        let out=Product::prepare_json(&provider,&v,Default::default(),Default::default(),4)?;
        let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,
            ContentDigest::of(b"review product race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation"),ContentDigest::of(b"transaction"))?;
        let boundary=rev::RevisionService::new(BoundaryRepo {inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
        let bound=StoredFormProvider::bind(&s.artifacts,&boundary,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
        match stage {0=>{Product::prepare_json(&bound,&v,Default::default(),Default::default(),5)?;},1=>{out.verify(&bound,5)?;},_=>{out.with_verified_bytes(&bound,5,|_|())?;}}
        let calls=boundary.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);boundary.repository().calls.store(0,Ordering::SeqCst);boundary.repository().trigger.store(calls,Ordering::SeqCst);let called=Cell::new(false);
        match stage {0=>assert!(Product::prepare_json(&bound,&v,Default::default(),Default::default(),6).is_err()),1=>assert!(out.verify(&bound,6).is_err()),_=>assert!(out.with_verified_bytes(&bound,6,|_|called.set(true)).is_err())}
        assert!(!called.get());assert_eq!(boundary.repository().calls.load(Ordering::SeqCst),calls);
    }Ok(())
}
#[test]
fn review_product_policy_exclusions_precede_caps_while_cache_control_noop_and_output_bounds_stay_closed()->TestResult {
    let raw=fixture::package(body())?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=envelope(&s,&raw)?;
    let mut v=good.clone();v["operation"]["max_replacements"]=json!(1);assert!(Product::prepare_json(&provider,&wire(&v)?,Default::default(),Default::default(),4).is_err());
    v["operation"]["review_policy"]=json!({"include_hidden_explanations":false,"include_memo_bodies":false});Product::prepare_json(&provider,&wire(&v)?,Default::default(),Default::default(),4)?;
    for (key,value) in [("query",json!("CACHE FROZEN")),("query",json!("\n")),("query",json!("NOT-FOUND")),("replacement",json!("PRIVATE-K"))] {let mut v=good.clone();v["operation"][key]=value;assert!(Product::prepare_json(&provider,&wire(&v)?,Default::default(),Default::default(),4).is_err());}
    assert!(Product::prepare_json(&provider,&wire(&good)?,SourceSearchLimits::new(Config {result_bytes:1,..Default::default()})?,Default::default(),4).is_err());
    assert!(Product::prepare_json(&provider,&wire(&good)?,Default::default(),WriterLimits::new(hwpx_package::WriterLimitConfig {max_output_bytes:1})?,4).is_err());
    Ok(())
}
#[test]
fn review_product_v1_v2_v3_schemas_and_unsupported_policy_never_silently_change_existing_meanings()->TestResult {
    let raw=fixture::package(body())?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=envelope(&s,&raw)?;let before=s.metadata.audit_events()?.len();
    for schema in [V1_SCHEMA,V2_SCHEMA] {let mut v=good.clone();v["schema_version"]=json!(schema);
        assert!(matches!(Product::prepare_json(&provider,&wire(&v)?,Default::default(),Default::default(),4),Err(E::Request)));
        assert!(matches!(V1::prepare_json(&provider,&wire(&v)?,Default::default(),Default::default(),4),Err(E::Request)));
        assert!(matches!(V2::prepare_json(&provider,&wire(&v)?,Default::default(),Default::default(),4),Err(E::Request)));
        v["operation"].as_object_mut().ok_or("operation")?.remove("review_policy");assert!(matches!(Product::prepare_json(&provider,&wire(&v)?,Default::default(),Default::default(),4),Err(E::Request)));
    }
    assert!(matches!(V1::prepare_json(&provider,&wire(&good)?,Default::default(),Default::default(),4),Err(E::Request)));
    assert!(matches!(V2::prepare_json(&provider,&wire(&good)?,Default::default(),Default::default(),4),Err(E::Request)));assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn review_product_malformed_review_and_enclosing_fields_cannot_be_bypassed_by_explicit_policy()->TestResult {
    let malformed=body().replace("</hp:hiddenComment>","<hp:subList/></hp:hiddenComment>");
    let raw=fixture::package(&malformed)?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    assert!(Product::prepare_json(&provider,&wire(&envelope(&s,&raw)?)?,Default::default(),Default::default(),4).is_err());
    let inner=body().strip_prefix("<hp:p id='1'><hp:run>").and_then(|s|s.strip_suffix("</hp:run></hp:p>")).ok_or("outer fixture")?;
    let outer=format!("<hp:p id='30'><hp:run><hp:ctrl><hp:fieldBegin id='31' type='DOC_DATE' editable='1'/></hp:ctrl>{inner}<hp:ctrl><hp:fieldEnd beginIDRef='31'/></hp:ctrl></hp:run></hp:p>");
    let raw=fixture::package(&outer)?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    assert!(matches!(Product::prepare_json(&provider,&wire(&envelope(&s,&raw)?)?,Default::default(),Default::default(),4),
        Err(E::Stored(hwpx_agent_cli::form_stored_provider::actual_import::literal_search_output::StoredLiteralSearchError::Output(
            hwpx_package::document_import::search::replacement::SourceLiteralReplacementError::FieldContent)))));
    Ok(())
}
