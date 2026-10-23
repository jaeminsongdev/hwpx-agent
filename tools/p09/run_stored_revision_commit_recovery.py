"""Repair only one new test match arm, reuse completed unchanged26; execute actual service13."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_stored_revision_commit_components as base
harness,shared,c,a,audit,tools,compact=base.harness,base.shared,base.c,base.a,base.audit,base.tools,base.compact
OUTPUT='implementation/p09/evidence/p09-361-stored-revision-commit-recovery256.v1.json'
DRIVER='tools/p09/run_stored_revision_commit_recovery.py'
SCRATCH='target/p09-stored-revision-commit-scratch-256'


def inventory(check):return base.inventory(check)|{DRIVER}


def inverse(q,old):
    before='            0 => f.artifacts.set_permissions(&f.owner, f.result, f.reader.subject(), BTreeSet::new(), 9)?,\n'
    after='            0 => { f.artifacts.set_permissions(&f.owner, f.result, f.reader.subject(), BTreeSet::new(), 9)?; }\n'
    text=q.text(base.SERVICE_TEST);c.require(text.count(after)==1,'ONE_U64_MATCH_ARM_DISCARDED_TO_UNIT')
    audit.inverse(text.replace(after,before),old[base.SERVICE_TEST],'ALL_SERVICE_TESTS_IDENTICAL_EXCEPT_NEW_TEST_ARM_RETURN_TYPE_FIX')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'STORED_REVISION_RECOVERY_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_STORED_REVISION_COMMIT_RECOVERY',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        P09_product_execution_or_commit=False,actual_registry_target_or_native_qualified=False,durable_database_or_idempotency_qualified=False,
        actual_ArtifactService_and_RevisionService_code=True,in_memory_repositories=True,manifest_scanner_and_validator_synthetic=True,
        service_artifact_and_revision_CAS_not_distributed_atomic=True,scratch_parent=SCRATCH)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=compact.unpack(q.json(base.OUTPUT))
        c.require(q.snapshots[base.OUTPUT]['sha256']=='22119ff209e6e8a151a81a67b524a82fbaa99aebc9ef0289c418b68392844ecf'
            and failed['cleanup']and len(failed['steps'])==2,'EXACT255_ENGINE_COMPLETED_NEW_SERVICE_COMPILE_FAILURE_RETAINED')
        old={p['path']:p for p in failed['source_pins']}
        for name in sorted(inventory(guard.check)):
            q.pin(name)
            if name not in{DRIVER,base.SERVICE_TEST}:c.require(q.snapshots[name]==old[name],'ALL255_ENGINE_SERVICE_PRODUCTION_NATIVE_ROUTES_AND_PRIOR_TESTS_UNCHANGED')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        inverse(q,old)
        engine=set(base.names(q,base.PARENT))|{'bytes_v1::'+n for n in base.names(q,base.base.base.base.TEST)}|{'unknown_cas::'+n for n in base.names(q,base.ENGINE_TEST)}
        c.require(len(engine)==26,'EXACT26_UNCHANGED_ENGINE_CASES');tools.good_step(failed['steps'][0],engine)
        job=failed['steps'][0]['owned_job'];c.require(job['owned_tree_empty']and job['cleanup_confirmed']and job['job_handle_closed']
            and job['last_job_accounting']['active_processes']==0,'255_ENGINE_JOB_TERMINAL_AND_CLEANED')
        service=set(base.names(q,base.SERVICE_TEST));c.require(len(service)==13,'EXACT13_NEW_SERVICE_CASES')
        build=failed['steps'][1];observation=build['bounded_output_observation']
        c.require(build['exit_code']==101 and not build['tests']and observation['rust_error_codes']==['E0308']
            and observation['short_error_locations']==[[base.SERVICE_TEST,'163','20']],'EXACT_NEW_TEST_MATCH_ARM_TYPE_ERROR_NO_PRODUCT_OR_RESOURCE_FAILURE')
        parent=c.ROOT/'target';scratch=c.ROOT/SCRATCH
        c.require(parent.is_dir()and not parent.is_symlink()and not parent.is_junction()and not scratch.exists()
            and scratch.resolve().is_relative_to(parent.resolve()),'NEW_RECOVERY_OWNED_TEMP_PARENT_ONLY')
        scratch.mkdir();environment=audit.environment();environment.update(TEMP=str(scratch),TMP=str(scratch))
        snapshot=base.base.base.base.prior.base.base.prior.base.base.base.prior.prior.base.prior.base.prior.base.base.snapshot
        print(json.dumps(dict(state='STORED_REVISION_RECOVERY_PREFLIGHT',inputs=len(q.snapshots),new_service13=True,unchanged_engine26_reused=True,official249_reexecuted=False)),flush=True)
        harness.run_one('actual_services_on_synthetic_storage_fixture13',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','stored_revision_commit','--message-format=short','--','--test-threads=1'],service,guard,environment,row,observe_capture=snapshot)
        tools.good_step(row['steps'][-1],service)
        c.require(not any(scratch.iterdir()),'ALL_RECOVERY_TEMP_TEST_DIRECTORIES_CLEANED')
        q.finish();guard.check(force=True)
        row.update(state='PASS_ACTUAL_STORAGE_SERVICE_CAS13_REUSED_UNKNOWN_ENGINE3_AFFECTED23_NOT_P09_EXECUTION_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,total_executed_cases=13,prior_engine_cases_reused=26,
            evidence_union_cases=39,new_feature_cases_across_two_runs=16,all_prior_engine_cases_unmodified_and_not_reexecuted=True,test_scratch_empty=True,
            next_work='durable_reconciliation_idempotency_and_current_P09_qualified_execution_path_NOT_component_promotion')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'STORED_REVISION_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_SERVICE_RECOVERY_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','test_scratch_empty','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations')},'pass_count':sum(v=='ok'for _,v in s.get('tests',[])),
                'failures':[n for n,v in s.get('tests',[])if v!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
