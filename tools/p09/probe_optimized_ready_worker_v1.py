"""Serial owned EOF/GO probes; every product subprocess denied before creation.

Uses actual original10 Capture/Input + readiness connection + pinned optimized
worker entry. Context8 is diagnostic only, never replayed as Native008 or9.
"""
import sys
from pathlib import Path

SELF="tools/p09/probe_optimized_ready_worker_v1.py"
ENTRY="tools/p09/optimized_ready_worker_v1.py"
PREFIX="implementation/p09/evidence/p09-361-case165-"
CHILD=r'''
import sys,runpy,json,copy
from pathlib import Path
original_copy=copy.deepcopy
historical=0
def audit(event,args):
 global historical
 if event=='subprocess.Popen':raise ValueError('DIAG_SUBPROCESS_DENIED')
 if event=='open' and args and isinstance(args[0],str) and 'current-runtime-run' in args[0].replace('\\','/') and args[0].endswith('.json'):historical+=1
sys.addaudithook(audit)
sys.argv=['tools/p09/optimized_ready_worker_v1.py','--ready-handle',sys.argv[1],'--task','case165-current-r008-tests']
try:runpy.run_path(sys.argv[0],run_name='__main__')
except ValueError as error:
 if error.args not in (('WORKER_NOT_AUTHORIZED',),('DIAG_SUBPROCESS_DENIED',)):raise
 assert historical==0 and copy.deepcopy is original_copy
 names=('worker_readiness_v1','ast_clone_namespace_v1','ast_copy_namespace_connection_v1')
 assert not any(name in sys.modules for name in names)
 root=Path.cwd()/'tools/p09';helpers=set()
 for module in tuple(sys.modules.values()):
  filename=getattr(module,'__file__',None)
  if filename and Path(filename).absolute().is_relative_to(root):helpers.add(Path(filename).absolute())
 print(json.dumps(dict(terminal=error.args[0],historical_runtime_reads=historical,
  private_helpers_not_default_imported=True,original_copy_unchanged=True,
  child_default_project_helper_count=len(helpers))),file=sys.stderr)
 raise SystemExit(1)
'''


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
    import successor_preparation_workspace_v1 as publisher
    import prepare_native008_carrier_v1 as producer
    from bounded_process_progress import BoundedProcessCapture
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True)
    attempt=producer.identifier(parser.parse_args().attempt);output=PREFIX+f'optimized-ready-worker-probe{attempt:03}.v1.json'
    a.require(not(c.ROOT/output).exists(),'EXCLUSIVE_OPTIMIZED_WORKER_PROBE')
    component=recovery.tighten_window(original_window,(c.ROOT/recovery.WINDOW_PIN['path']).read_bytes())
    guard=baseline.guard_type(pressure.guard_type(distinct.guard_type(a.Guard)))();started=time.monotonic();q=None
    row=dict(state='FAILED_OPTIMIZED_READY_WORKER_PROBE_NOT_NATIVE',accepted_count_delta=0,
        product_or_Native_executed=False,GO_authorized=False,Native008_replayed=False,Native009_started=False,
        full69_worker_reconstruction_executed=False,whole_Native009_helper_bound_qualified=False,cases=[])
    try:
        guard.acquire();guard.check(force=True);q=a.AcceptanceReader(c.ROOT,guard.check)
        code=q.json(PREFIX+'optimized-namespace-code001.v1.json')
        a.fields(code,dict(state='PASS_OPTIMIZED_NAMESPACE28_ON_ACTUAL_BINDING_NOT_WORKER_OR_NATIVE009',
            contracts=28,cleanup_confirmed=True,product_or_Native_executed=False,GO_authorized=False),'CURRENT_NAMESPACE28_ONLY')
        for pin in code['source_pins']:
            if pin['path'].startswith('tools/p09/') and pin['path'].endswith('.py'):a.exact(q.pin(pin['path']),pin,'CURRENT_QUALIFIED_NAMESPACE_PROGRAMS')
        for path in (SELF,ENTRY,protocol.SELF,protocol.TEST,connection.SELF,connection.TEST):q.pin(path)
        for mode in ('EOF','GO_DENIED'):
            guard.check(force=True);windows=c.Windows();job=windows.job();process=capture=api=None;assigned=False;terminal=None;begin=time.monotonic()
            try:
                limits=windows.verify_job_limits(job)
                command=[sys.executable,str(c.ROOT/'tools/p09/xz_unified_runtime_v1.py'),'--owned-worker','--task','case165-current-r008-tests']
                def launch(factory,event,*args,**kwargs):
                    a.require(list(args)==[command],'EXACT_ORIGINAL_WORKER_REQUEST')
                    event.inheritable(True);startup=subprocess.STARTUPINFO();startup.lpAttributeList={'handle_list':[event.handle]}
                    try:return factory([sys.executable,'-B','-c',CHILD,str(event.handle)],startupinfo=startup,close_fds=True,**kwargs)
                    finally:event.inheritable(False)
                def owned(actual):
                    member=c.w.BOOL()
                    return actual is process and bool(windows.k.IsProcessInJob(int(actual._handle),job,ctypes.byref(member))) and bool(member.value)
                api=connection.connect(component,protocol,subprocess.Popen,BoundedProcessCapture,launch,owned,guard.check)
                process=api.Popen(command,cwd=c.ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                    creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS|subprocess.CREATE_NO_WINDOW)
                handle=windows.k.OpenProcess(0x101,False,process.pid)
                try:a.require(handle and windows.k.AssignProcessToJobObject(job,handle),'PROBE_JOB_ASSIGN');assigned=True
                finally:
                    if handle:a.require(windows.k.CloseHandle(handle),'PROBE_PROCESS_HANDLE_CLOSE')
                if mode=='EOF':process.stdin.close();capture=BoundedProcessCapture(process)
                else:process.stdin.write(protocol.GO);process.stdin.flush();capture=api.Capture(process)
                deadline=time.monotonic()+15
                while True:
                    guard.check();a.require(time.monotonic()<deadline,'PROBE_CAPTURE_BOUND')
                    try:stdout,stderr=capture.communicate(.1);break
                    except subprocess.TimeoutExpired:capture.progress()
                details=json.loads(stderr)
                a.fields(details,dict(terminal='WORKER_NOT_AUTHORIZED' if mode=='EOF' else 'DIAG_SUBPROCESS_DENIED',
                    historical_runtime_reads=0,private_helpers_not_default_imported=True,original_copy_unchanged=True),'EXACT_NO_PRODUCT_CHILD_TERMINAL')
                a.require(process.returncode==1 and stdout=='','PROBE_NO_PRODUCT_EXIT')
            finally:
                a.require(windows.k.TerminateJobObject(job,1),'PROBE_OWNED_JOB_TERMINATE')
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
                    a.require(time.monotonic()<until,'PROBE_JOB_CLEANUP_BOUND');time.sleep(.02)
                a.require(windows.k.CloseHandle(job),'PROBE_JOB_HANDLE_CLOSE')
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
        row.update(state='PASS_OPTIMIZED_READY_WORKER_EOF_AND_GO_DENIED_NOT_NATIVE009',source_pins=list(q.snapshots.values()),
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            all_owned_Jobs_confirmed_empty=True,original_default_window15_unchanged=original_window.SECONDS==15)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        import re
        row['error_type']=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{1,160}',error.args[0]):row['error_code']=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),RAM_min=min((s['available_ram_percent'] for s in guard.samples),default=None))
    a.require(guard.cleanup,'OPTIMIZED_WORKER_PROBE_OWNER_CLEANUP');publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ('state','cases','fresh_inputs','final_fresh_hashes','elapsed_seconds','CPU_max','RAM_min','cleanup_confirmed','error_code')}))
    return 0 if row['state'].startswith('PASS_') else 1


if __name__=='__main__':raise SystemExit(main())
