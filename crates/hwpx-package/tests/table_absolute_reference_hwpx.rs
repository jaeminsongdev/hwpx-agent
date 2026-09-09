use std::io::{Cursor, Write};

use domain_ir::{
    CellCoordinate, FormulaAst, FormulaAstDraft, FormulaCache, FormulaCachePolicy, FormulaCell,
    FormulaCellDraft, FormulaDecimal, FormulaGridDimensions, FormulaLimitConfig, FormulaLimits,
    FormulaNumberFormat, FormulaValue, TABLE_FORMULA_SCHEMA_VERSION,
};
use hwpx_package::{
    BoundedZipReader, Compression, PackageGraph, PackageGraphLimits, PackageLimits,
    TABLE_ABSOLUTE_REFERENCE_HWPX_PROFILE_ID, TABLE_ABSOLUTE_REFERENCE_HWPX_SCHEMA_VERSION,
    TableAbsoluteReferenceHwpxBuilder, TableAbsoluteReferenceHwpxError,
    TableAbsoluteReferenceHwpxLimits, TableAbsoluteReferenceHwpxLowerer,
    TableAbsoluteReferenceHwpxPlan, TableAbsoluteReferenceHwpxReadback,
    TableAbsoluteReferenceHwpxReader, TableAbsoluteReferenceHwpxRequest,
    TableAbsoluteReferenceHwpxRequestDraft,
};
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, DateTime, ZipArchive, ZipWriter};

type TestResult<T = ()> = Result<T, Box<dyn std::error::Error>>;

const HEADER: &[u8] = include_bytes!("../src/hancom_2020_minimal_header.xml");
const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const SECTION_NS: &str = "http://www.hancom.co.kr/hwpml/2011/section";
const OWNER: CellCoordinate = CellCoordinate { row: 1, column: 2 };
const DIMENSIONS: FormulaGridDimensions = FormulaGridDimensions {
    rows: 2,
    columns: 3,
};
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

fn limits() -> TestResult<TableAbsoluteReferenceHwpxLimits> {
    Ok(TableAbsoluteReferenceHwpxLimits {
        formula: FormulaLimits::new(FormulaLimitConfig {
            rows: 16,
            columns: 16,
            ..FormulaLimitConfig::default()
        })?,
        ..TableAbsoluteReferenceHwpxLimits::default()
    })
}

fn flow(character: char) -> String {
    std::iter::repeat_n(character, 64).collect()
}

fn hex(value: impl AsRef<[u8]>) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(value.as_ref().len().saturating_mul(2));
    for byte in value.as_ref() {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}

fn text_paragraph(value: &str, row: u32, column: u32) -> String {
    format!(
        r#"<hp:p id="{row}{column}" paraPrIDRef="{row}" styleIDRef="{column}"><hp:run charPrIDRef="{style}"><hp:t>{value}</hp:t></hp:run></hp:p>"#,
        style = row + column + 1,
    )
}

fn formula_paragraph(
    row: u32,
    column: u32,
    begin_id: u64,
    field_id: u64,
    formula: &str,
    result: &str,
) -> String {
    let native = format!("={formula}");
    format!(
        concat!(
            r#"<hp:p id="{row}{column}" paraPrIDRef="{row}" styleIDRef="{column}"><hp:run charPrIDRef="{style}"><hp:ctrl>"#,
            r#"<hp:fieldBegin id="{begin_id}" type="FORMULA" name="" editable="0" dirty="0" zorder="-1" fieldid="{field_id}">"#,
            r#"<hp:parameters cnt="5" name=""><hp:integerParam name="Prop">8</hp:integerParam>"#,
            r#"<hp:stringParam name="Command">{native}??%g,;;{result}</hp:stringParam>"#,
            r#"<hp:stringParam name="Formula">{native}</hp:stringParam>"#,
            r#"<hp:stringParam name="ResultFormat">%g,</hp:stringParam>"#,
            r#"<hp:stringParam name="LastResult">{result}</hp:stringParam></hp:parameters>"#,
            r#"</hp:fieldBegin></hp:ctrl><hp:t>{result}</hp:t><hp:ctrl>"#,
            r#"<hp:fieldEnd beginIDRef="{begin_id}" fieldid="{field_id}"/></hp:ctrl><hp:t/></hp:run></hp:p>"#,
        ),
        row = row,
        column = column,
        begin_id = begin_id,
        field_id = field_id,
        native = native,
        result = result,
        style = row + column + 1,
    )
}

fn cell(row: u32, column: u32, payload: &str) -> String {
    format!(
        concat!(
            r#"<hp:tc name="" header="{header}" hasMargin="1" protect="0" editable="0" dirty="0" borderFillIDRef="1">"#,
            r#"<hp:cellAddr colAddr="{column}" rowAddr="{row}"/><hp:cellSpan colSpan="1" rowSpan="1"/>"#,
            r#"<hp:cellSz width="1000" height="600"/>"#,
            r#"<hp:cellMargin left="{left}" right="{right}" top="{top}" bottom="{bottom}"/>"#,
            r#"<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">"#,
            "{payload}</hp:subList></hp:tc>"
        ),
        row = row,
        column = column,
        payload = payload,
        header = u8::from(row == 0),
        left = row * 10 + column,
        right = row + column,
        top = row * 2,
        bottom = column * 3,
    )
}

fn table(first_formula: &str, target_formula: &str, target_result: &str) -> String {
    let row0 = [
        cell(0, 0, &formula_paragraph(0, 0, 101, 201, first_formula, "5")),
        cell(0, 1, &text_paragraph("other", 0, 1)),
        cell(0, 2, &text_paragraph("header", 0, 2)),
    ]
    .join("");
    let row1 = [
        cell(1, 0, &text_paragraph("5", 1, 0)),
        cell(1, 1, &text_paragraph("7", 1, 1)),
        cell(
            1,
            2,
            &formula_paragraph(1, 2, 102, 202, target_formula, target_result),
        ),
    ]
    .join("");
    format!(
        concat!(
            r#"<hp:tbl id="700" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="1" rowCnt="2" colCnt="3" cellSpacing="0" borderFillIDRef="1" noAdjust="0">"#,
            r#"<hp:sz width="3000" widthRelTo="ABSOLUTE" height="1200" heightRelTo="ABSOLUTE" protect="0"/>"#,
            r#"<hp:pos treatAsChar="0" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="2000" horzOffset="1000"/>"#,
            r#"<hp:outMargin left="0" right="0" top="0" bottom="0"/>"#,
            r#"<hp:caption side="TOP" fullSz="0" width="42520" gap="850" lastWidth="42520"><hp:subList><hp:p><hp:run><hp:t>ABSOLUTE REFERENCE CAPTION</hp:t></hp:run></hp:p></hp:subList></hp:caption>"#,
            r#"<hp:inMargin left="0" right="0" top="0" bottom="0"/>"#,
            "<hp:tr>{row0}</hp:tr><hp:tr>{row1}</hp:tr></hp:tbl>"
        ),
        row0 = row0,
        row1 = row1,
    )
}

fn section() -> Vec<u8> {
    format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{before}{table}{after}</hs:sec>"#,
        before = text_paragraph("BEFORE", 8, 8),
        table = table("A2", "SUM(A2:B2)", "12"),
        after = text_paragraph("AFTER", 9, 9),
    )
    .into_bytes()
}

fn decimal_cache(value: i64) -> FormulaCache {
    FormulaCache::Unverified {
        value: FormulaValue::Decimal {
            value: FormulaDecimal::new(value, 0),
        },
    }
}

fn formula(source: &str, cache: FormulaCache) -> TestResult<FormulaCell> {
    let limits = limits()?;
    let ast = FormulaAst::parse(source, limits.formula)?;
    Ok(FormulaCell::from_draft(
        FormulaCellDraft {
            schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
            owner: OWNER,
            ast: FormulaAstDraft {
                schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
                expression: ast.expression().clone(),
            },
            cache,
            number_format: FormulaNumberFormat::General,
        },
        DIMENSIONS,
        limits.formula,
    )?)
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

fn read(section: &[u8]) -> TestResult<TableAbsoluteReferenceHwpxReadback> {
    Ok(TableAbsoluteReferenceHwpxReader::read_context(
        HEADER,
        section,
        0,
        OWNER,
        limits()?,
    )?)
}

fn draft(
    source: &TableAbsoluteReferenceHwpxReadback,
    target: &FormulaCell,
    cache_policy: FormulaCachePolicy,
    before: char,
    after: char,
) -> TableAbsoluteReferenceHwpxRequestDraft {
    TableAbsoluteReferenceHwpxRequestDraft {
        schema_version: TABLE_ABSOLUTE_REFERENCE_HWPX_SCHEMA_VERSION.to_owned(),
        capability_id: "table.formula_absolute_ref".to_owned(),
        table_ordinal: 0,
        owner: OWNER,
        recalculate: false,
        cache_policy,
        target_formula: formula_draft(target),
        expected_header_sha256: hex(source.header_sha256),
        expected_section_sha256: hex(source.section_sha256),
        expected_table_content_sha256: hex(source.table_content_sha256),
        expected_source_formula_sha256: hex(source.selected_formula_sha256),
        expected_selected_unowned_sha256: hex(source.selected_unowned_sha256),
        expected_pagination_policy_sha256: hex(source.pagination_policy_sha256),
        expected_source_table_count: source.source_table_count,
        expected_formula_field_count: source.formula_field_count,
        expected_document_flow_sha256: flow(before),
        target_document_flow_sha256: flow(after),
    }
}

fn admitted(
    source: &TableAbsoluteReferenceHwpxReadback,
    request_draft: TableAbsoluteReferenceHwpxRequestDraft,
    current_flow: char,
) -> TestResult<(
    TableAbsoluteReferenceHwpxRequest,
    TableAbsoluteReferenceHwpxPlan,
)> {
    let limits = limits()?;
    let request = TableAbsoluteReferenceHwpxRequest::from_draft(
        request_draft,
        source,
        &flow(current_flow),
        limits,
    )?;
    let plan =
        TableAbsoluteReferenceHwpxBuilder::build(&request, source, &flow(current_flow), limits)?;
    Ok((request, plan))
}

#[test]
fn upgrades_independent_axes_and_preserves_other_formula_pagination_and_caption() -> TestResult {
    let section = section();
    let source = read(&section)?;
    assert_eq!(source.formula_field_count, 2);
    assert_eq!(source.profile_id, TABLE_ABSOLUTE_REFERENCE_HWPX_PROFILE_ID);
    let target = formula("SUM($A2:B$2)", decimal_cache(12))?;
    let (request, plan) = admitted(
        &source,
        draft(&source, &target, FormulaCachePolicy::Preserve, '0', '1'),
        '0',
    )?;
    assert_eq!(plan.changed_axis_count(), 2);
    let output = TableAbsoluteReferenceHwpxLowerer::lower(
        HEADER,
        &section,
        &flow('0'),
        &request,
        &plan,
        limits()?,
    )?;
    let text = String::from_utf8(output.section.clone())?;
    assert!(text.contains("=SUM($A2:B$2)??%g,;;12"));
    assert!(text.contains("<hp:stringParam name=\"Formula\">=A2</hp:stringParam>"));
    assert!(text.contains("ABSOLUTE REFERENCE CAPTION"));
    assert_eq!(output.receipt.formula_field_count, 2);
    assert_eq!(output.receipt.changed_axis_count, 2);
    assert_eq!(output.receipt.modified_text_count, 4);
    assert_eq!(output.receipt.source_table_count, 1);
    assert_eq!(output.receipt.target_table_count, 1);
    assert!(output.receipt.semantic_change);
    let reopened = read(&output.section)?;
    assert_eq!(reopened.formula, target);
    assert_eq!(reopened.pagination.page_split, source.pagination.page_split);
    assert_eq!(
        reopened.pagination.repeat_header_rows,
        source.pagination.repeat_header_rows
    );
    assert_eq!(reopened.pagination.caption, source.pagination.caption);
    assert_eq!(
        reopened.selected_unowned_sha256,
        source.selected_unowned_sha256
    );
    Ok(())
}

#[test]
fn recursive_formula_grammar_and_update_or_clear_cache_round_trip() -> TestResult {
    let section = section();
    let source = read(&section)?;
    let update = formula("(SUM($A2:B$2)+(A2*(-B2)))", decimal_cache(47))?;
    let invalid_body = draft(&source, &update, FormulaCachePolicy::Update, 'a', 'b');
    assert!(matches!(
        TableAbsoluteReferenceHwpxRequest::from_draft(invalid_body, &source, &flow('a'), limits()?),
        Err(TableAbsoluteReferenceHwpxError::InvalidReferenceTransition)
    ));

    let update = formula("SUM($A2:B$2)", decimal_cache(13))?;
    let (request, plan) = admitted(
        &source,
        draft(&source, &update, FormulaCachePolicy::Update, 'a', 'b'),
        'a',
    )?;
    let updated = TableAbsoluteReferenceHwpxLowerer::lower(
        HEADER,
        &section,
        &flow('a'),
        &request,
        &plan,
        limits()?,
    )?;
    assert!(String::from_utf8(updated.section.clone())?.contains(";;13"));
    let absolute_source = read(&updated.section)?;
    let cache_only = formula("SUM($A2:B$2)", decimal_cache(14))?;
    assert!(matches!(
        TableAbsoluteReferenceHwpxRequest::from_draft(
            draft(
                &absolute_source,
                &cache_only,
                FormulaCachePolicy::Update,
                'b',
                'e'
            ),
            &absolute_source,
            &flow('b'),
            limits()?
        ),
        Err(TableAbsoluteReferenceHwpxError::InvalidReferenceTransition)
    ));
    let downgrade = formula("SUM(A2:B$2)", decimal_cache(13))?;
    assert!(matches!(
        TableAbsoluteReferenceHwpxRequest::from_draft(
            draft(
                &absolute_source,
                &downgrade,
                FormulaCachePolicy::Preserve,
                'b',
                'e'
            ),
            &absolute_source,
            &flow('b'),
            limits()?
        ),
        Err(TableAbsoluteReferenceHwpxError::InvalidReferenceTransition)
    ));

    let cleared = formula("SUM($A2:B$2)", FormulaCache::Absent)?;
    let (request, plan) = admitted(
        &source,
        draft(&source, &cleared, FormulaCachePolicy::Clear, 'c', 'd'),
        'c',
    )?;
    let output = TableAbsoluteReferenceHwpxLowerer::lower(
        HEADER,
        &section,
        &flow('c'),
        &request,
        &plan,
        limits()?,
    )?;
    let text = String::from_utf8(output.section.clone())?;
    assert!(text.contains("=SUM($A2:B$2)??%g,;;</hp:stringParam>"));
    assert!(text.contains("name=\"LastResult\"></hp:stringParam>"));
    assert_eq!(
        read(&output.section)?.formula.cache(),
        &FormulaCache::Absent
    );
    Ok(())
}

#[test]
fn invalid_anchor_coordinate_operator_cache_and_recalculate_fail_closed() -> TestResult {
    let source = read(&section())?;
    for invalid in [
        formula("SUM(A2:B2)", decimal_cache(12))?,
        formula("SUM($A1:B$2)", decimal_cache(12))?,
        formula("PRODUCT($A2:B$2)", decimal_cache(12))?,
    ] {
        assert!(matches!(
            TableAbsoluteReferenceHwpxRequest::from_draft(
                draft(&source, &invalid, FormulaCachePolicy::Preserve, '0', '1'),
                &source,
                &flow('0'),
                limits()?
            ),
            Err(TableAbsoluteReferenceHwpxError::InvalidReferenceTransition
                | TableAbsoluteReferenceHwpxError::CachePolicyMismatch)
        ));
    }
    let target = formula("SUM($A2:B$2)", decimal_cache(12))?;
    let mut recalculate = draft(&source, &target, FormulaCachePolicy::Preserve, '0', '1');
    recalculate.recalculate = true;
    assert!(matches!(
        TableAbsoluteReferenceHwpxRequest::from_draft(recalculate, &source, &flow('0'), limits()?),
        Err(TableAbsoluteReferenceHwpxError::UnsupportedRecalculate)
    ));
    let cache_mismatch = draft(&source, &target, FormulaCachePolicy::Clear, '0', '1');
    assert!(matches!(
        TableAbsoluteReferenceHwpxRequest::from_draft(
            cache_mismatch,
            &source,
            &flow('0'),
            limits()?
        ),
        Err(TableAbsoluteReferenceHwpxError::CachePolicyMismatch)
    ));
    let mut non_general = draft(&source, &target, FormulaCachePolicy::Preserve, '0', '1');
    non_general.target_formula.number_format = FormulaNumberFormat::Number {
        decimal_places: 2,
        use_grouping: false,
    };
    assert!(
        TableAbsoluteReferenceHwpxRequest::from_draft(non_general, &source, &flow('0'), limits()?)
            .is_err()
    );
    let mut non_decimal = draft(&source, &target, FormulaCachePolicy::Update, '0', '1');
    non_decimal.target_formula.cache = FormulaCache::Unverified {
        value: FormulaValue::Boolean { value: true },
    };
    assert!(matches!(
        TableAbsoluteReferenceHwpxRequest::from_draft(non_decimal, &source, &flow('0'), limits()?),
        Err(TableAbsoluteReferenceHwpxError::CachePolicyMismatch)
    ));
    Ok(())
}

#[test]
fn request_json_and_every_source_binding_fail_closed_on_tamper() -> TestResult {
    let source = read(&section())?;
    let target = formula("SUM($A2:B$2)", decimal_cache(12))?;
    let base = draft(&source, &target, FormulaCachePolicy::Preserve, '0', '1');
    for name in [
        "header",
        "section",
        "table",
        "formula",
        "unowned",
        "pagination",
        "table_count",
        "formula_count",
        "owner",
        "flow",
    ] {
        let mut tampered = base.clone();
        match name {
            "header" => tampered.expected_header_sha256 = flow('f'),
            "section" => tampered.expected_section_sha256 = flow('f'),
            "table" => tampered.expected_table_content_sha256 = flow('f'),
            "formula" => tampered.expected_source_formula_sha256 = flow('f'),
            "unowned" => tampered.expected_selected_unowned_sha256 = flow('f'),
            "pagination" => tampered.expected_pagination_policy_sha256 = flow('f'),
            "table_count" => tampered.expected_source_table_count += 1,
            "formula_count" => tampered.expected_formula_field_count += 1,
            "owner" => tampered.owner = CellCoordinate { row: 1, column: 1 },
            "flow" => tampered.expected_document_flow_sha256 = flow('f'),
            _ => unreachable!(),
        }
        assert!(
            TableAbsoluteReferenceHwpxRequest::from_draft(tampered, &source, &flow('0'), limits()?)
                .is_err()
        );
    }
    let request =
        TableAbsoluteReferenceHwpxRequest::from_draft(base, &source, &flow('0'), limits()?)?;
    let json = request.canonical_json(limits()?)?;
    assert_eq!(
        TableAbsoluteReferenceHwpxRequest::from_json(&json, &source, &flow('0'), limits()?)?,
        request
    );
    let duplicate = String::from_utf8(json.clone())?.replacen(
        '{',
        "{\"schema_version\":\"hwpx-agent.table-absolute-reference-hwpx/v1\",",
        1,
    );
    assert!(matches!(
        TableAbsoluteReferenceHwpxRequest::from_json(
            duplicate.as_bytes(),
            &source,
            &flow('0'),
            limits()?
        ),
        Err(TableAbsoluteReferenceHwpxError::InvalidJson)
    ));
    let unknown = String::from_utf8(json)?.replacen('{', "{\"unknown\":true,", 1);
    assert!(matches!(
        TableAbsoluteReferenceHwpxRequest::from_json(
            unknown.as_bytes(),
            &source,
            &flow('0'),
            limits()?
        ),
        Err(TableAbsoluteReferenceHwpxError::InvalidJson)
    ));
    Ok(())
}

#[test]
fn builder_and_lowerer_repeat_source_flow_and_plan_checks() -> TestResult {
    let section = section();
    let source = read(&section)?;
    let target = formula("SUM($A2:B$2)", decimal_cache(12))?;
    let (request, plan) = admitted(
        &source,
        draft(&source, &target, FormulaCachePolicy::Preserve, '0', '1'),
        '0',
    )?;
    assert!(matches!(
        TableAbsoluteReferenceHwpxBuilder::build(&request, &source, &flow('9'), limits()?),
        Err(TableAbsoluteReferenceHwpxError::SourceBindingMismatch)
    ));
    let drifted = section
        .windows(b"BEFORE".len())
        .position(|window| window == b"BEFORE")
        .ok_or("marker missing")?;
    let mut changed_section = section.clone();
    changed_section[drifted] = b'X';
    assert!(
        TableAbsoluteReferenceHwpxLowerer::lower(
            HEADER,
            &changed_section,
            &flow('0'),
            &request,
            &plan,
            limits()?
        )
        .is_err()
    );
    let other = formula("SUM($A2:$B$2)", decimal_cache(12))?;
    let (_, other_plan) = admitted(
        &source,
        draft(&source, &other, FormulaCachePolicy::Preserve, '0', '1'),
        '0',
    )?;
    assert!(matches!(
        TableAbsoluteReferenceHwpxLowerer::lower(
            HEADER,
            &section,
            &flow('0'),
            &request,
            &other_plan,
            limits()?
        ),
        Err(TableAbsoluteReferenceHwpxError::PlanBindingMismatch)
    ));
    Ok(())
}

#[test]
fn selected_owner_native_shape_and_finite_limits_are_exact() -> TestResult {
    let section = section();
    assert!(
        TableAbsoluteReferenceHwpxReader::read_context(
            HEADER,
            &section,
            0,
            CellCoordinate { row: 0, column: 1 },
            limits()?
        )
        .is_err()
    );
    let duplicate = String::from_utf8(section.clone())?.replace(
        "<hp:p id=\"12\"",
        &format!(
            "{}<hp:p id=\"12\"",
            formula_paragraph(1, 2, 103, 203, "SUM(A2:B2)", "12")
        ),
    );
    assert!(
        TableAbsoluteReferenceHwpxReader::read_context(
            HEADER,
            duplicate.as_bytes(),
            0,
            OWNER,
            limits()?
        )
        .is_err()
    );
    for invalid in [
        String::from_utf8(section.clone())?.replace("=SUM(A2:B2)", "=SUM( A2:B2)"),
        String::from_utf8(section.clone())?.replace(";;12", ";;012"),
        String::from_utf8(section.clone())?.replace("fieldid=\"202\"/>", "fieldid=\"999\"/>"),
    ] {
        assert!(
            TableAbsoluteReferenceHwpxReader::read_context(
                HEADER,
                invalid.as_bytes(),
                0,
                OWNER,
                limits()?
            )
            .is_err()
        );
    }
    let mut tiny = limits()?;
    tiny.native =
        hwpx_package::TableFormulaHwpxLimits::new(hwpx_package::TableFormulaHwpxLimitConfig {
            input_bytes: 8,
            ..hwpx_package::TableFormulaHwpxLimitConfig::default()
        })?;
    assert!(matches!(
        TableAbsoluteReferenceHwpxReader::read_context(HEADER, &section, 0, OWNER, tiny),
        Err(TableAbsoluteReferenceHwpxError::InputLimit
            | TableAbsoluteReferenceHwpxError::Native(_))
    ));
    Ok(())
}

#[test]
fn already_absolute_noop_is_byte_exact_and_debug_is_redacted() -> TestResult {
    let section = format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{table}</hs:sec>"#,
        table = table("A2", "SUM($A2:B$2)", "12"),
    )
    .into_bytes();
    let source = read(&section)?;
    let target = source.formula.clone();
    let (request, plan) = admitted(
        &source,
        draft(&source, &target, FormulaCachePolicy::Preserve, '0', '0'),
        '0',
    )?;
    assert!(!plan.semantic_change());
    assert_eq!(plan.changed_axis_count(), 0);
    let output = TableAbsoluteReferenceHwpxLowerer::lower(
        HEADER,
        &section,
        &flow('0'),
        &request,
        &plan,
        limits()?,
    )?;
    assert_eq!(output.header, HEADER);
    assert_eq!(output.section, section);
    assert_eq!(output.receipt.modified_text_count, 0);
    let debug = format!("{source:?} {request:?} {plan:?} {output:?}");
    for private in ["SUM($A2:B$2)", "12", &flow('0')] {
        assert!(!debug.contains(private));
    }
    Ok(())
}

fn package(section: &[u8]) -> TestResult<Vec<u8>> {
    let mut cursor = Cursor::new(Vec::new());
    {
        let mut writer = ZipWriter::new(&mut cursor);
        let stored = SimpleFileOptions::default()
            .compression_method(CompressionMethod::Stored)
            .last_modified_time(DateTime::default());
        let deflated = SimpleFileOptions::default()
            .compression_method(CompressionMethod::Deflated)
            .last_modified_time(DateTime::default());
        writer.start_file("mimetype", stored)?;
        writer.write_all(b"application/hwp+zip")?;
        writer.start_file("version.xml", stored)?;
        writer.write_all(b"<version/>")?;
        writer.start_file("META-INF/container.xml", deflated)?;
        writer.write_all(CONTAINER.as_bytes())?;
        writer.start_file("Contents/content.hpf", deflated)?;
        writer.write_all(OPF.as_bytes())?;
        writer.start_file("Contents/header.xml", deflated)?;
        writer.write_all(HEADER)?;
        writer.start_file("Contents/section0.xml", deflated)?;
        writer.write_all(section)?;
        writer.start_file("Contents/opaque.bin", stored)?;
        writer.write_all(b"opaque-absolute-reference-evidence")?;
        writer.finish()?;
    }
    Ok(cursor.into_inner())
}

fn repack(source: &[u8], header: &[u8], section: &[u8]) -> TestResult<Vec<u8>> {
    let mut input = ZipArchive::new(Cursor::new(source))?;
    let mut cursor = Cursor::new(Vec::new());
    {
        let mut writer = ZipWriter::new(&mut cursor);
        for index in 0..input.len() {
            let mut entry = input.by_index(index)?;
            let mut bytes = Vec::new();
            std::io::copy(&mut entry, &mut bytes)?;
            let replacement = match entry.name() {
                "Contents/header.xml" => header,
                "Contents/section0.xml" => section,
                _ => &bytes,
            };
            let method = entry.compression();
            writer.start_file(
                entry.name(),
                SimpleFileOptions::default()
                    .compression_method(method)
                    .last_modified_time(DateTime::default()),
            )?;
            writer.write_all(replacement)?;
        }
        writer.finish()?;
    }
    Ok(cursor.into_inner())
}

fn read_package_entry(
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

#[test]
fn closed_package_graph_and_every_non_target_part_are_preserved() -> TestResult {
    let section = section();
    let source = read(&section)?;
    let target = formula("SUM($A2:B$2)", decimal_cache(12))?;
    let (request, plan) = admitted(
        &source,
        draft(&source, &target, FormulaCachePolicy::Preserve, '0', '1'),
        '0',
    )?;
    let output = TableAbsoluteReferenceHwpxLowerer::lower(
        HEADER,
        &section,
        &flow('0'),
        &request,
        &plan,
        limits()?,
    )?;
    let source_package = package(&section)?;
    let target_package = repack(&source_package, &output.header, &output.section)?;
    let package_limits = PackageLimits::default();
    let mut source_reader = BoundedZipReader::open(Cursor::new(source_package), package_limits)?;
    let mut target_reader = BoundedZipReader::open(Cursor::new(target_package), package_limits)?;
    let source_graph = PackageGraph::build(&mut source_reader, PackageGraphLimits::default())?;
    let target_graph = PackageGraph::build(&mut target_reader, PackageGraphLimits::default())?;
    assert_eq!(source_graph.spine, target_graph.spine);
    assert_eq!(source_graph.relationships, target_graph.relationships);
    let source_paths = source_reader
        .entries()
        .iter()
        .map(|entry| entry.path.as_str().to_owned())
        .collect::<Vec<_>>();
    let target_paths = target_reader
        .entries()
        .iter()
        .map(|entry| entry.path.as_str().to_owned())
        .collect::<Vec<_>>();
    assert_eq!(source_paths, target_paths);
    let source_compression = source_reader
        .entries()
        .iter()
        .map(|entry| (entry.path.as_str().to_owned(), entry.compression))
        .collect::<Vec<_>>();
    let target_compression = target_reader
        .entries()
        .iter()
        .map(|entry| (entry.path.as_str().to_owned(), entry.compression))
        .collect::<Vec<_>>();
    assert_eq!(source_compression, target_compression);
    for path in source_paths
        .iter()
        .filter(|path| path.as_str() != "Contents/section0.xml")
    {
        assert_eq!(
            read_package_entry(&mut source_reader, path)?,
            read_package_entry(&mut target_reader, path)?,
            "non-target package part drifted: {path}"
        );
    }
    assert_eq!(
        target_reader
            .entries()
            .iter()
            .find(|entry| entry.path.as_str() == "mimetype")
            .map(|entry| entry.compression),
        Some(Compression::Stored)
    );
    let reopened_section = read_package_entry(&mut target_reader, "Contents/section0.xml")?;
    assert_eq!(read(&reopened_section)?.formula, target);
    Ok(())
}
