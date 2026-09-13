use std::collections::{BTreeMap, BTreeSet};
use std::env;
use std::fs;
use std::io::Cursor;
use std::path::Path;

use domain_ir::{
    CellCoordinate, FormulaAstDraft, FormulaCellDraft, FormulaLimitConfig, FormulaLimits,
    FormulaNumberFormat, LogicalId, TABLE_FORMULA_SCHEMA_VERSION, TABLE_GRID_SCHEMA_VERSION,
    TABLE_NUMBER_FORMAT_SCHEMA_VERSION, TABLE_THOUSANDS_SCHEMA_VERSION, TableCellSpan, TableGrid,
    TableGridDraft, TableGridLimits, TableNumberFormatBuilder, TableNumberFormatCellDraft,
    TableNumberFormatLimits, TableNumberFormatPlan, TableNumberFormatRequest,
    TableNumberFormatRequestDraft, TableNumberFormatState, TableNumberFormatStateDraft,
    TableThousandsBuilder, TableThousandsMode, TableThousandsRequest, TableThousandsRequestDraft,
};
use hwpx_package::{
    BoundedZipReader, PackageLimits, TABLE_NUMBER_FORMAT_HWPX_PROFILE_ID,
    TABLE_NUMBER_FORMAT_HWPX_SCHEMA_VERSION, TABLE_THOUSANDS_HWPX_SCHEMA_VERSION,
    TableFormulaHwpxLimits, TableNumberFormatHwpxLowerer, TableNumberFormatHwpxReadback,
    TableNumberFormatHwpxReader, TableNumberFormatHwpxRequest, TableNumberFormatHwpxRequestDraft,
    TableThousandsHwpxLowerer, TableThousandsHwpxReader, TableThousandsHwpxRequest,
    TableThousandsHwpxRequestDraft,
};
use serde_json::json;
use sha2::{Digest as _, Sha256};

const MAX_HWPX_BYTES: u64 = 8 * 1024 * 1024;

type AnyError = Box<dyn std::error::Error>;

struct SourcePackage {
    package_sha256: [u8; 32],
    section: Vec<u8>,
    raw_flow_sha256: [u8; 32],
    semantic_flow_sha256: [u8; 32],
    entry_paths: BTreeSet<String>,
}

struct OracleResult<'a> {
    baseline: &'a SourcePackage,
    ungrouped: &'a SourcePackage,
    grouped: &'a SourcePackage,
    baseline_readback: &'a TableNumberFormatHwpxReadback,
    ungrouped_readback: &'a TableNumberFormatHwpxReadback,
    grouped_readback: &'a TableNumberFormatHwpxReadback,
    flow: &'a str,
    grouped_edits: usize,
    ungrouped_edits: usize,
    general_grouping_edits: usize,
}

fn main() -> Result<(), AnyError> {
    let paths = env::args_os().skip(1).collect::<Vec<_>>();
    if paths.len() != 3 {
        return Err("expected baseline, ungrouped and grouped HWPX paths".into());
    }
    let baseline = read_package(Path::new(&paths[0]))?;
    let ungrouped = read_package(Path::new(&paths[1]))?;
    let grouped = read_package(Path::new(&paths[2]))?;
    assert_package_consistency(&baseline, &ungrouped, &grouped)?;

    let formula_limits = FormulaLimits::new(FormulaLimitConfig {
        rows: 16,
        columns: 16,
        ..FormulaLimitConfig::default()
    })?;
    let section_limits = TableFormulaHwpxLimits::default();
    let selected = selected_cells();
    let baseline_readback = readback(&baseline.section, &selected, section_limits, formula_limits)?;
    let ungrouped_readback = readback(
        &ungrouped.section,
        &selected,
        section_limits,
        formula_limits,
    )?;
    let grouped_readback = readback(&grouped.section, &selected, section_limits, formula_limits)?;
    assert_profiles(&baseline_readback, &ungrouped_readback, &grouped_readback)?;

    let flow = hex(baseline.semantic_flow_sha256);
    let (direct_grouped, grouped_edits) = apply_number_formats(
        &baseline.section,
        true,
        &flow,
        section_limits,
        formula_limits,
    )?;
    if direct_grouped != grouped.section {
        return Err("direct grouped number-format section does not match native output".into());
    }

    let (plain_general, general_grouping_edits) =
        remove_general_grouping(&baseline.section, &flow, section_limits, formula_limits)?;
    let (direct_ungrouped, ungrouped_edits) =
        apply_number_formats(&plain_general, false, &flow, section_limits, formula_limits)?;
    if direct_ungrouped != ungrouped.section {
        return Err("direct ungrouped number-format section does not match native output".into());
    }

    print_result(&OracleResult {
        baseline: &baseline,
        ungrouped: &ungrouped,
        grouped: &grouped,
        baseline_readback: &baseline_readback,
        ungrouped_readback: &ungrouped_readback,
        grouped_readback: &grouped_readback,
        flow: &flow,
        grouped_edits,
        ungrouped_edits,
        general_grouping_edits,
    })?;
    Ok(())
}

fn print_result(value: &OracleResult<'_>) -> Result<(), AnyError> {
    let result = json!({
        "schema_version": "hwpx-agent.p06-09-table-number-format-source-oracle/v1",
        "state": "pass",
        "profile_id": TABLE_NUMBER_FORMAT_HWPX_PROFILE_ID,
        "target": {
            "product": "Hancom Hangul 2020",
            "build": "11.0.0.9136",
            "architecture": "x86",
            "locale": "ko-KR"
        },
        "source": {
            "baseline_hwpx_sha256": hex(value.baseline.package_sha256),
            "ungrouped_hwpx_sha256": hex(value.ungrouped.package_sha256),
            "grouped_hwpx_sha256": hex(value.grouped.package_sha256),
            "baseline_section_sha256": hex(value.baseline_readback.section_sha256()),
            "ungrouped_section_sha256": hex(value.ungrouped_readback.section_sha256()),
            "grouped_section_sha256": hex(value.grouped_readback.section_sha256()),
            "baseline_state_sha256": hex(value.baseline_readback.selected_state_sha256()),
            "ungrouped_state_sha256": hex(value.ungrouped_readback.selected_state_sha256()),
            "grouped_state_sha256": hex(value.grouped_readback.selected_state_sha256()),
            "document_flow_sha256": value.flow,
            "baseline_raw_flow_sha256": hex(value.baseline.raw_flow_sha256),
            "ungrouped_raw_flow_sha256": hex(value.ungrouped.raw_flow_sha256),
            "grouped_raw_flow_sha256": hex(value.grouped.raw_flow_sha256),
            "grid_sha256": hex(value.baseline_readback.grid_sha256()),
            "entry_count": value.baseline.entry_paths.len(),
            "formula_fields": value.baseline_readback.formula_field_count()
        },
        "native_profile": {
            "result_formats": ["%g,", "%.0f,", "%.1f,", "%.2f,", "%.3f,", "%.4f,"],
            "baseline_general_count": 6,
            "fixed_number_count": 5,
            "ungrouped_count": 6,
            "grouped_count": 6,
            "formula_ast_preserved": true,
            "numeric_cache_preserved": true,
            "grid_preserved": true,
            "outside_owned_bytes_preserved": true
        },
        "direct_differential": {
            "grouped_section_exact_match": true,
            "ungrouped_section_exact_match": true,
            "grouped_number_format_modified_text_count": value.grouped_edits,
            "ungrouped_number_format_modified_text_count": value.ungrouped_edits,
            "auxiliary_general_grouping_modified_text_count": value.general_grouping_edits,
            "document_flow_preserved": true
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
            "percent_or_scientific_native_mapping": false,
            "non_integer_native_mapping": false,
            "other_pc_or_hancom_version": false,
            "p06_complete": false,
            "product_complete": false
        }
    });
    println!("{}", serde_json::to_string(&result)?);
    Ok(())
}

fn selected_cells() -> Vec<CellCoordinate> {
    (0..6)
        .map(|row| CellCoordinate { row, column: 2 })
        .collect()
}

fn assert_profiles(
    baseline: &TableNumberFormatHwpxReadback,
    ungrouped: &TableNumberFormatHwpxReadback,
    grouped: &TableNumberFormatHwpxReadback,
) -> Result<(), AnyError> {
    if baseline.profile_id() != TABLE_NUMBER_FORMAT_HWPX_PROFILE_ID
        || baseline.dimensions().rows != 6
        || baseline.dimensions().columns != 3
        || baseline.formula_field_count() != 6
        || baseline.selected_formulas().len() != 6
        || baseline.grid_sha256() != ungrouped.grid_sha256()
        || baseline.grid_sha256() != grouped.grid_sha256()
        || baseline.selected_native_grouping() != [true; 6]
        || ungrouped.selected_native_grouping() != [false; 6]
        || grouped.selected_native_grouping() != [true; 6]
    {
        return Err("unexpected native table-number-format profile".into());
    }
    for index in 0..6 {
        let before = &baseline.selected_formulas()[index];
        let plain = &ungrouped.selected_formulas()[index];
        let after = &grouped.selected_formulas()[index];
        if before.owner()
            != (CellCoordinate {
                row: u32::try_from(index)?,
                column: 2,
            })
            || before.ast() != plain.ast()
            || before.ast() != after.ast()
            || before.cache() != plain.cache()
            || before.cache() != after.cache()
            || before.number_format() != FormulaNumberFormat::General
        {
            return Err("native formula/cache preservation mismatch".into());
        }
        let expected = if index == 0 {
            FormulaNumberFormat::General
        } else {
            FormulaNumberFormat::Number {
                decimal_places: u8::try_from(index - 1)?,
                use_grouping: false,
            }
        };
        if plain.number_format() != expected {
            return Err("native ungrouped format mapping mismatch".into());
        }
        let expected = match expected {
            FormulaNumberFormat::Number { decimal_places, .. } => FormulaNumberFormat::Number {
                decimal_places,
                use_grouping: true,
            },
            value => value,
        };
        if after.number_format() != expected {
            return Err("native grouped format mapping mismatch".into());
        }
    }
    Ok(())
}

fn apply_number_formats(
    source: &[u8],
    use_grouping: bool,
    flow: &str,
    section_limits: TableFormulaHwpxLimits,
    formula_limits: FormulaLimits,
) -> Result<(Vec<u8>, usize), AnyError> {
    let mut section = source.to_vec();
    let mut edits = 0_usize;
    for row in 1..6 {
        let all = readback(&section, &selected_cells(), section_limits, formula_limits)?;
        let state = state_from_readback(&all, formula_limits)?;
        let coordinate = CellCoordinate { row, column: 2 };
        let target = FormulaNumberFormat::Number {
            decimal_places: u8::try_from(row - 1)?,
            use_grouping,
        };
        let plan = build_plan(&state, coordinate, target, flow, formula_limits)?;
        let selected = readback(&section, &[coordinate], section_limits, formula_limits)?;
        let request = build_hwpx_request(
            &section,
            &selected,
            &plan,
            flow,
            section_limits,
            formula_limits,
        )?;
        let (output, receipt) = TableNumberFormatHwpxLowerer::lower_in_section_with_receipt(
            &request,
            &section,
            &plan,
            flow,
            section_limits,
            TableNumberFormatLimits::default(),
            formula_limits,
        )?;
        edits = edits
            .checked_add(receipt.modified_text_count())
            .ok_or("edit count overflow")?;
        section = output;
    }
    Ok((section, edits))
}

fn remove_general_grouping(
    source: &[u8],
    flow: &str,
    section_limits: TableFormulaHwpxLimits,
    formula_limits: FormulaLimits,
) -> Result<(Vec<u8>, usize), AnyError> {
    let coordinate = CellCoordinate { row: 0, column: 2 };
    let readback = TableThousandsHwpxReader::read_selected_in_section(
        source,
        0,
        &[coordinate],
        section_limits,
        formula_limits,
    )?;
    let request = TableThousandsRequest::from_draft(
        TableThousandsRequestDraft {
            schema_version: TABLE_THOUSANDS_SCHEMA_VERSION.to_owned(),
            mode: TableThousandsMode::Remove,
            selected_cells: vec![coordinate],
        },
        readback.dimensions(),
        formula_limits,
    )?;
    let plan = TableThousandsBuilder::build(request, readback.selected_formulas(), formula_limits)?;
    let hwpx_request = TableThousandsHwpxRequest::from_draft(
        TableThousandsHwpxRequestDraft {
            schema_version: TABLE_THOUSANDS_HWPX_SCHEMA_VERSION.to_owned(),
            table_ordinal: 0,
            expected_section_sha256: hex(readback.section_sha256()),
            expected_source_state_sha256: hex(readback.selected_state_sha256()),
            expected_source_grid_sha256: hex(readback.grid_sha256()),
            expected_document_flow_sha256: flow.to_owned(),
            expected_plan_sha256: hex(plan.canonical_sha256(formula_limits)?),
        },
        source,
        &plan,
        flow,
        section_limits,
        formula_limits,
    )?;
    let (output, receipt) = TableThousandsHwpxLowerer::lower_in_section_with_receipt(
        &hwpx_request,
        source,
        &plan,
        flow,
        section_limits,
        formula_limits,
    )?;
    Ok((output, receipt.modified_text_count()))
}

fn state_from_readback(
    readback: &TableNumberFormatHwpxReadback,
    formula_limits: FormulaLimits,
) -> Result<TableNumberFormatState, AnyError> {
    let grid = grid(readback.dimensions().rows, readback.dimensions().columns)?;
    let formulas = readback
        .selected_formulas()
        .iter()
        .map(|formula| (formula.owner(), formula))
        .collect::<BTreeMap<_, _>>();
    let mut cells = Vec::new();
    for (index, span) in grid.master_cells().iter().enumerate() {
        let coordinate = CellCoordinate {
            row: span.row,
            column: span.column,
        };
        let formula = formulas.get(&coordinate).map(|formula| FormulaCellDraft {
            schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
            owner: formula.owner(),
            ast: FormulaAstDraft {
                schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
                expression: formula.ast().expression().clone(),
            },
            cache: formula.cache().clone(),
            number_format: formula.number_format(),
        });
        cells.push(TableNumberFormatCellDraft {
            master_cell_id: span.master_cell_id.clone(),
            coordinate,
            non_formula_payload_sha256: indexed_digest(index, b'1'),
            properties_sha256: indexed_digest(index, b'a'),
            formula,
        });
    }
    Ok(TableNumberFormatState::from_draft(
        TableNumberFormatStateDraft {
            schema_version: TABLE_NUMBER_FORMAT_SCHEMA_VERSION.to_owned(),
            table_id: LogicalId::parse("native-table")?,
            grid_sha256: hex(grid.canonical_sha256()?),
            table_properties_sha256: indexed_digest(0, b'f'),
            cells,
        },
        &grid,
        TableNumberFormatLimits::default(),
        formula_limits,
    )?)
}

fn build_plan(
    state: &TableNumberFormatState,
    coordinate: CellCoordinate,
    target: FormulaNumberFormat,
    flow: &str,
    formula_limits: FormulaLimits,
) -> Result<TableNumberFormatPlan, AnyError> {
    let dimensions = state
        .cells()
        .iter()
        .fold((0_u32, 0_u32), |(rows, columns), cell| {
            (
                rows.max(cell.coordinate().row + 1),
                columns.max(cell.coordinate().column + 1),
            )
        });
    let grid = grid(dimensions.0, dimensions.1)?;
    let limits = TableNumberFormatLimits::default();
    let request = TableNumberFormatRequest::from_draft(
        TableNumberFormatRequestDraft {
            schema_version: TABLE_NUMBER_FORMAT_SCHEMA_VERSION.to_owned(),
            table_id: state.table_id().clone(),
            selected_cells: vec![coordinate],
            target_format: target,
            expected_source_state_sha256: hex(state.canonical_sha256(limits)?),
            expected_document_flow_sha256: flow.to_owned(),
        },
        state,
        &grid,
        flow,
        limits,
        formula_limits,
    )?;
    Ok(TableNumberFormatBuilder::build(
        &request,
        state,
        &grid,
        flow,
        limits,
        formula_limits,
    )?)
}

fn build_hwpx_request(
    section: &[u8],
    source: &TableNumberFormatHwpxReadback,
    plan: &TableNumberFormatPlan,
    flow: &str,
    section_limits: TableFormulaHwpxLimits,
    formula_limits: FormulaLimits,
) -> Result<TableNumberFormatHwpxRequest, AnyError> {
    Ok(TableNumberFormatHwpxRequest::from_draft(
        TableNumberFormatHwpxRequestDraft {
            schema_version: TABLE_NUMBER_FORMAT_HWPX_SCHEMA_VERSION.to_owned(),
            table_ordinal: 0,
            expected_section_sha256: hex(source.section_sha256()),
            expected_source_state_sha256: hex(source.selected_state_sha256()),
            expected_source_grid_sha256: hex(source.grid_sha256()),
            expected_document_flow_sha256: flow.to_owned(),
            expected_plan_sha256: hex(plan.canonical_sha256(TableNumberFormatLimits::default())?),
        },
        section,
        plan,
        flow,
        section_limits,
        TableNumberFormatLimits::default(),
        formula_limits,
    )?)
}

fn grid(rows: u32, columns: u32) -> Result<TableGrid, AnyError> {
    let mut master_cells = Vec::new();
    for row in 0..rows {
        for column in 0..columns {
            master_cells.push(TableCellSpan {
                master_cell_id: LogicalId::parse(format!("cell-{row}-{column}"))?,
                row,
                column,
                row_span: 1,
                column_span: 1,
            });
        }
    }
    Ok(TableGrid::from_draft(
        TableGridDraft {
            schema_version: TABLE_GRID_SCHEMA_VERSION.to_owned(),
            rows,
            columns,
            master_cells,
        },
        TableGridLimits::default(),
    )?)
}

fn indexed_digest(index: usize, base: u8) -> String {
    let value = base.saturating_add(u8::try_from(index % 10).unwrap_or(0));
    format!("{value:02x}").repeat(32)
}

fn readback(
    section: &[u8],
    selected: &[CellCoordinate],
    section_limits: TableFormulaHwpxLimits,
    formula_limits: FormulaLimits,
) -> Result<TableNumberFormatHwpxReadback, AnyError> {
    Ok(TableNumberFormatHwpxReader::read_selected_in_section(
        section,
        0,
        selected,
        section_limits,
        formula_limits,
    )?)
}

fn assert_package_consistency(
    baseline: &SourcePackage,
    ungrouped: &SourcePackage,
    grouped: &SourcePackage,
) -> Result<(), AnyError> {
    if baseline.entry_paths != ungrouped.entry_paths || baseline.entry_paths != grouped.entry_paths
    {
        return Err("package entry set drift".into());
    }
    if baseline.semantic_flow_sha256 != ungrouped.semantic_flow_sha256
        || baseline.semantic_flow_sha256 != grouped.semantic_flow_sha256
    {
        return Err("semantic document flow drift".into());
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
        raw_flow_sha256: Sha256::digest(&flow).into(),
        semantic_flow_sha256: source_flow_digest(&flow)?,
        entry_paths,
    })
}

fn source_flow_digest(flow: &[u8]) -> Result<[u8; 32], AnyError> {
    let text = std::str::from_utf8(flow)?;
    let prefix = "<opf:meta name=\"ModifiedDate\" content=\"text\">";
    let suffix = "</opf:meta>";
    let start = text.find(prefix).ok_or("ModifiedDate missing")? + prefix.len();
    let end = text[start..]
        .find(suffix)
        .map(|offset| start + offset)
        .ok_or("ModifiedDate end missing")?;
    if text[end + suffix.len()..].contains(prefix) {
        return Err("duplicate ModifiedDate".into());
    }
    let mut canonical = String::with_capacity(text.len());
    canonical.push_str(&text[..start]);
    canonical.push_str("<save-time>");
    canonical.push_str(&text[end..]);
    let canonical = canonical.replace(
        "<opf:itemref idref=\"header\"/>",
        "<opf:itemref idref=\"header\" linear=\"yes\"/>",
    );
    Ok(Sha256::digest(canonical.as_bytes()).into())
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
