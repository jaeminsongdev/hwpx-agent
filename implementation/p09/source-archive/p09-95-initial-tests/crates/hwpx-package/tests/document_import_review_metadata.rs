//! Original source reader/assembly on synthetic MEMO string-value metadata, NOT native meaning.
use domain_ir::{DocumentGraphLimits, DocumentId};
use hwpx_package::{
    BoundedZipReader, PackageLimits, PreservingXmlDocument, TextFlowLimits, TextFlowReader,
    document_import::{
        ImportedSourcePackage, SourceImportLimits,
        fields::{ImportedDocumentFields, semantics::{ImportedDocumentFieldSemantics, catalog::{ImportedDocumentCatalog, assembly::ImportedDocumentAssembly}}},
        forms::ImportedDocumentForms,
        structure::review::{ImportedDocumentReviewBodies, ReviewNativeMetadata},
    },
};
use sha2::{Digest as _, Sha256};
use std::{error::Error, io::Cursor};
#[path = "support/document_import_field_fixture.rs"]
mod fixture;
#[path = "support/document_import_review_assembly_fixture.rs"]
mod assembly_fixture;
type TestResult = Result<(), Box<dyn Error>>;
fn memo(payload: &str) -> String {
    format!("<hp:p id='1'><hp:run><hp:ctrl><hp:fieldBegin id='42' type='MEMO'>{payload}</hp:fieldBegin></hp:ctrl><hp:t>VISIBLE</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='42'/></hp:ctrl></hp:run></hp:p>")
}
fn body() -> &'static str {
    "<hp:subList><hp:p id='2'><hp:run><hp:t>PRIVATE-BODY</hp:t></hp:run></hp:p></hp:subList>"
}
fn meta() -> &'static str {
    "<hp:metaTag>{&quot;author&quot;:&quot;SYNTHETIC_PRIVATE_AUTHOR &amp; 한글&quot;,&quot;resolved&quot;:true}</hp:metaTag>"
}

#[test]
fn original_memo_reader_preserves_exact_meta_tag_in_all_closed_optional_payload_shapes() -> TestResult {
    for prefix in [String::new(), "<hp:parameters cnt='0'/>".into(), body().into(), format!("<hp:parameters cnt='0'/>{}", body())] {
        let bytes = fixture::package(&memo(&format!("{prefix}{}", meta())))?;
        let forms = fixture::forms(&bytes, "review-metadata")?;
        let review = ImportedDocumentReviewBodies::import(&forms)?;
        let observation = &review.observations()[0];
        let value = observation.meta_tag.as_ref().ok_or("metadata observation")?;
        assert_eq!(value.element_sha256, <[u8;32]>::from(Sha256::digest(meta().as_bytes())));
        assert_eq!(value.raw_bytes, meta().len());
        assert_eq!(forms.source().resolve_anchor(&value.source_anchor)?.element().ok_or("metadata element")?.name().local_name(), "metaTag");
        assert_eq!(observation.body.is_some(), prefix.contains("subList"));
        assert_eq!(observation.metadata, ReviewNativeMetadata::UnverifiedNativeMapping);
        assert!(!review.receipt().native_author_time_binding_verified);
        assert!(!review.receipt().native_visibility_resolution_binding_verified);
        assert_eq!(review.verify_source(&bytes)?, *review.receipt());
        let encoded = serde_json::to_string(observation)?;
        assert!(encoded.contains("meta_tag"));
        assert!(!encoded.contains("SYNTHETIC_PRIVATE_AUTHOR"));
        assert!(!format!("{observation:?} {value:?}").contains("SYNTHETIC_PRIVATE_AUTHOR"));
    }
    Ok(())
}
#[test]
fn empty_plain_entity_cdata_and_json_looking_text_remain_uninterpreted_exact_bytes() -> TestResult {
    for value in ["<hp:metaTag/>", "<hp:metaTag></hp:metaTag>", "<hp:metaTag>not JSON at all</hp:metaTag>", "<hp:metaTag>&lt;script&gt;&amp;never-executed&lt;/script&gt;</hp:metaTag>", "<hp:metaTag><![CDATA[{\"author\":\"SYNTHETIC\",\"time\":0}]]></hp:metaTag>"] {
        let bytes = fixture::package(&memo(value))?;
        let forms = fixture::forms(&bytes, "review-metadata")?;
        let review = ImportedDocumentReviewBodies::import(&forms)?;
        let observed = review.observations()[0].meta_tag.as_ref().ok_or("meta")?;
        assert_eq!(observed.element_sha256, <[u8;32]>::from(Sha256::digest(value.as_bytes())));
        assert_eq!(observed.raw_bytes, value.len());
        assert!(review.observations()[0].body.is_none());
        assert!(!review.receipt().native_author_time_binding_verified);
        assert!(!review.receipt().native_visibility_resolution_binding_verified);
    }
    Ok(())
}
#[test]
fn meta_tag_order_duplicate_namespace_attributes_and_nested_markup_reject_without_silently_losing_data() -> TestResult {
    for payload in [format!("{}{}", meta(), body()), format!("{}{}", meta(), meta()), format!("{}<hp:parameters cnt='0'/>", meta()),
        "<u:metaTag>foreign</u:metaTag>".into(), "<hp:metaTag extra='1'>data</hp:metaTag>".into(), "<hp:metaTag><hp:p/></hp:metaTag>".into(),
        "<hp:metaTag><hp:stringParam name='Author'>SYNTHETIC</hp:stringParam></hp:metaTag>".into()] {
        let bytes = fixture::package(&memo(&payload))?;
        if let Ok(forms) = fixture::forms(&bytes, "review-metadata") {assert!(ImportedDocumentReviewBodies::import(&forms).is_err());}
    }
    let hidden = format!("<hp:p id='1'><hp:run><hp:hiddenComment>{}{}</hp:hiddenComment></hp:run></hp:p>", body(), meta());
    let bytes = fixture::package(&hidden)?;
    if let Ok(forms) = fixture::forms(&bytes, "review-metadata") {assert!(ImportedDocumentReviewBodies::import(&forms).is_err());}
    Ok(())
}
#[test]
fn metadata_change_including_lexical_only_change_invalidates_whole_source_and_raw_observation() -> TestResult {
    let first = fixture::package(&memo(&format!("{}{}", body(), meta())))?;
    let forms = fixture::forms(&first, "review-metadata")?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    for altered in [meta().replace("resolved", "visibility"), meta().replace("&quot;", "&#34;")] {
        let next = fixture::package(&memo(&format!("{}{altered}", body())))?;
        assert!(review.verify_source(&next).is_err());
        let other = fixture::forms(&next, "review-metadata")?;
        let imported = ImportedDocumentReviewBodies::import(&other)?;
        assert_ne!(imported.observations()[0].meta_tag, review.observations()[0].meta_tag);
        assert_ne!(imported.receipt().body_observations_sha256, review.receipt().body_observations_sha256);
    }
    Ok(())
}
#[test]
fn no_meta_tag_keeps_legacy_serialized_observation_shape_and_existing_complete_body() -> TestResult {
    let bytes = fixture::package(&memo(body()))?;
    let forms = fixture::forms(&bytes, "review-metadata")?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    assert!(review.observations()[0].meta_tag.is_none());
    assert!(!serde_json::to_string(&review.observations()[0])?.contains("meta_tag"));
    assert_eq!(review.verify_source(&bytes)?, *review.receipt());
    Ok(())
}
#[test]
fn original_assembly_carries_exact_meta_sidecar_with_source_styles_and_does_not_promote_native_metadata() -> TestResult {
    let markers = assembly_fixture::markers("PRIVATE-BODY").replacen("</hp:fieldBegin>", &format!("{}</hp:fieldBegin>", meta()), 1);
    let bytes = assembly_fixture::package(&markers)?;
    let forms = ImportedDocumentForms::import(ImportedSourcePackage::import(&bytes, DocumentId::parse("review-metadata")?, Sha256::digest(&bytes).into(), SourceImportLimits::default())?)?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let catalog = ImportedDocumentCatalog::import(&meanings)?;
    let assembled = ImportedDocumentAssembly::import(&catalog)?;
    let direct = ImportedDocumentReviewBodies::import(&forms)?;
    assert_eq!(assembled.review_bodies().len(), direct.observations().len());
    for (complete, original) in assembled.review_bodies().iter().zip(direct.observations()) {assert_eq!(complete.source, *original);}
    assert_eq!(assembled.review_bodies()[0].source.meta_tag, direct.observations()[0].meta_tag);
    assert!(assembled.review_bodies()[0].catalog_body.is_some());
    assert!(!assembled.receipt().reviews.native_author_time_binding_verified);
    assert!(!assembled.receipt().reviews.native_visibility_resolution_binding_verified);
    assert_eq!(assembled.verify_source(&bytes)?, *assembled.receipt());
    assert_eq!(assembled.graph().validate(DocumentGraphLimits::default())?, ());
    Ok(())
}
#[test]
fn source_preserving_metadata_obeys_existing_text_budget_and_cannot_use_executable_lowering() -> TestResult {
    let paragraph = memo(&format!("<hp:metaTag>{}</hp:metaTag>", "X".repeat(4096)));
    let limits = TextFlowLimits::new(hwpx_package::TextFlowLimitConfig {text_bytes:512, ..Default::default()})?;
    assert!(TextFlowReader::read_source_preserving(paragraph.as_bytes(), limits).is_err());
    let bytes = fixture::package(&paragraph)?;
    let mut zip = BoundedZipReader::open(Cursor::new(&bytes), PackageLimits::default())?;
    let index = zip.entries().iter().find(|v|v.path.as_str()=="Contents/section0.xml").ok_or("section")?.index;
    let section = zip.read_entry(index)?;
    let xml = PreservingXmlDocument::parse(&section)?;
    let p = xml.elements().iter().position(|e|e.name().local_name()=="p").ok_or("paragraph")?;
    assert!(TextFlowReader::read_paragraph_element(&xml, p, limits).is_err());
    Ok(())
}
