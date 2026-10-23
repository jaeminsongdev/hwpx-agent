//! Historical actual bytes -> actual source-backed typed field meanings, never native execution.
use domain_ir::DocumentId;
use hwpx_package::document_import::{
    ImportedSourcePackage, SourceImportLimits,
    fields::{
        ImportedDocumentFields,
        semantics::{FieldSemanticImportReceipt, ImportedDocumentFieldSemantics},
    },
    forms::ImportedDocumentForms,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use std::{
    collections::BTreeMap,
    error::Error,
    path::{Path, PathBuf},
};

#[derive(Serialize)]
struct Evidence {
    profile: &'static str,
    actual_packages: usize,
    actual_field_ranges: usize,
    observed_kind_counts: BTreeMap<String, usize>,
    receipts: Vec<FieldSemanticImportReceipt>,
    native_activated: bool,
    approval_evaluations_policy_or_full_import_qualified: bool,
    p09_complete: bool,
}
fn read_locked(path: &Path, size: u64, sha: &str) -> Result<Vec<u8>, Box<dyn Error>> {
    let meta = std::fs::symlink_metadata(path)?;
    if !meta.is_file()
        || meta.file_type().is_symlink()
        || meta.len() != size
        || size > 32 * 1024 * 1024
    {
        return Err("locked actual input type or size drift".into());
    }
    let bytes = std::fs::read(path)?;
    if hex::encode(Sha256::digest(&bytes)) != sha {
        return Err("locked actual input digest drift".into());
    }
    Ok(bytes)
}
fn consume(bytes: &[u8], e: &mut Evidence) -> Result<(), Box<dyn Error>> {
    let forms = ImportedDocumentForms::import(ImportedSourcePackage::import(
        bytes,
        DocumentId::parse("actual-field-meaning-probe")?,
        Sha256::digest(bytes).into(),
        SourceImportLimits::default(),
    )?)?;
    let ranges = ImportedDocumentFields::import(&forms)?;
    let fields = ImportedDocumentFieldSemantics::import(&ranges)?;
    if fields.verify_source(bytes)? != *fields.receipt() {
        return Err("actual whole fresh range graph drift".into());
    }
    for f in ranges.fields() {
        if forms
            .source()
            .resolve_anchor(&f.begin_anchor)?
            .element()
            .is_none()
            || forms
                .source()
                .resolve_anchor(&f.end_anchor)?
                .element()
                .is_none()
        {
            return Err("actual field marker anchor missing".into());
        }
        *e.observed_kind_counts
            .entry(f.native_kind.clone())
            .or_default() += 1;
    }
    e.actual_packages += 1;
    e.actual_field_ranges += fields.observations().len();
    e.receipts.push(fields.receipt().clone());
    Ok(())
}
fn main() -> Result<(), Box<dyn Error>> {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
    let mut e = Evidence {
        profile: "hwpx-agent.document-import-field-semantics-probe/partial-v1",
        actual_packages: 0,
        actual_field_ranges: 0,
        observed_kind_counts: BTreeMap::new(),
        receipts: vec![],
        native_activated: false,
        approval_evaluations_policy_or_full_import_qualified: false,
        p09_complete: false,
    };
    let captured=read_locked(&root.join("implementation/p09/evidence/private/p09-14-hyperlink-discovery-20260912-attempt02/after.hwpx"),
        15097,"feb312b974de2dd7d0275e6043e927ea5cf8348cfc0a04b44045e0bf669d4480")?;
    consume(&captured, &mut e)?;
    let manifest = read_locked(
        &root.join(
            "implementation/p06/evidence/target/p06-table-aggregate.current-2020.attempt02.v2.json",
        ),
        std::fs::metadata(root.join(
            "implementation/p06/evidence/target/p06-table-aggregate.current-2020.attempt02.v2.json",
        ))?
        .len(),
        "edc71d554e0975d511ffe6f0de1b140a30ca932d0bf2b9c7b70517c5e8674fc5",
    )?;
    let manifest: serde_json::Value = serde_json::from_slice(&manifest)?;
    let cases = manifest["cases"].as_array().ok_or("actual table cases")?;
    if cases.len() != 8 {
        return Err("actual table case count".into());
    }
    for row in cases {
        for kind in ["input", "output"] {
            let relative = row[kind]["path"].as_str().ok_or("actual table path")?;
            if Path::new(relative).is_absolute()
                || Path::new(relative)
                    .components()
                    .any(|c| matches!(c, std::path::Component::ParentDir))
            {
                return Err("actual table path scope".into());
            }
            let bytes = read_locked(
                &root.join(relative),
                row[kind]["bytes"].as_u64().ok_or("actual table bytes")?,
                row[kind]["sha256"].as_str().ok_or("actual table SHA")?,
            )?;
            consume(&bytes, &mut e)?;
        }
    }
    if e.actual_packages != 17 {
        return Err("actual corpus count".into());
    }
    println!("{}", serde_json::to_string(&e)?);
    Ok(())
}
