"""Read-only public loader audit. Invoke as fixed -c source, not as a production module.

The audit host itself is pinned separately, outside the production dependency
graph. The real entry.load_manifest is NOT patched or given an exclude/filter.
No worker, Native, claim or external execute is called by this audit.
"""
import json,re,sys,time
from types import SimpleNamespace as NS
sys.path.insert(0,r'D:\개발\hwpx-agent\tools\p09')
import named_style_verification_runtime as r
import run_external_crossref_fixed_batch010 as entry

SELF='tools/p09/verify_capture010_handoff608.py'
OUTPUT='implementation/p09/evidence/p09-361-capture010-handoff608.v1.json'

def main():
    c,a,shared=r.c,r.a,r.shared
    c.require(sys.argv[1:]==['--metadata-only']and '__file__'not in globals(),'P608_SEPARATE_READONLY_AUDIT_HOST')
    c.require(not(c.ROOT/OUTPUT).exists(),'P608_IMMUTABLE_OUTPUT')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic()
    row=dict(state='FAILED_CAPTURE010_HANDOFF',own_cpu_selection=selection,actual_Hancom_COM_or_Native_started=False,
        public_entry_execute_called=False,existing_runs_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);q.pin(SELF)
        # Deliberately call the unmodified PUBLIC loader with CURRENT readiness.
        proof,manifest,paths=entry.load_manifest(q,require_runtime_ready=True)
        c.require(entry.SELF in paths and entry.runtime.CASE_PATHS<=paths,'P608_COMPLETE_CURRENT_CLOSURE')
        entry.runtime.absent_attempts()
        for name in(entry.NAMES['claim'],entry.NAMES['output'],entry.NAMES['scratch'],entry.publication.SPOOL):
            path=c.ROOT/name;c.require(not(path.exists()or path.is_symlink()or path.is_junction()),'P608_UNUSED010_NO_REPLAY')
        old_name='implementation/p09/evidence/p09-361-external-qualified-fixed-eight-run009.v1.json'
        old=entry.layout.unpack(q.json(old_name))
        c.require(q.snapshots[old_name]['sha256']=='2eb9a9cb848d888ad39cfe433601e5494b3f4072eab856ef57d67f65fd7d6cef'
            and old['cleanup']is False and old['fixed_eight_executed']is False,'P608_ORIGINAL009_FAILURE_PRESERVED')
        old_probe='target/debug/examples/p09_crossref_capture009_probe.exe'
        old_pin=next(p for p in old['source_pins']if p['path']==old_probe)
        c.require(q.pin(old_probe)==old_pin,'P608_CONSUMED009_BINARY_UNCHANGED')
        q.finish();guard.check(force=True)
        row.update(state='PASS_CURRENT_PUBLIC010_LOADER_CODE_READY_FIXED_INPUTS_NOT_NATIVE_OR_GATE',
            code_proof=q.snapshots[entry.NAMES['code']],readiness=q.snapshots[entry.NAMES['ready']],
            unchanged_public_loader_called=True,public_loader_function_patched=False,
            entry_dependency_paths=sorted(paths),old009_probe=old_pin,
            all_eight_current_attempts_claim_result_spool_absent=True,
            native_startup_qualified=False,actual010_capture_compatibility='NOT_RUN')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=error.args[0]if error.args else None
        row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'P608_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            resource_samples=guard.samples,elapsed_seconds=round(time.monotonic()-started,3),
            system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,entry.layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds',
            'system_CPU_max','available_RAM_min_percent')},'receipt':pin}),flush=True)
    return 0 if row['cleanup']and row['state'].startswith('PASS_')else 2

if __name__=='__main__':raise SystemExit(main())
