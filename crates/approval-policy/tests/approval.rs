use std::collections::BTreeSet;
use std::error::Error;

use approval_policy::{
    ApprovalError, ApprovalEvaluator, ApprovalPolicy, ApprovalScope, ConfirmationAuthority,
    ConfirmationToken, EffectKind, EffectRequest,
};

type TestResult = Result<(), Box<dyn Error>>;

const SECRET: &[u8] = b"approval-policy-test-secret-key-0001";
const NOW: u64 = 2_000_000_000;

fn digest(character: char) -> String {
    character.to_string().repeat(64)
}

fn request(effect: EffectKind, suffix: &str) -> Result<EffectRequest, ApprovalError> {
    EffectRequest::new(
        format!("op_operation{suffix}"),
        digest('a'),
        digest('b'),
        effect,
        digest('c'),
        digest('d'),
        NOW,
    )
}

fn policy(effect: EffectKind, capacity: usize) -> Result<ApprovalPolicy, ApprovalError> {
    ApprovalPolicy::new([effect], 120, capacity)
}

fn token(
    authority: &ConfirmationAuthority,
    request: &EffectRequest,
    suffix: &str,
) -> Result<ConfirmationToken, ApprovalError> {
    authority.mint(format!("cnf_confirm{suffix}"), request, true, NOW, NOW + 60)
}

#[test]
fn deny_all_rejects_even_a_valid_scope_and_confirmation() -> TestResult {
    let request = request(EffectKind::GitCommit, "0001")?;
    let authority = ConfirmationAuthority::new(SECRET)?;
    let token = token(&authority, &request, "0001")?;
    let mut evaluator = ApprovalEvaluator::new(ApprovalPolicy::deny_all()?, SECRET)?;
    let scopes = BTreeSet::from([ApprovalScope::WorkstationControl]);
    assert_eq!(
        evaluator.authorize(&request, &scopes, Some(&token), NOW + 1),
        Err(ApprovalError::DeniedByPolicy)
    );
    Ok(())
}

#[test]
fn allowlist_still_requires_scope_and_fresh_confirmation() -> TestResult {
    let request = request(EffectKind::AutomationExecute, "0001")?;
    let mut evaluator = ApprovalEvaluator::new(policy(EffectKind::AutomationExecute, 8)?, SECRET)?;
    assert_eq!(
        evaluator.authorize(&request, &BTreeSet::new(), None, NOW + 1),
        Err(ApprovalError::MissingScope)
    );
    let scopes = BTreeSet::from([ApprovalScope::AutomationUse]);
    assert_eq!(
        evaluator.authorize(&request, &scopes, None, NOW + 1),
        Err(ApprovalError::ConfirmationRequired)
    );
    Ok(())
}

#[test]
fn exact_confirmation_authorizes_once_and_emits_bounded_audit_receipt() -> TestResult {
    let request = request(EffectKind::ExternalInvoke, "0001")?;
    let authority = ConfirmationAuthority::new(SECRET)?;
    let token = token(&authority, &request, "0001")?;
    let scopes = BTreeSet::from([ApprovalScope::ExternalServiceUse]);
    let mut evaluator = ApprovalEvaluator::new(policy(EffectKind::ExternalInvoke, 8)?, SECRET)?;
    let authorized = evaluator.authorize(&request, &scopes, Some(&token), NOW + 1)?;
    assert_eq!(authorized.effect(), EffectKind::ExternalInvoke);
    let receipt = serde_json::to_string(authorized.receipt())?;
    assert!(receipt.contains("hwpx-agent.approval-receipt/v1"));
    assert!(!receipt.contains("op_operation0001"));
    assert!(!receipt.contains(token.encoded()));
    assert_eq!(
        evaluator.authorize(&request, &scopes, Some(&token), NOW + 2),
        Err(ApprovalError::ConfirmationReplay)
    );
    Ok(())
}

#[test]
fn confirmation_is_bound_to_actor_tenant_effect_target_plan_and_operation() -> TestResult {
    let original = request(EffectKind::GitCommit, "0001")?;
    let authority = ConfirmationAuthority::new(SECRET)?;
    let token = token(&authority, &original, "0001")?;
    let scopes = BTreeSet::from([ApprovalScope::WorkstationControl]);
    let mut evaluator = ApprovalEvaluator::new(policy(EffectKind::GitCommit, 8)?, SECRET)?;
    let drifted = EffectRequest::new(
        "op_operation0002".to_owned(),
        digest('a'),
        digest('b'),
        EffectKind::GitCommit,
        digest('c'),
        digest('d'),
        NOW,
    )?;
    assert_eq!(
        evaluator.authorize(&drifted, &scopes, Some(&token), NOW + 1),
        Err(ApprovalError::ConfirmationMismatch)
    );

    let other_effect = request(EffectKind::AutomationExecute, "0001")?;
    let other_scopes = BTreeSet::from([ApprovalScope::AutomationUse]);
    let mut other_evaluator =
        ApprovalEvaluator::new(policy(EffectKind::AutomationExecute, 8)?, SECRET)?;
    assert_eq!(
        other_evaluator.authorize(&other_effect, &other_scopes, Some(&token), NOW + 1),
        Err(ApprovalError::ConfirmationMismatch)
    );
    Ok(())
}

#[test]
fn unsigned_tampered_expired_and_future_tokens_fail_closed() -> TestResult {
    let request = request(EffectKind::PrintExecute, "0001")?;
    let authority = ConfirmationAuthority::new(SECRET)?;
    let original = token(&authority, &request, "0001")?;
    let mut encoded = original.encoded().to_owned();
    let replacement = if encoded.ends_with('a') { 'b' } else { 'a' };
    encoded.pop();
    encoded.push(replacement);
    let tampered = ConfirmationToken::parse(encoded)?;
    let scopes = BTreeSet::from([ApprovalScope::PrintExecute]);
    let mut evaluator = ApprovalEvaluator::new(policy(EffectKind::PrintExecute, 8)?, SECRET)?;
    assert_eq!(
        evaluator.authorize(&request, &scopes, Some(&tampered), NOW + 1),
        Err(ApprovalError::InvalidConfirmation)
    );
    assert_eq!(
        evaluator.authorize(&request, &scopes, Some(&original), NOW + 60),
        Err(ApprovalError::ConfirmationExpired)
    );

    let future = authority.mint(
        "cnf_confirm0002".to_owned(),
        &request,
        true,
        NOW + 20,
        NOW + 40,
    )?;
    assert_eq!(
        evaluator.authorize(&request, &scopes, Some(&future), NOW + 10),
        Err(ApprovalError::ConfirmationExpired)
    );
    Ok(())
}

#[test]
fn signer_rejects_absent_confirmation_and_excessive_lifetime() -> TestResult {
    let request = request(EffectKind::SecurityModify, "0001")?;
    let authority = ConfirmationAuthority::new(SECRET)?;
    assert_eq!(
        authority.mint("cnf_confirm0001".to_owned(), &request, false, NOW, NOW + 60,),
        Err(ApprovalError::InvalidRequest)
    );
    assert_eq!(
        authority.mint("cnf_confirm0001".to_owned(), &request, true, NOW, NOW + 301,),
        Err(ApprovalError::InvalidRequest)
    );
    assert_eq!(
        authority.mint(
            "cnf_confirm0002".to_owned(),
            &request,
            true,
            NOW + 301,
            NOW + 302,
        ),
        Err(ApprovalError::InvalidRequest)
    );
    Ok(())
}

#[test]
fn replay_registry_is_bounded_and_prunes_expired_tokens() -> TestResult {
    let first = request(EffectKind::GitCommit, "0001")?;
    let second = request(EffectKind::GitCommit, "0002")?;
    let authority = ConfirmationAuthority::new(SECRET)?;
    let first_token = token(&authority, &first, "0001")?;
    let second_token = token(&authority, &second, "0002")?;
    let scopes = BTreeSet::from([ApprovalScope::WorkstationControl]);
    let mut evaluator = ApprovalEvaluator::new(policy(EffectKind::GitCommit, 1)?, SECRET)?;
    evaluator.authorize(&first, &scopes, Some(&first_token), NOW + 1)?;
    assert_eq!(
        evaluator.authorize(&second, &scopes, Some(&second_token), NOW + 2),
        Err(ApprovalError::CapacityExceeded)
    );

    let later = EffectRequest::new(
        "op_operation0003".to_owned(),
        digest('a'),
        digest('b'),
        EffectKind::GitCommit,
        digest('c'),
        digest('d'),
        NOW + 61,
    )?;
    let later_token = authority.mint(
        "cnf_confirm0003".to_owned(),
        &later,
        true,
        NOW + 61,
        NOW + 100,
    )?;
    evaluator.authorize(&later, &scopes, Some(&later_token), NOW + 62)?;
    Ok(())
}

#[test]
fn debug_output_and_error_codes_do_not_disclose_secrets() -> TestResult {
    let request = request(EffectKind::AutomationExecute, "0001")?;
    let authority = ConfirmationAuthority::new(SECRET)?;
    let token = token(&authority, &request, "0001")?;
    let evaluator = ApprovalEvaluator::new(policy(EffectKind::AutomationExecute, 8)?, SECRET)?;
    let debug = format!("{request:?} {authority:?} {token:?} {evaluator:?}");
    assert!(!debug.contains("op_operation0001"));
    assert!(!debug.contains(&digest('a')));
    assert!(!debug.contains(token.encoded()));
    assert!(!debug.contains("approval-policy-test-secret"));
    assert_eq!(
        ApprovalError::DeniedByPolicy.code(),
        "APPROVAL_DENIED_BY_POLICY"
    );
    Ok(())
}

#[test]
fn malformed_requests_policy_bounds_and_token_wrappers_are_rejected() {
    assert!(matches!(
        EffectRequest::new(
            "arbitrary shell command".to_owned(),
            digest('a'),
            digest('b'),
            EffectKind::GitCommit,
            digest('c'),
            digest('d'),
            NOW,
        ),
        Err(ApprovalError::InvalidRequest)
    ));
    assert!(ApprovalPolicy::new([], 0, 1).is_err());
    assert!(ApprovalPolicy::new([], 1, 0).is_err());
    assert!(ConfirmationAuthority::new(b"short").is_err());
    assert!(ConfirmationToken::parse("bad".to_owned()).is_err());
}
