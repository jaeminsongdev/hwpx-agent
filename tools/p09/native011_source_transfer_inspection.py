"""One restricted source child, same owned Job, real two child hash passes.

Readonly mechanism probe, not the original worker, READY15, Native or GO.
Parent flags are restored and original identities rechecked BEFORE its start.
"""
import copy
import ctypes
from ctypes import wintypes as w
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import traceback
from types import SimpleNamespace as NS

SELF='tools/p09/native011_source_transfer_inspection.py'
CHILD='tools/p09/native011_inherited_source_probe_child.py'
ORIGINALS=(
    dict(path='tools/p09/runtime_input_frame.py',bytes=5802,sha256='44a21215a76f4160ca7bfeb55b02f3bb464a2017671b0c2dae9883d7c9cd8929'),
    dict(path='tools/p09/locked_runtime_inputs.py',bytes=15465,sha256='e7c40a2ec0367e01c359e3b89c179d45367e9db233348e76ba82364cc0599e14'))


def require(ok,label):
    if not ok:raise ValueError('SOURCE_TRANSFER_'+label)


def main():
    require(not sys.argv[1:],'CLOSED_SINGLE_SOURCE_TRANSFER')
    import accept_case112_current_epoch as a,conservative_maintenance as c
    import prepared_run_closure_v1 as host,owned_cpu_baseline_v1 as baseline
    import preparation_attributed_cpu_v1 as policy,distinct_final_sample_guard_v1 as final
    import current_stored_runtime_scope as scope,runtime_input_frame as frames,locked_runtime_inputs as locks
    import native011_source_coverage as coverage,native011_worker_source_inheritance as inheritance
    import successor_preparation_workspace_v1 as publisher
    from bounded_process_progress import BoundedProcessCapture
    host.configure_host_policy(c)
    g=baseline.guard_type(policy.guard_type(final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    command=[sys.executable,'-B',str(c.ROOT/CHILD),'--source-probe'];launches=[];denied=[]
    def audit(event,args):
        if event=='subprocess.Popen':
            require(not launches and (args[1]==command or args[1]==subprocess.list2cmdline(command)),
                'ONE_EXACT_READONLY_CHILD_ONLY');launches.append(1)
        elif event in ('os.system','os.startfile','os.exec','os.posix_spawn','os.fork'):
            denied.append(event);raise ValueError('SOURCE_TRANSFER_OTHER_PROCESS_DENIED')
    sys.addaudithook(audit)
    output='implementation/p09/evidence/p09-361-native011-current805-source-transfer001.v1.json'
    row=dict(state='FAILED_REAL_SOURCE_HANDLE_TRANSFER_NOT_READY_OR_NATIVE',GO_authorized=False,
        accepted_count_delta=0,actual_original_worker_executed=False,actual_product_executed=False,
        actual_READY15_or_Native_qualified=False)
    q=frame=loan=job=process=capture=None;assigned=False;started=time.monotonic()
    classes={cls:dict(vars(cls)) for cls in (frames.Frame,frames.Registry,locks.InputLocks)}
    try:
        g.acquire();q=a.AcceptanceReader(c.ROOT,g.check)
        require(not(c.ROOT/output).exists(),'EXCLUSIVE_SOURCE_TRANSFER_RESULT')
        for name in (SELF,CHILD,inheritance.SELF,inheritance.TEST,coverage.SELF,
            'tools/p09/tests/test_native011_inherited_source_probe_child.py','tools/p09/bounded_process_progress.py'):q.pin(name)
        for pin in ORIGINALS:a.exact(q.pin(pin['path']),pin,'EXACT_ORIGINAL_FRAME_AND_LOCKS')
        protocol=dict(path='tools/p09/worker_readiness_v1.py',bytes=6890,
            sha256='047c3f78f8a4472feeec4d56b65716f57e0429091321cb49afe5b685047d3a45')
        a.exact(q.pin(protocol['path']),protocol,'ORIGINAL_READY_PROTOCOL_UNMODIFIED')
        required=scope.pins([q.snapshots[name] for name in (inheritance.SELF,CHILD,protocol['path'])])
        held=locks.InputLocks(c.ROOT,g.check);held.api.pacer.rate=14
        frame=frames.Frame(frames.Registry(),required,g.check,held=held);frame.acquire();held.api.pacer.rate=20
        class Reader(a.AcceptanceReader):
            def diagnostics(self):return dict(read_passes=self.read_passes,bytes_read=self.bytes_read,
                observed_input_count=len(self.snapshots),open_rate=self.open_pacer.rate,actual_open_reservations=self.open_pacer.opens)
        factory=lambda checkpoint:Reader(c.ROOT,checkpoint)
        frame.read_boundary(factory,g.check);counts=dict(held.stream_read_counts);identities=copy.deepcopy(held.files)
        sources=[]
        for name,path,handle,directory in held.owned:
            if name in required and not directory:
                info=held.api.inspect(handle)
                sources.append(dict(handle=handle,pin=dict(required[name]),identity=list(info['identity'])))
        packet=dict(schema_version='hwpx-agent.p09-inherited-source-probe/v1',parent_pid=os.getpid(),sources=sources)
        payload=json.dumps(packet,ensure_ascii=True,allow_nan=False,separators=(',',':')).encode()+b'\n'
        require(len(payload)<=262144,'BOUNDED_SOURCE_PACKET')
        loan=inheritance.SourceInheritance(frame,required,coverage,frame_type=frames.Frame)
        job=g.windows.job();row['inner_job_limits']=g.windows.verify_job_limits(job)
        require(row['inner_job_limits']['verified'],'ORIGINAL_OWNED_LIMITS_READBACK')
        handles=loan.arm();startup=subprocess.STARTUPINFO();startup.lpAttributeList={'handle_list':list(handles)}
        spawn_error=None
        try:
            process=subprocess.Popen(command,cwd=c.ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS|subprocess.CREATE_NO_WINDOW,
                startupinfo=startup,close_fds=True)
        except BaseException as error:spawn_error=error;raise
        finally:
            restored=loan.restore()
            if not restored and spawn_error is None:raise ValueError('SOURCE_TRANSFER_PARENT_FLAGS_NOT_RESTORED')
        require(g.windows.k.AssignProcessToJobObject(job,int(process._handle)),'EXACT_INNER_JOB_ASSIGNMENT')
        assigned=True;member=w.BOOL()
        require(g.windows.k.IsProcessInJob(int(process._handle),job,ctypes.byref(member)) and member.value,
            'EXACT_SAME_OWNED_JOB_BEFORE_START')
        row['before_child_coverage']=coverage.verify(frame,required,frame_type=frames.Frame,boundary='before')
        require(held.stream_read_counts==counts and held.files==identities,'NO_PARENT_BYTE_CREDIT_OR_IDENTITY_REBASE')
        g.check(force=True);source_start=time.monotonic()
        data=b'P09_SOURCE_HANDLE_PROBE_V1\n'+payload
        require(process.stdin.write(data)==len(data),'COMPLETE_NO_GO_SOURCE_START');process.stdin.flush()
        capture=BoundedProcessCapture(process,output_limit=32768,parse_markers=False)
        deadline=time.monotonic()+30
        while True:
            g.check();require(time.monotonic()<deadline,'SOURCE_PROBE30_NOT_READY15')
            try:stdout,stderr=capture.communicate(timeout=.1);break
            except subprocess.TimeoutExpired:capture.progress()
        row['child_exit_code']=process.returncode
        result=json.loads(stdout.splitlines()[-1]);row['child']=result
        require(process.returncode==0 and not stderr
            and result['state']=='PASS_INHERITED_SOURCE_TWO_FRESH_HASH_PASSES_NOT_READY_OR_NATIVE'
            and result['cleanup_confirmed'] is True and result['pid']==process.pid and result['parent_pid']==os.getpid(),
            'EXACT_READONLY_CHILD_COMPLETED_NOT_ORIGINAL_WORKER')
        observation=result['source'];expected=list(required.values())
        require(observation['source_files']==3 and observation['actual_passes']==2
            and observation['actual_byte_pins']==[expected,expected]
            and observation['physical_bytes']==2*sum(pin['bytes'] for pin in required.values())
            and observation['inherited_source_handles_closed']==3 and observation['inherited_source_handles_remaining']==0
            and observation['new_source_pathname_opens']==observation['DuplicateHandle_calls']==0
            and observation['source_byte_or_hash_cache'] is False and result['denied_operations']==0,
            'BOTH_REAL_CHILD_HASH_PASSES_AND_HANDLE_CLEANUP')
        row['token_to_child_exit_seconds']=time.monotonic()-source_start
        require(held.stream_read_counts==counts and held.files==identities,'CHILD_READS_NOT_COUNTED_AS_PARENT_NATIVE_READS')
        row['after_child_coverage']=coverage.verify(frame,required,frame_type=frames.Frame,boundary='before')
        for access in (locks.WRITE,locks.DELETE):
            probe=held.api.access_probe(c.ROOT/inheritance.SELF,access)
            require(probe['opened'] is False and probe['win32_error']==32,'PARENT_SHARE_LOCKS_REMAIN_AFTER_CHILD_CLOSE')
        frame.read_boundary(factory,g.check)
        row['after_parent_second_coverage']=coverage.verify(frame,required,frame_type=frames.Frame,boundary='after')
        require(frame.close(),'ORIGINAL_PARENT_HANDLES_CLOSED')
        require(all(set(vars(cls))==set(saved) and all(vars(cls)[name] is value for name,value in saved.items())
            for cls,saved in classes.items()),'ORIGINAL_CLASSES_RETAINED')
        q.finish();g.check(force=True)
        require(q.final_fresh_hashes==len(q.snapshots) and not denied and len(launches)==1,'SOURCE_CLOSING_ONE_CHILD')
        row.update(state='PASS_REAL_INHERITED_SOURCE_TWO_CHILD_HASH_PASSES_NOT_READY15_OR_NATIVE',
            actual_source_files=3,source_bytes=sum(pin['bytes'] for pin in required.values()),
            actual_child_source_inheritance_qualified=True,parent_flag_restored_before_child_start=True,
            actual_original_worker_source198_qualified=False,original_classes_and_methods_retained=True,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,IndexError,TypeError,AttributeError,MemoryError,subprocess.SubprocessError) as error:
        value=error.args[0] if error.args else None
        row.update(error_type=type(error).__name__,error_code=value if type(value) is str
            and re.fullmatch('[A-Za-z0-9_]{1,160}',value) else 'CLOSED_SOURCE_TRANSFER_FAILURE',
            error_frames=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno)
                for f in traceback.extract_tb(error.__traceback__)[-5:]])
    finally:
        clean=True
        try:
            if process is not None:
                if process.poll() is None:
                    if assigned:require(g.windows.k.TerminateJobObject(job,1),'EXACT_OWNED_CHILD_TERMINATION')
                    else:process.terminate()
                process.wait(timeout=2)
            if capture is not None:capture.close()
            elif process is not None:
                for pipe in (process.stdin,process.stdout,process.stderr):pipe.close()
            if job is not None:
                row['inner_job_final']=g.windows.accounting(job)
                clean=row['inner_job_final']['active_processes']==0 and clean
                clean=bool(g.windows.k.CloseHandle(job)) and clean
            if loan is not None:
                clean=(loan.state=='RESTORED' or loan.restore()) and clean;row['parent_loan']=loan.summary()
            if frame is not None:
                clean=frame.close() and clean;row['parent_handles']=frame.held.summary();row['parent_frame_state']=frame.state
        finally:g.close()
        row.update(cleanup_confirmed=clean and g.cleanup,elapsed_seconds=time.monotonic()-started,
            source_pins=[] if q is None else list(q.snapshots.values()),actual_child_launches=len(launches),
            resource_summary=dict(count=len(g.samples),system_CPU_max=max((s['system_cpu_percent'] for s in g.samples),default=None),
                available_RAM_min=min((s['available_ram_percent'] for s in g.samples),default=None)))
        receipt=publisher.publish(c.ROOT,output,row,NS(require=c.require,exact=a.exact))
        print(json.dumps(dict(state=row['state'],error_code=row.get('error_code'),error_frames=row.get('error_frames'),
            child_error=row.get('child',{}).get('error_code'),fresh=row.get('fresh_inputs'),final=row.get('final_fresh_hashes'),
            cleanup=row['cleanup_confirmed'],receipt=receipt)),flush=True)
    return 0 if row['state'].startswith('PASS_') and row['cleanup_confirmed'] else 2


if __name__=='__main__':raise SystemExit(main())
