"""Retain274 zero-Cargo checker failure; correct prepare receiver spelling, no product changes."""
import run_stored_job_coordinator_components as origin
OUTPUT='implementation/p09/evidence/p09-361-stored-job-coordinator-checker-recovery275.v1.json'
DRIVER='tools/p09/run_stored_job_coordinator_checker_recovery.py'
FAILED=origin.OUTPUT
SCRATCH='target/p09-stored-job-coordinator-scratch-275'
def inverse(q,old):
    markers={origin.ADAPTER:'pub mod job;\n',origin.MANIFEST:'\n    #[must_use]\n    pub const fn target_profile_id(&self) -> &TargetProfileId { &self.target_profile_id }\n',
        origin.predecessor.LIFE:'    /// Same admitted backend/context with the received capability, never a new authority issuer.\n    fn with_job_lease(&self,lease:StoredJobLease)->Self where Self:Sized;\n',
        origin.predecessor.SQL:'    fn with_job_lease(&self,lease:StoredJobLease)->Self{self.with_received_lease(lease)}\n'}
    for path,marker in markers.items():
        text=q.text(path);origin.c.require(text.count(marker)==1,'ONE_ADDITIVE_COORDINATOR_LINK');origin.audit.inverse(text.replace(marker,''),old[path],'ALL_PREVIOUS_ENGINE_MANIFEST_SQL_LIFECYCLE_ADMISSION_STORAGE_AND_CAS_LOGIC_UNCHANGED')
    text=q.text(origin.PARENT);origin.c.require(text.endswith(origin.CHILD)and text.count(origin.CHILD)==1,'ONE_COORDINATOR_TEST_CHILD')
    origin.audit.inverse(text[:-len(origin.CHILD)],old[origin.PARENT],'ALL38_PREVIOUS_STORED_COMMIT_TEST_BODIES_UNCHANGED')
    text=q.text(origin.JOB)
    for marker in('self,artifacts:','binding.manifest.prepare_precommit','expected.expected_precommit_sha256','self.expected.matches_executed',
        'StoredJobRunStage::Replay;return report','id.attempt_no!=1','StoredJobAdvance::Validating','bind_registered','cas.compare_and_swap(request)',
        'report.registration_response=cas.registration_response().cloned()','complete_job','mark_job_unknown','report.transaction=Some(result)'):
        origin.c.require(marker in text,'ONE_SHOT_EXPECTED_BINDING_REPLAY_STOP_ORIGINAL_VALIDATOR_REGISTERED_CAS_AND_RETAINED_UNKNOWN_EVIDENCE')
    origin.c.require(text.count('tx.execute_bytes(')==1 and 'ValidationOutcome::Valid'not in text,'ONE_ORIGINAL_ENGINE_CALL_NO_FAKE_VALIDATOR_SUCCESS')
    for marker in('std::process','Command::','GRANT EXECUTE','std::fs::remove','no_effect','schedule_stored_revision_retry','Native011'):
        origin.c.require(marker not in text,'NO_NATIVE_GRANTS_ARTIFACT_DELETION_OR_AUTOMATIC_RETRY')
    failed=origin.compact.unpack(q.json(FAILED))
    origin.c.require(q.snapshots[FAILED]['sha256']=='8b78c7873a5d2a1b4ff570a9cda3c44f4f6d781e1d7585ea908027d95e0bae23'
        and failed['cleanup']and failed['steps']==[],'EXACT274_CHECKER_FAILURE_ZERO_CARGO_RETAINED')
    for pin in failed['source_pins']:
        if pin['path']in origin.CHANGED|{origin.JOB,origin.TEST,origin.DRIVER}:
            q.pin(pin['path']);origin.c.require(q.snapshots[pin['path']]==pin,'ALL_COORDINATOR_PRODUCT_AND_TEST_INPUTS_UNCHANGED_SINCE274')
if __name__=='__main__':
    origin.OUTPUT=OUTPUT;origin.SCRATCH=SCRATCH;origin.NEW|={DRIVER,FAILED};origin.inverse=inverse
    raise SystemExit(origin.main())
