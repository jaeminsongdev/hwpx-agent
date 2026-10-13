//! Exact preimage/current typed-model comparison; no native/SQL/product qualification.
use serde_json::{Value, json};
use std::{hint::black_box, time::Instant};
type TestResult = Result<(), Box<dyn std::error::Error>>;

#[allow(dead_code, clippy::expect_used)] // Archived implementation's existing private unit test.
mod baseline {
    include!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../implementation/p09/source-archive/p09-132-pre-comment-catalog-index/crates/domain-ir/src/comment_model.rs"
    ));
    pub fn revalidate(s: &CommentDocumentState, l: CommentLimits) -> Result<(), CommentError> {
        validate_document_state(s, l)
    }
}
#[allow(dead_code, clippy::expect_used)] // Same current source, private validator timing only.
mod embedded {
    include!(concat!(env!("CARGO_MANIFEST_DIR"), "/src/comment_model.rs"));
    pub fn revalidate(s: &CommentDocumentState, l: CommentLimits) -> Result<(), CommentError> {
        validate_document_state(s, l)
    }
}
fn limits() -> Result<domain_ir::CommentLimits, domain_ir::CommentError> {
    domain_ir::CommentLimits::new(domain_ir::CommentLimitConfig {
        input_bytes: 8 * 1024 * 1024,
        output_bytes: 8 * 1024 * 1024,
        ..domain_ir::CommentLimitConfig::default()
    })
}
fn old_limits() -> Result<baseline::CommentLimits, baseline::CommentError> {
    let c = limits()
        .map_err(|_| baseline::CommentError::InvalidLimit)?
        .config();
    baseline::CommentLimits::new(baseline::CommentLimitConfig {
        input_bytes: c.input_bytes,
        output_bytes: c.output_bytes,
        ..baseline::CommentLimitConfig::default()
    })
}
fn fixture() -> Result<Value, Box<dyn std::error::Error>> {
    let s = super::state(false, "section-1")?;
    let mut value: Value = serde_json::from_slice(&s.canonical_json(limits()?)?)?;
    let d = "a".repeat(64);
    value["hidden_explanations"] = json!([{
        "identity":{"logical_explanation_id":"explanation-1"},
        "anchor":value["comments"][0]["anchor"], "native_tag":"hidden_comment", "enabled":true,
        "body_graph_sha256":d,"plain_text_sha256":null,"sub_list_sha256":d,
        "opaque_native_payload_sha256":d,"opaque_properties":[],"locked":false
    }]);
    Ok(value)
}
fn current_state(value: &Value) -> Result<domain_ir::CommentDocumentState, String> {
    domain_ir::CommentDocumentState::from_draft(
        serde_json::from_value(value.clone()).map_err(|_| "decode".to_owned())?,
        limits().map_err(|e| e.code().to_owned())?,
    )
    .map_err(|e| e.code().to_owned())
}
fn old_state(value: &Value) -> Result<baseline::CommentDocumentState, String> {
    baseline::CommentDocumentState::from_draft(
        serde_json::from_value(value.clone()).map_err(|_| "decode".to_owned())?,
        old_limits().map_err(|e| e.code().to_owned())?,
    )
    .map_err(|e| e.code().to_owned())
}
fn admit(value: &Value) -> Result<Vec<u8>, String> {
    current_state(value)?
        .canonical_json(limits().map_err(|e| e.code().to_owned())?)
        .map_err(|e| e.code().to_owned())
}
fn old_admit(value: &Value) -> Result<Vec<u8>, String> {
    old_state(value)?
        .canonical_json(old_limits().map_err(|e| e.code().to_owned())?)
        .map_err(|e| e.code().to_owned())
}
fn parity(value: &Value) {
    // Do not print caller content, author values, payloads or full JSON on mismatch.
    assert!(
        admit(value) == old_admit(value),
        "state_acceptance_or_exact_bytes_changed"
    );
}
fn request_json(value: &Value, operation: Value) -> Result<Value, Box<dyn std::error::Error>> {
    let source = current_state(value)?;
    Ok(
        json!({"schema_version":domain_ir::COMMENT_MODEL_SCHEMA_VERSION,"request_id":"catalog-request",
        "expected_source_state_sha256":source.canonical_sha256(limits()?)?,
        "expected_document_flow_sha256":"b".repeat(64),"target_document_flow_sha256":"b".repeat(64),
        "operation":operation}),
    )
}
fn execute(value: &Value, request: &Value) -> Result<Vec<Vec<u8>>, String> {
    let s = current_state(value)?;
    let l = limits().map_err(|e| e.code().to_owned())?;
    let r = domain_ir::CommentRequest::from_draft(
        serde_json::from_value(request.clone()).map_err(|_| "decode".to_owned())?,
        &s,
        &"b".repeat(64),
        l,
    )
    .map_err(|e| e.code().to_owned())?;
    let p = domain_ir::CommentBuilder::plan(&s, &r, &"b".repeat(64), l)
        .map_err(|e| e.code().to_owned())?;
    let result = domain_ir::CommentBuilder::build(&p, &s, &"b".repeat(64), l)
        .map_err(|e| e.code().to_owned())?;
    Ok(vec![
        r.canonical_json(l).map_err(|e| e.code().to_owned())?,
        p.canonical_json(l).map_err(|e| e.code().to_owned())?,
        result
            .state
            .canonical_json(l)
            .map_err(|e| e.code().to_owned())?,
        serde_json::to_vec(&result.receipt).map_err(|_| "receipt".to_owned())?,
    ])
}
fn old_execute(value: &Value, request: &Value) -> Result<Vec<Vec<u8>>, String> {
    let s = old_state(value)?;
    let l = old_limits().map_err(|e| e.code().to_owned())?;
    let r = baseline::CommentRequest::from_draft(
        serde_json::from_value(request.clone()).map_err(|_| "decode".to_owned())?,
        &s,
        &"b".repeat(64),
        l,
    )
    .map_err(|e| e.code().to_owned())?;
    let p = baseline::CommentBuilder::plan(&s, &r, &"b".repeat(64), l)
        .map_err(|e| e.code().to_owned())?;
    let result = baseline::CommentBuilder::build(&p, &s, &"b".repeat(64), l)
        .map_err(|e| e.code().to_owned())?;
    Ok(vec![
        r.canonical_json(l).map_err(|e| e.code().to_owned())?,
        p.canonical_json(l).map_err(|e| e.code().to_owned())?,
        result
            .state
            .canonical_json(l)
            .map_err(|e| e.code().to_owned())?,
        serde_json::to_vec(&result.receipt).map_err(|_| "receipt".to_owned())?,
    ])
}
fn operations(value: &Value) -> Vec<Value> {
    let mut insert = value["comments"][0].clone();
    insert["identity"] =
        json!({"logical_comment_id":"comment-2","begin_control_id":3,"field_id":4});
    let mut style = value["styles"][1].clone();
    style["width_native_units"] = json!(2836);
    vec![
        json!({"kind":"set_hidden_explanation","target":value["hidden_explanations"][0]["identity"],"enabled":false}),
        json!({"kind":"insert_comment","insertion_index":1,"comment":insert}),
        json!({"kind":"replace_style","style_id":2,"style":style}),
        json!({"kind":"set_visibility","target":value["comments"][0]["identity"],"visibility":"hidden"}),
        json!({"kind":"set_resolution","target":value["comments"][0]["identity"],
            "resolution":{"resolved":true,"resolver_author_id":1,"resolved_at":value["comments"][0]["created_at"]}}),
    ]
}

#[test]
fn validated_catalog_permutations_keep_canonical_order() -> TestResult {
    let mut value = fixture()?;
    for author in [2, 3, 4] {
        let mut row = value["authors"][0].clone();
        row["author_id"] = json!(author);
        value["authors"]
            .as_array_mut()
            .ok_or("fixture_authors")?
            .push(row);
    }
    for _ in 0..4 {
        parity(&value);
        value["authors"]
            .as_array_mut()
            .ok_or("fixture_authors")?
            .rotate_left(1);
        value["styles"]
            .as_array_mut()
            .ok_or("fixture_styles")?
            .reverse();
    }
    value["comments"] = json!([]);
    value["authors"] = json!([]);
    parity(&value);
    assert!(admit(&value).is_ok());
    Ok(())
}
#[test]
fn missing_zero_and_resolver_references_keep_exact_errors() -> TestResult {
    for (pointer, expected) in [
        ("/comments/0/author_id", "comment_invalid_identity"),
        ("/comments/0/style_id", "comment_invalid_identity"),
    ] {
        for id in [0, 9] {
            let mut value = fixture()?;
            *value.pointer_mut(pointer).ok_or("fixture_reference")? = json!(id);
            parity(&value);
            assert!(
                admit(&value) == Err(expected.to_owned()),
                "reference_error_changed"
            );
        }
    }
    for id in [0, 9] {
        let mut value = fixture()?;
        value["comments"][0]["resolution"] = json!({"resolved":true,"resolver_author_id":id,
            "resolved_at":value["comments"][0]["created_at"]});
        parity(&value);
        assert!(admit(&value) == Err("comment_invalid_author_time".to_owned()));
    }
    Ok(())
}
#[test]
fn duplicate_catalog_and_validation_precedence_stay_rejected() -> TestResult {
    for catalog in ["authors", "styles", "sections"] {
        let mut value = fixture()?;
        let row = value[catalog][0].clone();
        value[catalog]
            .as_array_mut()
            .ok_or("fixture_catalog")?
            .push(row);
        value["comments"][0]["author_id"] = json!(0);
        parity(&value);
        assert!(admit(&value).is_err());
    }
    let mut value = fixture()?;
    value["authors"][0]["name_sha256"] = json!("invalid");
    value["styles"][0]["style_id"] = json!(0);
    parity(&value);
    assert!(admit(&value) == Err("comment_invalid_author_time".to_owned()));
    Ok(())
}
#[test]
fn payload_native_time_anchor_and_identity_rejections_are_unchanged() -> TestResult {
    for (pointer, replacement) in [
        ("/comments/0/body_graph_sha256", json!("invalid")),
        ("/comments/0/parameters_sha256", json!("invalid")),
        ("/comments/0/identity/field_id", json!(0)),
        ("/comments/0/identity/begin_control_id", json!(0)),
        ("/comments/0/anchor/section_id", json!("missing-section")),
        ("/comments/0/anchor/start/inline_ordinal", json!(2)),
        (
            "/comments/0/created_at/original_utc_offset_minutes",
            json!(841),
        ),
        (
            "/comments/0/modified_at",
            json!({"epoch_millis":1,"original_utc_offset_minutes":0}),
        ),
        ("/comments/0/resolution/resolved", json!(true)),
        (
            "/comments/0/opaque_properties",
            json!([{"namespace":"bad namespace","name":"x","value_sha256":"a".repeat(64)}]),
        ),
        ("/sections/0/memo_shape_id_ref", json!(9)),
        ("/styles/0/width_native_units", json!(0)),
    ] {
        let mut value = fixture()?;
        *value.pointer_mut(pointer).ok_or("fixture_mutation")? = replacement;
        parity(&value);
        assert!(admit(&value).is_err(), "invalid_state_accepted");
    }
    Ok(())
}
#[test]
fn all_five_operations_keep_request_plan_result_receipt_bytes() -> TestResult {
    let value = fixture()?;
    for op in operations(&value) {
        let r = request_json(&value, op)?;
        let current = execute(&value, &r);
        assert!(current.is_ok(), "valid_operation_failed");
        assert!(
            current == old_execute(&value, &r),
            "request_plan_result_or_receipt_changed"
        );
    }
    Ok(())
}
#[test]
fn protected_noop_stale_and_operation_references_keep_errors() -> TestResult {
    let original = fixture()?;
    for (pointer, replacement) in [
        ("/document_locked", json!(true)),
        ("/sections/0/locked", json!(true)),
        ("/comments/0/locked", json!(true)),
    ] {
        let mut value = original.clone();
        *value.pointer_mut(pointer).ok_or("fixture_protection")? = replacement;
        for op in operations(&value) {
            let r = request_json(&value, op)?;
            assert!(
                execute(&value, &r) == old_execute(&value, &r),
                "operation_protection_changed"
            );
        }
    }
    let mut r = request_json(&original, operations(&original)[1].clone())?;
    r["operation"]["comment"]["author_id"] = json!(9);
    assert!(execute(&original, &r) == Err("comment_invalid_identity".to_owned()));
    assert!(execute(&original, &r) == old_execute(&original, &r));
    r = request_json(&original, operations(&original)[4].clone())?;
    r["operation"]["resolution"]["resolver_author_id"] = json!(9);
    assert!(execute(&original, &r) == Err("comment_invalid_author_time".to_owned()));
    assert!(execute(&original, &r) == old_execute(&original, &r));
    r["expected_source_state_sha256"] = json!("c".repeat(64));
    assert!(execute(&original, &r) == old_execute(&original, &r));
    r = request_json(
        &original,
        json!({"kind":"set_visibility","target":original["comments"][0]["identity"],"visibility":"shown"}),
    )?;
    assert!(execute(&original, &r) == Err("comment_noop".to_owned()));
    assert!(execute(&original, &r) == old_execute(&original, &r));
    Ok(())
}
#[test]
fn configured_output_bound_is_not_relaxed() -> TestResult {
    let value = fixture()?;
    let current = domain_ir::CommentDocumentState::from_draft(
        serde_json::from_value(value.clone())?,
        domain_ir::CommentLimits::new(domain_ir::CommentLimitConfig {
            input_bytes: 128,
            output_bytes: 128,
            ..domain_ir::CommentLimitConfig::default()
        })?,
    );
    let old = baseline::CommentDocumentState::from_draft(
        serde_json::from_value(value)?,
        baseline::CommentLimits::new(baseline::CommentLimitConfig {
            input_bytes: 128,
            output_bytes: 128,
            ..baseline::CommentLimitConfig::default()
        })?,
    );
    assert!(matches!(current, Err(domain_ir::CommentError::OutputLimit)));
    assert!(matches!(old, Err(baseline::CommentError::OutputLimit)));
    Ok(())
}
fn large_fixture() -> Result<Value, Box<dyn std::error::Error>> {
    let mut value = fixture()?;
    let author = value["authors"][0].clone();
    let style = value["styles"][0].clone();
    let comment = value["comments"][0].clone();
    value["authors"] = json!([]);
    value["styles"] = json!([]);
    value["comments"] = json!([]);
    for id in 1..=4096 {
        let mut a = author.clone();
        a["author_id"] = json!(id);
        value["authors"]
            .as_array_mut()
            .ok_or("fixture_authors")?
            .push(a);
        let mut s = style.clone();
        s["style_id"] = json!(id);
        value["styles"]
            .as_array_mut()
            .ok_or("fixture_styles")?
            .push(s);
    }
    for id in 1..=2048 {
        let mut c = comment.clone();
        c["identity"] =
            json!({"logical_comment_id":format!("large-{id}"),"begin_control_id":id,"field_id":id});
        c["author_id"] = json!(4096);
        c["style_id"] = json!(4096);
        c["resolution"] =
            json!({"resolved":true,"resolver_author_id":4096,"resolved_at":c["created_at"]});
        value["comments"]
            .as_array_mut()
            .ok_or("fixture_comments")?
            .push(c);
    }
    Ok(value)
}
#[test]
fn large_validated_catalog_preserves_exact_public_state() -> TestResult {
    let value = large_fixture()?;
    assert!(admit(&value).is_ok(), "large_fixture_over_bound");
    parity(&value);
    Ok(())
}
#[test]
fn isolated_validator_profile_records_actual_before_after_only() -> TestResult {
    let value = large_fixture()?;
    let old = old_state(&value)?;
    let el = embedded::CommentLimits::new(embedded::CommentLimitConfig {
        input_bytes: 8 * 1024 * 1024,
        output_bytes: 8 * 1024 * 1024,
        ..embedded::CommentLimitConfig::default()
    })?;
    let current = embedded::CommentDocumentState::from_draft(serde_json::from_value(value)?, el)?;
    baseline::revalidate(&old, old_limits()?)?;
    embedded::revalidate(&current, el)?;
    let mut old_ns = Vec::new();
    let mut new_ns = Vec::new();
    for round in 0..7 {
        // Alternate order; samples exclude decode, allocation, canonical serialization and I/O.
        for before in if round % 2 == 0 {
            [true, false]
        } else {
            [false, true]
        } {
            let start = Instant::now();
            if before {
                baseline::revalidate(black_box(&old), old_limits()?)?;
            } else {
                embedded::revalidate(black_box(&current), el)?;
            }
            let elapsed = start.elapsed().as_nanos();
            if before {
                old_ns.push(elapsed)
            } else {
                new_ns.push(elapsed)
            }
        }
    }
    println!(
        "P132_CATALOG_PROFILE:{}",
        json!({"schema":"hwpx-agent.p09-comment-catalog-profile/v1",
        "scope":"isolated_validate_document_state_not_end_to_end", "authors":4096,"styles":4096,"comments":2048,
        "rounds":7,"before_ns":old_ns,"after_ns":new_ns,"native_verified":false,"product_complete":false})
    );
    Ok(())
}
