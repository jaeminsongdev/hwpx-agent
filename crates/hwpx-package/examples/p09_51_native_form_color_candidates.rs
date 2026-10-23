//! Complete 15-case candidates through the actual coupled-color SDK. No native activation.
use domain_ir::{
    FormControlIdentity, FormControlLimitConfig, FormControlLimits, FormControlPayload,
    FormDocumentState, FormTextValidation, LogicalId, NativeFormTag,
};
use hwpx_agent_foundation::workdir::SecureWorkspace;
use hwpx_package::{
    BoundedZipReader, NativeFormHwpxMap, NativeFormHwpxReadback, NativeFormObservedIdentity,
    NativeFormObservedPayload, NativeFormPackageLimits, NativeFormPackageMap,
    NativeFormPackagePolicy, NativeFormPackageReadback, NativeFormPackageReader,
    NativeFormPackageSectionMap, PackageLimits,
    native_form_color::{
        NativeFormColorLimits, NativeFormColorOutput, NativeFormColorPlan, NativeFormColorPreparer,
        NativeFormColorReceipt, NativeFormColorRequest,
    },
};
use serde_json::{Value, json};
use sha2::{Digest as _, Sha256};
use std::{
    env,
    error::Error,
    ffi::OsStr,
    fs,
    io::{Cursor, Read as _},
    path::{Component, Path, PathBuf},
};

type AnyError = Box<dyn Error>;
const ORIGINAL: &str =
    "fixtures/target-build/p09-35-native-form-diagnostics-01/output/fixture-manifest.json";
const ORIGINAL_SHA: &str = "ef1bdad32cf06b07725a17888b7378e9720b2111539675c20178ab850f1d9750";
const DIRECTORY_PREFIX: &str = "p09-51-native-form-candidates-";

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
fn entry(raw: &[u8], path: &str) -> Result<Vec<u8>, AnyError> {
    let mut archive = BoundedZipReader::open(Cursor::new(raw), PackageLimits::default())?;
    let index = archive
        .entries()
        .iter()
        .position(|e| e.path.as_str() == path)
        .ok_or("candidate section missing")?;
    Ok(archive.read_entry(index)?)
}
fn worker_plan(
    case_id: &str,
    raw: &[u8],
    map: &NativeFormPackageMap,
    observed: &NativeFormPackageReadback,
) -> Result<Value, AnyError> {
    if observed.section_count() != map.sections.len() {
        return Err("candidate section inventory".into());
    }
    let mut controls = Vec::new();
    let mut para_base = 0;
    for (section, binding) in observed.sections().zip(&map.sections) {
        let section_sha = sha(&entry(raw, &binding.part)?);
        for control in section.controls() {
            if control.native_identity != NativeFormObservedIdentity::Missing
                || control.shape_locked
            {
                return Err("candidate native ID or protection".into());
            }
            let kind = match control.tag {
                NativeFormTag::Edit => "+edt",
                NativeFormTag::RadioBtn => "+rbt",
                _ => return Err("candidate native form type unsupported".into()),
            };
            controls.push(json!({"section_part":binding.part,"section_sha256":section_sha,
                "paragraph_id":control.anchor.paragraph_id.as_str(),
                "physical_paragraph_ordinal":control.anchor.paragraph_ordinal,
                "run_ordinal":control.anchor.run_ordinal,"inline_ordinal":control.anchor.inline_ordinal,
                "native_identity_observation":"missing",
                "runtime_anchor_candidate":{"List":0,"Para":para_base+control.anchor.paragraph_ordinal},
                "native_ctrl_type":kind,"name":control.common.name,"tab_order":control.common.tab_order,
                "foreground_rgb":control.common.fore_color_rgb,"shape_locked":false}));
        }
        para_base += binding.map.paragraph_ids.len();
    }
    Ok(
        json!({"schema_version":"hwpx-agent.private-native-form-control-plan/v1","case_id":case_id,
        "source_package_sha256":sha(raw),"source_package_bytes":raw.len(),"controls":controls,
        "anchor_mapping_qualified":false,"native_runtime_qualified":false,"public_action_or_p09_gate":false}),
    )
}
struct Built {
    output: Vec<u8>,
    plan: Vec<u8>,
    record: Value,
}
fn prepare_checked_sdk(
    source: &[u8],
    map: &NativeFormPackageMap,
    policy: &[NativeFormPackagePolicy],
    requests: &[NativeFormColorRequest],
) -> Result<(NativeFormColorOutput, NativeFormColorReceipt), AnyError> {
    let plan = NativeFormColorPlan::bind(
        source,
        map,
        policy,
        requests,
        domain()?,
        NativeFormPackageLimits::default(),
    )?;
    let output = NativeFormColorPreparer::prepare(
        source,
        &plan,
        domain()?,
        NativeFormPackageLimits::default(),
        NativeFormColorLimits::default(),
    )?;
    let external = NativeFormColorPreparer::verify_output(
        source,
        &plan,
        output.bytes(),
        domain()?,
        NativeFormPackageLimits::default(),
        NativeFormColorLimits::default(),
    )?;
    let retry = NativeFormColorPreparer::prepare(
        source,
        &plan,
        domain()?,
        NativeFormPackageLimits::default(),
        NativeFormColorLimits::default(),
    )?;
    if &external != output.receipt()
        || retry.bytes() != output.bytes()
        || retry.receipt() != output.receipt()
        || external.requested_controls != requests.len()
        || external.actual_native_validation != "not_run"
    {
        return Err("candidate actual SDK external verification or retry".into());
    }
    Ok((output, external))
}
fn verify_original_intents(
    initial: &FormDocumentState,
    after: &FormDocumentState,
) -> Result<(), AnyError> {
    if initial.controls().len() != after.controls().len() {
        return Err("candidate control inventory changed".into());
    }
    for (old, new) in initial.controls().iter().zip(after.controls()) {
        let mut expected = old.clone();
        // ONLY the actual SDK's declared coupled style reference transition.
        // Never normalize names/tabs/colors/payload/protection to make equality.
        expected.common.character.char_pr_id_ref = new.common.character.char_pr_id_ref;
        if expected != *new {
            return Err("candidate exact original intent changed".into());
        }
    }
    Ok(())
}
fn build(root: &Path) -> Result<Vec<Built>, AnyError> {
    let manifest_raw = checked(&root.join(ORIGINAL), ORIGINAL_SHA)?;
    let manifest: Value = serde_json::from_slice(&manifest_raw)?;
    let originals = manifest["cases"]
        .as_array()
        .ok_or("candidate original inventory")?;
    if originals.len() != 15 {
        return Err("candidate all fifteen required".into());
    }
    let parent = root
        .join(ORIGINAL)
        .parent()
        .ok_or("candidate source parent")?
        .to_owned();
    let mut built = Vec::new();
    for (index, original) in originals.iter().enumerate() {
        let case_id = format!("P09-35-C{:02}", index + 1);
        if original["case_id"] != case_id {
            return Err("candidate original case identity".into());
        }
        let map = mapping(if index < 2 { 2 } else { 1 })?;
        if serde_json::to_value(&map)? != original["complete_map"] {
            return Err("candidate original map identity".into());
        }
        let source_file = original["file"].as_str().ok_or("candidate source name")?;
        if Path::new(source_file).components().count() != 1 {
            return Err("candidate source filename boundary".into());
        }
        let source = checked(
            &parent.join(source_file),
            original["package_sha256"]
                .as_str()
                .ok_or("candidate source sha")?,
        )?;
        if original["package_bytes"].as_u64() != Some(u64::try_from(source.len())?) {
            return Err("candidate original bytes".into());
        }
        let before =
            NativeFormPackageReader::read(&source, &map, NativeFormPackageLimits::default())?;
        let policy = policies(&before)?;
        let initial_state = before.bind_policies(&policy, domain()?)?;
        if sha(&serde_json::to_vec(&policy)?) != original["policy_sha256"]
            || initial_state.canonical_sha256(domain()?)? != original["target_state_sha256"]
            || before.document_flow_sha256() != original["document_flow_sha256"]
        {
            return Err("candidate original complete intent changed".into());
        }
        let requests: Vec<_> = before
            .sections()
            .flat_map(NativeFormHwpxReadback::controls)
            .map(|c| NativeFormColorRequest {
                target: c.component_identity.clone(),
                foreground_rgb: c.common.fore_color_rgb,
            })
            .collect();
        let (output, external) = prepare_checked_sdk(&source, &map, &policy, &requests)?;
        let after = NativeFormPackageReader::read(
            output.bytes(),
            &map,
            NativeFormPackageLimits::default(),
        )?;
        let state = after.bind_policies(&policy, domain()?)?;
        verify_original_intents(&initial_state, &state)?;
        let native_plan =
            serde_json::to_vec_pretty(&worker_plan(&case_id, output.bytes(), &map, &after)?)?;
        if native_plan.len() > 262_144 || output.bytes().len() > 4_194_304 {
            return Err("candidate output bound".into());
        }
        let file = format!("p09-51-c{:02}-coupled-native-form.hwpx", index + 1);
        let plan_file = format!("p09-50-c{:02}-native-form-plan.json", index + 1);
        built.push(Built {output:output.bytes().to_vec(),plan:native_plan.clone(),record:json!({
            "case_id":case_id,"file":file,"plan_file":plan_file,"plan_sha256":sha(&native_plan),"plan_bytes":native_plan.len(),
            "source_file":source_file,"original_package_sha256":sha(&source),"original_package_bytes":source.len(),
            "package_sha256":sha(output.bytes()),"package_bytes":output.bytes().len(),"complete_map":map,
            "controls":requests.len(),"policy_sha256":sha(&serde_json::to_vec(&policy)?),
            "original_state_sha256":original["target_state_sha256"],"target_state_sha256":state.canonical_sha256(domain()?)?,
            "document_flow_sha256":after.document_flow_sha256(),"actual_sdk_color_receipt":external,
            "whole_original_control_intent_except_declared_style_reference_exact":true,
            "actual_sdk_external_output_verification":true,"deterministic_preparation_retry":true,
            "native_runtime_qualified":false,"anchor_mapping_qualified":false})});
    }
    checked(&root.join(ORIGINAL), ORIGINAL_SHA)?;
    for record in &built {
        checked(
            &parent.join(
                record.record["source_file"]
                    .as_str()
                    .ok_or("candidate final input name")?,
            ),
            record.record["original_package_sha256"]
                .as_str()
                .ok_or("candidate final input sha")?,
        )?;
    }
    Ok(built)
}
fn manifest(cases: &[Built]) -> Result<Vec<u8>, AnyError> {
    let raw = serde_json::to_vec_pretty(
        &json!({"schema_version":"hwpx-agent.p09-51-complete-coupled-native-candidates/v1",
        "original_manifest_sha256":ORIGINAL_SHA,"cases":cases.iter().map(|c| &c.record).collect::<Vec<_>>(),
        "actual_hangul":false,"native_runtime_qualified":false,"render":"not_run","green_rows":0,
        "source_policy":"original_hash_checked_caller_declarations_not_native_defaults",
        "raw_document_values_present":false,"absolute_private_paths_present":false,"signed_form_publication_or_p09_gate":false}),
    )?;
    if raw.len() > 512 * 1024 {
        return Err("candidate manifest bound".into());
    }
    Ok(raw)
}
fn directory(root: &Path, argument: &OsStr, existing: bool) -> Result<PathBuf, AnyError> {
    let requested = PathBuf::from(argument);
    if !requested.is_absolute()
        || requested.exists() != existing
        || requested
            .components()
            .any(|c| matches!(c, Component::ParentDir | Component::CurDir))
    {
        return Err("candidate exclusive absolute directory required".into());
    }
    let name = requested
        .file_name()
        .and_then(OsStr::to_str)
        .ok_or("candidate directory name")?;
    if !name.starts_with(DIRECTORY_PREFIX)
        || name.len() > 100
        || name.len() <= DIRECTORY_PREFIX.len()
        || !name
            .bytes()
            .all(|b| b.is_ascii_lowercase() || b.is_ascii_digit() || b == b'-')
    {
        return Err("candidate directory name boundary".into());
    }
    let parent = requested.parent().ok_or("candidate directory parent")?;
    for ancestor in parent.ancestors() {
        if linked(&fs::symlink_metadata(ancestor)?) {
            return Err("candidate linked directory".into());
        }
    }
    if parent.canonicalize()? != root.join("fixtures/target-build").canonicalize()? {
        return Err("candidate directory boundary".into());
    }
    if existing && (!requested.is_dir() || linked(&fs::symlink_metadata(&requested)?)) {
        return Err("candidate existing directory invalid".into());
    }
    Ok(parent.join(name))
}
fn publish(root: &Path, argument: &OsStr) -> Result<(), AnyError> {
    let output = directory(root, argument, false)?;
    let cases = build(root)?;
    let value = manifest(&cases)?;
    fs::create_dir(&output)?; // Exclusive root before SecureWorkspace's create_dir_all.
    let workspace = SecureWorkspace::create(&output)?;
    for case in &cases {
        for (key, raw) in [
            ("file", case.output.as_slice()),
            ("plan_file", case.plan.as_slice()),
        ] {
            let name = Path::new(
                case.record[key]
                    .as_str()
                    .ok_or("candidate publication name")?,
            );
            let staged = workspace.stage_bytes(&Path::new("p09-51").join(name), raw)?;
            workspace.publish(&staged, name)?;
        }
    }
    let staged = workspace.stage_bytes(Path::new("p09-51/fixture-manifest.json"), &value)?;
    workspace.publish(&staged, Path::new("fixture-manifest.json"))?;
    println!(
        "{}",
        json!({"state":"pass","cases":15,"controls":17,"manifest_sha256":sha(&value),
        "native_session_started":false,"green_rows":0})
    );
    Ok(())
}
fn verify(root: &Path, argument: &OsStr) -> Result<(), AnyError> {
    let output = directory(root, argument, true)?.join("output");
    let cases = build(root)?;
    let value = manifest(&cases)?;
    if bytes(&output.join("fixture-manifest.json"))? != value
        || fs::read_dir(&output)?.count() != 31
    {
        return Err("candidate persisted complete inventory changed".into());
    }
    for case in &cases {
        for (key, raw) in [
            ("file", case.output.as_slice()),
            ("plan_file", case.plan.as_slice()),
        ] {
            if bytes(
                &output.join(
                    case.record[key]
                        .as_str()
                        .ok_or("candidate persisted name")?,
                ),
            )? != raw
            {
                return Err("candidate persisted artifact changed".into());
            }
        }
    }
    println!(
        "{}",
        json!({"state":"pass","scope":"fresh_complete_sdk_candidates_and_plans","cases":15,"controls":17,
        "files":31,"manifest_sha256":sha(&value),"native_session_started":false,"green_rows":0})
    );
    Ok(())
}
fn root() -> Result<PathBuf, AnyError> {
    Ok(Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()?)
}
fn run() -> Result<(), AnyError> {
    let root = root()?;
    let args: Vec<_> = env::args_os().skip(1).collect();
    match args.as_slice() {
        [mode] if mode == "--oracle-manifest" => {
            println!("{}", String::from_utf8(manifest(&build(&root)?)?)?);
            Ok(())
        }
        [mode, path] if mode == "--publish" => publish(&root, path),
        [mode, path] if mode == "--verify" => verify(&root, path),
        _ => Err("candidate bounded arguments required".into()),
    }
}
fn main() {
    if run().is_err() {
        eprintln!("P09_COUPLED_CANDIDATE_FAILED_NO_RAW_VALUES");
        std::process::exit(2);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn complete_fifteen_candidates_use_actual_sdk_and_external_verifier_and_preserve_intents()
    -> Result<(), AnyError> {
        let cases = build(&root()?)?;
        assert_eq!(cases.len(), 15);
        let mut controls = 0;
        for case in &cases {
            let plan: Value = serde_json::from_slice(&case.plan)?;
            controls += plan["controls"]
                .as_array()
                .ok_or("candidate test controls")?
                .len();
            assert_eq!(plan["source_package_sha256"], sha(&case.output));
            assert_eq!(plan["native_runtime_qualified"], false);
            assert_eq!(case.record["actual_sdk_external_output_verification"], true);
            assert_eq!(
                case.record["actual_sdk_color_receipt"]["actual_native_validation"],
                "not_run"
            );
        }
        assert_eq!(controls, 17);
        Ok(())
    }
    #[test]
    fn worker_plan_keeps_native_ids_missing_and_all_unicode_metachar_names_exact()
    -> Result<(), AnyError> {
        let cases = build(&root()?)?;
        for (index, name) in [
            "P09 이름 한글",
            "P09 이름 & 폼",
            "P09 이름 < 폼",
            "P09 이름 > 폼",
            "P09 이름 \" 폼",
            "P09 이름 ' 폼",
        ]
        .iter()
        .enumerate()
        {
            let plan: Value = serde_json::from_slice(&cases[index + 8].plan)?;
            assert_eq!(plan["controls"][0]["name"], *name);
            assert_eq!(
                plan["controls"][0]["native_identity_observation"],
                "missing"
            );
            assert!(plan["controls"][0].get("native_object_id").is_none());
            assert!(
                plan["controls"][0]["runtime_anchor_candidate"]
                    .get("Pos")
                    .is_none()
            );
        }
        Ok(())
    }
    #[test]
    fn public_manifest_is_hash_only_and_exclusive_output_boundaries_reject_aliases()
    -> Result<(), AnyError> {
        let root = root()?;
        let text = String::from_utf8(manifest(&build(&root)?)?)?;
        assert!(!text.contains("P09 이름") && !text.contains("\\\\?") && !text.contains("<hp:"));
        for path in [
            PathBuf::from("relative"),
            root.join("fixtures/target-build/p09-35-native-form-diagnostics-01"),
            root.join("implementation/p09/p09-51-native-form-candidates-outside"),
            root.join("fixtures/target-build/p09-51-native-form-candidates-bad_name"),
        ] {
            assert!(directory(&root, path.as_os_str(), false).is_err());
        }
        Ok(())
    }
}
