"""408: actual fixed candidate worker kernel/Job identity + root denial, no Native possible."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import crossref_session_worker as subject
import crossref_session_ready_denial_io as live

OUTPUT='implementation/p09/evidence/p09-361-crossref-session-ready-denial408.v1.json'
DRIVER='tools/p09/run_crossref_session_ready_denial.py'
PROOF='implementation/p09/evidence/p09-361-crossref-session-qualification-code407.v1.json'
SHELL=Path(subject.original.SHELL)


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'SESSION_READY_DENIAL408_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    # No preparation-only CPU policy is applied. This is the ORIGINAL native
    # sampler with measured cold CPU and distinct final sampling wrappers only.
    guard=shared.baseline.guard_type(shared.final.guard_type(a.Guard))()
    q=image=None;started=time.monotonic();row=dict(state='FAILED_SESSION_READY_DENIAL408',steps=[],own_cpu_selection=selection,
        original_native_guard_used=True,actual_Hangul_ROT_COM_or_native_started=False,
        Native_constructor_trap_installed=True,fixed_eight_executed=False,native_startup_qualified=False,
        Native011_executed=False,prior_Native_replayed=False,old_successful_tests_replayed=False,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);proof=r.compact.unpack(q.json(PROOF))
        c.require(q.snapshots[PROOF]['sha256']=='fc474e94efd9126f4c237e52e78adf092f8a41a293d1754b4e593ba7aa533729'
            and proof['state']=='PASS_SESSION_PROTOCOL_KERNEL25_X86_TRANSPORT_SOURCE10_NOT_NATIVE_SESSION_OR_GATE'
            and proof['cleanup']and proof['fresh_inputs']==proof['final_fresh_hashes']==206
            and proof['contracts']==dict(run=25,errors=0,failures=0,skipped=0)and len(proof['steps'])==1
            and len(proof['steps'][0]['tests'])==10 and proof['steps'][0]['exit_code']==0,'EXACT407_NEW35_CONTRACTS_PRESERVED_NOT_REEXECUTED')
        for pin in proof['source_pins']:c.require(q.pin(pin['path'])==pin,'ALL_VERIFIED_SESSION_WORKER_KERNEL_PROTOCOL_AND_ORIGINAL_NATIVE_CODE_UNCHANGED')
        q.pin(DRIVER);q.pin('tools/p09/crossref_session_ready_denial_io.py')
        for mod in tuple(sys.modules.values()):
            value=getattr(mod,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        image=a.AcceptanceReader(SHELL.parent,guard.check);pin=image.pin(SHELL.name)
        c.require(pin==proof['external_shell_pins'][0],'EXACT_407_FIXED_X86_WORKER_EXECUTABLE_UNCHANGED')
        scratch=c.ROOT/'target/p09-crossref-session-ready-denial-scratch-408'
        c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'SESSION_READY408_UNIQUE_COMPILER_TEMP')
        scratch.mkdir();env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONDONTWRITEBYTECODE='1')
        print(json.dumps(dict(state='SESSION_READY408_PREFLIGHT',inputs=len(q.snapshots),original_native_guard=True,actual_worker_share_percent=1,native_constructor_trapped=True)),flush=True)
        live.run(guard,q,lambda:image.pin(SHELL.name),env,row)
        step=row['steps'][0];c.require(step['native_constructor_trap_calls']==0 and step['session_summary']['worker_lease_closed']
            and step['session_summary']['native_backend_profile']is None,'EXACT_WORKER_KERNEL_LEASE_CLOSED_NO_NATIVE_BACKEND_CONSTRUCTED')
        entries=list(scratch.iterdir());c.require(len(entries)<=32,'SESSION_READY408_BOUNDED_SCRATCH');row['retained_compiler_scratch_entries']=len(entries)
        image.finish();q.finish();guard.check(force=True);row.update(state='PASS_ACTUAL_SESSION_WORKER_KERNEL_BINDING_ORIGINAL_ROOT_DENIAL_NOT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,external_shell_final_hashes=image.final_fresh_hashes,
            next_work='external_jobless_full_session_and_fixed_eight_entry_integration_source_closure_before_user_execution')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'SESSION_READY408_FAILURE_NO_RAW_VALUES')
        if q is not None:
            try:
                if image is not None:image.finish();row['external_shell_final_hashes']=image.final_fresh_hashes
                q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),external_shell_pins=[]if image is None else list(image.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,r.compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','external_shell_final_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','cleanup','requests','native_constructor_trap_calls')},'result':s.get('result')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
