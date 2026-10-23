//! Actual original owners and full optional-filter receipts through common v2 mutation/preview.
use super::*;
use sha2::{Digest as _,Sha256};
use hwpx_agent_cli::form_product_request::{stored_literal_replacement::named_styles::options::StoredNamedStyleOptionsMutationRequest as Mutation,
    stored_operations::{StoredProductRequest as Dispatch,PreparedStoredProductOperation as Operation,StoredProductOperationError as CommonError,
        search_mutations::{SearchMutationLimits as Limits,SearchMutationReceiptRef as Receipt,SEARCH_MUTATION_REQUEST_SCHEMAS as SCHEMAS},
        compiled_search::{PreparedCompiledSearchMutation as Compiled,CompiledSearchError}}};
fn common(p:&Provider<'_>,v:&Value)->Result<Operation,Box<dyn Error>>{Ok(Dispatch::prepare_json(p,&wire(v)?,None,4)?)}
fn compile(p:&Provider<'_>,v:&Value)->Result<Compiled,Box<dyn Error>>{Ok(Dispatch::prepare_compiled_search_json(p,&wire(v)?,Limits::standard()?,4)?)}
fn arg<'a>(op:&'a domain_ir::CompiledOperation,key:&str)->Result<&'a str,Box<dyn Error>>{let domain_ir::CanonicalArgumentValue::Text(v)=op.arguments().get(key).ok_or("argument")?.value()else{return Err("text argument".into())};Ok(v)}
fn check(p:&Provider<'_>,v:&Value,out:&Compiled)->R{
    let direct=Mutation::prepare_json(p,&wire(v)?,Default::default(),Default::default(),4)?;let payload=&direct.receipt().stored.output;let source=payload.source();
    assert_eq!(out.receipt().request_schema,V2);assert_eq!(out.receipt().capability_id,"search.replace_styles");assert!(!out.receipt().execution_authority);
    assert_eq!(out.receipt().source_edit_operations,source.changes.len());assert_eq!(out.receipt().mutation_receipt_sha256,<[u8;32]>::from(Sha256::digest(serde_json::to_vec(payload)?)));
    assert_eq!(out.receipt().compiled_plan_sha256,<[u8;32]>::from(Sha256::digest(serde_json::to_vec(out.compiled())?)));
    for(i,(op,change))in out.compiled().operations().iter().zip(&source.changes).enumerate(){assert_eq!(op.arguments().len(),12);assert_eq!(arg(op,"request_schema")?,V2);assert_eq!(arg(op,"source_edit_domain")?,"changes");assert_eq!(arg(op,"source_edit_index")?,i.to_string());
        assert_eq!(serde_json::from_str::<Value>(arg(op,"source_anchor_json")?)?,serde_json::to_value(&change.paragraph_anchor)?);assert_eq!(arg(op,"mutation_receipt_sha256")?,hex::encode(out.receipt().mutation_receipt_sha256));}
    assert_eq!(out.with_verified_bytes(p,5,ContentDigest::of)?,direct.with_verified_bytes(p,5,ContentDigest::of)?);Ok(())
}
#[test]
fn twenty_second_family_owns_original_v2_receipt_and_matches_standalone_output()->R{
    assert_eq!(SCHEMAS.len(),23);assert_eq!(SCHEMAS[20],SCHEMA);assert_eq!(SCHEMAS[21],V2);assert_eq!(SCHEMAS.iter().copied().collect::<BTreeSet<_>>().len(),23);
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=v2(&s,&bytes,false)?;let out=common(&p,&v)?;let direct=prepare_v2(&p,&v)?;
    let Operation::SearchMutation(c)=&out else{return Err("mutation".into())};let Receipt::NamedStyleOptions(r)=c.receipt()else{return Err("named options".into())};assert_eq!(r,direct.receipt());c.verify(&p,5)?;assert_eq!(out.with_verified_bytes(&p,None,5,ContentDigest::of)?,direct.with_verified_bytes(&p,5,ContentDigest::of)?);Ok(())
}
#[test]
fn physically_separate_preview_matches_original_metadata_and_has_no_file_output()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=v2(&s,&bytes,true)?;let out=common(&p,&v)?;let direct=prepare_v2(&p,&v)?;
    let Operation::NamedStyleOptionsPreview(preview)=&out else{return Err("options preview".into())};assert_eq!(preview.verify(&p,5)?,direct.verify(&p,5)?);assert!(preview.receipt().preview_only&&!preview.receipt().stored.candidate_output_retained);
    assert_eq!(out.with_verified_preview_json(&p,None,5,<[u8]>::to_vec)?,direct.with_verified_json(&p,5,<[u8]>::to_vec)?);let called=Cell::new(false);assert!(matches!(out.with_verified_bytes(&p,None,5,|_|called.set(true)),Err(CommonError::PreviewOnly)));assert!(!called.get());Ok(())
}
#[test]
fn preview_cannot_construct_mutation_or_compiled_plan_before_source_reads()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=v2(&s,&bytes,true)?;let n=s.metadata.audit_events()?.len();
    assert!(matches!(Mutation::prepare_json(&p,&wire(&v)?,Default::default(),Default::default(),4),Err(E::PreviewOnly)));assert!(matches!(Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4),Err(CompiledSearchError::Kind)));assert_eq!(s.metadata.audit_events()?.len(),n);Ok(())
}
#[test]
fn mutation_cannot_use_preview_json_delivery()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let out=common(&p,&v2(&s,&bytes,false)?)?;let called=Cell::new(false);
    assert!(matches!(out.with_verified_preview_json(&p,None,5,|_|called.set(true)),Err(CommonError::PreviewKind)));assert!(!called.get());Ok(())
}
#[test]
fn two_selected_original_paragraphs_bind_to_actual_second_and_third_owners()->R{
    let bytes=package(&(para(1,2,"KEEP")+&para(2,0,"A")+&para(3,1,"B")))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=v2(&s,&bytes,false)?;let out=compile(&p,&v)?;check(&p,&v,&out)?;
    let source=p.import_actual_forms(s.head,5)?;let nodes=&source.imported().graph().sections()[0].body.children;assert_eq!(out.receipt().structural_owner_nodes,2);assert_eq!(out.compiled().operations()[0].target().node_id(),&nodes[1].common().node_id);assert_eq!(out.compiled().operations()[1].target().node_id(),&nodes[2].common().node_id);Ok(())
}
#[test]
fn full_filter_receipt_not_just_same_source_output_is_bound_to_plan()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let a=v2(&s,&bytes,false)?;let mut b=a.clone();b["operation"]["style_filter"]=json!({"kind":"declared","filter":{"run_character_property":0}});
    let x=compile(&p,&a)?;let y=compile(&p,&b)?;assert_eq!(x.receipt().output_package_sha256,y.receipt().output_package_sha256);assert_ne!(x.receipt().mutation_receipt_sha256,y.receipt().mutation_receipt_sha256);assert_ne!(x.receipt().compiled_plan_sha256,y.receipt().compiled_plan_sha256);check(&p,&b,&y)?;Ok(())
}
#[test]
fn absent_filter_uses_original_v1_output_but_keeps_v2_plan_identity()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=v2(&s,&bytes,false)?;v["operation"].as_object_mut().ok_or("op")?.remove("style_filter");let out=compile(&p,&v)?;
    let old=compile(&p,&request(&s,&bytes,false)?)?;assert_eq!(out.receipt().output_package_sha256,old.receipt().output_package_sha256);assert_ne!(out.receipt().compiled_plan_sha256,old.receipt().compiled_plan_sha256);check(&p,&v,&out)?;Ok(())
}
#[test]
fn definition_filter_selects_only_original_matching_style_and_preserves_nonselected_owner()->R{
    let bytes=package(&(para(1,0,"A")+&para(2,1,"B").replace("charPrIDRef='0'","charPrIDRef='1'")))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=v2(&s,&bytes,false)?;
    v["operation"]["style_filter"]=json!({"kind":"definition","filter":{"character_source":"run_property","bold":true}});let out=compile(&p,&v)?;check(&p,&v,&out)?;assert_eq!(out.receipt().source_edit_operations,1);assert_eq!(out.with_verified_bytes(&p,5,refs)??,vec![(1,Some(0),Some(0)),(2,Some(0),Some(2))]);Ok(())
}
#[test]
fn malformed_filter_and_missing_preview_flag_reject_before_common_source_reads()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=v2(&s,&bytes,true)?;let n=s.metadata.audit_events()?.len();
    for value in [Value::Null,json!({}),json!({"kind":"declared","filter":{"unknown":0}})]{let mut v=good.clone();v["operation"]["style_filter"]=value;assert!(common(&p,&v).is_err());}
    let mut v=good;v["operation"].as_object_mut().ok_or("op")?.remove("preview_only");assert!(common(&p,&v).is_err());assert_eq!(s.metadata.audit_events()?.len(),n);Ok(())
}
#[test]
fn original_server_search_writer_and_metadata_limits_apply_before_common_success()->R{
    let bytes=package(&(para(1,0,"A")+&para(2,1,"B")))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    for preview in [false,true]{let v=v2(&s,&bytes,preview)?;for mode in 0..3{let mut limits=Limits::standard()?;match mode{0=>limits.search=SourceSearchLimits::new(Config{matches:1,..Default::default()})?,1=>limits.writer=WriterLimits::new(WriterLimitConfig{max_output_bytes:1})?,_=>limits.search=SourceSearchLimits::new(Config{result_bytes:1,..Default::default()})?}
        assert!(Dispatch::prepare_json_with_search_limits(&p,&wire(&v)?,None,limits,4).is_err());if !preview{assert!(Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,limits,4).is_err());}}}Ok(())
}
#[test]
fn current_write_and_foreign_provider_scope_block_both_common_result_modes()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let preview=common(&p,&v2(&s,&bytes,true)?)?;let out=compile(&p,&v2(&s,&bytes,false)?)?;let reader=s.provider()?;
    let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("foreign-options")?)?;let called=Cell::new(false);
    for provider in [&reader,&other]{assert!(preview.with_verified_preview_json(provider,None,5,|_|called.set(true)).is_err());assert!(out.with_verified_bytes(provider,5,|_|called.set(true)).is_err());}assert!(!called.get());Ok(())
}
#[test]
fn acl_revoke_regrant_and_ciphertext_tamper_remain_fresh_after_common_compilation()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let preview=common(&p,&v2(&s,&bytes,true)?)?;let out=compile(&p,&v2(&s,&bytes,false)?)?;
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;let called=Cell::new(false);assert!(preview.with_verified_preview_json(&p,None,6,|_|called.set(true)).is_err());assert!(out.verify(&p,6).is_err());assert!(!called.get());
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;out.verify(&p,8)?;preview.with_verified_preview_json(&p,None,8,|_|())?;s.blobs.tamper.store(true,Ordering::SeqCst);
    assert!(preview.with_verified_preview_json(&p,None,9,|_|called.set(true)).is_err());assert!(out.with_verified_bytes(&p,9,|_|called.set(true)).is_err());assert!(!called.get());Ok(())
}
#[test]
fn original_head_ingest_route_denial_and_private_value_redaction_are_preserved()->R{
    let bytes=raw("PRIVATE-COMMON-OPTIONS")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let preview=common(&p,&v2(&s,&bytes,true)?)?;let out=compile(&p,&v2(&s,&bytes,false)?)?;
    assert!(preview.require_current_product_route(&p,None,5).is_err());assert!(out.require_current_product_route(&p,5).is_err());for text in [format!("{preview:?}{out:?}"),serde_json::to_string(out.compiled())?]{assert!(!text.contains("PRIVATE-")&&!text.contains("SRC")&&!text.contains("<hp:"));}
    assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
}
fn common_head_race(stage:usize)->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let pv=v2(&s,&bytes,true)?;let mv=v2(&s,&bytes,false)?;let preview=common(&p,&pv)?;let out=compile(&p,&mv)?;
    let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,
        ContentDigest::of(b"common-options-race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation fixture"),ContentDigest::of(b"transaction fixture"))?;
    let repo=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
    let bound=StoredFormProvider::bind(&s.artifacts,&repo,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
    match stage{0=>{Dispatch::prepare_json(&bound,&wire(&pv)?,None,5)?;},1=>{preview.with_verified_preview_json(&bound,None,5,|_|())?;},2=>{Dispatch::prepare_compiled_search_json(&bound,&wire(&mv)?,Limits::standard()?,5)?;},3=>{out.verify(&bound,5)?;},_=>{out.with_verified_bytes(&bound,5,|_|())?;}}
    let count=repo.repository().calls.load(Ordering::SeqCst);assert!(count>=4);repo.repository().calls.store(0,Ordering::SeqCst);repo.repository().trigger.store(count,Ordering::SeqCst);let called=Cell::new(false);
    match stage{0=>assert!(Dispatch::prepare_json(&bound,&wire(&pv)?,None,6).is_err()),1=>assert!(preview.with_verified_preview_json(&bound,None,6,|_|called.set(true)).is_err()),2=>assert!(Dispatch::prepare_compiled_search_json(&bound,&wire(&mv)?,Limits::standard()?,6).is_err()),3=>assert!(out.verify(&bound,6).is_err()),_=>assert!(out.with_verified_bytes(&bound,6,|_|called.set(true)).is_err())}
    assert!(!called.get());assert_eq!(repo.repository().calls.load(Ordering::SeqCst),count);Ok(())
}
#[test]fn preview_preparation_last_head_rejects()->R{common_head_race(0)}
#[test]fn preview_json_last_head_blocks_consumer()->R{common_head_race(1)}
#[test]fn post_compiler_last_head_rejects()->R{common_head_race(2)}
#[test]fn compiled_retained_verification_last_head_rejects()->R{common_head_race(3)}
#[test]fn compiled_bytes_last_head_blocks_consumer()->R{common_head_race(4)}
