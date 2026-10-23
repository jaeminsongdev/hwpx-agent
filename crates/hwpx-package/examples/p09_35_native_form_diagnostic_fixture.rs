//! Complete changed diagnostics via qualified public APIs; never launches Hancom.
use domain_ir::{
    FORM_CONTROL_SCHEMA_VERSION, FormControlBuilder, FormControlIdentity, FormControlLimitConfig,
    FormControlLimits, FormControlOperation, FormControlPayload, FormControlRequest,
    FormControlRequestDraft, FormTextValidation, LogicalId,
};
use hwpx_agent_foundation::workdir::SecureWorkspace;
use hwpx_package::{
    BoundedZipReader, CharacterStyleCatalogReader, CharacterStyleLimits, Color, NativeFormHwpxMap,
    NativeFormHwpxReadback, NativeFormObservedIdentity, NativeFormObservedPayload,
    NativeFormPackageLimits, NativeFormPackageLowerer, NativeFormPackageMap,
    NativeFormPackageOutputLimits, NativeFormPackageOutputPlan, NativeFormPackagePolicy,
    NativeFormPackageReadback, NativeFormPackageReader, NativeFormPackageSectionMap,
    NativeRootManifestLimits, NativeRootManifestPlan, NativeRootManifestPreparer, PackageLimits,
};
use sha2::{Digest as _, Sha256};
use std::{
    env,
    error::Error,
    fs,
    io::{Cursor, Read as _},
    path::{Path, PathBuf},
};

type AnyError = Box<dyn Error>;
const CAPTURE: &str = "implementation/p08/evidence/private/p08-20-object-target-20260915-18/obj-012-form-insert.hancom-2020-readback.hwpx";
const CAPTURE_SHA: &str = "02e9b5acef95877b6934a6a3131069402138cc2190eff2e68db79aa7e9ac9ce7";
const PREVIOUS: &str = "fixtures/target-build/p09-32-native-form-target-20261002-01/output";
const MANIFEST_SHA: &str = "f07a8a73dbead998db253050d011ebe58ac331c42060b31c0c7a617a23ad8ef8";
const INPUTS: [(&str, &str); 2] = [
    (
        "p09-32-c05-global-tab.hwpx",
        "98f6c41d1ca3a10da2d8754ad2d73e71acb3d1a28e33ac0f573a8f654301aacc",
    ),
    (
        "p09-32-c06-cross-section-radio-tab.hwpx",
        "2525a8da465b257a9171a46a7d95a7a5d2ba6da68ac1449764e208b374fe06e9",
    ),
];
const CASES: [&str; 15] = [
    "root-two-section-text",
    "root-two-section-radio",
    "red-foreground-only",
    "blue-foreground-only",
    "blue-existing-style",
    "blue-existing-style-noneditable",
    "red-existing-blue-style",
    "noneditable-only",
    "unicode-name-only",
    "ampersand-name-only",
    "less-than-name-only",
    "greater-than-name-only",
    "double-quote-name-only",
    "apostrophe-name-only",
    "metachar-group-only",
];
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
            return Err("linked artifact refused".into());
        }
    }
    let metadata = fs::metadata(path)?;
    if !metadata.is_file() || metadata.len() == 0 || metadata.len() > 4 * 1024 * 1024 {
        return Err("artifact bound".into());
    }
    let mut value = Vec::new();
    fs::File::open(path)?
        .take(4 * 1024 * 1024 + 1)
        .read_to_end(&mut value)?;
    if value.len() as u64 != metadata.len() {
        return Err("artifact changed during read".into());
    }
    Ok(value)
}
fn checked(root: &Path, relative: &str, digest: &str) -> Result<Vec<u8>, AnyError> {
    let value = bytes(&root.join(relative))?;
    if sha(&value) != digest {
        return Err("source identity changed".into());
    }
    Ok(value)
}
fn map(count: usize) -> Result<NativeFormPackageMap, AnyError> {
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
                            native_object_id: 90001 + u32::try_from(i)?,
                        }],
                    },
                })
            })
            .collect::<Result<_, AnyError>>()?,
    })
}
fn limits() -> Result<FormControlLimits, AnyError> {
    Ok(FormControlLimits::new(FormControlLimitConfig::default())?)
}
fn read(raw: &[u8], map: &NativeFormPackageMap) -> Result<NativeFormPackageReadback, AnyError> {
    Ok(NativeFormPackageReader::read(
        raw,
        map,
        NativeFormPackageLimits::default(),
    )?)
}
// Caller-declared fixture policies, not defaults/validation inferred from native XML.
fn policies(
    observed: &NativeFormPackageReadback,
) -> Result<Vec<NativeFormPackagePolicy>, AnyError> {
    observed
        .sections()
        .flat_map(NativeFormHwpxReadback::controls)
        .map(|c| {
            let payload = match &c.payload {
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
                    radio_group_name: radio_group_name.clone().ok_or("radio group missing")?,
                    group_required: true,
                    tri_state: *tri_state,
                    back_style: *back_style,
                },
                _ => return Err("diagnostic captured payload unsupported".into()),
            };
            Ok(NativeFormPackagePolicy {
                identity: c.component_identity.clone(),
                payload,
            })
        })
        .collect()
}
fn controls_sha(
    observed: &NativeFormPackageReadback,
    policies: &[NativeFormPackagePolicy],
) -> Result<Vec<String>, AnyError> {
    observed
        .bind_policies(policies, limits()?)?
        .controls()
        .iter()
        .map(|c| Ok(sha(&serde_json::to_vec(c)?)))
        .collect()
}
fn style_admission(raw: &[u8]) -> Result<(), AnyError> {
    let mut package = BoundedZipReader::open(Cursor::new(raw), PackageLimits::default())?;
    let index = package
        .entries()
        .iter()
        .position(|entry| entry.path.as_str() == "Contents/header.xml")
        .ok_or("header missing")?;
    let header = package.read_entry(index)?;
    let catalog = CharacterStyleCatalogReader::read(&header, CharacterStyleLimits::default())?;
    for (id, expected) in [(0, Color::Rgb(0, 0, 0)), (5, Color::Rgb(0x2E, 0x74, 0xB5))] {
        if catalog
            .styles
            .iter()
            .filter(|s| s.id == id && s.text_color == expected)
            .count()
            != 1
        {
            return Err("real existing character style admission changed".into());
        }
    }
    Ok(())
}
fn property(
    index: usize,
    observed: &NativeFormPackageReadback,
    policies: &[NativeFormPackagePolicy],
) -> Result<FormControlOperation, AnyError> {
    let state = observed.bind_policies(policies, limits()?)?;
    let control = state.controls().first().ok_or("captured control missing")?;
    let mut common = control.common.clone();
    match index {
        2 => common.fore_color_rgb = 0x00CC_1100,
        3 => common.fore_color_rgb = 0x002E_74B5,
        4..=6 => {
            common.fore_color_rgb = if index == 6 { 0x00CC_1100 } else { 0x002E_74B5 };
            common.character.char_pr_id_ref = 5;
            if index == 5 {
                common.editable = false;
            }
        }
        7 => common.editable = false,
        8 => common.name = "P09 이름 한글".into(),
        9 => common.name = "P09 이름 & 폼".into(),
        10 => common.name = "P09 이름 < 폼".into(),
        11 => common.name = "P09 이름 > 폼".into(),
        12 => common.name = "P09 이름 \" 폼".into(),
        13 => common.name = "P09 이름 ' 폼".into(),
        14 => common.group_name = Some("P09 그룹 & <\"'>".into()),
        _ => return Err("diagnostic index invalid".into()),
    }
    Ok(FormControlOperation::ReplaceProperties {
        target: control.identity.clone(),
        common,
        payload: control.payload.clone(),
    })
}
struct Built {
    source: Vec<u8>,
    pre_root: Vec<u8>,
    output: Vec<u8>,
    map: NativeFormPackageMap,
    policies: Vec<NativeFormPackagePolicy>,
    record: serde_json::Value,
}
fn property_candidate(
    index: usize,
    source: &[u8],
    mapping: &NativeFormPackageMap,
    policy: &[NativeFormPackagePolicy],
    observed: &NativeFormPackageReadback,
) -> Result<(Vec<u8>, serde_json::Value), AnyError> {
    if index < 2 {
        return Ok((source.to_vec(), serde_json::Value::Null));
    }
    let state = observed.bind_policies(policy, limits()?)?;
    let flow = observed.document_flow_sha256();
    let request = FormControlRequest::from_draft(
        FormControlRequestDraft {
            schema_version: FORM_CONTROL_SCHEMA_VERSION.into(),
            request_id: LogicalId::parse(format!("diagnostic-{}", index + 1))?,
            expected_source_state_sha256: state.canonical_sha256(limits()?)?,
            expected_document_flow_sha256: flow.into(),
            target_document_flow_sha256: flow.into(),
            operation: property(index, observed, policy)?,
        },
        &state,
        flow,
        limits()?,
    )?;
    let domain = FormControlBuilder::plan(&state, &request, flow, limits()?)?;
    let plan = NativeFormPackageOutputPlan::bind(
        source,
        mapping,
        policy,
        &domain,
        limits()?,
        NativeFormPackageLimits::default(),
    )?;
    let output = NativeFormPackageLowerer::lower(
        source,
        &plan,
        limits()?,
        NativeFormPackageLimits::default(),
        NativeFormPackageOutputLimits::default(),
    )?;
    let retry = NativeFormPackageLowerer::lower(
        source,
        &plan,
        limits()?,
        NativeFormPackageLimits::default(),
        NativeFormPackageOutputLimits::default(),
    )?;
    let external = NativeFormPackageLowerer::verify_output(
        source,
        &plan,
        output.bytes(),
        limits()?,
        NativeFormPackageLimits::default(),
        NativeFormPackageOutputLimits::default(),
    )?;
    if output.bytes() != retry.bytes()
        || output.receipt() != retry.receipt()
        || output.receipt() != &external
        || read(output.bytes(), mapping)?.bind_policies(policy, limits()?)?
            != *domain.target_state()
    {
        return Err("complete property plan retry or target state drift".into());
    }
    let mut changed_source = source.to_vec();
    changed_source.push(0);
    if NativeFormPackageLowerer::lower(
        &changed_source,
        &plan,
        limits()?,
        NativeFormPackageLimits::default(),
        NativeFormPackageOutputLimits::default(),
    )
    .is_ok()
    {
        return Err("changed_source property source admitted".into());
    }
    Ok((
        output.bytes().to_vec(),
        serde_json::to_value(output.receipt())?,
    ))
}
fn root_candidate(pre_root: &[u8]) -> Result<hwpx_package::NativeRootManifestOutput, AnyError> {
    let plan = NativeRootManifestPlan::bind(pre_root, NativeRootManifestLimits::default())?;
    let output =
        NativeRootManifestPreparer::prepare(pre_root, &plan, NativeRootManifestLimits::default())?;
    let retry =
        NativeRootManifestPreparer::prepare(pre_root, &plan, NativeRootManifestLimits::default())?;
    let external = NativeRootManifestPreparer::verify_output(
        pre_root,
        &plan,
        output.bytes(),
        NativeRootManifestLimits::default(),
    )?;
    if output.bytes() != retry.bytes()
        || output.receipt() != retry.receipt()
        || output.receipt() != &external
    {
        return Err("root plan retry or external drift".into());
    }
    let mut changed_source = pre_root.to_vec();
    changed_source.push(0);
    if NativeRootManifestPreparer::prepare(
        &changed_source,
        &plan,
        NativeRootManifestLimits::default(),
    )
    .is_ok()
    {
        return Err("changed_source root source admitted".into());
    }
    Ok(output)
}
fn build(root: &Path) -> Result<Vec<Built>, AnyError> {
    let capture = checked(root, CAPTURE, CAPTURE_SHA)?;
    style_admission(&capture)?;
    let manifest: serde_json::Value = serde_json::from_slice(&checked(
        root,
        &format!("{PREVIOUS}/fixture-manifest.json"),
        MANIFEST_SHA,
    )?)?;
    let mut cases = Vec::new();
    for (index, label) in CASES.iter().enumerate() {
        let source = if index < 2 {
            checked(
                root,
                &format!("{PREVIOUS}/{}", INPUTS[index].0),
                INPUTS[index].1,
            )?
        } else {
            capture.clone()
        };
        let count = if index < 2 { 2 } else { 1 };
        let mapping = map(count)?;
        let observed = read(&source, &mapping)?;
        let policy = policies(&observed)?;
        if index < 2 {
            let previous = &manifest["cases"][index + 4];
            if serde_json::to_value(&mapping)? != previous["complete_map"]
                || serde_json::to_value(controls_sha(&observed, &policy)?)?
                    != previous["target_controls_sha256"]
                || sha(&serde_json::to_vec(&policy)?)
                    != previous["policy_sha256"]
                        .as_str()
                        .ok_or("previous policy digest missing")?
            {
                return Err("previous complete input intent changed".into());
            }
        }
        let (pre_root, property_receipt) =
            property_candidate(index, &source, &mapping, &policy, &observed)?;
        let before_root = read(&pre_root, &mapping)?;
        let output = root_candidate(&pre_root)?;
        let final_read = read(output.bytes(), &mapping)?;
        if before_root.document_flow_sha256() != final_read.document_flow_sha256()
            || controls_sha(&before_root, &policy)? != controls_sha(&final_read, &policy)?
        {
            return Err("root transition changed control intent or flow".into());
        }
        if final_read
            .sections()
            .flat_map(NativeFormHwpxReadback::controls)
            .any(|c| c.native_identity != NativeFormObservedIdentity::Missing)
        {
            return Err("diagnostic fabricated native identity".into());
        }
        let before_state = before_root
            .bind_policies(&policy, limits()?)?
            .canonical_sha256(limits()?)?;
        let target_state = final_read
            .bind_policies(&policy, limits()?)?
            .canonical_sha256(limits()?)?;
        let record = serde_json::json!({
            "case_id":format!("P09-35-C{:02}",index+1), "file":format!("p09-35-c{:02}-{label}.hwpx",index+1),
            "source_file":format!("p09-35-c{:02}-source.hwpx",index+1), "pre_root_file":format!("p09-35-c{:02}-pre-root.hwpx",index+1),
            "source_kind":if index<2 {"immutable_failed_native_batch_input"} else {"original_native_capture"},
            "source_package_sha256":sha(&source), "pre_root_package_sha256":sha(&pre_root), "package_sha256":sha(output.bytes()), "package_bytes":output.bytes().len(),
            "complete_map":mapping, "controls":count, "policy_sha256":sha(&serde_json::to_vec(&policy)?),
            "pre_root_state_sha256":before_state, "target_state_sha256":target_state, "target_controls_sha256":controls_sha(&final_read,&policy)?,
            "document_flow_sha256":final_read.document_flow_sha256(), "property_receipt":property_receipt, "root_receipt":output.receipt(),
            "packaging_transition_changes_complete_state":before_state!=target_state,
            "root_control_intent_and_flow_preserved":true, "deterministic_retry":true,"stale_source_rejected":true,
        });
        cases.push(Built {
            source,
            pre_root,
            output: output.bytes().to_vec(),
            map: mapping,
            policies: policy,
            record,
        });
    }
    if cases
        .iter()
        .map(|b| sha(&b.output))
        .collect::<std::collections::BTreeSet<_>>()
        .len()
        != CASES.len()
        || sha(&checked(root, CAPTURE, CAPTURE_SHA)?) != CAPTURE_SHA
    {
        return Err("duplicate diagnostic or source changed".into());
    }
    Ok(cases)
}
fn manifest(cases: &[Built]) -> serde_json::Value {
    serde_json::json!({"schema_version":"hwpx-agent.p09-native-form-diagnostic-fixtures/v1", "task":"P09-35",
        "source_capture_sha256":CAPTURE_SHA,"previous_manifest_sha256":MANIFEST_SHA,
        "cases":cases.iter().map(|c|&c.record).collect::<Vec<_>>(),"actual_hangul":false,"render":"not_run","green_rows":0,
        "source_policy":"caller_declared_not_native_inferred", "raw_document_text_present":false,"absolute_private_paths_present":false})
}
fn directory(root: &Path, argument: &std::ffi::OsStr) -> Result<PathBuf, AnyError> {
    let out = PathBuf::from(argument);
    if !out.is_absolute() || out.exists() {
        return Err("exclusive absolute output required".into());
    }
    let parent = out.parent().ok_or("output parent missing")?;
    for ancestor in parent.ancestors() {
        if linked(&fs::symlink_metadata(ancestor)?) {
            return Err("linked output refused".into());
        }
    }
    if parent.canonicalize()? != root.join("fixtures/target-build").canonicalize()? {
        return Err("output boundary refused".into());
    }
    Ok(parent.join(out.file_name().ok_or("output name missing")?))
}
fn publish(root: &Path, argument: &std::ffi::OsStr) -> Result<(), AnyError> {
    let out = directory(root, argument)?;
    let cases = build(root)?;
    let value = serde_json::to_vec_pretty(&manifest(&cases))?;
    if value.len() > 512 * 1024 {
        return Err("manifest bound".into());
    }
    let workspace = SecureWorkspace::create(&out)?;
    for case in &cases {
        for (key, bytes) in [
            ("source_file", case.source.as_slice()),
            ("pre_root_file", case.pre_root.as_slice()),
            ("file", case.output.as_slice()),
        ] {
            let name = Path::new(case.record[key].as_str().ok_or("artifact name missing")?);
            let staged = workspace.stage_bytes(&Path::new("p09-35").join(name), bytes)?;
            workspace.publish(&staged, name)?;
        }
    }
    let staged = workspace.stage_bytes(Path::new("p09-35/fixture-manifest.json"), &value)?;
    workspace.publish(&staged, Path::new("fixture-manifest.json"))?;
    println!(
        "{}",
        serde_json::json!({"state":"pass","cases":cases.len(),"manifest_sha256":sha(&value),"native_session_started":false,"green_rows":0})
    );
    Ok(())
}
fn compare(case: &Built, raw: &[u8]) -> Result<serde_json::Value, AnyError> {
    let expected = read(&case.output, &case.map)?;
    let observed = read(raw, &case.map)?;
    let target = observed
        .bind_policies(&case.policies, limits()?)?
        .canonical_sha256(limits()?)?;
    let control_sha = controls_sha(&observed, &case.policies)?;
    Ok(
        serde_json::json!({"complete_public_reader":"pass","complete_policy_binding":"pass","package_sha256":sha(raw),"package_bytes":raw.len(),
        "target_state_sha256":target,"target_controls_sha256":control_sha,"document_flow_sha256":observed.document_flow_sha256(),
        "complete_target_state_exact":serde_json::Value::String(target)==case.record["target_state_sha256"],
        "target_control_fingerprints_exact":serde_json::to_value(control_sha)?==case.record["target_controls_sha256"],
        "document_flow_exact":observed.document_flow_sha256()==expected.document_flow_sha256(),
        "complete_package_bindings_exact":observed.bindings()==expected.bindings(),"green_rows":0}),
    )
}
fn native_readback(root: &Path, prefix: &std::ffi::OsStr) -> Result<(), AnyError> {
    let prefix = prefix.to_str().ok_or("prefix invalid")?;
    if prefix.is_empty()
        || prefix.len() > 40
        || !prefix
            .bytes()
            .all(|b| b.is_ascii_lowercase() || b.is_ascii_digit() || b == b'-')
    {
        return Err("prefix invalid".into());
    }
    let cases = build(root)?;
    let mut rows = Vec::new();
    for (index, case) in cases.iter().enumerate() {
        let dir = root
            .join("implementation/p09/evidence/private")
            .join(format!(
                "p09-17-field-auto-number-target-{prefix}-c{:02}-attempt01",
                index + 1
            ));
        let mut row = serde_json::json!({"case_id":case.record["case_id"]});
        for stage in ["saved", "reopened"] {
            let path = dir.join(format!("{stage}.hwpx"));
            row[stage] = if path.exists() {
                let raw = bytes(&path)?;
                compare(case,&raw).unwrap_or_else(|_|serde_json::json!({"complete_public_reader_or_policy_binding":"fail","error_code":"complete_readback_failed","package_sha256":sha(&raw),"package_bytes":raw.len(),"green_rows":0}))
            } else {
                serde_json::json!({"complete_public_reader_or_policy_binding":"not_run","error_code":"native_output_missing","green_rows":0})
            };
        }
        rows.push(row);
    }
    println!(
        "{}",
        serde_json::json!({"schema_version":"hwpx-agent.p09-native-form-diagnostic-readback/v1","task":"P09-35","cases":rows,
        "qualification":"file_readback_only_native_trace_binding_required","native_session_started":false,"raw_document_text_present":false,"absolute_private_paths_present":false,"green_rows":0,"p09_complete":false})
    );
    Ok(())
}
fn run() -> Result<(), AnyError> {
    let root = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()?;
    let args: Vec<_> = env::args_os().skip(1).collect();
    match args.as_slice() {
        [flag] if flag == "--oracle-manifest" => {
            println!("{}", manifest(&build(&root)?));
            Ok(())
        }
        [flag, prefix] if flag == "--inspect-native-batch" => native_readback(&root, prefix),
        [output] => publish(&root, output),
        _ => Err("bounded arguments required".into()),
    }
}
fn main() {
    if run().is_err() {
        eprintln!("P09_NATIVE_FORM_DIAGNOSTIC_FIXTURE_FAILED");
        std::process::exit(2);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    fn root() -> Result<PathBuf, AnyError> {
        Ok(Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("../..")
            .canonicalize()?)
    }
    #[test]
    fn all_fifteen_different_complete_cases_retry_verify_and_keep_full_intent()
    -> Result<(), AnyError> {
        let cases = build(&root()?)?;
        assert_eq!(cases.len(), 15);
        for (i, case) in cases.iter().enumerate() {
            assert_eq!(case.record["controls"], if i < 2 { 2 } else { 1 });
            assert_eq!(
                case.record["root_receipt"]["changed_href_attributes"],
                usize::from(i < 2)
            );
            assert_eq!(
                case.record["packaging_transition_changes_complete_state"],
                i < 2
            );
            let result = compare(case, &case.output)?;
            for key in [
                "complete_target_state_exact",
                "target_control_fingerprints_exact",
                "document_flow_exact",
                "complete_package_bindings_exact",
            ] {
                assert_eq!(result[key], true);
            }
        }
        Ok(())
    }
    #[test]
    fn original_as_native_output_cannot_pass_property_or_packaging_intent() -> Result<(), AnyError>
    {
        for case in build(&root()?)? {
            let observed = compare(&case, &case.source)?;
            assert_eq!(observed["complete_target_state_exact"], false);
            if case.record["source_kind"] == "original_native_capture" {
                assert_eq!(observed["target_control_fingerprints_exact"], false);
            }
        }
        Ok(())
    }
    #[test]
    fn public_manifest_contains_hashes_not_document_values_paths_or_native_claims()
    -> Result<(), AnyError> {
        let root = root()?;
        let cases = build(&root)?;
        let value = manifest(&cases);
        let serialized = serde_json::to_string(&value)?;
        assert!(!serialized.contains(&root.to_string_lossy().to_string()));
        for text in ["P08FORMINSERT", "P09 이름", "P09 그룹"] {
            assert!(!serialized.contains(text));
        }
        assert_eq!(value["actual_hangul"], false);
        assert_eq!(value["green_rows"], 0);
        assert_eq!(value["render"], "not_run");
        Ok(())
    }
    #[test]
    fn existing_output_relative_and_outside_boundaries_are_rejected() -> Result<(), AnyError> {
        let root = root()?;
        for path in [
            root.join("fixtures/target-build"),
            root.join("outside-child"),
            PathBuf::from("relative"),
        ] {
            assert!(directory(&root, path.as_os_str()).is_err());
        }
        Ok(())
    }
}
