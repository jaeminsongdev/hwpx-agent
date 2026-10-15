"""Serial actual worker9 EOF/GO diagnostics, product creation always denied."""
import sys
from pathlib import Path

SELF="tools/p09/probe_native009_worker_v1.py"
ENTRY="tools/p09/native009_worker_probe_entry_v1.py"
PREFIX="implementation/p09/evidence/p09-361-case165-"
TASK="case165-current-r009-tests"


def main():
    import argparse,ctypes,json,subprocess,time
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    import prepared_run_closure_v1 as host
    host.configure_host_policy(c);c.Windows()
    import accept_case112_current_epoch as a
    import terminal_metadata_pressure_v1 as pressure
    import distinct_final_sample_guard_v1 as distinct
    import owned_cpu_baseline_v1 as baseline
    import worker_readiness_v1 as protocol
    import worker_readiness_connection_v1 as connection
    import strict_product_window_v1 as original_window
    import post_product_recovery_window_v1 as recovery
    import prepare_native008_carrier_v1 as producer
    import successor_preparation_workspace_v1 as publisher
    from bounded_process_progress import BoundedProcessCapture
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True)
    attempt=producer.identifier(parser.parse_args().attempt);output=PREFIX+f'native009-actual-worker-probe{attempt:03}.v1.json'
    a.require(not(c.ROOT/output).exists(),'EXCLUSIVE_ACTUAL_WORKER_PROBE')
    a.require(not(c.ROOT/(PREFIX+'current-runtime-run009.v1.json')).exists(),'NO_EXISTING_NATIVE009')
    component=recovery.tighten_window(original_window,(c.ROOT/recovery.WINDOW_PIN['path']).read_bytes())
    guard=baseline.guard_type(pressure.guard_type(distinct.guard_type(a.Guard)))();started=time.monotonic();q=None
    row=dict(state='FAILED_ACTUAL_NATIVE009_WORKER_PROBE_NOT_NATIVE',accepted_count_delta=0,
        actual_product_or_Native_executed=False,GO_authorized=False,Native008_replayed=False,
        Native009_product_or_Frame_started=False,whole_current_source_or_Native_helper_bound_qualified=False,cases=[])
    try:
        guard.acquire();guard.check(force=True);q=a.AcceptanceReader(c.ROOT,guard.check)
        code=q.json(PREFIX+'native009-engine-code001.v1.json')
        a.fields(code,dict(state='PASS_NATIVE009_REAL_ENGINE_WORKER_COMPOSITION10_NOT_EXECUTION_OR_NATIVE',
            contracts=dict(run=10,errors=0,failures=0,skipped=0),task=TASK,physical_run=9,descriptor_count=69,
            cleanup_confirmed=True,actual_worker_product_or_Native_executed=False,GO_authorized=False),'ACTUAL_ENGINE10_BEFORE_WORKER_PROBE')
        for pin in code['source_pins']:
            if pin['path'].startswith('tools/p09/') and pin['path'].endswith('.py'):a.exact(q.pin(pin['path']),pin,'CURRENT_QUALIFIED_ENGINE_PROGRAMS')
        for path in (SELF,ENTRY,protocol.SELF,protocol.TEST,connection.SELF,connection.TEST):q.pin(path)
        for mode in ('EOF','GO_DENIED'):
            guard.check(force=True);windows=c.Windows();job=windows.job();process=capture=api=None;assigned=False;terminal=None;begin=time.monotonic()
            try:
                limits=windows.verify_job_limits(job)
                command=[sys.executable,str(c.ROOT/'tools/p09/current_queue_successor_runtime.py'),'--owned-worker','--task',TASK]
                def launch(factory,event,*args,**kwargs):
                    a.require(list(args)==[command],'EXACT_CURRENT_WORKER_REQUEST')
                    event.inheritable(True);startup=subprocess.STARTUPINFO();startup.lpAttributeList={'handle_list':[event.handle]}
                    try:return factory([sys.executable,'-B',str(c.ROOT/ENTRY),'--ready-handle',str(event.handle),'--task',TASK],
                        startupinfo=startup,close_fds=True,**kwargs)
                    finally:event.inheritable(False)
                def owned(actual):
                    member=c.w.BOOL()
                    return actual is process and bool(windows.k.IsProcessInJob(int(actual._handle),job,ctypes.byref(member))) and bool(member.value)
                api=connection.connect(component,protocol,subprocess.Popen,BoundedProcessCapture,launch,owned,guard.check)
                process=api.Popen(command,cwd=c.ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                    creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS|subprocess.CREATE_NO_WINDOW)
                handle=windows.k.OpenProcess(0x101,False,process.pid)
                try:a.require(handle and windows.k.AssignProcessToJobObject(job,handle),'ACTUAL_WORKER_JOB_ASSIGN');assigned=True
                finally:
                    if handle:a.require(windows.k.CloseHandle(handle),'ACTUAL_WORKER_PROCESS_HANDLE_CLOSE')
                if mode=='EOF':process.stdin.close();capture=BoundedProcessCapture(process)
                else:process.stdin.write(protocol.GO);process.stdin.flush();capture=api.Capture(process)
                deadline=time.monotonic()+15
                while True:
                    guard.check();a.require(time.monotonic()<deadline,'ACTUAL_WORKER_CAPTURE_BOUND')
                    try:stdout,stderr=capture.communicate(.1);break
                    except subprocess.TimeoutExpired:capture.progress()
                details=json.loads(stderr)
                a.fields(details,dict(terminal='WORKER_NOT_AUTHORIZED' if mode=='EOF' else 'DIAG_SUBPROCESS_DENIED',
                    task=TASK,descriptor_count=69,actual_worker_attempts=1,actual_worker_calls=1,
                    original_worker_code='run_case112_current_stored.py',raw_policy_restored=True,
                    historical_runtime_reads=0,private_helpers_not_default_imported=True,actual_product_created=False),
                    'EXACT_ACTUAL_WORKER9_TERMINAL_NOT_TEMPLATE_ONLY')
                a.exact(details['product_command_verified'],None if mode=='EOF' else True,'ORIGINAL_EXACT_COMPILED_COMMAND_BEFORE_DENIAL')
                a.require(type(details['child_default_project_helper_count']) is int and
                    details['child_default_project_helper_count']<=64,'ACTUAL_WORKER_DEFAULT_HELPER64_NOT_EXPANDED')
                a.require(process.returncode==1 and stdout=='','ACTUAL_WORKER_DIAGNOSTIC_EXIT')
            finally:
                a.require(windows.k.TerminateJobObject(job,1),'ACTUAL_WORKER_OWNED_JOB_TERMINATE')
                if process is not None:
                    if not assigned and process.poll() is None:process.terminate()
                    process.wait(timeout=2)
                if capture is not None:capture.close()
                elif process is not None:
                    for stream in (process.stdin,process.stdout,process.stderr):stream.close()
                until=time.monotonic()+2
                while True:
                    terminal=windows.accounting(job)
                    if terminal['active_processes']==0:break
                    a.require(time.monotonic()<until,'ACTUAL_WORKER_JOB_CLEANUP_BOUND');time.sleep(.02)
                a.require(windows.k.CloseHandle(job),'ACTUAL_WORKER_JOB_HANDLE_CLOSE')
                if api is not None:
                    for event in api.events:event.close()
            row['cases'].append(dict(mode=mode,child_terminal=details,window=api.state.diagnostics(),
                original_worker_exit_code=process.returncode,elapsed_seconds=time.monotonic()-begin,
                owned_limits_readback=limits,active_after_cleanup=terminal['active_processes'],
                Job_CPU_seconds=terminal['job_cpu_seconds'],cleanup_confirmed=True))
        for module in tuple(sys.modules.values()):
            filename=getattr(module,'__file__',None)
            if filename:
                path=Path(filename).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        q.finish();guard.check(force=True)
        a.require(not(c.ROOT/(PREFIX+'current-runtime-run009.v1.json')).exists(),'NATIVE009_RECEIPT_STILL_ABSENT')
        row.update(state='PASS_ACTUAL_WORKER009_FULL69_EOF_AND_EXACT_COMMAND_DENIED_NOT_NATIVE',
            actual_worker_process_executed=True,full69_worker_reconstructed_and_original_body_called=True,
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            all_owned_Jobs_confirmed_empty=True,original_default_window15_unchanged=original_window.SECONDS==15)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        import re,traceback
        row['error_type']=type(error).__name__
        row['error_frames']=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno) for f in traceback.extract_tb(error.__traceback__)[-5:]]
        if error.args and type(error.args[0]) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{1,160}',error.args[0]):row['error_code']=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),RAM_min=min((s['available_ram_percent'] for s in guard.samples),default=None))
    a.require(guard.cleanup,'ACTUAL_WORKER_PROBE_OWNER_CLEANUP');publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ('state','cases','fresh_inputs','final_fresh_hashes','elapsed_seconds','CPU_max','RAM_min','cleanup_confirmed','error_type','error_code','error_frames')}))
    return 0 if row['state'].startswith('PASS_') else 1


if __name__=='__main__':raise SystemExit(main())
