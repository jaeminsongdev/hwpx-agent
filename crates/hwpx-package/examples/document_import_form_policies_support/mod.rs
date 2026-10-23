//! Explicit FIXTURE caller choices, never a real policy-provider or native default oracle.
use std::{error::Error, path::PathBuf};

use domain_ir::{FormButtonValue, FormSelectionValidation, FormTextValidation, NativeFormTag};
use hwpx_package::document_import::forms::{
    ImportedDocumentForms,
    policies::{ExplicitFormPolicy, SourceFormPolicy},
};
use sha2::{Digest as _, Sha256};

pub fn fixture_manifest() -> Result<(PathBuf, serde_json::Value), Box<dyn Error>> {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../fixtures/target-build/p09-42-product-form-values-01/output");
    let bytes = std::fs::read(root.join("fixture-manifest.json"))?;
    if hex::encode(Sha256::digest(&bytes))
        != "8208bff3f87a4e56ec68caecaf41b00c3fdccc5b3f083289f3c13ccede19466e"
    {
        return Err("fixture manifest drift".into());
    }
    Ok((root, serde_json::from_slice(&bytes)?))
}
pub fn fixture_bytes(case: &str, kind: &str) -> Result<Vec<u8>, Box<dyn Error>> {
    let (root, manifest) = fixture_manifest()?;
    let row = manifest["cases"]
        .as_array()
        .ok_or("cases")?
        .iter()
        .find(|r| r["case"] == case)
        .ok_or("case")?;
    let entry = &row[kind];
    let name = entry["path"].as_str().ok_or("path")?;
    if name.contains(['/', '\\', ':']) {
        return Err("fixture name".into());
    }
    let path = root.join(name);
    let metadata = std::fs::symlink_metadata(&path)?;
    if !metadata.is_file() || metadata.file_type().is_symlink() || metadata.len() > 32 * 1024 * 1024
    {
        return Err("fixture type or bound".into());
    }
    let bytes = std::fs::read(path)?;
    if bytes.len() as u64 != entry["bytes"].as_u64().ok_or("bytes")?
        || hex::encode(Sha256::digest(&bytes)) != entry["sha256"].as_str().ok_or("sha")?
    {
        return Err("fixture drift".into());
    }
    Ok(bytes)
}

/// Deliberately selected fixture-only policy: empty/unchecked/no selection,
/// optional values and no external validator. These are NOT read from HWPX.
pub fn explicit_test_policies(imported: &ImportedDocumentForms) -> Vec<SourceFormPolicy> {
    imported
        .forms()
        .iter()
        .map(|form| SourceFormPolicy {
            node_id: form.node_id.clone(),
            source_anchor: form.source_anchor.clone(),
            values: match form.tag {
                NativeFormTag::Edit => ExplicitFormPolicy::Text {
                    default_value: String::new(),
                    validation: FormTextValidation {
                        required: false,
                        minimum_characters: 0,
                        maximum_characters: None,
                        external_validator_sha256: None,
                    },
                },
                NativeFormTag::CheckBtn => ExplicitFormPolicy::Checkbox {
                    default_value: FormButtonValue::Unchecked,
                    must_be_checked: false,
                },
                NativeFormTag::RadioBtn => ExplicitFormPolicy::Radio {
                    default_value: FormButtonValue::Unchecked,
                    group_required: false,
                },
                NativeFormTag::ComboBox => ExplicitFormPolicy::Combo {
                    default_selected_value: None,
                    validation: optional_selection(),
                },
                NativeFormTag::ListBox => ExplicitFormPolicy::List {
                    default_selected_value: None,
                    validation: optional_selection(),
                },
            },
        })
        .collect()
}
fn optional_selection() -> FormSelectionValidation {
    FormSelectionValidation {
        required: false,
        external_validator_sha256: None,
    }
}
