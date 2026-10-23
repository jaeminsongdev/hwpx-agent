//! Immutable historical note inputs. No native activation or user documents.
use sha2::{Digest as _, Sha256};
use std::{error::Error, path::PathBuf};

pub struct LockedNoteInput {
    pub bytes: Vec<u8>,
    pub expected_notes: usize,
    pub lane: &'static str,
}
fn read(path: PathBuf, bytes: Option<u64>, sha: &str) -> Result<Vec<u8>, Box<dyn Error>> {
    let metadata = std::fs::symlink_metadata(&path)?;
    if !metadata.is_file()
        || metadata.file_type().is_symlink()
        || metadata.len() > 32 * 1024 * 1024
        || bytes.is_some_and(|expected| expected != metadata.len())
    {
        return Err("locked note input type/size drift".into());
    }
    let input = std::fs::read(path)?;
    if hex::encode(Sha256::digest(&input)) != sha {
        return Err("locked note input digest drift".into());
    }
    Ok(input)
}
pub fn actual_inputs() -> Result<Vec<LockedNoteInput>, Box<dyn Error>> {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
    let bundle = root.join("fixtures/target-build/p09-24-note-target-20261002-03/output");
    let manifest: serde_json::Value = serde_json::from_slice(&read(
        bundle.join("fixture-manifest.json"),
        None,
        "ef2e30388827c40e02b99017350f434b33840ce5564c2d46b2bae9c10dac9150",
    )?)?;
    let native: serde_json::Value = serde_json::from_slice(&read(root.join(
        "implementation/p09/evidence/p09-26-note-native-batch-qualification.current-2020.v1.json"), None,
        "a03e6461d94010d7b1ccfbf9eecdb8e1d06389f3a690363e7b414d4cda9f2347")?)?;
    if native["state"] != "failed_semantic_non_green" || native["claims"]["green_rows"] != 0 {
        return Err("historical failed note evidence was relabelled".into());
    }
    let mut inputs = Vec::new();
    for case in manifest["cases"].as_array().ok_or("note cases")? {
        let id = case["case_id"].as_str().ok_or("note case id")?;
        let slot = match id {
            "P09-24-C01" => "p09-17-field-auto-number-target-p09-24-20261002-c01-attempt01",
            "P09-24-C02" => "p09-17-field-auto-number-target-p09-24-20261002-c02-attempt01",
            "P09-24-C03" => "p09-17-field-auto-number-target-p09-24-20261002-c03-attempt01",
            _ => return Err("unknown locked note case".into()),
        };
        let expected_notes = usize::try_from(case["note_count"].as_u64().ok_or("note count")?)?;
        inputs.push(LockedNoteInput {
            bytes: read(
                bundle.join(case["file"].as_str().ok_or("note filename")?),
                Some(case["package_bytes"].as_u64().ok_or("note package bytes")?),
                case["package_sha256"].as_str().ok_or("note package sha")?,
            )?,
            expected_notes,
            lane: "generated",
        });
        let actual = native["cases"]
            .as_array()
            .ok_or("native cases")?
            .iter()
            .find(|v| v["case_id"] == id)
            .ok_or("native case")?;
        if actual["state"] != "failed_semantic_non_green" {
            return Err("native note failure relabelled".into());
        }
        for lane in ["saved", "reopened"] {
            let snapshot = &actual["snapshots"][lane];
            inputs.push(LockedNoteInput {
                bytes: read(
                    root.join("implementation/p09/evidence/private")
                        .join(slot)
                        .join(format!("{lane}.hwpx")),
                    Some(
                        snapshot["package_bytes"]
                            .as_u64()
                            .ok_or("native package bytes")?,
                    ),
                    snapshot["package_sha256"]
                        .as_str()
                        .ok_or("native package sha")?,
                )?,
                expected_notes,
                lane,
            });
        }
    }
    if inputs.len() != 9 {
        return Err("incomplete locked note corpus".into());
    }
    Ok(inputs)
}
