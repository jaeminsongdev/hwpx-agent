//! Actual moved slots through the original shared compiler, never synthetic document owners or execution authority.
use super::*;
use hwpx_agent_cli::form_product_request::stored_operations::compiled_search::p02_registry::PinnedP02RegistryBytes;
use hwpx_agent_cli::form_product_request::stored_literal_replacement::sort::{StoredParagraphSortProductRequest as Sort,
    PARAGRAPH_SORT_PRODUCT_REQUEST_SCHEMA as SORT_SCHEMA};
#[path="../../support/pinned_p02_registry_fixture.rs"]mod material;
fn source()->Result<Vec<u8>,Box<dyn Error>>{definition::package(&(para(1,"Z-PRIVATE")+&para(2,"B")+&para(3,"A")))}
fn request(s:&StoredFixture,bytes:&[u8])->Result<Value,Box<dyn Error>>{let mut v=super::super::super::request(s,bytes)?;v["schema_version"]=json!(SORT_SCHEMA);
    v["operation"]=json!({"kind":"sort_sibling_paragraphs","sort_spec":{"direction":"ascending","comparison":"nfc_unicode_scalar_lexicographic","max_comparison_bytes":1048576},"review_policy":policy(false,false)});Ok(v)}
#[test]
fn compiled_sort_dispatch_matches_original_product_output_and_exact_locked_plan()->TestResult{
    let bytes=source()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=request(&s,&bytes)?;
    let direct=Sort::prepare_json(&p,&wire(&v)?,Default::default(),Default::default(),4)?;
    let out=Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4)?;
    assert_eq!(out.with_verified_bytes(&p,5,<[u8]>::to_vec)?,direct.with_verified_bytes(&p,5,<[u8]>::to_vec)?);
    assert_eq!(out.receipt().source_edit_operations,2);assert_eq!(out.receipt().capability_id,"search.sort_text");verify_plan(&s,&p,&bytes,&out)
}
#[test]
fn compiled_sort_inventory_binds_exact_destinations_subtree_ranges_and_replacement_hashes()->TestResult{
    let bytes=source()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=request(&s,&bytes)?;
    let forms=p.import_actual_forms(s.head,4)?;let original=forms.imported();
    let raw=original.lower_selector_paragraph_sort_candidate(&bytes,Scope::Document,Policy::default(),
        hwpx_package::document_import::search::replacement::atoms::sort::SourceParagraphSortSpec{direction:hwpx_package::document_import::search::replacement::atoms::sort::SourceParagraphSortDirection::Ascending,
            comparison:hwpx_package::document_import::search::replacement::atoms::sort::SourceParagraphSortComparison::NfcUnicodeScalarLexicographic,max_comparison_bytes:1048576},Default::default(),Default::default())?;
    let out=Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4)?;
    assert_eq!(out.receipt().edit_inventory_sha256,raw.splice_inventory().canonical_sha256());assert_eq!(out.receipt().mutation_receipt_sha256,raw.splice_inventory().legacy_receipt_sha256());
    for(op,splice)in out.compiled().operations().iter().zip(raw.splice_inventory().splices()){
        assert_eq!(arg(op,"source_edit_domain")?,"final_permutation_splices");let anchor:domain_ir::SourceAnchorHandle=serde_json::from_str(arg(op,"source_anchor_json")?)?;
        assert_eq!(&anchor,splice.source_anchor());let at=original.source().resolve_anchor(&anchor)?;let span=at.element().ok_or("element")?.outer_span().ok_or("span")?;
        assert_eq!((splice.source_start(),splice.source_end()),(span.start(),span.end()));}
    verify_plan(&s,&p,&bytes,&out)
}
#[test]
fn compiled_sort_fixed_middle_slot_is_not_an_operation_or_fabricated_document_target()->TestResult{
    let bytes=source()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=request(&s,&bytes)?;
    let out=Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4)?;let forms=p.import_actual_forms(s.head,5)?;
    let nodes=&forms.imported().graph().sections()[0].body.children;let fixed=&nodes[1].common().node_id;
    assert!(out.compiled().operations().iter().all(|op|op.target().node_id()!=fixed));assert_eq!(out.receipt().structural_owner_nodes,2);verify_plan(&s,&p,&bytes,&out)
}
#[test]
fn compiled_sort_scope_policy_plan_and_key_bindings_do_not_collapse_equal_outputs()->TestResult{
    let bytes=source()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=request(&s,&bytes)?;
    let a=Dispatch::prepare_compiled_search_json(&p,&wire(&good)?,Limits::standard()?,4)?;
    for mode in 0..4{let mut v=good.clone();match mode{0=>v["idempotency_key"]=json!("different-sort-key"),1=>v["plan_id"]=json!("different-sort-plan"),2=>v["operation"]["review_policy"]=policy(true,true),_=>{let inv=inventory(&p,&good)?;v["selector"]["scope"]=json!("section");v["selector"]["section_ids"]=inv["inventory"]["section_ids"].clone();}}
        let b=Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4)?;assert_eq!(a.receipt().output_package_sha256,b.receipt().output_package_sha256);
        assert_ne!(a.receipt().compiled_plan_sha256,b.receipt().compiled_plan_sha256);}Ok(())
}
#[test]
fn compiled_sort_rejects_unknown_and_partial_requests_before_source_or_partial_plan()->TestResult{
    let bytes=source()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();
    for mode in 0..3{let mut v=good.clone();match mode{0=>v["operation"]["approved"]=json!(true),1=>v["operation"]["sort_spec"]["comparison"]=json!("native"),_=>v["schema_version"]=json!("unknown-sort-schema")};
        assert!(Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4).is_err());}assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn compiled_sort_current_access_and_acl_remain_required_for_held_plan_and_output()->TestResult{
    let bytes=source()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=request(&s,&bytes)?;
    let out=Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4)?;let reader=s.provider()?;let called=Cell::new(false);
    assert!(out.verify(&reader,5).is_err());assert!(out.with_verified_bytes(&reader,5,|_|called.set(true)).is_err());
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;assert!(out.verify(&p,6).is_err());assert!(out.with_verified_bytes(&p,6,|_|called.set(true)).is_err());assert!(!called.get());Ok(())
}
#[test]
fn compiled_sort_final_head_races_reject_prepare_verify_and_consumer_delivery()->TestResult{
    for stage in 0..3{let bytes=source()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=request(&s,&bytes)?;let raw=wire(&v)?;
        let out=Dispatch::prepare_compiled_search_json(&p,&raw,Limits::standard()?,4)?;
        let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,
            ContentDigest::of(b"compiled sort race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation"),ContentDigest::of(b"transaction"))?;
        let b=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
        let bound=StoredFormProvider::bind(&s.artifacts,&b,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
        match stage{0=>{Dispatch::prepare_compiled_search_json(&bound,&raw,Limits::standard()?,5)?;},1=>{out.verify(&bound,5)?;},_=>{out.with_verified_bytes(&bound,5,|_|())?;}}
        let count=b.repository().calls.load(Ordering::SeqCst);assert!(count>=4);b.repository().calls.store(0,Ordering::SeqCst);b.repository().trigger.store(count,Ordering::SeqCst);let called=Cell::new(false);
        match stage{0=>assert!(Dispatch::prepare_compiled_search_json(&bound,&raw,Limits::standard()?,6).is_err()),1=>assert!(out.verify(&bound,6).is_err()),_=>assert!(out.with_verified_bytes(&bound,6,|_|called.set(true)).is_err())}
        assert!(!called.get());assert_eq!(b.repository().calls.load(Ordering::SeqCst),count);
    }Ok(())
}
#[test]
fn compiled_sort_new_seventeenth_schema_keeps_real_p02_policy_denial_before_source()->TestResult{
    use hwpx_agent_cli::form_product_request::stored_operations::compiled_search::p02_registry::{PinnedP02RegistryEvidence as Evidence,PinnedRegistryError as PE,RegistryBoundSearchError as BE};
    let m=material::load()?;let evidence=Evidence::verify_pinned_snapshot(m.input())?;let bytes=source()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();
    assert!(matches!(Dispatch::prepare_compiled_search_json_with_pinned_registry(&p,&wire(&v)?,Limits::standard()?,&evidence,4),Err(BE::Registry(PE::RoutingDisabled))));
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[path="sort_groups_compiled_product.rs"]mod groups_v1;
