use domain_ir::{
    CaptionSide, LengthMicrometers, LogicalId, RowSplitEligibility, TABLE_GRID_SCHEMA_VERSION,
    TABLE_PAGINATION_OBSERVATION_SCHEMA_VERSION, TABLE_PAGINATION_SCHEMA_VERSION, TableCaption,
    TableCellSpan, TableGrid, TableGridDraft, TableGridLimits, TablePage, TablePageItem,
    TablePageSplitPolicy, TablePaginationError, TablePaginationLimitConfig, TablePaginationLimits,
    TablePaginationObservation, TablePaginationPolicy, TablePaginationRow,
    TablePaginationValidator,
};

type TestResult = Result<(), Box<dyn std::error::Error>>;

fn um(value: i64) -> LengthMicrometers {
    LengthMicrometers::from_raw(value)
}

fn span(
    identifier: &str,
    row: u32,
    row_span: u32,
) -> Result<TableCellSpan, Box<dyn std::error::Error>> {
    Ok(TableCellSpan {
        master_cell_id: LogicalId::parse(identifier)?,
        row,
        column: 0,
        row_span,
        column_span: 1,
    })
}

fn grid(rows: u32) -> Result<TableGrid, Box<dyn std::error::Error>> {
    let mut cells = Vec::new();
    for row in 0..rows {
        cells.push(span(&format!("row-{row}"), row, 1)?);
    }
    Ok(TableGrid::from_draft(
        TableGridDraft {
            schema_version: TABLE_GRID_SCHEMA_VERSION.to_owned(),
            rows,
            columns: 1,
            master_cells: cells,
        },
        TableGridLimits::default(),
    )?)
}

fn rows(heights: &[i64]) -> Vec<TablePaginationRow> {
    heights
        .iter()
        .enumerate()
        .map(|(row, height)| TablePaginationRow {
            row: u32::try_from(row).unwrap_or(u32::MAX),
            height: um(*height),
            split_eligibility: RowSplitEligibility::Allowed,
        })
        .collect()
}

fn policy(heights: &[i64]) -> TablePaginationPolicy {
    TablePaginationPolicy {
        schema_version: TABLE_PAGINATION_SCHEMA_VERSION.to_owned(),
        page_split: TablePageSplitPolicy::AvoidRow,
        repeat_header_rows: 1,
        rows: rows(heights),
        caption: None,
    }
}

fn row(row: u32, height: i64) -> TablePageItem {
    TablePageItem::RowFragment {
        row,
        fragment_index: 0,
        height: um(height),
        begins_row: true,
        ends_row: true,
    }
}

fn observation(
    first_height: i64,
    continuation_height: i64,
    pages: Vec<TablePage>,
) -> TablePaginationObservation {
    TablePaginationObservation {
        schema_version: TABLE_PAGINATION_OBSERVATION_SCHEMA_VERSION.to_owned(),
        anchor_page_index: 7,
        first_page_available_height: um(first_height),
        continuation_page_height: um(continuation_height),
        pages,
    }
}

#[test]
fn exact_boundary_and_one_row_after_repeat_header_validate() -> TestResult {
    let grid = grid(4)?;
    let policy = policy(&[1_000, 2_000, 2_000, 2_000]);
    let observed = observation(
        3_000,
        5_000,
        vec![
            TablePage {
                page_index: 7,
                items: vec![row(0, 1_000), row(1, 2_000)],
            },
            TablePage {
                page_index: 8,
                items: vec![
                    TablePageItem::RepeatedHeader { row: 0 },
                    row(2, 2_000),
                    row(3, 2_000),
                ],
            },
        ],
    );
    let receipt = TablePaginationValidator::validate(
        &grid,
        &policy,
        &observed,
        TablePaginationLimits::default(),
    )?;
    assert_eq!(receipt.page_count(), 2);
    assert_eq!(receipt.row_fragment_count(), 4);
    assert_eq!(receipt.split_row_count(), 0);
    assert_eq!(receipt.repeated_header_copy_count(), 1);
    assert_eq!(receipt.first_page_index(), 7);
    assert_eq!(receipt.last_page_index(), 8);
    assert_eq!(receipt.grid_sha256().len(), 64);
    assert_eq!(receipt.policy_sha256().len(), 64);
    assert_eq!(receipt.observation_sha256().len(), 64);
    assert_eq!(
        receipt.canonical_json(TablePaginationLimits::default())?,
        receipt.canonical_json(TablePaginationLimits::default())?
    );
    Ok(())
}

#[test]
fn one_micrometer_before_exact_and_after_boundary_are_distinct() -> TestResult {
    let grid = grid(2)?;
    let policy = policy(&[1_000, 2_000]);
    let page = TablePage {
        page_index: 7,
        items: vec![row(0, 1_000), row(1, 2_000)],
    };
    let before = observation(2_999, 3_000, vec![page.clone()]);
    let exact = observation(3_000, 3_000, vec![page.clone()]);
    let after = observation(3_001, 3_000, vec![page]);
    assert_eq!(
        TablePaginationValidator::validate(
            &grid,
            &policy,
            &before,
            TablePaginationLimits::default(),
        ),
        Err(TablePaginationError::PageOverflow)
    );
    TablePaginationValidator::validate(&grid, &policy, &exact, TablePaginationLimits::default())?;
    TablePaginationValidator::validate(&grid, &policy, &after, TablePaginationLimits::default())?;
    Ok(())
}

#[test]
fn allow_policy_validates_one_row_split_across_exact_boundary() -> TestResult {
    let grid = grid(2)?;
    let mut policy = policy(&[1_000, 6_000]);
    policy.page_split = TablePageSplitPolicy::Allow;
    let observed = observation(
        3_500,
        4_500,
        vec![
            TablePage {
                page_index: 7,
                items: vec![
                    row(0, 1_000),
                    TablePageItem::RowFragment {
                        row: 1,
                        fragment_index: 0,
                        height: um(2_500),
                        begins_row: true,
                        ends_row: false,
                    },
                ],
            },
            TablePage {
                page_index: 8,
                items: vec![
                    TablePageItem::RepeatedHeader { row: 0 },
                    TablePageItem::RowFragment {
                        row: 1,
                        fragment_index: 1,
                        height: um(3_500),
                        begins_row: false,
                        ends_row: true,
                    },
                ],
            },
        ],
    );
    let receipt = TablePaginationValidator::validate(
        &grid,
        &policy,
        &observed,
        TablePaginationLimits::default(),
    )?;
    assert_eq!(receipt.row_fragment_count(), 3);
    assert_eq!(receipt.split_row_count(), 1);
    Ok(())
}

#[test]
fn avoid_row_nested_and_unbreakable_rows_fail_closed() -> TestResult {
    let grid = grid(2)?;
    let mut observed = observation(
        3_500,
        4_500,
        vec![
            TablePage {
                page_index: 7,
                items: vec![
                    row(0, 1_000),
                    TablePageItem::RowFragment {
                        row: 1,
                        fragment_index: 0,
                        height: um(2_500),
                        begins_row: true,
                        ends_row: false,
                    },
                ],
            },
            TablePage {
                page_index: 8,
                items: vec![
                    TablePageItem::RepeatedHeader { row: 0 },
                    TablePageItem::RowFragment {
                        row: 1,
                        fragment_index: 1,
                        height: um(3_500),
                        begins_row: false,
                        ends_row: true,
                    },
                ],
            },
        ],
    );
    let mut avoid_row = policy(&[1_000, 6_000]);
    assert_eq!(
        TablePaginationValidator::validate(
            &grid,
            &avoid_row,
            &observed,
            TablePaginationLimits::default(),
        ),
        Err(TablePaginationError::RowSplitForbidden)
    );

    avoid_row.page_split = TablePageSplitPolicy::Allow;
    avoid_row.rows[1].split_eligibility = RowSplitEligibility::NestedTable;
    assert_eq!(
        TablePaginationValidator::validate(
            &grid,
            &avoid_row,
            &observed,
            TablePaginationLimits::default(),
        ),
        Err(TablePaginationError::NestedTableSplit)
    );

    avoid_row.rows[1].split_eligibility = RowSplitEligibility::UnbreakableObject;
    assert_eq!(
        TablePaginationValidator::validate(
            &grid,
            &avoid_row,
            &observed,
            TablePaginationLimits::default(),
        ),
        Err(TablePaginationError::UnbreakableObjectSplit)
    );

    if let TablePageItem::RowFragment { height, .. } = &mut observed.pages[1].items[1] {
        *height = um(3_499);
    }
    avoid_row.rows[1].split_eligibility = RowSplitEligibility::Allowed;
    assert_eq!(
        TablePaginationValidator::validate(
            &grid,
            &avoid_row,
            &observed,
            TablePaginationLimits::default(),
        ),
        Err(TablePaginationError::RowHeightMismatch)
    );
    Ok(())
}

#[test]
fn avoid_table_and_required_keep_reject_split_or_detached_caption() -> TestResult {
    let grid = grid(2)?;
    let pages = vec![
        TablePage {
            page_index: 7,
            items: vec![row(0, 1_000)],
        },
        TablePage {
            page_index: 8,
            items: vec![TablePageItem::RepeatedHeader { row: 0 }, row(1, 2_000)],
        },
    ];
    let observed = observation(2_000, 4_000, pages);
    let mut policy = policy(&[1_000, 2_000]);
    policy.page_split = TablePageSplitPolicy::AvoidTable;
    assert_eq!(
        TablePaginationValidator::validate(
            &grid,
            &policy,
            &observed,
            TablePaginationLimits::default(),
        ),
        Err(TablePaginationError::TableSplitForbidden)
    );

    policy.page_split = TablePageSplitPolicy::RequiredKeep;
    policy.repeat_header_rows = 0;
    policy.caption = Some(TableCaption {
        side: CaptionSide::Top,
        block_height: um(500),
        gap: um(100),
        keep_with_table: false,
        content_sha256: "a".repeat(64),
    });
    let one_page = observation(
        4_000,
        4_000,
        vec![TablePage {
            page_index: 7,
            items: vec![
                TablePageItem::Caption {
                    side: CaptionSide::Top,
                },
                row(0, 1_000),
                row(1, 2_000),
            ],
        }],
    );
    assert_eq!(
        TablePaginationValidator::validate(
            &grid,
            &policy,
            &one_page,
            TablePaginationLimits::default(),
        ),
        Err(TablePaginationError::RequiredKeepMissing)
    );
    Ok(())
}

#[test]
fn top_and_bottom_caption_position_and_height_are_exact() -> TestResult {
    let grid = grid(2)?;
    let mut policy = policy(&[1_000, 2_000]);
    policy.repeat_header_rows = 0;
    policy.caption = Some(TableCaption {
        side: CaptionSide::Top,
        block_height: um(500),
        gap: um(100),
        keep_with_table: true,
        content_sha256: "b".repeat(64),
    });
    let top = observation(
        3_600,
        4_000,
        vec![TablePage {
            page_index: 7,
            items: vec![
                TablePageItem::Caption {
                    side: CaptionSide::Top,
                },
                row(0, 1_000),
                row(1, 2_000),
            ],
        }],
    );
    let receipt =
        TablePaginationValidator::validate(&grid, &policy, &top, TablePaginationLimits::default())?;
    assert_eq!(receipt.caption_page_index(), Some(7));

    if let Some(caption) = policy.caption.as_mut() {
        caption.side = CaptionSide::Bottom;
    }
    let bottom = observation(
        3_600,
        4_000,
        vec![TablePage {
            page_index: 7,
            items: vec![
                row(0, 1_000),
                row(1, 2_000),
                TablePageItem::Caption {
                    side: CaptionSide::Bottom,
                },
            ],
        }],
    );
    TablePaginationValidator::validate(&grid, &policy, &bottom, TablePaginationLimits::default())?;

    let mut wrong_order = bottom.clone();
    wrong_order.pages[0].items.swap(1, 2);
    assert_eq!(
        TablePaginationValidator::validate(
            &grid,
            &policy,
            &wrong_order,
            TablePaginationLimits::default(),
        ),
        Err(TablePaginationError::CaptionOrder)
    );
    Ok(())
}

#[test]
fn repeated_header_mismatch_and_cross_body_span_fail_closed() -> TestResult {
    let base_grid = grid(3)?;
    let base_policy = policy(&[1_000, 2_000, 2_000]);
    let observed = observation(
        3_000,
        4_000,
        vec![
            TablePage {
                page_index: 7,
                items: vec![row(0, 1_000), row(1, 2_000)],
            },
            TablePage {
                page_index: 8,
                items: vec![row(2, 2_000)],
            },
        ],
    );
    assert_eq!(
        TablePaginationValidator::validate(
            &base_grid,
            &base_policy,
            &observed,
            TablePaginationLimits::default(),
        ),
        Err(TablePaginationError::HeaderMismatch)
    );

    let split_header_grid = grid(2)?;
    let mut split_header_policy = policy(&[2_000, 1_000]);
    split_header_policy.page_split = TablePageSplitPolicy::Allow;
    let split_header = observation(
        1_000,
        4_000,
        vec![
            TablePage {
                page_index: 7,
                items: vec![TablePageItem::RowFragment {
                    row: 0,
                    fragment_index: 0,
                    height: um(1_000),
                    begins_row: true,
                    ends_row: false,
                }],
            },
            TablePage {
                page_index: 8,
                items: vec![
                    TablePageItem::RepeatedHeader { row: 0 },
                    TablePageItem::RowFragment {
                        row: 0,
                        fragment_index: 1,
                        height: um(1_000),
                        begins_row: false,
                        ends_row: true,
                    },
                    row(1, 1_000),
                ],
            },
        ],
    );
    assert_eq!(
        TablePaginationValidator::validate(
            &split_header_grid,
            &split_header_policy,
            &split_header,
            TablePaginationLimits::default(),
        ),
        Err(TablePaginationError::HeaderRowSplit)
    );

    let crossing = TableGrid::new(
        2,
        1,
        vec![span("crossing", 0, 2)?],
        TableGridLimits::default(),
    )?;
    assert_eq!(
        TablePaginationValidator::validate(
            &crossing,
            &policy(&[1_000, 2_000]),
            &observation(
                3_000,
                3_000,
                vec![TablePage {
                    page_index: 7,
                    items: vec![row(0, 1_000), row(1, 2_000)],
                }],
            ),
            TablePaginationLimits::default(),
        ),
        Err(TablePaginationError::HeaderSpanCrossesBody)
    );
    Ok(())
}

#[test]
fn avoid_row_rejects_vertical_merged_cell_across_pages() -> TestResult {
    let grid = TableGrid::new(
        3,
        1,
        vec![span("header", 0, 1)?, span("merged", 1, 2)?],
        TableGridLimits::default(),
    )?;
    let policy = policy(&[1_000, 2_000, 2_000]);
    let observed = observation(
        3_000,
        3_000,
        vec![
            TablePage {
                page_index: 7,
                items: vec![row(0, 1_000), row(1, 2_000)],
            },
            TablePage {
                page_index: 8,
                items: vec![TablePageItem::RepeatedHeader { row: 0 }, row(2, 2_000)],
            },
        ],
    );
    assert_eq!(
        TablePaginationValidator::validate(
            &grid,
            &policy,
            &observed,
            TablePaginationLimits::default(),
        ),
        Err(TablePaginationError::MergedCellSplit)
    );
    Ok(())
}

#[test]
fn page_capacity_fragment_and_row_accounting_fail_closed() -> TestResult {
    let grid = grid(2)?;
    let policy = policy(&[1_000, 2_000]);
    let overflow = observation(
        2_999,
        3_000,
        vec![TablePage {
            page_index: 7,
            items: vec![row(0, 1_000), row(1, 2_000)],
        }],
    );
    assert_eq!(
        TablePaginationValidator::validate(
            &grid,
            &policy,
            &overflow,
            TablePaginationLimits::default(),
        ),
        Err(TablePaginationError::PageOverflow)
    );

    let incomplete = observation(
        3_000,
        3_000,
        vec![TablePage {
            page_index: 7,
            items: vec![row(0, 1_000)],
        }],
    );
    assert_eq!(
        TablePaginationValidator::validate(
            &grid,
            &policy,
            &incomplete,
            TablePaginationLimits::default(),
        ),
        Err(TablePaginationError::IncompleteRows)
    );

    let mut wrong_page = incomplete;
    wrong_page.pages[0].page_index = 8;
    assert_eq!(
        TablePaginationValidator::validate(
            &grid,
            &policy,
            &wrong_page,
            TablePaginationLimits::default(),
        ),
        Err(TablePaginationError::PageIndex)
    );
    Ok(())
}

#[test]
fn bounded_json_rejects_unknown_duplicate_and_oversized_inputs() -> TestResult {
    let limits = TablePaginationLimits::default();
    let policy = policy(&[1_000]);
    let canonical = policy.canonical_json(limits)?;
    assert_eq!(
        TablePaginationPolicy::from_json(&canonical, limits)?,
        policy
    );

    let unknown = br#"{"schema_version":"hwpx-agent.table-pagination/v1","page_split":"avoid_row","repeat_header_rows":0,"rows":[],"caption":null,"extra":true}"#;
    assert_eq!(
        TablePaginationPolicy::from_json(unknown, limits),
        Err(TablePaginationError::InvalidJson)
    );
    let duplicate = br#"{"schema_version":"hwpx-agent.table-pagination/v1","schema_version":"hwpx-agent.table-pagination/v1","page_split":"avoid_row","repeat_header_rows":0,"rows":[],"caption":null}"#;
    assert_eq!(
        TablePaginationPolicy::from_json(duplicate, limits),
        Err(TablePaginationError::InvalidJson)
    );

    let tiny = TablePaginationLimits::new(TablePaginationLimitConfig {
        rows: 1,
        pages: 1,
        fragments: 1,
        dimension_micrometers: 1,
        serialized_bytes: 1,
    })?;
    assert_eq!(
        TablePaginationPolicy::from_json(&canonical, tiny),
        Err(TablePaginationError::InputLimit)
    );
    Ok(())
}

#[test]
fn public_error_codes_are_stable() {
    assert_eq!(
        TablePaginationError::HeaderMismatch.code(),
        "table_pagination_header_mismatch"
    );
    assert_eq!(
        TablePaginationError::MergedCellSplit.code(),
        "table_pagination_merged_cell_split"
    );
    assert_eq!(
        TablePaginationError::UnbreakableObjectSplit.code(),
        "table_pagination_unbreakable_object_split"
    );
    assert_eq!(
        TablePaginationError::OutputLimit.code(),
        "table_pagination_output_limit"
    );
}
