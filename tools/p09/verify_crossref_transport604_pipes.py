"""One real Python EOF/Job cleanup proof. Never Hancom, COM, Native or run009 replay."""
import ctypes,json,re,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import named_style_verification_runtime as r
import crossref_fixed_worker as owned
import crossref_native_worker_io603 as transport
import crossref_inline_receipt567 as layout
import crossref_python_current555 as image
SELF='tools/p09/verify_crossref_transport604_pipes.py'
CHILD='tools/p09/transport603_pipe_child.py'
PROOF='implementation/p09/evidence/p09-361-native-worker-transport603-models.v1.json'
OUTPUT='implementation/p09/evidence/p09-361-native-worker-transport604-real-pipes.v1.json'

class PipeWorker(owned.FixedWorker):
    def _fixed_command(self,reader):
        reader.pin(CHILD)
        r.c.require(reader.pin(owned.prior.original.BOOTSTRAP)['sha256']==owned.prior.original.BOOTSTRAP_SHA,'P604_ORIGINAL_WAITING_BOOTSTRAP')
        return [sys.executable,'-B',str(r.c.ROOT/owned.prior.original.BOOTSTRAP),'--worker',
            json.dumps([sys.executable,'-B',str(r.c.ROOT/CHILD),'--io-only'])]

class PythonLifetime:
    """An exact PYTHON worker handle, NOT a Native owner or Native qualification."""
    def __init__(self,worker):self.worker=worker;self.closed=False
    @property
    def process(self):return self.worker.process._handle
    @property
    def pid(self):return self.worker.process.pid
    @property
    def owner_job(self):return NS(job=self.worker.job)
    def close(self):
        if self.closed:return
        w=self.worker.windows
        r.c.require(w.k.WaitForSingleObject(self.process,0)==0 and w.accounting(self.worker.job)['active_processes']==0,
            'P604_REAL_PYTHON_EXACT_HANDLE_AND_TREE_EXIT_REQUIRED')
        # Original worker owns both handles; do not close a borrowed alias.
        self.closed=True

class Handler:
    def __init__(self,worker):self.worker=worker;self.current=PythonLifetime(worker);self.requests=0
    def current_native(self):return None if self.worker.process is None else self.current
    def handle(self,line):
        value=json.loads(line)
        r.c.require(value==dict(schema_version='hwpx-agent.private.python-pipe-probe/v1',sequence=113,
            case_index=6,operation='checkpoint',step='reopen_session_close'),'P604_FIXED_PYTHON_REQUEST')
        self.requests+=1
        # Inject the exact original guard code, NOT a real guard deadline reset
        # or a request to run a product/Native test for 600 seconds.
        raise ValueError('CURRENT_EPOCH_ACCEPT_ORIGINAL600_TIMEOUT')
    def close(self):self.current.close()
    def summary(self):return dict(kind='python_pipe_lifetime_not_native',request_received=self.requests,
        query_lifetime_closed=self.current.closed,native_execution_authorized=False)

def main():
    c,a,shared=r.c,r.a,r.shared
    c.require(sys.argv[1:]==['--pipes-only']and Path(sys.executable)==image.fixed.PYTHON,'P604_FIXED_PYTHON_PIPE_SCOPE')
    c.require(not(c.ROOT/OUTPUT).exists(),'P604_IMMUTABLE_PROOF')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    # The unchanged worker requires the exact original Native guard, even though
    # this probe never reaches a Native constructor or Hancom API.
    guard=shared.baseline.guard_type(shared.final.guard_type(a.Guard))()
    q=runtime=worker=None;started=time.monotonic();attempt={}
    row=dict(state='FAILED_TRANSPORT604_REAL_PIPES',own_cpu_selection=selection,attempt=attempt,
        actual_Hancom_COM_Native_started=False,consumed009_replayed=False,candidate_wired_into_production=False,
        original600_guard_modified=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        proof=layout.unpack(q.json(PROOF))
        c.require(q.snapshots[PROOF]['sha256']=='d5ae22cd52f57e920632555d15c22ab590121174e95e509c9fdcf527f9398456'
            and proof['state']=='PASS_TRANSPORT603_MODELS_NOT_NATIVE_OR_PRODUCTION_OR_GATE'
            and proof['contracts']==dict(run=18,errors=0,failures=0,skipped=0)and proof['cleanup']is True,
            'P604_RETAINED18_MODELS_NOT_REPLAYED')
        for pin in proof['source_pins']:c.require(q.pin(pin['path'])==pin,'P604_CURRENT603_INPUT_UNCHANGED')
        paths={SELF,CHILD}
        for module in tuple(sys.modules.values()):
            filename=getattr(module,'__file__',None)
            if filename:
                p=Path(filename).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':paths.add(p.relative_to(c.ROOT).as_posix())
        for name in sorted(paths):q.pin(name)
        runtime=a.AcceptanceReader(image.fixed.PYTHON.parent,guard.check)
        runtime_pins={name:runtime.pin(name)for name in image.specifications()}
        row['current_python']=image.validate(runtime_pins,image.observe_loaded_images())
        c.require(ctypes.windll.kernel32.GetModuleHandleW('Hwp.exe')==0,'P604_NO_HANCOM_MODULE_IN_THIS_PROCESS')
        worker=PipeWorker(guard);handler=Handler(worker);caught=False
        print(json.dumps(dict(state='P604_ONE_REAL_PYTHON_PIPE_REQUEST_NO_NATIVE',inputs=len(q.snapshots))),flush=True)
        with patch.object(transport.closed.startup,'PreassignedNativeStartup',side_effect=AssertionError('P604_NATIVE_TRAP'))as native:
            try:
                transport.run(guard,worker,q,worker.start_fixed_worker,handler,
                    'hwpx-agent.private.unreachable-native-result/v1',r.audit.environment(),lambda notice:None,attempt)
            except ValueError as error:
                caught=error.args==('CURRENT_EPOCH_ACCEPT_ORIGINAL600_TIMEOUT',)
            row['native_constructor_trap_calls']=native.call_count
        c.require(caught and row['native_constructor_trap_calls']==0 and handler.requests==1
            and attempt['transport_failure']['error_code']=='CURRENT_EPOCH_ACCEPT_ORIGINAL600_TIMEOUT'
            and attempt['transport_failure']['transport_phase']=='handle_request'
            and attempt['abort_eof_sent_before_native_wait']is True and attempt['cleanup']is True
            and attempt['io_threads_joined']is True and attempt['owned_job']['owned_tree_empty']is True
            and attempt['owned_job']['forced_termination_invoked']is False
            and attempt['owned_job']['kill_on_close']is False and worker.returncode==0,'P604_ACTUAL_EOF_AND_NONKILLING_TREE_CLEANUP')
        runtime.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_TRANSPORT604_REAL_PYTHON_PIPES_NOT_NATIVE_OR_PRODUCTION_OR_GATE',
            retained_model_count=18,model_bodies_reexecuted=False,stand_in_is_python_not_native=True,
            current_python_final_fresh_hashes=runtime.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,AssertionError)as error:
        value=error.args[0]if error.args else None
        row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'P604_FAILURE_NO_RAW_VALUES')
    finally:
        if worker is not None and not worker.closed:
            # Non-killing fallback for this exact Python-only target. EOF once,
            # natural exit only; never touch unrelated processes or force close.
            if worker.process is not None:
                if not worker.stdin.closed:worker.stdin.close();worker.profile['input_eof_sent']=True
                worker.wait(timeout=10)
                while guard.windows.accounting(worker.job)['active_processes']:time.sleep(.05)
            worker.close()
        guard.close();row.update(cleanup=guard.cleanup and(worker is None or worker.profile['cleanup_confirmed']),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=guard.samples,
            elapsed_seconds=round(time.monotonic()-started,3),
            system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup',
            'elapsed_seconds','system_CPU_max','available_RAM_min_percent','native_constructor_trap_calls')},'receipt':pin}),flush=True)
    return 0 if row['cleanup']and row['state'].startswith('PASS_')else 2

if __name__=='__main__':raise SystemExit(main())
