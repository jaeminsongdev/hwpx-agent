"""Whole fixed entry dependency closure and changed controller tests; no Native."""
import json
from pathlib import Path
import re
import sys
import time
import run_block_bookmark_source650 as entry
from verify_prepared_bookmark631 import command

runtime=entry.runtime;r=runtime.r
SELF='tools/p09/verify_block_bookmark_source651.py'
TEST='tools/p09/tests/test_block_bookmark_source650.py'
PRIOR='implementation/p09/evidence/p09-361-block-bookmark-source649-code002.v1.json'

def require(ok,code):
    if not ok:raise ValueError('P651_'+code)

def main():
    require(sys.argv[1:]==['--code-only-no-native'],'CODE_ONLY_MODE')
    require(not(r.c.ROOT/entry.CODE).exists(),'IMMUTABLE_OUTPUT')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q=shell=None;start=time.monotonic()
    row=dict(state='FAILED651_ONE_SOURCE_CONTROLLER_CODE',steps=[],Native_started=False,
        all_new_tests_passed=False,whole_source_execution_qualified=False,previous_model_suites_replayed=False,P09_complete=False)
    try:
        guard.acquire();q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        old=entry.publisher.codec.unpack(q.json(PRIOR))
        require(q.snapshots[PRIOR]['sha256']=='62a35a83cbdd2a2ff694f63fdade9b945b6f0d6eed195e14be0bd69494166fb0'
            and old['state']=='QUALIFIED649_FIXED_WORKER_MODELS_AND_READY_DENIAL_NOT_NATIVE_ENTRY'
            and old['cleanup']is True and old['fresh_inputs']==old['final_fresh_hashes']==63
            and old['actual_READY_frames']==1 and old['actual_case_frames']==0 and old['source_directory_created']is False,'RETAINED_WORKER_CODE_NOT_NATIVE')
        for pin in old['source_pins']:require(q.pin(pin['path'])==pin,'UNCHANGED_RETAINED_SOURCE_INPUTS')
        paths=runtime.SOURCES|runtime.prior.prepared.loaded_dependencies(r.c.ROOT)|{SELF,TEST,entry.SELF}
        row['execution_dependency_paths']=sorted(paths)
        for path in sorted(paths):q.pin(path)
        runtime.absent()
        shell_path=Path(runtime.base.candidate.original.SHELL)
        shell=r.a.AcceptanceReader(shell_path.parent,guard.check);row['worker_shell_pin']=shell.pin(shell_path.name)
        require(row['worker_shell_pin']==old['worker_shell_pin'],'CURRENT_EXACT_WORKER_SHELL')
        before=runtime.base.session.startup.hwp_pids(guard.windows,guard.check)
        tests=command(guard,[sys.executable,'-B',str(r.c.ROOT/TEST)],r.audit.environment(),row,'new_controller_entry_producer_sections15')
        require({k:tests[k]for k in('run','errors','failures','skipped')}==dict(run=15,errors=0,failures=0,skipped=0)
            and tests['actual_native_started']is False,'ALL_NEW_CONTROLLER_MODELS')
        require(runtime.base.session.startup.hwp_pids(guard.windows,guard.check)==before,'HWP_SET_UNCHANGED')
        shell.finish();q.finish();guard.check(force=True)
        row.update(state=entry.STATE,all_new_tests_passed=True,new_controller_models=15,
            retained649_models_not_replayed=23,retained649_READY_denial_not_replayed=True,
            Native_process_set_unchanged=True,retained649=q.snapshots[PRIOR])
    except(ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt)as error:
        row.update(**runtime.prior.io.safe_failure(error))
        if isinstance(error,ValueError)and re.fullmatch(r'P651_[A-Z0-9_]{1,100}',str(error)):row['error_code']=str(error)
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,shell_final_fresh_hashes=0 if shell is None else shell.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-start,3),system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        row,_=entry.publisher.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-block-bookmark-source651-code001-forensic',row)
        pin=entry.publisher.publish(entry.CODE,row)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'failed_tests':[n for s in row['steps']for n in s.get('result',{}).get('failed_tests',[])],'receipt':pin}),flush=True)
    return 0 if row['state']==entry.STATE and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
