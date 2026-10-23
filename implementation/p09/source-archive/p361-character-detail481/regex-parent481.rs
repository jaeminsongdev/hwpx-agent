use super::*;
use hwpx_agent_cli::form_product_request::{stored_literal_replacement::{regex::{StoredRegexReplacementProductRequest as Product,RegexReplacementProductError as E,
    REGEX_REPLACEMENT_PRODUCT_REQUEST_SCHEMA as SCHEMA},LiteralReplacementProductError as LE},stored_source_search::selector::review::StoredReviewScopeProductRequest as Discovery};
use hwpx_agent_cli::form_stored_provider::actual_import::literal_search_output::regex::StoredRegexReplacementError as StoredError;
use hwpx_package::{WriterLimits,WriterLimitConfig,document_import::search::{SourceSearchLimits,SourceSearchLimitConfig as Config,
    SourceSearchQuery as Query,SourceSearchMode as Mode,selector::SourceIndexScopeSelector as Scope,reviews::SourceReviewTextPolicy as Policy,
    replacement::{SourceReplacementRunPolicy as Run,SourceLiteralReplacementError as Compile,atoms::regex::SourceRegexReplacementError as CoreError}}};
use serde_json::{json,Value};
use std::{cell::Cell,io::Cursor,sync::atomic::AtomicUsize};
use revision_service as rev;
#[path="../../../../hwpx-package/tests/support/review_scope_fixture.rs"] mod fixture;
#[allow(dead_code)] #[path="../../../../hwpx-package/tests/support/document_import_review_assembly_fixture.rs"] mod assembly;
#[allow(dead_code)] #[path="../../../../hwpx-package/tests/support/review_cell_output_fixture.rs"] mod table;
const TAB:&str="<hp:tab width='1' leader='0' type='0'/>";
macro_rules! write_provider{($s:ident,$actor:ident,$p:ident)=>{
    let $actor=RequestContext::new($s.reader.tenant_id(),$s.reader.subject(),[AuthScope::DocumentRead,AuthScope::DocumentWrite]);
    let $p=StoredFormProvider::bind(&$s.artifacts,&$s.revisions,&$actor,&$s.revision_context,$s.project,$s.branch,DocumentId::parse("actual-form-document")?)?;
}}
macro_rules! prepare{($p:expr,$v:expr)=>{Product::prepare_json($p,&wire($v)?,Default::default(),Default::default(),4)}}
fn wire(v:&Value)->Result<Vec<u8>,serde_json::Error>{serde_json::to_vec(v)}
fn policy(h:bool,m:bool)->Value{json!({"include_hidden_explanations":h,"include_memo_bodies":m})}
fn all()->Policy{Policy{include_hidden_explanations:true,include_memo_bodies:true}}
fn query(q:&str)->Query<'_>{Query{query:q,mode:Mode::Regex,case_sensitive:true,whole_word:false,max_results:100}}
fn envelope(s:&StoredFixture,raw:&[u8])->Result<Value,Box<dyn Error>>{let revision=s.head.revision_id().ok_or("head")?.public_id();Ok(json!({
    "schema_version":SCHEMA,"idempotency_key":"PRIVATE-REGEX-KEY","plan_id":"regex-candidate-plan","project_id":s.project.public_id(),"document_id":"actual-form-document","base_revision":revision,
    "expected_head_generation":s.head.generation(),"expected_source_package_sha256":ContentDigest::of(raw).hex(),"selector":{"revision_id":revision,"scope":"document"},
    "operation":{"kind":"replace_regex","query":"(K)","replacement":"${1}X<&","regex":true,"case_sensitive":true,"whole_word":false,"max_replacements":100,
        "run_policy":"first_original_run_retain_all_runs","review_policy":policy(true,true)}}))}
fn section(raw:&[u8])->Result<String,Box<dyn Error>>{let mut zip=hwpx_package::BoundedZipReader::open(Cursor::new(raw),Default::default())?;
    let i=zip.entries().iter().position(|e|e.path.as_str()=="Contents/section0.xml").ok_or("section")?;Ok(String::from_utf8(zip.read_entry(i)?)?)}
fn inventory(p:&Provider<'_>,base:&Value)->Result<Value,Box<dyn Error>>{let mut v=base.clone();v["schema_version"]=json!("hwpx-agent.product-source-search-request/v6");v["operation"]=json!({"kind":"scope_inventory"});
    let out=Discovery::prepare_json(p,&wire(&v)?,Default::default(),4)?;Ok(out.with_verified_json(p,5,|b|serde_json::from_slice(b))??)}
fn window(inv:&Value,region:&str,a:usize,z:usize)->Result<Value,Box<dyn Error>>{let n=inv["block_regions"].as_array().ok_or("regions")?.iter().position(|r|r==region).ok_or("region")?;
    let b=&inv["inventory"]["blocks"][n];let sha:[u8;32]=serde_json::from_value(inv["inventory"]["index"]["index_sha256"].clone())?;
    Ok(json!({"coordinate_space":"index_nfc_unicode_scalars","index_sha256":hex::encode(sha),
        "start":{"paragraph_handle":b["paragraph_handle"],"block_index":b["block_index"],"normalized_scalar":a},
        "end":{"paragraph_handle":b["paragraph_handle"],"block_index":b["block_index"],"normalized_scalar":z}}))}
#[test]
fn regex_product_discovery_builds_all_four_scopes_and_owned_exact_outputs_without_caller_import()->TestResult{
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=envelope(&s,&raw)?;let inv=inventory(&p,&good)?;let range=window(&inv,"memo_body",7,8)?;
    let node=inv["inventory"]["nodes"].as_array().ok_or("nodes")?.iter().find(|n|n["source_handle"]==range["start"]["paragraph_handle"]).ok_or("node")?;
    for(scope,count)in[("document",6),("section",6),("node_set",2),("selection",1)]{let mut v=good.clone();v["selector"]["scope"]=json!(scope);
        match scope{"section"=>v["selector"]["section_ids"]=inv["inventory"]["section_ids"].clone(),"node_set"=>v["selector"]["range"]=json!({"node_ids":[node["node_id"].clone()]}),"selection"=>{v["selector"]["range"]=range.clone();v["operation"]["query"]=json!("^(K)$");},_=>{}}
        let out=prepare!(&p,&v)?;drop(v);out.verify(&p,5)?;let actual=out.with_verified_bytes(&p,5,section)??;
        let old=section(&raw)?;let expected=if count==6{old.replace("K K","KX&lt;&amp; KX&lt;&amp;")}else if count==2{old.replace("MEMO K K","MEMO KX&lt;&amp; KX&lt;&amp;")}else{old.replace("MEMO K K","MEMO K KX&lt;&amp;")};
        assert_eq!(actual,expected);assert_eq!(out.receipt().stored.output.output.matched_occurrences,count);assert_eq!(out.receipt().capability_id,"search.replace_regex");}
    Ok(())
}
#[test]
fn regex_product_distinct_named_numbered_optional_and_casefold_values_are_not_a_fixed_literal_replacement()->TestResult{
    let raw=fixture::with_body("<hp:p id='1'><hp:run><hp:t>A12 B3 b</hp:t></hp:run></hp:p>")?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=envelope(&s,&raw)?;
    v["operation"]["query"]=json!(r"(?P<l>[AB])(?P<n>[0-9]+)|(?P<optional>a)?b");v["operation"]["replacement"]=json!("${n}-$l-$0-$$-${optional}");
    let out=prepare!(&p,&v)?;assert_eq!(out.with_verified_bytes(&p,5,section)??,section(&raw)?.replace("A12 B3 b","12-A-A12-$- 3-B-B3-$- --b-$-"));
    let r=&out.receipt().stored.output;assert_ne!(r.template_sha256,r.expansion_sha256);assert_eq!(r.expansion_sha256,r.output.replacement_sha256);assert_eq!(r.expanded_replacement_bytes,r.output.replacement_bytes);
    let raw=fixture::with_body("<hp:p id='1'><hp:run><hp:t>Cat scatter CAT</hp:t></hp:run></hp:p>")?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=envelope(&s,&raw)?;
    v["operation"]["query"]=json!("(?P<w>cat)");v["operation"]["replacement"]=json!("${w}!");v["operation"]["case_sensitive"]=json!(false);v["operation"]["whole_word"]=json!(true);
    assert_eq!(prepare!(&p,&v)?.with_verified_bytes(&p,5,section)??,section(&raw)?.replace("Cat scatter CAT","Cat! scatter CAT!"));Ok(())
}
#[test]
fn regex_product_partial_cross_run_hangul_nfc_and_mixed_atom_controls_keep_original_bytes_and_structure()->TestResult{
    let old="<hp:t>MEMO K K</hp:t>";let nfc="<hp:t>Xᄀ</hp:t></hp:run><hp:run><hp:t>ᅡ</hp:t></hp:run><hp:run><hp:t>ᆨY</hp:t>";
    let raw=fixture::with_body(&fixture::body().replace(old,nfc))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=envelope(&s,&raw)?;let inv=inventory(&p,&v)?;
    v["selector"]["scope"]=json!("selection");v["selector"]["range"]=window(&inv,"memo_body",1,2)?;v["operation"]["query"]=json!("^(각)$");v["operation"]["replacement"]=json!("${1}!");
    let out=prepare!(&p,&v)?;assert_eq!(out.with_verified_bytes(&p,5,section)??,section(&raw)?.replace("Xᄀ","X각!").replace('ᅡ',"").replace("ᆨY","Y"));assert_eq!(out.receipt().stored.output.output.changed_scalar_ranges,3);
    let raw=fixture::with_body(&fixture::body().replace("MEMO K K",&format!("K{TAB}K<hp:lineBreak> </hp:lineBreak>")))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=envelope(&s,&raw)?;
    v["operation"]["replacement"]=json!("${1}X");let out=prepare!(&p,&v)?;assert_eq!(out.with_verified_bytes(&p,5,section)??,section(&raw)?.replace('K',"KX"));assert!(out.receipt().stored.output.output.original_control_bytes_preserved);Ok(())
}
#[test]
fn regex_product_four_policies_exclude_before_caps_and_real_excluded_node_never_widens_scope()->TestResult{
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut hashes=BTreeSet::new();
    for(h,m,count)in[(false,false,2),(true,false,4),(false,true,4),(true,true,6)]{let mut v=envelope(&s,&raw)?;v["operation"]["review_policy"]=policy(h,m);v["operation"]["max_replacements"]=json!(count);
        let out=prepare!(&p,&v)?;hashes.insert(out.receipt().stored.output.search_request_sha256);assert_eq!(out.receipt().stored.output.output.matched_occurrences,count);
        let mut expected=section(&raw)?.replace("BODY K K","BODY KX&lt;&amp; KX&lt;&amp;");if h{expected=expected.replace("HIDDEN K K","HIDDEN KX&lt;&amp; KX&lt;&amp;");}if m{expected=expected.replace("MEMO K K","MEMO KX&lt;&amp; KX&lt;&amp;");}assert_eq!(out.with_verified_bytes(&p,5,section)??,expected);}
    assert_eq!(hashes.len(),4);let mut v=envelope(&s,&raw)?;let inv=inventory(&p,&v)?;let range=window(&inv,"memo_body",7,8)?;
    v["selector"]["scope"]=json!("selection");v["selector"]["range"]=range;v["operation"]["review_policy"]=policy(false,false);
    assert!(matches!(prepare!(&p,&v),Err(E::Stored(StoredError::Output(CoreError::Compile(Compile::NoMatches))))));Ok(())
}
#[test]
fn regex_product_strict_shape_template_fixed_mode_policy_duplicates_and_revision_fail_before_source_reads()->TestResult{
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=envelope(&s,&raw)?;let before=s.metadata.audit_events()?.len();let mut bad=vec![b"null".to_vec(),b"[]".to_vec(),format!("{} {{}}",serde_json::to_string(&good)?).into_bytes()];
    for key in["schema_version","idempotency_key","project_id","document_id","base_revision","expected_head_generation","expected_source_package_sha256","plan_id","selector","operation"]{let mut v=good.clone();v.as_object_mut().ok_or("envelope")?.remove(key);bad.push(wire(&v)?);}
    for key in["kind","query","replacement","regex","case_sensitive","whole_word","max_replacements","run_policy","review_policy"]{let mut v=good.clone();v["operation"].as_object_mut().ok_or("operation")?.remove(key);bad.push(wire(&v)?);}
    for(key,value)in[("kind",json!("replace_literal")),("regex",json!(false)),("query",json!("")),("query",json!("Q".repeat(4097))),("replacement",json!("$")),("replacement",json!("${}")),("replacement",json!("\n")),("max_replacements",json!(0)),("max_replacements",json!(10001)),("run_policy",json!("flatten_runs")),("style_filter",json!({})),("include_hidden",json!(true)),("preview_only",json!(false))]{let mut v=good.clone();v["operation"][key]=value;bad.push(wire(&v)?);}
    for pol in[json!(null),json!([]),json!({}),json!({"include_hidden_explanations":true}),json!({"include_hidden_explanations":true,"include_memo_bodies":1}),json!({"include_hidden_explanations":true,"include_memo_bodies":true,"approved":true})]{let mut v=good.clone();v["operation"]["review_policy"]=pol;bad.push(wire(&v)?);}
    for sel in[json!([]),json!({"scope":"document"}),json!({"revision_id":good["base_revision"],"scope":"document","range":null}),json!({"revision_id":good["base_revision"],"scope":"section","section_ids":[]}),json!({"revision_id":rev::RevisionId::generate().public_id(),"scope":"document"})]{let mut v=good.clone();v["selector"]=sel;bad.push(wire(&v)?);}
    for(key,value)in[("scope",json!({})),("source_graph",json!({})),("approved",json!(true)),("expected_head_generation",json!(0)),("expected_source_package_sha256",json!("A".repeat(64)))]{let mut v=good.clone();v[key]=value;bad.push(wire(&v)?);}
    let text=serde_json::to_string(&good)?;for(from,to)in[("\"regex\":true","\"regex\":true,\"reg\\u0065x\":false"),("\"scope\":\"document\"","\"scope\":\"document\",\"sco\\u0070e\":\"selection\"")]{let raw=text.replace(from,to);assert_ne!(raw,text);bad.push(raw.into_bytes());}
    for raw in bad{assert!(matches!(Product::prepare_json(&p,&raw,Default::default(),Default::default(),4),Err(E::Request)));}assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn regex_product_exact_16k_raw_canonical_template_expansion_key_plan_and_policy_bindings_are_distinct()->TestResult{
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=envelope(&s,&raw)?;let out=prepare!(&p,&good)?;
    let mut bytes=wire(&good)?;bytes.resize(16*1024,b' ');let padded=Product::prepare_json(&p,&bytes,Default::default(),Default::default(),4)?;
    assert_ne!(out.receipt().raw_request_sha256,padded.receipt().raw_request_sha256);assert_eq!(out.receipt().canonical_request_sha256,padded.receipt().canonical_request_sha256);bytes.push(b' ');
    assert!(matches!(Product::prepare_json(&p,&bytes,Default::default(),Default::default(),4),Err(E::Limit)));assert!(matches!(Product::prepare_json(&p,b"",Default::default(),Default::default(),4),Err(E::Limit)));
    for(key,value)in[("idempotency_key",json!("OTHER-KEY")),("plan_id",json!("other-plan"))]{let mut v=good.clone();v[key]=value;let other=prepare!(&p,&v)?;assert_ne!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);assert_ne!(out.receipt().scoped_request_sha256,other.receipt().scoped_request_sha256);assert_eq!(out.receipt().stored.output.output.output_package_sha256,other.receipt().stored.output.output.output_package_sha256);}
    let mut v=good.clone();v["operation"]["replacement"]=json!("$1X");assert!(prepare!(&p,&v).is_err());v["operation"]["replacement"]=json!("${01}X<&");let other=prepare!(&p,&v)?;
    assert_ne!(out.receipt().stored.output.template_sha256,other.receipt().stored.output.template_sha256);assert_ne!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);
    assert_eq!(out.receipt().stored.output.expansion_sha256,other.receipt().stored.output.expansion_sha256);assert_eq!(out.receipt().stored.output.output.output_package_sha256,other.receipt().stored.output.output.output_package_sha256);
    let mut v=good;v["operation"]["review_policy"]=policy(false,false);assert_ne!(out.receipt().stored.output.search_request_sha256,prepare!(&p,&v)?.receipt().stored.output.search_request_sha256);Ok(())
}
#[test]
fn regex_product_all_four_literal_schemas_reject_regex_combinations_before_original_reads()->TestResult{
    use hwpx_agent_cli::form_product_request::stored_literal_replacement::{StoredLiteralReplacementProductRequest as V1,atoms::StoredLiteralTextAtomProductRequest as V2,
        review::StoredReviewLiteralProductRequest as V3,selector::StoredSelectorLiteralProductRequest as V4};
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=envelope(&s,&raw)?;let before=s.metadata.audit_events()?.len();
    for version in 1..=4{let mut v=good.clone();v["schema_version"]=json!(format!("hwpx-agent.product-literal-replacement-request/v{version}"));let bytes=wire(&v)?;
        assert!(matches!(Product::prepare_json(&p,&bytes,Default::default(),Default::default(),4),Err(E::Request)));
        assert!(matches!(V1::prepare_json(&p,&bytes,Default::default(),Default::default(),4),Err(LE::Request)));assert!(matches!(V2::prepare_json(&p,&bytes,Default::default(),Default::default(),4),Err(LE::Request)));
        assert!(matches!(V3::prepare_json(&p,&bytes,Default::default(),Default::default(),4),Err(LE::Request)));assert!(matches!(V4::prepare_json(&p,&bytes,Default::default(),Default::default(),4),Err(LE::Request)));}
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn regex_product_current_write_source_head_and_five_foreign_scopes_reject_retained_output()->TestResult{
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=envelope(&s,&raw)?;let reader=s.provider()?;assert!(prepare!(&reader,&v).is_err());let out=prepare!(&p,&v)?;let called=Cell::new(false);
    assert!(out.with_verified_bytes(&reader,5,|_|called.set(true)).is_err());
    let source=reader.import_actual_forms(s.head,4)?;assert!(matches!(source.prepare_review_selector_regex_candidate(&reader,query("K"),Scope::Document,all(),"X",Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),4),Err(StoredError::Permission)));
    for variant in 0..5{let tenant=if variant==4{TenantId::new(Uuid::from_u128(997))?}else{s.reader.tenant_id()};let subject=if variant==3{SubjectDigest::from_authenticated_subject("foreign-regex")?}else{s.reader.subject()};
        let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);let context=rev::RevisionRequestContext::new(tenant,subject);let project=if variant==2{rev::ProjectId::parse("prj_70000000000000000000000000000002")?}else{s.project};let branch=if variant==1{rev::BranchId::parse("brn_70000000000000000000000000000002")?}else{s.branch};
        let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&context,project,branch,DocumentId::parse(if variant==0{"foreign-document"}else{"actual-form-document"})?)?;
        assert!(out.verify(&other,5).is_err());assert!(out.with_verified_bytes(&other,5,|_|called.set(true)).is_err());}
    for(key,value)in[("expected_head_generation",json!(s.head.generation()+1)),("expected_source_package_sha256",json!("0".repeat(64))),("document_id",json!("foreign-document")),("project_id",json!("prj_70000000000000000000000000000002"))]{let mut bad=v.clone();bad[key]=value;assert!(prepare!(&p,&bad).is_err());}assert!(!called.get());Ok(())
}
#[test]
fn regex_product_acl_regrant_quarantine_and_aead_guard_each_retained_output_and_new_preparation()->TestResult{
    for mode in 0..3{let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=envelope(&s,&raw)?;let out=prepare!(&p,&v)?;
        match mode{0=>{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;},1=>{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("REGEX_PRODUCT_TEST")?,5)?;},_=>s.blobs.tamper.store(true,Ordering::SeqCst)}
        let called=Cell::new(false);assert!(out.verify(&p,6).is_err());assert!(out.with_verified_bytes(&p,6,|_|called.set(true)).is_err());assert!(prepare!(&p,&v).is_err());assert!(!called.get());
        if mode==0{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;out.verify(&p,8)?;out.with_verified_bytes(&p,8,|_|())?;}}
    Ok(())
}
struct BoundaryRepo{inner:rev::InMemoryRevisionRepository,calls:AtomicUsize,trigger:AtomicUsize,context:rev::RevisionRequestContext,advance:rev::RevisionCommitRequest}
impl rev::RevisionRepository for BoundaryRepo{
    fn compare_and_swap(&self,c:&rev::RevisionRequestContext,r:&rev::RevisionCommitRequest)->Result<rev::CommitOutcome,rev::RevisionError>{self.inner.compare_and_swap(c,r)}
    fn head(&self,t:TenantId,p:rev::ProjectId,b:rev::BranchId)->Result<rev::RevisionHead,rev::RevisionError>{let n=self.calls.fetch_add(1,Ordering::SeqCst)+1;if n==self.trigger.load(Ordering::SeqCst){assert!(matches!(self.inner.compare_and_swap(&self.context,&self.advance)?,rev::CommitOutcome::Committed(_)));}self.inner.head(t,p,b)}
    fn node(&self,t:TenantId,p:rev::ProjectId,r:rev::RevisionId)->Result<rev::RevisionNode,rev::RevisionError>{self.inner.node(t,p,r)}
}
#[test]
fn regex_product_prepare_verify_and_bytes_final_head_races_block_consumer_access()->TestResult{
    for stage in 0..3{let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=envelope(&s,&raw)?;let bytes=wire(&v)?;let out=prepare!(&p,&v)?;
        let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,ContentDigest::of(b"regex candidate race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation"),ContentDigest::of(b"transaction"))?;
        let b=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});let bound=StoredFormProvider::bind(&s.artifacts,&b,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
        match stage{0=>{Product::prepare_json(&bound,&bytes,Default::default(),Default::default(),5)?;},1=>{out.verify(&bound,5)?;},_=>{out.with_verified_bytes(&bound,5,|_|())?;}}
        let calls=b.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);b.repository().calls.store(0,Ordering::SeqCst);b.repository().trigger.store(calls,Ordering::SeqCst);let called=Cell::new(false);
        match stage{0=>assert!(Product::prepare_json(&bound,&bytes,Default::default(),Default::default(),6).is_err()),1=>assert!(out.verify(&bound,6).is_err()),_=>assert!(out.with_verified_bytes(&bound,6,|_|called.set(true)).is_err())}
        assert!(!called.get());assert_eq!(b.repository().calls.load(Ordering::SeqCst),calls);}
    Ok(())
}
#[test]
fn regex_product_cache_control_zero_width_noop_and_table_protection_reject_whole_candidate()->TestResult{
    for(body,pattern)in[(fixture::body().replace("CACHE FROZEN","CACHE K"),"K"),(fixture::body(),"^"),(fixture::body(),"K")]{let raw=fixture::with_body(&body)?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=envelope(&s,&raw)?;v["operation"]["query"]=json!(pattern);v["operation"]["replacement"]=json!(if pattern=="K"&& !body.contains("CACHE K"){"$0"}else{"X"});assert!(prepare!(&p,&v).is_err());}
    let raw=fixture::with_body(&fixture::body().replace("MEMO K K",&format!("K{TAB}K")))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=envelope(&s,&raw)?;v["operation"]["query"]=json!(r"\t");v["operation"]["replacement"]=json!("X");assert!(prepare!(&p,&v).is_err());
    let raw=assembly::package(&table::table(300).replace("lock='0'","lock='1'"))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=envelope(&s,&raw)?;v["operation"]["query"]=json!("CELL-(OLD)");
    assert!(matches!(prepare!(&p,&v),Err(E::Stored(StoredError::Output(CoreError::Compile(Compile::Protection))))));Ok(())
}
#[test]
fn regex_product_pattern_reference_match_output_writer_and_empty_capture_work_limits_never_truncate()->TestResult{
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=envelope(&s,&raw)?;
    for(pattern,template)in[("(","X"),("(K)","${unknown}")]{let mut v=good.clone();v["operation"]["query"]=json!(pattern);v["operation"]["replacement"]=json!(template);assert!(prepare!(&p,&v).is_err());}
    let mut v=good.clone();v["operation"]["max_replacements"]=json!(1);assert!(prepare!(&p,&v).is_err());
    assert!(Product::prepare_json(&p,&wire(&good)?,SourceSearchLimits::new(Config{result_bytes:1,..Default::default()})?,Default::default(),4).is_err());
    assert!(Product::prepare_json(&p,&wire(&good)?,Default::default(),WriterLimits::new(WriterLimitConfig{max_output_bytes:1})?,4).is_err());
    let limits=SourceSearchLimits::new(Config{decomposed_scalars:512,..Default::default()})?;
    for(count,pass)in[(15,true),(16,false)]{let raw=fixture::with_body(&format!("<hp:p id='1'><hp:run><hp:t>{}</hp:t></hp:run></hp:p>","b".repeat(count)))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=envelope(&s,&raw)?;
        v["operation"]["query"]=json!("(a)?b");v["operation"]["replacement"]=json!("${1}".repeat(32));let out=Product::prepare_json(&p,&wire(&v)?,limits,Default::default(),4);
        if pass{let out=out?;out.verify(&p,5)?;assert_eq!(out.receipt().stored.output.expansion_work_units,512);assert_eq!(out.receipt().stored.output.expanded_replacement_bytes,0);}else{assert!(matches!(out,Err(E::Stored(StoredError::Output(CoreError::Limit)))));}}
    Ok(())
}
#[test]
fn regex_product_borrowed_owned_and_json_candidates_share_receipts_preserve_sources_and_do_not_grant_execution()->TestResult{
    let raw=fixture::package()?;let original=ContentDigest::of(&raw);let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=envelope(&s,&raw)?;let out=prepare!(&p,&v)?;
    let source=p.import_actual_forms(s.head,4)?;let borrowed=source.prepare_review_selector_regex_candidate(&p,query("(K)"),Scope::Document,all(),"${1}X<&",Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),4)?;
    assert_eq!(borrowed.verify(&p,5)?,out.receipt().stored);drop(borrowed);
    let owned=source.into_review_selector_regex_candidate(&p,query("(K)"),Scope::Document,all(),"${1}X<&",Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),4)?;
    assert_eq!(owned.verify(&p,5)?,out.receipt().stored);assert_eq!(owned.with_verified_bytes(&p,5,<[u8]>::to_vec)?,out.with_verified_bytes(&p,5,<[u8]>::to_vec)?);
    assert!(!format!("{out:?}{:?}",out.receipt()).contains("PRIVATE-REGEX-KEY"));assert!(!serde_json::to_string(out.receipt())?.contains("PRIVATE-AUTHOR"));
    assert!(matches!(out.require_current_product_route(&p,5),Err(E::RouteUnqualified)));assert!(!out.receipt().idempotency_key_claimed&&!out.receipt().full_search_native_cas_execution_publication_authority);
    assert_eq!(ContentDigest::of(&raw),original);assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);
    assert!(!out.receipt().stored.output.zero_width_control_or_field_cache_edit_qualified);Ok(())
}
#[path="regex_insertion_product.rs"] mod insertion_v2;
#[path="style_replacement_product.rs"] mod style_v1;
#[path="text_style_product.rs"] mod text_style_v1;
#[path="paragraph_style_product.rs"] mod paragraph_style_v1;
#[path="resolved_style_product.rs"] mod resolved_style_v9;
#[path="unicode_normalization_product.rs"] mod unicode_v1;
