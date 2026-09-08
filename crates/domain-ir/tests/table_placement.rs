use domain_ir::{
    LengthMicrometers, LogicalId, TABLE_PLACEMENT_SCHEMA_VERSION, TableAttachmentMode,
    TableFloatingPlacement, TableHorizontalAlignment, TableHorizontalReference, TableOuterMargins,
    TablePlacementError, TablePlacementLimitConfig, TablePlacementLimits, TablePlacementOperation,
    TablePlacementState, TablePlacementStateDraft, TableTextFlow, TableTextWrap,
    TableVerticalAlignment, TableVerticalReference,
};

type TestResult = Result<(), Box<dyn std::error::Error>>;

fn um(value: i64) -> LengthMicrometers {
    LengthMicrometers::from_raw(value)
}

fn margins(value: i64) -> TableOuterMargins {
    TableOuterMargins {
        left: um(value),
        right: um(value + 1),
        top: um(value + 2),
        bottom: um(value + 3),
    }
}

fn floating(seed: i64) -> TableFloatingPlacement {
    TableFloatingPlacement {
        horizontal_reference: TableHorizontalReference::Column,
        vertical_reference: TableVerticalReference::Paragraph,
        horizontal_alignment: TableHorizontalAlignment::Left,
        vertical_alignment: TableVerticalAlignment::Top,
        horizontal_offset: um(seed),
        vertical_offset: um(-seed),
        flow_with_text: true,
        allow_overlap: false,
        hold_anchor_and_shape: false,
    }
}

fn state(attachment: TableAttachmentMode) -> Result<TablePlacementState, TablePlacementError> {
    let table_id =
        LogicalId::parse("private-table").map_err(|_| TablePlacementError::InvalidJson)?;
    TablePlacementState::from_draft(
        TablePlacementStateDraft {
            schema_version: TABLE_PLACEMENT_SCHEMA_VERSION.to_owned(),
            table_id,
            attachment,
            text_wrap: TableTextWrap::TopAndBottom,
            text_flow: TableTextFlow::BothSides,
            outer_margins: margins(100),
        },
        TablePlacementLimits::default(),
    )
}

#[test]
fn state_roundtrips_with_exact_attachment_and_inactive_values() -> TestResult {
    let value = state(TableAttachmentMode::Inline {
        affect_line_spacing: true,
    })?;
    let bytes = value.canonical_json(TablePlacementLimits::default())?;
    let reopened = TablePlacementState::from_json(&bytes, TablePlacementLimits::default())?;
    assert_eq!(reopened, value);
    assert_eq!(reopened.text_wrap(), TableTextWrap::TopAndBottom);
    assert_eq!(reopened.text_flow(), TableTextFlow::BothSides);
    assert_eq!(reopened.outer_margins(), margins(100));
    Ok(())
}

#[test]
fn position_changes_only_floating_placement() -> TestResult {
    let source = state(TableAttachmentMode::Floating {
        placement: floating(20),
    })?;
    let next = TableFloatingPlacement {
        horizontal_reference: TableHorizontalReference::Page,
        vertical_reference: TableVerticalReference::Paper,
        horizontal_alignment: TableHorizontalAlignment::Outside,
        vertical_alignment: TableVerticalAlignment::Inside,
        horizontal_offset: um(500),
        vertical_offset: um(-250),
        flow_with_text: false,
        allow_overlap: true,
        hold_anchor_and_shape: true,
    };
    let result = source.apply(
        TablePlacementOperation::SetPosition { placement: next },
        TablePlacementLimits::default(),
    )?;
    assert_eq!(
        result.state().attachment(),
        TableAttachmentMode::Floating { placement: next }
    );
    assert_eq!(result.state().table_id(), source.table_id());
    assert_eq!(result.state().text_wrap(), source.text_wrap());
    assert_eq!(result.state().text_flow(), source.text_flow());
    assert_eq!(result.state().outer_margins(), source.outer_margins());
    assert_eq!(result.receipt().capability_id(), "table.position");
    assert!(result.receipt().changed());
    Ok(())
}

#[test]
fn inline_and_floating_conversion_preserve_wrap_and_margins() -> TestResult {
    let source = state(TableAttachmentMode::Floating {
        placement: floating(10),
    })?;
    let inline = source.apply(
        TablePlacementOperation::SetInline {
            affect_line_spacing: false,
        },
        TablePlacementLimits::default(),
    )?;
    assert_eq!(
        inline.state().attachment(),
        TableAttachmentMode::Inline {
            affect_line_spacing: false
        }
    );
    assert_eq!(inline.receipt().capability_id(), "table.inline_floating");
    assert_eq!(inline.state().text_wrap(), source.text_wrap());
    assert_eq!(inline.state().outer_margins(), source.outer_margins());

    let restored = inline.state().apply(
        TablePlacementOperation::SetFloating {
            placement: floating(99),
        },
        TablePlacementLimits::default(),
    )?;
    assert_eq!(
        restored.state().attachment(),
        TableAttachmentMode::Floating {
            placement: floating(99)
        }
    );
    assert_eq!(restored.state().text_wrap(), source.text_wrap());
    assert_eq!(restored.state().outer_margins(), source.outer_margins());
    Ok(())
}

#[test]
fn wrap_and_flow_change_together_without_touching_position() -> TestResult {
    let source = state(TableAttachmentMode::Floating {
        placement: floating(31),
    })?;
    let result = source.apply(
        TablePlacementOperation::SetWrap {
            text_wrap: TableTextWrap::Square,
            text_flow: TableTextFlow::LargestOnly,
        },
        TablePlacementLimits::default(),
    )?;
    assert_eq!(result.state().attachment(), source.attachment());
    assert_eq!(result.state().text_wrap(), TableTextWrap::Square);
    assert_eq!(result.state().text_flow(), TableTextFlow::LargestOnly);
    assert_eq!(result.state().outer_margins(), source.outer_margins());
    assert_eq!(result.receipt().capability_id(), "table.wrap");
    Ok(())
}

#[test]
fn outer_margin_operation_is_independent_and_idempotent() -> TestResult {
    let source = state(TableAttachmentMode::Inline {
        affect_line_spacing: true,
    })?;
    let operation = TablePlacementOperation::SetOuterMargins {
        margins: margins(700),
    };
    let first = source.apply(operation, TablePlacementLimits::default())?;
    assert_eq!(first.state().outer_margins(), margins(700));
    assert_eq!(first.state().attachment(), source.attachment());
    assert_eq!(first.receipt().capability_id(), "table.outer_margin");
    assert!(first.receipt().changed());
    let repeated = first
        .state()
        .apply(operation, TablePlacementLimits::default())?;
    assert_eq!(repeated.state(), first.state());
    assert!(!repeated.receipt().changed());
    Ok(())
}

#[test]
fn inactive_position_and_wrap_operations_fail_closed() -> TestResult {
    let source = state(TableAttachmentMode::Inline {
        affect_line_spacing: true,
    })?;
    let before = source.canonical_sha256(TablePlacementLimits::default())?;
    assert_eq!(
        source.apply(
            TablePlacementOperation::SetPosition {
                placement: floating(10)
            },
            TablePlacementLimits::default()
        ),
        Err(TablePlacementError::RequiresFloating)
    );
    assert_eq!(
        source.apply(
            TablePlacementOperation::SetWrap {
                text_wrap: TableTextWrap::BehindText,
                text_flow: TableTextFlow::LeftOnly
            },
            TablePlacementLimits::default()
        ),
        Err(TablePlacementError::RequiresFloating)
    );
    assert_eq!(
        source.canonical_sha256(TablePlacementLimits::default())?,
        before
    );
    Ok(())
}

#[test]
fn offset_margin_and_limit_bounds_fail_closed() -> TestResult {
    let limits = TablePlacementLimits::new(TablePlacementLimitConfig {
        input_bytes: 512,
        offset_micrometers: 1_000,
        margin_micrometers: 500,
        serialized_bytes: 2_048,
    })?;
    let table_id = LogicalId::parse("table-a")?;
    let draft = |attachment, outer_margins| TablePlacementStateDraft {
        schema_version: TABLE_PLACEMENT_SCHEMA_VERSION.to_owned(),
        table_id: table_id.clone(),
        attachment,
        text_wrap: TableTextWrap::Square,
        text_flow: TableTextFlow::BothSides,
        outer_margins,
    };
    assert_eq!(
        TablePlacementState::from_draft(
            draft(
                TableAttachmentMode::Floating {
                    placement: TableFloatingPlacement {
                        horizontal_offset: um(-1_001),
                        ..floating(0)
                    }
                },
                margins(1)
            ),
            limits
        ),
        Err(TablePlacementError::OffsetOutOfRange)
    );
    assert_eq!(
        TablePlacementState::from_draft(
            draft(
                TableAttachmentMode::Inline {
                    affect_line_spacing: false
                },
                TableOuterMargins {
                    left: um(-1),
                    right: um(0),
                    top: um(0),
                    bottom: um(0)
                }
            ),
            limits
        ),
        Err(TablePlacementError::MarginOutOfRange)
    );
    assert_eq!(
        TablePlacementLimits::new(TablePlacementLimitConfig {
            input_bytes: 2,
            offset_micrometers: 1,
            margin_micrometers: 1,
            serialized_bytes: 1,
        }),
        Err(TablePlacementError::InvalidLimit)
    );
    Ok(())
}

#[test]
fn strict_json_version_and_size_fail_closed() -> TestResult {
    let value = state(TableAttachmentMode::Floating {
        placement: floating(5),
    })?;
    let json = String::from_utf8(value.canonical_json(TablePlacementLimits::default())?)?;
    let unknown = json.replacen('{', "{\"unknown\":true,", 1);
    assert_eq!(
        TablePlacementState::from_json(unknown.as_bytes(), TablePlacementLimits::default()),
        Err(TablePlacementError::InvalidJson)
    );
    let duplicate = json.replacen(
        "{\"schema_version\":",
        "{\"schema_version\":\"duplicate\",\"schema_version\":",
        1,
    );
    assert_eq!(
        TablePlacementState::from_json(duplicate.as_bytes(), TablePlacementLimits::default()),
        Err(TablePlacementError::InvalidJson)
    );
    let wrong = json.replace(TABLE_PLACEMENT_SCHEMA_VERSION, "unsupported/v0");
    assert_eq!(
        TablePlacementState::from_json(wrong.as_bytes(), TablePlacementLimits::default()),
        Err(TablePlacementError::UnsupportedVersion)
    );
    assert_eq!(
        TablePlacementState::from_json(&[], TablePlacementLimits::default()),
        Err(TablePlacementError::InputLimit)
    );
    let tiny = TablePlacementLimits::new(TablePlacementLimitConfig {
        input_bytes: 32,
        offset_micrometers: 1_000,
        margin_micrometers: 1_000,
        serialized_bytes: 32,
    })?;
    assert_eq!(
        TablePlacementState::from_json(&[b' '; 33], tiny),
        Err(TablePlacementError::InputLimit)
    );
    Ok(())
}

#[test]
fn canonical_state_and_receipt_are_deterministic() -> TestResult {
    let source = state(TableAttachmentMode::Floating {
        placement: floating(44),
    })?;
    let operation = TablePlacementOperation::SetWrap {
        text_wrap: TableTextWrap::InFrontOfText,
        text_flow: TableTextFlow::RightOnly,
    };
    let first = source.apply(operation, TablePlacementLimits::default())?;
    let second = source.apply(operation, TablePlacementLimits::default())?;
    assert_eq!(first, second);
    assert_eq!(
        first
            .state()
            .canonical_json(TablePlacementLimits::default())?,
        second
            .state()
            .canonical_json(TablePlacementLimits::default())?
    );
    assert_eq!(
        first
            .receipt()
            .canonical_json(TablePlacementLimits::default())?,
        second
            .receipt()
            .canonical_json(TablePlacementLimits::default())?
    );
    Ok(())
}

#[test]
fn output_limit_is_checked_after_operation() -> TestResult {
    let source = state(TableAttachmentMode::Floating {
        placement: floating(1),
    })?;
    let bytes = source.canonical_json(TablePlacementLimits::default())?;
    let limit = bytes.len();
    let limits = TablePlacementLimits::new(TablePlacementLimitConfig {
        input_bytes: limit,
        offset_micrometers: 1_000,
        margin_micrometers: 1_000,
        serialized_bytes: limit,
    })?;
    let reopened = TablePlacementState::from_json(&bytes, limits)?;
    let error = reopened.apply(
        TablePlacementOperation::SetPosition {
            placement: TableFloatingPlacement {
                horizontal_reference: TableHorizontalReference::Paragraph,
                horizontal_alignment: TableHorizontalAlignment::Outside,
                horizontal_offset: um(999),
                ..floating(999)
            },
        },
        limits,
    );
    assert_eq!(error, Err(TablePlacementError::OutputLimit));
    Ok(())
}

#[test]
fn debug_output_redacts_identifiers_offsets_margins_and_hashes() -> TestResult {
    let source = state(TableAttachmentMode::Floating {
        placement: floating(654_321),
    })?;
    let result = source.apply(
        TablePlacementOperation::SetOuterMargins {
            margins: margins(765_432),
        },
        TablePlacementLimits::default(),
    )?;
    let debug = format!("{result:?}");
    assert!(!debug.contains("private-table"));
    assert!(!debug.contains("654321"));
    assert!(!debug.contains("765432"));
    assert!(!debug.contains(result.receipt().source_state_sha256()));
    assert!(!debug.contains(result.receipt().output_state_sha256()));
    Ok(())
}

#[test]
fn fixed_seed_operations_remain_bounded_and_deterministic() -> TestResult {
    for seed in 0_i64..256 {
        let source = state(TableAttachmentMode::Floating {
            placement: floating(seed),
        })?;
        let operation = match seed % 4 {
            0 => TablePlacementOperation::SetPosition {
                placement: floating(seed + 1),
            },
            1 => TablePlacementOperation::SetInline {
                affect_line_spacing: seed % 2 == 0,
            },
            2 => TablePlacementOperation::SetWrap {
                text_wrap: TableTextWrap::Square,
                text_flow: TableTextFlow::LargestOnly,
            },
            _ => TablePlacementOperation::SetOuterMargins {
                margins: margins(seed),
            },
        };
        let first = source.apply(operation, TablePlacementLimits::default())?;
        let second = source.apply(operation, TablePlacementLimits::default())?;
        assert_eq!(first, second);
    }
    Ok(())
}

#[test]
fn schema_capability_and_error_codes_are_stable() {
    assert_eq!(
        TABLE_PLACEMENT_SCHEMA_VERSION,
        "hwpx-agent.table-placement/v1"
    );
    assert_eq!(
        TablePlacementOperation::SetPosition {
            placement: floating(0)
        }
        .capability_id(),
        "table.position"
    );
    assert_eq!(
        TablePlacementOperation::SetFloating {
            placement: floating(0)
        }
        .capability_id(),
        "table.inline_floating"
    );
    assert_eq!(
        TablePlacementOperation::SetWrap {
            text_wrap: TableTextWrap::Square,
            text_flow: TableTextFlow::BothSides
        }
        .capability_id(),
        "table.wrap"
    );
    assert_eq!(
        TablePlacementOperation::SetOuterMargins {
            margins: margins(0)
        }
        .capability_id(),
        "table.outer_margin"
    );
    assert_eq!(
        TablePlacementError::RequiresFloating.code(),
        "table_placement_requires_floating"
    );
    assert_eq!(
        TablePlacementError::MarginOutOfRange.code(),
        "table_placement_margin_out_of_range"
    );
}
