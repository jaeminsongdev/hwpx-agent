//! Explicit text-axis products over original stored/discovery/race fixtures; no Native route.
use super::*;
use hwpx_agent_cli::form_product_request::stored_literal_replacement::text_styles::{StoredTextStyleProductRequest as TextProduct,
    TextStyleProductError as TE,TEXT_STYLE_PRODUCT_REQUEST_SCHEMA as TEXT_SCHEMA};
use hwpx_agent_cli::form_stored_provider::actual_import::literal_search_output::text_styles::StoredTextStyleError as TS;
use hwpx_package::document_import::{ImportedSourcePackage,forms::ImportedDocumentForms,search::{SourceSearchError as Search,
    reviews::selector::styles::SourceReviewStyleFilter as Filter,inspection::SourceDeclaredStyleFilter as Declared,replacement::atoms::styles::SourceStyleReplacementError as SC}};
#[allow(dead_code)] #[path="../../../../hwpx-package/tests/support/search_definition_fixture.rs"] mod definition;
#[allow(dead_code)] #[path="../../../../hwpx-package/tests/support/document_import_catalog_fixture.rs"] mod archive;
macro_rules! text_prepare{($p:expr,$v:expr)=>{TextProduct::prepare_json($p,&wire($v)?,Default::default(),Default::default(),4)}}
fn filter()->Filter{Filter::Declared(Declared {text_character_style:Some(0),..Default::default()})}
fn request(s:&StoredFixture,raw:&[u8])->Result<Value,Box<dyn Error>> {let mut v=envelope(s,raw)?;v["schema_version"]=json!(TEXT_SCHEMA);v["operation"]=json!({
    "kind":"replace_text_character_style","query":"K","regex":false,"case_sensitive":true,"whole_word":false,"max_replacements":100,
    "style_filter":{"kind":"declared","filter":{"text_character_style":0}},"replacement":{"axis":"text_character_style","declaration_id":1},"review_policy":policy(true,true)});Ok(v)}
fn raw(text:&str)->Result<Vec<u8>,Box<dyn Error>> {definition::package(&format!("<hp:p id='1' paraPrIDRef='0'><hp:run charPrIDRef='0'><hp:t charStyleIDRef='0'>{text}</hp:t></hp:run></hp:p>"))}
fn review_raw()->Result<Vec<u8>,Box<dyn Error>> {definition::package(&fixture::body().replace("<hp:run>","<hp:run charPrIDRef='0'>").replace("<hp:t>","<hp:t charStyleIDRef='0'>"))}
fn count(bytes:&[u8],q:&str,filter:Declared)->Result<usize,Box<dyn Error>> {
    let f=ImportedDocumentForms::import(ImportedSourcePackage::import(bytes,DocumentId::parse("text-style-product-readback")?,*ContentDigest::of(bytes).as_bytes(),Default::default())?)?;
    let index=f.source_review_scope_index(bytes,Default::default())?;Ok(index.find_style(Query {mode:Mode::Literal,max_results:10000,..query(q)},Scope::Document,all(),
        Filter::Declared(filter))?.search().result().matches().len())
}
fn text_matches(bytes:&[u8],q:&str,id:u32)->Result<usize,Box<dyn Error>> {count(bytes,q,Declared {text_character_style:Some(id),..Default::default()})}
#[test]
fn text_product_discovery_builds_four_scopes_and_owned_candidates_without_caller_source_import()->TestResult {
    let bytes=review_raw()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=request(&s,&bytes)?;let inv=inventory(&p,&good)?;
    let range=window(&inv,"memo_body",7,8)?;let node=inv["inventory"]["nodes"].as_array().ok_or("nodes")?.iter().find(|n|n["source_handle"]==range["start"]["paragraph_handle"]).ok_or("node")?;
    for(scope,total)in[("document",6),("section",6),("node_set",2),("selection",1)] {let mut v=good.clone();v["selector"]["scope"]=json!(scope);
        match scope {"section"=>v["selector"]["section_ids"]=inv["inventory"]["section_ids"].clone(),"node_set"=>v["selector"]["range"]=json!({"node_ids":[node["node_id"].clone()]}),
            "selection"=>v["selector"]["range"]=range.clone(),_=>{}}
        let out=text_prepare!(&p,&v)?;drop(v);out.verify(&p,5)?;assert_eq!(out.receipt().stored.output.matched_occurrences,total);
        assert_eq!(out.with_verified_bytes(&p,5,|b|text_matches(b,"K",1))??,total);assert_eq!(out.receipt().capability_id,"search.replace_style");
        assert!(out.with_verified_bytes(&p,5,section)??.contains("CACHE FROZEN"));
    }Ok(())
}
#[test]
fn text_product_partial_entities_and_cross_run_hangul_preserve_original_run_properties()->TestResult {
    let bytes=raw("A&#x1F600;B&amp;C")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=request(&s,&bytes)?;v["operation"]["query"]=json!("😀B");
    let out=text_prepare!(&p,&v)?;let after=out.with_verified_bytes(&p,5,<[u8]>::to_vec)?;
    assert_eq!(text_matches(&after,"😀B",1)?,1);assert_eq!(text_matches(&after,"A",0)?,1);assert_eq!(text_matches(&after,"C",0)?,1);
    let xml=section(&after)?;assert!(xml.contains("&#x1F600;B")&&xml.contains("&amp;C"));assert_eq!(xml.matches("<hp:run charPrIDRef='0'>").count(),1);
    let bytes=definition::package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t charStyleIDRef='0'>Xᄀ</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t charStyleIDRef='0'>ᅡ</hp:t></hp:run><hp:run charPrIDRef='0'><hp:t charStyleIDRef='0'>ᆨY</hp:t></hp:run></hp:p>")?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=request(&s,&bytes)?;v["operation"]["query"]=json!("각");let out=text_prepare!(&p,&v)?;
    let after=out.with_verified_bytes(&p,5,<[u8]>::to_vec)?;assert_eq!(text_matches(&after,"각",1)?,1);assert_eq!(text_matches(&after,"X",0)?,1);assert_eq!(text_matches(&after,"Y",0)?,1);
    assert_eq!(out.receipt().stored.output.original_changed_text_elements,3);assert_eq!(section(&after)?.matches("<hp:run charPrIDRef='1'>").count(),1);Ok(())
}
#[test]
fn text_product_definition_filter_regex_casefold_and_word_options_use_original_text_axis()->TestResult {
    let bytes=raw("Cat scatter CAT")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=request(&s,&bytes)?;
    v["operation"]["query"]=json!("c[a]t");v["operation"]["regex"]=json!(true);v["operation"]["case_sensitive"]=json!(false);v["operation"]["whole_word"]=json!(true);
    v["operation"]["style_filter"]=json!({"kind":"definition","filter":{"character_source":"text_style","bold":false}});
    let out=text_prepare!(&p,&v)?;let after=out.with_verified_bytes(&p,5,<[u8]>::to_vec)?;assert_eq!(out.receipt().stored.output.matched_occurrences,2);
    assert_eq!(text_matches(&after,"Cat",1)?,1);assert_eq!(text_matches(&after,"CAT",1)?,1);assert_eq!(text_matches(&after,"scatter",0)?,1);
    assert_eq!(count(&after,"Cat",Declared {run_character_property:Some(0),..Default::default()})?,1);Ok(())
}
#[test]
fn text_product_four_review_policies_exclude_before_caps_without_cache_edits()->TestResult {
    let bytes=review_raw()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut hashes=BTreeSet::new();
    for(h,m,total)in[(false,false,2),(true,false,4),(false,true,4),(true,true,6)] {let mut v=request(&s,&bytes)?;v["operation"]["review_policy"]=policy(h,m);v["operation"]["max_replacements"]=json!(total);
        let out=text_prepare!(&p,&v)?;hashes.insert(out.receipt().stored.output.search_request_sha256);let after=out.with_verified_bytes(&p,5,<[u8]>::to_vec)?;
        assert_eq!(text_matches(&after,"K",1)?,total);assert_eq!(text_matches(&after,"CACHE FROZEN",0)?,1);
    }assert_eq!(hashes.len(),4);let mut v=request(&s,&bytes)?;let inv=inventory(&p,&v)?;v["selector"]["scope"]=json!("selection");v["selector"]["range"]=window(&inv,"memo_body",7,8)?;
    v["operation"]["review_policy"]=policy(false,false);assert!(matches!(text_prepare!(&p,&v),Err(TE::Stored(TS::Output(SC::Compile(Compile::NoMatches))))));Ok(())
}
#[test]
fn text_product_required_closed_axis_filter_policy_and_decoded_duplicates_reject_before_reads()->TestResult {
    let bytes=raw("K")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();let mut bad=vec![b"null".to_vec(),b"[]".to_vec()];
    for key in["schema_version","idempotency_key","project_id","document_id","base_revision","expected_head_generation","expected_source_package_sha256","plan_id","selector","operation"] {
        let mut v=good.clone();v.as_object_mut().ok_or("envelope")?.remove(key);bad.push(wire(&v)?);
    }
    for key in["kind","query","regex","case_sensitive","whole_word","max_replacements","style_filter","replacement","review_policy"] {
        let mut v=good.clone();v["operation"].as_object_mut().ok_or("operation")?.remove(key);bad.push(wire(&v)?);
    }
    for replacement in[json!("1"),json!(null),json!([]),json!({}),json!({"axis":"text_character_style"}),json!({"declaration_id":1}),
        json!({"axis":"run_character_property","declaration_id":1}),json!({"axis":"text_character_style","declaration_id":-1}),json!({"axis":"text_character_style","declaration_id":4294967296u64}),
        json!({"axis":"text_character_style","declaration_id":1,"approved":true})] {let mut v=good.clone();v["operation"]["replacement"]=replacement;bad.push(wire(&v)?);}
    for f in[json!({}),json!([]),json!({"kind":"declared","filter":{}}),json!({"kind":"definition","filter":{"bold":true}}),json!({"kind":"declared","filter":{"unknown":0}})] {
        let mut v=good.clone();v["operation"]["style_filter"]=f;bad.push(wire(&v)?);
    }
    for(key,value)in[("kind",json!("replace_character_property")),("query",json!("")),("query",json!("Q".repeat(4097))),("regex",json!(1)),("max_replacements",json!(0)),("max_replacements",json!(10001)),
        ("run_policy",json!("flatten_runs")),("include_hidden",json!(true)),("preview_only",json!(false)),("review_policy",json!({"include_memo_bodies":true}))] {
        let mut v=good.clone();v["operation"][key]=value;bad.push(wire(&v)?);
    }
    for(key,value)in[("schema_version",json!(SCHEMA)),("approved",json!(true)),("source_graph",json!({})),("expected_head_generation",json!(0)),("expected_source_package_sha256",json!("A".repeat(64)))] {
        let mut v=good.clone();v[key]=value;bad.push(wire(&v)?);
    }
    let mut v=good.clone();v["selector"]["revision_id"]=json!(rev::RevisionId::generate().public_id());bad.push(wire(&v)?);
    let text=serde_json::to_string(&good)?;for(from,to)in[("\"axis\":\"text_character_style\"","\"axis\":\"text_character_style\",\"a\\u0078is\":\"run_character_property\""),
        ("\"declaration_id\":1","\"declaration_id\":1,\"declaration_\\u0069d\":0")] {let v=text.replace(from,to);assert_ne!(v,text);bad.push(v.into_bytes());}
    for bytes in bad {assert!(matches!(TextProduct::prepare_json(&p,&bytes,Default::default(),Default::default(),4),Err(TE::Request)));}
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn text_product_legacy_run_literal_regex_and_search_schemas_do_not_become_text_mutation_routes()->TestResult {
    use hwpx_agent_cli::form_product_request::stored_literal_replacement::{StoredLiteralReplacementProductRequest as L1,atoms::StoredLiteralTextAtomProductRequest as L2,
        review::StoredReviewLiteralProductRequest as L3,selector::StoredSelectorLiteralProductRequest as L4,regex::insertions::StoredRegexInsertionProductRequest as R2,
        styles::StoredCharacterStyleProductRequest as Run};
    use hwpx_agent_cli::form_product_request::stored_source_search::selector::styles::StoredSelectorStyleProductRequest as Find;
    let bytes=raw("K")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();
    for schema in[TEXT_SCHEMA,SCHEMA,"hwpx-agent.product-regex-replacement-request/v2","hwpx-agent.product-literal-replacement-request/v1","hwpx-agent.product-literal-replacement-request/v2",
        "hwpx-agent.product-literal-replacement-request/v3","hwpx-agent.product-literal-replacement-request/v4","hwpx-agent.product-source-search-request/v7","hwpx-agent.product-character-style-replacement-request/v1"] {
        let mut v=good.clone();v["schema_version"]=json!(schema);let bytes=wire(&v)?;
        assert!(Product::prepare_json(&p,&bytes,Default::default(),Default::default(),4).is_err());assert!(R2::prepare_json(&p,&bytes,Default::default(),Default::default(),4).is_err());
        assert!(L1::prepare_json(&p,&bytes,Default::default(),Default::default(),4).is_err());assert!(L2::prepare_json(&p,&bytes,Default::default(),Default::default(),4).is_err());
        assert!(L3::prepare_json(&p,&bytes,Default::default(),Default::default(),4).is_err());assert!(L4::prepare_json(&p,&bytes,Default::default(),Default::default(),4).is_err());
        assert!(Run::prepare_json(&p,&bytes,Default::default(),Default::default(),4).is_err());assert!(Find::prepare_json(&p,&bytes,Default::default(),4).is_err());
    }
    let mut run=good.clone();run["schema_version"]=json!("hwpx-agent.product-character-style-replacement-request/v1");run["operation"]["kind"]=json!("replace_character_property");run["operation"]["replacement"]["axis"]=json!("run_character_property");
    assert!(matches!(text_prepare!(&p,&run),Err(TE::Request)));assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn text_product_exact_16k_raw_canonical_provider_key_plan_and_filter_identities_are_distinct()->TestResult {
    let bytes=raw("K")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=request(&s,&bytes)?;let out=text_prepare!(&p,&v)?;let mut padded=wire(&v)?;padded.resize(16*1024,b' ');
    let other=TextProduct::prepare_json(&p,&padded,Default::default(),Default::default(),4)?;assert_ne!(out.receipt().raw_request_sha256,other.receipt().raw_request_sha256);assert_eq!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);
    padded.push(b' ');assert!(matches!(TextProduct::prepare_json(&p,&padded,Default::default(),Default::default(),4),Err(TE::Limit)));assert!(matches!(TextProduct::prepare_json(&p,b"",Default::default(),Default::default(),4),Err(TE::Limit)));
    for(key,value)in[("idempotency_key",json!("OTHER-KEY")),("plan_id",json!("other-plan"))] {let mut v=v.clone();v[key]=value;let other=text_prepare!(&p,&v)?;
        assert_ne!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);assert_ne!(out.receipt().scoped_request_sha256,other.receipt().scoped_request_sha256);assert_eq!(out.receipt().stored.output.output_package_sha256,other.receipt().stored.output.output_package_sha256);
    }
    let mut other=v.clone();other["operation"]["style_filter"]=json!({"kind":"definition","filter":{"character_source":"text_style","bold":false}});let other=text_prepare!(&p,&other)?;
    assert_ne!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);assert_ne!(out.receipt().stored.output.replacement_request_sha256,other.receipt().stored.output.replacement_request_sha256);
    assert_eq!(out.receipt().stored.output.output_package_sha256,other.receipt().stored.output.output_package_sha256);Ok(())
}
#[test]
fn text_product_current_write_and_five_foreign_scopes_block_all_retained_output()->TestResult {
    let bytes=raw("K")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=request(&s,&bytes)?;let reader=s.provider()?;assert!(text_prepare!(&reader,&v).is_err());
    let out=text_prepare!(&p,&v)?;let called=Cell::new(false);assert!(out.with_verified_bytes(&reader,5,|_|called.set(true)).is_err());
    let source=reader.import_actual_forms(s.head,4)?;assert!(matches!(source.prepare_text_style_candidate(&reader,Query {mode:Mode::Literal,..query("K")},Scope::Document,all(),filter(),1,
        Default::default(),Default::default(),4),Err(TS::Permission)));
    for variant in 0..5 {let tenant=if variant==4{TenantId::new(Uuid::from_u128(997))?}else{s.reader.tenant_id()};let subject=if variant==3{SubjectDigest::from_authenticated_subject("foreign-text-style")?}else{s.reader.subject()};
        let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);let context=rev::RevisionRequestContext::new(tenant,subject);
        let project=if variant==2{rev::ProjectId::parse("prj_70000000000000000000000000000002")?}else{s.project};let branch=if variant==1{rev::BranchId::parse("brn_70000000000000000000000000000002")?}else{s.branch};
        let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&context,project,branch,DocumentId::parse(if variant==0{"foreign-document"}else{"actual-form-document"})?)?;
        assert!(out.verify(&other,5).is_err());assert!(out.with_verified_bytes(&other,5,|_|called.set(true)).is_err());
    }assert!(!called.get());Ok(())
}
#[test]
fn text_product_acl_revoke_regrant_quarantine_and_aead_are_checked_for_old_and_new_candidates()->TestResult {
    for mode in 0..3 {let bytes=raw("K")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=request(&s,&bytes)?;let out=text_prepare!(&p,&v)?;
        match mode {0=>{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;},1=>{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("TEXT_STYLE_TEST")?,5)?;},_=>s.blobs.tamper.store(true,Ordering::SeqCst)}
        let called=Cell::new(false);assert!(out.verify(&p,6).is_err());assert!(out.with_verified_bytes(&p,6,|_|called.set(true)).is_err());assert!(text_prepare!(&p,&v).is_err());assert!(!called.get());
        if mode==0{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;out.verify(&p,8)?;out.with_verified_bytes(&p,8,|_|())?;}
    }Ok(())
}
#[test]
fn text_product_prepare_verify_and_delivery_final_head_races_block_consumer_calls()->TestResult {
    for stage in 0..3 {let bytes=raw("K")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=request(&s,&bytes)?;let request_bytes=wire(&v)?;let out=text_prepare!(&p,&v)?;
        let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,
            ContentDigest::of(b"text style race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation"),ContentDigest::of(b"transaction"))?;
        let b=rev::RevisionService::new(BoundaryRepo {inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
        let bound=StoredFormProvider::bind(&s.artifacts,&b,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
        match stage {0=>{TextProduct::prepare_json(&bound,&request_bytes,Default::default(),Default::default(),5)?;},1=>{out.verify(&bound,5)?;},_=>{out.with_verified_bytes(&bound,5,|_|())?;}}
        let calls=b.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);b.repository().calls.store(0,Ordering::SeqCst);b.repository().trigger.store(calls,Ordering::SeqCst);let called=Cell::new(false);
        match stage {0=>assert!(TextProduct::prepare_json(&bound,&request_bytes,Default::default(),Default::default(),6).is_err()),1=>assert!(out.verify(&bound,6).is_err()),_=>assert!(out.with_verified_bytes(&bound,6,|_|called.set(true)).is_err())}
        assert!(!called.get());assert_eq!(b.repository().calls.load(Ordering::SeqCst),calls);
    }Ok(())
}
#[test]
fn text_product_borrowed_owned_and_json_candidates_share_target_and_exact_output_receipts()->TestResult {
    let bytes=raw("K")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=request(&s,&bytes)?;let out=text_prepare!(&p,&v)?;let source=p.import_actual_forms(s.head,4)?;
    let borrowed=source.prepare_text_style_candidate(&p,Query {mode:Mode::Literal,..query("K")},Scope::Document,all(),filter(),1,Default::default(),Default::default(),4)?;
    assert_eq!(borrowed.verify(&p,5)?,out.receipt().stored);drop(borrowed);
    let owned=source.into_text_style_candidate(&p,Query {mode:Mode::Literal,..query("K")},Scope::Document,all(),filter(),1,Default::default(),Default::default(),4)?;
    assert_eq!(owned.verify(&p,5)?,out.receipt().stored);assert_eq!(owned.with_verified_bytes(&p,5,<[u8]>::to_vec)?,out.with_verified_bytes(&p,5,<[u8]>::to_vec)?);
    assert!(matches!(owned.require_current_product_route(&p,5),Err(TS::RouteUnqualified)));Ok(())
}
#[test]
fn text_product_wrong_source_head_document_and_project_reject_preparation()->TestResult {
    let bytes=raw("K")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=request(&s,&bytes)?;
    for(key,value)in[("expected_head_generation",json!(s.head.generation()+1)),("expected_source_package_sha256",json!("0".repeat(64))),("document_id",json!("foreign-document")),("project_id",json!("prj_70000000000000000000000000000002"))] {
        let mut bad=good.clone();bad[key]=value;assert!(text_prepare!(&p,&bad).is_err());
    }Ok(())
}
#[test]
fn text_product_invalid_target_ambiguous_nfc_partial_decomposition_and_noop_fail_closed()->TestResult {
    for(text,q)in[("a&#x315;&#x300;","à"),("&#x344;","\u{308}")] {let bytes=raw(text)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=request(&s,&bytes)?;v["operation"]["query"]=json!(q);
        assert!(matches!(text_prepare!(&p,&v),Err(TE::Stored(TS::Output(SC::Compile(Compile::Selection))))));
    }
    let bytes=raw("K")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=request(&s,&bytes)?;v["operation"]["replacement"]["declaration_id"]=json!(u32::MAX);
    assert!(matches!(text_prepare!(&p,&v),Err(TE::Stored(TS::Output(SC::Search(Search::Definition))))));v["operation"]["replacement"]["declaration_id"]=json!(0);
    assert!(matches!(text_prepare!(&p,&v),Err(TE::Stored(TS::Output(SC::Compile(Compile::NoChange))))));Ok(())
}
#[test]
fn text_product_cache_control_tracked_and_table_protection_remain_enforced()->TestResult {
    let table_bytes=assembly::package(&table::table(300).replace("lock='0'","lock='1'").replace("<hp:t>","<hp:t charStyleIDRef='0'>"))?;
    let table_bytes=archive::mutate_part(&table_bytes,"Contents/header.xml",|_|definition::header())?;
    for(body,q)in[(fixture::body().replace("<hp:t>","<hp:t charStyleIDRef='0'>").replace("CACHE FROZEN","CACHE K"),"K"),
        (format!("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t charStyleIDRef='0'>K{TAB}K</hp:t></hp:run></hp:p>"),"\t"),
        ("<hp:p id='1'><hp:run charPrIDRef='0' charTcId='2'><hp:t charStyleIDRef='0'>K</hp:t></hp:run></hp:p>".to_owned(),"K")] {
        let bytes=definition::package(&body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=request(&s,&bytes)?;v["operation"]["query"]=json!(q);assert!(text_prepare!(&p,&v).is_err());
    }
    let s=StoredFixture::new(&table_bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=request(&s,&table_bytes)?;v["operation"]["query"]=json!("OLD");
    assert!(matches!(text_prepare!(&p,&v),Err(TE::Stored(TS::Output(SC::Compile(Compile::Protection))))));Ok(())
}
#[test]
fn text_product_match_output_writer_pattern_and_zero_width_limits_reject_entire_candidate()->TestResult {
    let bytes=raw("K K")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=request(&s,&bytes)?;v["operation"]["max_replacements"]=json!(1);assert!(text_prepare!(&p,&v).is_err());
    v["operation"]["max_replacements"]=json!(100);assert!(TextProduct::prepare_json(&p,&wire(&v)?,SourceSearchLimits::new(Config {result_bytes:1,..Default::default()})?,Default::default(),4).is_err());
    assert!(matches!(TextProduct::prepare_json(&p,&wire(&v)?,Default::default(),WriterLimits::new(WriterLimitConfig {max_output_bytes:1})?,4),Err(TE::Stored(TS::Output(SC::Compile(Compile::Writer))))));
    for q in["(","^"] {v["operation"]["query"]=json!(q);v["operation"]["regex"]=json!(true);assert!(text_prepare!(&p,&v).is_err());}Ok(())
}
#[test]
fn text_product_missing_text_reference_is_not_defaulted_on_unselected_characters()->TestResult {
    let bytes=definition::package("<hp:p id='1' paraPrIDRef='0'><hp:run charPrIDRef='0'><hp:t>ABC</hp:t></hp:run></hp:p>")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=request(&s,&bytes)?;
    v["operation"]["query"]=json!("B");v["operation"]["style_filter"]=json!({"kind":"declared","filter":{"paragraph_property":0}});let out=text_prepare!(&p,&v)?;let after=out.with_verified_bytes(&p,5,<[u8]>::to_vec)?;
    assert_eq!(text_matches(&after,"B",1)?,1);assert_eq!(text_matches(&after,"A",0)?,0);assert_eq!(text_matches(&after,"C",0)?,0);
    assert_eq!(count(&after,"ABC",Declared {run_character_property:Some(0),..Default::default()})?,1);Ok(())
}
#[test]
fn text_product_many_matches_reuse_one_protection_map_without_head_ingest_or_privacy_changes()->TestResult {
    let bytes=raw(&"K ".repeat(128))?;let original=ContentDigest::of(&bytes);let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=request(&s,&bytes)?;v["operation"]["max_replacements"]=json!(128);
    let out=text_prepare!(&p,&v)?;assert_eq!(out.with_verified_bytes(&p,5,|b|text_matches(b,"K",1))??,128);let xml=hwpx_package::PreservingXmlDocument::parse(section(&bytes)?.as_bytes())?;
    assert_eq!(out.receipt().stored.output.observed_protection_element_visits,xml.elements().len()*2);assert_eq!(ContentDigest::of(&bytes),original);
    assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);
    assert!(!format!("{out:?}{:?}{}",out.receipt(),serde_json::to_string(out.receipt())?).contains("PRIVATE"));assert!(matches!(out.require_current_product_route(&p,5),Err(TE::RouteUnqualified)));
    assert!(!out.receipt().idempotency_key_claimed&&!out.receipt().full_style_native_cas_execution_publication_authority);Ok(())
}
#[test]
fn text_product_aliases_and_native_field_ids_preserve_the_original_run_and_cached_text()->TestResult {
    let bytes=definition::package("<hp:p id='1' xmlns:z='http://www.hancom.co.kr/hwpml/2011/paragraph'><z:run charPrIDRef='0'><z:t charStyleIDRef='0'>AB</z:t><z:ctrl><z:fieldBegin id='17' type='DOC_DATE' editable='1'/></z:ctrl><z:t charStyleIDRef='0'>FROZEN</z:t><z:ctrl><z:fieldEnd beginIDRef='17'/></z:ctrl><z:t charStyleIDRef='0'>CD</z:t></z:run></hp:p>")?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=request(&s,&bytes)?;v["operation"]["query"]=json!("B");let out=text_prepare!(&p,&v)?;let after=out.with_verified_bytes(&p,5,<[u8]>::to_vec)?;let xml=section(&after)?;
    assert_eq!(xml.matches("<z:fieldBegin id='17' type='DOC_DATE' editable='1'/>").count(),1);assert_eq!(xml.matches("<z:fieldEnd beginIDRef='17'/>").count(),1);assert_eq!(xml.matches("<z:run charPrIDRef='0'>").count(),1);
    assert_eq!(text_matches(&after,"B",1)?,1);assert_eq!(text_matches(&after,"FROZEN",0)?,1);Ok(())
}
