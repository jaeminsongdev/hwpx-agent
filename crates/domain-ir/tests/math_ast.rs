use domain_ir::{
    MATH_AST_NORMALIZATION_VERSION, MATH_AST_SCHEMA_VERSION, MathAccent, MathAlignedLine,
    MathAnnotationKind, MathAst, MathAstDraft, MathAstError, MathAstLimitConfig, MathAstLimits,
    MathCase, MathColor, MathCombinatorialKind, MathDelimiter, MathDerivativeKind,
    MathDerivativeVariable, MathExpression, MathFunction, MathGreekLetter, MathLargeOperator,
    MathLetterCase, MathMatrixKind, MathNode, MathOperator, MathSourceSpan, MathStyleHint,
    MathSymbol, MathVariant,
};

type TestResult = Result<(), Box<dyn std::error::Error>>;

fn limits() -> Result<MathAstLimits, MathAstError> {
    MathAstLimits::new(MathAstLimitConfig::default())
}

fn span(start_byte: u32, end_byte: u32) -> MathSourceSpan {
    MathSourceSpan {
        start_byte,
        end_byte,
    }
}

fn node(expression: MathExpression) -> MathNode {
    MathNode {
        span: span(0, 100),
        style: None,
        expression,
    }
}

fn number(value: &str) -> MathNode {
    node(MathExpression::Number {
        value: value.to_owned(),
    })
}

fn identifier(name: &str) -> MathNode {
    node(MathExpression::Identifier {
        name: name.to_owned(),
    })
}

fn text(value: &str) -> MathNode {
    node(MathExpression::Text {
        value: value.to_owned(),
    })
}

fn apply(operator: MathOperator, arguments: Vec<MathNode>) -> MathNode {
    node(MathExpression::Apply {
        operator,
        arguments,
    })
}

fn draft(root: MathNode) -> MathAstDraft {
    MathAstDraft {
        schema_version: MATH_AST_SCHEMA_VERSION.to_owned(),
        normalization_version: MATH_AST_NORMALIZATION_VERSION.to_owned(),
        source_length_bytes: 100,
        root,
    }
}

fn ast(root: MathNode) -> Result<MathAst, MathAstError> {
    MathAst::from_draft(draft(root), limits()?)
}

#[test]
fn normalizes_exact_numbers_and_unicode_without_losing_spans() -> TestResult {
    let mut root = node(MathExpression::Row {
        items: vec![
            number("00012.3400"),
            identifier("e\u{301}"),
            text("cafe\u{301}"),
        ],
    });
    root.style = Some(MathStyleHint {
        variant: None,
        color: None,
    });
    let ast = ast(root)?;
    assert_eq!(ast.root().style, None);
    let MathExpression::Row { items } = &ast.root().expression else {
        return Err("normalized root is not a row".into());
    };
    assert!(matches!(
        &items[0].expression,
        MathExpression::Number { value } if value == "12.34"
    ));
    assert!(matches!(
        &items[1].expression,
        MathExpression::Identifier { name } if name == "é"
    ));
    assert!(matches!(
        &items[2].expression,
        MathExpression::Text { value } if value == "café"
    ));
    assert_eq!(items[0].span, span(0, 100));
    Ok(())
}

#[test]
fn semantic_identity_ignores_spans_styles_positive_and_associative_grouping() -> TestResult {
    let flat = ast(apply(
        MathOperator::Add,
        vec![
            identifier("x"),
            number("1"),
            identifier("y"),
            identifier("z"),
        ],
    ))?;
    let mut nested_x = identifier("x");
    nested_x.span = span(5, 9);
    nested_x.style = Some(MathStyleHint {
        variant: Some(MathVariant::Bold),
        color: Some(MathColor {
            red: 10,
            green: 20,
            blue: 30,
        }),
    });
    let nested = ast(apply(
        MathOperator::Add,
        vec![
            apply(MathOperator::Add, vec![nested_x, number("01.0")]),
            apply(
                MathOperator::Positive,
                vec![apply(
                    MathOperator::Add,
                    vec![identifier("y"), identifier("z")],
                )],
            ),
        ],
    ))?;
    assert!(flat.semantically_eq(&nested));
    assert_eq!(
        flat.semantic_sha256(limits()?)?,
        nested.semantic_sha256(limits()?)?
    );
    assert_ne!(
        flat.canonical_json(limits()?)?,
        nested.canonical_json(limits()?)?
    );
    Ok(())
}

#[test]
fn square_root_and_degree_two_have_one_semantic_identity() -> TestResult {
    let square_root = ast(node(MathExpression::Root {
        degree: None,
        radicand: Box::new(identifier("x")),
    }))?;
    let mut degree = number("02.0");
    degree.style = Some(MathStyleHint {
        variant: Some(MathVariant::Italic),
        color: None,
    });
    let degree_two = ast(node(MathExpression::Root {
        degree: Some(Box::new(degree)),
        radicand: Box::new(identifier("x")),
    }))?;
    assert!(square_root.semantically_eq(&degree_two));
    Ok(())
}

#[test]
fn singleton_and_nested_rows_do_not_change_semantic_identity() -> TestResult {
    let plain = ast(identifier("x"))?;
    let nested = ast(node(MathExpression::Row {
        items: vec![node(MathExpression::Row {
            items: vec![identifier("x")],
        })],
    }))?;
    assert!(plain.semantically_eq(&nested));
    assert_eq!(
        plain.semantic_sha256(limits()?)?,
        nested.semantic_sha256(limits()?)?
    );
    Ok(())
}

#[test]
fn canonical_json_roundtrips_and_rejects_schema_tampering() -> TestResult {
    let original = ast(node(MathExpression::Fraction {
        numerator: Box::new(identifier("x")),
        denominator: Box::new(number("2")),
    }))?;
    let canonical = original.canonical_json(limits()?)?;
    assert_eq!(MathAst::from_json(&canonical, limits()?)?, original);

    let wrong_schema = String::from_utf8(canonical.clone())?
        .replace(MATH_AST_SCHEMA_VERSION, "hwpx-agent.math-ast/v0");
    assert_eq!(
        MathAst::from_json(wrong_schema.as_bytes(), limits()?),
        Err(MathAstError::UnsupportedVersion)
    );
    let wrong_normalization = String::from_utf8(canonical.clone())?.replace(
        MATH_AST_NORMALIZATION_VERSION,
        "hwpx-agent.math-ast-normalization/v0",
    );
    assert_eq!(
        MathAst::from_json(wrong_normalization.as_bytes(), limits()?),
        Err(MathAstError::UnsupportedNormalizationVersion)
    );
    let canonical_text = String::from_utf8(canonical)?;
    let unknown = canonical_text.replacen('{', "{\"unknown\":true,", 1);
    assert_eq!(
        MathAst::from_json(unknown.as_bytes(), limits()?),
        Err(MathAstError::InvalidJson)
    );
    let duplicate = format!(
        "{{\"schema_version\":\"{MATH_AST_SCHEMA_VERSION}\",{}",
        &canonical_text[1..]
    );
    assert_eq!(
        MathAst::from_json(duplicate.as_bytes(), limits()?),
        Err(MathAstError::InvalidJson)
    );
    assert_eq!(
        MathAst::from_json(b"", limits()?),
        Err(MathAstError::InputLimit)
    );
    assert_eq!(
        MathAst::from_json(b"{", limits()?),
        Err(MathAstError::InvalidJson)
    );
    Ok(())
}

#[test]
fn arithmetic_relation_logic_set_and_function_nodes_are_typed() -> TestResult {
    let function = node(MathExpression::Function {
        function: MathFunction::Named {
            name: "f\u{301}".to_owned(),
        },
        arguments: vec![identifier("x"), number("2")],
    });
    let relation = apply(
        MathOperator::Equal,
        vec![
            apply(MathOperator::Power, vec![function, number("2")]),
            apply(MathOperator::Union, vec![identifier("A"), identifier("B")]),
        ],
    );
    let result = ast(apply(
        MathOperator::LogicalAnd,
        vec![relation.clone(), relation],
    ))?;
    assert_eq!(result.schema_version(), MATH_AST_SCHEMA_VERSION);
    assert_eq!(
        result.normalization_version(),
        MATH_AST_NORMALIZATION_VERSION
    );
    assert_eq!(result.source_length_bytes(), 100);
    Ok(())
}

#[test]
fn scripts_accents_annotations_and_delimiters_are_complete() -> TestResult {
    let scripted = node(MathExpression::Script {
        base: Box::new(identifier("x")),
        subscript: Some(Box::new(identifier("i"))),
        superscript: Some(Box::new(number("2"))),
    });
    let accented = node(MathExpression::Accent {
        accent: MathAccent::VectorArrow,
        base: Box::new(scripted),
    });
    let annotated = node(MathExpression::Annotated {
        annotation_kind: MathAnnotationKind::OverBrace,
        base: Box::new(accented),
        annotation: Some(Box::new(text("vector"))),
    });
    let delimited = node(MathExpression::Delimited {
        left: MathDelimiter::LeftParenthesis,
        body: Box::new(annotated),
        right: MathDelimiter::RightBracket,
    });
    assert!(!ast(delimited)?.semantic_json(limits()?)?.is_empty());
    Ok(())
}

#[test]
fn large_operators_and_multivariable_derivatives_are_complete() -> TestResult {
    let integral = node(MathExpression::LargeOperator {
        operator: MathLargeOperator::Integral {
            multiplicity: 3,
            contour: false,
        },
        body: Box::new(identifier("f")),
        lower: Some(Box::new(number("0"))),
        upper: Some(Box::new(number("1"))),
    });
    let derivative = node(MathExpression::Derivative {
        derivative_kind: MathDerivativeKind::Partial,
        expression: Box::new(integral),
        variables: vec![
            MathDerivativeVariable {
                variable: Box::new(identifier("x")),
                order: 2,
            },
            MathDerivativeVariable {
                variable: Box::new(node(MathExpression::Symbol {
                    symbol: MathSymbol::Greek {
                        letter: MathGreekLetter::Theta,
                        letter_case: MathLetterCase::Lower,
                    },
                })),
                order: 1,
            },
        ],
    });
    let sum = node(MathExpression::LargeOperator {
        operator: MathLargeOperator::Sum,
        body: Box::new(derivative),
        lower: Some(Box::new(identifier("i"))),
        upper: Some(Box::new(identifier("n"))),
    });
    assert!(!ast(sum)?.semantic_json(limits()?)?.is_empty());
    Ok(())
}

#[test]
fn matrix_cases_aligned_combinatorial_and_set_builder_are_complete() -> TestResult {
    let matrix = node(MathExpression::Matrix {
        matrix_kind: MathMatrixKind::Determinant,
        rows: vec![
            vec![number("1"), number("2")],
            vec![number("3"), number("4")],
        ],
    });
    let cases = node(MathExpression::Cases {
        cases: vec![
            MathCase {
                value: matrix,
                condition: Some(apply(
                    MathOperator::GreaterThan,
                    vec![identifier("x"), number("0")],
                )),
            },
            MathCase {
                value: number("0"),
                condition: None,
            },
        ],
    });
    let combinatorial = node(MathExpression::Combinatorial {
        combinatorial_kind: MathCombinatorialKind::Combination,
        upper: Box::new(identifier("n")),
        lower: Box::new(identifier("r")),
    });
    let set_builder = node(MathExpression::SetBuilder {
        element: Box::new(identifier("x")),
        condition: Box::new(apply(
            MathOperator::ElementOf,
            vec![identifier("x"), identifier("R")],
        )),
    });
    let aligned = node(MathExpression::Aligned {
        lines: vec![
            MathAlignedLine {
                cells: vec![cases, combinatorial.clone()],
            },
            MathAlignedLine {
                cells: vec![set_builder, combinatorial],
            },
        ],
    });
    assert!(!ast(aligned)?.canonical_json(limits()?)?.is_empty());
    Ok(())
}

#[test]
fn malformed_numbers_identifiers_text_and_arity_fail_closed() {
    for invalid in ["", ".", "1.2.3", "+1", "-1", "1e3", "NaN", " 1"] {
        assert_eq!(ast(number(invalid)), Err(MathAstError::InvalidNumber));
    }
    for invalid in ["", "x y", "x\n", "\0x"] {
        assert_eq!(
            ast(identifier(invalid)),
            Err(MathAstError::InvalidIdentifier)
        );
    }
    for invalid in ["", "line\nfeed", "\0"] {
        assert_eq!(ast(text(invalid)), Err(MathAstError::InvalidText));
    }
    assert_eq!(
        ast(apply(MathOperator::Power, vec![number("2")])),
        Err(MathAstError::InvalidArity)
    );
    assert_eq!(
        ast(apply(
            MathOperator::Negative,
            vec![number("1"), number("2")]
        )),
        Err(MathAstError::InvalidArity)
    );
}

#[test]
fn invalid_spans_and_source_lengths_fail_closed() -> TestResult {
    let mut invalid = draft(identifier("x"));
    invalid.root.span = span(20, 10);
    assert_eq!(
        MathAst::from_draft(invalid, limits()?),
        Err(MathAstError::InvalidSpan)
    );

    let mut outside = draft(node(MathExpression::Fraction {
        numerator: Box::new(identifier("x")),
        denominator: Box::new(number("2")),
    }));
    let MathExpression::Fraction { numerator, .. } = &mut outside.root.expression else {
        return Err("fraction fixture changed".into());
    };
    numerator.span = span(0, 101);
    assert_eq!(
        MathAst::from_draft(outside, limits()?),
        Err(MathAstError::InvalidSpan)
    );

    let mut noncontained = draft(node(MathExpression::Fraction {
        numerator: Box::new(identifier("x")),
        denominator: Box::new(number("2")),
    }));
    noncontained.root.span = span(10, 90);
    assert_eq!(
        MathAst::from_draft(noncontained, limits()?),
        Err(MathAstError::InvalidSpan)
    );

    let mut zero_source = draft(identifier("x"));
    zero_source.source_length_bytes = 0;
    assert_eq!(
        MathAst::from_draft(zero_source, limits()?),
        Err(MathAstError::SourceLimit)
    );
    Ok(())
}

#[test]
fn invalid_structural_shapes_fail_closed() {
    let no_script = node(MathExpression::Script {
        base: Box::new(identifier("x")),
        subscript: None,
        superscript: None,
    });
    assert_eq!(ast(no_script), Err(MathAstError::InvalidStructure));
    let no_delimiter = node(MathExpression::Delimited {
        left: MathDelimiter::None,
        body: Box::new(identifier("x")),
        right: MathDelimiter::None,
    });
    assert_eq!(ast(no_delimiter), Err(MathAstError::InvalidStructure));
    let ragged = node(MathExpression::Matrix {
        matrix_kind: MathMatrixKind::Plain,
        rows: vec![vec![number("1")], vec![number("2"), number("3")]],
    });
    assert_eq!(ast(ragged), Err(MathAstError::InvalidStructure));
    let nonsquare_determinant = node(MathExpression::Matrix {
        matrix_kind: MathMatrixKind::Determinant,
        rows: vec![
            vec![number("1"), number("2")],
            vec![number("3"), number("4")],
            vec![number("5"), number("6")],
        ],
    });
    assert_eq!(
        ast(nonsquare_determinant),
        Err(MathAstError::InvalidStructure)
    );
    let misaligned = node(MathExpression::Aligned {
        lines: vec![
            MathAlignedLine {
                cells: vec![number("1")],
            },
            MathAlignedLine {
                cells: vec![number("2"), number("3")],
            },
        ],
    });
    assert_eq!(ast(misaligned), Err(MathAstError::InvalidStructure));
}

#[test]
fn invalid_limit_derivative_and_integral_shapes_fail_closed() {
    let limit_without_destination = node(MathExpression::LargeOperator {
        operator: MathLargeOperator::Limit,
        body: Box::new(identifier("f")),
        lower: None,
        upper: None,
    });
    assert_eq!(
        ast(limit_without_destination),
        Err(MathAstError::InvalidStructure)
    );
    let integral_zero = node(MathExpression::LargeOperator {
        operator: MathLargeOperator::Integral {
            multiplicity: 0,
            contour: false,
        },
        body: Box::new(identifier("f")),
        lower: None,
        upper: None,
    });
    assert_eq!(ast(integral_zero), Err(MathAstError::InvalidStructure));
    let derivative_zero = node(MathExpression::Derivative {
        derivative_kind: MathDerivativeKind::Ordinary,
        expression: Box::new(identifier("f")),
        variables: vec![MathDerivativeVariable {
            variable: Box::new(identifier("x")),
            order: 0,
        }],
    });
    assert_eq!(ast(derivative_zero), Err(MathAstError::InvalidStructure));
    let derivative_expression_variable = node(MathExpression::Derivative {
        derivative_kind: MathDerivativeKind::Ordinary,
        expression: Box::new(identifier("f")),
        variables: vec![MathDerivativeVariable {
            variable: Box::new(apply(
                MathOperator::Add,
                vec![identifier("x"), identifier("y")],
            )),
            order: 1,
        }],
    });
    assert_eq!(
        ast(derivative_expression_variable),
        Err(MathAstError::InvalidStructure)
    );
    let derivative_nonvariable_symbol = node(MathExpression::Derivative {
        derivative_kind: MathDerivativeKind::Ordinary,
        expression: Box::new(identifier("f")),
        variables: vec![MathDerivativeVariable {
            variable: Box::new(node(MathExpression::Symbol {
                symbol: MathSymbol::Infinity,
            })),
            order: 1,
        }],
    });
    assert_eq!(
        ast(derivative_nonvariable_symbol),
        Err(MathAstError::InvalidStructure)
    );
}

#[test]
fn finite_node_depth_and_source_limits_are_enforced() -> TestResult {
    let node_limited = MathAstLimits::new(MathAstLimitConfig {
        nodes: 1,
        ..MathAstLimitConfig::default()
    })?;
    assert_eq!(
        MathAst::from_draft(
            draft(apply(MathOperator::Add, vec![number("1"), number("2")])),
            node_limited
        ),
        Err(MathAstError::LimitExceeded)
    );
    let depth_limited = MathAstLimits::new(MathAstLimitConfig {
        depth: 1,
        ..MathAstLimitConfig::default()
    })?;
    assert_eq!(
        MathAst::from_draft(
            draft(node(MathExpression::Root {
                degree: None,
                radicand: Box::new(identifier("x")),
            })),
            depth_limited
        ),
        Err(MathAstError::LimitExceeded)
    );
    let source_limited = MathAstLimits::new(MathAstLimitConfig {
        source_bytes: 99,
        ..MathAstLimitConfig::default()
    })?;
    assert_eq!(
        MathAst::from_draft(draft(identifier("x")), source_limited),
        Err(MathAstError::SourceLimit)
    );
    Ok(())
}

#[test]
fn finite_collection_string_and_output_limits_are_enforced() -> TestResult {
    let string_limited = MathAstLimits::new(MathAstLimitConfig {
        string_bytes: 2,
        total_string_bytes: 4,
        ..MathAstLimitConfig::default()
    })?;
    assert_eq!(
        MathAst::from_draft(draft(identifier("long")), string_limited),
        Err(MathAstError::LimitExceeded)
    );
    let total_string_limited = MathAstLimits::new(MathAstLimitConfig {
        string_bytes: 4,
        total_string_bytes: 5,
        ..MathAstLimitConfig::default()
    })?;
    assert_eq!(
        MathAst::from_draft(
            draft(node(MathExpression::Row {
                items: vec![identifier("abc"), identifier("def")],
            })),
            total_string_limited
        ),
        Err(MathAstError::LimitExceeded)
    );
    let child_limited = MathAstLimits::new(MathAstLimitConfig {
        children_per_node: 2,
        ..MathAstLimitConfig::default()
    })?;
    assert_eq!(
        MathAst::from_draft(
            draft(apply(
                MathOperator::Add,
                vec![number("1"), number("2"), number("3")]
            )),
            child_limited
        ),
        Err(MathAstError::InvalidArity)
    );
    let matrix_limited = MathAstLimits::new(MathAstLimitConfig {
        matrix_rows: 1,
        matrix_columns: 1,
        ..MathAstLimitConfig::default()
    })?;
    assert_eq!(
        MathAst::from_draft(
            draft(node(MathExpression::Matrix {
                matrix_kind: MathMatrixKind::Plain,
                rows: vec![vec![number("1")], vec![number("2")]],
            })),
            matrix_limited
        ),
        Err(MathAstError::InvalidStructure)
    );
    let output_limited = MathAstLimits::new(MathAstLimitConfig {
        serialized_bytes: 8,
        ..MathAstLimitConfig::default()
    })?;
    assert_eq!(
        MathAst::from_draft(draft(identifier("x")), output_limited),
        Err(MathAstError::OutputLimit)
    );
    assert_eq!(
        MathAst::from_json(b"oversized", output_limited),
        Err(MathAstError::InputLimit)
    );
    assert_eq!(
        MathAstLimits::new(MathAstLimitConfig {
            string_bytes: 5,
            total_string_bytes: 4,
            ..MathAstLimitConfig::default()
        }),
        Err(MathAstError::InvalidLimit)
    );
    Ok(())
}

#[test]
fn error_codes_are_stable_and_content_free() {
    let cases = [
        (MathAstError::InvalidLimit, "math_ast_invalid_limit"),
        (MathAstError::InputLimit, "math_ast_input_limit"),
        (
            MathAstError::UnsupportedVersion,
            "math_ast_unsupported_version",
        ),
        (
            MathAstError::UnsupportedNormalizationVersion,
            "math_ast_unsupported_normalization_version",
        ),
        (MathAstError::InvalidJson, "math_ast_invalid_json"),
        (MathAstError::SourceLimit, "math_ast_source_limit"),
        (MathAstError::InvalidSpan, "math_ast_invalid_span"),
        (MathAstError::InvalidNumber, "math_ast_invalid_number"),
        (
            MathAstError::InvalidIdentifier,
            "math_ast_invalid_identifier",
        ),
        (MathAstError::InvalidText, "math_ast_invalid_text"),
        (MathAstError::InvalidArity, "math_ast_invalid_arity"),
        (MathAstError::InvalidStructure, "math_ast_invalid_structure"),
        (MathAstError::LimitExceeded, "math_ast_limit_exceeded"),
        (MathAstError::OutputLimit, "math_ast_output_limit"),
        (MathAstError::Serialization, "math_ast_serialization"),
    ];
    for (error, code) in cases {
        assert_eq!(error.code(), code);
        assert!(!error.to_string().contains("private"));
    }
}

#[test]
fn canonicalization_properties_hold_over_many_shapes_and_spellings() -> TestResult {
    let limits = limits()?;
    for index in 0_u32..128 {
        let left = (index % 17).to_string();
        let right = (index % 11).to_string();
        let flat = ast(apply(
            MathOperator::Multiply,
            vec![
                number(&format!("00{left}.0")),
                identifier("e\u{301}"),
                number(&right),
            ],
        ))?;
        let mut nested_root = apply(
            MathOperator::Multiply,
            vec![
                apply(MathOperator::Multiply, vec![number(&left), identifier("é")]),
                apply(
                    MathOperator::Positive,
                    vec![number(&format!("{right}.000"))],
                ),
            ],
        );
        nested_root.style = Some(MathStyleHint {
            variant: if index % 2 == 0 {
                Some(MathVariant::Italic)
            } else {
                None
            },
            color: None,
        });
        let nested = ast(nested_root)?;
        assert!(flat.semantically_eq(&nested));
        assert_eq!(
            flat.semantic_sha256(limits)?,
            nested.semantic_sha256(limits)?
        );
        let roundtrip = MathAst::from_json(&nested.canonical_json(limits)?, limits)?;
        assert_eq!(nested, roundtrip);
        assert_eq!(
            nested.semantic_sha256(limits)?,
            roundtrip.semantic_sha256(limits)?
        );
    }
    Ok(())
}

#[test]
fn debug_redacts_source_content_spans_and_tree_payloads() -> TestResult {
    let root = node(MathExpression::Function {
        function: MathFunction::Named {
            name: "privateFunction".to_owned(),
        },
        arguments: vec![identifier("privateVariable")],
    });
    let draft_debug = format!("{:?}", draft(root.clone()));
    let ast_debug = format!("{:?}", ast(root)?);
    for debug in [draft_debug, ast_debug] {
        assert!(!debug.contains("privateFunction"));
        assert!(!debug.contains("privateVariable"));
        assert!(!debug.contains("100"));
        assert!(debug.contains("<redacted>"));
    }
    Ok(())
}

#[test]
fn semantic_hash_distinguishes_order_operator_and_content() -> TestResult {
    let add_xy = ast(apply(
        MathOperator::Add,
        vec![identifier("x"), identifier("y")],
    ))?;
    let add_yx = ast(apply(
        MathOperator::Add,
        vec![identifier("y"), identifier("x")],
    ))?;
    let multiply_xy = ast(apply(
        MathOperator::Multiply,
        vec![identifier("x"), identifier("y")],
    ))?;
    assert!(!add_xy.semantically_eq(&add_yx));
    assert!(!add_xy.semantically_eq(&multiply_xy));
    assert_ne!(
        add_xy.semantic_sha256(limits()?)?,
        add_yx.semantic_sha256(limits()?)?
    );
    assert_ne!(
        add_xy.semantic_sha256(limits()?)?,
        multiply_xy.semantic_sha256(limits()?)?
    );
    Ok(())
}
