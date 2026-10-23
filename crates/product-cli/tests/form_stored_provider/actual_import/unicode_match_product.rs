//! Exact original-match normalization through current stored access and strict v2 requests.
use super::*;
use hwpx_agent_cli::form_product_request::stored_literal_replacement::unicode::matches::{StoredUnicodeMatchProductRequest as MatchProduct,
    UnicodeMatchProductError as ME,UNICODE_MATCH_PRODUCT_REQUEST_SCHEMA as MATCH_SCHEMA};
use hwpx_agent_cli::form_stored_provider::actual_import::literal_search_output::unicode::matches::StoredUnicodeMatchError as MS;
use hwpx_package::document_import::search::{SourceSearchError as Search,reviews::selector::styles::SourceReviewStyleFilter as Filter,
    inspection::SourceDeclaredStyleFilter as Declared};
macro_rules! match_prepare{($p:expr,$v:expr)=>{MatchProduct::prepare_json($p,&wire($v)?,Default::default(),Default::default(),4)}}
fn match_request(s:&StoredFixture,raw:&[u8])->Result<Value,Box<dyn Error>>{let mut v=request(s,raw)?;v["schema_version"]=json!(MATCH_SCHEMA);v["operation"]=json!({
    "kind":"normalize_unicode_matches","query":"à","regex":false,"case_sensitive":true,"whole_word":false,"max_matches":100,
    "form":"nfc","run_policy":"first_original_run_retain_all_runs","review_policy":policy(true,true)});Ok(v)}
#[test]
fn unicode_match_product_literal_uses_actual_original_not_search_nfc_and_retains_owned_request()->TestResult {
    let bytes=raw("à à KEEP é")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=match_request(&s,&bytes)?;let out=match_prepare!(&provider,&v)?;drop(v);
    out.verify(&provider,5)?;assert_eq!(out.with_verified_bytes(&provider,5,section)??,section(&bytes)?.replace("à à KEEP é","à à KEEP é"));
    assert_eq!(out.receipt().stored.output.search.search().result().matches().len(),2);assert_eq!(out.receipt().stored.output.output.changed_components,1);assert_eq!(out.receipt().capability_id,"search.normalize_unicode");Ok(())
}
#[test]
fn unicode_match_product_regex_casefold_whole_word_preserves_original_case()->TestResult {
    let bytes=raw("À MÀ à")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=match_request(&s,&bytes)?;
    v["operation"]["regex"]=json!(true);v["operation"]["case_sensitive"]=json!(false);v["operation"]["whole_word"]=json!(true);v["operation"]["form"]=json!("nfd");
    let out=match_prepare!(&provider,&v)?;assert_eq!(out.with_verified_bytes(&provider,5,section)??,section(&bytes)?.replace("À MÀ à","À MÀ à"));assert_eq!(out.receipt().stored.output.search.search().result().matches().len(),2);Ok(())
}
#[test]
fn unicode_match_product_declared_definition_filters_require_all_contributors_before_caps()->TestResult {
    let body="<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>ᄀ</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>ᅡ 가</hp:t></hp:run></hp:p>";
    let bytes=definition::package(body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for filter in[json!({"kind":"declared","filter":{"run_character_property":1}}),json!({"kind":"definition","filter":{"character_source":"run_property","bold":true}})]{
        let mut v=match_request(&s,&bytes)?;v["operation"]["query"]=json!("가");v["operation"]["max_matches"]=json!(1);v["operation"]["style_filter"]=filter;
        let out=match_prepare!(&provider,&v)?;assert_eq!(out.with_verified_bytes(&provider,5,section)??,section(&bytes)?.replace(">ᅡ 가<",">ᅡ 가<"));assert_eq!(out.receipt().stored.output.search.search().result().matches().len(),1);
    }Ok(())
}
#[test]
fn unicode_match_product_four_forms_and_adjacent_occurrences_have_explicit_distinct_semantics()->TestResult {
    let bytes=raw("각 à①ﬃ")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for(form,result)in[("nfc","각 à①ﬃ"),("nfd","각 à①ﬃ"),("nfkc","각 à1ffi"),("nfkd","각 à1ffi")]{let mut v=match_request(&s,&bytes)?;v["operation"]["query"]=json!(".+");v["operation"]["regex"]=json!(true);v["operation"]["form"]=json!(form);
        assert_eq!(match_prepare!(&provider,&v)?.with_verified_bytes(&provider,5,section)??,section(&bytes)?.replace("각 à①ﬃ",result));}
    let bytes=raw("ㄱㅏ")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for(q,result)in[(".","가"),(".+","가")]{let mut v=match_request(&s,&bytes)?;v["operation"]["query"]=json!(q);v["operation"]["regex"]=json!(true);v["operation"]["form"]=json!("nfkc");
        assert_eq!(match_prepare!(&provider,&v)?.with_verified_bytes(&provider,5,section)??,section(&bytes)?.replace("ㄱㅏ",result));}Ok(())
}
#[test]
fn unicode_match_product_discovery_builds_four_scopes_and_clipped_regex_without_caller_import()->TestResult {
    let bytes=definition::package(&(para(1,"X à Z")+&para(2,"Y à Z")))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=match_request(&s,&bytes)?;let inv=inventory(&provider,&good)?;let range=window(&inv,"body_and_notes",2,3)?;
    let node=inv["inventory"]["nodes"].as_array().ok_or("nodes")?.iter().find(|n|n["source_handle"]==range["start"]["paragraph_handle"]).ok_or("node")?;
    for(scope,n)in[("document",2),("section",2),("node_set",1),("selection",1)]{let mut v=good.clone();v["selector"]["scope"]=json!(scope);
        match scope{"section"=>v["selector"]["section_ids"]=inv["inventory"]["section_ids"].clone(),"node_set"=>v["selector"]["range"]=json!({"node_ids":[node["node_id"].clone()]}),"selection"=>{v["selector"]["range"]=range.clone();v["operation"]["regex"]=json!(true);v["operation"]["query"]=json!("^à$");},_=>{}}
        let out=match_prepare!(&provider,&v)?;assert_eq!(out.receipt().stored.output.search.search().result().matches().len(),n);let after=out.with_verified_bytes(&provider,5,section)??;assert!(after.contains("X à Z"));assert_eq!(after.contains("Y à Z"),n==1);
    }Ok(())
}
#[test]
fn unicode_match_product_review_policy_excludes_before_max_matches_and_cache_is_untouched()->TestResult {
    let bytes=definition::package(&fixture::body().replace("K K","à"))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for(h,m,n)in[(false,false,1),(true,false,2),(false,true,2),(true,true,3)]{let mut v=match_request(&s,&bytes)?;v["operation"]["review_policy"]=policy(h,m);v["operation"]["max_matches"]=json!(n);
        let out=match_prepare!(&provider,&v)?;let after=out.with_verified_bytes(&provider,5,section)??;assert_eq!(after.matches('à').count(),n);assert!(after.contains("CACHE FROZEN"));
        assert_eq!(out.receipt().stored.output.search.search().match_regions().len(),n);
    }Ok(())
}
#[test]
fn unicode_match_product_cross_run_entities_controls_and_reordering_keep_original_shells()->TestResult {
    let body="<hp:p id='1'><hp:run charPrIDRef='0'><hp:t charStyleIDRef='0'>&#x1F600;Xᄀ</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t charStyleIDRef='1'>ᅡ</hp:t></hp:run><hp:run><hp:t>ᆨY&#38;</hp:t></hp:run></hp:p>";
    let bytes=definition::package(body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=match_request(&s,&bytes)?;v["operation"]["query"]=json!("각");
    assert_eq!(match_prepare!(&provider,&v)?.with_verified_bytes(&provider,5,section)??,section(&bytes)?.replace('ᄀ',"각").replace(['ᅡ','ᆨ'],""));
    let bytes=raw(&format!("a{TAB}̀à"))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=match_request(&s,&bytes)?;v["operation"]["regex"]=json!(true);v["operation"]["query"]=json!("a\t̀à");
    assert_eq!(match_prepare!(&provider,&v)?.with_verified_bytes(&provider,5,section)??,section(&bytes)?.replace("̀à","̀à"));
    let bytes=raw("à̕")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=match_request(&s,&bytes)?;v["operation"]["query"]=json!("à̕");
    assert_eq!(match_prepare!(&provider,&v)?.with_verified_bytes(&provider,5,section)??,section(&bytes)?.replace("à̕","à̕"));Ok(())
}
#[test]
fn unicode_match_product_missing_unknown_wrong_types_and_policies_fail_before_source_reads()->TestResult {
    let bytes=raw("à")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=match_request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();let mut bad=vec![b"null".to_vec(),b"[]".to_vec(),format!("{} {{}}",serde_json::to_string(&good)?).into_bytes()];
    for key in["schema_version","idempotency_key","project_id","document_id","base_revision","expected_head_generation","expected_source_package_sha256","plan_id","selector","operation"]{let mut v=good.clone();v.as_object_mut().ok_or("envelope")?.remove(key);bad.push(wire(&v)?);}
    for key in["kind","query","regex","case_sensitive","whole_word","max_matches","form","run_policy","review_policy"]{let mut v=good.clone();v["operation"].as_object_mut().ok_or("operation")?.remove(key);bad.push(wire(&v)?);}
    for(key,value)in[("kind",json!("normalize_unicode_scope")),("query",json!("")),("query",json!("Q".repeat(4097))),("regex",json!(1)),("case_sensitive",json!("true")),("whole_word",json!(null)),("max_matches",json!(0)),("max_matches",json!(10001)),("form",json!("NFC")),("run_policy",json!("flatten_runs")),("replacement",json!("X")),("approved",json!(true)),("direction",json!("all"))]{let mut v=good.clone();v["operation"][key]=value;bad.push(wire(&v)?);}
    for pol in[json!(null),json!([]),json!({}),json!({"include_hidden_explanations":true}),json!({"include_hidden_explanations":true,"include_memo_bodies":true,"approved":true})]{let mut v=good.clone();v["operation"]["review_policy"]=pol;bad.push(wire(&v)?);}
    for(key,value)in[("source_graph",json!({})),("expected_head_generation",json!(0)),("expected_source_package_sha256",json!("A".repeat(64)))]{let mut v=good.clone();v[key]=value;bad.push(wire(&v)?);}
    for raw in bad{assert!(matches!(MatchProduct::prepare_json(&provider,&raw,Default::default(),Default::default(),4),Err(ME::Request)));}assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn unicode_match_product_invalid_typed_filters_selectors_and_escaped_duplicate_keys_fail_before_reads()->TestResult {
    let bytes=raw("à")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=match_request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();let mut bad=Vec::new();
    for filter in[json!([]),json!({}),json!({"kind":"declared","filter":{}}),json!({"kind":"definition","filter":{"bold":true}}),json!({"kind":"resolved","filter":{"bold":true}})]{let mut v=good.clone();v["operation"]["style_filter"]=filter;bad.push(wire(&v)?);}
    for selector in[json!([]),json!({"scope":"document"}),json!({"revision_id":good["base_revision"],"scope":"document","range":null}),json!({"revision_id":good["base_revision"],"scope":"section","section_ids":[]}),json!({"revision_id":rev::RevisionId::generate().public_id(),"scope":"document"})]{let mut v=good.clone();v["selector"]=selector;bad.push(wire(&v)?);}
    let text=serde_json::to_string(&good)?;for(from,to)in[("\"query\":\"à\"","\"query\":\"à\",\"qu\\u0065ry\":\"e\""),("\"regex\":false","\"regex\":false,\"regex\":true"),("\"scope\":\"document\"","\"scope\":\"document\",\"sco\\u0070e\":\"selection\"")]{let changed=text.replace(from,to);assert_ne!(changed,text);bad.push(changed.into_bytes());}
    for raw in bad{assert!(matches!(MatchProduct::prepare_json(&provider,&raw,Default::default(),Default::default(),4),Err(ME::Request)));}assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn unicode_match_product_exact_16k_and_optional_null_filter_have_stable_canonical_binding()->TestResult {
    let bytes=raw("à")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=match_request(&s,&bytes)?;let out=match_prepare!(&provider,&good)?;
    let mut padded=wire(&good)?;padded.resize(16*1024,b' ');let other=MatchProduct::prepare_json(&provider,&padded,Default::default(),Default::default(),4)?;assert_ne!(out.receipt().raw_request_sha256,other.receipt().raw_request_sha256);assert_eq!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);
    padded.push(b' ');assert!(matches!(MatchProduct::prepare_json(&provider,&padded,Default::default(),Default::default(),4),Err(ME::Limit)));assert!(matches!(MatchProduct::prepare_json(&provider,b"",Default::default(),Default::default(),4),Err(ME::Limit)));
    let mut v=good;v["operation"]["style_filter"]=json!(null);let other=match_prepare!(&provider,&v)?;assert_ne!(out.receipt().raw_request_sha256,other.receipt().raw_request_sha256);assert_eq!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);Ok(())
}
#[test]
fn unicode_match_product_v1_v2_and_legacy_requests_are_mutually_rejected_before_reads()->TestResult {
    use hwpx_agent_cli::form_product_request::stored_literal_replacement::{StoredLiteralReplacementProductRequest as Literal,paragraph_styles::StoredParagraphStyleProductRequest as Para};
    let bytes=raw("à")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=match_request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();
    for schema in[MATCH_SCHEMA,UNICODE_SCHEMA,"hwpx-agent.product-literal-replacement-request/v1","hwpx-agent.product-regex-replacement-request/v1"]{let mut v=good.clone();v["schema_version"]=json!(schema);let b=wire(&v)?;
        assert!(matches!(UnicodeProduct::prepare_json(&provider,&b,Default::default(),Default::default(),4),Err(UE::Request)));assert!(Literal::prepare_json(&provider,&b,Default::default(),Default::default(),4).is_err());assert!(Product::prepare_json(&provider,&b,Default::default(),Default::default(),4).is_err());assert!(Para::prepare_json(&provider,&b,Default::default(),Default::default(),4).is_err());assert!(Discovery::prepare_json(&provider,&b,Default::default(),4).is_err());
        if schema!=MATCH_SCHEMA{assert!(matches!(MatchProduct::prepare_json(&provider,&b,Default::default(),Default::default(),4),Err(ME::Request)));}}
    for mut old in[request(&s,&bytes)?,envelope(&s,&bytes)?]{old["schema_version"]=json!(MATCH_SCHEMA);assert!(matches!(match_prepare!(&provider,&old),Err(ME::Request)));}
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn unicode_match_product_query_mode_filter_form_policy_max_key_plan_and_scope_bindings_are_distinct()->TestResult {
    let bytes=raw("à①")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=match_request(&s,&bytes)?;let out=match_prepare!(&provider,&good)?;
    for(key,value)in[("idempotency_key",json!("OTHER-KEY")),("plan_id",json!("other-plan"))]{let mut v=good.clone();v[key]=value;let other=match_prepare!(&provider,&v)?;assert_ne!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);assert_ne!(out.receipt().scoped_request_sha256,other.receipt().scoped_request_sha256);assert_eq!(out.receipt().stored.output.output.output_package_sha256,other.receipt().stored.output.output.output_package_sha256);}
    for(key,value)in[("query",json!("à")),("regex",json!(true)),("case_sensitive",json!(false)),("max_matches",json!(101)),("form",json!("nfkc")),("review_policy",policy(false,false)),("style_filter",json!({"kind":"declared","filter":{"run_character_property":0}}))]{let mut v=good.clone();v["operation"][key]=value;
        let other=match_prepare!(&provider,&v)?;assert_ne!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);assert_ne!(out.receipt().stored.output.request_sha256,other.receipt().stored.output.request_sha256);}
    let inv=inventory(&provider,&good)?;let mut v=good;v["selector"]["scope"]=json!("section");v["selector"]["section_ids"]=inv["inventory"]["section_ids"].clone();let other=match_prepare!(&provider,&v)?;assert_ne!(out.receipt().scoped_request_sha256,other.receipt().scoped_request_sha256);Ok(())
}
#[test]
fn unicode_match_product_current_write_and_five_foreign_scopes_deny_retained_delivery()->TestResult {
    let bytes=raw("à")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=match_request(&s,&bytes)?;let reader=s.provider()?;assert!(match_prepare!(&reader,&v).is_err());
    let source=reader.import_actual_forms(s.head,4)?;assert!(matches!(source.prepare_unicode_match_candidate(&reader,Query {mode:Mode::Literal,..query("à")},Scope::Document,all(),None,Form::Nfc,Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),4),Err(MS::Permission)));
    let out=match_prepare!(&provider,&v)?;let called=Cell::new(false);assert!(out.with_verified_bytes(&reader,5,|_|called.set(true)).is_err());
    for variant in 0..5{let tenant=if variant==4{TenantId::new(Uuid::from_u128(997))?}else{s.reader.tenant_id()};let subject=if variant==3{SubjectDigest::from_authenticated_subject("foreign-unicode-match")?}else{s.reader.subject()};let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);let context=rev::RevisionRequestContext::new(tenant,subject);let project=if variant==2{rev::ProjectId::parse("prj_70000000000000000000000000000002")?}else{s.project};let branch=if variant==1{rev::BranchId::parse("brn_70000000000000000000000000000002")?}else{s.branch};
        let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&context,project,branch,DocumentId::parse(if variant==0{"foreign-document"}else{"actual-form-document"})?)?;assert!(out.verify(&other,5).is_err());assert!(out.with_verified_bytes(&other,5,|_|called.set(true)).is_err());}
    assert!(!called.get());Ok(())
}
#[test]
fn unicode_match_product_acl_regrant_quarantine_and_aead_protect_old_and_new_candidates()->TestResult {
    for mode in 0..3{let bytes=raw("à")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=match_request(&s,&bytes)?;let out=match_prepare!(&provider,&v)?;
        match mode{0=>{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;},1=>{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("UNICODE_MATCH_TEST")?,5)?;},_=>s.blobs.tamper.store(true,Ordering::SeqCst)}
        let called=Cell::new(false);assert!(out.verify(&provider,6).is_err());assert!(out.with_verified_bytes(&provider,6,|_|called.set(true)).is_err());assert!(match_prepare!(&provider,&v).is_err());assert!(!called.get());if mode==0{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;out.verify(&provider,8)?;out.with_verified_bytes(&provider,8,|_|())?;}
    }Ok(())
}
#[test]
fn unicode_match_product_prepare_verify_and_delivery_final_head_races_block_consumers()->TestResult {
    for stage in 0..3{let bytes=raw("à")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=match_request(&s,&bytes)?;let b=wire(&v)?;let out=match_prepare!(&provider,&v)?;
        let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,ContentDigest::of(b"unicode match race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation"),ContentDigest::of(b"transaction"))?;
        let repo=rev::RevisionService::new(BoundaryRepo {inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});let bound=StoredFormProvider::bind(&s.artifacts,&repo,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
        match stage{0=>{MatchProduct::prepare_json(&bound,&b,Default::default(),Default::default(),5)?;},1=>{out.verify(&bound,5)?;},_=>{out.with_verified_bytes(&bound,5,|_|())?;}}
        let calls=repo.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);repo.repository().calls.store(0,Ordering::SeqCst);repo.repository().trigger.store(calls,Ordering::SeqCst);let called=Cell::new(false);
        match stage{0=>assert!(MatchProduct::prepare_json(&bound,&b,Default::default(),Default::default(),6).is_err()),1=>assert!(out.verify(&bound,6).is_err()),_=>assert!(out.with_verified_bytes(&bound,6,|_|called.set(true)).is_err())}assert!(!called.get());assert_eq!(repo.repository().calls.load(Ordering::SeqCst),calls);
    }Ok(())
}
#[test]
fn unicode_match_product_borrowed_owned_and_json_share_bound_search_receipts_and_output()->TestResult {
    let bytes=raw("à")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=match_request(&s,&bytes)?;v["operation"]["style_filter"]=json!({"kind":"declared","filter":{"run_character_property":0}});let out=match_prepare!(&provider,&v)?;let source=provider.import_actual_forms(s.head,4)?;
    let filter=Some(Filter::Declared(Declared {run_character_property:Some(0),..Default::default()}));let q=Query {mode:Mode::Literal,..query("à")};
    let borrowed=source.prepare_unicode_match_candidate(&provider,q,Scope::Document,all(),filter.clone(),Form::Nfc,Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),4)?;assert_eq!(borrowed.verify(&provider,5)?,out.receipt().stored);drop(borrowed);
    let owned=source.into_unicode_match_candidate(&provider,q,Scope::Document,all(),filter,Form::Nfc,Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),4)?;
    assert_eq!(owned.verify(&provider,5)?,out.receipt().stored);assert_eq!(owned.with_verified_bytes(&provider,5,<[u8]>::to_vec)?,out.with_verified_bytes(&provider,5,<[u8]>::to_vec)?);assert!(matches!(owned.require_current_product_route(&provider,5),Err(MS::RouteUnqualified)));Ok(())
}
#[test]
fn unicode_match_product_wrong_source_head_revision_scope_and_index_reject_new_preparation()->TestResult {
    let bytes=raw("à")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=match_request(&s,&bytes)?;
    for(key,value)in[("expected_head_generation",json!(s.head.generation()+1)),("expected_source_package_sha256",json!("0".repeat(64))),("document_id",json!("foreign-document")),("project_id",json!("prj_70000000000000000000000000000002")),("base_revision",json!(rev::RevisionId::generate().public_id()))]{let mut v=good.clone();v[key]=value;assert!(match_prepare!(&provider,&v).is_err());}
    let inv=inventory(&provider,&good)?;let mut v=good;v["selector"]["scope"]=json!("selection");v["selector"]["range"]=window(&inv,"body_and_notes",0,1)?;v["selector"]["range"]["index_sha256"]=json!("0".repeat(64));assert!(match_prepare!(&provider,&v).is_err());Ok(())
}
#[test]
fn unicode_match_product_no_match_no_change_zero_width_and_ambiguous_inverse_are_distinct_errors()->TestResult {
    let bytes=raw("ABC à")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=match_request(&s,&bytes)?;v["operation"]["query"]=json!("ABSENT");assert!(matches!(match_prepare!(&provider,&v),Err(ME::Stored(MS::Output(Compile::NoMatches)))));
    v["operation"]["query"]=json!("ABC");assert!(matches!(match_prepare!(&provider,&v),Err(ME::Stored(MS::Output(Compile::NoChange)))));v["operation"]["query"]=json!("^|à");v["operation"]["regex"]=json!(true);assert!(matches!(match_prepare!(&provider,&v),Err(ME::Stored(MS::Output(Compile::Selection)))));
    for(text,q)in[("à̕","à"),("&#x344;","\u{308}")]{let bytes=raw(text)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=match_request(&s,&bytes)?;v["operation"]["query"]=json!(q);assert!(matches!(match_prepare!(&provider,&v),Err(ME::Stored(MS::Output(Compile::Selection)))));}Ok(())
}
#[test]
fn unicode_match_product_matching_protected_noops_and_cache_block_without_touching_unmatched_data()->TestResult {
    let tracked=para(1,"ABC").replace("charPrIDRef='0'","charPrIDRef='0' charTcId='1'");let bytes=definition::package(&tracked)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=match_request(&s,&bytes)?;v["operation"]["query"]=json!("ABC");assert!(matches!(match_prepare!(&provider,&v),Err(ME::Stored(MS::Output(Compile::Protection)))));
    let bytes=definition::package(&fixture::body().replace("K K","à"))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=match_request(&s,&bytes)?;assert!(match_prepare!(&provider,&v)?.with_verified_bytes(&provider,5,section)??.contains("CACHE FROZEN"));
    v["operation"]["query"]=json!("FROZEN");assert!(matches!(match_prepare!(&provider,&v),Err(ME::Stored(MS::Output(Compile::FieldContent)))));Ok(())
}
#[test]
fn unicode_match_product_pattern_match_expansion_response_and_writer_caps_never_return_partial_candidates()->TestResult {
    let bytes=raw("à à ﬃ")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=match_request(&s,&bytes)?;v["operation"]["max_matches"]=json!(1);assert!(matches!(match_prepare!(&provider,&v),Err(ME::Stored(MS::Output(Compile::Search(Search::Limit))))));
    v["operation"]["max_matches"]=json!(100);v["operation"]["query"]=json!("(");v["operation"]["regex"]=json!(true);assert!(matches!(match_prepare!(&provider,&v),Err(ME::Stored(MS::Output(Compile::Search(Search::Pattern))))));
    v["operation"]["regex"]=json!(false);v["operation"]["query"]=json!("à");assert!(MatchProduct::prepare_json(&provider,&wire(&v)?,SourceSearchLimits::new(Config {result_bytes:1,..Default::default()})?,Default::default(),4).is_err());
    assert!(matches!(MatchProduct::prepare_json(&provider,&wire(&v)?,Default::default(),WriterLimits::new(WriterLimitConfig {max_output_bytes:1,..Default::default()})?,4),Err(ME::Stored(MS::Output(Compile::Writer)))));
    let bytes=raw("ﬃ")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=match_request(&s,&bytes)?;v["operation"]["query"]=json!("ﬃ");v["operation"]["form"]=json!("nfkd");assert!(matches!(MatchProduct::prepare_json(&provider,&wire(&v)?,SourceSearchLimits::new(Config {decomposed_scalars:2,..Default::default()})?,Default::default(),4),Err(ME::Stored(MS::Output(Compile::Limit)))));Ok(())
}
#[test]
fn unicode_match_product_private_query_source_and_key_are_redacted_and_execution_stays_closed()->TestResult {
    let bytes=raw("PRIVATE-SOURCE à")?;let original=ContentDigest::of(&bytes);let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=match_request(&s,&bytes)?;v["operation"]["query"]=json!("PRIVATE-SOURCE .+");v["operation"]["regex"]=json!(true);let out=match_prepare!(&provider,&v)?;
    for text in[format!("{out:?}{:?}",out.receipt()),serde_json::to_string(out.receipt())?]{assert!(!text.contains("PRIVATE-SOURCE"));assert!(!text.contains("PRIVATE-UNICODE-KEY"));}
    assert!(matches!(out.require_current_product_route(&provider,5),Err(ME::RouteUnqualified)));assert!(!out.receipt().idempotency_key_claimed&&!out.receipt().full_normalization_native_cas_execution_publication_authority);assert_eq!(ContentDigest::of(&bytes),original);assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
}
#[test]
fn unicode_match_product_many_matches_share_one_span_and_protection_map_with_bound_regions()->TestResult {
    let bytes=raw(&"à ".repeat(128))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=match_request(&s,&bytes)?;v["operation"]["max_matches"]=json!(128);let out=match_prepare!(&provider,&v)?;
    assert_eq!(out.with_verified_bytes(&provider,5,section)??,section(&bytes)?.replace("à","à"));let r=&out.receipt().stored.output;assert_eq!(r.search.search().result().matches().len(),128);assert_eq!(r.search.search().match_regions().len(),128);assert_eq!(r.output.changed_components,128);assert_eq!(r.output.changes.len(),1);let xml=hwpx_package::PreservingXmlDocument::parse(section(&bytes)?.as_bytes())?;assert_eq!(r.output.observed_protection_element_visits,xml.elements().len()*3);Ok(())
}
