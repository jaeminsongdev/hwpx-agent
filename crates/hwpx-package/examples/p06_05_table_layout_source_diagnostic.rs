use std::env;
use std::error::Error;
use std::fs;
use std::io::Cursor;
use std::path::{Path, PathBuf};

use hwpx_package::{BoundedZipReader, PackageLimits, TableLayoutHwpxLimits, TableLayoutHwpxReader};
use sha2::{Digest as _, Sha256};

const MAX_FIXTURE_BYTES: u64 = 8 * 1024 * 1024;

fn main() -> Result<(), Box<dyn Error>> {
    let mut arguments = env::args_os();
    let _program = arguments.next();
    let input = arguments
        .next()
        .map(PathBuf::from)
        .ok_or("usage: p06_05_table_layout_source_diagnostic <input.hwpx>")?;
    if arguments.next().is_some() {
        return Err("exactly one input path is required".into());
    }
    let bytes = read_bounded_fixture(&input)?;
    let input_sha256 = hex(Sha256::digest(&bytes).into());
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let section = read_part(&mut reader, "Contents/section0.xml")?;
    let table_count =
        TableLayoutHwpxReader::count_in_section(&section, TableLayoutHwpxLimits::default())?;
    if table_count != 1 {
        return Err("diagnostic requires exactly one table".into());
    }
    let readback =
        TableLayoutHwpxReader::read_in_section(&section, 0, TableLayoutHwpxLimits::default())?;
    println!(
        "schema=hwpx-agent.p06-05-table-layout-source-diagnostic/v1 state=pass input_sha256={input_sha256} tables={table_count} rows={} columns={} cells={} width_hwpunit={} height_hwpunit={} inner_margin_hwpunit={},{},{},{} content_sha256={}",
        readback.rows,
        readback.columns,
        readback.cells.len(),
        readback.table_width_hwpunit,
        readback.table_height_hwpunit,
        readback.inner_margin.left_hwpunit,
        readback.inner_margin.right_hwpunit,
        readback.inner_margin.top_hwpunit,
        readback.inner_margin.bottom_hwpunit,
        hex(readback.content_sha256),
    );
    for (ordinal, cell) in readback.cells.iter().enumerate() {
        println!(
            "cell={ordinal} row={} column={} row_span={} column_span={} width_hwpunit={} height_hwpunit={}",
            cell.row,
            cell.column,
            cell.row_span,
            cell.column_span,
            cell.width_hwpunit,
            cell.height_hwpunit,
        );
    }
    Ok(())
}

fn read_part(
    reader: &mut BoundedZipReader<Cursor<Vec<u8>>>,
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

fn hex(value: [u8; 32]) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(64);
    for byte in value {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}
