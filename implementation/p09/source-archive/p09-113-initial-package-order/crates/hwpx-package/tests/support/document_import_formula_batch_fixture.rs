//! In-memory derivatives of the immutable actual corpus; no native/permission claim.
use hwpx_package::{BoundedZipReader, PackageLimits, PreservingXmlDocument};
use std::{
    collections::BTreeMap,
    error::Error,
    io::{Cursor, Write},
};
use zip::{CompressionMethod, ZipWriter, write::SimpleFileOptions};
#[path = "document_import_formula_output_fixture.rs"]
mod output;
#[path = "document_import_formula_evaluation_fixture.rs"]
pub mod source;
pub type Result<T> = std::result::Result<T, Box<dyn Error>>;

pub fn blank_results(bytes: &[u8], self_closing: bool) -> Result<Vec<u8>> {
    output::blank_results(bytes, self_closing)
}

pub fn batch(input: &str) -> Result<Vec<u8>> {
    let actual = source::inputs::actual_corpus()?.remove(0);
    let one = source::replace_formula(&actual, "=A1+1")?;
    let one = source::mutate_first_cell(&one, |cell| source::replace_first_text(cell, input))?;
    output::section(&one, |text| {
        let xml = PreservingXmlDocument::parse(text.as_bytes())?;
        let cells: Vec<_> = xml
            .elements()
            .iter()
            .enumerate()
            .filter(|(_, e)| e.name().local_name() == "tc")
            .collect();
        if cells.len() != 8 {
            return Err("expected pinned actual two-row four-column table".into());
        }
        let sub = |cell: usize| -> Result<_> {
            xml.elements()
                .iter()
                .find(|e| e.parent() == Some(cell) && e.name().local_name() == "subList")
                .and_then(hwpx_package::XmlElementToken::outer_span)
                .ok_or("actual cell sublist".into())
        };
        let original = sub(cells[7].0)?;
        let original = &text[original.start()..original.end()];
        // Preserve the actual root namespace context while parsing a copied subtree.
        let root = &xml.elements()[0];
        let tag = root.start_tag_span();
        let name = root.start_name_span();
        let wrapped = format!(
            "{}{original}</{}>",
            &text[tag.start()..tag.end()],
            &text[name.start()..name.end()]
        );
        let renamed = renumber(&wrapped, 1000)?;
        let renamed_xml = PreservingXmlDocument::parse(renamed.as_bytes())?;
        let content = renamed_xml.elements()[0]
            .content_span()
            .ok_or("copied content")?;
        let mut copied = renamed[content.start()..content.end()].to_owned();
        let ast = domain_ir::FormulaAst::parse("D2+1", domain_ir::FormulaLimits::default())?;
        let old = format!(
            "={}",
            domain_ir::FormulaAst::parse("A1+1", domain_ir::FormulaLimits::default())?
                .canonical_formula(domain_ir::FormulaLimits::default())?
        );
        let new = format!(
            "={}",
            ast.canonical_formula(domain_ir::FormulaLimits::default())?
        );
        if copied.matches(&old).count() != 2 {
            return Err("actual native tuple".into());
        }
        copied = copied.replace(&old, &new);
        let target = sub(cells[1].0)?;
        let mut result = text.to_owned();
        result.replace_range(target.start()..target.end(), &copied);
        Ok(result)
    })
}
pub fn entries(bytes: &[u8]) -> Result<BTreeMap<String, Vec<u8>>> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let mut result = BTreeMap::new();
    for i in 0..reader.entries().len() {
        let name = reader.entries()[i].path.as_str().to_owned();
        if result.insert(name, reader.read_entry(i)?).is_some() {
            return Err("duplicate part".into());
        }
    }
    Ok(result)
}
pub fn pack(parts: &BTreeMap<String, Vec<u8>>) -> Result<Vec<u8>> {
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for (name, bytes) in parts {
        writer.start_file(
            name,
            SimpleFileOptions::default().compression_method(CompressionMethod::Stored),
        )?;
        writer.write_all(bytes)?;
    }
    Ok(writer.finish()?.into_inner())
}
pub fn two_sections(first: &[u8], second: &[u8]) -> Result<Vec<u8>> {
    let mut parts = entries(first)?;
    let other = entries(second)?;
    let next = renumber(
        std::str::from_utf8(other.get("Contents/section0.xml").ok_or("second section")?)?,
        10000,
    )?;
    let opf = String::from_utf8(parts.get("Contents/content.hpf").ok_or("opf")?.clone())?;
    let xml = PreservingXmlDocument::parse(opf.as_bytes())?;
    let item = xml
        .elements()
        .iter()
        .find(|e| {
            e.name().local_name() == "item"
                && e.attributes().iter().any(|a| {
                    a.name().local_name() == "href"
                        && opf[a.value_span().start()..a.value_span().end()]
                            .ends_with("section0.xml")
                })
        })
        .ok_or("actual section manifest item")?;
    let attr = |name: &str| -> Result<_> {
        item.attributes()
            .iter()
            .find(|a| a.name().local_name() == name)
            .map(|a| a.value_span())
            .ok_or("item attribute".into())
    };
    let id = attr("id")?;
    let old_id = &opf[id.start()..id.end()];
    let item_span = item.outer_span().ok_or("manifest item span")?;
    let href = attr("href")?;
    let mut new_item = opf[item_span.start()..item_span.end()].to_owned();
    let mut edits = vec![
        (id, "p113-second".to_owned()),
        (
            href,
            opf[href.start()..href.end()].replace("section0.xml", "section1.xml"),
        ),
    ];
    edits.sort_by_key(|e| e.0.start());
    for (span, value) in edits.into_iter().rev() {
        new_item.replace_range(
            span.start() - item_span.start()..span.end() - item_span.start(),
            &value,
        );
    }
    let reference = xml
        .elements()
        .iter()
        .find(|e| {
            e.name().local_name() == "itemref"
                && e.attributes().iter().any(|a| {
                    a.name().local_name() == "idref"
                        && &opf[a.value_span().start()..a.value_span().end()] == old_id
                })
        })
        .ok_or("actual spine itemref")?;
    let ref_span = reference.outer_span().ok_or("spine reference span")?;
    let ref_attr = reference
        .attributes()
        .iter()
        .find(|a| a.name().local_name() == "idref")
        .ok_or("idref")?
        .value_span();
    let mut new_ref = opf[ref_span.start()..ref_span.end()].to_owned();
    new_ref.replace_range(
        ref_attr.start() - ref_span.start()..ref_attr.end() - ref_span.start(),
        "p113-second",
    );
    let insertion = |name: &str| -> Result<usize> {
        xml.elements()
            .iter()
            .find(|e| e.name().local_name() == name)
            .and_then(hwpx_package::XmlElementToken::content_span)
            .map(|s| s.end())
            .ok_or("opf container".into())
    };
    let mut insertions = vec![
        (insertion("manifest")?, new_item),
        (insertion("spine")?, new_ref),
    ];
    insertions.sort_by_key(|e| e.0);
    let mut next_opf = opf.clone();
    for (at, text) in insertions.into_iter().rev() {
        next_opf.insert_str(at, &text);
    }
    parts.insert("Contents/content.hpf".into(), next_opf.into_bytes());
    parts.insert("Contents/section1.xml".into(), next.into_bytes());
    pack(&parts)
}
fn renumber(text: &str, offset: u32) -> Result<String> {
    let xml = PreservingXmlDocument::parse(text.as_bytes())?;
    let mut edits = Vec::new();
    for node in xml.elements() {
        for attr in node.attributes() {
            let local = node.name().local_name();
            let name = attr.name().local_name();
            if (matches!(local, "fieldBegin" | "fieldEnd")
                && matches!(name, "id" | "beginIDRef" | "fieldid"))
                || (matches!(local, "tbl" | "p") && name == "id")
            {
                let span = attr.value_span();
                let value: u32 = text[span.start()..span.end()].parse()?;
                edits.push((
                    span,
                    value.checked_add(offset).ok_or("ID overflow")?.to_string(),
                ));
            }
        }
    }
    edits.sort_by_key(|e| e.0.start());
    let mut next = text.to_owned();
    for (span, value) in edits.into_iter().rev() {
        next.replace_range(span.start()..span.end(), &value);
    }
    Ok(next)
}
pub fn protect(bytes: &[u8], part: &str, field: usize) -> Result<Vec<u8>> {
    let mut parts = entries(bytes)?;
    let text = std::str::from_utf8(parts.get(part).ok_or("protected part")?)?;
    let xml = PreservingXmlDocument::parse(text.as_bytes())?;
    let (begin, _) = xml
        .elements()
        .iter()
        .enumerate()
        .filter(|(_, e)| e.name().local_name() == "fieldBegin")
        .nth(field)
        .ok_or("protected field")?;
    let mut parent = xml.elements()[begin].parent();
    let cell = loop {
        let i = parent.ok_or("cell ancestor")?;
        let node = &xml.elements()[i];
        if node.name().local_name() == "tc" {
            break node;
        }
        parent = node.parent();
    };
    let span = cell
        .attributes()
        .iter()
        .find(|a| a.name().local_name() == "protect")
        .ok_or("actual protect")?
        .value_span();
    let mut next = text.to_owned();
    next.replace_range(span.start()..span.end(), "1");
    parts.insert(part.into(), next.into_bytes());
    pack(&parts)
}
