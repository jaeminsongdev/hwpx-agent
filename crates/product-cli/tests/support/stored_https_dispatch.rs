//! Common dispatch uses actual stored ACL/AEAD/source/writer; repository/scanner are test fixtures.
use super::*;
use super::requests::{raw,allowed};
use hwpx_agent_cli::form_product_request::stored_operations::{StoredProductRequest as Entry,PreparedStoredProductOperation as Operation,
    StoredProductOperationError as OE,https_targets::{HttpsTargetProductError as PE,dispatch::PolicyBoundOperationLimits as Limits}};
use hwpx_agent_cli::form_stored_provider::actual_import::https_target_output::compiled::HttpsTargetCompileError as CE;
fn budget()->Result<Limits,Box<dyn Error>>{Ok(Limits::standard()?)}

#[test]
fn common_dispatch_captured_original_policy_bound_compiled_output_and_source_unchanged()->TestResult{
    let bytes=fixture::captured()?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let c=write_context(&f);let p=writable(&f,&c)?;
    let source=p.import_actual_forms(f.head,9)?;let repository=allowed(&f,&source)?;let request=serde_json::to_vec(&raw(&f,&bytes)?)?;
    let before=f.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count();
    let op=Entry::prepare_json_with_https_policy(&p,&repository,&request,None,budget()?,10)?;
    let product=op.as_https_targets().ok_or("HTTPS variant")?;
    assert_eq!(product.receipt().request_schema,hwpx_agent_cli::form_product_request::stored_operations::https_targets::HTTPS_TARGET_PRODUCT_REQUEST_SCHEMA);
    assert!(!product.receipt().idempotency_key_claimed&&!product.receipt().execution_or_publication_authority);
    let out=op.with_verified_bytes_with_https_policy(&p,&repository,None,11,|b|b.to_vec())?;
    assert_eq!(output_uris(&out,"actual-form-document")?,vec![Some("https://example.org/public?x=1&y=2".into())]);
    assert_eq!(f.artifacts.download(&f.reader,f.result,12)?,bytes);assert_eq!(f.revisions.head(&f.revision_context,f.project,f.branch)?,f.head);
    assert_eq!(f.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),before);
    let debug=format!("{op:?}");assert!(!debug.contains("https://")&&!debug.contains("PRIVATE"));Ok(())
}
#[test]
fn common_no_policy_apis_still_refuse_https_without_read_or_callback()->TestResult{
    let bytes=fixture::package(&link(1,"https://example.org/old"))?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let c=write_context(&f);let p=writable(&f,&c)?;
    let source=p.import_actual_forms(f.head,9)?;let repository=allowed(&f,&source)?;let request=serde_json::to_vec(&raw(&f,&bytes)?)?;
    let op=Entry::prepare_json_with_https_policy(&p,&repository,&request,None,budget()?,10)?;
    let count=repository.calls.load(Ordering::SeqCst);let before=f.metadata.audit_events()?.len();let mut consumed=false;
    assert!(matches!(Entry::prepare_json(&p,&request,None,11),Err(OE::PolicyRepositoryRequired)));
    assert!(matches!(op.with_verified_bytes(&p,None,11,|_|consumed=true),Err(OE::PolicyRepositoryRequired)));
    assert!(matches!(op.require_current_product_route(&p,None,11),Err(OE::PolicyRepositoryRequired)));
    assert!(matches!(op.with_verified_preview_json(&p,None,11,|_|consumed=true),Err(OE::PreviewKind)));
    assert!(!consumed);assert_eq!(repository.calls.load(Ordering::SeqCst),count);assert_eq!(f.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn common_strict_rejection_precedes_source_and_repository_reads()->TestResult{
    let bytes=fixture::package(&link(1,"https://example.org/old"))?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let c=write_context(&f);let p=writable(&f,&c)?;
    let source=p.import_actual_forms(f.head,9)?;let repository=allowed(&f,&source)?;let original=raw(&f,&bytes)?;let before=f.metadata.audit_events()?.len();
    f.blobs.tamper.store(true,Ordering::SeqCst);
    for i in 0..8{let mut value=original.clone();match i{0=>value["policy_artifact"]="caller-selected".into(),1=>value["operation"]["permit"]=true.into(),
        2=>value["operation"]["changes"][0]["target"]["uri"]="http://unsafe.example".into(),3=>value["operation"]["changes"]=serde_json::json!([]),
        4=>value["operation"]=serde_json::json!([]),5=>value["schema_version"]="unknown".into(),_=>{}}
        let mut wire=serde_json::to_vec(&value)?;
        if i==6{let mut duplicate=b"{\"plan_id\":\"duplicate\",".to_vec();duplicate.extend_from_slice(&wire[1..]);wire=duplicate;}
        if i==7{wire.extend_from_slice(b" {}");}
        assert!(Entry::prepare_json_with_https_policy(&p,&repository,&wire,None,budget()?,10).is_err());
    }assert_eq!(repository.calls.load(Ordering::SeqCst),0);assert_eq!(f.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn common_delivery_refreshes_current_source_policy_and_authenticated_write_scope()->TestResult{
    for mode in 0..4{let bytes=fixture::package(&link(1,"https://example.org/old"))?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let c=write_context(&f);let p=writable(&f,&c)?;
        let source=p.import_actual_forms(f.head,9)?;let repository=allowed(&f,&source)?;let raw=serde_json::to_vec(&raw(&f,&bytes)?)?;
        let op=Entry::prepare_json_with_https_policy(&p,&repository,&raw,None,budget()?,10)?;let read=f.provider()?;
        match mode{0=>repository.deny_after.store(0,Ordering::SeqCst),1=>{f.artifacts.set_permissions(&f.owner,f.result,f.reader.subject(),BTreeSet::new(),11)?;},
            2=>{f.artifacts.set_permissions(&f.owner,repository.row.lock().map_err(|_|"row")?.artifact,f.reader.subject(),BTreeSet::new(),11)?;},_=>{}}
        let mut consumed=false;assert!(op.with_verified_bytes_with_https_policy(if mode==3{&read}else{&p},&repository,None,12,|_|consumed=true).is_err());assert!(!consumed);
    }Ok(())
}
#[test]
fn common_stale_head_foreign_scope_or_source_digest_never_reaches_policy()->TestResult{
    let bytes=fixture::package(&link(1,"https://example.org/old"))?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let c=write_context(&f);let p=writable(&f,&c)?;
    let source=p.import_actual_forms(f.head,9)?;let repository=allowed(&f,&source)?;let original=raw(&f,&bytes)?;
    for i in 0..3{let mut value=original.clone();match i{0=>value["document_id"]="foreign-document".into(),1=>value["expected_head_generation"]=2.into(),_=>value["expected_source_package_sha256"]="0".repeat(64).into()}
        assert!(Entry::prepare_json_with_https_policy(&p,&repository,&serde_json::to_vec(&value)?,None,budget()?,10).is_err());
    }assert_eq!(repository.calls.load(Ordering::SeqCst),0);Ok(())
}
#[test]
fn common_legacy_form_dispatch_retains_binding_error_without_https_policy_lookup()->TestResult{
    let bytes=fixture::package(&link(1,"https://example.org/old"))?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let c=write_context(&f);let p=writable(&f,&c)?;
    let source=p.import_actual_forms(f.head,9)?;let repository=allowed(&f,&source)?;
    let mut request=raw(&f,&bytes)?;let fields=request.as_object_mut().ok_or("request object")?;
    fields.remove("operation");fields.insert("schema_version".into(),serde_json::json!(hwpx_agent_cli::form_product_request::FORM_PRODUCT_REQUEST_SCHEMA));
    fields.insert("form_input".into(),serde_json::json!({}));let request=serde_json::to_vec(&request)?;
    let before=f.metadata.audit_events()?.len();assert!(matches!(Entry::prepare_json(&p,&request,None,10),Err(OE::Bindings)));
    assert!(matches!(Entry::prepare_json_with_https_policy(&p,&repository,&request,None,budget()?,10),Err(OE::Bindings)));
    assert_eq!(repository.calls.load(Ordering::SeqCst),0);assert_eq!(f.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn common_current_route_still_returns_original_unqualified_after_fresh_policy()->TestResult{
    let bytes=fixture::package(&link(1,"https://example.org/old"))?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let c=write_context(&f);let p=writable(&f,&c)?;
    let source=p.import_actual_forms(f.head,9)?;let repository=allowed(&f,&source)?;let wire=serde_json::to_vec(&raw(&f,&bytes)?)?;
    let op=Entry::prepare_json_with_https_policy(&p,&repository,&wire,None,budget()?,10)?;let count=repository.calls.load(Ordering::SeqCst);
    assert!(matches!(op.require_current_product_route_with_https_policy(&p,&repository,None,11),Err(OE::HttpsTargets(PE::Compiler(CE::Stored(E::RouteUnqualified))))));
    assert!(repository.calls.load(Ordering::SeqCst)>count);let Operation::HttpsTargets(product)=op else{return Err("variant".into())};
    assert!(!product.receipt().execution_or_publication_authority);Ok(())
}
