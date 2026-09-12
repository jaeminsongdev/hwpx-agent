#![allow(clippy::expect_used)]

use domain_ir::{
    LinkAnchor, LinkPoint, LogicalId, MAIL_MERGE_SCHEMA_VERSION, MailMergeBuilder,
    MailMergeCacheStatus, MailMergeColumn, MailMergeColumnType, MailMergeDataSource,
    MailMergeDocumentState, MailMergeDocumentStateDraft, MailMergeError, MailMergeFieldCache,
    MailMergeFieldNode, MailMergeFieldType, MailMergeLimitConfig, MailMergeLimits,
    MailMergeNativeBeginTag, MailMergeNativeEndTag, MailMergeNativePair, MailMergeOperation,
    MailMergeRequest, MailMergeRequestDraft, MailMergeSectionState, MailMergeSemanticBinding,
    MailMergeSensitivity, OpaqueLinkProperty,
};

const FLOW_A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const FLOW_B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
const FLOW_C: &str = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc";

fn digest(byte: char) -> String {
    byte.to_string().repeat(64)
}

fn id(value: &str) -> LogicalId {
    LogicalId::parse(value).expect("logical id")
}

fn limits() -> MailMergeLimits {
    MailMergeLimits::new(MailMergeLimitConfig::default()).expect("limits")
}

fn anchor(section: &str) -> LinkAnchor {
    LinkAnchor {
        section_id: id(section),
        start: LinkPoint {
            paragraph_ordinal: 0,
            run_ordinal: 1,
            inline_ordinal: 2,
        },
        end: LinkPoint {
            paragraph_ordinal: 0,
            run_ordinal: 1,
            inline_ordinal: 2,
        },
    }
}

fn column(
    logical_id: &str,
    key: char,
    column_type: MailMergeColumnType,
    sensitivity: MailMergeSensitivity,
) -> MailMergeColumn {
    MailMergeColumn {
        logical_column_id: id(logical_id),
        provider_column_key_sha256: digest(key),
        display_name_sha256: digest('d'),
        column_type,
        nullable: false,
        sensitivity,
        semantic_definition_sha256: digest('e'),
        format_sha256: digest('f'),
        opaque_properties: vec![OpaqueLinkProperty {
            namespace: "provider".to_owned(),
            name: format!("column-{logical_id}"),
            value_sha256: digest('1'),
        }],
        locked: false,
    }
}

fn data_source() -> MailMergeDataSource {
    MailMergeDataSource {
        logical_source_id: id("data-source-1"),
        artifact_sha256: digest('1'),
        encryption_envelope_sha256: digest('2'),
        provider_id_sha256: digest('3'),
        provider_version_sha256: digest('4'),
        locale: "ko-KR".to_owned(),
        schema_sha256: digest('5'),
        row_identity_manifest_sha256: digest('6'),
        record_count: 3,
        access_policy_sha256: digest('7'),
        pii_policy_sha256: digest('8'),
        encrypted_artifact: true,
        columns: vec![
            column(
                "column-name",
                '9',
                MailMergeColumnType::Text,
                MailMergeSensitivity::Personal,
            ),
            column(
                "column-balance",
                'a',
                MailMergeColumnType::FixedDecimal,
                MailMergeSensitivity::Sensitive,
            ),
        ],
        opaque_properties: vec![OpaqueLinkProperty {
            namespace: "provider".to_owned(),
            name: "source".to_owned(),
            value_sha256: digest('b'),
        }],
        locked: false,
    }
}

fn draft() -> MailMergeDocumentStateDraft {
    MailMergeDocumentStateDraft {
        schema_version: MAIL_MERGE_SCHEMA_VERSION.to_owned(),
        sections: vec![
            MailMergeSectionState {
                section_id: id("section-1"),
                paragraph_count: 2,
                run_topology_sha256: digest('1'),
                inline_topology_sha256: digest('2'),
                page_assignment_sha256: digest('3'),
                opaque_section_state_sha256: digest('4'),
                locked: false,
            },
            MailMergeSectionState {
                section_id: id("section-2"),
                paragraph_count: 1,
                run_topology_sha256: digest('5'),
                inline_topology_sha256: digest('6'),
                page_assignment_sha256: digest('7'),
                opaque_section_state_sha256: digest('8'),
                locked: false,
            },
        ],
        data_sources: vec![data_source()],
        fields: Vec::new(),
        occupied_non_mailmerge_control_ids: vec![80],
        occupied_non_mailmerge_field_ids: vec![90],
        occupied_non_mailmerge_field_name_sha256: vec![digest('1')],
        preview_inventory_sha256: digest('2'),
        batch_output_inventory_sha256: digest('3'),
        label_layout_catalog_sha256: digest('4'),
        non_mailmerge_content_sha256: digest('5'),
        unrelated_field_inventory_sha256: digest('6'),
        reference_inventory_sha256: digest('7'),
        note_inventory_sha256: digest('8'),
        toc_index_inventory_sha256: digest('9'),
        citation_inventory_sha256: digest('a'),
        object_inventory_sha256: digest('b'),
        numbering_inventory_sha256: digest('c'),
        style_catalog_sha256: digest('d'),
        relationship_inventory_sha256: digest('e'),
        resource_inventory_sha256: digest('f'),
        document_protection_sha256: digest('1'),
        opaque_document_state_sha256: digest('2'),
        document_locked: false,
    }
}

fn state() -> MailMergeDocumentState {
    MailMergeDocumentState::from_draft(draft(), limits()).expect("state")
}

fn field(
    source: &MailMergeDataSource,
    logical_field_id: &str,
    logical_column_id: &str,
    begin_control_id: u32,
    field_id: u32,
) -> MailMergeFieldNode {
    let column_id = id(logical_column_id);
    MailMergeFieldNode {
        logical_field_id: id(logical_field_id),
        begin_control_id,
        field_id,
        anchor: anchor("section-1"),
        logical_source_id: source.logical_source_id.clone(),
        logical_column_id: column_id.clone(),
        cache: MailMergeFieldCache {
            binding_projection_sha256: MailMergeFieldNode::projection_sha256(
                source,
                &column_id,
                limits(),
            )
            .expect("projection"),
            placeholder_text_sha256: digest('3'),
            status: MailMergeCacheStatus::Current,
        },
        native_pair: MailMergeNativePair {
            begin_tag: MailMergeNativeBeginTag::FieldBegin,
            end_tag: MailMergeNativeEndTag::FieldEnd,
            field_type: MailMergeFieldType::Mailmerge,
            semantic_binding: MailMergeSemanticBinding::UnverifiedFieldParameters,
            end_begin_control_id_ref: begin_control_id,
            end_field_id: field_id,
            field_name_sha256: Some(digest('4')),
            editable: true,
            dirty: false,
            z_order: -1,
            parameters_sha256: digest('5'),
            sub_list_sha256: Some(digest('6')),
            meta_tag_sha256: None,
            opaque_begin_state_sha256: digest('7'),
            opaque_end_state_sha256: digest('8'),
        },
        opaque_field_state_sha256: digest('9'),
        opaque_properties: vec![OpaqueLinkProperty {
            namespace: "native".to_owned(),
            name: "mailmerge".to_owned(),
            value_sha256: digest('a'),
        }],
        locked: false,
    }
}

fn request(source: &MailMergeDocumentState, field: MailMergeFieldNode) -> MailMergeRequest {
    MailMergeRequest::from_draft(
        MailMergeRequestDraft {
            schema_version: MAIL_MERGE_SCHEMA_VERSION.to_owned(),
            request_id: id("request-1"),
            expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            operation: MailMergeOperation::FieldInsert {
                insertion_index: 0,
                field: Box::new(field),
            },
        },
        source,
        FLOW_A,
        limits(),
    )
    .expect("request")
}

#[test]
fn inserts_exact_field_and_preserves_sources_and_unrelated_state() {
    let source = state();
    let before: MailMergeDocumentStateDraft = source.clone().into();
    let operation = field(&source.data_sources()[0], "field-1", "column-name", 1, 2);
    let plan = MailMergeBuilder::plan(&source, &request(&source, operation), FLOW_A, limits())
        .expect("plan");
    let result = MailMergeBuilder::build(&plan, &source, FLOW_A, limits()).expect("build");
    let after: MailMergeDocumentStateDraft = result.state.clone().into();

    assert_eq!(result.receipt.capability_id, "ref.mailmerge_field");
    assert_eq!(after.fields.len(), 1);
    assert_eq!(after.data_sources, before.data_sources);
    assert_eq!(
        after.preview_inventory_sha256,
        before.preview_inventory_sha256
    );
    assert_eq!(
        after.batch_output_inventory_sha256,
        before.batch_output_inventory_sha256
    );
    assert_eq!(
        after.label_layout_catalog_sha256,
        before.label_layout_catalog_sha256
    );
    assert_eq!(
        after.non_mailmerge_content_sha256,
        before.non_mailmerge_content_sha256
    );
}

#[test]
fn projection_binds_schema_and_selected_column_but_not_rows_or_unselected_columns() {
    let source = data_source();
    let selected = id("column-name");
    let baseline =
        MailMergeFieldNode::projection_sha256(&source, &selected, limits()).expect("baseline");
    let mut generation_only = source.clone();
    generation_only.artifact_sha256 = digest('c');
    generation_only.encryption_envelope_sha256 = digest('d');
    generation_only.row_identity_manifest_sha256 = digest('e');
    generation_only.record_count = 99;
    generation_only.access_policy_sha256 = digest('f');
    generation_only.pii_policy_sha256 = digest('0');
    generation_only.columns[1].semantic_definition_sha256 = digest('0');
    assert_eq!(
        MailMergeFieldNode::projection_sha256(&generation_only, &selected, limits())
            .expect("generation-only"),
        baseline
    );

    let mut selected_change = source.clone();
    selected_change.columns[0].semantic_definition_sha256 = digest('0');
    assert_ne!(
        MailMergeFieldNode::projection_sha256(&selected_change, &selected, limits())
            .expect("selected change"),
        baseline
    );
    let mut provider_change = source;
    provider_change.schema_sha256 = digest('0');
    assert_ne!(
        MailMergeFieldNode::projection_sha256(&provider_change, &selected, limits())
            .expect("schema change"),
        baseline
    );
}

#[test]
fn missing_source_and_column_fail_before_a_plan_exists() {
    let source = state();
    let mut missing_source = field(&source.data_sources()[0], "field-1", "column-name", 1, 2);
    missing_source.logical_source_id = id("missing-source");
    let error = MailMergeRequest::from_draft(
        MailMergeRequestDraft {
            schema_version: MAIL_MERGE_SCHEMA_VERSION.to_owned(),
            request_id: id("request-1"),
            expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            operation: MailMergeOperation::FieldInsert {
                insertion_index: 0,
                field: Box::new(missing_source),
            },
        },
        &source,
        FLOW_A,
        limits(),
    )
    .expect_err("missing source");
    assert_eq!(error, MailMergeError::SourceMissing);

    let mut missing_column = field(&source.data_sources()[0], "field-1", "column-name", 1, 2);
    missing_column.logical_column_id = id("missing-column");
    assert_eq!(
        MailMergeRequest::from_draft(
            MailMergeRequestDraft {
                schema_version: MAIL_MERGE_SCHEMA_VERSION.to_owned(),
                request_id: id("request-2"),
                expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
                expected_document_flow_sha256: FLOW_A.to_owned(),
                target_document_flow_sha256: FLOW_B.to_owned(),
                operation: MailMergeOperation::FieldInsert {
                    insertion_index: 0,
                    field: Box::new(missing_column),
                },
            },
            &source,
            FLOW_A,
            limits(),
        )
        .expect_err("missing column"),
        MailMergeError::ColumnMissing
    );
}

#[test]
fn encrypted_source_schema_record_count_and_privacy_metadata_are_mandatory() {
    let mut value = draft();
    value.data_sources[0].encrypted_artifact = false;
    assert_eq!(
        MailMergeDocumentState::from_draft(value, limits()).expect_err("plaintext source"),
        MailMergeError::InvalidDataSource
    );

    let mut value = draft();
    value.data_sources[0].record_count = limits().config().records_per_source + 1;
    assert_eq!(
        MailMergeDocumentState::from_draft(value, limits()).expect_err("record bound"),
        MailMergeError::InvalidDataSource
    );

    let mut value = draft();
    value.data_sources[0].pii_policy_sha256.clear();
    assert_eq!(
        MailMergeDocumentState::from_draft(value, limits()).expect_err("pii policy"),
        MailMergeError::InvalidDataSource
    );

    let mut value = draft();
    value.data_sources[0].columns[1].provider_column_key_sha256 = value.data_sources[0].columns[0]
        .provider_column_key_sha256
        .clone();
    assert_eq!(
        MailMergeDocumentState::from_draft(value, limits()).expect_err("provider collision"),
        MailMergeError::InvalidDataSource
    );
}

#[test]
fn logical_native_and_field_name_collisions_are_rejected() {
    let mut value = draft();
    let first = field(&value.data_sources[0], "field-1", "column-name", 1, 2);
    let mut duplicate = field(&value.data_sources[0], "field-1", "column-balance", 3, 4);
    duplicate.native_pair.field_name_sha256 = Some(digest('5'));
    value.fields = vec![first, duplicate];
    assert_eq!(
        MailMergeDocumentState::from_draft(value, limits()).expect_err("logical collision"),
        MailMergeError::InvalidIdentity
    );

    let mut value = draft();
    value.fields = vec![field(
        &value.data_sources[0],
        "field-1",
        "column-name",
        80,
        2,
    )];
    assert_eq!(
        MailMergeDocumentState::from_draft(value, limits()).expect_err("control collision"),
        MailMergeError::InvalidIdentity
    );

    let source = state();
    let mut named = field(&source.data_sources()[0], "field-1", "column-name", 1, 2);
    named.native_pair.field_name_sha256 = Some(digest('1'));
    assert_eq!(
        MailMergeRequest::from_draft(
            MailMergeRequestDraft {
                schema_version: MAIL_MERGE_SCHEMA_VERSION.to_owned(),
                request_id: id("request-3"),
                expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
                expected_document_flow_sha256: FLOW_A.to_owned(),
                target_document_flow_sha256: FLOW_B.to_owned(),
                operation: MailMergeOperation::FieldInsert {
                    insertion_index: 0,
                    field: Box::new(named),
                },
            },
            &source,
            FLOW_A,
            limits(),
        )
        .expect_err("name collision"),
        MailMergeError::FieldNameConflict
    );
}

#[test]
fn stale_new_field_and_protected_targets_fail_without_partial_state() {
    let source = state();
    let mut stale = field(&source.data_sources()[0], "field-1", "column-name", 1, 2);
    stale.cache.binding_projection_sha256 = digest('0');
    stale.cache.status = MailMergeCacheStatus::Stale;
    assert_eq!(
        MailMergeRequest::from_draft(
            MailMergeRequestDraft {
                schema_version: MAIL_MERGE_SCHEMA_VERSION.to_owned(),
                request_id: id("request-1"),
                expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
                expected_document_flow_sha256: FLOW_A.to_owned(),
                target_document_flow_sha256: FLOW_B.to_owned(),
                operation: MailMergeOperation::FieldInsert {
                    insertion_index: 0,
                    field: Box::new(stale),
                },
            },
            &source,
            FLOW_A,
            limits(),
        )
        .expect_err("stale"),
        MailMergeError::InvalidField
    );

    for document_lock in [false, true] {
        let mut value = draft();
        value.document_locked = document_lock;
        value.sections[0].locked = !document_lock;
        let protected = MailMergeDocumentState::from_draft(value, limits()).expect("state");
        let candidate = field(&protected.data_sources()[0], "field-1", "column-name", 1, 2);
        assert_eq!(
            MailMergeRequest::from_draft(
                MailMergeRequestDraft {
                    schema_version: MAIL_MERGE_SCHEMA_VERSION.to_owned(),
                    request_id: id("request-2"),
                    expected_source_state_sha256: protected
                        .canonical_sha256(limits())
                        .expect("digest"),
                    expected_document_flow_sha256: FLOW_A.to_owned(),
                    target_document_flow_sha256: FLOW_B.to_owned(),
                    operation: MailMergeOperation::FieldInsert {
                        insertion_index: 0,
                        field: Box::new(candidate),
                    },
                },
                &protected,
                FLOW_A,
                limits(),
            )
            .expect_err("protected"),
            MailMergeError::Protected
        );
    }
}

#[test]
fn request_plan_and_build_recheck_exact_state_and_document_flow() {
    let source = state();
    let candidate = field(&source.data_sources()[0], "field-1", "column-name", 1, 2);
    let request = request(&source, candidate);
    assert_eq!(
        MailMergeBuilder::plan(&source, &request, FLOW_C, limits()).expect_err("plan flow"),
        MailMergeError::DocumentFlowDrift
    );
    let plan = MailMergeBuilder::plan(&source, &request, FLOW_A, limits()).expect("plan");
    assert_eq!(
        MailMergeBuilder::build(&plan, &source, FLOW_C, limits()).expect_err("build flow"),
        MailMergeError::DocumentFlowDrift
    );
    let mut drifted: MailMergeDocumentStateDraft = source.clone().into();
    drifted.preview_inventory_sha256 = digest('0');
    let drifted = MailMergeDocumentState::from_draft(drifted, limits()).expect("drifted");
    assert_eq!(
        MailMergeBuilder::build(&plan, &drifted, FLOW_A, limits()).expect_err("state drift"),
        MailMergeError::SourceStateDrift
    );
}

#[test]
fn strict_json_rejects_duplicate_unknown_and_oversized_inputs() {
    let source = state();
    let candidate = field(&source.data_sources()[0], "field-1", "column-name", 1, 2);
    let draft = MailMergeRequestDraft {
        schema_version: MAIL_MERGE_SCHEMA_VERSION.to_owned(),
        request_id: id("request-1"),
        expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
        expected_document_flow_sha256: FLOW_A.to_owned(),
        target_document_flow_sha256: FLOW_B.to_owned(),
        operation: MailMergeOperation::FieldInsert {
            insertion_index: 0,
            field: Box::new(candidate),
        },
    };
    let mut value = serde_json::to_value(&draft).expect("json");
    value
        .as_object_mut()
        .expect("object")
        .insert("unknown".to_owned(), serde_json::json!(true));
    assert_eq!(
        MailMergeRequest::from_json(
            &serde_json::to_vec(&value).expect("bytes"),
            &source,
            FLOW_A,
            limits(),
        )
        .expect_err("unknown"),
        MailMergeError::InvalidJson
    );
    let encoded = serde_json::to_string(&draft).expect("json");
    let duplicate = encoded.replacen(
        '{',
        &format!("{{\"schema_version\":\"{MAIL_MERGE_SCHEMA_VERSION}\","),
        1,
    );
    assert_eq!(
        MailMergeRequest::from_json(duplicate.as_bytes(), &source, FLOW_A, limits())
            .expect_err("duplicate"),
        MailMergeError::InvalidJson
    );
    let tiny = MailMergeLimits::new(MailMergeLimitConfig {
        input_bytes: 8,
        output_bytes: 8,
        ..MailMergeLimitConfig::default()
    })
    .expect("tiny");
    assert_eq!(
        MailMergeRequest::from_json(encoded.as_bytes(), &source, FLOW_A, tiny)
            .expect_err("input limit"),
        MailMergeError::InputLimit
    );
}

#[test]
fn canonical_state_is_deterministic_and_debug_is_redacted() {
    let source = state();
    let bytes = source.canonical_json(limits()).expect("json");
    let decoded: MailMergeDocumentState = serde_json::from_slice(&bytes).expect("decode");
    assert_eq!(
        decoded.canonical_sha256(limits()).expect("digest"),
        source.canonical_sha256(limits()).expect("digest")
    );
    let candidate = field(
        &source.data_sources()[0],
        "secret-field",
        "column-name",
        1,
        2,
    );
    let text = format!("{source:?} {:?} {:?}", source.data_sources()[0], candidate);
    for secret in ["data-source-1", "column-name", "secret-field", FLOW_A] {
        assert!(!text.contains(secret));
    }
    assert_eq!(
        candidate.native_pair.field_type,
        MailMergeFieldType::Mailmerge
    );
    assert_eq!(
        candidate.native_pair.semantic_binding,
        MailMergeSemanticBinding::UnverifiedFieldParameters
    );
}

#[test]
fn zero_records_and_every_typed_column_privacy_class_are_valid() {
    let variants = [
        (MailMergeColumnType::Text, MailMergeSensitivity::NonPersonal),
        (
            MailMergeColumnType::Integer,
            MailMergeSensitivity::Pseudonymous,
        ),
        (
            MailMergeColumnType::FixedDecimal,
            MailMergeSensitivity::Personal,
        ),
        (MailMergeColumnType::Date, MailMergeSensitivity::Sensitive),
        (
            MailMergeColumnType::Boolean,
            MailMergeSensitivity::NonPersonal,
        ),
        (MailMergeColumnType::Opaque, MailMergeSensitivity::Sensitive),
    ];
    let mut value = draft();
    value.data_sources[0].record_count = 0;
    value.data_sources[0].columns = variants
        .into_iter()
        .enumerate()
        .map(|(index, (kind, sensitivity))| {
            column(
                &format!("column-{index}"),
                char::from_digit(u32::try_from(index).expect("index"), 16).expect("hex"),
                kind,
                sensitivity,
            )
        })
        .collect();
    assert_eq!(
        MailMergeDocumentState::from_draft(value, limits())
            .expect("zero-record schema")
            .data_sources()[0]
            .columns
            .len(),
        variants.len()
    );
}

#[test]
fn insert_never_exposes_generation_or_provider_fallback_capabilities() {
    let source = state();
    let operation = MailMergeOperation::FieldInsert {
        insertion_index: 0,
        field: Box::new(field(
            &source.data_sources()[0],
            "field-1",
            "column-name",
            1,
            2,
        )),
    };
    assert_eq!(operation.capability_id(), "ref.mailmerge_field");
    let json = serde_json::to_string(&operation).expect("json");
    assert!(!json.contains("mailmerge_generate"));
    assert!(!json.contains("desktop_automation"));
    assert!(!json.contains("row_values"));
    assert!(!json.contains("plaintext"));
}
