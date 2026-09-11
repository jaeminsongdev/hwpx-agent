use domain_ir::{
    MathAstLimitConfig, MathAstLimits, MathExpression, MathLargeOperator, MathOperator,
};
use equation_engine::{
    LATEX_ADAPTER_SCHEMA_VERSION, LatexAdapter, LatexAdapterError, LatexAdapterLimitConfig,
    LatexAdapterLimits, LatexAmbiguityKind, LatexMacroDefinition, LatexParseOutcome,
    LatexParseRequestDraft,
};

type TestResult = Result<(), Box<dyn std::error::Error>>;

fn adapter() -> Result<LatexAdapter, LatexAdapterError> {
    LatexAdapter::new(
        LatexAdapterLimits::default(),
        MathAstLimits::new(MathAstLimitConfig::default())
            .map_err(|_| LatexAdapterError::InvalidLimit)?,
    )
}

fn request(source: &str) -> LatexParseRequestDraft {
    LatexParseRequestDraft {
        schema_version: LATEX_ADAPTER_SCHEMA_VERSION.to_owned(),
        source: source.to_owned(),
        macros: Vec::new(),
    }
}

fn parsed(source: &str) -> Result<domain_ir::MathAst, Box<dyn std::error::Error>> {
    let result = adapter()?.parse(request(source))?;
    match result.outcome() {
        LatexParseOutcome::Parsed { ast } => Ok(ast.clone()),
        LatexParseOutcome::Ambiguous { .. } => Err("unexpected ambiguity".into()),
    }
}

#[test]
fn precedence_fraction_root_script_and_function_are_typed() -> TestResult {
    let arithmetic = parsed(r"1+2\cdot3")?;
    assert!(matches!(
        arithmetic.root().expression,
        MathExpression::Apply {
            operator: MathOperator::Add,
            ..
        }
    ));
    assert!(matches!(
        parsed(r"\frac{x+1}{2}")?.root().expression,
        MathExpression::Fraction { .. }
    ));
    assert!(matches!(
        parsed(r"\sqrt[3]{x}")?.root().expression,
        MathExpression::Root {
            degree: Some(_),
            ..
        }
    ));
    assert!(matches!(
        parsed(r"x_{i}^{2}")?.root().expression,
        MathExpression::Script {
            subscript: Some(_),
            superscript: Some(_),
            ..
        }
    ));
    assert!(matches!(
        parsed(r"\sin{x}")?.root().expression,
        MathExpression::Function { .. }
    ));
    assert!(matches!(
        parsed(r"\sin^{2}{x}")?.root().expression,
        MathExpression::Script {
            superscript: Some(_),
            ..
        }
    ));
    Ok(())
}

#[test]
fn tier_a_symbols_relations_logic_sets_and_delimiters_are_typed() -> TestResult {
    assert!(matches!(
        parsed(r"\alpha\leq\beta")?.root().expression,
        MathExpression::Apply {
            operator: MathOperator::LessThanOrEqual,
            ..
        }
    ));
    assert!(matches!(
        parsed(r"A\subseteq B\land C\notin D")?.root().expression,
        MathExpression::Apply {
            operator: MathOperator::LogicalAnd,
            ..
        }
    ));
    assert!(matches!(
        parsed(r"\left(x+1\right)")?.root().expression,
        MathExpression::Delimited { .. }
    ));
    assert!(matches!(
        parsed(r"\set{x}{x>0}")?.root().expression,
        MathExpression::SetBuilder { .. }
    ));
    Ok(())
}

#[test]
fn large_operators_derivatives_accents_text_and_combinatorics_are_typed() -> TestResult {
    let sum = parsed(r"\sum_{i=1}^{n}{i^2}")?;
    assert!(matches!(
        sum.root().expression,
        MathExpression::LargeOperator {
            operator: MathLargeOperator::Sum,
            lower: Some(_),
            upper: Some(_),
            ..
        }
    ));
    assert!(matches!(
        parsed(r"\int_{0}^{1}{x^2}")?.root().expression,
        MathExpression::LargeOperator {
            operator: MathLargeOperator::Integral {
                multiplicity: 1,
                ..
            },
            ..
        }
    ));
    assert!(matches!(
        parsed(r"\dv[2]{x^3}{x}")?.root().expression,
        MathExpression::Derivative { .. }
    ));
    assert!(matches!(
        parsed(r"\vec{v}")?.root().expression,
        MathExpression::Accent { .. }
    ));
    assert!(matches!(
        parsed(r"x=\text{hello world}")?.root().expression,
        MathExpression::Apply { .. }
    ));
    assert!(matches!(
        parsed(r"\binom{n}{r}")?.root().expression,
        MathExpression::Combinatorial { .. }
    ));
    Ok(())
}

#[test]
fn ambiguous_sources_return_two_candidates_without_selecting_one() -> TestResult {
    for (source, expected) in [
        ("2x", LatexAmbiguityKind::ImplicitMultiplication),
        ("xy", LatexAmbiguityKind::BareMultiLetterIdentifier),
        ("f(x)", LatexAmbiguityKind::FunctionApplication),
        ("-x^2", LatexAmbiguityKind::UnaryMinusPower),
    ] {
        let result = adapter()?.parse(request(source))?;
        let LatexParseOutcome::Ambiguous {
            confidence_basis,
            ambiguities,
            candidates,
        } = result.outcome()
        else {
            return Err(format!("{source} was silently resolved").into());
        };
        assert_eq!(
            *confidence_basis,
            "deterministic_syntax_preference_not_empirical_probability"
        );
        assert!(ambiguities.iter().any(|item| item.kind == expected));
        assert_eq!(candidates.len(), 2);
        assert_eq!(
            candidates
                .iter()
                .map(|candidate| candidate.confidence_millionths)
                .sum::<u32>(),
            1_000_000
        );
        assert!(!candidates[0].ast.semantically_eq(&candidates[1].ast));
    }
    let multiple = adapter()?.parse(request("2x+3y"))?;
    let LatexParseOutcome::Ambiguous { ambiguities, .. } = multiple.outcome() else {
        return Err("multiple sites were silently resolved".into());
    };
    assert!(ambiguities.len() >= 2);
    Ok(())
}

#[test]
fn parameterized_and_nested_macros_expand_deterministically() -> TestResult {
    let mut value = request(r"\cube{x+1}");
    value.macros = vec![
        LatexMacroDefinition {
            name: "sq".to_owned(),
            parameters: 1,
            replacement: "{#1}^{2}".to_owned(),
        },
        LatexMacroDefinition {
            name: "cube".to_owned(),
            parameters: 1,
            replacement: r"\sq{#1}\cdot{#1}".to_owned(),
        },
    ];
    let first = adapter()?.parse(value.clone())?;
    let second = adapter()?.parse(value)?;
    assert_eq!(first, second);
    assert_eq!(first.macro_expansion_count(), 2);
    assert!(first.expanded_token_count() > first.input_token_count());
    assert!(matches!(first.outcome(), LatexParseOutcome::Parsed { .. }));
    Ok(())
}

#[test]
fn macro_conflict_recursion_parameter_and_expansion_limits_fail_closed() -> TestResult {
    let mut duplicate = request(r"\a");
    duplicate.macros = vec![
        LatexMacroDefinition {
            name: "a".to_owned(),
            parameters: 0,
            replacement: "x".to_owned(),
        },
        LatexMacroDefinition {
            name: "a".to_owned(),
            parameters: 0,
            replacement: "y".to_owned(),
        },
    ];
    assert_eq!(
        adapter()?.parse(duplicate),
        Err(LatexAdapterError::MacroConflict)
    );

    let mut reserved = request(r"\frac{x}{y}");
    reserved.macros = vec![LatexMacroDefinition {
        name: "frac".to_owned(),
        parameters: 0,
        replacement: "x".to_owned(),
    }];
    assert_eq!(
        adapter()?.parse(reserved),
        Err(LatexAdapterError::MacroConflict)
    );

    let mut recursive = request(r"\a");
    recursive.macros = vec![LatexMacroDefinition {
        name: "a".to_owned(),
        parameters: 0,
        replacement: r"\a".to_owned(),
    }];
    assert_eq!(
        adapter()?.parse(recursive),
        Err(LatexAdapterError::MacroRecursion)
    );

    let mut bad_parameter = request(r"\a{x}");
    bad_parameter.macros = vec![LatexMacroDefinition {
        name: "a".to_owned(),
        parameters: 1,
        replacement: "#2".to_owned(),
    }];
    assert_eq!(
        adapter()?.parse(bad_parameter),
        Err(LatexAdapterError::InvalidMacro)
    );

    let strict_limits = LatexAdapterLimits::new(LatexAdapterLimitConfig {
        macro_expansion_depth: 1,
        macro_expansions: 1,
        ..LatexAdapterLimitConfig::default()
    })?;
    let strict = LatexAdapter::new(strict_limits, MathAstLimits::default())?;
    let mut too_many = request(r"\a+\a");
    too_many.macros = vec![LatexMacroDefinition {
        name: "a".to_owned(),
        parameters: 0,
        replacement: "x".to_owned(),
    }];
    assert_eq!(
        strict.parse(too_many),
        Err(LatexAdapterError::MacroExpansionLimit)
    );
    let mut too_deep = request(r"\a");
    too_deep.macros = vec![
        LatexMacroDefinition {
            name: "a".to_owned(),
            parameters: 0,
            replacement: r"\b".to_owned(),
        },
        LatexMacroDefinition {
            name: "b".to_owned(),
            parameters: 0,
            replacement: "x".to_owned(),
        },
    ];
    assert_eq!(
        strict.parse(too_deep),
        Err(LatexAdapterError::MacroExpansionLimit)
    );
    Ok(())
}

#[test]
fn strict_json_rejects_duplicates_unknown_fields_and_wrong_versions() -> TestResult {
    let parser = adapter()?;
    let valid = format!(
        r#"{{"schema_version":"{LATEX_ADAPTER_SCHEMA_VERSION}","source":"x+1","macros":[]}}"#
    );
    assert!(parser.parse_json(valid.as_bytes()).is_ok());
    assert_eq!(
        parser.parse_json(
            format!(
                r#"{{"schema_version":"{LATEX_ADAPTER_SCHEMA_VERSION}","source":"x","source":"y"}}"#
            )
            .as_bytes()
        ),
        Err(LatexAdapterError::InvalidJson)
    );
    assert_eq!(
        parser.parse_json(
            format!(
                r#"{{"schema_version":"{LATEX_ADAPTER_SCHEMA_VERSION}","source":"x","unknown":true}}"#
            )
            .as_bytes()
        ),
        Err(LatexAdapterError::InvalidJson)
    );
    let mut wrong = request("x");
    wrong.schema_version = "hwpx-agent.latex-adapter/v0".to_owned();
    assert_eq!(
        parser.parse(wrong),
        Err(LatexAdapterError::UnsupportedVersion)
    );
    Ok(())
}

#[test]
fn unsupported_and_malformed_syntax_never_returns_a_partial_ast() -> TestResult {
    for source in [
        "",
        r"\unknown{x}",
        r"\frac{x}",
        r"\sqrt[]{x}",
        r"x<y<z",
        r"\begin{matrix}1\end{matrix}",
        r"x%comment",
        r"\lim_{x\to0}{x}",
    ] {
        assert!(adapter()?.parse(request(source)).is_err(), "{source}");
    }
    Ok(())
}

#[test]
fn source_token_macro_and_output_limits_are_finite() -> TestResult {
    let config = LatexAdapterLimitConfig {
        source_bytes: 8,
        input_tokens: 4,
        expanded_tokens: 4,
        parse_depth: 2,
        macro_definitions: 1,
        macro_parameters: 1,
        macro_expansion_depth: 1,
        macro_expansions: 1,
        macro_replacement_bytes: 8,
        total_macro_bytes: 8,
        ambiguity_sites: 2,
        ambiguity_candidates: 2,
        serialized_bytes: 512,
    };
    let limits = LatexAdapterLimits::new(config)?;
    let math_limits = MathAstLimits::new(MathAstLimitConfig::default())?;
    let parser = LatexAdapter::new(limits, math_limits)?;
    assert_eq!(
        parser.parse(request("123456789")),
        Err(LatexAdapterError::InputLimit)
    );
    assert_eq!(
        parser.parse(request("x+x+x")),
        Err(LatexAdapterError::TokenLimit)
    );
    assert!(matches!(
        parser.parse(request("x")),
        Err(LatexAdapterError::OutputLimit)
    ));
    assert_eq!(
        LatexAdapterLimits::new(LatexAdapterLimitConfig {
            ambiguity_candidates: 1,
            ..LatexAdapterLimitConfig::default()
        }),
        Err(LatexAdapterError::InvalidLimit)
    );
    let one_site = LatexAdapterLimits::new(LatexAdapterLimitConfig {
        ambiguity_sites: 1,
        ..LatexAdapterLimitConfig::default()
    })?;
    let one_site_parser = LatexAdapter::new(one_site, MathAstLimits::default())?;
    assert_eq!(
        one_site_parser.parse(request("2x+3y")),
        Err(LatexAdapterError::AmbiguityLimit)
    );
    let depth_parser = LatexAdapter::new(
        LatexAdapterLimits::new(LatexAdapterLimitConfig {
            parse_depth: 2,
            ..LatexAdapterLimitConfig::default()
        })?,
        MathAstLimits::default(),
    )?;
    assert_eq!(
        depth_parser.parse(request("{{{x}}}")),
        Err(LatexAdapterError::ParseDepthLimit)
    );
    Ok(())
}

#[test]
fn canonical_result_and_debug_are_deterministic_bounded_and_redacted() -> TestResult {
    let parser = adapter()?;
    let source = r"\frac{privateName+1}{2}";
    let first = parser.parse(request(source))?;
    let second = parser.parse(request(source))?;
    let limits = LatexAdapterLimits::default();
    assert_eq!(
        first.canonical_json(limits)?,
        second.canonical_json(limits)?
    );
    let debug = format!("{first:?}");
    assert!(!debug.contains("privateName"));
    assert!(!debug.contains(source));
    let request_debug = format!("{:?}", request(source));
    let macro_debug = format!(
        "{:?}",
        LatexMacroDefinition {
            name: "privateMacro".to_owned(),
            parameters: 1,
            replacement: "privateReplacement".to_owned(),
        }
    );
    assert!(!request_debug.contains(source));
    assert!(!macro_debug.contains("privateMacro"));
    assert!(!macro_debug.contains("privateReplacement"));
    for error in [
        LatexAdapterError::InvalidLimit,
        LatexAdapterError::InputLimit,
        LatexAdapterError::InvalidJson,
        LatexAdapterError::UnsupportedVersion,
        LatexAdapterError::InvalidMacro,
        LatexAdapterError::MacroConflict,
        LatexAdapterError::MacroRecursion,
        LatexAdapterError::MacroExpansionLimit,
        LatexAdapterError::TokenLimit,
        LatexAdapterError::ParseDepthLimit,
        LatexAdapterError::InvalidSyntax,
        LatexAdapterError::UnsupportedSyntax,
        LatexAdapterError::AmbiguityLimit,
        LatexAdapterError::MathAst,
        LatexAdapterError::OutputLimit,
        LatexAdapterError::Serialization,
    ] {
        assert!(error.code().starts_with("latex_adapter_"));
        assert!(!error.code().contains(source));
    }
    Ok(())
}

#[test]
fn explicit_tier_a_corpus_has_no_silent_ambiguity_or_approximation() -> TestResult {
    let corpus = [
        "0",
        "12.50",
        "x+1",
        "x-1",
        r"x\cdot y",
        "x/y",
        r"\frac{1}{x+1}",
        r"\frac{\frac{1}{x}}{2}",
        "x^2",
        "a_{n}",
        r"\sqrt{x}",
        r"\sqrt[3]{8}",
        r"\sin{x}",
        r"\sin^{2}{x}",
        r"\cos{\theta}",
        r"\log_{2}{x}",
        r"\ln{x}",
        r"\exp{x}",
        r"x\neq0",
        r"x\leq1",
        r"A\cup B",
        r"A\cap B",
        r"x\in A",
        r"A\subseteq B",
        r"P\land Q",
        r"P\lor Q",
        r"P\implies Q",
        r"\neg P",
        r"\sum_{i=1}^{n}{i}",
        r"\prod_{i=1}^{n}{i}",
        r"\int_{0}^{1}{x^2}",
        r"\iint_{0}^{1}{x}",
        r"\lim_{x=0}{x}",
        r"\dv{x^2}{x}",
        r"\pdv{x\cdot y}{x}",
        r"\vec{v}",
        r"\hat{x}",
        r"\left|x\right|",
        r"\left\{x+1\right\}",
        r"\binom{n}{r}",
        r"\set{x}{x>0}",
        r"x=\text{constant}",
        r"\mathbf{x}+\mathbb{R}",
        r"\operatorname{prob}{A}",
    ];
    for source in corpus {
        let result = adapter()?.parse(request(source))?;
        assert!(
            matches!(result.outcome(), LatexParseOutcome::Parsed { .. }),
            "{source}"
        );
    }
    Ok(())
}
