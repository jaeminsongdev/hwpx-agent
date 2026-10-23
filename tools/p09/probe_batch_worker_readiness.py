"""One owned run010 READY/EOF diagnostic, never GO or product permission.

Use the actual production launch and worker with an explicit no-GO flag only.
The child rejects non-EOF input and all process creation. A real unnamed event
and Job membership are observed; no Native Frame or Gate.write is simulated.
"""
import json
import re
import sys
import time
from pathlib import Path

SELF='tools/p09/probe_batch_worker_readiness.py'


def require(ok,code):
    if not ok:raise ValueError('BATCH_READY_PROBE_'+code)


def diagnostic_command(command,root,worker,*,zlib=False):
    require(type(zlib) is bool,'EXPLICIT_ZLIB_PROFILE')
    require(type(command) is list and len(command)==7
        and command[:3]==[sys.executable,'-B',str(root/worker.SELF)]
        and command[3]=='--ready-handle' and type(command[4]) is str
        and re.fullmatch('[1-9][0-9]{0,19}',command[4]) is not None and int(command[4])<2**64
        and command[5:]==['--task',worker.TASK],'ONE_EXACT_PRODUCTION_LAUNCH')
    return [*command[:3],'--probe-no-go',*(['--zlib'] if zlib else []),*command[3:]]


def closed_child_error(stderr):
    last=stderr[-16384:].splitlines()[-1:]
    match=re.fullmatch('(ValueError|RuntimeError): ([A-Z][A-Z0-9_]{0,160})',last[0]) if last else None
    return dict(stderr_characters=len(stderr),exception_type=match[1] if match else None,
        error_code=match[2] if match else None,raw_log_preserved_or_printed=False)


def run(root,q,guard,a,c,worker,protocol,connection,component,capture_type,loader,row,*,zlib=False):
    windows=c.Windows();job=windows.job();process=capture=binding=None;assigned=False
    details=None;row.update(GO_authorized=False,actual_GO_writes=0,Native_qualified=False)
    started=time.monotonic()
    try:
        row['owned_limits']=windows.verify_job_limits(job)
        entry_pin=dict(q.pin(worker.SELF))
        launch=worker.launch_api(root,loader)
        launches=[]
        def factory(command,**kwargs):
            require(not launches,'ONE_LAUNCH_NOT_RETRY')
            actual=diagnostic_command(command,root,worker,zlib=zlib)
            launches.append(actual)
            return c.subprocess.Popen(actual,**kwargs)
        def owned(actual):return launch.same_owned_job(windows,job,process,actual)
        binding=launch.connect(root,entry_pin,component,protocol,connection,factory,capture_type,
            c.subprocess,owned,guard.check)
        command=[sys.executable,str(root/'tools/p09/current_queue_successor_runtime.py'),
            '--owned-worker','--task',worker.TASK]
        process=binding.Popen(command,cwd=root,stdin=c.subprocess.PIPE,stdout=c.subprocess.PIPE,
            stderr=c.subprocess.PIPE,creationflags=c.subprocess.BELOW_NORMAL_PRIORITY_CLASS|c.subprocess.CREATE_NO_WINDOW)
        handle=windows.k.OpenProcess(0x101,False,process.pid)
        try:require(handle and windows.k.AssignProcessToJobObject(job,handle),'ACTUAL_JOB_ASSIGNMENT');assigned=True
        finally:
            if handle:require(windows.k.CloseHandle(handle),'ASSIGNMENT_HANDLE_CLOSE')
        require(len(binding.gates)==len(binding.events)==1 and not binding.launch_state.postspawn_inheritance_error,
            'ONE_REAL_GATE_EVENT_AND_RESTORED_INHERITANCE')
        while True:
            guard.check();require(time.monotonic()-started<protocol.SECONDS,'ACTUAL_READINESS15_TIMEOUT')
            require(process.poll() is None and owned(process),'SAME_LIVE_JOB_MEMBER_BEFORE_READY')
            if binding.events[0].wait(50):break
        guard.check();require(process.poll() is None and owned(process),'SAME_LIVE_JOB_MEMBER_AFTER_READY')
        row['readiness_seconds']=time.monotonic()-started
        require(row['readiness_seconds']<protocol.SECONDS,'ACTUAL_READINESS15_TIMEOUT')
        process.stdin.close();capture=capture_type(process)
        until=time.monotonic()+2
        while True:
            guard.check();require(time.monotonic()<until,'EOF_CAPTURE2_TIMEOUT')
            try:stdout,stderr=capture.communicate(.1);break
            except c.subprocess.TimeoutExpired:capture.progress()
        require(stdout=='' and process.returncode==1 and len(stderr)<=16384,'CLOSED_EOF_DIAGNOSTIC')
        try:details=json.loads(stderr)
        except ValueError:
            row['child_setup_failure']=closed_child_error(stderr)
            raise
        a.fields(details,dict(terminal='WORKER_NOT_AUTHORIZED',task=worker.TASK,descriptor_count=162,
            actual_worker_attempts=1,actual_worker_calls=1,raw_policy_restored=True,
            source_step_pin_checked_before_after=True),'ORIGINAL_FULL162_EOF_WITHOUT_PRODUCT')
        if zlib:
            import batch_zlib_runtime as package
            identity=details['zlib_preparation']
            a.exact(identity['package_pins'],list(package.PACKAGE),'ACTUAL_CHILD_NEW_PACKAGE_NOT_OLD010')
            require(type(identity['fresh_inputs']) is int and identity['fresh_inputs']>0
                and identity['final_fresh_hashes']==identity['fresh_inputs']
                and identity['actual_entry_metadata_reads']==4 and identity['Native_or_GO_qualified'] is False,
                'ACTUAL_CHILD_COMPLETE_ZLIB_PREPARATION')
            expected=set(package.CODE)|{package.SELF,worker.SELF}
            require(len(identity['source_pins'])==len(expected)
                and {p['path'] for p in identity['source_pins']}==expected,'CHILD_EXACT_PROFILE_SOURCE5')
            for pin in identity['source_pins']:a.exact(q.pin(pin['path']),pin,'SAME_FRESH_CHILD_AND_PARENT_PROFILE_SOURCE')
        require(type(details['child_default_project_helper_count']) is int
            and 0<details['child_default_project_helper_count']<=64,'CHILD_HELPER64')
        row.update(actual_worker_process_executed=True,actual_product_created=False,
            actual_event_observed=True,child_terminal=details,production_binding=binding.state.diagnostics(),
            production_Gate_write_or_Native_Frame_qualified=False,diagnostic_launch_flag_only=True)
    finally:
        row['cleanup']=dict(active_processes=None,job_handle_closed=False)
        try:
            require(windows.k.TerminateJobObject(job,1),'OWNED_JOB_TERMINATE')
            if process is not None:
                if not assigned and process.poll() is None:process.terminate()
                process.wait(timeout=2)
            until=time.monotonic()+2
            while True:
                terminal=windows.accounting(job)
                if terminal['active_processes']==0:break
                require(time.monotonic()<until,'OWNED_CLEANUP2_TIMEOUT');time.sleep(.02)
            row['cleanup'].update(active_processes=terminal['active_processes'],
                job_CPU_seconds=terminal['job_cpu_seconds'],peak_job_private_MiB=terminal['peak_job_private_mib'])
        finally:
            try:
                if capture is not None:capture.close()
                elif process is not None:
                    for stream in (process.stdin,process.stdout,process.stderr):stream.close()
            finally:
                try:
                    if binding is not None:
                        for event in binding.events:event.close()
                finally:
                    # KILL_ON_JOB_CLOSE remains a final owned-only fallback,
                    # even if termination, accounting or pipe cleanup failed.
                    closed=bool(windows.k.CloseHandle(job))
                    row['cleanup']['job_handle_closed']=closed
                    require(closed,'OWNED_JOB_HANDLE_CLOSE')
    return row


def main():
    sys.path.insert(0,str(Path(__file__).resolve().parent));sys.dont_write_bytecode=True
    require(sys.argv[1:] in ([],['--zlib']),'NO_EXTRA_ARGUMENTS')
    zlib=bool(sys.argv[1:])
    import accept_case112_current_epoch as a,conservative_maintenance as c
    import prepared_run_closure_v1 as host,owned_cpu_baseline_v1 as baseline
    import terminal_metadata_pressure_v1 as pressure,distinct_final_sample_guard_v1 as final
    import batch_worker_launch as worker,runtime_envelope_namespace_bundle_v1 as loader
    import worker_readiness_v1 as protocol,worker_readiness_connection_v1 as connection
    import strict_product_window_v1 as window,post_product_recovery_window_v1 as recovery
    from bounded_process_progress import BoundedProcessCapture
    host.configure_host_policy(c)
    guard=baseline.guard_type(pressure.guard_type(final.guard_type(a.Guard)))();q=None
    row=dict(state='FAILED_OWNED_RUN010_READY_EOF_NOT_NATIVE',GO_authorized=False,accepted_count_delta=0)
    started=time.monotonic()
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        for name in (SELF,worker.SELF,protocol.SELF,connection.SELF,window.SELF,recovery.SELF,worker.LAUNCH['path']):q.pin(name)
        if zlib:q.pin('tools/p09/batch_zlib_runtime.py')
        a.exact(q.pin(protocol.SELF),worker.PROTOCOL,'ORIGINAL_PROTOCOL_SOURCE')
        pin,raw=q._read(recovery.WINDOW_PIN['path'],parse=True);q._bind(pin['path'],pin)
        a.exact(pin,recovery.WINDOW_PIN,'ORIGINAL_WINDOW_SOURCE')
        component=recovery.tighten_window(window,bytes(raw))
        row['probe']={}
        run(c.ROOT,q,guard,a,c,worker,protocol,connection,component,BoundedProcessCapture,loader,row['probe'],zlib=zlib)
        row['zlib_profile']=zlib
        q.finish();guard.check(force=True)
        row.update(state='PASS_OWNED_RUN010_READY_EOF_NOT_NATIVE',source_pins=list(q.snapshots.values()))
    except (ValueError,OSError,KeyError,TypeError,AttributeError,c.subprocess.TimeoutExpired) as error:
        row['error_type']=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch('[A-Z0-9_]{1,160}',error.args[0]):row['error_code']=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            system_CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            owned_CPU_max=max((s.get('parent_cpu_machine_percent') or 0 for s in guard.samples),default=None),
            parent_private_MiB_max=max((s['parent_private_mib'] for s in guard.samples),default=None),
            RAM_available_min=min((s['available_ram_percent'] for s in guard.samples),default=None))
        print(json.dumps(row))
    return 0 if row['state'].startswith('PASS_') and guard.cleanup is True else 2


if __name__=='__main__':raise SystemExit(main())
