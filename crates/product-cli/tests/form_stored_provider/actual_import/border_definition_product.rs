use super::*;
use hwpx_agent_cli::form_product_request::stored_source_search::selector::resolved_styles::{StoredResolvedStyleProductRequest as Resolved,PreparedStoredResolvedStyleProduct as ResolvedPrepared};
#[allow(dead_code)] #[path="../../../../hwpx-package/tests/support/border_definition_fixture.rs"] mod border;
fn v9(s:&StoredFixture,raw:&[u8],filter:Value)->Result<Value,Box<dyn Error>> {
    let mut value=envelope(s,raw)?;value["schema_version"]=json!("hwpx-agent.product-source-search-request/v9");
    value["operation"]=json!({"kind":"find_resolved_style","query":"K","regex":false,"case_sensitive":true,"whole_word":false,"max_results":100,
        "style_filter":filter,"review_policy":policy(true,true)});Ok(value)
}
fn resolved(provider:&Provider<'_>,value:&Value)->Result<ResolvedPrepared,LegacyError> {Resolved::prepare_json(provider,&wire(value).map_err(|_|LegacyError::Request)?,Default::default(),4)}
fn resolved_data(out:&ResolvedPrepared,provider:&Provider<'_>)->Result<Value,Box<dyn Error>> {Ok(out.with_verified_json(provider,5,|bytes|serde_json::from_slice(bytes))??)}
#[test]
fn referenced_border30_conditions_reach_actual_v3_v4_v7_and_required_v9_products()->TestResult {
    let raw=border::package(&border::p(1,"K"))?;let original=raw.clone();let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    assert_eq!(border::predicates().len(),30);
    for(field,axis,source)in[("character_details","character_source","run_property"),("paragraph_details","paragraph_source","direct_property")] {
        for(yes,no)in border::predicates(){for(value,total)in[(yes,1),(no,0)] {
            let explicit=json!({axis:source,field:{"border_definition":value.clone()}});
            let base=definition(&s,&raw,explicit.clone())?;
            assert_eq!(legacy_count(&legacy_data(&legacy(&provider,&base)?,&provider)?)?,total);
            let mut compatible=base;compatible["schema_version"]=json!("hwpx-agent.product-source-search-request/v4");
            assert_eq!(legacy_count(&legacy_data(&legacy(&provider,&compatible)?,&provider)?)?,total);
            assert_eq!(selector_count(&selector_data(&scoped(&provider,&selector(&s,&raw,explicit)?)?,&provider)?)?,total);
            assert_eq!(selector_count(&resolved_data(&resolved(&provider,&v9(&s,&raw,json!({field:{"border_definition":value}}))?)?,&provider)?)?,total);
        }}
    }assert_eq!(raw,original);Ok(())
}
#[test]
fn invalid_nested_border_and_decoded_duplicates_deny_before_any_stored_source_read()->TestResult {
    let raw=border::package(&border::p(1,"K"))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let before=s.metadata.audit_events()?.len();
    for value in[json!({}),json!({"left":{}}),json!({"back_slash":{}}),json!({"left":{"width":"unknown"}}),
        json!({"fill_brush":{"kind":"window","filter":{}}}),json!({"fill_brush":{"kind":"window","filter":{"alpha":256}}})] {
        let explicit=json!({"character_source":"run_property","character_details":{"border_definition":value.clone()}});
        assert!(matches!(legacy(&provider,&definition(&s,&raw,explicit.clone())?),Err(LegacyError::Request)));
        assert!(matches!(scoped(&provider,&selector(&s,&raw,explicit)?),Err(LegacyError::Request)));
        assert!(matches!(resolved(&provider,&v9(&s,&raw,json!({"character_details":{"border_definition":value}}))?),Err(LegacyError::Request)));
    }
    let filter=json!({"character_details":{"border_definition":{"shadow":false}}});
    let value=v9(&s,&raw,filter)?;let text=serde_json::to_string(&value)?;
    let duplicate=text.replace("\"shadow\":false","\"shadow\":false,\"sha\\u0064ow\":true");assert_ne!(text,duplicate);
    assert!(matches!(Resolved::prepare_json(&provider,duplicate.as_bytes(),Default::default(),4),Err(LegacyError::Request)));
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn current_acl_and_aead_deny_retained_border_results_and_new_requests()->TestResult {
    let raw=border::package(&border::p(1,"K"))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let explicit=json!({"character_source":"run_property","character_details":{"border_definition":{"three_d":true}}});
    let a=definition(&s,&raw,explicit.clone())?;let b=selector(&s,&raw,explicit)?;let c=v9(&s,&raw,json!({"character_details":{"border_definition":{"three_d":true}}}))?;
    let first=legacy(&provider,&a)?;let second=scoped(&provider,&b)?;let third=resolved(&provider,&c)?;
    let called=Cell::new(false);s.blobs.tamper.store(true,Ordering::SeqCst);
    assert!(first.with_verified_json(&provider,6,|_|called.set(true)).is_err());assert!(second.with_verified_json(&provider,6,|_|called.set(true)).is_err());
    assert!(third.with_verified_json(&provider,6,|_|called.set(true)).is_err());assert!(legacy(&provider,&a).is_err());assert!(scoped(&provider,&b).is_err());assert!(resolved(&provider,&c).is_err());assert!(!called.get());
    s.blobs.tamper.store(false,Ordering::SeqCst);s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),7)?;
    assert!(first.verify(&provider,7).is_err());assert!(second.verify(&provider,7).is_err());assert!(third.verify(&provider,7).is_err());
    assert!(legacy(&provider,&a).is_err());assert!(scoped(&provider,&b).is_err());assert!(resolved(&provider,&c).is_err());Ok(())
}
#[test]
fn same_hits_different_border_predicates_cannot_reuse_retained_v7_or_v9_cursor()->TestResult {
    let raw=border::package(&border::p(1,"K K"))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for direct in[false,true] {
        let make=|property:&str|->Result<Value,Box<dyn Error>> {let filter=json!({"character_details":{"border_definition":{property:true}}});
            if direct{v9(&s,&raw,filter)}else{let mut filter=filter;filter["character_source"]=json!("run_property");selector(&s,&raw,filter)}};
        // Both properties true in border1, with distinct canonical requests.
        let a=make("three_d")?;let b=make("break_cell_separate_line")?;
        let called=Cell::new(false);
        if direct {
            let one=resolved(&provider,&a)?;let two=resolved(&provider,&b)?;
            assert_ne!(one.receipt().canonical_request_sha256,two.receipt().canonical_request_sha256);
            let request=json!({"schema_version":"hwpx-agent.product-source-search-next-request/v1","search_receipt_sha256":one.navigation_receipt_sha256()?,
                "navigation":{"direction":"forward","wrap":false,"cursor":null}});
            let first:Value=one.with_next_verified_json(&provider,&wire(&request)?,5,|bytes|serde_json::from_slice(bytes))??;
            let mut request=request;request["navigation"]["cursor"]=first["cursor"].clone();
            assert!(two.with_next_verified_json(&provider,&wire(&request)?,5,|_|called.set(true)).is_err());
        }else {
            let one=scoped(&provider,&a)?;let two=scoped(&provider,&b)?;
            let first:Value=one.with_next_verified_json(&provider,&wire(&next(&one,Value::Null)?)?,5,|bytes|serde_json::from_slice(bytes))??;
            assert!(two.with_next_verified_json(&provider,&wire(&next(&one,first["cursor"].clone())?)?,5,|_|called.set(true)).is_err());
        }assert!(!called.get());
    }Ok(())
}
#[test]
fn border_definition_products_keep_closed_native_routes_and_original_stored_source()->TestResult {
    let raw=border::package(&border::p(1,"K"))?;let before=raw.clone();let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let out=resolved(&provider,&v9(&s,&raw,json!({"character_details":{"border_definition":{"three_d":true}},"paragraph_details":{"border_definition":{"shadow":false}}}))?)?;
    let result=resolved_data(&out,&provider)?;assert_eq!(selector_count(&result)?,1);assert_eq!(result["native_cascade_visibility_or_execution_authority"],false);
    assert!(matches!(out.require_current_product_route(&provider,5),Err(LegacyError::RouteUnqualified)));assert_eq!(raw,before);Ok(())
}
