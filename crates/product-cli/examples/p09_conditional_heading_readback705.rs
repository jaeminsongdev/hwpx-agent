//! Fixed32 main Source assessment; conditional alternatives remain explicitly unresolved.
use domain_ir::{DocumentId,ReferenceAuxiliaryLimits};
use hwpx_agent_cli::reference_validation_product::{ReferenceValidationProductOperation as Product,source::ReferenceSourceStatus};
use hwpx_package::document_import::{SourceImportLimits,fields::cached_source::FieldCacheSnapshot};
use serde_json::{Value,json};
use sha2::{Digest as _,Sha256};
use std::{error::Error,fs::OpenOptions,io::Read,path::PathBuf,time::Duration};
type Result<T=()> = std::result::Result<T,Box<dyn Error>>;
const INPUT:&str=include_str!("../../../implementation/p09/evidence/p09-361-block-bookmark693-product-inputs.v1.json");
fn require(ok:bool,code:&'static str)->Result{if !ok{return Err(code.into());}Ok(())}
fn root() -> Result<PathBuf> {
    Ok(PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(std::path::Path::parent)
        .ok_or("P705_ROOT")?
        .to_owned())
}
fn read_pin(pin: &Value) -> Result<Vec<u8>> {
    let name = pin["path"].as_str().ok_or("P705_PATH")?;
    require(
        name.starts_with("implementation/p09/evidence/")
            && !name.contains('\\')
            && !name.contains(':')
            && !name
                .split('/')
                .any(|v| v.is_empty() || v == "." || v == ".."),
        "P705_PATH_SCOPE",
    )?;
    let path = root()?.join(name);
    for component in path.ancestors() {
        let meta = component.symlink_metadata()?;
        require(!meta.file_type().is_symlink(), "P705_LINK")?;
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt as _;
            require(meta.file_attributes() & 0x400 == 0, "P705_REPARSE")?;
        }
    }
    let expected = pin["bytes"].as_u64().ok_or("P705_SIZE")?;
    require(
        expected > 0
            && expected <= 4_194_304
            && path.metadata()?.is_file()
            && path.metadata()?.len() == expected,
        "P705_SIZE_LIMIT",
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
            "P705_GROWTH",
        )?;
        out.extend_from_slice(&chunk[..n]);
        std::thread::sleep(Duration::from_secs_f64(n as f64 / 2_097_152.));
    }
    require(
        out.len() as u64 == expected && hex::encode(Sha256::digest(&out)) == pin["sha256"],
        "P705_SHA",
    )?;
    Ok(out)
}

fn run()->Result<Value>{
    let input:Value=serde_json::from_str(INPUT)?;
    require(input["schema"]=="hwpx-agent.p09.block-capture-product-input693/v1"&&input["native_execution_authorized"]==false&&input["P09_complete"]==false,"P705_PROFILE")?;
    let cases=input["cases"].as_array().ok_or("P705_CASES")?;require(cases.len()==8,"P705_EIGHT")?;
    let document=DocumentId::parse("p09-block-product-readback705")?;
    let limits=ReferenceAuxiliaryLimits::new(Default::default())?;let mut rows=Vec::new();
    for(index,case)in cases.iter().enumerate(){
        require(case["case_index"]==index+1,"P705_CASE_ORDER")?;
        for stage in["candidate","initial","saved","reopened"]{
            let expected=&case["stages"][stage];let bytes=read_pin(&expected["pin"])?;let sha=Sha256::digest(&bytes).into();
            let full=Product::assess_package_source(&bytes,document.clone(),sha,SourceImportLimits::default(),limits)?;
            require(full.status()==ReferenceSourceStatus::Incomplete&&full.validation_report().is_none(),"P705_PARTIAL_ONLY")?;
            let raw=full.canonical_json(limits)?;let value:Value=serde_json::from_slice(&raw)?;
            let conditional=full.conditional_heading_declarations();
            if stage=="candidate"{
                let inventory=conditional.ok_or("P705_MISSING_ALTERNATIVES")?;
                require(value["schema_version"]=="hwpx-agent.product.reference-source-assessment/v16"&&full.heading_target_receipt().is_none()
                    &&inventory.receipt.paragraph_definitions==20&&inventory.receipt.direct_definitions==17
                    &&inventory.receipt.conditional_definitions==3&&inventory.receipt.heading_elements==23
                    &&!inventory.receipt.selected_conditional_branch&&!inventory.receipt.effective_headings_qualified
                    &&!inventory.receipt.native_or_complete_reference_state_qualified
                    &&value["unresolved"].as_array().ok_or("P705_UNRESOLVED")?.iter().any(|v|v=="conditional_heading_declarations"),"P705_EXACT_CONDITIONAL_HEADER")?;
            }else{
                require(value["schema_version"]=="hwpx-agent.product.reference-source-assessment/v15"&&conditional.is_none()
                    &&value.get("conditional_heading_declarations").is_none()&&full.heading_target_receipt().is_some(),"P705_LEGACY_NATIVE_DIRECT")?;
            }
            let field=Product::assess_package_field_semantics(&bytes,document.clone(),sha,SourceImportLimits::default(),limits)?;
            require(full.field_meanings()==&field&&field.receipt().ranges==9&&field.receipt().bookmark_crossrefs==1,"P705_FULL_FIELD_API_PARITY")?;
            let bindings=Product::read_source_bookmark_crossrefs(&bytes,document.clone(),sha,SourceImportLimits::default(),limits)?;
            require(bindings.bindings().len()==1,"P705_ONE_BINDING")?;let b=&bindings.bindings()[0];
            require(hex::encode(b.command_sha256)==expected["command_sha256"],"P705_COMMAND")?;
            let FieldCacheSnapshot::DecodedTextNotEvaluated{decoded_text_sha256,..}=&full.field_cached_source().observations().iter()
                .find(|v|v.field_reference_id==b.field_reference_id).ok_or("P705_CACHE")?.cache else{return Err("P705_DECODED".into())};
            require(hex::encode(decoded_text_sha256)==expected["display_sha256"],"P705_CACHE_PARITY")?;
            require(read_pin(&expected["pin"])?==bytes,"P705_FINAL_BYTES")?;
            rows.push(json!({"case_index":index+1,"stage":stage,"source":expected["pin"],"schema_version":value["schema_version"],
                "conditional_definitions":conditional.map_or(0,|v|v.receipt.conditional_definitions),"heading_targets_unavailable":full.heading_target_receipt().is_none(),
                "main_Source_partial_available":true,"field_API_and_cache_parity":true,"branch_selected":false,"complete_validation_qualified":false}));
        }
    }
    Ok(json!({"state":"QUALIFIED705_FIXED32_MAIN_SOURCE_CONDITIONAL_UNRESOLVED_AND_LEGACY_PARTIAL","observations":rows,"Native_started":false,"P09_complete":false}))
}
fn main(){
    let result=(||->Result{
        require(std::env::args().skip(1).collect::<Vec<_>>()==["--main-source32-readonly"],"P705_MODE")?;
        let raw=serde_json::to_vec(&run()?)?;require(raw.len()<=32768,"P705_OUTPUT")?;println!("{}",std::str::from_utf8(&raw)?);Ok(())
    })();
    if let Err(error)=result{
        let code=error.to_string();
        if code.starts_with("P705_")&&code.len()<90&&code.bytes().all(|c|c.is_ascii_uppercase()||c.is_ascii_digit()||c==b'_'){eprintln!("{code}");}
        else if let Some(kind)=error.downcast_ref::<hwpx_agent_cli::reference_validation_product::source::ReferenceSourceError>(){eprintln!("P705_MAIN_{kind}");}
        else{eprintln!("P705_REJECTED_NO_RAW_VALUES");}
        std::process::exit(2);
    }
}

