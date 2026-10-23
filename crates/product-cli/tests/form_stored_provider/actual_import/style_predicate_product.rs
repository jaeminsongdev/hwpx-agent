use super::*;
use hwpx_agent_cli::form_product_request::stored_source_search::selector::resolved_styles::StoredResolvedStyleProductRequest as Resolved;
fn resolved(s:&StoredFixture,raw:&[u8],emboss:bool)->Result<Value,Box<dyn Error>> {
    let mut value=envelope(s,raw)?;value["schema_version"]=json!("hwpx-agent.product-source-search-request/v9");
    value["operation"]=json!({"kind":"find_resolved_style","query":"K","regex":false,"case_sensitive":true,"whole_word":false,"max_results":100,
        "style_filter":{"character_details":{"emboss":emboss}},"review_policy":policy(true,true)});Ok(value)
}
#[test]
fn same_pair_new_predicates_never_reuse_prior_v3_v7_v9_product_acceptance()->TestResult {
    let raw=details::package(&(details::p(1,"K K")+&details::p(2,"K")))?;let original=raw.clone();let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    for(value,total)in[(true,3),(false,0),(true,3)] {
        let filter=json!({"character_source":"run_property","character_details":{"emboss":value}});
        assert_eq!(legacy_count(&legacy_data(&legacy(&provider,&definition(&s,&raw,filter.clone())?)?,&provider)?)?,total);
        assert_eq!(selector_count(&selector_data(&scoped(&provider,&selector(&s,&raw,filter)?)?,&provider)?)?,total);
        let out=Resolved::prepare_json(&provider,&wire(&resolved(&s,&raw,value)?)?,Default::default(),4)?;
        let found:Value=out.with_verified_json(&provider,5,|bytes|serde_json::from_slice(bytes))??;assert_eq!(selector_count(&found)?,total);
    }assert_eq!(raw,original);Ok(())
}
#[test]
fn retained_cached_search_still_rechecks_current_aead_and_never_discloses_after_tamper()->TestResult {
    let raw=details::package(&details::p(1,"K K"))?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
    let value=resolved(&s,&raw,true)?;let out=Resolved::prepare_json(&provider,&wire(&value)?,Default::default(),4)?;
    out.verify(&provider,5)?;s.blobs.tamper.store(true,Ordering::SeqCst);let called=Cell::new(false);
    assert!(out.with_verified_json(&provider,6,|_|called.set(true)).is_err());
    assert!(Resolved::prepare_json(&provider,&wire(&value)?,Default::default(),6).is_err());assert!(!called.get());Ok(())
}
