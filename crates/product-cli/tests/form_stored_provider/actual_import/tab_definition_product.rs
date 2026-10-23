//! Actual stored search paths; no native launch or product execution permission.
use super::*;
use hwpx_agent_cli::form_product_request::stored_source_search::selector::resolved_styles::{StoredResolvedStyleProductRequest as Resolved,PreparedStoredResolvedStyleProduct as ResolvedPrepared};
#[path="../../../../hwpx-package/tests/support/tab_definition_fixture.rs"] mod tabs;
fn explicit(value:Value)->Value {json!({"paragraph_source":"direct_property","tab_details":value})}
fn v9(s:&StoredFixture,raw:&[u8],filter:Value)->Result<Value,Box<dyn Error>> {
    let mut value=envelope(s,raw)?;value["schema_version"]=json!("hwpx-agent.product-source-search-request/v9");
    value["operation"]=json!({"kind":"find_resolved_style","query":"K","regex":false,"case_sensitive":true,"whole_word":false,"max_results":100,"style_filter":filter,"review_policy":policy(true,true)});Ok(value)
}
fn resolved(provider:&Provider<'_>,value:&Value)->Result<ResolvedPrepared,LegacyError> {Resolved::prepare_json(provider,&wire(value).map_err(|_|LegacyError::Request)?,Default::default(),4)}
fn data(out:&ResolvedPrepared,provider:&Provider<'_>)->Result<Value,Box<dyn Error>> {Ok(out.with_verified_json(provider,5,|bytes|serde_json::from_slice(bytes))??)}
#[test]
fn actual16_tab_conditions_reach_v3_v7_v9_positive_and_negative()->TestResult {
    let raw=tabs::package(&tabs::p(1,"K",0))?;let original=raw.clone();let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    assert_eq!(tabs::predicates().len(),16);
    for(yes,no)in tabs::predicates(){for(value,count)in[(yes,1),(no,0)] {
        let filter=explicit(value.clone());let a=legacy(&provider,&definition(&s,&raw,filter.clone())?)?;
        assert_eq!(legacy_count(&legacy_data(&a,&provider)?)?,count);
        let b=scoped(&provider,&selector(&s,&raw,filter)?)?;assert_eq!(selector_count(&selector_data(&b,&provider)?)?,count);
        let c=resolved(&provider,&v9(&s,&raw,json!({"tab_details":value}))?)?;let out=data(&c,&provider)?;
        assert_eq!(selector_count(&out)?,count);assert_eq!(out["coverage"]["requested_paragraph_axis_complete"],true);
    }}assert_eq!(original,raw);Ok(())
}
#[test]
fn tabs_keep_v4_and_named_axes_and_all_four_v7_review_scopes()->TestResult {
    let raw=tabs::package(&tabs::p(1,"K",1))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for(axis,count)in[("direct_property",0),("named_style",1)] {
        let mut value=definition(&s,&raw,json!({"paragraph_source":axis,"tab_details":{"auto_tab_left":true}}))?;
        value["schema_version"]=json!("hwpx-agent.product-source-search-request/v4");assert_eq!(legacy_count(&legacy_data(&legacy(&provider,&value)?,&provider)?)?,count);
    }
    let body=fixture::body().replace("<hp:p id='1'>","<hp:p id='1' paraPrIDRef='0' styleIDRef='0'>")
        .replace("<hp:p id='11'>","<hp:p id='11' paraPrIDRef='0' styleIDRef='0'>")
        .replace("<hp:p id='12'>","<hp:p id='12' paraPrIDRef='0' styleIDRef='0'>").replace("<hp:run>","<hp:run charPrIDRef='0'>");
    let raw=tabs::package(&body)?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let base=selector(&s,&raw,explicit(json!({"auto_tab_left":true,"stop_count":3})))?;
    let inv=inventory(&provider,&base)?;let range=window(&inv,"memo_body",7,8)?;
    let node=inv["inventory"]["nodes"].as_array().ok_or("nodes")?.iter().find(|n|n["source_handle"]==range["start"]["paragraph_handle"]).ok_or("node")?;
    for(scope,total)in[("document",6),("section",6),("node_set",2),("selection",1)] {
        let mut value=base.clone();value["selector"]["scope"]=json!(scope);
        match scope {"section"=>value["selector"]["section_ids"]=inv["inventory"]["section_ids"].clone(),"node_set"=>value["selector"]["range"]=json!({"node_ids":[node["node_id"].clone()]}),"selection"=>value["selector"]["range"]=range.clone(),_=>{}}
        assert_eq!(selector_count(&selector_data(&scoped(&provider,&value)?,&provider)?)?,total);
        value["operation"]["style_filter"]["filter"]["tab_details"]["stop_count"]=json!(0);
        assert_eq!(selector_count(&selector_data(&scoped(&provider,&value)?,&provider)?)?,0);
    }Ok(())
}
#[test]
fn invalid_tab_predicates_and_escaped_duplicates_are_request_errors_before_source_access()->TestResult {
    let raw=tabs::package(&tabs::p(1,"K",0))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let before=s.metadata.audit_events()?.len();
    for value in[json!({}),json!({"unknown":true}),json!({"stop_count":262145}),tabs::direct(0,json!({"position":-1})),
        tabs::direct(0,json!({})),tabs::direct(0,json!({"position":2147483648_i64})),tabs::direct(0,json!({"unit":{"kind":"present","unit":"pixel"}})),
        tabs::indexed(0,json!({"kind":"hwp_unit_char","current":{}}))] {
        assert!(matches!(legacy(&provider,&definition(&s,&raw,explicit(value.clone()))?),Err(LegacyError::Request)));
        assert!(matches!(scoped(&provider,&selector(&s,&raw,explicit(value.clone()))?),Err(LegacyError::Request)));
        assert!(matches!(resolved(&provider,&v9(&s,&raw,json!({"tab_details":value}))?),Err(LegacyError::Request)));
    }
    for(index,value)in[definition(&s,&raw,explicit(json!({"auto_tab_left":true})))?,selector(&s,&raw,explicit(json!({"auto_tab_left":true})))?,v9(&s,&raw,json!({"tab_details":{"auto_tab_left":true}}))?].iter().enumerate() {
        let raw=serde_json::to_string(value)?;let duplicate=raw.replace("\"auto_tab_left\":true","\"auto_tab_left\":true,\"auto_tab_le\\u0066t\":false");assert_ne!(raw,duplicate);
        let denied=match index {0=>Legacy::prepare_json(&provider,duplicate.as_bytes(),Default::default(),4).is_err(),1=>SelectorStyle::prepare_json(&provider,duplicate.as_bytes(),Default::default(),4).is_err(),_=>Resolved::prepare_json(&provider,duplicate.as_bytes(),Default::default(),4).is_err()};assert!(denied);
    }assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn tab_filter_identity_navigation_and_font_redaction_are_preserved_together()->TestResult {
    let header=tabs::header()?;let font_name=tabs::font_name()?;let raw=tabs::definition::package_with_header(&tabs::p(1,"K K",0),&header)?;
    let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let value=json!({"paragraph_source":"direct_property","tab_details":{"auto_tab_left":true},"character_source":"run_property",
        "font_details":{"hangul":{"face":{"query":font_name,"regex":false,"case_sensitive":true,"whole_word":false}}}});
    let one=scoped(&provider,&selector(&s,&raw,value.clone())?)?;let mut changed=value.clone();changed["tab_details"]=json!({"stop_count":3});
    let two=scoped(&provider,&selector(&s,&raw,changed)?)?;assert_ne!(one.receipt().canonical_request_sha256,two.receipt().canonical_request_sha256);
    let mut direct=value;direct.as_object_mut().ok_or("object")?.remove("character_source");direct.as_object_mut().ok_or("object")?.remove("paragraph_source");
    let three=resolved(&provider,&v9(&s,&raw,direct)?)?;
    for out in[selector_data(&one,&provider)?,data(&three,&provider)?] {
        let text=serde_json::to_string(&out)?;assert!(!text.contains(&font_name));assert!(text.contains("tab_details"));assert!(text.contains("source-font-definition-filter-binding/v1"));
    }
    let first:Value=one.with_next_verified_json(&provider,&wire(&next(&one,Value::Null)?)?,5,|bytes|serde_json::from_slice(bytes))??;
    let called=Cell::new(false);assert!(two.with_next_verified_json(&provider,&wire(&next(&one,first["cursor"].clone())?)?,5,|_|called.set(true)).is_err());assert!(!called.get());Ok(())
}
#[test]
fn tab_search_keeps_acl_aead_and_unqualified_product_route_closed()->TestResult {
    let raw=tabs::package(&tabs::p(1,"K",0))?;
    for tamper in[false,true] {
        let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
        let one=legacy(&provider,&definition(&s,&raw,explicit(json!({"stop_count":3})))?)?;
        let two=scoped(&provider,&selector(&s,&raw,explicit(json!({"stop_count":3})))?)?;
        let three=resolved(&provider,&v9(&s,&raw,json!({"tab_details":{"stop_count":3}}))?)?;
        assert!(matches!(three.require_current_product_route(&provider,5),Err(LegacyError::RouteUnqualified)));
        if tamper{s.blobs.tamper.store(true,Ordering::SeqCst);}else{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),7)?;}
        let called=Cell::new(false);
        assert!(one.with_verified_json(&provider,7,|_|called.set(true)).is_err());assert!(two.with_verified_json(&provider,7,|_|called.set(true)).is_err());
        assert!(three.with_verified_json(&provider,7,|_|called.set(true)).is_err());assert!(!called.get());
    }Ok(())
}
