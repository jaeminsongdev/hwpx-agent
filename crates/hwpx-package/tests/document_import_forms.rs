use std::{
    collections::BTreeMap,
    error::Error,
    io::{Cursor, Read as _, Write as _},
    path::PathBuf,
};

use domain_ir::{
    DocumentGraph, DocumentGraphLimits, DocumentId, Flow, LogicalId, NativeFormTag, Node,
};
use hwpx_package::{
    NativeFormObservedIdentity, NativeFormPackageError,
    document_import::{
        ImportedSourcePackage, SourceImportLimits,
        forms::{FormImportError, ImportedDocumentForms},
        structure::ImportedDocumentStructure,
    },
};
use sha2::{Digest as _, Sha256};
use zip::{CompressionMethod, ZipArchive, ZipWriter, write::SimpleFileOptions};

type TestResult = Result<(), Box<dyn Error>>;
const MANIFEST_SHA: &str = "8208bff3f87a4e56ec68caecaf41b00c3fdccc5b3f083289f3c13ccede19466e";

fn manifest() -> Result<(PathBuf, serde_json::Value), Box<dyn Error>> {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../fixtures/target-build/p09-42-product-form-values-01/output");
    let bytes = std::fs::read(root.join("fixture-manifest.json"))?;
    assert_eq!(hex::encode(Sha256::digest(&bytes)), MANIFEST_SHA);
    Ok((root, serde_json::from_slice(&bytes)?))
}
fn fixture(case: &str, kind: &str) -> Result<Vec<u8>, Box<dyn Error>> {
    let (root, manifest) = manifest()?;
    let row = manifest["cases"]
        .as_array()
        .ok_or("cases")?
        .iter()
        .find(|row| row["case"] == case)
        .ok_or("case")?;
    let entry = &row[kind];
    let name = entry["path"].as_str().ok_or("path")?;
    assert!(!name.contains(['/', '\\', ':']));
    let bytes = std::fs::read(root.join(name))?;
    assert_eq!(bytes.len() as u64, entry["bytes"]);
    assert_eq!(hex::encode(Sha256::digest(&bytes)), entry["sha256"]);
    Ok(bytes)
}
fn source(bytes: &[u8]) -> Result<ImportedSourcePackage, Box<dyn Error>> {
    Ok(ImportedSourcePackage::import(
        bytes,
        DocumentId::parse("form-import-test")?,
        Sha256::digest(bytes).into(),
        SourceImportLimits::default(),
    )?)
}
fn import(bytes: &[u8]) -> Result<ImportedDocumentForms, Box<dyn Error>> {
    Ok(ImportedDocumentForms::import(source(bytes)?)?)
}
fn parts(bytes: &[u8]) -> Result<BTreeMap<String, Vec<u8>>, Box<dyn Error>> {
    let mut zip = ZipArchive::new(Cursor::new(bytes))?;
    let mut out = BTreeMap::new();
    for index in 0..zip.len() {
        let mut entry = zip.by_index(index)?;
        let mut raw = Vec::new();
        entry.read_to_end(&mut raw)?;
        out.insert(entry.name().into(), raw);
    }
    Ok(out)
}
fn package(parts: &BTreeMap<String, Vec<u8>>) -> Result<Vec<u8>, Box<dyn Error>> {
    let mut zip = ZipWriter::new(Cursor::new(Vec::new()));
    // The normal closed HWPX admission requires mimetype FIRST. Do not change
    // that product guard to accommodate this test-only derived archive.
    zip.start_file(
        "mimetype",
        SimpleFileOptions::default().compression_method(CompressionMethod::Stored),
    )?;
    zip.write_all(parts.get("mimetype").ok_or("mimetype")?)?;
    for (path, bytes) in parts.iter().filter(|(path, _)| path.as_str() != "mimetype") {
        zip.start_file(
            path,
            SimpleFileOptions::default().compression_method(CompressionMethod::Stored),
        )?;
        zip.write_all(bytes)?;
    }
    Ok(zip.finish()?.into_inner())
}
fn originals(flow: &Flow, nodes: &mut BTreeMap<LogicalId, Node>) {
    for node in &flow.children {
        nodes.insert(node.common().node_id.clone(), node.clone());
        if let Node::Table(table) = node {
            for cell in &table.cells {
                originals(&cell.body, nodes);
            }
        }
    }
}
fn restore(flow: &mut Flow, nodes: &BTreeMap<LogicalId, Node>) -> TestResult {
    for node in &mut flow.children {
        if let Node::Table(table) = node {
            for cell in &mut table.cells {
                restore(&mut cell.body, nodes)?;
            }
        }
        if matches!(node, Node::FormControl(_)) {
            let original = nodes.get(&node.common().node_id).ok_or("original node")?;
            assert_eq!(node.common(), original.common());
            assert!(matches!(original, Node::EmbeddedObject(_)));
            *node = original.clone();
        }
    }
    Ok(())
}

#[test]
fn all_ten_locked_packages_lift_fifty_actual_forms_and_every_physical_anchor() -> TestResult {
    let (_, manifest) = manifest()?;
    let mut count = 0;
    let mut forms = 0;
    let mut kinds = [0; 5];
    for row in manifest["cases"].as_array().ok_or("cases")? {
        for kind in ["source", "output"] {
            let bytes = fixture(row["case"].as_str().ok_or("case")?, kind)?;
            let imported = import(&bytes)?;
            assert_eq!(imported.verify_source(&bytes)?, *imported.receipt());
            for form in imported.forms() {
                let resolved = imported.source().resolve_anchor(&form.source_anchor)?;
                let part = resolved.part();
                let xml = part.xml().ok_or("native XML")?;
                let element = resolved.element().ok_or("form element")?;
                let run = &xml.elements()[element.parent().ok_or("run")?];
                let paragraph = run.parent().ok_or("paragraph")?;
                let parent_anchor = part.element_anchor(paragraph).ok_or("paragraph anchor")?;
                assert_eq!(
                    form.physical_anchor.paragraph_id.as_str(),
                    format!("node-{}", parent_anchor.opaque_handle.as_str())
                );
                assert_eq!(
                    form.raw_control_sha256,
                    hex::encode(form.source_anchor.fingerprint_sha256)
                );
                assert_eq!(
                    form.node_id.as_str(),
                    format!("node-{}", form.source_anchor.opaque_handle.as_str())
                );
            }
            forms += imported.forms().len();
            for (sum, value) in kinds.iter_mut().zip(imported.receipt().kinds) {
                *sum += value;
            }
            count += 1;
        }
    }
    assert_eq!(count, 10);
    assert_eq!(forms, 50);
    assert_eq!(kinds, [10, 8, 16, 8, 8]);
    Ok(())
}

#[test]
fn non_form_graph_and_all_original_source_bindings_are_exact() -> TestResult {
    let bytes = fixture("five-kinds", "source")?;
    let body = ImportedDocumentStructure::import(source(&bytes)?)?;
    let imported = import(&bytes)?;
    assert_eq!(
        imported.receipt().body_graph_sha256,
        body.receipt().graph_sha256
    );
    let mut nodes = BTreeMap::new();
    for section in body.graph().sections() {
        originals(&section.body, &mut nodes);
    }
    let original = body.graph().clone().into_draft();
    let mut reversed = imported.graph().clone().into_draft();
    for section in &mut reversed.sections {
        restore(&mut section.body, &nodes)?;
    }
    reversed.metadata = original.metadata;
    reversed.security_state = original.security_state;
    assert_eq!(
        DocumentGraph::from_draft(reversed, DocumentGraphLimits::default())?,
        *body.graph()
    );
    assert_eq!(imported.receipt().form_controls, 6);
    assert_eq!(
        imported.receipt().remaining_opaque_nodes + 6,
        body.receipt().opaque_nodes
    );
    Ok(())
}

#[test]
fn native_observations_do_not_invent_defaults_validation_or_component_ids() -> TestResult {
    let imported = import(&fixture("five-kinds", "source")?)?;
    assert!(
        imported
            .forms()
            .iter()
            .any(|f| matches!(f.native_identity, NativeFormObservedIdentity::Missing))
    );
    for form in imported.forms() {
        let value = serde_json::to_value(form)?;
        assert!(value.get("component_identity").is_none());
        assert!(value.get("native_object_id").is_none());
        for forbidden in [
            "default_value",
            "default_selected_value",
            "validation",
            "must_be_checked",
            "group_required",
        ] {
            assert!(value["payload"].get(forbidden).is_none());
        }
    }
    let mut nodes = BTreeMap::new();
    for section in imported.graph().sections() {
        originals(&section.body, &mut nodes);
    }
    for node in nodes.values() {
        if let Node::FormControl(form) = node {
            assert!(
                form.properties
                    .iter()
                    .all(|(key, _)| key != "complete_control_state_json")
            );
            assert!(form.common.source_anchor.is_some());
        }
    }
    Ok(())
}

#[test]
fn supported_bad_native_properties_and_catalog_references_never_fall_back() -> TestResult {
    let original = fixture("actual", "source")?;
    for (before, after) in [
        ("enabled=\"1\"", "enabled=\"invalid\""),
        ("charPrIDRef=\"0\"", "charPrIDRef=\"999999\""),
    ] {
        let mut parts = parts(&original)?;
        let raw = String::from_utf8(parts.get("Contents/section0.xml").ok_or("section")?.clone())?;
        assert!(raw.contains(before));
        parts.insert(
            "Contents/section0.xml".into(),
            raw.replace(before, after).into_bytes(),
        );
        let bytes = package(&parts)?;
        let source = source(&bytes)?;
        assert!(matches!(
            ImportedDocumentForms::import(source),
            Err(FormImportError::Native(_))
        ));
    }
    Ok(())
}

#[test]
fn duplicate_observed_ids_across_real_sections_are_rejected_not_reservations() -> TestResult {
    let mut parts = parts(&fixture("five-kinds", "source")?)?;
    for name in ["Contents/section0.xml", "Contents/section1.xml"] {
        let raw = String::from_utf8(parts.get(name).ok_or("section")?.clone())?;
        let xml = hwpx_package::PreservingXmlDocument::parse(raw.as_bytes())?;
        let form = xml
            .elements()
            .iter()
            .find(|e| {
                e.name().namespace() == Some("http://www.hancom.co.kr/hwpml/2011/paragraph")
                    && ["edit", "checkBtn", "radioBtn", "comboBox", "listBox"]
                        .contains(&e.name().local_name())
            })
            .ok_or("actual native form")?;
        assert!(
            form.attributes()
                .iter()
                .all(|a| a.name().local_name() != "id")
        );
        let qualified = form.name().qualified_name();
        let needle = format!("<{qualified} ");
        assert!(raw.contains(&needle));
        parts.insert(
            name.into(),
            raw.replacen(&needle, &format!("<{qualified} id=\"777\" "), 1)
                .into_bytes(),
        );
    }
    let bytes = package(&parts)?;
    assert!(matches!(
        ImportedDocumentForms::import(source(&bytes)?),
        Err(FormImportError::Native(NativeFormPackageError::Map))
    ));
    Ok(())
}

#[test]
fn no_form_body_does_not_manufacture_native_catalog_or_security_attestation() -> TestResult {
    let native = hwpx_package::Hancom2020Vs0Builder::build("NO FORMS")?;
    let bytes = native.with_verified_bytes(<[u8]>::to_vec)?;
    let imported = import(&bytes)?;
    assert!(imported.forms().is_empty());
    assert_eq!(imported.receipt().native_binding_sha256, None);
    assert_eq!(imported.receipt().kinds, [0; 5]);
    assert_eq!(imported.verify_source(&bytes)?, *imported.receipt());
    Ok(())
}

#[test]
fn fresh_source_and_document_identity_are_not_rebound() -> TestResult {
    let bytes = fixture("actual", "source")?;
    let imported = import(&bytes)?;
    assert!(matches!(
        imported.verify_source(&fixture("actual", "output")?),
        Err(FormImportError::Source(_))
    ));
    let other = ImportedDocumentForms::import(ImportedSourcePackage::import(
        &bytes,
        DocumentId::parse("different-document")?,
        Sha256::digest(&bytes).into(),
        SourceImportLimits::default(),
    )?)?;
    assert_ne!(other.forms()[0].node_id, imported.forms()[0].node_id);
    assert_eq!(
        other.forms()[0].native_identity,
        imported.forms()[0].native_identity
    );
    Ok(())
}

#[test]
fn observed_edit_keeps_values_private_in_debug_receipt_and_errors() -> TestResult {
    let imported = import(&fixture("five-kinds", "output")?)?;
    let form = imported
        .forms()
        .iter()
        .find(|f| f.tag == NativeFormTag::Edit)
        .ok_or("edit")?;
    let output = format!(
        "{imported:?} {form:?} {:?} {}",
        imported.receipt(),
        FormImportError::Binding
    );
    let private = serde_json::to_value(form)?;
    let value = private["payload"]["value"].as_str().ok_or("text")?;
    assert!(!value.is_empty());
    assert!(!output.contains(value));
    for forbidden in [
        "<hp:",
        "observed_form_json",
        "section0.xml",
        "component_identity",
    ] {
        assert!(!output.contains(forbidden));
    }
    Ok(())
}

#[test]
fn all_sixteen_saved_table_packages_remain_real_body_graphs_without_fake_forms() -> TestResult {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
    let raw = std::fs::read(root.join(
        "implementation/p06/evidence/target/p06-table-aggregate.current-2020.attempt02.v2.json",
    ))?;
    assert_eq!(
        hex::encode(Sha256::digest(&raw)),
        "edc71d554e0975d511ffe6f0de1b140a30ca932d0bf2b9c7b70517c5e8674fc5"
    );
    let manifest: serde_json::Value = serde_json::from_slice(&raw)?;
    let cases = manifest["cases"].as_array().ok_or("table cases")?;
    assert_eq!(cases.len(), 8);
    let mut count = 0;
    for case in cases {
        for kind in ["input", "output"] {
            let entry = &case[kind];
            let bytes = std::fs::read(root.join(entry["path"].as_str().ok_or("table path")?))?;
            assert_eq!(bytes.len() as u64, entry["bytes"]);
            assert_eq!(hex::encode(Sha256::digest(&bytes)), entry["sha256"]);
            let imported = import(&bytes)?;
            assert!(imported.forms().is_empty());
            assert_eq!(imported.receipt().native_binding_sha256, None);
            assert_eq!(imported.receipt().legacy_reference_state, None);
            assert_eq!(imported.verify_source(&bytes)?, *imported.receipt());
            let body = ImportedDocumentStructure::import(source(&bytes)?)?;
            assert_eq!(body.receipt().tables, 1);
            assert_eq!(body.receipt().table_cells, 8);
            assert_eq!(imported.graph().sections(), body.graph().sections());
            count += 1;
        }
    }
    assert_eq!(count, 16);
    Ok(())
}

#[test]
fn real_native_forms_use_namespace_identity_not_a_fixed_xml_prefix() -> TestResult {
    let bytes = fixture("five-kinds", "source")?;
    let original = import(&bytes)?;
    let mut parts = parts(&bytes)?;
    for name in ["Contents/section0.xml", "Contents/section1.xml"] {
        let raw = String::from_utf8(parts.get(name).ok_or("section")?.clone())?;
        assert!(!raw.contains("xmlns:q="));
        let aliased = raw
            .replace("xmlns:hp=", "xmlns:q=")
            .replace("<hp:", "<q:")
            .replace("</hp:", "</q:");
        parts.insert(name.into(), aliased.into_bytes());
    }
    let aliased_bytes = package(&parts)?;
    let aliased = import(&aliased_bytes)?;
    assert_eq!(aliased.forms().len(), original.forms().len());
    for (a, b) in aliased.forms().iter().zip(original.forms()) {
        assert_eq!(a.tag, b.tag);
        assert_eq!(a.common, b.common);
        assert_eq!(a.payload, b.payload);
        assert_eq!(a.native_identity, b.native_identity);
        assert_ne!(a.source_anchor, b.source_anchor);
    }
    assert_eq!(aliased.verify_source(&aliased_bytes)?, *aliased.receipt());
    Ok(())
}
