use domain_ir::{MathAstLimitConfig, MathAstLimits};
use equation_engine::{
    EQEDIT_ADAPTER_SCHEMA_VERSION, EQEDIT_PROFILE_VERSION, EqEditEngine, EqEditLimits,
    EqEditParseRequestDraft, EquationCorpusError, EquationCorpusLimitConfig, EquationCorpusLimits,
    EquationCorpusRunner, LATEX_ADAPTER_SCHEMA_VERSION, LatexAdapter, LatexAdapterLimits,
    LatexParseOutcome, LatexParseRequestDraft, LegacyEquationScript, MathMlAdapterLimits,
};
use serde_json::Value;
use sha2::{Digest as _, Sha256};

type TestResult<T = ()> = Result<T, Box<dyn std::error::Error>>;

const MANIFEST: &[u8] = include_bytes!(
    "../../../implementation/p07/fixtures/p07-08-equation-corpus.current-2020.v1.json"
);
const MANIFEST_SHA256: &str = "8893bd3169f40a5b49472cbb6c2dd4a578202b338d47d49270d237084ad6bd3f";

fn limits() -> Result<EquationCorpusLimits, EquationCorpusError> {
    EquationCorpusLimits::new(EquationCorpusLimitConfig::default())
}

fn runner() -> Result<EquationCorpusRunner, EquationCorpusError> {
    EquationCorpusRunner::new(
        limits()?,
        MathAstLimits::new(MathAstLimitConfig::default())
            .map_err(|_| EquationCorpusError::InvalidLimit)?,
        LatexAdapterLimits::default(),
        MathMlAdapterLimits::default(),
        EqEditLimits::default(),
    )
}

#[test]
fn tier_b_eqedit_sources_roundtrip_individually() -> TestResult {
    let math_limits = MathAstLimits::new(MathAstLimitConfig::default())?;
    let engine = EqEditEngine::new(EqEditLimits::default(), math_limits)?;
    for source in [
        "MATRIX {{1} & {2} # {3} & {4}}",
        "PMATRIX {{1} & {2} # {3} & {4}}",
        "BMATRIX {{1} & {2} # {3} & {4}}",
        "DMATRIX {{1} & {2} # {3} & {4}}",
        "CASES {{x} & {x > 0} # {- {x}} & {x < 0}}",
        "PILE {{x = 1} & {y = 2} # {x = 3} & {y = 4}}",
        "LEFT { {x} VERT {x > 0} RIGHT }",
        "DINT _ {0} ^ {1} {x}",
        "OTINT _ {0} ^ {1} {x}",
        "OVERLINE {x}",
        "UNDERLINE {x}",
        "BINOM {n} {r}",
        "Alpha + omega + INF + EMPTYSET",
    ] {
        let ast = engine
            .parse(EqEditParseRequestDraft {
                schema_version: EQEDIT_ADAPTER_SCHEMA_VERSION.to_owned(),
                profile_version: EQEDIT_PROFILE_VERSION.to_owned(),
                source: source.to_owned(),
            })?
            .ast()
            .clone();
        let script = engine.compile(&ast)?;
        let reparsed = engine.parse(EqEditParseRequestDraft {
            schema_version: EQEDIT_ADAPTER_SCHEMA_VERSION.to_owned(),
            profile_version: EQEDIT_PROFILE_VERSION.to_owned(),
            source: script.script().to_owned(),
        })?;
        assert!(ast.semantically_eq(reparsed.ast()), "{source}");
    }
    Ok(())
}

#[test]
fn tier_a_sources_roundtrip_individually() -> TestResult {
    let math_limits = MathAstLimits::new(MathAstLimitConfig::default())?;
    let latex = LatexAdapter::new(LatexAdapterLimits::default(), math_limits)?;
    let engine = EqEditEngine::new(EqEditLimits::default(), math_limits)?;
    let manifest: Value = serde_json::from_slice(MANIFEST)?;
    let cases = manifest["cases"]
        .as_array()
        .ok_or_else(|| std::io::Error::other("manifest cases missing"))?;
    for case in cases {
        if case["tier"] != "a" {
            continue;
        }
        let source = case["source"]
            .as_str()
            .ok_or_else(|| std::io::Error::other("case source missing"))?;
        let parsed = latex.parse(LatexParseRequestDraft {
            schema_version: LATEX_ADAPTER_SCHEMA_VERSION.to_owned(),
            source: source.to_owned(),
            macros: Vec::new(),
        })?;
        let LatexParseOutcome::Parsed { ast } = parsed.outcome() else {
            panic!("ambiguous Tier A source: {source}");
        };
        let script = engine
            .compile(ast)
            .unwrap_or_else(|error| panic!("Tier A compile failed for {source}: {error:?}"));
        let reparsed = engine.parse(EqEditParseRequestDraft {
            schema_version: EQEDIT_ADAPTER_SCHEMA_VERSION.to_owned(),
            profile_version: EQEDIT_PROFILE_VERSION.to_owned(),
            source: script.script().to_owned(),
        })?;
        assert!(ast.semantically_eq(reparsed.ast()), "{source}");
    }
    Ok(())
}

fn resigned(mutator: impl FnOnce(&mut Value)) -> TestResult<(Vec<u8>, String)> {
    let mut value: Value = serde_json::from_slice(MANIFEST)?;
    mutator(&mut value);
    let bytes = serde_json::to_vec(&value)?;
    let digest = hex::encode(Sha256::digest(&bytes));
    Ok((bytes, digest))
}

#[test]
fn hash_pinned_current_manifest_passes_all_component_tiers() -> TestResult {
    assert_eq!(hex::encode(Sha256::digest(MANIFEST)), MANIFEST_SHA256);
    let receipt = runner()?.run_json(MANIFEST, MANIFEST_SHA256)?;
    assert_eq!(receipt.total_cases(), 64);
    assert_eq!(receipt.tier_a_semantic_passed(), 44);
    assert_eq!(receipt.tier_b_semantic_passed(), 14);
    assert_eq!(receipt.tier_c_preserve_passed(), 2);
    assert_eq!(receipt.tier_c_negative_passed(), 4);
    assert_eq!(receipt.silent_approximation_count(), 0);
    assert_eq!(receipt.tier_b_target_state(), "not_run");

    let first = receipt.canonical_json(limits()?)?;
    let second = runner()?
        .run_json(MANIFEST, MANIFEST_SHA256)?
        .canonical_json(limits()?)?;
    assert_eq!(first, second);
    let text = String::from_utf8(first)?;
    assert!(text.contains("\"actual_hangul\":false"));
    assert!(text.contains("\"product_complete\":false"));
    assert!(text.contains("\"tier_a_pass_millionths\":1000000"));
    assert!(text.contains("\"tier_b_component_pass_millionths\":1000000"));
    assert!(!text.contains("PHANTOM"));
    assert!(!text.contains("constant"));
    Ok(())
}

#[test]
fn manifest_hash_and_strict_json_tampering_fail_closed() -> TestResult {
    let mut tampered = MANIFEST.to_vec();
    tampered.push(b' ');
    assert_eq!(
        runner()?.run_json(&tampered, MANIFEST_SHA256),
        Err(EquationCorpusError::UntrustedManifest)
    );

    let (unknown, digest) = resigned(|value| {
        value["unexpected"] = Value::Bool(true);
    })?;
    assert_eq!(
        runner()?.run_json(&unknown, &digest),
        Err(EquationCorpusError::InvalidManifest)
    );

    let duplicate =
        br#"{"schema_version":"a","schema_version":"b","profile_version":"x","cases":[]}"#;
    let duplicate_digest = hex::encode(Sha256::digest(duplicate));
    assert_eq!(
        runner()?.run_json(duplicate, &duplicate_digest),
        Err(EquationCorpusError::InvalidManifest)
    );
    Ok(())
}

#[test]
fn profile_identity_case_identity_and_tier_completeness_are_exact() -> TestResult {
    let (profile, digest) = resigned(|value| {
        value["profile_version"] = Value::String("wrong".to_owned());
    })?;
    assert_eq!(
        runner()?.run_json(&profile, &digest),
        Err(EquationCorpusError::UnsupportedProfile)
    );

    let (duplicate, digest) = resigned(|value| {
        if let Some(cases) = value["cases"].as_array_mut() {
            cases[1]["id"] = cases[0]["id"].clone();
        }
    })?;
    assert_eq!(
        runner()?.run_json(&duplicate, &digest),
        Err(EquationCorpusError::InvalidCase)
    );

    let (incomplete, digest) = resigned(|value| {
        if let Some(cases) = value["cases"].as_array_mut() {
            cases.retain(|case| case["tier"] != "b");
        }
    })?;
    assert_eq!(
        runner()?.run_json(&incomplete, &digest),
        Err(EquationCorpusError::IncompleteTier)
    );
    Ok(())
}

#[test]
fn positive_adapter_failure_and_tier_policy_do_not_approximate() -> TestResult {
    let (unsupported, digest) = resigned(|value| {
        value["cases"][0]["source"] = Value::String("\\unknowncommand{x}".to_owned());
    })?;
    assert_eq!(
        runner()?.run_json(&unsupported, &digest),
        Err(EquationCorpusError::Adapter)
    );

    let (wrong_policy, digest) = resigned(|value| {
        value["cases"][0]["expectation"] = Value::String("preserve_exact".to_owned());
    })?;
    assert_eq!(
        runner()?.run_json(&wrong_policy, &digest),
        Err(EquationCorpusError::TierPolicy)
    );
    Ok(())
}

#[test]
fn negative_cases_require_the_exact_rejection_without_silent_acceptance() -> TestResult {
    let (accepted, digest) = resigned(|value| {
        value["cases"][60]["source"] = Value::String("x + 1".to_owned());
    })?;
    assert_eq!(
        runner()?.run_json(&accepted, &digest),
        Err(EquationCorpusError::SilentApproximation)
    );

    let (wrong_error, digest) = resigned(|value| {
        value["cases"][60]["expected_error_code"] =
            Value::String("eqedit_invalid_syntax".to_owned());
    })?;
    assert_eq!(
        runner()?.run_json(&wrong_error, &digest),
        Err(EquationCorpusError::NegativeMismatch)
    );
    Ok(())
}

#[test]
fn legacy_boundary_preserves_exact_bytes_and_redacts_debug() -> TestResult {
    let source = "SCALE 70 {비밀}".as_bytes().to_vec();
    let digest = hex::encode(Sha256::digest(&source));
    let admitted = LegacyEquationScript::new(source.clone(), &digest, limits()?)?;
    assert_eq!(admitted.preserved_bytes(), source);
    assert_eq!(admitted.sha256(), digest);
    let debug = format!("{admitted:?}");
    assert!(!debug.contains("비밀"));
    assert!(!debug.contains(&digest));

    assert_eq!(
        LegacyEquationScript::new(source.clone(), &"0".repeat(64), limits()?),
        Err(EquationCorpusError::LegacyBoundary)
    );
    assert_eq!(
        LegacyEquationScript::new(vec![0xff], &hex::encode(Sha256::digest([0xff])), limits()?),
        Err(EquationCorpusError::LegacyBoundary)
    );
    assert_eq!(
        LegacyEquationScript::new(
            vec![b'x', 0],
            &hex::encode(Sha256::digest([b'x', 0])),
            limits()?
        ),
        Err(EquationCorpusError::LegacyBoundary)
    );
    Ok(())
}

#[test]
fn finite_boundaries_and_error_codes_are_stable() -> TestResult {
    let invalid = EquationCorpusLimitConfig {
        manifest_bytes: 0,
        ..EquationCorpusLimitConfig::default()
    };
    assert_eq!(
        EquationCorpusLimits::new(invalid),
        Err(EquationCorpusError::InvalidLimit)
    );
    assert_eq!(
        runner()?.run_json(&[], MANIFEST_SHA256),
        Err(EquationCorpusError::ManifestLimit)
    );
    assert_eq!(
        runner()?.run_json(MANIFEST, "ABC"),
        Err(EquationCorpusError::InvalidDigest)
    );
    for error in [
        EquationCorpusError::InvalidLimit,
        EquationCorpusError::ManifestLimit,
        EquationCorpusError::InvalidDigest,
        EquationCorpusError::UntrustedManifest,
        EquationCorpusError::InvalidManifest,
        EquationCorpusError::UnsupportedProfile,
        EquationCorpusError::InvalidCase,
        EquationCorpusError::IncompleteTier,
        EquationCorpusError::TierPolicy,
        EquationCorpusError::Adapter,
        EquationCorpusError::SemanticRoundtrip,
        EquationCorpusError::LegacyBoundary,
        EquationCorpusError::Preservation,
        EquationCorpusError::NegativeMismatch,
        EquationCorpusError::SilentApproximation,
        EquationCorpusError::CountOverflow,
        EquationCorpusError::OutputLimit,
        EquationCorpusError::Serialization,
    ] {
        assert!(error.code().starts_with("equation_corpus_"));
    }
    Ok(())
}

#[test]
fn corpus_debug_does_not_expose_manifest_content_or_digest() -> TestResult {
    let receipt = runner()?.run_json(MANIFEST, MANIFEST_SHA256)?;
    let debug = format!("{receipt:?}");
    assert!(!debug.contains(MANIFEST_SHA256));
    assert!(!debug.contains("PHANTOM"));
    assert!(!debug.contains("constant"));
    Ok(())
}
