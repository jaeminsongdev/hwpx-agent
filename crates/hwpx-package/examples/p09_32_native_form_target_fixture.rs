//! Complete disposable native form fixtures through the actual public package API.
use domain_ir::{
    FORM_CONTROL_SCHEMA_VERSION, FormControlBuilder, FormControlIdentity, FormControlLimitConfig,
    FormControlLimits, FormControlOperation, FormControlPayload, FormControlPlan,
    FormControlRequest, FormControlRequestDraft, FormTabAssignment, FormTextValidation, LogicalId,
};
use hwpx_package::{
    CharacterStyleCatalogReader, CharacterStyleLimits, NATIVE_FORM_PACKAGE_OUTPUT_PROFILE_ID,
    NativeFormHwpxMap, NativeFormHwpxReadback, NativeFormObservedPayload, NativeFormPackageLimits,
    NativeFormPackageLowerer, NativeFormPackageMap, NativeFormPackageOutput,
    NativeFormPackageOutputLimits, NativeFormPackageOutputPlan, NativeFormPackageOutputReceipt,
    NativeFormPackagePolicy, NativeFormPackageReadback, NativeFormPackageReader,
    NativeFormPackageSectionMap,
};
use sha2::{Digest as _, Sha256};
use std::{
    collections::BTreeMap,
    error::Error,
    fs,
    io::{Cursor, Read as _, Write as _},
    path::Path,
};
use zip::{CompressionMethod, ZipArchive, ZipWriter, write::SimpleFileOptions};

type AnyError = Box<dyn Error>;
const CAPTURE: &str = "implementation/p08/evidence/private/p08-20-object-target-20260915-18/obj-012-form-insert.hancom-2020-readback.hwpx";
const CAPTURE_SHA: &str = "02e9b5acef95877b6934a6a3131069402138cc2190eff2e68db79aa7e9ac9ce7";
fn sha(raw: &[u8]) -> String {
    hex::encode(Sha256::digest(raw))
}
fn capture() -> Result<Vec<u8>, AnyError> {
    let path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .join(CAPTURE);
    for ancestor in path.ancestors() {
        let m = fs::symlink_metadata(ancestor)?;
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt as _;
            if m.file_attributes() & 0x400 != 0 {
                return Err("capture reparse refused".into());
            }
        }
        if m.file_type().is_symlink() {
            return Err("capture link refused".into());
        }
    }
    if fs::metadata(&path)?.len() != 14556 {
        return Err("capture size changed".into());
    }
    let raw = fs::read(path)?;
    if raw.len() != 14556 || sha(&raw) != CAPTURE_SHA {
        return Err("capture source identity changed".into());
    }
    Ok(raw)
}
fn parts(raw: &[u8]) -> Result<BTreeMap<String, Vec<u8>>, AnyError> {
    let mut zip = ZipArchive::new(Cursor::new(raw))?;
    let mut out = BTreeMap::new();
    for i in 0..zip.len() {
        let mut entry = zip.by_index(i)?;
        let mut value = Vec::new();
        entry.read_to_end(&mut value)?;
        out.insert(entry.name().into(), value);
    }
    Ok(out)
}
fn package(parts: &BTreeMap<String, Vec<u8>>) -> Result<Vec<u8>, AnyError> {
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    writer.start_file(
        "mimetype",
        SimpleFileOptions::default().compression_method(CompressionMethod::Stored),
    )?;
    writer.write_all(parts.get("mimetype").ok_or("mimetype")?)?;
    for (path, raw) in parts {
        if path != "mimetype" {
            writer.start_file(
                path,
                SimpleFileOptions::default().compression_method(CompressionMethod::Deflated),
            )?;
            writer.write_all(raw)?;
        }
    }
    Ok(writer.finish()?.into_inner())
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
fn observe(raw: &[u8], count: usize) -> Result<NativeFormPackageReadback, AnyError> {
    Ok(NativeFormPackageReader::read(
        raw,
        &map(count)?,
        NativeFormPackageLimits::default(),
    )?)
}
// Explicit test policy. Native XML has not established defaults or validation behavior.
fn text_policies(
    observed: &NativeFormPackageReadback,
) -> Result<Vec<NativeFormPackagePolicy>, AnyError> {
    observed
        .sections()
        .flat_map(NativeFormHwpxReadback::controls)
        .map(|c| {
            let NativeFormObservedPayload::Text {
                value,
                multi_line,
                password_character,
                native_max_length,
                scroll_bars,
                tab_key_behavior,
                number_only,
                read_only,
                alignment,
            } = &c.payload
            else {
                return Err("test policy supports captured edits only".into());
            };
            Ok(NativeFormPackagePolicy {
                identity: c.component_identity.clone(),
                payload: FormControlPayload::Text {
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
            })
        })
        .collect()
}
fn domain_plan(
    observed: &NativeFormPackageReadback,
    operation: FormControlOperation,
    flow: &str,
) -> Result<FormControlPlan, AnyError> {
    let state = observed.bind_policies(&policies(observed)?, limits()?)?;
    let request = FormControlRequest::from_draft(
        FormControlRequestDraft {
            schema_version: FORM_CONTROL_SCHEMA_VERSION.into(),
            request_id: LogicalId::parse("package-test-request")?,
            expected_source_state_sha256: state.canonical_sha256(limits()?)?,
            expected_document_flow_sha256: flow.into(),
            target_document_flow_sha256: flow.into(),
            operation,
        },
        &state,
        flow,
        limits()?,
    )?;
    Ok(FormControlBuilder::plan(&state, &request, flow, limits()?)?)
}
fn property(observed: &NativeFormPackageReadback) -> Result<FormControlOperation, AnyError> {
    let state = observed.bind_policies(&policies(observed)?, limits()?)?;
    let c = &state.controls()[0];
    let mut common = c.common.clone();
    common.enabled = !common.enabled;
    Ok(FormControlOperation::ReplaceProperties {
        target: c.identity.clone(),
        common,
        payload: c.payload.clone(),
    })
}
fn multi() -> Result<Vec<u8>, AnyError> {
    let original = capture()?;
    let observed = observe(&original, 1)?;
    let mut p = parts(&original)?;
    let section = String::from_utf8(p.get("Contents/section0.xml").ok_or("section")?.clone())?;
    let field = &observed.sections().next().ok_or("section")?.controls()[0]
        .common
        .name;
    let second = section
        .replace("<hp:p id=\"0\"", "<hp:p id=\"10\"")
        .replace("<hp:p id=\"1\"", "<hp:p id=\"11\"")
        .replace(
            &format!("name=\"{field}\""),
            "name=\"second-native-derived-field\"",
        )
        .replace("tabOrder=\"1\"", "tabOrder=\"2\"");
    p.insert("Contents/section1.xml".into(), second.into_bytes());
    let header = String::from_utf8(p.get("Contents/header.xml").ok_or("header")?.clone())?
        .replace("secCnt=\"1\"", "secCnt=\"2\"");
    p.insert("Contents/header.xml".into(), header.into_bytes());
    let opf = String::from_utf8(p.get("Contents/content.hpf").ok_or("opf")?.clone())?;
    let prefix = if opf.contains("</opf:manifest>") {
        "opf:"
    } else {
        ""
    };
    let changed = opf.replace(&format!("</{prefix}manifest>"), &format!("<{prefix}item id=\"section1\" href=\"section1.xml\" media-type=\"application/xml\"/></{prefix}manifest>"))
        .replace(&format!("</{prefix}spine>"), &format!("<{prefix}itemref idref=\"section1\" linear=\"yes\"/></{prefix}spine>"));
    if changed == opf {
        return Err("derived section manifest not changed".into());
    }
    p.insert("Contents/content.hpf".into(), changed.into_bytes());
    package(&p)
}

use hwpx_agent_foundation::workdir::SecureWorkspace;
use serde::Serialize;
use std::{env, path::PathBuf};

const FILENAMES: [&str; 6] = [
    "p09-32-c01-enabled-property.hwpx",
    "p09-32-c02-colors-editable.hwpx",
    "p09-32-c03-literal-name-group.hwpx",
    "p09-32-c04-character-properties.hwpx",
    "p09-32-c05-global-tab.hwpx",
    "p09-32-c06-cross-section-radio-tab.hwpx",
];
#[derive(Serialize)]
struct FixtureRecord {
    case_id: String,
    file: &'static str,
    source_file: String,
    source_kind: &'static str,
    package_sha256: String,
    package_bytes: usize,
    source_package_sha256: String,
    complete_map: NativeFormPackageMap,
    policy_sha256: String,
    target_state_sha256: String,
    target_controls_sha256: Vec<String>,
    receipt: NativeFormPackageOutputReceipt,
    deterministic_retry: bool,
    stale_source_rejected: bool,
}
struct Built {
    source: Vec<u8>,
    output: Vec<u8>,
    case: FixtureRecord,
}

fn policies(
    observed: &NativeFormPackageReadback,
) -> Result<Vec<NativeFormPackagePolicy>, AnyError> {
    if observed
        .sections()
        .flat_map(NativeFormHwpxReadback::controls)
        .all(|c| matches!(c.payload, NativeFormObservedPayload::Text { .. }))
    {
        return text_policies(observed);
    }
    observed
        .sections()
        .flat_map(NativeFormHwpxReadback::controls)
        .map(|c| {
            let NativeFormObservedPayload::Button {
                caption,
                value,
                radio_group_name,
                tri_state,
                back_style,
            } = &c.payload
            else {
                return Err("fixture policy unsupported".into());
            };
            Ok(NativeFormPackagePolicy {
                identity: c.component_identity.clone(),
                payload: FormControlPayload::Radio {
                    caption: caption.clone(),
                    value: *value,
                    default_value: *value,
                    radio_group_name: radio_group_name.clone().ok_or("radio group missing")?,
                    group_required: true,
                    tri_state: *tri_state,
                    back_style: *back_style,
                },
            })
        })
        .collect()
}
fn radio_source() -> Result<Vec<u8>, AnyError> {
    let mut p = parts(&multi()?)?;
    for i in 0..2 {
        let name = format!("Contents/section{i}.xml");
        let source = String::from_utf8(p.get(&name).ok_or("section missing")?.clone())?;
        let start = source.find("<hp:edit ").ok_or("edit missing")?;
        let end = source.find("</hp:edit>").ok_or("edit end missing")? + "</hp:edit>".len();
        let edit = &source[start..end];
        let geometry =
            &edit[edit.find("<hp:sz ").ok_or("geometry missing")?..edit.len() - "</hp:edit>".len()];
        let value = if i == 0 { "CHECKED" } else { "UNCHECKED" };
        let radio = format!(
            "<hp:radioBtn name=\"radio-{i}\" foreColor=\"#000000\" backColor=\"#FFFFFF\" groupName=\"\" tabStop=\"1\" editable=\"1\" tabOrder=\"{}\" enabled=\"1\" borderTypeIDRef=\"0\" drawFrame=\"1\" printable=\"1\" command=\"\" caption=\"radio\" value=\"{value}\" radioGroupName=\"complete-group\" triState=\"0\" backStyle=\"TRANSPARENT\"><hp:formCharPr charPrIDRef=\"0\" followContext=\"0\" autoSz=\"0\" wordWrap=\"1\"/>{geometry}</hp:radioBtn>",
            i + 1
        );
        p.insert(
            name,
            format!("{}{radio}{}", &source[..start], &source[end..]).into_bytes(),
        );
    }
    package(&p)
}
fn operation(
    index: usize,
    source: &[u8],
    observed: &NativeFormPackageReadback,
) -> Result<FormControlOperation, AnyError> {
    if index == 0 {
        return property(observed);
    }
    let state = observed.bind_policies(&policies(observed)?, limits()?)?;
    if index >= 4 {
        let assignments = state
            .controls()
            .iter()
            .enumerate()
            .map(|(i, c)| {
                Ok(FormTabAssignment {
                    target: c.identity.clone(),
                    tab_stop: true,
                    tab_order: Some(u32::try_from(if index == 4 {
                        i
                    } else {
                        state.controls().len() - 1 - i
                    })?),
                })
            })
            .collect::<Result<Vec<_>, AnyError>>()?;
        return Ok(FormControlOperation::SetTabOrder { assignments });
    }
    let c = state.controls().first().ok_or("fixture control missing")?;
    let mut common = c.common.clone();
    match index {
        1 => {
            common.fore_color_rgb = 0x00CC_1100;
            common.back_color_rgb = 0x00EE_F0FA;
            common.editable = false;
        }
        2 => {
            common.name = "P09 새 & <\"'> 폼".into();
            common.group_name = Some("P09 그룹 & <\"'>".into());
        }
        3 => {
            let p = parts(source)?;
            let catalog = CharacterStyleCatalogReader::read(
                p.get("Contents/header.xml").ok_or("header missing")?,
                CharacterStyleLimits::default(),
            )?;
            common.character.char_pr_id_ref = catalog
                .styles
                .iter()
                .find(|s| s.id != common.character.char_pr_id_ref)
                .ok_or("alternate catalog style missing")?
                .id;
            common.character.follow_context = !common.character.follow_context;
            common.character.auto_size = !common.character.auto_size;
            common.character.word_wrap = !common.character.word_wrap;
        }
        _ => return Err("fixture index invalid".into()),
    }
    Ok(FormControlOperation::ReplaceProperties {
        target: c.identity.clone(),
        common,
        payload: c.payload.clone(),
    })
}
fn build_cases() -> Result<Vec<Built>, AnyError> {
    let original = capture()?;
    let mut out = Vec::new();
    for (i, file) in FILENAMES.iter().enumerate() {
        let source = if i == 5 {
            radio_source()?
        } else if i == 4 {
            multi()?
        } else {
            original.clone()
        };
        let count = if i >= 4 { 2 } else { 1 };
        let map = map(count)?;
        let observed = observe(&source, count)?;
        let policies = policies(&observed)?;
        let domain = domain_plan(
            &observed,
            operation(i, &source, &observed)?,
            observed.document_flow_sha256(),
        )?;
        let plan = NativeFormPackageOutputPlan::bind(
            &source,
            &map,
            &policies,
            &domain,
            limits()?,
            NativeFormPackageLimits::default(),
        )?;
        let output = verified_output(&source, &plan)?;
        let result = NativeFormPackageReader::read(
            output.bytes(),
            &map,
            NativeFormPackageLimits::default(),
        )?;
        let target = result.bind_policies(&policies, limits()?)?;
        if &target != domain.target_state() {
            return Err("real complete target state mismatch".into());
        }
        let target_controls_sha256 = target
            .controls()
            .iter()
            .map(|c| Ok(sha(&serde_json::to_vec(c)?)))
            .collect::<Result<Vec<_>, AnyError>>()?;
        let case = FixtureRecord {
            case_id: format!("P09-32-C{:02}", i + 1),
            file,
            source_file: format!("p09-32-c{:02}-source.hwpx", i + 1),
            source_kind: if i == 5 {
                "derived_cross_section_radio"
            } else if i == 4 {
                "derived_two_section_text"
            } else {
                "original_native_capture"
            },
            package_sha256: sha(output.bytes()),
            package_bytes: output.bytes().len(),
            source_package_sha256: sha(&source),
            complete_map: map,
            policy_sha256: sha(&serde_json::to_vec(&policies)?),
            target_state_sha256: target.canonical_sha256(limits()?)?,
            target_controls_sha256,
            receipt: output.receipt().clone(),
            deterministic_retry: true,
            stale_source_rejected: true,
        };
        out.push(Built {
            source,
            output: output.bytes().to_vec(),
            case,
        });
    }
    if sha(&capture()?) != CAPTURE_SHA {
        return Err("original capture changed".into());
    }
    Ok(out)
}
fn verified_output(
    source: &[u8],
    plan: &NativeFormPackageOutputPlan,
) -> Result<NativeFormPackageOutput, AnyError> {
    let output = NativeFormPackageLowerer::lower(
        source,
        plan,
        limits()?,
        NativeFormPackageLimits::default(),
        NativeFormPackageOutputLimits::default(),
    )?;
    let repeated = NativeFormPackageLowerer::lower(
        source,
        plan,
        limits()?,
        NativeFormPackageLimits::default(),
        NativeFormPackageOutputLimits::default(),
    )?;
    if output.bytes() != repeated.bytes() || output.receipt() != repeated.receipt() {
        return Err("fixture retry drift".into());
    }
    let external = NativeFormPackageLowerer::verify_output(
        source,
        plan,
        output.bytes(),
        limits()?,
        NativeFormPackageLimits::default(),
        NativeFormPackageOutputLimits::default(),
    )?;
    if &external != output.receipt() {
        return Err("external output receipt drift".into());
    }
    let mut stale = source.to_vec();
    stale.push(0);
    if NativeFormPackageLowerer::lower(
        &stale,
        plan,
        limits()?,
        NativeFormPackageLimits::default(),
        NativeFormPackageOutputLimits::default(),
    )
    .is_ok()
    {
        return Err("stale source admitted".into());
    }
    Ok(output)
}
fn is_link(metadata: &fs::Metadata) -> bool {
    #[cfg(windows)]
    {
        use std::os::windows::fs::MetadataExt as _;
        if metadata.file_attributes() & 0x400 != 0 {
            return true;
        }
    }
    metadata.file_type().is_symlink()
}
fn output_argument(root: &Path) -> Result<PathBuf, AnyError> {
    let mut args = env::args_os().skip(1);
    let out = PathBuf::from(args.next().ok_or("new fixture output required")?);
    if args.next().is_some() || !out.is_absolute() || out.exists() {
        return Err("new absolute fixture child required".into());
    }
    let parent = out.parent().ok_or("fixture parent missing")?;
    for ancestor in parent.ancestors() {
        if is_link(&fs::symlink_metadata(ancestor)?) {
            return Err("fixture linked boundary refused".into());
        }
    }
    if parent.canonicalize()? != root.join("fixtures/target-build").canonicalize()? {
        return Err("fixture output boundary refused".into());
    }
    Ok(parent.join(out.file_name().ok_or("fixture output name missing")?))
}
fn run() -> Result<(), AnyError> {
    let root = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()?;
    let output = output_argument(&root)?;
    let built = build_cases()?;
    let value = serde_json::json!({"schema_version":"hwpx-agent.p09-native-form-target-fixtures/v1","task":"P09-32",
        "target_profile":{"product":"Hancom Hangul 2020","build":"11.0.0.9136","architecture":"x86","locale":"ko-KR"},
        "source_capture_sha256":CAPTURE_SHA,"public_api_profile":NATIVE_FORM_PACKAGE_OUTPUT_PROFILE_ID,
        "cases":built.iter().map(|c|&c.case).collect::<Vec<_>>(),"actual_hangul":false,"render":"not_run","green_rows":0,
        "raw_document_text_present":false,"absolute_private_paths_present":false});
    let raw = serde_json::to_vec_pretty(&value)?;
    if raw.len() > 512 * 1024 {
        return Err("fixture manifest bound".into());
    }
    let workspace = SecureWorkspace::create(&output)?;
    for row in &built {
        for (name, bytes) in [
            (&row.case.source_file, row.source.as_slice()),
            (&row.case.file.to_owned(), row.output.as_slice()),
        ] {
            let staged = workspace.stage_bytes(&Path::new("p09-32").join(name), bytes)?;
            workspace.publish(&staged, Path::new(name))?;
        }
    }
    let staged = workspace.stage_bytes(Path::new("p09-32/fixture-manifest.json"), &raw)?;
    workspace.publish(&staged, Path::new("fixture-manifest.json"))?;
    println!(
        "{}",
        serde_json::json!({"state":"pass","cases":6,"manifest_sha256":sha(&raw),"native_session_started":false,"green_rows":0})
    );
    Ok(())
}
fn main() {
    let native = env::args_os()
        .nth(1)
        .is_some_and(|s| s == "--inspect-native-batch");
    if (if native {
        inspect_native_batch()
    } else {
        run()
    })
    .is_err()
    {
        eprintln!("P09_NATIVE_FORM_FIXTURE_FAILED");
        std::process::exit(2);
    }
}
fn bounded_native_bytes(path: &Path) -> Result<Vec<u8>, AnyError> {
    for ancestor in path.ancestors() {
        if is_link(&fs::symlink_metadata(ancestor)?) {
            return Err("native linked evidence refused".into());
        }
    }
    let metadata = fs::metadata(path)?;
    if !metadata.is_file() || metadata.len() == 0 || metadata.len() > 4 * 1024 * 1024 {
        return Err("native package bound".into());
    }
    let mut raw = Vec::new();
    fs::File::open(path)?
        .take(4 * 1024 * 1024 + 1)
        .read_to_end(&mut raw)?;
    if raw.len() as u64 != metadata.len() {
        return Err("native package size changed".into());
    }
    Ok(raw)
}
fn inspect_native_stage(built: &Built, raw: &[u8]) -> Result<serde_json::Value, AnyError> {
    let expected = NativeFormPackageReader::read(
        &built.output,
        &built.case.complete_map,
        NativeFormPackageLimits::default(),
    )?;
    let actual = NativeFormPackageReader::read(
        raw,
        &built.case.complete_map,
        NativeFormPackageLimits::default(),
    )?;
    let state = actual.bind_policies(&policies(&expected)?, limits()?)?;
    let state_sha = state.canonical_sha256(limits()?)?;
    let controls_sha = state
        .controls()
        .iter()
        .map(|c| Ok(sha(&serde_json::to_vec(c)?)))
        .collect::<Result<Vec<_>, AnyError>>()?;
    Ok(
        serde_json::json!({"complete_public_reader":"pass", "complete_policy_binding":"pass",
        "package_sha256":sha(raw), "package_bytes":raw.len(), "controls":state.controls().len(),
        "target_state_sha256":state_sha, "document_flow_sha256":actual.document_flow_sha256(),
        "complete_target_state_exact":state_sha == built.case.target_state_sha256,
        "target_control_fingerprints_exact":controls_sha == built.case.target_controls_sha256,
        "document_flow_exact":actual.document_flow_sha256() == expected.document_flow_sha256(),
            "complete_package_bindings_exact":actual.bindings() == expected.bindings(),
        "green_rows":0}),
    )
}
fn inspect_native_batch() -> Result<(), AnyError> {
    let args: Vec<_> = env::args_os().skip(1).collect();
    if args.len() != 2 {
        return Err("native batch prefix required".into());
    }
    let prefix = args[1].to_str().ok_or("native batch prefix invalid")?;
    if prefix.is_empty()
        || prefix.len() > 40
        || !prefix
            .bytes()
            .all(|b| b.is_ascii_lowercase() || b.is_ascii_digit() || b == b'-')
    {
        return Err("native batch prefix invalid".into());
    }
    let root = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()?;
    let built = build_cases()?;
    let mut rows = Vec::new();
    for (i, case) in built.iter().enumerate() {
        let dir = root
            .join("implementation/p09/evidence/private")
            .join(format!(
                "p09-17-field-auto-number-target-{prefix}-c{:02}-attempt01",
                i + 1
            ));
        let mut row = serde_json::json!({"case_id":case.case.case_id});
        for stage in ["saved", "reopened"] {
            let path = dir.join(format!("{stage}.hwpx"));
            if !path.exists() {
                row[stage] = serde_json::json!({"complete_public_reader_or_policy_binding":"not_run",
                    "error_code":"native_output_missing", "green_rows":0});
                continue;
            }
            let raw = bounded_native_bytes(&path)?;
            let result = match inspect_native_stage(case, &raw) {
                Ok(result) => result,
                Err(_) => serde_json::json!({"complete_public_reader_or_policy_binding":"fail",
                    "error_code":"native_form_complete_readback_failed", "package_sha256":sha(&raw), "package_bytes":raw.len(), "green_rows":0}),
            };
            row[stage] = result;
        }
        rows.push(row);
    }
    println!(
        "{}",
        serde_json::json!({"schema_version":"hwpx-agent.p09-native-form-public-readback/v1",
        "task":"P09-32", "state":"actual_complete_public_readback_observations_non_green", "cases":rows,
        "native_session_started":false, "raw_document_text_present":false, "absolute_private_paths_present":false,
        "green_rows":0, "p09_complete":false})
    );
    Ok(())
}
#[cfg(test)]
mod tests {
    use super::*;
    use hwpx_package::NativeFormObservedIdentity;
    #[test]
    fn all_six_real_public_package_cases_have_complete_map_retry_and_external_verification()
    -> Result<(), AnyError> {
        let cases = build_cases()?;
        assert_eq!(cases.len(), 6);
        assert_eq!(cases[4].case.receipt.changed_sections, 2);
        assert_eq!(cases[5].case.receipt.changed_attributes, 1);
        assert!(
            cases
                .iter()
                .all(|c| c.case.deterministic_retry && c.case.stale_source_rejected)
        );
        Ok(())
    }
    #[test]
    fn original_and_derived_native_identity_are_not_fabricated() -> Result<(), AnyError> {
        for case in build_cases()? {
            let observed = NativeFormPackageReader::read(
                &case.output,
                &case.case.complete_map,
                NativeFormPackageLimits::default(),
            )?;
            for c in observed
                .sections()
                .flat_map(NativeFormHwpxReadback::controls)
            {
                assert_eq!(c.native_identity, NativeFormObservedIdentity::Missing);
            }
        }
        assert_eq!(sha(&capture()?), CAPTURE_SHA);
        Ok(())
    }
    #[test]
    fn native_observer_checks_real_complete_state_and_rejects_wrong_target() -> Result<(), AnyError>
    {
        let cases = build_cases()?;
        for case in &cases {
            let result = inspect_native_stage(case, &case.output)?;
            assert_eq!(result["complete_target_state_exact"], true);
            assert_eq!(result["target_control_fingerprints_exact"], true);
            assert_eq!(result["document_flow_exact"], true);
            assert_eq!(result["complete_package_bindings_exact"], true);
        }
        let wrong = inspect_native_stage(&cases[0], &cases[0].source)?;
        assert_eq!(wrong["complete_target_state_exact"], false);
        assert_eq!(wrong["target_control_fingerprints_exact"], false);
        assert_eq!(wrong["document_flow_exact"], true);
        Ok(())
    }
}
