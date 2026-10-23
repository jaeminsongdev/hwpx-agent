//! Standalone focused binary: reuse original service fixture, do not compile/run the huge old suite.
use std::{error::Error,cell::Cell,sync::atomic::AtomicUsize};
use domain_ir::DocumentId;
use serde_json::{json,Value};
use revision_service as rev;
use hwpx_agent_cli::form_product_request::stored_literal_replacement::fonts::{StoredFontProductRequest as Product,FontProductError as E,FONT_PRODUCT_REQUEST_SCHEMA as SCHEMA};
use hwpx_agent_cli::form_stored_provider::actual_import::literal_search_output::fonts::StoredFontError as Stored;
use hwpx_package::{PreservingXmlDocument,CharacterStyleCatalogReader,WriterLimits,WriterLimitConfig,
    document_import::{fields::semantics::catalog::fonts::{ImportedFontLanguage as L,names::FontNameReplacementQuery as Query},
        search::{SourceSearchLimits,SourceSearchLimitConfig as Config,selector::SourceIndexScopeSelector as Scope,reviews::SourceReviewTextPolicy as Policy,
            replacement::{SourceLiteralReplacementError as Compile,atoms::styles::fonts::{SourceFontStyleAxis as Axis,SourceFontReplacementError as SourceError}}}}};
include!("support/stored_source_fixture.rs");
#[path="../../hwpx-package/tests/support/search_definition_fixture.rs"]#[allow(dead_code)]mod definition;
#[path="../../hwpx-package/tests/support/document_import_catalog_fixture.rs"]#[allow(dead_code)]mod archive;
type R=Result<(),Box<dyn Error>>;
const TARGET:&str="PRIVATE-FONT-DEST";
const LANGUAGES:[L;7]=[L::Hangul,L::Latin,L::Hanja,L::Japanese,L::Other,L::Symbol,L::User];
macro_rules! writer{($s:ident,$actor:ident,$p:ident)=>{
    let $actor=RequestContext::new($s.reader.tenant_id(),$s.reader.subject(),[AuthScope::DocumentRead,AuthScope::DocumentWrite]);
    let $p=StoredFormProvider::bind(&$s.artifacts,&$s.revisions,&$actor,&$s.revision_context,$s.project,$s.branch,DocumentId::parse("actual-form-document")?)?;
}}
macro_rules! prepare{($p:expr,$v:expr)=>{Product::prepare_json($p,&wire($v)?,Default::default(),Default::default(),4)}}
fn wire(v:&Value)->Result<Vec<u8>,serde_json::Error>{serde_json::to_vec(v)}
fn policy()->Policy{Policy{include_hidden_explanations:false,include_memo_bodies:false}}
fn package(body:&str)->Result<Vec<u8>,Box<dyn Error>>{
    archive::mutate_part(&definition::package(body)?,"Contents/header.xml",|text|{
        let xml=PreservingXmlDocument::parse(text.as_bytes())?;let mut edits=Vec::new();
        for(i,group)in xml.elements().iter().enumerate().filter(|(_,n)|n.name().local_name()=="fontface"){
            let fonts:Vec<_>=xml.elements().iter().filter(|n|n.parent()==Some(i)&&n.name().local_name()=="font").collect();
            let first=fonts.first().ok_or("font")?;let span=first.outer_span().ok_or("font span")?;let mut copy=text[span.start()..span.end()].to_owned();let mut attrs=Vec::new();
            for a in first.attributes(){let v=match a.name().local_name(){"id"=>Some(fonts.len().to_string()),"face"=>Some(TARGET.to_owned()),_=>None};
                if let Some(v)=v{let s=a.value_span();attrs.push((s.start()-span.start(),s.end()-span.start(),v));}}
            attrs.sort_by_key(|e|e.0);for(a,b,v)in attrs.into_iter().rev(){copy.replace_range(a..b,&v);}
            let count=group.attributes().iter().find(|a|a.name().local_name()=="fontCnt").ok_or("font count")?.value_span();
            edits.push((count.start(),count.end(),(fonts.len()+1).to_string()));let at=group.end_tag_span().ok_or("font group")?.start();edits.push((at,at,copy));
        }edits.sort_by_key(|e|e.0);let mut result=text.to_owned();for(a,b,v)in edits.into_iter().rev(){result.replace_range(a..b,&v);}Ok(result)
    })
}
fn raw(text:&str)->Result<Vec<u8>,Box<dyn Error>>{package(&format!("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>{text}</hp:t></hp:run></hp:p>"))}
fn name(bytes:&[u8],style:u32)->Result<String,Box<dyn Error>>{
    let catalog=CharacterStyleCatalogReader::read(&archive::read_part(bytes,"Contents/header.xml")?,Default::default())?;
    let id=catalog.styles[style as usize].font_refs.hangul;
    Ok(catalog.font_faces.iter().find(|g|g.language==hwpx_package::LanguageSlot::Hangul).and_then(|g|g.fonts.iter().find(|f|f.id==id)).ok_or("font name")?.face.clone())
}
fn query<'a>(name:&'a str)->Query<'a>{Query{query:name,replacement:TARGET,regex:false,case_sensitive:true,whole_word:false,languages:&LANGUAGES}}
fn request(s:&StoredFixture,bytes:&[u8])->Result<Value,Box<dyn Error>>{
    let revision=s.head.revision_id().ok_or("head")?.public_id();
    Ok(json!({"schema_version":SCHEMA,"idempotency_key":"PRIVATE-FONT-KEY","plan_id":"font-plan","project_id":s.project.public_id(),"document_id":"actual-form-document",
        "base_revision":revision,"expected_head_generation":s.head.generation(),"expected_source_package_sha256":ContentDigest::of(bytes).hex(),
        "selector":{"revision_id":revision,"scope":"document"},"operation":{"kind":"replace_fonts","query":name(bytes,0)?,"replacement":TARGET,"regex":false,
        "case_sensitive":true,"whole_word":false,"languages":["hangul","latin","hanja","japanese","other","symbol","user"],"axis":"run_property",
        "max_changed_scalars":100,"review_policy":policy()}}))
}
fn inventory(provider:&Provider<'_>,request:&Value)->Result<Value,Box<dyn Error>>{
    use hwpx_agent_cli::form_product_request::stored_source_search::selector::review::StoredReviewScopeProductRequest;
    let mut v=request.clone();v["schema_version"]=json!("hwpx-agent.product-source-search-request/v6");v["operation"]=json!({"kind":"scope_inventory"});
    let out=StoredReviewScopeProductRequest::prepare_json(provider,&wire(&v)?,Default::default(),4)?;
    Ok(out.with_verified_json(provider,5,|bytes|serde_json::from_slice::<Value>(bytes))??)
}
fn selection(inv:&Value,a:usize,b:usize)->Result<Value,Box<dyn Error>>{
    let block=&inv["inventory"]["blocks"][0];let hash:[u8;32]=serde_json::from_value(inv["inventory"]["index"]["index_sha256"].clone())?;
    Ok(json!({"coordinate_space":"index_nfc_unicode_scalars","index_sha256":hex::encode(hash),
        "start":{"paragraph_handle":block["paragraph_handle"],"block_index":block["block_index"],"normalized_scalar":a},
        "end":{"paragraph_handle":block["paragraph_handle"],"block_index":block["block_index"],"normalized_scalar":b}}))
}
fn refs(bytes:&[u8])->Result<Vec<(String,u32,Option<u32>)>,Box<dyn Error>>{
    let bytes=archive::read_part(bytes,"Contents/section0.xml")?;let text=std::str::from_utf8(&bytes)?;let xml=PreservingXmlDocument::parse(&bytes)?;let mut out=Vec::new();
    for node in xml.elements().iter().filter(|n|n.name().local_name()=="t"){
        let parent=&xml.elements()[node.parent().ok_or("run")?];let attr=|n:&hwpx_package::XmlElementToken,key:&str|->Result<Option<u32>,Box<dyn Error>>{
            n.attributes().iter().find(|a|a.name().local_name()==key).map(|a|{let s=a.value_span();Ok(text[s.start()..s.end()].parse()?)}).transpose()
        };let span=node.content_span().ok_or("text")?;out.push((text[span.start()..span.end()].to_owned(),attr(parent,"charPrIDRef")?.ok_or("run style")?,attr(node,"charStyleIDRef")?));
    }Ok(out)
}
#[test]
fn product_document_candidate_is_owned_verified_and_changes_actual_source_refs()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=request(&s,&bytes)?;let out=prepare!(&p,&v)?;drop(v);
    out.verify(&p,5)?;let output=out.with_verified_bytes(&p,5,<[u8]>::to_vec)?;assert_eq!(refs(&output)?[0].0,"ABC");assert_ne!(refs(&output)?[0].1,0);
    assert_eq!(name(&output,refs(&output)?[0].1)?,TARGET);
    assert_eq!(out.receipt().capability_id,"search.replace_fonts");assert_eq!(out.receipt().stored.output.changed_source_scalars,3);Ok(())
}
#[test]
fn product_partial_selection_preserves_other_users_of_shared_property()->R{
    let bytes=raw("ABCD")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=request(&s,&bytes)?;let inv=inventory(&p,&v)?;
    v["selector"]["scope"]=json!("selection");v["selector"]["range"]=selection(&inv,1,3)?;let out=prepare!(&p,&v)?;let values=out.with_verified_bytes(&p,5,refs)??;
    assert_eq!(values.iter().map(|v|v.0.as_str()).collect::<String>(),"ABCD");assert_eq!(values[0].1,0);assert_ne!(values[1].1,0);assert_eq!(values[2].1,0);Ok(())
}
#[test]
fn product_text_axis_preserves_run_and_unselected_text_axis()->R{
    let bytes=package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t charStyleIDRef='1'>ABCD</hp:t></hp:run></hp:p>")?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=request(&s,&bytes)?;v["operation"]["axis"]=json!("text_style");v["operation"]["query"]=json!(name(&bytes,1)?);
    let inv=inventory(&p,&v)?;v["selector"]["scope"]=json!("selection");v["selector"]["range"]=selection(&inv,1,3)?;let out=prepare!(&p,&v)?;let values=out.with_verified_bytes(&p,5,refs)??;
    assert!(values.iter().all(|v|v.1==0));assert_eq!(values[0].2,Some(1));assert_ne!(values[1].2,Some(1));assert_eq!(values[2].2,Some(1));
    let output=out.with_verified_bytes(&p,5,<[u8]>::to_vec)?;assert_eq!(name(&output,values[1].2.ok_or("selected text style")?)?,TARGET);Ok(())
}
#[test]
fn product_section_and_node_set_selectors_come_from_current_discovery()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes)?;let inv=inventory(&p,&good)?;
    let mut section=good.clone();section["selector"]["scope"]=json!("section");section["selector"]["section_ids"]=inv["inventory"]["section_ids"].clone();assert_eq!(prepare!(&p,&section)?.receipt().stored.output.selector.kind,"section");
    let mut node=good;node["selector"]["scope"]=json!("node_set");node["selector"]["range"]=json!({"node_ids":[inv["inventory"]["nodes"][0]["node_id"].clone()]});
    assert_eq!(prepare!(&p,&node)?.receipt().stored.output.selector.kind,"node_set");Ok(())
}
#[test]
fn stored_borrowed_owned_and_product_paths_have_identical_source_bound_output()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let source=p.import_actual_forms(s.head,4)?;let n=name(&bytes,0)?;
    let borrowed=source.prepare_font_candidate(&p,query(&n),Scope::Document,policy(),Axis::RunProperty,Default::default(),Default::default(),4)?;
    let owned=p.import_actual_forms(s.head,4)?.into_font_candidate(&p,query(&n),Scope::Document,policy(),Axis::RunProperty,Default::default(),Default::default(),4)?;
    let product=prepare!(&p,&request(&s,&bytes)?)?;assert_eq!(borrowed.receipt(),owned.receipt());assert_eq!(borrowed.receipt(),&product.receipt().stored);
    borrowed.verify(&p,5)?;owned.verify(&p,5)?;assert_eq!(borrowed.with_verified_bytes(&p,5,ContentDigest::of)?,owned.with_verified_bytes(&p,5,ContentDigest::of)?);Ok(())
}
#[test]
fn malformed_unknown_missing_and_enum_object_json_reject_before_artifact_reads()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();
    for key in ["schema_version","idempotency_key","plan_id","project_id","document_id","base_revision","expected_head_generation","expected_source_package_sha256","selector","operation"]{
        let mut v=good.clone();v.as_object_mut().ok_or("object")?.remove(key);assert!(matches!(prepare!(&p,&v),Err(E::Request)));}
    for(key,value)in [("style_filter",json!({})),("preview_only",json!(true)),("unknown",json!(0)),("axis",json!({"run_property":null})),("kind",json!({"replace_fonts":null})),("languages",json!([{"hangul":null}]))]{
        let mut v=good.clone();v["operation"][key]=value;assert!(matches!(prepare!(&p,&v),Err(E::Request)));}
    let mut v=good;v["selector"]["scope"]=json!({"document":null});assert!(matches!(prepare!(&p,&v),Err(E::Request)));assert_eq!(before,s.metadata.audit_events()?.len());Ok(())
}
#[test]
fn duplicate_escaped_nested_keys_trailing_json_and_size_limits_reject_before_reads()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=serde_json::to_string(&request(&s,&bytes)?)?;let before=s.metadata.audit_events()?.len();
    for raw in ["null".to_owned(),"[]".to_owned(),format!("{good} {{}}"),format!("{{\"schema_version\":\"bad\",{}",&good[1..]),
        good.replace("\"regex\":false","\"regex\":false,\"reg\\u0065x\":true"),good.replace("\"include_memo_bodies\":false","\"include_memo_bodies\":false,\"include_memo_bodies\":true")]{
        assert!(matches!(Product::prepare_json(&p,raw.as_bytes(),Default::default(),Default::default(),4),Err(E::Request)));}
    assert!(matches!(Product::prepare_json(&p,&vec![b' ';16385],Default::default(),Default::default(),4),Err(E::Limit)));assert_eq!(before,s.metadata.audit_events()?.len());Ok(())
}
#[test]
fn request_maximum_and_tighter_server_scalar_limit_are_both_enforced()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes)?;
    let mut v=good.clone();v["operation"]["max_changed_scalars"]=json!(1);assert!(matches!(prepare!(&p,&v),Err(E::Stored(Stored::Output(SourceError::Compile(Compile::Limit))))));
    let limits=SourceSearchLimits::new(Config{matches:1,..Default::default()})?;assert!(Product::prepare_json(&p,&wire(&good)?,limits,Default::default(),4).is_err());
    v["operation"]["max_changed_scalars"]=json!(3);assert_eq!(prepare!(&p,&v)?.receipt().stored.output.changed_source_scalars,3);
    let writer=WriterLimits::new(WriterLimitConfig{max_output_bytes:1})?;
    assert!(matches!(Product::prepare_json(&p,&wire(&v)?,Default::default(),writer,4),Err(E::Stored(Stored::Output(SourceError::Compile(Compile::Writer))))));Ok(())
}
#[test]
fn query_budget_rejects_before_reads_and_pattern_budget_rejects_inside_authorized_source()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();
    assert!(matches!(Product::prepare_json(&p,&wire(&v)?,SourceSearchLimits::new(Config{query_bytes:1,..Default::default()})?,Default::default(),4),Err(E::Limit)));assert_eq!(before,s.metadata.audit_events()?.len());
    v["operation"]["regex"]=json!(true);v["operation"]["query"]=json!(".+");
    assert!(Product::prepare_json(&p,&wire(&v)?,SourceSearchLimits::new(Config{pattern_bytes:1,..Default::default()})?,Default::default(),4).is_err());Ok(())
}
#[test]
fn key_plan_and_json_order_bind_receipts_without_becoming_execution_authority()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes)?;let out=prepare!(&p,&good)?;
    for(key,value)in [("idempotency_key",json!("OTHER-KEY")),("plan_id",json!("other-plan"))]{let mut v=good.clone();v[key]=value;let other=prepare!(&p,&v)?;
        assert_ne!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);assert_ne!(out.receipt().scoped_request_sha256,other.receipt().scoped_request_sha256);assert_eq!(out.receipt().stored.output.output_package_sha256,other.receipt().stored.output.output_package_sha256);}
    let mut bytes=wire(&good)?;bytes.insert(0,b' ');let other=Product::prepare_json(&p,&bytes,Default::default(),Default::default(),4)?;
    assert_ne!(out.receipt().raw_request_sha256,other.receipt().raw_request_sha256);assert_eq!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);Ok(())
}
#[test]
fn current_write_scope_is_required_for_preparation_and_retained_delivery()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=request(&s,&bytes)?;let reader=s.provider()?;assert!(prepare!(&reader,&v).is_err());
    let source=reader.import_actual_forms(s.head,4)?;let n=name(&bytes,0)?;assert!(matches!(source.prepare_font_candidate(&reader,query(&n),Scope::Document,policy(),Axis::RunProperty,Default::default(),Default::default(),4),Err(Stored::Permission)));
    let out=prepare!(&p,&v)?;let called=Cell::new(false);assert!(out.with_verified_bytes(&reader,5,|_|called.set(true)).is_err());assert!(!called.get());Ok(())
}
#[test]
fn five_foreign_provider_scopes_cannot_reuse_a_prepared_product()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let out=prepare!(&p,&request(&s,&bytes)?)?;let called=Cell::new(false);
    for mode in 0..5{let tenant=if mode==4{TenantId::new(Uuid::from_u128(998))?}else{s.reader.tenant_id()};let subject=if mode==3{SubjectDigest::from_authenticated_subject("foreign-font")?}else{s.reader.subject()};
        let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);let context=rev::RevisionRequestContext::new(tenant,subject);
        let project=if mode==2{rev::ProjectId::parse("prj_70000000000000000000000000000002")?}else{s.project};let branch=if mode==1{rev::BranchId::parse("brn_70000000000000000000000000000002")?}else{s.branch};
        let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&context,project,branch,DocumentId::parse(if mode==0{"foreign-document"}else{"actual-form-document"})?)?;
        assert!(out.verify(&other,5).is_err());assert!(out.with_verified_bytes(&other,5,|_|called.set(true)).is_err());}assert!(!called.get());Ok(())
}
#[test]
fn acl_revocation_blocks_new_and_retained_candidates_and_regrant_rechecks_current_access()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=request(&s,&bytes)?;let out=prepare!(&p,&v)?;
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;let called=Cell::new(false);assert!(prepare!(&p,&v).is_err());assert!(out.verify(&p,6).is_err());assert!(out.with_verified_bytes(&p,6,|_|called.set(true)).is_err());assert!(!called.get());
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;out.verify(&p,8)?;out.with_verified_bytes(&p,8,|_|())?;Ok(())
}
#[test]
fn quarantine_blocks_new_and_retained_candidates_without_consumer_calls()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=request(&s,&bytes)?;let out=prepare!(&p,&v)?;
    s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("FONT_TEST")?,5)?;let called=Cell::new(false);assert!(prepare!(&p,&v).is_err());assert!(out.verify(&p,6).is_err());assert!(out.with_verified_bytes(&p,6,|_|called.set(true)).is_err());assert!(!called.get());Ok(())
}
#[test]
fn ciphertext_tamper_blocks_new_and_retained_candidates_without_consumer_calls()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=request(&s,&bytes)?;let out=prepare!(&p,&v)?;
    s.blobs.tamper.store(true,Ordering::SeqCst);let called=Cell::new(false);assert!(prepare!(&p,&v).is_err());assert!(out.verify(&p,6).is_err());assert!(out.with_verified_bytes(&p,6,|_|called.set(true)).is_err());assert!(!called.get());Ok(())
}
struct BoundaryRepo{inner:rev::InMemoryRevisionRepository,calls:AtomicUsize,trigger:AtomicUsize,context:rev::RevisionRequestContext,advance:rev::RevisionCommitRequest}
impl rev::RevisionRepository for BoundaryRepo{
    fn compare_and_swap(&self,c:&rev::RevisionRequestContext,r:&rev::RevisionCommitRequest)->Result<rev::CommitOutcome,rev::RevisionError>{self.inner.compare_and_swap(c,r)}
    fn head(&self,t:TenantId,p:rev::ProjectId,b:rev::BranchId)->Result<rev::RevisionHead,rev::RevisionError>{let n=self.calls.fetch_add(1,Ordering::SeqCst)+1;
        if n==self.trigger.load(Ordering::SeqCst){assert!(matches!(self.inner.compare_and_swap(&self.context,&self.advance)?,rev::CommitOutcome::Committed(_)));}self.inner.head(t,p,b)}
    fn node(&self,t:TenantId,p:rev::ProjectId,r:rev::RevisionId)->Result<rev::RevisionNode,rev::RevisionError>{self.inner.node(t,p,r)}
}
fn race(stage:usize)->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=request(&s,&bytes)?;let out=prepare!(&p,&v)?;
    let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,
        ContentDigest::of(b"font-race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation fixture"),ContentDigest::of(b"transaction fixture"))?;
    let repo=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
    let bound=StoredFormProvider::bind(&s.artifacts,&repo,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
    match stage{0=>{Product::prepare_json(&bound,&wire(&v)?,Default::default(),Default::default(),5)?;},1=>{out.verify(&bound,5)?;},_=>{out.with_verified_bytes(&bound,5,|_|())?;}}
    let calls=repo.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);repo.repository().calls.store(0,Ordering::SeqCst);repo.repository().trigger.store(calls,Ordering::SeqCst);let called=Cell::new(false);
    match stage{0=>assert!(Product::prepare_json(&bound,&wire(&v)?,Default::default(),Default::default(),6).is_err()),1=>assert!(out.verify(&bound,6).is_err()),_=>assert!(out.with_verified_bytes(&bound,6,|_|called.set(true)).is_err())}
    assert!(!called.get());assert_eq!(repo.repository().calls.load(Ordering::SeqCst),calls);Ok(())
}
#[test]fn final_head_race_during_preparation_rejects()->R{race(0)}
#[test]fn final_head_race_during_retained_verification_rejects()->R{race(1)}
#[test]fn final_head_race_inside_delivery_blocks_consumer()->R{race(2)}
#[test]
fn source_hash_revision_and_generation_must_match_the_current_sealed_source()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes)?;
    for(key,value)in [("expected_source_package_sha256",json!("0".repeat(64))),("expected_head_generation",json!(s.head.generation()+1)),("base_revision",json!(rev::RevisionId::generate().public_id()))]{let mut v=good.clone();v[key]=value;assert!(prepare!(&p,&v).is_err());}Ok(())
}
#[test]
fn legacy_schema_full_options_and_foreign_selector_shape_reject_before_reads()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();
    for schema in ["hwpx-agent.product-width-conversion-request/v1","hwpx-agent.product-literal-replacement-request/v1","hwpx-agent.product-source-search-request/v6"]{let mut v=good.clone();v["schema_version"]=json!(schema);assert!(matches!(prepare!(&p,&v),Err(E::Request)));}
    for range in [json!({"node_ids":[]}),json!({"foo":1}),json!({"index_sha256":"0".repeat(64)})]{let mut v=good.clone();v["selector"]["scope"]=json!("selection");v["selector"]["range"]=range;assert!(matches!(prepare!(&p,&v),Err(E::Request)));}
    assert_eq!(before,s.metadata.audit_events()?.len());Ok(())
}
#[test]
fn redacted_receipts_and_denied_route_leave_original_head_and_ingest_count_unchanged()->R{
    let bytes=raw("PRIVATE-SOURCE")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let out=prepare!(&p,&request(&s,&bytes)?)?;
    for text in [format!("{out:?}{:?}",out.receipt()),serde_json::to_string(out.receipt())?]{assert!(!text.contains("PRIVATE-FONT")&&!text.contains("PRIVATE-SOURCE"));}
    assert!(matches!(out.require_current_product_route(&p,5),Err(E::RouteUnqualified)));assert!(!out.receipt().idempotency_key_claimed&&!out.receipt().full_font_native_cas_execution_publication_authority);
    assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
}
#[test]
fn cached_field_text_is_not_silently_restyled()->R{
    let bytes=package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:ctrl><hp:fieldBegin id='17' type='DATE'/></hp:ctrl><hp:t>CACHE</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='17'/></hp:ctrl></hp:run></hp:p>")?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=request(&s,&bytes)?;
    assert!(matches!(prepare!(&p,&v),Err(E::Stored(Stored::Output(SourceError::Compile(Compile::FieldContent))))));Ok(())
}
#[test]
fn invalid_regex_missing_target_and_no_name_matches_produce_no_partial_result()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes)?;
    for(key,value)in [("query",json!("P09-NOT-DECLARED")),("replacement",json!("P09-MISSING-TARGET"))]{let mut v=good.clone();v["operation"][key]=value;assert!(prepare!(&p,&v).is_err());}
    let mut v=good;v["operation"]["regex"]=json!(true);v["operation"]["query"]=json!("[");assert!(prepare!(&p,&v).is_err());Ok(())
}
#[test]
fn language_and_policy_changes_bind_both_product_request_and_source_operation()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes)?;let first=prepare!(&p,&good)?;
    for(key,value)in [("languages",json!(["hangul"])),("review_policy",json!({"include_hidden_explanations":true,"include_memo_bodies":true})),("case_sensitive",json!(false))]{
        let mut v=good.clone();v["operation"][key]=value;let other=prepare!(&p,&v)?;assert_ne!(first.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);assert_ne!(first.receipt().stored.output.request_sha256,other.receipt().stored.output.request_sha256);}
    Ok(())
}
#[path="support/scoped_font_edit_inventory.rs"]mod edit_inventory_v1;
#[path="support/scoped_font_compiled.rs"]mod compiled_font_v1;
#[path="support/scoped_font_review.rs"]mod font_review_v1;
#[path="support/scoped_font_options.rs"]mod font_options_v2;
#[path="support/scoped_font_options_compiled.rs"]mod compiled_font_v2;
