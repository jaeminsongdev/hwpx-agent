//! Reuse the original v1 fixture/discovery/race helpers; do not duplicate original test bodies.
use super::*;
use hwpx_agent_cli::form_product_request::stored_literal_replacement::regex::insertions::{StoredRegexInsertionProductRequest as Product2,
    REGEX_INSERTION_PRODUCT_REQUEST_SCHEMA as SCHEMA2};
use hwpx_package::document_import::search::replacement::atoms::regex::SourceRegexInsertionPolicy as Insert;
#[allow(dead_code)] #[path="../../../../hwpx-package/tests/support/search_definition_fixture.rs"] mod definition;
const INSERTION:&str="right_original_point_else_left_first_empty_text";
macro_rules! prepare2{($p:expr,$v:expr)=>{Product2::prepare_json($p,&wire($v)?,Default::default(),Default::default(),4)}}
fn request(s:&StoredFixture,raw:&[u8])->Result<Value,Box<dyn Error>> {let mut v=envelope(s,raw)?;v["schema_version"]=json!(SCHEMA2);
    v["operation"]["insertion_policy"]=json!(INSERTION);v["operation"]["query"]=json!("^");v["operation"]["replacement"]=json!("X");Ok(v)}
fn plain(text:&str)->Result<Vec<u8>,Box<dyn Error>> {fixture::with_body(&format!("<hp:p id='1'><hp:run><hp:t>{text}</hp:t></hp:run></hp:p>"))}
#[test]
fn insertion_product_discovery_builds_all_four_scopes_and_exact_clipped_empty_selection()->TestResult {
    let raw=fixture::with_body("<hp:p id='1'><hp:run><hp:t>AB</hp:t></hp:run></hp:p><hp:p id='2'><hp:run><hp:t>CD</hp:t></hp:run></hp:p>")?;
    let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=request(&s,&raw)?;let inv=inventory(&p,&v)?;
    let range=window(&inv,"body_and_notes",1,1)?;let node=inv["inventory"]["nodes"].as_array().ok_or("nodes")?.iter().find(|n|n["source_handle"]==range["start"]["paragraph_handle"]).ok_or("node")?;
    for(scope,count)in[("document",2),("section",2),("node_set",1),("selection",1)] {let mut v=v.clone();v["selector"]["scope"]=json!(scope);
        match scope {"section"=>v["selector"]["section_ids"]=inv["inventory"]["section_ids"].clone(),"node_set"=>v["selector"]["range"]=json!({"node_ids":[node["node_id"].clone()]}),
            "selection"=>v["selector"]["range"]=range.clone(),_=>{}}
        let out=prepare2!(&p,&v)?;drop(v);out.verify(&p,5)?;let expected=match scope {"document"|"section"=>section(&raw)?.replace(">AB<",">XAB<").replace(">CD<",">XCD<"),
            "node_set"=>section(&raw)?.replace(">AB<",">XAB<"),_=>section(&raw)?.replace(">AB<",">AXB<")};
        assert_eq!(out.with_verified_bytes(&p,5,section)??,expected);assert_eq!(out.receipt().stored.output.zero_width_matches,count);
    }Ok(())
}
#[test]
fn insertion_product_right_original_run_style_and_cross_run_hangul_nfc_are_preserved()->TestResult {
    let body="<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>A</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>B</hp:t></hp:run></hp:p>";
    let raw=definition::package(body)?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=request(&s,&raw)?;let inv=inventory(&p,&v)?;
    v["selector"]["scope"]=json!("selection");v["selector"]["range"]=window(&inv,"body_and_notes",1,1)?;
    assert_eq!(prepare2!(&p,&v)?.with_verified_bytes(&p,5,section)??,section(&raw)?.replace("<hp:t>B</hp:t>","<hp:t>XB</hp:t>"));
    let raw=fixture::with_body("<hp:p id='1'><hp:run><hp:t>Xᄀ</hp:t></hp:run><hp:run><hp:t>ᅡ</hp:t></hp:run><hp:run><hp:t>ᆨY</hp:t></hp:run></hp:p>")?;
    let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=request(&s,&raw)?;v["operation"]["query"]=json!("(?:)");
    assert_eq!(prepare2!(&p,&v)?.with_verified_bytes(&p,5,section)??,section(&raw)?.replace("Xᄀ","XXXᄀ").replace("ᆨY","ᆨXYX"));Ok(())
}
#[test]
fn insertion_product_control_boundaries_and_empty_text_shells_keep_original_bytes()->TestResult {
    let old=format!("{TAB}<hp:lineBreak> </hp:lineBreak>");let raw=plain(&old)?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=request(&s,&raw)?;
    v["operation"]["query"]=json!("(?:)");v["operation"]["replacement"]=json!("<&");
    assert_eq!(prepare2!(&p,&v)?.with_verified_bytes(&p,5,section)??,section(&raw)?.replace(&old,&format!("&lt;&amp;{TAB}&lt;&amp;<hp:lineBreak> </hp:lineBreak>&lt;&amp;")));
    for(old,new)in[("<hp:t></hp:t>","<hp:t>X</hp:t>"),("<hp:t xmlns:k='urn:keep' />","<hp:t xmlns:k='urn:keep' >X</hp:t>")] {
        let raw=fixture::with_body(&format!("<hp:p id='1'><hp:run>{old}<hp:t/></hp:run></hp:p>"))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=request(&s,&raw)?;
        assert_eq!(prepare2!(&p,&v)?.with_verified_bytes(&p,5,section)??,section(&raw)?.replacen(old,new,1));
    }Ok(())
}
#[test]
fn insertion_product_ambiguous_nfc_and_absent_original_owner_reject_without_partial_output()->TestResult {
    for body in["<hp:p id='1'><hp:run><hp:t>a&#x315;&#x300;</hp:t></hp:run></hp:p>","<hp:p id='1'><hp:run><hp:t>&#x344;</hp:t></hp:run></hp:p>","<hp:p id='1'><hp:run/></hp:p>"] {
        let raw=fixture::with_body(body)?;let original=ContentDigest::of(&raw);let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=request(&s,&raw)?;v["operation"]["query"]=json!("(?:)");
        assert!(matches!(prepare2!(&p,&v),Err(E::Stored(StoredError::Output(CoreError::Compile(Compile::Selection))))));assert_eq!(ContentDigest::of(&raw),original);
        assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);
    }Ok(())
}
#[test]
fn insertion_product_review_policies_exclude_before_caps_and_keep_memo_cache_frozen()->TestResult {
    let raw=fixture::package()?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=request(&s,&raw)?;let inv=inventory(&p,&good)?;
    let ids:Vec<_>=["hidden_explanation","memo_body"].into_iter().map(|r|->Result<Value,Box<dyn Error>> {let range=window(&inv,r,0,0)?;
        Ok(inv["inventory"]["nodes"].as_array().ok_or("nodes")?.iter().find(|n|n["source_handle"]==range["start"]["paragraph_handle"]).ok_or("node")?["node_id"].clone())}).collect::<Result<_,_>>()?;
    let mut hashes=BTreeSet::new();for(h,m,count)in[(false,false,0),(true,false,1),(false,true,1),(true,true,2)] {
        let mut v=good.clone();v["selector"]["scope"]=json!("node_set");v["selector"]["range"]=json!({"node_ids":ids});v["operation"]["review_policy"]=policy(h,m);v["operation"]["max_replacements"]=json!(count.max(1));
        let out=prepare2!(&p,&v);if count==0{assert!(matches!(out,Err(E::Stored(StoredError::Output(CoreError::Compile(Compile::NoMatches))))));continue;}
        let out=out?;hashes.insert(out.receipt().stored.output.output.search_request_sha256);let mut expected=section(&raw)?;
        if h{expected=expected.replace("HIDDEN K K","XHIDDEN K K");}if m{expected=expected.replace("MEMO K K","XMEMO K K");}
        assert_eq!(out.with_verified_bytes(&p,5,section)??,expected);assert_eq!(out.receipt().stored.output.zero_width_matches,count);
    }assert_eq!(hashes.len(),3);Ok(())
}
#[test]
fn insertion_product_required_policy_strict_shape_and_decoded_duplicates_fail_before_source_reads()->TestResult {
    let raw=plain("AB")?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=request(&s,&raw)?;let before=s.metadata.audit_events()?.len();let mut bad=vec![b"null".to_vec(),b"[]".to_vec()];
    for key in["schema_version","idempotency_key","project_id","document_id","base_revision","expected_head_generation","expected_source_package_sha256","plan_id","selector","operation"] {
        let mut v=good.clone();v.as_object_mut().ok_or("envelope")?.remove(key);bad.push(wire(&v)?);
    }
    for key in["kind","query","replacement","regex","case_sensitive","whole_word","max_replacements","run_policy","review_policy","insertion_policy"] {
        let mut v=good.clone();v["operation"].as_object_mut().ok_or("operation")?.remove(key);bad.push(wire(&v)?);
    }
    for(key,value)in[("insertion_policy",json!(null)),("insertion_policy",json!([])),("insertion_policy",json!({})),("insertion_policy",json!(true)),("insertion_policy",json!("left_run")),
        ("query",json!("")),("query",json!("Q".repeat(4097))),("regex",json!(false)),("replacement",json!("$")),("replacement",json!("\n")),("kind",json!("replace_literal")),
        ("max_replacements",json!(0)),("max_replacements",json!(10001)),("style_filter",json!({})),("include_hidden",json!(true)),("preview_only",json!(false))] {
        let mut v=good.clone();v["operation"][key]=value;bad.push(wire(&v)?);
    }
    for(key,value)in[("schema_version",json!(SCHEMA)),("source_graph",json!({})),("approved",json!(true)),("expected_head_generation",json!(0)),("expected_source_package_sha256",json!("A".repeat(64)))] {
        let mut v=good.clone();v[key]=value;bad.push(wire(&v)?);
    }
    let mut v=good.clone();v["selector"]["revision_id"]=json!(rev::RevisionId::generate().public_id());bad.push(wire(&v)?);
    let text=serde_json::to_string(&good)?;for(from,to)in[("\"insertion_policy\":","\"insertion_policy\":\"left_run\",\"insertion_polic\\u0079\":"),("\"regex\":true","\"regex\":true,\"reg\\u0065x\":false")] {
        let bytes=text.replace(from,to);assert_ne!(bytes,text);bad.push(bytes.into_bytes());
    }
    for bytes in bad {assert!(matches!(Product2::prepare_json(&p,&bytes,Default::default(),Default::default(),4),Err(E::Request)));}
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn insertion_product_original_regex_and_literal_schemas_reject_policy_and_v2_before_reads()->TestResult {
    use hwpx_agent_cli::form_product_request::stored_literal_replacement::{StoredLiteralReplacementProductRequest as L1,atoms::StoredLiteralTextAtomProductRequest as L2,
        review::StoredReviewLiteralProductRequest as L3,selector::StoredSelectorLiteralProductRequest as L4};
    let raw=plain("AB")?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=request(&s,&raw)?;let before=s.metadata.audit_events()?.len();
    for schema in[SCHEMA,SCHEMA2,"hwpx-agent.product-literal-replacement-request/v1","hwpx-agent.product-literal-replacement-request/v2","hwpx-agent.product-literal-replacement-request/v3","hwpx-agent.product-literal-replacement-request/v4"] {
        let mut v=good.clone();v["schema_version"]=json!(schema);let bytes=wire(&v)?;
        assert!(matches!(Product::prepare_json(&p,&bytes,Default::default(),Default::default(),4),Err(E::Request)));
        assert!(matches!(L1::prepare_json(&p,&bytes,Default::default(),Default::default(),4),Err(LE::Request)));assert!(matches!(L2::prepare_json(&p,&bytes,Default::default(),Default::default(),4),Err(LE::Request)));
        assert!(matches!(L3::prepare_json(&p,&bytes,Default::default(),Default::default(),4),Err(LE::Request)));assert!(matches!(L4::prepare_json(&p,&bytes,Default::default(),Default::default(),4),Err(LE::Request)));
    }assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn insertion_product_exact_16k_and_versioned_policy_canonical_key_plan_bindings_are_distinct()->TestResult {
    let raw=plain("AB")?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=request(&s,&raw)?;let out=prepare2!(&p,&v)?;
    let mut bytes=wire(&v)?;bytes.resize(16*1024,b' ');let padded=Product2::prepare_json(&p,&bytes,Default::default(),Default::default(),4)?;
    assert_ne!(out.receipt().raw_request_sha256,padded.receipt().raw_request_sha256);assert_eq!(out.receipt().canonical_request_sha256,padded.receipt().canonical_request_sha256);
    bytes.push(b' ');assert!(matches!(Product2::prepare_json(&p,&bytes,Default::default(),Default::default(),4),Err(E::Limit)));assert!(matches!(Product2::prepare_json(&p,b"",Default::default(),Default::default(),4),Err(E::Limit)));
    for(key,value)in[("idempotency_key",json!("OTHER-KEY")),("plan_id",json!("other-plan"))] {let mut other=v.clone();other[key]=value;let other=prepare2!(&p,&other)?;
        assert_ne!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);assert_ne!(out.receipt().scoped_request_sha256,other.receipt().scoped_request_sha256);
        assert_eq!(out.receipt().stored.output.output.output.output_package_sha256,other.receipt().stored.output.output.output.output_package_sha256);
    }Ok(())
}
#[test]
fn insertion_product_write_current_source_head_and_five_foreign_scopes_reject_output()->TestResult {
    let raw=plain("AB")?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=request(&s,&raw)?;let reader=s.provider()?;
    assert!(prepare2!(&reader,&v).is_err());let out=prepare2!(&p,&v)?;let called=Cell::new(false);assert!(out.with_verified_bytes(&reader,5,|_|called.set(true)).is_err());
    let source=reader.import_actual_forms(s.head,4)?;assert!(matches!(source.prepare_review_selector_regex_insertion_candidate(&reader,query("^"),Scope::Document,all(),"X",Run::FirstOriginalRunRetainAllRuns,
        Insert::RightOriginalPointElseLeftFirstEmptyText,Default::default(),Default::default(),4),Err(StoredError::Permission)));
    for variant in 0..5 {let tenant=if variant==4{TenantId::new(Uuid::from_u128(997))?}else{s.reader.tenant_id()};let subject=if variant==3{SubjectDigest::from_authenticated_subject("foreign-insertion")?}else{s.reader.subject()};
        let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);let context=rev::RevisionRequestContext::new(tenant,subject);
        let project=if variant==2{rev::ProjectId::parse("prj_70000000000000000000000000000002")?}else{s.project};let branch=if variant==1{rev::BranchId::parse("brn_70000000000000000000000000000002")?}else{s.branch};
        let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&context,project,branch,DocumentId::parse(if variant==0{"foreign-document"}else{"actual-form-document"})?)?;
        assert!(out.verify(&other,5).is_err());assert!(out.with_verified_bytes(&other,5,|_|called.set(true)).is_err());
    }
    for(key,value)in[("expected_head_generation",json!(s.head.generation()+1)),("expected_source_package_sha256",json!("0".repeat(64))),("document_id",json!("foreign-document")),("project_id",json!("prj_70000000000000000000000000000002"))] {
        let mut bad=v.clone();bad[key]=value;assert!(prepare2!(&p,&bad).is_err());
    }assert!(!called.get());Ok(())
}
#[test]
fn insertion_product_acl_regrant_quarantine_aead_protect_every_retained_and_new_output()->TestResult {
    for mode in 0..3 {let raw=plain("AB")?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=request(&s,&raw)?;let out=prepare2!(&p,&v)?;
        match mode {0=>{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;},1=>{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("INSERTION_TEST")?,5)?;},_=>s.blobs.tamper.store(true,Ordering::SeqCst)}
        let called=Cell::new(false);assert!(out.verify(&p,6).is_err());assert!(out.with_verified_bytes(&p,6,|_|called.set(true)).is_err());assert!(prepare2!(&p,&v).is_err());assert!(!called.get());
        if mode==0{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;out.verify(&p,8)?;out.with_verified_bytes(&p,8,|_|())?;}
    }Ok(())
}
#[test]
fn insertion_product_prepare_verify_and_delivery_final_head_races_block_consumers()->TestResult {
    for stage in 0..3 {let raw=plain("AB")?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=request(&s,&raw)?;let bytes=wire(&v)?;let out=prepare2!(&p,&v)?;
        let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,
            ContentDigest::of(b"insertion race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation"),ContentDigest::of(b"transaction"))?;
        let b=rev::RevisionService::new(BoundaryRepo {inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
        let bound=StoredFormProvider::bind(&s.artifacts,&b,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
        match stage {0=>{Product2::prepare_json(&bound,&bytes,Default::default(),Default::default(),5)?;},1=>{out.verify(&bound,5)?;},_=>{out.with_verified_bytes(&bound,5,|_|())?;}}
        let calls=b.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);b.repository().calls.store(0,Ordering::SeqCst);b.repository().trigger.store(calls,Ordering::SeqCst);let called=Cell::new(false);
        match stage {0=>assert!(Product2::prepare_json(&bound,&bytes,Default::default(),Default::default(),6).is_err()),1=>assert!(out.verify(&bound,6).is_err()),_=>assert!(out.with_verified_bytes(&bound,6,|_|called.set(true)).is_err())}
        assert!(!called.get());assert_eq!(b.repository().calls.load(Ordering::SeqCst),calls);
    }Ok(())
}
#[test]
fn insertion_product_borrowed_owned_and_json_outputs_bind_same_policy_and_exact_boundary_digest()->TestResult {
    let raw=plain("AB")?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=request(&s,&raw)?;let out=prepare2!(&p,&v)?;let source=p.import_actual_forms(s.head,4)?;
    let borrowed=source.prepare_review_selector_regex_insertion_candidate(&p,query("^"),Scope::Document,all(),"X",Run::FirstOriginalRunRetainAllRuns,Insert::RightOriginalPointElseLeftFirstEmptyText,Default::default(),Default::default(),4)?;
    assert_eq!(borrowed.verify(&p,5)?,out.receipt().stored);drop(borrowed);
    let owned=source.into_review_selector_regex_insertion_candidate(&p,query("^"),Scope::Document,all(),"X",Run::FirstOriginalRunRetainAllRuns,Insert::RightOriginalPointElseLeftFirstEmptyText,Default::default(),Default::default(),4)?;
    assert_eq!(owned.verify(&p,5)?,out.receipt().stored);assert_eq!(owned.with_verified_bytes(&p,5,<[u8]>::to_vec)?,out.with_verified_bytes(&p,5,<[u8]>::to_vec)?);
    assert!(matches!(owned.require_current_product_route(&p,5),Err(StoredError::RouteUnqualified)));Ok(())
}
#[test]
fn insertion_product_equal_coordinates_different_selectors_keep_boundary_but_not_scope_or_request_digest()->TestResult {
    let raw=plain("AB")?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=request(&s,&raw)?;let a=prepare2!(&p,&v)?;let inv=inventory(&p,&v)?;
    let mut selected=v.clone();selected["selector"]["scope"]=json!("selection");selected["selector"]["range"]=window(&inv,"body_and_notes",0,0)?;let b=prepare2!(&p,&selected)?;
    assert_eq!(a.receipt().stored.output.insertion_boundaries_sha256,b.receipt().stored.output.insertion_boundaries_sha256);
    assert_ne!(a.receipt().stored.output.output.selector.scope_sha256,b.receipt().stored.output.output.selector.scope_sha256);
    assert_ne!(a.receipt().canonical_request_sha256,b.receipt().canonical_request_sha256);assert_eq!(a.with_verified_bytes(&p,5,<[u8]>::to_vec)?,b.with_verified_bytes(&p,5,<[u8]>::to_vec)?);Ok(())
}
#[test]
fn insertion_product_template_and_expansion_hashes_remain_distinct_for_identical_insertions()->TestResult {
    let raw=plain("AB")?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=request(&s,&raw)?;v["operation"]["query"]=json!("^()");
    let a=prepare2!(&p,&v)?;v["operation"]["replacement"]=json!("${1}X");let b=prepare2!(&p,&v)?;
    assert_eq!(a.receipt().stored.output.output.expansion_sha256,b.receipt().stored.output.output.expansion_sha256);
    assert_ne!(a.receipt().stored.output.output.template_sha256,b.receipt().stored.output.output.template_sha256);assert_ne!(a.receipt().canonical_request_sha256,b.receipt().canonical_request_sha256);
    assert_eq!(a.with_verified_bytes(&p,5,<[u8]>::to_vec)?,b.with_verified_bytes(&p,5,<[u8]>::to_vec)?);Ok(())
}
#[test]
fn insertion_product_cache_control_noop_protection_and_match_writer_output_limits_reject_entire_request()->TestResult {
    for(raw,pattern,value)in[(fixture::package()?,"^","X"),(plain(&format!("A{TAB}B"))?,r"\t","X"),(plain("AB")?,"^",""),
        (assembly::package(&table::table(300).replace("lock='0'","lock='1'"))?,"^","X")] {
        let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=request(&s,&raw)?;v["operation"]["query"]=json!(pattern);v["operation"]["replacement"]=json!(value);assert!(prepare2!(&p,&v).is_err());
    }
    let raw=plain("AB")?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=request(&s,&raw)?;v["operation"]["query"]=json!("(?:)");v["operation"]["max_replacements"]=json!(1);assert!(prepare2!(&p,&v).is_err());
    v["operation"]["max_replacements"]=json!(100);assert!(Product2::prepare_json(&p,&wire(&v)?,SourceSearchLimits::new(Config {result_bytes:1,..Default::default()})?,Default::default(),4).is_err());
    assert!(Product2::prepare_json(&p,&wire(&v)?,Default::default(),WriterLimits::new(WriterLimitConfig {max_output_bytes:1})?,4).is_err());
    for(pattern,template)in[("(","X"),("^","${missing}")] {v["operation"]["query"]=json!(pattern);v["operation"]["replacement"]=json!(template);assert!(prepare2!(&p,&v).is_err());}Ok(())
}
#[test]
fn insertion_product_many_control_edges_and_privacy_preserve_original_source_head_and_ingest_count()->TestResult {
    let old=TAB.repeat(256);let raw=plain(&old)?;let original=ContentDigest::of(&raw);let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=request(&s,&raw)?;
    v["operation"]["query"]=json!("(?:)");v["operation"]["max_replacements"]=json!(257);let out=prepare2!(&p,&v)?;
    assert_eq!(out.with_verified_bytes(&p,5,section)??,section(&raw)?.replace(&old,&format!("X{}",format!("{TAB}X").repeat(256))));assert_eq!(out.receipt().stored.output.zero_width_matches,257);
    let xml=hwpx_package::PreservingXmlDocument::parse(section(&raw)?.as_bytes())?;assert_eq!(out.receipt().stored.output.output.output.observed_protection_element_visits,xml.elements().len()*2);
    assert!(!format!("{out:?}{:?}{}",out.receipt(),serde_json::to_string(out.receipt())?).contains("PRIVATE"));assert!(matches!(out.require_current_product_route(&p,5),Err(E::RouteUnqualified)));
    assert_eq!(ContentDigest::of(&raw),original);assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
}
#[test]
fn insertion_product_nonempty_captures_remain_equivalent_to_v1_without_promoting_v1_zero_width()->TestResult {
    let raw=plain("A12 B3")?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=request(&s,&raw)?;
    v["operation"]["query"]=json!("([AB])([0-9]+)");v["operation"]["replacement"]=json!("$2$1");let v2=prepare2!(&p,&v)?;
    v["schema_version"]=json!(SCHEMA);v["operation"].as_object_mut().ok_or("operation")?.remove("insertion_policy");let v1=prepare!(&p,&v)?;
    assert_eq!(v2.receipt().stored.output.zero_width_matches,0);assert_eq!(v1.with_verified_bytes(&p,5,<[u8]>::to_vec)?,v2.with_verified_bytes(&p,5,<[u8]>::to_vec)?);
    assert_ne!(v1.receipt().canonical_request_sha256,v2.receipt().canonical_request_sha256);v["operation"]["query"]=json!("^");assert!(prepare!(&p,&v).is_err());Ok(())
}
#[test]
fn insertion_product_empty_capture_work_budget_and_zero_byte_noop_remain_bounded()->TestResult {
    let limits=SourceSearchLimits::new(Config {decomposed_scalars:512,..Default::default()})?;
    for(count,pass)in[(15,true),(16,false)] {let raw=plain(&"b".repeat(count))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=request(&s,&raw)?;
        v["operation"]["query"]=json!("(a)?b");v["operation"]["replacement"]=json!("${1}".repeat(32));let out=Product2::prepare_json(&p,&wire(&v)?,limits,Default::default(),4);
        if pass {let out=out?;assert_eq!(out.receipt().stored.output.output.expansion_work_units,512);assert_eq!(out.receipt().stored.output.output.expanded_replacement_bytes,0);out.verify(&p,5)?;}
        else {assert!(matches!(out,Err(E::Stored(StoredError::Output(CoreError::Limit)))));}
    }Ok(())
}
