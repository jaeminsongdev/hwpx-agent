use std::collections::BTreeSet;
use std::env;
use std::fs;
use std::io::Cursor;
use std::path::Path;

use domain_ir::{
    CellCoordinate, FormulaLimitConfig, FormulaLimits, FormulaNumberFormat,
    TABLE_THOUSANDS_SCHEMA_VERSION, TableThousandsBuilder, TableThousandsMode, TableThousandsPlan,
    TableThousandsRequest, TableThousandsRequestDraft,
};
use hwpx_package::{
    BoundedZipReader, PackageLimits, TABLE_THOUSANDS_HWPX_PROFILE_ID,
    TABLE_THOUSANDS_HWPX_SCHEMA_VERSION, TableFormulaHwpxLimits, TableThousandsHwpxLowerer,
    TableThousandsHwpxReadback, TableThousandsHwpxReader, TableThousandsHwpxRequest,
    TableThousandsHwpxRequestDraft,
};
use serde_json::json;
use sha2::{Digest as _, Sha256};

const MAX_HWPX_BYTES: u64 = 8 * 1024 * 1024;
const OWNER: CellCoordinate = CellCoordinate { row: 0, column: 2 };

type AnyError = Box<dyn std::error::Error>;

struct SourcePackage {
    package_sha256: [u8; 32],
    section: Vec<u8>,
    flow_sha256: [u8; 32],
    entry_paths: BTreeSet<String>,
}

struct DirectDifferential {
    remove_modified_text_count: usize,
    add_modified_text_count: usize,
    document_flow_preserved: bool,
}

struct OutputPackageDigests {
    removed: [u8; 32],
    added: [u8; 32],
}

fn main() -> Result<(), AnyError> {
    let paths = env::args_os().skip(1).collect::<Vec<_>>();
    if paths.len() != 3 {
        return Err("expected baseline, removed and added HWPX paths".into());
    }
    let baseline = read_package(Path::new(&paths[0]))?;
    let removed = read_package(Path::new(&paths[1]))?;
    let added = read_package(Path::new(&paths[2]))?;
    assert_package_consistency(&baseline, &removed, &added)?;

    let limits = FormulaLimits::new(FormulaLimitConfig {
        rows: 16,
        columns: 16,
        ..FormulaLimitConfig::default()
    })?;
    let section_limits = TableFormulaHwpxLimits::default();
    let baseline_readback = readback(&baseline.section, section_limits, limits)?;
    let removed_readback = readback(&removed.section, section_limits, limits)?;
    let added_readback = readback(&added.section, section_limits, limits)?;
    assert_profile(&baseline_readback, true)?;
    assert_profile(&removed_readback, false)?;
    assert_profile(&added_readback, true)?;
    if baseline_readback.dimensions() != removed_readback.dimensions()
        || baseline_readback.dimensions() != added_readback.dimensions()
        || baseline_readback.grid_sha256() != removed_readback.grid_sha256()
        || baseline_readback.grid_sha256() != added_readback.grid_sha256()
        || baseline_readback.selected_formulas()[0].ast()
            != removed_readback.selected_formulas()[0].ast()
        || baseline_readback.selected_formulas()[0].ast()
            != added_readback.selected_formulas()[0].ast()
        || baseline_readback.selected_formulas()[0].cache()
            != removed_readback.selected_formulas()[0].cache()
        || baseline_readback.selected_formulas()[0].cache()
            != added_readback.selected_formulas()[0].cache()
        || baseline.section != added.section
    {
        return Err("native semantic preservation mismatch".into());
    }

    let flow = hex(baseline.flow_sha256);
    let remove_plan = build_plan(&baseline_readback, TableThousandsMode::Remove, limits)?;
    let remove_request = build_request(
        &baseline.section,
        &baseline_readback,
        &remove_plan,
        &flow,
        section_limits,
        limits,
    )?;
    let (direct_removed, remove_receipt) =
        TableThousandsHwpxLowerer::lower_in_section_with_receipt(
            &remove_request,
            &baseline.section,
            &remove_plan,
            &flow,
            section_limits,
            limits,
        )?;
    if direct_removed != removed.section {
        return Err("direct remove does not exactly match native output section".into());
    }

    let add_plan = build_plan(&removed_readback, TableThousandsMode::Add, limits)?;
    let add_request = build_request(
        &removed.section,
        &removed_readback,
        &add_plan,
        &flow,
        section_limits,
        limits,
    )?;
    let (direct_added, add_receipt) = TableThousandsHwpxLowerer::lower_in_section_with_receipt(
        &add_request,
        &removed.section,
        &add_plan,
        &flow,
        section_limits,
        limits,
    )?;
    if direct_added != added.section {
        return Err("direct add does not exactly match native output section".into());
    }

    print_result(
        &baseline,
        &baseline_readback,
        &removed_readback,
        &added_readback,
        &flow,
        &OutputPackageDigests {
            removed: removed.package_sha256,
            added: added.package_sha256,
        },
        &DirectDifferential {
            remove_modified_text_count: remove_receipt.modified_text_count(),
            add_modified_text_count: add_receipt.modified_text_count(),
            document_flow_preserved: remove_receipt.document_flow_preserved()
                && add_receipt.document_flow_preserved(),
        },
    )?;
    Ok(())
}

fn print_result(
    baseline: &SourcePackage,
    baseline_readback: &TableThousandsHwpxReadback,
    removed_readback: &TableThousandsHwpxReadback,
    added_readback: &TableThousandsHwpxReadback,
    flow: &str,
    output_packages: &OutputPackageDigests,
    direct: &DirectDifferential,
) -> Result<(), AnyError> {
    let result = json!({
        "schema_version": "hwpx-agent.p06-09-table-thousands-source-oracle/v1",
        "state": "pass",
        "profile_id": TABLE_THOUSANDS_HWPX_PROFILE_ID,
        "target": {
            "product": "Hancom Hangul 2020",
            "build": "11.0.0.9136",
            "architecture": "x86",
            "locale": "ko-KR"
        },
        "source": {
            "baseline_hwpx_sha256": hex(baseline.package_sha256),
            "removed_hwpx_sha256": hex(output_packages.removed),
            "added_hwpx_sha256": hex(output_packages.added),
            "baseline_section_sha256": hex(baseline_readback.section_sha256()),
            "removed_section_sha256": hex(removed_readback.section_sha256()),
            "added_section_sha256": hex(added_readback.section_sha256()),
            "baseline_state_sha256": hex(baseline_readback.selected_state_sha256()),
            "removed_state_sha256": hex(removed_readback.selected_state_sha256()),
            "added_state_sha256": hex(added_readback.selected_state_sha256()),
            "document_flow_sha256": flow,
            "grid_sha256": hex(baseline_readback.grid_sha256()),
            "entry_count": baseline.entry_paths.len(),
            "formula_fields": baseline_readback.formula_field_count()
        },
        "native_transition": {
            "baseline_grouping": true,
            "removed_grouping": false,
            "added_grouping": true,
            "formula_ast_preserved": true,
            "numeric_cache_preserved": true,
            "grid_preserved": true,
            "baseline_and_added_sections_equal": true
        },
        "direct_differential": {
            "remove_section_exact_match": true,
            "add_section_exact_match": true,
            "remove_modified_text_count": direct.remove_modified_text_count,
            "add_modified_text_count": direct.add_modified_text_count,
            "unowned_bytes_preserved": true,
            "document_flow_preserved": direct.document_flow_preserved
        },
        "privacy": {
            "absolute_paths": false,
            "raw_document_text": false,
            "raw_formula_or_command": false,
            "secrets": false
        },
        "not_claimed": {
            "direct_output_package_save_reopen": false,
            "direct_output_render": false,
            "automation_route_runtime": false,
            "arbitrary_document_compatibility": false,
            "other_pc_or_hancom_version": false,
            "p06_complete": false,
            "product_complete": false
        }
    });
    println!("{}", serde_json::to_string(&result)?);
    Ok(())
}

fn assert_package_consistency(
    baseline: &SourcePackage,
    removed: &SourcePackage,
    added: &SourcePackage,
) -> Result<(), AnyError> {
    if baseline.entry_paths != removed.entry_paths || baseline.entry_paths != added.entry_paths {
        return Err("package entry set drift".into());
    }
    if baseline.flow_sha256 != removed.flow_sha256 || baseline.flow_sha256 != added.flow_sha256 {
        return Err("document flow drift".into());
    }
    Ok(())
}

fn read_package(path: &Path) -> Result<SourcePackage, AnyError> {
    let metadata = fs::symlink_metadata(path)?;
    if !metadata.is_file()
        || metadata.file_type().is_symlink()
        || metadata.len() == 0
        || metadata.len() > MAX_HWPX_BYTES
    {
        return Err("input is not a bounded regular HWPX file".into());
    }
    let bytes = fs::read(path)?;
    let package_sha256 = Sha256::digest(&bytes).into();
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let mut section_index = None;
    let mut flow_index = None;
    let mut entry_paths = BTreeSet::new();
    for entry in reader.entries() {
        if !entry_paths.insert(entry.path.as_str().to_owned()) {
            return Err("duplicate package path".into());
        }
        match entry.path.as_str() {
            "Contents/section0.xml" if section_index.replace(entry.index).is_none() => {}
            "Contents/content.hpf" if flow_index.replace(entry.index).is_none() => {}
            "Contents/section0.xml" | "Contents/content.hpf" => {
                return Err("duplicate required package part".into());
            }
            _ => {}
        }
    }
    let section = reader.read_entry(section_index.ok_or("section0.xml missing")?)?;
    let flow = reader.read_entry(flow_index.ok_or("content.hpf missing")?)?;
    Ok(SourcePackage {
        package_sha256,
        section,
        flow_sha256: Sha256::digest(flow).into(),
        entry_paths,
    })
}

fn readback(
    section: &[u8],
    section_limits: TableFormulaHwpxLimits,
    formula_limits: FormulaLimits,
) -> Result<TableThousandsHwpxReadback, AnyError> {
    Ok(TableThousandsHwpxReader::read_selected_in_section(
        section,
        0,
        &[OWNER],
        section_limits,
        formula_limits,
    )?)
}

fn assert_profile(readback: &TableThousandsHwpxReadback, grouping: bool) -> Result<(), AnyError> {
    if readback.profile_id() != TABLE_THOUSANDS_HWPX_PROFILE_ID
        || readback.dimensions().rows != 1
        || readback.dimensions().columns != 3
        || readback.selected_formulas().len() != 1
        || readback.selected_formulas()[0].owner() != OWNER
        || readback.selected_formulas()[0].number_format()
            != (FormulaNumberFormat::Number {
                decimal_places: 0,
                use_grouping: grouping,
            })
    {
        return Err("unexpected native source profile".into());
    }
    Ok(())
}

fn build_plan(
    source: &TableThousandsHwpxReadback,
    mode: TableThousandsMode,
    limits: FormulaLimits,
) -> Result<TableThousandsPlan, AnyError> {
    let request = TableThousandsRequest::from_draft(
        TableThousandsRequestDraft {
            schema_version: TABLE_THOUSANDS_SCHEMA_VERSION.to_owned(),
            mode,
            selected_cells: vec![OWNER],
        },
        source.dimensions(),
        limits,
    )?;
    Ok(TableThousandsBuilder::build(
        request,
        source.selected_formulas(),
        limits,
    )?)
}

fn build_request(
    section: &[u8],
    source: &TableThousandsHwpxReadback,
    plan: &TableThousandsPlan,
    flow: &str,
    section_limits: TableFormulaHwpxLimits,
    formula_limits: FormulaLimits,
) -> Result<TableThousandsHwpxRequest, AnyError> {
    Ok(TableThousandsHwpxRequest::from_draft(
        TableThousandsHwpxRequestDraft {
            schema_version: TABLE_THOUSANDS_HWPX_SCHEMA_VERSION.to_owned(),
            table_ordinal: 0,
            expected_section_sha256: hex(source.section_sha256()),
            expected_source_state_sha256: hex(source.selected_state_sha256()),
            expected_source_grid_sha256: hex(source.grid_sha256()),
            expected_document_flow_sha256: flow.to_owned(),
            expected_plan_sha256: hex(plan.canonical_sha256(formula_limits)?),
        },
        section,
        plan,
        flow,
        section_limits,
        formula_limits,
    )?)
}

fn hex(bytes: impl AsRef<[u8]>) -> String {
    use std::fmt::Write as _;

    bytes
        .as_ref()
        .iter()
        .fold(String::new(), |mut output, byte| {
            let _ = write!(output, "{byte:02x}");
            output
        })
}
