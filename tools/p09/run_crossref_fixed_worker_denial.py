"""412: actual full worker ready/kernel binding, unconditional denial before cases; Native trapped."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import named_style_verification_runtime as r
import crossref_session_qualification as session
import crossref_fixed_worker as fixed
import crossref_qualified_batch as wire
import crossref_native_worker_io as io

OUTPUT='implementation/p09/evidence/p09-361-crossref-fixed-worker-denial412.v1.json'
DRIVER='tools/p09/run_crossref_fixed_worker_denial.py'
PROOF='implementation/p09/evidence/p09-361-crossref-qualified-entry-code411.v1.json'
SHELL=Path(fixed.prior.original.SHELL)


class DenialHandler:
    def __init__(self,worker,shell_pin):self.worker,self.shell_pin=worker,shell_pin;self.lease=None;self.denied=False;self.binding=None
    def handle(self,raw):
        r.c.require(not self.denied and self.lease is None,'FIXED_DENIAL_ONE_READY_FRAME')
        value=json.loads(raw,object_pairs_hook=session.descriptor.original.unique_pairs)
        r.c.require(value.keys()=={'schema_version','worker_identity'}and value['schema_version']==wire.READY,'FIXED_DENIAL_EXACT_READY_SCHEMA')
        session.decode(json.dumps(dict(schema_version=session.REQUEST,sequence=1,operation='ready',worker_identity=value['worker_identity']),separators=(',',':')))
        self.lease=session.WorkerKernelLease(self.worker,value['worker_identity'],self.shell_pin,expected_role='private_fixed_eight_worker')
        self.binding=self.lease.observe();self.denied=True
        return json.dumps(dict(schema_version=wire.READY_REPLY,acknowledged=False,error_code='XREF_HOST_QUALIFIED_BATCH_READONLY_READY_DENIAL',
            native_execution_authorized=False,p09_complete=False),separators=(',',':'))
    def current_native(self):return None
    def close(self):
        if self.lease is not None:self.lease.close()
    def summary(self):
        return dict(ready_denied_before_case_io=self.denied,actual_worker_kernel_binding=self.binding,
            query_handle_closed=self.lease is None or self.lease.closed,native_execution_authorized=False,p09_complete=False)


def main():
    c,a,shared=r.c,r.a,r.shared;current002=sys.argv[1:]==['--generation002']
    c.require(current002 or not sys.argv[1:],'FIXED_WORKER_DENIAL_CLOSED_MODE')
    output='implementation/p09/evidence/p09-361-crossref-fixed-worker-denial480.v1.json'if current002 else OUTPUT
    proof_path='implementation/p09/evidence/p09-361-crossref-generation-code478.v1.json'if current002 else PROOF
    c.require(not(c.ROOT/output).exists(),'FIXED_WORKER_DENIAL412_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.final.guard_type(a.Guard))()
    q=image=None;started=time.monotonic();row=dict(state='FAILED_FIXED_WORKER_READY_DENIAL412',steps=[],own_cpu_selection=selection,
        actual_Hangul_ROT_COM_or_native_started=False,fixed_eight_executed=False,native_startup_qualified=False,
        Native011_executed=False,prior_Native_replayed=False,unaffected_successes_replayed=False,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);proof=r.compact.unpack(q.json(proof_path))
        expected_sha='6982fde81a6d089fb293290b270a77c996bbca22df4cff34a139cb407b84be33'if current002 else'ad8b5af9d425dc56419dffaa478f7a12f46047d5d334814708b292ac9b9bc754'
        c.require(q.snapshots[proof_path]['sha256']==expected_sha
            and proof['state']=='PASS_QUALIFIED_BATCH_ENTRY_CODE_CONTRACTS_NOT_NATIVE_OR_GATE'and proof['cleanup']
            and proof['fresh_inputs']==proof['final_fresh_hashes']==(233 if current002 else 228)
            and proof['contracts']==dict(run=23 if current002 else 42,errors=0,failures=0,skipped=0),
            'EXACT411_ENTRY42_AND_PS10_CONTRACTS_PRESERVED_NOT_REPLAYED')
        for pin in proof['source_pins']:c.require(q.pin(pin['path'])==pin,'ALL_VERIFIED_ENTRY_FIXED_WORKER_AND_ORIGINAL_NATIVE_INPUTS_UNCHANGED')
        q.pin(DRIVER)
        image=a.AcceptanceReader(SHELL.parent,guard.check);c.require(image.pin(SHELL.name)==proof['external_shell_pins'][0],'EXACT411_SHELL_IMAGE')
        scratch=c.ROOT/('target/p09-crossref-fixed-worker-denial-scratch-480'if current002 else'target/p09-crossref-fixed-worker-denial-scratch-412')
        c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'FIXED_DENIAL412_UNIQUE_COMPILER_TEMP')
        scratch.mkdir();env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONDONTWRITEBYTECODE='1')
        worker=fixed.FixedWorker(guard);handler=DenialHandler(worker,lambda:image.fresh_pin(SHELL.name));attempt={};row['steps'].append(attempt)
        print(json.dumps(dict(state='FIXED_DENIAL_PREFLIGHT',generation=2 if current002 else 1,inputs=len(q.snapshots),actual_worker_percent=1,native_constructor_trapped=True)),flush=True)
        with patch.object(session.startup,'PreassignedNativeStartup',side_effect=ValueError('FIXED_DENIAL_NATIVE_CONSTRUCTOR_TRAP'))as trap:
            result=io.run(guard,worker,q,worker.start_fixed_worker,handler,'hwpx-agent.private.crossref-fixed-worker-result/v1',env,
                lambda value:print(json.dumps(value),flush=True),attempt)
            row['native_constructor_trap_calls']=trap.call_count;c.require(trap.call_count==0,'NATIVE_CONSTRUCTOR_NEVER_REACHED_BY_FIXED_READY_DENIAL')
        c.require(attempt['exit_code']==2 and attempt['requests']==1 and handler.denied and handler.lease.closed
            and result['state']=='fixed_eight_worker_failed_or_uncertain'and result['phase']=='current_live_release'
            and result['completed_callback_cases']==0 and result['retained_live_or_uncertain_owners']==0
            and result['probe_lease_closed']is True and result['native_startup_qualified']is False,'ACTUAL_CURRENT_FIXED_WORKER_READY_DENIAL_NOT_NATIVE_OR_CASE_EXECUTION')
        from crossref_external_batch_runtime import absent_attempts
        absent_attempts();row['all_eight_native_directories_absent_after']=True
        entries=list(scratch.iterdir());c.require(len(entries)<=32,'FIXED_DENIAL412_BOUNDED_SCRATCH');row['retained_compiler_scratch_entries']=len(entries)
        image.finish();q.finish();guard.check(force=True);row.update(state='PASS_ACTUAL_FIXED_WORKER_KERNEL_READY_DENIAL_BEFORE_ALL_CASE_IO_NOT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,external_shell_final_hashes=image.final_fresh_hashes,
            next_work='independent_public_preflight_and_fixed_denial_source_package_before_user_external_execution')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'FIXED_DENIAL412_FAILURE_NO_RAW_VALUES')
        if q is not None:
            try:
                if image is not None:image.finish();row['external_shell_final_hashes']=image.final_fresh_hashes
                q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s.get('cleanup')is True for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),external_shell_pins=[]if image is None else list(image.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,output,r.compact.pack(row),NS(require=c.require,exact=r.a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','external_shell_final_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent','native_constructor_trap_calls')},
            'steps':[{**{k:s.get(k)for k in('exit_code','requests','cleanup','handler_summary')},'result':s.get('result')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
