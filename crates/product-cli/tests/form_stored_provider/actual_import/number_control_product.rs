//! Strict source-number values through current stored access; no Native counter or revision commit.
use super::*;
use hwpx_agent_cli::form_product_request::stored_literal_replacement::number_controls::{StoredNumberControlProductRequest as NumberProduct,
    NumberControlProductError as PE,NUMBER_CONTROL_PRODUCT_REQUEST_SCHEMA as NUMBER_SCHEMA};
use hwpx_agent_cli::form_stored_provider::actual_import::literal_search_output::number_controls::StoredNumberControlError as SE;
use hwpx_package::{NumberFormat,document_import::{search::{inspection::SourceControlKind as ControlKind,
    replacement::atoms::number_controls::{ValidatedNumberControlValues as Input,SourceNumberControlError as Core}},
    structure::caption_numbering_sequence::NativeNumberFormatReplacement as Format,structure::caption_text::CaptionTextOutputError as Stream}};
use domain_ir::{ReferenceAuxiliaryLimits,ReferenceAuxiliaryLimitConfig};
const NSTYLE:&str="<hp:autoNumFormat type='DIGIT' userChar='' prefixChar='' suffixChar='' supscript='0'/>";
const FORMATS:[&str;22]=["DIGIT","CIRCLED_DIGIT","ROMAN_CAPITAL","ROMAN_SMALL","LATIN_CAPITAL","LATIN_SMALL","CIRCLED_LATIN_CAPITAL","CIRCLED_LATIN_SMALL",
    "HANGUL_SYLLABLE","CIRCLED_HANGUL_SYLLABLE","HANGUL_JAMO","CIRCLED_HANGUL_JAMO","HANGUL_PHONETIC","IDEOGRAPH","CIRCLED_IDEOGRAPH","DECAGON_CIRCLE","DECAGON_CIRCLE_HANJA","SYMBOL","USER_CHAR","SYMBOL2","IMAGE","2DIGIT"];
fn aux()->Result<ReferenceAuxiliaryLimits,Box<dyn Error>>{Ok(ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig::default())?)}
macro_rules! number_prepare{($p:expr,$v:expr)=>{NumberProduct::prepare_json($p,&wire($v)?,Default::default(),aux()?,Default::default(),4)}}
fn nc(tag:&str,n:i32)->String{format!("<hp:ctrl><hp:{tag} num='{n}' numType='PICTURE'>{NSTYLE}</hp:{tag}></hp:ctrl>")}
fn np(id:u32,run:&str)->String{format!("<hp:p id='{id}' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'>{run}</hp:run></hp:p>")}
fn nraw()->Result<Vec<u8>,Box<dyn Error>>{definition::package(&np(1,&format!("<hp:t>A</hp:t>{}<hp:t>B&#38;</hp:t>{}<hp:t>C</hp:t>",nc("autoNum",2),nc("newNum",3))))}
fn nreview()->String{fixture::body().replace("<hp:t>BODY K K</hp:t>",&format!("<hp:t>BODY K K</hp:t>{}",nc("autoNum",2)))
    .replace("<hp:t>HIDDEN K K<hp:lineBreak/></hp:t>",&format!("<hp:t>HIDDEN K K<hp:lineBreak/></hp:t>{}",nc("autoNum",3)))
    .replace("<hp:t>MEMO K K</hp:t>",&format!("<hp:t>MEMO K K</hp:t>{}",nc("autoNum",4)))}
fn nformat(name:&str)->Value{json!({"kind":"replace","format":name,"user_character":"","prefix":"X","suffix":"Y","superscript":true})}
fn number_request(s:&StoredFixture,raw:&[u8])->Result<Value,Box<dyn Error>>{let mut v=request(s,raw)?;v["schema_version"]=json!(NUMBER_SCHEMA);
    v["operation"]=json!({"kind":"replace_number_controls","control_kind":"auto_number","max_replacements":100,"stored_number":9,"format":{"kind":"preserve"},"review_policy":policy(true,true)});Ok(v)}
fn exact_number(source:&[u8],out:&[u8],old:&str,new:&str)->TestResult{
    assert_eq!(section(out)?,section(source)?.replace(old,new));let mut a=hwpx_package::BoundedZipReader::open(Cursor::new(source),Default::default())?;
    let mut b=hwpx_package::BoundedZipReader::open(Cursor::new(out),Default::default())?;assert_eq!(a.entries().len(),b.entries().len());
    for i in 0..a.entries().len(){let path=a.entries()[i].path.clone();if path.as_str()=="Contents/section0.xml"{continue;}let j=b.entries().iter().position(|e|e.path==path).ok_or("part")?;assert_eq!(a.read_entry(i)?,b.read_entry(j)?);}Ok(())
}
#[test]
fn number_product_auto_i32_values_and_request_drop_preserve_original_stream()->TestResult{
    let bytes=nraw()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for n in[9,0,-1,i32::MIN,i32::MAX]{let mut v=number_request(&s,&bytes)?;v["operation"]["stored_number"]=json!(n);let out=number_prepare!(&provider,&v)?;drop(v);out.verify(&provider,5)?;
        exact_number(&bytes,&out.with_verified_bytes(&provider,5,<[u8]>::to_vec)?,"autoNum num='2'",&format!("autoNum num='{n}'"))?;assert_eq!(out.receipt().capability_id,"search.replace_control");
        assert!(!out.receipt().stored.output.native_recalculation_full_search_service_or_execution_authority);}Ok(())
}
#[test]
fn number_product_restart_changes_only_selected_kind_and_keeps_bookmark_reference()->TestResult{
    let bytes=definition::package(&np(1,&format!("<hp:t>A</hp:t>{}<hp:ctrl><hp:bookmark name='KEEP'/></hp:ctrl>{}<hp:t>B</hp:t>",nc("autoNum",2),nc("newNum",3))))?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=number_request(&s,&bytes)?;v["operation"]["control_kind"]=json!("new_number");
    let out=number_prepare!(&provider,&v)?;exact_number(&bytes,&out.with_verified_bytes(&provider,5,<[u8]>::to_vec)?,"newNum num='3'","newNum num='9'")?;Ok(())
}
#[test]
fn number_product_all_twenty_two_typed_formats_are_read_back_and_fingerprint_distinct()->TestResult{
    let bytes=nraw()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut hashes=BTreeSet::new();
    for name in FORMATS{let mut v=number_request(&s,&bytes)?;v["operation"]["format"]=nformat(name);let out=number_prepare!(&provider,&v)?;let text=out.with_verified_bytes(&provider,5,section)??;
        assert!(text.contains(&format!("type='{name}'"))&&text.contains("prefixChar='X'")&&text.contains("supscript='1'"));assert!(text.contains(&nc("newNum",3)));hashes.insert(out.receipt().stored.values_sha256);}
    assert_eq!(hashes.len(),22);Ok(())
}
#[test]
fn number_product_four_review_policies_exclude_before_caps_and_preserve_cache_metadata()->TestResult{
    let bytes=definition::package(&nreview())?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for hidden in[false,true]{for memo in[false,true]{let mut v=number_request(&s,&bytes)?;let count=1+usize::from(hidden)+usize::from(memo);v["operation"]["review_policy"]=policy(hidden,memo);v["operation"]["max_replacements"]=json!(count);
        let out=number_prepare!(&provider,&v)?;assert_eq!(out.receipt().stored.output.selected_controls,count);assert_eq!(out.receipt().stored.output.stream.number_sequence.requested_events,3);
        let mut expected=section(&bytes)?.replace("autoNum num='2'","autoNum num='9'");if hidden{expected=expected.replace("autoNum num='3'","autoNum num='9'");}if memo{expected=expected.replace("autoNum num='4'","autoNum num='9'");}
        assert_eq!(out.with_verified_bytes(&provider,5,section)??,expected);assert!(expected.contains("CACHE FROZEN")&&expected.contains("PRIVATE-AUTHOR"));
    }}Ok(())
}
#[test]
fn number_product_discovery_supplies_four_scopes_and_cross_block_selection()->TestResult{
    let bytes=definition::package(&(np(1,&format!("<hp:t>A</hp:t>{}<hp:t>B</hp:t>",nc("autoNum",2)))+&np(2,&format!("<hp:t>C</hp:t>{}<hp:t>D</hp:t>",nc("autoNum",4)))))?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=number_request(&s,&bytes)?;let inv=inventory(&provider,&good)?;
    let blocks=inv["inventory"]["blocks"].as_array().ok_or("blocks")?;let first=&blocks[0];let last=blocks.iter().filter(|b|b["paragraph_handle"]==first["paragraph_handle"]).last().ok_or("last block")?;
    let sha:[u8;32]=serde_json::from_value(inv["inventory"]["index"]["index_sha256"].clone())?;
    let range=json!({"coordinate_space":"index_nfc_unicode_scalars","index_sha256":hex::encode(sha),"start":{"paragraph_handle":first["paragraph_handle"],"block_index":first["block_index"],"normalized_scalar":0},
        "end":{"paragraph_handle":last["paragraph_handle"],"block_index":last["block_index"],"normalized_scalar":last["normalized_scalars"]}});
    let node=inv["inventory"]["nodes"].as_array().ok_or("nodes")?.iter().find(|n|n["source_handle"]==first["paragraph_handle"]).ok_or("node")?;
    for(scope,count)in[("document",2),("section",2),("node_set",1),("selection",1)]{let mut v=good.clone();v["selector"]["scope"]=json!(scope);
        match scope{"section"=>v["selector"]["section_ids"]=inv["inventory"]["section_ids"].clone(),"node_set"=>v["selector"]["range"]=json!({"node_ids":[node["node_id"].clone()]}),"selection"=>v["selector"]["range"]=range.clone(),_=>{}}
        let out=number_prepare!(&provider,&v)?;assert_eq!(out.receipt().stored.output.selected_controls,count);let after=out.with_verified_bytes(&provider,5,section)??;assert!(after.contains("autoNum num='9'"));assert_eq!(after.contains("autoNum num='4'"),count==1);
    }Ok(())
}
#[test]
fn number_product_noop_subset_preserves_original_lexemes_and_anchor_order()->TestResult{
    let first=nc("autoNum",9).replace("num='9'","num='009'");let bytes=definition::package(&np(1,&format!("<hp:t>A</hp:t>{first}{}<hp:t>B</hp:t>",nc("autoNum",2))))?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=number_request(&s,&bytes)?;let out=number_prepare!(&provider,&v)?;let r=&out.receipt().stored.output;
    assert_eq!((r.selected_controls,r.changed_controls),(2,1));assert_eq!(r.changes[0].source_control_anchor,r.search.controls()[1].control_anchor);
    exact_number(&bytes,&out.with_verified_bytes(&provider,5,<[u8]>::to_vec)?,"autoNum num='2'","autoNum num='9'")?;Ok(())
}
#[test]
fn number_product_strict_envelope_operation_and_required_policy_reject_before_reads()->TestResult{
    let bytes=nraw()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=number_request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();let mut bad=Vec::new();
    for key in["schema_version","idempotency_key","project_id","document_id","base_revision","expected_head_generation","expected_source_package_sha256","plan_id","selector","operation"]{let mut v=good.clone();v.as_object_mut().ok_or("root")?.remove(key);bad.push(v);}
    for key in["kind","control_kind","max_replacements","stored_number","format","review_policy"]{let mut v=good.clone();v["operation"].as_object_mut().ok_or("operation")?.remove(key);bad.push(v);}
    for(key,value)in[("kind",json!("replace_controls")),("max_replacements",json!(0)),("max_replacements",json!(4097)),("max_replacements",json!(-1)),("stored_number",json!(2147483648_i64)),("stored_number",json!(-2147483649_i64)),("stored_number",json!(1.5)),("stored_number",json!("9")),("stored_number",json!(null)),
        ("category",json!("PAGE")),("output",json!([])),("query",json!("autoNum")),("replacement",json!("9")),("regex",json!(true)),("style_filter",json!({})),("preview_only",json!(true)),("direction",json!("all")),("locale",json!("ko")),("approved",json!(true))]{let mut v=good.clone();v["operation"][key]=value;bad.push(v);}
    for policy in[json!({}),json!({"include_hidden_explanations":true}),json!({"include_hidden_explanations":true,"include_memo_bodies":true,"approved":true})]{let mut v=good.clone();v["operation"]["review_policy"]=policy;bad.push(v);}
    for v in bad{assert!(matches!(number_prepare!(&provider,&v),Err(PE::Request)));}assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn number_product_nested_format_is_strict_and_invalid_characters_fail_before_reads()->TestResult{
    let bytes=nraw()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=number_request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();
    let mut bad=vec![json!(null),json!("preserve"),json!({}),json!({"kind":"preserve","ignored":true}),json!({"kind":"replace"}),json!({"kind":"xml","value":"<hp:autoNum/>"})];
    for key in["format","user_character","prefix","suffix","superscript"]{let mut format=nformat("DIGIT");format.as_object_mut().ok_or("format")?.remove(key);bad.push(format);}
    for(key,value)in[("format",json!("digit")),("format",json!("UNKNOWN")),("format",json!(null)),("user_character",json!(1)),("prefix",json!(null)),("suffix",json!(false)),("superscript",json!(1)),("xml",json!("raw")),("prefix",json!("bad\u{0}")),("suffix",json!("bad\u{1}"))]{let mut format=nformat("DIGIT");format[key]=value;bad.push(format);}
    for format in bad{let mut v=good.clone();v["operation"]["format"]=format;assert!(matches!(number_prepare!(&provider,&v),Err(PE::Request)));}assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn number_product_other_control_kinds_are_unqualified_before_source_reads()->TestResult{
    let bytes=nraw()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=number_request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();
    for kind in["tab","line_break","table","field_begin","field_end","footnote","bookmark","section_properties","unknown_character"]{let mut v=good.clone();v["operation"]["control_kind"]=json!(kind);assert!(matches!(number_prepare!(&provider,&v),Err(PE::UnsupportedKind)));}
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn number_product_invalid_selectors_and_escaped_duplicate_keys_fail_before_reads()->TestResult{
    let bytes=nraw()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=number_request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();let mut bad=Vec::new();
    for selector in[json!([]),json!({"scope":"document"}),json!({"revision_id":good["base_revision"],"scope":"document","range":null}),json!({"revision_id":good["base_revision"],"scope":"section","section_ids":[]})]{let mut v=good.clone();v["selector"]=selector;bad.push(wire(&v)?);}
    let text=serde_json::to_string(&good)?;
    for(from,to)in[("\"stored_number\":9","\"stored_number\":9,\"stored_nu\\u006dber\":10"),("\"kind\":\"preserve\"","\"kind\":\"preserve\",\"ki\\u006ed\":\"replace\""),("\"scope\":\"document\"","\"scope\":\"document\",\"sco\\u0070e\":\"selection\"")]{let changed=text.replace(from,to);assert_ne!(changed,text);bad.push(changed.into_bytes());}
    for b in bad{assert!(matches!(NumberProduct::prepare_json(&provider,&b,Default::default(),aux()?,Default::default(),4),Err(PE::Request)));}assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn number_product_exact_16k_escaped_format_and_canonical_binding_are_distinct_from_raw()->TestResult{
    let bytes=nraw()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut good=number_request(&s,&bytes)?;good["operation"]["format"]=nformat("DIGIT");let out=number_prepare!(&provider,&good)?;
    let mut padded=wire(&good)?;padded.resize(16*1024,b' ');let other=NumberProduct::prepare_json(&provider,&padded,Default::default(),aux()?,Default::default(),4)?;
    assert_ne!(out.receipt().raw_request_sha256,other.receipt().raw_request_sha256);assert_eq!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);padded.push(b' ');
    assert!(matches!(NumberProduct::prepare_json(&provider,&padded,Default::default(),aux()?,Default::default(),4),Err(PE::Limit)));
    let text=serde_json::to_string(&good)?;let escaped=text.replace("\"prefix\":\"X\"","\"prefix\":\"\\u0058\"");assert_ne!(escaped,text);let other=NumberProduct::prepare_json(&provider,escaped.as_bytes(),Default::default(),aux()?,Default::default(),4)?;
    assert_ne!(out.receipt().raw_request_sha256,other.receipt().raw_request_sha256);assert_eq!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);Ok(())
}
#[test]
fn number_product_legacy_schemas_and_operations_are_mutually_rejected_without_reads()->TestResult{
    use hwpx_agent_cli::form_product_request::stored_literal_replacement::{controls::StoredControlProductRequest as Control,whitespace::StoredWhitespaceProductRequest as Whitespace,
        width::StoredWidthProductRequest as Width,case::StoredCaseProductRequest as Case,StoredLiteralReplacementProductRequest as Literal};
    let bytes=nraw()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=number_request(&s,&bytes)?;let b=wire(&good)?;let before=s.metadata.audit_events()?.len();
    assert!(Control::prepare_json(&provider,&b,Default::default(),Default::default(),4).is_err());assert!(Whitespace::prepare_json(&provider,&b,Default::default(),Default::default(),4).is_err());assert!(Width::prepare_json(&provider,&b,Default::default(),Default::default(),4).is_err());
    assert!(Case::prepare_json(&provider,&b,Default::default(),Default::default(),4).is_err());assert!(UnicodeProduct::prepare_json(&provider,&b,Default::default(),Default::default(),4).is_err());assert!(Literal::prepare_json(&provider,&b,Default::default(),Default::default(),4).is_err());assert!(Product::prepare_json(&provider,&b,Default::default(),Default::default(),4).is_err());assert!(Discovery::prepare_json(&provider,&b,Default::default(),4).is_err());
    for mut v in[request(&s,&bytes)?,envelope(&s,&bytes)?]{v["schema_version"]=json!(NUMBER_SCHEMA);assert!(matches!(number_prepare!(&provider,&v),Err(PE::Request)));}assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn number_product_kind_value_format_policy_cap_key_plan_and_scope_are_fingerprint_bound()->TestResult{
    let bytes=nraw()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=number_request(&s,&bytes)?;let out=number_prepare!(&provider,&good)?;
    for(key,value)in[("idempotency_key",json!("OTHER-KEY")),("plan_id",json!("other-plan"))]{let mut v=good.clone();v[key]=value;let other=number_prepare!(&provider,&v)?;assert_ne!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);assert_ne!(out.receipt().scoped_request_sha256,other.receipt().scoped_request_sha256);assert_eq!(out.receipt().stored.output.stream.content.output.output_package_sha256,other.receipt().stored.output.stream.content.output.output_package_sha256);}
    for(key,value)in[("control_kind",json!("new_number")),("stored_number",json!(8)),("format",nformat("ROMAN_CAPITAL")),("review_policy",policy(false,false)),("max_replacements",json!(1))]{let mut v=good.clone();v["operation"][key]=value;let other=number_prepare!(&provider,&v)?;assert_ne!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);assert_ne!(out.receipt().stored.output.request_sha256,other.receipt().stored.output.request_sha256);}
    let inv=inventory(&provider,&good)?;let mut v=good;v["selector"]["scope"]=json!("section");v["selector"]["section_ids"]=inv["inventory"]["section_ids"].clone();assert_ne!(out.receipt().scoped_request_sha256,number_prepare!(&provider,&v)?.receipt().scoped_request_sha256);Ok(())
}
#[test]
fn number_product_current_write_and_five_foreign_scopes_deny_retained_delivery()->TestResult{
    let bytes=nraw()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=number_request(&s,&bytes)?;let reader=s.provider()?;assert!(number_prepare!(&reader,&v).is_err());let source=reader.import_actual_forms(s.head,4)?;
    let input=Input::new(ControlKind::AutoNumber,9,Format::Preserve,Default::default(),aux()?)?;assert!(matches!(source.prepare_number_control_candidate(&reader,Scope::Document,all(),100,&input,Default::default(),4),Err(SE::Permission)));
    let out=number_prepare!(&provider,&v)?;let called=Cell::new(false);assert!(out.with_verified_bytes(&reader,5,|_|called.set(true)).is_err());
    for variant in 0..5{let tenant=if variant==4{TenantId::new(Uuid::from_u128(997))?}else{s.reader.tenant_id()};let subject=if variant==3{SubjectDigest::from_authenticated_subject("foreign-number-product")?}else{s.reader.subject()};let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);let context=rev::RevisionRequestContext::new(tenant,subject);let project=if variant==2{rev::ProjectId::parse("prj_70000000000000000000000000000002")?}else{s.project};let branch=if variant==1{rev::BranchId::parse("brn_70000000000000000000000000000002")?}else{s.branch};
        let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&context,project,branch,DocumentId::parse(if variant==0{"foreign-document"}else{"actual-form-document"})?)?;assert!(out.verify(&other,5).is_err());assert!(out.with_verified_bytes(&other,5,|_|called.set(true)).is_err());}assert!(!called.get());Ok(())
}
#[test]
fn number_product_acl_regrant_quarantine_and_aead_protect_new_and_retained_candidates()->TestResult{
    for mode in 0..3{let bytes=nraw()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=number_request(&s,&bytes)?;let out=number_prepare!(&provider,&v)?;
        match mode{0=>{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;},1=>{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("NUMBER_PRODUCT_TEST")?,5)?;},_=>s.blobs.tamper.store(true,Ordering::SeqCst)}
        let called=Cell::new(false);assert!(out.verify(&provider,6).is_err());assert!(out.with_verified_bytes(&provider,6,|_|called.set(true)).is_err());assert!(number_prepare!(&provider,&v).is_err());assert!(!called.get());
        if mode==0{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;out.verify(&provider,8)?;out.with_verified_bytes(&provider,8,|_|())?;}}Ok(())
}
#[test]
fn number_product_prepare_verify_and_delivery_final_head_races_block_consumers()->TestResult{
    for stage in 0..3{let bytes=nraw()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=number_request(&s,&bytes)?;let b=wire(&v)?;let out=number_prepare!(&provider,&v)?;
        let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,ContentDigest::of(b"number race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation"),ContentDigest::of(b"transaction"))?;
        let repo=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});let bound=StoredFormProvider::bind(&s.artifacts,&repo,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
        match stage{0=>{NumberProduct::prepare_json(&bound,&b,Default::default(),aux()?,Default::default(),5)?;},1=>{out.verify(&bound,5)?;},_=>{out.with_verified_bytes(&bound,5,|_|())?;}}
        let calls=repo.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);repo.repository().calls.store(0,Ordering::SeqCst);repo.repository().trigger.store(calls,Ordering::SeqCst);let called=Cell::new(false);
        match stage{0=>assert!(NumberProduct::prepare_json(&bound,&b,Default::default(),aux()?,Default::default(),6).is_err()),1=>assert!(out.verify(&bound,6).is_err()),_=>assert!(out.with_verified_bytes(&bound,6,|_|called.set(true)).is_err())}assert!(!called.get());assert_eq!(repo.repository().calls.load(Ordering::SeqCst),calls);
    }Ok(())
}
#[test]
fn number_product_borrowed_owned_and_json_share_exact_receipts_and_output()->TestResult{
    let bytes=nraw()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=number_request(&s,&bytes)?;let out=number_prepare!(&provider,&v)?;
    let source=provider.import_actual_forms(s.head,4)?;let input=Input::new(ControlKind::AutoNumber,9,Format::Preserve,Default::default(),aux()?)?;
    let borrowed=source.prepare_number_control_candidate(&provider,Scope::Document,all(),100,&input,Default::default(),4)?;assert_eq!(borrowed.verify(&provider,5)?,out.receipt().stored);drop(borrowed);
    let owned=source.into_number_control_candidate(&provider,Scope::Document,all(),100,&input,Default::default(),4)?;assert_eq!(owned.verify(&provider,5)?,out.receipt().stored);
    assert_eq!(owned.with_verified_bytes(&provider,5,<[u8]>::to_vec)?,out.with_verified_bytes(&provider,5,<[u8]>::to_vec)?);assert!(matches!(owned.require_current_product_route(&provider,5),Err(SE::RouteUnqualified)));Ok(())
}
#[test]
fn number_product_wrong_source_head_revision_scope_and_index_reject_preparation()->TestResult{
    let bytes=nraw()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=number_request(&s,&bytes)?;
    for(key,value)in[("expected_head_generation",json!(s.head.generation()+1)),("expected_source_package_sha256",json!("0".repeat(64))),("document_id",json!("foreign-document")),("project_id",json!("prj_70000000000000000000000000000002")),("base_revision",json!(rev::RevisionId::generate().public_id()))]{let mut v=good.clone();v[key]=value;assert!(number_prepare!(&provider,&v).is_err());}
    let inv=inventory(&provider,&good)?;let mut v=good;v["selector"]["scope"]=json!("selection");v["selector"]["range"]=window(&inv,"body_and_notes",0,1)?;v["selector"]["range"]["index_sha256"]=json!("0".repeat(64));assert!(number_prepare!(&provider,&v).is_err());Ok(())
}
#[test]
fn number_product_no_matches_nochange_and_empty_selection_are_distinct()->TestResult{
    let bytes=definition::package(&np(1,&format!("<hp:t>A</hp:t>{}<hp:t>B</hp:t>",nc("autoNum",2))))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=number_request(&s,&bytes)?;
    let mut v=good.clone();v["operation"]["control_kind"]=json!("new_number");assert!(matches!(number_prepare!(&provider,&v),Err(PE::Stored(SE::Output(Core::Output(Compile::NoMatches))))));
    v=good.clone();v["operation"]["stored_number"]=json!(2);assert!(matches!(number_prepare!(&provider,&v),Err(PE::Stored(SE::Output(Core::Stream(Stream::NoChange))))));
    let inv=inventory(&provider,&good)?;let mut v=good;v["selector"]["scope"]=json!("selection");v["selector"]["range"]=window(&inv,"body_and_notes",0,0)?;assert!(matches!(number_prepare!(&provider,&v),Err(PE::Stored(SE::Output(Core::Output(Compile::NoMatches))))));Ok(())
}
#[test]
fn number_product_protected_noops_and_memo_cache_do_not_gain_edit_authority()->TestResult{
    let bytes=definition::package(&np(1,&format!("<hp:t>A</hp:t>{}<hp:t>B</hp:t>",nc("autoNum",2).replace("<hp:autoNum ","<hp:autoNum lock='1' "))))?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=number_request(&s,&bytes)?;v["operation"]["stored_number"]=json!(2);assert!(matches!(number_prepare!(&provider,&v),Err(PE::Stored(SE::Output(Core::Output(Compile::Protection))))));
    let bytes=definition::package(&nreview().replace("<hp:t>CACHE FROZEN</hp:t>",&format!("<hp:t>CACHE FROZEN</hp:t>{}",nc("autoNum",8))))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=number_request(&s,&bytes)?;
    assert!(matches!(number_prepare!(&provider,&v),Err(PE::Stored(SE::Output(Core::Output(Compile::FieldContent))))));Ok(())
}
#[test]
fn number_product_match_work_response_format_and_writer_limits_do_not_return_partial_candidates()->TestResult{
    let bytes=definition::package(&np(1,&format!("<hp:t>A</hp:t>{}{}<hp:t>B</hp:t>",nc("autoNum",2),nc("autoNum",3))))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=number_request(&s,&bytes)?;v["operation"]["max_replacements"]=json!(1);
    assert!(number_prepare!(&provider,&v).is_err());v["operation"]["max_replacements"]=json!(100);
    assert!(NumberProduct::prepare_json(&provider,&wire(&v)?,SourceSearchLimits::new(Config{result_bytes:1,..Default::default()})?,aux()?,Default::default(),4).is_err());
    assert!(NumberProduct::prepare_json(&provider,&wire(&v)?,SourceSearchLimits::new(Config{decomposed_scalars:1,..Default::default()})?,aux()?,Default::default(),4).is_err());
    let before=s.metadata.audit_events()?.len();v["operation"]["format"]=nformat("DIGIT");let tight=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig{text_bytes:1,..Default::default()})?;v["operation"]["format"]["prefix"]=json!("long");
    assert!(matches!(NumberProduct::prepare_json(&provider,&wire(&v)?,Default::default(),tight,Default::default(),4),Err(PE::Request)));assert_eq!(s.metadata.audit_events()?.len(),before);
    v["operation"]["format"]=json!({"kind":"preserve"});assert!(matches!(NumberProduct::prepare_json(&provider,&wire(&v)?,Default::default(),aux()?,WriterLimits::new(WriterLimitConfig{max_output_bytes:1,..Default::default()})?,4),Err(PE::Stored(SE::Output(Core::Stream(Stream::Writer))))));Ok(())
}
#[test]
fn number_product_private_affixes_closed_route_original_head_and_ingest_are_preserved()->TestResult{
    let bytes=nraw()?;let original=ContentDigest::of(&bytes);let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=number_request(&s,&bytes)?;v["operation"]["format"]=nformat("USER_CHAR");v["operation"]["format"]["user_character"]=json!("PRIVATE-USER");v["operation"]["format"]["prefix"]=json!("PRIVATE-PREFIX");let out=number_prepare!(&provider,&v)?;
    for text in[format!("{out:?}{:?}",out.receipt()),serde_json::to_string(out.receipt())?]{assert!(!text.contains("PRIVATE-PREFIX"));assert!(!text.contains("PRIVATE-USER"));assert!(!text.contains("PRIVATE-UNICODE-KEY"));}
    assert!(matches!(out.require_current_product_route(&provider,5),Err(PE::RouteUnqualified)));assert!(!out.receipt().idempotency_key_claimed&&!out.receipt().native_counter_cas_execution_publication_authority);
    assert_eq!(ContentDigest::of(&bytes),original);assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
}
#[test]
fn number_product_many_controls_share_part_guard_and_bounded_node_aggregation()->TestResult{
    let bytes=definition::package(&np(1,&format!("<hp:t>A</hp:t>{}<hp:t>B</hp:t>",nc("autoNum",2).repeat(256))))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=number_request(&s,&bytes)?;v["operation"]["max_replacements"]=json!(256);let out=number_prepare!(&provider,&v)?;
    out.verify(&provider,5)?;exact_number(&bytes,&out.with_verified_bytes(&provider,5,<[u8]>::to_vec)?,"autoNum num='2'","autoNum num='9'")?;let r=&out.receipt().stored.output;assert_eq!(r.changed_controls,256);assert_eq!(r.observed_protection_parts,1);
    let xml=hwpx_package::PreservingXmlDocument::parse(section(&bytes)?.as_bytes())?;assert_eq!(r.observed_protection_element_visits,xml.elements().len()*4);Ok(())
}
#[test]
fn number_product_validated_values_are_not_a_source_or_limit_override_token()->TestResult{
    let bytes=nraw()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=number_request(&s,&bytes)?;let out=number_prepare!(&provider,&v)?;
    let source=provider.import_actual_forms(s.head,4)?;let other=provider.import_actual_forms(s.head,4)?;let proof=source.imported().reconstruct_source_for_verification(&bytes)?;
    let input=Input::new(ControlKind::AutoNumber,9,Format::Preserve,Default::default(),aux()?)?;assert_eq!(input.values_sha256(),out.receipt().stored.values_sha256);assert_eq!(input.kind(),ControlKind::AutoNumber);
    assert_eq!(input.request_sha256(out.receipt().stored.output.search.request_sha256())?,out.receipt().stored.output.request_sha256);
    assert!(matches!(input.lower(&proof,other.imported(),Scope::Document,all(),100,Default::default()),Err(Core::Output(Compile::Source))));
    let tight=Input::new(ControlKind::AutoNumber,9,Format::Preserve,SourceSearchLimits::new(Config{result_bytes:1,..Default::default()})?,aux()?)?;assert!(tight.lower(&proof,source.imported(),Scope::Document,all(),100,Default::default()).is_err());
    let private=Input::new(ControlKind::AutoNumber,9,Format::Replace{format:NumberFormat::Digit,user_character:"",prefix:"PRIVATE-INPUT",suffix:"",superscript:false},Default::default(),aux()?)?;assert!(!format!("{private:?}").contains("PRIVATE-INPUT"));Ok(())
}
#[test]
fn number_product_missing_format_is_preserved_but_not_inferred_for_replace()->TestResult{
    let bytes=definition::package(&np(1,"<hp:t>A</hp:t><hp:ctrl><hp:newNum num='3' numType='PICTURE'/></hp:ctrl><hp:t>B</hp:t>"))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=number_request(&s,&bytes)?;v["operation"]["control_kind"]=json!("new_number");
    let out=number_prepare!(&provider,&v)?;exact_number(&bytes,&out.with_verified_bytes(&provider,5,<[u8]>::to_vec)?,"newNum num='3'","newNum num='9'")?;v["operation"]["format"]=nformat("DIGIT");assert!(matches!(number_prepare!(&provider,&v),Err(PE::Stored(SE::Output(Core::Stream(Stream::Selection))))));Ok(())
}
#[test]
fn number_product_review_paragraph_limit_cannot_hide_behind_zero_extra_controls()->TestResult{
    use hwpx_package::document_import::{structure::review::ImportedDocumentReviewBodies,reference_targets::numbering::{ImportedCaptionNumbering,CaptionNumberingImportError as ImportError}};
    let body=fixture::body().replace("<hp:t>BODY K K</hp:t>",&format!("<hp:t>BODY K K</hp:t>{}",nc("autoNum",2)));let bytes=definition::package(&body)?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let source=provider.import_actual_forms(s.head,4)?;let review=ImportedDocumentReviewBodies::import(source.imported())?;
    let tight=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig{items_per_kind:1,..Default::default()})?;
    assert!(ImportedCaptionNumbering::import(source.imported().body_structure(),tight).is_ok());assert!(matches!(ImportedCaptionNumbering::import_review_bound(source.imported(),&review,tight),Err(ImportError::Limit)));
    let v=number_request(&s,&bytes)?;assert!(NumberProduct::prepare_json(&provider,&wire(&v)?,Default::default(),tight,Default::default(),4).is_err());number_prepare!(&provider,&v)?;Ok(())
}
