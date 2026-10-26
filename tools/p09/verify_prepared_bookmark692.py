"""24 changed drain/tail models,4 PS checks and actual READY denial only."""
import json,subprocess,sys,time
from pathlib import Path
import run_prepared_bookmark_native690 as entry
import run_prepared_bookmark_native684 as consumed
import prepared_bookmark690_retained as retained
from verify_prepared_bookmark631 import command,ReadyDenial
r=entry.r;m=entry.runtime
SELF='tools/p09/verify_prepared_bookmark692.py'
TEST='tools/p09/tests/test_prepared_bookmark691.py'
PS_TEST='implementation/p09/tools/test-prepared-bookmark690-profile.ps1'

def require(ok,code):
    if not ok:raise ValueError('XREF_CODE692_'+code)

def main():
    require(sys.argv[1:]==['--code-only-no-native']and not(r.c.ROOT/entry.CODE).exists(),'MODE_NEW_PROOF')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))();q=shell=None;begin=time.monotonic()
    row=dict(state='FAILED692_REMAINING_TWO_CODE',steps=[],actual_native_started=False,all_new_tests_passed=False,P09_complete=False)
    try:
        guard.acquire();q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        row['retained_six']=retained.validate(q)

        failure_path='implementation/p09/evidence/p09-361-prepared-bookmark691-code001.v1.json'
        failure=consumed.publisher.codec.unpack(q.json(failure_path))
        require(q.snapshots[failure_path]['sha256']=='13014a0f1c23c83c7556a94edc74b91e67ea08d908ef9dff2942cfe84976d756'
            and failure['cleanup']is True and len(failure['steps'])==1 and failure['steps'][0]['result']['run']==24
            and failure['steps'][0]['result']['errors']==0 and failure['steps'][0]['result']['failures']==1,'EXACT23_PASSED_ONE_PROFILE_FAILURE')
        archive='implementation/p09/source-archive/p361-prepared-bookmark691-failed/'
        for pin in failure['source_pins']:
            path=archive+pin['path']if pin['path']in(entry.SELF,m.TARGET)else pin['path']
            bound=q.pin(path);require((bound['bytes'],bound['sha256'])==(pin['bytes'],pin['sha256']),'FAILED_INPUTS_PRESERVED')
        require(q.text(m.TARGET)==q.text(archive+m.TARGET).replace('if (-not $PreparedBlockEightAfterCurrentSession)','if (-not $PreparedBlockRemainingTwoAfterCurrentSession)',1),'ONLY_CURRENT_SWITCH_GUARD_CORRECTION')
        require(q.text(entry.SELF)==q.text(archive+entry.SELF).replace('691','692'),'ONLY_NEW_CODE_PROOF_NAMESPACE')
        q.pin('tools/p09/tests/test_prepared_bookmark692_recovery.py')
        row['retained23_code_models_not_replayed']=True

        prior=consumed.publisher.codec.unpack(q.json(consumed.CODE))
        require(q.snapshots[consumed.CODE]['sha256']=='778af92a7b33701f2881e19f896cf9dd617c109dfb6d7330ea34c5a6afd76e88'
            and prior['state']==consumed.STATE and prior['cleanup']is True and prior['current_code_models']==34,'RETAINED34_QUALIFIED_MODELS')
        # Consumed684/631 Python and PS have been byte-bound by688; only new files change.
        row['prepared_files']=m.prepared.validate_prepared(q,consumed.publisher.codec.unpack)
        paths=m.SOURCES|m.prepared.loaded_dependencies(r.c.ROOT)|{entry.SELF,'tools/p09/prepared_bookmark690_receipt.py'}
        paths|={m.prepared.PREPARED,m.prepared.SOURCE_PIN['path']}|{c['output']['path']for c in row['prepared_files']['cases']if c['case_index']in(7,8)}
        row['execution_dependency_paths']=sorted(paths)
        for path in sorted(paths|{SELF,TEST,PS_TEST}):q.pin(path)
        require(not any(path.startswith('crates/')or'/source-archive/'in path or path==retained.PROOF for path in paths),'HISTORY_ONLY_AT_BUNDLE_BOUNDARIES')
        native=m.base.session.startup;before=native.hwp_pids(guard.windows,guard.check);require(not before,'NO_HWP_BEFORE')
        shell_path=Path(m.base.candidate.original.SHELL);shell=r.a.AcceptanceReader(shell_path.parent,guard.check)
        row['shell_pin']=shell.pin(shell_path.name);require(row['shell_pin']==prior['shell_pin'],'SAME_X86_SHELL')
        for args,count,label in(([sys.executable,'-B',str(r.c.ROOT/'tools/p09/tests/test_prepared_bookmark692_recovery.py')],1,'only_corrected_fixed_worker_profile_retained23'),
            ([str(shell_path),'-NoLogo','-NoProfile','-NonInteractive','-File',str(r.c.ROOT/PS_TEST),'-ModelsOnly'],4,'new_tail_syntax_and_fixed_profile4')):
            result=command(guard,args,r.audit.environment(),row,label)
            require({k:result[k]for k in('run','errors','failures','skipped')}==dict(run=count,errors=0,failures=0,skipped=0)
                and result['actual_native_started']is False,'NEW_CODE_MODELS_ALL_PASSED')
        worker=m.Worker(guard);handler=ReadyDenial(worker,lambda:shell.fresh_pin(shell_path.name));attempt={};row['ready_denial']=attempt
        result=m.io.run(guard,worker,q,worker.start_fixed_worker,handler,'hwpx-agent.private.crossref-fixed-worker-result/v1',r.audit.environment(),lambda v:None,attempt)
        require(attempt['exit_code']==2 and attempt['cleanup']is True and attempt['requests']==1 and handler.calls==1
            and result['planned_cases']==2 and result['completed_callback_cases']==0 and result['retained_live_or_uncertain_owners']==0,'REAL_READY_DENIAL_ZERO_CASES')
        require(native.hwp_pids(guard.windows,guard.check)==before,'NO_NATIVE_PROCESS_CHANGE');m.absent()
        shell.finish();q.finish();guard.check(force=True)
        row.update(state=entry.STATE,all_new_tests_passed=True,new_code_models=28,retained34_models_not_replayed=True,
            retained_six_captures_not_replayed=True,actual_READY_frames=1,actual_case_frames=0,Native_process_set_unchanged=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,KeyboardInterrupt)as error:row.update(**m.io.safe_failure(error))
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps'])and('ready_denial'not in row or row['ready_denial'].get('cleanup')is True),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-begin,3),system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        value,_=consumed.publisher.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-prepared-bookmark692-code001-forensic',row)
        pin=consumed.publisher.publish(entry.CODE,value)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','result')}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state']==entry.STATE and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
