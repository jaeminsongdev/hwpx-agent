use domain_ir::{
    CellCoordinate, FormulaAstDraft, FormulaCachePolicy, FormulaCell, FormulaCellDraft,
    FormulaGridDimensions, FormulaGridEdit, FormulaLimits, LogicalId, TABLE_FORMULA_SCHEMA_VERSION,
    TABLE_RULING_SCHEMA_VERSION, TABLE_STRUCTURE_SCHEMA_VERSION, TableGrid, TableGridLimits,
    TableRulingAxis, TableRulingCellDraft, TableRulingEdge, TableRulingFrame, TableRulingLimits,
    TableRulingStateDraft, TableStructureOperation, TableStructureRequestDraft,
};
use hwpx_package::{
    BoundedZipReader, Compression, PackageGraph, PackageGraphLimits, PackageLimits,
    TABLE_STRUCTURE_HWPX_SCHEMA_VERSION, TableLayoutHwpxError, TableLayoutHwpxLimits,
    TableLayoutHwpxReader, TableRulingHwpxBinding, TableRulingHwpxCellBinding,
    TableRulingHwpxReader, TableStructureHwpxBuilder, TableStructureHwpxError,
    TableStructureHwpxLimits, TableStructureHwpxLowerer, TableStructureHwpxReadback,
    TableStructureHwpxReader, TableStructureHwpxRequest, TableStructureHwpxRequestDraft,
};
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, DateTime, ZipWriter};

type TestResult<T = ()> = Result<T, Box<dyn std::error::Error>>;

const HEADER: &[u8] = include_bytes!("../src/hancom_2020_minimal_header.xml");
const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const SECTION_NS: &str = "http://www.hancom.co.kr/hwpml/2011/section";
const CONTAINER: &str = r#"<?xml version="1.0" encoding="UTF-8"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
  <rootfiles><rootfile full-path="Contents/content.hpf" media-type="application/oebps-package+xml"/></rootfiles>
</container>"#;
const OPF: &str = r#"<?xml version="1.0" encoding="UTF-8"?>
<opf:package xmlns:opf="http://www.idpf.org/2007/opf" version="2.0">
  <opf:manifest>
    <opf:item id="header" href="header.xml" media-type="application/xml"/>
    <opf:item id="section0" href="section0.xml" media-type="application/xml"/>
    <opf:item id="opaque" href="opaque.bin" media-type="application/octet-stream"/>
  </opf:manifest>
  <opf:spine><opf:itemref idref="section0" linear="yes"/></opf:spine>
</opf:package>"#;

fn id(value: &str) -> TestResult<LogicalId> {
    Ok(LogicalId::parse(value)?)
}

fn digest(character: char) -> String {
    std::iter::repeat_n(character, 64).collect()
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

fn paragraph(value: &str) -> String {
    format!(
        r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>{value}</hp:t></hp:run></hp:p>"#
    )
}

fn formula_paragraph() -> &'static str {
    concat!(
        r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:ctrl>"#,
        r#"<hp:fieldBegin id="101" type="FORMULA" name="" editable="0" dirty="0" zorder="-1" fieldid="202">"#,
        r#"<hp:parameters cnt="5" name=""><hp:integerParam name="Prop">8</hp:integerParam>"#,
        r#"<hp:stringParam name="Command">=SUM(LEFT)??%g,;;7</hp:stringParam>"#,
        r#"<hp:stringParam name="Formula">=SUM(LEFT)</hp:stringParam>"#,
        r#"<hp:stringParam name="ResultFormat">%g,</hp:stringParam>"#,
        r#"<hp:stringParam name="LastResult">7</hp:stringParam></hp:parameters>"#,
        r#"</hp:fieldBegin></hp:ctrl><hp:t>7</hp:t><hp:ctrl>"#,
        r#"<hp:fieldEnd beginIDRef="101" fieldid="202"/></hp:ctrl><hp:t/></hp:run></hp:p>"#,
    )
}

#[allow(clippy::too_many_arguments)]
fn cell(
    row: u32,
    column: u32,
    row_span: u32,
    column_span: u32,
    width: u32,
    height: u32,
    header: bool,
    payload: &str,
) -> String {
    format!(
        concat!(
            r#"<hp:tc name="" header="{header}" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="1">"#,
            r#"<hp:cellAddr colAddr="{column}" rowAddr="{row}"/>"#,
            r#"<hp:cellSpan colSpan="{column_span}" rowSpan="{row_span}"/>"#,
            r#"<hp:cellSz width="{width}" height="{height}"/>"#,
            r#"<hp:cellMargin left="0" right="0" top="0" bottom="0"/>"#,
            r#"<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">"#,
            "{payload}</hp:subList></hp:tc>"
        ),
        header = u8::from(header),
        column = column,
        row = row,
        column_span = column_span,
        row_span = row_span,
        width = width,
        height = height,
        payload = payload,
    )
}

fn caption() -> &'static str {
    concat!(
        r#"<hp:caption side="TOP" fullSz="0" width="42520" gap="850" lastWidth="42520">"#,
        r#"<hp:subList><hp:p><hp:run><hp:t>CAPTION &amp; LABEL</hp:t></hp:run></hp:p></hp:subList></hp:caption>"#,
    )
}

fn table(
    native_id: u32,
    rows: &[Vec<String>],
    row_count: u32,
    column_count: u32,
    repeat_header: bool,
    with_caption: bool,
) -> String {
    let mut body = String::new();
    for cells in rows {
        body.push_str("<hp:tr>");
        body.push_str(&cells.concat());
        body.push_str("</hp:tr>");
    }
    let caption = if with_caption { caption() } else { "" };
    format!(
        concat!(
            r#"<hp:tbl id="{native_id}" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="TABLE" repeatHeader="{repeat_header}" rowCnt="{row_count}" colCnt="{column_count}" cellSpacing="0" borderFillIDRef="1" noAdjust="0">"#,
            r#"<hp:sz width="{width}" widthRelTo="ABSOLUTE" height="{height}" heightRelTo="ABSOLUTE" protect="0"/>"#,
            r#"<hp:pos treatAsChar="0" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="2000" horzOffset="1000"/>"#,
            r#"<hp:outMargin left="0" right="0" top="0" bottom="0"/>"#,
            "{caption}",
            r#"<hp:inMargin left="0" right="0" top="0" bottom="0"/>"#,
            "{body}</hp:tbl>"
        ),
        native_id = native_id,
        repeat_header = u8::from(repeat_header),
        row_count = row_count,
        column_count = column_count,
        width = column_count * 1000,
        height = row_count * 500,
        caption = caption,
        body = body,
    )
}

fn wrapper(paragraph_id: u32, table: &str) -> String {
    format!(
        r#"<hp:p id="{paragraph_id}" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0">{table}</hp:run></hp:p>"#
    )
}

fn text_wrapper(paragraph_id: u32, value: &str) -> String {
    format!(
        r#"<hp:p id="{paragraph_id}" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>{value}</hp:t></hp:run></hp:p>"#
    )
}

fn section(parts: &[String]) -> Vec<u8> {
    format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{}</hs:sec>"#,
        parts.concat()
    )
    .into_bytes()
}

fn ordinary_table(rows: u32, columns: u32, repeat_header: bool, caption: bool) -> String {
    let mut result = Vec::new();
    for row in 0..rows {
        let mut cells = Vec::new();
        for column in 0..columns {
            cells.push(cell(
                row,
                column,
                1,
                1,
                1000,
                500,
                repeat_header && row == 0,
                &paragraph(&format!("R{row}C{column}")),
            ));
        }
        result.push(cells);
    }
    table(700, &result, rows, columns, repeat_header, caption)
}

fn formula_table() -> String {
    let mut rows = Vec::new();
    for row in 0..2 {
        let mut cells = Vec::new();
        for column in 0..3 {
            let payload = if row == 1 && column == 2 {
                formula_paragraph().to_owned()
            } else {
                paragraph(&format!("{}", row * 3 + column + 1))
            };
            cells.push(cell(row, column, 1, 1, 1000, 500, false, &payload));
        }
        rows.push(cells);
    }
    table(700, &rows, 2, 3, false, false)
}

fn merged_formula_table() -> String {
    table(
        700,
        &[
            vec![
                cell(0, 0, 1, 1, 1000, 500, false, &paragraph("1")),
                cell(0, 1, 1, 1, 1000, 500, false, &paragraph("2")),
                cell(0, 2, 1, 1, 1000, 500, false, &paragraph("3")),
            ],
            vec![
                cell(1, 0, 1, 1, 1000, 500, false, &paragraph("4")),
                cell(1, 1, 1, 2, 2000, 500, false, formula_paragraph()),
            ],
        ],
        2,
        3,
        false,
        false,
    )
}

fn wrapped_section(table: &str) -> Vec<u8> {
    section(&[wrapper(10, table), text_wrapper(90, "TAIL")])
}

fn binding(
    prefix: &str,
    rows: u32,
    columns: u32,
    formula: bool,
) -> TestResult<TableRulingHwpxBinding> {
    let mut cells = Vec::new();
    for row in 0..rows {
        for column in 0..columns {
            let formula_owner = formula && row == rows - 1 && column == columns - 1;
            cells.push(TableRulingHwpxCellBinding {
                master_cell_id: id(&format!("{prefix}-cell-{row}-{column}"))?,
                payload_block_ids: if formula_owner {
                    Vec::new()
                } else {
                    vec![id(&format!("{prefix}-payload-{row}-{column}"))?]
                },
            });
        }
    }
    Ok(TableRulingHwpxBinding {
        table_id: id(&format!("{prefix}-table"))?,
        row_boundaries_hwpunit: (0..=rows).map(|value| value * 500).collect(),
        column_boundaries_hwpunit: (0..=columns).map(|value| value * 1000).collect(),
        cells,
    })
}

fn read(
    section: &[u8],
    binding: &TableRulingHwpxBinding,
) -> TestResult<TableStructureHwpxReadback> {
    Ok(TableStructureHwpxReader::read_existing(
        HEADER,
        section,
        0,
        binding,
        TableStructureHwpxLimits::default(),
    )?)
}

fn formula_edit(
    operation: TableStructureOperation,
    source: &TableGrid,
    index: u32,
    count: u32,
) -> FormulaGridEdit {
    let before = FormulaGridDimensions {
        rows: source.rows(),
        columns: source.columns(),
    };
    match operation {
        TableStructureOperation::InsertRows => FormulaGridEdit::InsertRows {
            before,
            index,
            count,
        },
        TableStructureOperation::InsertColumns => FormulaGridEdit::InsertColumns {
            before,
            index,
            count,
        },
        TableStructureOperation::DeleteRows => FormulaGridEdit::DeleteRows {
            before,
            index,
            count,
        },
        TableStructureOperation::DeleteColumns => FormulaGridEdit::DeleteColumns {
            before,
            index,
            count,
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

fn boundaries(
    source: &[u32],
    insert: bool,
    index: u32,
    count: u32,
    inserted_size: u32,
) -> TestResult<Vec<u32>> {
    let mut sizes = source
        .windows(2)
        .map(|pair| pair[1].checked_sub(pair[0]).ok_or("invalid boundary"))
        .collect::<Result<Vec<_>, _>>()?;
    let index = usize::try_from(index)?;
    let count = usize::try_from(count)?;
    if insert {
        sizes.splice(index..index, std::iter::repeat_n(inserted_size, count));
    } else {
        sizes.drain(index..index + count);
    }
    let mut output = vec![0_u32];
    for size in sizes {
        output.push(
            output
                .last()
                .copied()
                .ok_or("missing boundary")?
                .checked_add(size)
                .ok_or("boundary overflow")?,
        );
    }
    Ok(output)
}

fn target_grid(
    source: &TableGrid,
    operation: TableStructureOperation,
    index: u32,
    count: u32,
    new_ids: Vec<LogicalId>,
) -> TestResult<TableGrid> {
    let result = match operation {
        TableStructureOperation::InsertRows => {
            source.insert_rows(index, count, new_ids, TableGridLimits::default())?
        }
        TableStructureOperation::InsertColumns => {
            source.insert_columns(index, count, new_ids, TableGridLimits::default())?
        }
        TableStructureOperation::DeleteRows => {
            source.delete_rows(index, count, TableGridLimits::default())?
        }
        TableStructureOperation::DeleteColumns => {
            source.delete_columns(index, count, TableGridLimits::default())?
        }
    };
    Ok(result.into_parts().0)
}

fn uniform_edges(
    source: &TableStructureHwpxReadback,
    target: &TableGrid,
) -> TestResult<Vec<TableRulingEdge>> {
    let line = source
        .ruling
        .state
        .edges()
        .first()
        .ok_or("source edge missing")?
        .line_sha256
        .clone();
    if !source
        .ruling
        .state
        .edges()
        .iter()
        .all(|edge| edge.line_sha256 == line)
    {
        return Err("fixture edges are not uniform".into());
    }
    let mut edges = Vec::new();
    for boundary in 0..=target.rows() {
        for offset in 0..target.columns() {
            edges.push(TableRulingEdge {
                axis: TableRulingAxis::Horizontal,
                boundary,
                offset,
                line_sha256: line.clone(),
            });
        }
    }
    for boundary in 0..=target.columns() {
        for offset in 0..target.rows() {
            edges.push(TableRulingEdge {
                axis: TableRulingAxis::Vertical,
                boundary,
                offset,
                line_sha256: line.clone(),
            });
        }
    }
    Ok(edges)
}

fn request_draft(
    source: &TableStructureHwpxReadback,
    operation: TableStructureOperation,
    index: u32,
    count: u32,
    new_ids: Vec<LogicalId>,
    inserted_property_source: CellCoordinate,
) -> TestResult<TableStructureHwpxRequestDraft> {
    let target_grid = target_grid(
        &source.ruling.grid,
        operation,
        index,
        count,
        new_ids.clone(),
    )?;
    let (row_boundaries, column_boundaries) = target_boundaries(source, operation, index, count)?;
    let edit = formula_edit(operation, &source.ruling.grid, index, count);
    let cells = target_cells(source, &target_grid, edit, inserted_property_source)?;
    Ok(TableStructureHwpxRequestDraft {
        schema_version: TABLE_STRUCTURE_HWPX_SCHEMA_VERSION.to_owned(),
        table_ordinal: source.table_ordinal,
        expected_header_sha256: hex(source.ruling.header_sha256),
        expected_section_sha256: hex(source.ruling.section_sha256),
        expected_wrapper_sha256: hex(source.wrapper_sha256),
        structure: TableStructureRequestDraft {
            schema_version: TABLE_STRUCTURE_SCHEMA_VERSION.to_owned(),
            operation,
            index,
            count,
            new_master_cell_ids: new_ids,
            expected_source_state_sha256: hex(source
                .ruling
                .state
                .canonical_sha256(TableRulingLimits::default())?),
            expected_source_grid_sha256: hex(source.ruling.grid.canonical_sha256()?),
            expected_document_flow_sha256: digest('f'),
            target_document_flow_sha256: digest('e'),
            target_state: TableRulingStateDraft {
                schema_version: TABLE_RULING_SCHEMA_VERSION.to_owned(),
                table_id: source.ruling.state.table_id().clone(),
                frame: TableRulingFrame {
                    left_hwpunit: source.ruling.state.frame().left_hwpunit,
                    top_hwpunit: source.ruling.state.frame().top_hwpunit,
                    width_hwpunit: *column_boundaries.last().ok_or("missing column boundary")?,
                    height_hwpunit: *row_boundaries.last().ok_or("missing row boundary")?,
                },
                grid_sha256: hex(target_grid.canonical_sha256()?),
                table_properties_sha256: source.ruling.state.table_properties_sha256().to_owned(),
                row_boundaries_hwpunit: row_boundaries,
                column_boundaries_hwpunit: column_boundaries,
                edges: uniform_edges(source, &target_grid)?,
                cells,
            },
        },
    })
}

fn target_boundaries(
    source: &TableStructureHwpxReadback,
    operation: TableStructureOperation,
    index: u32,
    count: u32,
) -> TestResult<(Vec<u32>, Vec<u32>)> {
    let is_rows = matches!(
        operation,
        TableStructureOperation::InsertRows | TableStructureOperation::DeleteRows
    );
    let insert = matches!(
        operation,
        TableStructureOperation::InsertRows | TableStructureOperation::InsertColumns
    );
    let row_boundaries = if is_rows {
        boundaries(
            source.ruling.state.row_boundaries_hwpunit(),
            insert,
            index,
            count,
            500,
        )?
    } else {
        source.ruling.state.row_boundaries_hwpunit().to_vec()
    };
    let column_boundaries = if is_rows {
        source.ruling.state.column_boundaries_hwpunit().to_vec()
    } else {
        boundaries(
            source.ruling.state.column_boundaries_hwpunit(),
            insert,
            index,
            count,
            1000,
        )?
    };
    Ok((row_boundaries, column_boundaries))
}

fn target_cells(
    source: &TableStructureHwpxReadback,
    target_grid: &TableGrid,
    edit: FormulaGridEdit,
    inserted_property_source: CellCoordinate,
) -> TestResult<Vec<TableRulingCellDraft>> {
    let inserted_properties = source
        .ruling
        .grid
        .master_cell_at(inserted_property_source)
        .ok()
        .and_then(|span| source.ruling.state.cell(&span.master_cell_id))
        .ok_or("inserted property template missing")?
        .properties()
        .clone();
    let mut cells = Vec::new();
    for span in target_grid.master_cells() {
        let coordinate = CellCoordinate {
            row: span.row,
            column: span.column,
        };
        if let Some(before) = source.ruling.state.cell(&span.master_cell_id) {
            let formula = before
                .formula()
                .map(|value| {
                    value.apply_grid_edit(
                        edit,
                        FormulaCachePolicy::Update,
                        Some(value.cache().clone()),
                        FormulaLimits::default(),
                    )
                })
                .transpose()?
                .as_ref()
                .map(formula_draft);
            cells.push(TableRulingCellDraft {
                master_cell_id: span.master_cell_id.clone(),
                coordinate,
                payload: before.payload().to_vec(),
                properties: before.properties().clone(),
                formula,
            });
        } else {
            cells.push(TableRulingCellDraft {
                master_cell_id: span.master_cell_id.clone(),
                coordinate,
                payload: Vec::new(),
                properties: inserted_properties.clone(),
                formula: None,
            });
        }
    }
    Ok(cells)
}

fn admitted(
    source: &TableStructureHwpxReadback,
    draft: TableStructureHwpxRequestDraft,
) -> TestResult<(
    TableStructureHwpxRequest,
    hwpx_package::TableStructureHwpxPlan,
)> {
    let limits = TableStructureHwpxLimits::default();
    let request = TableStructureHwpxRequest::from_draft(draft, source, &digest('f'), limits)?;
    let plan = TableStructureHwpxBuilder::build(&request, source, &digest('f'), limits)?;
    Ok((request, plan))
}

fn new_ids(prefix: &str, count: u32) -> TestResult<Vec<LogicalId>> {
    (0..count)
        .map(|index| id(&format!("{prefix}-{index}")))
        .collect()
}

#[test]
fn all_four_structural_operations_lower_and_reopen_exactly() -> TestResult {
    let limits = TableStructureHwpxLimits::default();
    for (operation, index, new_count, expected_rows, expected_columns) in [
        (TableStructureOperation::InsertRows, 1, 3, 4, 3),
        (TableStructureOperation::InsertColumns, 1, 3, 3, 4),
        (TableStructureOperation::DeleteRows, 1, 0, 2, 3),
        (TableStructureOperation::DeleteColumns, 1, 0, 3, 2),
    ] {
        let section = wrapped_section(&ordinary_table(3, 3, false, false));
        let source_binding = binding("source", 3, 3, false)?;
        let source = read(&section, &source_binding)?;
        let ids = new_ids("inserted", new_count)?;
        let draft = request_draft(
            &source,
            operation,
            index,
            1,
            ids,
            CellCoordinate { row: 0, column: 0 },
        )?;
        let (request, plan) = admitted(&source, draft)?;
        let lowered = TableStructureHwpxLowerer::lower_existing(
            HEADER,
            &section,
            &source_binding,
            &digest('f'),
            &request,
            &plan,
            limits,
        )?;
        let reopened = TableStructureHwpxReader::read_existing(
            &lowered.header,
            &lowered.section,
            0,
            &lowered.binding,
            limits,
        )?;
        assert_eq!(
            (reopened.ruling.grid.rows(), reopened.ruling.grid.columns()),
            (expected_rows, expected_columns)
        );
        assert_eq!(reopened.ruling.state, *plan.domain().after_state());
        assert_eq!(lowered.receipt.source_table_count, 1);
        assert_eq!(lowered.receipt.target_table_count, 1);
        assert_eq!(
            lowered.receipt.preserved_payload_block_count,
            if matches!(
                operation,
                TableStructureOperation::InsertRows | TableStructureOperation::InsertColumns
            ) {
                9
            } else {
                6
            }
        );
        assert!(
            String::from_utf8(lowered.section)?
                .ends_with(&(text_wrapper(90, "TAIL") + "</hs:sec>"))
        );
    }
    Ok(())
}

#[test]
fn formula_rebases_after_column_insertion_and_owner_deletion_is_explicit() -> TestResult {
    let limits = TableStructureHwpxLimits::default();
    let section = wrapped_section(&formula_table());
    let source_binding = binding("formula", 2, 3, true)?;
    let source = read(&section, &source_binding)?;
    let draft = request_draft(
        &source,
        TableStructureOperation::InsertColumns,
        1,
        1,
        new_ids("inserted-column", 2)?,
        CellCoordinate { row: 0, column: 0 },
    )?;
    let (request, plan) = admitted(&source, draft)?;
    let lowered = TableStructureHwpxLowerer::lower_existing(
        HEADER,
        &section,
        &source_binding,
        &digest('f'),
        &request,
        &plan,
        limits,
    )?;
    let formula = plan
        .domain()
        .after_state()
        .cells()
        .iter()
        .find_map(|cell| cell.formula())
        .ok_or("formula missing")?;
    assert_eq!(formula.owner(), CellCoordinate { row: 1, column: 3 });
    assert_eq!(
        formula.ast().canonical_formula(FormulaLimits::default())?,
        "SUM(A2:C2)"
    );
    assert_eq!(lowered.receipt.formula_rebased_count, 1);
    assert_eq!(lowered.receipt.formula_modified_text_count, 3);
    assert!(String::from_utf8(lowered.section.clone())?.contains("=SUM(LEFT)??%g,;;7"));

    let delete_draft = request_draft(
        &source,
        TableStructureOperation::DeleteRows,
        1,
        1,
        Vec::new(),
        CellCoordinate { row: 0, column: 0 },
    )?;
    let (delete_request, delete_plan) = admitted(&source, delete_draft)?;
    let deleted = TableStructureHwpxLowerer::lower_existing(
        HEADER,
        &section,
        &source_binding,
        &digest('f'),
        &delete_request,
        &delete_plan,
        limits,
    )?;
    assert_eq!(deleted.receipt.formula_deleted_count, 1);
    assert_eq!(deleted.receipt.formula_modified_text_count, 0);
    assert!(!String::from_utf8(deleted.section)?.contains("fieldBegin"));
    Ok(())
}

#[test]
fn merged_formula_span_survives_row_insertion_with_exact_rebase() -> TestResult {
    let section = wrapped_section(&merged_formula_table());
    let binding = TableRulingHwpxBinding {
        table_id: id("merged-formula-table")?,
        row_boundaries_hwpunit: vec![0, 500, 1000],
        column_boundaries_hwpunit: vec![0, 1000, 2000, 3000],
        cells: vec![
            TableRulingHwpxCellBinding {
                master_cell_id: id("mfc-0-0")?,
                payload_block_ids: vec![id("mfp-0-0")?],
            },
            TableRulingHwpxCellBinding {
                master_cell_id: id("mfc-0-1")?,
                payload_block_ids: vec![id("mfp-0-1")?],
            },
            TableRulingHwpxCellBinding {
                master_cell_id: id("mfc-0-2")?,
                payload_block_ids: vec![id("mfp-0-2")?],
            },
            TableRulingHwpxCellBinding {
                master_cell_id: id("mfc-1-0")?,
                payload_block_ids: vec![id("mfp-1-0")?],
            },
            TableRulingHwpxCellBinding {
                master_cell_id: id("mfc-formula")?,
                payload_block_ids: Vec::new(),
            },
        ],
    };
    let source = read(&section, &binding)?;
    let draft = request_draft(
        &source,
        TableStructureOperation::InsertRows,
        0,
        1,
        new_ids("merged-formula-insert", 3)?,
        CellCoordinate { row: 0, column: 0 },
    )?;
    let (request, plan) = admitted(&source, draft)?;
    let lowered = TableStructureHwpxLowerer::lower_existing(
        HEADER,
        &section,
        &binding,
        &digest('f'),
        &request,
        &plan,
        TableStructureHwpxLimits::default(),
    )?;
    let reopened = read(&lowered.section, &lowered.binding)?;
    let formula_cell = reopened
        .ruling
        .state
        .cells()
        .iter()
        .find(|cell| cell.master_cell_id().as_str() == "mfc-formula")
        .ok_or("merged formula cell missing")?;
    let formula = formula_cell.formula().ok_or("merged formula missing")?;
    assert_eq!(formula.owner(), CellCoordinate { row: 2, column: 1 });
    assert_eq!(
        formula.ast().canonical_formula(FormulaLimits::default())?,
        "SUM(A3:A3)"
    );
    let span = reopened.ruling.grid.master_cell_at(formula.owner())?;
    assert_eq!(span.row_span, 1);
    assert_eq!(span.column_span, 2);
    assert_eq!(lowered.receipt.formula_rebased_count, 1);
    assert_eq!(lowered.receipt.formula_modified_text_count, 3);
    assert!(String::from_utf8(lowered.section)?.contains("=SUM(LEFT)??%g,;;7"));
    Ok(())
}

#[test]
fn repeat_header_page_split_caption_and_native_wrapper_identity_are_preserved() -> TestResult {
    let section = wrapped_section(&ordinary_table(2, 2, true, true));
    let binding = binding("pagination", 2, 2, false)?;
    assert_eq!(
        TableLayoutHwpxReader::read_in_section(&section, 0, TableLayoutHwpxLimits::default()),
        Err(TableLayoutHwpxError::UnsupportedShape)
    );
    assert!(
        TableRulingHwpxReader::read_existing(
            HEADER,
            &section,
            0,
            &binding,
            TableStructureHwpxLimits::default().ruling,
        )
        .is_err()
    );
    let source = read(&section, &binding)?;
    assert_eq!(source.pagination.repeat_header_rows, 1);
    assert!(source.pagination.caption.is_some());
    let draft = request_draft(
        &source,
        TableStructureOperation::InsertRows,
        0,
        1,
        new_ids("header-row", 2)?,
        CellCoordinate { row: 0, column: 0 },
    )?;
    let (request, plan) = admitted(&source, draft)?;
    assert_eq!(plan.target_repeat_header_rows(), 2);
    let lowered = TableStructureHwpxLowerer::lower_existing(
        HEADER,
        &section,
        &binding,
        &digest('f'),
        &request,
        &plan,
        TableStructureHwpxLimits::default(),
    )?;
    let reopened = read(&lowered.section, &lowered.binding)?;
    assert_eq!(reopened.pagination.repeat_header_rows, 2);
    assert_eq!(reopened.pagination.page_split, source.pagination.page_split);
    assert_eq!(reopened.pagination.caption, source.pagination.caption);
    assert_eq!(reopened.wrapper_paragraph_id, 10);
    assert_eq!(reopened.native_table_id, 700);
    assert_eq!(
        String::from_utf8(lowered.section)?
            .matches("CAPTION &amp; LABEL")
            .count(),
        1
    );
    Ok(())
}

#[test]
fn span_conflicts_and_removing_every_repeat_header_fail_closed() -> TestResult {
    let merged = table(
        700,
        &[
            vec![
                cell(0, 0, 2, 1, 1000, 1000, false, &paragraph("MERGED")),
                cell(0, 1, 1, 1, 1000, 500, false, &paragraph("A")),
            ],
            vec![cell(1, 1, 1, 1, 1000, 500, false, &paragraph("B"))],
        ],
        2,
        2,
        false,
        false,
    );
    let section = wrapped_section(&merged);
    let merged_binding = TableRulingHwpxBinding {
        table_id: id("merged-table")?,
        row_boundaries_hwpunit: vec![0, 500, 1000],
        column_boundaries_hwpunit: vec![0, 1000, 2000],
        cells: vec![
            TableRulingHwpxCellBinding {
                master_cell_id: id("merged-cell")?,
                payload_block_ids: vec![id("merged-payload")?],
            },
            TableRulingHwpxCellBinding {
                master_cell_id: id("a-cell")?,
                payload_block_ids: vec![id("a-payload")?],
            },
            TableRulingHwpxCellBinding {
                master_cell_id: id("b-cell")?,
                payload_block_ids: vec![id("b-payload")?],
            },
        ],
    };
    let source = read(&section, &merged_binding)?;
    assert!(
        request_draft(
            &source,
            TableStructureOperation::InsertRows,
            1,
            1,
            new_ids("conflict", 2)?,
            CellCoordinate { row: 0, column: 0 },
        )
        .is_err()
    );

    let repeated_section = wrapped_section(&ordinary_table(2, 2, true, false));
    let repeated_binding = binding("repeat", 2, 2, false)?;
    let repeated = read(&repeated_section, &repeated_binding)?;
    let draft = request_draft(
        &repeated,
        TableStructureOperation::DeleteRows,
        0,
        1,
        Vec::new(),
        CellCoordinate { row: 0, column: 0 },
    )?;
    assert!(matches!(
        TableStructureHwpxRequest::from_draft(
            draft,
            &repeated,
            &digest('f'),
            TableStructureHwpxLimits::default(),
        ),
        Err(TableStructureHwpxError::UnsupportedPaginationTransition)
    ));
    Ok(())
}

#[test]
fn part_flow_plan_json_and_debug_tampering_fail_closed() -> TestResult {
    let section = wrapped_section(&ordinary_table(3, 3, false, false));
    let binding = binding("secret-source", 3, 3, false)?;
    let source = read(&section, &binding)?;
    let mut draft = request_draft(
        &source,
        TableStructureOperation::InsertRows,
        1,
        1,
        new_ids("secret-insert", 3)?,
        CellCoordinate { row: 0, column: 0 },
    )?;
    draft.expected_section_sha256 = digest('0');
    assert!(matches!(
        TableStructureHwpxRequest::from_draft(
            draft,
            &source,
            &digest('f'),
            TableStructureHwpxLimits::default(),
        ),
        Err(TableStructureHwpxError::SourceBindingMismatch)
    ));

    let draft = request_draft(
        &source,
        TableStructureOperation::InsertRows,
        1,
        1,
        new_ids("secret-insert", 3)?,
        CellCoordinate { row: 0, column: 0 },
    )?;
    let (request, plan) = admitted(&source, draft)?;
    assert!(
        TableStructureHwpxBuilder::build(
            &request,
            &source,
            &digest('0'),
            TableStructureHwpxLimits::default(),
        )
        .is_err()
    );
    let alternate_draft = request_draft(
        &source,
        TableStructureOperation::DeleteRows,
        1,
        1,
        Vec::new(),
        CellCoordinate { row: 0, column: 0 },
    )?;
    let (_, alternate_plan) = admitted(&source, alternate_draft)?;
    assert!(matches!(
        TableStructureHwpxLowerer::lower_existing(
            HEADER,
            &section,
            &binding,
            &digest('f'),
            &request,
            &alternate_plan,
            TableStructureHwpxLimits::default(),
        ),
        Err(TableStructureHwpxError::PlanBindingMismatch)
    ));
    let json = request.canonical_json(TableStructureHwpxLimits::default())?;
    let text = String::from_utf8(json)?;
    let unknown = text.replacen('{', r#"{"unknown":0,"#, 1);
    assert!(matches!(
        TableStructureHwpxRequest::from_json(
            unknown.as_bytes(),
            &source,
            &digest('f'),
            TableStructureHwpxLimits::default(),
        ),
        Err(TableStructureHwpxError::InvalidJson)
    ));
    let duplicate = text.replacen(
        r#""schema_version":"hwpx-agent.table-structure-hwpx/v1""#,
        r#""schema_version":"hwpx-agent.table-structure-hwpx/v1","schema_version":"hwpx-agent.table-structure-hwpx/v1""#,
        1,
    );
    assert!(matches!(
        TableStructureHwpxRequest::from_json(
            duplicate.as_bytes(),
            &source,
            &digest('f'),
            TableStructureHwpxLimits::default(),
        ),
        Err(TableStructureHwpxError::InvalidJson)
    ));
    let debug = format!("{source:?}{request:?}{plan:?}");
    assert!(!debug.contains("secret-source"));
    assert!(!debug.contains("secret-insert"));
    assert!(!debug.contains(&digest('f')));
    Ok(())
}

#[test]
fn non_top_level_wrapper_is_rejected() -> TestResult {
    let raw = format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{}</hs:sec>"#,
        ordinary_table(2, 2, false, false)
    )
    .into_bytes();
    assert!(matches!(
        TableStructureHwpxReader::read_existing(
            HEADER,
            &raw,
            0,
            &binding("raw", 2, 2, false)?,
            TableStructureHwpxLimits::default(),
        ),
        Err(TableStructureHwpxError::UnsupportedWrapper | TableStructureHwpxError::Ruling(_))
    ));
    Ok(())
}

#[test]
fn closed_package_reopen_preserves_unselected_parts() -> TestResult {
    let section = wrapped_section(&ordinary_table(3, 3, false, false));
    let binding = binding("package", 3, 3, false)?;
    let source = read(&section, &binding)?;
    let draft = request_draft(
        &source,
        TableStructureOperation::InsertColumns,
        2,
        1,
        new_ids("package-column", 3)?,
        CellCoordinate { row: 0, column: 0 },
    )?;
    let (request, plan) = admitted(&source, draft)?;
    let lowered = TableStructureHwpxLowerer::lower_existing(
        HEADER,
        &section,
        &binding,
        &digest('f'),
        &request,
        &plan,
        TableStructureHwpxLimits::default(),
    )?;
    let source_package = package(HEADER, &section)?;
    let immutable_source = source_package.clone();
    let target_package = replace_parts(&source_package, &lowered.header, &lowered.section)?;
    assert_eq!(source_package, immutable_source);
    assert_non_section_parts_preserved(&source_package, &target_package)?;

    let mut reader = BoundedZipReader::open(Cursor::new(target_package), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    assert_eq!(graph.spine.len(), 1);
    let header = read_entry_by_path(&mut reader, "Contents/header.xml")?;
    let section = read_entry_by_path(&mut reader, "Contents/section0.xml")?;
    let reopened = TableStructureHwpxReader::read_existing(
        &header,
        &section,
        0,
        &lowered.binding,
        TableStructureHwpxLimits::default(),
    )?;
    assert_eq!(reopened.ruling.state, *plan.domain().after_state());
    assert_eq!(reopened.ruling.grid, *plan.domain().after_grid());
    Ok(())
}

fn package(header: &[u8], section: &[u8]) -> Result<Vec<u8>, zip::result::ZipError> {
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for (path, bytes, method) in [
        (
            "mimetype",
            b"application/hwp+zip".as_slice(),
            CompressionMethod::Stored,
        ),
        (
            "version.xml",
            b"<version/>".as_slice(),
            CompressionMethod::Stored,
        ),
        (
            "META-INF/container.xml",
            CONTAINER.as_bytes(),
            CompressionMethod::Deflated,
        ),
        (
            "Contents/content.hpf",
            OPF.as_bytes(),
            CompressionMethod::Deflated,
        ),
        ("Contents/header.xml", header, CompressionMethod::Deflated),
        (
            "Contents/section0.xml",
            section,
            CompressionMethod::Deflated,
        ),
        (
            "Contents/opaque.bin",
            b"opaque".as_slice(),
            CompressionMethod::Stored,
        ),
    ] {
        let options = SimpleFileOptions::default()
            .compression_method(method)
            .last_modified_time(DateTime::default())
            .system(zip::System::Unix)
            .unix_permissions(0o644);
        writer.start_file(path, options)?;
        writer.write_all(bytes)?;
    }
    Ok(writer.finish()?.into_inner())
}

fn replace_parts(source: &[u8], header: &[u8], section: &[u8]) -> TestResult<Vec<u8>> {
    let mut reader = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let entries = reader.entries().to_vec();
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for entry in entries {
        let path = entry.path.as_str();
        let bytes = match path {
            "Contents/header.xml" => header.to_vec(),
            "Contents/section0.xml" => section.to_vec(),
            _ => reader.read_entry(entry.index)?,
        };
        let method = match entry.compression {
            Compression::Stored => CompressionMethod::Stored,
            Compression::Deflated => CompressionMethod::Deflated,
        };
        let options = SimpleFileOptions::default()
            .compression_method(method)
            .last_modified_time(DateTime::default())
            .system(zip::System::Unix)
            .unix_permissions(0o644);
        writer.start_file(path, options)?;
        writer.write_all(&bytes)?;
    }
    Ok(writer.finish()?.into_inner())
}

fn assert_non_section_parts_preserved(source: &[u8], target: &[u8]) -> TestResult {
    let mut source = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let mut target = BoundedZipReader::open(Cursor::new(target), PackageLimits::default())?;
    for entry in source.entries().to_vec() {
        let path = entry.path.as_str();
        if !matches!(path, "Contents/header.xml" | "Contents/section0.xml") {
            let target_index = target
                .entries()
                .iter()
                .find(|candidate| candidate.path.as_str() == path)
                .map(|candidate| candidate.index)
                .ok_or("target package entry missing")?;
            assert_eq!(
                source.read_entry(entry.index)?,
                target.read_entry(target_index)?
            );
        }
    }
    Ok(())
}

fn read_entry_by_path(
    reader: &mut BoundedZipReader<Cursor<Vec<u8>>>,
    path: &str,
) -> TestResult<Vec<u8>> {
    let index = reader
        .entries()
        .iter()
        .find(|entry| entry.path.as_str() == path)
        .map(|entry| entry.index)
        .ok_or("package entry missing")?;
    Ok(reader.read_entry(index)?)
}
use std::io::{Cursor, Write};
