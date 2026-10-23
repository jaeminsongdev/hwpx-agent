//! Actual current stored/multigroup JSON candidate tests, not execution or Native acceptance.
use super::*;
use hwpx_agent_cli::form_product_request::stored_literal_replacement::sort_groups::{StoredParagraphSortGroupsProductRequest as GroupsProduct,
    ParagraphSortGroupsProductError as GE,PARAGRAPH_SORT_GROUPS_PRODUCT_REQUEST_SCHEMA as GROUPS_SCHEMA};
use hwpx_agent_cli::form_stored_provider::actual_import::literal_search_output::sort_groups::StoredParagraphSortGroupsError as GS;
use std::io::Write as _;
macro_rules! groups_prepare{($p:expr,$v:expr)=>{GroupsProduct::prepare_json($p,&wire($v)?,Default::default(),Default::default(),4)}}
fn groups_request(s:&StoredFixture,b:&[u8])->Result<Value,Box<dyn Error>>{
    let mut v=sort_request(s,b)?;v["schema_version"]=json!(GROUPS_SCHEMA);v["operation"]["kind"]=json!("sort_paragraph_groups");Ok(v)
}
fn two_parts(first:&str,second:&str)->Result<Vec<u8>,Box<dyn Error>>{
    use zip::{ZipWriter,CompressionMethod,write::SimpleFileOptions};
    let raw=definition::package(first)?;let mut reader=hwpx_package::BoundedZipReader::open(Cursor::new(&raw),Default::default())?;
    let names:Vec<_>=reader.entries().iter().map(|e|e.path.as_str().to_owned()).collect();let mut writer=ZipWriter::new(Cursor::new(Vec::new()));
    for(i,name)in names.iter().enumerate(){let data=reader.read_entry(i)?;writer.start_file(name,SimpleFileOptions::default().compression_method(CompressionMethod::Stored))?;
        if name=="Contents/content.hpf"{let text=String::from_utf8(data)?.replace("</o:manifest>","<o:item id='s2' href='Contents/section1.xml' media-type='application/xml'/></o:manifest>")
            .replace("</o:spine>","<o:itemref idref='s2'/></o:spine>");writer.write_all(text.as_bytes())?;}else{writer.write_all(&data)?;}}
    writer.start_file("Contents/section1.xml",SimpleFileOptions::default().compression_method(CompressionMethod::Stored))?;
    writer.write_all(format!("<hs:sec xmlns:hs='http://www.hancom.co.kr/hwpml/2011/section' xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph'>{second}</hs:sec>").as_bytes())?;
    Ok(writer.finish()?.into_inner())
}
fn groups_specimen()->Result<Vec<u8>,Box<dyn Error>>{two_parts(&(para(1,"Z-PRIVATE")+&para(2,"A")),&(para(1,"Y")+&para(2,"B-LONG")))}
fn part_bytes(b:&[u8],name:&str)->Result<Vec<u8>,Box<dyn Error>>{
    let mut zip=hwpx_package::BoundedZipReader::open(Cursor::new(b),Default::default())?;let i=zip.entries().iter().find(|e|e.path.as_str()==name).ok_or("part")?.index;Ok(zip.read_entry(i)?)
}

#[test]
fn groups_product_sorts_two_parts_with_local_ids_and_retains_owned_request()->TestResult{
    let bytes=groups_specimen()?;let original=bytes.clone();let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=groups_request(&s,&bytes)?;
    let out=groups_prepare!(&p,&v)?;drop(v);out.verify(&p,5)?;let next=out.with_verified_bytes(&p,5,<[u8]>::to_vec)?;
    assert_eq!(section(&next)?,section(&bytes)?.replace(&(para(1,"Z-PRIVATE")+&para(2,"A")),&(para(2,"A")+&para(1,"Z-PRIVATE"))));
    assert_eq!(String::from_utf8(part_bytes(&next,"Contents/section1.xml")?)?,String::from_utf8(part_bytes(&bytes,"Contents/section1.xml")?)?.replace(&(para(1,"Y")+&para(2,"B-LONG")),&(para(2,"B-LONG")+&para(1,"Y"))));
    assert_eq!(bytes,original);let r=&out.receipt().stored.output;assert_eq!((r.groups.len(),r.changed_groups,r.changed_parts,r.moved_paragraphs),(2,2,2,4));
    assert!(r.groups.iter().all(|g|g.source_order==[1,0]));assert_eq!(out.receipt().capability_id,"search.sort_text");Ok(())
}
#[test]
fn groups_product_borrowed_owned_and_json_are_identical_without_repeated_sort()->TestResult{
    let bytes=groups_specimen()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=groups_request(&s,&bytes)?;let out=groups_prepare!(&p,&v)?;
    let source=p.import_actual_forms(s.head,4)?;let borrowed=source.prepare_paragraph_sort_groups_candidate(&p,Scope::Document,Policy::default(),spec(),Default::default(),Default::default(),4)?;
    assert_eq!(borrowed.verify(&p,5)?,out.receipt().stored);drop(borrowed);
    let owned=source.into_paragraph_sort_groups_candidate(&p,Scope::Document,Policy::default(),spec(),Default::default(),Default::default(),4)?;
    assert_eq!(owned.verify(&p,5)?,out.receipt().stored);assert_eq!(owned.with_verified_bytes(&p,5,<[u8]>::to_vec)?,out.with_verified_bytes(&p,5,<[u8]>::to_vec)?);
    assert!(matches!(owned.require_current_product_route(&p,5),Err(GS::RouteUnqualified)));Ok(())
}
#[test]
fn groups_product_discovers_four_scopes_and_does_not_widen_section_scope()->TestResult{
    let bytes=groups_specimen()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=groups_request(&s,&bytes)?;let inv=inventory(&p,&good)?;
    for scope in["document","section","node_set","selection"]{let mut v=good.clone();v["selector"]["scope"]=json!(scope);
        match scope{"section"=>v["selector"]["section_ids"]=json!([inv["inventory"]["section_ids"][0].clone()]),"node_set"=>{let ids:Vec<_>=inv["inventory"]["nodes"].as_array().ok_or("nodes")?.iter().map(|n|n["node_id"].clone()).collect();v["selector"]["range"]=json!({"node_ids":ids});},"selection"=>v["selector"]["range"]=full_range(&inv)?,_=>{}}
        let out=groups_prepare!(&p,&v)?;assert_eq!(out.receipt().stored.output.changed_groups,if scope=="section"{1}else{2});
        if scope=="section"{assert_eq!(out.with_verified_bytes(&p,5,|b|part_bytes(b,"Contents/section1.xml"))??,part_bytes(&bytes,"Contents/section1.xml")?);}
    }Ok(())
}
#[test]
fn groups_product_descending_nfc_equal_keys_keep_per_group_stable_identity()->TestResult{
    let body=para(1,"가")+&para(2,"Z")+&para(3,"가");let bytes=two_parts(&body,&body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
    for(direction,order)in[("ascending",vec![1,0,2]),("descending",vec![0,2,1])]{let mut v=groups_request(&s,&bytes)?;v["operation"]["sort_spec"]["direction"]=json!(direction);let out=groups_prepare!(&p,&v)?;
        assert!(out.receipt().stored.output.groups.iter().all(|g|g.source_order==order&&g.entries[0].normalized_key_sha256==g.entries[2].normalized_key_sha256));}Ok(())
}
#[test]
fn groups_product_singleton_and_identity_groups_remain_in_receipt()->TestResult{
    for second in[para(1,"SINGLE"),para(1,"A")+&para(2,"B")]{let bytes=two_parts(&(para(1,"Z")+&para(2,"A")),&second)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
        let v=groups_request(&s,&bytes)?;let out=groups_prepare!(&p,&v)?;let r=&out.receipt().stored.output;assert_eq!((r.groups.len(),r.changed_groups,r.changed_parts),(2,1,1));
        assert_eq!(out.with_verified_bytes(&p,5,|b|part_bytes(b,"Contents/section1.xml"))??,part_bytes(&bytes,"Contents/section1.xml")?);}Ok(())
}
#[test]
fn groups_product_partial_or_stale_selection_fails_without_widening()->TestResult{
    let bytes=groups_specimen()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=groups_request(&s,&bytes)?;let inv=inventory(&p,&v)?;
    v["selector"]["scope"]=json!("selection");v["selector"]["range"]=full_range(&inv)?;v["selector"]["range"]["start"]["normalized_scalar"]=json!(1);
    assert!(matches!(groups_prepare!(&p,&v),Err(GE::Stored(GS::Output(SortError::IncompleteParagraphScope)))));
    v["selector"]["range"]["index_sha256"]=json!("0".repeat(64));assert!(groups_prepare!(&p,&v).is_err());Ok(())
}
#[test]
fn groups_product_closed_schema_kind_and_unknown_fields_fail_before_source_reads()->TestResult{
    let bytes=groups_specimen()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=groups_request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();
    for mode in 0..8{let mut v=good.clone();match mode{0=>v["schema_version"]=json!(SORT_SCHEMA),1=>v["operation"]["kind"]=json!("sort_sibling_paragraphs"),2=>v["source_graph"]=json!({}),3=>v["operation"]["query"]=json!("private"),4=>v["selector"]["approved"]=json!(true),5=>v["operation"]["sort_spec"]["locale"]=json!("ko-KR"),6=>v["operation"]["review_policy"]["approved"]=json!(true),_=>v["operation"]["grouping"]=json!("cross_parents")};assert!(matches!(groups_prepare!(&p,&v),Err(GE::Request)));}
    for raw in[wire(&json!([good.clone()]))?,[wire(&good)?,b"{}".to_vec()].concat(),b"null".to_vec()]{assert!(matches!(GroupsProduct::prepare_json(&p,&raw,Default::default(),Default::default(),4),Err(GE::Request)));}
    assert!(matches!(SortProduct::prepare_json(&p,&wire(&good)?,Default::default(),Default::default(),4),Err(SE::Request)));
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn groups_product_escaped_duplicate_keys_fail_at_every_nested_boundary_before_reads()->TestResult{
    let bytes=groups_specimen()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=groups_request(&s,&bytes)?;let text=serde_json::to_string(&v)?;let before=s.metadata.audit_events()?.len();
    for(from,to)in[("\"direction\":\"ascending\"","\"direction\":\"ascending\",\"direct\\u0069on\":\"descending\""),("\"scope\":\"document\"","\"scope\":\"document\",\"scope\":\"section\""),("\"include_memo_bodies\":false","\"include_memo_bodies\":false,\"include_memo_bodies\":true"),("\"kind\":\"sort_paragraph_groups\"","\"kind\":\"sort_paragraph_groups\",\"kind\":\"sort_sibling_paragraphs\"")]{let bad=text.replace(from,to);assert_ne!(bad,text);assert!(matches!(GroupsProduct::prepare_json(&p,bad.as_bytes(),Default::default(),Default::default(),4),Err(GE::Request)));}
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn groups_product_missing_wrong_type_and_unsupported_policy_reject_before_reads()->TestResult{
    let bytes=groups_specimen()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=groups_request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();
    for key in["schema_version","idempotency_key","project_id","document_id","base_revision","expected_head_generation","expected_source_package_sha256","plan_id","selector","operation"]{let mut v=good.clone();v.as_object_mut().ok_or("root")?.remove(key);assert!(matches!(groups_prepare!(&p,&v),Err(GE::Request)));}
    for key in["kind","sort_spec","review_policy"]{let mut v=good.clone();v["operation"].as_object_mut().ok_or("operation")?.remove(key);assert!(matches!(groups_prepare!(&p,&v),Err(GE::Request)));}
    for value in[json!(null),json!([]),json!({}),json!({"include_memo_bodies":false})]{let mut v=good.clone();v["operation"]["review_policy"]=value;assert!(matches!(groups_prepare!(&p,&v),Err(GE::Request)));}
    for n in[0,33554433]{let mut v=good.clone();v["operation"]["sort_spec"]["max_comparison_bytes"]=json!(n);assert!(matches!(groups_prepare!(&p,&v),Err(GE::Request)));}
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn groups_product_exact_16k_and_raw_canonical_scoped_request_bindings()->TestResult{
    let bytes=groups_specimen()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=groups_request(&s,&bytes)?;let compact=wire(&good)?;let mut padded=compact.clone();padded.resize(16384,b' ');
    let a=GroupsProduct::prepare_json(&p,&compact,Default::default(),Default::default(),4)?;let b=GroupsProduct::prepare_json(&p,&padded,Default::default(),Default::default(),4)?;
    assert_ne!(a.receipt().raw_request_sha256,b.receipt().raw_request_sha256);assert_eq!(a.receipt().canonical_request_sha256,b.receipt().canonical_request_sha256);assert_eq!(a.receipt().scoped_request_sha256,b.receipt().scoped_request_sha256);
    let before=s.metadata.audit_events()?.len();padded.push(b' ');for raw in[padded,vec![]]{assert!(matches!(GroupsProduct::prepare_json(&p,&raw,Default::default(),Default::default(),4),Err(GE::Limit)));}assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn groups_product_key_plan_direction_and_policy_bind_canonical_and_scope_hashes()->TestResult{
    let body=para(1,"B")+&para(2,"A")+&para(3,"C");let bytes=two_parts(&body,&body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=groups_request(&s,&bytes)?;let a=groups_prepare!(&p,&good)?;
    for mode in 0..4{let mut v=good.clone();match mode{0=>v["idempotency_key"]=json!("DIFFERENT-KEY"),1=>v["plan_id"]=json!("different-plan"),2=>v["operation"]["sort_spec"]["direction"]=json!("descending"),_=>v["operation"]["review_policy"]=policy(true,true)};
        let b=groups_prepare!(&p,&v)?;assert_ne!(a.receipt().canonical_request_sha256,b.receipt().canonical_request_sha256);assert_ne!(a.receipt().scoped_request_sha256,b.receipt().scoped_request_sha256);}Ok(())
}
#[test]
fn groups_product_current_write_and_five_external_scope_axes_guard_retained_output()->TestResult{
    let bytes=groups_specimen()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=groups_request(&s,&bytes)?;let reader=s.provider()?;
    assert!(groups_prepare!(&reader,&v).is_err());let source=reader.import_actual_forms(s.head,4)?;
    assert!(matches!(source.prepare_paragraph_sort_groups_candidate(&reader,Scope::Document,Policy::default(),spec(),Default::default(),Default::default(),4),Err(GS::Permission)));
    let out=groups_prepare!(&p,&v)?;let called=Cell::new(false);assert!(out.with_verified_bytes(&reader,5,|_|called.set(true)).is_err());
    for variant in 0..5{let tenant=if variant==4{TenantId::new(Uuid::from_u128(997))?}else{s.reader.tenant_id()};let subject=if variant==3{SubjectDigest::from_authenticated_subject("foreign-groups")?}else{s.reader.subject()};
        let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);let context=rev::RevisionRequestContext::new(tenant,subject);
        let project=if variant==2{rev::ProjectId::parse("prj_70000000000000000000000000000002")?}else{s.project};let branch=if variant==1{rev::BranchId::parse("brn_70000000000000000000000000000002")?}else{s.branch};
        let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&context,project,branch,DocumentId::parse(if variant==0{"foreign-document"}else{"actual-form-document"})?)?;
        assert!(out.verify(&other,5).is_err());assert!(out.with_verified_bytes(&other,5,|_|called.set(true)).is_err());}assert!(!called.get());Ok(())
}
#[test]
fn groups_product_acl_regrant_quarantine_aead_recheck_on_every_delivery()->TestResult{
    for mode in 0..3{let bytes=groups_specimen()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=groups_request(&s,&bytes)?;let out=groups_prepare!(&p,&v)?;
        match mode{0=>{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;},1=>{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("GROUPS_TEST")?,5)?;},_=>s.blobs.tamper.store(true,Ordering::SeqCst)}
        let called=Cell::new(false);assert!(out.verify(&p,6).is_err());assert!(out.with_verified_bytes(&p,6,|_|called.set(true)).is_err());assert!(groups_prepare!(&p,&v).is_err());assert!(!called.get());
        if mode==0{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;out.verify(&p,8)?;}}Ok(())
}
#[test]
fn groups_product_prepare_verify_and_delivery_last_head_races_block_consumer()->TestResult{
    for stage in 0..3{let bytes=groups_specimen()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=groups_request(&s,&bytes)?;let wire=wire(&v)?;let out=groups_prepare!(&p,&v)?;
        let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,
            ContentDigest::of(b"groups race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation"),ContentDigest::of(b"transaction"))?;
        let b=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
        let bound=StoredFormProvider::bind(&s.artifacts,&b,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
        match stage{0=>{GroupsProduct::prepare_json(&bound,&wire,Default::default(),Default::default(),5)?;},1=>{out.verify(&bound,5)?;},_=>{out.with_verified_bytes(&bound,5,|_|())?;}}
        let calls=b.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);b.repository().calls.store(0,Ordering::SeqCst);b.repository().trigger.store(calls,Ordering::SeqCst);let called=Cell::new(false);
        match stage{0=>assert!(GroupsProduct::prepare_json(&bound,&wire,Default::default(),Default::default(),6).is_err()),1=>assert!(out.verify(&bound,6).is_err()),_=>assert!(out.with_verified_bytes(&bound,6,|_|called.set(true)).is_err())}
        assert!(!called.get());assert_eq!(b.repository().calls.load(Ordering::SeqCst),calls);
    }Ok(())
}
#[test]
fn groups_product_wrong_source_head_revision_project_and_document_reject()->TestResult{
    let bytes=groups_specimen()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=groups_request(&s,&bytes)?;
    for(key,value)in[("expected_head_generation",json!(s.head.generation()+1)),("expected_source_package_sha256",json!("0".repeat(64))),("document_id",json!("foreign-document")),("project_id",json!("prj_70000000000000000000000000000002")),("base_revision",json!(rev::RevisionId::generate().public_id()))]{let mut v=good.clone();v[key]=value;assert!(groups_prepare!(&p,&v).is_err());}Ok(())
}
#[test]
fn groups_product_global_comparison_source_response_and_writer_limits_reject_whole_output()->TestResult{
    let bytes=two_parts(&(para(1,"Z")+&para(2,"A")),&(para(1,"Y")+&para(2,"B")))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=groups_request(&s,&bytes)?;
    v["operation"]["sort_spec"]["max_comparison_bytes"]=json!(1);assert!(matches!(groups_prepare!(&p,&v),Err(GE::Stored(GS::Output(SortError::ComparisonLimit)))));
    v["operation"]["sort_spec"]["max_comparison_bytes"]=json!(2);assert_eq!(groups_prepare!(&p,&v)?.receipt().stored.output.comparison_bytes,2);
    for config in[Config{scalars:1,..Default::default()},Config{result_bytes:1,..Default::default()}]{assert!(GroupsProduct::prepare_json(&p,&wire(&v)?,SourceSearchLimits::new(config)?,Default::default(),4).is_err());}
    assert!(matches!(GroupsProduct::prepare_json(&p,&wire(&v)?,Default::default(),WriterLimits::new(WriterLimitConfig{max_output_bytes:1})?,4),Err(GE::Stored(GS::Output(SortError::Compile(Compile::Writer))))));Ok(())
}
#[test]
fn groups_product_protected_identity_group_and_all_noop_cases_are_not_skipped()->TestResult{
    let tracked=(para(1,"A")+&para(2,"B")).replace("charPrIDRef='0'","charPrIDRef='0' charTcId='1'");let bytes=two_parts(&(para(1,"Z")+&para(2,"A")),&tracked)?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=groups_request(&s,&bytes)?;assert!(matches!(groups_prepare!(&p,&v),Err(GE::Stored(GS::Output(SortError::Compile(Compile::Protection))))));
    for(first,second,nomatch)in[(para(1,"Z"),para(1,"A"),true),(para(1,"A")+&para(2,"B"),para(1,"C")+&para(2,"D"),false)]{
        let bytes=two_parts(&first,&second)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=groups_request(&s,&bytes)?;
        let e=groups_prepare!(&p,&v).expect_err("no change");if nomatch{assert!(matches!(e,GE::Stored(GS::Output(SortError::Compile(Compile::NoMatches)))));}else{assert!(matches!(e,GE::Stored(GS::Output(SortError::Compile(Compile::NoChange)))));}
    }Ok(())
}
#[test]
fn groups_product_hidden_and_memo_groups_obey_policy_and_keep_field_cache()->TestResult{
    for memo in[false,true]{let mut envelopes=String::new();for(base,a,b)in[(10,"Z","A"),(20,"Y","B")]{let sub=format!("<hp:subList>{}{}</hp:subList>",para(base+1,a),para(base+2,b));
        if memo{envelopes.push_str(&format!("<hp:ctrl><hp:fieldBegin id='{base}' type='MEMO' editable='0'>{sub}</hp:fieldBegin></hp:ctrl><hp:t>CACHE-{base}</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='{base}'/></hp:ctrl>"));}
        else{envelopes.push_str(&format!("<hp:ctrl><hp:hiddenComment>{sub}</hp:hiddenComment></hp:ctrl>"));}}
        let bytes=definition::package(&para(1,&format!("BODY</hp:t>{envelopes}<hp:t>TAIL")))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=groups_request(&s,&bytes)?;let inv=inventory(&p,&v)?;
        let blocks=inv["inventory"]["blocks"].as_array().ok_or("blocks")?;let regions=inv["block_regions"].as_array().ok_or("regions")?;let nodes=inv["inventory"]["nodes"].as_array().ok_or("nodes")?;
        let wanted=if memo{"memo_body"}else{"hidden_explanation"};let ids:Vec<_>=blocks.iter().zip(regions).filter(|(_,r)|**r==json!(wanted)).map(|(b,_)|nodes.iter().find(|n|n["source_handle"]==b["paragraph_handle"]).map(|n|n["node_id"].clone()).ok_or("node")).collect::<Result<_,_>>()?;
        assert_eq!(ids.len(),4);v["selector"]["scope"]=json!("node_set");v["selector"]["range"]=json!({"node_ids":ids});assert!(matches!(groups_prepare!(&p,&v),Err(GE::Stored(GS::Output(SortError::Compile(Compile::NoMatches))))));
        v["operation"]["review_policy"]=policy(!memo,memo);let out=groups_prepare!(&p,&v)?;assert_eq!(out.receipt().stored.output.changed_groups,2);let mut expected=section(&bytes)?;
        for(base,a,b)in[(10,"Z","A"),(20,"Y","B")]{expected=expected.replace(&(para(base+1,a)+&para(base+2,b)),&(para(base+2,b)+&para(base+1,a)));}
        assert_eq!(out.with_verified_bytes(&p,5,section)??,expected);
    }Ok(())
}
#[test]
fn groups_product_private_receipts_closed_routes_and_no_ingest_or_head_mutation()->TestResult{
    let bytes=groups_specimen()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=groups_request(&s,&bytes)?;let out=groups_prepare!(&p,&v)?;
    for text in[format!("{out:?}{:?}",out.receipt()),serde_json::to_string(out.receipt())?]{assert!(!text.contains("Z-PRIVATE")&&!text.contains("PRIVATE-UNICODE-KEY"));}
    assert!(matches!(out.require_current_product_route(&p,5),Err(GE::RouteUnqualified)));assert!(!out.receipt().idempotency_key_claimed&&!out.receipt().full_sort_native_cas_execution_publication_authority);
    assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
}
#[test]
fn groups_product_128_paragraphs_are_retained_as_one_current_candidate()->TestResult{
    let body=(0..64).rev().map(|i|para(i+1,&format!("KEY-{i:03}"))).collect::<String>();let bytes=two_parts(&body,&body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=groups_request(&s,&bytes)?;
    let out=groups_prepare!(&p,&v)?;let r=&out.receipt().stored.output;assert_eq!((r.selected_paragraphs,r.moved_paragraphs,r.changed_groups,r.changed_parts),(128,128,2,2));
    assert!(r.groups.iter().all(|g|g.source_order==(0..64).rev().collect::<Vec<_>>()));out.verify(&p,5)?;out.with_verified_bytes(&p,5,|_|())?;Ok(())
}
