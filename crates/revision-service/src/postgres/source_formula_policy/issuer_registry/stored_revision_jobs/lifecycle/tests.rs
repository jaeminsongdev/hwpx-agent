use super::*;
type TestResult=Result<(),Box<dyn std::error::Error>>;
fn input()->Result<StoredJobClaimInput,RevisionError>{
    Ok(StoredJobClaimInput{project:ProjectId::generate(),branch:BranchId::generate(),expected_head:RevisionHead::new(Some(RevisionId::generate()),1)?,
        key:Uuid::from_u128(31),job:Uuid::from_u128(32),request:Uuid::from_u128(33),source:ArtifactId::generate(),
        request_sha:ContentDigest::of(b"request"),manifest_sha:ContentDigest::of(b"manifest"),source_sha:ContentDigest::of(b"source"),
        effect_sha:ContentDigest::of(b"output"),precommit_sha:ContentDigest::of(b"precommit"),plan_sha:ContentDigest::of(b"plan"),
        target_profile:"server-fixture".into(),capability_sha:ContentDigest::of(b"capability"),max_attempts:3,base_delay_seconds:1,max_delay_seconds:60,ttl_seconds:600})
}
fn obs(outcome:StoredJobOutcome,state:StoredJobState,attempt:i32,retry:Option<i64>,revision:Option<RevisionId>,error:Option<&str>,receipt:Option<ArtifactId>)->Result<StoredJobObservation,RevisionError>{
    StoredJobObservation::observed(outcome,Uuid::from_u128(32),state,attempt,i64::from(attempt),retry,revision,error.map(str::to_owned),receipt)
}
#[test]fn valid_claim_is_bounded_and_retains_exact_server_bindings()->TestResult{
    let i=input()?;let c=StoredJobClaim::new(i.clone())?;let o=c.input();
    assert_eq!(o.project,i.project);assert_eq!(o.branch,i.branch);assert_eq!(o.expected_head,i.expected_head);assert_eq!(o.source,i.source);
    assert_eq!((o.key,o.job,o.request),(i.key,i.job,i.request));assert_eq!(o.request_sha,i.request_sha);assert_eq!(o.manifest_sha,i.manifest_sha);
    assert_eq!(o.source_sha,i.source_sha);assert_eq!(o.effect_sha,i.effect_sha);assert_eq!(o.precommit_sha,i.precommit_sha);assert_eq!(o.plan_sha,i.plan_sha);
    assert_eq!(o.capability_sha,i.capability_sha);assert_eq!(o.target_profile,i.target_profile);Ok(())
}
#[test]fn nil_ids_empty_head_and_generation_overflow_are_rejected()->TestResult{
    for mode in 0..5{let mut i=input()?;match mode{0=>i.key=Uuid::nil(),1=>i.job=Uuid::nil(),2=>i.request=Uuid::nil(),3=>i.expected_head=RevisionHead::empty(),
        _=>i.expected_head=RevisionHead::new(Some(RevisionId::generate()),u64::MAX)?};assert!(StoredJobClaim::new(i).is_err());}Ok(())
}
#[test]fn retry_ttl_and_target_profile_limits_match_sql23()->TestResult{
    for mode in 0..10{let mut i=input()?;match mode{0=>i.max_attempts=0,1=>i.max_attempts=11,2=>i.base_delay_seconds=0,3=>i.max_delay_seconds=0,
        4=>i.max_delay_seconds=86401,5=>i.ttl_seconds=59,6=>i.ttl_seconds=604801,7=>i.target_profile="a".into(),8=>i.target_profile="x".repeat(128),_=>i.target_profile="server profile".into()};assert!(StoredJobClaim::new(i).is_err());}
    let mut i=input()?;i.target_profile="x".repeat(127);i.max_attempts=10;i.base_delay_seconds=86400;i.max_delay_seconds=86400;i.ttl_seconds=604800;StoredJobClaim::new(i)?;Ok(())
}
#[test]fn every_zero_digest_and_unchanged_effect_are_rejected()->TestResult{
    let z=ContentDigest::parse(&"0".repeat(64))?;
    for field in 0..8{let mut i=input()?;match field{0=>i.request_sha=z,1=>i.manifest_sha=z,2=>i.source_sha=z,3=>i.effect_sha=z,4=>i.precommit_sha=z,5=>i.plan_sha=z,6=>i.capability_sha=z,_=>i.effect_sha=i.source_sha};assert!(StoredJobClaim::new(i).is_err());}Ok(())
}
#[test]fn all_replay_states_are_observations_not_implicit_execution_permits()->TestResult{
    use StoredJobState as S;use StoredJobOutcome as O;let rev=RevisionId::generate();let r=ArtifactId::generate();
    for(state,n,retry,revision,error,receipt)in[(S::Claimed,0,None,None,None,None),(S::InProgress,1,None,None,None,None),
        (S::RetryPending,2,Some(100),None,None,Some(r)),(S::OutcomeUnknown,2,None,None,Some("OUTCOME_UNKNOWN"),Some(r)),
        (S::TerminalSuccess,2,None,Some(rev),None,Some(r)),(S::TerminalFailure,3,None,None,Some("RETRY_EXHAUSTED"),Some(r))]{
        let o=obs(O::Replay,state,n,retry,revision,error,receipt)?;assert_eq!(o.outcome(),O::Replay);assert_eq!(o.state(),state);
        assert_eq!(o.retry_not_before_micros(),retry);assert_eq!(o.result_revision_id(),revision);assert_eq!(o.receipt_artifact_id(),receipt);assert_eq!(o.terminal_error_code(),error);
    }Ok(())
}
#[test]fn attempt_and_fence_must_match_dense_bounded_sql_sequence()->TestResult{
    use StoredJobState as S;use StoredJobOutcome as O;
    for(a,f)in[(-1,-1),(11,11),(1,0),(1,2),(0,1)]{assert!(StoredJobObservation::observed(O::Replay,Uuid::from_u128(32),S::InProgress,a,f,None,None,None,None).is_err());}
    assert!(StoredJobObservation::observed(O::New,Uuid::nil(),S::Claimed,0,0,None,None,None,None).is_err());Ok(())
}
#[test]fn new_and_live_transition_outcomes_require_exact_state_shapes()->TestResult{
    use StoredJobState as S;use StoredJobOutcome as O;
    for o in[O::Leased,O::Staged,O::Executing,O::Validating]{obs(o,S::InProgress,1,None,None,None,None)?;assert!(obs(o,S::Claimed,0,None,None,None,None).is_err());}
    obs(O::New,S::Claimed,0,None,None,None,None)?;assert!(obs(O::New,S::InProgress,1,None,None,None,None).is_err());
    assert!(obs(O::Replay,S::Claimed,1,None,None,None,None).is_err());assert!(obs(O::Replay,S::InProgress,1,None,None,None,Some(ArtifactId::generate())).is_err());Ok(())
}
#[test]fn terminal_success_unknown_and_retry_cannot_be_forged_by_partial_rows()->TestResult{
    use StoredJobState as S;use StoredJobOutcome as O;let rev=RevisionId::generate();let r=ArtifactId::generate();
    obs(O::Committed,S::TerminalSuccess,1,None,Some(rev),None,Some(r))?;
    for(revision,error,receipt)in[(None,None,Some(r)),(Some(rev),Some("ERROR"),Some(r)),(Some(rev),None,None)]{
        assert!(obs(O::Committed,S::TerminalSuccess,1,None,revision,error,receipt).is_err());}
    for(error,receipt)in[(None,Some(r)),(Some("OUTCOME_UNKNOWN"),None),(Some("RETRY_EXHAUSTED"),Some(r))]{assert!(obs(O::OutcomeUnknown,S::OutcomeUnknown,1,None,None,error,receipt).is_err());}
    assert!(obs(O::Replay,S::RetryPending,1,Some(0),None,None,Some(r)).is_err());assert!(obs(O::Replay,S::RetryPending,1,None,None,None,Some(r)).is_err());Ok(())
}
#[test]fn malformed_or_private_terminal_error_text_is_never_admitted()->TestResult{
    use StoredJobState as S;use StoredJobOutcome as O;
    for e in["bad","A","ERROR\nPRIVATE","ERROR value",&"A".repeat(65)]{assert!(obs(O::Replay,S::TerminalFailure,1,None,None,Some(e),Some(ArtifactId::generate())).is_err());}Ok(())
}
#[test]fn response_checks_reject_foreign_job_outcome_and_attempt()->TestResult{
    let r=obs(StoredJobOutcome::Staged,StoredJobState::InProgress,1,None,None,None,None)?;
    r.expect(Uuid::from_u128(32),StoredJobOutcome::Staged,Some(1))?;
    assert!(r.expect(Uuid::from_u128(99),StoredJobOutcome::Staged,Some(1)).is_err());
    assert!(r.expect(Uuid::from_u128(32),StoredJobOutcome::Executing,Some(1)).is_err());assert!(r.expect(Uuid::from_u128(32),StoredJobOutcome::Staged,Some(2)).is_err());Ok(())
}
#[test]fn transitions_are_closed_and_debug_redacts_server_identity()->TestResult{
    assert_eq!(StoredJobAdvance::Staged.states(),("leased","staged",StoredJobOutcome::Staged));
    assert_eq!(StoredJobAdvance::Executing.states(),("staged","executing",StoredJobOutcome::Executing));assert_eq!(StoredJobAdvance::Validating.states(),("executing","validating",StoredJobOutcome::Validating));
    let i=input()?;assert_eq!(format!("{i:?}"),"StoredJobClaimInput(<redacted>)");assert_eq!(format!("{:?}",StoredJobClaim::new(i)?),"StoredJobClaim(<redacted>)");
    let r=obs(StoredJobOutcome::New,StoredJobState::Claimed,0,None,None,None,None)?;assert!(!format!("{r:?}").contains(&r.job_id().to_string()));Ok(())
}
