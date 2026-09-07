use domain_ir::{
    CellCoordinate, FormulaAst, FormulaAstDraft, FormulaCache, FormulaCachePolicy, FormulaCell,
    FormulaCellDraft, FormulaDecimal, FormulaError, FormulaGridDimensions, FormulaGridEdit,
    FormulaLimitConfig, FormulaLimits, FormulaNumberFormat, FormulaValue,
    TABLE_FORMULA_SCHEMA_VERSION,
};

type TestResult = Result<(), Box<dyn std::error::Error>>;

fn limits() -> Result<FormulaLimits, FormulaError> {
    FormulaLimits::new(FormulaLimitConfig {
        rows: 100,
        columns: 100,
        ..FormulaLimitConfig::default()
    })
}

fn ast(source: &str) -> Result<FormulaAst, FormulaError> {
    FormulaAst::parse(source, limits()?)
}

fn draft(value: &FormulaAst) -> FormulaAstDraft {
    FormulaAstDraft {
        schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
        expression: value.expression().clone(),
    }
}

fn cell(
    source: &str,
    owner: CellCoordinate,
    cache: FormulaCache,
) -> Result<FormulaCell, FormulaError> {
    FormulaCell::from_draft(
        FormulaCellDraft {
            schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
            owner,
            ast: draft(&ast(source)?),
            cache,
            number_format: FormulaNumberFormat::Number {
                decimal_places: 2,
                use_grouping: true,
            },
        },
        dimensions(100, 100),
        limits()?,
    )
}

fn dimensions(rows: u32, columns: u32) -> FormulaGridDimensions {
    FormulaGridDimensions { rows, columns }
}

fn decimal_cache() -> FormulaCache {
    FormulaCache::Unverified {
        value: FormulaValue::Decimal {
            value: FormulaDecimal::new(30, 0),
        },
    }
}

#[test]
fn parser_normalizes_arithmetic_functions_ranges_and_anchors() -> TestResult {
    let parsed = ast(" = sum(B3:E3, $A$1) + PRODUCT(A1, 2.500) ")?;
    assert_eq!(
        parsed.canonical_formula(limits()?)?,
        "(SUM(B3:E3,$A$1)+PRODUCT(A1,2.5))"
    );
    let canonical = parsed.canonical_formula(limits()?)?;
    let reparsed = FormulaAst::parse(&canonical, limits()?)?;
    assert_eq!(parsed, reparsed);
    assert_eq!(
        parsed.canonical_sha256(limits()?)?,
        reparsed.canonical_sha256(limits()?)?
    );
    Ok(())
}

#[test]
fn parser_rejects_unknown_locale_and_malformed_syntax() -> TestResult {
    for invalid in [
        "",
        "SUM()",
        "SUM(A1,)",
        "MIN(A1)",
        "A0",
        "A1:B0",
        "B2:A1",
        "SUM(A1;B1)",
        "합계(A1)",
        "1.",
        "A1 trailing",
    ] {
        assert!(FormulaAst::parse(invalid, limits()?).is_err(), "{invalid}");
    }
    Ok(())
}

#[test]
fn typed_json_is_versioned_bounded_and_fail_closed() -> TestResult {
    let parsed = ast("AVG(A1:A3)")?;
    let canonical = parsed.canonical_json(limits()?)?;
    assert_eq!(FormulaAst::from_json(&canonical, limits()?)?, parsed);

    let wrong_version =
        String::from_utf8(canonical.clone())?.replace(TABLE_FORMULA_SCHEMA_VERSION, "wrong");
    assert_eq!(
        FormulaAst::from_json(wrong_version.as_bytes(), limits()?),
        Err(FormulaError::UnsupportedVersion)
    );

    let unknown = String::from_utf8(canonical)?.replacen('{', "{\"unknown\":true,", 1);
    assert_eq!(
        FormulaAst::from_json(unknown.as_bytes(), limits()?),
        Err(FormulaError::InvalidJson)
    );

    let tiny = FormulaLimits::new(FormulaLimitConfig {
        serialized_bytes: 8,
        ..FormulaLimitConfig::default()
    })?;
    assert_eq!(
        FormulaAst::from_json(b"{\"x\":true}", tiny),
        Err(FormulaError::InputLimitOrEncoding)
    );
    Ok(())
}

#[test]
fn formula_cell_json_roundtrips_only_inside_exact_grid() -> TestResult {
    let original = cell(
        "SUM(A1:B1)",
        CellCoordinate { row: 0, column: 2 },
        decimal_cache(),
    )?;
    let canonical = original.canonical_json(limits()?)?;
    assert_eq!(
        FormulaCell::from_json(&canonical, dimensions(10, 10), limits()?)?,
        original
    );
    let unknown = String::from_utf8(canonical.clone())?.replacen('{', "{\"unknown\":true,", 1);
    assert_eq!(
        FormulaCell::from_json(unknown.as_bytes(), dimensions(10, 10), limits()?),
        Err(FormulaError::InvalidJson)
    );
    assert_eq!(
        FormulaCell::from_json(&canonical, dimensions(1, 2), limits()?),
        Err(FormulaError::ReferenceOutOfBounds)
    );
    let reference_outside = cell(
        "D1",
        CellCoordinate { row: 0, column: 2 },
        FormulaCache::Absent,
    )?;
    assert_eq!(
        FormulaCell::from_json(
            &reference_outside.canonical_json(limits()?)?,
            dimensions(1, 3),
            limits()?,
        ),
        Err(FormulaError::ReferenceOutOfBounds)
    );
    assert_eq!(
        FormulaCell::from_json(&canonical, dimensions(0, 10), limits()?),
        Err(FormulaError::InvalidGridDimensions)
    );
    Ok(())
}

#[test]
fn rebase_moves_only_relative_reference_axes() -> TestResult {
    let parsed = ast("SUM(A1,$B1,C$2,$D$4)")?;
    let rebased = parsed.rebase(
        CellCoordinate { row: 1, column: 1 },
        CellCoordinate { row: 3, column: 2 },
        dimensions(10, 10),
        limits()?,
    )?;
    assert_eq!(
        rebased.canonical_formula(limits()?)?,
        "SUM(B3,$B3,D$2,$D$4)"
    );

    assert_eq!(
        ast("A1")?.rebase(
            CellCoordinate { row: 1, column: 1 },
            CellCoordinate { row: 0, column: 0 },
            dimensions(10, 10),
            limits()?,
        ),
        Err(FormulaError::RebaseOutOfBounds)
    );
    assert_eq!(
        ast("Z1")?.rebase(
            CellCoordinate { row: 0, column: 0 },
            CellCoordinate { row: 1, column: 0 },
            dimensions(10, 10),
            limits()?,
        ),
        Err(FormulaError::ReferenceOutOfBounds)
    );
    assert_eq!(
        ast("A1")?.rebase(
            CellCoordinate { row: 0, column: 0 },
            CellCoordinate { row: 1, column: 0 },
            dimensions(0, 10),
            limits()?,
        ),
        Err(FormulaError::InvalidGridDimensions)
    );
    Ok(())
}

#[test]
fn structural_edits_update_absolute_and_relative_references() -> TestResult {
    let parsed = ast("SUM(A1:C3,$B$2)")?;
    let rows = parsed.apply_grid_edit(
        FormulaGridEdit::InsertRows {
            before: dimensions(5, 5),
            index: 1,
            count: 2,
        },
        limits()?,
    )?;
    assert_eq!(rows.canonical_formula(limits()?)?, "SUM(A1:C5,$B$4)");
    let columns = parsed.apply_grid_edit(
        FormulaGridEdit::InsertColumns {
            before: dimensions(5, 5),
            index: 1,
            count: 1,
        },
        limits()?,
    )?;
    assert_eq!(columns.canonical_formula(limits()?)?, "SUM(A1:D3,$C$2)");
    let contracted = ast("SUM(A1:A5)")?.apply_grid_edit(
        FormulaGridEdit::DeleteRows {
            before: dimensions(5, 5),
            index: 1,
            count: 2,
        },
        limits()?,
    )?;
    assert_eq!(contracted.canonical_formula(limits()?)?, "SUM(A1:A3)");
    assert_eq!(
        ast("A2")?.apply_grid_edit(
            FormulaGridEdit::DeleteRows {
                before: dimensions(5, 5),
                index: 1,
                count: 1,
            },
            limits()?,
        ),
        Err(FormulaError::ReferenceDeleted)
    );
    Ok(())
}

#[test]
fn cache_policy_is_explicit_and_formula_bound() -> TestResult {
    let original = cell(
        "SUM(A1:B1)",
        CellCoordinate { row: 0, column: 2 },
        FormulaCache::Unverified {
            value: FormulaValue::Decimal {
                value: FormulaDecimal::new(30, 0),
            },
        },
    )?;
    assert_eq!(
        original.apply_grid_edit(
            FormulaGridEdit::InsertRows {
                before: dimensions(20, 20),
                index: 10,
                count: 1,
            },
            FormulaCachePolicy::Preserve,
            None,
            limits()?,
        )?,
        original
    );
    assert_eq!(
        original.apply_grid_edit(
            FormulaGridEdit::InsertColumns {
                before: dimensions(20, 20),
                index: 0,
                count: 1,
            },
            FormulaCachePolicy::Preserve,
            None,
            limits()?,
        ),
        Err(FormulaError::CachePreservationConflict)
    );
    let cleared = original.apply_grid_edit(
        FormulaGridEdit::InsertColumns {
            before: dimensions(20, 20),
            index: 0,
            count: 1,
        },
        FormulaCachePolicy::Clear,
        None,
        limits()?,
    )?;
    assert!(matches!(cleared.cache(), FormulaCache::Absent));

    let updated = cleared.apply_grid_edit(
        FormulaGridEdit::InsertRows {
            before: dimensions(20, 21),
            index: 10,
            count: 1,
        },
        FormulaCachePolicy::Update,
        Some(decimal_cache()),
        limits()?,
    )?;
    assert!(matches!(updated.cache(), FormulaCache::Unverified { .. }));
    Ok(())
}

#[test]
fn cache_policy_shape_mismatches_fail_closed() -> TestResult {
    let original = cell(
        "SUM(A1:B1)",
        CellCoordinate { row: 0, column: 2 },
        decimal_cache(),
    )?;
    let edit = FormulaGridEdit::InsertRows {
        before: dimensions(20, 20),
        index: 10,
        count: 1,
    };
    for (policy, replacement) in [
        (FormulaCachePolicy::Preserve, Some(decimal_cache())),
        (FormulaCachePolicy::Clear, Some(decimal_cache())),
        (FormulaCachePolicy::Update, None),
        (FormulaCachePolicy::Update, Some(FormulaCache::Absent)),
    ] {
        assert_eq!(
            original.apply_grid_edit(edit, policy, replacement, limits()?),
            Err(FormulaError::CachePolicyMismatch)
        );
    }
    Ok(())
}

#[test]
fn formula_cell_rebase_binds_cache_to_formula_digest() -> TestResult {
    let absolute = cell(
        "$A$1",
        CellCoordinate { row: 1, column: 1 },
        decimal_cache(),
    )?;
    let absolute_copy = absolute.rebase(
        CellCoordinate { row: 2, column: 2 },
        dimensions(20, 20),
        FormulaCachePolicy::Preserve,
        None,
        limits()?,
    )?;
    assert_eq!(absolute_copy.ast().canonical_formula(limits()?)?, "$A$1");
    assert!(matches!(
        absolute_copy.cache(),
        FormulaCache::Unverified { .. }
    ));

    let relative = cell(
        "SUM(A1:B1)",
        CellCoordinate { row: 0, column: 2 },
        decimal_cache(),
    )?;
    assert_eq!(
        relative.rebase(
            CellCoordinate { row: 1, column: 3 },
            dimensions(20, 20),
            FormulaCachePolicy::Preserve,
            None,
            limits()?,
        ),
        Err(FormulaError::CachePreservationConflict)
    );
    Ok(())
}

#[test]
fn owner_deletion_and_exact_grid_escape_fail_atomically() -> TestResult {
    let owned = cell(
        "A1",
        CellCoordinate { row: 1, column: 0 },
        FormulaCache::Absent,
    )?;
    let before = owned.canonical_sha256(limits()?)?;
    assert_eq!(
        owned.apply_grid_edit(
            FormulaGridEdit::DeleteRows {
                before: dimensions(3, 3),
                index: 1,
                count: 1,
            },
            FormulaCachePolicy::Clear,
            None,
            limits()?,
        ),
        Err(FormulaError::OwnerDeleted)
    );
    assert_eq!(owned.canonical_sha256(limits()?)?, before);
    assert_eq!(
        ast("F1")?.apply_grid_edit(
            FormulaGridEdit::InsertRows {
                before: dimensions(5, 5),
                index: 5,
                count: 1,
            },
            limits()?,
        ),
        Err(FormulaError::ReferenceOutOfBounds)
    );
    Ok(())
}

#[test]
fn cache_and_number_format_tamper_fail_closed() -> TestResult {
    let parsed = ast("SUM(A1:A2)")?;
    let invalid_cache = FormulaCellDraft {
        schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
        owner: CellCoordinate { row: 2, column: 0 },
        ast: draft(&parsed),
        cache: FormulaCache::Unverified {
            value: FormulaValue::Text {
                value: "e\u{301}".to_owned(),
            },
        },
        number_format: FormulaNumberFormat::General,
    };
    assert_eq!(
        FormulaCell::from_draft(invalid_cache, dimensions(10, 10), limits()?),
        Err(FormulaError::InvalidCache)
    );

    let invalid_format = FormulaCellDraft {
        schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
        owner: CellCoordinate { row: 2, column: 0 },
        ast: draft(&parsed),
        cache: FormulaCache::Absent,
        number_format: FormulaNumberFormat::Percent { decimal_places: 13 },
    };
    assert_eq!(
        FormulaCell::from_draft(invalid_format, dimensions(10, 10), limits()?),
        Err(FormulaError::InvalidNumberFormat)
    );
    Ok(())
}

#[test]
fn reversed_range_and_noncanonical_decimal_drafts_are_rejected() -> TestResult {
    let reversed = br#"{"schema_version":"hwpx-agent.table-formula/v1","expression":{"kind":"range","range":{"start":{"row":2,"column":2,"row_kind":"relative","column_kind":"relative"},"end":{"row":1,"column":1,"row_kind":"relative","column_kind":"relative"}}}}"#;
    assert_eq!(
        FormulaAst::from_json(reversed, limits()?),
        Err(FormulaError::InvalidRange)
    );
    let noncanonical = br#"{"schema_version":"hwpx-agent.table-formula/v1","expression":{"kind":"decimal","value":{"coefficient":120,"scale":2}}}"#;
    assert_eq!(
        FormulaAst::from_json(noncanonical, limits()?),
        Err(FormulaError::InvalidDecimal)
    );
    Ok(())
}

#[test]
fn deterministic_256_case_reference_move_corpus() -> TestResult {
    for seed in 0_u32..256 {
        let row = seed % 40 + 1;
        let column = seed % 20;
        let column_name = column_name(column)?;
        let source = format!(
            "SUM({column_name}{row}:${column_name}${row},{}.50)",
            seed + 1
        );
        let first = FormulaAst::parse(&source, limits()?)?;
        let inserted = first.apply_grid_edit(
            FormulaGridEdit::InsertRows {
                before: dimensions(50, 50),
                index: 0,
                count: 1,
            },
            limits()?,
        )?;
        let removed = inserted.apply_grid_edit(
            FormulaGridEdit::DeleteRows {
                before: dimensions(51, 50),
                index: 0,
                count: 1,
            },
            limits()?,
        )?;
        assert_eq!(first, removed, "seed {seed}");
        assert_eq!(
            first.canonical_sha256(limits()?)?,
            removed.canonical_sha256(limits()?)?,
            "seed {seed}"
        );
    }
    Ok(())
}

#[test]
fn public_errors_and_debug_redaction_are_stable() -> TestResult {
    let errors = [
        (FormulaError::InvalidLimit, "table_formula_invalid_limit"),
        (
            FormulaError::UnsupportedVersion,
            "table_formula_unsupported_version",
        ),
        (FormulaError::InvalidSyntax, "table_formula_invalid_syntax"),
        (
            FormulaError::InvalidGridDimensions,
            "table_formula_invalid_grid_dimensions",
        ),
        (
            FormulaError::ReferenceDeleted,
            "table_formula_reference_deleted",
        ),
        (FormulaError::OwnerDeleted, "table_formula_owner_deleted"),
        (
            FormulaError::CachePreservationConflict,
            "table_formula_cache_preservation_conflict",
        ),
        (FormulaError::InvalidCache, "table_formula_invalid_cache"),
        (FormulaError::OutputLimit, "table_formula_output_limit"),
    ];
    for (error, expected) in errors {
        assert_eq!(error.code(), expected);
    }
    let private_literal = "123456789";
    let parsed = ast(private_literal)?;
    assert!(!format!("{parsed:?}").contains(private_literal));
    assert!(!format!("{:?}", parsed.expression()).contains(private_literal));
    let value = FormulaValue::Text {
        value: "private-cell-value".to_owned(),
    };
    assert!(!format!("{value:?}").contains("private-cell-value"));
    Ok(())
}

#[test]
fn invalid_limits_and_grid_edits_are_rejected() -> TestResult {
    assert_eq!(
        FormulaLimits::new(FormulaLimitConfig {
            nodes: 0,
            ..FormulaLimitConfig::default()
        }),
        Err(FormulaError::InvalidLimit)
    );
    for edit in [
        FormulaGridEdit::InsertRows {
            before: dimensions(5, 5),
            index: 0,
            count: 0,
        },
        FormulaGridEdit::DeleteRows {
            before: dimensions(5, 5),
            index: 100,
            count: 1,
        },
        FormulaGridEdit::DeleteColumns {
            before: dimensions(5, 5),
            index: 99,
            count: 2,
        },
        FormulaGridEdit::InsertRows {
            before: dimensions(100, 5),
            index: 100,
            count: 1,
        },
    ] {
        assert_eq!(
            ast("A1")?.apply_grid_edit(edit, limits()?),
            Err(FormulaError::InvalidGridEdit)
        );
    }
    Ok(())
}

fn column_name(column: u32) -> Result<String, std::num::TryFromIntError> {
    let mut value = column + 1;
    let mut reversed = Vec::new();
    while value > 0 {
        reversed.push(char::from(b'A' + u8::try_from((value - 1) % 26)?));
        value = (value - 1) / 26;
    }
    Ok(reversed.iter().rev().collect())
}
