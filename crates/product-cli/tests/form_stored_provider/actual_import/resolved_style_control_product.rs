//! The contextual ambiguity must propagate through stored v9 without corrupting other scopes.
use super::*;
fn hidden()->String {body().replace("<hp:ctrl><hp:hiddenComment>","<hp:ctrl charStyleIDRef='1'><hp:hiddenComment>")}
#[test]
fn control_product_hidden_context_is_unresolved_and_memo_keeps_exact_original_admission_rejection()->TestResult {
    for (body,is_memo) in[(hidden(),false),(body().replace("<hp:ctrl><hp:fieldBegin","<hp:ctrl charStyleIDRef='0'><hp:fieldBegin"),true)] {
        let raw=definition::package(&body)?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);
        for query in["K","ABSENT"] {let mut v=request(&s,&raw)?;v["operation"]["query"]=json!(query);
            if is_memo {
                assert!(matches!(resolved!(&provider,&v),Err(PE::Import(hwpx_agent_cli::form_stored_provider::actual_import::StoredActualFormImportError::Import(
                    hwpx_package::document_import::forms::FormImportError::Body(_))))));
            }else{assert!(matches!(resolved!(&provider,&v),Err(PE::Stored(SE::Resolution(RE::Unresolved(_))))));}
        }
    }Ok(())
}
#[test]
fn control_product_exclusion_preserves_qualified_source_result_and_next_boundary()->TestResult {
    let raw=definition::package(&hidden())?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=request(&s,&raw)?;
    v["operation"]["review_policy"]=policy(false,false);let out=resolved!(&provider,&v)?;assert_eq!(count(&data(&out,&provider)?)?,2);
    let first:Value=out.with_next_verified_json(&provider,&wire(&next(&out,Value::Null,"forward",false)?)?,5,|b|serde_json::from_slice(b))??;assert_eq!(first["match_index"],0);out.verify(&provider,5)?;Ok(())
}
#[test]
fn control_product_unrequested_character_axis_reports_uncertainty_but_admits_paragraph_predicate()->TestResult {
    let raw=definition::package(&hidden())?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=request(&s,&raw)?;
    v["operation"]["style_filter"]=json!({"alignment":"right"});let found=data(&resolved!(&provider,&v)?,&provider)?;assert_eq!(count(&found)?,6);
    assert_eq!(found["coverage"]["unresolved_text_style_segments"],1);assert_eq!(found["coverage"]["requested_character_axis_complete"],true);Ok(())
}
#[test]
fn control_product_selected_sibling_window_and_empty_hidden_window_do_not_leak_context()->TestResult {
    let raw=definition::package(&hidden())?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=request(&s,&raw)?;let inv=inventory(&provider,&v)?;
    for(region,a,b,total)in[("body_and_notes",0,8,2),("hidden_explanation",0,0,0)] {v["selector"]["scope"]=json!("selection");v["selector"]["range"]=window(&inv,region,a,b)?;
        let found=data(&resolved!(&provider,&v)?,&provider)?;assert_eq!(count(&found)?,total);assert_eq!(found["coverage"]["unresolved_text_style_segments"],0);
    }Ok(())
}
#[test]
fn control_product_foreign_style_attribute_does_not_gain_native_meaning()->TestResult {
    let body=body().replace("<hp:ctrl><hp:hiddenComment>","<hp:ctrl xmlns:x='urn:foreign-style' x:charStyleIDRef='1'><hp:hiddenComment>");
    let raw=definition::package(&body)?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let out=resolved!(&provider,&request(&s,&raw)?)?;
    assert_eq!(count(&data(&out,&provider)?)?,6);Ok(())
}
#[test]
fn control_product_legacy_explicit_definition_search_keeps_its_separate_non_cascade_contract()->TestResult {
    use hwpx_agent_cli::form_product_request::stored_source_search::selector::styles::StoredSelectorStyleProductRequest as V7;
    let raw=definition::package(&hidden())?;let s=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(s,actor,provider);let mut v=request(&s,&raw)?;
    assert!(matches!(resolved!(&provider,&v),Err(PE::Stored(SE::Resolution(RE::Unresolved(_))))));v["schema_version"]=json!("hwpx-agent.product-source-search-request/v7");
    v["operation"]["kind"]=json!("find_style");v["operation"]["style_filter"]=json!({"kind":"declared","filter":{"run_character_property":1}});
    let out=V7::prepare_json(&provider,&wire(&v)?,Default::default(),4)?;let found:Value=out.with_verified_json(&provider,5,|b|serde_json::from_slice(b))??;
    assert_eq!(count(&found)?,6);assert_eq!(found["effective_style_visibility_or_execution_authority"],false);Ok(())
}
