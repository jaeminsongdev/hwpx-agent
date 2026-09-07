use std::{env, error::Error, fs, io::Cursor, io::Read as _};

use domain_ir::{FormulaCache, FormulaGridDimensions, FormulaLimits, FormulaValue};
use hwpx_package::{
    TABLE_FORMULA_HWPX_PROFILE_ID, TableFormulaHwpxLimits, TableFormulaHwpxLowerer,
    TableFormulaHwpxReader,
};
use serde_json::json;
use sha2::{Digest as _, Sha256};
use zip::ZipArchive;

const SECTION_PATH: &str = "Contents/section0.xml";
const MAX_SOURCE_BYTES: usize = 32 * 1024 * 1024;
const MAX_SECTION_BYTES: usize = 32 * 1024 * 1024;

fn main() -> Result<(), Box<dyn Error>> {
    let arguments: Vec<String> = env::args().collect();
    if arguments.len() != 3 {
        return Err("usage: p06_06_table_formula_source_adapter <source.hwpx> <sha256>".into());
    }
    let expected_source_sha256 = parse_sha256(&arguments[2])?;
    let source = fs::read(&arguments[1])?;
    if source.is_empty() || source.len() > MAX_SOURCE_BYTES {
        return Err("source size is outside the exact adapter bound".into());
    }
    let source_sha256: [u8; 32] = Sha256::digest(&source).into();
    if source_sha256 != expected_source_sha256 {
        return Err("source SHA-256 does not match the explicit lock".into());
    }

    let section = read_section(&source)?;
    let formula_limits = FormulaLimits::default();
    let limits = TableFormulaHwpxLimits::default();
    let readback = TableFormulaHwpxReader::read_in_section(&section, 0, limits, formula_limits)?;
    if readback.profile_id != TABLE_FORMULA_HWPX_PROFILE_ID
        || (readback.rows, readback.columns) != (1, 3)
        || (
            readback.formula.owner().row,
            readback.formula.owner().column,
        ) != (0, 2)
        || readback.formula.ast().canonical_formula(formula_limits)? != "SUM(A1:B1)"
    {
        return Err("actual source semantic readback drifted".into());
    }
    let FormulaCache::Unverified {
        value: FormulaValue::Decimal { value },
    } = readback.formula.cache()
    else {
        return Err("actual source cache provenance drifted".into());
    };
    if value.coefficient() != 42 || value.scale() != 0 {
        return Err("actual source cache value drifted".into());
    }

    let dimensions = FormulaGridDimensions {
        rows: readback.rows,
        columns: readback.columns,
    };
    let (lowered, receipt) = TableFormulaHwpxLowerer::lower_in_section_with_receipt(
        &section,
        0,
        &readback.formula,
        dimensions,
        limits,
        formula_limits,
    )?;
    if lowered != section || receipt.source_sha256 != receipt.output_sha256 {
        return Err("identity lowering did not preserve the exact section bytes".into());
    }

    let report = json!({
        "schema_version": "hwpx-agent.p06-06-source-adapter-check/1",
        "profile_id": TABLE_FORMULA_HWPX_PROFILE_ID,
        "source_sha256": hex(source_sha256),
        "section_sha256": hex(Sha256::digest(&section).into()),
        "formula_sha256": hex(receipt.target_formula_sha256),
        "unowned_sha256": hex(readback.unowned_sha256),
        "rows": readback.rows,
        "columns": readback.columns,
        "owner": {"row": readback.formula.owner().row, "column": readback.formula.owner().column},
        "formula_field_count": readback.formula_field_count,
        "cache_provenance": "unverified",
        "identity_lowering": "pass",
        "source_mutated": false,
        "raw_native_command_exposed": false
    });
    println!("{}", serde_json::to_string_pretty(&report)?);
    Ok(())
}

fn read_section(source: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    let mut archive = ZipArchive::new(Cursor::new(source))?;
    let entry = archive.by_name(SECTION_PATH)?;
    let declared = usize::try_from(entry.size()).map_err(|_| "section size overflow")?;
    if declared == 0 || declared > MAX_SECTION_BYTES {
        return Err("section size is outside the exact adapter bound".into());
    }
    let mut section = Vec::new();
    section.try_reserve_exact(declared)?;
    entry
        .take((MAX_SECTION_BYTES as u64) + 1)
        .read_to_end(&mut section)?;
    if section.len() != declared || section.len() > MAX_SECTION_BYTES {
        return Err("section stream size does not match its bound".into());
    }
    Ok(section)
}

fn parse_sha256(source: &str) -> Result<[u8; 32], Box<dyn Error>> {
    if source.len() != 64 || !source.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err("expected SHA-256 must be 64 hexadecimal characters".into());
    }
    let mut output = [0_u8; 32];
    for (index, byte) in output.iter_mut().enumerate() {
        *byte = u8::from_str_radix(&source[index * 2..index * 2 + 2], 16)?;
    }
    Ok(output)
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
