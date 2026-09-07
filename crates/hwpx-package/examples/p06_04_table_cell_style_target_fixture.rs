use std::env;
use std::error::Error;
use std::fs::{self, OpenOptions};
use std::io::{Cursor, Write as _};
use std::path::{Path, PathBuf};

use hwpx_package::{
    BoundedZipReader, CellMargins, CellProtection, CellTextDirection, CellVerticalAlignment,
    Compression, IdIndex, IdIndexLimits, IdRuleProfile, PackageGraph, PackageGraphLimits,
    PackageLimits, ParagraphStyleCatalog, ParagraphStyleCatalogReader, ParagraphStyleLimits,
    TableCellStyle, TableCellStyleLimits, TableCellStyleLowerer, TableCellStyleReadback,
    TableCellStyleReader,
};
use sha2::{Digest as _, Sha256};
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, DateTime, ZipWriter};

const MAX_FIXTURE_BYTES: u64 = 8 * 1024 * 1024;
const EXPECTED_CELL_COUNT: usize = 4;
const NORMALIZED_DEFLATE_LEVEL: i64 = 6;

fn main() -> Result<(), Box<dyn Error>> {
    let mut arguments = env::args_os();
    let _program = arguments.next();
    let mode = arguments
        .next()
        .and_then(|value| value.into_string().ok())
        .ok_or("usage: p06_04_table_cell_style_target_fixture <inspect|apply> <input> [output]")?;
    let input = arguments
        .next()
        .map(PathBuf::from)
        .ok_or("usage: p06_04_table_cell_style_target_fixture <inspect|apply> <input> [output]")?;
    match mode.as_str() {
        "inspect" => {
            if arguments.next().is_some() {
                return Err("inspect accepts exactly one input path".into());
            }
            inspect_path(&input)
        }
        "apply" => {
            let output = arguments
                .next()
                .map(PathBuf::from)
                .ok_or("apply requires an output path")?;
            if arguments.next().is_some() {
                return Err("apply accepts exactly one input and one output path".into());
            }
            apply_path(&input, &output)
        }
        _ => Err("mode must be inspect or apply".into()),
    }
}

fn inspect_path(path: &Path) -> Result<(), Box<dyn Error>> {
    let bytes = read_bounded_fixture(path)?;
    let inspection = inspect_package(&bytes)?;
    print_inspection("inspect", &bytes, &inspection);
    Ok(())
}

fn apply_path(input: &Path, output: &Path) -> Result<(), Box<dyn Error>> {
    if input == output || output.extension().and_then(|value| value.to_str()) != Some("hwpx") {
        return Err("output must be a distinct .hwpx path".into());
    }
    let source = read_bounded_fixture(input)?;
    let source_sha256: [u8; 32] = Sha256::digest(&source).into();
    let inspection = inspect_package(&source)?;
    if inspection.cells.len() != EXPECTED_CELL_COUNT {
        return Err("source must contain exactly four admitted cells".into());
    }
    let targets = target_styles(&inspection.catalog, &inspection.cells)?;
    let bytes = compose_target_package(&source, &inspection.catalog, &targets)?;
    let target_inspection = inspect_package(&bytes)?;
    if target_inspection.cells.len() != targets.len()
        || target_inspection
            .cells
            .iter()
            .zip(&targets)
            .zip(&inspection.cells)
            .any(|((actual, expected), before)| {
                actual.style != *expected
                    || actual.paragraph_count != before.paragraph_count
                    || actual.content_sha256 != before.content_sha256
            })
    {
        return Err("target semantic or content readback mismatch".into());
    }
    if Sha256::digest(read_bounded_fixture(input)?) != source_sha256 {
        return Err("source changed while target was built".into());
    }
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(output)?;
    file.write_all(&bytes)?;
    file.sync_all()?;
    print_inspection("apply", &bytes, &target_inspection);
    Ok(())
}

#[derive(Debug)]
struct PackageInspection {
    part_count: usize,
    catalog: ParagraphStyleCatalog,
    cells: Vec<TableCellStyleReadback>,
}

fn inspect_package(bytes: &[u8]) -> Result<PackageInspection, Box<dyn Error>> {
    if bytes.is_empty() || bytes.len() as u64 > MAX_FIXTURE_BYTES {
        return Err("package exceeds fixture bounds".into());
    }
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    let _index = IdIndex::build(
        &mut reader,
        &graph,
        IdRuleProfile::current_hancom_2020_core_v1(),
        IdIndexLimits::default(),
    )?;
    let header = read_part(&mut reader, "Contents/header.xml")?;
    let section = read_part(&mut reader, "Contents/section0.xml")?;
    let catalog = ParagraphStyleCatalogReader::read(&header, ParagraphStyleLimits::default())?;
    let actual_cell_count =
        TableCellStyleReader::count_in_section(&section, TableCellStyleLimits::default())?;
    if actual_cell_count != EXPECTED_CELL_COUNT {
        return Err("package must contain exactly four admitted cells".into());
    }
    let mut cells = Vec::new();
    for ordinal in 0..EXPECTED_CELL_COUNT {
        cells.push(TableCellStyleReader::read_in_section(
            &section,
            ordinal,
            &catalog,
            TableCellStyleLimits::default(),
        )?);
    }
    Ok(PackageInspection {
        part_count: graph.parts.len(),
        catalog,
        cells,
    })
}

fn target_styles(
    catalog: &ParagraphStyleCatalog,
    source: &[TableCellStyleReadback],
) -> Result<Vec<TableCellStyle>, Box<dyn Error>> {
    if source.len() != EXPECTED_CELL_COUNT || catalog.border_fills.is_empty() {
        return Err("target source domains are incomplete".into());
    }
    let margins = [
        Some(CellMargins {
            left: 300,
            right: 600,
            top: 900,
            bottom: 1_200,
        }),
        None,
        Some(CellMargins {
            left: 1_500,
            right: 1_200,
            top: 900,
            bottom: 600,
        }),
        Some(CellMargins {
            left: 2_000,
            right: 2_000,
            top: 1_000,
            bottom: 1_000,
        }),
    ];
    let verticals = [
        CellVerticalAlignment::Top,
        CellVerticalAlignment::Center,
        CellVerticalAlignment::Bottom,
        CellVerticalAlignment::Center,
    ];
    let directions = [
        CellTextDirection::Horizontal,
        CellTextDirection::Vertical,
        CellTextDirection::VerticalAll,
        CellTextDirection::Horizontal,
    ];
    let protections = [
        CellProtection::Open,
        CellProtection::Editable,
        CellProtection::Protected,
        CellProtection::ProtectedEditable,
    ];
    let mut targets = Vec::new();
    targets.try_reserve_exact(EXPECTED_CELL_COUNT)?;
    for index in 0..EXPECTED_CELL_COUNT {
        let reference_source = &source[(index + 1) % EXPECTED_CELL_COUNT].style;
        let border = &catalog.border_fills[(index + 1) % catalog.border_fills.len()];
        targets.push(TableCellStyle {
            margins: margins[index],
            border_fill_id_ref: border.id,
            paragraph_property_id_ref: reference_source.paragraph_property_id_ref,
            horizontal_alignment: reference_source.horizontal_alignment,
            vertical_alignment: verticals[index],
            text_direction: directions[index],
            protection: protections[index],
        });
    }
    Ok(targets)
}

fn compose_target_package(
    source: &[u8],
    catalog: &ParagraphStyleCatalog,
    targets: &[TableCellStyle],
) -> Result<Vec<u8>, Box<dyn Error>> {
    let mut archive = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let entries = archive.entries().to_vec();
    let mut parts = Vec::new();
    parts.try_reserve_exact(entries.len())?;
    let mut replaced = 0_u8;
    for entry in entries {
        let path = entry.path.as_str().to_owned();
        let method = match entry.compression {
            Compression::Stored => CompressionMethod::Stored,
            Compression::Deflated => CompressionMethod::Deflated,
        };
        let mut bytes = archive.read_entry(entry.index)?;
        if path == "Contents/section0.xml" {
            for (ordinal, style) in targets.iter().enumerate() {
                bytes = TableCellStyleLowerer::lower_in_section(
                    &bytes,
                    ordinal,
                    style,
                    catalog,
                    TableCellStyleLimits::default(),
                )?;
            }
            replaced += 1;
        }
        parts.push((path, method, bytes));
    }
    if replaced != 1 {
        return Err("section0.xml replacement cardinality mismatch".into());
    }
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for (path, method, bytes) in parts {
        let mut options = SimpleFileOptions::default()
            .compression_method(method)
            .last_modified_time(DateTime::default())
            .system(zip::System::Unix)
            .unix_permissions(0o644);
        if method == CompressionMethod::Deflated {
            options = options.compression_level(Some(NORMALIZED_DEFLATE_LEVEL));
        }
        writer.start_file(path, options)?;
        writer.write_all(&bytes)?;
    }
    Ok(writer.finish()?.into_inner())
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
        .ok_or("required package part missing")?;
    Ok(reader.read_entry(index)?)
}

fn read_bounded_fixture(path: &Path) -> Result<Vec<u8>, Box<dyn Error>> {
    let metadata = fs::symlink_metadata(path)?;
    if !metadata.is_file()
        || metadata.file_type().is_symlink()
        || metadata.len() == 0
        || metadata.len() > MAX_FIXTURE_BYTES
    {
        return Err("fixture input is not a bounded regular file".into());
    }
    let bytes = fs::read(path)?;
    if bytes.len() as u64 != metadata.len() {
        return Err("fixture input changed while being read".into());
    }
    Ok(bytes)
}

fn print_inspection(mode: &str, bytes: &[u8], inspection: &PackageInspection) {
    let style_digest = inspection
        .cells
        .iter()
        .fold(Sha256::new(), |mut digest, cell| {
            digest.update(format!("{:?}", cell.style).as_bytes());
            digest.update(cell.content_sha256);
            digest
        });
    println!(
        "schema=hwpx-agent.p06-04-table-cell-style-target/v1 mode={mode} state=pass size={} sha256={} parts={} cells={} border_fills={} para_styles={} style_digest={}",
        bytes.len(),
        hex::encode(Sha256::digest(bytes)),
        inspection.part_count,
        inspection.cells.len(),
        inspection.catalog.border_fills.len(),
        inspection.catalog.styles.len(),
        hex::encode(style_digest.finalize()),
    );
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn bounded_reader_rejects_empty_and_oversized_files() -> Result<(), Box<dyn Error>> {
        let directory = tempfile::tempdir()?;
        let empty = directory.path().join("empty.hwpx");
        fs::write(&empty, [])?;
        assert!(read_bounded_fixture(&empty).is_err());
        let oversized = directory.path().join("oversized.hwpx");
        let file = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&oversized)?;
        file.set_len(MAX_FIXTURE_BYTES + 1)?;
        assert!(read_bounded_fixture(&oversized).is_err());
        Ok(())
    }
}
