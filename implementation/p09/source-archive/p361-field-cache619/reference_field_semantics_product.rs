use domain_ir::{DocumentId,ReferenceAuxiliaryLimits,ReferenceAuxiliaryLimitConfig};
use hwpx_agent_cli::reference_validation_product::{ReferenceValidationProductOperation as Product,source::{ReferenceSourceError,ReferenceSourceStatus},
    source_field_semantics::ReferenceSourceMeaningKind};
use hwpx_package::document_import::{SourceImportLimits,fields::{ImportedDocumentFields,semantics::source_index::SourceFieldMeaningIndex}};
use sha2::{Digest as _,Sha256};
#[path="../../hwpx-package/tests/support/document_import_field_fixture.rs"]mod fixture;
#[path="reference_source_product.rs"]mod legacy_source;
type Result<T=()>=std::result::Result<T,Box<dyn std::error::Error>>;
fn limits()->Result<ReferenceAuxiliaryLimits>{Ok(ReferenceAuxiliaryLimits::new(Default::default())?)}
fn assess(bytes:&[u8],document:&str)->Result<hwpx_agent_cli::reference_validation_product::source_field_semantics::ReferenceSourceFieldMeaningAssessment>{
    Ok(Product::assess_package_field_semantics(bytes,DocumentId::parse(document)?,Sha256::digest(bytes).into(),SourceImportLimits::default(),limits()?)?)}
fn rewrite(bytes:&[u8],target:&str,change:impl FnOnce(String)->String)->Result<Vec<u8>>{
    use std::io::{Cursor,Read,Write};use zip::{ZipArchive,ZipWriter,write::SimpleFileOptions};
    let mut input=ZipArchive::new(Cursor::new(bytes))?;let mut output=ZipWriter::new(Cursor::new(Vec::new()));let mut change=Some(change);
    for i in 0..input.len(){let mut entry=input.by_index(i)?;let name=entry.name().to_owned();let mut data=Vec::new();entry.read_to_end(&mut data)?;
        if name==target{data=change.take().ok_or("duplicate target")?(String::from_utf8(data)?).into_bytes();}
        output.start_file(name,SimpleFileOptions::default().compression_method(entry.compression()))?;output.write_all(&data)?;}
    assert!(change.is_none());Ok(output.finish()?.into_inner())
}
#[test]
fn actual_captured_field_meanings_join_exact_source_without_uri_or_native_approval()->Result{
    let bytes=fixture::captured()?;let original=bytes.clone();let assessment=assess(&bytes,"meaning-product")?;
    let forms=fixture::forms(&bytes,"meaning-product")?;let fields=ImportedDocumentFields::import(&forms)?;
    let index=SourceFieldMeaningIndex::import(&fields,limits()?)?;assert_eq!(assessment.receipt(),index.receipt());
    assert_eq!(assessment.selections().len(),1);let selector=&assessment.selections()[0];
    assert_eq!(selector.reference_id,fields.fields()[0].reference_id);assert_eq!(selector.source_field_sha256,fields.fields()[0].begin_anchor.fingerprint_sha256);
    assert_eq!(selector.meaning_sha256,index.meaning_sha256(0)?);assert_eq!(selector.kind,ReferenceSourceMeaningKind::HttpsTarget);
    let output=assessment.canonical_json(limits()?)?;let value:serde_json::Value=serde_json::from_slice(&output)?;
    assert_eq!(value["status"],"incomplete");assert_eq!(value["reference_validation_or_external_approval"],false);
    for text in [String::from_utf8(output)?,format!("{assessment:?}")]{assert!(!text.contains("https:")&&!text.contains("<hp:")&&!text.contains("Command"));}
    assert_eq!(bytes,original);Ok(())
}
#[test]
fn selection_binds_document_package_and_meaning_and_main_v14_includes_it()->Result{
    let bytes=fixture::captured()?;let first=assess(&bytes,"meaning-product")?;let foreign=assess(&bytes,"other-document")?;
    assert_ne!(first.selections()[0].reference_id,foreign.selections()[0].reference_id);
    assert_eq!(first.selections()[0].source_field_sha256,foreign.selections()[0].source_field_sha256);
    let old=Product::assess_package_source(&bytes,DocumentId::parse("meaning-product")?,Sha256::digest(&bytes).into(),SourceImportLimits::default(),limits()?)?;
    assert_eq!(old.field_meanings(),&first);
    assert_eq!(old.status(),ReferenceSourceStatus::Incomplete);assert!(old.validation_report().is_none());
    let value:serde_json::Value=serde_json::from_slice(&old.canonical_json(limits()?)?)?;
    assert_eq!(value["schema_version"],"hwpx-agent.product.reference-source-assessment/v14");assert_eq!(value["unresolved"].as_array().ok_or("unresolved")?.len(),4);
    assert_eq!(Product::assess_package_field_semantics(&bytes,DocumentId::parse("meaning-product")?,[0;32],SourceImportLimits::default(),limits()?),Err(ReferenceSourceError::Binding));Ok(())
}
#[test]
fn output_exact_bound_unknown_meanings_and_field_coverage_are_not_success_defaults()->Result{
    let bytes=fixture::package("<hp:p id='1'><hp:run><hp:ctrl><hp:fieldBegin id='1' type='DATE'/></hp:ctrl><hp:t>PRIVATE</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='1'/></hp:ctrl></hp:run></hp:p>")?;
    let assessment=assess(&bytes,"meaning-product")?;assert_eq!(assessment.selections()[0].kind,ReferenceSourceMeaningKind::Unsupported);
    let n=assessment.canonical_json(limits()?)?.len();
    let exact=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig{input_bytes:n,output_bytes:n,..Default::default()})?;
    let short=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig{input_bytes:n-1,output_bytes:n-1,..Default::default()})?;
    assert_eq!(assessment.canonical_json(exact)?.len(),n);assert_eq!(assessment.canonical_json(short),Err(ReferenceSourceError::Output));Ok(())
}
#[test]
fn malformed_supported_https_never_becomes_unknown_or_a_successful_selection()->Result{
    let bytes=fixture::captured()?;let changed=rewrite(&bytes,"Contents/section0.xml",|xml|{assert!(xml.contains("https"));xml.replace("https","http")})?;
    assert!(matches!(Product::assess_package_field_semantics(&changed,DocumentId::parse("meaning-product")?,Sha256::digest(&changed).into(),SourceImportLimits::default(),limits()?),Err(ReferenceSourceError::FieldRanges)));
    Ok(())
}
#[test]
fn off_spine_field_pairs_and_reference_item_budget_are_rejected()->Result{
    let bytes=fixture::package("<hp:p id='1'><hp:run><hp:t>plain</hp:t></hp:run></hp:p>")?;
    for markers in ["<hp:fieldBegin id='901' type='DATE'/>","<hp:fieldEnd beginIDRef='901'/>","<hp:fieldBegin id='901' type='DATE'/><hp:fieldEnd beginIDRef='901'/>"]{
        let hidden=rewrite(&bytes,"Contents/header.xml",|_|format!("<header xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph'>{markers}</header>"))?;
        assert_eq!(Product::assess_package_field_semantics(&hidden,DocumentId::parse("meaning-product")?,Sha256::digest(&hidden).into(),SourceImportLimits::default(),limits()?),Err(ReferenceSourceError::Coverage));
    }
    let mut body=String::new();for id in 1..=2{body.push_str(&format!("<hp:p id='{id}'><hp:run><hp:ctrl><hp:fieldBegin id='{id}' type='DATE'/></hp:ctrl><hp:t>PRIVATE</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='{id}'/></hp:ctrl></hp:run></hp:p>"));}
    let bytes=fixture::package(&body)?;let bounded=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig{items_per_kind:1,..Default::default()})?;
    assert_eq!(Product::assess_package_field_semantics(&bytes,DocumentId::parse("meaning-product")?,Sha256::digest(&bytes).into(),SourceImportLimits::default(),bounded),Err(ReferenceSourceError::InputLimit));Ok(())
}
#[test]
fn actual_sixteen_table_sources_keep_formula_asts_and_unverified_caches()->Result{
    let root=std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
    let bytes=std::fs::read(root.join("implementation/p06/evidence/target/p06-table-aggregate.current-2020.attempt02.v2.json"))?;
    assert_eq!(hex::encode(Sha256::digest(&bytes)),"edc71d554e0975d511ffe6f0de1b140a30ca932d0bf2b9c7b70517c5e8674fc5");
    let manifest:serde_json::Value=serde_json::from_slice(&bytes)?;let mut count=0;
    for case in manifest["cases"].as_array().ok_or("cases")?{for kind in ["input","output"]{
        let item=&case[kind];let bytes=std::fs::read(root.join(item["path"].as_str().ok_or("path")?))?;
        assert_eq!(bytes.len()as u64,item["bytes"].as_u64().ok_or("bytes")?);assert_eq!(hex::encode(Sha256::digest(&bytes)),item["sha256"].as_str().ok_or("sha")?);
        let forms=fixture::forms(&bytes,"meaning-product")?;let fields=ImportedDocumentFields::import(&forms)?;let index=SourceFieldMeaningIndex::import(&fields,limits()?)?;
        let assessment=assess(&bytes,"meaning-product")?;assert_eq!(assessment.receipt(),index.receipt());assert_eq!(assessment.selections().len(),1);
        assert_eq!(assessment.selections()[0].kind,ReferenceSourceMeaningKind::TableFormulaAst);
        let hwpx_package::document_import::fields::semantics::ImportedFieldMeaning::TableFormula{formula,..}=&index.observations()[0].meaning else{return Err("formula required".into())};
        assert!(matches!(formula.cache(),domain_ir::FormulaCache::Unverified{..}));count+=1;
    }}assert_eq!(count,16);Ok(())
}
