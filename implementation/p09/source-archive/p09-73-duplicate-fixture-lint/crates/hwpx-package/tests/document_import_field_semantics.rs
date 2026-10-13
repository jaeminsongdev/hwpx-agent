use domain_ir::{DocumentGraph, DocumentGraphLimits, Flow, HyperlinkTarget, Node, Properties};
use hwpx_package::document_import::fields::{
    ImportedDocumentFields,
    semantics::{FieldSemanticImportError, ImportedDocumentFieldSemantics, ImportedFieldMeaning},
};
use sha2::{Digest as _, Sha256};
use std::{error::Error, path::PathBuf};
#[path = "support/document_import_field_fixture.rs"]
mod fixture;
type TestResult = Result<(), Box<dyn Error>>;

fn link(uri: &str, command: &str) -> String {
    format!(
        r#"<hp:p id="1"><hp:run><hp:ctrl><hp:fieldBegin id="1" type="HYPERLINK"><hp:parameters cnt="6" name=""><hp:integerParam name="Prop">0</hp:integerParam><hp:stringParam name="Command">{command}</hp:stringParam><hp:stringParam name="Path">{uri}</hp:stringParam><hp:stringParam name="Category">HWPHYPERLINK_TYPE_URL</hp:stringParam><hp:stringParam name="TargetType">HWPHYPERLINK_TARGET_BOOKMARK</hp:stringParam><hp:stringParam name="DocOpenType">HWPHYPERLINK_JUMP_CURRENTTAB</hp:stringParam></hp:parameters></hp:fieldBegin></hp:ctrl><hp:t>cached label</hp:t><hp:ctrl><hp:fieldEnd beginIDRef="1"/></hp:ctrl></hp:run></hp:p>"#
    )
}
fn command(uri: &str) -> String {
    format!(
        "https\\://{};1;0;0;",
        uri.replacen("https://", "https\\://", 1)
    )
}
fn retain(properties: &Properties) -> Properties {
    let mut out = Properties::new();
    for (key, value) in properties
        .iter()
        .filter(|(key, _)| *key != "source_derived_meaning")
    {
        out.insert(key, value.clone());
    }
    out
}
fn restore(flow: &mut Flow) {
    for node in &mut flow.children {
        match node {
            Node::Field(field) => field.properties = retain(&field.properties),
            Node::Table(table) => {
                for cell in &mut table.cells {
                    restore(&mut cell.body);
                }
            }
            Node::Drawing(drawing) => restore(&mut drawing.children),
            _ => (),
        }
    }
}
fn unchanged(
    fields: &ImportedDocumentFields<'_>,
    meaning: &ImportedDocumentFieldSemantics<'_, '_>,
) -> TestResult {
    let mut draft = meaning.graph().clone().into_draft();
    draft.metadata = fields.graph().clone().into_draft().metadata;
    for reference in &mut draft.references {
        reference.properties = retain(&reference.properties);
    }
    for section in &mut draft.sections {
        restore(&mut section.body);
    }
    assert_eq!(
        DocumentGraph::from_draft(draft, DocumentGraphLimits::default())?,
        *fields.graph()
    );
    Ok(())
}
#[test]
fn source_https_tuple_is_typed_without_approval_or_label_inference() -> TestResult {
    let uri = "https://example.org/a?x=1&amp;y=2";
    let bytes = fixture::package(&link(uri, &command(uri)))?;
    let forms = fixture::forms(&bytes, "meaning-test")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meaning = ImportedDocumentFieldSemantics::import(&fields)?;
    assert_eq!(meaning.receipt().https_targets, 1);
    assert!(matches!(&meaning.observations()[0].meaning,
        ImportedFieldMeaning::HttpsTarget { target: HyperlinkTarget::Https { uri } }
            if uri == "https://example.org/a?x=1&y=2"));
    assert!(
        meaning.graph().clone().into_draft().references[0]
            .target_node_id
            .is_none()
    );
    assert_eq!(meaning.verify_source(&bytes)?, *meaning.receipt());
    unchanged(&fields, &meaning)
}
#[test]
fn malformed_supported_parameter_tuples_reject_not_opaque_success() -> TestResult {
    let uri = "https://example.org/a";
    let good = link(uri, &command(uri));
    for body in [
        good.replace(&command(uri), "unmatched-command"),
        good.replace("HWPHYPERLINK_TYPE_URL", "other-category"),
        good.replace("JUMP_CURRENTTAB", "JUMP_NEWWINDOW"),
        good.replace(
            "<hp:integerParam name=\"Prop\">0",
            "<hp:integerParam name=\"Prop\">1",
        ),
        good.replace("https://", "http://"),
        good.replace("https://example.org/a", "javascript:alert(1)"),
    ] {
        let bytes = fixture::package(&body)?;
        let forms = fixture::forms(&bytes, "meaning-test")?;
        let fields = ImportedDocumentFields::import(&forms)?;
        assert!(matches!(
            ImportedDocumentFieldSemantics::import(&fields),
            Err(FieldSemanticImportError::Hyperlink { .. })
        ));
    }
    Ok(())
}
#[test]
fn foreign_parameter_namespace_cannot_supply_native_https_meaning() -> TestResult {
    let uri = "https://example.org/a";
    let body = link(uri, &command(uri))
        .replace("<hp:stringParam", "<u:stringParam")
        .replace("</hp:stringParam", "</u:stringParam");
    let bytes = fixture::package(&body)?;
    // The original source-preserving parser is allowed to reject this before
    // meaning import, but no admitted source path may claim HTTPS success.
    if let Ok(forms) = fixture::forms(&bytes, "meaning-test")
        && let Ok(fields) = ImportedDocumentFields::import(&forms)
    {
        assert!(ImportedDocumentFieldSemantics::import(&fields).is_err());
    }
    Ok(())
}
#[test]
fn unsupported_date_is_explicit_and_source_fresh_verification_is_whole() -> TestResult {
    let body = "<hp:p id='1'><hp:run><hp:ctrl><hp:fieldBegin id='1' type='DATE'/></hp:ctrl><hp:t>not-a-date</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='1'/></hp:ctrl></hp:run></hp:p>";
    let bytes = fixture::package(body)?;
    let forms = fixture::forms(&bytes, "meaning-test")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meaning = ImportedDocumentFieldSemantics::import(&fields)?;
    assert_eq!(meaning.receipt().unsupported_meanings, 1);
    assert!(
        matches!(&meaning.observations()[0].meaning, ImportedFieldMeaning::Unsupported { native_kind } if native_kind == "DATE")
    );
    let changed = fixture::package(&body.replace("not-a-date", "different"))?;
    assert!(meaning.verify_source(&changed).is_err());
    unchanged(&fields, &meaning)
}
#[test]
fn historical_captured_https_has_actual_target_and_whole_unchanged_graph() -> TestResult {
    let bytes = fixture::captured()?;
    let forms = fixture::forms(&bytes, "meaning-test")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meaning = ImportedDocumentFieldSemantics::import(&fields)?;
    assert_eq!(
        (
            meaning.receipt().ranges,
            meaning.receipt().https_targets,
            meaning.receipt().unsupported_meanings
        ),
        (1, 1, 0)
    );
    assert!(matches!(
        meaning.observations()[0].meaning,
        ImportedFieldMeaning::HttpsTarget { .. }
    ));
    assert_eq!(meaning.verify_source(&bytes)?, *meaning.receipt());
    unchanged(&fields, &meaning)
}
#[test]
fn all_sixteen_locked_table_sources_import_actual_formula_ast_and_unverified_cache() -> TestResult {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
    let manifest = std::fs::read(root.join(
        "implementation/p06/evidence/target/p06-table-aggregate.current-2020.attempt02.v2.json",
    ))?;
    assert_eq!(
        hex::encode(Sha256::digest(&manifest)),
        "edc71d554e0975d511ffe6f0de1b140a30ca932d0bf2b9c7b70517c5e8674fc5"
    );
    let manifest: serde_json::Value = serde_json::from_slice(&manifest)?;
    let mut count = 0;
    for case in manifest["cases"].as_array().ok_or("cases")? {
        for kind in ["input", "output"] {
            let item = &case[kind];
            let path = root.join(item["path"].as_str().ok_or("path")?);
            let metadata = std::fs::symlink_metadata(&path)?;
            assert!(metadata.is_file() && !metadata.file_type().is_symlink());
            let bytes = std::fs::read(path)?;
            assert_eq!(bytes.len() as u64, item["bytes"].as_u64().ok_or("bytes")?);
            assert_eq!(
                hex::encode(Sha256::digest(&bytes)),
                item["sha256"].as_str().ok_or("sha")?
            );
            let forms = fixture::forms(&bytes, "meaning-test")?;
            let fields = ImportedDocumentFields::import(&forms)?;
            let meaning = ImportedDocumentFieldSemantics::import(&fields)?;
            assert_eq!(
                (
                    meaning.receipt().ranges,
                    meaning.receipt().table_formula_asts
                ),
                (1, 1)
            );
            let ImportedFieldMeaning::TableFormula {
                dimensions,
                formula,
            } = &meaning.observations()[0].meaning
            else {
                return Err("not formula".into());
            };
            assert_eq!((dimensions.rows, dimensions.columns), (2, 4));
            assert!(matches!(
                formula.cache(),
                domain_ir::FormulaCache::Unverified { .. }
            ));
            assert_eq!(meaning.verify_source(&bytes)?, *meaning.receipt());
            unchanged(&fields, &meaning)?;
            count += 1;
        }
    }
    assert_eq!(count, 16);
    Ok(())
}
#[test]
fn no_fields_preserves_original_graph_and_resources() -> TestResult {
    let bytes = fixture::package("<hp:p id='1'><hp:run><hp:t>plain</hp:t></hp:run></hp:p>")?;
    let forms = fixture::forms(&bytes, "meaning-test")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meaning = ImportedDocumentFieldSemantics::import(&fields)?;
    assert!(meaning.observations().is_empty());
    unchanged(&fields, &meaning)
}
#[test]
fn debug_and_receipts_do_not_expose_targets_parameters_or_cache_values() -> TestResult {
    let bytes = fixture::captured()?;
    let forms = fixture::forms(&bytes, "meaning-test")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meaning = ImportedDocumentFieldSemantics::import(&fields)?;
    let metadata = format!(
        "{:?}{:?}{}",
        meaning,
        meaning.observations(),
        serde_json::to_string(meaning.receipt())?
    );
    assert!(
        !metadata.contains("https://")
            && !metadata.contains("Command")
            && !metadata.contains("cached label")
    );
    Ok(())
}
