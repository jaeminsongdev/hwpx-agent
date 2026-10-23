// Synthetic route evidence + actual immutable source. Never a signed/current registry or executor.
mod storage{include!("personal_info_catalog_mask_storage.rs");}
use super::*;
use domain_ir::{Architecture,BackendHealth,BackendHealthState,BackendId,BackendKind,CapabilityId,CapabilityRouteCatalog,
    CapabilityRouter,CapabilityRouterLimits,ExactTargetProfile,PolicyScope,PreservationImpact,PreservationRequirement,
    ProtectionState,RegistryTrustState,RouteBinding,RouteContext,RouteRestriction,SignatureImpact,SupportState,TargetProfileId,TransactionId};
use hwpx_agent_cli::form_product_request::stored_operations::compiled_search::{routing::SearchManifestError as RE,
    catalog_mask::routing::{PreparedCatalogMaskExecutionManifest as Manifest,CatalogMaskManifestError as M}};
use operation_engine::ExecutionManifest;
#[path="../../../hwpx-package/tests/support/source_protection_fixture.rs"]#[allow(dead_code)]mod security;
fn tx(s:&str)->Result<TransactionId,Box<dyn Error>>{Ok(TransactionId::parse(s)?)}
fn target(build:&str)->Result<ExactTargetProfile,Box<dyn Error>>{Ok(ExactTargetProfile::new(TargetProfileId::parse("synthetic-catalog-target")?,build,Architecture::X86)?)}
fn route(now:u64,mode:u8)->Result<(RouteContext,CapabilityRouteCatalog),Box<dyn Error>>{
    let backend=BackendId::parse(if mode==9{"other-direct"}else{"synthetic-direct"})?;
    let target=target(if mode==10{"11.0.0.9999"}else{"11.0.0.9136"})?;
    let sha=if mode==11{[9;32]}else{[7;32]};let seq=if mode==11{2}else{1};
    let context=RouteContext::new(target.clone(),sha,seq,RegistryTrustState::SignatureVerified,
        if mode==2{PolicyScope::Production}else{PolicyScope::CurrentPcPersonalLocalDevelopment},PreservationRequirement::Exact,
        if mode==3{ProtectionState::Protected}else{ProtectionState::Unprotected},now*1000,
        vec![BackendHealth::new(backend.clone(),if mode==4{BackendHealthState::Unknown}else{BackendHealthState::Healthy},
            1,now.saturating_sub(1)*1000,if mode==5{1}else{10000})])?;
    let binding=RouteBinding::new(CapabilityId::parse("search.personal_info_find_replace")?,backend,
        if mode==6{BackendKind::Hybrid}else{BackendKind::DirectHwpx},if mode==1{SupportState::NotRun}else{SupportState::Verified},
        target,sha,seq,10,1,if mode==7{PreservationImpact::Normalized}else{PreservationImpact::Exact},SignatureImpact::Preserved);
    Ok((context,CapabilityRouteCatalog::from_bindings(vec![if mode==8{binding.with_restriction(RouteRestriction::RequiresNetwork)}else{binding}])?))
}
fn manifest(p:&Provider<'_>,f:&Feed,v:&Value)->Result<Manifest,Box<dyn Error>>{
    let(context,routes)=route(5,0)?;Ok(compile(p,f,v)?.prepare_execution_manifest(p,f,&context,&routes,tx("catalog-transaction")?,5)?)
}
#[test]
fn shared_original_router_and_independent_manifest_agree_for_actual_catalog_owners()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let v=req(&s,&bytes,&f,false)?;
    let compiled=compile(&p,&f,&v)?;let(context,routes)=route(5,0)?;
    let independent=CapabilityRouter::new(CapabilityRouterLimits::default())?.route_plan(compiled.compiled(),&context,&routes)?;
    let expected=ExecutionManifest::from_receipts(tx("catalog-transaction")?,domain_ir::ArtifactId::parse(s.result.public_id())?,
        *ContentDigest::of(&bytes).as_bytes(),u64::try_from(bytes.len())?,compiled.compiled(),&independent)?;
    let out=compiled.prepare_execution_manifest(&p,&f,&context,&routes,tx("catalog-transaction")?,5)?;
    assert_eq!(out.manifest(),&expected);assert_eq!(out.routes(),independent);assert_eq!(out.manifest().route_count(),1);
    assert_eq!(out.manifest().source_artifact_id().as_str(),s.result.public_id());assert_eq!(out.manifest().expected_source_size(),u64::try_from(bytes.len())?);
    let(context,routes)=route(6,0)?;assert_eq!(out.verify(&p,&f,&context,&routes,6)?,&expected);
    assert!(out.with_verified_bytes(&p,&f,&context,&routes,6,section)??.contains("****"));Ok(())
}
#[test]
fn original_selected_mask_adapter_still_uses_same_shared_manifest_builder()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    let legacy=Dispatch::prepare_compiled_search_json(&p,&wire(&request(&s,&bytes,false)?)?,Limits::standard()?,4)?;
    // Legacy capability differs; construct its original route without widening catalog-mask routing.
    let target=target("11.0.0.9136")?;let backend=BackendId::parse("synthetic-legacy")?;
    let context=RouteContext::new(target.clone(),[7;32],1,RegistryTrustState::SignatureVerified,PolicyScope::CurrentPcPersonalLocalDevelopment,
        PreservationRequirement::Exact,ProtectionState::Unprotected,5000,vec![BackendHealth::new(backend.clone(),BackendHealthState::Healthy,1,4000,10000)])?;
    let routes=CapabilityRouteCatalog::from_bindings(vec![RouteBinding::new(CapabilityId::parse(legacy.receipt().capability_id)?,backend,BackendKind::DirectHwpx,
        SupportState::Verified,target,[7;32],1,10,1,PreservationImpact::Exact,SignatureImpact::Preserved)])?;
    let decisions=CapabilityRouter::new(CapabilityRouterLimits::default())?.route_plan(legacy.compiled(),&context,&routes)?;
    let expected=ExecutionManifest::from_receipts(tx("legacy-transaction")?,domain_ir::ArtifactId::parse(s.result.public_id())?,
        *ContentDigest::of(&bytes).as_bytes(),u64::try_from(bytes.len())?,legacy.compiled(),&decisions)?;
    assert_eq!(legacy.prepare_execution_manifest(&p,&context,&routes,tx("legacy-transaction")?,5)?.manifest(),&expected);Ok(())
}
#[test]
fn every_original_router_denial_stops_catalog_manifest_preparation()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let v=req(&s,&bytes,&f,false)?;
    for mode in 1..=8{let(context,routes)=route(5,mode)?;
        assert!(matches!(compile(&p,&f,&v)?.prepare_execution_manifest(&p,&f,&context,&routes,tx("deny")?,5),Err(M::Routing(_))));}Ok(())
}
#[test]
fn retained_manifest_rechecks_routes_and_rejects_valid_but_different_identity()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=manifest(&p,&f,&req(&s,&bytes,&f,false)?)?;
    for mode in 1..=11{let(context,routes)=route(6,mode)?;let called=Cell::new(false);
        assert!(out.with_verified_bytes(&p,&f,&context,&routes,6,|_|called.set(true)).is_err());assert!(!called.get());}
    let(context,routes)=route(6,0)?;out.verify(&p,&f,&context,&routes,6)?;Ok(())
}
#[test]
fn router_clock_must_be_fresh_seconds_to_milliseconds_not_a_previous_snapshot()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let v=req(&s,&bytes,&f,false)?;
    let(context,routes)=route(5,0)?;assert!(matches!(compile(&p,&f,&v)?.prepare_execution_manifest(&p,&f,&context,&routes,tx("time")?,6),Err(M::Routing(RE::Time))));Ok(())
}
#[test]
fn config_drift_and_read_failure_block_manifest_creation_and_retained_consumers()->R{
    for fail in [false,true]{let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let v=req(&s,&bytes,&f,false)?;
        let compiled=compile(&p,&f,&v)?;let out=manifest(&p,&f,&v)?;let(context,routes)=route(6,0)?;
        if fail{f.fail.set(true);}else{f.raw.borrow_mut()[2]^=1;}
        assert!(compiled.prepare_execution_manifest(&p,&f,&context,&routes,tx("config")?,6).is_err());let called=Cell::new(false);
        assert!(out.with_verified_bytes(&p,&f,&context,&routes,6,|_|called.set(true)).is_err());assert!(!called.get());}Ok(())
}
#[test]
fn final_config_race_after_routing_blocks_manifest_and_delivery()->R{
    for creation in [false,true]{let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let v=req(&s,&bytes,&f,false)?;
        let compiled=compile(&p,&f,&v)?;let out=manifest(&p,&f,&v)?;let(context,routes)=route(6,0)?;
        // Original byte delivery checks config twice; route completion requires a third fresh check.
        f.replace_at.set(f.reads.get()+3);let called=Cell::new(false);
        if creation{assert!(compiled.prepare_execution_manifest(&p,&f,&context,&routes,tx("race")?,6).is_err());}
        else{assert!(out.with_verified_bytes(&p,&f,&context,&routes,6,|_|called.set(true)).is_err());}
        assert!(!called.get());}Ok(())
}
#[test]
fn actual_document_protection_is_not_overridden_by_synthetic_unprotected_context()->R{
    let bytes=security::header_signal(&raw("MARK")?,"protect","0")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");
    use hwpx_package::document_import::search::replacement::atoms::personal_info::catalog::SourcePersonalInfoCatalogMaskError as CatalogError;
    // Catalog masking already rejects the original document signal before any plan/router exists.
    assert!(matches!(Dispatch::prepare_compiled_catalog_mask_json(&p,&f,&wire(&req(&s,&bytes,&f,false)?)?,Limits::standard()?,4),
        Err(CompileError::Product(PE::Stored(ME::Output(CatalogError::Replacement(Core::Protection)))))));
    assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);Ok(())
}
#[test]
fn write_scope_and_all_five_provider_dimensions_are_required_for_manifest_delivery()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=manifest(&p,&f,&req(&s,&bytes,&f,false)?)?;
    let(context,routes)=route(6,0)?;let called=Cell::new(false);assert!(out.with_verified_bytes(&s.provider()?,&f,&context,&routes,6,|_|called.set(true)).is_err());
    for mode in 0..5{let tenant=if mode==4{TenantId::new(Uuid::from_u128(882))?}else{s.reader.tenant_id()};
        let subject=if mode==3{SubjectDigest::from_authenticated_subject("foreign-manifest")?}else{s.reader.subject()};let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);
        let ctx=rev::RevisionRequestContext::new(tenant,subject);let project=if mode==2{rev::ProjectId::parse("prj_70000000000000000000000000000003")?}else{s.project};
        let branch=if mode==1{rev::BranchId::parse("brn_70000000000000000000000000000003")?}else{s.branch};
        let foreign=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&ctx,project,branch,DocumentId::parse(if mode==0{"foreign"}else{"actual-form-document"})?)?;
        assert!(out.with_verified_bytes(&foreign,&f,&context,&routes,6,|_|called.set(true)).is_err());}assert!(!called.get());Ok(())
}
#[test]
fn acl_quarantine_and_aead_still_block_retained_manifest_consumers()->R{
    for mode in 0..3{let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=manifest(&p,&f,&req(&s,&bytes,&f,false)?)?;
        match mode{0=>{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),6)?;},1=>{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("CATALOG_MANIFEST")?,6)?;},_=>s.blobs.tamper.store(true,Ordering::SeqCst)}
        let(context,routes)=route(7,0)?;let called=Cell::new(false);assert!(out.with_verified_bytes(&p,&f,&context,&routes,7,|_|called.set(true)).is_err());assert!(!called.get());}Ok(())
}
fn final_head(creation:bool)->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let v=req(&s,&bytes,&f,false)?;
    let out=manifest(&p,&f,&v)?;let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),
        artifact_service::ArtifactId::generate(),s.result,None,ContentDigest::of(b"manifest-head-race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation"),ContentDigest::of(b"transaction"))?;
    let repo=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
    let bound=StoredFormProvider::bind(&s.artifacts,&repo,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
    let(context,routes)=route(6,0)?;if creation{compile(&p,&f,&v)?.prepare_execution_manifest(&bound,&f,&context,&routes,tx("head")?,6)?;}else{out.with_verified_bytes(&bound,&f,&context,&routes,6,|_|())?;}
    let count=repo.repository().calls.load(Ordering::SeqCst);assert!(count>=5);repo.repository().calls.store(0,Ordering::SeqCst);repo.repository().trigger.store(count,Ordering::SeqCst);let called=Cell::new(false);
    if creation{assert!(compile(&p,&f,&v)?.prepare_execution_manifest(&bound,&f,&context,&routes,tx("head")?,6).is_err());}
    else{assert!(out.with_verified_bytes(&bound,&f,&context,&routes,6,|_|called.set(true)).is_err());}assert!(!called.get());Ok(())
}
#[test]fn manifest_creation_final_head_race_rejects()->R{final_head(true)}
#[test]fn manifest_delivery_final_head_race_blocks_consumer()->R{final_head(false)}
#[test]
fn transaction_identity_changes_manifest_without_recompiling_retained_output()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let v=req(&s,&bytes,&f,false)?;let(context,routes)=route(5,0)?;
    let a=compile(&p,&f,&v)?.prepare_execution_manifest(&p,&f,&context,&routes,tx("a")?,5)?;let b=compile(&p,&f,&v)?.prepare_execution_manifest(&p,&f,&context,&routes,tx("b")?,5)?;
    assert_ne!(a.manifest().canonical_sha256()?,b.manifest().canonical_sha256()?);assert_eq!(a.compiled_receipt(),b.compiled_receipt());Ok(())
}
#[test]
fn manifest_and_synthetic_routes_never_authorize_execution_or_disclose_source_patterns()->R{
    let bytes=raw("PRIVATE-MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("PRIVATE-MARK");let out=manifest(&p,&f,&req(&s,&bytes,&f,false)?)?;
    let(context,routes)=route(6,0)?;assert!(out.require_current_product_route(&p,&f,&context,&routes,6).is_err());assert!(!out.compiled_receipt().execution_authority);
    let text=format!("{out:?}{}",serde_json::to_string(out.manifest())?);assert!(!text.contains("PRIVATE-MARK")&&!text.contains("pattern0="));
    assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(s.artifacts.download(&s.reader,s.result,6)?,bytes);
    assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
}
