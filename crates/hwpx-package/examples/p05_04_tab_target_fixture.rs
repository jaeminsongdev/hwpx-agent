use std::env;
use std::error::Error;
use std::fs::{self, OpenOptions};
use std::io::{Cursor, Read as _, Write as _};
use std::path::{Path, PathBuf};

use hwpx_package::{
    BoundedZipReader, Hancom2020Vs0Builder, LineType2, PackageGraph, PackageGraphLimits,
    PackageLimits, ParagraphStyleCatalogReader, ParagraphStyleLimits, TabDefinition,
    TabDefinitionCatalog, TabDefinitionCatalogReader, TabDefinitionCatalogWriter,
    TabDefinitionLimits, TabItem, TabPositionUnit, TabStop, TabStopAlignment, TextFlowLimits,
    TextFlowReader,
};
use sha2::{Digest as _, Sha256};
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, DateTime, ZipArchive, ZipWriter};

const FIXTURE_TEXT: &str = "P05-04-TAB-FIXTURE";
const EXPECTED_TEXT: &str = "P05-04\tLEFT\tCENTER\tRIGHT\t123.45";
const TAB_FRAGMENT_END: &str = "</hh:tabProperties>";
const MAX_TARGET_FIXTURE_BYTES: u64 = 8 * 1024 * 1024;

fn main() -> Result<(), Box<dyn Error>> {
    let mut arguments = env::args_os();
    let _program = arguments.next();
    let mode = arguments
        .next()
        .and_then(|value| value.into_string().ok())
        .ok_or("usage: p05_04_tab_target_fixture <build|inspect> <path.hwpx>")?;
    let path = arguments
        .next()
        .map(PathBuf::from)
        .ok_or("usage: p05_04_tab_target_fixture <build|inspect> <path.hwpx>")?;
    if arguments.next().is_some() {
        return Err("usage: p05_04_tab_target_fixture <build|inspect> <path.hwpx>".into());
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
    let bytes = rebuild_with_tabs(&source_bytes)?;
    let inspection = inspect_bytes(&bytes, &expected_source_catalog())?;

    let mut output = OpenOptions::new().write(true).create_new(true).open(path)?;
    output.write_all(&bytes)?;
    output.sync_all()?;
    println!(
        "schema=hwpx-agent.p05-04-tab-target-fixture/v1 mode=build state=pass size={} sha256={} definitions={} stops={} text_sha256={}",
        bytes.len(),
        hex::encode(Sha256::digest(&bytes)),
        inspection.definition_count,
        inspection.stop_count,
        inspection.text_sha256,
    );
    Ok(())
}

fn inspect_path(path: &Path) -> Result<(), Box<dyn Error>> {
    let bytes = read_bounded_fixture(path)?;
    let inspection = inspect_bytes(&bytes, &expected_hancom_2020_saved_catalog())?;
    println!(
        "schema=hwpx-agent.p05-04-tab-target-fixture/v1 mode=inspect state=pass size={} sha256={} definitions={} stops={} text_sha256={}",
        bytes.len(),
        hex::encode(Sha256::digest(&bytes)),
        inspection.definition_count,
        inspection.stop_count,
        inspection.text_sha256,
    );
    Ok(())
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
    definition_count: usize,
    stop_count: usize,
    text_sha256: String,
}

fn inspect_bytes(
    bytes: &[u8],
    expected_catalog: &TabDefinitionCatalog,
) -> Result<Inspection, Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    let header = read_part(&mut reader, "Contents/header.xml")?;
    let section = read_part(&mut reader, "Contents/section0.xml")?;

    let catalog = TabDefinitionCatalogReader::read(&header, TabDefinitionLimits::default())
        .map_err(|error| std::io::Error::other(format!("tab_catalog:{error:?}")))?;
    if catalog != *expected_catalog {
        return Err("target tab-definition semantic readback mismatch".into());
    }
    let paragraphs = ParagraphStyleCatalogReader::read(&header, ParagraphStyleLimits::default())
        .map_err(|error| std::io::Error::other(format!("paragraph_catalog:{error:?}")))?;
    catalog.validate_paragraph_references(&paragraphs, TabDefinitionLimits::default())?;
    if paragraphs
        .styles
        .first()
        .map(|style| style.tab_property_id_ref)
        != Some(3)
    {
        return Err("target paragraph does not reference custom tab definition".into());
    }

    let paragraph = extract_exact_element(&section, b"<hp:p ", b"</hp:p>")?;
    let paragraph = std::str::from_utf8(paragraph)?;
    let paragraph = replace_exact_once(
        paragraph,
        "<hp:p ",
        "<hp:p xmlns:hp=\"http://www.hancom.co.kr/hwpml/2011/paragraph\" ",
    )?;
    let flow = TextFlowReader::read(paragraph.as_bytes(), TextFlowLimits::default())
        .map_err(|error| std::io::Error::other(format!("text_flow:{error:?}")))?;
    if flow.visible_text_nfc()? != EXPECTED_TEXT {
        return Err("target tab text readback mismatch".into());
    }
    if graph.parts.len() != reader.entries().len() {
        return Err("package graph does not cover every entry".into());
    }
    Ok(Inspection {
        definition_count: catalog.definitions.len(),
        stop_count: catalog
            .definitions
            .iter()
            .map(|definition| definition.stops.len())
            .sum(),
        text_sha256: hex::encode(Sha256::digest(EXPECTED_TEXT.as_bytes())),
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

fn rebuild_with_tabs(source: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
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
    let tab_xml = TabDefinitionCatalogWriter::lower(
        &expected_source_catalog(),
        TabDefinitionLimits::default(),
    )?;
    let tab_xml = std::str::from_utf8(&tab_xml)?;
    let replacement = extract_exact_element(
        tab_xml.as_bytes(),
        b"<hh:tabProperties ",
        TAB_FRAGMENT_END.as_bytes(),
    )?;
    let replacement = std::str::from_utf8(replacement)?;
    let existing = extract_exact_element(
        source.as_bytes(),
        b"<hh:tabProperties ",
        TAB_FRAGMENT_END.as_bytes(),
    )?;
    let existing = std::str::from_utf8(existing)?;
    let source = replace_exact_once(source, existing, replacement)?;
    let source = replace_exact_once(
        &source,
        "<hh:paraPr id=\"0\" tabPrIDRef=\"0\"",
        "<hh:paraPr id=\"0\" tabPrIDRef=\"3\"",
    )?;
    Ok(source.into_bytes())
}

fn mutate_section(bytes: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    let source = std::str::from_utf8(bytes)?;
    let replacement = concat!(
        "<hp:t>P05-04",
        "<hp:tab width=\"2000\" leader=\"0\" type=\"0\"/>LEFT",
        "<hp:tab width=\"2001\" leader=\"0\" type=\"0\"/>CENTER",
        "<hp:tab width=\"1999\" leader=\"0\" type=\"0\"/>RIGHT",
        "<hp:tab width=\"2000\" leader=\"0\" type=\"0\"/>123.45",
        "</hp:t>",
    );
    Ok(replace_exact_once(source, "<hp:t>P05-04-TAB-FIXTURE</hp:t>", replacement)?.into_bytes())
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

fn expected_source_catalog() -> TabDefinitionCatalog {
    expected_catalog_with_center_fallback(4001)
}

fn expected_hancom_2020_saved_catalog() -> TabDefinitionCatalog {
    expected_catalog_with_center_fallback(4000)
}

fn expected_catalog_with_center_fallback(center_fallback: i32) -> TabDefinitionCatalog {
    let custom = [
        (1000, 2000, TabStopAlignment::Left, LineType2::Dot),
        (
            2000,
            center_fallback,
            TabStopAlignment::Center,
            LineType2::Solid,
        ),
        (3000, 6000, TabStopAlignment::Right, LineType2::Dash),
        (4000, 8000, TabStopAlignment::Decimal, LineType2::DashDot),
    ]
    .into_iter()
    .map(
        |(current, fallback, alignment, leader)| TabStop::HwpUnitChar {
            current: TabItem {
                position: current,
                alignment,
                leader,
                unit: Some(TabPositionUnit::HwpUnit),
            },
            fallback: TabItem {
                position: fallback,
                alignment,
                leader,
                unit: None,
            },
        },
    )
    .collect();
    TabDefinitionCatalog {
        definitions: vec![
            TabDefinition {
                id: 0,
                auto_tab_left: false,
                auto_tab_right: false,
                stops: Vec::new(),
            },
            TabDefinition {
                id: 1,
                auto_tab_left: true,
                auto_tab_right: false,
                stops: Vec::new(),
            },
            TabDefinition {
                id: 2,
                auto_tab_left: false,
                auto_tab_right: true,
                stops: Vec::new(),
            },
            TabDefinition {
                id: 3,
                auto_tab_left: false,
                auto_tab_right: false,
                stops: custom,
            },
        ],
    }
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
    fn current_2020_save_expectation_changes_only_the_observed_odd_fallback() {
        let mut source = expected_source_catalog();
        let saved = expected_hancom_2020_saved_catalog();
        let TabStop::HwpUnitChar { fallback, .. } = &mut source.definitions[3].stops[1] else {
            panic!("fixture center stop must use HwpUnitChar");
        };
        assert_eq!(fallback.position, 4001);
        fallback.position = 4000;
        assert_eq!(source, saved);
    }
}
