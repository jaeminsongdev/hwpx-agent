use std::collections::BTreeMap;
use std::env;
use std::error::Error;
use std::fs::{self, OpenOptions};
use std::io::{Cursor, Write};
use std::path::{Path, PathBuf};

use domain_ir::{
    CellCoordinate, FormulaAst, FormulaAstDraft, FormulaCache, FormulaCachePolicy, FormulaCell,
    FormulaCellDraft, FormulaDecimal, FormulaGridDimensions, FormulaLimitConfig, FormulaLimits,
    FormulaNumberFormat, FormulaValue, LogicalId, TABLE_AUTO_FILL_SERIES_SCHEMA_VERSION,
    TABLE_FORMULA_SCHEMA_VERSION, TABLE_GRID_SCHEMA_VERSION, TABLE_NUMBER_FORMAT_SCHEMA_VERSION,
    TABLE_STYLE_DEFINITION_SCHEMA_VERSION, TABLE_STYLE_SCHEMA_VERSION,
    TABLE_THOUSANDS_SCHEMA_VERSION, TABLE_TRANSPOSE_SCHEMA_VERSION, TableAutoFillDefinition,
    TableAutoFillFormulaPolicy, TableAutoFillLimits, TableAutoFillNumber, TableAutoFillOrder,
    TableAutoFillRegion, TableAutoFillSeries, TableAutoFillSeriesDraft, TableAutoFillValue,
    TableBlankOrder, TableCellBorderState, TableCellSpan, TableFormulaMovePolicy, TableGrid,
    TableGridDraft, TableGridLimits, TableNumberFormatBuilder, TableNumberFormatCellDraft,
    TableNumberFormatLimits, TableNumberFormatPlan, TableNumberFormatRequest,
    TableNumberFormatRequestDraft, TableNumberFormatState, TableNumberFormatStateDraft,
    TableRulingLimits, TableSortAxis, TableSortDirection, TableSortKey, TableSortRegion,
    TableStyleBandPrecedence, TableStyleBanding, TableStyleBuilder, TableStyleCellDraft,
    TableStyleColumnEmphasis, TableStyleDefinition, TableStyleDefinitionDraft, TableStyleLimits,
    TableStyleMergedCellPolicy, TableStyleRegion, TableStyleRequest, TableStyleRequestDraft,
    TableStyleRule, TableTextCollation, TableThousandsBuilder, TableThousandsMode,
    TableThousandsRequest, TableThousandsRequestDraft, TableTransposeCellDraft,
    TableTransposeFormulaPolicy, TableTransposeRequestDraft,
};
use hwpx_package::{
    BoundedZipReader, CellMargins, CellProtection, CellTextDirection, CellVerticalAlignment,
    Compression, PackageLimits, TABLE_ABSOLUTE_REFERENCE_HWPX_SCHEMA_VERSION,
    TABLE_AUTO_FILL_HWPX_SCHEMA_VERSION, TABLE_NESTED_TABLE_HWPX_SCHEMA_VERSION,
    TABLE_NUMBER_FORMAT_HWPX_SCHEMA_VERSION, TABLE_SORT_HWPX_SCHEMA_VERSION,
    TABLE_THOUSANDS_HWPX_SCHEMA_VERSION, TABLE_TRANSPOSE_HWPX_SCHEMA_VERSION,
    TableAbsoluteReferenceHwpxBuilder, TableAbsoluteReferenceHwpxLimits,
    TableAbsoluteReferenceHwpxLowerer, TableAbsoluteReferenceHwpxReader,
    TableAbsoluteReferenceHwpxRequest, TableAbsoluteReferenceHwpxRequestDraft,
    TableAutoFillHwpxBuilder, TableAutoFillHwpxLimits, TableAutoFillHwpxLowerer,
    TableAutoFillHwpxReader, TableAutoFillHwpxRequest, TableAutoFillHwpxRequestDraft,
    TableNestedTableHwpxBuilder, TableNestedTableHwpxLimits, TableNestedTableHwpxLowerer,
    TableNestedTableHwpxReader, TableNestedTableHwpxRequest, TableNestedTableHwpxRequestDraft,
    TableNumberFormatHwpxLowerer, TableNumberFormatHwpxReadback, TableNumberFormatHwpxReader,
    TableNumberFormatHwpxRequest, TableNumberFormatHwpxRequestDraft, TablePropertiesHwpxBinding,
    TableRulingHwpxBinding, TableRulingHwpxCellBinding, TableSortHwpxBuilder, TableSortHwpxLimits,
    TableSortHwpxLowerer, TableSortHwpxReader, TableSortHwpxRequest, TableSortHwpxRequestDraft,
    TableStyleHwpxCellValue, TableStyleHwpxLimits, TableStyleHwpxLowerer,
    TableStyleHwpxPartBinding, TableStyleHwpxReadback, TableStyleHwpxReader,
    TableStyleHwpxValueCatalog, TableThousandsHwpxLowerer, TableThousandsHwpxReader,
    TableThousandsHwpxRequest, TableThousandsHwpxRequestDraft, TableTransposeHwpxBuilder,
    TableTransposeHwpxLimits, TableTransposeHwpxLowerer, TableTransposeHwpxReader,
    TableTransposeHwpxRequest, TableTransposeHwpxRequestDraft,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, DateTime, ZipWriter};

const MAX_FILE_BYTES: u64 = 16 * 1024 * 1024;
const MAX_OUTPUT_BYTES: u64 = 24 * 1024 * 1024;
const NORMALIZED_DEFLATE_LEVEL: i64 = 6;
const COMMON_SHA256: &str = "0459a05b8543edb2e05c9c0117f76df999c8543bad255d06d26d4b3b57388252";
const THOUSANDS_BASELINE_SHA256: &str =
    "8b125fd14e69612b7896f22f7a8e93180709ae41c675aba5166a03820aa1ff7c";
const THOUSANDS_REMOVED_SHA256: &str =
    "985e5a87f4396cc113203e00acae2b2868b515c409c07b51d167dc496081519a";
const THOUSANDS_ADDED_SHA256: &str =
    "15166fd74bc5f9cee21df4833b3d994e78edec2c700a4a612bc63e3be987a419";
const NUMBER_BASELINE_SHA256: &str =
    "9f862bb2772c95271d3e97089c3ca29b88aa138e7fae524e8461bcf77ddac042";
const NUMBER_UNGROUPED_SHA256: &str =
    "fa859aaff54cdc7faa8c5d55639040f0e6cc450691d61889356a59db4abbced9";
const NUMBER_GROUPED_SHA256: &str =
    "c5f0a1881f0c7d4b4fc0105bd76f3929a3f0b4d64da756dd124a4cd66d122027";

type AnyError = Box<dyn Error>;

#[derive(Debug)]
struct Arguments {
    common: PathBuf,
    thousands_baseline: PathBuf,
    thousands_removed: PathBuf,
    thousands_added: PathBuf,
    number_baseline: PathBuf,
    number_ungrouped: PathBuf,
    number_grouped: PathBuf,
    output_directory: PathBuf,
}

impl Arguments {
    fn parse() -> Result<Self, AnyError> {
        let mut values = BTreeMap::new();
        let mut input = env::args_os().skip(1);
        while let Some(key) = input.next() {
            let key = key.into_string().map_err(|_| "argument key is not UTF-8")?;
            let value = input.next().ok_or("argument value is missing")?;
            if !matches!(
                key.as_str(),
                "--common"
                    | "--thousands-baseline"
                    | "--thousands-removed"
                    | "--thousands-added"
                    | "--number-baseline"
                    | "--number-ungrouped"
                    | "--number-grouped"
                    | "--output-directory"
            ) || values.insert(key, value).is_some()
            {
                return Err("unknown or duplicate argument".into());
            }
        }
        if values.len() != 8 {
            return Err("all eight path arguments are required".into());
        }
        Ok(Self {
            common: take_path(&mut values, "--common")?,
            thousands_baseline: take_path(&mut values, "--thousands-baseline")?,
            thousands_removed: take_path(&mut values, "--thousands-removed")?,
            thousands_added: take_path(&mut values, "--thousands-added")?,
            number_baseline: take_path(&mut values, "--number-baseline")?,
            number_ungrouped: take_path(&mut values, "--number-ungrouped")?,
            number_grouped: take_path(&mut values, "--number-grouped")?,
            output_directory: take_path(&mut values, "--output-directory")?,
        })
    }
}

#[derive(Clone)]
struct PackageParts {
    bytes: Vec<u8>,
    header: Vec<u8>,
    section: Vec<u8>,
    flow: Vec<u8>,
}

#[derive(Serialize)]
struct Manifest {
    schema_version: &'static str,
    source_artifacts: Vec<SourceArtifact>,
    cases: Vec<ManifestCase>,
    actual_hangul_2020: bool,
    render: &'static str,
    automation: &'static str,
    differential: &'static str,
}

#[derive(Serialize)]
struct SourceArtifact {
    role: &'static str,
    path: String,
    sha256: &'static str,
}

#[derive(Serialize)]
struct ManifestCase {
    case_id: &'static str,
    feature_id: &'static str,
    capability_id: &'static str,
    adapter: &'static str,
    source_role: &'static str,
    file: &'static str,
    sha256: String,
    target_header_sha256: String,
    target_section_sha256: String,
    semantic_sha256: String,
    table_count: usize,
    formula_count: usize,
    primary_binding: Option<BindingEvidence>,
    secondary_binding: Option<BindingEvidence>,
    primary_table_ordinal: usize,
    secondary_table_ordinal: Option<usize>,
}

#[derive(Clone, Deserialize, Serialize)]
struct BindingEvidence {
    table_id: String,
    row_boundaries_hwpunit: Vec<u32>,
    column_boundaries_hwpunit: Vec<u32>,
    cells: Vec<CellBindingEvidence>,
}

#[derive(Clone, Deserialize, Serialize)]
struct CellBindingEvidence {
    master_cell_id: String,
    payload_block_ids: Vec<String>,
}

struct BuiltCase {
    metadata: CaseMetadata,
    package: Vec<u8>,
    header: Vec<u8>,
    section: Vec<u8>,
    semantic_sha256: String,
    table_count: usize,
    primary_binding: Option<TableRulingHwpxBinding>,
    secondary_binding: Option<TableRulingHwpxBinding>,
    primary_table_ordinal: usize,
    secondary_table_ordinal: Option<usize>,
}

#[derive(Clone, Copy)]
struct CaseMetadata {
    case_id: &'static str,
    feature_id: &'static str,
    capability_id: &'static str,
    adapter: &'static str,
    source_role: &'static str,
    file: &'static str,
}

fn main() -> Result<(), AnyError> {
    run(&Arguments::parse()?)
}

#[allow(clippy::too_many_lines)]
fn run(arguments: &Arguments) -> Result<(), AnyError> {
    if arguments.output_directory.exists() {
        return Err("output directory already exists".into());
    }
    let parent = arguments
        .output_directory
        .parent()
        .ok_or("output directory has no parent")?;
    if !parent.is_dir() {
        return Err("output parent is not an existing directory".into());
    }

    let common = read_package(&arguments.common, COMMON_SHA256)?;
    let thousands_baseline =
        read_package(&arguments.thousands_baseline, THOUSANDS_BASELINE_SHA256)?;
    let thousands_removed = read_package(&arguments.thousands_removed, THOUSANDS_REMOVED_SHA256)?;
    let thousands_added = read_package(&arguments.thousands_added, THOUSANDS_ADDED_SHA256)?;
    let number_baseline = read_package(&arguments.number_baseline, NUMBER_BASELINE_SHA256)?;
    let number_ungrouped = read_package(&arguments.number_ungrouped, NUMBER_UNGROUPED_SHA256)?;
    let number_grouped = read_package(&arguments.number_grouped, NUMBER_GROUPED_SHA256)?;

    let mut cases = Vec::new();
    cases.try_reserve_exact(10)?;
    cases.push(build_style_case(&common).map_err(|error| -> AnyError {
        format!("TABLE-020 target build failed: {error}").into()
    })?);
    cases.push(build_transpose_case(&common).map_err(|error| -> AnyError {
        format!("TABLE-021 target build failed: {error}").into()
    })?);
    cases.push(
        build_thousands_case(
            &thousands_removed,
            &thousands_added,
            TableThousandsMode::Add,
            metadata(
                "table-032-thousands-add",
                "TABLE-032",
                "table.thousands_add",
                "table_thousands_hwpx",
                "thousands_removed",
                "table-032-thousands-add.hwpx",
            ),
        )
        .map_err(|error| -> AnyError {
            format!("TABLE-032 target build failed: {error}").into()
        })?,
    );
    cases.push(
        build_thousands_case(
            &thousands_baseline,
            &thousands_removed,
            TableThousandsMode::Remove,
            metadata(
                "table-033-thousands-remove",
                "TABLE-033",
                "table.thousands_remove",
                "table_thousands_hwpx",
                "thousands_baseline",
                "table-033-thousands-remove.hwpx",
            ),
        )
        .map_err(|error| -> AnyError {
            format!("TABLE-033 target build failed: {error}").into()
        })?,
    );
    cases.push(
        build_number_format_case(&number_baseline, &number_ungrouped, &number_grouped).map_err(
            |error| -> AnyError { format!("TABLE-049 target build failed: {error}").into() },
        )?,
    );
    cases.push(build_nested_case(&common).map_err(|error| -> AnyError {
        format!("TABLE-054 target build failed: {error}").into()
    })?);
    cases.push(build_sort_case(&common).map_err(|error| -> AnyError {
        format!("TABLE-056 target build failed: {error}").into()
    })?);
    cases.push(
        build_auto_fill_case(&common, false).map_err(|error| -> AnyError {
            format!("TABLE-057 target build failed: {error}").into()
        })?,
    );
    cases.push(
        build_auto_fill_case(&common, true).map_err(|error| -> AnyError {
            format!("TABLE-058 target build failed: {error}").into()
        })?,
    );
    cases.push(
        build_absolute_reference_case(&common).map_err(|error| -> AnyError {
            format!("TABLE-060 target build failed: {error}").into()
        })?,
    );
    require_distinct_cases(&cases)?;

    for source in [
        (&arguments.common, COMMON_SHA256),
        (&arguments.thousands_baseline, THOUSANDS_BASELINE_SHA256),
        (&arguments.thousands_removed, THOUSANDS_REMOVED_SHA256),
        (&arguments.thousands_added, THOUSANDS_ADDED_SHA256),
        (&arguments.number_baseline, NUMBER_BASELINE_SHA256),
        (&arguments.number_ungrouped, NUMBER_UNGROUPED_SHA256),
        (&arguments.number_grouped, NUMBER_GROUPED_SHA256),
    ] {
        require_digest(
            &read_bounded_file(source.0, MAX_FILE_BYTES)?,
            source.1,
            "source recheck",
        )?;
    }

    fs::create_dir(&arguments.output_directory)?;
    let mut manifest_cases = Vec::new();
    manifest_cases.try_reserve_exact(cases.len())?;
    for case in cases {
        let path = arguments.output_directory.join(case.metadata.file);
        write_create_new(&path, &case.package)?;
        manifest_cases.push(ManifestCase {
            case_id: case.metadata.case_id,
            feature_id: case.metadata.feature_id,
            capability_id: case.metadata.capability_id,
            adapter: case.metadata.adapter,
            source_role: case.metadata.source_role,
            file: case.metadata.file,
            sha256: hex(Sha256::digest(&case.package)),
            target_header_sha256: hex(Sha256::digest(&case.header)),
            target_section_sha256: hex(Sha256::digest(&case.section)),
            semantic_sha256: case.semantic_sha256,
            table_count: case.table_count,
            formula_count: count_occurrences(&case.section, b"type=\"FORMULA\""),
            primary_binding: case.primary_binding.as_ref().map(binding_evidence),
            secondary_binding: case.secondary_binding.as_ref().map(binding_evidence),
            primary_table_ordinal: case.primary_table_ordinal,
            secondary_table_ordinal: case.secondary_table_ordinal,
        });
    }
    let manifest = Manifest {
        schema_version: "hwpx-agent.p06-09-table-remaining-target-fixture/v1",
        source_artifacts: vec![
            source_artifact("common", &arguments.common, COMMON_SHA256),
            source_artifact(
                "thousands_baseline",
                &arguments.thousands_baseline,
                THOUSANDS_BASELINE_SHA256,
            ),
            source_artifact(
                "thousands_removed",
                &arguments.thousands_removed,
                THOUSANDS_REMOVED_SHA256,
            ),
            source_artifact(
                "thousands_added",
                &arguments.thousands_added,
                THOUSANDS_ADDED_SHA256,
            ),
            source_artifact(
                "number_baseline",
                &arguments.number_baseline,
                NUMBER_BASELINE_SHA256,
            ),
            source_artifact(
                "number_ungrouped",
                &arguments.number_ungrouped,
                NUMBER_UNGROUPED_SHA256,
            ),
            source_artifact(
                "number_grouped",
                &arguments.number_grouped,
                NUMBER_GROUPED_SHA256,
            ),
        ],
        cases: manifest_cases,
        actual_hangul_2020: false,
        render: "not_run",
        automation: "not_run",
        differential: "not_run",
    };
    let mut bytes = serde_json::to_vec_pretty(&manifest)?;
    bytes.push(b'\n');
    write_create_new(
        &arguments.output_directory.join("fixture-manifest.json"),
        &bytes,
    )?;
    println!("{}", serde_json::to_string(&manifest)?);
    Ok(())
}

fn metadata(
    case_id: &'static str,
    feature_id: &'static str,
    capability_id: &'static str,
    adapter: &'static str,
    source_role: &'static str,
    file: &'static str,
) -> CaseMetadata {
    CaseMetadata {
        case_id,
        feature_id,
        capability_id,
        adapter,
        source_role,
        file,
    }
}

#[allow(clippy::too_many_lines)]
fn build_style_case(source_package: &PackageParts) -> Result<BuiltCase, AnyError> {
    let binding = common_binding()?;
    let properties_binding = TablePropertiesHwpxBinding {
        table: binding.clone(),
        diagonals: Vec::new(),
    };
    let source = TableStyleHwpxReader::read_existing(
        &source_package.header,
        &source_package.section,
        0,
        &properties_binding,
        TableStyleHwpxLimits::default(),
    )?;
    let mut whole = style_value(&source, &properties_binding, 0)?;
    whole.borders = TableCellBorderState {
        top_sha256: None,
        right_sha256: None,
        bottom_sha256: None,
        left_sha256: None,
    };
    whole.background_sha256 = None;
    whole.diagonal = None;
    whole.non_border.margins = Some(CellMargins {
        left: 90,
        right: 90,
        top: 60,
        bottom: 60,
    });
    whole.non_border.vertical_alignment = CellVerticalAlignment::Bottom;
    whole.non_border.text_direction = CellTextDirection::Horizontal;
    whole.non_border.protection = CellProtection::Editable;
    let mut header_style = whole.clone();
    header_style.non_border.margins = Some(CellMargins {
        left: 180,
        right: 180,
        top: 120,
        bottom: 120,
    });
    header_style.non_border.vertical_alignment = CellVerticalAlignment::Center;
    let whole_sha256 = whole.canonical_sha256()?;
    let header_sha256 = header_style.canonical_sha256()?;
    let definition = TableStyleDefinition::from_draft(
        TableStyleDefinitionDraft {
            schema_version: TABLE_STYLE_DEFINITION_SCHEMA_VERSION.to_owned(),
            style_id: id("remaining-target-style")?,
            table_properties_sha256: source.properties.state.table_properties_sha256().to_owned(),
            rules: vec![
                TableStyleRule {
                    region: TableStyleRegion::HeaderRows,
                    cell_style_sha256: header_sha256,
                },
                TableStyleRule {
                    region: TableStyleRegion::WholeTable,
                    cell_style_sha256: whole_sha256,
                },
            ],
        },
        TableStyleLimits::default(),
    )?;
    let request = style_request(&source, &definition)?;
    let plan = TableStyleBuilder::build(
        &request,
        &definition,
        &source.properties.grid,
        TableStyleLimits::default(),
    )?;
    let flow = flow_digest(&source_package.flow);
    let part = TableStyleHwpxPartBinding::from_readback(
        &source,
        &request,
        &definition,
        &plan,
        flow.clone(),
        TableStyleHwpxLimits::default(),
    )?;
    let output = TableStyleHwpxLowerer::lower_existing(
        &source_package.header,
        &source_package.section,
        0,
        &properties_binding,
        &part,
        &flow,
        &request,
        &definition,
        &plan,
        &TableStyleHwpxValueCatalog {
            table_values: Vec::new(),
            cell_styles: vec![whole, header_style],
            lines: Vec::new(),
            backgrounds: Vec::new(),
            border_fills: Vec::new(),
        },
        TableStyleHwpxLimits::default(),
    )?;
    built_case(
        source_package,
        output.header,
        output.section,
        hex(plan.canonical_sha256(TableStyleLimits::default())?),
        Some(output.binding.table),
        None,
        0,
        None,
        metadata(
            "table-020-style",
            "TABLE-020",
            "table.table_style",
            "table_style_hwpx",
            "common",
            "table-020-style.hwpx",
        ),
    )
}

fn style_value(
    source: &TableStyleHwpxReadback,
    binding: &TablePropertiesHwpxBinding,
    index: usize,
) -> Result<TableStyleHwpxCellValue, AnyError> {
    let cell = source
        .properties
        .state
        .cells()
        .get(index)
        .ok_or("style source cell is missing")?;
    let non_border = *source
        .properties
        .cell_values
        .get(index)
        .ok_or("style non-border value is missing")?;
    let diagonal = binding
        .diagonals
        .iter()
        .find(|value| value.master_cell_id == cell.master_cell_id)
        .map(|value| value.value.clone());
    Ok(TableStyleHwpxCellValue {
        non_border,
        borders: cell.properties.borders.clone(),
        background_sha256: cell.properties.background_sha256.clone(),
        diagonal,
    })
}

fn style_request(
    source: &TableStyleHwpxReadback,
    definition: &TableStyleDefinition,
) -> Result<TableStyleRequest, AnyError> {
    let mut cells = Vec::new();
    for ((cell, span), style_sha256) in source
        .properties
        .state
        .cells()
        .iter()
        .zip(source.properties.grid.master_cells())
        .zip(&source.cell_style_sha256)
    {
        cells.push(TableStyleCellDraft {
            master_cell_id: cell.master_cell_id.clone(),
            coordinate: CellCoordinate {
                row: span.row,
                column: span.column,
            },
            payload_sha256: cell.payload_sha256.clone(),
            formula_sha256: cell.formula_sha256.clone(),
            current_style_sha256: style_sha256.clone(),
        });
    }
    Ok(TableStyleRequest::from_draft(
        TableStyleRequestDraft {
            schema_version: TABLE_STYLE_SCHEMA_VERSION.to_owned(),
            table_id: source.properties.state.table_id().clone(),
            style_id: definition.style_id().clone(),
            style_definition_sha256: hex(definition.canonical_sha256(TableStyleLimits::default())?),
            current_table_properties_sha256: source
                .properties
                .state
                .table_properties_sha256()
                .to_owned(),
            header_rows: 1,
            footer_rows: 0,
            column_emphasis: TableStyleColumnEmphasis::None,
            banding: TableStyleBanding::Rows,
            row_band_size: 1,
            column_band_size: 1,
            band_precedence: TableStyleBandPrecedence::RowsFirst,
            merged_cell_policy: TableStyleMergedCellPolicy::UseMasterAnchor,
            cells,
        },
        definition,
        &source.properties.grid,
        TableStyleLimits::default(),
    )?)
}

fn build_transpose_case(source_package: &PackageParts) -> Result<BuiltCase, AnyError> {
    let binding = common_binding()?;
    let limits = TableTransposeHwpxLimits::default();
    let source = TableTransposeHwpxReader::read_existing(
        &source_package.header,
        &source_package.section,
        0,
        &binding,
        limits,
    )?;
    let before = flow_digest(&source_package.flow);
    let after = target_flow(&before, "TABLE-021");
    let cells = source
        .ruling
        .state
        .cells()
        .iter()
        .map(|cell| {
            Ok(TableTransposeCellDraft {
                master_cell_id: cell.master_cell_id().clone(),
                coordinate: cell.coordinate(),
                payload_sha256: component_digest(cell.payload())?,
                style_sha256: component_digest(cell.properties())?,
                formula: None,
            })
        })
        .collect::<Result<Vec<_>, AnyError>>()?;
    let request = TableTransposeHwpxRequest::from_draft(
        TableTransposeHwpxRequestDraft {
            schema_version: TABLE_TRANSPOSE_HWPX_SCHEMA_VERSION.to_owned(),
            table_ordinal: 0,
            expected_header_sha256: hex(source.ruling.header_sha256),
            expected_section_sha256: hex(source.ruling.section_sha256),
            expected_source_state_sha256: hex(source
                .ruling
                .state
                .canonical_sha256(TableRulingLimits::default())?),
            expected_source_grid_sha256: hex(source.ruling.grid.canonical_sha256()?),
            expected_document_flow_sha256: before.clone(),
            target_document_flow_sha256: after,
            transpose: TableTransposeRequestDraft {
                schema_version: TABLE_TRANSPOSE_SCHEMA_VERSION.to_owned(),
                table_id: source.ruling.state.table_id().clone(),
                table_properties_sha256: source.ruling.state.table_properties_sha256().to_owned(),
                formula_policy: TableTransposeFormulaPolicy::Reject,
                cells,
            },
        },
        &source,
        &before,
        limits,
    )?;
    let plan = TableTransposeHwpxBuilder::build(&request, &source, &before, limits)?;
    let output = TableTransposeHwpxLowerer::lower_existing(
        &source_package.header,
        &source_package.section,
        &binding,
        &before,
        &request,
        &plan,
        limits,
    )?;
    built_case(
        source_package,
        output.header,
        output.section,
        hex(plan.canonical_sha256(limits)?),
        Some(output.binding),
        None,
        0,
        None,
        metadata(
            "table-021-transpose",
            "TABLE-021",
            "table.transpose",
            "table_transpose_hwpx",
            "common",
            "table-021-transpose.hwpx",
        ),
    )
}

fn build_thousands_case(
    source_package: &PackageParts,
    native_target: &PackageParts,
    mode: TableThousandsMode,
    metadata: CaseMetadata,
) -> Result<BuiltCase, AnyError> {
    let formula_limits = formula_limits()?;
    let section_limits = hwpx_package::TableFormulaHwpxLimits::default();
    let owner = CellCoordinate { row: 0, column: 2 };
    let source = TableThousandsHwpxReader::read_selected_in_section(
        &source_package.section,
        0,
        &[owner],
        section_limits,
        formula_limits,
    )?;
    let request = TableThousandsRequest::from_draft(
        TableThousandsRequestDraft {
            schema_version: TABLE_THOUSANDS_SCHEMA_VERSION.to_owned(),
            mode,
            selected_cells: vec![owner],
        },
        source.dimensions(),
        formula_limits,
    )?;
    let plan = TableThousandsBuilder::build(request, source.selected_formulas(), formula_limits)?;
    let flow = flow_digest(&source_package.flow);
    let hwpx_request = TableThousandsHwpxRequest::from_draft(
        TableThousandsHwpxRequestDraft {
            schema_version: TABLE_THOUSANDS_HWPX_SCHEMA_VERSION.to_owned(),
            table_ordinal: 0,
            expected_section_sha256: hex(source.section_sha256()),
            expected_source_state_sha256: hex(source.selected_state_sha256()),
            expected_source_grid_sha256: hex(source.grid_sha256()),
            expected_document_flow_sha256: flow.clone(),
            expected_plan_sha256: hex(plan.canonical_sha256(formula_limits)?),
        },
        &source_package.section,
        &plan,
        &flow,
        section_limits,
        formula_limits,
    )?;
    let (section, _) = TableThousandsHwpxLowerer::lower_in_section_with_receipt(
        &hwpx_request,
        &source_package.section,
        &plan,
        &flow,
        section_limits,
        formula_limits,
    )?;
    if section != native_target.section {
        return Err("thousands target differs from exact native target section".into());
    }
    built_case(
        source_package,
        source_package.header.clone(),
        section,
        hex(plan.canonical_sha256(formula_limits)?),
        None,
        None,
        0,
        None,
        metadata,
    )
}

fn build_number_format_case(
    source_package: &PackageParts,
    native_ungrouped: &PackageParts,
    native_grouped: &PackageParts,
) -> Result<BuiltCase, AnyError> {
    let formula_limits = formula_limits()?;
    let section_limits = hwpx_package::TableFormulaHwpxLimits::default();
    let flow = hex(semantic_flow_digest(&source_package.flow)?);
    let (section, semantic_sha256) = apply_number_formats(
        &source_package.section,
        true,
        &flow,
        section_limits,
        formula_limits,
    )?;
    if section != native_grouped.section {
        return Err("number-format target differs from exact native grouped section".into());
    }
    let (plain_general, _) = remove_general_grouping(
        &source_package.section,
        &flow,
        section_limits,
        formula_limits,
    )?;
    let (ungrouped, _) =
        apply_number_formats(&plain_general, false, &flow, section_limits, formula_limits)?;
    if ungrouped != native_ungrouped.section {
        return Err("number-format ungrouped control differs from native section".into());
    }
    built_case(
        source_package,
        source_package.header.clone(),
        section,
        semantic_sha256,
        None,
        None,
        0,
        None,
        metadata(
            "table-049-number-format",
            "TABLE-049",
            "table.number_format",
            "table_number_format_hwpx",
            "number_baseline",
            "table-049-number-format.hwpx",
        ),
    )
}

fn apply_number_formats(
    source: &[u8],
    use_grouping: bool,
    flow: &str,
    section_limits: hwpx_package::TableFormulaHwpxLimits,
    formula_limits: FormulaLimits,
) -> Result<(Vec<u8>, String), AnyError> {
    let mut section = source.to_vec();
    let mut plan_sha256s = Vec::new();
    plan_sha256s.try_reserve_exact(5)?;
    for row in 1..6 {
        let all = number_readback(
            &section,
            &number_selected_cells(),
            section_limits,
            formula_limits,
        )?;
        let state = number_state_from_readback(&all, formula_limits)?;
        let coordinate = CellCoordinate { row, column: 2 };
        let plan = number_plan(
            &state,
            coordinate,
            FormulaNumberFormat::Number {
                decimal_places: u8::try_from(row - 1)?,
                use_grouping,
            },
            flow,
            formula_limits,
        )?;
        let selected = number_readback(&section, &[coordinate], section_limits, formula_limits)?;
        let request = number_hwpx_request(
            &section,
            &selected,
            &plan,
            flow,
            section_limits,
            formula_limits,
        )?;
        let (output, _) = TableNumberFormatHwpxLowerer::lower_in_section_with_receipt(
            &request,
            &section,
            &plan,
            flow,
            section_limits,
            TableNumberFormatLimits::default(),
            formula_limits,
        )?;
        plan_sha256s.push(hex(
            plan.canonical_sha256(TableNumberFormatLimits::default())?
        ));
        section = output;
    }
    if plan_sha256s.len() != 5 {
        return Err("number-format target did not produce all five plans".into());
    }
    Ok((section, component_digest(&plan_sha256s)?))
}

fn remove_general_grouping(
    source: &[u8],
    flow: &str,
    section_limits: hwpx_package::TableFormulaHwpxLimits,
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

fn number_state_from_readback(
    readback: &TableNumberFormatHwpxReadback,
    formula_limits: FormulaLimits,
) -> Result<TableNumberFormatState, AnyError> {
    let grid = formula_grid(readback.dimensions().rows, readback.dimensions().columns)?;
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
            non_formula_payload_sha256: indexed_digest(index, b'1')?,
            properties_sha256: indexed_digest(index, b'a')?,
            formula,
        });
    }
    Ok(TableNumberFormatState::from_draft(
        TableNumberFormatStateDraft {
            schema_version: TABLE_NUMBER_FORMAT_SCHEMA_VERSION.to_owned(),
            table_id: id("remaining-native-number-table")?,
            grid_sha256: hex(grid.canonical_sha256()?),
            table_properties_sha256: indexed_digest(0, b'f')?,
            cells,
        },
        &grid,
        TableNumberFormatLimits::default(),
        formula_limits,
    )?)
}

fn number_plan(
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
    let grid = formula_grid(dimensions.0, dimensions.1)?;
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

fn number_hwpx_request(
    section: &[u8],
    source: &TableNumberFormatHwpxReadback,
    plan: &TableNumberFormatPlan,
    flow: &str,
    section_limits: hwpx_package::TableFormulaHwpxLimits,
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

fn number_readback(
    section: &[u8],
    selected: &[CellCoordinate],
    section_limits: hwpx_package::TableFormulaHwpxLimits,
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

fn number_selected_cells() -> Vec<CellCoordinate> {
    (0..6)
        .map(|row| CellCoordinate { row, column: 2 })
        .collect()
}

fn build_nested_case(source_package: &PackageParts) -> Result<BuiltCase, AnyError> {
    let parent_binding = common_binding()?;
    let template_binding = nested_template_binding()?;
    let template = nested_template_section();
    let limits = TableNestedTableHwpxLimits::default();
    let source = TableNestedTableHwpxReader::read_context(
        &source_package.header,
        &source_package.section,
        0,
        CellCoordinate { row: 1, column: 0 },
        0,
        &parent_binding,
        &template,
        0,
        &template_binding,
        limits,
    )?;
    let before = flow_digest(&source_package.flow);
    let after = target_flow(&before, "TABLE-054");
    let request = TableNestedTableHwpxRequest::from_draft(
        TableNestedTableHwpxRequestDraft {
            schema_version: TABLE_NESTED_TABLE_HWPX_SCHEMA_VERSION.to_owned(),
            capability_id: "table.nested_table".to_owned(),
            parent_table_ordinal: source.parent_table_ordinal,
            parent_cell: source.parent_cell,
            placeholder_paragraph_ordinal: source.placeholder_paragraph_ordinal,
            template_table_ordinal: source.template_table_ordinal,
            nested_payload_block_id: id("remaining-target-nested-payload")?,
            expected_header_sha256: hex(source.header_sha256),
            expected_section_sha256: hex(source.section_sha256),
            expected_parent_state_sha256: hex(source
                .parent
                .state
                .canonical_sha256(limits.ruling.ruling)?),
            expected_parent_grid_sha256: hex(source.parent.grid.canonical_sha256()?),
            expected_parent_table_content_sha256: hex(source.parent.table_content_sha256),
            expected_template_section_sha256: hex(source.template_section_sha256),
            expected_template_state_sha256: hex(source
                .template
                .state
                .canonical_sha256(limits.ruling.ruling)?),
            expected_template_grid_sha256: hex(source.template.grid.canonical_sha256()?),
            expected_template_table_content_sha256: hex(source.template.table_content_sha256),
            expected_insertion_context_sha256: source.insertion_context_sha256.clone(),
            expected_nested_wrapper_sha256: source.nested_wrapper_sha256.clone(),
            expected_source_table_count: source.source_table_count,
            expected_document_flow_sha256: before.clone(),
            target_document_flow_sha256: after,
        },
        &source,
        &before,
        limits,
    )?;
    let plan = TableNestedTableHwpxBuilder::build(&request, &source, &before, limits)?;
    let output = TableNestedTableHwpxLowerer::lower_at_cell_placeholder(
        &source_package.header,
        &source_package.section,
        &parent_binding,
        &template,
        &template_binding,
        &before,
        &request,
        &plan,
        limits,
    )?;
    built_case(
        source_package,
        output.header,
        output.section,
        hex(plan.canonical_sha256(limits)?),
        Some(output.parent_binding),
        Some(output.nested_binding),
        output.parent_table_ordinal,
        Some(output.nested_table_ordinal),
        metadata(
            "table-054-nested-table",
            "TABLE-054",
            "table.nested_table",
            "table_nested_table_hwpx",
            "common_envelope_with_inline_nested_template",
            "table-054-nested-table.hwpx",
        ),
    )
}

fn build_sort_case(source_package: &PackageParts) -> Result<BuiltCase, AnyError> {
    let binding = common_binding()?;
    let limits = TableSortHwpxLimits::default();
    let source = TableSortHwpxReader::read_context(
        &source_package.header,
        &source_package.section,
        0,
        &binding,
        limits,
    )?;
    let before = flow_digest(&source_package.flow);
    let after = target_flow(&before, "TABLE-056");
    let request = TableSortHwpxRequest::from_draft(
        TableSortHwpxRequestDraft {
            schema_version: TABLE_SORT_HWPX_SCHEMA_VERSION.to_owned(),
            table_ordinal: 0,
            region: TableSortRegion {
                start: CellCoordinate { row: 0, column: 0 },
                end: CellCoordinate { row: 3, column: 2 },
            },
            axis: TableSortAxis::Rows,
            keys: vec![TableSortKey {
                offset: 0,
                direction: TableSortDirection::Descending,
                blank_order: TableBlankOrder::Last,
                text_collation: TableTextCollation::Binary,
            }],
            formula_move_policy: TableFormulaMovePolicy::Reject,
            expected_header_sha256: hex(source.header_sha256),
            expected_section_sha256: hex(source.section_sha256),
            expected_table_content_sha256: hex(source.ruling.table_content_sha256),
            expected_source_state_sha256: hex(source
                .ruling
                .state
                .canonical_sha256(limits.native.ruling)?),
            expected_source_grid_sha256: hex(source.ruling.grid.canonical_sha256()?),
            expected_text_grid_sha256: hex(source.text_grid_sha256),
            expected_pagination_policy_sha256: hex(source.pagination_policy_sha256),
            expected_source_table_count: source.source_table_count,
            expected_document_flow_sha256: before.clone(),
            target_document_flow_sha256: after,
        },
        &source,
        &before,
        limits,
    )?;
    let plan = TableSortHwpxBuilder::build(&request, &source, &before, limits)?;
    let output = TableSortHwpxLowerer::lower(
        &source_package.header,
        &source_package.section,
        &binding,
        &before,
        &request,
        &plan,
        limits,
    )?;
    built_case(
        source_package,
        output.header,
        output.section,
        hex(plan.canonical_sha256(limits)?),
        Some(output.binding),
        None,
        0,
        None,
        metadata(
            "table-056-sort",
            "TABLE-056",
            "table.sort_cells",
            "table_sort_hwpx",
            "common",
            "table-056-sort.hwpx",
        ),
    )
}

#[allow(clippy::too_many_lines)]
fn build_auto_fill_case(
    source_package: &PackageParts,
    linear: bool,
) -> Result<BuiltCase, AnyError> {
    let binding = auto_fill_binding()?;
    let source_section = auto_fill_source_section();
    let limits = TableAutoFillHwpxLimits::default();
    let region = TableAutoFillRegion {
        start: CellCoordinate { row: 1, column: 0 },
        end: CellCoordinate { row: 1, column: 2 },
    };
    let source = TableAutoFillHwpxReader::read_context(
        &source_package.header,
        &source_section,
        0,
        region,
        &binding,
        limits,
    )?;
    let (feature_id, capability_id, case_id, file, definition) = if linear {
        (
            "TABLE-058",
            "table.auto_fill_series",
            "table-058-auto-fill-series",
            "table-058-auto-fill-series.hwpx",
            TableAutoFillDefinition::LinearNumber {
                start: TableAutoFillNumber {
                    coefficient: 10,
                    scale: 0,
                },
                step: TableAutoFillNumber {
                    coefficient: 5,
                    scale: 0,
                },
            },
        )
    } else {
        (
            "TABLE-057",
            "table.auto_fill",
            "table-057-auto-fill",
            "table-057-auto-fill.hwpx",
            TableAutoFillDefinition::ExplicitCycle {
                items: vec![
                    TableAutoFillValue::Text {
                        value: "Alpha".to_owned(),
                    },
                    TableAutoFillValue::Boolean { value: true },
                    TableAutoFillValue::Decimal {
                        coefficient: 125,
                        scale: 2,
                    },
                ],
            },
        )
    };
    let series = TableAutoFillSeries::from_draft(
        TableAutoFillSeriesDraft {
            schema_version: TABLE_AUTO_FILL_SERIES_SCHEMA_VERSION.to_owned(),
            series_id: id(&format!("remaining-{feature_id}-series"))?,
            definition,
        },
        TableAutoFillLimits::default(),
    )?;
    let before = flow_digest(&source_package.flow);
    let after = target_flow(&before, feature_id);
    let target_ids = (0..3)
        .map(|column| id(&format!("remaining-{feature_id}-payload-{column}")))
        .map(|value| value.map(Some))
        .collect::<Result<Vec<_>, _>>()?;
    let request = TableAutoFillHwpxRequest::from_draft(
        TableAutoFillHwpxRequestDraft {
            schema_version: TABLE_AUTO_FILL_HWPX_SCHEMA_VERSION.to_owned(),
            table_ordinal: 0,
            region,
            order: TableAutoFillOrder::RowMajor,
            start_index: 0,
            formula_policy: TableAutoFillFormulaPolicy::Reject,
            expected_header_sha256: hex(source.header_sha256),
            expected_section_sha256: hex(source.section_sha256),
            expected_table_content_sha256: hex(source.ruling.table_content_sha256),
            expected_source_state_sha256: hex(source
                .ruling
                .state
                .canonical_sha256(limits.native.ruling)?),
            expected_source_grid_sha256: hex(source.ruling.grid.canonical_sha256()?),
            expected_scalar_state_sha256: hex(source.scalar_state_sha256),
            expected_pagination_policy_sha256: hex(source.pagination_policy_sha256),
            expected_series_sha256: hex(series.canonical_sha256(limits.auto_fill)?),
            expected_source_table_count: source.source_table_count,
            expected_document_flow_sha256: before.clone(),
            target_document_flow_sha256: after,
            target_payload_block_ids: target_ids,
        },
        &series,
        &source,
        &before,
        limits,
    )?;
    let plan = TableAutoFillHwpxBuilder::build(&request, &series, &source, &before, limits)?;
    let output = TableAutoFillHwpxLowerer::lower(
        &source_package.header,
        &source_section,
        &binding,
        &before,
        &series,
        &request,
        &plan,
        limits,
    )?;
    built_case(
        source_package,
        output.header,
        output.section,
        hex(plan.canonical_sha256(limits)?),
        Some(output.binding),
        None,
        0,
        None,
        metadata(
            case_id,
            feature_id,
            capability_id,
            "table_auto_fill_hwpx",
            "common_envelope_with_inline_auto_fill_section",
            file,
        ),
    )
}

fn build_absolute_reference_case(source_package: &PackageParts) -> Result<BuiltCase, AnyError> {
    let limits = absolute_limits()?;
    let section = absolute_source_section();
    let owner = CellCoordinate { row: 1, column: 2 };
    let source = TableAbsoluteReferenceHwpxReader::read_context(
        &source_package.header,
        &section,
        0,
        owner,
        limits,
    )?;
    let target = absolute_formula("SUM($A2:B$2)", absolute_cache(12))?;
    let before = flow_digest(&source_package.flow);
    let after = target_flow(&before, "TABLE-060");
    let request = TableAbsoluteReferenceHwpxRequest::from_draft(
        TableAbsoluteReferenceHwpxRequestDraft {
            schema_version: TABLE_ABSOLUTE_REFERENCE_HWPX_SCHEMA_VERSION.to_owned(),
            capability_id: "table.formula_absolute_ref".to_owned(),
            table_ordinal: 0,
            owner,
            recalculate: false,
            cache_policy: FormulaCachePolicy::Preserve,
            target_formula: formula_draft(&target),
            expected_header_sha256: hex(source.header_sha256),
            expected_section_sha256: hex(source.section_sha256),
            expected_table_content_sha256: hex(source.table_content_sha256),
            expected_source_formula_sha256: hex(source.selected_formula_sha256),
            expected_selected_unowned_sha256: hex(source.selected_unowned_sha256),
            expected_pagination_policy_sha256: hex(source.pagination_policy_sha256),
            expected_source_table_count: source.source_table_count,
            expected_formula_field_count: source.formula_field_count,
            expected_document_flow_sha256: before.clone(),
            target_document_flow_sha256: after,
        },
        &source,
        &before,
        limits,
    )?;
    let plan = TableAbsoluteReferenceHwpxBuilder::build(&request, &source, &before, limits)?;
    let output = TableAbsoluteReferenceHwpxLowerer::lower(
        &source_package.header,
        &section,
        &before,
        &request,
        &plan,
        limits,
    )?;
    built_case(
        source_package,
        output.header,
        output.section,
        hex(plan.canonical_sha256(limits)?),
        None,
        None,
        0,
        None,
        metadata(
            "table-060-absolute-reference",
            "TABLE-060",
            "table.formula_absolute_ref",
            "table_absolute_reference_hwpx",
            "common_envelope_with_inline_absolute_formula_section",
            "table-060-absolute-reference.hwpx",
        ),
    )
}

#[allow(clippy::too_many_arguments)]
fn built_case(
    source_package: &PackageParts,
    header: Vec<u8>,
    section: Vec<u8>,
    semantic_sha256: String,
    primary_binding: Option<TableRulingHwpxBinding>,
    secondary_binding: Option<TableRulingHwpxBinding>,
    primary_table_ordinal: usize,
    secondary_table_ordinal: Option<usize>,
    metadata: CaseMetadata,
) -> Result<BuiltCase, AnyError> {
    let package = replace_parts(&source_package.bytes, &header, &section)?;
    Ok(BuiltCase {
        metadata,
        package,
        header,
        section,
        semantic_sha256,
        table_count: if secondary_table_ordinal.is_some() {
            2
        } else {
            1
        },
        primary_binding,
        secondary_binding,
        primary_table_ordinal,
        secondary_table_ordinal,
    })
}

fn common_binding() -> Result<TableRulingHwpxBinding, AnyError> {
    let rows = [0_u32, 1, 2, 3];
    let columns = [0_u32, 1, 2];
    let mut cells = Vec::new();
    for row in rows {
        for column in columns {
            let (master, payload) = match row {
                0 => (
                    format!("structure-target-cell-0-{column}"),
                    Some(format!("structure-target-payload-0-{column}")),
                ),
                1 => (format!("structure-target-TABLE-012-new-{column}"), None),
                2 => (
                    format!("structure-target-cell-1-{column}"),
                    Some(format!("structure-target-payload-1-{column}")),
                ),
                3 => (
                    format!("structure-target-cell-2-{column}"),
                    Some(format!("structure-target-payload-2-{column}")),
                ),
                _ => return Err("common row is out of range".into()),
            };
            cells.push(TableRulingHwpxCellBinding {
                master_cell_id: id(&master)?,
                payload_block_ids: payload
                    .map(|value| id(&value))
                    .transpose()?
                    .into_iter()
                    .collect(),
            });
        }
    }
    Ok(TableRulingHwpxBinding {
        table_id: id("structure-target-table")?,
        row_boundaries_hwpunit: vec![0, 4_000, 8_000, 12_000, 16_000],
        column_boundaries_hwpunit: vec![0, 12_000, 24_000, 36_000],
        cells,
    })
}

fn nested_template_binding() -> Result<TableRulingHwpxBinding, AnyError> {
    Ok(TableRulingHwpxBinding {
        table_id: id("remaining-target-nested-table")?,
        row_boundaries_hwpunit: vec![0, 2_000, 4_000],
        column_boundaries_hwpunit: vec![0, 6_000, 12_000],
        cells: ["a", "b", "c", "d"]
            .into_iter()
            .enumerate()
            .map(|(index, suffix)| {
                Ok(TableRulingHwpxCellBinding {
                    master_cell_id: id(&format!("remaining-target-nested-cell-{suffix}"))?,
                    payload_block_ids: if index < 3 {
                        vec![id(&format!("remaining-target-nested-payload-{suffix}"))?]
                    } else {
                        Vec::new()
                    },
                })
            })
            .collect::<Result<Vec<_>, AnyError>>()?,
    })
}

fn auto_fill_binding() -> Result<TableRulingHwpxBinding, AnyError> {
    let mut cells = Vec::new();
    for row in 0..2_u32 {
        for column in 0..3_u32 {
            cells.push(TableRulingHwpxCellBinding {
                master_cell_id: id(&format!("remaining-auto-fill-cell-{row}-{column}"))?,
                payload_block_ids: if row == 0 {
                    vec![id(&format!("remaining-auto-fill-source-{column}"))?]
                } else {
                    Vec::new()
                },
            });
        }
    }
    Ok(TableRulingHwpxBinding {
        table_id: id("remaining-auto-fill-table")?,
        row_boundaries_hwpunit: vec![0, 4_000, 8_000],
        column_boundaries_hwpunit: vec![0, 12_000, 24_000, 36_000],
        cells,
    })
}

fn auto_fill_source_section() -> Vec<u8> {
    let row0 = [
        auto_fill_cell(0, 0, "Seed"),
        auto_fill_cell(0, 1, "Label"),
        auto_fill_cell(0, 2, "Keep"),
    ]
    .join("");
    let row1 = [
        auto_fill_cell(1, 0, ""),
        auto_fill_cell(1, 1, ""),
        auto_fill_cell(1, 2, ""),
    ]
    .join("");
    format!(
        concat!(
            r#"<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">"#,
            "{}",
            r#"<hp:tbl id="8701" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="1" rowCnt="2" colCnt="3" cellSpacing="0" borderFillIDRef="1" noAdjust="0">"#,
            r#"<hp:sz width="36000" widthRelTo="ABSOLUTE" height="8000" heightRelTo="ABSOLUTE" protect="0"/>"#,
            r#"<hp:pos treatAsChar="0" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="0" horzOffset="0"/>"#,
            r#"<hp:outMargin left="0" right="0" top="0" bottom="0"/><hp:inMargin left="0" right="0" top="0" bottom="0"/>"#,
            "<hp:tr>{row0}</hp:tr><hp:tr>{row1}</hp:tr></hp:tbl>{}</hs:sec>"
        ),
        text_paragraph(87, "BEFORE"),
        text_paragraph(88, "AFTER"),
        row0 = row0,
        row1 = row1,
    )
    .into_bytes()
}

fn auto_fill_cell(row: u32, column: u32, value: &str) -> String {
    let text = if value.is_empty() {
        "<hp:t/>".to_owned()
    } else {
        format!("<hp:t>{value}</hp:t>")
    };
    format!(
        concat!(
            r#"<hp:tc name="" header="{header}" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="3">"#,
            r#"<hp:cellAddr colAddr="{column}" rowAddr="{row}"/><hp:cellSpan colSpan="1" rowSpan="1"/>"#,
            r#"<hp:cellSz width="12000" height="4000"/><hp:cellMargin left="0" right="0" top="0" bottom="0"/>"#,
            r#"<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">"#,
            r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0">{text}</hp:run></hp:p></hp:subList></hp:tc>"#
        ),
        header = u8::from(row == 0),
        column = column,
        row = row,
        text = text,
    )
}

fn nested_template_section() -> Vec<u8> {
    let row0 = format!(
        "<hp:tr>{}{}</hp:tr>",
        nested_cell(0, 0, &text_paragraph(80, "N1")),
        nested_cell(0, 1, &text_paragraph(81, "N2")),
    );
    let row1 = format!(
        "<hp:tr>{}{}</hp:tr>",
        nested_cell(1, 0, &text_paragraph(82, "7")),
        nested_cell(1, 1, &formula_paragraph(8801, 8802, "SUM(LEFT)", "7")),
    );
    format!(
        concat!(
            r#"<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">"#,
            r#"<hp:p id="8900" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:ctrl>"#,
            r#"<hp:tbl id="8901" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="0" rowCnt="2" colCnt="2" cellSpacing="0" borderFillIDRef="1" noAdjust="0">"#,
            r#"<hp:sz width="12000" widthRelTo="ABSOLUTE" height="4000" heightRelTo="ABSOLUTE" protect="0"/>"#,
            r#"<hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="0" horzOffset="0"/>"#,
            r#"<hp:outMargin left="0" right="0" top="0" bottom="0"/><hp:inMargin left="0" right="0" top="0" bottom="0"/>"#,
            "{row0}{row1}</hp:tbl></hp:ctrl><hp:t/></hp:run></hp:p></hs:sec>"
        ),
        row0 = row0,
        row1 = row1,
    )
    .into_bytes()
}

fn nested_cell(row: u32, column: u32, payload: &str) -> String {
    format!(
        concat!(
            r#"<hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="3">"#,
            r#"<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">"#,
            "{payload}</hp:subList>",
            r#"<hp:cellAddr colAddr="{column}" rowAddr="{row}"/><hp:cellSpan colSpan="1" rowSpan="1"/>"#,
            r#"<hp:cellSz width="6000" height="2000"/><hp:cellMargin left="0" right="0" top="0" bottom="0"/></hp:tc>"#
        ),
        payload = payload,
        column = column,
        row = row,
    )
}

fn absolute_source_section() -> Vec<u8> {
    let row0 = [
        absolute_cell(0, 0, &formula_paragraph(9101, 9201, "A2", "5")),
        absolute_cell(0, 1, &text_paragraph(91, "other")),
        absolute_cell(0, 2, &text_paragraph(92, "header")),
    ]
    .join("");
    let row1 = [
        absolute_cell(1, 0, &text_paragraph(93, "5")),
        absolute_cell(1, 1, &text_paragraph(94, "7")),
        absolute_cell(1, 2, &formula_paragraph(9102, 9202, "SUM(A2:B2)", "12")),
    ]
    .join("");
    format!(
        concat!(
            r#"<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">"#,
            "{}",
            r#"<hp:tbl id="9001" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="1" rowCnt="2" colCnt="3" cellSpacing="0" borderFillIDRef="1" noAdjust="0">"#,
            r#"<hp:sz width="18000" widthRelTo="ABSOLUTE" height="4000" heightRelTo="ABSOLUTE" protect="0"/>"#,
            r#"<hp:pos treatAsChar="0" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="0" horzOffset="0"/>"#,
            r#"<hp:outMargin left="0" right="0" top="0" bottom="0"/><hp:inMargin left="0" right="0" top="0" bottom="0"/>"#,
            "<hp:tr>{row0}</hp:tr><hp:tr>{row1}</hp:tr></hp:tbl>{}</hs:sec>"
        ),
        text_paragraph(95, "BEFORE"),
        text_paragraph(96, "AFTER"),
        row0 = row0,
        row1 = row1,
    )
    .into_bytes()
}

fn absolute_cell(row: u32, column: u32, payload: &str) -> String {
    format!(
        concat!(
            r#"<hp:tc name="" header="{header}" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="3">"#,
            r#"<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">"#,
            "{payload}</hp:subList>",
            r#"<hp:cellAddr colAddr="{column}" rowAddr="{row}"/><hp:cellSpan colSpan="1" rowSpan="1"/>"#,
            r#"<hp:cellSz width="6000" height="2000"/><hp:cellMargin left="0" right="0" top="0" bottom="0"/></hp:tc>"#
        ),
        header = u8::from(row == 0),
        payload = payload,
        column = column,
        row = row,
    )
}

fn text_paragraph(identifier: u32, value: &str) -> String {
    format!(
        r#"<hp:p id="{identifier}" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>{value}</hp:t></hp:run></hp:p>"#
    )
}

fn formula_paragraph(begin_id: u64, field_id: u64, formula: &str, result: &str) -> String {
    let native = format!("={formula}");
    format!(
        concat!(
            r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:ctrl>"#,
            r#"<hp:fieldBegin id="{begin_id}" type="FORMULA" name="" editable="0" dirty="0" zorder="-1" fieldid="{field_id}">"#,
            r#"<hp:parameters cnt="5" name=""><hp:integerParam name="Prop">8</hp:integerParam>"#,
            r#"<hp:stringParam name="Command">{native}??%g,;;{result}</hp:stringParam>"#,
            r#"<hp:stringParam name="Formula">{native}</hp:stringParam><hp:stringParam name="ResultFormat">%g,</hp:stringParam>"#,
            r#"<hp:stringParam name="LastResult">{result}</hp:stringParam></hp:parameters></hp:fieldBegin></hp:ctrl>"#,
            r#"<hp:t>{result}</hp:t><hp:ctrl><hp:fieldEnd beginIDRef="{begin_id}" fieldid="{field_id}"/></hp:ctrl><hp:t/></hp:run></hp:p>"#
        ),
        begin_id = begin_id,
        field_id = field_id,
        native = native,
        result = result,
    )
}

fn absolute_limits() -> Result<TableAbsoluteReferenceHwpxLimits, AnyError> {
    Ok(TableAbsoluteReferenceHwpxLimits {
        formula: formula_limits()?,
        ..TableAbsoluteReferenceHwpxLimits::default()
    })
}

fn absolute_formula(source: &str, cache: FormulaCache) -> Result<FormulaCell, AnyError> {
    let limits = absolute_limits()?;
    let ast = FormulaAst::parse(source, limits.formula)?;
    Ok(FormulaCell::from_draft(
        FormulaCellDraft {
            schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
            owner: CellCoordinate { row: 1, column: 2 },
            ast: FormulaAstDraft {
                schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
                expression: ast.expression().clone(),
            },
            cache,
            number_format: FormulaNumberFormat::General,
        },
        FormulaGridDimensions {
            rows: 2,
            columns: 3,
        },
        limits.formula,
    )?)
}

fn absolute_cache(value: i64) -> FormulaCache {
    FormulaCache::Unverified {
        value: FormulaValue::Decimal {
            value: FormulaDecimal::new(value, 0),
        },
    }
}

fn formula_draft(value: &FormulaCell) -> FormulaCellDraft {
    FormulaCellDraft {
        schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
        owner: value.owner(),
        ast: FormulaAstDraft {
            schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
            expression: value.ast().expression().clone(),
        },
        cache: value.cache().clone(),
        number_format: value.number_format(),
    }
}

fn formula_limits() -> Result<FormulaLimits, AnyError> {
    Ok(FormulaLimits::new(FormulaLimitConfig {
        rows: 32,
        columns: 32,
        ..FormulaLimitConfig::default()
    })?)
}

fn formula_grid(rows: u32, columns: u32) -> Result<TableGrid, AnyError> {
    let mut master_cells = Vec::new();
    for row in 0..rows {
        for column in 0..columns {
            master_cells.push(TableCellSpan {
                master_cell_id: id(&format!("remaining-number-cell-{row}-{column}"))?,
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

fn indexed_digest(index: usize, base: u8) -> Result<String, AnyError> {
    let offset = u8::try_from(index % 10)?;
    let value = base
        .checked_add(offset)
        .ok_or("fixture digest byte must stay in range")?;
    Ok(format!("{value:02x}").repeat(32))
}

fn id(value: &str) -> Result<LogicalId, AnyError> {
    Ok(LogicalId::parse(value)?)
}

fn component_digest<T: Serialize + ?Sized>(value: &T) -> Result<String, AnyError> {
    Ok(hex(Sha256::digest(serde_json::to_vec(value)?)))
}

fn flow_digest(flow: &[u8]) -> String {
    hex(Sha256::digest(flow))
}

fn target_flow(before: &str, feature_id: &str) -> String {
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.p06-09-table-remaining-target-flow/v1\0");
    digest.update(before.as_bytes());
    digest.update(b"\0");
    digest.update(feature_id.as_bytes());
    hex(digest.finalize())
}

fn semantic_flow_digest(flow: &[u8]) -> Result<[u8; 32], AnyError> {
    let text = std::str::from_utf8(flow)?;
    let prefix = "<opf:meta name=\"ModifiedDate\" content=\"text\">";
    let suffix = "</opf:meta>";
    let start = text.find(prefix).ok_or("ModifiedDate is missing")? + prefix.len();
    let end = text[start..]
        .find(suffix)
        .map(|offset| start + offset)
        .ok_or("ModifiedDate end is missing")?;
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

fn binding_evidence(binding: &TableRulingHwpxBinding) -> BindingEvidence {
    BindingEvidence {
        table_id: binding.table_id.as_str().to_owned(),
        row_boundaries_hwpunit: binding.row_boundaries_hwpunit.clone(),
        column_boundaries_hwpunit: binding.column_boundaries_hwpunit.clone(),
        cells: binding
            .cells
            .iter()
            .map(|cell| CellBindingEvidence {
                master_cell_id: cell.master_cell_id.as_str().to_owned(),
                payload_block_ids: cell
                    .payload_block_ids
                    .iter()
                    .map(|value| value.as_str().to_owned())
                    .collect(),
            })
            .collect(),
    }
}

fn source_artifact(role: &'static str, path: &Path, sha256: &'static str) -> SourceArtifact {
    SourceArtifact {
        role,
        path: path.to_string_lossy().replace('\\', "/"),
        sha256,
    }
}

fn require_distinct_cases(cases: &[BuiltCase]) -> Result<(), AnyError> {
    if cases.len() != 10 {
        return Err("remaining target batch must contain exactly ten cases".into());
    }
    let mut features = std::collections::BTreeSet::new();
    let mut files = std::collections::BTreeSet::new();
    let mut packages = std::collections::BTreeSet::new();
    for case in cases {
        if case.package.is_empty()
            || case.package.len() as u64 > MAX_OUTPUT_BYTES
            || !features.insert(case.metadata.feature_id)
            || !files.insert(case.metadata.file)
            || !packages.insert(hex(Sha256::digest(&case.package)))
        {
            return Err("remaining target cases are empty, oversized or not distinct".into());
        }
    }
    Ok(())
}

fn read_package(path: &Path, expected: &str) -> Result<PackageParts, AnyError> {
    let bytes = read_bounded_file(path, MAX_FILE_BYTES)?;
    require_digest(&bytes, expected, "source package")?;
    let mut reader =
        BoundedZipReader::open(Cursor::new(bytes.as_slice()), PackageLimits::default())?;
    let header = read_part(&mut reader, "Contents/header.xml")?;
    let section = read_part(&mut reader, "Contents/section0.xml")?;
    let flow = read_part(&mut reader, "Contents/content.hpf")?;
    Ok(PackageParts {
        bytes,
        header,
        section,
        flow,
    })
}

fn read_part(
    reader: &mut BoundedZipReader<Cursor<&[u8]>>,
    path: &str,
) -> Result<Vec<u8>, AnyError> {
    let index = reader
        .entries()
        .iter()
        .find(|entry| entry.path.as_str() == path)
        .map(|entry| entry.index)
        .ok_or("required package part is missing")?;
    Ok(reader.read_entry(index)?)
}

fn replace_parts(source: &[u8], header: &[u8], section: &[u8]) -> Result<Vec<u8>, AnyError> {
    let mut reader = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let entries = reader.entries().to_vec();
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for entry in entries {
        let method = match entry.compression {
            Compression::Stored => CompressionMethod::Stored,
            Compression::Deflated => CompressionMethod::Deflated,
        };
        let mut options = SimpleFileOptions::default()
            .compression_method(method)
            .last_modified_time(DateTime::default())
            .system(zip::System::Unix)
            .unix_permissions(0o644);
        if method == CompressionMethod::Deflated {
            options = options.compression_level(Some(NORMALIZED_DEFLATE_LEVEL));
        }
        writer.start_file(entry.path.as_str(), options)?;
        let bytes = match entry.path.as_str() {
            "Contents/header.xml" => header.to_vec(),
            "Contents/section0.xml" => section.to_vec(),
            _ => reader.read_entry(entry.index)?,
        };
        writer.write_all(&bytes)?;
    }
    let output = writer.finish()?.into_inner();
    if output.is_empty() || output.len() as u64 > MAX_OUTPUT_BYTES {
        return Err("remaining target package exceeds bound".into());
    }
    Ok(output)
}

fn read_bounded_file(path: &Path, maximum: u64) -> Result<Vec<u8>, AnyError> {
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

fn write_create_new(path: &Path, bytes: &[u8]) -> Result<(), AnyError> {
    let mut file = OpenOptions::new().write(true).create_new(true).open(path)?;
    file.write_all(bytes)?;
    file.sync_all()?;
    Ok(())
}

fn require_digest(bytes: &[u8], expected: &str, label: &str) -> Result<(), AnyError> {
    if hex(Sha256::digest(bytes)) != expected {
        return Err(format!("{label} digest mismatch").into());
    }
    Ok(())
}

fn count_occurrences(source: &[u8], needle: &[u8]) -> usize {
    if needle.is_empty() {
        return 0;
    }
    source
        .windows(needle.len())
        .filter(|window| *window == needle)
        .count()
}

fn take_path(
    values: &mut BTreeMap<String, std::ffi::OsString>,
    key: &str,
) -> Result<PathBuf, AnyError> {
    Ok(PathBuf::from(
        values.remove(key).ok_or("required path is missing")?,
    ))
}

fn hex(value: impl AsRef<[u8]>) -> String {
    use std::fmt::Write as _;

    value
        .as_ref()
        .iter()
        .fold(String::new(), |mut output, byte| {
            let _ = write!(output, "{byte:02x}");
            output
        })
}
