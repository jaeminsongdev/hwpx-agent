//! Source-derived result semantics, not cached text as its own oracle or Native execution.
#![allow(dead_code)]
use domain_ir::{DocumentId,ReferenceAuxiliaryLimits};
use hwpx_agent_cli::reference_validation_product::{ReferenceValidationProductOperation as Product,
    source_bookmark_results727::{BookmarkResultSelection,BookmarkResultError as E,BookmarkResultStatus as S,
        BookmarkResultAssessment,PreparedBookmarkResultExpectation}};
use hwpx_package::{cross_reference_sdk::SdkCrossReferenceDisplay as D,
    document_import::{ImportedSourcePackage,SourceImportLimits,forms::ImportedDocumentForms}};
use serde_json::{Value,json};
use sha2::{Digest as _,Sha256};
use std::{error::Error,path::{Path,PathBuf},io::Read};
#[path="../../hwpx-package/tests/support/block_bookmark679_fixture.rs"]mod native;
type Result<T=()> = std::result::Result<T,Box<dyn Error>>;
const INPUT:&str=include_str!("../../../implementation/p09/evidence/p09-361-block-bookmark693-product-inputs.v1.json");
fn require(ok:bool)->Result{if ok{Ok(())}else{Err("P729_RESULT_SEMANTICS_CHECK_FAILED".into())}}
fn root()->Result<PathBuf>{Ok(PathBuf::from(env!("CARGO_MANIFEST_DIR")).parent().and_then(Path::parent).ok_or("root")?.to_owned())}
fn read_pin(pin:&Value)->Result<Vec<u8>>{
    let name=pin["path"].as_str().ok_or("path")?;
    require(name.starts_with("implementation/p09/evidence/")&&!name.contains(['\\',':'])
        &&!name.split('/').any(|v|v.is_empty()||matches!(v,"."|"..")))?;
    let path=root()?.join(name);for part in path.ancestors(){let m=part.symlink_metadata()?;require(!m.file_type().is_symlink())?;
        #[cfg(windows)]{use std::os::windows::fs::MetadataExt as _;require(m.file_attributes()&0x400==0)?;}}
    let size=pin["bytes"].as_u64().ok_or("size")?;require(size>0&&size<=4194304&&path.metadata()?.len()==size)?;
    let mut o=std::fs::OpenOptions::new();o.read(true);
    #[cfg(windows)]{use std::os::windows::fs::OpenOptionsExt as _;o.share_mode(1);}
    let mut f=o.open(path)?;let mut out=Vec::new();let mut chunk=[0u8;65536];loop{
        let n=f.read(&mut chunk)?;if n==0{break;}require(out.len().checked_add(n).is_some_and(|v|v<=size as usize))?;
        out.extend_from_slice(&chunk[..n]);std::thread::sleep(std::time::Duration::from_secs_f64(n as f64/2097152.));
    }
    require(out.len()==size as usize&&hex::encode(Sha256::digest(&out))==pin["sha256"])?;Ok(out)
}
fn doc()->Result<DocumentId>{Ok(DocumentId::parse("bookmark-result728")?)}
fn limits()->Result<ReferenceAuxiliaryLimits>{Ok(ReferenceAuxiliaryLimits::new(Default::default())?)}
fn selections(source:&[u8])->Result<Vec<BookmarkResultSelection>>{
    let package=ImportedSourcePackage::import(source,doc()?,Sha256::digest(source).into(),SourceImportLimits::default())?;
    let forms=ImportedDocumentForms::import(package)?;let(_,target)=native::select(&forms,source)?;
    Ok([D::Page,D::BookmarkName,D::Content,D::RelativePosition].into_iter().flat_map(|display|{
        let target=target.clone();[false,true].into_iter().map(move|hyperlink|BookmarkResultSelection{target_id:target.clone(),display,hyperlink})}).collect())
}
fn setup()->Result<(Value,Vec<u8>,Vec<PreparedBookmarkResultExpectation>)>{
    let input:Value=serde_json::from_str(INPUT)?;let source=read_pin(&input["source"])?;let choices=selections(&source)?;
    let prepared=Product::prepare_source_bookmark_result_expectations(&source,doc()?,Sha256::digest(&source).into(),SourceImportLimits::default(),limits()?,&choices)?;
    require(prepared.len()==8)?;Ok((input,source,prepared))
}
pub fn fixed_result_source728()->Result<(Value,Vec<u8>,Vec<PreparedBookmarkResultExpectation>)>{setup()}
pub fn read_result_pin728(pin:&Value)->Result<Vec<u8>>{read_pin(pin)}
fn assess(expected:&PreparedBookmarkResultExpectation,source:&[u8],actual:&[u8])->std::result::Result<BookmarkResultAssessment,E>{
    Product::assess_source_bookmark_result(expected,source,actual,DocumentId::parse("bookmark-result728").map_err(|_|E::Source)?,
        Sha256::digest(actual).into(),SourceImportLimits::default())
}
pub fn observation()->Result<Value>{
    let(input,source,expectations)=setup()?;let mut rows=Vec::new();let(mut matched,mut mismatched,mut flow)=(0,0,0);
    for(i,case)in input["cases"].as_array().ok_or("cases")?.iter().enumerate(){for stage in["candidate","initial","saved","reopened"]{
        let bytes=read_pin(&case["stages"][stage]["pin"])?;let receipt=assess(&expectations[i],&source,&bytes)?;
        let desired=if matches!(i/2,0|3){S::NeedsDocumentFlow}else if stage=="candidate"{S::SourceTextMismatch}else{S::SourceTextMatches};
        require(receipt.status==desired&&receipt.whole_source_bindings_checked&&receipt.source_target_text_signature_preserved
            &&!receipt.native_execution_or_layout_attested&&!receipt.publication_revision_or_complete_reference_authority)?;
        match receipt.status {S::SourceTextMatches=>matched+=1,S::SourceTextMismatch=>mismatched+=1,S::NeedsDocumentFlow=>flow+=1,_=>return Err("P729_UNEXPECTED_RESULT".into())}
        if matches!(i/2,1|2){let key=if i/2==1{"target_name_sha256"}else{"target_content_sha256"};
            require(receipt.expected_text_sha256.map(hex::encode).is_some_and(|v|v==input[key]))?;}
        require(receipt.observed_text_sha256.map(hex::encode).is_some_and(|v|v==case["stages"][stage]["display_sha256"]))?;
        rows.push(json!({"case_index":i+1,"stage":stage,"status":receipt.status,"source":case["stages"][stage]["pin"],
            "assessment_sha256":hex::encode(Sha256::digest(serde_json::to_vec(&receipt)?)),"source_target_preserved":true,
            "native_or_layout_authority":false}));
    }}
    require((matched,mismatched,flow)==(12,4,16)&&read_pin(&input["source"])?==source)?;
    Ok(json!({"state":"QUALIFIED729_SOURCE_DERIVED_NAME_CONTENT_NATIVE_CACHE12_CANDIDATE_MISMATCH4_FLOW_UNRESOLVED16",
        "observations":rows,"source_text_matches":matched,"candidate_text_mismatches":mismatched,"needs_document_flow":flow,
        "Native_started":false,"Native_producer_attested_by_this_API":false,"publication_or_revision_authority":false,"P09_complete":false}))
}
#[test]
fn source_name_and_content_oracles_match_native_saved_values_without_granting_authority()->Result{
    let(input,source,p)=setup()?;for i in[2,4]{let bytes=read_pin(&input["cases"][i]["stages"]["initial"]["pin"])?;
        let r=assess(&p[i],&source,&bytes)?;require(r.status==S::SourceTextMatches&&r.expected_text_sha256==r.observed_text_sha256
            &&!r.native_execution_or_layout_attested&&!r.publication_revision_or_complete_reference_authority)?;
        let text=serde_json::to_string(&r)?;require(!text.contains("B643_ALPHA")&&!text.contains("p09_block643_01"))?;
    }require(format!("{:?}",p[2]).contains("redacted"))
}
#[test]
fn placeholder_candidate_is_a_mismatch_not_a_computed_initial_result()->Result{
    let(input,source,p)=setup()?;for i in[2,4]{let bytes=read_pin(&input["cases"][i]["stages"]["candidate"]["pin"])?;
        require(assess(&p[i],&source,&bytes)?.status==S::SourceTextMismatch)?;}Ok(())
}
#[test]
fn page_and_relative_values_remain_unresolved_even_when_native_cache_is_nonempty()->Result{
    let(input,source,p)=setup()?;for i in[0,6]{let bytes=read_pin(&input["cases"][i]["stages"]["initial"]["pin"])?;
        let r=assess(&p[i],&source,&bytes)?;require(r.status==S::NeedsDocumentFlow&&r.expected_text_sha256.is_none()
            &&r.observed_utf8_bytes.is_some_and(|n|n>0)&&!r.native_execution_or_layout_attested)?;}Ok(())
}
#[test]
fn changed_original_is_rejected_before_using_retained_expectation()->Result{
    let(input,mut source,p)=setup()?;let bytes=read_pin(&input["cases"][2]["stages"]["initial"]["pin"])?;source[0]^=1;
    require(matches!(assess(&p[2],&source,&bytes),Err(E::Source)))
}
#[test]
fn incorrect_observed_package_digest_is_rejected()->Result{
    let(input,source,p)=setup()?;let bytes=read_pin(&input["cases"][2]["stages"]["initial"]["pin"])?;
    let mut sha:[u8;32]=Sha256::digest(&bytes).into();sha[0]^=1;
    require(matches!(Product::assess_source_bookmark_result(&p[2],&source,&bytes,doc()?,sha,SourceImportLimits::default()),Err(E::Source)))
}
#[test]
fn hyperlink_and_display_cannot_be_substituted_by_a_different_captured_command()->Result{
    let(input,source,p)=setup()?;for i in[3,4]{let bytes=read_pin(&input["cases"][i]["stages"]["initial"]["pin"])?;
        require(matches!(assess(&p[2],&source,&bytes),Err(E::Command)))?;}Ok(())
}
#[test]
fn changed_target_content_is_rejected_even_if_old_cached_result_still_matches()->Result{
    let(input,source,p)=setup()?;let bytes=read_pin(&input["cases"][4]["stages"]["initial"]["pin"])?;
    let changed=native::map_section(&bytes,|xml|{require(xml.matches("B643_ALPHA").count()==2)?;
        Ok(xml.replacen("B643_ALPHA","B643_DRIFT",1))})?;
    require(matches!(assess(&p[4],&source,&changed),Err(E::TargetDrift)))
}
#[test]
fn empty_duplicate_and_missing_target_selections_cannot_create_source_oracles()->Result{
    let(input,source,_)=setup()?;let choices=selections(&source)?;
    require(Product::prepare_source_bookmark_result_expectations(&source,doc()?,Sha256::digest(&source).into(),SourceImportLimits::default(),limits()?,&[]).is_err())?;
    require(Product::prepare_source_bookmark_result_expectations(&source,doc()?,Sha256::digest(&source).into(),SourceImportLimits::default(),limits()?,&[choices[0].clone(),choices[0].clone()]).is_err())?;
    // A nonexistent target cannot be promoted by selecting the Content display.
    let missing=BookmarkResultSelection{target_id:domain_ir::LogicalId::parse("missing-point-target")?,display:D::Content,hyperlink:false};
    require(Product::prepare_source_bookmark_result_expectations(&source,doc()?,Sha256::digest(&source).into(),SourceImportLimits::default(),limits()?,&[missing]).is_err())?;
    require(input["cases"].as_array().is_some_and(|v|v.len()==8))
}
