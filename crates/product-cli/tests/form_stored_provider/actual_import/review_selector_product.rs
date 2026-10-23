use super::*;
use hwpx_agent_cli::form_product_request::{stored_source_search::{SourceSearchProductError as SE,
    selector::{StoredSourceScopeProductRequest as V5,review::{StoredReviewScopeProductRequest as S,REVIEW_SCOPE_PRODUCT_REQUEST_SCHEMA as SS}}},
    stored_literal_replacement::{LiteralReplacementProductError as LE,selector::{StoredSelectorLiteralProductRequest as L,SELECTOR_LITERAL_PRODUCT_REQUEST_SCHEMA as LS}}};
use hwpx_package::{WriterLimits,WriterLimitConfig,document_import::search::{SourceSearchLimits,SourceSearchLimitConfig as Config}};
use serde_json::{json,Value};
use std::{cell::Cell,io::Cursor,sync::atomic::AtomicUsize};
use revision_service as rev;
#[path="../../../../hwpx-package/tests/support/review_scope_fixture.rs"] mod fixture;
macro_rules! write_provider {($s:ident,$actor:ident,$p:ident)=>{
    let $actor=RequestContext::new($s.reader.tenant_id(),$s.reader.subject(),[AuthScope::DocumentRead,AuthScope::DocumentWrite]);
    let $p=StoredFormProvider::bind(&$s.artifacts,&$s.revisions,&$actor,&$s.revision_context,$s.project,$s.branch,DocumentId::parse("actual-form-document")?)?;
}}
macro_rules! search {($p:expr,$v:expr)=>{S::prepare_json($p,&wire($v)?,Default::default(),4)}}
macro_rules! literal {($p:expr,$v:expr)=>{L::prepare_json($p,&wire($v)?,Default::default(),Default::default(),4)}}
macro_rules! response {($p:expr,$v:expr)=>{{let out=search!($p,$v)?;let value:Value=out.with_verified_json($p,5,|b|serde_json::from_slice(b))??;value}}}
fn envelope(s:&StoredFixture,raw:&[u8])->Result<Value,Box<dyn Error>> {let rev=s.head.revision_id().ok_or("head")?.public_id();Ok(json!({
    "schema_version":SS,"idempotency_key":"PRIVATE-SELECTOR-KEY","plan_id":"selector-product-plan","project_id":s.project.public_id(),"document_id":"actual-form-document",
    "base_revision":rev,"expected_head_generation":s.head.generation(),"expected_source_package_sha256":ContentDigest::of(raw).hex(),
    "selector":{"revision_id":rev,"scope":"document"},"operation":{"kind":"scope_inventory"}}))}
fn policy(hidden:bool,memo:bool)->Value {json!({"include_hidden_explanations":hidden,"include_memo_bodies":memo})}
fn find(base:&Value)->Value {let mut v=base.clone();v["operation"]=json!({"kind":"find_literal","query":"K","case_sensitive":true,"whole_word":false,"max_results":100,"review_policy":policy(true,true)});v}
fn replace(base:&Value)->Value {let mut v=base.clone();v["schema_version"]=json!(LS);v["operation"]=json!({"kind":"replace_literal","query":"K","replacement":"NEW<&",
    "case_sensitive":true,"whole_word":false,"max_replacements":100,"run_policy":"first_original_run_retain_all_runs","review_policy":policy(true,true)});v}
fn wire(v:&Value)->Result<Vec<u8>,serde_json::Error> {serde_json::to_vec(v)}
fn section(raw:&[u8])->Result<String,Box<dyn Error>> {let mut zip=hwpx_package::BoundedZipReader::open(Cursor::new(raw),Default::default())?;
    let n=zip.entries().iter().position(|e|e.path.as_str()=="Contents/section0.xml").ok_or("section")?;Ok(String::from_utf8(zip.read_entry(n)?)?)}
fn window(inv:&Value,region:&str,scalar:usize)->Result<Value,Box<dyn Error>> {
    let n=inv["block_regions"].as_array().ok_or("regions")?.iter().position(|v|v==region).ok_or("region")?;let b=&inv["inventory"]["blocks"][n];
    let hash:[u8;32]=serde_json::from_value(inv["inventory"]["index"]["index_sha256"].clone())?;
    Ok(json!({"coordinate_space":"index_nfc_unicode_scalars","index_sha256":hex::encode(hash),
        "start":{"paragraph_handle":b["paragraph_handle"],"block_index":b["block_index"],"normalized_scalar":scalar},
        "end":{"paragraph_handle":b["paragraph_handle"],"block_index":b["block_index"],"normalized_scalar":scalar+1}}))
}
fn node(inv:&Value,handle:&Value)->Result<Value,Box<dyn Error>> {Ok(inv["inventory"]["nodes"].as_array().ok_or("nodes")?.iter().find(|n|&n["source_handle"]==handle).ok_or("node")?["node_id"].clone())}
#[test]
fn review_selector_product_discovery_builds_four_search_and_literal_scopes_without_caller_import()->TestResult {
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let base=envelope(&s,&raw)?;let inv=response!(&p,&base);
    assert!(!serde_json::to_string(&inv)?.contains("PRIVATE-AUTHOR"));let selected=window(&inv,"memo_body",7)?;
    for(scope,sections,range,count)in[("document",None,None,6),("section",Some(inv["inventory"]["section_ids"].clone()),None,6),
        ("node_set",None,Some(json!({"node_ids":[node(&inv,&selected["start"]["paragraph_handle"])?]})),2),("selection",None,Some(selected),1)] {
        let mut v=find(&base);v["selector"]["scope"]=json!(scope);if let Some(ids)=sections{v["selector"]["section_ids"]=ids;}if let Some(r)=range{v["selector"]["range"]=r;}
        assert_eq!(response!(&p,&v)["result"]["matches"].as_array().ok_or("matches")?.len(),count);
        let mut r=replace(&base);r["selector"]=v["selector"].clone();let out=literal!(&p,&r)?;out.verify(&p,5)?;
        assert_eq!(out.receipt().stored.output.body_candidate.output.matched_occurrences,count);out.with_verified_bytes(&p,5,|_|())?;}
    assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
}
#[test]
fn review_selector_product_partial_window_clips_regex_before_caps_and_replaces_only_second_match()->TestResult {
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let base=envelope(&s,&raw)?;let inv=response!(&p,&base);
    for(region,scalar,old,new)in[("body_and_notes",7,"BODY K K","BODY K NEW&lt;&amp;"),("hidden_explanation",9,"HIDDEN K K","HIDDEN K NEW&lt;&amp;"),("memo_body",7,"MEMO K K","MEMO K NEW&lt;&amp;")] {
        let mut v=find(&base);v["selector"]["scope"]=json!("selection");v["selector"]["range"]=window(&inv,region,scalar)?;
        v["operation"]["kind"]=json!("find_regex");v["operation"]["query"]=json!("^K$");v["operation"]["max_results"]=json!(1);let value=response!(&p,&v);
        let matches=value["result"]["matches"].as_array().ok_or("matches")?;assert_eq!(matches.len(),1);assert_eq!(matches[0]["start_normalized_scalar"],scalar);
        let mut r=replace(&base);r["selector"]=v["selector"].clone();r["operation"]["max_replacements"]=json!(1);let out={let bytes=wire(&r)?;L::prepare_json(&p,&bytes,Default::default(),Default::default(),4)?};
        drop(r);assert_eq!(out.with_verified_bytes(&p,5,section)??,section(&raw)?.replace(old,new));}
    Ok(())
}
#[test]
fn review_selector_product_four_policies_bind_search_and_literal_excluding_before_caps()->TestResult {
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let base=envelope(&s,&raw)?;let mut hashes=BTreeSet::new();
    for(hidden,memo,count)in[(false,false,2),(true,false,4),(false,true,4),(true,true,6)] {let mut v=find(&base);v["operation"]["review_policy"]=policy(hidden,memo);v["operation"]["max_results"]=json!(count);
        let search=search!(&p,&v)?;hashes.insert(search.receipt().canonical_request_sha256.clone());let value:Value=search.with_verified_json(&p,5,|b|serde_json::from_slice(b))??;
        assert_eq!(value["result"]["matches"].as_array().ok_or("matches")?.len(),count);let mut r=replace(&base);r["operation"]["review_policy"]=policy(hidden,memo);r["operation"]["max_replacements"]=json!(count);
        let out=literal!(&p,&r)?;assert_eq!(out.receipt().stored.output.body_candidate.output.matched_occurrences,count);
        let mut expected=section(&raw)?.replace("BODY K K","BODY NEW&lt;&amp; NEW&lt;&amp;");if hidden{expected=expected.replace("HIDDEN K K","HIDDEN NEW&lt;&amp; NEW&lt;&amp;");}if memo{expected=expected.replace("MEMO K K","MEMO NEW&lt;&amp; NEW&lt;&amp;");}
        assert_eq!(out.with_verified_bytes(&p,5,section)??,expected);}
    assert_eq!(hashes.len(),4);Ok(())
}
#[test]
fn review_selector_product_excluded_real_node_is_valid_empty_search_and_no_literal_matches()->TestResult {
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let base=envelope(&s,&raw)?;let inv=response!(&p,&base);let range=window(&inv,"memo_body",7)?;
    let mut v=find(&base);v["selector"]["scope"]=json!("node_set");v["selector"]["range"]=json!({"node_ids":[node(&inv,&range["start"]["paragraph_handle"])?]});v["operation"]["review_policy"]=policy(false,false);
    let value=response!(&p,&v);assert_eq!(value["searched_blocks"],0);assert_eq!(value["excluded_memo_paragraphs"],1);assert!(value["result"]["matches"].as_array().ok_or("matches")?.is_empty());
    let mut r=replace(&base);r["selector"]=v["selector"].clone();r["operation"]["review_policy"]=policy(false,false);assert!(literal!(&p,&r).is_err());Ok(())
}
#[test]
fn review_selector_product_strict_envelopes_selector_shapes_and_revision_reject_before_reads()->TestResult {
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let base=envelope(&s,&raw)?;
    for literal in[false,true]{let good=if literal{replace(&base)}else{find(&base)};let before=s.metadata.audit_events()?.len();let mut bad=vec!["null".to_owned(),"[]".to_owned(),format!("{} {{}}",serde_json::to_string(&good)?)];
        for key in["schema_version","idempotency_key","plan_id","project_id","document_id","base_revision","expected_head_generation","expected_source_package_sha256","selector","operation"] {let mut v=good.clone();v.as_object_mut().ok_or("object")?.remove(key);bad.push(serde_json::to_string(&v)?);}
        for sel in[json!([]),json!({"scope":"document"}),json!({"revision_id":good["base_revision"],"scope":"document","section_ids":[]}),json!({"revision_id":good["base_revision"],"scope":"document","range":null}),
            json!({"revision_id":good["base_revision"],"scope":"section","section_ids":[]}),json!({"revision_id":good["base_revision"],"scope":"node_set","range":{"node_ids":[]}}),
            json!({"revision_id":rev::RevisionId::generate().public_id(),"scope":"document"}),json!({"revision_id":good["base_revision"],"scope":"document","approved":true})]{let mut v=good.clone();v["selector"]=sel;bad.push(serde_json::to_string(&v)?);}
        for(key,value)in[("scope",json!({"kind":"mapped_document","paragraph_handles":[]})),("operation",json!([])),("approved",json!(true)),("output_path",json!("D:/do-not-write")),("expected_head_generation",json!(0)),("expected_source_package_sha256",json!("A".repeat(64))) ]{let mut v=good.clone();v[key]=value;bad.push(serde_json::to_string(&v)?);}
        for raw in bad{if literal{assert!(matches!(L::prepare_json(&p,raw.as_bytes(),Default::default(),Default::default(),4),Err(LE::Request)));}else{assert!(matches!(S::prepare_json(&p,raw.as_bytes(),Default::default(),4),Err(SE::Request)));}}
        assert_eq!(s.metadata.audit_events()?.len(),before);}
    Ok(())
}
#[test]
fn review_selector_product_strict_required_policy_duplicates_and_inapplicable_inventory_options_reject_before_reads()->TestResult {
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let base=envelope(&s,&raw)?;
    for literal in[false,true]{let good=if literal{replace(&base)}else{find(&base)};let before=s.metadata.audit_events()?.len();let mut bad=Vec::new();
        let mut missing=good.clone();missing["operation"].as_object_mut().ok_or("operation")?.remove("review_policy");bad.push(serde_json::to_string(&missing)?);
        for policy in[json!(null),json!([]),json!(true),json!({}),json!({"include_hidden_explanations":true}),json!({"include_hidden_explanations":true,"include_memo_bodies":1}),json!({"include_hidden_explanations":true,"include_memo_bodies":true,"allow_cache":true})]{let mut v=good.clone();v["operation"]["review_policy"]=policy;bad.push(serde_json::to_string(&v)?);}
        for(key,value)in[("query",json!("")),("query",json!("q".repeat(4097))),("native_verified",json!(true)),("include_hidden",json!(true)),("style_filter",json!({})),("case_sensitive",json!(1))]{let mut v=good.clone();v["operation"][key]=value;bad.push(serde_json::to_string(&v)?);}
        for(key,value)in if literal{vec![("kind",json!("replace_regex")),("replacement",json!("\n")),("max_replacements",json!(0)),("max_replacements",json!(10001)),("run_policy",json!("last_run"))]}else{vec![("max_results",json!(0)),("max_results",json!(10001)),("kind",json!("replace_literal"))]}{let mut v=good.clone();v["operation"][key]=value;bad.push(serde_json::to_string(&v)?);}
        let text=serde_json::to_string(&good)?;for(from,to)in[("\"scope\":\"document\"","\"scope\":\"document\",\"sco\\u0070e\":\"section\""),("\"include_memo_bodies\":true","\"include_memo_bodies\":true,\"include_memo_bo\\u0064ies\":false")]{let dup=text.replace(from,to);assert_ne!(dup,text);bad.push(dup);}
        for raw in bad{if literal{assert!(matches!(L::prepare_json(&p,raw.as_bytes(),Default::default(),Default::default(),4),Err(LE::Request)));}else{assert!(matches!(S::prepare_json(&p,raw.as_bytes(),Default::default(),4),Err(SE::Request)));}}
        assert_eq!(s.metadata.audit_events()?.len(),before);}
    let before=s.metadata.audit_events()?.len();for key in["review_policy","query","max_results"]{let mut v=base.clone();v["operation"][key]=if key=="review_policy"{policy(true,true)}else{json!(1)};assert!(matches!(search!(&p,&v),Err(SE::Request)));}
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn review_selector_product_exact_16k_raw_canonical_key_plan_policy_and_operation_bindings()->TestResult {
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let base=envelope(&s,&raw)?;
    let v=find(&base);let r=replace(&base);let a=search!(&p,&v)?;let l=literal!(&p,&r)?;let mut search_raw=wire(&v)?;search_raw.resize(16*1024,b' ');let padded=S::prepare_json(&p,&search_raw,Default::default(),4)?;
    assert_ne!(a.receipt().raw_request_sha256,padded.receipt().raw_request_sha256);assert_eq!(a.receipt().canonical_request_sha256,padded.receipt().canonical_request_sha256);
    let mut literal_raw=wire(&r)?;literal_raw.resize(16*1024,b' ');let padded=L::prepare_json(&p,&literal_raw,Default::default(),Default::default(),4)?;
    assert_ne!(l.receipt().raw_request_sha256,padded.receipt().raw_request_sha256);assert_eq!(l.receipt().canonical_request_sha256,padded.receipt().canonical_request_sha256);
    search_raw.push(b' ');literal_raw.push(b' ');assert!(matches!(S::prepare_json(&p,&search_raw,Default::default(),4),Err(SE::Limit)));assert!(matches!(L::prepare_json(&p,&literal_raw,Default::default(),Default::default(),4),Err(LE::Limit)));
    assert!(matches!(S::prepare_json(&p,b"",Default::default(),4),Err(SE::Limit)));assert!(matches!(L::prepare_json(&p,b"",Default::default(),Default::default(),4),Err(LE::Limit)));
    for(key,value)in[("idempotency_key",json!("OTHER-KEY")),("plan_id",json!("other-plan"))]{let mut v2=v.clone();v2[key]=value.clone();let b=search!(&p,&v2)?;
        assert_ne!(a.receipt().canonical_request_sha256,b.receipt().canonical_request_sha256);assert_ne!(a.receipt().scoped_request_sha256,b.receipt().scoped_request_sha256);assert_eq!(a.receipt().stored.result_sha256,b.receipt().stored.result_sha256);
        let mut r2=r.clone();r2[key]=value;let b=literal!(&p,&r2)?;assert_ne!(l.receipt().canonical_request_sha256,b.receipt().canonical_request_sha256);assert_ne!(l.receipt().scoped_request_sha256,b.receipt().scoped_request_sha256);assert_eq!(l.receipt().stored.output.body_candidate.output.output_package_sha256,b.receipt().stored.output.body_candidate.output.output_package_sha256);}
    let mut v2=v;v2["operation"]["query"]=json!("BODY");assert_ne!(a.receipt().canonical_request_sha256,search!(&p,&v2)?.receipt().canonical_request_sha256);
    let mut r2=r;r2["operation"]["replacement"]=json!("OTHER");assert_ne!(l.receipt().canonical_request_sha256,literal!(&p,&r2)?.receipt().canonical_request_sha256);
    assert_eq!(a.receipt().profile,"hwpx-agent.product-source-search-preparation/v6");assert_eq!(l.receipt().profile,"hwpx-agent.product-literal-replacement-preparation/v4");
    assert!(!a.receipt().idempotency_key_claimed&&!l.receipt().idempotency_key_claimed);assert!(matches!(a.require_current_product_route(&p,5),Err(SE::RouteUnqualified)));assert!(matches!(l.require_current_product_route(&p,5),Err(LE::RouteUnqualified)));
    assert!(!format!("{a:?}{l:?}{:?}{:?}",a.receipt(),l.receipt()).contains("PRIVATE-SELECTOR-KEY"));Ok(())
}
#[test]
fn review_selector_product_write_and_five_foreign_provider_scopes_reject_retained_metadata_and_output()->TestResult {
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let base=envelope(&s,&raw)?;let v=find(&base);let r=replace(&base);let reader=s.provider()?;
    assert!(search!(&reader,&v).is_err());assert!(literal!(&reader,&r).is_err());let a=search!(&p,&v)?;let l=literal!(&p,&r)?;let called=Cell::new(false);
    assert!(a.with_verified_json(&reader,5,|_|called.set(true)).is_err());assert!(l.with_verified_bytes(&reader,5,|_|called.set(true)).is_err());
    for variant in 0..5{let tenant=if variant==4{TenantId::new(Uuid::from_u128(993))?}else{s.reader.tenant_id()};let subject=if variant==3{SubjectDigest::from_authenticated_subject("foreign-selector-product")?}else{s.reader.subject()};
        let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);let context=rev::RevisionRequestContext::new(tenant,subject);
        let project=if variant==2{rev::ProjectId::parse("prj_70000000000000000000000000000002")?}else{s.project};let branch=if variant==1{rev::BranchId::parse("brn_70000000000000000000000000000002")?}else{s.branch};
        let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&context,project,branch,DocumentId::parse(if variant==0{"foreign-document"}else{"actual-form-document"})?)?;
        assert!(a.verify(&other,5).is_err());assert!(a.with_verified_json(&other,5,|_|called.set(true)).is_err());assert!(l.verify(&other,5).is_err());assert!(l.with_verified_bytes(&other,5,|_|called.set(true)).is_err());}
    assert!(!called.get());Ok(())
}
#[test]
fn review_selector_product_expected_source_head_project_and_document_bind_current_result()->TestResult {
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let base=envelope(&s,&raw)?;
    for(key,value)in[("expected_head_generation",json!(s.head.generation()+1)),("expected_source_package_sha256",json!("0".repeat(64))),("project_id",json!("prj_70000000000000000000000000000002")),("document_id",json!("foreign-document"))]{
        let mut v=find(&base);v[key]=value.clone();assert!(search!(&p,&v).is_err());let mut r=replace(&base);r[key]=value;assert!(literal!(&p,&r).is_err());}Ok(())
}
#[test]
fn review_selector_product_acl_quarantine_and_aead_recheck_all_retained_variants_and_regrant()->TestResult {
    for mode in 0..3{let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let base=envelope(&s,&raw)?;
        let discovery=search!(&p,&base)?;let found=search!(&p,&find(&base))?;let out=literal!(&p,&replace(&base))?;
        match mode{0=>{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;},1=>{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("SELECTOR_PRODUCT_TEST")?,5)?;},_=>s.blobs.tamper.store(true,Ordering::SeqCst)}
        let called=Cell::new(false);for a in[&discovery,&found]{assert!(a.verify(&p,6).is_err());assert!(a.with_verified_json(&p,6,|_|called.set(true)).is_err());}assert!(out.verify(&p,6).is_err());assert!(out.with_verified_bytes(&p,6,|_|called.set(true)).is_err());
        assert!(search!(&p,&find(&base)).is_err());assert!(literal!(&p,&replace(&base)).is_err());assert!(!called.get());if mode==0{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;discovery.verify(&p,8)?;found.verify(&p,8)?;out.verify(&p,8)?;}}
    Ok(())
}
struct BoundaryRepo{inner:rev::InMemoryRevisionRepository,calls:AtomicUsize,trigger:AtomicUsize,context:rev::RevisionRequestContext,advance:rev::RevisionCommitRequest}
impl rev::RevisionRepository for BoundaryRepo{
    fn compare_and_swap(&self,c:&rev::RevisionRequestContext,r:&rev::RevisionCommitRequest)->Result<rev::CommitOutcome,rev::RevisionError>{self.inner.compare_and_swap(c,r)}
    fn head(&self,t:TenantId,p:rev::ProjectId,b:rev::BranchId)->Result<rev::RevisionHead,rev::RevisionError>{let n=self.calls.fetch_add(1,Ordering::SeqCst)+1;if n==self.trigger.load(Ordering::SeqCst){assert!(matches!(self.inner.compare_and_swap(&self.context,&self.advance)?,rev::CommitOutcome::Committed(_)));}self.inner.head(t,p,b)}
    fn node(&self,t:TenantId,p:rev::ProjectId,r:rev::RevisionId)->Result<rev::RevisionNode,rev::RevisionError>{self.inner.node(t,p,r)}
}
#[test]
fn review_selector_product_discovery_search_literal_prepare_verify_and_last_head_races_deny_delivery()->TestResult {
    for kind in 0..3{for stage in 0..3{let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let base=envelope(&s,&raw)?;let v=if kind==0{base.clone()}else{find(&base)};let r=replace(&base);
        let a=search!(&p,&v)?;let l=literal!(&p,&r)?;let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,
            ContentDigest::of(b"selector product race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation"),ContentDigest::of(b"transaction"))?;
        let b=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
        let bound=StoredFormProvider::bind(&s.artifacts,&b,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
        match(kind==2,stage){(false,0)=>{search!(&bound,&v)?;},(false,1)=>{a.verify(&bound,5)?;},(false,_)=>{a.with_verified_json(&bound,5,|_|())?;},(true,0)=>{literal!(&bound,&r)?;},(true,1)=>{l.verify(&bound,5)?;},_=>{l.with_verified_bytes(&bound,5,|_|())?;}}
        let n=b.repository().calls.load(Ordering::SeqCst);assert!(n>=4);b.repository().calls.store(0,Ordering::SeqCst);b.repository().trigger.store(n,Ordering::SeqCst);let called=Cell::new(false);
        match(kind==2,stage){(false,0)=>assert!(search!(&bound,&v).is_err()),(false,1)=>assert!(a.verify(&bound,6).is_err()),(false,_)=>assert!(a.with_verified_json(&bound,6,|_|called.set(true)).is_err()),
            (true,0)=>assert!(literal!(&bound,&r).is_err()),(true,1)=>assert!(l.verify(&bound,6).is_err()),_=>assert!(l.with_verified_bytes(&bound,6,|_|called.set(true)).is_err())}
        assert!(!called.get());assert_eq!(b.repository().calls.load(Ordering::SeqCst),n);}}Ok(())
}
#[test]
fn review_selector_product_stale_foreign_reversed_and_outside_selection_reject_absent_search_and_literal()->TestResult {
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let base=envelope(&s,&raw)?;let inv=response!(&p,&base);let range=window(&inv,"memo_body",7)?;
    for key in["stale","foreign","reversed","outside","extra"]{let mut v=find(&base);v["selector"]["scope"]=json!("selection");v["selector"]["range"]=range.clone();v["operation"]["query"]=json!("absent");
        match key{"stale"=>v["selector"]["range"]["index_sha256"]=json!("0".repeat(64)),"foreign"=>v["selector"]["range"]["start"]["paragraph_handle"]=json!("foreign-paragraph"),
            "reversed"=>v["selector"]["range"]["start"]["normalized_scalar"]=json!(9),"outside"=>v["selector"]["range"]["end"]["normalized_scalar"]=json!(9999),_=>v["selector"]["range"]["start"]["approved"]=json!(true)}
        let mut r=replace(&base);r["selector"]=v["selector"].clone();assert!(search!(&p,&v).is_err());assert!(literal!(&p,&r).is_err());}
    Ok(())
}
#[test]
fn review_selector_product_response_writer_and_selected_match_caps_reject_without_partial_output()->TestResult {
    let raw=fixture::package()?;let original=ContentDigest::of(&raw);let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let base=envelope(&s,&raw)?;
    for v in[base.clone(),find(&base)]{assert!(S::prepare_json(&p,&wire(&v)?,SourceSearchLimits::new(Config{result_bytes:1,..Default::default()})?,4).is_err());}
    let r=replace(&base);assert!(L::prepare_json(&p,&wire(&r)?,SourceSearchLimits::new(Config{result_bytes:1,..Default::default()})?,Default::default(),4).is_err());
    assert!(L::prepare_json(&p,&wire(&r)?,Default::default(),WriterLimits::new(WriterLimitConfig{max_output_bytes:1})?,4).is_err());
    let mut v=find(&base);v["operation"]["max_results"]=json!(1);assert!(search!(&p,&v).is_err());let mut r=r;r["operation"]["max_replacements"]=json!(1);assert!(literal!(&p,&r).is_err());
    assert_eq!(ContentDigest::of(&raw),original);assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
}
#[test]
fn review_selector_product_field_cache_enclosing_fields_controls_and_noop_are_not_write_grants()->TestResult {
    for outer in[false,true]{let body=if outer{format!("<hp:p id='1'><hp:run><hp:ctrl><hp:fieldBegin id='99' type='DOC_DATE'/></hp:ctrl>{}<hp:ctrl><hp:fieldEnd beginIDRef='99'/></hp:ctrl></hp:run></hp:p>",fixture::run_body())}else{fixture::body()};
        let raw=fixture::with_body(&body)?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let base=envelope(&s,&raw)?;let r=replace(&base);
        if outer{assert!(literal!(&p,&r).is_err());continue;}
        for q in["CACHE FROZEN","\n"]{let mut v=r.clone();v["operation"]["query"]=json!(q);assert!(literal!(&p,&v).is_err());}
        let mut v=r;v["operation"]["replacement"]=json!("K");assert!(literal!(&p,&v).is_err());}
    Ok(())
}
#[test]
fn review_selector_product_all_legacy_search_and_literal_schemas_remain_separate_before_source_reads()->TestResult {
    use hwpx_agent_cli::form_product_request::{stored_source_search::StoredSourceSearchProductRequest as LegacySearch,stored_literal_replacement::{StoredLiteralReplacementProductRequest as V1,atoms::StoredLiteralTextAtomProductRequest as V2,review::StoredReviewLiteralProductRequest as V3}};
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let base=envelope(&s,&raw)?;let before=s.metadata.audit_events()?.len();
    for version in 1..=5{let mut v=find(&base);v["schema_version"]=json!(format!("hwpx-agent.product-source-search-request/v{version}"));assert!(matches!(search!(&p,&v),Err(SE::Request)));assert!(matches!(LegacySearch::prepare_json(&p,&wire(&v)?,Default::default(),4),Err(SE::Request)));assert!(matches!(V5::prepare_json(&p,&wire(&v)?,Default::default(),4),Err(SE::Request)));}
    for version in 1..=3{let mut r=replace(&base);r["schema_version"]=json!(format!("hwpx-agent.product-literal-replacement-request/v{version}"));assert!(matches!(literal!(&p,&r),Err(LE::Request)));for result in[V1::prepare_json(&p,&wire(&r)?,Default::default(),Default::default(),4).map(|_|()),V2::prepare_json(&p,&wire(&r)?,Default::default(),Default::default(),4).map(|_|()),V3::prepare_json(&p,&wire(&r)?,Default::default(),Default::default(),4).map(|_|())]{assert!(matches!(result,Err(LE::Request)));}}
    assert!(matches!(V5::prepare_json(&p,&wire(&find(&base))?,Default::default(),4),Err(SE::Request)));assert!(matches!(V3::prepare_json(&p,&wire(&replace(&base))?,Default::default(),Default::default(),4),Err(LE::Request)));assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn review_selector_product_overlapping_node_sets_are_semantic_canonical_but_wire_order_remains_bound()->TestResult {
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let base=envelope(&s,&raw)?;let inv=response!(&p,&base);
    let main=window(&inv,"body_and_notes",7)?;let memo=window(&inv,"memo_body",7)?;let mut v=find(&base);v["selector"]["scope"]=json!("node_set");v["selector"]["range"]=json!({"node_ids":[node(&inv,&main["start"]["paragraph_handle"])?,node(&inv,&memo["start"]["paragraph_handle"])?]});
    let a=search!(&p,&v)?;let result:Value=a.with_verified_json(&p,5,|b|serde_json::from_slice(b))??;assert_eq!(result["result"]["matches"].as_array().ok_or("matches")?.len(),6);
    let mut r=replace(&base);r["selector"]=v["selector"].clone();let l=literal!(&p,&r)?;assert_eq!(l.receipt().stored.output.body_candidate.output.matched_occurrences,6);
    v["selector"]["range"]["node_ids"].as_array_mut().ok_or("nodes")?.reverse();let b=search!(&p,&v)?;assert_eq!(a.receipt().stored.result_sha256,b.receipt().stored.result_sha256);assert_ne!(a.receipt().canonical_request_sha256,b.receipt().canonical_request_sha256);
    r["selector"]=v["selector"].clone();let m=literal!(&p,&r)?;assert_eq!(l.receipt().stored.output,m.receipt().stored.output);assert_ne!(l.receipt().canonical_request_sha256,m.receipt().canonical_request_sha256);Ok(())
}
