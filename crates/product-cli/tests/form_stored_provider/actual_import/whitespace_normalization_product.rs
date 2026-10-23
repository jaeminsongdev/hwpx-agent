//! Exact whitespace/control candidates through current access and strict JSON, not full transactions.
use super::*;
use hwpx_agent_cli::form_product_request::stored_literal_replacement::whitespace::{StoredWhitespaceProductRequest as WProduct,
    WhitespaceProductError as WE,WHITESPACE_PRODUCT_REQUEST_SCHEMA as WSCHEMA};
use hwpx_agent_cli::form_stored_provider::actual_import::literal_search_output::whitespace::StoredWhitespaceError as WS;
use hwpx_package::document_import::search::{SourceSearchError as Search,reviews::selector::styles::SourceReviewStyleFilter as Filter,
    inspection::SourceDeclaredStyleFilter as Declared,replacement::atoms::whitespace::{SourceWhitespacePolicy as WPolicy,
        SourceWhitespaceTextPolicy as Text,SourceWhitespaceSequencePolicy as Sequence,SourceWhitespaceOutput as Out}};
macro_rules! whitespace_prepare{($p:expr,$v:expr)=>{WProduct::prepare_json($p,&wire($v)?,Default::default(),Default::default(),4)}}
fn wpolicy()->WPolicy{WPolicy{text:Text::AsciiSpace,tabs:true,line_breaks:true,sequence:Sequence::CollapseEachMatchedSequence,output:Out::Spaces{count:1}}}
fn wrequest(s:&StoredFixture,bytes:&[u8])->Result<Value,Box<dyn Error>>{let mut v=request(s,bytes)?;v["schema_version"]=json!(WSCHEMA);
    v["operation"]=json!({"kind":"normalize_whitespace_matches","query":"(?s:.+)","regex":true,"case_sensitive":true,"whole_word":false,"max_matches":100,
        "whitespace_policy":wpolicy(),"run_policy":"first_original_run_retain_all_runs","review_policy":policy(true,true)});Ok(v)}
fn exact_output(source:&[u8],out:&[u8],old:&str,new:&str)->TestResult{
    assert_eq!(section(out)?,section(source)?.replace(old,new));let mut a=hwpx_package::BoundedZipReader::open(Cursor::new(source),Default::default())?;
    let mut b=hwpx_package::BoundedZipReader::open(Cursor::new(out),Default::default())?;assert_eq!(a.entries().len(),b.entries().len());
    for i in 0..a.entries().len(){let path=a.entries()[i].path.clone();if path.as_str()=="Contents/section0.xml"{continue;}let j=b.entries().iter().position(|e|e.path==path).ok_or("part")?;assert_eq!(a.read_entry(i)?,b.read_entry(j)?);}Ok(())
}
#[test]
fn whitespace_product_explicit_collapse_each_remove_and_owned_request_drop()->TestResult{
    let bytes=raw("A   B")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for(sequence,out,expected)in[(Sequence::CollapseEachMatchedSequence,Out::Spaces{count:1},"A B"),(Sequence::EachOriginalScalar,Out::Spaces{count:2},"A      B"),(Sequence::CollapseEachMatchedSequence,Out::Remove,"AB")]{
        let mut v=wrequest(&s,&bytes)?;v["operation"]["whitespace_policy"]=json!(WPolicy{sequence,output:out,..wpolicy()});let out=whitespace_prepare!(&provider,&v)?;drop(v);out.verify(&provider,5)?;
        exact_output(&bytes,&out.with_verified_bytes(&provider,5,<[u8]>::to_vec)?,"A   B",expected)?;assert_eq!(out.receipt().capability_id,"search.normalize_whitespace");}Ok(())
}
#[test]
fn whitespace_product_cross_run_control_collapse_retains_first_style_and_all_shells()->TestResult{
    let body=format!("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t charStyleIDRef='0'>&#x1F600;A  {TAB}</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t charStyleIDRef='1'><hp:lineBreak> </hp:lineBreak> B&#38;</hp:t></hp:run></hp:p>");
    let bytes=definition::package(&body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=wrequest(&s,&bytes)?;let out=whitespace_prepare!(&provider,&v)?;
    let expected=body.replace(&format!("A  {TAB}"),"A ").replace("<hp:lineBreak> </hp:lineBreak> B","B");exact_output(&bytes,&out.with_verified_bytes(&provider,5,<[u8]>::to_vec)?,&body,&expected)?;
    assert_eq!(out.receipt().stored.output.changed_original_controls,2);assert_eq!(out.receipt().stored.output.changes.len(),2);Ok(())
}
#[test]
fn whitespace_product_typed_tab_linebreak_and_fixed_spaces_are_bound_not_visual_stops()->TestResult{
    let bytes=raw("A  B  C")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for(output,render)in[(Out::LineBreak,"<hp:lineBreak/>"),(Out::Tab{width:u32::MAX,leader:2,tab_type:1},"<hp:tab width=\"4294967295\" leader=\"2\" type=\"1\"/>"),(Out::Spaces{count:4},"    ")]{
        let mut v=wrequest(&s,&bytes)?;let pol=WPolicy{output,..wpolicy()};v["operation"]["whitespace_policy"]=json!(pol);let out=whitespace_prepare!(&provider,&v)?;
        exact_output(&bytes,&out.with_verified_bytes(&provider,5,<[u8]>::to_vec)?,"  ",render)?;assert_eq!(out.receipt().stored.output.policy,pol);}Ok(())
}
#[test]
fn whitespace_product_nonbreaking_and_unrelated_characters_follow_explicit_text_policy()->TestResult{
    let text="A  B\u{a0}\u{a0}C\u{2007}\u{2007}D\u{202f}\u{202f}E\u{3000}\u{3000}F\u{200b}\u{feff}";let bytes=raw(text)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for t in[Text::AsciiSpace,Text::Unicode17Breaking,Text::Unicode17AllModelAdmitted]{let mut v=wrequest(&s,&bytes)?;v["operation"]["whitespace_policy"]=json!(WPolicy{text:t,..wpolicy()});let out=whitespace_prepare!(&provider,&v)?;
        let mut expected=text.replace("  "," ");if t!=Text::AsciiSpace{expected=expected.replace("\u{3000}\u{3000}"," ");}if t==Text::Unicode17AllModelAdmitted{for c in['\u{a0}','\u{2007}','\u{202f}']{expected=expected.replace(&format!("{c}{c}")," ");}}
        exact_output(&bytes,&out.with_verified_bytes(&provider,5,<[u8]>::to_vec)?,text,&expected)?;}Ok(())
}
#[test]
fn whitespace_product_discovery_four_scopes_and_clipped_regex_without_caller_import()->TestResult{
    let bytes=definition::package(&(para(1,"A  B")+&para(2,"C  D")))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let mut good=wrequest(&s,&bytes)?;good["operation"]["query"]=json!("  ");let inv=inventory(&provider,&good)?;let range=window(&inv,"body_and_notes",1,3)?;
    let node=inv["inventory"]["nodes"].as_array().ok_or("nodes")?.iter().find(|n|n["source_handle"]==range["start"]["paragraph_handle"]).ok_or("node")?;
    for(scope,n)in[("document",2),("section",2),("node_set",1),("selection",1)]{let mut v=good.clone();v["selector"]["scope"]=json!(scope);
        match scope{"section"=>v["selector"]["section_ids"]=inv["inventory"]["section_ids"].clone(),"node_set"=>v["selector"]["range"]=json!({"node_ids":[node["node_id"].clone()]}),"selection"=>{v["selector"]["range"]=range.clone();v["operation"]["query"]=json!("^  $");},_=>{}}
        let out=whitespace_prepare!(&provider,&v)?;let after=out.with_verified_bytes(&provider,5,section)??;assert!(after.contains("A B"));assert_eq!(after.contains("C  D"),n==1);assert_eq!(out.receipt().stored.output.search.search().result().matches().len(),n);}Ok(())
}
#[test]
fn whitespace_product_declared_definition_folded_word_filters_preserve_original_case()->TestResult{
    let body="<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>A </hp:t></hp:run><hp:run charPrIDRef='1'><hp:t> B a  b xa  bx A  B</hp:t></hp:run></hp:p>";
    let bytes=definition::package(body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for filter in[json!({"kind":"declared","filter":{"run_character_property":1}}),json!({"kind":"definition","filter":{"character_source":"run_property","bold":true}})]{let mut v=wrequest(&s,&bytes)?;v["operation"]["query"]=json!("a  b");v["operation"]["case_sensitive"]=json!(false);v["operation"]["whole_word"]=json!(true);v["operation"]["max_matches"]=json!(2);v["operation"]["style_filter"]=filter;
        let out=whitespace_prepare!(&provider,&v)?;exact_output(&bytes,&out.with_verified_bytes(&provider,5,<[u8]>::to_vec)?,"> B a  b xa  bx A  B<","> B a b xa  bx A B<")?;assert_eq!(out.receipt().stored.output.search.search().result().matches().len(),2);}Ok(())
}
#[test]
fn whitespace_product_review_exclusions_precede_caps_and_keep_cache_and_metadata()->TestResult{
    let body=fixture::body().replace("K K","K  K");let bytes=definition::package(&body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for(h,m,n)in[(false,false,1),(true,false,2),(false,true,2),(true,true,3)]{let mut v=wrequest(&s,&bytes)?;v["operation"]["query"]=json!("  ");v["operation"]["regex"]=json!(false);v["operation"]["review_policy"]=policy(h,m);v["operation"]["max_matches"]=json!(n);v["operation"]["whitespace_policy"]["output"]=json!(Out::LineBreak);
        let mut expected=body.replace("BODY K  K","BODY K<hp:lineBreak/>K");if h{expected=expected.replace("HIDDEN K  K","HIDDEN K<hp:lineBreak/>K");}if m{expected=expected.replace("MEMO K  K","MEMO K<hp:lineBreak/>K");}
        let out=whitespace_prepare!(&provider,&v)?;exact_output(&bytes,&out.with_verified_bytes(&provider,5,<[u8]>::to_vec)?,&body,&expected)?;assert_eq!(out.receipt().stored.output.search.search().result().matches().len(),n);}Ok(())
}
#[test]
fn whitespace_product_alias_and_default_namespaces_keep_nonselected_controls_and_entities()->TestResult{
    let text=format!("&#x1F600;A  B{TAB}C<hp:lineBreak> </hp:lineBreak>D&#38;");
    for(prefix,decl)in[("q:"," xmlns:q='http://www.hancom.co.kr/hwpml/2011/paragraph'"),(""," xmlns='http://www.hancom.co.kr/hwpml/2011/paragraph'")]{
        let body=para(1,&text).replace("hp:",prefix).replacen(&format!("<{prefix}p "),&format!("<{prefix}p{decl} "),1);let bytes=definition::package(&body)?;
        let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=wrequest(&s,&bytes)?;
        v["operation"]["query"]=json!("  ");v["operation"]["whitespace_policy"]["output"]=json!(Out::LineBreak);let out=whitespace_prepare!(&provider,&v)?;
        exact_output(&bytes,&out.with_verified_bytes(&provider,5,<[u8]>::to_vec)?,"A  B",&format!("A<{prefix}lineBreak/>B"))?;}Ok(())
}
#[test]
fn whitespace_product_missing_unknown_wrong_types_and_unimplemented_options_fail_before_reads()->TestResult{
    let bytes=raw("A  B")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=wrequest(&s,&bytes)?;let before=s.metadata.audit_events()?.len();let mut bad=vec![b"null".to_vec(),b"[]".to_vec(),format!("{} {{}}",serde_json::to_string(&good)?).into_bytes()];
    for key in["schema_version","idempotency_key","project_id","document_id","base_revision","expected_head_generation","expected_source_package_sha256","plan_id","selector","operation"]{let mut v=good.clone();v.as_object_mut().ok_or("envelope")?.remove(key);bad.push(wire(&v)?);}
    for key in["kind","query","regex","case_sensitive","whole_word","max_matches","whitespace_policy","run_policy","review_policy"]{let mut v=good.clone();v["operation"].as_object_mut().ok_or("operation")?.remove(key);bad.push(wire(&v)?);}
    for(key,value)in[("kind",json!("normalize_whitespace")),("regex",json!("true")),("query",json!("")),("query",json!("a".repeat(4097))),("max_matches",json!(0)),("max_matches",json!(10001)),("max_matches",json!(-1)),("max_matches",json!(1.5)),("run_policy",json!("flatten_runs")),("mode",json!("visual")),("locale",json!("ko")),("normalization",json!("nfc")),("replacement",json!("X")),("direction",json!("backward"))]{let mut v=good.clone();v["operation"][key]=value;bad.push(wire(&v)?);}
    for pol in[json!({}),json!({"include_hidden_explanations":true}),json!({"include_hidden_explanations":true,"include_memo_bodies":true,"approved":true})]{let mut v=good.clone();v["operation"]["review_policy"]=pol;bad.push(wire(&v)?);}
    for(key,value)in[("source_graph",json!({})),("expected_head_generation",json!(0)),("expected_source_package_sha256",json!("A".repeat(64)))]{let mut v=good.clone();v[key]=value;bad.push(wire(&v)?);}
    for b in bad{assert!(matches!(WProduct::prepare_json(&provider,&b,Default::default(),Default::default(),4),Err(WE::Request)));}assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn whitespace_product_nested_policy_and_typed_output_validation_is_strict_before_reads()->TestResult{
    let bytes=raw("A  B")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=wrequest(&s,&bytes)?;let before=s.metadata.audit_events()?.len();let mut bad=Vec::new();
    for key in["text","tabs","line_breaks","sequence","output"]{let mut v=good.clone();v["operation"]["whitespace_policy"].as_object_mut().ok_or("policy")?.remove(key);bad.push(v);}
    for(key,value)in[("text",json!("all_unicode_controls")),("tabs",json!(1)),("line_breaks",json!(null)),("sequence",json!("native")),("approved",json!(true)),("output",json!("<hp:tab/>")),("output",json!({"spaces":{"count":0}})),("output",json!({"spaces":{"count":1025}})),("output",json!({"spaces":{"count":-1}})),("output",json!({"spaces":{"count":1.5}})),("output",json!({"spaces":{"count":1,"ignored":true}})),("output",json!({"tab":{"width":1,"leader":0}})),("output",json!({"tab":{"width":4294967296_u64,"leader":0,"tab_type":0}})),("output",json!({"tab":{"width":1,"leader":0,"tab_type":0,"xml":"X"}})),("output",json!({"line_break":{},"remove":{}}))]{let mut v=good.clone();v["operation"]["whitespace_policy"][key]=value;bad.push(v);}
    let mut v=good;v["operation"]["whitespace_policy"]=json!(WPolicy{text:Text::None,tabs:false,line_breaks:false,..wpolicy()});bad.push(v);
    for v in bad{assert!(matches!(whitespace_prepare!(&provider,&v),Err(WE::Request)));}assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn whitespace_product_filters_selectors_and_escaped_duplicates_reject_before_reads()->TestResult{
    let bytes=raw("A  B")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=wrequest(&s,&bytes)?;let before=s.metadata.audit_events()?.len();let mut bad=Vec::new();
    for filter in[json!([]),json!({}),json!({"kind":"declared","filter":{}}),json!({"kind":"definition","filter":{"bold":true}}),json!({"kind":"resolved","filter":{"bold":true}})]{let mut v=good.clone();v["operation"]["style_filter"]=filter;bad.push(wire(&v)?);}
    for selector in[json!([]),json!({"scope":"document"}),json!({"revision_id":good["base_revision"],"scope":"document","range":null}),json!({"revision_id":good["base_revision"],"scope":"section","section_ids":[]}),json!({"revision_id":rev::RevisionId::generate().public_id(),"scope":"document"})]{let mut v=good.clone();v["selector"]=selector;bad.push(wire(&v)?);}
    let text=serde_json::to_string(&good)?;for(from,to)in[("\"regex\":true","\"regex\":true,\"regex\":false"),("\"scope\":\"document\"","\"scope\":\"document\",\"sco\\u0070e\":\"selection\""),("\"tabs\":true","\"tabs\":true,\"ta\\u0062s\":false"),("\"count\":1","\"count\":1,\"co\\u0075nt\":2")]{let changed=text.replace(from,to);assert_ne!(changed,text);bad.push(changed.into_bytes());}
    for b in bad{assert!(matches!(WProduct::prepare_json(&provider,&b,Default::default(),Default::default(),4),Err(WE::Request)));}assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn whitespace_product_exact_16k_and_optional_null_filter_bind_canonical_requests()->TestResult{
    let bytes=raw("A  B")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=wrequest(&s,&bytes)?;let out=whitespace_prepare!(&provider,&good)?;let mut padded=wire(&good)?;padded.resize(16*1024,b' ');
    let other=WProduct::prepare_json(&provider,&padded,Default::default(),Default::default(),4)?;assert_ne!(out.receipt().raw_request_sha256,other.receipt().raw_request_sha256);assert_eq!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);padded.push(b' ');
    assert!(matches!(WProduct::prepare_json(&provider,&padded,Default::default(),Default::default(),4),Err(WE::Limit)));assert!(matches!(WProduct::prepare_json(&provider,b"",Default::default(),Default::default(),4),Err(WE::Limit)));
    let mut v=good;v["operation"]["style_filter"]=json!(null);let other=whitespace_prepare!(&provider,&v)?;assert_ne!(out.receipt().raw_request_sha256,other.receipt().raw_request_sha256);assert_eq!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);Ok(())
}
#[test]
fn whitespace_product_older_profiles_and_whitespace_request_are_mutually_rejected_before_reads()->TestResult{
    use hwpx_agent_cli::form_product_request::stored_literal_replacement::{StoredLiteralReplacementProductRequest as Literal,
        width::StoredWidthProductRequest as Width,case::StoredCaseProductRequest as Case,unicode::matches::StoredUnicodeMatchProductRequest as Match};
    let bytes=raw("A  B")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=wrequest(&s,&bytes)?;let before=s.metadata.audit_events()?.len();let b=wire(&good)?;
    assert!(Width::prepare_json(&provider,&b,Default::default(),Default::default(),4).is_err());assert!(Case::prepare_json(&provider,&b,Default::default(),Default::default(),4).is_err());assert!(UnicodeProduct::prepare_json(&provider,&b,Default::default(),Default::default(),4).is_err());assert!(Match::prepare_json(&provider,&b,Default::default(),Default::default(),4).is_err());assert!(Literal::prepare_json(&provider,&b,Default::default(),Default::default(),4).is_err());assert!(Product::prepare_json(&provider,&b,Default::default(),Default::default(),4).is_err());assert!(Discovery::prepare_json(&provider,&b,Default::default(),4).is_err());
    for mut v in[request(&s,&bytes)?,envelope(&s,&bytes)?]{v["schema_version"]=json!(WSCHEMA);assert!(matches!(whitespace_prepare!(&provider,&v),Err(WE::Request)));}
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn whitespace_product_query_policy_filter_key_plan_and_scope_bindings_are_distinct()->TestResult{
    let bytes=raw("A  B")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut good=wrequest(&s,&bytes)?;good["operation"]["query"]=json!("A  B");let out=whitespace_prepare!(&provider,&good)?;
    for(key,value)in[("idempotency_key",json!("OTHER-KEY")),("plan_id",json!("other-plan"))]{let mut v=good.clone();v[key]=value;let other=whitespace_prepare!(&provider,&v)?;assert_ne!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);assert_ne!(out.receipt().scoped_request_sha256,other.receipt().scoped_request_sha256);assert_eq!(out.receipt().stored.output.output_package_sha256,other.receipt().stored.output.output_package_sha256);}
    for(key,value)in[("query",json!("A {2}B")),("regex",json!(false)),("case_sensitive",json!(false)),("whole_word",json!(true)),("max_matches",json!(101)),("review_policy",policy(false,false)),("style_filter",json!({"kind":"declared","filter":{"run_character_property":0}}))]{let mut v=good.clone();v["operation"][key]=value;let other=whitespace_prepare!(&provider,&v)?;assert_ne!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);assert_ne!(out.receipt().stored.output.request_sha256,other.receipt().stored.output.request_sha256);}
    for pol in[WPolicy{text:Text::Unicode17Breaking,..wpolicy()},WPolicy{tabs:false,..wpolicy()},WPolicy{line_breaks:false,..wpolicy()},WPolicy{sequence:Sequence::EachOriginalScalar,output:Out::Spaces{count:2},..wpolicy()},WPolicy{output:Out::LineBreak,..wpolicy()}]{let mut v=good.clone();v["operation"]["whitespace_policy"]=json!(pol);let other=whitespace_prepare!(&provider,&v)?;assert_ne!(out.receipt().stored.output.request_sha256,other.receipt().stored.output.request_sha256);assert_ne!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);}
    let inv=inventory(&provider,&good)?;let mut v=good;v["selector"]["scope"]=json!("section");v["selector"]["section_ids"]=inv["inventory"]["section_ids"].clone();assert_ne!(out.receipt().scoped_request_sha256,whitespace_prepare!(&provider,&v)?.receipt().scoped_request_sha256);Ok(())
}
#[test]
fn whitespace_product_current_write_and_five_foreign_scopes_deny_retained_delivery()->TestResult{
    let bytes=raw("A  B")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=wrequest(&s,&bytes)?;let reader=s.provider()?;assert!(whitespace_prepare!(&reader,&v).is_err());let source=reader.import_actual_forms(s.head,4)?;
    assert!(matches!(source.prepare_whitespace_candidate(&reader,query("A  B"),Scope::Document,all(),None,wpolicy(),Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),4),Err(WS::Permission)));
    let out=whitespace_prepare!(&provider,&v)?;let called=Cell::new(false);assert!(out.with_verified_bytes(&reader,5,|_|called.set(true)).is_err());
    for variant in 0..5{let tenant=if variant==4{TenantId::new(Uuid::from_u128(997))?}else{s.reader.tenant_id()};let subject=if variant==3{SubjectDigest::from_authenticated_subject("foreign-whitespace")?}else{s.reader.subject()};let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);let context=rev::RevisionRequestContext::new(tenant,subject);let project=if variant==2{rev::ProjectId::parse("prj_70000000000000000000000000000002")?}else{s.project};let branch=if variant==1{rev::BranchId::parse("brn_70000000000000000000000000000002")?}else{s.branch};
        let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&context,project,branch,DocumentId::parse(if variant==0{"foreign-document"}else{"actual-form-document"})?)?;assert!(out.verify(&other,5).is_err());assert!(out.with_verified_bytes(&other,5,|_|called.set(true)).is_err());}assert!(!called.get());Ok(())
}
#[test]
fn whitespace_product_acl_regrant_quarantine_and_aead_protect_new_and_retained_candidates()->TestResult{
    for mode in 0..3{let bytes=raw("A  B")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=wrequest(&s,&bytes)?;let out=whitespace_prepare!(&provider,&v)?;
        match mode{0=>{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;},1=>{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("WHITESPACE_TEST")?,5)?;},_=>s.blobs.tamper.store(true,Ordering::SeqCst)}
        let called=Cell::new(false);assert!(out.verify(&provider,6).is_err());assert!(out.with_verified_bytes(&provider,6,|_|called.set(true)).is_err());assert!(whitespace_prepare!(&provider,&v).is_err());assert!(!called.get());
        if mode==0{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;out.verify(&provider,8)?;out.with_verified_bytes(&provider,8,|_|())?;}}Ok(())
}
#[test]
fn whitespace_product_prepare_verify_and_delivery_final_head_races_block_consumers()->TestResult{
    for stage in 0..3{let bytes=raw("A  B")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=wrequest(&s,&bytes)?;let b=wire(&v)?;let out=whitespace_prepare!(&provider,&v)?;
        let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,ContentDigest::of(b"whitespace race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation"),ContentDigest::of(b"transaction"))?;
        let repo=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});let bound=StoredFormProvider::bind(&s.artifacts,&repo,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
        match stage{0=>{WProduct::prepare_json(&bound,&b,Default::default(),Default::default(),5)?;},1=>{out.verify(&bound,5)?;},_=>{out.with_verified_bytes(&bound,5,|_|())?;}}
        let calls=repo.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);repo.repository().calls.store(0,Ordering::SeqCst);repo.repository().trigger.store(calls,Ordering::SeqCst);let called=Cell::new(false);
        match stage{0=>assert!(WProduct::prepare_json(&bound,&b,Default::default(),Default::default(),6).is_err()),1=>assert!(out.verify(&bound,6).is_err()),_=>assert!(out.with_verified_bytes(&bound,6,|_|called.set(true)).is_err())}assert!(!called.get());assert_eq!(repo.repository().calls.load(Ordering::SeqCst),calls);}Ok(())
}
#[test]
fn whitespace_product_borrowed_owned_and_json_share_bound_receipts_and_output()->TestResult{
    let bytes=raw("A  B")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=wrequest(&s,&bytes)?;v["operation"]["query"]=json!("A  B");v["operation"]["style_filter"]=json!({"kind":"declared","filter":{"run_character_property":0}});let out=whitespace_prepare!(&provider,&v)?;let source=provider.import_actual_forms(s.head,4)?;
    let filter=Some(Filter::Declared(Declared{run_character_property:Some(0),..Default::default()}));let borrowed=source.prepare_whitespace_candidate(&provider,query("A  B"),Scope::Document,all(),filter.clone(),wpolicy(),Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),4)?;
    assert_eq!(borrowed.verify(&provider,5)?,out.receipt().stored);drop(borrowed);let owned=source.into_whitespace_candidate(&provider,query("A  B"),Scope::Document,all(),filter,wpolicy(),Run::FirstOriginalRunRetainAllRuns,Default::default(),Default::default(),4)?;
    assert_eq!(owned.verify(&provider,5)?,out.receipt().stored);assert_eq!(owned.with_verified_bytes(&provider,5,<[u8]>::to_vec)?,out.with_verified_bytes(&provider,5,<[u8]>::to_vec)?);assert!(matches!(owned.require_current_product_route(&provider,5),Err(WS::RouteUnqualified)));Ok(())
}
#[test]
fn whitespace_product_wrong_source_head_revision_scope_and_index_reject_preparation()->TestResult{
    let bytes=raw("A  B")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=wrequest(&s,&bytes)?;
    for(key,value)in[("expected_head_generation",json!(s.head.generation()+1)),("expected_source_package_sha256",json!("0".repeat(64))),("document_id",json!("foreign-document")),("project_id",json!("prj_70000000000000000000000000000002")),("base_revision",json!(rev::RevisionId::generate().public_id()))]{let mut v=good.clone();v[key]=value;assert!(whitespace_prepare!(&provider,&v).is_err());}
    let inv=inventory(&provider,&good)?;let mut v=good;v["selector"]["scope"]=json!("selection");v["selector"]["range"]=window(&inv,"body_and_notes",0,1)?;v["selector"]["range"]["index_sha256"]=json!("0".repeat(64));assert!(whitespace_prepare!(&provider,&v).is_err());Ok(())
}
#[test]
fn whitespace_product_no_matches_no_change_zero_width_and_ambiguous_inverse_are_distinct()->TestResult{
    let bytes=raw("A  B")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=wrequest(&s,&bytes)?;v["operation"]["query"]=json!("ABSENT");assert!(matches!(whitespace_prepare!(&provider,&v),Err(WE::Stored(WS::Output(Compile::NoMatches)))));
    v["operation"]["query"]=json!("A");assert!(matches!(whitespace_prepare!(&provider,&v),Err(WE::Stored(WS::Output(Compile::NoChange)))));v["operation"]["query"]=json!("^|  ");assert!(matches!(whitespace_prepare!(&provider,&v),Err(WE::Stored(WS::Output(Compile::Selection)))));
    for(text,q)in[("à̕  ","à"),("&#x344;  A","\u{308}")]{let bytes=raw(text)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=wrequest(&s,&bytes)?;v["operation"]["query"]=json!(q);v["operation"]["regex"]=json!(false);assert!(matches!(whitespace_prepare!(&provider,&v),Err(WE::Stored(WS::Output(Compile::Selection)))));}Ok(())
}
#[test]
fn whitespace_product_matching_protected_noops_and_field_cache_are_blocked()->TestResult{
    let tracked=para(1,"A B").replace("charPrIDRef='0'","charPrIDRef='0' charTcId='1'");let bytes=definition::package(&tracked)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=wrequest(&s,&bytes)?;assert!(matches!(whitespace_prepare!(&provider,&v),Err(WE::Stored(WS::Output(Compile::Protection)))));
    let bytes=definition::package(&fixture::body().replace("K K","K  K"))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=wrequest(&s,&bytes)?;v["operation"]["query"]=json!("  ");assert!(whitespace_prepare!(&provider,&v)?.with_verified_bytes(&provider,5,section)??.contains("CACHE FROZEN"));
    v["operation"]["query"]=json!("FROZEN");assert!(matches!(whitespace_prepare!(&provider,&v),Err(WE::Stored(WS::Output(Compile::FieldContent)))));Ok(())
}
#[test]
fn whitespace_product_pattern_match_source_work_response_and_writer_caps_reject_partial_candidates()->TestResult{
    let bytes=raw("A  B  C")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=wrequest(&s,&bytes)?;v["operation"]["query"]=json!("  ");v["operation"]["max_matches"]=json!(1);assert!(matches!(whitespace_prepare!(&provider,&v),Err(WE::Stored(WS::Output(Compile::Search(Search::Limit))))));
    v["operation"]["max_matches"]=json!(100);v["operation"]["query"]=json!("(");assert!(matches!(whitespace_prepare!(&provider,&v),Err(WE::Stored(WS::Output(Compile::Search(Search::Pattern))))));v["operation"]["query"]=json!("  ");
    assert!(WProduct::prepare_json(&provider,&wire(&v)?,SourceSearchLimits::new(Config{result_bytes:1,..Default::default()})?,Default::default(),4).is_err());assert!(matches!(WProduct::prepare_json(&provider,&wire(&v)?,Default::default(),WriterLimits::new(WriterLimitConfig{max_output_bytes:1,..Default::default()})?,4),Err(WE::Stored(WS::Output(Compile::Writer)))));
    assert!(WProduct::prepare_json(&provider,&wire(&v)?,SourceSearchLimits::new(Config{decomposed_scalars:1,..Default::default()})?,Default::default(),4).is_err());Ok(())
}
#[test]
fn whitespace_product_private_data_closed_execution_and_original_head_ingest_are_preserved()->TestResult{
    let bytes=raw("PRIVATE-SOURCE  A")?;let original=ContentDigest::of(&bytes);let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=wrequest(&s,&bytes)?;v["operation"]["query"]=json!("PRIVATE-SOURCE .+");let out=whitespace_prepare!(&provider,&v)?;
    for text in[format!("{out:?}{:?}",out.receipt()),serde_json::to_string(out.receipt())?]{assert!(!text.contains("PRIVATE-SOURCE"));assert!(!text.contains("PRIVATE-UNICODE-KEY"));}
    assert!(matches!(out.require_current_product_route(&provider,5),Err(WE::RouteUnqualified)));assert!(!out.receipt().idempotency_key_claimed&&!out.receipt().full_whitespace_native_cas_execution_publication_authority);assert_eq!(ContentDigest::of(&bytes),original);assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
}
#[test]
fn whitespace_product_many_matches_and_long_sequence_share_one_span_and_protection_map()->TestResult{
    for(text,q,n,expected,ranges)in[("A  B ".repeat(128),"  ",128,"A B ".repeat(128),128),(format!("A{}B"," ".repeat(20000)),".+",1,"A B".to_owned(),1)]{
        let bytes=raw(&text)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=wrequest(&s,&bytes)?;v["operation"]["query"]=json!(q);v["operation"]["max_matches"]=json!(n);
        let out=whitespace_prepare!(&provider,&v)?;exact_output(&bytes,&out.with_verified_bytes(&provider,5,<[u8]>::to_vec)?,&text,&expected)?;let r=&out.receipt().stored.output;assert_eq!(r.search.search().result().matches().len(),n);assert_eq!(r.search.search().match_regions().len(),n);assert_eq!(r.changes.len(),1);assert_eq!(r.changed_scalar_ranges,ranges);
        let xml=hwpx_package::PreservingXmlDocument::parse(section(&bytes)?.as_bytes())?;assert_eq!(r.observed_protection_element_visits,xml.elements().len()*3);}Ok(())
}
