//! Fixed private worker readback only; no arbitrary paths, actions or writes.
use domain_ir::{DocumentId, ReferenceAuxiliaryLimitConfig, ReferenceAuxiliaryLimits};
use hwpx_agent_cli::reference_validation_product::{
    ReferenceValidationProductOperation as Product,
    source_crossref::{SourceCrossReferencePreparation, SourceCrossReferenceSelection},
};
use hwpx_package::{
    cross_reference_sdk::SdkCrossReferenceDisplay as Display,
    document_import::{
        ImportedSourcePackage, SourceImportLimits, structure::ImportedDocumentStructure,
    },
};
use serde_json::{Value, json};
use sha2::{Digest as _, Sha256};
use std::{
    error::Error,
    fs::{File, OpenOptions},
    io::Read,
    path::{Path, PathBuf},
    time::{Duration, Instant},
};
type Result<T> = std::result::Result<T, Box<dyn Error>>;
const INPUT_DIRECTORY: &str =
    "implementation/p09/evidence/private/p09-361-crossref-discovery-inputs-20261017-r01";
const INPUT_SHA: &str = "64539a2dc6e76f0301c8beba20cf24083810fdf571f1f5dabbbf2764cd1ee184";
const MANIFEST_SHA: &str = "fef538f8e072a72e8d0c0f42b0752a88ecdaf3fc582d4c67d07891bea34fcd29";
const PACKET_SHA: &str = "1709c77ac89e8dcb5b319e29db224d1a92dcfbb53868b44c88ce542a0ad206d1";
const BOOKMARK: &str = "p09_crossref_discovery_anchor";
const DOCUMENT: &str = "p09-crossref-sdk-discovery-input-r01";
const OUTPUT_LIMIT: usize = 16384;
fn require(ok: bool) -> Result<()> {
    if !ok {
        return Err("CROSSREF_FIXED_PROBE_REJECTED".into());
    }
    Ok(())
}
fn digest(bytes: &[u8]) -> String {
    hex::encode(Sha256::digest(bytes))
}
fn limits() -> Result<ReferenceAuxiliaryLimits> {
    Ok(ReferenceAuxiliaryLimits::new(
        ReferenceAuxiliaryLimitConfig {
            input_bytes: 65536,
            output_bytes: 262144,
            items_per_kind: 256,
            ..Default::default()
        },
    )?)
}
fn root() -> Result<PathBuf> {
    Ok(Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .ok_or("CROSSREF_PROBE_ROOT_REJECTED")?
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
fn read(path: &Path, maximum: usize) -> Result<Vec<u8>> {
    let parents: Vec<_> = path
        .parent()
        .ok_or("CROSSREF_PROBE_PARENT_REJECTED")?
        .ancestors()
        .collect();
    require(parents.len() <= 256)?;
    for parent in parents.into_iter().rev() {
        let meta = parent.symlink_metadata()?;
        direct(&meta)?;
        require(meta.is_dir())?;
    }
    let meta = path.symlink_metadata()?;
    direct(&meta)?;
    require(meta.is_file() && meta.len() > 0 && meta.len() <= maximum as u64)?;
    // Serial probe use: <=20 opens/s and <=2MiB/s source reads, including final rereads.
    std::thread::sleep(Duration::from_millis(50));
    let mut options = OpenOptions::new();
    options.read(true);
    #[cfg(windows)]
    {
        use std::os::windows::fs::OpenOptionsExt as _;
        options.share_mode(1);
    }
    let mut file: File = options.open(path)?;
    require(file.metadata()?.len() == meta.len())?;
    let mut bytes = Vec::new();
    let mut buffer = [0; 65536];
    let watch = Instant::now();
    loop {
        let n = file.read(&mut buffer)?;
        if n == 0 {
            break;
        }
        require(
            bytes
                .len()
                .checked_add(n)
                .is_some_and(|size| size <= maximum),
        )?;
        bytes.try_reserve(n)?;
        bytes.extend_from_slice(&buffer[..n]);
        let minimum = Duration::from_secs_f64(bytes.len() as f64 / 2097152.0);
        if let Some(delay) = minimum.checked_sub(watch.elapsed()) {
            std::thread::sleep(delay);
        }
    }
    require(bytes.len() as u64 == meta.len())?;
    Ok(bytes)
}
fn read_pin(path: &Path, maximum: usize, sha: &str) -> Result<Vec<u8>> {
    let bytes = read(path, maximum)?;
    require(digest(&bytes) == sha)?;
    Ok(bytes)
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum Phase {
    Opened,
    Saved,
    Reopened,
}
impl Phase {
    fn parse(text: &str) -> Result<Self> {
        Ok(match text {
            "opened" => Self::Opened,
            "saved" => Self::Saved,
            "reopened" => Self::Reopened,
            _ => return Err("CROSSREF_PROBE_PHASE_REJECTED".into()),
        })
    }
    fn name(self) -> &'static str {
        match self {
            Self::Opened => "opened",
            Self::Saved => "saved",
            Self::Reopened => "reopened",
        }
    }
}
#[derive(Clone, Debug, Eq, PartialEq)]
enum Request {
    Baseline,
    Case {
        index: usize,
        phase: Phase,
        sha: String,
    },
}
impl Request {
    fn parse(args: &[String]) -> Result<Self> {
        if args == ["baseline"] {
            return Ok(Self::Baseline);
        }
        require(args.len() == 4 && args[0] == "case")?;
        let index = args[1].parse::<usize>()?;
        require((1..=8).contains(&index) && args[1] == index.to_string())?;
        require(
            args[3].len() == 64
                && args[3]
                    .bytes()
                    .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b)),
        )?;
        Ok(Self::Case {
            index: index - 1,
            phase: Phase::parse(&args[2])?,
            sha: args[3].clone(),
        })
    }
    fn path(&self, root: &Path) -> PathBuf {
        match self {
            Self::Baseline=>root.join(INPUT_DIRECTORY).join("source-with-bookmark.hwpx"),
            Self::Case{index,phase,..}=>root.join(format!("implementation/p09/evidence/private/p09-361-crossref-bookmark-native-20261017-r01-c{:02}-attempt01/{}.hwpx",index+1,phase.name())),
        }
    }
    fn sha(&self) -> &str {
        match self {
            Self::Baseline => INPUT_SHA,
            Self::Case { sha, .. } => sha,
        }
    }
}

struct FixedPreparation {
    prepared: SourceCrossReferencePreparation,
    manifest: Vec<u8>,
    packet: Vec<u8>,
    input: Vec<u8>,
}
fn prepare(root: &Path) -> Result<FixedPreparation> {
    let directory = root.join(INPUT_DIRECTORY);
    let manifest = read_pin(
        &directory.join("source-input-manifest.v1.json"),
        65536,
        MANIFEST_SHA,
    )?;
    let packet = read_pin(
        &directory.join("prepared-sdk-batch.v1.json"),
        262144,
        PACKET_SHA,
    )?;
    let input = read_pin(
        &directory.join("source-with-bookmark.hwpx"),
        4 * 1024 * 1024,
        INPUT_SHA,
    )?;
    require(input.len() == 14425)?;
    let document = DocumentId::parse(DOCUMENT)?;
    let source = ImportedDocumentStructure::import(ImportedSourcePackage::import(
        &input,
        document.clone(),
        Sha256::digest(&input).into(),
        SourceImportLimits::default(),
    )?)?;
    let bookmark = source.observed_bookmark_by_name(BOOKMARK)?;
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
    let prepared = Product::prepare_source_crossref_discovery(
        &input,
        document,
        Sha256::digest(&input).into(),
        SourceImportLimits::default(),
        limits()?,
        &selections,
    )?;
    let bound: Value = serde_json::from_slice(&packet)?;
    require(
        bound["cases"]
            .as_array()
            .is_some_and(|rows| rows.len() == 8)
            && bound["native_execution_authorized"] == false,
    )?;
    for (i, candidate) in prepared.candidates_for_discovery().iter().enumerate() {
        require(
            bound["cases"][i]["case_id"] == format!("P09-XREF-BOOK-C{:02}", i + 1)
                && bound["cases"][i]["source_binding_receipt"]
                    == serde_json::to_value(candidate.receipt())?
                && bound["cases"][i]["sdk_command"] == candidate.command_for_discovery(),
        )?;
    }
    Ok(FixedPreparation {
        prepared,
        manifest,
        packet,
        input,
    })
}
fn summarize(
    prepared: &SourceCrossReferencePreparation,
    request: &Request,
    bytes: &[u8],
) -> Result<Value> {
    require(digest(bytes) == request.sha())?;
    let sha = Sha256::digest(bytes).into();
    // Both original observations share one immutable output import. Retain the
    // fixed probe response below; this adds no native authority or write route.
    let observed = prepared.observe_output_for_discovery(
        bytes,
        sha,
        SourceImportLimits::default(),
        limits()?,
    )?;
    let fields: Value = serde_json::from_slice(
        &observed.commands().canonical_json(limits()?)?,
    )?;
    let targets: Value = serde_json::from_slice(
        &observed.targets().canonical_json(limits()?)?,
    )?;
    let field_rows = fields["candidates"]
        .as_array()
        .ok_or("CROSSREF_PROBE_FIELD_ROWS")?;
    let target_rows = targets["candidates"]
        .as_array()
        .ok_or("CROSSREF_PROBE_TARGET_ROWS")?;
    require(field_rows.len() == 8 && target_rows.len() == 8)?;
    for i in 0..8 {
        require(
            field_rows[i]["expected_candidate_receipt_sha256"]
                == target_rows[i]["expected_candidate_receipt_sha256"],
        )?;
    }
    let selected = match request {
        Request::Baseline => Value::Null,
        Request::Case { index, phase, .. } => {
            json!({"case_id":format!("P09-XREF-BOOK-C{:02}",index+1),"phase":phase.name(),
            "source_target_observation":target_rows[*index],"crossref_command_observation":field_rows[*index]})
        }
    };
    let count = |key: &str| {
        target_rows
            .iter()
            .filter(|row| row["observation"] == key)
            .count()
    };
    let result = json!({
        "schema_version":"hwpx-agent.private.crossref-worker-source-probe/v1",
        "state":"source_probe_completed_not_native_attestation",
        "prepared_batch_sha256":PACKET_SHA,"prepared_source_sha256":INPUT_SHA,
        "observed_output_sha256":request.sha(),"observed_output_bytes":bytes.len(),"candidate_count":8,
        "observed_targets_receipt":targets["observed_targets"],
        "target_candidate_counts":{"unique_exact_name_observed":count("unique_exact_name_observed"),
            "not_observed":count("not_observed"),"ambiguous_exact_name":count("ambiguous_exact_name")},
        "crossref_fields":fields["crossref_fields"],"plain_string_leaves":fields["plain_string_leaves"],
        "opaque_parameter_children":fields["opaque_parameter_children"],"crossrefs_without_parameters":fields["crossrefs_without_parameters"],
        "selected_case":selected,
        "native_execution_attested":false,"native_target_resolution_qualified":false,
        "parameter_key_semantics_qualified":false,"causal_insertion_or_preservation_proved":false,
        "complete_reference_validation_qualified":false,"native_execution_authorized":false,
        "raw_document_values_or_sdk_commands_present":false,"p09_complete":false,
    });
    require(serde_json::to_vec(&result)?.len() <= OUTPUT_LIMIT)?;
    Ok(result)
}
#[derive(Clone, Copy)]
enum CaptureNamespace {
    Original,
    Fixed003,
    Fixed004,
    Fixed005,
    Fixed006,
}

impl CaptureNamespace {
    fn path(self, request: &Request, root: &Path) -> PathBuf {
        match (self, request) {
            (Self::Fixed006, Request::Case { index, phase, .. }) => root.join(format!(
                "implementation/p09/evidence/private/p09-361-crossref-bookmark-native-20261022-g006-c{:02}-attempt01/{}.hwpx",
                index + 1,
                phase.name()
            )),
            (Self::Fixed005, Request::Case { index, phase, .. }) => root.join(format!(
                "implementation/p09/evidence/private/p09-361-crossref-bookmark-native-20261022-g005-c{:02}-attempt01/{}.hwpx",
                index + 1,
                phase.name()
            )),
            (Self::Fixed004, Request::Case { index, phase, .. }) => root.join(format!(
                "implementation/p09/evidence/private/p09-361-crossref-bookmark-native-20261022-g004-c{:02}-attempt01/{}.hwpx",
                index + 1,
                phase.name()
            )),
            (Self::Fixed003, Request::Case { index, phase, .. }) => root.join(format!(
                "implementation/p09/evidence/private/p09-361-crossref-bookmark-native-20261021-g003-c{:02}-attempt01/{}.hwpx",
                index + 1,
                phase.name()
            )),
            _ => request.path(root),
        }
    }
}

fn run(request: &Request) -> Result<Value> {
    run_for_namespace(request, CaptureNamespace::Original)
}

fn run_for_namespace(request: &Request, namespace: CaptureNamespace) -> Result<Value> {
    let root = root()?;
    let fixed = prepare(&root)?;
    let path = namespace.path(request, &root);
    let output = match request {
        Request::Baseline => fixed.input.clone(),
        _ => read_pin(&path, 4 * 1024 * 1024, request.sha())?,
    };
    let result = summarize(&fixed.prepared, request, &output)?;
    let directory = root.join(INPUT_DIRECTORY);
    require(
        read_pin(
            &directory.join("source-input-manifest.v1.json"),
            65536,
            MANIFEST_SHA,
        )? == fixed.manifest
            && read_pin(
                &directory.join("prepared-sdk-batch.v1.json"),
                262144,
                PACKET_SHA,
            )? == fixed.packet,
    )?;
    fixed.prepared.verify_source(&read_pin(
        &directory.join("source-with-bookmark.hwpx"),
        4 * 1024 * 1024,
        INPUT_SHA,
    )?)?;
    if !matches!(request, Request::Baseline) {
        require(read_pin(&path, 4 * 1024 * 1024, request.sha())? == output)?;
    }
    Ok(result)
}
fn main() {
    entry(CaptureNamespace::Original);
}

#[allow(dead_code)] // Used by the separate fixed003 example wrapper.
pub(crate) fn main_for_capture003() {
    entry(CaptureNamespace::Fixed003);
}

#[allow(dead_code)] // A separate readonly wrapper, not a retry selector or Native entry.
pub(crate) fn main_for_capture004() {
    entry(CaptureNamespace::Fixed004);
}

#[allow(dead_code)] // Separate readonly fixed005 wrapper; never a generation selector or Native entry.
pub(crate) fn main_for_capture005() {
    entry(CaptureNamespace::Fixed005);
}

#[allow(dead_code)] // Fixed006 wrapper only; never a Native or retry selector.
pub(crate) fn main_for_capture006() {
    entry(CaptureNamespace::Fixed006);
}

fn entry(namespace: CaptureNamespace) {
    let result = std::env::args_os()
        .skip(1)
        .map(|a| {
            a.into_string()
                .map_err(|_| "CROSSREF_PROBE_ARGUMENT_ENCODING")
        })
        .collect::<std::result::Result<Vec<_>, _>>()
        .map_err(Into::into)
        .and_then(|args| Request::parse(&args))
        .and_then(|request| match namespace {
            CaptureNamespace::Original => run(&request),
            CaptureNamespace::Fixed003 => run_for_namespace(&request, namespace),
            CaptureNamespace::Fixed004 => run_for_namespace(&request, namespace),
            CaptureNamespace::Fixed005 => run_for_namespace(&request, namespace),
            CaptureNamespace::Fixed006 => run_for_namespace(&request, namespace),
        });
    match result {
        Ok(value) => println!("{value}"),
        Err(_) => {
            eprintln!("CROSSREF_FIXED_SOURCE_PROBE_FAILED");
            std::process::exit(2);
        }
    }
}

#[cfg(test)]
mod capture006_tests {
    use super::*;
    #[test]
    fn all24_paths_are_closed_unique_and_disjoint_from_every_consumed_namespace() -> Result<()> {
        let root = root()?;
        let mut seen = std::collections::BTreeSet::new();
        for case in 1..=8 {
            for phase in ["opened", "saved", "reopened"] {
                let request = Request::parse(&["case".into(), case.to_string(), phase.into(), INPUT_SHA.into()])?;
                let path = CaptureNamespace::Fixed006.path(&request, &root);
                require(path.ends_with(format!("p09-361-crossref-bookmark-native-20261022-g006-c{case:02}-attempt01/{phase}.hwpx")))?;
                require([CaptureNamespace::Original,CaptureNamespace::Fixed003,CaptureNamespace::Fixed004,CaptureNamespace::Fixed005]
                    .into_iter().all(|old|path != old.path(&request,&root)) && seen.insert(path))?;
            }
        }
        require(seen.len()==24)
    }
    #[test]
    fn baseline_is_original_source_only_not_a_native_or_semantic_permit() -> Result<()> {
        let value=run_for_namespace(&Request::Baseline,CaptureNamespace::Fixed006)?;
        require(value["candidate_count"]==8 && value["selected_case"].is_null())?;
        for key in ["native_execution_attested","native_target_resolution_qualified","parameter_key_semantics_qualified",
            "complete_reference_validation_qualified","native_execution_authorized","p09_complete"] {require(value[key]==false)?;}
        Ok(())
    }
    #[test]
    fn missing_fixed006_capture_cannot_reuse_older_artifacts() -> Result<()> {
        let request=Request::parse(&["case".into(),"1".into(),"opened".into(),INPUT_SHA.into()])?;
        require(!CaptureNamespace::Fixed006.path(&request,&root()?).try_exists()?)?;
        require(run_for_namespace(&request,CaptureNamespace::Fixed006).is_err())
    }
    #[test]
    fn no_caller_generation_or_retry_selector_is_added() -> Result<()> {
        for values in [vec!["generation","5"],vec!["baseline","5"],vec!["retry","1"],vec!["case","9","opened",INPUT_SHA]] {
            let args=values.into_iter().map(str::to_owned).collect::<Vec<_>>();
            require(Request::parse(&args).is_err())?;
        }
        Ok(())
    }
}
#[cfg(test)]
mod capture005_tests {
    use super::*;
    #[test]
    fn all24_paths_are_closed_unique_and_disjoint_from_every_consumed_namespace() -> Result<()> {
        let root = root()?;
        let mut seen = std::collections::BTreeSet::new();
        for case in 1..=8 {
            for phase in ["opened", "saved", "reopened"] {
                let request = Request::parse(&["case".into(), case.to_string(), phase.into(), INPUT_SHA.into()])?;
                let path = CaptureNamespace::Fixed005.path(&request, &root);
                require(path.ends_with(format!("p09-361-crossref-bookmark-native-20261022-g005-c{case:02}-attempt01/{phase}.hwpx")))?;
                require([CaptureNamespace::Original,CaptureNamespace::Fixed003,CaptureNamespace::Fixed004]
                    .into_iter().all(|old|path != old.path(&request,&root)) && seen.insert(path))?;
            }
        }
        require(seen.len()==24)
    }
    #[test]
    fn baseline_is_original_source_only_not_a_native_or_semantic_permit() -> Result<()> {
        let value=run_for_namespace(&Request::Baseline,CaptureNamespace::Fixed005)?;
        require(value["candidate_count"]==8 && value["selected_case"].is_null())?;
        for key in ["native_execution_attested","native_target_resolution_qualified","parameter_key_semantics_qualified",
            "complete_reference_validation_qualified","native_execution_authorized","p09_complete"] {require(value[key]==false)?;}
        Ok(())
    }
    #[test]
    fn missing_fixed005_capture_cannot_reuse_older_artifacts() -> Result<()> {
        let request=Request::parse(&["case".into(),"1".into(),"opened".into(),INPUT_SHA.into()])?;
        require(!CaptureNamespace::Fixed005.path(&request,&root()?).try_exists()?)?;
        require(run_for_namespace(&request,CaptureNamespace::Fixed005).is_err())
    }
    #[test]
    fn no_caller_generation_or_retry_selector_is_added() -> Result<()> {
        for values in [vec!["generation","5"],vec!["baseline","5"],vec!["retry","1"],vec!["case","9","opened",INPUT_SHA]] {
            let args=values.into_iter().map(str::to_owned).collect::<Vec<_>>();
            require(Request::parse(&args).is_err())?;
        }
        Ok(())
    }
}

#[cfg(test)]
mod capture004_tests {
    use super::*;
    #[test]
    fn all24_paths_are_new_and_disjoint_from_both_consumed_namespaces() -> Result<()> {
        let root = root()?;
        let mut seen = std::collections::BTreeSet::new();
        for case in 1..=8 {
            for phase in ["opened", "saved", "reopened"] {
                let request = Request::parse(&["case".into(), case.to_string(), phase.into(), INPUT_SHA.into()])?;
                let path = CaptureNamespace::Fixed004.path(&request, &root);
                require(path.ends_with(format!("p09-361-crossref-bookmark-native-20261022-g004-c{case:02}-attempt01/{phase}.hwpx")))?;
                require(path != CaptureNamespace::Original.path(&request, &root)
                    && path != CaptureNamespace::Fixed003.path(&request, &root) && seen.insert(path))?;
            }
        }
        require(seen.len() == 24)
    }
    #[test]
    fn fixed004_baseline_is_source_only_and_not_a_native_permit() -> Result<()> {
        let value = run_for_namespace(&Request::Baseline, CaptureNamespace::Fixed004)?;
        require(value["candidate_count"] == 8 && value["selected_case"].is_null())?;
        for key in ["native_execution_attested", "native_target_resolution_qualified", "parameter_key_semantics_qualified",
            "complete_reference_validation_qualified", "native_execution_authorized", "p09_complete"] { require(value[key] == false)?; }
        Ok(())
    }
    #[test]
    fn missing004_artifact_does_not_fall_back_to003_or_original_source() -> Result<()> {
        let request = Request::parse(&["case".into(), "1".into(), "opened".into(), INPUT_SHA.into()])?;
        require(!CaptureNamespace::Fixed004.path(&request, &root()?).try_exists()?)?;
        require(run_for_namespace(&request, CaptureNamespace::Fixed004).is_err())
    }
    #[test]
    fn caller_cannot_choose_generation_retry_path_or_case_subset() -> Result<()> {
        for args in [vec!["baseline", "--generation", "4"],vec!["case", "1", "opened", INPUT_SHA, "--retry"],
            vec!["case", "1", "../opened", INPUT_SHA],vec!["case", "01", "opened", INPUT_SHA],
            vec!["case", "9", "opened", INPUT_SHA],vec!["case", "1", "opened", "D:/private/document.hwpx"]] {
            require(Request::parse(&args.into_iter().map(str::to_owned).collect::<Vec<_>>()).is_err())?;
        }
        Ok(())
    }
}

#[cfg(test)]
mod capture003_tests {
    use super::*;

    #[test]
    fn all24_phase_paths_are_disjoint_from_consumed_original_paths() -> Result<()> {
        let root = root()?;
        let mut seen = std::collections::BTreeSet::new();
        for case in 1..=8 {
            for phase in ["opened", "saved", "reopened"] {
                let request = Request::parse(&[
                    "case".into(), case.to_string(), phase.into(), INPUT_SHA.into(),
                ])?;
                let path = CaptureNamespace::Fixed003.path(&request, &root);
                require(path.ends_with(format!(
                    "p09-361-crossref-bookmark-native-20261021-g003-c{case:02}-attempt01/{phase}.hwpx"
                )))?;
                require(path != CaptureNamespace::Original.path(&request, &root))?;
                require(seen.insert(path))?;
                require(CaptureNamespace::Original.path(&request, &root) == request.path(&root))?;
            }
        }
        require(seen.len() == 24)
    }

    #[test]
    fn fixed003_baseline_reads_original_pins_and_grants_no_native_claim() -> Result<()> {
        let root = root()?;
        require(CaptureNamespace::Fixed003.path(&Request::Baseline, &root)
            == Request::Baseline.path(&root))?;
        let value = run_for_namespace(&Request::Baseline, CaptureNamespace::Fixed003)?;
        require(value["candidate_count"] == 8 && value["crossref_fields"] == 0
            && value["prepared_source_sha256"] == INPUT_SHA
            && value["prepared_batch_sha256"] == PACKET_SHA
            && value["selected_case"].is_null())?;
        for key in ["native_execution_attested", "native_target_resolution_qualified",
            "parameter_key_semantics_qualified", "causal_insertion_or_preservation_proved",
            "complete_reference_validation_qualified", "native_execution_authorized",
            "raw_document_values_or_sdk_commands_present", "p09_complete"] {
            require(value[key] == false)?;
        }
        Ok(())
    }

    #[test]
    fn missing003_artifact_never_falls_back_to_original_case_or_source() -> Result<()> {
        let request = Request::parse(&["case".into(), "1".into(), "opened".into(), INPUT_SHA.into()])?;
        require(!CaptureNamespace::Fixed003.path(&request, &root()?).try_exists()?)?;
        require(run_for_namespace(&request, CaptureNamespace::Fixed003).is_err())
    }

    #[test]
    fn namespace_cannot_be_selected_by_extra_cli_path_or_retry_arguments() -> Result<()> {
        for args in [
            vec!["baseline", "--generation", "3"],
            vec!["case", "1", "opened", INPUT_SHA, "--retry"],
            vec!["case", "1", "../opened", INPUT_SHA],
            vec!["case", "01", "opened", INPUT_SHA],
            vec!["case", "9", "opened", INPUT_SHA],
            vec!["case", "1", "opened", "C:/private/file.hwpx"],
        ] {
            require(Request::parse(&args.into_iter().map(str::to_owned).collect::<Vec<_>>()).is_err())?;
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn actual_fixed_baseline_binds_both_product_readbacks_without_native_claims() -> Result<()> {
        let value = run(&Request::Baseline)?;
        require(
            value["candidate_count"] == 8
                && value["target_candidate_counts"]["unique_exact_name_observed"] == 8
                && value["crossref_fields"] == 0
                && value["selected_case"].is_null(),
        )?;
        for key in [
            "native_execution_attested",
            "native_target_resolution_qualified",
            "causal_insertion_or_preservation_proved",
            "native_execution_authorized",
        ] {
            require(value[key] == false)?;
        }
        Ok(())
    }
    #[test]
    fn fixed_case_phase_matrix_never_accepts_a_path_subset_or_noncanonical_index() -> Result<()> {
        require(Request::parse(&["baseline".into()])? == Request::Baseline)?;
        for i in 1..=8 {
            for phase in ["opened", "saved", "reopened"] {
                let request =
                    Request::parse(&["case".into(), i.to_string(), phase.into(), "a".repeat(64)])?;
                require(request.path(&root()?).ends_with(format!(
                    "p09-361-crossref-bookmark-native-20261017-r01-c{i:02}-attempt01/{phase}.hwpx"
                )))?;
            }
        }
        for args in [
            vec![],
            vec!["baseline".into(), "extra".into()],
            vec!["case".into(), "0".into(), "saved".into(), "a".repeat(64)],
            vec!["case".into(), "01".into(), "saved".into(), "a".repeat(64)],
            vec!["case".into(), "9".into(), "saved".into(), "a".repeat(64)],
            vec!["case".into(), "1".into(), "../saved".into(), "a".repeat(64)],
            vec!["case".into(), "1".into(), "saved".into(), "A".repeat(64)],
        ] {
            require(Request::parse(&args).is_err())?;
        }
        Ok(())
    }
    #[test]
    fn selected_case_reports_only_digest_bound_observations_without_a_native_attestation()
    -> Result<()> {
        let fixed = prepare(&root()?)?;
        let request = Request::Case {
            index: 7,
            phase: Phase::Saved,
            sha: INPUT_SHA.into(),
        };
        let value = summarize(&fixed.prepared, &request, &fixed.input)?;
        require(
            value["selected_case"]["case_id"] == "P09-XREF-BOOK-C08"
                && value["selected_case"]["source_target_observation"]["observation"]
                    == "unique_exact_name_observed"
                && value["selected_case"]["crossref_command_observation"]["observation"]
                    == "not_observed",
        )?;
        let text = value.to_string();
        require(!text.contains(BOOKMARK) && !text.contains("?p09_") && text.len() <= OUTPUT_LIMIT)?;
        Ok(())
    }
    #[test]
    fn bounded_local_reads_do_not_write_or_accept_a_wrong_pin() -> Result<()> {
        use std::io::Write as _;
        let mut file = tempfile::NamedTempFile::new()?;
        file.write_all(b"retained")?;
        file.flush()?;
        let path = file.into_temp_path(); // Close the writer before Windows deny-write read sharing.
        require(read_pin(&path, 8, &digest(b"retained"))? == b"retained")?;
        require(read(&path, 7).is_err() && read_pin(&path, 8, &"0".repeat(64)).is_err())?;
        require(std::fs::read(&path)? == b"retained")?;
        Ok(())
    }
}
