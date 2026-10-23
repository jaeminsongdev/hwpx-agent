//! Read-only shape counts: no numeric text, author, raw XML or source payload output.
use domain_ir::{DocumentId, Flow, Inline, Node};
use hwpx_package::document_import::{
    ImportedSourcePackage, SourceImportLimits, forms::ImportedDocumentForms,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use std::error::Error;
#[path = "../tests/support/document_import_settings_inputs.rs"]
mod inputs;
#[derive(Serialize)]
struct CellShape {
    row: u32,
    column: u32,
    children: Vec<String>,
    inlines: Vec<&'static str>,
    text_bytes: usize,
}
fn inspect(
    flow: &Flow,
    source: &ImportedSourcePackage,
    output: &mut Vec<CellShape>,
) -> Result<(), Box<dyn Error>> {
    for node in &flow.children {
        if let Node::Table(table) = node {
            for cell in &table.cells {
                let mut children = Vec::new();
                let mut inlines = Vec::new();
                let mut text_bytes = 0;
                for node in &cell.body.children {
                    let tag = source
                        .resolve_anchor(node.common().source_anchor.as_ref().ok_or("anchor")?)?
                        .element()
                        .ok_or("element")?
                        .name()
                        .local_name()
                        .to_owned();
                    children.push(tag);
                    if let Node::Paragraph(p) = node {
                        for inline in &p.inlines {
                            match inline {
                                Inline::Text { text } => {
                                    inlines.push("text");
                                    text_bytes += text.len();
                                }
                                Inline::ControlRef { .. } => inlines.push("control_ref"),
                                _ => inlines.push("other"),
                            }
                        }
                    }
                }
                output.push(CellShape {
                    row: cell.row,
                    column: cell.column,
                    children,
                    inlines,
                    text_bytes,
                });
            }
        }
    }
    Ok(())
}
fn main() -> Result<(), Box<dyn Error>> {
    let bytes = inputs::actual_corpus()?.into_iter().next().ok_or("input")?;
    let forms = ImportedDocumentForms::import(ImportedSourcePackage::import(
        &bytes,
        DocumentId::parse("numeric-shape-diagnostic")?,
        Sha256::digest(&bytes).into(),
        SourceImportLimits::default(),
    )?)?;
    let mut shapes = Vec::new();
    for s in forms.graph().sections() {
        inspect(&s.body, forms.source(), &mut shapes)?;
    }
    println!("{}", serde_json::to_string(&shapes)?);
    Ok(())
}
