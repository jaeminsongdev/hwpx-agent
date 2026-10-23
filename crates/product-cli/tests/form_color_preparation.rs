//! Actual product library -> public complete SDK, no mocked output or native claim.
use domain_ir::{
    FormControlIdentity, FormControlLimitConfig, FormControlLimits, FormControlPayload,
    FormTextValidation, LogicalId,
};
use hwpx_agent_cli::form_color_preparation::{
    FormColorContext, FormColorPreparation, FormColorPreparationError, FormColorPreparationLimits,
};
use hwpx_package::{
    NativeFormHwpxMap, NativeFormHwpxReadback, NativeFormObservedPayload, NativeFormPackageLimits,
    NativeFormPackageMap, NativeFormPackagePolicy, NativeFormPackageReader,
    NativeFormPackageSectionMap,
    native_form_color::{
        NativeFormColorLimits, NativeFormColorPlan, NativeFormColorPreparer, NativeFormColorRequest,
    },
};
use serde_json::Value;
use sha2::{Digest as _, Sha256};
use std::{error::Error, fs, path::Path};
type AnyError = Box<dyn Error>;
const MANIFEST: &str =
    "fixtures/target-build/p09-35-native-form-diagnostics-01/output/fixture-manifest.json";
const MANIFEST_SHA: &str = "ef1bdad32cf06b07725a17888b7378e9720b2111539675c20178ab850f1d9750";
fn sha(raw: &[u8]) -> String {
    hex::encode(Sha256::digest(raw))
}
fn checked(path: &Path, digest: &str) -> Result<Vec<u8>, AnyError> {
    for p in path.ancestors() {
        let m = fs::symlink_metadata(p)?;
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt as _;
            if m.file_attributes() & 0x400 != 0 {
                return Err("fixture reparse".into());
            }
        }
        if m.file_type().is_symlink() {
            return Err("fixture link".into());
        }
    }
    let m = fs::metadata(path)?;
    if !m.is_file() || m.len() == 0 || m.len() > 4 * 1024 * 1024 {
        return Err("fixture bound".into());
    }
    let raw = fs::read(path)?;
    if sha(&raw) != digest {
        return Err("fixture changed".into());
    }
    Ok(raw)
}
fn domain() -> Result<FormControlLimits, AnyError> {
    Ok(FormControlLimits::new(FormControlLimitConfig::default())?)
}
struct Fixture {
    raw: Vec<u8>,
    map: NativeFormPackageMap,
    policies: Vec<NativeFormPackagePolicy>,
}
fn fixture(index: usize) -> Result<Fixture, AnyError> {
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
    let manifest: Value = serde_json::from_slice(&checked(&root.join(MANIFEST), MANIFEST_SHA)?)?;
    let case = &manifest["cases"][index];
    let count = if index < 2 { 2 } else { 1 };
    let mapping = NativeFormPackageMap {
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
    };
    if serde_json::to_value(&mapping)? != case["complete_map"] {
        return Err("fixture map changed".into());
    }
    let parent = root
        .join(MANIFEST)
        .parent()
        .ok_or("manifest parent")?
        .to_owned();
    let raw = checked(
        &parent.join(case["file"].as_str().ok_or("input name")?),
        case["package_sha256"].as_str().ok_or("input sha")?,
    )?;
    let observed =
        NativeFormPackageReader::read(&raw, &mapping, NativeFormPackageLimits::default())?;
    let policy: Vec<_> = observed
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
                    radio_group_name: radio_group_name.clone().ok_or("group")?,
                    group_required: true,
                    tri_state: *tri_state,
                    back_style: *back_style,
                },
                _ => return Err("unsupported fixture".into()),
            };
            Ok(NativeFormPackagePolicy {
                identity: c.component_identity.clone(),
                payload,
            })
        })
        .collect::<Result<_, AnyError>>()?;
    if sha(&serde_json::to_vec(&policy)?) != case["policy_sha256"].as_str().ok_or("policy sha")? {
        return Err("caller fixture policy changed".into());
    }
    Ok(Fixture {
        raw,
        map: mapping,
        policies: policy,
    })
}
fn intent(f: &Fixture, rgb: u32) -> NativeFormColorRequest {
    NativeFormColorRequest {
        target: f.map.sections[0].map.component_controls[0].clone(),
        foreground_rgb: rgb,
    }
}
fn context(f: &Fixture) -> Result<FormColorContext<'_>, AnyError> {
    Ok(FormColorContext::bind(
        &f.raw,
        &f.map,
        &f.policies,
        FormColorPreparationLimits::bounded_default()?,
    )?)
}
#[test]
fn real_product_preparation_matches_whole_public_sdk_for_all_fifteen_inputs_but_denies_signed_route()
-> Result<(), AnyError> {
    for index in 0..15 {
        let f = fixture(index)?;
        let c = context(&f)?;
        let requests = [intent(&f, 0x00AB_CDEF)];
        let prepared = FormColorPreparation::prepare(&c, &requests)?;
        let plan = NativeFormColorPlan::bind(
            &f.raw,
            &f.map,
            &f.policies,
            &requests,
            domain()?,
            NativeFormPackageLimits::default(),
        )?;
        let direct = NativeFormColorPreparer::prepare(
            &f.raw,
            &plan,
            domain()?,
            NativeFormPackageLimits::default(),
            NativeFormColorLimits::default(),
        )?;
        assert!(direct.bytes() == prepared.candidate_bytes());
        assert_eq!(&prepared.receipt().component, direct.receipt());
        assert_eq!(prepared.verify(&c)?, *prepared.receipt());
        assert_eq!(
            prepared.require_current_product_route(&c),
            Err(FormColorPreparationError::RouteUnqualified)
        );
        assert_eq!(
            prepared.receipt().component.actual_native_validation,
            "not_run"
        );
    }
    Ok(())
}
#[test]
fn fresh_full_source_and_valid_map_policy_substitution_invalidate_old_preparation()
-> Result<(), AnyError> {
    let f = fixture(2)?;
    let c = context(&f)?;
    let prepared = FormColorPreparation::prepare(&c, &[intent(&f, 1)])?;
    let changed = fixture(3)?;
    let fresh = context(&changed)?;
    assert_eq!(
        prepared.verify(&fresh),
        Err(FormColorPreparationError::Drift)
    );
    let mut mapped = Fixture {
        raw: f.raw.clone(),
        map: f.map.clone(),
        policies: f.policies.clone(),
    };
    let identity = LogicalId::parse("different-provider-control")?;
    mapped.map.sections[0].map.component_controls[0].logical_control_id = identity.clone();
    mapped.policies[0].identity.logical_control_id = identity;
    let fresh = context(&mapped)?;
    assert_eq!(
        prepared.verify(&fresh),
        Err(FormColorPreparationError::Drift)
    );
    Ok(())
}
#[test]
fn empty_duplicate_unknown_and_out_of_range_product_intents_fail_closed() -> Result<(), AnyError> {
    let f = fixture(2)?;
    let c = context(&f)?;
    let one = intent(&f, 1);
    let mut wrong = one.clone();
    wrong.target.native_object_id += 1;
    for requests in [
        vec![],
        vec![one.clone(), one],
        vec![wrong],
        vec![intent(&f, 0x0100_0000)],
    ] {
        assert_eq!(
            FormColorPreparation::prepare(&c, &requests).err(),
            Some(FormColorPreparationError::Request)
        );
    }
    Ok(())
}
#[test]
fn canonical_retry_and_redacted_receipts_are_not_publication_or_product_idempotency()
-> Result<(), AnyError> {
    let f = fixture(2)?;
    let c = context(&f)?;
    let requests = [intent(&f, 1)];
    let a = FormColorPreparation::prepare(&c, &requests)?;
    let b = FormColorPreparation::prepare(&c, &requests)?;
    assert!(a.candidate_bytes() == b.candidate_bytes());
    assert_eq!(a.receipt(), b.receipt());
    let other = FormColorPreparation::prepare(&c, &[intent(&f, 2)])?;
    assert_ne!(
        a.receipt().typed_request_sha256,
        other.receipt().typed_request_sha256
    );
    let serialized = serde_json::to_string(a.receipt())?;
    let debug = format!("{a:?} {c:?}");
    for value in [
        "P08FORMINSERT",
        "section-0-control",
        "Contents/section0.xml",
    ] {
        assert!(!serialized.contains(value));
        assert!(!debug.contains(value));
    }
    assert_eq!(
        a.receipt().qualification,
        "product_preparation_only_route_native_and_gate_unqualified"
    );
    Ok(())
}
