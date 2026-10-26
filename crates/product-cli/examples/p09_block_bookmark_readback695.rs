//! Read all fixed32 block candidates/Native files through actual product APIs.
//! No Native, mutation, input substitution or complete-meaning/P09 promotion.
use domain_ir::{DocumentId,DocumentGraph,DocumentGraphLimits,ReferenceAuxiliaryLimits};
use hwpx_agent_cli::reference_validation_product::{ReferenceValidationProductOperation as Product,
    source_field_semantics::ReferenceSourceMeaningKind};
use hwpx_package::document_import::{ImportedSourcePackage,SourceImportLimits,forms::ImportedDocumentForms,
    fields::{ImportedDocumentFields,block_bookmarks::ImportedBlockBookmarks,
        bookmark_crossref::{BookmarkCrossReferenceDisplay as Display,SourceBookmarkResolution},
        cached_source::FieldCacheSnapshot,semantics::ImportedDocumentFieldSemantics}};
use serde_json::{Value,json};
use sha2::{Digest as _,Sha256};
use std::{error::Error,fs::OpenOptions,io::Read,path::PathBuf,time::Duration};
type Result<T=()> = std::result::Result<T,Box<dyn Error>>;
static PHASE:std::sync::atomic::AtomicUsize=std::sync::atomic::AtomicUsize::new(0);
static CASE:std::sync::atomic::AtomicUsize=std::sync::atomic::AtomicUsize::new(0);
const INPUT:&str=include_str!("../../../implementation/p09/evidence/p09-361-block-bookmark693-product-inputs.v1.json");
fn require(ok: bool, code: &'static str) -> Result<()> {
    if !ok {
        return Err(code.into());
    }
    Ok(())
}
fn root() -> Result<PathBuf> {
    Ok(PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(std::path::Path::parent)
        .ok_or("P695_ROOT")?
        .to_owned())
}
fn read_pin(pin: &Value) -> Result<Vec<u8>> {
    let name = pin["path"].as_str().ok_or("P695_PATH")?;
    require(
        name.starts_with("implementation/p09/evidence/")
            && !name.contains('\\')
            && !name.contains(':')
            && !name
                .split('/')
                .any(|v| v.is_empty() || v == "." || v == ".."),
        "P695_PATH_SCOPE",
    )?;
    let path = root()?.join(name);
    for component in path.ancestors() {
        let meta = component.symlink_metadata()?;
        require(!meta.file_type().is_symlink(), "P695_LINK")?;
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt as _;
            require(meta.file_attributes() & 0x400 == 0, "P695_REPARSE")?;
        }
    }
    let expected = pin["bytes"].as_u64().ok_or("P695_SIZE")?;
    require(
        expected > 0
            && expected <= 4_194_304
            && path.metadata()?.is_file()
            && path.metadata()?.len() == expected,
        "P695_SIZE_LIMIT",
    )?;
    let mut options = OpenOptions::new();
    options.read(true);
    #[cfg(windows)]
    {
        use std::os::windows::fs::OpenOptionsExt as _;
        options.share_mode(1);
    }
    let mut file = options.open(path)?;
    let mut out = Vec::new();
    let mut chunk = [0_u8; 65_536];
    loop {
        let n = file.read(&mut chunk)?;
        if n == 0 {
            break;
        }
        require(
            out.len()
                .checked_add(n)
                .is_some_and(|v| v <= expected as usize),
            "P695_GROWTH",
        )?;
        out.extend_from_slice(&chunk[..n]);
        std::thread::sleep(Duration::from_secs_f64(n as f64 / 2_097_152.));
    }
    require(
        out.len() as u64 == expected && hex::encode(Sha256::digest(&out)) == pin["sha256"],
        "P695_SHA",
    )?;
    Ok(out)
}
fn block_snapshot(blocks:&ImportedBlockBookmarks)->Result<Value>{
    let mut rows=Vec::new();
    for b in blocks.observations(){
        let FieldCacheSnapshot::DecodedTextNotEvaluated{decoded_text_sha256,utf8_bytes,tabs,line_breaks,..}=b.selected_source()
            else{return Err("P695_STRUCTURED_BLOCK_CACHE".into())};
        rows.push(json!({"name_sha256":hex::encode(Sha256::digest(b.name().as_bytes())),
            "selected_sha256":hex::encode(decoded_text_sha256),"utf8_bytes":utf8_bytes,"tabs":tabs,"line_breaks":line_breaks}));
    }
    rows.sort_by_key(Value::to_string);Ok(json!(rows))
}
fn run()->Result<Value>{
    let input:Value=serde_json::from_str(INPUT)?;
    require(input["schema"]=="hwpx-agent.p09.block-capture-product-input693/v1"&&input["native_execution_authorized"]==false
        &&input["P09_complete"]==false,"P695_FIXED_INPUT_PROFILE")?;
    let document=DocumentId::parse("p09-block-product-readback695")?;
    let limits=ReferenceAuxiliaryLimits::new(Default::default())?;
    let source=read_pin(&input["source"])?;
    let package=ImportedSourcePackage::import(&source,document.clone(),Sha256::digest(&source).into(),SourceImportLimits::default())?;
    let forms=ImportedDocumentForms::import(package)?;let fields=ImportedDocumentFields::import(&forms)?;
    let blocks=ImportedBlockBookmarks::import(&fields,limits)?;require(blocks.observations().len()==8&&fields.fields().len()==8,"P695_ORIGINAL_EIGHT_BLOCKS")?;
    let original=block_snapshot(&blocks)?;
    let cases=input["cases"].as_array().ok_or("P695_CASES")?;require(cases.len()==8,"P695_WHOLE_EIGHT")?;
    let mut rows=Vec::new();
    for(index,case)in cases.iter().enumerate(){
        CASE.store(index+1,std::sync::atomic::Ordering::Relaxed);
        let display=[Display::Page,Display::BookmarkName,Display::Content,Display::RelativePosition][index/2];
        require(case["case_index"]==index+1&&case["hyperlink"]==(index%2==1)&&serde_json::to_value(display)?==case["display"],"P695_FIXED_CASE_MODE")?;
        for stage in["candidate","initial","saved","reopened"]{
            PHASE.store(1,std::sync::atomic::Ordering::Relaxed);
            let expected=&case["stages"][stage];let bytes=read_pin(&expected["pin"])?;let sha=Sha256::digest(&bytes).into();
            let bindings=Product::read_source_bookmark_crossrefs(&bytes,document.clone(),sha,SourceImportLimits::default(),limits)?;
            require(bindings.bindings().len()==1,"P695_ONE_PRODUCT_BINDING")?;let binding=&bindings.bindings()[0];
            require(binding.display==display&&binding.hyperlink==(index%2==1)
                &&hex::encode(binding.command_sha256)==expected["command_sha256"]
                &&hex::encode(binding.exact_target_name_sha256)==input["target_name_sha256"],"P695_EXACT_TYPED_COMMAND")?;
            let SourceBookmarkResolution::Bound{logical_target_id,..}=&binding.target else{return Err("P695_BLOCK_TARGET_NOT_BOUND".into())};
            PHASE.store(2,std::sync::atomic::Ordering::Relaxed);
            let package=ImportedSourcePackage::import(&bytes,document.clone(),sha,SourceImportLimits::default())?;
            let forms=ImportedDocumentForms::import(package)?;let fields=ImportedDocumentFields::import(&forms)?;
            let blocks=ImportedBlockBookmarks::import(&fields,limits)?;
            require(fields.fields().len()==9&&blocks.observations().len()==8&&block_snapshot(&blocks)?==original,"P695_ALL_ORIGINAL_BLOCKS_PRESERVED")?;
            let target=blocks.observations().iter().find(|b|b.field_reference_id()==logical_target_id).ok_or("P695_TARGET_SOURCE_ID")?;
            require(hex::encode(Sha256::digest(target.name().as_bytes()))==input["target_name_sha256"],"P695_EXACT_BLOCK_NAME")?;
            let field=fields.fields().iter().find(|f|&f.reference_id==logical_target_id&&f.native_kind=="BOOKMARK").ok_or("P695_EXACT_ADMITTED_BLOCK_FIELD")?;
            PHASE.store(3,std::sync::atomic::Ordering::Relaxed);
            let assessment=Product::assess_package_source(&bytes,document.clone(),sha,SourceImportLimits::default(),limits)?;
            require(assessment.field_range_receipt().field_ranges==9&&assessment.field_meanings().receipt().bookmark_crossrefs==1
                &&assessment.field_meanings().selections().len()==9,"P695_MAIN_SOURCE_MEANING_COVERAGE")?;
            let meaning=assessment.field_meanings().selections().iter().find(|v|v.reference_id==binding.field_reference_id).ok_or("P695_MAIN_MEANING")?;
            require(meaning.kind==ReferenceSourceMeaningKind::BookmarkCrossReference,"P695_MAIN_TYPED_MEANING")?;
            let caches=assessment.field_cached_source().observations();
            let FieldCacheSnapshot::DecodedTextNotEvaluated{decoded_text_sha256,..}=&caches.iter().find(|v|v.field_reference_id==binding.field_reference_id).ok_or("P695_CACHE_FIELD")?.cache
                else{return Err("P695_CACHE_UNQUALIFIED".into())};
            require(hex::encode(decoded_text_sha256)==expected["display_sha256"],"P695_INDEPENDENT_XML_CACHE_PARITY")?;
            PHASE.store(4,std::sync::atomic::Ordering::Relaxed);
            let semantics=ImportedDocumentFieldSemantics::import(&fields)?;
            require(semantics.receipt().bookmark_crossrefs==1&&semantics.receipt().bound_bookmark_edges==1
                &&semantics.receipt().unsupported_meanings==8,"P695_BLOCKS_REMAIN_EXPLICIT_PARTIAL_MEANINGS")?;
            let graph=semantics.graph().canonical_json()?;let value:Value=serde_json::from_slice(&graph)?;
            let id=serde_json::to_value(&binding.field_reference_id)?;let node=serde_json::to_value(&field.begin_node_id)?;
            require(value["references"].as_array().ok_or("P695_REFERENCES")?.iter().filter(|v|v["reference_id"]==id&&v["target_node_id"]==node).count()==1,"P695_EXACT_SOURCE_BLOCK_BEGIN_EDGE")?;
            require(DocumentGraph::from_json(&graph,DocumentGraphLimits::default())?==*semantics.graph()
                &&semantics.verify_source(&bytes)?==*semantics.receipt(),"P695_GRAPH_REOPEN_AND_WHOLE_SOURCE_RECONSTRUCTION")?;
            require(read_pin(&expected["pin"])?==bytes,"P695_FINAL_CURRENT_FILE")?;
            rows.push(json!({"case_index":index+1,"stage":stage,"source":expected["pin"],
                "product_command_and_block_target_bound":true,"main_source_typed_meaning":true,
                "XML_cached_display_parity":true,"exact_block_begin_graph_edge":true,
                "original_eight_block_snapshots_preserved":true,"graph_serialization_reopened":true,
                "whole_source_reconstruction":true,"unsupported_block_meanings_preserved":8}));
        }
    }
    require(read_pin(&input["source"])?==source,"P695_FINAL_ORIGINAL_SOURCE")?;
    Ok(json!({"state":"QUALIFIED695_PRODUCT32_BLOCK_TARGET_CACHE_MAIN_MEANING_AND_GRAPH_NOT_FULL_F11",
        "observations":rows,"Native_started":false,"previous_Native_or_pass_tests_replayed":false,
        "render_or_navigation_qualified":false,"full_F11_or_P09_qualified":false}))
}
fn main(){
    let result=(||->Result{
        require(std::env::args().skip(1).collect::<Vec<_>>()==["--fixed32-readonly-no-native"],"P695_CLOSED_MODE")?;
        let raw=serde_json::to_vec(&run()?)?;require(raw.len()<=32768,"P695_BOUNDED_OUTPUT")?;
        println!("{}",std::str::from_utf8(&raw)?);Ok(())
    })();
    if let Err(error)=result{
        let text=error.to_string();
        if text.starts_with("P695_")&&text.len()<90&&text.bytes().all(|c|c.is_ascii_uppercase()||c.is_ascii_digit()||c==b'_'){eprintln!("{text}");}
        else if let Some(kind)=error.downcast_ref::<hwpx_agent_cli::reference_validation_product::source::ReferenceSourceError>(){
            eprintln!("P695_MAIN_{kind}");
        }else{eprintln!("P695_REJECTED_PHASE_{}_CASE_{}",PHASE.load(std::sync::atomic::Ordering::Relaxed),CASE.load(std::sync::atomic::Ordering::Relaxed));}
        std::process::exit(2);
    }
}
