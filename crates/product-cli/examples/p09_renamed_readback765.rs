//! Actual renamed Native files through existing product readers; no Native activation.
#[path="../tests/bookmark_results728.rs"]#[allow(dead_code,unused_imports)]mod pins;
use domain_ir::{DocumentId,DocumentGraph,DocumentGraphLimits,ReferenceAuxiliaryLimits};
use hwpx_agent_cli::reference_validation_product::{ReferenceValidationProductOperation as Product,
    source::ReferenceSourceStatus,
    source_bookmark_results727::{BookmarkResultSelection,BookmarkResultStatus as R,SinglePageObservation,SinglePageResultStatus as P},
    source_crossref::bookmark_navigation744::BookmarkNavigationStatus as N};
use hwpx_package::{cross_reference_sdk::SdkCrossReferenceDisplay as D,document_import::{ImportedSourcePackage,SourceImportLimits,
    forms::ImportedDocumentForms,fields::{ImportedDocumentFields,block_bookmarks::ImportedBlockBookmarks,
        semantics::{ImportedDocumentFieldSemantics,ImportedFieldMeaning,source_index::SourceFieldMeaningIndex}}}};
use serde_json::{Value,json};
use sha2::{Digest as _,Sha256};
use std::error::Error;
type Result<T=()>=std::result::Result<T,Box<dyn Error>>;
const INPUT:&str=include_str!("../../../implementation/p09/evidence/p09-361-renamed-bookmark764-inputs.v1.json");
fn require(ok:bool,code:&'static str)->Result{if ok{Ok(())}else{Err(code.into())}}
fn doc()->Result<DocumentId>{Ok(DocumentId::parse("renamed-readback765")?)}
fn limits()->Result<ReferenceAuxiliaryLimits>{Ok(ReferenceAuxiliaryLimits::new(Default::default())?)}
fn forms(b:&[u8])->Result<ImportedDocumentForms>{Ok(ImportedDocumentForms::import(ImportedSourcePackage::import(b,doc()?,Sha256::digest(b).into(),SourceImportLimits::default())?)?)}
fn display(v:&Value)->Result<D>{Ok(match v.as_str().ok_or("P765_DISPLAY_TYPE")?{
    "page"=>D::Page,"bookmark_name"=>D::BookmarkName,"content"=>D::Content,"relative_position"=>D::RelativePosition,_=>return Err("P765_DISPLAY_REJECTED".into())})}

fn observation()->Result<Value>{
    let input:Value=serde_json::from_str(INPUT)?;let cases=input["cases"].as_array().ok_or("P765_CASES")?;
    require(cases.len()==8&&input["snapshots"].as_array().is_some_and(|v|v.len()==24),"P765_COMPLETE_INPUTS")?;
    let mut rows=Vec::new();let(mut source_matches,mut stale_candidate_names,mut flow,mut page_matches,mut navigation_on,mut navigation_off)=(0,0,0,0,0,0);
    // Keep completed file observations even if a later, independent file fails.
    let assessed:Result<()>=(||{
    for(index,case)in cases.iter().enumerate(){
        require(case["case_index"]==index+1,"P765_ORDINAL")?;
        let candidate=pins::read_result_pin728(&case["stages"]["candidate"]["pin"])?;
        let original=forms(&candidate)?;let original_fields=ImportedDocumentFields::import(&original)?;
        let original_blocks=ImportedBlockBookmarks::import(&original_fields,limits()?)?;
        let target=original_blocks.by_exact_source_name("p09_renamed737")?.field_reference_id().clone();
        let choices=[BookmarkResultSelection{target_id:target,display:display(&case["display"])?,hyperlink:case["hyperlink"].as_bool().ok_or("P765_LINK")?}];
        let expectations=Product::prepare_source_bookmark_result_expectations(&candidate,doc()?,Sha256::digest(&candidate).into(),SourceImportLimits::default(),limits()?,&choices)?;
        require(expectations.len()==1,"P765_ONE_ORACLE")?;
        for stage in["candidate","initial","saved","reopened"]{
            let pin=&case["stages"][stage]["pin"];let bytes=if stage=="candidate"{candidate.clone()}else{pins::read_result_pin728(pin)?};
            let f=forms(&bytes)?;let fields=ImportedDocumentFields::import(&f)?;let blocks=ImportedBlockBookmarks::import(&fields,limits()?)?;
            let target=blocks.by_exact_source_name("p09_renamed737")?;
            let meanings=SourceFieldMeaningIndex::import(&fields,limits()?)?;let graph=ImportedDocumentFieldSemantics::import(&fields)?;
            require(blocks.observations().len()==8&&meanings.receipt().block_bookmarks==8&&meanings.receipt().unsupported_meanings==0
                &&meanings.receipt().bookmark_crossrefs==1&&graph.receipt().bound_bookmark_edges==1&&meanings.observations()==graph.observations(),"P765_COMMON_MEANINGS")?;
            for item in meanings.observations(){if let ImportedFieldMeaning::BookmarkCrossReference{command}=&item.meaning{
                require(hex::encode(command.exact_target_name_sha256)==input["target_name_sha256"]
                    &&hex::encode(command.command_sha256)==case["stages"][stage]["command_sha256"],"P765_EXACT_RENAMED_COMMAND")?;
            }}
            let api=Product::assess_package_field_semantics(&bytes,doc()?,Sha256::digest(&bytes).into(),SourceImportLimits::default(),limits()?)?;
            require(api.receipt()==meanings.receipt(),"P765_INDEPENDENT_API")?;
            let raw=graph.graph().canonical_json()?;require(DocumentGraph::from_json(&raw,DocumentGraphLimits::default())?==*graph.graph()
                &&graph.verify_source(&bytes)?==*graph.receipt(),"P765_GRAPH_ROUNDTRIP")?;
            let proof=f.reconstruct_source_for_verification(&bytes)?;require(meanings.verify_reconstruction(&proof)?==*meanings.receipt(),"P765_WHOLE_SOURCE")?;
            let result=Product::assess_source_bookmark_result(&expectations[0],&candidate,&bytes,doc()?,Sha256::digest(&bytes).into(),SourceImportLimits::default())?;
            require(result.whole_source_bindings_checked&&result.source_target_text_signature_preserved&&!result.native_execution_or_layout_attested
                &&!result.publication_revision_or_complete_reference_authority&&hex::encode(result.target_name_sha256)==input["target_name_sha256"]
                &&result.observed_text_sha256.map(hex::encode).is_some_and(|v|v==case["stages"][stage]["display_sha256"]),"P765_ORACLE_SCOPE")?;
            let mut conditional=None;
            match index/2{
                1|2=>{let stale=stage=="candidate"&&index/2==1;
                    require(result.status==if stale{R::SourceTextMismatch}else{R::SourceTextMatches},"P765_NAME_CONTENT_VALUE")?;
                    if stale{stale_candidate_names+=1;}else{source_matches+=1;}
                    require(result.expected_text_sha256.map(hex::encode).is_some_and(|v|v==input[if index/2==1{"target_name_sha256"}else{"target_content_sha256"}]),"P765_SOURCE_ORACLE_HASH")?;
                }
                0|3=>{require(result.status==R::NeedsDocumentFlow,"P765_FLOW_NOT_SOURCE_TEXT")?;flow+=1;
                    if stage!="candidate"{
                        let matching=input["snapshots"].as_array().ok_or("P765_SNAPSHOTS")?.iter().filter(|v|v["case_index"]==index+1&&v["stage"]==stage).collect::<Vec<_>>();
                        require(matching.len()==1,"P765_ONE_EXACT_PAGE_PRODUCER")?;let captured=matching[0];
                        require(captured["snapshot"]==*pin&&captured["page_count"]==1&&captured["page_indices"]==json!([0])
                            &&captured["previously_closed_native_producer_bound"]==true,"P765_EXTENT_SOURCE_IDENTITY")?;
                        let observation=SinglePageObservation::from_unattested_metadata(Sha256::digest(&bytes).into(),1,&[0])?;
                        let page=Product::assess_source_bookmark_single_page(&expectations[0],&candidate,&bytes,doc()?,Sha256::digest(&bytes).into(),SourceImportLimits::default(),&observation)?;
                        require(page.status==P::MatchesUnderObservation&&!page.native_extent_or_locale_attested_by_api
                            &&!page.general_document_flow_qualified&&!page.execution_publication_or_revision_authority,"P765_CONDITIONAL_PAGE_VALUE")?;
                        if index/2==3{require(page.target_line_y.zip(page.reference_line_y).is_some_and(|(a,b)|a<b),"P765_ABOVE_DIRECTION")?;}
                        conditional=Some(page.status);page_matches+=1;
                    }
                }
                _=>return Err("P765_PROFILE".into()),
            }
            let ids=fields.fields().iter().filter(|v|v.native_kind=="CROSSREF").map(|v|v.reference_id.clone()).collect::<Vec<_>>();
            let navigation=Product::prepare_source_bookmark_navigation(&bytes,doc()?,Sha256::digest(&bytes).into(),SourceImportLimits::default(),limits()?,&ids)?;
            let enabled=case["hyperlink"].as_bool().ok_or("P765_LINK")?;
            let status=navigation.with_current_results(&bytes,|r|->Result<N>{
                require(r.len()==1&&!r[0].receipt().cached_display_used_for_destination&&!r[0].receipt().native_cursor_or_execution_authority,"P765_NAVIGATION_SCOPE")?;
                if enabled{let destination=r[0].destination().ok_or("P765_DESTINATION")?;
                    require(r[0].receipt().status==N::SourceDestinationResolved&&destination.start()==target.begin_anchor()
                        &&destination.end()==Some(target.end_anchor()),"P765_EXACT_BEGIN_END")?;
                }else{require(r[0].receipt().status==N::HyperlinkDisabled&&r[0].destination().is_none(),"P765_DISABLED_DESTINATION")?;}
                Ok(r[0].receipt().status)
            })??;
            if enabled{navigation_on+=1;}else{navigation_off+=1;}
            let main=Product::assess_package_source(&bytes,doc()?,Sha256::digest(&bytes).into(),SourceImportLimits::default(),limits()?)?;
            require(main.validation_report().is_none()&&main.status()==ReferenceSourceStatus::Incomplete,"P765_MAIN_REMAINS_INCOMPLETE")?;
            require(pins::read_result_pin728(pin)?==bytes,"P765_SOURCE_UNCHANGED")?;
            rows.push(json!({"case_index":index+1,"stage":stage,"source":pin,"source_result":result.status,"conditional_page":conditional,
                "navigation":status,"assessment_sha256":hex::encode(Sha256::digest(serde_json::to_vec(&result)?)),"source_unchanged":true}));
        }
        require(pins::read_result_pin728(&case["stages"]["candidate"]["pin"])?==candidate,"P765_ORIGINAL_UNCHANGED")?;
    }
    require((rows.len(),source_matches,stale_candidate_names,flow,page_matches,navigation_on,navigation_off)==(32,14,2,16,12,16,16),"P765_WHOLE_MATRIX_COUNTS")?;Ok(())
    })();
    let passed=assessed.is_ok();let error_code=assessed.err().map(|error|{let code=error.to_string();
        if code.starts_with("P765_")&&code.bytes().all(|b|b.is_ascii_uppercase()||b.is_ascii_digit()||b==b'_'){code}else{"P765_READBACK_FAILED_NO_RAW_VALUES".to_owned()}});
    Ok(json!({"state":if passed{"QUALIFIED765_RENAMED_NATIVE24_CANDIDATE8_CURRENT_PRODUCT_MEANINGS_RESULTS_NAVIGATION_NOT_NATIVE_CURSOR_OR_P09"}else{"FAILED765_PARTIAL_OBSERVATIONS_NOT_WHOLE_ACCEPTANCE"},
        "all_conditions_passed":passed,"error_code":error_code,
        "observations":rows,"source_text_matches":source_matches,"stale_candidate_names":stale_candidate_names,"needs_document_flow":flow,
        "producer_bound_conditional_single_page_matches":page_matches,"source_destinations":navigation_on,"hyperlink_disabled":navigation_off,
        "common_block_meanings_per_source":8,"unsupported_per_source":0,"main_status":"incomplete","Native_started":false,
        "Native_cursor_or_general_flow_qualified":false,"publication_or_revision_authority":false,"P09_complete":false}))
}
fn main(){
    if std::env::args().skip(1).collect::<Vec<_>>()!=["--actual-renamed-thirty-two-no-native"]{eprintln!("P765_MODE_REJECTED");std::process::exit(2);}
    match observation(){Ok(value)=>println!("{value}"),Err(error)=>{
        let code=error.to_string();if code.starts_with("P765_")&&code.bytes().all(|b|b.is_ascii_uppercase()||b.is_ascii_digit()||b==b'_'){eprintln!("{code}");}
        else{eprintln!("P765_READBACK_FAILED_NO_RAW_VALUES");}std::process::exit(2);
    }}
}
