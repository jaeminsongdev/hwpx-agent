//! Conditional source layout with externally producer-bound historical snapshots.
#![allow(dead_code)]
#[path="bookmark_results728.rs"]mod prior;
#[path="../../hwpx-package/tests/support/block_bookmark679_fixture.rs"]mod native;
use domain_ir::{DocumentId,ReferenceAuxiliaryLimits};
use hwpx_agent_cli::reference_validation_product::{ReferenceValidationProductOperation as Product,
    source_bookmark_results727::{PreparedBookmarkResultExpectation,BookmarkResultSelection,BookmarkResultError as E,
        BookmarkResultStatus,SinglePageObservation,SinglePageResultStatus as S,SinglePageResultAssessment}};
use hwpx_package::{cross_reference_sdk::SdkCrossReferenceDisplay as D,document_import::{ImportedSourcePackage,SourceImportLimits,forms::ImportedDocumentForms}};
use serde_json::{Value,json};
use sha2::{Digest as _,Sha256};
use std::{error::Error,io::{Cursor,Read as _},collections::BTreeMap};
type Result<T=()> = std::result::Result<T,Box<dyn Error>>;
const LAYOUT:&str=include_str!("../../../implementation/p09/evidence/p09-361-single-page732-inputs.v1.json");
fn require(ok:bool)->Result{if ok{Ok(())}else{Err("P734_SINGLE_PAGE_SCOPE_CHECK_FAILED".into())}}
fn doc()->Result<DocumentId>{Ok(DocumentId::parse("bookmark-result728")?)}
fn assess(p:&PreparedBookmarkResultExpectation,source:&[u8],actual:&[u8],observation:&SinglePageObservation)->std::result::Result<SinglePageResultAssessment,E>{
    Product::assess_source_bookmark_single_page(p,source,actual,DocumentId::parse("bookmark-result728").map_err(|_|E::Source)?,
        Sha256::digest(actual).into(),SourceImportLimits::default(),observation)
}
fn hint(bytes:&[u8])->Result<SinglePageObservation>{Ok(SinglePageObservation::from_unattested_metadata(Sha256::digest(bytes).into(),1,&[0])?)}
fn payload_parts(bytes:&[u8])->Result<BTreeMap<String,String>>{
    let mut zip=zip::ZipArchive::new(Cursor::new(bytes))?;require(zip.len()<=128)?;let mut out=BTreeMap::new();let mut total=0u64;
    for i in 0..zip.len(){let mut entry=zip.by_index(i)?;total=total.checked_add(entry.size()).ok_or("size")?;require(total<=8388608)?;
        let name=entry.name().to_owned();let mut b=Vec::new();entry.read_to_end(&mut b)?;
        require(out.insert(name,hex::encode(Sha256::digest(&b))).is_none())?;
    }Ok(out)
}
pub fn observation()->Result<Value>{
    let(input,source,prepared)=prior::fixed_result_source728()?;let layout:Value=serde_json::from_str(LAYOUT)?;
    let snapshots=layout["snapshots"].as_array().ok_or("snapshots")?;require(snapshots.len()==8)?;
    let mut rows=Vec::new();let(mut matched,mut missing)=(0,0);
    for index in[0,1,6,7]{let case=&input["cases"][index];for stage in["candidate","initial","saved","reopened"]{
        let pin=&case["stages"][stage]["pin"];let bytes=prior::read_result_pin728(pin)?;
        let captured=snapshots.iter().find(|v|v["case_index"]==index+1&&v["stage"]==stage);
        if let Some(captured)=captured{
            require(captured["snapshot"]==*pin&&captured["page_count"]==1&&captured["page_indices"]==json!([0])
                &&captured["previously_closed_native_producer_bound"]==true)?;
            let receipt=assess(&prepared[index],&source,&bytes,&hint(&bytes)?)?;
            require(receipt.status==S::MatchesUnderObservation&&receipt.base.status==BookmarkResultStatus::NeedsDocumentFlow
                &&!receipt.native_extent_or_locale_attested_by_api&&!receipt.general_document_flow_qualified
                &&!receipt.execution_publication_or_revision_authority)?;
            if index>=6{require(receipt.target_line_y.zip(receipt.reference_line_y).is_some_and(|(a,b)|a<b))?;}
            matched+=1;rows.push(json!({"case_index":index+1,"stage":stage,"source":pin,"status":receipt.status,
                "capture":captured,"assessment_sha256":hex::encode(Sha256::digest(serde_json::to_vec(&receipt)?)),
                "target_line_y":receipt.target_line_y,"reference_line_y":receipt.reference_line_y,"API_attests_native_or_general_flow":false}));
        }else{
            let receipt=Product::assess_source_bookmark_result(&prepared[index],&source,&bytes,doc()?,Sha256::digest(&bytes).into(),SourceImportLimits::default())?;
            require(receipt.status==BookmarkResultStatus::NeedsDocumentFlow&&matches!(stage,"candidate"|"saved"))?;
            let mut difference=Vec::new();if stage=="saved"{
                let initial=prior::read_result_pin728(&case["stages"]["initial"]["pin"])?;
                let a=payload_parts(&initial)?;let b=payload_parts(&bytes)?;
                require(a.keys().eq(b.keys()))?;difference=a.iter().filter(|(k,v)|b.get(*k)!=Some(*v)).map(|(k,_)|k.clone()).collect();
                require(difference==["Contents/content.hpf"])?;
            }
            missing+=1;rows.push(json!({"case_index":index+1,"stage":stage,"source":pin,"status":"missing_snapshot_extent_kept_unresolved",
                "different_payload_parts_from_initial":difference,"layout_transfer_not_admitted":true,"API_attests_native_or_general_flow":false}));
        }
    }}
    require((matched,missing)==(8,8))?;
    Ok(json!({"state":"QUALIFIED734_EXISTING_RENDER_BOUND_SINGLE_PAGE8_SAVED4_CANDIDATE4_UNRESOLVED_NOT_GENERAL_FLOW",
        "observations":rows,"conditional_snapshot_matches":matched,"saved_or_candidate_extent_missing":missing,
        "Native_started":false,"API_attests_native_or_general_flow":false,"publication_or_revision_authority":false,"P09_complete":false}))
}
#[test]
fn page_text_matches_independent_one_page_and_decimal_source_profile_conditionally()->Result{
    let(input,source,p)=prior::fixed_result_source728()?;for i in[0,1]{let b=prior::read_result_pin728(&input["cases"][i]["stages"]["initial"]["pin"])?;
        let r=assess(&p[i],&source,&b,&hint(&b)?)?;require(r.status==S::MatchesUnderObservation&&r.expected_text_sha256==Some(Sha256::digest(b"1").into())
            &&!r.native_extent_or_locale_attested_by_api&&!r.general_document_flow_qualified&&!r.execution_publication_or_revision_authority)?;}
    let b=prior::read_result_pin728(&input["cases"][0]["stages"]["initial"]["pin"])?;
    let changed=native::map_section(&b,|xml|{require(xml.matches("<hp:t>1</hp:t>").count()==1)?;Ok(xml.replacen("<hp:t>1</hp:t>","<hp:t>2</hp:t>",1))})?;
    require(assess(&p[0],&source,&changed,&hint(&changed)?)?.status==S::MismatchUnderObservation)
}
#[test]
fn relative_above_uses_separate_native_lineseg_coordinates_not_cached_text_as_oracle()->Result{
    let(input,source,p)=prior::fixed_result_source728()?;let b=prior::read_result_pin728(&input["cases"][6]["stages"]["reopened"]["pin"])?;
    let r=assess(&p[6],&source,&b,&hint(&b)?)?;require(r.status==S::MatchesUnderObservation&&r.target_line_y==Some(0)&&r.reference_line_y==Some(12800)
        &&r.expected_text_sha256==Some(Sha256::digest("위".as_bytes()).into())&&!r.native_extent_or_locale_attested_by_api)
}
#[test]
fn extent_cannot_be_reused_for_another_snapshot_digest()->Result{
    let(input,source,p)=prior::fixed_result_source728()?;let b=prior::read_result_pin728(&input["cases"][0]["stages"]["initial"]["pin"])?;
    let wrong=SinglePageObservation::from_unattested_metadata([9;32],1,&[0])?;require(matches!(assess(&p[0],&source,&b,&wrong),Err(E::Source)))
}
#[test]
fn incomplete_duplicate_or_multiple_page_inventories_are_rejected()->Result{
    for(count,pages)in[(0,vec![]),(1,vec![]),(1,vec![0,0]),(2,vec![0,1]),(1,vec![1])]{
        require(SinglePageObservation::from_unattested_metadata([7;32],count,&pages).is_err())?;
    }require(SinglePageObservation::from_unattested_metadata([0;32],1,&[0]).is_err())
}
#[test]
fn a_page_count_claim_cannot_qualify_candidate_without_native_line_positions()->Result{
    let(input,source,p)=prior::fixed_result_source728()?;let b=prior::read_result_pin728(&input["cases"][0]["stages"]["candidate"]["pin"])?;
    let r=assess(&p[0],&source,&b,&hint(&b)?)?;require(r.status==S::UnqualifiedLayout&&!r.native_extent_or_locale_attested_by_api)
}
#[test]
fn numbering_restart_and_overlapping_lines_do_not_inherit_old_matching_cache()->Result{
    let(input,source,p)=prior::fixed_result_source728()?;let b=prior::read_result_pin728(&input["cases"][0]["stages"]["initial"]["pin"])?;
    let changed=native::map_section(&b,|xml|{require(xml.matches("page=\"0\"").count()==1)?;Ok(xml.replacen("page=\"0\"","page=\"2\"",1))})?;
    require(assess(&p[0],&source,&changed,&hint(&changed)?)?.status==S::UnqualifiedLayout)?;
    let b=prior::read_result_pin728(&input["cases"][6]["stages"]["initial"]["pin"])?;
    let changed=native::map_section(&b,|xml|{require(xml.matches("vertpos=\"12800\"").count()==1)?;Ok(xml.replacen("vertpos=\"12800\"","vertpos=\"0\"",1))})?;
    require(assess(&p[6],&source,&changed,&hint(&changed)?)?.status==S::UnqualifiedLayout)
}
#[test]
fn below_direction_is_not_guessed_from_the_above_only_native_profile()->Result{
    let(input,source,p)=prior::fixed_result_source728()?;let b=prior::read_result_pin728(&input["cases"][6]["stages"]["initial"]["pin"])?;
    let changed=native::map_section(&b,|xml|{require(xml.matches("vertpos=\"0\"").count()==1)?;Ok(xml.replacen("vertpos=\"0\"","vertpos=\"14000\"",1))})?;
    let r=assess(&p[6],&source,&changed,&hint(&changed)?)?;require(r.status==S::UnqualifiedDirection&&r.expected_text_sha256.is_none()&&!r.general_document_flow_qualified)
}
#[test]
fn oversized_preparation_result_is_rejected_before_reserving_the_entire_batch()->Result{
    let(input,source,_)=prior::fixed_result_source728()?;
    let package=ImportedSourcePackage::import(&source,doc()?,Sha256::digest(&source).into(),SourceImportLimits::default())?;
    let forms=ImportedDocumentForms::import(package)?;let(_,target)=native::select(&forms,&source)?;
    let limits=ReferenceAuxiliaryLimits::new(Default::default())?;
    let count=limits.config().output_bytes/std::mem::size_of::<PreparedBookmarkResultExpectation>()+1;require(count<8192)?;
    let choices=vec![BookmarkResultSelection{target_id:target,display:D::Page,hyperlink:false};count];
    require(matches!(Product::prepare_source_bookmark_result_expectations(&source,doc()?,Sha256::digest(&source).into(),SourceImportLimits::default(),limits,&choices),Err(E::Limit)))?;
    require(input["cases"].as_array().is_some_and(|v|v.len()==8))
}
