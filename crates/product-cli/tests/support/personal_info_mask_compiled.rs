//! Mutation-only mode, original edit inventory and actual common operation compiler. No Native/DB.
use super::*;
use sha2::{Digest as _,Sha256};
use hwpx_agent_cli::form_product_request::{stored_literal_replacement::personal_info::StoredPersonalInfoMaskMutationRequest as Mutation,
    stored_operations::{StoredProductRequest as Dispatch,PreparedStoredProductOperation as Operation,StoredProductOperationError as CommonError,
        search_mutations::{SearchMutationLimits as Limits,SearchMutationReceiptRef as Receipt,SEARCH_MUTATION_REQUEST_SCHEMAS as SCHEMAS},
        compiled_search::{PreparedCompiledSearchMutation as Compiled,CompiledSearchError}}};
fn common(p:&Provider<'_>,v:&Value)->Result<Operation,Box<dyn Error>>{Ok(Dispatch::prepare_json(p,&wire(v)?,None,4)?)}
fn compile(p:&Provider<'_>,v:&Value)->Result<Compiled,Box<dyn Error>>{Ok(Dispatch::prepare_compiled_search_json(p,&wire(v)?,Limits::standard()?,4)?)}
fn arg<'a>(op:&'a domain_ir::CompiledOperation,key:&str)->Result<&'a str,Box<dyn Error>>{let domain_ir::CanonicalArgumentValue::Text(v)=op.arguments().get(key).ok_or("argument")?.value()else{return Err("text argument".into())};Ok(v)}
#[test]
fn appended_twenty_third_family_preserves_original_twenty_two_schema_positions()->R{
    use hwpx_agent_cli::form_product_request::stored_literal_replacement as l;
    let old=[l::LITERAL_REPLACEMENT_PRODUCT_REQUEST_SCHEMA,l::atoms::LITERAL_TEXT_ATOM_PRODUCT_REQUEST_SCHEMA,l::review::REVIEW_LITERAL_PRODUCT_REQUEST_SCHEMA,l::selector::SELECTOR_LITERAL_PRODUCT_REQUEST_SCHEMA,
        l::regex::REGEX_REPLACEMENT_PRODUCT_REQUEST_SCHEMA,l::regex::insertions::REGEX_INSERTION_PRODUCT_REQUEST_SCHEMA,l::styles::CHARACTER_STYLE_PRODUCT_REQUEST_SCHEMA,l::text_styles::TEXT_STYLE_PRODUCT_REQUEST_SCHEMA,
        l::paragraph_styles::PARAGRAPH_STYLE_PRODUCT_REQUEST_SCHEMA,l::unicode::UNICODE_PRODUCT_REQUEST_SCHEMA,l::unicode::matches::UNICODE_MATCH_PRODUCT_REQUEST_SCHEMA,l::case::CASE_PRODUCT_REQUEST_SCHEMA,
        l::width::WIDTH_PRODUCT_REQUEST_SCHEMA,l::whitespace::WHITESPACE_PRODUCT_REQUEST_SCHEMA,l::controls::CONTROL_PRODUCT_REQUEST_SCHEMA,l::number_controls::NUMBER_CONTROL_PRODUCT_REQUEST_SCHEMA,
        l::sort::PARAGRAPH_SORT_PRODUCT_REQUEST_SCHEMA,l::sort_groups::PARAGRAPH_SORT_GROUPS_PRODUCT_REQUEST_SCHEMA,l::fonts::FONT_PRODUCT_REQUEST_SCHEMA,l::fonts::options::FONT_OPTIONS_REQUEST_SCHEMA,
        l::named_styles::NAMED_STYLE_PRODUCT_REQUEST_SCHEMA,l::named_styles::options::NAMED_STYLE_OPTIONS_REQUEST_SCHEMA];
    assert_eq!(&SCHEMAS[..22],&old);assert_eq!(SCHEMAS[22],SCHEMA);assert_eq!(SCHEMAS.len(),23);assert_eq!(SCHEMAS.iter().copied().collect::<BTreeSet<_>>().len(),23);Ok(())
}
#[test]
fn common_mask_receipt_and_output_match_standalone_owned_candidate()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=request(&s,&bytes,false)?;let out=common(&p,&v)?;let direct=prepare!(&p,&v)?;
    let Operation::SearchMutation(c)=&out else{return Err("mutation".into())};let Receipt::PersonalInfoMask(r)=c.receipt()else{return Err("personal info".into())};
    assert_eq!(r,direct.receipt());c.verify(&p,5)?;assert_eq!(out.with_verified_bytes(&p,None,5,ContentDigest::of)?,direct.with_verified_bytes(&p,5,ContentDigest::of)?);
    let called=Cell::new(false);assert!(matches!(out.with_verified_preview_json(&p,None,5,|_|called.set(true)),Err(CommonError::PreviewKind)));assert!(!called.get());Ok(())
}
#[test]
fn physically_separate_mask_preview_matches_metadata_and_never_delivers_a_file()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=request(&s,&bytes,true)?;let out=common(&p,&v)?;let direct=prepare!(&p,&v)?;
    let Operation::PersonalInfoMaskPreview(preview)=&out else{return Err("mask preview".into())};assert_eq!(preview.verify(&p,5)?,direct.verify(&p,5)?);
    assert_eq!(out.with_verified_preview_json(&p,None,5,<[u8]>::to_vec)?,direct.with_verified_json(&p,5,<[u8]>::to_vec)?);let called=Cell::new(false);
    assert!(matches!(out.with_verified_bytes(&p,None,5,|_|called.set(true)),Err(CommonError::PreviewOnly)));assert!(!called.get());Ok(())
}
#[test]
fn preview_is_rejected_by_mutation_and_compiler_before_any_source_read()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=request(&s,&bytes,true)?;let before=s.metadata.audit_events()?.len();
    assert!(matches!(Mutation::prepare_json(&p,&wire(&v)?,Default::default(),Default::default(),4),Err(E::PreviewOnly)));
    assert!(matches!(Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4),Err(CompiledSearchError::Kind)));assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn missing_preview_bad_policy_and_unknown_version_reject_before_common_reads()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes,false)?;let before=s.metadata.audit_events()?.len();
    let mut v=good.clone();v["operation"].as_object_mut().ok_or("operation")?.remove("preview_only");assert!(common(&p,&v).is_err());
    let mut v=good.clone();v["operation"]["mask_policy"]=json!("native_default");assert!(compile(&p,&v).is_err());let mut v=good;v["schema_version"]=json!("hwpx-agent.product-personal-info-selection-mask-request/v999");assert!(common(&p,&v).is_err());assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn compiled_mask_targets_actual_text_anchors_and_locks_twelve_arguments()->R{
    let bytes=raw("PRIVATE-MASK-ORIGINAL")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=request(&s,&bytes,false)?;let c=compile(&p,&v)?;
    assert_eq!(c.receipt().source_edit_operations,1);assert_eq!(c.receipt().structural_owner_nodes,1);assert!(!serde_json::to_string(c.compiled())?.contains("PRIVATE-"));
    let op=&c.compiled().operations()[0];assert_eq!(op.arguments().len(),12);assert_eq!(arg(op,"source_edit_domain")?,"selected_mask_text_splices");assert_eq!(arg(op,"request_schema")?,SCHEMA);
    let a:domain_ir::SourceAnchorHandle=serde_json::from_str(arg(op,"source_anchor_json")?)?;let source=p.import_actual_forms(s.head,5)?;assert_eq!(source.imported().source().resolve_anchor(&a)?.element().ok_or("t")?.name().local_name(),"t");
    let original=source.imported().lower_personal_info_mask_candidate(&bytes,Scope::Document,policy(),Mask::PerOriginalScalarPreserveSlots,Default::default(),Default::default())?;
    assert_eq!(c.receipt().mutation_receipt_sha256,<[u8;32]>::from(Sha256::digest(serde_json::to_vec(original.receipt())?)));
    assert_eq!(c.receipt().edit_inventory_sha256,original.edit_inventory().canonical_sha256());assert_eq!(c.receipt().mutation_receipt_sha256,original.edit_inventory().receipt_sha256());Ok(())
}
#[test]
fn many_mask_components_in_one_text_have_one_actual_edit_not_scalar_count_operations()->R{
    let bytes=raw("A*B*C*D")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=request(&s,&bytes,false)?;let direct=prepare!(&p,&v)?;let c=compile(&p,&v)?;
    assert_eq!(direct.receipt().stored.output.changed_components,4);assert_eq!(c.receipt().source_edit_operations,1);assert_eq!(c.with_verified_bytes(&p,5,ContentDigest::of)?,direct.with_verified_bytes(&p,5,ContentDigest::of)?);Ok(())
}
#[test]
fn cross_run_text_edits_resolve_one_original_paragraph_owner_without_collapsing_runs()->R{
    let bytes=definition::package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>AB</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>CD</hp:t></hp:run></hp:p>")?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let c=compile(&p,&request(&s,&bytes,false)?)?;
    assert_eq!(c.receipt().source_edit_operations,2);assert_eq!(c.receipt().structural_owner_nodes,1);assert!(c.with_verified_bytes(&p,5,section)??.contains("charPrIDRef='1'><hp:t>**"));Ok(())
}
#[test]
fn selected_partial_text_plan_preserves_nonselected_original_content()->R{
    let bytes=raw("A&amp;B PRIVATE-TAIL")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=request(&s,&bytes,false)?;let inv=inventory(&p,&v)?;
    v["selector"]["scope"]=json!("selection");v["selector"]["range"]=selection(&inv,1,2)?;let c=compile(&p,&v)?;
    assert_eq!(c.receipt().source_edit_operations,1);assert!(c.with_verified_bytes(&p,5,section)??.contains("A*B PRIVATE-TAIL"));Ok(())
}
#[test]
fn policy_key_and_plan_change_bound_plans_even_when_masked_bytes_are_equal()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes,false)?;let a=compile(&p,&good)?;
    for mode in 0..3{let mut v=good.clone();match mode{0=>v["operation"]["mask_policy"]=json!("three_asterisks_per_text_group"),1=>v["idempotency_key"]=json!("OTHER-PRIVATE-KEY"),_=>v["plan_id"]=json!("second-mask-plan")};let b=compile(&p,&v)?;
        assert_eq!(a.receipt().output_package_sha256,b.receipt().output_package_sha256);assert_ne!(a.receipt().compiled_plan_sha256,b.receipt().compiled_plan_sha256);}Ok(())
}
#[test]
fn compiled_receipts_and_debug_never_include_original_text_or_per_value_hash_fields()->R{
    let bytes=raw("PRIVATE-SENSITIVE-TEXT")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let c=compile(&p,&request(&s,&bytes,false)?)?;
    let text=format!("{c:?}{:?}{}",c.receipt(),serde_json::to_string(c.compiled())?);assert!(!text.contains("PRIVATE-")&&!text.contains("source_span_sha256")&&!text.contains("source_text_sha256"));Ok(())
}
#[test]
fn acl_revocation_blocks_compiled_and_preview_delivery_then_regrant_rechecks()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let c=compile(&p,&request(&s,&bytes,false)?)?;let preview=common(&p,&request(&s,&bytes,true)?)?;
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;let called=Cell::new(false);assert!(c.verify(&p,6).is_err());assert!(c.with_verified_bytes(&p,6,|_|called.set(true)).is_err());assert!(preview.with_verified_preview_json(&p,None,6,|_|called.set(true)).is_err());assert!(!called.get());
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;c.verify(&p,8)?;preview.with_verified_preview_json(&p,None,8,|_|())?;Ok(())
}
#[test]
fn quarantine_blocks_compiled_output_without_calling_consumer()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let c=compile(&p,&request(&s,&bytes,false)?)?;
    s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("MASK_COMPILED_TEST")?,5)?;let called=Cell::new(false);assert!(c.with_verified_bytes(&p,6,|_|called.set(true)).is_err());assert!(!called.get());Ok(())
}
#[test]
fn ciphertext_tamper_blocks_compiled_output_without_calling_consumer()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let c=compile(&p,&request(&s,&bytes,false)?)?;s.blobs.tamper.store(true,Ordering::SeqCst);
    let called=Cell::new(false);assert!(c.verify(&p,6).is_err());assert!(c.with_verified_bytes(&p,6,|_|called.set(true)).is_err());assert!(!called.get());Ok(())
}
#[test]
fn common_server_component_writer_and_metadata_limits_remain_strict()->R{
    let bytes=definition::package(&(para(1,"A")+&para(2,"B")))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=request(&s,&bytes,false)?;
    let mut limits=Limits::standard()?;limits.search=SourceSearchLimits::new(Config{matches:1,..Default::default()})?;
    assert!(Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,limits,4).is_err());let mut limits=Limits::standard()?;limits.writer=WriterLimits::new(WriterLimitConfig{max_output_bytes:1})?;
    assert!(Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,limits,4).is_err());Ok(())
}
fn compiled_race(stage:usize)->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=request(&s,&bytes,false)?;let out=compile(&p,&v)?;
    let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,
        ContentDigest::of(b"compiled-mask-race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation fixture"),ContentDigest::of(b"transaction fixture"))?;
    let repo=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
    let bound=StoredFormProvider::bind(&s.artifacts,&repo,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
    match stage{0=>{Dispatch::prepare_compiled_search_json(&bound,&wire(&v)?,Limits::standard()?,5)?;},1=>{out.verify(&bound,5)?;},_=>{out.with_verified_bytes(&bound,5,|_|())?;}}
    let n=repo.repository().calls.load(Ordering::SeqCst);assert!(n>=4);repo.repository().calls.store(0,Ordering::SeqCst);repo.repository().trigger.store(n,Ordering::SeqCst);let called=Cell::new(false);
    match stage{0=>assert!(Dispatch::prepare_compiled_search_json(&bound,&wire(&v)?,Limits::standard()?,6).is_err()),1=>assert!(out.verify(&bound,6).is_err()),_=>assert!(out.with_verified_bytes(&bound,6,|_|called.set(true)).is_err())}assert!(!called.get());assert_eq!(repo.repository().calls.load(Ordering::SeqCst),n);Ok(())
}
#[test]fn final_compilation_head_race_rejects()->R{compiled_race(0)}
#[test]fn final_compiled_verify_head_race_rejects()->R{compiled_race(1)}
#[test]fn final_compiled_delivery_head_race_blocks_consumer()->R{compiled_race(2)}
#[test]
fn compiled_and_preview_paths_preserve_source_and_head_and_keep_route_unqualified()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let c=compile(&p,&request(&s,&bytes,false)?)?;let preview=common(&p,&request(&s,&bytes,true)?)?;
    assert!(!c.receipt().execution_authority);assert!(c.require_current_product_route(&p,5).is_err());assert!(preview.require_current_product_route(&p,None,5).is_err());assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);
    assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);assert_eq!(s.artifacts.download(&s.reader,s.result,5)?,bytes);Ok(())
}
