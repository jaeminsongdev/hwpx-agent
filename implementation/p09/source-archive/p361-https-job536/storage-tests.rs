//! Synthetic route/scanner/policy repository; actual original engine/AEAD/CAS primitives. Not a product route.
use super::*;
use super::requests::{budget,raw,allowed};
use std::cell::Cell;
use domain_ir::{Architecture,BackendHealth,BackendHealthState,BackendId,BackendKind,CapabilityId,CapabilityRouteCatalog,ExactTargetProfile,
    PolicyScope,PreservationImpact,PreservationRequirement,ProtectionState,RegistryTrustState,RouteBinding,RouteContext,SignatureImpact,SupportState,TargetProfileId,TransactionId};
use hwpx_agent_cli::{form_product_request::stored_operations::{StoredProductRequest as Entry,https_targets::{HTTPS_TARGET_PRODUCT_REQUEST_SCHEMA,
    routing::{PreparedHttpsTargetExecutionManifest as Manifest,HTTPS_TARGET_STORAGE_PROFILE}}},stored_revision_commit::{StoredResultRevisionCas,StoredCommitError,StoredPrecommitGuard,
    job::identity::StoredJobPolicy}};
use operation_engine::{OutputValidator,ValidationOutcome,WorkspaceTransaction,FaultPlan};
fn routing(cap:&str,now:u64,mode:u8)->Result<(RouteContext,CapabilityRouteCatalog),Box<dyn Error>>{
    let backend=BackendId::parse("synthetic-https-storage-direct")?;
    let target=ExactTargetProfile::new(TargetProfileId::parse("synthetic-https-storage-target")?,if mode==1{"11.0.0.9999"}else{"11.0.0.9136"},Architecture::X86)?;
    let digest=if mode==2{[8;32]}else{[7;32]};let generation=if mode==3{2}else{1};
    let context=RouteContext::new(target.clone(),digest,1,RegistryTrustState::SignatureVerified,PolicyScope::CurrentPcPersonalLocalDevelopment,
        PreservationRequirement::Exact,ProtectionState::Unprotected,now*1000,
        vec![BackendHealth::new(backend.clone(),BackendHealthState::Healthy,generation,now*1000,10_000)])?;
    let binding=RouteBinding::new(CapabilityId::parse(if mode==5{"ref.hyperlink_insert"}else{cap})?,backend,BackendKind::DirectHwpx,SupportState::Verified,target,digest,1,10,1,PreservationImpact::Exact,SignatureImpact::Preserved);
    Ok((context,CapabilityRouteCatalog::from_bindings(vec![binding])?))
}
fn manifest(f:&StoredFixture,p:&Provider<'_>,bytes:&[u8],repo:&Repository)->Result<Manifest,Box<dyn Error>>{
    let product=Entry::prepare_https_targets_json(p,repo,&serde_json::to_vec(&raw(f,bytes)?)?,budget()?,10)?;
    let(c,r)=routing("ref.hyperlink_edit",11,0)?;Ok(product.prepare_execution_manifest(p,repo,&c,&r,TransactionId::parse("https-storage-transaction")?,11)?)
}
#[test]
fn captured_manifest_binds_current_source_output_identity_and_common_unclaimed_job_without_writes()->TestResult{
    let bytes=fixture::captured()?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let actor=write_context(&f);let p=writable(&f,&actor)?;
    let source=p.import_actual_forms(f.head,9)?;let repo=allowed(&f,&source)?;let out=manifest(&f,&p,&bytes,&repo)?;let(c,r)=routing("ref.hyperlink_edit",11,0)?;
    assert_eq!(out.verify(&p,&repo,&c,&r,11)?,out.manifest());assert!(out.require_current_product_route(&p,&repo,&c,&r,11).is_err());
    assert_eq!(out.manifest().source_artifact_id().as_str(),f.result.public_id());
    out.with_verified_storage_preparation(&p,&repo,&c,&r,11,|input|->TestResult{
        assert_eq!(input.source_bytes(),bytes);assert_ne!(input.output_bytes(),bytes);assert_eq!(input.manifest(),out.manifest());
        assert_eq!(input.receipt().profile,HTTPS_TARGET_STORAGE_PROFILE);assert_eq!(input.receipt().request_schema,HTTPS_TARGET_PRODUCT_REQUEST_SCHEMA);
        assert!(!input.receipt().validation_executed&&!input.receipt().execution_or_native_authority);
        assert_ne!(input.job_identity().key(),input.job_identity().job());assert_ne!(input.job_identity().job(),input.job_identity().request());
        let job=input.prepare_bound_job(StoredJobPolicy::default(),revision_service::CommitId::generate(),revision_service::RevisionId::generate(),Default::default())?;
        assert!(!format!("{job:?}{input:?}{out:?}").contains("PRIVATE"));
        assert!(input.commit_binding(revision_service::CommitId::generate(),f.head.revision_id().ok_or("head")?).is_err());Ok(())
    })??;
    assert_eq!(f.revisions.head(&f.revision_context,f.project,f.branch)?,f.head);
    assert_eq!(f.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),3);Ok(())
}
#[test]
fn captured_output_flows_through_original_workspace_validator_actual_aead_and_revision_cas()->TestResult{
    let bytes=fixture::captured()?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let actor=write_context(&f);let p=writable(&f,&actor)?;
    let source=p.import_actual_forms(f.head,9)?;let repo=allowed(&f,&source)?;let out=manifest(&f,&p,&bytes,&repo)?;let(c,r)=routing("ref.hyperlink_edit",11,0)?;
    assert!(out.require_current_product_route(&p,&repo,&c,&r,11).is_err());let root=tempfile::tempdir()?;
    out.with_verified_storage_preparation(&p,&repo,&c,&r,11,|input|->TestResult{
        let revision=revision_service::RevisionId::generate();let calls=Cell::new(0);
        let mut cas=StoredResultRevisionCas::bind(&f.artifacts,&f.revisions,&actor,&f.revision_context,
            input.commit_binding(revision_service::CommitId::generate(),revision)?,||12)?;
        cas.require_precommit_guard(Box::new(out.current_commit_guard(&p,&repo,||{calls.set(calls.get()+1);let(c,r)=routing("ref.hyperlink_edit",12,0).map_err(|_|())?;Ok((c,r,12))})))?;
        let mut validator=input.output_validator();let mut tx=WorkspaceTransaction::create(root.path().join("https-owned"),input.manifest().clone(),Default::default())?;
        assert!(tx.execute_bytes(input.source_bytes(),input.output_bytes(),&mut validator,&mut cas,&mut FaultPlan::none()).is_ok());
        assert_eq!(calls.get(),2);assert!(cas.error().is_none());let saved=cas.retained_result().ok_or("saved")?;
        let saved=f.artifacts.download(&actor,saved.artifact_id,13)?;assert_eq!(saved,input.output_bytes());
        assert_eq!(output_uris(&saved,"actual-form-document")?,vec![Some("https://example.org/public?x=1&y=2".into())]);
        assert_eq!(f.revisions.head(&f.revision_context,f.project,f.branch)?.revision_id(),Some(revision));
        assert_eq!(validator.validate(input.output_bytes()),ValidationOutcome::Failed);Ok(())
    })??;
    assert_eq!(f.artifacts.download(&f.reader,f.result,13)?,bytes);Ok(())
}
#[test]
fn one_shot_shared_validator_rejects_modified_output_and_never_promotes_contract_to_validation()->TestResult{
    let bytes=fixture::package(&link(1,"https://example.org/old"))?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let actor=write_context(&f);let p=writable(&f,&actor)?;
    let source=p.import_actual_forms(f.head,9)?;let repo=allowed(&f,&source)?;let out=manifest(&f,&p,&bytes,&repo)?;let(c,r)=routing("ref.hyperlink_edit",11,0)?;
    out.with_verified_storage_preparation(&p,&repo,&c,&r,11,|input|->TestResult{
        let mut corrupted=input.output_bytes().to_vec();corrupted[0]^=1;let mut bad=input.output_validator();assert_eq!(bad.validate(&corrupted),ValidationOutcome::Rejected);
        assert_eq!(bad.validate(input.output_bytes()),ValidationOutcome::Failed);let mut good=input.output_validator();assert_eq!(good.validate(input.output_bytes()),ValidationOutcome::Valid);
        assert_eq!(good.validate(input.output_bytes()),ValidationOutcome::Failed);assert!(!input.receipt().validation_executed);Ok(())
    })??;Ok(())
}
#[test]
fn retained_manifest_denies_current_target_registry_health_time_or_capability_drift_before_storage()->TestResult{
    let bytes=fixture::package(&link(1,"https://example.org/old"))?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let actor=write_context(&f);let p=writable(&f,&actor)?;
    let source=p.import_actual_forms(f.head,9)?;let repo=allowed(&f,&source)?;let out=manifest(&f,&p,&bytes,&repo)?;
    for mode in 1..=5{let(c,r)=routing("ref.hyperlink_edit",11,mode)?;let mut consumed=false;
        assert!(out.with_verified_storage_preparation(&p,&repo,&c,&r,if mode==4{12}else{11},|_|consumed=true).is_err(),"drift {mode}");assert!(!consumed);}
    Ok(())
}
#[test]
fn current_policy_guard_refreshes_and_latches_after_first_revocation_without_retry()->TestResult{
    let bytes=fixture::package(&link(1,"https://example.org/old"))?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let actor=write_context(&f);let p=writable(&f,&actor)?;
    let source=p.import_actual_forms(f.head,9)?;let repo=allowed(&f,&source)?;let out=manifest(&f,&p,&bytes,&repo)?;let calls=Cell::new(0);
    let mut guard=out.current_commit_guard(&p,&repo,||{calls.set(calls.get()+1);let(c,r)=routing("ref.hyperlink_edit",12,0).map_err(|_|())?;Ok((c,r,12))});
    guard.check()?;repo.deny_after.store(0,Ordering::SeqCst);assert_eq!(guard.check(),Err(StoredCommitError::CurrentGuard));
    let repo_calls=repo.calls.load(Ordering::SeqCst);repo.deny_after.store(usize::MAX,Ordering::SeqCst);
    assert_eq!(guard.check(),Err(StoredCommitError::CurrentGuard));assert_eq!(calls.get(),2);assert_eq!(repo.calls.load(Ordering::SeqCst),repo_calls);Ok(())
}
#[test]
fn policy_revocation_between_ingest_and_cas_preserves_original_head_and_retained_result()->TestResult{
    let bytes=fixture::package(&link(1,"https://example.org/old"))?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let actor=write_context(&f);let p=writable(&f,&actor)?;
    let source=p.import_actual_forms(f.head,9)?;let repo=allowed(&f,&source)?;let out=manifest(&f,&p,&bytes,&repo)?;let(c,r)=routing("ref.hyperlink_edit",11,0)?;let root=tempfile::tempdir()?;
    out.with_verified_storage_preparation(&p,&repo,&c,&r,11,|input|->TestResult{
        let calls=Cell::new(0);let mut cas=StoredResultRevisionCas::bind(&f.artifacts,&f.revisions,&actor,&f.revision_context,
            input.commit_binding(revision_service::CommitId::generate(),revision_service::RevisionId::generate())?,||12)?;
        cas.require_precommit_guard(Box::new(out.current_commit_guard(&p,&repo,||{calls.set(calls.get()+1);if calls.get()==2{repo.deny_after.store(0,Ordering::SeqCst);}
            let(c,r)=routing("ref.hyperlink_edit",12,0).map_err(|_|())?;Ok((c,r,12))})))?;
        let mut validator=input.output_validator();let mut tx=WorkspaceTransaction::create(root.path().join("https-revoked"),input.manifest().clone(),Default::default())?;
        assert!(tx.execute_bytes(input.source_bytes(),input.output_bytes(),&mut validator,&mut cas,&mut FaultPlan::none()).is_err());
        assert_eq!(cas.error(),Some(StoredCommitError::CurrentGuard));assert_eq!(calls.get(),2);
        assert_eq!(f.revisions.head(&f.revision_context,f.project,f.branch)?,f.head);
        let saved=cas.retained_result().ok_or("retain ingested result")?;assert_eq!(f.artifacts.download(&actor,saved.artifact_id,13)?,input.output_bytes());Ok(())
    })??;Ok(())
}
fn existing_literal_scope(paragraph_scope:bool)->TestResult{
    use hwpx_agent_cli::form_product_request::{stored_literal_replacement::LITERAL_REPLACEMENT_PRODUCT_REQUEST_SCHEMA,
        stored_operations::search_mutations::SearchMutationLimits};
    let bytes=fixture::package("<hp:p id='1'><hp:run><hp:t>K K</hp:t></hp:run></hp:p>")?;
    let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let actor=write_context(&f);let p=writable(&f,&actor)?;let source=p.import_actual_forms(f.head,9)?;
    let handles=if paragraph_scope{vec![source.imported().graph().sections()[0].body.children[0].common().source_anchor.as_ref().ok_or("paragraph")?.opaque_handle.clone()]}else{vec![]};
    let raw=serde_json::json!({"schema_version":LITERAL_REPLACEMENT_PRODUCT_REQUEST_SCHEMA,"idempotency_key":"existing-search-shared-storage",
        "project_id":f.project.public_id(),"document_id":"actual-form-document","base_revision":f.head.revision_id().ok_or("head")?.public_id(),
        "expected_head_generation":f.head.generation(),"expected_source_package_sha256":hex::encode(Sha256::digest(&bytes)),"plan_id":"existing-literal-plan",
        "scope":{"kind":if paragraph_scope{"paragraphs"}else{"mapped_document"},"paragraph_handles":handles},
        "operation":{"kind":"replace_literal","query":"K","replacement":"X","case_sensitive":true,"whole_word":false,"max_replacements":10,"run_policy":"first_original_run_retain_all_runs"}});
    let compiled=Entry::prepare_compiled_search_json(&p,&serde_json::to_vec(&raw)?,SearchMutationLimits::standard()?,10)?;
    let cap=compiled.receipt().capability_id;let(c,r)=routing(cap,11,0)?;let out=compiled.prepare_execution_manifest(&p,&c,&r,TransactionId::parse("existing-search-shared-transaction")?,11)?;
    assert!(out.require_current_product_route(&p,&c,&r,11).is_err());let root=tempfile::tempdir()?;
    out.with_verified_storage_preparation(&p,&c,&r,11,|input|->TestResult{
        let mut cas=StoredResultRevisionCas::bind(&f.artifacts,&f.revisions,&actor,&f.revision_context,
            input.commit_binding(revision_service::CommitId::generate(),revision_service::RevisionId::generate())?,||12)?;
        cas.require_precommit_guard(Box::new(out.current_commit_guard(&p,||{let(c,r)=routing(cap,12,0).map_err(|_|())?;Ok((c,r,12))})))?;
        let mut validator=input.output_validator();let mut tx=WorkspaceTransaction::create(root.path().join("existing-search"),input.manifest().clone(),Default::default())?;
        assert!(tx.execute_bytes(input.source_bytes(),input.output_bytes(),&mut validator,&mut cas,&mut FaultPlan::none()).is_ok());
        let saved=cas.retained_result().ok_or("saved")?;assert_eq!(f.artifacts.download(&actor,saved.artifact_id,13)?,input.output_bytes());Ok(())
    })??;Ok(())
}
#[test]fn shared_search_storage_still_commits_original_mapped_scope()->TestResult{existing_literal_scope(false)}
#[test]fn shared_search_storage_still_commits_original_paragraph_scope()->TestResult{existing_literal_scope(true)}
