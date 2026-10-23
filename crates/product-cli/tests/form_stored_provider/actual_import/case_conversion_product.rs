//! Original-case candidates through current stored access and strict requests, not full transactions.
use super::*;
use hwpx_agent_cli::form_product_request::stored_literal_replacement::case::{StoredCaseProductRequest as CaseProduct,
    CaseProductError as CE,CASE_PRODUCT_REQUEST_SCHEMA as CASE_SCHEMA};
use hwpx_agent_cli::form_stored_provider::actual_import::literal_search_output::case::StoredCaseError as CS;
use hwpx_package::document_import::search::{SourceSearchError as Search,reviews::selector::styles::SourceReviewStyleFilter as Filter,
    inspection::SourceDeclaredStyleFilter as Declared,
    replacement::atoms::case::{SourceCaseMode as CaseMode,SourceCasePolicy as CasePolicy}};
const CASE_POLICY:CasePolicy=CasePolicy::UnicodeDefaultEachMatchedTextGroup;
macro_rules! case_prepare{($p:expr,$v:expr)=>{CaseProduct::prepare_json($p,&wire($v)?,Default::default(),Default::default(),4)}}
fn case_request(s:&StoredFixture,bytes:&[u8])->Result<Value,Box<dyn Error>>{let mut v=request(s,bytes)?;v["schema_version"]=json!(CASE_SCHEMA);
    v["operation"]=json!({"kind":"convert_case_matches","query":"(?s:.+)","regex":true,"case_sensitive":true,"whole_word":false,"max_matches":100,
        "mode":"uppercase","case_policy":"unicode_default_each_matched_text_group","review_policy":policy(true,true)});Ok(v)}
#[test]
fn case_product_upper_lower_changes_original_and_retains_owned_request()->TestResult{
    let bytes=raw("ab CD")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for(mode,expected)in[("uppercase","AB CD"),("lowercase","ab cd")]{let mut v=case_request(&s,&bytes)?;v["operation"]["mode"]=json!(mode);let out=case_prepare!(&provider,&v)?;drop(v);
        out.verify(&provider,5)?;assert_eq!(out.with_verified_bytes(&provider,5,section)??,section(&bytes)?.replace("ab CD",expected));
        assert_eq!(out.receipt().capability_id,"search.case_convert");assert_eq!(out.receipt().stored.output.case_unicode_version,(17,0,0));}Ok(())
}
#[test]
fn case_product_sigma_context_is_match_local_and_crosses_run_style_boundaries()->TestResult{
    let body="<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>A</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t charStyleIDRef='1'>Σ</hp:t></hp:run></hp:p>";
    let bytes=definition::package(body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for(q,expected)in[("Σ",body.replace(">Σ<",">σ<")),(".",body.replace(">A<",">a<").replace(">Σ<",">σ<")),(".+",body.replace(">A<",">a<").replace(">Σ<",">ς<"))]{let mut v=case_request(&s,&bytes)?;v["operation"]["query"]=json!(q);v["operation"]["mode"]=json!("lowercase");
        assert_eq!(case_prepare!(&provider,&v)?.with_verified_bytes(&provider,5,section)??,section(&bytes)?.replace(body,&expected));}Ok(())
}
#[test]
fn case_product_full_expansion_default_i_and_non_bmp_mapping_are_not_casefold_or_normalization()->TestResult{
    for(text,mode,expected)in[("straße ﬃ ǰ","uppercase","STRASSE FFI J̌"),("Iİıi","lowercase","ii̇ıi"),("𐐀𐐨 Ꭰꭰ","lowercase","𐐨𐐨 ꭰꭰ"),("a&#x300; 한글😀","uppercase","A&#x300; 한글😀")]{
        let bytes=raw(text)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=case_request(&s,&bytes)?;v["operation"]["mode"]=json!(mode);
        assert_eq!(case_prepare!(&provider,&v)?.with_verified_bytes(&provider,5,section)??,section(&bytes)?.replace(text,expected));}Ok(())
}
#[test]
fn case_product_discovery_four_scopes_and_clipped_regex_do_not_require_caller_import()->TestResult{
    let bytes=definition::package(&(para(1,"X abc Z")+&para(2,"Y abc Z")))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut good=case_request(&s,&bytes)?;good["operation"]["query"]=json!("abc");let inv=inventory(&provider,&good)?;let range=window(&inv,"body_and_notes",2,5)?;
    let node=inv["inventory"]["nodes"].as_array().ok_or("nodes")?.iter().find(|n|n["source_handle"]==range["start"]["paragraph_handle"]).ok_or("node")?;
    for(scope,n)in[("document",2),("section",2),("node_set",1),("selection",1)]{let mut v=good.clone();v["selector"]["scope"]=json!(scope);
        match scope{"section"=>v["selector"]["section_ids"]=inv["inventory"]["section_ids"].clone(),"node_set"=>v["selector"]["range"]=json!({"node_ids":[node["node_id"].clone()]}),"selection"=>{v["selector"]["range"]=range.clone();v["operation"]["query"]=json!("^abc$");},_=>{}}
        let out=case_prepare!(&provider,&v)?;let after=out.with_verified_bytes(&provider,5,section)??;assert!(after.contains("X ABC Z"));assert_eq!(after.contains("Y abc Z"),n==1);assert_eq!(out.receipt().stored.output.search.search().result().matches().len(),n);}Ok(())
}
#[test]
fn case_product_declared_definition_filters_and_folded_whole_word_apply_before_caps()->TestResult{
    let body="<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>a</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>bc abc xabcx ABC</hp:t></hp:run></hp:p>";
    let bytes=definition::package(body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for filter in[json!({"kind":"declared","filter":{"run_character_property":1}}),json!({"kind":"definition","filter":{"character_source":"run_property","bold":true}})]{let mut v=case_request(&s,&bytes)?;
        v["operation"]["query"]=json!("a[b]c");v["operation"]["case_sensitive"]=json!(false);v["operation"]["whole_word"]=json!(true);v["operation"]["max_matches"]=json!(2);v["operation"]["style_filter"]=filter;
        let out=case_prepare!(&provider,&v)?;assert_eq!(out.with_verified_bytes(&provider,5,section)??,section(&bytes)?.replace(">bc abc xabcx ABC<",">bc ABC xabcx ABC<"));assert_eq!(out.receipt().stored.output.search.search().result().matches().len(),2);}Ok(())
}
#[test]
fn case_product_review_policies_preserve_excluded_bodies_cache_and_author_metadata()->TestResult{
    let body=fixture::body();let bytes=definition::package(&body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for(h,m,n)in[(false,false,2),(true,false,4),(false,true,4),(true,true,6)]{let mut v=case_request(&s,&bytes)?;v["operation"]["query"]=json!("K");v["operation"]["regex"]=json!(false);v["operation"]["mode"]=json!("lowercase");v["operation"]["review_policy"]=policy(h,m);v["operation"]["max_matches"]=json!(n);
        let mut expected=body.replace("BODY K K","BODY k k");if h{expected=expected.replace("HIDDEN K K","HIDDEN k k");}if m{expected=expected.replace("MEMO K K","MEMO k k");}
        let out=case_prepare!(&provider,&v)?;assert_eq!(out.with_verified_bytes(&provider,5,section)??,section(&bytes)?.replace(&body,&expected));assert_eq!(out.receipt().stored.output.search.search().result().matches().len(),n);}Ok(())
}
#[test]
fn case_product_expansion_and_controls_preserve_reference_shells_entities_and_individual_styles()->TestResult{
    let body=format!("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>A&#x26;{TAB}Σ<hp:lineBreak> </hp:lineBreak>AΣ</hp:t><hp:ctrl><hp:bookmark name='KEEP'/></hp:ctrl></hp:run><hp:run charPrIDRef='1'><hp:t charStyleIDRef='1'>ß</hp:t></hp:run></hp:p>");
    let bytes=definition::package(&body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=case_request(&s,&bytes)?;v["operation"]["query"]=json!("ß");
    let out=case_prepare!(&provider,&v)?;assert_eq!(out.with_verified_bytes(&provider,5,section)??,section(&bytes)?.replace(">ß<",">SS<"));v["operation"]["query"]=json!("(?s:.+)");v["operation"]["mode"]=json!("lowercase");
    let expected=section(&bytes)?.replace("A&#x26;","a&#x26;").replace(">Σ<",">σ<").replace(">AΣ<",">aς<");let out=case_prepare!(&provider,&v)?;
    assert_eq!(out.with_verified_bytes(&provider,5,section)??,expected);assert!(out.receipt().stored.output.original_controls_and_reference_shells_preserved);Ok(())
}
#[test]
fn case_product_required_unknown_wrong_types_and_unimplemented_options_fail_before_reads()->TestResult{
    let bytes=raw("ab CD")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=case_request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();let mut bad=vec![b"null".to_vec(),b"[]".to_vec(),format!("{} {{}}",serde_json::to_string(&good)?).into_bytes()];
    for key in["schema_version","idempotency_key","project_id","document_id","base_revision","expected_head_generation","expected_source_package_sha256","plan_id","selector","operation"]{let mut v=good.clone();v.as_object_mut().ok_or("envelope")?.remove(key);bad.push(wire(&v)?);}
    for key in["kind","query","regex","case_sensitive","whole_word","max_matches","mode","case_policy","review_policy"]{let mut v=good.clone();v["operation"].as_object_mut().ok_or("operation")?.remove(key);bad.push(wire(&v)?);}
    for(key,value)in[("kind",json!("case_convert")),("mode",json!("titlecase")),("mode",json!("UPPERCASE")),("mode",json!(null)),("mode",json!(1)),("case_policy",json!("whole_document")),("case_policy",json!(null)),("regex",json!("true")),("query",json!("")),("query",json!("a".repeat(4097))),("max_matches",json!(0)),("max_matches",json!(10001)),("max_matches",json!(-1)),("max_matches",json!(1.5)),("locale",json!("tr")),("normalization",json!("nfc")),("run_policy",json!("flatten_runs")),("replacement",json!("X")),("direction",json!("backward"))]{let mut v=good.clone();v["operation"][key]=value;bad.push(wire(&v)?);}
    for pol in[json!({}),json!({"include_hidden_explanations":true}),json!({"include_hidden_explanations":true,"include_memo_bodies":true,"approved":true})]{let mut v=good.clone();v["operation"]["review_policy"]=pol;bad.push(wire(&v)?);}
    for(key,value)in[("source_graph",json!({})),("expected_head_generation",json!(0)),("expected_source_package_sha256",json!("A".repeat(64)))]{let mut v=good.clone();v[key]=value;bad.push(wire(&v)?);}
    for bytes in bad{assert!(matches!(CaseProduct::prepare_json(&provider,&bytes,Default::default(),Default::default(),4),Err(CE::Request)));}assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn case_product_invalid_filters_selectors_and_escaped_duplicate_keys_fail_before_reads()->TestResult{
    let bytes=raw("abc")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=case_request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();let mut bad=Vec::new();
    for filter in[json!([]),json!({}),json!({"kind":"declared","filter":{}}),json!({"kind":"definition","filter":{"bold":true}}),json!({"kind":"resolved","filter":{"bold":true}})]{let mut v=good.clone();v["operation"]["style_filter"]=filter;bad.push(wire(&v)?);}
    for selector in[json!([]),json!({"scope":"document"}),json!({"revision_id":good["base_revision"],"scope":"document","range":null}),json!({"revision_id":good["base_revision"],"scope":"section","section_ids":[]}),json!({"revision_id":rev::RevisionId::generate().public_id(),"scope":"document"})]{let mut v=good.clone();v["selector"]=selector;bad.push(wire(&v)?);}
    let text=serde_json::to_string(&good)?;for(from,to)in[("\"mode\":\"uppercase\"","\"mode\":\"uppercase\",\"mo\\u0064e\":\"lowercase\""),("\"regex\":true","\"regex\":true,\"regex\":false"),("\"scope\":\"document\"","\"scope\":\"document\",\"sco\\u0070e\":\"selection\"")]{let changed=text.replace(from,to);assert_ne!(changed,text);bad.push(changed.into_bytes());}
    for bytes in bad{assert!(matches!(CaseProduct::prepare_json(&provider,&bytes,Default::default(),Default::default(),4),Err(CE::Request)));}assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn case_product_exact_16k_and_optional_null_filter_bind_canonical_requests()->TestResult{
    let bytes=raw("abc")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=case_request(&s,&bytes)?;let out=case_prepare!(&provider,&good)?;let mut padded=wire(&good)?;padded.resize(16*1024,b' ');
    let other=CaseProduct::prepare_json(&provider,&padded,Default::default(),Default::default(),4)?;assert_ne!(out.receipt().raw_request_sha256,other.receipt().raw_request_sha256);assert_eq!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);padded.push(b' ');
    assert!(matches!(CaseProduct::prepare_json(&provider,&padded,Default::default(),Default::default(),4),Err(CE::Limit)));assert!(matches!(CaseProduct::prepare_json(&provider,b"",Default::default(),Default::default(),4),Err(CE::Limit)));
    let mut v=good;v["operation"]["style_filter"]=json!(null);let other=case_prepare!(&provider,&v)?;assert_ne!(out.receipt().raw_request_sha256,other.receipt().raw_request_sha256);assert_eq!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);Ok(())
}
#[test]
fn case_product_old_profiles_and_operations_are_mutually_rejected_before_reads()->TestResult{
    use hwpx_agent_cli::form_product_request::stored_literal_replacement::{StoredLiteralReplacementProductRequest as Literal,
        unicode::matches::{StoredUnicodeMatchProductRequest as MatchProduct,UnicodeMatchProductError as ME}};
    let bytes=raw("abc")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=case_request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();
    for schema in[CASE_SCHEMA,UNICODE_SCHEMA,"hwpx-agent.product-unicode-normalization-request/v2","hwpx-agent.product-literal-replacement-request/v1","hwpx-agent.product-regex-replacement-request/v1"]{let mut v=good.clone();v["schema_version"]=json!(schema);let b=wire(&v)?;
        assert!(matches!(UnicodeProduct::prepare_json(&provider,&b,Default::default(),Default::default(),4),Err(UE::Request)));assert!(matches!(MatchProduct::prepare_json(&provider,&b,Default::default(),Default::default(),4),Err(ME::Request)));assert!(Literal::prepare_json(&provider,&b,Default::default(),Default::default(),4).is_err());assert!(Product::prepare_json(&provider,&b,Default::default(),Default::default(),4).is_err());assert!(Discovery::prepare_json(&provider,&b,Default::default(),4).is_err());
        if schema!=CASE_SCHEMA{assert!(matches!(CaseProduct::prepare_json(&provider,&b,Default::default(),Default::default(),4),Err(CE::Request)));}}
    for mut old in[request(&s,&bytes)?,envelope(&s,&bytes)?]{old["schema_version"]=json!(CASE_SCHEMA);assert!(matches!(case_prepare!(&provider,&old),Err(CE::Request)));}assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn case_product_query_mode_filter_policy_max_key_plan_and_scope_bindings_are_distinct()->TestResult{
    let bytes=raw("ab CD")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut good=case_request(&s,&bytes)?;good["operation"]["query"]=json!("ab CD");let out=case_prepare!(&provider,&good)?;
    for(key,value)in[("idempotency_key",json!("OTHER-KEY")),("plan_id",json!("other-plan"))]{let mut v=good.clone();v[key]=value;let other=case_prepare!(&provider,&v)?;assert_ne!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);assert_ne!(out.receipt().scoped_request_sha256,other.receipt().scoped_request_sha256);assert_eq!(out.receipt().stored.output.output_package_sha256,other.receipt().stored.output.output_package_sha256);}
    for(key,value)in[("query",json!("ab|CD")),("regex",json!(false)),("case_sensitive",json!(false)),("whole_word",json!(true)),("max_matches",json!(101)),("mode",json!("lowercase")),("review_policy",policy(false,false)),("style_filter",json!({"kind":"declared","filter":{"run_character_property":0}}))]{let mut v=good.clone();v["operation"][key]=value;let other=case_prepare!(&provider,&v)?;assert_ne!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);assert_ne!(out.receipt().stored.output.request_sha256,other.receipt().stored.output.request_sha256);}
    let inv=inventory(&provider,&good)?;let mut v=good;v["selector"]["scope"]=json!("section");v["selector"]["section_ids"]=inv["inventory"]["section_ids"].clone();let other=case_prepare!(&provider,&v)?;assert_ne!(out.receipt().scoped_request_sha256,other.receipt().scoped_request_sha256);Ok(())
}
#[test]
fn case_product_current_write_and_five_foreign_scopes_deny_retained_delivery()->TestResult{
    let bytes=raw("abc")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=case_request(&s,&bytes)?;let reader=s.provider()?;assert!(case_prepare!(&reader,&v).is_err());let source=reader.import_actual_forms(s.head,4)?;
    assert!(matches!(source.prepare_case_candidate(&reader,query("abc"),Scope::Document,all(),None,CaseMode::Uppercase,CASE_POLICY,Default::default(),Default::default(),4),Err(CS::Permission)));
    let out=case_prepare!(&provider,&v)?;let called=Cell::new(false);assert!(out.with_verified_bytes(&reader,5,|_|called.set(true)).is_err());
    for variant in 0..5{let tenant=if variant==4{TenantId::new(Uuid::from_u128(997))?}else{s.reader.tenant_id()};let subject=if variant==3{SubjectDigest::from_authenticated_subject("foreign-case-conversion")?}else{s.reader.subject()};let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);let context=rev::RevisionRequestContext::new(tenant,subject);let project=if variant==2{rev::ProjectId::parse("prj_70000000000000000000000000000002")?}else{s.project};let branch=if variant==1{rev::BranchId::parse("brn_70000000000000000000000000000002")?}else{s.branch};
        let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&context,project,branch,DocumentId::parse(if variant==0{"foreign-document"}else{"actual-form-document"})?)?;assert!(out.verify(&other,5).is_err());assert!(out.with_verified_bytes(&other,5,|_|called.set(true)).is_err());}assert!(!called.get());Ok(())
}
#[test]
fn case_product_acl_regrant_quarantine_and_aead_protect_new_and_retained_candidates()->TestResult{
    for mode in 0..3{let bytes=raw("abc")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=case_request(&s,&bytes)?;let out=case_prepare!(&provider,&v)?;
        match mode{0=>{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;},1=>{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("CASE_TEST")?,5)?;},_=>s.blobs.tamper.store(true,Ordering::SeqCst)}
        let called=Cell::new(false);assert!(out.verify(&provider,6).is_err());assert!(out.with_verified_bytes(&provider,6,|_|called.set(true)).is_err());assert!(case_prepare!(&provider,&v).is_err());assert!(!called.get());
        if mode==0{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;out.verify(&provider,8)?;out.with_verified_bytes(&provider,8,|_|())?;}}Ok(())
}
#[test]
fn case_product_prepare_verify_and_delivery_final_head_races_block_consumers()->TestResult{
    for stage in 0..3{let bytes=raw("abc")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=case_request(&s,&bytes)?;let b=wire(&v)?;let out=case_prepare!(&provider,&v)?;
        let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,ContentDigest::of(b"case race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation"),ContentDigest::of(b"transaction"))?;
        let repo=rev::RevisionService::new(BoundaryRepo {inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});let bound=StoredFormProvider::bind(&s.artifacts,&repo,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
        match stage{0=>{CaseProduct::prepare_json(&bound,&b,Default::default(),Default::default(),5)?;},1=>{out.verify(&bound,5)?;},_=>{out.with_verified_bytes(&bound,5,|_|())?;}}
        let calls=repo.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);repo.repository().calls.store(0,Ordering::SeqCst);repo.repository().trigger.store(calls,Ordering::SeqCst);let called=Cell::new(false);
        match stage{0=>assert!(CaseProduct::prepare_json(&bound,&b,Default::default(),Default::default(),6).is_err()),1=>assert!(out.verify(&bound,6).is_err()),_=>assert!(out.with_verified_bytes(&bound,6,|_|called.set(true)).is_err())}assert!(!called.get());assert_eq!(repo.repository().calls.load(Ordering::SeqCst),calls);}Ok(())
}
#[test]
fn case_product_borrowed_owned_and_json_share_receipts_and_actual_output()->TestResult{
    let bytes=raw("abc")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=case_request(&s,&bytes)?;v["operation"]["query"]=json!("abc");v["operation"]["style_filter"]=json!({"kind":"declared","filter":{"run_character_property":0}});let out=case_prepare!(&provider,&v)?;let source=provider.import_actual_forms(s.head,4)?;
    let filter=Some(Filter::Declared(Declared {run_character_property:Some(0),..Default::default()}));let borrowed=source.prepare_case_candidate(&provider,query("abc"),Scope::Document,all(),filter.clone(),CaseMode::Uppercase,CASE_POLICY,Default::default(),Default::default(),4)?;
    assert_eq!(borrowed.verify(&provider,5)?,out.receipt().stored);drop(borrowed);let owned=source.into_case_candidate(&provider,query("abc"),Scope::Document,all(),filter,CaseMode::Uppercase,CASE_POLICY,Default::default(),Default::default(),4)?;
    assert_eq!(owned.verify(&provider,5)?,out.receipt().stored);assert_eq!(owned.with_verified_bytes(&provider,5,<[u8]>::to_vec)?,out.with_verified_bytes(&provider,5,<[u8]>::to_vec)?);assert!(matches!(owned.require_current_product_route(&provider,5),Err(CS::RouteUnqualified)));Ok(())
}
#[test]
fn case_product_wrong_source_head_revision_scope_and_index_reject_preparation()->TestResult{
    let bytes=raw("abc")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=case_request(&s,&bytes)?;
    for(key,value)in[("expected_head_generation",json!(s.head.generation()+1)),("expected_source_package_sha256",json!("0".repeat(64))),("document_id",json!("foreign-document")),("project_id",json!("prj_70000000000000000000000000000002")),("base_revision",json!(rev::RevisionId::generate().public_id()))]{let mut v=good.clone();v[key]=value;assert!(case_prepare!(&provider,&v).is_err());}
    let inv=inventory(&provider,&good)?;let mut v=good;v["selector"]["scope"]=json!("selection");v["selector"]["range"]=window(&inv,"body_and_notes",0,1)?;v["selector"]["range"]["index_sha256"]=json!("0".repeat(64));assert!(case_prepare!(&provider,&v).is_err());Ok(())
}
#[test]
fn case_product_no_match_no_change_zero_width_and_ambiguous_inverse_are_distinct()->TestResult{
    let bytes=raw("ABC abc")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=case_request(&s,&bytes)?;v["operation"]["query"]=json!("ABSENT");assert!(matches!(case_prepare!(&provider,&v),Err(CE::Stored(CS::Output(Compile::NoMatches)))));
    v["operation"]["query"]=json!("ABC");assert!(matches!(case_prepare!(&provider,&v),Err(CE::Stored(CS::Output(Compile::NoChange)))));v["operation"]["query"]=json!("^|abc");assert!(matches!(case_prepare!(&provider,&v),Err(CE::Stored(CS::Output(Compile::Selection)))));
    for(text,q)in[("à̕","à"),("&#x344;ABC","\u{308}")]{let bytes=raw(text)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=case_request(&s,&bytes)?;v["operation"]["query"]=json!(q);v["operation"]["regex"]=json!(false);assert!(matches!(case_prepare!(&provider,&v),Err(CE::Stored(CS::Output(Compile::Selection)))));}Ok(())
}
#[test]
fn case_product_matching_protected_noops_and_cache_are_blocked_before_success()->TestResult{
    let tracked=para(1,"ABC").replace("charPrIDRef='0'","charPrIDRef='0' charTcId='1'");let bytes=definition::package(&tracked)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=case_request(&s,&bytes)?;assert!(matches!(case_prepare!(&provider,&v),Err(CE::Stored(CS::Output(Compile::Protection)))));
    let bytes=definition::package(&fixture::body())?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=case_request(&s,&bytes)?;v["operation"]["query"]=json!("K");v["operation"]["mode"]=json!("lowercase");assert!(case_prepare!(&provider,&v)?.with_verified_bytes(&provider,5,section)??.contains("CACHE FROZEN"));
    v["operation"]["query"]=json!("FROZEN");v["operation"]["mode"]=json!("uppercase");assert!(matches!(case_prepare!(&provider,&v),Err(CE::Stored(CS::Output(Compile::FieldContent)))));Ok(())
}
#[test]
fn case_product_pattern_match_mapping_response_and_writer_caps_never_return_partial_candidates()->TestResult{
    let bytes=raw("abc abc")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=case_request(&s,&bytes)?;v["operation"]["query"]=json!("abc");v["operation"]["max_matches"]=json!(1);assert!(matches!(case_prepare!(&provider,&v),Err(CE::Stored(CS::Output(Compile::Search(Search::Limit))))));
    v["operation"]["max_matches"]=json!(100);v["operation"]["query"]=json!("(");assert!(matches!(case_prepare!(&provider,&v),Err(CE::Stored(CS::Output(Compile::Search(Search::Pattern))))));v["operation"]["query"]=json!("abc");
    assert!(CaseProduct::prepare_json(&provider,&wire(&v)?,SourceSearchLimits::new(Config {result_bytes:1,..Default::default()})?,Default::default(),4).is_err());assert!(matches!(CaseProduct::prepare_json(&provider,&wire(&v)?,Default::default(),WriterLimits::new(WriterLimitConfig {max_output_bytes:1,..Default::default()})?,4),Err(CE::Stored(CS::Output(Compile::Writer)))));
    let bytes=raw("ß")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=case_request(&s,&bytes)?;assert!(matches!(CaseProduct::prepare_json(&provider,&wire(&v)?,SourceSearchLimits::new(Config {decomposed_scalars:1,..Default::default()})?,Default::default(),4),Err(CE::Stored(CS::Output(Compile::Limit)))));Ok(())
}
#[test]
fn case_product_private_data_is_redacted_and_execution_stays_closed_without_source_or_head_mutation()->TestResult{
    let bytes=raw("PRIVATE-SOURCE abc")?;let original=ContentDigest::of(&bytes);let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=case_request(&s,&bytes)?;v["operation"]["query"]=json!("PRIVATE-SOURCE .+");let out=case_prepare!(&provider,&v)?;
    for text in[format!("{out:?}{:?}",out.receipt()),serde_json::to_string(out.receipt())?]{assert!(!text.contains("PRIVATE-SOURCE"));assert!(!text.contains("PRIVATE-UNICODE-KEY"));}
    assert!(matches!(out.require_current_product_route(&provider,5),Err(CE::RouteUnqualified)));assert!(!out.receipt().idempotency_key_claimed&&!out.receipt().full_case_native_cas_execution_publication_authority);assert_eq!(ContentDigest::of(&bytes),original);assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
}
#[test]
fn case_product_many_matches_and_long_words_share_one_span_guard_and_coalesced_patch()->TestResult{
    for(text,q,n,components)in[("abc ".repeat(128),"abc",128,128),("a".repeat(20000),".+",1,1)]{let bytes=raw(&text)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=case_request(&s,&bytes)?;v["operation"]["query"]=json!(q);v["operation"]["max_matches"]=json!(n);
        let out=case_prepare!(&provider,&v)?;assert_eq!(out.with_verified_bytes(&provider,5,section)??,section(&bytes)?.replace(&text,&text.to_uppercase()));let r=&out.receipt().stored.output;assert_eq!(r.search.search().result().matches().len(),n);assert_eq!(r.search.search().match_regions().len(),n);assert_eq!(r.changed_components,components);assert_eq!(r.changes.len(),1);assert_eq!(r.changed_scalar_ranges,components);let xml=hwpx_package::PreservingXmlDocument::parse(section(&bytes)?.as_bytes())?;assert_eq!(r.observed_protection_element_visits,xml.elements().len()*3);}Ok(())
}
