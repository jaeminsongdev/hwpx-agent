//! Focused named-style service/product tests; existing synthetic fixture, no operational DB/Native.
use std::{error::Error,cell::Cell,sync::atomic::AtomicUsize};
use domain_ir::DocumentId;
use serde_json::{json,Value};
use revision_service as rev;
use hwpx_agent_cli::form_product_request::stored_literal_replacement::named_styles::{StoredNamedStyleProductRequest as Product,
    NamedStyleProductError as E,NAMED_STYLE_PRODUCT_REQUEST_SCHEMA as SCHEMA};
use hwpx_agent_cli::form_stored_provider::actual_import::literal_search_output::named_styles::StoredNamedStyleError as Stored;
use hwpx_package::{PreservingXmlDocument,WriterLimits,WriterLimitConfig,document_import::search::{SourceSearchLimits,SourceSearchLimitConfig as Config,
    selector::SourceIndexScopeSelector as Scope,reviews::SourceReviewTextPolicy as Policy,replacement::{SourceLiteralReplacementError as Compile,
        atoms::styles::paragraphs::{SourceParagraphStyleReplacementError as Paragraph,named::{SourceNamedParagraphStyleQuery as Query,
            SourceStyleNameAxis as Axis,SourceNamedParagraphStyleError as Core}}}}};
include!("support/stored_source_fixture.rs");
#[path="../../hwpx-package/tests/support/search_definition_fixture.rs"]#[allow(dead_code)]mod definition;
#[path="../../hwpx-package/tests/support/document_import_catalog_fixture.rs"]#[allow(dead_code)]mod archive;
#[path="../../hwpx-package/tests/support/review_scope_fixture.rs"]#[allow(dead_code)]mod review;
type R=Result<(),Box<dyn Error>>;
fn policy()->Policy{Policy{include_hidden_explanations:false,include_memo_bodies:false}}
fn para(id:u32,style:u32,text:&str)->String{format!("<hp:p id='{id}' paraPrIDRef='0' styleIDRef='{style}'><hp:run charPrIDRef='0'><hp:t>{text}</hp:t></hp:run></hp:p>")}
fn package(body:&str)->Result<Vec<u8>,Box<dyn Error>>{
    archive::mutate_part(&definition::package(body)?,"Contents/header.xml",|text|{
        let xml=PreservingXmlDocument::parse(text.as_bytes())?;let mut edits=Vec::new();
        for n in xml.elements().iter().filter(|n|n.name().local_name()=="style"){
            let id=n.attributes().iter().find(|a|a.name().local_name()=="id").map(|a|&text[a.value_span().start()..a.value_span().end()]);
            let pair=match id{Some("0")=>Some(("원본 문단 A","SRC First")),Some("1")=>Some(("원본 문단 B","SRC Second")),Some("2")=>Some(("대상 문단","DST")),_=>None};
            if let Some((native,english))=pair{for a in n.attributes(){let value=match a.name().local_name(){"name"=>Some(native),"engName"=>Some(english),_=>None};
                if let Some(value)=value{edits.push((a.value_span().start(),a.value_span().end(),value));}}}
        }edits.sort_by_key(|e|e.0);let mut out=text.to_owned();for(a,b,v)in edits.into_iter().rev(){out.replace_range(a..b,v);}Ok(out)
    })
}
fn raw(text:&str)->Result<Vec<u8>,Box<dyn Error>>{package(&para(1,0,text))}
fn query()->Query<'static>{Query{query:"SRC",replacement:"DST",regex:false,case_sensitive:true,whole_word:false,name_axis:Axis::EnglishName}}
fn wire(v:&Value)->Result<Vec<u8>,serde_json::Error>{serde_json::to_vec(v)}
fn request(s:&StoredFixture,bytes:&[u8],preview:bool)->Result<Value,Box<dyn Error>>{
    let revision=s.head.revision_id().ok_or("head")?.public_id();
    Ok(json!({"schema_version":SCHEMA,"idempotency_key":"PRIVATE-NAMED-KEY","plan_id":"named-style-plan","project_id":s.project.public_id(),"document_id":"actual-form-document",
        "base_revision":revision,"expected_head_generation":s.head.generation(),"expected_source_package_sha256":ContentDigest::of(bytes).hex(),"selector":{"revision_id":revision,"scope":"document"},
        "operation":{"kind":"replace_named_paragraph_styles","query":"SRC","replacement":"DST","regex":false,"case_sensitive":true,"whole_word":false,"name_axis":"english_name",
            "max_changed_paragraphs":100,"review_policy":policy(),"preview_only":preview}}))
}
fn refs(bytes:&[u8])->Result<Vec<(u32,Option<u32>,Option<u32>)>,Box<dyn Error>>{
    let bytes=archive::read_part(bytes,"Contents/section0.xml")?;let text=std::str::from_utf8(&bytes)?;let xml=PreservingXmlDocument::parse(&bytes)?;let mut out=Vec::new();
    for p in xml.elements().iter().filter(|p|p.name().local_name()=="p"){
        let get=|name:&str|->Result<Option<u32>,Box<dyn Error>>{p.attributes().iter().find(|a|a.name().local_name()==name).map(|a|{let span=a.value_span();Ok(text[span.start()..span.end()].parse()?)}).transpose()};
        out.push((get("id")?.ok_or("id")?,get("paraPrIDRef")?,get("styleIDRef")?));
    }Ok(out)
}
macro_rules! writer{($s:ident,$actor:ident,$p:ident)=>{
    let $actor=RequestContext::new($s.reader.tenant_id(),$s.reader.subject(),[AuthScope::DocumentRead,AuthScope::DocumentWrite]);
    let $p=StoredFormProvider::bind(&$s.artifacts,&$s.revisions,&$actor,&$s.revision_context,$s.project,$s.branch,DocumentId::parse("actual-form-document")?)?;
}}
macro_rules! prepare{($p:expr,$v:expr)=>{Product::prepare_json($p,&wire($v)?,Default::default(),Default::default(),4)}}
fn inventory(p:&Provider<'_>,v:&Value)->Result<Value,Box<dyn Error>>{
    use hwpx_agent_cli::form_product_request::stored_source_search::selector::review::StoredReviewScopeProductRequest;
    let mut v=v.clone();v["schema_version"]=json!("hwpx-agent.product-source-search-request/v6");v["operation"]=json!({"kind":"scope_inventory"});
    Ok(StoredReviewScopeProductRequest::prepare_json(p,&wire(&v)?,Default::default(),4)?.with_verified_json(p,5,|b|serde_json::from_slice::<Value>(b))??)
}
fn selection(inv:&Value,start:usize,end:usize)->Result<Value,Box<dyn Error>>{
    let b=&inv["inventory"]["blocks"][0];let sha:[u8;32]=serde_json::from_value(inv["inventory"]["index"]["index_sha256"].clone())?;
    Ok(json!({"coordinate_space":"index_nfc_unicode_scalars","index_sha256":hex::encode(sha),"start":{"paragraph_handle":b["paragraph_handle"],"block_index":b["block_index"],"normalized_scalar":start},
        "end":{"paragraph_handle":b["paragraph_handle"],"block_index":b["block_index"],"normalized_scalar":end}}))
}
#[test]
fn owned_product_changes_two_named_uses_and_preserves_header_and_direct_properties()->R{
    let bytes=package(&(para(1,0,"A&amp;B")+&para(2,1,"각")+&para(3,2,"KEEP")))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    let v=request(&s,&bytes,false)?;let out=prepare!(&p,&v)?;drop(v);out.verify(&p,5)?;let output=out.with_verified_bytes(&p,5,<[u8]>::to_vec)?;
    assert_eq!(refs(&output)?,vec![(1,Some(0),Some(2)),(2,Some(0),Some(2)),(3,Some(0),Some(2))]);assert_eq!(archive::read_part(&bytes,"Contents/header.xml")?,archive::read_part(&output,"Contents/header.xml")?);
    assert_eq!(out.receipt().capability_id,"search.replace_styles");assert_eq!(out.receipt().stored.output.changes.len(),2);Ok(())
}
#[test]
fn borrowed_owned_and_product_share_original_named_candidate_receipt_and_output()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let source=p.import_actual_forms(s.head,4)?;
    let a=source.prepare_named_style_candidate(&p,query(),Scope::Document,policy(),Default::default(),Default::default(),4)?;
    let b=p.import_actual_forms(s.head,4)?.into_named_style_candidate(&p,query(),Scope::Document,policy(),Default::default(),Default::default(),4)?;
    let product=prepare!(&p,&request(&s,&bytes,false)?)?;assert_eq!(a.receipt(),b.receipt());assert_eq!(a.receipt(),&product.receipt().stored);
    assert_eq!(a.with_verified_bytes(&p,5,ContentDigest::of)?,b.with_verified_bytes(&p,5,ContentDigest::of)?);a.verify(&p,5)?;b.verify(&p,5)?;
    assert!(matches!(a.require_current_product_route(&p,5),Err(Stored::RouteUnqualified)));let preview=b.into_preview();assert!(preview.verify(&p,5)?.preview_only);assert!(!preview.receipt().candidate_output_retained);Ok(())
}
#[test]
fn preview_predicts_same_result_but_discards_output_and_never_calls_byte_consumer()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mutation=prepare!(&p,&request(&s,&bytes,false)?)?;let preview=prepare!(&p,&request(&s,&bytes,true)?)?;
    assert_eq!(mutation.receipt().stored.output,preview.receipt().stored.output);assert_ne!(mutation.receipt().canonical_request_sha256,preview.receipt().canonical_request_sha256);
    assert!(preview.receipt().preview_only&&!preview.receipt().stored.candidate_output_retained);let called=Cell::new(false);
    assert!(matches!(preview.with_verified_bytes(&p,5,|_|called.set(true)),Err(E::PreviewOnly)));assert!(!called.get());
    let metadata=preview.with_verified_json(&p,5,|b|serde_json::from_slice::<Value>(b))??;assert_eq!(metadata["preview_only"],true);assert_eq!(metadata["stored"]["candidate_output_retained"],false);
    assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);assert_eq!(s.artifacts.download(&s.reader,s.result,5)?,bytes);Ok(())
}
#[test]
fn all_three_admitted_empty_shapes_are_counted_as_paragraphs_in_both_modes()->R{
    let bytes=package("<hp:p id='1' styleIDRef='0' paraPrIDRef='0'><hp:run charPrIDRef='0'/></hp:p><hp:p id='2' styleIDRef='1' paraPrIDRef='0'><hp:run charPrIDRef='0'><hp:t></hp:t></hp:run></hp:p><hp:p id='3' styleIDRef='0' paraPrIDRef='0'><hp:run charPrIDRef='0'><hp:t/></hp:run></hp:p>")?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    for preview in [false,true]{let out=prepare!(&p,&request(&s,&bytes,preview)?)?;out.verify(&p,5)?;assert_eq!(out.receipt().stored.output.matched_paragraphs,3);
        if !preview{assert!(out.with_verified_bytes(&p,5,refs)??.iter().all(|p|p.2==Some(2)));}}Ok(())
}
#[test]
fn empty_selection_and_runless_source_never_become_full_paragraph_preview_authority()->R{
    let bytes=package("<hp:p id='1' styleIDRef='0' paraPrIDRef='0'><hp:run charPrIDRef='0'/></hp:p>")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes,true)?;let inv=inventory(&p,&good)?;
    let mut v=good;v["selector"]["scope"]=json!("selection");v["selector"]["range"]=selection(&inv,0,0)?;assert!(matches!(prepare!(&p,&v),Err(E::Stored(Stored::Output(Core::Paragraph(Paragraph::IncompleteParagraphScope))))));
    let bytes=package("<hp:p id='1' styleIDRef='0' paraPrIDRef='0'/>")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    assert!(prepare!(&p,&request(&s,&bytes,true)?).is_err());Ok(())
}
#[test]
fn review_policy_reaches_hidden_and_memo_without_changing_cached_outer_paragraph()->R{
    let body=review::body().replace("<hp:p id='1'>","<hp:p id='1' styleIDRef='2' paraPrIDRef='0'>")
        .replace("<hp:p id='11'>","<hp:p id='11' styleIDRef='0' paraPrIDRef='0'>").replace("<hp:p id='12'>","<hp:p id='12' styleIDRef='1' paraPrIDRef='0'>");
    let bytes=package(&body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    for preview in [false,true]{for(h,m,count)in [(false,false,0),(true,false,1),(false,true,1),(true,true,2)]{
        let mut v=request(&s,&bytes,preview)?;v["operation"]["review_policy"]=json!({"include_hidden_explanations":h,"include_memo_bodies":m});let result=prepare!(&p,&v);
        if count==0{assert!(matches!(result,Err(E::Stored(Stored::Output(Core::NoMatches)))));continue;}let out=result?;assert_eq!(out.receipt().stored.output.changes.len(),count);
        if !preview{let output=out.with_verified_bytes(&p,5,<[u8]>::to_vec)?;assert_eq!(refs(&output)?[0].2,Some(2));let text=String::from_utf8(archive::read_part(&output,"Contents/section0.xml")?)?;assert!(text.contains("CACHE FROZEN")&&text.contains("PRIVATE-AUTHOR"));}
    }}Ok(())
}
#[test]
fn native_and_english_names_regex_case_and_word_options_reach_original_resolver()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes,false)?;
    for mode in 0..4{let mut v=good.clone();match mode{0=>{v["operation"]["name_axis"]=json!("native_name");v["operation"]["query"]=json!("원본 문단");v["operation"]["replacement"]=json!("대상 문단");},
        1=>{v["operation"]["regex"]=json!(true);v["operation"]["query"]=json!("^SRC (First|Second)$");},2=>{v["operation"]["query"]=json!("src");v["operation"]["case_sensitive"]=json!(false);},_=>v["operation"]["whole_word"]=json!(true)}
        assert_eq!(prepare!(&p,&v)?.receipt().stored.output.changes.len(),1);}Ok(())
}
#[test]
fn missing_ambiguous_character_target_invalid_regex_and_no_change_are_not_preview_success()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes,true)?;
    for target in ["NOT DECLARED","Page Number"]{let mut v=good.clone();v["operation"]["replacement"]=json!(target);assert!(matches!(prepare!(&p,&v),Err(E::Stored(Stored::Output(Core::MissingTarget)))));}
    let mut v=good.clone();v["operation"]["regex"]=json!(true);v["operation"]["query"]=json!("[");assert!(matches!(prepare!(&p,&v),Err(E::Stored(Stored::Output(Core::Pattern)))));
    let mut v=good;v["operation"]["query"]=json!("DST");assert!(matches!(prepare!(&p,&v),Err(E::Stored(Stored::Output(Core::NoChange)))));
    let bytes=archive::mutate_part(&bytes,"Contents/header.xml",|t|Ok(t.replace("SRC Second","DST")))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    assert!(matches!(prepare!(&p,&request(&s,&bytes,true)?),Err(E::Stored(Stored::Output(Core::AmbiguousTarget)))));Ok(())
}
#[test]
fn document_section_node_and_full_selection_do_not_widen_a_clipped_paragraph()->R{
    let bytes=package(&(para(1,0,"ABC")+&para(2,1,"DEF")))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes,false)?;let inv=inventory(&p,&good)?;
    let first=&inv["inventory"]["blocks"][0];let node=inv["inventory"]["nodes"].as_array().ok_or("nodes")?.iter().find(|n|n["source_handle"]==first["paragraph_handle"]).ok_or("node")?;
    for mode in 0..4{let mut v=good.clone();let count=match mode{0=>2,1=>{v["selector"]["scope"]=json!("section");v["selector"]["section_ids"]=inv["inventory"]["section_ids"].clone();2},
        2=>{v["selector"]["scope"]=json!("node_set");v["selector"]["range"]=json!({"node_ids":[node["node_id"]]});1},_=>{v["selector"]["scope"]=json!("selection");v["selector"]["range"]=selection(&inv,0,3)?;1}};
        assert_eq!(prepare!(&p,&v)?.receipt().stored.output.changes.len(),count);}
    let mut v=good;v["selector"]["scope"]=json!("selection");v["selector"]["range"]=selection(&inv,1,2)?;
    assert!(matches!(prepare!(&p,&v),Err(E::Stored(Stored::Output(Core::Paragraph(Paragraph::IncompleteParagraphScope))))));Ok(())
}
#[test]
fn required_root_fields_preview_flag_and_string_enum_shapes_reject_before_reads()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes,true)?;let before=s.metadata.audit_events()?.len();
    for key in ["schema_version","idempotency_key","project_id","document_id","base_revision","expected_head_generation","expected_source_package_sha256","plan_id","selector","operation"]{
        let mut v=good.clone();v.as_object_mut().ok_or("root")?.remove(key);assert!(matches!(prepare!(&p,&v),Err(E::Request)));}
    for key in ["preview_only","name_axis","review_policy","max_changed_paragraphs","replacement"]{let mut v=good.clone();v["operation"].as_object_mut().ok_or("op")?.remove(key);assert!(matches!(prepare!(&p,&v),Err(E::Request)));}
    for(key,value)in [("kind",json!({"replace_named_paragraph_styles":null})),("name_axis",json!({"english_name":null})),("preview_only",json!("true"))]{let mut v=good.clone();v["operation"][key]=value;assert!(matches!(prepare!(&p,&v),Err(E::Request)));}
    assert_eq!(before,s.metadata.audit_events()?.len());Ok(())
}
#[test]
fn unknown_filters_full_catalog_options_and_caller_approval_or_graph_data_are_rejected()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes,true)?;let before=s.metadata.audit_events()?.len();
    for key in ["style_filter","max_replacements","target_id","from_style_ids","approved","raw_xml","graph"]{let mut v=good.clone();v["operation"][key]=json!({});assert!(matches!(prepare!(&p,&v),Err(E::Request)));}
    for value in [Value::Null,json!(0),json!(false)]{let mut v=good.clone();v["selector"]["scope"]=value;assert!(matches!(prepare!(&p,&v),Err(E::Request)));}
    assert_eq!(before,s.metadata.audit_events()?.len());Ok(())
}
#[test]
fn duplicate_escaped_nested_keys_trailing_json_and_wrong_schema_reject_before_reads()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes,true)?;let text=serde_json::to_string(&good)?;let before=s.metadata.audit_events()?.len();
    for raw in [format!("{text} {{}}"),text.replace("\"preview_only\":true","\"preview_only\":true,\"preview_\\u006fnly\":false"),
        text.replace("\"english_name\"","\"english_name\",\"name_\\u0061xis\":\"native_name\""),"null".into(),"[]".into()]{
        assert!(matches!(Product::prepare_json(&p,raw.as_bytes(),Default::default(),Default::default(),4),Err(E::Request)));}
    let mut v=good;v["schema_version"]=json!("hwpx-agent.product-paragraph-style-replacement-request/v1");assert!(matches!(prepare!(&p,&v),Err(E::Request)));assert_eq!(before,s.metadata.audit_events()?.len());Ok(())
}
#[test]
fn exact_sixteen_kib_and_query_and_request_count_limits_reject_before_source_reads()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes,true)?;let mut padded=wire(&good)?;padded.resize(16384,b' ');
    Product::prepare_json(&p,&padded,Default::default(),Default::default(),4)?;let before=s.metadata.audit_events()?.len();padded.push(b' ');assert!(matches!(Product::prepare_json(&p,&padded,Default::default(),Default::default(),4),Err(E::Limit)));
    let limits=SourceSearchLimits::new(Config{query_bytes:1,..Default::default()})?;assert!(matches!(Product::prepare_json(&p,&wire(&good)?,limits,Default::default(),4),Err(E::Limit)));
    for count in [0,10001]{let mut v=good.clone();v["operation"]["max_changed_paragraphs"]=json!(count);assert!(matches!(prepare!(&p,&v),Err(E::Request)));}
    assert_eq!(before,s.metadata.audit_events()?.len());Ok(())
}
#[test]
fn request_server_and_writer_limits_apply_to_mutation_and_preview()->R{
    let bytes=package(&(para(1,0,"A")+&para(2,1,"B")))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    for preview in [false,true]{let mut v=request(&s,&bytes,preview)?;v["operation"]["max_changed_paragraphs"]=json!(1);assert!(matches!(prepare!(&p,&v),Err(E::Stored(Stored::Output(Core::Limit)))));
        v["operation"]["max_changed_paragraphs"]=json!(2);let limits=SourceSearchLimits::new(Config{matches:1,..Default::default()})?;assert!(matches!(Product::prepare_json(&p,&wire(&v)?,limits,Default::default(),4),Err(E::Stored(Stored::Output(Core::Limit)))));
        let writer=WriterLimits::new(WriterLimitConfig{max_output_bytes:1})?;assert!(matches!(Product::prepare_json(&p,&wire(&v)?,Default::default(),writer,4),Err(E::Stored(Stored::Output(Core::Compile(Compile::Writer))))));}Ok(())
}
#[test]
fn source_sha_revision_and_generation_are_required_for_both_modes()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    for preview in [false,true]{let good=request(&s,&bytes,preview)?;for(key,value)in [("expected_source_package_sha256",json!("0".repeat(64))),("expected_head_generation",json!(s.head.generation()+1)),("base_revision",json!(rev::RevisionId::generate().public_id()))]{let mut v=good.clone();v[key]=value;assert!(prepare!(&p,&v).is_err());}}Ok(())
}
#[test]
fn write_scope_is_required_for_preparation_and_retained_preview_metadata()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let reader=s.provider()?;
    let source=reader.import_actual_forms(s.head,4)?;assert!(matches!(source.prepare_named_style_candidate(&reader,query(),Scope::Document,policy(),Default::default(),Default::default(),4),Err(Stored::Permission)));
    for preview in [false,true]{let v=request(&s,&bytes,preview)?;assert!(prepare!(&reader,&v).is_err());let out=prepare!(&p,&v)?;let called=Cell::new(false);
        assert!(out.verify(&reader,5).is_err());assert!(out.with_verified_json(&reader,5,|_|called.set(true)).is_err());assert!(!called.get());}Ok(())
}
#[test]
fn five_foreign_provider_scopes_cannot_reuse_either_retained_result_mode()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    for preview in [false,true]{let out=prepare!(&p,&request(&s,&bytes,preview)?)?;let called=Cell::new(false);
        for mode in 0..5{let tenant=if mode==4{TenantId::new(Uuid::from_u128(998))?}else{s.reader.tenant_id()};let subject=if mode==3{SubjectDigest::from_authenticated_subject("foreign-named-style")?}else{s.reader.subject()};
            let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);let context=rev::RevisionRequestContext::new(tenant,subject);let project=if mode==2{rev::ProjectId::parse("prj_70000000000000000000000000000002")?}else{s.project};let branch=if mode==1{rev::BranchId::parse("brn_70000000000000000000000000000002")?}else{s.branch};
            let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&context,project,branch,DocumentId::parse(if mode==0{"foreign-document"}else{"actual-form-document"})?)?;
            assert!(out.verify(&other,5).is_err());assert!(out.with_verified_json(&other,5,|_|called.set(true)).is_err());}assert!(!called.get());}Ok(())
}
#[test]
fn acl_revocation_blocks_new_and_retained_results_and_regrant_rechecks()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mutation=prepare!(&p,&request(&s,&bytes,false)?)?;let preview=prepare!(&p,&request(&s,&bytes,true)?)?;
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;let called=Cell::new(false);
    for out in [&mutation,&preview]{assert!(out.verify(&p,6).is_err());assert!(out.with_verified_json(&p,6,|_|called.set(true)).is_err());}assert!(prepare!(&p,&request(&s,&bytes,true)?).is_err());assert!(!called.get());
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;mutation.verify(&p,8)?;preview.verify(&p,8)?;Ok(())
}
#[test]
fn quarantine_blocks_both_new_and_retained_result_modes_without_callbacks()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let a=prepare!(&p,&request(&s,&bytes,false)?)?;let b=prepare!(&p,&request(&s,&bytes,true)?)?;
    s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("NAMED_STYLE_TEST")?,5)?;let called=Cell::new(false);
    for out in [&a,&b]{assert!(out.verify(&p,6).is_err());assert!(out.with_verified_json(&p,6,|_|called.set(true)).is_err());}assert!(prepare!(&p,&request(&s,&bytes,true)?).is_err());assert!(!called.get());Ok(())
}
#[test]
fn ciphertext_tamper_blocks_new_and_retained_results_without_metadata_or_bytes()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let a=prepare!(&p,&request(&s,&bytes,false)?)?;let b=prepare!(&p,&request(&s,&bytes,true)?)?;
    s.blobs.tamper.store(true,Ordering::SeqCst);let called=Cell::new(false);for out in [&a,&b]{assert!(out.verify(&p,6).is_err());assert!(out.with_verified_json(&p,6,|_|called.set(true)).is_err());}
    assert!(a.with_verified_bytes(&p,6,|_|called.set(true)).is_err());assert!(!called.get());assert!(prepare!(&p,&request(&s,&bytes,true)?).is_err());Ok(())
}
#[test]
fn cached_fields_and_zero_tracking_still_block_both_preparation_modes()->R{
    let field=para(1,0,"A</hp:t><hp:ctrl><hp:fieldBegin id='17' type='DATE'/></hp:ctrl><hp:t>CACHE</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='17'/></hp:ctrl><hp:t>TAIL");let tracked=para(1,0,"A").replace("id='1'","id='1' paraTcId='0'");
    for body in [field,tracked]{let bytes=package(&body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);for preview in [false,true]{
        assert!(matches!(prepare!(&p,&request(&s,&bytes,preview)?),Err(E::Stored(Stored::Output(Core::Paragraph(Paragraph::Compile(Compile::FieldContent|Compile::Protection)))))));}}Ok(())
}
#[test]
fn names_axes_policy_plan_and_key_bind_requests_without_leaking_private_values()->R{
    let bytes=raw("PRIVATE-NAMED-BODY")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let good=request(&s,&bytes,true)?;let first=prepare!(&p,&good)?;
    for root in [false,true]{let mut v=good.clone();if root{v["plan_id"]=json!("named-style-plan-2");}else{v["operation"]["query"]=json!("SRC First");}let out=prepare!(&p,&v)?;
        assert_ne!(first.receipt().canonical_request_sha256,out.receipt().canonical_request_sha256);assert_eq!(first.receipt().stored.output.output_package_sha256,out.receipt().stored.output.output_package_sha256);}
    let mut v=good;v["idempotency_key"]=json!("PRIVATE-SECOND-KEY");assert_ne!(first.receipt().canonical_request_sha256,prepare!(&p,&v)?.receipt().canonical_request_sha256);
    for text in [format!("{first:?}{:?}",first.receipt()),first.with_verified_json(&p,5,|b|String::from_utf8_lossy(b).into_owned())?]{assert!(!text.contains("PRIVATE-")&&!text.contains("SRC First")&&!text.contains("DST"));}Ok(())
}
#[test]
fn retained_results_never_claim_key_ingest_commit_or_qualified_route()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);for preview in [false,true]{let out=prepare!(&p,&request(&s,&bytes,preview)?)?;
        assert!(matches!(out.require_current_product_route(&p,5),Err(E::RouteUnqualified)));assert!(!out.receipt().idempotency_key_claimed&&!out.receipt().full_style_native_cas_execution_publication_authority);}
    assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
}
struct BoundaryRepo{inner:rev::InMemoryRevisionRepository,calls:AtomicUsize,trigger:AtomicUsize,context:rev::RevisionRequestContext,advance:rev::RevisionCommitRequest}
impl rev::RevisionRepository for BoundaryRepo{
    fn compare_and_swap(&self,c:&rev::RevisionRequestContext,r:&rev::RevisionCommitRequest)->Result<rev::CommitOutcome,rev::RevisionError>{self.inner.compare_and_swap(c,r)}
    fn head(&self,t:TenantId,p:rev::ProjectId,b:rev::BranchId)->Result<rev::RevisionHead,rev::RevisionError>{let n=self.calls.fetch_add(1,Ordering::SeqCst)+1;
        if n==self.trigger.load(Ordering::SeqCst){assert!(matches!(self.inner.compare_and_swap(&self.context,&self.advance)?,rev::CommitOutcome::Committed(_)));}self.inner.head(t,p,b)}
    fn node(&self,t:TenantId,p:rev::ProjectId,r:rev::RevisionId)->Result<rev::RevisionNode,rev::RevisionError>{self.inner.node(t,p,r)}
}
fn race(preview:bool,stage:usize)->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=request(&s,&bytes,preview)?;let out=prepare!(&p,&v)?;
    let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,
        ContentDigest::of(b"named-style-race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation fixture"),ContentDigest::of(b"transaction fixture"))?;
    let repo=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
    let bound=StoredFormProvider::bind(&s.artifacts,&repo,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
    match stage{0=>{Product::prepare_json(&bound,&wire(&v)?,Default::default(),Default::default(),5)?;},1=>{out.verify(&bound,5)?;},_=>{out.with_verified_json(&bound,5,|_|())?;}}
    let count=repo.repository().calls.load(Ordering::SeqCst);assert!(count>=4);repo.repository().calls.store(0,Ordering::SeqCst);repo.repository().trigger.store(count,Ordering::SeqCst);let called=Cell::new(false);
    match stage{0=>assert!(Product::prepare_json(&bound,&wire(&v)?,Default::default(),Default::default(),6).is_err()),1=>assert!(out.verify(&bound,6).is_err()),_=>assert!(out.with_verified_json(&bound,6,|_|called.set(true)).is_err())}
    assert!(!called.get());assert_eq!(repo.repository().calls.load(Ordering::SeqCst),count);Ok(())
}
#[test]fn mutation_preparation_final_head_race_rejects()->R{race(false,0)}
#[test]fn mutation_verification_final_head_race_rejects()->R{race(false,1)}
#[test]fn mutation_metadata_delivery_final_head_race_blocks_consumer()->R{race(false,2)}
#[test]fn preview_preparation_final_head_race_rejects()->R{race(true,0)}
#[test]fn preview_verification_final_head_race_rejects()->R{race(true,1)}
#[test]fn preview_metadata_delivery_final_head_race_blocks_consumer()->R{race(true,2)}
// Named metadata server-budget boundary cases begin.
#[test]
fn large_named_metadata_over_sixty_four_kib_keeps_all_changes_and_respects_server_budget()->R{
    use hwpx_agent_cli::form_product_request::stored_literal_replacement::named_styles::NAMED_STYLE_PRODUCT_MAX_METADATA_BYTES;
    let mut body=String::new();for id in 1..=384{body.push_str(&para(id,id%2,"X"));}let bytes=package(&body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    for preview in [false,true]{let mut v=request(&s,&bytes,preview)?;v["operation"]["max_changed_paragraphs"]=json!(384);let out=prepare!(&p,&v)?;
        let metadata=out.with_verified_json(&p,5,<[u8]>::to_vec)?;assert!(metadata.len()>64*1024&&metadata.len()<=NAMED_STYLE_PRODUCT_MAX_METADATA_BYTES);
        let parsed:Value=serde_json::from_slice(&metadata)?;assert_eq!(parsed["stored"]["output"]["changes"].as_array().ok_or("changes")?.len(),384);
        assert_eq!(out.receipt().stored.output.matched_paragraphs,384);assert_eq!(out.receipt().stored.output.observed_protection_parts,1);
        if !preview{assert_eq!(out.with_verified_bytes(&p,5,refs)??.iter().filter(|p|p.2==Some(2)).count(),384);}}
    assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);Ok(())
}
#[test]
fn exact_server_metadata_envelope_limit_and_one_byte_less_are_enforced()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    for preview in [false,true]{let v=request(&s,&bytes,preview)?;let baseline=prepare!(&p,&v)?;let length=baseline.with_verified_json(&p,5,<[u8]>::len)?;
        let exact=SourceSearchLimits::new(Config{result_bytes:length,..Default::default()})?;assert_eq!(exact.maximum_result_bytes(),length);
        let out=Product::prepare_json(&p,&wire(&v)?,exact,Default::default(),4)?;assert_eq!(out.with_verified_json(&p,5,<[u8]>::len)?,length);
        let smaller=SourceSearchLimits::new(Config{result_bytes:length-1,..Default::default()})?;
        assert!(matches!(Product::prepare_json(&p,&wire(&v)?,smaller,Default::default(),4),Err(E::Limit)));}Ok(())
}
// Named metadata server-budget boundary cases end.
#[path="support/named_style_compiled.rs"]mod compiled_named;
#[path="support/named_style_options_product.rs"]mod named_options;
