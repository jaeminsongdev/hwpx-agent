#![allow(clippy::expect_used)] // Fixtures keep failures local and readable.

use domain_ir::{
    FIELD_ENGINE_SCHEMA_VERSION, FieldAnchor, FieldCacheStatus, FieldCachedResult, FieldDefinition,
    FieldDocumentState, FieldDocumentStateDraft, FieldEngineBuilder, FieldEngineError,
    FieldEngineLimitConfig, FieldEngineLimits, FieldIdentity, FieldNumberFormat, FieldOperation,
    FieldRequest, FieldRequestDraft, FieldState, FieldUpdatePolicy, LogicalId, ObjectNumberKind,
    OpaqueFieldProperty,
};

const FLOW_A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const FLOW_B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
const STATE_C: &str = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc";

fn limits() -> FieldEngineLimits {
    FieldEngineLimits::new(FieldEngineLimitConfig::default()).expect("limits")
}

fn identity(index: u32) -> FieldIdentity {
    FieldIdentity {
        logical_field_id: LogicalId::parse(format!("field-{index}")).expect("field id"),
        native_begin_id: index * 2 + 1,
        native_end_id: index * 2 + 2,
    }
}

fn result_for(definition: &FieldDefinition, index: u32) -> FieldCachedResult {
    if definition.expects_number_result() {
        FieldCachedResult::Number {
            value: i64::from(index + 1),
            display: format!("{}", index + 1),
        }
    } else {
        FieldCachedResult::Text {
            display: format!("private-result-{index}"),
        }
    }
}

fn field(index: u32, definition: FieldDefinition) -> FieldState {
    FieldState {
        identity: identity(index),
        anchor: FieldAnchor {
            paragraph_id: LogicalId::parse(format!("paragraph-{index}")).expect("paragraph id"),
            run_ordinal: index,
            inline_ordinal: index,
        },
        cached_result: result_for(&definition, index),
        definition,
        update_policy: FieldUpdatePolicy::RecomputeDirect,
        cache_status: FieldCacheStatus::Stale,
        locked: false,
        evaluation_context_sha256: None,
        character_style_sha256: FLOW_A.to_owned(),
        paragraph_style_sha256: FLOW_B.to_owned(),
        field_payload_sha256: STATE_C.to_owned(),
        opaque_properties: vec![OpaqueFieldProperty {
            namespace: "hp".to_owned(),
            name: format!("opaque-{index}"),
            value_sha256: STATE_C.to_owned(),
        }],
    }
}

fn state(fields: Vec<FieldState>) -> FieldDocumentState {
    FieldDocumentState::from_draft(
        FieldDocumentStateDraft {
            schema_version: FIELD_ENGINE_SCHEMA_VERSION.to_owned(),
            fields,
            non_field_content_sha256: FLOW_A.to_owned(),
            style_catalog_sha256: FLOW_B.to_owned(),
            reference_inventory_sha256: STATE_C.to_owned(),
            resource_inventory_sha256: FLOW_A.to_owned(),
            opaque_document_state_sha256: FLOW_B.to_owned(),
        },
        limits(),
    )
    .expect("valid state")
}

fn request(
    source: &FieldDocumentState,
    operation: FieldOperation,
) -> Result<FieldRequest, FieldEngineError> {
    FieldRequest::from_draft(
        FieldRequestDraft {
            schema_version: FIELD_ENGINE_SCHEMA_VERSION.to_owned(),
            request_id: LogicalId::parse("request-private").expect("request id"),
            expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            operation,
        },
        source,
        FLOW_A,
        limits(),
    )
}

fn build(source: &FieldDocumentState, operation: FieldOperation) -> FieldDocumentState {
    let request = request(source, operation).expect("request");
    let plan = FieldEngineBuilder::plan(source, &request, FLOW_A, limits()).expect("plan");
    FieldEngineBuilder::build(&plan, source, FLOW_A, limits())
        .expect("result")
        .state
}

fn definitions() -> Vec<FieldDefinition> {
    vec![
        FieldDefinition::Named {
            name: "private-name".to_owned(),
            parameter: "private-parameter".to_owned(),
        },
        FieldDefinition::UserDefined {
            name: "private-user".to_owned(),
        },
        FieldDefinition::ClickHere {
            prompt: "private prompt".to_owned(),
        },
        FieldDefinition::DateTime {
            format: "yyyy-MM-dd HH:mm".to_owned(),
            locale: "ko-KR".to_owned(),
            timezone_offset_minutes: 540,
        },
        FieldDefinition::FileName {
            include_path: false,
        },
        FieldDefinition::PageNumber {
            format: FieldNumberFormat::Digit,
        },
        FieldDefinition::SectionNumber {
            format: FieldNumberFormat::RomanUpper,
        },
        FieldDefinition::ObjectNumber {
            object_kind: ObjectNumberKind::Table,
            format: FieldNumberFormat::CircledDigit,
        },
    ]
}

#[test]
fn inserts_all_eight_field_kinds_with_distinct_capability_ids() {
    let expected = [
        "ref.field_insert",
        "ref.field_user",
        "ref.field_click_here",
        "ref.field_date_time",
        "ref.field_filename",
        "ref.field_page_number",
        "ref.field_section_number",
        "ref.field_object_number",
    ];
    let mut current = state(Vec::new());
    for (index, definition) in definitions().into_iter().enumerate() {
        let value = field(u32::try_from(index).expect("small index"), definition);
        let operation = FieldOperation::Insert {
            insertion_index: index,
            field: value,
        };
        assert_eq!(operation.capability_id(), expected[index]);
        current = build(&current, operation);
    }
    assert_eq!(current.fields().len(), 8);
}

#[test]
fn updates_cached_result_with_explicit_context_and_preserves_every_unrelated_binding() {
    let source = state(vec![field(
        1,
        FieldDefinition::FileName {
            include_path: false,
        },
    )]);
    let before: serde_json::Value =
        serde_json::from_slice(&source.canonical_json(limits()).expect("json")).expect("value");
    let target = build(
        &source,
        FieldOperation::UpdateResult {
            target: identity(1),
            cached_result: FieldCachedResult::Text {
                display: "updated-private-name.hwpx".to_owned(),
            },
            evaluation_context_sha256: STATE_C.to_owned(),
        },
    );
    let after: serde_json::Value =
        serde_json::from_slice(&target.canonical_json(limits()).expect("json")).expect("value");
    assert_eq!(after["fields"][0]["cache_status"], "current");
    assert_eq!(after["fields"][0]["evaluation_context_sha256"], STATE_C);
    for field_name in [
        "identity",
        "anchor",
        "definition",
        "update_policy",
        "locked",
        "character_style_sha256",
        "paragraph_style_sha256",
        "field_payload_sha256",
        "opaque_properties",
    ] {
        assert_eq!(
            before["fields"][0][field_name],
            after["fields"][0][field_name]
        );
    }
    for field_name in [
        "non_field_content_sha256",
        "style_catalog_sha256",
        "reference_inventory_sha256",
        "resource_inventory_sha256",
        "opaque_document_state_sha256",
    ] {
        assert_eq!(before[field_name], after[field_name]);
    }
}

#[test]
fn lock_and_freeze_policies_fail_closed_without_partial_update() {
    let source = state(vec![field(
        1,
        FieldDefinition::DateTime {
            format: "yyyy-MM-dd".to_owned(),
            locale: "ko-KR".to_owned(),
            timezone_offset_minutes: 540,
        },
    )]);
    let locked = build(
        &source,
        FieldOperation::SetLock {
            target: identity(1),
            locked: true,
        },
    );
    assert_eq!(
        request(
            &locked,
            FieldOperation::UpdateResult {
                target: identity(1),
                cached_result: FieldCachedResult::Text {
                    display: "2026-09-12".to_owned(),
                },
                evaluation_context_sha256: STATE_C.to_owned(),
            },
        ),
        Err(FieldEngineError::FieldLocked)
    );

    let mut frozen_field = field(
        2,
        FieldDefinition::UserDefined {
            name: "u".to_owned(),
        },
    );
    frozen_field.update_policy = FieldUpdatePolicy::FreezeText;
    frozen_field.cache_status = FieldCacheStatus::Current;
    let frozen = state(vec![frozen_field]);
    assert_eq!(
        request(
            &frozen,
            FieldOperation::UpdateResult {
                target: identity(2),
                cached_result: FieldCachedResult::Text {
                    display: "changed".to_owned(),
                },
                evaluation_context_sha256: STATE_C.to_owned(),
            },
        ),
        Err(FieldEngineError::FieldLocked)
    );
}

#[test]
fn collisions_missing_targets_bad_indexes_and_noops_are_rejected() {
    let existing = field(
        1,
        FieldDefinition::UserDefined {
            name: "one".to_owned(),
        },
    );
    let source = state(vec![existing.clone()]);
    assert_eq!(
        request(
            &source,
            FieldOperation::Insert {
                insertion_index: 2,
                field: field(
                    2,
                    FieldDefinition::UserDefined {
                        name: "two".to_owned()
                    }
                ),
            },
        ),
        Err(FieldEngineError::InvalidInsertionIndex)
    );
    assert_eq!(
        request(
            &source,
            FieldOperation::Insert {
                insertion_index: 1,
                field: existing,
            },
        ),
        Err(FieldEngineError::InvalidIdentity)
    );
    assert_eq!(
        request(
            &source,
            FieldOperation::SetLock {
                target: identity(99),
                locked: true,
            },
        ),
        Err(FieldEngineError::FieldNotFound)
    );
    assert_eq!(
        request(
            &source,
            FieldOperation::SetLock {
                target: identity(1),
                locked: false,
            },
        ),
        Err(FieldEngineError::Noop)
    );
}

#[test]
fn result_kind_names_timezones_and_opaque_keys_are_validated() {
    let mut number_field = field(
        1,
        FieldDefinition::PageNumber {
            format: FieldNumberFormat::Digit,
        },
    );
    number_field.cached_result = FieldCachedResult::Text {
        display: "1".to_owned(),
    };
    assert_eq!(
        FieldDocumentState::from_draft(
            FieldDocumentStateDraft {
                schema_version: FIELD_ENGINE_SCHEMA_VERSION.to_owned(),
                fields: vec![number_field],
                non_field_content_sha256: FLOW_A.to_owned(),
                style_catalog_sha256: FLOW_A.to_owned(),
                reference_inventory_sha256: FLOW_A.to_owned(),
                resource_inventory_sha256: FLOW_A.to_owned(),
                opaque_document_state_sha256: FLOW_A.to_owned(),
            },
            limits(),
        ),
        Err(FieldEngineError::InvalidField)
    );

    let invalid = field(
        2,
        FieldDefinition::DateTime {
            format: "yyyy".to_owned(),
            locale: "ko_KR".to_owned(),
            timezone_offset_minutes: 1_081,
        },
    );
    assert_eq!(
        request(
            &state(Vec::new()),
            FieldOperation::Insert {
                insertion_index: 0,
                field: invalid,
            },
        ),
        Err(FieldEngineError::InvalidField)
    );

    let mut duplicate_opaque = field(
        3,
        FieldDefinition::UserDefined {
            name: "u".to_owned(),
        },
    );
    duplicate_opaque
        .opaque_properties
        .push(duplicate_opaque.opaque_properties[0].clone());
    assert_eq!(
        request(
            &state(Vec::new()),
            FieldOperation::Insert {
                insertion_index: 0,
                field: duplicate_opaque,
            },
        ),
        Err(FieldEngineError::InvalidField)
    );
}

#[test]
fn request_plan_and_build_recheck_exact_state_and_document_flow() {
    let source = state(Vec::new());
    let operation = FieldOperation::Insert {
        insertion_index: 0,
        field: field(
            1,
            FieldDefinition::UserDefined {
                name: "u".to_owned(),
            },
        ),
    };
    let request = request(&source, operation).expect("request");
    assert_eq!(
        FieldEngineBuilder::plan(&source, &request, FLOW_B, limits()),
        Err(FieldEngineError::DocumentFlowDrift)
    );
    let plan = FieldEngineBuilder::plan(&source, &request, FLOW_A, limits()).expect("plan");
    let drifted = state(vec![field(
        9,
        FieldDefinition::UserDefined {
            name: "x".to_owned(),
        },
    )]);
    assert_eq!(
        FieldEngineBuilder::build(&plan, &drifted, FLOW_A, limits()),
        Err(FieldEngineError::SourceStateDrift)
    );
    assert_eq!(
        FieldEngineBuilder::build(&plan, &source, FLOW_B, limits()),
        Err(FieldEngineError::DocumentFlowDrift)
    );
}

#[test]
fn strict_json_rejects_duplicate_unknown_and_oversized_input() {
    let source = state(Vec::new());
    let request = request(
        &source,
        FieldOperation::Insert {
            insertion_index: 0,
            field: field(
                1,
                FieldDefinition::UserDefined {
                    name: "u".to_owned(),
                },
            ),
        },
    )
    .expect("request");
    let json = request.canonical_json(limits()).expect("json");
    assert!(FieldRequest::from_json(&json, &source, FLOW_A, limits()).is_ok());
    let duplicate = br#"{"schema_version":"hwpx-agent.field-engine/v1","schema_version":"hwpx-agent.field-engine/v1"}"#;
    assert_eq!(
        FieldRequest::from_json(duplicate, &source, FLOW_A, limits()),
        Err(FieldEngineError::InvalidJson)
    );
    let mut unknown: serde_json::Value = serde_json::from_slice(&json).expect("value");
    unknown
        .as_object_mut()
        .expect("object")
        .insert("unknown".to_owned(), serde_json::Value::Bool(true));
    assert_eq!(
        FieldRequest::from_json(
            &serde_json::to_vec(&unknown).expect("bytes"),
            &source,
            FLOW_A,
            limits(),
        ),
        Err(FieldEngineError::InvalidJson)
    );
    assert_eq!(
        FieldRequest::from_json(
            &vec![b' '; limits().config().input_bytes + 1],
            &source,
            FLOW_A,
            limits(),
        ),
        Err(FieldEngineError::InputLimit)
    );
}

#[test]
fn canonical_output_is_deterministic_and_debug_is_bounded_and_redacted() {
    let source = state(Vec::new());
    let operation = FieldOperation::Insert {
        insertion_index: 0,
        field: field(
            1,
            FieldDefinition::Named {
                name: "private-name".to_owned(),
                parameter: "private-parameter".to_owned(),
            },
        ),
    };
    let request = request(&source, operation).expect("request");
    let plan = FieldEngineBuilder::plan(&source, &request, FLOW_A, limits()).expect("plan");
    assert_eq!(
        plan.canonical_json(limits()).expect("json"),
        plan.canonical_json(limits()).expect("json")
    );
    let debug = format!("{source:?} {request:?} {plan:?}");
    for secret in [
        "private-name",
        "private-parameter",
        "private-result-1",
        "field-1",
        FLOW_A,
    ] {
        assert!(!debug.contains(secret));
    }
    assert_eq!(
        FieldEngineError::PlanTampered.code(),
        "field_engine_plan_tampered"
    );
}
