//! Common dispatch integration, not a second observer/compiler/executor implementation.
use super::*;
use hwpx_agent_cli::form_product_request::stored_operations::https_targets::dispatch::{
    PolicyBoundOperationLimits,recovery::PolicyBoundRequestEntry};
fn limits()->Result<PolicyBoundOperationLimits,Box<dyn Error>>{Ok(PolicyBoundOperationLimits::standard()?)}

#[test]
fn existing_terminal_or_in_progress_is_observed_without_source_policy_compile_or_claim()->TestResult{
    for mode in[1,4]{
        let bytes=small()?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let c=write_context(&f);let p=writable(&f,&c)?;
        let source=p.import_actual_forms(f.head,9)?;let repository=allowed(&f,&source)?;
        let revisions=rev::RevisionService::new(Model::new(&f,mode));
        let provider=StoredFormProvider::bind(&f.artifacts,&revisions,&c,&f.revision_context,f.project,f.branch,DocumentId::parse("actual-form-document")?)?;
        let request=wire(&raw(&f,&bytes)?)?;let before=f.metadata.audit_events()?.len();
        f.blobs.tamper.store(true,Ordering::SeqCst);repository.deny_after.store(0,Ordering::SeqCst);
        let entry=Entry::prepare_json_or_observe_with_https_policy(&provider,&repository,&request,None,limits()?,10)?;
        let debug=format!("{entry:?}");assert!(debug.contains("observation_only"));assert!(!debug.contains("https://")&&!debug.contains("https-request-key"));
        let PolicyBoundRequestEntry::ExistingHttps(job)=entry else{return Err("existing required".into())};
        assert_eq!(job.outcome(),StoredJobOutcome::Replay);
        assert_eq!(repository.calls.load(Ordering::SeqCst),0);assert_eq!(revisions.repository().calls.heads.load(Ordering::SeqCst),0);
        assert_eq!(revisions.repository().calls.commits.load(Ordering::SeqCst),0);assert_eq!(revisions.repository().calls.lookups.lock().map_err(|_|"rows")?.len(),1);
        assert_eq!(f.metadata.audit_events()?.len(),before);
    }Ok(())
}

#[test]
fn conflict_unknown_outcome_and_repository_failure_never_fall_back_to_preparation()->TestResult{
    for mode in[2,3,5]{
        let bytes=small()?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let c=write_context(&f);let p=writable(&f,&c)?;
        let source=p.import_actual_forms(f.head,9)?;let repository=allowed(&f,&source)?;let revisions=rev::RevisionService::new(Model::new(&f,mode));
        let provider=StoredFormProvider::bind(&f.artifacts,&revisions,&c,&f.revision_context,f.project,f.branch,DocumentId::parse("actual-form-document")?)?;
        f.blobs.tamper.store(true,Ordering::SeqCst);
        assert!(matches!(Entry::prepare_json_or_observe_with_https_policy(&provider,&repository,&wire(&raw(&f,&bytes)?)?,None,limits()?,10),
            Err(StoredProductOperationError::HttpsTargets(PE::Lookup(_)))));
        assert_eq!(repository.calls.load(Ordering::SeqCst),0);assert_eq!(revisions.repository().calls.heads.load(Ordering::SeqCst),0);
        assert_eq!(revisions.repository().calls.commits.load(Ordering::SeqCst),0);assert_eq!(revisions.repository().calls.lookups.lock().map_err(|_|"rows")?.len(),1);
    }Ok(())
}

#[test]
fn missing_observation_prepares_original_owned_common_product_once_without_publication()->TestResult{
    let bytes=small()?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let c=write_context(&f);let p=writable(&f,&c)?;
    let source=p.import_actual_forms(f.head,9)?;let repository=allowed(&f,&source)?;let revisions=rev::RevisionService::new(Model::new(&f,0));
    let provider=StoredFormProvider::bind(&f.artifacts,&revisions,&c,&f.revision_context,f.project,f.branch,DocumentId::parse("actual-form-document")?)?;
    let PolicyBoundRequestEntry::Prepared(product)=Entry::prepare_json_or_observe_with_https_policy(&provider,&repository,&wire(&raw(&f,&bytes)?)?,None,limits()?,10)?
        else{return Err("original preparation required".into())};
    let https=product.as_https_targets().ok_or("HTTPS operation")?;
    assert!(!https.receipt().idempotency_key_claimed&&!https.receipt().execution_or_publication_authority);
    let output=product.with_verified_bytes_with_https_policy(&provider,&repository,None,11,|v|v.to_vec())?;
    assert_eq!(output_uris(&output,"actual-form-document")?,vec![Some("https://example.org/public?x=1&y=2".into())]);
    assert!(product.require_current_product_route_with_https_policy(&provider,&repository,None,11).is_err());
    assert_eq!(revisions.repository().calls.lookups.lock().map_err(|_|"rows")?.len(),1);
    assert_eq!(revisions.repository().calls.commits.load(Ordering::SeqCst),0);
    assert_eq!(f.artifacts.download(&f.reader,f.result,12)?,bytes);Ok(())
}

#[test]
fn strict_malformed_request_fails_before_lookup_policy_or_source()->TestResult{
    let bytes=small()?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let c=write_context(&f);let p=writable(&f,&c)?;
    let source=p.import_actual_forms(f.head,9)?;let repository=allowed(&f,&source)?;let revisions=rev::RevisionService::new(Model::new(&f,0));
    let provider=StoredFormProvider::bind(&f.artifacts,&revisions,&c,&f.revision_context,f.project,f.branch,DocumentId::parse("actual-form-document")?)?;
    f.blobs.tamper.store(true,Ordering::SeqCst);
    for mode in 0..3{let mut v=raw(&f,&bytes)?;match mode{0=>v["policy_artifact"]="caller-selected".into(),
        1=>v["operation"]["changes"][0]["target"]["uri"]="http://unsafe.example".into(),_=>v["operation"]["changes"]=serde_json::json!([])}
        assert!(Entry::prepare_json_or_observe_with_https_policy(&provider,&repository,&wire(&v)?,None,limits()?,10).is_err());
    }
    assert_eq!(repository.calls.load(Ordering::SeqCst),0);assert_eq!(revisions.repository().calls.heads.load(Ordering::SeqCst),0);
    assert!(revisions.repository().calls.lookups.lock().map_err(|_|"rows")?.is_empty());Ok(())
}

#[test]
fn legacy_family_keeps_original_binding_error_without_https_lookup()->TestResult{
    let bytes=small()?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let c=write_context(&f);let p=writable(&f,&c)?;
    let source=p.import_actual_forms(f.head,9)?;let repository=allowed(&f,&source)?;let revisions=rev::RevisionService::new(Model::new(&f,0));
    let provider=StoredFormProvider::bind(&f.artifacts,&revisions,&c,&f.revision_context,f.project,f.branch,DocumentId::parse("actual-form-document")?)?;
    let mut v=raw(&f,&bytes)?;let object=v.as_object_mut().ok_or("request object")?;object.remove("operation");
    object.insert("schema_version".into(),serde_json::json!(hwpx_agent_cli::form_product_request::FORM_PRODUCT_REQUEST_SCHEMA));
    object.insert("form_input".into(),serde_json::json!({}));
    assert!(matches!(Entry::prepare_json_or_observe_with_https_policy(&provider,&repository,&wire(&v)?,None,limits()?,10),Err(StoredProductOperationError::Bindings)));
    assert_eq!(repository.calls.load(Ordering::SeqCst),0);assert_eq!(revisions.repository().calls.heads.load(Ordering::SeqCst),0);
    assert!(revisions.repository().calls.lookups.lock().map_err(|_|"rows")?.is_empty());Ok(())
}
