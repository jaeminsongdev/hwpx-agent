use std::env;
use std::error::Error;
use std::fs::{self, OpenOptions};
use std::io::{Cursor, Read as _, Write as _};
use std::path::{Path, PathBuf};

use hwpx_package::{
    BoundedZipReader, BulletDefinition, CompatibleHeading, Hancom2020Vs0Builder, Heading,
    HeadingType, ListDefinitionCatalog, ListDefinitionCatalogReader, ListDefinitionCatalogWriter,
    ListDefinitionLimits, NumberFormat, OutlineDefinitionBindingReader, PackageGraph,
    PackageGraphLimits, PackageLimits, ParagraphStyleCatalogReader, ParagraphStyleLimits,
    TextFlowLimits, TextFlowReader,
};
use sha2::{Digest as _, Sha256};
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, DateTime, ZipArchive, ZipWriter};

const SOURCE_HEADER: &[u8] = include_bytes!("../src/hancom_2020_minimal_header.xml");
const FIXTURE_TEXT: &str = "P05-05-NUMBER";
const EXPECTED_TEXTS: [&str; 3] = ["P05-05-NUMBER", "P05-05-BULLET", "P05-05-OUTLINE"];
const MAX_TARGET_FIXTURE_BYTES: u64 = 8 * 1024 * 1024;

fn main() -> Result<(), Box<dyn Error>> {
    let mut arguments = env::args_os();
    let _program = arguments.next();
    let mode = arguments
        .next()
        .and_then(|value| value.into_string().ok())
        .ok_or("usage: p05_05_list_target_fixture <build|inspect> <path.hwpx>")?;
    let path = arguments
        .next()
        .map(PathBuf::from)
        .ok_or("usage: p05_05_list_target_fixture <build|inspect> <path.hwpx>")?;
    if arguments.next().is_some() {
        return Err("usage: p05_05_list_target_fixture <build|inspect> <path.hwpx>".into());
    }

    match mode.as_str() {
        "build" => build(&path),
        "inspect" => inspect_path(&path),
        _ => Err("mode must be build or inspect".into()),
    }
}

fn build(path: &Path) -> Result<(), Box<dyn Error>> {
    let source = Hancom2020Vs0Builder::build(FIXTURE_TEXT)?;
    let source_bytes = source.with_verified_bytes(ToOwned::to_owned)?;
    let bytes = rebuild_with_lists(&source_bytes)?;
    let inspection = inspect_bytes(&bytes)?;

    let mut output = OpenOptions::new().write(true).create_new(true).open(path)?;
    output.write_all(&bytes)?;
    output.sync_all()?;
    print_result("build", &bytes, &inspection);
    Ok(())
}

fn inspect_path(path: &Path) -> Result<(), Box<dyn Error>> {
    let bytes = read_bounded_fixture(path)?;
    let inspection = inspect_bytes(&bytes)?;
    print_result("inspect", &bytes, &inspection);
    Ok(())
}

fn print_result(mode: &str, bytes: &[u8], inspection: &Inspection) {
    println!(
        "schema=hwpx-agent.p05-05-list-target-fixture/v1 mode={mode} state=pass size={} sha256={} numberings={} bullets={} levels={} text_sha256={}",
        bytes.len(),
        hex::encode(Sha256::digest(bytes)),
        inspection.numbering_count,
        inspection.bullet_count,
        inspection.level_count,
        inspection.text_sha256,
    );
}

fn read_bounded_fixture(path: &Path) -> Result<Vec<u8>, Box<dyn Error>> {
    let metadata = fs::symlink_metadata(path)?;
    if !metadata.is_file()
        || metadata.file_type().is_symlink()
        || metadata.len() == 0
        || metadata.len() > MAX_TARGET_FIXTURE_BYTES
    {
        return Err("fixture input is not a bounded regular file".into());
    }
    let bytes = fs::read(path)?;
    if u64::try_from(bytes.len())? != metadata.len() {
        return Err("fixture input changed while being read".into());
    }
    Ok(bytes)
}

struct Inspection {
    numbering_count: usize,
    bullet_count: usize,
    level_count: usize,
    text_sha256: String,
}

fn inspect_bytes(bytes: &[u8]) -> Result<Inspection, Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    let header = read_part(&mut reader, "Contents/header.xml")?;
    let section = read_part(&mut reader, "Contents/section0.xml")?;

    let catalog = ListDefinitionCatalogReader::read(&header, ListDefinitionLimits::default())
        .map_err(|error| std::io::Error::other(format!("list_catalog:{error:?}")))?;
    if catalog != expected_catalog()? {
        return Err("target list-definition semantic readback mismatch".into());
    }
    let paragraphs = ParagraphStyleCatalogReader::read(&header, ParagraphStyleLimits::default())
        .map_err(|error| std::io::Error::other(format!("paragraph_catalog:{error:?}")))?;
    let outline = OutlineDefinitionBindingReader::read(
        &section,
        &catalog,
        &[0, 1, 2, 3, 4, 5, 6],
        ListDefinitionLimits::default(),
    )?;
    catalog.validate_paragraph_references(
        &paragraphs,
        outline.numbering_definition_id,
        &[0, 1, 2, 3, 4, 5, 6],
        ListDefinitionLimits::default(),
    )?;
    let expected_headings = [
        Heading {
            heading_type: HeadingType::Number,
            id_ref: 2,
            level: 0,
        },
        Heading {
            heading_type: HeadingType::Bullet,
            id_ref: 1,
            level: 0,
        },
        Heading {
            heading_type: HeadingType::Outline,
            id_ref: 0,
            level: 0,
        },
    ];
    for (style, expected) in paragraphs.styles.iter().take(3).zip(expected_headings) {
        if style.heading != CompatibleHeading::Direct(expected) {
            return Err("target paragraph heading readback mismatch".into());
        }
    }

    let paragraph_bytes = extract_paragraphs(&section)?;
    if paragraph_bytes.len() != EXPECTED_TEXTS.len() {
        return Err("target paragraph count mismatch".into());
    }
    let mut visible = String::new();
    for (paragraph, expected) in paragraph_bytes.into_iter().zip(EXPECTED_TEXTS) {
        let paragraph = std::str::from_utf8(paragraph)?;
        let paragraph = replace_exact_once(
            paragraph,
            "<hp:p ",
            "<hp:p xmlns:hp=\"http://www.hancom.co.kr/hwpml/2011/paragraph\" ",
        )?;
        let flow = TextFlowReader::read(paragraph.as_bytes(), TextFlowLimits::default())
            .map_err(|error| std::io::Error::other(format!("text_flow:{error:?}")))?;
        let text = flow.visible_text_nfc()?;
        if text != expected {
            return Err("target list text readback mismatch".into());
        }
        visible.push_str(&text);
        visible.push('\n');
    }
    if graph.parts.len() != reader.entries().len() {
        return Err("package graph does not cover every entry".into());
    }
    Ok(Inspection {
        numbering_count: catalog.numberings.len(),
        bullet_count: catalog.bullets.len(),
        level_count: catalog
            .numberings
            .iter()
            .map(|definition| definition.levels.len())
            .sum::<usize>()
            + catalog.bullets.len(),
        text_sha256: hex::encode(Sha256::digest(visible.as_bytes())),
    })
}

fn read_part(
    reader: &mut BoundedZipReader<Cursor<&[u8]>>,
    path: &str,
) -> Result<Vec<u8>, Box<dyn Error>> {
    let index = reader
        .entries()
        .iter()
        .find(|entry| entry.path.as_str() == path)
        .map(|entry| entry.index)
        .ok_or("required fixture part is missing")?;
    Ok(reader.read_entry(index)?)
}

fn rebuild_with_lists(source: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    let mut archive = ZipArchive::new(Cursor::new(source))?;
    let mut parts = Vec::with_capacity(archive.len());
    for index in 0..archive.len() {
        let mut entry = archive.by_index(index)?;
        let mut bytes = Vec::new();
        entry.read_to_end(&mut bytes)?;
        let path = entry.name().to_owned();
        match path.as_str() {
            "Contents/header.xml" => bytes = mutate_header(&bytes)?,
            "Contents/section0.xml" => bytes = mutate_section(&bytes)?,
            _ => {}
        }
        parts.push((path, entry.compression(), bytes));
    }

    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for (path, method, bytes) in parts {
        let mut options = SimpleFileOptions::default()
            .compression_method(method)
            .last_modified_time(DateTime::default())
            .system(zip::System::Unix)
            .unix_permissions(0o644);
        if method == CompressionMethod::Deflated {
            options = options.compression_level(Some(6));
        }
        writer.start_file(path, options)?;
        writer.write_all(&bytes)?;
    }
    Ok(writer.finish()?.into_inner())
}

fn mutate_header(bytes: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    let source = std::str::from_utf8(bytes)?;
    let list_xml = ListDefinitionCatalogWriter::lower(
        &expected_catalog()?,
        &[0, 1, 2, 3, 4, 5, 6],
        ListDefinitionLimits::default(),
    )?;
    let list_xml = std::str::from_utf8(&list_xml)?;
    let replacement =
        extract_exact_element(list_xml.as_bytes(), b"<hh:numberings ", b"</hh:bullets>")?;
    let replacement = std::str::from_utf8(replacement)?;
    let existing =
        extract_exact_element(source.as_bytes(), b"<hh:numberings ", b"</hh:numberings>")?;
    let existing = std::str::from_utf8(existing)?;
    let mut result = replace_exact_once(source, existing, replacement)?;
    result = rewrite_para_heading(
        &result,
        0,
        "<hh:heading type=\"NUMBER\" idRef=\"2\" level=\"0\"/>",
        false,
    )?;
    result = rewrite_para_heading(
        &result,
        1,
        "<hh:heading type=\"BULLET\" idRef=\"1\" level=\"0\"/>",
        true,
    )?;
    result = rewrite_para_heading(
        &result,
        2,
        "<hh:heading type=\"OUTLINE\" idRef=\"0\" level=\"0\"/>",
        false,
    )?;
    Ok(result.into_bytes())
}

fn rewrite_para_heading(
    source: &str,
    id: u32,
    replacement: &str,
    checked: bool,
) -> Result<String, Box<dyn Error>> {
    let start = format!("<hh:paraPr id=\"{id}\" ");
    let paragraph = extract_exact_element(source.as_bytes(), start.as_bytes(), b"</hh:paraPr>")?;
    let paragraph = std::str::from_utf8(paragraph)?;
    let heading_start = paragraph
        .find("<hh:heading ")
        .ok_or("paragraph heading is missing")?;
    let heading_end = paragraph[heading_start..]
        .find("/>")
        .map(|relative| heading_start + relative + 2)
        .ok_or("paragraph heading end is missing")?;
    let old_heading = &paragraph[heading_start..heading_end];
    let mut rewritten = replace_exact_once(paragraph, old_heading, replacement)?;
    if checked {
        rewritten = replace_exact_once(&rewritten, " checked=\"0\"", " checked=\"1\"")?;
    }
    replace_exact_once(source, paragraph, &rewritten)
}

fn mutate_section(bytes: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    let source = std::str::from_utf8(bytes)?;
    let extra = concat!(
        "<hp:p id=\"2\" paraPrIDRef=\"1\" styleIDRef=\"0\" pageBreak=\"0\" columnBreak=\"0\" merged=\"0\">",
        "<hp:run charPrIDRef=\"0\"><hp:t>P05-05-BULLET</hp:t></hp:run>",
        "<hp:linesegarray><hp:lineseg textpos=\"0\" vertpos=\"1000\" vertsize=\"1000\" textheight=\"1000\" baseline=\"850\" spacing=\"600\" horzpos=\"0\" horzsize=\"42520\" flags=\"393216\"/></hp:linesegarray></hp:p>",
        "<hp:p id=\"3\" paraPrIDRef=\"2\" styleIDRef=\"0\" pageBreak=\"0\" columnBreak=\"0\" merged=\"0\">",
        "<hp:run charPrIDRef=\"0\"><hp:t>P05-05-OUTLINE</hp:t></hp:run>",
        "<hp:linesegarray><hp:lineseg textpos=\"0\" vertpos=\"2000\" vertsize=\"1000\" textheight=\"1000\" baseline=\"850\" spacing=\"600\" horzpos=\"0\" horzsize=\"42520\" flags=\"393216\"/></hp:linesegarray></hp:p>"
    );
    Ok(replace_exact_once(source, "</hs:sec>", &format!("{extra}</hs:sec>"))?.into_bytes())
}

fn extract_paragraphs(source: &[u8]) -> Result<Vec<&[u8]>, Box<dyn Error>> {
    let start = b"<hp:p ";
    let end = b"</hp:p>";
    let mut offset = 0;
    let mut paragraphs = Vec::new();
    while let Some(relative_start) = source[offset..]
        .windows(start.len())
        .position(|window| window == start)
    {
        let start_index = offset + relative_start;
        let relative_end = source[start_index..]
            .windows(end.len())
            .position(|window| window == end)
            .ok_or("paragraph end is missing")?;
        let end_index = start_index + relative_end + end.len();
        paragraphs.push(&source[start_index..end_index]);
        offset = end_index;
    }
    Ok(paragraphs)
}

fn replace_exact_once(source: &str, from: &str, to: &str) -> Result<String, Box<dyn Error>> {
    if source.matches(from).count() != 1 {
        return Err("fixture mutation anchor is not exact".into());
    }
    Ok(source.replacen(from, to, 1))
}

fn extract_exact_element<'a>(
    source: &'a [u8],
    start: &[u8],
    end: &[u8],
) -> Result<&'a [u8], Box<dyn Error>> {
    let start_index = source
        .windows(start.len())
        .position(|window| window == start)
        .ok_or("fixture element start is missing")?;
    if source[start_index + start.len()..]
        .windows(start.len())
        .any(|window| window == start)
    {
        return Err("fixture element start is not unique".into());
    }
    let relative_end = source[start_index..]
        .windows(end.len())
        .position(|window| window == end)
        .ok_or("fixture element end is missing")?;
    let end_index = start_index + relative_end + end.len();
    Ok(&source[start_index..end_index])
}

fn expected_catalog() -> Result<ListDefinitionCatalog, Box<dyn Error>> {
    let mut catalog =
        ListDefinitionCatalogReader::read(SOURCE_HEADER, ListDefinitionLimits::default())?;
    let mut custom = catalog.numberings[0].clone();
    custom.id = 2;
    custom.start = 5;
    custom.levels[0].start = 5;
    custom.levels[0].head.number_format = NumberFormat::Digit;
    "(^1)".clone_into(&mut custom.levels[0].head.template);
    custom.levels[1].head.number_format = NumberFormat::RomanSmall;
    "^1.^2".clone_into(&mut custom.levels[1].head.template);
    catalog.numberings.push(custom);
    let mut bullet_head = catalog.numberings[0].levels[0].head.clone();
    bullet_head.number_format = NumberFormat::Digit;
    bullet_head.checkable = true;
    bullet_head.template.clear();
    catalog.bullets.push(BulletDefinition {
        id: 1,
        mark: '•',
        checked_mark: Some('✓'),
        head: bullet_head,
    });
    Ok(catalog)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn bounded_fixture_reader_rejects_empty_and_oversized_files() -> Result<(), Box<dyn Error>> {
        let directory = tempfile::tempdir()?;
        let empty = directory.path().join("empty.hwpx");
        fs::write(&empty, [])?;
        assert!(read_bounded_fixture(&empty).is_err());

        let oversized = directory.path().join("oversized.hwpx");
        let file = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&oversized)?;
        file.set_len(MAX_TARGET_FIXTURE_BYTES + 1)?;
        assert!(read_bounded_fixture(&oversized).is_err());
        Ok(())
    }

    #[test]
    fn expected_catalog_has_separate_outline_number_and_bullet_definitions() -> TestResult {
        let catalog = expected_catalog()?;
        assert_eq!(catalog.numberings.len(), 2);
        assert_eq!(catalog.bullets.len(), 1);
        assert_eq!(catalog.numberings[1].levels[0].head.template, "(^1)");
        assert_eq!(catalog.bullets[0].checked_mark, Some('✓'));
        Ok(())
    }

    type TestResult = Result<(), Box<dyn Error>>;
}
