use domain_ir::{ReferenceAuxiliaryLimits,ReferenceAuxiliaryLimitConfig};
use hwpx_package::document_import::fields::{ImportedDocumentFields,semantics::{ImportedDocumentFieldSemantics,ImportedFieldMeaning,
    source_index::SourceFieldMeaningIndex}};
#[path="support/document_import_field_fixture.rs"]mod fixture;
#[path="document_import_field_semantics.rs"]mod legacy_meanings;
type Result<T=()>=std::result::Result<T,Box<dyn std::error::Error>>;
fn limits()->Result<ReferenceAuxiliaryLimits>{Ok(ReferenceAuxiliaryLimits::new(Default::default())?)}
fn source()->Result<Vec<u8>>{fixture::package("<hp:p id='1'><hp:run><hp:ctrl><hp:fieldBegin id='1' type='DATE'/></hp:ctrl><hp:t>PRIVATE</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='1'/></hp:ctrl></hp:run></hp:p>")}
#[test]
fn captured_https_index_equals_legacy_meanings_without_additional_graph_clone()->Result{
    let bytes=fixture::captured()?;let forms=fixture::forms(&bytes,"meaning-index")?;let fields=ImportedDocumentFields::import(&forms)?;
    let before=fields.graph().clone();let index=SourceFieldMeaningIndex::import(&fields,limits()?)?;
    let legacy=ImportedDocumentFieldSemantics::import(&fields)?;
    assert_eq!(index.observations(),legacy.observations());assert_eq!(index.receipt().https_targets,1);
    assert_eq!(index.receipt().additional_document_graph_clones,0);assert!(!index.receipt().complete_reference_state_or_external_approval);
    assert_eq!(fields.graph(),&before);assert!(index.meaning_sha256(0).is_ok());assert!(index.meaning_sha256(1).is_err());
    let fresh=forms.reconstruct_source_for_verification(&bytes)?;assert_eq!(index.verify_reconstruction(&fresh)?,*index.receipt());Ok(())
}
#[test]
fn unknown_meaning_and_empty_source_are_explicit_and_original_bound()->Result{
    for bytes in [source()?,fixture::package("<hp:p id='1'><hp:run><hp:t>plain</hp:t></hp:run></hp:p>")?]{
        let forms=fixture::forms(&bytes,"meaning-index")?;let fields=ImportedDocumentFields::import(&forms)?;
        let index=SourceFieldMeaningIndex::import(&fields,limits()?)?;
        assert_eq!(index.observations().len(),fields.fields().len());
        if let Some(item)=index.observations().first(){assert!(matches!(item.meaning,ImportedFieldMeaning::Unsupported{..}));}
        let foreign=fixture::forms(&bytes,"meaning-index")?;let fresh=foreign.reconstruct_source_for_verification(&bytes)?;
        assert!(index.verify_reconstruction(&fresh).is_err());assert!(!format!("{index:?}").contains("PRIVATE"));
    }Ok(())
}
#[test]
fn source_meaning_output_budget_and_item_limits_never_return_truncated_inventory()->Result{
    let bytes=fixture::captured()?;let forms=fixture::forms(&bytes,"meaning-index")?;let fields=ImportedDocumentFields::import(&forms)?;
    let small=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig{input_bytes:1,output_bytes:1,..Default::default()})?;
    assert!(SourceFieldMeaningIndex::import(&fields,small).is_err());
    let short=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig{text_bytes:1,..Default::default()})?;
    assert!(SourceFieldMeaningIndex::import(&fields,short).is_err());Ok(())
}
