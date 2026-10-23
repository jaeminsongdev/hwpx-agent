//! In-memory derivatives of pinned historical inputs; originals are never written.
use hwpx_package::{BoundedZipReader, PackageLimits, PreservingXmlDocument};
use std::{
    error::Error,
    io::{Cursor, Write},
};
use zip::{CompressionMethod, ZipWriter, write::SimpleFileOptions};
#[path = "document_import_settings_inputs.rs"]
pub mod inputs;

pub fn mutate_first_cell(
    bytes: &[u8],
    change: impl FnOnce(&str) -> Result<String, Box<dyn Error>>,
) -> Result<Vec<u8>, Box<dyn Error>> {
    mutate_section(bytes, |text| {
        let xml = PreservingXmlDocument::parse(text.as_bytes())?;
        let cell = xml
            .elements()
            .iter()
            .find(|e| {
                e.name().namespace() == Some("http://www.hancom.co.kr/hwpml/2011/paragraph")
                    && e.name().local_name() == "tc"
            })
            .ok_or("source cell")?;
        let span = cell.outer_span().ok_or("cell span")?;
        let original = &text[span.start()..span.end()];
        let replacement = change(original)?;
        if replacement == original {
            return Err("unchanged cell derivative".into());
        }
        let mut changed = text.to_owned();
        changed.replace_range(span.start()..span.end(), &replacement);
        Ok(changed)
    })
}
fn mutate_section(
    bytes: &[u8],
    change: impl FnOnce(&str) -> Result<String, Box<dyn Error>>,
) -> Result<Vec<u8>, Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let names: Vec<_> = reader
        .entries()
        .iter()
        .map(|e| e.path.as_str().to_owned())
        .collect();
    let index = names
        .iter()
        .position(|p| p == "Contents/section0.xml")
        .ok_or("section")?;
    let old = reader.read_entry(index)?;
    let text = std::str::from_utf8(&old)?;
    let changed = change(text)?;
    if changed == text {
        return Err("unchanged derivative".into());
    }
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for (index, name) in names.into_iter().enumerate() {
        let data = reader.read_entry(index)?;
        writer.start_file(
            &name,
            SimpleFileOptions::default().compression_method(CompressionMethod::Stored),
        )?;
        writer.write_all(if name == "Contents/section0.xml" {
            changed.as_bytes()
        } else {
            &data
        })?;
    }
    Ok(writer.finish()?.into_inner())
}
pub fn replace_formula(bytes: &[u8], replacement: &str) -> Result<Vec<u8>, Box<dyn Error>> {
    // The original source reader requires canonical native text. Build a
    // derivative with the original AST serializer; do not relax that reader.
    let limits = domain_ir::FormulaLimits::default();
    let ast = domain_ir::FormulaAst::parse(
        replacement.strip_prefix('=').ok_or("formula prefix")?,
        limits,
    )?;
    let replacement = format!("={}", ast.canonical_formula(limits)?);
    mutate_section(bytes, |text| {
        let xml = PreservingXmlDocument::parse(text.as_bytes())?;
        let parameter = xml
            .elements()
            .iter()
            .find(|e| {
                e.name().namespace() == Some("http://www.hancom.co.kr/hwpml/2011/paragraph")
                    && e.name().local_name() == "stringParam"
                    && e.attributes().iter().any(|a| {
                        a.name().namespace().is_none()
                            && a.name().local_name() == "name"
                            && &text[a.value_span().start()..a.value_span().end()] == "Formula"
                    })
            })
            .ok_or("formula parameter")?;
        let span = parameter.content_span().ok_or("formula text")?;
        let old = &text[span.start()..span.end()];
        if old.is_empty() || text.matches(old).count() != 2 {
            return Err("formula tuple count".into());
        }
        Ok(text.replace(old, &replacement))
    })
}
pub fn replace_first_text(cell: &str, replacement: &str) -> Result<String, Box<dyn Error>> {
    let begin = cell.find("<hp:t>").ok_or("actual numeric text start")? + "<hp:t>".len();
    let end = begin
        + cell[begin..]
            .find("</hp:t>")
            .ok_or("actual numeric text end")?;
    let mut out = cell.to_owned();
    out.replace_range(begin..end, replacement);
    Ok(out)
}
