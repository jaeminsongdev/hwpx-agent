//! Actual signed P02 artifact, actual service fixtures, no historical support promotion or source reads.
use super::*;
#[path="../../support/pinned_p02_registry_fixture.rs"]mod material;
use hwpx_agent_cli::form_product_request::stored_operations::compiled_search::p02_registry::{PinnedP02RegistryBytes,PinnedP02RegistryEvidence as Evidence,
    PinnedRegistryError as PE,RegistryBoundSearchError as BE};
fn registry()->Result<Evidence,Box<dyn Error>>{let m=material::load()?;Ok(Evidence::verify_pinned_snapshot(m.input())?)}
#[test]
fn registry_all16_known_schemas_are_policy_denied_before_any_source_or_candidate_work()->TestResult{
    let evidence=registry()?;assert!(evidence.receipt().signature_verified);
    for i in 0..16{let bytes=source(i)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
        let v=req(i,&s,&bytes)?;let before=s.metadata.audit_events()?.len();
        assert!(matches!(Dispatch::prepare_compiled_search_json_with_pinned_registry(&p,&wire(&v)?,Limits::standard()?,&evidence,4),Err(BE::Registry(PE::RoutingDisabled))));
        assert_eq!(s.metadata.audit_events()?.len(),before);assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);
    }Ok(())
}
#[test]
fn registry_unknown_legacy_and_malformed_outer_requests_still_fail_closed_before_source()->TestResult{
    let evidence=registry()?;let bytes=source(3)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let before=s.metadata.audit_events()?.len();
    for schema in["hwpx-agent.product-form-request/v1","hwpx-agent.product-operation-request/v2","hwpx-agent.product-literal-replacement-request/v999"]{
        let mut v=req(3,&s,&bytes)?;v["schema_version"]=json!(schema);
        assert!(matches!(Dispatch::prepare_compiled_search_json_with_pinned_registry(&p,&wire(&v)?,Limits::standard()?,&evidence,4),Err(BE::Product(_))));}
    for raw in[b"[]".as_slice(),b"null",b"{}",b"{bad}"]{assert!(Dispatch::prepare_compiled_search_json_with_pinned_registry(&p,raw,Limits::standard()?,&evidence,4).is_err());}
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn registry_request_approval_support_and_target_flags_cannot_override_signed_scope()->TestResult{
    let evidence=registry()?;let bytes=source(3)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
    let mut v=req(3,&s,&bytes)?;v["approved"]=json!(true);v["routing_enabled"]=json!(true);v["registry_trust"]=json!("SignatureVerified");
    v["support"]=json!("Verified");v["target"]=json!({"profile_id":"caller-authorized"});let before=s.metadata.audit_events()?.len();
    assert!(matches!(Dispatch::prepare_compiled_search_json_with_pinned_registry(&p,&wire(&v)?,Limits::standard()?,&evidence,4),Err(BE::Registry(PE::RoutingDisabled))));
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn registry_copied_receipt_flags_are_not_authority_and_reader_path_has_no_side_effects()->TestResult{
    let evidence=registry()?;let mut copied=evidence.receipt().clone();copied.execution_authority=true;copied.routing_enabled=true;
    assert!(copied.execution_authority&&copied.routing_enabled);
    let bytes=source(3)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let reader=s.provider()?;let v=req(3,&s,&bytes)?;
    let before=s.metadata.audit_events()?.len();assert!(matches!(Dispatch::prepare_compiled_search_json_with_pinned_registry(&reader,&wire(&v)?,Limits::standard()?,&evidence,4),Err(BE::Registry(PE::RoutingDisabled))));
    assert_eq!(s.metadata.audit_events()?.len(),before);assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);Ok(())
}
#[test]
fn registry_held_signed_snapshot_never_becomes_a_new_runtime_or_current_target_claim()->TestResult{
    let evidence=registry()?;assert!(!evidence.receipt().runtime_probe_reexecuted&&!evidence.receipt().current_installed_target_observed);
    for now in[4,10,1_000_000]{let bytes=source(3)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
        let v=req(3,&s,&bytes)?;let before=s.metadata.audit_events()?.len();
        assert!(matches!(Dispatch::prepare_compiled_search_json_with_pinned_registry(&p,&wire(&v)?,Limits::standard()?,&evidence,now),Err(BE::Registry(PE::RoutingDisabled))));
        assert_eq!(s.metadata.audit_events()?.len(),before);}Ok(())
}
#[test]
fn registry_authentic_signature_does_not_unlock_existing_candidate_manifest_or_product_route()->TestResult{
    let evidence=registry()?;let bytes=source(3)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let compiled=compile(3,&s,&p,&bytes)?;
    assert!(compiled.require_current_product_route(&p,5).is_err());assert_eq!(evidence.require_routing(),Err(PE::RoutingDisabled));
    let(context,catalog)=routing(compiled.receipt().capability_id,5,0)?;let out=compiled.prepare_execution_manifest(&p,&context,&catalog,transaction("not-a-registry-permit")?,5)?;
    assert!(out.require_current_product_route(&p,&context,&catalog,5).is_err());assert!(!out.compiled_receipt().execution_authority);
    assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
}
