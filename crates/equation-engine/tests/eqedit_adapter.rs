use std::error::Error;

use domain_ir::{
    MATH_AST_NORMALIZATION_VERSION, MATH_AST_SCHEMA_VERSION, MathAst, MathAstDraft, MathAstLimits,
    MathExpression, MathLargeOperator, MathNode, MathOperator, MathSourceSpan,
};
use equation_engine::{
    EQEDIT_ADAPTER_SCHEMA_VERSION, EQEDIT_PROFILE_VERSION, EqEditEngine, EqEditError,
    EqEditLimitConfig, EqEditLimits, EqEditParseRequestDraft, LATEX_ADAPTER_SCHEMA_VERSION,
    LatexAdapter, LatexAdapterLimits, LatexParseOutcome, LatexParseRequestDraft,
    MATHML_ADAPTER_SCHEMA_VERSION, MATHML_NAMESPACE, MathMlAdapter, MathMlAdapterLimits,
    MathMlParseRequestDraft,
};

type TestResult = Result<(), Box<dyn Error>>;

fn engine() -> Result<EqEditEngine, EqEditError> {
    EqEditEngine::new(EqEditLimits::default(), MathAstLimits::default())
}

fn request(source: &str) -> EqEditParseRequestDraft {
    EqEditParseRequestDraft {
        schema_version: EQEDIT_ADAPTER_SCHEMA_VERSION.to_owned(),
        profile_version: EQEDIT_PROFILE_VERSION.to_owned(),
        source: source.to_owned(),
    }
}

fn latex_ast(source: &str) -> Result<domain_ir::MathAst, Box<dyn Error>> {
    let adapter = LatexAdapter::new(LatexAdapterLimits::default(), MathAstLimits::default())?;
    let parsed = adapter.parse(LatexParseRequestDraft {
        schema_version: LATEX_ADAPTER_SCHEMA_VERSION.to_owned(),
        source: source.to_owned(),
        macros: Vec::new(),
    })?;
    let LatexParseOutcome::Parsed { ast } = parsed.outcome() else {
        return Err("ambiguous LaTeX fixture".into());
    };
    Ok(ast.clone())
}

fn mathml_ast(body: &str) -> Result<domain_ir::MathAst, Box<dyn Error>> {
    let adapter = MathMlAdapter::new(MathMlAdapterLimits::default(), MathAstLimits::default())?;
    let parsed = adapter.parse(MathMlParseRequestDraft {
        schema_version: MATHML_ADAPTER_SCHEMA_VERSION.to_owned(),
        source: format!(r#"<math xmlns="{MATHML_NAMESPACE}">{body}</math>"#),
    })?;
    Ok(parsed.ast().clone())
}

fn apply_power_ast() -> Result<MathAst, Box<dyn Error>> {
    let node = |span, expression| MathNode {
        span,
        style: None,
        expression,
    };
    Ok(MathAst::from_draft(
        MathAstDraft {
            schema_version: MATH_AST_SCHEMA_VERSION.to_owned(),
            normalization_version: MATH_AST_NORMALIZATION_VERSION.to_owned(),
            source_length_bytes: 3,
            root: node(
                MathSourceSpan {
                    start_byte: 0,
                    end_byte: 3,
                },
                MathExpression::Apply {
                    operator: MathOperator::Power,
                    arguments: vec![
                        node(
                            MathSourceSpan {
                                start_byte: 0,
                                end_byte: 1,
                            },
                            MathExpression::Identifier {
                                name: "x".to_owned(),
                            },
                        ),
                        node(
                            MathSourceSpan {
                                start_byte: 2,
                                end_byte: 3,
                            },
                            MathExpression::Number {
                                value: "2".to_owned(),
                            },
                        ),
                    ],
                },
            ),
        },
        MathAstLimits::default(),
    )?)
}

#[test]
fn documented_precedence_fraction_script_root_and_function_are_typed() -> TestResult {
    let arithmetic = engine()?.parse(request("1 + 2 TIMES 3"))?;
    assert!(matches!(
        arithmetic.ast().root().expression,
        MathExpression::Apply {
            operator: MathOperator::Add,
            ..
        }
    ));
    let fraction = engine()?.parse(request("{1 + 2} OVER {3 TIMES 4}"))?;
    assert!(matches!(
        fraction.ast().root().expression,
        MathExpression::Fraction { .. }
    ));
    let script = engine()?.parse(request("{x} _ {i} ^ {2}"))?;
    assert!(matches!(
        script.ast().root().expression,
        MathExpression::Script {
            subscript: Some(_),
            superscript: Some(_),
            ..
        }
    ));
    let root = engine()?.parse(request("^{3} SQRT {x + 1}"))?;
    assert!(matches!(
        root.ast().root().expression,
        MathExpression::Root {
            degree: Some(_),
            ..
        }
    ));
    assert!(matches!(
        engine()?.parse(request("sin {x}"))?.ast().root().expression,
        MathExpression::Function { .. }
    ));
    Ok(())
}

#[test]
fn exact_p06_hangul_2020_saved_script_is_admitted_without_native_promotion() -> TestResult {
    let source = "sum _{{i=1}} ^{{32}} {{i^2}} + int _0 ^1 {{x^4 + 3x^2 + 1}} dx = 10416";
    let parsed = engine()?.parse(request(source))?;
    assert!(matches!(
        parsed.ast().root().expression,
        MathExpression::Apply {
            operator: MathOperator::Equal,
            ..
        }
    ));
    assert!(parsed.token_count() > 20);
    Ok(())
}

#[test]
fn symbols_accents_large_operators_and_relations_roundtrip_semantically() -> TestResult {
    let corpus = [
        r"\alpha\leq\beta",
        r"A\subseteq B\land C\notin D",
        r"P\implies Q",
        r"\frac{1}{x+1}",
        r"x_{i}^{2}",
        r"\sqrt[3]{x}",
        r"\sin{x}",
        r"\sum_{i=1}^{n}{i^2}",
        r"\prod_{i=1}^{n}{i}",
        r"\int_{0}^{1}{x^2}",
        r"\iint_{0}^{1}{x}",
        r"\oint_{0}^{1}{x}",
        r"\lim_{x=0}{x}",
        r"\vec{v}",
        r"\hat{x}",
        r"\left|x\right|",
        r"\binom{n}{r}",
        r"x=\text{constant}",
    ];
    for source in corpus {
        let ast = latex_ast(source)?;
        let compiled = engine()?.compile(&ast)?;
        let reparsed = engine()?.parse(request(compiled.script()))?;
        assert!(ast.semantically_eq(reparsed.ast()), "{source}");
        assert_eq!(compiled.semantic_sha256().len(), 64);
        assert_eq!(compiled.script_sha256().len(), 64);
    }
    Ok(())
}

#[test]
fn matrix_cases_aligned_set_and_derivative_roundtrip_semantically() -> TestResult {
    let matrix = mathml_ast(
        "<matrix><matrixrow><cn>1</cn><cn>2</cn></matrixrow><matrixrow><cn>3</cn><cn>4</cn></matrixrow></matrix>",
    )?;
    let matrix_script = engine()?.compile(&matrix)?;
    assert!(matrix_script.script().starts_with("MATRIX"));
    assert!(matrix.semantically_eq(engine()?.parse(request(matrix_script.script()))?.ast()));

    for source in [
        "CASES {{x} & {x > 0} # {- {x}} & {x < 0}}",
        "PILE {{x = 1} & {y = 2} # {x = 3} & {y = 4}}",
        "LEFT { {x} VERT {x > 0} RIGHT }",
    ] {
        let ast = engine()?.parse(request(source))?.ast().clone();
        let compiled = engine()?.compile(&ast)?;
        let reparsed = engine()?.parse(request(compiled.script()))?;
        assert!(ast.semantically_eq(reparsed.ast()), "{source}");
    }

    for source in [r"\dv{x^2}{x}", r"\pdv[2]{x\cdot y}{x}"] {
        let ast = latex_ast(source)?;
        let compiled = engine()?.compile(&ast)?;
        assert!(compiled.script().contains(" OVER "));
        assert!(ast.semantically_eq(engine()?.parse(request(compiled.script()))?.ast()));
    }
    Ok(())
}

#[test]
fn current_profile_commands_and_removed_legacy_forms_are_distinct() -> TestResult {
    for source in [
        "DINT _ {0} ^ {1} {x}",
        "OTINT _ {0} ^ {1} {x}",
        "OVERLINE {x}",
        "UNDERLINE {x}",
        "BMATRIX {{1} & {2} # {3} & {4}}",
        "BINOM {n} {r}",
        "Alpha + omega + INF + EMPTYSET",
    ] {
        assert!(engine()?.parse(request(source)).is_ok(), "{source}");
    }
    for source in [
        "int FROM 0 TO 1 {x}",
        "SCALE 70 {x}",
        "PHANTOM {x}",
        r"\sqrt{x}",
        "x ~ y",
        "x ` y",
        "|x|",
        "||x||",
        "x < y < z",
        "matrix {{1} & {2} # {3}}",
    ] {
        assert!(engine()?.parse(request(source)).is_err(), "{source}");
    }
    Ok(())
}

#[test]
fn escaping_is_lossless_or_rejected_without_replacement() -> TestResult {
    let text = engine()?.parse(request(r#""한글 text 123""#))?;
    let compiled = engine()?.compile(text.ast())?;
    assert_eq!(compiled.script(), r#""한글 text 123""#);
    for source in [r#""unterminated"#, "x\\y", "x\u{0007}y"] {
        assert!(engine()?.parse(request(source)).is_err());
    }
    let forbidden = mathml_ast("<cs>private&quot;text</cs>")?;
    assert_eq!(
        engine()?.compile(&forbidden),
        Err(EqEditError::UnrepresentableValue)
    );
    Ok(())
}

#[test]
fn strict_json_version_profile_and_duplicate_fields_fail_closed() -> TestResult {
    let valid = serde_json::json!({
        "schema_version": EQEDIT_ADAPTER_SCHEMA_VERSION,
        "profile_version": EQEDIT_PROFILE_VERSION,
        "source": "x + 1",
    });
    assert!(engine()?.parse_json(&serde_json::to_vec(&valid)?).is_ok());
    let duplicate = format!(
        r#"{{"schema_version":"{EQEDIT_ADAPTER_SCHEMA_VERSION}","profile_version":"{EQEDIT_PROFILE_VERSION}","source":"x","source":"y"}}"#
    );
    assert_eq!(
        engine()?.parse_json(duplicate.as_bytes()),
        Err(EqEditError::InvalidJson)
    );
    let mut wrong_version = request("x");
    wrong_version.schema_version = "hwpx-agent.eqedit-adapter/v0".to_owned();
    assert_eq!(
        engine()?.parse(wrong_version),
        Err(EqEditError::UnsupportedVersion)
    );
    let mut wrong_profile = request("x");
    wrong_profile.profile_version = "hangul-2024".to_owned();
    assert_eq!(
        engine()?.parse(wrong_profile),
        Err(EqEditError::UnsupportedProfile)
    );
    Ok(())
}

#[test]
fn finite_source_token_depth_compile_and_serialized_limits_are_enforced() -> TestResult {
    let invalid = EqEditLimitConfig {
        parse_depth: 0,
        ..EqEditLimitConfig::default()
    };
    assert_eq!(EqEditLimits::new(invalid), Err(EqEditError::InvalidLimit));

    let source_limited = EqEditEngine::new(
        EqEditLimits::new(EqEditLimitConfig {
            source_bytes: 4,
            script_bytes: 4,
            ..EqEditLimitConfig::default()
        })?,
        MathAstLimits::default(),
    )?;
    assert_eq!(
        source_limited.parse(request("12345")),
        Err(EqEditError::InputLimit)
    );

    let token_limited = EqEditEngine::new(
        EqEditLimits::new(EqEditLimitConfig {
            tokens: 2,
            ..EqEditLimitConfig::default()
        })?,
        MathAstLimits::default(),
    )?;
    assert_eq!(
        token_limited.parse(request("x + y")),
        Err(EqEditError::TokenLimit)
    );

    let token_bytes_limited = EqEditEngine::new(
        EqEditLimits::new(EqEditLimitConfig {
            token_bytes: 3,
            ..EqEditLimitConfig::default()
        })?,
        MathAstLimits::default(),
    )?;
    assert_eq!(
        token_bytes_limited.parse(request("abcd")),
        Err(EqEditError::TokenLimit)
    );

    let depth_limited = EqEditEngine::new(
        EqEditLimits::new(EqEditLimitConfig {
            parse_depth: 2,
            ..EqEditLimitConfig::default()
        })?,
        MathAstLimits::default(),
    )?;
    assert_eq!(
        depth_limited.parse(request("{{{x}}}")),
        Err(EqEditError::ParseDepthLimit)
    );

    let output_limited = EqEditEngine::new(
        EqEditLimits::new(EqEditLimitConfig {
            serialized_bytes: 64,
            ..EqEditLimitConfig::default()
        })?,
        MathAstLimits::default(),
    )?;
    assert_eq!(
        output_limited.parse(request("x")),
        Err(EqEditError::OutputLimit)
    );

    let compile_depth_limited = EqEditEngine::new(
        EqEditLimits::new(EqEditLimitConfig {
            compile_depth: 2,
            ..EqEditLimitConfig::default()
        })?,
        MathAstLimits::default(),
    )?;
    assert_eq!(
        compile_depth_limited.compile(&latex_ast(r"\frac{1}{\frac{2}{3}}")?),
        Err(EqEditError::OutputLimit)
    );

    let script_limited = EqEditEngine::new(
        EqEditLimits::new(EqEditLimitConfig {
            source_bytes: 8,
            script_bytes: 8,
            ..EqEditLimitConfig::default()
        })?,
        MathAstLimits::default(),
    )?;
    assert_eq!(
        script_limited.compile(&latex_ast("x+1")?),
        Err(EqEditError::OutputLimit)
    );
    Ok(())
}

#[test]
fn deterministic_generated_ast_script_roundtrip_property_corpus() -> TestResult {
    let atoms = ["x", "y", "2", "alpha", "INF", "SQRT {z}"];
    let operators = ["+", "-", "TIMES", "DIVIDE", "SUP", "UNION", "INTER", "CIRC"];
    for index in 0..256 {
        let left = atoms[index % atoms.len()];
        let right = atoms[(index * 5 + 1) % atoms.len()];
        let tail = atoms[(index * 7 + 3) % atoms.len()];
        let operator = operators[(index * 3 + 2) % operators.len()];
        let source = format!("{{{left}}} {operator} {{{right}}} + {{{tail}}}");
        let ast = engine()?.parse(request(&source))?.ast().clone();
        let first = engine()?.compile(&ast)?;
        let second = engine()?.compile(&ast)?;
        assert_eq!(first.script(), second.script(), "case {index}");
        assert!(
            ast.semantically_eq(engine()?.parse(request(first.script()))?.ast()),
            "case {index}: {source}"
        );
    }
    Ok(())
}

#[test]
fn unsupported_ast_shapes_never_degrade_to_approximate_eqedit() -> TestResult {
    let styled = mathml_ast(r#"<mstyle mathvariant="bold"><mi>x</mi></mstyle>"#)?;
    assert_eq!(
        engine()?.compile(&styled),
        Err(EqEditError::UnsupportedStyle)
    );
    let named = mathml_ast("<mrow><mi>velocity</mi><mo>&#x2061;</mo><mi>t</mi></mrow>")?;
    assert_eq!(
        engine()?.compile(&named),
        Err(EqEditError::UnsupportedExpression)
    );
    let scripted_power = mathml_ast("<apply><power/><ci>x</ci><cn>2</cn></apply>")?;
    let compiled = engine()?.compile(&scripted_power)?;
    assert!(compiled.script().contains(" ^ "));
    let applied_power = apply_power_ast()?;
    let compiled = engine()?.compile(&applied_power)?;
    assert!(compiled.script().contains(" SUP "));
    Ok(())
}

#[test]
fn deterministic_receipts_and_debug_surfaces_are_bounded_and_redacted() -> TestResult {
    let parsed_one = engine()?.parse(request("{private} + {7}"))?;
    let parsed_two = engine()?.parse(request("{private} + {7}"))?;
    assert_eq!(
        parsed_one.canonical_json(EqEditLimits::default())?,
        parsed_two.canonical_json(EqEditLimits::default())?
    );
    let compiled_one = engine()?.compile(parsed_one.ast())?;
    let compiled_two = engine()?.compile(parsed_one.ast())?;
    assert_eq!(
        compiled_one.canonical_json(EqEditLimits::default())?,
        compiled_two.canonical_json(EqEditLimits::default())?
    );
    for debug in [
        format!("{parsed_one:?}"),
        format!("{compiled_one:?}"),
        format!("{:?}", request("private")),
    ] {
        assert!(!debug.contains("private"));
        assert!(debug.contains("redacted") || debug.contains("EqEdit"));
    }
    for error in [
        EqEditError::InvalidLimit,
        EqEditError::InputLimit,
        EqEditError::InvalidJson,
        EqEditError::UnsupportedVersion,
        EqEditError::UnsupportedProfile,
        EqEditError::TokenLimit,
        EqEditError::ParseDepthLimit,
        EqEditError::InvalidSyntax,
        EqEditError::UnsupportedSyntax,
        EqEditError::UnrepresentableValue,
        EqEditError::UnsupportedExpression,
        EqEditError::UnsupportedStyle,
        EqEditError::MathAst,
        EqEditError::RoundTripMismatch,
        EqEditError::OutputLimit,
        EqEditError::Serialization,
    ] {
        assert!(error.code().starts_with("eqedit_"));
        assert!(!error.code().contains("private"));
    }
    Ok(())
}

#[test]
fn integral_cardinality_is_preserved_by_current_hangul_tokens() -> TestResult {
    for (source, multiplicity, contour) in [
        ("INT {x}", 1, false),
        ("DINT {x}", 2, false),
        ("TINT {x}", 3, false),
        ("OINT {x}", 1, true),
        ("ODINT {x}", 2, true),
        ("OTINT {x}", 3, true),
    ] {
        assert!(matches!(
            engine()?.parse(request(source))?.ast().root().expression,
            MathExpression::LargeOperator {
                operator: MathLargeOperator::Integral {
                    multiplicity: actual,
                    contour: actual_contour,
                },
                ..
            } if actual == multiplicity && actual_contour == contour
        ));
    }
    Ok(())
}
