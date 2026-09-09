use std::env;
use std::error::Error;
use std::fs::{self, OpenOptions};
use std::io::{Cursor, Write as _};
use std::path::{Path, PathBuf};

use domain_ir::{
    FormulaLimits, LogicalId, TABLE_RULING_SCHEMA_VERSION, TableGrid, TableGridLimits,
    TableRulingAxis, TableRulingBuilder, TableRulingDiagonalDirection, TableRulingFormulaPolicy,
    TableRulingLimits, TableRulingOperation, TableRulingPlan, TableRulingRequest,
    TableRulingRequestDraft, TableRulingState, TableRulingStroke,
};
use hwpx_package::{
    BoundedZipReader, Compression, PackageLimits, TableRulingHwpxBinding,
    TableRulingHwpxCellBinding, TableRulingHwpxLimits, TableRulingHwpxLoweredParts,
    TableRulingHwpxLowerer, TableRulingHwpxReadback, TableRulingHwpxReader,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, DateTime, ZipWriter};

const MAX_FIXTURE_BYTES: u64 = 8 * 1024 * 1024;
const NORMALIZED_DEFLATE_LEVEL: i64 = 6;
const EXPECTED_ANCESTOR_SHA256: &str =
    "6514a69b8c8c9d320bc19a032b16f2b71d59a38f164c690bc9e3d320a93320e5";
const TABLE_WIDTH: u32 = 41_952;
const TABLE_HEIGHT: u32 = 8_000;
const ROW_HEIGHT: u32 = 4_000;
const SOURCE_PREVIEW: &[u8] = b"<2><3><4><5><17><10><25><52>\r\n\r\n";
const FORMULA_RUN_CONTENT: &str = concat!(
    r#"<hp:ctrl><hp:fieldBegin id="1188510575" type="FORMULA" name="" editable="0" dirty="0" zorder="-1" fieldid="627469685">"#,
    r#"<hp:parameters cnt="5" name=""><hp:integerParam name="Prop">8</hp:integerParam>"#,
    r#"<hp:stringParam name="Command">=SUM(LEFT)??%g,;;52</hp:stringParam>"#,
    r#"<hp:stringParam name="Formula">=SUM(LEFT)</hp:stringParam>"#,
    r#"<hp:stringParam name="ResultFormat">%g,</hp:stringParam>"#,
    r#"<hp:stringParam name="LastResult">52</hp:stringParam></hp:parameters>"#,
    r#"</hp:fieldBegin></hp:ctrl><hp:t>52</hp:t><hp:ctrl>"#,
    r#"<hp:fieldEnd beginIDRef="1188510575" fieldid="627469685"/></hp:ctrl><hp:t/>"#,
);
const EMPTY_TRAILING_PARAGRAPH: &str = concat!(
    r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">"#,
    r#"<hp:run charPrIDRef="0"/></hp:p>"#,
);
const OUTER_PLACEHOLDER_PARAGRAPH: &str = concat!(
    r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">"#,
    r#"<hp:run charPrIDRef="0"><hp:t/></hp:run></hp:p>"#,
);

struct Arguments {
    ancestor: PathBuf,
    expected_ancestor_sha256: String,
    output_directory: PathBuf,
}

impl Arguments {
    fn parse() -> Result<Self, Box<dyn Error>> {
        let mut arguments = env::args_os();
        let _program = arguments.next();
        let ancestor = arguments
            .next()
            .map(PathBuf::from)
            .ok_or("missing ancestor HWPX")?;
        let expected_ancestor_sha256 = arguments
            .next()
            .ok_or("missing ancestor SHA-256")?
            .into_string()
            .map_err(|_| "ancestor SHA-256 is not Unicode")?;
        let output_directory = arguments
            .next()
            .map(PathBuf::from)
            .ok_or("missing output directory")?;
        if arguments.next().is_some() {
            return Err("too many arguments".into());
        }
        Ok(Self {
            ancestor,
            expected_ancestor_sha256,
            output_directory,
        })
    }
}

#[derive(Serialize)]
struct Manifest {
    schema_version: &'static str,
    source_ancestor_sha256: &'static str,
    cases: Vec<ManifestCase>,
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
    file: &'static str,
    sha256: String,
    selected_table_ordinal: usize,
    source_section_sha256: String,
    target_header_sha256: String,
    target_section_sha256: String,
    target_state_sha256: String,
    target_grid_sha256: String,
    target_rows: u32,
    target_columns: u32,
    target_master_cells: usize,
    payload_block_count: usize,
    formula_count: usize,
    binding: BindingEvidence,
    operations: Vec<OperationEvidence>,
}

#[derive(Serialize)]
struct BindingEvidence {
    table_id: String,
    row_boundaries_hwpunit: Vec<u32>,
    column_boundaries_hwpunit: Vec<u32>,
    cells: Vec<BindingCellEvidence>,
}

#[derive(Serialize)]
struct BindingCellEvidence {
    master_cell_id: String,
    payload_block_ids: Vec<String>,
}

#[derive(Serialize)]
struct OperationEvidence {
    name: &'static str,
    capability_id: &'static str,
    request_sha256: String,
    plan_sha256: String,
    source_state_sha256: Option<String>,
    source_grid_sha256: Option<String>,
    target_state_sha256: String,
    target_grid_sha256: String,
    added_border_fill_count: usize,
}

struct WorkingTable {
    header: Vec<u8>,
    section: Vec<u8>,
    binding: TableRulingHwpxBinding,
    readback: TableRulingHwpxReadback,
}

impl WorkingTable {
    fn open(
        header: Vec<u8>,
        section: Vec<u8>,
        binding: TableRulingHwpxBinding,
    ) -> Result<Self, Box<dyn Error>> {
        let readback = TableRulingHwpxReader::read_existing(
            &header,
            &section,
            0,
            &binding,
            TableRulingHwpxLimits::default(),
        )?;
        Ok(Self {
            header,
            section,
            binding,
            readback,
        })
    }

    fn apply(
        &mut self,
        name: &'static str,
        operation: TableRulingOperation,
    ) -> Result<OperationEvidence, Box<dyn Error>> {
        let limits = TableRulingLimits::default();
        let flow = document_flow_sha256(&self.section);
        let request = TableRulingRequest::from_draft(
            TableRulingRequestDraft {
                schema_version: TABLE_RULING_SCHEMA_VERSION.to_owned(),
                table_id: self.readback.state.table_id().clone(),
                expected_state_sha256: Some(hex(self.readback.state.canonical_sha256(limits)?)),
                expected_grid_sha256: Some(hex(self.readback.grid.canonical_sha256()?)),
                expected_document_flow_sha256: flow.clone(),
                operation,
            },
            Some(&self.readback.state),
            Some(&self.readback.grid),
            &flow,
            limits,
        )?;
        let plan = TableRulingBuilder::build(
            &request,
            Some(&self.readback.state),
            Some(&self.readback.grid),
            &flow,
            TableGridLimits::default(),
            FormulaLimits::default(),
            limits,
        )?;
        let lowered = TableRulingHwpxLowerer::lower_existing(
            &self.header,
            &self.section,
            0,
            &self.binding,
            &self.readback.state,
            &self.readback.grid,
            &plan,
            &flow,
            TableRulingHwpxLimits::default(),
        )?;
        let target_grid = grid_from_plan(&plan)?;
        let target_binding = binding_from_state(plan.after_state(), &target_grid)?;
        let reopened = TableRulingHwpxReader::read_existing(
            &lowered.header,
            &lowered.section,
            0,
            &target_binding,
            TableRulingHwpxLimits::default(),
        )?;
        if reopened.state != *plan.after_state() || reopened.grid != target_grid {
            return Err("ruling step semantic reopen differs".into());
        }
        let evidence = operation_evidence(name, &request, &plan, &lowered)?;
        self.header = lowered.header;
        self.section = lowered.section;
        self.binding = target_binding;
        self.readback = reopened;
        Ok(evidence)
    }
}

fn main() -> Result<(), Box<dyn Error>> {
    run(&Arguments::parse()?)
}

fn run(arguments: &Arguments) -> Result<(), Box<dyn Error>> {
    require_lower_sha256(&arguments.expected_ancestor_sha256)?;
    if arguments.expected_ancestor_sha256 != EXPECTED_ANCESTOR_SHA256 {
        return Err("exact ruling fixture ancestor identity differs".into());
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
    fs::create_dir(&arguments.output_directory)?;

    let ancestor = read_bounded_file(&arguments.ancestor, MAX_FIXTURE_BYTES)?;
    require_digest(&ancestor, EXPECTED_ANCESTOR_SHA256, "ancestor")?;
    let (base_header, ancestor_section) = read_parts(&ancestor)?;
    let formula_section = prepare_formula_section(&ancestor_section)?;
    let plain_section = prepare_plain_section(&formula_section)?;

    let cases = vec![
        build_outer_case(
            &ancestor,
            &base_header,
            &formula_section,
            &arguments.output_directory,
        )?,
        build_draw_topology_case(
            &ancestor,
            &base_header,
            &plain_section,
            &arguments.output_directory,
        )?,
        build_draw_diagonal_case(
            &ancestor,
            &base_header,
            &formula_section,
            &arguments.output_directory,
        )?,
        build_eraser_merge_case(
            &ancestor,
            &base_header,
            &plain_section,
            &arguments.output_directory,
        )?,
        build_eraser_transparent_case(
            &ancestor,
            &base_header,
            &formula_section,
            &arguments.output_directory,
        )?,
    ];
    let manifest = Manifest {
        schema_version: "hwpx-agent.p06-09-table-ruling-target-fixture/v1",
        source_ancestor_sha256: EXPECTED_ANCESTOR_SHA256,
        cases,
        actual_hangul_2020: false,
        render: "not_run",
        automation: "not_run",
        differential: "not_run",
    };
    let manifest_bytes = serde_json::to_vec_pretty(&manifest)?;
    write_create_new(
        &arguments.output_directory.join("fixture-manifest.json"),
        &manifest_bytes,
    )?;
    require_digest(
        &read_bounded_file(&arguments.ancestor, MAX_FIXTURE_BYTES)?,
        EXPECTED_ANCESTOR_SHA256,
        "ancestor recheck",
    )?;
    println!(
        "schema={} state=pass target_count={} actual_hangul_2020=false",
        manifest.schema_version,
        manifest.cases.len(),
    );
    Ok(())
}

fn build_outer_case(
    ancestor: &[u8],
    base_header: &[u8],
    formula_section: &[u8],
    output_directory: &Path,
) -> Result<ManifestCase, Box<dyn Error>> {
    let section = replace_once(
        &String::from_utf8(formula_section.to_vec())?,
        EMPTY_TRAILING_PARAGRAPH,
        OUTER_PLACEHOLDER_PARAGRAPH,
    )?
    .into_bytes();
    let source_section_sha256 = hex(Sha256::digest(&section));
    let template_section = outer_template_section();
    let binding = outer_binding()?;
    let template = TableRulingHwpxReader::read_existing(
        base_header,
        &template_section,
        0,
        &binding,
        TableRulingHwpxLimits::default(),
    )?;
    let flow = document_flow_sha256(&section);
    let insertion_context = TableRulingHwpxLowerer::outer_insertion_context_sha256(&section, 1)?;
    let line_sha256 = template
        .state
        .edge(TableRulingAxis::Horizontal, 0, 0)
        .and_then(|edge| edge.line_sha256.clone())
        .ok_or("outer template line is missing")?;
    let cell = template
        .state
        .cells()
        .first()
        .ok_or("outer template cell is missing")?;
    let request = TableRulingRequest::from_draft(
        TableRulingRequestDraft {
            schema_version: TABLE_RULING_SCHEMA_VERSION.to_owned(),
            table_id: template.state.table_id().clone(),
            expected_state_sha256: None,
            expected_grid_sha256: None,
            expected_document_flow_sha256: flow.clone(),
            operation: TableRulingOperation::DrawOuterRectangle {
                frame: template.state.frame(),
                initial_master_cell_id: cell.master_cell_id().clone(),
                table_properties_sha256: template.state.table_properties_sha256().to_owned(),
                initial_cell_properties: cell.properties().clone(),
                line_sha256,
                insertion_context_sha256: insertion_context,
            },
        },
        None,
        None,
        &flow,
        TableRulingLimits::default(),
    )?;
    let plan = TableRulingBuilder::build(
        &request,
        None,
        None,
        &flow,
        TableGridLimits::default(),
        FormulaLimits::default(),
        TableRulingLimits::default(),
    )?;
    let lowered = TableRulingHwpxLowerer::lower_outer_rectangle(
        base_header,
        &section,
        1,
        &template_section,
        0,
        &plan,
        &flow,
        TableRulingHwpxLimits::default(),
    )?;
    let target_grid = grid_from_plan(&plan)?;
    let target_binding = binding_from_state(plan.after_state(), &target_grid)?;
    let reopened = TableRulingHwpxReader::read_existing(
        &lowered.header,
        &lowered.section,
        1,
        &target_binding,
        TableRulingHwpxLimits::default(),
    )?;
    if reopened.state != *plan.after_state()
        || reopened.grid != target_grid
        || count_formula_fields(&lowered.section) != 1
    {
        return Err("outer target or unselected formula preservation differs".into());
    }
    let operation = operation_evidence("draw_outer_rectangle", &request, &plan, &lowered)?;
    finish_case(
        ancestor,
        &source_section_sha256,
        output_directory,
        "table-002-draw-outer",
        "TABLE-002",
        "table.draw",
        "table-002-draw-outer.hwpx",
        1,
        &lowered.header,
        &lowered.section,
        &reopened,
        vec![operation],
    )
}

fn build_draw_topology_case(
    ancestor: &[u8],
    base_header: &[u8],
    plain_section: &[u8],
    output_directory: &Path,
) -> Result<ManifestCase, Box<dyn Error>> {
    let header = header_with_dot(base_header)?;
    let binding = source_binding("draw-topology", false)?;
    let mut working = WorkingTable::open(header, plain_section.to_vec(), binding)?;
    let solid = visible_edge_line(&working.readback)?;
    let dot = working
        .readback
        .style_catalog
        .edge_line_sha256
        .iter()
        .find(|value| **value != solid)
        .cloned()
        .ok_or("dot line identity is missing")?;
    let operations = vec![
        working.apply(
            "draw_full_row",
            TableRulingOperation::DrawStroke {
                stroke: TableRulingStroke {
                    axis: TableRulingAxis::Horizontal,
                    fixed_hwpunit: 2_000,
                    start_hwpunit: 0,
                    end_hwpunit: TABLE_WIDTH,
                },
                line_sha256: solid.clone(),
                new_master_cell_ids: (0..4)
                    .map(|index| id(&format!("draw-row-new-{index}")))
                    .collect::<Result<Vec<_>, _>>()?,
                formula_policy: TableRulingFormulaPolicy::RejectRebase,
            },
        )?,
        working.apply(
            "draw_full_column",
            TableRulingOperation::DrawStroke {
                stroke: TableRulingStroke {
                    axis: TableRulingAxis::Vertical,
                    fixed_hwpunit: 5_244,
                    start_hwpunit: 0,
                    end_hwpunit: TABLE_HEIGHT,
                },
                line_sha256: solid.clone(),
                new_master_cell_ids: (0..3)
                    .map(|index| id(&format!("draw-column-new-{index}")))
                    .collect::<Result<Vec<_>, _>>()?,
                formula_policy: TableRulingFormulaPolicy::RejectRebase,
            },
        )?,
        working.apply(
            "draw_local_cell_split",
            TableRulingOperation::DrawStroke {
                stroke: TableRulingStroke {
                    axis: TableRulingAxis::Vertical,
                    fixed_hwpunit: 15_732,
                    start_hwpunit: ROW_HEIGHT,
                    end_hwpunit: TABLE_HEIGHT,
                },
                line_sha256: solid,
                new_master_cell_ids: vec![id("draw-local-new")?],
                formula_policy: TableRulingFormulaPolicy::RejectRebase,
            },
        )?,
        working.apply(
            "draw_existing_boundary_style",
            TableRulingOperation::DrawStroke {
                stroke: TableRulingStroke {
                    axis: TableRulingAxis::Horizontal,
                    fixed_hwpunit: ROW_HEIGHT,
                    start_hwpunit: 0,
                    end_hwpunit: TABLE_WIDTH,
                },
                line_sha256: dot,
                new_master_cell_ids: Vec::new(),
                formula_policy: TableRulingFormulaPolicy::RejectRebase,
            },
        )?,
    ];
    if working.readback.grid.rows() != 3
        || working.readback.grid.columns() != 6
        || working.readback.grid.master_cell_count() != 16
        || working.readback.payload_block_count != 8
        || working.readback.formula_count != 0
    {
        return Err("draw topology target shape differs".into());
    }
    finish_working_case(
        ancestor,
        plain_section,
        output_directory,
        "table-002-draw-topology",
        "TABLE-002",
        "table.draw",
        "table-002-draw-topology.hwpx",
        &working,
        operations,
    )
}

fn build_draw_diagonal_case(
    ancestor: &[u8],
    base_header: &[u8],
    formula_section: &[u8],
    output_directory: &Path,
) -> Result<ManifestCase, Box<dyn Error>> {
    let header = header_with_diagonals(base_header)?;
    let binding = source_binding("draw-diagonal", true)?;
    let mut working = WorkingTable::open(header, formula_section.to_vec(), binding)?;
    let formula_cell_id = working
        .readback
        .state
        .cells()
        .iter()
        .find(|cell| cell.formula().is_some())
        .map(|cell| cell.master_cell_id().clone())
        .ok_or("formula cell is missing")?;
    let slash = working
        .readback
        .style_catalog
        .slash_diagonal_sha256
        .first()
        .cloned()
        .ok_or("slash identity is missing")?;
    let back_slash = working
        .readback
        .style_catalog
        .back_slash_diagonal_sha256
        .first()
        .cloned()
        .ok_or("back-slash identity is missing")?;
    let operations = vec![
        working.apply(
            "draw_slash_on_formula_cell",
            TableRulingOperation::DrawDiagonal {
                master_cell_id: formula_cell_id.clone(),
                direction: TableRulingDiagonalDirection::Slash,
                line_sha256: slash,
            },
        )?,
        working.apply(
            "draw_back_slash_on_formula_cell",
            TableRulingOperation::DrawDiagonal {
                master_cell_id: formula_cell_id,
                direction: TableRulingDiagonalDirection::BackSlash,
                line_sha256: back_slash,
            },
        )?,
    ];
    if working.readback.grid.rows() != 2
        || working.readback.grid.columns() != 4
        || working.readback.grid.master_cell_count() != 8
        || working.readback.payload_block_count != 7
        || working.readback.formula_count != 1
    {
        return Err("draw diagonal formula target shape differs".into());
    }
    finish_working_case(
        ancestor,
        formula_section,
        output_directory,
        "table-002-draw-diagonals-formula",
        "TABLE-002",
        "table.draw",
        "table-002-draw-diagonals-formula.hwpx",
        &working,
        operations,
    )
}

fn build_eraser_merge_case(
    ancestor: &[u8],
    base_header: &[u8],
    plain_section: &[u8],
    output_directory: &Path,
) -> Result<ManifestCase, Box<dyn Error>> {
    let binding = source_binding("eraser-merge", false)?;
    let mut working = WorkingTable::open(base_header.to_vec(), plain_section.to_vec(), binding)?;
    let operations = vec![working.apply(
        "erase_shared_column_edge",
        TableRulingOperation::EraseStroke {
            stroke: TableRulingStroke {
                axis: TableRulingAxis::Vertical,
                fixed_hwpunit: 10_488,
                start_hwpunit: 0,
                end_hwpunit: TABLE_HEIGHT,
            },
            formula_policy: TableRulingFormulaPolicy::RejectRebase,
        },
    )?];
    if working.readback.grid.rows() != 2
        || working.readback.grid.columns() != 4
        || working.readback.grid.master_cell_count() != 6
        || working.readback.payload_block_count != 8
        || working.readback.formula_count != 0
    {
        return Err("eraser structural target shape differs".into());
    }
    finish_working_case(
        ancestor,
        plain_section,
        output_directory,
        "table-003-eraser-structural-merge",
        "TABLE-003",
        "table.eraser",
        "table-003-eraser-structural-merge.hwpx",
        &working,
        operations,
    )
}

fn build_eraser_transparent_case(
    ancestor: &[u8],
    base_header: &[u8],
    formula_section: &[u8],
    output_directory: &Path,
) -> Result<ManifestCase, Box<dyn Error>> {
    let binding = source_binding("eraser-transparent", true)?;
    let mut working = WorkingTable::open(base_header.to_vec(), formula_section.to_vec(), binding)?;
    let operations = vec![working.apply(
        "erase_outer_edge_on_formula_cell",
        TableRulingOperation::EraseStroke {
            stroke: TableRulingStroke {
                axis: TableRulingAxis::Horizontal,
                fixed_hwpunit: TABLE_HEIGHT,
                start_hwpunit: 31_464,
                end_hwpunit: TABLE_WIDTH,
            },
            formula_policy: TableRulingFormulaPolicy::RejectRebase,
        },
    )?];
    if working.readback.grid.rows() != 2
        || working.readback.grid.columns() != 4
        || working.readback.grid.master_cell_count() != 8
        || working.readback.payload_block_count != 7
        || working.readback.formula_count != 1
        || working
            .readback
            .state
            .edge(TableRulingAxis::Horizontal, 2, 3)
            .is_none_or(|edge| edge.line_sha256.is_some())
    {
        return Err("eraser transparent formula target shape differs".into());
    }
    finish_working_case(
        ancestor,
        formula_section,
        output_directory,
        "table-003-eraser-transparent-formula",
        "TABLE-003",
        "table.eraser",
        "table-003-eraser-transparent-formula.hwpx",
        &working,
        operations,
    )
}

#[allow(clippy::too_many_arguments)]
fn finish_working_case(
    ancestor: &[u8],
    source_section: &[u8],
    output_directory: &Path,
    case_id: &'static str,
    feature_id: &'static str,
    capability_id: &'static str,
    file: &'static str,
    working: &WorkingTable,
    operations: Vec<OperationEvidence>,
) -> Result<ManifestCase, Box<dyn Error>> {
    finish_case(
        ancestor,
        &hex(Sha256::digest(source_section)),
        output_directory,
        case_id,
        feature_id,
        capability_id,
        file,
        0,
        &working.header,
        &working.section,
        &working.readback,
        operations,
    )
}

#[allow(clippy::too_many_arguments)]
fn finish_case(
    ancestor: &[u8],
    source_section_sha256: &str,
    output_directory: &Path,
    case_id: &'static str,
    feature_id: &'static str,
    capability_id: &'static str,
    file: &'static str,
    selected_table_ordinal: usize,
    header: &[u8],
    section: &[u8],
    readback: &TableRulingHwpxReadback,
    operations: Vec<OperationEvidence>,
) -> Result<ManifestCase, Box<dyn Error>> {
    if operations.is_empty()
        || operations
            .iter()
            .any(|operation| operation.capability_id != capability_id)
    {
        return Err("case operation capability differs".into());
    }
    let target_package = replace_parts(ancestor, header, section, SOURCE_PREVIEW)?;
    assert_non_selected_parts_preserved(ancestor, &target_package)?;
    let (reopened_header, reopened_section) = read_parts(&target_package)?;
    if reopened_header != header || reopened_section != section {
        return Err("closed target package parts differ".into());
    }
    let target_binding = binding_from_state(&readback.state, &readback.grid)?;
    let binding = binding_evidence(&target_binding);
    write_create_new(&output_directory.join(file), &target_package)?;
    Ok(ManifestCase {
        case_id,
        feature_id,
        capability_id,
        file,
        sha256: hex(Sha256::digest(&target_package)),
        selected_table_ordinal,
        source_section_sha256: source_section_sha256.to_owned(),
        target_header_sha256: hex(Sha256::digest(header)),
        target_section_sha256: hex(Sha256::digest(section)),
        target_state_sha256: hex(readback
            .state
            .canonical_sha256(TableRulingLimits::default())?),
        target_grid_sha256: hex(readback.grid.canonical_sha256()?),
        target_rows: readback.grid.rows(),
        target_columns: readback.grid.columns(),
        target_master_cells: readback.grid.master_cell_count(),
        payload_block_count: readback.payload_block_count,
        formula_count: readback.formula_count,
        binding,
        operations,
    })
}

fn binding_evidence(binding: &TableRulingHwpxBinding) -> BindingEvidence {
    BindingEvidence {
        table_id: binding.table_id.as_str().to_owned(),
        row_boundaries_hwpunit: binding.row_boundaries_hwpunit.clone(),
        column_boundaries_hwpunit: binding.column_boundaries_hwpunit.clone(),
        cells: binding
            .cells
            .iter()
            .map(|cell| BindingCellEvidence {
                master_cell_id: cell.master_cell_id.as_str().to_owned(),
                payload_block_ids: cell
                    .payload_block_ids
                    .iter()
                    .map(|block| block.as_str().to_owned())
                    .collect(),
            })
            .collect(),
    }
}

fn operation_evidence(
    name: &'static str,
    request: &TableRulingRequest,
    plan: &TableRulingPlan,
    lowered: &TableRulingHwpxLoweredParts,
) -> Result<OperationEvidence, Box<dyn Error>> {
    let limits = TableRulingLimits::default();
    Ok(OperationEvidence {
        name,
        capability_id: plan.capability_id(),
        request_sha256: hex(Sha256::digest(request.canonical_json(limits)?)),
        plan_sha256: hex(Sha256::digest(plan.canonical_json(limits)?)),
        source_state_sha256: lowered.receipt.source_state_sha256.map(hex),
        source_grid_sha256: lowered.receipt.source_grid_sha256.map(hex),
        target_state_sha256: hex(lowered.receipt.target_state_sha256),
        target_grid_sha256: hex(lowered.receipt.target_grid_sha256),
        added_border_fill_count: lowered.receipt.added_border_fill_count,
    })
}

fn source_binding(
    prefix: &str,
    formula_last_cell: bool,
) -> Result<TableRulingHwpxBinding, Box<dyn Error>> {
    let mut cells = Vec::new();
    for index in 0..8 {
        let payload_block_ids = if formula_last_cell && index == 7 {
            Vec::new()
        } else {
            vec![id(&format!("{prefix}-payload-{index}"))?]
        };
        cells.push(TableRulingHwpxCellBinding {
            master_cell_id: id(&format!("{prefix}-cell-{index}"))?,
            payload_block_ids,
        });
    }
    Ok(TableRulingHwpxBinding {
        table_id: id(&format!("{prefix}-table"))?,
        row_boundaries_hwpunit: vec![0, ROW_HEIGHT, TABLE_HEIGHT],
        column_boundaries_hwpunit: vec![0, 10_488, 20_976, 31_464, TABLE_WIDTH],
        cells,
    })
}

fn outer_binding() -> Result<TableRulingHwpxBinding, Box<dyn Error>> {
    Ok(TableRulingHwpxBinding {
        table_id: id("draw-outer-table")?,
        row_boundaries_hwpunit: vec![0, TABLE_HEIGHT],
        column_boundaries_hwpunit: vec![0, TABLE_WIDTH],
        cells: vec![TableRulingHwpxCellBinding {
            master_cell_id: id("draw-outer-cell")?,
            payload_block_ids: Vec::new(),
        }],
    })
}

fn binding_from_state(
    state: &TableRulingState,
    grid: &TableGrid,
) -> Result<TableRulingHwpxBinding, Box<dyn Error>> {
    let mut cells = Vec::new();
    cells.try_reserve_exact(grid.master_cell_count())?;
    for span in grid.master_cells() {
        let cell = state
            .cell(&span.master_cell_id)
            .ok_or("target state cell is missing")?;
        cells.push(TableRulingHwpxCellBinding {
            master_cell_id: span.master_cell_id.clone(),
            payload_block_ids: cell
                .payload()
                .iter()
                .map(|block| block.block_id.clone())
                .collect(),
        });
    }
    Ok(TableRulingHwpxBinding {
        table_id: state.table_id().clone(),
        row_boundaries_hwpunit: state.row_boundaries_hwpunit().to_vec(),
        column_boundaries_hwpunit: state.column_boundaries_hwpunit().to_vec(),
        cells,
    })
}

fn grid_from_plan(plan: &TableRulingPlan) -> Result<TableGrid, Box<dyn Error>> {
    Ok(TableGrid::new(
        plan.after_grid().rows(),
        plan.after_grid().columns(),
        plan.after_grid().master_cells().to_vec(),
        TableGridLimits::default(),
    )?)
}

fn visible_edge_line(readback: &TableRulingHwpxReadback) -> Result<String, Box<dyn Error>> {
    readback
        .state
        .edge(TableRulingAxis::Horizontal, 0, 0)
        .and_then(|edge| edge.line_sha256.clone())
        .ok_or_else(|| "visible source edge line is missing".into())
}

fn prepare_formula_section(bytes: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    let mut source = String::from_utf8(bytes.to_vec())?;
    source = replace_once(&source, "repeatHeader=\"1\"", "repeatHeader=\"0\"")?;
    source = replace_once(
        &source,
        "height=\"2564\" heightRelTo=\"ABSOLUTE\"",
        "height=\"8000\" heightRelTo=\"ABSOLUTE\"",
    )?;
    if source.matches("height=\"282\"").count() != 8 {
        return Err("source cell height cardinality differs".into());
    }
    source = source.replace("height=\"282\"", "height=\"4000\"");
    for value in ["2", "3", "4", "5"] {
        source = replace_first(&source, "<hp:t>0</hp:t>", &format!("<hp:t>{value}</hp:t>"))?;
    }
    if source.matches(FORMULA_RUN_CONTENT).count() != 1
        || source.matches("<hp:t>0</hp:t>").count() != 0
    {
        return Err("source formula or operand shape differs".into());
    }
    Ok(source.into_bytes())
}

fn prepare_plain_section(formula_section: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    let source = String::from_utf8(formula_section.to_vec())?;
    let plain = replace_once(&source, FORMULA_RUN_CONTENT, "<hp:t>52</hp:t>")?;
    if plain.contains("<hp:fieldBegin") || plain.matches("<hp:t>52</hp:t>").count() != 1 {
        return Err("plain ruling source formula removal differs".into());
    }
    Ok(plain.into_bytes())
}

fn header_with_dot(bytes: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    let dot = concat!(
        r#"<hh:borderFill id="4" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">"#,
        r#"<hh:slash type="NONE" Crooked="0" isCounter="0"/>"#,
        r#"<hh:backSlash type="NONE" Crooked="0" isCounter="0"/>"#,
        r##"<hh:leftBorder type="DOT" width="0.12 mm" color="#000000"/>"##,
        r##"<hh:rightBorder type="DOT" width="0.12 mm" color="#000000"/>"##,
        r##"<hh:topBorder type="DOT" width="0.12 mm" color="#000000"/>"##,
        r##"<hh:bottomBorder type="DOT" width="0.12 mm" color="#000000"/>"##,
        r##"<hh:diagonal type="SOLID" width="0.12 mm" color="#000000"/>"##,
        r#"</hh:borderFill>"#,
    );
    append_border_fills(bytes, 3, 4, dot)
}

fn header_with_diagonals(bytes: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    let diagonals = concat!(
        r#"<hh:borderFill id="4" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">"#,
        r#"<hh:slash type="CENTER" Crooked="0" isCounter="0"/>"#,
        r#"<hh:backSlash type="NONE" Crooked="0" isCounter="0"/>"#,
        r##"<hh:leftBorder type="SOLID" width="0.12 mm" color="#000000"/>"##,
        r##"<hh:rightBorder type="SOLID" width="0.12 mm" color="#000000"/>"##,
        r##"<hh:topBorder type="SOLID" width="0.12 mm" color="#000000"/>"##,
        r##"<hh:bottomBorder type="SOLID" width="0.12 mm" color="#000000"/>"##,
        r##"<hh:diagonal type="SOLID" width="0.12 mm" color="#000000"/>"##,
        r#"</hh:borderFill>"#,
        r#"<hh:borderFill id="5" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">"#,
        r#"<hh:slash type="NONE" Crooked="0" isCounter="0"/>"#,
        r#"<hh:backSlash type="CENTER" Crooked="0" isCounter="0"/>"#,
        r##"<hh:leftBorder type="SOLID" width="0.12 mm" color="#000000"/>"##,
        r##"<hh:rightBorder type="SOLID" width="0.12 mm" color="#000000"/>"##,
        r##"<hh:topBorder type="SOLID" width="0.12 mm" color="#000000"/>"##,
        r##"<hh:bottomBorder type="SOLID" width="0.12 mm" color="#000000"/>"##,
        r##"<hh:diagonal type="SOLID" width="0.12 mm" color="#000000"/>"##,
        r#"</hh:borderFill>"#,
    );
    append_border_fills(bytes, 3, 5, diagonals)
}

fn append_border_fills(
    bytes: &[u8],
    old_count: usize,
    new_count: usize,
    additions: &str,
) -> Result<Vec<u8>, Box<dyn Error>> {
    let source = String::from_utf8(bytes.to_vec())?;
    let old = format!("<hh:borderFills itemCnt=\"{old_count}\">");
    let new = format!("<hh:borderFills itemCnt=\"{new_count}\">");
    let updated = replace_once(&source, &old, &new)?;
    Ok(replace_once(
        &updated,
        "</hh:borderFills>",
        &format!("{additions}</hh:borderFills>"),
    )?
    .into_bytes())
}

fn outer_template_section() -> Vec<u8> {
    format!(
        concat!(
            r#"<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">"#,
            r#"<hp:p id="700" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0">"#,
            r#"<hp:tbl id="700" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="0" rowCnt="1" colCnt="1" cellSpacing="0" borderFillIDRef="3" noAdjust="0">"#,
            r#"<hp:sz width="{TABLE_WIDTH}" widthRelTo="ABSOLUTE" height="{TABLE_HEIGHT}" heightRelTo="ABSOLUTE" protect="0"/>"#,
            r#"<hp:pos treatAsChar="0" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="0" horzOffset="0"/>"#,
            r#"<hp:outMargin left="283" right="283" top="283" bottom="283"/>"#,
            r#"<hp:inMargin left="510" right="510" top="141" bottom="141"/>"#,
            r#"<hp:tr><hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="3">"#,
            r#"<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">"#,
            r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="0"><hp:t/></hp:run></hp:p>"#,
            r#"</hp:subList><hp:cellAddr colAddr="0" rowAddr="0"/><hp:cellSpan colSpan="1" rowSpan="1"/>"#,
            r#"<hp:cellSz width="{TABLE_WIDTH}" height="{TABLE_HEIGHT}"/>"#,
            r#"<hp:cellMargin left="510" right="510" top="141" bottom="141"/></hp:tc></hp:tr></hp:tbl>"#,
            r#"<hp:t/></hp:run></hp:p></hs:sec>"#,
        ),
        TABLE_WIDTH = TABLE_WIDTH,
        TABLE_HEIGHT = TABLE_HEIGHT,
    )
    .into_bytes()
}

fn read_parts(source: &[u8]) -> Result<(Vec<u8>, Vec<u8>), Box<dyn Error>> {
    let mut archive = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    Ok((
        read_part(&mut archive, "Contents/header.xml")?,
        read_part(&mut archive, "Contents/section0.xml")?,
    ))
}

fn read_part(
    archive: &mut BoundedZipReader<Cursor<&[u8]>>,
    path: &str,
) -> Result<Vec<u8>, Box<dyn Error>> {
    let index = archive
        .entries()
        .iter()
        .find(|entry| entry.path.as_str() == path)
        .map(|entry| entry.index)
        .ok_or("required package part is missing")?;
    Ok(archive.read_entry(index)?)
}

fn replace_parts(
    source: &[u8],
    header: &[u8],
    section: &[u8],
    preview: &[u8],
) -> Result<Vec<u8>, Box<dyn Error>> {
    let mut archive = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let entries = archive.entries().to_vec();
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    let mut replacements = [0_u8; 3];
    for entry in entries {
        let path = entry.path.as_str();
        let method = match entry.compression {
            Compression::Stored => CompressionMethod::Stored,
            Compression::Deflated => CompressionMethod::Deflated,
        };
        let bytes = match path {
            "Contents/header.xml" => {
                replacements[0] += 1;
                header.to_vec()
            }
            "Contents/section0.xml" => {
                replacements[1] += 1;
                section.to_vec()
            }
            "Preview/PrvText.txt" => {
                replacements[2] += 1;
                preview.to_vec()
            }
            _ => archive.read_entry(entry.index)?,
        };
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
    if replacements != [1, 1, 1] {
        return Err("package replacement cardinality differs".into());
    }
    Ok(writer.finish()?.into_inner())
}

fn assert_non_selected_parts_preserved(source: &[u8], target: &[u8]) -> Result<(), Box<dyn Error>> {
    let mut source_archive = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let mut target_archive = BoundedZipReader::open(Cursor::new(target), PackageLimits::default())?;
    let source_entries = source_archive.entries().to_vec();
    let target_entries = target_archive.entries().to_vec();
    if source_entries.len() != target_entries.len() {
        return Err("target package entry count differs".into());
    }
    for (source_entry, target_entry) in source_entries.iter().zip(&target_entries) {
        if source_entry.path != target_entry.path
            || source_entry.compression != target_entry.compression
        {
            return Err("target package graph differs".into());
        }
        let path = source_entry.path.as_str();
        if !matches!(
            path,
            "Contents/header.xml" | "Contents/section0.xml" | "Preview/PrvText.txt"
        ) && source_archive.read_entry(source_entry.index)?
            != target_archive.read_entry(target_entry.index)?
        {
            return Err(format!("non-selected package part changed: {path}").into());
        }
    }
    Ok(())
}

fn write_create_new(path: &Path, bytes: &[u8]) -> Result<(), Box<dyn Error>> {
    let mut file = OpenOptions::new().write(true).create_new(true).open(path)?;
    file.write_all(bytes)?;
    file.sync_all()?;
    Ok(())
}

fn read_bounded_file(path: &Path, limit: u64) -> Result<Vec<u8>, Box<dyn Error>> {
    let metadata = fs::symlink_metadata(path)?;
    if !metadata.file_type().is_file()
        || metadata.file_type().is_symlink()
        || metadata.len() > limit
    {
        return Err("input is not a bounded regular file".into());
    }
    Ok(fs::read(path)?)
}

fn require_digest(bytes: &[u8], expected: &str, label: &str) -> Result<(), Box<dyn Error>> {
    if hex(Sha256::digest(bytes)) != expected {
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

fn replace_once(source: &str, before: &str, after: &str) -> Result<String, Box<dyn Error>> {
    if source.matches(before).count() != 1 {
        return Err(format!("exact replacement cardinality differs: {before}").into());
    }
    Ok(source.replacen(before, after, 1))
}

fn replace_first(source: &str, before: &str, after: &str) -> Result<String, Box<dyn Error>> {
    if !source.contains(before) {
        return Err(format!("replacement marker is missing: {before}").into());
    }
    Ok(source.replacen(before, after, 1))
}

fn count_formula_fields(source: &[u8]) -> usize {
    source
        .windows(b"type=\"FORMULA\"".len())
        .filter(|window| *window == b"type=\"FORMULA\"")
        .count()
}

fn document_flow_sha256(section: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.p06-09-table-ruling-target-flow/v1\0");
    digest.update(section);
    hex(digest.finalize())
}

fn id(value: &str) -> Result<LogicalId, Box<dyn Error>> {
    Ok(LogicalId::parse(value)?)
}

fn hex(value: impl AsRef<[u8]>) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let bytes = value.as_ref();
    let mut output = String::with_capacity(bytes.len().saturating_mul(2));
    for byte in bytes {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn exact_ruling_target_case_set_is_complete() {
        let cases = [
            ("table-002-draw-outer", "TABLE-002", "table.draw"),
            ("table-002-draw-topology", "TABLE-002", "table.draw"),
            (
                "table-002-draw-diagonals-formula",
                "TABLE-002",
                "table.draw",
            ),
            (
                "table-003-eraser-structural-merge",
                "TABLE-003",
                "table.eraser",
            ),
            (
                "table-003-eraser-transparent-formula",
                "TABLE-003",
                "table.eraser",
            ),
        ];
        assert_eq!(cases.len(), 5);
        assert_eq!(cases.iter().filter(|case| case.1 == "TABLE-002").count(), 3);
        assert_eq!(cases.iter().filter(|case| case.1 == "TABLE-003").count(), 2);
    }

    #[test]
    fn header_catalog_extensions_are_dense_and_directional() {
        let source = br#"<hh:borderFills itemCnt="3"></hh:borderFills>"#;
        let dot = String::from_utf8(header_with_dot(source).unwrap()).unwrap();
        assert!(dot.contains("itemCnt=\"4\""));
        assert!(dot.contains("id=\"4\""));
        assert!(dot.contains("type=\"DOT\""));

        let diagonals = String::from_utf8(header_with_diagonals(source).unwrap()).unwrap();
        assert!(diagonals.contains("itemCnt=\"5\""));
        assert_eq!(diagonals.matches("type=\"CENTER\"").count(), 2);
        assert_eq!(diagonals.matches("<hh:borderFill id=").count(), 2);
    }

    #[test]
    fn outer_template_has_exact_one_by_one_shape() {
        let template = String::from_utf8(outer_template_section()).unwrap();
        assert!(template.contains("rowCnt=\"1\" colCnt=\"1\""));
        assert!(template.contains("width=\"41952\" height=\"8000\""));
        assert_eq!(template.matches("<hp:tbl ").count(), 1);
        assert_eq!(template.matches("<hp:tc ").count(), 1);
        assert_eq!(template.matches("<hp:t/>").count(), 2);
    }
}
