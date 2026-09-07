use std::env;
use std::error::Error;
use std::fs::{self, OpenOptions};
use std::io::{Cursor, Write as _};
use std::path::{Path, PathBuf};

use domain_ir::{
    FontMetricStatus, HwpUnit, LengthMicrometers, LogicalId, TABLE_LAYOUT_SCHEMA_VERSION,
    TableCellMeasure, TableCellSpan, TableColumnConstraint, TableGrid, TableGridLimits,
    TableLayoutLimits, TableLayoutPlan, TableLayoutProblem, TableLayoutSolver, TableWidthSpec,
};
use hwpx_package::{
    BoundedZipReader, Compression, CurrentFontMetricLimits, CurrentFontMetricReceipt, IdIndex,
    IdIndexLimits, IdRuleProfile, PackageGraph, PackageGraphLimits, PackageLimits, PageSetupLimits,
    PageSetupReader, TableInnerMarginReadback, TableLayoutHwpxLimits, TableLayoutHwpxLowerer,
    TableLayoutHwpxReadback, TableLayoutHwpxReader,
};
use sha2::{Digest as _, Sha256};
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, DateTime, ZipWriter};

const MAX_FIXTURE_BYTES: u64 = 8 * 1024 * 1024;
const MAX_RECEIPT_BYTES: u64 = 1024 * 1024;
const NORMALIZED_DEFLATE_LEVEL: i64 = 6;
const TARGET_TABLE_WIDTH_MICROMETERS: i64 = 70_000;
const CALIBRATION_GUARD_MICROMETERS: i64 = 350;
const CALIBRATION_PROFILE_ID: &str =
    "hwpx-agent.font-metric.hancom-2020-line-box-100-hwpunit-bucket/1";
const CALIBRATION_SOURCE_SHA256: &str =
    "09f3e8b27167a43650d710f6338b5712655e9fd70a30cef9c97dbe28abab1954";
const EXPECTED_INPUT_SHA256: &str =
    "b2887c929cdeb81fa1f5f3bac086265e19fb92a8bbf063f75e5ab0fbfa5cb299";
const EXPECTED_RECEIPT_SHA256: &str =
    "c4755f99ebf1e49010bf26425d61f77c496fa713d86404004348027acfc1d2ab";
const EXPECTED_CONTENT_SHA256: &str =
    "5542afbe344fa447f2598491ec7e0f7b473b2832402bfd203f26713d6448d86c";
const EXPECTED_MARGIN: TableInnerMarginReadback = TableInnerMarginReadback {
    left_hwpunit: 510,
    right_hwpunit: 510,
    top_hwpunit: 141,
    bottom_hwpunit: 141,
};
const CELL_IDS: [&str; 4] = ["cell-a", "cell-b", "cell-c", "cell-d"];

struct Arguments {
    input: PathBuf,
    expected_input_sha256: String,
    receipt_path: PathBuf,
    expected_receipt_sha256: String,
    calibration_path: PathBuf,
    expected_calibration_sha256: String,
    output: PathBuf,
}

impl Arguments {
    fn parse() -> Result<Self, Box<dyn Error>> {
        let mut arguments = env::args_os();
        let _program = arguments.next();
        let result = Self {
            input: path_argument(&mut arguments, "input target HWPX")?,
            expected_input_sha256: string_argument(&mut arguments, "expected input SHA-256")?,
            receipt_path: path_argument(&mut arguments, "font receipt")?,
            expected_receipt_sha256: string_argument(&mut arguments, "expected receipt SHA-256")?,
            calibration_path: path_argument(&mut arguments, "calibration HWPX")?,
            expected_calibration_sha256: string_argument(
                &mut arguments,
                "expected calibration SHA-256",
            )?,
            output: path_argument(&mut arguments, "output HWPX")?,
        };
        if arguments.next().is_some() {
            return Err("too many arguments".into());
        }
        Ok(result)
    }
}

fn main() -> Result<(), Box<dyn Error>> {
    run(Arguments::parse()?)
}

fn run(arguments: Arguments) -> Result<(), Box<dyn Error>> {
    let Arguments {
        input,
        expected_input_sha256,
        receipt_path,
        expected_receipt_sha256,
        calibration_path,
        expected_calibration_sha256,
        output,
    } = arguments;
    for value in [
        &expected_input_sha256,
        &expected_receipt_sha256,
        &expected_calibration_sha256,
    ] {
        require_lower_sha256(value)?;
    }
    if expected_input_sha256 != EXPECTED_INPUT_SHA256
        || expected_receipt_sha256 != EXPECTED_RECEIPT_SHA256
        || expected_calibration_sha256 != CALIBRATION_SOURCE_SHA256
    {
        return Err("exact calibrated target identity differs".into());
    }
    if input == output
        || receipt_path == output
        || calibration_path == output
        || output.extension().and_then(|value| value.to_str()) != Some("hwpx")
    {
        return Err("output must be a distinct .hwpx path".into());
    }

    let source = read_bounded_file(&input, MAX_FIXTURE_BYTES)?;
    require_digest(&source, &expected_input_sha256, "input")?;
    let source_inspection = inspect_package(&source)?;
    require_layout(&source_inspection.layout, 5_200, [15_021, 4_822])?;

    let receipt_bytes = read_bounded_file(&receipt_path, MAX_RECEIPT_BYTES)?;
    require_digest(&receipt_bytes, &expected_receipt_sha256, "font receipt")?;
    let receipt =
        CurrentFontMetricReceipt::parse(&receipt_bytes, CurrentFontMetricLimits::default())?;
    if receipt.receipt_sha256() != expected_receipt_sha256 {
        return Err("typed font receipt digest mismatch".into());
    }

    let calibration = read_bounded_file(&calibration_path, MAX_FIXTURE_BYTES)?;
    require_digest(&calibration, &expected_calibration_sha256, "calibration")?;
    let calibration_inspection = inspect_package(&calibration)?;
    require_layout(&calibration_inspection.layout, 7_364, [15_021, 4_822])?;

    let (grid, plan) = build_calibrated_plan(
        &source_inspection.layout,
        source_inspection.body_width_hwpunit,
        &receipt,
    )?;
    let (target_section, lowering) = TableLayoutHwpxLowerer::lower_in_section_with_receipt(
        &source_inspection.section,
        0,
        &grid,
        &plan,
        TableLayoutHwpxLimits::default(),
    )?;
    let target = replace_section(&source, &target_section)?;
    let target_inspection = inspect_package(&target)?;
    require_layout(&target_inspection.layout, 5_200, [15_120, 4_723])?;
    if target_inspection.part_count != source_inspection.part_count
        || target_inspection.body_width_hwpunit != source_inspection.body_width_hwpunit
        || target_inspection.layout.content_sha256 != source_inspection.layout.content_sha256
        || lowering.content_sha256 != source_inspection.layout.content_sha256
        || lowering.layout_plan_sha256 != plan.canonical_sha256(TableLayoutLimits::default())?
    {
        return Err("calibrated target readback differs from its exact plan".into());
    }

    recheck_sources(&input, &receipt_path, &calibration_path)?;
    write_create_new(&output, &target)?;

    println!(
        concat!(
            "schema=hwpx-agent.p06-05-table-layout-calibrated-target/v1 state=pass ",
            "input_sha256={} font_receipt_sha256={} calibration_sha256={} output_sha256={} ",
            "grid_sha256={} plan_sha256={} content_sha256={} guard_um={} ",
            "table_width_hwpunit={} table_height_hwpunit={} column_widths_um={} row_heights_um={}"
        ),
        expected_input_sha256,
        expected_receipt_sha256,
        expected_calibration_sha256,
        hex(Sha256::digest(&target).into()),
        hex(grid.canonical_sha256()?),
        hex(plan.canonical_sha256(TableLayoutLimits::default())?),
        hex(target_inspection.layout.content_sha256),
        CALIBRATION_GUARD_MICROMETERS,
        target_inspection.layout.table_width_hwpunit,
        target_inspection.layout.table_height_hwpunit,
        join_lengths(plan.column_widths()),
        join_lengths(plan.estimated_row_heights()),
    );
    Ok(())
}

struct PackageInspection {
    part_count: usize,
    section: Vec<u8>,
    body_width_hwpunit: u32,
    layout: TableLayoutHwpxReadback,
}

fn inspect_package(bytes: &[u8]) -> Result<PackageInspection, Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    let _index = IdIndex::build(
        &mut reader,
        &graph,
        IdRuleProfile::current_hancom_2020_table_v2(),
        IdIndexLimits::default(),
    )?;
    if graph.parts.len() != reader.entries().len() {
        return Err("package graph cardinality mismatch".into());
    }
    let section = read_part(&mut reader, "Contents/section0.xml")?;
    let body_width_hwpunit = PageSetupReader::read(&section, PageSetupLimits::default())?
        .metrics(PageSetupLimits::default())?
        .body_width;
    if TableLayoutHwpxReader::count_in_section(&section, TableLayoutHwpxLimits::default())? != 1 {
        return Err("fixture must contain exactly one table".into());
    }
    let layout =
        TableLayoutHwpxReader::read_in_section(&section, 0, TableLayoutHwpxLimits::default())?;
    Ok(PackageInspection {
        part_count: graph.parts.len(),
        section,
        body_width_hwpunit,
        layout,
    })
}

fn require_layout(
    layout: &TableLayoutHwpxReadback,
    table_height_hwpunit: u32,
    column_widths_hwpunit: [u32; 2],
) -> Result<(), Box<dyn Error>> {
    let columns = [
        layout
            .cells
            .iter()
            .find(|cell| cell.row == 0 && cell.column == 0)
            .ok_or("left column is missing")?
            .width_hwpunit,
        layout
            .cells
            .iter()
            .find(|cell| cell.row == 0 && cell.column == 1)
            .ok_or("right column is missing")?
            .width_hwpunit,
    ];
    if layout.rows != 2
        || layout.columns != 2
        || layout.cells.len() != 4
        || layout.table_width_hwpunit != 19_843
        || layout.table_height_hwpunit != table_height_hwpunit
        || layout.inner_margin != EXPECTED_MARGIN
        || layout.content_sha256 != parse_hex(EXPECTED_CONTENT_SHA256)?
        || columns != column_widths_hwpunit
    {
        return Err("fixture layout differs from the exact calibrated profile".into());
    }
    Ok(())
}

fn build_calibrated_plan(
    layout: &TableLayoutHwpxReadback,
    body_width_hwpunit: u32,
    receipt: &CurrentFontMetricReceipt,
) -> Result<(TableGrid, TableLayoutPlan), Box<dyn Error>> {
    let grid = TableGrid::new(
        2,
        2,
        CELL_IDS
            .iter()
            .enumerate()
            .map(|(index, identifier)| {
                Ok(TableCellSpan {
                    master_cell_id: LogicalId::parse(*identifier)?,
                    row: u32::try_from(index / 2)?,
                    column: u32::try_from(index % 2)?,
                    row_span: 1,
                    column_span: 1,
                })
            })
            .collect::<Result<Vec<_>, Box<dyn Error>>>()?,
        TableGridLimits::default(),
    )?;
    let leading = hwpunit_to_micrometers(layout.inner_margin.left_hwpunit)?;
    let trailing = hwpunit_to_micrometers(layout.inner_margin.right_hwpunit)?;
    let cells = CELL_IDS
        .iter()
        .map(|identifier| {
            let mut measure =
                receipt.table_cell_measure(&LogicalId::parse(*identifier)?, leading, trailing)?;
            apply_calibration_guard(&mut measure)?;
            Ok(measure)
        })
        .collect::<Result<Vec<_>, Box<dyn Error>>>()?;
    let columns = (0..2)
        .map(|column| {
            let source = layout
                .cells
                .iter()
                .find(|cell| cell.row == 0 && cell.column == column)
                .ok_or("source column width is missing")?;
            Ok(TableColumnConstraint {
                minimum_width: LengthMicrometers::from_raw(1_000),
                preferred_width: LengthMicrometers::from_raw(1_000),
                previous_width: hwpunit_to_micrometers(source.width_hwpunit)?,
                fixed_width: None,
            })
        })
        .collect::<Result<Vec<_>, Box<dyn Error>>>()?;
    let problem = TableLayoutProblem {
        schema_version: TABLE_LAYOUT_SCHEMA_VERSION.to_owned(),
        width: TableWidthSpec::Absolute {
            width: LengthMicrometers::from_raw(TARGET_TABLE_WIDTH_MICROMETERS),
        },
        body_width: hwpunit_to_micrometers(body_width_hwpunit)?,
        columns,
        cells,
    };
    let plan = TableLayoutSolver::solve(&grid, &problem, TableLayoutLimits::default())?;
    plan.require_verified()?;
    if plan.column_widths()
        != [
            LengthMicrometers::from_raw(53_340),
            LengthMicrometers::from_raw(16_660),
        ]
        || plan.estimated_row_heights()
            != [
                LengthMicrometers::from_raw(13_758),
                LengthMicrometers::from_raw(4_586),
            ]
        || plan.total_width().as_i64() != TARGET_TABLE_WIDTH_MICROMETERS
        || plan.body_overflow().as_i64() != 0
        || plan.target_overflow().as_i64() != 0
        || plan.target_underfill().as_i64() != 0
        || !plan.content_deficits().is_empty()
    {
        return Err("calibrated layout plan differs from the exact target".into());
    }
    Ok((grid, plan))
}

fn apply_calibration_guard(measure: &mut TableCellMeasure) -> Result<(), Box<dyn Error>> {
    if measure.font_metric_evidence.status != FontMetricStatus::Verified {
        return Err("base metric is not verified".into());
    }
    let guard = LengthMicrometers::from_raw(CALIBRATION_GUARD_MICROMETERS);
    measure.unbreakable_content_width = measure.unbreakable_content_width.checked_add(guard)?;
    measure.preferred_content_width = measure.preferred_content_width.checked_add(guard)?;
    measure.font_metric_evidence.profile_id = Some(CALIBRATION_PROFILE_ID.to_owned());
    measure.font_metric_evidence.source_sha256 = Some(CALIBRATION_SOURCE_SHA256.to_owned());
    Ok(())
}

fn replace_section(source: &[u8], target_section: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    let mut archive = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let entries = archive.entries().to_vec();
    let mut parts = Vec::new();
    parts.try_reserve_exact(entries.len())?;
    let mut replacements = 0_u8;
    for entry in entries {
        let path = entry.path.as_str().to_owned();
        let method = match entry.compression {
            Compression::Stored => CompressionMethod::Stored,
            Compression::Deflated => CompressionMethod::Deflated,
        };
        let bytes = if path == "Contents/section0.xml" {
            replacements = replacements.checked_add(1).ok_or("replacement overflow")?;
            target_section.to_vec()
        } else {
            archive.read_entry(entry.index)?
        };
        parts.push((path, method, bytes));
    }
    if replacements != 1 {
        return Err("section replacement cardinality mismatch".into());
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
    let result = writer.finish()?.into_inner();
    if result.len() > TableLayoutHwpxLimits::default().config().output_bytes {
        return Err("calibrated package exceeds output limit".into());
    }
    Ok(result)
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
        .ok_or("required package part is missing")?;
    Ok(reader.read_entry(index)?)
}

fn read_bounded_file(path: &Path, maximum: u64) -> Result<Vec<u8>, Box<dyn Error>> {
    let metadata = fs::symlink_metadata(path)?;
    if !metadata.is_file()
        || metadata.file_type().is_symlink()
        || metadata.len() == 0
        || metadata.len() > maximum
    {
        return Err("input is not a bounded regular file".into());
    }
    let bytes = fs::read(path)?;
    if bytes.len() as u64 != metadata.len() {
        return Err("input changed while being read".into());
    }
    Ok(bytes)
}

fn require_digest(bytes: &[u8], expected: &str, label: &str) -> Result<(), Box<dyn Error>> {
    if hex(Sha256::digest(bytes).into()) != expected {
        return Err(format!("{label} SHA-256 mismatch").into());
    }
    Ok(())
}

fn recheck(path: &Path, maximum: u64, expected: &str, label: &str) -> Result<(), Box<dyn Error>> {
    require_digest(&read_bounded_file(path, maximum)?, expected, label)
}

fn recheck_sources(input: &Path, receipt: &Path, calibration: &Path) -> Result<(), Box<dyn Error>> {
    recheck(input, MAX_FIXTURE_BYTES, EXPECTED_INPUT_SHA256, "input")?;
    recheck(
        receipt,
        MAX_RECEIPT_BYTES,
        EXPECTED_RECEIPT_SHA256,
        "font receipt",
    )?;
    recheck(
        calibration,
        MAX_FIXTURE_BYTES,
        CALIBRATION_SOURCE_SHA256,
        "calibration",
    )
}

fn write_create_new(path: &Path, bytes: &[u8]) -> Result<(), Box<dyn Error>> {
    let mut file = OpenOptions::new().write(true).create_new(true).open(path)?;
    file.write_all(bytes)?;
    Ok(file.sync_all()?)
}

fn require_lower_sha256(value: &str) -> Result<(), Box<dyn Error>> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || matches!(byte, b'a'..=b'f'))
    {
        return Err("expected SHA-256 must be lowercase hexadecimal".into());
    }
    Ok(())
}

fn parse_hex(value: &str) -> Result<[u8; 32], Box<dyn Error>> {
    require_lower_sha256(value)?;
    let mut result = [0_u8; 32];
    for (index, slot) in result.iter_mut().enumerate() {
        *slot = u8::from_str_radix(&value[index * 2..index * 2 + 2], 16)?;
    }
    Ok(result)
}

fn hwpunit_to_micrometers(value: u32) -> Result<LengthMicrometers, Box<dyn Error>> {
    Ok(*LengthMicrometers::from_hwp_unit(HwpUnit::from_raw(i64::from(value)))?.value())
}

fn join_lengths(values: &[LengthMicrometers]) -> String {
    values
        .iter()
        .map(|value| value.as_i64().to_string())
        .collect::<Vec<_>>()
        .join(",")
}

fn path_argument(
    arguments: &mut impl Iterator<Item = std::ffi::OsString>,
    label: &str,
) -> Result<PathBuf, Box<dyn Error>> {
    arguments
        .next()
        .map(PathBuf::from)
        .ok_or_else(|| format!("missing {label}").into())
}

fn string_argument(
    arguments: &mut impl Iterator<Item = std::ffi::OsString>,
    label: &str,
) -> Result<String, Box<dyn Error>> {
    arguments
        .next()
        .and_then(|value| value.into_string().ok())
        .ok_or_else(|| format!("missing or non-Unicode {label}").into())
}

fn hex(value: [u8; 32]) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(64);
    for byte in value {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}

#[cfg(test)]
mod tests {
    use domain_ir::FontMetricEvidence;

    use super::*;

    #[test]
    fn calibration_guard_is_exact_and_rebinds_evidence() -> Result<(), Box<dyn Error>> {
        let mut measure = TableCellMeasure {
            master_cell_id: LogicalId::parse("cell-a")?,
            leading_margin: LengthMicrometers::from_raw(0),
            trailing_margin: LengthMicrometers::from_raw(0),
            unbreakable_content_width: LengthMicrometers::from_raw(49_392),
            preferred_content_width: LengthMicrometers::from_raw(49_392),
            line_height: LengthMicrometers::from_raw(4_586),
            font_metric_evidence: FontMetricEvidence {
                status: FontMetricStatus::Verified,
                profile_id: Some("base".to_owned()),
                source_sha256: Some("0".repeat(64)),
            },
        };
        apply_calibration_guard(&mut measure)?;
        assert_eq!(measure.unbreakable_content_width.as_i64(), 49_742);
        assert_eq!(measure.preferred_content_width.as_i64(), 49_742);
        assert_eq!(
            measure.font_metric_evidence.profile_id.as_deref(),
            Some(CALIBRATION_PROFILE_ID)
        );
        assert_eq!(
            measure.font_metric_evidence.source_sha256.as_deref(),
            Some(CALIBRATION_SOURCE_SHA256)
        );
        Ok(())
    }
}
