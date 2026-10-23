//! Locked historical inputs and bounded in-memory derivatives; no native execution.
use hwpx_package::{BoundedZipReader, PackageLimits};
use sha2::{Digest as _, Sha256};
use std::{
    error::Error,
    io::{Cursor, Write},
    path::{Component, Path, PathBuf},
};
use zip::{CompressionMethod, ZipWriter, write::SimpleFileOptions};

fn read_locked(root: &Path, row: &serde_json::Value) -> Result<Vec<u8>, Box<dyn Error>> {
    let path = Path::new(row["path"].as_str().ok_or("locked path")?);
    if path.is_absolute()
        || path
            .components()
            .any(|c| !matches!(c, Component::Normal(_)))
    {
        return Err("locked path scope".into());
    }
    let path = root.join(path);
    let meta = std::fs::symlink_metadata(&path)?;
    if !meta.is_file()
        || meta.file_type().is_symlink()
        || meta.len() > 32 * 1024 * 1024
        || Some(meta.len()) != row["bytes"].as_u64()
    {
        return Err("locked file type/size drift".into());
    }
    let bytes = std::fs::read(path)?;
    if Some(hex::encode(Sha256::digest(&bytes)).as_str()) != row["sha256"].as_str() {
        return Err("locked package SHA drift".into());
    }
    Ok(bytes)
}
fn manifest(
    root: &Path,
    path: &str,
    size: u64,
    sha: &str,
) -> Result<serde_json::Value, Box<dyn Error>> {
    let row = serde_json::json!({"path": path, "bytes": size, "sha256": sha});
    Ok(serde_json::from_slice(&read_locked(root, &row)?)?)
}
pub fn actual_corpus() -> Result<Vec<Vec<u8>>, Box<dyn Error>> {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
    let source = manifest(
        &root,
        "implementation/p09/evidence/p09-75-document-import-bookmarks.source-progress.v1.json",
        111_910,
        "dc23091137a2262c9191cd060b923df282f50a25a0bfb16e605705c712953824",
    )?;
    let rows = source["actual_inputs"].as_array().ok_or("source inputs")?;
    if rows.len() != 26 {
        return Err("source count drift".into());
    }
    let mut corpus = rows
        .iter()
        .map(|row| read_locked(&root, row))
        .collect::<Result<Vec<_>, _>>()?;
    let form_root = root.join("fixtures/target-build/p09-42-product-form-values-01/output");
    let form = manifest(
        &form_root,
        "fixture-manifest.json",
        7471,
        "8208bff3f87a4e56ec68caecaf41b00c3fdccc5b3f083289f3c13ccede19466e",
    )?;
    let cases = form["cases"].as_array().ok_or("form cases")?;
    if cases.len() != 5 {
        return Err("form count drift".into());
    }
    for row in cases {
        for kind in ["source", "output"] {
            let name = row[kind]["path"].as_str().ok_or("form name")?;
            if name.contains(['/', '\\', ':']) {
                return Err("form path scope".into());
            }
            corpus.push(read_locked(&form_root, &row[kind])?);
        }
    }
    Ok(corpus)
}
pub fn generated(template: &[u8], body: &str, resource: bool) -> Result<Vec<u8>, Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(template), PackageLimits::default())?;
    let header = reader
        .entries()
        .iter()
        .position(|v| v.path.as_str() == "Contents/header.xml")
        .ok_or("native header missing")?;
    let header = reader.read_entry(header)?;
    let container = br#"<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="Contents/content.hpf" media-type="application/hwpml-package+xml"/></rootfiles></container>"#;
    let resource_item = if resource {
        r#"<o:item id="ole1" href="BinData/object.bin" media-type="application/octet-stream"/>"#
    } else {
        ""
    };
    let opf = format!(
        r#"<o:package xmlns:o="http://www.idpf.org/2007/opf/"><o:manifest><o:item id="h" href="Contents/header.xml" media-type="application/xml"/><o:item id="s" href="Contents/section0.xml" media-type="application/xml"/>{resource_item}</o:manifest><o:spine><o:itemref idref="s"/></o:spine></o:package>"#
    );
    let section = format!(
        r#"<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">{body}</hs:sec>"#
    );
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for (name, bytes) in [
        ("mimetype", b"application/hwp+zip".as_slice()),
        ("version.xml", b"<version/>".as_slice()),
        ("META-INF/container.xml", container.as_slice()),
        ("Contents/content.hpf", opf.as_bytes()),
        ("Contents/header.xml", header.as_slice()),
        ("Contents/section0.xml", section.as_bytes()),
    ] {
        writer.start_file(
            name,
            SimpleFileOptions::default().compression_method(CompressionMethod::Stored),
        )?;
        writer.write_all(bytes)?;
    }
    if resource {
        writer.start_file(
            "BinData/object.bin",
            SimpleFileOptions::default().compression_method(CompressionMethod::Stored),
        )?;
        writer.write_all(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1opaque-ole")?;
    }
    Ok(writer.finish()?.into_inner())
}

pub fn command_fixture(
    corpus: &[Vec<u8>],
    tag: &str,
    command: &str,
) -> Result<Vec<u8>, Box<dyn Error>> {
    for bytes in corpus {
        let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
        let indexes: Vec<_> = reader
            .entries()
            .iter()
            .enumerate()
            .filter(|(_, e)| {
                let name = e.path.as_str();
                name.starts_with("Contents/section")
                    && Path::new(name)
                        .extension()
                        .is_some_and(|v| v.eq_ignore_ascii_case("xml"))
            })
            .map(|(i, _)| i)
            .collect();
        for index in indexes {
            let part = reader.read_entry(index)?;
            let xml = hwpx_package::PreservingXmlDocument::parse(&part)?;
            if xml.elements().iter().any(|e| {
                e.name().local_name() == tag
                    && e.name().namespace() == Some("http://www.hancom.co.kr/hwpml/2011/paragraph")
            }) {
                return with_command(bytes, tag, command);
            }
        }
    }
    Err("fixture native tag missing from whole locked corpus".into())
}
fn with_command(template: &[u8], tag: &str, command: &str) -> Result<Vec<u8>, Box<dyn Error>> {
    if command.contains(['<', '>', '"', '\'']) {
        return Err("fixture command encoding".into());
    }
    let mut reader = BoundedZipReader::open(Cursor::new(template), PackageLimits::default())?;
    let names: Vec<_> = reader
        .entries()
        .iter()
        .map(|e| e.path.as_str().to_owned())
        .collect();
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    let mut changed = false;
    for (index, name) in names.iter().enumerate() {
        let mut bytes = reader.read_entry(index)?;
        if !changed
            && name.starts_with("Contents/section")
            && Path::new(name)
                .extension()
                .is_some_and(|v| v.eq_ignore_ascii_case("xml"))
        {
            let xml = hwpx_package::PreservingXmlDocument::parse(&bytes)?;
            if let Some(element) = xml.elements().iter().find(|e| {
                e.name().local_name() == tag
                    && e.name().namespace() == Some("http://www.hancom.co.kr/hwpml/2011/paragraph")
            }) {
                let mut text = String::from_utf8(bytes.clone())?;
                if let Some(attribute) = element
                    .attributes()
                    .iter()
                    .find(|a| a.name().local_name() == "command")
                {
                    text.replace_range(
                        attribute.value_span().start()..attribute.value_span().end(),
                        command,
                    );
                } else {
                    let end = element.start_name_span().end();
                    text.insert_str(end, &format!(" command=\"{command}\""));
                }
                bytes = text.into_bytes();
                changed = true;
            }
        }
        writer.start_file(
            name,
            SimpleFileOptions::default().compression_method(CompressionMethod::Stored),
        )?;
        writer.write_all(&bytes)?;
    }
    if !changed {
        return Err("fixture native tag missing".into());
    }
    Ok(writer.finish()?.into_inner())
}
