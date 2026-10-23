"""493: actual003 one-percent worker ready/kernel binding then unconditional denial. No Native."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import named_style_verification_runtime as r
import crossref_session_qualification as session
import crossref_capture003_worker as fixed
import crossref_native_worker_io as io
from run_crossref_fixed_worker_denial import DenialHandler

SELF='tools/p09/run_crossref_capture003_denial.py'
OUTPUT='implementation/p09/evidence/p09-361-capture003-worker-denial493.v1.json'
CODE='implementation/p09/evidence/p09-361-capture003-entry-code492.v1.json'
SHELL=Path(fixed.original.prior.original.SHELL)

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--deny-before-native'],'CAPTURE003_DENIAL_CLOSED_MODE')
    c.require(not(c.ROOT/OUTPUT).exists(),'CAPTURE003_DENIAL493_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.final.guard_type(a.Guard))()
    started=time.monotonic();q=shell=None
    row=dict(state='FAILED_CAPTURE003_WORKER_READY_DENIAL',steps=[],own_cpu_selection=selection,generation=3,
        actual_Hancom_ROT_COM_or_native_started=False,fixed_eight_executed=False,native_startup_qualified=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);proof=r.compact.unpack(q.json(CODE))
        c.require(q.snapshots[CODE]['sha256']=='a5433e8c7a73708615929614f4a5fec054dd3633d25108c977e218f1c29837dd'
            and proof['state']=='PASS_QUALIFIED_BATCH_ENTRY_CODE_CONTRACTS_NOT_NATIVE_OR_GATE'and proof['cleanup']is True
            and proof['fresh_inputs']==proof['final_fresh_hashes']==236
            and proof['contracts']==dict(run=30,errors=0,failures=0,skipped=0),'EXACT_CURRENT003_CODE492_WITHOUT_TEST_REPLAY')
        for pin in proof['source_pins']:c.require(q.pin(pin['path'])==pin,'ALL_CURRENT003_INPUTS_AND_VERIFIED_MODELS_UNCHANGED')
        for path in(SELF,'tools/p09/run_crossref_fixed_worker_denial.py'):q.pin(path)
        fixed.namespace.require_absent(c.ROOT)
        shell=a.AcceptanceReader(SHELL.parent,guard.check);c.require(shell.pin(SHELL.name)==proof['external_shell_pins'][0],'EXACT492_VERIFIED_SHELL')
        scratch=c.ROOT/'target/p09-capture003-worker-denial-scratch493'
        c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'CAPTURE003_DENIAL_UNIQUE_COMPILER_TEMP')
        scratch.mkdir();env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONDONTWRITEBYTECODE='1')
        worker=fixed.Fixed003Worker(guard);handler=DenialHandler(worker,lambda:shell.fresh_pin(SHELL.name))
        attempt={};row['steps'].append(attempt)
        print(json.dumps(dict(state='CAPTURE003_ACTUAL_READY_DENIAL_PREFLIGHT',inputs=len(q.snapshots),actual_worker_percent=1,native_constructor_trapped=True)),flush=True)
        with patch.object(session.startup,'PreassignedNativeStartup',side_effect=ValueError('CAPTURE003_DENIAL_NATIVE_CONSTRUCTOR_TRAP'))as trap:
            result=io.run(guard,worker,q,worker.start_fixed_worker,handler,'hwpx-agent.private.crossref-fixed-worker-result/v1',env,
                lambda value:print(json.dumps(value),flush=True),attempt)
            row['native_constructor_trap_calls']=trap.call_count;c.require(trap.call_count==0,'CAPTURE003_NATIVE_CONSTRUCTOR_NOT_REACHED')
        c.require(attempt['exit_code']==2 and attempt['requests']==1 and handler.denied and handler.lease.closed
            and result['state']=='fixed_eight_worker_failed_or_uncertain'and result['phase']=='current_live_release'
            and result['completed_callback_cases']==0 and result['retained_live_or_uncertain_owners']==0
            and result['probe_lease_closed']is True and result['native_startup_qualified']is False,'ACTUAL003_READY_DENIAL_BEFORE_NATIVE_OR_CASE_IO')
        fixed.namespace.require_absent(c.ROOT);row['all_eight_native_directories_absent_after']=True
        entries=list(scratch.iterdir());c.require(len(entries)<=32,'CAPTURE003_BOUNDED_COMPILER_SCRATCH');row['retained_compiler_scratch_entries']=len(entries)
        shell.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_ACTUAL_FIXED_WORKER_KERNEL_READY_DENIAL_BEFORE_ALL_CASE_IO_NOT_NATIVE_OR_GATE',
            external_shell_final_hashes=shell.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'CAPTURE003_DENIAL_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s.get('cleanup')is True for s in row['steps']),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            external_shell_pins=[]if shell is None else list(shell.snapshots.values()),resource_samples=samples,elapsed_seconds=round(time.monotonic()-started,3),
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,r.compact.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent','native_constructor_trap_calls')},
            'steps':[{**{k:s.get(k)for k in('exit_code','requests','cleanup','handler_summary')},'result':s.get('result')}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
