"""One-shot expected-precommit/job/engine/storage coordinator9; no SQL/Native qualification."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_stored_job_lifecycle_components as predecessor
import run_stored_job_lifecycle_compile_recovery as recovery
core=predecessor.core
harness,shared,c,a,audit,tools,compact=core.harness,core.shared,core.c,core.a,core.audit,core.tools,core.compact
OUTPUT='implementation/p09/evidence/p09-361-stored-job-coordinator-components274.v1.json'
DRIVER='tools/p09/run_stored_job_coordinator_components.py'
BASE=recovery.OUTPUT
ADAPTER='crates/product-cli/src/stored_revision_commit.rs'
JOB=ADAPTER[:-3]+'/job.rs'
PARENT='crates/product-cli/tests/stored_revision_commit.rs'
TEST='crates/product-cli/tests/support/stored_job_coordinator.rs'
MANIFEST='crates/operation-engine/src/manifest.rs'
CHANGED={ADAPTER,PARENT,MANIFEST,predecessor.LIFE,predecessor.SQL}
NEW={DRIVER,JOB,TEST}
CHILD='#[path="support/stored_job_coordinator.rs"] mod job_v1;\n'
SCRATCH='target/p09-stored-job-coordinator-scratch-274'

def inventory(check):return predecessor.inventory(check)|NEW|CHANGED|{recovery.DRIVER,recovery.FAILED,recovery.checker.DRIVER,recovery.checker.FAILED}

def inverse(q,old):
    markers={ADAPTER:'pub mod job;\n',MANIFEST:'\n    #[must_use]\n    pub const fn target_profile_id(&self) -> &TargetProfileId { &self.target_profile_id }\n',
        predecessor.LIFE:'    /// Same admitted backend/context with the received capability, never a new authority issuer.\n    fn with_job_lease(&self,lease:StoredJobLease)->Self where Self:Sized;\n',
        predecessor.SQL:'    fn with_job_lease(&self,lease:StoredJobLease)->Self{self.with_received_lease(lease)}\n'}
    for path,marker in markers.items():
        text=q.text(path);c.require(text.count(marker)==1,'ONE_ADDITIVE_COORDINATOR_LINK');audit.inverse(text.replace(marker,''),old[path],'ALL_PREVIOUS_ENGINE_MANIFEST_SQL_LIFECYCLE_ADMISSION_STORAGE_AND_CAS_LOGIC_UNCHANGED')
    text=q.text(PARENT);c.require(text.endswith(CHILD)and text.count(CHILD)==1,'ONE_COORDINATOR_TEST_CHILD')
    audit.inverse(text[:-len(CHILD)],old[PARENT],'ALL38_PREVIOUS_STORED_COMMIT_TEST_BODIES_UNCHANGED')
    text=q.text(JOB)
    for marker in('self,artifacts:','self.binding.manifest.prepare_precommit','expected.expected_precommit_sha256','self.expected.matches_executed',
        'StoredJobRunStage::Replay;return report','id.attempt_no!=1','StoredJobAdvance::Validating','bind_registered','cas.compare_and_swap(request)',
        'report.registration_response=cas.registration_response().cloned()','complete_job','mark_job_unknown','report.transaction=Some(result)'):
        c.require(marker in text,'ONE_SHOT_EXPECTED_BINDING_REPLAY_STOP_ORIGINAL_VALIDATOR_REGISTERED_CAS_AND_RETAINED_UNKNOWN_EVIDENCE')
    c.require(text.count('tx.execute_bytes(')==1 and 'ValidationOutcome::Valid'not in text,'ONE_ORIGINAL_ENGINE_CALL_NO_FAKE_VALIDATOR_SUCCESS')
    for marker in('std::process','Command::','GRANT EXECUTE','std::fs::remove','no_effect','schedule_stored_revision_retry','Native011'):
        c.require(marker not in text,'NO_NATIVE_GRANTS_ARTIFACT_DELETION_OR_AUTOMATIC_RETRY')

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'COORDINATOR_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_STORED_JOB_COORDINATOR_COMPONENTS',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_PostgreSQL_or_process_restart=False,SQL23_applied=False,SQL23_catalog_privilege_or_runtime_qualified=False,
        P09_product_execution_or_commit=False,durable_idempotency_complete=False,in_memory_repository_and_synthetic_manifest_validator=True,
        one_shot_storage_coordinator_not_product_route_authorization=True,scratch_parent=SCRATCH)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        scratch=c.ROOT/SCRATCH;parent=c.ROOT/'target';c.require(parent.is_dir()and not parent.is_symlink()and not parent.is_junction()
            and not scratch.exists()and scratch.resolve().is_relative_to(parent.resolve()),'EARLY_UNIQUE274_OWNED_TEMP_PARENT_ONLY')
        previous=compact.unpack(q.json(BASE))
        c.require(q.snapshots[BASE]['sha256']=='78ffabd31f729f59016278be6acb8a2800d141860f0e0404ccb5cb38a287f23f'
            and previous['cleanup']and previous['total_executed_cases']==15 and previous['fresh_inputs']==previous['final_fresh_hashes']==914,'EXACT273_LIFECYCLE15_TERMINAL_CLOSURE')
        old={p['path']:p for p in previous['source_pins']}
        for name in sorted(NEW|CHANGED):q.pin(name)
        inverse(q,old)
        for name in sorted(inventory(guard.check)):
            q.pin(name)
            if name not in NEW|CHANGED:c.require(q.snapshots[name]==old[name],'ALL_OTHER_MIGRATIONS_SERVICES_ROUTES_NATIVE_AND_PRIOR_TESTS_UNCHANGED')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        cases={'job_v1::'+n for n in predecessor.predecessor.names(q,TEST)};c.require(len(cases)==9,'EXACT_COORDINATOR9')
        scratch.mkdir();environment=audit.environment();environment.update(TEMP=str(scratch),TMP=str(scratch))
        snapshot=core.prior.base.base.base.base.base.base.prior.base.base.prior.base.base.base.prior.prior.base.prior.base.prior.base.base.snapshot
        print(json.dumps(dict(state='COORDINATOR_PREFLIGHT',inputs=len(q.snapshots),new_cases9=True,prior_models15_reused=True,actual_DB=False)),flush=True)
        harness.run_one('one_shot_coordinator9',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','stored_revision_commit',
            '--message-format=short','--','job_v1::','--test-threads=1'],cases,guard,environment,row,observe_capture=snapshot)
        tools.good_step(row['steps'][-1],cases)
        c.require(not any(scratch.iterdir()),'COORDINATOR_OWNED_TEST_SCRATCH_EMPTY')
        q.finish();guard.check(force=True)
        row.update(state='PASS_ONE_SHOT_STORED_JOB_COORDINATOR9_REUSED_LIFECYCLE15_NOT_SQL_RUNTIME_P09_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            total_executed_cases=9,new_cases=9,unchanged_lifecycle_cases_reused=15,all_prior_test_bodies_unmodified=True,test_scratch_empty=True,
            next_work='owned_SQL23_catalog_privilege_runtime_worker_and_restart_campaign_then_qualified_product_dispatch')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'COORDINATOR_COMPONENT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_COORDINATOR_RESOURCE_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','test_scratch_empty','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','bounded_output_observation')},'pass_count':sum(v=='ok'for _,v in s.get('tests',[])),
                'failures':[n for n,v in s.get('tests',[])if v!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
