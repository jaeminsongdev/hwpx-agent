//! Bounded in-memory derivatives only; original inputs are never rewritten.
use hwpx_package::{BoundedZipReader, PackageLimits, PreservingXmlDocument};
use std::{
    error::Error,
    io::{Cursor, Write},
};
use zip::{CompressionMethod, ZipWriter, write::SimpleFileOptions};
pub fn section(
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
        .ok_or("part")?;
    let raw = reader.read_entry(index)?;
    let changed = change(std::str::from_utf8(&raw)?)?;
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for (i, name) in names.iter().enumerate() {
        writer.start_file(
            name,
            SimpleFileOptions::default().compression_method(CompressionMethod::Stored),
        )?;
        let old = reader.read_entry(i)?;
        writer.write_all(if i == index { changed.as_bytes() } else { &old })?;
    }
    Ok(writer.finish()?.into_inner())
}
pub fn blank_results(bytes: &[u8], self_closing: bool) -> Result<Vec<u8>, Box<dyn Error>> {
    section(bytes, |text| {
        let xml = PreservingXmlDocument::parse(text.as_bytes())?;
        let last = xml
            .elements()
            .iter()
            .find(|e| {
                e.name().local_name() == "stringParam"
                    && e.attributes().iter().any(|a| {
                        a.name().local_name() == "name"
                            && &text[a.value_span().start()..a.value_span().end()] == "LastResult"
                    })
            })
            .ok_or("result")?;
        let span = last.content_span().ok_or("span")?;
        let result = &text[span.start()..span.end()];
        let mut next = text
            .replacen(
                &format!(";;{result}</hp:stringParam>"),
                ";;</hp:stringParam>",
                1,
            )
            .replacen(
                &format!("<hp:stringParam name=\"LastResult\">{result}</hp:stringParam>"),
                "<hp:stringParam name=\"LastResult\"></hp:stringParam>",
                1,
            )
            .replacen(&format!("<hp:t>{result}</hp:t>"), "<hp:t></hp:t>", 1);
        if self_closing {
            next = next
                .replacen(
                    "<hp:stringParam name=\"LastResult\"></hp:stringParam>",
                    "<hp:stringParam name=\"LastResult\"/>",
                    1,
                )
                .replacen("<hp:t></hp:t>", "<hp:t/>", 1);
        }
        if next == text {
            return Err("blank derivative no change".into());
        }
        Ok(next)
    })
}
