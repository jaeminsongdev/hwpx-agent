//! Selected-scope normalization through current stored access and strict JSON, not a full transaction.
use super::*;
use hwpx_agent_cli::form_product_request::stored_literal_replacement::unicode::{StoredUnicodeProductRequest as UnicodeProduct,
    UnicodeProductError as UE,UNICODE_PRODUCT_REQUEST_SCHEMA as UNICODE_SCHEMA};
use hwpx_agent_cli::form_stored_provider::actual_import::literal_search_output::unicode::StoredUnicodeError as US;
use hwpx_package::document_import::search::replacement::atoms::unicode::SourceUnicodeNormalizationForm as Form;
#[allow(dead_code)] #[path="../../../../hwpx-package/tests/support/search_definition_fixture.rs"] mod definition;
macro_rules! unicode_prepare{($p:expr,$v:expr)=>{UnicodeProduct::prepare_json($p,&wire($v)?,Default::default(),Default::default(),4)}}
fn para(id:u32,text:&str)->String{format!("<hp:p id='{id}' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'><hp:t charStyleIDRef='0'>{text}</hp:t></hp:run></hp:p>")}
fn raw(text:&str)->Result<Vec<u8>,Box<dyn Error>>{definition::package(&para(1,text))}
fn request(s:&StoredFixture,raw:&[u8])->Result<Value,Box<dyn Error>>{let mut v=envelope(s,raw)?;v["schema_version"]=json!(UNICODE_SCHEMA);v["idempotency_key"]=json!("PRIVATE-UNICODE-KEY");
    v["operation"]=json!({"kind":"normalize_unicode_scope","form":"nfc","run_policy":"first_original_run_retain_all_runs","review_policy":policy(true,true)});Ok(v)}
#[test]
fn unicode_product_four_forms_change_actual_source_and_owned_request_can_be_dropped()->TestResult {
    let bytes=raw("à각①ﬃＡ")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for(form,expected)in[("nfc","à각①ﬃＡ"),("nfd","à각①ﬃＡ"),("nfkc","à각1ffiA"),("nfkd","à각1ffiA")] {
        let mut v=request(&s,&bytes)?;v["operation"]["form"]=json!(form);let out=unicode_prepare!(&provider,&v)?;drop(v);out.verify(&provider,5)?;
        assert_eq!(out.with_verified_bytes(&provider,5,section)??,section(&bytes)?.replace("à각①ﬃＡ",expected));assert_eq!(out.receipt().capability_id,"search.normalize_unicode");
    }Ok(())
}
#[test]
fn unicode_product_discovery_supplies_four_exact_scopes_without_caller_side_form_import()->TestResult {
    let bytes=definition::package(&(para(1,"àZ")+&para(2,"éZ")))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let good=request(&s,&bytes)?;let inv=inventory(&provider,&good)?;let range=window(&inv,"body_and_notes",0,1)?;
    let node=inv["inventory"]["nodes"].as_array().ok_or("nodes")?.iter().find(|n|n["source_handle"]==range["start"]["paragraph_handle"]).ok_or("node")?;
    for(scope,n)in[("document",2),("section",2),("node_set",1),("selection",1)]{let mut v=good.clone();v["selector"]["scope"]=json!(scope);
        match scope{"section"=>v["selector"]["section_ids"]=inv["inventory"]["section_ids"].clone(),"node_set"=>v["selector"]["range"]=json!({"node_ids":[node["node_id"].clone()]}),"selection"=>v["selector"]["range"]=range.clone(),_=>{}}
        let out=unicode_prepare!(&provider,&v)?;assert_eq!(out.receipt().stored.output.changed_components,n);let after=out.with_verified_bytes(&provider,5,section)??;
        assert!(after.contains("àZ"));assert_eq!(after.contains("éZ"),n==1);
    }Ok(())
}
#[test]
fn unicode_product_cross_run_hangul_retains_styles_shells_and_unchanged_entities()->TestResult {
    let body="<hp:p id='1'><hp:run charPrIDRef='0'><hp:t charStyleIDRef='0'>&#x1F600;Xᄀ</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t charStyleIDRef='1'>ᅡ</hp:t></hp:run><hp:run charPrIDRef='0'><hp:t>ᆨY&#38;</hp:t></hp:run></hp:p>";
    let bytes=definition::package(body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=request(&s,&bytes)?;let out=unicode_prepare!(&provider,&v)?;
    assert_eq!(out.with_verified_bytes(&provider,5,section)??,section(&bytes)?.replace('ᄀ',"각").replace(['ᅡ','ᆨ'],""));assert_eq!(out.receipt().stored.output.changed_scalar_ranges,3);Ok(())
}
#[test]
fn unicode_product_tabs_linebreaks_and_bookmarks_are_normalization_barriers()->TestResult {
    let body=para(1,&format!("a{TAB}̀à<hp:lineBreak> </hp:lineBreak>ᄀ<hp:lineBreak/>ᅡ</hp:t><hp:ctrl><hp:bookmark name='KEEP'/></hp:ctrl><hp:t>à"));
    let bytes=definition::package(&body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=request(&s,&bytes)?;let out=unicode_prepare!(&provider,&v)?;
    assert_eq!(out.with_verified_bytes(&provider,5,section)??,section(&bytes)?.replace("à","à"));assert!(out.receipt().stored.output.original_controls_and_all_reference_shells_preserved);Ok(())
}
#[test]
fn unicode_product_nfd_reorders_only_changed_marks_and_keeps_base_style()->TestResult {
    let body="<hp:p id='1'><hp:run charPrIDRef='1'><hp:t>a</hp:t></hp:run><hp:run charPrIDRef='0'><hp:t>̕</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>̀Z</hp:t></hp:run></hp:p>";
    let bytes=definition::package(body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=request(&s,&bytes)?;v["operation"]["form"]=json!("nfd");
    let out=unicode_prepare!(&provider,&v)?;assert_eq!(out.with_verified_bytes(&provider,5,section)??,section(&bytes)?.replace(">̕<",">̀̕<").replace(">̀Z<",">Z<"));Ok(())
}
#[test]
fn unicode_product_review_policies_exclude_original_nodes_and_preserve_unselected_cache()->TestResult {
    let bytes=definition::package(&(para(30,"à")+&fixture::body().replace("K K","à")))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let good=request(&s,&bytes)?;let inv=inventory(&provider,&good)?;let blocks=inv["inventory"]["blocks"].as_array().ok_or("blocks")?;let regions=inv["block_regions"].as_array().ok_or("regions")?;
    let nodes=inv["inventory"]["nodes"].as_array().ok_or("nodes")?;let ids:Vec<Value>=blocks.iter().zip(regions).filter(|(b,r)|b["block_index"]==0||*r!=&json!("body_and_notes"))
        .map(|(b,_)|nodes.iter().find(|n|n["source_handle"]==b["paragraph_handle"]).map(|n|n["node_id"].clone()).ok_or("node")).collect::<Result<_,_>>()?;
    for(h,m,n)in[(false,false,1),(true,false,2),(false,true,2),(true,true,3)]{let mut v=good.clone();v["selector"]["scope"]=json!("node_set");v["selector"]["range"]=json!({"node_ids":ids});v["operation"]["review_policy"]=policy(h,m);
        let out=unicode_prepare!(&provider,&v)?;let after=out.with_verified_bytes(&provider,5,section)??;assert_eq!(after.matches('à').count(),n);assert!(after.contains("CACHE FROZEN"));
        assert_eq!(out.receipt().stored.output.excluded_hidden_paragraphs,usize::from(!h));assert_eq!(out.receipt().stored.output.excluded_memo_paragraphs,usize::from(!m));
    }Ok(())
}
#[test]
fn unicode_product_missing_unknown_wrong_types_and_unimplemented_options_fail_before_source_reads()->TestResult {
    let bytes=raw("à")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();let mut bad=vec![b"null".to_vec(),b"[]".to_vec(),format!("{} {{}}",serde_json::to_string(&good)?).into_bytes()];
    for key in["schema_version","idempotency_key","project_id","document_id","base_revision","expected_head_generation","expected_source_package_sha256","plan_id","selector","operation"]{let mut v=good.clone();v.as_object_mut().ok_or("envelope")?.remove(key);bad.push(wire(&v)?);}
    for key in["kind","form","run_policy","review_policy"]{let mut v=good.clone();v["operation"].as_object_mut().ok_or("operation")?.remove(key);bad.push(wire(&v)?);}
    for(key,value)in[("kind",json!("normalize_unicode")),("form",json!("NFC")),("form",json!(null)),("form",json!(1)),("run_policy",json!("flatten_runs")),("query",json!("a")),("regex",json!(false)),("style_filter",json!({})),("replacement",json!("X")),("approved",json!(true))]{let mut v=good.clone();v["operation"][key]=value;bad.push(wire(&v)?);}
    for value in[json!(null),json!([]),json!({}),json!({"include_hidden_explanations":true}),json!({"include_hidden_explanations":true,"include_memo_bodies":true,"approved":true})]{let mut v=good.clone();v["operation"]["review_policy"]=value;bad.push(wire(&v)?);}
    for selector in[json!([]),json!({"scope":"document"}),json!({"revision_id":good["base_revision"],"scope":"document","range":null}),json!({"revision_id":good["base_revision"],"scope":"section","section_ids":[]}),json!({"revision_id":rev::RevisionId::generate().public_id(),"scope":"document"})]{let mut v=good.clone();v["selector"]=selector;bad.push(wire(&v)?);}
    for(key,value)in[("scope",json!({})),("source_graph",json!({})),("approved",json!(true)),("expected_head_generation",json!(0)),("expected_source_package_sha256",json!("A".repeat(64)))]{let mut v=good.clone();v[key]=value;bad.push(wire(&v)?);}
    for raw in bad{assert!(matches!(UnicodeProduct::prepare_json(&provider,&raw,Default::default(),Default::default(),4),Err(UE::Request)));}assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn unicode_product_deep_duplicate_and_escaped_duplicate_keys_are_rejected_before_reads()->TestResult {
    let bytes=raw("à")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=request(&s,&bytes)?;let text=serde_json::to_string(&v)?;let before=s.metadata.audit_events()?.len();
    for(from,to)in[("\"form\":\"nfc\"","\"form\":\"nfc\",\"fo\\u0072m\":\"nfkd\""),("\"scope\":\"document\"","\"scope\":\"document\",\"sco\\u0070e\":\"selection\""),
        ("\"include_memo_bodies\":true","\"include_memo_bodies\":true,\"include_memo_bodies\":false")]{let bad=text.replace(from,to);assert_ne!(bad,text);assert!(matches!(UnicodeProduct::prepare_json(&provider,bad.as_bytes(),Default::default(),Default::default(),4),Err(UE::Request)));}
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn unicode_product_exact_16k_and_raw_canonical_scoped_key_plan_form_policy_bindings_are_distinct()->TestResult {
    let bytes=raw("à①")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=request(&s,&bytes)?;let out=unicode_prepare!(&provider,&v)?;
    let mut padded=wire(&v)?;padded.resize(16*1024,b' ');let other=UnicodeProduct::prepare_json(&provider,&padded,Default::default(),Default::default(),4)?;
    assert_ne!(out.receipt().raw_request_sha256,other.receipt().raw_request_sha256);assert_eq!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);padded.push(b' ');
    assert!(matches!(UnicodeProduct::prepare_json(&provider,&padded,Default::default(),Default::default(),4),Err(UE::Limit)));assert!(matches!(UnicodeProduct::prepare_json(&provider,b"",Default::default(),Default::default(),4),Err(UE::Limit)));
    for(key,value)in[("idempotency_key",json!("OTHER-KEY")),("plan_id",json!("other-plan"))]{let mut v=v.clone();v[key]=value;let other=unicode_prepare!(&provider,&v)?;
        assert_ne!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);assert_ne!(out.receipt().scoped_request_sha256,other.receipt().scoped_request_sha256);assert_eq!(out.receipt().stored.output.output_package_sha256,other.receipt().stored.output.output_package_sha256);}
    for(key,value)in[("form",json!("nfkc")),("review_policy",policy(false,false))]{let mut v=v.clone();v["operation"][key]=value;let other=unicode_prepare!(&provider,&v)?;
        assert_ne!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);assert_ne!(out.receipt().stored.output.request_sha256,other.receipt().stored.output.request_sha256);}
    Ok(())
}
#[test]
fn unicode_product_legacy_literal_regex_style_and_search_schemas_reject_new_operation()->TestResult {
    use hwpx_agent_cli::form_product_request::stored_literal_replacement::{StoredLiteralReplacementProductRequest as L1,atoms::StoredLiteralTextAtomProductRequest as L2,
        review::StoredReviewLiteralProductRequest as L3,selector::StoredSelectorLiteralProductRequest as L4,regex::insertions::StoredRegexInsertionProductRequest as R2,
        styles::StoredCharacterStyleProductRequest as Style,text_styles::StoredTextStyleProductRequest as Text,paragraph_styles::StoredParagraphStyleProductRequest as Para};
    let bytes=raw("à")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();
    for schema in["hwpx-agent.product-literal-replacement-request/v1","hwpx-agent.product-regex-replacement-request/v1","hwpx-agent.product-character-style-replacement-request/v1",UNICODE_SCHEMA] {
        let mut v=good.clone();v["schema_version"]=json!(schema);let b=wire(&v)?;
        assert!(L1::prepare_json(&provider,&b,Default::default(),Default::default(),4).is_err());assert!(L2::prepare_json(&provider,&b,Default::default(),Default::default(),4).is_err());
        assert!(L3::prepare_json(&provider,&b,Default::default(),Default::default(),4).is_err());assert!(L4::prepare_json(&provider,&b,Default::default(),Default::default(),4).is_err());
        assert!(Product::prepare_json(&provider,&b,Default::default(),Default::default(),4).is_err());assert!(R2::prepare_json(&provider,&b,Default::default(),Default::default(),4).is_err());
        assert!(Style::prepare_json(&provider,&b,Default::default(),Default::default(),4).is_err());assert!(Text::prepare_json(&provider,&b,Default::default(),Default::default(),4).is_err());assert!(Para::prepare_json(&provider,&b,Default::default(),Default::default(),4).is_err());
        assert!(Discovery::prepare_json(&provider,&b,Default::default(),4).is_err());if schema!=UNICODE_SCHEMA{assert!(matches!(UnicodeProduct::prepare_json(&provider,&b,Default::default(),Default::default(),4),Err(UE::Request)));}
    }let old=envelope(&s,&bytes)?;assert!(matches!(unicode_prepare!(&provider,&old),Err(UE::Request)));assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn unicode_product_current_write_and_five_foreign_provider_scopes_deny_retained_bytes()->TestResult {
    let bytes=raw("à")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=request(&s,&bytes)?;let reader=s.provider()?;assert!(unicode_prepare!(&reader,&v).is_err());
    let source=reader.import_actual_forms(s.head,4)?;assert!(matches!(source.prepare_unicode_candidate(&reader,Scope::Document,all(),Form::Nfc,Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),4),Err(US::Permission)));
    let out=unicode_prepare!(&provider,&v)?;let called=Cell::new(false);assert!(out.with_verified_bytes(&reader,5,|_|called.set(true)).is_err());
    for variant in 0..5{let tenant=if variant==4{TenantId::new(Uuid::from_u128(997))?}else{s.reader.tenant_id()};let subject=if variant==3{SubjectDigest::from_authenticated_subject("foreign-unicode")?}else{s.reader.subject()};
        let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);let context=rev::RevisionRequestContext::new(tenant,subject);let project=if variant==2{rev::ProjectId::parse("prj_70000000000000000000000000000002")?}else{s.project};let branch=if variant==1{rev::BranchId::parse("brn_70000000000000000000000000000002")?}else{s.branch};
        let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&context,project,branch,DocumentId::parse(if variant==0{"foreign-document"}else{"actual-form-document"})?)?;
        assert!(out.verify(&other,5).is_err());assert!(out.with_verified_bytes(&other,5,|_|called.set(true)).is_err());}
    assert!(!called.get());Ok(())
}
#[test]
fn unicode_product_acl_regrant_quarantine_and_aead_guard_every_delivery_and_preparation()->TestResult {
    for mode in 0..3{let bytes=raw("à")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=request(&s,&bytes)?;let out=unicode_prepare!(&provider,&v)?;
        match mode{0=>{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;},1=>{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("UNICODE_TEST")?,5)?;},_=>s.blobs.tamper.store(true,Ordering::SeqCst)}
        let called=Cell::new(false);assert!(out.verify(&provider,6).is_err());assert!(out.with_verified_bytes(&provider,6,|_|called.set(true)).is_err());assert!(unicode_prepare!(&provider,&v).is_err());assert!(!called.get());
        if mode==0{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;out.verify(&provider,8)?;out.with_verified_bytes(&provider,8,|_|())?;}
    }Ok(())
}
#[test]
fn unicode_product_prepare_verify_and_delivery_final_head_races_block_consumer()->TestResult {
    for stage in 0..3{let bytes=raw("à")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=request(&s,&bytes)?;let request_bytes=wire(&v)?;let out=unicode_prepare!(&provider,&v)?;
        let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,
            ContentDigest::of(b"unicode race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation"),ContentDigest::of(b"transaction"))?;
        let b=rev::RevisionService::new(BoundaryRepo {inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
        let bound=StoredFormProvider::bind(&s.artifacts,&b,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
        match stage{0=>{UnicodeProduct::prepare_json(&bound,&request_bytes,Default::default(),Default::default(),5)?;},1=>{out.verify(&bound,5)?;},_=>{out.with_verified_bytes(&bound,5,|_|())?;}}
        let calls=b.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);b.repository().calls.store(0,Ordering::SeqCst);b.repository().trigger.store(calls,Ordering::SeqCst);let called=Cell::new(false);
        match stage{0=>assert!(UnicodeProduct::prepare_json(&bound,&request_bytes,Default::default(),Default::default(),6).is_err()),1=>assert!(out.verify(&bound,6).is_err()),_=>assert!(out.with_verified_bytes(&bound,6,|_|called.set(true)).is_err())}
        assert!(!called.get());assert_eq!(b.repository().calls.load(Ordering::SeqCst),calls);
    }Ok(())
}
#[test]
fn unicode_product_borrowed_owned_and_json_share_receipt_and_output_without_reimport()->TestResult {
    let bytes=raw("à")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=request(&s,&bytes)?;let out=unicode_prepare!(&provider,&v)?;let source=provider.import_actual_forms(s.head,4)?;
    let borrowed=source.prepare_unicode_candidate(&provider,Scope::Document,all(),Form::Nfc,Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),4)?;
    assert_eq!(borrowed.verify(&provider,5)?,out.receipt().stored);drop(borrowed);
    let owned=source.into_unicode_candidate(&provider,Scope::Document,all(),Form::Nfc,Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),4)?;
    assert_eq!(owned.verify(&provider,5)?,out.receipt().stored);assert_eq!(owned.with_verified_bytes(&provider,5,<[u8]>::to_vec)?,out.with_verified_bytes(&provider,5,<[u8]>::to_vec)?);
    assert!(matches!(owned.require_current_product_route(&provider,5),Err(US::RouteUnqualified)));Ok(())
}
#[test]
fn unicode_product_wrong_source_head_revision_document_and_project_deny_new_preparation()->TestResult {
    let bytes=raw("à")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=request(&s,&bytes)?;
    for(key,value)in[("expected_head_generation",json!(s.head.generation()+1)),("expected_source_package_sha256",json!("0".repeat(64))),("document_id",json!("foreign-document")),("project_id",json!("prj_70000000000000000000000000000002")),("base_revision",json!(rev::RevisionId::generate().public_id()))]{let mut v=good.clone();v[key]=value;assert!(unicode_prepare!(&provider,&v).is_err());}Ok(())
}
#[test]
fn unicode_product_protection_tracking_and_cached_field_content_block_even_noops()->TestResult {
    let locked=format!("<hp:p id='1'><hp:run>{}</hp:run></hp:p>",table::table(300).replace("lock='0'","lock='1'"));
    for(body,field)in[(locked,false),(para(1,"ABC").replace("charPrIDRef='0'","charPrIDRef='0' charTcId='1'"),false),(fixture::body(),true)]{
        let bytes=definition::package(&body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=request(&s,&bytes)?;
        if field{assert!(matches!(unicode_prepare!(&provider,&v),Err(UE::Stored(US::Output(Compile::FieldContent)))));}else{assert!(matches!(unicode_prepare!(&provider,&v),Err(UE::Stored(US::Output(Compile::Protection)))));}
    }Ok(())
}
#[test]
fn unicode_product_expansion_component_response_and_writer_caps_never_return_partial_candidate()->TestResult {
    let bytes=raw("à à ﬃ")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=request(&s,&bytes)?;v["operation"]["form"]=json!("nfkc");
    for config in[Config {matches:1,..Default::default()},Config {decomposed_scalars:2,..Default::default()},Config {result_bytes:1,..Default::default()}]{assert!(UnicodeProduct::prepare_json(&provider,&wire(&v)?,SourceSearchLimits::new(config)?,Default::default(),4).is_err());}
    assert!(matches!(UnicodeProduct::prepare_json(&provider,&wire(&v)?,Default::default(),WriterLimits::new(WriterLimitConfig {max_output_bytes:1,..Default::default()})?,4),Err(UE::Stored(US::Output(Compile::Writer)))));Ok(())
}
#[test]
fn unicode_product_noop_empty_ambiguous_and_stale_index_selections_are_not_widened()->TestResult {
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=request(&s,&bytes)?;
    assert!(matches!(unicode_prepare!(&provider,&good),Err(UE::Stored(US::Output(Compile::NoChange)))));
    let inv=inventory(&provider,&good)?;let mut v=good;v["selector"]["scope"]=json!("selection");v["selector"]["range"]=window(&inv,"body_and_notes",1,1)?;
    assert!(matches!(unicode_prepare!(&provider,&v),Err(UE::Stored(US::Output(Compile::NoChange)))));v["selector"]["range"]["index_sha256"]=json!("0".repeat(64));assert!(unicode_prepare!(&provider,&v).is_err());
    let bytes=raw("&#x344;à")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=request(&s,&bytes)?;let inv=inventory(&provider,&v)?;
    v["selector"]["scope"]=json!("selection");v["selector"]["range"]=window(&inv,"body_and_notes",0,1)?;assert!(unicode_prepare!(&provider,&v).is_err());Ok(())
}
#[test]
fn unicode_product_receipt_redaction_and_closed_execution_preserve_source_head_and_ingest_count()->TestResult {
    let bytes=raw("PRIVATE-SOURCE à")?;let original=ContentDigest::of(&bytes);let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=request(&s,&bytes)?;let out=unicode_prepare!(&provider,&v)?;
    let debug=format!("{out:?}{:?}",out.receipt());let json=serde_json::to_string(out.receipt())?;for private in["PRIVATE-SOURCE","PRIVATE-UNICODE-KEY"]{assert!(!debug.contains(private));assert!(!json.contains(private));}
    assert!(matches!(out.require_current_product_route(&provider,5),Err(UE::RouteUnqualified)));assert!(!out.receipt().idempotency_key_claimed&&!out.receipt().full_normalization_native_cas_execution_publication_authority);
    assert_eq!(ContentDigest::of(&bytes),original);assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
}
#[test]
fn unicode_product_many_components_keep_one_part_guard_and_one_original_text_span()->TestResult {
    let bytes=raw(&"à ".repeat(128))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=request(&s,&bytes)?;let out=unicode_prepare!(&provider,&v)?;
    assert_eq!(out.with_verified_bytes(&provider,5,section)??,section(&bytes)?.replace("à","à"));let r=&out.receipt().stored.output;
    assert_eq!(r.changed_components,128);assert_eq!(r.changes.len(),1);assert_eq!(r.observed_protection_parts,1);let xml=hwpx_package::PreservingXmlDocument::parse(section(&bytes)?.as_bytes())?;
    assert_eq!(r.observed_protection_element_visits,xml.elements().len()*3);Ok(())
}
#[path="unicode_match_product.rs"] mod matches_v2;
#[path="case_conversion_product.rs"] mod case_v1;
#[path="width_conversion_product.rs"] mod width_v1;
#[path="whitespace_normalization_product.rs"] mod whitespace_v1;
#[path="control_replacement_product.rs"] mod controls_v1;
#[path="number_control_product.rs"] mod number_controls_v1;
#[path="search_mutation_dispatch.rs"] mod dispatch_v1;
#[path="paragraph_sort_product.rs"] mod sort_v1;
