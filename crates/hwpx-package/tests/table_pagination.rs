use domain_ir::{CaptionSide, FormulaLimitConfig, FormulaLimits, TablePageSplitPolicy};
use hwpx_package::{
    TABLE_PAGINATION_HWPX_PROFILE_ID, TableCaptionHwpxTarget, TableFormulaHwpxLimits,
    TableFormulaHwpxReader, TablePaginationHwpxError, TablePaginationHwpxLimitConfig,
    TablePaginationHwpxLimits, TablePaginationHwpxLowerer, TablePaginationHwpxReader,
    TablePaginationHwpxTarget,
};
use sha2::{Digest as _, Sha256};

trait Must<T> {
    fn must(self, message: &str) -> T;
}

impl<T, E: std::fmt::Debug> Must<T> for Result<T, E> {
    #[track_caller]
    fn must(self, message: &str) -> T {
        match self {
            Ok(value) => value,
            Err(error) => panic!("{message}: {error:?}"),
        }
    }
}

impl<T> Must<T> for Option<T> {
    #[track_caller]
    fn must(self, message: &str) -> T {
        match self {
            Some(value) => value,
            None => panic!("{message}"),
        }
    }
}

trait MustErr<E> {
    fn must_err(self, message: &str) -> E;
}

impl<T, E> MustErr<E> for Result<T, E> {
    #[track_caller]
    fn must_err(self, message: &str) -> E {
        match self {
            Ok(_) => panic!("{message}"),
            Err(error) => error,
        }
    }
}

const HP_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const HS_NS: &str = "http://www.hancom.co.kr/hwpml/2011/section";

fn table_body(page_break: &str, repeat_header: &str, caption: bool) -> String {
    let caption = if caption {
        concat!(
            "<hp:caption side=\"TOP\" fullSz=\"0\" width=\"42520\" gap=\"850\" ",
            "lastWidth=\"42520\"><hp:subList><hp:p><hp:run><hp:t>",
            "CAPTION &amp; LABEL",
            "</hp:t></hp:run></hp:p></hp:subList></hp:caption>"
        )
    } else {
        ""
    };
    format!(
        concat!(
            "<hp:tbl lock=\"0\" pageBreak=\"{}\" repeatHeader=\"{}\" rowCnt=\"1\" ",
            "colCnt=\"1\" cellSpacing=\"0\" noAdjust=\"0\">",
            "<hp:sz/><hp:pos/><hp:outMargin/>{}<hp:inMargin/>",
            "<hp:tr><hp:tc header=\"{}\"/></hp:tr>",
            "</hp:tbl>"
        ),
        page_break, repeat_header, caption, repeat_header
    )
}

fn standalone(page_break: &str, repeat_header: &str, caption: bool) -> Vec<u8> {
    table_body(page_break, repeat_header, caption)
        .replacen("<hp:tbl", &format!("<hp:tbl xmlns:hp=\"{HP_NS}\""), 1)
        .into_bytes()
}

fn section(tables: &[String]) -> Vec<u8> {
    format!(
        "<hs:sec xmlns:hs=\"{HS_NS}\" xmlns:hp=\"{HP_NS}\">{}</hs:sec>",
        tables.join("")
    )
    .into_bytes()
}

fn formula_limits() -> FormulaLimits {
    FormulaLimits::new(FormulaLimitConfig {
        rows: 8,
        columns: 8,
        ..FormulaLimitConfig::default()
    })
    .must("formula limits")
}

fn formula_table_body(page_break: &str, repeat_header: &str, caption: bool) -> String {
    let row = format!(
        concat!(
            "<hp:tr>",
            "<hp:tc header=\"{0}\"><hp:subList><hp:p><hp:run><hp:t>17</hp:t>",
            "</hp:run></hp:p></hp:subList><hp:cellAddr colAddr=\"0\" rowAddr=\"0\"/>",
            "<hp:cellSpan colSpan=\"1\" rowSpan=\"1\"/></hp:tc>",
            "<hp:tc header=\"{0}\"><hp:subList><hp:p><hp:run><hp:t>25</hp:t>",
            "</hp:run></hp:p></hp:subList><hp:cellAddr colAddr=\"1\" rowAddr=\"0\"/>",
            "<hp:cellSpan colSpan=\"1\" rowSpan=\"1\"/></hp:tc>",
            "<hp:tc header=\"{0}\"><hp:subList><hp:p><hp:run charPrIDRef=\"0\"><hp:ctrl>",
            "<hp:fieldBegin id=\"101\" type=\"FORMULA\" name=\"\" editable=\"0\" dirty=\"0\" ",
            "zorder=\"-1\" fieldid=\"202\"><hp:parameters cnt=\"5\" name=\"\">",
            "<hp:integerParam name=\"Prop\">8</hp:integerParam>",
            "<hp:stringParam name=\"Command\">=SUM(LEFT)??%g,;;42</hp:stringParam>",
            "<hp:stringParam name=\"Formula\">=SUM(LEFT)</hp:stringParam>",
            "<hp:stringParam name=\"ResultFormat\">%g,</hp:stringParam>",
            "<hp:stringParam name=\"LastResult\">42</hp:stringParam>",
            "</hp:parameters></hp:fieldBegin></hp:ctrl><hp:t>42</hp:t><hp:ctrl>",
            "<hp:fieldEnd beginIDRef=\"101\" fieldid=\"202\"/></hp:ctrl><hp:t/></hp:run>",
            "</hp:p></hp:subList><hp:cellAddr colAddr=\"2\" rowAddr=\"0\"/>",
            "<hp:cellSpan colSpan=\"1\" rowSpan=\"1\"/></hp:tc></hp:tr>"
        ),
        repeat_header
    );
    table_body(page_break, repeat_header, caption)
        .replace("colCnt=\"1\"", "colCnt=\"3\"")
        .replace(
            &format!("<hp:tr><hp:tc header=\"{repeat_header}\"/></hp:tr>"),
            &row,
        )
}

fn target(
    page_split: TablePageSplitPolicy,
    repeat_header_rows: u32,
    caption: TableCaptionHwpxTarget,
) -> TablePaginationHwpxTarget {
    TablePaginationHwpxTarget {
        page_split,
        repeat_header_rows,
        caption,
    }
}

#[test]
fn reads_all_native_page_break_mappings() {
    for (native, expected) in [
        ("CELL", TablePageSplitPolicy::Allow),
        ("TABLE", TablePageSplitPolicy::AvoidRow),
        ("NONE", TablePageSplitPolicy::AvoidTable),
    ] {
        let readback = TablePaginationHwpxReader::read(
            &standalone(native, "1", false),
            TablePaginationHwpxLimits::default(),
        )
        .must("mapping should be admitted");
        assert_eq!(readback.profile_id, TABLE_PAGINATION_HWPX_PROFILE_ID);
        assert_eq!(readback.page_split, expected);
        assert_eq!(readback.repeat_header_rows, 1);
        assert_eq!((readback.row_count, readback.column_count), (1, 1));
        assert!(readback.caption.is_none());
    }
}

#[test]
fn lowers_only_changed_table_attributes_and_is_idempotent() {
    let source = standalone("CELL", "1", false);
    let original = source.clone();
    let target = target(
        TablePageSplitPolicy::AvoidRow,
        0,
        TableCaptionHwpxTarget::Absent,
    );
    let (output, receipt) = TablePaginationHwpxLowerer::lower_with_receipt(
        &source,
        &target,
        TablePaginationHwpxLimits::default(),
    )
    .must("exact mapping should lower");
    assert_eq!(source, original, "the source buffer must stay untouched");
    let expected = String::from_utf8(source.clone())
        .must("fixture utf-8")
        .replace("pageBreak=\"CELL\"", "pageBreak=\"TABLE\"")
        .replace("repeatHeader=\"1\"", "repeatHeader=\"0\"")
        .replace("header=\"1\"", "header=\"0\"")
        .into_bytes();
    assert_eq!(output, expected);
    assert_eq!(receipt.modified_attribute_count, 3);
    let source_sha256: [u8; 32] = Sha256::digest(&source).into();
    let output_sha256: [u8; 32] = Sha256::digest(&output).into();
    assert_eq!(receipt.source_sha256, source_sha256);
    assert_eq!(receipt.output_sha256, output_sha256);
    assert_eq!(receipt.readback.page_split, TablePageSplitPolicy::AvoidRow);

    let (second, second_receipt) = TablePaginationHwpxLowerer::lower_with_receipt(
        &output,
        &target,
        TablePaginationHwpxLimits::default(),
    )
    .must("a repeated lower must be stable");
    assert_eq!(second, output);
    assert_eq!(second_receipt.modified_attribute_count, 0);
}

#[test]
fn lowers_a_contiguous_multirow_header_prefix() {
    let source = String::from_utf8(standalone("CELL", "0", false))
        .must("fixture")
        .replace("rowCnt=\"1\"", "rowCnt=\"3\"")
        .replace(
            "<hp:tr><hp:tc header=\"0\"/></hp:tr>",
            concat!(
                "<hp:tr><hp:tc header=\"0\"/></hp:tr>",
                "<hp:tr><hp:tc header=\"0\"/></hp:tr>",
                "<hp:tr><hp:tc header=\"0\"/></hp:tr>"
            ),
        )
        .into_bytes();
    let target = target(
        TablePageSplitPolicy::Allow,
        2,
        TableCaptionHwpxTarget::Absent,
    );
    let (output, receipt) = TablePaginationHwpxLowerer::lower_with_receipt(
        &source,
        &target,
        TablePaginationHwpxLimits::default(),
    )
    .must("two header rows should lower");
    assert_eq!(receipt.modified_attribute_count, 3);
    assert_eq!(receipt.readback.repeat_header_rows, 2);
    let output_text = String::from_utf8(output).must("output utf-8");
    assert_eq!(output_text.matches("header=\"1\"").count(), 2);
    assert_eq!(output_text.matches("header=\"0\"").count(), 1);
}

#[test]
fn updates_existing_caption_without_changing_its_content() {
    let source = standalone("CELL", "0", true);
    let source_readback =
        TablePaginationHwpxReader::read(&source, TablePaginationHwpxLimits::default())
            .must("caption source should read");
    let mut caption = source_readback.caption.must("caption should exist");
    let content_sha256 = caption.content_sha256;
    caption.side = CaptionSide::Bottom;
    caption.full_size = true;
    caption.width_hwpunit = 40000;
    caption.gap_hwpunit = 1000;
    caption.last_width_hwpunit = 39000;
    let target = target(
        TablePageSplitPolicy::Allow,
        0,
        TableCaptionHwpxTarget::Existing(caption.clone()),
    );
    let (output, receipt) = TablePaginationHwpxLowerer::lower_with_receipt(
        &source,
        &target,
        TablePaginationHwpxLimits::default(),
    )
    .must("existing caption attributes should lower");
    let output_text = String::from_utf8(output).must("output utf-8");
    for marker in [
        "side=\"BOTTOM\"",
        "fullSz=\"1\"",
        "width=\"40000\"",
        "gap=\"1000\"",
        "lastWidth=\"39000\"",
        "CAPTION &amp; LABEL",
    ] {
        assert!(output_text.contains(marker), "missing marker: {marker}");
    }
    assert_eq!(receipt.modified_attribute_count, 5);
    assert_eq!(receipt.readback.caption, Some(caption));
    assert_eq!(
        receipt
            .readback
            .caption
            .as_ref()
            .must("caption")
            .content_sha256,
        content_sha256
    );
}

#[test]
fn pagination_family_preserves_formula_semantics_in_one_batch() {
    let source = section(&[formula_table_body("CELL", "0", true)]);
    let source_formula = TableFormulaHwpxReader::read_in_section(
        &source,
        0,
        TableFormulaHwpxLimits::default(),
        formula_limits(),
    )
    .must("formula source should read");
    let source_pagination = TablePaginationHwpxReader::read_in_section(
        &source,
        0,
        TablePaginationHwpxLimits::default(),
    )
    .must("pagination source should read");
    let mut caption = source_pagination
        .caption
        .clone()
        .must("caption should exist");
    caption.side = CaptionSide::Bottom;
    caption.gap_hwpunit = 1000;

    let transitions = [
        target(
            TablePageSplitPolicy::AvoidRow,
            1,
            TableCaptionHwpxTarget::Existing(caption.clone()),
        ),
        target(
            TablePageSplitPolicy::AvoidTable,
            0,
            TableCaptionHwpxTarget::Existing(caption.clone()),
        ),
        target(
            TablePageSplitPolicy::Allow,
            0,
            TableCaptionHwpxTarget::Existing(caption),
        ),
    ];
    let mut current = source;
    for wanted in transitions {
        current = TablePaginationHwpxLowerer::lower_in_section(
            &current,
            0,
            &wanted,
            TablePaginationHwpxLimits::default(),
        )
        .must("pagination transition should lower");
        let formula = TableFormulaHwpxReader::read_in_section(
            &current,
            0,
            TableFormulaHwpxLimits::default(),
            formula_limits(),
        )
        .must("formula should survive pagination transition");
        let pagination = TablePaginationHwpxReader::read_in_section(
            &current,
            0,
            TablePaginationHwpxLimits::default(),
        )
        .must("pagination transition should reopen");

        assert_eq!(formula.formula, source_formula.formula);
        assert_eq!(
            formula.formula_field_count,
            source_formula.formula_field_count
        );
        assert_eq!(pagination.page_split, wanted.page_split);
        assert_eq!(pagination.repeat_header_rows, wanted.repeat_header_rows);
    }
}

#[test]
fn rejects_non_representable_policy_and_caption_presence_changes() {
    let without_caption = standalone("CELL", "0", false);
    let with_caption = standalone("CELL", "0", true);
    let keep = target(
        TablePageSplitPolicy::RequiredKeep,
        0,
        TableCaptionHwpxTarget::Preserve,
    );
    assert_eq!(
        TablePaginationHwpxLowerer::lower(
            &without_caption,
            &keep,
            TablePaginationHwpxLimits::default()
        )
        .must_err("required keep lacks an exact table attribute")
        .code(),
        "table_pagination_hwpx_unsupported_policy"
    );

    let repeated_two = target(
        TablePageSplitPolicy::Allow,
        2,
        TableCaptionHwpxTarget::Preserve,
    );
    assert_eq!(
        TablePaginationHwpxLowerer::lower(
            &without_caption,
            &repeated_two,
            TablePaginationHwpxLimits::default()
        )
        .must_err("requested header prefix exceeds the source row count")
        .code(),
        "table_pagination_hwpx_unsupported_policy"
    );

    let absent = target(
        TablePageSplitPolicy::Allow,
        0,
        TableCaptionHwpxTarget::Absent,
    );
    assert_eq!(
        TablePaginationHwpxLowerer::lower(
            &with_caption,
            &absent,
            TablePaginationHwpxLimits::default()
        )
        .must_err("caption removal is outside V1")
        .code(),
        "table_pagination_hwpx_caption_presence_mismatch"
    );

    let source_caption =
        TablePaginationHwpxReader::read(&with_caption, TablePaginationHwpxLimits::default())
            .must("source caption")
            .caption
            .must("caption");
    let create = target(
        TablePageSplitPolicy::Allow,
        0,
        TableCaptionHwpxTarget::Existing(source_caption),
    );
    assert_eq!(
        TablePaginationHwpxLowerer::lower(
            &without_caption,
            &create,
            TablePaginationHwpxLimits::default()
        )
        .must_err("caption creation is outside V1")
        .code(),
        "table_pagination_hwpx_caption_presence_mismatch"
    );
}

#[test]
fn rejects_caption_content_binding_drift() {
    let source = standalone("CELL", "0", true);
    let mut caption =
        TablePaginationHwpxReader::read(&source, TablePaginationHwpxLimits::default())
            .must("source caption")
            .caption
            .must("caption");
    caption.content_sha256 = [0x5a; 32];
    let target = target(
        TablePageSplitPolicy::Allow,
        0,
        TableCaptionHwpxTarget::Existing(caption),
    );
    assert_eq!(
        TablePaginationHwpxLowerer::lower(&source, &target, TablePaginationHwpxLimits::default())
            .must_err("content binding must be exact")
            .code(),
        "table_pagination_hwpx_caption_content_mismatch"
    );
}

#[test]
fn selects_tables_by_bounded_zero_based_section_order() {
    let source = section(&[
        table_body("CELL", "0", false),
        table_body("NONE", "1", true),
    ]);
    let limits = TablePaginationHwpxLimits::default();
    assert_eq!(
        TablePaginationHwpxReader::count_in_section(&source, limits).must("count"),
        2
    );
    let second = TablePaginationHwpxReader::read_in_section(&source, 1, limits)
        .must("second table should read");
    assert_eq!(second.page_split, TablePageSplitPolicy::AvoidTable);
    assert_eq!(second.repeat_header_rows, 1);
    assert!(second.caption.is_some());

    let target = target(
        TablePageSplitPolicy::AvoidRow,
        0,
        TableCaptionHwpxTarget::Preserve,
    );
    let output = TablePaginationHwpxLowerer::lower_in_section(&source, 1, &target, limits)
        .must("selected table should lower");
    let first = TablePaginationHwpxReader::read_in_section(&output, 0, limits)
        .must("first table should remain readable");
    let second = TablePaginationHwpxReader::read_in_section(&output, 1, limits)
        .must("second table should remain readable");
    assert_eq!(first.page_split, TablePageSplitPolicy::Allow);
    assert_eq!(second.page_split, TablePageSplitPolicy::AvoidRow);
}

#[test]
fn rejects_shape_enum_boolean_number_and_root_drift() {
    let limits = TablePaginationHwpxLimits::default();
    let cases = [
        (
            standalone("ROW", "0", false),
            "table_pagination_hwpx_unsupported_enum",
        ),
        (
            standalone("CELL", "true", false),
            "table_pagination_hwpx_invalid_boolean",
        ),
    ];
    for (source, code) in cases {
        assert_eq!(
            TablePaginationHwpxReader::read(&source, limits)
                .must_err("invalid fixture must fail")
                .code(),
            code
        );
    }

    let bad_number = String::from_utf8(standalone("CELL", "0", false))
        .must("fixture")
        .replace("rowCnt=\"1\"", "rowCnt=\"x\"")
        .into_bytes();
    assert_eq!(
        TablePaginationHwpxReader::read(&bad_number, limits)
            .must_err("invalid number must fail")
            .code(),
        "table_pagination_hwpx_invalid_number"
    );
    let unknown = String::from_utf8(standalone("CELL", "0", false))
        .must("fixture")
        .replace("lock=\"0\"", "lock=\"0\" surprise=\"1\"")
        .into_bytes();
    assert_eq!(
        TablePaginationHwpxReader::read(&unknown, limits)
            .must_err("unknown attribute must fail")
            .code(),
        "table_pagination_hwpx_unsupported_shape"
    );
    let duplicate_caption = String::from_utf8(standalone("CELL", "0", true))
        .must("fixture")
        .replace(
            "<hp:inMargin/>",
            concat!(
                "<hp:caption side=\"TOP\" fullSz=\"0\" width=\"1\" gap=\"1\" ",
                "lastWidth=\"1\"><hp:subList/></hp:caption><hp:inMargin/>"
            ),
        )
        .into_bytes();
    assert_eq!(
        TablePaginationHwpxReader::read(&duplicate_caption, limits)
            .must_err("duplicate caption must fail")
            .code(),
        "table_pagination_hwpx_unsupported_shape"
    );
    let wrong_root = format!("<hp:p xmlns:hp=\"{HP_NS}\"/>").into_bytes();
    assert_eq!(
        TablePaginationHwpxReader::read(&wrong_root, limits)
            .must_err("wrong root must fail")
            .code(),
        "table_pagination_hwpx_wrong_root"
    );

    let inconsistent_header = String::from_utf8(standalone("CELL", "1", false))
        .must("fixture")
        .replace("header=\"1\"", "header=\"0\"")
        .into_bytes();
    assert_eq!(
        TablePaginationHwpxReader::read(&inconsistent_header, limits)
            .must_err("table flag and cell header flags must agree")
            .code(),
        "table_pagination_hwpx_unsupported_shape"
    );
}

#[test]
fn enforces_finite_input_table_grid_and_dimension_limits() {
    let invalid = TablePaginationHwpxLimits::new(TablePaginationHwpxLimitConfig {
        input_bytes: 0,
        ..TablePaginationHwpxLimitConfig::default()
    })
    .must_err("zero limit must fail");
    assert_eq!(invalid.code(), "table_pagination_hwpx_invalid_limit");

    let input_limits = TablePaginationHwpxLimits::new(TablePaginationHwpxLimitConfig {
        input_bytes: 1,
        ..TablePaginationHwpxLimitConfig::default()
    })
    .must("bounded limits");
    assert_eq!(
        TablePaginationHwpxReader::read(b"xx", input_limits)
            .must_err("oversized input must fail")
            .code(),
        "table_pagination_hwpx_input_limit"
    );

    let grid_limits = TablePaginationHwpxLimits::new(TablePaginationHwpxLimitConfig {
        rows: 1,
        ..TablePaginationHwpxLimitConfig::default()
    })
    .must("bounded limits");
    let two_rows = String::from_utf8(standalone("CELL", "0", false))
        .must("fixture")
        .replace("rowCnt=\"1\"", "rowCnt=\"2\"")
        .replace(
            "<hp:tr><hp:tc header=\"0\"/></hp:tr>",
            concat!(
                "<hp:tr><hp:tc header=\"0\"/></hp:tr>",
                "<hp:tr><hp:tc header=\"0\"/></hp:tr>"
            ),
        )
        .into_bytes();
    assert_eq!(
        TablePaginationHwpxReader::read(&two_rows, grid_limits)
            .must_err("row limit must fail")
            .code(),
        "table_pagination_hwpx_grid_limit"
    );

    let dimension_limits = TablePaginationHwpxLimits::new(TablePaginationHwpxLimitConfig {
        dimension_hwpunit: 849,
        ..TablePaginationHwpxLimitConfig::default()
    })
    .must("bounded limits");
    assert_eq!(
        TablePaginationHwpxReader::read(&standalone("CELL", "0", true), dimension_limits)
            .must_err("caption dimension must be bounded")
            .code(),
        "table_pagination_hwpx_out_of_range"
    );

    let table_limits = TablePaginationHwpxLimits::new(TablePaginationHwpxLimitConfig {
        tables: 1,
        ..TablePaginationHwpxLimitConfig::default()
    })
    .must("bounded limits");
    let two_tables = section(&[
        table_body("CELL", "0", false),
        table_body("CELL", "0", false),
    ]);
    assert_eq!(
        TablePaginationHwpxReader::count_in_section(&two_tables, table_limits)
            .must_err("table count must be bounded")
            .code(),
        "table_pagination_hwpx_table_limit"
    );
}

#[test]
fn error_type_is_publicly_matchable() {
    let error = TablePaginationHwpxReader::read(b"", TablePaginationHwpxLimits::default())
        .must_err("empty input must fail");
    assert!(matches!(error, TablePaginationHwpxError::InputLimit));
}
