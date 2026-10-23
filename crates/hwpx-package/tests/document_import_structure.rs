use std::{
    error::Error,
    fmt::Write as _,
    io::{Cursor, Write},
    path::PathBuf,
};

use domain_ir::{
    DocumentGraph, DocumentGraphLimits, DocumentId, Flow, Inline, Node, OpaquePreservation,
    PropertyValue,
};
use hwpx_package::document_import::{
    ImportedSourcePackage, SourceImportError, SourceImportLimits,
    structure::{ImportedDocumentStructure, STRUCTURE_IMPORT_SCOPE, StructureImportError},
};
use sha2::{Digest as _, Sha256};
use zip::{CompressionMethod, ZipWriter, write::SimpleFileOptions};

type TestResult = Result<(), Box<dyn Error>>;
const HP: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const HS: &str = "http://www.hancom.co.kr/hwpml/2011/section";

fn paragraph(value: &str) -> String {
    format!(
        r#"<hp:p id="7" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>{value}</hp:t></hp:run></hp:p>"#
    )
}
fn section(body: &str) -> String {
    format!(r#"<hs:sec xmlns:hs="{HS}" xmlns:hp="{HP}" xmlns:u="urn:future">{body}</hs:sec>"#)
}
fn digest(bytes: &[u8]) -> [u8; 32] {
    Sha256::digest(bytes).into()
}

fn archive(sections: &[String]) -> Result<Vec<u8>, Box<dyn Error>> {
    let mut items = String::new();
    let mut spine = String::new();
    for index in 0..sections.len() {
        write!(
            items,
            r#"<o:item id="s{index}" href="Contents/section{index}.xml" media-type="application/xml"/>"#
        )?;
        write!(spine, r#"<o:itemref idref="s{index}"/>"#)?;
    }
    let opf = format!(
        r#"<o:package xmlns:o="http://www.idpf.org/2007/opf/"><o:manifest><o:item id="header" href="Contents/header.xml" media-type="application/xml"/>{items}<o:item id="private" href="BinData/private.dat" media-type="application/octet-stream"/></o:manifest><o:spine>{spine}</o:spine></o:package>"#
    );
    let container = br#"<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="Contents/content.hpf" media-type="application/hwpml-package+xml"/></rootfiles></container>"#;
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for (path, bytes) in [
        ("mimetype", b"application/hwp+zip".as_slice()),
        ("version.xml", b"<version/>".as_slice()),
        ("META-INF/container.xml", container.as_slice()),
        ("Contents/content.hpf", opf.as_bytes()),
        (
            "Contents/header.xml",
            b"<header private='TOPSECRET'/>".as_slice(),
        ),
        ("BinData/private.dat", b"PRIVATE_BINARY".as_slice()),
    ] {
        writer.start_file(
            path,
            SimpleFileOptions::default().compression_method(CompressionMethod::Stored),
        )?;
        writer.write_all(bytes)?;
    }
    for (index, section) in sections.iter().enumerate() {
        writer.start_file(
            format!("Contents/section{index}.xml"),
            SimpleFileOptions::default().compression_method(CompressionMethod::Stored),
        )?;
        writer.write_all(section.as_bytes())?;
    }
    Ok(writer.finish()?.into_inner())
}
fn import(bytes: &[u8]) -> Result<ImportedDocumentStructure, Box<dyn Error>> {
    Ok(ImportedDocumentStructure::import(
        ImportedSourcePackage::import(
            bytes,
            DocumentId::parse("structure-test")?,
            digest(bytes),
            SourceImportLimits::default(),
        )?,
    )?)
}
fn visible(flow: &Flow) -> String {
    let mut output = String::new();
    for node in &flow.children {
        match node {
            Node::Paragraph(p) => {
                for inline in &p.inlines {
                    match inline {
                        Inline::Text { text } => output.push_str(text),
                        Inline::Tab => output.push('\t'),
                        Inline::LineBreak => output.push('\n'),
                        _ => (),
                    }
                }
            }
            Node::Table(table) => {
                for cell in &table.cells {
                    output.push_str(&visible(&cell.body));
                }
            }
            _ => (),
        }
    }
    output
}
fn check_nodes(imported: &ImportedDocumentStructure, flow: &Flow) -> TestResult {
    for node in &flow.children {
        let common = node.common();
        assert_eq!(common.preserve, OpaquePreservation::PreserveExact);
        let anchor = common
            .source_anchor
            .as_ref()
            .ok_or("real source anchor missing")?;
        assert!(
            imported
                .source()
                .resolve_anchor(anchor)?
                .element()
                .is_some()
        );
        if let Node::Table(table) = node {
            for cell in &table.cells {
                check_nodes(imported, &cell.body)?;
            }
        }
    }
    Ok(())
}
fn cell(row: u32, column: u32, row_span: u32, column_span: u32, body: &str) -> String {
    format!(
        r#"<hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="1"><hp:cellAddr colAddr="{column}" rowAddr="{row}"/><hp:cellSpan colSpan="{column_span}" rowSpan="{row_span}"/><hp:cellSz width="1000" height="500"/><hp:cellMargin left="0" right="0" top="0" bottom="0"/><hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">{body}</hp:subList></hp:tc>"#
    )
}
fn table(body: &str, rows: u32, columns: u32) -> String {
    format!(
        r#"<hp:tbl id="9" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="0" rowCnt="{rows}" colCnt="{columns}" cellSpacing="0" borderFillIDRef="1" noAdjust="0"><hp:sz width="2000" widthRelTo="ABSOLUTE" height="1000" heightRelTo="ABSOLUTE" protect="0"/><hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="0" horzOffset="0"/><hp:outMargin left="0" right="0" top="0" bottom="0"/><hp:inMargin left="510" right="511" top="141" bottom="142"/>{body}</hp:tbl>"#
    )
}

#[test]
fn unicode_inline_and_run_order_styles_tabs_breaks_are_source_backed() -> TestResult {
    let body = r#"<hp:p id="7" paraPrIDRef="2" styleIDRef="3"><hp:run charPrIDRef="4"><hp:t charStyleIDRef="5">한글&amp;A&#x20;e&#x301;<hp:tab width="8000" leader="4" type="3"/><hp:lineBreak/>끝</hp:t></hp:run><hp:run charPrIDRef="6"><hp:t>B</hp:t></hp:run></hp:p>"#;
    let bytes = archive(&[section(body)])?;
    let imported = import(&bytes)?;
    assert_eq!(
        visible(&imported.graph().sections()[0].body),
        "한글&A e\u{301}\t\n끝B"
    );
    assert_eq!(imported.receipt().paragraphs, 1);
    let Node::Paragraph(p) = &imported.graph().sections()[0].body.children[0] else {
        return Err("paragraph".into());
    };
    let props: std::collections::BTreeMap<_, _> = p.paragraph_properties.iter().collect();
    let Some(PropertyValue::List(runs)) = props.get("run_segments") else {
        return Err("runs missing".into());
    };
    assert_eq!(runs.len(), 2);
    let private_graph = String::from_utf8(imported.graph().canonical_json()?)?;
    for retained in [
        "charPrIDRef",
        "charStyleIDRef",
        "8000",
        "atom_metadata",
        "source_anchor",
    ] {
        assert!(private_graph.contains(retained));
    }
    check_nodes(&imported, &imported.graph().sections()[0].body)?;
    assert_eq!(imported.verify_source(&bytes)?, *imported.receipt());
    Ok(())
}

#[test]
fn unknown_inline_and_section_objects_are_exact_not_fabricated_typed_forms() -> TestResult {
    let body = format!(
        r#"<u:future secret="TOPSECRET"><u:child/></u:future><hp:p id="7"><hp:run><hp:t>A</hp:t><hp:checkBtn id="7"/><hp:t>B</hp:t></hp:run></hp:p>{}"#,
        paragraph("C")
    );
    let bytes = archive(&[section(&body)])?;
    let imported = import(&bytes)?;
    let flow = &imported.graph().sections()[0].body;
    assert_eq!(visible(flow), "ABC");
    assert_eq!(imported.receipt().opaque_nodes, 2);
    assert!(matches!(&flow.children[0], Node::EmbeddedObject(_)));
    let Node::Paragraph(p) = &flow.children[1] else {
        return Err("paragraph".into());
    };
    assert!(matches!(&p.inlines[1], Inline::ControlRef { .. }));
    assert!(matches!(&flow.children[2], Node::EmbeddedObject(_)));
    assert!(
        !flow
            .children
            .iter()
            .any(|n| matches!(n, Node::FormControl(_)))
    );
    check_nodes(&imported, flow)?;
    Ok(())
}

#[test]
fn merged_grid_cell_bodies_and_real_placement_match_existing_reader() -> TestResult {
    let first = format!("<hp:tr>{}</hp:tr>", cell(0, 0, 1, 2, &paragraph("MERGED")));
    let second = format!(
        "<hp:tr>{}{}</hp:tr>",
        cell(1, 0, 1, 1, &paragraph("LEFT")),
        cell(1, 1, 1, 1, &paragraph("RIGHT"))
    );
    let table = table(&(first + &second), 2, 2);
    let outer = format!(
        r#"<hp:p id="7"><hp:run><hp:t>BEFORE</hp:t>{table}<hp:t>AFTER</hp:t></hp:run></hp:p>"#
    );
    let bytes = archive(&[section(&outer)])?;
    let imported = import(&bytes)?;
    let flow = &imported.graph().sections()[0].body;
    let Node::Paragraph(p) = &flow.children[0] else {
        return Err("paragraph".into());
    };
    assert!(matches!(&p.inlines[1], Inline::ControlRef { .. }));
    let Node::Table(t) = &flow.children[1] else {
        return Err("real table".into());
    };
    assert_eq!((t.rows, t.columns, t.cells.len()), (2, 2, 3));
    assert_eq!(
        (
            t.cells[0].row,
            t.cells[0].column,
            t.cells[0].row_span,
            t.cells[0].column_span
        ),
        (0, 0, 1, 2)
    );
    assert_eq!(visible(&t.cells[0].body), "MERGED");
    assert_eq!(
        (
            imported.receipt().tables,
            imported.receipt().table_cells,
            imported.receipt().paragraphs
        ),
        (1, 3, 4)
    );
    check_nodes(&imported, flow)?;
    Ok(())
}

#[test]
fn nested_table_is_a_real_nested_cell_flow_not_flattened_text() -> TestResult {
    let inner = table(
        &format!("<hp:tr>{}</hp:tr>", cell(0, 0, 1, 1, &paragraph("INNER"))),
        1,
        1,
    );
    let inside = format!(r#"<hp:p id="7"><hp:run><hp:t>CELL</hp:t>{inner}</hp:run></hp:p>"#);
    let outer = table(
        &format!("<hp:tr>{}</hp:tr>", cell(0, 0, 1, 1, &inside)),
        1,
        1,
    );
    let bytes = archive(&[section(&outer)])?;
    let imported = import(&bytes)?;
    let Node::Table(t) = &imported.graph().sections()[0].body.children[0] else {
        return Err("outer".into());
    };
    assert!(matches!(&t.cells[0].body.children[1], Node::Table(_)));
    assert_eq!(visible(&t.cells[0].body), "CELLINNER");
    assert_eq!(imported.receipt().tables, 2);
    check_nodes(&imported, &imported.graph().sections()[0].body)?;
    Ok(())
}

#[test]
fn invalid_supported_paragraph_and_grid_do_not_fall_back_to_opaque() -> TestResult {
    let malformed = [
        "<hp:p id='not-number'><hp:run><hp:t>A</hp:t></hp:run></hp:p>",
        "<hp:p id='7'><hp:run><hp:ctrl><hp:fieldEnd beginIDRef='missing'/></hp:ctrl></hp:run></hp:p>",
    ];
    for body in malformed {
        let bytes = archive(&[section(body)])?;
        let source = ImportedSourcePackage::import(
            &bytes,
            DocumentId::parse("doc")?,
            digest(&bytes),
            SourceImportLimits::default(),
        )?;
        assert!(matches!(
            ImportedDocumentStructure::import(source),
            Err(StructureImportError::Paragraph { .. })
        ));
    }
    let missing = table(
        &format!("<hp:tr>{}</hp:tr>", cell(0, 0, 1, 1, &paragraph("A"))),
        2,
        2,
    );
    let bytes = archive(&[section(&missing)])?;
    let source = ImportedSourcePackage::import(
        &bytes,
        DocumentId::parse("doc")?,
        digest(&bytes),
        SourceImportLimits::default(),
    )?;
    assert!(matches!(
        ImportedDocumentStructure::import(source),
        Err(StructureImportError::Table { .. })
    ));
    Ok(())
}

#[test]
fn duplicate_native_ids_across_sections_do_not_alias_logical_nodes() -> TestResult {
    let bytes = archive(&[section(&paragraph("FIRST")), section(&paragraph("SECOND"))])?;
    let imported = import(&bytes)?;
    let sections = imported.graph().sections();
    assert_eq!(sections.len(), 2);
    assert_ne!(
        sections[0].section_id.as_str(),
        sections[1].section_id.as_str()
    );
    assert_ne!(
        sections[0].body.children[0].common().node_id.as_str(),
        sections[1].body.children[0].common().node_id.as_str()
    );
    assert_eq!(visible(&sections[0].body), "FIRST");
    assert_eq!(visible(&sections[1].body), "SECOND");
    Ok(())
}

#[test]
fn all_original_parts_have_bound_resources_and_exact_preservation_not_security_admission()
-> TestResult {
    let bytes = archive(&[section(&paragraph("BODY"))])?;
    let imported = import(&bytes)?;
    let draft = imported.graph().clone().into_draft();
    assert_eq!(draft.resources.len(), imported.source().parts().len());
    assert_eq!(
        draft.opaque_preservation_bag.len(),
        imported.source().parts().len()
    );
    assert!(
        draft
            .opaque_preservation_bag
            .iter()
            .all(|p| p.preservation == OpaquePreservation::PreserveExact)
    );
    for part in imported.source().parts() {
        assert!(draft.resources.iter().any(|r| {
            r.artifact
                .as_ref()
                .is_some_and(|a| a.sha256 == part.anchor().fingerprint_sha256)
        }));
    }
    assert!(draft.metadata.iter().any(|(key, value)| key == "scope"
        && matches!(value, PropertyValue::Text(scope) if scope == STRUCTURE_IMPORT_SCOPE)));
    assert!(
        draft
            .security_state
            .properties
            .iter()
            .any(|(_, value)| matches!(value, PropertyValue::Text(v) if v.contains("unqualified")))
    );
    let canonical = imported.graph().canonical_json()?;
    assert!(
        DocumentGraph::from_json(&canonical, DocumentGraphLimits::default())? == *imported.graph()
    );
    Ok(())
}

#[test]
fn wrong_section_namespace_never_becomes_invented_body_and_fresh_drift_rejects() -> TestResult {
    let wrong = archive(&["<sec xmlns='urn:unknown'/>".into()])?;
    let source = ImportedSourcePackage::import(
        &wrong,
        DocumentId::parse("doc")?,
        digest(&wrong),
        SourceImportLimits::default(),
    )?;
    assert!(matches!(
        ImportedDocumentStructure::import(source),
        Err(StructureImportError::Section)
    ));
    let bytes = archive(&[section(&paragraph("BODY"))])?;
    let imported = import(&bytes)?;
    let changed = archive(&[section(&paragraph("CHANGED"))])?;
    assert!(matches!(
        imported.verify_source(&changed),
        Err(StructureImportError::Source(
            SourceImportError::SourceChanged
        ))
    ));
    Ok(())
}

#[test]
fn debug_receipt_and_errors_do_not_disclose_values_or_paths() -> TestResult {
    let bytes = archive(&[section(&paragraph("TOPSECRET"))])?;
    let imported = import(&bytes)?;
    let output = format!(
        "{imported:?} {:?} {}",
        imported.receipt(),
        StructureImportError::Graph
    );
    for forbidden in ["TOPSECRET", "PRIVATE_BINARY", "private.dat", "<hp:"] {
        assert!(!output.contains(forbidden));
    }
    Ok(())
}

#[test]
fn direct_section_text_is_rejected_and_rebound_namespaces_are_not_misclassified() -> TestResult {
    for body in ["unmodeled text", "&#x20;unmodeled"] {
        let bytes = archive(&[section(body)])?;
        let source = ImportedSourcePackage::import(
            &bytes,
            DocumentId::parse("invalid-body")?,
            digest(&bytes),
            SourceImportLimits::default(),
        )?;
        assert!(matches!(
            ImportedDocumentStructure::import(source),
            Err(StructureImportError::Binding)
        ));
    }
    let body = format!(
        "{}<hp:p xmlns:hp='urn:future'><hp:run><hp:t>TOPSECRET</hp:t></hp:run></hp:p>{}",
        paragraph("FIRST"),
        paragraph("LAST")
    );
    let bytes = archive(&[section(&body)])?;
    let imported = import(&bytes)?;
    assert_eq!(visible(&imported.graph().sections()[0].body), "FIRSTLAST");
    assert_eq!(imported.receipt().paragraphs, 2);
    assert_eq!(imported.receipt().opaque_nodes, 1);
    assert!(matches!(
        &imported.graph().sections()[0].body.children[1],
        Node::EmbeddedObject(_)
    ));
    Ok(())
}

#[test]
fn ten_locked_actual_packages_import_source_backed_body_and_verify_full_fresh_graph() -> TestResult
{
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../fixtures/target-build/p09-42-product-form-values-01/output");
    let manifest: serde_json::Value =
        serde_json::from_slice(&std::fs::read(root.join("fixture-manifest.json"))?)?;
    let cases = manifest["cases"].as_array().ok_or("fixture cases")?;
    assert_eq!(cases.len(), 5);
    let mut count = 0;
    for row in cases {
        for kind in ["source", "output"] {
            let name = row[kind]["path"].as_str().ok_or("fixture path")?;
            assert!(!name.contains(['/', '\\', ':']));
            let bytes = std::fs::read(root.join(name))?;
            assert_eq!(
                hex::encode(digest(&bytes)),
                row[kind]["sha256"].as_str().ok_or("fixture sha")?
            );
            assert_eq!(
                bytes.len() as u64,
                row[kind]["bytes"].as_u64().ok_or("fixture length")?
            );
            let imported = import(&bytes)?;
            assert!(imported.receipt().paragraphs > 0);
            assert_eq!(imported.verify_source(&bytes)?, *imported.receipt());
            for section in imported.graph().sections() {
                check_nodes(&imported, &section.body)?;
            }
            count += 1;
        }
    }
    assert_eq!(count, 10);
    Ok(())
}

fn parameter_field(id: u32, payload: &str) -> String {
    format!(
        r"<hp:ctrl><hp:fieldBegin id='{id}' type='FORMULA' editable='1' dirty='0'>{payload}</hp:fieldBegin></hp:ctrl>"
    )
}

#[test]
fn preserved_parameter_fields_keep_original_stack_and_public_reader_boundary() -> TestResult {
    let payload = "<hp:parameters cnt='1' name=''><u:future value='TOPSECRET'/></hp:parameters>";
    let begin = parameter_field(1, payload);
    let body = format!(
        "<hp:p id='7'><hp:run>{begin}<hp:t>A</hp:t></hp:run><hp:run><hp:ctrl><hp:fieldBegin id='2' type='BOOKMARK'/></hp:ctrl><hp:t>B</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='2'/></hp:ctrl><hp:ctrl><hp:fieldEnd beginIDRef='1'/></hp:ctrl></hp:run></hp:p>"
    );
    let bytes = archive(&[section(&body)])?;
    let imported = import(&bytes)?;
    assert_eq!(visible(&imported.graph().sections()[0].body), "AB");
    assert_eq!(imported.receipt().paragraphs, 1);
    assert_eq!(imported.receipt().opaque_nodes, 4);
    assert_eq!(imported.verify_source(&bytes)?, *imported.receipt());
    // The pre-existing typed paragraph API STILL rejects parameterized fields;
    // no lowering or semantic acceptance is granted by the source-only profile.
    let standalone = body.replacen(
        "<hp:p ",
        &format!("<hp:p xmlns:hp='{HP}' xmlns:u='urn:future' "),
        1,
    );
    assert_eq!(
        hwpx_package::TextFlowReader::read(
            standalone.as_bytes(),
            hwpx_package::TextFlowLimits::default(),
        ),
        Err(hwpx_package::TextFlowError::UnsupportedShape)
    );
    Ok(())
}

#[test]
fn malformed_parameter_envelope_or_field_headers_never_become_opaque_success() -> TestResult {
    let valid = "<hp:parameters cnt='1'><hp:stringParam name='Command'>VALUE</hp:stringParam></hp:parameters>";
    let valid_begin = parameter_field(1, valid);
    let malformed = [
        parameter_field(
            1,
            "<hp:parameters cnt='0'><hp:stringParam/></hp:parameters>",
        ),
        parameter_field(1, "<hp:parameters cnt='no'/>"),
        parameter_field(1, "<hp:parameters cnt='0'/>DIRECT"),
        parameter_field(1, "<hp:parameters cnt='0'/><hp:parameters cnt='0'/>"),
        parameter_field(1, "<u:parameters cnt='0'/>"),
        valid_begin.replace("id='1'", "id='invalid'"),
        valid_begin.replace("editable='1'", "editable='maybe'"),
        valid_begin.replace("type='FORMULA'", "type='unknown'"),
        valid_begin.replace("dirty='0'", "dirty='0' unsupported='1'"),
        format!("{valid_begin}{valid_begin}"),
    ];
    for begin in malformed {
        let body = format!(
            "<hp:p id='7'><hp:run>{begin}<hp:t>A</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='1'/></hp:ctrl></hp:run></hp:p>"
        );
        let bytes = archive(&[section(&body)])?;
        assert!(import(&bytes).is_err());
    }
    for end in ["", "<hp:ctrl><hp:fieldEnd beginIDRef='2'/></hp:ctrl>"] {
        let body = format!("<hp:p id='7'><hp:run>{valid_begin}<hp:t>A</hp:t>{end}</hp:run></hp:p>");
        let bytes = archive(&[section(&body)])?;
        assert!(import(&bytes).is_err());
    }
    Ok(())
}

#[test]
fn all_sixteen_historical_generated_and_saved_tables_match_locked_grid_oracles() -> TestResult {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
    let manifest_bytes = std::fs::read(root.join(
        "implementation/p06/evidence/target/p06-table-aggregate.current-2020.attempt02.v2.json",
    ))?;
    assert_eq!(
        hex::encode(digest(&manifest_bytes)),
        "edc71d554e0975d511ffe6f0de1b140a30ca932d0bf2b9c7b70517c5e8674fc5"
    );
    let manifest: serde_json::Value = serde_json::from_slice(&manifest_bytes)?;
    let cases = manifest["cases"].as_array().ok_or("table cases")?;
    assert_eq!(cases.len(), 8);
    let mut count = 0;
    for row in cases {
        for kind in ["input", "output"] {
            let bytes = std::fs::read(root.join(row[kind]["path"].as_str().ok_or("table path")?))?;
            assert_eq!(hex::encode(digest(&bytes)), row[kind]["sha256"]);
            assert_eq!(bytes.len() as u64, row[kind]["bytes"]);
            let imported = import(&bytes)?;
            assert_eq!(imported.receipt().tables, 1);
            assert_eq!(imported.receipt().table_cells, 8);
            assert_eq!(imported.verify_source(&bytes)?, *imported.receipt());
            let mut tables = 0;
            for section in imported.graph().sections() {
                check_nodes(&imported, &section.body)?;
                for node in &section.body.children {
                    if let Node::Table(table) = node {
                        assert_eq!(u64::from(table.rows), row["oracle"]["rows"]);
                        assert_eq!(u64::from(table.columns), row["oracle"]["columns"]);
                        assert_eq!(table.cells.len() as u64, row["oracle"]["master_cells"]);
                        assert!(
                            table
                                .cells
                                .iter()
                                .all(|cell| !visible(&cell.body).is_empty())
                        );
                        tables += 1;
                    }
                }
            }
            assert_eq!(tables, 1);
            count += 1;
        }
    }
    assert_eq!(count, 16);
    Ok(())
}
