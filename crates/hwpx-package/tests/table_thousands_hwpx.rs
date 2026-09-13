use domain_ir::{
    CellCoordinate, FormulaError, FormulaLimitConfig, FormulaLimits, FormulaNumberFormat,
    TABLE_THOUSANDS_SCHEMA_VERSION, TableThousandsBuilder, TableThousandsMode, TableThousandsPlan,
    TableThousandsRequest, TableThousandsRequestDraft,
};
use hwpx_package::{
    TABLE_THOUSANDS_HWPX_PROFILE_ID, TABLE_THOUSANDS_HWPX_SCHEMA_VERSION, TableFormulaHwpxLimits,
    TableThousandsHwpxError, TableThousandsHwpxLowerer, TableThousandsHwpxReadback,
    TableThousandsHwpxReader, TableThousandsHwpxRequest, TableThousandsHwpxRequestDraft,
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

fn read(section: &[u8]) -> Result<TableThousandsHwpxReadback, TableThousandsHwpxError> {
    TableThousandsHwpxReader::read_selected_in_section(
        section,
        0,
        &[OWNER],
        TableFormulaHwpxLimits::default(),
        formula_limits().map_err(TableThousandsHwpxError::Formula)?,
    )
}

fn plan(
    source: &TableThousandsHwpxReadback,
    mode: TableThousandsMode,
) -> Result<TableThousandsPlan, Box<dyn std::error::Error>> {
    let dimensions = source.dimensions();
    let limits = formula_limits()?;
    let request = TableThousandsRequest::from_draft(
        TableThousandsRequestDraft {
            schema_version: TABLE_THOUSANDS_SCHEMA_VERSION.to_owned(),
            mode,
            selected_cells: vec![OWNER],
        },
        dimensions,
        limits,
    )?;
    Ok(TableThousandsBuilder::build(
        request,
        source.selected_formulas(),
        limits,
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

fn request(
    source_bytes: &[u8],
    source: &TableThousandsHwpxReadback,
    plan: &TableThousandsPlan,
) -> Result<TableThousandsHwpxRequest, Box<dyn std::error::Error>> {
    let limits = formula_limits()?;
    Ok(TableThousandsHwpxRequest::from_draft(
        TableThousandsHwpxRequestDraft {
            schema_version: TABLE_THOUSANDS_HWPX_SCHEMA_VERSION.to_owned(),
            table_ordinal: 0,
            expected_section_sha256: hex(source.section_sha256()),
            expected_source_state_sha256: hex(source.selected_state_sha256()),
            expected_source_grid_sha256: hex(source.grid_sha256()),
            expected_document_flow_sha256: FLOW.to_owned(),
            expected_plan_sha256: hex(plan.canonical_sha256(limits)?),
        },
        source_bytes,
        plan,
        FLOW,
        TableFormulaHwpxLimits::default(),
        limits,
    )?)
}

#[test]
fn remove_changes_only_visible_result_and_preserves_native_metadata() -> TestResult {
    let source_bytes = section("4,600", "4,600", "%g,");
    let source = read(&source_bytes)?;
    assert_eq!(source.profile_id(), TABLE_THOUSANDS_HWPX_PROFILE_ID);
    assert_eq!(source.formula_field_count(), 1);
    assert_eq!(
        source.selected_formulas()[0].number_format(),
        FormulaNumberFormat::Number {
            decimal_places: 0,
            use_grouping: true,
        }
    );
    let plan = plan(&source, TableThousandsMode::Remove)?;
    let request = request(&source_bytes, &source, &plan)?;
    let (output, receipt) = TableThousandsHwpxLowerer::lower_in_section_with_receipt(
        &request,
        &source_bytes,
        &plan,
        FLOW,
        TableFormulaHwpxLimits::default(),
        formula_limits()?,
    )?;

    let output_text = std::str::from_utf8(&output)?;
    assert!(output_text.contains("name=\"Command\">=SUM(LEFT)??%g,;;4,600"));
    assert!(output_text.contains("name=\"ResultFormat\">%g,"));
    assert!(output_text.contains("name=\"LastResult\">4,600"));
    assert!(output_text.contains("</hp:ctrl><hp:t>4600</hp:t><hp:ctrl>"));
    assert_eq!(receipt.capability_id(), "table.thousands_remove");
    assert_eq!(receipt.selected_formula_cells(), 1);
    assert_eq!(receipt.modified_text_count(), 1);
    assert!(receipt.grid_preserved());
    assert!(receipt.document_flow_preserved());
    assert_ne!(
        receipt.source_section_sha256(),
        receipt.output_section_sha256()
    );
    assert_eq!(
        read(&output)?.selected_formulas()[0].number_format(),
        FormulaNumberFormat::Number {
            decimal_places: 0,
            use_grouping: false,
        }
    );
    assert!(!format!("{request:?}").contains(FLOW));
    assert!(!format!("{receipt:?}").contains("4,600"));
    let draft_debug = format!(
        "{:?}",
        TableThousandsHwpxRequestDraft {
            schema_version: TABLE_THOUSANDS_HWPX_SCHEMA_VERSION.to_owned(),
            table_ordinal: 0,
            expected_section_sha256: hex(source.section_sha256()),
            expected_source_state_sha256: hex(source.selected_state_sha256()),
            expected_source_grid_sha256: hex(source.grid_sha256()),
            expected_document_flow_sha256: FLOW.to_owned(),
            expected_plan_sha256: hex(plan.canonical_sha256(formula_limits()?)?),
        }
    );
    assert!(draft_debug.contains("<redacted>"));
    assert!(!draft_debug.contains(FLOW));
    Ok(())
}

#[test]
fn add_restores_exact_grouped_bytes_and_same_mode_is_idempotent() -> TestResult {
    let baseline = section("4,600", "4,600", "%g,");
    let removed = section("4600", "4,600", "%g,");
    let source = read(&removed)?;
    let add = plan(&source, TableThousandsMode::Add)?;
    let add_request = request(&removed, &source, &add)?;
    let (restored, receipt) = TableThousandsHwpxLowerer::lower_in_section_with_receipt(
        &add_request,
        &removed,
        &add,
        FLOW,
        TableFormulaHwpxLimits::default(),
        formula_limits()?,
    )?;
    assert_eq!(restored, baseline);
    assert_eq!(receipt.modified_text_count(), 1);

    let grouped = read(&restored)?;
    let idempotent = plan(&grouped, TableThousandsMode::Add)?;
    let idempotent_request = request(&restored, &grouped, &idempotent)?;
    let (same, idempotent_receipt) = TableThousandsHwpxLowerer::lower_in_section_with_receipt(
        &idempotent_request,
        &restored,
        &idempotent,
        FLOW,
        TableFormulaHwpxLimits::default(),
        formula_limits()?,
    )?;
    assert_eq!(same, restored);
    assert_eq!(idempotent_receipt.modified_text_count(), 0);
    Ok(())
}

#[test]
fn negative_decimal_grouping_is_exact_and_non_format_state_is_preserved() -> TestResult {
    let source_bytes = section("-1,234.5", "-1,234.5", "%g,");
    let source = read(&source_bytes)?;
    assert_eq!(
        source.selected_formulas()[0].number_format(),
        FormulaNumberFormat::Number {
            decimal_places: 1,
            use_grouping: true,
        }
    );
    let before_formula = source.selected_formulas()[0].ast().clone();
    let before_cache = source.selected_formulas()[0].cache().clone();
    let remove = plan(&source, TableThousandsMode::Remove)?;
    let request = request(&source_bytes, &source, &remove)?;
    let (output, _) = TableThousandsHwpxLowerer::lower_in_section_with_receipt(
        &request,
        &source_bytes,
        &remove,
        FLOW,
        TableFormulaHwpxLimits::default(),
        formula_limits()?,
    )?;
    let after = read(&output)?;
    assert_eq!(after.selected_formulas()[0].ast(), &before_formula);
    assert_eq!(after.selected_formulas()[0].cache(), &before_cache);
    assert_eq!(
        after.selected_formulas()[0].number_format(),
        FormulaNumberFormat::Number {
            decimal_places: 1,
            use_grouping: false,
        }
    );
    assert!(std::str::from_utf8(&output)?.contains("<hp:t>-1234.5</hp:t>"));
    Ok(())
}

#[test]
fn request_and_build_both_reject_section_flow_and_plan_drift() -> TestResult {
    let source_bytes = section("4,600", "4,600", "%g,");
    let source = read(&source_bytes)?;
    let remove = plan(&source, TableThousandsMode::Remove)?;
    let request = request(&source_bytes, &source, &remove)?;

    let mut changed = source_bytes.clone();
    let position = changed
        .windows(4)
        .position(|window| window == b"1200")
        .ok_or("operand marker missing")?;
    changed[position + 3] = b'1';
    assert!(matches!(
        TableThousandsHwpxLowerer::lower_in_section_with_receipt(
            &request,
            &changed,
            &remove,
            FLOW,
            TableFormulaHwpxLimits::default(),
            formula_limits()?,
        ),
        Err(TableThousandsHwpxError::SectionBindingMismatch)
    ));
    let other_flow = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789";
    assert!(matches!(
        TableThousandsHwpxLowerer::lower_in_section_with_receipt(
            &request,
            &source_bytes,
            &remove,
            other_flow,
            TableFormulaHwpxLimits::default(),
            formula_limits()?,
        ),
        Err(TableThousandsHwpxError::FlowBindingMismatch)
    ));
    let add = plan(&source, TableThousandsMode::Add)?;
    assert!(matches!(
        TableThousandsHwpxLowerer::lower_in_section_with_receipt(
            &request,
            &source_bytes,
            &add,
            FLOW,
            TableFormulaHwpxLimits::default(),
            formula_limits()?,
        ),
        Err(TableThousandsHwpxError::PlanBindingMismatch)
    ));

    let mut wrong = TableThousandsHwpxRequestDraft {
        schema_version: TABLE_THOUSANDS_HWPX_SCHEMA_VERSION.to_owned(),
        table_ordinal: 0,
        expected_section_sha256: hex(source.section_sha256()),
        expected_source_state_sha256: hex(source.selected_state_sha256()),
        expected_source_grid_sha256: hex(source.grid_sha256()),
        expected_document_flow_sha256: FLOW.to_owned(),
        expected_plan_sha256: hex(remove.canonical_sha256(formula_limits()?)?),
    };
    let replacement = if wrong.expected_source_grid_sha256.starts_with('f') {
        "e"
    } else {
        "f"
    };
    wrong
        .expected_source_grid_sha256
        .replace_range(..1, replacement);
    assert!(matches!(
        TableThousandsHwpxRequest::from_draft(
            wrong,
            &source_bytes,
            &remove,
            FLOW,
            TableFormulaHwpxLimits::default(),
            formula_limits()?,
        ),
        Err(TableThousandsHwpxError::RequestBindingMismatch)
    ));
    Ok(())
}

#[test]
fn malformed_or_ambiguous_native_profiles_fail_closed() {
    for invalid in [
        section("4,600", "4,600", "%g"),
        section("460", "460", "%g,"),
        section("46,00", "46,00", "%g,"),
        section("4,600", "4,600.0", "%g,"),
    ] {
        assert!(matches!(
            read(&invalid),
            Err(TableThousandsHwpxError::UnsupportedNativeProfile
                | TableThousandsHwpxError::FormulaHwpx(_))
        ));
    }
}

#[test]
fn strict_json_rejects_duplicate_unknown_and_invalid_digest_fields() -> TestResult {
    let source_bytes = section("4,600", "4,600", "%g,");
    let source = read(&source_bytes)?;
    let remove = plan(&source, TableThousandsMode::Remove)?;
    let request = request(&source_bytes, &source, &remove)?;
    let valid = request.canonical_json(TableFormulaHwpxLimits::default())?;
    let parsed = TableThousandsHwpxRequest::from_json(
        &valid,
        &source_bytes,
        &remove,
        FLOW,
        TableFormulaHwpxLimits::default(),
        formula_limits()?,
    )?;
    assert_eq!(parsed.table_ordinal(), 0);
    assert_eq!(parsed.expected_document_flow_sha256(), FLOW);

    let duplicate = String::from_utf8(valid.clone())?.replacen('{', "{\"table_ordinal\":0,", 1);
    assert!(matches!(
        TableThousandsHwpxRequest::from_json(
            duplicate.as_bytes(),
            &source_bytes,
            &remove,
            FLOW,
            TableFormulaHwpxLimits::default(),
            formula_limits()?,
        ),
        Err(TableThousandsHwpxError::InvalidJson)
    ));
    let unknown = String::from_utf8(valid)?.replacen('{', "{\"unknown\":true,", 1);
    assert!(matches!(
        TableThousandsHwpxRequest::from_json(
            unknown.as_bytes(),
            &source_bytes,
            &remove,
            FLOW,
            TableFormulaHwpxLimits::default(),
            formula_limits()?,
        ),
        Err(TableThousandsHwpxError::InvalidJson)
    ));

    assert_eq!(
        TableThousandsHwpxError::SectionBindingMismatch.code(),
        "table_thousands_hwpx_section_binding_mismatch"
    );
    assert_eq!(
        TableThousandsHwpxError::UnsupportedNativeProfile.code(),
        "table_thousands_hwpx_unsupported_native_profile"
    );
    Ok(())
}
