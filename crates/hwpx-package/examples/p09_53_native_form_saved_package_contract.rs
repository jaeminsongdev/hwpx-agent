//! Exact complete saved-package contract. No native activation or acceptance promotion.
use domain_ir::{
    FormControlIdentity, FormControlLimitConfig, FormControlLimits, FormControlPayload,
    FormTextValidation, LogicalId,
};
use hwpx_package::{
    BoundedZipReader, NativeFormHwpxMap, NativeFormHwpxReadback, NativeFormObservedPayload,
    NativeFormPackageLimits, NativeFormPackageMap, NativeFormPackagePolicy,
    NativeFormPackageReadback, NativeFormPackageReader, NativeFormPackageSectionMap, PackageLimits,
};
use serde_json::{Value, json};
use sha2::{Digest as _, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    error::Error,
    fs,
    io::{Cursor, Read as _},
    path::Path,
};

type AnyError = Box<dyn Error>;
const ORIGINAL: &str =
    "fixtures/target-build/p09-35-native-form-diagnostics-01/output/fixture-manifest.json";
const ORIGINAL_SHA: &str = "ef1bdad32cf06b07725a17888b7378e9720b2111539675c20178ab850f1d9750";
const CANDIDATES: &str =
    "fixtures/target-build/p09-51-native-form-candidates-20261003-r01/output/fixture-manifest.json";
const CANDIDATES_SHA: &str = "c18e5d8b3c9af28367137735572b6842c56aca43b0676f40e48836fc4f7a51cd";
const RECOVERY: &str = "implementation/p09/evidence/p09-36-native-form-complete-recovery.r06.json";
const RECOVERY_SHA: &str = "47df877e392f1ffd0a79f16eb2629db8eedc1f85390f4b75e47a5d77029586cb";
const DISPATCH: &str = "implementation/p09/evidence/p09-52-native-form-binding-dispatch.r01.json";
const ADMISSION: &str = "implementation/p09/evidence/p09-52-native-form-binding-admission.v1.json";
const ADMISSION_SHA: &str = "f33948527c1208019d3dc87693cf71c8a7e2cadbc9326feff66a6f9bae354752";

fn sha(raw: &[u8]) -> String {
    hex::encode(Sha256::digest(raw))
}
fn linked(metadata: &fs::Metadata) -> bool {
    #[cfg(windows)]
    {
        use std::os::windows::fs::MetadataExt as _;
        if metadata.file_attributes() & 0x400 != 0 {
            return true;
        }
    }
    metadata.file_type().is_symlink()
}
fn bytes(path: &Path) -> Result<Vec<u8>, AnyError> {
    for ancestor in path.ancestors() {
        if linked(&fs::symlink_metadata(ancestor)?) {
            return Err("candidate linked path".into());
        }
    }
    let metadata = fs::metadata(path)?;
    if !metadata.is_file() || metadata.len() == 0 || metadata.len() > 4 * 1024 * 1024 {
        return Err("candidate file bound".into());
    }
    let mut raw = Vec::new();
    fs::File::open(path)?
        .take(4 * 1024 * 1024 + 1)
        .read_to_end(&mut raw)?;
    if u64::try_from(raw.len())? != metadata.len() {
        return Err("candidate file changed".into());
    }
    Ok(raw)
}
fn checked(path: &Path, digest: &str) -> Result<Vec<u8>, AnyError> {
    let raw = bytes(path)?;
    if sha(&raw) != digest {
        return Err("candidate source changed".into());
    }
    Ok(raw)
}
fn domain() -> Result<FormControlLimits, AnyError> {
    Ok(FormControlLimits::new(FormControlLimitConfig::default())?)
}
fn mapping(count: usize) -> Result<NativeFormPackageMap, AnyError> {
    Ok(NativeFormPackageMap {
        sections: (0..count)
            .map(|i| {
                Ok(NativeFormPackageSectionMap {
                    part: format!("Contents/section{i}.xml"),
                    map: NativeFormHwpxMap {
                        paragraph_ids: (0..2)
                            .map(|j| LogicalId::parse(format!("section-{i}-paragraph-{j}")))
                            .collect::<Result<_, _>>()?,
                        component_controls: vec![FormControlIdentity {
                            logical_control_id: LogicalId::parse(format!("section-{i}-control"))?,
                            // Explicit component reservation; never a native instance ID.
                            native_object_id: 90001 + u32::try_from(i)?,
                        }],
                    },
                })
            })
            .collect::<Result<_, AnyError>>()?,
    })
}
// Original explicit fixture policies, with their original pinned hash checked.
// Defaults/validation here are caller declarations, not native inferred behavior.
fn policies(
    observed: &NativeFormPackageReadback,
) -> Result<Vec<NativeFormPackagePolicy>, AnyError> {
    observed
        .sections()
        .flat_map(NativeFormHwpxReadback::controls)
        .map(|control| {
            let payload = match &control.payload {
                NativeFormObservedPayload::Text {
                    value,
                    multi_line,
                    password_character,
                    native_max_length,
                    scroll_bars,
                    tab_key_behavior,
                    number_only,
                    read_only,
                    alignment,
                } => FormControlPayload::Text {
                    value: value.clone(),
                    default_value: value.clone(),
                    validation: FormTextValidation {
                        required: false,
                        minimum_characters: 0,
                        maximum_characters: *native_max_length,
                        external_validator_sha256: None,
                    },
                    multi_line: *multi_line,
                    password_character: password_character.clone(),
                    native_max_length: *native_max_length,
                    scroll_bars: *scroll_bars,
                    tab_key_behavior: *tab_key_behavior,
                    number_only: *number_only,
                    read_only: *read_only,
                    alignment: *alignment,
                },
                NativeFormObservedPayload::Button {
                    caption,
                    value,
                    radio_group_name,
                    tri_state,
                    back_style,
                } => FormControlPayload::Radio {
                    caption: caption.clone(),
                    value: *value,
                    default_value: *value,
                    radio_group_name: radio_group_name
                        .clone()
                        .ok_or("candidate radio group missing")?,
                    group_required: true,
                    tri_state: *tri_state,
                    back_style: *back_style,
                },
                _ => return Err("candidate fixture policy unsupported".into()),
            };
            Ok(NativeFormPackagePolicy {
                identity: control.component_identity.clone(),
                payload,
            })
        })
        .collect()
}

struct Expected {
    map: NativeFormPackageMap,
    policy: Vec<NativeFormPackagePolicy>,
    readback: NativeFormPackageReadback,
    state_sha256: String,
    raw: Vec<u8>,
}
fn expected(root: &Path, row: &Value, index: usize, candidate: bool) -> Result<Expected, AnyError> {
    let map = mapping(if index < 2 { 2 } else { 1 })?;
    if row["case_id"] != format!("P09-35-C{:02}", index + 1)
        || serde_json::to_value(&map)? != row["complete_map"]
    {
        return Err("contract source map".into());
    }
    let name = row["file"].as_str().ok_or("contract source filename")?;
    if candidate && name != format!("p09-51-c{:02}-coupled-native-form.hwpx", index + 1) {
        return Err("contract candidate alias".into());
    }
    if Path::new(name).components().count() != 1 || name.contains(['/', '\\', ':']) {
        return Err("contract source boundary".into());
    }
    let manifest = root.join(if candidate { CANDIDATES } else { ORIGINAL });
    let parent = manifest.parent().ok_or("contract manifest parent")?;
    let raw = checked(
        &parent.join(name),
        row["package_sha256"]
            .as_str()
            .ok_or("contract source sha")?,
    )?;
    if row["package_bytes"] != u64::try_from(raw.len())? {
        return Err("contract source bytes".into());
    }
    let readback = NativeFormPackageReader::read(&raw, &map, NativeFormPackageLimits::default())?;
    let policy = policies(&readback)?;
    if sha(&serde_json::to_vec(&policy)?)
        != row["policy_sha256"].as_str().ok_or("contract policy sha")?
    {
        return Err("contract original caller policy".into());
    }
    let state = readback.bind_policies(&policy, domain()?)?;
    readback.verify_domain_state(&state, &policy, domain()?)?;
    let state_sha256 = state.canonical_sha256(domain()?)?;
    if state_sha256
        != row["target_state_sha256"]
            .as_str()
            .ok_or("contract state sha")?
    {
        return Err("contract expected complete state".into());
    }
    Ok(Expected {
        map,
        policy,
        readback,
        state_sha256,
        raw,
    })
}
fn expanded(raw: &[u8]) -> Result<BTreeMap<String, String>, AnyError> {
    let mut zip = BoundedZipReader::open(Cursor::new(raw), PackageLimits::default())?;
    let names: Vec<_> = zip
        .entries()
        .iter()
        .map(|entry| entry.path.as_str().to_owned())
        .collect();
    if names.is_empty() || names.len() > 512 {
        return Err("contract part inventory bound".into());
    }
    let mut parts = BTreeMap::new();
    for (index, name) in names.into_iter().enumerate() {
        let hash = sha(&zip.read_entry(index)?);
        if parts.insert(name, hash).is_some() {
            return Err("contract duplicate part".into());
        }
    }
    Ok(parts)
}
fn part_comparison(
    expected: &BTreeMap<String, String>,
    observed: &BTreeMap<String, String>,
) -> Value {
    let names: BTreeSet<_> = expected.keys().chain(observed.keys()).collect();
    let mut changed = 0;
    let mut added = 0;
    let mut removed = 0;
    for name in names {
        match (expected.get(name), observed.get(name)) {
            (Some(a), Some(b)) if a != b => changed += 1,
            (None, Some(_)) => added += 1,
            (Some(_), None) => removed += 1,
            _ => {}
        }
    }
    json!({"state":if expected == observed {"exact"} else {"changed"},
        "expected_parts":expected.len(),"observed_parts":observed.len(),
        "changed_parts":changed,"added_parts":added,"removed_parts":removed,
        "all_expanded_part_bytes_checked":true,"xml_or_document_metadata_normalized":false,
        "entry_names_or_raw_values_present":false})
}
fn controls(value: &NativeFormPackageReadback) -> Result<Value, AnyError> {
    let controls: Vec<_> = value
        .sections()
        .flat_map(NativeFormHwpxReadback::controls)
        .collect();
    Ok(serde_json::to_value(controls)?)
}
fn analyze(raw: &[u8], expected: &Expected) -> Result<Value, AnyError> {
    let parts = match expanded(raw) {
        Ok(value) => part_comparison(&expanded(&expected.raw)?, &value),
        Err(_) => json!({"state":"rejected","error_code":"P09_SAVED_PACKAGE_ZIP_REJECTED"}),
    };
    let mut result = json!({"state":"rejected","package_sha256":sha(raw),"package_bytes":raw.len(),
        "expanded_parts":parts,"public_package_reader":"not_run","complete_policy_binding":"not_run",
        "complete_state_exact":null,"observed_state_sha256":null,"complete_controls_exact":null,
        "full_package_bindings_exact":null,"document_flow_exact":null,"reference_overlay_exact":null,
        "expected_state_sha256":expected.state_sha256,
        "native_identity_or_setter_or_rollback_qualified":false,
        "render_or_differential_or_product_or_p09_gate_qualified":false});
    let observed =
        match NativeFormPackageReader::read(raw, &expected.map, NativeFormPackageLimits::default())
        {
            Ok(value) => value,
            Err(error) => {
                result["public_package_reader"] = json!("fail");
                result["reader_error_code"] = json!(error.to_string());
                return Ok(result);
            }
        };
    result["public_package_reader"] = json!("pass");
    result["complete_controls_exact"] =
        json!(controls(&observed)? == controls(&expected.readback)?);
    result["full_package_bindings_exact"] =
        json!(observed.bindings() == expected.readback.bindings());
    result["document_flow_exact"] =
        json!(observed.document_flow_sha256() == expected.readback.document_flow_sha256());
    result["reference_overlay_exact"] =
        json!(observed.reference_overlay_status() == expected.readback.reference_overlay_status());
    match observed.bind_policies(&expected.policy, domain()?) {
        Ok(state) => {
            observed.verify_domain_state(&state, &expected.policy, domain()?)?;
            let hash = state.canonical_sha256(domain()?)?;
            result["complete_policy_binding"] = json!("pass");
            result["complete_state_exact"] = json!(hash == expected.state_sha256);
            result["observed_state_sha256"] = json!(hash);
        }
        Err(error) => {
            result["complete_policy_binding"] = json!("fail");
            result["policy_error_code"] = json!(error.to_string());
            result["complete_state_exact"] = json!(false);
        }
    }
    let exact = [
        "complete_state_exact",
        "complete_controls_exact",
        "full_package_bindings_exact",
        "document_flow_exact",
        "reference_overlay_exact",
    ]
    .iter()
    .all(|key| result[*key] == true)
        && result["expanded_parts"]["state"] == "exact";
    result["state"] = json!(if exact {
        "exact_package_contract_not_native_acceptance"
    } else {
        "rejected"
    });
    Ok(result)
}
fn source_rows(root: &Path, candidate: bool) -> Result<Vec<Value>, AnyError> {
    let (name, hash) = if candidate {
        (CANDIDATES, CANDIDATES_SHA)
    } else {
        (ORIGINAL, ORIGINAL_SHA)
    };
    let value: Value = serde_json::from_slice(&checked(&root.join(name), hash)?)?;
    let rows = value["cases"]
        .as_array()
        .ok_or("contract source rows")?
        .clone();
    if rows.len() != 15 {
        return Err("contract complete fifteen required".into());
    }
    Ok(rows)
}
fn old_evidence(root: &Path) -> Result<BTreeMap<String, String>, AnyError> {
    let recovery: Value = serde_json::from_slice(&checked(&root.join(RECOVERY), RECOVERY_SHA)?)?;
    let pins = recovery["native_evidence_sha256"]
        .as_object()
        .ok_or("contract native pins")?;
    if pins.len() != 75 {
        return Err("contract native inventory".into());
    }
    let mut inventory = BTreeMap::new();
    for (relative, hash) in pins {
        let parts: Vec<_> = relative.split(['/', '\\']).collect();
        if parts.len() != 6
            || parts[..4] != ["implementation", "p09", "evidence", "private"]
            || ![
                "saved.hwpx",
                "reopened.hwpx",
                "saved.pdf",
                "reopened.pdf",
                "target-trace.json",
            ]
            .contains(&parts[5])
            || !(1..=15).any(|i| {
                parts[4]
                    == format!(
                        "p09-17-field-auto-number-target-p09-35-20261003-r05-c{i:02}-attempt01"
                    )
            })
        {
            return Err("contract native boundary".into());
        }
        let digest = hash.as_str().ok_or("contract native hash")?;
        checked(
            &root.join(parts.iter().collect::<std::path::PathBuf>()),
            digest,
        )?;
        inventory.insert(relative.clone(), digest.to_owned());
    }
    Ok(inventory)
}
fn self_check(root: &Path) -> Result<Value, AnyError> {
    let rows = source_rows(root, true)?;
    let mut cases = Vec::new();
    for (index, row) in rows.iter().enumerate() {
        let input = expected(root, row, index, true)?;
        let result = analyze(&input.raw, &input)?;
        if result["state"] != "exact_package_contract_not_native_acceptance" {
            return Err("contract positive complete package rejected".into());
        }
        cases.push(json!({"case_id":row["case_id"],"source_self_contract":result}));
    }
    source_rows(root, true)?;
    Ok(
        json!({"schema_version":"hwpx-agent.p09-53-saved-package-contract-source/v1",
        "scope":"all_fifteen_actual_sdk_candidates_positive_source_contract_not_native",
        "state":"pass","cases":cases,"manifest_sha256":CANDIDATES_SHA,
        "native_session_started":false,"native_acceptance_qualified":false,
        "raw_document_values_or_private_paths_present":false,"green_rows":0,"p09_complete":false}),
    )
}
fn historical(root: &Path) -> Result<Value, AnyError> {
    let before = old_evidence(root)?;
    let rows = source_rows(root, false)?;
    let mut cases = Vec::new();
    for (index, row) in rows.iter().enumerate() {
        let input = expected(root, row, index, false)?;
        let directory = root
            .join("implementation/p09/evidence/private")
            .join(format!(
                "p09-17-field-auto-number-target-p09-35-20261003-r05-c{:02}-attempt01",
                index + 1
            ));
        let mut record =
            json!({"case_id":row["case_id"],"actual_original_input_sha256":sha(&input.raw)});
        for stage in ["saved", "reopened"] {
            let raw = bytes(&directory.join(format!("{stage}.hwpx")))?;
            record[stage] = analyze(&raw, &input)?;
        }
        cases.push(record);
    }
    if before != old_evidence(root)? {
        return Err("contract historical evidence changed".into());
    }
    source_rows(root, false)?;
    Ok(
        json!({"schema_version":"hwpx-agent.p09-53-saved-package-contract-historical/v1",
        "state":"pass","scope":"complete_historical_fifteen_case_thirty_saved_stages_failure_oracle",
        "cases":cases,"original_manifest_sha256":ORIGINAL_SHA,"recovery_sha256":RECOVERY_SHA,
        "all_seventy_five_original_native_files_unchanged":true,"native_session_started":false,
        "new_native_repair_or_p52_current_batch_qualified":false,"raw_document_values_or_private_paths_present":false,
        "render_or_differential_or_product_qualified":false,"green_rows":0,"p09_complete":false}),
    )
}
fn current_not_run(root: &Path) -> Result<Value, AnyError> {
    if root.join(DISPATCH).exists() {
        return Err("contract current batch requires actual Python trace binding".into());
    }
    Ok(
        json!({"state":"not_run","scope":"p52_current_native_saved_package_contract",
        "reason":"no_actual_p52_dispatch_receipt","actual_current_cases":0,
        "native_session_started":false,"green_rows":0,"p09_complete":false}),
    )
}
fn current_inventory(root: &Path, dispatch: &Value) -> Result<BTreeMap<String, String>, AnyError> {
    checked(&root.join(ADMISSION), ADMISSION_SHA)?;
    if dispatch["schema_version"] != "hwpx-agent.p09-52-native-form-binding-dispatch/v1"
        || dispatch["state"] != "all_fifteen_actual_attempts_terminal_non_green"
        || dispatch["prefix"] != "p09-52-20261003-r01"
        || dispatch["admission_sha256"] != ADMISSION_SHA
        || dispatch["claims"]["green_rows"] != 0
        || dispatch["claims"]["p09_complete"] != false
    {
        return Err("contract current dispatcher binding".into());
    }
    let pins = dispatch["native_evidence_sha256"]
        .as_object()
        .ok_or("contract current pins")?;
    if !(15..=75).contains(&pins.len()) {
        return Err("contract current inventory bound".into());
    }
    let mut result = BTreeMap::new();
    for (relative, hash) in pins {
        let parts: Vec<_> = relative.split('/').collect();
        if parts.len() != 6
            || parts[..4] != ["implementation", "p09", "evidence", "private"]
            || ![
                "saved.hwpx",
                "reopened.hwpx",
                "saved.pdf",
                "reopened.pdf",
                "target-trace.json",
            ]
            .contains(&parts[5])
            || !(1..=15).any(|i| {
                parts[4]
                    == format!(
                        "p09-17-field-auto-number-target-p09-52-20261003-r01-c{i:02}-attempt01"
                    )
            })
        {
            return Err("contract current native boundary".into());
        }
        let digest = hash.as_str().ok_or("contract current digest")?;
        checked(&root.join(relative), digest)?;
        result.insert(relative.clone(), digest.to_owned());
    }
    Ok(result)
}
fn current_stage(
    root: &Path,
    directory: &Path,
    stage: &str,
    trace: &Value,
    input: &Expected,
    pins: &BTreeMap<String, String>,
) -> Result<Value, AnyError> {
    let (claim, prefix) = if stage == "saved" {
        ("first_save", "output")
    } else {
        ("fresh_reopen_save", "reopened")
    };
    if trace[claim] == "not_run" {
        return Ok(
            json!({"state":"not_run","reason":"actual_native_stage_not_saved",
            "native_package_semantics_or_render_or_product_qualified":false}),
        );
    }
    if trace[claim] != "pass" {
        return Err("contract current stage claim".into());
    }
    let path = directory.join(format!("{stage}.hwpx"));
    let relative = path
        .strip_prefix(root)?
        .to_string_lossy()
        .replace('\\', "/");
    let hash = trace[format!("{prefix}_sha256")]
        .as_str()
        .ok_or("contract current stage hash")?;
    if pins.get(&relative).map(String::as_str) != Some(hash) {
        return Err("contract current artifact pin".into());
    }
    let raw = checked(&path, hash)?;
    if trace[format!("{prefix}_bytes")] != u64::try_from(raw.len())? {
        return Err("contract current artifact bytes".into());
    }
    analyze(&raw, input)
}
fn current(root: &Path) -> Result<Value, AnyError> {
    if !root.join(DISPATCH).exists() {
        return current_not_run(root);
    }
    let raw = bytes(&root.join(DISPATCH))?;
    let dispatch: Value = serde_json::from_slice(&raw)?;
    let before = current_inventory(root, &dispatch)?;
    let records = dispatch["cases"]
        .as_array()
        .ok_or("contract current cases")?;
    let rows = source_rows(root, true)?;
    if records.len() != 15 {
        return Err("contract current complete fifteen".into());
    }
    let mut cases = Vec::new();
    for (index, (row, record)) in rows.iter().zip(records).enumerate() {
        if row["case_id"] != record["case_id"] {
            return Err("contract current case order".into());
        }
        let input = expected(root, row, index, true)?;
        let directory = root
            .join("implementation/p09/evidence/private")
            .join(format!(
                "p09-17-field-auto-number-target-p09-52-20261003-r01-c{:02}-attempt01",
                index + 1
            ));
        let trace_path = directory.join("target-trace.json");
        let relative = trace_path
            .strip_prefix(root)?
            .to_string_lossy()
            .replace('\\', "/");
        let trace: Value = serde_json::from_slice(&checked(
            &trace_path,
            before.get(&relative).ok_or("contract current trace pin")?,
        )?)?;
        if trace["input_sha256"] != row["package_sha256"]
            || trace["native_form_plan_sha256"] != row["plan_sha256"]
            || trace["remaining_hwp_process_count"] != 0
            || trace["native_semantics_render_or_p09_gate_qualified"] != false
        {
            return Err("contract current trace source".into());
        }
        let mut record =
            json!({"case_id":row["case_id"],"actual_candidate_input_sha256":sha(&input.raw)});
        for stage in ["saved", "reopened"] {
            record[stage] = current_stage(root, &directory, stage, &trace, &input, &before)?;
        }
        cases.push(record);
    }
    if before != current_inventory(root, &dispatch)? || bytes(&root.join(DISPATCH))? != raw {
        return Err("contract current evidence changed".into());
    }
    source_rows(root, true)?;
    Ok(
        json!({"schema_version":"hwpx-agent.p09-53-saved-package-contract-current/v1",
        "state":"pass","scope":"actual_current_fifteen_bound_saved_package_checks_not_render_or_product",
        "cases":cases,"actual_dispatch_sha256":sha(&raw),"candidate_manifest_sha256":CANDIDATES_SHA,
        "native_session_started":false,"raw_document_values_or_private_paths_present":false,
        "native_identity_or_setter_or_rollback_qualified":false,"render_or_differential_or_product_qualified":false,
        "green_rows":0,"p09_complete":false}),
    )
}
fn run() -> Result<(), AnyError> {
    let root = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()?;
    let args: Vec<_> = std::env::args_os().skip(1).collect();
    let result = match args.as_slice() {
        [mode] if mode == "--source-self-check" => self_check(&root)?,
        [mode] if mode == "--historical" => historical(&root)?,
        [mode] if mode == "--current-status" => current_not_run(&root)?,
        [mode] if mode == "--current" => current(&root)?,
        _ => return Err("contract fixed mode required".into()),
    };
    println!("{result}");
    Ok(())
}
fn main() {
    if run().is_err() {
        eprintln!("P09_SAVED_PACKAGE_CONTRACT_FAILED");
        std::process::exit(2);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write as _;
    fn rewrite(raw: &[u8], edited: Option<(&str, Vec<u8>)>) -> Result<Vec<u8>, AnyError> {
        let mut archive = BoundedZipReader::open(Cursor::new(raw), PackageLimits::default())?;
        let mut contents = BTreeMap::new();
        for index in 0..archive.entries().len() {
            let name = archive.entries()[index].path.as_str().to_owned();
            contents.insert(name, archive.read_entry(index)?);
        }
        if let Some((name, value)) = edited {
            contents.insert(name.to_owned(), value);
        }
        let mut writer = zip::ZipWriter::new(Cursor::new(Vec::new()));
        let mime = contents.remove("mimetype").ok_or("test mimetype")?;
        writer.start_file(
            "mimetype",
            zip::write::SimpleFileOptions::default()
                .compression_method(zip::CompressionMethod::Stored),
        )?;
        writer.write_all(&mime)?;
        for (name, value) in contents {
            writer.start_file(
                name,
                zip::write::SimpleFileOptions::default()
                    .compression_method(zip::CompressionMethod::Stored),
            )?;
            writer.write_all(&value)?;
        }
        Ok(writer.finish()?.into_inner())
    }
    fn root() -> Result<std::path::PathBuf, AnyError> {
        Ok(Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("../..")
            .canonicalize()?)
    }
    #[test]
    fn all_fifteen_complete_sdk_outputs_pass_only_source_contract() -> Result<(), AnyError> {
        let value = self_check(&root()?)?;
        assert_eq!(value["cases"].as_array().ok_or("cases")?.len(), 15);
        assert_eq!(value["native_acceptance_qualified"], false);
        assert_eq!(value["green_rows"], 0);
        Ok(())
    }
    #[test]
    fn all_thirty_original_native_outputs_retain_full_package_failures() -> Result<(), AnyError> {
        let value = historical(&root()?)?;
        for row in value["cases"].as_array().ok_or("cases")? {
            for stage in ["saved", "reopened"] {
                assert_eq!(row[stage]["state"], "rejected");
                assert_ne!(row[stage]["expanded_parts"]["state"], "exact");
                assert_eq!(
                    row[stage]["render_or_differential_or_product_or_p09_gate_qualified"],
                    false
                );
            }
        }
        Ok(())
    }
    #[test]
    fn unmanaged_parts_inventory_content_and_names_cannot_be_discarded() {
        let source = BTreeMap::from([
            ("Contents/header.xml".into(), "a".into()),
            ("private-part-name".into(), "b".into()),
        ]);
        for target in [
            BTreeMap::from([
                ("Contents/header.xml".into(), "changed".into()),
                ("private-part-name".into(), "b".into()),
            ]),
            BTreeMap::from([("Contents/header.xml".into(), "a".into())]),
            BTreeMap::from([
                ("Contents/header.xml".into(), "a".into()),
                ("private-part-name".into(), "b".into()),
                ("extra".into(), "x".into()),
            ]),
        ] {
            let result = part_comparison(&source, &target);
            assert_eq!(result["state"], "changed");
            assert_eq!(result["xml_or_document_metadata_normalized"], false);
            let text = result.to_string();
            assert!(!text.contains("private-part-name"));
            assert!(!text.contains("Contents/header.xml"));
        }
    }
    #[test]
    fn invalid_archive_fails_closed_without_raw_exception_or_native_claims() -> Result<(), AnyError>
    {
        let root = root()?;
        let rows = source_rows(&root, true)?;
        let source = expected(&root, &rows[0], 0, true)?;
        let result = analyze(b"not-an-archive-private-value", &source)?;
        assert_eq!(result["state"], "rejected");
        assert_eq!(result["expanded_parts"]["state"], "rejected");
        assert_eq!(result["public_package_reader"], "fail");
        assert!(!result.to_string().contains("not-an-archive-private-value"));
        Ok(())
    }
    #[test]
    fn current_dispatch_absence_is_not_run_not_success() -> Result<(), AnyError> {
        let result = current_not_run(&root()?)?;
        assert_eq!(current(&root()?)?, result);
        assert_eq!(result["state"], "not_run");
        assert_eq!(result["actual_current_cases"], 0);
        assert_eq!(result["p09_complete"], false);
        Ok(())
    }
    #[test]
    fn actual_candidate_managed_name_change_rejects_without_replacing_expectation()
    -> Result<(), AnyError> {
        let root = root()?;
        let rows = source_rows(&root, true)?;
        let source = expected(&root, &rows[4], 4, true)?;
        let control = source
            .readback
            .sections()
            .flat_map(NativeFormHwpxReadback::controls)
            .next()
            .ok_or("test control")?;
        let name = format!("name=\"{}\"", control.common.name);
        let mut zip = BoundedZipReader::open(Cursor::new(&source.raw), PackageLimits::default())?;
        let index = zip
            .entries()
            .iter()
            .position(|e| e.path.as_str() == "Contents/section0.xml")
            .ok_or("test section")?;
        let original = String::from_utf8(zip.read_entry(index)?)?;
        assert_eq!(original.matches(&name).count(), 1);
        let edited = original
            .replacen(&name, "name=\"changed-unit-fixture-name\"", 1)
            .into_bytes();
        let raw = rewrite(&source.raw, Some(("Contents/section0.xml", edited)))?;
        let result = analyze(&raw, &source)?;
        assert_eq!(result["public_package_reader"], "pass");
        assert_eq!(result["state"], "rejected");
        assert_eq!(result["complete_controls_exact"], false);
        assert_eq!(result["expanded_parts"]["changed_parts"], 1);
        assert!(!result.to_string().contains("changed-unit-fixture-name"));
        Ok(())
    }
    #[test]
    fn actual_unmanaged_header_bytes_change_cannot_be_normalized_away() -> Result<(), AnyError> {
        let root = root()?;
        let rows = source_rows(&root, true)?;
        let source = expected(&root, &rows[0], 0, true)?;
        let mut zip = BoundedZipReader::open(Cursor::new(&source.raw), PackageLimits::default())?;
        let index = zip
            .entries()
            .iter()
            .position(|e| e.path.as_str() == "Contents/header.xml")
            .ok_or("test header")?;
        let mut edited = zip.read_entry(index)?;
        edited.extend_from_slice(b"\n ");
        let raw = rewrite(&source.raw, Some(("Contents/header.xml", edited)))?;
        let result = analyze(&raw, &source)?;
        assert_eq!(result["public_package_reader"], "pass");
        assert_eq!(result["state"], "rejected");
        assert_eq!(result["complete_controls_exact"], true);
        assert_eq!(result["expanded_parts"]["changed_parts"], 1);
        assert_eq!(
            result["expanded_parts"]["xml_or_document_metadata_normalized"],
            false
        );
        Ok(())
    }
    #[test]
    fn archive_recompression_is_not_document_mutation_or_native_acceptance() -> Result<(), AnyError>
    {
        let root = root()?;
        let rows = source_rows(&root, true)?;
        let source = expected(&root, &rows[0], 0, true)?;
        let raw = rewrite(&source.raw, None)?;
        assert_ne!(sha(&raw), sha(&source.raw));
        let result = analyze(&raw, &source)?;
        assert_eq!(
            result["state"],
            "exact_package_contract_not_native_acceptance"
        );
        assert_eq!(result["expanded_parts"]["state"], "exact");
        assert_eq!(
            result["render_or_differential_or_product_or_p09_gate_qualified"],
            false
        );
        Ok(())
    }
}
