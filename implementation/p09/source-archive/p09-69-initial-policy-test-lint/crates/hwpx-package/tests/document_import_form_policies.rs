use std::error::Error;

use domain_ir::{
    DocumentGraph, DocumentGraphLimits, DocumentId, Flow, FormButtonValue, FormControlIdentity,
    FormControlLimitConfig, FormControlLimits, FormControlPayload, LogicalId, NativeFormTag, Node,
    Properties, PropertyValue,
};
use hwpx_package::{
    NativeFormHwpxMap, NativeFormObservedIdentity, NativeFormObservedPayload,
    NativeFormPackageLimits, NativeFormPackageMap, NativeFormPackagePolicy,
    NativeFormPackageReader, NativeFormPackageSectionMap,
    document_import::{
        ImportedSourcePackage, SourceImportLimits,
        forms::{
            ImportedDocumentForms,
            policies::{
                COMPONENT_IDENTITY_SCOPE, ExplicitFormPolicy, FormPolicyBindingError,
                FormPolicySourceBinding, PolicyBoundDocumentForms,
            },
        },
    },
};
use sha2::{Digest as _, Sha256};

#[path = "../examples/document_import_form_policies_support/mod.rs"]
mod support;
use support::{explicit_test_policies, fixture_bytes, fixture_manifest};
type TestResult = Result<(), Box<dyn Error>>;

fn import(bytes: &[u8], document: &str) -> Result<ImportedDocumentForms, Box<dyn Error>> {
    Ok(ImportedDocumentForms::import(
        ImportedSourcePackage::import(
            bytes,
            DocumentId::parse(document)?,
            Sha256::digest(bytes).into(),
            SourceImportLimits::default(),
        )?,
    )?)
}
fn original_map(imported: &ImportedDocumentForms) -> Result<NativeFormPackageMap, Box<dyn Error>> {
    let mut sections = Vec::new();
    let mut next = 0;
    for path in imported
        .source()
        .spine()
        .iter()
        .filter(|p| p.as_str() != "Contents/header.xml")
    {
        let part = imported
            .source()
            .parts()
            .iter()
            .find(|p| p.path() == path)
            .ok_or("part")?;
        let mut map = NativeFormHwpxMap {
            paragraph_ids: vec![],
            component_controls: vec![],
        };
        for (index, element) in part.xml().ok_or("xml")?.elements().iter().enumerate() {
            if element.name().namespace() != Some("http://www.hancom.co.kr/hwpml/2011/paragraph") {
                continue;
            }
            let id = LogicalId::parse(format!(
                "node-{}",
                part.element_anchor(index)
                    .ok_or("anchor")?
                    .opaque_handle
                    .as_str()
            ))?;
            match element.name().local_name() {
                "p" => map.paragraph_ids.push(id),
                "edit" | "checkBtn" | "radioBtn" | "comboBox" | "listBox" => {
                    next += 1;
                    map.component_controls.push(FormControlIdentity {
                        logical_control_id: id,
                        native_object_id: next,
                    });
                }
                _ => {}
            }
        }
        sections.push(NativeFormPackageSectionMap {
            part: path.as_str().into(),
            map,
        });
    }
    Ok(NativeFormPackageMap { sections })
}
fn check_nodes(bound: &PolicyBoundDocumentForms<'_>, flow: &Flow, nodes: &mut usize) -> TestResult {
    for node in &flow.children {
        match node {
            Node::FormControl(form) => {
                let state = bound
                    .state()
                    .controls()
                    .iter()
                    .find(|s| s.identity.logical_control_id == form.common.node_id)
                    .ok_or("state")?;
                let json = serde_json::to_string(state)?;
                assert!(
                    form.properties
                        .iter()
                        .any(|(k, v)| k == "complete_control_state_json"
                            && v == &PropertyValue::Text(json.clone()))
                );
                assert!(
                    form.properties
                        .iter()
                        .any(|(k, v)| k == "component_identity_scope"
                            && v == &PropertyValue::Text(COMPONENT_IDENTITY_SCOPE.into()))
                );
                assert_eq!(form.control_kind, state.payload.capability_id());
                *nodes += 1;
            }
            Node::Table(table) => {
                for cell in &table.cells {
                    check_nodes(bound, &cell.body, nodes)?;
                }
            }
            Node::Drawing(drawing) => check_nodes(bound, &drawing.children, nodes)?,
            _ => {}
        }
    }
    Ok(())
}

#[test]
fn ten_locked_actual_packages_bind_complete_form_states_via_unchanged_native_reader() -> TestResult
{
    let (_, manifest) = fixture_manifest()?;
    let mut count = 0;
    let mut controls = 0;
    for row in manifest["cases"].as_array().ok_or("cases")? {
        for kind in ["source", "output"] {
            let bytes = fixture_bytes(row["case"].as_str().ok_or("case")?, kind)?;
            let imported = import(&bytes, "explicit-policy-test")?;
            let binding = FormPolicySourceBinding::for_imported(&imported);
            let policies = explicit_test_policies(&imported);
            let bound = PolicyBoundDocumentForms::bind(&imported, &binding, &policies)?;
            assert_eq!(
                bound.verify_source(&bytes, &binding, &policies)?,
                *bound.receipt()
            );
            // Independent public original package API checks all actual common,
            // values, anchors, catalogs/resources/refs/protection/opaque hashes.
            let readback = NativeFormPackageReader::read(
                &bytes,
                &original_map(&imported)?,
                NativeFormPackageLimits::default(),
            )?;
            let native: Vec<_> = bound
                .state()
                .controls()
                .iter()
                .map(|s| NativeFormPackagePolicy {
                    identity: s.identity.clone(),
                    payload: s.payload.clone(),
                })
                .collect();
            let limits = FormControlLimits::new(FormControlLimitConfig::default())?;
            assert_eq!(readback.bind_policies(&native, limits)?, *bound.state());
            readback.verify_domain_state(bound.state(), &native, limits)?;
            assert_eq!(
                bound.receipt().legacy_reference_state,
                "id_index_validation_failed"
            );
            assert_eq!(
                bound.receipt().verified_native_reference_overlay_issues,
                imported.receipt().verified_native_reference_overlay_issues
            );
            let mut nodes = 0;
            for section in bound.graph().sections() {
                check_nodes(&bound, &section.body, &mut nodes)?;
            }
            assert_eq!(nodes, imported.forms().len());
            controls += nodes;
            count += 1;
        }
    }
    assert_eq!((count, controls), (10, 50));
    Ok(())
}

#[test]
fn every_policy_envelope_identity_and_digest_is_checked() -> TestResult {
    let imported = import(
        &fixture_bytes("five-kinds", "source")?,
        "explicit-policy-test",
    )?;
    let binding = FormPolicySourceBinding::for_imported(&imported);
    let policies = explicit_test_policies(&imported);
    for field in 0..4 {
        let mut wrong = binding.clone();
        match field {
            0 => wrong.document_id = DocumentId::parse("other-document")?,
            1 => wrong.source_package_sha256[0] ^= 1,
            2 => wrong.source_provenance_sha256[0] ^= 1,
            _ => wrong.observed_graph_sha256[0] ^= 1,
        }
        assert!(matches!(
            PolicyBoundDocumentForms::bind(&imported, &wrong, &policies),
            Err(FormPolicyBindingError::Binding)
        ));
    }
    let bytes = fixture_bytes("five-kinds", "source")?;
    let other = import(&bytes, "other-document")?;
    assert!(PolicyBoundDocumentForms::bind(&other, &binding, &policies).is_err());
    Ok(())
}

#[test]
fn missing_extra_duplicate_reordered_and_wrong_anchor_policy_sets_are_rejected() -> TestResult {
    let imported = import(
        &fixture_bytes("five-kinds", "source")?,
        "explicit-policy-test",
    )?;
    let binding = FormPolicySourceBinding::for_imported(&imported);
    let policies = explicit_test_policies(&imported);
    for variant in 0..7 {
        let mut wrong = policies.clone();
        match variant {
            0 => {
                wrong.pop();
            }
            1 => wrong.push(wrong[0].clone()),
            2 => wrong[1] = wrong[0].clone(),
            3 => wrong.swap(0, 1),
            4 => wrong[0].node_id = LogicalId::parse("unknown-form")?,
            5 => wrong[0].source_anchor.fingerprint_sha256[0] ^= 1,
            _ => {
                wrong[0].source_anchor.opaque_handle = wrong[1].source_anchor.opaque_handle.clone()
            }
        }
        assert!(matches!(
            PolicyBoundDocumentForms::bind(&imported, &binding, &wrong),
            Err(FormPolicyBindingError::Binding)
        ));
    }
    Ok(())
}

#[test]
fn policy_kinds_cannot_change_observed_native_form_types() -> TestResult {
    let imported = import(
        &fixture_bytes("five-kinds", "source")?,
        "explicit-policy-test",
    )?;
    let binding = FormPolicySourceBinding::for_imported(&imported);
    let policies = explicit_test_policies(&imported);
    for (index, form) in imported.forms().iter().enumerate() {
        let mut wrong = policies.clone();
        let other = policies
            .iter()
            .zip(imported.forms())
            .find(|(_, o)| o.tag != form.tag)
            .ok_or("other kind")?;
        wrong[index].values = other.0.values.clone();
        assert!(matches!(
            PolicyBoundDocumentForms::bind(&imported, &binding, &wrong),
            Err(FormPolicyBindingError::Kind)
        ));
    }
    Ok(())
}

#[test]
fn original_domain_rejects_invalid_defaults_validation_and_external_digest() -> TestResult {
    let imported = import(
        &fixture_bytes("five-kinds", "source")?,
        "explicit-policy-test",
    )?;
    let binding = FormPolicySourceBinding::for_imported(&imported);
    let policies = explicit_test_policies(&imported);
    for variant in 0..5 {
        let mut wrong = policies.clone();
        for policy in &mut wrong {
            match (&mut policy.values, variant) {
                (ExplicitFormPolicy::Text { validation, .. }, 0) => {
                    validation.maximum_characters = Some(0)
                }
                (ExplicitFormPolicy::Text { validation, .. }, 1) => {
                    validation.external_validator_sha256 = Some("invalid".into())
                }
                (ExplicitFormPolicy::Text { default_value, .. }, 2) => *default_value = "\0".into(),
                (
                    ExplicitFormPolicy::Combo {
                        default_selected_value,
                        ..
                    },
                    3,
                ) => *default_selected_value = Some("\0".into()),
                (
                    ExplicitFormPolicy::List {
                        default_selected_value,
                        ..
                    },
                    4,
                ) => *default_selected_value = Some("not-an-observed-item".into()),
                _ => {}
            }
        }
        assert!(
            matches!(
                PolicyBoundDocumentForms::bind(&imported, &binding, &wrong),
                Err(FormPolicyBindingError::Native(_))
            ),
            "invalid policy variant {variant}"
        );
    }
    Ok(())
}

#[test]
fn editable_combo_preserves_original_custom_default_semantics() -> TestResult {
    let imported = import(
        &fixture_bytes("five-kinds", "source")?,
        "explicit-policy-test",
    )?;
    let binding = FormPolicySourceBinding::for_imported(&imported);
    let mut policies = explicit_test_policies(&imported);
    let index = imported
        .forms()
        .iter()
        .position(|o| {
            matches!(
                o.payload,
                NativeFormObservedPayload::Combo {
                    edit_enable: true,
                    ..
                }
            )
        })
        .ok_or("actual editable combo")?;
    if let ExplicitFormPolicy::Combo {
        default_selected_value,
        ..
    } = &mut policies[index].values
    {
        *default_selected_value = Some("explicit-caller-custom-default".into());
    }
    let bound = PolicyBoundDocumentForms::bind(&imported, &binding, &policies)?;
    let control = bound
        .state()
        .controls()
        .iter()
        .find(|c| c.identity.logical_control_id == policies[index].node_id)
        .ok_or("combo state")?;
    assert!(matches!(&control.payload, FormControlPayload::Combo {
        edit_enable: true, default_selected_value: Some(value), ..
    } if value == "explicit-caller-custom-default"));
    Ok(())
}

#[test]
fn radio_defaults_and_required_policy_validate_as_a_complete_global_group() -> TestResult {
    let imported = import(
        &fixture_bytes("five-kinds", "source")?,
        "explicit-policy-test",
    )?;
    let binding = FormPolicySourceBinding::for_imported(&imported);
    let mut policies = explicit_test_policies(&imported);
    let radios: Vec<_> = imported
        .forms()
        .iter()
        .enumerate()
        .filter(|(_, o)| o.tag == NativeFormTag::RadioBtn)
        .map(|(i, _)| i)
        .collect();
    assert_eq!(radios.len(), 2);
    for &index in &radios {
        if let ExplicitFormPolicy::Radio { default_value, .. } = &mut policies[index].values {
            *default_value = FormButtonValue::Checked;
        }
    }
    assert!(matches!(
        PolicyBoundDocumentForms::bind(&imported, &binding, &policies),
        Err(FormPolicyBindingError::Native(_))
    ));
    policies = explicit_test_policies(&imported);
    if let ExplicitFormPolicy::Radio { group_required, .. } = &mut policies[radios[0]].values {
        *group_required = true;
    }
    assert!(matches!(
        PolicyBoundDocumentForms::bind(&imported, &binding, &policies),
        Err(FormPolicyBindingError::Native(_))
    ));
    Ok(())
}

#[test]
fn policy_changes_are_explicit_not_native_default_inference() -> TestResult {
    let bytes = fixture_bytes("five-kinds", "source")?;
    let imported = import(&bytes, "explicit-policy-test")?;
    let binding = FormPolicySourceBinding::for_imported(&imported);
    let mut policies = explicit_test_policies(&imported);
    let first = PolicyBoundDocumentForms::bind(&imported, &binding, &policies)?;
    let text = policies
        .iter_mut()
        .find(|p| matches!(p.values, ExplicitFormPolicy::Text { .. }))
        .ok_or("text")?;
    if let ExplicitFormPolicy::Text { validation, .. } = &mut text.values {
        validation.external_validator_sha256 = Some("ab".repeat(32));
    }
    let second = PolicyBoundDocumentForms::bind(&imported, &binding, &policies)?;
    assert_ne!(
        first.receipt().policy_sha256,
        second.receipt().policy_sha256
    );
    assert_ne!(first.receipt().state_sha256, second.receipt().state_sha256);
    assert_ne!(first.receipt().graph_sha256, second.receipt().graph_sha256);
    assert_eq!(
        first.receipt().native_binding_sha256,
        second.receipt().native_binding_sha256
    );
    assert_eq!(first.receipt().source, second.receipt().source);
    assert!(first.verify_source(&bytes, &binding, &policies).is_err());
    // A syntactically valid digest is a caller policy value, NOT proof that an
    // actual external validator was invoked or authorized.
    assert!(second.receipt().qualification.contains("not_authoritative"));
    Ok(())
}

#[test]
fn fresh_package_drift_cannot_rebind_existing_policy_state() -> TestResult {
    let bytes = fixture_bytes("actual", "source")?;
    let imported = import(&bytes, "explicit-policy-test")?;
    let binding = FormPolicySourceBinding::for_imported(&imported);
    let policies = explicit_test_policies(&imported);
    let bound = PolicyBoundDocumentForms::bind(&imported, &binding, &policies)?;
    assert!(
        bound
            .verify_source(&fixture_bytes("actual", "output")?, &binding, &policies)
            .is_err()
    );
    let other = import(&fixture_bytes("actual", "output")?, "explicit-policy-test")?;
    assert!(PolicyBoundDocumentForms::bind(&other, &binding, &policies).is_err());
    Ok(())
}

#[test]
fn policy_budget_is_enforced_before_cloning_or_merging_untrusted_strings() -> TestResult {
    let imported = import(
        &fixture_bytes("five-kinds", "source")?,
        "explicit-policy-test",
    )?;
    let binding = FormPolicySourceBinding::for_imported(&imported);
    let mut policies = explicit_test_policies(&imported);
    let text = policies
        .iter_mut()
        .find(|p| matches!(p.values, ExplicitFormPolicy::Text { .. }))
        .ok_or("text")?;
    if let ExplicitFormPolicy::Text { default_value, .. } = &mut text.values {
        *default_value = "x".repeat(1024 * 1024);
    }
    assert!(matches!(
        PolicyBoundDocumentForms::bind(&imported, &binding, &policies),
        Err(FormPolicyBindingError::Budget)
    ));
    Ok(())
}

#[test]
fn component_reservations_remain_distinct_from_observed_missing_native_identity() -> TestResult {
    let imported = import(
        &fixture_bytes("five-kinds", "source")?,
        "explicit-policy-test",
    )?;
    let bound = PolicyBoundDocumentForms::bind(
        &imported,
        &FormPolicySourceBinding::for_imported(&imported),
        &explicit_test_policies(&imported),
    )?;
    assert_eq!(
        bound.receipt().component_identity_scope,
        COMPONENT_IDENTITY_SCOPE
    );
    assert!(
        imported
            .forms()
            .iter()
            .any(|o| o.native_identity == NativeFormObservedIdentity::Missing)
    );
    for (observed, state) in imported.forms().iter().zip(bound.state().controls()) {
        assert_eq!(observed.node_id, state.identity.logical_control_id);
        assert_ne!(state.identity.native_object_id, 0);
        let json = serde_json::to_value(observed)?;
        assert!(json.get("native_object_id").is_none());
        assert!(json.get("component_identity").is_none());
        // Current native values remain read-only original facts.
        if let (
            NativeFormObservedPayload::Text { value: actual, .. },
            FormControlPayload::Text { value, .. },
        ) = (&observed.payload, &state.payload)
        {
            assert_eq!(actual, value);
        }
    }
    Ok(())
}

fn remove_added(flow: &mut Flow) {
    for node in &mut flow.children {
        match node {
            Node::FormControl(form) => {
                let mut properties = Properties::new();
                for (key, value) in form.properties.iter() {
                    if ![
                        "complete_control_state_json",
                        "component_identity_scope",
                        "policy_qualification",
                    ]
                    .contains(&key)
                    {
                        properties.insert(key, value.clone());
                    }
                }
                form.properties = properties;
            }
            Node::Table(table) => {
                for cell in &mut table.cells {
                    remove_added(&mut cell.body);
                }
            }
            Node::Drawing(drawing) => remove_added(&mut drawing.children),
            _ => {}
        }
    }
}
#[test]
fn every_non_policy_graph_field_and_source_binding_is_preserved_exactly() -> TestResult {
    let imported = import(
        &fixture_bytes("five-kinds", "source")?,
        "explicit-policy-test",
    )?;
    let bound = PolicyBoundDocumentForms::bind(
        &imported,
        &FormPolicySourceBinding::for_imported(&imported),
        &explicit_test_policies(&imported),
    )?;
    let mut reversed = bound.graph().clone().into_draft();
    for section in &mut reversed.sections {
        remove_added(&mut section.body);
    }
    let mut metadata = Properties::new();
    for (key, value) in reversed.metadata.iter() {
        if !key.starts_with("native_form_policy_") {
            metadata.insert(key, value.clone());
        }
    }
    reversed.metadata = metadata;
    assert_eq!(
        DocumentGraph::from_draft(reversed, DocumentGraphLimits::default())?,
        *imported.graph()
    );
    Ok(())
}

#[test]
fn no_form_import_does_not_fabricate_native_policy_attestation() -> TestResult {
    let bytes = hwpx_package::Hancom2020Vs0Builder::build("NO FORMS")?
        .with_verified_bytes(<[u8]>::to_vec)?;
    let imported = import(&bytes, "explicit-policy-test")?;
    assert!(matches!(
        PolicyBoundDocumentForms::bind(
            &imported,
            &FormPolicySourceBinding::for_imported(&imported),
            &[]
        ),
        Err(FormPolicyBindingError::NoForms)
    ));
    assert_eq!(imported.receipt().native_binding_sha256, None);
    assert_eq!(imported.verify_source(&bytes)?, *imported.receipt());
    Ok(())
}

#[test]
fn debug_and_public_receipts_do_not_print_policy_or_document_values() -> TestResult {
    let imported = import(
        &fixture_bytes("five-kinds", "source")?,
        "explicit-policy-test",
    )?;
    let binding = FormPolicySourceBinding::for_imported(&imported);
    let policies = explicit_test_policies(&imported);
    let bound = PolicyBoundDocumentForms::bind(&imported, &binding, &policies)?;
    assert_eq!(format!("{bound:?}"), "PolicyBoundDocumentForms(<redacted>)");
    assert_eq!(format!("{:?}", policies[0]), "SourceFormPolicy(<redacted>)");
    assert_eq!(
        format!("{:?}", policies[0].values),
        "ExplicitFormPolicy(<redacted>)"
    );
    let receipt = serde_json::to_value(bound.receipt())?;
    assert!(receipt.get("policies").is_none());
    assert!(receipt.get("state").is_none());
    assert!(receipt.get("graph").is_none());
    Ok(())
}
