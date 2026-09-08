use domain_ir::{
    CellCoordinate, LogicalId, TABLE_GRID_SCHEMA_VERSION, TABLE_STYLE_DEFINITION_SCHEMA_VERSION,
    TABLE_STYLE_SCHEMA_VERSION, TableCellSpan, TableGrid, TableGridDraft, TableGridLimits,
    TableStyleBandPrecedence, TableStyleBanding, TableStyleBuilder, TableStyleCellDraft,
    TableStyleColumnEmphasis, TableStyleDefinition, TableStyleDefinitionDraft, TableStyleError,
    TableStyleLimitConfig, TableStyleLimits, TableStyleMergedCellPolicy, TableStyleRegion,
    TableStyleRequest, TableStyleRequestDraft, TableStyleRule,
};

type TestResult = Result<(), Box<dyn std::error::Error>>;

fn id(value: &str) -> Result<LogicalId, Box<dyn std::error::Error>> {
    Ok(LogicalId::parse(value)?)
}

fn digest(character: char) -> String {
    std::iter::repeat_n(character, 64).collect()
}

fn unmerged_grid(rows: u32, columns: u32) -> Result<TableGrid, Box<dyn std::error::Error>> {
    let mut master_cells = Vec::new();
    for row in 0..rows {
        for column in 0..columns {
            master_cells.push(TableCellSpan {
                master_cell_id: id(&format!("cell-{row}-{column}"))?,
                row,
                column,
                row_span: 1,
                column_span: 1,
            });
        }
    }
    Ok(TableGrid::from_draft(
        TableGridDraft {
            schema_version: TABLE_GRID_SCHEMA_VERSION.to_owned(),
            rows,
            columns,
            master_cells,
        },
        TableGridLimits::default(),
    )?)
}

fn definition(
    rules: Vec<(TableStyleRegion, char)>,
) -> Result<TableStyleDefinition, Box<dyn std::error::Error>> {
    Ok(TableStyleDefinition::from_draft(
        TableStyleDefinitionDraft {
            schema_version: TABLE_STYLE_DEFINITION_SCHEMA_VERSION.to_owned(),
            style_id: id("style-blue")?,
            table_properties_sha256: digest('f'),
            rules: rules
                .into_iter()
                .map(|(region, character)| TableStyleRule {
                    region,
                    cell_style_sha256: digest(character),
                })
                .collect(),
        },
        TableStyleLimits::default(),
    )?)
}

fn all_rules() -> Vec<(TableStyleRegion, char)> {
    vec![
        (TableStyleRegion::WholeTable, '0'),
        (TableStyleRegion::HeaderRows, '1'),
        (TableStyleRegion::FooterRows, '2'),
        (TableStyleRegion::FirstColumn, '3'),
        (TableStyleRegion::LastColumn, '4'),
        (TableStyleRegion::OddRowBand, '5'),
        (TableStyleRegion::EvenRowBand, '6'),
        (TableStyleRegion::OddColumnBand, '7'),
        (TableStyleRegion::EvenColumnBand, '8'),
        (TableStyleRegion::TopLeftCell, '9'),
        (TableStyleRegion::TopRightCell, 'a'),
        (TableStyleRegion::BottomLeftCell, 'b'),
        (TableStyleRegion::BottomRightCell, 'c'),
    ]
}

fn request_draft(
    grid: &TableGrid,
    definition: &TableStyleDefinition,
) -> Result<TableStyleRequestDraft, Box<dyn std::error::Error>> {
    let style_definition_sha256 = hex(definition.canonical_sha256(TableStyleLimits::default())?);
    Ok(TableStyleRequestDraft {
        schema_version: TABLE_STYLE_SCHEMA_VERSION.to_owned(),
        table_id: id("table-main")?,
        style_id: definition.style_id().clone(),
        style_definition_sha256,
        current_table_properties_sha256: digest('d'),
        header_rows: 1,
        footer_rows: 1,
        column_emphasis: TableStyleColumnEmphasis::FirstAndLast,
        banding: TableStyleBanding::RowsAndColumns,
        row_band_size: 1,
        column_band_size: 1,
        band_precedence: TableStyleBandPrecedence::RowsFirst,
        merged_cell_policy: TableStyleMergedCellPolicy::RejectMixedResolvedStyle,
        cells: grid
            .master_cells()
            .iter()
            .enumerate()
            .map(|(index, span)| TableStyleCellDraft {
                master_cell_id: span.master_cell_id.clone(),
                coordinate: CellCoordinate {
                    row: span.row,
                    column: span.column,
                },
                payload_sha256: digest('e'),
                formula_sha256: (index == 1).then(|| digest('a')),
                current_style_sha256: digest('d'),
            })
            .collect(),
    })
}

fn request(
    grid: &TableGrid,
    definition: &TableStyleDefinition,
) -> Result<TableStyleRequest, Box<dyn std::error::Error>> {
    Ok(TableStyleRequest::from_draft(
        request_draft(grid, definition)?,
        definition,
        grid,
        TableStyleLimits::default(),
    )?)
}

fn mutation_region(
    plan: &domain_ir::TableStylePlan,
    row: u32,
    column: u32,
) -> Result<TableStyleRegion, Box<dyn std::error::Error>> {
    plan.mutations()
        .iter()
        .find(|mutation| mutation.coordinate == CellCoordinate { row, column })
        .map(|mutation| mutation.resolved_region)
        .ok_or_else(|| std::io::Error::other("coordinate missing").into())
}

#[test]
fn definition_is_rule_order_independent_and_digest_bound() -> TestResult {
    let mut reversed = all_rules();
    reversed.reverse();
    let left = definition(all_rules())?;
    let right = definition(reversed)?;
    assert_eq!(
        left.canonical_json(TableStyleLimits::default())?,
        right.canonical_json(TableStyleLimits::default())?
    );
    assert_eq!(left.rules().len(), 13);
    assert_eq!(left.table_properties_sha256(), digest('f'));
    Ok(())
}

#[test]
fn fixed_precedence_resolves_corners_headers_footers_columns_and_bands() -> TestResult {
    let grid = unmerged_grid(5, 5)?;
    let definition = definition(all_rules())?;
    let request = request(&grid, &definition)?;
    let plan = TableStyleBuilder::build(&request, &definition, &grid, TableStyleLimits::default())?;

    assert_eq!(mutation_region(&plan, 0, 0)?, TableStyleRegion::TopLeftCell);
    assert_eq!(
        mutation_region(&plan, 0, 4)?,
        TableStyleRegion::TopRightCell
    );
    assert_eq!(
        mutation_region(&plan, 4, 0)?,
        TableStyleRegion::BottomLeftCell
    );
    assert_eq!(
        mutation_region(&plan, 4, 4)?,
        TableStyleRegion::BottomRightCell
    );
    assert_eq!(mutation_region(&plan, 0, 2)?, TableStyleRegion::HeaderRows);
    assert_eq!(mutation_region(&plan, 4, 2)?, TableStyleRegion::FooterRows);
    assert_eq!(mutation_region(&plan, 2, 0)?, TableStyleRegion::FirstColumn);
    assert_eq!(mutation_region(&plan, 2, 4)?, TableStyleRegion::LastColumn);
    assert_eq!(mutation_region(&plan, 1, 2)?, TableStyleRegion::OddRowBand);
    assert_eq!(mutation_region(&plan, 2, 2)?, TableStyleRegion::EvenRowBand);
    assert_eq!(plan.receipt().master_cell_count, 25);
    assert_eq!(plan.receipt().payload_preserved_count, 25);
    assert_eq!(plan.receipt().formula_preserved_count, 1);
    Ok(())
}

#[test]
fn row_or_column_band_precedence_is_explicit() -> TestResult {
    let grid = unmerged_grid(3, 3)?;
    let definition = definition(vec![
        (TableStyleRegion::WholeTable, '0'),
        (TableStyleRegion::OddRowBand, '1'),
        (TableStyleRegion::EvenRowBand, '2'),
        (TableStyleRegion::OddColumnBand, '3'),
        (TableStyleRegion::EvenColumnBand, '4'),
    ])?;
    let mut draft = request_draft(&grid, &definition)?;
    draft.header_rows = 0;
    draft.footer_rows = 0;
    draft.column_emphasis = TableStyleColumnEmphasis::None;
    let rows_first = TableStyleRequest::from_draft(
        draft.clone(),
        &definition,
        &grid,
        TableStyleLimits::default(),
    )?;
    let rows_plan =
        TableStyleBuilder::build(&rows_first, &definition, &grid, TableStyleLimits::default())?;
    assert_eq!(
        mutation_region(&rows_plan, 1, 2)?,
        TableStyleRegion::EvenRowBand
    );

    draft.band_precedence = TableStyleBandPrecedence::ColumnsFirst;
    let columns_first =
        TableStyleRequest::from_draft(draft, &definition, &grid, TableStyleLimits::default())?;
    let columns_plan = TableStyleBuilder::build(
        &columns_first,
        &definition,
        &grid,
        TableStyleLimits::default(),
    )?;
    assert_eq!(
        mutation_region(&columns_plan, 1, 2)?,
        TableStyleRegion::OddColumnBand
    );
    Ok(())
}

#[test]
fn inactive_header_footer_and_column_flags_disable_corner_rules() -> TestResult {
    let grid = unmerged_grid(2, 2)?;
    let definition = definition(vec![
        (TableStyleRegion::WholeTable, '0'),
        (TableStyleRegion::TopLeftCell, '1'),
        (TableStyleRegion::BottomRightCell, '2'),
    ])?;
    let mut draft = request_draft(&grid, &definition)?;
    draft.header_rows = 0;
    draft.footer_rows = 0;
    draft.column_emphasis = TableStyleColumnEmphasis::None;
    draft.banding = TableStyleBanding::None;
    let request =
        TableStyleRequest::from_draft(draft, &definition, &grid, TableStyleLimits::default())?;
    let plan = TableStyleBuilder::build(&request, &definition, &grid, TableStyleLimits::default())?;
    assert!(
        plan.mutations()
            .iter()
            .all(|mutation| mutation.resolved_region == TableStyleRegion::WholeTable)
    );
    Ok(())
}

#[test]
fn merged_cells_reject_mixed_regions_or_use_the_explicit_anchor() -> TestResult {
    let grid = TableGrid::new(
        2,
        2,
        vec![
            TableCellSpan {
                master_cell_id: id("merged")?,
                row: 0,
                column: 0,
                row_span: 2,
                column_span: 1,
            },
            TableCellSpan {
                master_cell_id: id("right-top")?,
                row: 0,
                column: 1,
                row_span: 1,
                column_span: 1,
            },
            TableCellSpan {
                master_cell_id: id("right-bottom")?,
                row: 1,
                column: 1,
                row_span: 1,
                column_span: 1,
            },
        ],
        TableGridLimits::default(),
    )?;
    let definition = definition(vec![
        (TableStyleRegion::WholeTable, '0'),
        (TableStyleRegion::HeaderRows, '1'),
    ])?;
    let mut draft = request_draft(&grid, &definition)?;
    draft.footer_rows = 0;
    draft.column_emphasis = TableStyleColumnEmphasis::None;
    draft.banding = TableStyleBanding::None;
    let rejecting = TableStyleRequest::from_draft(
        draft.clone(),
        &definition,
        &grid,
        TableStyleLimits::default(),
    )?;
    assert_eq!(
        TableStyleBuilder::build(&rejecting, &definition, &grid, TableStyleLimits::default()),
        Err(TableStyleError::MergedRegionConflict)
    );

    draft.merged_cell_policy = TableStyleMergedCellPolicy::UseMasterAnchor;
    let anchored =
        TableStyleRequest::from_draft(draft, &definition, &grid, TableStyleLimits::default())?;
    let plan =
        TableStyleBuilder::build(&anchored, &definition, &grid, TableStyleLimits::default())?;
    assert_eq!(plan.receipt().merged_cell_count, 1);
    assert_eq!(mutation_region(&plan, 0, 0)?, TableStyleRegion::HeaderRows);
    Ok(())
}

#[test]
fn missing_duplicate_and_invalid_style_rules_fail_closed() -> TestResult {
    let base = TableStyleDefinitionDraft {
        schema_version: TABLE_STYLE_DEFINITION_SCHEMA_VERSION.to_owned(),
        style_id: id("style")?,
        table_properties_sha256: digest('a'),
        rules: vec![TableStyleRule {
            region: TableStyleRegion::HeaderRows,
            cell_style_sha256: digest('b'),
        }],
    };
    assert_eq!(
        TableStyleDefinition::from_draft(base.clone(), TableStyleLimits::default()),
        Err(TableStyleError::MissingWholeTableRule)
    );
    let mut duplicate = base.clone();
    duplicate.rules = vec![
        TableStyleRule {
            region: TableStyleRegion::WholeTable,
            cell_style_sha256: digest('a'),
        },
        TableStyleRule {
            region: TableStyleRegion::WholeTable,
            cell_style_sha256: digest('b'),
        },
    ];
    assert_eq!(
        TableStyleDefinition::from_draft(duplicate, TableStyleLimits::default()),
        Err(TableStyleError::DuplicateRule)
    );
    let mut invalid = base;
    invalid.rules[0].region = TableStyleRegion::WholeTable;
    invalid.rules[0].cell_style_sha256 = "not-a-digest".to_owned();
    assert_eq!(
        TableStyleDefinition::from_draft(invalid, TableStyleLimits::default()),
        Err(TableStyleError::DigestInvalid)
    );
    Ok(())
}

#[test]
fn definition_binding_and_region_constraints_fail_before_planning() -> TestResult {
    let grid = unmerged_grid(2, 2)?;
    let definition = definition(all_rules())?;
    let mut draft = request_draft(&grid, &definition)?;
    draft.style_definition_sha256 = digest('9');
    assert_eq!(
        TableStyleRequest::from_draft(draft, &definition, &grid, TableStyleLimits::default()),
        Err(TableStyleError::DefinitionBindingMismatch)
    );
    let mut draft = request_draft(&grid, &definition)?;
    draft.header_rows = 2;
    draft.footer_rows = 1;
    assert_eq!(
        TableStyleRequest::from_draft(draft, &definition, &grid, TableStyleLimits::default()),
        Err(TableStyleError::RegionInvalid)
    );
    Ok(())
}

#[test]
fn incomplete_duplicate_and_digest_drift_cell_sets_fail_closed() -> TestResult {
    let grid = unmerged_grid(2, 2)?;
    let definition = definition(all_rules())?;
    let mut draft = request_draft(&grid, &definition)?;
    draft.cells.pop();
    assert_eq!(
        TableStyleRequest::from_draft(draft, &definition, &grid, TableStyleLimits::default()),
        Err(TableStyleError::CellSetMismatch)
    );
    let mut draft = request_draft(&grid, &definition)?;
    draft.cells[1] = draft.cells[0].clone();
    assert_eq!(
        TableStyleRequest::from_draft(draft, &definition, &grid, TableStyleLimits::default()),
        Err(TableStyleError::CellSetMismatch)
    );
    let mut draft = request_draft(&grid, &definition)?;
    draft.cells[0].payload_sha256 = "ABC".to_owned();
    assert_eq!(
        TableStyleRequest::from_draft(draft, &definition, &grid, TableStyleLimits::default()),
        Err(TableStyleError::DigestInvalid)
    );
    Ok(())
}

#[test]
fn strict_json_rejects_duplicate_unknown_version_and_size() -> TestResult {
    let definition = definition(all_rules())?;
    let definition_json = definition.canonical_json(TableStyleLimits::default())?;
    assert!(TableStyleDefinition::from_json(&definition_json, TableStyleLimits::default()).is_ok());
    let duplicate = String::from_utf8(definition_json.clone())?.replacen(
        '{',
        "{\"schema_version\":\"duplicate\",",
        1,
    );
    assert_eq!(
        TableStyleDefinition::from_json(duplicate.as_bytes(), TableStyleLimits::default()),
        Err(TableStyleError::InvalidJson)
    );
    let unknown =
        String::from_utf8(definition_json.clone())?.replacen('{', "{\"unknown\":true,", 1);
    assert_eq!(
        TableStyleDefinition::from_json(unknown.as_bytes(), TableStyleLimits::default()),
        Err(TableStyleError::InvalidJson)
    );
    let wrong = String::from_utf8(definition_json)?.replace(
        TABLE_STYLE_DEFINITION_SCHEMA_VERSION,
        "table-style-definition/wrong",
    );
    assert_eq!(
        TableStyleDefinition::from_json(wrong.as_bytes(), TableStyleLimits::default()),
        Err(TableStyleError::UnsupportedDefinitionVersion)
    );
    assert_eq!(
        TableStyleDefinition::from_json(&[], TableStyleLimits::default()),
        Err(TableStyleError::InputLimit)
    );
    Ok(())
}

#[test]
fn canonical_request_plan_and_receipt_are_repeatable() -> TestResult {
    let grid = unmerged_grid(4, 4)?;
    let definition = definition(all_rules())?;
    let request = request(&grid, &definition)?;
    let first =
        TableStyleBuilder::build(&request, &definition, &grid, TableStyleLimits::default())?;
    let second =
        TableStyleBuilder::build(&request, &definition, &grid, TableStyleLimits::default())?;
    assert_eq!(
        request.canonical_sha256(TableStyleLimits::default())?,
        request.canonical_sha256(TableStyleLimits::default())?
    );
    assert_eq!(
        first.canonical_json(TableStyleLimits::default())?,
        second.canonical_json(TableStyleLimits::default())?
    );
    assert_eq!(first.receipt(), second.receipt());
    assert_eq!(first.table_properties_sha256(), digest('f'));
    Ok(())
}

#[test]
fn finite_limits_and_output_bound_return_no_partial_plan() -> TestResult {
    assert_eq!(
        TableStyleLimits::new(TableStyleLimitConfig {
            style_rules: 0,
            ..TableStyleLimitConfig::default()
        }),
        Err(TableStyleError::InvalidLimit)
    );
    let grid = unmerged_grid(2, 2)?;
    let definition = definition(all_rules())?;
    let request = request(&grid, &definition)?;
    let tight = TableStyleLimits::new(TableStyleLimitConfig {
        serialized_bytes: 256,
        input_bytes: 128,
        ..TableStyleLimitConfig::default()
    })?;
    assert_eq!(
        TableStyleBuilder::build(&request, &definition, &grid, tight),
        Err(TableStyleError::OutputLimit)
    );
    Ok(())
}

#[test]
fn debug_surfaces_redact_ids_and_all_content_digests() -> TestResult {
    let grid = unmerged_grid(2, 2)?;
    let definition = definition(all_rules())?;
    let draft = request_draft(&grid, &definition)?;
    let draft_debug = format!("{draft:?}");
    assert!(!draft_debug.contains("table-main"));
    assert!(!draft_debug.contains(&digest('d')));
    let request = request(&grid, &definition)?;
    let plan = TableStyleBuilder::build(&request, &definition, &grid, TableStyleLimits::default())?;
    let debug = format!(
        "{request:?}{plan:?}{:?}{:?}{:?}",
        plan.mutations()[0],
        plan.receipt(),
        definition.rules()[0]
    );
    for secret in ["table-main", "style-blue", &digest('d'), &digest('e')] {
        assert!(!debug.contains(secret));
    }
    Ok(())
}

#[test]
fn fixed_seed_shape_corpus_resolves_every_master_exactly_once() -> TestResult {
    let definition = definition(all_rules())?;
    for rows in 1..=12 {
        for columns in 1..=12 {
            let grid = unmerged_grid(rows, columns)?;
            let mut draft = request_draft(&grid, &definition)?;
            draft.header_rows = u32::from(rows > 1);
            draft.footer_rows = u32::from(rows > 2);
            draft.row_band_size = ((rows * 17 + columns * 3) % rows) + 1;
            draft.column_band_size = ((columns * 11 + rows * 5) % columns) + 1;
            let request = TableStyleRequest::from_draft(
                draft,
                &definition,
                &grid,
                TableStyleLimits::default(),
            )?;
            let plan = TableStyleBuilder::build(
                &request,
                &definition,
                &grid,
                TableStyleLimits::default(),
            )?;
            assert_eq!(plan.mutations().len(), grid.master_cell_count());
            assert_eq!(
                plan.receipt().payload_preserved_count,
                grid.master_cell_count()
            );
        }
    }
    Ok(())
}

#[test]
fn public_error_codes_are_stable() {
    let cases = [
        (TableStyleError::InvalidLimit, "table_style_invalid_limit"),
        (
            TableStyleError::UnsupportedDefinitionVersion,
            "table_style_unsupported_definition_version",
        ),
        (
            TableStyleError::UnsupportedRequestVersion,
            "table_style_unsupported_request_version",
        ),
        (TableStyleError::InputLimit, "table_style_input_limit"),
        (TableStyleError::InvalidJson, "table_style_invalid_json"),
        (
            TableStyleError::IdentifierLimit,
            "table_style_identifier_limit",
        ),
        (TableStyleError::DigestInvalid, "table_style_digest_invalid"),
        (TableStyleError::RuleLimit, "table_style_rule_limit"),
        (TableStyleError::DuplicateRule, "table_style_duplicate_rule"),
        (
            TableStyleError::MissingWholeTableRule,
            "table_style_missing_whole_table_rule",
        ),
        (
            TableStyleError::DefinitionBindingMismatch,
            "table_style_definition_binding_mismatch",
        ),
        (TableStyleError::RegionInvalid, "table_style_region_invalid"),
        (
            TableStyleError::CellSetMismatch,
            "table_style_cell_set_mismatch",
        ),
        (TableStyleError::GridMismatch, "table_style_grid_mismatch"),
        (TableStyleError::BindingDrift, "table_style_binding_drift"),
        (
            TableStyleError::MergedRegionConflict,
            "table_style_merged_region_conflict",
        ),
        (
            TableStyleError::MasterCellLimit,
            "table_style_master_cell_limit",
        ),
        (TableStyleError::OutputLimit, "table_style_output_limit"),
        (TableStyleError::Serialization, "table_style_serialization"),
        (TableStyleError::AllocationFailed, "table_style_allocation"),
    ];
    for (error, code) in cases {
        assert_eq!(error.code(), code);
    }
}

fn hex(value: [u8; 32]) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(64);
    for byte in value {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}
