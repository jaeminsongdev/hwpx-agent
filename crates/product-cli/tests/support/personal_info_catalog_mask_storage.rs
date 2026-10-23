// Original candidate -> real HWPX validator -> original workspace/storage primitives.
// In-memory repositories/scanner/key fixture; not SQL durability, a trusted registry or a product execution route.
mod guard{include!("personal_info_catalog_mask_commit_guard.rs");}
mod identity{include!("personal_info_catalog_mask_job_identity.rs");}
mod lookup{include!("personal_info_catalog_request_lookup.rs");}
use super::*;
use hwpx_agent_cli::{stored_revision_commit::{StoredResultRevisionCas,job::StoredJobOptions},
    form_product_request::stored_operations::compiled_search::catalog_mask::routing::storage::CatalogMaskStorageError as SError};
use operation_engine::{OutputValidator,ValidationOutcome,WorkspaceTransaction,FaultPlan,TransactionError};
fn options(canonical:&str,route_set:[u8;32])->Result<StoredJobOptions,Box<dyn Error>>{
    Ok(StoredJobOptions{key:Uuid::from_u128(7701),job:Uuid::from_u128(7702),request:Uuid::from_u128(7703),request_sha:ContentDigest::parse(canonical)?,
        capability_sha:ContentDigest::parse(&hex::encode(route_set))?,max_attempts:3,base_delay_seconds:1,max_delay_seconds:60,ttl_seconds:600})
}
#[test]
fn source_output_manifest_and_validation_contract_come_only_from_original_owner()->R{
    let bytes=raw("KEEP MARK END")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=manifest(&p,&f,&req(&s,&bytes,&f,false)?)?;
    let(context,routes)=route(6,0)?;out.with_verified_storage_preparation(&p,&f,&context,&routes,6,|input|->R{
        assert_eq!(input.source_bytes(),bytes);assert_eq!(input.manifest(),out.manifest());assert_ne!(input.source_bytes(),input.output_bytes());
        assert_eq!(ContentDigest::of(input.output_bytes()).as_bytes(),&input.receipt().output_package_sha256);
        assert_eq!(input.receipt().catalog_sha256,sha(&f));assert!(!input.receipt().execution_or_native_authority&&!input.receipt().validation_executed);
        assert!(section(input.output_bytes())?.contains("KEEP **** END"));Ok(())
    })??;Ok(())
}
#[test]
fn real_hwp_import_and_review_readback_validate_once_without_mask_replay()->R{
    let bytes=raw("KEEP MARK END")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=manifest(&p,&f,&req(&s,&bytes,&f,false)?)?;
    let(context,routes)=route(6,0)?;out.with_verified_storage_preparation(&p,&f,&context,&routes,6,|input|{
        let reads=f.reads.get();let mut validator=input.output_validator();assert_eq!(validator.validate(input.output_bytes()),ValidationOutcome::Valid);
        assert_eq!(validator.validate(input.output_bytes()),ValidationOutcome::Failed);assert_eq!(f.reads.get(),reads);
    })?;Ok(())
}
#[test]
fn mismatched_size_corruption_source_and_other_candidate_are_never_valid_output()->R{
    let bytes=raw("KEEP MARK END")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=manifest(&p,&f,&req(&s,&bytes,&f,false)?)?;
    let(context,routes)=route(6,0)?;out.with_verified_storage_preparation(&p,&f,&context,&routes,6,|input|{
        let mut changed=input.output_bytes().to_vec();changed[10]^=1;
        for proposed in [&[][..],input.source_bytes(),&changed,input.output_bytes().get(..10).unwrap_or_default()]{
            let mut validator=input.output_validator();assert_eq!(validator.validate(proposed),ValidationOutcome::Rejected);
            assert_eq!(validator.validate(input.output_bytes()),ValidationOutcome::Failed);}
    })?;Ok(())
}
#[test]
fn whole_encrypted_artifact_ingest_and_revision_cas_use_actual_hwpx_validator()->R{
    let bytes=raw("KEEP MARK END")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=manifest(&p,&f,&req(&s,&bytes,&f,false)?)?;
    let(context,routes)=route(6,0)?;let root=tempfile::tempdir()?;
    out.with_verified_storage_preparation(&p,&f,&context,&routes,6,|input|->R{
        let new_revision=rev::RevisionId::generate();let binding=input.commit_binding(rev::CommitId::generate(),new_revision)?;
        let mut cas=StoredResultRevisionCas::bind(&s.artifacts,&s.revisions,&actor,&s.revision_context,binding,||7)?;
        let mut validator=input.output_validator();let mut tx=WorkspaceTransaction::create(root.path().join("actual-hwpx"),input.manifest().clone(),Default::default())?;
        let result=tx.execute_bytes(input.source_bytes(),input.output_bytes(),&mut validator,&mut cas,&mut FaultPlan::none());
        assert!(result.is_ok(),"source-bound transaction rejected");assert!(cas.error().is_none());
        let saved=cas.retained_result().ok_or("saved")?;assert_eq!(s.artifacts.download(&actor,saved.artifact_id,8)?,input.output_bytes());
        assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?.revision_id(),Some(new_revision));
        assert_eq!(s.artifacts.download(&s.reader,s.result,8)?,bytes);Ok(())
    })??;Ok(())
}
#[test]
fn rejected_proposed_bytes_never_reach_revision_cas_or_artifact_ingest()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=manifest(&p,&f,&req(&s,&bytes,&f,false)?)?;
    let(context,routes)=route(6,0)?;let root=tempfile::tempdir()?;
    out.with_verified_storage_preparation(&p,&f,&context,&routes,6,|input|->R{
        let mut changed=input.output_bytes().to_vec();changed[10]^=1;let called=Cell::new(false);let mut validator=input.output_validator();
        let mut tx=WorkspaceTransaction::create(root.path().join("rejected"),input.manifest().clone(),Default::default())?;
        let result=tx.execute_bytes(input.source_bytes(),&changed,&mut validator,&mut |_:&operation_engine::RevisionCommitRequest|{called.set(true);operation_engine::RevisionCasOutcome::Failed},&mut FaultPlan::none());
        assert_eq!(result.err().ok_or("failure")?.primary(),TransactionError::ValidationRejected);assert!(!called.get());
        assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);Ok(())
    })??;Ok(())
}
#[test]
fn prepared_job_binds_original_source_head_output_canonical_request_and_routes()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=manifest(&p,&f,&req(&s,&bytes,&f,false)?)?;
    let(context,routes)=route(6,0)?;out.with_verified_storage_preparation(&p,&f,&context,&routes,6,|input|->R{
        let prepared=input.prepare_job(options(&out.compiled_receipt().canonical_request_sha256,input.manifest().route_set_sha256())?,rev::CommitId::generate(),rev::RevisionId::generate(),Default::default())?;
        let claim=prepared.claim().input();assert_eq!(claim.project,s.project);assert_eq!(claim.branch,s.branch);assert_eq!(claim.expected_head,s.head);assert_eq!(claim.source,s.result);
        assert_eq!(claim.effect_sha,ContentDigest::of(input.output_bytes()));assert_eq!(claim.manifest_sha.as_bytes(),&input.manifest().canonical_sha256()?);Ok(())
    })??;assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);Ok(())
}
#[test]
fn caller_request_route_digest_and_old_revision_cannot_rebind_job_preparation()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=manifest(&p,&f,&req(&s,&bytes,&f,false)?)?;
    let(context,routes)=route(6,0)?;out.with_verified_storage_preparation(&p,&f,&context,&routes,6,|input|->R{
        for mode in 0..2{let mut opts=options(&out.compiled_receipt().canonical_request_sha256,input.manifest().route_set_sha256())?;
            if mode==0{opts.request_sha=ContentDigest::of(b"forged");}else{opts.capability_sha=ContentDigest::of(b"forged");}
            assert!(matches!(input.prepare_job(opts,rev::CommitId::generate(),rev::RevisionId::generate(),Default::default()),Err(SError::Binding)));}
        assert!(matches!(input.commit_binding(rev::CommitId::generate(),s.head.revision_id().ok_or("head")?),Err(SError::Binding)));Ok(())
    })??;Ok(())
}
#[test]
fn changed_catalog_read_failure_and_final_race_stop_storage_consumer()->R{
    for mode in 0..3{let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=manifest(&p,&f,&req(&s,&bytes,&f,false)?)?;
        match mode{0=>f.fail.set(true),1=>f.raw.borrow_mut()[2]^=1,_=>f.replace_at.set(f.reads.get()+4)}
        let(context,routes)=route(6,0)?;let called=Cell::new(false);assert!(out.with_verified_storage_preparation(&p,&f,&context,&routes,6,|_|called.set(true)).is_err());assert!(!called.get());}Ok(())
}
#[test]
fn current_acl_quarantine_and_aead_block_storage_preparation()->R{
    for mode in 0..3{let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=manifest(&p,&f,&req(&s,&bytes,&f,false)?)?;
        match mode{0=>{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),6)?;},1=>{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("STORAGE_BINDING")?,6)?;},_=>s.blobs.tamper.store(true,Ordering::SeqCst)}
        let(context,routes)=route(7,0)?;let called=Cell::new(false);assert!(out.with_verified_storage_preparation(&p,&f,&context,&routes,7,|_|called.set(true)).is_err());assert!(!called.get());}Ok(())
}
#[test]
fn storage_preparation_and_receipt_never_open_product_execution_route()->R{
    let bytes=raw("PRIVATE-MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("PRIVATE-MARK");let out=manifest(&p,&f,&req(&s,&bytes,&f,false)?)?;
    let(context,routes)=route(6,0)?;out.with_verified_storage_preparation(&p,&f,&context,&routes,6,|input|->R{
        let text=format!("{input:?}{:?}{:?}{}",input.receipt(),input.output_validator(),serde_json::to_string(input.receipt())?);
        assert!(!text.contains("PRIVATE-MARK")&&!text.contains("pattern0="));assert!(!input.receipt().execution_or_native_authority&&!input.receipt().validation_executed);Ok(())
    })??;assert!(out.require_current_product_route(&p,&f,&context,&routes,6).is_err());Ok(())
}
#[test]
fn scanner_unverified_output_prevents_actual_revision_commit()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=manifest(&p,&f,&req(&s,&bytes,&f,false)?)?;
    let blocked=fixture_artifacts(s.metadata.clone(),s.blobs.clone(),true)?;let(context,routes)=route(6,0)?;let root=tempfile::tempdir()?;
    out.with_verified_storage_preparation(&p,&f,&context,&routes,6,|input|->R{
        let mut cas=StoredResultRevisionCas::bind(&blocked,&s.revisions,&actor,&s.revision_context,input.commit_binding(rev::CommitId::generate(),rev::RevisionId::generate())?,||7)?;
        let mut validator=input.output_validator();let mut tx=WorkspaceTransaction::create(root.path().join("scanner-block"),input.manifest().clone(),Default::default())?;
        assert!(tx.execute_bytes(input.source_bytes(),input.output_bytes(),&mut validator,&mut cas,&mut FaultPlan::none()).is_err());
        assert!(cas.error().is_some());assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);Ok(())
    })??;Ok(())
}
#[test]
fn final_head_race_after_extra_source_borrow_blocks_storage_consumer()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=manifest(&p,&f,&req(&s,&bytes,&f,false)?)?;
    let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),
        artifact_service::ArtifactId::generate(),s.result,None,ContentDigest::of(b"storage-final-head"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation"),ContentDigest::of(b"transaction"))?;
    let repo=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
    let bound=StoredFormProvider::bind(&s.artifacts,&repo,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
    let(context,routes)=route(6,0)?;out.with_verified_storage_preparation(&bound,&f,&context,&routes,6,|_|())?;
    let count=repo.repository().calls.load(Ordering::SeqCst);assert!(count>=7);repo.repository().calls.store(0,Ordering::SeqCst);repo.repository().trigger.store(count,Ordering::SeqCst);
    let called=Cell::new(false);assert!(out.with_verified_storage_preparation(&bound,&f,&context,&routes,6,|_|called.set(true)).is_err());assert!(!called.get());Ok(())
}
#[test]
fn storage_consumer_cannot_rebind_write_scope_or_five_provider_dimensions()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=manifest(&p,&f,&req(&s,&bytes,&f,false)?)?;
    let(context,routes)=route(6,0)?;let called=Cell::new(false);assert!(out.with_verified_storage_preparation(&s.provider()?,&f,&context,&routes,6,|_|called.set(true)).is_err());
    for mode in 0..5{let tenant=if mode==4{TenantId::new(Uuid::from_u128(883))?}else{s.reader.tenant_id()};let subject=if mode==3{SubjectDigest::from_authenticated_subject("foreign-storage")?}else{s.reader.subject()};
        let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);let ctx=rev::RevisionRequestContext::new(tenant,subject);
        let project=if mode==2{rev::ProjectId::parse("prj_70000000000000000000000000000003")?}else{s.project};let branch=if mode==1{rev::BranchId::parse("brn_70000000000000000000000000000003")?}else{s.branch};
        let foreign=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&ctx,project,branch,DocumentId::parse(if mode==0{"foreign"}else{"actual-form-document"})?)?;
        assert!(out.with_verified_storage_preparation(&foreign,&f,&context,&routes,6,|_|called.set(true)).is_err());}assert!(!called.get());Ok(())
}
#[test]
fn equal_output_with_other_request_or_transaction_has_a_distinct_validation_contract()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let v=req(&s,&bytes,&f,false)?;
    let(context,routes)=route(6,0)?;let out=manifest(&p,&f,&v)?;
    let a=out.with_verified_storage_preparation(&p,&f,&context,&routes,6,|input|input.receipt().clone())?;
    let mut other=v;other["idempotency_key"]=json!("other-private-storage-key");let out=manifest(&p,&f,&other)?;
    let b=out.with_verified_storage_preparation(&p,&f,&context,&routes,6,|input|input.receipt().clone())?;
    assert_eq!(a.output_package_sha256,b.output_package_sha256);assert_ne!(a.validation_contract_sha256,b.validation_contract_sha256);
    let out=compile(&p,&f,&other)?.prepare_execution_manifest(&p,&f,&context,&routes,tx("another-storage-transaction")?,6)?;
    let c=out.with_verified_storage_preparation(&p,&f,&context,&routes,6,|input|input.receipt().clone())?;
    assert_eq!(b.output_package_sha256,c.output_package_sha256);assert_ne!(b.validation_contract_sha256,c.validation_contract_sha256);Ok(())
}
