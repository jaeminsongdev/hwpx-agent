#![allow(clippy::expect_used)] // Synthetic bounded fixtures only.

use domain_ir::*;
use hwpx_agent_cli::reference_validation_product::*;
use serde_json::{Value, json};
use std::error::Error;

type TestResult = Result<(), Box<dyn Error>>;

fn digest(character: char) -> String {
    std::iter::repeat_n(character, 64).collect()
}

fn limits() -> Result<ReferenceAuxiliaryLimits, ReferenceAuxiliaryError> {
    ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig::default())
}

fn source(
    limits: ReferenceAuxiliaryLimits,
) -> Result<ReferenceAuxiliaryDocumentState, Box<dyn Error>> {
    let hash = digest('a');
    let draft = json!({
        "schema_version": REFERENCE_AUXILIARY_SCHEMA_VERSION,
        "sections": [{
            "section_id": "section-1",
            "paragraph_count": 1,
            "run_topology_sha256": hash,
            "inline_topology_sha256": digest('b'),
            "page_assignment_sha256": digest('c'),
            "opaque_section_state_sha256": digest('d'),
            "locked": false
        }],
        "caption_objects": [],
        "caption_sequences": [],
        "captions": [],
        "date_time_fields": [],
        "file_name_literals": [],
        "correction_marks": [],
        "data_link": null,
        "validation_targets": [],
        "validation_edges": [{
            "logical_reference_id": "reference-1",
            "source_node_id": "node-1",
            "expected_target_id": "missing-target",
            "expected_target_kind": "bookmark",
            "source_anchor": {
                "section_id": "section-1",
                "start": {"paragraph_ordinal": 0, "run_ordinal": 0, "inline_ordinal": 0},
                "end": {"paragraph_ordinal": 0, "run_ordinal": 0, "inline_ordinal": 0}
            },
            "cached_display_sha256": digest('e'),
            "cache_status": "current",
            "edge_state_sha256": digest('f')
        }],
        "occupied_non_aux_control_ids": [],
        "occupied_non_aux_field_ids": [],
        "non_auxiliary_content_sha256": digest('1'),
        "field_inventory_sha256": digest('2'),
        "form_inventory_sha256": digest('3'),
        "note_inventory_sha256": digest('4'),
        "comment_inventory_sha256": digest('5'),
        "link_inventory_sha256": digest('6'),
        "cross_reference_inventory_sha256": digest('7'),
        "toc_index_inventory_sha256": digest('8'),
        "citation_inventory_sha256": digest('9'),
        "mail_merge_inventory_sha256": digest('a'),
        "object_inventory_sha256": digest('b'),
        "numbering_inventory_sha256": digest('c'),
        "style_catalog_sha256": digest('d'),
        "relationship_inventory_sha256": digest('e'),
        "resource_inventory_sha256": digest('f'),
        "document_protection_sha256": digest('1'),
        "opaque_document_state_sha256": digest('2'),
        "document_locked": false
    });
    Ok(ReferenceAuxiliaryDocumentState::from_draft(
        serde_json::from_value(draft)?,
        limits,
    )?)
}

fn request_json(
    source: &ReferenceAuxiliaryDocumentState,
    flow_sha256: &str,
    limits: ReferenceAuxiliaryLimits,
) -> Result<Vec<u8>, Box<dyn Error>> {
    let source_sha256 = source.canonical_sha256(limits)?;
    let report_sha256 = source
        .validate_references(limits)?
        .canonical_sha256(limits)?;
    Ok(serde_json::to_vec(&json!({
        "schema_version": REFERENCE_AUXILIARY_SCHEMA_VERSION,
        "request_id": "request-1",
        "expected_source_state_sha256": source_sha256,
        "expected_document_flow_sha256": flow_sha256,
        "target_document_flow_sha256": flow_sha256,
        "operation": {
            "kind": "validate_references",
            "expected_report_sha256": report_sha256
        }
    }))?)
}

#[test]
fn executes_bound_read_only_validation_and_returns_deterministic_report() -> TestResult {
    let limits = limits()?;
    let source = source(limits)?;
    let flow_sha256 = digest('9');
    let request = request_json(&source, &flow_sha256, limits)?;
    let source_sha256 = source.canonical_sha256(limits)?;

    let result =
        ReferenceValidationProductOperation::execute_json(&source, &flow_sha256, &request, limits)?;
    assert_eq!(result.profile_id, REFERENCE_VALIDATION_PRODUCT_PROFILE_ID);
    assert_eq!(
        result.qualification,
        REFERENCE_VALIDATION_PRODUCT_QUALIFICATION
    );
    assert_eq!(
        result.domain_receipt.capability_id,
        "ref.reference_validate"
    );
    assert_eq!(result.domain_receipt.source_state_sha256, source_sha256);
    assert_eq!(result.domain_receipt.target_state_sha256, source_sha256);
    assert_eq!(result.report.checked_references, 1);
    assert_eq!(result.report.valid_references, 0);
    assert_eq!(result.report.issues.len(), 1);
    assert_eq!(
        result.report_sha256,
        result.report.canonical_sha256(limits)?
    );
    assert_eq!(
        result.domain_receipt.validation_report_sha256.as_deref(),
        Some(result.report_sha256.as_str())
    );
    assert!(!format!("{result:?}").contains("reference-1"));

    let output = result.canonical_json(limits)?;
    let output: Value = serde_json::from_slice(&output)?;
    assert_eq!(output["report"]["checked_references"], 1);
    assert_eq!(output["report"]["issues"][0]["kind"], "missing_target");
    Ok(())
}

#[test]
fn rejects_mutating_capabilities_before_domain_execution() -> TestResult {
    let limits = limits()?;
    let source = source(limits)?;
    let flow_sha256 = digest('9');
    let valid = request_json(&source, &flow_sha256, limits)?;
    let mut request: Value = serde_json::from_slice(&valid)?;
    request["operation"]["kind"] = json!("set_caption_state");
    let request = serde_json::to_vec(&request)?;

    assert_eq!(
        ReferenceValidationProductOperation::execute_json(&source, &flow_sha256, &request, limits,),
        Err(ReferenceValidationProductError::UnsupportedCapability)
    );
    Ok(())
}

#[test]
fn malformed_capability_envelope_is_not_misclassified_as_unsupported() -> TestResult {
    let limits = limits()?;
    let source = source(limits)?;
    let flow_sha256 = digest('9');

    assert_eq!(
        ReferenceValidationProductOperation::execute_json(
            &source,
            &flow_sha256,
            br#"{"schema_version":"hwpx-agent.reference-auxiliary/v1"}"#,
            limits,
        ),
        Err(ReferenceValidationProductError::Request)
    );
    Ok(())
}

#[test]
fn duplicate_keys_still_fail_closed_in_domain_parser() -> TestResult {
    let limits = limits()?;
    let source = source(limits)?;
    let flow_sha256 = digest('9');
    let valid = String::from_utf8(request_json(&source, &flow_sha256, limits)?)?;
    let duplicate = valid.replace(
        "\"kind\":\"validate_references\"",
        "\"kind\":\"validate_references\",\"kind\":\"validate_references\"",
    );
    assert_ne!(duplicate, valid);

    assert_eq!(
        ReferenceValidationProductOperation::execute_json(
            &source,
            &flow_sha256,
            duplicate.as_bytes(),
            limits,
        ),
        Err(ReferenceValidationProductError::Request)
    );
    Ok(())
}

mod auxiliary_preparation_tests {
    use super::*;
    use sha2::{Digest as _, Sha256};

    fn id(value: &str) -> Result<LogicalId, Box<dyn Error>> { Ok(LogicalId::parse(value)?) }
    fn sha(value: &str) -> String { hex::encode(Sha256::digest(value.as_bytes())) }
    fn anchor() -> Result<LinkAnchor, Box<dyn Error>> {
        let point = LinkPoint { paragraph_ordinal: 0, run_ordinal: 0, inline_ordinal: 0 };
        Ok(LinkAnchor { section_id: id("section-1")?, start: point, end: point })
    }
    fn full_state(limits: ReferenceAuxiliaryLimits) -> Result<ReferenceAuxiliaryDocumentState, Box<dyn Error>> {
        let mut draft: ReferenceAuxiliaryDocumentStateDraft = source(limits)?.into();
        draft.caption_objects.push(CaptionObjectTarget {
            logical_object_id: id("caption-object")?, object_kind: CaptionObjectKind::Picture,
            section_id: id("section-1")?, object_state_sha256: digest('a'), locked: false,
        });
        let mut field = DateTimeFieldNode {
            logical_field_id: id("date-field")?, anchor: anchor()?, begin_control_id: 101, field_id: 201,
            end_begin_control_id_ref: 101, end_field_id: 201, native_field_type: NativeDateFieldType::DocDate,
            format: DateTimeFormatDefinition { pattern: "yyyy-MM-dd".into(), locale: "ko-KR".into(),
                timezone_offset_minutes: 540, calendar: DateTimeCalendar::Gregorian },
            cache: DateTimeFieldCache { format_projection_sha256: digest('a'), display_text_sha256: digest('b'),
                status: AuxiliaryCacheStatus::Current },
            native_parameters_sha256: digest('c'), opaque_field_state_sha256: digest('d'),
            opaque_properties: Vec::new(), locked: false,
        };
        field.cache.format_projection_sha256 = field.format_projection_sha256(limits)?;
        draft.date_time_fields.push(field);
        draft.data_link = Some(DataLinkState {
            logical_link_id: id("private-link")?, logical_artifact_id: id("private-artifact")?,
            encrypted_artifact_sha256: digest('a'), encryption_envelope_sha256: digest('b'),
            allowlisted_location_sha256: digest('c'), source_revision_sha256: digest('d'),
            relationship_state_sha256: digest('e'), inheritance: DataLinkInheritance::Page,
            availability: DataLinkAvailability::Available, artifact_protection: DataLinkArtifactProtection::Encrypted,
            opaque_native_state_sha256: digest('f'), opaque_properties: Vec::new(), locked: false,
        });
        Ok(ReferenceAuxiliaryDocumentState::from_draft(draft, limits)?)
    }
    fn context<'a>(state: &'a ReferenceAuxiliaryDocumentState, flow: &'a str)
        -> Result<ReferenceAuxiliaryProductContext<'a>, Box<dyn Error>> {
        Ok(ReferenceAuxiliaryProductContext::new(state, DocumentId::parse("private-document")?,
            RevisionId::parse("revision-1")?, [2; 32], flow))
    }
    fn literal() -> Result<FileNameLiteralNode, Box<dyn Error>> {
        Ok(FileNameLiteralNode {
            logical_literal_id: id("private-literal")?, anchor: anchor()?, literal: "private.hwpx".into(),
            source_leaf_name_sha256: sha("private.hwpx"), source_revision_sha256: digest('a'),
            include_extension: true, character_style_sha256: digest('b'), paragraph_style_sha256: digest('c'),
            opaque_text_state_sha256: digest('d'), opaque_properties: Vec::new(), locked: false,
        })
    }
    fn mark(kind: CorrectionMarkKind) -> Result<CorrectionMarkNode, Box<dyn Error>> {
        Ok(CorrectionMarkNode {
            logical_mark_id: id("private-mark")?, anchor: anchor()?, kind,
            begin_control_id: 301, field_id: 401, end_begin_control_id_ref: 301, end_field_id: 401,
            author_identity_sha256: digest('a'), created_at_epoch_millis: 1_788_796_800_000,
            mark_content_sha256: digest('b'), native_parameters_sha256: digest('c'),
            opaque_field_state_sha256: digest('d'), opaque_properties: Vec::new(), locked: false,
        })
    }
    fn operations(state: &ReferenceAuxiliaryDocumentState, limits: ReferenceAuxiliaryLimits)
        -> Result<Vec<ReferenceAuxiliaryOperation>, Box<dyn Error>> {
        let draft: ReferenceAuxiliaryDocumentStateDraft = state.clone().into();
        let object = &draft.caption_objects[0];
        let sequence = CaptionSequenceDefinition {
            logical_sequence_id: id("private-sequence")?, object_kind: CaptionObjectKind::Picture,
            label: "private-caption".into(), separator: " ".into(), number_format: CaptionNumberFormat::Decimal,
            restart_policy: CaptionRestartPolicy::Continuous, start_at: 1,
            number_style_sha256: digest('a'), opaque_properties: Vec::new(), locked: false,
        };
        let mut caption = CaptionBinding {
            logical_caption_id: id("private-caption")?, logical_object_id: object.logical_object_id.clone(),
            logical_sequence_id: sequence.logical_sequence_id.clone(), document_order: 0,
            caption_content_sha256: digest('b'),
            cache: CaptionSequenceCache { sequence_projection_sha256: digest('a'), rendered_number_sha256: sha("1"),
                resolved_number: 1, status: AuxiliaryCacheStatus::Current },
            native_envelope: CaptionNativeEnvelope { side: NativeCaptionSide::Bottom, full_size: false,
                width_hwpunit: -1, gap_hwpunit: 850, last_width_hwpunit: 0,
                sub_list_sha256: digest('c'), opaque_native_state_sha256: digest('d'),
                semantic_binding: CaptionNativeSemanticBinding::UnverifiedSubListNumbering },
            opaque_properties: Vec::new(), locked: false,
        };
        caption.cache.sequence_projection_sha256 = CaptionBinding::projection_sha256(&sequence, object, &caption, 1, limits)?;
        Ok(vec![
            ReferenceAuxiliaryOperation::SetCaptionState { caption_sequences: vec![sequence], captions: vec![caption] },
            ReferenceAuxiliaryOperation::SetDateTimeFormat { logical_field_id: id("date-field")?,
                format: DateTimeFormatDefinition { pattern: "yyyyMMdd".into(), locale: "ko-KR".into(),
                    timezone_offset_minutes: 540, calendar: DateTimeCalendar::Gregorian } },
            ReferenceAuxiliaryOperation::InsertFileNameLiteral { insertion_index: 0, literal: Box::new(literal()?) },
            ReferenceAuxiliaryOperation::InsertCorrectionMark { insertion_index: 0, mark: Box::new(mark(CorrectionMarkKind::Change)?) },
            ReferenceAuxiliaryOperation::SetDataLink { data_link: None },
            ReferenceAuxiliaryOperation::ValidateReferences { expected_report_sha256: state.validate_references(limits)?.canonical_sha256(limits)? },
        ])
    }
    fn operation_json(state: &ReferenceAuxiliaryDocumentState, flow: &str,
        operation: ReferenceAuxiliaryOperation, limits: ReferenceAuxiliaryLimits) -> Result<Vec<u8>, Box<dyn Error>> {
        Ok(serde_json::to_vec(&ReferenceAuxiliaryRequestDraft {
            schema_version: REFERENCE_AUXILIARY_SCHEMA_VERSION.into(), request_id: id("private-request")?,
            expected_source_state_sha256: state.canonical_sha256(limits)?,
            expected_document_flow_sha256: flow.into(), target_document_flow_sha256: flow.into(), operation,
        })?)
    }

    #[test]
    fn all_six_typed_operations_match_original_builder_without_changing_read_only_route() -> TestResult {
        let limits = limits()?; let state = full_state(limits)?; let flow = digest('9');
        let context = context(&state, &flow)?;
        let original = state.canonical_json(limits)?;
        for operation in operations(&state, limits)? {
            let capability = operation.capability_id();
            let json = operation_json(&state, &flow, operation, limits)?;
            let request = ReferenceAuxiliaryRequest::from_json(&json, &state, &flow, limits)?;
            let plan = ReferenceAuxiliaryBuilder::plan(&state, &request, &flow, limits)?;
            let expected = ReferenceAuxiliaryBuilder::build(&plan, &state, &flow, limits)?;
            let prepared = ReferenceAuxiliaryProductPreparation::prepare_json(&context, &json, limits)?;
            assert_eq!(prepared.target_state(), &expected.state);
            assert_eq!(prepared.receipt().domain_receipt(), &expected.receipt);
            assert_eq!(prepared.verify(&context, limits)?, *prepared.receipt());
            assert_eq!(prepared.require_current_product_route(&context, limits),
                Err(ReferenceAuxiliaryProductPreparationError::RouteUnqualified));
            let receipt: Value = serde_json::from_slice(&prepared.receipt().canonical_json(limits)?)?;
            assert_eq!(receipt["profile"], REFERENCE_AUXILIARY_PREPARATION_PROFILE);
            assert_eq!(receipt["qualification"], REFERENCE_AUXILIARY_PREPARATION_QUALIFICATION);
            assert_eq!(receipt["request_sha256"], hex::encode(Sha256::digest(&json)));
            assert_eq!(receipt["original_domain_plan_sha256"], hex::encode(Sha256::digest(serde_json::to_vec(&plan)?)));
            for flag in ["source_completeness_verified", "target_document_flow_verified", "hwpx_lowered",
                "execution_authority_verified", "external_data_access_verified"] { assert_eq!(receipt[flag], false); }
            if capability != "ref.reference_validate" {
                assert_eq!(ReferenceValidationProductOperation::execute_json(&state, &flow, &json, limits),
                    Err(ReferenceValidationProductError::UnsupportedCapability));
            }
        }
        assert!(state.canonical_json(limits)? == original);
        Ok(())
    }

    #[test]
    fn prepared_identity_state_flow_and_limit_drift_are_rejected() -> TestResult {
        let limits = limits()?; let state = full_state(limits)?; let flow = digest('9');
        let base = context(&state, &flow)?;
        let json = operation_json(&state, &flow, ReferenceAuxiliaryOperation::InsertFileNameLiteral {
            insertion_index: 0, literal: Box::new(literal()?) }, limits)?;
        let prepared = ReferenceAuxiliaryProductPreparation::prepare_json(&base, &json, limits)?;
        for (document, revision, package) in [("other-document", "revision-1", [2; 32]),
            ("private-document", "revision-2", [2; 32]), ("private-document", "revision-1", [3; 32])] {
            let changed = ReferenceAuxiliaryProductContext::new(&state, DocumentId::parse(document)?,
                RevisionId::parse(revision)?, package, &flow);
            assert_eq!(prepared.verify(&changed, limits), Err(ReferenceAuxiliaryProductPreparationError::Binding));
        }
        let other_flow = digest('8'); let changed = context(&state, &other_flow)?;
        assert!(matches!(prepared.verify(&changed, limits),
            Err(ReferenceAuxiliaryProductPreparationError::Domain(ReferenceAuxiliaryError::DocumentFlowDrift))));
        let mut draft: ReferenceAuxiliaryDocumentStateDraft = state.clone().into();
        draft.non_auxiliary_content_sha256 = digest('9');
        let changed_state = ReferenceAuxiliaryDocumentState::from_draft(draft, limits)?;
        assert!(matches!(prepared.verify(&context(&changed_state, &flow)?, limits),
            Err(ReferenceAuxiliaryProductPreparationError::Domain(ReferenceAuxiliaryError::SourceStateDrift))));
        let tighter = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig { text_bytes: 100, ..Default::default() })?;
        assert_eq!(prepared.verify(&base, tighter), Err(ReferenceAuxiliaryProductPreparationError::Binding));
        Ok(())
    }

    #[test]
    fn preparation_strict_json_does_not_accept_duplicate_unknown_or_raw_action_fields() -> TestResult {
        let limits = limits()?; let state = full_state(limits)?; let flow = digest('9');
        let context = context(&state, &flow)?;
        let json = operation_json(&state, &flow, ReferenceAuxiliaryOperation::InsertFileNameLiteral {
            insertion_index: 0, literal: Box::new(literal()?) }, limits)?;
        let text = String::from_utf8(json.clone())?;
        let duplicate = text.replacen("\"kind\":", "\"kind\":\"insert_file_name_literal\",\"kind\":", 1);
        assert_ne!(duplicate, text);
        assert!(ReferenceAuxiliaryProductPreparation::prepare_json(&context, duplicate.as_bytes(), limits).is_err());
        for fault in ["unknown", "raw-action"] {
            let mut value: Value = serde_json::from_slice(&json)?;
            if fault == "unknown" { value["unexpected"] = json!(true); }
            else { value["operation"]["kind"] = json!("run_native_action"); }
            assert!(ReferenceAuxiliaryProductPreparation::prepare_json(&context, &serde_json::to_vec(&value)?, limits).is_err());
        }
        Ok(())
    }

    #[test]
    fn preparation_preserves_date_cache_and_unrelated_inventories() -> TestResult {
        let limits = limits()?; let state = full_state(limits)?; let flow = digest('9');
        let operation = operations(&state, limits)?.remove(1);
        let json = operation_json(&state, &flow, operation, limits)?;
        let prepared = ReferenceAuxiliaryProductPreparation::prepare_json(&context(&state, &flow)?, &json, limits)?;
        let target = prepared.target_state();
        assert_eq!(target.date_time_fields()[0].format.pattern, "yyyyMMdd");
        assert_eq!(target.date_time_fields()[0].cache.status, AuxiliaryCacheStatus::Stale);
        assert_eq!(target.date_time_fields()[0].cache.display_text_sha256, state.date_time_fields()[0].cache.display_text_sha256);
        let mut source_value = serde_json::to_value(&state)?;
        let mut target_value = serde_json::to_value(target)?;
        source_value.as_object_mut().ok_or("source")?.remove("date_time_fields");
        target_value.as_object_mut().ok_or("target")?.remove("date_time_fields");
        assert_eq!(source_value, target_value);
        Ok(())
    }

    #[test]
    fn preparation_cannot_bypass_document_locks_caption_cache_or_expected_report() -> TestResult {
        let limits = limits()?; let state = full_state(limits)?; let flow = digest('9');
        let mut draft: ReferenceAuxiliaryDocumentStateDraft = state.clone().into(); draft.document_locked = true;
        let locked = ReferenceAuxiliaryDocumentState::from_draft(draft, limits)?;
        for operation in operations(&locked, limits)?.into_iter().take(5) {
            let json = operation_json(&locked, &flow, operation, limits)?;
            assert!(matches!(ReferenceAuxiliaryProductPreparation::prepare_json(&context(&locked, &flow)?, &json, limits),
                Err(ReferenceAuxiliaryProductPreparationError::Domain(ReferenceAuxiliaryError::Protected))));
        }
        let mut operation = operations(&state, limits)?.remove(0);
        if let ReferenceAuxiliaryOperation::SetCaptionState { captions, .. } = &mut operation {
            captions[0].cache.sequence_projection_sha256 = digest('9');
        }
        let json = operation_json(&state, &flow, operation, limits)?;
        assert!(ReferenceAuxiliaryProductPreparation::prepare_json(&context(&state, &flow)?, &json, limits).is_err());
        let bad = operation_json(&state, &flow, ReferenceAuxiliaryOperation::ValidateReferences {
            expected_report_sha256: digest('0') }, limits)?;
        assert!(matches!(ReferenceAuxiliaryProductPreparation::prepare_json(&context(&state, &flow)?, &bad, limits),
            Err(ReferenceAuxiliaryProductPreparationError::Domain(ReferenceAuxiliaryError::ValidationReportDrift))));
        Ok(())
    }

    #[test]
    fn preparation_receipt_budget_and_debug_do_not_expose_caller_payloads() -> TestResult {
        let limits = limits()?; let state = full_state(limits)?; let flow = digest('9');
        let context = context(&state, &flow)?;
        let json = operation_json(&state, &flow, ReferenceAuxiliaryOperation::InsertFileNameLiteral {
            insertion_index: 0, literal: Box::new(literal()?) }, limits)?;
        let prepared = ReferenceAuxiliaryProductPreparation::prepare_json(&context, &json, limits)?;
        let bytes = prepared.receipt().canonical_json(limits)?;
        let exact = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig { input_bytes: 1,
            output_bytes: bytes.len(), ..Default::default() })?;
        assert!(prepared.receipt().canonical_json(exact)? == bytes);
        let small = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig { input_bytes: 1,
            output_bytes: bytes.len() - 1, ..Default::default() })?;
        assert_eq!(prepared.receipt().canonical_json(small), Err(ReferenceAuxiliaryProductPreparationError::OutputLimit));
        assert!(matches!(ReferenceAuxiliaryProductPreparation::prepare_json(&context, &json, small),
            Err(ReferenceAuxiliaryProductPreparationError::InputLimit)));
        let text = format!("{prepared:?} {:?} {context:?} {}", prepared.receipt(), String::from_utf8(bytes)?);
        for private in ["private.hwpx", "private-document", "private-literal", "revision-1"] {
            assert!(!text.contains(private));
        }
        Ok(())
    }

    #[test]
    fn preparation_supports_all_nineteen_correction_kinds_without_native_execution() -> TestResult {
        let limits = limits()?; let state = full_state(limits)?; let flow = digest('9');
        let context = context(&state, &flow)?;
        let kinds = [CorrectionMarkKind::Change, CorrectionMarkKind::Sign, CorrectionMarkKind::Delete,
            CorrectionMarkKind::Attach, CorrectionMarkKind::Clipping, CorrectionMarkKind::Sawtooth,
            CorrectionMarkKind::Thinking, CorrectionMarkKind::Praise, CorrectionMarkKind::Line,
            CorrectionMarkKind::SimpleChange, CorrectionMarkKind::Hyperlink, CorrectionMarkKind::LineAttach,
            CorrectionMarkKind::LineLink, CorrectionMarkKind::LineTransfer, CorrectionMarkKind::RightMove,
            CorrectionMarkKind::LeftMove, CorrectionMarkKind::Transfer, CorrectionMarkKind::Split, CorrectionMarkKind::SimpleInsert];
        assert_eq!(kinds.len(), 19);
        for kind in kinds {
            let json = operation_json(&state, &flow, ReferenceAuxiliaryOperation::InsertCorrectionMark {
                insertion_index: 0, mark: Box::new(mark(kind)?) }, limits)?;
            let prepared = ReferenceAuxiliaryProductPreparation::prepare_json(&context, &json, limits)?;
            assert_eq!(prepared.target_state().correction_marks()[0].kind, kind);
            assert_eq!(prepared.receipt().domain_receipt().capability_id, "ref.correction_mark");
            assert_eq!(prepared.require_current_product_route(&context, limits), Err(ReferenceAuxiliaryProductPreparationError::RouteUnqualified));
        }
        Ok(())
    }

    #[test]
    fn all_six_typed_preparation_read_only_flow_rejects_mutation() -> TestResult {
        let limits = limits()?; let state = full_state(limits)?; let flow = digest('9');
        let context = context(&state, &flow)?;
        let operation = ReferenceAuxiliaryOperation::ValidateReferences {
            expected_report_sha256: state.validate_references(limits)?.canonical_sha256(limits)?,
        };
        let json = operation_json(&state, &flow, operation, limits)?;
        let mut value: Value = serde_json::from_slice(&json)?;
        value["target_document_flow_sha256"] = json!(digest('8'));
        let changed = serde_json::to_vec(&value)?;
        assert!(matches!(ReferenceAuxiliaryProductPreparation::prepare_json(&context, &changed, limits),
            Err(ReferenceAuxiliaryProductPreparationError::Binding)));
        assert_eq!(ReferenceValidationProductOperation::execute_json(&state, &flow, &changed, limits),
            Err(ReferenceValidationProductError::Binding));
        Ok(())
    }

    #[test]
    fn declared_target_flow_is_bound_but_never_marked_observed() -> TestResult {
        let limits = limits()?; let state = full_state(limits)?; let flow = digest('9');
        let context = context(&state, &flow)?;
        let json = operation_json(&state, &flow, ReferenceAuxiliaryOperation::InsertFileNameLiteral {
            insertion_index: 0, literal: Box::new(literal()?) }, limits)?;
        let mut value: Value = serde_json::from_slice(&json)?;
        value["target_document_flow_sha256"] = json!(digest('8'));
        let prepared = ReferenceAuxiliaryProductPreparation::prepare_json(&context, &serde_json::to_vec(&value)?, limits)?;
        assert_eq!(prepared.receipt().domain_receipt().source_document_flow_sha256, flow);
        assert_eq!(prepared.receipt().domain_receipt().target_document_flow_sha256, digest('8'));
        let receipt: Value = serde_json::from_slice(&prepared.receipt().canonical_json(limits)?)?;
        assert_eq!(receipt["target_document_flow_verified"], false);
        value["target_document_flow_sha256"] = json!(digest('7'));
        let other = ReferenceAuxiliaryProductPreparation::prepare_json(&context, &serde_json::to_vec(&value)?, limits)?;
        assert_eq!(prepared.target_state(), other.target_state());
        assert_ne!(prepared.receipt(), other.receipt());
        assert_eq!(prepared.require_current_product_route(&context, limits),
            Err(ReferenceAuxiliaryProductPreparationError::RouteUnqualified));
        Ok(())
    }

    #[test]
    fn preparation_binds_all_data_link_inheritance_and_availability_without_accessing_sources() -> TestResult {
        let limits = limits()?; let state = full_state(limits)?; let flow = digest('9');
        let context = context(&state, &flow)?;
        for inheritance in [DataLinkInheritance::None, DataLinkInheritance::Page,
            DataLinkInheritance::Footnote, DataLinkInheritance::PageAndFootnote] {
            for availability in [DataLinkAvailability::Available, DataLinkAvailability::Unavailable] {
                let mut link = state.data_link().ok_or("link")?.clone();
                link.logical_link_id = id("private-new-link")?;
                link.inheritance = inheritance; link.availability = availability;
                let json = operation_json(&state, &flow, ReferenceAuxiliaryOperation::SetDataLink {
                    data_link: Some(Box::new(link.clone())) }, limits)?;
                let prepared = ReferenceAuxiliaryProductPreparation::prepare_json(&context, &json, limits)?;
                assert_eq!(prepared.target_state().data_link(), Some(&link));
                let value: Value = serde_json::from_slice(&prepared.receipt().canonical_json(limits)?)?;
                assert_eq!(value["external_data_access_verified"], false);
                assert_eq!(value["execution_authority_verified"], false);
            }
        }
        Ok(())
    }
}

#[path = "../../hwpx-package/tests/support/document_import_field_fixture.rs"]
#[allow(dead_code)]
mod file_literal_fixture;

mod file_literal_product_candidates {
    use super::*;
    use sha2::{Digest as _, Sha256};
    use hwpx_package::{WriterLimits, document_import::{ImportedSourcePackage, SourceImportLimits, structure::ImportedDocumentStructure}};
    use super::file_literal_fixture as fixture;

    const FLOW: &str = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";
    fn setup() -> Result<(Vec<u8>, ImportedDocumentStructure, ReferenceAuxiliaryDocumentState, FileNameLiteralNode), Box<dyn Error>> {
        let bytes = fixture::package("<hp:p id='1'><hp:run><hp:t>original</hp:t></hp:run></hp:p>")?;
        let package = ImportedSourcePackage::import(&bytes, DocumentId::parse("file-product")?, Sha256::digest(&bytes).into(), SourceImportLimits::default())?;
        let actual = ImportedDocumentStructure::import(package)?;
        // Deliberately caller-owned synthetic state. Actual source section/point
        // binding does not authenticate all these other inventories or styles.
        let mut draft: ReferenceAuxiliaryDocumentStateDraft = source(limits()?)?.into();
        draft.sections[0].section_id = actual.graph().sections()[0].section_id.clone();
        draft.validation_edges.clear();
        let state = ReferenceAuxiliaryDocumentState::from_draft(draft, limits()?)?;
        let point = LinkPoint { paragraph_ordinal: 0, run_ordinal: 0, inline_ordinal: 1 };
        let literal = FileNameLiteralNode {
            logical_literal_id: LogicalId::parse("private-file-literal")?,
            anchor: LinkAnchor { section_id: actual.graph().sections()[0].section_id.clone(), start: point, end: point },
            literal: "한글&frozen.hwpx".into(), source_leaf_name_sha256: hex::encode(Sha256::digest("한글&frozen.hwpx".as_bytes())),
            source_revision_sha256: hex::encode(Sha256::digest(b"revision-file-one")), include_extension: true,
            character_style_sha256: digest('a'), paragraph_style_sha256: digest('b'), opaque_text_state_sha256: digest('c'),
            opaque_properties: Vec::new(), locked: false,
        };
        Ok((bytes, actual, state, literal))
    }
    fn context<'a>(state: &'a ReferenceAuxiliaryDocumentState, bytes: &[u8]) -> Result<ReferenceAuxiliaryProductContext<'a>, Box<dyn Error>> {
        Ok(ReferenceAuxiliaryProductContext::new(state, DocumentId::parse("file-product")?, RevisionId::parse("revision-file-one")?, Sha256::digest(bytes).into(), FLOW))
    }
    fn prepare(state: &ReferenceAuxiliaryDocumentState, bytes: &[u8], operation: ReferenceAuxiliaryOperation) -> Result<PreparedReferenceAuxiliaryProductOperation, Box<dyn Error>> {
        let request = serde_json::to_vec(&ReferenceAuxiliaryRequestDraft {
            schema_version: REFERENCE_AUXILIARY_SCHEMA_VERSION.into(), request_id: LogicalId::parse("file-request")?,
            expected_source_state_sha256: state.canonical_sha256(limits()?)?, expected_document_flow_sha256: FLOW.into(),
            target_document_flow_sha256: FLOW.into(), operation,
        })?;
        Ok(ReferenceAuxiliaryProductPreparation::prepare_json(&context(state, bytes)?, &request, limits()?)?)
    }
    #[test]
    fn source_file_literal_prepared_product_generates_verified_package_but_never_promotes_route() -> TestResult {
        let (bytes, actual, state, literal) = setup()?;
        let original = state.clone();
        let prepared = prepare(&state, &bytes, ReferenceAuxiliaryOperation::InsertFileNameLiteral { insertion_index: 0, literal: Box::new(literal) })?;
        let ctx = context(&state, &bytes)?;
        let output = prepared.lower_file_name_literal_candidate(&ctx, &actual, &bytes, limits()?, WriterLimits::default())?;
        assert_eq!(output.preparation_receipt(), prepared.receipt());
        let receipt: Value = serde_json::from_slice(&output.preparation_receipt().canonical_json(limits()?)?)?;
        for flag in ["source_completeness_verified", "target_document_flow_verified", "hwpx_lowered", "execution_authority_verified", "external_data_access_verified"] {
            assert_eq!(receipt[flag], false);
        }
        let after = output.with_verified_bytes(<[u8]>::to_vec)?;
        assert_ne!(after, bytes);
        assert_eq!(Sha256::digest(&after).as_slice(), output.output_receipt().output_package_sha256);
        assert!(output.output_receipt().outside_selected_run_exact);
        assert!(output.output_receipt().source_style_attributes_preserved);
        assert!(!output.output_receipt().complete_auxiliary_state_verified);
        assert!(!format!("{output:?}").contains("한글"));
        assert!(matches!(prepared.require_current_product_route(&ctx, limits()?), Err(ReferenceAuxiliaryProductPreparationError::RouteUnqualified)));
        assert_eq!(state, original);
        assert_eq!(actual.verify_source(&bytes)?, *actual.receipt());
        Ok(())
    }
    #[test]
    fn source_file_literal_prepared_product_rejects_source_revision_fresh_drift_and_unrepresented_range() -> TestResult {
        let (bytes, actual, state, literal) = setup()?;
        let prepared = prepare(&state, &bytes, ReferenceAuxiliaryOperation::InsertFileNameLiteral { insertion_index: 0, literal: Box::new(literal.clone()) })?;
        let ctx = context(&state, &bytes)?;
        let foreign = ImportedDocumentStructure::import(ImportedSourcePackage::import(&bytes, DocumentId::parse("foreign-document")?, Sha256::digest(&bytes).into(), SourceImportLimits::default())?)?;
        assert!(matches!(prepared.lower_file_name_literal_candidate(&ctx, &foreign, &bytes, limits()?, WriterLimits::default()), Err(ReferenceFileLiteralCandidateError::Binding)));
        let changed = fixture::package("<hp:p id='1'><hp:run><hp:t>changed</hp:t></hp:run></hp:p>")?;
        assert!(matches!(prepared.lower_file_name_literal_candidate(&ctx, &actual, &changed, limits()?, WriterLimits::default()), Err(ReferenceFileLiteralCandidateError::Lowering)));
        let mut wrong_revision = literal.clone(); wrong_revision.source_revision_sha256 = digest('a');
        let prepared = prepare(&state, &bytes, ReferenceAuxiliaryOperation::InsertFileNameLiteral { insertion_index: 0, literal: Box::new(wrong_revision) })?;
        assert!(matches!(prepared.lower_file_name_literal_candidate(&ctx, &actual, &bytes, limits()?, WriterLimits::default()), Err(ReferenceFileLiteralCandidateError::Binding)));
        let mut range = literal; range.anchor.end.inline_ordinal += 1;
        let prepared = prepare(&state, &bytes, ReferenceAuxiliaryOperation::InsertFileNameLiteral { insertion_index: 0, literal: Box::new(range) })?;
        assert!(matches!(prepared.lower_file_name_literal_candidate(&ctx, &actual, &bytes, limits()?, WriterLimits::default()), Err(ReferenceFileLiteralCandidateError::NotRepresentable)));
        Ok(())
    }
    #[test]
    fn source_file_literal_prepared_product_cannot_lower_read_only_validation_or_rebind_limits() -> TestResult {
        let (bytes, actual, state, _) = setup()?;
        let prepared = prepare(&state, &bytes, ReferenceAuxiliaryOperation::ValidateReferences {
            expected_report_sha256: state.validate_references(limits()?)?.canonical_sha256(limits()?)?,
        })?;
        let ctx = context(&state, &bytes)?;
        assert!(matches!(prepared.lower_file_name_literal_candidate(&ctx, &actual, &bytes, limits()?, WriterLimits::default()), Err(ReferenceFileLiteralCandidateError::NotRepresentable)));
        let changed = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig { text_bytes: 1, ..Default::default() })?;
        assert!(matches!(prepared.lower_file_name_literal_candidate(&ctx, &actual, &bytes, changed, WriterLimits::default()), Err(ReferenceFileLiteralCandidateError::Preparation(ReferenceAuxiliaryProductPreparationError::Binding))));
        Ok(())
    }
}

mod stored_file_literal_candidates {
    use super::*;
    use artifact_service::*;
    use artifact_service::ArtifactId as StoredArtifactId;
    use hwpx_agent_cli::form_stored_provider::{StoredFormProvider, file_literal::*};
    use hwpx_package::{WriterLimits, document_import::{ImportedSourcePackage, SourceImportLimits, structure::ImportedDocumentStructure}};
    use revision_service as rev;
    use sha2::{Digest as _, Sha256};
    use std::{cell::Cell, collections::BTreeSet, sync::{Arc, atomic::{AtomicBool, Ordering}}};
    use super::file_literal_fixture as fixture;

    // TEST ONLY: isolated service repositories, a declared fixture scanner and
    // synthetic encryption material. No live issuer/scanner/native qualification.
    #[derive(Debug)]
    struct Scanner;
    impl ArtifactScanner for Scanner {
        fn scan(&self, _: ScanRequest<'_>) -> Result<ScanEvidence, ArtifactError> {
            Ok(ScanEvidence { engine: ScannerReference::parse("literal.fixture-scanner")?,
                signature_version: ScannerSignatureVersion::parse("fixture-only")?, verdict: ScanVerdict::Clean })
        }
    }
    #[derive(Clone,Debug,Default)]
    struct Blob { inner: InMemoryBlobStore, tamper: Arc<AtomicBool> }
    impl EncryptedBlobStore for Blob {
        fn put_if_absent(&self, key: &ObjectKey, bytes: &[u8]) -> Result<(),ArtifactError> { self.inner.put_if_absent(key, bytes) }
        fn get(&self, key: &ObjectKey) -> Result<Option<Vec<u8>>,ArtifactError> {
            let mut bytes = self.inner.get(key)?;
            if self.tamper.load(Ordering::SeqCst) && let Some(first) = bytes.as_mut().and_then(|b| b.first_mut()) { *first ^= 1; }
            Ok(bytes)
        }
        fn relocate_if_absent(&self, from: &ObjectKey, to: &ObjectKey) -> Result<(),ArtifactError> { self.inner.relocate_if_absent(from,to) }
    }
    type Store = ArtifactService<InMemoryMetadataRepository,Blob,Scanner>;
    type Provider<'a> = StoredFormProvider<'a,InMemoryMetadataRepository,Blob,Scanner,rev::InMemoryRevisionRepository>;
    struct Rig {
        store: Store, metadata: InMemoryMetadataRepository, blob: Blob,
        revisions: rev::RevisionService<rev::InMemoryRevisionRepository>, owner: RequestContext, reader: RequestContext,
        revision_context: rev::RevisionRequestContext, project: rev::ProjectId, branch: rev::BranchId,
        result: StoredArtifactId, head: rev::RevisionHead, bytes: Vec<u8>,
    }
    impl Rig {
        fn new() -> Result<Self,Box<dyn Error>> {
            let bytes = fixture::package("<hp:p id='1'><hp:run><hp:t>private original content</hp:t></hp:run></hp:p>")?;
            let tenant = TenantId::new(uuid::Uuid::from_u128(9081))?;
            let owner = RequestContext::new(tenant, SubjectDigest::from_authenticated_subject("literal fixture owner")?,
                [AuthScope::DocumentRead,AuthScope::DocumentWrite,AuthScope::ArtifactShare,AuthScope::SecurityModify]);
            let reader = RequestContext::new(tenant, SubjectDigest::from_authenticated_subject("literal fixture reader")?, [AuthScope::DocumentRead]);
            let revision_context = rev::RevisionRequestContext::new(tenant,reader.subject());
            let metadata = InMemoryMetadataRepository::default(); let blob = Blob::default();
            let key = KeyReference::parse("literal.fixture-aead")?;
            let ring = Aes256GcmKeyring::new(key.clone(), [(key,[83;32])])?;
            let signer = DownloadSigner::new("https://fixture.example.test/literal",KeyReference::parse("literal.fixture-hmac")?, &[84;32],60)?;
            let store = ArtifactService::new(metadata.clone(),blob.clone(),Scanner,ring,signer,ArtifactServiceConfig::new(32*1024*1024,60)?);
            let prior = store.ingest(&owner,IngestRequest { bytes:b"fixture prior only".to_vec(),media_type:MediaType::parse("application/octet-stream")?,file_name:FileName::parse("prior.bin")?,kind:ArtifactKind::Source },1)?;
            let result = store.ingest(&owner,IngestRequest { bytes:bytes.clone(),media_type:MediaType::parse("application/vnd.hancom.hwpx+zip")?,file_name:FileName::parse("private-original.hwpx")?,kind:ArtifactKind::Result },2)?;
            store.set_permissions(&owner,result.artifact_id,reader.subject(),BTreeSet::from([ArtifactPermission::Read]),3)?;
            let project = rev::ProjectId::parse("prj_90810000000000000000000000000001")?;
            let branch = rev::BranchId::parse("brn_90810000000000000000000000000001")?;
            let repo = rev::InMemoryRevisionRepository::default(); repo.provision_stream(tenant,project,branch)?;
            let revisions = rev::RevisionService::new(repo);
            let request = rev::RevisionCommitRequest::new(rev::CommitId::generate(),project,branch,rev::RevisionHead::empty(),
                rev::RevisionId::generate(),vec![],prior.artifact_id,result.artifact_id,None,ContentDigest::of(b"fixture operation"),
                rev::RevisionValidationState::Verified,ContentDigest::of(b"fixture validation"),ContentDigest::of(b"fixture transaction"))?;
            assert!(matches!(revisions.commit(&revision_context,&request)?, rev::CommitOutcome::Committed(_)));
            let head = revisions.head(&revision_context,project,branch)?;
            Ok(Self {store,metadata,blob,revisions,owner,reader,revision_context,project,branch,result:result.artifact_id,head,bytes})
        }
        fn provider(&self) -> Result<Provider<'_>,Box<dyn Error>> {
            Ok(StoredFormProvider::bind(&self.store,&self.revisions,&self.reader,&self.revision_context,
                self.project,self.branch,DocumentId::parse("stored-literal-document")?)?)
        }
        fn request(&self, name: &str, include_extension: bool) -> Result<(ReferenceAuxiliaryDocumentState,Vec<u8>),Box<dyn Error>> {
            let imported = ImportedDocumentStructure::import(ImportedSourcePackage::import(&self.bytes,DocumentId::parse("stored-literal-document")?,
                Sha256::digest(&self.bytes).into(),SourceImportLimits::default())?)?;
            let mut draft: ReferenceAuxiliaryDocumentStateDraft = source(limits()?)?.into();
            draft.sections[0].section_id = imported.graph().sections()[0].section_id.clone(); draft.validation_edges.clear();
            let state = ReferenceAuxiliaryDocumentState::from_draft(draft,limits()?)?;
            let point = LinkPoint {paragraph_ordinal:0,run_ordinal:0,inline_ordinal:1};
            let literal = FileNameLiteralNode {logical_literal_id:LogicalId::parse("stored-literal")?,
                anchor:LinkAnchor {section_id:imported.graph().sections()[0].section_id.clone(),start:point,end:point}, literal:name.into(),
                source_leaf_name_sha256:hex::encode(Sha256::digest(name.as_bytes())),
                source_revision_sha256:hex::encode(Sha256::digest(self.head.revision_id().ok_or("revision")?.public_id().as_bytes())),
                include_extension,character_style_sha256:digest('a'),paragraph_style_sha256:digest('b'),opaque_text_state_sha256:digest('c'),opaque_properties:Vec::new(),locked:false};
            let request = serde_json::to_vec(&ReferenceAuxiliaryRequestDraft {schema_version:REFERENCE_AUXILIARY_SCHEMA_VERSION.into(),
                request_id:LogicalId::parse("stored-literal-request")?,expected_source_state_sha256:state.canonical_sha256(limits()?)?,
                expected_document_flow_sha256:digest('f'),target_document_flow_sha256:digest('f'),
                operation:ReferenceAuxiliaryOperation::InsertFileNameLiteral {insertion_index:0,literal:Box::new(literal)}})?;
            Ok((state,request))
        }
        fn prepare(&self, state: &ReferenceAuxiliaryDocumentState, request: &[u8]) -> Result<PreparedStoredFileLiteralCandidate,StoredFileLiteralError> {
            let flow = digest('f');
            self.provider().map_err(|_|StoredFileLiteralError::Source)?.prepare_file_literal_candidate(StoredFileLiteralInputs {
                expected_head:self.head,caller_state:state,declared_flow_sha256:&flow,request_json:request,
                source_limits:SourceImportLimits::default(),reference_limits:limits().map_err(|_|StoredFileLiteralError::Request)?,writer_limits:WriterLimits::default()},4)
        }
        fn advance(&self) -> Result<(),Box<dyn Error>> {
            let request = rev::RevisionCommitRequest::new(rev::CommitId::generate(),self.project,self.branch,self.head,rev::RevisionId::generate(),
                self.head.revision_id().into_iter().collect(),StoredArtifactId::generate(),self.result,None,ContentDigest::of(b"fixture advance"),
                rev::RevisionValidationState::Verified,ContentDigest::of(b"fixture advance validation"),ContentDigest::of(b"fixture advance transaction"))?;
            assert!(matches!(self.revisions.commit(&self.revision_context,&request)?,rev::CommitOutcome::Committed(_))); Ok(())
        }
    }
    #[test]
    fn stored_file_literal_service_descriptor_binds_name_without_ingest_commit_or_route() -> TestResult {
        let rig = Rig::new()?; let (state,request) = rig.request("private-original.hwpx",true)?;
        let before = rig.metadata.audit_events()?.len(); let candidate = rig.prepare(&state,&request)?;
        assert!(candidate.receipt().provider_scoped_filename_metadata_verified);
        assert!(!candidate.receipt().complete_auxiliary_state_verified);
        assert!(!candidate.receipt().issuer_execution_publication_authority);
        let bytes = candidate.with_verified_bytes(&rig.provider()?,5,<[u8]>::to_vec)?;
        assert_ne!(bytes,rig.bytes);
        assert_eq!(Sha256::digest(&bytes).as_slice(),candidate.receipt().output_package_sha256);
        assert_eq!(candidate.require_current_product_route(&rig.provider()?,6),Err(StoredFileLiteralError::RouteUnqualified));
        assert_eq!(rig.revisions.head(&rig.revision_context,rig.project,rig.branch)?,rig.head);
        assert_eq!(rig.store.download(&rig.owner,rig.result,7)?,rig.bytes);
        let events = rig.metadata.audit_events()?;
        assert!(events[before..].iter().all(|e| matches!(e.event,"artifact.metadata.read"|"artifact.download")));
        let text = format!("{candidate:?}{}",String::from_utf8(serde_json::to_vec(candidate.receipt())?)?);
        for private in ["private-original.hwpx","private original content","literal fixture reader"] {assert!(!text.contains(private));}
        Ok(())
    }
    #[test]
    fn stored_file_literal_service_cannot_accept_caller_filename_or_guess_extension_projection() -> TestResult {
        let rig = Rig::new()?;
        let (state,request) = rig.request("caller-substitute.hwpx",true)?;
        assert!(matches!(rig.prepare(&state,&request),Err(StoredFileLiteralError::Binding)));
        let (state,request) = rig.request("private-original",false)?;
        assert!(matches!(rig.prepare(&state,&request),Err(StoredFileLiteralError::Projection)));
        let (state,request) = rig.request("private-original.hwpx",true)?;
        let duplicate = String::from_utf8(request)?.replace("\"include_extension\":true","\"include_extension\":true,\"include_extension\":true");
        assert!(matches!(rig.prepare(&state,duplicate.as_bytes()),Err(StoredFileLiteralError::Request)));
        Ok(())
    }
    #[test]
    fn stored_file_literal_service_acl_revocation_blocks_every_later_byte_callback() -> TestResult {
        let rig = Rig::new()?; let (state,request) = rig.request("private-original.hwpx",true)?;
        let candidate = rig.prepare(&state,&request)?;
        rig.store.set_permissions(&rig.owner,rig.result,rig.reader.subject(),BTreeSet::new(),5)?;
        let called = Cell::new(false);
        assert!(matches!(candidate.with_verified_bytes(&rig.provider()?,6,|_|called.set(true)),Err(StoredFileLiteralError::Source)));
        assert!(!called.get());
        assert!(matches!(candidate.verify(&rig.provider()?,6),Err(StoredFileLiteralError::Source)));
        assert!(matches!(rig.prepare(&state,&request),Err(StoredFileLiteralError::Source)));
        Ok(())
    }
    #[test]
    fn stored_file_literal_service_quarantine_and_aead_tamper_never_expose_candidate_bytes() -> TestResult {
        for quarantine in [false,true] {
            let rig = Rig::new()?; let (state,request) = rig.request("private-original.hwpx",true)?;
            let candidate = rig.prepare(&state,&request)?;
            if quarantine {rig.store.quarantine(&rig.owner,rig.result,QuarantineReason::parse("FIXTURE_QUARANTINE")?,5)?;}
            else {rig.blob.tamper.store(true,Ordering::SeqCst);}
            let called = Cell::new(false);
            assert!(matches!(candidate.with_verified_bytes(&rig.provider()?,6,|_|called.set(true)),Err(StoredFileLiteralError::Source)));
            assert!(!called.get());
        }
        Ok(())
    }
    #[test]
    fn stored_file_literal_service_old_head_is_invalid_even_for_identical_result_bytes() -> TestResult {
        let rig = Rig::new()?; let (state,request) = rig.request("private-original.hwpx",true)?;
        let candidate = rig.prepare(&state,&request)?; rig.advance()?;
        let called = Cell::new(false);
        assert!(matches!(candidate.with_verified_bytes(&rig.provider()?,6,|_|called.set(true)),Err(StoredFileLiteralError::Source)));
        assert!(!called.get()); assert!(matches!(rig.prepare(&state,&request),Err(StoredFileLiteralError::Source)));
        Ok(())
    }
    #[test]
    fn stored_file_literal_service_provider_scope_cannot_be_rebound_to_another_document() -> TestResult {
        let rig = Rig::new()?; let (state,request) = rig.request("private-original.hwpx",true)?;
        let candidate = rig.prepare(&state,&request)?;
        let foreign = StoredFormProvider::bind(&rig.store,&rig.revisions,&rig.reader,&rig.revision_context,
            rig.project,rig.branch,DocumentId::parse("foreign-document")?)?;
        let called = Cell::new(false);
        assert!(matches!(candidate.with_verified_bytes(&foreign,6,|_|called.set(true)),Err(StoredFileLiteralError::Binding)));
        assert!(!called.get());
        Ok(())
    }

    mod stored_caption_service_cases {
        use super::*;
        use hwpx_agent_cli::form_stored_provider::actual_import::reference_captions::*;
        use hwpx_package::document_import::reference_targets::captions::ReferenceCaptionImportError;

        fn caption(side:&str)->String {
            format!("<hp:p id='1'><hp:run><hp:rect id='7'><hp:caption side='{side}' fullSz='0' width='1200' gap='30' lastWidth='1100'><hp:subList><hp:p id='99'><hp:run><hp:t>private caption service text</hp:t></hp:run></hp:p></hp:subList></hp:caption></hp:rect></hp:run></hp:p>")
        }
        // Test setup only. Production adapter never ingests or commits.
        fn caption_rig(body:&str)->Result<Rig,Box<dyn Error>> {
            let mut rig=Rig::new()?; let bytes=fixture::package(body)?;
            let result=rig.store.ingest(&rig.owner,IngestRequest {bytes:bytes.clone(),media_type:MediaType::parse("application/vnd.hancom.hwpx+zip")?,
                file_name:FileName::parse("private-caption.hwpx")?,kind:ArtifactKind::Result},3)?;
            rig.store.set_permissions(&rig.owner,result.artifact_id,rig.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),3)?;
            let request=rev::RevisionCommitRequest::new(rev::CommitId::generate(),rig.project,rig.branch,rig.head,rev::RevisionId::generate(),
                rig.head.revision_id().into_iter().collect(),rig.result,result.artifact_id,None,ContentDigest::of(b"caption fixture setup"),
                rev::RevisionValidationState::Verified,ContentDigest::of(b"caption fixture validation"),ContentDigest::of(b"caption fixture transaction"))?;
            assert!(matches!(rig.revisions.commit(&rig.revision_context,&request)?,rev::CommitOutcome::Committed(_)));
            rig.result=result.artifact_id; rig.head=rig.revisions.head(&rig.revision_context,rig.project,rig.branch)?; rig.bytes=bytes;
            Ok(rig)
        }
        #[test]
        fn stored_caption_service_fresh_source_envelopes_read_only_and_route_denied() -> TestResult {
            let rig=caption_rig(&caption("BOTTOM"))?; let provider=rig.provider()?;
            let before=rig.metadata.audit_events()?.len(); let source=provider.import_actual_forms(rig.head,4)?;
            let imported=source.import_reference_captions(&provider,limits()?,4)?;
            assert_eq!(&imported.receipt().source,source.receipt());
            assert_eq!(imported.receipt().captions.source_package_sha256,<[u8;32]>::from(Sha256::digest(&rig.bytes)));
            assert_eq!(imported.receipt().captions.caption_targets,1);
            assert!(!imported.receipt().captions.sub_list_numbering_qualified);
            assert!(!imported.receipt().captions.complete_auxiliary_state_qualified);
            imported.with_source_captions(&provider,5,|envelopes,targets|{assert_eq!(envelopes.len(),1);assert_eq!(targets.len(),1);})?;
            assert!(matches!(imported.require_current_product_route(&provider,6),Err(StoredReferenceCaptionError::RouteUnqualified)));
            assert_eq!(rig.revisions.head(&rig.revision_context,rig.project,rig.branch)?,rig.head);
            assert_eq!(rig.store.download(&rig.owner,rig.result,7)?,rig.bytes);
            assert!(rig.metadata.audit_events()?[before..].iter().all(|e|matches!(e.event,"artifact.metadata.read"|"artifact.download")));
            let redacted=format!("{imported:?}{}",String::from_utf8(serde_json::to_vec(imported.receipt())?)?);
            for private in ["private-caption.hwpx","private caption service text","literal fixture reader"] {assert!(!redacted.contains(private));}
            Ok(())
        }
        #[test]
        fn stored_caption_service_revoked_acl_never_calls_consumer_or_reimports() -> TestResult {
            let rig=caption_rig(&caption("TOP"))?; let provider=rig.provider()?;
            let source=provider.import_actual_forms(rig.head,4)?; let imported=source.import_reference_captions(&provider,limits()?,4)?;
            rig.store.set_permissions(&rig.owner,rig.result,rig.reader.subject(),BTreeSet::new(),5)?;
            let called=Cell::new(false);
            assert!(matches!(imported.with_source_captions(&provider,6,|_,_|called.set(true)),Err(StoredReferenceCaptionError::Source(_))));
            assert!(!called.get()); assert!(imported.verify(&provider,6).is_err());
            assert!(source.import_reference_captions(&provider,limits()?,6).is_err()); Ok(())
        }
        #[test]
        fn stored_caption_service_quarantine_or_aead_tamper_never_calls_consumer() -> TestResult {
            for quarantine in [false,true] {
                let rig=caption_rig(&caption("LEFT"))?; let provider=rig.provider()?;
                let source=provider.import_actual_forms(rig.head,4)?; let imported=source.import_reference_captions(&provider,limits()?,4)?;
                if quarantine {rig.store.quarantine(&rig.owner,rig.result,QuarantineReason::parse("CAPTION_FIXTURE_QUARANTINE")?,5)?;}
                else {rig.blob.tamper.store(true,Ordering::SeqCst);}
                let called=Cell::new(false);
                assert!(matches!(imported.with_source_captions(&provider,6,|_,_|called.set(true)),Err(StoredReferenceCaptionError::Source(_))));
                assert!(!called.get());
            } Ok(())
        }
        #[test]
        fn stored_caption_service_advanced_head_blocks_same_artifact_and_old_model() -> TestResult {
            let rig=caption_rig(&caption("RIGHT"))?; let provider=rig.provider()?;
            let source=provider.import_actual_forms(rig.head,4)?; let imported=source.import_reference_captions(&provider,limits()?,4)?;
            rig.advance()?; let called=Cell::new(false);
            assert!(matches!(imported.with_source_captions(&provider,6,|_,_|called.set(true)),Err(StoredReferenceCaptionError::Source(_))));
            assert!(!called.get()); assert!(source.import_reference_captions(&provider,limits()?,6).is_err()); Ok(())
        }
        #[test]
        fn stored_caption_service_foreign_scope_and_reconstruction_cannot_be_rebound() -> TestResult {
            let rig=caption_rig(&caption("BOTTOM"))?; let provider=rig.provider()?;
            let source=provider.import_actual_forms(rig.head,4)?; let imported=source.import_reference_captions(&provider,limits()?,4)?;
            let foreign=StoredFormProvider::bind(&rig.store,&rig.revisions,&rig.reader,&rig.revision_context,rig.project,rig.branch,DocumentId::parse("foreign-caption-document")?)?;
            let called=Cell::new(false);
            assert!(imported.with_source_captions(&foreign,6,|_,_|called.set(true)).is_err()); assert!(!called.get());
            use hwpx_package::document_import::{forms::ImportedDocumentForms,reference_targets::captions::ImportedReferenceCaptions};
            let other=ImportedDocumentForms::import(ImportedSourcePackage::import(&rig.bytes,DocumentId::parse("stored-literal-document")?,Sha256::digest(&rig.bytes).into(),SourceImportLimits::default())?)?;
            let original=source.imported(); let model=ImportedReferenceCaptions::import(original.body_structure(),limits()?)?;
            let proof=other.reconstruct_source_for_verification(&rig.bytes)?;
            assert!(matches!(model.verify_reconstructed(original,&proof,limits()?),Err(ReferenceCaptionImportError::Binding)));
            let proof=original.reconstruct_source_for_verification(&rig.bytes)?;
            assert!(matches!(model.verify_reconstructed(&other,&proof,limits()?),Err(ReferenceCaptionImportError::Binding))); Ok(())
        }
        #[test]
        fn stored_caption_service_limits_and_malformed_envelopes_fail_closed() -> TestResult {
            let rig=caption_rig(&format!("{}{}",caption("BOTTOM"),caption("TOP")))?; let provider=rig.provider()?;
            let source=provider.import_actual_forms(rig.head,4)?;
            let small=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {items_per_kind:1,..Default::default()})?;
            assert!(matches!(source.import_reference_captions(&provider,small,4),Err(StoredReferenceCaptionError::Model(ReferenceCaptionImportError::Limit))));
            let small=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {input_bytes:1,output_bytes:1,..Default::default()})?;
            assert!(matches!(source.import_reference_captions(&provider,small,4),Err(StoredReferenceCaptionError::Model(ReferenceCaptionImportError::Limit))));
            let rig=caption_rig(&caption("UNSUPPORTED"))?; let provider=rig.provider()?;
            let source=provider.import_actual_forms(rig.head,4)?;
            assert!(matches!(source.import_reference_captions(&provider,limits()?,4),Err(StoredReferenceCaptionError::Model(ReferenceCaptionImportError::Envelope)))); Ok(())
        }

        mod text_output_binding {
            use super::*;
            use hwpx_agent_cli::form_stored_provider::actual_import::{StoredImportedDocumentForms,caption_text_output::*};
            use hwpx_package::document_import::{forms::ImportedDocumentForms,reference_targets::numbering::ImportedCaptionNumbering,
                structure::caption_text::CaptionTextOutputError};
            fn selected(source:&StoredImportedDocumentForms)->Result<(LogicalId,LogicalId),Box<dyn Error>> {
                let numbering=ImportedCaptionNumbering::import(source.imported().body_structure(),limits()?)?;
                let frames=numbering.import_frames(limits()?)?;let frame=frames.frames().first().ok_or("caption frame")?;
                let text=frame.segments.iter().find(|segment|frames.plain_text(&segment.logical_source_id).is_some()).ok_or("plain caption text")?;
                Ok((frame.logical_caption_id.clone(),text.logical_source_id.clone()))
            }
            #[test]
            fn stored_caption_text_read_only_candidate_binds_request_and_reauthorizes_each_exposure() -> TestResult {
                let rig=caption_rig(&caption("BOTTOM"))?;let provider=rig.provider()?;
                let before=rig.metadata.audit_events()?.len();let source=provider.import_actual_forms(rig.head,4)?;let (cap,text)=selected(&source)?;
                let replacement="private replacement & <캡션>\r\n";
                let candidate=source.prepare_caption_text_candidate(&provider,&cap,&text,replacement,limits()?,WriterLimits::default(),4)?;
                assert_eq!(&candidate.receipt().source,source.receipt());assert_eq!(candidate.receipt().source_caption_id,cap);assert_eq!(candidate.receipt().source_text_id,text);
                assert_eq!(candidate.receipt().requested_text_sha256,<[u8;32]>::from(Sha256::digest(replacement.as_bytes())));
                assert_eq!(candidate.receipt().requested_text_bytes,replacement.len());
                assert_eq!(candidate.receipt().requested_text_sha256,candidate.receipt().output.output_text_sha256);
                assert!(!candidate.receipt().issuer_execution_publication_authority&&!candidate.receipt().output.execution_publication_authority);
                assert!(!candidate.receipt().output.complete_auxiliary_state_and_protection_verified);
                let bytes=candidate.with_verified_bytes(&provider,5,<[u8]>::to_vec)?;
                assert_ne!(bytes,rig.bytes);assert_eq!(<[u8;32]>::from(Sha256::digest(&bytes)),candidate.receipt().output.output_package_sha256);
                let output=ImportedDocumentForms::import(ImportedSourcePackage::import(&bytes,DocumentId::parse("stored-literal-document")?,Sha256::digest(&bytes).into(),SourceImportLimits::default())?)?;
                let numbers=ImportedCaptionNumbering::import(output.body_structure(),limits()?)?;let frames=numbers.import_frames(limits()?)?;
                assert_eq!(frames.plain_text(&frames.frames()[0].segments[0].logical_source_id),Some(replacement));
                let audit=rig.metadata.audit_events()?.len();candidate.with_verified_bytes(&provider,6,|_|())?;
                assert!(rig.metadata.audit_events()?.len()>audit);
                assert!(matches!(candidate.require_current_product_route(&provider,7),Err(StoredCaptionTextError::RouteUnqualified)));
                assert_eq!(rig.revisions.head(&rig.revision_context,rig.project,rig.branch)?,rig.head);assert_eq!(rig.store.download(&rig.owner,rig.result,8)?,rig.bytes);
                assert!(rig.metadata.audit_events()?[before..].iter().all(|event|matches!(event.event,"artifact.metadata.read"|"artifact.download")));
                let safe=format!("{candidate:?}{}",serde_json::to_string(candidate.receipt())?);
                for private in ["private-caption.hwpx","private caption service text","private replacement","literal fixture reader"]{assert!(!safe.contains(private));}Ok(())
            }
            #[test]
            fn stored_caption_text_acl_revocation_blocks_preparation_verify_route_and_byte_callback() -> TestResult {
                let rig=caption_rig(&caption("BOTTOM"))?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let (cap,text)=selected(&source)?;
                let candidate=source.prepare_caption_text_candidate(&provider,&cap,&text,"new",limits()?,WriterLimits::default(),4)?;
                let _old_proof=source.imported().reconstruct_source_for_verification(&rig.bytes)?;
                rig.store.set_permissions(&rig.owner,rig.result,rig.reader.subject(),BTreeSet::new(),5)?;let called=Cell::new(false);
                assert!(matches!(candidate.with_verified_bytes(&provider,6,|_|called.set(true)),Err(StoredCaptionTextError::Source(_))));assert!(!called.get());
                assert!(matches!(candidate.verify(&provider,6),Err(StoredCaptionTextError::Source(_))));
                assert!(matches!(candidate.require_current_product_route(&provider,6),Err(StoredCaptionTextError::Source(_))));
                assert!(matches!(source.prepare_caption_text_candidate(&provider,&cap,&text,"new",limits()?,WriterLimits::default(),6),Err(StoredCaptionTextError::Source(_))));Ok(())
            }
            #[test]
            fn stored_caption_text_quarantine_or_ciphertext_tamper_blocks_all_prepared_output() -> TestResult {
                for quarantine in [false,true] {
                    let rig=caption_rig(&caption("BOTTOM"))?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let (cap,text)=selected(&source)?;
                    let candidate=source.prepare_caption_text_candidate(&provider,&cap,&text,"new",limits()?,WriterLimits::default(),4)?;
                    if quarantine {rig.store.quarantine(&rig.owner,rig.result,QuarantineReason::parse("CAPTION_TEXT_FIXTURE_QUARANTINE")?,5)?;} else {rig.blob.tamper.store(true,Ordering::SeqCst);}
                    let called=Cell::new(false);assert!(matches!(candidate.with_verified_bytes(&provider,6,|_|called.set(true)),Err(StoredCaptionTextError::Source(_))));assert!(!called.get());
                    assert!(candidate.verify(&provider,6).is_err());assert!(source.prepare_caption_text_candidate(&provider,&cap,&text,"new",limits()?,WriterLimits::default(),6).is_err());
                }Ok(())
            }
            #[test]
            fn stored_caption_text_advanced_head_invalidates_old_source_even_when_artifact_is_the_same() -> TestResult {
                let rig=caption_rig(&caption("BOTTOM"))?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let (cap,text)=selected(&source)?;
                let candidate=source.prepare_caption_text_candidate(&provider,&cap,&text,"new",limits()?,WriterLimits::default(),4)?;
                rig.advance()?;let called=Cell::new(false);
                assert!(matches!(candidate.with_verified_bytes(&provider,6,|_|called.set(true)),Err(StoredCaptionTextError::Source(_))));assert!(!called.get());
                assert!(candidate.verify(&provider,6).is_err());assert!(source.prepare_caption_text_candidate(&provider,&cap,&text,"new",limits()?,WriterLimits::default(),6).is_err());Ok(())
            }
            #[test]
            fn stored_caption_text_foreign_scope_original_proof_and_fresh_bytes_cannot_be_substituted() -> TestResult {
                let rig=caption_rig(&caption("BOTTOM"))?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let (cap,text)=selected(&source)?;
                let candidate=source.prepare_caption_text_candidate(&provider,&cap,&text,"new",limits()?,WriterLimits::default(),4)?;
                let foreign=StoredFormProvider::bind(&rig.store,&rig.revisions,&rig.reader,&rig.revision_context,rig.project,rig.branch,DocumentId::parse("foreign-caption-text-document")?)?;
                let called=Cell::new(false);assert!(candidate.with_verified_bytes(&foreign,6,|_|called.set(true)).is_err());assert!(!called.get());
                assert!(source.prepare_caption_text_candidate(&foreign,&cap,&text,"new",limits()?,WriterLimits::default(),6).is_err());
                let other=provider.import_actual_forms(rig.head,6)?;let proof=source.imported().reconstruct_source_for_verification(&rig.bytes)?;
                assert!(matches!(proof.lower_caption_text_candidate(other.imported(),&rig.bytes,&cap,&text,"new",limits()?,WriterLimits::default()),Err(CaptionTextOutputError::Source)));
                let mut wrong=rig.bytes.clone();wrong[0]^=1;
                assert!(matches!(proof.lower_caption_text_candidate(source.imported(),&wrong,&cap,&text,"new",limits()?,WriterLimits::default()),Err(CaptionTextOutputError::Source)));Ok(())
            }
            #[test]
            fn stored_caption_text_keeps_selector_protection_value_noop_and_finite_limit_rejections() -> TestResult {
                let rig=caption_rig(&caption("BOTTOM"))?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let (cap,text)=selected(&source)?;
                let tight=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig{input_bytes:1,output_bytes:1,..Default::default()})?;
                assert!(matches!(source.prepare_caption_text_candidate(&provider,&cap,&text,"new",tight,WriterLimits::default(),4),Err(StoredCaptionTextError::Output(CaptionTextOutputError::Limit))));
                let writer=WriterLimits::new(hwpx_package::WriterLimitConfig{max_output_bytes:1})?;
                assert!(matches!(source.prepare_caption_text_candidate(&provider,&cap,&text,"new",limits()?,writer,4),Err(StoredCaptionTextError::Output(CaptionTextOutputError::Writer))));
                assert!(matches!(source.prepare_caption_text_candidate(&provider,&cap,&LogicalId::parse("foreign-caption-text")?,"new",limits()?,WriterLimits::default(),4),Err(StoredCaptionTextError::Output(CaptionTextOutputError::Selection))));
                assert!(matches!(source.prepare_caption_text_candidate(&provider,&cap,&text,"bad\0",limits()?,WriterLimits::default(),4),Err(StoredCaptionTextError::Output(CaptionTextOutputError::Value))));
                assert!(matches!(source.prepare_caption_text_candidate(&provider,&cap,&text,"private caption service text",limits()?,WriterLimits::default(),4),Err(StoredCaptionTextError::Output(CaptionTextOutputError::NoChange))));
                let rig=caption_rig(&caption("BOTTOM").replace("<hp:rect id='7'>","<hp:rect id='7' lock='1'>"))?;
                let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let (cap,text)=selected(&source)?;
                assert!(matches!(source.prepare_caption_text_candidate(&provider,&cap,&text,"new",limits()?,WriterLimits::default(),4),Err(StoredCaptionTextError::Output(CaptionTextOutputError::Protection))));Ok(())
            }
        }

        mod text_batch_output_binding {
            use super::*;
            use hwpx_agent_cli::form_stored_provider::actual_import::{StoredImportedDocumentForms,caption_text_batch_output::*,caption_text_output::StoredCaptionTextError as E};
            use hwpx_package::document_import::{forms::ImportedDocumentForms,reference_targets::numbering::ImportedCaptionNumbering,
                structure::{caption_text::CaptionTextOutputError,caption_text_batch::CaptionTextReplacement as Request}};
            fn body(locked:bool)->String {
                (0..3).map(|i|{let mut text=caption("BOTTOM").replace("id='1'",&format!("id='{}'",1+i)).replace("id='7'",&format!("id='{}'",7+i)).replace("id='99'",&format!("id='{}'",99+i));
                    if locked&&i==2 {text=text.replace(&format!("<hp:rect id='{}'>",7+i),&format!("<hp:rect id='{}' lock='1'>",7+i));}text}).collect()
            }
            fn selections(source:&StoredImportedDocumentForms)->Result<Vec<(LogicalId,LogicalId)>,Box<dyn Error>> {
                let numbers=ImportedCaptionNumbering::import(source.imported().body_structure(),limits()?)?;let frames=numbers.import_frames(limits()?)?;
                Ok(frames.frames().iter().flat_map(|frame|frame.segments.iter().filter(|s|frames.plain_text(&s.logical_source_id).is_some()).map(|s|(frame.logical_caption_id.clone(),s.logical_source_id.clone()))).collect())
            }
            fn requests(ids:&[(LogicalId,LogicalId)])->Vec<Request<'_>> {
                let values=["private new A & <x>\r\n","private caption service text","private new B"];
                ids.iter().zip(values).map(|((cap,text),value)|Request{caption_id:cap,text_id:text,replacement:value}).collect()
            }
            #[test]
            fn stored_caption_text_batch_request_hashes_noops_and_read_only_exposures_remain_bound() -> TestResult {
                let rig=caption_rig(&body(false))?;let provider=rig.provider()?;let before=rig.metadata.audit_events()?.len();
                let source=provider.import_actual_forms(rig.head,4)?;let ids=selections(&source)?;assert_eq!(ids.len(),3);let request=requests(&ids);
                let candidate=source.prepare_caption_text_batch_candidate(&provider,&request,limits()?,WriterLimits::default(),4)?;
                assert_eq!(&candidate.receipt().source,source.receipt());assert_eq!((candidate.receipt().output.requested_leaves,candidate.receipt().output.changed_leaves),(3,2));
                assert_eq!(candidate.receipt().requests.iter().map(|r|r.changed).collect::<Vec<_>>(),[true,false,true]);
                for (binding,request) in candidate.receipt().requests.iter().zip(&request) {
                    assert_eq!(&binding.source_caption_id,request.caption_id);assert_eq!(&binding.source_text_id,request.text_id);
                    assert_eq!(binding.requested_text_sha256,<[u8;32]>::from(Sha256::digest(request.replacement.as_bytes())));assert_eq!(binding.requested_text_bytes,request.replacement.len());
                }
                assert!(!candidate.receipt().issuer_execution_publication_authority&&!candidate.receipt().output.execution_publication_authority&&!candidate.receipt().output.complete_auxiliary_state_and_protection_verified);
                let bytes=candidate.with_verified_bytes(&provider,5,<[u8]>::to_vec)?;
                assert_eq!(<[u8;32]>::from(Sha256::digest(&bytes)),candidate.receipt().output.output_package_sha256);
                let output=ImportedDocumentForms::import(ImportedSourcePackage::import(&bytes,DocumentId::parse("stored-literal-document")?,Sha256::digest(&bytes).into(),SourceImportLimits::default())?)?;
                let numbers=ImportedCaptionNumbering::import(output.body_structure(),limits()?)?;let frames=numbers.import_frames(limits()?)?;
                for (frame,wanted) in frames.frames().iter().zip(&request) {assert_eq!(frames.plain_text(&frame.segments[0].logical_source_id),Some(wanted.replacement));}
                let audit=rig.metadata.audit_events()?.len();assert_eq!(candidate.verify(&provider,6)?,*candidate.receipt());candidate.with_verified_bytes(&provider,6,|_|())?;assert!(rig.metadata.audit_events()?.len()>audit);
                assert!(matches!(candidate.require_current_product_route(&provider,7),Err(E::RouteUnqualified)));
                assert_eq!(rig.revisions.head(&rig.revision_context,rig.project,rig.branch)?,rig.head);assert_eq!(rig.store.download(&rig.owner,rig.result,8)?,rig.bytes);
                assert!(rig.metadata.audit_events()?[before..].iter().all(|event|matches!(event.event,"artifact.metadata.read"|"artifact.download")));
                let safe=format!("{candidate:?}{}",serde_json::to_string(candidate.receipt())?);
                for private in ["private-caption.hwpx","private caption service text","private new A","private new B","literal fixture reader"]{assert!(!safe.contains(private));}Ok(())
            }
            #[test]
            fn stored_caption_text_batch_acl_revocation_invalidates_candidate_old_proof_and_all_callbacks() -> TestResult {
                let rig=caption_rig(&body(false))?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let ids=selections(&source)?;let request=requests(&ids);
                let candidate=source.prepare_caption_text_batch_candidate(&provider,&request,limits()?,WriterLimits::default(),4)?;let _old=source.imported().reconstruct_source_for_verification(&rig.bytes)?;
                rig.store.set_permissions(&rig.owner,rig.result,rig.reader.subject(),BTreeSet::new(),5)?;let called=Cell::new(false);
                assert!(matches!(candidate.with_verified_bytes(&provider,6,|_|called.set(true)),Err(E::Source(_))));assert!(!called.get());
                assert!(matches!(candidate.verify(&provider,6),Err(E::Source(_))));assert!(matches!(candidate.require_current_product_route(&provider,6),Err(E::Source(_))));
                assert!(matches!(source.prepare_caption_text_batch_candidate(&provider,&request,limits()?,WriterLimits::default(),6),Err(E::Source(_))));Ok(())
            }
            #[test]
            fn stored_caption_text_batch_quarantine_and_ciphertext_tamper_never_expose_partial_outputs() -> TestResult {
                for quarantine in [false,true] {
                    let rig=caption_rig(&body(false))?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let ids=selections(&source)?;let request=requests(&ids);
                    let candidate=source.prepare_caption_text_batch_candidate(&provider,&request,limits()?,WriterLimits::default(),4)?;
                    if quarantine {rig.store.quarantine(&rig.owner,rig.result,QuarantineReason::parse("CAPTION_BATCH_FIXTURE_QUARANTINE")?,5)?;}else{rig.blob.tamper.store(true,Ordering::SeqCst);}
                    let called=Cell::new(false);assert!(matches!(candidate.with_verified_bytes(&provider,6,|_|called.set(true)),Err(E::Source(_))));assert!(!called.get());
                    assert!(candidate.verify(&provider,6).is_err());assert!(source.prepare_caption_text_batch_candidate(&provider,&request,limits()?,WriterLimits::default(),6).is_err());
                }Ok(())
            }
            #[test]
            fn stored_caption_text_batch_new_head_invalidates_old_candidate_with_same_artifact() -> TestResult {
                let rig=caption_rig(&body(false))?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let ids=selections(&source)?;let request=requests(&ids);
                let candidate=source.prepare_caption_text_batch_candidate(&provider,&request,limits()?,WriterLimits::default(),4)?;
                rig.advance()?;let called=Cell::new(false);
                assert!(matches!(candidate.with_verified_bytes(&provider,6,|_|called.set(true)),Err(E::Source(_))));assert!(!called.get());
                assert!(candidate.verify(&provider,6).is_err());assert!(source.prepare_caption_text_batch_candidate(&provider,&request,limits()?,WriterLimits::default(),6).is_err());Ok(())
            }
            #[test]
            fn stored_caption_text_batch_foreign_scope_original_proof_and_bytes_cannot_be_substituted() -> TestResult {
                let rig=caption_rig(&body(false))?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let ids=selections(&source)?;let request=requests(&ids);
                let candidate=source.prepare_caption_text_batch_candidate(&provider,&request,limits()?,WriterLimits::default(),4)?;
                let foreign=StoredFormProvider::bind(&rig.store,&rig.revisions,&rig.reader,&rig.revision_context,rig.project,rig.branch,DocumentId::parse("foreign-caption-batch-document")?)?;
                let called=Cell::new(false);assert!(candidate.with_verified_bytes(&foreign,6,|_|called.set(true)).is_err());assert!(!called.get());
                assert!(source.prepare_caption_text_batch_candidate(&foreign,&request,limits()?,WriterLimits::default(),6).is_err());
                let other=provider.import_actual_forms(rig.head,6)?;let proof=source.imported().reconstruct_source_for_verification(&rig.bytes)?;
                assert!(matches!(proof.lower_caption_text_batch_candidate(other.imported(),&rig.bytes,&request,limits()?,WriterLimits::default()),Err(CaptionTextOutputError::Source)));
                let mut drift=rig.bytes.clone();drift[0]^=1;assert!(matches!(proof.lower_caption_text_batch_candidate(source.imported(),&drift,&request,limits()?,WriterLimits::default()),Err(CaptionTextOutputError::Source)));Ok(())
            }
            #[test]
            fn stored_caption_text_batch_invalid_noop_duplicate_protected_and_limited_requests_publish_nothing() -> TestResult {
                let rig=caption_rig(&body(false))?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let ids=selections(&source)?;let request=requests(&ids);
                let foreign=LogicalId::parse("foreign-caption-batch-text")?;
                let invalid=[Request{caption_id:&ids[0].0,text_id:&ids[0].1,replacement:"new"},Request{caption_id:&ids[1].0,text_id:&foreign,replacement:"new"}];
                assert!(matches!(source.prepare_caption_text_batch_candidate(&provider,&invalid,limits()?,WriterLimits::default(),4),Err(E::Output(CaptionTextOutputError::Selection))));
                let duplicate=[Request{caption_id:&ids[0].0,text_id:&ids[0].1,replacement:"new"},Request{caption_id:&ids[0].0,text_id:&ids[0].1,replacement:"other"}];
                assert!(matches!(source.prepare_caption_text_batch_candidate(&provider,&duplicate,limits()?,WriterLimits::default(),4),Err(E::Output(CaptionTextOutputError::Selection))));
                let noops=ids.iter().map(|(cap,text)|Request{caption_id:cap,text_id:text,replacement:"private caption service text"}).collect::<Vec<_>>();
                assert!(matches!(source.prepare_caption_text_batch_candidate(&provider,&noops,limits()?,WriterLimits::default(),4),Err(E::Output(CaptionTextOutputError::NoChange))));
                let invalid=[Request{caption_id:&ids[0].0,text_id:&ids[0].1,replacement:"bad\0"}];
                assert!(matches!(source.prepare_caption_text_batch_candidate(&provider,&invalid,limits()?,WriterLimits::default(),4),Err(E::Output(CaptionTextOutputError::Value))));
                let small=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig{text_bytes:1,..Default::default()})?;
                assert!(matches!(source.prepare_caption_text_batch_candidate(&provider,&request,small,WriterLimits::default(),4),Err(E::Output(CaptionTextOutputError::Limit))));
                assert!(matches!(source.prepare_caption_text_batch_candidate(&provider,&request,limits()?,WriterLimits::new(hwpx_package::WriterLimitConfig{max_output_bytes:1})?,4),Err(E::Output(CaptionTextOutputError::Writer))));
                let rig=caption_rig(&body(true))?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let ids=selections(&source)?;let request=requests(&ids);
                assert!(matches!(source.prepare_caption_text_batch_candidate(&provider,&request,limits()?,WriterLimits::default(),4),Err(E::Output(CaptionTextOutputError::Protection))));Ok(())
            }

            mod edit_batch_output_binding {
                mod content_output_binding {include!("reference_validation_product/caption_content_output.rs");}
                use super::*;
                use domain_ir::NativeCaptionSide;
                use hwpx_package::document_import::structure::{caption_layout::CaptionLayout,
                    caption_edit_batch::CaptionLayoutReplacement as Layout};
                fn same_layout()->CaptionLayout {CaptionLayout {side:NativeCaptionSide::Bottom,full_size:false,width_hwpunit:1200,gap_hwpunit:30,last_width_hwpunit:1100}}
                fn layouts(ids:&[(LogicalId,LogicalId)])->Vec<Layout<'_>> {
                    vec![Layout {caption_id:&ids[0].0,layout:CaptionLayout {side:NativeCaptionSide::Left,full_size:true,width_hwpunit:80,gap_hwpunit:12,last_width_hwpunit:40}},
                        Layout {caption_id:&ids[1].0,layout:same_layout()},Layout {caption_id:&ids[2].0,layout:CaptionLayout {side:NativeCaptionSide::Top,..same_layout()}}]
                }
                #[test]
                fn stored_caption_edit_batch_binds_both_request_families_noops_and_read_only_complete_output() -> TestResult {
                    let rig=caption_rig(&body(false))?;let provider=rig.provider()?;let before=rig.metadata.audit_events()?.len();
                    let source=provider.import_actual_forms(rig.head,4)?;let ids=selections(&source)?;let texts=requests(&ids);let values=layouts(&ids);
                    let candidate=source.prepare_caption_edit_batch_candidate(&provider,&texts,&values,limits()?,WriterLimits::default(),4)?;
                    let receipt=candidate.receipt();assert_eq!(&receipt.source,source.receipt());
                    assert_eq!((receipt.output.requested_text_leaves,receipt.output.requested_layouts,receipt.output.text_changes.len(),receipt.output.layout_changes.len()),(3,3,2,2));
                    assert_eq!(receipt.text_requests.iter().map(|r|r.changed).collect::<Vec<_>>(),[true,false,true]);
                    assert_eq!(receipt.layout_requests.iter().map(|r|r.changed).collect::<Vec<_>>(),[true,false,true]);
                    for (binding,request) in receipt.text_requests.iter().zip(&texts) {
                        assert_eq!(&binding.source_caption_id,request.caption_id);assert_eq!(&binding.source_text_id,request.text_id);
                        assert_eq!(binding.requested_text_sha256,<[u8;32]>::from(Sha256::digest(request.replacement.as_bytes())));assert_eq!(binding.requested_text_bytes,request.replacement.len());
                    }
                    for (binding,request) in receipt.layout_requests.iter().zip(&values) {assert_eq!(&binding.source_caption_id,request.caption_id);assert_eq!(binding.requested_layout,request.layout);}
                    let bytes=candidate.with_verified_bytes(&provider,5,<[u8]>::to_vec)?;
                    assert_eq!(<[u8;32]>::from(Sha256::digest(&bytes)),receipt.output.output_package_sha256);
                    let output=ImportedDocumentForms::import(ImportedSourcePackage::import(&bytes,DocumentId::parse("stored-literal-document")?,Sha256::digest(&bytes).into(),SourceImportLimits::default())?)?;
                    let numbers=ImportedCaptionNumbering::import(output.body_structure(),limits()?)?;let frames=numbers.import_frames(limits()?)?;
                    for (frame,request) in frames.frames().iter().zip(&texts) {assert_eq!(frames.plain_text(&frame.segments[0].logical_source_id),Some(request.replacement));}
                    for (envelope,request) in numbers.caption_import().envelopes().iter().zip(&values) {
                        let found=envelope.native_envelope();let wanted=request.layout;
                        assert_eq!((found.side,found.full_size,found.width_hwpunit,found.gap_hwpunit,found.last_width_hwpunit),(wanted.side,wanted.full_size,wanted.width_hwpunit,wanted.gap_hwpunit,wanted.last_width_hwpunit));
                    }
                    let audits=rig.metadata.audit_events()?.len();assert_eq!(candidate.verify(&provider,6)?,*receipt);candidate.with_verified_bytes(&provider,6,|_|())?;
                    assert!(rig.metadata.audit_events()?.len()>audits);assert!(matches!(candidate.require_current_product_route(&provider,7),Err(E::RouteUnqualified)));
                    assert_eq!(rig.revisions.head(&rig.revision_context,rig.project,rig.branch)?,rig.head);assert_eq!(rig.store.download(&rig.owner,rig.result,8)?,rig.bytes);
                    assert!(rig.metadata.audit_events()?[before..].iter().all(|event|matches!(event.event,"artifact.metadata.read"|"artifact.download")));
                    assert!(!receipt.issuer_execution_publication_authority&&!receipt.output.execution_publication_authority&&!receipt.output.complete_auxiliary_state_and_protection_verified);
                    let safe=format!("{candidate:?}{}",serde_json::to_string(receipt)?);
                    for private in ["private-caption.hwpx","private caption service text","private new A","private new B","literal fixture reader"] {assert!(!safe.contains(private));}Ok(())
                }
                #[test]
                fn stored_caption_edit_batch_revoked_acl_blocks_prepare_verify_route_and_both_edit_outputs() -> TestResult {
                    let rig=caption_rig(&body(false))?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let ids=selections(&source)?;
                    let texts=requests(&ids);let values=layouts(&ids);let candidate=source.prepare_caption_edit_batch_candidate(&provider,&texts,&values,limits()?,WriterLimits::default(),4)?;
                    let _proof=source.imported().reconstruct_source_for_verification(&rig.bytes)?;
                    rig.store.set_permissions(&rig.owner,rig.result,rig.reader.subject(),BTreeSet::new(),5)?;let called=Cell::new(false);
                    assert!(matches!(candidate.with_verified_bytes(&provider,6,|_|called.set(true)),Err(E::Source(_))));assert!(!called.get());
                    assert!(matches!(candidate.verify(&provider,6),Err(E::Source(_))));assert!(matches!(candidate.require_current_product_route(&provider,6),Err(E::Source(_))));
                    assert!(matches!(source.prepare_caption_edit_batch_candidate(&provider,&texts,&values,limits()?,WriterLimits::default(),6),Err(E::Source(_))));Ok(())
                }
                #[test]
                fn stored_caption_edit_batch_quarantine_or_ciphertext_tamper_never_exposes_partial_candidate() -> TestResult {
                    for quarantine in [false,true] {
                        let rig=caption_rig(&body(false))?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let ids=selections(&source)?;
                        let texts=requests(&ids);let values=layouts(&ids);let candidate=source.prepare_caption_edit_batch_candidate(&provider,&texts,&values,limits()?,WriterLimits::default(),4)?;
                        if quarantine {rig.store.quarantine(&rig.owner,rig.result,QuarantineReason::parse("CAPTION_EDIT_BATCH_FIXTURE_QUARANTINE")?,5)?;}else{rig.blob.tamper.store(true,Ordering::SeqCst);}
                        let called=Cell::new(false);assert!(candidate.with_verified_bytes(&provider,6,|_|called.set(true)).is_err());assert!(!called.get());
                        assert!(candidate.verify(&provider,6).is_err());assert!(candidate.require_current_product_route(&provider,6).is_err());
                        assert!(source.prepare_caption_edit_batch_candidate(&provider,&texts,&values,limits()?,WriterLimits::default(),6).is_err());
                    }Ok(())
                }
                #[test]
                fn stored_caption_edit_batch_advanced_head_invalidates_candidate_even_for_same_artifact() -> TestResult {
                    let rig=caption_rig(&body(false))?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let ids=selections(&source)?;
                    let texts=requests(&ids);let values=layouts(&ids);let candidate=source.prepare_caption_edit_batch_candidate(&provider,&texts,&values,limits()?,WriterLimits::default(),4)?;
                    rig.advance()?;let called=Cell::new(false);
                    assert!(matches!(candidate.with_verified_bytes(&provider,6,|_|called.set(true)),Err(E::Source(_))));assert!(!called.get());
                    assert!(candidate.verify(&provider,6).is_err());assert!(candidate.require_current_product_route(&provider,6).is_err());
                    assert!(source.prepare_caption_edit_batch_candidate(&provider,&texts,&values,limits()?,WriterLimits::default(),6).is_err());Ok(())
                }
                #[test]
                fn stored_caption_edit_batch_foreign_scope_original_proof_and_bytes_cannot_replace_current_source() -> TestResult {
                    let rig=caption_rig(&body(false))?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let ids=selections(&source)?;
                    let texts=requests(&ids);let values=layouts(&ids);let candidate=source.prepare_caption_edit_batch_candidate(&provider,&texts,&values,limits()?,WriterLimits::default(),4)?;
                    let foreign=StoredFormProvider::bind(&rig.store,&rig.revisions,&rig.reader,&rig.revision_context,rig.project,rig.branch,DocumentId::parse("foreign-caption-edit-batch-document")?)?;
                    let called=Cell::new(false);assert!(candidate.with_verified_bytes(&foreign,6,|_|called.set(true)).is_err());assert!(!called.get());
                    assert!(candidate.verify(&foreign,6).is_err());assert!(source.prepare_caption_edit_batch_candidate(&foreign,&texts,&values,limits()?,WriterLimits::default(),6).is_err());
                    let other=provider.import_actual_forms(rig.head,6)?;let proof=source.imported().reconstruct_source_for_verification(&rig.bytes)?;
                    assert!(matches!(proof.lower_caption_edit_batch_candidate(other.imported(),&rig.bytes,&texts,&values,limits()?,WriterLimits::default()),Err(CaptionTextOutputError::Source)));
                    let mut drift=rig.bytes.clone();drift[0]^=1;
                    assert!(matches!(proof.lower_caption_edit_batch_candidate(source.imported(),&drift,&texts,&values,limits()?,WriterLimits::default()),Err(CaptionTextOutputError::Source)));Ok(())
                }
                #[test]
                fn stored_caption_edit_batch_invalid_cross_family_noop_duplicate_protected_and_limited_requests_publish_nothing() -> TestResult {
                    let rig=caption_rig(&body(false))?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let ids=selections(&source)?;
                    let texts=requests(&ids);let values=layouts(&ids);let foreign=LogicalId::parse("foreign-caption-edit-batch")?;
                    assert!(matches!(source.prepare_caption_edit_batch_candidate(&provider,&texts,&[Layout {caption_id:&foreign,layout:values[0].layout}],limits()?,WriterLimits::default(),4),Err(E::Output(CaptionTextOutputError::Selection))));
                    assert!(matches!(source.prepare_caption_edit_batch_candidate(&provider,&texts,&[values[0],values[0]],limits()?,WriterLimits::default(),4),Err(E::Output(CaptionTextOutputError::Selection))));
                    let bad=[Request {caption_id:&ids[0].0,text_id:&foreign,replacement:"changed"}];
                    assert!(matches!(source.prepare_caption_edit_batch_candidate(&provider,&bad,&values,limits()?,WriterLimits::default(),4),Err(E::Output(CaptionTextOutputError::Selection))));
                    let bad_layout=[Layout {caption_id:&ids[0].0,layout:CaptionLayout {width_hwpunit:-2,..same_layout()}}];
                    assert!(matches!(source.prepare_caption_edit_batch_candidate(&provider,&texts,&bad_layout,limits()?,WriterLimits::default(),4),Err(E::Output(CaptionTextOutputError::Value))));
                    let no_text=ids.iter().map(|(caption_id,text_id)|Request {caption_id,text_id,replacement:"private caption service text"}).collect::<Vec<_>>();
                    let no_layout=ids.iter().map(|(caption_id,_)|Layout {caption_id,layout:same_layout()}).collect::<Vec<_>>();
                    assert!(matches!(source.prepare_caption_edit_batch_candidate(&provider,&no_text,&no_layout,limits()?,WriterLimits::default(),4),Err(E::Output(CaptionTextOutputError::NoChange))));
                    let tiny=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {text_bytes:1,..Default::default()})?;
                    assert!(matches!(source.prepare_caption_edit_batch_candidate(&provider,&texts,&values,tiny,WriterLimits::default(),4),Err(E::Output(CaptionTextOutputError::Limit))));
                    assert!(matches!(source.prepare_caption_edit_batch_candidate(&provider,&texts,&values,limits()?,WriterLimits::new(hwpx_package::WriterLimitConfig {max_output_bytes:1})?,4),Err(E::Output(CaptionTextOutputError::Writer))));
                    let rig=caption_rig(&body(true))?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let ids=selections(&source)?;let texts=requests(&ids);
                    let blocked=[Layout {caption_id:&ids[2].0,layout:values[0].layout}];
                    assert!(matches!(source.prepare_caption_edit_batch_candidate(&provider,&texts[..1],&blocked,limits()?,WriterLimits::default(),4),Err(E::Output(CaptionTextOutputError::Protection))));Ok(())
                }
            }

        }

        mod layout_output_binding {
            use super::*;
            use hwpx_agent_cli::form_stored_provider::actual_import::{StoredImportedDocumentForms,caption_layout_output::*};
            use hwpx_package::document_import::{forms::ImportedDocumentForms,reference_targets::captions::ImportedReferenceCaptions,
                structure::caption_layout::{CaptionLayout,CaptionLayoutOutputError}};
            use domain_ir::NativeCaptionSide;

            fn target()->CaptionLayout {CaptionLayout {side:NativeCaptionSide::Left,full_size:true,width_hwpunit:80,gap_hwpunit:12,last_width_hwpunit:40}}
            fn selected(source:&StoredImportedDocumentForms)->Result<LogicalId,Box<dyn Error>> {
                Ok(ImportedReferenceCaptions::import(source.imported().body_structure(),limits()?)?.envelopes()[0].logical_caption_id().clone())
            }
            #[test]
            fn stored_caption_layout_read_only_candidate_binds_source_and_reauthorizes_every_exposure() -> TestResult {
                let rig=caption_rig(&caption("BOTTOM"))?;let provider=rig.provider()?;
                let before=rig.metadata.audit_events()?.len();let source=provider.import_actual_forms(rig.head,4)?;let id=selected(&source)?;
                let candidate=source.prepare_caption_layout_candidate(&provider,&id,target(),limits()?,WriterLimits::default(),4)?;
                assert_eq!(&candidate.receipt().source,source.receipt());assert_eq!(candidate.receipt().source_caption_id,id);
                assert_eq!(candidate.receipt().requested_layout,target());assert_eq!(candidate.receipt().output.changed_attributes,5);
                assert!(!candidate.receipt().issuer_execution_publication_authority);
                assert!(!candidate.receipt().output.complete_auxiliary_state_and_protection_verified);
                assert!(!candidate.receipt().output.execution_publication_authority);
                let bytes=candidate.with_verified_bytes(&provider,5,<[u8]>::to_vec)?;
                assert_ne!(bytes,rig.bytes);assert_eq!(<[u8;32]>::from(Sha256::digest(&bytes)),candidate.receipt().output.output_package_sha256);
                let output=ImportedDocumentForms::import(ImportedSourcePackage::import(&bytes,DocumentId::parse("stored-literal-document")?,Sha256::digest(&bytes).into(),SourceImportLimits::default())?)?;
                let caps=ImportedReferenceCaptions::import(output.body_structure(),limits()?)?;assert_eq!(caps.envelopes().len(),1);
                let native=caps.envelopes()[0].native_envelope();assert_eq!(native.side,NativeCaptionSide::Left);
                assert_eq!(native.sub_list_sha256,candidate.receipt().output.preserved_sub_list_sha256);
                let audit=rig.metadata.audit_events()?.len();candidate.with_verified_bytes(&provider,6,|_|())?;
                assert!(rig.metadata.audit_events()?.len()>audit);
                assert!(matches!(candidate.require_current_product_route(&provider,7),Err(StoredCaptionLayoutError::RouteUnqualified)));
                assert_eq!(rig.revisions.head(&rig.revision_context,rig.project,rig.branch)?,rig.head);
                assert_eq!(rig.store.download(&rig.owner,rig.result,8)?,rig.bytes);
                assert!(rig.metadata.audit_events()?[before..].iter().all(|e|matches!(e.event,"artifact.metadata.read"|"artifact.download")));
                let redacted=format!("{candidate:?}{}",String::from_utf8(serde_json::to_vec(candidate.receipt())?)?);
                for private in ["private-caption.hwpx","private caption service text","literal fixture reader"] {assert!(!redacted.contains(private));}Ok(())
            }
            #[test]
            fn stored_caption_layout_acl_revocation_blocks_preparation_verification_and_byte_callback() -> TestResult {
                let rig=caption_rig(&caption("BOTTOM"))?;let provider=rig.provider()?;
                let source=provider.import_actual_forms(rig.head,4)?;let id=selected(&source)?;
                let candidate=source.prepare_caption_layout_candidate(&provider,&id,target(),limits()?,WriterLimits::default(),4)?;
                let _old_proof=source.imported().reconstruct_source_for_verification(&rig.bytes)?;
                rig.store.set_permissions(&rig.owner,rig.result,rig.reader.subject(),BTreeSet::new(),5)?;let called=Cell::new(false);
                assert!(matches!(candidate.with_verified_bytes(&provider,6,|_|called.set(true)),Err(StoredCaptionLayoutError::Source(_))));assert!(!called.get());
                assert!(matches!(candidate.verify(&provider,6),Err(StoredCaptionLayoutError::Source(_))));
                assert!(matches!(candidate.require_current_product_route(&provider,6),Err(StoredCaptionLayoutError::Source(_))));
                assert!(matches!(source.prepare_caption_layout_candidate(&provider,&id,target(),limits()?,WriterLimits::default(),6),Err(StoredCaptionLayoutError::Source(_))));Ok(())
            }
            #[test]
            fn stored_caption_layout_quarantine_or_ciphertext_tamper_blocks_prepared_output() -> TestResult {
                for quarantine in [false,true] {
                    let rig=caption_rig(&caption("BOTTOM"))?;let provider=rig.provider()?;
                    let source=provider.import_actual_forms(rig.head,4)?;let id=selected(&source)?;
                    let candidate=source.prepare_caption_layout_candidate(&provider,&id,target(),limits()?,WriterLimits::default(),4)?;
                    if quarantine {rig.store.quarantine(&rig.owner,rig.result,QuarantineReason::parse("CAPTION_LAYOUT_FIXTURE_QUARANTINE")?,5)?;}
                    else {rig.blob.tamper.store(true,Ordering::SeqCst);}
                    let called=Cell::new(false);assert!(matches!(candidate.with_verified_bytes(&provider,6,|_|called.set(true)),Err(StoredCaptionLayoutError::Source(_))));assert!(!called.get());
                    assert!(source.prepare_caption_layout_candidate(&provider,&id,target(),limits()?,WriterLimits::default(),6).is_err());
                }Ok(())
            }
            #[test]
            fn stored_caption_layout_new_head_invalidates_old_source_even_with_same_result_artifact() -> TestResult {
                let rig=caption_rig(&caption("BOTTOM"))?;let provider=rig.provider()?;
                let source=provider.import_actual_forms(rig.head,4)?;let id=selected(&source)?;
                let candidate=source.prepare_caption_layout_candidate(&provider,&id,target(),limits()?,WriterLimits::default(),4)?;
                rig.advance()?;let called=Cell::new(false);
                assert!(matches!(candidate.with_verified_bytes(&provider,6,|_|called.set(true)),Err(StoredCaptionLayoutError::Source(_))));assert!(!called.get());
                assert!(candidate.verify(&provider,6).is_err());
                assert!(source.prepare_caption_layout_candidate(&provider,&id,target(),limits()?,WriterLimits::default(),6).is_err());Ok(())
            }
            #[test]
            fn stored_caption_layout_foreign_scope_original_proof_and_fresh_bytes_cannot_be_substituted() -> TestResult {
                let rig=caption_rig(&caption("BOTTOM"))?;let provider=rig.provider()?;
                let source=provider.import_actual_forms(rig.head,4)?;let id=selected(&source)?;
                let candidate=source.prepare_caption_layout_candidate(&provider,&id,target(),limits()?,WriterLimits::default(),4)?;
                let foreign=StoredFormProvider::bind(&rig.store,&rig.revisions,&rig.reader,&rig.revision_context,rig.project,rig.branch,DocumentId::parse("foreign-caption-layout-document")?)?;
                let called=Cell::new(false);assert!(candidate.with_verified_bytes(&foreign,6,|_|called.set(true)).is_err());assert!(!called.get());
                assert!(source.prepare_caption_layout_candidate(&foreign,&id,target(),limits()?,WriterLimits::default(),6).is_err());
                let other=provider.import_actual_forms(rig.head,6)?;let proof=source.imported().reconstruct_source_for_verification(&rig.bytes)?;
                assert!(matches!(proof.lower_caption_layout_candidate(other.imported(),&rig.bytes,&id,target(),limits()?,WriterLimits::default()),Err(CaptionLayoutOutputError::Source)));
                let mut wrong=rig.bytes.clone();wrong[0]^=1;
                assert!(matches!(proof.lower_caption_layout_candidate(source.imported(),&wrong,&id,target(),limits()?,WriterLimits::default()),Err(CaptionLayoutOutputError::Source)));Ok(())
            }
            #[test]
            fn stored_caption_layout_keeps_limits_protection_selector_and_noop_rejections() -> TestResult {
                let rig=caption_rig(&caption("BOTTOM"))?;let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;let id=selected(&source)?;
                let tight=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig{input_bytes:1,output_bytes:1,..Default::default()})?;
                assert!(matches!(source.prepare_caption_layout_candidate(&provider,&id,target(),tight,WriterLimits::default(),4),Err(StoredCaptionLayoutError::Output(CaptionLayoutOutputError::Limit))));
                let writer=WriterLimits::new(hwpx_package::WriterLimitConfig{max_output_bytes:1})?;
                assert!(matches!(source.prepare_caption_layout_candidate(&provider,&id,target(),limits()?,writer,4),Err(StoredCaptionLayoutError::Output(CaptionLayoutOutputError::Writer))));
                assert!(matches!(source.prepare_caption_layout_candidate(&provider,&LogicalId::parse("foreign-caption-layout")?,target(),limits()?,WriterLimits::default(),4),Err(StoredCaptionLayoutError::Output(CaptionLayoutOutputError::Selection))));
                let no_change=CaptionLayout{side:NativeCaptionSide::Bottom,full_size:false,width_hwpunit:1200,gap_hwpunit:30,last_width_hwpunit:1100};
                assert!(matches!(source.prepare_caption_layout_candidate(&provider,&id,no_change,limits()?,WriterLimits::default(),4),Err(StoredCaptionLayoutError::Output(CaptionLayoutOutputError::NoChange))));
                let rig=caption_rig(&caption("BOTTOM").replace("<hp:rect id='7'>","<hp:rect id='7' lock='1'>"))?;
                let provider=rig.provider()?;let source=provider.import_actual_forms(rig.head,4)?;
                assert!(matches!(source.prepare_caption_layout_candidate(&provider,&selected(&source)?,target(),limits()?,WriterLimits::default(),4),Err(StoredCaptionLayoutError::Output(CaptionLayoutOutputError::Protection))));Ok(())
            }
        }
    }
}
