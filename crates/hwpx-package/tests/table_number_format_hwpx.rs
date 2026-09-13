use domain_ir::{
    CellCoordinate, FormulaAstDraft, FormulaCellDraft, FormulaError, FormulaLimitConfig,
    FormulaLimits, FormulaNumberFormat, LogicalId, TABLE_FORMULA_SCHEMA_VERSION,
    TABLE_GRID_SCHEMA_VERSION, TABLE_NUMBER_FORMAT_SCHEMA_VERSION, TableCellSpan, TableGrid,
    TableGridDraft, TableGridLimits, TableNumberFormatBuilder, TableNumberFormatCellDraft,
    TableNumberFormatLimits, TableNumberFormatPlan, TableNumberFormatRequest,
    TableNumberFormatRequestDraft, TableNumberFormatState, TableNumberFormatStateDraft,
};
use hwpx_package::{
    TABLE_NUMBER_FORMAT_HWPX_PROFILE_ID, TABLE_NUMBER_FORMAT_HWPX_SCHEMA_VERSION,
    TableFormulaHwpxLimits, TableNumberFormatHwpxError, TableNumberFormatHwpxLowerer,
    TableNumberFormatHwpxReadback, TableNumberFormatHwpxReader, TableNumberFormatHwpxRequest,
    TableNumberFormatHwpxRequestDraft, TablePaginationHwpxLimits, TablePaginationHwpxReader,
};

type TestResult = Result<(), Box<dyn std::error::Error>>;

const OWNER: CellCoordinate = CellCoordinate { row: 0, column: 2 };
const FLOW: &str = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";

fn formula_limits() -> Result<FormulaLimits, FormulaError> {
    FormulaLimits::new(FormulaLimitConfig {
        rows: 16,
        columns: 16,
        ..FormulaLimitConfig::default()
    })
}

fn section(visible: &str, last_result: &str, result_format: &str) -> Vec<u8> {
    format!(
        r#"<?xml version="1.0" encoding="UTF-8" standalone="yes" ?><hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"><hp:tbl rowCnt="1" colCnt="3"><hp:tr><hp:tc><hp:subList><hp:p><hp:run><hp:t>1200</hp:t></hp:run></hp:p></hp:subList><hp:cellAddr colAddr="0" rowAddr="0"/><hp:cellSpan colSpan="1" rowSpan="1"/></hp:tc><hp:tc><hp:subList><hp:p><hp:run><hp:t>3400</hp:t></hp:run></hp:p></hp:subList><hp:cellAddr colAddr="1" rowAddr="0"/><hp:cellSpan colSpan="1" rowSpan="1"/></hp:tc><hp:tc><hp:subList><hp:p><hp:run><hp:ctrl><hp:fieldBegin id="100" type="FORMULA" name="" editable="0" dirty="0" zorder="-1" fieldid="101"><hp:parameters cnt="5" name=""><hp:integerParam name="Prop">8</hp:integerParam><hp:stringParam name="Command">=SUM(LEFT)??{result_format};;{last_result}</hp:stringParam><hp:stringParam name="Formula">=SUM(LEFT)</hp:stringParam><hp:stringParam name="ResultFormat">{result_format}</hp:stringParam><hp:stringParam name="LastResult">{last_result}</hp:stringParam></hp:parameters></hp:fieldBegin></hp:ctrl><hp:t>{visible}</hp:t><hp:ctrl><hp:fieldEnd beginIDRef="100" fieldid="101"/></hp:ctrl><hp:t/></hp:run></hp:p></hp:subList><hp:cellAddr colAddr="2" rowAddr="0"/><hp:cellSpan colSpan="1" rowSpan="1"/></hp:tc></hp:tr></hp:tbl></hs:sec>"#
    )
    .into_bytes()
}

fn paginated_section(
    visible: &str,
    last_result: &str,
    result_format: &str,
) -> Result<Vec<u8>, std::string::FromUtf8Error> {
    Ok(
        String::from_utf8(section(visible, last_result, result_format))?
            .replace(
                "<hp:tbl rowCnt=\"1\" colCnt=\"3\">",
                concat!(
                    "<hp:tbl lock=\"0\" pageBreak=\"CELL\" repeatHeader=\"0\" rowCnt=\"1\" ",
                    "colCnt=\"3\" cellSpacing=\"0\" noAdjust=\"0\">",
                    "<hp:sz/><hp:pos/><hp:outMargin/><hp:inMargin/>"
                ),
            )
            .replace("<hp:tc>", "<hp:tc header=\"0\">")
            .into_bytes(),
    )
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

fn id(value: &str) -> Result<LogicalId, Box<dyn std::error::Error>> {
    Ok(LogicalId::parse(value)?)
}

fn grid() -> Result<TableGrid, Box<dyn std::error::Error>> {
    Ok(TableGrid::from_draft(
        TableGridDraft {
            schema_version: TABLE_GRID_SCHEMA_VERSION.to_owned(),
            rows: 1,
            columns: 3,
            master_cells: vec![
                TableCellSpan {
                    master_cell_id: id("left-a")?,
                    row: 0,
                    column: 0,
                    row_span: 1,
                    column_span: 1,
                },
                TableCellSpan {
                    master_cell_id: id("left-b")?,
                    row: 0,
                    column: 1,
                    row_span: 1,
                    column_span: 1,
                },
                TableCellSpan {
                    master_cell_id: id("formula")?,
                    row: 0,
                    column: 2,
                    row_span: 1,
                    column_span: 1,
                },
            ],
        },
        TableGridLimits::default(),
    )?)
}

fn read(section: &[u8]) -> Result<TableNumberFormatHwpxReadback, TableNumberFormatHwpxError> {
    TableNumberFormatHwpxReader::read_selected_in_section(
        section,
        0,
        &[OWNER],
        TableFormulaHwpxLimits::default(),
        formula_limits().map_err(TableNumberFormatHwpxError::Formula)?,
    )
}

fn plan(
    source: &TableNumberFormatHwpxReadback,
    target_format: FormulaNumberFormat,
) -> Result<TableNumberFormatPlan, Box<dyn std::error::Error>> {
    let grid = grid()?;
    let formula_limits = formula_limits()?;
    let source_formula = &source.selected_formulas()[0];
    let cells = grid
        .master_cells()
        .iter()
        .enumerate()
        .map(|(index, span)| {
            let coordinate = CellCoordinate {
                row: span.row,
                column: span.column,
            };
            Ok(TableNumberFormatCellDraft {
                master_cell_id: span.master_cell_id.clone(),
                coordinate,
                non_formula_payload_sha256: digest(['a', 'b', 'c'][index]),
                properties_sha256: digest(['d', 'e', 'f'][index]),
                formula: (coordinate == OWNER).then(|| FormulaCellDraft {
                    schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
                    owner: source_formula.owner(),
                    ast: FormulaAstDraft {
                        schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
                        expression: source_formula.ast().expression().clone(),
                    },
                    cache: source_formula.cache().clone(),
                    number_format: source_formula.number_format(),
                }),
            })
        })
        .collect::<Result<Vec<_>, Box<dyn std::error::Error>>>()?;
    let number_limits = TableNumberFormatLimits::default();
    let state = TableNumberFormatState::from_draft(
        TableNumberFormatStateDraft {
            schema_version: TABLE_NUMBER_FORMAT_SCHEMA_VERSION.to_owned(),
            table_id: id("table-main")?,
            grid_sha256: hex(grid.canonical_sha256()?),
            table_properties_sha256: digest('9'),
            cells,
        },
        &grid,
        number_limits,
        formula_limits,
    )?;
    let request = TableNumberFormatRequest::from_draft(
        TableNumberFormatRequestDraft {
            schema_version: TABLE_NUMBER_FORMAT_SCHEMA_VERSION.to_owned(),
            table_id: state.table_id().clone(),
            selected_cells: vec![OWNER],
            target_format,
            expected_source_state_sha256: hex(state.canonical_sha256(number_limits)?),
            expected_document_flow_sha256: FLOW.to_owned(),
        },
        &state,
        &grid,
        FLOW,
        number_limits,
        formula_limits,
    )?;
    Ok(TableNumberFormatBuilder::build(
        &request,
        &state,
        &grid,
        FLOW,
        number_limits,
        formula_limits,
    )?)
}

fn request(
    source_bytes: &[u8],
    source: &TableNumberFormatHwpxReadback,
    plan: &TableNumberFormatPlan,
) -> Result<TableNumberFormatHwpxRequest, Box<dyn std::error::Error>> {
    Ok(TableNumberFormatHwpxRequest::from_draft(
        TableNumberFormatHwpxRequestDraft {
            schema_version: TABLE_NUMBER_FORMAT_HWPX_SCHEMA_VERSION.to_owned(),
            table_ordinal: 0,
            expected_section_sha256: hex(source.section_sha256()),
            expected_source_state_sha256: hex(source.selected_state_sha256()),
            expected_source_grid_sha256: hex(source.grid_sha256()),
            expected_document_flow_sha256: FLOW.to_owned(),
            expected_plan_sha256: hex(plan.canonical_sha256(TableNumberFormatLimits::default())?),
        },
        source_bytes,
        plan,
        FLOW,
        TableFormulaHwpxLimits::default(),
        TableNumberFormatLimits::default(),
        formula_limits()?,
    )?)
}

fn lower(
    source_bytes: &[u8],
    source: &TableNumberFormatHwpxReadback,
    plan: &TableNumberFormatPlan,
) -> Result<(Vec<u8>, hwpx_package::TableNumberFormatHwpxLoweringReceipt), Box<dyn std::error::Error>>
{
    let request = request(source_bytes, source, plan)?;
    Ok(TableNumberFormatHwpxLowerer::lower_in_section_with_receipt(
        &request,
        source_bytes,
        plan,
        FLOW,
        TableFormulaHwpxLimits::default(),
        TableNumberFormatLimits::default(),
        formula_limits()?,
    )?)
}

#[test]
fn integer_format_changes_exact_native_fields_and_preserves_everything_else() -> TestResult {
    let source_bytes = section("4,600", "4,600", "%g,");
    let source = read(&source_bytes)?;
    assert_eq!(source.profile_id(), TABLE_NUMBER_FORMAT_HWPX_PROFILE_ID);
    assert_eq!(source.formula_field_count(), 1);
    assert_eq!(source.selected_native_grouping(), &[true]);
    assert_eq!(
        source.selected_formulas()[0].number_format(),
        FormulaNumberFormat::General
    );
    let plan = plan(
        &source,
        FormulaNumberFormat::Number {
            decimal_places: 2,
            use_grouping: false,
        },
    )?;
    let (output, receipt) = lower(&source_bytes, &source, &plan)?;
    assert_eq!(output, section("4600.00", "4,600.00", "%.2f,"));
    assert_eq!(receipt.capability_id(), "table.number_format");
    assert_eq!(receipt.selected_formula_cells(), 1);
    assert_eq!(receipt.modified_text_count(), 4);
    assert!(receipt.grid_preserved());
    assert!(receipt.document_flow_preserved());
    assert_ne!(
        receipt.source_section_sha256(),
        receipt.output_section_sha256()
    );
    let after = read(&output)?;
    assert_eq!(
        after.selected_formulas()[0].number_format(),
        FormulaNumberFormat::Number {
            decimal_places: 2,
            use_grouping: false,
        }
    );
    assert_eq!(
        after.selected_formulas()[0].ast(),
        source.selected_formulas()[0].ast()
    );
    assert_eq!(
        after.selected_formulas()[0].cache(),
        source.selected_formulas()[0].cache()
    );
    Ok(())
}

#[test]
fn every_number_format_preserves_page_split_semantics() -> TestResult {
    let source_bytes = paginated_section("4,600", "4,600", "%g,")?;
    let source = read(&source_bytes)?;
    let source_pagination = TablePaginationHwpxReader::read_in_section(
        &source_bytes,
        0,
        TablePaginationHwpxLimits::default(),
    )?;

    let mut target_formats = vec![FormulaNumberFormat::General];
    for decimal_places in 0..=4 {
        for use_grouping in [false, true] {
            target_formats.push(FormulaNumberFormat::Number {
                decimal_places,
                use_grouping,
            });
        }
    }
    for target_format in target_formats {
        let format_plan = plan(&source, target_format)?;
        let (output, _) = lower(&source_bytes, &source, &format_plan)?;
        let target_pagination = TablePaginationHwpxReader::read_in_section(
            &output,
            0,
            TablePaginationHwpxLimits::default(),
        )?;
        assert_eq!(source_pagination.page_split, target_pagination.page_split);
        assert_eq!(
            source_pagination.repeat_header_rows,
            target_pagination.repeat_header_rows
        );
        assert_eq!(source_pagination.caption, target_pagination.caption);
        assert_eq!(
            (source_pagination.row_count, source_pagination.column_count),
            (target_pagination.row_count, target_pagination.column_count)
        );
    }
    Ok(())
}

#[test]
fn general_preserves_native_grouping_and_same_format_is_idempotent() -> TestResult {
    let number_bytes = section("4600.00", "4,600.00", "%.2f,");
    let number = read(&number_bytes)?;
    let to_general = plan(&number, FormulaNumberFormat::General)?;
    let (general_bytes, receipt) = lower(&number_bytes, &number, &to_general)?;
    assert_eq!(general_bytes, section("4600", "4,600", "%g,"));
    assert_eq!(receipt.modified_text_count(), 4);
    assert_eq!(read(&general_bytes)?.selected_native_grouping(), &[false]);

    let general = read(&general_bytes)?;
    let same = plan(&general, FormulaNumberFormat::General)?;
    let (same_bytes, same_receipt) = lower(&general_bytes, &general, &same)?;
    assert_eq!(same_bytes, general_bytes);
    assert_eq!(same_receipt.modified_text_count(), 0);
    Ok(())
}

#[test]
fn all_exact_number_tokens_and_negative_integer_are_supported() -> TestResult {
    for decimal_places in 0..=4 {
        for use_grouping in [false, true] {
            let source_bytes = section("-4,600", "-4,600", "%g,");
            let source = read(&source_bytes)?;
            let plan = plan(
                &source,
                FormulaNumberFormat::Number {
                    decimal_places,
                    use_grouping,
                },
            )?;
            let (output, _) = lower(&source_bytes, &source, &plan)?;
            let after = read(&output)?;
            assert_eq!(
                after.selected_formulas()[0].number_format(),
                FormulaNumberFormat::Number {
                    decimal_places,
                    use_grouping,
                }
            );
            assert_eq!(after.selected_native_grouping(), &[use_grouping]);
        }
    }
    Ok(())
}

#[test]
fn request_and_build_reject_section_state_grid_flow_and_plan_drift() -> TestResult {
    let source_bytes = section("4,600", "4,600", "%g,");
    let source = read(&source_bytes)?;
    let target = FormulaNumberFormat::Number {
        decimal_places: 2,
        use_grouping: true,
    };
    let format_plan = plan(&source, target)?;
    let request = request(&source_bytes, &source, &format_plan)?;

    let mut changed = source_bytes.clone();
    let position = changed
        .windows(4)
        .position(|window| window == b"1200")
        .ok_or("operand marker missing")?;
    changed[position + 3] = b'1';
    assert!(matches!(
        TableNumberFormatHwpxLowerer::lower_in_section_with_receipt(
            &request,
            &changed,
            &format_plan,
            FLOW,
            TableFormulaHwpxLimits::default(),
            TableNumberFormatLimits::default(),
            formula_limits()?,
        ),
        Err(TableNumberFormatHwpxError::SectionBindingMismatch)
    ));
    let other_flow = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789";
    assert!(matches!(
        TableNumberFormatHwpxLowerer::lower_in_section_with_receipt(
            &request,
            &source_bytes,
            &format_plan,
            other_flow,
            TableFormulaHwpxLimits::default(),
            TableNumberFormatLimits::default(),
            formula_limits()?,
        ),
        Err(TableNumberFormatHwpxError::FlowBindingMismatch)
    ));
    let other_plan = plan(
        &source,
        FormulaNumberFormat::Number {
            decimal_places: 3,
            use_grouping: true,
        },
    )?;
    assert!(matches!(
        TableNumberFormatHwpxLowerer::lower_in_section_with_receipt(
            &request,
            &source_bytes,
            &other_plan,
            FLOW,
            TableFormulaHwpxLimits::default(),
            TableNumberFormatLimits::default(),
            formula_limits()?,
        ),
        Err(TableNumberFormatHwpxError::PlanBindingMismatch)
    ));

    let mut wrong = TableNumberFormatHwpxRequestDraft {
        schema_version: TABLE_NUMBER_FORMAT_HWPX_SCHEMA_VERSION.to_owned(),
        table_ordinal: 0,
        expected_section_sha256: hex(source.section_sha256()),
        expected_source_state_sha256: hex(source.selected_state_sha256()),
        expected_source_grid_sha256: hex(source.grid_sha256()),
        expected_document_flow_sha256: FLOW.to_owned(),
        expected_plan_sha256: hex(format_plan.canonical_sha256(TableNumberFormatLimits::default())?),
    };
    wrong.expected_source_state_sha256.replace_range(..1, "f");
    assert!(matches!(
        TableNumberFormatHwpxRequest::from_draft(
            wrong,
            &source_bytes,
            &format_plan,
            FLOW,
            TableFormulaHwpxLimits::default(),
            TableNumberFormatLimits::default(),
            formula_limits()?,
        ),
        Err(TableNumberFormatHwpxError::RequestBindingMismatch)
    ));
    Ok(())
}

#[test]
fn unsupported_native_and_target_profiles_fail_closed() -> TestResult {
    for invalid in [
        section("4,600", "4,600", "%e,"),
        section("4600", "4600", "%g,"),
        section("4,600.5", "4,600.5", "%.1f,"),
        section("46,00", "46,00", "%g,"),
    ] {
        assert!(matches!(
            read(&invalid),
            Err(TableNumberFormatHwpxError::UnsupportedNativeProfile
                | TableNumberFormatHwpxError::FormulaHwpx(_))
        ));
    }
    let source_bytes = section("4,600", "4,600", "%g,");
    let source = read(&source_bytes)?;
    for target in [
        FormulaNumberFormat::Number {
            decimal_places: 5,
            use_grouping: true,
        },
        FormulaNumberFormat::Percent { decimal_places: 2 },
        FormulaNumberFormat::Scientific { decimal_places: 2 },
    ] {
        let plan = plan(&source, target)?;
        assert!(matches!(
            request(&source_bytes, &source, &plan),
            Err(error) if error.downcast_ref::<TableNumberFormatHwpxError>()
                .is_some_and(|value| matches!(value, TableNumberFormatHwpxError::UnsupportedTargetFormat))
        ));
    }
    Ok(())
}

#[test]
fn strict_json_and_debug_redaction_fail_closed() -> TestResult {
    let source_bytes = section("4,600", "4,600", "%g,");
    let source = read(&source_bytes)?;
    let plan = plan(
        &source,
        FormulaNumberFormat::Number {
            decimal_places: 2,
            use_grouping: true,
        },
    )?;
    let request = request(&source_bytes, &source, &plan)?;
    let valid = request.canonical_json(TableFormulaHwpxLimits::default())?;
    let parsed = TableNumberFormatHwpxRequest::from_json(
        &valid,
        &source_bytes,
        &plan,
        FLOW,
        TableFormulaHwpxLimits::default(),
        TableNumberFormatLimits::default(),
        formula_limits()?,
    )?;
    assert_eq!(parsed.table_ordinal(), 0);
    assert_eq!(parsed.expected_document_flow_sha256(), FLOW);

    for invalid in [
        String::from_utf8(valid.clone())?.replacen('{', "{\"table_ordinal\":0,", 1),
        String::from_utf8(valid)?.replacen('{', "{\"unknown\":true,", 1),
    ] {
        assert!(matches!(
            TableNumberFormatHwpxRequest::from_json(
                invalid.as_bytes(),
                &source_bytes,
                &plan,
                FLOW,
                TableFormulaHwpxLimits::default(),
                TableNumberFormatLimits::default(),
                formula_limits()?,
            ),
            Err(TableNumberFormatHwpxError::InvalidJson)
        ));
    }
    let debug = format!("{source:?} {request:?}");
    assert!(debug.contains("<redacted>"));
    assert!(!debug.contains(FLOW));
    assert!(!debug.contains("4,600"));
    assert_eq!(
        TableNumberFormatHwpxError::SectionBindingMismatch.code(),
        "table_number_format_hwpx_section_binding_mismatch"
    );
    assert_eq!(
        TableNumberFormatHwpxError::UnsupportedNativeProfile.code(),
        "table_number_format_hwpx_unsupported_native_profile"
    );
    Ok(())
}
