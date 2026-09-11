use base64::{Engine as _, engine::general_purpose::URL_SAFE_NO_PAD};
use remote_credential_lifecycle::{
    CredentialState, IssuerKey, LifecycleError, LifecycleOperation, LifecyclePolicy,
    PendingTransition, apply_definitive_rejection, begin_transition, verify_access_token,
    verify_revocation,
};
use ring::{
    rand::SystemRandom,
    signature::{Ed25519KeyPair, KeyPair as _},
};
use serde::Serialize;
use serde_json::json;
use sha2::Digest as _;

const NOW: u64 = 1_800_000_000;
const ISSUER: &str = "https://issuer.example";
const SUBJECT: &str = "service-account-0001";
const AUDIENCE: &str = "hwpx-agent-remote-sync";
const KEY_ID: &str = "issuer-key-0001";

fn must_ok<T, E: core::fmt::Debug>(result: Result<T, E>) -> T {
    match result {
        Ok(value) => value,
        Err(error) => panic!("unexpected error: {error:?}"),
    }
}

fn signing_key() -> Ed25519KeyPair {
    let random = SystemRandom::new();
    let document = must_ok(Ed25519KeyPair::generate_pkcs8(&random));
    must_ok(Ed25519KeyPair::from_pkcs8(document.as_ref()))
}

fn issuer_key(pair: &Ed25519KeyPair, key_id: &str) -> IssuerKey {
    let raw = pair.public_key().as_ref();
    assert_eq!(raw.len(), 32);
    let mut public_key = [0_u8; 32];
    public_key.copy_from_slice(raw);
    must_ok(IssuerKey::new(key_id.to_owned(), public_key))
}

fn policy(pair: &Ed25519KeyPair) -> LifecyclePolicy {
    must_ok(LifecyclePolicy::new(
        ISSUER.to_owned(),
        SUBJECT.to_owned(),
        AUDIENCE.to_owned(),
        vec![issuer_key(pair, KEY_ID)],
        300,
        900,
        120,
        30,
        120,
    ))
}

#[derive(Serialize)]
struct Header<'a> {
    alg: &'a str,
    typ: &'a str,
    kid: &'a str,
}

#[derive(Clone, Serialize)]
struct AccessClaims {
    iss: String,
    sub: String,
    aud: String,
    scope: String,
    iat: u64,
    nbf: u64,
    exp: u64,
    jti: String,
    operation_id: String,
    request_sha256: String,
    generation: u64,
    key_generation: u64,
}

#[derive(Clone, Serialize)]
struct RevocationClaims {
    iss: String,
    sub: String,
    aud: String,
    iat: u64,
    jti: String,
    operation_id: String,
    request_sha256: String,
    generation: u64,
    key_generation: u64,
    credential_sha256: String,
    revoked: bool,
}

fn signed_jwt(
    pair: &Ed25519KeyPair,
    token_type: &str,
    key_id: &str,
    claims: &impl Serialize,
) -> String {
    let header = must_ok(serde_json::to_vec(&Header {
        alg: "EdDSA",
        typ: token_type,
        kid: key_id,
    }));
    let payload = must_ok(serde_json::to_vec(claims));
    let header = URL_SAFE_NO_PAD.encode(header);
    let payload = URL_SAFE_NO_PAD.encode(payload);
    let signing_input = format!("{header}.{payload}");
    let signature = pair.sign(signing_input.as_bytes());
    format!(
        "{signing_input}.{}",
        URL_SAFE_NO_PAD.encode(signature.as_ref())
    )
}

#[allow(clippy::too_many_arguments)]
fn access_claims(
    pending: &PendingTransition,
    operation_id: &str,
    generation: u64,
    key_generation: u64,
    issued_at: u64,
    not_before: u64,
    expires_at: u64,
    jti: &str,
) -> AccessClaims {
    AccessClaims {
        iss: ISSUER.to_owned(),
        sub: SUBJECT.to_owned(),
        aud: AUDIENCE.to_owned(),
        scope: "mirror.sync".to_owned(),
        iat: issued_at,
        nbf: not_before,
        exp: expires_at,
        jti: jti.to_owned(),
        operation_id: operation_id.to_owned(),
        request_sha256: pending.request_sha256().to_owned(),
        generation,
        key_generation,
    }
}

fn issue(policy: &LifecyclePolicy, pair: &Ed25519KeyPair, now: u64) -> (CredentialState, String) {
    let operation_id = "operation-issue-0001";
    let pending = must_ok(begin_transition(
        policy,
        &CredentialState::Absent,
        LifecycleOperation::Issue,
        operation_id.to_owned(),
        now,
    ));
    let claims = access_claims(
        &pending,
        operation_id,
        1,
        1,
        now,
        now,
        now + 600,
        "credential-jti-0001",
    );
    let token = signed_jwt(pair, "hwpx-agent-service+jwt", KEY_ID, &claims);
    let verified = must_ok(verify_access_token(policy, &pending, token.clone(), now));
    (
        CredentialState::Active {
            credential: verified.metadata().clone(),
        },
        token,
    )
}

fn tamper_signature(token: &str) -> String {
    let mut segments = token.split('.');
    let header = segments.next().unwrap_or_default();
    let payload = segments.next().unwrap_or_default();
    let signature = segments.next().unwrap_or_default();
    assert!(segments.next().is_none());
    let mut raw = must_ok(URL_SAFE_NO_PAD.decode(signature));
    raw[0] ^= 1;
    format!("{header}.{payload}.{}", URL_SAFE_NO_PAD.encode(raw))
}

#[test]
fn issue_is_signed_bound_canonical_and_retry_stable() {
    let pair = signing_key();
    let policy = policy(&pair);
    let operation_id = "operation-issue-0001";
    let pending = must_ok(begin_transition(
        &policy,
        &CredentialState::Absent,
        LifecycleOperation::Issue,
        operation_id.to_owned(),
        NOW,
    ));
    let first = must_ok(pending.retry_request(&policy, NOW));
    let retry = must_ok(pending.retry_request(&policy, NOW + 119));
    assert_eq!(first, retry);
    assert_eq!(
        hex::encode(sha2::Sha256::digest(&first)),
        pending.request_sha256()
    );

    let encoded = must_ok(pending.to_canonical_json(&policy));
    let restored = must_ok(PendingTransition::from_canonical_json(&policy, &encoded));
    assert_eq!(restored, pending);
    assert_eq!(must_ok(restored.retry_request(&policy, NOW + 1)), first);

    let claims = access_claims(
        &pending,
        operation_id,
        1,
        1,
        NOW,
        NOW,
        NOW + 600,
        "credential-jti-0001",
    );
    let token = signed_jwt(&pair, "hwpx-agent-service+jwt", KEY_ID, &claims);
    let verified = must_ok(verify_access_token(&policy, &pending, token.clone(), NOW));
    assert_eq!(verified.metadata().generation(), 1);
    assert_eq!(verified.metadata().key_generation(), 1);
    assert_eq!(verified.metadata().refresh_at(), NOW + 480);
    assert_eq!(verified.metadata().expires_at(), NOW + 600);
    verified.with_secret(|secret| assert_eq!(secret, token));
}

#[test]
fn refresh_is_due_only_and_advances_token_not_key_generation() {
    let pair = signing_key();
    let policy = policy(&pair);
    let (active, prior_token) = issue(&policy, &pair, NOW);
    assert_eq!(
        begin_transition(
            &policy,
            &active,
            LifecycleOperation::Refresh,
            "operation-issue-0001".to_owned(),
            NOW + 480,
        )
        .err(),
        Some(LifecycleError::InvalidOperation)
    );
    assert_eq!(
        begin_transition(
            &policy,
            &active,
            LifecycleOperation::Refresh,
            "operation-refresh-0001".to_owned(),
            NOW + 479,
        )
        .err(),
        Some(LifecycleError::NotDue)
    );
    let pending = must_ok(begin_transition(
        &policy,
        &active,
        LifecycleOperation::Refresh,
        "operation-refresh-0001".to_owned(),
        NOW + 480,
    ));
    let claims = access_claims(
        &pending,
        "operation-refresh-0001",
        2,
        1,
        NOW + 480,
        NOW + 480,
        NOW + 1_080,
        "credential-jti-0002",
    );
    let token = signed_jwt(&pair, "hwpx-agent-service+jwt", KEY_ID, &claims);
    let reused_identifier = AccessClaims {
        jti: "credential-jti-0001".to_owned(),
        ..claims.clone()
    };
    assert_eq!(
        verify_access_token(
            &policy,
            &pending,
            signed_jwt(&pair, "hwpx-agent-service+jwt", KEY_ID, &reused_identifier,),
            NOW + 480,
        )
        .err(),
        Some(LifecycleError::InvalidResponse)
    );
    let verified = must_ok(verify_access_token(
        &policy,
        &pending,
        token.clone(),
        NOW + 480,
    ));
    assert_ne!(token, prior_token);
    assert_eq!(verified.metadata().generation(), 2);
    assert_eq!(verified.metadata().key_generation(), 1);

    assert_eq!(
        verify_access_token(&policy, &pending, prior_token, NOW + 480).err(),
        Some(LifecycleError::InvalidResponse)
    );
}

#[test]
fn rotation_advances_both_generations_and_rejects_wrong_generation() {
    let pair = signing_key();
    let policy = policy(&pair);
    let (active, _) = issue(&policy, &pair, NOW);
    let pending = must_ok(begin_transition(
        &policy,
        &active,
        LifecycleOperation::Rotate,
        "operation-rotate-0001".to_owned(),
        NOW + 100,
    ));
    let mut wrong = access_claims(
        &pending,
        "operation-rotate-0001",
        2,
        2,
        NOW + 100,
        NOW + 100,
        NOW + 700,
        "credential-jti-0003",
    );
    wrong.key_generation = 1;
    assert_eq!(
        verify_access_token(
            &policy,
            &pending,
            signed_jwt(&pair, "hwpx-agent-service+jwt", KEY_ID, &wrong),
            NOW + 100,
        )
        .err(),
        Some(LifecycleError::InvalidResponse)
    );
    let claims = AccessClaims {
        key_generation: 2,
        ..wrong
    };
    let verified = must_ok(verify_access_token(
        &policy,
        &pending,
        signed_jwt(&pair, "hwpx-agent-service+jwt", KEY_ID, &claims),
        NOW + 100,
    ));
    assert_eq!(verified.metadata().generation(), 2);
    assert_eq!(verified.metadata().key_generation(), 2);
}

#[test]
fn signed_revocation_is_distinct_and_terminal() {
    let pair = signing_key();
    let policy = policy(&pair);
    let (active, _) = issue(&policy, &pair, NOW);
    let prior = active
        .active()
        .map_or("", |value| value.credential_sha256());
    let pending = must_ok(begin_transition(
        &policy,
        &active,
        LifecycleOperation::Revoke,
        "operation-revoke-0001".to_owned(),
        NOW + 200,
    ));
    let claims = RevocationClaims {
        iss: ISSUER.to_owned(),
        sub: SUBJECT.to_owned(),
        aud: AUDIENCE.to_owned(),
        iat: NOW + 200,
        jti: "revocation-jti-0001".to_owned(),
        operation_id: "operation-revoke-0001".to_owned(),
        request_sha256: pending.request_sha256().to_owned(),
        generation: 1,
        key_generation: 1,
        credential_sha256: prior.to_owned(),
        revoked: true,
    };
    let reused_identifier = RevocationClaims {
        jti: "credential-jti-0001".to_owned(),
        ..claims.clone()
    };
    assert_eq!(
        verify_revocation(
            &policy,
            &pending,
            &signed_jwt(
                &pair,
                "hwpx-agent-revocation+jwt",
                KEY_ID,
                &reused_identifier,
            ),
            NOW + 200,
        )
        .err(),
        Some(LifecycleError::InvalidResponse)
    );
    let stale_issuance = RevocationClaims {
        iat: NOW + 169,
        ..claims.clone()
    };
    assert_eq!(
        verify_revocation(
            &policy,
            &pending,
            &signed_jwt(&pair, "hwpx-agent-revocation+jwt", KEY_ID, &stale_issuance,),
            NOW + 200,
        )
        .err(),
        Some(LifecycleError::InvalidResponse)
    );
    let receipt = signed_jwt(&pair, "hwpx-agent-revocation+jwt", KEY_ID, &claims);
    assert_eq!(
        verify_access_token(&policy, &pending, receipt.clone(), NOW + 200).err(),
        Some(LifecycleError::InvalidOperation)
    );
    let revoked = must_ok(verify_revocation(&policy, &pending, &receipt, NOW + 200));
    let terminal = CredentialState::Revoked {
        credential: revoked,
    };
    for operation in [
        LifecycleOperation::Issue,
        LifecycleOperation::Refresh,
        LifecycleOperation::Rotate,
        LifecycleOperation::Revoke,
    ] {
        assert_eq!(
            begin_transition(
                &policy,
                &terminal,
                operation,
                "operation-after-revoke".to_owned(),
                NOW + 201,
            )
            .err(),
            Some(LifecycleError::InvalidOperation)
        );
    }
}

#[test]
fn wrong_signature_key_algorithm_type_and_malformed_jws_fail_closed() {
    let pair = signing_key();
    let other = signing_key();
    let policy = policy(&pair);
    let pending = must_ok(begin_transition(
        &policy,
        &CredentialState::Absent,
        LifecycleOperation::Issue,
        "operation-issue-0001".to_owned(),
        NOW,
    ));
    let claims = access_claims(
        &pending,
        "operation-issue-0001",
        1,
        1,
        NOW,
        NOW,
        NOW + 600,
        "credential-jti-0001",
    );
    let valid = signed_jwt(&pair, "hwpx-agent-service+jwt", KEY_ID, &claims);
    for token in [
        tamper_signature(&valid),
        signed_jwt(&other, "hwpx-agent-service+jwt", KEY_ID, &claims),
        signed_jwt(&pair, "hwpx-agent-revocation+jwt", KEY_ID, &claims),
        signed_jwt(&pair, "hwpx-agent-service+jwt", "unknown-key-0001", &claims),
        "a.b.c".to_owned(),
        "a.b.c.d".to_owned(),
        format!("{valid}="),
    ] {
        assert!(matches!(
            verify_access_token(&policy, &pending, token, NOW),
            Err(LifecycleError::InvalidResponse | LifecycleError::SignatureRejected)
        ));
    }
}

#[test]
fn issuer_subject_audience_scope_request_and_operation_are_exact() {
    let pair = signing_key();
    let policy = policy(&pair);
    let pending = must_ok(begin_transition(
        &policy,
        &CredentialState::Absent,
        LifecycleOperation::Issue,
        "operation-issue-0001".to_owned(),
        NOW,
    ));
    let base = access_claims(
        &pending,
        "operation-issue-0001",
        1,
        1,
        NOW,
        NOW,
        NOW + 600,
        "credential-jti-0001",
    );
    let mut variants = Vec::new();
    let mut changed = base.clone();
    changed.iss = "https://other.example".to_owned();
    variants.push(changed);
    let mut changed = base.clone();
    changed.sub = "other-subject-0001".to_owned();
    variants.push(changed);
    let mut changed = base.clone();
    changed.aud = "other-audience-0001".to_owned();
    variants.push(changed);
    let mut changed = base.clone();
    changed.scope = "mirror.read".to_owned();
    variants.push(changed);
    let mut changed = base.clone();
    changed.request_sha256 = "0".repeat(64);
    variants.push(changed);
    let mut changed = base;
    changed.operation_id = "operation-other-0001".to_owned();
    variants.push(changed);
    for claims in variants {
        let token = signed_jwt(&pair, "hwpx-agent-service+jwt", KEY_ID, &claims);
        assert_eq!(
            verify_access_token(&policy, &pending, token, NOW).err(),
            Some(LifecycleError::InvalidResponse)
        );
    }
}

#[test]
fn lifetime_clock_and_pending_deadline_boundaries_fail_closed() {
    let pair = signing_key();
    let policy = policy(&pair);
    let pending = must_ok(begin_transition(
        &policy,
        &CredentialState::Absent,
        LifecycleOperation::Issue,
        "operation-issue-0001".to_owned(),
        NOW,
    ));
    let cases = [
        (NOW, NOW, NOW + 299),
        (NOW, NOW, NOW + 901),
        (NOW + 31, NOW + 31, NOW + 631),
        (NOW - 31, NOW - 31, NOW + 569),
        (NOW, NOW + 31, NOW + 600),
        (NOW, NOW, NOW),
    ];
    for (iat, nbf, exp) in cases {
        let claims = access_claims(
            &pending,
            "operation-issue-0001",
            1,
            1,
            iat,
            nbf,
            exp,
            "credential-jti-0001",
        );
        assert_eq!(
            verify_access_token(
                &policy,
                &pending,
                signed_jwt(&pair, "hwpx-agent-service+jwt", KEY_ID, &claims),
                NOW,
            )
            .err(),
            Some(LifecycleError::InvalidResponse)
        );
    }
    assert_eq!(
        pending.retry_request(&policy, NOW + 121).err(),
        Some(LifecycleError::PendingExpired)
    );
}

#[test]
fn definitive_rejection_restores_exact_state_but_unknown_outcome_stays_pending() {
    let pair = signing_key();
    let policy = policy(&pair);
    let (active, _) = issue(&policy, &pair, NOW);
    let pending = must_ok(begin_transition(
        &policy,
        &active,
        LifecycleOperation::Rotate,
        "operation-rotate-0001".to_owned(),
        NOW + 10,
    ));
    let retry = must_ok(pending.retry_request(&policy, NOW + 20));
    assert_eq!(retry, must_ok(pending.retry_request(&policy, NOW + 30)));
    let restored = must_ok(apply_definitive_rejection(
        &policy,
        pending.clone(),
        NOW + 30,
    ));
    assert_eq!(restored, active);
    assert_eq!(
        apply_definitive_rejection(&policy, pending, NOW + 131).err(),
        Some(LifecycleError::PendingExpired)
    );
}

#[test]
fn pending_json_rejects_unknown_duplicate_noncanonical_drift_and_oversize() {
    let pair = signing_key();
    let policy = policy(&pair);
    let pending = must_ok(begin_transition(
        &policy,
        &CredentialState::Absent,
        LifecycleOperation::Issue,
        "operation-issue-0001".to_owned(),
        NOW,
    ));
    let encoded = must_ok(pending.to_canonical_json(&policy));
    let text = String::from_utf8_lossy(&encoded);
    let unknown = text.replacen('{', "{\"unknown\":true,", 1);
    let duplicate = text.replacen(
        '{',
        "{\"schema_version\":\"hwpx-agent.remote-credential-pending/v1\",",
        1,
    );
    let mut drifted: serde_json::Value = must_ok(serde_json::from_slice(&encoded));
    drifted["request_sha256"] = json!("0".repeat(64));
    let drifted = must_ok(serde_json::to_vec(&drifted));
    for invalid in [
        unknown.into_bytes(),
        duplicate.into_bytes(),
        [b" ".as_slice(), encoded.as_slice()].concat(),
        drifted,
        vec![b'x'; 16_385],
    ] {
        assert!(PendingTransition::from_canonical_json(&policy, &invalid).is_err());
    }
}

#[test]
fn policy_and_operation_boundaries_are_exact() {
    let pair = signing_key();
    let raw = pair.public_key().as_ref();
    let mut public_key = [0_u8; 32];
    public_key.copy_from_slice(raw);
    let key = must_ok(IssuerKey::new(KEY_ID.to_owned(), public_key));
    let invalid_policies = [
        LifecyclePolicy::new(
            "http://issuer.example".to_owned(),
            SUBJECT.to_owned(),
            AUDIENCE.to_owned(),
            vec![key.clone()],
            300,
            900,
            120,
            30,
            120,
        ),
        LifecyclePolicy::new(
            ISSUER.to_owned(),
            SUBJECT.to_owned(),
            AUDIENCE.to_owned(),
            vec![],
            300,
            900,
            120,
            30,
            120,
        ),
        LifecyclePolicy::new(
            ISSUER.to_owned(),
            SUBJECT.to_owned(),
            AUDIENCE.to_owned(),
            vec![key.clone(), key],
            300,
            900,
            120,
            30,
            120,
        ),
    ];
    assert!(invalid_policies.into_iter().all(|result| result.is_err()));

    let policy = policy(&pair);
    for operation in [
        LifecycleOperation::Refresh,
        LifecycleOperation::Rotate,
        LifecycleOperation::Revoke,
    ] {
        assert_eq!(
            begin_transition(
                &policy,
                &CredentialState::Absent,
                operation,
                "operation-invalid-0001".to_owned(),
                NOW,
            )
            .err(),
            Some(LifecycleError::InvalidOperation)
        );
    }
    assert_eq!(
        begin_transition(
            &policy,
            &CredentialState::Absent,
            LifecycleOperation::Issue,
            "short".to_owned(),
            NOW,
        )
        .err(),
        Some(LifecycleError::InvalidOperation)
    );
}

#[test]
fn arithmetic_overflow_is_rejected() {
    let pair = signing_key();
    let policy = policy(&pair);
    assert_eq!(
        begin_transition(
            &policy,
            &CredentialState::Absent,
            LifecycleOperation::Issue,
            "operation-time-overflow".to_owned(),
            u64::MAX,
        )
        .err(),
        Some(LifecycleError::Overflow)
    );

    let (active, _) = issue(&policy, &pair, NOW);
    let mut serialized = must_ok(serde_json::to_value(&active));
    serialized["credential"]["generation"] = json!(u64::MAX);
    let overflow_state: CredentialState = must_ok(serde_json::from_value(serialized));
    assert_eq!(
        begin_transition(
            &policy,
            &overflow_state,
            LifecycleOperation::Refresh,
            "operation-generation-overflow".to_owned(),
            NOW + 480,
        )
        .err(),
        Some(LifecycleError::Overflow)
    );
}

#[test]
fn pending_binds_all_keys_and_lifetime_policy() {
    let pair = signing_key();
    let pending = must_ok(begin_transition(
        &policy(&pair),
        &CredentialState::Absent,
        LifecycleOperation::Issue,
        "operation-policy-binding".to_owned(),
        NOW,
    ));
    let replacement = signing_key();
    let key_drift = must_ok(LifecyclePolicy::new(
        ISSUER.to_owned(),
        SUBJECT.to_owned(),
        AUDIENCE.to_owned(),
        vec![issuer_key(&replacement, KEY_ID)],
        300,
        900,
        120,
        30,
        120,
    ));
    let lifetime_drift = must_ok(LifecyclePolicy::new(
        ISSUER.to_owned(),
        SUBJECT.to_owned(),
        AUDIENCE.to_owned(),
        vec![issuer_key(&pair, KEY_ID)],
        300,
        901,
        120,
        30,
        120,
    ));
    for drifted in [&key_drift, &lifetime_drift] {
        assert_eq!(
            pending.retry_request(drifted, NOW).err(),
            Some(LifecycleError::InvalidState)
        );
        assert_eq!(
            pending.to_canonical_json(drifted).err(),
            Some(LifecycleError::InvalidState)
        );
    }
}

#[test]
fn persisted_active_state_must_match_complete_policy() {
    let pair = signing_key();
    let policy = policy(&pair);
    let (active, _) = issue(&policy, &pair, NOW);
    let base = must_ok(serde_json::to_value(&active));
    for (field, value) in [
        ("refresh_at", json!(NOW + 481)),
        ("not_before", json!(NOW + 31)),
        ("issuer_key_id_sha256", json!("0".repeat(64))),
        ("key_generation", json!(2)),
    ] {
        let mut tampered = base.clone();
        tampered["credential"][field] = value;
        let state: CredentialState = must_ok(serde_json::from_value(tampered));
        assert_eq!(
            begin_transition(
                &policy,
                &state,
                LifecycleOperation::Refresh,
                "operation-state-policy-drift".to_owned(),
                NOW + 480,
            )
            .err(),
            Some(LifecycleError::InvalidState)
        );
    }
}

#[test]
fn debug_state_request_and_metadata_never_disclose_secrets_or_identities() {
    let pair = signing_key();
    let policy = policy(&pair);
    let pending = must_ok(begin_transition(
        &policy,
        &CredentialState::Absent,
        LifecycleOperation::Issue,
        "operation-secret-0001".to_owned(),
        NOW,
    ));
    let claims = access_claims(
        &pending,
        "operation-secret-0001",
        1,
        1,
        NOW,
        NOW,
        NOW + 600,
        "credential-secret-0001",
    );
    let token = signed_jwt(&pair, "hwpx-agent-service+jwt", KEY_ID, &claims);
    let verified = must_ok(verify_access_token(&policy, &pending, token.clone(), NOW));
    let surfaces = format!("{policy:?}\n{pending:?}\n{verified:?}");
    for forbidden in [
        ISSUER,
        SUBJECT,
        AUDIENCE,
        KEY_ID,
        "operation-secret-0001",
        "credential-secret-0001",
        token.as_str(),
    ] {
        assert!(!surfaces.contains(forbidden));
    }
    let pending_json = must_ok(pending.to_canonical_json(&policy));
    assert!(
        !pending_json
            .windows(token.len())
            .any(|window| window == token.as_bytes())
    );
    let metadata_json = must_ok(serde_json::to_vec(verified.metadata()));
    assert!(
        !metadata_json
            .windows(token.len())
            .any(|window| window == token.as_bytes())
    );
}

#[test]
fn expired_active_state_refuses_refresh_and_rotation_but_allows_revocation() {
    let pair = signing_key();
    let policy = policy(&pair);
    let (active, _) = issue(&policy, &pair, NOW);
    for operation in [LifecycleOperation::Refresh, LifecycleOperation::Rotate] {
        assert_eq!(
            begin_transition(
                &policy,
                &active,
                operation,
                "operation-expired-0001".to_owned(),
                NOW + 600,
            )
            .err(),
            Some(LifecycleError::Expired)
        );
    }
    assert!(
        begin_transition(
            &policy,
            &active,
            LifecycleOperation::Revoke,
            "operation-revoke-expired".to_owned(),
            NOW + 600,
        )
        .is_ok()
    );
}
