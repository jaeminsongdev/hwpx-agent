use std::error::Error;

use domain_ir::{MathAstLimits, MathExpression, MathLargeOperator, MathOperator};
use equation_engine::{
    MATHML_ADAPTER_SCHEMA_VERSION, MATHML_NAMESPACE, MathMlAdapter, MathMlAdapterError,
    MathMlAdapterLimitConfig, MathMlAdapterLimits, MathMlParseRequestDraft, MathMlSourceProfile,
};

type TestResult = Result<(), Box<dyn Error>>;

fn limits() -> Result<MathMlAdapterLimits, MathMlAdapterError> {
    MathMlAdapterLimits::new(MathMlAdapterLimitConfig::default())
}

fn adapter() -> Result<MathMlAdapter, MathMlAdapterError> {
    MathMlAdapter::new(limits()?, MathAstLimits::default())
}

fn document(body: &str) -> String {
    format!(r#"<math xmlns="{MATHML_NAMESPACE}">{body}</math>"#)
}

fn parse(source: &str) -> Result<equation_engine::MathMlParseResult, MathMlAdapterError> {
    adapter()?.parse(MathMlParseRequestDraft {
        schema_version: MATHML_ADAPTER_SCHEMA_VERSION.to_owned(),
        source: source.to_owned(),
    })
}

fn assert_code(source: &str, code: &str) {
    let Err(error) = parse(source) else {
        panic!("invalid MathML was accepted");
    };
    assert_eq!(error.code(), code);
}

#[test]
fn presentation_and_content_roundtrip_corpus_is_semantically_exact() -> TestResult {
    let corpus = [
        (
            "<mrow><mn>1</mn><mo>+</mo><mn>2</mn></mrow>",
            "<apply><plus/><cn>1</cn><cn>2</cn></apply>",
        ),
        (
            "<mrow><mn>5</mn><mo>−</mo><mn>3</mn></mrow>",
            "<apply><minus/><cn>5</cn><cn>3</cn></apply>",
        ),
        (
            "<mrow><mo>−</mo><mi>x</mi></mrow>",
            "<apply><minus/><ci>x</ci></apply>",
        ),
        (
            "<mrow><mi>x</mi><mo>&#x2062;</mo><mi>y</mi></mrow>",
            "<apply><times/><ci>x</ci><ci>y</ci></apply>",
        ),
        (
            "<mfrac><mi>x</mi><mn>2</mn></mfrac>",
            "<apply><divide/><ci>x</ci><cn>2</cn></apply>",
        ),
        (
            "<msup><mi>x</mi><mn>2</mn></msup>",
            "<apply><power/><ci>x</ci><cn>2</cn></apply>",
        ),
        (
            "<msqrt><mi>x</mi></msqrt>",
            "<apply><root/><ci>x</ci></apply>",
        ),
        (
            "<mroot><mi>x</mi><mn>3</mn></mroot>",
            "<apply><root/><degree><cn>3</cn></degree><ci>x</ci></apply>",
        ),
        (
            "<mrow><mi>x</mi><mo>≤</mo><mi>y</mi></mrow>",
            "<apply><leq/><ci>x</ci><ci>y</ci></apply>",
        ),
        (
            "<mrow><mi>p</mi><mo>∧</mo><mi>q</mi></mrow>",
            "<apply><and/><ci>p</ci><ci>q</ci></apply>",
        ),
        (
            "<mrow><mo>¬</mo><mi>p</mi></mrow>",
            "<apply><not/><ci>p</ci></apply>",
        ),
        (
            "<mrow><mi>sin</mi><mo>&#x2061;</mo><mfenced><mi>x</mi></mfenced></mrow>",
            "<apply><sin/><ci>x</ci></apply>",
        ),
        (
            "<mrow><mi>x</mi><mo>!</mo></mrow>",
            "<apply><factorial/><ci>x</ci></apply>",
        ),
        ("<mi>π</mi>", "<pi/>"),
        (
            "<mrow><munderover><mo>∑</mo><mn>1</mn><mi>n</mi></munderover><mi>x</mi></mrow>",
            "<apply><sum/><lowlimit><cn>1</cn></lowlimit><uplimit><ci>n</ci></uplimit><ci>x</ci></apply>",
        ),
        (
            "<mrow><munderover><mo>∫</mo><mn>0</mn><mn>1</mn></munderover><mi>x</mi></mrow>",
            "<apply><int/><lowlimit><cn>0</cn></lowlimit><uplimit><cn>1</cn></uplimit><ci>x</ci></apply>",
        ),
        (
            "<mtable><mtr><mtd><mn>1</mn></mtd><mtd><mn>2</mn></mtd></mtr><mtr><mtd><mn>3</mn></mtd><mtd><mn>4</mn></mtd></mtr></mtable>",
            "<matrix><matrixrow><cn>1</cn><cn>2</cn></matrixrow><matrixrow><cn>3</cn><cn>4</cn></matrixrow></matrix>",
        ),
    ];

    for (presentation, content) in corpus {
        let presentation = parse(&document(presentation))?;
        let content = parse(&document(content))?;
        assert_eq!(
            presentation.source_profile(),
            MathMlSourceProfile::Presentation
        );
        assert_eq!(content.source_profile(), MathMlSourceProfile::Content);
        assert!(
            presentation.ast().semantically_eq(content.ast()),
            "semantic mismatch: {presentation:?} / {content:?}"
        );
    }
    Ok(())
}

#[test]
fn presentation_structures_styles_accents_and_named_functions_are_typed() -> TestResult {
    let styled = parse(&document(
        r##"<mstyle mathvariant="bold" mathcolor="#1020f0"><mi>x</mi></mstyle>"##,
    ))?;
    assert!(styled.ast().root().style.is_some());

    let accent = parse(&document(
        "<mover accent=\"true\"><mi>v</mi><mo>→</mo></mover>",
    ))?;
    assert!(matches!(
        accent.ast().root().expression,
        MathExpression::Accent { .. }
    ));

    let function = parse(&document(
        "<mrow><mi>velocity</mi><mo>&#x2061;</mo><mi>t</mi></mrow>",
    ))?;
    assert!(matches!(
        &function.ast().root().expression,
        MathExpression::Function { function, .. }
            if matches!(function, domain_ir::MathFunction::Named { name } if name == "velocity")
    ));

    let script = parse(&document(
        "<msubsup><mi>x</mi><mi>i</mi><mn>2</mn></msubsup>",
    ))?;
    assert!(matches!(
        script.ast().root().expression,
        MathExpression::Script {
            subscript: Some(_),
            superscript: Some(_),
            ..
        }
    ));
    Ok(())
}

#[test]
fn content_derivative_set_and_large_operator_are_typed() -> TestResult {
    let derivative = parse(&document(
        "<apply><partialdiff/><bvar><ci>x</ci><degree><cn>2</cn></degree></bvar><bvar><ci>y</ci></bvar><ci>f</ci></apply>",
    ))?;
    assert!(matches!(
        &derivative.ast().root().expression,
        MathExpression::Derivative { variables, .. }
            if variables.len() == 2 && variables[0].order == 2 && variables[1].order == 1
    ));

    let set = parse(&document(
        "<set><bvar><ci>x</ci></bvar><condition><apply><gt/><ci>x</ci><cn>0</cn></apply></condition></set>",
    ))?;
    assert!(matches!(
        set.ast().root().expression,
        MathExpression::SetBuilder { .. }
    ));

    let limit = parse(&document(
        "<apply><limit/><lowlimit><ci>a</ci></lowlimit><ci>f</ci></apply>",
    ))?;
    assert!(matches!(
        limit.ast().root().expression,
        MathExpression::LargeOperator {
            operator: MathLargeOperator::Limit,
            lower: Some(_),
            ..
        }
    ));
    Ok(())
}

#[test]
fn namespace_declaration_and_entity_security_fail_closed() {
    let cases = [
        (
            "<!DOCTYPE math><math xmlns=\"http://www.w3.org/1998/Math/MathML\"><mi>x</mi></math>",
            "mathml_adapter_dtd_forbidden",
        ),
        (
            "<math xmlns=\"http://www.w3.org/1998/Math/MathML\"><mi>&custom;</mi></math>",
            "mathml_adapter_entity_forbidden",
        ),
        (
            "<?target data?><math xmlns=\"http://www.w3.org/1998/Math/MathML\"><mi>x</mi></math>",
            "mathml_adapter_pi_forbidden",
        ),
        (
            "<math xmlns=\"http://www.w3.org/1998/Math/MathML\"><mi><![CDATA[x]]></mi></math>",
            "mathml_adapter_cdata_forbidden",
        ),
        (
            "<math xmlns=\"http://www.w3.org/1998/Math/MathML\"><!--x--><mi>x</mi></math>",
            "mathml_adapter_unsupported_element",
        ),
        (
            "<?xml version=\"1.1\"?><math xmlns=\"http://www.w3.org/1998/Math/MathML\"><mi>x</mi></math>",
            "mathml_adapter_encoding_forbidden",
        ),
        (
            "<?xml version=\"1.0\" encoding=\"EUC-KR\"?><math xmlns=\"http://www.w3.org/1998/Math/MathML\"><mi>x</mi></math>",
            "mathml_adapter_encoding_forbidden",
        ),
        (
            "<math><mi>x</mi></math>",
            "mathml_adapter_namespace_invalid",
        ),
        (
            "<math xmlns=\"urn:not-mathml\"><mi>x</mi></math>",
            "mathml_adapter_namespace_invalid",
        ),
        (
            "<m:math xmlns:m=\"http://www.w3.org/1998/Math/MathML\" xmlns:x=\"urn:foreign\"><m:mi>x</m:mi></m:math>",
            "mathml_adapter_namespace_invalid",
        ),
        (
            "<math xmlns=\"http://www.w3.org/1998/Math/MathML\"><x:mi xmlns:x=\"urn:foreign\">x</x:mi></math>",
            "mathml_adapter_namespace_invalid",
        ),
    ];
    for (source, code) in cases {
        assert_code(source, code);
    }

    let numeric = parse(&document("<mi>&#x3b1;</mi>"));
    assert!(numeric.is_ok());
    let prefixed = parse(&format!(
        r#"<m:math xmlns:m="{MATHML_NAMESPACE}"><m:mi>x</m:mi></m:math>"#
    ));
    assert!(prefixed.is_ok());
}

#[test]
fn mixed_unsupported_ambiguous_and_malformed_shapes_fail_closed() {
    let cases = [
        (
            document("<mrow><mi>x</mi></mrow><apply><plus/><cn>1</cn><cn>2</cn></apply>"),
            "mathml_adapter_mixed_profile",
        ),
        (
            document("<mrow><mi>x</mi><mi>y</mi></mrow>"),
            "mathml_adapter_ambiguous_presentation",
        ),
        (
            document("<mrow><mi>x</mi><mo>&lt;</mo><mi>y</mi><mo>&lt;</mo><mi>z</mi></mrow>"),
            "mathml_adapter_ambiguous_presentation",
        ),
        (
            document("<semantics><mi>x</mi></semantics>"),
            "mathml_adapter_unsupported_element",
        ),
        (
            document("<mi intent=\"x\">x</mi>"),
            "mathml_adapter_unsupported_attribute",
        ),
        (
            document("<mi mathvariant=\"bold\" mathvariant=\"italic\">x</mi>"),
            "mathml_adapter_xml_malformed",
        ),
        (
            document("<mfrac><mi>x</mi></mfrac>"),
            "mathml_adapter_invalid_structure",
        ),
        (
            document("<mover><mi>x</mi><mo>→</mo></mover>"),
            "mathml_adapter_unsupported_attribute",
        ),
        (
            document("<apply><plus/><cn>1</cn></apply>"),
            "mathml_adapter_invalid_structure",
        ),
        (
            document(
                "<matrix><matrixrow><cn>1</cn></matrixrow><matrixrow><cn>2</cn><cn>3</cn></matrixrow></matrix>",
            ),
            "mathml_adapter_invalid_structure",
        ),
        (
            document("<apply><diff/><ci>x</ci></apply>"),
            "mathml_adapter_invalid_structure",
        ),
        (
            document("<apply><sum/><ci>x</ci><lowlimit><cn>1</cn></lowlimit></apply>"),
            "mathml_adapter_invalid_structure",
        ),
        (document("<mi> x </mi>"), "mathml_adapter_invalid_token"),
    ];
    for (source, code) in cases {
        assert_code(&source, code);
    }
}

#[test]
fn finite_xml_resource_limits_are_enforced() -> TestResult {
    let bounded_cases = [
        (
            MathMlAdapterLimitConfig {
                source_bytes: 64,
                text_bytes: 64,
                total_text_bytes: 64,
                ..MathMlAdapterLimitConfig::default()
            },
            document("<mi>x</mi>"),
            MathMlAdapterError::InputLimit,
        ),
        (
            MathMlAdapterLimitConfig {
                events: 2,
                ..MathMlAdapterLimitConfig::default()
            },
            document("<mi>x</mi>"),
            MathMlAdapterError::XmlLimit,
        ),
        (
            MathMlAdapterLimitConfig {
                elements: 1,
                ..MathMlAdapterLimitConfig::default()
            },
            document("<mi>x</mi>"),
            MathMlAdapterError::XmlLimit,
        ),
        (
            MathMlAdapterLimitConfig {
                text_bytes: 1,
                ..MathMlAdapterLimitConfig::default()
            },
            document("<mi>xx</mi>"),
            MathMlAdapterError::XmlLimit,
        ),
        (
            MathMlAdapterLimitConfig {
                text_bytes: 1,
                total_text_bytes: 1,
                ..MathMlAdapterLimitConfig::default()
            },
            document("<mrow><mi>x</mi><mo>+</mo><mi>y</mi></mrow>"),
            MathMlAdapterError::XmlLimit,
        ),
        (
            MathMlAdapterLimitConfig {
                attributes_per_element: 1,
                ..MathMlAdapterLimitConfig::default()
            },
            document("<mi mathvariant=\"bold\" mathcolor=\"#000000\">x</mi>"),
            MathMlAdapterError::XmlLimit,
        ),
        (
            MathMlAdapterLimitConfig {
                attribute_bytes: 16,
                ..MathMlAdapterLimitConfig::default()
            },
            document("<mi>x</mi>"),
            MathMlAdapterError::XmlLimit,
        ),
        (
            MathMlAdapterLimitConfig {
                namespace_bindings: 1,
                ..MathMlAdapterLimitConfig::default()
            },
            format!(
                r#"<math xmlns="{MATHML_NAMESPACE}" xmlns:m="{MATHML_NAMESPACE}"><mi>x</mi></math>"#
            ),
            MathMlAdapterError::XmlLimit,
        ),
        (
            MathMlAdapterLimitConfig {
                children_per_element: 1,
                ..MathMlAdapterLimitConfig::default()
            },
            document("<mrow><mi>x</mi><mo>+</mo><mi>y</mi></mrow>"),
            MathMlAdapterError::XmlLimit,
        ),
    ];
    for (config, source, expected) in bounded_cases {
        let bounded =
            MathMlAdapter::new(MathMlAdapterLimits::new(config)?, MathAstLimits::default())?;
        let Err(error) = bounded.parse(MathMlParseRequestDraft {
            schema_version: MATHML_ADAPTER_SCHEMA_VERSION.to_owned(),
            source,
        }) else {
            return Err("finite XML limit was not enforced".into());
        };
        assert_eq!(error, expected);
    }
    Ok(())
}

#[test]
fn finite_tree_parser_and_output_limits_are_enforced() -> TestResult {
    let invalid = MathMlAdapterLimitConfig {
        depth: 0,
        ..MathMlAdapterLimitConfig::default()
    };
    let Err(error) = MathMlAdapterLimits::new(invalid) else {
        return Err("zero depth accepted".into());
    };
    assert_eq!(error, MathMlAdapterError::InvalidLimit);

    let depth_limits = MathMlAdapterLimits::new(MathMlAdapterLimitConfig {
        depth: 2,
        ..MathMlAdapterLimitConfig::default()
    })?;
    let bounded = MathMlAdapter::new(depth_limits, MathAstLimits::default())?;
    let Err(error) = bounded.parse(MathMlParseRequestDraft {
        schema_version: MATHML_ADAPTER_SCHEMA_VERSION.to_owned(),
        source: document("<mrow><mi>x</mi></mrow>"),
    }) else {
        return Err("over-depth tree accepted".into());
    };
    assert_eq!(error, MathMlAdapterError::XmlLimit);

    let parser_limits = MathMlAdapterLimits::new(MathMlAdapterLimitConfig {
        parser_depth: 2,
        ..MathMlAdapterLimitConfig::default()
    })?;
    let bounded = MathMlAdapter::new(parser_limits, MathAstLimits::default())?;
    let Err(error) = bounded.parse(MathMlParseRequestDraft {
        schema_version: MATHML_ADAPTER_SCHEMA_VERSION.to_owned(),
        source: document("<mrow><mo>−</mo><mo>−</mo><mo>−</mo><mi>x</mi></mrow>"),
    }) else {
        return Err("over-depth presentation expression accepted".into());
    };
    assert_eq!(error, MathMlAdapterError::XmlLimit);

    let output_limits = MathMlAdapterLimits::new(MathMlAdapterLimitConfig {
        serialized_bytes: 32,
        ..MathMlAdapterLimitConfig::default()
    })?;
    let bounded = MathMlAdapter::new(output_limits, MathAstLimits::default())?;
    let Err(error) = bounded.parse(MathMlParseRequestDraft {
        schema_version: MATHML_ADAPTER_SCHEMA_VERSION.to_owned(),
        source: document("<mi>x</mi>"),
    }) else {
        return Err("oversized result accepted".into());
    };
    assert_eq!(error, MathMlAdapterError::OutputLimit);
    Ok(())
}

#[test]
fn strict_json_and_versions_reject_tampering() -> TestResult {
    let source = document("<mi>x</mi>");
    let valid = serde_json::json!({
        "schema_version": MATHML_ADAPTER_SCHEMA_VERSION,
        "source": source,
    });
    assert!(adapter()?.parse_json(&serde_json::to_vec(&valid)?).is_ok());

    let duplicate = format!(
        r#"{{"schema_version":"{MATHML_ADAPTER_SCHEMA_VERSION}","source":"x","source":"y"}}"#
    );
    let Err(error) = adapter()?.parse_json(duplicate.as_bytes()) else {
        return Err("duplicate accepted".into());
    };
    assert_eq!(error, MathMlAdapterError::InvalidJson);
    let unknown = serde_json::json!({
        "schema_version": MATHML_ADAPTER_SCHEMA_VERSION,
        "source": document("<mi>x</mi>"),
        "extra": true,
    });
    let Err(error) = adapter()?.parse_json(&serde_json::to_vec(&unknown)?) else {
        return Err("unknown accepted".into());
    };
    assert_eq!(error, MathMlAdapterError::InvalidJson);
    let wrong = MathMlParseRequestDraft {
        schema_version: "hwpx-agent.mathml-adapter/v0".to_owned(),
        source: document("<mi>x</mi>"),
    };
    let Err(error) = adapter()?.parse(wrong) else {
        return Err("wrong version accepted".into());
    };
    assert_eq!(error, MathMlAdapterError::UnsupportedVersion);
    Ok(())
}

#[test]
fn canonical_result_is_deterministic_bounded_and_debug_redacted() -> TestResult {
    let source = document("<mrow><mi>secretName</mi><mo>+</mo><mn>7</mn></mrow>");
    let first = parse(&source)?;
    let second = parse(&source)?;
    assert_eq!(
        first.canonical_json(limits()?)?,
        second.canonical_json(limits()?)?
    );
    assert_eq!(first.source_length_bytes(), u32::try_from(source.len())?);
    assert!(first.element_count() >= 5);
    assert!(first.decoded_text_bytes() >= "secretName7+".len());
    assert_eq!(first.source_sha256().len(), 64);
    let debug = format!("{first:?}");
    assert!(!debug.contains("secretName"));
    assert!(!debug.contains(first.source_sha256()));
    assert!(!debug.contains(&source.len().to_string()));
    assert!(
        format!(
            "{:?}",
            MathMlParseRequestDraft {
                schema_version: MATHML_ADAPTER_SCHEMA_VERSION.to_owned(),
                source,
            }
        )
        .contains("<redacted>")
    );
    Ok(())
}

#[test]
fn operator_identity_and_explicit_function_application_are_preserved() -> TestResult {
    let multiply = parse(&document(
        "<mrow><mi>x</mi><mo>&#x2062;</mo><mi>y</mi></mrow>",
    ))?;
    assert!(matches!(
        multiply.ast().root().expression,
        MathExpression::Apply {
            operator: MathOperator::Multiply,
            ..
        }
    ));
    assert_code(
        &document("<mrow><mi>f</mi><mfenced><mi>x</mi></mfenced></mrow>"),
        "mathml_adapter_ambiguous_presentation",
    );
    Ok(())
}
