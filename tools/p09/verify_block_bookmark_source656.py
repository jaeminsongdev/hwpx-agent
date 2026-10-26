"""Changed successor entry/worker qualification; no Native GO or650 retry."""
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import run_block_bookmark_source655 as entry
from verify_prepared_bookmark631 import command,ReadyDenial
r=entry.r;m=entry.runtime
SELF='tools/p09/verify_block_bookmark_source656.py'
TEST='tools/p09/tests/test_block_bookmark_source655.py'
WORKER_TEST='tools/p09/tests/test_block_bookmark_source655_worker.py'
PORT_PROOF='implementation/p09/evidence/p09-361-block-bookmark-source654-code003.v1.json'
OLD_PROOF='implementation/p09/evidence/p09-361-block-bookmark-source651-code002.v1.json'
FAIL='implementation/p09/evidence/p09-361-block-bookmark-source650-native001.v1.json'

def require(ok,code):
    if not ok:raise ValueError('BLOCK656_'+code)

def project_controller(value):
    return value.replace('block_bookmark_source648_worker','block_bookmark_source655_worker').replace(
        'block_bookmark_source650.py','block_bookmark_source655.py').replace(
        'run_block_bookmark_source650.py','run_block_bookmark_source655.py').replace(
        'block-bookmark643-source-document001','block-bookmark655-source-document001').replace(
        'block-bookmark-source648-trace','block-bookmark-source655-trace').replace(
        'XREF_BLOCK650_','XREF_BLOCK655_').replace('block650_current_session','block655_current_session').replace('block650_capture','block655_capture')

def project_entry(value):
    for old,new in(('import block_bookmark_source650 as runtime','import block_bookmark_source655 as runtime'),
        ('source651-code002','source656-code001'),('QUALIFIED651_','QUALIFIED656_'),('source650-','source655-'),
        ('FAILED650_','FAILED655_'),('CAPTURED650_','CAPTURED655_'),('OBSERVED650_','OBSERVED655_'),('BLOCK648_RESULT','BLOCK655_RESULT')):
        value=value.replace(old,new)
    return value

def project_worker(value):
    for old,new in(('BLOCK648_','BLOCK655_'),('block-bookmark-source648-trace','block-bookmark-source655-trace'),
        ('block-bookmark-source648-result','block-bookmark-source655-result'),
        ("'block-bookmark-source646-document','block-bookmark-source648-channel'","'block-bookmark-source653-typed','block-bookmark-source646-document','block-bookmark-source648-channel'"),
        ("    $phase='prewarm';","    function Invoke-P09Block645Ranges($State) {Invoke-P09Block653Ranges $State}\n    $phase='prewarm';"),
        ('cleanup_error=$null;\n','cleanup_error=$null;parameter_call_failure=$null;\n'),
        ('p09-361-block-bookmark643-source-document001','p09-361-block-bookmark655-source-document001'),
        ('range_trace=$trace.block_ranges;cleanup_error_code=$null;',"range_trace=$trace.block_ranges;cleanup_error_code=$null;\n        parameter_call_site='not_started';parameter_range_index=0;parameter_call_failure=$null;"),
        ('catch {$trace.error_code=Get-P09Block648SafeCode $_;$state.failed=$true}',
        'catch {$trace.error_code=Get-P09Block648SafeCode $_;$state.failed=$true;$trace.parameter_call_failure=$state.parameter_call_failure}'),
        ('phase=$trace.phase;error_code=$errorCode}','phase=$trace.phase;error_code=$errorCode;parameter_call_failure=$trace.parameter_call_failure}')):
        require(old in value,'FIXED_WORKER_PROJECTION_ANCHOR');value=value.replace(old,new)
    return value

def main():
    require(sys.argv[1:]==['--code-only-no-native']and not(r.c.ROOT/entry.CODE).exists(),'MODE_OR_IMMUTABLE_OUTPUT')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q=shell=None;start=time.monotonic()
    row=dict(state='FAILED656_SUCCESSOR_CODE',steps=[],Native_started=False,all_new_tests_passed=False,
        whole_source_execution_qualified=False,P09_complete=False,old249_replayed=False)
    try:
        guard.acquire();q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        ports=entry.publisher.codec.unpack(q.json(PORT_PROOF));old=entry.publisher.codec.unpack(q.json(OLD_PROOF))
        failed=entry.publisher.codec.unpack(q.json(FAIL))
        require(q.snapshots[PORT_PROOF]['sha256']=='96a6fa16a3ac23e815dcdaa4cd69b83aaad8473205b8b796305d7a9b15928328'
            and ports['state']=='QUALIFIED654_TYPED_RANGE_BODIES_AND_SAFE_CALL_DIAGNOSTICS_NOT_NATIVE'
            and ports['cleanup']is True and ports['new_models']==24 and ports['fresh_inputs']==ports['final_fresh_hashes']==9,'RETAINED_TYPED_BODIES')
        require(q.snapshots[OLD_PROOF]['sha256']=='55699bac142e9f1f8515e5d615b36904abd1747557f7617b0ee8a9acf202043e'
            and old['cleanup']is True and old['all_new_tests_passed']is True,'PRESERVED_650_CODE_PROOF')
        require(q.snapshots[FAIL]['sha256']=='1d468b67f6ed889cc67607ddd8ffc84004af1d534bee8d29c799693ebd5d927c'
            and failed['cleanup']is True and failed['source_capture_executed']is False,'CONSUMED650_NOT_PROMOTED')
        for proof in(ports,old):
            for pin in proof['source_pins']:require(q.pin(pin['path'])==pin,'FROZEN_SOURCE_OR_RETAINED_TYPED_BODY_CHANGED')
        def text(path):return(r.c.ROOT/path).read_text(encoding='utf-8').rstrip('\n')
        require(text(m.SELF)==project_controller(text('tools/p09/block_bookmark_source650.py')),'UNCHANGED_CONTROLLER_GUARDS_AND_FIXED_NAMESPACE')
        require(text(entry.SELF)==project_entry(text('tools/p09/run_block_bookmark_source650.py')),'UNCHANGED_ENTRY_GUARDS_AND_FIXED_NAMESPACE')
        require(text(m.worker_code.TARGET)==project_worker(text('implementation/p09/tools/run-block-bookmark-source648-worker.ps1')),'ONLY_TYPED_RANGE_AND_BOUNDED_TRACE_WORKER_CHANGES')
        paths=m.SOURCES|m.prior.prepared.loaded_dependencies(r.c.ROOT)|{SELF,TEST,WORKER_TEST,entry.SELF,PORT_PROOF}
        row['execution_dependency_paths']=sorted(paths)
        for path in sorted(paths):q.pin(path)
        m.absent()
        for path in(entry.OUTPUT,entry.CLAIM,entry.SCRATCH):m.prior.prepared.require_absent(r.c.ROOT,path)
        image=Path(m.base.candidate.original.SHELL);shell=r.a.AcceptanceReader(image.parent,guard.check)
        row['worker_shell_pin']=shell.pin(image.name)
        require(row['worker_shell_pin']==ports['worker_shell_pin']==old['worker_shell_pin'],'EXACT_CURRENT_TARGET_SHELL')
        native=m.base.session.startup;before=native.hwp_pids(guard.windows,guard.check)
        for test,count,label in((TEST,15,'successor_controller_entry_and_trace_models15'),(WORKER_TEST,8,'successor_command_and_bounded_notice_models8')):
            v=command(guard,[sys.executable,'-B',str(r.c.ROOT/test)],r.audit.environment(),row,label)
            require({k:v[k]for k in('run','errors','failures','skipped')}==dict(run=count,errors=0,failures=0,skipped=0)
                and v['actual_native_started']is False,'ALL_CHANGED_SUCCESSOR_MODELS')
        worker=m.worker_code.Worker(guard);denial=ReadyDenial(worker,lambda:shell.fresh_pin(image.name))
        attempt={};row['ready_denial']=attempt
        v=m.prior.io.run(guard,worker,q,worker.start_fixed_worker,denial,m.worker_code.RESULT,r.audit.environment(),lambda v:None,attempt)
        require(attempt['cleanup']is True and attempt['exit_code']==2 and attempt['requests']==1 and denial.calls==1
            and v['state']=='block_source_callbacks_failed_or_partial'and v['completed_callback_cases']==0
            and v['retained_live_or_uncertain_owners']==0 and v['planned_cases']==1
            and v['error_code']=='P09_XREF_BIND_BLOCK655_CURRENT_RELEASE_REQUIRED','ACTUAL_READY_ONLY_DENIAL')
        require(native.hwp_pids(guard.windows,guard.check)==before and not(r.c.ROOT/m.DIRECTORY).exists(),'NO_HWP_OR_SOURCE_SIDE_EFFECT')
        shell.finish();q.finish();guard.check(force=True)
        row.update(state=entry.STATE,all_new_tests_passed=True,new_controller_models=15,new_worker_models=8,
            actual_READY_frames=1,actual_case_frames=0,retained_typed_models_not_replayed=24,
            consumed650_preserved=q.snapshots[FAIL],Native_process_set_unchanged=True,
            actual650_root_cause_proven=False,source_directory_created=False)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,KeyboardInterrupt)as error:
        row.update(**m.prior.io.safe_failure(error))
        if isinstance(error,ValueError)and re.fullmatch(r'BLOCK656_[A-Z0-9_]{1,100}',str(error)):row['error_code']=str(error)
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(v['cleanup']for v in row['steps'])and('ready_denial'not in row or row['ready_denial'].get('cleanup')is True),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,shell_final_fresh_hashes=0 if shell is None else shell.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-start,3),system_CPU_max=max((v['system_cpu_percent']for v in guard.samples),default=None),
            available_RAM_min_percent=min((v['available_ram_percent']for v in guard.samples),default=None))
        row,_=entry.publisher.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-block-bookmark-source656-code001-forensic',row)
        pin=entry.publisher.publish(entry.CODE,row)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'failed_tests':[n for s in row['steps']for n in s.get('result',{}).get('failed_tests',[])],'receipt':pin}),flush=True)
    return 0 if row['state']==entry.STATE and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
