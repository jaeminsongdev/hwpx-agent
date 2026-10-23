"""405: preserve preparation12/gate8; new drain4 + affected actual worker1% once, no Native."""
import importlib.util,json,re,subprocess,sys,time,unittest
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import crossref_preassigned_preparation as subject
import crossref_preassigned_preparation_io as live

OUTPUT='implementation/p09/evidence/p09-361-crossref-preassigned-preparation-drain405.v1.json'
DRIVER='tools/p09/run_crossref_preassigned_preparation_drain.py'
FAILED='implementation/p09/evidence/p09-361-crossref-preassigned-preparation404.v1.json'
IO='tools/p09/crossref_preassigned_preparation_io.py'
DRAIN='tools/p09/crossref_preassigned_preparation_drain.py'
TEST='tools/p09/tests/test_crossref_preassigned_preparation_drain.py'
SHELL=Path(subject.original.SHELL)


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'PREPARATION_DRAIN405_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=image=None;started=time.monotonic();row=dict(state='FAILED_PREPARATION_TREE_DRAIN405',steps=[],own_cpu_selection=selection,
        actual_Hangul_ROT_COM_or_native_started=False,actual_native7_job_started=False,fixed_eight_executed=False,
        native_startup_qualified=False,Native011_executed=False,prior_Native_replayed=False,
        unaffected_successes_replayed=False,affected_readonly_worker_reexecuted=True,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=r.compact.unpack(q.json(FAILED))
        c.require(q.snapshots[FAILED]['sha256']=='c4a48b2fb05178372a006432e7114946bb84da721a4ffa1669caa7a3fe4bdbf0'
            and failed['state']=='FAILED_PREASSIGNED_PREPARATION404'and not failed['cleanup']
            and failed['error_code']=='XREF_HOST_PROCESS_LIVE_TREE_NO_FORCE_CLOSE'
            and failed['fresh_inputs']==failed['final_fresh_hashes']==214
            and failed['contracts']==dict(run=12,errors=0,failures=0,skipped=0)and len(failed['steps'])==2,
            'ORIGINAL404_BODY_RETURNED_BUT_TREE_CLEANUP_FAILED_NOT_RELABELED_PASS')
        gates,body=failed['steps'];c.require(gates['exit_code']==0 and len(gates['tests'])==8 and all(s=='ok'for n,s in gates['tests'])
            and gates['cleanup']and body['exit_code']==0 and body['requests']==2 and not body['cleanup']
            and body['result']['state']=='closed_preassigned_worker_controller_prepared_not_native'
            and body['result']['probe_lease_closed']and not body['result']['native_directory_or_owner_or_trace_created'],
            'EXACT20_SUCCESSFUL_CONTRACTS_PRESERVED_ACTUAL_BODY_NOT_COMPLETE_CLEANUP')
        pins={p['path']:p for p in failed['source_pins']}
        for path,pin in sorted(pins.items()):
            if path!=IO:c.require(q.pin(path)==pin,'ALL_CONTROLLER_GATE_ORIGINAL_NON_KILLING_ENVELOPE_AND_PASSED20_INPUTS_UNCHANGED')
        text=q.text(IO)
        added="import crossref_preassigned_preparation_drain as drain\n"
        changed="        owned=drain.DrainedPreparationWorker(guard.windows,guard.check)\n        step['owned_job']=owned.profile\n"
        old="        owned=subject.PreparationWorker(guard.windows,guard.check)\n"
        pid="        owned.profile['bootstrap_pid']=owned.process.pid\n"
        c.require(text.count(added)==text.count(changed)==text.count(pid)==1,'EXACT_ONE_POST_TERMINAL_DRAIN_ADAPTER_AND_OWNED_DIAGNOSTICS')
        r.audit.inverse(text.replace(added,'').replace(changed,old).replace(pid,''),pins[IO],
            'ONLY_CLOSE_DRAIN_CLASS_AND_EARLY_RETAINED_PROFILE_PID_ORIGINAL_BODY_LIMITS_DENIAL_AND_CLEANUP_UNCHANGED')
        for path in(DRIVER,DRAIN,TEST):q.pin(path)
        spec=importlib.util.spec_from_file_location('p09_preparation_drain_contracts',c.ROOT/TEST)
        models=importlib.util.module_from_spec(spec);spec.loader.exec_module(models)
        for mod in tuple(sys.modules.values()):
            value=getattr(mod,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        class GuardedResult(unittest.TestResult):
            def stopTest(self,test):super().stopTest(test);guard.check(force=True)
        result=GuardedResult();unittest.defaultTestLoader.loadTestsFromModule(models).run(result)
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['failed_contract_names']=[test.id()for test,_ in result.errors+result.failures]
        c.require(row['contracts']==dict(run=4,errors=0,failures=0,skipped=0),'EXACT4_NEW_POST_TERMINAL_TREE_DRAIN_MODELS')
        image=a.AcceptanceReader(SHELL.parent,guard.check);image.pin(SHELL.name)
        scratch=c.ROOT/'target/p09-crossref-preassigned-preparation-scratch-405'
        c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'PREPARATION405_UNIQUE_COMPILER_TEMP')
        scratch.mkdir();env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONDONTWRITEBYTECODE='1')
        print(json.dumps(dict(state='PREPARATION405_PREFLIGHT',inputs=len(q.snapshots),preserved_contracts=20,new_drain_contracts=4,actual_worker_percent=1)),flush=True)
        live.run(guard,q,env,row)
        step=row['steps'][0];profile=step['owned_job'];observed=profile['post_terminal_tree_drain']
        c.require(step['cleanup']and profile['owned_tree_empty']and profile['job_handle_closed']and not profile['kill_on_close']
            and not profile['forced_termination_invoked']and observed['same_job_observed']and observed['final_active']==0
            and not observed['forced_termination_invoked']and profile['limits_readback']['verified'],
            'ACTUAL_SAME_ONE_PERCENT_JOB_EMPTY_BEFORE_ORIGINAL_HANDLE_CLOSE_NO_FORCE_KILL')
        entries=list(scratch.iterdir());c.require(len(entries)<=32,'PREPARATION405_BOUNDED_SCRATCH');row['retained_compiler_scratch_entries']=len(entries)
        image.finish();q.finish();guard.check(force=True);row.update(state='PASS_PRESERVED20_DRAIN4_ACTUAL_WORKER1_CONTROLLER_DENIAL_COMPLETE_CLEANUP_NOT_NATIVE_OR_GATE',
            current_distinct_contracts=24,preserved_contracts=20,new_contracts=4,actual_worker_integration_cases=1,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,external_shell_final_hashes=image.final_fresh_hashes,
            next_work='independent_current_source_closure_then_external_jobless_native_worker_session_qualification_before_fixed_eight')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'PREPARATION405_FAILURE_NO_RAW_VALUES')
        if q is not None:
            try:
                if image is not None:image.finish();row['external_shell_final_hashes']=image.final_fresh_hashes
                q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),external_shell_pins=[]if image is None else list(image.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,r.compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','contracts','failed_contract_names','fresh_inputs','final_fresh_hashes','external_shell_final_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','safe_error_codes','cleanup','requests')},'tree_drain':s.get('owned_job',{}).get('post_terminal_tree_drain')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
