//! Current sealed synthetic service + real package candidates. No operational DB or Native.
use super::*;
use hwpx_agent_cli::form_product_request::stored_literal_replacement::fonts::options::{StoredFontOptionsProductRequest as Options,
    FontOptionsProductError as X,FONT_OPTIONS_REQUEST_SCHEMA as V2};
use hwpx_package::document_import::search::{inspection::SourceDeclaredStyleFilter as Declared,reviews::selector::styles::SourceReviewStyleFilter as Filter};
fn v2(s:&StoredFixture,bytes:&[u8],preview:bool)->Result<Value,Box<dyn Error>>{
    let mut v=request(s,bytes)?;v["schema_version"]=json!(V2);v["operation"]["preview_only"]=json!(preview);Ok(v)
}
fn declared()->Value{json!({"kind":"declared","filter":{"run_character_property":0}})}
macro_rules! options{($p:expr,$v:expr)=>{Options::prepare_json($p,&wire($v)?,Default::default(),Default::default(),4)}}
fn two()->Result<Vec<u8>,Box<dyn Error>>{package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>A</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>B</hp:t></hp:run></hp:p>")}

#[test]
fn filtered_mutation_changes_only_matching_original_style()->R{
    let bytes=two()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=v2(&s,&bytes,false)?;v["operation"]["style_filter"]=declared();
    let out=options!(&p,&v)?;out.verify(&p,5)?;let values=out.with_verified_bytes(&p,5,refs)??;
    assert_ne!(values[0].1,0);assert_eq!(values[1].1,1);assert_eq!(out.receipt().stored.output.source().changed_source_scalars,1);
    assert!(!out.receipt().preview_only);assert!(out.receipt().stored.candidate_output_retained);Ok(())
}
#[test]
fn original_definition_filter_reaches_product_without_default_axis_guess()->R{
    let bytes=two()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=v2(&s,&bytes,false)?;
    v["operation"]["query"]=json!(name(&bytes,1)?);v["operation"]["style_filter"]=json!({"kind":"definition","filter":{"character_source":"run_property","bold":true}});
    let out=options!(&p,&v)?;let values=out.with_verified_bytes(&p,5,refs)??;assert_eq!(values[0].1,0);assert_ne!(values[1].1,1);Ok(())
}
#[test]
fn absent_filter_uses_original_v1_output_and_receipt_unchanged()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    let old=prepare!(&p,&request(&s,&bytes)?)?;let new=options!(&p,&v2(&s,&bytes,false)?)?;
    assert_eq!(&old.receipt().stored.output,new.receipt().stored.output.source());
    assert_eq!(old.with_verified_bytes(&p,5,<[u8]>::to_vec)?,new.with_verified_bytes(&p,5,<[u8]>::to_vec)?);Ok(())
}
#[test]
fn preview_discards_output_and_matches_mutation_predicted_result_without_claiming_a_key()->R{
    let bytes=two()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=v2(&s,&bytes,false)?;v["operation"]["style_filter"]=declared();
    let mutation=options!(&p,&v)?;v["operation"]["preview_only"]=json!(true);let preview=options!(&p,&v)?;
    assert_eq!(mutation.receipt().stored.output,preview.receipt().stored.output);assert!(preview.receipt().preview_only);
    assert!(!preview.receipt().stored.candidate_output_retained);assert_ne!(mutation.receipt().canonical_request_sha256,preview.receipt().canonical_request_sha256);
    let called=Cell::new(false);assert!(matches!(preview.with_verified_bytes(&p,5,|_|called.set(true)),Err(X::PreviewOnly)));assert!(!called.get());
    let metadata=preview.with_verified_json(&p,5,|b|serde_json::from_slice::<Value>(b))??;assert_eq!(metadata["preview_only"],true);assert_eq!(metadata["stored"]["candidate_output_retained"],false);
    assert!(!preview.receipt().idempotency_key_claimed&&!preview.receipt().full_font_native_cas_execution_publication_authority);Ok(())
}
#[test]
fn preview_without_filter_does_not_ingest_commit_or_change_original_head()->R{
    let bytes=raw("PRIVATE-SOURCE")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let out=options!(&p,&v2(&s,&bytes,true)?)?;
    out.verify(&p,5)?;assert!(out.receipt().stored.output.style_filter().is_none());
    assert!(matches!(out.require_current_product_route(&p,5),Err(X::RouteUnqualified)));
    assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);
    assert_eq!(s.artifacts.download(&s.reader,s.result,6)?,bytes);Ok(())
}
#[test]
fn direct_borrowed_owned_and_preview_reuse_same_current_source_candidate()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let n=name(&bytes,0)?;
    let source=p.import_actual_forms(s.head,4)?;let filter=Some(Filter::Declared(Declared{run_character_property:Some(0),..Default::default()}));
    let borrowed=source.prepare_font_options_candidate(&p,query(&n),Scope::Document,policy(),Axis::RunProperty,filter,Default::default(),Default::default(),4)?;
    let owned=p.import_actual_forms(s.head,4)?.into_font_options_candidate(&p,query(&n),Scope::Document,policy(),Axis::RunProperty,filter,Default::default(),Default::default(),4)?;
    assert_eq!(borrowed.receipt(),owned.receipt());borrowed.verify(&p,5)?;
    let preview=owned.into_preview();assert_eq!(preview.verify(&p,5)?.output,borrowed.receipt().output);
    assert!(matches!(preview.require_current_product_route(&p,5),Err(Stored::RouteUnqualified)));Ok(())
}
#[test]
fn explicit_text_filter_preserves_run_axis_and_unselected_text()->R{
    let bytes=package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t charStyleIDRef='0'>A</hp:t><hp:t charStyleIDRef='1'>B</hp:t></hp:run></hp:p>")?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=v2(&s,&bytes,false)?;v["operation"]["axis"]=json!("text_style");v["operation"]["query"]=json!(name(&bytes,1)?);
    v["operation"]["style_filter"]=json!({"kind":"declared","filter":{"text_character_style":1}});let out=options!(&p,&v)?;let values=out.with_verified_bytes(&p,5,refs)??;
    assert_eq!(values[0].2,Some(0));assert_ne!(values[1].2,Some(1));assert!(values.iter().all(|v|v.1==0));Ok(())
}
#[test]
fn selection_window_and_style_filter_both_limit_changed_scalars()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=v2(&s,&bytes,false)?;
    // The old inventory request rejects new operation options, so use the original v1 envelope.
    let inv=inventory(&p,&request(&s,&bytes)?)?;v["selector"]["scope"]=json!("selection");v["selector"]["range"]=selection(&inv,1,2)?;v["operation"]["style_filter"]=declared();
    let out=options!(&p,&v)?;assert_eq!(out.receipt().stored.output.source().changed_source_scalars,1);let values=out.with_verified_bytes(&p,5,refs)??;
    assert_eq!(values[0].1,0);assert_ne!(values[1].1,0);assert_eq!(values[2].1,0);Ok(())
}
#[test]
fn required_preview_flag_and_closed_filter_shapes_reject_before_source_reads()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=v2(&s,&bytes,true)?;let before=s.metadata.audit_events()?.len();
    let mut absent=good.clone();absent["operation"].as_object_mut().ok_or("op")?.remove("preview_only");assert!(matches!(options!(&p,&absent),Err(X::Request)));
    for value in [Value::Null,json!([]),json!({}),json!({"kind":"declared","filter":{}}),json!({"kind":"definition","filter":{"bold":true}}),
        json!({"kind":"declared","filter":{"run_character_property":0,"fallback":true}}),json!({"kind":{"declared":null},"filter":{"run_character_property":0}})]{
        let mut v=good.clone();v["operation"]["style_filter"]=value;assert!(matches!(options!(&p,&v),Err(X::Request)));}
    for value in [Value::Null,json!(1),json!("true")]{let mut v=good.clone();v["operation"]["preview_only"]=value;assert!(matches!(options!(&p,&v),Err(X::Request)));}
    assert_eq!(before,s.metadata.audit_events()?.len());Ok(())
}
#[test]
fn unknown_missing_root_and_enum_object_fields_remain_strict_before_reads()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=v2(&s,&bytes,true)?;let before=s.metadata.audit_events()?.len();
    for key in ["project_id","document_id","expected_source_package_sha256","selector","operation","idempotency_key","plan_id"]{let mut v=good.clone();v.as_object_mut().ok_or("root")?.remove(key);assert!(matches!(options!(&p,&v),Err(X::Request)));}
    for(key,value)in [("unknown",json!(true)),("kind",json!({"replace_fonts":null})),("axis",json!({"run_property":null})),("languages",json!([{"hangul":null}]))]{
        let mut v=good.clone();v["operation"][key]=value;assert!(matches!(options!(&p,&v),Err(X::Request)));}
    let mut v=good;v["extra"]=json!(1);assert!(matches!(options!(&p,&v),Err(X::Request)));assert_eq!(before,s.metadata.audit_events()?.len());Ok(())
}
#[test]
fn duplicate_escaped_filter_keys_trailing_json_and_wrong_schema_reject_before_reads()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=v2(&s,&bytes,true)?;v["operation"]["style_filter"]=declared();let text=serde_json::to_string(&v)?;let before=s.metadata.audit_events()?.len();
    for raw in [format!("{text} {{}}"),text.replace("\"preview_only\":true","\"preview_only\":true,\"preview_\\u006fnly\":false"),
        text.replace("\"run_character_property\":0","\"run_character_property\":0,\"run_character_\\u0070roperty\":1"),"null".into(),"[]".into()]{
        assert!(matches!(Options::prepare_json(&p,raw.as_bytes(),Default::default(),Default::default(),4),Err(X::Request)));}
    v["schema_version"]=json!(SCHEMA);assert!(matches!(options!(&p,&v),Err(X::Request)));assert_eq!(before,s.metadata.audit_events()?.len());Ok(())
}
#[test]
fn exact_sixteen_kib_request_boundary_and_query_budget_are_enforced()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=v2(&s,&bytes,true)?;let mut raw=wire(&v)?;raw.resize(16384,b' ');
    Options::prepare_json(&p,&raw,Default::default(),Default::default(),4)?;let before=s.metadata.audit_events()?.len();raw.push(b' ');
    assert!(matches!(Options::prepare_json(&p,&raw,Default::default(),Default::default(),4),Err(X::Limit)));
    let limits=SourceSearchLimits::new(Config{query_bytes:1,..Default::default()})?;assert!(matches!(Options::prepare_json(&p,&wire(&v)?,limits,Default::default(),4),Err(X::Limit)));
    assert_eq!(before,s.metadata.audit_events()?.len());Ok(())
}
#[test]
fn request_server_and_writer_limits_apply_to_preview_as_well_as_mutation()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    for preview in [false,true]{let mut v=v2(&s,&bytes,preview)?;v["operation"]["style_filter"]=declared();v["operation"]["max_changed_scalars"]=json!(1);
        assert!(matches!(options!(&p,&v),Err(X::Stored(Stored::Output(SourceError::Compile(Compile::Limit))))));
        v["operation"]["max_changed_scalars"]=json!(3);let limits=SourceSearchLimits::new(Config{matches:1,..Default::default()})?;
        assert!(matches!(Options::prepare_json(&p,&wire(&v)?,limits,Default::default(),4),Err(X::Stored(Stored::Output(SourceError::Compile(Compile::Limit))))));
        let writer=WriterLimits::new(WriterLimitConfig{max_output_bytes:1})?;assert!(matches!(Options::prepare_json(&p,&wire(&v)?,Default::default(),writer,4),Err(X::Stored(Stored::Output(SourceError::Compile(Compile::Writer))))));}
    Ok(())
}
#[test]
fn write_scope_required_even_for_preview_preparation_and_metadata_delivery()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let reader=s.provider()?;
    for preview in [false,true]{let v=v2(&s,&bytes,preview)?;assert!(options!(&reader,&v).is_err());let out=options!(&p,&v)?;let called=Cell::new(false);
        assert!(out.with_verified_json(&reader,5,|_|called.set(true)).is_err());assert!(!called.get());}
    Ok(())
}
#[test]
fn five_foreign_provider_scopes_cannot_read_retained_preview_or_mutation_metadata()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    for preview in [false,true]{let out=options!(&p,&v2(&s,&bytes,preview)?)?;let called=Cell::new(false);
        for mode in 0..5{let tenant=if mode==4{TenantId::new(Uuid::from_u128(998))?}else{s.reader.tenant_id()};let subject=if mode==3{SubjectDigest::from_authenticated_subject("foreign-font-options")?}else{s.reader.subject()};
            let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);let context=rev::RevisionRequestContext::new(tenant,subject);
            let project=if mode==2{rev::ProjectId::parse("prj_70000000000000000000000000000002")?}else{s.project};let branch=if mode==1{rev::BranchId::parse("brn_70000000000000000000000000000002")?}else{s.branch};
            let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&context,project,branch,DocumentId::parse(if mode==0{"foreign-document"}else{"actual-form-document"})?)?;
            assert!(out.verify(&other,5).is_err());assert!(out.with_verified_json(&other,5,|_|called.set(true)).is_err());}
        assert!(!called.get());}Ok(())
}
#[test]
fn revoked_acl_blocks_preview_metadata_and_mutation_bytes_then_regrant_rechecks()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mutation=options!(&p,&v2(&s,&bytes,false)?)?;let preview=options!(&p,&v2(&s,&bytes,true)?)?;
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;let called=Cell::new(false);
    for out in [&mutation,&preview]{assert!(out.verify(&p,6).is_err());assert!(out.with_verified_json(&p,6,|_|called.set(true)).is_err());}assert!(!called.get());
    assert!(mutation.with_verified_bytes(&p,6,|_|called.set(true)).is_err());assert!(!called.get());
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;mutation.verify(&p,8)?;preview.verify(&p,8)?;Ok(())
}
#[test]
fn quarantine_blocks_retained_preview_metadata_and_new_preparation()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=v2(&s,&bytes,true)?;let out=options!(&p,&v)?;
    s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("FONT_OPTIONS_TEST")?,5)?;let called=Cell::new(false);
    assert!(options!(&p,&v).is_err());assert!(out.verify(&p,6).is_err());assert!(out.with_verified_json(&p,6,|_|called.set(true)).is_err());assert!(!called.get());Ok(())
}
#[test]
fn ciphertext_tamper_blocks_retained_preview_metadata_and_new_preparation()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=v2(&s,&bytes,true)?;let out=options!(&p,&v)?;
    s.blobs.tamper.store(true,Ordering::SeqCst);let called=Cell::new(false);assert!(options!(&p,&v).is_err());assert!(out.verify(&p,6).is_err());
    assert!(out.with_verified_json(&p,6,|_|called.set(true)).is_err());assert!(!called.get());Ok(())
}
#[test]
fn source_revision_and_head_generation_are_not_bypassed_by_preview()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=v2(&s,&bytes,true)?;
    for(key,value)in [("expected_source_package_sha256",json!("0".repeat(64))),("expected_head_generation",json!(s.head.generation()+1)),("base_revision",json!(rev::RevisionId::generate().public_id()))]{
        let mut v=good.clone();v[key]=value;assert!(options!(&p,&v).is_err());}Ok(())
}
#[test]
fn field_cache_and_zero_tracking_are_rejected_in_preview_and_mutation()->R{
    for body in ["<hp:p id='1'><hp:run charPrIDRef='0'><hp:ctrl><hp:fieldBegin id='17' type='DATE'/></hp:ctrl><hp:t>CACHE</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='17'/></hp:ctrl></hp:run></hp:p>",
        "<hp:p id='1' paraTcId='0'><hp:run charPrIDRef='0'><hp:t>A</hp:t></hp:run></hp:p>"]{
        let bytes=package(body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
        for preview in [false,true]{let mut v=v2(&s,&bytes,preview)?;v["operation"]["style_filter"]=declared();let error=options!(&p,&v).unwrap_err();
            assert!(matches!(error,X::Stored(Stored::Output(SourceError::Compile(Compile::FieldContent|Compile::Protection)))));}}
    Ok(())
}
#[test]
fn invalid_regex_and_missing_font_target_do_not_return_preview_success()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=v2(&s,&bytes,true)?;
    for(key,value)in [("query",json!("P09-NOT-DECLARED")),("replacement",json!("P09-MISSING-TARGET"))]{let mut v=good.clone();v["operation"][key]=value;assert!(options!(&p,&v).is_err());}
    let mut v=good;v["operation"]["regex"]=json!(true);v["operation"]["query"]=json!("[");assert!(options!(&p,&v).is_err());Ok(())
}
#[test]
fn conditions_policy_and_language_bind_requests_without_disclosing_private_text()->R{
    let bytes=package("<hp:p id='1' paraPrIDRef='0'><hp:run charPrIDRef='0'><hp:t>PRIVATE-SOURCE</hp:t></hp:run></hp:p>")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut good=v2(&s,&bytes,true)?;good["operation"]["style_filter"]=declared();let first=options!(&p,&good)?;
    for(key,value)in [("languages",json!(["hangul"])),("review_policy",json!({"include_hidden_explanations":true,"include_memo_bodies":true})),("style_filter",json!({"kind":"declared","filter":{"run_character_property":0,"paragraph_property":0}}))]{
        let mut v=good.clone();v["operation"][key]=value;let other=options!(&p,&v)?;
        assert_ne!(first.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);}
    for text in [format!("{first:?}{:?}",first.receipt()),first.with_verified_json(&p,5,|b|String::from_utf8_lossy(b).into_owned())?]{assert!(!text.contains("PRIVATE-FONT")&&!text.contains("PRIVATE-SOURCE")&&!text.contains("PRIVATE-FONT-KEY"));}
    Ok(())
}
fn race_options(preview:bool,stage:usize)->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=v2(&s,&bytes,preview)?;let out=options!(&p,&v)?;
    let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,
        ContentDigest::of(b"font-options-race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation fixture"),ContentDigest::of(b"transaction fixture"))?;
    let repo=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
    let bound=StoredFormProvider::bind(&s.artifacts,&repo,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
    match stage{0=>{Options::prepare_json(&bound,&wire(&v)?,Default::default(),Default::default(),5)?;},1=>{out.verify(&bound,5)?;},_=>{out.with_verified_json(&bound,5,|_|())?;}}
    let calls=repo.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);repo.repository().calls.store(0,Ordering::SeqCst);repo.repository().trigger.store(calls,Ordering::SeqCst);let called=Cell::new(false);
    match stage{0=>assert!(Options::prepare_json(&bound,&wire(&v)?,Default::default(),Default::default(),6).is_err()),1=>assert!(out.verify(&bound,6).is_err()),_=>assert!(out.with_verified_json(&bound,6,|_|called.set(true)).is_err())}
    assert!(!called.get());assert_eq!(repo.repository().calls.load(Ordering::SeqCst),calls);Ok(())
}
#[test]fn final_head_race_in_preview_preparation_rejects()->R{race_options(true,0)}
#[test]fn final_head_race_in_preview_verification_rejects()->R{race_options(true,1)}
#[test]fn final_head_race_in_preview_json_delivery_blocks_consumer()->R{race_options(true,2)}
#[test]fn final_head_race_in_mutation_preparation_rejects()->R{race_options(false,0)}
#[test]fn final_head_race_in_mutation_verification_rejects()->R{race_options(false,1)}
#[test]fn final_head_race_in_mutation_metadata_delivery_blocks_consumer()->R{race_options(false,2)}
