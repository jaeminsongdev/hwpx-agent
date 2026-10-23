//! Exact control candidates through current access and typed JSON, not full control transactions.
use super::*;
use hwpx_agent_cli::form_product_request::stored_literal_replacement::controls::{StoredControlProductRequest as ControlProduct,
    ControlProductError as PE,CONTROL_PRODUCT_REQUEST_SCHEMA as CONTROL_SCHEMA};
use hwpx_agent_cli::form_stored_provider::actual_import::literal_search_output::controls::StoredControlError as SE;
use hwpx_package::{TextAtom,document_import::search::{SourceSearchError as Search,inspection::SourceControlKind as ControlKind,
    replacement::atoms::controls::{ValidatedTextControlOutput,SourceControlReplacementError as Core}}};
macro_rules! control_prepare{($p:expr,$v:expr)=>{ControlProduct::prepare_json($p,&wire($v)?,Default::default(),Default::default(),4)}}
fn tx(value:&str)->Value{json!({"kind":"text","value":value})}
fn control_request(s:&StoredFixture,bytes:&[u8])->Result<Value,Box<dyn Error>>{let mut v=request(s,bytes)?;v["schema_version"]=json!(CONTROL_SCHEMA);
    v["operation"]=json!({"kind":"replace_text_controls","control_kind":"tab","max_replacements":100,"output":[tx("X")],"review_policy":policy(true,true)});Ok(v)}
fn exact_control(source:&[u8],out:&[u8],old:&str,new:&str)->TestResult{
    assert_eq!(section(out)?,section(source)?.replace(old,new));let mut a=hwpx_package::BoundedZipReader::open(Cursor::new(source),Default::default())?;
    let mut b=hwpx_package::BoundedZipReader::open(Cursor::new(out),Default::default())?;assert_eq!(a.entries().len(),b.entries().len());
    for i in 0..a.entries().len(){let p=a.entries()[i].path.clone();if p.as_str()=="Contents/section0.xml"{continue;}let j=b.entries().iter().position(|e|e.path==p).ok_or("part")?;assert_eq!(a.read_entry(i)?,b.read_entry(j)?);}Ok(())
}
#[test]
fn control_product_text_mixed_typed_output_delete_and_request_drop_preserve_original()->TestResult{
    let input=format!("A{TAB}B<hp:lineBreak/>C");let bytes=raw(&input)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for(output,expected)in[(json!([tx("한글😀&<hp:tab/>e\u{301}")]),"한글😀&amp;&lt;hp:tab/&gt;e\u{301}"),
        (json!([tx("A"),{"kind":"tab","width":4294967295_u64,"leader":2,"tab_type":1},{"kind":"line_break"},tx("B")]),"A<hp:tab width=\"4294967295\" leader=\"2\" type=\"1\"/><hp:lineBreak/>B"),(json!([]),"")]{
        let mut v=control_request(&s,&bytes)?;v["operation"]["output"]=output;let out=control_prepare!(&provider,&v)?;drop(v);out.verify(&provider,5)?;
        exact_control(&bytes,&out.with_verified_bytes(&provider,5,<[u8]>::to_vec)?,TAB,expected)?;assert_eq!(out.receipt().capability_id,"search.replace_control");}Ok(())
}
#[test]
fn control_product_linebreak_kind_and_multiple_parents_keep_run_shells_and_references()->TestResult{
    let body="<hp:p id='1'><hp:run charPrIDRef='0'><hp:t charStyleIDRef='0'>A<hp:lineBreak/></hp:t><hp:ctrl><hp:bookmark name='KEEP'/></hp:ctrl></hp:run><hp:run charPrIDRef='1'><hp:t charStyleIDRef='1'>B<hp:lineBreak/>C&#38;</hp:t></hp:run></hp:p>";
    let bytes=definition::package(body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=control_request(&s,&bytes)?;v["operation"]["control_kind"]=json!("line_break");
    let out=control_prepare!(&provider,&v)?;exact_control(&bytes,&out.with_verified_bytes(&provider,5,<[u8]>::to_vec)?,"<hp:lineBreak/>","X")?;assert_eq!(out.receipt().stored.output.span_changes.len(),2);Ok(())
}
#[test]
fn control_product_noop_subset_preserves_paired_control_bytes_and_forward_anchor_order()->TestResult{
    let first="<hp:tab width='1' leader='0' type='0'> </hp:tab>";let second="<hp:tab width='2' leader='0' type='0'/>";let bytes=raw(&format!("A{first}B{second}C"))?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=control_request(&s,&bytes)?;v["operation"]["output"]=json!([{"kind":"tab","width":1,"leader":0,"tab_type":0}]);
    let out=control_prepare!(&provider,&v)?;exact_control(&bytes,&out.with_verified_bytes(&provider,5,<[u8]>::to_vec)?,second,"<hp:tab width=\"1\" leader=\"0\" type=\"0\"/>")?;
    assert_eq!(out.receipt().stored.output.selected_controls,2);assert_eq!(out.receipt().stored.output.changed_controls,1);assert_eq!(out.receipt().stored.output.changes[0].original_atom,3);Ok(())
}
#[test]
fn control_product_discovery_supplies_four_atomic_scopes_without_caller_import()->TestResult{
    let bytes=definition::package(&(para(1,&format!("A{TAB}B"))+&para(2,&format!("C{TAB}D"))))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let good=control_request(&s,&bytes)?;let inv=inventory(&provider,&good)?;let range=window(&inv,"body_and_notes",1,2)?;
    let node=inv["inventory"]["nodes"].as_array().ok_or("nodes")?.iter().find(|n|n["source_handle"]==range["start"]["paragraph_handle"]).ok_or("node")?;
    for(scope,n)in[("document",2),("section",2),("node_set",1),("selection",1)]{let mut v=good.clone();v["selector"]["scope"]=json!(scope);
        match scope{"section"=>v["selector"]["section_ids"]=inv["inventory"]["section_ids"].clone(),"node_set"=>v["selector"]["range"]=json!({"node_ids":[node["node_id"].clone()]}),"selection"=>v["selector"]["range"]=range.clone(),_=>{}}
        let out=control_prepare!(&provider,&v)?;let after=out.with_verified_bytes(&provider,5,section)??;assert!(after.contains("AXB"));assert_eq!(after.contains(&format!("C{TAB}D")),n==1);assert_eq!(out.receipt().stored.output.changed_controls,n);}Ok(())
}
#[test]
fn control_product_review_exclusions_precede_caps_and_keep_author_metadata_and_cache()->TestResult{
    let body=fixture::body().replace("BODY K K",&format!("BODY{TAB} K K")).replace("HIDDEN K K",&format!("HIDDEN{TAB} K K")).replace("MEMO K K",&format!("MEMO{TAB} K K"));
    let bytes=definition::package(&body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for(h,m,n)in[(false,false,1),(true,false,2),(false,true,2),(true,true,3)]{let mut v=control_request(&s,&bytes)?;v["operation"]["review_policy"]=policy(h,m);v["operation"]["max_replacements"]=json!(n);
        let mut expected=body.replace(&format!("BODY{TAB}"),"BODYX");if h{expected=expected.replace(&format!("HIDDEN{TAB}"),"HIDDENX");}if m{expected=expected.replace(&format!("MEMO{TAB}"),"MEMOX");}
        let out=control_prepare!(&provider,&v)?;exact_control(&bytes,&out.with_verified_bytes(&provider,5,<[u8]>::to_vec)?,&body,&expected)?;assert_eq!(out.receipt().stored.output.selected_controls,n);}Ok(())
}
#[test]
fn control_product_alias_default_namespaces_keep_original_entities_and_prefixes()->TestResult{
    for(prefix,decl)in[("q:"," xmlns:q='http://www.hancom.co.kr/hwpml/2011/paragraph'"),(""," xmlns='http://www.hancom.co.kr/hwpml/2011/paragraph'")]{
        let body=para(1,&format!("A{TAB}B&#38;")).replace("hp:",prefix).replacen(&format!("<{prefix}p "),&format!("<{prefix}p{decl} "),1);let bytes=definition::package(&body)?;
        let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=control_request(&s,&bytes)?;v["operation"]["output"]=json!([{"kind":"line_break"}]);
        let out=control_prepare!(&provider,&v)?;exact_control(&bytes,&out.with_verified_bytes(&provider,5,<[u8]>::to_vec)?,&format!("<{prefix}tab width='1' leader='0' type='0'/>"),&format!("<{prefix}lineBreak/>"))?;}Ok(())
}
#[test]
fn control_product_required_unknown_wrong_types_and_unimplemented_options_fail_before_reads()->TestResult{
    let bytes=raw(&format!("A{TAB}B"))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=control_request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();let mut bad=vec![b"null".to_vec(),b"[]".to_vec(),format!("{} {{}}",serde_json::to_string(&good)?).into_bytes()];
    for key in["schema_version","idempotency_key","project_id","document_id","base_revision","expected_head_generation","expected_source_package_sha256","plan_id","selector","operation"]{let mut v=good.clone();v.as_object_mut().ok_or("envelope")?.remove(key);bad.push(wire(&v)?);}
    for key in["kind","control_kind","max_replacements","output","review_policy"]{let mut v=good.clone();v["operation"].as_object_mut().ok_or("operation")?.remove(key);bad.push(wire(&v)?);}
    for(key,value)in[("kind",json!("replace_control")),("control_kind",json!("TAB")),("control_kind",json!(null)),("control_kind",json!(1)),("max_replacements",json!(0)),("max_replacements",json!(4097)),("max_replacements",json!(-1)),("max_replacements",json!(1.5)),("query",json!("tab")),("replacement",json!("X")),("regex",json!(true)),("case_sensitive",json!(true)),("whole_word",json!(false)),("style_filter",json!(null)),("direction",json!("all")),("preview_only",json!(true)),("approved",json!(true)),("locale",json!("ko"))]{let mut v=good.clone();v["operation"][key]=value;bad.push(wire(&v)?);}
    for p in[json!({}),json!({"include_hidden_explanations":true}),json!({"include_hidden_explanations":true,"include_memo_bodies":true,"approved":true})]{let mut v=good.clone();v["operation"]["review_policy"]=p;bad.push(wire(&v)?);}
    for(key,value)in[("source_graph",json!({})),("expected_head_generation",json!(0)),("expected_source_package_sha256",json!("A".repeat(64)))]{let mut v=good.clone();v[key]=value;bad.push(wire(&v)?);}
    for b in bad{assert!(matches!(ControlProduct::prepare_json(&provider,&b,Default::default(),Default::default(),4),Err(PE::Request)));}assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn control_product_nested_output_is_strict_including_linebreak_fields_and_raw_controls()->TestResult{
    let bytes=raw(&format!("A{TAB}B"))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=control_request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();
    for output in[json!(null),json!("X"),json!({}),json!([{}]),json!([{"kind":"xml","value":"<hp:tab/>"}]),json!([{"kind":"text"}]),json!([{"kind":"text","value":null}]),json!([{"kind":"text","value":1}]),json!([tx("")]),json!([tx("\t")]),json!([tx("\r")]),json!([tx("\n")]),json!([tx("\u{ffff}")]),
        json!([{"kind":"text","value":"X","ignored":true}]),json!([{"kind":"tab","width":1,"leader":0}]),json!([{"kind":"tab","width":-1,"leader":0,"tab_type":0}]),json!([{"kind":"tab","width":4294967296_u64,"leader":0,"tab_type":0}]),json!([{"kind":"tab","width":1.5,"leader":0,"tab_type":0}]),json!([{"kind":"tab","width":1,"leader":0,"tab_type":0,"xml":"X"}]),json!([{"kind":"line_break","ignored":true}])]{
        let mut v=good.clone();v["operation"]["output"]=output;assert!(matches!(control_prepare!(&provider,&v),Err(PE::Request)));}assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn control_product_other_observed_kinds_are_unqualified_before_source_access()->TestResult{
    let bytes=raw(&format!("A{TAB}B"))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=control_request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();
    for kind in["table","field_begin","field_end","footnote","endnote","bookmark","picture","nonbreaking_space","unknown_character"]{let mut v=good.clone();v["operation"]["control_kind"]=json!(kind);assert!(matches!(control_prepare!(&provider,&v),Err(PE::UnsupportedKind)));}
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn control_product_invalid_selectors_and_escaped_duplicate_keys_fail_before_reads()->TestResult{
    let bytes=raw(&format!("A{TAB}B"))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=control_request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();let mut bad=Vec::new();
    for selector in[json!([]),json!({"scope":"document"}),json!({"revision_id":good["base_revision"],"scope":"document","range":null}),json!({"revision_id":good["base_revision"],"scope":"section","section_ids":[]}),json!({"revision_id":rev::RevisionId::generate().public_id(),"scope":"document"})]{let mut v=good.clone();v["selector"]=selector;bad.push(wire(&v)?);}
    let text=serde_json::to_string(&good)?;for(from,to)in[("\"control_kind\":\"tab\"","\"control_kind\":\"tab\",\"control_ki\\u006ed\":\"line_break\""),("\"scope\":\"document\"","\"scope\":\"document\",\"sco\\u0070e\":\"selection\""),("\"value\":\"X\"","\"value\":\"X\",\"va\\u006cue\":\"Y\""),("\"kind\":\"text\"","\"kind\":\"text\",\"ki\\u006ed\":\"line_break\"")]{let changed=text.replace(from,to);assert_ne!(changed,text);bad.push(changed.into_bytes());}
    for b in bad{assert!(matches!(ControlProduct::prepare_json(&provider,&b,Default::default(),Default::default(),4),Err(PE::Request)));}assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn control_product_exact_16k_and_escaped_value_have_distinct_raw_but_equal_canonical_binding()->TestResult{
    let bytes=raw(&format!("A{TAB}B"))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=control_request(&s,&bytes)?;let out=control_prepare!(&provider,&good)?;let mut padded=wire(&good)?;padded.resize(16*1024,b' ');
    let other=ControlProduct::prepare_json(&provider,&padded,Default::default(),Default::default(),4)?;assert_ne!(out.receipt().raw_request_sha256,other.receipt().raw_request_sha256);assert_eq!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);padded.push(b' ');
    assert!(matches!(ControlProduct::prepare_json(&provider,&padded,Default::default(),Default::default(),4),Err(PE::Limit)));assert!(matches!(ControlProduct::prepare_json(&provider,b"",Default::default(),Default::default(),4),Err(PE::Limit)));
    let text=serde_json::to_string(&good)?;let escaped=text.replace("\"value\":\"X\"","\"value\":\"\\u0058\"");assert_ne!(escaped,text);let other=ControlProduct::prepare_json(&provider,escaped.as_bytes(),Default::default(),Default::default(),4)?;
    assert_ne!(out.receipt().raw_request_sha256,other.receipt().raw_request_sha256);assert_eq!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);Ok(())
}
#[test]
fn control_product_legacy_profiles_are_mutually_rejected_without_reading_source()->TestResult{
    use hwpx_agent_cli::form_product_request::stored_literal_replacement::{StoredLiteralReplacementProductRequest as Literal,
        whitespace::StoredWhitespaceProductRequest as Whitespace,width::StoredWidthProductRequest as Width,case::StoredCaseProductRequest as Case,unicode::matches::StoredUnicodeMatchProductRequest as Match};
    let bytes=raw(&format!("A{TAB}B"))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=control_request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();let b=wire(&good)?;
    assert!(Whitespace::prepare_json(&provider,&b,Default::default(),Default::default(),4).is_err());assert!(Width::prepare_json(&provider,&b,Default::default(),Default::default(),4).is_err());assert!(Case::prepare_json(&provider,&b,Default::default(),Default::default(),4).is_err());assert!(UnicodeProduct::prepare_json(&provider,&b,Default::default(),Default::default(),4).is_err());assert!(Match::prepare_json(&provider,&b,Default::default(),Default::default(),4).is_err());assert!(Literal::prepare_json(&provider,&b,Default::default(),Default::default(),4).is_err());assert!(Product::prepare_json(&provider,&b,Default::default(),Default::default(),4).is_err());assert!(Discovery::prepare_json(&provider,&b,Default::default(),4).is_err());
    for mut v in[request(&s,&bytes)?,envelope(&s,&bytes)?]{v["schema_version"]=json!(CONTROL_SCHEMA);assert!(matches!(control_prepare!(&provider,&v),Err(PE::Request)));}assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn control_product_kind_output_review_cap_key_plan_and_scope_are_fingerprint_bound()->TestResult{
    let bytes=raw(&format!("A{TAB}B<hp:lineBreak/>C"))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=control_request(&s,&bytes)?;let out=control_prepare!(&provider,&good)?;
    for(key,value)in[("idempotency_key",json!("OTHER-KEY")),("plan_id",json!("other-plan"))]{let mut v=good.clone();v[key]=value;let other=control_prepare!(&provider,&v)?;assert_ne!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);assert_ne!(out.receipt().scoped_request_sha256,other.receipt().scoped_request_sha256);assert_eq!(out.receipt().stored.output.output_package_sha256,other.receipt().stored.output.output_package_sha256);}
    for(key,value)in[("control_kind",json!("line_break")),("output",json!([tx("Y")])),("review_policy",policy(false,false)),("max_replacements",json!(1))]{let mut v=good.clone();v["operation"][key]=value;let other=control_prepare!(&provider,&v)?;assert_ne!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);assert_ne!(out.receipt().stored.output.request_sha256,other.receipt().stored.output.request_sha256);}
    let inv=inventory(&provider,&good)?;let mut v=good;v["selector"]["scope"]=json!("section");v["selector"]["section_ids"]=inv["inventory"]["section_ids"].clone();assert_ne!(out.receipt().scoped_request_sha256,control_prepare!(&provider,&v)?.receipt().scoped_request_sha256);Ok(())
}
#[test]
fn control_product_current_write_and_five_foreign_scopes_deny_retained_delivery()->TestResult{
    let bytes=raw(&format!("A{TAB}B"))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=control_request(&s,&bytes)?;let reader=s.provider()?;assert!(control_prepare!(&reader,&v).is_err());let source=reader.import_actual_forms(s.head,4)?;
    assert!(matches!(source.prepare_control_candidate(&reader,Scope::Document,all(),ControlKind::Tab,100,&[TextAtom::Text("X".into())],Default::default(),Default::default(),4),Err(SE::Permission)));
    let out=control_prepare!(&provider,&v)?;let called=Cell::new(false);assert!(out.with_verified_bytes(&reader,5,|_|called.set(true)).is_err());
    for variant in 0..5{let tenant=if variant==4{TenantId::new(Uuid::from_u128(997))?}else{s.reader.tenant_id()};let subject=if variant==3{SubjectDigest::from_authenticated_subject("foreign-control-replacement")?}else{s.reader.subject()};let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);let context=rev::RevisionRequestContext::new(tenant,subject);let project=if variant==2{rev::ProjectId::parse("prj_70000000000000000000000000000002")?}else{s.project};let branch=if variant==1{rev::BranchId::parse("brn_70000000000000000000000000000002")?}else{s.branch};
        let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&context,project,branch,DocumentId::parse(if variant==0{"foreign-document"}else{"actual-form-document"})?)?;assert!(out.verify(&other,5).is_err());assert!(out.with_verified_bytes(&other,5,|_|called.set(true)).is_err());}assert!(!called.get());Ok(())
}
#[test]
fn control_product_acl_regrant_quarantine_and_aead_protect_new_and_retained_candidates()->TestResult{
    for mode in 0..3{let bytes=raw(&format!("A{TAB}B"))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=control_request(&s,&bytes)?;let out=control_prepare!(&provider,&v)?;
        match mode{0=>{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;},1=>{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("CONTROL_TEST")?,5)?;},_=>s.blobs.tamper.store(true,Ordering::SeqCst)}
        let called=Cell::new(false);assert!(out.verify(&provider,6).is_err());assert!(out.with_verified_bytes(&provider,6,|_|called.set(true)).is_err());assert!(control_prepare!(&provider,&v).is_err());assert!(!called.get());
        if mode==0{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;out.verify(&provider,8)?;out.with_verified_bytes(&provider,8,|_|())?;}}Ok(())
}
#[test]
fn control_product_prepare_verify_and_delivery_final_head_races_block_consumers()->TestResult{
    for stage in 0..3{let bytes=raw(&format!("A{TAB}B"))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=control_request(&s,&bytes)?;let b=wire(&v)?;let out=control_prepare!(&provider,&v)?;
        let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,ContentDigest::of(b"control race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation"),ContentDigest::of(b"transaction"))?;
        let repo=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});let bound=StoredFormProvider::bind(&s.artifacts,&repo,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
        match stage{0=>{ControlProduct::prepare_json(&bound,&b,Default::default(),Default::default(),5)?;},1=>{out.verify(&bound,5)?;},_=>{out.with_verified_bytes(&bound,5,|_|())?;}}
        let calls=repo.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);repo.repository().calls.store(0,Ordering::SeqCst);repo.repository().trigger.store(calls,Ordering::SeqCst);let called=Cell::new(false);
        match stage{0=>assert!(ControlProduct::prepare_json(&bound,&b,Default::default(),Default::default(),6).is_err()),1=>assert!(out.verify(&bound,6).is_err()),_=>assert!(out.with_verified_bytes(&bound,6,|_|called.set(true)).is_err())}assert!(!called.get());assert_eq!(repo.repository().calls.load(Ordering::SeqCst),calls);}Ok(())
}
#[test]
fn control_product_borrowed_owned_and_json_share_bound_receipts_and_output()->TestResult{
    let bytes=raw(&format!("A{TAB}B"))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=control_request(&s,&bytes)?;let out=control_prepare!(&provider,&v)?;let source=provider.import_actual_forms(s.head,4)?;let data=[TextAtom::Text("X".into())];
    let borrowed=source.prepare_control_candidate(&provider,Scope::Document,all(),ControlKind::Tab,100,&data,Default::default(),Default::default(),4)?;assert_eq!(borrowed.verify(&provider,5)?,out.receipt().stored);drop(borrowed);
    let owned=source.into_control_candidate(&provider,Scope::Document,all(),ControlKind::Tab,100,&data,Default::default(),Default::default(),4)?;assert_eq!(owned.verify(&provider,5)?,out.receipt().stored);
    assert_eq!(owned.with_verified_bytes(&provider,5,<[u8]>::to_vec)?,out.with_verified_bytes(&provider,5,<[u8]>::to_vec)?);assert!(matches!(owned.require_current_product_route(&provider,5),Err(SE::RouteUnqualified)));Ok(())
}
#[test]
fn control_product_wrong_source_head_revision_scope_and_index_reject_preparation()->TestResult{
    let bytes=raw(&format!("A{TAB}B"))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=control_request(&s,&bytes)?;
    for(key,value)in[("expected_head_generation",json!(s.head.generation()+1)),("expected_source_package_sha256",json!("0".repeat(64))),("document_id",json!("foreign-document")),("project_id",json!("prj_70000000000000000000000000000002")),("base_revision",json!(rev::RevisionId::generate().public_id()))]{let mut v=good.clone();v[key]=value;assert!(control_prepare!(&provider,&v).is_err());}
    let inv=inventory(&provider,&good)?;let mut v=good;v["selector"]["scope"]=json!("selection");v["selector"]["range"]=window(&inv,"body_and_notes",1,2)?;v["selector"]["range"]["index_sha256"]=json!("0".repeat(64));assert!(control_prepare!(&provider,&v).is_err());Ok(())
}
#[test]
fn control_product_no_matches_nochange_and_empty_atomic_selection_are_distinct()->TestResult{
    let bytes=raw(&format!("A{TAB}B"))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=control_request(&s,&bytes)?;let mut v=good.clone();v["operation"]["control_kind"]=json!("line_break");
    assert!(matches!(control_prepare!(&provider,&v),Err(PE::Stored(SE::Output(Core::Output(Compile::NoMatches))))));v=good.clone();v["operation"]["output"]=json!([{"kind":"tab","width":1,"leader":0,"tab_type":0}]);
    assert!(matches!(control_prepare!(&provider,&v),Err(PE::Stored(SE::Output(Core::Output(Compile::NoChange))))));let inv=inventory(&provider,&good)?;let mut v=good;v["selector"]["scope"]=json!("selection");v["selector"]["range"]=window(&inv,"body_and_notes",1,1)?;
    assert!(matches!(control_prepare!(&provider,&v),Err(PE::Stored(SE::Output(Core::Output(Compile::NoMatches))))));Ok(())
}
#[test]
fn control_product_protected_noops_field_cache_and_ambiguous_nfc_boundaries_reject()->TestResult{
    let body=para(1,&format!("A{TAB}B")).replace("charPrIDRef='0'","charPrIDRef='0' charTcId='1'");let bytes=definition::package(&body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=control_request(&s,&bytes)?;v["operation"]["output"]=json!([{"kind":"tab","width":1,"leader":0,"tab_type":0}]);
    assert!(matches!(control_prepare!(&provider,&v),Err(PE::Stored(SE::Output(Core::Output(Compile::Protection))))));
    let bytes=definition::package(&fixture::body().replace("CACHE FROZEN",&format!("CACHE{TAB} FROZEN")))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=control_request(&s,&bytes)?;
    assert!(matches!(control_prepare!(&provider,&v),Err(PE::Stored(SE::Output(Core::Output(Compile::FieldContent))))));
    let bytes=raw(&format!("x\u{315}\u{300}{TAB}Z"))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=control_request(&s,&bytes)?;let inv=inventory(&provider,&v)?;v["selector"]["scope"]=json!("selection");v["selector"]["range"]=window(&inv,"body_and_notes",2,4)?;
    assert!(matches!(control_prepare!(&provider,&v),Err(PE::Stored(SE::Output(Core::Output(Compile::Search(Search::Scope)))))));Ok(())
}
#[test]
fn control_product_match_work_response_and_writer_limits_never_return_partial_candidates()->TestResult{
    let bytes=raw(&format!("A{TAB}B{TAB}C"))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=control_request(&s,&bytes)?;v["operation"]["max_replacements"]=json!(1);
    assert!(matches!(control_prepare!(&provider,&v),Err(PE::Stored(SE::Output(Core::Output(Compile::Search(Search::Limit)))))));v["operation"]["max_replacements"]=json!(100);
    assert!(ControlProduct::prepare_json(&provider,&wire(&v)?,SourceSearchLimits::new(Config{result_bytes:1,..Default::default()})?,Default::default(),4).is_err());assert!(ControlProduct::prepare_json(&provider,&wire(&v)?,SourceSearchLimits::new(Config{decomposed_scalars:1,..Default::default()})?,Default::default(),4).is_err());
    assert!(matches!(ControlProduct::prepare_json(&provider,&wire(&v)?,Default::default(),WriterLimits::new(WriterLimitConfig{max_output_bytes:1,..Default::default()})?,4),Err(PE::Stored(SE::Output(Core::Output(Compile::Writer))))));Ok(())
}
#[test]
fn control_product_private_data_closed_route_and_original_head_ingest_are_preserved()->TestResult{
    let bytes=raw(&format!("PRIVATE-SOURCE{TAB}B"))?;let original=ContentDigest::of(&bytes);let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=control_request(&s,&bytes)?;v["operation"]["output"]=json!([tx("PRIVATE-OUTPUT")]);let out=control_prepare!(&provider,&v)?;
    for text in[format!("{out:?}{:?}",out.receipt()),serde_json::to_string(out.receipt())?]{assert!(!text.contains("PRIVATE-SOURCE"));assert!(!text.contains("PRIVATE-OUTPUT"));assert!(!text.contains("PRIVATE-UNICODE-KEY"));}
    assert!(matches!(out.require_current_product_route(&provider,5),Err(PE::RouteUnqualified)));assert!(!out.receipt().idempotency_key_claimed&&!out.receipt().full_control_native_cas_execution_publication_authority);assert_eq!(ContentDigest::of(&bytes),original);assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
}
#[test]
fn control_product_many_controls_use_one_span_guard_and_linear_retained_anchor_subset()->TestResult{
    let input=format!("A{}B",TAB.repeat(2000));let bytes=raw(&input)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=control_request(&s,&bytes)?;v["operation"]["max_replacements"]=json!(2000);let out=control_prepare!(&provider,&v)?;
    out.verify(&provider,5)?;exact_control(&bytes,&out.with_verified_bytes(&provider,5,<[u8]>::to_vec)?,&input,&format!("A{}B","X".repeat(2000)))?;let r=&out.receipt().stored.output;assert_eq!(r.changed_controls,2000);assert_eq!(r.span_changes.len(),1);
    let xml=hwpx_package::PreservingXmlDocument::parse(section(&bytes)?.as_bytes())?;assert_eq!(r.observed_protection_element_visits,xml.elements().len()*3);Ok(())
}
#[test]
fn control_product_validated_borrowed_input_is_not_a_source_or_limit_override_token()->TestResult{
    let bytes=raw(&format!("A{TAB}B"))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=control_request(&s,&bytes)?;let out=control_prepare!(&provider,&v)?;
    let source=provider.import_actual_forms(s.head,4)?;let other=provider.import_actual_forms(s.head,4)?;let proof=source.imported().reconstruct_source_for_verification(&bytes)?;let data=[TextAtom::Text("X".into())];let input=ValidatedTextControlOutput::new(ControlKind::Tab,&data,Default::default())?;
    assert_eq!(input.replacement_sha256(),out.receipt().stored.output.replacement_sha256);assert_eq!(input.output_atoms(),1);assert_eq!(input.text_bytes(),1);assert_eq!(input.kind(),ControlKind::Tab);
    assert!(matches!(input.lower(&proof,other.imported(),Scope::Document,all(),100,Default::default()),Err(Core::Output(Compile::Source))));
    let bounded=ValidatedTextControlOutput::new(ControlKind::Tab,&data,SourceSearchLimits::new(Config{result_bytes:1,..Default::default()})?)?;assert!(bounded.lower(&proof,source.imported(),Scope::Document,all(),100,Default::default()).is_err());
    let secret=[TextAtom::Text("PRIVATE-INPUT".into())];assert!(!format!("{:?}",ValidatedTextControlOutput::new(ControlKind::Tab,&secret,Default::default())?).contains("PRIVATE-INPUT"));Ok(())
}
