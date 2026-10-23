//! Read-only real public SDK diagnosis of the frozen fifteen-case native batch.
//! No COM, source repair, normalization, policy inference or acceptance promotion.
use domain_ir::{
    FORM_CONTROL_SCHEMA_VERSION, FormControlAnchor, FormControlIdentity, FormControlLimitConfig,
    FormControlLimits, FormControlPayload, FormControlState, FormDocumentState,
    FormDocumentStateDraft, FormNativeBinding, FormTextValidation, LogicalId,
};
use hwpx_package::{
    BoundedZipReader, NativeFormHwpxLimits, NativeFormHwpxMap, NativeFormHwpxReadback,
    NativeFormHwpxReader, NativeFormObservedPayload, NativeFormPackageLimits, NativeFormPackageMap,
    NativeFormPackagePolicy, NativeFormPackageReadback, NativeFormPackageReader,
    NativeFormPackageSectionMap, PackageLimits,
};
use serde_json::{Value, json};
use sha2::{Digest as _, Sha256};
use std::{
    collections::BTreeSet,
    error::Error,
    fs,
    io::{Cursor, Read as _},
    path::{Path, PathBuf},
};

type AnyError = Box<dyn Error>;
const MANIFEST: &str =
    "fixtures/target-build/p09-35-native-form-diagnostics-01/output/fixture-manifest.json";
const MANIFEST_SHA: &str = "ef1bdad32cf06b07725a17888b7378e9720b2111539675c20178ab850f1d9750";
const RECOVERY: &str = "implementation/p09/evidence/p09-36-native-form-complete-recovery.r06.json";
const RECOVERY_SHA: &str = "47df877e392f1ffd0a79f16eb2629db8eedc1f85390f4b75e47a5d77029586cb";

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
            return Err("linked source refused".into());
        }
    }
    let metadata = fs::metadata(path)?;
    if !metadata.is_file() || metadata.len() == 0 || metadata.len() > 4 * 1024 * 1024 {
        return Err("source bound".into());
    }
    let mut value = Vec::new();
    fs::File::open(path)?
        .take(4 * 1024 * 1024 + 1)
        .read_to_end(&mut value)?;
    if value.len() as u64 != metadata.len() {
        return Err("source changed".into());
    }
    Ok(value)
}
fn checked(path: &Path, digest: &str) -> Result<Vec<u8>, AnyError> {
    let raw = bytes(path)?;
    if sha(&raw) != digest {
        return Err("source identity changed".into());
    }
    Ok(raw)
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
// Reproduce the original fixture's explicit caller policy and verify its sealed hash.
// These are not newly discovered native defaults or validation guarantees.
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
                    radio_group_name: radio_group_name.clone().ok_or("fixture group missing")?,
                    group_required: true,
                    tri_state: *tri_state,
                    back_style: *back_style,
                },
                _ => return Err("unsupported fixture payload".into()),
            };
            Ok(NativeFormPackagePolicy {
                identity: c.component_identity.clone(),
                payload,
            })
        })
        .collect()
}
fn fingerprint(value: Option<&Value>) -> Result<Value, AnyError> {
    Ok(match value {
        Some(v) => json!({"present":true,"sha256":sha(&serde_json::to_vec(v)?)}),
        None => json!({"present":false}),
    })
}
// Keys come from public typed struct serialization, never document text or XML attributes.
fn differences(
    left: &Value,
    right: &Value,
    path: &str,
    output: &mut Vec<Value>,
) -> Result<(), AnyError> {
    if left == right {
        return Ok(());
    }
    match (left, right) {
        (Value::Object(a), Value::Object(b)) => {
            let keys: BTreeSet<_> = a.keys().chain(b.keys()).collect();
            for key in keys {
                let next = format!("{path}/{key}");
                match (a.get(key), b.get(key)) {
                    (Some(x), Some(y)) => differences(x, y, &next, output)?,
                    (x, y) => output.push(json!({"field":next,"expected":fingerprint(x)?,"observed":fingerprint(y)?})),
                }
            }
        }
        (Value::Array(a), Value::Array(b)) if a.len() == b.len() => {
            for (i, (x, y)) in a.iter().zip(b).enumerate() {
                differences(x, y, &format!("{path}/{i}"), output)?;
            }
        }
        _ => output.push(json!({"field":path,"expected":fingerprint(Some(left))?,"observed":fingerprint(Some(right))?})),
    }
    if output.len() > 256 {
        return Err("difference bound".into());
    }
    Ok(())
}
fn section_results(raw: &[u8], map: &NativeFormPackageMap) -> Result<Value, AnyError> {
    let mut zip = BoundedZipReader::open(Cursor::new(raw), PackageLimits::default())?;
    let mut rows = Vec::new();
    for section in &map.sections {
        let index = zip
            .entries()
            .iter()
            .position(|e| e.path.as_str() == section.part)
            .ok_or("section missing")?;
        let part = zip.read_entry(index)?;
        let result = match NativeFormHwpxReader::read_section(
            &part,
            &section.map,
            NativeFormHwpxLimits::default(),
        ) {
            Ok(value) => json!({"state":"pass","controls":value.controls().len()}),
            Err(error) => json!({"state":"fail","error_code":error.to_string()}),
        };
        rows.push(
            json!({"part":section.part,"section_sha256":sha(&part),"public_section_reader":result}),
        );
    }
    Ok(json!(rows))
}
fn domain_result(
    observed: &NativeFormPackageReadback,
    policies: &[NativeFormPackagePolicy],
) -> Result<Value, AnyError> {
    let mut controls = Vec::new();
    let mut orders = BTreeSet::new();
    let mut duplicate_orders = 0;
    for (c, policy) in observed
        .sections()
        .flat_map(NativeFormHwpxReadback::controls)
        .zip(policies)
    {
        if c.component_identity != policy.identity {
            return Err("domain diagnostic policy identity".into());
        }
        if c.common.tab_order.is_some_and(|o| !orders.insert(o)) {
            duplicate_orders += 1;
        }
        controls.push(FormControlState {
            identity: c.component_identity.clone(),
            anchor: FormControlAnchor {
                paragraph_id: c.anchor.paragraph_id.clone(),
                run_ordinal: c.anchor.run_ordinal,
                inline_ordinal: c.anchor.inline_ordinal,
            },
            native_binding: FormNativeBinding::Exact { tag: c.tag },
            common: c.common.clone(),
            payload: policy.payload.clone(),
            shape_locked: c.shape_locked,
            shape_state_sha256: c.geometry_sha256.clone(),
            opaque_native_payload_sha256: c.preserved_opaque_sha256.clone(),
            opaque_properties: Vec::new(),
        });
    }
    if controls.len() != policies.len() {
        return Err("domain diagnostic inventory".into());
    }
    // Keep all actual package fingerprints; no zero bindings or discarded metadata.
    let serialized = serde_json::to_value(observed)?;
    let bindings: Value = serde_json::from_slice(&observed.bindings().canonical_json()?)?;
    let digest = |name: &str| -> Result<String, AnyError> {
        Ok(bindings[name]
            .as_str()
            .ok_or("actual binding digest missing")?
            .to_owned())
    };
    let draft = FormDocumentStateDraft {
        schema_version: FORM_CONTROL_SCHEMA_VERSION.into(),
        controls,
        non_form_content_sha256: serialized["non_form_content_sha256"]
            .as_str()
            .ok_or("actual nonform digest missing")?
            .into(),
        style_catalog_sha256: digest("style_catalog_sha256")?,
        border_catalog_sha256: digest("border_catalog_sha256")?,
        resource_inventory_sha256: digest("resource_inventory_sha256")?,
        reference_inventory_sha256: digest("reference_inventory_sha256")?,
        document_protection_sha256: digest("document_protection_sha256")?,
        opaque_document_state_sha256: digest("opaque_document_state_sha256")?,
    };
    let mut result = match FormDocumentState::from_draft(draft, limits()?) {
        Ok(state) => json!({"state":"pass","canonical_sha256":state.canonical_sha256(limits()?)?}),
        Err(error) => json!({"state":"fail","error_code":error.code()}),
    };
    result["duplicate_tab_order_count"] = json!(duplicate_orders);
    Ok(result)
}
fn observe(
    raw: &[u8],
    expected: &NativeFormPackageReadback,
    map: &NativeFormPackageMap,
    policies: &[NativeFormPackagePolicy],
) -> Result<Value, AnyError> {
    let observed = match NativeFormPackageReader::read(raw, map, NativeFormPackageLimits::default())
    {
        Ok(value) => value,
        Err(error) => {
            return Ok(
                json!({"public_package_reader":"fail","error_code":error.to_string(),
            "independent_public_section_readers":section_results(raw, map)?}),
            );
        }
    };
    let mut control_changes = Vec::new();
    let expected_controls: Vec<_> = expected
        .sections()
        .flat_map(NativeFormHwpxReadback::controls)
        .collect();
    let observed_controls: Vec<_> = observed
        .sections()
        .flat_map(NativeFormHwpxReadback::controls)
        .collect();
    differences(
        &serde_json::to_value(expected_controls)?,
        &serde_json::to_value(observed_controls)?,
        "/controls",
        &mut control_changes,
    )?;
    let mut binding_changes = Vec::new();
    differences(
        &serde_json::from_slice(&expected.bindings().canonical_json()?)?,
        &serde_json::from_slice(&observed.bindings().canonical_json()?)?,
        "/bindings",
        &mut binding_changes,
    )?;
    let policy_result = match observed.bind_policies(policies, limits()?) {
        Ok(state) => json!({"state":"pass","canonical_sha256":state.canonical_sha256(limits()?)?}),
        Err(error) => json!({"state":"fail","error_code":error.to_string()}),
    };
    let domain = domain_result(&observed, policies)?;
    if policy_result["state"] == "pass"
        && (domain["state"] != "pass"
            || domain["canonical_sha256"] != policy_result["canonical_sha256"])
    {
        return Err("independent domain binding disagreement".into());
    }
    Ok(
        json!({"public_package_reader":"pass","public_policy_binding":policy_result,
        "independent_public_domain_validator":domain,
        "control_field_differences":control_changes,"package_binding_differences":binding_changes,
        "document_flow_exact":observed.document_flow_sha256()==expected.document_flow_sha256(),
        "independent_public_section_readers":section_results(raw, map)?}),
    )
}
fn evidence(root: &Path, recovery: &Value) -> Result<(), AnyError> {
    let pins = recovery["native_evidence_sha256"]
        .as_object()
        .ok_or("native pins missing")?;
    if pins.len() != 75 {
        return Err("native pin count".into());
    }
    for (relative, digest) in pins {
        let parts: Vec<_> = relative.split(['/', '\\']).collect();
        if parts.len() != 6
            || parts[..4] != ["implementation", "p09", "evidence", "private"]
            || !parts[4].starts_with("p09-17-field-auto-number-target-p09-35-20261003-r05-c")
            || ![
                "saved.hwpx",
                "reopened.hwpx",
                "saved.pdf",
                "reopened.pdf",
                "target-trace.json",
            ]
            .contains(&parts[5])
        {
            return Err("native pin boundary".into());
        }
        checked(
            &root.join(parts.iter().collect::<PathBuf>()),
            digest.as_str().ok_or("pin missing")?,
        )?;
    }
    Ok(())
}
fn diagnose(root: &Path) -> Result<Value, AnyError> {
    let manifest: Value = serde_json::from_slice(&checked(&root.join(MANIFEST), MANIFEST_SHA)?)?;
    let recovery: Value = serde_json::from_slice(&checked(&root.join(RECOVERY), RECOVERY_SHA)?)?;
    evidence(root, &recovery)?;
    let cases = manifest["cases"].as_array().ok_or("cases missing")?;
    if cases.len() != 15 {
        return Err("case count".into());
    }
    let parent = root
        .join(MANIFEST)
        .parent()
        .ok_or("manifest parent missing")?
        .to_owned();
    let mut rows = Vec::new();
    for (i, case) in cases.iter().enumerate() {
        let map = mapping(if i < 2 { 2 } else { 1 })?;
        if serde_json::to_value(&map)? != case["complete_map"] {
            return Err("map identity changed".into());
        }
        let file = case["file"].as_str().ok_or("fixture file missing")?;
        if Path::new(file).components().count() != 1 || file.contains(['/', '\\', ':']) {
            return Err("fixture path boundary".into());
        }
        let input = checked(
            &parent.join(file),
            case["package_sha256"].as_str().ok_or("input pin missing")?,
        )?;
        let expected =
            NativeFormPackageReader::read(&input, &map, NativeFormPackageLimits::default())?;
        let caller_policy = policies(&expected)?;
        if sha(&serde_json::to_vec(&caller_policy)?)
            != case["policy_sha256"].as_str().ok_or("policy pin missing")?
            || expected
                .bind_policies(&caller_policy, limits()?)?
                .canonical_sha256(limits()?)?
                != case["target_state_sha256"]
                    .as_str()
                    .ok_or("state pin missing")?
        {
            return Err("original fixture intent changed".into());
        }
        let mut row = json!({"case_id":case["case_id"],"input_sha256":sha(&input)});
        let directory = root
            .join("implementation/p09/evidence/private")
            .join(format!(
                "p09-17-field-auto-number-target-p09-35-20261003-r05-c{:02}-attempt01",
                i + 1
            ));
        for stage in ["saved", "reopened"] {
            let raw = bytes(&directory.join(format!("{stage}.hwpx")))?;
            row[stage] = observe(&raw, &expected, &map, &caller_policy)?;
            row[stage]["package_sha256"] = json!(sha(&raw));
        }
        rows.push(row);
    }
    evidence(root, &recovery)?;
    checked(&root.join(MANIFEST), MANIFEST_SHA)?;
    checked(&root.join(RECOVERY), RECOVERY_SHA)?;
    Ok(
        json!({"schema_version":"hwpx-agent.p09-native-public-readback-diagnosis/v1",
        "recovery_sha256":RECOVERY_SHA,"manifest_sha256":MANIFEST_SHA,"cases":rows,
        "all_seventy_five_native_files_before_after_exact":true,
        "caller_policy":"original_fixture_explicit_hash_verified_not_native_inferred",
        "native_session_started":false,"raw_document_values_present":false,
        "native_semantic_repair_qualified":false,"green_rows":0,"p09_complete":false}),
    )
}
fn run() -> Result<(), AnyError> {
    if std::env::args_os().len() != 1 {
        return Err("arguments refused".into());
    }
    let root = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()?;
    println!("{}", diagnose(&root)?);
    Ok(())
}
fn main() {
    if run().is_err() {
        eprintln!("P09_NATIVE_READBACK_DIAGNOSIS_FAILED");
        std::process::exit(2);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn changed_fields_are_reported_as_fingerprints_without_values() -> Result<(), AnyError> {
        let mut out = Vec::new();
        differences(
            &json!({"name":"private_expected","flag":true}),
            &json!({"name":"private_observed","flag":false}),
            "/common",
            &mut out,
        )?;
        assert_eq!(out.len(), 2);
        let value = serde_json::to_string(&out)?;
        assert!(!value.contains("private_expected"));
        assert!(!value.contains("private_observed"));
        assert!(value.contains("/common/name"));
        Ok(())
    }
    #[test]
    fn equal_missing_array_and_null_remain_distinct() -> Result<(), AnyError> {
        let mut out = Vec::new();
        differences(
            &json!({"a":null,"b":[1]}),
            &json!({"b":[1,2]}),
            "",
            &mut out,
        )?;
        assert_eq!(out.len(), 2);
        assert_eq!(out[0]["observed"]["present"], false);
        let mut same = Vec::new();
        differences(&json!([1, null]), &json!([1, null]), "", &mut same)?;
        assert!(same.is_empty());
        Ok(())
    }
    #[test]
    fn real_fifteen_case_reader_failures_are_not_promoted() -> Result<(), AnyError> {
        let root = Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("../..")
            .canonicalize()?;
        let value = diagnose(&root)?;
        assert_eq!(value["cases"].as_array().ok_or("cases missing")?.len(), 15);
        for stage in ["saved", "reopened"] {
            assert_eq!(value["cases"][0][stage]["public_package_reader"], "pass");
            assert_eq!(
                value["cases"][0][stage]["public_policy_binding"]["state"],
                "fail"
            );
            assert_eq!(
                value["cases"][0][stage]["independent_public_domain_validator"]["error_code"],
                "form_control_invalid_tab_order"
            );
            assert_eq!(
                value["cases"][0][stage]["independent_public_domain_validator"]["duplicate_tab_order_count"],
                1
            );
        }
        assert_eq!(value["native_semantic_repair_qualified"], false);
        assert_eq!(value["green_rows"], 0);
        Ok(())
    }
}
