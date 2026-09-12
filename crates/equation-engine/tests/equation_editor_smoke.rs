use domain_ir::{MathAstDraft, MathAstLimitConfig, MathAstLimits};
use equation_engine::{
    EQEDIT_ADAPTER_SCHEMA_VERSION, EQEDIT_PROFILE_VERSION,
    EQUATION_EDITOR_SMOKE_EVIDENCE_SCHEMA_VERSION, EQUATION_EDITOR_SMOKE_PROFILE_VERSION,
    EQUATION_EDITOR_SMOKE_SCHEMA_VERSION, EQUATION_EDITOR_TARGET_EXECUTABLE_SHA256, EqEditEngine,
    EqEditLimits, EqEditParseRequestDraft, EquationEditorAutomationProof,
    EquationEditorManualAttestationState, EquationEditorManualProof, EquationEditorSmokeError,
    EquationEditorSmokeEvidenceDraft, EquationEditorSmokeEvidenceState,
    EquationEditorSmokeLimitConfig, EquationEditorSmokeLimits, EquationEditorSmokePlan,
    EquationEditorSmokePlanner, EquationEditorSmokeRequestDraft, EquationEditorSmokeSnapshot,
    EquationEditorSmokeSourceState, EquationEditorTargetIdentity, EquationEditorVerificationState,
};
use serde_json::Value;
use sha2::{Digest as _, Sha256};

type TestResult<T = ()> = Result<T, Box<dyn std::error::Error>>;

fn math_limits() -> Result<MathAstLimits, Box<dyn std::error::Error>> {
    Ok(MathAstLimits::new(MathAstLimitConfig::default())?)
}

fn planner() -> Result<EquationEditorSmokePlanner, Box<dyn std::error::Error>> {
    Ok(EquationEditorSmokePlanner::new(
        EquationEditorSmokeLimits::default(),
        math_limits()?,
        EqEditLimits::default(),
    ))
}

fn ast(source: &str) -> TestResult<MathAstDraft> {
    let parsed = EqEditEngine::new(EqEditLimits::default(), math_limits()?)?.parse(
        EqEditParseRequestDraft {
            schema_version: EQEDIT_ADAPTER_SCHEMA_VERSION.to_owned(),
            profile_version: EQEDIT_PROFILE_VERSION.to_owned(),
            source: source.to_owned(),
        },
    )?;
    Ok(serde_json::from_slice(
        &parsed.ast().canonical_json(math_limits()?)?,
    )?)
}

fn source() -> TestResult<EquationEditorSmokeSourceState> {
    let engine = EqEditEngine::new(EqEditLimits::default(), math_limits()?)?;
    let before = engine.compile(
        engine
            .parse(EqEditParseRequestDraft {
                schema_version: EQEDIT_ADAPTER_SCHEMA_VERSION.to_owned(),
                profile_version: EQEDIT_PROFILE_VERSION.to_owned(),
                source: "x + 1".to_owned(),
            })?
            .ast(),
    )?;
    Ok(EquationEditorSmokeSourceState {
        revision: "revision-1".to_owned(),
        artifact_sha256: "1".repeat(64),
        package_graph_sha256: "2".repeat(64),
        document_flow_sha256: "3".repeat(64),
        anchor_fingerprint_sha256: "4".repeat(64),
        object_id: 77,
        semantic_sha256: before.semantic_sha256().to_owned(),
        script_sha256: before.script_sha256().to_owned(),
        native_object_count: 1,
    })
}

fn request(before: &str, after: &str) -> TestResult<EquationEditorSmokeRequestDraft> {
    request_with_saved_script(before, after, &after.replace(' ', ""))
}

fn request_with_saved_script(
    before: &str,
    after: &str,
    saved_after_script: &str,
) -> TestResult<EquationEditorSmokeRequestDraft> {
    Ok(EquationEditorSmokeRequestDraft {
        schema_version: EQUATION_EDITOR_SMOKE_SCHEMA_VERSION.to_owned(),
        profile_version: EQUATION_EDITOR_SMOKE_PROFILE_VERSION.to_owned(),
        harness_sha256: "a".repeat(64),
        oracle_contract_sha256: "b".repeat(64),
        source: source()?,
        before_math_ast: ast(before)?,
        after_math_ast: ast(after)?,
        saved_after_script: saved_after_script.to_owned(),
    })
}

fn plan() -> TestResult<(EquationEditorSmokePlan, EquationEditorSmokeSourceState)> {
    let source = source()?;
    let plan = planner()?.build(request("x + 1", "x + 2")?, &source)?;
    Ok((plan, source))
}

fn snapshot_from_source(source: &EquationEditorSmokeSourceState) -> EquationEditorSmokeSnapshot {
    EquationEditorSmokeSnapshot {
        artifact_sha256: source.artifact_sha256.clone(),
        package_graph_sha256: source.package_graph_sha256.clone(),
        document_flow_sha256: source.document_flow_sha256.clone(),
        object_id: source.object_id,
        semantic_sha256: source.semantic_sha256.clone(),
        script_sha256: source.script_sha256.clone(),
        native_object_count: source.native_object_count,
    }
}

fn evidence(
    plan: &EquationEditorSmokePlan,
    source: &EquationEditorSmokeSourceState,
) -> EquationEditorSmokeEvidenceDraft {
    let after = EquationEditorSmokeSnapshot {
        artifact_sha256: "5".repeat(64),
        package_graph_sha256: "6".repeat(64),
        document_flow_sha256: "7".repeat(64),
        object_id: source.object_id,
        semantic_sha256: plan.after_semantic_sha256().to_owned(),
        script_sha256: plan.saved_after_script_sha256().to_owned(),
        native_object_count: source.native_object_count,
    };
    EquationEditorSmokeEvidenceDraft {
        schema_version: EQUATION_EDITOR_SMOKE_EVIDENCE_SCHEMA_VERSION.to_owned(),
        profile_version: EQUATION_EDITOR_SMOKE_PROFILE_VERSION.to_owned(),
        plan_sha256: plan.plan_sha256().to_owned(),
        source_state_sha256: plan.source_state_sha256().to_owned(),
        harness_sha256: "a".repeat(64),
        oracle_contract_sha256: "b".repeat(64),
        target: EquationEditorTargetIdentity {
            product: "Hangul 2020".to_owned(),
            prog_id: "HWPFrame.HwpObject.2".to_owned(),
            build: "11.0.0.9136".to_owned(),
            executable_sha256: EQUATION_EDITOR_TARGET_EXECUTABLE_SHA256.to_owned(),
            architecture: "x86".to_owned(),
            locale: "ko-KR".to_owned(),
        },
        state: EquationEditorSmokeEvidenceState::Succeeded,
        manual: EquationEditorManualProof {
            before_equation_matches_plan: EquationEditorManualAttestationState::UserAttested,
            double_click: EquationEditorManualAttestationState::UserAttested,
            editor_visible: EquationEditorManualAttestationState::UserAttested,
            one_token_change: EquationEditorManualAttestationState::UserAttested,
            editor_closed_after_commit: EquationEditorManualAttestationState::UserAttested,
            post_commit_equation_matches_plan: EquationEditorManualAttestationState::UserAttested,
            saved_as_after_hwpx: EquationEditorManualAttestationState::UserAttested,
            user_performed_all_clicks_and_typing:
                EquationEditorManualAttestationState::UserAttested,
            anomaly_reported: false,
            computer_use_click_or_type_invoked: false,
            operator_checklist_sha256: "e".repeat(64),
        },
        automation: EquationEditorAutomationProof {
            exact_target_preflight: EquationEditorVerificationState::Passed,
            immutable_input: EquationEditorVerificationState::Passed,
            initial_native_readback: EquationEditorVerificationState::Passed,
            saved_native_readback: EquationEditorVerificationState::Passed,
            reopen_native_readback: EquationEditorVerificationState::Passed,
            save: EquationEditorVerificationState::Passed,
            close: EquationEditorVerificationState::Passed,
            reopen: EquationEditorVerificationState::Passed,
            all_phases: EquationEditorVerificationState::Passed,
            trace_sha256: "f".repeat(64),
            oracle_receipt_sha256: "0".repeat(64),
        },
        before: snapshot_from_source(source),
        after_save: after.clone(),
        after_reopen: after,
        silent_fallback_count: 0,
        text_fallback_count: 0,
        image_fallback_count: 0,
        object_replacement_count: 0,
    }
}

fn verify(
    plan: &EquationEditorSmokePlan,
    draft: &EquationEditorSmokeEvidenceDraft,
) -> Result<equation_engine::EquationEditorSmokeReceipt, EquationEditorSmokeError> {
    let bytes = serde_json::to_vec(draft).map_err(|_| EquationEditorSmokeError::Serialization)?;
    let digest = hex::encode(Sha256::digest(&bytes));
    planner()
        .map_err(|_| EquationEditorSmokeError::InvalidLimit)?
        .verify_evidence_json(plan, &bytes, &digest)
}

#[test]
fn exact_one_token_plan_and_combined_evidence_pass_deterministically() -> TestResult {
    let source = source()?;
    let first = planner()?.build(request("x + 1", "x + 2")?, &source)?;
    let second = planner()?.build(request("x + 1", "x + 2")?, &source)?;
    assert_eq!(first.plan_sha256(), second.plan_sha256());
    assert_eq!(first.changed_token_index(), second.changed_token_index());
    assert_eq!(first.before_script(), "{x} + {1}");
    assert_eq!(first.after_script(), "{x} + {2}");
    assert_eq!(first.saved_after_script(), "x+2");
    assert_eq!(first.changed_token_index(), 5);
    assert_ne!(
        first.before_semantic_sha256(),
        first.after_semantic_sha256()
    );
    assert_ne!(first.before_script_sha256(), first.after_script_sha256());
    assert_ne!(
        first.after_script_sha256(),
        first.saved_after_script_sha256()
    );

    let receipt = verify(&first, &evidence(&first, &source))?;
    assert!(receipt.manual_double_click_user_attested());
    let receipt_json =
        String::from_utf8(receipt.canonical_json(EquationEditorSmokeLimits::default())?)?;
    assert!(receipt_json.contains("\"manual_double_click_state\":\"user_attested\""));
    assert!(!receipt_json.contains("screenshot"));
    assert!(receipt.automated_save_reopen_verified());
    assert!(receipt.actual_hangul());
    let json = String::from_utf8(receipt.canonical_json(EquationEditorSmokeLimits::default())?)?;
    assert!(json.contains("\"silent_fallback_count\":0"));
    assert!(json.contains("\"render_state\":\"not_run\""));
    assert!(json.contains("\"p07_state\":\"in_progress\""));
    assert!(json.contains("\"product_complete\":false"));
    assert!(!json.contains("x + 1"));
    Ok(())
}

#[test]
fn private_plan_loader_recomputes_file_source_semantic_token_and_plan_hashes() -> TestResult {
    let (plan, source) = plan()?;
    let bytes = plan.canonical_json(EquationEditorSmokeLimits::default())?;
    let digest = hex::encode(Sha256::digest(&bytes));
    let loaded = planner()?.load_plan_json(&bytes, &digest, &source)?;
    assert_eq!(loaded, plan);

    let mut appended = bytes.clone();
    appended.push(b' ');
    assert_eq!(
        planner()?.load_plan_json(&appended, &digest, &source),
        Err(EquationEditorSmokeError::UntrustedPlan)
    );

    let mut value: Value = serde_json::from_slice(&bytes)?;
    value["changed_token_index"] = Value::from(0);
    let tampered = serde_json::to_vec(&value)?;
    let tampered_digest = hex::encode(Sha256::digest(&tampered));
    assert_eq!(
        planner()?.load_plan_json(&tampered, &tampered_digest, &source),
        Err(EquationEditorSmokeError::PlanMismatch)
    );

    let mut legacy: Value = serde_json::from_slice(&bytes)?;
    legacy["schema_version"] = Value::String("hwpx-agent.equation-editor-smoke/v2".to_owned());
    let legacy_object = legacy.as_object_mut().ok_or("plan must be an object")?;
    legacy_object.remove("saved_after_script");
    legacy_object.remove("saved_after_script_sha256");
    let legacy_bytes = serde_json::to_vec(&legacy)?;
    let legacy_digest = hex::encode(Sha256::digest(&legacy_bytes));
    assert_eq!(
        planner()?.load_plan_json(&legacy_bytes, &legacy_digest, &source),
        Err(EquationEditorSmokeError::InvalidJson)
    );

    let mut relabeled: Value = serde_json::from_slice(&bytes)?;
    relabeled["schema_version"] = Value::String("hwpx-agent.equation-editor-smoke/v2".to_owned());
    let relabeled_bytes = serde_json::to_vec(&relabeled)?;
    let relabeled_digest = hex::encode(Sha256::digest(&relabeled_bytes));
    assert_eq!(
        planner()?.load_plan_json(&relabeled_bytes, &relabeled_digest, &source),
        Err(EquationEditorSmokeError::UnsupportedVersion)
    );

    let mut stale = source.clone();
    stale.artifact_sha256 = "f".repeat(64);
    assert_eq!(
        planner()?.load_plan_json(&bytes, &digest, &stale),
        Err(EquationEditorSmokeError::SourceStateDrift)
    );
    Ok(())
}

#[test]
fn no_op_multi_token_and_token_cardinality_changes_fail_closed() -> TestResult {
    let source = source()?;
    assert_eq!(
        planner()?.build(request("x + 1", "x + 1")?, &source),
        Err(EquationEditorSmokeError::NoSemanticChange)
    );
    assert_eq!(
        planner()?.build(request("x + 1", "y + 2")?, &source),
        Err(EquationEditorSmokeError::TokenChangeMismatch)
    );
    assert_eq!(
        planner()?.build(request("x + 1", "x + 1 + 2")?, &source),
        Err(EquationEditorSmokeError::TokenChangeMismatch)
    );
    Ok(())
}

#[test]
fn saved_native_script_must_match_the_planned_after_math() -> TestResult {
    let source = source()?;
    assert_eq!(
        planner()?.build(request_with_saved_script("x + 1", "x + 2", "y+2")?, &source,),
        Err(EquationEditorSmokeError::EditorCanonicalizationMismatch)
    );
    assert_eq!(
        planner()?.build(request_with_saved_script("x + 1", "x + 2", "x+3")?, &source,),
        Err(EquationEditorSmokeError::EditorCanonicalizationMismatch)
    );
    Ok(())
}

#[test]
fn request_and_build_recheck_complete_source_and_semantic_state() -> TestResult {
    let source = source()?;
    let mut stale = source.clone();
    stale.document_flow_sha256 = "f".repeat(64);
    assert_eq!(
        planner()?.build(request("x + 1", "x + 2")?, &stale),
        Err(EquationEditorSmokeError::SourceStateDrift)
    );

    let mut semantic_drift = request("x + 1", "x + 2")?;
    semantic_drift.source.semantic_sha256 = "f".repeat(64);
    assert_eq!(
        planner()?.build(semantic_drift.clone(), &semantic_drift.source.clone()),
        Err(EquationEditorSmokeError::SourceSemanticDrift)
    );

    let json = serde_json::to_vec(&request("x + 1", "x + 2")?)?;
    assert!(planner()?.build_json(&json, &source).is_ok());
    assert_eq!(
        planner()?.build_json(&json, &stale),
        Err(EquationEditorSmokeError::SourceStateDrift)
    );
    Ok(())
}

#[test]
fn strict_request_json_versions_identity_and_limits_are_enforced() -> TestResult {
    let source = source()?;
    let valid = serde_json::to_vec(&request("x + 1", "x + 2")?)?;
    let duplicate = String::from_utf8(valid.clone())?.replacen(
        "\"schema_version\":",
        "\"schema_version\":\"duplicate\",\"schema_version\":",
        1,
    );
    assert_eq!(
        planner()?.build_json(duplicate.as_bytes(), &source),
        Err(EquationEditorSmokeError::InvalidJson)
    );
    let mut unknown: Value = serde_json::from_slice(&valid)?;
    unknown["raw_action_id"] = Value::String("forbidden".to_owned());
    assert_eq!(
        planner()?.build_json(&serde_json::to_vec(&unknown)?, &source),
        Err(EquationEditorSmokeError::InvalidJson)
    );
    let mut wrong_profile = request("x + 1", "x + 2")?;
    wrong_profile.profile_version = "wrong".to_owned();
    assert_eq!(
        planner()?.build(wrong_profile, &source),
        Err(EquationEditorSmokeError::UnsupportedProfile)
    );
    let invalid = EquationEditorSmokeLimitConfig {
        request_bytes: 0,
        ..EquationEditorSmokeLimitConfig::default()
    };
    assert_eq!(
        EquationEditorSmokeLimits::new(invalid),
        Err(EquationEditorSmokeError::InvalidLimit)
    );
    Ok(())
}

#[test]
fn evidence_hash_strict_json_profile_and_target_are_exact() -> TestResult {
    let (plan, source) = plan()?;
    let draft = evidence(&plan, &source);
    let bytes = serde_json::to_vec(&draft)?;
    let digest = hex::encode(Sha256::digest(&bytes));
    assert_eq!(
        planner()?.verify_evidence_json(&plan, &[bytes.clone(), vec![b' ']].concat(), &digest),
        Err(EquationEditorSmokeError::UntrustedEvidence)
    );
    let mut value = serde_json::to_value(&draft)?;
    value["target"]["build"] = Value::String("11.0.0.9137".to_owned());
    let changed = serde_json::to_vec(&value)?;
    let changed_digest = hex::encode(Sha256::digest(&changed));
    assert_eq!(
        planner()?.verify_evidence_json(&plan, &changed, &changed_digest),
        Err(EquationEditorSmokeError::TargetMismatch)
    );
    value["unexpected"] = Value::Bool(true);
    let unknown = serde_json::to_vec(&value)?;
    let unknown_digest = hex::encode(Sha256::digest(&unknown));
    assert_eq!(
        planner()?.verify_evidence_json(&plan, &unknown, &unknown_digest),
        Err(EquationEditorSmokeError::InvalidJson)
    );
    Ok(())
}

#[test]
fn manual_automation_and_effect_proofs_are_all_mandatory() -> TestResult {
    let (plan, source) = plan()?;
    let mut failed = evidence(&plan, &source);
    failed.state = EquationEditorSmokeEvidenceState::EffectUnknown;
    assert_eq!(
        verify(&plan, &failed),
        Err(EquationEditorSmokeError::EffectNotProven)
    );
    let mut manual = evidence(&plan, &source);
    manual.manual.double_click = EquationEditorManualAttestationState::Failed;
    assert_eq!(
        verify(&plan, &manual),
        Err(EquationEditorSmokeError::ManualEvidenceIncomplete)
    );
    let mut computer_use = evidence(&plan, &source);
    computer_use.manual.computer_use_click_or_type_invoked = true;
    assert_eq!(
        verify(&plan, &computer_use),
        Err(EquationEditorSmokeError::ManualEvidenceIncomplete)
    );
    let mut anomaly = evidence(&plan, &source);
    anomaly.manual.anomaly_reported = true;
    assert_eq!(
        verify(&plan, &anomaly),
        Err(EquationEditorSmokeError::ManualEvidenceIncomplete)
    );
    let mut not_attested = evidence(&plan, &source);
    not_attested.manual.saved_as_after_hwpx = EquationEditorManualAttestationState::NotRun;
    assert_eq!(
        verify(&plan, &not_attested),
        Err(EquationEditorSmokeError::ManualEvidenceIncomplete)
    );
    let mut invalid_checklist = evidence(&plan, &source);
    invalid_checklist.manual.operator_checklist_sha256 = "not-a-digest".to_owned();
    assert_eq!(
        verify(&plan, &invalid_checklist),
        Err(EquationEditorSmokeError::InvalidIdentity)
    );
    let mut automated = evidence(&plan, &source);
    automated.automation.reopen_native_readback = EquationEditorVerificationState::NotRun;
    assert_eq!(
        verify(&plan, &automated),
        Err(EquationEditorSmokeError::AutomationEvidenceIncomplete)
    );
    Ok(())
}

#[test]
fn v2_screenshot_evidence_cannot_be_relabeled_as_v3() -> TestResult {
    let (plan, source) = plan()?;
    let mut value = serde_json::to_value(evidence(&plan, &source))?;
    let manual = value["manual"]
        .as_object_mut()
        .ok_or("manual proof must be an object")?;
    manual.insert(
        "before_screenshot_sha256".to_owned(),
        Value::String("8".repeat(64)),
    );
    let bytes = serde_json::to_vec(&value)?;
    let digest = hex::encode(Sha256::digest(&bytes));
    assert_eq!(
        planner()?.verify_evidence_json(&plan, &bytes, &digest),
        Err(EquationEditorSmokeError::InvalidJson)
    );
    Ok(())
}

#[test]
fn object_semantic_graph_flow_reopen_and_fallback_drift_fail() -> TestResult {
    let (plan, source) = plan()?;
    let mut object = evidence(&plan, &source);
    object.after_save.object_id += 1;
    object.after_reopen.object_id += 1;
    assert_eq!(
        verify(&plan, &object),
        Err(EquationEditorSmokeError::MutationMismatch)
    );
    let mut reopen = evidence(&plan, &source);
    reopen.after_reopen.artifact_sha256 = "f".repeat(64);
    assert_eq!(
        verify(&plan, &reopen),
        Err(EquationEditorSmokeError::MutationMismatch)
    );
    let mut graph = evidence(&plan, &source);
    graph.after_save.package_graph_sha256 = source.package_graph_sha256.clone();
    graph.after_reopen.package_graph_sha256 = source.package_graph_sha256.clone();
    assert_eq!(
        verify(&plan, &graph),
        Err(EquationEditorSmokeError::MutationMismatch)
    );
    let mut fallback = evidence(&plan, &source);
    fallback.silent_fallback_count = 1;
    assert_eq!(
        verify(&plan, &fallback),
        Err(EquationEditorSmokeError::FallbackDetected)
    );
    Ok(())
}

#[test]
fn debug_surfaces_redact_scripts_objects_and_digests() -> TestResult {
    let (plan, source) = plan()?;
    let draft = evidence(&plan, &source);
    let receipt = verify(&plan, &draft)?;
    let debug = format!("{source:?} {plan:?} {draft:?} {receipt:?}");
    for secret in [
        "revision-1",
        "x + 1",
        "x + 2",
        "x+1",
        "x+2",
        plan.plan_sha256(),
        receipt.evidence_sha256(),
        &source.object_id.to_string(),
    ] {
        assert!(!debug.contains(secret), "debug leaked {secret}");
    }
    Ok(())
}

#[test]
fn all_public_error_codes_are_stable() {
    for error in [
        EquationEditorSmokeError::InvalidLimit,
        EquationEditorSmokeError::InvalidJson,
        EquationEditorSmokeError::UnsupportedVersion,
        EquationEditorSmokeError::UnsupportedProfile,
        EquationEditorSmokeError::InvalidIdentity,
        EquationEditorSmokeError::SourceStateDrift,
        EquationEditorSmokeError::SourceSemanticDrift,
        EquationEditorSmokeError::MathAst,
        EquationEditorSmokeError::EqEdit,
        EquationEditorSmokeError::SemanticRoundtrip,
        EquationEditorSmokeError::NoSemanticChange,
        EquationEditorSmokeError::EditorCanonicalizationMismatch,
        EquationEditorSmokeError::TokenChangeMismatch,
        EquationEditorSmokeError::UntrustedEvidence,
        EquationEditorSmokeError::UntrustedPlan,
        EquationEditorSmokeError::PlanMismatch,
        EquationEditorSmokeError::EvidenceMismatch,
        EquationEditorSmokeError::TargetMismatch,
        EquationEditorSmokeError::EffectNotProven,
        EquationEditorSmokeError::ManualEvidenceIncomplete,
        EquationEditorSmokeError::AutomationEvidenceIncomplete,
        EquationEditorSmokeError::MutationMismatch,
        EquationEditorSmokeError::FallbackDetected,
        EquationEditorSmokeError::OutputLimit,
        EquationEditorSmokeError::Serialization,
    ] {
        assert!(error.code().starts_with("equation_editor_smoke_"));
    }
}
