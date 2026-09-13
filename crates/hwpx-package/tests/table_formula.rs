use domain_ir::{
    CellCoordinate, FormulaAst, FormulaAstDraft, FormulaCache, FormulaCell, FormulaCellDraft,
    FormulaDecimal, FormulaGridDimensions, FormulaLimitConfig, FormulaLimits, FormulaNumberFormat,
    FormulaValue, TABLE_FORMULA_SCHEMA_VERSION,
};
use hwpx_package::{
    TABLE_FORMULA_HWPX_PROFILE_ID, TableFormulaHwpxError, TableFormulaHwpxLimitConfig,
    TableFormulaHwpxLimits, TableFormulaHwpxLowerer, TableFormulaHwpxReader,
    TablePaginationHwpxLimits, TablePaginationHwpxReader,
};

type TestResult = Result<(), Box<dyn std::error::Error>>;

const DIMENSIONS: FormulaGridDimensions = FormulaGridDimensions {
    rows: 1,
    columns: 3,
};

fn formula_limits() -> Result<FormulaLimits, Box<dyn std::error::Error>> {
    Ok(FormulaLimits::new(FormulaLimitConfig {
        rows: 10,
        columns: 10,
        ..FormulaLimitConfig::default()
    })?)
}

fn limits() -> TableFormulaHwpxLimits {
    TableFormulaHwpxLimits::default()
}

fn section() -> String {
    r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">
  <hp:p><hp:run><hp:tbl id="100" rowCnt="1" colCnt="3">
    <hp:tr>
      <hp:tc><hp:subList><hp:p><hp:run><hp:t>17</hp:t></hp:run></hp:p></hp:subList><hp:cellAddr colAddr="0" rowAddr="0"/><hp:cellSpan colSpan="1" rowSpan="1"/></hp:tc>
      <hp:tc><hp:subList><hp:p><hp:run><hp:t>25</hp:t></hp:run></hp:p></hp:subList><hp:cellAddr colAddr="1" rowAddr="0"/><hp:cellSpan colSpan="1" rowSpan="1"/></hp:tc>
      <hp:tc><hp:subList><hp:p><hp:run charPrIDRef="0"><hp:ctrl><hp:fieldBegin id="101" type="FORMULA" name="" editable="0" dirty="0" zorder="-1" fieldid="202"><hp:parameters cnt="5" name=""><hp:integerParam name="Prop">8</hp:integerParam><hp:stringParam name="Command">=SUM(LEFT)??%g,;;42</hp:stringParam><hp:stringParam name="Formula">=SUM(LEFT)</hp:stringParam><hp:stringParam name="ResultFormat">%g,</hp:stringParam><hp:stringParam name="LastResult">42</hp:stringParam></hp:parameters></hp:fieldBegin></hp:ctrl><hp:t>42</hp:t><hp:ctrl><hp:fieldEnd beginIDRef="101" fieldid="202"/></hp:ctrl><hp:t/></hp:run></hp:p></hp:subList><hp:cellAddr colAddr="2" rowAddr="0"/><hp:cellSpan colSpan="1" rowSpan="1"/></hp:tc>
    </hp:tr>
  </hp:tbl></hp:run></hp:p>
</hs:sec>"#
        .to_owned()
}

fn paginated_section() -> String {
    section()
        .replace(
            "<hp:tbl id=\"100\" rowCnt=\"1\" colCnt=\"3\">",
            concat!(
                "<hp:tbl id=\"100\" lock=\"0\" pageBreak=\"CELL\" repeatHeader=\"0\" ",
                "rowCnt=\"1\" colCnt=\"3\" cellSpacing=\"0\" noAdjust=\"0\">",
                "<hp:sz/><hp:pos/><hp:outMargin/><hp:inMargin/>"
            ),
        )
        .replace("<hp:tc>", "<hp:tc header=\"0\">")
}

fn target(source: &str, cache: FormulaCache) -> Result<FormulaCell, Box<dyn std::error::Error>> {
    let ast = FormulaAst::parse(source, formula_limits()?)?;
    Ok(FormulaCell::from_draft(
        FormulaCellDraft {
            schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
            owner: CellCoordinate { row: 0, column: 2 },
            ast: FormulaAstDraft {
                schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
                expression: ast.expression().clone(),
            },
            cache,
            number_format: FormulaNumberFormat::General,
        },
        DIMENSIONS,
        formula_limits()?,
    )?)
}

fn decimal_cache(coefficient: i64, scale: u8) -> FormulaCache {
    FormulaCache::Unverified {
        value: FormulaValue::Decimal {
            value: FormulaDecimal::new(coefficient, scale),
        },
    }
}

#[test]
fn reads_exact_hancom_2020_left_formula_as_locale_neutral_ast() -> TestResult {
    let readback = TableFormulaHwpxReader::read_in_section(
        section().as_bytes(),
        0,
        limits(),
        formula_limits()?,
    )?;
    assert_eq!(readback.profile_id, TABLE_FORMULA_HWPX_PROFILE_ID);
    assert_eq!((readback.rows, readback.columns), (1, 3));
    assert_eq!(
        readback.formula.owner(),
        CellCoordinate { row: 0, column: 2 }
    );
    assert_eq!(
        readback
            .formula
            .ast()
            .canonical_formula(formula_limits()?)?,
        "SUM(A1:B1)"
    );
    assert_eq!(readback.formula.cache(), &decimal_cache(42, 0));
    assert_eq!(
        readback.formula.number_format(),
        FormulaNumberFormat::General
    );
    assert_eq!(readback.formula_field_count, 1);
    assert_eq!(
        TableFormulaHwpxReader::formula_count_in_section(
            section().as_bytes(),
            0,
            limits(),
            formula_limits()?
        )?,
        1
    );
    Ok(())
}

#[test]
fn lowering_updates_only_command_cache_and_visible_result() -> TestResult {
    let source = section();
    let wanted = target("SUM(A1:B1)", decimal_cache(435, 1))?;
    let (output, receipt) = TableFormulaHwpxLowerer::lower_in_section_with_receipt(
        source.as_bytes(),
        0,
        &wanted,
        DIMENSIONS,
        limits(),
        formula_limits()?,
    )?;
    let output_text = std::str::from_utf8(&output)?;
    assert!(output_text.contains("=SUM(LEFT)??%g,;;43.5"));
    assert!(output_text.contains("<hp:stringParam name=\"LastResult\">43.5</hp:stringParam>"));
    assert!(output_text.contains("</hp:fieldBegin></hp:ctrl><hp:t>43.5</hp:t>"));
    assert!(output_text.contains("<hp:t>17</hp:t>"));
    assert!(output_text.contains("<hp:t>25</hp:t>"));

    let readback =
        TableFormulaHwpxReader::read_in_section(&output, 0, limits(), formula_limits()?)?;
    assert_eq!(readback.formula, wanted);
    assert_eq!(receipt.profile_id, TABLE_FORMULA_HWPX_PROFILE_ID);
    assert_eq!(receipt.modified_text_count, 3);
    assert_eq!(receipt.unowned_sha256, readback.unowned_sha256);
    assert_ne!(receipt.source_sha256, receipt.output_sha256);
    assert_eq!(
        receipt.target_formula_sha256,
        wanted.canonical_sha256(formula_limits()?)?
    );
    Ok(())
}

#[test]
fn formula_and_cache_lowering_preserves_page_split_semantics() -> TestResult {
    let source = paginated_section();
    let source_pagination = TablePaginationHwpxReader::read_in_section(
        source.as_bytes(),
        0,
        TablePaginationHwpxLimits::default(),
    )?;
    let wanted = target("SUM(A1:B1)", decimal_cache(435, 1))?;
    let output = TableFormulaHwpxLowerer::lower_in_section(
        source.as_bytes(),
        0,
        &wanted,
        DIMENSIONS,
        limits(),
        formula_limits()?,
    )?;
    let target_pagination = TablePaginationHwpxReader::read_in_section(
        &output,
        0,
        TablePaginationHwpxLimits::default(),
    )?;
    let target_formula =
        TableFormulaHwpxReader::read_in_section(&output, 0, limits(), formula_limits()?)?;

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
    assert_eq!(target_formula.formula, wanted);
    assert_eq!(target_formula.formula_field_count, 1);
    Ok(())
}

#[test]
fn lowering_is_deterministic_and_accepts_negative_decimal_cache() -> TestResult {
    let source = section();
    let wanted = target("SUM(A1:B1)", decimal_cache(-75, 1))?;
    let first = TableFormulaHwpxLowerer::lower_in_section(
        source.as_bytes(),
        0,
        &wanted,
        DIMENSIONS,
        limits(),
        formula_limits()?,
    )?;
    let second = TableFormulaHwpxLowerer::lower_in_section(
        source.as_bytes(),
        0,
        &wanted,
        DIMENSIONS,
        limits(),
        formula_limits()?,
    )?;
    assert_eq!(first, second);
    assert!(std::str::from_utf8(&first)?.contains(";;-7.5"));
    Ok(())
}

#[test]
fn source_field_shape_and_identity_drift_fail_closed() -> TestResult {
    let cases = [
        section().replace("=SUM(LEFT)??%g,;;42", "=SUM(LEFT)??%g,;;41"),
        section().replace("beginIDRef=\"101\"", "beginIDRef=\"999\""),
        section().replace("fieldid=\"202\"/></hp:ctrl>", "fieldid=\"999\"/></hp:ctrl>"),
        section().replace(
            "<hp:integerParam name=\"Prop\">8",
            "<hp:integerParam name=\"Prop\">7",
        ),
        section().replace(
            "<hp:stringParam name=\"Formula\">=SUM(LEFT)",
            "<hp:stringParam name=\"Formula\">=SUM(ABOVE)",
        ),
        section().replace(
            "<hp:stringParam name=\"LastResult\">42",
            "<hp:stringParam name=\"LastResult\">042",
        ),
        section().replace(
            "</hp:parameters>",
            "<hp:stringParam name=\"Extra\">x</hp:stringParam></hp:parameters>",
        ),
        section().replace("<hp:t>42</hp:t><hp:ctrl>", "<hp:t>41</hp:t><hp:ctrl>"),
    ];
    for invalid in cases {
        assert!(
            TableFormulaHwpxReader::read_in_section(
                invalid.as_bytes(),
                0,
                limits(),
                formula_limits()?
            )
            .is_err()
        );
    }
    Ok(())
}

#[test]
fn grid_coverage_selector_and_namespace_drift_fail_closed() -> TestResult {
    let duplicate_address = section().replace(
        "<hp:cellAddr colAddr=\"1\" rowAddr=\"0\"/>",
        "<hp:cellAddr colAddr=\"0\" rowAddr=\"0\"/>",
    );
    let span = section().replace("colSpan=\"1\"", "colSpan=\"2\"");
    let namespace = section().replace(
        "http://www.hancom.co.kr/hwpml/2011/paragraph",
        "urn:not-hancom-paragraph",
    );
    for invalid in [duplicate_address, span, namespace] {
        assert!(
            TableFormulaHwpxReader::read_in_section(
                invalid.as_bytes(),
                0,
                limits(),
                formula_limits()?
            )
            .is_err()
        );
    }
    assert!(
        TableFormulaHwpxReader::read_in_section(
            section().as_bytes(),
            1,
            limits(),
            formula_limits()?
        )
        .is_err()
    );
    Ok(())
}

#[test]
fn lowerer_rejects_non_left_prefix_absent_cache_and_shape_drift() -> TestResult {
    let source = section();
    let wrong_formula = target("SUM(B1:B1)", decimal_cache(42, 0))?;
    assert!(matches!(
        TableFormulaHwpxLowerer::lower_in_section(
            source.as_bytes(),
            0,
            &wrong_formula,
            DIMENSIONS,
            limits(),
            formula_limits()?
        ),
        Err(TableFormulaHwpxError::UnsupportedFormula)
    ));

    let absent = target("SUM(A1:B1)", FormulaCache::Absent)?;
    assert!(matches!(
        TableFormulaHwpxLowerer::lower_in_section(
            source.as_bytes(),
            0,
            &absent,
            DIMENSIONS,
            limits(),
            formula_limits()?
        ),
        Err(TableFormulaHwpxError::UnsupportedCache)
    ));

    let valid = target("SUM(A1:B1)", decimal_cache(42, 0))?;
    assert!(matches!(
        TableFormulaHwpxLowerer::lower_in_section(
            source.as_bytes(),
            0,
            &valid,
            FormulaGridDimensions {
                rows: 1,
                columns: 4,
            },
            limits(),
            formula_limits()?
        ),
        Err(TableFormulaHwpxError::UnsupportedShape)
    ));
    Ok(())
}

#[test]
fn finite_limits_are_enforced_before_publication() -> TestResult {
    assert!(matches!(
        TableFormulaHwpxLimits::new(TableFormulaHwpxLimitConfig {
            input_bytes: 0,
            ..TableFormulaHwpxLimitConfig::default()
        }),
        Err(TableFormulaHwpxError::InvalidLimit)
    ));

    let tiny_input = TableFormulaHwpxLimits::new(TableFormulaHwpxLimitConfig {
        input_bytes: 8,
        ..TableFormulaHwpxLimitConfig::default()
    })?;
    assert!(matches!(
        TableFormulaHwpxReader::read_in_section(
            section().as_bytes(),
            0,
            tiny_input,
            formula_limits()?
        ),
        Err(TableFormulaHwpxError::InputLimit)
    ));

    let tiny_output = TableFormulaHwpxLimits::new(TableFormulaHwpxLimitConfig {
        output_bytes: section().len(),
        ..TableFormulaHwpxLimitConfig::default()
    })?;
    let longer = target("SUM(A1:B1)", decimal_cache(123_456, 0))?;
    assert!(matches!(
        TableFormulaHwpxLowerer::lower_in_section(
            section().as_bytes(),
            0,
            &longer,
            DIMENSIONS,
            tiny_output,
            formula_limits()?
        ),
        Err(TableFormulaHwpxError::OutputLimit)
    ));
    Ok(())
}

#[test]
fn debug_and_error_codes_do_not_disclose_native_command_or_cache() -> TestResult {
    let readback = TableFormulaHwpxReader::read_in_section(
        section().as_bytes(),
        0,
        limits(),
        formula_limits()?,
    )?;
    let debug = format!("{readback:?}");
    assert!(!debug.contains("SUM(LEFT)"));
    assert!(!debug.contains("42"));
    assert_eq!(
        TableFormulaHwpxError::UnsupportedFormula.code(),
        "table_formula_hwpx_unsupported_formula"
    );
    Ok(())
}
