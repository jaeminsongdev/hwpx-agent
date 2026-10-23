//! Actual stored sort/strict JSON/current-access tests; not dispatcher, commit, Native or Gate acceptance.
use super::*;
use hwpx_agent_cli::form_product_request::stored_literal_replacement::sort::{StoredParagraphSortProductRequest as SortProduct,
    ParagraphSortProductError as SE,PARAGRAPH_SORT_PRODUCT_REQUEST_SCHEMA as SORT_SCHEMA};
use hwpx_agent_cli::form_stored_provider::actual_import::literal_search_output::sort::StoredParagraphSortError as SS;
use hwpx_package::document_import::search::replacement::atoms::sort::{SourceParagraphSortSpec as Spec,SourceParagraphSortDirection as Direction,
    SourceParagraphSortComparison as Comparison,SourceParagraphSortError as SortError};
macro_rules! sort_prepare{($p:expr,$v:expr)=>{SortProduct::prepare_json($p,&wire($v)?,Default::default(),Default::default(),4)}}
fn specimen()->Result<Vec<u8>,Box<dyn Error>>{definition::package(&(para(1,"Z-PRIVATE")+&para(2,"A")))}
fn sort_request(s:&StoredFixture,b:&[u8])->Result<Value,Box<dyn Error>>{let mut v=request(s,b)?;v["schema_version"]=json!(SORT_SCHEMA);
    v["operation"]=json!({"kind":"sort_sibling_paragraphs","sort_spec":{"direction":"ascending","comparison":"nfc_unicode_scalar_lexicographic","max_comparison_bytes":1048576},"review_policy":policy(false,false)});Ok(v)}
fn spec()->Spec{Spec{direction:Direction::Ascending,comparison:Comparison::NfcUnicodeScalarLexicographic,max_comparison_bytes:1048576}}
fn full_range(inv:&Value)->Result<Value,Box<dyn Error>>{let blocks=inv["inventory"]["blocks"].as_array().ok_or("blocks")?;let last=blocks.last().ok_or("last")?;
    let mut range=window(inv,"body_and_notes",0,1)?;range["end"]=json!({"paragraph_handle":last["paragraph_handle"],"block_index":last["block_index"],"normalized_scalar":last["normalized_scalars"]});Ok(range)}

#[test]
fn sort_product_changes_actual_source_and_owns_request_without_source_mutation()->TestResult{
    let bytes=specimen()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=sort_request(&s,&bytes)?;
    let out=sort_prepare!(&p,&v)?;drop(v);out.verify(&p,5)?;
    assert_eq!(out.with_verified_bytes(&p,5,section)??,section(&bytes)?.replace(&(para(1,"Z-PRIVATE")+&para(2,"A")),&(para(2,"A")+&para(1,"Z-PRIVATE"))));
    assert_eq!(out.receipt().stored.output.source_order,vec![1,0]);assert_eq!(out.receipt().capability_id,"search.sort_text");assert!(section(&bytes)?.contains("Z-PRIVATE"));Ok(())
}
#[test]
fn sort_product_borrowed_owned_and_json_share_exact_receipt_and_output()->TestResult{
    let bytes=specimen()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=sort_request(&s,&bytes)?;let out=sort_prepare!(&p,&v)?;
    let source=p.import_actual_forms(s.head,4)?;let borrowed=source.prepare_paragraph_sort_candidate(&p,Scope::Document,Policy::default(),spec(),Default::default(),Default::default(),4)?;
    assert_eq!(borrowed.verify(&p,5)?,out.receipt().stored);drop(borrowed);
    let owned=source.into_paragraph_sort_candidate(&p,Scope::Document,Policy::default(),spec(),Default::default(),Default::default(),4)?;
    assert_eq!(owned.verify(&p,5)?,out.receipt().stored);assert_eq!(owned.with_verified_bytes(&p,5,<[u8]>::to_vec)?,out.with_verified_bytes(&p,5,<[u8]>::to_vec)?);
    assert!(matches!(owned.require_current_product_route(&p,5),Err(SS::RouteUnqualified)));Ok(())
}
#[test]
fn sort_product_nfc_equal_keys_are_stable_in_both_directions()->TestResult{
    let bytes=definition::package(&(para(1,"가")+&para(2,"Z")+&para(3,"가")))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
    for(direction,order)in[("ascending",vec![1,0,2]),("descending",vec![0,2,1])]{let mut v=sort_request(&s,&bytes)?;v["operation"]["sort_spec"]["direction"]=json!(direction);
        let out=sort_prepare!(&p,&v)?;assert_eq!(out.receipt().stored.output.source_order,order);assert_eq!(out.receipt().stored.output.entries[0].normalized_key_sha256,out.receipt().stored.output.entries[2].normalized_key_sha256);
        assert!(out.with_verified_bytes(&p,5,section)??.contains("가"));}Ok(())
}
#[test]
fn sort_product_discovers_all_four_scopes_without_caller_source_import()->TestResult{
    let bytes=specimen()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=sort_request(&s,&bytes)?;let inv=inventory(&p,&v)?;
    for scope in["document","section","node_set","selection"]{let mut v=v.clone();v["selector"]["scope"]=json!(scope);
        match scope{"section"=>v["selector"]["section_ids"]=inv["inventory"]["section_ids"].clone(),"node_set"=>{let ids:Vec<_>=inv["inventory"]["nodes"].as_array().ok_or("nodes")?.iter().map(|n|n["node_id"].clone()).collect();v["selector"]["range"]=json!({"node_ids":ids});},"selection"=>v["selector"]["range"]=full_range(&inv)?,_=>{}}
        assert_eq!(sort_prepare!(&p,&v)?.receipt().stored.output.source_order,vec![1,0]);}Ok(())
}
#[test]
fn sort_product_clipped_or_stale_selection_is_not_widened()->TestResult{
    let bytes=specimen()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=sort_request(&s,&bytes)?;let inv=inventory(&p,&v)?;
    v["selector"]["scope"]=json!("selection");v["selector"]["range"]=full_range(&inv)?;v["selector"]["range"]["start"]["normalized_scalar"]=json!(1);
    assert!(matches!(sort_prepare!(&p,&v),Err(SE::Stored(SS::Output(SortError::IncompleteParagraphScope)))));
    v["selector"]["range"]["index_sha256"]=json!("0".repeat(64));assert!(sort_prepare!(&p,&v).is_err());Ok(())
}
#[test]
fn sort_product_unknown_fields_arrays_trailing_and_oversize_fail_before_reads()->TestResult{
    let bytes=specimen()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=sort_request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();
    for place in["root","operation","selector","spec","policy"]{let mut v=good.clone();match place{"root"=>v["approved"]=json!(true),"operation"=>v["operation"]["query"]=json!("Z"),"selector"=>v["selector"]["approved"]=json!(true),"spec"=>v["operation"]["sort_spec"]["locale"]=json!("ko-KR"),_=>v["operation"]["review_policy"]["approved"]=json!(true)};
        assert!(matches!(sort_prepare!(&p,&v),Err(SE::Request)));}
    for raw in[wire(&json!([good.clone()]))?,[wire(&good)?,b"{}".to_vec()].concat(),b"null".to_vec(),vec![b' ';16385]]{
        assert!(matches!(SortProduct::prepare_json(&p,&raw,Default::default(),Default::default(),4),Err(SE::Request)|Err(SE::Limit)));}
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn sort_product_nested_and_escaped_duplicate_keys_fail_before_reads()->TestResult{
    let bytes=specimen()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=sort_request(&s,&bytes)?;let text=serde_json::to_string(&v)?;let before=s.metadata.audit_events()?.len();
    for(from,to)in[("\"direction\":\"ascending\"","\"direction\":\"ascending\",\"direct\\u0069on\":\"descending\""),("\"scope\":\"document\"","\"scope\":\"document\",\"scope\":\"section\""),("\"include_memo_bodies\":false","\"include_memo_bodies\":false,\"include_memo_bodies\":true")]{let bad=text.replace(from,to);assert_ne!(bad,text);
        assert!(matches!(SortProduct::prepare_json(&p,bad.as_bytes(),Default::default(),Default::default(),4),Err(SE::Request)));}
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn sort_product_unsupported_specs_selector_shapes_and_missing_policy_fail_before_reads()->TestResult{
    let bytes=specimen()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=sort_request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();
    for key in["direction","comparison","review_policy"]{let mut v=good.clone();if key=="review_policy"{v["operation"].as_object_mut().ok_or("operation")?.remove(key);}else{v["operation"]["sort_spec"][key]=json!("unsupported");}assert!(matches!(sort_prepare!(&p,&v),Err(SE::Request)));}
    for limit in[0,33554433]{let mut v=good.clone();v["operation"]["sort_spec"]["max_comparison_bytes"]=json!(limit);assert!(matches!(sort_prepare!(&p,&v),Err(SE::Request)));}
    for scope in[json!({"revision_id":good["base_revision"],"scope":"document","section_ids":[]}),json!({"revision_id":good["base_revision"],"scope":"node_set","range":{"node_ids":[]}})]{let mut v=good.clone();v["selector"]=scope;assert!(matches!(sort_prepare!(&p,&v),Err(SE::Request)));}
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn sort_product_exact_16k_accepts_whitespace_without_changing_canonical_binding()->TestResult{
    let bytes=specimen()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=sort_request(&s,&bytes)?;let compact=wire(&v)?;let mut padded=compact.clone();padded.resize(16384,b' ');
    let a=SortProduct::prepare_json(&p,&compact,Default::default(),Default::default(),4)?;let b=SortProduct::prepare_json(&p,&padded,Default::default(),Default::default(),4)?;
    assert_ne!(a.receipt().raw_request_sha256,b.receipt().raw_request_sha256);assert_eq!(a.receipt().canonical_request_sha256,b.receipt().canonical_request_sha256);assert_eq!(a.receipt().scoped_request_sha256,b.receipt().scoped_request_sha256);Ok(())
}
#[test]
fn sort_product_key_plan_spec_and_policy_change_canonical_and_scoped_bindings()->TestResult{
    let bytes=definition::package(&(para(1,"B")+&para(2,"A")+&para(3,"C")))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=sort_request(&s,&bytes)?;let a=sort_prepare!(&p,&good)?;
    for mode in 0..4{let mut v=good.clone();match mode{0=>v["idempotency_key"]=json!("DIFFERENT-KEY"),1=>v["plan_id"]=json!("different-plan"),2=>v["operation"]["sort_spec"]["direction"]=json!("descending"),_=>v["operation"]["review_policy"]=policy(true,true)};
        let b=sort_prepare!(&p,&v)?;assert_ne!(a.receipt().canonical_request_sha256,b.receipt().canonical_request_sha256);assert_ne!(a.receipt().scoped_request_sha256,b.receipt().scoped_request_sha256);}Ok(())
}
#[test]
fn sort_product_current_write_and_all_five_external_scope_axes_guard_retained_output()->TestResult{
    let bytes=specimen()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=sort_request(&s,&bytes)?;let reader=s.provider()?;
    assert!(sort_prepare!(&reader,&v).is_err());let source=reader.import_actual_forms(s.head,4)?;assert!(matches!(source.prepare_paragraph_sort_candidate(&reader,Scope::Document,Policy::default(),spec(),Default::default(),Default::default(),4),Err(SS::Permission)));
    let out=sort_prepare!(&p,&v)?;let called=Cell::new(false);assert!(out.with_verified_bytes(&reader,5,|_|called.set(true)).is_err());
    for variant in 0..5{let tenant=if variant==4{TenantId::new(Uuid::from_u128(997))?}else{s.reader.tenant_id()};let subject=if variant==3{SubjectDigest::from_authenticated_subject("foreign-sort")?}else{s.reader.subject()};let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);let context=rev::RevisionRequestContext::new(tenant,subject);let project=if variant==2{rev::ProjectId::parse("prj_70000000000000000000000000000002")?}else{s.project};let branch=if variant==1{rev::BranchId::parse("brn_70000000000000000000000000000002")?}else{s.branch};
        let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&context,project,branch,DocumentId::parse(if variant==0{"foreign-document"}else{"actual-form-document"})?)?;
        assert!(out.verify(&other,5).is_err());assert!(out.with_verified_bytes(&other,5,|_|called.set(true)).is_err());}assert!(!called.get());Ok(())
}
#[test]
fn sort_product_acl_regrant_quarantine_and_aead_guard_every_retained_delivery()->TestResult{
    for mode in 0..3{let bytes=specimen()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=sort_request(&s,&bytes)?;let out=sort_prepare!(&p,&v)?;
        match mode{0=>{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;},1=>{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("SORT_TEST")?,5)?;},_=>s.blobs.tamper.store(true,Ordering::SeqCst)}
        let called=Cell::new(false);assert!(out.verify(&p,6).is_err());assert!(out.with_verified_bytes(&p,6,|_|called.set(true)).is_err());assert!(sort_prepare!(&p,&v).is_err());assert!(!called.get());
        if mode==0{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;out.verify(&p,8)?;}}Ok(())
}
#[test]
fn sort_product_prepare_verify_and_delivery_last_head_races_block_consumer()->TestResult{
    for stage in 0..3{let bytes=specimen()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=sort_request(&s,&bytes)?;let wire=wire(&v)?;let out=sort_prepare!(&p,&v)?;
        let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,
            ContentDigest::of(b"sort race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation"),ContentDigest::of(b"transaction"))?;
        let b=rev::RevisionService::new(BoundaryRepo {inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
        let bound=StoredFormProvider::bind(&s.artifacts,&b,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
        match stage{0=>{SortProduct::prepare_json(&bound,&wire,Default::default(),Default::default(),5)?;},1=>{out.verify(&bound,5)?;},_=>{out.with_verified_bytes(&bound,5,|_|())?;}}
        let calls=b.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);b.repository().calls.store(0,Ordering::SeqCst);b.repository().trigger.store(calls,Ordering::SeqCst);let called=Cell::new(false);
        match stage{0=>assert!(SortProduct::prepare_json(&bound,&wire,Default::default(),Default::default(),6).is_err()),1=>assert!(out.verify(&bound,6).is_err()),_=>assert!(out.with_verified_bytes(&bound,6,|_|called.set(true)).is_err())}
        assert!(!called.get());assert_eq!(b.repository().calls.load(Ordering::SeqCst),calls);
    }Ok(())
}
#[test]
fn sort_product_wrong_source_head_revision_project_and_document_fail_preparation()->TestResult{
    let bytes=specimen()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=sort_request(&s,&bytes)?;
    for(key,value)in[("expected_head_generation",json!(s.head.generation()+1)),("expected_source_package_sha256",json!("0".repeat(64))),("document_id",json!("foreign-document")),("project_id",json!("prj_70000000000000000000000000000002")),("base_revision",json!(rev::RevisionId::generate().public_id()))]{let mut v=good.clone();v[key]=value;assert!(sort_prepare!(&p,&v).is_err());}Ok(())
}
#[test]
fn sort_product_original_tracking_and_field_guards_are_not_removed_for_sorting()->TestResult{
    let bytes=definition::package(&(para(1,"Z").replace("charPrIDRef='0'","charPrIDRef='0' charTcId='1'")+&para(2,"A")))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=sort_request(&s,&bytes)?;
    assert!(matches!(sort_prepare!(&p,&v),Err(SE::Stored(SS::Output(SortError::Compile(Compile::Protection))))));
    let bytes=definition::package(&format!("{}{}",fixture::body(),para(2,"A")))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=sort_request(&s,&bytes)?;assert!(sort_prepare!(&p,&v).is_err());Ok(())
}
#[test]
fn sort_product_work_source_response_and_writer_limits_do_not_return_partial_candidates()->TestResult{
    let bytes=definition::package(&(para(1,"SAME-LONG-Z")+&para(2,"SAME-LONG-A")))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=sort_request(&s,&bytes)?;v["operation"]["sort_spec"]["max_comparison_bytes"]=json!(1);
    assert!(matches!(sort_prepare!(&p,&v),Err(SE::Stored(SS::Output(SortError::ComparisonLimit)))));v["operation"]["sort_spec"]["max_comparison_bytes"]=json!(1048576);
    for config in[Config{scalars:1,..Default::default()},Config{result_bytes:1,..Default::default()}]{assert!(SortProduct::prepare_json(&p,&wire(&v)?,SourceSearchLimits::new(config)?,Default::default(),4).is_err());}
    assert!(matches!(SortProduct::prepare_json(&p,&wire(&v)?,Default::default(),WriterLimits::new(WriterLimitConfig{max_output_bytes:1})?,4),Err(SE::Stored(SS::Output(SortError::Compile(Compile::Writer))))));Ok(())
}
#[test]
fn sort_product_already_sorted_and_single_paragraph_do_not_fabricate_results()->TestResult{
    for(body,no_change)in[(para(1,"A")+&para(2,"B"),true),(para(1,"A"),false)]{let bytes=definition::package(&body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=sort_request(&s,&bytes)?;
        if no_change{assert!(matches!(sort_prepare!(&p,&v),Err(SE::Stored(SS::Output(SortError::Compile(Compile::NoChange))))));}
        else{assert!(matches!(sort_prepare!(&p,&v),Err(SE::Stored(SS::Output(SortError::Compile(Compile::NoMatches))))));}}Ok(())
}
#[test]
fn sort_product_private_receipts_and_closed_route_preserve_ingest_and_head()->TestResult{
    let bytes=specimen()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=sort_request(&s,&bytes)?;let out=sort_prepare!(&p,&v)?;
    for text in[format!("{out:?}{:?}",out.receipt()),serde_json::to_string(out.receipt())?]{assert!(!text.contains("Z-PRIVATE"));assert!(!text.contains("PRIVATE-UNICODE-KEY"));}
    assert!(matches!(out.require_current_product_route(&p,5),Err(SE::RouteUnqualified)));assert!(!out.receipt().idempotency_key_claimed&&!out.receipt().full_sort_native_cas_execution_publication_authority);
    assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
}
#[test]
fn sort_product_hundred_twenty_eight_paragraphs_use_one_original_sort_candidate()->TestResult{
    let body=(0..128).rev().map(|i|para(i+1,&format!("KEY-{i:03}"))).collect::<String>();let bytes=definition::package(&body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=sort_request(&s,&bytes)?;
    let out=sort_prepare!(&p,&v)?;assert_eq!(out.receipt().stored.output.source_order,(0..128).rev().collect::<Vec<_>>());let xml=hwpx_package::PreservingXmlDocument::parse(section(&bytes)?.as_bytes())?;
    assert_eq!(out.receipt().stored.output.observed_protection_element_visits,xml.elements().len()*3);out.verify(&p,5)?;out.with_verified_bytes(&p,5,|_|())?;Ok(())
}
#[test]
fn sort_product_hidden_sibling_scope_obeys_explicit_policy_without_touching_outer_body()->TestResult{
    let a=para(11,"Z");let b=para(12,"A");let body=para(1,&format!("BODY</hp:t><hp:ctrl><hp:hiddenComment><hp:subList>{a}{b}</hp:subList></hp:hiddenComment></hp:ctrl><hp:t>TAIL"));
    let bytes=definition::package(&body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=sort_request(&s,&bytes)?;let inv=inventory(&p,&v)?;
    let blocks=inv["inventory"]["blocks"].as_array().ok_or("blocks")?;let regions=inv["block_regions"].as_array().ok_or("regions")?;let nodes=inv["inventory"]["nodes"].as_array().ok_or("nodes")?;
    let ids:Vec<_>=blocks.iter().zip(regions).filter(|(_,r)|**r==json!("hidden_explanation")).map(|(b,_)|nodes.iter().find(|n|n["source_handle"]==b["paragraph_handle"]).map(|n|n["node_id"].clone()).ok_or("node")).collect::<Result<_,_>>()?;
    assert_eq!(ids.len(),2);v["selector"]["scope"]=json!("node_set");v["selector"]["range"]=json!({"node_ids":ids});assert!(matches!(sort_prepare!(&p,&v),Err(SE::Stored(SS::Output(SortError::Compile(Compile::NoMatches))))));
    v["operation"]["review_policy"]=policy(true,false);let out=sort_prepare!(&p,&v)?;assert_eq!(out.with_verified_bytes(&p,5,section)??,section(&bytes)?.replace(&(a.clone()+&b),&(b+&a)));Ok(())
}
#[path="paragraph_sort_groups_product.rs"]mod groups_v1;
