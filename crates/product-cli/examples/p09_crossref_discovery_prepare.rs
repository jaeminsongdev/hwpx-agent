//! Fixed private preparation artifact only. No arguments, SDK/native executor,
//! public CLI route, output/attempt selector or automatic retry is provided.
use std::{
    error::Error,
    fs::{File, OpenOptions},
    io::{Read, Write},
    path::{Path, PathBuf},
};

use domain_ir::{DocumentId, ReferenceAuxiliaryLimits};
use hwpx_agent_cli::reference_validation_product::{
    ReferenceValidationProductOperation, source_crossref::SourceCrossReferenceSelection,
};
use hwpx_package::{
    cross_reference_sdk::SdkCrossReferenceDisplay as Display,
    document_import::{
        ImportedSourcePackage, SourceImportLimits, reference_targets::ImportedReferenceTargets,
        structure::ImportedDocumentStructure,
    },
};
use serde_json::{Value, json};
use sha2::{Digest as _, Sha256};

type Result<T> = std::result::Result<T, Box<dyn Error>>;
const DIRECTORY: &str =
    "implementation/p09/evidence/private/p09-361-crossref-discovery-inputs-20261017-r01";
const MANIFEST_SHA: &str = "fef538f8e072a72e8d0c0f42b0752a88ecdaf3fc582d4c67d07891bea34fcd29";
const INPUT_SHA: &str = "64539a2dc6e76f0301c8beba20cf24083810fdf571f1f5dabbbf2764cd1ee184";
const BOOKMARK: &str = "p09_crossref_discovery_anchor";
const DOCUMENT: &str = "p09-crossref-sdk-discovery-input-r01";
const OUTPUT: &str = "prepared-sdk-batch.v1.json";

fn require(ok: bool) -> Result<()> {
    if !ok {
        return Err("CROSSREF_FIXED_PREPARATION_REJECTED".into());
    }
    Ok(())
}
fn digest(bytes: &[u8]) -> String {
    hex::encode(Sha256::digest(bytes))
}
fn root() -> Result<PathBuf> {
    Ok(Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .ok_or("CROSSREF_ROOT_REJECTED")?
        .to_owned())
}
fn direct(metadata: &std::fs::Metadata) -> Result<()> {
    require(!metadata.file_type().is_symlink())?;
    #[cfg(windows)]
    {
        use std::os::windows::fs::MetadataExt as _;
        require(metadata.file_attributes() & 0x400 == 0)?;
    }
    Ok(())
}
fn parents(path: &Path) -> Result<()> {
    let chain: Vec<_> = path
        .parent()
        .ok_or("CROSSREF_PARENT_REJECTED")?
        .ancestors()
        .collect();
    require(chain.len() <= 256)?;
    for ancestor in chain.into_iter().rev() {
        let metadata = ancestor.symlink_metadata()?;
        direct(&metadata)?;
        require(metadata.is_dir())?;
    }
    Ok(())
}
fn read(path: &Path, maximum: usize) -> Result<Vec<u8>> {
    parents(path)?;
    let metadata = path.symlink_metadata()?;
    direct(&metadata)?;
    require(metadata.is_file() && metadata.len() <= maximum as u64)?;
    let file = File::open(path)?;
    require(file.metadata()?.is_file())?;
    let mut bytes = Vec::new();
    file.take(maximum as u64 + 1).read_to_end(&mut bytes)?;
    require(bytes.len() <= maximum)?;
    Ok(bytes)
}
fn write_once(path: &Path, bytes: &[u8]) -> Result<()> {
    parents(path)?;
    require(bytes.len() <= 262144)?;
    let mut file = OpenOptions::new().create_new(true).write(true).open(path)?;
    file.write_all(bytes)?;
    file.flush()?;
    file.sync_all()?;
    Ok(())
}
fn limits() -> Result<ReferenceAuxiliaryLimits> {
    Ok(ReferenceAuxiliaryLimits::new(Default::default())?)
}

fn build(root: &Path) -> Result<Value> {
    let directory = root.join(DIRECTORY);
    let manifest_bytes = read(&directory.join("source-input-manifest.v1.json"), 65536)?;
    require(digest(&manifest_bytes) == MANIFEST_SHA)?;
    let manifest: Value = serde_json::from_slice(&manifest_bytes)?;
    require(
        manifest["fixture_only"] == true
            && manifest["native_execution_authorized"] == false
            && manifest["expected_candidate_count"] == 8
            && manifest["generated_input"]["sha256"] == INPUT_SHA,
    )?;
    let input_path = directory.join("source-with-bookmark.hwpx");
    let bytes = read(&input_path, 4 * 1024 * 1024)?;
    require(digest(&bytes) == INPUT_SHA && bytes.len() == 14425)?;
    let expected: [u8; 32] = Sha256::digest(&bytes).into();
    let document = DocumentId::parse(DOCUMENT)?;
    // The initial read derives a selector from the actual source, not a guessed
    // logical ID. Product preparation then imports once for the entire batch.
    let source = ImportedDocumentStructure::import(ImportedSourcePackage::import(
        &bytes,
        document.clone(),
        expected,
        SourceImportLimits::default(),
    )?)?;
    let bookmark = source.observed_bookmark_by_name(BOOKMARK)?;
    let targets = ImportedReferenceTargets::import(&source, limits()?)?;
    require(
        targets.receipt().bookmark_targets == 1 && targets.receipt().observed_native_fields == 1,
    )?;
    let mut selections = Vec::new();
    for display in [
        Display::Page,
        Display::BookmarkName,
        Display::Content,
        Display::RelativePosition,
    ] {
        for hyperlink in [false, true] {
            selections.push(SourceCrossReferenceSelection {
                target_id: bookmark.reference_id.clone(),
                display,
                hyperlink,
            });
        }
    }
    let prepared = ReferenceValidationProductOperation::prepare_source_crossref_discovery(
        &bytes,
        document,
        expected,
        SourceImportLimits::default(),
        limits()?,
        &selections,
    )?;
    require(prepared.candidates_for_discovery().len() == 8)?;
    let observations = prepared.observe_crossref_output(
        &bytes,
        expected,
        SourceImportLimits::default(),
        limits()?,
    )?;
    let input_observations: Value =
        serde_json::from_slice(&observations.canonical_json(limits()?)?)?;
    require(
        input_observations["crossref_fields"] == 0
            && input_observations["native_execution_attested"] == false,
    )?;
    let mut cases = Vec::new();
    for (index, candidate) in prepared.candidates_for_discovery().iter().enumerate() {
        cases.push(json!({
            "case_id":format!("P09-XREF-BOOK-C{:02}",index+1),
            "sdk_action":"InsertCrossReference", "sdk_parameter_set":"HActionCrossRef", "sdk_property":"Command",
            "sdk_command":candidate.command_for_discovery(), "source_binding_receipt":candidate.receipt(),
            "native_execution":"not_run", "requires_native_target_qualification":true,
        }));
    }
    prepared.verify_source(&read(&input_path, 4 * 1024 * 1024)?)?;
    require(read(&directory.join("source-input-manifest.v1.json"), 65536)? == manifest_bytes)?;
    Ok(json!({
        "schema_version":"hwpx-agent.private.crossref-discovery-prepared-batch/v1",
        "state":"prepared_eight_source_bound_candidates_not_native_ready",
        "native_execution_authorized":false, "native_executed":false, "native_attempt_created":false,
        "generated_input_pin":manifest["generated_input"], "source_manifest_sha256":MANIFEST_SHA,
        "document_namespace":DOCUMENT, "cases":cases, "generated_input_observations":input_observations,
        "contains_generated_private_sdk_commands":true, "public_raw_action_route":false,
        "separate_from_frozen_p58_full34_queue":true,
        "remaining_native_prerequisites":["qualified_owned_session_and_active_document_binding","native_target_binding_after_open","current_safe_worker_and_whole_batch_preflight","explicit_human_native_execution_authority","actual_save_reopen_and_preservation_readback"],
        "accepted_count_delta":0, "p09_complete":false,
    }))
}

fn run() -> Result<Value> {
    require(std::env::args_os().len() == 1)?;
    let root = root()?;
    let bundle = build(&root)?;
    let mut bytes = serde_json::to_vec_pretty(&bundle)?;
    bytes.push(b'\n');
    let path = root.join(DIRECTORY).join(OUTPUT);
    write_once(&path, &bytes)?;
    require(read(&path, 262144)? == bytes)?;
    Ok(
        json!({"state":"private_eight_candidate_preparation_written_no_native","candidate_count":8,
              "native_execution_authorized":false,"bytes":bytes.len(),"sha256":digest(&bytes)}),
    )
}
fn main() {
    match run() {
        Ok(summary) => println!("{summary}"),
        Err(_) => {
            eprintln!("CROSSREF_FIXED_PREPARATION_FAILED");
            std::process::exit(2);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn actual_fixed_input_prepares_all_eight_without_native_authority() -> Result<()> {
        let bundle = build(&root()?)?;
        require(bundle["cases"].as_array().ok_or("cases")?.len() == 8)?;
        require(
            bundle["native_execution_authorized"] == false
                && bundle["native_attempt_created"] == false,
        )?;
        require(bundle["generated_input_observations"]["crossref_fields"] == 0)?;
        for case in bundle["cases"].as_array().ok_or("cases")? {
            require(
                case["source_binding_receipt"]["source"]["source_package_sha256"]
                    == json!(hex::decode(INPUT_SHA)?),
            )?;
            require(case["requires_native_target_qualification"] == true)?;
        }
        Ok(())
    }
    #[test]
    fn exclusive_artifact_write_never_overwrites_existing_file() -> Result<()> {
        let temp = tempfile::tempdir()?;
        let path = temp.path().join("retained.json");
        write_once(&path, b"original")?;
        require(write_once(&path, b"replacement").is_err())?;
        require(read(&path, 1024)? == b"original")?;
        Ok(())
    }
    #[test]
    fn command_set_is_distinct_current_document_and_receipts_do_not_publish_names() -> Result<()> {
        let bundle = build(&root()?)?;
        let mut commands = std::collections::BTreeSet::new();
        for case in bundle["cases"].as_array().ok_or("cases")? {
            let command = case["sdk_command"].as_str().ok_or("command")?;
            require(
                command.starts_with('?') && command.ends_with(";0") && commands.insert(command),
            )?;
            require(!serde_json::to_string(&case["source_binding_receipt"])?.contains(BOOKMARK))?;
        }
        require(commands.len() == 8)?;
        Ok(())
    }
}
