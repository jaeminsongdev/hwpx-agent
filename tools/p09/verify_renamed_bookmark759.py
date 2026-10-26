"""Prepare renamed8 with saved-frame capture; models and real READY denial only."""
import json,subprocess,sys,time
from pathlib import Path
import run_prepared_bookmark_native755 as entry
import resource_bundle714 as journal
from verify_prepared_bookmark631 import command,ReadyDenial
r=entry.r;m=entry.runtime
SELF='tools/p09/verify_renamed_bookmark759.py'
TEST='tools/p09/tests/test_renamed_bookmark756.py'
PS_TEST='implementation/p09/tools/test-renamed-bookmark757-profile.ps1'

def require(ok,code):
    if not ok:raise ValueError('XREF_CODE759_'+code)

def main():
    require(sys.argv[1:]==['--code-only-no-native']and not(r.c.ROOT/entry.CODE).exists(),'MODE_NEW_PROOF')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q=shell=observer=None;begin=time.monotonic()
    row=dict(state='FAILED760_RENAMED_EIGHT_CODE',steps=[],actual_native_started=False,all_new_tests_passed=False,P09_complete=False)
    try:
        observer=journal.Attached(guard);guard.acquire();observer.phase('input_binding');q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        prepared=m.prepared.validate_prepared(q,entry.publisher.codec.unpack);row['prepared_files']=prepared
        previous=entry.publisher.codec.unpack(q.json(m.prepared.PROOF))
        current_product={pin['path']:pin for pin in previous['source_pins']}
        for pin in previous['source_pins']:require(q.pin(pin['path'])==pin,'CURRENT_PRODUCT_CODE_AND_INPUTS_UNCHANGED_NO_PRODUCT_REPLAY')
        row['prior754_product_not_replayed']=True
        prior_name='implementation/p09/evidence/p09-361-prepared-bookmark692-code001.v1.json'
        prior=entry.publisher.codec.unpack(q.json(prior_name))
        require(prior['state']=='QUALIFIED692_BLOCK_TAIL_TWO_CODE_AND_REAL_READY_DENIAL_NOT_NATIVE'
            and prior['cleanup']is True and prior['all_new_tests_passed']is True and prior['actual_native_started']is False,'RETAINED_TRANSPORT_LIFECYCLE_CODE_NOT_NATIVE')
        # Byte-bind the shared startup/guard/transport code. No old model or
        # consumed Native755 predecessor is invoked by this preparation.
        history=[]
        for pin in prior['source_pins']:
            path=pin['path']
            if path.startswith('crates/')or path in('Cargo.toml','Cargo.lock'):
                require(path in current_product and q.pin(path)==current_product[path],'CURRENT_PRODUCT_COVERAGE_FOR_HISTORICAL_RUST_INPUT')
                history.append(dict(historical=pin,current=current_product[path],runtime_execution_input=False))
            else:require(q.pin(path)==pin,'SHARED_NATIVE_GUARD_AND_LIFECYCLE_CODE_UNCHANGED')
        row['historical_product_pins_not_native_execution_inputs']=history
        failure='implementation/p09/evidence/p09-361-renamed-bookmark759-code001.v1.json'
        require(q.pin(failure)['sha256']=='3cb200a2bbc4e47f7b85027dfb5b363f9dd6a150df0a74c4969710bfbdf5a828','PRESERVE_EARLY_HISTORICAL_BOUNDARY_FAILURE')
        paths=m.SOURCES|m.prepared.loaded_dependencies(r.c.ROOT)|{entry.SELF,'tools/p09/prepared_bookmark690_receipt.py',m.prepared.PREPARED,m.prepared.SOURCE_PIN['path']}
        paths|={c['output']['path']for c in prepared['cases']}
        row['execution_dependency_paths']=sorted(paths)
        for path in sorted(paths|{SELF,TEST,PS_TEST,m.prepared.PINS,m.prepared.ORIGINAL}):q.pin(path)
        require(not any(path.startswith('crates/')or'/source-archive/'in path or path==m.prepared.PROOF for path in paths),'HISTORY_ONLY_AT_BUNDLE_BOUNDARIES')
        native=m.base.session.startup;before=native.hwp_pids(guard.windows,guard.check);require(not before,'NO_HWP_BEFORE_CODE_PROOF')
        shell_path=Path(m.base.candidate.original.SHELL);shell=r.a.AcceptanceReader(shell_path.parent,guard.check)
        row['shell_pin']=shell.pin(shell_path.name);require(row['shell_pin']==prior['shell_pin'],'SAME_VERIFIED_X86_SHELL')
        observer.phase('model_checks')
        for args,count,label in(([sys.executable,'-B',str(r.c.ROOT/TEST)],21,'new_renamed8_saved_roles_and_guard_contracts21'),
            ([str(shell_path),'-NoLogo','-NoProfile','-NonInteractive','-File',str(r.c.ROOT/PS_TEST),'-ModelsOnly'],6,'new_powershell_syntax_saved_frame_and_no_action6')):
            value=command(guard,args,r.audit.environment(),row,label)
            require({k:value[k]for k in('run','errors','failures','skipped')}==dict(run=count,errors=0,failures=0,skipped=0)
                and value['actual_native_started']is False,'NEW_MODELS_ALL_PASSED')
        observer.phase('readback');worker=m.Worker(guard);handler=ReadyDenial(worker,lambda:shell.fresh_pin(shell_path.name));attempt={};row['ready_denial']=attempt
        value=m.io.run(guard,worker,q,worker.start_fixed_worker,handler,'hwpx-agent.private.crossref-fixed-worker-result/v1',r.audit.environment(),lambda v:None,attempt)
        require(attempt['exit_code']==2 and attempt['cleanup']is True and attempt['requests']==1 and handler.calls==1
            and value['planned_cases']==8 and value['completed_callback_cases']==0 and value['retained_live_or_uncertain_owners']==0,'REAL_READY_DENIAL_ZERO_NATIVE_AND_CASES')
        require(native.hwp_pids(guard.windows,guard.check)==before,'NO_NATIVE_PROCESS_CHANGE');m.absent()
        observer.phase('final_binary');shell.finish()
        observer.phase('final_source');q.finish()
        observer.phase('final_resource');guard.check(force=True)
        row.update(state=entry.STATE,all_new_tests_passed=True,new_code_models=27,shared_transport_guard_and_lifecycle_not_changed=True,
            actual_READY_frames=1,actual_case_frames=0,Native_process_set_unchanged=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,KeyboardInterrupt)as error:row.update(**m.io.safe_failure(error))
    finally:
        guard.close();observer_cleanup=True if observer is None else observer.close()
        if observer is not None:row['phase_resources']=observer.packet()
        row.update(cleanup=guard.cleanup and observer_cleanup and all(s['cleanup']for s in row['steps'])and row.get('ready_denial',{}).get('cleanup',True),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,shell_final_fresh_hashes=0 if shell is None else shell.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-begin,3),resource_samples=len(guard.samples),
            system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        normalized,_=entry.publisher.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-renamed-bookmark760-code001-forensic',row)
        pin=entry.publish(entry.CODE,normalized)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','shell_final_fresh_hashes','resource_samples','system_CPU_max','available_RAM_min_percent','elapsed_seconds')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','result')}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state']==entry.STATE and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
