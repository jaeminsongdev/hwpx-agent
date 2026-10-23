//! Real stored-service boundaries with synthetic scanner/keys. No operational database, Native or body edits.
use std::{error::Error,cell::Cell,sync::atomic::AtomicUsize};
use domain_ir::DocumentId;
use serde_json::{json,Value};
use revision_service as rev;
use hwpx_package::{PreservingXmlDocument,document_import::fields::semantics::catalog::named_styles::{SourceNamedStyleNameQuery as Query,
    SourceNamedStyleKind as Kind,SourceNamedStyleNameAxis as Axis,SourceNamedStyleNameLimits as Limits,SourceNamedStyleNameError as Core}};
use hwpx_agent_cli::form_product_request::named_style_declarations::{NamedStyleDeclarationsProductRequest as Product,NamedStyleDeclarationsProductError as E,
    NAMED_DECLARATIONS_PRODUCT_SCHEMA as SCHEMA};
use hwpx_agent_cli::form_stored_provider::actual_import::named_style_declarations::StoredNamedStyleDeclarationsError as Stored;
include!("support/stored_source_fixture.rs");
#[path="../../hwpx-package/tests/support/search_definition_fixture.rs"]#[allow(dead_code)]mod definition;
#[path="../../hwpx-package/tests/support/document_import_catalog_fixture.rs"]#[allow(dead_code)]mod archive;
type R=Result<(),Box<dyn Error>>;
fn package()->Result<Vec<u8>,Box<dyn Error>>{
    let bytes=definition::package("<hp:p id='1' styleIDRef='0' paraPrIDRef='0'><hp:run charPrIDRef='0'><hp:t>PRIVATE-DECLARATION-BODY</hp:t></hp:run></hp:p>")?;
    archive::mutate_part(&bytes,"Contents/header.xml",|text|{
        let xml=PreservingXmlDocument::parse(text.as_bytes())?;let mut edits=Vec::new();
        for n in xml.elements().iter().filter(|n|n.name().local_name()=="style"){
            let id=n.attributes().iter().find(|a|a.name().local_name()=="id").map(|a|&text[a.value_span().start()..a.value_span().end()]);
            let(kind,native,english)=match id{Some("0")=>("PARA","원본 문단 A","SRC First"),Some("1")=>("PARA","원본 문단 B","SRC Second"),Some("2")=>("PARA","대상 문단","DST"),
                Some("12")=>("CHAR","원본 문자 A","SRC First"),Some("13")=>("CHAR","원본 문자 B","SRC Second"),Some("14")=>("CHAR","대상 문자","DST"),_=>continue};
            for a in n.attributes(){let value=match a.name().local_name(){"type"=>Some(kind),"name"=>Some(native),"engName"=>Some(english),_=>None};
                if let Some(value)=value{edits.push((a.value_span().start(),a.value_span().end(),value));}}
        }edits.sort_by_key(|e|e.0);let mut out=text.to_owned();for(a,b,v)in edits.into_iter().rev(){out.replace_range(a..b,v);}Ok(out)
    })
}
fn query()->Query<'static>{Query{query:"SRC",replacement:"DST",regex:false,case_sensitive:true,whole_word:false,kind:Kind::Character,name_axis:Axis::EnglishName}}
fn request(s:&StoredFixture,bytes:&[u8])->Result<Value,Box<dyn Error>>{Ok(json!({"schema_version":SCHEMA,"idempotency_key":"PRIVATE-DECLARATION-KEY",
    "plan_id":"declaration-plan","project_id":s.project.public_id(),"document_id":"actual-form-document","base_revision":s.head.revision_id().ok_or("head")?.public_id(),
    "expected_head_generation":s.head.generation(),"expected_source_package_sha256":ContentDigest::of(bytes).hex(),
    "operation":{"kind":"resolve_named_style_declarations","query":"SRC","replacement":"DST","regex":false,"case_sensitive":true,"whole_word":false,
        "style_kind":"character","name_axis":"english_name"}}))}
fn wire(v:&Value)->Result<Vec<u8>,serde_json::Error>{serde_json::to_vec(v)}
macro_rules! writer{($s:ident,$actor:ident,$p:ident)=>{
    let $actor=RequestContext::new($s.reader.tenant_id(),$s.reader.subject(),[AuthScope::DocumentRead,AuthScope::DocumentWrite]);
    let $p=StoredFormProvider::bind(&$s.artifacts,&$s.revisions,&$actor,&$s.revision_context,$s.project,$s.branch,DocumentId::parse("actual-form-document")?)?;
}}
macro_rules! prepare{($p:expr,$v:expr)=>{Product::prepare_json($p,&wire($v)?,Default::default(),4)}}
#[test]
fn service_and_product_bind_original_character_declarations_not_equal_property_ids()->R{
    let bytes=package()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=request(&s,&bytes)?;
    let stored=p.import_actual_forms(s.head,4)?.into_named_style_declarations(&p,query(),Default::default(),4)?;let out=prepare!(&p,&v)?;drop(v);
    assert_eq!(stored.receipt(),&out.receipt().stored);let r=stored.verify(&p,5)?;
    assert_eq!(r.from.iter().map(|d|d.native_style_id).collect::<Vec<_>>(),vec![12,13]);assert_eq!(r.from.iter().map(|d|d.character_property.native_id).collect::<Vec<_>>(),vec![1,2]);
    assert_eq!(r.target.native_style_id,14);assert_eq!(r.target.character_property.native_id,3);assert_eq!(r.resolution.changed_mappings,2);
    let value=out.with_verified_json(&p,5,|b|serde_json::from_slice::<Value>(b))??;assert_eq!(value["stored"]["target"]["native_style_id"],14);
    assert_eq!(value["capability_id"],"search.replace_styles");Ok(())
}
#[test]
fn explicit_paragraph_kind_never_infers_character_name_aliases()->R{
    let bytes=package()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=request(&s,&bytes)?;v["operation"]["style_kind"]=json!("paragraph");
    let out=prepare!(&p,&v)?;assert_eq!(out.receipt().stored.from.iter().map(|d|d.native_style_id).collect::<Vec<_>>(),vec![0,1]);assert_eq!(out.receipt().stored.target.native_style_id,2);Ok(())
}
#[test]
fn native_english_regex_case_and_word_axes_reach_single_original_resolution()->R{
    let bytes=package()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes)?;
    for mode in 0..4{let mut v=good.clone();match mode{0=>{v["operation"]["name_axis"]=json!("native_name");v["operation"]["query"]=json!("원본 문자");v["operation"]["replacement"]=json!("대상 문자");},
        1=>{v["operation"]["regex"]=json!(true);v["operation"]["query"]=json!("^SRC (First|Second)$");},2=>{v["operation"]["query"]=json!("src");v["operation"]["case_sensitive"]=json!(false);},_=>v["operation"]["whole_word"]=json!(true)}
        assert_eq!(prepare!(&p,&v)?.receipt().stored.resolution.changed_mappings,2);}Ok(())
}
#[test]
fn every_root_and_operation_field_is_required_before_any_artifact_read()->R{
    let bytes=package()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();
    for key in ["schema_version","idempotency_key","plan_id","project_id","document_id","base_revision","expected_head_generation","expected_source_package_sha256","operation"]{
        let mut v=good.clone();v.as_object_mut().ok_or("root")?.remove(key);assert!(matches!(prepare!(&p,&v),Err(E::Request)));}
    for key in ["kind","query","replacement","regex","case_sensitive","whole_word","style_kind","name_axis"]{
        let mut v=good.clone();v["operation"].as_object_mut().ok_or("operation")?.remove(key);assert!(matches!(prepare!(&p,&v),Err(E::Request)));}
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn enum_objects_null_arrays_and_wrong_boolean_types_are_rejected_before_reads()->R{
    let bytes=package()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();
    for(key,value)in [("kind",json!({"resolve_named_style_declarations":null})),("style_kind",json!({"character":null})),("name_axis",json!({"english_name":null})),
        ("style_kind",Value::Null),("regex",json!("false")),("query",json!([]))]{let mut v=good.clone();v["operation"][key]=value;assert!(matches!(prepare!(&p,&v),Err(E::Request)));}
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn body_selectors_filters_approval_graph_and_mutation_options_are_not_silently_ignored()->R{
    let bytes=package()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();
    for key in ["selector","scope","graph","approved","raw_xml","target_id"]{let mut v=good.clone();v[key]=json!({});assert!(matches!(prepare!(&p,&v),Err(E::Request)));}
    for key in ["preview_only","style_filter","review_policy","source_style_ids","max_changed_paragraphs","body_semantics_verified"]{let mut v=good.clone();v["operation"][key]=json!(false);assert!(matches!(prepare!(&p,&v),Err(E::Request)));}
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn duplicate_escaped_keys_trailing_documents_and_old_schemas_reject_before_reads()->R{
    let bytes=package()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes)?;let text=String::from_utf8(wire(&good)?)?;let before=s.metadata.audit_events()?.len();
    for raw in [text.replace("\"regex\":false","\"regex\":false,\"r\\u0065gex\":true"),text.replace("\"plan_id\":","\"plan_\\u0069d\":\"other\",\"plan_id\":"),format!("{text} {{}}"),"null".into(),"[]".into()]{
        assert!(matches!(Product::prepare_json(&p,raw.as_bytes(),Default::default(),4),Err(E::Request)));}
    for schema in ["hwpx-agent.product-named-paragraph-style-replacement-request/v1","hwpx-agent.product-named-paragraph-style-replacement-request/v2","hwpx-agent.product-named-style-declarations-request/v2"]{
        let mut v=good.clone();v["schema_version"]=json!(schema);assert!(matches!(prepare!(&p,&v),Err(E::Request)));}assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn exact_request_byte_limit_accepts_whitespace_but_one_more_byte_never_reads()->R{
    let bytes=package()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=request(&s,&bytes)?;let mut raw=wire(&v)?;raw.resize(16*1024,b' ');
    let padded=Product::prepare_json(&p,&raw,Default::default(),4)?;let ordinary=prepare!(&p,&v)?;assert_eq!(padded.receipt().canonical_request_sha256,ordinary.receipt().canonical_request_sha256);
    assert_ne!(padded.receipt().raw_request_sha256,ordinary.receipt().raw_request_sha256);raw.push(b' ');let before=s.metadata.audit_events()?.len();
    assert!(matches!(Product::prepare_json(&p,&raw,Default::default(),4),Err(E::Limit)));assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn invalid_names_server_query_limits_and_malformed_digests_reject_before_reads()->R{
    let bytes=package()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();
    for value in ["","A\nB"]{let mut v=good.clone();v["operation"]["query"]=json!(value);assert!(matches!(prepare!(&p,&v),Err(E::Request)));}
    for value in ["F".repeat(64),"0".repeat(63),"g".repeat(64)]{let mut v=good.clone();v["expected_source_package_sha256"]=json!(value);assert!(matches!(prepare!(&p,&v),Err(E::Request)));}
    assert!(matches!(Product::prepare_json(&p,&wire(&good)?,Limits::new(128,2,1024*1024,4*1024*1024)?,4),Err(E::Request)));
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn expected_source_digest_revision_and_generation_must_match_sealed_current_result()->R{
    let bytes=package()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes)?;
    for(key,value)in [("expected_source_package_sha256",json!("0".repeat(64))),("base_revision",json!(rev::RevisionId::generate().public_id())),("expected_head_generation",json!(s.head.generation()+1))]{
        let mut v=good.clone();v[key]=value;assert!(prepare!(&p,&v).is_err());}Ok(())
}
#[test]
fn current_document_write_is_required_for_service_product_and_retained_metadata()->R{
    let bytes=package()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let reader=s.provider()?;let v=request(&s,&bytes)?;
    let source=reader.import_actual_forms(s.head,4)?;assert!(matches!(source.into_named_style_declarations(&reader,query(),Default::default(),4),Err(Stored::Permission)));assert!(prepare!(&reader,&v).is_err());
    let out=prepare!(&p,&v)?;let called=Cell::new(false);assert!(out.verify(&reader,5).is_err());assert!(out.with_verified_json(&reader,5,|_|called.set(true)).is_err());assert!(!called.get());Ok(())
}
#[test]
fn foreign_request_project_and_document_are_rejected_before_reads()->R{
    let bytes=package()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();
    for(key,value)in [("project_id",json!("prj_70000000000000000000000000000002")),("document_id",json!("foreign-document"))]{let mut v=good.clone();v[key]=value;assert!(prepare!(&p,&v).is_err());}
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn five_foreign_provider_scopes_cannot_reuse_service_or_product_results()->R{
    let bytes=package()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let out=prepare!(&p,&request(&s,&bytes)?)?;
    let stored=p.import_actual_forms(s.head,4)?.into_named_style_declarations(&p,query(),Default::default(),4)?;let called=Cell::new(false);
    for mode in 0..5{let tenant=if mode==4{TenantId::new(Uuid::from_u128(998))?}else{s.reader.tenant_id()};let subject=if mode==3{SubjectDigest::from_authenticated_subject("foreign-declarations")?}else{s.reader.subject()};
        let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);let context=rev::RevisionRequestContext::new(tenant,subject);
        let project=if mode==2{rev::ProjectId::parse("prj_70000000000000000000000000000002")?}else{s.project};let branch=if mode==1{rev::BranchId::parse("brn_70000000000000000000000000000002")?}else{s.branch};
        let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&context,project,branch,DocumentId::parse(if mode==0{"foreign-document"}else{"actual-form-document"})?)?;
        assert!(out.verify(&other,5).is_err());assert!(out.with_verified_json(&other,5,|_|called.set(true)).is_err());assert!(stored.verify(&other,5).is_err());assert!(stored.with_verified_json(&other,5,|_|called.set(true)).is_err());}
    assert!(!called.get());Ok(())
}
#[test]
fn revoked_acl_blocks_new_and_retained_declarations_and_regrant_rechecks()->R{
    let bytes=package()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=request(&s,&bytes)?;let out=prepare!(&p,&v)?;
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;let called=Cell::new(false);assert!(out.verify(&p,6).is_err());
    assert!(out.with_verified_json(&p,6,|_|called.set(true)).is_err());assert!(prepare!(&p,&v).is_err());assert!(!called.get());
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;out.verify(&p,8)?;Ok(())
}
#[test]
fn quarantine_blocks_new_and_retained_metadata_without_calling_consumer()->R{
    let bytes=package()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=request(&s,&bytes)?;let out=prepare!(&p,&v)?;
    s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("DECLARATIONS_TEST")?,5)?;let called=Cell::new(false);
    assert!(out.verify(&p,6).is_err());assert!(out.with_verified_json(&p,6,|_|called.set(true)).is_err());assert!(prepare!(&p,&v).is_err());assert!(!called.get());Ok(())
}
#[test]
fn changed_ciphertext_blocks_new_and_retained_metadata_without_calling_consumer()->R{
    let bytes=package()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=request(&s,&bytes)?;let out=prepare!(&p,&v)?;
    s.blobs.tamper.store(true,Ordering::SeqCst);let called=Cell::new(false);assert!(out.verify(&p,6).is_err());assert!(out.with_verified_json(&p,6,|_|called.set(true)).is_err());
    assert!(prepare!(&p,&v).is_err());assert!(!called.get());Ok(())
}
#[test]
fn source_kind_and_unverified_scanner_do_not_become_current_result_authority()->R{
    let bytes=package()?;for(kind,unverified)in [(ArtifactKind::Source,false),(ArtifactKind::Result,true)]{
        let s=StoredFixture::new(&bytes,kind,unverified)?;writer!(s,actor,p);assert!(prepare!(&p,&request(&s,&bytes)?).is_err());}Ok(())
}
#[test]
fn exact_entire_product_response_budget_and_one_byte_less_are_enforced()->R{
    let bytes=package()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=request(&s,&bytes)?;
    let out=prepare!(&p,&v)?;let n=out.with_verified_json(&p,5,<[u8]>::len)?;
    let exact=Product::prepare_json(&p,&wire(&v)?,Limits::new(128,4096,1024*1024,n)?,4)?;assert_eq!(exact.with_verified_json(&p,5,<[u8]>::len)?,n);
    assert!(matches!(Product::prepare_json(&p,&wire(&v)?,Limits::new(128,4096,1024*1024,n-1)?,4),Err(E::Limit)));Ok(())
}
#[test]
fn exact_entire_service_response_budget_is_not_just_inner_resolution_budget()->R{
    let bytes=package()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    let out=p.import_actual_forms(s.head,4)?.into_named_style_declarations(&p,query(),Default::default(),4)?;let n=out.with_verified_json(&p,5,<[u8]>::len)?;
    let exact=p.import_actual_forms(s.head,4)?.into_named_style_declarations(&p,query(),Limits::new(128,4096,1024*1024,n)?,4)?;assert_eq!(exact.with_verified_json(&p,5,<[u8]>::len)?,n);
    assert!(matches!(p.import_actual_forms(s.head,4)?.into_named_style_declarations(&p,query(),Limits::new(128,4096,1024*1024,n-1)?,4),Err(Stored::Limit)));Ok(())
}
#[test]
fn server_mapping_limit_and_regex_compiler_limit_do_not_return_partial_success()->R{
    let bytes=package()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=request(&s,&bytes)?;
    assert!(matches!(Product::prepare_json(&p,&wire(&v)?,Limits::new(1,4096,1024*1024,4*1024*1024)?,4),Err(E::Stored(Stored::Resolution(Core::Limit)))));
    let mut v=v;v["operation"]["regex"]=json!(true);v["operation"]["query"]=json!("[A-Z]+SRC");
    assert!(matches!(Product::prepare_json(&p,&wire(&v)?,Limits::new(128,4096,1,4*1024*1024)?,4),Err(E::Stored(Stored::Resolution(Core::Pattern)))));Ok(())
}
#[test]
fn no_match_no_change_missing_target_and_bad_regex_are_not_successful_previews()->R{
    let bytes=package()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes)?;
    for(query,target,regex,expected)in [("NO SUCH","DST",false,Core::NoMatches),("DST","DST",false,Core::NoChange),("SRC","ABSENT",false,Core::MissingTarget),("[","DST",true,Core::Pattern)]{
        let mut v=good.clone();v["operation"]["query"]=json!(query);v["operation"]["replacement"]=json!(target);v["operation"]["regex"]=json!(regex);
        assert!(matches!(prepare!(&p,&v),Err(E::Stored(Stored::Resolution(e)))if e==expected));}Ok(())
}
#[test]
fn request_plan_key_axis_and_names_bind_receipts_without_disclosing_private_values()->R{
    let bytes=package()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes)?;let first=prepare!(&p,&good)?;
    for(key,value)in [("plan_id",json!("second-plan")),("idempotency_key",json!("PRIVATE-SECOND-KEY"))]{let mut v=good.clone();v[key]=value;let next=prepare!(&p,&v)?;
        assert_ne!(first.receipt().canonical_request_sha256,next.receipt().canonical_request_sha256);assert_eq!(first.receipt().stored,next.receipt().stored);}
    let mut v=good;v["operation"]["query"]=json!("SRC First");assert_ne!(first.receipt().canonical_request_sha256,prepare!(&p,&v)?.receipt().canonical_request_sha256);
    for text in [format!("{first:?}{:?}",first.receipt()),first.with_verified_json(&p,5,|b|String::from_utf8_lossy(b).into_owned())?]{
        assert!(!text.contains("PRIVATE-")&&!text.contains("SRC First")&&!text.contains("DST")&&!text.contains("원본 문자"));}Ok(())
}
#[test]
fn declarations_do_not_mutate_ingest_claim_keys_or_qualify_body_and_route()->R{
    let bytes=package()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let out=prepare!(&p,&request(&s,&bytes)?)?;
    assert!(!out.receipt().idempotency_key_claimed&&!out.receipt().body_mapping_mutation_native_or_execution_qualified);
    assert!(!out.receipt().stored.resolution.body_occurrences_or_target_semantics_qualified&&!out.receipt().stored.resolution.current_access_execution_or_publication_authority);
    assert!(matches!(out.require_current_product_route(&p,5),Err(E::RouteUnqualified)));
    let stored=p.import_actual_forms(s.head,4)?.into_named_style_declarations(&p,query(),Default::default(),4)?;
    assert!(matches!(stored.require_current_product_route(&p,5),Err(Stored::RouteUnqualified)));
    assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);
    assert_eq!(s.artifacts.download(&s.reader,s.result,5)?,bytes);Ok(())
}
struct BoundaryRepo{inner:rev::InMemoryRevisionRepository,calls:AtomicUsize,trigger:AtomicUsize,context:rev::RevisionRequestContext,advance:rev::RevisionCommitRequest}
impl rev::RevisionRepository for BoundaryRepo{
    fn compare_and_swap(&self,c:&rev::RevisionRequestContext,r:&rev::RevisionCommitRequest)->Result<rev::CommitOutcome,rev::RevisionError>{self.inner.compare_and_swap(c,r)}
    fn head(&self,t:TenantId,p:rev::ProjectId,b:rev::BranchId)->Result<rev::RevisionHead,rev::RevisionError>{let n=self.calls.fetch_add(1,Ordering::SeqCst)+1;
        if n==self.trigger.load(Ordering::SeqCst){assert!(matches!(self.inner.compare_and_swap(&self.context,&self.advance)?,rev::CommitOutcome::Committed(_)));}self.inner.head(t,p,b)}
    fn node(&self,t:TenantId,p:rev::ProjectId,r:rev::RevisionId)->Result<rev::RevisionNode,rev::RevisionError>{self.inner.node(t,p,r)}
}
fn race(stage:usize)->R{
    let bytes=package()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=request(&s,&bytes)?;let out=prepare!(&p,&v)?;
    let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,
        ContentDigest::of(b"declaration-race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation fixture"),ContentDigest::of(b"transaction fixture"))?;
    let repo=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
    let bound=StoredFormProvider::bind(&s.artifacts,&repo,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
    match stage{0=>{Product::prepare_json(&bound,&wire(&v)?,Default::default(),5)?;},1=>{out.verify(&bound,5)?;},_=>{out.with_verified_json(&bound,5,|_|())?;}}
    let count=repo.repository().calls.load(Ordering::SeqCst);assert!(count>=4);repo.repository().calls.store(0,Ordering::SeqCst);repo.repository().trigger.store(count,Ordering::SeqCst);let called=Cell::new(false);
    match stage{0=>assert!(Product::prepare_json(&bound,&wire(&v)?,Default::default(),6).is_err()),1=>assert!(out.verify(&bound,6).is_err()),_=>assert!(out.with_verified_json(&bound,6,|_|called.set(true)).is_err())}
    assert!(!called.get());assert_eq!(repo.repository().calls.load(Ordering::SeqCst),count);Ok(())
}
#[test]fn preparation_consumer_final_head_race_rejects()->R{race(0)}
#[test]fn retained_verification_final_head_race_rejects()->R{race(1)}
#[test]fn metadata_delivery_final_head_race_blocks_consumer()->R{race(2)}
