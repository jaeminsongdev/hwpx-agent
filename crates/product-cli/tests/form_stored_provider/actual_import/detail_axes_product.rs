use super::*;
#[path="border_definition_product.rs"] mod border_definitions;
#[path="style_predicate_product.rs"] mod predicate_cache;
#[path="font_definition_product.rs"] mod font_definitions;
#[path="tab_definition_product.rs"] mod tab_definitions;
#[path="search_storage_product.rs"] mod search_storage;
use hwpx_agent_cli::form_product_request::stored_source_search::{StoredSourceSearchProductRequest as Legacy,PreparedStoredSourceSearchProduct as LegacyPrepared,
    SourceSearchProductError as LegacyError,SourceSearchProductError as SelectorError,
    selector::styles::{StoredSelectorStyleProductRequest as SelectorStyle,PreparedStoredSelectorStyleProduct as SelectorPrepared}};
use hwpx_package::document_import::search::inspection::definitions::SourceDefinitionStyleFilter;
#[allow(dead_code)] #[path="../../../../hwpx-package/tests/support/detail_axes_fixture.rs"] mod details;

fn definition(s:&StoredFixture,raw:&[u8],filter:Value)->Result<Value,Box<dyn Error>> {
    let mut value=envelope(s,raw)?;value.as_object_mut().ok_or("request")?.remove("selector");
    value["schema_version"]=json!("hwpx-agent.product-source-search-request/v3");value["scope"]=json!({"kind":"mapped_document","paragraph_handles":[]});
    value["operation"]=json!({"kind":"find_definition_style","query":"K","case_sensitive":true,"whole_word":false,"max_results":100,"definition_filter":filter});Ok(value)
}
fn selector(s:&StoredFixture,raw:&[u8],filter:Value)->Result<Value,Box<dyn Error>> {
    let mut value=envelope(s,raw)?;value["schema_version"]=json!("hwpx-agent.product-source-search-request/v7");
    value["operation"]=json!({"kind":"find_style","query":"K","regex":false,"case_sensitive":true,"whole_word":false,"max_results":100,
        "style_filter":{"kind":"definition","filter":filter},"review_policy":policy(true,true)});Ok(value)
}
fn legacy(provider:&Provider<'_>,value:&Value)->Result<LegacyPrepared,LegacyError> {Legacy::prepare_json(provider,&serde_json::to_vec(value).map_err(|_|LegacyError::Request)?,Default::default(),4)}
fn scoped(provider:&Provider<'_>,value:&Value)->Result<SelectorPrepared,SelectorError> {SelectorStyle::prepare_json(provider,&serde_json::to_vec(value).map_err(|_|SelectorError::Request)?,Default::default(),4)}
fn legacy_data(out:&LegacyPrepared,provider:&Provider<'_>)->Result<Value,Box<dyn Error>> {Ok(out.with_verified_json(provider,5,|bytes|serde_json::from_slice(bytes))??)}
fn selector_data(out:&SelectorPrepared,provider:&Provider<'_>)->Result<Value,Box<dyn Error>> {Ok(out.with_verified_json(provider,5,|bytes|serde_json::from_slice(bytes))??)}
fn legacy_count(value:&Value)->Result<usize,Box<dyn Error>> {Ok(value["matches"]["matches"].as_array().ok_or("matches")?.len())}
fn selector_count(value:&Value)->Result<usize,Box<dyn Error>> {Ok(value["search"]["result"]["matches"].as_array().ok_or("matches")?.len())}
fn next(out:&SelectorPrepared,cursor:Value)->Result<Value,Box<dyn Error>> {Ok(json!({"schema_version":"hwpx-agent.product-source-search-next-request/v1",
    "search_receipt_sha256":out.navigation_receipt_sha256()?,"navigation":{"direction":"forward","wrap":false,"cursor":cursor}}))}
fn body()->String {fixture::body().replace("<hp:p id='1'>","<hp:p id='1' paraPrIDRef='1' styleIDRef='0'>")
    .replace("<hp:p id='11'>","<hp:p id='11' paraPrIDRef='1' styleIDRef='0'>").replace("<hp:p id='12'>","<hp:p id='12' paraPrIDRef='1' styleIDRef='0'>")
    .replace("<hp:run>","<hp:run charPrIDRef='1'>")}

#[test]
fn all51_character_and_paragraph_details_reach_explicit_v3_and_v7_matchers()->TestResult {
    let raw=details::package(&details::p(1,"K"))?;let original=raw.clone();let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let predicates=details::characters::predicates().into_iter().map(|(yes,no)|("character_details","character_source","run_property",yes,no))
        .chain(details::paragraphs::predicates().into_iter().map(|(yes,no)|("paragraph_details","paragraph_source","direct_property",yes,no))).collect::<Vec<_>>();
    assert_eq!(predicates.len(),51);
    for(field,axis,source,yes,no)in predicates {for(value,total)in[(yes,1),(no,0)] {
        let filter=json!({axis:source,field:value});
        let a=legacy(&provider,&definition(&s,&raw,filter.clone())?)?;a.verify(&provider,5)?;assert_eq!(legacy_count(&legacy_data(&a,&provider)?)?,total);
        let b=scoped(&provider,&selector(&s,&raw,filter)?)?;b.verify(&provider,5)?;assert_eq!(selector_count(&selector_data(&b,&provider)?)?,total);
    }}assert_eq!(raw,original);Ok(())
}
#[test]
fn explicit_run_text_named_and_direct_paragraph_axes_are_not_native_precedence()->TestResult {
    let raw=details::package(&details::p(1,"K").replace("<hp:t>","<hp:t charStyleIDRef='0'>"))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for(axis,total)in[("run_property",1),("text_style",0),("named_style",0)] {
        let filter=json!({"character_source":axis,"character_details":{"underline_position":"bottom"}});
        assert_eq!(legacy_count(&legacy_data(&legacy(&provider,&definition(&s,&raw,filter.clone())?)?,&provider)?)?,total);
        assert_eq!(selector_count(&selector_data(&scoped(&provider,&selector(&s,&raw,filter)?)?,&provider)?)?,total);
    }
    for(axis,total)in[("direct_property",1),("named_style",0)] {
        let filter=json!({"paragraph_source":axis,"paragraph_details":{"condense":17}});
        assert_eq!(legacy_count(&legacy_data(&legacy(&provider,&definition(&s,&raw,filter.clone())?)?,&provider)?)?,total);
        assert_eq!(selector_count(&selector_data(&scoped(&provider,&selector(&s,&raw,filter)?)?,&provider)?)?,total);
    }Ok(())
}
#[test]
fn v3_mapped_and_paragraph_scopes_keep_real_original_handles_and_v4_compatibility()->TestResult {
    let raw=details::package(&(details::p(1,"K")+&details::p(2,"K")))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let filter=json!({"paragraph_source":"direct_property","paragraph_details":{"condense":17}});let value=definition(&s,&raw,filter)?;
    let result=legacy_data(&legacy(&provider,&value)?,&provider)?;assert_eq!(legacy_count(&result)?,2);
    let mut one=value.clone();one["scope"]=json!({"kind":"paragraphs","paragraph_handles":[result["matches"]["matches"][0]["paragraph_anchor"]["opaque_handle"].clone()]});
    assert_eq!(legacy_count(&legacy_data(&legacy(&provider,&one)?,&provider)?)?,1);
    one["schema_version"]=json!("hwpx-agent.product-source-search-request/v4");let out=legacy(&provider,&one)?;
    assert_eq!(out.receipt().profile,"hwpx-agent.product-source-search-preparation/v4");assert_eq!(legacy_count(&legacy_data(&out,&provider)?)?,1);Ok(())
}
#[test]
fn v7_all_four_review_scopes_and_both_style_families_remain_conjunctive()->TestResult {
    let raw=details::package(&body())?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let filter=json!({"character_source":"run_property","paragraph_source":"direct_property","character_details":{"underline_position":"bottom"},"paragraph_details":{"condense":17}});
    let base=selector(&s,&raw,filter)?;let inv=inventory(&provider,&base)?;let range=window(&inv,"memo_body",7,8)?;
    let node=inv["inventory"]["nodes"].as_array().ok_or("nodes")?.iter().find(|n|n["source_handle"]==range["start"]["paragraph_handle"]).ok_or("node")?;
    for(scope,total)in[("document",6),("section",6),("node_set",2),("selection",1)] {
        let mut value=base.clone();value["selector"]["scope"]=json!(scope);
        match scope {"section"=>value["selector"]["section_ids"]=inv["inventory"]["section_ids"].clone(),"node_set"=>value["selector"]["range"]=json!({"node_ids":[node["node_id"].clone()]}),"selection"=>value["selector"]["range"]=range.clone(),_=>{}}
        assert_eq!(selector_count(&selector_data(&scoped(&provider,&value)?,&provider)?)?,total);
        value["operation"]["style_filter"]["filter"]["paragraph_details"]["condense"]=json!(0);
        assert_eq!(selector_count(&selector_data(&scoped(&provider,&value)?,&provider)?)?,0);
    }Ok(())
}
#[test]
fn v3_v7_invalid_new_axes_nested_conditions_and_duplicates_deny_before_reads()->TestResult {
    let raw=details::package(&details::p(1,"K"))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let before=s.metadata.audit_events()?.len();
    for filter in[json!({"paragraph_details":{"condense":17}}),json!({"paragraph_source":"direct_property","character_details":{"emboss":true}}),
        json!({"paragraph_source":"direct_property","paragraph_details":{}}),json!({"paragraph_source":"direct_property","paragraph_details":{"current_layout":{}}}),
        json!({"paragraph_source":"direct_property","paragraph_details":{"condense":76}}),json!({"character_source":"run_property","character_details":{"font_refs":{}}}),
        json!({"paragraph_source":"direct_property","paragraph_details":{"unknown":true}})] {
        assert!(matches!(legacy(&provider,&definition(&s,&raw,filter.clone())?),Err(LegacyError::Request)));
        assert!(matches!(scoped(&provider,&selector(&s,&raw,filter)?),Err(SelectorError::Request)));
    }
    for selected in[false,true] {
        let filter=json!({"paragraph_source":"direct_property","paragraph_details":{"condense":17}});
        let value=if selected{selector(&s,&raw,filter)?}else{definition(&s,&raw,filter)?};let text=serde_json::to_string(&value)?;
        let duplicate=text.replace("\"condense\":17","\"condense\":17,\"conde\\u006ese\":0");assert_ne!(text,duplicate);
        if selected {assert!(matches!(SelectorStyle::prepare_json(&provider,duplicate.as_bytes(),Default::default(),4),Err(SelectorError::Request)));}
        else {assert!(matches!(Legacy::prepare_json(&provider,duplicate.as_bytes(),Default::default(),4),Err(LegacyError::Request)));}
    }assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn canonical_expansion_over16k_is_rejected_before_v3_source_access()->TestResult {
    let raw=details::package(&details::p(1,"K"))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let filter=json!({"paragraph_source":"direct_property","paragraph_details":{"condense":17}});let typed:SourceDefinitionStyleFilter=serde_json::from_value(filter.clone())?;
    let mut value=definition(&s,&raw,filter)?;value["scope"]=json!({"kind":"paragraphs","paragraph_handles":[]});
    let mut length=wire(&value)?.len();
    for index in 0..2000 {
        let handle=json!(format!("p09-pad-{index:05}"));let added=wire(&handle)?.len()+usize::from(index!=0);
        if length+added>16*1024 {break;}
        value["scope"]["paragraph_handles"].as_array_mut().ok_or("handles")?.push(handle);length+=added;
    }
    let bytes=wire(&value)?;assert_eq!(bytes.len(),length);assert!(bytes.len()<=16*1024);let mut canonical=value.clone();canonical["operation"]["definition_filter"]=serde_json::to_value(typed)?;
    assert!(wire(&canonical)?.len()>16*1024);let before=s.metadata.audit_events()?.len();
    assert!(matches!(Legacy::prepare_json(&provider,&bytes,Default::default(),4),Err(LegacyError::Limit)));
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn exact16k_raw_padding_and_canonical_identity_preserve_previous_success_contract()->TestResult {
    let raw=details::package(&details::p(1,"K"))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let filter=json!({"paragraph_source":"direct_property","paragraph_details":{"condense":17}});let base=definition(&s,&raw,filter)?;
    for version in 1..=4 {
        let mut value=base.clone();value["schema_version"]=json!(format!("hwpx-agent.product-source-search-request/v{version}"));
        if version<=2 {value["operation"]["kind"]=json!("find_literal");value["operation"].as_object_mut().ok_or("operation")?.remove("definition_filter");}
        let out=legacy(&provider,&value)?;let mut bytes=wire(&value)?;bytes.resize(16*1024,b' ');let padded=Legacy::prepare_json(&provider,&bytes,Default::default(),4)?;
        assert_ne!(out.receipt().raw_request_sha256,padded.receipt().raw_request_sha256);assert_eq!(out.receipt().canonical_request_sha256,padded.receipt().canonical_request_sha256);
        assert_eq!(out.receipt().stored.result_sha256,padded.receipt().stored.result_sha256);bytes.push(b' ');
        assert!(matches!(Legacy::prepare_json(&provider,&bytes,Default::default(),4),Err(LegacyError::Limit)));
    }Ok(())
}
#[test]
fn v7_retained_cursor_cannot_be_reused_for_different_details_with_the_same_hits()->TestResult {
    let raw=details::package(&details::p(1,"K K"))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let a=selector(&s,&raw,json!({"paragraph_source":"direct_property","paragraph_details":{"condense":17}}))?;let out=scoped(&provider,&a)?;
    let first:Value=out.with_next_verified_json(&provider,&wire(&next(&out,Value::Null)?)?,5,|bytes|serde_json::from_slice(bytes))??;
    let second:Value=out.with_next_verified_json(&provider,&wire(&next(&out,first["cursor"].clone())?)?,5,|bytes|serde_json::from_slice(bytes))??;assert_eq!(second["match_index"],1);
    let b=selector(&s,&raw,json!({"paragraph_source":"direct_property","paragraph_details":{"checked":true}}))?;let other=scoped(&provider,&b)?;
    assert_ne!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);let called=Cell::new(false);
    assert!(other.with_next_verified_json(&provider,&wire(&next(&out,first["cursor"].clone())?)?,5,|_|called.set(true)).is_err());assert!(!called.get());Ok(())
}
#[test]
fn retained_v3_v7_details_still_require_current_write_acl_and_deny_quarantine()->TestResult {
    let raw=details::package(&details::p(1,"K"))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let filter=json!({"paragraph_source":"direct_property","paragraph_details":{"condense":17}});let a=definition(&s,&raw,filter.clone())?;let b=selector(&s,&raw,filter)?;
    let reader=s.provider()?;assert!(legacy(&reader,&a).is_err());assert!(scoped(&reader,&b).is_err());let x=legacy(&provider,&a)?;let y=scoped(&provider,&b)?;
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;let called=Cell::new(false);
    assert!(x.with_verified_json(&provider,6,|_|called.set(true)).is_err());assert!(y.with_verified_json(&provider,6,|_|called.set(true)).is_err());assert!(!called.get());
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;x.verify(&provider,8)?;y.verify(&provider,8)?;
    s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("DETAIL_AXES_TEST")?,9)?;
    // A clean independent source must also fail AEAD before any earlier ACL/quarantine denial.
    {
        let fresh=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(fresh,fresh_actor,fresh_provider);
        let filter=json!({"paragraph_source":"direct_property","paragraph_details":{"condense":17}});
        let a=definition(&fresh,&raw,filter.clone())?;let b=selector(&fresh,&raw,filter)?;
        let first=legacy(&fresh_provider,&a)?;let second=scoped(&fresh_provider,&b)?;
        fresh.blobs.tamper.store(true,Ordering::SeqCst);let called=Cell::new(false);
        assert!(first.with_verified_json(&fresh_provider,6,|_|called.set(true)).is_err());
        assert!(second.with_verified_json(&fresh_provider,6,|_|called.set(true)).is_err());
        assert!(legacy(&fresh_provider,&a).is_err());assert!(scoped(&fresh_provider,&b).is_err());assert!(!called.get());
    }
    assert!(x.verify(&provider,10).is_err());assert!(y.verify(&provider,10).is_err());Ok(())
}
#[test]
fn new_details_preserve_privacy_original_source_head_and_closed_native_routes()->TestResult {
    let raw=details::package(&details::p(1,"K"))?;let original=raw.clone();let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let filter=json!({"character_source":"run_property","paragraph_source":"direct_property","character_details":{"emboss":true},"paragraph_details":{"condense":17}});
    let x=legacy(&provider,&definition(&s,&raw,filter.clone())?)?;let y=scoped(&provider,&selector(&s,&raw,filter)?)?;
    assert!(matches!(x.require_current_product_route(&provider,5),Err(LegacyError::RouteUnqualified)));
    assert!(matches!(y.require_current_product_route(&provider,5),Err(SelectorError::RouteUnqualified)));
    assert!(!x.receipt().idempotency_key_claimed);assert!(!y.receipt().full_search_product_native_cas_execution_publication_authority);
    assert_eq!(s.metadata.audit_events()?.iter().filter(|event|event.event=="artifact.ingested").count(),2);
    assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(raw,original);Ok(())
}
