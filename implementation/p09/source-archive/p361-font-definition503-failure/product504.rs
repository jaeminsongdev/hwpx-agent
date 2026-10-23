//! Stored product-path contracts for original font declarations, never installed/native font claims.
//! Source integration and these new tests remain UNVERIFIED / NOT_RUN.
use super::*;
use hwpx_agent_cli::form_product_request::stored_source_search::selector::resolved_styles::{
    StoredResolvedStyleProductRequest as Resolved,PreparedStoredResolvedStyleProduct as ResolvedPrepared};
#[path="../../../../hwpx-package/tests/support/font_definition_fixture.rs"] mod fonts;

fn v9(s:&StoredFixture,raw:&[u8],filter:Value)->Result<Value,Box<dyn Error>> {
    let mut value=envelope(s,raw)?;value["schema_version"]=json!("hwpx-agent.product-source-search-request/v9");
    value["operation"]=json!({"kind":"find_resolved_style","query":"K","regex":false,"case_sensitive":true,"whole_word":false,"max_results":100,
        "style_filter":filter,"review_policy":policy(true,true)});Ok(value)
}
fn resolved(provider:&Provider<'_>,value:&Value)->Result<ResolvedPrepared,LegacyError> {
    Resolved::prepare_json(provider,&wire(value).map_err(|_|LegacyError::Request)?,Default::default(),4)
}
fn resolved_data(out:&ResolvedPrepared,provider:&Provider<'_>)->Result<Value,Box<dyn Error>> {
    Ok(out.with_verified_json(provider,5,|bytes|serde_json::from_slice(bytes))??)
}
fn named(query:&str)->Value {json!({"query":query,"regex":false,"case_sensitive":true,"whole_word":false})}
fn explicit(fonts:Value)->Value {json!({"character_source":"run_property","font_details":fonts})}

#[test]
fn font19_conditions_in_all7_languages_reach_stored_v3_v7_and_v9_original_resources()->TestResult {
    let raw=fonts::package(&fonts::p(1,"K",0))?;let original=raw.clone();
    let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for(language,native)in[("hangul","Hangul"),("latin","Latin"),("hanja","Hanja"),("japanese","Japanese"),("other","Other"),("symbol","Symbol"),("user","User")] {
        let predicates=fonts::predicates(native);assert_eq!(predicates.len(),19);
        for(yes,no)in predicates {for(value,total)in[(yes,1),(no,0)] {
            let fonts=json!({language:value});let filter=explicit(fonts.clone());
            let a=legacy(&provider,&definition(&s,&raw,filter.clone())?)?;
            assert_eq!(legacy_count(&legacy_data(&a,&provider)?)?,total,"v3/{language}");
            let b=scoped(&provider,&selector(&s,&raw,filter)?)?;
            assert_eq!(selector_count(&selector_data(&b,&provider)?)?,total,"v7/{language}");
            let c=resolved(&provider,&v9(&s,&raw,json!({"font_details":fonts}))?)?;
            let result=resolved_data(&c,&provider)?;assert_eq!(selector_count(&result)?,total,"v9/{language}");
            assert_eq!(result["coverage"]["requested_character_axis_complete"],true);
        }}
    }assert_eq!(raw,original);Ok(())
}
#[test]
fn font_filters_keep_v4_explicit_axes_four_review_scopes_and_language_conjunction()->TestResult {
    let body=fixture::body().replace("<hp:p id='1'>","<hp:p id='1' paraPrIDRef='0' styleIDRef='0'>")
        .replace("<hp:p id='11'>","<hp:p id='11' paraPrIDRef='0' styleIDRef='0'>")
        .replace("<hp:p id='12'>","<hp:p id='12' paraPrIDRef='0' styleIDRef='0'>")
        .replace("<hp:run>","<hp:run charPrIDRef='0'>");
    let raw=fonts::package(&body)?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let filter=explicit(json!({"hangul":{"face":named("P09.Hangul.Font")},"latin":{"face":named("P09.Latin.Font")}}));
    let mut old=definition(&s,&raw,filter.clone())?;old["schema_version"]=json!("hwpx-agent.product-source-search-request/v4");
    assert_eq!(legacy_count(&legacy_data(&legacy(&provider,&old)?,&provider)?)?,6);
    let base=selector(&s,&raw,filter)?;let inv=inventory(&provider,&base)?;let range=window(&inv,"memo_body",7,8)?;
    let node=inv["inventory"]["nodes"].as_array().ok_or("nodes")?.iter().find(|n|n["source_handle"]==range["start"]["paragraph_handle"]).ok_or("node")?;
    for(scope,total)in[("document",6),("section",6),("node_set",2),("selection",1)] {
        let mut value=base.clone();value["selector"]["scope"]=json!(scope);
        match scope {"section"=>value["selector"]["section_ids"]=inv["inventory"]["section_ids"].clone(),
            "node_set"=>value["selector"]["range"]=json!({"node_ids":[node["node_id"].clone()]}),"selection"=>value["selector"]["range"]=range.clone(),_=>{}}
        assert_eq!(selector_count(&selector_data(&scoped(&provider,&value)?,&provider)?)?,total);
        value["operation"]["style_filter"]["filter"]["font_details"]["latin"]["face"]=named("P09.Hangul.Font");
        assert_eq!(selector_count(&selector_data(&scoped(&provider,&value)?,&provider)?)?,0);
    }Ok(())
}
#[test]
fn malformed_empty_unknown_or_duplicate_font_conditions_deny_before_stored_source_reads()->TestResult {
    let raw=fonts::package(&fonts::p(1,"K",0))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let before=s.metadata.audit_events()?.len();
    for font in[json!({}),json!({"hangul":{}}),json!({"unknown":{"is_embedded":true}}),json!({"hangul":{"font_type":"TTF"}}),
        json!({"hangul":{"binary_item_id_ref":{"kind":"absent","value":"unexpected"}}}),
        json!({"hangul":{"substitute":{"kind":"absent","filter":{"font_type":"true_type"}}}}),
        json!({"hangul":{"type_info":{"kind":"present","filter":{}}}}),
        json!({"hangul":{"face":{"query":".*","regex":true,"case_sensitive":true,"whole_word":false}}})] {
        assert!(matches!(legacy(&provider,&definition(&s,&raw,explicit(font.clone()))?),Err(LegacyError::Request)));
        assert!(matches!(scoped(&provider,&selector(&s,&raw,explicit(font.clone()))?),Err(LegacyError::Request)));
        assert!(matches!(resolved(&provider,&v9(&s,&raw,json!({"font_details":font}))?),Err(LegacyError::Request)));
    }
    let font=json!({"hangul":{"is_embedded":true}});
    let requests=[definition(&s,&raw,explicit(font.clone()))?,selector(&s,&raw,explicit(font.clone()))?,v9(&s,&raw,json!({"font_details":font}))?];
    for(index,value)in requests.into_iter().enumerate() {
        let raw=serde_json::to_string(&value)?;let duplicated=raw.replace("\"is_embedded\":true","\"is_embedded\":true,\"is_embed\\u0064ed\":false");assert_ne!(raw,duplicated);
        let denied=match index {0=>Legacy::prepare_json(&provider,duplicated.as_bytes(),Default::default(),4).is_err(),
            1=>SelectorStyle::prepare_json(&provider,duplicated.as_bytes(),Default::default(),4).is_err(),
            _=>Resolved::prepare_json(&provider,duplicated.as_bytes(),Default::default(),4).is_err()};assert!(denied);
    }assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn font_name_and_binary_text_remain_request_bound_without_leaking_from_retained_results()->TestResult {
    let raw=fonts::package(&fonts::p(1,"K K",0))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let fonts=json!({"hangul":{"face":named("P09.Hangul.Font"),"binary_item_id_ref":{"kind":"present","value":"declared-font-Hangul"},
        "substitute":{"kind":"present","filter":{"face":named("P09.Hangul.Substitute")}},
        "type_info":{"kind":"present","filter":{"serif_style":{"kind":"present","value":"declared-serif"}}}}});
    let a=selector(&s,&raw,explicit(fonts.clone()))?;let b=selector(&s,&raw,explicit(json!({"hangul":{"is_embedded":true}})))?;
    let one=scoped(&provider,&a)?;let two=scoped(&provider,&b)?;let direct=resolved(&provider,&v9(&s,&raw,json!({"font_details":fonts}))?)?;
    assert_ne!(one.receipt().canonical_request_sha256,two.receipt().canonical_request_sha256);
    assert_eq!(selector_count(&selector_data(&one,&provider)?)?,selector_count(&selector_data(&two,&provider)?)?);
    for value in[selector_data(&one,&provider)?,resolved_data(&direct,&provider)?] {
        let text=serde_json::to_string(&value)?;
        for hidden in["P09.Hangul.Font","declared-font-Hangul","P09.Hangul.Substitute","declared-serif"]{assert!(!text.contains(hidden));}
        assert!(text.contains("hwpx-agent.source-font-definition-filter-binding/v1"));
    }
    let first:Value=one.with_next_verified_json(&provider,&wire(&next(&one,Value::Null)?)?,5,|bytes|serde_json::from_slice(bytes))??;
    let called=Cell::new(false);assert!(two.with_next_verified_json(&provider,&wire(&next(&one,first["cursor"].clone())?)?,5,|_|called.set(true)).is_err());
    assert!(!called.get());Ok(())
}
#[test]
fn font_predicates_never_bypass_current_acl_aead_or_closed_native_product_route()->TestResult {
    let raw=fonts::package(&fonts::p(1,"K",0))?;let original=raw.clone();
    for tamper in[false,true] {
        let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
        let filter=explicit(json!({"hangul":{"is_embedded":true}}));let a=definition(&s,&raw,filter.clone())?;let b=selector(&s,&raw,filter)?;
        let c=v9(&s,&raw,json!({"font_details":{"hangul":{"is_embedded":true}}}))?;
        let one=legacy(&provider,&a)?;let two=scoped(&provider,&b)?;let three=resolved(&provider,&c)?;
        assert!(matches!(three.require_current_product_route(&provider,5),Err(LegacyError::RouteUnqualified)));
        if tamper{s.blobs.tamper.store(true,Ordering::SeqCst);}else{
            s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),7)?;
        }
        let called=Cell::new(false);
        assert!(one.with_verified_json(&provider,7,|_|called.set(true)).is_err());
        assert!(two.with_verified_json(&provider,7,|_|called.set(true)).is_err());
        assert!(three.with_verified_json(&provider,7,|_|called.set(true)).is_err());
        assert!(legacy(&provider,&a).is_err());assert!(scoped(&provider,&b).is_err());assert!(resolved(&provider,&c).is_err());assert!(!called.get());
    }assert_eq!(raw,original);Ok(())
}
