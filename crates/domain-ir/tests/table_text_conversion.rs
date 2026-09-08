use domain_ir::{
    TABLE_TABLE_TO_TEXT_CAPABILITY_ID, TABLE_TEXT_CONVERSION_SCHEMA_VERSION,
    TABLE_TEXT_TO_TABLE_CAPABILITY_ID, TableDelimiter, TableLineEnding, TableTextConversionError,
    TableTextConversionLimitConfig, TableTextConversionLimits, TableTextGrid, TableTextGridDraft,
};

type TestResult = Result<(), Box<dyn std::error::Error>>;

fn limits() -> TableTextConversionLimits {
    TableTextConversionLimits::default()
}

fn grid(rows: &[&[&str]]) -> Result<TableTextGrid, TableTextConversionError> {
    TableTextGrid::from_draft(
        TableTextGridDraft {
            schema_version: TABLE_TEXT_CONVERSION_SCHEMA_VERSION.to_owned(),
            rows: rows
                .iter()
                .map(|row| row.iter().map(|cell| (*cell).to_owned()).collect())
                .collect(),
        },
        limits(),
    )
}

#[test]
fn tab_text_parses_to_exact_rectangular_unicode_grid() -> TestResult {
    let parsed = TableTextGrid::parse_delimited(
        "이름\t값\n가\t1\n나\t2".as_bytes(),
        TableDelimiter::Tab,
        limits(),
    )?;
    assert_eq!(parsed.row_count(), 3);
    assert_eq!(parsed.column_count(), 2);
    assert_eq!(parsed.cell(0, 0), Some("이름"));
    assert_eq!(parsed.cell(1, 0), Some("가"));
    assert_eq!(parsed.cell(2, 1), Some("2"));
    assert_eq!(TABLE_TEXT_TO_TABLE_CAPABILITY_ID, "table.text_to_table");
    assert_eq!(TABLE_TABLE_TO_TEXT_CAPABILITY_ID, "table.table_to_text");
    Ok(())
}

#[test]
fn quoted_csv_accepts_crlf_delimiters_quotes_and_semantic_newlines() -> TestResult {
    let input = concat!(
        "name,note\r\n",
        "\"A, B\",\"line1\r\nline2\"\r\n",
        "quote,\"He said \"\"yes\"\"\"\r\n"
    );
    let parsed = TableTextGrid::parse_delimited(input.as_bytes(), TableDelimiter::Comma, limits())?;
    assert_eq!(parsed.row_count(), 3);
    assert_eq!(parsed.cell(1, 0), Some("A, B"));
    assert_eq!(parsed.cell(1, 1), Some("line1\nline2"));
    assert_eq!(parsed.cell(2, 1), Some("He said \"yes\""));
    Ok(())
}

#[test]
fn deterministic_writer_quotes_minimally_and_roundtrips_both_line_endings() -> TestResult {
    let value = grid(&[
        &["name", "note"],
        &["A,B", "line1\nline2"],
        &["quote", "He said \"yes\""],
    ])?;
    let crlf = value.to_delimited(TableDelimiter::Comma, TableLineEnding::CrLf, limits())?;
    assert_eq!(
        String::from_utf8(crlf.clone())?,
        concat!(
            "name,note\r\n",
            "\"A,B\",\"line1\r\nline2\"\r\n",
            "quote,\"He said \"\"yes\"\"\""
        )
    );
    assert_eq!(
        TableTextGrid::parse_delimited(&crlf, TableDelimiter::Comma, limits())?,
        value
    );

    let lf = value.to_delimited(TableDelimiter::Semicolon, TableLineEnding::Lf, limits())?;
    assert_eq!(
        TableTextGrid::parse_delimited(&lf, TableDelimiter::Semicolon, limits())?,
        value
    );
    Ok(())
}

#[test]
fn final_record_ending_and_empty_fields_are_unambiguous() -> TestResult {
    let with_final = TableTextGrid::parse_delimited(b"a,\n,b\n", TableDelimiter::Comma, limits())?;
    let without_final = TableTextGrid::parse_delimited(b"a,\n,b", TableDelimiter::Comma, limits())?;
    assert_eq!(with_final, without_final);
    assert_eq!(
        with_final.rows(),
        &[
            vec!["a".to_owned(), String::new()],
            vec![String::new(), "b".to_owned()]
        ]
    );
    assert_eq!(
        with_final.to_delimited(TableDelimiter::Comma, TableLineEnding::Lf, limits())?,
        b"a,\n,b"
    );
    Ok(())
}

#[test]
fn malformed_quotes_line_endings_controls_and_ragged_rows_fail_closed() {
    for invalid in [b"a\"b,c".as_slice(), b"\"a\"x,b", b"\"a,b", b"a\rb"] {
        assert!(matches!(
            TableTextGrid::parse_delimited(invalid, TableDelimiter::Comma, limits()),
            Err(TableTextConversionError::InvalidQuotedField
                | TableTextConversionError::InvalidLineEnding)
        ));
    }
    assert_eq!(
        TableTextGrid::parse_delimited(b"a,b\nc", TableDelimiter::Comma, limits()),
        Err(TableTextConversionError::RaggedRows)
    );
    assert_eq!(
        TableTextGrid::parse_delimited(b"a,\0", TableDelimiter::Comma, limits()),
        Err(TableTextConversionError::InvalidControl)
    );
}

#[test]
fn strict_grid_json_rejects_duplicate_unknown_version_and_invalid_content() -> TestResult {
    let valid =
        br#"{"schema_version":"hwpx-agent.table-text-conversion/v1","rows":[["a","b"],["c","d"]]}"#;
    assert_eq!(
        TableTextGrid::from_json(valid, limits())?.cell(1, 1),
        Some("d")
    );
    for invalid in [
        br#"{"schema_version":"hwpx-agent.table-text-conversion/v1","schema_version":"duplicate","rows":[["a"]]}"#.as_slice(),
        br#"{"schema_version":"hwpx-agent.table-text-conversion/v1","rows":[["a"]],"unknown":true}"#.as_slice(),
    ] {
        assert_eq!(
            TableTextGrid::from_json(invalid, limits()),
            Err(TableTextConversionError::InvalidJson)
        );
    }
    let wrong = valid
        .windows(TABLE_TEXT_CONVERSION_SCHEMA_VERSION.len())
        .position(|window| window == TABLE_TEXT_CONVERSION_SCHEMA_VERSION.as_bytes())
        .ok_or("version marker missing")?;
    let mut wrong_version = valid.to_vec();
    wrong_version[wrong] = b'x';
    assert_eq!(
        TableTextGrid::from_json(&wrong_version, limits()),
        Err(TableTextConversionError::UnsupportedVersion)
    );
    assert_eq!(
        grid(&[&["a\r"]]),
        Err(TableTextConversionError::InvalidControl)
    );
    Ok(())
}

#[test]
fn every_finite_limit_is_enforced() -> TestResult {
    let configured = |changes: fn(&mut TableTextConversionLimitConfig)| {
        let mut config = TableTextConversionLimitConfig::default();
        changes(&mut config);
        TableTextConversionLimits::new(config)
    };

    let input_limit = configured(|config| config.input_bytes = 2)?;
    assert_eq!(
        TableTextGrid::parse_delimited(b"abc", TableDelimiter::Comma, input_limit),
        Err(TableTextConversionError::InputLimit)
    );
    let row_limit = configured(|config| config.rows = 1)?;
    assert_eq!(
        TableTextGrid::parse_delimited(b"a\nb", TableDelimiter::Comma, row_limit),
        Err(TableTextConversionError::RowLimit)
    );
    let column_limit = configured(|config| config.columns = 1)?;
    assert_eq!(
        TableTextGrid::parse_delimited(b"a,b", TableDelimiter::Comma, column_limit),
        Err(TableTextConversionError::ColumnLimit)
    );
    let cell_limit = configured(|config| config.cells = 1)?;
    assert_eq!(
        TableTextGrid::parse_delimited(b"a,b", TableDelimiter::Comma, cell_limit),
        Err(TableTextConversionError::CellLimit)
    );
    let cell_bytes = configured(|config| config.cell_bytes = 1)?;
    assert_eq!(
        TableTextGrid::parse_delimited("é".as_bytes(), TableDelimiter::Comma, cell_bytes),
        Err(TableTextConversionError::CellBytes)
    );

    let value = grid(&[&["a,b"]])?;
    let output_limit = configured(|config| config.output_bytes = 2)?;
    assert_eq!(
        value.to_delimited(TableDelimiter::Comma, TableLineEnding::Lf, output_limit),
        Err(TableTextConversionError::OutputLimit)
    );
    let serialized_limit = configured(|config| config.serialized_bytes = 2)?;
    assert_eq!(
        value.canonical_json(serialized_limit),
        Err(TableTextConversionError::OutputLimit)
    );
    assert_eq!(
        TableTextConversionLimits::new(TableTextConversionLimitConfig {
            rows: 0,
            ..TableTextConversionLimitConfig::default()
        }),
        Err(TableTextConversionError::InvalidLimit)
    );
    Ok(())
}

#[test]
fn canonical_json_sha_and_debug_are_deterministic_and_private() -> TestResult {
    let first = grid(&[&["private-value", "2"]])?;
    let second = grid(&[&["private-value", "2"]])?;
    let canonical = first.canonical_json(limits())?;
    assert_eq!(canonical, second.canonical_json(limits())?);
    assert_eq!(TableTextGrid::from_json(&canonical, limits())?, first);
    assert_eq!(
        first.canonical_sha256(limits())?,
        second.canonical_sha256(limits())?
    );
    let debug = format!("{first:?}");
    assert!(!debug.contains("private-value"));
    assert!(debug.contains("content: \"<redacted>\""));
    Ok(())
}

#[test]
fn public_error_codes_are_stable() {
    assert_eq!(
        TableTextConversionError::InvalidUtf8.code(),
        "table_text_conversion_invalid_utf8"
    );
    assert_eq!(
        TableTextConversionError::RaggedRows.code(),
        "table_text_conversion_ragged_rows"
    );
    assert_eq!(
        TableTextConversionError::InvalidQuotedField.code(),
        "table_text_conversion_invalid_quoted_field"
    );
    assert_eq!(
        TableTextConversionError::OutputLimit.code(),
        "table_text_conversion_output_limit"
    );
}
