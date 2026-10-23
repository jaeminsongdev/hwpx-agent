//! Actual shared entry, repositories and original mutators. No Native/DB/publication authority.
use super::*;
use hwpx_agent_cli::form_product_request::{stored_literal_replacement as literal,
    stored_operations::{StoredProductRequest as Dispatch, PreparedStoredProductOperation as Operation,
        StoredProductOperationError as DE, search_mutations::{SearchMutationError as ME,
            SearchMutationReceiptRef as Receipt, SearchMutationLimits as Limits, SEARCH_MUTATION_REQUEST_SCHEMAS}}};
use literal::{atoms, review, selector, regex, styles, text_styles, paragraph_styles, unicode, case, width, whitespace, controls, number_controls};
use regex::insertions;
use unicode::matches as unicode_matches;
const SCHEMAS: [&str;16] = [
    "hwpx-agent.product-literal-replacement-request/v1", "hwpx-agent.product-literal-replacement-request/v2",
    "hwpx-agent.product-literal-replacement-request/v3", "hwpx-agent.product-literal-replacement-request/v4",
    "hwpx-agent.product-regex-replacement-request/v1", "hwpx-agent.product-regex-replacement-request/v2",
    "hwpx-agent.product-character-style-replacement-request/v1", "hwpx-agent.product-text-style-replacement-request/v1",
    "hwpx-agent.product-paragraph-style-replacement-request/v1", "hwpx-agent.product-unicode-normalization-request/v1",
    "hwpx-agent.product-unicode-normalization-request/v2", "hwpx-agent.product-case-conversion-request/v1",
    "hwpx-agent.product-width-conversion-request/v1", "hwpx-agent.product-whitespace-normalization-request/v1",
    "hwpx-agent.product-text-control-replacement-request/v1", "hwpx-agent.product-number-control-replacement-request/v1",
];
fn source(i: usize) -> Result<Vec<u8>,Box<dyn Error>> {
    match i {
        0..=6 => definition::package(&para(1,"K").replace(" charStyleIDRef='0'","")),
        9|10 => raw("a&#x300;"), 11 => raw("ab"), 12 => raw("a"), 13 => raw("A  B"),
        14 => raw(&format!("K{TAB}Y")),
        15 => definition::package("<hp:p id='1' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'><hp:t>K</hp:t><hp:ctrl><hp:autoNum num='2' numType='PICTURE'><hp:autoNumFormat type='DIGIT' userChar='' prefixChar='' suffixChar='' supscript='0'/></hp:autoNum></hp:ctrl><hp:t>Y</hp:t></hp:run></hp:p>"),
        _ => raw("K"),
    }
}
fn req(i: usize,s:&StoredFixture,bytes:&[u8])->Result<Value,Box<dyn Error>> {
    let mut v=request(s,bytes)?; v["schema_version"]=json!(SCHEMAS[i]);
    v["operation"]=json!({"kind":"replace_literal","query":"K","replacement":"X","case_sensitive":true,"whole_word":false,
        "max_replacements":100,"run_policy":"first_original_run_retain_all_runs","review_policy":policy(true,true)});
    if i<3 { v.as_object_mut().ok_or("request")?.remove("selector");v["scope"]=json!({"kind":"mapped_document","paragraph_handles":[]}); }
    if i<2 { v["operation"].as_object_mut().ok_or("operation")?.remove("review_policy"); }
    match i {
        4|5 => {v["operation"]["kind"]=json!("replace_regex");v["operation"]["regex"]=json!(true);
            if i==5 {v["operation"]["query"]=json!("^");v["operation"]["insertion_policy"]=json!("right_original_point_else_left_first_empty_text");}},
        6..=8 => {let (kind,axis)=match i {6=>("replace_character_property","run_character_property"),7=>("replace_text_character_style","text_character_style"),_=>("replace_paragraph_style_reference","paragraph_property")};
            v["operation"]=json!({"kind":kind,"query":"K","regex":false,"case_sensitive":true,"whole_word":false,"max_replacements":100,
                "style_filter":{"kind":"declared","filter":{axis:0}},"replacement":{"axis":axis,"declaration_id":1},"review_policy":policy(true,true)});
            if i==8 {v["operation"]["extent"]=json!("whole_matched_paragraph_within_scope");}},
        9..=13 => {v["operation"]=json!({"kind":"normalize_unicode_matches","query":"(?s:.+)","regex":true,"case_sensitive":true,"whole_word":false,"max_matches":100,
            "form":"nfc","run_policy":"first_original_run_retain_all_runs","review_policy":policy(true,true)});
            match i {
                9 => {v["operation"]=json!({"kind":"normalize_unicode_scope","form":"nfc","run_policy":"first_original_run_retain_all_runs","review_policy":policy(true,true)});},
                11 => {let op=v["operation"].as_object_mut().ok_or("operation")?;op.remove("form");op.remove("run_policy");op.insert("kind".into(),json!("convert_case_matches"));op.insert("mode".into(),json!("uppercase"));op.insert("case_policy".into(),json!("unicode_default_each_matched_text_group"));},
                12 => {let op=v["operation"].as_object_mut().ok_or("operation")?;op.remove("form");op.insert("kind".into(),json!("convert_width_matches"));op.insert("mode".into(),json!("fullwidth"));op.insert("width_policy".into(),json!("unicode17_width_pairs_with_kana_pairs"));},
                13 => {let op=v["operation"].as_object_mut().ok_or("operation")?;op.remove("form");op.insert("kind".into(),json!("normalize_whitespace_matches"));op.insert("whitespace_policy".into(),json!({"text":"ascii_space","tabs":true,"line_breaks":true,"sequence":"collapse_each_matched_sequence","output":{"spaces":{"count":1}}}));}, _=>{}
            }},
        14 => v["operation"]=json!({"kind":"replace_text_controls","control_kind":"tab","max_replacements":100,"output":[{"kind":"text","value":"X"}],"review_policy":policy(true,true)}),
        15 => v["operation"]=json!({"kind":"replace_number_controls","control_kind":"auto_number","max_replacements":100,"stored_number":9,"format":{"kind":"preserve"},"review_policy":policy(true,true)}),
        _=>{}
    }
    Ok(v)
}
macro_rules! original {
    (text,$module:ident,$request:ident,$p:ident,$b:ident,$limits:ident) => {$module::$request::prepare_json(&$p,&$b,$limits.search,$limits.writer,4)};
    (number,$module:ident,$request:ident,$p:ident,$b:ident,$limits:ident) => {$module::$request::prepare_json(&$p,&$b,$limits.search,$limits.auxiliary,$limits.writer,4)};
}
macro_rules! dispatch_case {
    ($name:ident,$i:literal,$variant:ident,$module:ident,$request:ident,$err:path,$budget:ident) => {
        #[test] fn $name()->TestResult {
            use $err as OriginalError;
            let bytes=source($i)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
            let v=req($i,&s,&bytes)?;let b=wire(&v)?;let limits=Limits::standard()?;
            let direct=original!($budget,$module,$request,provider,b,limits)?;
            let out=Dispatch::prepare_json(&provider,&b,None,4)?;drop(v);drop(b);
            let Operation::SearchMutation(candidate)=&out else {return Err("wrong dispatch".into())};
            assert_eq!(candidate.schema_version(),SCHEMAS[$i]);candidate.verify(&provider,5)?;
            let Receipt::$variant(receipt)=candidate.receipt() else {return Err("wrong receipt".into())};assert_eq!(receipt,direct.receipt());
            let actual=out.with_verified_bytes(&provider,None,5,<[u8]>::to_vec)?;
            assert_eq!(actual,direct.with_verified_bytes(&provider,5,<[u8]>::to_vec)?);assert_ne!(actual,bytes);
            assert!(matches!(out.require_current_product_route(&provider,None,5),Err(DE::SearchMutation(ME::$variant(OriginalError::RouteUnqualified)))));
            assert!(!format!("{out:?}").contains("PRIVATE-UNICODE-KEY"));
            assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);
            assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
        }
    }
}
dispatch_case!(dispatch_literal_v1,0,Literal,literal,StoredLiteralReplacementProductRequest,literal::LiteralReplacementProductError,text);
dispatch_case!(dispatch_literal_atoms_v2,1,LiteralAtoms,atoms,StoredLiteralTextAtomProductRequest,literal::LiteralReplacementProductError,text);
dispatch_case!(dispatch_review_literal_v3,2,ReviewLiteral,review,StoredReviewLiteralProductRequest,literal::LiteralReplacementProductError,text);
dispatch_case!(dispatch_selector_literal_v4,3,SelectorLiteral,selector,StoredSelectorLiteralProductRequest,literal::LiteralReplacementProductError,text);
dispatch_case!(dispatch_regex_v1,4,Regex,regex,StoredRegexReplacementProductRequest,regex::RegexReplacementProductError,text);
dispatch_case!(dispatch_regex_insertions_v2,5,RegexInsertion,insertions,StoredRegexInsertionProductRequest,regex::RegexReplacementProductError,text);
dispatch_case!(dispatch_character_style_v1,6,CharacterStyle,styles,StoredCharacterStyleProductRequest,styles::CharacterStyleProductError,text);
dispatch_case!(dispatch_text_style_v1,7,TextStyle,text_styles,StoredTextStyleProductRequest,text_styles::TextStyleProductError,text);
dispatch_case!(dispatch_paragraph_style_v1,8,ParagraphStyle,paragraph_styles,StoredParagraphStyleProductRequest,paragraph_styles::ParagraphStyleProductError,text);
dispatch_case!(dispatch_unicode_scope_v1,9,UnicodeScope,unicode,StoredUnicodeProductRequest,unicode::UnicodeProductError,text);
dispatch_case!(dispatch_unicode_matches_v2,10,UnicodeMatches,unicode_matches,StoredUnicodeMatchProductRequest,unicode_matches::UnicodeMatchProductError,text);
dispatch_case!(dispatch_case_v1,11,Case,case,StoredCaseProductRequest,case::CaseProductError,text);
dispatch_case!(dispatch_width_v1,12,Width,width,StoredWidthProductRequest,width::WidthProductError,text);
dispatch_case!(dispatch_whitespace_v1,13,Whitespace,whitespace,StoredWhitespaceProductRequest,whitespace::WhitespaceProductError,text);
dispatch_case!(dispatch_text_control_v1,14,TextControl,controls,StoredControlProductRequest,controls::ControlProductError,text);
dispatch_case!(dispatch_number_control_v1,15,NumberControl,number_controls,StoredNumberControlProductRequest,number_controls::NumberControlProductError,number);

#[test]
fn dispatch_closed_schemas_strict_each_family_and_no_cross_kind_fallback_before_reads()->TestResult {
    assert_eq!(&SEARCH_MUTATION_REQUEST_SCHEMAS[..16],SCHEMAS);assert_eq!(SCHEMAS.into_iter().collect::<BTreeSet<_>>().len(),16);
    assert_eq!(SEARCH_MUTATION_REQUEST_SCHEMAS.len(),23);assert_eq!(SEARCH_MUTATION_REQUEST_SCHEMAS[16],literal::sort::PARAGRAPH_SORT_PRODUCT_REQUEST_SCHEMA);
    assert_eq!(SEARCH_MUTATION_REQUEST_SCHEMAS[17],literal::sort_groups::PARAGRAPH_SORT_GROUPS_PRODUCT_REQUEST_SCHEMA);
    assert_eq!(SEARCH_MUTATION_REQUEST_SCHEMAS[18],literal::fonts::FONT_PRODUCT_REQUEST_SCHEMA);
    assert_eq!(SEARCH_MUTATION_REQUEST_SCHEMAS[19],literal::fonts::options::FONT_OPTIONS_REQUEST_SCHEMA);
    assert_eq!(SEARCH_MUTATION_REQUEST_SCHEMAS[20],literal::named_styles::NAMED_STYLE_PRODUCT_REQUEST_SCHEMA);
    assert_eq!(SEARCH_MUTATION_REQUEST_SCHEMAS.iter().copied().collect::<BTreeSet<_>>().len(),23);
    let bytes=source(3)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let before=s.metadata.audit_events()?.len();
    for i in 0..16 {let good=req(i,&s,&bytes)?;
        for key in ["schema_version","operation","idempotency_key","expected_head_generation"] {let mut bad=good.clone();bad.as_object_mut().ok_or("object")?.remove(key);assert!(Dispatch::prepare_json(&p,&wire(&bad)?,None,4).is_err());}
        for (key,value) in [("kind",json!("execute")),("approved",json!(true))] {let mut bad=good.clone();bad["operation"][key]=value;assert!(Dispatch::prepare_json(&p,&wire(&bad)?,None,4).is_err());}
        let mut bad=good.clone();bad["schema_version"]=json!("hwpx-agent.product-operation-request/v999");assert!(Dispatch::prepare_json(&p,&wire(&bad)?,None,4).is_err());
        let mut bad=good;bad["operation"]=json!({"kind":"recalculate_table_formulas"});assert!(Dispatch::prepare_json(&p,&wire(&bad)?,None,4).is_err());
    }assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn dispatch_duplicate_root_nested_escaped_keys_trailing_values_and_raw_limits_fail_closed()->TestResult {
    let bytes=source(3)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=req(3,&s,&bytes)?;
    let text=serde_json::to_string(&good)?;let before=s.metadata.audit_events()?.len();
    for (from,to) in [("\"scope\":\"document\"","\"scope\":\"document\",\"sco\\u0070e\":\"document\""),
        ("\"kind\":\"replace_literal\"","\"kind\":\"replace_literal\",\"ki\\u006ed\":\"replace_literal\"")]{let bad=text.replace(from,to);assert_ne!(bad,text);assert!(Dispatch::prepare_json(&p,bad.as_bytes(),None,4).is_err());}
    for b in [b"null".to_vec(),b"[]".to_vec(),format!("{text} {{}}").into_bytes(),format!("{{\"schema_version\":\"{}\",{}",SCHEMAS[3],&text[1..]).into_bytes()] {assert!(Dispatch::prepare_json(&p,&b,None,4).is_err());}
    let mut padded=wire(&good)?;padded.resize(16*1024+1,b' ');assert!(matches!(Dispatch::prepare_json(&p,&padded,None,4),Err(DE::Request(_))));
    assert_eq!(s.metadata.audit_events()?.len(),before);padded.pop();Dispatch::prepare_json(&p,&padded,None,4)?;Ok(())
}
#[test]
fn dispatch_server_search_writer_and_number_format_budgets_are_not_dropped()->TestResult {
    for i in [3,15] {let bytes=source(i)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=req(i,&s,&bytes)?;
        let baseline=Dispatch::prepare_json_with_search_limits(&p,&wire(&v)?,None,Limits::standard()?,4)?;
        baseline.with_verified_bytes(&p,None,5,|_|())?;
        let mut limits=Limits::standard()?;limits.writer=WriterLimits::new(WriterLimitConfig{max_output_bytes:1})?;
        assert!(Dispatch::prepare_json_with_search_limits(&p,&wire(&v)?,None,limits,4).is_err());
        let mut limits=Limits::standard()?;limits.search=SourceSearchLimits::new(Config{result_bytes:1,..Default::default()})?;
        assert!(Dispatch::prepare_json_with_search_limits(&p,&wire(&v)?,None,limits,4).is_err());
        if i==15 {let mut limits=Limits::standard()?;limits.auxiliary=domain_ir::ReferenceAuxiliaryLimits::new(domain_ir::ReferenceAuxiliaryLimitConfig{text_bytes:1,..Default::default()})?;
            v["operation"]["format"]=json!({"kind":"replace","format":"DIGIT","user_character":"","prefix":"LONG","suffix":"","superscript":false});let before=s.metadata.audit_events()?.len();
            assert!(Dispatch::prepare_json_with_search_limits(&p,&wire(&v)?,None,limits,4).is_err());assert_eq!(s.metadata.audit_events()?.len(),before);}
    }Ok(())
}
#[test]
fn dispatch_fresh_write_scope_acl_quarantine_and_aead_reject_retained_consumers()->TestResult {
    for i in [3,15] {for mode in 0..3 {let bytes=source(i)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=req(i,&s,&bytes)?;
        let out=Dispatch::prepare_json(&p,&wire(&v)?,None,4)?;let reader=s.provider()?;let called=Cell::new(false);
        assert!(out.with_verified_bytes(&reader,None,5,|_|called.set(true)).is_err());
        match mode {0=>{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;},1=>{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("DISPATCH_TEST")?,5)?;},_=>s.blobs.tamper.store(true,Ordering::SeqCst)}
        assert!(out.with_verified_bytes(&p,None,6,|_|called.set(true)).is_err());assert!(out.require_current_product_route(&p,None,6).is_err());assert!(Dispatch::prepare_json(&p,&wire(&v)?,None,6).is_err());assert!(!called.get());
        if mode==0 {s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;out.with_verified_bytes(&p,None,8,|_|())?;}
    }}Ok(())
}
#[test]
fn dispatch_five_foreign_provider_scopes_cannot_rebind_retained_candidate()->TestResult {
    let bytes=source(15)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let out=Dispatch::prepare_json(&p,&wire(&req(15,&s,&bytes)?)?,None,4)?;let called=Cell::new(false);
    for i in 0..5 {let tenant=if i==4{TenantId::new(Uuid::from_u128(1205))?}else{s.reader.tenant_id()};let subject=if i==3{SubjectDigest::from_authenticated_subject("foreign-dispatch")?}else{s.reader.subject()};
        let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);let context=rev::RevisionRequestContext::new(tenant,subject);
        let project=if i==2{rev::ProjectId::parse("prj_70000000000000000000000000000002")?}else{s.project};let branch=if i==1{rev::BranchId::parse("brn_70000000000000000000000000000002")?}else{s.branch};
        let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&context,project,branch,DocumentId::parse(if i==0{"foreign-document"}else{"actual-form-document"})?)?;
        assert!(out.with_verified_bytes(&other,None,5,|_|called.set(true)).is_err());assert!(out.require_current_product_route(&other,None,5).is_err());
    }assert!(!called.get());Ok(())
}
#[test]
fn dispatch_prepare_verify_and_delivery_final_head_races_keep_original_boundaries()->TestResult {
    for stage in 0..3 {let bytes=source(15)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let b=wire(&req(15,&s,&bytes)?)?;let out=Dispatch::prepare_json(&p,&b,None,4)?;
        let Operation::SearchMutation(candidate)=&out else{return Err("kind".into())};
        let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,ContentDigest::of(b"dispatch race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation"),ContentDigest::of(b"transaction"))?;
        let repo=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
        let bound=StoredFormProvider::bind(&s.artifacts,&repo,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
        match stage {0=>{Dispatch::prepare_json(&bound,&b,None,5)?;},1=>candidate.verify(&bound,5)?,_=>{out.with_verified_bytes(&bound,None,5,|_|())?;}}
        let calls=repo.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);repo.repository().calls.store(0,Ordering::SeqCst);repo.repository().trigger.store(calls,Ordering::SeqCst);let called=Cell::new(false);
        match stage {0=>assert!(Dispatch::prepare_json(&bound,&b,None,6).is_err()),1=>assert!(candidate.verify(&bound,6).is_err()),_=>assert!(out.with_verified_bytes(&bound,None,6,|_|called.set(true)).is_err())}
        assert!(!called.get());assert_eq!(repo.repository().calls.load(Ordering::SeqCst),calls);
    }Ok(())
}
#[test]
fn dispatch_selector_inventory_and_review_policy_keep_exact_selected_source()->TestResult {
    let bytes=definition::package(&fixture::body().replace("<hp:run>","<hp:run charPrIDRef='0'>"))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=req(3,&s,&bytes)?;let inv=inventory(&p,&good)?;
    let mut v=good;v["selector"]["scope"]=json!("selection");v["selector"]["range"]=window(&inv,"memo_body",7,8)?;
    let out=Dispatch::prepare_json(&p,&wire(&v)?,None,4)?;
    assert_eq!(out.with_verified_bytes(&p,None,5,section)??,section(&bytes)?.replace("MEMO K K","MEMO K X"));
    v["operation"]["review_policy"]=policy(false,false);assert!(Dispatch::prepare_json(&p,&wire(&v)?,None,4).is_err());Ok(())
}
#[test]
fn dispatch_source_head_revision_index_and_client_authority_injections_are_not_trusted()->TestResult {
    let bytes=source(3)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=req(3,&s,&bytes)?;
    for(key,value)in[("expected_source_package_sha256",json!("0".repeat(64))),("expected_head_generation",json!(s.head.generation()+1)),("document_id",json!("foreign")),("approved",json!(true)),("limits",json!({"max_output_bytes":u64::MAX}))] {
        let mut v=good.clone();v[key]=value;assert!(Dispatch::prepare_json(&p,&wire(&v)?,None,4).is_err());
    }let mut v=good;v["selector"]["revision_id"]=json!(rev::RevisionId::generate().public_id());assert!(Dispatch::prepare_json(&p,&wire(&v)?,None,4).is_err());Ok(())
}
#[test]
fn dispatch_search_rejects_legacy_bindings_before_reads_and_before_retained_consumers()->TestResult {
    use hwpx_agent_cli::form_product_request::stored::StoredProductFormBindings;
    let map=hwpx_package::NativeFormPackageMap{sections:vec![]};
    let access=domain_ir::form_input::FormInputAccessPolicy{document_protection_sha256:"0".repeat(64),input_allowed:true};
    let bindings=StoredProductFormBindings{map:&map,policies:&[],access:&access};
    let bytes=source(3)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let b=wire(&req(3,&s,&bytes)?)?;
    let before=s.metadata.audit_events()?.len();assert!(matches!(Dispatch::prepare_json(&p,&b,Some(&bindings),4),Err(DE::Bindings)));
    assert_eq!(s.metadata.audit_events()?.len(),before);let out=Dispatch::prepare_json(&p,&b,None,4)?;let before=s.metadata.audit_events()?.len();let called=Cell::new(false);
    assert!(matches!(out.with_verified_bytes(&p,Some(&bindings),5,|_|called.set(true)),Err(DE::Bindings)));
    assert!(matches!(out.require_current_product_route(&p,Some(&bindings),5),Err(DE::Bindings)));
    assert_eq!(s.metadata.audit_events()?.len(),before);assert!(!called.get());
    let Operation::SearchMutation(candidate)=out else{return Err("kind".into())};
    assert_eq!(format!("{:?}",candidate.receipt()),"SearchMutationReceiptRef(<redacted>; candidate_only)");Ok(())
}
#[test]
fn dispatch_legacy_envelopes_do_not_accept_search_fields_or_operations()->TestResult {
    let bytes=source(3)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let good=req(3,&s,&bytes)?;let before=s.metadata.audit_events()?.len();
    for schema in ["hwpx-agent.product-form-request/v1","hwpx-agent.product-operation-request/v2"] {
        let mut v=good.clone();v["schema_version"]=json!(schema);assert!(Dispatch::prepare_json(&p,&wire(&v)?,None,4).is_err());
    }assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[path="style_splice_inventory_product.rs"] mod style_inventory_v1;
#[path="compiled_search_product.rs"] mod compiled_v1;
#[path="compiled_search_routing.rs"] mod routing_v1;
