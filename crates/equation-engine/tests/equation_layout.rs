use std::error::Error;

use domain_ir::{
    MATH_AST_NORMALIZATION_VERSION, MATH_AST_SCHEMA_VERSION, MathAst, MathAstDraft, MathAstLimits,
    MathExpression, MathNode, MathSourceSpan,
};
use equation_engine::{
    EQUATION_LAYOUT_PROFILE_VERSION, EQUATION_LAYOUT_QUALIFICATION_SCHEMA_VERSION,
    EquationLayoutError, EquationLayoutEstimator, EquationLayoutLimitConfig, EquationLayoutLimits,
    EquationLayoutMode, EquationLayoutSource,
};
use serde_json::{Value, json};
use sha2::{Digest as _, Sha256};

type TestResult = Result<(), Box<dyn Error>>;

fn ast(value: &str) -> MathAstDraft {
    let length = u32::try_from(value.len()).unwrap_or_default();
    MathAstDraft {
        schema_version: MATH_AST_SCHEMA_VERSION.to_owned(),
        normalization_version: MATH_AST_NORMALIZATION_VERSION.to_owned(),
        source_length_bytes: length,
        root: MathNode {
            span: MathSourceSpan {
                start_byte: 0,
                end_byte: length,
            },
            style: None,
            expression: MathExpression::Identifier {
                name: value.to_owned(),
            },
        },
    }
}

fn fraction() -> MathAstDraft {
    MathAstDraft {
        schema_version: MATH_AST_SCHEMA_VERSION.to_owned(),
        normalization_version: MATH_AST_NORMALIZATION_VERSION.to_owned(),
        source_length_bytes: 3,
        root: MathNode {
            span: MathSourceSpan {
                start_byte: 0,
                end_byte: 3,
            },
            style: None,
            expression: MathExpression::Fraction {
                numerator: Box::new(MathNode {
                    span: MathSourceSpan {
                        start_byte: 0,
                        end_byte: 1,
                    },
                    style: None,
                    expression: MathExpression::Identifier {
                        name: "x".to_owned(),
                    },
                }),
                denominator: Box::new(MathNode {
                    span: MathSourceSpan {
                        start_byte: 2,
                        end_byte: 3,
                    },
                    style: None,
                    expression: MathExpression::Identifier {
                        name: "y".to_owned(),
                    },
                }),
            },
        },
    }
}

fn semantic(value: &str) -> String {
    let Ok(normalized) = MathAst::from_draft(ast(value), MathAstLimits::default()) else {
        return String::new();
    };
    let Ok(digest) = normalized.semantic_sha256(MathAstLimits::default()) else {
        return String::new();
    };
    hex::encode(digest)
}

fn qualification_value() -> Value {
    let mut samples = Vec::new();
    for mode in ["inline", "display"] {
        for index in 0..4 {
            samples.push(json!({
                "semantic_sha256": semantic(&format!("x{index}")),
                "layout": mode,
                "base_unit": 1000,
                "width_hwpunit": 2000,
                "height_hwpunit": 1000,
                "baseline_percent": if mode == "inline" { 84 } else { 86 },
                "native_readback_sha256": "a".repeat(64),
                "render_evidence_sha256": "b".repeat(64),
                "metrics": {
                    "advance_units": 2,
                    "above_levels": 0,
                    "below_levels": 0,
                    "nodes": 1,
                    "depth": 1,
                    "matrix_rows": 0,
                    "matrix_columns": 0
                },
                "ink_box": {
                    "page_width_pixels": 1488,
                    "page_height_pixels": 2103,
                    "left": 100,
                    "top": 100,
                    "width": 200,
                    "height": 80,
                    "dpi": 180
                }
            }));
        }
    }
    json!({
        "schema_version": EQUATION_LAYOUT_QUALIFICATION_SCHEMA_VERSION,
        "profile_version": EQUATION_LAYOUT_PROFILE_VERSION,
        "target": {
            "build": "11.0.0.9136",
            "architecture": "x86",
            "locale": "ko-KR",
            "font_name": "HancomEQN"
        },
        "evidence_sha256": "c".repeat(64),
        "font_metrics_sha256": "d".repeat(64),
        "corpus_semantic_sha256": "e".repeat(64),
        "model": {
            "width_per_advance_milli": 500,
            "horizontal_padding_milli": 1000,
            "line_height_milli": 1000,
            "vertical_level_milli": 400,
            "inline_baseline_percent": 84,
            "display_baseline_percent": 86
        },
        "envelope": {
            "maximum_nodes": 64,
            "maximum_depth": 16,
            "maximum_advance_units": 8,
            "maximum_vertical_levels": 8,
            "maximum_matrix_rows": 4,
            "maximum_matrix_columns": 4
        },
        "validation": {
            "sample_count": 8,
            "inline_sample_count": 4,
            "display_sample_count": 4,
            "extent_max_error_hwpunit": 0,
            "baseline_max_error_hwpunit": 0,
            "ink_box_overflow_count": 0,
            "clipping_count": 0,
            "overlap_count": 0,
            "silent_fallback_count": 0,
            "all_pages_inspected": true
        },
        "exact_samples": samples
    })
}

fn qualified(value: &Value) -> Result<EquationLayoutEstimator, EquationLayoutError> {
    let bytes = serde_json::to_vec(value).unwrap_or_default();
    let digest = hex::encode(Sha256::digest(&bytes));
    EquationLayoutEstimator::from_qualification_json(
        EquationLayoutLimits::default(),
        MathAstLimits::default(),
        &bytes,
        &digest,
    )
}

#[test]
fn unqualified_estimates_are_conservative_provisional_and_render_required() -> TestResult {
    let estimator = EquationLayoutEstimator::provisional(
        EquationLayoutLimits::default(),
        MathAstLimits::default(),
    );
    let simple = estimator.estimate(ast("x"), EquationLayoutMode::Inline, 1000)?;
    assert_eq!(simple.source(), EquationLayoutSource::Provisional);
    assert_eq!(simple.width_hwpunit(), 1700);
    assert_eq!(simple.height_hwpunit(), 1600);
    assert_eq!(simple.baseline_percent(), 85);
    assert!(simple.render_required());
    assert_eq!(simple.source_evidence_sha256(), None);

    let fraction = estimator.estimate(fraction(), EquationLayoutMode::Display, 1000)?;
    assert_eq!(fraction.width_hwpunit(), 3100);
    assert_eq!(fraction.height_hwpunit(), 3400);
    assert!(fraction.render_required());
    Ok(())
}

#[test]
fn structural_metrics_are_exposed_without_reimplementing_the_model() -> TestResult {
    let estimator = EquationLayoutEstimator::provisional(
        EquationLayoutLimits::default(),
        MathAstLimits::default(),
    );
    let metrics = estimator.measure(ast("abc"))?;
    assert_eq!(metrics.advance_units(), 3);
    assert_eq!(metrics.above_levels(), 0);
    assert_eq!(metrics.below_levels(), 0);
    assert_eq!(metrics.nodes(), 1);
    assert_eq!(metrics.depth(), 1);
    assert_eq!(metrics.matrix_rows(), 0);
    assert_eq!(metrics.matrix_columns(), 0);
    assert_eq!(
        serde_json::to_value(metrics)?,
        json!({
            "advance_units": 3,
            "above_levels": 0,
            "below_levels": 0,
            "nodes": 1,
            "depth": 1,
            "matrix_rows": 0,
            "matrix_columns": 0
        })
    );
    Ok(())
}

#[test]
fn exact_sample_uses_target_readback_without_recomputing_extent() -> TestResult {
    let estimator = qualified(&qualification_value())?;
    let result = estimator.estimate(ast("x0"), EquationLayoutMode::Inline, 1000)?;
    assert_eq!(result.source(), EquationLayoutSource::TargetReadback);
    assert_eq!(result.width_hwpunit(), 2000);
    assert_eq!(result.height_hwpunit(), 1000);
    assert_eq!(result.baseline_percent(), 84);
    assert_eq!(
        result.source_evidence_sha256(),
        Some("c".repeat(64).as_str())
    );
    assert!(!result.render_required());
    Ok(())
}

#[test]
fn qualified_model_is_used_only_inside_its_complete_envelope() -> TestResult {
    let estimator = qualified(&qualification_value())?;
    let admitted = estimator.estimate(ast("z"), EquationLayoutMode::Display, 1000)?;
    assert_eq!(admitted.source(), EquationLayoutSource::VerifiedEstimator);
    assert_eq!(admitted.width_hwpunit(), 1500);
    assert_eq!(admitted.height_hwpunit(), 1000);
    assert_eq!(admitted.baseline_percent(), 86);
    assert!(!admitted.render_required());

    let outside = estimator.estimate(ast("abcdefghijklmnop"), EquationLayoutMode::Display, 1000)?;
    assert_eq!(outside.source(), EquationLayoutSource::Provisional);
    assert!(outside.render_required());
    assert_eq!(outside.source_evidence_sha256(), None);
    Ok(())
}

#[test]
fn qualification_digest_schema_visual_and_sample_tamper_fail_closed() {
    let value = qualification_value();
    let bytes = serde_json::to_vec(&value).unwrap_or_default();
    assert_eq!(
        EquationLayoutEstimator::from_qualification_json(
            EquationLayoutLimits::default(),
            MathAstLimits::default(),
            &bytes,
            &"0".repeat(64),
        )
        .err(),
        Some(EquationLayoutError::UntrustedQualification)
    );

    for mutation in [
        |value: &mut Value| value["validation"]["clipping_count"] = json!(1),
        |value: &mut Value| value["target"]["build"] = json!("11.0.0.9999"),
        |value: &mut Value| value["exact_samples"][1] = value["exact_samples"][0].clone(),
        |value: &mut Value| value["exact_samples"][0]["ink_box"]["width"] = json!(1488),
    ] {
        let mut changed = qualification_value();
        mutation(&mut changed);
        assert!(qualified(&changed).is_err());
    }
}

#[test]
fn malformed_duplicate_unknown_and_oversized_qualification_fail() -> TestResult {
    for bytes in [
        Vec::new(),
        br#"{"schema_version":"a","schema_version":"b"}"#.to_vec(),
        br#"{"unknown":true}"#.to_vec(),
    ] {
        let digest = hex::encode(Sha256::digest(&bytes));
        assert!(
            EquationLayoutEstimator::from_qualification_json(
                EquationLayoutLimits::default(),
                MathAstLimits::default(),
                &bytes,
                &digest,
            )
            .is_err()
        );
    }
    let limits = EquationLayoutLimits::new(EquationLayoutLimitConfig {
        qualification_bytes: 8,
        ..EquationLayoutLimitConfig::default()
    })?;
    let bytes = vec![b'x'; 9];
    let digest = hex::encode(Sha256::digest(&bytes));
    assert_eq!(
        EquationLayoutEstimator::from_qualification_json(
            limits,
            MathAstLimits::default(),
            &bytes,
            &digest,
        )
        .err(),
        Some(EquationLayoutError::QualificationLimit)
    );
    Ok(())
}

#[test]
fn limits_base_unit_and_ast_failure_are_typed() {
    assert_eq!(
        EquationLayoutLimits::new(EquationLayoutLimitConfig {
            samples: 7,
            ..EquationLayoutLimitConfig::default()
        }),
        Err(EquationLayoutError::InvalidLimit)
    );
    let estimator = EquationLayoutEstimator::provisional(
        EquationLayoutLimits::default(),
        MathAstLimits::default(),
    );
    assert_eq!(
        estimator.estimate(ast("x"), EquationLayoutMode::Inline, 0),
        Err(EquationLayoutError::InvalidBaseUnit)
    );
    let mut invalid = ast("x");
    invalid.root.span.end_byte = 2;
    assert_eq!(
        estimator.estimate(invalid, EquationLayoutMode::Inline, 1000),
        Err(EquationLayoutError::MathAst)
    );
}

#[test]
fn receipt_is_deterministic_bounded_and_debug_is_redacted() -> TestResult {
    let estimator = qualified(&qualification_value())?;
    let result = estimator.estimate(ast("private_name"), EquationLayoutMode::Inline, 1000)?;
    let repeated = estimator.estimate(ast("private_name"), EquationLayoutMode::Inline, 1000)?;
    assert_eq!(
        result.canonical_json(EquationLayoutLimits::default())?,
        repeated.canonical_json(EquationLayoutLimits::default())?
    );
    let debug = format!("{result:?}");
    assert!(!debug.contains("private_name"));
    assert!(!debug.contains(&"c".repeat(64)));
    assert!(!debug.contains("1000"));
    Ok(())
}

#[test]
fn public_error_codes_are_stable() {
    let cases = [
        (
            EquationLayoutError::InvalidLimit,
            "equation_layout_invalid_limit",
        ),
        (
            EquationLayoutError::QualificationLimit,
            "equation_layout_qualification_limit",
        ),
        (
            EquationLayoutError::InvalidQualification,
            "equation_layout_invalid_qualification",
        ),
        (
            EquationLayoutError::UntrustedQualification,
            "equation_layout_untrusted_qualification",
        ),
        (
            EquationLayoutError::UnsupportedProfile,
            "equation_layout_unsupported_profile",
        ),
        (
            EquationLayoutError::FailedVisualQualification,
            "equation_layout_failed_visual_qualification",
        ),
        (
            EquationLayoutError::InvalidBaseUnit,
            "equation_layout_invalid_base_unit",
        ),
        (EquationLayoutError::MathAst, "equation_layout_math_ast"),
        (
            EquationLayoutError::MetricLimit,
            "equation_layout_metric_limit",
        ),
        (
            EquationLayoutError::MetricOverflow,
            "equation_layout_metric_overflow",
        ),
        (
            EquationLayoutError::OutputLimit,
            "equation_layout_output_limit",
        ),
        (
            EquationLayoutError::Serialization,
            "equation_layout_serialization",
        ),
    ];
    for (error, code) in cases {
        assert_eq!(error.code(), code);
    }
}
