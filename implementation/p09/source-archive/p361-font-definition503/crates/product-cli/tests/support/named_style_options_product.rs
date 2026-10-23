//! Optional predicates reach current stored bytes and output-discarded preview through strict v2 JSON.
use super::*;
use hwpx_agent_cli::form_product_request::stored_literal_replacement::named_styles::options::{StoredNamedStyleOptionsProductRequest as Options,
    PreparedStoredNamedStyleOptionsProduct,NAMED_STYLE_OPTIONS_REQUEST_SCHEMA as V2};
use hwpx_agent_cli::form_stored_provider::actual_import::literal_search_output::named_styles::options::StoredNamedStyleOptionsOutputReceipt as Output;
use hwpx_package::document_import::search::reviews::selector::styles::SourceReviewStyleFilter as Filter;
fn v2(s:&StoredFixture,bytes:&[u8],preview:bool)->Result<Value,Box<dyn Error>>{let mut v=request(s,bytes,preview)?;v["schema_version"]=json!(V2);v["operation"]["style_filter"]=json!({"kind":"declared","filter":{"paragraph_property":0}});Ok(v)}
fn prepare_v2(p:&Provider<'_>,v:&Value)->Result<PreparedStoredNamedStyleOptionsProduct,E>{Options::prepare_json(p,&serde_json::to_vec(v).map_err(|_|E::Request)?,Default::default(),Default::default(),4)}
fn typed_filter(v:&Value)->Result<Filter,serde_json::Error>{serde_json::from_value(v["operation"]["style_filter"].clone())}
#[test]
fn borrowed_owned_and_product_share_same_original_filtered_receipt_and_output()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=v2(&s,&bytes,false)?;let filter=Some(typed_filter(&v)?);let source=p.import_actual_forms(s.head,4)?;
    let a=source.prepare_named_style_options_candidate(&p,query(),Scope::Document,policy(),filter,Default::default(),Default::default(),4)?;
    let b=p.import_actual_forms(s.head,4)?.into_named_style_options_candidate(&p,query(),Scope::Document,policy(),filter,Default::default(),Default::default(),4)?;let product=prepare_v2(&p,&v)?;
    assert_eq!(a.receipt(),b.receipt());assert_eq!(a.receipt(),&product.receipt().stored);assert_eq!(a.with_verified_bytes(&p,5,ContentDigest::of)?,product.with_verified_bytes(&p,5,ContentDigest::of)?);
    assert!(matches!(a.require_current_product_route(&p,5),Err(Stored::RouteUnqualified)));let preview=b.into_preview();assert!(preview.verify(&p,5)?.preview_only);assert!(!preview.receipt().candidate_output_retained);Ok(())
}
#[test]
fn absent_filter_keeps_v1_output_and_source_receipt_including_empty_paragraphs()->R{
    let bytes=package(&(para(1,0,"A")+"<hp:p id='2' paraPrIDRef='0' styleIDRef='1'><hp:run charPrIDRef='0'/></hp:p>"))?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    for preview in [false,true]{let mut v=v2(&s,&bytes,preview)?;v["operation"].as_object_mut().ok_or("op")?.remove("style_filter");let out=prepare_v2(&p,&v)?;let old=prepare!(&p,&request(&s,&bytes,preview)?)?;
        let Output::Unfiltered(r)=&out.receipt().stored.output else{return Err("unfiltered".into())};assert_eq!(r,&old.receipt().stored.output);out.verify(&p,5)?;
        if !preview{assert_eq!(out.with_verified_bytes(&p,5,ContentDigest::of)?,old.with_verified_bytes(&p,5,ContentDigest::of)?);}}Ok(())
}
#[test]
fn declared_filter_changes_only_matching_named_paragraph_and_keeps_all_other_parts()->R{
    let bytes=package(&(para(1,0,"A")+&para(2,1,"B")))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=v2(&s,&bytes,false)?;
    v["operation"]["style_filter"]=json!({"kind":"declared","filter":{"paragraph_style":0}});let out=prepare_v2(&p,&v)?;let after=out.with_verified_bytes(&p,5,<[u8]>::to_vec)?;
    assert_eq!(refs(&after)?,vec![(1,Some(0),Some(2)),(2,Some(0),Some(1))]);assert_eq!(archive::read_part(&bytes,"Contents/header.xml")?,archive::read_part(&after,"Contents/header.xml")?);
    let Output::Filtered(r)=&out.receipt().stored.output else{return Err("filtered".into())};assert_eq!(r.style_filter.filtered_paragraphs,1);assert_eq!(r.source.matched_paragraphs,1);assert_eq!(out.receipt().capability_id,"search.replace_styles");Ok(())
}
#[test]
fn explicit_definition_axes_and_conjunctive_conditions_reach_product()->R{
    let first=para(1,0,"A").replace("charPrIDRef='0'","charPrIDRef='1'").replace("paraPrIDRef='0'","paraPrIDRef='1'");let bytes=package(&(first+&para(2,1,"B")))?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    for preview in [false,true]{let mut v=v2(&s,&bytes,preview)?;v["operation"]["style_filter"]=json!({"kind":"definition","filter":{"character_source":"run_property","bold":true,"paragraph_source":"direct_property","alignment":"right"}});
        let out=prepare_v2(&p,&v)?;let Output::Filtered(r)=&out.receipt().stored.output else{return Err("filtered".into())};assert!(r.style_filter.definitions.is_some());assert_eq!(r.source.changes.len(),1);
        if !preview{assert_eq!(out.with_verified_bytes(&p,5,refs)??,vec![(1,Some(1),Some(2)),(2,Some(0),Some(1))]);}}Ok(())
}
#[test]
fn mixed_runs_and_nfc_contributors_never_become_partial_paragraph_style_changes()->R{
    for mixed in ["A</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>B","ᄀ</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>ᅡᆨ"]{
        let bytes=package(&(para(1,0,mixed)+&para(2,1,"각")))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=v2(&s,&bytes,false)?;
        v["operation"]["style_filter"]=json!({"kind":"declared","filter":{"run_character_property":0}});let out=prepare_v2(&p,&v)?;
        assert_eq!(out.with_verified_bytes(&p,5,refs)??,vec![(1,Some(0),Some(0)),(2,Some(0),Some(2))]);}Ok(())
}
#[test]
fn preview_predicts_same_candidate_but_drops_output_and_never_calls_file_consumer()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mutation=prepare_v2(&p,&v2(&s,&bytes,false)?)?;let preview=prepare_v2(&p,&v2(&s,&bytes,true)?)?;
    assert_eq!(mutation.receipt().stored.output,preview.receipt().stored.output);assert_ne!(mutation.receipt().canonical_request_sha256,preview.receipt().canonical_request_sha256);assert!(preview.receipt().preview_only&&!preview.receipt().stored.candidate_output_retained);
    let called=Cell::new(false);assert!(matches!(preview.with_verified_bytes(&p,5,|_|called.set(true)),Err(E::PreviewOnly)));assert!(!called.get());
    let parsed=preview.with_verified_json(&p,5,|b|serde_json::from_slice::<Value>(b))??;assert_eq!(parsed["preview_only"],true);assert_eq!(parsed["stored"]["candidate_output_retained"],false);Ok(())
}
#[test]
fn filtered_empty_paragraphs_are_not_vacuous_matches_while_unfiltered_remains_supported()->R{
    let empty="<hp:p id='1' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'/></hp:p><hp:p id='2' paraPrIDRef='0' styleIDRef='1'><hp:run charPrIDRef='0'><hp:t/></hp:run></hp:p>";
    let bytes=package(&(empty.to_owned()+&para(3,0,"A")))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    for preview in [false,true]{let out=prepare_v2(&p,&v2(&s,&bytes,preview)?)?;let Output::Filtered(r)=&out.receipt().stored.output else{return Err("filtered".into())};assert_eq!(r.style_filter.empty_paragraphs,2);assert_eq!(r.source.matched_paragraphs,1);}
    let bytes=package(empty)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);assert!(matches!(prepare_v2(&p,&v2(&s,&bytes,true)?),Err(E::Stored(Stored::Output(Core::NoMatches)))));Ok(())
}
#[test]
fn four_selector_kinds_and_partial_scope_guards_are_retained_in_v2()->R{
    let bytes=package(&(para(1,0,"ABC")+&para(2,1,"DEF")))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=v2(&s,&bytes,false)?;
    let inv=inventory(&p,&request(&s,&bytes,false)?)?;let first=&inv["inventory"]["blocks"][0];let node=inv["inventory"]["nodes"].as_array().ok_or("nodes")?.iter().find(|n|n["source_handle"]==first["paragraph_handle"]).ok_or("node")?;
    for mode in 0..4{let mut v=good.clone();let count=match mode{0=>2,1=>{v["selector"]["scope"]=json!("section");v["selector"]["section_ids"]=inv["inventory"]["section_ids"].clone();2},
        2=>{v["selector"]["scope"]=json!("node_set");v["selector"]["range"]=json!({"node_ids":[node["node_id"]]});1},_=>{v["selector"]["scope"]=json!("selection");v["selector"]["range"]=selection(&inv,0,3)?;1}};
        assert_eq!(prepare_v2(&p,&v)?.receipt().stored.output.source().changes.len(),count);}
    let mut v=good;v["selector"]["scope"]=json!("selection");v["selector"]["range"]=selection(&inv,1,2)?;assert!(matches!(prepare_v2(&p,&v),Err(E::Stored(Stored::Output(Core::Paragraph(Paragraph::IncompleteParagraphScope))))));Ok(())
}
#[test]
fn hidden_and_memo_policies_apply_before_filter_in_both_result_modes()->R{
    let body=review::body().replace("<hp:p id='1'>","<hp:p id='1' paraPrIDRef='0' styleIDRef='2'>").replace("<hp:p id='11'>","<hp:p id='11' paraPrIDRef='0' styleIDRef='0'>").replace("<hp:p id='12'>","<hp:p id='12' paraPrIDRef='0' styleIDRef='1'>");
    let bytes=package(&body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    for preview in [false,true]{for(h,m,total)in [(false,false,0),(true,false,1),(false,true,1),(true,true,2)]{let mut v=v2(&s,&bytes,preview)?;
        v["operation"]["review_policy"]=json!({"include_hidden_explanations":h,"include_memo_bodies":m});let result=prepare_v2(&p,&v);if total==0{assert!(matches!(result,Err(E::Stored(Stored::Output(Core::NoMatches)))));continue;}
        let out=result?;assert_eq!(out.receipt().stored.output.source().changes.len(),total);if !preview{let after=out.with_verified_bytes(&p,5,<[u8]>::to_vec)?;assert_eq!(refs(&after)?[0].2,Some(2));assert!(String::from_utf8(archive::read_part(&after,"Contents/section0.xml")?)?.contains("CACHE FROZEN"));}}}Ok(())
}
#[test]
fn required_mode_and_closed_filter_shapes_are_rejected_before_source_reads()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=v2(&s,&bytes,true)?;let n=s.metadata.audit_events()?.len();
    for key in ["schema_version","idempotency_key","project_id","document_id","base_revision","expected_head_generation","expected_source_package_sha256","plan_id","selector","operation"]{let mut v=good.clone();v.as_object_mut().ok_or("root")?.remove(key);assert!(matches!(prepare_v2(&p,&v),Err(E::Request)));}
    for value in [Value::Null,json!([]),json!({}),json!({"kind":{"declared":null},"filter":{"paragraph_property":0}}),json!({"kind":"declared","filter":{}}),json!({"kind":"declared","filter":{"unknown":0}}),json!({"kind":"definition","filter":{"bold":true}})]{
        let mut v=good.clone();v["operation"]["style_filter"]=value;assert!(matches!(prepare_v2(&p,&v),Err(E::Request)));}
    for value in [Value::Null,json!("true"),json!(1)]{let mut v=good.clone();v["operation"]["preview_only"]=value;assert!(matches!(prepare_v2(&p,&v),Err(E::Request)));}
    let mut v=good;v["operation"].as_object_mut().ok_or("op")?.remove("preview_only");assert!(matches!(prepare_v2(&p,&v),Err(E::Request)));assert_eq!(s.metadata.audit_events()?.len(),n);Ok(())
}
#[test]
fn unknown_duplicate_escaped_duplicate_trailing_and_exact_request_byte_limit_are_strict()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=v2(&s,&bytes,true)?;let n=s.metadata.audit_events()?.len();
    for key in ["raw_xml","approved","full_catalog","max_replacements"]{let mut v=good.clone();v["operation"][key]=json!({});assert!(matches!(prepare_v2(&p,&v),Err(E::Request)));}
    let raw=String::from_utf8(wire(&good)?)?;for invalid in [raw.replacen("\"preview_only\":true","\"preview_only\":true,\"preview_only\":false",1),raw.replacen("\"kind\":\"declared\"","\"kind\":\"declared\",\"k\\u0069nd\":\"declared\"",1),format!("{raw}{{}}")]{
        assert!(matches!(Options::prepare_json(&p,invalid.as_bytes(),Default::default(),Default::default(),4),Err(E::Request)));}
    assert_eq!(s.metadata.audit_events()?.len(),n);let mut exact=wire(&good)?;exact.resize(16*1024,b' ');Options::prepare_json(&p,&exact,Default::default(),Default::default(),4)?;let n=s.metadata.audit_events()?.len();exact.push(b' ');
    assert!(matches!(Options::prepare_json(&p,&exact,Default::default(),Default::default(),4),Err(E::Limit)));assert_eq!(s.metadata.audit_events()?.len(),n);Ok(())
}
#[test]
fn v1_stays_closed_and_foreign_v2_schema_rejects_before_source_reads()->R{
    use hwpx_agent_cli::form_product_request::stored_operations::{StoredProductRequest,search_mutations::SearchMutationLimits};
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=v2(&s,&bytes,true)?;let n=s.metadata.audit_events()?.len();
    assert!(matches!(prepare!(&p,&good),Err(E::Request)));let mut old=good.clone();old["schema_version"]=json!(SCHEMA);assert!(matches!(prepare!(&p,&old),Err(E::Request)));assert!(matches!(prepare_v2(&p,&old),Err(E::Request)));
    let mut foreign=good;foreign["schema_version"]=json!("hwpx-agent.product-named-paragraph-style-replacement-request/v999");
    assert!(StoredProductRequest::prepare_json(&p,&wire(&foreign)?,None,4).is_err());assert!(StoredProductRequest::prepare_compiled_search_json(&p,&wire(&foreign)?,SearchMutationLimits::standard()?,4).is_err());assert_eq!(s.metadata.audit_events()?.len(),n);Ok(())
}
#[test]
fn request_server_query_writer_and_result_limits_apply_to_both_modes()->R{
    let bytes=package(&(para(1,0,"A")+&para(2,1,"B")))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    for preview in [false,true]{let good=v2(&s,&bytes,preview)?;let mut v=good.clone();v["operation"]["max_changed_paragraphs"]=json!(1);assert!(prepare_v2(&p,&v).is_err());
        for limits in [SourceSearchLimits::new(Config{matches:1,..Default::default()})?,SourceSearchLimits::new(Config{query_bytes:1,..Default::default()})?,SourceSearchLimits::new(Config{result_bytes:1,..Default::default()})?]{assert!(Options::prepare_json(&p,&wire(&good)?,limits,Default::default(),4).is_err());}
        assert!(Options::prepare_json(&p,&wire(&good)?,Default::default(),WriterLimits::new(WriterLimitConfig{max_output_bytes:1})?,4).is_err());}Ok(())
}
#[test]
fn exact_outer_server_metadata_limit_and_one_byte_less_are_enforced()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    for preview in [false,true]{let v=v2(&s,&bytes,preview)?;let base=prepare_v2(&p,&v)?;let length=base.with_verified_json(&p,5,<[u8]>::len)?;
        let exact=SourceSearchLimits::new(Config{result_bytes:length,..Default::default()})?;assert_eq!(Options::prepare_json(&p,&wire(&v)?,exact,Default::default(),4)?.with_verified_json(&p,5,<[u8]>::len)?,length);
        let smaller=SourceSearchLimits::new(Config{result_bytes:length-1,..Default::default()})?;assert!(matches!(Options::prepare_json(&p,&wire(&v)?,smaller,Default::default(),4),Err(E::Limit)));}Ok(())
}
#[test]
fn filtered_metadata_above_sixty_four_kib_keeps_all_three_hundred_eighty_four_changes()->R{
    let mut body=String::new();for id in 1..=384{body.push_str(&para(id,id%2,"A"));}let bytes=package(&body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    for preview in [false,true]{let mut v=v2(&s,&bytes,preview)?;v["operation"]["max_changed_paragraphs"]=json!(384);let out=prepare_v2(&p,&v)?;let metadata=out.with_verified_json(&p,5,<[u8]>::to_vec)?;
        assert!(metadata.len()>64*1024&&metadata.len()<=4*1024*1024);assert_eq!(out.receipt().stored.output.source().changes.len(),384);if !preview{assert_eq!(out.with_verified_bytes(&p,5,refs)??.iter().filter(|p|p.2==Some(2)).count(),384);}}Ok(())
}
#[test]
fn source_sha_revision_and_head_binding_are_not_preview_bypasses()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    for preview in [false,true]{let good=v2(&s,&bytes,preview)?;for key in ["expected_source_package_sha256","base_revision","expected_head_generation"]{let mut v=good.clone();v[key]=match key{"expected_source_package_sha256"=>json!("0".repeat(64)),"base_revision"=>json!("rev_70000000000000000000000000000002"),_=>json!(s.head.generation()+1)};assert!(prepare_v2(&p,&v).is_err());}}Ok(())
}
#[test]
fn current_write_scope_and_five_foreign_provider_scopes_block_retained_results()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let reader=s.provider()?;
    for preview in [false,true]{let v=v2(&s,&bytes,preview)?;assert!(prepare_v2(&reader,&v).is_err());let out=prepare_v2(&p,&v)?;let called=Cell::new(false);assert!(out.with_verified_json(&reader,5,|_|called.set(true)).is_err());
        for mode in 0..5{let tenant=if mode==4{TenantId::new(Uuid::from_u128(998))?}else{s.reader.tenant_id()};let subject=if mode==3{SubjectDigest::from_authenticated_subject("foreign-named-options")?}else{s.reader.subject()};
            let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);let context=rev::RevisionRequestContext::new(tenant,subject);let project=if mode==2{rev::ProjectId::parse("prj_70000000000000000000000000000002")?}else{s.project};let branch=if mode==1{rev::BranchId::parse("brn_70000000000000000000000000000002")?}else{s.branch};
            let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&context,project,branch,DocumentId::parse(if mode==0{"foreign-document"}else{"actual-form-document"})?)?;
            assert!(out.verify(&other,5).is_err());assert!(out.with_verified_json(&other,5,|_|called.set(true)).is_err());}assert!(!called.get());}Ok(())
}
#[test]
fn acl_revoke_regrant_is_fresh_for_new_and_retained_mutation_and_preview()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let a=prepare_v2(&p,&v2(&s,&bytes,false)?)?;let b=prepare_v2(&p,&v2(&s,&bytes,true)?)?;
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;let called=Cell::new(false);for out in [&a,&b]{assert!(out.verify(&p,6).is_err());assert!(out.with_verified_json(&p,6,|_|called.set(true)).is_err());}
    assert!(prepare_v2(&p,&v2(&s,&bytes,true)?).is_err());assert!(!called.get());s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;a.verify(&p,8)?;b.verify(&p,8)?;Ok(())
}
#[test]
fn quarantine_and_ciphertext_tamper_block_new_and_retained_metadata_and_bytes()->R{
    for tamper in [false,true]{let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let a=prepare_v2(&p,&v2(&s,&bytes,false)?)?;let b=prepare_v2(&p,&v2(&s,&bytes,true)?)?;
        if tamper{s.blobs.tamper.store(true,Ordering::SeqCst);}else{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("NAMED_OPTIONS_TEST")?,5)?;}let called=Cell::new(false);
        for out in [&a,&b]{assert!(out.verify(&p,6).is_err());assert!(out.with_verified_json(&p,6,|_|called.set(true)).is_err());}assert!(a.with_verified_bytes(&p,6,|_|called.set(true)).is_err());assert!(!called.get());assert!(prepare_v2(&p,&v2(&s,&bytes,true)?).is_err());}Ok(())
}
#[test]
fn field_cache_and_zero_valued_tracking_guards_are_not_bypassed_by_filter_or_preview()->R{
    for body in [para(1,0,"A</hp:t><hp:ctrl><hp:fieldBegin id='17' type='DATE'/></hp:ctrl><hp:t>CACHE</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='17'/></hp:ctrl><hp:t>TAIL"),
        para(1,0,"A").replace("id='1'","id='1' paraTcId='0'"),para(1,0,"A").replace("charPrIDRef='0'","charPrIDRef='0' charTcId='0'")]{let bytes=package(&body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
        for preview in [false,true]{assert!(prepare_v2(&p,&v2(&s,&bytes,preview)?).is_err());}}Ok(())
}
#[test]
fn entire_filter_request_hashes_are_bound_and_private_names_body_and_keys_are_redacted()->R{
    let bytes=raw("PRIVATE-NAMED-OPTIONS-BODY")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=v2(&s,&bytes,true)?;let first=prepare_v2(&p,&good)?;let mut second=good.clone();second["operation"]["style_filter"]=json!({"kind":"declared","filter":{"run_character_property":0}});let second=prepare_v2(&p,&second)?;
    assert_eq!(first.receipt().stored.output.source(),second.receipt().stored.output.source());assert_ne!(first.receipt().canonical_request_sha256,second.receipt().canonical_request_sha256);assert_ne!(first.receipt().stored.output,second.receipt().stored.output);
    for key in ["plan_id","idempotency_key"]{let mut v=good.clone();v[key]=json!("PRIVATE-DIFFERENT-ID");assert_ne!(first.receipt().canonical_request_sha256,prepare_v2(&p,&v)?.receipt().canonical_request_sha256);}
    for text in [format!("{first:?}{:?}",first.receipt()),first.with_verified_json(&p,5,|b|String::from_utf8_lossy(b).into_owned())?]{assert!(!text.contains("PRIVATE-")&&!text.contains("SRC")&&!text.contains("DST"));}Ok(())
}
#[test]
fn no_idempotency_claim_ingest_commit_or_route_authority_is_issued_in_either_mode()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    for preview in [false,true]{let out=prepare_v2(&p,&v2(&s,&bytes,preview)?)?;out.verify(&p,5)?;assert!(matches!(out.require_current_product_route(&p,5),Err(E::RouteUnqualified)));assert!(!out.receipt().idempotency_key_claimed&&!out.receipt().full_style_native_cas_execution_publication_authority);}
    assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(s.artifacts.download(&s.reader,s.result,5)?,bytes);assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
}
fn final_head_race(preview:bool,stage:usize)->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=v2(&s,&bytes,preview)?;let out=prepare_v2(&p,&v)?;
    let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,
        ContentDigest::of(b"named-options-race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation fixture"),ContentDigest::of(b"transaction fixture"))?;
    let repo=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
    let bound=StoredFormProvider::bind(&s.artifacts,&repo,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
    match stage{0=>{Options::prepare_json(&bound,&wire(&v)?,Default::default(),Default::default(),5)?;},1=>{out.verify(&bound,5)?;},_=>{out.with_verified_json(&bound,5,|_|())?;}}
    let count=repo.repository().calls.load(Ordering::SeqCst);assert!(count>=4);repo.repository().calls.store(0,Ordering::SeqCst);repo.repository().trigger.store(count,Ordering::SeqCst);let called=Cell::new(false);
    match stage{0=>assert!(Options::prepare_json(&bound,&wire(&v)?,Default::default(),Default::default(),6).is_err()),1=>assert!(out.verify(&bound,6).is_err()),_=>assert!(out.with_verified_json(&bound,6,|_|called.set(true)).is_err())}
    assert!(!called.get());assert_eq!(repo.repository().calls.load(Ordering::SeqCst),count);Ok(())
}
#[test]fn mutation_preparation_final_head_race_rejects()->R{final_head_race(false,0)}
#[test]fn mutation_verification_final_head_race_rejects()->R{final_head_race(false,1)}
#[test]fn mutation_metadata_final_head_race_blocks_consumer()->R{final_head_race(false,2)}
#[test]fn preview_preparation_final_head_race_rejects()->R{final_head_race(true,0)}
#[test]fn preview_verification_final_head_race_rejects()->R{final_head_race(true,1)}
#[test]fn preview_metadata_final_head_race_blocks_consumer()->R{final_head_race(true,2)}
#[path="named_style_options_compiled.rs"]mod compiled;
