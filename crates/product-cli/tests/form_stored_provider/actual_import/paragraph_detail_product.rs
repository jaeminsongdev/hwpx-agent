use super::*;
#[allow(dead_code)] #[path="../../../../hwpx-package/tests/support/paragraph_detail_fixture.rs"] mod detail_fixture;

#[test]
fn paragraph_product_all27_predicates_use_current_stored_source_and_strict_v9()->TestResult {
    let raw=detail_fixture::package(&p(1,"K"))?;let original=raw.clone();let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for(yes,no)in detail_fixture::predicates(){for(details,total)in[(yes,1),(no,0)] {
        let mut v=request(&s,&raw)?;v["operation"]["style_filter"]=json!({"paragraph_details":details});
        let out=resolved!(&provider,&v)?;out.verify(&provider,5)?;let found=data(&out,&provider)?;
        assert_eq!(count(&found)?,total);assert_eq!(found["coverage"]["requested_paragraph_axis_complete"],true);
        assert_eq!(found["native_cascade_visibility_or_execution_authority"],false);
    }}assert_eq!(raw,original);Ok(())
}
#[test]
fn paragraph_product_empty_unknown_duplicate_units_and_overflows_reject_before_reads()->TestResult {
    let raw=detail_fixture::package(&p(1,"K"))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let base=request(&s,&raw)?;let before=s.metadata.audit_events()?.len();
    for details in[json!({}),json!({"current_layout":{}}),json!({"fallback_layout":{"indent":{"value":3}}}),json!({"unknown":true}),
        json!({"condense":76}),json!({"border_offset_left":2147483648_i64}),json!({"heading":{"kind":"meta_tag"}}),
        json!({"non_latin_word":"hyphenation"}),json!({"current_layout":{"line_spacing":{"spacing_type":"percent","value":501,"unit":"hwp_unit"}}})] {
        let mut v=base.clone();v["operation"]["style_filter"]=json!({"paragraph_details":details});assert!(matches!(resolved!(&provider,&v),Err(PE::Request)));
    }
    let mut v=base;v["operation"]["style_filter"]=json!({"paragraph_details":{"condense":17}});let text=serde_json::to_string(&v)?;
    let duplicate=text.replace("\"condense\":17","\"condense\":17,\"conde\\u006ese\":0");assert_ne!(text,duplicate);
    assert!(matches!(Resolved::prepare_json(&provider,duplicate.as_bytes(),Default::default(),4),Err(PE::Request)));
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn paragraph_product_all_four_scopes_combine_character_alignment_and_detail_conditions()->TestResult {
    let raw=detail_fixture::package(&body())?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut base=request(&s,&raw)?;
    base["operation"]["style_filter"]=json!({"bold":true,"alignment":"right","paragraph_details":{"condense":17,"snap_to_grid":false}});
    let inv=inventory(&provider,&base)?;let range=window(&inv,"memo_body",7,8)?;let node=inv["inventory"]["nodes"].as_array().ok_or("nodes")?.iter()
        .find(|n|n["source_handle"]==range["start"]["paragraph_handle"]).ok_or("node")?;
    for(scope,total)in[("document",6),("section",6),("node_set",2),("selection",1)] {
        let mut v=base.clone();v["selector"]["scope"]=json!(scope);
        match scope {"section"=>v["selector"]["section_ids"]=inv["inventory"]["section_ids"].clone(),"node_set"=>v["selector"]["range"]=json!({"node_ids":[node["node_id"].clone()]}),"selection"=>v["selector"]["range"]=range.clone(),_=>{}}
        assert_eq!(count(&data(&resolved!(&provider,&v)?,&provider)?)?,total);
        v["operation"]["style_filter"]["paragraph_details"]["snap_to_grid"]=json!(true);
        assert_eq!(count(&data(&resolved!(&provider,&v)?,&provider)?)?,0);
    }Ok(())
}
#[test]
fn paragraph_product_same_match_set_does_not_allow_cross_predicate_cursor_reuse()->TestResult {
    let raw=detail_fixture::package(&p(1,"K K"))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut a=request(&s,&raw)?;
    a["operation"]["style_filter"]=json!({"paragraph_details":{"condense":17}});let out=resolved!(&provider,&a)?;
    let first:Value=out.with_next_verified_json(&provider,&wire(&next(&out,Value::Null,"forward",false)?)?,5,|b|serde_json::from_slice(b))??;
    let second:Value=out.with_next_verified_json(&provider,&wire(&next(&out,first["cursor"].clone(),"forward",false)?)?,5,|b|serde_json::from_slice(b))??;
    assert_eq!(second["match_index"],1);let mut b=a;b["operation"]["style_filter"]=json!({"paragraph_details":{"checked":true}});
    let other=resolved!(&provider,&b)?;assert_ne!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);
    let called=Cell::new(false);assert!(other.with_next_verified_json(&provider,&wire(&next(&out,first["cursor"].clone(),"forward",false)?)?,5,|_|called.set(true)).is_err());
    assert!(!called.get());Ok(())
}
#[test]
fn paragraph_product_missing_paragraph_axis_rejects_absent_query_but_unrequested_character_is_optional()->TestResult {
    let raw=detail_fixture::package(&p(1,"K").replace("paraPrIDRef='1'",""))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let mut v=request(&s,&raw)?;v["operation"]["query"]=json!("ABSENT");v["operation"]["style_filter"]=json!({"paragraph_details":{"condense":17}});
    assert!(matches!(resolved!(&provider,&v),Err(PE::Stored(SE::Resolution(RE::Unresolved(_))))));
    let raw=detail_fixture::package(&p(1,"K").replace("charPrIDRef='1'","").replace("<hp:t>","<hp:t charStyleIDRef='0'>"))?;
    let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=request(&s,&raw)?;
    v["operation"]["style_filter"]=json!({"paragraph_details":{"condense":17}});assert_eq!(count(&data(&resolved!(&provider,&v)?,&provider)?)?,1);Ok(())
}
#[test]
fn paragraph_product_current_fallback_heading_branches_do_not_grant_native_route_or_change_source()->TestResult {
    let raw=detail_fixture::package(&p(1,"K"))?;let original=raw.clone();let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for(fallback,total)in[(1500,1),(120,0)] {
        let mut v=request(&s,&raw)?;v["operation"]["style_filter"]=json!({"paragraph_details":{
            "current_layout":{"left":{"value":120,"unit":"hwp_unit"}},"fallback_layout":{"left":{"value":fallback,"unit":"hwp_unit"}},
            "heading":{"kind":"meta_tag","current":{"heading_type":"outline","id_ref":0,"level":4},"fallback":{"heading_type":"none","id_ref":0,"level":0}}}});
        let out=resolved!(&provider,&v)?;let found=data(&out,&provider)?;assert_eq!(count(&found)?,total);
        assert_eq!(found["native_cascade_visibility_or_execution_authority"],false);
        assert!(matches!(out.require_current_product_route(&provider,5),Err(PE::RouteUnqualified)));
    }assert_eq!(raw,original);Ok(())
}
