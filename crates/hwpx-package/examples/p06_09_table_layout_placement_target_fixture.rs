use std::env;
use std::error::Error;
use std::fs::{self, OpenOptions};
use std::io::{Cursor, Write as _};
use std::path::{Path, PathBuf};

use domain_ir::{
    FontMetricEvidence, FontMetricStatus, HwpUnit, LengthMicrometers, LogicalId,
    TABLE_LAYOUT_SCHEMA_VERSION, TABLE_PLACEMENT_SCHEMA_VERSION, TableAttachmentMode,
    TableCellMeasure, TableCellSpan, TableColumnConstraint, TableFloatingPlacement,
    TableGeometryLimits, TableGeometryOperation, TableGeometryState, TableGrid, TableGridLimits,
    TableHorizontalAlignment, TableHorizontalReference, TableLayoutLimits, TableLayoutPlan,
    TableLayoutProblem, TableLayoutSolver, TableOuterMargins, TablePlacementLimits,
    TablePlacementOperation, TablePlacementState, TablePlacementStateDraft, TableTextFlow,
    TableTextWrap, TableTrackRange, TableVerticalAlignment, TableVerticalReference, TableWidthSpec,
};
use hwpx_package::{
    BoundedZipReader, Compression, PackageLimits, TableGeometryHwpxLowerer, TableLayoutHwpxLimits,
    TableLayoutHwpxLowerer, TableLayoutHwpxReadback, TableLayoutHwpxReader,
    TablePlacementHwpxLowerer, TablePlacementHwpxReadback, TablePlacementHwpxReader,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, DateTime, ZipWriter};

const MAX_FILE_BYTES: u64 = 8 * 1024 * 1024;
const EXPECTED_ANCESTOR_SHA256: &str =
    "0459a05b8543edb2e05c9c0117f76df999c8543bad255d06d26d4b3b57388252";
const FONT_PROFILE_ID: &str = "hwpx-agent.font-metric.hancom-2020-line-box-100-hwpunit-bucket/1";
const FONT_RECEIPT_SHA256: &str =
    "c4755f99ebf1e49010bf26425d61f77c496fa713d86404004348027acfc1d2ab";

struct Arguments {
    ancestor: PathBuf,
    expected_ancestor_sha256: String,
    output_directory: PathBuf,
}

impl Arguments {
    fn parse() -> Result<Self, Box<dyn Error>> {
        let mut values = env::args_os();
        let _program = values.next();
        let result = Self {
            ancestor: values
                .next()
                .map(PathBuf::from)
                .ok_or("missing ancestor HWPX")?,
            expected_ancestor_sha256: values
                .next()
                .ok_or("missing ancestor SHA-256")?
                .into_string()
                .map_err(|_| "ancestor SHA-256 is not Unicode")?,
            output_directory: values
                .next()
                .map(PathBuf::from)
                .ok_or("missing output directory")?,
        };
        if values.next().is_some() {
            return Err("too many arguments".into());
        }
        Ok(result)
    }
}

#[derive(Serialize)]
struct Manifest {
    schema_version: &'static str,
    source_ancestor_sha256: &'static str,
    source_section_sha256: String,
    prepared_section_sha256: String,
    grid_sha256: String,
    font_metric_profile_id: &'static str,
    font_metric_receipt_sha256: &'static str,
    cases: Vec<ManifestCase>,
    shared_content_sha256: String,
    all_cases_content_preserved: bool,
    actual_hangul_2020: bool,
    render: &'static str,
    automation: &'static str,
    differential: &'static str,
}

#[derive(Serialize)]
struct ManifestCase {
    case_id: &'static str,
    feature_id: &'static str,
    capability_id: &'static str,
    adapter: &'static str,
    file: &'static str,
    sha256: String,
    target_section_sha256: String,
    semantic_sha256: String,
    modified_attribute_count: usize,
    layout: LayoutEvidence,
    placement: PlacementEvidence,
    formula_count: usize,
    page_split: &'static str,
}

#[derive(Serialize)]
struct LayoutEvidence {
    rows: u32,
    columns: u32,
    table_width_hwpunit: u32,
    table_height_hwpunit: u32,
    column_widths_hwpunit: Vec<u32>,
    row_heights_hwpunit: Vec<u32>,
    content_sha256: String,
}

#[derive(Serialize)]
#[allow(clippy::struct_excessive_bools)]
struct PlacementEvidence {
    treat_as_char: bool,
    affect_line_spacing: bool,
    horizontal_reference: TableHorizontalReference,
    vertical_reference: TableVerticalReference,
    horizontal_alignment: TableHorizontalAlignment,
    vertical_alignment: TableVerticalAlignment,
    horizontal_offset_hwpunit: i64,
    vertical_offset_hwpunit: i64,
    flow_with_text: bool,
    allow_overlap: bool,
    hold_anchor_and_shape: bool,
    text_wrap: TableTextWrap,
    text_flow: TableTextFlow,
    outer_margins_hwpunit: [u32; 4],
}

struct BuiltCase {
    metadata: CaseMetadata,
    package: Vec<u8>,
    section: Vec<u8>,
    semantic_sha256: [u8; 32],
    modified_attribute_count: usize,
}

#[derive(Clone, Copy)]
struct CaseMetadata {
    case_id: &'static str,
    feature_id: &'static str,
    capability_id: &'static str,
    adapter: &'static str,
    file: &'static str,
}

#[derive(Clone, Copy)]
enum LayoutCase {
    FixedColumn,
    FitContent,
    FitPage,
}

fn main() -> Result<(), Box<dyn Error>> {
    run(&Arguments::parse()?)
}

#[allow(clippy::too_many_lines)]
fn run(arguments: &Arguments) -> Result<(), Box<dyn Error>> {
    require_lower_sha256(&arguments.expected_ancestor_sha256)?;
    if arguments.expected_ancestor_sha256 != EXPECTED_ANCESTOR_SHA256 {
        return Err("exact layout/placement ancestor identity differs".into());
    }
    if arguments
        .ancestor
        .extension()
        .and_then(|value| value.to_str())
        != Some("hwpx")
    {
        return Err("ancestor must be an .hwpx file".into());
    }
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

    let ancestor = read_bounded_file(&arguments.ancestor, MAX_FILE_BYTES)?;
    require_digest(&ancestor, EXPECTED_ANCESTOR_SHA256, "ancestor")?;
    let source_section = read_section(&ancestor)?;
    let grid = grid_4x3()?;
    let base_geometry = base_geometry(&grid)?;
    let (prepared_section, prepared_receipt) =
        TableGeometryHwpxLowerer::lower_in_section_with_receipt(
            &source_section,
            0,
            &grid,
            &base_geometry,
            TableLayoutHwpxLimits::default(),
        )?;
    let prepared_layout = TableLayoutHwpxReader::read_in_section(
        &prepared_section,
        0,
        TableLayoutHwpxLimits::default(),
    )?;
    require_prepared_layout(&prepared_layout)?;
    let source_placement = source_placement()?;
    let native_source_placement = TablePlacementHwpxReader::read_in_section(
        &prepared_section,
        0,
        TableLayoutHwpxLimits::default(),
    )?;
    require_source_placement(&native_source_placement)?;

    let mut cases = Vec::new();
    cases.try_reserve_exact(10)?;
    cases.push(build_geometry_case(
        &ancestor,
        &prepared_section,
        &grid,
        &base_geometry,
        TableGeometryOperation::EqualRowHeights {
            range: TableTrackRange::new(0, 4),
        },
        metadata(
            "table-018-equal-row-height-4x3",
            "TABLE-018",
            "table.equal_row_height",
            "table-018-equal-row-height-4x3.hwpx",
        ),
    )?);
    cases.push(build_geometry_case(
        &ancestor,
        &prepared_section,
        &grid,
        &base_geometry,
        TableGeometryOperation::EqualColumnWidths {
            range: TableTrackRange::new(0, 3),
        },
        metadata(
            "table-019-equal-column-width-4x3",
            "TABLE-019",
            "table.equal_column_width",
            "table-019-equal-column-width-4x3.hwpx",
        ),
    )?);
    cases.push(build_geometry_case(
        &ancestor,
        &prepared_section,
        &grid,
        &base_geometry,
        TableGeometryOperation::SetRowMinimumHeight {
            range: TableTrackRange::new(0, 4),
            minimum_height: hwp(7_000)?,
        },
        metadata(
            "table-050-row-min-height-4x3",
            "TABLE-050",
            "table.row_min_height",
            "table-050-row-min-height-4x3.hwpx",
        ),
    )?);

    for (layout_case, case_metadata) in [
        (
            LayoutCase::FixedColumn,
            metadata(
                "table-051-column-fixed-width-4x3",
                "TABLE-051",
                "table.column_fixed_width",
                "table-051-column-fixed-width-4x3.hwpx",
            ),
        ),
        (
            LayoutCase::FitContent,
            metadata(
                "table-052-autofit-content-4x3",
                "TABLE-052",
                "table.autofit_content",
                "table-052-autofit-content-4x3.hwpx",
            ),
        ),
        (
            LayoutCase::FitPage,
            metadata(
                "table-053-autofit-page-4x3",
                "TABLE-053",
                "table.autofit_page",
                "table-053-autofit-page-4x3.hwpx",
            ),
        ),
    ] {
        cases.push(build_layout_case(
            &ancestor,
            &prepared_section,
            &grid,
            layout_case,
            case_metadata,
        )?);
    }

    let positioned = TableFloatingPlacement {
        horizontal_reference: TableHorizontalReference::Paper,
        vertical_reference: TableVerticalReference::Page,
        horizontal_alignment: TableHorizontalAlignment::Right,
        vertical_alignment: TableVerticalAlignment::Bottom,
        horizontal_offset: hwp(720)?,
        vertical_offset: hwp(360)?,
        flow_with_text: false,
        allow_overlap: true,
        hold_anchor_and_shape: true,
    };
    for (operation, case_metadata) in [
        (
            TablePlacementOperation::SetPosition {
                placement: positioned,
            },
            metadata(
                "table-034-position-4x3",
                "TABLE-034",
                "table.position",
                "table-034-position-4x3.hwpx",
            ),
        ),
        (
            TablePlacementOperation::SetInline {
                affect_line_spacing: true,
            },
            metadata(
                "table-036-inline-floating-4x3",
                "TABLE-036",
                "table.inline_floating",
                "table-036-inline-floating-4x3.hwpx",
            ),
        ),
        (
            TablePlacementOperation::SetWrap {
                text_wrap: TableTextWrap::Square,
                text_flow: TableTextFlow::LargestOnly,
            },
            metadata(
                "table-037-wrap-4x3",
                "TABLE-037",
                "table.wrap",
                "table-037-wrap-4x3.hwpx",
            ),
        ),
        (
            TablePlacementOperation::SetOuterMargins {
                margins: TableOuterMargins {
                    left: hwp(360)?,
                    right: hwp(720)?,
                    top: hwp(1_080)?,
                    bottom: hwp(1_440)?,
                },
            },
            metadata(
                "table-038-outer-margin-4x3",
                "TABLE-038",
                "table.outer_margin",
                "table-038-outer-margin-4x3.hwpx",
            ),
        ),
    ] {
        cases.push(build_placement_case(
            &ancestor,
            &prepared_section,
            &source_placement,
            operation,
            case_metadata,
        )?);
    }

    let shared_content_sha256 = hex(prepared_layout.content_sha256);
    let mut manifest_cases = Vec::new();
    manifest_cases.try_reserve_exact(cases.len())?;
    for case in &cases {
        let layout = TableLayoutHwpxReader::read_in_section(
            &case.section,
            0,
            TableLayoutHwpxLimits::default(),
        )?;
        let placement = TablePlacementHwpxReader::read_in_section(
            &case.section,
            0,
            TableLayoutHwpxLimits::default(),
        )?;
        if hex(layout.content_sha256) != shared_content_sha256
            || placement.content_sha256 != layout.content_sha256
            || count_occurrences(&case.section, b"<hp:fieldBegin") != 0
            || count_occurrences(&case.section, b"pageBreak=\"CELL\"") != 1
        {
            return Err(
                format!("{} preservation boundary differs", case.metadata.feature_id).into(),
            );
        }
        manifest_cases.push(ManifestCase {
            case_id: case.metadata.case_id,
            feature_id: case.metadata.feature_id,
            capability_id: case.metadata.capability_id,
            adapter: case.metadata.adapter,
            file: case.metadata.file,
            sha256: hex(Sha256::digest(&case.package).into()),
            target_section_sha256: hex(Sha256::digest(&case.section).into()),
            semantic_sha256: hex(case.semantic_sha256),
            modified_attribute_count: case.modified_attribute_count,
            layout: layout_evidence(&layout)?,
            placement: placement_evidence(&placement),
            formula_count: 0,
            page_split: "cell",
        });
    }
    require_case_distinctness(&manifest_cases)?;
    let manifest = Manifest {
        schema_version: "hwpx-agent.p06-09-table-layout-placement-target-fixture/v1",
        source_ancestor_sha256: EXPECTED_ANCESTOR_SHA256,
        source_section_sha256: hex(Sha256::digest(&source_section).into()),
        prepared_section_sha256: hex(Sha256::digest(&prepared_section).into()),
        grid_sha256: hex(grid.canonical_sha256()?),
        font_metric_profile_id: FONT_PROFILE_ID,
        font_metric_receipt_sha256: FONT_RECEIPT_SHA256,
        cases: manifest_cases,
        shared_content_sha256,
        all_cases_content_preserved: true,
        actual_hangul_2020: false,
        render: "not_run",
        automation: "not_run",
        differential: "not_run",
    };
    if prepared_receipt.modified_attribute_count == 0 {
        return Err("prepared unequal geometry did not change the ancestor".into());
    }

    fs::create_dir(&arguments.output_directory)?;
    for case in &cases {
        write_create_new(
            &arguments.output_directory.join(case.metadata.file),
            &case.package,
        )?;
    }
    write_create_new(
        &arguments.output_directory.join("fixture-manifest.json"),
        &serde_json::to_vec_pretty(&manifest)?,
    )?;
    require_digest(
        &read_bounded_file(&arguments.ancestor, MAX_FILE_BYTES)?,
        EXPECTED_ANCESTOR_SHA256,
        "ancestor recheck",
    )?;
    println!(
        "schema={} state=pass feature_count=10 actual_hangul_2020=false",
        manifest.schema_version
    );
    Ok(())
}

fn metadata(
    case_id: &'static str,
    feature_id: &'static str,
    capability_id: &'static str,
    file: &'static str,
) -> CaseMetadata {
    CaseMetadata {
        case_id,
        feature_id,
        capability_id,
        adapter: if matches!(feature_id, "TABLE-018" | "TABLE-019" | "TABLE-050") {
            "table_geometry_hwpx"
        } else if matches!(feature_id, "TABLE-051" | "TABLE-052" | "TABLE-053") {
            "table_layout_hwpx"
        } else {
            "table_placement_hwpx"
        },
        file,
    }
}

fn build_geometry_case(
    ancestor: &[u8],
    source: &[u8],
    grid: &TableGrid,
    base: &TableGeometryState,
    operation: TableGeometryOperation,
    metadata: CaseMetadata,
) -> Result<BuiltCase, Box<dyn Error>> {
    let result = base.apply(grid, operation, TableGeometryLimits::default())?;
    let (section, receipt) = TableGeometryHwpxLowerer::lower_in_section_with_receipt(
        source,
        0,
        grid,
        result.state(),
        TableLayoutHwpxLimits::default(),
    )?;
    Ok(BuiltCase {
        metadata,
        package: replace_section(ancestor, &section)?,
        section,
        semantic_sha256: result
            .state()
            .canonical_sha256(TableGeometryLimits::default())?,
        modified_attribute_count: receipt.modified_attribute_count,
    })
}

fn build_layout_case(
    ancestor: &[u8],
    source: &[u8],
    grid: &TableGrid,
    kind: LayoutCase,
    metadata: CaseMetadata,
) -> Result<BuiltCase, Box<dyn Error>> {
    let plan = layout_plan(grid, kind)?;
    plan.require_verified()?;
    let (section, receipt) = TableLayoutHwpxLowerer::lower_in_section_with_receipt(
        source,
        0,
        grid,
        &plan,
        TableLayoutHwpxLimits::default(),
    )?;
    Ok(BuiltCase {
        metadata,
        package: replace_section(ancestor, &section)?,
        section,
        semantic_sha256: plan.canonical_sha256(TableLayoutLimits::default())?,
        modified_attribute_count: receipt.modified_attribute_count,
    })
}

fn build_placement_case(
    ancestor: &[u8],
    source: &[u8],
    source_state: &TablePlacementState,
    operation: TablePlacementOperation,
    metadata: CaseMetadata,
) -> Result<BuiltCase, Box<dyn Error>> {
    let target = source_state
        .apply(operation, TablePlacementLimits::default())?
        .state()
        .clone();
    let (section, receipt) = TablePlacementHwpxLowerer::lower_in_section_with_receipt(
        source,
        0,
        source_state,
        &target,
        TablePlacementLimits::default(),
        TableLayoutHwpxLimits::default(),
    )?;
    Ok(BuiltCase {
        metadata,
        package: replace_section(ancestor, &section)?,
        section,
        semantic_sha256: target.canonical_sha256(TablePlacementLimits::default())?,
        modified_attribute_count: receipt.modified_attribute_count,
    })
}

fn grid_4x3() -> Result<TableGrid, Box<dyn Error>> {
    let mut cells = Vec::new();
    cells.try_reserve_exact(12)?;
    for row in 0..4_u32 {
        for column in 0..3_u32 {
            cells.push(TableCellSpan {
                master_cell_id: LogicalId::parse(format!("layout-placement-cell-{row}-{column}"))?,
                row,
                column,
                row_span: 1,
                column_span: 1,
            });
        }
    }
    Ok(TableGrid::new(4, 3, cells, TableGridLimits::default())?)
}

fn base_geometry(grid: &TableGrid) -> Result<TableGeometryState, Box<dyn Error>> {
    Ok(TableGeometryState::new(
        grid,
        vec![hwp(3_000)?, hwp(4_000)?, hwp(5_000)?, hwp(6_000)?],
        vec![hwp(2_000)?; 4],
        vec![hwp(8_000)?, hwp(12_000)?, hwp(16_000)?],
        vec![hwp(4_000)?; 3],
        TableGeometryLimits::default(),
    )?)
}

fn layout_plan(grid: &TableGrid, kind: LayoutCase) -> Result<TableLayoutPlan, Box<dyn Error>> {
    let width = match kind {
        LayoutCase::FixedColumn => TableWidthSpec::Absolute {
            width: hwp(36_000)?,
        },
        LayoutCase::FitContent => TableWidthSpec::FitContent,
        LayoutCase::FitPage => TableWidthSpec::FitPage,
    };
    let columns = match kind {
        LayoutCase::FixedColumn => vec![
            column(6_000, 8_000, 8_000, Some(8_000))?,
            column(6_000, 12_000, 12_000, None)?,
            column(6_000, 16_000, 16_000, None)?,
        ],
        LayoutCase::FitContent | LayoutCase::FitPage => vec![
            column(6_000, 9_000, 8_000, None)?,
            column(6_000, 12_000, 12_000, None)?,
            column(6_000, 15_000, 16_000, None)?,
        ],
    };
    let mut cells = Vec::new();
    cells.try_reserve_exact(12)?;
    for row in 0..4_i64 {
        for column in 0..3_i64 {
            cells.push(TableCellMeasure {
                master_cell_id: LogicalId::parse(format!("layout-placement-cell-{row}-{column}"))?,
                leading_margin: hwp(36)?,
                trailing_margin: hwp(36)?,
                unbreakable_content_width: hwp(1_000 + column * 250)?,
                preferred_content_width: hwp(1_500 + column * 500)?,
                line_height: hwp(2_000 + row * 500)?,
                font_metric_evidence: FontMetricEvidence {
                    status: FontMetricStatus::Verified,
                    profile_id: Some(FONT_PROFILE_ID.to_owned()),
                    source_sha256: Some(FONT_RECEIPT_SHA256.to_owned()),
                },
            });
        }
    }
    let problem = TableLayoutProblem {
        schema_version: TABLE_LAYOUT_SCHEMA_VERSION.to_owned(),
        width,
        body_width: hwp(48_000)?,
        columns,
        cells,
    };
    Ok(TableLayoutSolver::solve(
        grid,
        &problem,
        TableLayoutLimits::default(),
    )?)
}

fn column(
    minimum: i64,
    preferred: i64,
    previous: i64,
    fixed: Option<i64>,
) -> Result<TableColumnConstraint, Box<dyn Error>> {
    Ok(TableColumnConstraint {
        minimum_width: hwp(minimum)?,
        preferred_width: hwp(preferred)?,
        previous_width: hwp(previous)?,
        fixed_width: fixed.map(hwp).transpose()?,
    })
}

fn source_placement() -> Result<TablePlacementState, Box<dyn Error>> {
    Ok(TablePlacementState::from_draft(
        TablePlacementStateDraft {
            schema_version: TABLE_PLACEMENT_SCHEMA_VERSION.to_owned(),
            table_id: LogicalId::parse("layout-placement-target-table")?,
            attachment: TableAttachmentMode::Floating {
                placement: TableFloatingPlacement {
                    horizontal_reference: TableHorizontalReference::Column,
                    vertical_reference: TableVerticalReference::Paragraph,
                    horizontal_alignment: TableHorizontalAlignment::Center,
                    vertical_alignment: TableVerticalAlignment::Top,
                    horizontal_offset: hwp(0)?,
                    vertical_offset: hwp(0)?,
                    flow_with_text: true,
                    allow_overlap: false,
                    hold_anchor_and_shape: false,
                },
            },
            text_wrap: TableTextWrap::TopAndBottom,
            text_flow: TableTextFlow::BothSides,
            outer_margins: TableOuterMargins {
                left: hwp(283)?,
                right: hwp(283)?,
                top: hwp(283)?,
                bottom: hwp(283)?,
            },
        },
        TablePlacementLimits::default(),
    )?)
}

fn require_prepared_layout(value: &TableLayoutHwpxReadback) -> Result<(), Box<dyn Error>> {
    let columns = track_widths(value)?;
    let rows = track_heights(value)?;
    if value.rows != 4
        || value.columns != 3
        || value.table_width_hwpunit != 36_000
        || value.table_height_hwpunit != 18_000
        || columns != [8_000, 12_000, 16_000]
        || rows != [3_000, 4_000, 5_000, 6_000]
        || value.cells.len() != 12
    {
        return Err("prepared unequal layout differs".into());
    }
    Ok(())
}

fn require_source_placement(value: &TablePlacementHwpxReadback) -> Result<(), Box<dyn Error>> {
    if value.attachment_flags.treat_as_char
        || value.attachment_flags.affect_line_spacing
        || value.horizontal_reference != TableHorizontalReference::Column
        || value.vertical_reference != TableVerticalReference::Paragraph
        || value.horizontal_alignment != TableHorizontalAlignment::Center
        || value.vertical_alignment != TableVerticalAlignment::Top
        || value.horizontal_offset_hwpunit != 0
        || value.vertical_offset_hwpunit != 0
        || !value.floating_flags.flow_with_text
        || value.floating_flags.allow_overlap
        || value.floating_flags.hold_anchor_and_shape
        || value.text_wrap != TableTextWrap::TopAndBottom
        || value.text_flow != TableTextFlow::BothSides
        || [
            value.outer_margins.left_hwpunit,
            value.outer_margins.right_hwpunit,
            value.outer_margins.top_hwpunit,
            value.outer_margins.bottom_hwpunit,
        ] != [283; 4]
    {
        return Err("source placement differs".into());
    }
    Ok(())
}

fn require_case_distinctness(cases: &[ManifestCase]) -> Result<(), Box<dyn Error>> {
    let by_id = |feature: &str| {
        cases
            .iter()
            .find(|case| case.feature_id == feature)
            .ok_or("manifest feature is missing")
    };
    if by_id("TABLE-018")?.layout.row_heights_hwpunit != [4_500; 4]
        || by_id("TABLE-019")?.layout.column_widths_hwpunit != [12_000; 3]
        || by_id("TABLE-050")?.layout.row_heights_hwpunit != [7_000; 4]
        || by_id("TABLE-051")?.layout.column_widths_hwpunit[0] != 8_000
        || by_id("TABLE-052")?.layout.table_width_hwpunit
            >= by_id("TABLE-053")?.layout.table_width_hwpunit
        || !by_id("TABLE-036")?.placement.treat_as_char
        || by_id("TABLE-037")?.placement.text_wrap != TableTextWrap::Square
        || by_id("TABLE-038")?.placement.outer_margins_hwpunit != [360, 720, 1_080, 1_440]
    {
        return Err("batch feature targets are not semantically distinct".into());
    }
    Ok(())
}

fn layout_evidence(value: &TableLayoutHwpxReadback) -> Result<LayoutEvidence, Box<dyn Error>> {
    Ok(LayoutEvidence {
        rows: value.rows,
        columns: value.columns,
        table_width_hwpunit: value.table_width_hwpunit,
        table_height_hwpunit: value.table_height_hwpunit,
        column_widths_hwpunit: track_widths(value)?,
        row_heights_hwpunit: track_heights(value)?,
        content_sha256: hex(value.content_sha256),
    })
}

fn placement_evidence(value: &TablePlacementHwpxReadback) -> PlacementEvidence {
    PlacementEvidence {
        treat_as_char: value.attachment_flags.treat_as_char,
        affect_line_spacing: value.attachment_flags.affect_line_spacing,
        horizontal_reference: value.horizontal_reference,
        vertical_reference: value.vertical_reference,
        horizontal_alignment: value.horizontal_alignment,
        vertical_alignment: value.vertical_alignment,
        horizontal_offset_hwpunit: value.horizontal_offset_hwpunit,
        vertical_offset_hwpunit: value.vertical_offset_hwpunit,
        flow_with_text: value.floating_flags.flow_with_text,
        allow_overlap: value.floating_flags.allow_overlap,
        hold_anchor_and_shape: value.floating_flags.hold_anchor_and_shape,
        text_wrap: value.text_wrap,
        text_flow: value.text_flow,
        outer_margins_hwpunit: [
            value.outer_margins.left_hwpunit,
            value.outer_margins.right_hwpunit,
            value.outer_margins.top_hwpunit,
            value.outer_margins.bottom_hwpunit,
        ],
    }
}

fn track_widths(value: &TableLayoutHwpxReadback) -> Result<Vec<u32>, Box<dyn Error>> {
    if value.cells.len()
        != usize::try_from(
            value
                .rows
                .checked_mul(value.columns)
                .ok_or("grid overflow")?,
        )?
    {
        return Err("layout is not an unmerged rectangular grid".into());
    }
    Ok(value
        .cells
        .iter()
        .take(usize::try_from(value.columns)?)
        .map(|cell| cell.width_hwpunit)
        .collect())
}

fn track_heights(value: &TableLayoutHwpxReadback) -> Result<Vec<u32>, Box<dyn Error>> {
    let columns = usize::try_from(value.columns)?;
    if columns == 0
        || value.cells.len()
            != usize::try_from(
                value
                    .rows
                    .checked_mul(value.columns)
                    .ok_or("grid overflow")?,
            )?
    {
        return Err("layout is not an unmerged rectangular grid".into());
    }
    Ok(value
        .cells
        .iter()
        .step_by(columns)
        .map(|cell| cell.height_hwpunit)
        .collect())
}

fn hwp(value: i64) -> Result<LengthMicrometers, Box<dyn Error>> {
    Ok(*LengthMicrometers::from_hwp_unit(HwpUnit::from_raw(value))?.value())
}

fn read_section(package: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(package), PackageLimits::default())?;
    let index = reader
        .entries()
        .iter()
        .find(|entry| entry.path.as_str() == "Contents/section0.xml")
        .map(|entry| entry.index)
        .ok_or("section part is missing")?;
    Ok(reader.read_entry(index)?)
}

fn replace_section(source: &[u8], section: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let entries = reader.entries().to_vec();
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    let mut replacements = 0_usize;
    for entry in entries {
        let method = match entry.compression {
            Compression::Stored => CompressionMethod::Stored,
            Compression::Deflated => CompressionMethod::Deflated,
        };
        let options = SimpleFileOptions::default()
            .compression_method(method)
            .last_modified_time(DateTime::default())
            .system(zip::System::Unix)
            .unix_permissions(0o644);
        writer.start_file(entry.path.as_str(), options)?;
        if entry.path.as_str() == "Contents/section0.xml" {
            replacements += 1;
            writer.write_all(section)?;
        } else {
            writer.write_all(&reader.read_entry(entry.index)?)?;
        }
    }
    if replacements != 1 {
        return Err("section replacement cardinality differs".into());
    }
    Ok(writer.finish()?.into_inner())
}

fn count_occurrences(source: &[u8], needle: &[u8]) -> usize {
    source
        .windows(needle.len())
        .filter(|window| *window == needle)
        .count()
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

fn write_create_new(path: &Path, bytes: &[u8]) -> Result<(), Box<dyn Error>> {
    let mut file = OpenOptions::new().write(true).create_new(true).open(path)?;
    file.write_all(bytes)?;
    file.sync_all()?;
    Ok(())
}

fn require_digest(bytes: &[u8], expected: &str, label: &str) -> Result<(), Box<dyn Error>> {
    if hex(Sha256::digest(bytes).into()) != expected {
        return Err(format!("{label} SHA-256 differs").into());
    }
    Ok(())
}

fn require_lower_sha256(value: &str) -> Result<(), Box<dyn Error>> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err("SHA-256 must be lowercase hexadecimal".into());
    }
    Ok(())
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
