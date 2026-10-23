//! Whole-paragraph reference candidates through current stored source and strict JSON, not execution.
use super::*;
use hwpx_agent_cli::form_product_request::stored_literal_replacement::paragraph_styles::{StoredParagraphStyleProductRequest as ParaProduct,
    ParagraphStyleProductError as PE,PARAGRAPH_STYLE_PRODUCT_REQUEST_SCHEMA as PARA_SCHEMA};
use hwpx_agent_cli::form_stored_provider::actual_import::literal_search_output::paragraph_styles::StoredParagraphStyleError as PS;
use hwpx_package::document_import::search::{reviews::selector::styles::SourceReviewStyleFilter as Filter,inspection::SourceDeclaredStyleFilter as Declared,
    SourceSearchError as Search,replacement::atoms::styles::paragraphs::{SourceParagraphStyleReplacementError as PC,SourceParagraphStyleTarget as Target,SourceParagraphStyleExtent as Extent}};
#[allow(dead_code)] #[path="../../../../hwpx-package/tests/support/search_definition_fixture.rs"] mod definition;
#[allow(dead_code)] #[path="../../../../hwpx-package/tests/support/document_import_catalog_fixture.rs"] mod archive;
const EXTENT:Extent=Extent::WholeMatchedParagraphWithinScope;
macro_rules! para_prepare{($p:expr,$v:expr)=>{ParaProduct::prepare_json($p,&wire($v)?,Default::default(),Default::default(),4)}}
fn filter()->Filter{Filter::Declared(Declared {paragraph_property:Some(0),..Default::default()})}
fn request(s:&StoredFixture,raw:&[u8])->Result<Value,Box<dyn Error>> {let mut v=envelope(s,raw)?;v["schema_version"]=json!(PARA_SCHEMA);v["operation"]=json!({
    "kind":"replace_paragraph_style_reference","query":"K","regex":false,"case_sensitive":true,"whole_word":false,"max_replacements":100,
    "style_filter":{"kind":"declared","filter":{"paragraph_property":0}},"replacement":{"axis":"paragraph_property","declaration_id":1},
    "extent":"whole_matched_paragraph_within_scope","review_policy":policy(true,true)});Ok(v)}
fn p(id:u32,text:&str)->String{format!("<hp:p id='{id}' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'><hp:t>{text}</hp:t></hp:run></hp:p>")}
fn raw(text:&str)->Result<Vec<u8>,Box<dyn Error>> {definition::package(&p(1,text))}
fn review_raw()->Result<Vec<u8>,Box<dyn Error>> {definition::package(&fixture::body().replace("BODY K K","BODY")
    .replace("<hp:p id='1'>","<hp:p id='1' paraPrIDRef='0' styleIDRef='0'>")
    .replace("<hp:p id='11'>","<hp:p id='11' paraPrIDRef='0' styleIDRef='0'>").replace("<hp:p id='12'>","<hp:p id='12' paraPrIDRef='0' styleIDRef='0'>"))}
fn reference_number(raw:&str)->Result<u32,Box<dyn Error>> {
    // Read unsigned XML reference values independently without a new crate dependency.
    let mut decoded=String::new();let mut tail=raw;
    while let Some(start)=tail.find('&') {
        decoded.push_str(&tail[..start]);let entity=&tail[start+1..];let end=entity.find(';').ok_or("unterminated numeric reference")?;
        let token=&entity[..end];let scalar=if let Some(hex)=token.strip_prefix("#x"){u32::from_str_radix(hex,16)?}
            else if let Some(decimal)=token.strip_prefix('#'){decimal.parse::<u32>()?}else{return Err("non-numeric reference".into())};
        decoded.push(char::from_u32(scalar).ok_or("invalid numeric scalar")?);tail=&entity[end+1..];
    }
    decoded.push_str(tail);Ok(decoded.parse()?)
}
fn references(bytes:&[u8])->Result<Vec<(u32,Option<u32>,Option<u32>)>,Box<dyn Error>> {
    let raw=section(bytes)?;let xml=hwpx_package::PreservingXmlDocument::parse(raw.as_bytes())?;let mut out=Vec::new();
    for node in xml.elements().iter().filter(|n|n.name().namespace()==Some(hwpx_package::HANCOM_2020_PARAGRAPH_NAMESPACE)&&n.name().local_name()=="p") {
        let get=|name:&str|->Result<Option<u32>,Box<dyn Error>>{Ok(node.attributes().iter().find(|a|a.name().namespace().is_none()&&a.name().local_name()==name)
            .map(|a|reference_number(&raw[a.value_span().start()..a.value_span().end()])).transpose()?)};
        out.push((get("id")?.ok_or("paragraph id")?,get("paraPrIDRef")?,get("styleIDRef")?));
    }Ok(out)
}
#[test]
fn paragraph_product_both_axes_change_only_selected_original_attribute_values()->TestResult {
    assert_eq!(reference_number("&#48;")?,0);assert_eq!(reference_number("&#x31;2")?,12);assert!(reference_number("&amp;").is_err());assert!(reference_number("&#x110000;").is_err());
    let bytes=raw("A K B")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for(axis,key)in[("paragraph_property","paraPrIDRef"),("paragraph_style","styleIDRef")] {
        let mut v=request(&s,&bytes)?;v["operation"]["replacement"]["axis"]=json!(axis);let out=para_prepare!(&provider,&v)?;let after=out.with_verified_bytes(&provider,5,<[u8]>::to_vec)?;
        assert_eq!(section(&after)?,section(&bytes)?.replacen(&format!("{key}='0'"),&format!("{key}='1'"),1));
        assert_eq!(out.receipt().stored.output.matched_paragraphs,1);assert_eq!(out.receipt().stored.output.changes.len(),1);
        assert_eq!(out.receipt().stored.output.extent,EXTENT);assert_eq!(out.receipt().capability_id,"search.replace_style");
    }Ok(())
}
#[test]
fn paragraph_product_discovery_four_scopes_and_owned_request_drop_preserve_full_paragraph_extent()->TestResult {
    let bytes=review_raw()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=request(&s,&bytes)?;let inv=inventory(&provider,&good)?;
    let range=window(&inv,"memo_body",0,8)?;let node=inv["inventory"]["nodes"].as_array().ok_or("nodes")?.iter().find(|n|n["source_handle"]==range["start"]["paragraph_handle"]).ok_or("node")?;
    for axis in["paragraph_property","paragraph_style"] {for(scope,total)in[("document",2),("section",2),("node_set",1),("selection",1)] {
        let mut v=good.clone();v["operation"]["replacement"]["axis"]=json!(axis);v["selector"]["scope"]=json!(scope);
        match scope {"section"=>v["selector"]["section_ids"]=inv["inventory"]["section_ids"].clone(),"node_set"=>v["selector"]["range"]=json!({"node_ids":[node["node_id"].clone()]}),"selection"=>v["selector"]["range"]=range.clone(),_=>{}}
        let out=para_prepare!(&provider,&v)?;drop(v);out.verify(&provider,5)?;assert_eq!(out.receipt().stored.output.matched_paragraphs,total);
        let after=out.with_verified_bytes(&provider,5,<[u8]>::to_vec)?;assert_eq!(references(&after)?.iter().filter(|(_,p,s)|if axis=="paragraph_property"{*p==Some(1)}else{*s==Some(1)}).count(),total);
        assert!(section(&after)?.contains("CACHE FROZEN"));
    }}Ok(())
}
#[test]
fn paragraph_product_partial_selector_is_not_widened_even_under_explicit_whole_paragraph_policy()->TestResult {
    let bytes=review_raw()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=request(&s,&bytes)?;let inv=inventory(&provider,&v)?;
    v["selector"]["scope"]=json!("selection");v["selector"]["range"]=window(&inv,"memo_body",7,8)?;
    for axis in["paragraph_property","paragraph_style"] {v["operation"]["replacement"]["axis"]=json!(axis);
        assert!(matches!(para_prepare!(&provider,&v),Err(PE::Stored(PS::Output(PC::IncompleteParagraphScope)))));
    }Ok(())
}
#[test]
fn paragraph_product_entities_cross_run_hangul_and_character_style_axes_remain_byte_exact()->TestResult {
    for(body,q)in[(p(1,"A&#x1F600;B&amp;C"),"😀B"),
        ("<hp:p id='1' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'><hp:t charStyleIDRef='0'>Xᄀ</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t charStyleIDRef='1'>ᅡᆨY</hp:t></hp:run></hp:p>".to_owned(),"각")] {
        let bytes=definition::package(&body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=request(&s,&bytes)?;
        v["operation"]["query"]=json!(q);let out=para_prepare!(&provider,&v)?;
        assert_eq!(out.with_verified_bytes(&provider,5,section)??,section(&bytes)?.replacen("paraPrIDRef='0'","paraPrIDRef='1'",1));
    }Ok(())
}
#[test]
fn paragraph_product_declared_definition_regex_case_and_word_options_bind_original_paragraphs()->TestResult {
    let bytes=definition::package(&(p(1,"Cat")+&p(2,"scatter")+&p(3,"CAT")))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for axis in["paragraph_property","paragraph_style"] {let mut v=request(&s,&bytes)?;v["operation"]["replacement"]["axis"]=json!(axis);v["operation"]["query"]=json!("c[a]t");
        v["operation"]["regex"]=json!(true);v["operation"]["case_sensitive"]=json!(false);v["operation"]["whole_word"]=json!(true);
        v["operation"]["style_filter"]=json!({"kind":"definition","filter":{"paragraph_source":"direct_property","alignment":"justify"}});
        let out=para_prepare!(&provider,&v)?;assert_eq!(out.receipt().stored.output.matched_occurrences,2);let after=out.with_verified_bytes(&provider,5,<[u8]>::to_vec)?;
        let expected=if axis=="paragraph_property"{vec![(1,Some(1),Some(0)),(2,Some(0),Some(0)),(3,Some(1),Some(0))]}else{vec![(1,Some(0),Some(1)),(2,Some(0),Some(0)),(3,Some(0),Some(1))]};
        assert_eq!(references(&after)?,expected);
    }Ok(())
}
#[test]
fn paragraph_product_review_policies_exclude_before_match_caps_and_never_restyle_outer_cache()->TestResult {
    let bytes=review_raw()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut hashes=BTreeSet::new();
    for(h,m,total)in[(false,false,0),(true,false,1),(false,true,1),(true,true,2)] {let mut v=request(&s,&bytes)?;v["operation"]["review_policy"]=policy(h,m);v["operation"]["max_replacements"]=json!(if total==0{1}else{total*2});
        let result=para_prepare!(&provider,&v);if total==0{assert!(matches!(result,Err(PE::Stored(PS::Output(PC::Compile(Compile::NoMatches))))));continue;}
        let out=result?;hashes.insert(out.receipt().stored.output.search_request_sha256);assert_eq!(out.receipt().stored.output.matched_paragraphs,total);
        let after=out.with_verified_bytes(&provider,5,<[u8]>::to_vec)?;assert_eq!(references(&after)?[0],(1,Some(0),Some(0)));assert!(section(&after)?.contains("CACHE FROZEN"));
    }assert_eq!(hashes.len(),3);Ok(())
}
#[test]
fn paragraph_product_required_extent_target_filter_policy_shape_and_decoded_duplicates_reject_before_reads()->TestResult {
    let bytes=raw("K")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();let mut bad=vec![b"null".to_vec(),b"[]".to_vec()];
    for key in["schema_version","idempotency_key","project_id","document_id","base_revision","expected_head_generation","expected_source_package_sha256","plan_id","selector","operation"] {
        let mut v=good.clone();v.as_object_mut().ok_or("envelope")?.remove(key);bad.push(wire(&v)?);
    }
    for key in["kind","query","regex","case_sensitive","whole_word","max_replacements","style_filter","replacement","extent","review_policy"] {
        let mut v=good.clone();v["operation"].as_object_mut().ok_or("operation")?.remove(key);bad.push(wire(&v)?);
    }
    for replacement in[json!("1"),json!(null),json!([]),json!({}),json!({"axis":"paragraph_property"}),json!({"declaration_id":1}),
        json!({"axis":"run_character_property","declaration_id":1}),json!({"axis":"paragraph_property","declaration_id":-1}),json!({"axis":"paragraph_style","declaration_id":4294967296u64}),
        json!({"axis":"paragraph_property","declaration_id":1,"approved":true})] {let mut v=good.clone();v["operation"]["replacement"]=replacement;bad.push(wire(&v)?);}
    for f in[json!({}),json!([]),json!({"kind":"declared","filter":{}}),json!({"kind":"definition","filter":{"alignment":"justify"}}),json!({"kind":"declared","filter":{"unknown":0}})] {
        let mut v=good.clone();v["operation"]["style_filter"]=f;bad.push(wire(&v)?);
    }
    for(key,value)in[("kind",json!("replace_text_character_style")),("query",json!("")),("query",json!("Q".repeat(4097))),("regex",json!(1)),("max_replacements",json!(0)),("max_replacements",json!(10001)),
        ("extent",json!("expand_selection")),("extent",json!(null)),("extent",json!(true)),("include_hidden",json!(true)),("preview_only",json!(false)),("review_policy",json!({"include_memo_bodies":true}))] {
        let mut v=good.clone();v["operation"][key]=value;bad.push(wire(&v)?);
    }
    for(key,value)in[("schema_version",json!(SCHEMA)),("approved",json!(true)),("source_graph",json!({})),("expected_head_generation",json!(0)),("expected_source_package_sha256",json!("A".repeat(64)))] {
        let mut v=good.clone();v[key]=value;bad.push(wire(&v)?);
    }
    let mut v=good.clone();v["selector"]["revision_id"]=json!(rev::RevisionId::generate().public_id());bad.push(wire(&v)?);
    let text=serde_json::to_string(&good)?;for(from,to)in[("\"axis\":\"paragraph_property\"","\"axis\":\"paragraph_property\",\"a\\u0078is\":\"paragraph_style\""),
        ("\"declaration_id\":1","\"declaration_id\":1,\"declaration_\\u0069d\":0"),("\"extent\":\"whole_matched_paragraph_within_scope\"","\"extent\":\"whole_matched_paragraph_within_scope\",\"e\\u0078tent\":\"expand_selection\"")] {
        let v=text.replace(from,to);assert_ne!(v,text);bad.push(v.into_bytes());
    }
    for bytes in bad {assert!(matches!(ParaProduct::prepare_json(&provider,&bytes,Default::default(),Default::default(),4),Err(PE::Request)));}assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn paragraph_product_legacy_run_text_literal_regex_and_search_schemas_reject_paragraph_operations()->TestResult {
    use hwpx_agent_cli::form_product_request::stored_literal_replacement::{StoredLiteralReplacementProductRequest as L1,atoms::StoredLiteralTextAtomProductRequest as L2,
        review::StoredReviewLiteralProductRequest as L3,selector::StoredSelectorLiteralProductRequest as L4,regex::insertions::StoredRegexInsertionProductRequest as R2,
        styles::StoredCharacterStyleProductRequest as Run,text_styles::StoredTextStyleProductRequest as Text};
    use hwpx_agent_cli::form_product_request::stored_source_search::selector::styles::StoredSelectorStyleProductRequest as Find;
    let bytes=raw("K")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=request(&s,&bytes)?;let before=s.metadata.audit_events()?.len();
    for schema in[PARA_SCHEMA,SCHEMA,"hwpx-agent.product-regex-replacement-request/v2","hwpx-agent.product-literal-replacement-request/v1","hwpx-agent.product-literal-replacement-request/v2",
        "hwpx-agent.product-literal-replacement-request/v3","hwpx-agent.product-literal-replacement-request/v4","hwpx-agent.product-source-search-request/v7",
        "hwpx-agent.product-character-style-replacement-request/v1","hwpx-agent.product-text-style-replacement-request/v1"] {
        let mut v=good.clone();v["schema_version"]=json!(schema);let bytes=wire(&v)?;
        assert!(Product::prepare_json(&provider,&bytes,Default::default(),Default::default(),4).is_err());assert!(R2::prepare_json(&provider,&bytes,Default::default(),Default::default(),4).is_err());
        assert!(L1::prepare_json(&provider,&bytes,Default::default(),Default::default(),4).is_err());assert!(L2::prepare_json(&provider,&bytes,Default::default(),Default::default(),4).is_err());
        assert!(L3::prepare_json(&provider,&bytes,Default::default(),Default::default(),4).is_err());assert!(L4::prepare_json(&provider,&bytes,Default::default(),Default::default(),4).is_err());
        assert!(Run::prepare_json(&provider,&bytes,Default::default(),Default::default(),4).is_err());assert!(Text::prepare_json(&provider,&bytes,Default::default(),Default::default(),4).is_err());assert!(Find::prepare_json(&provider,&bytes,Default::default(),4).is_err());
    }
    for(kind,axis)in[("replace_character_property","run_character_property"),("replace_text_character_style","text_character_style")] {let mut old=good.clone();old["operation"]["kind"]=json!(kind);old["operation"]["replacement"]["axis"]=json!(axis);
        assert!(matches!(para_prepare!(&provider,&old),Err(PE::Request)));
    }assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn paragraph_product_exact_16k_raw_canonical_scope_target_key_plan_and_filter_bindings_are_distinct()->TestResult {
    let bytes=raw("K")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=request(&s,&bytes)?;let out=para_prepare!(&provider,&v)?;let mut padded=wire(&v)?;padded.resize(16*1024,b' ');
    let other=ParaProduct::prepare_json(&provider,&padded,Default::default(),Default::default(),4)?;assert_ne!(out.receipt().raw_request_sha256,other.receipt().raw_request_sha256);assert_eq!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);
    padded.push(b' ');assert!(matches!(ParaProduct::prepare_json(&provider,&padded,Default::default(),Default::default(),4),Err(PE::Limit)));assert!(matches!(ParaProduct::prepare_json(&provider,b"",Default::default(),Default::default(),4),Err(PE::Limit)));
    for(key,value)in[("idempotency_key",json!("OTHER-KEY")),("plan_id",json!("other-plan"))] {let mut v=v.clone();v[key]=value;let other=para_prepare!(&provider,&v)?;
        assert_ne!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);assert_ne!(out.receipt().scoped_request_sha256,other.receipt().scoped_request_sha256);assert_eq!(out.receipt().stored.output.output_package_sha256,other.receipt().stored.output.output_package_sha256);
    }
    let mut named=v.clone();named["operation"]["replacement"]["axis"]=json!("paragraph_style");let named=para_prepare!(&provider,&named)?;
    assert_ne!(out.receipt().canonical_request_sha256,named.receipt().canonical_request_sha256);assert_ne!(out.receipt().scoped_request_sha256,named.receipt().scoped_request_sha256);
    assert_eq!(out.receipt().stored.output.search_request_sha256,named.receipt().stored.output.search_request_sha256);assert_ne!(out.receipt().stored.output.replacement_request_sha256,named.receipt().stored.output.replacement_request_sha256);
    let mut other=v.clone();other["operation"]["style_filter"]=json!({"kind":"definition","filter":{"paragraph_source":"direct_property","alignment":"justify"}});let other=para_prepare!(&provider,&other)?;
    assert_ne!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);assert_eq!(out.receipt().stored.output.output_package_sha256,other.receipt().stored.output.output_package_sha256);Ok(())
}
#[test]
fn paragraph_product_current_write_and_five_foreign_scopes_deny_retained_output()->TestResult {
    let bytes=raw("K")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=request(&s,&bytes)?;let reader=s.provider()?;assert!(para_prepare!(&reader,&v).is_err());
    let out=para_prepare!(&provider,&v)?;let called=Cell::new(false);assert!(out.with_verified_bytes(&reader,5,|_|called.set(true)).is_err());
    let source=reader.import_actual_forms(s.head,4)?;assert!(matches!(source.prepare_paragraph_style_candidate(&reader,Query {mode:Mode::Literal,..query("K")},Scope::Document,all(),filter(),Target::ParagraphProperty(1),EXTENT,
        Default::default(),Default::default(),4),Err(PS::Permission)));
    for variant in 0..5 {let tenant=if variant==4{TenantId::new(Uuid::from_u128(997))?}else{s.reader.tenant_id()};let subject=if variant==3{SubjectDigest::from_authenticated_subject("foreign-paragraph-style")?}else{s.reader.subject()};
        let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);let context=rev::RevisionRequestContext::new(tenant,subject);
        let project=if variant==2{rev::ProjectId::parse("prj_70000000000000000000000000000002")?}else{s.project};let branch=if variant==1{rev::BranchId::parse("brn_70000000000000000000000000000002")?}else{s.branch};
        let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&context,project,branch,DocumentId::parse(if variant==0{"foreign-document"}else{"actual-form-document"})?)?;
        assert!(out.verify(&other,5).is_err());assert!(out.with_verified_bytes(&other,5,|_|called.set(true)).is_err());
    }assert!(!called.get());Ok(())
}
#[test]
fn paragraph_product_acl_revoke_regrant_quarantine_and_aead_protect_old_and_new_candidates()->TestResult {
    for mode in 0..3 {let bytes=raw("K")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let v=request(&s,&bytes)?;let out=para_prepare!(&provider,&v)?;
        match mode {0=>{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;},1=>{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("PARAGRAPH_STYLE_TEST")?,5)?;},_=>s.blobs.tamper.store(true,Ordering::SeqCst)}
        let called=Cell::new(false);assert!(out.verify(&provider,6).is_err());assert!(out.with_verified_bytes(&provider,6,|_|called.set(true)).is_err());assert!(para_prepare!(&provider,&v).is_err());assert!(!called.get());
        if mode==0{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;out.verify(&provider,8)?;out.with_verified_bytes(&provider,8,|_|())?;}
    }Ok(())
}
#[test]
fn paragraph_product_both_axes_prepare_verify_and_delivery_final_head_races_block_consumers()->TestResult {
    for axis in["paragraph_property","paragraph_style"] {for stage in 0..3 {
        let bytes=raw("K")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=request(&s,&bytes)?;v["operation"]["replacement"]["axis"]=json!(axis);let request_bytes=wire(&v)?;let out=para_prepare!(&provider,&v)?;
        let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,
            ContentDigest::of(b"paragraph race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation"),ContentDigest::of(b"transaction"))?;
        let b=rev::RevisionService::new(BoundaryRepo {inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
        let bound=StoredFormProvider::bind(&s.artifacts,&b,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
        match stage {0=>{ParaProduct::prepare_json(&bound,&request_bytes,Default::default(),Default::default(),5)?;},1=>{out.verify(&bound,5)?;},_=>{out.with_verified_bytes(&bound,5,|_|())?;}}
        let calls=b.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);b.repository().calls.store(0,Ordering::SeqCst);b.repository().trigger.store(calls,Ordering::SeqCst);let called=Cell::new(false);
        match stage {0=>assert!(ParaProduct::prepare_json(&bound,&request_bytes,Default::default(),Default::default(),6).is_err()),1=>assert!(out.verify(&bound,6).is_err()),_=>assert!(out.with_verified_bytes(&bound,6,|_|called.set(true)).is_err())}
        assert!(!called.get());assert_eq!(b.repository().calls.load(Ordering::SeqCst),calls);
    }}Ok(())
}
#[test]
fn paragraph_product_borrowed_owned_and_json_share_both_axis_target_receipts_and_output_bytes()->TestResult {
    let bytes=raw("K")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for target in[Target::ParagraphProperty(1),Target::ParagraphStyle(1)] {let mut v=request(&s,&bytes)?;v["operation"]["replacement"]=serde_json::to_value(target)?;let out=para_prepare!(&provider,&v)?;let source=provider.import_actual_forms(s.head,4)?;
        let borrowed=source.prepare_paragraph_style_candidate(&provider,Query {mode:Mode::Literal,..query("K")},Scope::Document,all(),filter(),target,EXTENT,Default::default(),Default::default(),4)?;
        assert_eq!(borrowed.verify(&provider,5)?,out.receipt().stored);drop(borrowed);
        let owned=source.into_paragraph_style_candidate(&provider,Query {mode:Mode::Literal,..query("K")},Scope::Document,all(),filter(),target,EXTENT,Default::default(),Default::default(),4)?;
        assert_eq!(owned.verify(&provider,5)?,out.receipt().stored);assert_eq!(owned.with_verified_bytes(&provider,5,<[u8]>::to_vec)?,out.with_verified_bytes(&provider,5,<[u8]>::to_vec)?);
        assert!(matches!(owned.require_current_product_route(&provider,5),Err(PS::RouteUnqualified)));
    }Ok(())
}
#[test]
fn paragraph_product_wrong_source_head_document_and_project_reject_new_preparation()->TestResult {
    let bytes=raw("K")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let good=request(&s,&bytes)?;
    for(key,value)in[("expected_head_generation",json!(s.head.generation()+1)),("expected_source_package_sha256",json!("0".repeat(64))),("document_id",json!("foreign-document")),("project_id",json!("prj_70000000000000000000000000000002"))] {
        let mut bad=good.clone();bad[key]=value;assert!(para_prepare!(&provider,&bad).is_err());
    }Ok(())
}
#[test]
fn paragraph_product_nonexistent_wrong_kind_targets_and_noops_never_become_successful_candidates()->TestResult {
    let bytes=raw("K")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=request(&s,&bytes)?;
    for target in[Target::ParagraphProperty(u32::MAX),Target::ParagraphStyle(u32::MAX),Target::ParagraphStyle(12)] {
        v["operation"]["replacement"]=serde_json::to_value(target)?;assert!(matches!(para_prepare!(&provider,&v),Err(PE::Stored(PS::Output(PC::Search(Search::Definition))))));
    }
    for target in[Target::ParagraphProperty(0),Target::ParagraphStyle(0)] {v["operation"]["replacement"]=serde_json::to_value(target)?;
        assert!(matches!(para_prepare!(&provider,&v),Err(PE::Stored(PS::Output(PC::Compile(Compile::NoChange))))));
    }Ok(())
}
#[test]
fn paragraph_product_unqueried_fields_locked_descendants_and_tracking_block_whole_batch_including_noops()->TestResult {
    let cache=fixture::body().replace("<hp:p id='1'>","<hp:p id='1' paraPrIDRef='0' styleIDRef='0'>");
    let locked=table::table(300).replace("lock='0'","lock='1'");let mixed=p(1,"K")+&p(2,&format!("K</hp:t>{locked}<hp:t>TAIL"));
    for(body,q,field)in[(cache,"BODY",true),(mixed,"K",false),(p(1,"K").replace("charPrIDRef='0'","charPrIDRef='0' charTcId='1'"),"K",false)] {
        let bytes=definition::package(&body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
        for id in[0,1] {let mut v=request(&s,&bytes)?;v["operation"]["query"]=json!(q);v["operation"]["replacement"]["declaration_id"]=json!(id);
            if field{assert!(matches!(para_prepare!(&provider,&v),Err(PE::Stored(PS::Output(PC::Compile(Compile::FieldContent))))));}
            else{assert!(matches!(para_prepare!(&provider,&v),Err(PE::Stored(PS::Output(PC::Compile(Compile::Protection))))));}
        }
    }Ok(())
}
#[test]
fn paragraph_product_missing_references_are_not_defaulted_on_the_other_axis_or_unselected_paragraph()->TestResult {
    let bytes=definition::package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>ABC</hp:t></hp:run></hp:p><hp:p id='2'><hp:run charPrIDRef='0'><hp:t>KEEP</hp:t></hp:run></hp:p>")?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for target in[Target::ParagraphProperty(1),Target::ParagraphStyle(1)] {let mut v=request(&s,&bytes)?;v["operation"]["query"]=json!("B");v["operation"]["replacement"]=serde_json::to_value(target)?;
        v["operation"]["style_filter"]=json!({"kind":"declared","filter":{"run_character_property":0}});let out=para_prepare!(&provider,&v)?;let after=out.with_verified_bytes(&provider,5,<[u8]>::to_vec)?;
        let first=if matches!(target,Target::ParagraphProperty(_)){(1,Some(1),None)}else{(1,None,Some(1))};assert_eq!(references(&after)?,vec![first,(2,None,None)]);
        assert_eq!(out.receipt().stored.output.changes[0].previous_reference,None);
    }Ok(())
}
#[test]
fn paragraph_product_match_output_writer_pattern_and_zero_width_limits_reject_entire_candidate()->TestResult {
    let bytes=raw("K K")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=request(&s,&bytes)?;v["operation"]["max_replacements"]=json!(1);assert!(para_prepare!(&provider,&v).is_err());
    v["operation"]["max_replacements"]=json!(100);assert!(ParaProduct::prepare_json(&provider,&wire(&v)?,SourceSearchLimits::new(Config {result_bytes:1,..Default::default()})?,Default::default(),4).is_err());
    assert!(matches!(ParaProduct::prepare_json(&provider,&wire(&v)?,Default::default(),WriterLimits::new(WriterLimitConfig {max_output_bytes:1})?,4),Err(PE::Stored(PS::Output(PC::Compile(Compile::Writer))))));
    for q in["(","^"]{v["operation"]["query"]=json!(q);v["operation"]["regex"]=json!(true);assert!(para_prepare!(&provider,&v).is_err());}Ok(())
}
#[test]
fn paragraph_product_ambiguous_nfc_and_partial_decompositions_do_not_invent_original_matches()->TestResult {
    for(text,q)in[("a&#x315;&#x300;","à"),("&#x344;","\u{308}")] {let bytes=raw(text)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=request(&s,&bytes)?;v["operation"]["query"]=json!(q);
        assert!(matches!(para_prepare!(&provider,&v),Err(PE::Stored(PS::Output(PC::Compile(Compile::Selection))))));
    }Ok(())
}
#[test]
fn paragraph_product_many_matches_and_paragraphs_share_protection_without_ingest_head_or_privacy_changes()->TestResult {
    for body in[p(1,&"PRIVATE K ".repeat(128)),(1..=128).map(|id|p(id,"PRIVATE K")).collect::<String>()] {
        let bytes=definition::package(&body)?;let original=ContentDigest::of(&bytes);let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=request(&s,&bytes)?;v["operation"]["max_replacements"]=json!(128);
        let out=para_prepare!(&provider,&v)?;let total=references(&bytes)?.len();assert_eq!(out.receipt().stored.output.matched_occurrences,128);assert_eq!(out.receipt().stored.output.changes.len(),total);
        let xml=hwpx_package::PreservingXmlDocument::parse(section(&bytes)?.as_bytes())?;assert_eq!(out.receipt().stored.output.observed_protection_element_visits,xml.elements().len()*3);
        out.with_verified_bytes(&provider,5,|_|())?;assert_eq!(ContentDigest::of(&bytes),original);assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);
        assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);assert!(!format!("{out:?}{:?}{}",out.receipt(),serde_json::to_string(out.receipt())?).contains("PRIVATE"));
        assert!(matches!(out.require_current_product_route(&provider,5),Err(PE::RouteUnqualified)));assert!(!out.receipt().idempotency_key_claimed&&!out.receipt().full_style_native_cas_execution_publication_authority);
    }Ok(())
}
#[test]
fn paragraph_product_aliases_and_native_field_ids_in_unselected_paragraph_are_preserved_once()->TestResult {
    let bytes=definition::package("<z:p xmlns:z='http://www.hancom.co.kr/hwpml/2011/paragraph' id='1' paraPrIDRef='0' styleIDRef='0'><z:run charPrIDRef='0'><z:t>AB</z:t></z:run></z:p><z:p xmlns:z='http://www.hancom.co.kr/hwpml/2011/paragraph' id='2' paraPrIDRef='0' styleIDRef='0'><z:run charPrIDRef='0'><z:ctrl><z:fieldBegin id='17' type='DOC_DATE' editable='1'/></z:ctrl><z:t>FROZEN</z:t><z:ctrl><z:fieldEnd beginIDRef='17'/></z:ctrl></z:run></z:p>")?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=request(&s,&bytes)?;v["operation"]["query"]=json!("B");let out=para_prepare!(&provider,&v)?;
    let after=out.with_verified_bytes(&provider,5,section)??;assert_eq!(after,section(&bytes)?.replacen("paraPrIDRef='0'","paraPrIDRef='1'",1));
    assert_eq!(after.matches("<z:fieldBegin id='17' type='DOC_DATE' editable='1'/>").count(),1);assert_eq!(after.matches("<z:fieldEnd beginIDRef='17'/>").count(),1);Ok(())
}
