use domain_ir::{
    DocumentId, ReferenceAuxiliaryLimitConfig, ReferenceAuxiliaryLimits, ReferenceTargetKind,
};
use hwpx_package::document_import::{
    ImportedSourcePackage, SourceImportLimits,
    reference_targets::{ImportedReferenceTargets, ReferenceTargetImportError},
    structure::ImportedDocumentStructure,
};
use sha2::{Digest as _, Sha256};
use std::error::Error;
#[path="support/reference_heading_targets.rs"]mod source_headings;

#[path = "support/document_import_field_fixture.rs"]
#[allow(dead_code)] // Shared fixture entrypoints not all used by this focused suite.
mod base;
#[path = "support/document_import_bookmark_fixture.rs"]
#[allow(dead_code)] // Keep the original shared fixture unchanged.
mod fixture;
#[path = "support/document_import_note_fixture.rs"]
mod notes;
type TestResult = Result<(), Box<dyn Error>>;

fn structure(bytes: &[u8], name: &str) -> Result<ImportedDocumentStructure, Box<dyn Error>> {
    Ok(ImportedDocumentStructure::import(
        ImportedSourcePackage::import(
            bytes,
            DocumentId::parse(name)?,
            Sha256::digest(bytes).into(),
            SourceImportLimits::default(),
        )?,
    )?)
}
fn limits() -> Result<ReferenceAuxiliaryLimits, Box<dyn Error>> {
    Ok(ReferenceAuxiliaryLimits::new(
        ReferenceAuxiliaryLimitConfig::default(),
    )?)
}

#[test]
fn actual_source_target_identity_is_bound_without_fabricated_flow_or_reference_edges() -> TestResult
{
    let bytes = base::package(&fixture::paragraph(&fixture::marker("private source name")))?;
    let source = structure(&bytes, "reference-source")?;
    let targets = ImportedReferenceTargets::import(&source, limits()?)?;
    let target = targets.by_exact_source_name("private source name")?;
    assert_eq!(target.logical_target_id, source.bookmarks()[0].reference_id);
    assert_eq!(target.target_kind, ReferenceTargetKind::Bookmark);
    assert!(target.active);
    assert!(target.anchor.is_none());
    assert_eq!(targets.receipt().bookmark_targets, 1);
    assert!(!targets.receipt().complete_reference_state_qualified);
    assert_eq!(targets.verify_source(&bytes)?, *targets.receipt());
    assert!(!format!("{targets:?}").contains("private source name"));
    assert!(!serde_json::to_string(targets.receipt())?.contains("private source name"));
    Ok(())
}

#[test]
fn duplicate_names_and_absence_have_distinct_closed_errors() -> TestResult {
    let bytes = base::package(&fixture::paragraph(&format!(
        "{}{}",
        fixture::marker("same"),
        fixture::marker("same")
    )))?;
    let source = structure(&bytes, "reference-source")?;
    let targets = ImportedReferenceTargets::import(&source, limits()?)?;
    assert_eq!(targets.targets().len(), 2);
    assert_ne!(
        targets.targets()[0].logical_target_id,
        targets.targets()[1].logical_target_id
    );
    assert_eq!(
        targets.by_exact_source_name("same"),
        Err(ReferenceTargetImportError::Ambiguous)
    );
    assert_eq!(
        targets.by_exact_source_name("missing"),
        Err(ReferenceTargetImportError::Missing)
    );
    assert_eq!(targets.receipt().ambiguous_source_names, 1);
    Ok(())
}

#[test]
fn decoding_does_not_normalize_unicode_or_case() -> TestResult {
    let bytes = base::package(&fixture::paragraph(&fixture::marker("e&#x301;")))?;
    let source = structure(&bytes, "reference-source")?;
    let targets = ImportedReferenceTargets::import(&source, limits()?)?;
    assert!(targets.by_exact_source_name("e\u{301}").is_ok());
    for name in ["é", "E\u{301}"] {
        assert_eq!(
            targets.by_exact_source_name(name),
            Err(ReferenceTargetImportError::Missing)
        );
    }
    Ok(())
}

#[test]
fn multiple_spine_parts_and_nested_table_note_targets_keep_original_identity() -> TestResult {
    let two = fixture::two_sections()?;
    let source = structure(&two, "reference-source")?;
    let targets = ImportedReferenceTargets::import(&source, limits()?)?;
    assert_eq!(targets.targets().len(), 2);
    assert_eq!(
        targets.by_exact_source_name("same-across-sections"),
        Err(ReferenceTargetImportError::Ambiguous)
    );
    for body in [
        fixture::paragraph(&fixture::table(&fixture::marker("nested"))),
        fixture::paragraph(&fixture::note(&fixture::table(&fixture::marker("nested")))),
    ] {
        let bytes = base::package(&body)?;
        let source = structure(&bytes, "reference-source")?;
        let targets = ImportedReferenceTargets::import(&source, limits()?)?;
        assert_eq!(targets.receipt().bookmark_targets, 1);
        assert_eq!(
            targets.targets().len(),
            1 + source.notes().len() + source.receipt().tables
        );
        assert_eq!(targets.verify_source(&bytes)?, *targets.receipt());
    }
    Ok(())
}

#[test]
fn field_presence_is_not_misreported_as_complete_reference_import() -> TestResult {
    let bytes = base::package(&fixture::paragraph(&format!(
        "{}{}",
        fixture::marker("point"),
        fixture::field()
    )))?;
    let source = structure(&bytes, "reference-source")?;
    let targets = ImportedReferenceTargets::import(&source, limits()?)?;
    assert_eq!(targets.receipt().observed_native_fields, 1);
    assert!(!targets.receipt().complete_reference_state_qualified);
    let bytes = base::package(&fixture::paragraph("<u:bookmark name='foreign'/>"))?;
    let source = structure(&bytes, "reference-source")?;
    assert!(
        ImportedReferenceTargets::import(&source, limits()?)?
            .targets()
            .is_empty()
    );
    Ok(())
}

#[test]
fn original_package_and_document_binding_cannot_be_rebound() -> TestResult {
    let bytes = base::package(&fixture::paragraph(&fixture::marker("point")))?;
    let source = structure(&bytes, "document-one")?;
    let other = structure(&bytes, "document-two")?;
    let targets = ImportedReferenceTargets::import(&source, limits()?)?;
    let other_targets = ImportedReferenceTargets::import(&other, limits()?)?;
    assert_ne!(
        targets.targets()[0].logical_target_id,
        other_targets.targets()[0].logical_target_id
    );
    assert_ne!(
        targets.receipt().target_inventory_sha256,
        other_targets.receipt().target_inventory_sha256
    );
    let changed = base::package(&fixture::paragraph(&fixture::marker("changed")))?;
    assert_eq!(
        targets.verify_source(&changed),
        Err(ReferenceTargetImportError::Binding)
    );
    Ok(())
}

#[test]
fn caller_limits_reject_name_count_and_streamed_json_budget() -> TestResult {
    let bytes = base::package(&fixture::paragraph(&format!(
        "{}{}",
        fixture::marker("point"),
        fixture::marker("other")
    )))?;
    let source = structure(&bytes, "reference-source")?;
    for config in [
        ReferenceAuxiliaryLimitConfig {
            items_per_kind: 1,
            ..ReferenceAuxiliaryLimitConfig::default()
        },
        ReferenceAuxiliaryLimitConfig {
            text_bytes: 1,
            ..ReferenceAuxiliaryLimitConfig::default()
        },
        ReferenceAuxiliaryLimitConfig {
            input_bytes: 1,
            output_bytes: 1,
            ..ReferenceAuxiliaryLimitConfig::default()
        },
    ] {
        assert!(matches!(
            ImportedReferenceTargets::import(&source, ReferenceAuxiliaryLimits::new(config)?),
            Err(ReferenceTargetImportError::Limit)
        ));
    }
    Ok(())
}

#[test]
fn native_captured_hyperlink_keeps_field_coverage_explicit_without_fabricated_targets() -> TestResult
{
    let bytes = base::captured()?;
    let source = structure(&bytes, "reference-source")?;
    let targets = ImportedReferenceTargets::import(&source, limits()?)?;
    assert!(targets.targets().is_empty());
    assert_eq!(targets.receipt().observed_native_fields, 1);
    assert!(!targets.receipt().complete_reference_state_qualified);
    Ok(())
}

fn package_with_header_control(control: &str) -> Result<Vec<u8>, Box<dyn Error>> {
    use std::io::{Cursor, Read, Write};
    use zip::{ZipArchive, ZipWriter, write::SimpleFileOptions};
    let bytes = base::package(&fixture::paragraph("<hp:t>body</hp:t>"))?;
    let mut original = ZipArchive::new(Cursor::new(bytes))?;
    let mut output = ZipWriter::new(Cursor::new(Vec::new()));
    for index in 0..original.len() {
        let mut entry = original.by_index(index)?;
        let name = entry.name().to_owned();
        let mut data = Vec::new();
        entry.read_to_end(&mut data)?;
        if name == "Contents/header.xml" {
            data = format!(
                "<head xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph'>{}</head>",
                control
            )
            .into_bytes();
        }
        output.start_file(
            name,
            SimpleFileOptions::default().compression_method(zip::CompressionMethod::Stored),
        )?;
        output.write_all(&data)?;
    }
    Ok(output.finish()?.into_inner())
}

#[test]
fn bookmark_outside_supported_structure_is_not_silently_omitted() -> TestResult {
    let bytes = package_with_header_control(&fixture::marker("uncovered"))?;
    let source = structure(&bytes, "reference-source")?;
    assert!(matches!(
        ImportedReferenceTargets::import(&source, limits()?),
        Err(ReferenceTargetImportError::Coverage)
    ));
    Ok(())
}

#[test]
fn actual_footnote_and_endnote_targets_use_source_ids_not_shared_native_numbers() -> TestResult {
    let foot = fixture::note("<hp:t>private foot body</hp:t>");
    let end = foot.replace("footNote", "endNote");
    let bytes = base::package(&fixture::paragraph(&format!("{foot}{end}")))?;
    let source = structure(&bytes, "note-targets")?;
    let targets = ImportedReferenceTargets::import(&source, limits()?)?;
    assert_eq!(targets.receipt().bookmark_targets, 0);
    assert_eq!(targets.receipt().note_targets, 2);
    assert!(format!("{targets:?}").contains("source_bookmarks_notes_and_tables"));
    assert_ne!(
        targets.targets()[0].logical_target_id,
        targets.targets()[1].logical_target_id
    );
    assert_eq!(
        source.notes()[0].native_instance_id,
        source.notes()[1].native_instance_id
    );
    for (target, note) in targets.targets().iter().zip(source.notes()) {
        assert_eq!(target.logical_target_id, note.note_id);
        assert_eq!(target.target_kind, ReferenceTargetKind::Note);
        assert!(target.active);
        assert!(target.anchor.is_none());
    }
    assert!(matches!(
        targets.by_exact_source_name("101"),
        Err(ReferenceTargetImportError::Missing)
    ));
    assert!(!targets.receipt().complete_reference_state_qualified);
    assert!(!serde_json::to_string(targets.targets())?.contains("private foot body"));
    assert_eq!(targets.verify_source(&bytes)?, *targets.receipt());
    Ok(())
}

#[test]
fn note_inventory_digest_tracks_body_changes_and_per_kind_limit_is_enforced() -> TestResult {
    let body = fixture::paragraph(&fixture::note("<hp:t>A</hp:t>"));
    let bytes = base::package(&body)?;
    let changed = base::package(&body.replace("<hp:t>A", "<hp:t>B"))?;
    let source = structure(&bytes, "note-targets")?;
    let changed_source = structure(&changed, "note-targets")?;
    let targets = ImportedReferenceTargets::import(&source, limits()?)?;
    let changed_targets = ImportedReferenceTargets::import(&changed_source, limits()?)?;
    assert_ne!(
        targets.receipt().target_inventory_sha256,
        changed_targets.receipt().target_inventory_sha256
    );
    assert_ne!(
        targets.targets()[0].target_state_sha256,
        changed_targets.targets()[0].target_state_sha256
    );
    assert_eq!(
        targets.verify_source(&changed),
        Err(ReferenceTargetImportError::Binding)
    );
    let two = base::package(&fixture::paragraph(
        &fixture::note("<hp:t>A</hp:t>").repeat(2),
    ))?;
    let source = structure(&two, "note-targets")?;
    let tight = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {
        items_per_kind: 1,
        ..ReferenceAuxiliaryLimitConfig::default()
    })?;
    assert!(matches!(
        ImportedReferenceTargets::import(&source, tight),
        Err(ReferenceTargetImportError::Limit)
    ));
    Ok(())
}

#[test]
fn note_outside_supported_structure_is_not_silently_omitted() -> TestResult {
    let bytes = package_with_header_control(&fixture::note("<hp:t>uncovered</hp:t>"))?;
    let source = structure(&bytes, "note-targets")?;
    assert!(matches!(
        ImportedReferenceTargets::import(&source, limits()?),
        Err(ReferenceTargetImportError::Coverage)
    ));
    Ok(())
}

#[test]
fn historical_generated_saved_reopened_notes_are_targets_without_relabelling_failures() -> TestResult
{
    let mut lanes = [0usize; 3];
    for input in notes::actual_inputs()? {
        let source = structure(&input.bytes, "historical-note-targets")?;
        let targets = ImportedReferenceTargets::import(&source, limits()?)?;
        assert_eq!(targets.receipt().note_targets, input.expected_notes);
        assert_eq!(targets.receipt().bookmark_targets, 0);
        assert_eq!(targets.targets().len(), input.expected_notes);
        assert!(!targets.receipt().complete_reference_state_qualified);
        lanes[match input.lane {
            "generated" => 0,
            "saved" => 1,
            "reopened" => 2,
            _ => return Err("unknown lane".into()),
        }] += 1;
    }
    assert_eq!(lanes, [3, 3, 3]);
    Ok(())
}

#[test]
fn nested_tables_and_note_tables_keep_actual_node_identity_without_native_id_aliases() -> TestResult
{
    use domain_ir::{Flow, Node};
    fn tables<'a>(flow: &'a Flow, result: &mut Vec<&'a domain_ir::TableNode>) {
        for node in &flow.children {
            if let Node::Table(table) = node {
                result.push(table);
                for cell in &table.cells {
                    tables(&cell.body, result);
                }
            }
        }
    }
    let body = format!(
        "{}{}{}",
        fixture::marker("point"),
        fixture::table(&fixture::table("<hp:t>private nested table</hp:t>")),
        fixture::note(&fixture::table("<hp:t>private note table</hp:t>")),
    );
    let bytes = base::package(&fixture::paragraph(&body))?;
    let source = structure(&bytes, "table-targets")?;
    let targets = ImportedReferenceTargets::import(&source, limits()?)?;
    assert_eq!(targets.receipt().bookmark_targets, 1);
    assert_eq!(targets.receipt().note_targets, 1);
    assert_eq!(targets.receipt().table_targets, 3);
    assert_eq!(targets.targets().len(), 5);
    let mut nodes = Vec::new();
    for section in source.graph().sections() {
        tables(&section.body, &mut nodes);
    }
    for note in source.graph().notes() {
        tables(&note.body, &mut nodes);
    }
    let table_targets: Vec<_> = targets
        .targets()
        .iter()
        .filter(|t| t.target_kind == ReferenceTargetKind::Table)
        .collect();
    assert_eq!(nodes.len(), table_targets.len());
    for (target, table) in table_targets.iter().zip(nodes) {
        assert_eq!(target.logical_target_id, table.common.node_id);
        assert!(target.anchor.is_none());
        assert!(target.active);
    }
    let unique: std::collections::BTreeSet<_> =
        table_targets.iter().map(|t| &t.logical_target_id).collect();
    assert_eq!(unique.len(), 3);
    assert!(!serde_json::to_string(targets.targets())?.contains("private"));
    assert_eq!(targets.verify_source(&bytes)?, *targets.receipt());
    Ok(())
}

#[test]
fn table_body_fingerprint_changes_and_table_limit_does_not_count_other_families() -> TestResult {
    let body = fixture::paragraph(&format!(
        "{}{}{}",
        fixture::marker("point"),
        fixture::note("<hp:t>note</hp:t>"),
        fixture::table("<hp:t>A</hp:t>")
    ));
    let bytes = base::package(&body)?;
    let changed = base::package(&body.replace("<hp:t>A", "<hp:t>B"))?;
    let source = structure(&bytes, "table-targets")?;
    let changed_source = structure(&changed, "table-targets")?;
    let tight = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {
        items_per_kind: 1,
        ..Default::default()
    })?;
    let targets = ImportedReferenceTargets::import(&source, tight)?;
    let changed_targets = ImportedReferenceTargets::import(&changed_source, tight)?;
    assert_eq!(targets.targets().len(), 3);
    assert_ne!(
        targets.targets()[2].target_state_sha256,
        changed_targets.targets()[2].target_state_sha256
    );
    assert_eq!(
        targets.verify_source(&changed),
        Err(ReferenceTargetImportError::Binding)
    );
    let two = base::package(&fixture::paragraph(
        &fixture::table("<hp:t>A</hp:t>").repeat(2),
    ))?;
    let source = structure(&two, "table-targets")?;
    assert!(matches!(
        ImportedReferenceTargets::import(&source, tight),
        Err(ReferenceTargetImportError::Limit)
    ));
    Ok(())
}

#[test]
fn table_outside_structure_rejects_but_foreign_namespace_is_not_a_native_target() -> TestResult {
    let bytes = package_with_header_control(&fixture::table("<hp:t>uncovered</hp:t>"))?;
    let source = structure(&bytes, "table-targets")?;
    assert!(matches!(
        ImportedReferenceTargets::import(&source, limits()?),
        Err(ReferenceTargetImportError::Coverage)
    ));
    let bytes = base::package(&fixture::paragraph("<u:tbl id='1'/><u:equation id='2'/>"))?;
    let source = structure(&bytes, "table-targets")?;
    let targets = ImportedReferenceTargets::import(&source, limits()?)?;
    assert!(targets.targets().is_empty());
    assert!(!targets.receipt().complete_reference_state_qualified);
    Ok(())
}

#[test]
fn sixteen_locked_historical_tables_have_source_targets_not_new_native_acceptance() -> TestResult {
    use std::{fs, path::PathBuf};
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
    let manifest_bytes = fs::read(root.join(
        "implementation/p06/evidence/target/p06-table-aggregate.current-2020.attempt02.v2.json",
    ))?;
    assert_eq!(
        hex::encode(Sha256::digest(&manifest_bytes)),
        "edc71d554e0975d511ffe6f0de1b140a30ca932d0bf2b9c7b70517c5e8674fc5"
    );
    let manifest: serde_json::Value = serde_json::from_slice(&manifest_bytes)?;
    let cases = manifest["cases"].as_array().ok_or("table cases")?;
    assert_eq!(cases.len(), 8);
    let mut count = 0;
    for row in cases {
        for kind in ["input", "output"] {
            let bytes = fs::read(root.join(row[kind]["path"].as_str().ok_or("table path")?))?;
            assert_eq!(hex::encode(Sha256::digest(&bytes)), row[kind]["sha256"]);
            assert_eq!(bytes.len() as u64, row[kind]["bytes"]);
            let source = structure(&bytes, "historical-table-targets")?;
            let targets = ImportedReferenceTargets::import(&source, limits()?)?;
            assert_eq!(targets.receipt().table_targets, 1);
            assert_eq!(
                targets
                    .targets()
                    .iter()
                    .filter(|t| t.target_kind == ReferenceTargetKind::Table)
                    .count(),
                1
            );
            assert!(!targets.receipt().complete_reference_state_qualified);
            count += 1;
        }
    }
    assert_eq!(count, 16);
    Ok(())
}

#[test]
fn source_object_targets_all_nine_native_names_keep_original_target_inventory_exact() -> TestResult {
    use hwpx_package::document_import::reference_targets::ImportedReferenceObjectTargets;
    let mut body = fixture::marker("private bookmark");
    for name in ["pic", "rect", "ellipse", "line", "arc", "polygon", "curve", "connectLine", "equation"] {
        body.push_str(&format!("<hp:{name} id='7' instId='9'><hp:t>private object text</hp:t></hp:{name}>"));
    }
    let bytes = base::package(&fixture::paragraph(&body))?;
    let source = structure(&bytes, "source-objects")?;
    let original = ImportedReferenceTargets::import(&source, limits()?)?;
    let original_json = serde_json::to_vec(original.receipt())?;
    let objects = ImportedReferenceObjectTargets::import(&source, limits()?)?;
    assert_eq!(objects.targets().len(), 9);
    assert_eq!(objects.receipt().object_targets, 8);
    assert_eq!(objects.receipt().equation_targets, 1);
    let ids: std::collections::BTreeSet<_> = objects.targets().iter().map(|t| &t.logical_target_id).collect();
    assert_eq!(ids.len(), 9); // Shared native id/instId never aliases distinct objects.
    for (index, target) in objects.targets().iter().enumerate() {
        assert_eq!(target.target_kind, if index == 8 { ReferenceTargetKind::Equation } else { ReferenceTargetKind::Object });
        assert!(target.active && target.anchor.is_none());
        assert_eq!(target.target_state_sha256.len(), 64);
    }
    assert_eq!(objects.receipt().target_inventory_sha256, <[u8; 32]>::from(Sha256::digest(serde_json::to_vec(objects.targets())?)));
    assert!(!objects.receipt().complete_reference_state_qualified);
    assert!(!objects.receipt().native_geometry_or_equation_semantics_qualified);
    let text = format!("{:?}{}", objects, String::from_utf8(serde_json::to_vec(objects.receipt())?)?);
    assert!(!text.contains("private"));
    assert_eq!(serde_json::to_vec(ImportedReferenceTargets::import(&source, limits()?)?.receipt())?, original_json);
    assert_eq!(original.targets().len(), 1);
    assert_eq!(objects.verify_source(&bytes)?, *objects.receipt());
    Ok(())
}

#[test]
fn source_object_targets_use_original_nested_table_and_detached_note_nodes() -> TestResult {
    use hwpx_package::document_import::reference_targets::ImportedReferenceObjectTargets;
    let body = format!("{}{}", fixture::table("<hp:pic id='7'/><hp:equation id='8'/>"),
        fixture::note(&fixture::table("<hp:rect id='7'/><hp:equation id='8'/>")));
    let bytes = base::package(&fixture::paragraph(&body))?;
    let source = structure(&bytes, "nested-objects")?;
    let objects = ImportedReferenceObjectTargets::import(&source, limits()?)?;
    assert_eq!((objects.receipt().object_targets, objects.receipt().equation_targets), (2, 2));
    assert_eq!(objects.targets().iter().map(|t| &t.logical_target_id).collect::<std::collections::BTreeSet<_>>().len(), 4);
    assert_eq!(objects.verify_source(&bytes)?, *objects.receipt());
    Ok(())
}

#[test]
fn source_object_targets_require_expanded_namespace_not_prefix_or_local_name() -> TestResult {
    use hwpx_package::document_import::reference_targets::ImportedReferenceObjectTargets;
    let bytes = base::package(&fixture::paragraph("<u:pic/><u:rect/><u:equation/><alias:rect xmlns:alias='http://www.hancom.co.kr/hwpml/2011/paragraph'/><alias:equation xmlns:alias='http://www.hancom.co.kr/hwpml/2011/paragraph'/>"))?;
    let source = structure(&bytes, "namespace-objects")?;
    let objects = ImportedReferenceObjectTargets::import(&source, limits()?)?;
    assert_eq!((objects.receipt().object_targets, objects.receipt().equation_targets), (1, 1));
    Ok(())
}

#[test]
fn source_object_targets_reject_whole_source_coverage_holes_without_guessing_children() -> TestResult {
    use hwpx_package::document_import::reference_targets::ImportedReferenceObjectTargets;
    for bytes in [
        package_with_header_control("<hp:pic/><hp:equation/>")?,
        base::package(&fixture::paragraph("<u:future><hp:rect/></u:future>"))?,
        base::package(&fixture::paragraph("<hp:ctrl><hp:equation/></hp:ctrl>"))?,
    ] {
        let source = structure(&bytes, "uncovered-objects")?;
        assert!(matches!(ImportedReferenceObjectTargets::import(&source, limits()?), Err(ReferenceTargetImportError::Coverage)));
        // Original target-only API is intentionally not changed by the new stage.
        assert!(ImportedReferenceTargets::import(&source, limits()?)?.targets().is_empty());
    }
    Ok(())
}

#[test]
fn source_object_targets_limits_are_per_family_and_aggregate_output_is_bounded() -> TestResult {
    use hwpx_package::document_import::reference_targets::ImportedReferenceObjectTargets;
    let tight = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig { items_per_kind: 1, ..Default::default() })?;
    let bytes = base::package(&fixture::paragraph("<hp:pic/><hp:equation/>"))?;
    let source = structure(&bytes, "limited-objects")?;
    assert_eq!(ImportedReferenceObjectTargets::import(&source, tight)?.targets().len(), 2);
    for body in ["<hp:pic/><hp:rect/>", "<hp:equation/><hp:equation/>"] {
        let bytes = base::package(&fixture::paragraph(body))?;
        let source = structure(&bytes, "limited-objects")?;
        assert!(matches!(ImportedReferenceObjectTargets::import(&source, tight), Err(ReferenceTargetImportError::Limit)));
    }
    let tiny = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig { input_bytes: 1, output_bytes: 1, ..Default::default() })?;
    assert!(matches!(ImportedReferenceObjectTargets::import(&source, tiny), Err(ReferenceTargetImportError::Limit)));
    Ok(())
}

#[test]
fn source_object_targets_bind_document_package_subtree_and_fresh_reconstruction() -> TestResult {
    use hwpx_package::document_import::reference_targets::ImportedReferenceObjectTargets;
    let bytes = base::package(&fixture::paragraph("<hp:rect id='7'><hp:t>original</hp:t></hp:rect>"))?;
    let source = structure(&bytes, "original-document")?;
    let objects = ImportedReferenceObjectTargets::import(&source, limits()?)?;
    let other = structure(&bytes, "other-document")?;
    let other_objects = ImportedReferenceObjectTargets::import(&other, limits()?)?;
    assert_ne!(objects.targets()[0], other_objects.targets()[0]);
    let changed = base::package(&fixture::paragraph("<hp:rect id='7'><hp:t>changed</hp:t></hp:rect>"))?;
    assert!(matches!(objects.verify_source(&changed), Err(ReferenceTargetImportError::Binding)));
    let changed_source = structure(&changed, "original-document")?;
    let changed_objects = ImportedReferenceObjectTargets::import(&changed_source, limits()?)?;
    assert_ne!(objects.targets()[0].target_state_sha256, changed_objects.targets()[0].target_state_sha256);
    assert_ne!(objects.receipt().target_inventory_sha256, changed_objects.receipt().target_inventory_sha256);
    assert_eq!(objects.verify_source(&bytes)?, *objects.receipt());
    Ok(())
}

mod file_literal_candidates {
    use super::*;
    use domain_ir::LinkPoint;
    use hwpx_package::{BoundedZipReader, PackageLimits, PreservingXmlDocument, WriterLimits};
    use hwpx_package::document_import::structure::file_literal::{FileLiteralOutputCandidate, FileLiteralOutputError};
    use std::io::Cursor;

    fn point(paragraph: u32, run: u32, inline: u32) -> LinkPoint {
        LinkPoint { paragraph_ordinal: paragraph, run_ordinal: run, inline_ordinal: inline }
    }
    fn lower(source: &ImportedDocumentStructure, bytes: &[u8], point: LinkPoint, name: &str) -> Result<FileLiteralOutputCandidate, FileLiteralOutputError> {
        source.lower_file_literal_candidate(bytes, &source.graph().sections()[0].section_id,
            point, name, ReferenceAuxiliaryLimits::new(Default::default()).map_err(|_| FileLiteralOutputError::Limit)?, WriterLimits::default())
    }
    fn part(candidate: &FileLiteralOutputCandidate, path: &str) -> Result<Vec<u8>, Box<dyn Error>> {
        candidate.with_verified_bytes(|bytes| {
            let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
            let index = reader.entries().iter().position(|e| e.path.as_str() == path).ok_or("part")?;
            Ok::<_,Box<dyn Error>>(reader.read_entry(index)?)
        })?
    }
    fn text_leaves(raw: &[u8]) -> Result<Vec<String>, Box<dyn Error>> {
        let xml = PreservingXmlDocument::parse(raw)?;
        xml.elements().iter().filter(|e| e.name().namespace() == Some("http://www.hancom.co.kr/hwpml/2011/paragraph") && e.name().local_name() == "t")
            .map(|e| {
                let content = e.content_span().ok_or("text")?;
                let text = std::str::from_utf8(&raw[content.start()..content.end()])?;
                Ok(quick_xml::escape::unescape(text)?.into_owned())
            }).collect()
    }

    #[test]
    fn source_file_literal_every_existing_run_child_boundary_preserves_original_content() -> TestResult {
        let unsupported = base::package("<hp:p id='1'><hp:run><hp:t>before</hp:t><!--private preserved comment--><hp:t>after</hp:t></hp:run></hp:p>")?;
        assert!(matches!(structure(&unsupported, "literal-source"), Err(_)));
        let bytes = base::package("<hp:p id='1'><hp:run><hp:t>before</hp:t><hp:t>after</hp:t></hp:run></hp:p>")?;
        let source = structure(&bytes, "literal-source")?;
        let original = source.receipt().clone();
        for ordinal in 0..=2 {
            let output = lower(&source, &bytes, point(0,0,ordinal), "한글&amp<>'\".hwpx")?;
            let mut expected = vec!["before", "after"];
            expected.insert(ordinal as usize, "한글&amp<>'\".hwpx");
            let raw = part(&output, "Contents/section0.xml")?;
            assert_eq!(text_leaves(&raw)?, expected);
            assert!(String::from_utf8(raw)?.contains("<hp:t>after</hp:t>"));
            assert!(output.receipt().outside_selected_run_exact);
            assert!(output.receipt().source_style_attributes_preserved);
            assert!(!output.receipt().complete_auxiliary_state_verified);
            assert!(!output.receipt().execution_publication_authority);
            assert!(!format!("{output:?}").contains("한글"));
            assert_eq!(source.verify_source(&bytes)?, original);
        }
        Ok(())
    }
    #[test]
    fn source_file_literal_empty_and_self_closed_runs_keep_namespace_and_attributes() -> TestResult {
        let unsupported = base::package("<hp:p id='1' u:paragraph='private-style'><hp:run/></hp:p>")?;
        assert!(structure(&unsupported, "empty-literal").is_err());
        for run in ["<hp:run/>", "<hp:run></hp:run>", "<a:run xmlns:a='http://www.hancom.co.kr/hwpml/2011/paragraph'/>"] {
            let bytes = base::package(&format!("<hp:p id='1'>{run}</hp:p>"))?;
            let source = structure(&bytes, "empty-literal")?;
            let output = lower(&source, &bytes, point(0,0,0), "frozen.hwpx")?;
            assert_eq!(text_leaves(&part(&output, "Contents/section0.xml")?)?, ["frozen.hwpx"]);
            assert!(!format!("{output:?}{:?}", output.receipt()).contains("private-style"));
        }
        Ok(())
    }
    #[test]
    fn source_file_literal_real_captured_package_keeps_original_styles_and_other_parts() -> TestResult {
        let bytes = base::captured()?;
        let source = structure(&bytes, "captured-literal")?;
        let output = lower(&source, &bytes, point(0,0,0), "frozen-captured.hwpx")?;
        output.with_verified_bytes(|after| -> TestResult {
            let mut original = BoundedZipReader::open(Cursor::new(&bytes), PackageLimits::default())?;
            let mut result = BoundedZipReader::open(Cursor::new(after), PackageLimits::default())?;
            assert_eq!(original.entries().len(), result.entries().len());
            let mut changed = 0;
            for index in 0..original.entries().len() {
                assert_eq!(original.entries()[index].path, result.entries()[index].path);
                assert_eq!(original.entries()[index].compression, result.entries()[index].compression);
                changed += usize::from(original.read_entry(index)? != result.read_entry(index)?);
            }
            assert_eq!(changed, 1);
            Ok(())
        })??;
        assert!(output.receipt().source_style_attributes_preserved);
        assert!(!output.receipt().source_file_metadata_authenticated);
        Ok(())
    }
    #[test]
    fn source_file_literal_never_inserts_a_frozen_name_inside_a_dynamic_field_cache() -> TestResult {
        let bytes = base::package(&fixture::paragraph(fixture::field()))?;
        let source = structure(&bytes, "field-literal")?;
        for inline in [1,2] {
            assert!(matches!(lower(&source, &bytes, point(0,0,inline), "frozen.hwpx"), Err(FileLiteralOutputError::Selection)));
        }
        for inline in [0,3] {
            let output = lower(&source, &bytes, point(0,0,inline), "frozen.hwpx")?;
            assert!(output.receipt().outside_selected_run_exact);
        }
        Ok(())
    }
    #[test]
    fn source_file_literal_rejects_foreign_unrepresented_and_out_of_range_positions() -> TestResult {
        let bytes = base::package(&fixture::paragraph("<hp:t>original</hp:t><u:future><hp:p><hp:run/></hp:p></u:future>"))?;
        let source = structure(&bytes, "selection-literal")?;
        for point in [point(99,0,0),point(0,99,0),point(0,0,99),point(1,0,0)] {
            assert!(matches!(lower(&source, &bytes, point, "frozen.hwpx"), Err(FileLiteralOutputError::Selection)));
        }
        assert!(matches!(source.lower_file_literal_candidate(&bytes, &domain_ir::LogicalId::parse("foreign-section")?,
            point(0,0,0), "frozen.hwpx", limits()?, WriterLimits::default()), Err(FileLiteralOutputError::Selection)));
        let changed = base::package(&fixture::paragraph("<hp:t>changed</hp:t>"))?;
        assert!(matches!(lower(&source, &changed, point(0,0,0), "frozen.hwpx"), Err(FileLiteralOutputError::Source)));
        Ok(())
    }
    #[test]
    fn source_file_literal_preserves_native_table_cell_protection_and_rejects_invalid_values() -> TestResult {
        let bytes = base::package(&fixture::paragraph(&fixture::table("<hp:t>protected</hp:t>").replace("protect=\"0\"", "protect=\"1\"")))?;
        let source = structure(&bytes, "protected-literal")?;
        assert!(matches!(lower(&source, &bytes, point(1,0,0), "frozen.hwpx"), Err(FileLiteralOutputError::Selection)));
        let bytes = base::package(&fixture::paragraph("<hp:t>original</hp:t>"))?;
        let source = structure(&bytes, "invalid-literal")?;
        for value in ["C:secret.hwpx", "dir/file.hwpx", "dir\\file.hwpx", "bad\0.hwpx", "bad\n.hwpx"] {
            assert!(matches!(lower(&source, &bytes, point(0,0,0), value), Err(FileLiteralOutputError::Value)));
        }
        let tight = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig { text_bytes: 1, ..Default::default() })?;
        assert!(matches!(source.lower_file_literal_candidate(&bytes, &source.graph().sections()[0].section_id,
            point(0,0,0), "frozen.hwpx", tight, WriterLimits::default()), Err(FileLiteralOutputError::Limit)));
        let writer = WriterLimits::new(hwpx_package::WriterLimitConfig { max_output_bytes: 1 })?;
        assert!(matches!(source.lower_file_literal_candidate(&bytes, &source.graph().sections()[0].section_id,
            point(0,0,0), "frozen.hwpx", limits()?, writer), Err(FileLiteralOutputError::Writer)));
        Ok(())
    }
}

mod caption_source_envelopes {
    use super::*;
    use domain_ir::{CaptionNativeSemanticBinding,NativeCaptionSide};
    use hwpx_package::document_import::reference_targets::captions::{ImportedReferenceCaptions,ReferenceCaptionImportError};
    fn caption(text:&str)->String {
        format!("<hp:caption side='BOTTOM' fullSz='1' width='-1' gap='7' lastWidth='9'><hp:subList><hp:p id='99'><hp:run><hp:t>{text}</hp:t></hp:run></hp:p></hp:subList></hp:caption>")
    }
    fn object(body:&str)->String {format!("<hp:rect id='7'>{body}</hp:rect>")}
    fn import(body:&str)->Result<ImportedDocumentStructure,Box<dyn Error>> {structure(&base::package(&fixture::paragraph(body))?,"caption-source")}
    #[test]
    fn caption_source_envelope_all_ten_owner_types_bind_original_nodes_and_source_fingerprints() -> TestResult {
        let mut body=String::new();
        for name in ["pic","rect","ellipse","line","arc","polygon","curve","connectLine","equation"] {
            body.push_str(&format!("<hp:{name} id='7'>{}</hp:{name}>",caption("private caption text")));
        }
        body.push_str(&fixture::table("<hp:t>cell</hp:t>").replace("</hp:tbl>",&format!("{}</hp:tbl>",caption("private table caption"))));
        let bytes=base::package(&fixture::paragraph(&body))?; let source=structure(&bytes,"caption-source")?;
        let before=ImportedReferenceTargets::import(&source,limits()?)?.receipt().clone();
        let captions=ImportedReferenceCaptions::import(&source,limits()?)?;
        assert_eq!(captions.targets().len(),10); assert_eq!(captions.receipt().caption_targets,10);
        assert_eq!(captions.envelopes().iter().map(|c|c.logical_object_id()).collect::<std::collections::BTreeSet<_>>().len(),10);
        for (target,observation) in captions.targets().iter().zip(captions.envelopes()) {
            assert_eq!(&target.logical_target_id,observation.logical_caption_id());
            assert_eq!(target.target_kind,ReferenceTargetKind::Caption); assert!(target.active&&target.anchor.is_none());
            let native=observation.native_envelope();
            assert_eq!((native.side,native.full_size,native.width_hwpunit,native.gap_hwpunit,native.last_width_hwpunit),(NativeCaptionSide::Bottom,true,-1,7,9));
            assert_eq!(native.semantic_binding,CaptionNativeSemanticBinding::UnverifiedSubListNumbering);
            let mut found=false;
            for part in source.source().parts() {
                let Some(xml)=part.xml() else {continue};
                for (index,node) in xml.elements().iter().enumerate().filter(|(_,e)|e.name().namespace()==Some("http://www.hancom.co.kr/hwpml/2011/paragraph")&&e.name().local_name()=="caption") {
                    let anchor=part.element_anchor(index).ok_or("caption anchor")?;
                    if observation.logical_caption_id().as_str()==format!("caption-{}",anchor.opaque_handle.as_str()) {
                        assert_eq!(native.opaque_native_state_sha256,hex::encode(anchor.fingerprint_sha256));
                        assert_eq!(native.sub_list_sha256,hex::encode(part.element_anchor(node.first_child().ok_or("sublist")?).ok_or("sublist anchor")?.fingerprint_sha256)); found=true;
                    }
                }
            }
            assert!(found);
        }
        assert_eq!(captions.receipt().target_inventory_sha256,<[u8;32]>::from(Sha256::digest(serde_json::to_vec(captions.targets())?)));
        assert_eq!(captions.receipt().envelope_inventory_sha256,<[u8;32]>::from(Sha256::digest(serde_json::to_vec(captions.envelopes())?)));
        assert_eq!(ImportedReferenceTargets::import(&source,limits()?)?.receipt(),&before);
        assert_eq!(captions.verify_source(&bytes)?,*captions.receipt());
        assert!(!format!("{captions:?}{:?}",captions.envelopes()).contains("private"));
        Ok(())
    }
    #[test]
    fn caption_source_envelope_exact_native_sides_and_boolean_forms_never_infer_numbering() -> TestResult {
        for (side,expected) in [("LEFT",NativeCaptionSide::Left),("RIGHT",NativeCaptionSide::Right),("TOP",NativeCaptionSide::Top),("BOTTOM",NativeCaptionSide::Bottom)] {
            for full in ["0","1","false","true"] {
                let body=object(&caption("private sequence label").replace("BOTTOM",side).replace("fullSz='1'",&format!("fullSz='{full}'")));
                let source=import(&body)?; let value=ImportedReferenceCaptions::import(&source,limits()?)?;
                assert_eq!(value.envelopes()[0].native_envelope().side,expected);
                assert_eq!(value.envelopes()[0].native_envelope().full_size,matches!(full,"1"|"true"));
                assert!(!value.receipt().sub_list_numbering_qualified); assert!(!value.receipt().complete_auxiliary_state_qualified);
            }
        }
        Ok(())
    }
    #[test]
    fn caption_source_envelope_missing_malformed_and_duplicate_data_fail_without_defaults() -> TestResult {
        let complete=caption("private label");
        let mut variants=Vec::new();
        for attr in [" side='BOTTOM'"," fullSz='1'"," width='-1'"," gap='7'"," lastWidth='9'"] {variants.push(complete.replace(attr,""));}
        for (before,after) in [("BOTTOM","UNKNOWN"),("fullSz='1'","fullSz='2'"),("width='-1'","width='-2'"),("gap='7'","gap='-1'"),("lastWidth='9'","lastWidth='4294967296'"),("hp:subList","u:subList")] {variants.push(complete.replace(before,after));}
        variants.push(complete.replace("</hp:caption>","<hp:subList/></hp:caption>"));
        variants.push(format!("{complete}{complete}"));
        for body in variants {
            let source=import(&object(&body))?;
            assert!(matches!(ImportedReferenceCaptions::import(&source,limits()?),Err(ReferenceCaptionImportError::Envelope)));
        }
        Ok(())
    }
    #[test]
    fn caption_source_envelope_whole_source_coverage_rejects_header_opaque_and_unsupported_owners() -> TestResult {
        for bytes in [package_with_header_control(&object(&caption("header")))?,
            base::package(&fixture::paragraph(&format!("<u:future>{}</u:future>",object(&caption("hidden")))))?,
            base::package(&fixture::paragraph(&caption("no owner")))?,
            base::package(&fixture::paragraph(&format!("<hp:container>{}</hp:container>",caption("unsupported owner"))))?] {
            let source=structure(&bytes,"caption-source")?;
            assert!(matches!(ImportedReferenceCaptions::import(&source,limits()?),Err(ReferenceCaptionImportError::Coverage)));
        }
        Ok(())
    }
    #[test]
    fn caption_source_envelope_nested_notes_tables_and_expanded_names_keep_distinct_identity() -> TestResult {
        let body=format!("{}{}",fixture::table(&object(&caption("table child"))),fixture::note(&object(&caption("note child"))));
        let source=import(&body)?; let value=ImportedReferenceCaptions::import(&source,limits()?)?;
        assert_eq!(value.targets().len(),2); assert_ne!(value.envelopes()[0].logical_object_id(),value.envelopes()[1].logical_object_id());
        let source=import("<hp:rect><u:caption/></hp:rect>")?;
        assert!(ImportedReferenceCaptions::import(&source,limits()?)?.targets().is_empty());
        let alias=caption("private alias").replace("hp:caption","a:caption").replace("<a:caption ","<a:caption xmlns:a='http://www.hancom.co.kr/hwpml/2011/paragraph' ");
        let source=import(&object(&alias))?; assert_eq!(ImportedReferenceCaptions::import(&source,limits()?)?.targets().len(),1);
        Ok(())
    }
    #[test]
    fn caption_source_envelope_item_extent_output_and_fresh_source_limits_are_enforced() -> TestResult {
        let bytes=base::package(&fixture::paragraph(&format!("{}{}",object(&caption("original")),object(&caption("second")))))?;
        let source=structure(&bytes,"caption-source")?; let original=ImportedReferenceCaptions::import(&source,limits()?)?;
        for config in [ReferenceAuxiliaryLimitConfig{items_per_kind:1,..Default::default()},ReferenceAuxiliaryLimitConfig{extent_hwpunit:6,..Default::default()},ReferenceAuxiliaryLimitConfig{input_bytes:1,output_bytes:1,..Default::default()}] {
            assert!(matches!(ImportedReferenceCaptions::import(&source,ReferenceAuxiliaryLimits::new(config)?),Err(ReferenceCaptionImportError::Limit)));
        }
        let changed=base::package(&fixture::paragraph(&format!("{}{}",object(&caption("changed")),object(&caption("second")))))?;
        assert!(matches!(original.verify_source(&changed),Err(ReferenceCaptionImportError::Binding)));
        let changed_source=structure(&changed,"caption-source")?; let changed_captions=ImportedReferenceCaptions::import(&changed_source,limits()?)?;
        assert_ne!(original.receipt().envelope_inventory_sha256,changed_captions.receipt().envelope_inventory_sha256);
        assert_ne!(original.receipt().target_inventory_sha256,changed_captions.receipt().target_inventory_sha256);
        Ok(())
    }
}

mod caption_layout_output {
    use super::*;
    use domain_ir::{LogicalId,NativeCaptionSide};
    use hwpx_package::{WriterLimits,document_import::{reference_targets::captions::ImportedReferenceCaptions,
        structure::caption_layout::{CaptionLayout,CaptionLayoutOutputCandidate,CaptionLayoutOutputError}}};
    use std::{collections::BTreeMap,io::{Cursor,Read}};
    fn caption()->String {
        "<hp:caption side='BOTTOM' fullSz='1' width='-1' gap='7' lastWidth='9' u:future='private opaque'><hp:subList><hp:p id='99'><hp:run charPrIDRef='4'><hp:t>private caption label</hp:t><hp:ctrl><hp:autoNum num='19' numType='PICTURE'><hp:autoNumFormat type='DIGIT' userChar='' prefixChar='' suffixChar='' supscript='0'/></hp:autoNum></hp:ctrl></hp:run></hp:p></hp:subList></hp:caption>".into()
    }
    fn layout()->CaptionLayout {CaptionLayout {side:NativeCaptionSide::Left,full_size:false,width_hwpunit:80,gap_hwpunit:12,last_width_hwpunit:40}}
    fn parts(bytes:&[u8])->Result<BTreeMap<String,Vec<u8>>,Box<dyn Error>> {
        let mut zip=zip::ZipArchive::new(Cursor::new(bytes))?; let mut parts=BTreeMap::new();
        for i in 0..zip.len() {let mut file=zip.by_index(i)?;let mut bytes=Vec::new();file.read_to_end(&mut bytes)?;parts.insert(file.name().to_owned(),bytes);}
        Ok(parts)
    }
    // Positive fixtures declare the style/border IDs actually referenced by
    // their runs and table cells. The real captured package is never rewritten.
    fn package(body:&str)->Result<Vec<u8>,Box<dyn Error>> {
        use std::io::Write;
        let mut original=parts(&base::package(body)?)?;
        original.insert("Contents/header.xml".into(),b"<hh:head xmlns:hh='http://www.hancom.co.kr/hwpml/2011/head'><hh:refList><hh:charProperties><hh:charPr id='4'/></hh:charProperties><hh:borderFills><hh:borderFill id='1'/></hh:borderFills></hh:refList></hh:head>".to_vec());
        let mut zip=zip::ZipWriter::new(Cursor::new(Vec::new()));
        let mimetype=original.remove("mimetype").ok_or("fixture mimetype")?;
        for (name,bytes) in std::iter::once(("mimetype".to_owned(),mimetype)).chain(original) {zip.start_file(name,zip::write::SimpleFileOptions::default().compression_method(zip::CompressionMethod::Stored))?;zip.write_all(&bytes)?;}
        Ok(zip.finish()?.into_inner())
    }
    fn id(source:&ImportedDocumentStructure,index:usize)->Result<LogicalId,Box<dyn Error>> {
        Ok(ImportedReferenceCaptions::import(source,limits()?)?.envelopes().get(index).ok_or("caption index")?.logical_caption_id().clone())
    }
    fn lower(source:&ImportedDocumentStructure,bytes:&[u8],index:usize,value:CaptionLayout)->Result<CaptionLayoutOutputCandidate,Box<dyn Error>> {
        Ok(source.lower_caption_layout_candidate(bytes,&id(source,index)?,value,limits()?,WriterLimits::default())?)
    }
    #[test]
    fn source_caption_layout_changes_only_five_attributes_and_keeps_numbering_and_all_parts() -> TestResult {
        let body=fixture::paragraph(&format!("<hp:rect id='7' lock='0'>{}</hp:rect><hp:t>private outside</hp:t>",caption()));
        let bytes=package(&body)?;let source=structure(&bytes,"caption-layout")?;
        let result=lower(&source,&bytes,0,layout())?;let output=result.with_verified_bytes(<[u8]>::to_vec)?;
        let before=parts(&bytes)?;let after=parts(&output)?;assert_eq!(before.keys().collect::<Vec<_>>(),after.keys().collect::<Vec<_>>());
        for (name,original) in &before {
            if name=="Contents/section0.xml" {
                let expected=String::from_utf8(original.clone())?.replace("side='BOTTOM'","side='LEFT'").replace("fullSz='1'","fullSz='0'")
                    .replace("width='-1'","width='80'").replace("gap='7'","gap='12'").replace("lastWidth='9'","lastWidth='40'");
                assert_eq!(after.get(name).map(Vec::as_slice),Some(expected.as_bytes()));
            } else {assert_eq!(after.get(name),Some(original));}
        }
        assert_eq!(result.receipt().changed_attributes,5);assert_ne!(result.receipt().source_caption_sha256,result.receipt().output_caption_sha256);
        assert!(result.receipt().outside_selected_attribute_values_exact&&result.receipt().numbering_and_caption_content_preserved);
        assert!(!result.receipt().complete_auxiliary_state_and_protection_verified&&!result.receipt().execution_publication_authority);
        let redacted=format!("{result:?}{}",String::from_utf8(serde_json::to_vec(result.receipt())?)?);
        for private in ["private opaque","private caption label","private outside"] {assert!(!redacted.contains(private));}
        Ok(())
    }
    #[test]
    fn source_caption_layout_keeps_lexical_aliases_uses_anchors_and_rejects_duplicate_native_ids() -> TestResult {
        let cap=caption().replace("fullSz='1'","fullSz='true'").replace("width='-1'","width='-01'").replace("gap='7'","gap='007'");
        let second=cap.replace("id='99'","id='100'");
        let body=fixture::paragraph(&format!("<hp:rect id='7'>{cap}</hp:rect><hp:rect id='8'>{second}</hp:rect>"));
        let bytes=package(&body)?;let source=structure(&bytes,"caption-layout-alias")?;
        assert_ne!(id(&source,0)?,id(&source,1)?);
        let original=CaptionLayout{side:NativeCaptionSide::Bottom,full_size:true,width_hwpunit:-1,gap_hwpunit:7,last_width_hwpunit:9};
        assert!(matches!(source.lower_caption_layout_candidate(&bytes,&id(&source,0)?,original,limits()?,WriterLimits::default()),Err(CaptionLayoutOutputError::NoChange)));
        let result=lower(&source,&bytes,1,CaptionLayout{side:NativeCaptionSide::Top,..original})?;
        assert_eq!(result.receipt().changed_attributes,1);
        let after=parts(&result.with_verified_bytes(<[u8]>::to_vec)?)?;
        let before=parts(&bytes)?;let xml=String::from_utf8(before["Contents/section0.xml"].clone())?;
        let start=xml.rfind("side='BOTTOM'").ok_or("second caption")?;
        let expected=format!("{}{}{}",&xml[..start],"side='TOP'",&xml[start+"side='BOTTOM'".len()..]);
        assert_eq!(after["Contents/section0.xml"],expected.as_bytes());
        let duplicate=package(&body.replace("id='8'","id='7'"))?;let source=structure(&duplicate,"caption-layout-duplicate")?;
        assert!(matches!(source.lower_caption_layout_candidate(&duplicate,&id(&source,1)?,layout(),limits()?,WriterLimits::default()),Err(CaptionLayoutOutputError::Patch("id_index_duplicate_declaration"))));
        let duplicate=package(&body.replace("id='100'","id='99'"))?;let source=structure(&duplicate,"caption-layout-duplicate-paragraph")?;
        assert!(matches!(source.lower_caption_layout_candidate(&duplicate,&id(&source,1)?,layout(),limits()?,WriterLimits::default()),Err(CaptionLayoutOutputError::Patch("id_index_duplicate_declaration"))));Ok(())
    }
    #[test]
    fn source_caption_layout_rejects_source_drift_foreign_selector_and_invalid_bounds() -> TestResult {
        let bytes=package(&fixture::paragraph(&format!("<hp:rect id='7'>{}</hp:rect>",caption())))?;
        let source=structure(&bytes,"caption-layout-bounds")?;let selected=id(&source,0)?;
        let changed=package(&fixture::paragraph(&format!("<hp:rect id='7'>{}</hp:rect>",caption().replace("private caption label","changed"))))?;
        assert!(matches!(source.lower_caption_layout_candidate(&changed,&selected,layout(),limits()?,WriterLimits::default()),Err(CaptionLayoutOutputError::Source)));
        assert!(matches!(source.lower_caption_layout_candidate(&bytes,&LogicalId::parse("foreign-caption")?,layout(),limits()?,WriterLimits::default()),Err(CaptionLayoutOutputError::Selection)));
        assert!(matches!(lower(&source,&bytes,0,CaptionLayout{width_hwpunit:-2,..layout()}),Err(e) if e.downcast_ref::<CaptionLayoutOutputError>()==Some(&CaptionLayoutOutputError::Value)));
        let tight=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig{extent_hwpunit:10,..Default::default()})?;
        assert!(matches!(source.lower_caption_layout_candidate(&bytes,&selected,layout(),tight,WriterLimits::default()),Err(CaptionLayoutOutputError::Limit)));
        let tight=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig{input_bytes:1,output_bytes:1,..Default::default()})?;
        assert!(matches!(source.lower_caption_layout_candidate(&bytes,&selected,layout(),tight,WriterLimits::default()),Err(CaptionLayoutOutputError::Limit)));
        let writer=WriterLimits::new(hwpx_package::WriterLimitConfig{max_output_bytes:1})?;
        assert!(matches!(source.lower_caption_layout_candidate(&bytes,&selected,layout(),limits()?,writer),Err(CaptionLayoutOutputError::Writer)));
        let dangling=base::package(&fixture::paragraph(&format!("<hp:rect id='7'>{}</hp:rect>",caption())))?;
        let source=structure(&dangling,"caption-layout-dangling")?;
        assert!(matches!(source.lower_caption_layout_candidate(&dangling,&id(&source,0)?,layout(),limits()?,WriterLimits::default()),Err(CaptionLayoutOutputError::Patch("id_index_dangling_reference"))));Ok(())
    }
    #[test]
    fn source_caption_layout_preserves_object_and_containing_table_protection() -> TestResult {
        for flag in ["1","true","unknown"] {
            let bytes=base::package(&fixture::paragraph(&format!("<hp:rect id='7' lock='{flag}'>{}</hp:rect>",caption())))?;
            let source=structure(&bytes,"caption-layout-lock")?;
            assert!(matches!(source.lower_caption_layout_candidate(&bytes,&id(&source,0)?,layout(),limits()?,WriterLimits::default()),Err(CaptionLayoutOutputError::Protection)));
        }
        let nested=format!("<hp:rect id='7' lock='0'>{}</hp:rect>",caption());
        for table in [fixture::table(&nested).replace("protect=\"0\"","protect=\"1\""),fixture::table(&nested).replace("lock=\"0\"","lock=\"1\"")] {
            let bytes=base::package(&fixture::paragraph(&table))?;let source=structure(&bytes,"caption-layout-table-lock")?;
            assert!(matches!(source.lower_caption_layout_candidate(&bytes,&id(&source,0)?,layout(),limits()?,WriterLimits::default()),Err(CaptionLayoutOutputError::Protection)));
        } Ok(())
    }
    #[test]
    fn source_caption_layout_supports_namespace_alias_and_nested_note_table_without_content_loss() -> TestResult {
        for object in [format!("<hp:rect id='7'>{}</hp:rect>",caption()),fixture::table("<hp:t>cell</hp:t>").replace("<hp:p id='1'>","<hp:p id='2'>").replace("</hp:tbl>",&format!("{}</hp:tbl>",caption()))] {
            let note=fixture::note(&object).replace("<hp:p id='1'>","<hp:p id='3'>");
            for body in [fixture::paragraph(&object),fixture::paragraph(&note)] {
                // The fixture root owns hp; q is explicitly bound on each paragraph.
                let body=body.replace("hp:","q:").replace("<q:p ","<q:p xmlns:q='http://www.hancom.co.kr/hwpml/2011/paragraph' ");
                let bytes=package(&body)?;
                let source=structure(&bytes,"caption-layout-prefix")?;let result=lower(&source,&bytes,0,layout())?;
                assert!(result.receipt().numbering_and_caption_content_preserved);assert_eq!(result.receipt().changed_attributes,5);
            }
        } Ok(())
    }
    #[test]
    fn source_caption_layout_original_complete_rectangle_package_is_read_only_candidate_not_native_acceptance() -> TestResult {
        let path=std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../fixtures/target-build/p09-19-object-caption-number-target-20261002-01/output/p09-19-c01-rectangle-caption-number.hwpx");
        let meta=std::fs::symlink_metadata(&path)?;assert!(meta.is_file()&&!meta.file_type().is_symlink());assert_eq!(meta.len(),7886);
        let bytes=std::fs::read(path)?;assert_eq!(hex::encode(Sha256::digest(&bytes)),"fe58ad76019828a0df0051fc54b97f98f04de82a8c46e7fc1d8b68ad5f2fbc91");
        let source=structure(&bytes,"caption-layout-original-rectangle")?;
        let original=ImportedReferenceCaptions::import(&source,limits()?)?;let native=original.envelopes()[0].native_envelope();
        let target=CaptionLayout{side:if native.side==NativeCaptionSide::Left {NativeCaptionSide::Right} else {NativeCaptionSide::Left},
            full_size:native.full_size,width_hwpunit:native.width_hwpunit,gap_hwpunit:native.gap_hwpunit,last_width_hwpunit:native.last_width_hwpunit};
        let result=lower(&source,&bytes,0,target)?;assert_eq!(result.receipt().changed_attributes,1);
        assert_eq!(result.receipt().preserved_sub_list_sha256,native.sub_list_sha256);
        assert!(result.receipt().numbering_and_caption_content_preserved&&!result.receipt().execution_publication_authority);Ok(())
    }
}

mod caption_numbering_source {
    use super::*;
    use hwpx_package::document_import::reference_targets::numbering::*;
    fn number(kind:&str,value:&str,format:&str)->String {
        format!("<hp:ctrl><hp:autoNum num='{value}' numType='{kind}'><hp:autoNumFormat type='{format}' userChar='' prefixChar='private prefix' suffixChar='' supscript='0'/></hp:autoNum></hp:ctrl>")
    }
    fn caption(body:&str)->String {format!("<hp:rect id='7'><hp:caption side='BOTTOM' fullSz='0' width='1000' gap='20' lastWidth='900'><hp:subList><hp:p id='99'><hp:run>{body}</hp:run></hp:p></hp:subList></hp:caption></hp:rect>")}
    fn start()->&'static str {"<hp:secPr><hp:startNum pageStartsOn='BOTH' page='0' pic='5' tbl='0' equation='3'/></hp:secPr>"}
    #[test]
    fn caption_numbering_source_reads_stored_cache_restart_and_section_start_without_resolving() -> TestResult {
        let body=fixture::paragraph(&format!("{}<hp:ctrl><hp:newNum num='4' numType='PICTURE'/></hp:ctrl>{}{}",start(),number("PAGE","8","DIGIT"),caption(&number("PICTURE","19","DIGIT"))));
        let bytes=base::package(&body)?;let source=structure(&bytes,"numbering-source")?;
        let imported=ImportedCaptionNumbering::import(&source,limits()?)?;
        assert_eq!((imported.receipt().auto_numbers,imported.receipt().caption_auto_numbers,imported.receipt().restart_controls,imported.receipt().section_starts),(2,1,1,1));
        assert_eq!(imported.section_starts()[0].picture,5);assert_eq!(imported.section_starts()[0].table,0);
        assert_eq!(imported.controls().iter().map(|c|c.stored_number).collect::<Vec<_>>(),[4,8,19]);
        assert_eq!(imported.controls()[0].kind,NativeNumberControlKind::Restart);assert!(imported.controls()[0].format.is_none());
        assert!(imported.controls()[1].logical_caption_id.is_none());assert!(imported.controls()[2].logical_caption_id.is_some());
        assert_eq!(imported.controls()[2].category,NativeNumberCategory::Picture);
        assert_eq!(imported.controls()[2].format.as_ref().ok_or("format")?.prefix_sha256,<[u8;32]>::from(Sha256::digest(b"private prefix")));
        assert!(!imported.receipt().sequence_interpretation_qualified&&!imported.receipt().native_recalculation_qualified&&!imported.receipt().complete_auxiliary_state_qualified);
        let redacted=format!("{imported:?}{}",String::from_utf8(serde_json::to_vec(imported.controls())?)?);assert!(!redacted.contains("private prefix"));
        assert_eq!(imported.receipt().control_inventory_sha256,<[u8;32]>::from(Sha256::digest(serde_json::to_vec(imported.controls())?)));
        assert_eq!(imported.verify_source(&bytes)?,*imported.receipt());Ok(())
    }
    #[test]
    fn caption_numbering_source_all_official_categories_and_formats_keep_unmapped_formats_explicit() -> TestResult {
        let types=["DIGIT","CIRCLED_DIGIT","ROMAN_CAPITAL","ROMAN_SMALL","LATIN_CAPITAL","LATIN_SMALL","CIRCLED_LATIN_CAPITAL","CIRCLED_LATIN_SMALL","HANGUL_SYLLABLE","CIRCLED_HANGUL_SYLLABLE","HANGUL_JAMO","CIRCLED_HANGUL_JAMO","HANGUL_PHONETIC","IDEOGRAPH","CIRCLED_IDEOGRAPH","DECAGON_CIRCLE","DECAGON_CIRCLE_HANJA","SYMBOL","USER_CHAR","SYMBOL2","IMAGE","2DIGIT"];
        let mut body=String::new();for format in types {body.push_str(&caption(&number("PICTURE","19",format)));}
        for category in ["PAGE","FOOTNOTE","ENDNOTE","PICTURE","TABLE","EQUATION","TOTAL_PAGE"] {body.push_str(&number(category,"0","DIGIT"));}
        for value in ["-2147483648","2147483647"] {body.push_str(&number("PICTURE",value,"DIGIT"));}
        let bytes=base::package(&fixture::paragraph(&body))?;let source=structure(&bytes,"all-numbering")?;let imported=ImportedCaptionNumbering::import(&source,limits()?)?;
        assert_eq!(imported.controls().len(),31);assert_eq!(imported.receipt().caption_auto_numbers,22);
        assert_eq!(imported.controls()[..22].iter().filter(|c|c.format.as_ref().is_some_and(|f|f.typed_format.is_some())).count(),7);
        assert_eq!(imported.controls()[29].stored_number,i32::MIN);assert_eq!(imported.controls()[30].stored_number,i32::MAX);
        assert!(imported.controls().iter().all(|c|!c.format.as_ref().is_some_and(|f|f.affixes_and_user_character_empty)));Ok(())
    }
    #[test]
    fn caption_numbering_source_missing_malformed_and_duplicate_values_fail_without_defaults() -> TestResult {
        let valid=number("PICTURE","19","DIGIT");let mut variants=Vec::new();
        for missing in [" num='19'"," numType='PICTURE'"," type='DIGIT'"," userChar=''"," prefixChar='private prefix'"," suffixChar=''"," supscript='0'"] {variants.push(valid.replace(missing,""));}
        for (a,b) in [("num='19'","num='2147483648'"),("numType='PICTURE'","numType='NONE'"),("type='DIGIT'","type='DIGTI'"),("supscript='0'","supscript='2'")] {variants.push(valid.replace(a,b));}
        variants.push(valid.replace("</hp:autoNum>","<hp:autoNumFormat type='DIGIT' userChar='' prefixChar='' suffixChar='' supscript='0'/></hp:autoNum>"));
        for value in variants {let bytes=base::package(&fixture::paragraph(&caption(&value)))?;let source=structure(&bytes,"bad-numbering")?;
            assert!(matches!(ImportedCaptionNumbering::import(&source,limits()?),Err(CaptionNumberingImportError::Value)));}
        for value in [start().replace(" pic='5'",""),start().replace("pageStartsOn='BOTH'","pageStartsOn='UNKNOWN'"),start().replace("tbl='0'","tbl='-1'"),start().replace("equation='3'","equation='4294967296'")] {
            let bytes=base::package(&fixture::paragraph(&value))?;let source=structure(&bytes,"bad-start")?;assert!(matches!(ImportedCaptionNumbering::import(&source,limits()?),Err(CaptionNumberingImportError::Value)));}
        Ok(())
    }
    #[test]
    fn caption_numbering_source_whole_xml_and_exact_control_ancestry_reject_hidden_or_header_controls() -> TestResult {
        let n=number("PICTURE","19","DIGIT");
        for bytes in [package_with_header_control(&fixture::paragraph(&n))?,base::package(&fixture::paragraph(&format!("<u:future>{}</u:future>",fixture::paragraph(&n))))?,
            base::package(&fixture::paragraph(&n.replace("hp:ctrl","u:ctrl")))?,base::package(&fixture::paragraph(&format!("{}{}",start(),start())))?] {
            let source=structure(&bytes,"coverage-numbering")?;assert!(matches!(ImportedCaptionNumbering::import(&source,limits()?),Err(CaptionNumberingImportError::Coverage)));}
        let bytes=base::package(&fixture::paragraph("<u:autoNum num='19'/><u:newNum/><u:startNum/>"))?;let source=structure(&bytes,"foreign-numbering")?;
        let imported=ImportedCaptionNumbering::import(&source,limits()?)?;assert!(imported.controls().is_empty()&&imported.section_starts().is_empty());Ok(())
    }
    #[test]
    fn caption_numbering_source_notes_tables_limits_and_fresh_identity_remain_source_bound() -> TestResult {
        let n=number("PICTURE","19","DIGIT");let body=format!("{}{}{}",fixture::table(&n),fixture::note(&n),caption(&n));
        let bytes=base::package(&fixture::paragraph(&body))?;let source=structure(&bytes,"numbering-nested")?;let imported=ImportedCaptionNumbering::import(&source,limits()?)?;
        assert_eq!(imported.controls().len(),3);assert_eq!(imported.receipt().caption_auto_numbers,1);
        assert_eq!(imported.controls().iter().map(|c|&c.logical_control_id).collect::<std::collections::BTreeSet<_>>().len(),3);
        for config in [ReferenceAuxiliaryLimitConfig{items_per_kind:2,..Default::default()},ReferenceAuxiliaryLimitConfig{input_bytes:1,output_bytes:1,..Default::default()},ReferenceAuxiliaryLimitConfig{text_bytes:1,..Default::default()}] {
            assert!(matches!(ImportedCaptionNumbering::import(&source,ReferenceAuxiliaryLimits::new(config)?),Err(CaptionNumberingImportError::Limit)));}
        let changed=base::package(&fixture::paragraph(&body.replace("num='19'","num='20'")))?;
        assert!(matches!(imported.verify_source(&changed),Err(CaptionNumberingImportError::Binding)));
        let other=structure(&bytes,"other-numbering-document")?;let other=ImportedCaptionNumbering::import(&other,limits()?)?;
        assert_ne!(imported.controls()[0].logical_control_id,other.controls()[0].logical_control_id);
        use std::io::{Cursor,Read,Write};
        let two=fixture::two_sections()?;let mut input=zip::ZipArchive::new(Cursor::new(two))?;let mut output=zip::ZipWriter::new(Cursor::new(Vec::new()));
        for index in 0..input.len() {let mut entry=input.by_index(index)?;let name=entry.name().to_owned();let mut data=Vec::new();entry.read_to_end(&mut data)?;
            if name.starts_with("Contents/section") {data=String::from_utf8(data)?.replace("<hp:bookmark name='same-across-sections'/>","<hp:newNum num='5' numType='TABLE'/>").into_bytes();}
            output.start_file(name,zip::write::SimpleFileOptions::default().compression_method(zip::CompressionMethod::Stored))?;output.write_all(&data)?;}
        let two=output.finish()?.into_inner();let source=structure(&two,"numbering-two-sections")?;let imported=ImportedCaptionNumbering::import(&source,limits()?)?;
        let tight=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig{sections:1,..Default::default()})?;
        assert!(matches!(ImportedCaptionNumbering::import(&source,tight),Err(CaptionNumberingImportError::Limit)));
        assert_eq!(imported.controls().len(),2);assert_ne!(imported.controls()[0].section_id,imported.controls()[1].section_id);
        assert_ne!(imported.controls()[0].logical_control_id,imported.controls()[1].logical_control_id);Ok(())
    }
    #[test]
    fn caption_numbering_source_complete_original_rectangle_cache19_is_not_recalculated_number1() -> TestResult {
        let path=std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../fixtures/target-build/p09-19-object-caption-number-target-20261002-01/output/p09-19-c01-rectangle-caption-number.hwpx");
        let meta=std::fs::symlink_metadata(&path)?;assert!(meta.is_file()&&!meta.file_type().is_symlink());assert_eq!(meta.len(),7886);
        let bytes=std::fs::read(path)?;assert_eq!(hex::encode(Sha256::digest(&bytes)),"fe58ad76019828a0df0051fc54b97f98f04de82a8c46e7fc1d8b68ad5f2fbc91");
        let source=structure(&bytes,"numbering-original-rectangle")?;let imported=ImportedCaptionNumbering::import(&source,limits()?)?;
        let captions=imported.controls().iter().filter(|c|c.logical_caption_id.is_some()&&c.kind==NativeNumberControlKind::AutoNumber).collect::<Vec<_>>();
        assert_eq!(captions.len(),1);assert_eq!(captions[0].stored_number,19);assert_eq!(captions[0].category,NativeNumberCategory::Picture);
        assert!(!imported.receipt().native_recalculation_qualified&&!imported.receipt().sequence_interpretation_qualified);Ok(())
    }
}

mod caption_numbering_context {
    use super::*;
    use hwpx_package::document_import::reference_targets::numbering::{ImportedCaptionNumbering,CaptionNumberingImportError,context::*};
    use std::io::{Cursor,Read,Write};
    fn begin()->&'static str {"<hh:beginNum page='1' footnote='2' endnote='3' pic='4' tbl='5' equation='6'/>"}
    fn header(body:&str)->String {format!("<hh:head xmlns:hh='http://www.hancom.co.kr/hwpml/2011/head' xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph' xmlns:u='urn:future'>{body}</hh:head>")}
    fn package(body:&str,head:&str)->Result<Vec<u8>,Box<dyn Error>> {
        let bytes=base::package(&fixture::paragraph(body))?;let mut input=zip::ZipArchive::new(Cursor::new(bytes))?;let mut output=zip::ZipWriter::new(Cursor::new(Vec::new()));
        for index in 0..input.len(){let mut entry=input.by_index(index)?;let name=entry.name().to_owned();let mut data=Vec::new();entry.read_to_end(&mut data)?;
            if name=="Contents/header.xml"{data=head.as_bytes().to_vec();}
            output.start_file(name,zip::write::SimpleFileOptions::default().compression_method(zip::CompressionMethod::Stored))?;output.write_all(&data)?;}
        Ok(output.finish()?.into_inner())
    }
    fn auto()->&'static str {"<hp:ctrl><hp:autoNum num='19' numType='PICTURE'><hp:autoNumFormat type='DIGIT' userChar='' prefixChar='' suffixChar='' supscript='0'/></hp:autoNum></hp:ctrl>"}
    fn caption()->String {format!("<hp:caption side='BOTTOM' fullSz='0' width='1000' gap='20' lastWidth='900'><hp:subList><hp:p id='99'><hp:run><hp:t>private caption content</hp:t>{}</hp:run></hp:p></hp:subList></hp:caption>",auto())}
    #[test]
    fn caption_numbering_context_explicit_document_starts_and_uncaptioned_owners_are_not_omitted() -> TestResult {
        let body=format!("<hp:rect id='7' numberingType='PICTURE'>{}</hp:rect><hp:rect id='8' numberingType='NONE'/><hp:equation id='9' numberingType='EQUATION'/>{}",caption(),fixture::table("<hp:t>private cell</hp:t>"));
        let bytes=package(&body,&header(begin()))?;let source=structure(&bytes,"numbering-context")?;let imported=ImportedCaptionNumbering::import(&source,limits()?)?;let context=imported.import_context(limits()?)?;
        let start=context.document_start().ok_or("document start")?;assert_eq!((start.page,start.footnote,start.endnote,start.picture,start.table,start.equation),(1,2,3,4,5,6));
        assert_eq!(context.receipt().known_owners,4);assert_eq!(context.receipt().uncaptioned_owners,3);assert_eq!(context.receipt().missing_owner_numbering_types,0);
        assert_eq!(context.owners()[0].numbering_type,Some(NativeOwnerNumberingType::Picture));assert!(context.owners()[0].logical_caption_id.is_some());
        assert_eq!(context.owners()[1].numbering_type,Some(NativeOwnerNumberingType::None));assert!(context.owners()[1].logical_caption_id.is_none());
        assert_eq!(context.ordered_controls().len(),1);assert_eq!(context.ordered_controls()[0].logical_control_id,imported.controls()[0].logical_control_id);
        assert!(context.owners()[0].source_position<context.ordered_controls()[0].source_position);
        assert!(!context.receipt().complete_auxiliary_state_and_sequence_interpretation_qualified);
        assert_eq!(context.receipt().owner_inventory_sha256,<[u8;32]>::from(Sha256::digest(serde_json::to_vec(context.owners())?)));
        let redacted=format!("{context:?}{}",String::from_utf8(serde_json::to_vec(context.owners())?)?);assert!(!redacted.contains("private"));Ok(())
    }
    #[test]
    fn caption_numbering_context_missing_values_remain_unknown_and_zero_is_not_defaulted() -> TestResult {
        let bytes=package("<hp:rect id='7'/><hp:rect id='8' numberingType='NONE'/>",&header(""))?;let source=structure(&bytes,"context-unknown")?;
        let imported=ImportedCaptionNumbering::import(&source,limits()?)?;let context=imported.import_context(limits()?)?;
        assert!(context.document_start().is_none());assert!(!context.receipt().document_start_observed);assert_eq!(context.receipt().missing_owner_numbering_types,1);
        assert_eq!(context.owners()[0].numbering_type,None);assert_eq!(context.owners()[1].numbering_type,Some(NativeOwnerNumberingType::None));
        let head=header(&begin().replace("page='1'","page='0'").replace("pic='4'","pic='4294967295'"));
        let bytes=package("<hp:t>body</hp:t>",&head)?;let source=structure(&bytes,"context-zero")?;let imported=ImportedCaptionNumbering::import(&source,limits()?)?;
        let context=imported.import_context(limits()?)?;assert_eq!(context.document_start().ok_or("start")?.page,0);assert_eq!(context.document_start().ok_or("start")?.picture,u32::MAX);Ok(())
    }
    #[test]
    fn caption_numbering_context_malformed_duplicate_hidden_or_foreign_placement_fails_closed() -> TestResult {
        let mut heads=Vec::new();for value in [" page='1'"," footnote='2'"," endnote='3'"," pic='4'"," tbl='5'"," equation='6'"]{heads.push(header(&begin().replace(value,"")));}
        heads.push(header(&begin().replace("pic='4'","pic='-1'")));heads.push(header(&begin().replace("tbl='5'","tbl='4294967296'")));heads.push(header(&format!("{}{}",begin(),begin())));
        for head in heads {let bytes=package("<hp:t>body</hp:t>",&head)?;let source=structure(&bytes,"context-invalid")?;let imported=ImportedCaptionNumbering::import(&source,limits()?)?;
            assert!(matches!(imported.import_context(limits()?),Err(CaptionNumberingImportError::Value)));}
        for (body,head) in [("<hp:t>body</hp:t>".to_owned(),header(&format!("<u:future>{}</u:future>",begin()))),
            (begin().replace("<hh:beginNum ","<hh:beginNum xmlns:hh='http://www.hancom.co.kr/hwpml/2011/head' "),header(""))] {
            let bytes=package(&body,&head)?;let source=structure(&bytes,"context-wrong-part")?;let imported=ImportedCaptionNumbering::import(&source,limits()?)?;
            assert!(matches!(imported.import_context(limits()?),Err(CaptionNumberingImportError::Coverage)));}
        let bytes=package("<hp:rect numberingType='INVALID'/>",&header(begin()))?;let source=structure(&bytes,"context-bad-kind")?;let imported=ImportedCaptionNumbering::import(&source,limits()?)?;
        assert!(matches!(imported.import_context(limits()?),Err(CaptionNumberingImportError::Value)));Ok(())
    }
    #[test]
    fn caption_numbering_context_spine_order_not_zip_order_binds_controls_and_owner_positions() -> TestResult {
        let mut input=zip::ZipArchive::new(Cursor::new(fixture::two_sections()?))?;let mut output=zip::ZipWriter::new(Cursor::new(Vec::new()));
        for index in 0..input.len(){let mut entry=input.by_index(index)?;let name=entry.name().to_owned();let mut data=Vec::new();entry.read_to_end(&mut data)?;
            if name=="Contents/content.hpf"{let text=String::from_utf8(data)?;let changed=text.replace("<o:spine><o:itemref idref=\"s\"/><o:itemref idref='s1'/></o:spine>","<o:spine><o:itemref idref='s1'/><o:itemref idref=\"s\"/></o:spine>");assert_ne!(text,changed);data=changed.into_bytes();}
            if name.starts_with("Contents/section"){data=String::from_utf8(data)?.replace("<hp:ctrl><hp:bookmark name='same-across-sections'/></hp:ctrl>","<hp:rect id='7' numberingType='PICTURE'/><hp:ctrl><hp:newNum num='5' numType='PICTURE'/></hp:ctrl>").into_bytes();}
            output.start_file(name,zip::write::SimpleFileOptions::default().compression_method(zip::CompressionMethod::Stored))?;output.write_all(&data)?;}
        let bytes=output.finish()?.into_inner();let source=structure(&bytes,"context-spine-order")?;let imported=ImportedCaptionNumbering::import(&source,limits()?)?;let context=imported.import_context(limits()?)?;
        assert_eq!(context.owners().len(),2);assert_eq!(context.ordered_controls().len(),2);
        assert_eq!(context.owners()[0].source_position.spine_ordinal,0);assert_eq!(context.owners()[1].source_position.spine_ordinal,1);
        assert_eq!(context.owners()[0].section_id,source.graph().sections()[0].section_id);assert_eq!(context.ordered_controls()[0].section_id,context.owners()[0].section_id);
        assert_ne!(context.ordered_controls()[0].logical_control_id,imported.controls()[0].logical_control_id);Ok(())
    }
    #[test]
    fn caption_numbering_context_all_ten_known_families_and_unrepresented_numbered_owners_are_checked() -> TestResult {
        let mut body=String::new();for name in ["pic","rect","ellipse","line","arc","polygon","curve","connectLine","equation"] {
            body.push_str(&format!("<hp:{name} id='7' numberingType='{}'/>",if name=="equation"{"EQUATION"}else{"PICTURE"}));}
        body.push_str(&fixture::table("<hp:t>cell</hp:t>"));let bytes=package(&body,&header(begin()))?;let source=structure(&bytes,"context-ten-families")?;
        let imported=ImportedCaptionNumbering::import(&source,limits()?)?;let context=imported.import_context(limits()?)?;assert_eq!(context.owners().len(),10);
        assert_eq!(context.owners().iter().map(|o|&o.logical_object_id).collect::<std::collections::BTreeSet<_>>().len(),10);
        for (body,head) in [("<hp:t>body</hp:t>".to_owned(),header("<hp:rect numberingType='PICTURE'/>")),
            ("<u:future><hp:rect numberingType='PICTURE'/></u:future>".to_owned(),header(begin())),
            ("<hp:chart numberingType='PICTURE'/>".to_owned(),header(begin()))] {
            let bytes=package(&body,&head)?;let source=structure(&bytes,"context-hidden-owner")?;let imported=ImportedCaptionNumbering::import(&source,limits()?)?;
            assert!(matches!(imported.import_context(limits()?),Err(CaptionNumberingImportError::Coverage)));}Ok(())
    }
    #[test]
    fn caption_numbering_context_limits_fresh_source_and_original_complete_package_keep_claim_boundaries() -> TestResult {
        let bytes=package("<hp:rect numberingType='PICTURE'/><hp:rect numberingType='NONE'/>",&header(begin()))?;let source=structure(&bytes,"context-limits")?;let imported=ImportedCaptionNumbering::import(&source,limits()?)?;
        for config in [ReferenceAuxiliaryLimitConfig{items_per_kind:1,..Default::default()},ReferenceAuxiliaryLimitConfig{input_bytes:1,output_bytes:1,..Default::default()}] {
            assert!(matches!(imported.import_context(ReferenceAuxiliaryLimits::new(config)?),Err(CaptionNumberingImportError::Limit)));}
        let context=imported.import_context(limits()?)?;assert_eq!(context.verify_source(&bytes)?,*context.receipt());
        let mut changed=bytes.clone();changed[0]^=1;assert!(matches!(context.verify_source(&changed),Err(CaptionNumberingImportError::Binding)));
        let path=std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../fixtures/target-build/p09-19-object-caption-number-target-20261002-01/output/p09-19-c01-rectangle-caption-number.hwpx");
        let meta=std::fs::symlink_metadata(&path)?;assert!(meta.is_file()&&!meta.file_type().is_symlink());assert_eq!(meta.len(),7886);let bytes=std::fs::read(path)?;
        assert_eq!(hex::encode(Sha256::digest(&bytes)),"fe58ad76019828a0df0051fc54b97f98f04de82a8c46e7fc1d8b68ad5f2fbc91");
        let source=structure(&bytes,"context-original-rectangle")?;let imported=ImportedCaptionNumbering::import(&source,limits()?)?;let context=imported.import_context(limits()?)?;
        assert!(context.document_start().is_some());let owner=context.owners().iter().find(|o|o.logical_caption_id.is_some()).ok_or("caption owner")?;
        assert_eq!(owner.numbering_type,Some(NativeOwnerNumberingType::Picture));assert_eq!(imported.controls().iter().find(|c|c.logical_caption_id==owner.logical_caption_id).ok_or("caption number")?.stored_number,19);
        assert!(!context.receipt().complete_auxiliary_state_and_sequence_interpretation_qualified);Ok(())
    }
}

mod caption_object_projection {
    use super::*;
    use hwpx_package::document_import::reference_targets::numbering::{ImportedCaptionNumbering,CaptionNumberingImportError};
    use hwpx_package::document_import::reference_targets::caption_object_state::ImportedCaptionObjectStates;
    fn caption()->&'static str {
        "<hp:caption side='BOTTOM' fullSz='0' width='1000' gap='20' lastWidth='900' u:future='private opaque'><hp:subList><hp:p id='99'><hp:run><hp:t>private caption</hp:t></hp:run></hp:p></hp:subList></hp:caption>"
    }
    fn owner(cap:&str,other:&str)->String {format!("<hp:rect id='7' numberingType='PICTURE' u:private='opaque body'>{other}{cap}</hp:rect>")}
    fn imported(source:&ImportedDocumentStructure)->Result<ImportedCaptionObjectStates<'_>,Box<dyn Error>> {
        // Returned projections borrow only the immutable source, not these
        // call-local inventories. They carry no caller-asserted context.
        let numbers=ImportedCaptionNumbering::import(source,limits()?)?;
        let context=numbers.import_context(limits()?)?;
        Ok(context.project_object_states(limits()?)?)
    }
    fn digests(body:&str)->Result<Vec<[u8;32]>,Box<dyn Error>> {
        let bytes=base::package(&fixture::paragraph(body))?;let source=structure(&bytes,"object-projection")?;
        Ok(imported(&source)?.objects().iter().map(|o|o.object_state_sha256).collect())
    }
    #[test]
    fn caption_object_projection_caption_changes_keep_body_identity_but_not_source_verification() -> TestResult {
        let original=owner(caption(),"<u:future>private body</u:future>");let expected=digests(&original)?;
        for (from,to) in [("side='BOTTOM'","side='LEFT'"),("width='1000'","width='13'"),("private caption","different caption content"),
            ("private opaque","changed opaque caption"),("<hp:run>","<hp:run charPrIDRef='21'>")] {
            let changed=original.replace(from,to);assert_ne!(original,changed);assert_eq!(digests(&changed)?,expected);
            let before=base::package(&fixture::paragraph(&original))?;let after=base::package(&fixture::paragraph(&changed))?;
            let source=structure(&before,"object-projection")?;let numbers=ImportedCaptionNumbering::import(&source,limits()?)?;let context=numbers.import_context(limits()?)?;
            let states=context.project_object_states(limits()?)?;
            assert!(matches!(states.verify_source(&after),Err(CaptionNumberingImportError::Binding)));
            let changed_source=structure(&after,"object-projection")?;let changed_numbers=ImportedCaptionNumbering::import(&changed_source,limits()?)?;
            assert_ne!(numbers.caption_import().receipt().envelope_inventory_sha256,changed_numbers.caption_import().receipt().envelope_inventory_sha256);
        }
        // Presence/position is retained; insertion/deletion is not silently
        // claimed as an existing-caption mutation with identical object state.
        assert_ne!(digests(&owner("","<u:future>private body</u:future>"))?,expected);
        Ok(())
    }
    #[test]
    fn caption_object_projection_all_non_caption_bytes_and_namespace_context_remain_bound() -> TestResult {
        let original=owner(caption(),"<u:future>private body</u:future><!--body comment-->");let expected=digests(&original)?;
        for changed in [original.replace("opaque body","changed body"),original.replace("private body","different body"),
            original.replace("body comment","new comment"),
            original.replace("<u:future>","<u:future xmlns:u='urn:changed'>"),
            original.replace("</hp:rect>","<u:caption>not admitted</u:caption></hp:rect>"),
            original.replace(caption(),&format!("<u:before/>{}",caption()))] {assert_ne!(digests(&changed)?,expected);}
        let forbidden=base::package(&fixture::paragraph(&format!("{original}<?future data?>")))?;
        assert!(structure(&forbidden,"projection-forbidden-PI").is_err());
        // Moving the same caption marker relative to other content is a change.
        assert_ne!(digests(&owner(caption(),"<u:before/>"))?,digests(&owner(&format!("{}<u:before/>",caption()),""))?);
        // Same raw owner, different inherited namespace identity.
        let bytes=base::package(&fixture::paragraph(&original))?;
        let mut input=zip::ZipArchive::new(std::io::Cursor::new(&bytes))?;let mut output=zip::ZipWriter::new(std::io::Cursor::new(Vec::new()));
        use std::io::{Read,Write};
        let mut changed_any=false;
        for i in 0..input.len(){let mut entry=input.by_index(i)?;let name=entry.name().to_owned();let mut data=Vec::new();entry.read_to_end(&mut data)?;
            if name=="Contents/section0.xml"{let old=String::from_utf8(data)?;let new=old.replace("urn:unmodeled-test","urn:different").replace("urn:future","urn:different");changed_any=old!=new;data=new.into_bytes();}
            output.start_file(name,zip::write::SimpleFileOptions::default().compression_method(zip::CompressionMethod::Stored))?;output.write_all(&data)?;}
        assert!(changed_any);let changed=output.finish()?.into_inner();let source=structure(&changed,"object-projection")?;
        let numbers=ImportedCaptionNumbering::import(&source,limits()?)?;let context=numbers.import_context(limits()?)?;
        assert_ne!(context.project_object_states(limits()?)?.objects()[0].object_state_sha256,expected[0]);Ok(())
    }
    #[test]
    fn caption_object_projection_nested_owners_all_families_and_duplicate_native_ids_stay_distinct() -> TestResult {
        let inner=owner(caption(),"<u:future>inner body</u:future>");let table=fixture::table(&inner);
        let table=table.replacen("</hp:tbl>",&format!("{}</hp:tbl>",caption()),1);
        let expected=digests(&table)?;assert_eq!(expected.len(),2);
        assert_eq!(digests(&table.replace("private caption","changed nested caption"))?,expected);
        let changed=digests(&table.replace("inner body","new inner body"))?;
        assert!(expected.iter().zip(changed).all(|(a,b)|*a!=b));
        let mut body=String::new();for name in ["pic","rect","ellipse","line","arc","polygon","curve","connectLine","equation"] {
            body.push_str(&format!("<hp:{name} id='7' numberingType='NONE'>{}</hp:{name}>",caption()));}
        body.push_str(&fixture::table("<hp:t>cell body</hp:t>"));
        let bytes=base::package(&fixture::paragraph(&body))?;let source=structure(&bytes,"projection-families")?;
        let numbers=ImportedCaptionNumbering::import(&source,limits()?)?;let context=numbers.import_context(limits()?)?;let states=context.project_object_states(limits()?)?;
        assert_eq!(states.objects().len(),10);assert_eq!(states.receipt().masked_caption_subtrees,9);
        assert_eq!(states.objects().iter().map(|o|&o.logical_object_id).collect::<std::collections::BTreeSet<_>>().len(),10);
        assert_eq!(states.objects().last().ok_or("table")?.excluded_caption_subtrees,0);
        Ok(())
    }
    // Independent, deliberately overlapping recursive oracle. Production uses
    // a reverse pass and fixed-size slots, never this per-owner traversal.
    fn oracle(xml:&hwpx_package::PreservingXmlDocument,raw:&[u8],index:usize)->Result<[u8;32],Box<dyn Error>> {
        let node=&xml.elements()[index];
        if node.name().namespace()==Some(hwpx_package::HANCOM_2020_PARAGRAPH_NAMESPACE)&&node.name().local_name()=="caption" {
            return Ok(Sha256::digest(b"hwpx-agent.caption-object-state/excluded-existing-caption-v1").into());
        }
        fn emit(hash:&mut Sha256,tag:u8,value:&[u8]){hash.update([tag]);hash.update((value.len() as u64).to_le_bytes());hash.update(value);}
        let mut hash=Sha256::new();hash.update(b"hwpx-agent.caption-object-state/existing-caption-mask-merkle-v1");
        emit(&mut hash,1,node.name().namespace().unwrap_or("").as_bytes());
        for attr in node.attributes(){emit(&mut hash,2,attr.name().namespace().unwrap_or("").as_bytes());}emit(&mut hash,3,&[]);
        let span=node.outer_span().ok_or("oracle span")?;let mut cursor=span.start();let mut child=node.first_child();
        while let Some(i)=child {let nested=&xml.elements()[i];let span=nested.outer_span().ok_or("oracle child")?;
            emit(&mut hash,4,&raw[cursor..span.start()]);emit(&mut hash,5,&oracle(xml,raw,i)?);cursor=span.end();child=nested.next_sibling();}
        emit(&mut hash,4,&raw[cursor..span.end()]);Ok(hash.finalize().into())
    }
    #[test]
    fn caption_object_projection_matches_recursive_oracle_and_original_captured_package() -> TestResult {
        let synthetic=base::package(&fixture::paragraph(&fixture::table(&owner(caption(),"<u:future>body</u:future>"))))?;
        let path=std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../fixtures/target-build/p09-19-object-caption-number-target-20261002-01/output/p09-19-c01-rectangle-caption-number.hwpx");
        let metadata=std::fs::symlink_metadata(&path)?;assert!(metadata.is_file()&&!metadata.file_type().is_symlink());assert_eq!(metadata.len(),7886);
        let captured=std::fs::read(path)?;assert_eq!(hex::encode(Sha256::digest(&captured)),"fe58ad76019828a0df0051fc54b97f98f04de82a8c46e7fc1d8b68ad5f2fbc91");
        for bytes in [synthetic,captured] {
            let source=structure(&bytes,"projection-oracle")?;let numbers=ImportedCaptionNumbering::import(&source,limits()?)?;let context=numbers.import_context(limits()?)?;let states=context.project_object_states(limits()?)?;
            for object in states.objects(){let path=&source.source().spine()[object.source_position.spine_ordinal];
                let xml=source.source().parts().iter().find(|part|part.path()==path).and_then(|part|part.xml()).ok_or("part")?;
                let mut archive=zip::ZipArchive::new(std::io::Cursor::new(&bytes))?;let mut raw=Vec::new();
                use std::io::Read;
                archive.by_name(path.as_str())?.read_to_end(&mut raw)?;
                assert_eq!(object.object_state_sha256,oracle(xml,&raw,object.source_position.xml_element_ordinal)?);}
            assert_eq!(states.verify_source(&bytes)?,*states.receipt());
            assert!(!states.receipt().complete_auxiliary_state_and_protection_qualified&&!states.receipt().execution_publication_authority);
            assert_eq!(states.receipt().object_states_sha256,<[u8;32]>::from(Sha256::digest(serde_json::to_vec(states.objects())?)));
            let redacted=format!("{states:?}{}",serde_json::to_string(states.objects())?);assert!(!redacted.contains("private"));
        }Ok(())
    }
    #[test]
    fn caption_object_projection_work_is_one_xml_pass_not_overlapping_owner_subtrees() -> TestResult {
        for depth in [4,6,8] {
            let mut body=owner(caption(),"<u:future>body</u:future>");for _ in 0..depth {body=fixture::table(&body);}
            let bytes=base::package(&fixture::paragraph(&body))?;let source=structure(&bytes,"projection-work")?;
            let numbers=ImportedCaptionNumbering::import(&source,limits()?)?;let context=numbers.import_context(limits()?)?;let states=context.project_object_states(limits()?)?;
            let path=&source.source().spine()[0];let xml=source.source().parts().iter().find(|part|part.path()==path).and_then(|part|part.xml()).ok_or("part")?;
            assert_eq!(states.receipt().projected_parts,1);assert_eq!(states.receipt().xml_elements_visited,xml.elements().len());
            assert!(states.receipt().raw_bytes_hashed<=xml.original_len());assert!(states.receipt().child_edges_hashed<xml.elements().len());
            assert_eq!(states.objects().len(),depth+1);assert!(states.objects().iter().all(|o|o.excluded_caption_subtrees==1));
            let overlapping:usize=states.objects().iter().map(|o|xml.elements()[o.source_position.xml_element_ordinal].outer_span().map_or(0,|span|span.len())).sum();
            assert!(overlapping>states.receipt().raw_bytes_hashed*2);
        }Ok(())
    }
    #[test]
    fn caption_object_projection_limits_identity_and_empty_sources_remain_fail_closed() -> TestResult {
        let body=format!("{}{}",owner(caption(),""),"<hp:rect id='8' numberingType='NONE'/>");let bytes=base::package(&fixture::paragraph(&body))?;
        let source=structure(&bytes,"projection-limits")?;let numbers=ImportedCaptionNumbering::import(&source,limits()?)?;let context=numbers.import_context(limits()?)?;
        for config in [ReferenceAuxiliaryLimitConfig{items_per_kind:1,..Default::default()},ReferenceAuxiliaryLimitConfig{input_bytes:1,output_bytes:1,..Default::default()}] {
            assert!(matches!(context.project_object_states(ReferenceAuxiliaryLimits::new(config)?),Err(CaptionNumberingImportError::Limit)));}
        let states=context.project_object_states(limits()?)?;let other=structure(&bytes,"projection-another-doc")?;
        let other_numbers=ImportedCaptionNumbering::import(&other,limits()?)?;let other_context=other_numbers.import_context(limits()?)?;let other_states=other_context.project_object_states(limits()?)?;
        assert_ne!(states.objects()[0].logical_object_id,other_states.objects()[0].logical_object_id);
        assert_eq!(states.objects()[0].object_state_sha256,other_states.objects()[0].object_state_sha256);
        let bytes=base::package(&fixture::paragraph("<hp:t>empty of owners</hp:t>"))?;let source=structure(&bytes,"projection-empty")?;
        let numbers=ImportedCaptionNumbering::import(&source,limits()?)?;let context=numbers.import_context(limits()?)?;let states=context.project_object_states(limits()?)?;
        assert!(states.objects().is_empty());assert_eq!((states.receipt().projected_parts,states.receipt().xml_elements_visited,states.receipt().raw_bytes_hashed),(0,0,0));
        let bytes=fixture::two_sections()?;let source=structure(&bytes,"projection-section-limit")?;
        let numbers=ImportedCaptionNumbering::import(&source,limits()?)?;let context=numbers.import_context(limits()?)?;
        let tight=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig{sections:1,..Default::default()})?;
        assert!(matches!(context.project_object_states(tight),Err(CaptionNumberingImportError::Limit)));
        Ok(())
    }
}

mod caption_source_frames {
    use super::*;
    use hwpx_package::document_import::reference_targets::numbering::{ImportedCaptionNumbering,CaptionNumberingImportError};
    use hwpx_package::document_import::reference_targets::caption_frames::{CaptionFrameSegmentKind as Kind,CaptionStyleReferenceStatus as Style};
    use std::io::{Cursor,Read,Write};
    fn auto()->&'static str {"<hp:ctrl><hp:autoNum num='19' numType='PICTURE'><hp:autoNumFormat type='DIGIT' userChar='' prefixChar='' suffixChar='' supscript='0'/></hp:autoNum></hp:ctrl>"}
    fn cap(paragraphs:&str)->String {format!("<hp:rect id='7'><hp:caption side='BOTTOM' fullSz='0' width='1000' gap='20' lastWidth='900'><hp:subList>{paragraphs}</hp:subList></hp:caption></hp:rect>")}
    fn p(body:&str)->String {format!("<hp:p id='99' paraPrIDRef='5' styleIDRef='6'>{body}</hp:p>")}
    fn run(body:&str)->String {format!("<hp:run charPrIDRef='4'>{body}</hp:run>")}
    fn declarations()->&'static str {"<hh:refList><hh:charProperties><hh:charPr id='4' private='private style'/><hh:charPr id='7'/></hh:charProperties><hh:paraProperties><hh:paraPr id='5'/></hh:paraProperties><hh:styles><hh:style id='6' name='private style name'/></hh:styles></hh:refList>"}
    fn package(body:&str,head:&str)->Result<Vec<u8>,Box<dyn Error>> {
        let bytes=base::package(&fixture::paragraph(body))?;let mut input=zip::ZipArchive::new(Cursor::new(bytes))?;let mut output=zip::ZipWriter::new(Cursor::new(Vec::new()));
        for i in 0..input.len(){let mut file=input.by_index(i)?;let name=file.name().to_owned();let mut data=Vec::new();file.read_to_end(&mut data)?;
            if name=="Contents/header.xml"{data=format!("<hh:head xmlns:hh='http://www.hancom.co.kr/hwpml/2011/head' xmlns:u='urn:future'>{head}</hh:head>").into_bytes();}
            output.start_file(name,zip::write::SimpleFileOptions::default().compression_method(zip::CompressionMethod::Stored))?;output.write_all(&data)?;}
        Ok(output.finish()?.into_inner())
    }
    #[test]
    fn caption_source_frames_exact_plain_text_order_styles_and_number_control_bindings_without_label_split() -> TestResult {
        let first=run("<hp:t>그림 &amp; </hp:t>");let second=run(&format!("{}<hp:t> &#xAC00; private suffix\r\nraw&#13;end</hp:t>",auto())).replace("charPrIDRef='4'","charPrIDRef='7'");
        let bytes=package(&cap(&p(&format!("{first}{second}"))),declarations())?;let source=structure(&bytes,"caption-frames")?;
        let numbers=ImportedCaptionNumbering::import(&source,limits()?)?;let frames=numbers.import_frames(limits()?)?;
        let frame=&frames.frames()[0];assert_eq!((frame.paragraphs.len(),frame.runs.len(),frame.segments.len()),(1,2,3));
        assert_eq!(frame.segments.iter().map(|s|s.kind).collect::<Vec<_>>(),[Kind::PlainText,Kind::AutoNumber,Kind::PlainText]);
        assert_eq!(frames.plain_text(&frame.segments[0].logical_source_id),Some("그림 & "));assert_eq!(frames.plain_text(&frame.segments[2].logical_source_id),Some(" 가 private suffix\nraw\rend"));
        assert_eq!(frames.plain_text(&frame.segments[1].logical_source_id),None);
        assert_eq!(frame.segments[1].number_control_id.as_ref(),Some(&numbers.controls()[0].logical_control_id));assert_eq!(numbers.controls()[0].stored_number,19);
        assert_eq!(frame.paragraphs[0].paragraph_style.reference_id,Some(5));assert_eq!(frame.paragraphs[0].named_style.reference_id,Some(6));
        assert!(frame.runs.iter().all(|r|r.character_style.status==Style::UniqueSourceDeclaration&&r.character_style.declaration_sha256.is_some()));
        assert_ne!(frame.runs[0].character_style.declaration_sha256,frame.runs[1].character_style.declaration_sha256);
        assert!(frame.single_auto_number_linear_layout_observed);assert_eq!(frames.receipt().unresolved_style_references,0);
        assert_eq!(frame.segments[0].decoded_text_sha256,Some(Sha256::digest("그림 & ".as_bytes()).into()));
        assert_eq!(frames.receipt().frames_sha256,<[u8;32]>::from(Sha256::digest(serde_json::to_vec(frames.frames())?)));
        let safe=format!("{frames:?}{}",serde_json::to_string(frames.frames())?);assert!(!safe.contains("private")&&!safe.contains("그림"));Ok(())
    }
    #[test]
    fn caption_source_frames_missing_ambiguous_and_misplaced_styles_never_become_default_or_effective_style() -> TestResult {
        let base=cap(&p(&run(&format!("<hp:t>label</hp:t>{}",auto()))));
        for (body,head,expected) in [
            (base.replace(" charPrIDRef='4'",""),declarations().to_owned(),Style::MissingReference),
            (base.replace("charPrIDRef='4'","charPrIDRef='99'"),declarations().to_owned(),Style::MissingDeclaration),
            (base.clone(),declarations().replace("<hh:charPr id='7'/>","<hh:charPr id='4'/>"),Style::AmbiguousDeclarations),
            (base.clone(),"<u:future><hh:charPr id='4'/></u:future>".into(),Style::UnverifiedDeclarationLocation),
        ] {
            let bytes=package(&body,&head)?;let source=structure(&bytes,"caption-style-status")?;let numbers=ImportedCaptionNumbering::import(&source,limits()?)?;let frames=numbers.import_frames(limits()?)?;
            let style=&frames.frames()[0].runs[0].character_style;assert_eq!(style.status,expected);assert!(style.declaration_sha256.is_none());
            assert!(!frames.receipt().effective_style_and_sequence_semantics_qualified);
        }
        for body in [base.replace("charPrIDRef='4'","charPrIDRef='-1'"),base.replace("paraPrIDRef='5'","paraPrIDRef='4294967296'")] {
            let bytes=package(&body,declarations())?;let source=structure(&bytes,"caption-invalid-style")?;let numbers=ImportedCaptionNumbering::import(&source,limits()?)?;
            assert!(matches!(numbers.import_frames(limits()?),Err(CaptionNumberingImportError::Value)));}
        Ok(())
    }
    #[test]
    fn caption_source_frames_rich_mixed_multiple_and_unknown_content_stays_explicit_not_concatenated() -> TestResult {
        let bodies=[
            p(&run(&format!("<hp:t>A<hp:tab/>B</hp:t>{}",auto()))),
            p(&run(&format!("<hp:t>A<!--private comment-->B</hp:t>{}",auto()))),
            p(&run(&format!("private direct text<hp:t>label</hp:t>{}",auto()))),
            format!("{}{}",p(&run("<hp:t>first</hp:t>")),p(&run(auto()))),
            p(&run(&format!("{}{}",auto(),auto()))),
            p(&run(&format!("<hp:ctrl><hp:newNum num='5' numType='PICTURE'/></hp:ctrl>{}",auto()))),
            p(&run(&format!("<u:autoNum/>{}",auto()))),
            p(&run(&format!("<hp:ctrl><hp:t>not a direct run leaf</hp:t></hp:ctrl>{}",auto()))),
        ];
        for body in bodies {let bytes=package(&cap(&body),declarations())?;let source=structure(&bytes,"caption-complex")?;
            let numbers=ImportedCaptionNumbering::import(&source,limits()?)?;let frames=numbers.import_frames(limits()?)?;
            assert!(!frames.frames()[0].single_auto_number_linear_layout_observed);
            assert!(frames.receipt().opaque_segments>0||frames.receipt().mixed_structural_containers>0||frames.receipt().paragraphs>1||frames.receipt().number_segments>1);
            for segment in &frames.frames()[0].segments {if segment.kind!=Kind::PlainText {assert!(frames.plain_text(&segment.logical_source_id).is_none());}}
        }
        let bytes=package(&cap(&p(&run(&format!("<hp:t/> {}",auto())))),declarations())?;let source=structure(&bytes,"caption-empty-text")?;
        let numbers=ImportedCaptionNumbering::import(&source,limits()?)?;let frames=numbers.import_frames(limits()?)?;
        assert_eq!(frames.plain_text(&frames.frames()[0].segments[0].logical_source_id),Some(""));Ok(())
    }
    #[test]
    fn caption_source_frames_spine_order_notes_tables_and_noncaption_controls_keep_source_identity() -> TestResult {
        let object=cap(&p(&run(&format!("<hp:t>label</hp:t>{}",auto()))));
        let body=format!("{}{}<hp:ctrl><hp:autoNum num='2' numType='PAGE'><hp:autoNumFormat type='DIGIT' userChar='' prefixChar='' suffixChar='' supscript='0'/></hp:autoNum></hp:ctrl>",fixture::table(&object),fixture::note(&object));
        let bytes=package(&body,declarations())?;let source=structure(&bytes,"caption-nested-frames")?;let numbers=ImportedCaptionNumbering::import(&source,limits()?)?;let frames=numbers.import_frames(limits()?)?;
        assert_eq!((frames.frames().len(),frames.receipt().number_segments,numbers.controls().len()),(2,2,3));
        assert_ne!(frames.frames()[0].logical_object_id,frames.frames()[1].logical_object_id);
        let mut input=zip::ZipArchive::new(Cursor::new(fixture::two_sections()?))?;let mut output=zip::ZipWriter::new(Cursor::new(Vec::new()));
        for i in 0..input.len(){let mut entry=input.by_index(i)?;let name=entry.name().to_owned();let mut data=Vec::new();entry.read_to_end(&mut data)?;
            if name=="Contents/content.hpf"{let text=String::from_utf8(data)?;let changed=text.replace("<o:spine><o:itemref idref=\"s\"/><o:itemref idref='s1'/></o:spine>","<o:spine><o:itemref idref='s1'/><o:itemref idref=\"s\"/></o:spine>");assert_ne!(text,changed);data=changed.into_bytes();}
            if name.starts_with("Contents/section"){data=String::from_utf8(data)?.replace("<hp:ctrl><hp:bookmark name='same-across-sections'/></hp:ctrl>",&object).into_bytes();}
            output.start_file(name,zip::write::SimpleFileOptions::default().compression_method(zip::CompressionMethod::Stored))?;output.write_all(&data)?;}
        let bytes=output.finish()?.into_inner();let source=structure(&bytes,"caption-frame-spine")?;let numbers=ImportedCaptionNumbering::import(&source,limits()?)?;let frames=numbers.import_frames(limits()?)?;
        assert_eq!(frames.frames().len(),2);assert_eq!(frames.frames()[0].source_position.spine_ordinal,0);assert_eq!(frames.frames()[1].source_position.spine_ordinal,1);
        assert_ne!(frames.frames()[0].logical_caption_id,numbers.caption_import().envelopes()[0].logical_caption_id().clone());Ok(())
    }
    #[test]
    fn caption_source_frames_item_text_output_and_fresh_source_limits_cannot_be_bypassed() -> TestResult {
        let body=cap(&p(&run(&format!("<hp:t>private label</hp:t>{}",auto()))));let bytes=package(&body,"")?;let source=structure(&bytes,"caption-frame-limits")?;
        let numbers=ImportedCaptionNumbering::import(&source,limits()?)?;let frames=numbers.import_frames(limits()?)?;
        for config in [ReferenceAuxiliaryLimitConfig{items_per_kind:1,..Default::default()},ReferenceAuxiliaryLimitConfig{text_bytes:2,..Default::default()},ReferenceAuxiliaryLimitConfig{input_bytes:1,output_bytes:1,..Default::default()}] {
            assert!(matches!(numbers.import_frames(ReferenceAuxiliaryLimits::new(config)?),Err(CaptionNumberingImportError::Limit)));}
        let changed=package(&body.replace("private label","new label"),"")?;assert!(matches!(frames.verify_source(&changed),Err(CaptionNumberingImportError::Binding)));
        assert_eq!(frames.verify_source(&bytes)?,*frames.receipt());
        let other=structure(&bytes,"caption-frame-other-doc")?;let other_numbers=ImportedCaptionNumbering::import(&other,limits()?)?;let other_frames=other_numbers.import_frames(limits()?)?;
        assert!(other_frames.plain_text(&frames.frames()[0].segments[0].logical_source_id).is_none());
        let bytes=fixture::two_sections()?;let source=structure(&bytes,"caption-frame-section-limit")?;let numbers=ImportedCaptionNumbering::import(&source,limits()?)?;
        assert!(matches!(numbers.import_frames(ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig{sections:1,..Default::default()})?),Err(CaptionNumberingImportError::Limit)));Ok(())
    }
    #[test]
    fn caption_source_frames_original_complete_rectangle_is_read_only_and_never_resolves_number19() -> TestResult {
        let path=std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../fixtures/target-build/p09-19-object-caption-number-target-20261002-01/output/p09-19-c01-rectangle-caption-number.hwpx");
        let meta=std::fs::symlink_metadata(&path)?;assert!(meta.is_file()&&!meta.file_type().is_symlink());assert_eq!(meta.len(),7886);let bytes=std::fs::read(path)?;
        assert_eq!(hex::encode(Sha256::digest(&bytes)),"fe58ad76019828a0df0051fc54b97f98f04de82a8c46e7fc1d8b68ad5f2fbc91");
        let source=structure(&bytes,"caption-frames-original")?;let numbers=ImportedCaptionNumbering::import(&source,limits()?)?;let frames=numbers.import_frames(limits()?)?;
        assert_eq!(frames.frames().len(),1);assert_eq!(frames.frames()[0].logical_caption_id,*numbers.caption_import().envelopes()[0].logical_caption_id());
        assert_eq!(frames.receipt().number_segments,1);assert!(numbers.controls().iter().any(|c|c.logical_caption_id.is_some()&&c.stored_number==19));
        assert!(!frames.receipt().effective_style_and_sequence_semantics_qualified&&!frames.receipt().complete_auxiliary_state_and_protection_qualified&&!frames.receipt().execution_publication_authority);
        assert_eq!(frames.verify_source(&bytes)?,*frames.receipt());Ok(())
    }
}

mod caption_text_output {
    use super::*;
    use domain_ir::LogicalId;
    use hwpx_package::{WriterLimits,document_import::{reference_targets::numbering::ImportedCaptionNumbering,
        structure::caption_text::{CaptionTextOutputError as E,CaptionTextOutputCandidate}}};
    use std::{collections::BTreeMap,io::{Cursor,Read,Write}};
    fn caption(leaf:&str)->String {format!("<hp:caption side='BOTTOM' fullSz='0' width='1000' gap='20' lastWidth='900' u:future='private opaque'><hp:subList><hp:p id='99'><hp:run charPrIDRef='4'>{leaf}<hp:ctrl><hp:autoNum num='19' numType='PICTURE'><hp:autoNumFormat type='DIGIT' userChar='' prefixChar='' suffixChar='' supscript='0'/></hp:autoNum></hp:ctrl><hp:t>private unchanged suffix</hp:t></hp:run></hp:p></hp:subList></hp:caption>")}
    fn object(leaf:&str)->String {format!("<hp:rect id='7' lock='0'>{}</hp:rect>",caption(leaf))}
    fn package(body:&str)->Result<Vec<u8>,Box<dyn Error>> {
        let bytes=base::package(&fixture::paragraph(body))?;let mut input=zip::ZipArchive::new(Cursor::new(bytes))?;let mut output=zip::ZipWriter::new(Cursor::new(Vec::new()));
        for i in 0..input.len(){let mut file=input.by_index(i)?;let name=file.name().to_owned();let mut data=Vec::new();file.read_to_end(&mut data)?;
            if name=="Contents/header.xml"{data=b"<hh:head xmlns:hh='http://www.hancom.co.kr/hwpml/2011/head'><hh:refList><hh:charProperties><hh:charPr id='4'/></hh:charProperties><hh:borderFills><hh:borderFill id='1'/></hh:borderFills></hh:refList></hh:head>".to_vec();}
            output.start_file(name,zip::write::SimpleFileOptions::default().compression_method(zip::CompressionMethod::Stored))?;output.write_all(&data)?;}
        Ok(output.finish()?.into_inner())
    }
    fn ids(source:&ImportedDocumentStructure,frame:usize,segment:usize)->Result<(LogicalId,LogicalId),Box<dyn Error>> {
        let numbering=ImportedCaptionNumbering::import(source,limits()?)?;let frames=numbering.import_frames(limits()?)?;
        let frame=frames.frames().get(frame).ok_or("frame")?;Ok((frame.logical_caption_id.clone(),frame.segments.get(segment).ok_or("segment")?.logical_source_id.clone()))
    }
    fn lower(source:&ImportedDocumentStructure,bytes:&[u8],frame:usize,segment:usize,value:&str)->Result<CaptionTextOutputCandidate,Box<dyn Error>> {
        let (caption,text)=ids(source,frame,segment)?;Ok(source.lower_caption_text_candidate(bytes,&caption,&text,value,limits()?,WriterLimits::default())?)
    }
    fn parts(bytes:&[u8])->Result<BTreeMap<String,Vec<u8>>,Box<dyn Error>> {
        let mut zip=zip::ZipArchive::new(Cursor::new(bytes))?;let mut result=BTreeMap::new();
        for i in 0..zip.len(){let mut file=zip.by_index(i)?;let mut data=Vec::new();file.read_to_end(&mut data)?;result.insert(file.name().to_owned(),data);}Ok(result)
    }
    #[test]
    fn caption_text_output_changes_exact_leaf_preserving_number_style_other_content_and_package_parts() -> TestResult {
        let bytes=package(&format!("{}<hp:t>private outside</hp:t>",object("<hp:t u:future='unchanged'>old&#38;text</hp:t>")))?;let source=structure(&bytes,"caption-text")?;
        let result=lower(&source,&bytes,0,0,"새 & <태그> \" ' \r\n끝")?;let output=result.with_verified_bytes(<[u8]>::to_vec)?;
        let before=parts(&bytes)?;let after=parts(&output)?;assert_eq!(before.keys().collect::<Vec<_>>(),after.keys().collect::<Vec<_>>());
        for (part,old) in &before {if part=="Contents/section0.xml" {
            let expected=String::from_utf8(old.clone())?.replacen("old&#38;text","새 &amp; &lt;태그&gt; \" ' &#13;\n끝",1);assert_eq!(after[part],expected.as_bytes());
        } else {assert_eq!(&after[part],old);}}
        assert_ne!(result.receipt().source_caption_sha256,result.receipt().output_caption_sha256);
        assert!(result.receipt().outside_selected_leaf_edit_exact&&result.receipt().numbering_style_and_other_caption_content_preserved);
        assert!(!result.receipt().complete_auxiliary_state_and_protection_verified&&!result.receipt().execution_publication_authority);
        assert!(!format!("{result:?}{}",serde_json::to_string(result.receipt())?).contains("private"));Ok(())
    }
    #[test]
    fn caption_text_output_self_closing_empty_entity_aliases_and_semantic_noop_keep_lexical_bytes() -> TestResult {
        for (leaf,expected) in [("<hp:t u:future='keep' />","<hp:t u:future='keep' >가😀 &amp;\n</hp:t>"),
            ("<a:t xmlns:a='http://www.hancom.co.kr/hwpml/2011/paragraph'></a:t>","<a:t xmlns:a='http://www.hancom.co.kr/hwpml/2011/paragraph'>가😀 &amp;\n</a:t>")] {
            let bytes=package(&object(leaf))?;let source=structure(&bytes,"caption-text-empty")?;let result=lower(&source,&bytes,0,0,"가😀 &\n")?;
            let before=parts(&bytes)?;let after=parts(&result.with_verified_bytes(<[u8]>::to_vec)?)?;
            assert_eq!(after["Contents/section0.xml"],String::from_utf8(before["Contents/section0.xml"].clone())?.replacen(leaf,expected,1).as_bytes());}
        for (leaf,same) in [("<hp:t>a&#38;b</hp:t>","a&b"),("<hp:t/>","")] {let bytes=package(&object(leaf))?;let source=structure(&bytes,"caption-text-noop")?;let (cap,text)=ids(&source,0,0)?;
            assert!(matches!(source.lower_caption_text_candidate(&bytes,&cap,&text,same,limits()?,WriterLimits::default()),Err(E::NoChange)));}Ok(())
    }
    #[test]
    fn caption_text_output_drift_cross_caption_opaque_number_and_outside_selectors_are_rejected() -> TestResult {
        let first=object("<hp:t>first</hp:t>");let second=object("<hp:t>second</hp:t>").replace("id='7'","id='8'").replace("id='99'","id='100'");
        let bytes=package(&format!("{first}{second}<hp:t>outside</hp:t>"))?;let source=structure(&bytes,"caption-text-selectors")?;
        let (cap,text)=ids(&source,0,0)?;let (_,other)=ids(&source,1,0)?;let (_,number)=ids(&source,0,1)?;
        for selector in [other,number,LogicalId::parse("foreign-caption-segment")?] {assert!(matches!(source.lower_caption_text_candidate(&bytes,&cap,&selector,"new",limits()?,WriterLimits::default()),Err(E::Selection)));}
        let changed=package(&format!("{}{}",first.replace("first","changed"),second))?;
        assert!(matches!(source.lower_caption_text_candidate(&changed,&cap,&text,"new",limits()?,WriterLimits::default()),Err(E::Source)));
        for leaf in ["<hp:t>A<hp:tab/>B</hp:t>","<hp:t>A<!--KEEP-->B</hp:t>"] {let bytes=package(&object(leaf))?;let source=structure(&bytes,"caption-text-opaque")?;
            assert!(matches!(lower(&source,&bytes,0,0,"new"),Err(error) if error.downcast_ref::<E>()==Some(&E::Selection)));}
        Ok(())
    }
    #[test]
    fn caption_text_output_observed_protection_invalid_values_limits_and_duplicate_ids_fail_closed() -> TestResult {
        let body=object("<hp:t>old</hp:t>");
        for protected in [body.replace("lock='0'","lock='1'"),body.replace("lock='0'","lock='unknown'"),
            fixture::table(&body).replace("protect=\"0\"","protect=\"1\""),fixture::table(&body).replace("lock=\"0\"","lock=\"1\"")] {
            let bytes=package(&protected)?;let source=structure(&bytes,"caption-text-protection")?;
            assert!(matches!(lower(&source,&bytes,0,0,"new"),Err(error) if error.downcast_ref::<E>()==Some(&E::Protection)));}
        let bytes=package(&body)?;let source=structure(&bytes,"caption-text-limits")?;let (cap,text)=ids(&source,0,0)?;
        assert!(matches!(source.lower_caption_text_candidate(&bytes,&cap,&text,"bad\0",limits()?,WriterLimits::default()),Err(E::Value)));
        for config in [ReferenceAuxiliaryLimitConfig{text_bytes:1,..Default::default()},ReferenceAuxiliaryLimitConfig{input_bytes:1,output_bytes:1,..Default::default()}] {
            assert!(matches!(source.lower_caption_text_candidate(&bytes,&cap,&text,"new",ReferenceAuxiliaryLimits::new(config)?,WriterLimits::default()),Err(E::Limit)));}
        assert!(matches!(source.lower_caption_text_candidate(&bytes,&cap,&text,"new",limits()?,WriterLimits::new(hwpx_package::WriterLimitConfig{max_output_bytes:1})?),Err(E::Writer)));
        let duplicate=format!("{}{}",body,object("<hp:t>other</hp:t>").replace("id='99'","id='100'"));let bytes=package(&duplicate)?;let source=structure(&bytes,"caption-text-duplicate")?;
        assert!(matches!(lower(&source,&bytes,0,0,"new"),Err(error) if matches!(error.downcast_ref::<E>(),Some(E::Patch("id_index_duplicate_declaration")))));Ok(())
    }
    #[test]
    fn caption_text_output_nested_tables_and_exact_form_reconstruction_reuse_original_whole_source_proof() -> TestResult {
        let body=fixture::table(&object("<hp:t>old</hp:t>")).replace("<hp:p id='1'>","<hp:p id='2'>");let bytes=package(&body)?;
        let package=ImportedSourcePackage::import(&bytes,DocumentId::parse("caption-text-proof")?,Sha256::digest(&bytes).into(),SourceImportLimits::default())?;
        let forms=hwpx_package::document_import::forms::ImportedDocumentForms::import(package)?;let source=forms.body_structure();let (cap,text)=ids(source,0,0)?;
        let direct=source.lower_caption_text_candidate(&bytes,&cap,&text,"new",limits()?,WriterLimits::default())?;
        let proof=forms.reconstruct_source_for_verification(&bytes)?;
        let bound=proof.lower_caption_text_candidate(&forms,&bytes,&cap,&text,"new",limits()?,WriterLimits::default())?;
        assert_eq!(parts(&direct.with_verified_bytes(<[u8]>::to_vec)?)?,parts(&bound.with_verified_bytes(<[u8]>::to_vec)?)?);
        let foreign=base::forms(&bytes,"caption-text-other-form")?;
        assert!(matches!(proof.lower_caption_text_candidate(&foreign,&bytes,&cap,&text,"new",limits()?,WriterLimits::default()),Err(E::Source)));
        let mut changed=bytes.clone();changed[0]^=1;
        assert!(matches!(proof.lower_caption_text_candidate(&forms,&changed,&cap,&text,"new",limits()?,WriterLimits::default()),Err(E::Source)));Ok(())
    }
    #[test]
    fn caption_text_output_original_complete_rectangle_memory_candidate_preserves_stored_number19() -> TestResult {
        let path=std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../fixtures/target-build/p09-19-object-caption-number-target-20261002-01/output/p09-19-c01-rectangle-caption-number.hwpx");
        let metadata=std::fs::symlink_metadata(&path)?;assert!(metadata.is_file()&&!metadata.file_type().is_symlink());assert_eq!(metadata.len(),7886);let bytes=std::fs::read(&path)?;
        assert_eq!(hex::encode(Sha256::digest(&bytes)),"fe58ad76019828a0df0051fc54b97f98f04de82a8c46e7fc1d8b68ad5f2fbc91");
        let source=structure(&bytes,"caption-text-original")?;let numbering=ImportedCaptionNumbering::import(&source,limits()?)?;let frames=numbering.import_frames(limits()?)?;
        let segment=frames.frames()[0].segments.iter().position(|s|frames.plain_text(&s.logical_source_id).is_some()).ok_or("original plain text")?;
        let candidate=lower(&source,&bytes,0,segment,"새 캡션 본문")?;let output=candidate.with_verified_bytes(<[u8]>::to_vec)?;
        let after=structure(&output,"caption-text-original")?;let numbers=ImportedCaptionNumbering::import(&after,limits()?)?;
        assert!(numbers.controls().iter().any(|c|c.logical_caption_id.is_some()&&c.stored_number==19));
        assert!(!candidate.receipt().complete_auxiliary_state_and_protection_verified&&!candidate.receipt().execution_publication_authority);
        assert_eq!(std::fs::read(path)?,bytes);Ok(())
    }
}

mod caption_text_batch_output {
    use super::*;
    use domain_ir::LogicalId;
    use hwpx_package::{WriterLimits,document_import::{reference_targets::numbering::ImportedCaptionNumbering,
        structure::{caption_text::CaptionTextOutputError as E,caption_text_batch::CaptionTextReplacement as Request}}};
    use std::{collections::BTreeMap,io::{Cursor,Read,Write}};
    const HEADER:&str="<hh:head xmlns:hh='http://www.hancom.co.kr/hwpml/2011/head'><hh:refList><hh:charProperties><hh:charPr id='4'/></hh:charProperties><hh:borderFills><hh:borderFill id='1'/></hh:borderFills></hh:refList></hh:head>";
    fn object(index:usize,leaf:&str)->String {format!("<hp:rect id='{}' lock='0'><hp:caption side='BOTTOM' fullSz='0' width='1000' gap='20' lastWidth='900'><hp:subList><hp:p id='{}'><hp:run charPrIDRef='4'>{leaf}<hp:ctrl><hp:autoNum num='19' numType='PICTURE'><hp:autoNumFormat type='DIGIT' userChar='' prefixChar='' suffixChar='' supscript='0'/></hp:autoNum></hp:ctrl><hp:t>oldB</hp:t></hp:run></hp:p></hp:subList></hp:caption></hp:rect>",7+index,99+index)}
    fn rewrite(bytes:&[u8],mut change:impl FnMut(&str,Vec<u8>)->Result<Vec<u8>,Box<dyn Error>>)->Result<Vec<u8>,Box<dyn Error>> {
        let mut input=zip::ZipArchive::new(Cursor::new(bytes))?;let mut output=zip::ZipWriter::new(Cursor::new(Vec::new()));
        for i in 0..input.len(){let mut file=input.by_index(i)?;let name=file.name().to_owned();let mut data=Vec::new();file.read_to_end(&mut data)?;
            let data=change(&name,data)?;output.start_file(name,zip::write::SimpleFileOptions::default().compression_method(zip::CompressionMethod::Stored))?;output.write_all(&data)?;}
        Ok(output.finish()?.into_inner())
    }
    fn package(body:&str)->Result<Vec<u8>,Box<dyn Error>> {
        rewrite(&base::package(body)?,|name,data|Ok(if name=="Contents/header.xml"{HEADER.as_bytes().to_vec()}else{data}))
    }
    fn selections(source:&ImportedDocumentStructure)->Result<Vec<(LogicalId,LogicalId)>,Box<dyn Error>> {
        let numbers=ImportedCaptionNumbering::import(source,limits()?)?;let frames=numbers.import_frames(limits()?)?;
        Ok(frames.frames().iter().flat_map(|frame|frame.segments.iter().filter(|s|frames.plain_text(&s.logical_source_id).is_some()).map(|s|(frame.logical_caption_id.clone(),s.logical_source_id.clone()))).collect())
    }
    fn parts(bytes:&[u8])->Result<BTreeMap<String,Vec<u8>>,Box<dyn Error>> {
        let mut input=zip::ZipArchive::new(Cursor::new(bytes))?;let mut result=BTreeMap::new();
        for i in 0..input.len(){let mut file=input.by_index(i)?;let mut data=Vec::new();file.read_to_end(&mut data)?;result.insert(file.name().to_owned(),data);}Ok(result)
    }
    #[test]
    fn caption_text_batch_output_multiple_caps_noop_aliases_and_other_bytes_are_one_atomic_candidate() -> TestResult {
        let body=fixture::paragraph(&format!("{}{}",object(0,"<hp:t>old&#38;A</hp:t>"),object(1,"<hp:t/>")));let bytes=package(&body)?;let source=structure(&bytes,"batch-captions")?;let ids=selections(&source)?;
        let requests=[Request{caption_id:&ids[2].0,text_id:&ids[2].1,replacement:"new & <값>\r\n"},Request{caption_id:&ids[0].0,text_id:&ids[0].1,replacement:"newA"},Request{caption_id:&ids[1].0,text_id:&ids[1].1,replacement:"oldB"}];
        let result=source.lower_caption_text_batch_candidate(&bytes,&requests,limits()?,WriterLimits::default())?;let output=result.with_verified_bytes(<[u8]>::to_vec)?;
        assert_eq!((result.receipt().requested_leaves,result.receipt().changed_leaves,result.receipt().changed_parts),(3,2,1));
        let before=parts(&bytes)?;let after=parts(&output)?;assert_eq!(before.keys().collect::<Vec<_>>(),after.keys().collect::<Vec<_>>());
        for (part,old) in before {if part=="Contents/section0.xml"{assert_eq!(after[&part],String::from_utf8(old)?.replacen("old&#38;A","newA",1).replacen("<hp:t/>","<hp:t>new &amp; &lt;값&gt;&#13;\n</hp:t>",1).as_bytes());}else{assert_eq!(after[&part],old);}}
        assert!(result.receipt().outside_selected_leaf_edits_exact&&!result.receipt().complete_auxiliary_state_and_protection_verified&&!result.receipt().execution_publication_authority);
        assert!(!format!("{result:?}{}",serde_json::to_string(result.receipt())?).contains("newA"));Ok(())
    }
    #[test]
    fn caption_text_batch_output_single_leaf_matches_existing_writer_and_all_noops_preserve_lexical_source() -> TestResult {
        for leaf in ["<hp:t>old&#38;A</hp:t>","<hp:t u:future='keep' />","<a:t xmlns:a='http://www.hancom.co.kr/hwpml/2011/paragraph'></a:t>"] {
            let bytes=package(&fixture::paragraph(&object(0,leaf)))?;let source=structure(&bytes,"batch-single-oracle")?;let ids=selections(&source)?;
            let single=source.lower_caption_text_candidate(&bytes,&ids[0].0,&ids[0].1,"새 & <x>\r\n😀",limits()?,WriterLimits::default())?;
            let requests=[Request{caption_id:&ids[0].0,text_id:&ids[0].1,replacement:"새 & <x>\r\n😀"}];let batch=source.lower_caption_text_batch_candidate(&bytes,&requests,limits()?,WriterLimits::default())?;
            assert_eq!(parts(&single.with_verified_bytes(<[u8]>::to_vec)?)?,parts(&batch.with_verified_bytes(<[u8]>::to_vec)?)?);
        }
        let bytes=package(&fixture::paragraph(&object(0,"<hp:t>old&#38;A</hp:t>")))?;let source=structure(&bytes,"batch-noops")?;let ids=selections(&source)?;
        let requests=[Request{caption_id:&ids[0].0,text_id:&ids[0].1,replacement:"old&A"},Request{caption_id:&ids[1].0,text_id:&ids[1].1,replacement:"oldB"}];
        assert!(matches!(source.lower_caption_text_batch_candidate(&bytes,&requests,limits()?,WriterLimits::default()),Err(E::NoChange)));Ok(())
    }
    #[test]
    fn caption_text_batch_output_protection_inventory_matches_original_guard_for_128_flag_combinations() -> TestResult {
        for truth in ["1","unknown"] {for mask in 0..64 {
            let value=|bit|if mask&(1<<bit)!=0{truth}else{if truth=="1"{"0"}else{"false"}};
            let table_value=|bit|if mask&(1<<bit)!=0{"1"}else{"0"};
            let object=object(0,&format!("<hp:t lock='{}'>oldA</hp:t>",value(5))).replacen("lock='0'",&format!("lock='{}'",value(0)),1).replacen("<hp:caption ",&format!("<hp:caption lock='{}' ",value(4)),1);
            let table=fixture::table(&object).replace("<hp:p id='1'>","<hp:p id='2'>")
                .replace("lock=\"0\"",&format!("lock=\"{}\"",table_value(1)))
                .replace("hasMargin=\"0\" protect=\"0\"",&format!("hasMargin=\"0\" protect=\"{}\"",table_value(2)))
                .replace("heightRelTo=\"ABSOLUTE\" protect=\"0\"",&format!("heightRelTo=\"ABSOLUTE\" protect=\"{}\"",table_value(3)));
            let body=fixture::paragraph(&table);
            let bytes=package(&body)?;let source=structure(&bytes,"batch-guard-oracle")?;let ids=selections(&source)?;
            let single=source.lower_caption_text_candidate(&bytes,&ids[0].0,&ids[0].1,"new",limits()?,WriterLimits::default());
            let requests=[Request{caption_id:&ids[0].0,text_id:&ids[0].1,replacement:"new"}];let batch=source.lower_caption_text_batch_candidate(&bytes,&requests,limits()?,WriterLimits::default());
            assert_eq!(single.is_ok(),mask==0);assert_eq!(batch.is_ok(),single.is_ok());
            if mask!=0 {assert!(matches!(single,Err(E::Protection)));assert!(matches!(batch,Err(E::Protection)));}
        }}
        let rejected=fixture::paragraph(&object(0,"<hp:t>oldA</hp:t>")).replacen("<hp:run>","<hp:run lock='0'>",1);
        assert!(structure(&package(&rejected)?,"batch-original-run-admission").is_err());
        let rejected=fixture::paragraph(&fixture::table(&object(0,"<hp:t>oldA</hp:t>")).replace("protect=\"0\"","protect=\"unknown\""));
        assert!(structure(&package(&rejected)?,"batch-original-table-boolean-admission").is_err());Ok(())
    }
    #[test]
    fn caption_text_batch_output_one_invalid_protected_duplicate_or_limited_request_rejects_whole_batch() -> TestResult {
        let bytes=package(&fixture::paragraph(&format!("{}{}",object(0,"<hp:t>oldA</hp:t>"),object(1,"<hp:t>oldA</hp:t>").replace("lock='0'","lock='1'"))))?;let source=structure(&bytes,"batch-atomic-reject")?;let ids=selections(&source)?;
        let good=Request{caption_id:&ids[0].0,text_id:&ids[0].1,replacement:"new"};let blocked=Request{caption_id:&ids[2].0,text_id:&ids[2].1,replacement:"new"};
        assert!(matches!(source.lower_caption_text_batch_candidate(&bytes,&[good,blocked],limits()?,WriterLimits::default()),Err(E::Protection)));
        let foreign=LogicalId::parse("foreign-batch-text")?;
        for (cap,text) in [(&ids[0].0,&foreign),(&ids[2].0,&ids[0].1)] {
            let requests=[Request{caption_id:&ids[0].0,text_id:&ids[0].1,replacement:"new"},Request{caption_id:cap,text_id:text,replacement:"new"}];
            assert!(matches!(source.lower_caption_text_batch_candidate(&bytes,&requests,limits()?,WriterLimits::default()),Err(E::Selection)));}
        let duplicates=[Request{caption_id:&ids[0].0,text_id:&ids[0].1,replacement:"new"},Request{caption_id:&ids[0].0,text_id:&ids[0].1,replacement:"other"}];
        assert!(matches!(source.lower_caption_text_batch_candidate(&bytes,&duplicates,limits()?,WriterLimits::default()),Err(E::Selection)));
        assert!(matches!(source.lower_caption_text_batch_candidate(&bytes,&[],limits()?,WriterLimits::default()),Err(E::Value)));
        let invalid=[Request{caption_id:&ids[0].0,text_id:&ids[0].1,replacement:"bad\0"}];assert!(matches!(source.lower_caption_text_batch_candidate(&bytes,&invalid,limits()?,WriterLimits::default()),Err(E::Value)));
        let requests=[Request{caption_id:&ids[0].0,text_id:&ids[0].1,replacement:"new"}];let tight=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig{text_bytes:1,..Default::default()})?;
        assert!(matches!(source.lower_caption_text_batch_candidate(&bytes,&requests,tight,WriterLimits::default()),Err(E::Limit)));
        assert!(matches!(source.lower_caption_text_batch_candidate(&bytes,&requests,limits()?,WriterLimits::new(hwpx_package::WriterLimitConfig{max_output_bytes:1})?),Err(E::Writer)));
        let mut drift=bytes.clone();drift[0]^=1;assert!(matches!(source.lower_caption_text_batch_candidate(&drift,&requests,limits()?,WriterLimits::default()),Err(E::Source)));Ok(())
    }
    #[test]
    fn caption_text_batch_output_multiple_sections_and_original_form_proof_use_one_output_candidate() -> TestResult {
        let bytes=rewrite(&fixture::two_sections()?,|name,data|{
            if name=="Contents/header.xml"{return Ok(HEADER.as_bytes().to_vec());}
            if name.starts_with("Contents/section"){let i=usize::from(name.ends_with("section1.xml"));let text=String::from_utf8(data)?.replace("<hp:ctrl><hp:bookmark name='same-across-sections'/></hp:ctrl>",&object(i,"<hp:t>oldA</hp:t>"));
                return Ok(if i==1{text.replacen("<hp:p id='1'>","<hp:p id='2'>",1)}else{text}.into_bytes());}Ok(data)
        })?;
        let forms=hwpx_package::document_import::forms::ImportedDocumentForms::import(ImportedSourcePackage::import(&bytes,DocumentId::parse("batch-multiple-parts")?,Sha256::digest(&bytes).into(),SourceImportLimits::default())?)?;
        let source=forms.body_structure();let ids=selections(source)?;assert_eq!(ids.len(),4);
        let requests=[Request{caption_id:&ids[0].0,text_id:&ids[0].1,replacement:"first"},Request{caption_id:&ids[2].0,text_id:&ids[2].1,replacement:"second"}];
        let proof=forms.reconstruct_source_for_verification(&bytes)?;let output=proof.lower_caption_text_batch_candidate(&forms,&bytes,&requests,limits()?,WriterLimits::default())?;
        assert_eq!((output.receipt().changed_parts,output.receipt().observed_protection_parts),(2,2));
        let before=parts(&bytes)?;let after=parts(&output.with_verified_bytes(<[u8]>::to_vec)?)?;
        for (name,old) in &before {if !name.starts_with("Contents/section"){assert_eq!(&after[name],old);}}
        let other=base::forms(&bytes,"batch-foreign-proof")?;
        assert!(matches!(proof.lower_caption_text_batch_candidate(&other,&bytes,&requests,limits()?,WriterLimits::default()),Err(E::Source)));Ok(())
    }
    #[test]
    fn caption_text_batch_output_128_leaf_edits_reuse_one_part_guard_and_preserve_source_order_independence() -> TestResult {
        let body=(0..64).map(|i|object(i,"<hp:t>oldA</hp:t>")).collect::<String>();let bytes=package(&fixture::paragraph(&body))?;let source=structure(&bytes,"batch-work-bound")?;let ids=selections(&source)?;
        assert_eq!(ids.len(),128);let values=(0..128).map(|i|format!("private replacement {i}")).collect::<Vec<_>>();
        let requests=ids.iter().zip(&values).map(|((cap,text),value)|Request{caption_id:cap,text_id:text,replacement:value}).collect::<Vec<_>>();
        let result=source.lower_caption_text_batch_candidate(&bytes,&requests,limits()?,WriterLimits::default())?;
        let xml=source.source().parts().iter().find(|p|p.path().as_str()=="Contents/section0.xml").and_then(|p|p.xml()).ok_or("xml")?;
        assert_eq!(result.receipt().changed_leaves,128);assert_eq!(result.receipt().observed_protection_parts,1);assert_eq!(result.receipt().observed_protection_element_visits,2*xml.elements().len());
        let reversed=ids.iter().zip(&values).rev().map(|((cap,text),value)|Request{caption_id:cap,text_id:text,replacement:value}).collect::<Vec<_>>();
        let other=source.lower_caption_text_batch_candidate(&bytes,&reversed,limits()?,WriterLimits::default())?;
        assert_eq!(parts(&result.with_verified_bytes(<[u8]>::to_vec)?)?,parts(&other.with_verified_bytes(<[u8]>::to_vec)?)?);
        assert!(!serde_json::to_string(result.receipt())?.contains("private replacement"));Ok(())
    }

    mod caption_edit_batch_output {
        use super::*;
        use domain_ir::NativeCaptionSide;
        use hwpx_package::document_import::structure::{caption_edit_batch::CaptionLayoutReplacement as Layout,
            caption_layout::{CaptionLayout,CaptionLayoutOutputError as LE}};
        fn layout()->CaptionLayout {CaptionLayout {side:NativeCaptionSide::Left,full_size:true,width_hwpunit:80,gap_hwpunit:12,last_width_hwpunit:40}}
        fn unchanged()->CaptionLayout {CaptionLayout {side:NativeCaptionSide::Bottom,full_size:false,width_hwpunit:1000,gap_hwpunit:20,last_width_hwpunit:900}}
        #[test]
        fn caption_edit_batch_combines_text_layout_and_noops_in_one_exact_output() -> TestResult {
            let body=fixture::paragraph(&format!("{}{}",object(0,"<hp:t>oldA</hp:t>"),object(1,"<hp:t/>")));
            let bytes=package(&body)?;let original=bytes.clone();let source=structure(&bytes,"edit-batch")?;let ids=selections(&source)?;
            let texts=[Request {caption_id:&ids[0].0,text_id:&ids[0].1,replacement:"new & <x>\r\n"},
                Request {caption_id:&ids[1].0,text_id:&ids[1].1,replacement:"oldB"},Request {caption_id:&ids[2].0,text_id:&ids[2].1,replacement:"empty changed"}];
            let layouts=[Layout {caption_id:&ids[0].0,layout:layout()},Layout {caption_id:&ids[2].0,layout:CaptionLayout {side:NativeCaptionSide::Top,..unchanged()}}];
            let result=source.lower_caption_edit_batch_candidate(&bytes,&texts,&layouts,limits()?,WriterLimits::default())?;
            let receipt=result.receipt();assert_eq!((receipt.requested_text_leaves,receipt.requested_layouts,receipt.text_changes.len(),receipt.layout_changes.len(),receipt.changed_parts),(3,2,2,2,1));
            assert_eq!(receipt.layout_changes.iter().map(|c|c.changed_attributes).sum::<usize>(),6);
            let before=parts(&bytes)?;let output=result.with_verified_bytes(<[u8]>::to_vec)?;let after=parts(&output)?;
            for (name,old) in &before {
                if name=="Contents/section0.xml" {
                    let expected=String::from_utf8(old.clone())?.replacen("side='BOTTOM'","side='LEFT'",1)
                        .replacen("fullSz='0'","fullSz='1'",1).replacen("width='1000'","width='80'",1)
                        .replacen("gap='20'","gap='12'",1).replacen("lastWidth='900'","lastWidth='40'",1)
                        .replacen("side='BOTTOM'","side='TOP'",1).replacen("oldA","new &amp; &lt;x&gt;&#13;\n",1)
                        .replacen("<hp:t/>","<hp:t>empty changed</hp:t>",1);
                    assert_eq!(after[name],expected.as_bytes());
                }else{assert_eq!(&after[name],old);}
            }
            assert_eq!(before.keys().collect::<Vec<_>>(),after.keys().collect::<Vec<_>>());
            let rebuilt=structure(&output,"edit-batch")?;let numbers=ImportedCaptionNumbering::import(&rebuilt,limits()?)?;
            assert!(numbers.controls().iter().all(|c|c.stored_number==19));
            assert!(receipt.outside_selected_edits_exact&&!receipt.complete_auxiliary_state_and_protection_verified&&!receipt.execution_publication_authority);
            assert!(!format!("{result:?}{}",serde_json::to_string(receipt)?).contains("empty changed"));
            assert_eq!(bytes,original);Ok(())
        }
        #[test]
        fn caption_edit_batch_text_or_layout_only_matches_original_single_lowerers_and_keeps_lexical_noops() -> TestResult {
            let body=fixture::paragraph(&object(0,"<hp:t>old&#38;A</hp:t>")).replace("fullSz='0'","fullSz='false'").replace("gap='20'","gap='020'");
            let bytes=package(&body)?;let source=structure(&bytes,"edit-batch-oracles")?;let ids=selections(&source)?;
            let layouts=[Layout {caption_id:&ids[0].0,layout:layout()}];
            let combined=source.lower_caption_edit_batch_candidate(&bytes,&[],&layouts,limits()?,WriterLimits::default())?;
            let single=source.lower_caption_layout_candidate(&bytes,&ids[0].0,layout(),limits()?,WriterLimits::default())?;
            assert_eq!(parts(&combined.with_verified_bytes(<[u8]>::to_vec)?)?,parts(&single.with_verified_bytes(<[u8]>::to_vec)?)?);
            let texts=[Request {caption_id:&ids[0].0,text_id:&ids[0].1,replacement:"new text"}];
            let combined=source.lower_caption_edit_batch_candidate(&bytes,&texts,&[],limits()?,WriterLimits::default())?;
            let single=source.lower_caption_text_candidate(&bytes,&ids[0].0,&ids[0].1,"new text",limits()?,WriterLimits::default())?;
            assert_eq!(parts(&combined.with_verified_bytes(<[u8]>::to_vec)?)?,parts(&single.with_verified_bytes(<[u8]>::to_vec)?)?);
            let no_layout=[Layout {caption_id:&ids[0].0,layout:unchanged()}];
            let with_noop=source.lower_caption_edit_batch_candidate(&bytes,&texts,&no_layout,limits()?,WriterLimits::default())?;
            assert_eq!(parts(&with_noop.with_verified_bytes(<[u8]>::to_vec)?)?,parts(&combined.with_verified_bytes(<[u8]>::to_vec)?)?);
            assert!(with_noop.receipt().layout_changes.is_empty());
            let no_text=[Request {caption_id:&ids[0].0,text_id:&ids[0].1,replacement:"old&A"}];
            assert!(matches!(source.lower_caption_edit_batch_candidate(&bytes,&no_text,&no_layout,limits()?,WriterLimits::default()),Err(E::NoChange)));Ok(())
        }
        #[test]
        fn caption_edit_batch_rejects_whole_invalid_duplicate_foreign_protected_or_limited_transaction() -> TestResult {
            let body=fixture::paragraph(&format!("{}{}",object(0,"<hp:t>oldA</hp:t>"),object(1,"<hp:t>oldA</hp:t>").replace("lock='0'","lock='1'")));
            let bytes=package(&body)?;let source=structure(&bytes,"edit-batch-rejections")?;let ids=selections(&source)?;
            let texts=[Request {caption_id:&ids[0].0,text_id:&ids[0].1,replacement:"changed"}];
            let foreign=LogicalId::parse("foreign-edit-caption")?;
            for (selected,error) in [(&foreign,E::Selection),(&ids[2].0,E::Protection)] {
                let layouts=[Layout {caption_id:selected,layout:layout()}];
                assert!(matches!(source.lower_caption_edit_batch_candidate(&bytes,&texts,&layouts,limits()?,WriterLimits::default()),Err(e) if e==error));
            }
            let good=Layout {caption_id:&ids[0].0,layout:layout()};
            assert!(matches!(source.lower_caption_edit_batch_candidate(&bytes,&texts,&[good,good],limits()?,WriterLimits::default()),Err(E::Selection)));
            assert!(matches!(source.lower_caption_edit_batch_candidate(&bytes,&texts,&[Layout {layout:CaptionLayout {width_hwpunit:-2,..layout()},..good}],limits()?,WriterLimits::default()),Err(E::Value)));
            let bad=[Request {caption_id:&ids[0].0,text_id:&ids[0].1,replacement:"bad\0"}];
            assert!(matches!(source.lower_caption_edit_batch_candidate(&bytes,&bad,&[good],limits()?,WriterLimits::default()),Err(E::Value)));
            let tight=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {extent_hwpunit:10,..Default::default()})?;
            assert!(matches!(source.lower_caption_edit_batch_candidate(&bytes,&texts,&[good],tight,WriterLimits::default()),Err(E::Limit)));
            assert!(matches!(source.lower_caption_edit_batch_candidate(&bytes,&texts,&[good],limits()?,WriterLimits::new(hwpx_package::WriterLimitConfig {max_output_bytes:1})?),Err(E::Writer)));
            assert!(matches!(source.lower_caption_edit_batch_candidate(&bytes,&[],&[],limits()?,WriterLimits::default()),Err(E::Value)));
            let mut changed=bytes.clone();changed[0]^=1;
            assert!(matches!(source.lower_caption_edit_batch_candidate(&changed,&texts,&[good],limits()?,WriterLimits::default()),Err(E::Source)));Ok(())
        }
        #[test]
        fn caption_edit_batch_layout_guard_matches_original_for64_ancestor_flags_and_protected_descendants() -> TestResult {
            for truth in ["1","unknown"] {for mask in 0..32 {
                let value=|bit|if mask&(1<<bit)!=0{truth}else{if truth=="1"{"0"}else{"false"}};
                let table_value=|bit|if mask&(1<<bit)!=0{"1"}else{"0"};
                let object=object(0,"<hp:t>oldA</hp:t>").replacen("lock='0'",&format!("lock='{}'",value(0)),1)
                    .replacen("<hp:caption ",&format!("<hp:caption lock='{}' ",value(4)),1);
                let table=fixture::table(&object).replace("<hp:p id='1'>","<hp:p id='2'>")
                    .replace("lock=\"0\"",&format!("lock=\"{}\"",table_value(1)))
                    .replace("hasMargin=\"0\" protect=\"0\"",&format!("hasMargin=\"0\" protect=\"{}\"",table_value(2)))
                    .replace("heightRelTo=\"ABSOLUTE\" protect=\"0\"",&format!("heightRelTo=\"ABSOLUTE\" protect=\"{}\"",table_value(3)));
                let bytes=package(&fixture::paragraph(&table))?;let source=structure(&bytes,"edit-batch-layout-guard")?;let ids=selections(&source)?;
                let single=source.lower_caption_layout_candidate(&bytes,&ids[0].0,layout(),limits()?,WriterLimits::default());
                let batch=source.lower_caption_edit_batch_candidate(&bytes,&[],&[Layout {caption_id:&ids[0].0,layout:layout()}],limits()?,WriterLimits::default());
                assert_eq!(single.is_ok(),mask==0);assert_eq!(batch.is_ok(),single.is_ok());
                if mask!=0 {assert!(matches!(single,Err(LE::Protection)));assert!(matches!(batch,Err(E::Protection)));}
            }}
            for flag in ["lock=\"0\"","hasMargin=\"0\" protect=\"0\"","heightRelTo=\"ABSOLUTE\" protect=\"0\""] {
                let table=fixture::table("<hp:t>private protected descendant</hp:t>").replace("<hp:p id='1'>","<hp:p id='333'>");
                let protected=match flag {"lock=\"0\""=>table.replace(flag,"lock=\"1\""),_=>table.replace(flag,&flag.replacen("protect=\"0\"","protect=\"1\"",1))};
                let object=object(0,&format!("<hp:t>oldA</hp:t>{protected}"));
                let bytes=package(&fixture::paragraph(&object))?;let source=structure(&bytes,"edit-batch-protected-descendant")?;let ids=selections(&source)?;
                assert!(matches!(source.lower_caption_layout_candidate(&bytes,&ids[0].0,layout(),limits()?,WriterLimits::default()),Err(LE::Protection)));
                assert!(matches!(source.lower_caption_edit_batch_candidate(&bytes,&[],&[Layout {caption_id:&ids[0].0,layout:layout()}],limits()?,WriterLimits::default()),Err(E::Protection)));
            }Ok(())
        }
        #[test]
        fn caption_edit_batch_multiple_parts_reuses_exact_whole_form_proof_and_rejects_foreign_binding() -> TestResult {
            let bytes=rewrite(&fixture::two_sections()?,|name,data|{
                if name=="Contents/header.xml"{return Ok(HEADER.as_bytes().to_vec());}
                if name.starts_with("Contents/section"){let i=usize::from(name.ends_with("section1.xml"));let text=String::from_utf8(data)?.replace("<hp:ctrl><hp:bookmark name='same-across-sections'/></hp:ctrl>",&object(i,"<hp:t>oldA</hp:t>"));
                    return Ok(if i==1{text.replacen("<hp:p id='1'>","<hp:p id='2'>",1)}else{text}.into_bytes());}Ok(data)
            })?;
            let forms=base::forms(&bytes,"edit-batch-proof")?;let ids=selections(forms.body_structure())?;
            let texts=[Request {caption_id:&ids[0].0,text_id:&ids[0].1,replacement:"first"}];
            let layouts=[Layout {caption_id:&ids[2].0,layout:layout()}];
            let proof=forms.reconstruct_source_for_verification(&bytes)?;
            let candidate=proof.lower_caption_edit_batch_candidate(&forms,&bytes,&texts,&layouts,limits()?,WriterLimits::default())?;
            assert_eq!((candidate.receipt().changed_parts,candidate.receipt().observed_protection_parts),(2,2));
            let pure=forms.body_structure().lower_caption_edit_batch_candidate(&bytes,&texts,&layouts,limits()?,WriterLimits::default())?;
            assert_eq!(parts(&candidate.with_verified_bytes(<[u8]>::to_vec)?)?,parts(&pure.with_verified_bytes(<[u8]>::to_vec)?)?);
            let other=base::forms(&bytes,"edit-batch-other-proof")?;
            assert!(matches!(proof.lower_caption_edit_batch_candidate(&other,&bytes,&texts,&layouts,limits()?,WriterLimits::default()),Err(E::Source)));
            let mut bad=bytes.clone();bad[0]^=1;
            assert!(matches!(proof.lower_caption_edit_batch_candidate(&forms,&bad,&texts,&layouts,limits()?,WriterLimits::default()),Err(E::Source)));Ok(())
        }
        #[test]
        fn caption_edit_batch192_requests_share_part_guards_and_are_request_order_independent() -> TestResult {
            let bytes=package(&fixture::paragraph(&(0..64).map(|i|object(i,"<hp:t>oldA</hp:t>")).collect::<String>()))?;
            let source=structure(&bytes,"edit-batch-work")?;let ids=selections(&source)?;
            let values=(0..128).map(|i|format!("private edited text {i}")).collect::<Vec<_>>();
            let texts=ids.iter().zip(&values).map(|((caption_id,text_id),replacement)|Request {caption_id,text_id,replacement}).collect::<Vec<_>>();
            let layouts=ids.iter().step_by(2).map(|(caption_id,_)|Layout {caption_id,layout:layout()}).collect::<Vec<_>>();
            let candidate=source.lower_caption_edit_batch_candidate(&bytes,&texts,&layouts,limits()?,WriterLimits::default())?;
            assert_eq!((candidate.receipt().text_changes.len(),candidate.receipt().layout_changes.len(),candidate.receipt().observed_protection_parts),(128,64,1));
            let xml=source.source().parts().iter().find(|p|p.path().as_str()=="Contents/section0.xml").and_then(|p|p.xml()).ok_or("xml")?;
            assert_eq!(candidate.receipt().observed_protection_element_visits,4*xml.elements().len());
            let reverse_text=ids.iter().zip(&values).rev().map(|((caption_id,text_id),replacement)|Request {caption_id,text_id,replacement}).collect::<Vec<_>>();
            let reverse_layout=layouts.iter().rev().copied().collect::<Vec<_>>();
            let reversed=source.lower_caption_edit_batch_candidate(&bytes,&reverse_text,&reverse_layout,limits()?,WriterLimits::default())?;
            assert_eq!(parts(&candidate.with_verified_bytes(<[u8]>::to_vec)?)?,parts(&reversed.with_verified_bytes(<[u8]>::to_vec)?)?);
            assert!(!serde_json::to_string(candidate.receipt())?.contains("private edited"));Ok(())
        }
    }

    mod source_state_assembly {
        use super::*;
        use hwpx_package::document_import::reference_targets::{caption_source_state::{
            ImportedCaptionSourceState,CaptionNumberingSourceEventKind as Event},
            numbering::{CaptionNumberingImportError as StateError,context::NativeOwnerNumberingType},
            caption_frames::{CaptionFrameSegmentKind,CaptionStyleReferenceStatus}};
        const BEGIN:&str="<hh:beginNum page='0' footnote='2' endnote='3' pic='0' tbl='5' equation='6'/>";
        fn with_begin(body:&str)->Result<Vec<u8>,Box<dyn Error>> {
            rewrite(&package(&fixture::paragraph(body))?,|name,data|Ok(if name=="Contents/header.xml" {
                String::from_utf8(data)?.replace("<hh:refList>",&format!("{BEGIN}<hh:refList>")).into_bytes()
            }else{data}))
        }
        #[test]
        fn caption_source_state_exact_original_models_join_owners_captions_controls_and_zero_starts() -> TestResult {
            let body=format!("<hp:secPr><hp:startNum pageStartsOn='BOTH' page='0' pic='0' tbl='3' equation='4'/></hp:secPr><hp:ctrl><hp:newNum num='5' numType='PICTURE'/></hp:ctrl>{}<hp:rect id='8' numberingType='NONE'/>",object(0,"<hp:t>private source text</hp:t>"));
            let bytes=with_begin(&body)?;let source=structure(&bytes,"caption-source-state")?;
            let original=ImportedCaptionNumbering::import(&source,limits()?)?;let context=original.import_context(limits()?)?;
            let frames=original.import_frames(limits()?)?;let states=context.project_object_states(limits()?)?;
            let result=ImportedCaptionSourceState::import(&source,limits()?)?;
            assert_eq!(result.numbering().receipt(),original.receipt());assert_eq!(result.numbering().controls(),original.controls());
            assert_eq!(result.context().receipt(),context.receipt());assert_eq!(result.frames().frames(),frames.frames());assert_eq!(result.object_states().objects(),states.objects());
            assert_eq!((result.receipt().owner_links,result.receipt().caption_links,result.receipt().source_events),(2,1,5));
            let link=result.owner_links()[0];let caption=link.caption.ok_or("caption link")?;
            let owner=&result.context().owners()[link.owner_index];let body=&result.object_states().objects()[link.object_state_index];
            assert_eq!(owner.logical_object_id,body.logical_object_id);
            assert_eq!(result.numbering().caption_import().envelopes()[caption.envelope_index].logical_object_id(),&owner.logical_object_id);
            assert_eq!(result.frames().frames()[caption.frame_index].logical_object_id,owner.logical_object_id);
            assert!(result.owner_links()[1].caption.is_none());
            assert!(matches!(result.source_events()[0].event,Event::SectionStart {section_start_index:0}));
            assert!(matches!(result.source_events()[1].event,Event::Restart {control_index:0,owner_index:None}));
            assert!(matches!(result.source_events()[2].event,Event::Owner {owner_index:0}));
            assert!(matches!(result.source_events()[3].event,Event::AutoNumber {control_index:1,owner_index:Some(0)}));
            assert_eq!(result.context().document_start().ok_or("explicit begin")?.picture,0);
            assert_eq!(result.numbering().section_starts()[0].picture,0);assert_eq!(result.numbering().controls()[1].stored_number,19);
            assert!(!result.receipt().sequence_interpretation_and_recalculation_qualified&&!result.receipt().complete_auxiliary_state_and_protection_qualified&&!result.receipt().execution_publication_authority);
            assert!(!format!("{result:?}{}",serde_json::to_string(result.receipt())?).contains("private source text"));
            assert_eq!(result.verify_source(&bytes)?,*result.receipt());Ok(())
        }
        #[test]
        fn caption_source_state_all_ten_owner_families_keep_uncaptioned_missing_and_explicit_none_distinct() -> TestResult {
            let mut body=String::new();
            for name in ["pic","rect","ellipse","line","arc","polygon","curve","connectLine","equation"] {
                let attr=match name {"rect"=>" numberingType='NONE'","line"=>"","equation"=>" numberingType='EQUATION'",_=>" numberingType='PICTURE'"};
                body.push_str(&format!("<hp:{name} id='7'{attr}/>"));
            }
            body.push_str(&fixture::table("<hp:t>private table body</hp:t>"));
            let bytes=with_begin(&body)?;let source=structure(&bytes,"caption-state-ten")?;let result=ImportedCaptionSourceState::import(&source,limits()?)?;
            assert_eq!((result.owner_links().len(),result.receipt().caption_links,result.source_events().len()),(10,0,10));
            assert!(result.owner_links().iter().all(|link|link.caption.is_none()));
            assert_eq!(result.context().owners()[1].numbering_type,Some(NativeOwnerNumberingType::None));
            assert_eq!(result.context().owners()[3].numbering_type,None);
            assert_eq!(result.context().owners().iter().map(|o|&o.logical_object_id).collect::<std::collections::BTreeSet<_>>().len(),10);
            for link in result.owner_links() {
                assert_eq!(result.context().owners()[link.owner_index].logical_object_id,result.object_states().objects()[link.object_state_index].logical_object_id);
            }Ok(())
        }
        #[test]
        fn caption_source_state_spine_not_zip_order_and_duplicate_native_ids_bind_exact_original_indices() -> TestResult {
            let bytes=rewrite(&fixture::two_sections()?,|name,data|{
                if name=="Contents/header.xml"{return Ok(HEADER.as_bytes().to_vec());}
                if name.starts_with("Contents/section"){let i=usize::from(name.ends_with("section1.xml"));
                    let text=String::from_utf8(data)?.replace("<hp:ctrl><hp:bookmark name='same-across-sections'/></hp:ctrl>",&object(0,"<hp:t>private per-section text</hp:t>"));
                    return Ok(if i==1{text.replacen("<hp:p id='1'>","<hp:p id='2'>",1)}else{text}.into_bytes());}Ok(data)
            })?;
            let mut expanded=parts(&bytes)?;let mut zip=zip::ZipWriter::new(Cursor::new(Vec::new()));
            let mimetype=expanded.remove("mimetype").ok_or("mimetype")?;
            for (name,data) in std::iter::once(("mimetype".to_owned(),mimetype)).chain(expanded.into_iter().rev()) {
                zip.start_file(name,zip::write::SimpleFileOptions::default().compression_method(zip::CompressionMethod::Stored))?;zip.write_all(&data)?;
            }
            let bytes=zip.finish()?.into_inner();let source=structure(&bytes,"caption-state-spine")?;
            let result=ImportedCaptionSourceState::import(&source,limits()?)?;
            assert_eq!((result.owner_links().len(),result.receipt().caption_links,result.source_events().len()),(2,2,4));
            assert!(result.source_events().windows(2).all(|w|w[0].source_position<w[1].source_position));
            assert_eq!(result.source_events().iter().map(|e|e.source_position.spine_ordinal).collect::<Vec<_>>(),[0,0,1,1]);
            assert_ne!(result.context().owners()[0].logical_object_id,result.context().owners()[1].logical_object_id);
            let consumed=ImportedCaptionNumbering::import(&source,limits()?)?.assemble_source_state(limits()?)?;
            assert_eq!(result.receipt(),consumed.receipt());
            for link in result.owner_links(){let caption=link.caption.ok_or("caption link")?;
                assert_eq!(result.frames().frames()[caption.frame_index].logical_object_id,result.context().owners()[link.owner_index].logical_object_id);
            }Ok(())
        }
        #[test]
        fn caption_source_state_complex_frames_and_mid_caption_restart_are_preserved_without_label_or_number_inference() -> TestResult {
            let inner="<hp:t>private<!--private comment--> opaque</hp:t><hp:ctrl><hp:newNum num='0' numType='PICTURE'/></hp:ctrl>";
            let bytes=with_begin(&object(0,inner))?;let source=structure(&bytes,"caption-state-complex")?;
            let result=ImportedCaptionSourceState::import(&source,limits()?)?;let frame=&result.frames().frames()[0];
            assert_eq!(frame.segments[0].kind,CaptionFrameSegmentKind::Opaque);
            assert_eq!(result.frames().plain_text(&frame.segments[0].logical_source_id),None);
            assert_eq!(frame.segments[1].kind,CaptionFrameSegmentKind::Restart);assert!(!frame.single_auto_number_linear_layout_observed);
            assert_eq!(result.numbering().controls()[0].stored_number,0);assert_eq!(result.numbering().controls()[1].stored_number,19);
            assert_eq!(frame.paragraphs[0].paragraph_style.status,CaptionStyleReferenceStatus::MissingReference);
            assert!(matches!(result.source_events()[1].event,Event::Restart {owner_index:Some(0),..}));
            assert!(matches!(result.source_events()[2].event,Event::AutoNumber {owner_index:Some(0),..}));
            let safe=format!("{result:?}{}{}",serde_json::to_string(result.receipt())?,serde_json::to_string(result.source_events())?);
            assert!(!safe.contains("private"));Ok(())
        }
        #[test]
        fn caption_source_state_fresh_source_drift_inside_masked_caption_still_invalidates_joined_snapshot() -> TestResult {
            let bytes=with_begin(&object(0,"<hp:t>oldA</hp:t>"))?;let source=structure(&bytes,"caption-state-fresh")?;
            let result=ImportedCaptionSourceState::import(&source,limits()?)?;
            let changed=with_begin(&object(0,"<hp:t>different text</hp:t>"))?;let other=structure(&changed,"caption-state-fresh")?;
            let after=ImportedCaptionSourceState::import(&other,limits()?)?;
            assert_eq!(result.object_states().objects()[0].object_state_sha256,after.object_states().objects()[0].object_state_sha256);
            assert_ne!(result.receipt().joined_state_sha256,after.receipt().joined_state_sha256);
            assert!(matches!(result.verify_source(&changed),Err(StateError::Binding)));
            assert_eq!(result.verify_source(&bytes)?,*result.receipt());
            let foreign=structure(&bytes,"caption-state-different-document")?;
            assert_ne!(result.receipt().joined_state_sha256,ImportedCaptionSourceState::import(&foreign,limits()?)?.receipt().joined_state_sha256);
            Ok(())
        }
        #[test]
        fn caption_source_state_finite_bounds_and128_owner_links_use_complete_indexed_inventories() -> TestResult {
            let body=(0..128).map(|i|if i%2==0{object(i,"<hp:t>private indexed source</hp:t>")}else{format!("<hp:rect id='{}' numberingType='NONE'/>",7+i)}).collect::<String>();
            let bytes=with_begin(&body)?;let source=structure(&bytes,"caption-state-index")?;
            let result=ImportedCaptionSourceState::import(&source,limits()?)?;
            assert_eq!((result.owner_links().len(),result.receipt().caption_links,result.source_events().len()),(128,64,192));
            let mut seen=std::collections::BTreeSet::new();
            for link in result.owner_links(){assert!(seen.insert(link.owner_index));assert_eq!(link.owner_index,link.object_state_index);}
            assert_eq!(result.source_events().iter().filter(|e|matches!(e.event,Event::AutoNumber {owner_index:Some(_),..})).count(),64);
            for config in [ReferenceAuxiliaryLimitConfig {items_per_kind:1,..Default::default()},ReferenceAuxiliaryLimitConfig {input_bytes:1,output_bytes:1,..Default::default()}] {
                assert!(matches!(ImportedCaptionSourceState::import(&source,ReferenceAuxiliaryLimits::new(config)?),Err(StateError::Limit)));
            }Ok(())
        }

        mod output_compiler {include!("support/caption_source_state_output.rs");}
        mod style_compiler {include!("support/caption_style_batch_output.rs");}
        mod number_sequence_compiler {include!("support/caption_number_sequence_output.rs");}
        mod number_topology_compiler {include!("support/caption_number_topology_output.rs");}
        mod caption_program_compiler {include!("support/caption_program_output.rs");}
        mod caption_structure_compiler {include!("support/caption_structure_output.rs");}

    }


}
