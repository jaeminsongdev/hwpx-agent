"""Actual child202 inherited IO/READY, original GO blocked by a fixed sink.

Source mechanism qualification only: the Frame holds the declared worker202,
not the whole product Native corpus. No product GO, intent or case acceptance.
"""
import copy
import ctypes
from ctypes import wintypes as w
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from types import SimpleNamespace as NS

SELF='tools/p09/native011_product_worker_ready_probe.py'
TEST='tools/p09/tests/test_native011_product_worker_ready_probe.py'


def require(ok,code):
    if not ok:raise ValueError('PRODUCT_WORKER_READY_PROBE_'+code)


def output_for(attempt):
    require(type(attempt) is int and attempt in (1,2,3),'CLOSED_PREPARATION_ATTEMPT')
    return f'implementation/p09/evidence/p09-361-native011-current805-product-worker-ready{attempt:03}.v1.json'


def validate_child(child,required,digest):
    require(child['state']=='COMPLETED_ORIGINAL_INHERITED_WORKER_NOT_PRODUCT_ACCEPTANCE'
        and child['original_worker_exit_code']==1 and child['error_code'] is None
        and child['cleanup_confirmed'] is True and child['cleanup']['import_finder_restored'] is True
        and child['cleanup']['inherited_source_cleanup_confirmed'] is True
        and child['source_count']==child['final_fresh_hashes']==child['inherited_sources_closed']==len(required)==202
        and child['source_pin_sha256']==digest(required)
        and child['source_closing_before_original_READY'] is True
        and child['every_declared_source_read_at_least_twice'] is True
        and child['original_GO_observed'] is False and child['original_input_reads']==1
        and child['product_creation_attempts']==0 and child['GO_written_by_child'] is False
        and child['Native_or_product_acceptance_qualified'] is False,'REAL_CHILD202_CLOSING_EOF_AND_NO_PRODUCT')


def cleanup(g,job,process,capture,assigned,event,handoff,frame,row):
    clean=True
    try:
        if process is not None:
            if process.poll() is None:
                if assigned:require(g.windows.k.TerminateJobObject(job,1),'OWNED_CHILD_TERMINATION')
                else:process.terminate()
            process.wait(timeout=2);process.stdin.close()
        if capture is not None:capture.close()
        elif process is not None:
            for pipe in (process.stdin,process.stdout,process.stderr):pipe.close()
        if job is not None:
            if g.windows.accounting(job)['active_processes']:
                require(g.windows.k.TerminateJobObject(job,1),'OWNED_REMAINING_TREE_TERMINATION')
                deadline=time.monotonic()+2
                while g.windows.accounting(job)['active_processes'] and time.monotonic()<deadline:time.sleep(.01)
            row['inner_job_final']=g.windows.accounting(job)
            clean=row['inner_job_final']['active_processes']==0 and clean
            clean=bool(g.windows.k.CloseHandle(job)) and clean
    except (ValueError,OSError,subprocess.SubprocessError):clean=False
    finally:
        try:
            if event is not None:event.close()
        except (ValueError,OSError):clean=False
        try:
            if handoff is not None:
                # A failed transfer never becomes qualified after cleanup.
                clean=handoff.cleanup_handles() and clean;row['source_handoff']=handoff.summary()
        except (ValueError,OSError):clean=False
        try:
            if frame is not None:
                clean=frame.close() and clean;row['parent_handles']=frame.held.summary()
                row['parent_frame_state']=frame.state
        finally:g.close()
    return clean and g.cleanup


def main():
    require(sys.argv[1:] in (['--attempt','1'],['--attempt','2'],['--attempt','3']),'CLOSED_NO_GO_ENTRY')
    output=output_for(int(sys.argv[2]));sys.dont_write_bytecode=True
    import accept_case112_current_epoch as a,conservative_maintenance as c
    import prepared_run_closure_v1 as host,owned_cpu_baseline_v1 as baseline
    import preparation_attributed_cpu_v1 as policy,distinct_final_sample_guard_v1 as final
    import current_stored_runtime_scope as scope,runtime_input_frame as frames,locked_runtime_inputs as locks
    import native011_source_coverage as coverage,native011_worker_source_inheritance as inheritance
    import native011_inherited_source_probe_child as bridge,native011_nested_preparation_job as nested
    import native011_product_worker_entry as worker,native011_product_source_handoff as transfer
    import native011_ready_scope_connection as control,worker_readiness_v1 as protocol
    import native011_inherited_worker_ready_inspection as original
    import successor_preparation_workspace_v1 as publisher
    from bounded_process_progress import BoundedProcessCapture
    host.configure_host_policy(c)
    g=baseline.guard_type(policy.guard_type(final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=frame=job=process=capture=event=handoff=None;assigned=False;launches=[];command=None;started=time.monotonic()
    row=dict(state='FAILED_PRODUCT_CHILD202_SOURCE_READY_NOT_NATIVE',GO_authorized=False,
        accepted_count_delta=0,actual_product_GO_writes=0,actual_product_or_Native_qualified=False)
    def process_audit(event,values):
        if event=='subprocess.Popen':
            require(command is not None and not launches and values[1] in (command,subprocess.list2cmdline(command)),
                'ONE_EXACT_CHILD202_ONLY');launches.append(1)
        elif event in ('os.system','os.startfile','os.exec','os.posix_spawn','os.fork'):
            raise ValueError('PRODUCT_WORKER_READY_PROBE_OTHER_PROCESS_DENIED')
    sys.addaudithook(process_audit)
    try:
        g.acquire();q=a.AcceptanceReader(c.ROOT,g.check)
        require(not(c.ROOT/output).exists(),'EXCLUSIVE_NEW_NO_GO_RESULT')
        for name in (SELF,TEST,worker.SELF,worker.TEST,transfer.SELF,transfer.TEST,control.SELF,original.SELF,
            bridge.SELF,inheritance.SELF,inheritance.TEST,coverage.SELF,nested.SELF,'tools/p09/native011_inherited_audit_reader.py'):
            q.pin(name)
        declaration=worker.source_declaration(q,a,scope,control);required=declaration.required
        row['worker_source_declaration']=declaration.proof
        held=locks.InputLocks(c.ROOT,g.check);held.api.pacer.rate=14
        frame=frames.Frame(frames.Registry(),required,g.check,held=held);frame.acquire();held.api.pacer.rate=20
        class Reader(a.AcceptanceReader):
            def diagnostics(self):return dict(read_passes=self.read_passes,bytes_read=self.bytes_read,
                observed_input_count=len(self.snapshots),open_rate=self.open_pacer.rate,actual_open_reservations=self.open_pacer.opens)
        reader=lambda checkpoint:Reader(c.ROOT,checkpoint)
        frame.read_boundary(reader,g.check);counts=dict(held.stream_read_counts);identities=copy.deepcopy(held.files)
        row['first_source_boundary']=coverage.verify(frame,required,frame_type=frames.Frame,boundary='before')
        normalized=nested.InnerPreparationJob(g.windows);job=normalized.create();row['inner_job_limits']=normalized.verify(job)
        held.api.pacer.reserve();event=protocol.WindowsEvent();event.inheritable(True)
        handoff=transfer.Handoff(c.ROOT,declaration.entry_pin,frame,required,coverage,inheritance,bridge,protocol,g.check,frame_type=frames.Frame)
        startup=subprocess.STARTUPINFO();startup.lpAttributeList={'handle_list':[event.handle]}
        def factory(argv,**options):
            nonlocal command
            require(command is None,'ONE_ACTUAL_CHILD_FACTORY');worker.arguments(argv[3:]);command=argv
            return subprocess.Popen(argv,**options)
        argv=[sys.executable,'-B',str(c.ROOT/worker.SELF),'--ready-handle',str(event.handle),'--task',worker.TASK]
        try:
            process=handoff.spawn(factory,argv,cwd=c.ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS|subprocess.CREATE_NO_WINDOW,startupinfo=startup,close_fds=True)
        finally:event.inheritable(False)
        require(g.windows.k.AssignProcessToJobObject(job,int(process._handle)),'EXACT_ORIGINAL_JOB_ASSIGNMENT');assigned=True
        def owned(actual):
            normalized.parent_check();member=w.BOOL()
            return actual is process and bool(g.windows.k.IsProcessInJob(int(actual._handle),job,ctypes.byref(member))) and bool(member.value)
        output_only=NS(stdin=NS(close=lambda:None),stdout=process.stdout,stderr=process.stderr,wait=process.wait)
        capture=BoundedProcessCapture(output_only,output_limit=32768,parse_markers=False)
        sink=original.NoGoReadySink(protocol.GO)
        gate=protocol.Gate(sink,event,process,lambda p:handoff.verify_owned(p,owned),handoff.gate_checkpoint)
        handoff.bind_gate(gate);gate_error=None
        try:gate.write(protocol.GO)
        except ValueError as error:
            if error.args!=('READINESS_PROBE_PRODUCT_GO_DENIED',):gate_error=error
        else:gate_error=ValueError('PRODUCT_WORKER_READY_PROBE_GO_MUST_BE_DENIED')
        row['readiness']=gate.diagnostics();row['inner_job_limits_after_ready']=normalized.verify(job)
        process.stdin.close();deadline=time.monotonic()+30
        while True:
            g.check();require(time.monotonic()<deadline,'CLOSED_CHILD_TERMINAL30_AFTER_GATE15')
            try:stdout,stderr=capture.communicate(timeout=.1);break
            except subprocess.TimeoutExpired:capture.progress()
        child=json.loads(stdout.splitlines()[-1]);row['child']=child;row['child_exit_code']=process.returncode
        if gate_error is not None:raise gate_error
        require(gate.ready and gate.stopped and not gate.written and sink.attempts==1
            and handoff.started and not handoff.failed and process.returncode==1,'ORIGINAL_READY15_THEN_REAL_EOF_NOT_PRODUCT_GO')
        validate_child(child,required,worker.pin_digest)
        require(json.loads(stderr.strip())['terminal']=='WORKER_NOT_AUTHORIZED','ORIGINAL_EOF_REJECTION_TERMINAL')
        require(held.stream_read_counts==counts and held.files==identities,'NO_CHILD_READS_AS_PARENT_NATIVE_CREDIT')
        row['after_child_source_boundary']=coverage.verify(frame,required,frame_type=frames.Frame,boundary='before')
        for access in (locks.WRITE,locks.DELETE):
            probe=held.api.access_probe(c.ROOT/worker.SELF,access)
            require(probe['opened'] is False and probe['win32_error']==32,'PARENT_SHARE_LOCKS_STILL_HELD')
        frame.read_boundary(reader,g.check);row['second_source_boundary']=coverage.verify(frame,required,frame_type=frames.Frame,boundary='after')
        require(frame.close(),'ALL_ORIGINAL_PARENT_SOURCE_HANDLES_CLOSED')
        q.finish();g.check(force=True)
        row.update(state='PASS_PRODUCT_CHILD202_SOURCE_AND_ORIGINAL_READY_REAL_EOF_NOT_NATIVE',actual_source_files=202,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            prewarm_before_original_gate_started=False,original_worker_source_scope_pin_sha256=worker.pin_digest(required))
    except (ValueError,OSError,KeyError,IndexError,TypeError,AttributeError,MemoryError,subprocess.SubprocessError) as error:
        value=error.args[0] if error.args else None
        row.update(error_type=type(error).__name__,error_code=value if type(value) is str and re.fullmatch('[A-Za-z0-9_]{1,160}',value)
            else 'CLOSED_CHILD202_READY_FAILURE')
    finally:
        clean=cleanup(g,job,process,capture,assigned,event,handoff,frame,row)
        row.update(cleanup_confirmed=clean,elapsed_seconds=time.monotonic()-started,actual_child_launches=len(launches),
            source_pins=[] if q is None else list(q.snapshots.values()),resource_summary=dict(count=len(g.samples),
                system_CPU_max=max((s['system_cpu_percent'] for s in g.samples),default=None),
                available_RAM_min=min((s['available_ram_percent'] for s in g.samples),default=None)))
        pin=publisher.publish(c.ROOT,output,row,NS(require=c.require,exact=a.exact))
        print(json.dumps(dict(state=row['state'],error_code=row.get('error_code'),child_error=row.get('child',{}).get('error_code'),
            cleanup=clean,fresh=row.get('fresh_inputs'),final=row.get('final_fresh_hashes'),elapsed=row['elapsed_seconds'],receipt=pin)),flush=True)
    return 0 if row['state'].startswith('PASS_') and row['cleanup_confirmed'] else 2


if __name__=='__main__':raise SystemExit(main())
