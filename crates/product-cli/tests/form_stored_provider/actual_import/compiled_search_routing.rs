//! Actual source-to-manifest integration. Routing evidence here is synthetic, never a trusted registry.
use super::*;
use domain_ir::{Architecture,BackendHealth,BackendHealthState,BackendId,BackendKind,CapabilityId,CapabilityRouteCatalog,
    CapabilityRouter,CapabilityRouterError as RE,CapabilityRouterLimits,ExactTargetProfile,PolicyScope,PreservationImpact,
    PreservationRequirement,ProtectionState,RegistryTrustState,RouteBinding,RouteContext,RouteRestriction,SignatureImpact,
    SupportState,TargetProfileId,TransactionId};
use hwpx_agent_cli::form_product_request::stored_operations::compiled_search::{PreparedCompiledSearchMutation as Compiled,
    routing::SearchManifestError as E};
use operation_engine::ExecutionManifest;

fn transaction(name:&str)->Result<TransactionId,Box<dyn Error>>{Ok(TransactionId::parse(name)?)}
fn profile(build:&str)->Result<ExactTargetProfile,Box<dyn Error>>{
    Ok(ExactTargetProfile::new(TargetProfileId::parse("synthetic-current-target")?,build,Architecture::X86)?)
}
fn routing(cap:&str,now:u64,mode:u8)->Result<(RouteContext,CapabilityRouteCatalog),Box<dyn Error>>{
    let backend=BackendId::parse(if mode==18{"other-direct"}else{"synthetic-direct"})?;
    let target=profile(if mode==15{"11.0.0.9999"}else{"11.0.0.9136"})?;
    let digest=if mode==17{[8;32]}else{[7;32]};let sequence=if mode==17{2}else{1};
    let context=RouteContext::new(target.clone(),digest,sequence,RegistryTrustState::SignatureVerified,
        if mode==4{PolicyScope::Production}else{PolicyScope::CurrentPcPersonalLocalDevelopment},PreservationRequirement::Exact,
        if mode==5{ProtectionState::Protected}else if mode==11{ProtectionState::Signed}else{ProtectionState::Unprotected},now*1000,
        vec![BackendHealth::new(backend.clone(),if mode==6{BackendHealthState::Unknown}else{BackendHealthState::Healthy},
            if mode==16{2}else{1},if mode==8{now*1000+1}else{now.saturating_sub(1)*1000},if mode==7{1}else{10_000})])?;
    let binding=RouteBinding::new(CapabilityId::parse(if mode==13{"synthetic.other"}else{cap})?,backend,
        if mode==14{BackendKind::Hybrid}else{BackendKind::DirectHwpx},if mode==1{SupportState::NotRun}else{SupportState::Verified},
        if mode==2{profile("11.0.0.0001")?}else{target},if mode==3{[9;32]}else{digest},sequence,10,1,
        if mode==9{PreservationImpact::Normalized}else{PreservationImpact::Exact},
        if mode==11{SignatureImpact::Invalidated}else{SignatureImpact::Preserved});
    let mut bindings=vec![if mode==10{binding.with_restriction(RouteRestriction::RequiresNetwork)}else{binding}];
    if mode==12{bindings.push(RouteBinding::new(CapabilityId::parse(cap)?,BackendId::parse("ambiguous-other")?,BackendKind::DirectHwpx,
        SupportState::Verified,profile("11.0.0.9136")?,digest,sequence,10,1,PreservationImpact::Exact,SignatureImpact::Preserved));
        let context=RouteContext::new(profile("11.0.0.9136")?,digest,sequence,RegistryTrustState::SignatureVerified,
            PolicyScope::CurrentPcPersonalLocalDevelopment,PreservationRequirement::Exact,ProtectionState::Unprotected,now*1000,
            vec![BackendHealth::new(BackendId::parse("synthetic-direct")?,BackendHealthState::Healthy,1,now*1000,10_000),
                BackendHealth::new(BackendId::parse("ambiguous-other")?,BackendHealthState::Healthy,1,now*1000,10_000)])?;
        return Ok((context,CapabilityRouteCatalog::from_bindings(bindings)?));}
    Ok((context,CapabilityRouteCatalog::from_bindings(bindings)?))
}
fn compile(i:usize,s:&StoredFixture,p:&Provider<'_>,bytes:&[u8])->Result<Compiled,Box<dyn Error>>{
    Ok(Dispatch::prepare_compiled_search_json(p,&wire(&req(i,s,bytes)?)?,Limits::standard()?,4)?)
}
fn assert_manifest(s:&StoredFixture,p:&Provider<'_>,bytes:&[u8],compiled:Compiled)->TestResult{
    let cap=compiled.receipt().capability_id;let plan_sha=compiled.receipt().compiled_plan_sha256;
    let count=compiled.compiled().operations().len();let(context,catalog)=routing(cap,5,0)?;
    let independent=CapabilityRouter::new(CapabilityRouterLimits::default())?;
    let routes=compiled.compiled().operations().iter().map(|op|independent.route(op,&context,&catalog)).collect::<Result<Vec<_>,_>>()?;
    let expected=ExecutionManifest::from_receipts(transaction("test-source-transaction")?,domain_ir::ArtifactId::parse(s.result.public_id())?,
        *ContentDigest::of(bytes).as_bytes(),u64::try_from(bytes.len())?,compiled.compiled(),&routes)?;
    let out=compiled.prepare_execution_manifest(p,&context,&catalog,transaction("test-source-transaction")?,5)?;
    assert_eq!(out.routes(),routes);assert_eq!(out.manifest(),&expected);assert_eq!(out.manifest().compiled_plan_sha256(),plan_sha);
    assert_eq!(out.manifest().route_count(),count);assert_eq!(out.manifest().expected_source_size(),u64::try_from(bytes.len())?);
    assert_eq!(out.manifest().source_artifact_id().as_str(),s.result.public_id());assert_eq!(out.manifest().base_revision(),&out.compiled_receipt().base_revision);
    let(current,catalog)=routing(cap,6,0)?;assert_eq!(out.verify(p,&current,&catalog,6)?,&expected);
    let candidate=out.with_verified_bytes(p,&current,&catalog,6,<[u8]>::to_vec)?;
    assert_eq!(*ContentDigest::of(&candidate).as_bytes(),out.compiled_receipt().output_package_sha256);assert_ne!(candidate,bytes);
    assert!(!out.compiled_receipt().execution_authority);assert!(matches!(out.require_current_product_route(p,&current,&catalog,6),Err(E::Candidate(_))));
    assert!(!format!("{out:?}").contains("PRIVATE"));assert!(!serde_json::to_string(out.manifest())?.contains("PRIVATE"));
    assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);
    assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
}
macro_rules! manifest_case{($name:ident,$i:literal)=>{#[test]fn $name()->TestResult{
    let bytes=source($i)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
    assert_manifest(&s,&p,&bytes,compile($i,&s,&p,&bytes)?)
}}}
manifest_case!(manifest_literal_v1,0);
manifest_case!(manifest_atoms_v2,1);
manifest_case!(manifest_review_v3,2);
manifest_case!(manifest_selector_v4,3);
manifest_case!(manifest_regex_v1,4);
manifest_case!(manifest_regex_insertion_v2,5);
manifest_case!(manifest_character_style_v1,6);
manifest_case!(manifest_text_style_v1,7);
manifest_case!(manifest_paragraph_style_v1,8);
manifest_case!(manifest_unicode_scope_v1,9);
manifest_case!(manifest_unicode_match_v2,10);
manifest_case!(manifest_case_v1,11);
manifest_case!(manifest_width_v1,12);
manifest_case!(manifest_whitespace_v1,13);
manifest_case!(manifest_text_control_v1,14);
manifest_case!(manifest_number_control_v1,15);

#[test]
fn manifest_batch128_equals_independent_original_routes_for_every_actual_owner()->TestResult{
    let mut body=String::new();for n in 1..=128{body.push_str(&para(n,"K"));}
    let bytes=definition::package(&body.replace(" charStyleIDRef='0'",""))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
    let mut v=req(3,&s,&bytes)?;v["operation"]["max_replacements"]=json!(128);
    let compiled=Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4)?;
    assert_eq!(compiled.receipt().source_edit_operations,128);assert_eq!(compiled.receipt().structural_owner_nodes,128);
    assert_manifest(&s,&p,&bytes,compiled)
}
#[test]
fn manifest_original_router_rejections_and_wrong_backend_are_not_widened()->TestResult{
    let bytes=source(3)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
    let expected=[RE::SupportUnavailable,RE::TargetProfileMismatch,RE::RegistryMismatch,RE::PolicyDenied,RE::ConfirmationRequired,
        RE::HealthUnavailable,RE::HealthUnavailable,RE::HealthUnavailable,RE::PreservationDenied,RE::PolicyDenied,RE::PreservationDenied,
        RE::AmbiguousRoute,RE::CapabilityNotFound];
    for(mode,error)in(1..=13).zip(expected){let compiled=compile(3,&s,&p,&bytes)?;let(context,catalog)=routing(compiled.receipt().capability_id,5,mode)?;
        assert!(matches!(compiled.prepare_execution_manifest(&p,&context,&catalog,transaction("denied")?,5),Err(E::Route(e))if e==error));}
    let compiled=compile(3,&s,&p,&bytes)?;let(context,catalog)=routing(compiled.receipt().capability_id,5,14)?;
    assert!(matches!(compiled.prepare_execution_manifest(&p,&context,&catalog,transaction("wrong-backend")?,5),Err(E::Backend)));Ok(())
}
#[test]
fn manifest_clock_snapshot_must_match_current_service_time_and_not_overflow()->TestResult{
    let bytes=source(3)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
    let compiled=compile(3,&s,&p,&bytes)?;let cap=compiled.receipt().capability_id;let(context,catalog)=routing(cap,5,0)?;
    assert!(matches!(compiled.prepare_execution_manifest(&p,&context,&catalog,transaction("stale-clock")?,6),Err(E::Time)));
    let compiled=compile(3,&s,&p,&bytes)?;let out=compiled.prepare_execution_manifest(&p,&context,&catalog,transaction("clock")?,5)?;
    for now in[6,u64::MAX]{let called=Cell::new(false);assert!(matches!(out.with_verified_bytes(&p,&context,&catalog,now,|_|called.set(true)),Err(E::Time)));assert!(!called.get());}
    let(context,catalog)=routing(cap,6,0)?;out.verify(&p,&context,&catalog,6)?;Ok(())
}
#[test]
fn manifest_retained_routes_reject_new_target_registry_health_and_backend_evidence()->TestResult{
    let bytes=source(3)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
    let compiled=compile(3,&s,&p,&bytes)?;let cap=compiled.receipt().capability_id;let(context,catalog)=routing(cap,5,0)?;
    let out=compiled.prepare_execution_manifest(&p,&context,&catalog,transaction("retained")?,5)?;
    for mode in[15,16,17,18]{let(context,catalog)=routing(cap,6,mode)?;let called=Cell::new(false);
        assert!(matches!(out.with_verified_bytes(&p,&context,&catalog,6,|_|called.set(true)),Err(E::Drift)));assert!(!called.get());}
    let(context,catalog)=routing(cap,6,7)?;assert!(matches!(out.verify(&p,&context,&catalog,6),Err(E::Route(RE::HealthUnavailable))));Ok(())
}
#[test]
fn manifest_current_source_acl_quarantine_and_aead_rechecked_before_delivery()->TestResult{
    for mode in 0..3{let bytes=source(3)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
        let compiled=compile(3,&s,&p,&bytes)?;let cap=compiled.receipt().capability_id;let(context,catalog)=routing(cap,5,0)?;
        let out=compiled.prepare_execution_manifest(&p,&context,&catalog,transaction("security")?,5)?;
        match mode{0=>{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),6)?;},
            1=>{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("MANIFEST_SOURCE")?,6)?;},_=>s.blobs.tamper.store(true,Ordering::SeqCst)}
        let(context,catalog)=routing(cap,7,0)?;let called=Cell::new(false);assert!(out.with_verified_bytes(&p,&context,&catalog,7,|_|called.set(true)).is_err());assert!(!called.get());
        if mode==0{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),8)?;
            let(context,catalog)=routing(cap,9,0)?;out.verify(&p,&context,&catalog,9)?;}
    }Ok(())
}
#[test]
fn manifest_current_write_and_five_provider_scopes_are_not_retained_authority()->TestResult{
    let bytes=source(3)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
    let compiled=compile(3,&s,&p,&bytes)?;let cap=compiled.receipt().capability_id;let(context,catalog)=routing(cap,5,0)?;
    let out=compiled.prepare_execution_manifest(&p,&context,&catalog,transaction("scope")?,5)?;let(context,catalog)=routing(cap,6,0)?;
    let reader=s.provider()?;let called=Cell::new(false);assert!(out.with_verified_bytes(&reader,&context,&catalog,6,|_|called.set(true)).is_err());
    for i in 0..5{let tenant=if i==4{TenantId::new(Uuid::from_u128(1213))?}else{s.reader.tenant_id()};let subject=if i==3{SubjectDigest::from_authenticated_subject("foreign-manifest")?}else{s.reader.subject()};
        let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);let rctx=rev::RevisionRequestContext::new(tenant,subject);
        let project=if i==2{rev::ProjectId::parse("prj_70000000000000000000000000000002")?}else{s.project};let branch=if i==1{rev::BranchId::parse("brn_70000000000000000000000000000002")?}else{s.branch};
        let foreign=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&rctx,project,branch,DocumentId::parse(if i==0{"foreign-document"}else{"actual-form-document"})?)?;
        assert!(out.with_verified_bytes(&foreign,&context,&catalog,6,|_|called.set(true)).is_err());}
    assert!(!called.get());Ok(())
}
#[test]
fn manifest_final_head_after_routing_blocks_consumer_on_last_boundary_race()->TestResult{
    let bytes=source(3)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
    let compiled=compile(3,&s,&p,&bytes)?;let cap=compiled.receipt().capability_id;let(context,catalog)=routing(cap,5,0)?;
    let out=compiled.prepare_execution_manifest(&p,&context,&catalog,transaction("head-race")?,5)?;
    let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),
        artifact_service::ArtifactId::generate(),s.result,None,ContentDigest::of(b"manifest race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation"),ContentDigest::of(b"transaction"))?;
    let repo=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
    let bound=StoredFormProvider::bind(&s.artifacts,&repo,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
    let(context,catalog)=routing(cap,6,0)?;out.with_verified_bytes(&bound,&context,&catalog,6,|_|())?;
    let calls=repo.repository().calls.load(Ordering::SeqCst);assert!(calls>=5);repo.repository().calls.store(0,Ordering::SeqCst);repo.repository().trigger.store(calls,Ordering::SeqCst);
    let called=Cell::new(false);assert!(out.with_verified_bytes(&bound,&context,&catalog,6,|_|called.set(true)).is_err());assert!(!called.get());Ok(())
}
#[test]
fn manifest_transaction_and_original_request_key_bind_exact_source_plan_not_output_only()->TestResult{
    let bytes=source(3)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
    let a=compile(3,&s,&p,&bytes)?;let(context,catalog)=routing(a.receipt().capability_id,5,0)?;
    let a=a.prepare_execution_manifest(&p,&context,&catalog,transaction("transaction-a")?,5)?;
    let b=compile(3,&s,&p,&bytes)?.prepare_execution_manifest(&p,&context,&catalog,transaction("transaction-b")?,5)?;
    assert_ne!(a.manifest().canonical_sha256()?,b.manifest().canonical_sha256()?);assert_eq!(a.manifest().compiled_plan_sha256(),b.manifest().compiled_plan_sha256());
    let mut v=req(3,&s,&bytes)?;v["idempotency_key"]=json!("OTHER-PRIVATE-KEY");
    let b=Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4)?.prepare_execution_manifest(&p,&context,&catalog,transaction("transaction-a")?,5)?;
    assert_ne!(a.manifest().compiled_plan_sha256(),b.manifest().compiled_plan_sha256());assert_eq!(a.compiled_receipt().output_package_sha256,b.compiled_receipt().output_package_sha256);
    assert!(!serde_json::to_string(b.manifest())?.contains("OTHER-PRIVATE-KEY"));Ok(())
}
#[test]
fn manifest_failed_later_route_does_not_return_a_partial_multi_capability_plan()->TestResult{
    use domain_ir::{CapabilityCatalog,CapabilityDefinitionDraft,DocumentGraph,DocumentGraphDraft,DocumentGraphLimits,Flow,Inline,LogicalId,Node,NodeCommon,
        OperationDraft,OperationId,OperationPlanCompiler,OperationPlanDraft,OperationPlanLimits,ParagraphNode,PlanId,Properties,RevisionId,Section,Selector,SelectorDraft,SelectorLimits,SelectorSnapshot};
    let owner=LogicalId::parse("synthetic-p")?;let g=DocumentGraph::from_draft(DocumentGraphDraft::new(DocumentId::parse("synthetic-router-only")?,vec![Section{
        section_id:LogicalId::parse("synthetic-s")?,properties:Properties::new(),master_pages:vec![],headers_footers:vec![],body:Flow{children:vec![Node::Paragraph(ParagraphNode{
            common:NodeCommon::new(owner.clone()),inlines:vec![Inline::Text{text:"synthetic".into()}],paragraph_properties:Properties::new()})]}}]),DocumentGraphLimits::default())?;
    let revision=RevisionId::parse("synthetic-revision")?;let snapshot=SelectorSnapshot::build(&g,revision.clone(),SelectorLimits::default())?;
    let a=CapabilityId::parse("synthetic.a")?;let b=CapabilityId::parse("synthetic.b")?;let definitions=CapabilityCatalog::from_drafts(vec![CapabilityDefinitionDraft::new(a.clone()),CapabilityDefinitionDraft::new(b.clone())])?;
    let operations=[a,b].into_iter().cycle().take(20).enumerate().map(|(n,cap)|Ok(OperationDraft{operation_id:OperationId::parse(format!("op-{n}"))?,capability_id:cap,
        selector:SelectorDraft::one(Selector::by_logical_id(owner.clone())),arguments:Default::default(),depends_on:vec![]})).collect::<Result<Vec<_>,domain_ir::IdentityError>>()?;
    let plan=OperationPlanCompiler::new(OperationPlanLimits::default())?.compile(OperationPlanDraft::new(PlanId::parse("synthetic-plan")?,revision,operations),&definitions,&snapshot,&snapshot.expectation())?;
    let(context,catalog)=routing("synthetic.a",5,0)?;let router=CapabilityRouter::new(CapabilityRouterLimits::default())?;
    assert!(matches!(router.route_plan(&plan,&context,&catalog),Err(RE::CapabilityNotFound)));
    let bindings=["synthetic.a","synthetic.b"].into_iter().map(|cap|Ok(RouteBinding::new(CapabilityId::parse(cap)?,BackendId::parse("synthetic-direct")?,BackendKind::DirectHwpx,
        SupportState::Verified,profile("11.0.0.9136")?,[7;32],1,10,1,PreservationImpact::Exact,SignatureImpact::Preserved))).collect::<Result<Vec<_>,Box<dyn Error>>>()?;
    let catalog=CapabilityRouteCatalog::from_bindings(bindings)?;let all=router.route_plan(&plan,&context,&catalog)?;assert_eq!(all.len(),20);
    for(op,r)in plan.operations().iter().zip(&all){assert_eq!(&router.route(op,&context,&catalog)?,r);assert_eq!(op.operation_id(),r.operation_id());assert_eq!(op.capability_id(),r.capability_id());}Ok(())
}
#[test]
fn manifest_later_call_rechecks_policy_and_does_not_cache_previous_route_success()->TestResult{
    let bytes=source(3)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
    let compiled=compile(3,&s,&p,&bytes)?;let cap=compiled.receipt().capability_id;let(context,catalog)=routing(cap,5,0)?;
    let out=compiled.prepare_execution_manifest(&p,&context,&catalog,transaction("policy-recheck")?,5)?;
    for mode in[1,4,5,6,9,10]{let(context,catalog)=routing(cap,6,mode)?;let called=Cell::new(false);assert!(matches!(out.with_verified_bytes(&p,&context,&catalog,6,|_|called.set(true)),Err(E::Route(_))));assert!(!called.get());}
    let(context,catalog)=routing(cap,6,0)?;out.verify(&p,&context,&catalog,6)?;Ok(())
}
#[path="source_protection_manifest.rs"]mod protection_v1;
#[path="pinned_p02_registry_product.rs"]mod p02_registry_v1;
#[path="sort_manifest_product.rs"]mod sort_v1;
