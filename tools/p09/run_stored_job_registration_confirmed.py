"""Separate rejected response diagnostics from confirmed registration, execute only affected9."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_stored_job_registration_fresh_temp as predecessor
base=predecessor.base
harness,shared,c,a,audit,tools,compact=base.harness,base.shared,base.c,base.a,base.audit,base.tools,base.compact
OUTPUT='implementation/p09/evidence/p09-361-stored-job-registration-confirmed268.v1.json'
DRIVER='tools/p09/run_stored_job_registration_confirmed.py'
SCRATCH='target/p09-stored-job-registration-scratch-268'
CHANGED={base.ADAPTER,base.CHILD,base.TEST}


def inventory(check):return base.inventory(check)|{predecessor.DRIVER,predecessor.origin.DRIVER,DRIVER}


def inverse(q,old):
    text=q.text(base.ADAPTER)
    markers=['    registration_response: Option<StoredCommitIntentRecord>,\n',
        '            .field("registration_response_received", &self.registration_response.is_some())\n',
        '            registration_response: None,\n',
        '    /// Diagnostic response, including a rejected foreign row. Not a confirmed registration.\n    #[must_use]\n    pub const fn registration_response(&self) -> Option<&StoredCommitIntentRecord> { self.registration_response.as_ref() }\n']
    for marker in markers:c.require(text.count(marker)==1,'EXACT_ADDITIVE_RAW_RESPONSE_DIAGNOSTICS');text=text.replace(marker,'')
    audit.inverse(text,old[base.ADAPTER],'ALL_BIND_SOURCE_STORAGE_SCOPE_CAS_AND_RECOVERY_LOGIC_UNCHANGED')
    text=q.text(base.CHILD)
    before='        self.registered_job_intent=Some(record);\n        if !valid{return Err(StoredCommitError::Binding);}Ok(())\n'
    after='        self.registration_response=Some(record.clone());\n        if !valid{return Err(StoredCommitError::Binding);}\n        self.registered_job_intent=Some(record);Ok(())\n'
    c.require(text.count(after)==1,'CONFIRMED_RECORD_SET_ONLY_AFTER_VALIDATION');audit.inverse(text.replace(after,before),old[base.CHILD],'ALL_SAME_REPOSITORY_CALLBACK_BINDING_AND_UNKNOWN_MAPPING_UNCHANGED')
    text=q.text(base.TEST)
    before='    assert_eq!(cas.error(),Some(StoredCommitError::Binding));assert!(cas.registered_job_intent().is_some());\n'
    after='    assert_eq!(cas.error(),Some(StoredCommitError::Binding));assert!(cas.registered_job_intent().is_none());assert!(cas.registration_response().is_some());\n'
    c.require(text.count(after)==1,'STRONGER_NEGATIVE_ASSERTION_DIAGNOSTICS_NOT_CONFIRMATION');audit.inverse(text.replace(after,before),old[base.TEST],'ALL_OTHER_REGISTERED_TESTS_AND_BAD_RESPONSE_CAS_DENIAL_UNCHANGED')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'CONFIRMED_REGISTRATION_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_CONFIRMED_REGISTRATION_COMPONENTS',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_PostgreSQL_or_process_restart=False,SQL23_applied=False,SQL23_catalog_privilege_or_runtime_qualified=False,
        P09_product_execution_or_commit=False,durable_idempotency_complete=False,in_memory_repositories=True,
        model_SQL23_admission_only=True,model_registry_not_SQL_authority=True,scratch_parent=SCRATCH)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        scratch=c.ROOT/SCRATCH;parent=c.ROOT/'target';c.require(parent.is_dir()and not parent.is_symlink()and not parent.is_junction()
            and not scratch.exists()and scratch.resolve().is_relative_to(parent.resolve()),'EARLY_NEW268_OWNED_TEMP_PARENT_ONLY')
        previous=compact.unpack(q.json(predecessor.OUTPUT))
        c.require(q.snapshots[predecessor.OUTPUT]['sha256']=='a5c69bdcde17d83fcdff94dd77ee2a8f7b203393a91e5eb2177d427e09059312'
            and previous['cleanup']and previous['total_executed_cases']==43 and previous['fresh_inputs']==previous['final_fresh_hashes']==903,'EXACT267_MODEL5_REGISTERED9_PRIOR29_AND903_CLOSURE')
        old={p['path']:p for p in previous['source_pins']}
        for name in sorted(CHANGED):q.pin(name)
        inverse(q,old)
        for name in sorted(inventory(guard.check)):
            q.pin(name)
            if name not in CHANGED|{DRIVER}:c.require(q.snapshots[name]==old[name],'ALL_OTHER_ADMISSION_MODELS_FULL23_MIGRATIONS_ENGINE_AND29_CASES_UNCHANGED')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        models={base.PREFIX+n for n in base.names(q,base.ADMISSION)}
        allproduct=set(base.names(q,base.PARENT))|{'recovery_v1::'+n for n in base.names(q,base.prior.RECOVERY_TEST)}|{'precommit_v1::'+n for n in base.names(q,base.prior.TEST)}|{'registered_v1::'+n for n in base.names(q,base.TEST)}
        tools.good_step(previous['steps'][0],models);tools.good_step(previous['steps'][1],allproduct)
        for step in previous['steps']:
            job=step['owned_job'];c.require(job['owned_tree_empty']and job['cleanup_confirmed']and job['job_handle_closed']and
                job['last_job_accounting']['active_processes']==0,'267_BOTH_JOBS_TERMINAL_EMPTY_CLOSED')
        cases={'registered_v1::'+n for n in base.names(q,base.TEST)};c.require(len(cases)==9 and len(models)==5 and len(allproduct-cases)==29,'EXACT9_AFFECTED34_REUSED')
        scratch.mkdir();environment=audit.environment();environment.update(TEMP=str(scratch),TMP=str(scratch))
        snapshot=base.prior.base.base.base.base.base.base.prior.base.base.prior.base.base.base.prior.prior.base.prior.base.prior.base.base.snapshot
        print(json.dumps(dict(state='CONFIRMED_REGISTRATION_PREFLIGHT',inputs=len(q.snapshots),affected9=True,unchanged34_reused=True,actual_DB=False)),flush=True)
        harness.run_one('confirmed_registration9',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','stored_revision_commit','--message-format=short','--','registered_v1::','--test-threads=1'],cases,guard,environment,row,observe_capture=snapshot)
        tools.good_step(row['steps'][-1],cases)
        c.require(not any(scratch.iterdir()),'ALL268_REGISTERED_TEST_TEMP_DIRECTORIES_CLEANED')
        q.finish();guard.check(force=True)
        row.update(state='PASS_CONFIRMED_REGISTRATION9_REUSED_ADMISSION5_PRIOR29_NOT_SQL_RUNTIME_P09_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,total_executed_cases=9,unchanged_cases_reused=34,
            evidence_union_cases=43,test_scratch_empty=True,next_work='ArtifactService_SQL23_profile_typed_job_coordinator_then_real_DB_runtime_restart_evidence')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'CONFIRMED_REGISTRATION_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_CONFIRMED_REGISTRATION_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','test_scratch_empty','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','bounded_output_observation')},'pass_count':sum(v=='ok'for _,v in s.get('tests',[])),
                'failures':[n for n,v in s.get('tests',[])if v!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
