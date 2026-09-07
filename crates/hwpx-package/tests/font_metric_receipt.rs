use domain_ir::{
    FontMetricStatus, LengthMicrometers, LogicalId, TABLE_LAYOUT_SCHEMA_VERSION, TableCellSpan,
    TableColumnConstraint, TableGrid, TableGridLimits, TableLayoutLimits, TableLayoutProblem,
    TableLayoutSolver, TableWidthSpec,
};
use hwpx_package::{
    CURRENT_FONT_METRIC_PROFILE_ID, CurrentFontMetricLimits, CurrentFontMetricReceipt,
    FontMetricReceiptError,
};
use sha2::{Digest as _, Sha256};

type TestResult = Result<(), Box<dyn std::error::Error>>;

const CELLS_JSON: &str = concat!(
    r#"[{"cell_id":"cell-a","text_sha256":"df47d07aa15a6493ed52bcddfbd594ff255d9566138ab7137f90b13fedd2ed98","minimum_content_width_micrometers":11829,"preferred_content_width_micrometers":15378,"line_height_micrometers":4586},"#,
    r#"{"cell_id":"cell-b","text_sha256":"b81461d5ac0a8865284ef84c147e0743da482750e1a499d80126e31c7324ee7b","minimum_content_width_micrometers":6845,"preferred_content_width_micrometers":27132,"line_height_micrometers":4586},"#,
    r#"{"cell_id":"cell-c","text_sha256":"25dfcb4b0c5e694cf7bf977f1870cd2025fa363bfa2a26118ea00f305a3afdd3","minimum_content_width_micrometers":49392,"preferred_content_width_micrometers":49392,"line_height_micrometers":4586},"#,
    r#"{"cell_id":"cell-d","text_sha256":"d932f7dee69be5f5763a0647e1ed14067e5231e783b4039a9aabbf8387405845","minimum_content_width_micrometers":6845,"preferred_content_width_micrometers":11326,"line_height_micrometers":4586}]"#,
);

fn um(value: i64) -> LengthMicrometers {
    LengthMicrometers::from_raw(value)
}

fn valid_receipt() -> Vec<u8> {
    receipt_with_cells(CELLS_JSON)
}

fn receipt_with_cells(cells: &str) -> Vec<u8> {
    let measurement_sha256 = hex::encode(Sha256::digest(cells.as_bytes()));
    format!(
        concat!(
            r#"{{"schema_version":"hwpx-agent.p06-05-current-font-metric-receipt/v1","#,
            r#""run_id":"ec63c360ea974ad7a971f95c59c191bd","#,
            r#""scope":"current_pc_named_synthetic_fixture_only","state":"pass","#,
            r#""profile_id":"hwpx-agent.font-metric.gdiplus-typographic-96dpi/1","#,
            r#""target":{{"hangul_build":"11.0.0.9136","architecture":"x86","#,
            r#""executable_sha256":"7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce","#,
            r#""font_file_name":"HANBatang.ttf","font_file_bytes":28412796,"#,
            r#""font_file_sha256":"0dbeb7b129fcec63f8d6b7f1d3b5bb991c1d599e725286518ccc598de643f014","#,
            r#""font_family":"함초롬바탕"}},"#,
            r#""measurement":{{"provider":"System.Drawing.GDIPlus.GenericTypographic/1","dpi":96,"#,
            r#""font_size_millipoints":10000,"repeat_count":2,"#,
            r#""conversion":"micrometers=round_away_from_zero(pixels*25400/96)"}},"#,
            r#""cells":{0},"measurement_set_sha256":"{1}","#,
            r#""visible_text_present":false,"user_document_opened":false,"#,
            r#""hwp_process_created":false,"external_network_invoked":false,"#,
            r#""registry_or_system_setting_changed":false,"computer_use_click_or_type_invoked":false,"#,
            r#""actual_hangul_renderer":false,"other_pc_or_version":false,"product_complete":false}}"#,
        ),
        cells,
        measurement_sha256,
    )
    .into_bytes()
}

fn parse(source: &[u8]) -> Result<CurrentFontMetricReceipt, FontMetricReceiptError> {
    CurrentFontMetricReceipt::parse(source, CurrentFontMetricLimits::default())
}

fn span(
    identifier: &str,
    row: u32,
    column: u32,
) -> Result<TableCellSpan, Box<dyn std::error::Error>> {
    Ok(TableCellSpan {
        master_cell_id: LogicalId::parse(identifier)?,
        row,
        column,
        row_span: 1,
        column_span: 1,
    })
}

#[test]
fn exact_current_receipt_is_redacted_and_yields_verified_metrics() -> TestResult {
    let source = valid_receipt();
    let receipt = parse(&source)?;
    assert_eq!(
        receipt.receipt_sha256(),
        hex::encode(Sha256::digest(&source))
    );
    assert_eq!(
        receipt.measurement_set_sha256(),
        "96e3ad33591b098d3ca15c88242303aa7b11dc1730cf2a499273afe3ad7790a9"
    );
    assert_eq!(receipt.cells().len(), 4);
    assert_eq!(receipt.cells()[0].minimum_content_width(), um(11_829));
    assert_eq!(receipt.cells()[2].preferred_content_width(), um(49_392));
    assert_eq!(receipt.cells()[3].line_height(), um(4_586));

    let debug = format!("{receipt:?}");
    assert!(!debug.contains("함초롬"));
    assert!(!debug.contains("cell-a"));

    let cell_id = LogicalId::parse("cell-a")?;
    let measure = receipt.table_cell_measure(&cell_id, um(127), um(127))?;
    assert_eq!(measure.master_cell_id, cell_id);
    assert_eq!(measure.leading_margin, um(127));
    assert_eq!(measure.unbreakable_content_width, um(11_829));
    assert_eq!(measure.preferred_content_width, um(15_378));
    assert_eq!(
        measure.font_metric_evidence.status,
        FontMetricStatus::Verified
    );
    assert_eq!(
        measure.font_metric_evidence.profile_id.as_deref(),
        Some(CURRENT_FONT_METRIC_PROFILE_ID)
    );
    assert_eq!(
        measure.font_metric_evidence.source_sha256.as_deref(),
        Some(receipt.receipt_sha256())
    );
    Ok(())
}

#[test]
fn verified_receipt_composes_with_the_table_layout_solver() -> TestResult {
    let receipt = parse(&valid_receipt())?;
    let grid = TableGrid::new(
        2,
        2,
        vec![
            span("cell-a", 0, 0)?,
            span("cell-b", 0, 1)?,
            span("cell-c", 1, 0)?,
            span("cell-d", 1, 1)?,
        ],
        TableGridLimits::default(),
    )?;
    let mut cells = Vec::new();
    for identifier in ["cell-a", "cell-b", "cell-c", "cell-d"] {
        cells.push(receipt.table_cell_measure(&LogicalId::parse(identifier)?, um(127), um(127))?);
    }
    let columns = (0..2)
        .map(|_| TableColumnConstraint {
            minimum_width: um(1_000),
            preferred_width: um(1_000),
            previous_width: um(1_000),
            fixed_width: None,
        })
        .collect();
    let problem = TableLayoutProblem {
        schema_version: TABLE_LAYOUT_SCHEMA_VERSION.to_owned(),
        width: TableWidthSpec::FitContent,
        body_width: um(100_000),
        columns,
        cells,
    };
    let plan = TableLayoutSolver::solve(&grid, &problem, TableLayoutLimits::default())?;
    plan.require_verified()?;
    assert_eq!(plan.column_widths(), &[um(49_646), um(27_386)]);
    assert_eq!(plan.estimated_row_heights(), &[um(4_586), um(4_586)]);
    Ok(())
}

#[test]
fn target_claim_digest_and_cell_drift_fail_closed() -> TestResult {
    let valid = String::from_utf8(valid_receipt())?;
    let target_drift = valid.replace("11.0.0.9136", "11.0.0.9137");
    assert_eq!(
        parse(target_drift.as_bytes()),
        Err(FontMetricReceiptError::UnsupportedTarget)
    );

    let claim_drift = valid.replacen("\"product_complete\":false", "\"product_complete\":true", 1);
    assert_eq!(
        parse(claim_drift.as_bytes()),
        Err(FontMetricReceiptError::UnsupportedTarget)
    );

    let digest_drift = valid.replacen(
        "96e3ad33591b098d3ca15c88242303aa7b11dc1730cf2a499273afe3ad7790a9",
        "06e3ad33591b098d3ca15c88242303aa7b11dc1730cf2a499273afe3ad7790a9",
        1,
    );
    assert_eq!(
        parse(digest_drift.as_bytes()),
        Err(FontMetricReceiptError::MeasurementDigestMismatch)
    );

    let cell_drift = CELLS_JSON.replace(
        "\"minimum_content_width_micrometers\":11829",
        "\"minimum_content_width_micrometers\":11830",
    );
    assert_eq!(
        parse(&receipt_with_cells(&cell_drift)),
        Err(FontMetricReceiptError::MeasurementDigestMismatch)
    );
    Ok(())
}

#[test]
fn limits_missing_cells_and_margins_fail_closed() -> TestResult {
    assert_eq!(
        CurrentFontMetricLimits::new(0, 4, 1_000_000_000),
        Err(FontMetricReceiptError::InvalidLimit)
    );
    assert_eq!(
        CurrentFontMetricReceipt::parse(
            &valid_receipt(),
            CurrentFontMetricLimits::new(262_144, 4, 40_000)?,
        ),
        Err(FontMetricReceiptError::MetricInvalid)
    );
    let receipt = parse(&valid_receipt())?;
    assert_eq!(
        receipt.table_cell_measure(&LogicalId::parse("absent")?, um(0), um(0)),
        Err(FontMetricReceiptError::CellMissing)
    );
    assert_eq!(
        receipt.table_cell_measure(&LogicalId::parse("cell-a")?, um(-1), um(0)),
        Err(FontMetricReceiptError::MetricInvalid)
    );
    Ok(())
}

#[test]
fn malformed_ambiguous_or_oversized_json_is_rejected() -> TestResult {
    assert_eq!(parse(b"{}"), Err(FontMetricReceiptError::MalformedJson));
    let duplicate = String::from_utf8(valid_receipt())?.replacen(
        r#""schema_version":"hwpx-agent.p06-05-current-font-metric-receipt/v1""#,
        concat!(
            r#""schema_version":"hwpx-agent.p06-05-current-font-metric-receipt/v1","#,
            r#""schema_version":"hwpx-agent.p06-05-current-font-metric-receipt/v1""#,
        ),
        1,
    );
    assert_eq!(
        parse(duplicate.as_bytes()),
        Err(FontMetricReceiptError::MalformedJson)
    );

    let oversized = vec![b' '; 262_145];
    assert_eq!(parse(&oversized), Err(FontMetricReceiptError::InputLimit));
    Ok(())
}

#[test]
fn errors_expose_stable_public_codes() {
    assert_eq!(
        FontMetricReceiptError::MeasurementDigestMismatch.code(),
        "font_metric_receipt_measurement_digest_mismatch"
    );
    assert_eq!(
        FontMetricReceiptError::UnsupportedTarget.code(),
        "font_metric_receipt_unsupported_target"
    );
    assert_eq!(
        FontMetricReceiptError::MetricInvalid.code(),
        "font_metric_receipt_metric_invalid"
    );
}
