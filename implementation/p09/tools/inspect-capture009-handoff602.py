"""Fresh public009 loader/readiness check only; never invoke its main/execute.

Audit driver is outside the production tools/p09 module tree. The public
loaded-module closure is used UNMODIFIED; this driver's own source is pinned
separately. No mocks, claim, Native, COM or case replay.
"""
import json,re,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/p09'))
import named_style_verification_runtime as r
import run_external_crossref_fixed_batch009 as entry

SELF='implementation/p09/tools/inspect-capture009-handoff602.py'
OUTPUT='implementation/p09/evidence/p09-361-capture009-handoff602.v1.json'

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--current-inputs-only'],'P602_CURRENT_INPUTS_ONLY')
    c.require(not(c.ROOT/OUTPUT).exists(),'P602_IMMUTABLE_HANDOFF')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=native=None;started=time.monotonic()
    row=dict(state='FAILED_CAPTURE009_HANDOFF_INPUTS',generation=9,own_cpu_selection=selection,
        actual_Hancom_COM_Native_or_SQL_started=False,external009_executed=False,models_reexecuted=False,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False,native_startup_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);q.pin(SELF)
        proof,pins,paths=entry.load_manifest(q,require_runtime_ready=True)
        c.require(q.snapshots[entry.NAMES['code']]['sha256']=='94f55799a7bbd33635cb62f59f666d9fc1a726578d94333482e20745dbf1750b'
            and q.snapshots[entry.NAMES['ready']]['sha256']=='bea9b6033dfcd3e6e8c8e044f05ac7a9ac37145538a46dd7e0bdcbfdc55a1d6f',
            'P602_EXACT_CURRENT_600_601')
        old=q.pin('target/debug/examples/p09_crossref_capture008_probe.exe')
        c.require((old['bytes'],old['sha256'])==(5151744,'f63c2a3559cc853f8076258cd2ece0b28a2178234f1bf4980209a9705be70592'),
            'P602_CONSUMED008_BINARY_NOT_OVERWRITTEN')
        entry.runtime.absent_attempts()
        c.require(all(not(c.ROOT/n).exists()for n in(entry.NAMES['claim'],entry.NAMES['output'],entry.publication.SPOOL)),
            'P602_NO009_NATIVE_EXECUTION_OR_RESULT_NAMESPACE')
        native=a.AcceptanceReader(Path(entry.installed.native.EXECUTABLE).parent,guard.check)
        current=entry.prerequisites.inspect(guard.windows,guard.check,
            lambda:native.fresh_pin(Path(entry.installed.native.EXECUTABLE).name))
        c.require(current['preexisting_hwp_processes']==0 and current['failed_prerequisites']==['caller_lifecycle_native_safe']
            and current['closed_errors']==dict(caller_lifecycle_native_safe='XREF_NATIVE_STARTUP_PARENT_LIFECYCLE_NOT_NATIVE_SAFE')
            and current['process_created']is False and current['COM_activated']is False and current['document_opened']is False,
            'P602_ZERO_HANCOM_ONLY_EXPECTED_CODEX_PARENT_DENIAL')
        native.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_CAPTURE009_CURRENT_HANDOFF_INPUTS_NOT_NATIVE_OR_GATE',
            current_public_loader_unmodified=True,code_receipt=q.snapshots[entry.NAMES['code']],
            readiness_receipt=q.snapshots[entry.NAMES['ready']],production_dependency_paths=len(paths),
            external_native_final_hashes=native.final_fresh_hashes,preexisting_hwp_processes=0,
            external_user_PowerShell_current_qualification_still_required=True,
            guarded_Hancom_open_and_SaveAs_compatibility='NOT_RUN',all_eight_capture_and_semantics='NOT_RUN')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        code=error.args[0]if error.args else None
        row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'P602_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            resource_samples=guard.samples,elapsed_seconds=round(time.monotonic()-started,3),
            system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        receipt=shared.publisher.publish(c.ROOT,OUTPUT,entry.layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'receipt':receipt}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
