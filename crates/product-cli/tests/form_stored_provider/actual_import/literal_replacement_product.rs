use super::*;
use hwpx_agent_cli::form_product_request::stored_literal_replacement::{StoredLiteralReplacementProductRequest as Product,
    LiteralReplacementProductError as E,LITERAL_REPLACEMENT_PRODUCT_REQUEST_SCHEMA,LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES};
use hwpx_package::{WriterLimits,document_import::search::{SourceSearchLimits,SourceSearchLimitConfig as Config,replacement::validate_literal_replacement}};
use serde_json::{json,Value};
use std::{cell::Cell,io::Cursor,sync::atomic::AtomicUsize};
use revision_service as rev;
#[allow(dead_code)] #[path="../../../../hwpx-package/tests/support/search_definition_fixture.rs"] mod fixture;
macro_rules! write_provider {($s:ident,$actor:ident,$provider:ident)=>{
    let $actor=RequestContext::new($s.reader.tenant_id(),$s.reader.subject(),[AuthScope::DocumentRead,AuthScope::DocumentWrite]);
    let $provider=StoredFormProvider::bind(&$s.artifacts,&$s.revisions,&$actor,&$s.revision_context,$s.project,$s.branch,DocumentId::parse("actual-form-document")?)?;
}}
fn bytes()->Result<Vec<u8>,Box<dyn std::error::Error>> {fixture::package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>PRIVATE-</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>QUERY</hp:t></hp:run></hp:p><hp:p id='2'><hp:run><hp:t>PRIVATE-QUERY</hp:t></hp:run></hp:p>")}
fn envelope(s:&StoredFixture,b:&[u8])->Result<Value,Box<dyn std::error::Error>> {Ok(json!({
    "schema_version":LITERAL_REPLACEMENT_PRODUCT_REQUEST_SCHEMA,"idempotency_key":"PRIVATE-LITERAL-KEY","plan_id":"literal-product-plan",
    "project_id":s.project.public_id(),"document_id":"actual-form-document","base_revision":s.head.revision_id().ok_or("head")?.public_id(),
    "expected_head_generation":s.head.generation(),"expected_source_package_sha256":ContentDigest::of(b).hex(),
    "scope":{"kind":"mapped_document","paragraph_handles":[]},
    "operation":{"kind":"replace_literal","query":"PRIVATE-QUERY","replacement":"NEW<&","case_sensitive":true,"whole_word":false,
        "max_replacements":100,"run_policy":"first_original_run_retain_all_runs"}}))}
fn wire(v:&Value)->Result<Vec<u8>,serde_json::Error> {serde_json::to_vec(v)}
fn section(b:&[u8])->Result<String,Box<dyn std::error::Error>> {let mut r=hwpx_package::BoundedZipReader::open(Cursor::new(b),hwpx_package::PackageLimits::default())?;
    let i=r.entries().iter().position(|e|e.path.as_str()=="Contents/section0.xml").ok_or("section")?;Ok(String::from_utf8(r.read_entry(i)?)?)}
#[test]
fn literal_product_owned_source_from_strict_json_replaces_cross_run_text_without_caller_import_or_commit()->TestResult {
    let raw=bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let prepared=Product::prepare_json(&provider,&wire(&envelope(&s,&raw)?)?,Default::default(),Default::default(),4)?;
    prepared.verify(&provider,5)?;let output=prepared.with_verified_bytes(&provider,5,<[u8]>::to_vec)?;
    assert!(section(&output)?.contains("<hp:t>NEW&lt;&amp;</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t></hp:t>"));
    assert_eq!(prepared.receipt().capability_id,"search.replace_literal");assert_eq!(prepared.receipt().stored.output.matched_occurrences,2);
    assert!(!prepared.receipt().idempotency_key_claimed&&!prepared.receipt().full_search_native_cas_execution_publication_authority);
    assert!(matches!(prepared.require_current_product_route(&provider,5),Err(E::RouteUnqualified)));
    assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);
    assert!(section(&raw)?.contains("PRIVATE-"));assert!(!format!("{prepared:?}{:?}",prepared.receipt()).contains("PRIVATE-LITERAL-KEY"));Ok(())
}
#[test]
fn literal_product_strict_missing_unknown_duplicate_and_typed_values_reject_before_artifact_reads()->TestResult {
    let raw=bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=envelope(&s,&raw)?;let before=s.metadata.audit_events()?.len();
    let mut bad=vec!["null".to_owned(),"[]".to_owned(),format!("{} {{}}",serde_json::to_string(&v)?)];
    for key in ["schema_version","idempotency_key","plan_id","project_id","document_id","base_revision","expected_head_generation","expected_source_package_sha256","scope","operation"] {
        let mut x=v.clone();x.as_object_mut().ok_or("object")?.remove(key);bad.push(serde_json::to_string(&x)?);}
    for key in ["kind","query","replacement","case_sensitive","whole_word","max_replacements","run_policy"] {
        let mut x=v.clone();x["operation"].as_object_mut().ok_or("operation")?.remove(key);bad.push(serde_json::to_string(&x)?);}
    for (key,value) in [("schema_version",json!("hwpx-agent.product-source-search-request/v4")),("scope",json!(["mapped_document"])),("operation",json!([])),
        ("output_path",json!("D:/do-not-write")),("approved",json!(true)),("expected_head_generation",json!(0)),("expected_source_package_sha256",json!("A".repeat(64))),
        ("document_id",json!("d".repeat(1025)))] {let mut x=v.clone();x[key]=value;bad.push(serde_json::to_string(&x)?);}
    for (key,value) in [("kind",json!("replace_regex")),("query",json!("")),("query",json!("q".repeat(4097))),
        ("replacement",json!(null)),("replacement",json!("bad\r")),("replacement",json!("bad\n")),("replacement",json!("bad\t")),("replacement",json!("\u{1fffe}")),
        ("case_sensitive",json!(1)),("max_replacements",json!(0)),("max_replacements",json!(10001)),("run_policy",json!("use_last_run")),
        ("regex",json!(false)),("style_filter",json!({})),("include_hidden",json!(true)),("preview_only",json!(true)),("native_verified",json!(true))] {
        let mut x=v.clone();x["operation"][key]=value;bad.push(serde_json::to_string(&x)?);}
    for scope in [json!({"kind":"paragraphs","paragraph_handles":[]}),json!({"kind":"mapped_document","paragraph_handles":["foreign"]}),
        json!({"kind":"paragraphs","paragraph_handles":["same","same"]}),json!({"kind":"mapped_document","paragraph_handles":[],"allow_protected":true})] {
        let mut x=v.clone();x["scope"]=scope;bad.push(serde_json::to_string(&x)?);}
    bad.push(serde_json::to_string(&v)?.replace("\"replacement\":\"NEW<&\"","\"replacement\":\"NEW<&\",\"replacemen\\u0074\":\"OTHER\""));
    for raw in bad {assert!(matches!(Product::prepare_json(&provider,raw.as_bytes(),Default::default(),Default::default(),4),Err(E::Request)));}
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn literal_product_exact_envelope_limit_and_shared_pure_value_policy_are_enforced()->TestResult {
    let raw=bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut good=wire(&envelope(&s,&raw)?)?;
    good.resize(LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES,b' ');Product::prepare_json(&provider,&good,Default::default(),Default::default(),4)?;
    good.push(b' ');assert!(matches!(Product::prepare_json(&provider,&good,Default::default(),Default::default(),4),Err(E::Limit)));
    assert!(matches!(Product::prepare_json(&provider,b"",Default::default(),Default::default(),4),Err(E::Limit)));
    validate_literal_replacement("")?;validate_literal_replacement("한글<&")?;
    assert!(validate_literal_replacement(&"x".repeat(1024*1024+1)).is_err());for value in ["\r","\n","\t","\u{1fffe}"] {assert!(validate_literal_replacement(value).is_err());}Ok(())
}
#[test]
fn literal_product_raw_canonical_key_plan_query_replacement_and_scope_bindings_never_claim_idempotency()->TestResult {
    let raw=bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=envelope(&s,&raw)?;
    let first=Product::prepare_json(&provider,&wire(&v)?,Default::default(),Default::default(),4)?;
    let pretty=Product::prepare_json(&provider,&serde_json::to_vec_pretty(&v)?,Default::default(),Default::default(),4)?;
    assert_ne!(first.receipt().raw_request_sha256,pretty.receipt().raw_request_sha256);assert_eq!(first.receipt().canonical_request_sha256,pretty.receipt().canonical_request_sha256);
    for (key,value) in [("idempotency_key",json!("OTHER-KEY")),("plan_id",json!("other-plan"))] {let mut x=v.clone();x[key]=value;
        let other=Product::prepare_json(&provider,&wire(&x)?,Default::default(),Default::default(),4)?;assert_ne!(first.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);
        assert_ne!(first.receipt().scoped_request_sha256,other.receipt().scoped_request_sha256);assert_eq!(first.receipt().stored.output.output_package_sha256,other.receipt().stored.output.output_package_sha256);}
    let mut changed=v.clone();changed["operation"]["replacement"]=json!("DIFFERENT");let other=Product::prepare_json(&provider,&wire(&changed)?,Default::default(),Default::default(),4)?;
    assert_ne!(first.receipt().stored.output.replacement_sha256,other.receipt().stored.output.replacement_sha256);assert_ne!(first.receipt().stored.output.output_package_sha256,other.receipt().stored.output.output_package_sha256);
    let mut changed=v.clone();changed["operation"]["case_sensitive"]=json!(false);let other=Product::prepare_json(&provider,&wire(&changed)?,Default::default(),Default::default(),4)?;
    assert_ne!(first.receipt().stored.output.query_sha256,other.receipt().stored.output.query_sha256);assert!(!other.receipt().idempotency_key_claimed);Ok(())
}
#[test]
fn literal_product_uses_authenticated_search_handles_for_selected_scope_and_empty_replacement()->TestResult {
    use hwpx_agent_cli::form_product_request::stored_source_search::StoredSourceSearchProductRequest as Search;
    let raw=bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=envelope(&s,&raw)?;let mut lookup=v.clone();
    lookup["schema_version"]=json!("hwpx-agent.product-source-search-request/v1");lookup["operation"]=json!({"kind":"find_literal","query":"PRIVATE-QUERY","case_sensitive":true,"whole_word":false,"max_results":100});
    let found=Search::prepare_json(&provider,&wire(&lookup)?,Default::default(),4)?;let json:Value=found.with_verified_json(&provider,5,|b|serde_json::from_slice(b))??;
    v["scope"]=json!({"kind":"paragraphs","paragraph_handles":[json["result"]["matches"][0]["paragraph_anchor"]["opaque_handle"].clone()]});v["operation"]["replacement"]=json!("");
    let prepared=Product::prepare_json(&provider,&wire(&v)?,Default::default(),Default::default(),5)?;
    let text=prepared.with_verified_bytes(&provider,6,section)??;assert_eq!(prepared.receipt().stored.output.matched_occurrences,1);
    assert!(text.contains("<hp:run charPrIDRef='0'><hp:t></hp:t></hp:run><hp:run charPrIDRef='1'><hp:t></hp:t>"));assert!(text.contains("<hp:t>PRIVATE-QUERY</hp:t>"));Ok(())
}
#[test]
fn literal_product_write_scope_foreign_head_source_and_all_provider_scopes_are_rechecked()->TestResult {
    let raw=bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=envelope(&s,&raw)?;let reader=s.provider()?;let before=s.metadata.audit_events()?.len();
    assert!(Product::prepare_json(&reader,&wire(&v)?,Default::default(),Default::default(),4).is_err());assert_eq!(s.metadata.audit_events()?.len(),before);
    let prepared=Product::prepare_json(&provider,&wire(&v)?,Default::default(),Default::default(),4)?;
    for (key,value) in [("project_id",json!("prj_70000000000000000000000000000002")),("document_id",json!("other-document")),("base_revision",json!(rev::RevisionId::generate().public_id())),
        ("expected_head_generation",json!(s.head.generation()+1)),("expected_source_package_sha256",json!("0".repeat(64)))] {let mut x=v.clone();x[key]=value;assert!(Product::prepare_json(&provider,&wire(&x)?,Default::default(),Default::default(),5).is_err());}
    let called=Cell::new(false);assert!(prepared.with_verified_bytes(&reader,5,|_|called.set(true)).is_err());assert!(!called.get());
    for variant in 0..5 {let tenant=if variant==4 {TenantId::new(uuid::Uuid::from_u128(702))?}else{s.reader.tenant_id()};let subject=if variant==3 {s.owner.subject()}else{s.reader.subject()};
        let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);let context=rev::RevisionRequestContext::new(tenant,subject);
        let project=if variant==2 {rev::ProjectId::parse("prj_70000000000000000000000000000002")?}else{s.project};let branch=if variant==1 {rev::BranchId::parse("brn_70000000000000000000000000000002")?}else{s.branch};
        let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&context,project,branch,DocumentId::parse(if variant==0 {"foreign-literal"}else{"actual-form-document"})?)?;
        assert!(prepared.with_verified_bytes(&other,5,|_|called.set(true)).is_err());assert!(!called.get());assert!(prepared.verify(&other,5).is_err());}Ok(())
}
#[test]
fn literal_product_acl_quarantine_aead_and_regrant_never_turn_owned_candidate_into_access()->TestResult {
    for mode in 0..3 {let raw=bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=wire(&envelope(&s,&raw)?)?;
        let prepared=Product::prepare_json(&provider,&v,Default::default(),Default::default(),4)?;let called=Cell::new(false);
        match mode {0=>{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;},1=>{s.artifacts.quarantine(&s.owner,s.result,artifact_service::QuarantineReason::parse("LITERAL_PRODUCT_TEST")?,5)?;},_=>s.blobs.tamper.store(true,Ordering::SeqCst)}
        assert!(prepared.with_verified_bytes(&provider,6,|_|called.set(true)).is_err());assert!(!called.get());assert!(prepared.verify(&provider,6).is_err());assert!(Product::prepare_json(&provider,&v,Default::default(),Default::default(),6).is_err());
        if mode==0 {s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([artifact_service::ArtifactPermission::Read]),7)?;prepared.verify(&provider,8)?;}
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
fn literal_product_prepare_verify_and_final_consumer_head_races_never_deliver_stale_bytes()->TestResult {
    for stage in 0..3 {let raw=bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=wire(&envelope(&s,&raw)?)?;
        let prepared=Product::prepare_json(&provider,&v,Default::default(),Default::default(),4)?;
        let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,
            ContentDigest::of(b"literal product race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation"),ContentDigest::of(b"transaction"))?;
        let boundary=rev::RevisionService::new(BoundaryRepo {inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
        let bound=StoredFormProvider::bind(&s.artifacts,&boundary,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
        match stage {0=>{Product::prepare_json(&bound,&v,Default::default(),Default::default(),5)?;},1=>{prepared.verify(&bound,5)?;},_=>{prepared.with_verified_bytes(&bound,5,|_|())?;}}
        let calls=boundary.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);boundary.repository().calls.store(0,Ordering::SeqCst);boundary.repository().trigger.store(calls,Ordering::SeqCst);let called=Cell::new(false);
        match stage {0=>assert!(Product::prepare_json(&bound,&v,Default::default(),Default::default(),6).is_err()),1=>assert!(prepared.verify(&bound,6).is_err()),_=>assert!(prepared.with_verified_bytes(&bound,6,|_|called.set(true)).is_err())}
        assert!(!called.get());assert_eq!(boundary.repository().calls.load(Ordering::SeqCst),calls);
    }Ok(())
}
#[test]
fn literal_product_runtime_match_limits_noop_fields_and_writer_failures_do_not_become_prepared_success()->TestResult {
    let raw=bytes()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=envelope(&s,&raw)?;
    for (key,value) in [("max_replacements",json!(1)),("query",json!("NO-MATCH"))] {let mut v=good.clone();v["operation"][key]=value;assert!(Product::prepare_json(&provider,&wire(&v)?,Default::default(),Default::default(),4).is_err());}
    assert!(Product::prepare_json(&provider,&wire(&good)?,SourceSearchLimits::new(Config {result_bytes:1,..Default::default()})?,Default::default(),4).is_err());
    assert!(Product::prepare_json(&provider,&wire(&good)?,Default::default(),WriterLimits::new(hwpx_package::WriterLimitConfig {max_output_bytes:1})?,4).is_err());
    let field=fixture::package("<hp:p id='1'><hp:run><hp:ctrl><hp:fieldBegin id='17' type='MEMO' editable='1'/></hp:ctrl><hp:t>PRIVATE-QUERY</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='17'/></hp:ctrl></hp:run></hp:p>")?;
    let s=StoredFixture::new(&field,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);assert!(Product::prepare_json(&provider,&wire(&envelope(&s,&field)?)?,Default::default(),Default::default(),4).is_err());
    let raw=fixture::package("<hp:p id='1'><hp:run><hp:t>PRIVATE-QUERY</hp:t></hp:run></hp:p>")?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let mut v=envelope(&s,&raw)?;v["operation"]["replacement"]=json!("PRIVATE-QUERY");assert!(Product::prepare_json(&provider,&wire(&v)?,Default::default(),Default::default(),4).is_err());Ok(())
}
