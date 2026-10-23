//! Actual common named-style dispatch, opaque mode separation and original operation compiler.
use super::*;
use sha2::{Digest as _,Sha256};
use hwpx_agent_cli::form_product_request::{stored_literal_replacement::named_styles::StoredNamedStyleMutationRequest as Mutation,
    stored_operations::{StoredProductRequest as Dispatch,PreparedStoredProductOperation as Operation,StoredProductOperationError as CommonError,
        search_mutations::{SearchMutationLimits as Limits,SearchMutationReceiptRef as Receipt,SEARCH_MUTATION_REQUEST_SCHEMAS as SCHEMAS},
        compiled_search::{PreparedCompiledSearchMutation as Compiled,CompiledSearchError}}};
fn common(p:&Provider<'_>,v:&Value)->Result<Operation,Box<dyn Error>>{Ok(Dispatch::prepare_json(p,&wire(v)?,None,4)?)}
fn compile(p:&Provider<'_>,v:&Value)->Result<Compiled,Box<dyn Error>>{Ok(Dispatch::prepare_compiled_search_json(p,&wire(v)?,Limits::standard()?,4)?)}
fn arg<'a>(op:&'a domain_ir::CompiledOperation,key:&str)->Result<&'a str,Box<dyn Error>>{
    let domain_ir::CanonicalArgumentValue::Text(v)=op.arguments().get(key).ok_or("locked argument")?.value()else{return Err("text argument".into())};Ok(v)
}
fn check(p:&Provider<'_>,v:&Value,out:&Compiled)->R{
    let direct=Mutation::prepare_json(p,&wire(v)?,Default::default(),Default::default(),4)?;let r=&direct.receipt().stored.output;
    assert_eq!(out.receipt().request_schema,SCHEMA);assert_eq!(out.receipt().capability_id,"search.replace_styles");assert!(!out.receipt().execution_authority);
    assert_eq!(out.receipt().source_edit_operations,r.changes.len());assert_eq!(out.receipt().mutation_receipt_sha256,<[u8;32]>::from(Sha256::digest(serde_json::to_vec(r)?)));
    assert_eq!(out.receipt().compiled_plan_sha256,<[u8;32]>::from(Sha256::digest(serde_json::to_vec(out.compiled())?)));
    let head=rev::RevisionHead::new(Some(rev::RevisionId::parse(v["base_revision"].as_str().ok_or("revision")?)?),v["expected_head_generation"].as_u64().ok_or("generation")?)?;
    let source=p.import_actual_forms(head,5)?;
    for(i,(op,change))in out.compiled().operations().iter().zip(&r.changes).enumerate(){
        assert_eq!(op.capability_id().as_str(),"search.replace_styles");assert_eq!(op.arguments().len(),12);assert_eq!(arg(op,"source_edit_domain")?,"changes");
        assert_eq!(arg(op,"request_schema")?,SCHEMA);assert_eq!(arg(op,"source_edit_index")?,i.to_string());
        assert_eq!(serde_json::from_str::<Value>(arg(op,"source_anchor_json")?)?,serde_json::to_value(&change.paragraph_anchor)?);
        assert_eq!(arg(op,"mutation_receipt_sha256")?,hex::encode(out.receipt().mutation_receipt_sha256));
        let at=source.imported().source().resolve_anchor(&change.paragraph_anchor)?;assert_eq!(at.element().ok_or("paragraph")?.name().local_name(),"p");
    }
    assert_eq!(out.with_verified_bytes(p,5,ContentDigest::of)?,direct.with_verified_bytes(p,5,ContentDigest::of)?);Ok(())
}
#[test]
fn appended_named_family_preserves_first_twenty_positions()->R{
    use hwpx_agent_cli::form_product_request::stored_literal_replacement as l;
    let old=[l::LITERAL_REPLACEMENT_PRODUCT_REQUEST_SCHEMA,l::atoms::LITERAL_TEXT_ATOM_PRODUCT_REQUEST_SCHEMA,l::review::REVIEW_LITERAL_PRODUCT_REQUEST_SCHEMA,
        l::selector::SELECTOR_LITERAL_PRODUCT_REQUEST_SCHEMA,l::regex::REGEX_REPLACEMENT_PRODUCT_REQUEST_SCHEMA,l::regex::insertions::REGEX_INSERTION_PRODUCT_REQUEST_SCHEMA,
        l::styles::CHARACTER_STYLE_PRODUCT_REQUEST_SCHEMA,l::text_styles::TEXT_STYLE_PRODUCT_REQUEST_SCHEMA,l::paragraph_styles::PARAGRAPH_STYLE_PRODUCT_REQUEST_SCHEMA,
        l::unicode::UNICODE_PRODUCT_REQUEST_SCHEMA,l::unicode::matches::UNICODE_MATCH_PRODUCT_REQUEST_SCHEMA,l::case::CASE_PRODUCT_REQUEST_SCHEMA,l::width::WIDTH_PRODUCT_REQUEST_SCHEMA,
        l::whitespace::WHITESPACE_PRODUCT_REQUEST_SCHEMA,l::controls::CONTROL_PRODUCT_REQUEST_SCHEMA,l::number_controls::NUMBER_CONTROL_PRODUCT_REQUEST_SCHEMA,
        l::sort::PARAGRAPH_SORT_PRODUCT_REQUEST_SCHEMA,l::sort_groups::PARAGRAPH_SORT_GROUPS_PRODUCT_REQUEST_SCHEMA,l::fonts::FONT_PRODUCT_REQUEST_SCHEMA,l::fonts::options::FONT_OPTIONS_REQUEST_SCHEMA];
    assert_eq!(&SCHEMAS[..20],&old);assert_eq!(SCHEMAS[20],SCHEMA);assert_eq!(SCHEMAS.len(),23);assert_eq!(SCHEMAS.iter().copied().collect::<BTreeSet<_>>().len(),23);Ok(())
}
#[test]
fn common_mutation_receipt_and_output_match_standalone_without_repreparing_owner()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=request(&s,&bytes,false)?;
    let out=common(&p,&v)?;let direct=prepare!(&p,&v)?;let Operation::SearchMutation(c)=&out else{return Err("mutation".into())};let Receipt::NamedStyle(r)=c.receipt()else{return Err("named family".into())};
    assert_eq!(r,direct.receipt());c.verify(&p,5)?;assert_eq!(out.with_verified_bytes(&p,None,5,ContentDigest::of)?,direct.with_verified_bytes(&p,5,ContentDigest::of)?);Ok(())
}
#[test]
fn separate_preview_metadata_matches_standalone_and_has_no_output()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=request(&s,&bytes,true)?;let out=common(&p,&v)?;
    let Operation::NamedStylePreview(preview)=&out else{return Err("named preview".into())};let direct=prepare!(&p,&v)?;assert_eq!(preview.verify(&p,5)?,direct.verify(&p,5)?);
    assert!(preview.receipt().preview_only&&!preview.receipt().stored.candidate_output_retained);assert_eq!(out.with_verified_preview_json(&p,None,5,<[u8]>::to_vec)?,direct.with_verified_json(&p,5,<[u8]>::to_vec)?);
    let called=Cell::new(false);assert!(matches!(out.with_verified_bytes(&p,None,5,|_|called.set(true)),Err(CommonError::PreviewOnly)));assert!(!called.get());Ok(())
}
#[test]
fn preview_rejected_by_mutation_and_compiler_before_source_reads()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=request(&s,&bytes,true)?;
    let n=s.metadata.audit_events()?.len();assert!(matches!(Mutation::prepare_json(&p,&wire(&v)?,Default::default(),Default::default(),4),Err(E::PreviewOnly)));
    assert!(matches!(Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4),Err(CompiledSearchError::Kind)));assert_eq!(s.metadata.audit_events()?.len(),n);Ok(())
}
#[test]
fn mutation_cannot_deliver_preview_json()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let out=common(&p,&request(&s,&bytes,false)?)?;let called=Cell::new(false);
    assert!(matches!(out.with_verified_preview_json(&p,None,5,|_|called.set(true)),Err(CommonError::PreviewKind)));assert!(!called.get());Ok(())
}
#[test]
fn two_named_paragraphs_compile_to_two_actual_owners_not_first_node()->R{
    let bytes=package(&(para(1,2,"KEEP")+&para(2,0,"ABC")+&para(3,1,"XYZ")))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    let v=request(&s,&bytes,false)?;let out=compile(&p,&v)?;check(&p,&v,&out)?;assert_eq!(out.receipt().structural_owner_nodes,2);
    let source=p.import_actual_forms(s.head,5)?;let nodes=&source.imported().graph().sections()[0].body.children;
    assert_eq!(out.compiled().operations()[0].target().node_id(),&nodes[1].common().node_id);assert_eq!(out.compiled().operations()[1].target().node_id(),&nodes[2].common().node_id);Ok(())
}
#[test]
fn whole_output_receipt_binds_name_query_axis_even_for_identical_changes()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let a=request(&s,&bytes,false)?;let mut b=a.clone();b["operation"]["query"]=json!("SRC First");
    let first=compile(&p,&a)?;let second=compile(&p,&b)?;assert_eq!(first.receipt().output_package_sha256,second.receipt().output_package_sha256);
    assert_ne!(first.receipt().mutation_receipt_sha256,second.receipt().mutation_receipt_sha256);assert_ne!(first.receipt().compiled_plan_sha256,second.receipt().compiled_plan_sha256);check(&p,&b,&second)?;Ok(())
}
#[test]
fn selected_second_paragraph_and_empty_run_use_original_paragraph_anchors()->R{
    let bytes=package(&(para(1,0,"KEEP")+"<hp:p id='2' styleIDRef='1' paraPrIDRef='0'><hp:run charPrIDRef='0'/></hp:p>"))?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=request(&s,&bytes,false)?;let source=p.import_actual_forms(s.head,5)?;
    v["selector"]["scope"]=json!("node_set");v["selector"]["range"]=json!({"node_ids":[source.imported().graph().sections()[0].body.children[1].common().node_id]});
    let out=compile(&p,&v)?;assert_eq!(out.receipt().source_edit_operations,1);assert_eq!(out.with_verified_bytes(&p,5,refs)??,vec![(1,Some(0),Some(0)),(2,Some(0),Some(2))]);Ok(())
}
#[test]
fn malformed_mode_and_unsafe_fields_reject_before_source_reads()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    for preview in [false,true]{let good=request(&s,&bytes,preview)?;let n=s.metadata.audit_events()?.len();
        for value in [Value::Null,json!("true"),json!({"true":null})]{let mut v=good.clone();v["operation"]["preview_only"]=value;assert!(common(&p,&v).is_err());}
        for key in ["style_filter","raw_xml","approved","plan"]{let mut v=good.clone();v["operation"][key]=json!({});assert!(common(&p,&v).is_err());}
        let mut v=good;v["operation"].as_object_mut().ok_or("op")?.remove("preview_only");assert!(common(&p,&v).is_err());assert_eq!(s.metadata.audit_events()?.len(),n);
    }Ok(())
}
#[test]
fn server_search_writer_and_metadata_limits_reach_both_common_modes()->R{
    let bytes=package(&(para(1,0,"A")+&para(2,1,"B")))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    for preview in [false,true]{let v=request(&s,&bytes,preview)?;for mode in 0..3{let mut limits=Limits::standard()?;
        match mode{0=>limits.search=SourceSearchLimits::new(Config{matches:1,..Default::default()})?,1=>limits.writer=WriterLimits::new(WriterLimitConfig{max_output_bytes:1})?,_=>limits.search=SourceSearchLimits::new(Config{result_bytes:1,..Default::default()})?}
        assert!(Dispatch::prepare_json_with_search_limits(&p,&wire(&v)?,None,limits,4).is_err());if !preview{assert!(Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,limits,4).is_err());}
    }}Ok(())
}
#[test]
fn current_write_access_and_foreign_provider_block_preview_and_compiled_bytes()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let preview=common(&p,&request(&s,&bytes,true)?)?;let out=compile(&p,&request(&s,&bytes,false)?)?;
    let reader=s.provider()?;let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("foreign-named")?)?;let called=Cell::new(false);
    for bound in [&reader,&other]{assert!(preview.with_verified_preview_json(bound,None,5,|_|called.set(true)).is_err());assert!(out.with_verified_bytes(bound,5,|_|called.set(true)).is_err());}assert!(!called.get());Ok(())
}
#[test]
fn acl_revoke_and_regrant_are_fresh_for_both_common_modes()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let preview=common(&p,&request(&s,&bytes,true)?)?;let out=compile(&p,&request(&s,&bytes,false)?)?;
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;let called=Cell::new(false);
    assert!(preview.with_verified_preview_json(&p,None,6,|_|called.set(true)).is_err());assert!(out.verify(&p,6).is_err());assert!(out.with_verified_bytes(&p,6,|_|called.set(true)).is_err());assert!(!called.get());
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;out.verify(&p,8)?;preview.with_verified_preview_json(&p,None,8,|_|())?;Ok(())
}
#[test]
fn quarantine_and_ciphertext_tamper_block_both_retained_modes()->R{
    for tamper in [false,true]{let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let preview=common(&p,&request(&s,&bytes,true)?)?;let out=compile(&p,&request(&s,&bytes,false)?)?;
        if tamper{s.blobs.tamper.store(true,Ordering::SeqCst);}else{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("COMMON_NAMED_STYLE")?,5)?;}
        let called=Cell::new(false);assert!(preview.with_verified_preview_json(&p,None,6,|_|called.set(true)).is_err());assert!(out.with_verified_bytes(&p,6,|_|called.set(true)).is_err());assert!(!called.get());
    }Ok(())
}
#[test]
fn common_modes_keep_head_ingest_and_route_denial_and_redact_private_inputs()->R{
    let bytes=raw("PRIVATE-TEXT")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let preview=common(&p,&request(&s,&bytes,true)?)?;let out=compile(&p,&request(&s,&bytes,false)?)?;
    assert!(preview.require_current_product_route(&p,None,5).is_err());assert!(out.require_current_product_route(&p,5).is_err());assert!(!out.receipt().execution_authority);
    for text in [format!("{out:?}{preview:?}"),serde_json::to_string(out.compiled())?]{assert!(!text.contains("PRIVATE-")&&!text.contains("<hp:")&&!text.contains("SRC"));}
    assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
}
fn final_head_race(stage:usize)->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let pv=request(&s,&bytes,true)?;let mv=request(&s,&bytes,false)?;let preview=common(&p,&pv)?;let out=compile(&p,&mv)?;
    let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,
        ContentDigest::of(b"common-named-race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation fixture"),ContentDigest::of(b"transaction fixture"))?;
    let repo=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
    let bound=StoredFormProvider::bind(&s.artifacts,&repo,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
    match stage{0=>{Dispatch::prepare_json(&bound,&wire(&pv)?,None,5)?;},1=>{preview.with_verified_preview_json(&bound,None,5,|_|())?;},2=>{Dispatch::prepare_compiled_search_json(&bound,&wire(&mv)?,Limits::standard()?,5)?;},3=>{out.verify(&bound,5)?;},_=>{out.with_verified_bytes(&bound,5,|_|())?;}}
    let calls=repo.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);repo.repository().calls.store(0,Ordering::SeqCst);repo.repository().trigger.store(calls,Ordering::SeqCst);let called=Cell::new(false);
    match stage{0=>assert!(Dispatch::prepare_json(&bound,&wire(&pv)?,None,6).is_err()),1=>assert!(preview.with_verified_preview_json(&bound,None,6,|_|called.set(true)).is_err()),2=>assert!(Dispatch::prepare_compiled_search_json(&bound,&wire(&mv)?,Limits::standard()?,6).is_err()),3=>assert!(out.verify(&bound,6).is_err()),_=>assert!(out.with_verified_bytes(&bound,6,|_|called.set(true)).is_err())}
    assert!(!called.get());assert_eq!(repo.repository().calls.load(Ordering::SeqCst),calls);Ok(())
}
#[test]fn preview_preparation_final_head_race_rejects()->R{final_head_race(0)}
#[test]fn preview_delivery_final_head_race_blocks_consumer()->R{final_head_race(1)}
#[test]fn post_compiler_final_head_race_rejects()->R{final_head_race(2)}
#[test]fn compiled_retained_verification_final_head_race_rejects()->R{final_head_race(3)}
#[test]fn compiled_output_final_head_race_blocks_consumer()->R{final_head_race(4)}
