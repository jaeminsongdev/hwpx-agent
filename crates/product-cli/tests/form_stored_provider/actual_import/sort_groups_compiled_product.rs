//! New18th family uses actual multi-part source slots through the unmodified common compiler.
use super::*;
use hwpx_agent_cli::form_product_request::stored_literal_replacement::sort_groups::StoredParagraphSortGroupsProductRequest as Groups;
#[path="sort_groups_plan_fixture.rs"]mod multigroup;
use multigroup::{source,request};
#[test]
fn compiled_groups_common_dispatch_matches_direct_product_and_preserves_all18_closed_schemas()->TestResult{
    let bytes=source()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=request(&s,&bytes)?;
    let direct=Groups::prepare_json(&p,&wire(&v)?,Default::default(),Default::default(),4)?;let out=Dispatch::prepare_json(&p,&wire(&v)?,None,4)?;
    let Operation::SearchMutation(candidate)=&out else{return Err("dispatch".into())};
    let Receipt::ParagraphSortGroups(r)=candidate.receipt()else{return Err("receipt".into())};assert_eq!(r,direct.receipt());
    assert_eq!(candidate.with_verified_bytes(&p,5,<[u8]>::to_vec)?,direct.with_verified_bytes(&p,5,<[u8]>::to_vec)?);
    assert_eq!(SEARCH_MUTATION_REQUEST_SCHEMAS.len(),18);assert_eq!(&SEARCH_MUTATION_REQUEST_SCHEMAS[..16],SCHEMAS);
    assert!(matches!(candidate.require_current_product_route(&p,5),Err(ME::ParagraphSortGroups(_))));Ok(())
}
#[test]
fn compiled_groups_exact_original_ranges_inventory_hashes_and_actual_structural_owners()->TestResult{
    use hwpx_package::document_import::search::replacement::atoms::sort::{SourceParagraphSortSpec,SourceParagraphSortDirection,SourceParagraphSortComparison};
    let bytes=source()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=request(&s,&bytes)?;
    let forms=p.import_actual_forms(s.head,4)?;let original=forms.imported();
    let raw=original.lower_selector_paragraph_sort_groups_candidate(&bytes,Scope::Document,Policy::default(),SourceParagraphSortSpec{
        direction:SourceParagraphSortDirection::Ascending,comparison:SourceParagraphSortComparison::NfcUnicodeScalarLexicographic,max_comparison_bytes:1048576},Default::default(),Default::default())?;
    let out=Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4)?;
    assert_eq!(out.receipt().source_edit_operations,4);assert_eq!(out.receipt().edit_inventory_sha256,raw.splice_inventory().canonical_sha256());
    assert_eq!(out.receipt().mutation_receipt_sha256,raw.splice_inventory().legacy_receipt_sha256());
    let mut paths=BTreeSet::new();for(op,splice)in out.compiled().operations().iter().zip(raw.splice_inventory().splices()){
        assert_eq!(arg(op,"source_edit_domain")?,"final_permutation_splices");let anchor:domain_ir::SourceAnchorHandle=serde_json::from_str(arg(op,"source_anchor_json")?)?;
        assert_eq!(&anchor,splice.source_anchor());let at=original.source().resolve_anchor(&anchor)?;let span=at.element().ok_or("element")?.outer_span().ok_or("span")?;
        assert_eq!((splice.source_start(),splice.source_end()),(span.start(),span.end()));paths.insert(at.part().path().as_str());}
    assert_eq!(paths.len(),2);verify_plan(&s,&p,&bytes,&out)
}
#[test]
fn compiled_groups_singleton_and_fixed_slots_are_not_extra_operations()->TestResult{
    let bytes=multigroup::two_parts(&(para(1,"Z")+&para(2,"B")+&para(3,"A")),&para(1,"SINGLE"))?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=request(&s,&bytes)?;
    let out=Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4)?;assert_eq!(out.receipt().source_edit_operations,2);
    let forms=p.import_actual_forms(s.head,5)?;let fixed=&forms.imported().graph().sections()[0].body.children[1].common().node_id;
    for op in out.compiled().operations(){assert_ne!(op.target().node_id(),fixed);let anchor:domain_ir::SourceAnchorHandle=serde_json::from_str(arg(op,"source_anchor_json")?)?;
        assert_eq!(forms.imported().source().resolve_anchor(&anchor)?.part().path().as_str(),"Contents/section0.xml");}
    verify_plan(&s,&p,&bytes,&out)
}
#[test]
fn compiled_groups_request_scope_policy_plan_and_key_bindings_remain_distinct()->TestResult{
    let bytes=source()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=request(&s,&bytes)?;
    let a=Dispatch::prepare_compiled_search_json(&p,&wire(&good)?,Limits::standard()?,4)?;
    for mode in 0..4{let mut v=good.clone();match mode{0=>v["idempotency_key"]=json!("different-group-key"),1=>v["plan_id"]=json!("different-group-plan"),2=>v["operation"]["review_policy"]=policy(true,true),_=>{let inv=inventory(&p,&good)?;v["selector"]["scope"]=json!("section");v["selector"]["section_ids"]=inv["inventory"]["section_ids"].clone();}}
        let b=Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4)?;assert_eq!(a.receipt().output_package_sha256,b.receipt().output_package_sha256);
        assert_ne!(a.receipt().compiled_plan_sha256,b.receipt().compiled_plan_sha256);}Ok(())
}
#[test]
fn compiled_groups_unknown_fields_cross_kind_and_schema_reject_before_source()->TestResult{
    let bytes=source()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();
    for mode in 0..4{let mut v=good.clone();match mode{0=>v["operation"]["approved"]=json!(true),1=>v["operation"]["sort_spec"]["comparison"]=json!("native"),2=>v["operation"]["kind"]=json!("sort_sibling_paragraphs"),_=>v["schema_version"]=json!("unknown-group-schema")};
        assert!(Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4).is_err());}assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn compiled_groups_held_plan_requires_current_write_acl_quarantine_and_aead()->TestResult{
    for mode in 0..3{let bytes=source()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=request(&s,&bytes)?;
        let out=Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4)?;let reader=s.provider()?;let called=Cell::new(false);
        assert!(out.verify(&reader,5).is_err());match mode{0=>{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;},1=>{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("GROUP_PLAN")?,5)?;},_=>s.blobs.tamper.store(true,Ordering::SeqCst)}
        assert!(out.verify(&p,6).is_err());assert!(out.with_verified_bytes(&p,6,|_|called.set(true)).is_err());assert!(!called.get());}Ok(())
}
#[test]
fn compiled_groups_final_head_races_block_prepare_verify_and_consumer()->TestResult{
    for stage in 0..3{let bytes=source()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=request(&s,&bytes)?;let raw=wire(&v)?;
        let out=Dispatch::prepare_compiled_search_json(&p,&raw,Limits::standard()?,4)?;
        let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,
            ContentDigest::of(b"group plan race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation"),ContentDigest::of(b"transaction"))?;
        let b=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
        let bound=StoredFormProvider::bind(&s.artifacts,&b,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
        match stage{0=>{Dispatch::prepare_compiled_search_json(&bound,&raw,Limits::standard()?,5)?;},1=>{out.verify(&bound,5)?;},_=>{out.with_verified_bytes(&bound,5,|_|())?;}}
        let count=b.repository().calls.load(Ordering::SeqCst);assert!(count>=4);b.repository().calls.store(0,Ordering::SeqCst);b.repository().trigger.store(count,Ordering::SeqCst);let called=Cell::new(false);
        match stage{0=>assert!(Dispatch::prepare_compiled_search_json(&bound,&raw,Limits::standard()?,6).is_err()),1=>assert!(out.verify(&bound,6).is_err()),_=>assert!(out.with_verified_bytes(&bound,6,|_|called.set(true)).is_err())}
        assert!(!called.get());assert_eq!(b.repository().calls.load(Ordering::SeqCst),count);
    }Ok(())
}
#[test]
fn compiled_groups_real_p02_routing_disabled_before_any_source_read()->TestResult{
    use hwpx_agent_cli::form_product_request::stored_operations::compiled_search::p02_registry::{PinnedP02RegistryEvidence as Evidence,PinnedRegistryError as PE,RegistryBoundSearchError as BE};
    let m=material::load()?;let evidence=Evidence::verify_pinned_snapshot(m.input())?;let bytes=source()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();
    assert!(matches!(Dispatch::prepare_compiled_search_json_with_pinned_registry(&p,&wire(&v)?,Limits::standard()?,&evidence,4),Err(BE::Registry(PE::RoutingDisabled))));
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn compiled_groups_global_budget_does_not_produce_a_partial_group_plan()->TestResult{
    let bytes=multigroup::two_parts(&(para(1,"Z")+&para(2,"A")),&(para(1,"Y")+&para(2,"B")))?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=request(&s,&bytes)?;v["operation"]["sort_spec"]["max_comparison_bytes"]=json!(1);
    assert!(Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4).is_err());v["operation"]["sort_spec"]["max_comparison_bytes"]=json!(2);
    let out=Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4)?;assert_eq!(out.receipt().source_edit_operations,4);verify_plan(&s,&p,&bytes,&out)
}
#[test]
fn compiled_groups_128_operations_have_original_owners_and_bounded_locked_arguments()->TestResult{
    let body=(0..64).rev().map(|i|para(i+1,&format!("KEY-{i:03}"))).collect::<String>();let bytes=multigroup::two_parts(&body,&body)?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=request(&s,&bytes)?;
    let out=Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4)?;assert_eq!(out.receipt().source_edit_operations,128);verify_plan(&s,&p,&bytes,&out)
}
