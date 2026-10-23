use super::*;
#[allow(dead_code)] #[path="../../../../hwpx-package/tests/support/character_detail_fixture.rs"] mod detail_fixture;

#[test]
fn detail_product_all24_predicates_use_current_stored_source_and_strict_json()->TestResult {
    let raw=detail_fixture::package(&p(1,"K"))?;let original=raw.clone();let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for(positive,negative)in detail_fixture::predicates() {for(details,total)in[(positive,1),(negative,0)] {
        let mut v=request(&s,&raw)?;v["operation"]["style_filter"]=json!({"character_details":details});
        let out=resolved!(&provider,&v)?;out.verify(&provider,5)?;let found=data(&out,&provider)?;assert_eq!(count(&found)?,total);
        assert_eq!(found["native_cascade_visibility_or_execution_authority"],false);
        assert!(matches!(out.require_current_product_route(&provider,5),Err(PE::RouteUnqualified)));
    }}assert_eq!(raw,original);Ok(())
}
#[test]
fn detail_product_empty_unknown_duplicate_and_numeric_overflow_reject_before_source_reads()->TestResult {
    let raw=detail_fixture::package(&p(1,"K"))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let base=request(&s,&raw)?;
    let before=s.metadata.audit_events()?.len();
    for details in[json!({}),json!({"font_refs":{}}),json!({"bogus":true}),json!({"spacing":{"hangul":40000}}),
        json!({"font_refs":{"user":-1}}),json!({"shadow_type":"bad"}),json!({"shade_color":{"kind":"none","rgb":[0,0,0]}})] {
        let mut v=base.clone();v["operation"]["style_filter"]=json!({"character_details":details});assert!(matches!(resolved!(&provider,&v),Err(PE::Request)));
    }
    let mut v=base;v["operation"]["style_filter"]=json!({"character_details":{"emboss":true}});let text=serde_json::to_string(&v)?;
    let duplicate=text.replace("\"emboss\":true","\"emboss\":true,\"embo\\u0073s\":false");assert_ne!(text,duplicate);
    assert!(matches!(Resolved::prepare_json(&provider,duplicate.as_bytes(),Default::default(),4),Err(PE::Request)));
    assert_eq!(s.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn detail_product_all_four_scopes_and_combined_legacy_predicates_are_exact()->TestResult {
    let raw=detail_fixture::package(&body())?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut base=request(&s,&raw)?;
    base["operation"]["style_filter"]=json!({"bold":true,"alignment":"right","character_details":{"underline_position":"bottom","spacing":{"hangul":-4}}});
    let inv=inventory(&provider,&base)?;let range=window(&inv,"memo_body",7,8)?;let node=inv["inventory"]["nodes"].as_array().ok_or("nodes")?.iter()
        .find(|n|n["source_handle"]==range["start"]["paragraph_handle"]).ok_or("node")?;
    for(scope,total)in[("document",6),("section",6),("node_set",2),("selection",1)] {let mut v=base.clone();v["selector"]["scope"]=json!(scope);
        match scope {"section"=>v["selector"]["section_ids"]=inv["inventory"]["section_ids"].clone(),"node_set"=>v["selector"]["range"]=json!({"node_ids":[node["node_id"].clone()]}),"selection"=>v["selector"]["range"]=range.clone(),_=>{}}
        assert_eq!(count(&data(&resolved!(&provider,&v)?,&provider)?)?,total);
        v["operation"]["style_filter"]["bold"]=json!(false);assert_eq!(count(&data(&resolved!(&provider,&v)?,&provider)?)?,0);
    }Ok(())
}
#[test]
fn detail_product_retained_cursor_binds_predicate_not_just_the_same_matches()->TestResult {
    let raw=detail_fixture::package(&p(1,"K K"))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut a=request(&s,&raw)?;
    a["operation"]["style_filter"]=json!({"character_details":{"emboss":true}});let out=resolved!(&provider,&a)?;
    let first:Value=out.with_next_verified_json(&provider,&wire(&next(&out,Value::Null,"forward",false)?)?,5,|b|serde_json::from_slice(b))??;
    let second:Value=out.with_next_verified_json(&provider,&wire(&next(&out,first["cursor"].clone(),"forward",false)?)?,5,|b|serde_json::from_slice(b))??;
    assert_eq!(second["match_index"],1);let mut b=a;b["operation"]["style_filter"]=json!({"character_details":{"engrave":false}});let other=resolved!(&provider,&b)?;
    assert_ne!(out.receipt().canonical_request_sha256,other.receipt().canonical_request_sha256);let called=Cell::new(false);
    assert!(other.with_next_verified_json(&provider,&wire(&next(&out,first["cursor"].clone(),"forward",false)?)?,5,|_|called.set(true)).is_err());assert!(!called.get());Ok(())
}
#[test]
fn detail_product_missing_or_uninterpreted_direct_axis_still_rejects_without_matches()->TestResult {
    for body in[p(1,"K").replace("charPrIDRef='1'",""),p(1,"K").replace("<hp:t>","<hp:t charStyleIDRef='0'>")] {
        let raw=detail_fixture::package(&body)?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=request(&s,&raw)?;
        v["operation"]["query"]=json!("ABSENT");v["operation"]["style_filter"]=json!({"character_details":{"emboss":true}});
        assert!(matches!(resolved!(&provider,&v),Err(PE::Stored(SE::Resolution(RE::Unresolved(_))))));
    }Ok(())
}
