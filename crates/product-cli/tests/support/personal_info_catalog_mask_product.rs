// Strict catalog mask products and the real shared operation compiler; no Native or operational DB.
mod routing{include!("personal_info_catalog_mask_routing.rs");}
use super::*;
use hwpx_agent_cli::form_product_request::{stored_literal_replacement::personal_info::catalog::{StoredPersonalInfoCatalogMaskProductRequest as CP,
    PreparedStoredPersonalInfoCatalogMaskProduct as Prepared,PersonalInfoCatalogMaskProductError as PE,PERSONAL_INFO_CATALOG_MASK_PRODUCT_SCHEMA as CS},
    stored_operations::{StoredProductRequest as Dispatch,search_mutations::SearchMutationLimits as Limits,
        compiled_search::catalog_mask::{PreparedCompiledCatalogMask as Compiled,CatalogMaskCompilationError as CompileError}}};
fn req(s:&StoredFixture,bytes:&[u8],f:&Feed,preview:bool)->Result<Value,Box<dyn Error>>{
    let mut v=request(s,bytes,preview)?;v["schema_version"]=json!(CS);v["expected_catalog_sha256"]=json!(hex::encode(sha(f)));
    v["operation"]=json!({"kind":"mask_personal_info_catalog","families":FAMILIES,"mask_policy":"per_original_scalar_preserve_slots",
        "max_matches":10000,"max_changed_components":10000,"review_policy":policy(),"preview_only":preview});Ok(v)
}
fn product(p:&Provider<'_>,f:&Feed,v:&Value)->Result<Prepared,Box<dyn Error>>{Ok(CP::prepare_json(p,f,&wire(v)?,Default::default(),Default::default(),4)?)}
fn compile(p:&Provider<'_>,f:&Feed,v:&Value)->Result<Compiled,Box<dyn Error>>{Ok(Dispatch::prepare_compiled_catalog_mask_json(p,f,&wire(v)?,Limits::standard()?,4)?)}
fn arg<'a>(op:&'a domain_ir::CompiledOperation,key:&str)->Result<&'a str,Box<dyn Error>>{
    let domain_ir::CanonicalArgumentValue::Text(value)=op.arguments().get(key).ok_or("argument")?.value()else{return Err("argument type".into())};Ok(value)
}
fn rejected_before_reads(p:&Provider<'_>,s:&StoredFixture,f:&Feed,raw:&[u8])->R{
    let reads=f.reads.get();let events=s.metadata.audit_events()?.len();assert!(CP::prepare_json(p,f,raw,Default::default(),Default::default(),4).is_err());
    assert_eq!(f.reads.get(),reads);assert_eq!(s.metadata.audit_events()?.len(),events);Ok(())
}
#[test]
fn explicit_synthetic_catalog_never_uses_an_installed_or_private_default()->R{
    let bytes=raw("KEEP MARK END")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=product(&p,&f,&req(&s,&bytes,&f,false)?)?;
    assert_eq!(out.receipt().stored.output.catalog.total_patterns,64);assert_eq!(out.receipt().stored.output.selected_patterns,64);
    assert!(out.with_verified_bytes(&p,&f,5,section)??.contains("KEEP **** END"));assert!(!out.receipt().native_cas_execution_publication_authority);Ok(())
}
#[test]
fn product_and_original_stored_mask_have_identical_bound_output()->R{
    let bytes=raw("KEEP MARK END")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");
    let direct=p.import_actual_forms(s.head,4)?.into_personal_info_catalog_mask_candidate(
        &p,&f,sha(&f),&FAMILIES,Scope::Document,policy(),Mask::PerOriginalScalarPreserveSlots,Default::default(),Default::default(),4)?;
    let out=product(&p,&f,&req(&s,&bytes,&f,false)?)?;assert_eq!(&out.receipt().stored,direct.receipt());
    assert_eq!(out.with_verified_bytes(&p,&f,5,ContentDigest::of)?,direct.with_verified_bytes(&p,&f,5,ContentDigest::of)?);Ok(())
}
#[test]
fn missing_root_fields_reject_before_document_or_catalog_reads()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let good=req(&s,&bytes,&f,false)?;
    for key in ["schema_version","idempotency_key","project_id","document_id","base_revision","expected_head_generation","expected_source_package_sha256","expected_catalog_sha256","plan_id","selector","operation"]{
        let mut v=good.clone();v.as_object_mut().ok_or("root")?.remove(key);rejected_before_reads(&p,&s,&f,&wire(&v)?)?;}Ok(())
}
#[test]
fn missing_operation_or_selector_fields_reject_before_reads()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let good=req(&s,&bytes,&f,false)?;
    for key in ["kind","families","mask_policy","max_matches","max_changed_components","review_policy","preview_only"]{
        let mut v=good.clone();v["operation"].as_object_mut().ok_or("operation")?.remove(key);rejected_before_reads(&p,&s,&f,&wire(&v)?)?;}
    for key in ["scope","revision_id"]{let mut v=good.clone();v["selector"].as_object_mut().ok_or("selector")?.remove(key);rejected_before_reads(&p,&s,&f,&wire(&v)?)?;}Ok(())
}
#[test]
fn arbitrary_paths_patterns_approval_and_replacement_fields_reject_before_reads()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let good=req(&s,&bytes,&f,false)?;
    for location in ["root","operation"]{for key in ["catalog_path","source_path","patterns","rules","approved","replacement","raw_xml","native_defaults"]{
        let mut v=good.clone();if location=="root"{v[key]=json!("PRIVATE");}else{v["operation"][key]=json!("PRIVATE");}rejected_before_reads(&p,&s,&f,&wire(&v)?)?;}}Ok(())
}
#[test]
fn enum_objects_and_wrong_scalar_policy_types_reject_before_reads()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let good=req(&s,&bytes,&f,false)?;
    for(key,value)in [("kind",json!({"mask_personal_info_catalog":null})),("mask_policy",json!({"per_original_scalar_preserve_slots":null})),
        ("families",json!([{"telephone":null}])),("families",json!(["address"])),("preview_only",json!(1)),("max_matches",json!(true)),("review_policy",json!([]))]{
        let mut v=good.clone();v["operation"][key]=value;rejected_before_reads(&p,&s,&f,&wire(&v)?)?;}Ok(())
}
#[test]
fn escaped_duplicate_keys_trailing_json_and_wrong_schema_reject_before_reads()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let good=String::from_utf8(wire(&req(&s,&bytes,&f,false)?)?)?;
    for text in [good.replace("\"max_matches\":10000","\"max_matches\":10000,\"max_mat\\u0063hes\":1"),format!("{good} {{}}"),"null".into(),"[]".into(),good.replace(CS,"unknown/v2")]{
        rejected_before_reads(&p,&s,&f,text.as_bytes())?;}Ok(())
}
#[test]
fn empty_duplicate_families_invalid_digest_and_count_ranges_reject_before_reads()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let good=req(&s,&bytes,&f,false)?;
    for value in [json!([]),json!(["telephone","telephone"]),Value::Null]{let mut v=good.clone();v["operation"]["families"]=value;rejected_before_reads(&p,&s,&f,&wire(&v)?)?;}
    for key in ["max_matches","max_changed_components"]{for n in [0,10001]{let mut v=good.clone();v["operation"][key]=json!(n);rejected_before_reads(&p,&s,&f,&wire(&v)?)?;}}
    for key in ["expected_source_package_sha256","expected_catalog_sha256"]{let mut v=good.clone();v[key]=json!("NOT_A_DIGEST");rejected_before_reads(&p,&s,&f,&wire(&v)?)?;}Ok(())
}
#[test]
fn oversized_raw_request_is_not_read_or_truncated()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");
    rejected_before_reads(&p,&s,&f,&vec![b' ';16385])?;Ok(())
}
#[test]
fn document_scope_rejects_foreign_range_and_revision_shape_before_reads()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let good=req(&s,&bytes,&f,false)?;
    for value in [json!({"scope":"document","revision_id":good["base_revision"],"section_ids":[]}),json!({"scope":"document","revision_id":good["base_revision"],"range":{}}),json!({"scope":{"document":null},"revision_id":good["base_revision"]})]{
        let mut v=good.clone();v["selector"]=value;rejected_before_reads(&p,&s,&f,&wire(&v)?)?;}Ok(())
}
#[test]
fn all_four_selectors_bind_the_original_scope_without_widening_masked_text()->R{
    let bytes=definition::package(&(para(1,"MARK MARK")+&para(2,"MARK")))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let good=req(&s,&bytes,&f,false)?;
    let mut base=good.clone();base.as_object_mut().ok_or("request")?.remove("expected_catalog_sha256");let inv=inventory(&p,&base)?;
    let node=inv["inventory"]["nodes"].as_array().ok_or("nodes")?.iter().find(|n|n["source_handle"]==inv["inventory"]["blocks"][0]["paragraph_handle"]).ok_or("node")?;
    for mode in 0..4{let mut v=good.clone();match mode{0=>{},1=>{v["selector"]["scope"]=json!("section");v["selector"]["section_ids"]=inv["inventory"]["section_ids"].clone();},
        2=>{v["selector"]["scope"]=json!("node_set");v["selector"]["range"]=json!({"node_ids":[node["node_id"]]});},_=>{v["selector"]["scope"]=json!("selection");v["selector"]["range"]=selection(&inv,5,9)?;}}
        let out=product(&p,&f,&v)?;assert_eq!(out.receipt().stored.output.matched_formats,if mode<2{3}else if mode==2{2}else{1});
        let c=compile(&p,&f,&v)?;assert_eq!(c.receipt().output_package_sha256,out.receipt().stored.output.output_package_sha256);
        if mode==3{let xml=c.with_verified_bytes(&p,&f,5,section)??;assert!(xml.contains("MARK ****")&&xml.contains(">MARK<"));}}
    Ok(())
}
#[test]
fn raw_canonical_and_key_plan_bindings_do_not_conflate_equal_output()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let good=req(&s,&bytes,&f,false)?;let a=product(&p,&f,&good)?;
    let pretty=serde_json::to_vec_pretty(&good)?;let b=CP::prepare_json(&p,&f,&pretty,Default::default(),Default::default(),4)?;
    assert_ne!(a.receipt().raw_request_sha256,b.receipt().raw_request_sha256);assert_eq!(a.receipt().canonical_request_sha256,b.receipt().canonical_request_sha256);
    for key in ["idempotency_key","plan_id"]{let mut v=good.clone();v[key]=json!("different-bound-identity");let b=product(&p,&f,&v)?;
        assert_ne!(a.receipt().scoped_request_sha256,b.receipt().scoped_request_sha256);assert_eq!(a.receipt().stored.output.output_package_sha256,b.receipt().stored.output.output_package_sha256);}Ok(())
}
#[test]
fn selected_family_order_is_bound_without_mutating_catalog_or_output()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let mut v=req(&s,&bytes,&f,false)?;let a=product(&p,&f,&v)?;
    v["operation"]["families"].as_array_mut().ok_or("families")?.reverse();let b=product(&p,&f,&v)?;assert_ne!(a.receipt().canonical_request_sha256,b.receipt().canonical_request_sha256);
    assert_eq!(a.receipt().stored.output.catalog,b.receipt().stored.output.catalog);assert_eq!(a.receipt().stored.output.output_package_sha256,b.receipt().stored.output.output_package_sha256);Ok(())
}
#[test]
fn changed_source_or_catalog_digest_cannot_prepare_an_output()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let good=req(&s,&bytes,&f,false)?;
    for key in ["expected_source_package_sha256","expected_catalog_sha256"]{let mut v=good.clone();v[key]=json!("a".repeat(64));assert!(product(&p,&f,&v).is_err());}Ok(())
}
#[test]
fn preparation_rechecks_catalog_after_outer_product_serialization()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let v=req(&s,&bytes,&f,false)?;f.replace_at.set(3);
    assert!(product(&p,&f,&v).is_err());assert_eq!(f.reads.get(),3);Ok(())
}
#[test]
fn retained_product_config_drift_blocks_bytes_metadata_and_verify()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=product(&p,&f,&req(&s,&bytes,&f,false)?)?;
    f.raw.borrow_mut()[2]^=1;let called=Cell::new(false);assert!(out.with_verified_bytes(&p,&f,5,|_|called.set(true)).is_err());
    assert!(out.with_verified_json(&p,&f,5,|_|called.set(true)).is_err());assert!(out.verify(&p,&f,5).is_err());assert!(!called.get());Ok(())
}
#[test]
fn final_catalog_race_blocks_outer_metadata_and_byte_consumers()->R{
    for preview in [false,true]{for metadata in [false,true]{let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=product(&p,&f,&req(&s,&bytes,&f,preview)?)?;
        f.replace_at.set(f.reads.get()+2);let called=Cell::new(false);let failed=if metadata{out.with_verified_json(&p,&f,5,|_|called.set(true)).is_err()}else{out.with_verified_bytes(&p,&f,5,|_|called.set(true)).is_err()};
        assert!(failed&&!called.get());}}Ok(())
}
#[test]
fn match_and_component_budgets_are_distinct_and_both_enforced()->R{
    let bytes=raw("MARK MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let mut v=req(&s,&bytes,&f,false)?;
    v["operation"]["max_matches"]=json!(1);assert!(product(&p,&f,&v).is_err());v["operation"]["max_matches"]=json!(2);v["operation"]["max_changed_components"]=json!(1);
    assert!(product(&p,&f,&v).is_err());v["operation"]["max_changed_components"]=json!(2);product(&p,&f,&v)?;
    let bytes=definition::package("<hp:p id='1' styleIDRef='0' paraPrIDRef='0'><hp:run charPrIDRef='0'><hp:t>MA</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>RK</hp:t></hp:run></hp:p>")?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=req(&s,&bytes,&f,false)?;v["operation"]["max_changed_components"]=json!(1);assert!(product(&p,&f,&v).is_err());Ok(())
}
#[test]
fn one_match_can_have_two_components_without_request_match_budget_shrinking_server_budget()->R{
    let bytes=definition::package("<hp:p id='1' styleIDRef='0' paraPrIDRef='0'><hp:run charPrIDRef='0'><hp:t>KEEP MA</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>RK END</hp:t></hp:run></hp:p>")?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let mut v=req(&s,&bytes,&f,false)?;
    v["operation"]["max_matches"]=json!(1);v["operation"]["max_changed_components"]=json!(2);let out=product(&p,&f,&v)?;
    assert_eq!(out.receipt().stored.output.matched_formats,1);assert_eq!(out.receipt().stored.output.changed_components,2);let c=compile(&p,&f,&v)?;
    assert_eq!(c.receipt().source_edit_operations,2);v["operation"]["mask_policy"]=json!("three_asterisks_per_text_group");v["operation"]["max_changed_components"]=json!(1);
    let fixed=product(&p,&f,&v)?;assert_eq!(fixed.receipt().stored.output.changed_components,1);assert_eq!(compile(&p,&f,&v)?.receipt().source_edit_operations,2);Ok(())
}
#[test]
fn request_maxima_never_raise_a_smaller_validated_server_budget()->R{
    let bytes=raw("MARK MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let v=req(&s,&bytes,&f,false)?;
    let limits=SourceSearchLimits::new(Config{matches:1,..Default::default()})?;
    assert!(CP::prepare_json(&p,&f,&wire(&v)?,limits,Default::default(),4).is_err());Ok(())
}
#[test]
fn metadata_limit_covers_the_entire_product_envelope()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let v=req(&s,&bytes,&f,false)?;
    let out=product(&p,&f,&v)?;let size=out.with_verified_json(&p,&f,5,|b|b.len())?;
    for n in [size,size-1]{let limits=SourceSearchLimits::new(Config{result_bytes:n,..Default::default()})?;let result=CP::prepare_json(&p,&f,&wire(&v)?,limits,Default::default(),4);
        if n==size{result?;}else{assert!(result.is_err());}}Ok(())
}
#[test]
fn preview_has_metadata_but_no_output_or_compile_conversion()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=product(&p,&f,&req(&s,&bytes,&f,true)?)?;
    assert!(out.receipt().preview_only&&!out.receipt().stored.candidate_output_retained);let called=Cell::new(false);
    assert!(matches!(out.with_verified_bytes(&p,&f,5,|_|called.set(true)),Err(PE::PreviewOnly)));assert!(!called.get());out.with_verified_json(&p,&f,5,|_|())?;
    assert!(matches!(out.compile(&p,&f,5),Err(CompileError::Product(PE::PreviewOnly))));Ok(())
}
#[test]
fn compiled_entry_rejects_preview_before_source_and_configuration_reads()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let v=req(&s,&bytes,&f,true)?;let before=s.metadata.audit_events()?.len();
    assert!(matches!(Dispatch::prepare_compiled_catalog_mask_json(&p,&f,&wire(&v)?,Limits::standard()?,4),Err(CompileError::Product(PE::PreviewOnly))));
    assert_eq!(f.reads.get(),0);assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn context_free_common_dispatcher_does_not_substitute_cached_catalog_or_legacy_mask()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let v=req(&s,&bytes,&f,false)?;let before=s.metadata.audit_events()?.len();
    assert!(Dispatch::prepare_json(&p,&wire(&v)?,None,4).is_err());assert!(Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4).is_err());
    assert_eq!(f.reads.get(),0);assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn shared_compiler_binds_twelve_arguments_and_actual_source_owners()->R{
    let bytes=raw("KEEP MARK END")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let c=compile(&p,&f,&req(&s,&bytes,&f,false)?)?;
    assert_eq!(c.receipt().source_edit_operations,1);assert_eq!(c.receipt().structural_owner_nodes,1);assert!(!c.receipt().execution_authority);
    let op=&c.compiled().operations()[0];assert_eq!(op.arguments().len(),12);assert_eq!(arg(op,"source_edit_domain")?,"catalog_matched_mask_text_splices");
    assert_eq!(arg(op,"request_schema")?,CS);assert_eq!(arg(op,"owner_binding_profile")?,"actual_structural_owner_with_exact_source_edit/v1");
    assert_eq!(op.capability_id().as_str(),"search.personal_info_find_replace");assert_eq!(c.with_verified_bytes(&p,&f,5,ContentDigest::of)?.as_bytes(),&c.receipt().output_package_sha256);Ok(())
}
#[test]
fn multiple_format_matches_in_one_text_slot_compile_one_real_edit()->R{
    let bytes=raw("MARK MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let c=compile(&p,&f,&req(&s,&bytes,&f,false)?)?;
    assert_eq!(c.receipt().source_edit_operations,1);assert!(c.with_verified_bytes(&p,&f,5,section)??.contains("**** ****"));Ok(())
}
#[test]
fn cross_run_match_compiles_exact_two_text_anchors_to_one_actual_paragraph()->R{
    let bytes=definition::package("<hp:p id='1' styleIDRef='0' paraPrIDRef='0'><hp:run charPrIDRef='0'><hp:t>KEEP MA</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>RK END</hp:t></hp:run></hp:p>")?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let c=compile(&p,&f,&req(&s,&bytes,&f,false)?)?;
    assert_eq!(c.receipt().source_edit_operations,2);assert_eq!(c.receipt().structural_owner_nodes,1);let xml=c.with_verified_bytes(&p,&f,5,section)??;
    assert!(xml.contains("KEEP **")&&xml.contains("** END")&&xml.contains("charPrIDRef='1'"));Ok(())
}
#[test]
fn equal_output_with_different_key_or_plan_has_a_different_compiled_plan()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let good=req(&s,&bytes,&f,false)?;let a=compile(&p,&f,&good)?;
    for key in ["idempotency_key","plan_id"]{let mut v=good.clone();v[key]=json!("other-catalog-mask-binding");let b=compile(&p,&f,&v)?;
        assert_eq!(a.receipt().output_package_sha256,b.receipt().output_package_sha256);assert_ne!(a.receipt().compiled_plan_sha256,b.receipt().compiled_plan_sha256);}Ok(())
}
#[test]
fn compiled_delivery_requires_current_catalog_and_never_rematches()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let c=compile(&p,&f,&req(&s,&bytes,&f,false)?)?;
    let receipt=c.receipt().clone();let before=f.reads.get();c.verify(&p,&f,5)?;assert_eq!(f.reads.get(),before+2);assert_eq!(c.receipt(),&receipt);
    f.fail.set(true);let called=Cell::new(false);assert!(c.with_verified_bytes(&p,&f,5,|_|called.set(true)).is_err());assert!(!called.get());Ok(())
}
#[test]
fn compile_rechecks_catalog_after_common_compiler_returns()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let v=req(&s,&bytes,&f,false)?;
    compile(&p,&f,&v)?;let count=f.reads.get();assert!(count>=6);let f=feed("MARK");f.replace_at.set(count);assert!(compile(&p,&f,&v).is_err());assert_eq!(f.reads.get(),count);Ok(())
}
#[test]
fn acl_revocation_blocks_compiled_bytes_and_preview_metadata_then_regrant_rechecks()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let c=compile(&p,&f,&req(&s,&bytes,&f,false)?)?;let preview=product(&p,&f,&req(&s,&bytes,&f,true)?)?;
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;let called=Cell::new(false);assert!(c.with_verified_bytes(&p,&f,6,|_|called.set(true)).is_err());
    assert!(preview.with_verified_json(&p,&f,6,|_|called.set(true)).is_err());assert!(!called.get());s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;
    c.verify(&p,&f,8)?;preview.verify(&p,&f,8)?;Ok(())
}
#[test]
fn document_write_is_required_before_catalog_reads_for_product_and_compiled_delivery()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let v=req(&s,&bytes,&f,false)?;let c=compile(&p,&f,&v)?;
    let read=s.provider()?;let count=f.reads.get();assert!(product(&read,&f,&v).is_err());let called=Cell::new(false);
    assert!(c.with_verified_bytes(&read,&f,5,|_|called.set(true)).is_err());assert!(!called.get());assert_eq!(f.reads.get(),count);Ok(())
}
#[test]
fn all_five_foreign_provider_dimensions_block_retained_compiled_delivery()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let c=compile(&p,&f,&req(&s,&bytes,&f,false)?)?;let called=Cell::new(false);
    for mode in 0..5{let tenant=if mode==4{TenantId::new(Uuid::from_u128(993))?}else{s.reader.tenant_id()};
        let subject=if mode==3{SubjectDigest::from_authenticated_subject("foreign-catalog-product")?}else{s.reader.subject()};let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);
        let context=rev::RevisionRequestContext::new(tenant,subject);let project=if mode==2{rev::ProjectId::parse("prj_70000000000000000000000000000003")?}else{s.project};
        let branch=if mode==1{rev::BranchId::parse("brn_70000000000000000000000000000003")?}else{s.branch};
        let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&context,project,branch,DocumentId::parse(if mode==0{"foreign-catalog-product"}else{"actual-form-document"})?)?;
        assert!(c.with_verified_bytes(&other,&f,5,|_|called.set(true)).is_err());}assert!(!called.get());Ok(())
}
#[test]
fn quarantine_and_aead_tamper_block_compiled_and_preview_consumers()->R{
    for tamper in [false,true]{let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let c=compile(&p,&f,&req(&s,&bytes,&f,false)?)?;let preview=product(&p,&f,&req(&s,&bytes,&f,true)?)?;
        if tamper{s.blobs.tamper.store(true,Ordering::SeqCst);}else{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("CATALOG_PRODUCT_TEST")?,5)?;}
        let called=Cell::new(false);assert!(c.with_verified_bytes(&p,&f,6,|_|called.set(true)).is_err());assert!(preview.with_verified_json(&p,&f,6,|_|called.set(true)).is_err());assert!(!called.get());}Ok(())
}
fn head_race(stage:usize)->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let v=req(&s,&bytes,&f,false)?;
    let out=product(&p,&f,&v)?;let c=compile(&p,&f,&v)?;let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,
        ContentDigest::of(b"catalog-product-head-race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation fixture"),ContentDigest::of(b"transaction fixture"))?;
    let repo=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
    let bound=StoredFormProvider::bind(&s.artifacts,&repo,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;let raw=wire(&v)?;
    match stage{0=>{CP::prepare_json(&bound,&f,&raw,Default::default(),Default::default(),5)?;},1=>{out.with_verified_bytes(&bound,&f,5,|_|())?;},
        2=>{out.with_verified_json(&bound,&f,5,|_|())?;},3=>{Dispatch::prepare_compiled_catalog_mask_json(&bound,&f,&raw,Limits::standard()?,5)?;},_=>{c.with_verified_bytes(&bound,&f,5,|_|())?;}}
    let count=repo.repository().calls.load(Ordering::SeqCst);assert!(count>=4);repo.repository().calls.store(0,Ordering::SeqCst);repo.repository().trigger.store(count,Ordering::SeqCst);let called=Cell::new(false);
    let failed=match stage{0=>CP::prepare_json(&bound,&f,&raw,Default::default(),Default::default(),6).is_err(),1=>out.with_verified_bytes(&bound,&f,6,|_|called.set(true)).is_err(),
        2=>out.with_verified_json(&bound,&f,6,|_|called.set(true)).is_err(),3=>Dispatch::prepare_compiled_catalog_mask_json(&bound,&f,&raw,Limits::standard()?,6).is_err(),_=>c.with_verified_bytes(&bound,&f,6,|_|called.set(true)).is_err()};
    assert!(failed&&!called.get());assert_eq!(repo.repository().calls.load(Ordering::SeqCst),count);Ok(())
}
#[test]fn product_preparation_final_head_race_rejects()->R{head_race(0)}
#[test]fn product_byte_consumer_final_head_race_rejects()->R{head_race(1)}
#[test]fn product_metadata_consumer_final_head_race_rejects()->R{head_race(2)}
#[test]fn common_compiler_final_head_race_rejects()->R{head_race(3)}
#[test]fn compiled_delivery_final_head_race_rejects()->R{head_race(4)}
#[test]
fn receipts_plans_and_debug_omit_patterns_original_values_and_value_hashes()->R{
    let bytes=raw("PRIVATE-CATALOG-VALUE")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("PRIVATE-CATALOG-VALUE");let v=req(&s,&bytes,&f,false)?;let out=product(&p,&f,&v)?;let c=compile(&p,&f,&v)?;
    for text in [out.with_verified_json(&p,&f,5,|b|String::from_utf8_lossy(b).into_owned())?,serde_json::to_string(c.compiled())?,format!("{out:?}{c:?}{:?}",out.receipt())]{
        for private in ["PRIVATE-CATALOG-VALUE","NEVERF","pattern0=","matched_value_sha256","source_span_sha256"]{assert!(!text.contains(private));}}Ok(())
}
#[test]
fn source_head_and_ingest_count_stay_unchanged_and_routes_stay_unqualified()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let v=req(&s,&bytes,&f,false)?;let c=compile(&p,&f,&v)?;let out=product(&p,&f,&v)?;
    assert!(matches!(c.require_current_product_route(&p,&f,5),Err(CompileError::Product(PE::RouteUnqualified))));assert!(matches!(out.require_current_product_route(&p,&f,5),Err(PE::RouteUnqualified)));
    assert_eq!(s.artifacts.download(&s.reader,s.result,6)?,bytes);assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);
    assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
}
#[cfg(all(windows,feature="p09-installed-format-fixture"))]
#[test]
fn explicit_installed_catalog_mask_uses_all_telephone_patterns_and_shared_compiler()->R{
    use hwpx_agent_cli::form_stored_provider::actual_import::source_search::personal_info_catalog::InstalledPersonalInfoCatalogSource;
    let catalog=InstalledPersonalInfoCatalogSource;let config=catalog.read_current_catalog()?;assert_eq!(config.len(),17020);
    assert_eq!(ContentDigest::of(&config).hex(),"fe3721e68a749c3d1ec843207d475249fa75e68f1de569fe45468c05b1022434");
    let bytes=raw("KEEP 010-000-0000 END")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let mut v=req(&s,&bytes,&f,false)?;
    v["expected_catalog_sha256"]=json!(ContentDigest::of(&config).hex());v["operation"]["families"]=json!([F::Telephone]);
    let out=CP::prepare_json(&p,&catalog,&wire(&v)?,Default::default(),Default::default(),4)?;
    assert_eq!(out.receipt().stored.output.selected_patterns,8);assert_eq!(out.receipt().stored.output.catalog.total_patterns,64);
    assert!(out.with_verified_bytes(&p,&catalog,5,section)??.contains("KEEP ************ END"));
    let c=Dispatch::prepare_compiled_catalog_mask_json(&p,&catalog,&wire(&v)?,Limits::standard()?,4)?;assert_eq!(c.receipt().output_package_sha256,out.receipt().stored.output.output_package_sha256);
    assert!(!c.receipt().execution_authority&&!out.receipt().stored.output.native_catalog_mask_semantics_or_service_execution_qualified);Ok(())
}
