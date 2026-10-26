"""Qualify changed origin-mapping source entry, with real READY denial only."""
import inspect,json,re,subprocess,sys,time
from pathlib import Path
import run_block_bookmark_source670 as entry
import block_bookmark_source660 as consumed
from verify_prepared_bookmark631 import command,ReadyDenial
r=entry.r;m=entry.runtime
SELF='tools/p09/verify_block_bookmark_source671.py'
TEST='tools/p09/tests/test_block_bookmark_source670.py'
WORKER_TEST='tools/p09/tests/test_block_bookmark_source670_worker.py'
PORT_PROOF='implementation/p09/evidence/p09-361-block-bookmark-origin669-code001.v1.json'
OLD_PROOF='implementation/p09/evidence/p09-361-block-bookmark-source661-code001.v1.json'

def require(ok,code):
    if not ok:raise ValueError('BLOCK671_'+code)

def main():
    require(sys.argv[1:]==['--code-only-no-native']and not(r.c.ROOT/entry.CODE).exists(),'MODE_OR_IMMUTABLE_OUTPUT')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q=shell=None;start=time.monotonic();row=dict(state='FAILED671_ORIGIN_SOURCE_ENTRY_CODE',steps=[],Native_started=False,
        all_new_tests_passed=False,whole_source_execution_qualified=False,selection_API_qualified=False,P09_complete=False)
    try:
        guard.acquire();q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        ports=entry.publisher.codec.unpack(q.json(PORT_PROOF));old=entry.publisher.codec.unpack(q.json(OLD_PROOF))
        require(q.snapshots[PORT_PROOF]['sha256']=='93589999c1cd321ed37915a8557c462b72273d1ce7e875e317c02e16e8b9c886'
            and ports['cleanup']is True and ports['new_models']==20
            and ports['state']=='QUALIFIED669_OBSERVED_ORIGIN_MAPPING_MODELS_NOT_NATIVE_OR_CAPTURE','RETAINED_ORIGIN_MODELS')
        require(q.snapshots[OLD_PROOF]['sha256']=='7c322b5010be3e6c325318e91f50439d58230d8bc682a0701f47df21450fa9f2'
            and old['cleanup']is True and old['all_new_tests_passed']is True,'UNCHANGED_CONSUMED660_CODE')
        for proof in(ports,old):
            for pin in proof['source_pins']:require(q.pin(pin['path'])==pin,'RETAINED_SOURCE_CHANGED')
        def text(path):return q.text(path).rstrip('\n')
        require(inspect.getsource(m.execute)==inspect.getsource(consumed.execute).replace('660','670'),
            'ORIGINAL_NATIVE_GUARDS_LIFECYCLE_SOURCE_BOUNDARIES_AND_TIMEOUTS')
        require(text(entry.SELF)==text('tools/p09/run_block_bookmark_source660.py').replace('660','670')
            .replace('source661-code001','source671-code001').replace('QUALIFIED661_','QUALIFIED671_'),'ORIGINAL_ONE_USE_ENTRY_GUARDS')
        expected=text('implementation/p09/tools/run-block-bookmark-source660-worker.ps1').replace('660','670')
        expected=expected.replace("'block-bookmark-source653-typed'","'block-bookmark-origin668'").replace('Invoke-P09Block653Ranges $State','Invoke-P09Block668Ranges $State')
        require(text(m.worker_code.TARGET)==expected,'ONLY_MAPPING_PORT_AND_NEW_NAMESPACE_WORKER_CHANGES')
        expected=text('tools/p09/block_bookmark_source660_worker.py').replace('660','670')
        expected=expected.replace('implementation/p09/tools/block-bookmark-source653-typed.ps1','implementation/p09/tools/block-bookmark-origin668.ps1')
        expected=expected.replace('block-bookmark653-call-failure','block-bookmark668-call-failure').replace("'release_references','unknown'","'release_references','origin_set','origin_read','origin_map','unknown'")
        require(text('tools/p09/block_bookmark_source670_worker.py')==expected,'ORIGINAL_LIMITED_WORKER_ENVELOPE_ONLY_NEW_FIXED_PORT')
        paths=m.SOURCES|m.prior.prepared.loaded_dependencies(r.c.ROOT)|{SELF,TEST,WORKER_TEST,entry.SELF,PORT_PROOF}
        row['execution_dependency_paths']=sorted(paths)
        for path in sorted(paths):q.pin(path)
        m.absent()
        for path in(entry.OUTPUT,entry.CLAIM,entry.SCRATCH):m.prior.prepared.require_absent(r.c.ROOT,path)
        image=Path(m.base.candidate.original.SHELL);shell=r.a.AcceptanceReader(image.parent,guard.check)
        row['worker_shell_pin']=shell.pin(image.name)
        require(row['worker_shell_pin']==ports['worker_shell_pin']==old['worker_shell_pin'],'EXACT_CURRENT_TARGET_SHELL')
        native=m.base.session.startup;before=native.hwp_pids(guard.windows,guard.check)
        for test,count,label in((TEST,19,'changed_controller_origin_trace_text_entry_and_original_guards19'),
            (WORKER_TEST,8,'changed_fixed_worker_envelope_and_bounded_notice8')):
            value=command(guard,[sys.executable,'-B',str(r.c.ROOT/test)],r.audit.environment(),row,label)
            require({k:value[k]for k in('run','errors','failures','skipped')}==dict(run=count,errors=0,failures=0,skipped=0)
                and value['actual_native_started']is False,'ALL_CHANGED_ENTRY_MODELS')
        worker=m.worker_code.Worker(guard);denial=ReadyDenial(worker,lambda:shell.fresh_pin(image.name))
        attempt={};row['ready_denial']=attempt
        value=m.prior.io.run(guard,worker,q,worker.start_fixed_worker,denial,m.worker_code.RESULT,r.audit.environment(),lambda v:None,attempt)
        require(attempt['cleanup']is True and attempt['exit_code']==2 and attempt['requests']==1 and denial.calls==1
            and value['state']=='block_source_callbacks_failed_or_partial'and value['completed_callback_cases']==0
            and value['retained_live_or_uncertain_owners']==0 and value['planned_cases']==1
            and value['error_code']=='P09_XREF_BIND_BLOCK670_CURRENT_RELEASE_REQUIRED','REAL_READY_DENIED_BEFORE_NATIVE')
        require(native.hwp_pids(guard.windows,guard.check)==before and not(r.c.ROOT/m.DIRECTORY).exists(),'NO_HWP_OR_SOURCE_CREATED')
        shell.finish();q.finish();guard.check(force=True)
        row.update(state=entry.STATE,all_new_tests_passed=True,new_controller_models=19,new_worker_models=8,
            retained_origin_models_not_replayed=20,actual_READY_frames=1,actual_case_frames=0,
            Native_process_set_unchanged=True,source_directory_created=False)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,KeyboardInterrupt)as error:
        row.update(**m.prior.io.safe_failure(error))
        if isinstance(error,ValueError)and re.fullmatch(r'BLOCK671_[A-Z0-9_]{1,100}',str(error)):row['error_code']=str(error)
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(v['cleanup']for v in row['steps'])and('ready_denial'not in row or row['ready_denial'].get('cleanup')is True),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,shell_final_fresh_hashes=0 if shell is None else shell.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-start,3),system_CPU_max=max((v['system_cpu_percent']for v in guard.samples),default=None),
            available_RAM_min_percent=min((v['available_ram_percent']for v in guard.samples),default=None))
        value,_=entry.publisher.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-block-bookmark-source671-code001-forensic',row)
        pin=entry.publisher.publish(entry.CODE,value)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','elapsed_seconds',
            'system_CPU_max','available_RAM_min_percent')},'failed_tests':[n for s in row['steps']for n in s.get('result',{}).get('failed_tests',[])],'receipt':pin}),flush=True)
    return 0 if row['state']==entry.STATE and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
